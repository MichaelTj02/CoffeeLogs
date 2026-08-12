import hashlib
import secrets
from datetime import timedelta

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

COOKIE_NAME = "coffeelogs_session"
SESSION_TTL = timedelta(days=30)

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    # argon2's verify() raises on a mismatch instead of returning False.
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


_DUMMY_HASH = _hasher.hash("dummy password, never a real credential")


def burn_dummy_verification() -> None:
    # Login on an unknown email has no hash to check, so it would answer far faster than a
    # wrong password and leak which addresses are registered. Spend the time anyway.
    verify_password("not the dummy password", _DUMMY_HASH)
