# Industrial Communications & OT Toolkit

An offline Windows desktop field companion for automation and OT engineers. It combines a curated communications reference, hierarchy and comparison tools, Modbus utilities, data converters, subnet tools, port lookup, troubleshooting guides, and a glossary.

## Run

With GNU Make installed, set up and start the backend and desktop app with:

```powershell
make setup
make dev
```

Run `make help` to list all shortcuts. `make dev` starts both the desktop app
and FastAPI backend. Use `make api` and `make run` in separate terminals when
you want to manage the processes independently.

The equivalent commands without Make are run in two terminals:

```powershell
# Terminal 1
uv sync --extra dev
uv run ot-toolkit-api

# Terminal 2
uv run ot-toolkit
```

The frontend uses `HttpToolkitService` for every backend operation. By default,
it connects to `http://127.0.0.1:8000/api/v1` and signs in with the seeded demo
account for authenticated favorites. The backend uses bundled data and remains
fully usable without an internet connection.

Runtime configuration can be overridden without changing source code:

| Variable | Default | Purpose |
| --- | --- | --- |
| `OT_TOOLKIT_API_URL` | `http://127.0.0.1:8000/api/v1` | Backend API base URL |
| `OT_TOOLKIT_USERNAME` | `demo` | Username used for favorites |
| `OT_TOOLKIT_PASSWORD` | `demo-password` | Password used to obtain bearer tokens |
| `OT_TOOLKIT_DATABASE_URL` | `sqlite+pysqlite:///./ot_toolkit.db` | SQLAlchemy database connection URL |

## Test

```powershell
make test
```

Or run pytest directly:

```powershell
uv run pytest
```

## FastAPI backend

The HTTP backend implements the root `openapi.yaml` contract with SQLAlchemy
persistence. Start it from the repository root:

```powershell
uv sync --extra dev
uv run ot-toolkit-api
```

Interactive documentation is available at
`http://127.0.0.1:8000/api/v1/docs`. Reference, discovery, and calculation
routes are public. Favorites require a bearer token from `POST
/api/v1/auth/token`.

Development seed account:

```text
username: demo
password: demo-password
```

Passwords are held only as Argon2 hashes, tokens are opaque and expire after
eight hours, and only token digests are stored. Users and favorites persist
across restarts. The frontend keeps bearer tokens only in memory and
automatically signs in again when a token expires.

SQLite is used by default and creates `ot_toolkit.db` in the repository root.
To choose another database, set a SQLAlchemy URL before starting the server:

```powershell
$env:OT_TOOLKIT_DATABASE_URL = "sqlite+pysqlite:///./my-ot-toolkit.db"
uv run ot-toolkit-api
```

The persistence layer does not issue dialect-specific queries. A future
PostgreSQL deployment can use a PostgreSQL SQLAlchemy URL after its selected
DBAPI driver is added to the environment.

## Architecture

- `frontend/` contains the PySide6 desktop interface, launcher, UI smoke tests,
  preview artifacts, and Windows packaging scripts.
- `backend/` contains the service contract, local mock implementation, pure
  engineering calculations, structured reference data, and backend tests.
- `backend/src/ot_toolkit_backend/services/base.py` is the single backend
  boundary used by the frontend.
- `backend/src/ot_toolkit_backend/services/http.py` is the real HTTP client used
  by the desktop composition root.
- `backend/src/ot_toolkit_backend/services/mock.py` is the complete offline
  implementation used behind FastAPI and in isolated tests.
- `backend/src/ot_toolkit_backend/api/database.py` owns engine configuration;
  `tables.py` defines the portable ORM schema, and `store.py` owns persistence
  queries.
- `plan.md`, `pyproject.toml`, `uv.lock`, and `AGENTS.md` apply to the complete
  project and remain at the repository root.

UI widgets remain transport-agnostic: they receive `ToolkitService` and do not
make HTTP requests directly.

## Project layout

```text
backend/
  src/ot_toolkit_backend/
    data/          Curated JSON reference content
    services/      Backend boundary, HTTP client, and seeded implementation
    engineering.py Pure calculators and decoders
    models.py      Shared data-transfer models
  tests/
frontend/
  src/ot_toolkit_frontend/
    app.py         Desktop composition root
    ui/            PySide6 interface
  tests/
  scripts/         Preview and Windows build scripts
  artifacts/       Visual QA renders
```

## Build the Windows executable

From the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File frontend/scripts/build_windows.ps1
```

The executable is written to `frontend/dist/OT-Toolkit.exe`.
