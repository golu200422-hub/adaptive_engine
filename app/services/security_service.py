# ============================================================
# app/services/security_service.py
# Anti-Pattern Assessment Security Engine
#
# What does this do?
# It acts like a vigilant proctor watching for cheating patterns.
# It doesn't ACCUSE anyone - it just calculates a "risk score".
#
# What it detects:
# 1. ⚡ TIMING ANALYSIS: Did they answer too fast?
#    - A 200-word answer in 5 seconds? Likely copy-pasted!
#    - We calculate minimum expected typing time
#
# 2. 📋 PATTERN DETECTION: Signs of copy-paste
#    - Perfect formatting (real typed answers are messier)
#    - Answer length vs typing time mismatch
#    - Unusual special characters
#
# 3. 📊 SCORE ANALYSIS: Inconsistent performance
#    - Very high similarity scores + very fast timing = suspicious
#    - Sudden jumps from Poor to Excellent = suspicious
#
# 4. 🔢 FINAL CHEATING SCORE: 0.0 to 1.0
#    - 0.0 - 0.3: Low risk (probably fine)
#    - 0.3 - 0.6: Medium risk (some flags)
#    - 0.6 - 0.8: High risk (multiple flags)
#    - 0.8 - 1.0: Critical risk (very suspicious)
# ============================================================

import logging
import json
import time
import re
from typing import List, Tuple, Optional
from app.models.database import get_connection

logger = logging.getLogger(__name__)

# ---- Configuration Constants ----
# Average human typing speed
AVERAGE_TYPING_WPM = 40        # Words per minute (average)
FAST_TYPING_WPM = 80           # Fast typist
MINIMUM_CHARS_PER_SECOND = 3   # Absolute minimum for any human

# Risk score weights (how much each factor contributes)
WEIGHT_TIMING = 0.35           # 35% - Timing is most important signal
WEIGHT_PASTE_DETECTION = 0.30  # 30% - Copy-paste detection
WEIGHT_PERFORMANCE_SPIKE = 0.20  # 20% - Sudden performance improvements
WEIGHT_PATTERN = 0.15          # 15% - Formatting/pattern analysis


def analyze_timing(
    answer_text: str,
    time_taken_seconds: float,
    question_difficulty: int
) -> dict:
    """
    Analyzes whether the time taken matches the answer length.
    
    Theory:
    - Average typing speed: ~40 words/minute = ~0.67 words/second
    - If someone writes 100 words in 5 seconds... 20 words/second!
    - That's physically impossible without copy-paste.
    
    Args:
        answer_text: The student's answer
        time_taken_seconds: How long they took
        question_difficulty: 1=Easy, 2=Medium, 3=Hard (affects expected time)
    
    Returns:
        Analysis dictionary with timing flags
    """
    
    word_count = len(answer_text.split())
    char_count = len(answer_text)
    
    # Minimum time to think about the question
    # Harder questions should take longer to think about
    thinking_time = {1: 5, 2: 10, 3: 15}[question_difficulty]
    
    # Minimum time to physically type the answer
    # Based on fast typing speed (generous)
    typing_time = (word_count / FAST_TYPING_WPM) * 60
    
    # Total minimum expected time = thinking + typing
    expected_min_time = thinking_time + typing_time
    
    # Maximum reasonable time (very slow + overthinking)
    expected_max_time = expected_min_time * 8
    
    flags = []
    timing_score = 0.0  # 0 = normal, 1 = very suspicious
    
    # Check 1: Way too fast
    if time_taken_seconds < expected_min_time * 0.3:
        timing_score += 0.7
        flags.append(f"⚡ Answer submitted in {time_taken_seconds:.1f}s (minimum expected: {expected_min_time:.1f}s)")
    elif time_taken_seconds < expected_min_time * 0.5:
        timing_score += 0.4
        flags.append(f"🚀 Suspiciously fast ({time_taken_seconds:.1f}s for {word_count} words)")
    elif time_taken_seconds < expected_min_time:
        timing_score += 0.2
        flags.append(f"⏱️ Faster than expected ({time_taken_seconds:.1f}s vs min {expected_min_time:.1f}s)")
    
    # Check 2: Characters per second (physical typing limit)
    chars_per_second = char_count / max(time_taken_seconds, 0.1)
    if chars_per_second > 30:  # 30 chars/sec = 360 wpm - impossible
        timing_score = min(1.0, timing_score + 0.5)
        flags.append(f"🔴 {chars_per_second:.0f} chars/second is physically impossible for human typing")
    elif chars_per_second > 15:  # 15 chars/sec = 180 wpm - suspicious
        timing_score = min(1.0, timing_score + 0.3)
        flags.append(f"🟡 {chars_per_second:.0f} chars/second exceeds expert typing speed")
    
    return {
        "time_taken": round(time_taken_seconds, 2),
        "word_count": word_count,
        "expected_min_time": round(expected_min_time, 2),
        "expected_max_time": round(expected_max_time, 2),
        "chars_per_second": round(chars_per_second, 2),
        "is_too_fast": timing_score >= 0.4,
        "is_suspiciously_fast": timing_score >= 0.7,
        "timing_score": round(min(1.0, timing_score), 4),
        "flags": flags
    }


