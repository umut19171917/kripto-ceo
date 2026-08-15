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
    """Son `limit` funding kaydi — startTime SAYFALAMALI.
    DUZELTME (2026-07-04): uc nokta limit=1000 istense de tek istekte ~200 kayit
    donduruyor (backtest.funding_serisi'nde 2026-07-02'de tespit edildi) ->
    sayfalanmazsa gercek pencere ~66 gun kalir (hedef 500 kayit ~166 gun @8s).
    Kadans adaptif: ilk bloktan medyan settlement araligi olculur; SAATLIK
    funding'li coinlerde (LAB tipi) pencere ona gore daralir, istek patlamaz."""
    probe = sorted(olcucu._get("/fapi/v1/fundingRate", {"symbol": symbol, "limit": 1000}),
                   key=lambda x: int(x["fundingTime"]))
    if not probe:
        return [], None, None
    ts = [int(x["fundingTime"]) for x in probe]
    fr = [float(x["fundingRate"]) for x in probe]
    if len(ts) < limit:
        gaps = sorted(ts[i] - ts[i - 1] for i in range(1, len(ts)))
        gap = gaps[len(gaps) // 2] if gaps else 8 * 3600 * 1000
        cur = ts[-1] - int(limit * gap * 1.2)   # hedef pencerenin basi (tahmini)
        eski_ts, eski_fr = [], []
        for _ in range(40):                      # guvenlik tavani
            raw = sorted(olcucu._get("/fapi/v1/fundingRate",
                                     {"symbol": symbol, "startTime": cur, "limit": 1000}),
                         key=lambda x: int(x["fundingTime"]))
            yeni = False
            for r in raw:
                t = int(r["fundingTime"])
                if t >= ts[0]:
                    break                        # probe blogunun basina ulastik
                if not eski_ts or t > eski_ts[-1]:
                    eski_ts.append(t)
                    eski_fr.append(float(r["fundingRate"]))
                    yeni = True
            if not yeni or not raw:
                break
            son_t = int(raw[-1]["fundingTime"])
            if son_t >= ts[0]:
                break
            cur = son_t + 1
        ts = eski_ts + ts
        fr = eski_fr + fr
    ts, fr = ts[-limit:], fr[-limit:]
    t0 = datetime.fromtimestamp(ts[0] / 1000, timezone.utc).date()
    t1 = datetime.fromtimestamp(ts[-1] / 1000, timezone.utc).date()
    return fr, t0, t1


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
    th = {
        "neutral": round(percentile(s, 50), 8),        # medyan
        "long_crowded": round(percentile(s, 85), 8),   # ust %15 -> long kalabalik
        "short_crowded": round(percentile(s, 15), 8),  # alt %15 -> short kalabalik
        "oi_rising": round(percentile(pos, 80), 4) if pos else 0.4,
    }
    uyari = saglik_kontrol(th)
    if uyari:
        th["saglik_uyari"] = uyari      # SALT BAYRAK — davranisi ETKILEMEZ (asagiya bak)
    return th


# Binance USD-M funding tavani (standart semboller): %0.01 = 0.0001
FUNDING_TAVAN = 0.0001


def saglik_kontrol(th):
    """Dejenere esik tespiti (2026-08-09, dis denetim BULGU 5). SALT TESPIT:
    esikleri DEGISTIRMEZ, sadece bayrak dondurur.
    GEREKCE (bilincli): fallback uygulamak BNB'nin canli skorlamasini ANINDA
    degistirirdi; K2'ye 6 islem kala olcumu bozar. Once GORUNUR yapiyoruz,
    duzeltme K2 gundeminde (o gun konfig etiketiyle birlikte).
    Gercek bulgular (2026-08-09 esikler.json):
      - BNBUSDT: neutral == short_crowded == 0.0 -> SHORT-squeeze funding kolu OLU
      - 6 sembolde long_crowded funding TAVANINA yapismis (kalibrasyon bilgi uretmiyor)
      - LABUSDT: short_crowded -%0.51 (pratikte ulasilamaz) -> SHORT kolu kapali"""
    n, lc, sc = th.get("neutral"), th.get("long_crowded"), th.get("short_crowded")
    if None in (n, lc, sc):
        return "eksik esik"
    u = []
    if not (sc < n < lc):
        u.append("siralama-bozuk")
    if sc == n:
        u.append("short_crowded==neutral (SHORT-squeeze funding kolu olu)")
    if lc == n:
        u.append("long_crowded==neutral")
    if lc >= FUNDING_TAVAN:
        u.append("long_crowded funding tavaninda (ayrim gucu dusuk)")
    return " | ".join(u) if u else None


def write_config(path=None):
    """Tum SYMBOLS icin esikleri hesapla ve esikler.json'a yaz.

    DAYANIKLILIK (2026-08-15 — canli arizadan sonra):
    Eskiden her kosu dosyayi SIFIRDAN kurardi. Bir sembolun hesabi patlarsa
    (gecici DNS/ag kesintisi yeter) o sembolun CALISAN kalibrasyonu
    {"error": ...} ile EZILIYORDU. olcucu.get_thresholds() bu kaydi gorunce
    sessizce DEFAULT_TH'ye duser -> sistem JENERIK esiklerle skorlamaya devam
    eder ve hicbir yerde yazmaz.
    2026-08-15 11:46'da tam bu oldu: 11 sembolun 11'i birden silindi, hicbir
    uyari cikmadi, K2 olcumu jenerik esiklerle devam etti.

    Yeni davranis:
      - hesap patlarsa ONCEKI IYI DEGER KORUNUR (+ bayat_since / son_hata damgasi)
      - gercekten hic degeri yoksa error kaydi yazilir
      - ust seviyeye 'bayat' listesi konur (durum.py + gunluk ozet gorur)
    Basarili kosuda compute_thresholds temiz dict dondurdugu icin damga
    kendiliginden silinir."""
    path = Path(path) if path else ESIK_FILE
    try:
        eski = (json.loads(path.read_text(encoding="utf-8")) or {}).get("symbols") or {}
    except Exception:
        eski = {}

    simdi = datetime.now(timezone.utc).isoformat(timespec="seconds")
    out = {"updated_at": simdi, "symbols": {}}
    bayat = []
    for sym in olcucu.SYMBOLS:
        try:
            out["symbols"][sym] = compute_thresholds(sym)
        except Exception as e:
            hata = f"{type(e).__name__}: {e}"
            onceki = eski.get(sym)
            if isinstance(onceki, dict) and onceki.get("neutral") is not None:
                kayit = dict(onceki)                       # SON IYI DEGERI KORU
                kayit["bayat_since"] = onceki.get("bayat_since") or simdi
                kayit["son_hata"] = hata
                out["symbols"][sym] = kayit
            else:
                out["symbols"][sym] = {"error": hata}      # hic iyi deger yok
            bayat.append(sym)
    if bayat:
        out["bayat"] = bayat
    olcucu.atomik_yaz(path, out)
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
