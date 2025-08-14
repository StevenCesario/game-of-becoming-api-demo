# 🎮 Codename: The Game of Becoming

A robust FastAPI backend that transforms personal development and goal achievement into an engaging, stat-based role-playing game. This project is currently in active development, and "The Game of Becoming" serves as its working title.

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-teal)](https://fastapi.tiangolo.com)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red)](https://www.sqlalchemy.org/)
[![CI/CD](https://github.com/stevenlomon/game-of-becoming-api-demo/actions/workflows/ci.yml/badge.svg)](https://github.com/stevenlomon/game-of-becoming-api-demo/actions/workflows/ci.yml)

> ⚠️ **Demonstration Repository:** This repository showcases the architecture, testing, and API design of a larger, proprietary project. The core business logic in the `services` layer has been replaced with simplified, mock implementations for demonstration purposes.

## 🎯 The Problem: The "Self-Development Trap"

For ambitious entrepreneurs and professionals, the path to growth is often a frustrating cycle. We know *what* to do, but execution blockers, procrastination, and a loss of self-trust create a loop of "self-development hell." Traditional habit trackers and to-do lists fail because they lack engagement and don't address the underlying motivational challenges.

This system is designed to break that cycle.

## ✨ The Solution: Gamify Your Growth

This API provides the backend foundation for an application that reframes personal and business growth as an engaging role-playing game. By applying the same proven game mechanics we were addicted to in our youth, it creates a powerful, intrinsic motivation loop.

* **Problem:** It's hard to stay consistent when progress feels invisible.
* **Solution:** Frame daily actions as **Quests**, focused work as **Execution Sprints**, and personal growth as **Leveling Up**. Provide tangible, visible feedback (XP, Character Stats) for every action taken, turning failure into a learning opportunity and success into a rewarding experience.

## 🔑 Key Features & Technical Highlights

⚡️ **Modern & Robust Backend**
* Built with **FastAPI** for high-performance, async-ready API endpoints.
* **SQLAlchemy 2.0** for a fully type-annotated, modern ORM experience.
* **Pydantic V2** for rigorous data validation, serialization, and clear API contracts.
* **Alembic** for safe and reliable database schema migrations.

🛡️ **Secure & Scalable Architecture**
* **Secure User Authentication** with JWT for stateless, secure sessions.
* **Clean Architecture** with a clear separation of concerns (API endpoints, business logic `services`, data access `crud`, and database `models`).
* **Dependency Injection** used throughout for maintainable and testable code.
* **Eager Loading** (`joinedload`) implemented for efficient database queries, solving the N+1 problem.

🎮 **Engaging Game Mechanics**
* **Character Progression:** Users earn XP and level up core stats like `Clarity`, `Discipline`, and `Resilience` by completing their goals.
* **Daily Intentions:** A core game loop where users set a single, measurable goal for the day.
* **Focus Blocks:** Timed execution sprints to "chunk down" the daily intention and make progress.
* **"Fail Forward" System:** A "Recovery Quest" mechanic that reframes failure as an opportunity to gain `Resilience` XP.

🤖 **AI-Ready Service Layer**
* A "hollowed-out" service layer demonstrates how to cleanly integrate with external AI providers (like Anthropic Claude) for intelligent feedback and coaching, without coupling the core application to a specific vendor.

✅ **Fully Tested & Automated**
* Comprehensive integration test suite using **Pytest**.
* Separate in-memory test database ensures tests are isolated and fast.
* **GitHub Actions CI/CD pipeline** automatically runs tests on every push to `main`, ensuring code quality and reliability.

## 🏗️ System Architecture
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