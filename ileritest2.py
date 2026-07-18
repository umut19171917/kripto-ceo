"""
ileritest2.py — WALK-FORWARD deney 2: TREND HIZALAMA + GENIS-STOP/ZAMAN-ASIMI CIKIS
================================================================================
Gerekce (2026-07-17, kullanici onayi): canli sicil tahlili iki hipotez uretti:
  (1) TREND filtresi — islem yonu coin'in KENDI 50g (1200x1h) ortalamasiyla ayni
      yonde olsun (LONG sadece fiyat ortalamanin USTUNDEyse, SHORT sadece ALTINDA).
      Kaynak bulgu: 19 kapali islemde LONG 3/11 + SHORT 0/8, iki yon birden
      kaybediyor; akintiya karsi islemler suphe altinda.
  (2) GENIS STOP + zaman-asimi cikisi — stop 5.0/7.5 ATR (canli 2.5), TP1 ayni
      (5.2 ATR), 120 bar dolunca SON FIYATTAN kapat (mark-to-market).
      Kaynak bulgu: stop-esneklik analizi (2026-07-16): 3x stopta toplam -9.81R
      -> -0.95R; ama o analiz gecmise bakarak yapildi = tek basina KANIT DEGIL.

Bu arac ileritest.py'nin walk-forward iskeletini kullanir (esikler SADECE fold
oncesi KAL_GUN'den; test gorulmemis dilimde) — B1'in in-sample tuzagini kirar.

ileritest.py'den FARKLAR (bilincli):
  - zaman_asimi = MARK-TO-MARKET (0R degil). Genis-stop stratejisinin ana cikisi
    bu; 0R saymak stratejiyi olcusuz birakirdi. Dar-stop configlerde za nadir ->
    B1 sayilariyla kabaca karsilastirilabilir kalir.
  - basis modlari YOK (o hipotez B1'de olculdu, bekliyor); yerine trend modlari.
  - TP mesafesi configte AYRIK (tp_atr): genis configlerde TP sabit 5.2 ATR
    kalir (odul kucuk R olur: 5.2/7.5=0.69R) — dunku analizin birebir mekanigi.

Calistirma: venv\\Scripts\\python.exe ileritest2.py
Canli sisteme DOKUNMAZ; Telegram'a/sicile YAZMAZ; sadece okur+hesaplar+basar.
"""

import sys
from datetime import datetime, timezone

import olcucu
import backtest
import ileritest  # funding_serisi_gun, _dilim (walk-forward veri iskeleti)
from kalibrasyon import percentile

TOPLAM_GUN = ileritest.TOPLAM_GUN     # 540
KAL_GUN = ileritest.KAL_GUN           # 166
ADIM_GUN = ileritest.ADIM_GUN         # 30
GUN_MS = ileritest.GUN_MS

TREND_BAR = 1200                      # 50 gun x 24 (rejim.py'nin 50g SMA ruhu, coin-bazli)
MODLAR = ("filtresiz", "funding", "trend", "funding+trend")
CANLI_CFG = "seviye-2.5 (CANLI)"
ODAK_CFGLER = (CANLI_CFG, "genis-7.5")

# (ad, giris_mod, stop_atr, tp_atr) — tp_atr None ise TP = RR*stop (eski davranis)
CONFIGS = [
    ("seviye-1.2",         "seviye",  1.2, None),
    ("seviye-1.8",         "seviye",  1.8, None),
    ("seviye-2.5 (CANLI)", "seviye",  2.5, None),
    ("kirilim-1.2",        "kirilim", 1.2, None),
    ("kirilim-1.8",        "kirilim", 1.8, None),
    ("kirilim-2.5",        "kirilim", 2.5, None),
    ("genis-5.0",          "seviye",  5.0, 5.2),
    ("genis-7.5",          "seviye",  7.5, 5.2),
]


def fold_esik_funding(fts, ffr, fold_start_ms):
    """Funding esigi SADECE [fold_start - KAL_GUN, fold_start) verisinden."""
    f = sorted(ileritest._dilim(fts, ffr, fold_start_ms - KAL_GUN * GUN_MS, fold_start_ms))
    return ({"long_crowded": percentile(f, 85), "short_crowded": percentile(f, 15)}
            if len(f) >= 100 else None)


def _resolve_mtm(K, i_entry, yon, entry, stop, tp, risk):
    """backtest._resolve + zaman_asiminda MARK-TO-MARKET (son bar kapanisiyla R)."""
    son = min(i_entry + backtest.MAXBAR, len(K) - 1)
    for j in range(i_entry + 1, son + 1):
        hi, lo = K[j]["h"], K[j]["l"]
        if yon == "SHORT":
            if hi >= stop:
                return "stop", -1.0
            if lo <= tp:
                return "tp", abs(entry - tp) / risk
        else:
            if lo <= stop:
                return "stop", -1.0
            if hi >= tp:
                return "tp", abs(tp - entry) / risk
    c = K[son]["c"]
    return "za", ((entry - c) if yon == "SHORT" else (c - entry)) / risk


