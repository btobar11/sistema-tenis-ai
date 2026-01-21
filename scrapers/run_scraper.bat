@echo off
REM Automated Tennis Match Scraper
REM Runs every hour to fetch latest matches

cd /d "%~dp0"

echo [%date% %time%] Starting scraper...
python live_monitor.py --once

if %ERRORLEVEL% EQU 0 (
    echo [%date% %time%] Scraper completed successfully
) else (
    echo [%date% %time%] Scraper failed with error code %ERRORLEVEL%
)
