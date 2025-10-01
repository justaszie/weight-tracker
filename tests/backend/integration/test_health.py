from app.main import app
from fastapi.testclient import TestClient


def test_health_check():
    with TestClient(app) as client:
        response = client.get("/api/v1/healthz")

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
