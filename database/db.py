import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "ai_tutor.db"

_schema_ensured = False


def get_connection():
    """
    Create and return a SQLite database connection.
    Auto-migrates schema on first call.
    """
    global _schema_ensured
    if not _schema_ensured:
        _ensure_schema()
        _schema_ensured = True
    connection = sqlite3.connect(DB_PATH, timeout=30.0)
    connection.row_factory = sqlite3.Row
    return connection


def _ensure_schema():
    """
    Auto-migration: creates any missing tables and adds any missing columns.
    Safe to run on every startup — uses CREATE IF NOT EXISTS and checks PRAGMA.
    """
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # ── Core tables ──────────────────────────────────────────────────────────

    cur.execute("""
        CREATE TABLE IF NOT EXISTS learner_profile (
            learner_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            goal TEXT,
            skill_level TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS learning_plan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            learner_id TEXT NOT NULL,
            subject TEXT NOT NULL,
            current_level TEXT NOT NULL,
            plan_title TEXT,
            current_topic TEXT,
            recommended_next_step TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (learner_id) REFERENCES learner_profile (learner_id)
        )
    """)
    
    

    cur.execute("""
        CREATE TABLE IF NOT EXISTS learning_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            learner_id TEXT NOT NULL,
            subject TEXT NOT NULL,
            current_level TEXT NOT NULL,
            completed_topic TEXT,
            current_topic TEXT,
            total_score REAL DEFAULT 0,
            course_completed INTEGER DEFAULT 0,
            status TEXT DEFAULT 'in_progress',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (learner_id) REFERENCES learner_profile (learner_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS topic_completion (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            learner_id TEXT NOT NULL,
            subject TEXT NOT NULL,
            level TEXT NOT NULL,
            topic TEXT NOT NULL,
            quiz_score REAL,
            completed INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (learner_id) REFERENCES learner_profile (learner_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS quiz_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            learner_id TEXT NOT NULL,
            subject TEXT,
            level TEXT,
            topic TEXT,
            question TEXT,
            learner_answer TEXT,
            correct_answer TEXT,
            score REAL,
            feedback TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (learner_id) REFERENCES learner_profile (learner_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS weak_areas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            learner_id TEXT NOT NULL,
            subject TEXT,
            level TEXT,
            topic TEXT,
            weakness TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (learner_id) REFERENCES learner_profile (learner_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS assessment_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            learner_id TEXT NOT NULL,
            subject TEXT NOT NULL,
            beginner_score INTEGER,
            intermediate_score INTEGER,
            advanced_score INTEGER,
            assigned_level TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (learner_id) REFERENCES learner_profile (learner_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS cached_questions (
            cache_key TEXT PRIMARY KEY,
            questions_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS active_attempt_tokens (
            token TEXT PRIMARY KEY,
            subject TEXT,
            level TEXT,
            topic TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS cached_explanations (
            key TEXT PRIMARY KEY,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS quiz_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            learner_id TEXT NOT NULL,
            subject TEXT NOT NULL,
            level TEXT NOT NULL,
            topic TEXT NOT NULL,
            score REAL NOT NULL,
            attempt_token TEXT,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (learner_id) REFERENCES learner_profile (learner_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS topic_summary (
            learner_id TEXT NOT NULL,
            subject TEXT NOT NULL,
            level TEXT NOT NULL,
            topic TEXT NOT NULL,
            attempt_count INTEGER DEFAULT 0,
            last_score REAL DEFAULT 0.0,
            rolling_average REAL DEFAULT 0.0,
            completed INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (learner_id, subject, level, topic),
            FOREIGN KEY (learner_id) REFERENCES learner_profile (learner_id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS support_tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            learner_id TEXT NOT NULL,
            email TEXT,
            category TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (learner_id) REFERENCES learner_profile (learner_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS learner_badges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            learner_id TEXT NOT NULL,
            badge_id TEXT NOT NULL,
            subject TEXT,
            earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(learner_id, badge_id),
            FOREIGN KEY (learner_id) REFERENCES learner_profile (learner_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS github_connections (
            learner_id TEXT PRIMARY KEY,
            github_username TEXT,
            github_access_token TEXT,
            connected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (learner_id) REFERENCES learner_profile (learner_id)
        )
    """)

    conn.commit()

    # ── Column migrations: add missing columns to existing tables ────────────

    _add_column_if_missing(cur, "learning_plan", "subject",       "TEXT")
    _add_column_if_missing(cur, "learning_plan", "current_level", "TEXT")

    conn.commit()
    conn.close()


def _add_column_if_missing(cur, table: str, column: str, col_type: str):
    """Add a column to a table only if it does not already exist."""
    cur.execute(f"PRAGMA table_info({table})")
    existing = [row[1] for row in cur.fetchall()]
    if column not in existing:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")


def initialize_learning_progress(learner_id: str, subject: str, current_level: str, current_topic: str):
    """
    Initialize progress tracking for a learner and subject.
    Prevents duplicates by updating if it already exists.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 1 FROM learning_progress
        WHERE learner_id = ? AND subject = ?
    """, (learner_id, subject))
    row = cursor.fetchone()

    if row:
        cursor.execute("""
            UPDATE learning_progress
            SET current_level = ?, current_topic = ?, course_completed = 0, status = 'in_progress'
            WHERE learner_id = ? AND subject = ?
        """, (current_level, current_topic, learner_id, subject))
    else:
        cursor.execute("""
            INSERT INTO learning_progress (learner_id, subject, current_level, current_topic, total_score, course_completed, status)
            VALUES (?, ?, ?, ?, 0.0, 0, 'in_progress')
        """, (learner_id, subject, current_level, current_topic))
    conn.commit()
    conn.close()


