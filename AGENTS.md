# OT Toolkit Agent Guide

## Purpose

This repository contains an offline PySide6 field companion for industrial
communications and OT engineering. Preserve the guiding principle from
`plan.md`: help engineers understand where a technology fits, calculate common
field values, compare technologies, and troubleshoot failures without an
internet connection.

## Repository boundaries

- `frontend/` owns presentation code, desktop composition, UI tests, visual QA
  artifacts, and Windows packaging scripts.
- `backend/` owns models, structured reference data, calculations, persistence,
  search, comparisons, hierarchy logic, and the service implementations.
- Root files are shared project concerns: dependency/build configuration,
  lockfile, product plan, contributor guidance, and repository documentation.
- Do not move generated `.venv`, `.uv-cache`, `build`, or `dist` content into
  either source tree.

## Architecture rules

- `ToolkitService` in
  `backend/src/ot_toolkit_backend/services/base.py` is the only backend boundary
  available to UI widgets.
- UI modules may import backend DTOs/models and the `ToolkitService` contract.
  They must not import backend calculators, JSON data loaders, filesystem
  persistence, or concrete service implementations.
- The frontend composition root may construct `MockToolkitService` and inject it
  into `MainWindow`.
- Every new calculation, search, persistence operation, or data lookup must be
  exposed through `ToolkitService`, implemented by `MockToolkitService`, and
  called through that interface by the frontend.
- Backend modules must not import PySide6 or frontend packages.
- Keep the application fully usable offline. Do not add runtime API calls,
  telemetry, remote fonts, or CDN assets for core features.
- Connectivity commands are informational output only and must never be
  executed by the application.

## Reference content

- Store protocol and standards content as curated JSON under
  `backend/src/ot_toolkit_backend/data/`; do not generate it dynamically at
  runtime.
- Keep technology IDs stable because relationships and favorites depend on
  them.
- Add standards bodies and source URLs when introducing or materially changing
  a technology entry.
- Update schema checks and search coverage when adding fields or data types.

## Tests and validation

- Backend unit tests belong in `backend/tests/`.
- Frontend and UI smoke tests belong in `frontend/tests/`.
- Add tests for every calculator edge case and every new service method.
- From the repository root, install and test with:

  ```powershell
  uv sync --extra dev
  uv run pytest
  ```

- Render visual QA screenshots after meaningful UI changes:

  ```powershell
  uv run python frontend/scripts/render_preview.py
  ```

- Build the standalone Windows executable with:

  ```powershell
  powershell -ExecutionPolicy Bypass -File frontend/scripts/build_windows.ps1
  ```

## Change discipline

- Preserve unrelated user changes and keep commits focused.
- Update `README.md` when commands, directory layout, or packaging behavior
  changes.
- Never commit secrets, local favorites, virtual environments, build output, or
  caches.
- Keep visible UI copy concise, practical, and written for automation and OT
  engineers.
