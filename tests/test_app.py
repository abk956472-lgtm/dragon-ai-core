from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["system"] == "DRAGON AI CORE"
    assert data["status"] == "online"


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_chat_greeting():
    response = client.post("/chat", json={"message": "مرحبا"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "response" in data


def test_security_status():
    response = client.get("/security/status")
    assert response.status_code == 200
    data = response.json()
    assert "policy_version" in data
    assert "kill_switch" in data


def test_kill_switch_test_endpoint():
    response = client.post("/security/test-kill-switch")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["kill_switch_test"] is True
