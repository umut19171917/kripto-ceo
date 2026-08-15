"""
spread_olcum.py — ALIS-SATIS FARKI: maliyet modelimiz gercek mi? (2026-08-15)
================================================================================
NEDEN: `SLIPPAGE = 0.0002` (%0.02/taker bacak) 2026-07-02'den beri VARSAYIM olarak
duruyor, hic olculmedi. Spread/likidite kontrolu denetimlerde uc kez "acik" diye
isaretlendi ve her seferinde K3'e ertelendi.

Bu ERTELEME YANLISTI: piyasa emri en iyi ihtimalle YARIM SPREAD oder. Yani
  gercek kayma >= spread / 2
Spread %0.04'ten genisse varsayimimiz KUCUK kaliyor ve bugune kadarki TUM net-R
hesaplari (K1, K2 sicili, aday sinavi, sinif testi, carry) IYIMSER demektir.
Ozellikle radar evreni (vol>=30M, ince coinler) ve `sinif_testi` KUCUK kademesi
icin belirleyici.

EN KARAR-ILGILI OLCU: spread'in STOP MESAFESINE orani. Stop = 2.5 ATR = 1R.
Spread 1R'nin %10'uysa, her islem daha acilirken %10 R kaybeder — isabet
oranindan bagimsiz, dogrudan muhasebeden duser.

YONTEM: /fapi/v1/ticker/bookTicker (tek istek, tum semboller) N kez orneklenir
(anlik carpiklik icin medyan alinir). ATR her sembolun 1h mumlarindan.
⚠ SINIR: top-of-book olculur, DERINLIK olculmez. Buyuk emir defteri yurur;
kucuk hesapta ust kademe yaklasik dogrudur. Ayrica anlik — haber/dalgalanma
aninda spread aciliyor, bu olcum sakin bir ani yakalamis olabilir (IYIMSER yon).

Calistirma: venv\\Scripts\\python.exe spread_olcum.py
Canliya DOKUNMAZ.
"""
import statistics
import sys
import time
from datetime import datetime, timezone

import olcucu
import backtest
import tarayici

ORNEK = 5              # bookTicker orneklemesi (medyan alinir)
ARA_SN = 15
STOP_ATR = 2.5         # canli config: stop = 2.5 ATR = 1R
SLIP_VARSAYIM = 0.0002 # backtest.SLIPPAGE — sinanan varsayim
KADEME_N = 20


def book_ornekleri():
    """{sym: medyan spread orani} — N ornegin medyani."""
    birikim = {}
    for i in range(ORNEK):
        try:
            for x in olcucu._get("/fapi/v1/ticker/bookTicker"):
                b, a = float(x.get("bidPrice") or 0), float(x.get("askPrice") or 0)
                if b > 0 and a > b:
                    birikim.setdefault(x["symbol"], []).append((a - b) / ((a + b) / 2))
        except Exception as e:
            print(f"  ornek {i+1}: HATA {type(e).__name__}", flush=True)
        if i < ORNEK - 1:
            time.sleep(ARA_SN)
    return {s: statistics.median(v) for s, v in birikim.items() if v}


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print("=" * 96)
    print("  SPREAD OLCUMU — 'kayma %0.02' varsayimi gercek mi?")
    print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} | "
          f"{ORNEK} ornek x {ARA_SN}sn | stop = {STOP_ATR} ATR = 1R")
    print(f"  SINANAN VARSAYIM: kayma %{SLIP_VARSAYIM*100:.3f}/bacak "
          f"(piyasa emri en az YARIM spread oder)")
    print("=" * 96)

    print(f"\n  bookTicker orneklemesi ({ORNEK} x {ARA_SN}sn) ...", flush=True)
    sp = book_ornekleri()
    print(f"  {len(sp)} sembol")

    # evren: hacme gore kademeler (tarayici.evren ile ayni suzgec)
    rows = tarayici.evren(0)                      # [(sym, 24s quoteVolume)] hacme gore sirali
    rows = [(s, v) for s, v in rows if s in sp]
    print(f"  hacim verisi olan: {len(rows)} sembol")

    kademeler = [("BUYUK (1-20)", rows[:KADEME_N]),
                 ("ORTA (21-40)", rows[KADEME_N:2 * KADEME_N]),
                 ("KUCUK (41-60)", rows[2 * KADEME_N:3 * KADEME_N]),
                 ("RADAR ESIGI (>=30M)", [r for r in rows if r[1] >= 30_000_000])]

    print("\n" + "=" * 96)
    print("  KADEME BAZINDA SPREAD")
    print("=" * 96)
    print(f"  {'kademe':<22}{'n':>4}{'medyan spread':>15}{'yarim spread':>14}"
          f"{'varsayimin kaci':>17}")
    for ad, liste in kademeler:
        v = sorted(sp[s] for s, _ in liste if s in sp)
        if not v:
            continue
        med = statistics.median(v)
        print(f"  {ad:<22}{len(v):>4}{'%'+format(med*100,'.4f'):>15}"
              f"{'%'+format(med/2*100,'.4f'):>14}{med/2/SLIP_VARSAYIM:>16.1f}x")

    # --- asil olcu: spread / stop mesafesi (R'nin yuzde kaci) ---
    print("\n" + "=" * 96)
    print("  ASIL OLCU — spread, 1R'nin (2.5 ATR stop) yuzde kaci?")
    print("  (her islem acilirken bu kadarini pesin kaybeder; isabetten bagimsiz)")
    print("=" * 96)
    print(f"  {'kademe':<22}{'n':>4}{'medyan spread/R':>18}{'en kotu':>12}")
    ayrinti = {}
    for ad, liste in kademeler[:3]:
        oran = []
        for s, _ in liste:
            try:
                K = olcucu.get_klines(s, "1h", 30)
                a = olcucu.atr(K)
                if not a or a <= 0 or not K:
                    continue
                fiyat = K[-1]["c"]
                r_mesafe = STOP_ATR * a / fiyat          # R, fiyatin yuzdesi olarak
                if r_mesafe > 0:
                    oran.append((s, sp[s] / r_mesafe))
            except Exception:
                continue
            time.sleep(0.1)
        if not oran:
            continue
        v = sorted(x[1] for x in oran)
        ayrinti[ad] = oran
        enk = max(oran, key=lambda x: x[1])
        print(f"  {ad:<22}{len(v):>4}{'%'+format(statistics.median(v)*100,'.2f'):>18}"
              f"  {enk[0]} %{enk[1]*100:.2f}")

    print("\n" + "=" * 96)
    print("OKUMA:")
    print("  - 'varsayimin kaci' 1.0'a yakinsa maliyet modelimiz dogru; 2-3x ise")
    print("    bugune kadarki TUM net-R hesaplari o oranda IYIMSER demektir.")
    print("  - spread/R %5'i gecerse dar-stop stratejisi yapisal olarak zorlanir:")
    print("    her islem daha acilmadan R'nin o kadarini oder.")
    print("  - ⚠ Derinlik olculmedi (top-of-book). Buyuk emir daha kotu doldurur.")
    print("  - ⚠ Anlik olcum; carkanti aninda spread acilir -> bu sayi IYIMSER yon.")


if __name__ == "__main__":
    main()
