from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


def error_response(
    status_code: int,
    code: str,
    message: str,
    details: list[dict[str, Any]] | None = None,
) -> JSONResponse:
    """Build a response in the SRS §4.2 error envelope."""
    error: dict[str, Any] = {"code": code, "message": message}
    if details is not None:
        error["details"] = details
    return JSONResponse(status_code=status_code, content={"error": error})


async def handle_http_exception(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Wrap framework HTTP errors, such as an unknown route, in the envelope."""
    return error_response(exc.status_code, "NOT_FOUND", "Resource not found.")


async def handle_validation_error(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Report each invalid field without echoing the submitted values."""
    details = [
        {
            "location": str(error["loc"][0]),
            "field": ".".join(str(part) for part in error["loc"][1:]),
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
