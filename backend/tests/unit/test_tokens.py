import base64
import json
from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.core.tokens import (
    InvalidTokenError,
    TokenExpiredError,
    create_access_token,
    decode_access_token,
)

SECRET = "s" * 64
LIFETIME = timedelta(minutes=30)


def make_token(user_id: int = 7, now: datetime | None = None) -> str:
    return create_access_token(
        user_id, secret=SECRET, lifetime=LIFETIME, now=now or datetime.now(UTC)
    )


def test_token_is_hs256_with_only_sub_iat_and_exp():
    """FR-AUTH-004 / NFR-SEC-003: HS256, claims sub, iat and exp only."""
    now = datetime(2026, 10, 23, 16, 40, tzinfo=UTC)
    token = make_token(user_id=7, now=now)

    assert jwt.get_unverified_header(token)["alg"] == "HS256"
    claims = jwt.decode(
        token, SECRET, algorithms=["HS256"], options={"verify_exp": False}
    )
    assert claims == {
        "sub": "7",
        "iat": int(now.timestamp()),
        "exp": int((now + LIFETIME).timestamp()),
    }


def test_a_fresh_token_decodes_to_its_user_id():
    """T-AUTH-08: a token the server issued identifies the user."""
    assert decode_access_token(make_token(user_id=7), secret=SECRET) == 7


def test_an_expired_token_is_rejected_as_expired():
    """T-AUTH-11: exp in the past raises TokenExpiredError."""
    now = datetime.now(UTC)
    claims = {"sub": "7", "iat": now - 2 * LIFETIME, "exp": now - LIFETIME}
    token = jwt.encode(claims, SECRET, algorithm="HS256")

    with pytest.raises(TokenExpiredError):
        decode_access_token(token, secret=SECRET)


def encode_segment(data: dict) -> str:
    """Base64url-encode a JWT header or payload, as the JWT format does."""
    raw = json.dumps(data, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def forged_token(kind: str) -> str:
    """A token the server did not issue, or one that is not a JWT at all."""
    now = int(datetime.now(UTC).timestamp())
    claims = {"sub": "7", "iat": now, "exp": now + int(LIFETIME.total_seconds())}
    header, _, signature = jwt.encode(claims, SECRET, algorithm="HS256").split(".")
    other_user = encode_segment({**claims, "sub": "8"})
    return {
        "wrong_secret": jwt.encode(claims, "x" * 64, algorithm="HS256"),
        "tampered_payload": f"{header}.{other_user}.{signature}",
        "alg_none": jwt.encode(claims, None, algorithm="none"),
        "hs512": jwt.encode(claims, SECRET, algorithm="HS512"),
        "garbage": "not-a-jwt",
    }[kind]


@pytest.mark.parametrize(
    "kind", ["wrong_secret", "tampered_payload", "alg_none", "hs512", "garbage"]
)
def test_a_forged_or_malformed_token_is_rejected(kind):
    """T-AUTH-12 / NFR-SEC-002: only HS256 tokens signed with our secret pass."""
    with pytest.raises(InvalidTokenError) as error:
        decode_access_token(forged_token(kind), secret=SECRET)

    assert not isinstance(error.value, TokenExpiredError)
