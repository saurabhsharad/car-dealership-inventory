from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import User, Vehicle
from tests.support.auth import bearer_headers
from tests.support.database import rebuild_schema, require_test_database_url


@pytest.fixture(scope="session")
def db_engine():
    """Engine for the validated test database, rebuilt by Alembic once per run."""
    try:
        url = require_test_database_url(get_settings().test_database_url)
    except ValueError as error:
        pytest.fail(str(error), pytrace=False)

    engine = create_engine(url)
    with engine.begin() as connection:
        rebuild_schema(connection)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    """Session whose work, commits included, is rolled back after the test."""
    with db_engine.connect() as connection:
        transaction = connection.begin()
        session = Session(bind=connection, join_transaction_mode="create_savepoint")
        try:
            yield session
        finally:
            session.close()
            transaction.rollback()


@pytest.fixture
def committed_db(db_engine):
    """Engine for tests that really commit; every table is emptied around them."""

    def empty_all_tables() -> None:
        tables = ", ".join(table.name for table in Base.metadata.sorted_tables)
        with db_engine.begin() as connection:
            connection.execute(text(f"TRUNCATE {tables} RESTART IDENTITY"))

    empty_all_tables()
    yield db_engine
    empty_all_tables()


@pytest.fixture
def client(db_session):
    """The real app, with each request's work going through db_session."""

    def get_test_db():
        try:
            yield db_session
            db_session.commit()
        except Exception:
            db_session.rollback()
            raise

    app.dependency_overrides[get_db] = get_test_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def user_factory(db_session):
    """Create users directly in db_session; their password is never checked.

    Factories commit (in db_session that only releases a savepoint), so a
    request that fails and rolls back cannot undo the test's own setup.
    """

    def create(role: str = "customer", email: str | None = None) -> User:
        user = User(
            email=email or f"{role}@example.com", password_hash="not-used", role=role
        )
        db_session.add(user)
        db_session.commit()
        return user

    return create


@pytest.fixture
def vehicle_factory(db_session):
    """Create vehicles directly in db_session; any field can be overridden."""

    def create(**overrides) -> Vehicle:
        values = {
            "make": "Toyota",
            "model": "Corolla",
            "category": "Sedan",
            "price": Decimal("24999.00"),
            "quantity_in_stock": 3,
            **overrides,
        }
        vehicle = Vehicle(**values)
        db_session.add(vehicle)
        db_session.commit()
        return vehicle

    return create


@pytest.fixture
def admin_headers(user_factory):
    """Authorization header for a freshly created admin."""
    return bearer_headers(user_factory("admin").id)


@pytest.fixture
def customer_headers(user_factory):
    """Authorization header for a freshly created customer."""
    return bearer_headers(user_factory("customer").id)
