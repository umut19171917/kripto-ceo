"""
pozisyon.py — KAGIT ISLEM BOTUNUN CEKIRDEGI: pozisyon nesnesi + simulator
================================================================================
TASARIM-BOT.md §2 karari: sifirdan kurulmuyor, `defter.py` de revize edilmiyor.
`defter.py`'nin cekirdek nesnesi bir TAHMIN, bunun cekirdek nesnesi bir POZISYON.
Tahmin "fiyat nereye gider" der ve R-kati ile puanlanir; pozisyonun miktari,
teminati, kaldiraci, funding borcu ve likidasyon fiyati vardir ve USD ile olculur.

⛔ `defter.py` ve `radar_defter.py` DEGISTIRILMEZ (kosan `radar-v2` on kaydi
   gecersiz olur — ON-KAYIT-radar-v2.md §6). Bu modul onlari yalnizca IMPORT eder.

--------------------------------------------------------------------------------
IMPORT EDILEN (kopyalanmadi — tek kaynak korunuyor)
--------------------------------------------------------------------------------
  defter.coz          : COZME MOTORU. Kapanmis 1dk mum, fitil semantigi, ayni
                        mumda stop+TP -> temkinli STOP, son_mum_ts ile idempotans,
                        zaman_asimi'nda mark-to-market. Bu mantik aylarca duzeltildi;
                        yeniden yazmak TASARIM-BOT §2'ye gore "bu projenin
                        yapabilecegi en pahali hata".
  defter.MAKER_FEE / TAKER_FEE / SLIPPAGE / BNB_CARPAN / GIRIS_TAKER
                      : vadeli maliyet modeli (Binance USDⓈ-M, VIP0, kaynakli).
  defter.RISK_TAVANI_PCT : ayni-yon toplam risk tavani.
  olcucu._get / get_klines / atomik_yaz / _p : veri ve I/O altyapisi.

--------------------------------------------------------------------------------
STRATEJIDEN BAGIMSIZ (TASARIM-BOT §8 karari = (c), 2026-08-23)
--------------------------------------------------------------------------------
Bu modul "hangi sinyal" bilmez. Yalnizca su zinciri modeller:
    emir gelir -> pozisyon acilir -> maliyet/funding isler -> kapanir.
Strateji secimi kosan `radar-v2` on kaydina birakildi; simdi bir strateji
gommek (ornegin "yalniz LONG") testi onden yemek olurdu.

KISMI CIKIS da bu yuzden MEKANIZMA olarak var, POLITIKA olarak yok:
`kismi_kapat()` cagirilabilir, ama "TP1'de yariyi al" gibi bir kural buraya
YAZILMAZ — o bir stratejidir ve `strateji/` katmanina aittir.

--------------------------------------------------------------------------------
⚠ BILINEN IYIMSERLIKLER (simulator yalan soylememeli — TASARIM-BOT §5)
--------------------------------------------------------------------------------
1. GAP/KAYMA (bekleyenler defteri E1) OLCULMEDI. `defter.coz` stop'u tam
   seviyeden doldurur; gercek stop-market dolumu bosluklu piyasada seviyeden
   KOTU olur. Asiri kisim sabit SLIPPAGE varsayiminda kalir.
   -> `uyarilar()` bunu her pozisyonda ISIMLE bildirir. Sessiz gecilmez.
2. MMR (surdurme teminat orani) tahmindir; kesin degerler Binance
   /fapi/v1/leverageBracket (imzali endpoint) ister. Varsayilan MUHAFAZAKAR
   (likidasyon fiyatini girise YAKLASTIRIR) — bkz. MMR_VARSAYILAN.
3. Funding, gercek odeme anlarindan (/fapi/v1/fundingRate) alinir ama notional
   o andaki 1dk mum KAPANISI ile hesaplanir; Binance mark price kullanir.
4. Spot komisyonu KULLANICI HESABINDA DOGRULANMADI (bkz. SPOT_BNB_CARPAN).

Calistirma: venv\\Scripts\\python.exe pozisyon.py   -> kendi testini kosar
Canliya DOKUNMAZ; kendi defteri `bot-defter.json`.
"""
import json
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

KOK = Path(__file__).parent
sys.path.insert(0, str(KOK))
import defter
import olcucu

BOT_DEFTER = KOK / "bot-defter.json"

KAPALI_DURUMLAR = ("tp1", "tp2", "stop", "zaman_asimi", "likidasyon", "iptal")
ACIK_DURUMLAR = ("beklemede", "izleniyor")

# --- SPOT komisyon modeli ---
# KAYNAK: Binance Spot Trading Fee, Regular User / VIP 0 = %0.1000 maker ve taker.
#   https://www.binance.com/en/fee/schedule
# BNB ile odeme spot'ta %25 indirim verir. 2026-08-23: KULLANICI TEYIT ETTI —
#   spot'ta da BNB odemesi ACIK -> SPOT_BNB_CARPAN = 0.75.
#   (Futures tarafi defter.BNB_CARPAN = 0.90 ile zaten modelli, 2026-07-06.)
SPOT_FEE = 0.001000
SPOT_BNB_CARPAN = 0.75

# Vadeli tarafta defter.py'nin modeli AYNEN kullanilir (import, kopya degil).
# Spot taker (%0.100) vadeli taker'in (%0.045 BNB'li) ~2,2 KATI -> piyasa secimi
# maliyet acisindan notrdur SANILMAMALI. TASARIM-BOT §5 bunu ayri tutmayi sart kosar.

