from fastapi import FastAPI

from app.api.errors import register_exception_handlers
from app.api.routes import auth

app = FastAPI(
    title="Car Dealership Inventory API",
    version="0.1.0",
)
register_exception_handlers(app)
app.include_router(auth.router, prefix="/api")
