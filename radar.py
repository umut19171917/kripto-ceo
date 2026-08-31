"""
radar.py — MOD 2: Surekli piyasa radari (D1, 2026-07-06). AYRI SUREC.
================================================================================
Iki gorevi var, ikisi de Telegram'a bildirir (bildirim.py; token yoksa sadece log):

  1) HAREKET RADARI (5 dk'da bir, 1 REST istegi — ticker/24hr toplu):
     Olagandisi hareketi tespit eder (LAB +%145 dersi). 2026-07-08 kullanici
     karari: bunlar TAVSIYE degil BILGI -> Telegram'a GITMEZ; radar.log'a
     yazilir + gunluk Telegram ozetine tek satir girer + durum.py'de gorunur.
     Esikler (SAKIN-gun probu 2026-07-06: %20+ = 3 coin, %15+ = 9, %10+ = 14):
       - |24s degisim| >= HAREKET_24S (%20) ve hacim >= RADAR_VOL (30M)
       - VEYA son ~30 dk'da >= HIZLI_PCT (%8) (gelisen spike'i erken yakala)
     Spam freni: coin basina 24 saatte 1 alarm; ESKALASYON istisna (onceki
     alarm seviyesinin 2 kati asilirsa yeniden bildirir: 20 -> 40 -> 80...).
     Gunluk kuresel tavan MAX_GUN_ALARM.

  2) KURULUM TARAMASI (2 saatte bir, ~400 istek / ~3 dk):
     tarayici.py'nin Mod-1 mantigi otomatik: evren (50M taban) -> per-symbol
     kalibre -> analyze_symbol -> GECERLI plan varsa Telegram'a tam plan.
     - Canli SYMBOLS atlanir (onlar zaten defter+Telegram uretiyor).
     - Makro kapi KAPALI ise kurulum alarmi GONDERILMEZ (sadece log).
     - Ayni coin+yon 12 saatte bir kez bildirilir.
     - 2026-07-09 (kullanici istegi): adaylar ARTIK radar_defter.py'ye
       kaydedilip GERCEK mumlarla sonuclandirilir — AYRI sicil, K2 olcumune
       KARISMAZ (radar-defter.json). durum.py'de "RADAR SICILI" bolumunde
       istenilen an gorulebilir.

  3) DUYURU NOBETCISI (6 saatte bir, 1 istek — 2026-07-08, kullanici onayli):
     Binance RESMI delisting/removal duyurularini tarar; basligimda CANLI
     listedeki coinlerden biri (kelime-sinirli eslesme) YENI bir duyuruda
     gecerse Telegram'a [ONEMLI DUYURU] gonderir. "Sadece tavsiye" kuralinin
     bilincli istisnasi: tavsiye degil ama kritik + nadir (~ayda 0-1).
     Ilk tarama = taban cizgisi (mevcut/eski duyurular bildirilmez).
     Otomatik kapi/veto YOK (K2 disiplini) — degerlendirme kullanicida.
     Kaynak probu 2026-07-08: bapi/composite cms endpoint'i bu agdan HTTP 200,
     catalogId=161 = delisting kategorisi (DefiLlama unlock bacagi 402 = VERI-BLOKE).

ANA SICIL (kripto-defter.json, K2 edge olcumu) BOZULMAZ: radar-sicili TAMAMEN
AYRI bir dosyaya (radar-defter.json) yazar. signals.json'a hic dokunulmaz.
Emir HER ZAMAN kullanicida.

Calistirma:
    venv\\Scripts\\python.exe radar.py            # surekli (Startup VBS bunu baslatir)
    venv\\Scripts\\python.exe radar.py --once     # tek tur (test): hareket + kurulum
Durum dosyasi: radar-durum.json (dedupe kalicidir -> yeniden baslatma spam yapmaz).
Log: radar.log (izleyicinin olcucu.log'undan AYRI; iki surec ayni dosyaya yazmasin).
"""

import sys
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import re

import requests

import olcucu
import tarayici
import bildirim
import radar_defter   # AYRI sicil (2026-07-09): kurulum adaylari K2'den bagimsiz takip edilir

KOK = Path(__file__).parent
DURUM_FILE = KOK / "radar-durum.json"
LOG_FILE = KOK / "radar.log"

