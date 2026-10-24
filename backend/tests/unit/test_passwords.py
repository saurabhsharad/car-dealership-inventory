from app.core.security import hash_password, verify_password

PASSWORD = "s3cure-pass"


def test_hash_is_argon2id_and_never_contains_the_password():
    """FR-AUTH-003 / NFR-SEC-001: passwords are stored as Argon2id hashes."""
    password_hash = hash_password(PASSWORD)

    assert password_hash.startswith("$argon2id$")
    assert PASSWORD not in password_hash


def test_same_password_hashes_differently_each_time():
    """Each hash has its own random salt, so equal passwords look different."""
    assert hash_password(PASSWORD) != hash_password(PASSWORD)


def test_verify_accepts_the_right_password():
    """T-AUTH-06: the correct password matches its hash."""
    assert verify_password(PASSWORD, hash_password(PASSWORD)) is True


def test_verify_rejects_a_wrong_password():
    """T-AUTH-06: any other password does not."""
    assert verify_password("wrong-pass", hash_password(PASSWORD)) is False