def _yeni_acc(n_fold):
    return {m: [{ad: {y: {"tetik": 0, "kazanc": 0, "kayip": 0, "za": 0,
                          "gross": 0.0, "net": 0.0}
                      for y in ("SHORT", "LONG")} for ad, _, _, _ in CONFIGS}
                for _ in range(n_fold)] for m in MODLAR}


def _isle(K, i, yon, seviye, a, hedef):
    for ad, mod, smul, tp_atr in CONFIGS:
        i_e, e = backtest._giris(K, i, yon, seviye, a, mod)
        if i_e is None:
            continue
        risk = smul * a
        tp_mesafe = (tp_atr * a) if tp_atr else (backtest.RR * risk)
        if yon == "SHORT":
            stop, tp = e + risk, e - tp_mesafe
        else:
            stop, tp = e - risk, e + tp_mesafe
        if min(stop, tp) <= 0 or min(e, risk) <= 0:
            continue   # dejenere plan (canli veto ile ayni ruh)
        sonuc, gross = _resolve_mtm(K, i_e, yon, e, stop, tp, risk)
        cost = e * (backtest._bacak(True) + backtest._bacak(sonuc != "tp")) / risk
        d = hedef[ad][yon]
        d["tetik"] += 1
        d["gross"] += gross
        d["net"] += gross - cost
        if sonuc == "tp":
            d["kazanc"] += 1
        elif sonuc == "stop":
            d["kayip"] += 1
        else:
            d["za"] += 1


