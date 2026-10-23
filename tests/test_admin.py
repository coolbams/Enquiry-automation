from unittest.mock import patch


def test_admin_auth_required(client):
    """Test that admin endpoints reject unauthenticated or wrong credentials with 401."""
    # 1. No credentials provided
    response = client.get("/api/admin/stats")
    assert response.status_code == 401
    assert "WWW-Authenticate" in response.headers

    # 2. Invalid password
    bad_auth = client.get("/api/admin/stats", auth=("admin", "wrongpassword"))
    assert bad_auth.status_code == 401

    # 3. Valid credentials
    good_auth = client.get("/api/admin/stats", auth=("admin", "admin123"))
    assert good_auth.status_code == 200


def test_admin_stats(client):
    """Test that admin stats correctly aggregate enquiries, emails, and blocked bots."""
    with patch("enquiry_automation.main.send_email"):
        # Submit 1 legitimate human enquiry
        client.post(
            "/enquiries",
            json={
                "name": "Jane Doe",
                "email": "jane@example.com",
                "message": "Hello from Jane!",
            },
        )

        # Submit 1 spam bot (honeypot filled)
        client.post(
            "/enquiries",
            json={
                "name": "Spam Bot",
                "email": "bot@spam.com",
                "message": "Buy cheap watches",
                "website": "http://spamsite.com",
            },
        )

    # Fetch stats as admin
    response = client.get("/api/admin/stats", auth=("admin", "admin123"))
    assert response.status_code == 200
    data = response.json()

    assert data["total_enquiries"] == 1
    assert data["emails_sent"] == 1
    assert data["emails_failed"] == 0
    assert data["bots_blocked"] == 1


def test_admin_enquiries_list(client):
    """Test fetching enquiries list includes customer info and nested audit logs."""
    with patch("enquiry_automation.main.send_email"):
        client.post(
            "/enquiries",
            json={
                "name": "Alex Morgan",
                "email": "alex@example.com",
                "message": "I'd like to schedule a demo.",
            },
        )

    response = client.get("/api/admin/enquiries", auth=("admin", "admin123"))
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 1
    enquiry = data[0]
    assert enquiry["name"] == "Alex Morgan"
    assert enquiry["email"] == "alex@example.com"
    assert enquiry["message"] == "I'd like to schedule a demo."

    # Verify audit logs are nested inside the enquiry
    assert len(enquiry["logs"]) == 2
    log_statuses = [log["status"] for log in enquiry["logs"]]
    assert "received" in log_statuses
    assert "email_sent" in log_statuses


def test_admin_bots_list(client):
    """Test fetching bot logs returns only blocked bot attempts."""
    with patch("enquiry_automation.main.send_email"):
        # Human enquiry
        client.post(
            "/enquiries",
            json={"name": "Human", "email": "human@example.com", "message": "Hi"},
        )
        # Bot attempt
        client.post(
            "/enquiries",
            json={
                "name": "Bot",
                "email": "bot@bad.com",
                "message": "Spam",
                "website": "http://bad.com",
            },
        )

    response = client.get("/api/admin/bots", auth=("admin", "admin123"))
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 1
    bot_log = data[0]
    assert bot_log["status"] == "bot_blocked"
    assert bot_log["is_human"] is False
