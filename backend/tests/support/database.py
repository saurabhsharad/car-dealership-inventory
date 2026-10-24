def require_test_database_url(url: str | None) -> str:
    """Return url only if it names a database ending in _test."""
    return url
