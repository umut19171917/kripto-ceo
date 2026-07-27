@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Kritik dosyalar Google Drive'a yedekleniyor...
venv\Scripts\python.exe yedek.py --zorla
echo.
pause
