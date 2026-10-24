from fastapi.testclient import TestClient

from app.main import app


def test_application_returns_openapi_schema():
    client = TestClient(app)

    response = client.get("/openapi.json")

    assert response.status_code == 200

    schema = response.json()
    assert schema["info"]["title"] == "Car Dealership Inventory API"
    assert schema["info"]["version"] == "0.1.0"
