"""
olcucu.py — Kripto CEO sistemi · YEREL VERI + MATEMATIK katmani (Faz 1 + Faz 2)
================================================================================
Amac: Binance futures public verisini cek -> TUM matematigi burada (deterministik)
yap -> kucuk bir ozet (signals.json) yaz. Token harcamaz. CEO (Claude/Opus) sadece
bu ozeti okur, sinyal sayar, veto uygular, rapor verir.

Esikler PER-SYMBOL olarak esikler.json'dan okunur (izleyici periyodik gunceller);
dosya yoksa DEFAULT_TH kullanilir.

Calistirma:
    venv\\Scripts\\python.exe olcucu.py            # tek snapshot
    venv\\Scripts\\python.exe olcucu.py --loop 30   # her 30 sn'de bir guncelle
"""

import os
import sys
import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

# ============================== CONFIG ==============================
BASE = "https://fapi.binance.com"
# C2 genislemesi (2026-07-05, kullanici onayi): 4 -> 11 coin.
# Secim verisi: hacim + funding gecmisi >=166g + 8s funding ritmi + korelasyon
# cesitliligi (ZEC 0.50 / NEAR 0.57). LABUSDT = kullanici istegiyle TAM UYE; ama
# funding'i SAATLIK oldugundan kalibrasyonu yapisal zayif (pencere ~1 ay) ->
# tahminleri "deneysel" etiketlenir, ANA sicil istatistigine (K2) KARISMAZ.
SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "LINKUSDT",
           "XRPUSDT", "BNBUSDT", "DOGEUSDT", "ZECUSDT", "ADAUSDT", "NEARUSDT",
           "LABUSDT"]
DENEYSEL = {"LABUSDT"}   # kayitlari tutulur+cozulur ama ana sicilden ayri raporlanir
SCALP_TF = "5m"
SWING_TF = "1h"                  # PLAN bu dilimden uretilir (swing-1h konfig, 2026-07-02)
KLINE_LIMIT = 200            # gosterge penceresi
SWING_LOOKBACK = 50          # likidasyon miknatis seviyeleri icin
HTTP_TIMEOUT = 15
OUT_FILE = Path(__file__).parent / "signals.json"
LOG_FILE = Path(__file__).parent / "olcucu.log"
ESIK_FILE = Path(__file__).parent / "esikler.json"

# Esikler.json yoksa kullanilacak KALIBRE varsayilan (BTC+ETH ~2 ay @2026-06-27)
DEFAULT_TH = {
    "neutral": 0.000021,         # ~+0.0021% (medyan)
    "long_crowded": 0.000065,    # ~+0.0065% (P85) -> long kalabalik
    "short_crowded": -0.000043,  # ~-0.0043% (P15) -> short kalabalik
    "oi_rising": 0.43,           # 1s OI pozitif degisim P80 -> yakit birikiyor
}
SQUEEZE_FLAG = 70                # >=70 -> sikisma kurulumu flag

# --- Faz 2 uretici: ATR-tabanli deterministik giris/stop/TP ---
# SWING-1H (2026-07-02): plan 1h ATR + 1h seviyeden. Gerekce (backtest 90g+180g,
# 4 major): net R 5m'de her configde negatif, 1h'de filtreli 6/6 pozitif; genis
# stop (2.5 ATR) tutarli en iyi bolge. Oranlar korundu: rr1=2.08, rr2=3.33.
PLAN_FLAG = SQUEEZE_FLAG          # plan ancak alarm seviyesinde (>=70) uretilir (tutarlilik)
STOP_ATR = 2.5                   # stop = giris -+ ATR(1h)*2.5
TP1_ATR = 5.2                    # TP1  = giris +- ATR*5.2   (rr1 = 5.2/2.5 = 2.08)
STOP_PCT_TABAN = 0.1             # stop mesafesi fiyatin %0.1'inden dar -> dejenere (stablecoin/olu oynaklik);
                                 # gidis-donus fee (~%0.08-0.13) tek basina stop mesafesini asar, icra edilemez
TP2_ATR = 8.33                   # TP2  = giris +- ATR*8.33  (rr2 = 3.33)
RISK_PCT = 1.0                   # islem basina portfoyun %1'i risk


def get_thresholds(symbol):
    """Per-symbol esikleri esikler.json'dan oku; yoksa/eksikse DEFAULT_TH ile doldur."""
    th = dict(DEFAULT_TH)
    if ESIK_FILE.exists():
        try:
            data = json.loads(ESIK_FILE.read_text(encoding="utf-8"))
            th.update(data.get("symbols", {}).get(symbol, {}))
        except Exception:
            pass
    return th


