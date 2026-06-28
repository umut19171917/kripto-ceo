@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ================================================
echo   KRIPTO - CANLI IZLEYICI  (REST + likidasyon)
echo   Surekli calisir, signals.json'u gunceller.
echo   Likidasyon olunca [LIKIDASYON] satiri duser.
echo   DURDURMAK: bu pencereyi kapat veya Ctrl+C.
echo ================================================
echo.
".\venv\Scripts\python.exe" izleyici.py
