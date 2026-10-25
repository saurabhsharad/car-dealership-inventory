import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app

OTHER_ORIGIN = "http://evil.example"


@pytest.fixture
def frontend_origin() -> str:
    """The first allowed origin, the Vite dev server by default."""
    return get_settings().cors_origins[0]


def preflight(origin: str):
    """What a browser sends before a cross-origin request with a token."""
    return TestClient(app).options(
        "/api/vehicles",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization, content-type",
        },
    )


def test_the_frontend_origin_passes_the_preflight(frontend_origin):
    """NFR-SEC-006: the SPA may send JSON with a bearer token."""
    response = preflight(frontend_origin)

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == frontend_origin
    allowed_headers = response.headers["access-control-allow-headers"].lower()
    assert {"authorization", "content-type"} <= {
        header.strip() for header in allowed_headers.split(",")
    }
    assert "POST" in response.headers["access-control-allow-methods"]


def test_an_error_response_is_still_readable_by_the_frontend(frontend_origin):
    """The SPA must be able to read error envelopes, such as a 401."""
    response = TestClient(app).get("/api/vehicles", headers={"Origin": frontend_origin})

    assert response.status_code == 401
    assert response.headers.get("access-control-allow-origin") == frontend_origin


def test_any_other_origin_is_refused():
    """NFR-SEC-006: an explicit allowlist; other sites get no CORS grant."""
    response = preflight(OTHER_ORIGIN)

    assert "access-control-allow-origin" not in response.headers


def test_the_wildcard_origin_is_never_used(frontend_origin):
    """NFR-SEC-006: never "*", even for an allowed origin."""
    response = preflight(frontend_origin)

    assert response.headers.get("access-control-allow-origin") != "*"
    assert "*" not in get_settings().cors_origins
