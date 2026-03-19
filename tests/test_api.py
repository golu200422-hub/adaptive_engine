# ============================================================
# tests/test_api.py
# Automated tests for the entire API
#
# HOW TO RUN:
#   pip install pytest httpx
#   pytest tests/test_api.py -v
#
# These tests simulate a real student taking a quiz:
# 1. Start session
# 2. Get question
# 3. Submit answer
# 4. Check security report
# ============================================================

import pytest
import sys
import os

# Add parent directory to path so we can import our app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app

# TestClient lets us make HTTP requests to the app without starting a real server
client = TestClient(app)

# ---- We'll store the session token between tests ----
session_token = None
question_id = None


class TestSessionManagement:
    """Tests for starting and managing sessions."""
    
    def test_start_session_success(self):
        """Test that we can start a new session."""
        global session_token
        
        response = client.post("/api/v1/session/start", json={
            "user_id": "test_student_001",
            "starting_difficulty": 1
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert "session_token" in data
        assert data["session_token"].startswith("sess_")
        assert data["current_difficulty"] == 1
        
        # Save for other tests
        session_token = data["session_token"]
        print(f"\n✅ Session created: {session_token}")
    
    def test_start_session_with_topic(self):
        """Test starting a session with a specific topic."""
        response = client.post("/api/v1/session/start", json={
            "user_id": "test_student_002",
            "topic": "python",
            "starting_difficulty": 2
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["current_difficulty"] == 2
    
    def test_health_check(self):
        """Test that the server is running."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestQuestions:
    """Tests for getting questions."""
    
    def test_get_next_question(self):
        """Test getting a question for our session."""
        global question_id
        
        # Make sure we have a session first
        if not session_token:
            pytest.skip("No session token available")
        
        response = client.get(f"/api/v1/question/next/{session_token}")
        assert response.status_code == 200
        
        data = response.json()
        assert "question_id" in data
        assert "question_text" in data
        assert "difficulty_level" in data
        
        question_id = data["question_id"]
        print(f"\n✅ Got question: {data['question_text'][:50]}...")
    
    def test_get_question_invalid_session(self):
        """Test that invalid session returns 404."""
        response = client.get("/api/v1/question/next/invalid_session_token")
        assert response.status_code == 404
    
    def test_list_questions(self):
        """Test listing all questions."""
        response = client.get("/api/v1/questions/list")
        assert response.status_code == 200
        data = response.json()
        assert "questions" in data
        assert len(data["questions"]) > 0
    
    def test_list_questions_by_difficulty(self):
        """Test filtering questions by difficulty."""
        response = client.get("/api/v1/questions/list?difficulty=1")
        assert response.status_code == 200
        data = response.json()
        # All returned questions should be difficulty 1
        for q in data["questions"]:
            assert q["difficulty_level"] == 1
    
    def test_add_question(self):
        """Test adding a new question."""
        response = client.post("/api/v1/question/add", json={
            "question_text": "What is a binary search tree and how does it work?",
            "expected_answer": "A binary search tree is a tree data structure where each node has at most two children. The left subtree contains values less than the node, and the right subtree contains values greater than the node. This property allows O(log n) search, insertion, and deletion operations.",
            "difficulty_level": 2,
            "topic": "data_structures"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "question_id" in data
        print(f"\n✅ Added question ID: {data['question_id']}")


class TestAnswerSubmission:
    """Tests for submitting answers."""
    
    def test_submit_good_answer(self):
        """Test submitting a high-quality answer."""
        if not session_token or not question_id:
            pytest.skip("No session/question available")
        
        response = client.post("/api/v1/answer/submit", json={
            "session_token": session_token,
            "question_id": question_id,
            "answer_text": "A variable is a named container in programming that stores data values. It has a name (identifier) and holds a value that can change during program execution. Variables are essential for storing and manipulating data in programs.",
            "time_taken_seconds": 45.0,
            "paste_detected": False
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert "similarity_score" in data
        assert "cheating_score" in data
        assert "next_difficulty" in data
        assert 0.0 <= data["similarity_score"] <= 1.0
        assert 0.0 <= data["cheating_score"] <= 1.0
        
        print(f"\n✅ Answer evaluated:")
        print(f"   Similarity: {data['similarity_percentage']}%")
        print(f"   Performance: {data['performance_label']}")
        print(f"   Risk Level: {data['risk_level']}")
    
    def test_submit_fast_answer_triggers_flags(self):
        """Test that suspiciously fast answer gets flagged."""
        # Start a fresh session for this test
        session_resp = client.post("/api/v1/session/start", json={
            "user_id": "test_cheat_detector",
            "starting_difficulty": 1
        })
        token = session_resp.json()["session_token"]
        
        # Get a question
        q_resp = client.get(f"/api/v1/question/next/{token}")
        q_id = q_resp.json()["question_id"]
        
        # Submit with suspiciously fast timing
        response = client.post("/api/v1/answer/submit", json={
            "session_token": token,
            "question_id": q_id,
            "answer_text": "A variable is a named storage location in memory that holds a value which can change during program execution. Variables have data types and are fundamental to programming in any language.",
            "time_taken_seconds": 0.5,  # 0.5 seconds for 30 words - suspicious!
            "paste_detected": True       # Also detected paste
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have flags
        assert len(data["security_flags"]) > 0
        # Risk should not be Low
        assert data["risk_level"] in ["Medium", "High", "Critical"]
        print(f"\n✅ Fast answer correctly flagged: {data['risk_level']} risk")
    
    def test_submit_answer_invalid_session(self):
        """Test that invalid session returns error."""
        response = client.post("/api/v1/answer/submit", json={
            "session_token": "fake_token",
            "question_id": 1,
            "answer_text": "Some answer",
            "time_taken_seconds": 30.0
        })
        assert response.status_code == 404


class TestSecurityReport:
    """Tests for security reporting."""
    
    def test_get_security_report(self):
        """Test getting the security report for a session."""
        if not session_token:
            pytest.skip("No session token available")
        
        response = client.get(f"/api/v1/security/report/{session_token}")
        assert response.status_code == 200
        
        data = response.json()
        assert "overall_risk_score" in data
        assert "risk_level" in data
        assert "recommendation" in data
        
        print(f"\n✅ Security Report:")
        print(f"   Overall Risk: {data['overall_risk_score']}")
        print(f"   Level: {data['risk_level']}")
        print(f"   Recommendation: {data['recommendation']}")
    
    def test_get_difficulty_status(self):
        """Test getting difficulty status."""
        if not session_token:
            pytest.skip("No session token available")
        
        response = client.get(f"/api/v1/difficulty/status/{session_token}")
        assert response.status_code == 200
        
        data = response.json()
        assert "current_difficulty" in data
        assert "difficulty_label" in data
        assert "trend" in data
    
    def test_cache_status(self):
        """Test cache status endpoint."""
        response = client.get("/api/v1/cache/status")
        assert response.status_code == 200
        data = response.json()
        assert "backend" in data
        assert data["backend"] in ["redis", "memory"]


# ---- MANUAL TEST HELPER ----
# Run this to see a complete workflow
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🎯 MANUAL WORKFLOW TEST")
    print("="*60)
    
    print("\n📌 Step 1: Start Session")
    r = client.post("/api/v1/session/start", json={
        "user_id": "demo_student",
        "starting_difficulty": 1
    })
    session = r.json()
    token = session["session_token"]
    print(f"   Token: {token}")
    print(f"   Difficulty: {session['current_difficulty']}")
    
    print("\n📌 Step 2: Get First Question")
    r = client.get(f"/api/v1/question/next/{token}")
    question = r.json()
    q_id = question["question_id"]
    print(f"   Q#{q_id}: {question['question_text'][:60]}...")
    
    print("\n📌 Step 3: Submit Answer")
    r = client.post("/api/v1/answer/submit", json={
        "session_token": token,
        "question_id": q_id,
        "answer_text": "A variable is a named storage location that holds data which can change. It represents a memory location with a name, allowing programs to store and retrieve values.",
        "time_taken_seconds": 35.0,
        "paste_detected": False
    })
    result = r.json()
    print(f"   Similarity: {result['similarity_percentage']}%")
    print(f"   Performance: {result['performance_label']}")
    print(f"   Risk: {result['risk_level']}")
    print(f"   Next Difficulty: {result['next_difficulty']}")
    print(f"   Feedback: {result['feedback']}")
    
    print("\n📌 Step 4: Security Report")
    r = client.get(f"/api/v1/security/report/{token}")
    report = r.json()
    print(f"   Overall Risk: {report['overall_risk_score']}")
    print(f"   Recommendation: {report['recommendation']}")
    
    print("\n✅ Complete workflow test passed!")
