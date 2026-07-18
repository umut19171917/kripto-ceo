@echo off
chcp 65001 >nul
cd /d "%~dp0"
venv\Scripts\python.exe _hat_testi.py
echo.
pause
