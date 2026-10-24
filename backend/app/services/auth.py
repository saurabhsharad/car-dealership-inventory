from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models import User
from app.services.errors import EmailAlreadyRegisteredError, InvalidCredentialsError

# Checked when the email is unknown, so that path costs one Argon2
# verification too and its timing does not reveal which emails exist.
DUMMY_PASSWORD_HASH = hash_password("not-a-real-password")


def register_user(db: Session, email: str, password: str) -> User:
    """Create a customer account with a hashed password (FR-AUTH-001)."""
    return add_user(db, email, password, role="customer")


def create_admin(db: Session, email: str, password: str) -> User:
    """Create an admin account; only the CLI calls this (FR-AUTH-008, A-03)."""
    return add_user(db, email, password, role="admin")


def add_user(db: Session, email: str, password: str, role: str) -> User:
    """Insert a user with a hashed password and the given role.

    The unique constraint decides whether the email is taken, so a
    duplicate is caught atomically, even when two requests race.
    """
    user = User(email=email, password_hash=hash_password(password), role=role)
    db.add(user)
    try:
        db.flush()
    except IntegrityError as error:
        if error.orig.diag.constraint_name == "uq_users_email":
            raise EmailAlreadyRegisteredError from error
        raise
    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    """Return the account for these credentials (FR-AUTH-004, FR-AUTH-005).

    An unknown email and a wrong password raise the same error after the
    same amount of hashing work, so neither reveals whether the email exists.
    """
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        verify_password(password, DUMMY_PASSWORD_HASH)
        raise InvalidCredentialsError
    if not verify_password(password, user.password_hash):
        raise InvalidCredentialsError
    return user
