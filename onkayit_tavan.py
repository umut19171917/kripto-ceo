"""ON-KAYIT OLCUM ARACI — `radar-tavan` (ON-KAYIT-radar-tavan.md)

Korelasyonlu yigilma freni DUSUSU azaltiyor mu?

BU BETIK SALT OKURDUR. Hicbir sicile, state'e ya da config'e yazmaz.
Radar'in davranisini DEGISTIRMEZ — kapiyi yalnizca SIMULE eder.

72 KABUL'e ulasilmadan hukum BASMAZ, yalniz sayac gosterir. Sebep:
radar-v2'de erken bakis yaniltici olurdu (kural ilk 15 islemde kazaniyordu,
sonunda 1/5 ile dustu). Ayni tuzak burada da kurulmasin.

Kullanim:  venv\\Scripts\\python.exe onkayit_tavan.py
"""
import sys as _sys
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import json
import random
import statistics
from datetime import datetime, timezone, timedelta
from pathlib import Path

import defter
import olcucu
import metrikler as M

KOK = Path(__file__).parent
SICIL = KOK / "radar-defter.json"

# --- DONDURULMUS PARAMETRELER (ON-KAYIT-radar-tavan.md) ---------------------
# Ornekem baslangici = on kaydin KENDI commit'i (b66a046). Bu tarihten
# onceki 459 kayit KULLANILMAZ: uzerlerinde 2026-08-30'da kesifsel geriye
# oynatma yapildi, yani orneklem icidir.
KAYIT_ANI = "2026-08-31T19:33:13+00:00"   # 2. kurulum: 1.si §7 geregi IPTAL (kapi canliya girdi)
ON_KAYIT_COMMIT = "b66a046"
HEDEF_KABUL = 72          # §5 guc hesabi: n=72/196 -> gorulebilen fark 0,531R
AZAMI_GUN = 30            # hangisi once
BLOK = 6                  # P2: 6/6 -> p = 1/64 = 0,016
KAPALI = ("tp1", "tp2", "stop", "zaman_asimi", "gecersiz")


def _dt(s):
    d = datetime.fromisoformat(s)
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def kayitlar():
    """Ornekem: KAYIT_ANI'ndan SONRA olusturulmus radar kayitlari, kronolojik."""
    t0 = _dt(KAYIT_ANI)
    T = json.loads(SICIL.read_text(encoding="utf-8"))["tahminler"]
    return sorted((t for t in T if t.get("tarih") and _dt(t["tarih"]) >= t0),
                  key=lambda t: t["tarih"])


def kapiyi_uygula(T):
    """§2'nin kurali, BIREBIR. Doner: (A=kabul, B=red).

    Kapi kabul edilmis kumenin fonksiyonudur -> tam kayittan simule edilebilir.
    Bu yuzden radar'in davranisini degistirmeye gerek yoktur (§3).
    """
    A, B = [], []
    for t in T:
        simdi = _dt(t["tarih"])
        # (a) cooldown: ayni coine son COOLDOWN_SAAT icinde KABUL var mi
        z = [_dt(x["tarih"]) for x in A if x["token"] == t["token"]]
        if z and (simdi - max(z)).total_seconds() / 3600 < defter.COOLDOWN_SAAT:
            B.append(t)
            continue
        # (b) tavan: o an ACIK olan ayni-yon kabullerin toplam riski
        acik = sum(
            x.get("risk_pct", 1.0) for x in A
            if x["yon"] == t["yon"] and _dt(x["tarih"]) <= simdi
            and (not x.get("kapanis_tarih") or _dt(x["kapanis_tarih"]) > simdi)
        )
        if acik + olcucu.RISK_PCT > defter.RISK_TAVANI_PCT + 1e-9:
            B.append(t)
            continue
        A.append(t)
    return A, B


def _R(kayitlar_):
    """Kapanmis kayitlarin R listesi, kronolojik (yol istatistigi icin sira SART)."""
    k = [t for t in kayitlar_ if t.get("durum") in KAPALI and t.get("sonuc_R") is not None]
    k.sort(key=lambda t: t.get("kapanis_tarih") or t["tarih"])
    return [t["sonuc_R"] for t in k]


def dusus(rler, risk_pct=1.0):
    """En derin bilesik dusus (%). panel._bilesik ile AYNI yontem."""
    b = tepe = 1000.0
    dd = 0.0
    for r in rler:
        b *= (1 + risk_pct / 100.0 * r)
        tepe = max(tepe, b)
        dd = min(dd, b / tepe - 1)
    return dd * 100


