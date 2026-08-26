"""
perp_arsiv.py — 30 GUNLUK UCLARIN ARSIVCISI (2026-08-25)
================================================================================
NEDEN VAR: Binance'te iki sinif uc var ve ikisi ayni `fapi` altinda duruyor —
  KALICI : /fapi/v1/klines · /fapi/v1/fundingRate      -> istendigi an 2 yil geriye
  30 GUN : /futures/data/globalLongShortAccountRatio
           /futures/data/openInterestHist
           /futures/data/takerlongshortRatio           -> YALNIZ ~30 gun

OLCULDU (2026-08-25, bu projede; dis kaynagin sayisi tekrarlanmadi, DOGRULANDI):
  29 gun geriye  -> OK, n=30
  32 gun geriye  -> HTTP 400

⚠ SONUC: bu veri SONRADAN CEKILEMEZ. Yalnizca O AN arsivlenirse vardir.
Her gecen gun kuyrugundan bir gun KALICI olarak dusuyor.

--------------------------------------------------------------------------------
NEDEN ACIL: `ls_ratio` hicbir yerde saklanmiyor
--------------------------------------------------------------------------------
`olcucu.squeeze_scores` icinde ls_ratio +20 puan veriyor ve esikleri KODA GOMULU
(SHORT-squeeze <1.0 / LONG-squeeze >1.5) — funding ve OI persentille kalibre
edilirken ls_ratio hic kalibre edilmiyor. Canli olcum (69 sembol): medyan 1,46;
+20 puan SHORT sinyaline 2,5 kat daha sik gidiyor.

Ama bu simetrisizligin ZARAR verdigi KANITLANAMADI — cunku veri yok:
defterde ls_ratio alani yok · olcucu.log yalniz SS/LS TOPLAMINI yaziyor,
bilesenleri degil · signals.json anlik.

**SISTEM.md §12 madde 7'nin testi, bu arsiv olmadan HICBIR ZAMAN yapilamaz.**
Bu betik o testi MUMKUN kilar; testi kendisi YAPMAZ.

--------------------------------------------------------------------------------
⛔ NEYE DOKUNMAZ (kosan `radar-v2` on kaydi acikken yazildi)
--------------------------------------------------------------------------------
- `defter.py` · `radar_defter.py` · `olcucu.py` · `makro.py`: DOKUNULMAZ.
  Bu modul `olcucu`'yu yalnizca _get/atomik_yaz/log_line icin IMPORT eder.
- Radar esikleri, plan mekanigi, makro kapi mantigi, kanonik suzgec: DEGISMEZ.
  -> ON-KAYIT-radar-v2.md §6'nin hicbir gecersizlik sarti tetiklenmez.
- Calisan `izleyici.py` / `radar.py` surecleri: DURDURULMAZ, okunmaz, yazilmaz.
- Kendi dizinine yazar: `perp-arsiv/` (gitignore'lu).

--------------------------------------------------------------------------------
🔴 BIRLESTIRME DEGISMEZI (dis proje dersi, 2026-08-25)
--------------------------------------------------------------------------------
O projede `os.replace` var olan DAHA UZUN dosyayi ezdi ve 58 sembolde 4 gunluk
OI/LS/taker KALICI olarak gitti. Bizde ayni sinif hata bir kez oldu (A1: ag
hatasi esikler.json'un 11 sembolunu birden sildi).

Bu yuzden `_birlestir()` uc sey yapar: (a) var olani okur, (b) zaman damgasina
gore birlestirir, (c) **sonuc eskisinden KISAysa RuntimeError firlatir.**
Bu bir "iyi olur" degil, DEGISMEZ — silme yolu kapali olmali.

Calistirma:
  venv\\Scripts\\python.exe perp_arsiv.py            -> bir tur (artimli)
  venv\\Scripts\\python.exe perp_arsiv.py --dolgu    -> ilk kurulum, 30 gun geri
  venv\\Scripts\\python.exe perp_arsiv.py --durum    -> kapsama raporu (ag YOK)
"""
import json
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

KOK = Path(__file__).parent
sys.path.insert(0, str(KOK))
import olcucu

