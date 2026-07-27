"""
aday_testi.py — K2 ADAYLARININ WALK-FORWARD SINAVI (2026-07-27)
================================================================================
Amac: K2 gunu (30 kapali swing) elimizde her aday icin DIS-ORNEKLEM (OOS) kaniti
olsun; karar tahminle degil veriyle siralansin. Canli sisteme DOKUNMAZ.

YONTEM KARARI (kritik): her aday TEK DEGISKEN olarak CANLI ayara karsi test edilir.
Dev kombinasyon izgarasi KURULMAZ — B1/ileritest2 dersi: 32 hucreden en parlagini
secmek coklu-karsilastirma tuzagidir. Baz = canli config (seviye-2.5, lookback 50,
filtresiz). Her aday = baz + TEK degisiklik.

Walk-forward iskeleti ileritest.py/ileritest2.py ile AYNI: esikler her 30g dilimde
SADECE onceki 166g'den; test gorulmemis dilimde. za = MARK-TO-MARKET.

VERI ONBELLEGI: 11 coin x 540g klines + funding her kosuda yeniden cekilmesin diye
_cache/ klasorune gunluk yazilir (gitignore'lu). Ayni gun tekrar kosulursa aninda.

Calistirma: venv\\Scripts\\python.exe aday_testi.py [--aday seviye|hepsi]
"""

import bisect
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import olcucu
import backtest
import ileritest
import ileritest2
import rejim as rejim_mod   # KOR_SYMS, KOR_SPIKE, VOL_YUKSEK (canli esiklerle AYNI)
from kalibrasyon import percentile

TOPLAM_GUN = ileritest.TOPLAM_GUN     # 540
KAL_GUN = ileritest.KAL_GUN           # 166
ADIM_GUN = ileritest.ADIM_GUN         # 30
GUN_MS = ileritest.GUN_MS

CACHE = Path(__file__).parent / "_cache"
BAZ_LOOKBACK = backtest.LOOKBACK       # 50 (canli SWING_LOOKBACK)
BAZ_CFG = ("seviye", 2.5, None)        # (giris_mod, stop_atr, tp_atr) = canli


# ============================== veri onbellegi ==============================
def _cache_oku(ad):
    p = CACHE / f"{ad}.json"
    if not p.exists():
        return None
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        if d.get("gun") == datetime.now(timezone.utc).date().isoformat():
            return d["veri"]
    except Exception:
        pass
    return None


def _cache_yaz(ad, veri):
    CACHE.mkdir(exist_ok=True)
    try:
        (CACHE / f"{ad}.json").write_text(
            json.dumps({"gun": datetime.now(timezone.utc).date().isoformat(), "veri": veri}),
            encoding="utf-8")
    except Exception:
        pass


def veri_getir(sym):
    """(klines, funding_ts, funding_fr) — gunluk onbellekli."""
    ad = f"{sym}_{TOPLAM_GUN}g"
    c = _cache_oku(ad)
    if c:
        return c["K"], c["fts"], c["ffr"]
    K = backtest.klines_history(sym, "1h", TOPLAM_GUN)
    fts, ffr = ileritest.funding_serisi_gun(sym, TOPLAM_GUN)
    _cache_yaz(ad, {"K": K, "fts": fts, "ffr": ffr})
    return K, fts, ffr


# ============================== simulasyon ==============================
def _yeni_hucre():
    return {"tetik": 0, "kazanc": 0, "kayip": 0, "za": 0, "gross": 0.0, "net": 0.0}


def _isle(K, i, yon, seviye, a, hucre):
    """Tek config (BAZ_CFG) ile bir adayi simule et -> hucreye yaz."""
    mod, smul, tp_atr = BAZ_CFG
    i_e, e = backtest._giris(K, i, yon, seviye, a, mod)
    if i_e is None:
        return
    risk = smul * a
    tp_mesafe = (tp_atr * a) if tp_atr else (backtest.RR * risk)
    if yon == "SHORT":
        stop, tp = e + risk, e - tp_mesafe
    else:
        stop, tp = e - risk, e + tp_mesafe
    if min(stop, tp) <= 0 or min(e, risk) <= 0:
        return   # dejenere plan (canli veto ruhu)
    sonuc, gross = ileritest2._resolve_mtm(K, i_e, yon, e, stop, tp, risk)
    cost = e * (backtest._bacak(True) + backtest._bacak(sonuc != "tp")) / risk
    hucre["tetik"] += 1
    hucre["gross"] += gross
    hucre["net"] += gross - cost
    if sonuc == "tp":
        hucre["kazanc"] += 1
    elif sonuc == "stop":
        hucre["kayip"] += 1
    else:
        hucre["za"] += 1