# ---- hareket radari ----
HAREKET_SEC = 300          # 5 dk'da bir toplu ticker
RADAR_VOL = 30_000_000     # 24s hacim tabani (bunun alti hareket = islenemez gurultu)
HAREKET_24S = 20.0         # ⚠ baslangic esigi (sakin-gun probu: ~3 coin/gun) — canliyla ayarlanir
HIZLI_PCT = 8.0            # ~30 dk icinde bu kadar hareket -> erken alarm
HIZLI_DK = 30
ALARM_TEKRAR_SAAT = 24     # coin basina alarm araligi (eskalasyon haric)
ESKALASYON_KAT = 2.0       # onceki alarm seviyesinin bu kati asilirsa yeniden bildir
MAX_GUN_ALARM = 20         # gunluk kuresel hareket-alarmi tavani (spam sigortasi)

# ---- kurulum taramasi ----
KURULUM_SEC = 2 * 3600     # 2 saatte bir (1h zaman diliminde kurulumlar yavas degisir)
KURULUM_TEKRAR_SAAT = 12   # ayni coin+yon icin bildirim araligi (canli COOLDOWN ile ayni)

# ---- risk tavani + cooldown kapisi (madde 2.4) ----
# 🔴 2026-08-31: KAPALI. Neden bayrak var — "radar.py'yi yeniden baslatmiyorum"
# bir uretim kapisi DEGILMIS: radar kendi kendine yeniden basliyor (3 gunde 5
# [BASLA]), 2026-08-30 21:24'teki baslatma commit'li kodu canliya aldi ve tavan
# 23:28'de calismaya basladi. ON-KAYIT-radar-tavan.md §7 bunu pesinen
# gecersizlik sarti saymisti -> 1. kurulum IPTAL (19 aday B kolundan kayip).
# Test SIMULASYONLA kosar: defter TAM kalmali, kapi canlida SUZMEMELI.
# Bunu True yapmak = kosan on kaydi ikinci kez gecersiz kilmak.
TAVAN_CANLI = False

# ---- duyuru nobetcisi ----
DUYURU_SEC = 6 * 3600      # Binance resmi duyurulari 6 saatte bir kontrol et
DUYURU_URL = "https://www.binance.com/bapi/composite/v1/public/cms/article/list/query"
DUYURU_KATALOG = 161       # delisting/removal kategorisi (prob 2026-07-08 ile dogrulandi)
_UA = {"User-Agent": "Mozilla/5.0"}

_exinfo_cache = {"ts": 0.0, "valid": set()}
_fiyat_gecmisi = {}        # sym -> [(epoch, fiyat)] son ~40 dk (bellekte; restart'ta yeniden birikir)


def log(msg):
    satir = f"[{datetime.now(timezone.utc).isoformat(timespec='seconds')}] {msg}"
    try:
        print(satir, flush=True)
    except Exception:
        pass
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(satir + "\n")
    except Exception:
        pass


def bildir(msg):
    """Telegram + log (cift kanal). Telegram yoksa alarm log'da yasar."""
    log("ALARM >>> " + msg.replace("\n", " | "))
    bildirim.gonder(msg)


def _durum_yukle():
    try:
        return json.loads(DURUM_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"alarmlar": {}, "kurulum_alarmlar": {}, "gun": "", "gun_sayac": 0}


def _durum_kaydet(d):
    olcucu.atomik_yaz(DURUM_FILE, d)


def radar_ozeti(saat=24):
    """Son `saat` icindeki radar aktivitesi (gunluk Telegram ozeti + durum.py icin).
    radar-durum.json'dan okur; radar hic calismamissa None (cagiran atlar)."""
    try:
        d = json.loads(DURUM_FILE.read_text(encoding="utf-8"))
    except Exception:
        return None
    simdi = time.time()
    hareket = sorted(((s, v.get("seviye", 0)) for s, v in d.get("alarmlar", {}).items()
                      if simdi - v.get("ts", 0) <= saat * 3600), key=lambda x: -x[1])
    kurulum = [k for k, ts in d.get("kurulum_alarmlar", {}).items()
               if simdi - ts <= saat * 3600]
    return {"hareket": hareket, "kurulum": kurulum}


def _evren_seti():
    """PERPETUAL+USDT+TRADING sembol kumesi (12 saatte bir tazelenir)."""
    if time.time() - _exinfo_cache["ts"] > 12 * 3600:
        info = olcucu._get("/fapi/v1/exchangeInfo")
        _exinfo_cache["valid"] = {s["symbol"] for s in info["symbols"]
                                  if s.get("contractType") == "PERPETUAL"
                                  and s.get("quoteAsset") == "USDT"
                                  and s.get("status") == "TRADING"}
        _exinfo_cache["ts"] = time.time()
    return _exinfo_cache["valid"]


