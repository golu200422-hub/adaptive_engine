# ============================================================
# app/services/session_service.py
# Session Management
#
# A "session" is like a single quiz attempt.
# It tracks:
# - Who is taking the quiz
# - What difficulty they're on
# - How many questions they've answered
# - Their overall score
# ============================================================

import uuid
import time
import logging
from typing import Optional
from app.models.database import get_connection
from app.utils.cache import cache

logger = logging.getLogger(__name__)


def create_session(user_id: str, starting_difficulty: int = 1) -> dict:
    """
    Start a new quiz session for a user.
    
    Generates a unique token (like a ticket number) that
    identifies this specific quiz attempt.
    
    Returns session info including the token the user needs
    to include with all subsequent requests.
    """
    # Generate a unique session token
    # Example: "sess_a3f9b2e1-4d5c-..."
    session_token = f"sess_{uuid.uuid4()}"
    start_time = time.time()
    
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO sessions (session_token, user_id, start_time, current_difficulty)
            VALUES (?, ?, ?, ?)
        """, (session_token, user_id, start_time, starting_difficulty))
        conn.commit()
        
        # Cache session data for fast access
        session_data = {
            "session_token": session_token,
            "user_id": user_id,
            "start_time": start_time,
            "current_difficulty": starting_difficulty,
            "total_score": 0.0,
            "questions_answered": 0
        }
        cache.set_session(session_token, session_data)
        
        logger.info(f"New session created: {session_token} for user {user_id}")
        return session_data
    
    finally:
        conn.close()


def get_session(session_token: str) -> Optional[dict]:
    """
    Retrieve session data.
    First checks cache (fast), then database (slower).
    """
    # Try cache first
    cached = cache.get_session(session_token)
    if cached:
        return cached
    
    # Fall back to database
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT session_token, user_id, start_time, current_difficulty,
                   total_score, questions_answered, status
            FROM sessions
            WHERE session_token = ?
        """, (session_token,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        data = {
            "session_token": row[0],
            "user_id": row[1],
            "start_time": row[2],
            "current_difficulty": row[3],
            "total_score": row[4],
            "questions_answered": row[5],
            "status": row[6]
        }
        
        # Re-cache it
        cache.set_session(session_token, data)
        return data
    
    finally:
        conn.close()


def update_session_difficulty(session_token: str, new_difficulty: int):
    """Update the difficulty level for a session."""
    conn = get_connection()
    try:
        conn.execute("""
            UPDATE sessions
            SET current_difficulty = ?
            WHERE session_token = ?
        """, (new_difficulty, session_token))
        conn.commit()
        
        # Update cache too
        session_data = cache.get_session(session_token)
        if session_data:
            session_data["current_difficulty"] = new_difficulty
            cache.set_session(session_token, session_data)
    
    finally:
        conn.close()


def update_session_score(session_token: str, new_score: float, questions_count: int):
    """Update the running score and question count for a session."""
    conn = get_connection()
    try:
        conn.execute("""
            UPDATE sessions
            SET total_score = ?, questions_answered = ?
            WHERE session_token = ?
        """, (new_score, questions_count, session_token))
        conn.commit()
    finally:
        conn.close()


def validate_session(session_token: str) -> bool:
    """Check if a session exists and is still active."""
    session = get_session(session_token)
    if not session:
        return False
    return session.get("status", "active") == "active"
