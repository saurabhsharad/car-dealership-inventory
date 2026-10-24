from datetime import datetime, timedelta

import jwt

ALGORITHM = "HS256"


class InvalidTokenError(Exception):
    """The token is missing, malformed, badly signed or otherwise unusable."""


class TokenExpiredError(InvalidTokenError):
    """The token was valid but its exp time has passed."""


def create_access_token(
    user_id: int, *, secret: str, lifetime: timedelta, now: datetime
) -> str:
    """Sign an HS256 access token carrying only sub, iat and exp (NFR-SEC-003)."""
    claims = {"sub": str(user_id), "iat": now, "exp": now + lifetime}
    return jwt.encode(claims, secret, algorithm=ALGORITHM)


def decode_access_token(token: str, *, secret: str) -> int:
    """Return the user id from a token this server signed and that has not expired.

    Only HS256 is accepted, so tokens using "none" or another algorithm fail.
    """
    try:
        claims = jwt.decode(
            token,
            secret,
            algorithms=[ALGORITHM],
            options={"require": ["sub", "iat", "exp"]},
        )
    except jwt.ExpiredSignatureError as error:
        raise TokenExpiredError from error
    except jwt.PyJWTError as error:
        raise InvalidTokenError from error
    return int(claims["sub"])
