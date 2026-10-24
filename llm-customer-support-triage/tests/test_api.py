import os

os.environ["ANTHROPIC_API_KEY_1"] = "mock-key-1"
os.environ["ANTHROPIC_API_KEY_2"] = "mock-key-2"
os.environ["ANTHROPIC_API_KEY_3"] = "mock-key-3"

from fastapi.testclient import TestClient

from app import config

# model/timeout/mock-mode live in config.yml, not in env vars — force mock mode
# for tests regardless of what config.yml says, so `make test` never hits the
# real Anthropic API.
config.USE_MOCK_LLM = True

from app.session.store import clear_sessions

from app.main import app

client = TestClient(app)

def setup_function():
    clear_sessions()

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["use_mock_llm"] is True

def test_event_flow_updates_state():
    response_1 = client.post("/cases/T-001/events", json={"message": "I want to return an item."})
    assert response_1.status_code == 200
    assert response_1.json()["operation"] == "ask_for_order_id"
    response_2 = client.post("/cases/T-001/events", json={"message": "The order number is 8921."})
    assert response_2.status_code == 200
    assert response_2.json()["operation"] == "ask_for_reason"
    response_3 = client.post("/cases/T-001/events", json={"message": "It arrived broken."})
    assert response_3.status_code == 200
    body = response_3.json()
    assert body["operation"] == "start_refund_validation"
    assert body["state"]["order_id"] == "8921"
    assert body["state"]["ready_for_next_step"] is True

def test_empty_message_returns_422():
    response = client.post("/cases/T-002/events", json={"message": ""})
    assert response.status_code == 422
