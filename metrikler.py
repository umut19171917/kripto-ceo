"""
metrikler.py — RISK-DUZELTILMIS OLCUM + ISTATISTIKSEL SINAV (2026-08-18)
================================================================================
NEDEN: Iki dis denetim belgesi de ayni bosluga isaret etti ve HAKLILAR: sicilde
yalniz TOPLAM R var. Toplam R, "iyi strateji" ile "sansli strateji"yi ayirt
edemez. Eksikler: equity egrisi, Sharpe/Sortino/Calmar, maks cekilme, aykiri
deger analizi, ve en onemlisi ISTATISTIKSEL SINAV.

⚠ BELGENIN ONERDIGI TEST YANLIS KURULMUSTU:
  "Canli sicildeki islemlerin SIRASINI karistir; p<0.05 ise gercek edge."
Sirayi karistirmak TOPLAMI DEGISTIRMEZ — yalnizca yolu (cekilme, seri) degistirir.
Ortalama R sira permutasyonuna karsi degismezdir; o test "edge var mi" sorusunu
OLCEMEZ. Dogru araclar:
  - "ortalama R sifirdan farkli mi?"     -> BOOTSTRAP guven araligi
  - "Sharpe gercekten pozitif mi?"       -> PSR (Bailey & Lopez de Prado 2012)
  - "iki grup arasindaki fark sans mi?"  -> ETIKET PERMUTASYONU (dogru kullanim)

Bu modul ucunu de dogru kurar. Ozellikle SONUNCUSU kritik: projenin TEK pozitif
bulgusu (makro kapisi ACIK vs DIKKAT farki) VERIDEN TURETILDI ve sans olasiligi
simdiye kadar hic olculmedi. Etiket permutasyonu tam bu is icindir.

EVREN: defter.ozet() ile AYNI kanonik suzgec (geri-doldurma + deneysel HARIC).
Bagimlilik yok (numpy/matplotlib gerekmez) — saf Python + ASCII egri.

Calistirma: venv\\Scripts\\python.exe metrikler.py
Canliya DOKUNMAZ — sadece okur.
"""
import json
import math
import random
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

KOK = Path(__file__).parent
KAPALI = ("tp1", "tp2", "stop", "zaman_asimi")
KAZANC = ("tp1", "tp2")
TEKRAR = 20000            # bootstrap / permutasyon tekrari
BASABAS_ISABET = 32.5     # R/R 2,08 icin gereken isabet %
random.seed(20260818)     # tekrarlanabilir


# ============================== veri ==============================
def yukle(dosya):
    """defter.ozet() ile AYNI evren."""
    d = json.loads((KOK / dosya).read_text(encoding="utf-8"))
    return [t for t in d.get("tahminler", [])
            if t.get("kaynak", "canli") != "geri-doldurma" and t.get("sicil") != "deneysel"]


try:
    sys.path.insert(0, str(KOK))
    import defter as _defter
except Exception:
    _defter = None


def net_r(t):
    if _defter is not None:
        try:
            return _defter.net_R(t) or 0.0
        except Exception:
            pass
    return t.get("sonuc_R") or 0.0


def kapalilar(kay):
    v = [t for t in kay if t.get("durum") in KAPALI]
    v.sort(key=lambda t: t.get("kapanis_tarih") or t.get("tarih") or "")
    return v


# ============================== istatistik ==============================
def _norm_cdf(z):
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2)))


def sharpe(r):
    if len(r) < 2:
        return None
    sd = statistics.stdev(r)
    return (statistics.mean(r) / sd) if sd else None


def sortino(r):
    if len(r) < 2:
        return None
    asagi = [x for x in r if x < 0]
    if not asagi:
        return None
    dd = math.sqrt(sum(x * x for x in asagi) / len(r))
    return (statistics.mean(r) / dd) if dd else None


def cekilme(r):
    """(maks cekilme R, en dip islem indeksi) — kumulatif egriden."""
    tepe, en, kum, idx = 0.0, 0.0, 0.0, 0
    for i, x in enumerate(r):
        kum += x
        tepe = max(tepe, kum)
        if kum - tepe < en:
            en, idx = kum - tepe, i
    return en, idx


def psr(r, hedef_sr=0.0):
    """Probabilistic Sharpe Ratio: gercek Sharpe'in hedefi asma olasiligi.
    Carpiklik (g3) ve basikligi (g4) hesaba katar — kucuk ornekte sart."""
    n = len(r)
    sr = sharpe(r)
    if not sr or n < 4:
        return None
    m, sd = statistics.mean(r), statistics.stdev(r)
    g3 = sum(((x - m) / sd) ** 3 for x in r) / n
    g4 = sum(((x - m) / sd) ** 4 for x in r) / n
    payda = 1 - g3 * sr + (g4 - 1) / 4 * sr * sr
    if payda <= 0:
        return None
    return _norm_cdf((sr - hedef_sr) * math.sqrt(n - 1) / math.sqrt(payda))


