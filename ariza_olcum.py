"""
ariza_olcum.py — K2 GUNDEMI MADDE 6 ve 7: ARIZALARIN OLCUMU (2026-08-24)
================================================================================
Kullanici talimati: "olc, sonra 30 Agustos'u bekleyelim."
SALT OKUR. Hicbir dosyayi degistirmez, hicbir kodu duzeltmez. Kosan `radar-v2`
on kaydini ETKILEMEZ (dondurulmus dosyalara dokunmaz, yalniz gecmis veriyi okur).

--------------------------------------------------------------------------------
MADDE 6 — FUNDING BILESENI (test EDILEBILIR)
--------------------------------------------------------------------------------
`olcucu.squeeze_scores`:  if funding >= long_c: ls += 30
  ls = LONG-squeeze = "asagi risk" = SHORT sinyali.

YONTEM — VEKIL DEGIL, BIREBIR YENIDEN KURULUM:
  - `olcucu.get_funding` premiumIndex.lastFundingRate okur = SON ODENEN funding.
    O odemelerin tam gecmisi /fapi/v1/fundingRate'te duruyor.
  - `tarayici.kalibre` long_crowded = son 500 odemenin 85. persentili.
  Ikisi de tahmin ANINA GORE yeniden hesaplanabilir. Yani "bilesen atesledi mi"
  sorusu vekille degil, kodun yaptigi hesabin AYNISIYLA cevaplanir.

⚠ olcucu.log bu is icin OLU: funding yalniz ILK 33 satirda var (27 Haziran'da
  `olcucu.py --loop` kisa sure kosmus). Sonrasini `izleyici.py` yaziyor ve
  funding loglamiyor. API'den yeniden kurulum tek dogru yol.

⚠ SINIR: ANA sicil esikleri `kalibrasyon.py`den gelir (farkli pencere, ~166 gun);
  radar `tarayici.kalibre` kullanir (son 500 odeme). Burada ikisine de RADAR
  yontemi uygulanir -> radar icin BIREBIR, ana sicil icin YAKLASIK.

--------------------------------------------------------------------------------
MADDE 7 — L/S BILESENI (test EDILEMEZ — sebebi burada kayda geciyor)
--------------------------------------------------------------------------------
`ls_ratio` HICBIR YERDE SAKLANMIYOR: defterde yok, olcucu.log'da yok,
signals.json yalniz ANLIK durumu tutuyor, skor bilesenleri de saklanmiyor
(yalniz SS/LS toplami). Funding'den farkli olarak API gecmisi de yetersiz
(/futures/data/globalLongShortAccountRatio ~30 gun).

Yapilabilen: arizanin BUYUKLUGUNU bugunun evreninde olcmek (Bolum 7).
Yapilmasi gereken: ls_ratio'yu loglamaya baslamak -> ileriye donuk test acilir.

⚠ HIPOTEZ SAYACI: bu olcumler 22. ve 23. hipotezdir. Bonferroni esigi
  0.05/23 = 0.00217. Ham p bu esigin altinda degilse "anlamli" DENMEZ.

Calistirma: venv\\Scripts\\python.exe ariza_olcum.py
"""
import json
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

KOK = Path(__file__).parent
sys.path.insert(0, str(KOK))
import kalibrasyon as kal
import metrikler as M
import olcucu
import tarayici

FUNDING_TAVAN = 0.0001
HIPOTEZ_SAYISI = 23
BONFERRONI = 0.05 / HIPOTEZ_SAYISI


def _ts(s):
    d = datetime.fromisoformat(s.replace("Z", "+00:00"))
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def tahminler():
    out = []
    for ad, dosya in (("ANA", "kripto-defter.json"), ("RADAR", "radar-defter.json")):
        try:
            ham = json.loads((KOK / dosya).read_text(encoding="utf-8"))["tahminler"]
        except Exception:
            continue
        for t in ham:
            if t.get("kaynak", "canli") == "geri-doldurma" or t.get("sicil") == "deneysel":
                continue
            sym = t.get("token") or t.get("sembol")
            if sym and t.get("tarih"):
                out.append((ad, sym, _ts(t["tarih"]), t))
    return out