def kosu(lookback, n_fold, t_ilk_fold, acc_key, acc):
    """Verilen lookback ile TUM coinleri gez; acc[acc_key][fold] hucrelerine yaz."""
    LB, CD = lookback, backtest.COOLDOWN_BAR
    for sym in olcucu.SYMBOLS:
        try:
            K, fts, ffr = veri_getir(sym)
        except Exception as e:
            print(f"    {sym}: HATA {type(e).__name__} - atlandi", flush=True)
            continue
        if len(K) < (KAL_GUN + ADIM_GUN) * 24:
            continue
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
                _isle(K, i, yon, seviye, a, acc[acc_key][f][yon])


# ============================== ADAY 2: REJIM KAPISI ==============================
# rejim.py'nin TARIHSEL yeniden-insasi. Canli esikler AYNEN kullanilir (KOR_SPIKE=0.85,
# VOL_YUKSEK=1.5). SIZINTI YOK: her deger SADECE o andan ONCEKI kapanmis barlardan.
KOR_PENCERE = 168        # canli: son ~7 gun saatlik getiri
REJIM_ADIM = 6           # her 6 barda bir yeniden hesapla (canli 20dk throttle'in kaba dengi)


def _hizali_getiriler(symbols):
    """Ortak zaman damgalarinda hizalanmis saatlik getiriler -> (ts_listesi, {sym: getiriler})."""
    maps = {}
    for s in symbols:
        K, _, _ = veri_getir(s)
        maps[s] = {k["t"]: k["c"] for k in K}
    ortak = sorted(set.intersection(*[set(m.keys()) for m in maps.values()]))
    rets = {s: [] for s in symbols}
    for i in range(1, len(ortak)):
        for s in symbols:
            c0, c1 = maps[s][ortak[i - 1]], maps[s][ortak[i]]
            rets[s].append((c1 - c0) / c0 if c0 else 0.0)
    return ortak[1:], rets


def _btc_gunluk_vol_serisi():
    """(gun_ts_listesi, vol_orani_listesi) — rejim.vol_rejimi'nin tarihsel dengi:
    son30g realize vol / taban vol (en fazla son 200 gun, canli ile ayni pencere)."""
    K, _, _ = veri_getir("BTCUSDT")
    gunluk = {}
    for k in K:
        gun = k["t"] // 86_400_000
        gunluk[gun] = k["c"]              # gunun son kapanisi (siralı veri)
    gunler = sorted(gunluk)
    kapanis = [gunluk[g] for g in gunler]
    ts_out, oran_out = [], []
    for i in range(61, len(gunler)):
        pencere = kapanis[max(0, i - 200):i]      # SADECE gecmis
        r = [(pencere[j] - pencere[j - 1]) / pencere[j - 1]
             for j in range(1, len(pencere)) if pencere[j - 1]]
        if len(r) < 60:
            continue
        son30, taban = rejim_mod._std(r[-30:]), rejim_mod._std(r[:-30])
        if son30 and taban:
            ts_out.append(gunler[i] * 86_400_000)
            oran_out.append(son30 / taban)
    return ts_out, oran_out


def rejim_serisi():
    """[(ts, korelasyon, vol_orani, oynak_mi)] — canli rejim.py mantiginin tarihsel izi."""
    ts, rets = _hizali_getiriler(list(rejim_mod.KOR_SYMS))
    syms = list(rejim_mod.KOR_SYMS)
    vol_ts, vol_or = _btc_gunluk_vol_serisi()
    out = []
    for j in range(KOR_PENCERE, len(ts), REJIM_ADIM):
        ciftler = []
        for x in range(len(syms)):
            for y in range(x + 1, len(syms)):
                p = rejim_mod._pearson(rets[syms[x]][j - KOR_PENCERE:j],
                                       rets[syms[y]][j - KOR_PENCERE:j])
                if p is not None:
                    ciftler.append(p)
        if not ciftler:
            continue
        kor = sum(ciftler) / len(ciftler)
        vi = bisect.bisect_right(vol_ts, ts[j]) - 1     # o ana kadarki SON gunluk vol
        vol = vol_or[vi] if vi >= 0 else None
        oynak = (kor >= rejim_mod.KOR_SPIKE) or bool(vol and vol >= rejim_mod.VOL_YUKSEK)
        out.append((ts[j], round(kor, 3), round(vol, 2) if vol else None, oynak))
    return out


