@echo off
echo =======================================================
echo Starting SatQuery AI Backend
echo =======================================================

cd backend

echo Activating environment...
REM If the user has a virtual env, they should activate it here.
REM We assume Python is in PATH as per Windows standard.

echo.
echo Starting FastAPI server...
python -m uvicorn main:app --port 8000 --reload
