"""
sinyal_tarama.py — EDGE ARAMA: aday sinyallerin ileri-tahmin gucu var mi? (2026-08-09)
================================================================================
NEDEN: 2026-08-09'da `skor_gucu.py` sikisma skorunun kullanilabilir yon bilgisi
TASIMADIGINI gosterdi (964k canli gozlem). Karar: strateji kurmayi birak, once
EDGE ARA. Bu arac aday sinyalleri AYNI yontemle, AYNI tabana karsi, ucuza eler.

YONTEM (skor_gucu.py ile ayni, tek fark: sinyal takilabilir):
  her (zaman, sembol, sinyal-atesledi-mi) gozlemi icin ileri-getiri olculur;
  kosullu getiri - kosulsuz taban = EDGE. Sembol bazinda ISARET TUTARLILIGI esas.

DURUSTLUK:
  - Islem simulasyonu DEGIL (giris/stop/TP/komisyon yok). "Sinyalde bilgi var mi"
    sorusu. Maliyet eklemek sonucu KOTULESTIRIR, iyilestirmez.
  - Log gozlemleri 30sn ritimle ustuste biniyor -> KOVA TEKLESTIRME yapilir
    (sembol basina her 5dk'da tek gozlem) ve p-degeri hesaplanmaz.
  - Tek rejim (2026 dusen/testere). Boga rejimi hic gorulmedi.
  - Bir sinyal "gecti" demek EDGE'i kanitlandi demek DEGIL; sadece "elenmedi,
    daha pahali testi hak ediyor" demek.

ADAY 1 (bu surum): LIKIDASYON KADEMESI — sistemin kurulus tezine en yakin olan
ve simdiye kadar HIC sinanmamis sinyal. Coinalyze beslemesi 2026-07-06'dan beri
`olcucu.log`'a "5dk likid L$x S$y" olarak yaziliyor (35 gun, 211k sifir-olmayan).
  - LONG likidasyonu = zorunlu SATIS -> tez A (devam): fiyat DUSER
                                        tez B (fade): fiyat SEKER/YUKSELIR
  - SHORT likidasyonu = zorunlu ALIM  -> tez A: fiyat YUKSELIR | tez B: duser
Isaret hangi teze uydugunu SOYLER; onceden yon dayatilmaz (ham getiri raporlanir).

Calistirma: venv\\Scripts\\python.exe sinyal_tarama.py
Canliya DOKUNMAZ.
"""
import bisect
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import olcucu
import backtest

KOK = Path(__file__).parent
LOG = KOK / "olcucu.log"
ESIK_FILE = KOK / "likidasyon-esik.json"
UFUKLAR = [1, 4, 24]          # saat — kademe hizli bir olay, kisa ufuklar onemli
KOVA_DK = 5                   # sembol basina her 5dk'da TEK gozlem (ustuste binmeyi kir)
GUN = 40                      # klines ufku (likidasyon verisi 35 gun)
TF = "5m"                     # ileri-getiri granulu

SATIR = re.compile(r"^\[([\d\-T:+]+)\] (\w+USDT) .*?likid L\$([\d,]+) S\$([\d,]+)")


