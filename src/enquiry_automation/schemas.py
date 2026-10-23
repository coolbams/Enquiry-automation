from pydantic import BaseModel
from datetime import datetime

import uuid


class EnquiryRequest(BaseModel):
    name: str
    email: str
    message: str
    website: str | None = None


class EnquiryResponse(BaseModel):
    message: str

class EnquiryLogResponse(BaseModel):
    status: str
    sent_confirmation_email: bool
    is_human: bool
    error_message: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}

class EnquiryDetailsResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    message: str
    received_at: datetime
    logs: list[EnquiryLogResponse] = []

    model_config = {"from_attributes": True}

class AdminStatsResponse(BaseModel):
    total_enquiries: int
    emails_sent: int
    emails_failed: int
    bots_blocked: int


class AdminLoginRequest(BaseModel):
    username: str
    password: str

