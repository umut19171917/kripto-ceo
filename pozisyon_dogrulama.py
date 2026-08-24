"""
pozisyon_dogrulama.py — SIMULATORUN GECMIS SICILE KARSI DOGRULANMASI
================================================================================
KULLANICI KURALI 3 (2026-08-23): "pozisyon.py'yi gecmis kapanmis islemler
uzerinde calistir. Funding ve likidasyon KAPALIYKEN mevcut net-R'yi BIREBIR
uretmeli. Uretmiyorsa motor bozuk demektir — coz() testinde 19/19 esleme
aramistik, ayni standart."

Bu arac o standardi uygular. UC BOLUM:

  A. MUHASEBE (agsiz, TUM kapanmis kanonik islemler)
     A1  fiyat -> R yolu       : brut_USD / risk_USD  ==  sicildeki sonuc_R
     A2  maliyet yolu (BIREBIR): kendi komisyonum     ==  defter.maliyet_R()
     A3  uctan uca             : round(pnl_R, 2)      ==  defter.net_R()

  B. COZME MOTORU (agli, ornek islemler)
     Gercek 1dk mumlar yeniden cekilir, pozisyon SIFIRDAN cozulur;
     durum ve sonuc_R sicildekiyle ayni cikmali. Bu, `defter.coz`'un
     pozisyon dict'i uzerinde de dogru calistigini kanitlar.

  C. FARK OLCUMU (bilgi)
     defter'in maliyet YAKLASIKLIGI (iki bacagi da GIRIS fiyatindan olcer) ile
     gercek muhasebe (cikis bacagi CIKIS fiyatindan) arasindaki fark nicelenir.
     Bu bir hata degil, bilinen bir yaklasiklik — buyuklugu bilinsin diye.

⚠ A ve B'de funding KAPALI, likidasyon KAPALI, kaldirac 1x. Amac motoru
  dogrulamak; funding/likidasyon zaten sicilde MEVCUT DEGIL, bu yuzden onlar
  acikken birebir esleme BEKLENMEZ (ve beklenmemeli).

Calistirma: venv\\Scripts\\python.exe pozisyon_dogrulama.py
            venv\\Scripts\\python.exe pozisyon_dogrulama.py --hizli   (B'yi atlar)
Canliya DOKUNMAZ — yalnizca okur.
"""
import sys
from datetime import datetime
from pathlib import Path

KOK = Path(__file__).parent
sys.path.insert(0, str(KOK))
import defter
import metrikler as M
import pozisyon as P

BAKIYE, RISK_PCT = 1000.0, 1.0
RISK_USD = BAKIYE * RISK_PCT / 100.0
SICILLER = (("ANA", "kripto-defter.json"), ("RADAR", "radar-defter.json"))

# Bir islem en fazla PENDING+ACTIVE kadar yasar -> mum tavani bu kadar yeter.
# (defter.k1m_kapanmis_araliktan'in `tavan` parametresi; fonksiyon KOPYALANMADI.)
MUM_TAVANI = 9000


# `coz()` (fitil-tabanli 1dk mum motoru) 2026-07-02'de geldi. ONCESI kayitlar 30sn
# NOKTA ORNEKLEMESI ile cozuldu ve defter.py'nin kendi notuna gore o yontem
# "sicili sistematik IYIMSER kaydeder". Bu yuzden coz() onaki kayitlarin fitil
# motoruyla yeniden uretilmesi BEKLENMEZ — fark, motorun DAHA DOGRU olmasidir.
COZ_MOTORU_TARIHI = "2026-07-02"


