from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Vehicle
from app.schemas.vehicles import VehicleCreate, VehicleSearch, VehicleUpdate
from app.services.errors import VehicleNotFoundError

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


def search_vehicles(db: Session, filters: VehicleSearch) -> list[Vehicle]:
    """Vehicles matching every given filter, newest first (FR-VEH-004).

    Text filters are case-insensitive substrings with %, _ and the escape
    character matched literally; price bounds are inclusive.
    """
    query = select(Vehicle).order_by(*NEWEST_FIRST)
    for column, text in [
        (Vehicle.make, filters.make),
        (Vehicle.model, filters.model),
        (Vehicle.category, filters.category),
    ]:
        if text is not None:
            query = query.where(column.icontains(text, autoescape=True))
    if filters.min_price is not None:
        query = query.where(Vehicle.price >= filters.min_price)
    if filters.max_price is not None:
        query = query.where(Vehicle.price <= filters.max_price)
    return list(db.scalars(query))


def update_vehicle(db: Session, vehicle_id: int, data: VehicleUpdate) -> Vehicle:
    """Replace make, model, category and price; stock is untouched (FR-VEH-006)."""
    vehicle = db.get(Vehicle, vehicle_id)
    if vehicle is None:
        raise VehicleNotFoundError
    for field, value in data.model_dump().items():
        setattr(vehicle, field, value)
    db.flush()
    return vehicle
