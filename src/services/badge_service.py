"""
badge_service.py — Computes and awards learner achievement badges.

Badge definitions and logic for the Evolyn platform.
Badges are computed dynamically from DB data and persisted in learner_badges table.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))
sys.path.append(str(ROOT / "database"))

from db import get_connection

# ─────────────────────────────────────────────────────────────────────────────
# Badge Definitions
# ─────────────────────────────────────────────────────────────────────────────

ALL_BADGES = [
    {
        "badge_id": "first_step",
        "title": "First Step",
        "description": "Completed your very first quiz on Evolyn.",
        "emoji": "🚀",
        "color": "#6366f1",
        "glow": "rgba(99, 102, 241, 0.4)",
        "rarity": "Common",
    },
    {
        "badge_id": "level_up_intermediate",
        "title": "Level Up: Intermediate",
        "description": "Promoted from Beginner to Intermediate level.",
        "emoji": "⬆️",
        "color": "#f59e0b",
        "glow": "rgba(245, 158, 11, 0.4)",
        "rarity": "Rare",
    },
    {
        "badge_id": "level_up_advanced",
        "title": "Level Up: Advanced",
        "description": "Promoted from Intermediate to Advanced level.",
        "emoji": "🔥",
        "color": "#ef4444",
        "glow": "rgba(239, 68, 68, 0.4)",
        "rarity": "Epic",
    },
    {
        "badge_id": "python_master",
        "title": "Python Master",
        "description": "Completed the full Python learning path — all three levels.",
        "emoji": "🐍",
        "color": "#10b981",
        "glow": "rgba(16, 185, 129, 0.4)",
        "rarity": "Legendary",
    },
    {
        "badge_id": "java_master",
        "title": "Java Master",
        "description": "Completed the full Java learning path — all three levels.",
        "emoji": "☕",
        "color": "#f97316",
        "glow": "rgba(249, 115, 22, 0.4)",
        "rarity": "Legendary",
    },
    {
        "badge_id": "perfect_score",
        "title": "Perfect Score",
        "description": "Achieved 100% on any topic quiz.",
        "emoji": "💯",
        "color": "#8b5cf6",
        "glow": "rgba(139, 92, 246, 0.4)",
        "rarity": "Rare",
    },
    {
        "badge_id": "no_weak_areas",
        "title": "Solid Foundation",
        "description": "Cleared all weak areas — no topics left behind.",
        "emoji": "🏗️",
        "color": "#06b6d4",
        "glow": "rgba(6, 182, 212, 0.4)",
        "rarity": "Rare",
    },
    {
        "badge_id": "10_quizzes",
        "title": "Quiz Veteran",
        "description": "Completed 10 or more quizzes.",
        "emoji": "🎯",
        "color": "#7D82B0",
        "glow": "rgba(125, 130, 176, 0.4)",
        "rarity": "Uncommon",
    },
    {
        "badge_id": "evolyn_certified",
        "title": "Evolyn Certified",
        "description": "Completed any full course and connected GitHub for public verification.",
        "emoji": "🏅",
        "color": "#fbbf24",
        "glow": "rgba(251, 191, 36, 0.5)",
        "rarity": "Legendary",
    },
]

BADGE_MAP = {b["badge_id"]: b for b in ALL_BADGES}

# ─────────────────────────────────────────────────────────────────────────────
# Badge Logic — Check which badges a learner has EARNED
# ─────────────────────────────────────────────────────────────────────────────

def compute_earned_badge_ids(learner_id: str) -> dict:
    """
    Analyzes DB data for a learner and returns a dict of badge_id -> subject (or None).
    Does NOT write to DB — pure computation.
    """
    earned = {}
    conn = get_connection()
    cur = conn.cursor()

    try:
        # --- first_step: at least 1 quiz attempt ---
        cur.execute(
            "SELECT COUNT(*) FROM quiz_attempts WHERE learner_id = ?", (learner_id,)
        )
        if cur.fetchone()[0] >= 1:
            earned["first_step"] = None

        # --- 10_quizzes ---
        cur.execute(
            "SELECT COUNT(*) FROM quiz_attempts WHERE learner_id = ?", (learner_id,)
        )
        if cur.fetchone()[0] >= 10:
            earned["10_quizzes"] = None

        # --- perfect_score: any quiz_attempts score == 100 ---
        cur.execute(
            "SELECT COUNT(*) FROM quiz_attempts WHERE learner_id = ? AND score >= 100",
            (learner_id,),
        )
        if cur.fetchone()[0] >= 1:
            earned["perfect_score"] = None

        # --- Level-up badges from learning_plan ---
        # intermediate promotion
        cur.execute(
            """
            SELECT COUNT(*) FROM learning_plan
            WHERE learner_id = ? AND current_level IN ('intermediate', 'advanced', 'completed')
            """,
            (learner_id,),
        )
        if cur.fetchone()[0] >= 1:
            earned["level_up_intermediate"] = None

        # advanced promotion
        cur.execute(
            """
            SELECT COUNT(*) FROM learning_plan
            WHERE learner_id = ? AND current_level IN ('advanced', 'completed')
            """,
            (learner_id,),
        )
        if cur.fetchone()[0] >= 1:
            earned["level_up_advanced"] = None

        # --- Course completion (python_master / java_master) ---
        cur.execute(
            """
            SELECT DISTINCT subject FROM learning_plan
            WHERE learner_id = ? AND current_level = 'completed'
            """,
            (learner_id,),
        )
        for (subj,) in cur.fetchall():
            if subj and "python" in subj.lower():
                earned["python_master"] = "python"
            if subj and "java" in subj.lower():
                earned["java_master"] = "java"

        # --- no_weak_areas: weak_areas table is empty for this learner ---
        cur.execute(
            "SELECT COUNT(*) FROM weak_areas WHERE learner_id = ?", (learner_id,)
        )
        if cur.fetchone()[0] == 0:
            # only award if they've done at least one quiz
            cur.execute(
                "SELECT COUNT(*) FROM quiz_attempts WHERE learner_id = ?", (learner_id,)
            )
            if cur.fetchone()[0] >= 1:
                earned["no_weak_areas"] = None

        # --- evolyn_certified: course completed AND github connected ---
        is_course_done = "python_master" in earned or "java_master" in earned
        cur.execute(
            "SELECT COUNT(*) FROM github_connections WHERE learner_id = ?", (learner_id,)
        )
        github_connected = cur.fetchone()[0] >= 1
        if is_course_done and github_connected:
            earned["evolyn_certified"] = None

    finally:
        conn.close()

    return earned


def sync_badges(learner_id: str):
    """
    Computes earned badges and persists any new ones to learner_badges table.
    Returns full badge list with earned status.
    """
    earned_map = compute_earned_badge_ids(learner_id)

    conn = get_connection()
    cur = conn.cursor()

    # Fetch already-stored badge earned_at timestamps
    cur.execute(
        "SELECT badge_id, earned_at FROM learner_badges WHERE learner_id = ?",
        (learner_id,),
    )
    existing = {row[0]: row[1] for row in cur.fetchall()}

    # Insert newly earned badges not yet stored
    for badge_id, subject in earned_map.items():
        if badge_id not in existing:
            cur.execute(
                """
                INSERT OR IGNORE INTO learner_badges (learner_id, badge_id, subject)
                VALUES (?, ?, ?)
                """,
                (learner_id, badge_id, subject),
            )

    conn.commit()

    # Fetch updated earned_at
    cur.execute(
        "SELECT badge_id, earned_at FROM learner_badges WHERE learner_id = ?",
        (learner_id,),
    )
    stored = {row[0]: row[1] for row in cur.fetchall()}
    conn.close()

    # Build final badge list
    result = []
    for badge_def in ALL_BADGES:
        bid = badge_def["badge_id"]
        entry = dict(badge_def)
        if bid in stored:
            entry["earned"] = True
            entry["earned_at"] = stored[bid]
        else:
            entry["earned"] = False
            entry["earned_at"] = None
        result.append(entry)

    return result


def get_github_connection(learner_id: str):
    """Returns GitHub connection data for a learner, or None."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT github_username, github_access_token FROM github_connections WHERE learner_id = ?",
        (learner_id,),
    )
    row = cur.fetchone()
    conn.close()
    if row:
        return {"github_username": row[0], "github_access_token": row[1]}
    return None


def save_github_connection(learner_id: str, github_username: str, access_token: str):
    """Stores or updates GitHub OAuth token for a learner."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT OR REPLACE INTO github_connections (learner_id, github_username, github_access_token)
        VALUES (?, ?, ?)
        """,
        (learner_id, github_username, access_token),
    )
    conn.commit()
    conn.close()
