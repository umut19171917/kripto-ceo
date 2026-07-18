"""
likidasyon.py — Coinalyze REST likidasyon beslemesi (2026-07-06)
================================================================================
Binance WS forceOrder bu agda OLU (bolgesel engel, 2026-07-01 teshisi). Bu modul
o bacagi Coinalyze'in ucretsiz REST API'siyle doldurur.

DURUST SINIR: Bu GERCEK-ZAMANLI degil — 1 dakikalik barlar, ~2-3 dk yayin
gecikmesi (prob 2026-07-06). 5dk/1s pencereli ozet ve kademe (cascade) tespiti
icin yeterli; saniyelik tepki icin degil. Bar'lar SEYREK: likidasyon olmayan
dakikada bar gelmez (bar yoklugu = olay yoklugu).

CASCADE KALIBRASYONU (prob bulgusu): eski sabit $1M/5dk esigi veriyle curudu —
BTC'de gunde ~14 kez asiliyor (nadir degil), LINK/ADA/NEAR/LAB'da 30 gunde hic
(asla atesle(e)mez). Dogrusu PER-SYMBOL: son 30 gunun 5dk tek-taraf max USD
dagiliminda P99.5 ("BU coin icin olagandisi"). Gunde ~1 kez tazelenir,
likidasyon-esik.json'a yazilir (izleyici okur).

API: coinalyze.json {api_key, url} (GITIGNORE'lu). Limit 40 istek/dk.
Kullanim: izleyici.likidasyon_loop 60 sn'de bir taze_bars() cagirir (TEK istek,
11 sembol birden). Config yoksa her fonksiyon sessiz bos doner (fail-safe).
Test: venv\\Scripts\\python.exe likidasyon.py
"""

import sys
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

import olcucu  # SYMBOLS, atomik_yaz, log_line

CONF_FILE = Path(__file__).parent / "coinalyze.json"
ESIK_FILE = Path(__file__).parent / "likidasyon-esik.json"

KAL_GUN = 30            # cascade kalibrasyon penceresi
KAL_PCT = 99.5          # tek-taraf 5dk max dagiliminda persentil -> "olagandisi" esigi
KAL_TAZE_SAAT = 24      # esik dosyasi bundan yeniyse yeniden kalibre etme
TIMEOUT = 20


def _conf():
    try:
        c = json.loads(CONF_FILE.read_text(encoding="utf-8"))
        return c if c.get("api_key") else None
    except Exception:
        return None


def aktif():
    return _conf() is not None


def _esle(sym):
    """Binance sembolu -> Coinalyze sembolu (A = Binance; prob'la dogrulandi)."""
    return f"{sym}_PERP.A"


def _sorgu(c, **params):
    r = requests.get(c["url"] + "/liquidation-history",
                     headers={"api_key": c["api_key"]}, params=params, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def taze_bars(symbols, dk=10):
    """Son `dk` dakikanin KAPANMIS 1dk likidasyon barlari, TEK istekte.
    Doner: {sym: [(bar_ts_epoch, long_usd, short_usd), ...]} (bos olabilir).
    Olusan son dakika atilir (yarim bar cift sayima yol acmasin)."""
    c = _conf()
    if not c:
        return {}
    simdi = int(time.time())
    d = _sorgu(c, symbols=",".join(_esle(s) for s in symbols), interval="1min",
               **{"from": simdi - dk * 60, "to": simdi}, convert_to_usd="true")
    ters = {_esle(s): s for s in symbols}
    out = {}
    for x in d:
        sym = ters.get(x.get("symbol"))
        if not sym:
            continue
        out[sym] = [(int(b["t"]), float(b.get("l") or 0), float(b.get("s") or 0))
                    for b in x.get("history", [])
                    if int(b["t"]) + 60 <= simdi]   # sadece kapanmis dakika
    return out


def _pct(sorted_vals, p):
    if not sorted_vals:
        return None
    k = (len(sorted_vals) - 1) * p / 100.0
    f = int(k)
    cx = min(f + 1, len(sorted_vals) - 1)
    return sorted_vals[f] + (sorted_vals[cx] - sorted_vals[f]) * (k - f)


def kalibre(symbols, zorla=False):
    """Per-symbol cascade esigi (5dk tek-taraf max USD, son KAL_GUN gun, P99.5).
    Dosya tazeyse atlar. Doner: {sym: esik_usd} (hata/veri-yok sembol atlanir)."""
    if not zorla and ESIK_FILE.exists():
        yas = (time.time() - ESIK_FILE.stat().st_mtime) / 3600
        if yas < KAL_TAZE_SAAT:
            return esikler()
    c = _conf()
    if not c:
        return {}
    simdi = int(time.time())
    out = {}
    for s in symbols:
        try:
            d = _sorgu(c, symbols=_esle(s), interval="5min",
                       **{"from": simdi - KAL_GUN * 86400, "to": simdi},
                       convert_to_usd="true")
            h = d[0].get("history", []) if d else []
            vals = sorted(max(float(b.get("l") or 0), float(b.get("s") or 0)) for b in h)
            e = _pct(vals, KAL_PCT)
            if e and e > 0:
                out[s] = round(e)
        except Exception as e:
            olcucu.log_line(f"[LIKIDASYON] {s} kalibrasyon atlandi: {type(e).__name__}: {str(e)[:50]}")
        time.sleep(1.6)   # 40 istek/dk limitine nazik tempo
    if out:
        olcucu.atomik_yaz(ESIK_FILE, {
            "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "_kaynak": f"Coinalyze {KAL_GUN}g 5dk tek-taraf max, P{KAL_PCT}",
            "esikler": out})
    return out


def esikler():
    """Kayitli per-symbol cascade esikleri. Yoksa bos dict (izleyici fallback kullanir)."""
    try:
        return json.loads(ESIK_FILE.read_text(encoding="utf-8")).get("esikler", {})
    except Exception:
        return {}


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    if not aktif():
        print("coinalyze.json yok/bos - modul pasif")
        sys.exit(1)
    b = taze_bars(olcucu.SYMBOLS, dk=15)
    print("taze_bars (15dk):")
    for s in olcucu.SYMBOLS:
        h = b.get(s, [])
        L = sum(x[1] for x in h)
        S = sum(x[2] for x in h)
        print(f"  {s:<10} {len(h):>2} bar | L ${L:,.0f} / S ${S:,.0f}")
    e = kalibre(olcucu.SYMBOLS)
    print("cascade esikleri (P%s, %sg):" % (KAL_PCT, KAL_GUN))
    for s, v in e.items():
        print(f"  {s:<10} ${v:,.0f}")
