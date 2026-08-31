"""ON-KAYIT OLCUM ARACI — `skor-yonu` (ON-KAYIT-skor-yonu.md, commit 64fb19e)

Sikisma skoru ileri getiriyi TAHMIN mi ediyor, TERS mi?

SALT OKURDUR: yalnizca olcucu.log okunur. Hicbir sicile/state'e/config'e yazmaz.
Olcutler ON KAYITTA DONDURULDU; bu betik onlari uygular, yeniden tanimlamaz.

Kullanim:  venv\\Scripts\\python.exe onkayit_skor.py
"""
import sys as _sys
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import io
import math
import random
import re
import statistics as st
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import olcucu

# --- DONDURULMUS PARAMETRELER (ON-KAYIT-skor-yonu.md §2-§4) ------------------
ON_KAYIT_COMMIT = "64fb19e"
LOG = Path(__file__).parent / "olcucu.log"
UFUK_SAAT = 24
FLAG = olcucu.SQUEEZE_FLAG                      # 70 — sistemin KENDI esigi
BANTLAR = [(0, 20), (20, 40), (40, 60), (60, 80), (80, 101)]
S1_RHO = -0.75
S2_PAY = 0.60
S3_P = 0.05
PERM = 2000
TOHUM = 11

DES = re.compile(r"^\[([\d\-T:+]+)\] ([A-Z0-9]+USDT) \$([\d.]+) .*?SS (\d+) LS (\d+)")


def veri():
    """Log -> saat kovasina seyreltilmis gozlemler + 24s ileri getiri.

    Seyreltme: her (sembol, saat) kovasindan ILK gozlem. Her N'inci kaydi
    almak FAZ KILITLER (dis proje: bir kova orneklemin %62'sini tasimisti).
    """
    kova = {}
    with io.open(LOG, encoding="utf-8", errors="replace") as f:
        for satir in f:
            if " SS " not in satir:
                continue
            m = DES.match(satir)
            if not m:
                continue
            dt = datetime.fromisoformat(m.group(1))
            k = (m.group(2), dt.replace(minute=0, second=0, microsecond=0))
            if k not in kova:
                kova[k] = (float(m.group(3)), int(m.group(4)), int(m.group(5)))

    seri = defaultdict(dict)
    for (sym, saat), v in kova.items():
        seri[sym][saat] = v

    out = []
    for sym, s in seri.items():
        for saat, (px, ss, ls) in s.items():
            hedef = saat + timedelta(hours=UFUK_SAAT)
            ileri = s.get(hedef)
            if ileri is None:
                continue
            out.append({"sym": sym, "gun": saat.date().isoformat(),
                        "ss": ss, "ls": ls,
                        "getiri": (ileri[0] / px - 1) * 100})
    return out


def spearman(x, y):
    def sirala(v):
        s = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        for yer, i in enumerate(s):
            r[i] = yer + 1.0
        return r
    rx, ry = sirala(x), sirala(y)
    n = len(x)
    mx, my = st.fmean(rx), st.fmean(ry)
    pay = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    payda = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return pay / payda if payda else 0.0


def gunluk_karsitlik(D, alan, haric=()):
    """Her gun icin: (skor>=FLAG ortalamasi) - (skor<FLAG ortalamasi).
    Karsitlik GUN ICINDE kurulur -> piyasa geneli hareket goturur."""
    g = defaultdict(list)
    for r in D:
        if r["sym"] in haric:
            continue
        g[r["gun"]].append(r)
    farklar = []
    for gun, kayitlar in g.items():
        ust = [r["getiri"] for r in kayitlar if r[alan] >= FLAG]
        alt = [r["getiri"] for r in kayitlar if r[alan] < FLAG]
        if len(ust) < 2 or len(alt) < 2:
            continue
        farklar.append(st.fmean(ust) - st.fmean(alt))
    return farklar