# ============================== 1) HAREKET RADARI ==============================
def hareket_taramasi(durum):
    simdi = time.time()
    bugun = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if durum.get("gun") != bugun:
        durum["gun"], durum["gun_sayac"] = bugun, 0

    valid = _evren_seti()
    tick = olcucu._get("/fapi/v1/ticker/24hr")
    degisti = False

    for x in tick:
        sym = x["symbol"]
        if sym not in valid or float(x["quoteVolume"]) < RADAR_VOL:
            continue
        fiyat = float(x["lastPrice"])
        chg24 = float(x["priceChangePercent"])

        # ~30 dk penceresi icin fiyat gecmisi (bellekte)
        g = _fiyat_gecmisi.setdefault(sym, [])
        g.append((simdi, fiyat))
        while g and simdi - g[0][0] > (HIZLI_DK + 10) * 60:
            g.pop(0)
        hizli = 0.0
        eski = [f for t, f in g if simdi - t >= HIZLI_DK * 60 * 0.8]
        if eski and eski[0]:
            hizli = (fiyat - eski[0]) / eski[0] * 100.0

        tetik = None
        if abs(chg24) >= HAREKET_24S:
            tetik = f"{chg24:+.0f}%/24s"
        elif abs(hizli) >= HIZLI_PCT:
            tetik = f"{hizli:+.1f}%/{HIZLI_DK}dk (24s {chg24:+.0f}%)"
        if not tetik:
            continue

        seviye = max(abs(chg24), abs(hizli))
        onceki = durum["alarmlar"].get(sym)
        yeni_pencere = (onceki is None) or (simdi - onceki["ts"] > ALARM_TEKRAR_SAAT * 3600)
        eskalasyon = onceki and seviye >= onceki["seviye"] * ESKALASYON_KAT
        if not (yeni_pencere or eskalasyon):
            continue
        if durum["gun_sayac"] >= MAX_GUN_ALARM:
            log(f"[CAP] gunluk alarm tavani doldu ({MAX_GUN_ALARM}) - {sym} {tetik} SUSTURULDU")
            continue

        vol_m = float(x["quoteVolume"]) / 1e6
        onek = "[RADAR-HAREKET ESKALASYON]" if eskalasyon else "[RADAR-HAREKET]"
        # 2026-07-08 kullanici karari: hareket alarmi TAVSIYE degil BILGI ->
        # Telegram'a GITMEZ (telefon dolmasin); dosyaya yazilir, gunluk ozete
        # tek satir girer, durum.py RADAR bolumunde gorunur.
        log(f"ALARM >>> {onek} {sym} {tetik} | fiyat {fiyat} | 24s hacim {vol_m:,.0f}M "
            f"| 24s aralik {x['lowPrice']}-{x['highPrice']}")
        durum["alarmlar"][sym] = {"seviye": seviye, "ts": simdi}
        durum["gun_sayac"] += 1
        degisti = True

    if degisti:
        _durum_kaydet(durum)


