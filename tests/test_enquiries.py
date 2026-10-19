from unittest.mock import patch
from enquiry_automation.database.models import Enquiry, EnquiryLog


def test_read_root(client):
    """Test that the root URL serves the HTML landing page."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "We’d love to hear from you" in response.text


def test_successful_enquiry(client, db_session):
    """Test standard submission: saves to DB, logs receipt and email_sent, and sends email."""
    with patch("enquiry_automation.main.send_email") as mock_send_email:
        payload = {
            "name": "Alice Morgan",
            "email": "alice@example.com",
            "message": "Interested in learning more about your services.",
        }

        response = client.post("/enquiries", json=payload)

        assert response.status_code == 200
        assert response.json() == {"message": "Enquiry received successfully"}

        # Verify saved in the enquiries table
        saved = db_session.query(Enquiry).filter_by(email="alice@example.com").first()
        assert saved is not None
        assert saved.name == "Alice Morgan"
        assert saved.message == "Interested in learning more about your services."

        # Verify confirmation email was dispatched
        mock_send_email.assert_called_once_with("alice@example.com")

        # Verify audit logs in enquiry_logs
        logs = db_session.query(EnquiryLog).filter_by(enquiry_id=saved.id).all()
        assert len(logs) == 2
        statuses = [l.status for l in logs]
        assert "received" in statuses
        assert "email_sent" in statuses

        sent_log = [l for l in logs if l.status == "email_sent"][0]
        assert sent_log.sent_confirmation_email is True
        assert sent_log.is_human is True


def test_honeypot_drops_bot(client, db_session):
    """Test honeypot: if 'website' is filled, do not save enquiry, but log bot_blocked."""
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

        # Verify NOTHING was saved to the enquiries table
        assert db_session.query(Enquiry).count() == 0

        # Verify NO email was sent
        mock_send_email.assert_not_called()

        # Verify bot attempt was logged in enquiry_logs
        bot_log = db_session.query(EnquiryLog).filter_by(status="bot_blocked").first()
        assert bot_log is not None
        assert bot_log.is_human is False
        assert bot_log.enquiry_id is None


def test_cooldown_skips_second_email(client, db_session):
    """Test cooldown: repeated submissions within 5 mins save to DB and log cooldown_skipped."""
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

        # Verify cooldown_skipped was logged for the second message
        cooldown_log = (
            db_session.query(EnquiryLog)
            .filter_by(enquiry_id=bobs_messages[1].id, status="cooldown_skipped")
            .first()
        )
        assert cooldown_log is not None
        assert cooldown_log.sent_confirmation_email is False


def test_failed_email_logs_error(client, db_session):
    """Test that if Resend fails, the failure and error message are recorded in enquiry_logs."""
    with patch("enquiry_automation.main.send_email", side_effect=Exception("Resend API rate limit exceeded")):
        payload = {
            "name": "Charlie",
            "email": "charlie@example.com",
            "message": "Hello there!",
        }

        response = client.post("/enquiries", json=payload)
        assert response.status_code == 200

        saved = db_session.query(Enquiry).filter_by(email="charlie@example.com").first()
        assert saved is not None

        failed_log = (
            db_session.query(EnquiryLog)
            .filter_by(enquiry_id=saved.id, status="email_failed")
            .first()
        )
        assert failed_log is not None
        assert failed_log.sent_confirmation_email is False
        assert "Resend API rate limit exceeded" in failed_log.error_message


def test_validation_error_on_missing_fields(client):
    """Test validation: missing required fields returns 422 Unprocessable Entity."""
    response = client.post("/enquiries", json={"name": "Incomplete"})
    assert response.status_code == 422