def gozlemler():
    """[(ts_ms, sym, L_usd, S_usd)] — kova-teklestirilmis (sembol basina 5dk'da 1)."""
    gorulen = set()
    out = []
    with LOG.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            m = SATIR.match(line)
            if not m:
                continue
            try:
                ts = int(datetime.fromisoformat(m.group(1)).timestamp() * 1000)
            except Exception:
                continue
            sym = m.group(2)
            kova = (sym, ts // (KOVA_DK * 60_000))
            if kova in gorulen:
                continue
            gorulen.add(kova)
            out.append((ts, sym, int(m.group(3).replace(",", "")),
                        int(m.group(4).replace(",", ""))))
    return out


def esikler():
    """Canli sistemin kullandigi per-symbol cascade esikleri (P99.5, 30g)."""
    try:
        d = json.loads(ESIK_FILE.read_text(encoding="utf-8"))
        return d.get("esikler", {})      # {"BTCUSDT": 3497237, ...}
    except Exception:
        return {}


def _fiyat(ts_list, cl, t_ms):
    i = bisect.bisect_right(ts_list, t_ms) - 1
    return cl[i] if 0 <= i < len(cl) else None


def _ort(x):
    return sum(x) / len(x) if x else None


def _persentil(sirali, p):
    if not sirali:
        return None
    i = min(len(sirali) - 1, max(0, int(round(p / 100 * (len(sirali) - 1)))))
    return sirali[i]


def esik_kademeleri(gozl, sym):
    """Sembolun KENDI log dagilimindan kademeli esikler.
    GEREKCE (2026-08-09): canli P99.5 esigi olcum icin cok sert — 35 gunde sembol
    basina ~4 olay -> n=41 toplam, istatistiksel guc SIFIR. Kademeli esik hem
    ornegi buyutur hem DOZ-TEPKI gosterir: gercek bir etki kademeli esikte
    guclenmeli. Guclenmiyorsa gurultudur."""
    tek_taraf = sorted(max(L, S) for ts, s, L, S in gozl if s == sym and max(L, S) > 0)
    return {f"P{p}": _persentil(tek_taraf, p) for p in (90, 95, 99)}


def olc(gozl, sym, ts_list, cl, esik):
    """{ufuk: {"long_liq": [...], "short_liq": [...], "taban": [...]}} — HAM getiriler
    (isaret cevrilmez; yonu veri soylesin)."""
    R = {h: {"long_liq": [], "short_liq": [], "taban": []} for h in UFUKLAR}
    for ts, s, L, S in gozl:
        if s != sym:
            continue
        p0 = _fiyat(ts_list, cl, ts)
        if not p0:
            continue
        for h in UFUKLAR:
            p1 = _fiyat(ts_list, cl, ts + h * 3_600_000)
            if not p1 or p1 == p0:
                continue
            chg = (p1 - p0) / p0 * 100
            R[h]["taban"].append(chg)
            if L >= esik and L > S:
                R[h]["long_liq"].append(chg)     # zorunlu SATIS oldu
            elif S >= esik and S > L:
                R[h]["short_liq"].append(chg)    # zorunlu ALIM oldu
    return R


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    haric = set(getattr(olcucu, "DENEYSEL", set()))
    print("=" * 92)
    print("  SINYAL TARAMA #1 — LIKIDASYON KADEMESI (ileri-getiri, ham isaret)")
    print(f"  ufuklar {UFUKLAR}s | kova {KOVA_DK}dk | fiyat {TF} | "
          + datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))
    print(f"  HARIC (deneysel): {', '.join(sorted(haric)) or '—'}")
    print("=" * 92)

    g = gozlemler()
    g = [x for x in g if x[1] not in haric]
    if not g:
        print("  gozlem yok")
        return
    t0 = datetime.fromtimestamp(g[0][0] / 1000, timezone.utc).date()
    t1 = datetime.fromtimestamp(g[-1][0] / 1000, timezone.utc).date()
    print(f"  {len(g):,} teklestirilmis gozlem | {t0} -> {t1}")

    E = esikler()
    semboller = sorted({x[1] for x in g})
    KADEMELER = ["P90", "P95", "P99", "CANLI(P99.5)"]
    top = {kd: {h: {"long_liq": [], "short_liq": [], "taban": []} for h in UFUKLAR}
           for kd in KADEMELER}
    per = {kd: {} for kd in KADEMELER}
    for sym in semboller:
        try:
            K = backtest.klines_history(sym, TF, GUN)
        except Exception as e:
            print(f"  {sym}: fiyat cekilemedi ({type(e).__name__}) - atlandi", flush=True)
            continue
        ts_list, cl = [k["t"] for k in K], [k["c"] for k in K]
        kd_esik = esik_kademeleri(g, sym)
        kd_esik["CANLI(P99.5)"] = E.get(sym) or 1_000_000
        satir = f"  {sym:<11}"
        for kd in KADEMELER:
            esik = kd_esik.get(kd) or 10 ** 12
            R = olc(g, sym, ts_list, cl, esik)
            per[kd][sym] = R
            for h in UFUKLAR:
                for kk in R[h]:
                    top[kd][h][kk].extend(R[h][kk])
            n = len(R[UFUKLAR[0]]["long_liq"]) + len(R[UFUKLAR[0]]["short_liq"])
            satir += f" | {kd} ${esik:>10,.0f} n={n:<5}"
        print(satir, flush=True)

    print()
    print("=" * 92)
    print("  DOZ-TEPKI — kademe buyudukce etki gucleniyor mu? (gercek etki gucleNMELI)")
    print("  tez A (devam): LONG-liq EDGE negatif + SHORT-liq EDGE pozitif (ZIT isaretler)")
    print("  tez B (fade) : LONG-liq EDGE pozitif + SHORT-liq EDGE negatif")
    print("=" * 92)
    for h in UFUKLAR:
        print(f"\n  --- ufuk +{h} saat ---")
        print(f"  {'kademe':<15}{'L-liq n':>9}{'L EDGE':>10}{'S-liq n':>10}{'S EDGE':>10}{'yorum':>12}")
        for kd in KADEMELER:
            tb = _ort(top[kd][h]["taban"])
            lo, so = _ort(top[kd][h]["long_liq"]), _ort(top[kd][h]["short_liq"])
            ln, sn = len(top[kd][h]["long_liq"]), len(top[kd][h]["short_liq"])
            if tb is None or lo is None or so is None:
                print(f"  {kd:<15}{ln:>9}{'—':>10}{sn:>10}{'—':>10}{'veri yok':>12}")
                continue
            le, se = lo - tb, so - tb
            yorum = "FADE" if (le > 0 and se < 0) else ("DEVAM" if (le < 0 and se > 0) else "karisik")
            print(f"  {kd:<15}{ln:>9,}{le:>+10.3f}{sn:>10,}{se:>+10.3f}{yorum:>12}")

    kd, h = "P95", UFUKLAR[1]
    print()
    print("=" * 92)
    print(f"  SEMBOL BAZINDA ({kd}, +{h}s) — isaret tutarliligi")
    print("=" * 92)
    print(f"  {'sembol':<11}{'L-liq n':>9}{'L edge':>10}{'S-liq n':>10}{'S edge':>10}")
    say = {"long_liq": [0, 0], "short_liq": [0, 0]}
    for sym in semboller:
        R = per[kd].get(sym)
        if not R:
            continue
        tb = _ort(R[h]["taban"])
        if tb is None:
            continue
        sat = f"  {sym:<11}"
        for kk in ("long_liq", "short_liq"):
            o = _ort(R[h][kk])
            n = len(R[h][kk])
            if o is None:
                sat += f"{n:>9}{'—':>10}" if kk == "long_liq" else f"{n:>10}{'—':>10}"
                continue
            e = o - tb
            say[kk][0 if e > 0 else 1] += 1
            sat += f"{n:>9,}{e:>+10.3f}" if kk == "long_liq" else f"{n:>10,}{e:>+10.3f}"
        print(sat)
    print()
    for kk, ad in (("long_liq", "LONG likid"), ("short_liq", "SHORT likid")):
        print(f"  {ad} isaret: {say[kk][0]} sembolde pozitif / {say[kk][1]} negatif")

    print()
    print("OKUMA: (1) Her iki olayin EDGE'i AYNI isaretteyse yon bilgisi degil, ortak")
    print("piyasa hareketidir. (2) DOZ-TEPKI sart: kademe buyudukce etki guclenmiyorsa")
    print("gurultudur. (3) Buyukluk: <%0.5 hareket 2.5 ATR stop mesafesini tasimaz.")
    print("(4) CANLI(P99.5) kademesi 35 gunde ~4 olay/sembol uretiyor -> canli kademe")
    print("tespiti fiilen ATIL; olcum icin de istatistiksel guc vermiyor.")


if __name__ == "__main__":
    main()