def kol(D, alan, ad, birincil):
    print(f"\n{'='*76}")
    print(f"  {ad}")
    print(f"{'='*76}")
    ust = [r for r in D if r[alan] >= FLAG]
    gunler = {r["gun"] for r in ust}
    print(f"  n(>={FLAG}) = {len(ust):,}  ·  {len(gunler)} gunde gorulmus  "
          f"·  toplam gozlem {len(D):,}")

    # --- bant ortalamalari (S1) ---
    print(f"\n  {'bant':<12} {'n':>7} {'ort +24s getiri':>18}")
    idx, ort = [], []
    for i, (a, b) in enumerate(BANTLAR):
        v = [r["getiri"] for r in D if a <= r[alan] < b]
        if len(v) < 30:
            print(f"  [{a:>3},{b:>3})   {len(v):>7,} {'(n<30, atlandi)':>18}")
            continue
        m = st.fmean(v)
        idx.append(i)
        ort.append(m)
        print(f"  [{a:>3},{b:>3})   {len(v):>7,} {m:>17.3f}%")
    rho = spearman(idx, ort) if len(idx) >= 3 else float("nan")

    farklar = gunluk_karsitlik(D, alan)
    if not farklar:
        print("\n  Gunluk karsitlik kurulamadi (yeterli gun yok).")
        return
    gozlenen = st.fmean(farklar)
    ayni = sum(1 for f in farklar if f < 0) / len(farklar)

    # --- S3: gun ici etiket permutasyonu ---
    random.seed(TOHUM)
    g = defaultdict(list)
    for r in D:
        g[r["gun"]].append(r)
    daha_uc = 0
    for _ in range(PERM):
        pf = []
        for gun, kayitlar in g.items():
            sk = [r[alan] for r in kayitlar]
            gt = [r["getiri"] for r in kayitlar]
            random.shuffle(sk)
            u = [b for a, b in zip(sk, gt) if a >= FLAG]
            al = [b for a, b in zip(sk, gt) if a < FLAG]
            if len(u) < 2 or len(al) < 2:
                continue
            pf.append(st.fmean(u) - st.fmean(al))
        if pf and st.fmean(pf) <= gozlenen:
            daha_uc += 1
    p = daha_uc / PERM

    # --- S4: yogunlasma (en cok katkili 3 sembol cikar) ---
    semboller = {r["sym"] for r in D}
    etki = []
    for s in semboller:
        k = gunluk_karsitlik(D, alan, haric=(s,))
        etki.append((abs(st.fmean(k) - gozlenen) if k else 0.0, s))
    etki.sort(reverse=True)
    top3 = tuple(s for _, s in etki[:3])
    k3 = gunluk_karsitlik(D, alan, haric=top3)
    sonra = st.fmean(k3) if k3 else float("nan")

    print(f"\n  gunluk karsitlik (>={FLAG} eksi <{FLAG}) : {gozlenen:+.3f}%  "
          f"({len(farklar)} gun)")

    if not birincil:
        print(f"  Spearman rho = {rho:+.3f} · beklenen isarette gun %{100*ayni:.0f} · "
              f"p = {p:.4f}")
        print("\n  ⚠ IKINCIL KOL — hukum DOGURMAZ (§4). Guc %1,93'un altini goremez.")
        return

    print(f"\n  KILL SARTLARI (dordu de gerekli)")
    print("  " + "-" * 72)
    s1 = rho <= S1_RHO
    s2 = ayni >= S2_PAY
    s3 = p <= S3_P
    s4 = (sonra < 0) == (gozlenen < 0) and not math.isnan(sonra)
    print(f"  {'GECTI' if s1 else 'KALDI'}  S1. monotonluk rho <= {S1_RHO}"
          f"{'':>18} rho = {rho:+.3f}")
    print(f"  {'GECTI' if s2 else 'KALDI'}  S2. beklenen isarette gun >= %{S2_PAY*100:.0f}"
          f"{'':>7} %{100*ayni:.0f}  ({sum(1 for f in farklar if f<0)}/{len(farklar)})")
    print(f"  {'GECTI' if s3 else 'KALDI'}  S3. gun-ici permutasyon p <= {S3_P}"
          f"{'':>10} p = {p:.4f}  ({PERM} tur)")
    print(f"  {'GECTI' if s4 else 'KALDI'}  S4. top-3 sembol cikinca isaret ayni"
          f"{'':>7} {gozlenen:+.3f}% -> {sonra:+.3f}%  ({', '.join(top3)})")

    print("\n  " + "=" * 72)
    if s1 and s2 and s3 and s4:
        print("  HUKUM: GECTI — LS skoru SHORT yonunde BILGI TASIYOR.")
        print("  ⚠ Kural degisikligi DOGURMAZ: bu HAM SINYAL asamasidir.")
        print("    Mekanik ve portfoy asamalari ayrica gerekir (madde 7.2).")
    elif rho >= 0.75 and gozlenen > 0:
        print("  HUKUM: 🔴 ISARET TERS — skor SHORT derken fiyat YUKSELIYOR.")
        print("  SISTEM.md §12 madde 1'e dogrudan baglanir.")
        print("  ⚠ 'Tersine cevir' DEMEK DEGILDIR — mekanik/maliyet asamalari yapilmadi.")
    else:
        print("  HUKUM: KALDI — iddia dustu, skor KANITLANMAMIS kalir.")
        print("  Bilesen ayari (madde 3.2/3.3) bu bulguya baglanir.")
    print("  ⚠ Guc serhi AYRILAMAZ: bu test %0,489'dan kucuk bir farki goremez.")
    print("  " + "=" * 72)


def main():
    print("=" * 76)
    print("  ON-KAYITLI TEST — skor-yonu")
    print(f"  on kayit: ON-KAYIT-skor-yonu.md (commit {ON_KAYIT_COMMIT})")
    print(f"  esik: olcucu.SQUEEZE_FLAG = {FLAG} (sistemin kendi esigi, icat edilmedi)")
    print("=" * 76)
    D = veri()
    gunler = sorted({r["gun"] for r in D})
    print(f"\n  gozlem {len(D):,} · {len(gunler)} gun "
          f"({gunler[0]} -> {gunler[-1]}) · {len({r['sym'] for r in D})} sembol")
    kol(D, "ls", "BIRINCIL KOL — LS >= 70  (LONG-squeeze = SHORT sinyali)", True)
    kol(D, "ss", "IKINCIL KOL — SS >= 70  (SHORT-squeeze = LONG sinyali)", False)


if __name__ == "__main__":
    main()
