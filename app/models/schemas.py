# ============================================================
# app/models/schemas.py
# Data Models - Define the shape of data going in and out
#
# Pydantic models validate that incoming data has the right format.
# For example, if someone sends a number where text is expected,
# Pydantic will catch that error automatically!
# ============================================================

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# ============================================================
# SESSION MODELS
# ============================================================

class StartSessionRequest(BaseModel):
    """
    Data needed to start a new quiz session.
    Example JSON: {"user_id": "student_001", "topic": "python"}
    """
    user_id: str = Field(..., description="Unique identifier for the user", example="student_001")
    topic: Optional[str] = Field(None, description="Topic to focus on (optional)", example="python")
    starting_difficulty: Optional[int] = Field(1, ge=1, le=3, description="Starting difficulty 1-3")

class SessionResponse(BaseModel):
    """Response when a session is created"""
    session_token: str
    user_id: str
    message: str
    current_difficulty: int
    instructions: str

# ============================================================
# QUESTION MODELS
# ============================================================

class QuestionResponse(BaseModel):
    """A question sent to the student"""
    question_id: int
    question_text: str
    difficulty_level: int
    topic: str
    difficulty_label: str  # "Easy", "Medium", "Hard"
    hint: Optional[str] = None

class AddQuestionRequest(BaseModel):
    """Data to add a new question to the system"""
    question_text: str = Field(..., min_length=10, description="The question to ask")
    expected_answer: str = Field(..., min_length=10, description="The ideal answer")
    difficulty_level: int = Field(..., ge=1, le=3, description="1=Easy, 2=Medium, 3=Hard")
    topic: str = Field(..., description="Topic category", example="python")

# ============================================================
# ANSWER MODELS
# ============================================================

class SubmitAnswerRequest(BaseModel):
    """
    When a student submits their answer.
    We also track HOW LONG they took (for cheat detection).
    """
    session_token: str = Field(..., description="Your session token from StartSession")
    question_id: int = Field(..., description="Which question you're answering")
    answer_text: str = Field(..., min_length=1, description="Your answer")
    time_taken_seconds: float = Field(..., gt=0, description="How many seconds you took")
    
    # Optional metadata for better detection
    keystroke_count: Optional[int] = Field(None, description="Number of keystrokes (from frontend)")
    paste_detected: Optional[bool] = Field(False, description="Did browser detect paste event?")

class AnswerEvaluationResponse(BaseModel):
    """
    Detailed feedback after evaluating an answer.
    This is what the student sees after submitting.
    """
    # Score information
    similarity_score: float          # How similar to expected answer (0.0 to 1.0)
    similarity_percentage: float     # Same but as percentage (0 to 100)
    performance_label: str           # "Excellent", "Good", "Average", "Poor"
    
    # Security analysis
    cheating_score: float            # Risk score (0.0 = no risk, 1.0 = very suspicious)
    security_flags: List[str]        # List of issues detected
    risk_level: str                  # "Low", "Medium", "High", "Critical"
    
    # Difficulty adaptation
    next_difficulty: int             # What difficulty next question will be
    difficulty_changed: bool         # Did difficulty change?
    difficulty_message: str          # Explanation of difficulty change
    
    # Feedback
    feedback: str                    # Human-readable feedback
    next_question_id: Optional[int]  # ID of next question (if available)

# ============================================================
# SECURITY MODELS
# ============================================================

class SecurityReport(BaseModel):
    """Full security analysis for a session"""
    session_token: str
    overall_risk_score: float
    risk_level: str
    total_answers: int
    suspicious_answers: int
    
    # Breakdown of findings
    timing_analysis: Dict[str, Any]
    pattern_analysis: Dict[str, Any]
    similarity_analysis: Dict[str, Any]
    
    # List of all security events
    events: List[Dict[str, Any]]
    
    # Final recommendation
    recommendation: str

class SecurityEvent(BaseModel):
    """A single security event/flag"""
    event_type: str
    severity: str  # "low", "medium", "high", "critical"
    description: str
    metadata: Dict[str, Any] = {}

# ============================================================
# DIFFICULTY MODELS
# ============================================================

class DifficultyStatus(BaseModel):
    """Current state of the difficulty engine"""
    session_token: str
    current_difficulty: int
    difficulty_label: str
    questions_answered: int
    average_score: float
    trend: str  # "improving", "declining", "stable"
    history: List[Dict[str, Any]]

# ============================================================
# ANALYSIS MODELS (Internal use)
# ============================================================

class TimingAnalysis(BaseModel):
    """Result of timing analysis on an answer"""
    time_taken: float
    expected_min_time: float
    expected_max_time: float
    is_too_fast: bool
    is_suspiciously_fast: bool
    timing_score: float  # 0.0 = normal, 1.0 = very suspicious
    flags: List[str]

class PatternAnalysis(BaseModel):
    """Result of pattern/behavior analysis"""
    paste_likely: bool
    copy_paste_score: float
    answer_length: int
    words_per_minute: float
    unusual_formatting: bool
    flags: List[str]

class SimilarityAnalysis(BaseModel):
    """Result of semantic similarity analysis"""
    cosine_similarity: float
    semantic_match: bool
    match_level: str  # "exact", "high", "medium", "low", "very_low"
    key_concepts_found: List[str]
    key_concepts_missing: List[str]
