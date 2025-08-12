from fastapi.testclient import TestClient
from app.main import app # Import our main FastAPI instance

# Create a TestClient instance
client = TestClient(app)

def test_read_root():
    """Test that the root endpoint '/' returns a 200 OK status and the expected JSON response"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "message": "Welcome to The Game of Becoming API!",
        "description": "Ready to turn your exectution blockers into breakthrough momentum?",
        "docs": "Visit /docs for interactive API documentation.",
    }