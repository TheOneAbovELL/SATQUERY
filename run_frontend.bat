@echo off
echo =======================================================
echo Starting SatQuery AI Frontend
echo =======================================================

cd frontend

echo Verifying dependencies...
call npm install

echo.
echo Starting Next.js development server...
call npm run dev
