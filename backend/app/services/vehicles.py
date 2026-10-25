from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Vehicle
from app.schemas.vehicles import VehicleCreate

NEWEST_FIRST = (Vehicle.created_at.desc(), Vehicle.id.desc())


def create_vehicle(db: Session, data: VehicleCreate) -> Vehicle:
    """Store a new vehicle; the database assigns its id and timestamps."""
    vehicle = Vehicle(**data.model_dump())
    db.add(vehicle)
    db.flush()
    return vehicle


def list_vehicles(db: Session) -> list[Vehicle]:
    """Every vehicle, zero stock included, newest first (FR-VEH-003)."""
    return list(db.scalars(select(Vehicle).order_by(*NEWEST_FIRST)))
