$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"

Write-Host "Starting EasyPDF backend on http://127.0.0.1:8000"
Start-Process powershell -WindowStyle Hidden -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd `"$backend`"; conda run -n lang-chain01 python -m uvicorn app.main:app --reload --port 8000"
)

Write-Host "Starting EasyPDF frontend on http://127.0.0.1:5173"
Start-Process powershell -WindowStyle Hidden -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd `"$frontend`"; npm.cmd run dev"
)
