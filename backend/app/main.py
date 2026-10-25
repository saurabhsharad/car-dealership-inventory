from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.errors import register_exception_handlers
from app.api.routes import auth, vehicles
from app.core.config import get_settings

app = FastAPI(
    title="Car Dealership Inventory API",
    version="0.1.0",
)
# Only the listed origins (the Vite dev server by default) may call the API
# from a browser; there is no wildcard (NFR-SEC-006). The token travels in the
# Authorization header, not a cookie, so credentials mode is not needed.
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
register_exception_handlers(app)
app.include_router(auth.router, prefix="/api")
app.include_router(vehicles.router, prefix="/api")
