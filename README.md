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

- `ui/` contains presentation code and calls only `ToolkitService`.
- `services/base.py` is the single backend boundary.
- `services/mock.py` is the offline implementation used by the application and tests.
- `engineering.py` contains pure calculations reached through the service.
- `data/` contains curated, schema-validated JSON reference data.

To connect a future backend, implement `ToolkitService` and inject it into `MainWindow`; UI code does not need to change.

