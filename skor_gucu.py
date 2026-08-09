"""
skor_gucu.py — SIKISMA SKORUNUN TAHMIN GUCU VAR MI? (2026-08-09)
================================================================================
SORU: Sistemin cekirdek tezi "sikisma skoru >=70 -> fiyat o yone gider". Bu
tez BUGUNE KADAR HIC DOGRUDAN OLCULMEDI. backtest/ileritest/aday_testi araclarinin
HICBIRI skoru simule etmiyor (dis denetim BULGU 1, 2026-08-03) — hepsi filtresiz
kirilim tabanini olcuyor. Sicil ise n=24 ile hukum vermek icin cok kucuk.

COZUM: `olcucu.log` 42 gundur her 30 saniyede her sembol icin GERCEK skoru yaziyor
(TAM skor — funding+OI+L/S+yakinlik hepsi dahil). 918k gozlem. Bu, skorun canli
davranisinin tam kaydidir; yeniden insaya GEREK YOK.

YONTEM: her (zaman, sembol, SS, LS) gozlemi icin ileri-getiri olc:
  - SHORT-squeeze >=70 iddiasi: fiyat YUKARI gitmeli (yukari kirilim avi)
  - LONG-squeeze  >=70 iddiasi: fiyat ASAGI gitmeli (asagi kirilim avi)
Ufuklar: +4s, +24s, +120s (120s = canli ACTIVE_SAAT).
Karsilastirma capasi: AYNI sembol-saatlerdeki KOSULSUZ ortalama getiri (taban).
Skorun degeri = kosullu getiri - kosulsuz getiri (edge), yon-isaretli.

DURUSTLUK SINIRLARI:
  - Bu bir ISLEM simulasyonu DEGIL: giris/stop/TP yok, sadece skorun yon tahmini
    olculur. Komisyon/kayma yok. Amac "sinyalde bilgi var mi" sorusu.
  - Gozlemler 30sn araliklarla ve ustuste biniyor (bagimsiz degil) -> ORTALAMA
    guvenilir, ama klasik p-degeri gecersiz. Bu yuzden SEMBOL-BAZINDA ve
    HAFTA-BAZINDA tutarlilik raporlanir (tek sayiya guvenme, B1 dersi).
  - Anlik-fiyat log'dan, ileri-fiyat Binance 1h klines'tan -> ~dakika hizalamasi.

Calistirma: venv\\Scripts\\python.exe skor_gucu.py
Canliya DOKUNMAZ; sadece log okur + klines ceker + rapor basar.
"""
import bisect
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import olcucu
import backtest

LOG = Path(__file__).parent / "olcucu.log"
UFUKLAR = [4, 24, 120]          # saat
ESIK = olcucu.SQUEEZE_FLAG      # 70
GUN = 60                        # klines ufku (log ~42 gun)
SATIR = re.compile(r"^\[([\d\-T:+]+)\] (\w+USDT) .*?SS (\d+) LS (\d+)")


def log_gozlemleri():
    """[(ts_ms, sym, ss, ls)] — log'daki TUM skor kayitlari."""
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
            out.append((ts, m.group(2), int(m.group(3)), int(m.group(4))))
    return out


def fiyat_serisi(sym):
    """(ts_listesi, kapanis_listesi) — 1h klines, ileri-getiri icin."""
    K = backtest.klines_history(sym, "1h", GUN)
    return [k["t"] for k in K], [k["c"] for k in K]


def _fiyat(ts_list, cl, t_ms):
    i = bisect.bisect_right(ts_list, t_ms) - 1
    return cl[i] if 0 <= i < len(cl) else None


def olc(gozlemler, sym, ts_list, cl):
    """Bir sembol icin kosullu vs kosulsuz ileri-getiri.
    Doner: {ufuk: {"ss": [...], "ls": [...], "taban": [...]}} (yuzde getiriler)."""
    R = {h: {"ss": [], "ls": [], "taban": []} for h in UFUKLAR}
    for ts, s, ss, ls in gozlemler:
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
            if ss >= ESIK:
                R[h]["ss"].append(chg)      # iddia: YUKARI
            if ls >= ESIK:
                R[h]["ls"].append(-chg)     # iddia: ASAGI -> isaret cevrilir
    return R


