import pytest
from pydantic import ValidationError

from app.core.config import Settings

VALID_ENV = {
    "DATABASE_URL": "postgresql+psycopg://user:pass@localhost:5432/dealership",
    "JWT_SECRET_KEY": "x" * 32,
}


@pytest.mark.parametrize("missing_var", ["DATABASE_URL", "JWT_SECRET_KEY"])
def test_settings_fail_fast_when_required_variable_missing(monkeypatch, missing_var):
    """T-CFG-01 / NFR-REL-002: settings refuse to load without a required variable."""
    for name, value in VALID_ENV.items():
        monkeypatch.setenv(name, value)
    monkeypatch.delenv(missing_var)

    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)

    error_fields = {error["loc"][0] for error in exc_info.value.errors()}
    assert missing_var.lower() in error_fields

def test_optional_settings_use_srs_defaults(monkeypatch):
    """NFR-CFG-001: optional settings fall back to their documented defaults."""
    for name, value in VALID_ENV.items():
        monkeypatch.setenv(name, value)
    for name in ("JWT_EXPIRES_MINUTES", "CORS_ORIGINS", "TEST_DATABASE_URL"):
        monkeypatch.delenv(name, raising=False)

    settings = Settings(_env_file=None)

    assert settings.jwt_expires_minutes == 30
    assert settings.cors_origins == ["http://localhost:5173"]
    assert settings.test_database_url is None
