from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    database_url: str
    jwt_secret_key: str
    test_database_url: str | None = None
    jwt_expires_minutes: int = 30
    cors_origins: list[str] = ["http://localhost:5173"]




def get_settings() -> Settings:
    """Return the application settings."""
    return Settings()    