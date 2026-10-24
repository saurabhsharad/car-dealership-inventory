from typing import Annotated

from fastapi import Depends
from sqlalchemy import select

from app.db.session import DbSession
from app.models import User


def get_current_user(db: DbSession) -> User:
    """Placeholder: treats every request as the first user, with no token check."""
    return db.scalar(select(User))


CurrentUser = Annotated[User, Depends(get_current_user)]
