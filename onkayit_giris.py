"""ON-KAYIT OLCUM ARACI — `giris` (ON-KAYIT-giris.md, commit cf69073)

Madde 5.2 — TERS SECILIM. Kirilim girisi kenari mi yiyor?

UC KOL, AYNI 462 SINYAL, ayni stop/TP/pencere/maliyet:
  A KIRILIM   : swing_low'a kirilim (mevcut kural)
  B ANINDA    : sinyal barinin kapanisindan hemen gir (kontrol)
  C RASTGELE  : 24s penceresi icinde rastgele saatten gir (plasebo)

SALT OKURDUR. Sinyal ve mum yolu `onkayit_mekanik`ten CAGRILIR (madde 8.3).
Cikarim `olcum.py`den gelir — permutasyon hesaplanmadan hukum basilmaz (8.4).

Kullanim:  venv\\Scripts\\python.exe onkayit_giris.py
"""
import sys as _sys
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import math
import random
import statistics as st
from collections import Counter, defaultdict
from datetime import datetime, timezone

import defter
import olcucu
import olcum
import onkayit_mekanik as M

ON_KAYIT_COMMIT = "cf69073"
SAPTANABILIR = 0.241            # §5 — sonuc gorulmeden hesaplandi
TUR = 4000
rnd = random.Random(11)         # §2: sinyal basina TEK cekilis


# --------------------------------------------------------------------------
# Ortak cozum motoru — uc kol da AYNI fonksiyonu kullanir (sapma imkansiz)
# --------------------------------------------------------------------------
def _coz(bars, i_giris, giris, stop, tp1, tp2):
    """i_giris barindan itibaren ACTIVE penceresinde coz. TEMKINLI: stop oncelikli."""
    risk = giris - stop                      # SHORT: stop USTTE, risk negatif degil
    sonuc, cikis, cj = "zaman_asimi", None, None
    for j in range(i_giris, min(i_giris + M.ACTIVE, len(bars))):
        b = bars[j]
        if b["h"] >= stop:
            sonuc, cikis, cj = "stop", stop, j
            break
        if b["l"] <= tp2:
            sonuc, cikis, cj = "tp2", tp2, j
            break
        if b["l"] <= tp1:
            sonuc, cikis, cj = "tp1", tp1, j
            break
    son = min(i_giris + M.ACTIVE, len(bars)) - 1
    if cikis is None:
        cikis, cj = bars[son]["c"], son
    brut = (giris - cikis) / abs(risk)       # SHORT: dusus = kar
    mal = defter.maliyet_R({"giris": giris, "stop": stop, "yon": "SHORT"})
    return {"durum": sonuc, "net_R": brut - mal, "cikis_ts": bars[cj]["t"]}


def kollar(r, bars):
    """Tek sinyal icin uc kolu birden uretir. Doner: {"A":..,"B":..,"C":..} veya None."""
    ms = int(r["dt"].timestamp() * 1000)
    i = next((j for j, b in enumerate(bars) if b["t"] >= ms), None)
    if i is None or i < M.LOOKBACK + 15:
        return None
    swing_low = min(b["l"] for b in bars[i - M.LOOKBACK:i])
    atr = olcucu.atr(bars[:i], 14)
    if not atr or atr <= 0:
        return None

    def kur(giris):
        stop = giris + atr * M.STOP_ATR
        tp1 = giris - atr * M.TP1_ATR
        tp2 = giris - atr * M.TP2_ATR
        if giris <= 0 or min(tp1, tp2) <= 0:
            return None
        if (stop - giris) / giris * 100 < M.TABAN:
            return None
        return stop, tp1, tp2

    # --- A: KIRILIM ---
    k = kur(swing_low)
    if k is None:
        return None
    stopA, tp1A, tp2A = k
    tetik = None
    for j in range(i, min(i + M.PENDING, len(bars))):
        if bars[j]["l"] <= swing_low:
            tetik = j
            break
    A = ({"durum": "tetiklenmedi", "net_R": 0.0, "cikis_ts": None}
         if tetik is None else _coz(bars, tetik, swing_low, stopA, tp1A, tp2A))

    # --- B: ANINDA (sinyal barinin kapanisi) ---
    girisB = bars[i]["c"]
    kb = kur(girisB)
    B = _coz(bars, i + 1, girisB, *kb) if kb and i + 1 < len(bars) else None

    # --- C: RASTGELE (24s penceresi icinde rastgele saat) ---
    ust = min(i + M.PENDING, len(bars) - 1)
    C = None
    if ust > i:
        jc = rnd.randrange(i, ust)           # §2: sinyal basina TEK cekilis
        girisC = bars[jc]["c"]
        kc = kur(girisC)
        if kc and jc + 1 < len(bars):
            C = _coz(bars, jc + 1, girisC, *kc)
    return {"A": A, "B": B, "C": C}


