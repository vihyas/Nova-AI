import pytest
from starlette.testclient import TestClient
from backend.app.main import app
from backend.app.database import init_db

@pytest.fixture
def client():
    init_db()
    return TestClient(app)

def test_api_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_api_get_tasks(client):
    response = client.get("/api/tasks")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0

def test_api_parse_task(client):
    response = client.post("/api/tasks/parse", json={"text": "Study Java tomorrow at 6 PM for 2 hours"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["parsed_task"]["duration_minutes"] == 120

def test_api_reminders(client):
    response = client.get("/api/reminders")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_api_memory_list_and_export(client):
    response = client.get("/api/memory")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

    export_res = client.get("/api/memory/export")
    assert export_res.status_code == 200
    assert "markdown_format" in export_res.json()

def test_api_productivity_analytics(client):
    response = client.get("/api/analytics/productivity")
    assert response.status_code == 200
    data = response.json()
    assert "completion_rate" in data
    assert "velocity_score" in data

def test_api_settings_get_and_update(client):
    response = client.get("/api/settings")
    assert response.status_code == 200
    data = response.json()
    assert "default_provider" in data

    update_res = client.post("/api/settings", json={"temperature": 0.8, "system_language": "en"})
    assert update_res.status_code == 200
    assert update_res.json()["temperature"] == 0.8

def test_api_chat(client):
    response = client.post("/api/chat", json={
        "message": "Explain linked lists in Java",
        "session_id": "test_session",
        "agent_name": "auto"
    })
    assert response.status_code == 200
    data = response.json()
    assert "Linked List" in data["reply"] or "Java" in data["reply"]

