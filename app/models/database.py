# ============================================================
# app/models/database.py
# Database setup and table definitions
#
# What is a Database?
# Think of a database like a super-organized Excel spreadsheet
# that your computer can search through very quickly.
# Instead of one big sheet, we have multiple "tables" (like sheets)
# that are connected to each other.
#
# Why SQLite?
# SQLite is the simplest database - it stores everything in ONE file!
# No installation needed. Perfect for beginners.
# ============================================================

import sqlite3  # Built into Python! No installation needed.
import os

# Where to store the database file
# It will create a file called "adaptive_engine.db" in your project folder
DATABASE_PATH = "adaptive_engine.db"

def get_connection():
    """
    Opens a connection to the database.
    Like opening an Excel file to read/write data.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # This makes results come back as dictionaries
    conn.execute("PRAGMA foreign_keys = ON")  # Enable relationship checking
    return conn

def init_db():
    """
    Creates all database tables if they don't exist yet.
    This is called when the server starts.
    
    Think of tables like sheets in Excel:
    - sessions_table = one row per quiz session
    - questions_table = all our quiz questions
    - answers_table = student answers
    - security_events_table = suspicious activity log
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # ---- TABLE 1: Sessions ----
    # A "session" is one complete quiz/interview attempt
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_token TEXT UNIQUE NOT NULL,
            user_id TEXT NOT NULL,
            start_time REAL NOT NULL,
            current_difficulty INTEGER DEFAULT 1,
            total_score REAL DEFAULT 0.0,
            questions_answered INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # ---- TABLE 2: Questions ----
    # All quiz questions with their difficulty levels
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_text TEXT NOT NULL,
            expected_answer TEXT NOT NULL,
            difficulty_level INTEGER NOT NULL,
            topic TEXT NOT NULL,
            question_fingerprint TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # ---- TABLE 3: Answers ----
    # Every answer a student submits
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_token TEXT NOT NULL,
            question_id INTEGER NOT NULL,
            answer_text TEXT NOT NULL,
            time_taken_seconds REAL NOT NULL,
            similarity_score REAL DEFAULT 0.0,
            cheating_score REAL DEFAULT 0.0,
            flags TEXT DEFAULT '[]',
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_token) REFERENCES sessions(session_token),
            FOREIGN KEY (question_id) REFERENCES questions(id)
        )
    """)
    
    # ---- TABLE 4: Security Events ----
    # Log of all suspicious activities detected
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS security_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_token TEXT NOT NULL,
            event_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            description TEXT NOT NULL,
            metadata TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_token) REFERENCES sessions(session_token)
        )
    """)
    
    # ---- TABLE 5: Difficulty History ----
    # Track how difficulty changed over time for each session
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS difficulty_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_token TEXT NOT NULL,
            old_difficulty INTEGER NOT NULL,
            new_difficulty INTEGER NOT NULL,
            reason TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_token) REFERENCES sessions(session_token)
        )
    """)
    
    conn.commit()
    conn.close()
    
    # Seed some sample questions
    _seed_questions()
    print("✅ All database tables created successfully!")

def _seed_questions():
    """
    Add sample questions to the database if none exist.
    These are starter questions across 3 difficulty levels.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if questions already exist
    cursor.execute("SELECT COUNT(*) FROM questions")
    count = cursor.fetchone()[0]
    
    if count > 0:
        conn.close()
        return  # Don't add duplicates
    
    sample_questions = [
        # Difficulty Level 1 - Easy
        ("What is a variable in programming?", 
         "A variable is a named storage location in memory that holds a value which can change during program execution.",
         1, "programming_basics"),
        
        ("What does HTML stand for?", 
         "HTML stands for HyperText Markup Language. It is the standard language for creating web pages.",
         1, "web_basics"),
        
        ("What is a function?", 
         "A function is a reusable block of code that performs a specific task. It can take inputs (parameters) and return outputs.",
         1, "programming_basics"),
        
        # Difficulty Level 2 - Medium
        ("Explain the difference between a list and a tuple in Python.",
         "A list is mutable (can be changed after creation) and uses square brackets. A tuple is immutable (cannot be changed) and uses parentheses. Tuples are faster and used for fixed data.",
         2, "python"),
        
        ("What is REST API?",
         "REST (Representational State Transfer) API is an architectural style for building web services. It uses HTTP methods (GET, POST, PUT, DELETE) and is stateless, meaning each request contains all necessary information.",
         2, "web_development"),
        
        ("Explain Object-Oriented Programming.",
         "OOP is a programming paradigm that organizes code into objects that contain data (attributes) and behavior (methods). Key concepts include encapsulation, inheritance, polymorphism, and abstraction.",
         2, "programming_concepts"),
        
        # Difficulty Level 3 - Hard
        ("What is the time complexity of QuickSort and when does it degrade to O(n²)?",
         "QuickSort has average time complexity of O(n log n). It degrades to O(n²) in the worst case when the pivot is always the smallest or largest element, creating maximally unbalanced partitions. This happens with already sorted arrays using naive pivot selection.",
         3, "algorithms"),
        
        ("Explain database ACID properties.",
         "ACID stands for Atomicity (transactions complete fully or not at all), Consistency (data remains valid), Isolation (concurrent transactions don't interfere), and Durability (committed data persists). These properties ensure reliable database transactions.",
         3, "databases"),
        
        ("What is the CAP theorem?",
         "CAP theorem states that a distributed system can only guarantee 2 of 3 properties: Consistency (all nodes see same data), Availability (system responds to requests), and Partition Tolerance (system works despite network failures). In practice, partition tolerance is essential, so systems choose between CP or AP.",
         3, "distributed_systems"),
    ]
    
    cursor.executemany(
        "INSERT INTO questions (question_text, expected_answer, difficulty_level, topic) VALUES (?, ?, ?, ?)",
        sample_questions
    )
    conn.commit()
    conn.close()
    print(f"✅ Added {len(sample_questions)} sample questions to database!")
