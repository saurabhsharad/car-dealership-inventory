import logging
from collections.abc import Mapping
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.services.errors import (
    DomainError,
    EmailAlreadyRegisteredError,
    ForbiddenError,
    InvalidCredentialsError,
    NotAuthenticatedError,
    OutOfStockError,
    SessionExpiredError,
    VehicleNotFoundError,
)

logger = logging.getLogger("app.errors")

HTTP_ERRORS = {
    404: ("NOT_FOUND", "Resource not found."),
    405: ("METHOD_NOT_ALLOWED", "Method not allowed."),
}

DOMAIN_ERRORS: dict[type[DomainError], tuple[int, str, str]] = {
    EmailAlreadyRegisteredError: (
        409,
        "EMAIL_ALREADY_REGISTERED",
        "An account with this email already exists.",
    ),
    InvalidCredentialsError: (
        401,
        "INVALID_CREDENTIALS",
        "Invalid email or password.",
    ),
    NotAuthenticatedError: (401, "NOT_AUTHENTICATED", "Authentication required."),
    SessionExpiredError: (
        401,
        "TOKEN_EXPIRED",
        "Your session has expired. Please log in again.",
    ),
    ForbiddenError: (403, "FORBIDDEN", "Admin access required."),
    VehicleNotFoundError: (404, "VEHICLE_NOT_FOUND", "Vehicle not found."),
    OutOfStockError: (409, "OUT_OF_STOCK", "This vehicle is out of stock."),
}


def error_response(
    status_code: int,
    code: str,
    message: str,
    details: list[dict[str, Any]] | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    """Build a response in the SRS §4.2 error envelope.

    Every 401 carries WWW-Authenticate: Bearer (SRS §4.2).
    """
    if status_code == 401:
        headers = {**(headers or {}), "WWW-Authenticate": "Bearer"}
    error: dict[str, Any] = {"code": code, "message": message}
    if details is not None:
        error["details"] = details
    return JSONResponse(
        status_code=status_code, content={"error": error}, headers=headers
    )


async def handle_http_exception(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Wrap framework HTTP errors in the envelope, keeping their headers."""
    code, message = HTTP_ERRORS.get(exc.status_code, ("HTTP_ERROR", "Request failed."))
    return error_response(exc.status_code, code, message, headers=exc.headers)


def error_field(error: dict[str, Any]) -> str | None:
    """Dotted path of the invalid field, or None if the whole body is unusable."""
    if error["type"] == "json_invalid":
        return None
    return ".".join(str(part) for part in error["loc"][1:]) or None


async def handle_validation_error(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Report each invalid field without echoing the submitted values."""
    details = [
        {
            "location": str(error["loc"][0]),
            "field": error_field(error),
            "message": error["msg"],
        }
        for error in exc.errors()
    ]
    return error_response(
        422, "VALIDATION_ERROR", "Request validation failed.", details
    )


async def handle_domain_error(request: Request, exc: DomainError) -> JSONResponse:
    """Map a business-rule failure from the services to its HTTP error."""
    status_code, code, message = DOMAIN_ERRORS[type(exc)]
    return error_response(status_code, code, message)


async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    """Log any unhandled error in full and answer with a generic 500.

    The client never sees the exception, its message or a traceback
    (NFR-ERR-001); they are written to the app.errors logger instead.
    """
    logger.error(
        "Unhandled error on %s %s", request.method, request.url.path, exc_info=exc
    )
    return error_response(500, "INTERNAL_ERROR", "An unexpected error occurred.")


def register_exception_handlers(app: FastAPI) -> None:
    """Make every error the app returns use the SRS §4.2 envelope."""
    app.add_exception_handler(StarletteHTTPException, handle_http_exception)
    app.add_exception_handler(RequestValidationError, handle_validation_error)
    app.add_exception_handler(DomainError, handle_domain_error)
    app.add_exception_handler(Exception, handle_unexpected_error)
