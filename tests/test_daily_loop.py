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
