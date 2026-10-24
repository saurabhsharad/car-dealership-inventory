from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_unknown_route_returns_not_found_envelope():
    """T-ERR-01 / SRS §4.2: an unknown route answers with the error envelope."""
    response = client.get("/api/does-not-exist")

    assert response.status_code == 404
    assert response.json() == {
        "error": {"code": "NOT_FOUND", "message": "Resource not found."}
    }
