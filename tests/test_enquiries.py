from unittest.mock import patch
from enquiry_automation.database.models import Enquiry


def test_read_root(client):
    """Test that the root URL serves the HTML landing page."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "We’d love to hear from you" in response.text


def test_successful_enquiry(client, db_session):
    """Test standard submission: saves to DB and sends a confirmation email."""
    with patch("enquiry_automation.main.send_email") as mock_send_email:
        payload = {
            "name": "Alice Morgan",
            "email": "alice@example.com",
            "message": "Interested in learning more about your services.",
        }

        response = client.post("/enquiries", json=payload)

        assert response.status_code == 200
        assert response.json() == {"message": "Enquiry received successfully"}

        # Verify saved in the database
        saved = db_session.query(Enquiry).filter_by(email="alice@example.com").first()
        assert saved is not None
        assert saved.name == "Alice Morgan"
        assert saved.message == "Interested in learning more about your services."

        # Verify confirmation email was dispatched
        mock_send_email.assert_called_once_with("alice@example.com")


def test_honeypot_drops_bot(client, db_session):
    """Test honeypot: if 'website' is filled, fake success but do not save or email."""
    with patch("enquiry_automation.main.send_email") as mock_send_email:
        bot_payload = {
            "name": "Spam Bot",
            "email": "spammer@botnet.com",
            "message": "Cheap pharmaceutical deals!",
            "website": "https://spam-link.example.com",
        }

        response = client.post("/enquiries", json=bot_payload)

        assert response.status_code == 200
        assert response.json() == {"message": "Enquiry received successfully"}

        # Verify NOTHING was saved to the database
        count = db_session.query(Enquiry).count()
        assert count == 0

        # Verify NO email was sent
        mock_send_email.assert_not_called()


def test_cooldown_skips_second_email(client, db_session):
    """Test cooldown: repeated submissions within 5 mins save to DB, but only send 1 email."""
    with patch("enquiry_automation.main.send_email") as mock_send_email:
        payload1 = {
            "name": "Bob Smith",
            "email": "bob@example.com",
            "message": "First message from Bob.",
        }
        payload2 = {
            "name": "Bob Smith",
            "email": "bob@example.com",
            "message": "Second message shortly after from Bob.",
        }

        # 1st Submission: should save to DB AND send email
        res1 = client.post("/enquiries", json=payload1)
        assert res1.status_code == 200
        assert mock_send_email.call_count == 1

        # 2nd Submission immediately after: should save to DB BUT skip email
        res2 = client.post("/enquiries", json=payload2)
        assert res2.status_code == 200
        assert mock_send_email.call_count == 1  # Still 1! Not called again.

        # Verify BOTH enquiries were saved to the database
        bobs_messages = db_session.query(Enquiry).filter_by(email="bob@example.com").all()
        assert len(bobs_messages) == 2


def test_validation_error_on_missing_fields(client):
    """Test validation: missing required fields returns 422 Unprocessable Entity."""
    response = client.post("/enquiries", json={"name": "Incomplete"})
    assert response.status_code == 422
