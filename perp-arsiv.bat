@echo off
chcp 65001 >nul
cd /d "%~dp0"
rem ============================================================
rem  PERP ARSIVCI - gunluk artimli tur (~2 gun geri, ortusmeli)
rem
rem  NEDEN GUNLUK: /futures/data/* uclari yalniz ~29 gun geriye
rem  gidiyor (olculdu 2026-08-25: 29g OK, 32g HTTP 400). Bu veri
rem  SONRADAN CEKILEMEZ - kosmazsa kuyruktan gun DUSER.
rem
rem  Gorev Zamanlayici'ya eklemek icin (PowerShell, tek satir):
rem    Register-ScheduledTask -TaskName "KriptoPerpArsiv" `
rem      -Action (New-ScheduledTaskAction -Execute "%~f0") `
rem      -Trigger (New-ScheduledTaskTrigger -Daily -At 04:00) `
rem      -Settings (New-ScheduledTaskSettingsSet -StartWhenAvailable)
rem
rem  Denetim:  Get-ScheduledTaskInfo -TaskName KriptoPerpArsiv
rem  Kapsama:  venv\Scripts\python.exe perp_arsiv.py --durum
rem ============================================================
".\venv\Scripts\python.exe" perp_arsiv.py
