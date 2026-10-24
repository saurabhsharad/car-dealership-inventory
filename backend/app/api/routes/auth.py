from fastapi import APIRouter, status

from app.db.session import DbSession
from app.schemas.auth import PublicUser, RegisterRequest, RegisterResponse
from app.services.auth import register_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register", status_code=status.HTTP_201_CREATED, response_model=RegisterResponse
)
def register(body: RegisterRequest, db: DbSession) -> RegisterResponse:
    """Register a customer account (FR-AUTH-001)."""
    user = register_user(db, body.email, body.password)
    return RegisterResponse(user=PublicUser.model_validate(user))
