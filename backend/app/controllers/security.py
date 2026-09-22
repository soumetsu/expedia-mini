"""Small standard-library helpers for demo account credentials."""

from __future__ import annotations

import hashlib
import hmac
import secrets


HASH_ALGORITHM = "pbkdf2_sha256"
HASH_ITERATIONS = 240_000


def hash_password(password: str, salt: bytes | None = None) -> str:
    """Return a salted password hash suitable for the demo SQLite store."""

    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, HASH_ITERATIONS
    )
    return f"{HASH_ALGORITHM}${HASH_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Compare a password against a stored PBKDF2 hash without plaintext storage."""

    try:
        algorithm, iterations, salt_hex, digest_hex = stored_hash.split("$", 3)
        if algorithm != HASH_ALGORITHM:
            return False
        expected = bytes.fromhex(digest_hex)
        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(iterations),
        )
    except (TypeError, ValueError):
        return False
    return hmac.compare_digest(actual, expected)