# --- Likidasyon: surdurme teminat orani (MMR) ---
# Binance kademeli (tier) MMR uygular; kucuk notional'da majorlerde ~%0.4,
# altcoinlerde ~%1.0 ve uzeri. Kesin deger imzali endpoint ister (yok).
# MUHAFAZAKAR SECIM: %1.0 -> likidasyon fiyati girise DAHA YAKIN cikar, yani
# simulator kendini fazla guvende gostermez. Sembol bazinda ezilebilir.
MMR_VARSAYILAN = 0.010
MMR_SEMBOL = {}

VARSAYILAN_BAKIYE = 1000.0
VARSAYILAN_RISK_PCT = 1.0


# ==============================================================================
#  MALIYET
# ==============================================================================
def bacak_maliyet_orani(piyasa, taker):
    """Tek bacagin (giris veya cikis) maliyeti, FIYAT ORANI olarak.

    Vadeli: defter.py'nin modeli aynen (taker+slippage / maker).
    Spot  : maker=taker=%0.1 (VIP0); slippage yine taker bacakta.
    """
    if piyasa == "spot":
        temel = SPOT_FEE * SPOT_BNB_CARPAN
        return temel + (defter.SLIPPAGE if taker else 0.0)
    return defter._bacak_maliyet(taker)


def komisyon_usd(notional, piyasa, taker):
    """Tek bacagin USD maliyeti."""
    return abs(notional) * bacak_maliyet_orani(piyasa, taker)


# ==============================================================================
#  LIKIDASYON
# ==============================================================================
def mmr(sembol):
    return MMR_SEMBOL.get(sembol, MMR_VARSAYILAN)


def likidasyon_fiyati(giris, yon, kaldirac, mmr_oran, teminat_orani=None):
    """Izole marjin likidasyon fiyati.

    TUREV (baslangic teminati = notional/kaldirac):
        teminat - zarar = surdurme_teminati
        notional*m - notional*D/giris = notional*mmr        (m = teminat/notional)
        D/giris = m - mmr
      LONG : liq = giris * (1 - m + mmr)
      SHORT: liq = giris * (1 + m - mmr)

    `teminat_orani` verilirse m = teminat_orani (odenen funding teminati
    eritince likidasyon girise YAKLASIR — o etkiyi modellemek icin).
    Verilmezse m = 1/kaldirac.

    Spot'ta likidasyon YOKTUR (borc yok) -> None doner.
    """
    if yon == "SPOT" or kaldirac is None or kaldirac <= 0:
        return None
    m = teminat_orani if teminat_orani is not None else (1.0 / kaldirac)
    mesafe = m - mmr_oran
    if mesafe <= 0:
        # Teminat zaten surdurme esiginin altinda -> aninda likidasyon.
        return giris
    return giris * (1 - mesafe) if yon == "LONG" else giris * (1 + mesafe)


# ==============================================================================
#  BOYUTLANDIRMA
# ==============================================================================
def boyutlandir(bakiye, risk_pct, giris, stop, kaldirac=1.0, piyasa="vadeli"):
    """Risk-tabanli boyutlandirma.

    ⚠ ANLASILMASI ONEMLI (kullanici notu): kaldirac, stop'a UYULDUGU surece
    riski DEGISTIRMEZ. Riski belirleyen sey stop mesafesidir:
        miktar = risk_usd / |giris - stop|
    Kaldirac yalnizca (a) ne kadar TEMINAT bagladigini ve (b) likidasyonun
    ne kadar YAKIN oldugunu degistirir. 10x kaldirac "10 kat risk" demek
    degildir; "ayni risk, 1/10 teminat, cok daha yakin likidasyon" demektir.
    Tehlike, kaldirac likidasyonu stop'un ICINE soktugunda baslar — o noktada
    stop artik korumaz. `uyarilar()` tam bunu kontrol eder.
    """
    risk_birim = abs(giris - stop)
    if risk_birim <= 0:
        raise ValueError("giris ile stop ayni fiyat olamaz (risk birimi 0)")
    risk_usd = bakiye * (risk_pct / 100.0)
    miktar = risk_usd / risk_birim
    notional = miktar * giris
    kald = 1.0 if piyasa == "spot" else float(kaldirac)
    teminat = notional / kald
    return {
        "miktar": miktar,
        "notional": notional,
        "teminat": teminat,
        "risk_usd": risk_usd,
        "risk_birim": risk_birim,
        "kaldirac": kald,
    }


