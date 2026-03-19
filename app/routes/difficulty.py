# ============================================================
# app/routes/difficulty.py + security.py combined
# Difficulty Status and Security Report Endpoints
# ============================================================

from fastapi import APIRouter, HTTPException
from app.services.difficulty_service import (
    get_session_performance,
    get_difficulty_history,
    get_difficulty_label
)
from app.services.session_service import get_session

router = APIRouter()


@router.get("/difficulty/status/{session_token}")
def get_difficulty_status(session_token: str):
    """
    📈 GET CURRENT DIFFICULTY STATUS
    
    Shows current difficulty, performance trend, and change history.
    
    URL: GET /api/v1/difficulty/status/sess_abc123
    """
    
    session = get_session(session_token)
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found. Start one at POST /api/v1/session/start"
        )
    
    performance = get_session_performance(session_token)
    history = get_difficulty_history(session_token)
    
    current_difficulty = session.get("current_difficulty", 1)
    
    return {
        "session_token": session_token,
        "current_difficulty": current_difficulty,
        "difficulty_label": get_difficulty_label(current_difficulty),
        "questions_answered": performance.get("answers_count", 0),
        "average_score": performance.get("average_score", 0.0),
        "average_score_percent": round(performance.get("average_score", 0.0) * 100, 1),
        "trend": performance.get("trend", "early_stage"),
        "recent_scores": performance.get("recent_scores", []),
        "difficulty_history": history,
        "explanation": {
            "upgrade_trigger": "Score >= 75% in last 3 questions",
            "downgrade_trigger": "Score <= 35% in last 3 questions",
            "stable_range": "Score between 35% and 75%"
        }
    }
