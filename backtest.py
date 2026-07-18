"""
backtest.py — Icra mekanigi (GIRIS x STOP) hipotez testi  [Option A: revize]
================================================================================
Amac: trade_plan'in GIRIS ZAMANI ve STOP GENISLIGI mekanigini gecmis klines
uzerinde A/B test etmek. Canli sisteme DOKUNMAZ; sadece okur+hesaplar+rapor.

Bu surum (Option A revizeleri):
  1) KOMISYON + SLIPPAGE  -> net R (gercekci; dar stop'u cezalandirir)
  2) LONG / SHORT ayrimi  -> her yon ayri raporlanir
  3) FUNDING-FILTRELI alt-kume -> "kalabalik taraf" sartini saglayan adaylar
     (canli sikisma setup'ina yaklasik; turev filtresinin en baskin bileseni)

SINIR (durust): Tam sikisma skoru (OI/likidasyon) gecmise yok; funding filtresi
yaklasik. Mutlak isabet canliyla bire bir degil; GECERLI olan config'lerin
ESLI siralamasi. Funding esikleri esikler.json'dan (yoksa DEFAULT_TH) -> yeni/
kalibresiz coin (LABUSDT) filtre sonuclari yanli olabilir (not dusulur).

Calistirma: venv\\Scripts\\python.exe backtest.py
"""

import sys
import bisect
from datetime import datetime, timezone

import olcucu  # _get, atr, get_thresholds, SYMBOLS

# ---- parametreler (canli mekanigi taklit eder; SWING-1H konfig 2026-07-02) ----
INTERVAL = "1h"
GUN = 90
LOOKBACK = 50
MAXBAR = 120            # 120 bar = 5 gun ileri tarama (canli ACTIVE_SAAT ile uyumlu)
COOLDOWN_BAR = 12       # 12s (canli COOLDOWN_SAAT)
CONF_ATR = 0.5          # "kirilim onayi" girisi: seviyeden 0.5*ATR ote
CONF_PENCERE = 12       # onay icin en fazla 12 mum bekle
RR = 2.08

# ---- maliyet (KAYNAKLI: Binance USDⓈ-M VIP0, maker %0.02 / taker %0.05) ----
# https://www.binance.com/en/fee/futureFee  | defter.py ile AYNI model (per-leg).
# Varsayim: giris=taker, TP=maker, stop=taker; slippage sadece taker bacakta.
MAKER_FEE = 0.000200
TAKER_FEE = 0.000500
SLIPPAGE = 0.000200
BNB_CARPAN = 0.90       # 2026-07-06: kullanici Futures'ta BNB ile fee odemeyi aktifletti (defter.py ile ayni)


def _bacak(taker):
    return (TAKER_FEE * BNB_CARPAN + SLIPPAGE) if taker else (MAKER_FEE * BNB_CARPAN)

CONFIGS = [
    ("seviye-1.2",         "seviye", 1.2),
    ("seviye-1.8",         "seviye", 1.8),
    ("seviye-2.5 (CANLI)", "seviye", 2.5),
    ("kirilim-1.2",        "kirilim", 1.2),
    ("kirilim-1.8",        "kirilim", 1.8),
    ("kirilim-2.5",        "kirilim", 2.5),
]


def klines_history(symbol, interval, gun):
    per_day = {"5m": 288, "15m": 96, "1h": 24}[interval]
    hedef = gun * per_day
    out, end = [], None
    while len(out) < hedef:
        params = {"symbol": symbol, "interval": interval, "limit": 1500}
        if end:
            params["endTime"] = end
        raw = olcucu._get("/fapi/v1/klines", params)
        if not raw:
            break
        batch = [{"t": k[0], "o": float(k[1]), "h": float(k[2]),
                  "l": float(k[3]), "c": float(k[4])} for k in raw]
        out = batch + out
        end = raw[0][0] - 1
        if len(raw) < 1500:
            break
    return out[-hedef:]