# ============================== REST yardimcilari ==============================
def _get(path, params=None):
    r = requests.get(BASE + path, params=params, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    return r.json()


def get_klines(symbol, interval, limit=KLINE_LIMIT):
    """Binance kline dizisi -> [{t,o,h,l,c,v,taker_buy}]."""
    raw = _get("/fapi/v1/klines", {"symbol": symbol, "interval": interval, "limit": limit})
    # idx: 0 openTime,1 o,2 h,3 l,4 c,5 vol,6 closeTime,7 quoteVol,8 trades,9 takerBuyBase,...
    return [
        {"t": k[0], "o": float(k[1]), "h": float(k[2]), "l": float(k[3]),
         "c": float(k[4]), "v": float(k[5]), "taker_buy": float(k[9])}
        for k in raw
    ]


def get_funding(symbol):
    d = _get("/fapi/v1/premiumIndex", {"symbol": symbol})
    return {"mark": float(d["markPrice"]),
            "index": float(d["indexPrice"]),
            "funding": float(d["lastFundingRate"])}


def get_oi(symbol):
    return float(_get("/fapi/v1/openInterest", {"symbol": symbol})["openInterest"])


def get_oi_hist(symbol, period="5m", limit=288):
    raw = _get("/futures/data/openInterestHist",
               {"symbol": symbol, "period": period, "limit": limit})
    return [{"t": x["timestamp"], "oi": float(x["sumOpenInterest"])} for x in raw]


def get_ls_ratio(symbol, period="5m"):
    raw = _get("/futures/data/globalLongShortAccountRatio",
               {"symbol": symbol, "period": period, "limit": 1})
    return float(raw[-1]["longShortRatio"])


# top_ls (topLongShortPositionRatio) KALDIRILDI (2026-07-04, B1 karari):
# canli sicilde katkisiz (monotonluk rho -0.12, n=30) + tarihsel test IMKANSIZ
# (uc nokta ~30 gun tutar; 60g istegi HTTP 400, probe ile dogrulandi) ->
# "ya kullan ya toplama" kurali geregi cekim birakildi (~11.5k bos istek/gun idi).


# ============================== Matematik (deterministik) ==============================
def atr(klines, period=14):
    """Average True Range (son `period` mum)."""
    if len(klines) < period + 1:
        return None
    trs = []
    for i in range(1, len(klines)):
        h, l, pc = klines[i]["h"], klines[i]["l"], klines[i - 1]["c"]
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    return sum(trs[-period:]) / period


def rsi(klines, period=14):
    """Wilder RSI."""
    closes = [k["c"] for k in klines]
    if len(closes) < period + 1:
        return None
    gains, losses = [], []
    for i in range(1, len(closes)):
        d = closes[i] - closes[i - 1]
        gains.append(max(d, 0.0))
        losses.append(max(-d, 0.0))
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - 100.0 / (1.0 + rs)


def vwap(klines):
    """Pencere VWAP (tipik fiyat x hacim)."""
    num = den = 0.0
    for k in klines:
        tp = (k["h"] + k["l"] + k["c"]) / 3.0
        num += tp * k["v"]
        den += k["v"]
    return num / den if den else None


def cvd(klines, last_n=None):
    """Cumulative Volume Delta. Mum basina delta = 2*takerBuy - hacim.
    last_n verilirse son N mumun toplam deltasi (yakin baski yonu)."""
    seq = klines[-last_n:] if last_n else klines
    return sum(2.0 * k["taker_buy"] - k["v"] for k in seq)


def pct_change(old, new):
    if not old:
        return None
    return (new - old) / old * 100.0


def swing_levels(klines, lookback=SWING_LOOKBACK):
    window = klines[-lookback:]
    return max(k["h"] for k in window), min(k["l"] for k in window)


# ============================== Sikisma modulu ==============================
def squeeze_scores(price, funding, oi_delta_pct, ls_ratio, swing_high, swing_low, th):
    """
    SHORT squeeze (yukari av): short'lar likide olur -> zorunlu alim -> fiyat YUKARI.
    LONG  squeeze (asagi av):  long'lar  likide olur -> zorunlu satis -> fiyat ASAGI.
    Her biri 0-100. Yakit: kalabalik taraf (funding) + OI birikimi + L/S egimi + kumeye yakinlik.
    `th` per-symbol kalibre esikler (esikler.json).
    """
    short_c, neutral, long_c, oi_rise = (
        th["short_crowded"], th["neutral"], th["long_crowded"], th["oi_rising"])
    oi_delta_pct = oi_delta_pct or 0.0
    dist_high = pct_change(price, swing_high) or 0.0   # fiyatin ustteki kumeye uzakligi %
    dist_low = pct_change(swing_low, price) or 0.0     # fiyatin alttaki kumeye uzakligi %

    # --- SHORT SQUEEZE ---
    ss = 0
    if funding <= short_c:
        ss += 30
    elif funding < neutral:
        ss += 15
    if oi_delta_pct >= oi_rise:
        ss += 25
    if ls_ratio < 1.0:               # short hesaplar baskin
        ss += 20
    if 0 <= dist_high <= 2:          # fiyat ustteki short-likidasyon kumesine cok yakin
        ss += 25
    elif 2 < dist_high <= 4:
        ss += 12

    # --- LONG SQUEEZE ---
    ls = 0
    if funding >= long_c:
        ls += 30
    elif funding > neutral:
        ls += 15
    if oi_delta_pct >= oi_rise:
        ls += 25
    if ls_ratio > 1.5:               # long hesaplar baskin
        ls += 20
    if 0 <= dist_low <= 2:           # fiyat alttaki long-likidasyon kumesine cok yakin
        ls += 25
    elif 2 < dist_low <= 4:
        ls += 12

    ss, ls = min(ss, 100), min(ls, 100)
    note = "yok"
    if ss >= SQUEEZE_FLAG and ss >= ls:
        note = f"SHORT SQUEEZE kurulumu ({ss}/100) -> yukari risk, hedef ~{swing_high:.2f}"
    elif ls >= SQUEEZE_FLAG:
        note = f"LONG SQUEEZE kurulumu ({ls}/100) -> asagi risk, hedef ~{swing_low:.2f}"
    return ss, ls, note


# ============================== Faz 2 uretici (islem plani) ==============================
def _p(price):
    """Fiyat buyuklugune gore ondalik hassasiyet (~4 anlamli hane).
    2026-07-16 AKE dersi: 0.001$ coinde sabit 4 hane = %10'luk fiyat adimlari ->
    0.1 altinda hane sayisi buyuklukle olceklenir (onde gelen sifir basina +1),
    tavan 8 (Binance max hassasiyet)."""
    if price >= 1000:
        return 1
    if price >= 10:
        return 2
    if price >= 1:
        return 3
    if price >= 0.1:
        return 4
    return min(8, 3 - math.floor(math.log10(price)))


def trade_plan(price, atr_val, swing_high, swing_low, ss, lsq):
    """Sikisma yonu + ATR + yapisal seviyeden DETERMINISTIK islem plani.
    SHORT squeeze -> LONG (yukari kirilim) | LONG squeeze -> SHORT (asagi kirilim).
    Pozisyon boyutu = portfoyun %'si (notional); makro boyut_carpani ile carpilir (rapor aninda)."""
    if not atr_val or atr_val <= 0:
        return {"yon": None, "neden": "ATR yok"}
    d = _p(price)
    if lsq >= ss and lsq >= PLAN_FLAG:
        yon, giris = "SHORT", swing_low          # long squeeze -> asagi kirilim
        stop = giris + atr_val * STOP_ATR
        tp1, tp2 = giris - atr_val * TP1_ATR, giris - atr_val * TP2_ATR
    elif ss > lsq and ss >= PLAN_FLAG:
        yon, giris = "LONG", swing_high          # short squeeze -> yukari kirilim
        stop = giris - atr_val * STOP_ATR
        tp1, tp2 = giris + atr_val * TP1_ATR, giris + atr_val * TP2_ATR
    else:
        return {"yon": None, "neden": f"sikisma yetersiz (SS{ss}/LS{lsq} < {PLAN_FLAG})"}

    risk = abs(giris - stop)
    rr1 = round(abs(tp1 - giris) / risk, 2) if risk else None
    rr2 = round(abs(tp2 - giris) / risk, 2) if risk else None
    stop_pct = round(risk / giris * 100, 2) if giris else None
    poz_pct = round(RISK_PCT / stop_pct * 100, 1) if stop_pct else None
    gecerli = rr1 is not None and rr1 >= 2.0
    neden = "R/R yeterli (>=2)" if gecerli else "R/R<2 -> VETO (girme)"
    # Sagliklilik kontrolu (2026-07-08, LAB #110 dersi): cokus sonrasi ATR eski
    # (yuksek-fiyat donemi) oynakligi tasirken fiyat dusukse stop/TP sifirin
    # altina inebilir — fiyat negatif OLAMAZ, boyle plan matematiksel sacmadir.
    if min(stop, tp1, tp2) <= 0:
        gecerli = False
        neden = "dejenere plan: stop/TP <= 0 (ATR fiyata gore asiri genis) -> VETO (girme)"
    # Sagliklilik #2 (2026-07-16, USDC dersi): pegli/olu-oynaklik varliklarda stop
    # girise yapisik kalir (USDC: stop %0.025) — fee mesafeyi asar, ustune yuvarlama
    # seviyeleri cakistirip risk=0 "plan" yayinlatabilir. Iki kontrol birden:
    elif stop_pct is not None and (stop_pct < STOP_PCT_TABAN or round(stop, d) == round(giris, d)):
        gecerli = False
        neden = (f"dejenere plan: stop girise yapisik (stop %{stop_pct} < %{STOP_PCT_TABAN}"
                 f" veya yuvarlamada cakisiyor) -> VETO (girme)")
    return {
        "yon": yon,
        "giris": round(giris, d), "stop": round(stop, d),
        "tp1": round(tp1, d), "tp2": round(tp2, d),
        "rr1": rr1, "rr2": rr2,
        "risk_pct": RISK_PCT, "stop_mesafe_pct": stop_pct,
        "pozisyon_buyukluk_pct": poz_pct,
        "ima_kaldirac": round(poz_pct / 100, 1) if poz_pct else None,
        "gecerli": gecerli,
        "neden": neden,
    }


# ============================== Tek sembol analizi ==============================
def analyze_symbol(symbol, th=None):
    k_scalp = get_klines(symbol, SCALP_TF)
    k_swing = get_klines(symbol, SWING_TF)
    price = k_scalp[-1]["c"]

    fund = get_funding(symbol)
    oi_now = get_oi(symbol)
    oi_hist = get_oi_hist(symbol, "5m", 288)  # 288 x 5m = 24s
    oi_24h = pct_change(oi_hist[0]["oi"], oi_hist[-1]["oi"]) if oi_hist else None
    oi_1h = pct_change(oi_hist[-12]["oi"], oi_hist[-1]["oi"]) if len(oi_hist) >= 12 else None
    ls = get_ls_ratio(symbol)

    sh, sl = swing_levels(k_swing)   # 1h yapisal seviyeler (plan girisi + sikisma yakinligi)
    th = get_thresholds(symbol) if th is None else th   # tarayici kendi kalibre esigini verebilir
    # Sikismada 1s OI deltasi kullanilir (1h plan dilimiyle uyumlu); esikler per-symbol kalibre
    ss, lsq, note = squeeze_scores(price, fund["funding"], oi_1h, ls, sh, sl, th)
    plan = trade_plan(price, atr(k_swing), sh, sl, ss, lsq)   # swing-1h: ATR de 1h

    def tf_block(klines):
        vw = vwap(klines)
        a = atr(klines)
        r = rsi(klines)
        return {
            "rsi": round(r, 1) if r is not None else None,
            "vwap": round(vw, 2) if vw else None,
            "price_vs_vwap_pct": round(pct_change(vw, price), 2) if vw else None,
            "atr": round(a, 2) if a else None,
            "atr_pct": round(a / price * 100, 2) if a else None,
            "cvd": round(cvd(klines), 1),
            "cvd_son10": round(cvd(klines, 10), 1),
        }

    return {
        "price": price,
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "scalp": {"tf": SCALP_TF, **tf_block(k_scalp)},
        "swing": {"tf": SWING_TF, **tf_block(k_swing)},
        "derivs": {
            "funding": fund["funding"],
            "funding_pct": round(fund["funding"] * 100, 4),
            "oi": oi_now,
            "oi_delta_1h_pct": round(oi_1h, 2) if oi_1h is not None else None,
            "oi_delta_24h_pct": round(oi_24h, 2) if oi_24h is not None else None,
            "ls_ratio": round(ls, 3),
        },
        "levels": {
            "swing_high": round(sh, 2),
            "swing_low": round(sl, 2),
            "dist_to_high_pct": round(pct_change(price, sh), 2),
            "dist_to_low_pct": round(pct_change(sl, price), 2),
        },
        "squeeze": {"short_squeeze": ss, "long_squeeze": lsq, "note": note},
        "plan": plan,
        "esik": th,
    }


# ============================== Calisma dongusu ==============================
# --- BIRIKEN DOSYALAR: asla kucumeyen sicil/arsivler (madde 7.6) --------------
# Bu dosyalar YALNIZ BUYUR. Yarisindan fazlasini kaybeden bir yazma, veri
# kaybinin ta kendisidir ve yazilmadan REDDEDILIR.
#
# NEDEN BURADA: defter.py ve radar_defter.py duzenleme kilidi altinda; ama ikisi
# de atomik_yaz'dan geciyor. Korumayi tek gecis noktasina koymak, kilitli
# dosyalara DOKUNMADAN onlari da kapsar.
#
# NEDEN %50 (hassas degil, felaket esigi): amac gunluk dalgalanmayi yakalamak
# degil, TOPLU KAYBI yakalamaktir. Dis proje `os.replace` ile 58 sembolde 4
# gunluk veriyi kaybetti; bizde A1 arizasi esikler.json'un 11 sembolunu birden
# sildi. Ikisi de bu esigi asardi. Dar bir esik canli sureci yanlis alarmla
# durdurabilirdi — kayit tutmayi durdurmak da bir veri kaybidir.
BIRIKEN_DOSYALAR = ("kripto-defter.json", "radar-defter.json", "bot-defter.json")
KUCULME_SINIRI = 0.50


class BirikenDosyaKuculdu(RuntimeError):
    """Biriken bir dosya yarisindan fazlasini kaybedecekti; yazma iptal edildi."""


def atomik_yaz(path, obj):
    """JSON'u atomik yaz (tmp + os.replace): okuyucu asla yarim dosya gormez.
    signals/makro/rejim/esikler ayni anda baska surecler tarafindan okunur.

    🔴 BIRIKEN_DOSYALAR icin ek degismez (madde 7.6): sonuc eskisinin
    %50'sinden kucukse BirikenDosyaKuculdu firlatir ve ESKI DOSYA KALIR."""
    path = Path(path)
    metin = json.dumps(obj, ensure_ascii=False, indent=2)
    if path.name in BIRIKEN_DOSYALAR and path.exists():
        try:
            eski = path.stat().st_size
        except OSError:
            eski = 0
        yeni = len(metin.encode("utf-8"))
        if eski > 0 and yeni < eski * KUCULME_SINIRI:
            raise BirikenDosyaKuculdu(
                f"{path.name}: {eski:,} -> {yeni:,} bayt "
                f"(%{100*yeni/eski:.0f}). Yazma IPTAL, eski dosya korundu. "
                f"Bu, kalici veri kaybinin ta kendisidir.")
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(metin, encoding="utf-8")
    os.replace(tmp, path)


def atomik_yaz_metin(path, text):
    """atomik_yaz ile ayni garanti, JSON-olmayan dosyalar icin (ornek: HTML rapor)."""
    path = Path(path)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def run_once():
    out = {"updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "source": "binance-futures-rest", "symbols": {}}
    for sym in SYMBOLS:
        try:
            out["symbols"][sym] = analyze_symbol(sym)
        except Exception as e:
            out["symbols"][sym] = {"error": f"{type(e).__name__}: {e}"}
    atomik_yaz(OUT_FILE, out)
    return out


def log_line(msg):
    """Konsola yaz (varsa) + olcucu.log dosyasina ekle. pythonw/arka planda print guvenli."""
    try:
        print(msg, flush=True)
    except Exception:
        pass  # pythonw.exe altinda stdout yok -> sadece dosyaya yaz
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")


def main():
    # Konsol/log Turkce karakterleri sorunsuz yazsin
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    loop_sec = None
    if "--loop" in sys.argv:
        try:
            loop_sec = int(sys.argv[sys.argv.index("--loop") + 1])
        except (IndexError, ValueError):
            loop_sec = 30

    while True:
        t0 = time.time()
        out = run_once()
        stamp = out["updated_at"]
        for sym, d in out["symbols"].items():
            if "error" in d:
                log_line(f"[{stamp}] {sym}: HATA {d['error']}")
                continue
            sq = d["squeeze"]
            der = d["derivs"]
            log_line(f"[{stamp}] {sym} ${d['price']} | funding {der['funding_pct']}% "
                     f"| OI24s {der['oi_delta_24h_pct']}% | SS {sq['short_squeeze']} LS {sq['long_squeeze']}")
            if sq["note"] != "yok":
                log_line(f"    >>> ALARM: {sq['note']}")
        if loop_sec is None:
            break
        time.sleep(max(1, loop_sec - (time.time() - t0)))


if __name__ == "__main__":
    main()
