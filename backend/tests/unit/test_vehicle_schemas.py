from datetime import UTC, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.vehicles import VehicleCreate, VehicleOut, VehicleUpdate

VALID = {"make": "Toyota", "model": "Corolla", "category": "Sedan", "price": "24999.00"}


def invalid_fields(schema, data: dict) -> set[str]:
    """Names of the fields the schema rejects, or an empty set if it accepts."""
    try:
        schema.model_validate(data)
    except ValidationError as error:
        return {str(e["loc"][0]) for e in error.errors()}
    return set()


def test_create_trims_text_and_keeps_the_exact_price():
    """FR-VEH-002: text is trimmed; price is an exact Decimal, never a float."""
    vehicle = VehicleCreate.model_validate(
        {**VALID, "make": "  Toyota ", "price": "24999.10"}
    )

    assert vehicle.make == "Toyota"
    assert vehicle.price == Decimal("24999.10")
    assert isinstance(vehicle.price, Decimal)


@pytest.mark.parametrize("price", ["24999.10", 24999.1, 1, "0.01", "9999999999.99"])
def test_create_accepts_a_price_as_number_or_numeric_string(price):
    """FR-VEH-002: a JSON number or numeric string, up to the column limit."""
    assert invalid_fields(VehicleCreate, {**VALID, "price": price}) == set()


@pytest.mark.parametrize(
    "price",
    [0, -5, "abc", True, "10.999", 10.999, "10000000000.00", "NaN", None],
)
def test_create_rejects_an_invalid_price(price):
    """T-VEH-04: not positive, not numeric, boolean, 3 decimals or too large."""
    assert invalid_fields(VehicleCreate, {**VALID, "price": price}) == {"price"}


def test_create_defaults_stock_to_zero():
    """T-VEH-02: quantity_in_stock is optional and defaults to 0."""
    assert VehicleCreate.model_validate(VALID).quantity_in_stock == 0


@pytest.mark.parametrize("stock", [0, 10_000])
def test_create_accepts_stock_from_0_to_10000(stock):
    """FR-VEH-002: both ends of the initial-stock range are allowed."""
    assert invalid_fields(VehicleCreate, {**VALID, "quantity_in_stock": stock}) == set()


@pytest.mark.parametrize("stock", [-1, 1.5, 1.0, "3", True, 10_001])
def test_create_rejects_stock_that_is_not_a_strict_integer_in_range(stock):
    """T-VEH-06: floats, strings, booleans and out-of-range values fail."""
    assert invalid_fields(VehicleCreate, {**VALID, "quantity_in_stock": stock}) == {
        "quantity_in_stock"
    }


@pytest.mark.parametrize("field", ["make", "model", "category"])
@pytest.mark.parametrize("value", ["", "   ", "x" * 51])
def test_create_rejects_blank_or_too_long_text(field, value):
    """T-VEH-07: text must be 1 to 50 characters after trimming."""
    assert invalid_fields(VehicleCreate, {**VALID, field: value}) == {field}


def test_create_accepts_50_characters_after_trimming():
    """FR-VEH-002: the limit applies to the trimmed value."""
    assert invalid_fields(VehicleCreate, {**VALID, "make": f"  {'x' * 50}  "}) == set()


@pytest.mark.parametrize("field", ["make", "model", "category", "price"])
def test_create_requires_every_descriptive_field(field):
    """T-VEH-03: a missing required field fails on that field."""
    data = {key: value for key, value in VALID.items() if key != field}

    assert invalid_fields(VehicleCreate, data) == {field}


@pytest.mark.parametrize("field", ["id", "created_at", "updated_at", "colour"])
def test_create_rejects_fields_outside_the_schema(field):
    """T-VEH-07 / FR-VEH-002: clients can never set id or timestamps."""
    assert invalid_fields(VehicleCreate, {**VALID, field: 1}) == {field}


def test_update_rejects_a_stock_change():
    """T-VEH-18 / A-10: stock changes only through purchase and restock."""
    assert invalid_fields(VehicleUpdate, {**VALID, "quantity_in_stock": 5}) == {
        "quantity_in_stock"
    }


@pytest.mark.parametrize("field", ["make", "model", "category", "price"])
def test_update_requires_every_field(field):
    """T-VEH-18 / FR-VEH-006: PUT replaces all four fields."""
    data = {key: value for key, value in VALID.items() if key != field}

    assert invalid_fields(VehicleUpdate, data) == {field}


def test_update_applies_the_same_rules_as_create():
    """FR-VEH-006: an update is validated as in FR-VEH-002."""
    assert invalid_fields(VehicleUpdate, {**VALID, "make": " ", "price": 0}) == {
        "make",
        "price",
    }


@pytest.mark.parametrize(
    ("stored", "shown"),
    [
        (Decimal("24999.10"), "24999.10"),
        (Decimal("24999"), "24999.00"),
        (Decimal("0.5"), "0.50"),
    ],
)
def test_output_shows_the_price_as_a_two_decimal_string(stored, shown):
    """SRS §4.1 / T-VEH-05: price leaves the API as a string with 2 decimals."""
    now = datetime(2026, 10, 23, 16, 40, tzinfo=UTC)
    vehicle = VehicleOut(
        id=42,
        make="Toyota",
        model="Corolla",
        category="Sedan",
        price=stored,
        quantity_in_stock=3,
        created_at=now,
        updated_at=now,
    )

    assert vehicle.model_dump(mode="json")["price"] == shown
