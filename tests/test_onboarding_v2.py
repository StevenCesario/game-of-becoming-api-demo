from app import schemas

def test_full_v2_onboarding_flow(client, user_token):
    """
    Tests the entire V2 conversational onboarding flow from start to finish.

    This test simulates a user progressing through each step of the mock
    state machine, verifying that:
    1. Each step correctly returns the next expected step.
    2. The final step saves the user's HLA (Highest Leverage Action).
    3. The user's streak is correctly initiated to 1 upon completion.
    """
    headers = {"Authorization": f"Bearer {user_token}"}

    # 1. Verify the user's initial state (no HLA, streak is 0)
    initial_user = client.get("/users/me", headers=headers).json()
    assert initial_user["hla"] is None
    assert initial_user["current_streak"] == 0

    # --- Step 1: Provide Business Stage ---
    payload = {
        "current_step": schemas.OnboardingStepName.AWAITING_BUSINESS_STAGE,
        "user_text": "SaaS"
    }
    response = client.post("/api/onboarding/step", headers=headers, json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["next_step"] == schemas.OnboardingStepName.AWAITING_STRETCH_GOAL
    assert "what's your 6-12 month stretch goal?" in data["ai_message"]

    # --- Step 2: Provide Stretch Goal ---
    payload = {
        "current_step": schemas.OnboardingStepName.AWAITING_STRETCH_GOAL,
        "user_text": "Reach $10k MRR"
    }
    response = client.post("/api/onboarding/step", headers=headers, json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["next_step"] == schemas.OnboardingStepName.AWAITING_CONSTRAINT_CHOICE
    assert "What's your #1 constraint" in data["ai_message"]

    # --- Step 3: Choose Constraint ---
    payload = {
        "current_step": schemas.OnboardingStepName.AWAITING_CONSTRAINT_CHOICE,
        "user_text": "Sales"
    }
    response = client.post("/api/onboarding/step", headers=headers, json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["next_step"] == schemas.OnboardingStepName.AWAITING_OBSTACLE_DEFINITION
    assert "biggest obstacle" in data["ai_message"]

    # --- Step 4: Define Obstacle ---
    payload = {
        "current_step": schemas.OnboardingStepName.AWAITING_OBSTACLE_DEFINITION,
        "user_text": "Getting qualified leads"
    }
    response = client.post("/api/onboarding/step", headers=headers, json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["next_step"] == schemas.OnboardingStepName.AWAITING_HLA_DEFINITION
    assert "Highest Leverage Action" in data["ai_message"]

    # --- Step 5: Define HLA (Final Step) ---
    final_hla_text = "Send 15 personalized outreach emails daily"
    payload = {
        "current_step": schemas.OnboardingStepName.AWAITING_HLA_DEFINITION,
        "user_text": final_hla_text
    }
    response = client.post("/api/onboarding/step", headers=headers, json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["next_step"] == schemas.OnboardingStepName.COMPLETE
    assert data["final_hla"] == final_hla_text
    assert "onboarding is now complete" in data["ai_message"]

    # 3. Verify the final state after the conversation is complete
    final_user = client.get("/users/me", headers=headers).json()
    assert final_user["hla"] == final_hla_text
    assert final_user["current_streak"] == 1