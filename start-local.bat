@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo  NYAYASHASTRA - Starting Local Development Environment
echo  (Running without Docker)
echo ========================================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not found in PATH. Please install Python 3.10+ and add it to PATH.
    pause
    exit /b 1
)

:: Check Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not found in PATH. Please install Node.js 18+ and add it to PATH.
    pause
    exit /b 1
)

:: ----------------------------------------------------
:: 1. Backend Setup
:: ----------------------------------------------------
echo [1/4] Checking Backend Environment...
cd backend

if not exist ".env" (
    echo [INFO] Creating backend/.env from .env.example...
    copy .env.example .env >nul
)

if not exist "venv" (
    echo [INFO] Creating Python virtual environment (backend/venv)...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        cd ..
        pause
        exit /b 1
    )
)

echo [INFO] Activating virtual environment and verifying dependencies...
call venv\Scripts\activate.bat

python -c "import fastapi" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installing backend dependencies from requirements.txt...
    echo (This may take a few minutes on the first run)
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install backend dependencies.
        cd ..
        pause
        exit /b 1
    )
)

:: Seed database if SQLite DB does not exist
if not exist "nyayashastra.db" (
    echo [INFO] Seeding initial legal database (IPC, BNS, mappings)...
    python -m app.seed_database
)

cd ..

:: ----------------------------------------------------
:: 2. Frontend Setup
:: ----------------------------------------------------
echo [2/4] Checking Frontend Environment...

if not exist ".env" (
    if exist ".env.example" (
        echo [INFO] Creating .env from .env.example...
        copy .env.example .env >nul
    )
)

if not exist "node_modules" (
    echo [INFO] Installing frontend dependencies (npm install)...
    echo (This may take a few moments on the first run)
    call npm install
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install npm packages.
        pause
        exit /b 1
    )
)

:: ----------------------------------------------------
:: 3. Launch Services
:: ----------------------------------------------------
echo [3/4] Launching Backend & Frontend services in separate windows...

:: Launch Backend
start "NYAYASHASTRA Backend (FastAPI)" cmd /k "cd backend && call venv\Scripts\activate.bat && python -m uvicorn app.main:app --reload --port 8000"

:: Launch Frontend
start "NYAYASHASTRA Frontend (Vite)" cmd /k "npm run dev"

:: ----------------------------------------------------
:: 4. Ready
:: ----------------------------------------------------
echo.
echo ========================================================
echo  NYAYASHASTRA is launching!
echo ========================================================
echo - Frontend:  http://localhost:5173
echo - Backend:   http://localhost:8000
echo - API Docs:  http://localhost:8000/docs
echo.
echo Opening browser...
timeout /t 3 >nul
start http://localhost:5173

echo.
echo Backend and Frontend are running in their own command windows.
echo To stop them, simply close those terminal windows.
echo.
pause
