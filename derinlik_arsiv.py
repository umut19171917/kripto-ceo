"""
derinlik_arsiv.py — EMIR DEFTERI DERINLIGININ ILERI ARSIVCISI (2026-08-31)
================================================================================
NEDEN VAR: madde 7.4 / B4. Bant disi dort adaydan biri "emir defterinde
bekleyen likidite". Fizibilite olculdu (2026-08-31):

  /fapi/v1/depth  ->  YALNIZ ANLIK. `startTime` kabul ediliyor ama AYNI anlik
                      veriyi donduruyor. GECMIS YOK. Hicbir ucta yok.

⚠ SONUC: bu veri sonradan CEKILEMEZ. `perp_arsiv.py`'nin 30 gunluk uclarindan
bile daha katidir — orada 29 gun geri dolgu vardi, burada SIFIR. Bugun
arsivlenmeyen an, kalici olarak yoktur.

--------------------------------------------------------------------------------
🔴 ORNEKLEM UFKU — insa etmeden ONCE hesaplandi (aksi halde aylarca bosa toplanir)
--------------------------------------------------------------------------------
`basis` olcumu (162100b) 1.459 gun / 3.650 bagimsiz birimle ±%0,25 hassasiyet
verdi. Ileri arsivde 30 gun ~= 75 bagimsiz birim (gun-kumeli, semboller birlikte
hareket ettigi icin ~2,5 etkin sembol):

    24 SAATLIK ufuk, 30 gun  ->  hassasiyet ±%1,74   ekonomik esik %0,5  ❌ ISE YARAMAZ
    24 SAATLIK ufuk,  1 yil  ->  hassasiyet ±%0,50                        ~sinirda
     1 SAATLIK ufuk, 30 gun  ->  hassasiyet ±%0,064  maliyet esigi %0,13  ✅ YETERLI

Gerekce: 1 saatlik ufukta gun ici pencereler ortusmez, bagimsiz birim sayisi
~24 kat artar; sd(1s getiri) ~ sd(24s)/sqrt(24) ile duser ama maliyet esigi
DUSMEZ (%0,13 gidis-donus sabittir) -> oran lehe doner.

⚠ Ve bu zaten DOGRU ufuktur: emir defteri derinligi bir mikroyapi degiskenidir,
doğal olcegi dakikalar-saatlerdir. 24 saat sormak, degiskeni kendi olceginin
disinda sinamak olurdu.

**Bu betik veri TOPLAR, hipotez SINAMAZ.** Sinama ayri bir on kayit ister.

--------------------------------------------------------------------------------
NE SAKLANIR (ham defter DEGIL — ozet)
--------------------------------------------------------------------------------
500 kademelik ham defteri 30 sembol x 144 tur/gun saklamak anlamsiz buyuklukte
olurdu. Snapshot basina 7 sayi saklanir.

🔴 KADEME SAYISI, YUZDE BANDI DEGIL — ilk tasarim ELENDI (2026-08-31, olculdu):
sabit yuzde bantlari (±%0,10 / %0,25 / %0,50) dar-tick'li sembollerde COKUYOR.
Olcum: BTCUSDT'de 500 kademe yalnizca ~50 $ = fiyatin **%0,06**'sini kapsiyor,
yani UC BANT DA AYNI emirleri iceriyordu (imb10=imb25=imb50=0,00443). Bir
sembolde ozdes, digerinde farkli olan bir olcut kiyaslanamaz.

  spread_bps : (ask-bid)/orta x 10000
  imb5/50/N  : en iyi 5 / 50 / TUM kademede
               (alis_notional - satis_notional) / (toplam)   -> [-1, +1]
  notN       : TUM alinan kademelerdeki toplam notional (likidite SEVIYESI)
  span_bps   : alinan defterin kapsadigi fiyat araligi (bps)
               🔴 TESHIS ALANI: bir sembolde defter %0,06, digerinde %5
               kapsiyorsa bunlar ayni sey DEGILDIR. Bu alan olmadan derin
               defterle sig defteri sessizce kiyaslardik.
  orta       : orta fiyat (getiri hesabi ve denetim icin)

Dengesizlik ORANDIR: sembol buyuklugune ve coin fiyatina gore normalize.
`notN` seviyeyi ayri tutar — "dengesiz mi" ile "ince mi" ayri sorulardir.

--------------------------------------------------------------------------------
🔴 BIRLESTIRME DEGISMEZI (perp_arsiv.py ile AYNI kural, dis proje dersi)
--------------------------------------------------------------------------------
Yazmadan once var olan okunur, zaman damgasina gore birlestirilir ve sonuc
eskisinden KISAysa RuntimeError firlatilir. Silme yolu kapali olmalidir.

Calistirma:
  venv\\Scripts\\python.exe derinlik_arsiv.py            -> bir tur (bir snapshot)
  venv\\Scripts\\python.exe derinlik_arsiv.py --durum    -> kapsama raporu (AG YOK)
"""
import sys as _sys
# 🔴 Konsol cp1254 -> Cince adli semboller (我踏马来了USDT vb.) --durum raporunu
# COKERTIR. Bu tuzaga bu projede birden fazla kez dusuldu; bastan kapatiliyor.
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

