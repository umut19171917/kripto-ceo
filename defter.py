"""
defter.py — Tahmin kaydi + sonuc takibi (kendi kendini gelistirme cekirdegi)
================================================================================
Her GECERLI plan (sikisma>=70, R/R ok, makro kapi != KAPALI) bir tahmin olarak
kripto-defter.json "tahminler"e yazilir; sonra sonucu takip edilir.

Durum akisi (durust takip):
  beklemede  -> fiyat giris'e ulasti mi?  evet -> izleniyor | sure dolarsa -> tetiklenmedi
  izleniyor  -> TP1/TP2 vuruldu (kazanc) | STOP (kayip) | sure dolarsa -> zaman_asimi

Boylece GIRMEDIGI islem kayip sayilmaz. R-multiple ile puanlanir (TP1 ~+2, stop -1).

TAKIP MEKANIGI (2026-07-02 revizyonu): tetik/TP/stop kontrolu 30sn'lik nokta
ornekleme ile DEGIL, KAPANMIS 1dk mumlarin high/low'u ile yapilir (coz()).
Gerekce: borsada bekleyen emir fiyat seviyeye bir tik degse dolar; nokta
ornekleme fitil dokunuslarini kacirir ve stop TP'den yakin oldugu icin sicili
sistematik IYIMSER kaydeder. Ayni coz() motorunu bosluk.py (geri-doldurma) da
kullanir -> canli ve bosluk TEK muhasebe. Sonuc fiyati = seviye (stop/tp);
kayma zaten net_R maliyet modelinde. Bilincli sinir: gercek stop-market dolumu
seviyeden kotu olabilir (gap); o asiri kisim sabit SLIPPAGE varsayiminda kalir.
"""

import os
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import olcucu  # log_line

try:
    import bildirim as _bildirim   # Telegram (C1); yoksa/bozuksa defter etkilenmez
except Exception:
    _bildirim = None


def _bildir(txt):
    """Telegram'a gonder (varsa). Bildirim hatasi defteri ASLA etkilemez."""
    if _bildirim:
        try:
            _bildirim.gonder(txt)
        except Exception:
            pass


DEFTER_FILE = Path(__file__).parent / "kripto-defter.json"
MAKRO_FILE = Path(__file__).parent / "makro.json"

# SWING-1H konfig sureleri (2026-07-02; backtest MAXBAR=120 bar ile uyumlu)
PENDING_SAAT = 24    # bu surede giris tetiklenmezse -> tetiklenmedi
ACTIVE_SAAT = 120    # bu surede TP/stop gelmezse -> zaman_asimi (~5 gun)
COOLDOWN_SAAT = 12   # ayni coine bu sure icinde yeni tahmin acma
KONFIG = "swing-1h"  # yeni kayitlarin etiketi -> 5m-donemi sicilinden ayrilir

# Risk tavani (kullanici karari 2026-07-02): AYNI YONDE eszamanli toplam risk
# portfoyun %2'sini gecemez. RISK_PCT=%1/islem -> ayni yonde en fazla 2 acik tahmin.
# "beklemede" de sayilir: bekleyen emir her an tetiklenebilir (bekleyen-emir semantigi).
RISK_TAVANI_PCT = 2.0

# 5m-donemi kayitlari (konfig etiketi YOK) kendi kurallariyla cozulur (durust sicil):
_ESKI_PENDING_SAAT, _ESKI_ACTIVE_SAAT = 6, 24


def _limitler(t):
    """Tahminin ait oldugu konfige gore (pending, active) saat limitleri."""
    if t.get("konfig") == KONFIG:
        return PENDING_SAAT, ACTIVE_SAAT
    return _ESKI_PENDING_SAAT, _ESKI_ACTIVE_SAAT

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
BNB_CARPAN = 0.90        # 2026-07-06: kullanici Futures'ta BNB ile fee odemeyi aktifletti (ek %10 indirim)
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


# --- Net/sozel mesaj formati (kullanici karari 2026-07-06) ---
# Telegram VE durum.py AYNI bu fonksiyonlari kullanir (tek kaynak, iki cikti sapmaz).
# Amac: piyasa bilgisi temel olan kullanici icin "al/sat/stop/hedef" jargonsuz net.


