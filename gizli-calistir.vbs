' ============================================================================
'  gizli-calistir.vbs — verilen komutu PENCERESIZ calistirir (2026-09-01)
' ============================================================================
'  NEDEN VAR: zamanlanmis gorevler .bat dosyasi calistirinca Windows gorunur
'  bir cmd.exe penceresi aciyor. KriptoDerinlikArsiv 10 DAKIKADA BIR kosuyor ve
'  her tur 18-21 saniye suruyor -> ekranda surekli siyah pencere belirip
'  kayboluyordu. Kullanici bunu 2026-09-01'de bildirdi.
'
'  NEDEN VBS: Run'in ucuncu parametresi pencere stilidir; 0 = TAMAMEN GIZLI.
'  powershell -WindowStyle Hidden bile kisa bir an pencere gosterebiliyor;
'  wscript.exe hic gostermiyor. (Kullanicinin eski Baslangic girdileri de bu
'  yontemi kullaniyordu ve hic pencere carpmamisti.)
'
'  Kullanim:
'     wscript.exe "gizli-calistir.vbs" "C:\...\derinlik-arsiv.bat"
'
'  ⚠ Cikti/log davranisi DEGISMEZ: .bat kendi icinde yonlendirmesini yapiyor.
'  Bu sarmalayici yalnizca PENCEREYI gizler, calistirdigi seyi degistirmez.
' ============================================================================
Option Explicit
Dim i, komut, kabuk

If WScript.Arguments.Count = 0 Then
    WScript.Quit 1
End If

komut = ""
For i = 0 To WScript.Arguments.Count - 1
    komut = komut & """" & WScript.Arguments(i) & """"
    If i < WScript.Arguments.Count - 1 Then komut = komut & " "
Next

Set kabuk = CreateObject("WScript.Shell")
' 0 = pencere yok · False = bitmesini BEKLEME (gorev hemen serbest kalsin)
kabuk.Run komut, 0, False