def bootstrap_ga(r, pct=95):
    """Ortalamanin guven araligi — yerine koyarak yeniden orneklem."""
    n = len(r)
    if n < 5:
        return None, None
    ort = sorted(sum(random.choice(r) for _ in range(n)) / n for _ in range(TEKRAR))
    a = (100 - pct) / 2 / 100
    return ort[int(a * TEKRAR)], ort[int((1 - a) * TEKRAR) - 1]


def etiket_permutasyon(A, B):
    """DOGRU permutasyon testi: grup etiketlerini karistir, farkin sans olma
    olasiligini olc. Sira permutasyonundan farki: bu, ortalamayi DEGISTIRIR."""
    if len(A) < 3 or len(B) < 3:
        return None, None
    gozlenen = statistics.mean(A) - statistics.mean(B)
    havuz = list(A) + list(B)
    na, nb = len(A), len(B)
    ust = 0
    for _ in range(TEKRAR):
        random.shuffle(havuz)
        f = sum(havuz[:na]) / na - sum(havuz[na:]) / nb
        if abs(f) >= abs(gozlenen):
            ust += 1
    return gozlenen, ust / TEKRAR


# ============================== gosterim ==============================
def ascii_egri(r, en=64, yuk=10):
    """Kumulatif net-R egrisi — bagimliliksiz."""
    kum, s = [], 0.0
    for x in r:
        s += x
        kum.append(s)
    if not kum:
        return []
    adim = max(1.0, len(kum) / en)
    ornek = [kum[min(len(kum) - 1, int(i * adim))] for i in range(min(en, len(kum)))]
    lo, hi = min(min(ornek), 0.0), max(max(ornek), 0.0)
    if hi - lo < 1e-9:
        hi = lo + 1.0
    birim = (hi - lo) / yuk
    out = []
    for sr in range(yuk, -1, -1):
        seviye = lo + birim * sr
        cizgi = "".join("#" if v >= seviye - birim / 2 else " " for v in ornek)
        isaret = "0>" if abs(seviye) <= birim / 2 else "  "
        out.append(f"  {seviye:>+7.1f}R {isaret}|{cizgi}")
    return out


def rapor(ad, kay):
    kap = kapalilar(kay)
    if len(kap) < 5:
        print(f"\n{ad}: yetersiz kapanmis islem ({len(kap)})")
        return None
    r = [net_r(t) for t in kap]
    n, top, ort = len(r), sum(r), statistics.mean(r)

    t0 = (kap[0].get("kapanis_tarih") or kap[0].get("tarih") or "")[:10]
    t1 = (kap[-1].get("kapanis_tarih") or kap[-1].get("tarih") or "")[:10]
    try:
        gun = max(1, (datetime.fromisoformat(t1) - datetime.fromisoformat(t0)).days)
    except Exception:
        gun = 1
    yillik_islem = n / gun * 365

    print("\n" + "=" * 78)
    print(f"  {ad} — {n} kapanmis islem | {t0} -> {t1} ({gun} gun)")
    print("=" * 78)

    print("\n  EQUITY EGRISI (kumulatif net R)")
    for s in ascii_egri(r):
        print(s)

    sr, so = sharpe(r), sortino(r)
    md, mi = cekilme(r)
    print("\n  RISK-DUZELTILMIS")
    print(f"    toplam net        {top:>+8.2f}R     islem basina   {ort:>+7.3f}R")
    if sr:
        print(f"    Sharpe (islem)    {sr:>+8.3f}      yillik~ "
              f"{sr * math.sqrt(yillik_islem):>+7.2f}  (~{yillik_islem:.0f} islem/yil)")
    if so:
        print(f"    Sortino (islem)   {so:>+8.3f}")
    print(f"    maks cekilme      {md:>+8.2f}R     (islem #{mi + 1} dibinde)")
    if md:
        print(f"    Calmar~           {(ort * yillik_islem / abs(md)):>+8.2f}")
    p = psr(r)
    if p is not None:
        yorum = ("gercek Sharpe muhtemelen POZITIF" if p > 0.95
                 else ("gercek Sharpe muhtemelen NEGATIF" if p < 0.05 else "KARARSIZ"))
        print(f"    PSR (Sharpe>0)    {p * 100:>7.1f}%      -> {yorum}")

    lo, hi = bootstrap_ga(r)
    if lo is not None:
        icinde = lo <= 0 <= hi
        print("\n  BOOTSTRAP — islem basina net R %95 guven araligi")
        print(f"    [{lo:+.3f} , {hi:+.3f}]    gozlenen {ort:+.3f}")
        print("    -> sifir " + ("ICINDE: kayip SANSLA aciklanabilir (edge de yok)"
                                 if icinde else "DISINDA: sistematik"))

    sirali = sorted(r)
    en_iyi, en_kotu = sum(sirali[-5:]), sum(sirali[:5])
    govde = top - en_iyi - en_kotu
    print("\n  AYKIRI DEGER — en iyi/kotu 5 islemin katkisi")
    print(f"    en iyi 5 {en_iyi:>+8.2f}R  |  en kotu 5 {en_kotu:>+8.2f}R")
    print(f"    ikisi de cikinca GOVDE: {govde:>+7.2f}R  ({n - 10} islem, "
          f"islem basina {govde / max(1, n - 10):+.3f}R)")

    kz = sum(1 for t in kap if t["durum"] in KAZANC
             or (t["durum"] == "zaman_asimi" and (t.get("sonuc_R") or 0) > 0))
    print(f"\n  isabet %{kz / n * 100:.1f}   (basabas ~%{BASABAS_ISABET} @ R/R 2,08)")
    return kap


