from collections.abc import Mapping
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

HTTP_ERRORS = {
    404: ("NOT_FOUND", "Resource not found."),
    405: ("METHOD_NOT_ALLOWED", "Method not allowed."),
}


def error_response(
    status_code: int,
    code: str,
    message: str,
    details: list[dict[str, Any]] | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    """Build a response in the SRS §4.2 error envelope."""
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


def register_exception_handlers(app: FastAPI) -> None:
    """Make every error the app returns use the SRS §4.2 envelope."""
    app.add_exception_handler(StarletteHTTPException, handle_http_exception)
    app.add_exception_handler(RequestValidationError, handle_validation_error)
