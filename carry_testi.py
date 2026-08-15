"""
carry_testi.py — NAKIT-TASIMA (cash-and-carry): TAHMIN ETMEDEN PARA ALMAK
================================================================================
NEDEN (2026-08-11 sistem analizi): Bugune kadar olculen 13 adayin HEPSI tek bir
aileye aitti — TAHMIN. Hepsi "fiyat bundan sonra ne yapacak?" diye soruyordu.
Sinyali 13 kez degistirdik, OYUNU hic degistirmedik. Ve tahmin, hiz/veri/sermaye
ustunlugumuzun olmadigi en kalabalik masa.

Bu test baska bir aileye ait: fiyat tahmini YOK.
    spot'tan AL  +  perp'ten SAT  (ayni miktar)
Fiyat ne yaparsa yapsin iki bacak birbirini goturur (birim bazinda tam notr).
Getiri, uzun tarafin kisa tarafa yaptigi ZORUNLU odemeden gelir: funding.

Ironi: funding'in yapisal tek-yonlulugunu aylardir goruyoruz (sistem 5:1 SHORT
uretiyor, cunku funding cogunlukla pozitif) ve onu TAHMIN sinyali sanip
kullanmaya calistik. Oysa o bir tahmin degil, bir GELIR AKISI.

MATEMATIK (birim bazinda: 1 spot long + 1 perp short):
    P&L = (S1-S0) + (P0-P1) = baz0 - baz1        (baz = perp - spot)
    + her 8 saatte funding_orani x perp_notional  (kisa taraf ALIR, oran pozitifse)
Delta-notr TAM saglanir; yeniden dengeleme P&L icin GEREKMEZ (yalniz teminat
yonetimi icin gerekir). Bu yuzden "dengelemedik" bir sapma yaratmaz.

ON-KAYIT (kosmadan once sabit):
  A) HEP-ACIK      : 540 gun boyunca tut, tum funding'i topla, 4 bacak maliyet
  B) SECICI        : yalniz onceki 30 gun ortalama funding > 0 iken tut (haftalik karar)
  C) KESITSEL      : her hafta en yuksek funding'li 10 coini tut (devir maliyetli)
IDAM SARTLARI: net getiri SERMAYEYE gore pozitif olmali, HER IKI rejimde de
ayakta kalmali, ve en kotu cekilme katlanilabilir olmali.

⚠ DURUSTLUK SINIRLARI (bunlar ölçüme girmez, karari etkiler):
  - BORSA RISKI: iki bacak da Binance'te. FTX dersi — bu risk modellenmez.
  - TEMINAT: perp bacagi marj ister. Getiri SPOT NOTIONAL'a gore degil TOPLAM
    SERMAYEYE gore raporlanir (TEMINAT_KAT ile). Bu adim atlanirsa carry getirisi
    oolarak sisirilmis gorunur — literaturdeki en yaygin hata.
  - LIKIDASYON: perp bacagi yetersiz marjla tasfiye olabilir; modellenmedi.
  - Funding NEGATIFE doner (odeyen taraf olursun). Olculur ve raporlanir.
  - Hayatta kalma yanliligi: delist olanlar veride yok.

Calistirma: venv\\Scripts\\python.exe carry_testi.py
Canliya DOKUNMAZ.
"""
import bisect
import json
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

import olcucu
import backtest
import ileritest
import kesitsel_test

GUN = 540
EVREN_N = 30                  # spot+perp kesisiminden en likit N coin
KESITSEL_K = 10               # C stratejisinde tutulan coin sayisi
FUND_PENCERE = 30             # gun — secici/kesitsel karar penceresi (SADECE gecmis)
DENGELEME = 7                 # gun — B ve C icin karar araligi
TEMINAT_KAT = 1.5             # toplam sermaye = spot notional x bu (perp marji dahil)
TREND_GUN = 200               # BTC rejim SMA

# Maliyet: spot ve perp AYRI tarifeler (spot taker daha PAHALI — atlanmasi yaygin hata)
SPOT_TAKER = 0.001 * 0.75 + 0.0002      # %0.1 taker x BNB indirimi + kayma
PERP_TAKER = backtest._bacak(True)      # %0.05 x 0.90 + kayma
GIRIS_CIKIS = 2 * (SPOT_TAKER + PERP_TAKER)   # 4 bacak (gir + cik)

