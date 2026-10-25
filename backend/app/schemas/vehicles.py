from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PlainSerializer,
    StrictInt,
    StringConstraints,
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
