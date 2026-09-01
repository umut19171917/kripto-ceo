"""ON-KAYIT OLCUM ARACI — `ucesik` (ON-KAYIT-ucesik.md, commit e2a070e)

Madde 3.2'nin acik parcasi: funding UCLARDA bilgi tasiyor mu? (U bicimi)

🔴 KESIF/TEST AYRIMI (§0): hipotez `basis`in 10 sembolunde DOGDU. O semboller
   bu olcume HIC girmez. Hukum yalniz 132 baska semboldan.

ANA ISTATISTIK: uc_orta = ort(bant 1+5) - ort(bant 2+3+4)
   Gerekce: Madde 6 uclarda atesler; monotonik istatistik U bicimine KORDUR.

SALT OKURDUR. Kullanim:  venv\\Scripts\\python.exe onkayit_ucesik.py
"""
import sys as _sys
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import bisect
import json
import os
import random
import statistics as st
import time
from collections import defaultdict
from datetime import datetime, timezone

import requests

import olcucu
import olcum

ON_KAYIT_COMMIT = "e2a070e"
BASE = "https://fapi.binance.com"
GUN = 86400_000
PENCERE_GUN = 1460
MIN_GUN = 1095                    # §3: >= 3 yil
BANT = 5
TUR = 4000
SAPTANABILIR = 0.367              # §5
KESIF = set(olcucu.SYMBOLS)       # §0: HUKUM DOGURMAZ, olcume GIRMEZ
ONBELLEK = os.path.join("_cache", "ucesik")


def _ist(yol, params, deneme=3):
    for k in range(deneme):
        try:
            r = requests.get(BASE + yol, params=params, timeout=25)
            if r.status_code == 200:
                return r.json()
            if r.status_code in (418, 429):
                time.sleep(4 * (k + 1))
                continue
            return None
        except Exception:
            time.sleep(2)
    return None


def test_kumesi(t0):
    d = _ist("/fapi/v1/exchangeInfo", {})
    if not d:
        return []
    tum = [s["symbol"] for s in d["symbols"]
           if s.get("contractType") == "PERPETUAL" and s.get("status") == "TRADING"
           and s["symbol"].endswith("USDT") and s["symbol"] not in KESIF]
    return sorted(tum)


_ELENEN_YOL = os.path.join(ONBELLEK, "_elenen.json")
_elenen_kume = None


def _elenen():
    global _elenen_kume
    if _elenen_kume is None:
        try:
            _elenen_kume = set(json.load(open(_ELENEN_YOL, encoding="utf-8")))
        except Exception:
            _elenen_kume = set()
    return _elenen_kume


def _elenen_ekle(sym):
    _elenen().add(sym)
    try:
        os.makedirs(ONBELLEK, exist_ok=True)
        gecici = _ELENEN_YOL + ".tmp"
        json.dump(sorted(_elenen_kume), open(gecici, "w", encoding="utf-8"))
        os.replace(gecici, _ELENEN_YOL)
    except Exception:
        pass


def sembol_verisi(sym, t0, t1):
    """Gunluk bar + funding. Doner: [(gun_ms, acilis, kapanis)], [(ft, oran)]"""
    os.makedirs(ONBELLEK, exist_ok=True)
    yol = os.path.join(ONBELLEK, f"{sym}.json")
    if os.path.exists(yol):
        try:
            j = json.load(open(yol, encoding="utf-8"))
            return j["bar"], j["fund"]
        except Exception:
            pass
    # 🔴 ELENENLERI DE ONBELLEKLE: aday havuz 515, gecen 132. Elenen ~380
    # sembol her kosumda yeniden sorgulaniyordu ve sure oradan sisiyordu.
    # Bu yalniz AG tasarrufudur; hangi sembolun elendigi ayni olcutle belirlenir.
    if sym in _elenen():
        return None, None
    k = _ist("/fapi/v1/klines", {"symbol": sym, "interval": "1d",
                                 "startTime": t0, "limit": 1500})
    if not k or len(k) < MIN_GUN:
        _elenen_ekle(sym)
        return None, None
    bar = [[int(x[0]), float(x[1]), float(x[4])] for x in k]
    fund, t = [], t0
    while t < t1:
        f = _ist("/fapi/v1/fundingRate",
                 {"symbol": sym, "startTime": t, "limit": 1000})
        if not f:
            break
        fund += [[int(x["fundingTime"]), float(x["fundingRate"]) * 100] for x in f]
        t = int(f[-1]["fundingTime"]) + 1
        if len(f) < 1000:
            break
        time.sleep(0.08)
    fund.sort()
    if len(fund) < MIN_GUN:
        return None, None
    try:
        gecici = yol + ".tmp"
        json.dump({"bar": bar, "fund": fund}, open(gecici, "w", encoding="utf-8"))
        os.replace(gecici, yol)
    except Exception:
        pass
    return bar, fund


