def test_create_daily_intention_flow(client, user_token):
    """Happy path: authenticated user creates an intention."""
    response = client.post(
        "/intentions",
        json={"daily_intention_text": "Send 5 cold emails", "target_quantity": 5, "focus_block_count": 3},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 201


def test_daily_results_cannot_get_duplicated(client, user_token, today_intention_id):
    """Evening reflection can only be posted once per intention."""
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # First POST
    client.post("/daily-results", headers=headers)

    # Duplicate attempt
    r2 = client.post("/daily-results", headers=headers)
    assert r2.status_code == 400
    assert "already exists" in r2.json()["detail"]

def test_completed_focus_block_awards_xp(client, user_token, today_intention_id):
    """Completing a Focus Block awards XP to the user"""
    headers = {"Authorization": f"Bearer: {user_token}"}

    # 1. Create a Focus Block via Daily Intention
    b = client.post("/focus-blocks", headers=headers,
                     json={"focus_block_intention": "finish email 1-3",
                           "duration_minutes": 25})
    block = b.json()
    block_id = block["id"]

    # 1.5 Grab initial stats (for step 3)
    start = client.get("/users/me/stats", headers=headers).json()
    initial_xp = start["xp"]

    # 2. Mark it as completed
    update = client.patch(f"/focus-blocks/{block_id}", headers=headers,
                          json={"status": "completed"})
    assert update.status_code == 200

    # 3. Stats should have +10XP (value from service mock), compare delta
    end = client.get("/users/me/stats", headers=headers).json()
    assert end["xp"] == initial_xp + 10
