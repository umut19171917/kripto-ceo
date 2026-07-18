"""
rejim.py — D0: PIYASA REJIMI + capraz-varlik KONTAJYON katmani
================================================================================
Bu modul tek bir coine degil, PIYASANIN GENEL HAVASINA bakar:
  - Volatilite rejimi : BTC gunluk getirilerinin son-30g oynakligi / taban oynaklik
  - Korelasyon        : BTC-ETH-SOL-LINK saatlik getirilerinin ort. ikili korelasyonu
  - Trend             : BTC fiyat vs 50g ortalama + 30g degisim

Cikti -> rejim.json + makro kapisina "gate katkisi" (kapi / boyut / min_skor).
FELSEFE: skora DOGRUDAN karismaz; KAPI/BOYUT/SECICILIK ayarlar (Kanal 2 ile ayni mantik).
GUVENLIK: her hata -> NOTR rejim (hicbir kisitlama eklemez) -> mevcut davranis korunur.

Calistirma: venv\\Scripts\\python.exe rejim.py
"""

import sys
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import olcucu  # get_klines, SYMBOLS, SQUEEZE_FLAG

REJIM_FILE = Path(__file__).parent / "rejim.json"
TAZE_DK = 20            # rejim.json bu dk'dan yeniyse yeniden hesaplama (rejim yavas degisir)

# Esikler (canli veride kalibre edilebilir)
VOL_YUKSEK = 1.5       # son30g vol / taban vol >= 1.5 -> yuksek volatilite rejimi
KOR_SPIKE = 0.85       # ortalama ikili korelasyon >= 0.85 -> kontajyon riski
SMA_GUN = 50           # trend icin BTC gunluk SMA penceresi

BASE_MIN_SKOR = olcucu.SQUEEZE_FLAG   # 70 — normal secicilik tabani
SIKI_MIN_SKOR = 80                    # oynak/kontajyon -> sadece guclu setup


# ============================== Matematik yardimcilari ==============================
def _returns(closes):
    return [(closes[i] - closes[i - 1]) / closes[i - 1]
            for i in range(1, len(closes)) if closes[i - 1]]


def _std(xs):
    n = len(xs)
    if n < 2:
        return None
    m = sum(xs) / n
    return math.sqrt(sum((x - m) ** 2 for x in xs) / n)


def _pearson(a, b):
    n = min(len(a), len(b))
    if n < 10:
        return None
    a, b = a[-n:], b[-n:]
    ma, mb = sum(a) / n, sum(b) / n
    cov = sum((a[i] - ma) * (b[i] - mb) for i in range(n))
    va = sum((x - ma) ** 2 for x in a)
    vb = sum((x - mb) ** 2 for x in b)
    if va <= 0 or vb <= 0:
        return None
    return cov / math.sqrt(va * vb)


# ============================== Bilesenler ==============================
def vol_rejimi():
    """BTC gunluk: son-30g realize vol / taban vol -> oran + yuksek mi."""
    try:
        cl = [k["c"] for k in olcucu.get_klines("BTCUSDT", "1d", 200)]
        r = _returns(cl)
        if len(r) < 60:
            return {"vol_orani": None, "yuksek": False, "btc_30g_vol_pct": None}
        son30 = _std(r[-30:])
        taban = _std(r[:-30]) or _std(r)
        oran = (son30 / taban) if (son30 and taban) else None
        return {"vol_orani": round(oran, 2) if oran else None,
                "yuksek": bool(oran and oran >= VOL_YUKSEK),
                "btc_30g_vol_pct": round(son30 * 100, 2) if son30 else None}
    except Exception as e:
        return {"vol_orani": None, "yuksek": False, "btc_30g_vol_pct": None, "hata": str(e)[:50]}


# Korelasyon SABIT 4 majorden olculur (T5 dersi: KOR_SPIKE=0.85 esigi bu 4'luye
# gore ayarlandi; SYMBOLS genisledikce metrik kaymasin diye SYMBOLS'ten AYRILDI).
KOR_SYMS = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "LINKUSDT")


def korelasyon():
    """BTC-ETH-SOL-LINK saatlik getiri ortalama ikili korelasyonu."""
    try:
        rets = {}
        for s in KOR_SYMS:
            cl = [k["c"] for k in olcucu.get_klines(s, "1h", 168)]   # ~7 gun
            rets[s] = _returns(cl)
        syms = list(rets.keys())
        ciftler = []
        for i in range(len(syms)):
            for j in range(i + 1, len(syms)):
                p = _pearson(rets[syms[i]], rets[syms[j]])
                if p is not None:
                    ciftler.append(p)
        if not ciftler:
            return {"ort": None, "spike": False}
        ort = sum(ciftler) / len(ciftler)
        return {"ort": round(ort, 2), "spike": bool(ort >= KOR_SPIKE)}
    except Exception as e:
        return {"ort": None, "spike": False, "hata": str(e)[:50]}


