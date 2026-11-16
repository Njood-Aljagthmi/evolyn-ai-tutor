from db import get_connection


def create_tables():
    connection = get_connection()
    cursor = connection.cursor()

    # --------------------------------------------------
    # Learner Profile
    # --------------------------------------------------

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS learner_profile (
        learner_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        goal TEXT,
        skill_level TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # --------------------------------------------------
    # Learning Plan
    # --------------------------------------------------

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS learning_plan (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        learner_id TEXT NOT NULL,

        subject TEXT NOT NULL,

        current_level TEXT NOT NULL,

        plan_title TEXT,

        current_topic TEXT,

        recommended_next_step TEXT,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (learner_id)
            REFERENCES learner_profile (learner_id)
    )
    """)

    # --------------------------------------------------
    # Learning Progress
    # --------------------------------------------------

    cursor.execute("""
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

        FOREIGN KEY (learner_id)
            REFERENCES learner_profile (learner_id)
    )
    """)

    # --------------------------------------------------
    # Topic Completion
    # --------------------------------------------------

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS topic_completion (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        learner_id TEXT NOT NULL,

        subject TEXT NOT NULL,

        level TEXT NOT NULL,

        topic TEXT NOT NULL,

        quiz_score REAL,

        completed INTEGER DEFAULT 0,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (learner_id)
            REFERENCES learner_profile (learner_id)
    )
    """)

    # --------------------------------------------------
    # Quiz History
    # --------------------------------------------------

    cursor.execute("""
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

        FOREIGN KEY (learner_id)
            REFERENCES learner_profile (learner_id)
    )
    """)

    # --------------------------------------------------
    # Weak Areas
    # --------------------------------------------------

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS weak_areas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        learner_id TEXT NOT NULL,

        subject TEXT,

        level TEXT,

        topic TEXT,

        weakness TEXT,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (learner_id)
            REFERENCES learner_profile (learner_id)
    )
    """)

    # --------------------------------------------------
    # Assessment Results
    # --------------------------------------------------

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS assessment_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        learner_id TEXT NOT NULL,

        subject TEXT NOT NULL,

        beginner_score INTEGER,

        intermediate_score INTEGER,

        advanced_score INTEGER,

        assigned_level TEXT,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (learner_id)
            REFERENCES learner_profile (learner_id)
    )
    """)

    # --------------------------------------------------
    # Quiz Cache & Tokens
    # --------------------------------------------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cached_questions (
        cache_key TEXT PRIMARY KEY,
        questions_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS active_attempt_tokens (
        token TEXT PRIMARY KEY,
        subject TEXT,
        level TEXT,
        topic TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # --------------------------------------------------
    # Explanation Cache
    # --------------------------------------------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cached_explanations (
        key TEXT PRIMARY KEY,
        content TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # --------------------------------------------------
    # Progress & Attempts tracking
    # --------------------------------------------------
    cursor.execute("""
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

    cursor.execute("""
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

    cursor.execute("""
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

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS github_connections (
        learner_id TEXT PRIMARY KEY,
        github_username TEXT,
        github_access_token TEXT,
        connected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (learner_id) REFERENCES learner_profile (learner_id)
    )
    """)

    cursor.execute("""
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

    connection.commit()
    connection.close()


if __name__ == "__main__":
    create_tables()
    print("SQLite database and tables created successfully.")