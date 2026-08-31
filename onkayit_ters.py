"""ON-KAYIT OLCUM ARACI — `ters` (ON-KAYIT-ters.md, commit 0130da6)

"LS >= 70 iken LONG" ne yapardi?

🔴 ORNEKLEM-ICI INSA. Hukum DOGURMAZ (§0). Tek cevapladigi soru:
   ileri-zamanli test kurmaya deger mi?

SALT OKURDUR. Sinyal/mum/tekillestirme yolu onkayit_mekanik'ten CAGRILIR.

Kullanim:  venv\\Scripts\\python.exe onkayit_ters.py
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

ON_KAYIT_COMMIT = "0130da6"
BOGA_BAS = "2026-08-20"          # §3'te sabitlendi (SISTEM.md kaydi)
BASLANGIC = 1000.0
SLOT = int(defter.RISK_TAVANI_PCT / olcucu.RISK_PCT)


def simule_long(r, bars):
    """trade_plan'in LONG dali, BIREBIR. SHORT'un aynasi DEGIL:
    giris swing_HIGH (yukari kirilim), stop ALTTA, TP USTTE."""
    ms = int(r["dt"].timestamp() * 1000)
    i = next((j for j, b in enumerate(bars) if b["t"] >= ms), None)
    if i is None or i < M.LOOKBACK + 15:
        return None
    swing_high = max(b["h"] for b in bars[i - M.LOOKBACK:i])
    atr = olcucu.atr(bars[:i], 14)
    if not atr or atr <= 0:
        return None

    giris = swing_high
    stop = giris - atr * M.STOP_ATR
    tp1 = giris + atr * M.TP1_ATR
    tp2 = giris + atr * M.TP2_ATR
    risk = giris - stop
    if risk <= 0 or min(stop, tp1, tp2) <= 0:
        return None
    if risk / giris * 100 < M.TABAN:
        return None

    tetik = None
    for j in range(i, min(i + M.PENDING, len(bars))):
        if bars[j]["h"] >= giris:            # YUKARI kirilim
            tetik = j
            break
    if tetik is None:
        return {"durum": "tetiklenmedi", "net_R": 0.0,
                "tetik_ts": None, "cikis_ts": None}

    sonuc, cikis, cj = "zaman_asimi", None, None
    for j in range(tetik, min(tetik + M.ACTIVE, len(bars))):
        b = bars[j]
        if b["l"] <= stop:                   # TEMKINLI: stop oncelikli
            sonuc, cikis, cj = "stop", stop, j
            break
        if b["h"] >= tp2:
            sonuc, cikis, cj = "tp2", tp2, j
            break
        if b["h"] >= tp1:
            sonuc, cikis, cj = "tp1", tp1, j
            break
    son = min(tetik + M.ACTIVE, len(bars)) - 1
    if cikis is None:
        cikis, cj = bars[son]["c"], son

    brut = (cikis - giris) / risk            # LONG: yukari = kar
    mal = defter.maliyet_R({"giris": giris, "stop": stop, "yon": "LONG"})
    return {"durum": sonuc, "net_R": brut - mal,
            "tetik_ts": bars[tetik]["t"], "cikis_ts": bars[cj]["t"]}


def bilesik(rler):
    b = tepe = BASLANGIC
    dd = 0.0
    for r in rler:
        b *= (1 + olcucu.RISK_PCT / 100.0 * r)
        tepe = max(tepe, b)
        dd = min(dd, b / tepe - 1)
    return b, dd * 100


def portfoy(S):
    acik, alinan = [], []
    for s in sorted(S, key=lambda x: x["dt"]):
        acik = [a for a in acik if a > s["dt"]]
        if len(acik) >= SLOT:
            continue
        if s["durum"] == "tetiklenmedi":
            acik.append(s["dt"] + timedelta(hours=defter.PENDING_SAAT))
            continue
        acik.append(datetime.fromtimestamp(s["cikis_ts"] / 1000, timezone.utc))
        alinan.append(s)
    alinan.sort(key=lambda x: x["cikis_ts"])
    return alinan


def ga_gun(S):
    if len(S) < 5:
        return None
    g = defaultdict(list)
    for s in S:
        g[s["gun"]].append(s["net_R"])
    bl = list(g.values())
    random.seed(11)
    o = []
    for _ in range(3000):
        d = [x for _ in bl for x in random.choice(bl)]
        if d:
            o.append(st.fmean(d))
    o.sort()
    return o[75], o[-75]


def kesit(S, ad):
    tet = [s for s in S if s["durum"] != "tetiklenmedi"]
    print(f"\n  {ad}")
    print("  " + "-" * 70)
    if not S:
        print("    sinyal yok")
        return
    print(f"    sinyal {len(S)} · tetiklenme {len(tet)} (%{100*len(tet)/len(S):.1f})")
    if len(tet) < 5:
        print("    ⚠ n<5 — hicbir nicelik raporlanmiyor")
        return
    say = Counter(s["durum"] for s in tet)
    print("    sonuc: " + " · ".join(f"{k} {v}" for k, v in say.most_common()))
    R = [s["net_R"] for s in tet]
    ga = ga_gun(tet)
    gs = f"[{ga[0]:+.3f}, {ga[1]:+.3f}]" if ga else "GA yok"
    isaret = "⚠ n<20 -> OLCULEMEDI" if len(tet) < 20 else ""
    print(f"    ortalama net R: {st.fmean(R):+.3f}R  gun-kumeli GA95 {gs}  {isaret}")
    al = portfoy(S)
    bak, dd = bilesik([s["net_R"] for s in al])
    print(f"    portfoy: {len(al)} islem · {bak:.2f} $ · en derin dusus {dd:.1f}%")


def main():
    print("=" * 76)
    print("  ON-KAYITLI OLCUM — ters kural ('LS>=70 iken LONG')")
    print(f"  on kayit: ON-KAYIT-ters.md (commit {ON_KAYIT_COMMIT})")
    print("  🔴 ORNEKLEM-ICI INSA — HUKUM DOGURMAZ (§0)")
    print("=" * 76)

    _, _, sig = M.sinyaller()
    bars = M.mumlar()
    L, S = [], []
    for r in sig:
        b = bars.get(r["sym"])
        if not b:
            continue
        a = simule_long(r, b)
        k = M.simule(r, b)
        if a is None or k is None:
            continue
        for d, hedef in ((a, L), (k, S)):
            d["sym"] = r["sym"]
            d["dt"] = r["dt"]
            d["gun"] = r["dt"].date().isoformat()
            hedef.append(d)
    print(f"\n  simule edilen sinyal: {len(L)}  (ayni sinyaller, iki yon)")

    kesit(L, "1. TERS KURAL (LONG) — TUM PENCERE")
    print("\n  " + "=" * 70)
    print("  2. REJIM KIRILIMI — bu olcumun ASIL sorusu")
    print("  " + "=" * 70)
    kesit([s for s in L if s["gun"] < BOGA_BAS], f"2a. BOGA ONCESI (< {BOGA_BAS})")
    kesit([s for s in L if s["gun"] >= BOGA_BAS], f"2b. BOGA (>= {BOGA_BAS})")

    katki = Counter(s["sym"] for s in portfoy(L))
    top3 = tuple(x for x, _ in katki.most_common(3))
    kesit([s for s in L if s["sym"] not in top3],
          f"4. SAGLAMLIK — top-3 ({', '.join(top3)}) CIKARILDI")

    print("\n  " + "=" * 70)
    print("  5. YAN YANA — ayni sinyaller, iki yon")
    print("  " + "=" * 70)
    for ad, D in (("MEVCUT (SHORT)", S), ("TERS (LONG)", L)):
        tet = [s for s in D if s["durum"] != "tetiklenmedi"]
        al = portfoy(D)
        bak, dd = bilesik([s["net_R"] for s in al])
        R = st.fmean([s["net_R"] for s in tet]) if tet else 0
        print(f"    {ad:16s} tetik {len(tet):3d} · ort {R:+.3f}R · "
              f"portfoy {len(al):2d} islem {bak:7.2f} $ · dusus {dd:6.1f}%")

    print("\n  " + "=" * 70)
    print("  ⛔ §0: bu ORNEKLEM-ICI bir insadir. Kural degisikligi DOGURMAZ,")
    print("     'ters kural calisiyor' cumlesini KURDURAMAZ. Tek cevapladigi:")
    print("     ileri-zamanli test kurmaya deger mi?")
    print("  ⚠ §5: YALNIZ bogada pozitiflik BULGU DEGIL TOTOLOJIDIR.")
    print("  " + "=" * 70)


if __name__ == "__main__":
    main()
