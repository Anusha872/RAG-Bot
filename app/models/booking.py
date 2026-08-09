from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime
from app.core.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class InterviewBooking(Base):
    __tablename__ = "interview_bookings"

    id = Column(String, primary_key=True, index=True)
    candidate_name = Column(String, nullable=False)
    candidate_email = Column(String, nullable=False, index=True)
    booking_date = Column(String, nullable=False)  # YYYY-MM-DD
    booking_time = Column(String, nullable=False)  # HH:MM
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=utc_now)
