# ============================================================
# app/services/difficulty_service.py
# Adaptive Difficulty Intelligence Engine
#
# How it works (like a video game difficulty system):
# 
# 🎮 Imagine you're playing a game:
# - You beat 3 levels easily? The game increases difficulty.
# - You fail 3 levels in a row? The game makes it easier.
# - This KEEPS you in the "flow zone" - not too easy, not too hard.
#
# Our system does the same for quiz questions!
# 
# Algorithm:
# - Track the last 3 answers' scores
# - If average score >= 75%: Increase difficulty (student is doing great!)
# - If average score <= 35%: Decrease difficulty (student is struggling)
# - Otherwise: Keep the same difficulty
# ============================================================

import logging
from typing import List, Optional, Tuple
from app.models.database import get_connection
import json

logger = logging.getLogger(__name__)

# ---- Configuration ----
# These numbers control when difficulty changes
DIFFICULTY_LEVELS = {
    1: "Easy",
    2: "Medium", 
    3: "Hard"
}

MIN_DIFFICULTY = 1  # Can't go lower than Easy
MAX_DIFFICULTY = 3  # Can't go higher than Hard

# Number of recent answers to consider
WINDOW_SIZE = 3

# Score thresholds for changing difficulty
UPGRADE_THRESHOLD = 0.75   # Score >= 75%? Increase difficulty
DOWNGRADE_THRESHOLD = 0.35  # Score <= 35%? Decrease difficulty

# Minimum answers before we change difficulty
MIN_ANSWERS_FOR_CHANGE = 2


def get_difficulty_label(level: int) -> str:
    """Convert difficulty number to human-readable label."""
    return DIFFICULTY_LEVELS.get(level, "Unknown")


def calculate_adaptive_difficulty(
    session_token: str,
    current_difficulty: int,
    recent_scores: List[float]
) -> Tuple[int, str, str]:
    """
    The core adaptive algorithm.
    
    Analyzes recent performance and decides new difficulty.
    
    Args:
        session_token: The current quiz session
        current_difficulty: Current difficulty level (1, 2, or 3)
        recent_scores: List of recent similarity scores (0.0 to 1.0)
    
    Returns:
        Tuple of (new_difficulty, reason, detailed_message)
    
    Example:
        recent_scores = [0.9, 0.85, 0.88]  # All high scores!
        Returns: (2, "upgrade", "Great performance! Moving to Medium difficulty.")
    """
    
    # Need at least MIN_ANSWERS_FOR_CHANGE answers to change difficulty
    if len(recent_scores) < MIN_ANSWERS_FOR_CHANGE:
        return (
            current_difficulty,
            "not_enough_data",
            f"Need {MIN_ANSWERS_FOR_CHANGE - len(recent_scores)} more answer(s) before adjusting difficulty."
        )
    
    # Calculate average score of recent answers
    avg_score = sum(recent_scores) / len(recent_scores)
    
    # ---- Decision Logic ----
    
    if avg_score >= UPGRADE_THRESHOLD and current_difficulty < MAX_DIFFICULTY:
        # Student is doing great! Make it harder.
        new_difficulty = current_difficulty + 1
        reason = "upgrade"
        message = (
            f"🎯 Excellent work! Your average score is {avg_score*100:.0f}%. "
            f"Moving from {get_difficulty_label(current_difficulty)} → {get_difficulty_label(new_difficulty)}!"
        )
    
    elif avg_score <= DOWNGRADE_THRESHOLD and current_difficulty > MIN_DIFFICULTY:
        # Student is struggling. Make it easier.
        new_difficulty = current_difficulty - 1
        reason = "downgrade"
        message = (
            f"💡 Let's practice more fundamentals. Your average score is {avg_score*100:.0f}%. "
            f"Moving from {get_difficulty_label(current_difficulty)} → {get_difficulty_label(new_difficulty)} for now."
        )
    
    elif avg_score >= UPGRADE_THRESHOLD and current_difficulty == MAX_DIFFICULTY:
        # Already at maximum! Keep it there.
        new_difficulty = current_difficulty
        reason = "max_reached"
        message = f"🏆 Outstanding! You're performing at the highest level ({avg_score*100:.0f}%). Keep it up!"
    
    elif avg_score <= DOWNGRADE_THRESHOLD and current_difficulty == MIN_DIFFICULTY:
        # Already at minimum. Keep it there.
        new_difficulty = current_difficulty
        reason = "min_reached"
        message = f"📚 Focus on the basics. Take your time with these questions."
    
    else:
        # Score is in the "good" range. Keep same difficulty.
        new_difficulty = current_difficulty
        reason = "stable"
        message = (
            f"📊 Good progress! Staying at {get_difficulty_label(current_difficulty)} difficulty "
            f"(average: {avg_score*100:.0f}%)."
        )
    
    # Save the difficulty change to database if it changed
    if new_difficulty != current_difficulty:
        _save_difficulty_change(session_token, current_difficulty, new_difficulty, reason)
    
    return (new_difficulty, reason, message)


