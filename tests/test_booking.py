import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_manual_interview_booking():
    payload = {
        "candidate_name": "Bob Martin",
        "candidate_email": "bob.martin@example.com",
        "booking_date": "2026-09-01",
        "booking_time": "11:00 AM",
        "notes": "Backend Developer Technical Interview"
    }

    res = client.post("/api/v1/bookings", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["candidate_name"] == "Bob Martin"
    assert data["candidate_email"] == "bob.martin@example.com"
    assert "id" in data

    # Retrieve booking details
    booking_id = data["id"]
    get_res = client.get(f"/api/v1/bookings/{booking_id}")
    assert get_res.status_code == 200
    assert get_res.json()["booking_date"] == "2026-09-01"


def test_conversational_interview_booking():
    session_id = f"booking_session_{uuid.uuid4()}"

    # User expresses booking intent with parameters
    booking_msg = "I would like to schedule an interview. My name is Clara Oswald, my email is clara@example.com, date: 2026-08-20, time: 2:00 PM."
    
    chat_res = client.post(
        "/api/v1/chat",
        json={
            "session_id": session_id,
            "message": booking_msg,
            "top_k": 2
        }
    )

    assert chat_res.status_code == 200
    data = chat_res.json()
    assert "interview has been successfully scheduled" in data["answer"].lower() or "clara" in data["answer"].lower()
    assert data["booking_info"] is not None
    assert data["booking_info"]["candidate_email"] == "clara@example.com"
    assert data["booking_info"]["is_created"] is True

    # Check that booking is saved in DB
    list_res = client.get("/api/v1/bookings")
    assert list_res.status_code == 200
    bookings = list_res.json()
    clara_bookings = [b for b in bookings if b["candidate_email"] == "clara@example.com"]
    assert len(clara_bookings) == 1
    assert clara_bookings[0]["candidate_name"] == "Clara Oswald"
