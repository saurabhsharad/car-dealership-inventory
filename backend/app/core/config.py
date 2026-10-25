from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Application settings loaded from environment variables and backend/.env."""

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        hide_input_in_errors=True,
    )

    database_url: str
    jwt_secret_key: SecretStr = Field(min_length=32)
    test_database_url: str | None = None
    jwt_expires_minutes: int = 30
    cors_origins: list[str] = ["http://localhost:5173"]

    @field_validator("database_url", mode="before")
    @classmethod
    def use_psycopg_driver(cls, value: str) -> str:
        """Normalize hosting-provider PostgreSQL URLs for psycopg 3."""
        if isinstance(value, str):
            if value.startswith("postgres://"):
                return "postgresql+psycopg://" + value.removeprefix("postgres://")
            if value.startswith("postgresql://"):
                return "postgresql+psycopg://" + value.removeprefix("postgresql://")
        return value


@lru_cache
def get_settings() -> Settings:
    """Return the application settings, loaded once and cached."""
    return Settings()