def analyze_patterns(
    answer_text: str,
    time_taken_seconds: float,
    paste_detected: bool = False
) -> dict:
    """
    Detect copy-paste patterns and unusual formatting.
    
    Patterns that suggest copy-paste:
    1. Very long answer submitted very quickly
    2. Perfect punctuation throughout
    3. Unusual whitespace (multiple spaces, tabs)
    4. Browser paste event detected
    5. Answer looks like copied from documentation (perfect formatting)
    
    Returns:
        Pattern analysis dictionary
    """
    
    flags = []
    copy_paste_score = 0.0
    
    # Check 1: Browser detected paste (from frontend)
    if paste_detected:
        copy_paste_score += 0.5
        flags.append("📋 Browser paste event detected (Ctrl+V or right-click paste)")
    
    # Check 2: Unusual whitespace patterns
    # Real typed answers rarely have multiple spaces or tabs
    tab_count = answer_text.count('\t')
    if tab_count > 2:
        copy_paste_score += 0.2
        flags.append(f"🔧 Contains {tab_count} tab characters (unusual for typed answers)")
    
    # Check 3: Check for markdown-style formatting
    # Real interview answers don't usually have ```code blocks```
    code_blocks = len(re.findall(r'```[\s\S]*?```', answer_text))
    if code_blocks > 0:
        copy_paste_score += 0.2
        flags.append(f"📝 Contains {code_blocks} code block(s) - may indicate copy from documentation")
    
    # Check 4: Bullet point density
    # Perfectly formatted lists are suspicious for quick answers
    bullet_count = len(re.findall(r'^\s*[-•*]\s', answer_text, re.MULTILINE))
    if bullet_count > 3 and time_taken_seconds < 30:
        copy_paste_score += 0.25
        flags.append(f"📋 {bullet_count} bullet points in {time_taken_seconds:.0f}s - perfect formatting too quickly")
    
    # Check 5: Answer length vs time
    word_count = len(answer_text.split())
    if word_count > 150 and time_taken_seconds < 30:
        copy_paste_score += 0.3
        flags.append(f"📏 {word_count} words submitted in {time_taken_seconds:.0f}s - too long to type")
    
    # Check 6: Consecutive capital letters (acronym soup from docs)
    acronyms = re.findall(r'\b[A-Z]{3,}\b', answer_text)
    if len(acronyms) > 5:
        copy_paste_score += 0.1
        flags.append(f"🔤 High density of acronyms ({len(acronyms)}) - may be from documentation")
    
    # Normalize score to 0-1
    copy_paste_score = min(1.0, copy_paste_score)
    
    # Determine if paste is likely
    paste_likely = copy_paste_score >= 0.4
    
    return {
        "paste_likely": paste_likely,
        "copy_paste_score": round(copy_paste_score, 4),
        "answer_length": len(answer_text),
        "word_count": word_count,
        "unusual_formatting": any([tab_count > 2, code_blocks > 0, bullet_count > 5]),
        "flags": flags
    }