ARSIV = KOK / "perp-arsiv"
PERIYOT = "5m"           # canli sistem 5dk okuyor -> birebir yeniden kurulum icin sart
TAVAN_GUN = 29           # 32'de HTTP 400 olculdu; 29 guvenli
ARA_SN = 0.2             # istekler arasi bekleme (rate-limit nezaketi)

# Uc adi -> (yol, arsivdeki anahtar, kayittan deger cikaran fonksiyon)
UCLAR = {
    "ls":    ("/futures/data/globalLongShortAccountRatio", lambda x: float(x["longShortRatio"])),
    "oi":    ("/futures/data/openInterestHist",            lambda x: float(x["sumOpenInterest"])),
    "taker": ("/futures/data/takerlongshortRatio",         lambda x: float(x["buySellRatio"])),
}


def semboller():
    """Ana 11 coin (esikler.json'un evreni) + radar evreninin hacim liderleri.
    Ana 11 ONCELIKLI: §12 madde 7'nin testi once orada kurulacak."""
    ana = list(olcucu.SYMBOLS)
    try:
        import tarayici
        radar = [s for s, _v in tarayici.evren(30_000_000)][:40]
    except Exception as e:
        olcucu.log_line(f"[PERP-ARSIV] radar evreni alinamadi ({type(e).__name__}), yalniz ana 11")
        radar = []
    out = list(ana)
    for s in radar:
        if s not in out:
            out.append(s)
    return out


def _dosya(sym):
    return ARSIV / f"{sym}.json"


def _oku(sym):
    try:
        return json.loads(_dosya(sym).read_text(encoding="utf-8"))
    except Exception:
        return {}


def _sayac(d):
    return sum(len(v) for v in d.values() if isinstance(v, dict))


def _birlestir(eski, yeni):
    """🔴 DEGISMEZ: birlestir, EZME. Sonuc kisaliyorsa HATA.

    Eski ve yeni ayni zaman damgasini tasiyorsa yeni kazanir (tazeleme), ama
    eskide olup yenide olmayan HICBIR nokta dusmez."""
    birlesik = {}
    for anahtar in set(list(eski.keys()) + list(yeni.keys())):
        e = eski.get(anahtar) or {}
        y = yeni.get(anahtar) or {}
        if not isinstance(e, dict) or not isinstance(y, dict):
            birlesik[anahtar] = y or e
            continue
        birlesik[anahtar] = {**e, **y}
    if _sayac(birlesik) < _sayac(eski):
        raise RuntimeError(
            f"BIRLESTIRME KISALTTI: {_sayac(eski)} -> {_sayac(birlesik)}. "
            "Yazma iptal — bu, kalici veri kaybinin ta kendisidir.")
    return birlesik


def _cek(yol, sym, bitis_ms, cikar):
    """Tek uctan tek sayfa, GERIYE dogru. Doner: {ts_str: deger}.

    🔴 `startTime` BU UCLARDA YOK SAYILIYOR — olculdu (2026-08-26): 2, 10 ve 25
    gun oncesi verilen uc ayri istek AYNI pencereyi dondurdu
    (2026-08-24 14:35 -> 2026-08-26 08:10). Sayfalama YALNIZ `endTime` ile olur.
    ⚠ Ilk surumde startTime kullanildi ve her sembolde yalniz SON 500 nokta
    (~41 saat) alindi; "29 gunluk dolgu" yapildi saniliyordu. Bu yol kapali."""
    ham = olcucu._get(yol, {"symbol": sym, "period": PERIYOT,
                            "endTime": int(bitis_ms), "limit": 500})
    out = {}
    for x in ham:
        try:
            out[str(int(x["timestamp"]))] = round(cikar(x), 6)
        except Exception:
            pass
    return out