def initialize_topic_completion(learner_id: str, subject: str, level: str, topics: list):
    """
    Insert all generated topics into topic_completion, preventing duplicates.
    """
    conn = get_connection()
    cursor = conn.cursor()
    for topic in topics:
        cursor.execute("""
            SELECT 1 FROM topic_completion
            WHERE learner_id = ? AND subject = ? AND level = ? AND topic = ?
        """, (learner_id, subject, level, topic))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO topic_completion (learner_id, subject, level, topic, completed, quiz_score)
                VALUES (?, ?, ?, ?, 0, NULL)
            """, (learner_id, subject, level, topic))
    conn.commit()
    conn.close()


def record_quiz_attempt(learner_id: str, subject: str, level: str, topic: str, score: float, attempt_token: str = None):
    """
    Insert a record into quiz_attempts.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO quiz_attempts (learner_id, subject, level, topic, score, attempt_token, status)
        VALUES (?, ?, ?, ?, ?, ?, 'active')
    """, (learner_id, subject, level, topic, score, attempt_token))
    conn.commit()
    conn.close()


def mark_topic_completed(learner_id: str, subject: str, level: str, topic: str, score: float):
    """
    Update topic_completion.completed = 1 and topic_completion.quiz_score = latest score.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE topic_completion
        SET completed = 1, quiz_score = ?
        WHERE learner_id = ? AND subject = ? AND level = ? AND topic = ?
    """, (score, learner_id, subject, level, topic))
    conn.commit()
    conn.close()


def get_next_unfinished_topic(learner_id: str, subject: str, level: str) -> str:
    """
    Get the next unfinished topic for a learner, subject, and level.
    Returns the topic name, or 'completed' if all are finished.
    """
    import json
    conn = get_connection()
    cursor = conn.cursor()

    # Try loading from the learning plan first to preserve custom order
    cursor.execute("""
        SELECT recommended_next_step FROM learning_plan
        WHERE learner_id = ? AND subject = ? AND current_level = ?
        ORDER BY created_at DESC LIMIT 1
    """, (learner_id, subject, level))
    row = cursor.fetchone()

    plan_topics = []
    if row and row["recommended_next_step"]:
        try:
            plan_topics = json.loads(row["recommended_next_step"])
        except:
            pass

    if plan_topics:
        for topic in plan_topics:
            cursor.execute("""
                SELECT completed FROM topic_completion
                WHERE learner_id = ? AND subject = ? AND level = ? AND topic = ?
            """, (learner_id, subject, level, topic))
            comp_row = cursor.fetchone()
            if not comp_row or comp_row["completed"] == 0:
                conn.close()
                return topic
        conn.close()
        return "completed"

    # Fallback to insertion order in topic_completion
    cursor.execute("""
        SELECT topic FROM topic_completion
        WHERE learner_id = ? AND subject = ? AND level = ? AND completed = 0
        ORDER BY id ASC LIMIT 1
    """, (learner_id, subject, level))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row["topic"]
    return "completed"


def update_learning_progress(learner_id: str, subject: str):
    """
    Update learning_progress automatically:
    - current_topic should point to the next unfinished topic
    - total_score should be updated with the learner's average score across all quiz attempts
    - course_completed should be 1 if all topics for the learner and subject are completed
    """
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Fetch current level
    cursor.execute("""
        SELECT current_level FROM learning_progress
        WHERE learner_id = ? AND subject = ?
    """, (learner_id, subject))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return
    current_level = row["current_level"]

    # 2. Find the next unfinished topic across all levels
    cursor.execute("""
        SELECT level, topic FROM topic_completion
        WHERE learner_id = ? AND subject = ? AND completed = 0
        ORDER BY id ASC LIMIT 1
    """, (learner_id, subject))
    unfinished = cursor.fetchone()

    if unfinished:
        next_topic = unfinished["topic"]
        next_level = unfinished["level"]
        course_completed = 0
        status = "in_progress"
    else:
        # Check if there are any topics at all
        cursor.execute("""
            SELECT COUNT(*) FROM topic_completion
            WHERE learner_id = ? AND subject = ?
        """, (learner_id, subject))
        count = cursor.fetchone()[0]
        if count > 0:
            next_topic = "completed"
            next_level = current_level
            course_completed = 1
            status = "completed"
        else:
            next_topic = "start"
            next_level = current_level
            course_completed = 0
            status = "in_progress"

    # 3. Calculate average score
    cursor.execute("""
        SELECT AVG(score) FROM quiz_attempts
        WHERE learner_id = ? AND subject = ?
    """, (learner_id, subject))
    avg_row = cursor.fetchone()
    average_score = avg_row[0] if avg_row and avg_row[0] is not None else 0.0

    cursor.execute("""
        UPDATE learning_progress
        SET current_level = ?, current_topic = ?, total_score = ?, course_completed = ?, status = ?
        WHERE learner_id = ? AND subject = ?
    """, (next_level, next_topic, average_score, course_completed, status, learner_id, subject))

    conn.commit()
    conn.close()