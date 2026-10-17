from fastapi.testclient import TestClient

from ai_proxy.main import app

client = TestClient(app)


def test_health_and_mock_inference():
    assert client.get("/healthz").json() == {"status": "ok"}
    response = client.post("/v1/inference", json={"prompt": "hello"})
    assert response.status_code == 200
    assert response.json()["model"] == "mock"


def test_empty_prompt_is_rejected():
    assert client.post("/v1/inference", json={"prompt": ""}).status_code == 422
