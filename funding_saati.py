"""
funding_saati.py — FUNDING ODEME SAATI ETKISI (B5, 2026-08-15)
================================================================================
NEDEN: Takvim/zorunlu-akis ailesinin en UCUZ uyesi — veri zaten elimizde.
Funding 8 saatte bir (00/08/16 UTC) odenir. Odeme ani ONCEDEN BILINIR ve
odemeyi vermek istemeyen taraf pozisyonunu kapatmak zorunda kalabilir. Yani
ZORUNLU AKIS adayi: tahmin degil, takvim.

HIPOTEZ (on-kayitli): funding yuksek pozitifken, odeme saatinden HEMEN ONCE
long'lar odemekten kacinmak icin cikar -> fiyat baskilanir; odeme gecince geri
alinir. Beklenen iz: settlement-1 saatinde NEGATIF, settlement+1'de POZITIF
sapma (yuksek-funding kosulunda), ve dusuk-funding kosulunda ETKI YOK.

OLCU: her saatlik barin getirisi, funding dongusundeki konumuna gore kovalanir
  konum = (UTC saat) % 8   ->  0 = odeme saati, 7 = odemeden hemen once
Taban COIN+FOLD bazinda cikarilir (piyasa suruklenmesi edge sanilmasin).

BES SART (digerleriyle AYNI): gurultu/maliyet · iki rejim · fold cogunlugu ·
doz-tepki (yuksek funding'de guclu, dusukte zayif) · en iyi 3 fold cikinca ayakta.

⚠ MALIYET: 1 saatlik islem gidis-donus %0.13 oder. Etki bunun altindaysa bilgi
olsa bile islenemez — tabloda cizgi olarak basilir.

Calistirma: venv\\Scripts\\python.exe funding_saati.py
Canliya DOKUNMAZ.
"""
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timezone

import olcucu
import backtest
import ileritest
import fade_testi

GUN = 540
ADIM_GUN = 30
KAL_GUN = 166
GUN_MS = 86_400_000
MALIYET = backtest._bacak(True) * 2 * 100      # % gidis-donus


