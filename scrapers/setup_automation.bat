@echo off
REM Windows Task Scheduler Setup Script
REM Creates automated tasks for tennis match scraping

echo ========================================
echo Tennis Match Scraper - Task Scheduler Setup
echo ========================================
echo.

set SCRIPT_DIR=%~dp0
set PYTHON_EXE=python

echo Creating Task: Tennis Live Results Scraper
schtasks /create /tn "Tennis Live Results Scraper" /tr "%SCRIPT_DIR%run_scraper.bat" /sc hourly /st 00:00 /f
if %ERRORLEVEL% EQU 0 (
    echo [OK] Live results scraper task created successfully
) else (
    echo [ERROR] Failed to create live results task
)

echo.
echo Creating Task: Tennis Upcoming Matches Scraper
schtasks /create /tn "Tennis Upcoming Matches Scraper" /tr "%PYTHON_EXE% %SCRIPT_DIR%upcoming_scraper.py" /sc daily /st 06:00 /f
if %ERRORLEVEL% EQU 0 (
    echo [OK] Upcoming matches scraper task created successfully
) else (
    echo [ERROR] Failed to create upcoming matches task
)

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Tasks created:
echo 1. Tennis Live Results Scraper - Runs every hour
echo 2. Tennis Upcoming Matches Scraper - Runs daily at 6:00 AM
echo.
echo To view tasks: Open Task Scheduler (taskschd.msc)
echo To run manually: Right-click task and select "Run"
echo.
pause
