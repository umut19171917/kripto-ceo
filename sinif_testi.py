"""
sinif_testi.py — COIN SINIFI: AYNI SINYAL, FARKLI EVREN (2026-08-11)
================================================================================
KAPATILAN SORU (bekleyenler defteri, madde 0 — "MUHTEMELEN EN ONEMLI MADDE"):
2026-07-31'de canli sicilde 27 KAT fark olculmustu:
    cekirdek 11 major  -0.794R/islem  (18 islem)
    radar genis evren  -0.029R/islem  (56 islem)
ve "belki majorlerde kirilim kaliplari yutuluyor, ince coinlerde calisiyor"
hipotezi kuruldu.

⚠ O KARSILASTIRMA CIFT DEGISKENLI (2026-08-11'de kodda dogrulandi):
    ana sicil : sikisma skoru >= 70 -> seviye kirilimi plani (2.5 ATR stop, RR>=2)
    radar     : |24s degisim| >= %20 VE hacim >= 30M  (VEYA %8/30dk)
Iki sicil AYNI sinyali kullanmiyor. Hem SINYAL hem COIN SINIFI birlikte
degismis -> farkin coin sinifindan geldigi SOYLENEMEZ. Hipotez cürümüs degil,
FIILEN HIC TEST EDILMEMIS.

BU TEST tek degiskenli halidir: CANLI CONFIG sabit (seviye-2.5, lookback 50,
filtresiz — aday_testi.BAZ_CFG ile AYNI), degisen tek sey COIN SINIFI.

YONTEM: pencere BASINDA hacme gore siralanmis ilk 60 coin, 20'serli uc kademe
(BUYUK / ORTA / KUCUK). Liste pencere basinda SABITLENIR -> sinif atamasi
gelecege bakmaz. Walk-forward iskeleti aday_testi/ileritest ile AYNI (12 fold,
esikler yok — bu testte ogrenilen parametre zaten yok).

IDAM SARTLARI (kesitsel_test'ten devralindi, 5. sart dahil):
  1. Kademeler arasi fark GURULTU TABANINI (0.03R) asmali
  2. Fark her iki rejimde de ayni yonde olmali
  3. Fold'larin cogunda ayni yonde olmali
  4. Kademeye gore MONOTON olmali (buyuk -> orta -> kucuk duzenli degisim)
  5. En iyi 3 fold cikarilinca isaret korunmali (B1 yogunlasma dersi)

⚠ HAYATTA KALMA YANLILIGI: Binance yalniz bugun islem gorenleri veriyor;
pencere icinde delist olanlar yok. Kucuk kademe bundan EN COK etkilenen
kademedir -> kucuk kademe lehine cikan her sonuc UST SINIR'dir.

Calistirma: venv\\Scripts\\python.exe sinif_testi.py
Canliya DOKUNMAZ.
"""
import bisect
import statistics
import sys
import time
from datetime import datetime, timezone

import olcucu
import backtest
import ileritest
import ileritest2
import aday_testi
import fade_testi
import kesitsel_test

TOPLAM_GUN = aday_testi.TOPLAM_GUN      # 540
KAL_GUN = aday_testi.KAL_GUN            # 166
ADIM_GUN = aday_testi.ADIM_GUN          # 30
GUN_MS = aday_testi.GUN_MS
LB = aday_testi.BAZ_LOOKBACK            # 50 (canli)

KADEME_N = 20                           # kademe basina coin
KADEMELER = ["BUYUK (1-20)", "ORTA (21-40)", "KUCUK (41-60)"]
GURULTU = 0.03                          # R — 2026-07-27 olcumu


def evren_kur():
    """Pencere BASINDAKI hacme gore ilk 3*KADEME_N coin -> {kademe: [sym]}.
    Gunluk onbellek (kesitsel_test) kullanilir; siralama penceresi pencere
    basindan ONCEKI 30 gun -> gelecege bakmaz."""
    gunluk = kesitsel_test.veri_getir()
    tum = sorted({g for m in gunluk.values() for g in m})
    basla = tum[-1] - TOPLAM_GUN
    sirali = []
    for s, m in gunluk.items():
        hac = [m[g][1] for g in range(basla - 30, basla) if g in m]
        if len(hac) < 25 or basla not in m:
            continue
        sirali.append((s, statistics.median(hac)))
    sirali.sort(key=lambda x: -x[1])
    secim = sirali[:3 * KADEME_N]
    return {KADEMELER[i]: secim[i * KADEME_N:(i + 1) * KADEME_N] for i in range(3)}


def kosu(K, n_fold, t_ilk_fold, hucreler):
    """CANLI config ile bir sembolu gez; hucreler[fold][yon] doldur.
    Tetikleme mantigi aday_testi.kosu ile BIREBIR ayni (tek fark: hucre adresi)."""
    CD = backtest.COOLDOWN_BAR
    son_short = son_long = -10 ** 9
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
            aday_testi._isle(K, i, yon, seviye, a, hucreler[f][yon])


