"""ON-KAYIT OLCUM ARACI — `portfoy` (ON-KAYIT-portfoy.md, commit 8843367)

Ucuncu ve son asama: bu sinyal ailesi bir KASADA ne yapardi?

SALT OKURDUR. Islem sonuclari `onkayit_mekanik.simule()`den CAGRILIR —
kopyalanmaz, boylece B2 ile sapma imkansizdir.

Kullanim:  venv\\Scripts\\python.exe onkayit_portfoy.py
"""
import sys as _sys
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import random
import statistics as st
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

import defter
import olcucu
import onkayit_mekanik as M

ON_KAYIT_COMMIT = "8843367"
BASLANGIC = 1000.0
SLOT = int(defter.RISK_TAVANI_PCT / olcucu.RISK_PCT)   # 2


def bilesik(rler):
    """1000$ · her islem GUNCEL bakiyenin %1'i. panel._bilesik ile ayni."""
    b = tepe = BASLANGIC
    dd = 0.0
    egri = [b]
    for r in rler:
        b *= (1 + olcucu.RISK_PCT / 100.0 * r)
        tepe = max(tepe, b)
        dd = min(dd, b / tepe - 1)
        egri.append(b)
    return b, dd * 100, egri


def altut(bars, t0_ms, t1_ms):
    """Ayni pencerede al-tut: bakiye ve en derin dusus."""
    p = [b for b in bars if t0_ms <= b["t"] <= t1_ms]
    if len(p) < 2:
        return None, None
    giris = p[0]["o"]
    b = tepe = BASLANGIC
    dd = 0.0
    for k in p:
        b = BASLANGIC * (k["c"] / giris)
        tepe = max(tepe, b)
        dd = min(dd, b / tepe - 1)
    return b, dd * 100


def portfoy(S, tavan=True):
    """Kronolojik; tavan varsa ayni yonde en fazla SLOT eszamanli.
    Tavan 'beklemede'yi DE sayar -> slot sinyalden cozume kadar dolu."""
    acik = []
    alinan = []
    for s in sorted(S, key=lambda x: x["dt"]):
        t0 = s["dt"]
        acik = [a for a in acik if a > t0]
        if tavan and len(acik) >= SLOT:
            continue
        if s["durum"] == "tetiklenmedi":
            acik.append(t0 + timedelta(hours=defter.PENDING_SAAT))
            continue                                    # slot doldu ama islem YOK
        acik.append(datetime.fromtimestamp(s["cikis_ts"] / 1000, timezone.utc))
        alinan.append(s)
    alinan.sort(key=lambda x: x["cikis_ts"])            # kapanis sirasi = kasa sirasi
    return alinan


def blok_bootstrap(alinan, tur=4000):
    """Gun bloklu: GUNLER yeniden orneklenir, islemler degil."""
    if len(alinan) < 5:
        return None
    g = defaultdict(list)
    for s in alinan:
        g[datetime.fromtimestamp(s["cikis_ts"] / 1000, timezone.utc).date()].append(s["net_R"])
    bloklar = list(g.values())
    random.seed(11)
    son = []
    for _ in range(tur):
        rl = [r for _ in bloklar for r in random.choice(bloklar)]
        son.append(bilesik(rl)[0])
    son.sort()
    return son[int(0.025 * tur)], son[int(0.975 * tur)]


