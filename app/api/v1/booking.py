from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.booking import InterviewBooking
from app.schemas.booking import BookingCreate, BookingResponse
from app.services.booking_service import booking_service

router = APIRouter(prefix="/bookings", tags=["Interview Bookings API"])


@router.post("", response_model=BookingResponse, status_code=201)
def create_booking_manual(payload: BookingCreate, db: Session = Depends(get_db)):
    """Create an interview booking record directly."""
    booking = booking_service.create_booking(
        db=db,
        candidate_name=payload.candidate_name,
        candidate_email=payload.candidate_email,
        booking_date=payload.booking_date,
        booking_time=payload.booking_time,
        notes=payload.notes
    )
    return booking


@router.get("", response_model=List[BookingResponse])
def list_bookings(db: Session = Depends(get_db)):
    """List all interview bookings stored in the database."""
    return db.query(InterviewBooking).order_by(InterviewBooking.created_at.desc()).all()


@router.get("/{booking_id}", response_model=BookingResponse)
def get_booking(booking_id: str, db: Session = Depends(get_db)):
    """Retrieve details of a specific interview booking."""
    booking = db.query(InterviewBooking).filter(InterviewBooking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Interview booking not found.")
    return booking
