@echo off

echo ========================================================
echo               CrimeRakshak Runner Script
echo ========================================================
echo.

:: 1. Verify Prerequisites
echo [INFO] Verifying prerequisites...

docker --version >nul 2>&1
if %errorlevel% neq 0 goto docker_missing

docker info >nul 2>&1
if %errorlevel% neq 0 goto docker_not_running

python --version >nul 2>&1
if %errorlevel% neq 0 goto python_missing

set NODE_READY=0
node --version >nul 2>&1
if %errorlevel% equ 0 set NODE_READY=1

if %NODE_READY% equ 0 (
    echo [WARNING] Node.js is not installed or not in PATH.
    echo The frontend Next.js application will not be started automatically.
)

echo [SUCCESS] Prerequisites verified.
echo.
goto env_check

:docker_missing
echo [ERROR] Docker is not installed or not in PATH.
echo Please install Docker Desktop and add it to your PATH, then try again.
pause
exit /b 1

:docker_not_running
echo [ERROR] Docker Desktop or daemon is not running.
echo Please start Docker Desktop and run this script again.
pause
exit /b 1

:python_missing
echo [ERROR] Python is not installed or not in PATH.
echo Please install Python (3.10+) and ensure it is added to your PATH.
pause
exit /b 1


:: 2. Setup Environment Files
:env_check
echo [INFO] Checking environment configuration...
if exist backend\.env goto backend_env_exists
if not exist .env.example goto backend_env_no_example

echo [INFO] Creating backend\.env from .env.example...
copy .env.example backend\.env
goto backend_env_exists

:backend_env_no_example
echo [WARNING] .env.example not found. Please create backend\.env manually.

:backend_env_exists
if exist .env goto root_env_exists
if exist .env.example copy .env.example .env

:root_env_exists
echo [SUCCESS] Environment files verified.
echo.


:: 3. Start Database Containers
echo [INFO] Launching databases (PostgreSQL, Neo4j) via Docker Compose...
docker compose up -d
if %errorlevel% neq 0 goto docker_compose_failed
echo [SUCCESS] Docker containers are starting/running.
echo.
goto venv_setup

:docker_compose_failed
echo [ERROR] Failed to start Docker databases.
pause
exit /b 1


:: 4. Set Up Python Virtual Environment
:venv_setup
if exist backend\venv goto venv_exists
echo [INFO] Creating Python virtual environment in backend\venv...
python -m venv backend\venv
if %errorlevel% neq 0 goto venv_failed
goto install_deps

:venv_exists
echo [INFO] Python virtual environment already exists.

:install_deps
echo [INFO] Upgrading pip and installing backend dependencies...
backend\venv\Scripts\python.exe -m pip install --upgrade pip
backend\venv\Scripts\python.exe -m pip install -r backend\requirements.txt
if %errorlevel% neq 0 goto pip_failed
echo [SUCCESS] Backend dependencies verified.
echo.
goto db_init

:venv_failed
echo [ERROR] Failed to create Python virtual environment.
pause
exit /b 1

:pip_failed
echo [ERROR] Failed to install backend dependencies.
pause
exit /b 1


:: 5. Initialize Databases (Schema, Constraints, Migrations, Seeds, Ingestion)
:db_init
echo [INFO] Executing database schemas and constraint setup...
backend\venv\Scripts\python.exe backend\initialize_db.py
if %errorlevel% neq 0 goto db_init_failed

echo [INFO] Applying Alembic migrations...
cd backend
venv\Scripts\python.exe -m alembic upgrade head
if %errorlevel% neq 0 goto migration_failed

echo [INFO] Seeding baseline permissions, roles, and initial superuser...
venv\Scripts\python.exe -m app.seed
if %errorlevel% neq 0 goto seed_failed

echo [INFO] Ingesting CSV datasets into PostgreSQL and Neo4j...
venv\Scripts\python.exe ingest.py
if %errorlevel% neq 0 (
    echo [WARNING] Ingestion pipeline encountered warnings or failed.
)
cd ..
echo [SUCCESS] Database initialization and data ingestion completed.
echo.
goto frontend_setup

:db_init_failed
echo [ERROR] Database schema or constraint execution failed.
pause
exit /b 1

:migration_failed
echo [ERROR] Alembic migrations failed.
cd ..
pause
exit /b 1

:seed_failed
echo [ERROR] Seeding baseline data failed.
cd ..
pause
exit /b 1


:: 6. Setup Frontend NPM Dependencies
:frontend_setup
if %NODE_READY% neq 1 goto start_services
if exist frontend\node_modules goto start_services

echo [INFO] Installing frontend dependencies (node_modules)...
cd frontend
call npm install
cd ..
if %errorlevel% neq 0 goto npm_failed
echo [SUCCESS] Frontend dependencies installed.
echo.
goto start_services

:npm_failed
echo [ERROR] Failed to install frontend npm packages.
pause
exit /b 1


:: 7. Start Frontend & Backend Services Concurrently
:start_services
echo [INFO] Starting application servers...

start "CrimeRakshak Backend API" cmd /k "cd backend && venv\Scripts\uvicorn app.main:app --reload --port 8000"

if %NODE_READY% equ 1 (
    start "CrimeRakshak Frontend UI" cmd /k "cd frontend && call npm run dev:lowmem"
)

echo.
echo ========================================================
echo             CrimeRakshak is running!
echo ========================================================
echo.
echo   [Frontend UI]  - http://localhost:3000
echo   [Backend API]  - http://localhost:8000
echo   [API Docs]     - http://localhost:8000/docs
echo   [Neo4j UI]     - http://localhost:7474 (neo4j / password)
echo.
echo ========================================================
echo Press any key to close this console. The servers will
echo continue running in their respective windows.
echo.
pause
