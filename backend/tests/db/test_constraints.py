from decimal import Decimal

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import User, Vehicle

INSERT_VEHICLE = text(
    "INSERT INTO vehicles (make, model, category, price, quantity_in_stock) "
    "VALUES (:make, :model, :category, :price, :stock) RETURNING id"
)
INSERT_USER = text(
    "INSERT INTO users (email, password_hash, role) VALUES (:email, 'hash', :role)"
)
VALID_VEHICLE = {
    "make": "Toyota",
    "model": "Corolla",
    "category": "Sedan",
    "price": Decimal("24999.00"),
    "stock": 3,
}


def violated_constraint(error: pytest.ExceptionInfo[IntegrityError]) -> str:
    """Name of the constraint PostgreSQL reported for an integrity error."""
    return error.value.orig.diag.constraint_name


@pytest.mark.parametrize(
    ("field", "value", "constraint"),
    [
        ("price", Decimal("0"), "ck_vehicles_price_positive"),
        ("price", Decimal("-5.00"), "ck_vehicles_price_positive"),
        ("make", "   ", "ck_vehicles_make_not_blank"),
        ("model", "", "ck_vehicles_model_not_blank"),
        ("category", " ", "ck_vehicles_category_not_blank"),
        ("stock", -1, "ck_vehicles_stock_non_negative"),
    ],
)
def test_database_rejects_invalid_vehicle_insert(db_session, field, value, constraint):
    """T-DB-02 / NFR-INT-001: raw inserts that break a rule are rejected."""
    with pytest.raises(IntegrityError) as error:
        db_session.execute(INSERT_VEHICLE, {**VALID_VEHICLE, field: value})

    assert violated_constraint(error) == constraint


def test_database_rejects_stock_update_below_zero(db_session):
    """T-DB-03 / FR-INV-003: stock can never be set negative, even by raw SQL."""
    vehicle_id = db_session.execute(INSERT_VEHICLE, VALID_VEHICLE).scalar_one()

    with pytest.raises(IntegrityError) as error:
        db_session.execute(
            text("UPDATE vehicles SET quantity_in_stock = -1 WHERE id = :id"),
            {"id": vehicle_id},
        )

    assert violated_constraint(error) == "ck_vehicles_stock_non_negative"


def test_database_rejects_unknown_role(db_session):
    """T-DB-04: only the customer and admin roles can be stored."""
    with pytest.raises(IntegrityError) as error:
        db_session.execute(INSERT_USER, {"email": "a@x.com", "role": "superuser"})

    assert violated_constraint(error) == "ck_users_role_allowed"


def test_database_rejects_duplicate_email(db_session):
    """T-DB-04 / FR-AUTH-002: an email can be registered only once."""
    db_session.execute(INSERT_USER, {"email": "a@x.com", "role": "customer"})

    with pytest.raises(IntegrityError) as error:
        db_session.execute(INSERT_USER, {"email": "a@x.com", "role": "customer"})

    assert violated_constraint(error) == "uq_users_email"


def test_database_rejects_email_that_is_not_lower_case(db_session):
    """SRS §5.1: emails are stored lower-case."""
    with pytest.raises(IntegrityError) as error:
        db_session.execute(INSERT_USER, {"email": "A@x.com", "role": "customer"})

    assert violated_constraint(error) == "ck_users_email_lowercase"


def test_committed_vehicle_is_readable_from_a_new_session(db_session):
    """T-DB-05: a committed vehicle is stored, with exact price and defaults."""
    vehicle = Vehicle(
        make="Toyota", model="Corolla", category="Sedan", price=Decimal("24999.10")
    )
    db_session.add(vehicle)
    db_session.commit()

    with Session(bind=db_session.connection()) as other_session:
        stored = other_session.get(Vehicle, vehicle.id)

        assert stored is not None
        assert stored is not vehicle
        assert stored.price == Decimal("24999.10")
        assert stored.quantity_in_stock == 0
        assert stored.created_at is not None


def test_each_test_starts_with_empty_tables(db_session):
    """Rows written by earlier tests were rolled back (NFR-TST-002)."""
    assert db_session.scalar(select(func.count()).select_from(Vehicle)) == 0
    assert db_session.scalar(select(func.count()).select_from(User)) == 0
