"""Smoke tests for health endpoint."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint_returns_ok() -> None:
    response = client.get("/api/v1/health/ping")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "environment" in payload
    assert "version" in payload
