# Windows setup. Run via setup.cmd (double-click or `.\setup.cmd`), which bypasses the
# PowerShell execution policy for this script only.
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

function Step($message) { Write-Host "`n==> $message" -ForegroundColor Cyan }
function Run($exe, [string[]]$arguments) {
    & $exe @arguments
    if ($LASTEXITCODE -ne 0) { throw "'$exe $($arguments -join ' ')' failed with exit code $LASTEXITCODE" }
}

Step "Checking prerequisites"
$missing = @()
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    $missing += "uv      ->  winget install --id=astral-sh.uv -e"
}
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    $missing += "Node.js ->  winget install --id=OpenJS.NodeJS.LTS -e"
}
if ($missing.Count -gt 0) {
    Write-Host "Missing prerequisites:" -ForegroundColor Red
    $missing | ForEach-Object { Write-Host "  $_" }
    Write-Host "Install them, then open a NEW terminal (so PATH refreshes) and run setup.cmd again."
    exit 1
}
$nodeMajor = [int]((node --version).TrimStart("v").Split(".")[0])
if ($nodeMajor -lt 20) {
    Write-Host "Node.js 20+ is required (found $(node --version)). winget upgrade OpenJS.NodeJS.LTS" -ForegroundColor Red
    exit 1
}
Write-Host "uv $(uv --version), node $(node --version)"

Step "Installing Python 3.12 + backend dependencies (uv sync)"
Run "uv" @("sync")

Step "Installing root npm tools"
Run "npm.cmd" @("install", "--no-fund", "--no-audit")

Step "Installing frontend dependencies"
Run "npm.cmd" @("install", "--prefix", "frontend", "--no-fund", "--no-audit")

Step "Creating your exercise working copies"
Run "uv" @("run", "python", "scripts/workspace.py", "init")

Step "Self-check"
Run "uv" @("run", "pytest", "backend/tests/trainer", "-q")

Write-Host "`nSetup complete. Start everything with:  .\start.cmd" -ForegroundColor Green
