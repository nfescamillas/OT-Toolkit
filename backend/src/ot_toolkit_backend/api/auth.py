from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash

from .store import InMemoryStore, UserRecord


password_hash = PasswordHash.recommended()
bearer = HTTPBearer(auto_error=False, scheme_name="bearerAuth")


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)


def get_store(request: Request) -> InMemoryStore:
    return request.app.state.store


def require_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    store: InMemoryStore = Depends(get_store),
) -> UserRecord:
    if credentials is None or credentials.scheme.casefold() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A valid bearer token is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    username = store.username_for_token(credentials.credentials)
    user = store.get_user(username) if username else None
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The bearer token is invalid or expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

