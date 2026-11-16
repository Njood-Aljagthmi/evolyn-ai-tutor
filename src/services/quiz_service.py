import os
import sys
import json
import uuid
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parents[1]
sys.path.append(str(ROOT_DIR))
sys.path.append(str(ROOT_DIR / "database"))

from db import get_connection
from src.services.rag_service import retrieve_knowledge_cached

from typing import List, Dict, Any, Optional

from src.agent.evaluate_answer import normalize_choice, evaluate_answer

MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


class QuizService:
    def __init__(self):
        self.llm = ChatOpenAI(model=MODEL_NAME, temperature=0.7)

    def _generate_cache_key(self, prefix: str, subject: str, level: str = "", topic: str = "", salt: str = "") -> str:
        """
        Create a unique MD5 hash for caching questions.
        """
        raw_key = f"{prefix}_{subject}_{level}_{topic}_{salt}"
        return hashlib.md5(raw_key.encode('utf-8')).hexdigest()

    def _get_cached_questions(self, cache_key: str) -> List[Dict[str, Any]]:
        """
        Retrieve cached questions from DB if present.
        """
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cached_questions (
                cache_key TEXT PRIMARY KEY,
                questions_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        cursor.execute("SELECT questions_json FROM cached_questions WHERE cache_key = ?", (cache_key,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            try:
                return json.loads(row["questions_json"])
            except Exception:
                return None
        return None

    def _save_cached_questions(self, cache_key: str, questions: List[Dict[str, Any]]):
        """
        Save generated questions to the cache.
        """
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cached_questions (
                cache_key TEXT PRIMARY KEY,
                questions_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        cursor.execute("""
            INSERT OR REPLACE INTO cached_questions (cache_key, questions_json)
            VALUES (?, ?)
        """, (cache_key, json.dumps(questions)))
        conn.commit()
        conn.close()

    def generate_assessment(self, subject: str) -> Dict[str, Any]:
        """
        Generates 12 assessment questions: 4 beginner, 4 intermediate, 4 advanced.
        Uses a random salt so they are generated fresh every time.
        """
        salt = str(uuid.uuid4())[:8]
        cache_key = self._generate_cache_key("assessment", subject, salt=salt)
        
        # Cache miss: Generate dynamically every time to ensure fresh questions
        quiz = {}
        all_questions = []

        topics_by_level = {
            "beginner": ["variables", "strings", "lists", "functions"],
            "intermediate": ["functions", "object oriented programming", "classes"],
            "advanced": ["advanced programming concepts", "decorators", "error handling"]
        }

        for level, topics in topics_by_level.items():
            # 1. FAISS retrieval FIRST
            combined_content = []
            for topic in topics:
                res = retrieve_knowledge_cached(
                    query=f"{subject} {topic}",
                    language=subject,
                    level=level,
                    k=2
                )
                for item in res["results"]:
                    combined_content.append(item["content"])
            
            content_text = "\n\n".join(combined_content)
            
            # 2. Call LLM ONLY for formatting and refinement
            questions = self._generate_questions_with_llm(content_text, level, 4, subject=subject)
            quiz[level] = questions
            all_questions.extend(questions)

        # Save all generated questions to the cache
        self._save_cached_questions(cache_key, all_questions)
        return quiz
    def generate_topic_quiz(self, subject: str, level: str, topic: str, bypass_cache: bool = False) -> Dict[str, Any]:
        """
        Generates 3 topic questions using FAISS content.
        Always uses a random salt so questions are dynamically generated and fresh every time.
        """
        salt = str(uuid.uuid4())[:8]
        cache_key = self._generate_cache_key("topic", subject, level, topic, salt)

        # 1. FAISS retrieval
        res = retrieve_knowledge_cached(
            query=f"{subject} {topic}",
            language=subject,
            level=level,
            k=3
        )
        content_text = "\n\n".join(c["content"] for c in res["results"])

        # 2. LLM formatting
        questions = self._generate_questions_with_llm(content_text, level, 3, topic, subject=subject)
        
        # Save to cache if not bypassing or save it as a new salt variation
        self._save_cached_questions(cache_key, questions)
        
        attempt_token = self._create_attempt_token(subject, level, topic)
        return {"questions": questions, "attempt_token": attempt_token}

    def _generate_questions_with_llm(self, context: str, difficulty: str, count: int, topic_hint: str = "", subject: str = "python") -> List[Dict[str, Any]]:
        """
        Prompts LLM to structure multiple choice questions from context.
        """
        prompt = f"""
You are an expert programming instructor for the {subject} programming language.
Based strictly on the provided context, generate exactly {count} multiple-choice questions.

CRITICAL REQUIREMENT:
- All questions, concepts, terms, syntax, and options MUST be strictly about {subject}.
- DO NOT generate questions, examples, explanations, or options referencing other programming languages (e.g. if the subject is Python, do NOT mention Java, C++, C, or JavaScript keywords, syntax, or paradigms).
- Maintain the context of the programming language '{subject}' at all times.

Requirements:
- Difficulty Level: {difficulty}
- Topic: {topic_hint if topic_hint else "Extract from context"}
- Return ONLY a valid JSON object matching the schema:
{{
  "questions": [
    {{
      "question": "Clear question text?",
      "options": {{
        "A": "Option text A",
        "B": "Option text B",
        "C": "Option text C",
        "D": "Option text D"
      }},
      "correct_answer": "A",
      "difficulty": "{difficulty}",
      "topic": "topic_name"
    }}
  ]
}}

Formatting Rules:
- Only ONE correct answer.
- correct_answer must be exactly one letter: A, B, C, or D.
- Never use options like "All of the above", "None of the above", or combined options (e.g. "Both A and B").
- All options must be clear, distinct, and standalone.

Context:
{context}
"""
        try:
            response = self.llm.invoke(prompt)
            clean_json = (
                response.content
                .replace("```json", "")
                .replace("```", "")
                .strip()
            )
            data = json.loads(clean_json)
            questions = data.get("questions", data)
            if isinstance(questions, dict):
                questions = [questions]
            return questions[:count]
        except Exception as e:
            # Fallback mock questions in case of API issues to maintain stability
            logger.error("Error generating questions: %s", str(e))
            return [
                {
                    "question": f"Verify key concept of {topic_hint or 'programming'} under {difficulty} context.",
                    "options": {
                        "A": "Valid statement representation",
                        "B": "Invalid statement representation",
                        "C": "Compilation error side effect",
                        "D": "Memory overflow condition"
                    },
                    "correct_answer": "A",
                    "difficulty": difficulty,
                    "topic": topic_hint or "general"
                }
                for _ in range(count)
            ]

    def _create_attempt_token(self, subject: str, level: str, topic: str) -> str:
        """
        Generate and register a secure single-use token in the database to prevent replay submissions.
        """
        token = str(uuid.uuid4())
        conn = get_connection()
        cursor = conn.cursor()
        # Create table for active tokens if not exists (fail-safe)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS active_attempt_tokens (
                token TEXT PRIMARY KEY,
                subject TEXT,
                level TEXT,
                topic TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            INSERT INTO active_attempt_tokens (token, subject, level, topic)
            VALUES (?, ?, ?, ?)
        """, (token, subject, level, topic))
        conn.commit()
        conn.close()
        return token

    def verify_and_consume_token(self, token: str, subject: str, level: str, topic: str) -> bool:
        """
        Checks if an attempt token is active and consumes it.
        """
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM active_attempt_tokens WHERE token = ? AND subject = ? AND level = ? AND topic = ?", 
                       (token, subject, level, topic))
        exists = cursor.fetchone()
        
        if exists:
            cursor.execute("DELETE FROM active_attempt_tokens WHERE token = ?", (token,))
            conn.commit()
            conn.close()
            return True
        conn.close()
        return False

    def evaluate_quiz_answers(self, questions: List[Dict[str, Any]], user_answers: List[str]) -> Dict[str, Any]:
        """
        Evaluates answers and calculates the percentage score.
        Enforces three-tier grading:
        - 70-100: PASS
        - 50-69: RETRY REQUIRED
        - 0-49: FAIL
        """
        correct_count = 0
        wrong_questions = []

        for q, user_ans in zip(questions, user_answers):
            res = evaluate_answer(
                question=q["question"],
                options=q["options"],
                learner_answer=user_ans,
                correct_answer=q["correct_answer"],
                topic=q.get("topic", "general"),
                difficulty=q.get("difficulty", "beginner")
            )
            
            if res["is_correct"]:
                correct_count += 1
            else:
                wrong_questions.append({
                    "question": res["question"],
                    "options": res["options"],
                    "correct_answer": res["correct_answer"],
                    "learner_answer": res["learner_answer"],
                    "difficulty": res["difficulty"],
                    "topic": res["topic"]
                })

        total = len(questions)
        score_percent = round((correct_count / total) * 100, 2) if total else 0.0

        if score_percent >= 70:
            grade_status = "PASS"
        elif score_percent >= 50:
            grade_status = "RETRY"
        else:
            grade_status = "FAIL"

        return {
            "score": score_percent,
            "correct": correct_count,
            "total": total,
            "status": grade_status,
            "wrong_questions": wrong_questions
        }
