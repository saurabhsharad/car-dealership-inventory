from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Identity,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Vehicle(Base):
    """A vehicle model in the inventory with its current stock (SRS §5.1)."""

    __tablename__ = "vehicles"
    __table_args__ = (
        CheckConstraint("length(btrim(make)) > 0", name="make_not_blank"),
        CheckConstraint("length(btrim(model)) > 0", name="model_not_blank"),
        CheckConstraint("length(btrim(category)) > 0", name="category_not_blank"),
        CheckConstraint("price > 0", name="price_positive"),
        CheckConstraint("quantity_in_stock >= 0", name="stock_non_negative"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    make: Mapped[str] = mapped_column(String(50))
    model: Mapped[str] = mapped_column(String(50))
    category: Mapped[str] = mapped_column(String(50))
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    quantity_in_stock: Mapped[int] = mapped_column(Integer, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
