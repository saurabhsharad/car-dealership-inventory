from datetime import datetime, timedelta

from sqlalchemy import select

from app.models import User

REGISTER_URL = "/api/auth/register"
PASSWORD = "s3cure-pass"


def test_register_creates_a_customer_with_a_normalized_email(client):
    """T-AUTH-01: 201 with the public user; the email is trimmed and lower-cased."""
    response = client.post(
        REGISTER_URL, json={"email": "  Asha@Example.com ", "password": PASSWORD}
    )

    assert response.status_code == 201
    user = response.json()["user"]
    assert set(response.json()) == {"user"}
    assert set(user) == {"id", "email", "role", "created_at"}
    assert user["email"] == "asha@example.com"
    assert user["role"] == "customer"
    assert datetime.fromisoformat(user["created_at"]).utcoffset() == timedelta(0)


def test_register_never_returns_the_password_or_its_hash(client):
    """FR-AUTH-001 / NFR-SEC-001: the response holds no secret material."""
    response = client.post(
        REGISTER_URL, json={"email": "asha@example.com", "password": PASSWORD}
    )

    assert response.status_code == 201
    assert PASSWORD not in response.text
    assert "argon2" not in response.text


def test_register_stores_an_argon2id_hash(client, db_session):
    """T-AUTH-07: the stored hash is Argon2id, never the plaintext."""
    client.post(REGISTER_URL, json={"email": "asha@example.com", "password": PASSWORD})

    stored = db_session.scalar(select(User).where(User.email == "asha@example.com"))

    assert stored is not None
    assert stored.password_hash.startswith("$argon2id$")