def _yon_sozel(yon):
    """(ongoru, islem, stop_yonu, tp_yonu) — SHORT: stop yukarida/tp asagida, LONG tersi."""
    if yon == "LONG":
        return "YUKSELECEGINI", "ALIS (long)", "inerse", "cikarsa"
    return "DUSECEGINI", "SATIS (short)", "cikarsa", "inerse"


def kaldirac_hesapla(giris, stop, risk_pct=None):
    """Ima edilen kaldirac (olcucu.trade_plan'daki ima_kaldirac ile AYNI formul).
    Saklanan alan DEGIL — giris/stop/risk_pct'ten her zaman yeniden hesaplanir,
    boylece eski kayitlarda (ima_kaldirac saklanmamis) da dogru gosterilir."""
    risk_pct = olcucu.RISK_PCT if risk_pct is None else risk_pct
    risk = abs(giris - stop)
    stop_pct = risk / giris * 100 if giris else None
    return round(risk_pct / stop_pct, 1) if stop_pct else None


def mesaj_sinyal(token, yon, giris, stop, tp1, tp2, rr1, risk_pct=None, skor=None,
                 kapi=None, price=None, deneysel=False, baslik_etiket="SINYAL"):
    """Net sozel sinyal metni. price/skor/kapi opsiyonel (kaydedilmis acik tahmin
    gosterilirken anlik fiyat/kapi bilinmeyebilir)."""
    risk_pct = olcucu.RISK_PCT if risk_pct is None else risk_pct
    ongoru, islem, stop_yon, tp_yon = _yon_sozel(yon)
    kald = kaldirac_hesapla(giris, stop, risk_pct)
    kald_s = f"~{kald}x" if kald else "belirsiz"
    baslik = f"[{baslik_etiket}] {token}" + (" (DENEYSEL - ana sicile girmez)" if deneysel else "")
    ust = f"Su anki fiyat: {price}\n\n" if price is not None else ""
    alt_parcalar = []
    if skor is not None:
        alt_parcalar.append(f"Guven skoru: {skor}/100")
    if kapi is not None:
        alt_parcalar.append(f"Piyasa kapisi: {kapi}")
    alt = (" | ".join(alt_parcalar) + "\n") if alt_parcalar else ""
    return (
        f"{baslik}\n{ust}"
        f"Sistem fiyatin {ongoru} ongoruyor.\n"
        f"Onerilen islem: {islem}\n"
        f"Kaldirac: {kald_s}\n\n"
        f"Giris fiyati: {giris}\n"
        f"Zarari-kes (stop): {stop} -> fiyat buraya {stop_yon} cik, kayip = portfoyun %{risk_pct:g}'i\n"
        f"Kar hedefi (TP1): {tp1} -> fiyat buraya {tp_yon} karinin bir kismini al (R/R {rr1})\n"
        f"Kar hedefi (TP2): {tp2}\n\n"
        f"{alt}"
        f"Emir SENDE - bu bir oneri, otomatik islem acilmaz."
    )


def mesaj_tetik(t):
    """[TETIKLENDI] fiyat giris seviyesine ulasti -> pozisyon 'acik' sayilir."""
    _, islem, stop_yon, tp_yon = _yon_sozel(t["yon"])
    return (
        f"[TETIKLENDI] {t['token']}\n"
        f"Giris fiyatina ({t['giris']}) ulasildi -> {islem} pozisyonu ACIK sayilir.\n\n"
        f"Zarari-kes (stop): {t['stop']} -> fiyat buraya {stop_yon} cik\n"
        f"Kar hedefi (TP1): {t['tp1']} -> fiyat buraya {tp_yon} karinin bir kismini al (R/R {t['rr1']})\n"
        f"Kar hedefi (TP2): {t['tp2']}\n\n"
        f"Emir SENDE - sistem sadece izliyor."
    )


def mesaj_sonuc(t):
    """[SONUC] TP/stop/zaman_asimi kapanisi - gross+net R ile."""
    baslik = {"tp1": "KAR (hedef 1'e ulasildi)", "tp2": "KAR (hedef 2'ye ulasildi)",
              "stop": "ZARAR (stop'a takildi)", "zaman_asimi": "SURE DOLDU (zaman asimi)"
              }.get(t["durum"], t["durum"].upper())
    satir = f"[SONUC] {t['token']} {t['yon']} -> {baslik}\nKapanis fiyati: {t.get('sonuc_fiyat')}"
    r = t.get("sonuc_R")
    if r is not None:
        nr = net_R(t)
        nr_s = f" (net: {nr:+.2f}R, komisyon dahil)" if nr is not None else ""
        satir += f"\nSonuc: {r:+.2f}R{nr_s}"
    return satir