def _rejim_bak(seri, seri_ts, t_ms):
    """t anindaki YURURLUKTEKI rejim (en son hesaplanmis, gelecege bakmaz)."""
    i = bisect.bisect_right(seri_ts, t_ms) - 1
    return seri[i] if i >= 0 else None


def kosu_rejim(n_fold, t_ilk_fold, acc, seri):
    """Ayni aday akisini BAZ ve SAKIN-only olarak eszamanli isler (esli test)."""
    seri_ts = [x[0] for x in seri]
    LB, CD = BAZ_LOOKBACK, backtest.COOLDOWN_BAR
    for sym in olcucu.SYMBOLS:
        try:
            K, _, _ = veri_getir(sym)
        except Exception:
            continue
        if len(K) < (KAL_GUN + ADIM_GUN) * 24:
            continue
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
            if not adaylar:
                continue
            r = _rejim_bak(seri, seri_ts, K[i]["t"])
            oynak = bool(r and r[3])
            for yon, seviye in adaylar:
                _isle(K, i, yon, seviye, a, acc["baz (tum rejimler)"][f][yon])
                hedef = "SAKIN'de islem (OYNAK atlanir)" if not oynak else "SADECE OYNAK'ta islem"
                _isle(K, i, yon, seviye, a, acc[hedef][f][yon])
                # Rafine hipotez (2026-07-27, esli kosunun LONG/SHORT ayriminden dogdu):
                # OYNAK'ta LONG cokuyor (-0.031) ama SHORT bozulmuyor (+0.034) ->
                # blanket kapi yerine SADECE yon-secici kapi. Mekanizma: korelasyon
                # spike + yuksek vol = risk-off/kontajyon; yukari kirilimlar yutuluyor.
                if (not oynak) or yon == "SHORT":
                    _isle(K, i, yon, seviye, a, acc["OYNAK'ta LONG yok (SHORT serbest)"][f][yon])


# ============================== ADAY 3-4: FUNDING TABANI + F&G ==============================
MUTLAK_FUNDING = 0.0001   # %0.01 — monotonluk testinde (2026-07-02) persentil-sismesi (F6) bulgusu


def fng_serisi():
    """alternative.me Korku&Achgozluluk endeksi -> [(ts_ms, deger)] artan. Gunluk onbellekli.
    Prob (2026-07-27): 3095 kayit, 2018-02-01'den beri, anahtarsiz -> 540g ufuk icin YETERLI."""
    c = _cache_oku("fng")
    if c:
        return [(int(t), int(v)) for t, v in c]
    import urllib.request
    raw = json.loads(urllib.request.urlopen(
        "https://api.alternative.me/fng/?limit=0&format=json", timeout=30).read())
    seri = sorted((int(x["timestamp"]) * 1000, int(x["value"])) for x in raw["data"])
    _cache_yaz("fng", seri)
    return seri


def _seri_bak(ts_list, val_list, t_ms):
    i = bisect.bisect_right(ts_list, t_ms) - 1
    return val_list[i] if i >= 0 else None


def basis_getir(sym):
    """1h basisRate serisi (vadeli prim/iskonto), gunluk onbellekli.
    B1'in TEK OOS-pozitif adayiydi (+0.13) AMA fold-konsantre -> tazeleme testi."""
    ad = f"{sym}_basis_{TOPLAM_GUN}g"
    c = _cache_oku(ad)
    if c:
        return c["ts"], c["br"]
    ts, br = ileritest.basis_serisi(sym, TOPLAM_GUN)
    _cache_yaz(ad, {"ts": ts, "br": br})
    return ts, br


