@echo off
:: ========================================================
::   CrimeRakshak - DIRECT RUN (fast start, no setup)
::   Assumes first-time setup is already done via run.bat
::   (venv created, deps installed, database initialized).
:: ========================================================
echo ========================================================
echo            CrimeRakshak - Starting all services
echo ========================================================
echo.

cd /d "%~dp0"

:: --- 1. Make sure Docker is running ---
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker Desktop is not running. Please start it and retry.
    pause
    exit /b 1
)

:: --- 2. Start databases (no-op if already up) ---
echo [INFO] Starting databases (PostgreSQL, Neo4j)...
docker compose up -d
if %errorlevel% neq 0 (
    echo [ERROR] Failed to start database containers.
    pause
    exit /b 1
)

:: --- 3. Verify backend was set up ---
if not exist backend\venv\Scripts\uvicorn.exe (
    echo [ERROR] Backend not set up yet. Run run.bat once first.
    pause
    exit /b 1
)

:: --- 4. Refresh the CSV analytics database (fast, stateless) ---
echo [INFO] Building CSV analytics database (DuckDB)...
cd backend
venv\Scripts\python.exe -m app.chat.data.loader
cd ..

:: --- 5. Launch backend + frontend in separate windows ---
echo [INFO] Launching Backend API...
start "CrimeRakshak Backend API" cmd /k "cd /d \"%~dp0backend\" && venv\Scripts\uvicorn app.main:app --reload --port 8000"

node --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] Launching Frontend UI...
    start "CrimeRakshak Frontend UI" cmd /k "cd /d \"%~dp0frontend\" && call npm run dev:lowmem"
) else (
    echo [WARNING] Node.js not found - skipping frontend.
)

echo.
echo ========================================================
echo             CrimeRakshak is starting!
echo ========================================================
echo   [Frontend UI]  - http://localhost:3000
echo   [Backend API]  - http://localhost:8000
echo   [API Docs]     - http://localhost:8000/docs
echo ========================================================
echo Servers run in their own windows. Close them to stop.
echo.
pause
