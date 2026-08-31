"""ON-KAYIT OLCUM ARACI — `maliyet` (ON-KAYIT-maliyet.md, commit d932217)

Soru: baglayici kisit MALIYET mi, YON mu?
ASIL CIKTI: `taban_R` — her gelecek adayin asmak zorunda oldugu maliyet tabani.

SALT OKURDUR. `defter.maliyet_R` (tek sahip) ve `olcum.py` kullanilir.

Kullanim:  venv\\Scripts\\python.exe onkayit_maliyet.py
"""
import sys as _sys
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import json
import math
import random
import statistics as st
from collections import defaultdict
from datetime import datetime

import defter
import olcum

ON_KAYIT_COMMIT = "d932217"
SAPTANABILIR = 0.354            # §5 — sonuc gorulmeden hesaplandi
GURULTU_TABANI = 0.03           # proje teamulu
KAPALI = ("tp1", "tp2", "stop", "zaman_asimi")
TUR = 4000


def kayitlar(dosya):
    T = json.load(open(dosya, encoding="utf-8"))["tahminler"]
    out = []
    for t in T:
        if t.get("durum") not in KAPALI or t.get("sonuc_R") is None:
            continue
        if t.get("kaynak") == "backtest" or t.get("backtest"):
            continue                                   # §3: geri-doldurma haric
        if t.get("token") in getattr(__import__("olcucu"), "DENEYSEL", set()):
            continue                                   # §3: LAB haric
        g = t.get("giris")
        s = t.get("stop")
        if not g or not s or g <= 0:
            continue
        t["_mal"] = defter.maliyet_R(t)
        t["_brut"] = t["sonuc_R"]
        t["_net"] = t["_brut"] - t["_mal"]
        t["_stop_pct"] = abs(g - s) / g * 100
        t["_gun"] = (t.get("kapanis_tarih") or t.get("tarih") or "")[:10]
        out.append(t)
    return out


def gun_kumeli(degerler, gunler):
    """Gun-kumeli GA95 + isaret permutasyonu (olcum.py deseni)."""
    if len(degerler) < 20:
        return None, None
    g = defaultdict(list)
    for v, gun in zip(degerler, gunler):
        g[gun].append(v)
    bl = [(sum(v), len(v)) for v in g.values()]
    n = len(bl)
    ort = st.fmean(degerler)
    r = random.Random(olcum.TOHUM)
    boot = []
    for _ in range(TUR):
        t = a = 0
        for _ in range(n):
            s, c = bl[r.randrange(n)]
            t += s
            a += c
        if a:
            boot.append(t / a)
    boot.sort()
    ga = (boot[int(0.025 * len(boot))], boot[int(0.975 * len(boot))])
    bloklar = list(g.values())
    sifir = []
    for _ in range(TUR):
        t = a = 0
        for v in bloklar:
            isaret = 1 if r.random() < 0.5 else -1
            t += isaret * sum(v)
            a += len(v)
        if a:
            sifir.append(t / a)
    p = (sum(1 for x in sifir if abs(x) >= abs(ort)) + 1) / (len(sifir) + 1)
    return ga, p


