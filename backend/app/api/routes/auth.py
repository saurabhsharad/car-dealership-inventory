from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, status

from app.api.dependencies import AppSettings
from app.core.tokens import create_access_token
from app.db.session import DbSession
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    PublicUser,
    RegisterRequest,
    RegisterResponse,
)
from app.services.auth import authenticate_user, register_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register", status_code=status.HTTP_201_CREATED, response_model=RegisterResponse
)
def register(body: RegisterRequest, db: DbSession) -> RegisterResponse:
    """Register a customer account (FR-AUTH-001)."""
    user = register_user(db, body.email, body.password)
    return RegisterResponse(user=PublicUser.model_validate(user))


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, db: DbSession, settings: AppSettings) -> LoginResponse:
    """Exchange an email and password for a bearer token (FR-AUTH-004)."""
    user = authenticate_user(db, body.email, body.password)
    lifetime = timedelta(minutes=settings.jwt_expires_minutes)
    token = create_access_token(
        user.id,
        secret=settings.jwt_secret_key.get_secret_value(),
        lifetime=lifetime,
        now=datetime.now(UTC),
    )
    return LoginResponse(
        access_token=token,
        expires_in=int(lifetime.total_seconds()),
        user=PublicUser.model_validate(user),
    )
