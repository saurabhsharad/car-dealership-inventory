import logging

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.errors import register_exception_handlers

SECRET_DETAIL = "connection to db-internal:5432 failed for password=hunter2"


@pytest.fixture
def failing_client() -> TestClient:
    """A throwaway app whose one route fails with an unexpected exception."""
    test_app = FastAPI()
    register_exception_handlers(test_app)

    @test_app.get("/boom")
    def boom() -> None:
        raise RuntimeError(SECRET_DETAIL)

    return TestClient(test_app, raise_server_exceptions=False)


def test_an_unexpected_error_is_a_generic_500_envelope(failing_client):
    """T-ERR-02 / NFR-ERR-001: 500 INTERNAL_ERROR with a generic message."""
    response = failing_client.get("/boom")

    assert response.status_code == 500
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == {
        "error": {
            "code": "INTERNAL_ERROR",
            "message": "An unexpected error occurred.",
        }
    }


def test_an_unexpected_error_reveals_nothing_to_the_client(failing_client):
    """SRS §4.2: no stack trace, internal detail or secret in the response."""
    response = failing_client.get("/boom")

    assert "hunter2" not in response.text
    assert "RuntimeError" not in response.text
    assert "Traceback" not in response.text


def test_an_unexpected_error_is_logged_with_its_traceback(failing_client, caplog):
    """NFR-ERR-001: the details go to the server log instead."""
    with caplog.at_level(logging.ERROR, logger="app.errors"):
        failing_client.get("/boom")

    records = [r for r in caplog.records if r.name == "app.errors"]
    assert len(records) == 1
    record = records[0]
    assert "GET /boom" in record.getMessage()
    assert record.exc_info is not None
    assert isinstance(record.exc_info[1], RuntimeError)
