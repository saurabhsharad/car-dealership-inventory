from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import Settings, get_settings
from app.core.tokens import InvalidTokenError, TokenExpiredError, decode_access_token
from app.db.session import DbSession
from app.models import User
from app.services.errors import NotAuthenticatedError, SessionExpiredError

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: DbSession,
    settings: Annotated[Settings, Depends(get_settings)],
) -> User:
    """The user named by a valid bearer token, who must still exist (FR-AUTH-006)."""
    if credentials is None:
        raise NotAuthenticatedError
    try:
        user_id = decode_access_token(
            credentials.credentials,
            secret=settings.jwt_secret_key.get_secret_value(),
        )
    except TokenExpiredError as error:
        raise SessionExpiredError from error
    except InvalidTokenError as error:
        raise NotAuthenticatedError from error

    user = db.get(User, user_id)
    if user is None:
        raise NotAuthenticatedError
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