def mesaj_gecersiz(t):
    """[GECERSIZ] fiyat giris seviyesine hic ulasmadi, sure doldu."""
    return (f"[GECERSIZ] {t['token']} {t['yon']}\n"
            f"Fiyat giris seviyesine ({t['giris']}) ulasmadi, sure doldu.\n"
            f"Bu sinyal artik gecerli degil, herhangi bir pozisyon acilmadi.")


def _yukle():
    try:
        d = json.loads(DEFTER_FILE.read_text(encoding="utf-8"))
        for k in ("pozisyonlar", "tahminler", "dersler"):
            d.setdefault(k, [])
        return d
    except Exception:
        return {"pozisyonlar": [], "tahminler": [], "dersler": []}


def _kaydet(d):
    """Atomik kayit: gecici dosyaya yaz + os.replace. Yarim JSON okunamaz."""
    tmp = DEFTER_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, DEFTER_FILE)


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


def rejim_damga():
    """Kayit ANINDAKI rejim baglami (makro.json piyasa_rejimi + min_skor) — salt damga,
    davranisi ETKILEMEZ. Amac (2026-07-14, K2 gundemi): 30 islem dolunca 'kayiplar
    OYNAK rejimde mi kumeleniyor' sorusuna kayit-bazli cevap verebilmek; damga
    olmadan gecmis kayitlarin rejimi geri kazanilamaz. radar_defter.kaydet de
    ayni fonksiyonu kullanir (tek kaynak). makro.json yok/bozuksa bos dict."""
    try:
        m = json.loads(MAKRO_FILE.read_text(encoding="utf-8"))
        pr = m.get("piyasa_rejimi") or {}
        return {"rejim_durum": pr.get("durum"),
                "korelasyon": pr.get("korelasyon"),
                "vol_orani": pr.get("vol_orani"),
                "etkin_min_skor": m.get("min_skor", 0)}
    except Exception:
        return {}


def _fiyat_yuvarla(x):
    """sonuc_fiyat hassasiyeti: en az 4 hane (eski davranis), mikro-fiyat coinlerde
    olcucu._p ile incelir (2026-07-16 AKE dersi: 0.001$ coinde 4 hane = %10 adim).
    sonuc_R yuvarlanmamis degerden hesaplanir, bu salt kayit/gosterim hassasiyeti."""
    try:
        return round(x, max(4, olcucu._p(x)))
    except Exception:
        return round(x, 4)


def k1m_kapanmis(sym, dk):
    """Son `dk` dakikanin KAPANMIS 1dk mumlari (halen olusan son mum atilir).
    Bekleyen-emir semantigi kapanmis mumun kesin high/low'unu ister; olusan
    mumu isleyip isaretlersek ayni dakikanin sonraki fitilleri kacar."""
    k = olcucu.get_klines(sym, "1m", min(1440, max(5, dk + 3)))
    simdi_ms = time.time() * 1000
    return [x for x in k if x["t"] + 60_000 <= simdi_ms]


