@echo off
cd /d "%~dp0backend"
echo [Backend] Starting FastAPI on http://localhost:8001 ...
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)
python -m uvicorn app.main:app --reload --port 8001
pause
