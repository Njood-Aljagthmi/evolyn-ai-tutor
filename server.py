#3

import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Path setup
ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT))
sys.path.append(str(ROOT / "database"))

load_dotenv()

import httpx
from fastapi.responses import RedirectResponse
from src.services.auth_service import verify_firebase_token, get_or_create_user
from src.services.quiz_service import QuizService
from src.services.progress_service import ProgressService, LEVEL_TOPICS
from src.services.rate_limiter import rate_limit_auth, rate_limit_quiz
from db import get_connection
from langchain_openai import ChatOpenAI
from database.progress_tool import get_progress
from src.rag.vector_store import retrieve_knowledge
from src.services.badge_service import sync_badges, get_github_connection, save_github_connection
from src.agent.job_recommender import generate_career_recommendations

# GitHub OAuth config
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
GITHUB_CALLBACK_URL = os.getenv("GITHUB_CALLBACK_URL", "https://ai-tutoring-agent.onrender.com/github/callback")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

# FastAPI Initialization
app = FastAPI(
    title="AI Tutor API",
    description="Adaptive learning backend for Python and Java with FAISS RAG and GPT-4o-mini",
    version="2.0.0"
)

# CORS Middleware
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://ai-tutoring-agent-evolyn.onrender.com",
]

# If FRONTEND_URL environment variable is set, add it to allowed origins
frontend_env = os.getenv("FRONTEND_URL")
if frontend_env:
    # Ensure no trailing slashes are present in origins
    origins.append(frontend_env.rstrip("/"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

quiz_service = QuizService()
progress_service = ProgressService()

# ─────────────────────────────────────────────────────────────────────────────
# Pydantic Schemas for Strict Input Validation
# ─────────────────────────────────────────────────────────────────────────────

class AuthRequest(BaseModel):
    idToken: str = Field(..., description="Firebase ID token sent by client")

class SelectSubjectRequest(BaseModel):
    learner_id: str
    subject: str

class SubmitAssessmentRequest(BaseModel):
    learner_id: str
    subject: str
    quiz: Dict[str, List[Dict[str, Any]]]
    answers: Dict[str, List[str]]

class ExplainTopicRequest(BaseModel):
    learner_id: str
    subject: str
    level: str
    topic: str
    bypass_cache: Optional[bool] = False

class GenerateTopicQuizRequest(BaseModel):
    subject: str
    level: str
    topic: str
    bypass_cache: bool = False

class SubmitTopicQuizRequest(BaseModel):
    learner_id: str
    subject: str
    level: str
    topic: str
    questions: List[Dict[str, Any]]
    answers: List[str]
    attempt_token: str

class VerifyLevelRequest(BaseModel):
    learner_id: str
    subject: str
    level: str

class SoftResetRequest(BaseModel):
    learner_id: str
    subject: str

class SupportTicketRequest(BaseModel):
    learner_id: str
    email: Optional[str] = None
    category: str
    message: str

# ─────────────────────────────────────────────────────────────────────────────
# Classmate's Schemas and Session State
# ─────────────────────────────────────────────────────────────────────────────

# Temporary in-memory session storage
learner_sessions: Dict[str, List[Dict[str, str]]] = {}


class ChatRequest(BaseModel):
    learner_id: str
    message: str
    language: Optional[str] = None
    level: Optional[str] = None
    top_k: int = 3


class ChatResponse(BaseModel):
    learner_id: str
    reply: str
    retrieved_context: List[Dict[str, Any]]
    session_history: List[Dict[str, str]]


class AssessmentSubmitRequest(BaseModel):
    learner_id: str
    name: str
    email: str
    goal: Optional[str] = "Learn Python and AI basics"
    path: str = "python"
    quiz: Dict[str, Any]
    user_answers: Dict[str, List[str]]


def normalize_retrieved_context(results):
    """
    Convert retrieval results into JSON-safe dictionaries.
    Works with:
    - list of dictionaries
    - LangChain Document objects
    - tuples like (Document, score)
    """

    normalized = []

    if not results:
        return normalized

    for item in results:
        # Case 1: result is already a dictionary
        if isinstance(item, dict):
            content = (
                item.get("content")
                or item.get("page_content")
                or item.get("text")
                or item.get("result")
                or str(item)
            )

            metadata = item.get("metadata", {})

            # Some retrieval tools store metadata fields directly in the dict
            if not metadata:
                metadata = {
                    key: value
                    for key, value in item.items()
                    if key not in ["content", "page_content", "text", "result", "score"]
                }

            score = item.get("score")

            normalized.append({
                "content": content,
                "metadata": metadata,
                "score": score
            })

        # Case 2: result is LangChain Document
        elif hasattr(item, "page_content"):
            normalized.append({
                "content": item.page_content,
                "metadata": getattr(item, "metadata", {}),
                "score": None
            })

        # Case 3: result is tuple like (Document, score)
        elif isinstance(item, tuple) and len(item) > 0:
            doc = item[0]
            score = item[1] if len(item) > 1 else None

            if hasattr(doc, "page_content"):
                normalized.append({
                    "content": doc.page_content,
                    "metadata": getattr(doc, "metadata", {}),
                    "score": score
                })
            else:
                normalized.append({
                    "content": str(doc),
                    "metadata": {},
                    "score": score
                })

        # Case 4: fallback
        else:
            normalized.append({
                "content": str(item),
                "metadata": {},
                "score": None
            })

    return normalized

# ─────────────────────────────────────────────────────────────────────────────
# Helper for Explanation Caching (reducing LLM usage for lessons)
# ─────────────────────────────────────────────────────────────────────────────

def get_cached_explanation(subject: str, level: str, topic: str) -> Optional[str]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cached_explanations (
            key TEXT PRIMARY KEY,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

    key = f"explain_{subject}_{level}_{topic}".lower()
    cursor.execute("SELECT content FROM cached_explanations WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row["content"] if row else None

def save_cached_explanation(subject: str, level: str, topic: str, content: str):
    conn = get_connection()
    cursor = conn.cursor()
    key = f"explain_{subject}_{level}_{topic}".lower()
    cursor.execute("""
        INSERT OR REPLACE INTO cached_explanations (key, content)
        VALUES (?, ?)
    """, (key, content))
    conn.commit()
    conn.close()

# ─────────────────────────────────────────────────────────────────────────────
# API Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/auth", dependencies=[Depends(rate_limit_auth)])
async def api_auth(payload: AuthRequest):
    """
    Verifies Firebase token and returns/registers learner profile.
    """
    try:
        decoded = verify_firebase_token(payload.idToken)
        user = get_or_create_user(decoded)
        return user
    except ValueError as e:
        print("ValueError in api_auth:", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal authentication error: {str(e)}"
        )

@app.post("/api/select_subject")
async def api_select_subject(payload: SelectSubjectRequest):
    """
    Selects learning subject (Python/Java).
    """
    learner_id = payload.learner_id
    subject = payload.subject.lower()
    
    if subject not in ["python", "java"]:
        raise HTTPException(status_code=400, detail="Invalid subject selection. Must be python or java.")

    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Update learner profile goal/state
    cursor.execute("""
        UPDATE learner_profile SET goal = ? WHERE learner_id = ?
    """, (f"Master {subject.upper()} programming", learner_id))
    
    # 2. Check if a progress entry already exists for this subject
    cursor.execute("""
        SELECT 1 FROM learning_progress WHERE learner_id = ? AND subject = ?
    """, (learner_id, subject))
    exists = cursor.fetchone()
    
    if not exists:
        # Create initial record
        cursor.execute("""
            INSERT INTO learning_progress (learner_id, subject, current_level, completed_topic, current_topic, status)
            VALUES (?, ?, 'beginner', 'none', 'assessment', 'in_progress')
        """, (learner_id, subject))
        
        cursor.execute("""
            INSERT INTO learning_plan (learner_id, subject, current_level, plan_title, current_topic, recommended_next_step)
            VALUES (?, ?, 'beginner', 'Dynamic Plan', 'assessment', 'Take Initial Assessment')
        """, (learner_id, subject))
    else:
        # Restore the saved level for this subject back to the learner profile
        cursor.execute("""
            SELECT current_level FROM learning_progress 
            WHERE learner_id = ? AND subject = ? 
            ORDER BY created_at DESC LIMIT 1
        """, (learner_id, subject))
        row = cursor.fetchone()
        if row:
            saved_level = row["current_level"]
            cursor.execute("""
                UPDATE learner_profile SET skill_level = ?
                WHERE learner_id = ?
            """, (saved_level, learner_id))
        
    conn.commit()
    conn.close()
    
    return {"status": "success", "message": f"Subject set to {subject}."}

@app.get("/api/assessment/generate", dependencies=[Depends(rate_limit_quiz)])
async def api_generate_assessment(subject: str):
    """
    Generates 12 assessment questions (4 beginner, 4 intermediate, 4 advanced) utilizing classmate's assessment agent.
    """
    if subject.lower() not in ["python", "java"]:
        raise HTTPException(status_code=400, detail="Invalid subject")
    try:
        from src.agent.assessment_quiz import generate_assessment_quiz
        quiz = generate_assessment_quiz(subject)
        return quiz
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate assessment: {str(e)}")

@app.post("/api/assessment/submit")
async def api_submit_assessment(payload: SubmitAssessmentRequest):
    """
    Evaluates assessment answers, determines initial level, stores weak areas, and builds the initial learning plan.
    """
    try:
        from src.agent.assessment_quiz import evaluate_assessment, determine_level
        from src.agent.learning_plan import update_learning_path
        
        # 1. Evaluate quiz scores per tier
        result = evaluate_assessment(payload.quiz, payload.answers)
        scores = result["scores"]
        level = determine_level(scores["beginner"], scores["intermediate"], scores["advanced"])

        # 2. Generate adaptive learning path plan first
        path_result = update_learning_path(
            learner_id=payload.learner_id,
            name=payload.learner_id,
            email=f"{payload.learner_id}@tutor.com",
            skill_level=level,
            goal=f"Learn {payload.subject}",
            wrong_questions=result["wrong_questions"],
            path=payload.subject
        )
        plan_data = path_result.get("plan", {})



        # 4. Save assessment results to database
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO assessment_results (learner_id, subject, beginner_score, intermediate_score, advanced_score, assigned_level)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (payload.learner_id, payload.subject, scores["beginner"], scores["intermediate"], scores["advanced"], level))
        
        # Update current profile skill level
        cursor.execute("""
            UPDATE learner_profile SET skill_level = ? WHERE learner_id = ?
        """, (level, payload.learner_id))
        
        conn.commit()
        conn.close()

        # Save plan to database
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO learning_plan (learner_id, subject, current_level, plan_title, current_topic, recommended_next_step)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            payload.learner_id,
            payload.subject,
            level,
            plan_data.get("plan_title", "Adaptive Plan"),
            plan_data.get("current_topic", "basics"),
            plan_data.get("recommended_next_step", "[]")
        ))
        conn.commit()
        conn.close()

        return {
            "assigned_level": level,
            "scores": scores,
            "plan": plan_data,
            "weak_topics": path_result.get("weak_topics", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Assessment processing failed: {str(e)}")

@app.get("/api/progress")
async def api_get_progress(learner_id: str, subject: str = "python"):
    """
    Retrieves full dashboard parameters for profile, current level, learning plan, completed and weak topics.
    """
    try:
        info = progress_service.get_learner_progress_info(learner_id, subject)
        if "error" in info:
            raise HTTPException(status_code=404, detail=info["error"])
        return info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def fetch_explanation_en(topic: str, difficulty: str, subject: str) -> str:
    result = retrieve_knowledge(query=topic, language=subject, level=difficulty, k=3)
    results_list = result.get("results", []) if isinstance(result, dict) else result
    chunks = "\n\n".join(r["content"] for r in results_list)
    prompt = f"""You are an expert programming tutor named Evolyn.
Explain the following programming topic in a simple, clear, and comprehensive manner in English.

Topic: {topic}
Level: {difficulty}
Language: {subject}

Instructions:
1. Explain the core concepts of the topic in 2-3 structured paragraphs.
2. YOU MUST INCLUDE AT LEAST ONE CLEAR, EXECUTABLE CODE EXAMPLE. Format the code blocks using markdown syntax (e.g., ```python or ```java) so it renders correctly in the code viewer.
3. Write clean, readable code and include comments explaining what each key line does.
4. Keep the presentation educational, encouraging, and clear.
5. CRITICAL: Strictly explain this topic and write code examples for the '{subject}' programming language ONLY. Do NOT reference other languages (e.g. if the language is Python, do not mention or use Java syntax, classes, C++ pointers, etc.).

Reference Material:
{chunks[:1500]}
"""
    llm_instance = ChatOpenAI(model="gpt-4o-mini", temperature=0.5)
    return llm_instance.invoke(prompt).content


@app.post("/api/topic/explain")
async def api_explain_topic(payload: ExplainTopicRequest):
    """
    Fetches FAISS content and returns a rich English markdown explanation from caching or LLM.
    """
    # 1. Try cache first (only if bypass_cache is False)
    if not payload.bypass_cache:
        cached = get_cached_explanation(payload.subject, payload.level, payload.topic)
        if cached:
            return {"explanation": cached}

    try:
        # 2. Perform explanation in English
        explanation = fetch_explanation_en(payload.topic, payload.level, payload.subject)
        save_cached_explanation(payload.subject, payload.level, payload.topic, explanation)
        return {"explanation": explanation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate explanation: {str(e)}")

@app.post("/api/topic/quiz/generate", dependencies=[Depends(rate_limit_quiz)])
async def api_generate_topic_quiz(payload: GenerateTopicQuizRequest):
    """
    Generates 3 topic multiple choice questions with FAISS. Protects from replays using attempt tokens.
    """
    try:
        res = quiz_service.generate_topic_quiz(
            subject=payload.subject,
            level=payload.level,
            topic=payload.topic,
            bypass_cache=payload.bypass_cache
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate quiz: {str(e)}")

@app.post("/api/topic/quiz/submit")
async def api_submit_topic_quiz(payload: SubmitTopicQuizRequest):
    """
    Submits and evaluates a topic quiz. Requires a valid single-use attempt_token for security.
    """
    # 1. Anti-replay check
    valid = quiz_service.verify_and_consume_token(
        token=payload.attempt_token,
        subject=payload.subject,
        level=payload.level,
        topic=payload.topic
    )
    
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired attempt token. Quiz has already been submitted."
        )

    # 2. Evaluate answers
    eval_result = quiz_service.evaluate_quiz_answers(payload.questions, payload.answers)
    score = eval_result["score"]
    
    # 3. Save attempts and calculate rolling average
    stats = progress_service.record_attempt(
        learner_id=payload.learner_id,
        subject=payload.subject,
        level=payload.level,
        topic=payload.topic,
        score=score,
        attempt_token=payload.attempt_token
    )

    # 4. Save to historical logs
    conn = get_connection()
    cursor = conn.cursor()
    for q, ans in zip(payload.questions, payload.answers):
        cursor.execute("""
            INSERT INTO quiz_history (learner_id, subject, level, topic, question, learner_answer, correct_answer, score, feedback)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            payload.learner_id, 
            payload.subject, 
            payload.level, 
            payload.topic, 
            q["question"], 
            ans, 
            q["correct_answer"], 
            score, 
            eval_result["status"]
        ))
    conn.commit()
    conn.close()

    return {
        "score": score,
        "grade_status": eval_result["status"],
        "attempt_count": stats["attempt_count"],
        "rolling_average": stats["rolling_average"],
        "completed": stats["completed"],
        "wrong_questions": eval_result["wrong_questions"]
    }

@app.post("/api/level/verify")
async def api_verify_level(payload: VerifyLevelRequest):
    """
    Verifies if all level requirements are met, and handles user promotion.
    """
    try:
        result = progress_service.check_level_progression(
            learner_id=payload.learner_id,
            subject=payload.subject,
            level=payload.level
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/reset")
async def api_soft_reset(payload: SoftResetRequest):
    """
    Performs soft reset: archives active records but preserves logs for reports.
    """
    try:
        progress_service.soft_reset(payload.learner_id, payload.subject)
        return {"status": "success", "message": "Soft reset completed successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reset failed: {str(e)}")

@app.get("/api/reports")
async def api_get_reports(learner_id: str):
    """
    Compiles complete historical stats including milestones and attempts trends.
    """
    try:
        report = progress_service.compile_historical_report(learner_id)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/support/ticket")
async def api_submit_support_ticket(payload: SupportTicketRequest):
    """
    Submits a support ticket/report. Saves to SQLite and attempts to send email.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO support_tickets (learner_id, email, category, message)
            VALUES (?, ?, ?, ?)
        """, (payload.learner_id, payload.email, payload.category, payload.message))
        conn.commit()
        conn.close()

        # Print ticket info to server console/logs
        print(f"\n[SUPPORT TICKET] New report from {payload.learner_id} ({payload.email or 'No email'}):")
        print(f"Category: {payload.category}")
        print(f"Message: {payload.message}\n")

        # Optional SMTP email dispatch
        smtp_server = os.getenv("SMTP_SERVER")
        smtp_port = os.getenv("SMTP_PORT")
        smtp_user = os.getenv("SMTP_USER")
        smtp_password = os.getenv("SMTP_PASSWORD")
        support_email = os.getenv("SUPPORT_EMAIL")

        if smtp_server and smtp_port and smtp_user and smtp_password and support_email:
            try:
                import smtplib
                from email.mime.text import MIMEText
                
                body = f"Support Ticket Details:\n\nLearner ID: {payload.learner_id}\nEmail: {payload.email or 'N/A'}\nCategory: {payload.category}\nMessage:\n{payload.message}"
                msg = MIMEText(body)
                msg['Subject'] = f"[Support Ticket] {payload.category} - {payload.learner_id}"
                msg['From'] = smtp_user
                msg['To'] = support_email

                with smtplib.SMTP(smtp_server, int(smtp_port)) as server:
                    server.starttls()
                    server.login(smtp_user, smtp_password)
                    server.send_message(msg)
                print("Support email dispatched successfully via SMTP.")
            except Exception as email_err:
                print(f"Failed to send support SMTP email: {email_err}")

        return {"status": "success", "message": "Support ticket submitted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit ticket: {str(e)}")


# ─────────────────────────────────────────────────────────────────────────────
# Classmate's Integrated Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "message": "AI Tutoring Agent API is running.",
        "endpoints": {
            "chat": "POST /chat",
            "progress": "GET /progress/{learner_id}",
            "generate_assessment": "GET /assessment/generate/{path}",
            "submit_assessment": "POST /assessment/submit",
            "get_session": "GET /session/{learner_id}",
            "clear_session": "DELETE /session/{learner_id}",
        },
    }


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Chat endpoint:
    - Receives learner message
    - Retrieves relevant knowledge from FAISS Vector DB
    - Stores conversation in learner session
    """

    if not request.learner_id.strip():
        raise HTTPException(status_code=400, detail="learner_id is required.")

    if not request.message.strip():
        raise HTTPException(status_code=400, detail="message is required.")

    learner_id = request.learner_id

    if learner_id not in learner_sessions:
        learner_sessions[learner_id] = []

    try:
        raw_results = retrieve_knowledge(
            query=request.message,
            language=request.language,
            level=request.level,
            k=request.top_k,
        )

        # If vector_store.py returns a dictionary like:
        # {"status": "success", "query": "...", "results": [...]}
        if isinstance(raw_results, dict) and "results" in raw_results:
            retrieved_context = normalize_retrieved_context(raw_results["results"])
        else:
            retrieved_context = normalize_retrieved_context(raw_results)

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Retrieval failed: {str(error)}"
        )

    # Let's generate an intelligent response using the classmate's tutor agent
    try:
        from src.agent.agent import run_tutor_agent
        agent_res = run_tutor_agent(request.message, request.learner_id)
        reply = agent_res.get("output", "No response generated by agent.")
    except Exception as error:
        # Fallback
        if retrieved_context:
            first_result = retrieved_context[0]
            content = first_result.get("content", "")
            reply = f"Here is an explanation: {content[:500]}..."
        else:
            reply = "I'm sorry, I couldn't find any relevant content in my knowledge base. Can you please rephrase?"

    learner_sessions[learner_id].append({
        "role": "user",
        "message": request.message,
    })

    learner_sessions[learner_id].append({
        "role": "assistant",
        "message": reply,
    })

    return {
        "learner_id": learner_id,
        "reply": reply,
        "retrieved_context": retrieved_context,
        "session_history": learner_sessions[learner_id],
    }


@app.get("/progress/{learner_id}")
def progress(learner_id: str):
    """
    Progress endpoint:
    - Reads learner progress from SQLite using get_progress()
    """

    if not learner_id.strip():
        raise HTTPException(status_code=400, detail="learner_id is required.")

    progress_data = get_progress(learner_id)

    if not progress_data.get("learner"):
        raise HTTPException(
            status_code=404,
            detail=f"No learner found with learner_id: {learner_id}",
        )

    return progress_data


@app.get("/assessment/generate/{path}")
def generate_assessment(path: str):
    """
    Generate assessment quiz through the backend.

    This connects FastAPI with assessment_quiz.py instead of running
    assessment_quiz.py manually from the terminal.
    """

    if not path.strip():
        raise HTTPException(status_code=400, detail="path is required.")

    try:
        from src.agent.assessment_quiz import generate_assessment_quiz

        quiz = generate_assessment_quiz(path)

        return {
            "message": "Assessment quiz generated successfully.",
            "path": path,
            "quiz": quiz
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Assessment generation failed: {str(error)}"
        )


@app.post("/assessment/submit")
def submit_assessment(request: AssessmentSubmitRequest):
    """
    Submit assessment answers through the backend.
    """

    if not request.learner_id.strip():
        raise HTTPException(status_code=400, detail="learner_id is required.")

    if not request.name.strip():
        raise HTTPException(status_code=400, detail="name is required.")

    if not request.email.strip():
        raise HTTPException(status_code=400, detail="email is required.")

    if not request.quiz:
        raise HTTPException(status_code=400, detail="quiz is required.")

    if not request.user_answers:
        raise HTTPException(status_code=400, detail="user_answers is required.")

    try:
        from src.agent.assessment_quiz import evaluate_assessment, determine_level
        from src.agent.learning_plan import update_learning_path
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Assessment tools import failed: {str(error)}"
        )

    try:
        assessment_result = evaluate_assessment(
            request.quiz,
            request.user_answers
        )

        scores = assessment_result["scores"]

        level = determine_level(
            scores["beginner"],
            scores["intermediate"],
            scores["advanced"]
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Assessment evaluation failed: {str(error)}"
        )


    try:
        learning_path_result = update_learning_path(
            learner_id=request.learner_id,
            name=request.name,
            email=request.email,
            skill_level=level,
            goal=request.goal or "Learn Python and AI basics",
            wrong_questions=assessment_result["wrong_questions"],
            path=request.path
        )

    except Exception as error:
        learning_path_result = {
            "status": "failed",
            "message": f"Learning path update failed: {str(error)}"
        }

    try:
        progress_data = get_progress(request.learner_id)

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Progress retrieval failed: {str(error)}"
        )

    return {
        "message": "Assessment submitted successfully.",
        "learner_id": request.learner_id,
        "scores": scores,
        "level": level,
        "wrong_questions_count": len(assessment_result["wrong_questions"]),
        "wrong_questions": assessment_result["wrong_questions"],
        "evaluated_answers": assessment_result.get("evaluated_answers", []),
        "learning_path": learning_path_result,
        "progress": progress_data
    }


@app.get("/session/{learner_id}")
def get_session(learner_id: str):
    """
    Get learner session history.
    """

    if not learner_id.strip():
        raise HTTPException(status_code=400, detail="learner_id is required.")

    return {
        "learner_id": learner_id,
        "session_history": learner_sessions.get(learner_id, []),
    }


@app.delete("/session/{learner_id}")
def clear_session(learner_id: str):
    """
    Clear learner session history.
    """

    if not learner_id.strip():
        raise HTTPException(status_code=400, detail="learner_id is required.")

    learner_sessions.pop(learner_id, None)

    return {
        "message": f"Session cleared for learner_id: {learner_id}"
    }

# ─────────────────────────────────────────────────────────────────────────────
# Phase 1 — Badge System
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/badges/{learner_id}")
def get_badges(learner_id: str):
    """Return all badges for a learner with earned/locked status."""
    if not learner_id.strip():
        raise HTTPException(status_code=400, detail="learner_id is required.")
    badges = sync_badges(learner_id)
    github = get_github_connection(learner_id)
    return {
        "badges": badges,
        "github_connected": github is not None,
        "github_username": github["github_username"] if github else None,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Phase 2 — GitHub OAuth
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/github/connect")
def github_connect(learner_id: str):
    """Redirect learner to GitHub OAuth authorization page."""
    if not GITHUB_CLIENT_ID:
        raise HTTPException(status_code=500, detail="GitHub OAuth not configured.")
    scope = "user:email read:user"
    github_auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={GITHUB_CLIENT_ID}"
        f"&redirect_uri={GITHUB_CALLBACK_URL}"
        f"&scope={scope}"
        f"&state={learner_id}"
    )
    return RedirectResponse(url=github_auth_url)


@app.get("/github/callback")
async def github_callback(code: str, state: str):
    """Handle GitHub OAuth callback — exchange code for token and save."""
    learner_id = state

    # Exchange code for access token
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": GITHUB_CALLBACK_URL,
            },
            headers={"Accept": "application/json"},
        )
        token_data = token_resp.json()
        access_token = token_data.get("access_token")

        if not access_token:
            return RedirectResponse(
                url=f"{FRONTEND_URL}?github_error=token_failed"
            )

        # Get GitHub username
        user_resp = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        github_user = user_resp.json()
        github_username = github_user.get("login", "")

    # Save to DB
    save_github_connection(learner_id, github_username, access_token)

    return RedirectResponse(
        url=f"{FRONTEND_URL}?github_connected=true&github_user={github_username}"
    )


