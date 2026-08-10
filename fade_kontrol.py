"""
fade_kontrol.py — LIKIDASYON SINYALI "BUYUK HAREKET"TEN FAZLASI MI? (2026-08-10)
================================================================================
NEDEN: `fade_testi.py` (540g, 10 sembol, 12 fold) FIYAT SOKU uzerinde fade
BULAMADI — on-kayitli hucrede DEVAM cikti, 1/10 sembolde, 2/12 fold'da tuttu,
ve buyukluk maliyet cizgisinin altinda kaldi. Ama `sinyal_tarama.py` 35 gunluk
LIKIDASYON verisinde FADE bulmustu.

Iki acikma var, ayirt etmek sart:
  (A) Likidasyon olayi "buyuk fiyat hareketi"nin baska adi -> 35 gunluk fade
      bulgusu tek-donem dalgalanmasi; 540g testi onu zaten curutuyor.
  (B) Likidasyon olayi fiyat hareketinden AYRI bilgi tasiyor (zorunlu satis,
      istekli satistan farklidir) -> bulgu ayakta kalir, sadece dogrulanamaz.

TEST: AYNI 35 gunde, AYNI sembollerde, AYNI ileri-getiri yontemiyle:
  likidasyon olaylari  vs  ESIT SAYIDA en-sert 5dk FIYAT hareketi (esli kontrol).
Frekans esitlenir ki karsilastirma adil olsun. Ayrica ORTUSME olculur: iki kume
buyuk oranda ayni anlarsa sinyal zaten fiyatin kendisidir.

Calistirma: venv\\Scripts\\python.exe fade_kontrol.py
Canliya DOKUNMAZ.
"""
import sys
from datetime import datetime, timezone

import olcucu
import backtest
import sinyal_tarama as st

UFUKLAR = st.UFUKLAR          # [1, 4, 24] — onceki testle AYNI
GUN = st.GUN                  # 40
TF = st.TF                    # 5m
GERI_BAR = 1                  # sok penceresi = 1 bar (5dk) — likidasyon kovasiyla AYNI ritim


