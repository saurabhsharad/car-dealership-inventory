from datetime import UTC, datetime

import pytest

from app.models import Vehicle

CIVIC = {
    "make": "Honda",
    "model": "Civic",
    "category": "Hatchback",
    "price": "25999.50",
}
LONG_AGO = datetime(2026, 1, 1, tzinfo=UTC)
VEHICLE_NOT_FOUND = {
    "error": {"code": "VEHICLE_NOT_FOUND", "message": "Vehicle not found."}
}


def url(vehicle_id) -> str:
    return f"/api/vehicles/{vehicle_id}"


@pytest.fixture
def corolla(vehicle_factory):
    """A vehicle with 4 in stock, created and last updated long ago."""
    return vehicle_factory(
        quantity_in_stock=4, created_at=LONG_AGO, updated_at=LONG_AGO
    )


def assert_unchanged(db_session, vehicle: Vehicle) -> None:
    db_session.refresh(vehicle)
    assert (vehicle.make, vehicle.model, vehicle.quantity_in_stock) == (
        "Toyota",
        "Corolla",
        4,
    )
    assert vehicle.updated_at == LONG_AGO


def test_admin_replaces_the_descriptive_fields(client, admin_headers, corolla):
    """T-VEH-17 / FR-VEH-006: new values, same id, created_at and stock."""
    response = client.put(url(corolla.id), json=CIVIC, headers=admin_headers)

    assert response.status_code == 200
    body = response.json()
    assert {key: body[key] for key in CIVIC} == CIVIC
    assert (body["id"], body["quantity_in_stock"]) == (corolla.id, 4)
    assert datetime.fromisoformat(body["created_at"]) == LONG_AGO
    assert datetime.fromisoformat(body["updated_at"]) > LONG_AGO

    listed = client.get("/api/vehicles", headers=admin_headers).json()
    assert [vehicle["model"] for vehicle in listed] == ["Civic"]


@pytest.mark.parametrize(
    ("body", "field"),
    [
        ({**CIVIC, "quantity_in_stock": 10}, "quantity_in_stock"),
        ({k: v for k, v in CIVIC.items() if k != "price"}, "price"),
    ],
)
def test_stock_or_a_missing_field_is_a_422(
    client, admin_headers, corolla, db_session, body, field
):
    """T-VEH-18 / A-10: stock changes only through purchase and restock."""
    response = client.put(url(corolla.id), json=body, headers=admin_headers)

    assert response.status_code == 422
    assert [d["field"] for d in response.json()["error"]["details"]] == [field]
    assert_unchanged(db_session, corolla)


def test_updating_a_vehicle_that_does_not_exist_is_a_404(client, admin_headers):
    """T-VEH-19 / FR-VEH-008: an unused id gives 404 VEHICLE_NOT_FOUND."""
    response = client.put(url(999_999), json=CIVIC, headers=admin_headers)

    assert response.status_code == 404
    assert response.json() == VEHICLE_NOT_FOUND


@pytest.mark.parametrize("vehicle_id", ["abc", "0", "-1"])
def test_an_id_that_is_not_a_positive_integer_is_a_422(
    client, admin_headers, vehicle_id
):
    """T-VEH-22 / FR-VEH-008: the id must be a positive integer."""
    response = client.put(url(vehicle_id), json=CIVIC, headers=admin_headers)

    assert response.status_code == 422
    details = response.json()["error"]["details"]
    assert [(d["location"], d["field"]) for d in details] == [("path", "vehicle_id")]


def test_a_customer_cannot_update_a_vehicle(
    client, customer_headers, corolla, db_session
):
    """T-AUTH-14 / A-01: update is admin-only; nothing changes."""
    response = client.put(url(corolla.id), json=CIVIC, headers=customer_headers)

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"
    assert_unchanged(db_session, corolla)


def test_updating_requires_a_token(client, corolla, db_session):
    """FR-AUTH-006: no token gives 401 and nothing changes."""
    response = client.put(url(corolla.id), json=CIVIC)

    assert response.status_code == 401
    assert_unchanged(db_session, corolla)
