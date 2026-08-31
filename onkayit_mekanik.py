"""ON-KAYIT OLCUM ARACI — `mekanik` (ON-KAYIT-mekanik.md, commit 984a6bb)

Stopumuz sinyalin ne kadarini yiyor? (bekleyen-isler 7.2 / yol haritasi B2)

SALT OKURDUR. Mekanik sabitleri `olcucu`/`defter`ten CAGRILIR, kopyalanmaz.
Olcutler ON KAYITTA donduruldu; bu betik onlari uygular.

Kullanim:  venv\\Scripts\\python.exe onkayit_mekanik.py
"""
import sys as _sys
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import io
import json
import random
import re
import statistics as st
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import defter
import olcucu

ON_KAYIT_COMMIT = "984a6bb"
KLINE_DIZIN = Path(r"C:\Users\KURT~1\AppData\Local\Temp\claude"
                   r"\c--Users-KURT-1-Desktop-KLASRL-1-kripto"
                   r"\db3a2db3-76e1-4464-a5d6-abc8bbc0abce\scratchpad\b2_klines")
LOG = Path(__file__).parent / "olcucu.log"
DES = re.compile(r"^\[([\d\-T:+]+)\] ([A-Z0-9]+USDT) \$([\d.]+) .*?SS (\d+) LS (\d+)")

FLAG = olcucu.SQUEEZE_FLAG          # 70
LOOKBACK = olcucu.SWING_LOOKBACK    # 50
STOP_ATR = olcucu.STOP_ATR          # 2.5
TP1_ATR = olcucu.TP1_ATR            # 5.2
TP2_ATR = olcucu.TP2_ATR            # 8.33
TABAN = olcucu.STOP_PCT_TABAN       # 0.1
PENDING = defter.PENDING_SAAT       # 24
ACTIVE = defter.ACTIVE_SAAT         # 120
COOLDOWN = defter.COOLDOWN_SAAT     # 12
SON_VERI = datetime(2026, 8, 31, tzinfo=timezone.utc)


def sinyaller():
    """Log -> saat kovasi -> LS>=70 -> 12s cooldown -> tam pencereye siganlar."""
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
                kova[k] = int(m.group(5))
    ham = sorted([{"sym": s, "dt": t, "ls": ls}
                  for (s, t), ls in kova.items() if ls >= FLAG],
                 key=lambda r: r["dt"])
    son, tekil = {}, []
    for r in ham:
        if r["sym"] in son and (r["dt"] - son[r["sym"]]) < timedelta(hours=COOLDOWN):
            continue
        son[r["sym"]] = r["dt"]
        tekil.append(r)
    tam = [r for r in tekil
           if r["dt"] + timedelta(hours=PENDING + ACTIVE) <= SON_VERI]
    return len(ham), len(tekil), tam


def mumlar():
    d = {}
    for f in KLINE_DIZIN.glob("*.json"):
        d[f.stem] = json.loads(f.read_text(encoding="utf-8"))
    return d


def simule(r, bars):
    """trade_plan mekanigini BIREBIR uygular, 1h barla cozer.

    Temkinli kural: ayni barda hem stop hem TP degerse STOP kabul edilir
    (bar ici yol bilinmiyor) -> sinyalin ALEYHINE yanlilik.
    """
    ms = int(r["dt"].timestamp() * 1000)
    i = next((j for j, b in enumerate(bars) if b["t"] >= ms), None)
    if i is None or i < LOOKBACK + 15:
        return None
    pencere = bars[i - LOOKBACK:i]
    swing_low = min(b["l"] for b in pencere)
    atr = olcucu.atr(bars[:i], 14)
    if not atr or atr <= 0:
        return None

    giris = swing_low
    stop = giris + atr * STOP_ATR
    tp1 = giris - atr * TP1_ATR
    tp2 = giris - atr * TP2_ATR
    risk = stop - giris
    if risk <= 0 or min(stop, tp1, tp2) <= 0:
        return None                                   # dejenere plan -> VETO
    if risk / giris * 100 < TABAN:
        return None                                   # stop girise yapisik -> VETO

    # --- tetiklenme (24s): SHORT girisi swing_low'un ALTINA kirilim ---
    tetik = None
    for j in range(i, min(i + PENDING, len(bars))):
        if bars[j]["l"] <= giris:
            tetik = j
            break
    if tetik is None:
        return {"durum": "tetiklenmedi", "net_R": 0.0, "giris": giris,
                "stop_pct": risk / giris * 100}

    # --- cozum (120s) ---
    sonuc, cikis = "zaman_asimi", None
    for j in range(tetik, min(tetik + ACTIVE, len(bars))):
        b = bars[j]
        vurdu_stop = b["h"] >= stop
        vurdu_tp2 = b["l"] <= tp2
        vurdu_tp1 = b["l"] <= tp1
        if vurdu_stop:                       # TEMKINLI: stop oncelikli
            sonuc, cikis = "stop", stop
            break
        if vurdu_tp2:
            sonuc, cikis = "tp2", tp2
            break
        if vurdu_tp1:
            sonuc, cikis = "tp1", tp1
            break
    ufuk_son = min(tetik + ACTIVE, len(bars)) - 1
    if cikis is None:
        cikis = bars[ufuk_son]["c"]

    brut_R = (giris - cikis) / risk
    mal = defter.maliyet_R({"giris": giris, "stop": stop, "yon": "SHORT"})
    # stop kaldirilsaydi ufuk sonunda ne olurdu (7.2'nin ASIL sorusu)
    ufukta = (giris - bars[ufuk_son]["c"]) / risk - mal
    return {"durum": sonuc, "net_R": brut_R - mal, "ufuk_R": ufukta,
            "giris": giris, "stop_pct": risk / giris * 100}


