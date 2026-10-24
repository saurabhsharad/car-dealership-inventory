"""Command-line tools for operators, run as python -m app.cli <command>.

create-admin is the only way to create an admin account (SRS §2.5, A-03).
"""

import argparse
import getpass
import os
import sys

from pydantic import ValidationError
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from app.db.session import get_engine
from app.schemas.auth import RegisterRequest
from app.services.auth import create_admin
from app.services.errors import EmailAlreadyRegisteredError


class CommandError(Exception):
    """A problem to report to the operator before exiting with status 1."""


def read_password() -> str:
    """ADMIN_PASSWORD if set, otherwise a hidden prompt typed twice."""
    password = os.environ.get("ADMIN_PASSWORD")
    if password is not None:
        return password
    password = getpass.getpass("Password: ")
    if getpass.getpass("Confirm password: ") != password:
        raise CommandError("Passwords do not match.")
    return password


def validated_credentials(email: str, password: str) -> RegisterRequest:
    """Apply the registration rules; report fields, never the values."""
    try:
        return RegisterRequest(email=email, password=password)
    except ValidationError as error:
        problems = "; ".join(f"{e['loc'][0]}: {e['msg']}" for e in error.errors())
        raise CommandError(problems) from None


def create_admin_command(email: str, engine: Engine) -> str:
    """Create the admin in its own committed transaction and return its email."""
    credentials = validated_credentials(email, read_password())
    with Session(engine) as session, session.begin():
        try:
            admin = create_admin(session, credentials.email, credentials.password)
        except EmailAlreadyRegisteredError:
            raise CommandError("An account with this email already exists.") from None
        return admin.email


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create-admin", help="create an admin account")
    create.add_argument("--email", required=True)
    return parser


def main(argv: list[str] | None = None, *, engine: Engine | None = None) -> int:
    """Run a command and return the process exit status."""
    args = build_parser().parse_args(argv)
    try:
        email = create_admin_command(args.email, engine or get_engine())
    except CommandError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    print(f"Created admin {email}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
