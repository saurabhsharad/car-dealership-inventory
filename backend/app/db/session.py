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
    """Placeholder: a session with no transaction handling yet."""
    with Session(engine) as session:
        yield session


DbSession = Annotated[Session, Depends(get_db)]
