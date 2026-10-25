import pytest

from app.models import Vehicle

VEHICLE_NOT_FOUND = {
    "error": {"code": "VEHICLE_NOT_FOUND", "message": "Vehicle not found."}
}


def url(vehicle_id) -> str:
    return f"/api/vehicles/{vehicle_id}"


def listed_ids(client, headers) -> list[int]:
    return [v["id"] for v in client.get("/api/vehicles", headers=headers).json()]


def test_admin_deletes_a_vehicle(client, admin_headers, vehicle_factory, db_session):
    """T-VEH-20 / FR-VEH-007: 204 with no body; gone from list and search."""
    keep = vehicle_factory(model="Camry")
    gone = vehicle_factory(model="Corolla")

    response = client.delete(url(gone.id), headers=admin_headers)

    assert response.status_code == 204
    assert response.content == b""
    assert listed_ids(client, admin_headers) == [keep.id]
    found = client.get(
        "/api/vehicles/search", params={"model": "Corolla"}, headers=admin_headers
    )
    assert found.json() == []
    assert db_session.get(Vehicle, gone.id) is None


def test_deleting_twice_is_a_404_the_second_time(
    client, admin_headers, vehicle_factory
):
    """T-VEH-21: a deleted id no longer exists."""
    vehicle = vehicle_factory()
    assert client.delete(url(vehicle.id), headers=admin_headers).status_code == 204

    response = client.delete(url(vehicle.id), headers=admin_headers)

    assert response.status_code == 404
    assert response.json() == VEHICLE_NOT_FOUND


def test_deleting_an_unused_id_is_a_404(client, admin_headers):
    """T-VEH-21 / FR-VEH-008: an id that never existed gives 404."""
    response = client.delete(url(999_999), headers=admin_headers)

    assert response.status_code == 404
    assert response.json() == VEHICLE_NOT_FOUND


@pytest.mark.parametrize("vehicle_id", ["abc", "0", "-1"])
def test_an_id_that_is_not_a_positive_integer_is_a_422(
    client, admin_headers, vehicle_id
):
    """T-VEH-22: the id must be a positive integer."""
    response = client.delete(url(vehicle_id), headers=admin_headers)

    assert response.status_code == 422
    details = response.json()["error"]["details"]
    assert [(d["location"], d["field"]) for d in details] == [("path", "vehicle_id")]


def test_a_customer_cannot_delete_a_vehicle(
    client, customer_headers, vehicle_factory, db_session
):
    """T-AUTH-14 / B-1.4: delete is admin-only; the vehicle stays."""
    vehicle = vehicle_factory()

    response = client.delete(url(vehicle.id), headers=customer_headers)

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"
    assert db_session.get(Vehicle, vehicle.id) is not None


@pytest.mark.parametrize("vehicle_id", ["999999", "abc"])
def test_a_customer_is_forbidden_before_the_id_is_checked(
    client, customer_headers, vehicle_id
):
    """T-AUTH-15 / FR-AUTH-007: 403, not 404 or 422, so ids are not revealed."""
    response = client.delete(url(vehicle_id), headers=customer_headers)

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_deleting_requires_a_token(client, vehicle_factory, db_session):
    """FR-AUTH-006: no token gives 401; the vehicle stays."""
    vehicle = vehicle_factory()

    response = client.delete(url(vehicle.id))

    assert response.status_code == 401
    assert db_session.get(Vehicle, vehicle.id) is not None