def sym_kosusu(symbol, n_fold, t_ilk_fold, acc):
    K = backtest.klines_history(symbol, "1h", TOPLAM_GUN)
    if len(K) < (KAL_GUN + ADIM_GUN) * 24:
        return f"{symbol}: yetersiz veri ({len(K)} bar)"
    fts, ffr = ileritest.funding_serisi_gun(symbol, TOPLAM_GUN)
    esikler = [fold_esik_funding(fts, ffr, t_ilk_fold + f * ADIM_GUN * GUN_MS)
               for f in range(n_fold)]

    # 50g SMA on-toplami: sma(i) = [i-TREND_BAR, i) kapanislari — SADECE gecmis bar
    pre = [0.0]
    for k in K:
        pre.append(pre[-1] + k["c"])

    def sma(i):
        return (pre[i] - pre[i - TREND_BAR]) / TREND_BAR if i >= TREND_BAR else None

    LB, CD = backtest.LOOKBACK, backtest.COOLDOWN_BAR
    son_short = son_long = -10 ** 9
    n_aday = n_trend_yok = 0
    for i in range(LB + 1, len(K) - 1):
        f = int((K[i]["t"] - t_ilk_fold) // (ADIM_GUN * GUN_MS))
        if f < 0 or f >= n_fold:
            continue
        win = K[i - LB:i]
        sl = min(k["l"] for k in win)
        sh = max(k["h"] for k in win)
        a = olcucu.atr(K[max(0, i - 15):i + 1])
        if not a or a <= 0:
            continue
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
            s50 = sma(i)
            if s50 is None:
                n_trend_yok += 1
                trend_ok = False   # trend tanimsizsa trend-modu islemi almaz (durust)
            else:
                trend_ok = (K[i]["c"] < s50) if yon == "SHORT" else (K[i]["c"] > s50)
            fv = backtest.funding_at(fts, ffr, K[i]["t"])
            f_ok = ileritest._uygun(yon, fv, esikler[f])
            gecti = {"filtresiz": True, "funding": f_ok,
                     "trend": trend_ok, "funding+trend": f_ok and trend_ok}
            for m in MODLAR:
                if gecti[m]:
                    _isle(K, i, yon, seviye, a, acc[m][f])
    ek = f" | {n_trend_yok} adayda trend tanimsiz" if n_trend_yok else ""
    return f"{symbol}: {n_aday} aday | funding {len(ffr)} kayit{ek}"


# ============================== rapor ==============================
def _cfg_toplam(acc, m, ad, n_fold):
    t = {"tetik": 0, "kazanc": 0, "kayip": 0, "za": 0, "gross": 0.0, "net": 0.0}
    poz_fold = 0
    for f in range(n_fold):
        fold_net = 0.0
        fold_n = 0
        for y in ("SHORT", "LONG"):
            d = acc[m][f][ad][y]
            for k in t:
                t[k] += d[k]
            fold_net += d["net"]
            fold_n += d["tetik"]
        if fold_n and fold_net > 0:
            poz_fold += 1
    return t, poz_fold


def rapor(acc, n_fold, t_ilk_fold, btc_k):
    print("\n" + "=" * 88)
    print("  TOPLAM OOS — mod x config | netR komisyon dahil | za=zaman-asimi (MTM) | pozF=pozitif fold")
    print("=" * 88)
    for m in MODLAR:
        print(f"\n  MOD: {m}")
        print(f"  {'config':<22}{'tetik':>6}{'isabet':>8}{'za':>5}{'grossR':>9}{'netR':>9}{'ortNetR':>9}{'pozF':>6}")
        for ad, _, _, _ in CONFIGS:
            t, pf = _cfg_toplam(acc, m, ad, n_fold)
            g = t["kazanc"] + t["kayip"]
            isb = f"%{t['kazanc'] / g * 100:.0f}" if g else "-"
            ort = t["net"] / t["tetik"] if t["tetik"] else 0.0
            print(f"  {ad:<22}{t['tetik']:>6}{isb:>8}{t['za']:>5}{t['gross']:>+9.1f}"
                  f"{t['net']:>+9.1f}{ort:>+9.2f}{pf:>4}/{n_fold}")

    for cfg in ODAK_CFGLER:
        print("\n" + "=" * 88)
        print(f"  FOLD CIZELGESI — '{cfg}' (n / netR) | btc% = dilimde BTC degisimi")
        print("=" * 88)
        print(f"  {'dilim basi':<12}{'btc%':>7} | " + " | ".join(f"{m:>16}" for m in MODLAR))
        for f in range(n_fold):
            t0 = t_ilk_fold + f * ADIM_GUN * GUN_MS
            t1 = t0 + ADIM_GUN * GUN_MS
            ks = [k for k in btc_k if t0 <= k["t"] < t1]
            btc = (ks[-1]["c"] - ks[0]["o"]) / ks[0]["o"] * 100 if ks else 0.0
            tarih = datetime.fromtimestamp(t0 / 1000, timezone.utc).strftime("%Y-%m-%d")
            hucre = []
            for m in MODLAR:
                n = sum(acc[m][f][cfg][y]["tetik"] for y in ("SHORT", "LONG"))
                net = sum(acc[m][f][cfg][y]["net"] for y in ("SHORT", "LONG"))
                hucre.append(f"{n:>4} /{net:>+7.1f}")
            print(f"  {tarih:<12}{btc:>+6.1f}% | " + " | ".join(f"{h:>16}" for h in hucre))

        print(f"\n  LONG/SHORT ayrimi — '{cfg}':")
        for m in MODLAR:
            parca = []
            for y in ("SHORT", "LONG"):
                t = {"tetik": 0, "kazanc": 0, "kayip": 0, "net": 0.0}
                for f in range(n_fold):
                    for k in t:
                        t[k] += acc[m][f][cfg][y][k]
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
    t_ilk_fold = simdi - TOPLAM_GUN * GUN_MS + KAL_GUN * GUN_MS
    n_fold = (TOPLAM_GUN - KAL_GUN) // ADIM_GUN

    print("=" * 88)
    print(f"  ILERITEST-2 (trend + genis-stop) | 1h | ufuk {TOPLAM_GUN}g | kalibrasyon {KAL_GUN}g"
          f" | dilim {ADIM_GUN}g | {n_fold} fold")
    print(f"  za=MTM (0R degil!) | trend = coin 50g SMA (1200x1h, sadece gecmis) | "
          + datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))
    print(f"  coinler: {', '.join(olcucu.SYMBOLS)}")
    print("=" * 88)

    acc = _yeni_acc(n_fold)
    btc_k = None
    for s in olcucu.SYMBOLS:
        try:
            if s == "BTCUSDT":
                btc_k = backtest.klines_history("BTCUSDT", "1h", TOPLAM_GUN)
            msg = sym_kosusu(s, n_fold, t_ilk_fold, acc)
        except Exception as e:
            msg = f"{s}: HATA {type(e).__name__}: {str(e)[:70]}"
        print("  " + msg, flush=True)

    rapor(acc, n_fold, t_ilk_fold, btc_k or [])
    print("\nOKUMA: (1) za artik MTM — dar-stop configlerde nadir, genis configlerde ANA cikis.")
    print("(2) pozF = kac fold'da net pozitif; tek buyuk toplamdan daha onemli (B1 dersi).")
    print("(3) Seviye-dolum varsayimi surer; mutlak degil GORELI oku. Canli parametre")
    print("degisikligi bu rapora degil K2'ye (30 kapali swing) baglidir.")


if __name__ == "__main__":
    main()