# --------------------------------------------------------------------------
# Eslestirilmis fark — gun-kumeli GA + permutasyon
# --------------------------------------------------------------------------
def eslesmis(farklar, gunler):
    """farklar[i] ile gunler[i] eslesir. Doner (ort, GA95, p)."""
    if len(farklar) < 20:
        return None, None, None
    g = defaultdict(list)
    for f, gun in zip(farklar, gunler):
        g[gun].append(f)
    bl = [(sum(v), len(v)) for v in g.values()]
    n = len(bl)
    ort = sum(f for f in farklar) / len(farklar)

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

    # isaret permutasyonu: sifir hipotezi "fark simetrik, ortalamasi 0"
    # (eslestirilmis tasarimin dogal permutasyonu — gun bloklari korunur)
    sifir = []
    bloklar = list(g.values())
    for _ in range(TUR):
        t = a = 0
        for v in bloklar:
            isaret = 1 if r.random() < 0.5 else -1
            t += isaret * sum(v)
            a += len(v)
        if a:
            sifir.append(t / a)
    asan = sum(1 for x in sifir if abs(x) >= abs(ort))
    p = (asan + 1) / (len(sifir) + 1)
    return ort, ga, p


def kol_ozet(ad, kayitlar):
    islem = [k for k in kayitlar if k and k["durum"] != "tetiklenmedi"]
    if not islem:
        print(f"    {ad:12s} islem yok")
        return None
    R = [k["net_R"] for k in islem]
    say = Counter(k["durum"] for k in islem)
    print(f"    {ad:12s} islem {len(islem):3d}  ort {st.fmean(R):+.3f}R  "
          f"medyan {st.median(R):+.3f}R  " +
          " ".join(f"{k}:{v}" for k, v in say.most_common()))
    return R


