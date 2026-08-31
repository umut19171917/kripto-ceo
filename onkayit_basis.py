"""ON-KAYIT OLCUM ARACI — `basis` (ON-KAYIT-basis.md, commit b8b9e6b)

Madde 7.4 / B4 — TEK-BANT SORUNU.
Soru: spot-perp farki bandin DISINDA yeni bilgi mi, yoksa funding'in
      baska adi mi?

SALT OKURDUR. Canli hicbir dosyaya yazmaz, calisan sureclere dokunmaz.
Tek yazdigi yer: `_cache/basis/` (gitignore'lu; silinmesi olcumu bozmaz).

Kullanim:  venv\\Scripts\\python.exe onkayit_basis.py
"""
import sys as _sys
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import bisect
import json
import math
import os
import random
import statistics as st
import time
from collections import defaultdict
from datetime import datetime, timezone

import requests

import olcucu

ON_KAYIT_COMMIT = "b8b9e6b"

SAAT = 3600_000
GUN = 24 * SAAT
YIL4 = 1460 * GUN
BANT = 5
TUR = 3000
ONBELLEK = os.path.join("_cache", "basis")

SPOT_BASE = "https://api.binance.com"
PERP_BASE = "https://fapi.binance.com"

random.seed(11)                      # §2: proje teamulu


# --------------------------------------------------------------------------
# 1. VERI — indir, onbellekle
# --------------------------------------------------------------------------
def _ist(url, params, deneme=4):
    for k in range(deneme):
        try:
            r = requests.get(url, params=params, timeout=25)
            if r.status_code == 200:
                return r.json()
            if r.status_code in (418, 429):
                time.sleep(5 * (k + 1))
                continue
            return None
        except Exception:
            time.sleep(2 * (k + 1))
    return None


def _klines(base, yol, sym, t0, t1):
    """Sayfalanmis 1h kline -> {ms: kapanis}. Bos donerse boru biter."""
    out, t = {}, t0
    while t < t1:
        d = _ist(base + yol, {"symbol": sym, "interval": "1h",
                              "startTime": t, "limit": 1000})
        if not d:
            break
        for k in d:
            if int(k[0]) <= t1:
                out[int(k[0])] = float(k[4])
        t = int(d[-1][0]) + SAAT
        if len(d) < 1000:
            break
        time.sleep(0.15)
    return out


def _funding(sym, t0, t1):
    """[(fundingTime, rate)] artan. 8 saatte bir yayimlanir."""
    out, t = [], t0
    while t < t1:
        d = _ist(PERP_BASE + "/fapi/v1/fundingRate",
                 {"symbol": sym, "startTime": t, "limit": 1000})
        if not d:
            break
        for f in d:
            out.append((int(f["fundingTime"]), float(f["fundingRate"])))
        t = int(d[-1]["fundingTime"]) + 1
        if len(d) < 1000:
            break
        time.sleep(0.15)
    out.sort()
    return out


def veri(sym, t0, t1):
    """Onbellekten oku ya da indir. Onbellek anahtari pencereyi icerir."""
    os.makedirs(ONBELLEK, exist_ok=True)
    yol = os.path.join(ONBELLEK, f"{sym}_{t0 // GUN}_{t1 // GUN}.json")
    if os.path.exists(yol):
        try:
            with open(yol, encoding="utf-8") as f:
                d = json.load(f)
            return ({int(k): v for k, v in d["spot"].items()},
                    {int(k): v for k, v in d["perp"].items()},
                    [(int(a), b) for a, b in d["fund"]])
        except Exception:
            pass
    sp = _klines(SPOT_BASE, "/api/v3/klines", sym, t0, t1)
    pe = _klines(PERP_BASE, "/fapi/v1/klines", sym, t0, t1)
    fu = _funding(sym, t0, t1)
    try:
        gecici = yol + ".tmp"
        with open(gecici, "w", encoding="utf-8") as f:
            json.dump({"spot": sp, "perp": pe, "fund": fu}, f)
        os.replace(gecici, yol)
    except Exception:
        pass
    return sp, pe, fu


def tick_oranlari():
    """exchangeInfo -> {sym: tickSize}. Gurultu tabani kontrolu (§4.3)."""
    d = _ist(PERP_BASE + "/fapi/v1/exchangeInfo", {})
    out = {}
    if not d:
        return out
    for s in d.get("symbols", []):
        for f in s.get("filters", []):
            if f.get("filterType") == "PRICE_FILTER":
                out[s["symbol"]] = float(f["tickSize"])
    return out


