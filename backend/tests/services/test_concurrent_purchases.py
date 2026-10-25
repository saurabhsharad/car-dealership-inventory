from decimal import Decimal

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from app.models import Vehicle
from app.services.errors import OutOfStockError
from app.services.vehicles import purchase_vehicle
from tests.support.concurrency import run_concurrently

BUYERS = 10


def add_vehicle(engine: Engine, stock: int) -> int:
    with Session(engine) as session, session.begin():
        vehicle = Vehicle(
            make="Toyota",
            model="Corolla",
            category="Sedan",
            price=Decimal("24999.00"),
            quantity_in_stock=stock,
        )
        session.add(vehicle)
        session.flush()
        return vehicle.id


def connected_session(engine: Engine) -> Session:
    """A session that already holds its own connection and transaction."""
    session = Session(engine)
    session.connection()
    return session


def buy(session: Session, vehicle_id: int) -> str:
    """One customer's purchase, committed or rolled back on its own."""
    with session:
        try:
            purchase_vehicle(session, vehicle_id)
        except OutOfStockError:
            session.rollback()
            return "out of stock"
        session.commit()
        return "sold"


def stock_of(engine: Engine, vehicle_id: int) -> int:
    with Session(engine) as session:
        return session.get(Vehicle, vehicle_id).quantity_in_stock


@pytest.mark.concurrency
@pytest.mark.parametrize("stock", [1, 3])
def test_simultaneous_purchases_never_oversell(committed_db, stock):
    """T-INV-06 / T-INV-07 / FR-INV-003: exactly min(N, k) of N buyers succeed."""
    vehicle_id = add_vehicle(committed_db, stock)

    outcomes = run_concurrently(
        BUYERS,
        prepare=lambda: connected_session(committed_db),
        act=lambda session: buy(session, vehicle_id),
    )

    assert outcomes.count("sold") == stock
    assert outcomes.count("out of stock") == BUYERS - stock
    assert stock_of(committed_db, vehicle_id) == 0
