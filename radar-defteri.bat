@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist "radar-defteri.html" (
    echo Henuz radar-defteri.html olusmadi - radar.py ilk turunu tamamlamis olmali.
    pause
    exit /b
)
start "" "radar-defteri.html"
