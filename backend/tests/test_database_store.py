from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import inspect, select

from ot_toolkit_backend.api.auth import hash_password
from ot_toolkit_backend.api.store import DatabaseStore
from ot_toolkit_backend.api.tables import TokenTable


def sqlite_url(path: Path) -> str:
    return f"sqlite+pysqlite:///{path.as_posix()}"


def test_database_store_creates_portable_schema_and_persists_state(tmp_path: Path):
    database_url = sqlite_url(tmp_path / "persistent.db")
    first = DatabaseStore(database_url)
    first.add_user("Field.Engineer", hash_password("correct-horse-battery"))
    first.set_favorite("field.engineer", "profinet", True)
    raw_token, _ = first.issue_token("field.engineer")
    first.close()

    second = DatabaseStore(database_url)
    assert set(inspect(second.engine).get_table_names()) == {"favorites", "tokens", "users"}
    assert second.get_user("FIELD.ENGINEER").username == "field.engineer"
    assert second.favorites_for("field.engineer") == ["profinet"]
    assert second.username_for_token(raw_token) == "field.engineer"

    with second._sessions() as session:
        stored_digests = list(session.scalars(select(TokenTable.token_digest)))
    assert raw_token not in stored_digests
    assert DatabaseStore._token_digest(raw_token) in stored_digests
    second.close()


def test_expired_database_token_is_rejected_and_removed():
    store = DatabaseStore("sqlite+pysqlite:///:memory:")
    store.add_user("engineer", hash_password("correct-horse-battery"))
    raw_token = "expired-token"
    with store._sessions.begin() as session:
        session.add(
            TokenTable(
                token_digest=DatabaseStore._token_digest(raw_token),
                username="engineer",
                expires_at=datetime.now(UTC) - timedelta(seconds=1),
            )
        )

    assert store.username_for_token(raw_token) is None
    with store._sessions() as session:
        assert session.get(TokenTable, DatabaseStore._token_digest(raw_token)) is None
    store.close()


def test_database_url_comes_from_environment(monkeypatch, tmp_path: Path):
    configured_url = sqlite_url(tmp_path / "configured.db")
    monkeypatch.setenv("OT_TOOLKIT_DATABASE_URL", configured_url)

    store = DatabaseStore()
    assert store.database_url == configured_url
    assert store.engine.url.get_backend_name() == "sqlite"
    store.close()
