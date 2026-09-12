# Industrial Communications & OT Toolkit

An offline Windows desktop field companion for automation and OT engineers. It combines a curated communications reference, hierarchy and comparison tools, Modbus utilities, data converters, subnet tools, port lookup, troubleshooting guides, and a glossary.

## Run

```powershell
uv sync --extra dev
uv run ot-toolkit
```

The default app uses `MockToolkitService`, a complete local implementation of the service contract. It reads bundled JSON and uses local storage for favorites, so no server, account, or internet connection is required.

## Test

```powershell
uv run pytest
```

## Architecture

- `frontend/` contains the PySide6 desktop interface, launcher, UI smoke tests,
  preview artifacts, and Windows packaging scripts.
- `backend/` contains the service contract, local mock implementation, pure
  engineering calculations, structured reference data, and backend tests.
- `backend/src/ot_toolkit_backend/services/base.py` is the single backend
  boundary used by the frontend.
- `backend/src/ot_toolkit_backend/services/mock.py` is the complete offline
  implementation used by the application and tests.
- `plan.md`, `pyproject.toml`, `uv.lock`, and `AGENTS.md` apply to the complete
  project and remain at the repository root.

To connect a future backend, implement `ToolkitService` and inject it into `MainWindow`; UI code does not need to change.

## Project layout

```text
backend/
  src/ot_toolkit_backend/
    data/          Curated JSON reference content
    services/      Backend boundary and offline implementation
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
