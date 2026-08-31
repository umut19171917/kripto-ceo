"""ON-KAYIT OLCUM ARACI — `topls` (ON-KAYIT-topls.md, commit a809dc2)

Madde 7.4 / B4. Soru: buyuk hesaplarin POZISYON KAYMASI yon tasiyor mu?
🔴 ANA DEGISKEN SEVIYE DEGIL DEGISIMDIR — ufku ve bicimi VERI secti (§1):
   seviye'nin otokorelasyon suresi ~416 saat -> sembol basina 1,7 bagimsiz
   gozlem -> hicbir ufukta sinanamaz. Degisim: ~1,8 saat -> 394,6.

SALT OKURDUR. Canli hicbir dosyaya yazmaz, calisan sureclere dokunmaz.

Kullanim:  venv\\Scripts\\python.exe onkayit_topls.py
"""
import sys as _sys
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import glob
import json
import math
import os
import random
import statistics as st
import time
from collections import defaultdict
from datetime import datetime, timezone

import requests

ON_KAYIT_COMMIT = "a809dc2"
SAAT = 3600_000
ARSIV = "perp-arsiv"
BANT = 5
TUR = 3000
MIN_GUN = 20                 # §3: en az 20 gunluk seri
KIRP = 0.01                  # §4.3: %1-%99 kirpma

random.seed(11)              # §2


