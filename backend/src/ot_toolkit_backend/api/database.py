from __future__ import annotations

import os
from typing import Any

from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


DATABASE_URL_ENV = "OT_TOOLKIT_DATABASE_URL"
DEFAULT_DATABASE_URL = "sqlite+pysqlite:///./ot_toolkit.db"


def database_url_from_environment() -> str:
    return os.environ.get(DATABASE_URL_ENV, DEFAULT_DATABASE_URL)


def create_database_engine(database_url: str) -> Engine:
    """Create an engine while keeping dialect-specific settings at the edge."""
    url = make_url(database_url)
    options: dict[str, Any] = {"pool_pre_ping": True}
    if url.get_backend_name() == "sqlite":
        options["connect_args"] = {"check_same_thread": False}
        if url.database in {None, "", ":memory:"}:
            options["poolclass"] = StaticPool
    return create_engine(url, **options)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
