import logging
import uuid
from pathlib import Path

from fastapi import BackgroundTasks, Depends, FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from .apis.resendEmailApi import send_email
from .database import crud
from .database.connection import Base, SessionLocal, engine, get_db
from .schemas import EnquiryRequest, EnquiryResponse

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


def send_email_background(enquiry_id: uuid.UUID, email: str):
    """Worker task that runs after response is returned and records delivery log."""
    db = SessionLocal()
    try:
        send_email(email)
        crud.create_log(
            db,
            enquiry_id=enquiry_id,
            status="email_sent",
            sent_confirmation_email=True,
        )
    except Exception as exc:
        logger.exception("Failed to send confirmation email to %s", email)
        crud.create_log(
            db,
            enquiry_id=enquiry_id,
            status="email_failed",
            sent_confirmation_email=False,
            error_message=str(exc)[:500],
        )
    finally:
        db.close()


@app.get("/")
def read_root():
    """Serve the enquiry form."""
    return FileResponse(TEMPLATE_DIR / "Index.html")


@app.post("/enquiries", response_model=EnquiryResponse)
def make_enquiry(
    enquiry: EnquiryRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Endpoint to handle new enquiries."""
    if enquiry.website:
        logger.warning("Bot detected via honeypot from %s", enquiry.email)
        crud.create_log(db, status="bot_blocked", is_human=False)
        return {"message": "Enquiry received successfully"}

    new_enquiry = crud.create_enquiry(db, enquiry)

    if not crud.is_in_cooldown(db, email=enquiry.email, exclude_enquiry_id=new_enquiry.id):
        background_tasks.add_task(send_email_background, new_enquiry.id, enquiry.email)
    else:
        logger.info("Skipping confirmation email for %s (cooldown active)", enquiry.email)
        crud.create_log(
            db,
            enquiry_id=new_enquiry.id,
            status="cooldown_skipped",
        )

    return {"message": "Enquiry received successfully"}