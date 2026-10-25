from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select

from app.models import Vehicle

VEHICLES_URL = "/api/vehicles"
COROLLA = {
    "make": "Toyota",
    "model": "Corolla",
    "category": "Sedan",
    "price": "24999.00",
    "quantity_in_stock": 3,
}


def vehicle_count(db_session) -> int:
    return db_session.scalar(select(func.count()).select_from(Vehicle))


def test_admin_creates_a_vehicle(client, admin_headers, db_session):
    """T-VEH-01 / FR-VEH-001: 201 with the stored vehicle, id and timestamps."""
    response = client.post(VEHICLES_URL, json=COROLLA, headers=admin_headers)

    assert response.status_code == 201
    body = response.json()
    assert set(body) == {*COROLLA, "id", "created_at", "updated_at"}
    assert {key: body[key] for key in COROLLA} == COROLLA
    assert isinstance(body["id"], int)
    assert datetime.fromisoformat(body["created_at"]).utcoffset() == timedelta(0)

    stored = db_session.get(Vehicle, body["id"])
    assert (stored.make, stored.model, stored.category, stored.quantity_in_stock) == (
        "Toyota",
        "Corolla",
        "Sedan",
        3,
    )


def test_stock_defaults_to_zero_when_omitted(client, admin_headers):
    """T-VEH-02: quantity_in_stock is optional."""
    body = {key: value for key, value in COROLLA.items() if key != "quantity_in_stock"}

    response = client.post(VEHICLES_URL, json=body, headers=admin_headers)

    assert response.status_code == 201
    assert response.json()["quantity_in_stock"] == 0


def test_price_round_trips_exactly(client, admin_headers, db_session):
    """T-VEH-05: "24999.10" comes back unchanged and is stored as a Decimal."""
    response = client.post(
        VEHICLES_URL, json={**COROLLA, "price": "24999.10"}, headers=admin_headers
    )

    assert response.json()["price"] == "24999.10"
    assert db_session.get(Vehicle, response.json()["id"]).price == Decimal("24999.10")


def test_invalid_input_is_a_422_on_each_field_and_stores_nothing(
    client, admin_headers, db_session
):
    """FR-VEH-002: one details entry per invalid field; nothing is written."""
    response = client.post(
        VEHICLES_URL,
        json={**COROLLA, "price": 0, "quantity_in_stock": "3", "make": " "},
        headers=admin_headers,
    )

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert {detail["field"] for detail in error["details"]} == {
        "make",
        "price",
        "quantity_in_stock",
    }
    assert vehicle_count(db_session) == 0


def test_a_customer_cannot_create_a_vehicle(client, customer_headers, db_session):
    """T-AUTH-14 / A-01: create is admin-only; nothing is written."""
    response = client.post(VEHICLES_URL, json=COROLLA, headers=customer_headers)

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"
    assert vehicle_count(db_session) == 0


def test_creating_a_vehicle_requires_a_token(client, db_session):
    """T-AUTH-10: no token gives 401."""
    response = client.post(VEHICLES_URL, json=COROLLA)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "NOT_AUTHENTICATED"
    assert vehicle_count(db_session) == 0
