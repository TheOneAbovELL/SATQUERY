@echo off
echo =======================================================
echo SatQuery AI SIH 2026 - Demo Launcher
echo =======================================================

echo 1. Launching Backend...
start cmd /k "run_backend.bat"

echo 2. Waiting 5 seconds for backend to initialize...
timeout /t 5 /nobreak >nul

echo 3. Launching Frontend...
start cmd /k "run_frontend.bat"

echo.
echo Demo is running!
echo Frontend: http://localhost:3000
echo Backend API: http://localhost:8000/docs
