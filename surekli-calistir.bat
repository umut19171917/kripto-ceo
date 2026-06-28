@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo   KRIPTO VERI MOTORU  -  surekli mod
echo   Her 30 saniyede bir gunceller.
echo   DURDURMAK icin: bu pencereyi kapat.
echo ============================================
echo.
".\venv\Scripts\python.exe" olcucu.py --loop 30
