@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo 🏛️ NYAYASHASTRA - Starting Docker Environment...
echo ===================================================

:: Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not running. Please start Docker Desktop and try again.
    pause
    exit /b 1
)

:: Build and start the containers in detached mode
echo [INFO] Running docker compose up...
docker compose up -d --build

if %errorlevel% neq 0 (
    echo [ERROR] Failed to start Docker Compose services.
    pause
    exit /b 1
)

echo [INFO] Waiting for backend to initialize and database to seed...
echo [INFO] This might take a moment on first startup.

:: Loop to wait for the backend to be healthy
set "health_url=http://localhost:8000/health"
set /a attempt=1
set /a max_attempts=30

:check_health
curl -s -f !health_url! >nul 2>&1
if %errorlevel% equ 0 (
    echo.
    echo [SUCCESS] Backend is healthy and ready!
    goto open_browser
)

:: Print progress dot
<nul set /p "=. "
timeout /t 2 >nul
set /a attempt+=1

if !attempt! gtr !max_attempts! (
    echo.
    echo [WARNING] Backend did not respond within time limit.
    echo Opening browser anyway.
) else (
    goto check_health
)

:open_browser
echo [INFO] Opening NYAYASHASTRA in default browser...
start http://localhost:5173
echo.
echo [SUCCESS] NYAYASHASTRA is running!
echo - Frontend: http://localhost:5173
echo - Backend API: http://localhost:8000
echo - API Docs: http://localhost:8000/docs
echo.
echo Press any key to stop the services and clean up...
pause >nul

echo [INFO] Stopping Docker containers...
docker compose down
echo [SUCCESS] NYAYASHASTRA stopped.
pause