def sicil(ad, dosya):
    K = kayitlar(dosya)
    if len(K) < 30:
        print(f"\n  {ad}: n={len(K)} — yetersiz, atlandi")
        return None
    brut = [t["_brut"] for t in K]
    mal = [t["_mal"] for t in K]
    net = [t["_net"] for t in K]
    gunler = [t["_gun"] for t in K]

    print(f"\n  {'=' * 72}")
    print(f"  {ad}   n={len(K)}   kapanis gunu={len(set(gunler))}")
    print(f"  {'=' * 72}")

    # --- 2. AYRISTIRMA ---
    print("\n  2. AYRISTIRMA")
    print(f"    {'':10s} {'toplam':>10s} {'islem basina':>14s}")
    for etiket, v in (("BRUT", brut), ("MALIYET", mal), ("NET", net)):
        print(f"    {etiket:10s} {sum(v):+10.2f}R {st.fmean(v):+13.4f}R")

    # --- 3. MALIYET DAGILIMI ---
    ms = sorted(mal)
    q1, q3 = ms[len(ms) // 4], ms[3 * len(ms) // 4]
    en_pahali = ms[int(0.9 * len(ms)):]
    pay = sum(en_pahali) / sum(mal) * 100
    print("\n  3. MALIYET DAGILIMI")
    print(f"    ortalama {st.fmean(mal):.4f}R · medyan {st.median(mal):.4f}R · "
          f"Q1 {q1:.4f}R · Q3 {q3:.4f}R · max {ms[-1]:.4f}R")
    print(f"    en pahali %10 islemin toplam maliyetteki payi: %{pay:.1f}")
    carpik = st.fmean(mal) > 1.5 * st.median(mal)
    print(f"    -> dagilim {'CARPIK (ortalama medyanin 1,5 katindan buyuk)' if carpik else 'dengeli'}")

    # --- 4. BRUT SIFIRDAN AYIRT EDILEBILIYOR MU ---
    ga, p = gun_kumeli(brut, gunler)
    print("\n  4. BRUT SIFIRDAN AYIRT EDILEBILIYOR MU")
    if ga:
        disliyor = ga[0] > 0 or ga[1] < 0
        print(f"    brut ort {st.fmean(brut):+.4f}R   gun-kumeli GA95 "
              f"[{ga[0]:+.4f}, {ga[1]:+.4f}]   isaret-perm p={p:.4f}")
        print(f"    -> GA sifiri {'DISLIYOR' if disliyor else 'KAPSIYOR'} · "
              f"p {'<' if p < 0.05 else '>='} 0,05")
    else:
        disliyor = False
        print("    hesaplanamadi")

    # --- 5. SURUCU (mekanik dogrulama, BULGU DEGIL) ---
    sp = [t["_stop_pct"] for t in K]
    rho = olcum.spearman(sp, mal)
    print("\n  5. SURUCU — maliyet vs stop genisligi (MEKANIK DOGRULAMA, bulgu DEGIL)")
    print(f"    stop_pct: ortalama %{st.fmean(sp):.3f} · medyan %{st.median(sp):.3f}")
    print(f"    Spearman rho(stop_pct, maliyet_R) = {rho:+.3f}")
    print(f"    -> beklenen: kuvvetli NEGATIF (maliyet ~ 1/stop_pct). "
          f"{'DOGRULANDI' if rho < -0.8 else '🔴 BEKLENEN CIKMADI — HESAPTA HATA OLABILIR'}")

    # --- 6. TABAN ---
    taban = st.fmean(mal)
    print("\n  6. 🔴 TABAN — net pozitif icin gereken en kucuk BRUT kenar")
    print(f"    taban_R = {taban:.4f}R")
    print(f"    gurultu tabaninin ({GURULTU_TABANI}R) {taban/GURULTU_TABANI:.1f} kati")
    print(f"    saptanabilir brut kenarin ({SAPTANABILIR}R) "
          f"{taban/SAPTANABILIR:.2f} kati")

    # --- 7. SAGLAMLIK ---
    print("\n  7. SAGLAMLIK")
    esik90 = ms[int(0.9 * len(ms))]
    ucuz = [t for t in K if t["_mal"] < esik90]
    print(f"    en pahali %10 CIKARILDI -> taban_R "
          f"{st.fmean([t['_mal'] for t in ucuz]):.4f}R "
          f"(tumu: {taban:.4f}R)")
    gs = sorted(set(gunler))
    orta = gs[len(gs) // 2]
    for etiket, alt in (("ilk yari", [t for t in K if t["_gun"] < orta]),
                        ("ikinci yari", [t for t in K if t["_gun"] >= orta])):
        if len(alt) < 20:
            continue
        print(f"    {etiket:12s} n={len(alt):3d}  taban_R "
              f"{st.fmean([t['_mal'] for t in alt]):.4f}R  "
              f"brut {st.fmean([t['_brut'] for t in alt]):+.4f}R")

    # --- HUKUM ---
    print("\n  §6 KARAR KURALI")
    if carpik and st.fmean([t["_mal"] for t in ucuz]) < taban * 0.5:
        h = "⚠ MALIYET BIRKAC ISLEMIN ESERI — genel sonuc yazilamaz"
    elif taban > SAPTANABILIR:
        h = ("❌ BU SICIL YAPISAL OLARAK KARLI OLAMAZ: odedigi maliyet, "
             "olcebilecegimiz en kucuk kenardan BUYUK")
    elif disliyor and p < 0.05:
        h = "✅ Kenar var ve maliyeti karsiliyor OLABILIR -> ayri on kayit"
    else:
        h = ("⚠ BAGLAYICI KISIT MALIYET DEGIL BELIRSIZLIK: maliyet odenebilir "
             "buyuklukte ama kenarin VARLIGI gosterilemiyor")
    print(f"    {h}")
    return {"ad": ad, "taban": taban, "n": len(K), "brut": st.fmean(brut),
            "hukum": h}


def main():
    print("=" * 78)
    print("  ON-KAYITLI OLCUM — maliyet (baglayici kisit maliyet mi, yon mu?)")
    print(f"  on kayit: ON-KAYIT-maliyet.md (commit {ON_KAYIT_COMMIT})")
    print(f"  saptanabilir en kucuk brut kenar (§5): {SAPTANABILIR}R")
    print("  🔴 IKI SICIL AYRI RAPORLANIR, TOPLANMAZ (§3)")
    print("=" * 78)

    S = []
    for ad, f in (("ANA SICIL", "kripto-defter.json"),
                  ("RADAR", "radar-defter.json")):
        r = sicil(ad, f)
        if r:
            S.append(r)

    print("\n" + "=" * 78)
    print("  🔴 GELECEK ON KAYITLARA GIRECEK ESIK")
    print("=" * 78)
    for r in S:
        print(f"    {r['ad']:12s} taban_R = {r['taban']:.4f}R   (n={r['n']})")
    print("\n    Bir aday 'bilgi var' dese bile, buldugu kenar ilgili sicilin")
    print("    taban_R'sinin ALTINDAYSA mekanik asamasina GECILMEZ.")
    print("\n  ⛔ YASAK (§6): 'stop'u genisletirsek maliyet duser, deneyelim.'")
    print("     Bu bir PARAMETRE TARAMASIDIR. Stop genisletmenin BRUT uzerindeki")
    print("     etkisi olculmeden boyle bir cumle kurulamaz.")
    print("  ⚠ SINIR: tek donem, tek rejim. Iki sicil TOPLANMADI.")
    print("=" * 78)


if __name__ == "__main__":
    main()
