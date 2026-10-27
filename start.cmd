@echo off
rem Windows: starts the trainer API (:8710), the clinic, booking and payouts APIs (:8711-:8713) and the dashboard (:5173).
rem Press Ctrl+C to stop everything.
cd /d "%~dp0"
if not exist "node_modules" goto needsetup
if not exist "frontend\node_modules" goto needsetup
if not exist ".venv" goto needsetup
set TRAINER_OPEN_BROWSER=1
call npm.cmd run dev
exit /b %errorlevel%

:needsetup
echo Dependencies are missing. Run setup.cmd first.
pause
exit /b 1
