# ==============================================================================
#  otomatik-baslat.ps1 — canli surecleri ayakta tutar (2026-09-01)
# ==============================================================================
#  NEDEN VAR: izleyici.py ve radar.py zamanlanmis gorev DEGILDI; elle
#  baslatilmis pythonw surecleriydi. Makine kapaninca oluyorlar ve KENDILIGINDEN
#  GERI GELMIYORLARDI. Kullanici gunde <=45 dk makineyi kapatmak zorunda
#  (2026-09-01) -> her kapanista canli sistem elle baslatilmayi bekliyordu.
#
#  NE YAPAR: her calistiginda her betik icin bakar —
#     koşuyorsa    -> DOKUNMAZ (kopya acmaz)
#     kosmuyorsa   -> gizli pencerede baslatir
#  Gorev hem ACILISTA hem 10 DAKIKADA BIR kosar; yani sadece acilisi degil,
#  cokmeyi de telafi eder (kendini iyilestiren).
#
#  🔴 KOSAN ON KAYITLARA ETKISI YOK: bu betik KODU degistirmez, yalnizca
#  baslatma bicimini degistirir. radar.py'nin TAVAN_CANLI=False bayragi
#  commit'li oldugu icin yeniden baslatma ON-KAYIT-radar-tavan.md §7'yi
#  IHLAL ETMEZ — bayrak zaten bunun icin konmustu (2026-08-31 dersi).
#
# ------------------------------------------------------------------------------
#  🔴 NEYIN YERINE GECTI (2026-09-01) — ve ONCEKI TESHISIMIN DUZELTMESI
# ------------------------------------------------------------------------------
#  Baslangic klasorunde ZATEN iki dosya vardi ve KOSULSUZ baslatiyorlardi:
#     KriptoIzleyici.vbs :
#       CreateObject("WScript.Shell").Run "...\venv\Scripts\pythonw.exe ...\izleyici.py", 0, False
#     KriptoRadar.vbs :
#       CreateObject("WScript.Shell").Run "...\venv\Scripts\pythonw.exe ...\radar.py", 0, False
#
#  ⚠ DUZELTME: 2026-08-31'de "radar 3 gunde 5 kez yeniden basladi, zamanlanmis
#  gorev YOK, demek ki makine ya da kullanici" demistim. MEKANIZMAYI YANLIS
#  TESHIS ETMISIM — sebep bu Baslangic girdileriydi; her oturum acilista
#  atesliyorlardi. (Vardigim SONUC dogruydu: commit'lenen kod bir sonraki
#  kalkista canliya girer. Yalniz nedeni yanlis gostermistim.)
#
#  NEDEN KALDIRILDILAR: kontrol yapmiyorlardi. Bu betikle birlikte calissalardi
#  acilista IKISER KOPYA riski dogardi — iki izleyici.py ayni deftere yazar.
#  (Tam olarak 2026-08-30'da arastirip CURUTTUGUM senaryo; gercekten yaratmak
#  kotu olurdu.) Icerikleri yukarida birebir duruyor; geri konmasi gerekirse
#  iki satir yeterli.
#
#  Elle calistirma / denetim:
#     powershell -ExecutionPolicy Bypass -File otomatik-baslat.ps1
#     Get-Content otomatik-baslat.log -Tail 20 -Encoding utf8
# ==============================================================================

$KOK = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $KOK
$PY  = Join-Path $KOK "venv\Scripts\pythonw.exe"
$LOG = Join-Path $KOK "otomatik-baslat.log"

# Ayakta tutulacak betikler. Yeni bir surekli betik eklenirse buraya yazilir.
$BETIKLER = @("izleyici.py", "radar.py")

function Yaz([string]$m) {
    $damga = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    Add-Content -Path $LOG -Value "[$damga] $m" -Encoding utf8
}

if (-not (Test-Path $PY)) {
    Yaz "HATA: pythonw bulunamadi -> $PY"
    exit 1
}

$baslatilan = @()
$zaten      = @()

foreach ($betik in $BETIKLER) {
    # Calisan var mi? pythonw KABUK sureci de ayni komut satirini tasir,
    # o yuzden herhangi biri varsa betik AYAKTA sayilir (2026-08-30 dersi:
    # venv\pythonw.exe bir baslatici kabuktur, 2 betik 4 surec gorunur).
    $var = Get-CimInstance Win32_Process -Filter "Name='pythonw.exe'" -ErrorAction SilentlyContinue |
           Where-Object { $_.CommandLine -and $_.CommandLine -match [regex]::Escape($betik) }
    if ($var) {
        $zaten += $betik
        continue
    }
    try {
        Start-Process -FilePath $PY -ArgumentList $betik `
                      -WorkingDirectory $KOK -WindowStyle Hidden
        $baslatilan += $betik
    } catch {
        Yaz "HATA: $betik baslatilamadi -> $($_.Exception.Message)"
    }
}

if ($baslatilan.Count -gt 0) {
    Yaz ("BASLATILDI: " + ($baslatilan -join ", ") +
         $(if ($zaten.Count) { "  | zaten kosuyordu: " + ($zaten -join ", ") } else { "" }))
} else {
    # Her 10 dakikada bir "hepsi ayakta" yazmak log'u sisirir; yalniz gunde
    # bir kez nabiz satiri dusurulur (denetim icin: log tamamen susmasin).
    $sonNabiz = $null
    if (Test-Path $LOG) {
        $s = Get-Content $LOG -Tail 200 -Encoding utf8 -ErrorAction SilentlyContinue |
             Where-Object { $_ -match "NABIZ" } | Select-Object -Last 1
        if ($s -and $s -match "\[(.+?)\]") { $sonNabiz = [datetime]::Parse($matches[1]).ToUniversalTime() }
    }
    if (-not $sonNabiz -or ((Get-Date).ToUniversalTime() - $sonNabiz).TotalHours -ge 24) {
        Yaz ("NABIZ: hepsi ayakta (" + ($zaten -join ", ") + ")")
    }
}
