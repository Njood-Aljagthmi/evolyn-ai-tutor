import os
import sys
import time
import json
import urllib.request
from pathlib import Path

import jwt
from jwt import PyJWKClient

# Add database path to sys.path
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parents[1]
sys.path.append(str(ROOT_DIR))
sys.path.append(str(ROOT_DIR / "database"))

from db import get_connection

# Firebase project ID
FIREBASE_PROJECT_ID = "ai-tutoring-agent"

# Firebase public JWKS endpoint (no credentials needed)
FIREBASE_JWKS_URL = "https://www.googleapis.com/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com"
FIREBASE_JWKS_CLIENT = None


def _get_jwks_client():
    """Lazy initialization of PyJWKClient for Firebase public keys."""
    global FIREBASE_JWKS_CLIENT
    if FIREBASE_JWKS_CLIENT is None:
        # PyJWKClient works with JWK Sets; Firebase uses x509 certs so we use a custom approach
        pass
    return FIREBASE_JWKS_CLIENT


def verify_firebase_token(id_token: str) -> dict:
    """
    Verify Firebase ID token by decoding without signature validation for local development.
    """
    try:
        decoded_token = jwt.decode(id_token, options={"verify_signature": False})
        return decoded_token
    except Exception as e:
        raise ValueError(f"Failed to decode Firebase token: {str(e)}")


def get_or_create_user(decoded_token: dict) -> dict:
    """
    Fetch user from DB or create a new profile if they don't exist.
    """
    email = decoded_token.get("email")
    name = decoded_token.get("name", email.split("@")[0] if email else "User")
    # Clean learner_id for SQLite compatibility
    learner_id = email.replace(".", "_").replace("@", "_") if email else decoded_token.get("uid")

    if not learner_id:
        raise ValueError("Invalid user token: No email or uid found.")

    conn = get_connection()
    cursor = conn.cursor()

    # Check if user exists
    cursor.execute("""
        SELECT learner_id, name, email, goal, skill_level 
        FROM learner_profile 
        WHERE learner_id = ?
    """, (learner_id,))
    user = cursor.fetchone()

    if not user:
        # Create user profile
        cursor.execute("""
            INSERT INTO learner_profile (learner_id, name, email, goal, skill_level)
            VALUES (?, ?, ?, ?, ?)
        """, (learner_id, name, email, "Learn programming concepts", "beginner"))
        conn.commit()
        
        user_data = {
            "learner_id": learner_id,
            "name": name,
            "email": email,
            "goal": "Learn programming concepts",
            "skill_level": "beginner",
            "is_new": True
        }
    else:
        user_data = {
            "learner_id": user["learner_id"],
            "name": user["name"],
            "email": user["email"],
            "goal": user["goal"],
            "skill_level": user["skill_level"],
            "is_new": False
        }

    conn.close()
    return user_data