# --------------------------------------------------------------------------
# 2. GOZLEM KURULUMU (§2 tanimlari birebir)
# --------------------------------------------------------------------------
def gozlemler(sym, t0, t1):
    sp, pe, fu = veri(sym, t0, t1)
    if not sp or not pe or not fu:
        return []
    ft = [x[0] for x in fu]
    ortak = sorted(set(sp) & set(pe))
    G = []
    for t in ortak:
        t24 = t + GUN
        if t24 not in pe:
            continue
        i = bisect.bisect_right(ft, t) - 1     # 🔴 ILERI BAKIS YASAGI
        if i < 0:
            continue
        G.append({
            "sym": sym,
            "t": t,
            "gun": datetime.fromtimestamp(t / 1000, timezone.utc).date().isoformat(),
            "saat": datetime.fromtimestamp(t / 1000, timezone.utc).hour,
            "fiyat": pe[t],
            "basis": (pe[t] - sp[t]) / sp[t] * 100.0,
            "fund": fu[i][1] * 100.0,          # % cinsine
            "ileri": (pe[t24] - pe[t]) / pe[t] * 100.0,
        })
    return G


def ekk_artik(G):
    """Sembol basina EKK: basis ~ funding. Artik = basis - tahmin. (§2)"""
    x = [g["fund"] for g in G]
    y = [g["basis"] for g in G]
    mx, my = st.fmean(x), st.fmean(y)
    sxx = sum((a - mx) ** 2 for a in x)
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    b = sxy / sxx if sxx > 0 else 0.0
    a = my - b * mx
    for g, xi, yi in zip(G, x, y):
        g["artik"] = yi - (a + b * xi)
    sy = sum((v - my) ** 2 for v in y)
    r2 = (1 - sum((g["artik"]) ** 2 for g in G) / sy) if sy > 0 else 0.0
    return a, b, r2


# --------------------------------------------------------------------------
# 3. ISTATISTIK
# --------------------------------------------------------------------------
def spearman(x, y):
    def sira(v):
        s = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(s):
            j = i
            while j + 1 < len(s) and v[s[j + 1]] == v[s[i]]:
                j += 1
            ort = (i + j) / 2.0 + 1
            for k in range(i, j + 1):
                r[s[k]] = ort
            i = j + 1
        return r
    rx, ry = sira(x), sira(y)
    mx, my = st.fmean(rx), st.fmean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return num / den if den > 0 else 0.0