def main():
    T = kayitlar()
    A, B = kapiyi_uygula(T)
    gecen = (datetime.now(timezone.utc) - _dt(KAYIT_ANI)).days

    print("=" * 78)
    print("  ON-KAYITLI TEST — radar-tavan (korelasyonlu yigilma freni)")
    print(f"  kayit ani: {KAYIT_ANI}  (commit {ON_KAYIT_COMMIT})")
    print(f"  {gecen} gun gecti | kural ve kill sartlari: ON-KAYIT-radar-tavan.md")
    print("=" * 78)
    print()

    if len(A) < HEDEF_KABUL and gecen < AZAMI_GUN:
        print(f"  SAYAC: {len(A)}/{HEDEF_KABUL} kabul  ·  {len(B)} red  "
              f"·  {gecen}/{AZAMI_GUN} gun")
        print()
        print("  Hukum BASILMADI — ornekem dolmadi (§9).")
        print("  Ara sonuca bakmak radar-v2'de yaniltici olurdu: kural ilk 15")
        print("  islemde kazaniyordu, sonunda 1/5 ile dustu.")
        return

    AR, BR = _R(A), _R(B)
    ABR = _R(A + B)
    print(f"  ORNEKEM TAMAM: {len(A)} kabul / {len(B)} red  ({gecen} gun)")
    print(f"  kapanmis: A={len(AR)}  B={len(BR)}  A∪B={len(ABR)}")
    print()

    if len(AR) < 2 or len(BR) < 2:
        print("  Kapanmis islem yetersiz — hukum yok.")
        return

    # ---- P1: dusus yonu -----------------------------------------------------
    ddA, ddAB = dusus(AR), dusus(ABR)
    p1 = ddA > ddAB          # dusus negatif; "daha az dusus" = daha BUYUK deger
    print("  KILL SARTLARI (P1 ve P2 birden gecmeli, G1 kalmamali)")
    print("  " + "-" * 74)
    print(f"  {'GECTI' if p1 else 'KALDI'}  P1. dd(A) < dd(A∪B)"
          f"{'':>21} A {ddA:6.1f}% | A∪B {ddAB:6.1f}%")

    # ---- P2: 6 blokta isaret testi -----------------------------------------
    t0, t1 = _dt(T[0]["tarih"]), _dt(T[-1]["tarih"])
    adim = (t1 - t0) / BLOK
    tutan = 0
    detay = []
    for i in range(BLOK):
        bas, bit = t0 + adim * i, t0 + adim * (i + 1)
        pencere = lambda g: [x for x in g if bas <= _dt(x["tarih"]) < bit]
        a, ab = _R(pencere(A)), _R(pencere(A + B))
        if len(a) < 2 or len(ab) < 2:
            detay.append("veri-yok")
            continue
        da, dab = dusus(a), dusus(ab)
        ok = da > dab
        tutan += ok
        detay.append(f"{'+' if ok else '-'}")
    p2 = tutan >= BLOK
    print(f"  {'GECTI' if p2 else 'KALDI'}  P2. {BLOK} blokta {BLOK}/{BLOK} ayni yon"
          f"{'':>13} {tutan}/{BLOK}  [{' '.join(detay)}]")

    # ---- G1: getiri felaket freni ------------------------------------------
    random.seed(7)
    farklar = []
    for _ in range(4000):
        a = [random.choice(AR) for _ in AR]
        b = [random.choice(BR) for _ in BR]
        farklar.append(statistics.fmean(a) - statistics.fmean(b))
    farklar.sort()
    lo, hi = farklar[int(0.025 * 4000)], farklar[int(0.975 * 4000)]
    g1 = hi > 0
    print(f"  {'GECTI' if g1 else 'KALDI'}  G1. ort(A)-ort(B) GA95 ust siniri > 0"
          f"{'':>7} {statistics.fmean(AR) - statistics.fmean(BR):+.3f} "
          f"[{lo:+.3f}, {hi:+.3f}]")

    # ---- HUKUM --------------------------------------------------------------
    print()
    print("  " + "=" * 74)
    if p1 and p2 and g1:
        print("  HUKUM: GECTI — kapi radar.py'de ACILABILIR.")
        print("  ⚠ Hukum yazilirken §5 guc serhi AYRILAMAZ: bu test 0,531R'den")
        print("    kucuk bir getiri farkini goremez; G1'in gecmesi 'getiri")
        print("    bozulmadi' DEMEK DEGILDIR, 'bozuldugunu gosteremedik' demektir.")
        print("  ⚠ P1/P2 ISARET testidir — 'dusus %X azaldi' cumlesi bu testten CIKMAZ.")
    else:
        print("  HUKUM: KALDI — kapi ACILMAZ, 'G — KAPALI' listesine yazilir.")
        print("  'Olcum zayifti, yine de acalim' YASAK (§8).")
        print("  'Tavani gevsetip yeniden deneyelim' YASAK — esik taramasi olur")
        print("  ve §2'nin sifir-serbestlik-derecesi gerekcesini yok eder.")
    print("  " + "=" * 74)


if __name__ == "__main__":
    main()