def gozlemler(sym, bar, fund):
    """§2 tanimlari BIREBIR. f_t: fundingTime < gun_acilisi (KESIN kucuk)."""
    ft = [x[0] for x in fund]
    G = []
    for gun_ms, acilis, kapanis in bar:
        if acilis <= 0:
            continue
        i = bisect.bisect_left(ft, gun_ms) - 1      # 🔴 KESIN ONCE
        if i < 0:
            continue
        G.append({"sym": sym,
                  "gun": datetime.fromtimestamp(gun_ms / 1000, timezone.utc).date().isoformat(),
                  "f": fund[i][1],
                  "ileri": (kapanis - acilis) / acilis * 100})
    return G


def bantla(G):
    per = defaultdict(list)
    for g in G:
        per[g["sym"]].append(g)
    for lst in per.values():
        lst.sort(key=lambda g: g["f"])
        n = len(lst)
        for i, g in enumerate(lst):
            g["bant"] = min(BANT - 1, i * BANT // n)
    return G


def uc_orta(G):
    uc = [g["ileri"] for g in G if g["bant"] in (0, BANT - 1)]
    orta = [g["ileri"] for g in G if g["bant"] in (1, 2, 3)]
    if not uc or not orta:
        return None
    return st.fmean(uc) - st.fmean(orta)


def cikarim(G):
    """Gun-kumeli bootstrap + gun-ici etiket permutasyonu (olcum deseni)."""
    gozlenen = uc_orta(G)
    gunler = defaultdict(list)
    for g in G:
        gunler[g["gun"]].append(g)
    bl = []
    for v in gunler.values():
        su = sum(x["ileri"] for x in v if x["bant"] in (0, BANT - 1))
        cu = sum(1 for x in v if x["bant"] in (0, BANT - 1))
        so = sum(x["ileri"] for x in v if x["bant"] in (1, 2, 3))
        co = sum(1 for x in v if x["bant"] in (1, 2, 3))
        bl.append((su, cu, so, co))
    n = len(bl)
    r = random.Random(olcum.TOHUM)
    boot = []
    for _ in range(TUR):
        su = cu = so = co = 0
        for _ in range(n):
            a, b, c, d = bl[r.randrange(n)]
            su += a; cu += b; so += c; co += d
        if cu and co:
            boot.append(su / cu - so / co)
    boot.sort()
    ga = (boot[int(0.025 * len(boot))], boot[int(0.975 * len(boot))])

    # --- gun ICI etiket permutasyonu ---
    # 🔴 HIZ NOTU (2026-09-01, ilk kosum 1,5 saat surecekti): etiketleri
    # karistirip butun gozlemleri gezmek tur basina 184 bin Python adimi
    # ediyordu (4.000 tur = 736 milyon). MATEMATIKSEL OLARAK OZDES ama C
    # seviyesinde calisan bicim: gun icinde etiket karistirmak, o gunun
    # getirilerinden UC SAYISI KADARINI rastgele secmekle AYNI SEYDIR.
    # Secim `random.sample`, toplama `sum` -> ikisi de C.
    # Olcut/esik/istatistik DEGISMEDI; yalniz ayni sonuca daha az adimda
    # varilyor. ⚠ Rastgele cekilis sirasi degistigi icin p'nin son
    # basamaklari ilk surumden farkli cikar — Monte Carlo gurultusudur.
    bloklar = []
    for v in gunler.values():
        deger = [x["ileri"] for x in v]
        k = sum(1 for x in v if x["bant"] in (0, BANT - 1))
        if 0 < k < len(deger):
            bloklar.append((deger, k, sum(deger), len(deger)))
        elif deger:                       # gunun tamami tek grupta
            bloklar.append((deger, k, sum(deger), len(deger)))
    ornekle = r.sample
    sifir = []
    for _ in range(TUR):
        su = 0.0; cu = 0; so = 0.0; co = 0
        for deger, k, toplam, nn in bloklar:
            if k <= 0:
                so += toplam; co += nn
            elif k >= nn:
                su += toplam; cu += nn
            else:
                s = sum(ornekle(deger, k))
                su += s; cu += k
                so += toplam - s; co += nn - k
        if cu and co:
            sifir.append(su / cu - so / co)
    p = (sum(1 for x in sifir if abs(x) >= abs(gozlenen)) + 1) / (len(sifir) + 1)
    return gozlenen, ga, p, n


def main():
    print("=" * 78)
    print("  ON-KAYITLI OLCUM — ucesik (funding UCLARDA bilgi var mi?)")
    print(f"  on kayit: ON-KAYIT-ucesik.md (commit {ON_KAYIT_COMMIT})")
    print(f"  saptanabilir (§5): %{SAPTANABILIR}   ekonomik esik: %{olcum.EKONOMIK_ESIK}")
    print("  🔴 KESIF KUMESI (10 sembol) BU OLCUME GIRMEZ (§0)")
    print("=" * 78)

    t1 = int(time.time() * 1000) // GUN * GUN
    t0 = t1 - PENCERE_GUN * GUN
    adaylar = test_kumesi(t0)
    print(f"\n  1. KAPSAMA")
    print("  " + "-" * 72)
    print(f"    aday havuz (kesif HARIC): {len(adaylar)}")

    G = []
    kabul = 0
    for i, sym in enumerate(adaylar):
        bar, fund = sembol_verisi(sym, t0, t1)
        if not bar:
            continue
        g = gozlemler(sym, bar, fund)
        if len(g) >= MIN_GUN:
            G += g
            kabul += 1
        if i % 25 == 24:
            time.sleep(0.3)
    print(f"    >=3 yil verisi olan (TEST kumesi): {kabul} sembol")
    print(f"    sembol-gun: {len(G):,}   takvim gunu: {len(set(g['gun'] for g in G)):,}")
    if kabul < 30 or len(G) < 20000:
        print("\n  ⚠ ornekem yetersiz — hukum basilmiyor")
        return

    # kesif kumesi sizmasi denetimi (§9 gecersizlik sarti)
    sizinti = KESIF & set(g["sym"] for g in G)
    print(f"    🔴 kesif kumesi sizintisi: {len(sizinti)} "
          f"{'(TAMAM)' if not sizinti else '-> GECERSIZ: ' + str(sizinti)}")
    if sizinti:
        return

    bantla(G)
    b = defaultdict(list)
    for g in G:
        b[g["bant"]].append(g["ileri"])
    ort = [st.fmean(b[k]) for k in range(BANT)]

    print("\n  2. ANA — uc_orta = ort(bant 1+5) - ort(bant 2+3+4)")
    print("  " + "-" * 72)
    print("    bant ortalamalari: " + "  ".join(f"{v:+6.3f}%" for v in ort))
    gozlenen, ga, p, nblok = cikarim(G)
    print(f"    uc_orta = {gozlenen:+.3f}%")
    print(f"    [1] gun-kumeli bootstrap GA95 : [{ga[0]:+.3f}%, {ga[1]:+.3f}%]  ({nblok} gun)")
    print(f"    [2] gun-ici permutasyon       : p = {p:.4f}")

    print("\n  3. KARSILASTIRMA — MONOTONIK istatistik (kor muydu?)")
    print("  " + "-" * 72)
    rho = olcum.spearman(list(range(BANT)), ort)
    print(f"    bant5 - bant1 = {ort[BANT-1]-ort[0]:+.3f}%   Spearman rho = {rho:+.3f}")

    print("\n  5. UC DEGER DENETIMI")
    print("  " + "-" * 72)
    uc = [g["ileri"] for g in G if g["bant"] in (0, BANT - 1)]
    orta_l = [g["ileri"] for g in G if g["bant"] in (1, 2, 3)]
    print(f"    medyan farki   : {st.median(uc) - st.median(orta_l):+.3f}%")
    print(f"    kirpilmis farki: {olcum._kirp(uc) - olcum._kirp(orta_l):+.3f}%")

    print("\n  6. KONTROL KOLU — RASTGELE bant etiketi (madde 8.2)")
    print("  " + "-" * 72)
    r2 = random.Random(777)
    K = [dict(g) for g in G]
    per = defaultdict(list)
    for g in K:
        per[g["sym"]].append(g)
    for lst in per.values():
        etik = [g["bant"] for g in lst]
        r2.shuffle(etik)
        for g, e in zip(lst, etik):
            g["bant"] = e
    kg, kga, kp, _ = cikarim(K)
    print(f"    uc_orta = {kg:+.3f}%   GA95 [{kga[0]:+.3f}%, {kga[1]:+.3f}%]   p={kp:.4f}")
    kontrol_gecti = (kga[0] > 0 or kga[1] < 0) and kp < 0.05

    print("\n  7. SAGLAMLIK")
    print("  " + "-" * 72)
    gs = sorted(set(g["gun"] for g in G))
    orta_gun = gs[len(gs) // 2]
    for ad, alt in ((f"ilk yari (< {orta_gun})", [g for g in G if g["gun"] < orta_gun]),
                    (f"ikinci yari (>= {orta_gun})", [g for g in G if g["gun"] >= orta_gun])):
        if len(alt) < 5000:
            continue
        o, gaa, pp, _ = cikarim(alt)
        print(f"    {ad:28s} uc_orta {o:+.3f}%  GA [{gaa[0]:+.3f}, {gaa[1]:+.3f}]  p={pp:.4f}")

    # ---- HUKUM ----
    print("\n  " + "=" * 72)
    print("  §6 KARAR KURALI")
    print("  " + "=" * 72)
    if kontrol_gecti:
        print("  🔴 TASARIM HATASI — kontrol kolu (rastgele etiket) de gecti.")
        print("     Hicbir sonuc okunmaz, arac incelenir.")
        return
    disliyor = ga[0] > 0 or ga[1] < 0
    med_ayni = (gozlenen > 0) == (st.median(uc) - st.median(orta_l) > 0)
    kir_ayni = (gozlenen > 0) == (olcum._kirp(uc) - olcum._kirp(orta_l) > 0)
    if not (disliyor and p < 0.05):
        h = ("❌ UCLARDA DA BILGI YOK -> Madde 6 EMEKLILIK ADAYIDIR (§7)")
    elif gozlenen < 0:
        h = ("⚠ ISARET TERS — on kayit POZITIF bekliyordu (§6). basis'teki "
             "gozlemin TERSI; 'bulduk' DENEMEZ, ayri hipotezdir")
    elif not (med_ayni and kir_ayni):
        h = "❌ UC DEGER ESERI — ortalama ile medyan/kirpilmis ayni yonde degil"
    elif gozlenen >= olcum.EKONOMIK_ESIK:
        h = "✅ UCLARDA BILGI VAR -> Madde 6 DOGRULANDI; mekanik icin ayri on kayit"
    elif gozlenen >= olcum.MALIYET_UZUN_KISA:
        h = "⚠ istatistiksel VAR, ekonomik YOK — Madde 6 kalir ama GUCLENDIRILMEZ"
    else:
        h = "⚠ istatistiksel VAR ama fark maliyetin (%0,26) ALTINDA"
    print(f"  {h}")
    print("\n  ⚠ SINIR (§0): test kumesi kesif kumesinden TAM BAGIMSIZ DEGIL —")
    print("    kripto sembolleri birlikte hareket eder. Elimizdeki en iyi ayrim bu.")
    print("  ⚠ Hayatta kalma yanliligi: bugun TRADING olan semboller (§3).")
    print("  " + "=" * 72)


if __name__ == "__main__":
    main()