def kosu_filtre(n_fold, t_ilk_fold, acc, tur):
    """Esli filtre testi. tur='funding' -> persentil vs persentil+mutlak taban.
    tur='fng' -> skill kurali (F&G>=75 LONG yok, <=25 SHORT yok)."""
    LB, CD = BAZ_LOOKBACK, backtest.COOLDOWN_BAR
    fng_ts = fng_val = None
    if tur == "fng":
        s = fng_serisi()
        fng_ts, fng_val = [x[0] for x in s], [x[1] for x in s]
    for sym in olcucu.SYMBOLS:
        try:
            K, fts, ffr = veri_getir(sym)
        except Exception:
            continue
        if len(K) < (KAL_GUN + ADIM_GUN) * 24:
            continue
        esikler = [ileritest2.fold_esik_funding(fts, ffr, t_ilk_fold + f * ADIM_GUN * GUN_MS)
                   for f in range(n_fold)] if tur == "funding" else None
        if tur == "basis":
            bts, bbr = basis_getir(sym)
            b_esik = []
            for f in range(n_fold):
                t0 = t_ilk_fold + f * ADIM_GUN * GUN_MS
                b = sorted(ileritest._dilim(bts, bbr, t0 - KAL_GUN * GUN_MS, t0))
                b_esik.append({"long_crowded": percentile(b, 85),
                               "short_crowded": percentile(b, 15)} if len(b) >= 500 else None)
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
            if not adaylar:
                continue
            for yon, seviye in adaylar:
                _isle(K, i, yon, seviye, a, acc["baz (filtresiz)"][f][yon])
                if tur == "funding":
                    fv = backtest.funding_at(fts, ffr, K[i]["t"])
                    th = esikler[f]
                    if ileritest._uygun(yon, fv, th):
                        _isle(K, i, yon, seviye, a, acc["funding persentil"][f][yon])
                        mutlak_ok = (fv >= MUTLAK_FUNDING) if yon == "SHORT" else (fv <= -MUTLAK_FUNDING)
                        if mutlak_ok:
                            _isle(K, i, yon, seviye, a, acc["persentil + mutlak taban"][f][yon])
                elif tur == "basis":
                    bv = backtest.funding_at(bts, bbr, K[i]["t"])   # ayni "son deger" mantigi
                    if ileritest._uygun(yon, bv, b_esik[f]):
                        _isle(K, i, yon, seviye, a, acc["basis persentil"][f][yon])
                else:
                    g = _seri_bak(fng_ts, fng_val, K[i]["t"])
                    if g is None:
                        continue
                    # Skill kurali (ON-KAYITLI, veriden turetilmedi): asiri acgozlulukte
                    # LONG yok, asiri korkuda SHORT yok.
                    if not ((yon == "LONG" and g >= 75) or (yon == "SHORT" and g <= 25)):
                        _isle(K, i, yon, seviye, a, acc["F&G kapisi (skill kurali)"][f][yon])


# ============================== rapor ==============================
def rapor(acc, adlar, n_fold, baz_ad):
    print("\n" + "=" * 92)
    print("  ADAY KARSILASTIRMASI — TEK DEGISKEN, canli config (seviye-2.5) sabit")
    print("  netR komisyon dahil | za = zaman-asimi (MTM) | pozF = net-pozitif fold sayisi")
    print("=" * 92)
    print(f"  {'aday':<26}{'tetik':>7}{'isabet':>8}{'za':>6}{'grossR':>9}{'netR':>9}{'ortNetR':>9}{'pozF':>7}")
    baz_ort = None
    for ad in adlar:
        t = _yeni_hucre()
        poz = 0
        for f in range(n_fold):
            fn = fnet = 0
            for y in ("SHORT", "LONG"):
                d = acc[ad][f][y]
                for k in t:
                    t[k] += d[k]
                fn += d["tetik"]
                fnet += d["net"]
            if fn and fnet > 0:
                poz += 1
        g = t["kazanc"] + t["kayip"]
        isb = f"%{t['kazanc'] / g * 100:.0f}" if g else "-"
        ort = t["net"] / t["tetik"] if t["tetik"] else 0.0
        if ad == baz_ad:
            baz_ort = ort
        fark = "" if baz_ort is None or ad == baz_ad else f"  ({ort - baz_ort:+.3f})"
        print(f"  {ad:<26}{t['tetik']:>7}{isb:>8}{t['za']:>6}{t['gross']:>+9.1f}"
              f"{t['net']:>+9.1f}{ort:>+9.3f}{poz:>5}/{n_fold}{fark}")

    print(f"\n  LONG/SHORT ayrimi:")
    for ad in adlar:
        parca = []
        for y in ("SHORT", "LONG"):
            t = _yeni_hucre()
            for f in range(n_fold):
                for k in t:
                    t[k] += acc[ad][f][y][k]
            g = t["kazanc"] + t["kayip"]
            isb = f"%{t['kazanc'] / g * 100:.0f}" if g else "-"
            ort = t["net"] / t["tetik"] if t["tetik"] else 0.0
            parca.append(f"{y} n={t['tetik']} isabet {isb} ortNet {ort:+.3f}")
        print(f"    {ad:<26}: " + " | ".join(parca))


