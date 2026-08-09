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
    top = {h: {"long_liq": [], "short_liq": [], "taban": []} for h in UFUKLAR}
    per = {}
    for sym in semboller:
        esik = E.get(sym) or 1_000_000    # yoksa eski sabit CASCADE_USD
        try:
            K = backtest.klines_history(sym, TF, GUN)
        except Exception as e:
            print(f"  {sym}: fiyat cekilemedi ({type(e).__name__}) - atlandi", flush=True)
            continue
        ts_list, cl = [k["t"] for k in K], [k["c"] for k in K]
        R = olc(g, sym, ts_list, cl, esik)
        per[sym] = R
        for h in UFUKLAR:
            for kk in R[h]:
                top[h][kk].extend(R[h][kk])
        n1 = len(R[UFUKLAR[0]]["long_liq"])
        n2 = len(R[UFUKLAR[0]]["short_liq"])
        print(f"  {sym:<11} esik ${esik:>12,.0f} | LONG-liq {n1:>5} | SHORT-liq {n2:>5}", flush=True)

    print()
    print("=" * 92)
    print("  TOPLAM — kademe SONRASI ham fiyat degisimi (%) | edge = kosullu - taban")
    print("  tez A (devam): LONG-liq sonrasi NEGATIF, SHORT-liq sonrasi POZITIF beklenir")
    print("  tez B (fade) : tam TERSI")
    print("=" * 92)
    print(f"  {'ufuk':<7}{'olay':<14}{'n':>8}{'ort chg':>11}{'taban':>10}{'EDGE':>10}")
    for h in UFUKLAR:
        tb = _ort(top[h]["taban"])
        for kk, ad in (("long_liq", "LONG likid"), ("short_liq", "SHORT likid")):
            v = top[h][kk]
            o = _ort(v)
            if o is None or tb is None:
                print(f"  +{h:<6}{ad:<14}{len(v):>8}{'—':>11}{'—':>10}{'—':>10}")
                continue
            print(f"  +{h:<6}{ad:<14}{len(v):>8,}{o:>+11.3f}{tb:>+10.3f}{o - tb:>+10.3f}")
        print()

    h = UFUKLAR[1]
    print("=" * 92)
    print(f"  SEMBOL BAZINDA (+{h}s, EDGE) — tutarlilik (tek sayiya guvenme)")
    print("=" * 92)
    print(f"  {'sembol':<11}{'L-liq n':>9}{'L edge':>10}{'S-liq n':>10}{'S edge':>10}")
    say = {"long_liq": [0, 0], "short_liq": [0, 0]}
    for sym in semboller:
        R = per.get(sym)
        if not R:
            continue
        tb = _ort(R[h]["taban"])
        if tb is None:
            continue
        sat = f"  {sym:<11}"
        for kk in ("long_liq", "short_liq"):
            o = _ort(R[h][kk])
            if o is None:
                sat += f"{len(R[h][kk]):>9}{'—':>10}" if kk == "long_liq" else f"{len(R[h][kk]):>10}{'—':>10}"
                continue
            e = o - tb
            say[kk][0 if e > 0 else 1] += 1
            sat += (f"{len(R[h][kk]):>9,}{e:>+10.3f}" if kk == "long_liq"
                    else f"{len(R[h][kk]):>10,}{e:>+10.3f}")
        print(sat)
    print()
    for kk, ad in (("long_liq", "LONG likid"), ("short_liq", "SHORT likid")):
        print(f"  {ad} isaret: {say[kk][0]} sembolde pozitif / {say[kk][1]} negatif")

    print()
    print("OKUMA: her iki olayin EDGE'i AYNI isaretteyse bu yon bilgisi degil, ortak")
    print("piyasa hareketidir. Tez A icin LONG-liq NEGATIF + SHORT-liq POZITIF gerekir")
    print("(zit isaretler). Buyukluk de onemli: <%0.5 hareket stop mesafesini tasimaz.")


if __name__ == "__main__":
    main()