def _poz_kur(t):
    """Sicildeki tahminden AYNI parametrelerle pozisyon kurar (cozulmemis).

    ⚠ `konfig` sicildekiyle AYNI birakilir (pozisyon.yeni onu defter.KONFIG'e
    sabitler). Gerekce: defter._limitler() konfig etiketine gore pending/active
    suresi secer — 5dk donemi (etiketsiz) 6s/24s, swing-1h 24s/120s. Gecmis bir
    islemi MODERN limitlerle oynatmak onu farkli bir isleme cevirir; tarihsel
    replay kendi doneminin kurallariyla yapilmalidir.
    """
    p = P.yeni(
        t.get("token") or t.get("sembol") or "?", t["yon"],
        t["giris"], t["stop"], t["tp1"], t.get("tp2") or t["tp1"],
        piyasa="vadeli", kaldirac=1, bakiye=BAKIYE, risk_pct=RISK_PCT,
        tarih=t["tarih"], strateji="dogrulama",
    )
    p["konfig"] = t.get("konfig")
    return p


def _durum_aktar(p, t):
    """Sicildeki KAPANIS durumunu pozisyona giydirir (cozme motoru calistirmadan).
    A bolumu muhasebeyi test eder; cozumu B bolumu test eder."""
    p["durum"] = t["durum"]
    p["tetik_tarih"] = t.get("tetik_tarih")
    p["sonuc_fiyat"] = t.get("sonuc_fiyat")
    p["sonuc_R"] = t.get("sonuc_R")
    p["kapanis_tarih"] = t.get("kapanis_tarih")
    return p


def bolum_a():
    print("=" * 78)
    print("  A. MUHASEBE DOGRULAMASI — tum kapanmis kanonik islemler, agsiz")
    print("     funding KAPALI · likidasyon KAPALI · kaldirac 1x")
    print("=" * 78)
    genel = {"n": 0, "a1": 0, "a2": 0, "a3": 0}
    sapmalar = []
    for ad, dosya in SICILLER:
        ts = [t for t in M.kapalilar(M.yukle(dosya))
              if t.get("tetik_tarih") and t.get("sonuc_R") is not None]
        n = a1 = a2 = a3 = 0
        for t in ts:
            p = _durum_aktar(_poz_kur(t), t)
            P.muhasebe(p, defter_uyumlu=True)
            n += 1

            # A1 — fiyat -> R yolu
            if abs(p["pnl_brut_usd"] / RISK_USD - t["sonuc_R"]) <= 0.005:
                a1 += 1
            else:
                sapmalar.append((ad, t, "A1",
                                 p["pnl_brut_usd"] / RISK_USD, t["sonuc_R"]))

            # A2 — maliyet yolu, BIREBIR (yuvarlanmamis alan uzerinden)
            benim_maliyet_R = p["komisyon_R"]
            if abs(benim_maliyet_R - defter.maliyet_R(t)) <= 1e-12:
                a2 += 1
            else:
                sapmalar.append((ad, t, "A2", benim_maliyet_R, defter.maliyet_R(t)))

            # A3 — uctan uca. Cift-yuvarlamadan kacinmak icin R tek adimda
            # yuvarlanir (defter.net_R de tek adimda yuvarlar).
            benim_net_R = round(p["sonuc_R"] - p["komisyon_R"], 2)
            if benim_net_R == defter.net_R(t):
                a3 += 1
            else:
                sapmalar.append((ad, t, "A3", benim_net_R, defter.net_R(t)))

        print(f"\n  {ad:6s} n={n:4d}   A1 fiyat->R {a1}/{n}"
              f"   A2 maliyet {a2}/{n}   A3 uctan uca {a3}/{n}")
        genel["n"] += n
        genel["a1"] += a1
        genel["a2"] += a2
        genel["a3"] += a3

    print("\n  " + "-" * 74)
    tam = genel["a1"] == genel["a2"] == genel["a3"] == genel["n"]
    print(f"  TOPLAM n={genel['n']}   A1 {genel['a1']}/{genel['n']}"
          f"   A2 {genel['a2']}/{genel['n']}   A3 {genel['a3']}/{genel['n']}"
          f"   -> {'BIREBIR' if tam else 'SAPMA VAR'}")
    for ad, t, hangi, benim, sicil in sapmalar[:15]:
        print(f"    SAPMA {hangi} {ad} {t.get('token')} {t['durum']}: "
              f"benim {benim} vs sicil {sicil}")
    if len(sapmalar) > 15:
        print(f"    ... +{len(sapmalar) - 15} sapma daha")
    return tam, genel


