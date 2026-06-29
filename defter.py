"""
defter.py — Tahmin kaydi + sonuc takibi (kendi kendini gelistirme cekirdegi)
================================================================================
Her GECERLI plan (sikisma>=70, R/R ok, makro kapi != KAPALI) bir tahmin olarak
kripto-defter.json "tahminler"e yazilir; sonra sonucu takip edilir.

Durum akisi (durust takip):
  beklemede  -> fiyat giris'e ulasti mi?  evet -> izleniyor | sure dolarsa -> tetiklenmedi
  izleniyor  -> TP1/TP2 vuruldu (kazanc) | STOP (kayip) | sure dolarsa -> zaman_asimi

Boylece GIRMEDIGI islem kayip sayilmaz. R-multiple ile puanlanir (TP1 ~+2, stop -1).
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import olcucu  # log_line

DEFTER_FILE = Path(__file__).parent / "kripto-defter.json"
MAKRO_FILE = Path(__file__).parent / "makro.json"

PENDING_SAAT = 6     # bu surede giris tetiklenmezse -> tetiklenmedi
ACTIVE_SAAT = 24     # bu surede TP/stop gelmezse -> zaman_asimi
COOLDOWN_SAAT = 2    # ayni coine bu sure icinde yeni tahmin acma

# --- Komisyon + slippage modeli (KAYNAKLI) ---
# KAYNAK: Binance USDⓈ-M Futures fee tarifesi, VIP 0 / regular (2026):
#   maker %0.0200, taker %0.0500.  https://www.binance.com/en/fee/futureFee
#   BNB ile fee odenirse ek %10 indirim -> BNB_CARPAN = 0.90 yap.
# Emir-tipi VARSAYIMI (degistirilebilir): giris=taker (seviyeye gelince agresif market),
#   TP=maker (onceden konan limit), STOP=taker (stop-market). Slippage SADECE taker bacakta.
# net_R = gross sonuc_R - (giris * (giris_bacak + cikis_bacak)) / risk.  Trade mantigina KARISMAZ.
MAKER_FEE = 0.000200     # %0.0200
TAKER_FEE = 0.000500     # %0.0500
SLIPPAGE = 0.000200      # taker bacak basina tahmini kayma (~%0.02)
BNB_CARPAN = 1.0         # BNB ile fee odersen 0.90 (ek %10 indirim)
GIRIS_TAKER = True       # giris market/agresif mi? Limit(maker) ile giriyorsan False yap


def _bacak_maliyet(taker):
    """Tek bacak (giris veya cikis) maliyeti, fiyat orani. taker=True -> taker+slippage."""
    return (TAKER_FEE * BNB_CARPAN + SLIPPAGE) if taker else (MAKER_FEE * BNB_CARPAN)


def maliyet_R(t):
    """Komisyon+slippage maliyeti, R cinsinden. giris=GIRIS_TAKER, TP->maker, stop->taker."""
    try:
        risk = abs(t["giris"] - t["stop"])
        if risk <= 0:
            return 0.0
        giris_b = _bacak_maliyet(GIRIS_TAKER)
        cikis_b = _bacak_maliyet(t.get("durum") not in ("tp1", "tp2"))
        return t["giris"] * (giris_b + cikis_b) / risk
    except Exception:
        return 0.0


def net_R(t):
    """Komisyon dusulmus net R. Girilmemis (sonuc_R yok) -> None."""
    g = t.get("sonuc_R")
    if g is None:
        return None
    return round(g - maliyet_R(t), 2)


def _yukle():
    try:
        d = json.loads(DEFTER_FILE.read_text(encoding="utf-8"))
        for k in ("pozisyonlar", "tahminler", "dersler"):
            d.setdefault(k, [])
        return d
    except Exception:
        return {"pozisyonlar": [], "tahminler": [], "dersler": []}


def _kaydet(d):
    DEFTER_FILE.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


def _makro_kapi():
    try:
        return json.loads(MAKRO_FILE.read_text(encoding="utf-8")).get("kapi", "ACIK")
    except Exception:
        return "ACIK"


def _makro_min_skor():
    """Rejim katmaninin onerdigi min skor (makro.json). Yoksa 0 -> filtre yok (eski davranis)."""
    try:
        return json.loads(MAKRO_FILE.read_text(encoding="utf-8")).get("min_skor", 0)
    except Exception:
        return 0


def _acik_tahmin(T, token):
    return any(t["token"] == token and t["durum"] in ("beklemede", "izleniyor") for t in T)


def _son_tahmin_yasi(T, token, now):
    zlar = [datetime.fromisoformat(t["tarih"]) for t in T if t["token"] == token]
    return (now - max(zlar)).total_seconds() / 3600 if zlar else None


def guncelle(snapshot):
    """signals.json yapisini al -> acik tahminleri ilerlet/sonuclandir + yeni gecerli plan ekle."""
    d = _yukle()
    T = d["tahminler"]
    kapi = _makro_kapi()
    min_skor = _makro_min_skor()
    now = datetime.now(timezone.utc)
    degisti = False

    # --- 1) Acik tahminleri ilerlet/sonuclandir ---
    for t in T:
        if t["durum"] not in ("beklemede", "izleniyor"):
            continue
        v = snapshot["symbols"].get(t["token"], {})
        if "error" in v or "price" not in v:
            continue
        fiyat = v["price"]
        yas = (now - datetime.fromisoformat(t["tarih"])).total_seconds() / 3600

        if t["durum"] == "beklemede":
            tetik = (fiyat <= t["giris"]) if t["yon"] == "SHORT" else (fiyat >= t["giris"])
            if tetik:
                t["durum"] = "izleniyor"
                t["tetik_tarih"] = now.isoformat(timespec="seconds")
                olcucu.log_line(f"[DEFTER] #{t['no']} {t['token']} {t['yon']} TETIKLENDI @ {fiyat}")
                degisti = True
            elif yas >= PENDING_SAAT:
                t["durum"] = "tetiklenmedi"
                t["kapanis_tarih"] = now.isoformat(timespec="seconds")
                olcucu.log_line(f"[DEFTER] #{t['no']} {t['token']} tetiklenmedi (sure doldu)")
                degisti = True
            continue

        # izleniyor -> sonuc
        sonuc = None
        if t["yon"] == "SHORT":
            if fiyat <= t["tp1"]:
                sonuc = "tp2" if fiyat <= t["tp2"] else "tp1"
            elif fiyat >= t["stop"]:
                sonuc = "stop"
        else:
            if fiyat >= t["tp1"]:
                sonuc = "tp2" if fiyat >= t["tp2"] else "tp1"
            elif fiyat <= t["stop"]:
                sonuc = "stop"
        if sonuc is None and yas >= ACTIVE_SAAT:
            sonuc = "zaman_asimi"

        if sonuc:
            risk = abs(t["giris"] - t["stop"])
            R = ((t["giris"] - fiyat) if t["yon"] == "SHORT" else (fiyat - t["giris"])) / risk if risk else None
            t["durum"] = sonuc
            t["sonuc_fiyat"] = round(fiyat, 4)
            t["sonuc_R"] = round(R, 2) if R is not None else None
            t["kapanis_tarih"] = now.isoformat(timespec="seconds")
            olcucu.log_line(f"[DEFTER] #{t['no']} {t['token']} SONUC: {sonuc.upper()} (R={t['sonuc_R']})")
            degisti = True

    # --- 2) Yeni gecerli plan ekle ---
    if kapi != "KAPALI":
        for sym, v in snapshot["symbols"].items():
            if "error" in v:
                continue
            p = v.get("plan", {})
            if not (p.get("yon") and p.get("gecerli")):
                continue
            if _acik_tahmin(T, sym):
                continue
            yas = _son_tahmin_yasi(T, sym, now)
            if yas is not None and yas < COOLDOWN_SAAT:
                continue
            sq = v["squeeze"]
            if max(sq["short_squeeze"], sq["long_squeeze"]) < min_skor:
                continue   # rejim yuksek-vol/kontajyon -> sadece guclu setup'lara izin ver
            no = max([t.get("no", 0) for t in T], default=0) + 1
            T.append({
                "no": no, "tarih": now.isoformat(timespec="seconds"),
                "token": sym, "yon": p["yon"],
                "setup": "long_squeeze" if sq["long_squeeze"] >= sq["short_squeeze"] else "short_squeeze",
                "skor": max(sq["short_squeeze"], sq["long_squeeze"]),
                "giris": p["giris"], "stop": p["stop"], "tp1": p["tp1"], "tp2": p["tp2"],
                "rr1": p["rr1"], "log_fiyat": v["price"], "makro_kapi": kapi,
                "durum": "beklemede", "tetik_tarih": None,
                "sonuc_fiyat": None, "sonuc_R": None, "kapanis_tarih": None,
            })
            olcucu.log_line(f"[DEFTER] YENI tahmin #{no} {sym} {p['yon']} giris {p['giris']} stop {p['stop']} tp1 {p['tp1']} (skor {max(sq['short_squeeze'], sq['long_squeeze'])})")
            degisti = True

    if degisti:
        _kaydet(d)
    return d


def ozet():
    d = _yukle()
    T = d["tahminler"]
    acik = [t for t in T if t["durum"] in ("beklemede", "izleniyor")]
    kapali = [t for t in T if t["durum"] in ("tp1", "tp2", "stop", "zaman_asimi")]
    kazanc = [t for t in kapali if t["durum"] in ("tp1", "tp2")]
    kayip = [t for t in kapali if t["durum"] == "stop"]
    girilmis = kazanc + kayip
    toplam_R = round(sum((t.get("sonuc_R") or 0) for t in kapali), 2)
    toplam_net_R = round(sum((net_R(t) or 0) for t in kapali), 2)
    isabet = round(len(kazanc) / len(girilmis) * 100, 1) if girilmis else None
    return {"acik": len(acik), "kapali": len(kapali), "kazanc": len(kazanc),
            "kayip": len(kayip), "isabet_pct": isabet,
            "toplam_R": toplam_R, "toplam_net_R": toplam_net_R}


if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print("DEFTER OZET:", ozet())
