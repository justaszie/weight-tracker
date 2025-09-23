from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_health_check():
    response = client.get("/api/healthz")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
