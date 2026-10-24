from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import User


def register_user(db: Session, email: str, password: str) -> User:
    """Create a customer account with a hashed password (FR-AUTH-001)."""
    user = User(email=email, password_hash=hash_password(password))
    db.add(user)
    db.flush()
    return user
