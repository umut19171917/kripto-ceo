"""
ileritest.py — WALK-FORWARD dogrulama (B1): esikler SADECE gecmisten, test ILERIDE
================================================================================
Amac: backtest.py bulgulari IN-SAMPLE idi (esikler ve config ayni veriden). Bu
arac canli isleyisi taklit eder: her 30 gunluk test diliminden ONCE, esikler o
dilimin oncesindeki KAL_GUN'luk pencereden hesaplanir (canlinin 12 saatte bir
kendini kalibre etmesinin kaba simulasyonu; dilim icinde donuk = muhafazakar).

Ayrica filtre adaylarini ESLI test eder (ayni aday sinyal kumesi uzerinde):
  - filtresiz          : tum swing kirilim adaylari
  - funding            : kalabalik-taraf sarti (canli yaklasimi)
  - basis              : vadeli prim/iskonto persentil sarti (HIPOTEZ — canlide yok)
  - funding+basis      : ikisi birden

SINIRLAR (durust):
  - Seviye-dolum varsayimi: fitil degince dolmus sayilir (backtest ile ayni).
  - zaman_asimi = 0R (canli defter mark-to-market yapar; burada eski basitlestirme).
  - Tam sikisma skoru (OI) gecmise yok -> funding/basis yaklasik vekil.
  - top_ls TEST EDILEMEZ: Binance /futures/data/* ~30 gun tutar (probe 2026-07-04:
    60g istegi HTTP 400). basis ISTISNA: derin gecmisi var (probe: 600g+ mevcut).

Calistirma: venv\\Scripts\\python.exe ileritest.py
Canli sisteme DOKUNMAZ; sadece okur + hesaplar + rapor basar.
"""

import sys
import bisect
from datetime import datetime, timezone

import olcucu
import backtest
from kalibrasyon import percentile

# ---- pencere parametreleri ----
TOPLAM_GUN = 540    # veri ufku (ilk kalibrasyon penceresi dahil)
KAL_GUN = 166       # esik penceresi = canli kalibrasyon (~500 settlement @8s, A2 sonrasi)
ADIM_GUN = 30       # her test dilimi (fold)
GUN_MS = 86_400_000

MODLAR = ("filtresiz", "funding", "basis", "funding+basis")
CANLI_CFG = "seviye-2.5 (CANLI)"


# ============================== veri cekiciler ==============================
def funding_serisi_gun(symbol, gun):
    """backtest.funding_serisi'nin ufku parametreli hali (startTime sayfalamali)."""
    start = int(datetime.now(timezone.utc).timestamp() * 1000) - (gun + 3) * GUN_MS
    ts, fr, cur = [], [], start
    while True:
        raw = olcucu._get("/fapi/v1/fundingRate",
                          {"symbol": symbol, "startTime": cur, "limit": 1000})
        if not raw:
            break
        raw.sort(key=lambda x: int(x["fundingTime"]))
        yeni = False
        for r in raw:
            t = int(r["fundingTime"])
            if not ts or t > ts[-1]:
                ts.append(t)
                fr.append(float(r["fundingRate"]))
                yeni = True
        if not yeni or len(raw) < 2 or len(ts) > 30000:
            break
        cur = ts[-1] + 1
    return ts, fr


def basis_serisi(symbol, gun):
    """1h basisRate serisi. Sayfalama ACIK pencerelerle (20g = 480 kayit < limit 500);
    startTime-only davranisi belgesiz oldugundan her istekte start+end verilir."""
    simdi = int(datetime.now(timezone.utc).timestamp() * 1000)
    start = simdi - (gun + 3) * GUN_MS
    adim = 20 * GUN_MS
    ts, br, cur = [], [], start
    while cur < simdi:
        try:
            raw = olcucu._get("/futures/data/basis",
                              {"pair": symbol, "contractType": "PERPETUAL", "period": "1h",
                               "limit": 500, "startTime": cur,
                               "endTime": min(cur + adim, simdi) - 1})
        except Exception:
            raw = []   # tek pencere hatasi seriyi oldurmesin
        for r in sorted(raw, key=lambda x: int(x["timestamp"])):
            t = int(r["timestamp"])
            v = r.get("basisRate")
            if v is None or (ts and t <= ts[-1]):
                continue
            ts.append(t)
            br.append(float(v))
        cur += adim
    return ts, br


# ============================== fold esikleri ==============================
def _dilim(ts, vals, t0, t1):
    i0 = bisect.bisect_left(ts, t0)
    i1 = bisect.bisect_left(ts, t1)
    return vals[i0:i1]

def fold_esikleri(fts, ffr, bts, bbr, fold_start_ms):
    """Esikler SADECE [fold_start - KAL_GUN, fold_start) verisinden (sizinti yok)."""
    t0 = fold_start_ms - KAL_GUN * GUN_MS
    f = sorted(_dilim(fts, ffr, t0, fold_start_ms))
    b = sorted(_dilim(bts, bbr, t0, fold_start_ms))
    th_f = {"long_crowded": percentile(f, 85), "short_crowded": percentile(f, 15),
            "n": len(f)} if len(f) >= 100 else None
    th_b = {"long_crowded": percentile(b, 85), "short_crowded": percentile(b, 15),
            "n": len(b)} if len(b) >= 500 else None
    return th_f, th_b


