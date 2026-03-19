# ============================================================
# main.py - The heart of our application
# This file starts the web server and connects all the pieces
# ============================================================

# FastAPI is a modern web framework for building APIs with Python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# These are our own route files (like chapters of a book)
from app.routes import questions, answers, difficulty, security

# This sets up the database tables when the app starts
from app.models.database import init_db

# This creates the FastAPI application object
# Think of it like creating a new restaurant - this is the building
app = FastAPI(
    title="Adaptive Difficulty & Anti-Cheat Engine",
    description="""
    🎯 A smart interview/quiz system that:
    - Adapts question difficulty based on your performance
    - Detects suspicious patterns (copy-paste, too-fast answers)
    - Analyzes semantic similarity of answers
    - Generates a cheating risk score
    """,
    version="1.0.0"
)

# CORS = Cross-Origin Resource Sharing
# This allows web browsers to talk to our API
# Think of it like opening the door for visitors
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # Allow all websites (change in production)
    allow_credentials=True,
    allow_methods=["*"],      # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],      # Allow all headers
)

# This runs when the server starts
# Like a chef prepping the kitchen before opening
@app.on_event("startup")
async def startup_event():
    print("🚀 Server is starting...")
    init_db()  # Create database tables if they don't exist
    print("✅ Database ready!")
    print("✅ Server is running at http://localhost:8000")
    print("📚 API docs at http://localhost:8000/docs")

# Register all our route groups (like different departments)
app.include_router(questions.router, prefix="/api/v1", tags=["Questions"])
app.include_router(answers.router, prefix="/api/v1", tags=["Answers"])
app.include_router(difficulty.router, prefix="/api/v1", tags=["Difficulty"])
app.include_router(security.router, prefix="/api/v1", tags=["Security"])

# This is the home page of our API
@app.get("/")
def home():
    return {
        "message": "Welcome to the Adaptive Difficulty & Anti-Cheat Engine!",
        "docs": "Visit /docs to see all available APIs",
        "status": "running"
    }

# Health check endpoint - used to verify the server is alive
@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "All systems operational"}
