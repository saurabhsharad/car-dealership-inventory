from datetime import UTC, datetime

import pytest

from app.models import Vehicle

LONG_AGO = datetime(2026, 1, 1, tzinfo=UTC)


def restock_url(vehicle_id) -> str:
    return f"/api/vehicles/{vehicle_id}/restock"


def stock_of(db_session, vehicle: Vehicle) -> int:
    db_session.refresh(vehicle)
    return vehicle.quantity_in_stock


def test_admin_restocks_a_sold_out_vehicle(
    client, admin_headers, customer_headers, vehicle_factory, db_session
):
    """T-INV-08 / FR-INV-004: stock 0 + 5 = 5, and it can be bought again."""
    vehicle = vehicle_factory(quantity_in_stock=0, updated_at=LONG_AGO)

    response = client.post(
        restock_url(vehicle.id), json={"quantity": 5}, headers=admin_headers
    )

    assert response.status_code == 200
    body = response.json()
    assert (body["id"], body["quantity_in_stock"]) == (vehicle.id, 5)
    assert datetime.fromisoformat(body["updated_at"]) > LONG_AGO
    assert stock_of(db_session, vehicle) == 5
    purchase = client.post(
        f"/api/vehicles/{vehicle.id}/purchase", headers=customer_headers
    )
    assert purchase.status_code == 200


def test_stock_may_grow_past_10000_through_repeated_restocks(
    client, admin_headers, vehicle_factory, db_session
):
    """FR-INV-005: 10,000 limits one request, not the total stock."""
    vehicle = vehicle_factory(quantity_in_stock=9_000)

    response = client.post(
        restock_url(vehicle.id), json={"quantity": 10_000}, headers=admin_headers
    )

    assert response.status_code == 200
    assert stock_of(db_session, vehicle) == 19_000


@pytest.mark.parametrize(
    "body",
    [
        {"quantity": 0},
        {"quantity": -3},
        {"quantity": 1.5},
        {"quantity": "5"},
        {"quantity": True},
        {"quantity": 10_001},
        {},
        {"quantity": 5, "note": "extra"},
    ],
)
def test_an_invalid_quantity_is_a_422_and_stock_is_unchanged(
    client, admin_headers, vehicle_factory, db_session, body
):
    """T-INV-09 / FR-INV-005: a strict integer from 1 to 10,000, nothing else."""
    vehicle = vehicle_factory(quantity_in_stock=2)

    response = client.post(restock_url(vehicle.id), json=body, headers=admin_headers)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert stock_of(db_session, vehicle) == 2


def test_restocking_a_vehicle_that_does_not_exist_is_a_404(client, admin_headers):
    """T-INV-10: an unused id gives 404 VEHICLE_NOT_FOUND."""
    response = client.post(
        restock_url(999_999), json={"quantity": 5}, headers=admin_headers
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "VEHICLE_NOT_FOUND"


def test_a_customer_cannot_restock(
    client, customer_headers, vehicle_factory, db_session
):
    """T-INV-10 / T-AUTH-14: restock is admin-only; stock is unchanged."""
    vehicle = vehicle_factory(quantity_in_stock=2)

    response = client.post(
        restock_url(vehicle.id), json={"quantity": 5}, headers=customer_headers
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"
    assert stock_of(db_session, vehicle) == 2


def test_restocking_requires_a_token(client, vehicle_factory, db_session):
    """FR-AUTH-006: no token gives 401; stock is unchanged."""
    vehicle = vehicle_factory(quantity_in_stock=2)

    response = client.post(restock_url(vehicle.id), json={"quantity": 5})

    assert response.status_code == 401
    assert stock_of(db_session, vehicle) == 2