def coz(t, k1m):
    """t tahminini kapanmis 1dk mumlarla KRONOLOJIK ilerlet (fitil-tabanli).
    t yerinde guncellenir; doner: durum degisti mi. Canli (guncelle) ve
    geri-doldurma (bosluk.py) ayni motoru kullanir.
      - Tetik/TP/stop: mum high/low (bekleyen emir bir tik degse dolar).
      - Ayni mumda hem stop hem TP -> temkinli: STOP sayilir.
      - zaman_asimi: R = son mumun kapanisiyla mark-to-market (0 varsaymak
        acik pozisyonun gercek sonucunu gizlerdi).
      - t["son_mum_ts"] = islenmis son mum -> tekrarli cagrilar idempotent;
        tetik ONCESI stop-ustu fitiller tetik SONRASI stop sayilmaz."""
    yon, giris, stop, tp1, tp2 = t["yon"], t["giris"], t["stop"], t["tp1"], t["tp2"]
    tarih = datetime.fromisoformat(t["tarih"])
    tetik = datetime.fromisoformat(t["tetik_tarih"]) if t.get("tetik_tarih") else None
    risk = abs(giris - stop)
    pend_saat, act_saat = _limitler(t)   # konfig-donemine gore sureler
    degisti = False

    for k in k1m:
        if k["t"] <= (t.get("son_mum_ts") or 0):
            continue
        kt = datetime.fromtimestamp(k["t"] / 1000, timezone.utc)
        if kt < tarih:
            continue
        t["son_mum_ts"] = k["t"]

        if t["durum"] == "beklemede":
            if tetik is None and (kt - tarih).total_seconds() / 3600 >= pend_saat:
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
            if tetik and (kt - tetik).total_seconds() / 3600 >= act_saat:
                R = ((giris - k["c"]) if yon == "SHORT" else (k["c"] - giris)) / risk if risk else None
                t["durum"] = "zaman_asimi"
                t["sonuc_fiyat"] = _fiyat_yuvarla(k["c"])
                t["sonuc_R"] = round(R, 2) if R is not None else None
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
            t["sonuc_fiyat"] = _fiyat_yuvarla(fiyat)
            t["sonuc_R"] = round(R, 2) if R is not None else None
            t["kapanis_tarih"] = kt.isoformat(timespec="seconds")
            return True
    return degisti


def _acik_tahmin(T, token):
    return any(t["token"] == token and t["durum"] in ("beklemede", "izleniyor") for t in T)


def acik_risk_pct(T, yon):
    """Ayni yondeki ACIK canli tahminlerin toplam riski (portfoy %'si).
    Geri-doldurma kayitlari sayilmaz (canli sicilden ayri). Eski kayitlarda
    risk_pct alani yok -> 1.0 (olusturulduklari donemin RISK_PCT degeri)."""
    return sum(t.get("risk_pct", 1.0) for t in T
               if t.get("kaynak", "canli") != "geri-doldurma"
               and t["durum"] in ("beklemede", "izleniyor") and t["yon"] == yon)


_tavan_log_ts = {}   # sym -> son log zamani; 30sn dongude ayni atlamayi tekrar tekrar loglama