def _uygun(yon, deger, th):
    """Kalabalik-taraf sarti (funding ve basis icin ayni sekil)."""
    if th is None or deger is None:
        return False
    return deger >= th["long_crowded"] if yon == "SHORT" else deger <= th["short_crowded"]


# ============================== simulasyon ==============================
def _yeni_acc(n_fold):
    return {m: [{ad: {y: {"tetik": 0, "kazanc": 0, "kayip": 0, "gross": 0.0, "net": 0.0}
                      for y in ("SHORT", "LONG")} for ad, _, _ in backtest.CONFIGS}
                for _ in range(n_fold)] for m in MODLAR}


def _isle(K, i, yon, seviye, a, hedef):
    """backtest._isle esdegeri; hedef = acc[mod][fold]."""
    for ad, mod, smul in backtest.CONFIGS:
        i_e, e = backtest._giris(K, i, yon, seviye, a, mod)
        if i_e is None:
            continue
        risk = smul * a
        if yon == "SHORT":
            stop, tp = e + risk, e - backtest.RR * risk
        else:
            stop, tp = e - risk, e + backtest.RR * risk
        sonuc, gross = backtest._resolve(K, i_e, yon, e, stop, tp)
        cost = e * (backtest._bacak(True) + backtest._bacak(sonuc != "tp")) / risk if risk else 0.0
        d = hedef[ad][yon]
        d["tetik"] += 1
        d["gross"] += gross
        d["net"] += gross - cost
        if sonuc == "tp":
            d["kazanc"] += 1
        elif sonuc == "stop":
            d["kayip"] += 1


