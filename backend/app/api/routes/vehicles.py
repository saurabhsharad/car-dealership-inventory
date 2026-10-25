from typing import Annotated

from fastapi import APIRouter, Query, status

from app.api.dependencies import AdminUser, CurrentUser
from app.db.session import DbSession
from app.schemas.vehicles import VehicleCreate, VehicleOut, VehicleSearch
from app.services.vehicles import create_vehicle, list_vehicles, search_vehicles

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=VehicleOut)
def create(body: VehicleCreate, db: DbSession, admin: AdminUser) -> VehicleOut:
    """Add a vehicle to the inventory (FR-VEH-001, admin only)."""
    return VehicleOut.model_validate(create_vehicle(db, body))


@router.get("", response_model=list[VehicleOut])
def list_all(db: DbSession, user: CurrentUser) -> list[VehicleOut]:
    """Every vehicle, newest first (FR-VEH-003)."""
    return [VehicleOut.model_validate(vehicle) for vehicle in list_vehicles(db)]


# Registered before any /{id} route so "search" is never read as an id (§4.4).
@router.get("/search", response_model=list[VehicleOut])
def search(
    filters: Annotated[VehicleSearch, Query()], db: DbSession, user: CurrentUser
) -> list[VehicleOut]:
    """Vehicles matching every given filter, newest first (FR-VEH-004)."""
    return [VehicleOut.model_validate(v) for v in search_vehicles(db, filters)]