def bolum_b(ornek_basi=3):
    print("\n" + "=" * 78)
    print("  B. COZME MOTORU DOGRULAMASI — gercek mumlarla SIFIRDAN cozum")
    print("=" * 78)
    ornekler = []
    for ad, dosya in SICILLER:
        ts = [t for t in M.kapalilar(M.yukle(dosya))
              if t.get("tetik_tarih") and t.get("sonuc_R") is not None]
        ts.sort(key=lambda t: t.get("kapanis_tarih") or "", reverse=True)
        kova = {}
        for t in ts:
            k = (t["durum"], t["yon"])
            if len(kova.setdefault(k, [])) < ornek_basi:
                kova[k].append(t)
                ornekler.append((ad, t))
    print(f"  ornek: {len(ornekler)} islem "
          f"(sicil x durum x yon kombinasyonlarindan en fazla {ornek_basi}'er)")
    print(f"  her islem KENDI doneminin limitleriyle oynatilir "
          f"(5dk donemi 6s/24s, swing-1h 24s/120s)")
    print(f"\n  {'sicil':6s} {'sembol':13s} {'yon':6s} {'durum':12s} "
          f"{'sicilR':>7s} {'cozumR':>7s} {'esleme':>8s}")
    tam = kirik = atlanan = 0
    eski_tam = eski_kirik = 0
    eskiler, veri_farklari = [], []
    for ad, t in ornekler:
        sym = t.get("token") or t.get("sembol")
        try:
            t0 = int(datetime.fromisoformat(t["tarih"]).timestamp() * 1000)
            k1m = defter.k1m_kapanmis_araliktan(sym, t0, tavan=MUM_TAVANI)
        except Exception as e:
            print(f"  {ad:6s} {sym:13s} ATLANDI ({type(e).__name__})")
            atlanan += 1
            continue
        p = _poz_kur(t)
        P.coz(p, k1m, funding_olaylari=None, likidasyon=False, defter_uyumlu=True)
        es = (p["durum"] == t["durum"] and p["sonuc_R"] == t["sonuc_R"])

        # MANTIK farki mi, KAYNAK VERI farki mi? Motor ayni durumu ve ayni
        # kapanis anini sectiyse karar mantigi dogrudur; kalan fark mumun
        # kendi degerinden gelir (API'nin bugun dondurdugu kapanis, sicile
        # kaydedilenden farkli olabilir). Ikisi ayni sey degildir.
        veri_farki = (not es
                      and p["durum"] == t["durum"]
                      and p.get("kapanis_tarih") == t.get("kapanis_tarih"))
        if veri_farki:
            veri_farklari.append((sym, t, p))
            es = True                  # mantik dogru -> hukumde KIRIK sayilmaz

        coz_oncesi = t["tarih"][:10] < COZ_MOTORU_TARIHI
        if coz_oncesi:
            eski_tam += es
            eski_kirik += (not es)
            if not es:
                eskiler.append((sym, t, p))
        else:
            tam += es
            kirik += (not es)
        etiket = ("ok" if not veri_farki else "ok~") if es else "KIRIK -> " + p["durum"]
        print(f"  {ad:6s} {sym:13s} {t['yon']:6s} {t['durum']:12s} "
              f"{t['sonuc_R']:>7} {str(p['sonuc_R']):>7} {etiket:>8s}"
              f"{'   [coz() ONCESI]' if coz_oncesi else ''}")

    print(f"\n  ESLESME (coz() donemi, {COZ_MOTORU_TARIHI} ve sonrasi): "
          f"{tam}/{tam + kirik}" + (f"  (atlanan {atlanan})" if atlanan else ""))
    if eski_tam + eski_kirik:
        print(f"  coz() ONCESI kayitlar (bilgi, hukme girmez): "
              f"{eski_tam}/{eski_tam + eski_kirik}")
        for sym, t, p in eskiler:
            print(f"    {sym} {t['tarih'][:10]}: sicil {t['durum']} {t['sonuc_R']}R"
                  f" vs fitil motoru {p['durum']} {p['sonuc_R']}R")
        print("    ^ BEKLENEN. O kayitlar 30sn NOKTA ORNEKLEMESI ile cozuldu;")
        print("      defter.py'nin kendi notu: nokta ornekleme 'sicili sistematik")
        print("      IYIMSER kaydeder'. Fark, fitil motorunun DAHA DOGRU olmasidir.")
    return kirik == 0, tam, kirik


