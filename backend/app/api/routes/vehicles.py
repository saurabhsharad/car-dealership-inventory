from typing import Annotated

from fastapi import APIRouter, Path, Query, status

from app.api.dependencies import AdminUser, CurrentUser
from app.db.session import DbSession
from app.schemas.vehicles import (
    VehicleCreate,
    VehicleOut,
    VehicleSearch,
    VehicleUpdate,
)
from app.services.vehicles import (
    create_vehicle,
    delete_vehicle,
    list_vehicles,
    purchase_vehicle,
    search_vehicles,
    update_vehicle,
)

router = APIRouter(prefix="/vehicles", tags=["vehicles"])

VehicleId = Annotated[int, Path(gt=0)]


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


@router.put("/{vehicle_id}", response_model=VehicleOut)
def update(
    vehicle_id: VehicleId, body: VehicleUpdate, db: DbSession, admin: AdminUser
) -> VehicleOut:
    """Replace a vehicle's details; stock is unchanged (FR-VEH-006, admin only)."""
    return VehicleOut.model_validate(update_vehicle(db, vehicle_id, body))


@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(vehicle_id: VehicleId, db: DbSession, admin: AdminUser) -> None:
    """Remove a vehicle permanently (FR-VEH-007, admin only)."""
    delete_vehicle(db, vehicle_id)


@router.post("/{vehicle_id}/purchase", response_model=VehicleOut)
def purchase(vehicle_id: VehicleId, db: DbSession, user: CurrentUser) -> VehicleOut:
    """Buy one unit of a vehicle (FR-INV-001, any logged-in user)."""
    return VehicleOut.model_validate(purchase_vehicle(db, vehicle_id))
