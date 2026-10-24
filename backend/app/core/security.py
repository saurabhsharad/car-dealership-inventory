from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

password_hasher = PasswordHash((Argon2Hasher(),))


def hash_password(password: str) -> str:
    """Hash a password with Argon2id (FR-AUTH-003, NFR-SEC-001)."""
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Check a password against a stored Argon2id hash."""
    return password_hasher.verify(password, password_hash)
