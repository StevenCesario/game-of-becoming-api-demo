# 🎮 Codename: The Game of Becoming

A robust FastAPI backend that transforms personal growth and daily journaling into an engaging, stat-based role-playing game. This project is currently in active development, and "The Game of Becoming" serves as its working title.

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-teal)](https://fastapi.tiangolo.com)
[![CI/CD](https://github.com/StevenLomon/game-of-becoming/actions/workflows/ci.yml/badge.svg)](https://github.com/StevenLomon/game-of-becoming/actions/workflows/ci.yml)
[![Testing](https://img.shields.io/badge/Tests-100%25%20Passed-brightgreen)](tests/)

## 🎯 Core Concept

Traditional journaling and habit-tracking apps often fail because they lack engagement. This application solves this by applying proven game mechanics to personal development. The core concept is currently being explored under the name "The Game of Becoming."

-   **Problem:** It's hard to stay motivated with long-term goals. Progress is often invisible.
-   **Solution:** Frame daily actions as "quests" and personal growth as "leveling up." Provide tangible, visible feedback (stats, XP) for every positive action, creating a powerful motivation loop.

## ✨ Key Features

-   **Secure User Authentication**: Full user registration and login system using JWT (JSON Web Tokens) for stateless, secure sessions.
-   **Character Creation**: Users create a unique in-game character to represent their journey.
-   **AI-Powered Intentions**: (Mocked) AI service helps users craft powerful, actionable daily intentions.
-   **Focus Blocks**: A core game mechanic where users commit to and complete timed blocks of focused work.
-   **Stat Progression**: Earn XP and level up stats (e.g., Intellect, Discipline, Mindfulness) by completing intentions and focus blocks.
-   **Relational Database**: Robust data persistence using SQLAlchemy and PostgreSQL, with migrations managed by Alembic.
-   **Automated Testing**: Comprehensive integration test suite using Pytest to ensure API reliability.
-   **Continuous Integration**: GitHub Actions pipeline automatically installs dependencies, runs tests, and validates code on every push.

## 🏗️ System Architecture
User Client (e.g., Mobile/Web App)
↓ (HTTPS API Requests)
FastAPI Application
|
├──> Secure Authentication (JWT)
|
├─> Business Logic (Intentions, Focus Blocks)
|     ↓
|   (Mock AI Service Call)
|
├──> Database Layer (SQLAlchemy ORM)
↓
PostgreSQL Database (Managed by Alembic)

## 🚀 How to Run Locally

### Prerequisites
-   Python 3.11+
-   PostgreSQL installed and running

### 1. Clone and Set Up

```console
# Clone the repository
git clone https://github.com/your-username/game-of-becoming.git
cd game-of-becoming

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure the Database

You will need to create a database in PostgreSQL and provide its connection URL to the application.

1. Create a database, for example, named `becoming_db`.
2. Open the `alembic.ini` file and find the `sqlalchemy.url `line. Update it with your database connection string.

```console
# Example for a user 'myuser' with password 'mypass'
sqlalchemy.url = postgresql://myuser:mypass@localhost/becoming_db
```

3. Open `app/database.py` and update the `DATABASE_URL` variable with the same connection string.

### 3. Apply Database Migrations
With the configuration set, apply the schema to your newly created database.
```console
alembic upgrade head
```

### 4. Run the API Server
```console
uvicorn app.main:app --reload
```
The API will be available at `http://127.0.0.1:8000.`

### 5. Explore the API
Open your browser to `http://127.0.0.1:8000/docs` to see the interactive Swagger UI documentation, where you can test all the endpoints.

## 🧪 Testing
The project is configured with a complete integration test suite that runs against a separate test database, ensuring that tests do not interfere with development data.

```console
# To run the test suite:
pytest -v
```

Tests are also automatically executed in a clean environment on every `git push` via the GitHub Actions CI pipeline, providing immediate feedback on code changes.

**Built by Steven Lomon Lennartsson** 🌱