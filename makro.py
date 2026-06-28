"""
makro.py — KANAL 2: Makro + Jeopolitik "GUVENLIK KAPISI" (D3)
================================================================================
Bu modul FIRSAT uretmez; sadece "su an girilir mi, boyut ne?" der.
Cikti: makro.json -> kapi (ACIK/DIKKAT/KAPALI) + boyut_carpani + notlar.
Teknik/turev skoruna KARISMAZ — sadece kapi/filtre.

Uc bilesen:
  1) Takvim  : makro-takvim.json (sabit) + saat karsilastirma -> olay VETO'su
  2) Rejim   : DXY (Yahoo, anahtarsiz) -> risk-on/off bias
  3) Sok     : Binance BTC+alt esZAMANLI risk-off (0 ekstra kazima) -> sok VETO'su

Oncelik: SOK > OLAY > REJIM.  izleyici.py bunu periyodik tazeler.
Calistirma: venv\\Scripts\\python.exe makro.py
"""

import sys
import json
from datetime import datetime, timezone
from pathlib import Path

import requests

import olcucu  # get_klines, SYMBOLS

MAKRO_FILE = Path(__file__).parent / "makro.json"
TAKVIM_FILE = Path(__file__).parent / "makro-takvim.json"
UA = {"User-Agent": "Mozilla/5.0"}

# Esikler (canli veride kalibre edilebilir)
DXY_RISKOFF = 0.4    # DXY 24s > +%0.4 -> risk-off lean
DXY_RISKON = -0.4    # DXY 24s < -%0.4 -> risk-on lean
SOK_BTC = -1.5       # BTC 15dk <= -%1.5
SOK_ALT = -1.0       # alt 15dk <= -%1.0
SOK_MIN_ALT = 2      # en az 2 alt ayni anda dusmeli -> esZAMANLI risk-off

# Takvim (OTOMATIK - ForexFactory ucretsiz JSON, anahtarsiz)
FF_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
TAKVIM_TAZE_SAAT = 6   # makro-takvim.json bu sureden eskiyse yeniden cek


# ============================== Yahoo (makro fiyatlar) ==============================
def yahoo_closes(symbol, interval="1h", rng="5d"):
    u = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval={interval}&range={rng}"
    r = requests.get(u, headers=UA, timeout=12)
    r.raise_for_status()
    res = r.json()["chart"]["result"][0]
    cl = res["indicators"]["quote"][0]["close"]
    return [c for c in cl if c is not None]


def dxy_regime():
    try:
        cl = yahoo_closes("DX-Y.NYB", "1h", "5d")
        now = cl[-1]
        ref = cl[-24] if len(cl) >= 24 else cl[0]   # ~1 gun once
        chg = (now - ref) / ref * 100
        durum = "risk-off" if chg >= DXY_RISKOFF else "risk-on" if chg <= DXY_RISKON else "notr"
        return {"dxy": round(now, 3), "dxy_24s_pct": round(chg, 2), "durum": durum}
    except Exception as e:
        return {"dxy": None, "dxy_24s_pct": None, "durum": "bilinmiyor", "hata": str(e)[:60]}


# ============================== Takvim (otomatik) ==============================
def takvim_guncelle(zorla=False):
    """ForexFactory ucretsiz JSON'dan ABD yuksek/orta etki olaylarini cek -> makro-takvim.json.
    Throttle: dosya TAKVIM_TAZE_SAAT'ten yeniyse atla (zorla=True haric)."""
    if not zorla and TAKVIM_FILE.exists():
        yas = (datetime.now(timezone.utc).timestamp() - TAKVIM_FILE.stat().st_mtime) / 3600
        if yas < TAKVIM_TAZE_SAAT:
            return None
    try:
        data = requests.get(FF_URL, headers=UA, timeout=12).json()
    except Exception:
        return None
    olaylar = []
    for e in data:
        if e.get("country") != "USD" or e.get("impact") not in ("High", "Medium"):
            continue
        try:
            t = datetime.fromisoformat(e["date"]).astimezone(timezone.utc)
        except Exception:
            continue
        olaylar.append({"olay": e.get("title", "?"),
                        "etki": "yuksek" if e["impact"] == "High" else "orta",
                        "zaman": t.isoformat()})
    if olaylar:
        TAKVIM_FILE.write_text(json.dumps(
            {"_kaynak": "ForexFactory/FairEconomy (otomatik)",
             "guncellendi": datetime.now(timezone.utc).isoformat(timespec="seconds"),
             "olaylar": olaylar}, ensure_ascii=False, indent=2), encoding="utf-8")
    return olaylar


