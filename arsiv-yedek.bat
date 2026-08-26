@echo off
chcp 65001 >nul
cd /d "%~dp0"
rem ============================================================
rem  ARSIV YEDEK - haftalik sikistirilmis yedek (perp-arsiv/)
rem
rem  Pazar 04:30 - gunluk arsivciden (04:00) YARIM SAAT SONRA,
rem  boylece taze veri yedeklenir.
rem
rem  ⚠ yedek.py'ye DOKUNULMADI: o gunluk defter yedegini yapiyor
rem  ve izleyici.py dongusunden cagriliyor. Bu AYRI ve BAGIMSIZ.
rem
rem  Denetim:  Get-ScheduledTaskInfo -TaskName KriptoArsivYedek
rem  Durum  :  venv\Scripts\python.exe arsiv_yedek.py --durum
rem  Kaldir :  Unregister-ScheduledTask -TaskName KriptoArsivYedek
rem ============================================================
".\venv\Scripts\python.exe" -u arsiv_yedek.py >> "arsiv-yedek.log" 2>&1
echo [%date% %time%] cikis kodu=%ERRORLEVEL% >> "arsiv-yedek.log"