def sembol_arsivle(sym, gun_geri):
    """Bir sembolun uc serisini cek + BIRLESTIR + atomik yaz. Doner: (eklenen, toplam)."""
    eski = _oku(sym)
    yeni = {}
    simdi = time.time() * 1000
    hedef = simdi - gun_geri * 86400_000        # bu ana kadar GERIYE inilecek
    for anahtar, (yol, cikar) in UCLAR.items():
        seri, imlec, tur = {}, simdi, 0
        # GERIYE sayfalama: her sayfa 500 nokta x 5dk = ~41 saat.
        # 29 gun ~= 17 sayfa; tavan 25 (guvenlik payi + eksik sayfa ihtimali).
        while tur < 25:
            try:
                sayfa = _cek(yol, sym, imlec, cikar)
            except Exception as e:
                olcucu.log_line(f"[PERP-ARSIV] {sym}/{anahtar} cekim hatasi: "
                                f"{type(e).__name__}: {str(e)[:60]}")
                break
            if not sayfa:
                break                            # veri sinirina gelindi
            seri.update(sayfa)
            en_eski = min(int(k) for k in sayfa)
            if en_eski >= imlec:
                break                            # ilerleme yok -> sonsuz dongu koru
            imlec = en_eski - 1
            tur += 1
            if en_eski <= hedef:
                break                            # istenen derinlige inildi
            time.sleep(ARA_SN)
        if seri:
            yeni[anahtar] = seri
    if not yeni:
        return 0, _sayac(eski)
    birlesik = _birlestir(eski, yeni)          # kisalirsa burada patlar
    ARSIV.mkdir(exist_ok=True)
    olcucu.atomik_yaz(_dosya(sym), birlesik)
    return _sayac(birlesik) - _sayac(eski), _sayac(birlesik)


def durum():
    """Kapsama raporu — AG KULLANMAZ."""
    if not ARSIV.exists():
        print("perp-arsiv/ yok — henuz hic kosulmamis.")
        return
    dosyalar = sorted(ARSIV.glob("*.json"))
    print(f"{'sembol':<14} {'ls':>7} {'oi':>7} {'taker':>7}   {'en eski':<17} {'en yeni':<17}")
    print("-" * 78)
    top = 0
    for f in dosyalar:
        d = json.loads(f.read_text(encoding="utf-8"))
        tsler = [int(k) for v in d.values() if isinstance(v, dict) for k in v]
        if not tsler:
            continue
        top += _sayac(d)
        an = lambda ms: datetime.fromtimestamp(ms / 1000, timezone.utc).strftime("%Y-%m-%d %H:%M")
        print(f"{f.stem:<14} {len(d.get('ls', {})):>7} {len(d.get('oi', {})):>7} "
              f"{len(d.get('taker', {})):>7}   {an(min(tsler)):<17} {an(max(tsler)):<17}")
    print("-" * 78)
    print(f"{len(dosyalar)} sembol · {top:,} nokta · {sum(f.stat().st_size for f in dosyalar)/1e6:.1f} MB")


def main():
    if "--durum" in sys.argv:
        durum()
        return 0
    gun = TAVAN_GUN if "--dolgu" in sys.argv else 2
    syms = semboller()
    bas = time.time()
    print(f"perp-arsiv: {len(syms)} sembol · {gun} gun geri · periyot {PERIYOT}")
    print("⛔ dondurulmus dosyalara DOKUNULMAZ; yalniz perp-arsiv/ yazilir\n")
    top_eklenen, hatali = 0, []
    for i, sym in enumerate(syms, 1):
        try:
            eklenen, toplam = sembol_arsivle(sym, gun)
            top_eklenen += eklenen
            print(f"  [{i:2d}/{len(syms)}] {sym:<14} +{eklenen:<6d} toplam {toplam:,}")
        except RuntimeError as e:
            hatali.append((sym, str(e)))
            print(f"  [{i:2d}/{len(syms)}] {sym:<14} 🔴 {e}")
        except Exception as e:
            hatali.append((sym, f"{type(e).__name__}: {e}"))
            print(f"  [{i:2d}/{len(syms)}] {sym:<14} HATA {type(e).__name__}")
    sure = time.time() - bas
    print(f"\n{top_eklenen:,} yeni nokta · {sure:.0f} sn · {len(hatali)} hatali")
    olcucu.log_line(f"[PERP-ARSIV] {len(syms)} sembol, +{top_eklenen} nokta, "
                    f"{len(hatali)} hata, {sure:.0f}sn")
    if hatali:
        print("\nHATALILAR:")
        for s, e in hatali[:10]:
            print(f"  {s}: {e[:90]}")
    return 1 if hatali else 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    sys.exit(main())
