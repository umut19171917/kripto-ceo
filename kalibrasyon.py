"""
kalibrasyon.py — Esikleri GERCEK tarihsel veriyle ayarla (Faz 1 kalibrasyon)
================================================================================
Tahmini esikler yerine, son aylarin gercek dagilimindan yuzdelik-tabanli esik uretir
ve PER-SYMBOL olarak esikler.json'a yazar. olcucu.py bu dosyayi okur.

  - Funding: son ~settlement (8s) -> dagilim -> "kalabalik" esikleri yuzdelikten
  - OI delta: son ~saat -> 1s % degisim dagilimi -> "OI artiyor" esigi yuzdelikten

Kullanim:
  - Elle:        venv\\Scripts\\python.exe kalibrasyon.py   (rapor basar + esikler.json yazar)
  - Otomatik:    izleyici.py acilista + her 12s'te write_config()'i kendisi cagirir.

NOT: Likidasyon/CASCADE esigi tarihsel veride YOK (Binance vermez) -> canli gozlemle ayarlanir.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import olcucu

ESIK_FILE = Path(__file__).parent / "esikler.json"


def percentile(sorted_data, p):
    n = len(sorted_data)
    if n == 0:
        return None
    k = (n - 1) * p / 100.0
    f = int(k)
    c = min(f + 1, n - 1)
    return sorted_data[f] + (sorted_data[c] - sorted_data[f]) * (k - f)


def pct_str(x):
    return f"{x * 100:+.4f}%" if x is not None else "n/a"


def funding_rates(symbol, limit=500):
    raw = olcucu._get("/fapi/v1/fundingRate", {"symbol": symbol, "limit": limit})
    rates = [float(x["fundingRate"]) for x in raw]
    t0 = datetime.fromtimestamp(raw[0]["fundingTime"] / 1000, timezone.utc).date()
    t1 = datetime.fromtimestamp(raw[-1]["fundingTime"] / 1000, timezone.utc).date()
    return rates, t0, t1


def oi_1h_deltas(symbol, limit=500):
    raw = olcucu._get("/futures/data/openInterestHist",
                      {"symbol": symbol, "period": "1h", "limit": limit})
    ois = [float(x["sumOpenInterest"]) for x in raw]
    deltas = []
    for i in range(1, len(ois)):
        if ois[i - 1]:
            deltas.append((ois[i] - ois[i - 1]) / ois[i - 1] * 100.0)
    return deltas


def compute_thresholds(symbol):
    """Tek sembol icin veriye dayali esikler."""
    rates, _, _ = funding_rates(symbol)
    s = sorted(rates)
    pos = sorted(d for d in oi_1h_deltas(symbol) if d > 0)
    return {
        "neutral": round(percentile(s, 50), 8),        # medyan
        "long_crowded": round(percentile(s, 85), 8),   # ust %15 -> long kalabalik
        "short_crowded": round(percentile(s, 15), 8),  # alt %15 -> short kalabalik
        "oi_rising": round(percentile(pos, 80), 4) if pos else 0.4,
    }


def write_config(path=None):
    """Tum SYMBOLS icin esikleri hesapla ve esikler.json'a yaz."""
    path = Path(path) if path else ESIK_FILE
    out = {"updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "symbols": {}}
    for sym in olcucu.SYMBOLS:
        try:
            out["symbols"][sym] = compute_thresholds(sym)
        except Exception as e:
            out["symbols"][sym] = {"error": f"{type(e).__name__}: {e}"}
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def _report(symbol):
    rates, t0, t1 = funding_rates(symbol)
    s = sorted(rates)
    print(f"\n=== {symbol} FUNDING ({len(rates)} settlement, {t0} -> {t1}) ===")
    for p in (5, 15, 25, 50, 75, 85, 95):
        print(f"  P{p:<2} = {pct_str(percentile(s, p))}")
    print(f"  ort = {pct_str(sum(rates)/len(rates))}  | min {pct_str(s[0])}  max {pct_str(s[-1])}")
    pos = sorted(d for d in oi_1h_deltas(symbol) if d > 0)
    print(f"  OI 1s pozitif degisim: P75 {percentile(pos,75):+.2f}%  P80 {percentile(pos,80):+.2f}%  P90 {percentile(pos,90):+.2f}%")


def main():
    print("KALIBRASYON — gercek tarihsel dagilim")
    for sym in olcucu.SYMBOLS:
        try:
            _report(sym)
        except Exception as e:
            print(f"  {sym}: HATA {type(e).__name__}: {e}")

    cfg = write_config()
    print("\n" + "=" * 64)
    print(f"esikler.json yazildi (per-symbol) @ {cfg['updated_at']}")
    for sym, th in cfg["symbols"].items():
        if "error" in th:
            print(f"  {sym}: HATA {th['error']}")
        else:
            print(f"  {sym:<9} neutral {th['neutral']:+.6f} | long {th['long_crowded']:+.6f} "
                  f"| short {th['short_crowded']:+.6f} | oi_rising {th['oi_rising']}")
    print("=" * 64)


if __name__ == "__main__":
    main()
