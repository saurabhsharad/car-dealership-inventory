import pytest
from sqlalchemy import func, select

from app.core.security import verify_password
from app.models import User
from app.services.auth import create_admin
from app.services.errors import EmailAlreadyRegisteredError

PASSWORD = "s3cure-admin-pass"


def test_create_admin_stores_an_admin_with_a_hashed_password(db_session):
    """FR-AUTH-008: the admin gets role admin and an Argon2id hash."""
    admin = create_admin(db_session, "admin@example.com", PASSWORD)

    stored = db_session.get(User, admin.id)
    assert stored.role == "admin"
    assert stored.password_hash.startswith("$argon2id$")
    assert verify_password(PASSWORD, stored.password_hash)


def test_create_admin_refuses_an_email_that_is_already_registered(db_session):
    """FR-AUTH-008: an existing email fails and changes nothing."""
    create_admin(db_session, "admin@example.com", PASSWORD)
    db_session.commit()

    with pytest.raises(EmailAlreadyRegisteredError):
        create_admin(db_session, "admin@example.com", "another-pass")
    db_session.rollback()

    assert db_session.scalar(select(func.count()).select_from(User)) == 1