def topla(acc):
    t = aday_testi._yeni_hucre()
    for f in acc:
        for y in ("SHORT", "LONG"):
            for k in t:
                t[k] += f[y][k]
    return t


def _ort_r(t):
    return t["net"] / t["tetik"] if t["tetik"] else 0.0


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    simdi = int(datetime.now(timezone.utc).timestamp() * 1000)
    t_ilk_fold = simdi - TOPLAM_GUN * GUN_MS + KAL_GUN * GUN_MS
    n_fold = (TOPLAM_GUN - KAL_GUN) // ADIM_GUN

    print("=" * 100)
    print("  COIN SINIFI SINAVI — AYNI SINYAL, FARKLI EVREN (tek degisken)")
    print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} | 1h | "
          f"{TOPLAM_GUN}g | {n_fold} fold | config: seviye-2.5 lookback-50 (CANLI)")
    print("  ⚠ 2026-07-31'in 27 kat farki CIFT DEGISKENLIYDI (ana sicil=sikisma skoru,")
    print("    radar=%20/24s hareket). Bu test sinyali SABITLER, yalniz sinifi degistirir.")
    print("=" * 100)

    evren = evren_kur()
    print("\n  EVREN (pencere basindaki 30g medyan hacme gore):")
    for kad, liste in evren.items():
        ilk = ", ".join(s for s, _ in liste[:6])
        print(f"    {kad:<14} medyan hacim ${statistics.median([v for _, v in liste])/1e6:>7.1f}M"
              f"  | {ilk} ...")

    acc = {kad: [{y: aday_testi._yeni_hucre() for y in ("SHORT", "LONG")}
                 for _ in range(n_fold)] for kad in KADEMELER}
    per_sym = {}
    print(f"\n  saatlik veri cekiliyor ({3*KADEME_N} sembol; onbellekli olanlar aninda) ...")
    for kad, liste in evren.items():
        for s, _v in liste:
            try:
                K = fade_testi.fiyat_getir(s)
            except Exception as e:
                print(f"    {s}: HATA {type(e).__name__} - atlandi", flush=True)
                continue
            if len(K) < (KAL_GUN + ADIM_GUN) * 24:
                print(f"    {s}: yetersiz gecmis ({len(K)} bar) - atlandi", flush=True)
                continue
            tek = [{y: aday_testi._yeni_hucre() for y in ("SHORT", "LONG")}
                   for _ in range(n_fold)]
            kosu(K, n_fold, t_ilk_fold, tek)
            for f in range(n_fold):
                for y in ("SHORT", "LONG"):
                    for k in acc[kad][f][y]:
                        acc[kad][f][y][k] += tek[f][y][k]
            per_sym[s] = (kad, topla(tek))
            time.sleep(1.5)          # agirlik limiti (klines limit=1500 -> agirlik 10)
        print(f"    {kad} tamam", flush=True)

    # ---------- ana tablo ----------
    print("\n" + "=" * 100)
    print("  KADEME KARSILASTIRMASI — netR komisyon dahil | ortNetR = islem basina")
    print("=" * 100)
    print(f"  {'kademe':<16}{'coin':>6}{'tetik':>8}{'isabet':>9}{'grossR':>10}"
          f"{'netR':>10}{'ortNetR':>10}{'pozFold':>9}")
    ort = {}
    for kad in KADEMELER:
        t = topla(acc[kad])
        g = t["kazanc"] + t["kayip"]
        isb = f"%{t['kazanc']/g*100:.0f}" if g else "-"
        poz = sum(1 for f in acc[kad]
                  if sum(f[y]["tetik"] for y in ("SHORT", "LONG"))
                  and sum(f[y]["net"] for y in ("SHORT", "LONG")) > 0)
        ort[kad] = _ort_r(t)
        n_coin = sum(1 for s, (k, _) in per_sym.items() if k == kad)
        print(f"  {kad:<16}{n_coin:>6}{t['tetik']:>8,}{isb:>9}{t['gross']:>+10.1f}"
              f"{t['net']:>+10.1f}{ort[kad]:>+10.3f}{poz:>7}/{n_fold}")

    fark = ort[KADEMELER[2]] - ort[KADEMELER[0]]      # kucuk - buyuk
    print(f"\n  KUCUK - BUYUK = {fark:+.3f}R/islem   (gurultu tabani {GURULTU}R)")
    yon = 1 if fark > 0 else -1

    # ---------- rejim ayrimi ----------
    print("\n" + "=" * 100)
    print("  REJIM AYRIMI — fark iki rejimde de ayni yonde mi?")
    print("=" * 100)
    # Rejim = BTC kendi 50g SMA'sinin ustunde mi (fade_testi ile AYNI tanim; bugunun
    # diger testleriyle tutarli olsun diye oynaklik degil BOGA/AYI secildi).
    rmap = fade_testi.trend_rejimi(fade_testi.fiyat_getir("BTCUSDT"))
    rts = sorted(rmap)
    fold_rej = []
    for f in range(n_fold):
        t0 = t_ilk_fold + f * ADIM_GUN * GUN_MS + ADIM_GUN * GUN_MS // 2
        i = bisect.bisect_right(rts, t0) - 1
        fold_rej.append(rmap[rts[i]] if i >= 0 else "AYI")
    print(f"  {'rejim':<10}{'fold':>6}" + "".join(f"{k[:12]:>14}" for k in KADEMELER)
          + f"{'kucuk-buyuk':>14}")
    rej_fark = {}
    for rej in ("BOGA", "AYI"):
        idx = [f for f in range(n_fold) if fold_rej[f] == rej]
        if not idx:
            continue
        satir = f"  {rej:<10}{len(idx):>6}"
        o = {}
        for kad in KADEMELER:
            t = topla([acc[kad][f] for f in idx])
            o[kad] = _ort_r(t)
            satir += f"{o[kad]:>+14.3f}"
        rej_fark[rej] = o[KADEMELER[2]] - o[KADEMELER[0]]
        print(satir + f"{rej_fark[rej]:>+14.3f}")

    # ---------- fold dokumu ----------
    print("\n" + "=" * 100)
    print("  FOLD DOKUMU — yogunlasma kontrolu (5. sart)")
    print("=" * 100)
    print(f"  {'dilim basi':<13}{'rejim':<8}" + "".join(f"{k[:12]:>14}" for k in KADEMELER)
          + f"{'kucuk-buyuk':>14}")
    fold_f = []
    for f in range(n_fold):
        t0 = t_ilk_fold + f * ADIM_GUN * GUN_MS
        tar = datetime.fromtimestamp(t0 / 1000, timezone.utc).strftime("%Y-%m-%d")
        satir = f"  {tar:<13}{fold_rej[f]:<8}"
        o = {}
        for kad in KADEMELER:
            t = topla([acc[kad][f]])
            o[kad] = _ort_r(t)
            satir += f"{o[kad]:>+14.3f}"
        d = o[KADEMELER[2]] - o[KADEMELER[0]]
        fold_f.append(d)
        print(satir + f"{d:>+14.3f}")

    fold_s = sorted(fold_f)
    top_f = sum(fold_f)
    kalan3 = sum(fold_s[:-3]) if yon > 0 else sum(fold_s[3:])
    ayni = sum(1 for d in fold_f if d * yon > 0)

    # ---------- sembol dagilimi ----------
    print("\n" + "=" * 100)
    print("  KADEME ICI DAGILIM — fark bir avuc coinden mi geliyor?")
    print("=" * 100)
    for kad in KADEMELER:
        v = sorted(((s, _ort_r(t)) for s, (k, t) in per_sym.items() if k == kad),
                   key=lambda x: -x[1])
        if not v:
            continue
        poz = sum(1 for _, r in v if r > 0)
        print(f"  {kad:<16} {poz}/{len(v)} coin pozitif | en iyi {v[0][0]} {v[0][1]:+.3f}"
              f" | medyan {statistics.median([r for _, r in v]):+.3f}"
              f" | en kotu {v[-1][0]} {v[-1][1]:+.3f}")

    # ---------- idam karari ----------
    print("\n" + "=" * 100)
    print("  IDAM KARARI")
    print("=" * 100)
    monoton = (ort[KADEMELER[0]] < ort[KADEMELER[1]] < ort[KADEMELER[2]]) or \
              (ort[KADEMELER[0]] > ort[KADEMELER[1]] > ort[KADEMELER[2]])
    k1 = abs(fark) > GURULTU
    k2 = len(rej_fark) == 2 and all(v * yon > 0 for v in rej_fark.values())
    k3 = ayni > n_fold / 2
    k4 = monoton
    k5 = kalan3 * yon > 0
    for ad, ok, detay in (
            ("1. gurultu tabanini asiyor", k1, f"|{fark:+.3f}| vs {GURULTU}R"),
            ("2. iki rejimde ayni yon", k2,
             " / ".join(f"{r} {v:+.3f}" for r, v in rej_fark.items())),
            ("3. fold'larin cogunda", k3, f"{ayni}/{n_fold}"),
            ("4. kademeye gore monoton", k4,
             " -> ".join(f"{ort[k]:+.3f}" for k in KADEMELER)),
            ("5. en iyi 3 foldsuz ayakta", k5, f"toplam {top_f:+.3f} -> {kalan3:+.3f}")):
        print(f"  {'GECTI ' if ok else 'KALDI '} {ad:<30} {detay}")
    hepsi = k1 and k2 and k3 and k4 and k5
    print(f"\n  HUKUM: {'COIN SINIFI FARKI GERCEK — sinav gecildi' if hepsi else 'DESTEKLENMEDI'}")

    print("\nOKUMA:")
    print("  - Tek degisken: sinyal, config, donem, fold'lar AYNI; yalniz coin sinifi degisti.")
    print("  - ⚠ Delist olanlar veride yok; KUCUK kademe bundan en cok etkilenen kademedir")
    print("    -> kucuk lehine cikan her sonuc UST SINIR'dir.")
    print("  - Tum kademeler negatifse 'hangisi daha az kotu' sorusu KARLILIK sorusu degildir.")


if __name__ == "__main__":
    main()