def trend():
    """BTC gunluk: fiyat vs 50g SMA + 30g degisim -> boga/ayi/yatay."""
    try:
        cl = [k["c"] for k in olcucu.get_klines("BTCUSDT", "1d", 60)]
        if len(cl) < SMA_GUN + 1:
            return {"bias": "bilinmiyor", "chg30_pct": None}
        sma = sum(cl[-SMA_GUN:]) / SMA_GUN
        fiyat = cl[-1]
        chg30 = (cl[-1] - cl[-31]) / cl[-31] * 100
        if fiyat > sma and chg30 > 0:
            bias = "boga"
        elif fiyat < sma and chg30 < 0:
            bias = "ayi"
        else:
            bias = "yatay"
        return {"bias": bias, "chg30_pct": round(chg30, 1)}
    except Exception as e:
        return {"bias": "bilinmiyor", "chg30_pct": None, "hata": str(e)[:50]}


# ============================== Birlestir ==============================
def hesapla():
    now = datetime.now(timezone.utc)
    v = vol_rejimi()
    k = korelasyon()
    t = trend()
    vy, ks = bool(v.get("yuksek")), bool(k.get("spike"))
    if vy and ks:
        durum = "COKUS-RISKI"
    elif vy or ks:
        durum = "OYNAK"
    else:
        durum = "SAKIN"
    return {
        "updated_at": now.isoformat(timespec="seconds"),
        "durum": durum,
        "vol_orani": v.get("vol_orani"),
        "vol_yuksek": vy,
        "korelasyon": k.get("ort"),
        "kor_spike": ks,
        "trend": t.get("bias"),
        "btc_30g_degisim_pct": t.get("chg30_pct"),
        "_detay": {"vol": v, "kor": k, "trend": t},
    }


def write_rejim(path=None):
    path = Path(path) if path else REJIM_FILE
    out = hesapla()
    try:
        olcucu.atomik_yaz(path, out)
    except Exception:
        pass
    return out


def oku_veya_hesapla(taze_dk=TAZE_DK):
    """rejim.json yeterince yeniyse onu oku; degilse yeniden hesapla+yaz.
    Her hata -> NOTR (kisitlamasiz) rejim doner -> mevcut davranis korunur."""
    try:
        if REJIM_FILE.exists():
            yas = (datetime.now(timezone.utc).timestamp() - REJIM_FILE.stat().st_mtime) / 60
            if yas < taze_dk:
                return json.loads(REJIM_FILE.read_text(encoding="utf-8"))
        return write_rejim()
    except Exception:
        return {"durum": "bilinmiyor", "vol_orani": None, "vol_yuksek": False,
                "korelasyon": None, "kor_spike": False, "trend": "bilinmiyor"}


def gate_katkisi(rej):
    """Rejim -> makro kapisina katki: {kapi, carpan, min_skor, notlar}.
    NOTR taban: ACIK / 1.0 / 70 (BASE_MIN_SKOR). Tamamen hata-toleransli."""
    try:
        vy = bool(rej.get("vol_yuksek"))
        ks = bool(rej.get("kor_spike"))
        if vy and ks:
            return {"kapi": "KAPALI", "carpan": 0.0, "min_skor": SIKI_MIN_SKOR,
                    "notlar": [f"COKUS rejimi (vol x{rej.get('vol_orani')} + korelasyon "
                               f"{rej.get('korelasyon')}) -> yeni giris yok"]}
        if vy:
            return {"kapi": "DIKKAT", "carpan": 0.5, "min_skor": SIKI_MIN_SKOR,
                    "notlar": [f"yuksek volatilite (vol x{rej.get('vol_orani')}) -> "
                               f"yari boyut + sadece guclu setup (>={SIKI_MIN_SKOR})"]}
        if ks:
            return {"kapi": "DIKKAT", "carpan": 0.5, "min_skor": SIKI_MIN_SKOR,
                    "notlar": [f"capraz-varlik korelasyonu yuksek ({rej.get('korelasyon')}) -> "
                               f"kontajyon riski, yari boyut + secici"]}
    except Exception:
        pass
    return {"kapi": "ACIK", "carpan": 1.0, "min_skor": BASE_MIN_SKOR, "notlar": []}


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    o = write_rejim()
    print("rejim.json yazildi")
    print(f"  DURUM: {o['durum']}  (trend: {o['trend']}, 30g {o.get('btc_30g_degisim_pct')}%)")
    print(f"  volatilite orani: {o['vol_orani']} (yuksek mi: {o['vol_yuksek']})")
    print(f"  korelasyon: {o['korelasyon']} (spike: {o['kor_spike']})")
    gk = gate_katkisi(o)
    print(f"  -> KAPI katkisi: {gk['kapi']} | boyut x{gk['carpan']} | min_skor {gk['min_skor']}")
    for n in gk["notlar"]:
        print("   -", n)


if __name__ == "__main__":
    main()
