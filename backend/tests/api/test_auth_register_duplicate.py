import pytest
from sqlalchemy import func, select

from app.models import User

REGISTER_URL = "/api/auth/register"
PASSWORD = "s3cure-pass"


@pytest.mark.parametrize("second_email", ["a@x.com", "A@X.com", "  a@x.com "])
def test_register_rejects_an_email_that_is_already_registered(
    client, db_session, second_email
):
    """T-AUTH-04 / FR-AUTH-002: emails are unique regardless of case or spaces."""
    first = client.post(REGISTER_URL, json={"email": "a@x.com", "password": PASSWORD})
    assert first.status_code == 201

    response = client.post(
        REGISTER_URL, json={"email": second_email, "password": PASSWORD}
    )

    assert response.status_code == 409
    assert response.json() == {
        "error": {
            "code": "EMAIL_ALREADY_REGISTERED",
            "message": "An account with this email already exists.",
        }
    }
    assert db_session.scalar(select(func.count()).select_from(User)) == 1