def _bos_acc(adlar, n_fold):
    return {ad: [{y: _yeni_hucre() for y in ("SHORT", "LONG")} for _ in range(n_fold)]
            for ad in adlar}


def aday_seviye(n_fold, t_ilk_fold):
    lookbacklar = [(50, "lookback 50 (CANLI)"), (100, "lookback 100 (~4g)"),
                   (200, "lookback 200 (~8g)"), (400, "lookback 400 (~17g)")]
    adlar = [ad for _, ad in lookbacklar]
    acc = _bos_acc(adlar, n_fold)
    print("  ADAY TESTI #1 — SEVIYE PENCERESI")
    print("  soru: destek/direnc penceresi ~2 gun (50 bar) yerine daha DERIN olsa daha mi iyi?")
    print("=" * 92)
    for lb, ad in lookbacklar:
        print(f"  kosuluyor: {ad} ...", flush=True)
        kosu(lb, n_fold, t_ilk_fold, ad, acc)
    rapor(acc, adlar, n_fold, "lookback 50 (CANLI)")


def aday_rejim(n_fold, t_ilk_fold):
    adlar = ["baz (tum rejimler)", "SAKIN'de islem (OYNAK atlanir)", "SADECE OYNAK'ta islem",
             "OYNAK'ta LONG yok (SHORT serbest)"]
    acc = _bos_acc(adlar, n_fold)
    print("  ADAY TESTI #2 — REJIM KAPISI")
    print("  soru: piyasa OYNAK'ken (korelasyon>=0.85 VEYA vol>=1.5x) hic islem acmasak?")
    print("  canli sicil ipucu: DIKKAT'te acilan 12 islem -6.41R vs ACIK'ta 7 islem -4.22R")
    print("=" * 92)
    print("  rejim serisi tarihsel yeniden-insa ediliyor (korelasyon + vol) ...", flush=True)
    seri = rejim_serisi()
    oynak_pay = sum(1 for x in seri if x[3]) / len(seri) * 100 if seri else 0
    print(f"  {len(seri)} rejim noktasi | zamanin %{oynak_pay:.0f}'i OYNAK", flush=True)
    print("  kosuluyor: esli (baz / SAKIN / OYNAK) ...", flush=True)
    kosu_rejim(n_fold, t_ilk_fold, acc, seri)
    rapor(acc, adlar, n_fold, "baz (tum rejimler)")


def aday_funding(n_fold, t_ilk_fold):
    adlar = ["baz (filtresiz)", "funding persentil", "persentil + mutlak taban"]
    acc = _bos_acc(adlar, n_fold)
    print("  ADAY TESTI #3 — MUTLAK FUNDING TABANI")
    print(f"  soru: persentil esigine ek olarak |funding| >= %{MUTLAK_FUNDING*100:g} sarti aransa?")
    print("  kaynak: monotonluk testi (2026-07-02) persentil-sismesi bulgusu (F6)")
    print("=" * 92)
    print("  kosuluyor: esli (baz / persentil / persentil+mutlak) ...", flush=True)
    kosu_filtre(n_fold, t_ilk_fold, acc, "funding")
    rapor(acc, adlar, n_fold, "baz (filtresiz)")


def aday_fng(n_fold, t_ilk_fold):
    adlar = ["baz (filtresiz)", "F&G kapisi (skill kurali)"]
    acc = _bos_acc(adlar, n_fold)
    print("  ADAY TESTI #4 — KORKU & ACGOZLULUK ENDEKSI")
    print("  soru: F&G>=75 iken LONG yok, F&G<=25 iken SHORT yok (skill D4 kurali) fayda verir mi?")
    print("  ON-KAYITLI: kural dis skill'den ALINDI, bizim verimizden turetilmedi (tuzak yok)")
    print("=" * 92)
    print("  kosuluyor: esli (baz / F&G kapisi) ...", flush=True)
    kosu_filtre(n_fold, t_ilk_fold, acc, "fng")
    rapor(acc, adlar, n_fold, "baz (filtresiz)")
    fold_dokumu(acc, adlar, n_fold, t_ilk_fold)


