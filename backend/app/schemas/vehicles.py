from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class VehicleCreate(BaseModel):
    """Placeholder: plain types with none of the SRS limits yet."""

    make: str
    model: str
    category: str
    price: Decimal
    quantity_in_stock: int = 0


class VehicleUpdate(BaseModel):
    """Placeholder: plain types with none of the SRS limits yet."""

    make: str
    model: str
    category: str
    price: Decimal


class VehicleOut(BaseModel):
    """Placeholder: price is not yet serialized as a two-decimal string."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    make: str
    model: str
    category: str
    price: Decimal
    quantity_in_stock: int
    created_at: datetime
    updated_at: datetime
