import os
import sys
from pathlib import Path
from typing import List, Dict, Any

CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parents[1]
sys.path.append(str(ROOT_DIR))
sys.path.append(str(ROOT_DIR / "database"))

from db import (
    get_connection,
    record_quiz_attempt,
    mark_topic_completed,
    update_learning_progress
)
from src.agent.memory_tool import update_memory

# Level topic definitions (Fallback only)
LEVEL_TOPICS = {
    "beginner": ["variables", "strings", "lists", "functions"],
    "intermediate": ["functions", "object oriented programming", "classes"],
    "advanced": ["advanced programming concepts", "decorators", "error handling"]
}
import json
from src.agent.learning_plan import generate_topics_for_level

class ProgressService:
    def __init__(self):
        self._init_db()

    def _init_db(self):
        conn = get_connection()
        cursor = conn.cursor()
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
        conn.commit()
        conn.close()
    
    def record_attempt(self, learner_id: str, subject: str, level: str, topic: str, score: float, attempt_token: str = None) -> Dict[str, Any]:
        """
        Record a quiz attempt, recalculate rolling average, and update topic status.
        """
        # 1. Insert into quiz_attempts using helper
        record_quiz_attempt(learner_id, subject, level, topic, score, attempt_token)

        conn = get_connection()
        cursor = conn.cursor()
        
        # 2. Fetch all active attempts for this topic to calculate stats
        cursor.execute("""
            SELECT score FROM quiz_attempts
            WHERE learner_id = ? AND subject = ? AND level = ? AND topic = ? AND status = 'active'
            ORDER BY created_at DESC
        """, (learner_id, subject, level, topic))
        attempts = cursor.fetchall()
        
        attempt_count = len(attempts)
        scores = [row["score"] for row in attempts]
        
        # Calculate rolling average of the last 3 attempts
        last_3_scores = scores[:3]
        rolling_avg = sum(last_3_scores) / len(last_3_scores) if last_3_scores else 0.0
        
        # Enforce topic completion if rolling average is >= 70 or current score is >= 70
        completed = 1 if (rolling_avg >= 70.0 or score >= 70.0) else 0
        
        # 3. Insert or update topic_summary for active status
        cursor.execute("""
            INSERT OR REPLACE INTO topic_summary 
            (learner_id, subject, level, topic, attempt_count, last_score, rolling_average, completed, status, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', CURRENT_TIMESTAMP)
        """, (learner_id, subject, level, topic, attempt_count, score, rolling_avg, completed))
        conn.commit()

        # 4. If rolling average is < 70, mark as a weak area in database
        if rolling_avg < 70.0 and score < 70.0:
            cursor.execute("""
                INSERT OR IGNORE INTO weak_areas (learner_id, subject, level, topic, weakness)
                VALUES (?, ?, ?, ?, ?)
            """, (learner_id, subject, level, topic, f"Topic average is {round(rolling_avg, 1)}%. Needs reinforcement."))
            conn.commit()
        else:
            # If completed, remove from active weak areas (soft delete)
            cursor.execute("""
                DELETE FROM weak_areas 
                WHERE learner_id = ? AND subject = ? AND topic = ?
            """, (learner_id, subject, topic))
            conn.commit()

        # Update comprehensive memory
        update_memory(
            learner_id=learner_id,
            name=learner_id,
            email=f"{learner_id}@tutor.com",
            skill_level=level,
            subject=subject,
            completed_topic=topic if completed else None,
            current_topic=topic,
            total_score=rolling_avg
        )

        conn.close()

        # Update topic completion status and progress automatically using helpers
        if completed:
            mark_topic_completed(learner_id, subject, level, topic, score)
            update_learning_progress(learner_id, subject)
        
        return {
            "attempt_count": attempt_count,
            "last_score": score,
            "rolling_average": rolling_avg,
            "completed": bool(completed),
            "status": "PASS" if score >= 70 else ("RETRY" if score >= 50 else "FAIL")
        }

    def check_level_progression(self, learner_id: str, subject: str, level: str) -> Dict[str, Any]:
        """
        Check if level requirements are fully met:
        1. All topics completed.
        2. Level average score >= 70%.
        3. No active weak areas remaining (rolling average < 70%).
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        # Load required topics from the latest learning plan recommended_next_step JSON
        cursor.execute("""
            SELECT recommended_next_step FROM learning_plan
            WHERE learner_id = ? AND subject = ? AND current_level = ?
            ORDER BY created_at DESC LIMIT 1
        """, (learner_id, subject, level))
        plan_row = cursor.fetchone()
        
        required_topics = []
        if plan_row and plan_row["recommended_next_step"]:
            try:
                required_topics = json.loads(plan_row["recommended_next_step"])
            except:
                pass
                
        if not required_topics:
            required_topics = generate_topics_for_level(subject, level)

        if not required_topics:
            conn.close()
            return {"status": "error", "message": f"Unknown level: {level}"}

        # Fetch summaries of active topics
        placeholders = ",".join("?" for _ in required_topics)
        query = f"""
            SELECT topic, rolling_average, completed FROM topic_summary
            WHERE learner_id = ? AND subject = ? AND level = ? AND topic IN ({placeholders}) AND status = 'active'
        """
        cursor.execute(query, (learner_id, subject, level, *required_topics))
        summaries = {row["topic"]: {"rolling_average": row["rolling_average"], "completed": row["completed"]} 
                     for row in cursor.fetchall()}

        # Verify completions
        completed_topics = []
        weak_topics = []
        total_rolling = 0.0

        for topic in required_topics:
            stats = summaries.get(topic)
            if stats and stats["completed"] == 1:
                completed_topics.append(topic)
                total_rolling += stats["rolling_average"]
            else:
                weak_topics.append(topic)
                total_rolling += stats["rolling_average"] if stats else 0.0

        level_average = total_rolling / len(required_topics) if required_topics else 0.0
        conn.close()

        # All topics completed and average is >= 70% and no weak topics remaining
        requirements_met = (len(completed_topics) == len(required_topics)) and (level_average >= 70.0)

        if requirements_met:
            # Promote learner
            new_level = self._promote_learner(learner_id, subject, level)
            return {
                "status": "promoted",
                "requirements_met": True,
                "current_level": level,
                "new_level": new_level,
                "level_average": level_average,
                "completed_topics": completed_topics
            }
        else:
            return {
                "status": "review_required",
                "requirements_met": False,
                "level_average": level_average,
                "completed_topics": completed_topics,
                "weak_topics": weak_topics,
                "message": "Requirements not met. Please review weak topics and retake reinforcement quizzes."
            }

    def _promote_learner(self, learner_id: str, subject: str, current_level: str) -> str:
        """
        Updates database records to promote the student to the next tier.
        """
        next_level_map = {
            "beginner": "intermediate",
            "intermediate": "advanced",
            "advanced": "completed"
        }
        new_level = next_level_map.get(current_level.lower(), current_level)
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # 1. Update learner profile
        cursor.execute("""
            UPDATE learner_profile SET skill_level = ? WHERE learner_id = ?
        """, (new_level, learner_id))
        
        # 2. Add transition row in learning_progress
        cursor.execute("""
            INSERT INTO learning_progress (learner_id, subject, current_level, completed_topic, current_topic, status)
            VALUES (?, ?, ?, ?, ?, 'in_progress')
        """, (learner_id, subject, new_level, f"completed_{current_level}", f"start_{new_level}"))
        
        # 3. Update learning_plan record with dynamically generated topics
        if new_level != "completed":
            new_topics = generate_topics_for_level(subject, new_level)
            cursor.execute("""
                INSERT INTO learning_plan (learner_id, subject, current_level, plan_title, current_topic, recommended_next_step)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                learner_id, 
                subject, 
                new_level, 
                f"Personalized Plan for {new_level.title()}", 
                new_topics[0] if new_topics else "completed",
                json.dumps(new_topics)
            ))
        else:
            cursor.execute("""
                INSERT INTO learning_plan (learner_id, subject, current_level, plan_title, current_topic, recommended_next_step)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                learner_id, 
                subject, 
                new_level, 
                "Course Completed Plan", 
                "completed",
                "[]"
            ))
        
        conn.commit()
        conn.close()
        return new_level

    def soft_reset(self, learner_id: str, subject: str):
        """
        Perform a soft reset: archive progress and topic summaries, preserving historical analysis.
        """
        conn = get_connection()
        cursor = conn.cursor()

        # Archive active topic summaries
        cursor.execute("""
            UPDATE topic_summary SET status = 'archived'
            WHERE learner_id = ? AND subject = ? AND status = 'active'
        """, (learner_id, subject))

        # Archive active attempts
        cursor.execute("""
            UPDATE quiz_attempts SET status = 'archived'
            WHERE learner_id = ? AND subject = ? AND status = 'active'
        """, (learner_id, subject))

        # Archive weak areas
        cursor.execute("""
            DELETE FROM weak_areas WHERE learner_id = ? AND subject = ?
        """, (learner_id, subject))

        # Reset profile level and goal
        cursor.execute("""
            UPDATE learner_profile SET skill_level = 'beginner', goal = NULL
            WHERE learner_id = ?
        """, (learner_id,))

        # Delete assessment results to force diagnostic test on next subject selection
        cursor.execute("""
            DELETE FROM assessment_results
            WHERE learner_id = ? AND subject = ?
        """, (learner_id, subject))

        # Delete active topic completion statuses for this user and subject
        cursor.execute("""
            DELETE FROM topic_completion
            WHERE learner_id = ? AND subject = ?
        """, (learner_id, subject))

        # Delete previous progress tracking rows for this user and subject
        cursor.execute("""
            DELETE FROM learning_progress
            WHERE learner_id = ? AND subject = ?
        """, (learner_id, subject))

        # Delete previous learning plans for this user and subject
        cursor.execute("""
            DELETE FROM learning_plan
            WHERE learner_id = ? AND subject = ?
        """, (learner_id, subject))

        # Create clean start progress row pointing to assessment
        cursor.execute("""
            INSERT INTO learning_progress (learner_id, subject, current_level, completed_topic, current_topic, total_score, status)
            VALUES (?, ?, 'beginner', 'reset', 'assessment', 0.0, 'in_progress')
        """, (learner_id, subject))

        # Create new learning plan pointing to assessment
        cursor.execute("""
            INSERT INTO learning_plan (learner_id, subject, current_level, plan_title, current_topic, recommended_next_step)
            VALUES (?, ?, 'beginner', 'Fresh Adaptive Learning Plan', 'assessment', 'Take Initial Assessment')
        """, (learner_id, subject))

        conn.commit()
        conn.close()

    def get_learner_progress_info(self, learner_id: str, subject: str = "python") -> Dict[str, Any]:
        """
        Generates full profile and status values for dashboard hydration.
        """
        conn = get_connection()
        cursor = conn.cursor()

        # 1. Fetch Profile
        cursor.execute("""
            SELECT name, email, skill_level, goal FROM learner_profile WHERE learner_id = ?
        """, (learner_id,))
        profile = cursor.fetchone()
        
        if not profile:
            conn.close()
            return {"error": "User profile not found"}

        # 2. Fetch active topic summaries
        cursor.execute("""
            SELECT topic, attempt_count, last_score, rolling_average, completed FROM topic_summary
            WHERE learner_id = ? AND subject = ? AND status = 'active'
        """, (learner_id, subject))
        summaries = [dict(row) for row in cursor.fetchall()]

        # 3. Fetch active weak areas
        cursor.execute("""
            SELECT topic, weakness FROM weak_areas WHERE learner_id = ? AND subject = ?
        """, (learner_id, subject))
        weak_list = [dict(row) for row in cursor.fetchall()]

        # 4. Fetch plan details
        cursor.execute("""
            SELECT plan_title, current_topic, recommended_next_step FROM learning_plan
            WHERE learner_id = ? AND subject = ?
            ORDER BY created_at DESC LIMIT 1
        """, (learner_id, subject))
        plan = cursor.fetchone()

        # Build list of topics mapped to status based on summary state
        current_level = profile["skill_level"]
        
        # Load from learning plan recommended_next_step JSON instead of hardcoded dictionary
        cursor.execute("""
            SELECT recommended_next_step FROM learning_plan
            WHERE learner_id = ? AND subject = ? AND current_level = ?
            ORDER BY created_at DESC LIMIT 1
        """, (learner_id, subject, current_level))
        plan_row = cursor.fetchone()
        
        topics_in_level = []
        if plan_row and plan_row["recommended_next_step"]:
            try:
                topics_in_level = json.loads(plan_row["recommended_next_step"])
            except:
                pass
                
        if not topics_in_level and current_level != "completed":
            topics_in_level = generate_topics_for_level(subject, current_level)
            # Save it
            cursor.execute("""
                INSERT INTO learning_plan (learner_id, subject, current_level, plan_title, current_topic, recommended_next_step)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                learner_id,
                subject,
                current_level,
                f"Personalized Plan for {current_level.title()}",
                topics_in_level[0] if topics_in_level else "completed",
                json.dumps(topics_in_level)
            ))
            conn.commit()
        
        mapped_topics = []
        for i, t in enumerate(topics_in_level):
            summary = next((s for s in summaries if s["topic"].lower() == t.lower()), None)
            topic_status = "locked"
            
            if summary:
                topic_status = "done" if summary["completed"] == 1 else "active"
            else:
                # First topic in level is active by default
                if i == 0:
                    topic_status = "active"
                else:
                    # Active if previous is completed
                    prev_topic = topics_in_level[i - 1]
                    prev_summary = next((s for s in summaries if s["topic"].lower() == prev_topic.lower()), None)
                    if prev_summary and prev_summary["completed"] == 1:
                        topic_status = "active"
                    else:
                        topic_status = "locked"

            mapped_topics.append({
                "topic": t,
                "difficulty": current_level,
                "status": topic_status,
                "attempt_count": summary["attempt_count"] if summary else 0,
                "last_score": summary["last_score"] if summary else 0.0,
                "rolling_average": summary["rolling_average"] if summary else 0.0,
            })

        # Check if they have taken the placement/assessment test for this subject
        cursor.execute("""
            SELECT 1 FROM assessment_results WHERE learner_id = ? AND subject = ?
        """, (learner_id, subject))
        assessment_taken = cursor.fetchone() is not None

        conn.close()

        return {
            "name": profile["name"],
            "email": profile["email"],
            "current_level": current_level,
            "goal": profile["goal"],
            "topics": mapped_topics,
            "weak_areas": weak_list,
            "plan_title": plan["plan_title"] if plan else "Dynamic Learning Path",
            "current_topic": plan["current_topic"] if plan else (topics_in_level[0] if topics_in_level else "completed"),
            "recommended_next_step": plan["recommended_next_step"] if plan else "Complete assessments",
            "assessment_taken": assessment_taken
        }

    def compile_historical_report(self, learner_id: str) -> Dict[str, Any]:
        """
        Compiles advanced analytical report including:
        - Progress over time
        - Performance by difficulty (including archived attempts)
        - Weak area trends
        - Full attempt logs per topic
        """
        conn = get_connection()
        cursor = conn.cursor()

        # 1. Fetch attempts sorted by time (full history, active + archived)
        cursor.execute("""
            SELECT id, subject, level, topic, score, status, created_at FROM quiz_attempts
            WHERE learner_id = ?
            ORDER BY created_at ASC
        """, (learner_id,))
        all_attempts = [dict(row) for row in cursor.fetchall()]

        # 2. Performance by difficulty
        cursor.execute("""
            SELECT level, AVG(score) as avg_score, COUNT(id) as total_quizzes FROM quiz_attempts
            WHERE learner_id = ?
            GROUP BY level
        """, (learner_id,))
        difficulty_performance = [dict(row) for row in cursor.fetchall()]

        # 3. Weak Area Trends (counts of fails < 70)
        cursor.execute("""
            SELECT topic, COUNT(id) as fail_count FROM quiz_attempts
            WHERE learner_id = ? AND score < 70
            GROUP BY topic
            ORDER BY fail_count DESC
        """, (learner_id,))
        weakness_trends = [dict(row) for row in cursor.fetchall()]

        # 4. Progress milestones (Level changes)
        cursor.execute("""
            SELECT current_level, created_at FROM learning_progress
            WHERE learner_id = ? AND completed_topic LIKE 'completed_%'
            ORDER BY created_at ASC
        """, (learner_id,))
        milestones = [dict(row) for row in cursor.fetchall()]

        conn.close()

        # Generate timeline chart points
        timeline = []
        for i, att in enumerate(all_attempts):
            timeline.append({
                "index": i + 1,
                "date": att["created_at"][:16], # format as YYYY-MM-DD HH:MM
                "score": att["score"],
                "topic": att["topic"],
                "level": att["level"]
            })

        return {
            "attempts": all_attempts,
            "timeline": timeline,
            "difficulty_performance": difficulty_performance,
            "weakness_trends": weakness_trends,
            "milestones": milestones
        }
