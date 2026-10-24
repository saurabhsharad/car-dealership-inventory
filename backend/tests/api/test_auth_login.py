import jwt

from app.core.config import get_settings

LOGIN_URL = "/api/auth/login"
PASSWORD = "s3cure-pass"


def register(client, email: str = "asha@example.com") -> dict:
    response = client.post(
        "/api/auth/register", json={"email": email, "password": PASSWORD}
    )
    assert response.status_code == 201
    return response.json()["user"]


def test_login_returns_a_bearer_token_for_the_user(client):
    """T-AUTH-08 / FR-AUTH-004: 200 with a token, its lifetime and the user."""
    user = register(client)
    settings = get_settings()

    response = client.post(
        LOGIN_URL, json={"email": " Asha@Example.com ", "password": PASSWORD}
    )

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"access_token", "token_type", "expires_in", "user"}
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == settings.jwt_expires_minutes * 60
    assert body["user"] == user

    claims = jwt.decode(
        body["access_token"],
        settings.jwt_secret_key.get_secret_value(),
        algorithms=["HS256"],
    )
    assert claims["sub"] == str(user["id"])
    assert claims["exp"] - claims["iat"] == body["expires_in"]
