@echo off
chcp 65001 >nul
cd /d "%~dp0"
rem ============================================================
rem  EMIR DEFTERI DERINLIGI - ILERI ARSIVCI (tek snapshot turu)
rem
rem  NEDEN SIK: /fapi/v1/depth'in GECMISI YOK (olculdu 2026-08-31:
rem  startTime kabul ediliyor ama ayni anlik veriyi donduruyor).
rem  perp_arsiv'de 29 gun geri dolgu vardi; BURADA SIFIR.
rem  Kosulmayan an KALICI olarak yoktur.
rem
rem  NEDEN 10 DAKIKA: sinanacak ufuk 1 SAAT (derinlik bir mikroyapi
rem  degiskenidir; 24 saatlik ufukta 30 gunluk arsiv ±%1,74
rem  hassasiyet verir = ise yaramaz. 1 saatlik ufukta ±%0,064).
rem  10 dakikada bir = saatte 6 ornek.
rem
rem  Gorev Zamanlayici'ya eklemek icin (PowerShell, tek satir):
rem    $t = New-ScheduledTaskTrigger -Once -At (Get-Date) `
rem           -RepetitionInterval (New-TimeSpan -Minutes 10)
rem    Register-ScheduledTask -TaskName "KriptoDerinlikArsiv" `
rem      -Action (New-ScheduledTaskAction -Execute "%~f0") -Trigger $t `
rem      -Settings (New-ScheduledTaskSettingsSet -StartWhenAvailable)
rem
rem  Denetim:  Get-ScheduledTaskInfo -TaskName KriptoDerinlikArsiv
rem  Kapsama:  venv\Scripts\python.exe derinlik_arsiv.py --durum
rem
rem  UYARI LOG UTF-8'DIR. PowerShell 5.1 Get-Content varsayilan ANSI okur
rem  ve Turkce bozuk gorunur; dosya bozuk DEGILDIR.
rem  Dogru okuma:  Get-Content derinlik-arsiv.log -Tail 20 -Encoding utf8
rem ============================================================
".\venv\Scripts\python.exe" -u derinlik_arsiv.py >> "derinlik-arsiv.log" 2>&1
