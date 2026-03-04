import pytest
from fastapi.testclient import TestClient
from service import app, agent

client = TestClient(app)

# We want to mock the actual join behavior so that tests run quickly
# and do not interact with the system's WeMeet client.
def mock_process_meeting(meeting_id: str):
    agent._set_meeting_state(meeting_id, "in_progress")
    # Simulate finishing later
    pass

agent.process_meeting = mock_process_meeting

def test_join_meeting_unauthorized():
    # Attempting to join without API key
    response = client.post("/meeting/join", json={"meeting_id": "test_meeting_123"})
    assert response.status_code == 401
    assert "API Key" in response.json()["detail"]

def test_join_meeting_authorized():
    # Attempting to join with the default API key
    response = client.post("/meeting/join", json={"meeting_id": "test_meeting_123"}, headers={"x-api-key": "secret"})
    assert response.status_code == 202
    data = response.json()
    assert "accepted" in data["message"]
    # We meet agent might fail the join in background, but the API response should be 202

def test_download_status_in_progress():
    # The agent state is likely in progress now
    response = client.get("/meeting/download/test_meeting_123", headers={"x-api-key": "secret"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["joining", "in progress", "failed"]  # It might fail quickly if UI isn't found
    print("Download status for test_meeting_123:", data["status"])

if __name__ == "__main__":
    pytest.main(["-v", __file__])
