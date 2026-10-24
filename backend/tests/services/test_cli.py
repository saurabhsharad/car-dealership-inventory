import pytest
from sqlalchemy import select

from app.cli import main
from app.models import User

PASSWORD = "s3cure-admin-pass"


@pytest.fixture
def prompted(monkeypatch):
    """Answer the hidden password prompts with the given values, in order."""

    def answer(*replies: str) -> None:
        monkeypatch.delenv("ADMIN_PASSWORD", raising=False)
        queue = iter(replies)
        monkeypatch.setattr("getpass.getpass", lambda prompt="": next(queue))

    return answer


def stored_users(engine) -> list[tuple[str, str]]:
    with engine.connect() as connection:
        return [tuple(row) for row in connection.execute(select(User.email, User.role))]


def create_admin_cli(engine, email: str = "Admin@Example.com") -> int:
    return main(["create-admin", "--email", email], engine=engine)


def test_creates_an_admin_who_can_log_in(committed_db, client, monkeypatch, capsys):
    """T-AUTH-16 / FR-AUTH-008: the new admin can log in with that password."""
    monkeypatch.setenv("ADMIN_PASSWORD", PASSWORD)

    assert create_admin_cli(committed_db) == 0

    assert stored_users(committed_db) == [("admin@example.com", "admin")]
    output = capsys.readouterr()
    assert "Created admin admin@example.com" in output.out
    assert PASSWORD not in output.out + output.err

    login = client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": PASSWORD},
    )
    assert login.status_code == 200
    assert login.json()["user"]["role"] == "admin"


def test_prompts_twice_for_the_password_when_it_is_not_in_the_environment(
    committed_db, prompted
):
    """SRS §2.5: a hidden prompt with confirmation is the interactive path."""
    prompted(PASSWORD, PASSWORD)

    assert create_admin_cli(committed_db) == 0
    assert stored_users(committed_db) == [("admin@example.com", "admin")]


def test_fails_without_changes_when_the_passwords_differ(
    committed_db, prompted, capsys
):
    """FR-AUTH-008: a confirmation mismatch exits non-zero and creates nothing."""
    prompted(PASSWORD, "something-else")

    assert create_admin_cli(committed_db) == 1
    assert stored_users(committed_db) == []
    assert "Passwords do not match." in capsys.readouterr().err


def test_fails_without_changes_when_the_email_exists(committed_db, monkeypatch, capsys):
    """T-AUTH-16: running it again with the same email exits non-zero."""
    monkeypatch.setenv("ADMIN_PASSWORD", PASSWORD)
    assert create_admin_cli(committed_db) == 0
    capsys.readouterr()

    assert create_admin_cli(committed_db, email="admin@EXAMPLE.com") == 1
    assert stored_users(committed_db) == [("admin@example.com", "admin")]
    assert "An account with this email already exists." in capsys.readouterr().err


@pytest.mark.parametrize(
    ("email", "password", "field"),
    [
        ("admin@example.com", "short", "password"),
        ("not-an-email", PASSWORD, "email"),
    ],
)
def test_fails_without_changes_when_the_input_breaks_the_policy(
    committed_db, monkeypatch, capsys, email, password, field
):
    """FR-AUTH-008: the registration rules apply, and the password is not echoed."""
    monkeypatch.setenv("ADMIN_PASSWORD", password)

    assert create_admin_cli(committed_db, email=email) == 1
    assert stored_users(committed_db) == []
    output = capsys.readouterr()
    assert f"{field}:" in output.err
    assert password not in output.out + output.err
