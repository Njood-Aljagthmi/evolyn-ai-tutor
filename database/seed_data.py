from db import get_connection


def insert_sample_data():
    connection = get_connection()
    cursor = connection.cursor()

    learner_id = "student_1"

    # Remove old sample data to avoid duplicates
    cursor.execute("DELETE FROM learning_plan WHERE learner_id = ?", (learner_id,))
    cursor.execute("DELETE FROM learning_progress WHERE learner_id = ?", (learner_id,))
    cursor.execute("DELETE FROM quiz_history WHERE learner_id = ?", (learner_id,))
    cursor.execute("DELETE FROM weak_areas WHERE learner_id = ?", (learner_id,))

    cursor.execute("""
    INSERT OR REPLACE INTO learner_profile
    (learner_id, name, email, goal, skill_level)
    VALUES (?, ?, ?, ?, ?)
    """, (
        learner_id,
        "Njood",
        "njood@example.com",
        "Learn Python and AI basics",
        "Beginner"
    ))

    cursor.execute("""
    INSERT INTO learning_plan
    (learner_id, plan_title, current_topic, recommended_next_step)
    VALUES (?, ?, ?, ?)
    """, (
        learner_id,
        "Python Basics Learning Plan",
        "Python Loops",
        "Practice for loops and while loops"
    ))

    cursor.execute("""
    INSERT INTO learning_progress
    (learner_id, completed_topic, current_topic, status)
    VALUES (?, ?, ?, ?)
    """, (
        learner_id,
        "Python Variables",
        "Python Loops",
        "in_progress"
    ))

    cursor.execute("""
    INSERT INTO quiz_history
    (learner_id, topic, question, learner_answer, correct_answer, score, feedback)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        learner_id,
        "Python Variables",
        "What is a variable?",
        "A place to store data",
        "A named container used to store data",
        85,
        "Good answer, but add more detail."
    ))

    cursor.execute("""
    INSERT INTO weak_areas
    (learner_id, topic, weakness)
    VALUES (?, ?, ?)
    """, (
        learner_id,
        "Python Loops",
        "Needs more practice with loop syntax."
    ))

    connection.commit()
    connection.close()


if __name__ == "__main__":
    insert_sample_data()
    print("Sample data inserted successfully.")