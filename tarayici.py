"""
tarayici.py — Piyasa TARAYICI (on-demand). Canli sisteme DOKUNMAZ.
================================================================================
Ne yapar:
  1) Binance USDT perpetual evrenini al (sadece COIN/INDEX -> tokenize hisse/emtia ELENIR).
  2) 24s hacim tabanini uygula (VARSAYILAN 50M USDT) -> ~likit ~50 coin.
  3) Her coin'i KENDI tarihiyle kalibre et (per-symbol esik) + analiz et (olcucu.analyze_symbol).
  4) Plani GECERLI olanlari (yon var + R/R>=2 + squeeze>=min) skorla sirala, TAM PLAN bas.

YAZMAZ: signals.json'a dokunmaz, deftere (kripto-defter.json) YAZMAZ. Tamamen durumsuz.
Emir HER ZAMAN kullanicida. Bu bir DISIPLIN araci: aday kurulum listeler, kristal kure DEGIL.
net-R analizi hala gecerli (gross+, net-); tarayici edge yaratmaz, sadece nereye baktigini genisletir.

Calistirma:
    venv\\Scripts\\python.exe tarayici.py               # 50M taban (~48 coin)
    venv\\Scripts\\python.exe tarayici.py --taban 30     # 30M taban (daha genis ~66 coin)
    venv\\Scripts\\python.exe tarayici.py --min 75        # min squeeze skoru 75
  veya cift tikla: tarayici.bat
"""

import sys
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import olcucu
import kalibrasyon as kal

# ============================== CONFIG ==============================
VOL_TABAN = 50_000_000            # 24s quote hacim tabani (USDT). Altini gurultu kabul et.
HARD_CAP = 120                    # guvenlik: taban cok dusukse bile en fazla bu kadar coin tara
MIN_SKOR = olcucu.SQUEEZE_FLAG    # 70 -> squeeze flag esigi
DUSUK_GUVEN_SETTLEMENT = 60       # bu kadar altinda funding gecmisi -> "dusuk-guven kalibrasyon"
KALDIRAC_UYARI = 5.0              # ima kaldirac bunu asarsa uyar (dar stop -> cikista slippage riski)
BEKLE = 0.15                      # semboller arasi nazik bekleme (rate-limit koruma)
# 2026-07-16 USDC dersi: $1'a pegli varlikta "sikisma" anlamsiz — USDC LONG plani
# uretilip Telegram'a gitti (stop %0.025, yuvarlamada giris=stop=tp). Liste disinda
# kalan bir peg kacarsa olcucu.STOP_PCT_TABAN vetosu yakalar (cift kademeli savunma).
STABLE_BASES = {"USDC", "FDUSD", "TUSD", "DAI", "USDP", "BUSD", "AEUR", "EUR",
                "USDE", "USD1", "XUSD", "BFUSD", "PYUSD", "EURI"}
MAKRO_FILE = Path(__file__).parent / "makro.json"


def _makro_durum():
    """Kanal 2 kapisi + rejim min-skoru + boyut carpani (varsa)."""
    try:
        m = json.loads(MAKRO_FILE.read_text(encoding="utf-8"))
        return m.get("kapi", "ACIK"), m.get("min_skor", 0), m.get("boyut_carpani", 1.0)
    except Exception:
        return "ACIK", 0, 1.0


def evren(taban):
    """PERPETUAL USDT TRADING (COIN/INDEX) + 24s hacim>=taban - stablecoin'ler.
    Hacme gore sirali [(sym, vol)]."""
    info = olcucu._get("/fapi/v1/exchangeInfo")
    valid = {s["symbol"] for s in info["symbols"]
             if s.get("contractType") == "PERPETUAL"
             and s.get("quoteAsset") == "USDT"
             and s.get("baseAsset") not in STABLE_BASES
             and s.get("status") == "TRADING"}   # EQUITY/COMMODITY (Tesla/altin) bu filtreye girmez
    tick = olcucu._get("/fapi/v1/ticker/24hr")
    rows = [(x["symbol"], float(x["quoteVolume"])) for x in tick
            if x["symbol"] in valid and float(x["quoteVolume"]) >= taban]
    rows.sort(key=lambda r: -r[1])
    return rows[:HARD_CAP]