def ga_gun(degerler_gun, tur=4000):
    """Gun-kumeli bootstrap: GUNLER yeniden ornekleniyor, islemler degil."""
    if len(degerler_gun) < 3:
        return None
    random.seed(11)
    g = list(degerler_gun.values())
    ort = []
    for _ in range(tur):
        s = [random.choice(g) for _ in g]
        duz = [x for grup in s for x in grup]
        if duz:
            ort.append(st.fmean(duz))
    ort.sort()
    return ort[int(0.025 * len(ort))], ort[int(0.975 * len(ort))]


def rapor(sonuclar, baslik, haric=()):
    S = [s for s in sonuclar if s["sym"] not in haric]
    if not S:
        return
    tetik = [s for s in S if s["durum"] != "tetiklenmedi"]
    print(f"\n  {baslik}")
    print(f"  {'-'*70}")
    print(f"  A1. tetiklenme orani : {len(tetik)}/{len(S)} = "
          f"%{100*len(tetik)/len(S):.1f}")
    if not tetik:
        return
    say = Counter(s["durum"] for s in tetik)
    print("  A2. sonuc dagilimi   : " + " · ".join(
        f"{k} {v} (%{100*v/len(tetik):.0f})" for k, v in say.most_common()))

    stoplar = [s for s in tetik if s["durum"] == "stop"]
    if stoplar:
        kurtulan = [s for s in stoplar if s["ufuk_R"] > 0]
        print(f"  B3. STOP olanlarin ufuk sonunda KARDA olacaklari : "
              f"{len(kurtulan)}/{len(stoplar)} = %{100*len(kurtulan)/len(stoplar):.1f}")
    kazanan = [s for s in tetik if s["durum"] in ("tp1", "tp2")]
    if kazanan:
        bozulan = [s for s in kazanan if s["ufuk_R"] <= 0]
        print(f"  B4. TP'ye ulasanlarin ufukta ZARARA donecekleri  : "
              f"{len(bozulan)}/{len(kazanan)} = %{100*len(bozulan)/len(kazanan):.1f}")

    gunluk = defaultdict(list)
    for s in tetik:
        gunluk[s["gun"]].append(s["net_R"])
    R = [s["net_R"] for s in tetik]
    ga = ga_gun(gunluk)
    ga_s = f"[{ga[0]:+.3f}, {ga[1]:+.3f}]" if ga else "GA yok"
    print(f"  C5. ortalama net R   : {st.fmean(R):+.3f}R  gun-kumeli GA95 {ga_s}"
          f"  (n={len(R)}, {len(gunluk)} gun)")

    gunluk_u = defaultdict(list)
    for s in tetik:
        gunluk_u[s["gun"]].append(s["ufuk_R"])
    U = [s["ufuk_R"] for s in tetik]
    print(f"  C6. STOPSUZ (ufuk sonu) : {st.fmean(U):+.3f}R"
          f"   ->  STOPUN ETKISI {st.fmean(R)-st.fmean(U):+.3f}R/islem")


def main():
    print("=" * 76)
    print("  ON-KAYITLI TEST — mekanik (stopumuz sinyalin ne kadarini yiyor?)")
    print(f"  on kayit: ON-KAYIT-mekanik.md (commit {ON_KAYIT_COMMIT})")
    print(f"  mekanik: LS>={FLAG} · giris swing_low({LOOKBACK}h) · stop {STOP_ATR}xATR"
          f" · TP {TP1_ATR}/{TP2_ATR}xATR · {PENDING}s+{ACTIVE}s")
    print("=" * 76)

    n_ham, n_tekil, sig = sinyaller()
    bars = mumlar()
    print(f"\n  ham LS>=70 {n_ham:,} -> cooldown {n_tekil} -> tam pencere {len(sig)}")
    print(f"  1h mum: {len(bars)} sembol")

    sonuclar = []
    atlanan = 0
    for r in sig:
        b = bars.get(r["sym"])
        if not b:
            atlanan += 1
            continue
        s = simule(r, b)
        if s is None:
            atlanan += 1
            continue
        s["sym"] = r["sym"]
        s["gun"] = r["dt"].date().isoformat()
        sonuclar.append(s)
    print(f"  simule edilen: {len(sonuclar)}  ·  atlanan (dejenere/veri): {atlanan}")

    rapor(sonuclar, "TUM SINYALLER")

    # D7 — saglamlik
    katki = Counter(s["sym"] for s in sonuclar if s["durum"] != "tetiklenmedi")
    top3 = tuple(s for s, _ in katki.most_common(3))
    rapor(sonuclar, f"D7. SAGLAMLIK — top-3 sembol ({', '.join(top3)}) CIKARILDI",
          haric=top3)

    print("\n  " + "=" * 70)
    print("  ⚠ GUC SERHI (ayrilamaz): sayim nicelikleri (A/B) iyi guclendirilmis")
    print("    (oran GA yari genisligi ~±%4,7). BUYUKLUK (C5) DEGIL: gorulebilen")
    print("    fark ~0,32R, B1'in ham etkisinin R karsiligi ~0,06-0,10R.")
    print("    C5'ten 'etki yok' CIKARILAMAZ; yalniz 'gosterilemedi' denir.")
    print("  ⚠ Ayni barda stop+TP -> STOP sayildi: sinyalin ALEYHINE yanlilik.")
    print("  " + "=" * 70)


if __name__ == "__main__":
    main()
