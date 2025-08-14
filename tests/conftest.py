import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_db
from app.models import Base

# --- Test Database Setup ---
# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}, # Required for SQLite
    poolclass=StaticPool, # Use a static pool for in-memory DB
)

# Create a new sessionmaker for the test database
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# --- Pytest Fixtures ---

@pytest.fixture(scope="function")
def db_session():
    """
    Pytest fixture to create a new database session for each test function.
    It creates all tables, yields the session, and then drops all tables.
    """
    # Create the database tables
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop the database tables
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    """Pytest fixture to create a TestClient with the database dependency overridden."""
    def override_get_db():
        """Dependency override to use the test database."""
        try:
            yield db_session
        finally:
            db_session.close()

    # Apply the dependency override
    app.dependency_overrides[get_db] = override_get_db
    
    yield TestClient(app)

    # Clean up the override after the test is done
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def user_token(client):
    payload = {
        "name": "Demo", "email": "demo@example.com",
        "hrga": "LinkedIn Outreach", "password": "pass123123123"
    }
    r = client.post("/register", json=payload)
    assert r.status_code == 201, f"registration failed: {r.json()}"

    login = client.post("/login", data={
        "username": "demo@example.com", "password": "pass123123123"
    })
    assert login.status_code == 200, f"login failed: {login.json()}"

    return login.json()["access_token"]   # now guaranteed to exist