# 🎮 Codename: xecution.ai

A robust FastAPI backend for an AI-powered behavioral transformation platform designed to help entrepreneurs improve execution consistency.

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-teal)](https://fastapi.tiangolo.com)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red)](https://www.sqlalchemy.org/)
[![CI/CD](https://github.com/stevenlomon/game-of-becoming-api-demo/actions/workflows/ci.yml/badge.svg)](https://github.com/stevenlomon/game-of-becoming-api-demo/actions/workflows/ci.yml)

> ⚠️ **Demonstration Repository:** This repository showcases the architecture, testing, and API design of a larger, proprietary project. The core business logic in the `services` layer has been replaced with simplified, mock implementations for demonstration purposes.

## 🎯 The Problem: Execution Over Motivation

Ambitious entrepreneurs know what to do but struggle with consistent execution. Traditional productivity tools fail because they don't address the core challenge: maintaining motivation through the inevitable ups and downs of building something meaningful.

The gap isn't knowledge—it's the psychological framework needed to turn intentions into consistent action.

## ✨ The Solution: Gamify Your Business Growth

This API powers a system that transforms business growth into an engaging, measurable experience using proven game mechanics and behavioral psychology.

**Core Approach**:
* **Daily Intentions** replace overwhelming to-do lists with single, focused output.
* **Execution Sprints** break work into manageable, timed sessions.
* **Character Progression** provides tangible feedback through XP, stats, and streaks.
* **"Fail Forward" Mechanics** turn setbacks into learning opportunities with AI-guided reflection.
**The Result:** A sustainable motivation system that makes consistent execution feel rewarding rather than draining, helping users build momentum through small, daily wins that compound into significant business growth.

## 🔑 Key Features & Technical Highlights

⚡️ **Modern & Robust Backend**
* Built with **FastAPI** for high-performance, async-ready API endpoints.
* **SQLAlchemy 2.0** for a fully type-annotated, modern ORM experience.
* **Pydantic V2** for rigorous data validation, clear API contracts, and declarative, computed_field responses.
* **Alembic** for safe and reliable database schema migrations.

🛡️ **Secure & Scalable Architecture**
* **Secure User Authentication** with JWT for stateless, secure sessions.
* **Clean Architecture** with a clear separation of concerns (API endpoints, business logic `services`, data access `crud`, and database `models`).
* **Atomic Endpoints** for critical state changes (e.g., completing a daily intention), ensuring data integrity across multiple database tables in a single transaction.
* **Dependency Injection** used throughout for maintainable and testable code.
* **Declarative State Endpoint** (/api/users/me/game-state) providing a single source of truth for the frontend client on load.

🤖 **Conversational AI Core**
* **Conversational Onboarding Flow** (/api/onboarding/step) that guides users to define their core vision and goals through a multi-step dialogue with an AI Clarity coach.
* **Stateful Conversational API** for creating Daily Intentions, demonstrating how to manage a multi-step dialogue with a user via a state machine pattern.
* **Provider Factory** (llm_providers/factory.py) makes the system extensible and pluggable for different AI services, cleanly decoupling the application from a specific vendor.

🎮 **Core Behavioral Mechanics**
* **The Daily Streak:** A core retention mechanic that rewards daily consistency, with a forgiving "grace day" rule to encourage users after a setback.
* **Character Progression:** Users earn XP and level up core stats like `Clarity`, `Discipline`, and `Resilience` by completing their execution sprints and daily intentions.
* **"Fail Forward" System:** A "Recovery Quest" mechanic that reframes failure as an opportunity to gain Resilience and preserve the user's streak.

✅ **Fully Tested & Automated**
* Comprehensive integration and unit test suite using **Pytest**.
* **Time-Travel Testing** with `freezegun` to reliably test time-sensitive logic like the daily streak mechanic.
* Separate in-memory test database ensures tests are isolated and fast.
* **GitHub Actions CI/CD pipeline** automatically runs tests on every push.

## 🏗️ System Architecture
```text
User Client (Web/Mobile App)
       │
       ▼ (HTTPS API Requests)
+---------------------------------+
|      FastAPI Application        |
|  (main.py - Endpoint Layer)     |
+---------------------------------+
       │
       ▼ (Business Logic Delegation)
+---------------------------------+
|      Service Layer              |
|  (services.py - Game Mechanics) |
+---------------------------------+
       │
       ▼ (Database Operations)
+---------------------------------+
|      Data Access Layer          |
|  (crud.py - Read/Write Logic)   |
+---------------------------------+
       │
       ▼ (ORM Mapping)
+---------------------------------+
|      Database Models & Schema   |
|  (models.py, schemas.py)        |
+---------------------------------+
       │
       ▼
+---------------------------------+
|      PostgreSQL Database        |
|  (Migrations via Alembic)       |
+---------------------------------+
```

## 🚀 How to Run Locally

### Prerequisites
* Python 3.12+
* PostgreSQL installed and running

### 1. Clone and Set Up

```bash
# Clone the repository
git clone [https://github.com/stevenlomon/game-of-becoming-api-demo.git](https://github.com/stevenlomon/game-of-becoming-api-demo.git)
cd game-of-becoming-api-demo

# Create and activate a virtual environment
python -m venv env
source env/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the project root. You can do this by copying the `.env.example` file if one exists, or by creating a new file and adding the following content:

```bash
DATABASE_URL="postgresql://user:password@localhost/becoming_db"
SECRET_KEY="your_super_secret_random_string_here"
# ANTHROPIC_API_KEY="sk-..." # Optional, for connecting to a real AI service
```

*Replace the values with your actual database connection string and a unique secret key.*

### 3. Apply Database Migrations
With the configuration set, apply the schema to your newly created database.
```bash
alembic upgrade head
```

### 4. Run the API Server
```bash
uvicorn app.main:app --reload
```
The API will be available at `http://127.0.0.1:8000.`

### 5. Explore the API
Open your browser to `http://127.0.0.1:8000/docs` to see the interactive Swagger UI documentation, where you can test all the endpoints.

## 🧪 Testing
The project is configured with a complete integration test suite that runs against a separate test database, ensuring that tests do not interfere with development data.

```bash
# To run the test suite:
pytest -v
```

Tests are also automatically executed in a clean environment on every `git push` via the GitHub Actions CI pipeline, providing immediate feedback on code changes.

**Built by Steven Cesario** 🌱