def _tavan_logla(sym, yon, mevcut):
    simdi = time.time()
    if simdi - _tavan_log_ts.get(sym, 0) < 3600:
        return
    _tavan_log_ts[sym] = simdi
    olcucu.log_line(f"[DEFTER] {sym} {yon} atlandi: ayni-yon acik risk "
                    f"%{mevcut:.1f} + %{olcucu.RISK_PCT:.1f} > tavan %{RISK_TAVANI_PCT:.1f}")


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

    # --- 1) Acik tahminleri KAPANMIS 1dk mumlarla ilerlet (fitil-tabanli coz) ---
    acik = [t for t in T if t["durum"] in ("beklemede", "izleniyor")]
    for sym in sorted({t["token"] for t in acik}):
        grup = [t for t in acik if t["token"] == sym]
        eski = min((t.get("son_mum_ts") or int(datetime.fromisoformat(t["tarih"]).timestamp() * 1000))
                   for t in grup)
        dk = int((now.timestamp() * 1000 - eski) / 60_000) + 2
        try:
            k1m = k1m_kapanmis(sym, dk)
        except Exception as e:
            olcucu.log_line(f"[DEFTER] {sym} 1dk mum alinamadi ({type(e).__name__}) - bu tur atlandi")
            continue
        for t in grup:
            onceki_durum, onceki_ts = t["durum"], t.get("son_mum_ts")
            if coz(t, k1m) or t.get("son_mum_ts") != onceki_ts:
                degisti = True
            if t["durum"] != onceki_durum:
                if t["durum"] == "izleniyor":
                    olcucu.log_line(f"[DEFTER] #{t['no']} {t['token']} {t['yon']} TETIKLENDI @ {t['giris']}")
                    _bildir(mesaj_tetik(t))
                elif t["durum"] == "tetiklenmedi":
                    olcucu.log_line(f"[DEFTER] #{t['no']} {t['token']} tetiklenmedi (sure doldu)")
                    _bildir(mesaj_gecersiz(t))
                else:
                    olcucu.log_line(f"[DEFTER] #{t['no']} {t['token']} SONUC: {t['durum'].upper()} (R={t['sonuc_R']})")
                    _bildir(mesaj_sonuc(t))

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
            mevcut_risk = acik_risk_pct(T, p["yon"])
            if mevcut_risk + olcucu.RISK_PCT > RISK_TAVANI_PCT + 1e-9:
                _tavan_logla(sym, p["yon"], mevcut_risk)
                continue   # ayni-yon toplam risk tavani (korelasyonlu yigilma freni)
            no = max([t.get("no", 0) for t in T], default=0) + 1
            kayit = {
                "no": no, "tarih": now.isoformat(timespec="seconds"),
                "token": sym, "yon": p["yon"],
                "setup": "long_squeeze" if sq["long_squeeze"] >= sq["short_squeeze"] else "short_squeeze",
                "skor": max(sq["short_squeeze"], sq["long_squeeze"]),
                "giris": p["giris"], "stop": p["stop"], "tp1": p["tp1"], "tp2": p["tp2"],
                "rr1": p["rr1"], "log_fiyat": v["price"], "makro_kapi": kapi,
                "konfig": KONFIG, "risk_pct": olcucu.RISK_PCT,
                "durum": "beklemede", "tetik_tarih": None, "son_mum_ts": None,
                "sonuc_fiyat": None, "sonuc_R": None, "kapanis_tarih": None,
            }
            kayit.update(rejim_damga())
            if sym in getattr(olcucu, "DENEYSEL", set()):
                kayit["sicil"] = "deneysel"   # takip edilir ama K2/ana istatistige girmez
            T.append(kayit)
            olcucu.log_line(f"[DEFTER] YENI tahmin #{no} {sym} {p['yon']} giris {p['giris']} stop {p['stop']} tp1 {p['tp1']} (skor {max(sq['short_squeeze'], sq['long_squeeze'])})")
            deneysel = sym in getattr(olcucu, "DENEYSEL", set())
            _bildir(mesaj_sinyal(sym, p["yon"], p["giris"], p["stop"], p["tp1"], p["tp2"], p["rr1"],
                                risk_pct=olcucu.RISK_PCT, skor=kayit["skor"], kapi=kapi,
                                price=v["price"], deneysel=deneysel, baslik_etiket="YENI SINYAL"))
            degisti = True

    if degisti:
        _kaydet(d)
    return d


def ozet():
    """ANA sicil ozeti (K2 olcumu): geri-doldurma VE deneysel (LAB) kayitlar HARIC.
    (Duzeltme 2026-07-05: eski surum geri-doldurmayi da sayiyordu -> durum.py'nin
    'gercek/canli' ayrimiyla tutarsizdi.) Deneysel varsa ayri alt-ozet doner."""
    d = _yukle()
    tum = d["tahminler"]
    T = [t for t in tum if t.get("kaynak", "canli") != "geri-doldurma"
         and t.get("sicil") != "deneysel"]
    acik = [t for t in T if t["durum"] in ("beklemede", "izleniyor")]
    kapali = [t for t in T if t["durum"] in ("tp1", "tp2", "stop", "zaman_asimi")]
    kazanc = [t for t in kapali if t["durum"] in ("tp1", "tp2")]
    kayip = [t for t in kapali if t["durum"] == "stop"]
    girilmis = kazanc + kayip
    toplam_R = round(sum((t.get("sonuc_R") or 0) for t in kapali), 2)
    toplam_net_R = round(sum((net_R(t) or 0) for t in kapali), 2)
    isabet = round(len(kazanc) / len(girilmis) * 100, 1) if girilmis else None
    out = {"acik": len(acik), "kapali": len(kapali), "kazanc": len(kazanc),
           "kayip": len(kayip), "isabet_pct": isabet,
           "toplam_R": toplam_R, "toplam_net_R": toplam_net_R}
    dn = [t for t in tum if t.get("sicil") == "deneysel"]
    if dn:
        dn_kapali = [t for t in dn if t["durum"] in ("tp1", "tp2", "stop", "zaman_asimi")]
        out["deneysel"] = {"acik": len([t for t in dn if t["durum"] in ("beklemede", "izleniyor")]),
                           "kapali": len(dn_kapali),
                           "toplam_net_R": round(sum((net_R(t) or 0) for t in dn_kapali), 2)}
    return out


if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print("DEFTER OZET:", ozet())
