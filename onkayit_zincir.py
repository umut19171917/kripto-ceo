"""ON-KAYIT OLCUM ARACI — `zincir` (ON-KAYIT-zincir.md, commit 38590d7)

Projenin sinadigi ILK GERCEK BANT DISI degisken: borsa giris/cikis akislari.

🔴 ANA DEGISKEN `z = net / 30g sd` — bicimi VERI SECTI (§2):
   ham giris/cikis tau ~8-9 gun -> etkin n 631/672 (gucsuz)
   net                tau 1,01g -> etkin n 5.576  (guclu)

SALT OKURDUR. Canli hicbir dosyaya yazmaz. `olcum.py` cikarim katmanini
kullanir — permutasyon hesaplanmadan hukum basilmaz (madde 8.4).

Kullanim:  venv\\Scripts\\python.exe onkayit_zincir.py
"""
import sys as _sys
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import json
import os
import random
import statistics as st
import time
from collections import defaultdict

import requests

import olcum

ON_KAYIT_COMMIT = "38590d7"
BASLANGIC = "2017-01-01"          # §3 — turdeslik gerekcesiyle, sonuca bakilmadan
SAPTANABILIR = 0.372              # §5
EKONOMIK_ESIK = olcum.EKONOMIK_ESIK
BANT = 5
TUR = 4000
ONBELLEK = os.path.join("_cache", "zincir")
CM = "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"
METRIKLER = "FlowInExNtv,FlowOutExNtv,AdrActCnt,PriceUSD"


# --------------------------------------------------------------------------
def veri():
    os.makedirs(ONBELLEK, exist_ok=True)
    yol = os.path.join(ONBELLEK, "btc_gunluk.json")
    if os.path.exists(yol):
        try:
            return json.load(open(yol, encoding="utf-8"))
        except Exception:
            pass
    out, sonraki = {}, None
    while True:
        p = {"assets": "btc", "metrics": METRIKLER, "frequency": "1d",
             "start_time": "2011-01-01", "page_size": 10000}
        if sonraki:
            p["next_page_token"] = sonraki
        r = requests.get(CM, params=p, headers={"User-Agent": "Mozilla/5.0"},
                         timeout=40)
        r.raise_for_status()
        j = r.json()
        for row in j.get("data", []):
            out[row["time"][:10]] = row
        sonraki = j.get("next_page_token")
        if not sonraki:
            break
        time.sleep(0.2)
    try:
        gecici = yol + ".tmp"
        json.dump(out, open(gecici, "w", encoding="utf-8"))
        os.replace(gecici, yol)
    except Exception:
        pass
    return out


def gozlemler(D):
    """§2 tanimlari BIREBIR. z'nin boleni YALNIZ gecmis 30 gunden."""
    gunler = sorted(D)
    net, fiyat, adr, ham_g, ham_c = {}, {}, {}, {}, {}
    for g in gunler:
        r = D[g]
        try:
            gi = float(r["FlowInExNtv"]); ci = float(r["FlowOutExNtv"])
            fiyat[g] = float(r["PriceUSD"])
            net[g] = ci - gi
            ham_g[g] = gi
            ham_c[g] = ci
        except (KeyError, TypeError, ValueError):
            continue
        try:
            adr[g] = float(r["AdrActCnt"])
        except (KeyError, TypeError, ValueError):
            pass

    ng = sorted(net)
    G = []
    for i, g in enumerate(ng):
        if i < 30 or g < BASLANGIC:
            continue
        pencere = [net[ng[j]] for j in range(i - 30, i)]     # 🔴 YALNIZ GECMIS
        sd = st.pstdev(pencere)
        if sd <= 0:
            continue
        # ertesi gunun getirisi
        idx = ng.index(g) if False else i
        if idx + 1 >= len(ng):
            continue
        yarin = ng[idx + 1]
        if g not in fiyat or yarin not in fiyat or fiyat[g] <= 0:
            continue
        kayit = {
            "gun": g, "sym": "BTC",
            "z": net[g] / sd,
            "ham_giris": ham_g[g], "ham_cikis": ham_c[g],
            "ileri": (fiyat[yarin] - fiyat[g]) / fiyat[g] * 100,
        }
        # kontrol kolu: aktif adres GUNLUK DEGISIMI
        onceki = ng[i - 1]
        if g in adr and onceki in adr and adr[onceki] > 0:
            kayit["adr_degisim"] = (adr[g] - adr[onceki]) / adr[onceki] * 100
        G.append(kayit)
    return G


