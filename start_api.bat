@echo off
echo Starting Tennis API Server...
cd /d "%~dp0"
.venv\Scripts\python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
pause
