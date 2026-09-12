$ErrorActionPreference = "Stop"
uv --cache-dir .uv-cache sync --extra dev --extra package
uv --cache-dir .uv-cache run pyinstaller --noconfirm --clean --windowed --onefile `
  --name "OT-Toolkit" `
  --collect-data ot_toolkit_backend `
  --workpath "frontend/.pyinstaller" `
  --distpath "frontend/dist" `
  --specpath "frontend" `
  "frontend/run_ot_toolkit.py"
Write-Host "Standalone application created at frontend/dist/OT-Toolkit.exe"