CACHE = Path(__file__).parent / "_cache"
GUN_MS = 86_400_000
SPOT_BASE = "https://api.binance.com"


# ============================== veri ==============================
def _cache_json(ad, uret):
    p = CACHE / f"{ad}.json"
    bugun = datetime.now(timezone.utc).date().isoformat()
    if p.exists():
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            if d.get("gun") == bugun:
                return d["veri"]
        except Exception:
            pass
    v = uret()
    CACHE.mkdir(exist_ok=True)
    try:
        p.write_text(json.dumps({"gun": bugun, "veri": v}), encoding="utf-8")
    except Exception:
        pass
    return v


def spot_semboller():
    def uret():
        d = requests.get(SPOT_BASE + "/api/v3/exchangeInfo", timeout=40).json()
        return sorted({s["symbol"] for s in d["symbols"]
                       if s.get("status") == "TRADING" and s.get("quoteAsset") == "USDT"})
    return set(_cache_json("spot_semboller", uret))


def spot_gunluk(syms):
    def uret():
        out = {}
        for i, s in enumerate(syms, 1):
            try:
                r = requests.get(SPOT_BASE + "/api/v3/klines", timeout=30,
                                 params={"symbol": s, "interval": "1d", "limit": 1000})
                if r.status_code == 200:
                    out[s] = {str(k[0] // GUN_MS): float(k[4]) for k in r.json()}
            except Exception:
                pass
            time.sleep(0.15)
            if i % 10 == 0:
                print(f"    spot {i}/{len(syms)} ...", flush=True)
        return out
    d = _cache_json(f"spot_{GUN}g", uret)
    return {s: {int(g): v for g, v in m.items()} for s, m in d.items()}


def funding_serileri(syms):
    def uret():
        out = {}
        for i, s in enumerate(syms, 1):
            try:
                ts, fr = ileritest.funding_serisi_gun(s, GUN)
                out[s] = [list(ts), list(fr)]
            except Exception:
                pass
            time.sleep(0.3)
            if i % 10 == 0:
                print(f"    funding {i}/{len(syms)} ...", flush=True)
        return out
    return _cache_json(f"funding_{GUN}g", uret)


# ============================== olcum ==============================
def seri_kur(sym, perp, spot, fts, ffr, g0, g1):
    """Gunluk kumulatif carry getirisi (spot notional'a gore, maliyet HARIC).
    [(gun, kum_getiri, gunluk_funding)] — baz P&L + toplanan funding."""
    S0 = spot.get(g0)
    P0 = perp.get(g0, (None,))[0]
    if not S0 or not P0:
        return None
    baz0 = (P0 - S0) / S0
    kum_f = 0.0
    out = []
    fi = 0
    for g in range(g0, g1 + 1):
        S = spot.get(g)
        P = perp.get(g, (None,))[0]
        if not S or not P:
            continue
        t_son = (g + 1) * GUN_MS
        gun_f = 0.0
        while fi < len(fts) and fts[fi] < t_son:
            if fts[fi] >= g0 * GUN_MS:
                gun_f += ffr[fi] * (P / S0)     # kisa taraf ALIR (oran pozitifse)
            fi += 1
        kum_f += gun_f
        baz = (P - S) / S0
        out.append((g, kum_f + (baz0 - baz), gun_f))
    return out


def _yillik(net, gun):
    return net / (gun / 365.0) * 100 if gun else 0.0


def _cekilme(seri):
    tepe, en = -10 ** 9, 0.0
    for _, v, _ in seri:
        tepe = max(tepe, v)
        en = min(en, v - tepe)
    return en * 100


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    print("=" * 96)
    print("  NAKIT-TASIMA (cash-and-carry) — TAHMIN YOK, ODEME VAR")
    print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} | {GUN} gun | "
          f"spot LONG + perp SHORT")
    print(f"  maliyet: spot taker %{SPOT_TAKER*100:.3f} | perp taker %{PERP_TAKER*100:.3f}"
          f" -> gir+cik 4 bacak %{GIRIS_CIKIS*100:.3f}")
    print(f"  sermaye varsayimi: spot notional x {TEMINAT_KAT} (perp marji dahil)")
    print("=" * 96)

    perp = kesitsel_test.veri_getir()
    spot_var = spot_semboller()
    tum = sorted({g for m in perp.values() for g in m})
    g_son = tum[-1]
    g_ilk = g_son - GUN

    aday = []
    for s, m in perp.items():
        if s not in spot_var or g_ilk not in m:
            continue
        hac = [m[g][1] for g in range(g_ilk - 30, g_ilk) if g in m]
        if len(hac) < 25:
            continue
        aday.append((s, statistics.median(hac)))
    aday.sort(key=lambda x: -x[1])
    syms = [s for s, _ in aday[:EVREN_N]]
    print(f"\n  spot+perp kesisimi: {len(aday)} coin -> en likit {len(syms)} alindi")
    print(f"  {', '.join(syms[:12])} ...")

    print("\n  veri cekiliyor (gunluk onbellekli) ...", flush=True)
    spot = spot_gunluk(syms)
    fund = funding_serileri(syms)

    # BTC rejim
    rejim = kesitsel_test.rejim_haritasi(perp["BTCUSDT"])

    # ---------- A: HEP-ACIK ----------
    seriler = {}
    print("\n" + "=" * 96)
    print("  A) HEP-ACIK — 540 gun boyunca tut, tum funding'i topla")
    print("=" * 96)
    print(f"  {'coin':<12}{'gun':>6}{'funding%':>11}{'baz P&L%':>11}{'brut%':>9}"
          f"{'net%':>9}{'yillik%':>10}{'neg.oran':>10}")
    satirlar = []
    for s in syms:
        if s not in spot or s not in fund:
            continue
        fts, ffr = fund[s]
        ort = [g for g in spot[s] if g in perp[s] and g_ilk <= g <= g_son]
        if len(ort) < GUN * 0.8:
            continue
        seri = seri_kur(s, perp[s], spot[s], fts, ffr, min(ort), max(ort))
        if not seri or len(seri) < 100:
            continue
        seriler[s] = seri
        gun_sayi = seri[-1][0] - seri[0][0]
        f_top = sum(x[2] for x in seri)
        brut = seri[-1][1]
        net = brut - GIRIS_CIKIS
        neg = sum(1 for t, r in zip(fts, ffr) if r < 0 and t >= g_ilk * GUN_MS)
        top = sum(1 for t in fts if t >= g_ilk * GUN_MS)
        satirlar.append((s, gun_sayi, f_top * 100, (brut - f_top) * 100, brut * 100,
                         net * 100, _yillik(net, gun_sayi) / TEMINAT_KAT,
                         neg / top * 100 if top else 0))
    satirlar.sort(key=lambda x: -x[6])
    for r in satirlar:
        print(f"  {r[0]:<12}{r[1]:>6}{r[2]:>+11.2f}{r[3]:>+11.2f}{r[4]:>+9.2f}"
              f"{r[5]:>+9.2f}{r[6]:>+10.2f}{r[7]:>9.0f}%")

    if not satirlar:
        print("  veri yok")
        return

    # esit agirlikli portfoy
    ortak = sorted(set.intersection(*[{x[0] for x in s} for s in seriler.values()]))
    port = []
    for g in ortak:
        v = [dict((x[0], x[1]) for x in s)[g] for s in seriler.values()]
        gf = [dict((x[0], x[2]) for x in s)[g] for s in seriler.values()]
        port.append((g, sum(v) / len(v), sum(gf) / len(gf)))
    p_gun = port[-1][0] - port[0][0]
    p_net = port[-1][1] - GIRIS_CIKIS
    p_yil = _yillik(p_net, p_gun) / TEMINAT_KAT
    print(f"\n  ESIT AGIRLIKLI PORTFOY ({len(seriler)} coin, {p_gun} gun):")
    print(f"    brut {port[-1][1]*100:+.2f}% | maliyet -{GIRIS_CIKIS*100:.2f}%"
          f" | net {p_net*100:+.2f}%")
    print(f"    SERMAYEYE gore yillik: {p_yil:+.2f}%   (teminat kat {TEMINAT_KAT})")
    print(f"    en kotu cekilme: {_cekilme(port):.2f}%")

    # rejim ayrimi
    print(f"\n  REJIM AYRIMI (gunluk funding ortalamasi, yillik %):")
    for rej in ("BOGA", "AYI"):
        v = [x[2] for x in port if rejim.get(x[0]) == rej]
        if v:
            print(f"    {rej:<6} {len(v):>4} gun | funding {sum(v)/len(v)*365*100:>+7.2f}%/yil")

    # ---------- B ve C: secici / kesitsel ----------
    print("\n" + "=" * 96)
    print(f"  B) SECICI (onceki {FUND_PENCERE}g ort. funding > 0 ise tut)  ve")
    print(f"  C) KESITSEL (her {DENGELEME} gunde en yuksek funding'li {KESITSEL_K} coin)")
    print("=" * 96)
    gunluk_f = {s: dict((x[0], x[2]) for x in seri) for s, seri in seriler.items()}
    b_top = c_top = 0.0
    b_dev = c_dev = 0
    onceki_c = set()
    n_karar = 0
    for g in range(ortak[0] + FUND_PENCERE, ortak[-1] - DENGELEME, DENGELEME):
        skor = {}
        for s, m in gunluk_f.items():
            gec = [m[x] for x in range(g - FUND_PENCERE, g) if x in m]
            if len(gec) >= FUND_PENCERE * 0.8:
                skor[s] = sum(gec) / len(gec)
        if not skor:
            continue
        n_karar += 1
        # B: pozitif olanlari tut
        b_sec = {s for s, v in skor.items() if v > 0}
        # C: en yuksek K
        c_sec = set(sorted(skor, key=lambda s: -skor[s])[:KESITSEL_K])
        for s_set, ad in ((b_sec, "b"), (c_sec, "c")):
            kaz = 0.0
            for s in s_set:
                kaz += sum(gunluk_f[s].get(x, 0) for x in range(g, g + DENGELEME))
            kaz = kaz / len(s_set) if s_set else 0.0
            if ad == "b":
                b_top += kaz
            else:
                c_top += kaz
        b_dev += len(b_sec)
        c_dev += len(c_sec - onceki_c)
        onceki_c = c_sec

    sure = ortak[-1] - ortak[0] - FUND_PENCERE
    c_mal = (c_dev / KESITSEL_K) * GIRIS_CIKIS      # her degisen uye gir+cik oder
    print(f"  {'strateji':<28}{'brut%':>10}{'devir mal.%':>13}{'net%':>10}{'yillik%(serm)':>15}")
    print(f"  {'B) secici (funding>0)':<28}{b_top*100:>+10.2f}{GIRIS_CIKIS*100:>13.2f}"
          f"{(b_top-GIRIS_CIKIS)*100:>+10.2f}"
          f"{_yillik(b_top-GIRIS_CIKIS, sure)/TEMINAT_KAT:>+15.2f}")
    print(f"  {'C) kesitsel ilk 10':<28}{c_top*100:>+10.2f}{c_mal*100:>13.2f}"
          f"{(c_top-c_mal)*100:>+10.2f}"
          f"{_yillik(c_top-c_mal, sure)/TEMINAT_KAT:>+15.2f}")
    print(f"\n  C devir: {n_karar} kararda toplam {c_dev} uye degisimi"
          f" -> dengeleme basina {c_dev/max(1,n_karar):.1f}/{KESITSEL_K}")

    print("\n" + "=" * 96)
    print("OKUMA:")
    print("  - Bu bir TAHMIN testi degil. Getiri fiyat yonunden degil, funding")
    print("    odemesinden geliyor. 13 adayin oldugu aileye ait DEGIL.")
    print(f"  - Getiriler SERMAYEYE gore (spot notional x {TEMINAT_KAT}). Yalniz notional'a")
    print("    gore raporlamak yaygin ve ciddi bir sisirmedir.")
    print("  - ⚠ Borsa riski (FTX dersi) ve perp bacagi likidasyon riski MODELLENMEDI.")
    print("    Sayi pozitif ciksa bile bu iki risk karari degistirebilir.")
    print("  - C'de devir maliyeti belirleyici: carry ince bir marj, sik dengeleme yer.")


if __name__ == "__main__":
    main()
