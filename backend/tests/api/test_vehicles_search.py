from decimal import Decimal

import pytest

SEARCH_URL = "/api/vehicles/search"


@pytest.fixture
def showroom(vehicle_factory):
    """Four vehicles with distinct makes, models, categories and prices."""
    for make, model, category, price in [
        ("Toyota", "Corolla", "Sedan", "20000.00"),
        ("Toyota", "Camry", "Sedan", "30000.00"),
        ("Honda", "Civic", "Hatchback", "25000.00"),
        ("Honda", "CR-V", "SUV", "35000.00"),
    ]:
        vehicle_factory(make=make, model=model, category=category, price=Decimal(price))


def search(client, headers, **params) -> list[str]:
    """Models returned by a search, in response order."""
    response = client.get(SEARCH_URL, params=params, headers=headers)
    assert response.status_code == 200
    return [vehicle["model"] for vehicle in response.json()]


@pytest.mark.parametrize("make", ["toy", "TOY", "yot"])
def test_text_filters_match_any_part_ignoring_case(
    client, customer_headers, showroom, make
):
    """T-VEH-10 / FR-VEH-004: "toy" matches Toyota."""
    assert set(search(client, customer_headers, make=make)) == {"Corolla", "Camry"}


def test_filters_combine_with_and(client, customer_headers, showroom):
    """T-VEH-11: every supplied filter must match."""
    assert search(client, customer_headers, category="sedan", model="cam") == ["Camry"]


def test_price_bounds_are_inclusive(client, customer_headers, showroom):
    """T-VEH-12: vehicles priced exactly at either bound are included."""
    assert set(
        search(client, customer_headers, min_price="20000", max_price="30000")
    ) == {"Corolla", "Camry", "Civic"}
    assert search(client, customer_headers, min_price="20000", max_price="20000") == [
        "Corolla"
    ]


def test_a_search_with_no_matches_is_an_empty_list(client, customer_headers, showroom):
    """T-VEH-13: no matches gives 200 []."""
    assert search(client, customer_headers, make="Ferrari") == []


def test_a_search_without_filters_equals_the_list(client, customer_headers, showroom):
    """T-VEH-13 / SRS §4.4: no filters returns the full list, in the same order."""
    listed = client.get("/api/vehicles", headers=customer_headers).json()

    assert search(client, customer_headers) == [v["model"] for v in listed]


def test_blank_and_unknown_parameters_are_ignored(client, customer_headers, showroom):
    """FR-VEH-004 / FR-VEH-005: make= and colour=red do not filter anything."""
    results = search(client, customer_headers, make="", min_price="", colour="red")

    assert len(results) == 4


@pytest.mark.parametrize(
    ("make", "expected"), [("_", {"Z4"}), ("%", set()), ("\\", set())]
)
def test_like_wildcards_in_input_match_literally(
    client, customer_headers, showroom, vehicle_factory, make, expected
):
    """T-VEH-14 / NFR-SEC-005: %, _ and \\ are not treated as wildcards."""
    vehicle_factory(make="B_W", model="Z4")

    assert set(search(client, customer_headers, make=make)) == expected


def test_search_is_a_route_not_a_vehicle_id(client, customer_headers):
    """T-VEH-15 / SRS §4.4: /search returns a list, never a vehicle lookup."""
    response = client.get(SEARCH_URL, headers=customer_headers)

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.parametrize(
    ("params", "field"),
    [
        ({"min_price": "500", "max_price": "100"}, "max_price"),
        ({"min_price": "-1"}, "min_price"),
        ({"max_price": "abc"}, "max_price"),
        ({"min_price": "10.999"}, "min_price"),
        ({"make": "x" * 51}, "make"),
    ],
)
def test_invalid_search_parameters_are_a_422(
    client, customer_headers, showroom, params, field
):
    """T-VEH-16 / FR-VEH-005: bad prices, min > max or long text give 422."""
    response = client.get(SEARCH_URL, params=params, headers=customer_headers)

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert {(d["location"], d["field"]) for d in error["details"]} == {("query", field)}


def test_searching_requires_a_token(client):
    """FR-AUTH-006: no token gives 401."""
    response = client.get(SEARCH_URL, params={"make": "toy"})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "NOT_AUTHENTICATED"