# ==============================================================================
#  POZISYON
# ==============================================================================
def yeni(sembol, yon, giris, stop, tp1, tp2, *, piyasa="vadeli", kaldirac=1.0,
         bakiye=VARSAYILAN_BAKIYE, risk_pct=VARSAYILAN_RISK_PCT, tarih=None,
         strateji="(belirlenmedi)", no=None, notlar=None):
    """Yeni pozisyon dict'i uretir (henuz tetiklenmemis: durum=beklemede).

    ⚠ ANAHTAR ISIMLERI KASITLI: `yon/giris/stop/tp1/tp2/tarih/tetik_tarih/durum/
    son_mum_ts/sonuc_fiyat/sonuc_R/kapanis_tarih/konfig` alanlari defter.coz()'un
    bekledigi semanin AYNISIDIR. Boylece pozisyon dict'i coz()'a DOGRUDAN
    verilebilir; arada ceviri katmani yoktur -> ceviri hatasi riski de yoktur.

    ⚠ `konfig` neden defter.KONFIG'e sabitli: defter._limitler() konfig etiketi
    "swing-1h" DEGILSE 5dk-doneminin ESKI limitlerine (6s/24s) duser. Botun kendi
    zaman politikasi istenirse bu alan DEGISTIRILEREK yapilmaz — sessizce yanlis
    limitler secilir. Botun kendi etiketi ayri alanda: `strateji`.
    """
    if piyasa == "spot" and yon != "LONG":
        raise ValueError("spot'ta SHORT yok (borclanma modellenmiyor) — vadeli kullan")
    if yon not in ("LONG", "SHORT"):
        raise ValueError("yon LONG veya SHORT olmali")
    b = boyutlandir(bakiye, risk_pct, giris, stop, kaldirac, piyasa)
    t = (tarih or datetime.now(timezone.utc)).isoformat(timespec="seconds") \
        if not isinstance(tarih, str) else tarih
    p = {
        # --- defter.coz() semasi (AYNEN) ---
        "yon": yon, "giris": giris, "stop": stop, "tp1": tp1, "tp2": tp2,
        "tarih": t, "tetik_tarih": None, "durum": "beklemede",
        "son_mum_ts": None, "sonuc_fiyat": None, "sonuc_R": None,
        "kapanis_tarih": None, "konfig": defter.KONFIG,
        # --- pozisyona OZGU ---
        "no": no, "sembol": sembol, "piyasa": piyasa,
        "kaldirac": b["kaldirac"], "miktar": b["miktar"],
        "miktar_ilk": b["miktar"], "notional": b["notional"],
        "teminat": b["teminat"], "risk_usd": b["risk_usd"],
        "risk_birim": b["risk_birim"], "risk_pct": risk_pct,
        "bakiye_acilista": bakiye,
        "likidasyon_fiyati": likidasyon_fiyati(giris, yon, b["kaldirac"], mmr(sembol)),
        "mmr": mmr(sembol),
        "kismi_cikislar": [], "funding_odemeleri": [],
        "funding_toplam_usd": 0.0, "komisyon_usd": 0.0, "komisyon_R": None,
        "gerceklesen_usd": 0.0,
        "pnl_brut_usd": None, "pnl_net_usd": None, "pnl_R": None,
        "strateji": strateji, "defter": "bot", "notlar": notlar or [],
    }
    return p


def uyarilar(p):
    """Pozisyonun YAPISAL tehlikeleri. Bos liste = temiz. Panel bunu gostermeli."""
    u = []
    liq = p.get("likidasyon_fiyati")
    if liq is not None:
        stop_mesafe = abs(p["giris"] - p["stop"])
        liq_mesafe = abs(p["giris"] - liq)
        if liq_mesafe <= stop_mesafe:
            u.append(
                f"LIKIDASYON STOP'UN ICINDE: liq {liq:.6g} stop'tan ({p['stop']:.6g}) "
                f"once gelir. Bu kaldiracta ({p['kaldirac']:g}x) stop KORUMAZ — "
                f"kayip 1R degil, TEMINATIN TAMAMI olur."
            )
        elif liq_mesafe < stop_mesafe * 2:
            u.append(
                f"likidasyon stop'a yakin: liq mesafesi stop'un "
                f"{liq_mesafe / stop_mesafe:.2f} kati. Bosluk (gap) halinde stop "
                f"atlanip likidasyona gidilebilir."
            )
    if p["piyasa"] == "vadeli":
        u.append("GAP/KAYMA MODELLENMEDI (E1): stop tam seviyeden dolduruldu "
                 "varsayiliyor; calkantida gercek dolum daha kotu olur.")
    if p["piyasa"] == "spot" and SPOT_BNB_CARPAN == 1.00:
        u.append("spot komisyonu %0.1 (BNB indirimi YOK) varsayildi — hesapta "
                 "BNB odemesi aciksa maliyet abartiliyor.")
    return u


# ==============================================================================
#  FUNDING
# ==============================================================================
def funding_gecmisi(sembol, limit=1000):
    """Gercek funding ODEME ANLARI ve oranlari: [(t_ms, oran), ...].

    /fapi/v1/fundingRate gercek odeme zamanlarini dondurur -> 8 saatlik ritim
    VARSAYILMAZ (bazi sembollerde 4 saat). bosluk.py ile ayni endpoint.
    """
    raw = olcucu._get("/fapi/v1/fundingRate", {"symbol": sembol, "limit": limit})
    return sorted((int(x["fundingTime"]), float(x["fundingRate"])) for x in raw)


def _fiyat_at(k1m, t_ms):
    """t_ms aninda ya da hemen oncesinde kapanmis 1dk mumun kapanisi."""
    fiyat = None
    for k in k1m:
        if k["t"] <= t_ms:
            fiyat = k["c"]
        else:
            break
    return fiyat


def funding_uygula(p, olaylar, k1m=None):
    """Pozisyon ACIKKEN denk gelen funding odemelerini isler.

    ISARET: oran>0 iken LONG ODER, SHORT ALIR.
        tutar = -yon_isareti * notional * oran
    Notional o andaki fiyattan hesaplanir (mum kapanisi; Binance mark price
    kullanir — yaklasiklik burada, bkz. modul basligi §3).

    Idempotent: ayni odeme anini iki kez islemez.
    """
    if p["piyasa"] != "vadeli" or not p.get("tetik_tarih"):
        return 0.0
    t0 = int(datetime.fromisoformat(p["tetik_tarih"]).timestamp() * 1000)
    t1 = int(datetime.fromisoformat(p["kapanis_tarih"]).timestamp() * 1000) \
        if p.get("kapanis_tarih") else int(time.time() * 1000)
    islenmis = {o["t"] for o in p["funding_odemeleri"]}
    isaret = 1 if p["yon"] == "LONG" else -1
    eklenen = 0.0
    for t_ms, oran in olaylar:
        if t_ms < t0 or t_ms > t1 or t_ms in islenmis:
            continue
        fiyat = (_fiyat_at(k1m, t_ms) if k1m else None) or p["giris"]
        notional = p["miktar"] * fiyat
        tutar = -isaret * notional * oran
        p["funding_odemeleri"].append({
            "t": t_ms,
            "zaman": datetime.fromtimestamp(t_ms / 1000, timezone.utc).isoformat(timespec="seconds"),
            "oran": oran, "fiyat": fiyat, "notional": round(notional, 2),
            "tutar_usd": round(tutar, 4),
        })
        eklenen += tutar
    if eklenen:
        p["funding_toplam_usd"] = round(p["funding_toplam_usd"] + eklenen, 4)
        _likidasyon_tazele(p)
    return eklenen


