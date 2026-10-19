import uuid
from datetime import datetime, UTC
from sqlalchemy import Boolean, DateTime, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .connection import Base


class Enquiry(Base):
    __tablename__ = "enquiries"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4, unique=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False)
    message: Mapped[str] = mapped_column(String(500), nullable=False)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    logs: Mapped[list["EnquiryLog"]] = relationship(
        back_populates="enquiry",
        cascade="all, delete-orphan",
        order_by="EnquiryLog.created_at.asc()",
    )


class EnquiryLog(Base):
    __tablename__ = "enquiry_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4, unique=True, nullable=False
    )
    enquiry_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("enquiries.id", ondelete="CASCADE"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    sent_confirmation_email: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    is_human: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    enquiry: Mapped["Enquiry | None"] = relationship(back_populates="logs")
