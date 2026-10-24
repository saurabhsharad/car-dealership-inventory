from app.core import security

LOGIN_URL = "/api/auth/login"
PASSWORD = "s3cure-pass"
INVALID_CREDENTIALS = {
    "error": {
        "code": "INVALID_CREDENTIALS",
        "message": "Invalid email or password.",
    }
}


def register(client) -> None:
    response = client.post(
        "/api/auth/register", json={"email": "asha@example.com", "password": PASSWORD}
    )
    assert response.status_code == 201


def test_wrong_password_is_rejected_with_invalid_credentials(client):
    """T-AUTH-09 / FR-AUTH-005: a wrong password is a 401, never a token."""
    register(client)

    response = client.post(
        LOGIN_URL, json={"email": "asha@example.com", "password": "wrong-pass"}
    )

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert response.json() == INVALID_CREDENTIALS


def test_unknown_email_gets_the_identical_response(client):
    """T-AUTH-09 / FR-AUTH-005: nobody can tell which emails have accounts."""
    register(client)
    wrong_password = client.post(
        LOGIN_URL, json={"email": "asha@example.com", "password": "wrong-pass"}
    )

    unknown_email = client.post(
        LOGIN_URL, json={"email": "nobody@example.com", "password": PASSWORD}
    )

    assert unknown_email.status_code == wrong_password.status_code == 401
    assert unknown_email.headers["WWW-Authenticate"] == "Bearer"
    assert unknown_email.content == wrong_password.content


def test_unknown_email_still_spends_one_password_check(client, monkeypatch):
    """FR-AUTH-005: an unknown email costs one Argon2 check, like a known one."""
    checked_hashes = []
    real_verify = security.password_hasher.verify

    def spy(password: str, password_hash: str) -> bool:
        checked_hashes.append(password_hash)
        return real_verify(password, password_hash)

    monkeypatch.setattr(security.password_hasher, "verify", spy)

    response = client.post(
        LOGIN_URL, json={"email": "nobody@example.com", "password": PASSWORD}
    )

    assert response.status_code == 401
    assert len(checked_hashes) == 1
    assert checked_hashes[0].startswith("$argon2id$")
