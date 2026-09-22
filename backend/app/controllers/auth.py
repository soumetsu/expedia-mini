"""Demo account workflows and process-local bearer sessions."""

from __future__ import annotations

import secrets
from pathlib import Path

from ..models import AuthUserResponse
from .database import (
    DATABASE_PATH,
    AccountConflictError,
    AuthenticationError,
    DataAccessError,
    authenticate_user,
    create_user_account,
)


_sessions: dict[str, str] = {}


def register_account(
    username: str,
    password: str,
    email: str | None = None,
    database_path: Path = DATABASE_PATH,
) -> tuple[str, AuthUserResponse]:
    user = create_user_account(username, password, email, database_path)
    token = secrets.token_urlsafe(32)
    _sessions[token] = user.user_id
    return token, user


def login_account(
    username: str, password: str, database_path: Path = DATABASE_PATH
) -> tuple[str, AuthUserResponse]:
    user = authenticate_user(username, password, database_path)
    token = secrets.token_urlsafe(32)
    _sessions[token] = user.user_id
    return token, user


def user_id_for_token(token: str | None) -> str:
    if not token or token not in _sessions:
        raise AuthenticationError("Sign in to continue.")
    return _sessions[token]


def logout_account(token: str | None) -> None:
    if token:
        _sessions.pop(token, None)


__all__ = [
    "AccountConflictError",
    "AuthenticationError",
    "DataAccessError",
    "login_account",
    "logout_account",
    "register_account",
    "user_id_for_token",
]
