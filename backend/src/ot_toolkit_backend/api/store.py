from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from threading import RLock

from ..services import MockToolkitService


@dataclass(frozen=True)
class UserRecord:
    username: str
    password_hash: str


@dataclass(frozen=True)
class TokenRecord:
    username: str
    expires_at: datetime


class InMemoryStore:
    """Process-local API state seeded with the bundled reference service."""

    token_lifetime = timedelta(hours=8)

    def __init__(self, service: MockToolkitService | None = None) -> None:
        self.service = service or MockToolkitService()
        self._users: dict[str, UserRecord] = {}
        self._tokens: dict[str, TokenRecord] = {}
        self._favorites: dict[str, set[str]] = {}
        self._lock = RLock()

    @staticmethod
    def normalize_username(username: str) -> str:
        return username.strip().casefold()

    def add_user(self, username: str, password_hash: str) -> UserRecord:
        normalized = self.normalize_username(username)
        with self._lock:
            if normalized in self._users:
                raise ValueError("Username is already registered.")
            record = UserRecord(normalized, password_hash)
            self._users[normalized] = record
            self._favorites[normalized] = set()
            return record

    def get_user(self, username: str) -> UserRecord | None:
        with self._lock:
            return self._users.get(self.normalize_username(username))

    def issue_token(self, username: str) -> tuple[str, int]:
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(UTC) + self.token_lifetime
        with self._lock:
            self._tokens[token] = TokenRecord(self.normalize_username(username), expires_at)
        return token, int(self.token_lifetime.total_seconds())

    def username_for_token(self, token: str) -> str | None:
        with self._lock:
            record = self._tokens.get(token)
            if record is None:
                return None
            if record.expires_at <= datetime.now(UTC):
                self._tokens.pop(token, None)
                return None
            return record.username

    def favorites_for(self, username: str) -> list[str]:
        with self._lock:
            return sorted(self._favorites.get(self.normalize_username(username), set()))

    def set_favorite(self, username: str, item_id: str, enabled: bool) -> list[str]:
        normalized = self.normalize_username(username)
        with self._lock:
            values = self._favorites.setdefault(normalized, set())
            values.add(item_id) if enabled else values.discard(item_id)
            return sorted(values)