def _likidasyon_tazele(p):
    """Odenen funding teminati eritir -> likidasyon girise yaklasir."""
    if p["piyasa"] != "vadeli" or not p["notional"]:
        return
    teminat_kalan = p["teminat"] + p["funding_toplam_usd"]
    p["likidasyon_fiyati"] = likidasyon_fiyati(
        p["giris"], p["yon"], p["kaldirac"], p["mmr"],
        teminat_orani=teminat_kalan / p["notional"],
    )


# ==============================================================================
#  KISMI CIKIS (MEKANIZMA — politika degil, bkz. modul basligi)
# ==============================================================================
def kismi_kapat(p, oran, fiyat, tarih=None, taker=True):
    """Pozisyonun `oran` kadarini (0-1) `fiyat`tan kapatir.

    Kalan miktar, teminat ve notional orantili kucultulur; izole marjinde
    orantili kapatis likidasyon fiyatini DEGISTIRMEZ (teminat/notional sabit).
    """
    if p["durum"] != "izleniyor":
        raise ValueError("yalnizca izlenen (tetiklenmis) pozisyon kismi kapatilir")
    if not 0 < oran < 1:
        raise ValueError("oran 0 ile 1 arasinda olmali (1 = tam kapanis, coz() halleder)")
    kapanan = p["miktar"] * oran
    isaret = 1 if p["yon"] == "LONG" else -1
    brut = isaret * (fiyat - p["giris"]) * kapanan
    kom = komisyon_usd(kapanan * fiyat, p["piyasa"], taker)
    p["kismi_cikislar"].append({
        "tarih": (tarih or datetime.now(timezone.utc)).isoformat(timespec="seconds")
                 if not isinstance(tarih, str) else tarih,
        "oran": oran, "fiyat": fiyat, "miktar": kapanan,
        "brut_usd": round(brut, 4), "komisyon_usd": round(kom, 4),
        "net_usd": round(brut - kom, 4),
    })
    p["miktar"] -= kapanan
    p["notional"] = p["miktar"] * p["giris"]
    p["teminat"] = p["notional"] / p["kaldirac"] if p["kaldirac"] else p["notional"]
    p["komisyon_usd"] = round(p["komisyon_usd"] + kom, 4)
    p["gerceklesen_usd"] = round(p["gerceklesen_usd"] + brut - kom, 4)
    return brut - kom


# ==============================================================================
#  COZUM — defter.coz() + likidasyon + funding
# ==============================================================================
def _likidasyon_tarama(p, k1m):
    """Likidasyonun deldigi ILK mumu bulur -> (mum, fiyat) veya None.

    AYNI MUMDA STOP + LIKIDASYON KURALI (defter.coz'un kuralinin ayni-taraf hali):
      defter.coz'da "ayni mumda stop+TP -> STOP" kurali vardir cunku stop ve TP
      girisin ZIT taraflarindadir ve mum ici yol BELIRSIZDIR. Stop ile likidasyon
      ise AYNI taraftadir; surekli bir fiyat yolunda girise YAKIN olana once
      degilir. Yani yol belirsiz DEGILDIR:
        - stop likidasyondan yakinsa -> once STOP dolar (likidasyon olmaz)
        - likidasyon stop'tan yakinsa -> once LIKIDASYON olur
      Bu yuzden likidasyon, ancak kaldirac onu stop'un ICINE soktugunda gerceklesir.
      ⚠ Bu, gap olmadigi varsayimidir (E1) — `uyarilar()` bunu bildirir.
    """
    liq = p.get("likidasyon_fiyati")
    if liq is None or p["piyasa"] != "vadeli" or not p.get("tetik_tarih"):
        return None
    if abs(p["giris"] - liq) >= abs(p["giris"] - p["stop"]):
        return None                      # stop daha yakin -> likidasyon erisilmez
    tetik = datetime.fromisoformat(p["tetik_tarih"])
    for k in k1m:
        kt = datetime.fromtimestamp(k["t"] / 1000, timezone.utc)
        if kt < tetik:
            continue
        delindi = (k["l"] <= liq) if p["yon"] == "LONG" else (k["h"] >= liq)
        if delindi:
            return k, liq
    return None


def coz(p, k1m, funding_olaylari=None, *, likidasyon=True, defter_uyumlu=False):
    """Pozisyonu kapanmis 1dk mumlarla ilerletir. Doner: durum degisti mi.

    SIRA:
      1) defter.coz() — tetik / TP / stop / zaman_asimi (ODUNC ALINAN MOTOR)
      2) likidasyon taramasi — coz'un buldugu kapanistan ONCE mi oldu?
      3) funding — acik kalinan sure boyunca
      4) USD muhasebesi

    `likidasyon=False` + `funding_olaylari=None` + `defter_uyumlu=True`
    -> DOGRULAMA MODU: sonuc, `defter.net_R()` ile BIREBIR ayni olmali.
       `pozisyon_dogrulama.py` bunu 211 gecmis islemde kosar (kullanici kurali 3).
    """
    onceki = p["durum"]
    degisti = defter.coz(p, k1m)

    lik = _likidasyon_tarama(p, k1m) if likidasyon else None
    if lik:
        mum, liq_fiyat = lik
        kapanis_ts = None
        if p["durum"] in KAPALI_DURUMLAR and p.get("kapanis_tarih"):
            kapanis_ts = datetime.fromisoformat(p["kapanis_tarih"]).timestamp() * 1000
        if kapanis_ts is None or mum["t"] <= kapanis_ts:
            kt = datetime.fromtimestamp(mum["t"] / 1000, timezone.utc)
            p["durum"] = "likidasyon"
            p["sonuc_fiyat"] = defter._fiyat_yuvarla(liq_fiyat)
            p["sonuc_R"] = round(
                ((p["giris"] - liq_fiyat) if p["yon"] == "SHORT" else (liq_fiyat - p["giris"]))
                / p["risk_birim"], 2)
            p["kapanis_tarih"] = kt.isoformat(timespec="seconds")
            degisti = True

    if funding_olaylari:
        funding_uygula(p, funding_olaylari, k1m)

    if p["durum"] != onceki:
        degisti = True
    if p["durum"] in KAPALI_DURUMLAR:
        muhasebe(p, defter_uyumlu=defter_uyumlu)
    return degisti


