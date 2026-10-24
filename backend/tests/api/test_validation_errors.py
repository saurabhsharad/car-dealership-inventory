from decimal import Decimal

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from app.api.errors import register_exception_handlers


class Payload(BaseModel):
    password: str = Field(min_length=8)
    price: Decimal = Field(gt=0)


def make_client() -> TestClient:
    """A throwaway app with one validated route and the real error handlers."""
    test_app = FastAPI()
    register_exception_handlers(test_app)

    @test_app.post("/items")
    def create_item(payload: Payload) -> dict[str, str]:
        return {}

    return TestClient(test_app)


def test_validation_error_returns_envelope_with_field_details():
    """T-ERR-01 / SRS §4.2: invalid fields return 422 with one detail each."""
    response = make_client().post("/items", json={"password": "short", "price": 0})

    assert response.status_code == 422
    assert response.json() == {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Request validation failed.",
            "details": [
                {
                    "location": "body",
                    "field": "password",
                    "message": "String should have at least 8 characters",
                },
                {
                    "location": "body",
                    "field": "price",
                    "message": "Input should be greater than 0",
                },
            ],
        }
    }


def test_validation_error_never_echoes_submitted_values():
    """NFR-SEC-008: a rejected password must not appear in the error body."""
    response = make_client().post(
        "/items", json={"password": "hunter2", "price": "1.00"}
    )

    assert response.status_code == 422
    assert "hunter2" not in response.text


@pytest.mark.parametrize(
    ("body", "message"),
    [
        ("{not valid json", "JSON decode error"),
        ("", "Field required"),
    ],
)
def test_unusable_body_is_reported_without_a_field(body, message):
    """T-ERR-01: malformed or missing JSON is a 422 about the body as a whole."""
    response = make_client().post(
        "/items", content=body, headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 422
    assert response.json()["error"]["details"] == [
        {"location": "body", "field": None, "message": message}
    ]
