-- ============================================================
-- AI Tutoring Agent — PostgreSQL Database Schema
-- Memory System for Learner Profiles & Progress Tracking
-- ============================================================

-- 1. LEARNER PROFILE
-- Stores learner goals, skill level, and preferences
CREATE TABLE learner_profile (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    email           VARCHAR(150) UNIQUE NOT NULL,
    goal            TEXT,                        -- e.g. "Learn LangChain for a job"
    skill_level     VARCHAR(20) DEFAULT 'beginner', -- beginner / intermediate / advanced
    preferred_style VARCHAR(20) DEFAULT 'visual',   -- visual / reading / practice
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. LEARNING PLAN
-- Stores the AI-generated learning roadmap for each learner
CREATE TABLE learning_plan (
    id          SERIAL PRIMARY KEY,
    learner_id  INT REFERENCES learner_profile(id) ON DELETE CASCADE,
    topic       VARCHAR(150) NOT NULL,           -- e.g. "RAG Systems"
    week_number INT NOT NULL,                    -- Week 1, 2, etc.
    order_index INT NOT NULL,                    -- Order within the week
    status      VARCHAR(20) DEFAULT 'pending',   -- pending / in_progress / completed
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. QUIZ HISTORY
-- Stores every quiz attempt and score
CREATE TABLE quiz_history (
    id          SERIAL PRIMARY KEY,
    learner_id  INT REFERENCES learner_profile(id) ON DELETE CASCADE,
    topic       VARCHAR(150) NOT NULL,           -- Topic of the quiz
    question    TEXT NOT NULL,                   -- The quiz question
    user_answer TEXT,                            -- What the learner answered
    is_correct  BOOLEAN,                         -- True / False
    score       FLOAT,                           -- 0.0 to 1.0
    feedback    TEXT,                            -- AI feedback on the answer
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. PROGRESS TRACKING
-- Tracks which topics are strong, weak, or completed
CREATE TABLE progress (
    id              SERIAL PRIMARY KEY,
    learner_id      INT REFERENCES learner_profile(id) ON DELETE CASCADE,
    topic           VARCHAR(150) NOT NULL,
    status          VARCHAR(20) DEFAULT 'not_started', -- not_started / in_progress / completed
    mastery_score   FLOAT DEFAULT 0.0,           -- 0.0 to 1.0 (average quiz score)
    attempts        INT DEFAULT 0,               -- Number of quiz attempts
    is_weak_area    BOOLEAN DEFAULT FALSE,       -- Flagged as weak if score < 0.5
    last_studied_at TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. SESSION MEMORY
-- Stores short-term session context
CREATE TABLE session_memory (
    id              SERIAL PRIMARY KEY,
    learner_id      INT REFERENCES learner_profile(id) ON DELETE CASCADE,
    session_id      VARCHAR(100) NOT NULL,       -- Unique session identifier
    current_topic   VARCHAR(150),               -- What topic is being studied now
    current_goal    TEXT,                        -- Goal for this session
    messages        JSONB,                       -- Chat history as JSON
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- INDEXES for faster queries
-- ============================================================
CREATE INDEX idx_quiz_learner    ON quiz_history(learner_id);
CREATE INDEX idx_progress_learner ON progress(learner_id);
CREATE INDEX idx_plan_learner    ON learning_plan(learner_id);
CREATE INDEX idx_session_learner ON session_memory(learner_id);
CREATE INDEX idx_weak_areas      ON progress(learner_id, is_weak_area);

-- ============================================================
-- SAMPLE DATA for testing
-- ============================================================
INSERT INTO learner_profile (name, email, goal, skill_level)
VALUES ('Test Learner', 'test@example.com', 'Learn AI Engineering', 'beginner');