def muhasebe(p, defter_uyumlu=False):
    """USD muhasebesini kapatir: brut PnL, komisyon, funding, net, net-R.

    net_usd = gerceklesen(kismi) + kalan_brut - giris_komisyonu - cikis_komisyonu
              + funding_toplam   (funding isareti zaten dogru: odeme negatif)

    `defter_uyumlu=True`: CIKIS komisyonu da GIRIS notional'i uzerinden hesaplanir.
      Gerekce: defter.maliyet_R() `giris * (giris_bacak + cikis_bacak) / risk`
      formulunu kullanir — yani iki bacagi da GIRIS fiyatindan olcer. Gerceginde
      cikis komisyonu CIKIS notional'i uzerinden odenir; varsayilan (False) bu
      yuzden daha dogrudur. Bu bayrak yalnizca DOGRULAMA icindir: eski sicille
      birebir kiyaslama yapilabilsin diye defter'in yaklasikligini taklit eder.
      Iki yontemin farki `pozisyon_dogrulama.py`'de olculur ve raporlanir.
    """
    if p["durum"] == "tetiklenmedi" or not p.get("tetik_tarih"):
        p["pnl_brut_usd"] = p["pnl_net_usd"] = p["pnl_R"] = 0.0
        p["komisyon_usd"] = p["komisyon_R"] = 0.0
        return p
    cikis = p.get("sonuc_fiyat")
    isaret = 1 if p["yon"] == "LONG" else -1

    # ⚠ YUVARLAMA DISIPLINI: butun ara hesap TAM HASSASIYETTE yapilir; yuvarlama
    # YALNIZ saklanan/gosterilen alanlara uygulanir. Onceki surumde komisyon 4
    # haneye yuvarlanip R ONDAN turetiliyordu; bu, 211 gecmis islemin 29'unda
    # net-R'yi 0,01R kaydiriyordu (2026-08-23 dogrulamasinda yakalandi).
    if defter_uyumlu and p.get("sonuc_R") is not None:
        # defter.net_R() brut olarak ZATEN YUVARLANMIS sonuc_R'yi kullanir.
        # Birebir kiyas icin ayni girdi kullanilmali.
        kalan_brut = p["sonuc_R"] * p["risk_usd"]
    else:
        kalan_brut = isaret * ((cikis - p["giris"]) * p["miktar"]) if cikis is not None else 0.0

    giris_kom = komisyon_usd(p["miktar_ilk"] * p["giris"], p["piyasa"], defter.GIRIS_TAKER)
    cikis_taker = p["durum"] not in ("tp1", "tp2")      # TP = onceden konan limit (maker)
    cikis_fiyat = p["giris"] if defter_uyumlu else (cikis or p["giris"])
    cikis_kom = komisyon_usd(abs(p["miktar"] * cikis_fiyat), p["piyasa"], cikis_taker)
    kismi_kom = sum(k["komisyon_usd"] for k in p["kismi_cikislar"])
    kismi_brut = sum(k["brut_usd"] for k in p["kismi_cikislar"])

    kom_ham = giris_kom + cikis_kom + kismi_kom
    brut_ham = kalan_brut + kismi_brut
    net_ham = brut_ham - kom_ham + p["funding_toplam_usd"]

    if p["durum"] == "likidasyon":
        # Likidasyonda teminatin tamami gider; PnL bundan daha kotu olamaz.
        net_ham = max(net_ham, -(p["teminat"] + kom_ham))

    p["komisyon_usd"] = round(kom_ham, 4)
    p["komisyon_R"] = kom_ham / p["risk_usd"] if p["risk_usd"] else None
    p["pnl_brut_usd"] = round(brut_ham, 4)
    p["pnl_net_usd"] = round(net_ham, 4)
    p["pnl_R"] = round(net_ham / p["risk_usd"], 4) if p["risk_usd"] else None
    return p


def mark_to_market(p, fiyat):
    """Acik pozisyonun ANLIK (gerceklesmemis) durumu — panel icin."""
    if p["durum"] != "izleniyor":
        return {"acik": False}
    isaret = 1 if p["yon"] == "LONG" else -1
    brut = isaret * (fiyat - p["giris"]) * p["miktar"]
    net = brut + p["funding_toplam_usd"] - komisyon_usd(p["miktar_ilk"] * p["giris"],
                                                        p["piyasa"], defter.GIRIS_TAKER)
    liq = p.get("likidasyon_fiyati")
    return {
        "acik": True, "fiyat": fiyat,
        "brut_usd": round(brut, 4), "net_usd": round(net, 4),
        "R": round(net / p["risk_usd"], 3) if p["risk_usd"] else None,
        "funding_usd": p["funding_toplam_usd"],
        "likidasyona_uzaklik_pct": round(abs(fiyat - liq) / fiyat * 100, 2) if liq else None,
    }