# --------------------------------------------------------------------------
def bantla_tekil(G, alan):
    """Tek varlik -> sembol ici bantlama gereksiz; tum gunler esit sayili bese."""
    lst = sorted([g for g in G if alan in g], key=lambda g: g[alan])
    n = len(lst)
    for i, g in enumerate(lst):
        g["bant"] = min(BANT - 1, i * BANT // n)
    return lst


def cikarim(lst):
    """§4.2 uyarlamasi: gozlem = GUN oldugu icin gun-kumeli bootstrap
    siradan bootstrap'a indirgenir; permutasyon etiketleri TUM gunler
    arasinda karistirir. Tasarimin geregi, yontemden sapma DEGIL."""
    b = defaultdict(list)
    for g in lst:
        b[g["bant"]].append(g["ileri"])
    if not b[0] or not b[BANT - 1]:
        return None
    ort = [st.fmean(b[k]) for k in range(BANT)]
    med = [st.median(b[k]) for k in range(BANT)]
    kir = [olcum._kirp(b[k]) for k in range(BANT)]
    fark = ort[BANT - 1] - ort[0]
    rho = olcum.spearman(list(range(BANT)), ort)

    r = random.Random(olcum.TOHUM)
    a0, a4 = b[0], b[BANT - 1]
    boot = []
    for _ in range(TUR):
        s0 = st.fmean(r.choices(a0, k=len(a0)))
        s4 = st.fmean(r.choices(a4, k=len(a4)))
        boot.append(s4 - s0)
    boot.sort()
    ga = (boot[int(0.025 * TUR)], boot[int(0.975 * TUR)])

    etiketler = [g["bant"] for g in lst]
    getiriler = [g["ileri"] for g in lst]
    sifir = []
    calisma = list(etiketler)
    for _ in range(TUR):
        r.shuffle(calisma)
        t = [0.0] * BANT
        c = [0] * BANT
        for e, v in zip(calisma, getiriler):
            t[e] += v
            c[e] += 1
        if c[0] and c[BANT - 1]:
            sifir.append(t[BANT - 1] / c[BANT - 1] - t[0] / c[0])
    p = (sum(1 for x in sifir if abs(x) >= abs(fark)) + 1) / (len(sifir) + 1)
    return {"ort": ort, "med": med, "kir": kir, "fark": fark, "rho": rho,
            "ga": ga, "p": p, "n": len(lst)}


def kol(G, alan, ad, guclu=True):
    lst = bantla_tekil(G, alan)
    if len(lst) < 200:
        print(f"\n  {ad}: n={len(lst)} yetersiz")
        return None
    s = cikarim(lst)
    print(f"\n  {ad}   (n={s['n']:,})")
    print("  " + "-" * 72)
    print("    ortalama : " + "  ".join(f"{v:+7.3f}%" for v in s["ort"]))
    print("    MEDYAN   : " + "  ".join(f"{v:+7.3f}%" for v in s["med"]))
    print("    KIRPILMIS: " + "  ".join(f"{v:+7.3f}%" for v in s["kir"]))
    print(f"    rho={s['rho']:+.3f}   uc bant farki {s['fark']:+.3f}%")
    print(f"    [1] bootstrap GA95   : [{s['ga'][0]:+.3f}%, {s['ga'][1]:+.3f}%]")
    print(f"    [2] etiket permutasyon: p = {s['p']:.4f}")
    if not guclu:
        print("    §5 HUKMU: ⚠ OLCULEMEDI — bu kol gucsuz (on kayitta ilan edildi)")
        return s
    disliyor = s["ga"][0] > 0 or s["ga"][1] < 0
    ayni = ((s["fark"] > 0) == (s["med"][BANT-1] - s["med"][0] > 0)
            and (s["fark"] > 0) == (s["kir"][BANT-1] - s["kir"][0] > 0))
    if not (disliyor and s["p"] < 0.05):
        h = "❌ BILGI YOK (iki cikarimin ikisi birden gerekli)"
    elif not ayni:
        h = "❌ UC DEGER ESERI — ortalama ile medyan/kirpilmis ayni yonde degil"
    elif abs(s["fark"]) >= EKONOMIK_ESIK and abs(s["rho"]) >= olcum.RHO_ESIK:
        h = "✅ BANT DISINDA BILGI VAR -> mekanik asamasi icin AYRI on kayit"
    elif abs(s["fark"]) >= olcum.MALIYET_UZUN_KISA:
        h = "⚠ istatistiksel VAR, ekonomik YOK (%0,26-0,5 bandi)"
    else:
        h = "⚠ istatistiksel VAR ama fark maliyetin (%0,26) ALTINDA"
    print(f"    §6 HUKMU: {h}")
    s["gecti"] = h.startswith("✅")
    return s


def main():
    print("=" * 78)
    print("  ON-KAYITLI OLCUM — zincir (borsa akislari)")
    print(f"  on kayit: ON-KAYIT-zincir.md (commit {ON_KAYIT_COMMIT})")
    print(f"  pencere: {BASLANGIC} -> bugun · saptanabilir (§5): %{SAPTANABILIR}")
    print("  🔴 PROJENIN SINADIGI ILK GERCEK BANT DISI DEGISKEN")
    print("=" * 78)

    D = veri()
    G = gozlemler(D)
    if len(G) < 500:
        print(f"\n  gozlem yetersiz: {len(G)}")
        return
    print(f"\n  1. KAPSAMA")
    print("  " + "-" * 72)
    print(f"    gun: {len(G):,}   ({G[0]['gun']} -> {G[-1]['gun']})")
    print(f"    kontrol kolu verisi olan gun: {sum(1 for g in G if 'adr_degisim' in g):,}")

    print("\n  2-3. ANA SORU + UC DEGER DENETIMI")
    print("  " + "=" * 72)
    ana = kol(G, "z", "2. NET BORSA AKISI (z = net / 30g sd) -> ERTESI GUN")

    print("\n  4. KONTROL KOLU (madde 8.2)")
    print("  " + "=" * 72)
    kontrol = kol(G, "adr_degisim", "4. AKTIF ADRES gunluk degisimi")

    print("\n  5. GUCSUZ KOLLAR — hukum DOGURMAZ (§5'te ilan edildi)")
    print("  " + "=" * 72)
    kol(G, "ham_giris", "5a. HAM GIRIS", guclu=False)
    kol(G, "ham_cikis", "5b. HAM CIKIS", guclu=False)

    print("\n  6. SAGLAMLIK")
    print("  " + "=" * 72)
    orta = G[len(G) // 2]["gun"]
    for ad, alt in ((f"6a. ILK YARI (< {orta})", [g for g in G if g["gun"] < orta]),
                    (f"6b. IKINCI YARI (>= {orta})", [g for g in G if g["gun"] >= orta])):
        kol(alt, "z", ad)

    print("\n  " + "=" * 72)
    print("  §6 PESINEN KONAN IKI KURAL")
    print("  " + "=" * 72)
    if ana and kontrol:
        if ana.get("gecti") and kontrol.get("gecti"):
            print("  🔴 KONTROL KOLU DA GECTI -> ana kolun sonucu ZAYIFLAR.")
            print("     Bulunan sey borsa akisina OZGU degil, herhangi bir")
            print("     zincir-ustu serinin tasidigi GENEL bilgi olabilir.")
        elif not ana.get("gecti") and kontrol.get("gecti"):
            print("  ⚠ ANA KOL DUSTU, ikincil kol gecti -> BU BULGU DEGILDIR.")
            print("     Alti kol raporlandi; birinin p<0,05 cikmasi BEKLENIR.")
        else:
            print("  ✅ Kontrol kolu ana kolu golgelemiyor.")
    print("\n  ⚠ SINIRLAR: tek varlik (BTC) · tek pencere · bu bir BILGI testidir,")
    print("    KARLILIK testi DEGILDIR. Mekanik asamasi icin ayrica taban_R sarti")
    print("    vardir (sablon §6: ana sicil 0,1736R · radar 0,0279R).")
    print("  " + "=" * 78)


if __name__ == "__main__":
    main()
