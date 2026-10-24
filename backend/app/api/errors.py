from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


def error_response(status_code: int, code: str, message: str) -> JSONResponse:
    """Build a response in the SRS §4.2 error envelope."""
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message}},
    )


async def handle_http_exception(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Wrap framework HTTP errors, such as an unknown route, in the envelope."""
    return error_response(exc.status_code, "NOT_FOUND", "Resource not found.")


def register_exception_handlers(app: FastAPI) -> None:
    """Make every error the app returns use the SRS §4.2 envelope."""
    app.add_exception_handler(StarletteHTTPException, handle_http_exception)