# ==============================================================================
#  PORTFOY
# ==============================================================================
def mutabakat(kapali, tolerans=0.01):
    """🔴 MUTABAKAT DENKLEMI (madde 7.5) — bir P&L toplami basilmadan ONCE kosar.

        Σ net = Σ brut − Σ komisyon + Σ funding

    Dis proje dersi: dogru yontem KURUS sapar, yanlis yontem BINLERCE dolar.
    Bu denklem olmadan yanlis toplama sessizce dogru gorunur.

    ⚠ LIKIDASYON MESRU BIR ISTISNADIR: `muhasebe()` likidasyonda
    `net = max(net, -(teminat + komisyon))` kirpmasi uygular; kirpilan pozisyonda
    ozdeslik BOZULUR ve bu bir hata DEGILDIR. Denklem onlari AYRI sayar ve
    raporlar — gizlemez, hataya da saymaz. Gizlenirse denklemin kendisi yalan
    soylemeye baslar.

    Doner: {"tamam": bool, "fark": float, "kirpilmis": int, ...}
    """
    brut = sum(p.get("pnl_brut_usd") or 0 for p in kapali)
    kom = sum(p.get("komisyon_usd") or 0 for p in kapali)
    fund = sum(p.get("funding_toplam_usd") or 0 for p in kapali)
    net = sum(p.get("pnl_net_usd") or 0 for p in kapali)

    # kirpma etkisi: yalniz likidasyonlarda ve yalniz kirpma GERCEKTEN devreye
    # girdiyse. Beklenen net ile saklanan net arasindaki fark kirpmanin miktaridir.
    kirpma, kirpilmis = 0.0, 0
    for p in kapali:
        if p.get("durum") != "likidasyon":
            continue
        bek = ((p.get("pnl_brut_usd") or 0) - (p.get("komisyon_usd") or 0)
               + (p.get("funding_toplam_usd") or 0))
        gercek = p.get("pnl_net_usd") or 0
        if abs(gercek - bek) > 1e-6:
            kirpma += gercek - bek
            kirpilmis += 1

    beklenen = brut - kom + fund + kirpma
    fark = net - beklenen
    return {"tamam": abs(fark) <= tolerans, "fark": round(fark, 6),
            "brut": round(brut, 4), "komisyon": round(kom, 4),
            "funding": round(fund, 4), "net": round(net, 4),
            "kirpma_usd": round(kirpma, 4), "kirpilmis_pozisyon": kirpilmis,
            "n": len(kapali)}


def portfoy_ozet(pozisyonlar, bakiye=VARSAYILAN_BAKIYE):
    """Spot ve vadeli AYRI, toplam risk BIRLESIK (TASARIM-BOT §5).

    🔴 Ciktida `mutabakat` alani ZORUNLUDUR (madde 7.5): bu ozet bir P&L
    toplamidir ve denklem kosmadan doner degeri yayimlanmamalidir."""
    acik = [p for p in pozisyonlar if p["durum"] in ACIK_DURUMLAR]
    kapali = [p for p in pozisyonlar if p["durum"] in KAPALI_DURUMLAR]
    o = {"bakiye_baslangic": bakiye, "acik": len(acik), "kapali": len(kapali)}
    for pi in ("spot", "vadeli"):
        alt = [p for p in kapali if p["piyasa"] == pi]
        o[pi] = {
            "kapali": len(alt),
            "net_usd": round(sum(p.get("pnl_net_usd") or 0 for p in alt), 4),
            "funding_usd": round(sum(p.get("funding_toplam_usd") or 0 for p in alt), 4),
            "komisyon_usd": round(sum(p.get("komisyon_usd") or 0 for p in alt), 4),
            "acik": sum(1 for p in acik if p["piyasa"] == pi),
        }
    o["net_usd"] = round(sum(p.get("pnl_net_usd") or 0 for p in kapali), 4)
    o["bakiye"] = round(bakiye + o["net_usd"], 4)
    o["net_R"] = round(sum(p.get("pnl_R") or 0 for p in kapali), 3)
    izlenen = [p for p in acik if p["durum"] == "izleniyor"]
    for yon in ("LONG", "SHORT"):
        o[f"acik_risk_{yon}_pct"] = round(
            sum(p["risk_pct"] for p in izlenen if p["yon"] == yon), 2)
    o["risk_tavani_pct"] = defter.RISK_TAVANI_PCT
    o["teminat_bagli_usd"] = round(sum(p["teminat"] for p in izlenen), 2)
    o["mutabakat"] = mutabakat(kapali)          # madde 7.5 — atlanamaz
    if not o["mutabakat"]["tamam"]:
        olcucu.log_line(
            f"[MUTABAKAT] 🔴 DENKLEM TUTMADI: fark {o['mutabakat']['fark']:+.6f} $ "
            f"(n={o['mutabakat']['n']}). P&L toplami SUPHELIDIR.")
    return o


# ==============================================================================
#  DEFTER (bot-defter.json)  — canli defterlere DOKUNMAZ
# ==============================================================================
def defter_yukle():
    if not BOT_DEFTER.exists():
        return {"pozisyonlar": [], "bakiye": VARSAYILAN_BAKIYE, "sonraki_no": 1}
    return json.loads(BOT_DEFTER.read_text(encoding="utf-8"))


def defter_kaydet(d):
    olcucu.atomik_yaz(BOT_DEFTER, d)


def defter_ekle(p, d=None):
    kendi = d is None
    d = d or defter_yukle()
    if p.get("no") is None:
        p["no"] = d["sonraki_no"]
        d["sonraki_no"] += 1
    d["pozisyonlar"].append(p)
    if kendi:
        defter_kaydet(d)
    return p


# ==============================================================================
#  KENDI TESTI
# ==============================================================================
def _mum(t_ms, h, l, c):
    return {"t": t_ms, "h": h, "l": l, "c": c}


