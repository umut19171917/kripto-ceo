@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Masaustune kripto-tam-kod.md uretiliyor...
venv\Scripts\python.exe tamkod.py
echo.
pause