def main():
    print("=" * 78)
    print("  ON-KAYITLI OLCUM — giris (madde 5.2: TERS SECILIM)")
    print(f"  on kayit: ON-KAYIT-giris.md (commit {ON_KAYIT_COMMIT})")
    print(f"  saptanabilir en kucuk fark (§5): {SAPTANABILIR}R")
    print("=" * 78)

    _, _, sig = M.sinyaller()
    bars = M.mumlar()
    S = []
    for r in sig:
        b = bars.get(r["sym"])
        if not b:
            continue
        k = kollar(r, b)
        if k is None or k["B"] is None or k["C"] is None:
            continue
        k["sym"] = r["sym"]
        k["gun"] = r["dt"].date().isoformat()
        S.append(k)

    print(f"\n  1. KAPSAMA")
    print("  " + "-" * 72)
    print(f"    uc kolu da kurulabilen sinyal: {len(S)}")
    tetik = sum(1 for k in S if k["A"]["durum"] != "tetiklenmedi")
    print(f"    A kolu tetiklenme: {tetik}/{len(S)} (%{100*tetik/max(len(S),1):.1f})")
    print(f"    takvim gunu: {len(set(k['gun'] for k in S))}")
    if len(S) < 100:
        print("\n  ⚠ ornekleme yetersiz — hukum basilmiyor")
        return

    print("\n  2. KOL BASINA (islem basina ortalama net R)")
    print("  " + "-" * 72)
    for ad in ("A", "B", "C"):
        kol_ozet({"A": "A KIRILIM", "B": "B ANINDA", "C": "C RASTGELE"}[ad],
                 [k[ad] for k in S])

    print("\n  3. ESLESTIRILMIS FARK — ayni sinyalde (A tetiklenmediyse katkisi 0R)")
    print("  " + "-" * 72)
    gunler = [k["gun"] for k in S]
    sonuc = {}
    for ad in ("B", "C"):
        farklar = [k[ad]["net_R"] - k["A"]["net_R"] for k in S]
        ort, ga, p = eslesmis(farklar, gunler)
        sonuc[ad] = (ort, ga, p)
        gs = f"[{ga[0]:+.3f}, {ga[1]:+.3f}]" if ga else "yok"
        print(f"    {ad} − A : {ort:+.3f}R   gun-kumeli GA95 {gs}   "
              f"isaret-permutasyon p={p:.4f}")

    print("\n  4. UC DEGER DENETIMI (medyan farki)")
    print("  " + "-" * 72)
    for ad in ("B", "C"):
        f = [k[ad]["net_R"] - k["A"]["net_R"] for k in S]
        print(f"    {ad} − A medyan: {st.median(f):+.3f}R   "
              f"kirpilmis: {olcum._kirp(f):+.3f}R")

    print("\n  5-6. SAGLAMLIK")
    print("  " + "-" * 72)
    katki = Counter()
    for k in S:
        katki[k["sym"]] += abs(k["C"]["net_R"] - k["A"]["net_R"])
    top3 = [s for s, _ in katki.most_common(3)]
    alt = [k for k in S if k["sym"] not in top3]
    if len(alt) >= 50:
        f = [k["C"]["net_R"] - k["A"]["net_R"] for k in alt]
        o, ga, p = eslesmis(f, [k["gun"] for k in alt])
        print(f"    top-3 ({', '.join(top3)}) CIKARILDI -> C−A {o:+.3f}R  "
              f"GA [{ga[0]:+.3f}, {ga[1]:+.3f}]  p={p:.4f}")
    gs = sorted(set(gunler))
    orta = gs[len(gs) // 2]
    for ad, alt in (("ilk yari", [k for k in S if k["gun"] < orta]),
                    ("ikinci yari", [k for k in S if k["gun"] >= orta])):
        if len(alt) < 50:
            continue
        f = [k["C"]["net_R"] - k["A"]["net_R"] for k in alt]
        o, ga, p = eslesmis(f, [k["gun"] for k in alt])
        print(f"    {ad:12s} -> C−A {o:+.3f}R  GA [{ga[0]:+.3f}, {ga[1]:+.3f}]  p={p:.4f}")

    # ---------------- HUKUM ----------------
    print("\n  " + "=" * 72)
    print("  §6 KARAR KURALI")
    print("  " + "=" * 72)
    ortC, gaC, pC = sonuc["C"]
    ortB, gaB, pB = sonuc["B"]

    def gecti(ort, ga, p):
        return (ga and (ga[0] > 0 or ga[1] < 0)) and p < 0.05 and abs(ort) >= SAPTANABILIR

    if gecti(ortC, gaC, pC) and ortC > 0:
        h = ("✅ TERS SECILIM VAR — kirilim sarti AKTIF OLARAK ZARARLI.\n"
             "     Emeklilik adayi (§7): kirilim girisi.")
    elif gecti(ortB, gaB, pB) and ortB > 0 and not gecti(ortC, gaC, pC):
        h = "⚠ Zararli olan BEKLEMENIN KENDISI, kirilim sarti degil."
    elif gecti(ortC, gaC, pC) and ortC < 0:
        h = "🔵 TERSI CIKTI — kirilim sarti KORUYUCU. Beklentim curudu."
    else:
        h = ("❌ GIRIS MEKANIGI SUCSUZ — uc kol arasinda saptanabilir fark yok.\n"
             "     Kenari yiyen sey baska bir sey; aramaya devam.")
    print(f"  {h}")

    print("\n  ⚠ SINIRLAR: tek yon (SHORT) · tek pencere · tek rejim ·")
    print("    ornekem-ici (sinyaller daha once incelendi, ama BU KARSILASTIRMA")
    print("    hic olculmedi) -> ileri-zamanli dogrulama gerekir.")
    print("  ⚠ Hicbir sonuc 'su girisi kullanalim' DEMEZ: uc kol da negatif")
    print("    olabilir (sinyal zaten ters). Bu olcum SIRALAMA hakkindadir.")
    print("  " + "=" * 72)


if __name__ == "__main__":
    main()