# ============================== 2) KURULUM TARAMASI ==============================
def kurulum_taramasi(durum):
    kapi, makro_min, boyut = tarayici._makro_durum()
    etkin_min = max(tarayici.MIN_SKOR, makro_min)
    coins = tarayici.evren(tarayici.VOL_TABAN)
    canli = set(olcucu.SYMBOLS)
    simdi = time.time()
    log(f"[KURULUM] tarama basladi: {len(coins)} coin | kapi {kapi} | min-skor {etkin_min}")

    bulunan, hata = 0, 0
    for sym, vol in coins:
        if sym in canli:
            continue   # canli liste zaten defter+Telegram uretiyor
        try:
            th, n_settle = tarayici.kalibre(sym)
            d = olcucu.analyze_symbol(sym, th)
            sq, p = d["squeeze"], d.get("plan", {})
            skor = max(sq["short_squeeze"], sq["long_squeeze"])
            if not (p.get("yon") and p.get("gecerli") and skor >= etkin_min):
                continue
            bulunan += 1
            anahtar = f"{sym}|{p['yon']}"
            son = durum["kurulum_alarmlar"].get(anahtar, 0)
            if simdi - son < KURULUM_TEKRAR_SAAT * 3600:
                continue
            if kapi == "KAPALI":
                log(f"[KURULUM] {sym} {p['yon']} skor {skor} bulundu ama kapi KAPALI -> bildirilmedi")
                continue
            # ---- RISK TAVANI + COOLDOWN (madde 2.4, 2026-08-30) ------------------
            # SISTEM.md §12/8: radar'da ikisi de YOKTU. Olculdu: tepe 10 acik
            # pozisyon, 7'si AYNI YONDE, coinler arasi korelasyon 0,69 -> o yedi
            # pozisyon yedi ayri bahis DEGIL, tek bahsin yedi kopyasidir.
            # 🔴 ESIK ICAT EDILMEDI. Ana sicilin zaten yururlukteki degerleri
            #    kullanildi: defter.COOLDOWN_SAAT (12s) · defter.RISK_TAVANI_PCT
            #    (2.0) · olcucu.RISK_PCT. Radar'a OZEL bir sayi uydurmak
            #    "en iyi hucreyi secmek" olurdu; tek dogruluk kaynagi korunuyor.
            # ⚠ Radar kayitlarinda `risk_pct` alani YOK (459/459 kayit) ->
            #    defter.acik_risk_pct'nin kendi varsayimi aynen: 1.0.
            # ⚠ Kapi gecilmezse NE KAYIT NE BILDIRIM gider. Bildirilip
            #    kaydedilmeyen kurulum, sicili "gercekte gorulen"den ayirir.
            # ⚠ HATA HALINDE FAIL-OPEN (kaydeder, ama log'a yazar). Gerekce:
            #    fail-closed bir bug'da radar'i SESSIZCE hic kayit almaz hale
            #    getirirdi ve olcum tabanini yok ederdi; fazladan bir pozisyon
            #    ise gorunur ve geri alinabilir. Secim bilincli.
            try:
                if TAVAN_CANLI:
                    import defter as _defter
                    _T = radar_defter.tum_kayitlar()
                    _zlar = [datetime.fromisoformat(t["tarih"]) for t in _T if t["token"] == sym]
                    if _zlar:
                        _yas = (datetime.now(timezone.utc) - max(_zlar)).total_seconds() / 3600
                        if _yas < _defter.COOLDOWN_SAAT:
                            log(f"[RADAR-TAVAN] {sym} {p['yon']} atlandi: cooldown "
                                f"({_yas:.1f}s < {_defter.COOLDOWN_SAAT}s)")
                            continue
                    _mevcut = sum(t.get("risk_pct", 1.0) for t in _T
                                  if t.get("durum") in ("beklemede", "izleniyor")
                                  and t["yon"] == p["yon"])
                    if _mevcut + olcucu.RISK_PCT > _defter.RISK_TAVANI_PCT + 1e-9:
                        log(f"[RADAR-TAVAN] {sym} {p['yon']} atlandi: ayni-yon acik risk "
                            f"%{_mevcut:.1f} + %{olcucu.RISK_PCT:.1f} > tavan "
                            f"%{_defter.RISK_TAVANI_PCT:.1f}")
                        continue
            except Exception as e:
                log(f"[RADAR-TAVAN] kontrol hatasi (FAIL-OPEN, kayit gecti): "
                    f"{type(e).__name__}: {str(e)[:70]}")
            # ----------------------------------------------------------------------
            kald = p.get("ima_kaldirac")
            kald_s = f"\n[!] YUKSEK KALDIRAC ~{kald}x - boyutu elle kis" \
                     if kald and kald > tarayici.KALDIRAC_UYARI else ""
            guven_s = "" if n_settle >= tarayici.DUSUK_GUVEN_SETTLEMENT else \
                      f"\n[!] dusuk-guven kalibrasyon ({n_settle} funding kaydi)"
            dikkat_s = f" | kapi DIKKAT boyut x{boyut}" if kapi != "ACIK" else ""
            try:
                radar_defter.kaydet(sym, p["yon"], p["giris"], p["stop"], p["tp1"], p["tp2"],
                                    p["rr1"], skor, kapi)
            except Exception as e:
                log(f"[RADAR-SICIL] kayit hatasi: {type(e).__name__}: {str(e)[:70]}")
            bildir(f"[RADAR-KURULUM] {sym} {p['yon']} (skor {skor}{dikkat_s})\n"
                   f"giris {p['giris']} | stop {p['stop']} (%{p['stop_mesafe_pct']}) | "
                   f"TP1 {p['tp1']} (R/R {p['rr1']})"
                   f"{kald_s}{guven_s}\n"
                   f"radar-sicili'ne kaydedildi (ayri, K2'ye girmez) - durum.py'de takip edilebilir")
            durum["kurulum_alarmlar"][anahtar] = simdi
            _durum_kaydet(durum)
        except Exception:
            hata += 1
        time.sleep(tarayici.BEKLE)
    log(f"[KURULUM] bitti: {bulunan} gecerli plan | {hata} hata")


