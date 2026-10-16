from sqlalchemy import String, Uuid, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, UTC

from .connection import Base

import uuid

class Enquiry(Base):
    __tablename__ = "enquiries"

    id: Mapped[uuid.UUID] = mapped_column(Uuid,primary_key=True,default=uuid.uuid4, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=False,nullable=False)
    message: Mapped[str] = mapped_column(String(500),nullable=False)
    received_at: Mapped[datetime]= mapped_column(
        DateTime(timezone=True),
        default = lambda: datetime.now(UTC),
        nullable=False
    )