import olcucu

ARSIV = Path("derinlik-arsiv")
LIMIT = 1000             # /fapi/v1/depth'in azami kademe sayisi
ARA_SN = 0.15            # istekler arasi nezaket
KADEMELER = (5, 50)      # yuzde bandi DEGIL kademe sayisi (bkz. dosya basi)
SEMBOL_TAVANI = 30       # ana 11 + hacim liderleri; tur ~10 sn'de bitsin
ZAMAN_ASIMI = 12


def _dosya(sym):
    return ARSIV / f"{sym}.json"


def _oku(sym):
    y = _dosya(sym)
    if not y.exists():
        return {}
    try:
        return json.loads(y.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _sayac(d):
    return len(d) if isinstance(d, dict) else 0


def _birlestir(eski, yeni):
    """🔴 DEGISMEZ: birlestir, EZME. Sonuc kisaliyorsa HATA."""
    birlesik = {**eski, **yeni}
    if _sayac(birlesik) < _sayac(eski):
        raise RuntimeError(
            f"BIRLESTIRME KISALTTI: {_sayac(eski)} -> {_sayac(birlesik)}. "
            "Yazma iptal — bu, kalici veri kaybinin ta kendisidir.")
    return birlesik


def semboller():
    """Ana 11 ONCELIKLI (her onceki olcum orada kosuldu) + hacim liderleri."""
    ana = list(olcucu.SYMBOLS)
    try:
        import tarayici
        digerleri = [s for s, _v in tarayici.evren(30_000_000)]
    except Exception as e:
        olcucu.log_line(f"[DERINLIK] evren alinamadi ({type(e).__name__}), yalniz ana {len(ana)}")
        digerleri = []
    out = list(ana)
    for s in digerleri:
        if s not in out:
            out.append(s)
        if len(out) >= SEMBOL_TAVANI:
            break
    return out


def ozet(defter):
    """Ham defter -> 7 sayi. Bozuk/ince defterde None doner.

    [spread_bps, imb5, imb50, imbN, notN, span_bps, orta]"""
    bids = [(float(p), float(q)) for p, q in defter.get("bids", [])]
    asks = [(float(p), float(q)) for p, q in defter.get("asks", [])]
    if not bids or not asks:
        return None
    en_iyi_alis, en_iyi_satis = bids[0][0], asks[0][0]
    if en_iyi_alis <= 0 or en_iyi_satis <= 0 or en_iyi_satis <= en_iyi_alis:
        return None                       # capraz/bozuk defter -> kayit YOK
    orta = (en_iyi_alis + en_iyi_satis) / 2.0
    spread_bps = (en_iyi_satis - en_iyi_alis) / orta * 10000.0

    def dengesizlik(n):
        a = sum(p * q for p, q in bids[:n])
        s = sum(p * q for p, q in asks[:n])
        t = a + s
        return ((a - s) / t if t > 0 else 0.0), t

    imb = [dengesizlik(n)[0] for n in KADEMELER]
    imbN, notN = dengesizlik(max(len(bids), len(asks)))

    # 🔴 defterin ULASTIGI fiyat araligi — kiyaslanabilirligin tek denetimi
    span_bps = (asks[-1][0] - bids[-1][0]) / orta * 10000.0

    return [round(spread_bps, 4), round(imb[0], 5), round(imb[1], 5),
            round(imbN, 5), round(notN, 2), round(span_bps, 2), orta]


def sembol_arsivle(sym, ts):
    """Tek snapshot cek + ozetle + BIRLESTIR + atomik yaz. Doner: True/False."""
    r = requests.get(olcucu.BASE + "/fapi/v1/depth",
                     params={"symbol": sym, "limit": LIMIT}, timeout=ZAMAN_ASIMI)
    r.raise_for_status()
    o = ozet(r.json())
    if o is None:
        return False
    eski = _oku(sym)
    birlesik = _birlestir(eski, {str(ts): o})     # kisalirsa burada patlar
    ARSIV.mkdir(exist_ok=True)
    olcucu.atomik_yaz(_dosya(sym), birlesik)
    return True


def durum():
    """Kapsama raporu — AG KULLANMAZ."""
    if not ARSIV.exists():
        print("derinlik-arsiv/ yok — henuz hic kosulmamis.")
        return
    dosyalar = sorted(ARSIV.glob("*.json"))
    an = lambda ms: datetime.fromtimestamp(ms / 1000, timezone.utc).strftime("%Y-%m-%d %H:%M")
    print(f"{'sembol':<14} {'snapshot':>9} {'gun':>6}   {'en eski':<17} {'en yeni':<17}")
    print("-" * 72)
    top = 0
    for f in dosyalar:
        d = json.loads(f.read_text(encoding="utf-8"))
        ts = [int(k) for k in d]
        if not ts:
            continue
        top += len(ts)
        gun = (max(ts) - min(ts)) / 86400_000
        print(f"{f.stem:<14} {len(ts):>9} {gun:>6.1f}   {an(min(ts)):<17} {an(max(ts)):<17}")
    print("-" * 72)
    boyut = sum(f.stat().st_size for f in dosyalar) / 1e6
    print(f"{len(dosyalar)} sembol · {top:,} snapshot · {boyut:.1f} MB")
    if top:
        gunler = max(1e-9, (max(ts) - min(ts)) / 86400_000)
        print(f"⚠ 1 SAATLIK ufuk icin ~30 gun gerekir (bkz. dosya basi). "
              f"Su an ~{gunler:.1f} gun.")


def main():
    if "--durum" in sys.argv:
        durum()
        return 0
    syms = semboller()
    ts = int(time.time() * 1000) // 60000 * 60000       # dakikaya yuvarla
    bas = time.time()
    yazan, hatali = 0, []
    for sym in syms:
        try:
            if sembol_arsivle(sym, ts):
                yazan += 1
        except RuntimeError as e:
            hatali.append((sym, str(e)))
            print(f"  🔴 {sym}: {e}")
        except Exception as e:
            hatali.append((sym, f"{type(e).__name__}: {str(e)[:60]}"))
        time.sleep(ARA_SN)
    sn = time.time() - bas
    # log_line KONSOLA DA yazar (olcucu.py:400) -> ayrica print ETME, log ikilenir.
    # Zaman damgasi SART: gunde 144 tur kosuyor, damgasiz log'da "kac tur atlandi"
    # sorusu cevaplanamaz (sessiz bozulma en tehlikelisi — arsiv 8. ders).
    damga = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    olcucu.log_line(f"[{damga}] [DERINLIK] {yazan}/{len(syms)} sembol, "
                    f"{len(hatali)} hata, {sn:.0f}sn")
    if hatali:
        for s, e in hatali[:5]:
            print(f"    {s}: {e}")
    return 0 if yazan else 1


if __name__ == "__main__":
    sys.exit(main())
