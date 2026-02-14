@echo off
echo ==========================================
echo      SISTEMA TENIS - SESION DIARIA
echo ==========================================
echo.

python "%~dp0system_health_check.py"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Fallo en el chequeo de salud!
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [INFO] Salud del Sistema Verificada.
echo.

set /p running="Ejecutar Auto-Guardado (Commit & Push)? (S/N): "
if /i "%running%"=="S" (
    call "%~dp0auto_save.bat"
) else (
    echo [INFO] Auto-Guardado omitido.
)

echo.
echo ==========================================
echo           SESION LISTA
echo ==========================================
pause