def sym_kosusu(symbol, n_fold, t_ilk_fold, acc):
    K = backtest.klines_history(symbol, "1h", TOPLAM_GUN)
    if len(K) < (KAL_GUN + ADIM_GUN) * 24:
        return f"{symbol}: yetersiz veri ({len(K)} bar)"
    fts, ffr = funding_serisi_gun(symbol, TOPLAM_GUN)
    bts, bbr = basis_serisi(symbol, TOPLAM_GUN)
    esikler = [fold_esikleri(fts, ffr, bts, bbr, t_ilk_fold + f * ADIM_GUN * GUN_MS)
               for f in range(n_fold)]

    LB, CD = backtest.LOOKBACK, backtest.COOLDOWN_BAR
    son_short = son_long = -10 ** 9
    n_aday = 0
    for i in range(LB + 1, len(K) - 1):
        f = int((K[i]["t"] - t_ilk_fold) // (ADIM_GUN * GUN_MS))
        if f < 0 or f >= n_fold:
            continue   # ilk kalibrasyon donemi (veya ufuk disi)
        win = K[i - LB:i]
        sl = min(k["l"] for k in win)
        sh = max(k["h"] for k in win)
        a = olcucu.atr(K[max(0, i - 15):i + 1])
        if not a or a <= 0:
            continue
        th_f, th_b = esikler[f]
        adaylar = []
        prev_sl = min(k["l"] for k in K[i - 1 - LB:i - 1])
        if K[i]["l"] <= sl and K[i - 1]["l"] > prev_sl and i - son_short >= CD:
            son_short = i
            adaylar.append(("SHORT", sl))
        prev_sh = max(k["h"] for k in K[i - 1 - LB:i - 1])
        if K[i]["h"] >= sh and K[i - 1]["h"] < prev_sh and i - son_long >= CD:
            son_long = i
            adaylar.append(("LONG", sh))
        for yon, seviye in adaylar:
            n_aday += 1
            fv = backtest.funding_at(fts, ffr, K[i]["t"])
            bv = backtest.funding_at(bts, bbr, K[i]["t"])   # ayni "son deger" mantigi
            gecti = {"filtresiz": True,
                     "funding": _uygun(yon, fv, th_f),
                     "basis": _uygun(yon, bv, th_b),
                     "funding+basis": _uygun(yon, fv, th_f) and _uygun(yon, bv, th_b)}
            for m in MODLAR:
                if gecti[m]:
                    _isle(K, i, yon, seviye, a, acc[m][f])
    return f"{symbol}: {n_aday} aday | funding {len(ffr)} kayit | basis {len(bbr)} kayit"


# ============================== rapor ==============================
def _fold_toplam(acc_m, f, cfg):
    S = acc_m[f][cfg]["SHORT"]
    L = acc_m[f][cfg]["LONG"]
    return (S["tetik"] + L["tetik"], S["net"] + L["net"])


def rapor(acc, n_fold, t_ilk_fold, btc_k):
    print("\n" + "=" * 78)
    print("  TOPLAM OOS (tum fold'lar) — mod x config, netR = komisyon dahil")
    print("=" * 78)
    for m in MODLAR:
        print(f"\n  MOD: {m}")
        print(f"  {'config':<22}{'tetik':>6}{'isabet':>8}{'grossR':>9}{'netR':>9}{'ortNetR':>9}")
        for ad, _, _ in backtest.CONFIGS:
            t = {"tetik": 0, "kazanc": 0, "kayip": 0, "gross": 0.0, "net": 0.0}
            for f in range(n_fold):
                for y in ("SHORT", "LONG"):
                    for k in t:
                        t[k] += acc[m][f][ad][y][k]
            isb = f"%{t['kazanc'] / (t['kazanc'] + t['kayip']) * 100:.0f}" if (t['kazanc'] + t['kayip']) else "-"
            ort = t["net"] / t["tetik"] if t["tetik"] else 0.0
            print(f"  {ad:<22}{t['tetik']:>6}{isb:>8}{t['gross']:>+9.1f}{t['net']:>+9.1f}{ort:>+9.2f}")

    # CANLI config: fold zaman cizelgesi (tutarlilik) + BTC rejim etiketi
    print("\n" + "=" * 78)
    print(f"  FOLD CIZELGESI — '{CANLI_CFG}' (n / netR) | btc% = dilimde BTC degisimi")
    print("=" * 78)
    print(f"  {'dilim basi':<12}{'btc%':>7} | " + " | ".join(f"{m:>16}" for m in MODLAR))
    for f in range(n_fold):
        t0 = t_ilk_fold + f * ADIM_GUN * GUN_MS
        t1 = t0 + ADIM_GUN * GUN_MS
        ks = [k for k in btc_k if t0 <= k["t"] < t1]
        btc = (ks[-1]["c"] - ks[0]["o"]) / ks[0]["o"] * 100 if ks else 0.0
        tarih = datetime.fromtimestamp(t0 / 1000, timezone.utc).strftime("%Y-%m-%d")
        hucre = []
        for m in MODLAR:
            n, net = _fold_toplam(acc[m], f, CANLI_CFG)
            hucre.append(f"{n:>4} /{net:>+7.1f}")
        print(f"  {tarih:<12}{btc:>+6.1f}% | " + " | ".join(f"{h:>16}" for h in hucre))

    # LONG/SHORT ayrimi (CANLI config, mod bazinda, tum fold toplami)
    print("\n  LONG/SHORT ayrimi — '" + CANLI_CFG + "':")
    for m in MODLAR:
        parca = []
        for y in ("SHORT", "LONG"):
            t = {"tetik": 0, "kazanc": 0, "kayip": 0, "net": 0.0}
            for f in range(n_fold):
                for k in t:
                    t[k] += acc[m][f][CANLI_CFG][y][k]
            g = t["kazanc"] + t["kayip"]
            isb = f"%{t['kazanc'] / g * 100:.0f}" if g else "-"
            ort = t["net"] / t["tetik"] if t["tetik"] else 0.0
            parca.append(f"{y} n={t['tetik']} isabet {isb} ortNet {ort:+.2f}")
        print(f"    {m:<16}: " + " | ".join(parca))


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    simdi = int(datetime.now(timezone.utc).timestamp() * 1000)
    t_veri_basi = simdi - TOPLAM_GUN * GUN_MS
    t_ilk_fold = t_veri_basi + KAL_GUN * GUN_MS
    n_fold = (TOPLAM_GUN - KAL_GUN) // ADIM_GUN

    print("=" * 78)
    print(f"  ILERITEST (walk-forward) | 1h | ufuk {TOPLAM_GUN}g | kalibrasyon {KAL_GUN}g "
          f"| dilim {ADIM_GUN}g | {n_fold} fold")
    print(f"  esikler her dilimde SADECE onceki {KAL_GUN}g'den (sizinti yok) | "
          + datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))
    print(f"  coinler: {', '.join(olcucu.SYMBOLS)}")
    print("=" * 78)

    acc = _yeni_acc(n_fold)
    btc_k = None
    for s in olcucu.SYMBOLS:
        try:
            msg = sym_kosusu(s, n_fold, t_ilk_fold, acc)
            if s == "BTCUSDT":
                btc_k = backtest.klines_history("BTCUSDT", "1h", TOPLAM_GUN)
        except Exception as e:
            msg = f"{s}: HATA {type(e).__name__}: {str(e)[:70]}"
        print("  " + msg)

    rapor(acc, n_fold, t_ilk_fold, btc_k or [])
    print("\nOKUMA: fold'lar goruLMEMIS donemde islem yapar; poz. ortNetR'nin fold'lar")
    print("arasi TUTARLILIGI, tek toplam sayidan daha onemli. zaman_asimi=0R basitlestirmesi")
    print("ve seviye-dolum varsayimi gecerli — mutlak degil, GORELI oku.")


if __name__ == "__main__":
    main()
