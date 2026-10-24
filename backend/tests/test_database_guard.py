import pytest

from tests.support.database import require_test_database_url


def test_missing_test_database_url_is_rejected():
    """SRS §7.3: database tests refuse to run without TEST_DATABASE_URL."""
    with pytest.raises(ValueError, match="TEST_DATABASE_URL is not set"):
        require_test_database_url(None)


@pytest.mark.parametrize(
    "url",
    [
        "postgresql+psycopg://user:pass@localhost:5435/dealership",
        "postgresql+psycopg://user:pass@localhost:5435/dealership_testing",
        "postgresql+psycopg://user:pass@localhost:5435/test_dealership",
        "postgresql+psycopg://user:pass@db_test:5435/dealership",
        "postgresql+psycopg://user:pass@localhost:5435/dealership?app=x_test",
    ],
)
def test_database_name_not_ending_in_test_is_rejected(url):
    """SRS §7.3: only a database whose name ends in _test may be wiped."""
    with pytest.raises(ValueError, match="must end in _test"):
        require_test_database_url(url)


def test_test_database_url_is_returned_unchanged():
    """A database name ending in _test is accepted as-is."""
    url = "postgresql+psycopg://user:pass@localhost:5435/dealership_test"

    assert require_test_database_url(url) == url
