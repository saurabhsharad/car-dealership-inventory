from datetime import UTC, datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies import AdminUser
from app.api.errors import register_exception_handlers
from app.core.config import get_settings
from app.core.tokens import create_access_token
from app.db.session import get_db
from app.models import User

FORBIDDEN = {"error": {"code": "FORBIDDEN", "message": "Admin access required."}}


@pytest.fixture
def admin_client(db_session):
    """A throwaway app with one route that only admins may call."""
    test_app = FastAPI()
    register_exception_handlers(test_app)

    @test_app.post("/admin-only")
    def admin_only(user: AdminUser) -> dict[str, str]:
        return {"role": user.role}

    def get_test_db():
        yield db_session

    test_app.dependency_overrides[get_db] = get_test_db
    return TestClient(test_app)


def make_user(db_session, role: str) -> User:
    user = User(email=f"{role}@example.com", password_hash="not-used", role=role)
    db_session.add(user)
    db_session.flush()
    return user


def auth_header(user: User) -> dict[str, str]:
    settings = get_settings()
    token = create_access_token(
        user.id,
        secret=settings.jwt_secret_key.get_secret_value(),
        lifetime=timedelta(minutes=settings.jwt_expires_minutes),
        now=datetime.now(UTC),
    )
    return {"Authorization": f"Bearer {token}"}


def test_an_admin_is_allowed(admin_client, db_session):
    """FR-AUTH-007: an admin can call an admin-only route."""
    admin = make_user(db_session, "admin")

    response = admin_client.post("/admin-only", headers=auth_header(admin))

    assert response.status_code == 200
    assert response.json() == {"role": "admin"}


def test_a_customer_is_forbidden(admin_client, db_session):
    """T-AUTH-14 / FR-AUTH-007: a customer gets 403 FORBIDDEN."""
    customer = make_user(db_session, "customer")

    response = admin_client.post("/admin-only", headers=auth_header(customer))

    assert response.status_code == 403
    assert response.json() == FORBIDDEN
    assert "WWW-Authenticate" not in response.headers


def test_a_missing_token_is_401_before_any_role_check(admin_client):
    """SRS §4.1: authentication (401) is checked before authorization (403)."""
    response = admin_client.post("/admin-only")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "NOT_AUTHENTICATED"


def test_the_role_is_read_from_the_database_on_every_request(admin_client, db_session):
    """NFR-SEC-003: demoting an admin takes effect while their token is valid."""
    admin = make_user(db_session, "admin")
    headers = auth_header(admin)
    admin.role = "customer"
    db_session.flush()

    response = admin_client.post("/admin-only", headers=headers)

    assert response.status_code == 403
    assert response.json() == FORBIDDEN
