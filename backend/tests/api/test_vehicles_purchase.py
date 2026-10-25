from datetime import UTC, datetime

import pytest

from app.models import Vehicle

LONG_AGO = datetime(2026, 1, 1, tzinfo=UTC)


def purchase_url(vehicle_id) -> str:
    return f"/api/vehicles/{vehicle_id}/purchase"


def stock_of(db_session, vehicle: Vehicle) -> int:
    db_session.refresh(vehicle)
    return vehicle.quantity_in_stock


@pytest.mark.parametrize(("stock", "left"), [(3, 2), (1, 0)])
def test_a_purchase_takes_exactly_one_unit(
    client, customer_headers, vehicle_factory, db_session, stock, left
):
    """T-INV-01 / T-INV-02 / FR-INV-001: stock drops by one, last unit included."""
    vehicle = vehicle_factory(quantity_in_stock=stock, updated_at=LONG_AGO)

    response = client.post(purchase_url(vehicle.id), headers=customer_headers)

    assert response.status_code == 200
    body = response.json()
    assert (body["id"], body["quantity_in_stock"]) == (vehicle.id, left)
    assert datetime.fromisoformat(body["updated_at"]) > LONG_AGO
    assert stock_of(db_session, vehicle) == left


def test_admins_can_purchase_too(client, admin_headers, vehicle_factory, db_session):
    """A-02: any authenticated user may purchase."""
    vehicle = vehicle_factory(quantity_in_stock=2)

    response = client.post(purchase_url(vehicle.id), headers=admin_headers)

    assert response.status_code == 200
    assert stock_of(db_session, vehicle) == 1


def test_buying_at_zero_stock_is_a_409_and_stock_stays_zero(
    client, customer_headers, vehicle_factory, db_session
):
    """T-INV-03 / FR-INV-002: every attempt at stock 0 gets 409 OUT_OF_STOCK."""
    vehicle = vehicle_factory(quantity_in_stock=0)

    for _ in range(2):
        response = client.post(purchase_url(vehicle.id), headers=customer_headers)

        assert response.status_code == 409
        assert response.json() == {
            "error": {
                "code": "OUT_OF_STOCK",
                "message": "This vehicle is out of stock.",
            }
        }
    assert stock_of(db_session, vehicle) == 0


def test_buying_a_vehicle_that_does_not_exist_is_a_404(client, customer_headers):
    """T-INV-04 / FR-VEH-008: an unused id gives 404 VEHICLE_NOT_FOUND."""
    response = client.post(purchase_url(999_999), headers=customer_headers)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "VEHICLE_NOT_FOUND"


@pytest.mark.parametrize("vehicle_id", ["abc", "0", "-1"])
def test_an_id_that_is_not_a_positive_integer_is_a_422(
    client, customer_headers, vehicle_id
):
    """FR-VEH-008: the id must be a positive integer."""
    response = client.post(purchase_url(vehicle_id), headers=customer_headers)

    assert response.status_code == 422


def test_buying_requires_a_token(client, vehicle_factory, db_session):
    """T-INV-05: no token gives 401 and the stock is unchanged."""
    vehicle = vehicle_factory(quantity_in_stock=3)

    response = client.post(purchase_url(vehicle.id))

    assert response.status_code == 401
    assert stock_of(db_session, vehicle) == 3
