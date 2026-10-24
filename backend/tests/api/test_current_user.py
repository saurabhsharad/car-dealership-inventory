from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies import CurrentUser
from app.api.errors import register_exception_handlers
from app.core.config import get_settings
from app.core.tokens import create_access_token
from app.db.session import get_db
from app.models import User

NOT_AUTHENTICATED = {
    "error": {"code": "NOT_AUTHENTICATED", "message": "Authentication required."}
}


@pytest.fixture
def protected_client(db_session):
    """A throwaway app with one route that requires a logged-in user."""
    test_app = FastAPI()
    register_exception_handlers(test_app)

    @test_app.get("/me")
    def me(user: CurrentUser) -> dict[str, int | str]:
        return {"id": user.id, "email": user.email}

    def get_test_db():
        yield db_session

    test_app.dependency_overrides[get_db] = get_test_db
    return TestClient(test_app)


@pytest.fixture
def user(db_session):
    user = User(email="asha@example.com", password_hash="not-used-here")
    db_session.add(user)
    db_session.flush()
    return user


def token_for(user_id: int, issued_at: datetime | None = None) -> str:
    settings = get_settings()
    return create_access_token(
        user_id,
        secret=settings.jwt_secret_key.get_secret_value(),
        lifetime=timedelta(minutes=settings.jwt_expires_minutes),
        now=issued_at or datetime.now(UTC),
    )


def get_me(client, authorization: str | None):
    headers = {} if authorization is None else {"Authorization": authorization}
    return client.get("/me", headers=headers)


def test_a_valid_token_identifies_the_user(protected_client, user):
    """FR-AUTH-006: a valid bearer token resolves to its user."""
    response = get_me(protected_client, f"Bearer {token_for(user.id)}")

    assert response.status_code == 200
    assert response.json() == {"id": user.id, "email": "asha@example.com"}


@pytest.mark.parametrize(
    "authorization",
    [None, "", "Bearer", "Bearer not-a-jwt", "Basic YXNoYTpzM2N1cmU="],
)
def test_a_missing_or_malformed_header_is_not_authenticated(
    protected_client, user, authorization
):
    """T-AUTH-10 / T-AUTH-12: no usable bearer token gives 401."""
    response = get_me(protected_client, authorization)

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert response.json() == NOT_AUTHENTICATED


def test_a_token_signed_with_another_secret_is_not_authenticated(
    protected_client, user
):
    """T-AUTH-12: a forged token gives 401 NOT_AUTHENTICATED."""
    now = datetime.now(UTC)
    claims = {"sub": str(user.id), "iat": now, "exp": now + timedelta(minutes=30)}
    forged = jwt.encode(claims, "x" * 64, algorithm="HS256")

    response = get_me(protected_client, f"Bearer {forged}")

    assert response.status_code == 401
    assert response.json() == NOT_AUTHENTICATED


def test_an_expired_token_is_reported_as_expired(protected_client, user):
    """T-AUTH-11: an expired token gives 401 TOKEN_EXPIRED."""
    long_ago = datetime.now(UTC) - timedelta(days=1)

    response = get_me(protected_client, f"Bearer {token_for(user.id, long_ago)}")

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert response.json() == {
        "error": {
            "code": "TOKEN_EXPIRED",
            "message": "Your session has expired. Please log in again.",
        }
    }


def test_a_token_for_a_deleted_user_is_not_authenticated(
    protected_client, user, db_session
):
    """T-AUTH-13: the token's user must still exist."""
    token = token_for(user.id)
    db_session.delete(user)
    db_session.flush()

    response = get_me(protected_client, f"Bearer {token}")

    assert response.status_code == 401
    assert response.json() == NOT_AUTHENTICATED