def _ort(x):
    return sum(x) / len(x) if x else None


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    haric = set(getattr(olcucu, "DENEYSEL", set()))
    g = [x for x in st.gozlemler() if x[1] not in haric]
    if not g:
        print("  gozlem yok")
        return

    print("=" * 96)
    print("  ESLI KONTROL — likidasyon olayi mi, yoksa sadece 'buyuk hareket' mi?")
    print(f"  {len(g):,} teklestirilmis gozlem | fiyat {TF} | ufuklar {UFUKLAR}s | "
          + datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))
    print("  kontrol grubu: AYNI sayida en-sert 5dk fiyat hareketi (frekans eslenmis)")
    print("=" * 96)

    semboller = sorted({x[1] for x in g})
    top = {h: {k: [] for k in ("liq_dus", "liq_yuk", "fiy_dus", "fiy_yuk", "taban")}
           for h in UFUKLAR}
    ort_say = [0, 0, 0]        # [liq olay, fiyat olay, ortusen]
    isaret = {"liq": [0, 0], "fiy": [0, 0]}    # [FADE sembol, digerleri]

    print(f"\n  {'sembol':<11}{'liq n':>7}{'fiyat n':>9}{'ortusme':>9}   sembol yorumu (+4s)")
    for sym in semboller:
        try:
            K = backtest.klines_history(sym, TF, GUN)
        except Exception as e:
            print(f"  {sym:<11}fiyat cekilemedi ({type(e).__name__}) - atlandi", flush=True)
            continue
        ts_list, cl = [k["t"] for k in K], [k["c"] for k in K]
        esik = st.esik_kademeleri(g, sym).get("P95")
        if not esik:
            continue

        # --- gozlemleri fiyatla eslestir; likidasyon ve 5dk getiri birlikte ---
        kayit = []      # (ts, L, S, getiri_5dk, p0)
        for ts, s, L, S in g:
            if s != sym:
                continue
            p0 = st._fiyat(ts_list, cl, ts)
            pm = st._fiyat(ts_list, cl, ts - GERI_BAR * 300_000)
            if not p0 or not pm:
                continue
            kayit.append((ts, L, S, (p0 - pm) / pm * 100, p0))
        if not kayit:
            continue

        liq_dus = {k[0] for k in kayit if k[1] >= esik and k[1] > k[2]}   # LONG-liq = zorunlu SATIS
        liq_yuk = {k[0] for k in kayit if k[2] >= esik and k[2] > k[1]}   # SHORT-liq = zorunlu ALIM

        # --- frekans eslenmis fiyat kontrolu: ayni sayida en sert dusus/yukselis ---
        sirali_dus = sorted(kayit, key=lambda k: k[3])
        sirali_yuk = sorted(kayit, key=lambda k: -k[3])
        fiy_dus = {k[0] for k in sirali_dus[:len(liq_dus)]}
        fiy_yuk = {k[0] for k in sirali_yuk[:len(liq_yuk)]}

        ort = len((liq_dus & fiy_dus) | (liq_yuk & fiy_yuk))
        ort_say[0] += len(liq_dus) + len(liq_yuk)
        ort_say[1] += len(fiy_dus) + len(fiy_yuk)
        ort_say[2] += ort

        yerel = {h: {k: [] for k in ("liq_dus", "liq_yuk", "fiy_dus", "fiy_yuk", "taban")}
                 for h in UFUKLAR}
        for ts, L, S, r5, p0 in kayit:
            for h in UFUKLAR:
                p1 = st._fiyat(ts_list, cl, ts + h * 3_600_000)
                if not p1 or p1 == p0:
                    continue
                chg = (p1 - p0) / p0 * 100
                yerel[h]["taban"].append(chg)
                if ts in liq_dus:
                    yerel[h]["liq_dus"].append(chg)
                if ts in liq_yuk:
                    yerel[h]["liq_yuk"].append(chg)
                if ts in fiy_dus:
                    yerel[h]["fiy_dus"].append(chg)
                if ts in fiy_yuk:
                    yerel[h]["fiy_yuk"].append(chg)
        for h in UFUKLAR:
            for k in yerel[h]:
                top[h][k].extend(yerel[h][k])

        # sembol yorumu (+4s)
        h4 = UFUKLAR[1]
        tb = _ort(yerel[h4]["taban"])
        notlar = []
        for on, ad in (("liq", "likid"), ("fiy", "fiyat")):
            d, y = _ort(yerel[h4][f"{on}_dus"]), _ort(yerel[h4][f"{on}_yuk"])
            if tb is None or d is None or y is None:
                notlar.append(f"{ad}: —")
                continue
            yr = "FADE" if (d - tb > 0 and y - tb < 0) else \
                 ("DEVAM" if (d - tb < 0 and y - tb > 0) else "karisik")
            isaret[on][0 if yr == "FADE" else 1] += 1
            notlar.append(f"{ad}: {yr}")
        pay = f"%{ort / max(1, len(liq_dus) + len(liq_yuk)) * 100:.0f}"
        print(f"  {sym:<11}{len(liq_dus)+len(liq_yuk):>7}{len(fiy_dus)+len(fiy_yuk):>9}"
              f"{pay:>9}   " + " | ".join(notlar), flush=True)

    print(f"\n  TOPLAM ortusme: {ort_say[2]:,}/{ort_say[0]:,} likidasyon olayi ayni anda"
          f" en-sert fiyat hareketi (%{ort_say[2]/max(1,ort_say[0])*100:.0f})")

    print("\n" + "=" * 96)
    print("  ESLI KARSILASTIRMA — ayni pencere, ayni taban, ayni olay sayisi")
    print("=" * 96)
    for h in UFUKLAR:
        tb = _ort(top[h]["taban"])
        if tb is None:
            continue
        print(f"\n  --- ufuk +{h} saat (taban {tb:+.3f}%) ---")
        print(f"  {'grup':<22}{'dus n':>8}{'dus EDGE':>11}{'yuk n':>8}{'yuk EDGE':>11}{'yorum':>10}")
        for on, ad in (("liq", "LIKIDASYON olayi"), ("fiy", "FIYAT soku (kontrol)")):
            d, y = _ort(top[h][f"{on}_dus"]), _ort(top[h][f"{on}_yuk"])
            nd, ny = len(top[h][f"{on}_dus"]), len(top[h][f"{on}_yuk"])
            if d is None or y is None:
                print(f"  {ad:<22}{nd:>8,}{'—':>11}{ny:>8,}{'—':>11}{'—':>10}")
                continue
            ed, ey = d - tb, y - tb
            yr = "FADE" if (ed > 0 and ey < 0) else ("DEVAM" if (ed < 0 and ey > 0) else "karisik")
            print(f"  {ad:<22}{nd:>8,}{ed:>+11.3f}{ny:>8,}{ey:>+11.3f}{yr:>10}")

    print(f"\n  sembol bazinda FADE sayisi (+{UFUKLAR[1]}s): "
          f"likidasyon {isaret['liq'][0]}/{sum(isaret['liq'])} | "
          f"fiyat soku {isaret['fiy'][0]}/{sum(isaret['fiy'])}")

    print("\n" + "=" * 96)
    print("OKUMA:")
    print("  - Iki grup AYNI davraniyorsa: likidasyon 'buyuk hareket'in baska adidir.")
    print("    O zaman 540g fiyat testi (fade YOK) likidasyon bulgusunu da curutur.")
    print("  - Likidasyon FADE verip fiyat soku vermiyorsa: zorunlu satis AYRI bilgi")
    print("    tasiyor demektir; bulgu ayakta kalir ama 60g veri sinirindan oturu")
    print("    farkli rejimde DOGRULANAMAZ.")
    print("  - ORTUSME yuksekse (>%60) zaten ayni olaylardan bahsediyoruz.")


if __name__ == "__main__":
    main()
