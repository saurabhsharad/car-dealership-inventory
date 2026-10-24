from fastapi import FastAPI

from app.api.errors import register_exception_handlers

app = FastAPI(
    title="Car Dealership Inventory API",
    version="0.1.0",
)
register_exception_handlers(app)
