# ============================================================
# Dockerfile
# Instructions for building a Docker container for our app
#
# What is Docker? (BEGINNER EXPLANATION)
# =========================================
# Imagine you have a recipe for a cake.
# No matter which kitchen you use (your laptop, a friend's PC, 
# or a cloud server), if you follow the recipe exactly, 
# you get the SAME cake every time.
#
# Docker is like that recipe for your software.
# It packages your app + ALL its dependencies into a "container"
# that runs IDENTICALLY everywhere.
#
# Without Docker: "It works on MY machine!" 😤
# With Docker: "It works everywhere!" ✅
#
# How to read this file:
# Each line starting with a word in CAPITALS is a Docker instruction.
# ============================================================

# ---- START FROM A BASE IMAGE ----
# Think of this as choosing your kitchen.
# We use Python 3.11 running on a lightweight Linux (slim)
FROM python:3.11-slim

# ---- SET THE WORKING DIRECTORY ----
# All commands will run from /app folder inside the container
# Like cd /app
WORKDIR /app

# ---- COPY REQUIREMENTS FIRST ----
# Why copy requirements first? Docker CACHES each step.
# If we copy requirements first, it only re-downloads packages
# when requirements.txt changes (not on every code change!)
COPY requirements.txt .

# ---- INSTALL PYTHON PACKAGES ----
# --no-cache-dir = don't save download cache (saves disk space)
# --upgrade pip = make sure pip itself is up to date
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ---- COPY OUR APPLICATION CODE ----
# Copy everything from our project folder to /app in the container
COPY . .

# ---- EXPOSE PORT ----
# Tell Docker our app uses port 8000
# (This doesn't open the port yet - docker-compose does that)
EXPOSE 8000

# ---- START THE APP ----
# This command runs when the container starts
# uvicorn = the server
# app.main:app = the FastAPI app object
# --host 0.0.0.0 = listen on all network interfaces
# --port 8000 = listen on port 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
