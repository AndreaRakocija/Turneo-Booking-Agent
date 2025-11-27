import os

from fastapi.testclient import TestClient

os.environ["OPENAI_API_KEY"] = ""

from app.main import app

client = TestClient(app)


def test_query_endpoint_basic_flow():
    payload = {"query": "Show me bookings in November 2024 in EUR"}

    response = client.post("/query", json=payload)

    assert response.status_code in (200, 400)
    data = response.json()

    assert "message" in data
    assert "total_value" in data
    assert "currency" in data
