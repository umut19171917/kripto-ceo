"""
fng_sinavi.py — F&G KAPISININ GUNCEL STANDARTLARLA SINAVI (B1, 2026-08-15)
================================================================================
NEDEN: F&G kapisi (F&G>=75 LONG yok, <=25 SHORT yok) projenin TEK hayatta kalan
tahmin adayi. 2026-07-27 sinavinda birinci cikmisti: +0.037 ortNetR (gurultu
tabani 0.03'un ustunde), pozF 8/12 — cogunlugu tutturan tek aday.

AMA o sinav BUGUNKU standartlarla yapilmadi. Aradan gecen surede iki sey degisti:
  1. YOGUNLASMA SARTI (5. sart) eklendi. `kesitsel_test` 2026-08-11'de bu sart
     olmadigi icin "+%4,5/hafta" gibi bir SAHTE bulguyu ayakta tutmustu; sart
     eklenince cokmustu. Ayni sart F&G'ye HIC uygulanmadi.
  2. REJIM SARTI (2. sart) — F&G'nin iki rejimde de ayni yonde calisip
     calismadigi HIC olculmedi.
Ayrica fold penceresi ~19 gun kaydi -> TAZE fold'larda tekrar (7/27'de "o gun
tekrar edilecek" denmisti).

BES SART (kesitsel_test/sinif_testi ile AYNI; sonuca bakilarak degistirilmez):
  1. Fark GURULTU TABANINI (0.03R) asmali
  2. HER IKI rejimde (BOGA/AYI) ayni yonde olmali
  3. Fold'larin COGUNDA ayni yonde olmali
  4. Kural TEK-TARAFLI degil, iki bacagi da olculebilir olmali
     (⚠ bilinen sinir: LONG bacagi fiilen hic islem kesmiyor)
  5. EN IYI 3 FOLD cikarilinca fark AYAKTA kalmali

Karsilastirma ESLI: ayni fold, ayni coin, ayni config; tek fark kural.
Fark FOLD BASINA ORTALAMA-NET-R uzerinden olculur (toplam netR degil — kural
islem sayisini degistirdigi icin toplamlar kiyaslanamaz).

Calistirma: venv\\Scripts\\python.exe fng_sinavi.py
Canliya DOKUNMAZ.
"""
import bisect
import statistics
import sys
from datetime import datetime, timezone

import aday_testi
import fade_testi

GURULTU = 0.03
BAZ = "baz (filtresiz)"
ADAY = "F&G kapisi (skill kurali)"


