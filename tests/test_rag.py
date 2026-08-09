import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_conversational_rag_flow():
    session_id = f"test_session_{uuid.uuid4()}"

    # Turn 1: Initial query
    res1 = client.post(
        "/api/v1/chat",
        json={
            "session_id": session_id,
            "message": "What is Python FastAPI?",
            "top_k": 3
        }
    )
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["session_id"] == session_id
    assert "answer" in data1
    assert isinstance(data1["sources"], list)

    # Turn 2: Follow-up query in same session (Multi-turn)
    res2 = client.post(
        "/api/v1/chat",
        json={
            "session_id": session_id,
            "message": "Can you explain how Redis chat memory works with it?",
            "top_k": 3
        }
    )
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["session_id"] == session_id

    # Verify history stored in Redis
    hist_res = client.get(f"/api/v1/chat/{session_id}/history")
    assert hist_res.status_code == 200
    history = hist_res.json()["messages"]
    # 2 turns * 2 messages (user + assistant) = 4 messages
    assert len(history) == 4
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "What is Python FastAPI?"

    # Reset chat session
    del_res = client.delete(f"/api/v1/chat/{session_id}")
    assert del_res.status_code == 200

    # Verify history cleared
    empty_hist = client.get(f"/api/v1/chat/{session_id}/history").json()["messages"]
    assert len(empty_hist) == 0
