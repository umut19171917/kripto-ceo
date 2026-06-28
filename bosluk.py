"""
bosluk.py — BOSLUK KURTARMA / geri-doldurma (PC kapali kaldigi araligi tamamlar)
================================================================================
PC acilinca izleyici bunu bir kez cagirir (tamamla()). signals.json'daki son
"updated_at"e bakip bosluk suresini bulur ve:

  A) ACIK tahminleri (beklemede/izleniyor) o aradaki GERCEK 1dk mumlariyla,
     kronolojik olarak tetik/TP/stop kontrol edip DOGRU sonuclandirir. (Kesin.)
  B) Bosluk araliginda kacirilan >=70 setuplari tarihsel veriden yeniden kurar,
     "geri-doldurma" etiketiyle deftere ekler ve mumlarla sonuclandirir.
     (YAKLASIK: funding 8s granul, likidasyon yok, makro atlanir -> ayri tutulur.)

A bolumu sicili korur; B bolumu ogrenme/backtest verisi ekler (etiketli).
"""

import json
from datetime import datetime, timezone, timedelta

import olcucu
import defter

MAX_BOSLUK_SAAT = 24    # en fazla son 24s geri doldur
ADIM_DK = 30            # B: tarama adimi
BACKFILL_COOLDOWN_SAAT = 2


def _now():
    return datetime.now(timezone.utc)


def _son_calisma():
    try:
        d = json.loads(olcucu.OUT_FILE.read_text(encoding="utf-8"))
        return datetime.fromisoformat(d["updated_at"])
    except Exception:
        return None


# ---- tarihsel veri yardimcilari ----
def _funding_hist(sym, limit=200):
    raw = olcucu._get("/fapi/v1/fundingRate", {"symbol": sym, "limit": limit})
    return [(int(x["fundingTime"]), float(x["fundingRate"])) for x in raw]


def _ls_hist(sym, limit=288):
    raw = olcucu._get("/futures/data/globalLongShortAccountRatio",
                      {"symbol": sym, "period": "5m", "limit": limit})
    return [(int(x["timestamp"]), float(x["longShortRatio"])) for x in raw]


def _nearest_le(pairs, t_ms):
    val = None
    for ts, v in pairs:
        if ts <= t_ms:
            val = v
        else:
            break
    return val


# ---- cekirdek: bir tahmini mumlarla ilerlet/sonuclandir ----
def coz(t, k1m):
    """t tahminini 1dk mumlariyla (kronolojik) ilerlet. t yerinde guncellenir. Doner: degisti_mi."""
    yon, giris, stop, tp1, tp2 = t["yon"], t["giris"], t["stop"], t["tp1"], t["tp2"]
    tarih = datetime.fromisoformat(t["tarih"])
    tetik = datetime.fromisoformat(t["tetik_tarih"]) if t.get("tetik_tarih") else None
    risk = abs(giris - stop)
    degisti = False

    for k in k1m:
        kt = datetime.fromtimestamp(k["t"] / 1000, timezone.utc)
        if kt < tarih:
            continue

        if t["durum"] == "beklemede":
            if tetik is None and (kt - tarih).total_seconds() / 3600 >= defter.PENDING_SAAT:
                t["durum"] = "tetiklenmedi"
                t["kapanis_tarih"] = kt.isoformat(timespec="seconds")
                return True
            triggered = (k["l"] <= giris) if yon == "SHORT" else (k["h"] >= giris)
            if triggered:
                t["durum"] = "izleniyor"
                t["tetik_tarih"] = kt.isoformat(timespec="seconds")
                tetik = kt
                degisti = True
            else:
                continue

        if t["durum"] == "izleniyor":
            if tetik and (kt - tetik).total_seconds() / 3600 >= defter.ACTIVE_SAAT:
                t["durum"] = "zaman_asimi"
                t["sonuc_fiyat"] = round(k["c"], 4)
                t["sonuc_R"] = 0.0
                t["kapanis_tarih"] = kt.isoformat(timespec="seconds")
                return True
            if yon == "SHORT":
                stop_hit, tp_hit = k["h"] >= stop, k["l"] <= tp1
            else:
                stop_hit, tp_hit = k["l"] <= stop, k["h"] >= tp1
            if stop_hit and tp_hit:
                sonuc = "stop"          # ayni mumda ikisi -> temkinli: stop
            elif tp_hit:
                if yon == "SHORT":
                    sonuc = "tp2" if k["l"] <= tp2 else "tp1"
                else:
                    sonuc = "tp2" if k["h"] >= tp2 else "tp1"
            elif stop_hit:
                sonuc = "stop"
            else:
                continue
            fiyat = stop if sonuc == "stop" else (tp2 if sonuc == "tp2" else tp1)
            R = ((giris - fiyat) if yon == "SHORT" else (fiyat - giris)) / risk if risk else None
            t["durum"] = sonuc
            t["sonuc_fiyat"] = round(fiyat, 4)
            t["sonuc_R"] = round(R, 2) if R is not None else None
            t["kapanis_tarih"] = kt.isoformat(timespec="seconds")
            return True
    return degisti