def _ort(h):
    n = sum(h[y]["tetik"] for y in ("SHORT", "LONG"))
    return (sum(h[y]["net"] for y in ("SHORT", "LONG")) / n) if n else None, n


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    simdi = int(datetime.now(timezone.utc).timestamp() * 1000)
    t_ilk = simdi - aday_testi.TOPLAM_GUN * aday_testi.GUN_MS + aday_testi.KAL_GUN * aday_testi.GUN_MS
    n_fold = (aday_testi.TOPLAM_GUN - aday_testi.KAL_GUN) // aday_testi.ADIM_GUN
    adim_ms = aday_testi.ADIM_GUN * aday_testi.GUN_MS

    print("=" * 96)
    print("  F&G KAPISI — GUNCEL STANDARTLARLA SINAV (5 sart)")
    print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} | "
          f"{n_fold} fold | esli | gurultu tabani {GURULTU}R")
    print("  ON-KAYITLI KURAL (dis skill'den, verimizden turetilmedi):")
    print("    F&G >= 75 -> LONG acma | F&G <= 25 -> SHORT acma")
    print("=" * 96)

    acc = aday_testi._bos_acc([BAZ, ADAY], n_fold)
    print("\n  esli kosu (baz / F&G) ...", flush=True)
    aday_testi.kosu_filtre(n_fold, t_ilk, acc, "fng")

    # rejim: her fold'un ORTA anindaki BTC trendi (fade_testi ile ayni tanim)
    rmap = fade_testi.trend_rejimi(fade_testi.fiyat_getir("BTCUSDT"))
    rts = sorted(rmap)
    fold_rej = []
    for f in range(n_fold):
        t = t_ilk + f * adim_ms + adim_ms // 2
        i = bisect.bisect_right(rts, t) - 1
        fold_rej.append(rmap[rts[i]] if i >= 0 else "AYI")

    print("\n" + "=" * 96)
    print("  FOLD BAZINDA — ortalama net R (fark = aday - baz)")
    print("=" * 96)
    print(f"  {'dilim basi':<13}{'rejim':<7}{'baz n':>7}{'baz ortR':>10}"
          f"{'aday n':>8}{'aday ortR':>11}{'FARK':>10}")
    farklar, kesilen = [], []
    for f in range(n_fold):
        tar = datetime.fromtimestamp((t_ilk + f * adim_ms) / 1000, timezone.utc).strftime("%Y-%m-%d")
        b, bn = _ort(acc[BAZ][f])
        a, an = _ort(acc[ADAY][f])
        if b is None or a is None:
            print(f"  {tar:<13}{fold_rej[f]:<7}{bn:>7}{'—':>10}{an:>8}{'—':>11}{'—':>10}")
            continue
        d = a - b
        farklar.append((f, d))
        kesilen.append(1 - an / bn if bn else 0)
        print(f"  {tar:<13}{fold_rej[f]:<7}{bn:>7}{b:>+10.3f}{an:>8}{a:>+11.3f}{d:>+10.3f}")

    tf = aday_testi._yeni_hucre()
    ta = aday_testi._yeni_hucre()
    for f in range(n_fold):
        for y in ("SHORT", "LONG"):
            for k in tf:
                tf[k] += acc[BAZ][f][y][k]
                ta[k] += acc[ADAY][f][y][k]
    b_ort = tf["net"] / tf["tetik"] if tf["tetik"] else 0
    a_ort = ta["net"] / ta["tetik"] if ta["tetik"] else 0
    genel = a_ort - b_ort

    print(f"\n  GENEL: baz {b_ort:+.3f} ({tf['tetik']} islem) | "
          f"aday {a_ort:+.3f} ({ta['tetik']} islem) | FARK {genel:+.3f}")
    print(f"  kural islemlerin %{statistics.mean(kesilen)*100:.0f}'ini kesiyor")

    # ---------- 5 SART ----------
    yon = 1 if genel > 0 else -1
    d_list = [d for _, d in farklar]
    ayni = sum(1 for d in d_list if d * yon > 0)
    top = sum(d_list)
    kalan = sum(sorted(d_list)[:-3]) if yon > 0 else sum(sorted(d_list)[3:])

    rej_fark = {}
    for rej in ("BOGA", "AYI"):
        idx = [f for f in range(n_fold) if fold_rej[f] == rej]
        if not idx:
            continue
        hb = aday_testi._yeni_hucre()
        ha = aday_testi._yeni_hucre()
        for f in idx:
            for y in ("SHORT", "LONG"):
                for k in hb:
                    hb[k] += acc[BAZ][f][y][k]
                    ha[k] += acc[ADAY][f][y][k]
        if hb["tetik"] and ha["tetik"]:
            rej_fark[rej] = ha["net"] / ha["tetik"] - hb["net"] / hb["tetik"]

    # LONG bacagi gercekten calisiyor mu?
    lb = sum(acc[BAZ][f]["LONG"]["tetik"] for f in range(n_fold))
    la = sum(acc[ADAY][f]["LONG"]["tetik"] for f in range(n_fold))
    sb = sum(acc[BAZ][f]["SHORT"]["tetik"] for f in range(n_fold))
    sa = sum(acc[ADAY][f]["SHORT"]["tetik"] for f in range(n_fold))

    print("\n" + "=" * 96)
    print("  REJIM AYRIMI (2. sart)")
    print("=" * 96)
    for rej in ("BOGA", "AYI"):
        n_t = sum(1 for x in fold_rej if x == rej)
        v = rej_fark.get(rej)
        print(f"  {rej:<6} {n_t:>2} fold | fark {v:+.3f}" if v is not None
              else f"  {rej:<6} {n_t:>2} fold | veri yok")

    print("\n" + "=" * 96)
    print("  BES SART")
    print("=" * 96)
    k1 = abs(genel) > GURULTU
    k2 = len(rej_fark) == 2 and all(v * yon > 0 for v in rej_fark.values())
    k3 = ayni > len(d_list) / 2
    k4 = (lb - la) > 0.05 * lb and (sb - sa) > 0.05 * sb    # her iki bacak da fiilen kesiyor
    k5 = kalan * yon > 0 and abs(kalan) > GURULTU / 2       # isaret VE anlamli buyukluk
    for ad, ok, det in (
            ("1. gurultu tabanini asiyor", k1, f"{genel:+.3f} vs {GURULTU}R"),
            ("2. iki rejimde ayni yon", k2,
             " / ".join(f"{r} {v:+.3f}" for r, v in rej_fark.items()) or "olculemedi"),
            ("3. fold'larin cogunda", k3, f"{ayni}/{len(d_list)}"),
            ("4. iki bacak da fiilen kesiyor", k4,
             f"LONG {lb}->{la} (%{(1-la/lb)*100:.0f} kesildi) | "
             f"SHORT {sb}->{sa} (%{(1-sa/sb)*100:.0f} kesildi)"),
            ("5. en iyi 3 foldsuz ayakta", k5,
             f"toplam fark {top:+.3f} -> {kalan:+.3f} "
             f"(%{(1-kalan/top)*100:.0f}'i en iyi 3 fold'dan)")):
        print(f"  {'GECTI ' if ok else 'KALDI '} {ad:<32} {det}")

    hepsi = k1 and k2 and k3 and k4 and k5
    print(f"\n  HUKUM: {'AYAKTA — canli sinamayi hak ediyor' if hepsi else 'SINAVI GECEMEDI'}")
    print("\nOKUMA: 2026-07-27'de bu aday +0.037 ile birinci cikmisti, ama o sinavda")
    print("  yogunlasma (5) ve rejim (2) sartlari YOKTU. Ayni eksik olcu aleti")
    print("  kesitsel momentumu da ayakta tutmustu — sart eklenince cokmustu.")


if __name__ == "__main__":
    main()
