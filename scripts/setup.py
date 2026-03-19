#!/usr/bin/env python3
# ============================================================
# scripts/setup.py
# BEGINNER-FRIENDLY SETUP SCRIPT
#
# Run this script to verify everything is installed correctly
# and set up the project for the first time.
#
# HOW TO RUN:
#   python scripts/setup.py
# ============================================================

import sys
import os
import subprocess

# Make sure we're in the right directory
script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(script_dir)
os.chdir(project_dir)

print("\n" + "="*60)
print("🚀 ADAPTIVE ENGINE - SETUP CHECKER")
print("="*60)

# ---- Check Python version ----
print("\n📌 Checking Python version...")
version = sys.version_info
if version.major < 3 or version.minor < 9:
    print(f"❌ Python {version.major}.{version.minor} found.")
    print("   Please install Python 3.9 or newer.")
    print("   Download from: https://python.org/downloads")
    sys.exit(1)
else:
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK!")

# ---- Check required packages ----
print("\n📌 Checking installed packages...")

packages = {
    "fastapi": "FastAPI (web framework)",
    "uvicorn": "Uvicorn (web server)",
    "sentence_transformers": "Sentence Transformers (AI model)",
    "sklearn": "Scikit-learn (similarity math)",
    "numpy": "NumPy (numerical computing)",
    "pydantic": "Pydantic (data validation)",
}

all_installed = True
for package, description in packages.items():
    try:
        __import__(package)
        print(f"  ✅ {description}")
    except ImportError:
        print(f"  ❌ {description} - NOT INSTALLED")
        all_installed = False

# ---- Check Redis (optional) ----
print("\n📌 Checking Redis (optional)...")
try:
    import redis
    r = redis.Redis(host='localhost', port=6379, socket_timeout=1)
    r.ping()
    print("  ✅ Redis is running!")
except Exception:
    print("  ⚠️  Redis not running (that's OK! App will use memory cache)")

# ---- Create .env file if it doesn't exist ----
print("\n📌 Checking .env file...")
if not os.path.exists(".env"):
    if os.path.exists(".env.example"):
        import shutil
        shutil.copy(".env.example", ".env")
        print("  ✅ Created .env from .env.example")
    else:
        print("  ⚠️  No .env file found (using defaults)")
else:
    print("  ✅ .env file exists")

# ---- Test database initialization ----
print("\n📌 Testing database setup...")
try:
    sys.path.insert(0, project_dir)
    from app.models.database import init_db
    init_db()
    print("  ✅ Database initialized successfully!")
    
    # Check that questions were loaded
    import sqlite3
    conn = sqlite3.connect("adaptive_engine.db")
    count = conn.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
    conn.close()
    print(f"  ✅ {count} questions in database")
except Exception as e:
    print(f"  ❌ Database error: {e}")

# ---- Final summary ----
print("\n" + "="*60)
if all_installed:
    print("✅ ALL CHECKS PASSED! Your project is ready.")
    print("\n🚀 TO START THE SERVER, RUN:")
    print("   uvicorn app.main:app --reload --port 8000")
    print("\n📖 Then open in browser:")
    print("   http://localhost:8000/docs")
else:
    print("❌ Some packages are missing. Run:")
    print("   pip install -r requirements.txt")
    print("   Then run this script again.")
print("="*60 + "\n")