def funding_bilesen(kayitlar):
    """Her tahmin icin tahmin ANINDAKI funding + esikleri YENIDEN KURAR."""
    semboller = sorted({sym for _, sym, _, _ in kayitlar})
    print("  {} sembol icin funding gecmisi cekiliyor...".format(len(semboller)))
    gecmis, hata = {}, 0
    for j, sym in enumerate(semboller, 1):
        try:
            raw = olcucu._get("/fapi/v1/fundingRate", {"symbol": sym, "limit": 1000})
            gecmis[sym] = sorted((int(x["fundingTime"]), float(x["fundingRate"])) for x in raw)
        except Exception:
            hata += 1
        if j % 40 == 0:
            print("    {}/{}".format(j, len(semboller)))
    print("  cekildi: {} sembol ({} hata)".format(len(gecmis), hata))

    out = {}
    for i, (ad, sym, ts, t) in enumerate(kayitlar):
        h = gecmis.get(sym)
        if not h:
            continue
        t_ms = int(ts.timestamp() * 1000)
        onceki = [(tm, r) for tm, r in h if tm <= t_ms]
        if len(onceki) < 50:
            continue
        funding = onceki[-1][1]
        pencere = sorted(r for _, r in onceki[-500:])
        long_c = kal.percentile(pencere, 85)
        short_c = kal.percentile(pencere, 15)
        neutral = kal.percentile(pencere, 50)
        out[i] = {
            "funding": funding, "long_c": long_c, "short_c": short_c, "neutral": neutral,
            "ls_puan": 30 if funding >= long_c else (15 if funding > neutral else 0),
            "ss_puan": 30 if funding <= short_c else (15 if funding < neutral else 0),
            "tavanda": funding >= FUNDING_TAVAN - 1e-12,
            "esik_tavanda": long_c >= FUNDING_TAVAN - 1e-12,
        }
    return out


def _perm(a, b):
    return M.etiket_permutasyon(a, b) if a and b else (None, None)


def _hkm(p):
    if p is None:
        return "p yok"
    return "ESIGI GECIYOR" if p < BONFERRONI else "esigi GECMIYOR"


def _p_str(p):
    return "{:.5f}".format(p) if p is not None else "—"


def bolum_6(kayitlar, bil):
    print("=" * 78)
    print("  MADDE 6 — FUNDING BILESENI")
    print("  Ayrim: tahmin aninda  funding >= long_crowded  ATESLEDI mi (+30)?")
    print("  (+30 LONG-squeeze dalina gider = asagi risk = SHORT sinyali)")
    print("=" * 78)

    atesli, sonuk = [], []
    for i, (ad, sym, ts, t) in enumerate(kayitlar):
        b = bil.get(i)
        if not b:
            continue
        (atesli if b["ls_puan"] == 30 else sonuk).append((ad, sym, t, b))
    tot = len(atesli) + len(sonuk)
    print("")
    print("  yeniden kurulabilen tahmin: {} / {}".format(tot, len(kayitlar)))
    print("    +30 ATESLEDI : {}".format(len(atesli)))
    print("    ateslemedi   : {}".format(len(sonuk)))

    print("")
    print("  6a) MEKANIZMA — bilesen ateslediginde sinyal SHORT'a mi kayiyor?")
    print("    {:14s} {:>5s} {:>6s} {:>6s} {:>11s}".format("kume", "n", "LONG", "SHORT", "SHORT payi"))
    oran = {}
    for ad, kume in (("+30 ATESLEDI", atesli), ("ateslemedi", sonuk)):
        n = len(kume)
        if not n:
            continue
        sh = sum(1 for _, _, t, _ in kume if t.get("yon") == "SHORT")
        oran[ad] = sh / n
        print("    {:14s} {:5d} {:6d} {:6d} {:10.1f}%".format(ad, n, n - sh, sh, 100 * sh / n))
    if len(oran) == 2:
        a = [1.0 if t.get("yon") == "SHORT" else 0.0 for _, _, t, _ in atesli]
        b = [1.0 if t.get("yon") == "SHORT" else 0.0 for _, _, t, _ in sonuk]
        _, p = _perm(a, b)
        print("")
        print("    SHORT payi farki: {:+.1f} puan   permutasyon p = {}".format(
            100 * (oran["+30 ATESLEDI"] - oran["ateslemedi"]), _p_str(p)))
        print("    Bonferroni ({} hipotez) esigi {:.5f}  -> {}".format(
            HIPOTEZ_SAYISI, BONFERRONI, _hkm(p)))

    print("")
    print("  6b) ZARAR — bilesen ateslediginde sonuc daha mi kotu?")
    print("    {:14s} {:>5s} {:>9s} {:>11s} {:>22s}".format("kume", "n", "net R", "islem basi", "%95 GA"))
    Rs = {}
    for ad, kume in (("+30 ATESLEDI", atesli), ("ateslemedi", sonuk)):
        r = [x for x in (M.net_r(t) for _, _, t, _ in kume) if x is not None]
        Rs[ad] = r
        if len(r) < 2:
            print("    {:14s} {:5d}  (yetersiz)".format(ad, len(r)))
            continue
        ga = M.bootstrap_ga(r) if len(r) >= 10 else None
        gs = "[{:+.3f}, {:+.3f}]".format(ga[0], ga[1]) if ga else "n<10, aralik YOK"
        print("    {:14s} {:5d} {:+9.2f} {:+11.3f} {:>22s}".format(
            ad, len(r), sum(r), statistics.mean(r), gs))
    if all(len(Rs.get(k, [])) >= 2 for k in ("+30 ATESLEDI", "ateslemedi")):
        a, b = Rs["+30 ATESLEDI"], Rs["ateslemedi"]
        _, p = _perm(a, b)
        print("")
        print("    fark: {:+.3f}R/islem   permutasyon p = {}".format(
            statistics.mean(a) - statistics.mean(b), _p_str(p)))
        print("    Bonferroni esigi {:.5f}  -> {}".format(BONFERRONI, _hkm(p)))

    print("")
    print("  6c) ARIZANIN YAYGINLIGI — esik tavana ne siklikta yapisiyor?")
    if tot:
        hepsi = atesli + sonuk
        et = sum(1 for _, _, _, b in hepsi if b["esik_tavanda"])
        ft = sum(1 for _, _, _, b in hepsi if b["tavanda"])
        ik = sum(1 for _, _, _, b in hepsi if b["tavanda"] and b["esik_tavanda"])
        print("    long_crowded esigi TAVANDA    : {}/{} (%{:.0f})".format(et, tot, 100 * et / tot))
        print("    funding TAVANDA               : {}/{} (%{:.0f})".format(ft, tot, 100 * ft / tot))
        print("    IKISI BIRDEN (+30 kacinilmaz) : {}/{} (%{:.0f})".format(ik, tot, 100 * ik / tot))
    return atesli, sonuk


