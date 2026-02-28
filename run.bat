@echo off
echo Starting SwasthyaSarthi Backend and Frontend...
echo.

echo [1/2] Starting Backend on port 8000...
start "SwasthyaSarthi Backend" cmd /k "cd /d c:\Users\soham\OneDrive\Desktop\SwasthyaSarthi && call venv\Scripts\activate.bat && uvicorn backend.main:app --reload --port 8000"

timeout /t 3 /nobreak >nul

echo [2/2] Starting Frontend on port 3000...
start "SwasthyaSarthi Frontend" cmd /k "cd /d c:\Users\soham\OneDrive\Desktop\SwasthyaSarthi\frontend && npm run dev"

echo.
echo Both servers are starting!
echo - Backend: http://localhost:8000
echo - Frontend: http://localhost:3000
echo.
pause
