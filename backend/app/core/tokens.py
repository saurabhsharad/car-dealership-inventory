from datetime import datetime, timedelta

import jwt


class InvalidTokenError(Exception):
    """The token is missing, malformed, badly signed or otherwise unusable."""


class TokenExpiredError(InvalidTokenError):
    """The token was valid but its exp time has passed."""


def create_access_token(
    user_id: int, *, secret: str, lifetime: timedelta, now: datetime
) -> str:
    """Placeholder: signs only the subject, with no iat or exp."""
    return jwt.encode({"sub": str(user_id)}, secret, algorithm="HS256")


def decode_access_token(token: str, *, secret: str) -> int:
    """Placeholder: reads the claims without checking signature or expiry."""
    try:
        claims = jwt.decode(token, options={"verify_signature": False})
    except jwt.PyJWTError as error:
        raise InvalidTokenError from error
    return int(claims["sub"])