def _ort(x):
    return sum(x) / len(x) if x else None


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print("=" * 96)
    print("  SIKISMA SKORUNUN TAHMIN GUCU — canli log ileri-getiri testi")
    print(f"  esik >={ESIK} | ufuklar {UFUKLAR} saat | " +
          datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))
    print("=" * 96)

    g = log_gozlemleri()
    if not g:
        print("  olcucu.log okunamadi / gozlem yok")
        return
    t0 = datetime.fromtimestamp(g[0][0] / 1000, timezone.utc).date()
    t1 = datetime.fromtimestamp(g[-1][0] / 1000, timezone.utc).date()
    print(f"  {len(g):,} gozlem | {t0} -> {t1}")
    print()

    # DENEYSEL semboller (LAB) HARIC — ilk kosuda (2026-08-09) LAB tabloyu domine etti:
    # SS edge -58.8 / LS edge +30.2 (o donemde $16 -> $0.12 coktu). LAB SS gozlemlerinin
    # %8'iydi ama toplam SS edge'inin TAMAMINI tek basina uretiyordu. Ana sicilde de
    # (defter.ozet) deneysel ayri tutuldugu icin burada da AYNI kural uygulanir.
    haric = set(getattr(olcucu, "DENEYSEL", set()))
    if "--lab-dahil" in sys.argv:
        haric = set()
    semboller = sorted({x[1] for x in g} - haric)
    if haric:
        print(f"  HARIC (deneysel): {', '.join(sorted(haric))}")
    top = {h: {"ss": [], "ls": [], "taban": []} for h in UFUKLAR}
    per_sym = {}
    for sym in semboller:
        try:
            ts_list, cl = fiyat_serisi(sym)
        except Exception as e:
            print(f"  {sym}: fiyat cekilemedi ({type(e).__name__}) - atlandi", flush=True)
            continue
        R = olc(g, sym, ts_list, cl)
        per_sym[sym] = R
        for h in UFUKLAR:
            for kk in ("ss", "ls", "taban"):
                top[h][kk].extend(R[h][kk])
        print(f"  {sym} islendi", flush=True)

    print()
    print("=" * 96)
    print("  TOPLAM — 'iddia yonunde ortalama getiri' (%) | edge = kosullu - taban")
    print("=" * 96)
    print(f"  {'ufuk':<8}{'sinyal':<16}{'n':>9}{'ort getiri':>13}{'taban':>10}{'EDGE':>10}")
    for h in UFUKLAR:
        tb = _ort(top[h]["taban"])
        for ad, kk in (("SHORT-sq (yukari)", "ss"), ("LONG-sq (asagi)", "ls")):
            v = top[h][kk]
            o = _ort(v)
            if o is None:
                print(f"  +{h:<7}{ad:<16}{0:>9}{'—':>13}{'—':>10}{'—':>10}")
                continue
            # taban yon-isaretli: LONG-sq iddiasi asagi oldugu icin taban da cevrilir
            tb_y = tb if kk == "ss" else -tb
            print(f"  +{h:<7}{ad:<16}{len(v):>9,}{o:>+13.3f}{tb_y:>+10.3f}{o - tb_y:>+10.3f}")
        print()

    print("=" * 96)
    print("  SEMBOL BAZINDA (+120s ufku, EDGE) — tutarlilik kontrolu (tek sayiya guvenme)")
    print("=" * 96)
    print(f"  {'sembol':<11}{'SS n':>7}{'SS edge':>10}{'LS n':>9}{'LS edge':>10}")
    h = UFUKLAR[-1]
    for sym in semboller:
        R = per_sym.get(sym)
        if not R:
            continue
        tb = _ort(R[h]["taban"])
        if tb is None:
            continue
        ss_o, ls_o = _ort(R[h]["ss"]), _ort(R[h]["ls"])
        ss_s = f"{ss_o - tb:+.3f}" if ss_o is not None else "—"
        ls_s = f"{ls_o + tb:+.3f}" if ls_o is not None else "—"
        print(f"  {sym:<11}{len(R[h]['ss']):>7,}{ss_s:>10}{len(R[h]['ls']):>9,}{ls_s:>10}")

    # Isaret tutarliligi: kac sembolde edge pozitif? (tek sayiya guvenme, B1 dersi)
    print()
    for kk, ad in (("ss", "SHORT-sq"), ("ls", "LONG-sq")):
        poz = neg = 0
        for sym in semboller:
            R = per_sym.get(sym)
            if not R:
                continue
            tb = _ort(R[h]["taban"])
            o = _ort(R[h][kk])
            if tb is None or o is None:
                continue
            e = (o - tb) if kk == "ss" else (o + tb)
            poz += e > 0
            neg += e <= 0
        print(f"  {ad} isaret tutarliligi (+120s): {poz} sembolde POZITIF / {neg} sembolde negatif")

    print()
    print("OKUMA: EDGE > 0 -> skor o yonde BILGI tasiyor. 0 civari -> gurultu.")
    print("EDGE < 0 -> skor TERS yonde bilgi tasiyor (fade adayi).")
    print("Gozlemler ustuste biniyor (30sn ritim) -> p-degeri hesaplanmadi; sembol")
    print("bazinda ISARET TUTARLILIGINA bak. Islem simulasyonu DEGIL (giris/stop/fee yok).")


if __name__ == "__main__":
    main()
