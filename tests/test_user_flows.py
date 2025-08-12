# No need to import TestClient here, the `client` fixture provides it.

def test_register_user_success(client):
    """
    Test successful user registration.
    The `client` argument is automatically provided by pytest from conftest.py
    """
    response = client.post(
        "/register",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "hrga": "My test HRGA",
            "password": "a_strong_password"
        }
    )
    
    # Assert that the request was successful
    assert response.status_code == 201

    # Assert the response body is correct
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["name"] == "Test User"
    assert "id" in data
    
    # IMPORTANT: Assert that the password is NOT returned
    assert "password_hash" not in data


def test_register_user_duplicate_email(client):
    """
    Test that registering with a duplicate email fails.
    """
    user_data = {
        "name": "Test User",
        "email": "test@example.com",
        "hrga": "My test HRGA",
        "password": "a_strong_password"
    }

    # First registration should succeed
    response1 = client.post("/register", json=user_data)
    assert response1.status_code == 201

    # Second registration with the same email should fail
    response2 = client.post("/register", json=user_data)
    assert response2.status_code == 400
    assert response2.json() == {"detail": "Email already registered. Ready to log in instead?"}