@echo off
rem Windows: installs Python (via uv), all dependencies, and your exercise working copies.
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\setup.ps1"
if errorlevel 1 (
  echo.
  echo Setup failed - see the messages above.
  pause
  exit /b 1
)