def takvim_kapisi(now):
    try:
        olaylar = json.loads(TAKVIM_FILE.read_text(encoding="utf-8")).get("olaylar", [])
    except Exception:
        return {"sonraki": None, "guncel_mi": False, "saat_kala": None,
                "yuksek_saat": None, "fomc_saat": None}
    gelecek = []
    for o in olaylar:
        try:
            t = datetime.fromisoformat(o["zaman"])
            if t.tzinfo is None:
                t = t.replace(tzinfo=timezone.utc)
            saat = (t - now).total_seconds() / 3600.0
            if saat > -0.5:  # henuz gecmemis
                gelecek.append((saat, o))
        except Exception:
            continue
    if not gelecek:
        return {"sonraki": None, "guncel_mi": False, "saat_kala": None,
                "yuksek_saat": None, "fomc_saat": None}
    gelecek.sort(key=lambda x: x[0])
    saat0, o0 = gelecek[0]
    yuksekler = [(s, o) for s, o in gelecek if o.get("etki") == "yuksek"]
    fomclar = [(s, o) for s, o in gelecek
               if "fomc" in o["olay"].lower() or "federal funds" in o["olay"].lower()]
    return {"sonraki": o0["olay"], "etki": o0.get("etki"), "saat_kala": round(saat0, 1),
            "yuksek_olay": yuksekler[0][1]["olay"] if yuksekler else None,
            "yuksek_saat": round(yuksekler[0][0], 1) if yuksekler else None,
            "fomc_saat": round(fomclar[0][0], 1) if fomclar else None,
            "guncel_mi": True}


# ============================== Sok ayak izi (Binance) ==============================
def _chg15(sym):
    k = olcucu.get_klines(sym, "1m", 16)  # ~son 15 dk
    if len(k) < 16:
        return None
    return (k[-1]["c"] - k[0]["c"]) / k[0]["c"] * 100.0


def sok_ayak_izi():
    try:
        btc = _chg15("BTCUSDT")
        alt_chgs, alt_dusen = {}, 0
        for s in olcucu.SYMBOLS:
            if s == "BTCUSDT":
                continue
            c = _chg15(s)
            alt_chgs[s] = round(c, 2) if c is not None else None
            if c is not None and c <= SOK_ALT:
                alt_dusen += 1
        aktif = (btc is not None and btc <= SOK_BTC and alt_dusen >= SOK_MIN_ALT)
        return {"aktif": aktif, "btc_15dk_pct": round(btc, 2) if btc is not None else None,
                "dusen_alt": alt_dusen, "alt_15dk": alt_chgs}
    except Exception as e:
        return {"aktif": False, "hata": str(e)[:60]}


# ============================== Birlestir -> kapi ==============================
def hesapla():
    takvim_guncelle()  # otomatik takvim tazele (throttle: TAKVIM_TAZE_SAAT)
    now = datetime.now(timezone.utc)
    tak = takvim_kapisi(now)
    rej = dxy_regime()
    sok = sok_ayak_izi()

    kapi, carpan, notlar = "ACIK", 1.0, []

    # 1) SOK (en oncelikli)
    if sok.get("aktif"):
        kapi, carpan = "KAPALI", 0.0
        notlar.append(f"RISK-OFF SOK aktif (BTC {sok.get('btc_15dk_pct')}%/15dk) -> yeni giris yok")

    # 2) OLAY (takvim) - yuksek etki olaya yakinlik
    if kapi != "KAPALI" and tak.get("guncel_mi"):
        ys = tak.get("yuksek_saat")
        fs = tak.get("fomc_saat")
        if ys is not None and 0 <= ys <= 0.5:
            kapi, carpan = "KAPALI", 0.0
            notlar.append(f"{tak.get('yuksek_olay')} {ys}s sonra -> dur, girme")
        elif ys is not None and 0 <= ys <= 2:
            kapi, carpan = "DIKKAT", min(carpan, 0.5)
            notlar.append(f"{tak.get('yuksek_olay')} {ys}s sonra -> DIKKAT, boyut yari")
        elif fs is not None and 0 <= fs <= 48:
            kapi, carpan = "DIKKAT", min(carpan, 0.5)
            notlar.append(f"FOMC {fs}s sonra -> DIKKAT, boyut yari")

    # 3) REJIM (sadece yumusatir, kapatmaz)
    if kapi == "ACIK" and rej.get("durum") == "risk-off":
        kapi, carpan = "DIKKAT", min(carpan, 0.5)
        notlar.append(f"DXY risk-off ({rej.get('dxy_24s_pct')}%) -> long bias dikkat")

    if not tak.get("guncel_mi"):
        notlar.append("UYARI: makro-takvim.json guncel degil -> gercek tarihleri gir")
    if not notlar:
        notlar.append("temiz - engel yok")

    return {"updated_at": now.isoformat(timespec="seconds"),
            "kapi": kapi, "boyut_carpani": carpan,
            "takvim": tak, "rejim": rej, "sok": sok, "notlar": notlar}


def write_makro(path=None):
    path = Path(path) if path else MAKRO_FILE
    out = hesapla()
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    o = write_makro()
    print(f"makro.json yazildi | KAPI: {o['kapi']} (boyut carpani {o['boyut_carpani']})")
    print("  takvim:", o["takvim"])
    print("  rejim :", o["rejim"])
    print("  sok   :", o["sok"])
    for n in o["notlar"]:
        print("  -", n)


if __name__ == "__main__":
    main()
