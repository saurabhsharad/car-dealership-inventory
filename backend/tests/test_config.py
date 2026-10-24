import pytest
from pydantic import ValidationError
from pathlib import Path

from app.core.config import Settings, get_settings

VALID_ENV = {
    "DATABASE_URL": "postgresql+psycopg://user:pass@localhost:5432/dealership",
    "JWT_SECRET_KEY": "x" * 32,
}


@pytest.fixture
def required_env(monkeypatch):
    """Set every required variable to a valid value for the duration of one test."""
    for name, value in VALID_ENV.items():
        monkeypatch.setenv(name, value)


@pytest.fixture
def clear_settings_cache():
    """Run the test with an empty get_settings cache and leave it empty afterwards."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.mark.usefixtures("required_env")
@pytest.mark.parametrize("missing_var", ["DATABASE_URL", "JWT_SECRET_KEY"])
def test_settings_fail_fast_when_required_variable_missing(monkeypatch, missing_var):
    """T-CFG-01 / NFR-REL-002: settings refuse to load without a required variable."""
    monkeypatch.delenv(missing_var)

    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)

    error_fields = {error["loc"][0] for error in exc_info.value.errors()}
    assert missing_var.lower() in error_fields


@pytest.mark.usefixtures("required_env")
def test_optional_settings_use_srs_defaults(monkeypatch):
    """NFR-CFG-001: optional settings fall back to their documented defaults."""
    for name in ("JWT_EXPIRES_MINUTES", "CORS_ORIGINS", "TEST_DATABASE_URL"):
        monkeypatch.delenv(name, raising=False)

    settings = Settings(_env_file=None)

    assert settings.jwt_expires_minutes == 30
    assert settings.cors_origins == ["http://localhost:5173"]
    assert settings.test_database_url is None


@pytest.mark.usefixtures("required_env", "clear_settings_cache")
def test_get_settings_returns_one_cached_instance():
    """SRS §8.1: settings are loaded once and reused."""
    first = get_settings()
    second = get_settings()

    assert first is second

@pytest.mark.usefixtures("required_env")
def test_jwt_secret_key_is_hidden_when_settings_are_printed(monkeypatch):
    """NFR-SEC-008: the JWT secret never appears when settings are printed or logged."""
    secret = "unit-test-secret-" + "z" * 16
    monkeypatch.setenv("JWT_SECRET_KEY", secret)

    settings = Settings(_env_file=None)

    assert secret not in repr(settings)
    assert secret not in str(settings)
    assert settings.jwt_secret_key.get_secret_value() == secret    

def test_settings_read_dotenv_from_backend_directory():
    """Settings read backend/.env regardless of the directory the app is started from."""
    expected = Path(__file__).resolve().parents[1] / ".env"

    assert Settings.model_config.get("env_file") == expected