def funding_serisi(symbol):
    """Funding gecmisi TAM KAPSAMA -> (zamanlar[], oranlar[]) sirali; yoksa bos.
    DUZELTME (2026-07-02): uc nokta limit=1000 istense de tek istekte ~200 kayit
    donduruyor -> startTime ile sayfalanmazsa pencerenin basi funding'siz kalir
    ve filtre adaylari SESSIZCE eler (ilk kosuda 180g == 90g cikma sebebi)."""
    try:
        start = int(datetime.now(timezone.utc).timestamp() * 1000) - (GUN + 3) * 86_400_000
        ts, fr, cur = [], [], start
        while True:
            raw = olcucu._get("/fapi/v1/fundingRate",
                              {"symbol": symbol, "startTime": cur, "limit": 1000})
            if not raw:
                break
            raw.sort(key=lambda x: x["fundingTime"])
            for r in raw:
                t = int(r["fundingTime"])
                if not ts or t > ts[-1]:
                    ts.append(t)
                    fr.append(float(r["fundingRate"]))
            nxt = int(raw[-1]["fundingTime"]) + 1
            if nxt <= cur or len(raw) < 2 or len(ts) > 20000:
                break
            cur = nxt
        return ts, fr
    except Exception:
        return [], []


def funding_at(ts_list, fr_list, t_ms):
    if not ts_list:
        return None
    idx = bisect.bisect_right(ts_list, t_ms) - 1
    return fr_list[idx] if idx >= 0 else None


def _funding_uygun(yon, f, th):
    """SHORT (long_squeeze) -> longlar kalabalik (funding yuksek);
    LONG (short_squeeze) -> shortlar kalabalik (funding dusuk)."""
    if f is None:
        return False
    return f >= th["long_crowded"] if yon == "SHORT" else f <= th["short_crowded"]


def _resolve(K, i_entry, yon, entry, stop, tp):
    for j in range(i_entry + 1, min(i_entry + 1 + MAXBAR, len(K))):
        hi, lo = K[j]["h"], K[j]["l"]
        if yon == "SHORT":
            if hi >= stop:
                return "stop", -1.0
            if lo <= tp:
                return "tp", RR
        else:
            if lo <= stop:
                return "stop", -1.0
            if hi >= tp:
                return "tp", RR
    return "zaman_asimi", 0.0


def _giris(K, i, yon, seviye, atr_val, mod):
    if mod == "seviye":
        return i, seviye
    if yon == "SHORT":
        e = seviye - CONF_ATR * atr_val
        for j in range(i + 1, min(i + 1 + CONF_PENCERE, len(K))):
            if K[j]["l"] <= e:
                return j, e
    else:
        e = seviye + CONF_ATR * atr_val
        for j in range(i + 1, min(i + 1 + CONF_PENCERE, len(K))):
            if K[j]["h"] >= e:
                return j, e
    return None, None


def _yeni_acc():
    return {ad: {y: {"tetik": 0, "kazanc": 0, "kayip": 0, "gross": 0.0, "net": 0.0}
                 for y in ("SHORT", "LONG")} for ad, _, _ in CONFIGS}


def _isle(K, i, yon, seviye, a, acc):
    """Bir aday icin tum config'leri simule et + acc'ye yaz."""
    for ad, mod, smul in CONFIGS:
        i_e, e = _giris(K, i, yon, seviye, a, mod)
        if i_e is None:
            continue
        risk = smul * a
        if yon == "SHORT":
            stop, tp = e + risk, e - RR * risk
        else:
            stop, tp = e - risk, e + RR * risk
        sonuc, gross = _resolve(K, i_e, yon, e, stop, tp)
        # per-leg: giris taker, cikis TP->maker / stop->taker
        cost = e * (_bacak(True) + _bacak(sonuc != "tp")) / risk if risk else 0.0
        d = acc[ad][yon]
        d["tetik"] += 1
        d["gross"] += gross
        d["net"] += gross - cost
        if sonuc == "tp":
            d["kazanc"] += 1
        elif sonuc == "stop":
            d["kayip"] += 1


def backtest_symbol(symbol, filtre=False):
    K = klines_history(symbol, INTERVAL, GUN)
    if len(K) < LOOKBACK + 30:
        return None
    ts_list, fr_list = funding_serisi(symbol) if filtre else ([], [])
    th = olcucu.get_thresholds(symbol)
    acc = _yeni_acc()
    son_short = son_long = -10 ** 9

    for i in range(LOOKBACK + 1, len(K) - 1):
        win = K[i - LOOKBACK:i]
        sl = min(k["l"] for k in win)
        sh = max(k["h"] for k in win)
        a = olcucu.atr(K[max(0, i - 15):i + 1])
        if not a or a <= 0:
            continue

        prev_sl = min(k["l"] for k in K[i - 1 - LOOKBACK:i - 1])
        if K[i]["l"] <= sl and K[i - 1]["l"] > prev_sl and i - son_short >= COOLDOWN_BAR:
            son_short = i
            if not (filtre and not _funding_uygun("SHORT", funding_at(ts_list, fr_list, K[i]["t"]), th)):
                _isle(K, i, "SHORT", sl, a, acc)

        prev_sh = max(k["h"] for k in K[i - 1 - LOOKBACK:i - 1])
        if K[i]["h"] >= sh and K[i - 1]["h"] < prev_sh and i - son_long >= COOLDOWN_BAR:
            son_long = i
            if not (filtre and not _funding_uygun("LONG", funding_at(ts_list, fr_list, K[i]["t"]), th)):
                _isle(K, i, "LONG", sh, a, acc)

    return acc