def analyze_performance_consistency(
    session_token: str,
    current_similarity_score: float
) -> dict:
    """
    Check if current answer's score is consistent with history.
    
    A sudden leap from 10% to 95% in one answer is suspicious!
    Real learning is gradual.
    
    Args:
        session_token: The current session
        current_similarity_score: Score for the current answer (0.0 to 1.0)
    
    Returns:
        Consistency analysis
    """
    
    conn = get_connection()
    cursor = conn.cursor()
    flags = []
    consistency_score = 0.0
    
    try:
        # Get all previous scores in this session
        cursor.execute("""
            SELECT similarity_score 
            FROM answers 
            WHERE session_token = ? 
            ORDER BY submitted_at ASC
        """, (session_token,))
        
        previous_scores = [row[0] for row in cursor.fetchall()]
        
        if not previous_scores:
            # First answer - no history to compare
            return {
                "consistency_score": 0.0,
                "flags": [],
                "previous_avg": None,
                "spike_detected": False
            }
        
        previous_avg = sum(previous_scores) / len(previous_scores)
        
        # Check for sudden performance spike
        score_jump = current_similarity_score - previous_avg
        
        if score_jump > 0.5 and previous_avg < 0.3:
            # Example: Was averaging 15%, suddenly got 85%
            consistency_score += 0.5
            flags.append(
                f"📈 Suspicious performance spike: {previous_avg*100:.0f}% avg → "
                f"{current_similarity_score*100:.0f}% (jump of {score_jump*100:.0f}%)"
            )
        elif score_jump > 0.4:
            consistency_score += 0.3
            flags.append(f"📊 Large performance jump detected ({score_jump*100:.0f}% improvement)")
        
        # Check for consistently perfect scores (possible answer sharing)
        if len(previous_scores) >= 3:
            recent_perfect = sum(1 for s in previous_scores[-3:] if s > 0.9)
            if recent_perfect >= 3 and current_similarity_score > 0.9:
                consistency_score += 0.2
                flags.append("⭐ 4+ consecutive near-perfect scores - statistically unusual")
        
        return {
            "consistency_score": round(min(1.0, consistency_score), 4),
            "previous_avg": round(previous_avg, 4),
            "previous_answers_count": len(previous_scores),
            "spike_detected": score_jump > 0.4,
            "flags": flags
        }
    
    finally:
        conn.close()


def calculate_cheating_score(
    timing_analysis: dict,
    pattern_analysis: dict,
    consistency_analysis: dict
) -> Tuple[float, str, List[str]]:
    """
    Combine all signals into a single cheating risk score.
    
    This is a WEIGHTED AVERAGE of all the individual scores.
    Think of it like a medical diagnosis - one symptom isn't conclusive,
    but multiple symptoms together increase the probability.
    
    Formula:
    cheating_score = (timing × 0.35) + (pattern × 0.30) + (consistency × 0.20) + (other × 0.15)
    
    Returns:
        Tuple of (cheating_score, risk_level, all_flags)
    """
    
    # Weighted combination
    cheating_score = (
        timing_analysis.get("timing_score", 0.0) * WEIGHT_TIMING +
        pattern_analysis.get("copy_paste_score", 0.0) * WEIGHT_PASTE_DETECTION +
        consistency_analysis.get("consistency_score", 0.0) * WEIGHT_PERFORMANCE_SPIKE
    )
    
    # Normalize to 0-1
    cheating_score = min(1.0, max(0.0, cheating_score))
    
    # Determine risk level
    if cheating_score >= 0.8:
        risk_level = "Critical"
    elif cheating_score >= 0.6:
        risk_level = "High"
    elif cheating_score >= 0.3:
        risk_level = "Medium"
    else:
        risk_level = "Low"
    
    # Collect all flags from all analyses
    all_flags = (
        timing_analysis.get("flags", []) +
        pattern_analysis.get("flags", []) +
        consistency_analysis.get("flags", [])
    )
    
    return round(cheating_score, 4), risk_level, all_flags


