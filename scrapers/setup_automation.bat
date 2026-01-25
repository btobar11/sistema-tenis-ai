@echo off
REM Windows Task Scheduler Setup Script
REM Creates automated tasks for tennis match scraping with proper descriptions

echo ========================================
echo Tennis Match Scraper - Task Scheduler Setup
echo ========================================
echo.

set SCRIPT_DIR=%~dp0
REM Remove trailing backslash if present
if "%SCRIPT_DIR:~-1%"=="\" set SCRIPT_DIR=%SCRIPT_DIR:~0,-1%

echo Creating Task: EDGESET Live Monitor
schtasks /create /tn "EDGESET Live Monitor" /tr "\"%SCRIPT_DIR%\run_scraper.bat\"" /sc hourly /mo 1 /f /rl HIGHEST
if %ERRORLEVEL% EQU 0 (
    echo [OK] Live Monitor task created successfully
) else (
    echo [ERROR] Failed to create Live Monitor task with error %ERRORLEVEL%
)

echo.
echo Creating Task: EDGESET Upcoming Scraper
schtasks /create /tn "EDGESET Upcoming Scraper" /tr "\"%SCRIPT_DIR%\run_upcoming.bat\"" /sc daily /st 06:00 /f /rl HIGHEST
if %ERRORLEVEL% EQU 0 (
    echo [OK] Upcoming Scraper task created successfully
) else (
    echo [ERROR] Failed to create Upcoming Scraper task with error %ERRORLEVEL%
)

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Tasks created:
echo 1. EDGESET Live Monitor - Attempts to run every hour.
echo 2. EDGESET Upcoming Scraper - Runs daily at 6:00 AM.
echo.
echo To view tasks: Open Task Scheduler (taskschd.msc)
echo.
pause