def _ort(x):
    return sum(x) / len(x) if x else None


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    haric = set(getattr(olcucu, "DENEYSEL", set()))
    syms = [s for s in olcucu.SYMBOLS if s not in haric]
    simdi = int(datetime.now(timezone.utc).timestamp() * 1000)
    t_ilk = simdi - GUN * GUN_MS + KAL_GUN * GUN_MS
    n_fold = (GUN - KAL_GUN) // ADIM_GUN

    print("=" * 96)
    print("  FUNDING ODEME SAATI — zorunlu akis var mi?")
    print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} | "
          f"{GUN}g | {len(syms)} coin | {n_fold} fold")
    print("  konum = UTC saat %% 8   (0 = odeme ani, 7 = odemeden hemen once)")
    print(f"  MALIYET CIZGISI: %{MALIYET:.3f} gidis-donus")
    print("  ON-KAYITLI HIPOTEZ: yuksek funding'de konum 7 NEGATIF, konum 1 POZITIF")
    print("=" * 96)

    rmap = fade_testi.trend_rejimi(fade_testi.fiyat_getir("BTCUSDT"))
    # kova: (kademe, konum) -> demeanlenmis getiriler ; ayrica fold ve rejim kirilimi
    kova = defaultdict(list)
    fold_kova = defaultdict(lambda: defaultdict(list))
    rej_kova = defaultdict(lambda: defaultdict(list))

    print(f"\n  {'coin':<11}{'bar':>7}{'funding kaydi':>15}")
    for sym in syms:
        try:
            K = fade_testi.fiyat_getir(sym)
            fts, ffr = ileritest.funding_serisi_gun(sym, GUN)
        except Exception as e:
            print(f"  {sym:<11}HATA {type(e).__name__}", flush=True)
            continue
        if len(K) < (KAL_GUN + ADIM_GUN) * 24 or not fts:
            print(f"  {sym:<11}yetersiz veri", flush=True)
            continue
        print(f"  {sym:<11}{len(K):>7}{len(fts):>15}", flush=True)

        # her fold+coin icin taban (kosulsuz ortalama saatlik getiri)
        getiri, meta = [], []
        for i in range(len(K) - 1):
            c0, c1 = K[i]["c"], K[i + 1]["c"]
            if c0 <= 0:
                continue
            f = int((K[i]["t"] - t_ilk) // (ADIM_GUN * GUN_MS))
            if f < 0 or f >= n_fold:
                continue
            getiri.append((c1 - c0) / c0 * 100)
            meta.append((f, K[i]["t"]))
        if not getiri:
            continue
        taban = defaultdict(list)
        for r, (f, _) in zip(getiri, meta):
            taban[f].append(r)
        tb = {f: sum(v) / len(v) for f, v in taban.items() if v}

        # funding kademesi: sembolun KENDI dagiliminda ust/alt ucte bir
        sirali = sorted(ffr)
        ust = sirali[int(len(sirali) * 2 / 3)] if sirali else 0
        alt = sirali[int(len(sirali) / 3)] if sirali else 0

        for r, (f, t) in zip(getiri, meta):
            saat = datetime.fromtimestamp(t / 1000, timezone.utc).hour
            konum = saat % 8
            fv = backtest.funding_at(fts, ffr, t)
            kademe = ("YUKSEK" if fv >= ust else ("DUSUK" if fv <= alt else "ORTA"))
            d = r - tb.get(f, 0)
            for kd in (kademe, "TUMU"):
                kova[(kd, konum)].append(d)
                if kd == "YUKSEK":
                    fold_kova[konum][f].append(d)
                    rej_kova[konum][rmap.get(t, "AYI")].append(d)

    print("\n" + "=" * 96)
    print("  KONUMA GORE SAPMA (%) — taban coin+fold bazinda cikarildi")
    print("=" * 96)
    print(f"  {'konum':<24}" + "".join(f"{k:>12}" for k in ("TUMU", "YUKSEK f.", "ORTA", "DUSUK f.")))
    for konum in range(8):
        ad = {0: "0  = ODEME ANI", 1: "1  (odemeden sonra)", 7: "7  (odemeden ONCE)"}.get(
            konum, f"{konum}")
        satir = f"  {ad:<24}"
        for kd in ("TUMU", "YUKSEK", "ORTA", "DUSUK"):
            v = kova.get((kd, konum))
            # DIKKAT: getiriler ZATEN yuzde; bir kez daha 100'le carpma (2026-08-15
            # birim hatasi: etki 100 kat buyuk gorunup maliyet cizgisini "asiyor"du).
            satir += f"{_ort(v):>12.4f}" if v else f"{'—':>12}"
        print(satir)

    print(f"\n  (deger = o konumdaki ortalama saatlik getiri EKSI kosulsuz taban, YUZDE)")

    # ---- on-kayitli hucreler ----
    print("\n" + "=" * 96)
    print("  ON-KAYITLI HUCRELER — hipotez tuttu mu?")
    print("=" * 96)
    h7 = _ort(kova.get(("YUKSEK", 7)))
    h1 = _ort(kova.get(("YUKSEK", 1)))
    d7 = _ort(kova.get(("DUSUK", 7)))
    print(f"  yuksek funding, konum 7 (odeme oncesi): {h7:+.4f}%  "
          f"(beklenen: NEGATIF) -> {'TUTTU' if h7 and h7 < 0 else 'TUTMADI'}")
    print(f"  yuksek funding, konum 1 (odeme sonrasi): {h1:+.4f}%  "
          f"(beklenen: POZITIF) -> {'TUTTU' if h1 and h1 > 0 else 'TUTMADI'}")
    print(f"  DUSUK funding, konum 7 (kontrol):        {d7:+.4f}%  "
          f"(beklenen: ~0, etki funding'e bagli olmali)")

    buyukluk = max(abs(h7 or 0), abs(h1 or 0))
    print(f"\n  en buyuk etki %{buyukluk:.4f} vs maliyet cizgisi %{MALIYET:.3f}"
          f"  -> {'ASIYOR' if buyukluk > MALIYET else 'ALTINDA (islenemez)'}")

    # ---- fold / rejim tutarliligi (konum 7, yuksek funding) ----
    fv = [(_ort(v) or 0) for f, v in sorted(fold_kova[7].items())]
    if fv:
        yon = 1 if (h7 or 0) < 0 else -1          # hipotez yonu: negatif
        ayni = sum(1 for x in fv if x * (-1 if yon > 0 else 1) > 0)
        top = sum(fv)
        kalan = sum(sorted(fv)[3:]) if yon > 0 else sum(sorted(fv)[:-3])
        print(f"\n  konum 7 / yuksek funding — fold tutarliligi: {ayni}/{len(fv)} fold ayni yonde")
        print(f"  yogunlasma: fold ort. toplami {top:+.4f} -> en iyi 3 foldsuz {kalan:+.4f}")
    for rej in ("BOGA", "AYI"):
        v = rej_kova[7].get(rej)
        if v:
            print(f"  konum 7 / {rej}: {_ort(v):+.4f}% (n={len(v):,})")

    print("\n" + "=" * 96)
    print("OKUMA:")
    print("  - Etki maliyet cizgisinin ALTINDAYSA, gercek olsa bile islenemez.")
    print("  - DUSUK funding kontrolu sart: etki orada da varsa mekanizma funding")
    print("    degil, gunun saati (seans etkisi) demektir — baska bir sey olculmus olur.")
    print("  - Saatlik ritim -> yuzlerce islem/yil -> maliyet en cok burada isirir.")


if __name__ == "__main__":
    main()
