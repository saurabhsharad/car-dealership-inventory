from datetime import UTC, datetime
from decimal import Decimal

VEHICLES_URL = "/api/vehicles"


def at(month: int) -> datetime:
    return datetime(2026, month, 1, 12, 0, tzinfo=UTC)


def test_an_empty_catalogue_is_an_empty_list(client, customer_headers):
    """T-VEH-09: no vehicles gives 200 []."""
    response = client.get(VEHICLES_URL, headers=customer_headers)

    assert response.status_code == 200
    assert response.json() == []


def test_list_shows_every_vehicle_newest_first(
    client, customer_headers, vehicle_factory
):
    """T-VEH-08 / FR-VEH-003: all vehicles, zero stock included, newest first."""
    oldest = vehicle_factory(model="Corolla", created_at=at(1))
    sold_out = vehicle_factory(model="Camry", quantity_in_stock=0, created_at=at(3))
    same_time_later_id = vehicle_factory(model="Prius", created_at=at(3))

    response = client.get(VEHICLES_URL, headers=customer_headers)

    assert response.status_code == 200
    assert [vehicle["id"] for vehicle in response.json()] == [
        same_time_later_id.id,
        sold_out.id,
        oldest.id,
    ]
    assert response.json()[1]["quantity_in_stock"] == 0


def test_each_listed_vehicle_has_the_public_shape(
    client, customer_headers, vehicle_factory
):
    """SRS §4.3: every field, with the price as a two-decimal string."""
    vehicle = vehicle_factory(price=Decimal("24999.10"))

    response = client.get(VEHICLES_URL, headers=customer_headers)

    assert response.status_code == 200
    [listed] = response.json()
    assert listed == {
        "id": vehicle.id,
        "make": "Toyota",
        "model": "Corolla",
        "category": "Sedan",
        "price": "24999.10",
        "quantity_in_stock": 3,
        "created_at": listed["created_at"],
        "updated_at": listed["updated_at"],
    }


def test_admins_can_list_too(client, admin_headers, vehicle_factory):
    """SRS §2.4: listing is open to any logged-in user."""
    vehicle_factory()

    response = client.get(VEHICLES_URL, headers=admin_headers)

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_listing_requires_a_token(client):
    """T-AUTH-10 / FR-AUTH-006: no token gives 401."""
    response = client.get(VEHICLES_URL)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "NOT_AUTHENTICATED"
