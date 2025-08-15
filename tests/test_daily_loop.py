#Full, self-contained showcase of the daily loop endpoints.

def test_creat_daily_intention_unauthenticated_fails(client):
    """Verify that an unatuhenticated user receives a 401 error when trying to create a Daily Intention"""
    payload = {
        "daily_intention_text": "Try to sneak in",
        "target_quantity": 1,
        "focus_block_count": 1,
        "is_refined": True
    }
    # No headers are sent with this request
    response = client.post("/intentions", json=payload)
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_create_daily_intention_flow(client, user_token):
    """Authenticated user creates a Daily Intention."""
    headers = {"Authorization": f"Bearer {user_token}"}
    payload = {
        "daily_intention_text": "Send 5 cold emails",
        "target_quantity": 5,
        "focus_block_count": 3,
        "is_refined": True,
    }

    resp = client.post("/intentions", headers=headers, json=payload)
    assert resp.status_code == 201, resp.text


def test_daily_results_cannot_get_duplicated(client, user_token):
    """Endpoint refuses double DailyResult for today."""
    headers = {"Authorization": f"Bearer {user_token}"}

    # 1. Create todays Daily Intention (prerequisite)
    client.post(
        "/intentions",
        headers=headers,
        json={
            "daily_intention_text": "Write API tests",
            "target_quantity": 1,
            "focus_block_count": 1,
            "is_refined": True,
        },
    )

    # 2. First evening reflection should succeed
    r1 = client.post("/daily-results", headers=headers)
    assert r1.status_code == 201

    # 3. Duplicate call must return 400
    r2 = client.post("/daily-results", headers=headers)
    assert r2.status_code == 400, r2.text
    assert "already exists" in r2.json()["detail"]


def test_completed_focus_block_awards_xp(client, user_token):
    """Completing a Focus Block awards +10 XP. (service mock value)"""
    headers = {"Authorization": f"Bearer {user_token}"}

    # 1. Daily Intention for today
    i_resp = client.post(
        "/intentions",
        headers=headers,
        json={
            "daily_intention_text": "Finish API tests",
            "target_quantity": 1,
            "focus_block_count": 1,
            "is_refined": True,
        },
    )
    assert i_resp.status_code == 201

    # 2. Create & complete one Focus Block
    f_resp = client.post(
        "/focus-blocks",
        headers=headers,
        json={"focus_block_intention": "Finish endpoint tests", "duration_minutes": 30},
    )
    assert f_resp.status_code == 201
    block_id = f_resp.json()["id"]

    # 3. Check user xp before, complete the Focus Block and compare
    start = client.get("/users/me/stats", headers=headers).json()
    start_xp = start["xp"]

    client.patch(
        f"/focus-blocks/{block_id}",
        headers=headers,
        json={"status": "completed"},
    )

    end = client.get("/users/me/stats", headers=headers).json()
    assert end["xp"] == start_xp + 10

def test_full_fail_forward_recovery_quest_loop(client, user_token):
    """
    Tests the entire "Fail Forward" loop:
    1. Create an intention and fail to complete it.
    2. Create a daily result, which should trigger a recovery quest.
    3. Respond to the recovery quest.
    4. Verify that the user's 'resilience' stat has increased.
    """
    headers = {"Authorization": f"Bearer {user_token}"}

    # 1. Create a Daily Intention
    intention_payload = {
        "daily_intention_text": "Send 5 Upwork proposals",
        "target_quantity": 5,
        "focus_block_count": 3,
        "is_refined": True
    }
    intention_resp = client.post("/intentions", headers=headers, json=intention_payload)
    assert intention_resp.status_code == 201

    # 2. Partially complete the intention (i.e. fail)
    progress_payload = {"completed_quantity": 3}
    progress_resp = client.patch("intentions/today/progress", headers=headers, json=progress_payload)
    assert progress_resp.status_code == 200
    assert progress_resp.json()["status"] == "in_progress"

    # 3. Trigger the evening reflection (Daily Result creation)
    # This is the step that should generate the Recovery Quest
    result_resp = client.post("/daily-results", headers=headers)
    assert result_resp.status_code == 201
    result_data = result_resp.json()
    assert result_data["succeeded_failed"] is False
    assert result_data["recovery_quest"] is not None # Verify a Recovery Quest was generated
    result_id = result_data["id"]

    # 4. Check the user's starting stats
    start_stats_resp = client.get("/users/me/stats", headers=headers)
    assert start_stats_resp.status_code == 200
    start_resilience = start_stats_resp.json()["resilience"]

    # 5. Respond to the Recovery Quest
    quest_response_payload = {
        "recovery_quest_response": "I got distracted by social media in the afternoon and lost my momentum."
    }
    quest_resp = client.post(
        f"/daily-results/{result_id}/recovery-quest",
        headers=headers,
        json=quest_response_payload
    )
    assert quest_resp.status_code == 200
    assert "ai_coaching_feedback" in quest_resp.json()

    # 6. Verify that the Resilience stat has increased
    end_stats_resp = client.get("/users/me/stats", headers=headers)
    assert end_stats_resp.status_code == 200
    end_resilience = end_stats_resp.json()["resilience"]
    assert end_resilience == start_resilience + 1