# --------------------------------------------------------------------------
# 1. VERI
# --------------------------------------------------------------------------
def arsiv_serileri():
    """{sym: {saat_ms: (top_ls, ls)}} — 5dk noktalari saatlik kovaya indirilir."""
    out = {}
    for f in glob.glob(os.path.join(ARSIV, "*.json")):
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        t, l = d.get("top_ls"), d.get("ls")
        if not t or not l:
            continue
        kova = defaultdict(list)
        for k, v in t.items():
            if k in l:                       # ayni damgada ikisi de olsun
                kova[int(k) // SAAT * SAAT].append((v, l[k]))
        if len(kova) < 24 * MIN_GUN:
            continue
        out[os.path.basename(f)[:-5]] = {
            s: (st.fmean(x[0] for x in v), st.fmean(x[1] for x in v))
            for s, v in kova.items()}
    return out


def klines(sym, t0, t1):
    out, t = {}, t0
    while t < t1:
        try:
            r = requests.get("https://fapi.binance.com/fapi/v1/klines",
                             params={"symbol": sym, "interval": "1h",
                                     "startTime": t, "limit": 1000}, timeout=25)
            if r.status_code != 200:
                return out
            d = r.json()
        except Exception:
            return out
        if not d:
            break
        for k in d:
            out[int(k[0])] = float(k[4])
        t = int(d[-1][0]) + SAAT
        if len(d) < 1000:
            break
        time.sleep(0.1)
    return out


# --------------------------------------------------------------------------
# 2. ISTATISTIK
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
            o = (i + j) / 2.0 + 1
            for k in range(i, j + 1):
                r[s[k]] = o
            i = j + 1
        return r
    rx, ry = sira(x), sira(y)
    mx, my = st.fmean(rx), st.fmean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return num / den if den > 0 else 0.0


def kirpilmis(v):
    """§4.3 zorunlu: %1-%99 kirpilmis ortalama."""
    if len(v) < 20:
        return st.fmean(v) if v else float("nan")
    s = sorted(v)
    a = int(len(s) * KIRP)
    return st.fmean(s[a:len(s) - a])


def bantla(G, alan):
    """§2: bantlar SEMBOL ICINDE esit sayili bese bolunur, sonra havuzlanir."""
    per = defaultdict(list)
    for g in G:
        per[g["sym"]].append(g)
    for lst in per.values():
        lst.sort(key=lambda g: g[alan])
        n = len(lst)
        for i, g in enumerate(lst):
            g["bant"] = min(BANT - 1, i * BANT // n)
    return G


def gun_bootstrap(G):
    """Takvim gunu yeniden orneklenir; bant atamalari sabit."""
    ozet = defaultdict(lambda: [[0.0, 0] for _ in range(BANT)])
    for g in G:
        h = ozet[g["gun"]][g["bant"]]
        h[0] += g["ileri"]
        h[1] += 1
    bl = list(ozet.values())
    n = len(bl)
    if n < 10:
        return None
    fark = []
    for _ in range(TUR):
        t0 = a0 = t4 = a4 = 0.0
        for _ in range(n):
            b = bl[random.randrange(n)]
            t0 += b[0][0]; a0 += b[0][1]
            t4 += b[BANT - 1][0]; a4 += b[BANT - 1][1]
        if a0 and a4:
            fark.append(t4 / a4 - t0 / a0)
    if len(fark) < 100:
        return None
    fark.sort()
    return fark[int(0.025 * len(fark))], fark[int(0.975 * len(fark))]


def kol(G, alan, ad, hukum=True, guclu=True):
    bantla(G, alan)
    b = defaultdict(list)
    for g in G:
        b[g["bant"]].append(g["ileri"])
    ort = [st.fmean(b[k]) if b[k] else float("nan") for k in range(BANT)]
    med = [st.median(b[k]) if b[k] else float("nan") for k in range(BANT)]
    kir = [kirpilmis(b[k]) if b[k] else float("nan") for k in range(BANT)]
    rho = spearman(list(range(BANT)), ort)
    fark = ort[BANT - 1] - ort[0]
    f_med = med[BANT - 1] - med[0]
    f_kir = kir[BANT - 1] - kir[0]
    ga = gun_bootstrap(G)

    print(f"\n  {ad}   (n={len(G)})")
    print("  " + "-" * 72)
    print("    ortalama : " + "  ".join(f"{v:+7.3f}%" for v in ort))
    print("    MEDYAN   : " + "  ".join(f"{v:+7.3f}%" for v in med))
    print("    KIRPILMIS: " + "  ".join(f"{v:+7.3f}%" for v in kir))
    gs = f"[{ga[0]:+.3f}%, {ga[1]:+.3f}%]" if ga else "GA yok"
    print(f"    rho={rho:+.3f}  uc fark: ort {fark:+.3f}%  medyan {f_med:+.3f}%"
          f"  kirp {f_kir:+.3f}%")
    print(f"    gun-kumeli GA95 (ortalama farki): {gs}")

    if not hukum:
        return
    if not guclu:
        print("    §5 HUKMU: ⚠ OLCULEMEDI — bu kol yeterince guclu DEGIL")
        print("              (on kayitta sonuc gorulmeden yazildi)")
        return
    if not ga:
        print("    §6 HUKMU: GA hesaplanamadi")
        return
    sifir_disi = (ga[0] > 0) or (ga[1] < 0)
    ayni_yon = (fark > 0) == (f_med > 0) and (fark > 0) == (f_kir > 0)
    if not sifir_disi:
        h = "❌ GA sifiri KAPSIYOR -> bilgi yok"
    elif not ayni_yon:
        h = "❌ UC DEGER ESERI — ortalama ile medyan/kirpilmis AYNI YONDE DEGIL"
    elif abs(fark) >= 0.5 and abs(rho) >= 0.8:
        h = "✅ GA sifiri disliyor · |fark|>=%0,5 · |rho|>=0,8 · uc deger denetimi GECTI"
    elif abs(fark) >= 0.26:
        h = "⚠ istatistiksel VAR, ekonomik YOK (%0,26-0,5 bandi)"
    else:
        h = "⚠ istatistiksel VAR ama fark maliyetin (%0,26) ALTINDA"
    print(f"    §6 HUKMU: {h}")


# --------------------------------------------------------------------------
# 3. ANA
# --------------------------------------------------------------------------
def main():
    print("=" * 78)
    print("  ON-KAYITLI OLCUM — topls (madde 7.4 / B4)")
    print(f"  on kayit: ON-KAYIT-topls.md (commit {ON_KAYIT_COMMIT})")
    print("  🔴 ANA DEGISKEN: SEVIYE DEGIL 1 SAATLIK DEGISIM (ufku VERI sectI)")
    print("=" * 78)

    S = arsiv_serileri()
    if not S:
        print("\n  arsivde uygun seri yok")
        return
    tum_ts = [t for v in S.values() for t in v]
    t0, t1 = min(tum_ts), max(tum_ts) + 12 * SAAT

    print(f"\n  1. KAPSAMA")
    print("  " + "-" * 72)
    print(f"    sembol (>= {MIN_GUN} gun): {len(S)}")
    print(f"    pencere: {datetime.fromtimestamp(t0/1000, timezone.utc):%Y-%m-%d} -> "
          f"{datetime.fromtimestamp(max(tum_ts)/1000, timezone.utc):%Y-%m-%d}"
          f"  ({(max(tum_ts)-t0)/86400_000:.1f} gun)")

    G1, G8, GS = [], [], []
    fiyatsiz = []
    for sym in sorted(S):
        p = klines(sym, t0, t1)
        if len(p) < 24 * MIN_GUN:
            fiyatsiz.append(sym)
            continue
        v = S[sym]
        ts = sorted(v)
        for i, t in enumerate(ts):
            t_ileri = t + SAAT
            if t not in p or t_ileri not in p:
                continue
            ileri1 = (p[t_ileri] - p[t]) / p[t] * 100
            gun = datetime.fromtimestamp(t / 1000, timezone.utc).date().isoformat()
            temel = {"sym": sym, "gun": gun, "t": t}
            # seviye kolu (§4.4 — guclu DEGIL)
            GS.append({**temel, "x": v[t][0], "ileri": ileri1})
            # ANA: 1 saatlik degisim
            if i >= 1 and ts[i - 1] == t - SAAT:
                G1.append({**temel, "x": v[t][0] - v[ts[i - 1]][0], "ileri": ileri1})
            # 8 saatlik degisim, 8 saatlik ufuk (§4.5)
            t8 = t + 8 * SAAT
            if i >= 8 and ts[i - 8] == t - 8 * SAAT and t8 in p:
                G8.append({**temel, "x": v[t][0] - v[ts[i - 8]][0],
                           "ileri": (p[t8] - p[t]) / p[t] * 100})
        time.sleep(0.05)

    print(f"    fiyat serisi alinamayan: {len(fiyatsiz)}"
          f"{' -> ' + ', '.join(fiyatsiz[:6]) if fiyatsiz else ''}")
    print(f"    gozlem — ana(d1): {len(G1):,} · d8: {len(G8):,} · seviye: {len(GS):,}")
    print(f"    takvim gunu: {len(set(g['gun'] for g in G1))}")
    if len(G1) < 500:
        print("\n  ⚠ ana kolda gozlem yetersiz — hukum basilmiyor")
        return

    print("\n  2-3. ANA SORU + UC DEGER DENETIMI")
    print("  " + "=" * 72)
    kol(G1, "x", "2. POZISYON KAYMASI (d1) -> 1 SAATLIK ILERI GETIRI")

    print("\n  4-5. PARALEL KOLLAR")
    print("  " + "=" * 72)
    kol(GS, "x", "4. SEVIYE (top_ls) — ⚠ ON KAYITTA GUCSUZ ILAN EDILDI",
        guclu=False)
    if len(G8) >= 500:
        kol(G8, "x", "5. 8 SAATLIK KAYMA -> 8 SAATLIK UFUK (sinirda guclu)")

    print("\n  6. SAGLAMLIK")
    print("  " + "=" * 72)
    katki = {}
    for sym in sorted(set(g["sym"] for g in G1)):
        alt = [g for g in G1 if g["sym"] == sym]
        bantla(alt, "x")
        b = defaultdict(list)
        for g in alt:
            b[g["bant"]].append(g["ileri"])
        if b[0] and b[BANT - 1]:
            katki[sym] = abs(st.fmean(b[BANT - 1]) - st.fmean(b[0]))
    top3 = [s for s, _ in sorted(katki.items(), key=lambda x: -x[1])[:3]]
    kol([g for g in G1 if g["sym"] not in top3], "x",
        f"6a. TOP-3 CIKARILDI ({', '.join(top3)})")

    gunler = sorted(set(g["gun"] for g in G1))
    orta = gunler[len(gunler) // 2]
    kol([g for g in G1 if g["gun"] < orta], "x", f"6b. ILK YARI (< {orta})")
    kol([g for g in G1 if g["gun"] >= orta], "x", f"6c. IKINCI YARI (>= {orta})")

    print("\n  " + "=" * 72)
    print("  ⚠ SINIRLAR (§3): TEK REJIM (~29,5 gun) — rejimler arasi genelleme")
    print("    YAPILAMAZ · hayatta kalma yanliligi (arsiv evreni hacim lideri) ·")
    print("    bu bir BILGI testidir, KARLILIK testi DEGILDIR.")
    print("  " + "=" * 72)


if __name__ == "__main__":
    main()
