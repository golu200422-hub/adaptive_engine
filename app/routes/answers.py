# ============================================================
# app/routes/answers.py
# Answer Submission & Evaluation Endpoints
#
# This is where ALL the magic happens!
# When a student submits an answer, this endpoint:
# 1. Looks up the correct answer
# 2. Calculates semantic similarity
# 3. Runs security/anti-cheat checks
# 4. Decides if difficulty should change
# 5. Returns comprehensive feedback
# ============================================================

from fastapi import APIRouter, HTTPException
from app.models.schemas import SubmitAnswerRequest, AnswerEvaluationResponse
from app.models.database import get_connection
from app.services.similarity_service import analyze_semantic_similarity
from app.services.security_service import (
    analyze_timing,
    analyze_patterns,
    analyze_performance_consistency,
    calculate_cheating_score,
    log_security_event
)
from app.services.difficulty_service import (
    calculate_adaptive_difficulty,
    get_session_performance,
    get_next_question
)
from app.services.session_service import (
    get_session,
    update_session_difficulty,
    update_session_score
)
import json
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/answer/submit")
def submit_answer(request: SubmitAnswerRequest):
    """
    📝 SUBMIT AN ANSWER FOR EVALUATION
    
    This is the MAIN endpoint of the system.
    Send your answer here and receive:
    - Similarity score (how correct your answer is)
    - Cheating risk assessment
    - Difficulty recommendation for next question
    - Detailed feedback
    
    Example request body:
    {
        "session_token": "sess_abc123...",
        "question_id": 1,
        "answer_text": "A variable stores data that can change...",
        "time_taken_seconds": 45.5,
        "paste_detected": false
    }
    """
    
    # ---- Step 1: Validate session ----
    session = get_session(request.session_token)
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found. Please start a new session with POST /api/v1/session/start"
        )
    
    # ---- Step 2: Fetch the question and correct answer ----
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT id, question_text, expected_answer, difficulty_level, topic
            FROM questions
            WHERE id = ?
        """, (request.question_id,))
        
        question = cursor.fetchone()
    finally:
        conn.close()
    
    if not question:
        raise HTTPException(
            status_code=404,
            detail=f"Question ID {request.question_id} not found."
        )
    
    question_id = question[0]
    expected_answer = question[2]
    question_difficulty = question[3]
    
    # ---- Step 3: Semantic Similarity Analysis ----
    # Compare student's answer to the correct answer using AI
    similarity_result = analyze_semantic_similarity(
        student_answer=request.answer_text,
        expected_answer=expected_answer
    )
    similarity_score = similarity_result["cosine_similarity"]
    
    # ---- Step 4: Security Analysis ----
    # 4a: Timing analysis
    timing = analyze_timing(
        answer_text=request.answer_text,
        time_taken_seconds=request.time_taken_seconds,
        question_difficulty=question_difficulty
    )
    
    # 4b: Pattern analysis
    patterns = analyze_patterns(
        answer_text=request.answer_text,
        time_taken_seconds=request.time_taken_seconds,
        paste_detected=request.paste_detected or False
    )
    
    # 4c: Performance consistency check
    consistency = analyze_performance_consistency(
        session_token=request.session_token,
        current_similarity_score=similarity_score
    )
    
    # 4d: Calculate final cheating score
    cheating_score, risk_level, all_flags = calculate_cheating_score(
        timing_analysis=timing,
        pattern_analysis=patterns,
        consistency_analysis=consistency
    )
    
    # ---- Step 5: Log security events if needed ----
    if cheating_score >= 0.6:
        severity = "high" if cheating_score >= 0.8 else "medium"
        log_security_event(
            session_token=request.session_token,
            event_type="suspicious_answer",
            severity=severity,
            description=f"Cheating score: {cheating_score:.2f} ({risk_level})",
            metadata={
                "question_id": question_id,
                "cheating_score": cheating_score,
                "flags": all_flags[:3]  # Log first 3 flags
            }
        )
    
    # ---- Step 6: Save answer to database ----
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO answers 
            (session_token, question_id, answer_text, time_taken_seconds,
             similarity_score, cheating_score, flags)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            request.session_token,
            question_id,
            request.answer_text,
            request.time_taken_seconds,
            similarity_score,
            cheating_score,
            json.dumps(all_flags)
        ))
        conn.commit()
    finally:
        conn.close()
    
    # ---- Step 7: Adaptive Difficulty ----
    # Get recent performance data
    performance = get_session_performance(request.session_token)
    recent_scores = performance.get("recent_scores", [])
    
    # Get current difficulty and calculate new difficulty
    current_difficulty = session.get("current_difficulty", 1)
    new_difficulty, change_reason, difficulty_message = calculate_adaptive_difficulty(
        session_token=request.session_token,
        current_difficulty=current_difficulty,
        recent_scores=recent_scores + [similarity_score]  # Include current score
    )
    
    difficulty_changed = new_difficulty != current_difficulty
    
    # Update session if difficulty changed
    if difficulty_changed:
        update_session_difficulty(request.session_token, new_difficulty)
    
    # ---- Step 8: Get next question ID (preview) ----
    next_question = get_next_question(request.session_token, new_difficulty)
    next_question_id = next_question["id"] if next_question else None
    
    # ---- Step 9: Update session stats ----
    questions_answered = performance.get("answers_count", 0) + 1
    new_avg_score = (
        performance.get("average_score", 0) * (questions_answered - 1) + similarity_score
    ) / questions_answered
    update_session_score(request.session_token, new_avg_score, questions_answered)
    
    # ---- Step 10: Build response ----
    return {
        # Answer quality
        "similarity_score": similarity_result["cosine_similarity"],
        "similarity_percentage": similarity_result["similarity_percentage"],
        "performance_label": similarity_result["performance_label"],
        "key_concepts_found": similarity_result.get("key_concepts_found", []),
        "key_concepts_missing": similarity_result.get("key_concepts_missing", []),
        
        # Security
        "cheating_score": cheating_score,
        "risk_level": risk_level,
        "security_flags": all_flags,
        
        # Difficulty adaptation
        "next_difficulty": new_difficulty,
        "difficulty_changed": difficulty_changed,
        "difficulty_message": difficulty_message,
        
        # Navigation
        "next_question_id": next_question_id,
        
        # Detailed feedback
        "feedback": _generate_feedback(
            similarity_score=similarity_score,
            key_concepts_found=similarity_result.get("key_concepts_found", []),
            key_concepts_missing=similarity_result.get("key_concepts_missing", [])
        ),
        
        # Analysis details
        "detailed_analysis": {
            "timing": {
                "time_taken": request.time_taken_seconds,
                "expected_min": timing.get("expected_min_time"),
                "is_suspicious": timing.get("is_too_fast")
            },
            "patterns": {
                "paste_likely": patterns.get("paste_likely"),
                "word_count": patterns.get("word_count")
            }
        }
    }


def _generate_feedback(
    similarity_score: float,
    key_concepts_found: list,
    key_concepts_missing: list
) -> str:
    """Generate human-readable feedback based on the score."""
    
    if similarity_score >= 0.8:
        base = "🌟 Excellent answer! You demonstrated strong understanding of the topic."
    elif similarity_score >= 0.6:
        base = "✅ Good answer! You covered the key points well."
    elif similarity_score >= 0.4:
        base = "📚 Decent attempt, but there's room to improve."
    elif similarity_score >= 0.2:
        base = "💡 You're on the right track but missed some key concepts."
    else:
        base = "📖 This answer needs more work. Review the fundamentals."
    
    if key_concepts_found:
        base += f" Great job covering: {', '.join(key_concepts_found[:3])}."
    
    if key_concepts_missing:
        base += f" Consider including: {', '.join(key_concepts_missing[:3])}."
    
    return base


@router.get("/answer/history/{session_token}")
def get_answer_history(session_token: str):
    """
    📊 GET ANSWER HISTORY FOR A SESSION
    
    Returns all answers submitted in a session with their scores.
    """
    
    session = get_session(session_token)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT a.id, q.question_text, a.answer_text, 
                   a.time_taken_seconds, a.similarity_score, 
                   a.cheating_score, a.submitted_at
            FROM answers a
            JOIN questions q ON a.question_id = q.id
            WHERE a.session_token = ?
            ORDER BY a.submitted_at ASC
        """, (session_token,))
        
        history = [
            {
                "answer_id": row[0],
                "question": row[1][:80] + "..." if len(row[1]) > 80 else row[1],
                "answer": row[2][:100] + "..." if len(row[2]) > 100 else row[2],
                "time_taken": row[3],
                "similarity_score": round(row[4], 4),
                "similarity_percentage": round(row[4] * 100, 1),
                "cheating_score": round(row[5], 4),
                "risk_level": "High" if row[5] > 0.6 else "Medium" if row[5] > 0.3 else "Low",
                "submitted_at": row[6]
            }
            for row in cursor.fetchall()
        ]
        
        return {
            "session_token": session_token,
            "total_answers": len(history),
            "average_similarity": round(
                sum(h["similarity_score"] for h in history) / len(history), 4
            ) if history else 0,
            "answers": history
        }
    
    finally:
        conn.close()
