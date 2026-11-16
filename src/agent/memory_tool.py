import sys
from pathlib import Path

DATABASE_DIR = Path(__file__).resolve().parents[2] / "database"
sys.path.append(str(DATABASE_DIR))

from db import get_connection


def update_memory(
    learner_id,
    name,
    email,
    skill_level,
    goal=None,
    completed_topic=None,
    current_topic=None,
    topic=None,
    score=None,
    feedback=None,
    wrong_questions=None,
    weak_topic=None,
    weakness=None,
    subject=None,
    total_score=None,
    **kwargs
):
    """
    Update learner memory in SQLite.

    Stores:
    - learner profile
    - completed/current topic progress
    - wrong questions only
    - weak areas
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
    INSERT OR REPLACE INTO learner_profile
    (learner_id, name, email, goal, skill_level)
    VALUES (?, ?, ?, ?, ?)
    """, (
        learner_id,
        name,
        email,
        goal,
        skill_level
    ))

    if completed_topic or current_topic:
        cursor.execute("""
        INSERT INTO learning_progress
        (learner_id, subject, current_level, completed_topic, current_topic, total_score, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            learner_id,
            subject or "python",
            skill_level or "beginner",
            completed_topic,
            current_topic,
            total_score or 0.0,
            "in_progress"
        ))

    if wrong_questions:
        seen_topics = set()

        for item in wrong_questions:
            question_topic = item.get("topic", topic)
            question_text = item.get("question")
            learner_answer = item.get("learner_answer")
            correct_answer = item.get("correct_answer")

            cursor.execute("""
            INSERT INTO quiz_history
            (learner_id, subject, level, topic, question, learner_answer, correct_answer, score, feedback)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                learner_id,
                subject or "python",
                skill_level or "beginner",
                question_topic,
                question_text,
                learner_answer,
                correct_answer,
                None,
                f"Needs review in {question_topic}"
            ))

            if question_topic and question_topic not in seen_topics:
                cursor.execute("""
                INSERT INTO weak_areas
                (learner_id, subject, level, topic, weakness)
                VALUES (?, ?, ?, ?, ?)
                """, (
                    learner_id,
                    subject or "python",
                    skill_level or "beginner",
                    question_topic,
                    f"Needs more practice in {question_topic}"
                ))

                seen_topics.add(question_topic)

    elif topic:
        cursor.execute("""
        INSERT INTO quiz_history
        (learner_id, subject, level, topic, question, learner_answer, correct_answer, score, feedback)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            learner_id,
            subject or "python",
            skill_level or "beginner",
            topic,
            None,
            None,
            None,
            score,
            feedback
        ))

    if weak_topic:
        cursor.execute("""
        INSERT INTO weak_areas
        (learner_id, subject, level, topic, weakness)
        VALUES (?, ?, ?, ?, ?)
        """, (
            learner_id,
            subject or "python",
            skill_level or "beginner",
            weak_topic,
            weakness or f"Needs more practice in {weak_topic}"
        ))

    connection.commit()
    connection.close()

    return {
        "status": "success",
        "message": "Learner memory updated successfully",
        "learner_id": learner_id
    }


if __name__ == "__main__":

    sample_wrong_questions = [
        {
            "difficulty": "beginner",
            "topic": "variables",
            "question": "What is a variable?",
            "options": {
                "A": "A named container",
                "B": "A loop",
                "C": "A function",
                "D": "A class"
            },
            "learner_answer": "B",
            "correct_answer": "A"
        },
        {
            "difficulty": "intermediate",
            "topic": "loops",
            "question": "What does a for loop do?",
            "options": {
                "A": "Stores data",
                "B": "Repeats code",
                "C": "Deletes variables",
                "D": "Creates a database"
            },
            "learner_answer": "A",
            "correct_answer": "B"
        }
    ]

    result = update_memory(
        learner_id="student_1",
        name="Njood",
        email="njood@example.com",
        skill_level="beginner",
        goal="Learn Python and AI basics",
        completed_topic="assessment",
        current_topic="variables",
        wrong_questions=sample_wrong_questions
    )

    print(result)