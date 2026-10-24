import pytest
from sqlalchemy import func, select

from app.models import User

REGISTER_URL = "/api/auth/register"
VALID_BODY = {"email": "asha@example.com", "password": "s3cure-pass"}


def user_count(db_session) -> int:
    return db_session.scalar(select(func.count()).select_from(User))


def invalid_fields(response) -> set[str]:
    return {detail["field"] for detail in response.json()["error"]["details"]}


@pytest.mark.parametrize(
    "email",
    ["not-an-email", "asha@", "@example.com", "a" * 245 + "@example.com"],
)
def test_register_rejects_an_invalid_email(client, db_session, email):
    """T-AUTH-02: a malformed or over-long email is a 422 on the email field."""
    response = client.post(REGISTER_URL, json={**VALID_BODY, "email": email})

    assert response.status_code == 422
    assert invalid_fields(response) == {"email"}
    assert user_count(db_session) == 0


@pytest.mark.parametrize("extra", [{"role": "admin"}, {"nickname": "asha"}])
def test_register_rejects_unknown_fields_including_role(client, db_session, extra):
    """T-AUTH-03 / NFR-SEC-004: no field outside the schema, so no self-made admin."""
    response = client.post(REGISTER_URL, json={**VALID_BODY, **extra})

    assert response.status_code == 422
    assert invalid_fields(response) == set(extra)
    assert user_count(db_session) == 0


@pytest.mark.parametrize("length", [7, 129])
def test_register_rejects_a_password_outside_8_to_128_characters(
    client, db_session, length
):
    """T-AUTH-05 / FR-AUTH-003: passwords must be 8 to 128 characters."""
    response = client.post(REGISTER_URL, json={**VALID_BODY, "password": "p" * length})

    assert response.status_code == 422
    assert invalid_fields(response) == {"password"}
    assert user_count(db_session) == 0


@pytest.mark.parametrize("length", [8, 128])
def test_register_accepts_passwords_of_exactly_8_and_128_characters(client, length):
    """T-AUTH-05: both ends of the range are allowed."""
    response = client.post(REGISTER_URL, json={**VALID_BODY, "password": "p" * length})

    assert response.status_code == 201