def kalibre(sym):
    """Per-symbol esik (coin'in KENDI tarihinden) + funding settlement sayisi (guven olcusu)."""
    raw = olcucu._get("/fapi/v1/fundingRate", {"symbol": sym, "limit": 500})
    rates = sorted(float(x["fundingRate"]) for x in raw)
    pos = sorted(d for d in kal.oi_1h_deltas(sym) if d > 0)
    th = {
        "neutral": round(kal.percentile(rates, 50), 8),
        "long_crowded": round(kal.percentile(rates, 85), 8),
        "short_crowded": round(kal.percentile(rates, 15), 8),
        "oi_rising": round(kal.percentile(pos, 80), 4) if pos else 0.4,
    }
    return th, len(raw)


def tara(taban, min_skor):
    kapi, makro_min, boyut = _makro_durum()
    etkin_min = max(min_skor, makro_min)
    coins = evren(taban)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"\n[{stamp}]")
    print(f"EVREN: {len(coins)} coin (USDT-perp, COIN/INDEX; hacim>={taban/1e6:.0f}M) "
          f"| makro kapi: {kapi} | etkin min-skor: {etkin_min}")
    if kapi == "KAPALI":
        print("  UYARI: makro kapi KAPALI -> canli sistem yeni islem ACMAZ. Adaylar yalniz bilgi amacli.")
    print("Taraniyor... (biraz surer)\n")

    bulunan, hata = [], 0
    for sym, vol in coins:
        try:
            th, n_settle = kalibre(sym)
            d = olcucu.analyze_symbol(sym, th)
            sq = d["squeeze"]
            p = d.get("plan", {})
            skor = max(sq["short_squeeze"], sq["long_squeeze"])
            if p.get("yon") and p.get("gecerli") and skor >= etkin_min:
                bulunan.append((skor, sym, vol, d, n_settle))
        except Exception:
            hata += 1
        time.sleep(BEKLE)

    bulunan.sort(key=lambda r: -r[0])
    print("=" * 62)
    if not bulunan:
        print("Hicbir coin'de gecerli plan YOK. (Bu NORMAL — kurulumlar seyrektir.)")
    for skor, sym, vol, d, n_settle in bulunan:
        p, sq = d["plan"], d["squeeze"]
        setup = "LONG SQUEEZE" if sq["long_squeeze"] >= sq["short_squeeze"] else "SHORT SQUEEZE"
        guven = "" if n_settle >= DUSUK_GUVEN_SETTLEMENT else \
                f"   [!] dusuk-guven kalibrasyon (yalniz {n_settle} funding kaydi)"
        print(f"{sym}  —  {setup} kurulumu (skor {skor})   24s hacim {vol/1e6:.0f}M{guven}")
        print(f"   Yon:   {p['yon']}   |   Giris: {p['giris']}   Stop: {p['stop']}  (mesafe %{p['stop_mesafe_pct']})")
        print(f"   TP1:   {p['tp1']}  (R/R {p['rr1']})     TP2: {p['tp2']}  (R/R {p['rr2']})")
        kald = p.get("ima_kaldirac")
        print(f"   Ima kaldirac: ~{kald}x  (portfoyun ~%{p['pozisyon_buyukluk_pct']}, makro boyut x{boyut})   son fiyat: {d['price']}")
        if kald and kald > KALDIRAC_UYARI:
            print(f"   [!] YUKSEK KALDIRAC (~{kald}x): stop cok dar (%{p['stop_mesafe_pct']}) -> cikista slippage riski. Boyutu ELLE kis.")
        print("-" * 62)
    print("=" * 62)
    print(f"OZET: {len(coins)} coin tarandi | {len(bulunan)} gecerli plan | {hata} hata/veri-yok")
    print("NOT: Bunlar ADAY kurulum (disiplinli kural), onaylanmis firsat DEGIL. Emir sende.")


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    taban, min_skor = VOL_TABAN, MIN_SKOR
    if "--taban" in sys.argv:
        try:
            taban = float(sys.argv[sys.argv.index("--taban") + 1]) * 1e6
        except (IndexError, ValueError):
            pass
    if "--min" in sys.argv:
        try:
            min_skor = int(sys.argv[sys.argv.index("--min") + 1])
        except (IndexError, ValueError):
            pass
    t0 = time.time()
    tara(taban, min_skor)
    print(f"(sure: {time.time() - t0:.0f}s)")


if __name__ == "__main__":
    main()