def log_security_event(
    session_token: str,
    event_type: str,
    severity: str,
    description: str,
    metadata: dict = None
):
    """
    Save a security event to the database.
    
    Event types:
    - "timing_violation": Answer too fast
    - "paste_detected": Copy-paste detected
    - "performance_spike": Sudden score jump
    - "pattern_anomaly": Unusual formatting
    """
    
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO security_events (session_token, event_type, severity, description, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, (
            session_token,
            event_type,
            severity,
            description,
            json.dumps(metadata or {})
        ))
        conn.commit()
    except Exception as e:
        logger.error(f"Failed to log security event: {e}")
    finally:
        conn.close()


def get_session_security_report(session_token: str) -> dict:
    """
    Generate a complete security report for a session.
    
    Aggregates all answers and security events to produce
    an overall risk assessment.
    """
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Get all answers with their scores
        cursor.execute("""
            SELECT similarity_score, cheating_score, time_taken_seconds, flags
            FROM answers
            WHERE session_token = ?
            ORDER BY submitted_at ASC
        """, (session_token,))
        
        answers = cursor.fetchall()
        
        if not answers:
            return {
                "session_token": session_token,
                "overall_risk_score": 0.0,
                "risk_level": "Low",
                "total_answers": 0,
                "suspicious_answers": 0,
                "events": [],
                "recommendation": "No answers submitted yet."
            }
        
        # Calculate aggregate statistics
        cheating_scores = [row[1] for row in answers]
        overall_risk = sum(cheating_scores) / len(cheating_scores)
        suspicious_count = sum(1 for s in cheating_scores if s > 0.5)
        
        # Get all security events
        cursor.execute("""
            SELECT event_type, severity, description, metadata, created_at
            FROM security_events
            WHERE session_token = ?
            ORDER BY created_at ASC
        """, (session_token,))
        
        events = [
            {
                "type": row[0],
                "severity": row[1],
                "description": row[2],
                "metadata": json.loads(row[3]),
                "timestamp": row[4]
            }
            for row in cursor.fetchall()
        ]
        
        # Determine risk level
        if overall_risk >= 0.8:
            risk_level = "Critical"
            recommendation = "🔴 High probability of academic dishonesty. Consider manual review."
        elif overall_risk >= 0.6:
            risk_level = "High"
            recommendation = "🟠 Multiple suspicious patterns detected. Recommend proctored re-test."
        elif overall_risk >= 0.3:
            risk_level = "Medium"
            recommendation = "🟡 Some suspicious patterns. Monitor closely."
        else:
            risk_level = "Low"
            recommendation = "🟢 No significant suspicious activity detected."
        
        return {
            "session_token": session_token,
            "overall_risk_score": round(overall_risk, 4),
            "risk_level": risk_level,
            "total_answers": len(answers),
            "suspicious_answers": suspicious_count,
            "suspicious_percentage": round(suspicious_count / len(answers) * 100, 1),
            "events": events,
            "recommendation": recommendation,
            "timing_analysis": {
                "avg_time_per_answer": round(
                    sum(row[2] for row in answers) / len(answers), 2
                )
            },
            "similarity_analysis": {
                "avg_similarity": round(
                    sum(row[0] for row in answers) / len(answers), 4
                )
            }
        }
    
    finally:
        conn.close()
