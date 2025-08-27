#Full, self-contained showcase of the daily loop endpoints
from freezegun import freeze_time
from datetime import datetime, timezone
from app import services

# --- Mocks ---
# These functions simulate the responses from our service layer. This allows us
# to test the API endpoints in isolation, without making real (and slow) AI calls.
def mock_intention_approved(db, user, intention_data):
    """A mock that simulates the service layer approving an intention."""
    return {
        "needs_refinement": False,
        "ai_feedback": "Mock AI Feedback: Approved!",
        "clarity_stat_gain": 1
    }

def mock_reflection_success(db, user, daily_intention):
    return {"succeeded": True, "ai_feedback": "Mock Success!", "recovery_quest": None, "discipline_stat_gain": 1, "xp_awarded": 20}

def mock_reflection_failed(db, user, daily_intention):
    return {"succeeded": False, "ai_feedback": "Mock Fail.", "recovery_quest": "What happened?", "discipline_stat_gain": 0, "xp_awarded": 0}

def mock_recovery_quest_coaching(db, user, result, response_text):
    return {"ai_coaching_feedback": "Mock Coaching.", "resilience_stat_gain": 1, "xp_awarded": 15}

# --- Tests ---

def test_create_and_get_daily_intention(client, user_token, monkeypatch):
    """
    Ensures the fundamental loop of creating and then reading an intention works.
    This confirms the data is being correctly saved and retrieved.
    """
    # We replace the real AI service with our simple "approved" mock.
    monkeypatch.setattr(services, "create_and_process_intention", mock_intention_approved)
    headers = {"Authorization": f"Bearer {user_token}"}
    payload = {"daily_intention_text": "Write tests", "target_quantity": 5, "focus_block_count": 3, "is_refined": True}

    # Step 1: Create the intention via a POST request.
    create_resp = client.post("/intentions", headers=headers, json=payload)
    assert create_resp.status_code == 201
    assert "id" in create_resp.json() # A robust check to confirm creation.

    # Step 2: Immediately retrieve the intention via a GET request.
    get_resp = client.get("/intentions/today/me", headers=headers)
    assert get_resp.status_code == 200
    # Step 3: Verify the content of the retrieved intention matches what we sent.
    assert get_resp.json()["daily_intention_text"] == "Write tests"

def test_complete_intention_updates_stats_and_streak(client, long_lived_user_token, monkeypatch):
    """
    This is a critical test for the core game loop and retention mechanic.
    It verifies that completing intentions on CONSECUTIVE days correctly
    increments the user's streak.
    """
    # We mock all the service functions this test will trigger.
    monkeypatch.setattr(services, "create_and_process_intention", mock_intention_approved)
    monkeypatch.setattr(services, "create_daily_reflection", mock_reflection_success)
    headers = {"Authorization": f"Bearer {long_lived_user_token}"} # Use the long-lived token for time-travel

    # --- Day 1 ---
    with freeze_time("2025-08-26"):
        # Onboarding is the first "successful action" that starts the streak.
        client.put("/users/me", headers=headers, json={"hrga": "Test HRGA"})
        
        # Simulate a full day's cycle: create, update progress, and complete.
        client.post("/intentions", headers=headers, json={"daily_intention_text": "Day 1", "target_quantity": 1, "focus_block_count": 1, "is_refined": True})
        client.patch("/intentions/today/progress", headers=headers, json={"completed_quantity": 1})
        client.post("/intentions/today/complete", headers=headers)
        
        # Verify that after the first day, the streak is 1.
        day1_user = client.get("/users/me", headers=headers).json()
        assert day1_user["current_streak"] == 1

    # --- Day 2 ---
    # We use the "Time Machine" to travel to the next day.
    with freeze_time("2025-08-27"):
        # Simulate the second full day's cycle for the SAME user.
        client.post("/intentions", headers=headers, json={"daily_intention_text": "Day 2", "target_quantity": 1, "focus_block_count": 1, "is_refined": True})
        client.patch("/intentions/today/progress", headers=headers, json={"completed_quantity": 1})
        client.post("/intentions/today/complete", headers=headers)
        
        # The core assertion: Verify the streak has correctly incremented to 2.
        day2_user = client.get("/users/me", headers=headers).json()
        assert day2_user["current_streak"] == 2

def test_full_fail_forward_recovery_quest_loop(client, user_token, monkeypatch):
    """
    Tests the "Fail Forward" philosophy. It ensures that failing a quest,
    reflecting on it, and completing the recovery quest correctly awards
    Resilience and preserves the user's streak.
    """
    # We mock all services, including the "failure" and "coaching" paths.
    monkeypatch.setattr(services, "create_and_process_intention", mock_intention_approved)
    monkeypatch.setattr(services, "create_daily_reflection", mock_reflection_failed)
    monkeypatch.setattr(services, "process_recovery_quest_response", mock_recovery_quest_coaching)
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # Step 1: Onboard the user to establish a baseline state.
    client.put("/users/me", headers=headers, json={"hrga": "Test HRGA"})
    start_stats = client.get("/users/me/stats", headers=headers).json()

    # Step 2: Create a daily intention.
    client.post("/intentions", headers=headers, json={"daily_intention_text": "stuff", "target_quantity": 5, "focus_block_count": 3, "is_refined": True})
    
    # Step 3: The user chooses to "Fail Forward" by hitting the fail endpoint.
    fail_resp = client.post("/intentions/today/fail", headers=headers)
    assert fail_resp.status_code == 200
    result_id = fail_resp.json()["id"] # Get the ID for the generated DailyResult
    
    # Step 4: The user completes the resulting Recovery Quest.
    client.post(f"/daily-results/{result_id}/recovery-quest", headers=headers, json={"recovery_quest_response": "I reflected."})

    # Step 5: Verify that the correct rewards have been given.
    end_stats = client.get("/users/me/stats", headers=headers).json()
    end_user = client.get("/users/me", headers=headers).json()
    
    # The user should gain Resilience and XP for their reflection.
    assert end_stats["resilience"] == start_stats["resilience"] + 1
    assert end_stats["xp"] == start_stats["xp"] + 15
    # Crucially, their streak is preserved (or started), rewarding the "Fail Forward" action.
    assert end_user["current_streak"] == 1