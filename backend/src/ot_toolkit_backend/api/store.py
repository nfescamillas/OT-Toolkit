from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError

from ..services import MockToolkitService
from .database import (
    create_database_engine,
    create_session_factory,
    database_url_from_environment,
)
from .tables import FavoriteTable, OrmBase, TokenTable, UserTable


@dataclass(frozen=True)
class UserRecord:
    username: str
    password_hash: str


class DatabaseStore:
    """Database-backed API state with a dialect-neutral repository interface."""

    token_lifetime = timedelta(hours=8)

    def __init__(
        self,
        database_url: str | None = None,
        service: MockToolkitService | None = None,
    ) -> None:
        self.service = service or MockToolkitService()
        self.database_url = database_url or database_url_from_environment()
        self.engine = create_database_engine(self.database_url)
        self._sessions = create_session_factory(self.engine)
        OrmBase.metadata.create_all(self.engine)

    def close(self) -> None:
        self.engine.dispose()

    @staticmethod
    def normalize_username(username: str) -> str:
        return username.strip().casefold()

    @staticmethod
    def _token_digest(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)

    def add_user(self, username: str, password_hash: str) -> UserRecord:
        normalized = self.normalize_username(username)
        try:
            with self._sessions.begin() as session:
                if session.get(UserTable, normalized) is not None:
                    raise ValueError("Username is already registered.")
                session.add(UserTable(username=normalized, password_hash=password_hash))
        except IntegrityError as exc:
            raise ValueError("Username is already registered.") from exc
        return UserRecord(normalized, password_hash)

    def get_user(self, username: str) -> UserRecord | None:
        normalized = self.normalize_username(username)
        with self._sessions() as session:
            row = session.get(UserTable, normalized)
            return UserRecord(row.username, row.password_hash) if row is not None else None

    def issue_token(self, username: str) -> tuple[str, int]:
        token = secrets.token_urlsafe(32)
        row = TokenTable(
            token_digest=self._token_digest(token),
            username=self.normalize_username(username),
            expires_at=datetime.now(UTC) + self.token_lifetime,
        )
        with self._sessions.begin() as session:
            session.add(row)
        return token, int(self.token_lifetime.total_seconds())

    def username_for_token(self, token: str) -> str | None:
        digest = self._token_digest(token)
        with self._sessions.begin() as session:
            row = session.get(TokenTable, digest)
            if row is None:
                return None
            if self._as_utc(row.expires_at) <= datetime.now(UTC):
                session.delete(row)
                return None
            return row.username

    def revoke_tokens(self, username: str) -> None:
        with self._sessions.begin() as session:
            session.execute(
                delete(TokenTable).where(TokenTable.username == self.normalize_username(username))
            )

    def favorites_for(self, username: str) -> list[str]:
        statement = (
            select(FavoriteTable.item_id)
            .where(FavoriteTable.username == self.normalize_username(username))
            .order_by(FavoriteTable.item_id)
        )
        with self._sessions() as session:
            return list(session.scalars(statement))

    def set_favorite(self, username: str, item_id: str, enabled: bool) -> list[str]:
        normalized = self.normalize_username(username)
        identity = (normalized, item_id)
        with self._sessions.begin() as session:
            row = session.get(FavoriteTable, identity)
            if enabled and row is None:
                session.add(FavoriteTable(username=normalized, item_id=item_id))
            elif not enabled and row is not None:
                session.delete(row)
        return self.favorites_for(normalized)
