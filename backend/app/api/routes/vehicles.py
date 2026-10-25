from fastapi import APIRouter, status

from app.api.dependencies import AdminUser
from app.db.session import DbSession
from app.schemas.vehicles import VehicleCreate, VehicleOut
from app.services.vehicles import create_vehicle

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=VehicleOut)
def create(body: VehicleCreate, db: DbSession, admin: AdminUser) -> VehicleOut:
    """Add a vehicle to the inventory (FR-VEH-001, admin only)."""
    return VehicleOut.model_validate(create_vehicle(db, body))
