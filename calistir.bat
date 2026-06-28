@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo   KRIPTO VERI MOTORU  -  tek tarama
echo ============================================
echo.
".\venv\Scripts\python.exe" olcucu.py
echo.
echo Bitti. signals.json guncellendi.
echo Bu pencereyi kapatabilirsin.
pause