def bantla(G, alan):
    """§2: bantlar SEMBOL ICINDE esit sayili bese bolunur, sonra havuzlanir."""
    per = defaultdict(list)
    for g in G:
        per[g["sym"]].append(g)
    for sym, lst in per.items():
        lst.sort(key=lambda g: g[alan])
        n = len(lst)
        for i, g in enumerate(lst):
            g["bant"] = min(BANT - 1, i * BANT // n)
    return G


def bant_ozet(G):
    b = defaultdict(list)
    for g in G:
        b[g["bant"]].append(g["ileri"])
    return [st.fmean(b[k]) if b[k] else float("nan") for k in range(BANT)]


def gun_bootstrap(G):
    """Takvim gunu yeniden orneklenir; bant ATAMALARI sabit kalir.

    Hiz notu: her turda ham gozlemleri gezmek 4 yilda ~1,2 milyar islem eder.
    Bunun yerine gun basina (bant -> toplam, adet) ONCEDEN hesaplanir; tur
    basina is 1.460x5'e duser. Sonuc matematiksel olarak AYNIDIR (ortalama =
    toplamlarin orani), yalnizca hizlidir.
    """
    ozet = defaultdict(lambda: [[0.0, 0] for _ in range(BANT)])
    for g in G:
        h = ozet[g["gun"]][g["bant"]]
        h[0] += g["ileri"]
        h[1] += 1
    bloklar = list(ozet.values())
    n = len(bloklar)
    if n < 20:
        return None
    fark = []
    for _ in range(TUR):
        t0 = a0 = t4 = a4 = 0.0
        for _ in range(n):
            b = bloklar[random.randrange(n)]
            t0 += b[0][0]
            a0 += b[0][1]
            t4 += b[BANT - 1][0]
            a4 += b[BANT - 1][1]
        if a0 and a4:
            fark.append(t4 / a4 - t0 / a0)
    if len(fark) < 100:
        return None
    fark.sort()
    return fark[int(0.025 * len(fark))], fark[int(0.975 * len(fark))]


def kol(G, alan, ad, esik_yaz=True):
    """Bir degiskeni bantlar, raporlar, hukum satirini basar."""
    bantla(G, alan)
    o = bant_ozet(G)
    rho = spearman(list(range(BANT)), o)
    fark = o[BANT - 1] - o[0]
    ga = gun_bootstrap(G)
    print(f"\n  {ad}")
    print("  " + "-" * 72)
    print("    bant:  " + "  ".join(f"{v:+7.3f}%" for v in o))
    gs = f"[{ga[0]:+.3f}%, {ga[1]:+.3f}%]" if ga else "GA yok"
    print(f"    Spearman rho = {rho:+.3f}   uc bant farki = {fark:+.3f}%"
          f"   gun-kumeli GA95 {gs}")
    if esik_yaz and ga:
        sifir_disi = (ga[0] > 0) or (ga[1] < 0)
        if not sifir_disi:
            h = "❌ GA sifiri KAPSIYOR -> bilgi yok"
        elif abs(fark) >= 0.5 and abs(rho) >= 0.8:
            h = "✅ GA sifiri disliyor · |fark|>=%0,5 · |rho|>=0,8 -> BILGI VAR"
        elif abs(fark) >= 0.26:
            h = "⚠ istatistiksel VAR, ekonomik YOK (%0,26-0,5 bandi)"
        else:
            h = "⚠ istatistiksel VAR ama fark maliyetin (%0,26) ALTINDA"
        print(f"    §6 HUKMU: {h}")
    return {"bant": o, "rho": rho, "fark": fark, "ga": ga}


# --------------------------------------------------------------------------
# 4. ANA
# --------------------------------------------------------------------------
def main():
    t1 = int(time.time() * 1000) // SAAT * SAAT
    t0 = t1 - YIL4

    print("=" * 78)
    print("  ON-KAYITLI OLCUM — basis (madde 7.4 / B4: TEK-BANT SORUNU)")
    print(f"  on kayit: ON-KAYIT-basis.md (commit {ON_KAYIT_COMMIT})")
    print(f"  pencere: {datetime.fromtimestamp(t0/1000, timezone.utc):%Y-%m-%d} -> "
          f"{datetime.fromtimestamp(t1/1000, timezone.utc):%Y-%m-%d}  (4 yil, 1h)")
    print("=" * 78)

    ticks = tick_oranlari()

    print("\n  1. KAPSAMA")
    print("  " + "-" * 72)
    print(f"    {'sembol':10s} {'n(saat)':>9s} {'ilk gozlem':>12s} "
          f"{'rho(basis,fund)':>16s} {'R2':>7s}")
    TUM = []
    S1 = []
    for sym in olcucu.SYMBOLS:
        G = gozlemler(sym, t0, t1)
        if len(G) < 500:
            print(f"    {sym:10s} {len(G):9d}   YETERSIZ -> orneklemden CIKARILDI")
            continue
        _, _, r2 = ekk_artik(G)
        rho_bf = spearman([g["basis"] for g in G], [g["fund"] for g in G])
        S1.append((sym, rho_bf, r2))
        ilk = min(g["gun"] for g in G)
        print(f"    {sym:10s} {len(G):9d} {ilk:>12s} {rho_bf:>16.3f} {r2:>7.3f}")
        TUM += G

    if not TUM:
        print("\n  veri yok — olcum yapilamadi")
        return

    print(f"\n    TOPLAM {len(TUM)} saatlik gozlem · "
          f"{len(set(g['gun'] for g in TUM))} takvim gunu · "
          f"{len(set(g['sym'] for g in TUM))} sembol")

    # --- 2. ARTIKLIK ---
    print("\n  2. S1 — ARTIKLIK: basis ne kadari funding'in icinde?")
    print("  " + "-" * 72)
    med_rho = st.median([x[1] for x in S1])
    med_r2 = st.median([x[2] for x in S1])
    print(f"    havuz medyani: rho(basis,funding) = {med_rho:+.3f} · R2 = {med_r2:.3f}")
    print(f"    -> basis'in ~%{100*med_r2:.1f}'i funding tarafindan aciklaniyor")

    # --- 3. GURULTU TABANI ---
    print("\n  3. ARTIGIN OLCEGI vs TICK GURULTUSU (§4.3 / §5 ek sart)")
    print("  " + "-" * 72)
    print(f"    {'sembol':10s} {'sd(artik)%':>12s} {'tick/fiyat%':>13s} {'oran':>8s}")
    olculebilir = True
    for sym in sorted(set(g["sym"] for g in TUM)):
        alt = [g for g in TUM if g["sym"] == sym]
        sd = st.pstdev([g["artik"] for g in alt])
        tk = ticks.get(sym)
        if not tk:
            print(f"    {sym:10s} {sd:12.5f}          tick yok")
            continue
        tp = tk / st.fmean([g["fiyat"] for g in alt]) * 100
        print(f"    {sym:10s} {sd:12.5f} {tp:13.5f} {sd/tp:8.1f}x")
        if sd / tp < 1.0:
            olculebilir = False
    print(f"    -> {'artik tick gurultusunun UZERINDE, olculebilir' if olculebilir else '⚠ EN AZ BIR SEMBOLDE artik tick seviyesinde -> OLCULEMEDI'}")

    # --- 4/5/6. UC KOL ---
    print("\n  4-6. UC KOL — bilgi nerede? (§4 sirasi: artik, ham basis, funding)")
    print("  " + "=" * 72)
    R = {}
    R["artik"] = kol(TUM, "artik", "4. ARTIK (funding'den arta kalan) — ASIL SORU")
    R["basis"] = kol(TUM, "basis", "5. HAM BASIS (paralel kol)")
    R["fund"] = kol(TUM, "fund", "6. FUNDING (paralel kol — bant ICI kontrol)")

    # --- 7. SAGLAMLIK ---
    print("\n  7. SAGLAMLIK")
    print("  " + "=" * 72)
    # 7a. ortusmesiz gunluk: gun d icin saat (d mod 24) -> faz kilidi YOK
    gun_idx = {g: i for i, g in enumerate(sorted(set(x["gun"] for x in TUM)))}
    tekil = [g for g in TUM if g["saat"] == gun_idx[g["gun"]] % 24]
    print(f"\n  7a. ORTUSMESIZ GUNLUK  (n={len(tekil)}; gun d -> saat d mod 24,"
          f" faz kilidi yok)")
    if len(tekil) >= 500:
        kol(tekil, "artik", "     artik — ortusmesiz")
    else:
        print("      n yetersiz")

    # 7b. top-3 sembol cikarilinca (en guclu 3 = sonuca bakilarak, MUHAFAZAKAR)
    tek_fark = {}
    for sym in sorted(set(g["sym"] for g in TUM)):
        alt = [g for g in TUM if g["sym"] == sym]
        bantla(alt, "artik")
        o = bant_ozet(alt)
        tek_fark[sym] = abs(o[BANT - 1] - o[0])
    top3 = [s for s, _ in sorted(tek_fark.items(), key=lambda x: -x[1])[:3]]
    kalan = [g for g in TUM if g["sym"] not in top3]
    print(f"\n  7b. TOP-3 CIKARILDI ({', '.join(top3)}) — en guclu uc sembol atildi")
    if kalan:
        kol(kalan, "artik", "     artik — top-3 haric")

    # --- HUKUM OZETI ---
    print("\n  " + "=" * 72)
    print("  §6 UC KOLLU OKUMA")
    print("  " + "=" * 72)

    def var_mi(d):
        if not d["ga"]:
            return False
        return (d["ga"][0] > 0 or d["ga"][1] < 0) and abs(d["fark"]) >= 0.5 and abs(d["rho"]) >= 0.8

    hb, ha = var_mi(R["basis"]), var_mi(R["artik"])
    if hb and ha:
        print("  -> Bant DISINDA gercekten yeni bilgi. Mekanik asamasi icin AYRI on kayit.")
    elif hb and not ha:
        print("  -> 🔴 Bilgi funding'in ICINDEYDI. Bu bant DISI bulgu DEGILDIR;")
        print("     fundingin zaten tasidigi seyi yeniden kesfetmis oluruz. (§6 orta satir)")
    elif not hb and not ha:
        print("  -> ❌ BASIS DALI OLU. Bant disi adaylardan birini daha eledik.")
    else:
        print("  -> Artikta var, ham basiste yok: funding GURULTU ekliyor demektir.")
        print("     Bu beklenmedik; ayrica incelenmeli, tek basina hukum kurulmaz.")

    print("\n  ⚠ SINIRLAR (§3): hayatta kalma yanliligi (11 sembol bugun yasiyor) ·")
    print("    ortusen 24s pencereler (gun-kumeli bootstrap kismen kapatir) ·")
    print("    bu bir BILGI testidir, KARLILIK testi DEGILDIR.")
    print("  " + "=" * 72)


if __name__ == "__main__":
    main()
