from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class BookingCreate(BaseModel):
    candidate_name: str = Field(..., json_schema_extra={"example": "Alice Smith"})
    candidate_email: EmailStr = Field(..., json_schema_extra={"example": "alice@example.com"})
    booking_date: str = Field(..., json_schema_extra={"example": "2026-08-15"})
    booking_time: str = Field(..., json_schema_extra={"example": "14:00"})
    notes: Optional[str] = Field(None, json_schema_extra={"example": "Frontend Engineer interview slot"})


class BookingResponse(BaseModel):
    id: str
    candidate_name: str
    candidate_email: str
    booking_date: str
    booking_time: str
    notes: Optional[str] = ""
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