def fold_dokumu(acc, adlar, n_fold, t_ilk_fold):
    """Fold-fold netR. B1 DERSI: toplam parlak olup kazancin tamami TEK fold'dan
    gelebilir (basis hipotezi boyle olmustu) -> yogunlasma kontrolu ZORUNLU."""
    print(f"\n  FOLD DOKUMU (netR) — yogunlasma kontrolu")
    print(f"  {'dilim basi':<13}" + "".join(f"{ad[:22]:>24}" for ad in adlar))
    toplamlar = {ad: [] for ad in adlar}
    for f in range(n_fold):
        t0 = t_ilk_fold + f * ADIM_GUN * GUN_MS
        tarih = datetime.fromtimestamp(t0 / 1000, timezone.utc).strftime("%Y-%m-%d")
        satir = f"  {tarih:<13}"
        for ad in adlar:
            net = sum(acc[ad][f][y]["net"] for y in ("SHORT", "LONG"))
            n = sum(acc[ad][f][y]["tetik"] for y in ("SHORT", "LONG"))
            toplamlar[ad].append(net)
            satir += f"{n:>6} /{net:>+8.1f}   "
        print(satir)
    print(f"\n  YOGUNLASMA: en iyi fold toplamin yuzde kaci?")
    for ad in adlar:
        v = toplamlar[ad]
        top = sum(v)
        enb = max(v) if v else 0
        pay = (enb / top * 100) if top > 0 else 0
        poz = sum(1 for x in v if x > 0)
        print(f"    {ad:<34}: toplam {top:+.1f} | en iyi fold {enb:+.1f} "
              f"(%{pay:.0f}) | pozitif {poz}/{n_fold}")


def aday_basis(n_fold, t_ilk_fold):
    adlar = ["baz (filtresiz)", "basis persentil"]
    acc = _bos_acc(adlar, n_fold)
    print("  ADAY TESTI #5 — BASIS TAZELEME")
    print("  soru: B1'in TEK OOS-pozitif adayi (+0.13) yeni fold'larda hala tutuyor mu?")
    print("  ⚠ B1 uyarisi: +27.2'nin +24.0'i TEK fold'dan geliyordu (yogunlasma)")
    print("=" * 92)
    print("  basis serileri cekiliyor (ilk kosuda yavas, sonra onbellekli) ...", flush=True)
    kosu_filtre(n_fold, t_ilk_fold, acc, "basis")
    rapor(acc, adlar, n_fold, "baz (filtresiz)")
    fold_dokumu(acc, adlar, n_fold, t_ilk_fold)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    simdi = int(datetime.now(timezone.utc).timestamp() * 1000)
    t_ilk_fold = simdi - TOPLAM_GUN * GUN_MS + KAL_GUN * GUN_MS
    n_fold = (TOPLAM_GUN - KAL_GUN) // ADIM_GUN
    aday = sys.argv[sys.argv.index("--aday") + 1] if "--aday" in sys.argv else "seviye"

    print("=" * 92)
    print(f"  K2 ADAY SINAVI | 1h | ufuk {TOPLAM_GUN}g | kalibrasyon {KAL_GUN}g | {n_fold} fold"
          f" | {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"  YONTEM: tek degisken, canli config (seviye-2.5) sabit | coinler: {len(olcucu.SYMBOLS)}")
    print("=" * 92)

    if aday in ("seviye", "hepsi"):
        aday_seviye(n_fold, t_ilk_fold)
    if aday in ("rejim", "hepsi"):
        aday_rejim(n_fold, t_ilk_fold)
    if aday in ("funding", "hepsi"):
        aday_funding(n_fold, t_ilk_fold)
    if aday in ("fng", "hepsi"):
        aday_fng(n_fold, t_ilk_fold)
    if aday in ("basis", "hepsi"):
        aday_basis(n_fold, t_ilk_fold)

    print("\nOKUMA: pozF (kac fold'da pozitif) tek toplam sayidan ONEMLI (B1 dersi).")
    print("GURULTU TABANI (2026-07-27 olcumu): ayni baz config 10 gun arayla +0.05 vs +0.02")
    print("ortNetR verdi -> 0.03R'den KUCUK farklar ANLAMSIZ. Seviye-dolum varsayimi surer.")


if __name__ == "__main__":
    main()