def _topla(hedef, kaynak):
    for ad in hedef:
        for y in ("SHORT", "LONG"):
            for k in hedef[ad][y]:
                hedef[ad][y][k] += kaynak[ad][y][k]


def _tablo(toplam, baslik):
    print("\n" + "=" * 74)
    print(f"  {baslik}")
    print("=" * 74)
    print(f"{'config':<22}{'tetik':>6}{'isabet':>8}{'grossR':>9}{'netR':>9}{'ortNetR':>9}")
    print("-" * 74)
    for ad, _, _ in CONFIGS:
        S, L = toplam[ad]["SHORT"], toplam[ad]["LONG"]
        tetik = S["tetik"] + L["tetik"]
        kaz = S["kazanc"] + L["kazanc"]
        kay = S["kayip"] + L["kayip"]
        gross = S["gross"] + L["gross"]
        net = S["net"] + L["net"]
        isabet = f"%{kaz / (kaz + kay) * 100:.0f}" if (kaz + kay) else "-"
        ortnet = net / tetik if tetik else 0.0
        print(f"{ad:<22}{tetik:>6}{isabet:>8}{gross:>+9.1f}{net:>+9.1f}{ortnet:>+9.2f}")


def _yon_kirilim(toplam, cfg_ad):
    print(f"\n  '{cfg_ad}' LONG/SHORT ayrimi (net R):")
    for y in ("SHORT", "LONG"):
        d = toplam[cfg_ad][y]
        g = d["kazanc"] + d["kayip"]
        isabet = f"%{d['kazanc'] / g * 100:.0f}" if g else "-"
        ortnet = d["net"] / d["tetik"] if d["tetik"] else 0.0
        print(f"    {y:<6} tetik {d['tetik']:>4} | isabet {isabet:>4} | netR {d['net']:>+7.1f} | ortNetR {ortnet:>+6.2f}")


def calistir(filtre, baslik):
    toplam = _yeni_acc()
    satir = []
    for s in olcucu.SYMBOLS:
        try:
            acc = backtest_symbol(s, filtre=filtre)
            if acc is None:
                satir.append(f"{s}: yetersiz veri")
                continue
            _topla(toplam, acc)
            n = sum(acc[CONFIGS[0][0]][y]["tetik"] for y in ("SHORT", "LONG"))
            satir.append(f"{s}: {n} tetik (CANLI cfg)")
        except Exception as e:
            satir.append(f"{s}: HATA {type(e).__name__}: {str(e)[:60]}")
    print("  " + " | ".join(satir))
    _tablo(toplam, baslik)
    _yon_kirilim(toplam, "seviye-2.5 (CANLI)")
    return toplam


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print("=" * 74)
    print(f"  BACKTEST (Option A) | {INTERVAL} son {GUN}g | R/R {RR} | "
          f"fee maker%{MAKER_FEE*100:.3f}/taker%{TAKER_FEE*100:.3f}+slip | " +
          datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))
    print(f"  coinler: {', '.join(olcucu.SYMBOLS)}")
    print("=" * 74)

    print("\n>>> 1) FILTRESIZ (her swing testi):")
    calistir(filtre=False, baslik="FILTRESIZ — config karsilastirmasi (net = komisyon dahil)")

    print("\n\n>>> 2) FUNDING-FILTRELI (kalabalik taraf sarti):")
    calistir(filtre=True, baslik="FUNDING-FILTRELI — config karsilastirmasi (net)")

    print("\n" + "=" * 74)
    print("OKUMA: 'ortNetR' = islem basi net R (komisyon dahil). En yuksek = en iyi.")
    print("  - Filtresiz: cok ornek, mutlak deger yanli ama config SIRASI gecerli.")
    print("  - Funding-filtreli: canli setup'a yakin alt-kume (yaklasik).")
    print("  - Yeni/az-gecmisli coinlerde funding-filtresi yaniltici olabilir (kalibrasyon penceresi kisa).")


if __name__ == "__main__":
    main()
