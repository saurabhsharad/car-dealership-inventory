from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.api.errors import register_exception_handlers
from app.main import app

client = TestClient(app)


def test_unknown_route_returns_not_found_envelope():
    """T-ERR-01 / SRS §4.2: an unknown route answers with the error envelope."""
    response = client.get("/api/does-not-exist")

    assert response.status_code == 404
    assert response.json() == {
        "error": {"code": "NOT_FOUND", "message": "Resource not found."}
    }


def test_wrong_method_returns_method_not_allowed_envelope():
    """SRS §4.2: a known route called with the wrong method keeps its 405."""
    response = client.post("/openapi.json")

    assert response.status_code == 405
    assert response.json() == {
        "error": {"code": "METHOD_NOT_ALLOWED", "message": "Method not allowed."}
    }
    assert set(response.headers["Allow"].split(", ")) == {"GET", "HEAD"}


def test_unmapped_http_error_keeps_its_status_in_the_envelope():
    """SRS §4.2: any other framework HTTP error still uses the envelope."""
    test_app = FastAPI()
    register_exception_handlers(test_app)

    @test_app.get("/teapot")
    def teapot() -> None:
        raise HTTPException(status_code=418)

    response = TestClient(test_app).get("/teapot")

    assert response.status_code == 418
    assert response.json() == {
        "error": {"code": "HTTP_ERROR", "message": "Request failed."}
    }
