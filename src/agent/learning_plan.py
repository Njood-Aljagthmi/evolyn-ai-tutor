"""
learning_path.py
----------------
Adaptive learning path: reads wrong_questions, finds weak topics,
generates a new plan via LLM, saves via update_memory.
"""

from __future__ import annotations
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

DATABASE_DIR = Path(__file__).resolve().parents[2] / "database"
sys.path.append(str(DATABASE_DIR))

from src.rag.vector_store import retrieve_knowledge
from src.agent.memory_tool import update_memory

load_dotenv()
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


# ─────────────────────────────────────────────────────────────────────────────
# 1. استخرج المواضيع الضعيفة من الأخطاء
# ─────────────────────────────────────────────────────────────────────────────

def extract_weak_topics(wrong_questions: List[Dict]) -> List[Dict]:
    topic_counts: Dict[str, Dict] = {}
    for item in wrong_questions:
        topic = item.get("topic", "unknown")
        diff  = item.get("difficulty", "beginner")
        if topic not in topic_counts:
            topic_counts[topic] = {"count": 0, "difficulty": diff}
        topic_counts[topic]["count"] += 1

    weak = [
        {"topic": t, "mistake_count": d["count"], "difficulty": d["difficulty"]}
        for t, d in topic_counts.items()
    ]
    weak.sort(key=lambda x: x["mistake_count"], reverse=True)
    return weak


# ─────────────────────────────────────────────────────────────────────────────
# 2. جيب محتوى RAG لكل موضوع ضعيف
# ─────────────────────────────────────────────────────────────────────────────

def fetch_content_for_weak_topics(weak_topics: List[Dict], path: str) -> Dict[str, str]:
    content_map: Dict[str, str] = {}
    for w in weak_topics:
        result = retrieve_knowledge(
            query=f"{path} {w['topic']}",
            language=path.lower(),
            level=w["difficulty"].lower(),
            k=3,
        )
        chunks = result.get("results", [])
        content_map[w["topic"]] = "\n\n".join(c["content"] for c in chunks) if chunks else ""
    return content_map


# ─────────────────────────────────────────────────────────────────────────────
# 3. ولّد خطة تكيفية بالـ LLM
# ─────────────────────────────────────────────────────────────────────────────

def generate_topics_for_level(path: str, level: str) -> List[str]:
    """
    Generate a list of 4-6 key topics for the given programming subject and skill level using ChatOpenAI.
    """
    llm = ChatOpenAI(model=MODEL_NAME, temperature=0.3)

    system = SystemMessage(content=(
        "You are an expert programming tutor curriculum planner.\n"
        "Generate a list of 4-6 key topics for the given programming subject and skill level.\n"
        "Return ONLY a JSON list of strings (no markdown blocks, no extra text, just raw JSON).\n"
        "Each string should be a short, clean topic name (e.g., 'variables', 'loops', 'decorators').\n"
        "The language must be English, in lowercase.\n"
        "Example output:\n"
        "[\"variables\", \"strings\", \"lists\", \"loops\"]"
    ))

    human = HumanMessage(content=f"Subject: {path} | Level: {level}")

    try:
        response = llm.invoke([system, human])
        text = response.content.strip().replace("```json", "").replace("```", "").strip()
        topics = json.loads(text)
        if isinstance(topics, list) and all(isinstance(t, str) for t in topics):
            return [t.strip().lower() for t in topics]
    except Exception as e:
        print(f"Error generating topics dynamically: {e}")

    # Fallback default topics if LLM fails
    defaults = {
        "beginner": {
            "python": ["variables", "strings", "lists", "functions", "loops"],
            "java": ["variables and types", "operators", "conditionals", "loops", "arrays", "methods"]
        },
        "intermediate": {
            "python": ["classes and objects", "generators", "decorators", "context managers", "exception handling"],
            "java": ["classes and objects", "inheritance and polymorphism", "interfaces and abstract classes", "exceptions", "generics"]
        },
        "advanced": {
            "python": ["asyncio", "threading and multiprocessing", "metaclasses", "design patterns", "memory management"],
            "java": ["concurrency and threads", "jvm internals and memory", "reflection and annotations", "design patterns", "streams api"]
        }
    }
    subj_defaults = defaults.get(level.lower(), {})
    return subj_defaults.get(path.lower(), ["variables", "loops", "functions"])