def bolum_7():
    print("")
    print("=" * 78)
    print("  MADDE 7 — L/S BILESENI")
    print("=" * 78)
    print("")
    print("  GECMISE DONUK TEST KURULAMIYOR.")
    print("    ls_ratio hicbir yerde saklanmiyor (defter/log/signals.json) ve")
    print("    funding'den farkli olarak API gecmisi de yetersiz (~30 gun).")
    print("    Bu bir VERI eksigi, yontem eksigi degil.")
    print("")
    print("  Yapilabilen: arizanin BUYUKLUGUNU bugunun evreninde olcmek.")
    print("  Kod: SHORT-squeeze  ls_ratio < 1.0  (+20)")
    print("       LONG-squeeze   ls_ratio > 1.5  (+20)")
    print("  Esikler KODA GOMULU; funding ve OI ise PERSENTILLE kalibre ediliyor.")
    print("")
    try:
        syms = [s for s, v in tarayici.evren(30_000_000)][:80]
    except Exception as e:
        print("  evren cekilemedi:", type(e).__name__)
        return
    vals = []
    for s in syms:
        try:
            r = olcucu.get_ls_ratio(s, "5m")
            if r:
                vals.append(r)
        except Exception:
            pass
    if len(vals) < 10:
        print("  yeterli veri yok")
        return
    vals.sort()
    n = len(vals)
    p15 = kal.percentile(vals, 15)
    p50 = kal.percentile(vals, 50)
    p85 = kal.percentile(vals, 85)
    alt = sum(1 for v in vals if v < 1.0)
    ust = sum(1 for v in vals if v > 1.5)
    print("  canli olcum: {} sembol".format(n))
    print("    medyan {:.2f} | 15.p {:.2f} | 85.p {:.2f} | min {:.2f} max {:.2f}".format(
        p50, p15, p85, min(vals), max(vals)))
    print("")
    print("  MEVCUT (koda gomulu) esiklerle:")
    print("    ls_ratio < 1.00 -> LONG sinyaline  +20 : {:3d} sembol (%{:.0f})".format(alt, 100 * alt / n))
    print("    ls_ratio > 1.50 -> SHORT sinyaline +20 : {:3d} sembol (%{:.0f})".format(ust, 100 * ust / n))
    if alt:
        print("    -> +20 puan SHORT sinyaline {:.1f} KAT daha sik gidiyor".format(ust / alt))
    print("")
    print("  PERSENTILLE kalibre edilseydi (funding/OI ile ayni mantik, 15/85):")
    a2 = sum(1 for v in vals if v < p15)
    u2 = sum(1 for v in vals if v > p85)
    print("    ls_ratio < {:.2f} -> LONG'a  +20 : {:3d} sembol (%{:.0f})".format(p15, a2, 100 * a2 / n))
    print("    ls_ratio > {:.2f} -> SHORT'a +20 : {:3d} sembol (%{:.0f})".format(p85, u2, 100 * u2 / n))
    print("    -> tanim geregi simetrik")


def main():
    print("=" * 78)
    print("  ARIZA OLCUMU — K2 gundemi madde 6 ve 7")
    print("  {} | SALT OKUR".format(datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")))
    print("  hipotez sayaci: {} | Bonferroni esigi {:.5f}".format(HIPOTEZ_SAYISI, BONFERRONI))
    print("=" * 78)
    kayitlar = tahminler()
    print("")
    print("  kanonik tahmin: {}".format(len(kayitlar)))
    bil = funding_bilesen(kayitlar)
    bolum_6(kayitlar, bil)
    bolum_7()
    print("")
    print("=" * 78)
    print("  HICBIR SEY DUZELTILMEDI. Bu bir OLCUMDUR.")
    print("  Duzeltme squeeze_scores'a dokunmayi gerektirir -> on kayit kapaninca.")
    print("=" * 78)


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    main()
