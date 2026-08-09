import uuid
import re
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.booking import InterviewBooking
from app.core.config import settings

logger = logging.getLogger(__name__)


class BookingService:
    """Service to handle interview booking requests and persistence."""

    @staticmethod
    def create_booking(
        db: Session,
        candidate_name: str,
        candidate_email: str,
        booking_date: str,
        booking_time: str,
        notes: Optional[str] = None
    ) -> InterviewBooking:
        booking = InterviewBooking(
            id=str(uuid.uuid4()),
            candidate_name=candidate_name,
            candidate_email=candidate_email,
            booking_date=booking_date,
            booking_time=booking_time,
            notes=notes or ""
        )
        db.add(booking)
        db.commit()
        db.refresh(booking)
        return booking

    @staticmethod
    def extract_booking_details_from_text(user_message: str) -> Optional[Dict[str, Any]]:
        """
        Extract booking parameters (name, email, date, time) from user text.
        Returns a dict if all or some essential parameters are found.
        """
        # Regex extraction fallback for email, date, time
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', user_message)
        date_match = re.search(r'\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}/\d{1,2}/\d{4}\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}(?:st|nd|rd|th)?,? \d{4}\b', user_message, re.IGNORECASE)
        time_match = re.search(r'\b\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?\b|\b\d{1,2}\s*(?:AM|PM|am|pm)\b', user_message, re.IGNORECASE)
        
        # Name extraction attempt ("name is John", "I am John", "candidate: John")
        name_match = re.search(r'(?:name is|I am|my name is|candidate:?)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', user_message, re.IGNORECASE)

        email = email_match.group(0) if email_match else None
        date_str = date_match.group(0) if date_match else None
        time_str = time_match.group(0) if time_match else None
        name = name_match.group(1) if name_match else None

        if email or date_str or time_str or name:
            return {
                "candidate_name": name or "Applicant",
                "candidate_email": email or "",
                "booking_date": date_str or datetime.now().strftime("%Y-%m-%d"),
                "booking_time": time_str or "10:00 AM",
                "is_complete": bool(email and date_str and time_str)
            }
        return None


booking_service = BookingService()
