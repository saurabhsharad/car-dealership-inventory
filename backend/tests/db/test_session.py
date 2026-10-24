from decimal import Decimal

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.db.session import DbSession, get_engine
from app.models import Vehicle


class EndpointFailed(Exception):
    """Raised by the test route after it has written a vehicle."""


def make_client(engine, price: str, fail: bool) -> TestClient:
    """A throwaway app whose one route writes a vehicle through get_db."""
    test_app = FastAPI()
    test_app.dependency_overrides[get_engine] = lambda: engine

    @test_app.post("/vehicles")
    def create_vehicle(db: DbSession) -> dict[str, bool]:
        db.add(
            Vehicle(
                make="Toyota", model="Corolla", category="Sedan", price=Decimal(price)
            )
        )
        if fail:
            raise EndpointFailed
        return {"ok": True}

    return TestClient(test_app, raise_server_exceptions=False)


def vehicle_count(engine) -> int:
    with engine.connect() as connection:
        return connection.scalar(select(func.count()).select_from(Vehicle))


def test_get_db_commits_when_the_endpoint_succeeds(committed_db):
    """SRS §5.3: a successful request commits its transaction."""
    response = make_client(committed_db, price="24999.00", fail=False).post("/vehicles")

    assert response.status_code == 200
    assert vehicle_count(committed_db) == 1


def test_get_db_rolls_back_when_the_endpoint_raises(committed_db):
    """FR-INV-006: an exception rolls the whole request back."""
    response = make_client(committed_db, price="24999.00", fail=True).post("/vehicles")

    assert response.status_code == 500
    assert vehicle_count(committed_db) == 0


def test_failed_commit_is_never_reported_as_success(committed_db):
    """FR-INV-006: the response is sent only after the commit succeeds."""
    response = make_client(committed_db, price="0", fail=False).post("/vehicles")

    assert response.status_code == 500
    assert vehicle_count(committed_db) == 0
