# ============================================================
# app/routes/security.py
# Security & Anti-Cheat Report Endpoints
# ============================================================

from fastapi import APIRouter, HTTPException
from app.services.security_service import get_session_security_report
from app.services.session_service import get_session
from app.utils.cache import cache

router = APIRouter()


@router.get("/security/report/{session_token}")
def get_security_report(session_token: str):
    """
    🔐 GET FULL SECURITY REPORT FOR A SESSION
    
    Returns a complete anti-cheat analysis including:
    - Overall risk score (0.0 to 1.0)
    - Risk level (Low/Medium/High/Critical)
    - List of all suspicious events detected
    - Recommendation (manual review needed?)
    
    URL: GET /api/v1/security/report/sess_abc123
    """
    
    session = get_session(session_token)
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found."
        )
    
    report = get_session_security_report(session_token)
    
    return {
        **report,
        "score_interpretation": {
            "0.0 - 0.3": "🟢 Low Risk - Normal behavior",
            "0.3 - 0.6": "🟡 Medium Risk - Some flags",
            "0.6 - 0.8": "🟠 High Risk - Multiple suspicious patterns",
            "0.8 - 1.0": "🔴 Critical Risk - Strong indicators of dishonesty"
        }
    }


@router.get("/cache/status")
def get_cache_status():
    """
    ⚡ CHECK CACHE (REDIS) STATUS
    
    Shows whether Redis is connected or using the fallback in-memory cache.
    """
    return cache.get_status()
