
import os
import resend
from dotenv import load_dotenv

load_dotenv()

resend.api_key = os.getenv("RESEND_API_KEY")

FROM_EMAIL = "onboarding@resend.dev"

def send_email(to_email: str):
    """Send an email using the Resend API."""

    params: resend.Emails.SendParams = {
        "from": f"Acme <{FROM_EMAIL}>",
        "to": [f"{to_email}"],
        "subject": "We received your enquiry",
        "text": "Thanks for contacting us! \n We'll reach out to you shortly",
        "html": "<strong> Thank you :) </strong>",
    }

    return resend.Emails.send(params)