# ---- A: acik tahminleri coz ----
def _bolum_a(d, k1m_cache):
    n = 0
    for t in d["tahminler"]:
        if t["durum"] not in ("beklemede", "izleniyor"):
            continue
        k1m = k1m_cache.get(t["token"])
        if not k1m:
            continue
        if coz(t, k1m):
            n += 1
    return n


# ---- B: kacirilan setuplari yeniden kur ----
def _bolum_b(d, t0, t1, k5m_cache, k1m_cache):
    T = d["tahminler"]
    eklenen = 0
    son_backfill = {}
    adim = timedelta(minutes=ADIM_DK)
    for sym in olcucu.SYMBOLS:
        k5m = k5m_cache.get(sym)
        if not k5m or len(k5m) < 64:
            continue
        try:
            oi_pairs = [(x["t"], x["oi"]) for x in olcucu.get_oi_hist(sym, "5m", 288)]
            ls_pairs = _ls_hist(sym)
            fnd_pairs = _funding_hist(sym)
        except Exception:
            continue
        th = olcucu.get_thresholds(sym)
        T_cur = t0
        while T_cur <= t1:
            tms = int(T_cur.timestamp() * 1000)
            upto = [k for k in k5m if k["t"] <= tms]
            if len(upto) >= 64:
                price = upto[-1]["c"]
                a = olcucu.atr(upto)
                sh, sl = olcucu.swing_levels(upto)
                oi_now = _nearest_le(oi_pairs, tms)
                oi_ref = _nearest_le(oi_pairs, tms - 3_600_000)
                oi_1h = (oi_now - oi_ref) / oi_ref * 100 if (oi_now and oi_ref) else None
                lsr = _nearest_le(ls_pairs, tms)
                fnd = _nearest_le(fnd_pairs, tms)
                if a and lsr is not None and fnd is not None:
                    ss, lsq, _ = olcucu.squeeze_scores(price, fnd, oi_1h, lsr, sh, sl, th)
                    if max(ss, lsq) >= olcucu.SQUEEZE_FLAG:
                        plan = olcucu.trade_plan(price, a, sh, sl, ss, lsq)
                        sb = son_backfill.get(sym)
                        cooldown_ok = sb is None or (T_cur - sb).total_seconds() / 3600 >= BACKFILL_COOLDOWN_SAAT
                        if plan.get("gecerli") and cooldown_ok:
                            no = max([x.get("no", 0) for x in T], default=0) + 1
                            pred = {
                                "no": no, "tarih": T_cur.isoformat(timespec="seconds"),
                                "token": sym, "yon": plan["yon"],
                                "setup": "long_squeeze" if lsq >= ss else "short_squeeze",
                                "skor": max(ss, lsq), "giris": plan["giris"], "stop": plan["stop"],
                                "tp1": plan["tp1"], "tp2": plan["tp2"], "rr1": plan["rr1"],
                                "log_fiyat": price, "makro_kapi": "backfill-atlandi",
                                "kaynak": "geri-doldurma",
                                "durum": "beklemede", "tetik_tarih": None,
                                "sonuc_fiyat": None, "sonuc_R": None, "kapanis_tarih": None,
                            }
                            coz(pred, k1m_cache.get(sym, []))
                            T.append(pred)
                            son_backfill[sym] = T_cur
                            eklenen += 1
            T_cur += adim
    return eklenen


def tamamla(backfill=True):
    """PC acilista cagrilir. Bosluk varsa A (+B) calistirir. Ozet doner."""
    son = _son_calisma()
    now = _now()
    if son is None:
        return {"durum": "ilk-calisma"}
    bosluk = (now - son).total_seconds() / 3600
    if bosluk < 0.15:  # ~9dk altinda bosluk yok (normal snapshot araligi)
        return {"durum": "bosluk-yok", "bosluk_saat": round(bosluk, 2)}

    t0 = now - timedelta(hours=min(bosluk, MAX_BOSLUK_SAAT))
    gerekli_dk = int(min(bosluk, MAX_BOSLUK_SAAT) * 60) + 90
    d = defter._yukle()

    # 1dk + 5dk mum onbellegi (bir kez cek)
    k1m_cache, k5m_cache = {}, {}
    for sym in olcucu.SYMBOLS:
        try:
            k1m_cache[sym] = olcucu.get_klines(sym, "1m", min(1440, gerekli_dk))
            k5m_cache[sym] = olcucu.get_klines(sym, "5m", 300)
        except Exception:
            pass

    cozulen = _bolum_a(d, k1m_cache)
    eklenen = _bolum_b(d, t0, now, k5m_cache, k1m_cache) if backfill else 0

    defter._kaydet(d)
    return {"durum": "tamamlandi", "bosluk_saat": round(bosluk, 2),
            "cozulen_acik": cozulen, "geri_doldurulan": eklenen}


if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print("BOSLUK:", tamamla())
