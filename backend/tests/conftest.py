import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import get_settings
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
