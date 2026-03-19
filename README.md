# 🎯 Adaptive Difficulty Intelligence & Anti-Pattern Assessment Security Engine

> A complete backend system that acts like a **smart interviewer** — it adjusts question difficulty based on your performance and detects suspicious patterns like copy-pasting.

---

## 📋 TABLE OF CONTENTS

1. [What is this project?](#section-1-what-is-this-project)
2. [How the system works](#section-2-how-the-system-works)
3. [Prerequisites — Install everything first](#section-3-prerequisites)
4. [Step-by-step local setup](#section-4-local-setup)
5. [How to run WITHOUT Redis](#section-5-running-without-redis)
6. [How to test APIs](#section-6-testing-the-apis)
7. [Example complete workflow](#section-7-example-workflow)
8. [Common errors and fixes](#section-8-common-errors-and-fixes)
9. [Docker setup](#section-9-docker-setup)
10. [AWS deployment](#section-10-aws-deployment)
11. [Folder structure explained](#section-11-folder-structure)
12. [Future improvements](#section-12-future-improvements)

---

## SECTION 1: What is this project?

### 🧠 In Simple Words

Imagine you're taking an online quiz or interview. Normally, you get random questions regardless of your skill level — too easy if you're an expert, too hard if you're a beginner.

**This system is smarter.** It works like a human interviewer:

- 🎯 **Adaptive Difficulty**: If you answer 3 questions with 80%+ accuracy, it gives you harder questions. If you're struggling (below 35%), it gives you easier ones. Just like a good teacher.

- 🔍 **Cheating Detection**: If you type a 200-word answer in 2 seconds, or paste text from somewhere, the system flags it. It assigns a **cheating risk score** from 0.0 (no risk) to 1.0 (very suspicious).

- 🤖 **AI Similarity**: Instead of needing word-for-word correct answers, the system uses AI to understand the *meaning* of your answer. So "dogs are canines" and "dogs are a type of canine animal" get similar scores.

### 🏗️ Real-World Use Cases
- Online interview platforms
- E-learning systems
- Coding bootcamp assessments
- University online exams
- Corporate training quizzes

---

## SECTION 2: How the System Works

### Step-by-Step Flow

```
STUDENT                          SYSTEM
  │                                │
  │── POST /session/start ────────>│  Creates a quiz session
  │<── Returns session_token ───────│  (like a ticket number)
  │                                │
  │── GET /question/next/{token} ─>│  Looks up appropriate question
  │<── Returns question ────────────│  (matched to current difficulty)
  │                                │
  │   [Student reads and types     │
  │    their answer, timer runs]   │
  │                                │
  │── POST /answer/submit ────────>│  1. AI compares to expected answer
  │                                │  2. Timing analysis (too fast?)
  │                                │  3. Pattern detection (copy-paste?)
  │                                │  4. Consistency check (sudden spike?)
  │                                │  5. Calculate cheating score
  │                                │  6. Decide new difficulty
  │<── Returns full evaluation ─────│
  │                                │
  │   [Repeat until session ends]  │
  │                                │
  │── GET /security/report/{token}>│  Full anti-cheat analysis
  │<── Returns risk report ─────────│
```

### 🧩 The 7 Core Modules

| Module | What it does |
|--------|-------------|
| **Adaptive Difficulty Engine** | Tracks last 3 scores, increases/decreases difficulty |
| **Semantic Similarity** | Uses AI to compare meaning of answers (not just words) |
| **Pattern Detection** | Looks for copy-paste signs (formatting, length vs time) |
| **Question Fingerprinting** | Creates unique ID for each question to prevent duplicates |
| **Timing Analysis** | Checks if answer time matches expected human typing speed |
| **Cheating Score Engine** | Combines all signals into one 0.0-1.0 risk score |
| **Session Management** | Tracks each quiz attempt with a unique token |

---

## SECTION 3: Prerequisites

> ⚠️ **Read this entire section before starting.** Getting these installed correctly is the most important step.

### 3.1 Install Python

**What is Python?** Python is a programming language. Our backend code is written in Python.

#### On Windows:
1. Go to [https://python.org/downloads](https://python.org/downloads)
2. Click the big yellow "Download Python 3.11.x" button
3. Run the installer
4. ⚠️ **VERY IMPORTANT**: Check the box that says **"Add Python to PATH"** before clicking Install
5. Click "Install Now"
6. Verify: Open Command Prompt (search "cmd" in Start menu) and type:
   ```
   python --version
   ```
   You should see: `Python 3.11.x`

#### On Mac:
1. Open Terminal (search "Terminal" in Spotlight)
2. Install Homebrew first (if not installed):
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```
3. Install Python:
   ```bash
   brew install python@3.11
   ```
4. Verify:
   ```bash
   python3 --version
   ```

#### On Linux (Ubuntu/Debian):
```bash
sudo apt update
sudo apt install python3.11 python3.11-pip python3.11-venv
python3 --version
```

---

### 3.2 What is pip?

`pip` is Python's package manager. Think of it like an "App Store" for Python libraries.

- `pip install fastapi` → Downloads and installs FastAPI
- `pip install -r requirements.txt` → Installs ALL packages listed in a file

**pip comes with Python 3.** Verify it works:
```bash
pip --version
# or on Mac/Linux:
pip3 --version
```

---

### 3.3 What is a Virtual Environment?

**Problem:** If you have 10 Python projects, they might need different versions of packages. Project A needs `numpy 1.20`, Project B needs `numpy 1.24`.

**Solution:** A virtual environment is like a **separate Python installation just for ONE project**. It keeps packages isolated.

```
Your Computer
├── Python (global)
│
├── project_a/
│   └── venv/              ← Virtual environment for project A
│       └── numpy 1.20     ← Only exists here
│
└── adaptive_engine/
    └── venv/              ← Virtual environment for our project
        └── numpy 1.24     ← Only exists here
```

---

### 3.4 Install Git (Optional but Recommended)

Git lets you download code from GitHub.

#### Windows:
1. Download from [https://git-scm.com/download/win](https://git-scm.com/download/win)
2. Install with all defaults
3. Verify: `git --version`

#### Mac:
```bash
brew install git
```

#### Linux:
```bash
sudo apt install git
```

---

## SECTION 4: Local Setup

> Follow these steps IN ORDER. Don't skip any step.

### Step 1: Get the Project Files

**Option A: If you have Git installed:**
```bash
git clone https://github.com/yourusername/adaptive-engine.git
cd adaptive-engine
```

**Option B: Without Git:**
1. Download the ZIP file
2. Extract it
3. Open Terminal/Command Prompt
4. Navigate to the folder:
   ```bash
   # Windows example:
   cd C:\Users\YourName\Downloads\adaptive_engine
   
   # Mac/Linux example:
   cd ~/Downloads/adaptive_engine
   ```

---

### Step 2: Create a Virtual Environment

```bash
# This creates a folder called 'venv' with a private Python
python -m venv venv
```

**What this does:** Creates a `/venv` folder with its own Python and pip.

---

### Step 3: Activate the Virtual Environment

> ⚠️ You must do this EVERY TIME you open a new terminal!

**Windows (Command Prompt):**
```bash
venv\Scripts\activate
```

**Windows (PowerShell):**
```powershell
venv\Scripts\Activate.ps1
```
> If you get an error about execution policy, run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

**Mac/Linux:**
```bash
source venv/bin/activate
```

**How to know it worked:**
Your terminal prompt will change to show `(venv)`:
```
(venv) C:\Users\YourName\adaptive_engine>    # Windows
(venv) yourname@computer:~/adaptive_engine$  # Mac/Linux
```

---

### Step 4: Install All Required Packages

```bash
pip install -r requirements.txt
```

**What this does:** Reads `requirements.txt` and installs every package listed.

> ⏳ **This takes 5-10 minutes** the first time! It downloads packages including a 90MB AI model. Please be patient.

You'll see lots of output like:
```
Collecting fastapi==0.104.1
  Downloading fastapi-0.104.1-py3-none-any.whl (92 kB)
Collecting sentence-transformers==2.2.2
  Downloading sentence_transformers-2.2.2...
Installing collected packages: ...
Successfully installed fastapi-0.104.1 ...
```

---

### Step 5: Set Up Environment File

```bash
# Make a copy of the example config file
# Windows:
copy .env.example .env

# Mac/Linux:
cp .env.example .env
```

You can leave the defaults as-is for now.

---

### Step 6: Verify Everything is Installed

```bash
python scripts/setup.py
```

You should see:
```
✅ Python 3.11.x - OK!
✅ FastAPI (web framework)
✅ Uvicorn (web server)
✅ Sentence Transformers (AI model)
✅ Scikit-learn (similarity math)
⚠️  Redis not running (that's OK!)
✅ Database initialized successfully!
✅ 9 questions in database
```

---

### Step 7: Start the Server

```bash
uvicorn app.main:app --reload --port 8000
```

**Breaking down this command:**
- `uvicorn` → The web server program
- `app.main:app` → "In the `app/main.py` file, find the variable called `app`"
- `--reload` → Auto-restart when you change code (development mode)
- `--port 8000` → Listen on port 8000

**You should see:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
🚀 Server is starting...
🤖 Loading AI model (sentence-transformers)...
   First time may take a minute to download...
✅ AI model loaded successfully!
✅ Database ready!
✅ Server is running at http://localhost:8000
📚 API docs at http://localhost:8000/docs
```

---

### Step 8: Open the API Documentation

Open your browser and go to:
```
http://localhost:8000/docs
```

You'll see a beautiful interactive API documentation page where you can **test every endpoint** directly from your browser!

---

## SECTION 5: Running WITHOUT Redis

### What if I don't have Redis?

**Good news: You don't need Redis!** The app automatically detects whether Redis is running.

- ✅ **Redis running** → Uses Redis (faster, data persists after restart)
- ✅ **Redis NOT running** → Uses Python dictionary in memory (slightly slower, resets on restart)

**Both work correctly.** The only difference:
- Without Redis, cached data is lost when you restart the server
- With Redis, cached data persists (faster startup next time)

### How to verify which is being used

```bash
# While server is running, open a new terminal and run:
curl http://localhost:8000/api/v1/cache/status
```

Response with Redis:
```json
{"backend": "redis", "available": true, "message": "Using Redis"}
```

Response without Redis:
```json
{"backend": "memory", "available": true, "message": "Using in-memory cache (Redis not connected)"}
```

### If you want to install Redis later

**Windows:**
1. Download from [https://github.com/microsoftarchive/redis/releases](https://github.com/microsoftarchive/redis/releases)
2. Install the `.msi` file
3. Redis runs as a Windows Service automatically

**Mac:**
```bash
brew install redis
brew services start redis
```

**Linux:**
```bash
sudo apt install redis-server
sudo systemctl start redis
```

**Verify Redis is running:**
```bash
redis-cli ping
# Should return: PONG
```

---

## SECTION 6: Testing the APIs

### Method 1: Interactive Browser Docs (Easiest!)

1. Open `http://localhost:8000/docs`
2. Click on any endpoint (e.g., "POST /api/v1/session/start")
3. Click "Try it out"
4. Fill in the request body
5. Click "Execute"
6. See the response below!

---

### Method 2: Postman (Recommended for beginners)

**What is Postman?** A free app for testing APIs with a nice visual interface.

1. Download Postman from [https://postman.com/downloads](https://postman.com/downloads)
2. Install and open it
3. Click "Import"
4. Select the file `postman_collection.json` from our project
5. The complete test collection loads automatically!
6. Click on "1. Start Session" → "Send"
7. Copy the `session_token` from the response
8. Update the `session_token` variable in Postman
9. Continue with other requests in order

---

### Method 3: curl (Command Line)

curl is a command-line tool for making HTTP requests. It's included on Mac and Linux. On Windows, use Git Bash or install curl separately.

**Start a session:**
```bash
curl -X POST "http://localhost:8000/api/v1/session/start" \
     -H "Content-Type: application/json" \
     -d '{"user_id": "student_001", "starting_difficulty": 1}'
```

**Get a question** (replace TOKEN with your actual session_token):
```bash
curl "http://localhost:8000/api/v1/question/next/TOKEN"
```

**Submit an answer** (replace TOKEN and QUESTION_ID):
```bash
curl -X POST "http://localhost:8000/api/v1/answer/submit" \
     -H "Content-Type: application/json" \
     -d '{
       "session_token": "TOKEN",
       "question_id": QUESTION_ID,
       "answer_text": "A variable is a named storage location that holds a value which can change during execution.",
       "time_taken_seconds": 35.0,
       "paste_detected": false
     }'
```

**Get security report:**
```bash
curl "http://localhost:8000/api/v1/security/report/TOKEN"
```

---

### Sample API Responses

**Start Session Response:**
```json
{
  "session_token": "sess_a3f9b2e1-4d5c-11ee-be56-0242ac120002",
  "user_id": "student_001",
  "message": "🎯 Quiz session started!",
  "current_difficulty": 1,
  "instructions": "Step 1: Copy your session_token. Step 2: Call GET /api/v1/question/next/{token}..."
}
```

**Get Question Response:**
```json
{
  "question_id": 1,
  "question_text": "What is a variable in programming?",
  "difficulty_level": 1,
  "difficulty_label": "Easy",
  "topic": "programming_basics",
  "hint": "💡 Take your time. Think about the core concept.",
  "instructions": "Submit your answer to POST /api/v1/answer/submit"
}
```

**Submit Answer Response:**
```json
{
  "similarity_score": 0.8234,
  "similarity_percentage": 82.3,
  "performance_label": "Excellent",
  "key_concepts_found": ["storage", "value", "memory"],
  "key_concepts_missing": ["identifier", "named"],
  "cheating_score": 0.0821,
  "risk_level": "Low",
  "security_flags": [],
  "next_difficulty": 2,
  "difficulty_changed": true,
  "difficulty_message": "🎯 Excellent work! Moving from Easy → Medium!",
  "next_question_id": 4,
  "feedback": "🌟 Excellent answer! You demonstrated strong understanding."
}
```

---

## SECTION 7: Example Workflow

Here's a complete real-world example of a student taking a quiz:

### Step 1: Start the Quiz
```bash
POST /api/v1/session/start
Body: {"user_id": "alice_smith", "starting_difficulty": 1}

Response: session_token = "sess_abc123"
```

### Step 2: Get First Question (Easy)
```bash
GET /api/v1/question/next/sess_abc123

Response: "What is a variable in programming?" (Difficulty: Easy)
```

### Step 3: Answer Correctly (Fast Enough)
```bash
POST /api/v1/answer/submit
{
  "session_token": "sess_abc123",
  "question_id": 1,
  "answer_text": "A variable stores data with a name, like x = 5 in Python.",
  "time_taken_seconds": 20.0
}

Response: similarity=0.72, cheating_score=0.05, next_difficulty=1 (same, need more answers)
```

### Step 4: Answer 2nd Question Well
```bash
Similar to above...
Response: similarity=0.85, cheating_score=0.03, next_difficulty=2 (UPGRADED to Medium!)
```

### Step 5: Get Medium Question
```bash
GET /api/v1/question/next/sess_abc123

Response: "Explain the difference between a list and a tuple in Python." (Difficulty: Medium)
```

### Step 6: Paste Answer Too Quickly (Gets Flagged!)
```bash
POST /api/v1/answer/submit
{
  "session_token": "sess_abc123",
  "question_id": 4,
  "answer_text": "A list is mutable and uses square brackets [...]. A tuple is immutable and uses parentheses (...). Lists support operations like append(), remove(). Tuples are faster and memory-efficient.",
  "time_taken_seconds": 1.2,   ← 1.2 seconds for 35 words? SUSPICIOUS!
  "paste_detected": true        ← Browser detected paste!
}

Response: cheating_score=0.74, risk_level="High", 
          flags=["⚡ Submitted in 1.2s (min expected: 18s)", "📋 Browser paste detected"]
```

### Step 7: View Security Report
```bash
GET /api/v1/security/report/sess_abc123

Response: {
  "overall_risk_score": 0.37,
  "risk_level": "Medium",
  "total_answers": 3,
  "suspicious_answers": 1,
  "recommendation": "🟡 Some suspicious patterns. Monitor closely."
}
```

---

## SECTION 8: Common Errors and Fixes

### Error 1: `ModuleNotFoundError: No module named 'fastapi'`
**Meaning:** Package not installed  
**Fix:**
```bash
# Make sure virtual environment is activated! You should see (venv) in prompt
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows

# Then install packages
pip install -r requirements.txt
```

### Error 2: `Address already in use`
**Meaning:** Port 8000 is already being used by another program  
**Fix Option A:** Use a different port:
```bash
uvicorn app.main:app --reload --port 8001
```
**Fix Option B:** Find and stop the process using port 8000:
```bash
# Mac/Linux:
lsof -ti:8000 | xargs kill -9

# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID_NUMBER> /F
```

### Error 3: `Connection refused` (Redis error in logs)
**Meaning:** Redis is not running  
**Fix:** This is NOT a fatal error! The app keeps working with memory cache. Ignore this warning OR install Redis (see Section 5).

### Error 4: `Python was not found` (Windows)
**Meaning:** Python not added to PATH during installation  
**Fix:** 
1. Uninstall Python
2. Reinstall with "Add Python to PATH" checkbox ✅ checked
3. Restart Command Prompt

### Error 5: `uvicorn: command not found`
**Meaning:** Virtual environment not activated or uvicorn not installed  
**Fix:**
```bash
# Activate virtual environment first:
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows

# Install uvicorn:
pip install uvicorn
```

### Error 6: `No such file or directory: 'venv/Scripts/activate'`
**Meaning:** Virtual environment wasn't created correctly  
**Fix:**
```bash
# Delete old venv and recreate:
rm -rf venv                # Mac/Linux
rmdir /s venv              # Windows

python -m venv venv
```

### Error 7: Sentence Transformers model download fails
**Meaning:** No internet connection or download was interrupted  
**Fix:**
```bash
# Try manually downloading:
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```
If it still fails, the app automatically falls back to keyword-based similarity.

### Error 8: `sqlite3.OperationalError: database is locked`
**Meaning:** Two processes trying to write to SQLite at the same time  
**Fix:** Stop all running servers and restart:
```bash
# Press Ctrl+C to stop current server
# Then restart:
uvicorn app.main:app --reload --port 8000
```

---

## SECTION 9: Docker Setup

### What is Docker? (Beginner Explanation)

Imagine you're a chef. Your recipe works perfectly in YOUR kitchen, but when your friend tries it in THEIR kitchen, something goes wrong — wrong pan size, different stove temperature.

**Docker solves this by shipping your kitchen along with your recipe.**

Technically: Docker creates a "container" — a lightweight, isolated environment that includes your app AND all its dependencies. It runs identically on any computer that has Docker installed.

**Why use Docker?**
- ✅ "Works on my machine" problem is solved forever
- ✅ Easy to share with your team
- ✅ Same container runs on your laptop AND on cloud servers
- ✅ Easy to scale (run multiple copies)

### Installing Docker

**Windows:**
1. Check if your Windows supports WSL2: Windows 10 version 2004+ or Windows 11
2. Download Docker Desktop from [https://docker.com/products/docker-desktop](https://docker.com/products/docker-desktop)
3. Run the installer
4. Restart your computer when asked
5. Open Docker Desktop — let it start (takes 1-2 minutes)
6. Verify: Open Command Prompt and type `docker --version`

**Mac:**
1. Download Docker Desktop from [https://docker.com/products/docker-desktop](https://docker.com/products/docker-desktop)
   - Choose "Mac with Apple Silicon" or "Mac with Intel Chip" based on your Mac
2. Open the `.dmg` file and drag Docker to Applications
3. Open Docker from Applications
4. Verify: `docker --version`

**Linux (Ubuntu):**
```bash
sudo apt update
sudo apt install docker.io docker-compose
sudo systemctl start docker
sudo usermod -aG docker $USER   # Allow running without sudo
# Log out and back in
docker --version
```

---

### Running with Docker (Step-by-Step)

**Step 1: Make sure Docker Desktop is running**
You should see the Docker whale icon in your taskbar.

**Step 2: Open Terminal in the project folder**

**Step 3: Build and start the application**
```bash
docker compose up --build
```
Breaking this down:
- `docker compose` → Use docker compose tool
- `up` → Start all services
- `--build` → Rebuild the images (needed first time or after code changes)

**You'll see lots of output.** Wait for:
```
adaptive_engine_api   | ✅ Server is running at http://localhost:8000
```

**Step 4: Test it's working**
```bash
curl http://localhost:8000/health
# Should return: {"status": "healthy"}
```

**Step 5: Stop everything**
```bash
# Press Ctrl+C in the terminal running docker compose
# OR in a separate terminal:
docker compose down
```

### Useful Docker Commands

```bash
# Start in background (no output in terminal):
docker compose up -d

# See running containers:
docker compose ps

# View logs from the API:
docker compose logs api

# View logs from Redis:
docker compose logs redis

# Restart just the API (after code change):
docker compose restart api

# Stop and remove everything (including volumes/data):
docker compose down -v

# Access the container's terminal (for debugging):
docker compose exec api bash
```

---

## SECTION 10: AWS Deployment

### What is AWS?

AWS (Amazon Web Services) is like renting a computer in Amazon's data center.

Instead of running the server on YOUR computer (which can only be accessed from your network), AWS lets you run it on a computer accessible to the ENTIRE INTERNET.

### Why EC2?

EC2 (Elastic Compute Cloud) is the most basic AWS service — it's literally just a virtual computer (called an "instance") you can rent by the hour.

Think of it as: **renting a computer from Amazon, 24/7, accessible worldwide.**

### Step-by-Step EC2 Deployment

#### Step 1: Create AWS Account
1. Go to [https://aws.amazon.com](https://aws.amazon.com)
2. Click "Create an AWS Account"
3. Enter email, set password
4. Enter credit card (you won't be charged if using free tier)
5. Verify phone number
6. Choose "Basic Support - Free"

> 💡 **Free Tier**: AWS gives you 750 hours/month of a small EC2 instance FREE for 12 months.

#### Step 2: Launch an EC2 Instance
1. Log in to [console.aws.amazon.com](https://console.aws.amazon.com)
2. Click the search bar at top, type "EC2", click EC2
3. Click "Launch Instance" (orange button)
4. Fill in:
   - **Name**: `adaptive-engine-server`
   - **Application and OS Images**: Select "Ubuntu Server 22.04 LTS"
   - **Instance type**: Select "t2.micro" (Free Tier eligible ✅)
   - **Key pair**: Click "Create new key pair"
     - Name: `mykey`
     - Type: RSA
     - Format: `.pem` (Mac/Linux) or `.ppk` (Windows)
     - Click "Create key pair" — this downloads a file. **KEEP IT SAFE!**
   - **Network settings**: Check "Allow HTTP traffic" and "Allow HTTPS traffic"
5. Click "Launch Instance"

#### Step 3: Connect to Your Server

**Mac/Linux:**
```bash
# Move your key file and set permissions
chmod 400 ~/Downloads/mykey.pem

# Connect (replace YOUR_IP with the Public IPv4 address from EC2 console)
ssh -i ~/Downloads/mykey.pem ubuntu@YOUR_IP
```

**Windows (using PuTTY):**
1. Download PuTTY from [https://putty.org](https://putty.org)
2. Open PuTTY
3. Host Name: `ubuntu@YOUR_IP`
4. Connection → SSH → Auth → Browse for your `.ppk` file
5. Click "Open"

#### Step 4: Install Dependencies on the Server
```bash
# Update the system
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install -y python3.11 python3.11-pip python3.11-venv git

# Install Redis (optional)
sudo apt install -y redis-server
sudo systemctl start redis
sudo systemctl enable redis  # Start Redis on boot
```

#### Step 5: Deploy the Application
```bash
# Clone your project (or upload files using scp)
git clone https://github.com/yourusername/adaptive-engine.git
cd adaptive-engine

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install packages
pip install -r requirements.txt

# Copy environment config
cp .env.example .env
```

#### Step 6: Start the Server in Production

For production, we use a process manager so the server restarts if it crashes:

```bash
# Install a process manager
pip install supervisor

# Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

> **Note:** For real production, use `gunicorn` or `supervisor` to keep the server running after you disconnect. This basic setup is fine for learning.

#### Step 7: Open the Firewall Port
1. In AWS Console, go to EC2 → Instances → Click your instance
2. Scroll down → Click "Security" tab
3. Click the Security Group link
4. Click "Edit inbound rules"
5. Click "Add rule"
   - Type: Custom TCP
   - Port range: 8000
   - Source: 0.0.0.0/0 (allow from anywhere)
6. Click "Save rules"

#### Step 8: Test Your Live API
```bash
# From your local computer:
curl http://YOUR_IP:8000/health
# Should return: {"status": "healthy"}
```

Your API is now live on the internet! Share `http://YOUR_IP:8000/docs` with anyone.

> ⚠️ **Important**: When you're done testing, **stop or terminate your EC2 instance** to avoid charges!

---

## SECTION 11: Folder Structure

```
adaptive_engine/                    ← Main project folder
│
├── app/                            ← All Python application code
│   ├── __init__.py                 ← Makes 'app' a Python package
│   ├── main.py                     ← 🚀 App entry point (start here!)
│   │
│   ├── routes/                     ← API endpoints (URL handlers)
│   │   ├── __init__.py
│   │   ├── questions.py            ← /session/start, /question/next
│   │   ├── answers.py              ← /answer/submit, /answer/history
│   │   ├── difficulty.py           ← /difficulty/status
│   │   └── security.py             ← /security/report, /cache/status
│   │
│   ├── services/                   ← Business logic (the "brain")
│   │   ├── __init__.py
│   │   ├── similarity_service.py   ← 🤖 AI text comparison
│   │   ├── security_service.py     ← 🔐 Anti-cheat detection
│   │   ├── difficulty_service.py   ← 📈 Adaptive difficulty algorithm
│   │   └── session_service.py      ← 🎫 Session management
│   │
│   ├── models/                     ← Data definitions
│   │   ├── __init__.py
│   │   ├── database.py             ← SQLite setup & table creation
│   │   └── schemas.py              ← Request/response data shapes
│   │
│   └── utils/                      ← Helper utilities
│       ├── __init__.py
│       └── cache.py                ← ⚡ Redis/memory cache manager
│
├── tests/                          ← Automated tests
│   └── test_api.py                 ← Test all endpoints
│
├── scripts/                        ← Helper scripts
│   └── setup.py                    ← Verify installation
│
├── requirements.txt                ← Package dependencies list
├── Dockerfile                      ← Docker container recipe
├── docker-compose.yml              ← Multi-container orchestration
├── .env.example                    ← Configuration template
├── postman_collection.json         ← Import into Postman for testing
└── README.md                       ← This file!
```

### Key File Relationships

```
Request comes in
      ↓
   main.py         ← FastAPI app, registers routes
      ↓
  routes/*.py      ← "What should happen for this URL?"
      ↓
 services/*.py     ← "How do we actually do it?" (business logic)
      ↓
models/database.py ← "How do we read/write the database?"
      ↓
  utils/cache.py   ← "Can we cache this for speed?"
```

---

## SECTION 12: Future Improvements

Here are features you could add to make this system more powerful:

### 🔐 Security
- [ ] **JWT Authentication**: Secure API with login tokens (currently open to anyone)
- [ ] **Rate Limiting**: Prevent abuse (max 100 requests/minute per user)
- [ ] **IP Tracking**: Flag the same IP submitting for multiple users
- [ ] **Keystroke Analytics**: Track typing rhythm (real typists have varied patterns)

### 📊 Analytics
- [ ] **Admin Dashboard**: Web interface to view all sessions and risk reports
- [ ] **Export to CSV**: Download session data for offline analysis
- [ ] **Real-time alerts**: Notify admins when high-risk events are detected
- [ ] **Historical trends**: "This student's performance improved 30% this month"

### 🤖 AI Improvements
- [ ] **Better AI Model**: Use `all-mpnet-base-v2` for more accurate similarity
- [ ] **GPT Integration**: Use ChatGPT to give more detailed answer feedback
- [ ] **Auto Question Generation**: GPT generates new questions on any topic
- [ ] **Multi-language Support**: Handle answers in multiple languages

### 🏗️ Infrastructure
- [ ] **PostgreSQL**: Replace SQLite with PostgreSQL for production scale
- [ ] **Async Database**: Use async SQLAlchemy for better performance
- [ ] **WebSockets**: Real-time updates to frontend without polling
- [ ] **Kubernetes**: Auto-scale to handle thousands of concurrent users
- [ ] **CDN**: Serve the AI model from a CDN for faster startup

### 📱 Features
- [ ] **Topic Progression**: Track what topics have been mastered
- [ ] **Spaced Repetition**: Re-ask questions you got wrong at optimal intervals
- [ ] **Peer Comparison**: "You scored better than 70% of students"
- [ ] **Certificate Generation**: PDF certificate when completing a topic

---

## 📬 Quick Reference Card

| Task | Command |
|------|---------|
| Activate venv (Mac/Linux) | `source venv/bin/activate` |
| Activate venv (Windows) | `venv\Scripts\activate` |
| Start server | `uvicorn app.main:app --reload` |
| Start server (different port) | `uvicorn app.main:app --reload --port 8001` |
| Run tests | `pytest tests/test_api.py -v` |
| Run setup checker | `python scripts/setup.py` |
| Start with Docker | `docker compose up --build` |
| Stop Docker | `docker compose down` |
| Open API docs | http://localhost:8000/docs |
| Check health | http://localhost:8000/health |

---

## 🆘 Getting Help

1. **Check Section 8** (Common Errors) first
2. **Run the setup checker**: `python scripts/setup.py`
3. **Check server logs** — they often contain the exact error message
4. **Search the error message** on Google or Stack Overflow
5. **Paste the full error** (not just the last line) when asking for help

---

*Built with ❤️ using FastAPI, Sentence Transformers, and SQLite*