# ============================== 3) DUYURU NOBETCISI ==============================
def _duyuru_cek():
    r = requests.get(DUYURU_URL, headers=_UA, timeout=15,
                     params={"type": 1, "pageNo": 1, "pageSize": 20,
                             "catalogId": DUYURU_KATALOG})
    r.raise_for_status()
    d = r.json().get("data") or {}
    arts = d.get("articles")
    if not arts:
        cats = d.get("catalogs") or []
        arts = (cats[0].get("articles") if cats else []) or []
    return arts


def duyuru_taramasi(durum):
    """Binance resmi delisting duyurulari. Canli listedeki bir coin YENI duyuru
    basliginda KELIME-SINIRLI gecerse Telegram + log; ilk calisma taban cizgisi
    (bildirmeden isaretler). Eslesmeyen yeni duyurular sadece loglanir."""
    arts = _duyuru_cek()
    taban = "duyuru_gorulen" not in durum
    gorulen = durum.setdefault("duyuru_gorulen", {})
    bases = [s[:-4] for s in olcucu.SYMBOLS if s.endswith("USDT")]
    yeni, degisti = 0, False
    for a in arts:
        aid = str(a.get("id") or a.get("code") or a.get("title"))
        if aid in gorulen:
            continue
        gorulen[aid] = time.time()
        degisti = True
        yeni += 1
        if taban:
            continue   # eski duyurulari geriye donuk bildirme
        baslik = a.get("title") or ""
        # \bADA\b "CANADA"/"Labs" gibi kelimelere TAKILMAZ (buyuk harf + sinir)
        esles = [b for b in bases if re.search(rf"\b{b}\b", baslik)]
        if esles:
            bildir(f"[ONEMLI DUYURU] {'/'.join(esles)} resmi Binance duyurusunda geciyor:\n"
                   f"{baslik}\n"
                   f"kaynak: Binance delisting/removal kategorisi - detayi borsadan dogrula.\n"
                   f"Otomatik islem/veto YOK - degerlendirme sende.")
        else:
            log(f"[DUYURU] yeni (bizimkilerle eslesme yok): {baslik[:80]}")
    if taban:
        log(f"[DUYURU] taban cizgisi: {yeni} mevcut duyuru isaretlendi (bildirilmedi)")
    if len(gorulen) > 300:   # durum dosyasi sissmesin
        for k in sorted(gorulen, key=gorulen.get)[:len(gorulen) - 300]:
            del gorulen[k]
        degisti = True
    if degisti:
        _durum_kaydet(durum)


# ============================== dongu ==============================
def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    durum = _durum_yukle()
    tek = "--once" in sys.argv
    log(f"[BASLA] radar | hareket {HAREKET_SEC}s (esik %{HAREKET_24S:g}/24s, %{HIZLI_PCT:g}/{HIZLI_DK}dk, vol>={RADAR_VOL/1e6:.0f}M) "
        f"| kurulum {KURULUM_SEC/3600:g}s'te bir | telegram {'AKTIF' if bildirim.aktif() else 'YOK (yalniz log)'}")

    if tek:
        hareket_taramasi(durum)
        kurulum_taramasi(durum)
        duyuru_taramasi(durum)
        radar_defter.coz_tumu()
        radar_defter.rapor_yaz()
        log("[DUR] --once tamam")
        return

    son_kurulum = son_duyuru = 0.0
    while True:
        try:
            hareket_taramasi(durum)
        except Exception as e:
            log(f"[HATA] hareket: {type(e).__name__}: {str(e)[:80]}")
        try:
            radar_defter.coz_tumu()   # acik radar-sicili kayitlarini ilerlet (5dk'da bir)
            radar_defter.rapor_yaz()  # radar-defteri.html'i tazele (kullanici istedigi an acar)
        except Exception as e:
            log(f"[HATA] radar-sicil coz: {type(e).__name__}: {str(e)[:80]}")
        if time.time() - son_kurulum >= KURULUM_SEC:
            son_kurulum = time.time()
            try:
                kurulum_taramasi(durum)
            except Exception as e:
                log(f"[HATA] kurulum: {type(e).__name__}: {str(e)[:80]}")
        if time.time() - son_duyuru >= DUYURU_SEC:
            son_duyuru = time.time()
            try:
                duyuru_taramasi(durum)
            except Exception as e:
                log(f"[HATA] duyuru: {type(e).__name__}: {str(e)[:80]}")
        time.sleep(HAREKET_SEC)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("durduruldu")
