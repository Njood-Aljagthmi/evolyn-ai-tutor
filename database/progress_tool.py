from typing import Any, Dict
try:
    from .db import get_connection
except ImportError:
    from db import get_connection


def get_progress(learner_id: str) -> Dict[str, Any]:
    """
    Retrieve learner profile, learning plan, quiz history,
    weak areas, and progress summary from SQLite.
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
    SELECT learner_id, name, email, goal, skill_level, created_at
    FROM learner_profile
    WHERE learner_id = ?
    """, (learner_id,))
    learner = cursor.fetchone()

    cursor.execute("""
    SELECT plan_title, current_topic, recommended_next_step, created_at
    FROM learning_plan
    WHERE learner_id = ?
    ORDER BY created_at DESC
    LIMIT 1
    """, (learner_id,))
    learning_plan = cursor.fetchone()

    cursor.execute("""
    SELECT completed_topic, current_topic, status, created_at
    FROM learning_progress
    WHERE learner_id = ?
    ORDER BY created_at DESC
    """, (learner_id,))
    progress_rows = cursor.fetchall()

    cursor.execute("""
    SELECT topic, question, learner_answer, correct_answer, score, feedback, created_at
    FROM quiz_history
    WHERE learner_id = ?
    ORDER BY created_at DESC
    """, (learner_id,))
    quiz_rows = cursor.fetchall()

    cursor.execute("""
    SELECT topic, weakness, created_at
    FROM weak_areas
    WHERE learner_id = ?
    ORDER BY created_at DESC
    """, (learner_id,))
    weak_rows = cursor.fetchall()

    connection.close()

    quiz_scores = [row["score"] for row in quiz_rows if row["score"] is not None]
    quiz_average = round(sum(quiz_scores) / len(quiz_scores), 2) if quiz_scores else 0

    completed_topics = [
        row["completed_topic"]
        for row in progress_rows
        if row["completed_topic"]
    ]

    current_topic = None
    if learning_plan:
        current_topic = learning_plan["current_topic"]
    elif progress_rows:
        current_topic = progress_rows[0]["current_topic"]

    return {
        "learner": dict(learner) if learner else None,
        "learning_plan": dict(learning_plan) if learning_plan else None,
        "completed_topics": completed_topics,
        "current_topic": current_topic,
        "quiz_history": [dict(row) for row in quiz_rows],
        "quiz_average": quiz_average,
        "weak_areas": [dict(row) for row in weak_rows],
    }


if __name__ == "__main__":
    import json

    result = get_progress("student_1")
    print(json.dumps(result, indent=4, ensure_ascii=False))