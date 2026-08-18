"""
onkayit_radar.py — ON-KAYITLI `radar-v2` TESTININ OLCUMU (2026-08-18)
================================================================================
Kural ve kill sartlari `ON-KAYIT-radar-v2.md` dosyasinda DONDURULDU. Bu arac
yalnizca olcer; kural veya esik BURADA tanimlanmaz, orada tanimlidir.

KURAL: kayit anindan SONRA olusturulan radar tahminlerinden
       yon == LONG  VE  makro_kapi == ACIK  olanlar (kanonik evren).

⚠ ERKEN BAKMA KORUMASI: 30 isleme ulasilmadan HUKUM BASILMAZ, yalnizca sayac
gosterilir. Gerekce: ara sonuca bakip karar vermek (veya orneklemi uzatmak)
on-kayitli testin butun degerini yok eder. Bu projede F&G ve kesitsel momentum
tam olarak bu tur esneklikle ayakta kalmisti.

Calistirma: venv\\Scripts\\python.exe onkayit_radar.py
Canliya DOKUNMAZ — sadece okur.
"""
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

KOK = Path(__file__).parent
sys.path.insert(0, str(KOK))
import metrikler as M

# --- ON-KAYITTAN (ON-KAYIT-radar-v2.md) — DEGISTIRILEMEZ ---
KAYIT_ANI = "2026-08-18T20:14:04Z"
HEDEF_N = 30
BASABAS = 32.5          # %
PSR_ESIK = 0.95
YOGUN_CIKAR = 3         # en iyi 3 islem cikarilinca hala pozitif mi


def _ts(s):
    if not s:
        return None
    try:
        d = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def uygun_islemler():
    """Kayit anindan SONRA olusturulmus, kurala uyan, KAPANMIS radar islemleri."""
    t0 = _ts(KAYIT_ANI)
    out = []
    for t in M.kapalilar(M.yukle("radar-defter.json")):
        oluş = _ts(t.get("tarih"))
        if not oluş or oluş < t0:
            continue
        if t.get("yon") != "LONG" or t.get("makro_kapi") != "ACIK":
            continue
        out.append(t)
    out.sort(key=lambda t: t.get("kapanis_tarih") or t.get("tarih") or "")
    return out


def degerlendir(kap):
    r = [M.net_r(t) for t in kap]
    n = len(r)
    ort = statistics.mean(r)
    lo, hi = M.bootstrap_ga(r)
    p = M.psr(r)
    kaz = sum(1 for t in kap if t["durum"] in ("tp1", "tp2")
              or (t["durum"] == "zaman_asimi" and (t.get("sonuc_R") or 0) > 0))
    isabet = kaz / n * 100
    govde = sorted(r)[:-YOGUN_CIKAR]
    govde_ort = statistics.mean(govde) if govde else 0.0
    yari = n // 2
    ilk, son = statistics.mean(r[:yari]), statistics.mean(r[yari:])

    sartlar = [
        ("1. ort>0 VE bootstrap GA sifiri disliyor", (lo is not None and lo > 0),
         f"ort {ort:+.3f} | GA[{lo:+.3f},{hi:+.3f}]" if lo is not None else "GA yok"),
        ("2. isabet basabasi asiyor", isabet > BASABAS,
         f"%{isabet:.1f} vs %{BASABAS}"),
        ("3. PSR >= %95", (p is not None and p >= PSR_ESIK),
         f"%{p*100:.1f}" if p is not None else "hesaplanamadi"),
        (f"4. en iyi {YOGUN_CIKAR} cikinca hala pozitif", govde_ort > 0,
         f"{ort:+.3f} -> {govde_ort:+.3f}"),
        ("5. iki yari da pozitif", (ilk > 0 and son > 0),
         f"ilk {yari} {ilk:+.3f} | son {n-yari} {son:+.3f}"),
    ]
    return sartlar, ort, isabet


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    kap = uygun_islemler()
    n = len(kap)
    gecen = (datetime.now(timezone.utc) - _ts(KAYIT_ANI)).days

    print("=" * 78)
    print("  ON-KAYITLI TEST — radar-v2 (ACIK + LONG)")
    print(f"  kayit ani: {KAYIT_ANI} | {gecen} gun gecti")
    print(f"  kural ve kill sartlari: ON-KAYIT-radar-v2.md (dondurulmus)")
    print("=" * 78)

    if n < HEDEF_N:
        kalan = HEDEF_N - n
        hiz = (n / gecen) if gecen > 0 else 0
        tahmin = f"~{kalan/hiz:.0f} gun" if hiz > 0 else "—"
        print(f"\n  SAYAC: {n}/{HEDEF_N}   ({kalan} islem kaldi, tahmini {tahmin})")
        print(f"\n  ⚠ HUKUM BASILMIYOR. {HEDEF_N} isleme ulasilmadan ara sonuca bakmak")
        print("    on-kayitli testin degerini yok eder (F&G ve kesitsel momentum")
        print("    tam olarak bu esneklikle ayakta kalmisti).")
        if kap:
            print(f"\n  (yalnizca ilerleme: son islem "
                  f"{(kap[-1].get('kapanis_tarih') or '')[:16]}, "
                  f"{kap[-1].get('token')})")
        return

    print(f"\n  ORNEKLEM TAMAM: {n} islem "
          f"({(kap[0].get('kapanis_tarih') or '')[:10]} -> "
          f"{(kap[-1].get('kapanis_tarih') or '')[:10]})")
    if n > HEDEF_N:
        print(f"  NOT: {n} islem birikmis; on-kayit geregi ILK {HEDEF_N} degerlendirilir.")
        kap = kap[:HEDEF_N]

    sartlar, ort, isabet = degerlendir(kap)
    print(f"\n  toplam net {sum(M.net_r(t) for t in kap):+.2f}R | "
          f"islem basina {ort:+.3f}R | isabet %{isabet:.1f}")

    print("\n  KILL SARTLARI (besi de gecmeli)")
    print("  " + "-" * 74)
    for ad, ok, detay in sartlar:
        print(f"  {'GECTI ' if ok else 'KALDI '} {ad:<42} {detay}")

    hepsi = all(ok for _, ok, _ in sartlar)
    print("\n  " + "=" * 74)
    if hepsi:
        print("  HUKUM: 5/5 GECTI — projenin ILK ayakta kalan bulgusu.")
        print("  Sonraki adim: 60+ islem + iki makro rejim ile IKINCI dogrulama turu.")
        print("  ⚠ K3 (gercek para) bu testle ACILMAZ.")
    else:
        kalan = sum(1 for _, ok, _ in sartlar if not ok)
        print(f"  HUKUM: {5-kalan}/5 — KURAL OLDU.")
        print("  Kismi gecis gecis degildir. 'G — KAPALI' listesine yaz, tekrar acma.")
        print("  Tahmin ailesi kesin kapanir.")


if __name__ == "__main__":
    main()
