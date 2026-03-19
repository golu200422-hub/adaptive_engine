# ============================================================
# app/routes/questions.py
# Question Management Endpoints
#
# Available endpoints:
# GET  /api/v1/session/start          - Start a new quiz session
# GET  /api/v1/question/next/{token}  - Get next question
# POST /api/v1/question/add           - Add a new question
# GET  /api/v1/questions/list         - List all questions
# ============================================================

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import uuid

from app.models.schemas import StartSessionRequest, SessionResponse, AddQuestionRequest, QuestionResponse
from app.models.database import get_connection
from app.services.session_service import create_session, get_session, validate_session
from app.services.difficulty_service import get_next_question, get_difficulty_label
from app.services.similarity_service import generate_question_fingerprint

# Create a router (like a mini-app for this section)
router = APIRouter()


@router.post("/session/start", response_model=SessionResponse)
def start_session(request: StartSessionRequest):
    """
    🎯 START A NEW QUIZ SESSION
    
    This is the FIRST step. Call this to get your session token.
    
    Example request body:
    {
        "user_id": "student_001",
        "topic": "python",
        "starting_difficulty": 1
    }
    
    Example response:
    {
        "session_token": "sess_abc123...",
        "message": "Session started!",
        ...
    }
    """
    
    session = create_session(
        user_id=request.user_id,
        starting_difficulty=request.starting_difficulty or 1
    )
    
    return SessionResponse(
        session_token=session["session_token"],
        user_id=request.user_id,
        message="🎯 Quiz session started! Use your session_token for all future requests.",
        current_difficulty=session["current_difficulty"],
        instructions=(
            "Step 1: Copy your session_token.\n"
            "Step 2: Call GET /api/v1/question/next/{your_session_token}\n"
            "Step 3: Answer using POST /api/v1/answer/submit\n"
            "Step 4: Repeat!"
        )
    )


@router.get("/question/next/{session_token}")
def get_next_question_endpoint(
    session_token: str,
    topic: Optional[str] = Query(None, description="Filter by topic (optional)")
):
    """
    📚 GET THE NEXT QUESTION
    
    Returns a question appropriate for the student's current difficulty level.
    
    URL: GET /api/v1/question/next/sess_abc123
    Optional: /api/v1/question/next/sess_abc123?topic=python
    """
    
    # Verify session exists
    session = get_session(session_token)
    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"Session '{session_token}' not found. Please start a new session first."
        )
    
    current_difficulty = session.get("current_difficulty", 1)
    
    # Get an appropriate question
    question = get_next_question(session_token, current_difficulty, topic)
    
    if not question:
        return {
            "message": "No more questions available! 🎉 You've completed all questions.",
            "questions_answered": session.get("questions_answered", 0),
            "session_complete": True
        }
    
    # Add helpful context
    hints = {
        1: "💡 Take your time. Think about the core concept.",
        2: "💡 Think about specific details and examples.",
        3: "💡 Consider edge cases and technical depth."
    }
    
    return {
        "question_id": question["id"],
        "question_text": question["question_text"],
        "difficulty_level": question["difficulty_level"],
        "difficulty_label": question["difficulty_label"],
        "topic": question["topic"],
        "hint": hints.get(current_difficulty, ""),
        "instructions": "Submit your answer to POST /api/v1/answer/submit"
    }


@router.post("/question/add")
def add_question(request: AddQuestionRequest):
    """
    ➕ ADD A NEW QUESTION TO THE SYSTEM
    
    Adds a question and automatically:
    - Generates a fingerprint (to detect duplicate questions)
    - Validates the difficulty level
    
    Example request:
    {
        "question_text": "What is a linked list?",
        "expected_answer": "A linked list is a data structure...",
        "difficulty_level": 1,
        "topic": "data_structures"
    }
    """
    
    # Generate a fingerprint for duplicate detection
    fingerprint = generate_question_fingerprint(request.question_text)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Check for similar questions (simple text match)
        cursor.execute(
            "SELECT id FROM questions WHERE question_fingerprint = ?",
            (fingerprint,)
        )
        existing = cursor.fetchone()
        
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"A very similar question already exists (Question ID: {existing[0]})"
            )
        
        # Insert the new question
        cursor.execute("""
            INSERT INTO questions (question_text, expected_answer, difficulty_level, topic, question_fingerprint)
            VALUES (?, ?, ?, ?, ?)
        """, (
            request.question_text,
            request.expected_answer,
            request.difficulty_level,
            request.topic,
            fingerprint
        ))
        conn.commit()
        
        new_id = cursor.lastrowid
        
        return {
            "success": True,
            "question_id": new_id,
            "message": f"Question added successfully!",
            "fingerprint": fingerprint,
            "difficulty_label": get_difficulty_label(request.difficulty_level)
        }
    
    finally:
        conn.close()


@router.get("/questions/list")
def list_questions(
    difficulty: Optional[int] = Query(None, ge=1, le=3, description="Filter by difficulty"),
    topic: Optional[str] = Query(None, description="Filter by topic"),
    limit: int = Query(20, ge=1, le=100, description="Max number of questions")
):
    """
    📋 LIST ALL QUESTIONS
    
    Returns questions filtered by difficulty and/or topic.
    
    Examples:
    - /api/v1/questions/list
    - /api/v1/questions/list?difficulty=1
    - /api/v1/questions/list?topic=python
    - /api/v1/questions/list?difficulty=2&topic=algorithms
    """
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Build dynamic query based on filters
        conditions = []
        params = []
        
        if difficulty:
            conditions.append("difficulty_level = ?")
            params.append(difficulty)
        
        if topic:
            conditions.append("topic = ?")
            params.append(topic)
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        params.append(limit)
        
        cursor.execute(f"""
            SELECT id, question_text, difficulty_level, topic
            FROM questions
            {where_clause}
            ORDER BY difficulty_level, id
            LIMIT ?
        """, params)
        
        questions = [
            {
                "id": row[0],
                "question_text": row[1][:100] + "..." if len(row[1]) > 100 else row[1],
                "difficulty_level": row[2],
                "difficulty_label": get_difficulty_label(row[2]),
                "topic": row[3]
            }
            for row in cursor.fetchall()
        ]
        
        return {
            "total": len(questions),
            "filters_applied": {
                "difficulty": difficulty,
                "topic": topic
            },
            "questions": questions
        }
    
    finally:
        conn.close()