def makro_permutasyon(siciller):
    """PROJENIN TEK POZITIF BULGUSUNUN SINAVI.
    Makro kapisi ACIK vs DIKKAT farki VERIDEN turetildi; sans olasiligi hic
    olculmedi. Etiket permutasyonu tam bu is icin dogru aractir."""
    print("\n" + "=" * 78)
    print("  MAKRO KAPISI — ETIKET PERMUTASYON SINAVI")
    print("  Soru: ACIK/DIKKAT farki, etiketler RASTGELE dagitilsa da cikar miydi?")
    print("=" * 78)
    p_ler = []
    for ad, kay in siciller:
        g = {"ACIK": [], "DIKKAT": []}
        for t in kapalilar(kay):
            k = t.get("makro_kapi")
            if k in g:
                g[k].append(net_r(t))
        if len(g["ACIK"]) < 3 or len(g["DIKKAT"]) < 3:
            print(f"\n  {ad}: yetersiz ornek "
                  f"(ACIK {len(g['ACIK'])}, DIKKAT {len(g['DIKKAT'])})")
            continue
        fark, p = etiket_permutasyon(g["ACIK"], g["DIKKAT"])
        p_ler.append(p)
        print(f"\n  {ad}")
        print(f"    ACIK    n={len(g['ACIK']):<4} ort {statistics.mean(g['ACIK']):+.3f}R")
        print(f"    DIKKAT  n={len(g['DIKKAT']):<4} ort {statistics.mean(g['DIKKAT']):+.3f}R")
        print(f"    fark {fark:+.3f}R  ->  p = {p:.4f}  "
              + ("(ANLAMLI)" if p < 0.05 else "(anlamli DEGIL)"))

    if len(p_ler) == 2:
        khi = -2 * sum(math.log(max(x, 1e-12)) for x in p_ler)
        p_bir = math.exp(-khi / 2) * (1 + khi / 2)      # df=4 ust kuyruk
        print(f"\n  FISHER BIRLESIK: p = {p_bir:.4f}  "
              + ("-> ANLAMLI" if p_bir < 0.05 else "-> anlamli degil"))
        print("  (iki sicil FARKLI sinyal kullanir -> bagimsiz kanit sayilabilir)")


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print("=" * 78)
    print("  RISK-DUZELTILMIS OLCUM + ISTATISTIKSEL SINAV")
    print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} | "
          f"{TEKRAR:,} tekrar | evren: kanonik")
    print("=" * 78)

    siciller = []
    for dosya, ad in (("kripto-defter.json", "ANA SICIL"), ("radar-defter.json", "RADAR")):
        try:
            kay = yukle(dosya)
        except Exception as e:
            print(f"{ad}: okunamadi ({type(e).__name__})")
            continue
        rapor(ad, kay)
        siciller.append((ad, kay))

    try:
        k2 = [t for t in yukle("kripto-defter.json") if t.get("konfig") == "swing-1h"]
        rapor("K2 KUMESI (swing-1h)", k2)
    except Exception:
        pass

    makro_permutasyon(siciller)

    print("\n" + "=" * 78)
    print("OKUMA:")
    print("  - Bootstrap sifiri ICERIYORSA: kayip sansla aciklanabilir; sistemin")
    print("    kaybettirdigi iddiasi bu veriyle KANITLANAMAZ (edge de yok).")
    print("  - PSR: gercek Sharpe'in pozitif olma olasiligi. <%5 muhtemelen negatif,")
    print("    >%95 muhtemelen pozitif, arasi KARARSIZ.")
    print("  - GOVDE: en iyi/kotu 5 cikinca kalan; stratejinin asil karakteri.")
    print("  - Makro permutasyonu p<0.05 ise fark sansla aciklanamaz -> bulgu")
    print("    on-kayitli canli sinavi HAK EDER. p>0.05 ise bulgu ZAYIFTIR.")


if __name__ == "__main__":
    main()