def rapor(S, bars, baslik, haric=()):
    S2 = [s for s in S if s["sym"] not in haric]
    alinan = portfoy(S2)
    R = [s["net_R"] for s in alinan]
    bak, dd, _ = bilesik(R)
    print(f"\n  {baslik}")
    print("  " + "-" * 70)
    print(f"  1. acilan islem   : {len(alinan)}  (sinyal {len(S2)}, tavan+tetik suzgeci)")
    print(f"  2. son bakiye     : {bak:8.2f} $   en derin dusus {dd:7.1f}%")

    t0 = min(s["dt"] for s in S2)
    t0_ms = int(t0.timestamp() * 1000)
    t1_ms = max(b["t"] for b in bars["BTCUSDT"])
    bb, bdd = altut(bars["BTCUSDT"], t0_ms, t1_ms)
    sepet_b, sepet_dd = [], []
    for sym, bl in bars.items():
        x, y = altut(bl, t0_ms, t1_ms)
        if x:
            sepet_b.append(x)
            sepet_dd.append(y)
    print(f"  3. BTC al-tut     : {bb:8.2f} $   en derin dusus {bdd:7.1f}%")
    print(f"     11-coin sepeti : {st.fmean(sepet_b):8.2f} $   en derin dusus "
          f"{st.fmean(sepet_dd):7.1f}%")

    gecti_getiri = bak > bb
    gecti_dusus = dd > bdd                    # dusus negatif; buyuk = daha SIG
    print(f"  4. G4 HUKMU       : getiri {'GECTI' if gecti_getiri else 'GECMEDI'}"
          f" · dusus {'DAHA AZ' if gecti_dusus else 'DAHA COK'}"
          f"  ->  {'GECTI' if (gecti_getiri and gecti_dusus) else 'GECMEDI'}")

    ga = blok_bootstrap(alinan)
    if ga:
        print(f"  5. gun-bloklu %95 : [{ga[0]:.2f} $, {ga[1]:.2f} $]"
              f"   (tek yol {bak:.2f} $)")
    return alinan


def main():
    print("=" * 76)
    print("  ON-KAYITLI TEST — portfoy (3. ve son asama)")
    print(f"  on kayit: ON-KAYIT-portfoy.md (commit {ON_KAYIT_COMMIT})")
    print(f"  kurallar: risk %{olcucu.RISK_PCT} · tavan %{defter.RISK_TAVANI_PCT}"
          f" (={SLOT} eszamanli) · baslangic {BASLANGIC:.0f}$")
    print("=" * 76)

    _, _, sig = M.sinyaller()
    bars = M.mumlar()
    S = []
    for r in sig:
        b = bars.get(r["sym"])
        if not b:
            continue
        s = M.simule(r, b)
        if s is None:
            continue
        s["sym"] = r["sym"]
        s["dt"] = r["dt"]
        S.append(s)
    print(f"\n  simule edilen sinyal: {len(S)}  (B2 ile AYNI fonksiyon)")

    alinan = rapor(S, bars, "TUM SEMBOLLER")

    katki = Counter(s["sym"] for s in alinan)
    top3 = tuple(s for s, _ in katki.most_common(3))
    rapor(S, bars, f"6. SAGLAMLIK — top-3 ({', '.join(top3)}) CIKARILDI", haric=top3)

    # 7. tavanin etkisi
    tavansiz = [s for s in S if s["durum"] != "tetiklenmedi"]
    tavansiz.sort(key=lambda x: x["cikis_ts"])
    tb, tdd, _ = bilesik([s["net_R"] for s in tavansiz])
    tb2, tdd2, _ = bilesik([s["net_R"] for s in alinan])
    print(f"\n  7. TAVANIN ETKISI")
    print("  " + "-" * 70)
    print(f"     tavanLI  : {len(alinan):3d} islem  {tb2:8.2f} $  dusus {tdd2:7.1f}%")
    print(f"     tavanSIZ : {len(tavansiz):3d} islem  {tb:8.2f} $  dusus {tdd:7.1f}%")
    print(f"     -> tavan {'KORUYOR' if tb2 > tb else 'ZARAR VERIYOR'}"
          f"  ({tb2-tb:+.2f} $)")

    print("\n  " + "=" * 70)
    print("  ⚠ SINIR: bu TEK BIR YOL gerceklesmesidir. Bakiye ve dusus NOKTA")
    print("    TAHMINIDIR; bootstrap oynakligi gosterir, ANLAMLILIK DOGURMAZ.")
    print("  ⚠ Pencerede 20 Agustos bogasi var -> kiyas strateji ALEYHINE zor.")
    print("    Bu bilincli: G4 zaten 'al-tutu gec' diyor, kolay donem secmek")
    print("    olcutu anlamsizlastirir.")
    print("  " + "=" * 70)


if __name__ == "__main__":
    main()
