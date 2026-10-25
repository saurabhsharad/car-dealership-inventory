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
