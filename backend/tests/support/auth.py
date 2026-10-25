from datetime import UTC, datetime, timedelta

from app.core.config import get_settings
from app.core.tokens import create_access_token


def access_token_for(user_id: int, issued_at: datetime | None = None) -> str:
    """An access token signed exactly as /api/auth/login signs it."""
    settings = get_settings()
    return create_access_token(
        user_id,
        secret=settings.jwt_secret_key.get_secret_value(),
        lifetime=timedelta(minutes=settings.jwt_expires_minutes),
        now=issued_at or datetime.now(UTC),
    )


def bearer_headers(user_id: int) -> dict[str, str]:
    """An Authorization header carrying a fresh access token for the user."""
    return {"Authorization": f"Bearer {access_token_for(user_id)}"}
