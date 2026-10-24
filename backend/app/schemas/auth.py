from datetime import datetime
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, EmailStr, Field

NormalizedEmail = Annotated[EmailStr, AfterValidator(str.lower)]


class RegisterRequest(BaseModel):
    """Body of POST /api/auth/register; any other field is rejected (A-03)."""

    model_config = ConfigDict(extra="forbid")

    email: NormalizedEmail
    password: str = Field(min_length=8, max_length=128)


class PublicUser(BaseModel):
    """A user as the API shows it: never the password hash (SRS §4.3)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    role: Literal["customer", "admin"]
    created_at: datetime


class RegisterResponse(BaseModel):
    """Body of a successful registration: the new user, and no token."""

    user: PublicUser