def kendi_testi():
    ok, hata = 0, []

    def kontrol(ad, sart, ek=""):
        nonlocal ok
        if sart:
            ok += 1
            print(f"  ok   {ad}")
        else:
            hata.append(ad)
            print(f"  HATA {ad} {ek}")

    print("\n[1] Boyutlandirma — kaldirac riski DEGISTIRMEZ")
    a = boyutlandir(1000, 1.0, 100.0, 95.0, kaldirac=1)
    b = boyutlandir(1000, 1.0, 100.0, 95.0, kaldirac=10)
    kontrol("risk_usd kaldiractan bagimsiz", a["risk_usd"] == b["risk_usd"] == 10.0)
    kontrol("miktar kaldiractan bagimsiz", abs(a["miktar"] - b["miktar"]) < 1e-9)
    kontrol("teminat 10x'te 1/10", abs(b["teminat"] - a["teminat"] / 10) < 1e-9,
            f"{b['teminat']} vs {a['teminat']}")

    print("\n[2] Likidasyon formulu")
    liq = likidasyon_fiyati(100.0, "LONG", 10, 0.01)
    kontrol("LONG 10x mmr%1 -> 91.0", abs(liq - 91.0) < 1e-9, f"{liq}")
    liqs = likidasyon_fiyati(100.0, "SHORT", 10, 0.01)
    kontrol("SHORT 10x mmr%1 -> 109.0", abs(liqs - 109.0) < 1e-9, f"{liqs}")
    kontrol("spot'ta likidasyon yok", likidasyon_fiyati(100, "SPOT", 1, 0.01) is None)
    kontrol("kaldirac artinca liq girise yaklasir",
            likidasyon_fiyati(100, "LONG", 25, 0.01) > likidasyon_fiyati(100, "LONG", 5, 0.01))

    print("\n[3] Uyari — likidasyon stop'un icinde mi")
    p_tehlike = yeni("XUSDT", "LONG", 100.0, 95.0, 110.0, 116.0, kaldirac=20)
    u = uyarilar(p_tehlike)
    kontrol("20x + %5 stop -> STOP'UN ICINDE uyarisi",
            any("STOP'UN ICINDE" in x for x in u), str(u))
    p_guvenli = yeni("XUSDT", "LONG", 100.0, 95.0, 110.0, 116.0, kaldirac=2)
    kontrol("2x + %5 stop -> o uyari YOK",
            not any("STOP'UN ICINDE" in x for x in uyarilar(p_guvenli)))
    kontrol("gap uyarisi her vadeli pozisyonda var",
            any("GAP" in x for x in uyarilar(p_guvenli)))

    print("\n[4] defter.coz() ile birlikte calisma (tetik -> TP1)")
    t0 = datetime(2026, 8, 1, tzinfo=timezone.utc)
    p = yeni("XUSDT", "LONG", 100.0, 95.0, 110.0, 116.0, kaldirac=2,
             bakiye=1000, risk_pct=1.0, tarih=t0)
    ms = int(t0.timestamp() * 1000)
    mumlar = [
        _mum(ms + 60_000, 100.5, 99.0, 100.2),      # tetik (h >= giris)
        _mum(ms + 120_000, 104.0, 100.0, 103.0),
        _mum(ms + 180_000, 110.5, 103.0, 110.2),    # TP1
    ]
    coz(p, mumlar)
    kontrol("durum tp1", p["durum"] == "tp1", p["durum"])
    kontrol("sonuc_R ~ +2.0", abs(p["sonuc_R"] - 2.0) < 0.01, str(p["sonuc_R"]))
    kontrol("brut USD = 2R = 20", abs(p["pnl_brut_usd"] - 20.0) < 1e-6, str(p["pnl_brut_usd"]))
    kontrol("net < brut (komisyon dusuldu)", p["pnl_net_usd"] < p["pnl_brut_usd"])
    kontrol("net_R komisyondan sonra 2R altinda", p["pnl_R"] < 2.0, str(p["pnl_R"]))

    print("\n[5] Ayni mumda stop+TP -> temkinli STOP (motor odunc alindi)")
    p2 = yeni("XUSDT", "LONG", 100.0, 95.0, 110.0, 116.0, kaldirac=2, tarih=t0)
    coz(p2, [_mum(ms + 60_000, 100.5, 99.0, 100.2),
             _mum(ms + 120_000, 111.0, 94.0, 100.0)])
    kontrol("stop secildi", p2["durum"] == "stop", p2["durum"])
    kontrol("net USD negatif", p2["pnl_net_usd"] < 0, str(p2["pnl_net_usd"]))

    print("\n[6] Likidasyon stop'un icindeyse tetiklenir")
    p3 = yeni("XUSDT", "LONG", 100.0, 90.0, 110.0, 116.0, kaldirac=20, tarih=t0)
    kontrol("liq (=95.x) stop'un (90) icinde",
            p3["likidasyon_fiyati"] > p3["stop"], str(p3["likidasyon_fiyati"]))
    coz(p3, [_mum(ms + 60_000, 100.5, 99.0, 100.2),
             _mum(ms + 120_000, 100.0, 94.0, 94.5)])
    kontrol("durum likidasyon", p3["durum"] == "likidasyon", p3["durum"])
    kontrol("kayip teminattan buyuk degil",
            p3["pnl_net_usd"] >= -(p3["teminat"] + p3["komisyon_usd"]) - 1e-6,
            f"{p3['pnl_net_usd']} vs teminat {p3['teminat']}")

    print("\n[7] Likidasyon stop'un DISINDAYSA tetiklenmez (gap yok varsayimi)")
    p4 = yeni("XUSDT", "LONG", 100.0, 95.0, 110.0, 116.0, kaldirac=2, tarih=t0)
    coz(p4, [_mum(ms + 60_000, 100.5, 99.0, 100.2),
             _mum(ms + 120_000, 100.0, 40.0, 45.0)])       # cok sert dusus
    kontrol("stop secildi, likidasyon degil", p4["durum"] == "stop", p4["durum"])

    print("\n[8] Funding isareti — oran>0'da LONG ODER, SHORT ALIR")
    pf = yeni("XUSDT", "LONG", 100.0, 95.0, 110.0, 116.0, kaldirac=2, tarih=t0)
    pf["durum"], pf["tetik_tarih"] = "izleniyor", t0.isoformat(timespec="seconds")
    pf["kapanis_tarih"] = (t0 + timedelta(hours=24)).isoformat(timespec="seconds")
    funding_uygula(pf, [(ms + 8 * 3600_000, 0.0001)])
    kontrol("LONG oder (negatif)", pf["funding_toplam_usd"] < 0, str(pf["funding_toplam_usd"]))
    ps = yeni("XUSDT", "SHORT", 100.0, 105.0, 90.0, 84.0, kaldirac=2, tarih=t0)
    ps["durum"], ps["tetik_tarih"] = "izleniyor", t0.isoformat(timespec="seconds")
    ps["kapanis_tarih"] = (t0 + timedelta(hours=24)).isoformat(timespec="seconds")
    funding_uygula(ps, [(ms + 8 * 3600_000, 0.0001)])
    kontrol("SHORT alir (pozitif)", ps["funding_toplam_usd"] > 0, str(ps["funding_toplam_usd"]))
    onceki = pf["funding_toplam_usd"]
    funding_uygula(pf, [(ms + 8 * 3600_000, 0.0001)])
    kontrol("idempotent (ayni odeme iki kez islenmez)",
            pf["funding_toplam_usd"] == onceki)
    kontrol("odenen funding likidasyonu girise yaklastirdi",
            pf["likidasyon_fiyati"] > likidasyon_fiyati(100.0, "LONG", 2, pf["mmr"]),
            str(pf["likidasyon_fiyati"]))
    kontrol("spot'ta funding yok",
            funding_uygula(yeni("XUSDT", "LONG", 100, 95, 110, 116, piyasa="spot"),
                           [(ms, 0.01)]) == 0.0)

    print("\n[9] Kismi cikis mekanizmasi")
    pk = yeni("XUSDT", "LONG", 100.0, 95.0, 110.0, 116.0, kaldirac=2, tarih=t0)
    pk["durum"], pk["tetik_tarih"] = "izleniyor", t0.isoformat(timespec="seconds")
    ilk_miktar = pk["miktar"]
    kismi_kapat(pk, 0.5, 110.0, tarih=t0)
    kontrol("miktar yariya indi", abs(pk["miktar"] - ilk_miktar / 2) < 1e-9)
    kontrol("gerceklesen pozitif", pk["gerceklesen_usd"] > 0, str(pk["gerceklesen_usd"]))
    kontrol("kismi cikis kaydedildi", len(pk["kismi_cikislar"]) == 1)

    print("\n[10] Spot maliyeti vadeliden PAHALI (ayri model)")
    sv = bacak_maliyet_orani("vadeli", True)
    ss = bacak_maliyet_orani("spot", True)
    kontrol("spot taker > vadeli taker", ss > sv, f"spot {ss:.6f} vs vadeli {sv:.6f}")
    kontrol("spot SHORT reddedilir",
            _hata_verir(lambda: yeni("XUSDT", "SHORT", 100, 105, 90, 84, piyasa="spot")))
    kontrol("giris==stop reddedilir",
            _hata_verir(lambda: yeni("XUSDT", "LONG", 100, 100, 110, 116)))

    print("\n[11] JSON gidis-donus + konfig sabiti")
    p5 = yeni("XUSDT", "LONG", 100.0, 95.0, 110.0, 116.0, kaldirac=3, tarih=t0)
    kontrol("konfig defter.KONFIG'e sabit (eski 5dk limitleri secilmesin)",
            p5["konfig"] == defter.KONFIG, p5["konfig"])
    kontrol("defter.coz limitleri modern okur",
            defter._limitler(p5) == (defter.PENDING_SAAT, defter.ACTIVE_SAAT))
    kontrol("JSON gidis-donus", json.loads(json.dumps(p5, ensure_ascii=False)) == p5)

    print("\n[12] Portfoy — spot/vadeli ayri, risk birlesik")
    poz = [p, p2, p3]
    o = portfoy_ozet(poz, bakiye=1000)
    kontrol("kapali 3", o["kapali"] == 3, str(o["kapali"]))
    kontrol("vadeli alt toplami var", "vadeli" in o and "spot" in o)
    kontrol("net_usd = alt toplamlarin toplami",
            abs(o["net_usd"] - (o["spot"]["net_usd"] + o["vadeli"]["net_usd"])) < 1e-6)
    kontrol("risk tavani defter'den", o["risk_tavani_pct"] == defter.RISK_TAVANI_PCT)

    print("\n[13] Canli defterlere DOKUNULMADI")
    kontrol("bot kendi defterini kullanir", BOT_DEFTER.name == "bot-defter.json")
    kontrol("defter.py'nin dosyasi ayri",
            defter.DEFTER_FILE.name != BOT_DEFTER.name)

    print("\n" + "=" * 60)
    print(f"  {ok} gecti, {len(hata)} kaldi")
    if hata:
        for h in hata:
            print("   KALAN:", h)
    print("=" * 60)
    return not hata


def _hata_verir(fn):
    try:
        fn()
        return False
    except Exception:
        return True


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print("=" * 60)
    print("  pozisyon.py — KENDI TESTI (canliya dokunmaz)")
    print("=" * 60)
    sys.exit(0 if kendi_testi() else 1)
