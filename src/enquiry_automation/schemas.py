from pydantic import BaseModel


class EnquiryRequest(BaseModel):
    name: str
    email: str
    message: str
    website: str | None = None


class EnquiryResponse(BaseModel):
    message: str
