@echo off
REM Automated Upcoming Matches Scraper
REM Runs daily to fetch future matches

cd /d "%~dp0"

echo [%date% %time%] Starting upcoming matches scraper...
python upcoming_scraper.py

if %ERRORLEVEL% EQU 0 (
    echo [%date% %time%] Scraper completed successfully
) else (
    echo [%date% %time%] Scraper failed with error code %ERRORLEVEL%
)
