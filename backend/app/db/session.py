from collections.abc import Iterator
from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

from app.core.config import get_settings


@lru_cache
def get_engine() -> Engine:
    """The app's engine for DATABASE_URL, created on first use."""
    return create_engine(get_settings().database_url, pool_pre_ping=True)


def get_db(engine: Annotated[Engine, Depends(get_engine)]) -> Iterator[Session]:
    """One session and one transaction per request (SRS §5.3).

    The transaction commits after the endpoint returns and rolls back if
    anything raises, including the commit itself.
    """
    with Session(engine) as session, session.begin():
        yield session


# scope="function" finishes the commit before the response is sent, so a
# failed commit can never be reported to the client as a success.
DbSession = Annotated[Session, Depends(get_db, scope="function")]
