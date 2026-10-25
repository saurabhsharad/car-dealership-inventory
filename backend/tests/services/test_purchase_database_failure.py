from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.db.session import get_engine
from app.main import app
from app.models import User, Vehicle
from tests.support.auth import bearer_headers


@pytest.fixture
def real_client(committed_db):
    """The real app on the test database with real commits and rollbacks."""
    app.dependency_overrides[get_engine] = lambda: committed_db
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def failing_commits():
    """Make every commit fail as if the database connection had dropped."""

    def fail(session: Session) -> None:
        raise OperationalError("COMMIT", {}, Exception("simulated database failure"))

    event.listen(Session, "before_commit", fail)
    yield
    event.remove(Session, "before_commit", fail)


def add(engine, row):
    with Session(engine, expire_on_commit=False) as session, session.begin():
        session.add(row)
    return row


def stock_of(engine, vehicle_id: int) -> int:
    with Session(engine) as session:
        return session.get(Vehicle, vehicle_id).quantity_in_stock


def test_a_failed_commit_leaves_stock_unchanged(committed_db, real_client, request):
    """T-INV-11 / FR-INV-006: the decrement is rolled back and a 500 is sent."""
    customer = add(
        committed_db, User(email="buyer@example.com", password_hash="not-used")
    )
    vehicle = add(
        committed_db,
        Vehicle(
            make="Toyota",
            model="Corolla",
            category="Sedan",
            price=Decimal("24999.00"),
            quantity_in_stock=2,
        ),
    )
    request.getfixturevalue("failing_commits")

    response = real_client.post(
        f"/api/vehicles/{vehicle.id}/purchase", headers=bearer_headers(customer.id)
    )

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_ERROR"
    assert stock_of(committed_db, vehicle.id) == 2