def get_next_question(session_token: str, difficulty: int, topic: Optional[str] = None) -> Optional[dict]:
    """
    Fetch the next appropriate question for a session.
    
    Rules:
    1. Match the requested difficulty level
    2. Don't repeat questions already asked in this session
    3. Optionally filter by topic
    
    Args:
        session_token: Current session
        difficulty: Desired difficulty level (1, 2, or 3)
        topic: Optional topic filter (e.g., "python", "algorithms")
    
    Returns:
        Question dictionary or None if no questions available
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Get list of questions already answered in this session
        cursor.execute("""
            SELECT DISTINCT question_id 
            FROM answers 
            WHERE session_token = ?
        """, (session_token,))
        
        answered_ids = [row[0] for row in cursor.fetchall()]
        
        # Build query to find a new question
        if answered_ids:
            # Exclude already-answered questions
            placeholders = ','.join(['?' for _ in answered_ids])
            
            if topic:
                query = f"""
                    SELECT id, question_text, difficulty_level, topic
                    FROM questions
                    WHERE difficulty_level = ?
                    AND topic = ?
                    AND id NOT IN ({placeholders})
                    ORDER BY RANDOM()
                    LIMIT 1
                """
                params = [difficulty, topic] + answered_ids
            else:
                query = f"""
                    SELECT id, question_text, difficulty_level, topic
                    FROM questions
                    WHERE difficulty_level = ?
                    AND id NOT IN ({placeholders})
                    ORDER BY RANDOM()
                    LIMIT 1
                """
                params = [difficulty] + answered_ids
        else:
            # No answered questions yet - any question works
            if topic:
                query = """
                    SELECT id, question_text, difficulty_level, topic
                    FROM questions
                    WHERE difficulty_level = ? AND topic = ?
                    ORDER BY RANDOM()
                    LIMIT 1
                """
                params = [difficulty, topic]
            else:
                query = """
                    SELECT id, question_text, difficulty_level, topic
                    FROM questions
                    WHERE difficulty_level = ?
                    ORDER BY RANDOM()
                    LIMIT 1
                """
                params = [difficulty]
        
        cursor.execute(query, params)
        row = cursor.fetchone()
        
        if row:
            return {
                "id": row[0],
                "question_text": row[1],
                "difficulty_level": row[2],
                "topic": row[3],
                "difficulty_label": get_difficulty_label(row[2])
            }
        
        # If no question found at exact difficulty, try adjacent difficulties
        logger.warning(f"No question found at difficulty {difficulty}. Trying adjacent levels...")
        return _find_fallback_question(cursor, difficulty, answered_ids)
    
    finally:
        conn.close()


def _find_fallback_question(cursor, target_difficulty: int, exclude_ids: List[int]) -> Optional[dict]:
    """
    If no questions available at target difficulty,
    try nearby difficulty levels.
    """
    # Try difficulties in order: target, target-1, target+1, etc.
    for diff in [target_difficulty, target_difficulty-1, target_difficulty+1]:
        if diff < MIN_DIFFICULTY or diff > MAX_DIFFICULTY:
            continue
        
        if exclude_ids:
            placeholders = ','.join(['?' for _ in exclude_ids])
            cursor.execute(f"""
                SELECT id, question_text, difficulty_level, topic
                FROM questions
                WHERE difficulty_level = ?
                AND id NOT IN ({placeholders})
                ORDER BY RANDOM()
                LIMIT 1
            """, [diff] + exclude_ids)
        else:
            cursor.execute("""
                SELECT id, question_text, difficulty_level, topic
                FROM questions
                WHERE difficulty_level = ?
                ORDER BY RANDOM()
                LIMIT 1
            """, [diff])
        
        row = cursor.fetchone()
        if row:
            return {
                "id": row[0],
                "question_text": row[1],
                "difficulty_level": row[2],
                "topic": row[3],
                "difficulty_label": get_difficulty_label(row[2])
            }
    
    return None  # No questions available at all


def get_session_performance(session_token: str) -> dict:
    """
    Analyze how a student has been performing throughout the session.
    
    Returns statistics like:
    - Average score
    - Trend (improving/declining/stable)
    - Current streak (consecutive good/bad answers)
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT similarity_score, submitted_at
            FROM answers
            WHERE session_token = ?
            ORDER BY submitted_at ASC
        """, (session_token,))
        
        rows = cursor.fetchall()
        
        if not rows:
            return {
                "answers_count": 0,
                "average_score": 0.0,
                "trend": "no_data",
                "recent_scores": []
            }
        
        scores = [row[0] for row in rows]
        recent_scores = scores[-WINDOW_SIZE:]  # Last N scores
        
        avg_score = sum(scores) / len(scores)
        
        # Determine trend
        if len(scores) >= 3:
            first_half = sum(scores[:len(scores)//2]) / (len(scores)//2)
            second_half = sum(scores[len(scores)//2:]) / len(scores[len(scores)//2:])
            
            if second_half > first_half + 0.1:
                trend = "improving"
            elif second_half < first_half - 0.1:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "early_stage"
        
        return {
            "answers_count": len(scores),
            "average_score": round(avg_score, 4),
            "recent_scores": [round(s, 4) for s in recent_scores],
            "trend": trend,
            "highest_score": round(max(scores), 4),
            "lowest_score": round(min(scores), 4)
        }
    
    finally:
        conn.close()


def _save_difficulty_change(
    session_token: str,
    old_difficulty: int,
    new_difficulty: int,
    reason: str
):
    """Record a difficulty change in the history table."""
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO difficulty_history (session_token, old_difficulty, new_difficulty, reason)
            VALUES (?, ?, ?, ?)
        """, (session_token, old_difficulty, new_difficulty, reason))
        conn.commit()
    except Exception as e:
        logger.error(f"Failed to save difficulty change: {e}")
    finally:
        conn.close()


def get_difficulty_history(session_token: str) -> List[dict]:
    """Get the full difficulty change history for a session."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT old_difficulty, new_difficulty, reason, created_at
            FROM difficulty_history
            WHERE session_token = ?
            ORDER BY created_at ASC
        """, (session_token,))
        
        return [
            {
                "from": row[0],
                "to": row[1],
                "from_label": get_difficulty_label(row[0]),
                "to_label": get_difficulty_label(row[1]),
                "reason": row[2],
                "timestamp": row[3]
            }
            for row in cursor.fetchall()
        ]
    finally:
        conn.close()