class PushBadgeRequest(BaseModel):
    learner_id: str
    badge_id: str
    badge_title: str
    badge_emoji: str
    badge_color: str
    subject: Optional[str] = None


@app.post("/github/push-badge")
async def push_badge_to_github(req: PushBadgeRequest):
    """Push an earned badge to the learner's GitHub Profile README."""
    github = get_github_connection(req.learner_id)
    if not github:
        raise HTTPException(status_code=400, detail="GitHub not connected.")

    access_token = github["github_access_token"]
    username = github["github_username"]

    badge_markdown = (
        f"\n\n<!-- evolyn-badge:{req.badge_id} -->\n"
        f"![{req.badge_title}](https://img.shields.io/badge/"
        f"{req.badge_title.replace(' ', '%20')}-"
        f"{req.badge_color.replace('#', '')}"
        f"?style=for-the-badge&logo=github&logoColor=white)\n"
        f"<!-- evolyn-badge-end -->"
    )

    async with httpx.AsyncClient() as client:
        # Check if profile README repo exists
        repo_url = f"https://api.github.com/repos/{username}/{username}/contents/README.md"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
        }
        get_resp = await client.get(repo_url, headers=headers)

        if get_resp.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail=f"GitHub profile README not found. Create a repo named '{username}' with a README.md first."
            )

        readme_data = get_resp.json()
        import base64
        current_content = base64.b64decode(readme_data["content"]).decode("utf-8")
        sha = readme_data["sha"]

        # Avoid duplicates
        tag = f"<!-- evolyn-badge:{req.badge_id} -->"
        if tag in current_content:
            return {"status": "already_pushed", "message": "Badge already on GitHub profile."}

        new_content = current_content + badge_markdown
        new_content_encoded = base64.b64encode(new_content.encode("utf-8")).decode("utf-8")

        update_resp = await client.put(
            repo_url,
            headers=headers,
            json={
                "message": f"Add Evolyn badge: {req.badge_title}",
                "content": new_content_encoded,
                "sha": sha,
            },
        )

        if update_resp.status_code not in (200, 201):
            raise HTTPException(status_code=500, detail="Failed to update GitHub README.")

    return {
        "status": "success",
        "message": f"Badge '{req.badge_title}' pushed to @{username}'s GitHub profile!",
        "github_url": f"https://github.com/{username}",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Phase 3 — AI Career Hub
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/career/{learner_id}")
def get_career_recommendations(learner_id: str):
    """Generate AI-powered career recommendations for a learner."""
    if not learner_id.strip():
        raise HTTPException(status_code=400, detail="learner_id is required.")
    try:
        result = generate_career_recommendations(learner_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Career generation failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
