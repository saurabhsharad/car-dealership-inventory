from sqlalchemy import make_url


def require_test_database_url(url: str | None) -> str:
    """Return url only if it names a database ending in _test.

    Database tests drop and rebuild the schema, so this guard stops them
    from ever running against the development or any other database.
    """
    if not url:
        raise ValueError("TEST_DATABASE_URL is not set.")

    database = make_url(url).database or ""
    if not database.endswith("_test"):
        raise ValueError(
            f"TEST_DATABASE_URL database name must end in _test, got {database!r}."
        )
    return url
