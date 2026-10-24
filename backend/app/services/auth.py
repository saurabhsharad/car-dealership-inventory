from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import User
from app.services.errors import EmailAlreadyRegisteredError


def register_user(db: Session, email: str, password: str) -> User:
    """Create a customer account with a hashed password (FR-AUTH-001).

    The unique constraint decides whether the email is taken, so a
    duplicate is caught atomically, even when two requests race.
    """
    user = User(email=email, password_hash=hash_password(password))
    db.add(user)
    try:
        db.flush()
    except IntegrityError as error:
        if error.orig.diag.constraint_name == "uq_users_email":
            raise EmailAlreadyRegisteredError from error
        raise
    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    """Return the account for these credentials (FR-AUTH-004)."""
    return db.scalar(select(User).where(User.email == email))
