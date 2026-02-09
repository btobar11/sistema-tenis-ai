@echo off
REM Windows Task Scheduler CLEANUP Script
REM Removes automated tasks for tennis match scraping to prevent local execution

echo ========================================
echo Tennis Match Scraper - REMOVING LOCAL TASKS
echo ========================================
echo.

echo Deleting Task: EDGESET Live Monitor
schtasks /delete /tn "EDGESET Live Monitor" /f
if %ERRORLEVEL% EQU 0 (
    echo [OK] Live Monitor task removed successfully
) else (
    echo [INFO] Live Monitor task not found or already removed
)

echo.
echo Deleting Task: EDGESET Upcoming Scraper
schtasks /delete /tn "EDGESET Upcoming Scraper" /f
if %ERRORLEVEL% EQU 0 (
    echo [OK] Upcoming Scraper task removed successfully
) else (
    echo [INFO] Upcoming Scraper task not found or already removed
)

echo.
echo ========================================
echo Cleanup Complete! Local automation disabled.
echo ========================================
echo.

