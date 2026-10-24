from sqlalchemy import Inspector, inspect


def constraint_names(inspector: Inspector, table: str) -> set[str]:
    """Names of the primary key, unique and check constraints on a table."""
    if not inspector.has_table(table):
        return set()

    names = {inspector.get_pk_constraint(table)["name"]}
    names |= {c["name"] for c in inspector.get_unique_constraints(table)}
    names |= {c["name"] for c in inspector.get_check_constraints(table)}
    return names


def test_migrations_create_users_and_vehicles_tables(db_engine):
    """T-DB-01: alembic upgrade head creates both MVP tables."""
    tables = set(inspect(db_engine).get_table_names())

    assert {"users", "vehicles"} <= tables


def test_migrations_create_every_named_constraint(db_engine):
    """T-DB-01 / SRS §5.1: every constraint exists under its agreed name."""
    inspector = inspect(db_engine)

    assert constraint_names(inspector, "users") == {
        "pk_users",
        "uq_users_email",
        "ck_users_email_lowercase",
        "ck_users_role_allowed",
    }
    assert constraint_names(inspector, "vehicles") == {
        "pk_vehicles",
        "ck_vehicles_make_not_blank",
        "ck_vehicles_model_not_blank",
        "ck_vehicles_category_not_blank",
        "ck_vehicles_price_positive",
        "ck_vehicles_stock_non_negative",
    }
