from sqlalchemy.orm import Session

from app.models import Vehicle
from app.schemas.vehicles import VehicleCreate


def create_vehicle(db: Session, data: VehicleCreate) -> Vehicle:
    """Store a new vehicle; the database assigns its id and timestamps."""
    vehicle = Vehicle(**data.model_dump())
    db.add(vehicle)
    db.flush()
    return vehicle
