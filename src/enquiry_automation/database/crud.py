import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from .models import Enquiry, EnquiryLog
from ..schemas import EnquiryRequest


def create_enquiry(db: Session, data: EnquiryRequest) -> Enquiry:
    """Create a new enquiry and automatically attach the initial 'received' audit log."""
    new_enquiry = Enquiry(
        name=data.name,
        email=data.email,
        message=data.message,
        logs=[
            EnquiryLog(
                status="received",
                sent_confirmation_email=False,
                is_human=True,
            )
        ],
    )
    db.add(new_enquiry)
    db.commit()
    db.refresh(new_enquiry)
    return new_enquiry


def create_log(
    db: Session,
    status: str,
    enquiry_id: uuid.UUID | None = None,
    sent_confirmation_email: bool = False,
    is_human: bool = True,
    error_message: str | None = None,
) -> EnquiryLog:
    """Create and persist a new audit log entry."""
    log_entry = EnquiryLog(
        enquiry_id=enquiry_id,
        status=status,
        sent_confirmation_email=sent_confirmation_email,
        is_human=is_human,
        error_message=error_message,
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry


def is_in_cooldown(
    db: Session,
    email: str,
    exclude_enquiry_id: uuid.UUID | None = None,
    minutes: int = 5,
) -> bool:
    """Check if the given email has submitted an enquiry within the cooldown window."""
    cooldown_limit = datetime.now(UTC) - timedelta(minutes=minutes)
    query = db.query(Enquiry).filter(
        Enquiry.email == email,
        Enquiry.received_at >= cooldown_limit,
    )
    if exclude_enquiry_id is not None:
        query = query.filter(Enquiry.id != exclude_enquiry_id)

    return query.first() is not None