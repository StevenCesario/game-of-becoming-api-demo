# No need to import TestClient here, the `client` fixture provides it
from freezegun import freeze_time

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
            "password": "a_strong_password"
        }
    )
    
    # Assert that the request was successful
    assert response.status_code == 201

    # Assert the response body is correct
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["hrga"] is None # HRGA is now null at registration
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

@freeze_time("2025-08-27")
def test_onboarding_sets_hrga_and_starts_streak(client, user_token):
    """Verify `PUT /users/me` sets the HRGA and starts the user's streak at 1."""
    headers = {"Authorization": f"Bearer {user_token}"}

    # 1. Check initial state
    initial_user = client.get("/users/me", headers=headers).json()
    assert initial_user["hrga"] is None
    assert initial_user["current_streak"] == 0

    # 2. Complete the onboarding
    client.put("/users/me", headers=headers, json={"hrga": "My new awesome HRGA!"})

    # 3. Verify the final state
    final_user = client.get("/users/me", headers=headers).json()
    assert final_user["hrga"] == "My new awesome HRGA!"
    assert final_user["current_streak"] == 1