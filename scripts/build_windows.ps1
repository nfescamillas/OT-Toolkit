$ErrorActionPreference = "Stop"
uv --cache-dir .uv-cache sync --extra dev --extra package
uv --cache-dir .uv-cache run pyinstaller --noconfirm --clean --windowed --onefile `
  --name "OT-Toolkit" `
  --collect-data ot_toolkit `
  "run_ot_toolkit.py"
Write-Host "Standalone application created at dist/OT-Toolkit.exe"