def generate_adaptive_plan(
    learner_name: str,
    skill_level: str,
    goal: str,
    weak_topics: List[Dict],
    content_map: Dict[str, str],
) -> Dict[str, str]:
    llm = ChatOpenAI(model=MODEL_NAME, temperature=0.3)

    weak_lines = "\n".join(
        f"- {w['topic']} ({w['difficulty']}): {w['mistake_count']} mistake(s)"
        for w in weak_topics
    )

    top_topic      = weak_topics[0]["topic"] if weak_topics else None
    content_snippet = content_map.get(top_topic, "")[:600] if top_topic else ""

    system = SystemMessage(content=(
        "You are an adaptive learning coach for programming students.\n"
        "Given the learner's mistakes and study material, create a focused plan.\n"
        "Reply in EXACTLY this format (no extra text):\n"
        "PLAN_TITLE: <short title>\n"
        "CURRENT_TOPIC: <single topic to focus on now>\n"
        "NEXT_STEP: <one concrete action the learner should do>"
    ))

    human = HumanMessage(content=(
        f"Learner: {learner_name} | Level: {skill_level} | Goal: {goal}\n"
        f"Weak topics:\n{weak_lines}\n\n"
        f"Study material for '{top_topic}':\n{content_snippet}"
    ))

    response = llm.invoke([system, human])
    text = response.content.strip()

    plan: Dict[str, str] = {}
    for line in text.splitlines():
        if line.startswith("PLAN_TITLE:"):
            plan["plan_title"] = line.split(":", 1)[1].strip()
        elif line.startswith("CURRENT_TOPIC:"):
            plan["current_topic"] = line.split(":", 1)[1].strip()
        elif line.startswith("NEXT_STEP:"):
            plan["recommended_next_step"] = line.split(":", 1)[1].strip()

    plan.setdefault("plan_title", "Adaptive Learning Plan")
    plan.setdefault("current_topic", top_topic or "Review Basics")
    plan.setdefault("recommended_next_step", "Re-read the material and retry the quiz.")
    return plan


# ─────────────────────────────────────────────────────────────────────────────
# 4. الدالة الرئيسية
# ─────────────────────────────────────────────────────────────────────────────

def update_learning_path(
    learner_id: str,
    name: str,
    email: str,
    skill_level: str,
    goal: str,
    wrong_questions: List[Dict],
    path: str = "python",
) -> Dict[str, Any]:
    """
    استدعيها بعد evaluate_assessment مباشرة.
    """
    weak_topics = extract_weak_topics(wrong_questions)
    content_map = fetch_content_for_weak_topics(weak_topics, path)

    # 1. Generate standard topics for this level
    standard_topics = generate_topics_for_level(path, skill_level)

    # 2. Combine weakness topics and level topics
    # Keep weakness topics first, followed by standard topics, with no duplicates
    combined_topics = []
    for w in weak_topics:
        topic_name = w["topic"].strip()
        if topic_name not in combined_topics:
            combined_topics.append(topic_name)

    for s in standard_topics:
        if s.strip() not in combined_topics:
            combined_topics.append(s.strip())

    plan = generate_adaptive_plan(
        learner_name=name,
        skill_level=skill_level,
        goal=goal,
        weak_topics=weak_topics,
        content_map=content_map,
    )

    # Override next step to contain JSON of topics
    plan["recommended_next_step"] = json.dumps(combined_topics)

    update_memory(
        learner_id=learner_id,
        name=name,
        email=email,
        skill_level=skill_level,
        goal=goal,
        completed_topic="assessment",
        current_topic=combined_topics[0] if combined_topics else "Basics",
        wrong_questions=wrong_questions,
        subject=path,
    )

    return {
        "status": "success",
        "plan": plan,
        "weak_topics": weak_topics,
        "content_preview": {
            t: c[:300] for t, c in content_map.items() if c
        },
    }



# ─────────────────────────────────────────────────────────────────────────────
# اختبار سريع
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json
    from src.agent.assessment_quiz import (
        generate_assessment_quiz,
        evaluate_assessment,
        determine_level,
    )

    quiz = generate_assessment_quiz("python")
    sample_answers = {
        "beginner":     ["D", "D", "D", "D"],
        "intermediate": ["D", "D", "D", "D"],
        "advanced":     ["D", "D", "D", "D"],
    }

    assessment_result = evaluate_assessment(quiz, sample_answers)
    scores = assessment_result["scores"]
    level  = determine_level(scores["beginner"], scores["intermediate"], scores["advanced"])

    print("SCORES:", scores)
    print("LEVEL:", level)
    print("WRONG:", len(assessment_result["wrong_questions"]), "questions\n")

    result = update_learning_path(
        learner_id="student_1",
        name="Njood",
        email="njood@example.com",
        skill_level=level,
        goal="Learn Python and AI basics",
        wrong_questions=assessment_result["wrong_questions"],
        path="python",
    )

    print(json.dumps(result, indent=4, ensure_ascii=False))