from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, UTC

from .database.connection import Base, engine, get_db
from .database.models import Enquiry

from .apis.resendEmailApi import send_email

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"

Base.metadata.create_all(bind=engine)

app = FastAPI(
    debug=True,
    title="Enquiry Automation API",
    version="1.0.0",
    description="API for automating enquiry processes.",
)
app.mount("/static", StaticFiles(directory=TEMPLATE_DIR), name="static")


class EnquiryRequest(BaseModel):
    name: str
    email: str
    message: str
    website: str | None = None


class EnquiryResponse(BaseModel):
    message: str

def send_email_background(email: str):
    """Worker task that runs after response is returned."""
    try:
        send_email(email)
    except Exception:
        logger.exception("Failed to send confirmation email to %s", email)




@app.get("/")
def read_root():
    """Serve the enquiry form."""
    return FileResponse(TEMPLATE_DIR / "Index.html")


@app.post("/enquiries", response_model=EnquiryResponse)
def make_enquiry(enquiry: EnquiryRequest, 
                 background_tasks: BackgroundTasks, 
                 db: Session = Depends(get_db)):
    """Endpoint to handle new enquiries."""

    if enquiry.website:
        logger.warning("Bot detected via honeypot from %s", enquiry.email)
        return {"message": "Enquiry received successfully"}

    new_enquiry = Enquiry(
        name=enquiry.name,
        email=enquiry.email,
        message=enquiry.message
    )

    db.add(new_enquiry)
    db.commit()

    cooldown_limit = datetime.now(UTC) - timedelta(minutes=5)
    recent_enquiry = db.query(Enquiry).filter(
        Enquiry.email == enquiry.email,
        Enquiry.received_at >= cooldown_limit,
        Enquiry.id != new_enquiry.id
    ).first()

    if not recent_enquiry:
        background_tasks.add_task(send_email_background, enquiry.email)
    else:
        logger.info("Skipping confirmation email for %s (cooldown active)", enquiry.email)
   
    return {"message": "Enquiry received successfully"}