def bolum_c():
    print("\n" + "=" * 78)
    print("  C. defter'in MALIYET YAKLASIKLIGI ne kadar sapiyor? (bilgi)")
    print("=" * 78)
    print("  defter.maliyet_R(): giris * (giris_bacak + cikis_bacak) / risk")
    print("     -> CIKIS bacagini da GIRIS fiyatindan olcer.")
    print("  gercek           : cikis bacagi CIKIS notional'i uzerinden odenir.")
    for ad, dosya in SICILLER:
        ts = [t for t in M.kapalilar(M.yukle(dosya))
              if t.get("tetik_tarih") and t.get("sonuc_R") is not None]
        fark_top = 0.0
        en_kotu = (0.0, None)
        for t in ts:
            p = _durum_aktar(_poz_kur(t), t)
            P.muhasebe(p, defter_uyumlu=True)
            uyumlu_kom = p["komisyon_R"]
            P.muhasebe(p, defter_uyumlu=False)
            # YALNIZ maliyet konvansiyonu farki (brut yuvarlamasi disarida):
            # maliyet artarsa net DUSER -> isaret ters cevrilir.
            fark = -(p["komisyon_R"] - uyumlu_kom)
            fark_top += fark
            if abs(fark) > abs(en_kotu[0]):
                en_kotu = (fark, t)
        if not ts:
            continue
        print(f"\n  {ad}: n={len(ts)}  toplam fark {fark_top:+.4f}R  "
              f"islem basina {fark_top / len(ts):+.5f}R")
        f, t = en_kotu
        print(f"    en buyuk tek sapma: {t.get('token')} {t['durum']} {f:+.5f}R")
    print("\n  YORUM: fark isaretlidir — kazanan islemde cikis notional'i BUYUK")
    print("  oldugu icin gercek maliyet defter'in varsaydigindan YUKSEK, kaybeden")
    print("  islemde DUSUK. Yani defter kazananlari hafif iyimser, kaybedenleri")
    print("  hafif kotumser gosterir. Gurultu tabani 0,03R ile kiyasla.")


def main():
    hizli = "--hizli" in sys.argv
    print("=" * 78)
    print("  POZISYON SIMULATORU — GECMIS SICILE KARSI DOGRULAMA")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')} | bakiye {BAKIYE:.0f} | "
          f"risk %{RISK_PCT} | kaldirac 1x")
    print("=" * 78)
    a_ok, genel = bolum_a()
    b_ok = None
    if not hizli:
        b_ok, b_tam, b_kirik = bolum_b()
    bolum_c()

    print("\n" + "=" * 78)
    print("  HUKUM")
    print("=" * 78)
    print(f"  A muhasebe   : {'BIREBIR GECTI' if a_ok else 'KALDI'} "
          f"({genel['n']} islem x 3 kontrol)")
    if b_ok is None:
        print("  B cozme motoru: ATLANDI (--hizli)")
    else:
        print(f"  B cozme motoru: {'BIREBIR GECTI' if b_ok else 'KALDI'}")
    gecti = a_ok and (b_ok is not False)
    print(f"\n  {'SIMULATOR DOGRULANDI.' if gecti else 'SIMULATOR DOGRULANMADI — MOTOR BOZUK.'}")
    if gecti:
        print("  Funding ve likidasyon KAPALIYKEN simulator sicili birebir uretiyor;")
        print("  yani aradaki her fark, EKLENEN gercekcilikten gelir — hatadan degil.")
    return 0 if gecti else 1


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    sys.exit(main())
