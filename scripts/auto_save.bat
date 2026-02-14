@echo off
cd /d "%~dp0.."
echo --- Auto-Guardado de Progreso ---
git add .
git commit -m "Auto-save: %date% %time%"
git push
echo --- Guardado Completo ---
timeout /t 5
