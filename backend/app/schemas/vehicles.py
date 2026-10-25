from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    PlainSerializer,
    StrictInt,
    StringConstraints,
    ValidationInfo,
    field_validator,
)

VehicleText = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)
]

# Exact, positive, at most two decimals and within NUMERIC(12,2). Pydantic
# accepts a JSON number or numeric string and rejects booleans and NaN.
Price = Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=2)]

# Money leaves the API as a two-decimal string, so it never becomes a float.
PriceText = Annotated[
    Decimal, PlainSerializer(lambda price: f"{price:.2f}", return_type=str)
]


def blank_to_none(value: object) -> object:
    """Treat an empty or whitespace-only query parameter as not given."""
    if isinstance(value, str) and not value.strip():
        return None
    return value


OptionalFilter = Annotated[
    Annotated[str, StringConstraints(max_length=50)] | None,
    BeforeValidator(blank_to_none),
]
OptionalPrice = Annotated[
    Annotated[Decimal, Field(ge=0, max_digits=12, decimal_places=2)] | None,
    BeforeValidator(blank_to_none),
]


class VehicleSearch(BaseModel):
    """Query parameters of GET /api/vehicles/search; all optional (FR-VEH-004).

    Prices are decimals of at least 0 with two places at most, min_price may
    not exceed max_price, and text filters are at most 50 characters
    (FR-VEH-005).
    """

    make: OptionalFilter = None
    model: OptionalFilter = None
    category: OptionalFilter = None
    min_price: OptionalPrice = None
    max_price: OptionalPrice = None

    @field_validator("max_price")
    @classmethod
    def not_below_min_price(
        cls, max_price: Decimal | None, info: ValidationInfo
    ) -> Decimal | None:
        min_price = info.data.get("min_price")
        if None not in (min_price, max_price) and max_price < min_price:
            raise ValueError("max_price must not be less than min_price")
        return max_price


class VehicleUpdate(BaseModel):
    """Body of PUT /api/vehicles/{id}: every field, but never the stock (A-10)."""

    model_config = ConfigDict(extra="forbid")

    make: VehicleText
    model: VehicleText
    category: VehicleText
    price: Price


class VehicleCreate(VehicleUpdate):
    """Body of POST /api/vehicles; initial stock is optional (FR-VEH-002)."""

    quantity_in_stock: StrictInt = Field(default=0, ge=0, le=10_000)


class VehicleOut(BaseModel):
    """A vehicle as the API returns it (SRS §4.3)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    make: str
    model: str
    category: str
    price: PriceText
    quantity_in_stock: int
    created_at: datetime
    updated_at: datetime


class RestockRequest(BaseModel):
    """Body of POST /api/vehicles/{id}/restock (FR-INV-005).

    The 10,000 limit applies to one request; total stock may grow beyond it.
    """

    model_config = ConfigDict(extra="forbid")

    quantity: StrictInt = Field(ge=1, le=10_000)
