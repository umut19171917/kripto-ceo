"""
kesitsel_test.py — KESITSEL GORELI GUC (cross-sectional momentum) — 2026-08-10
================================================================================
NEDEN: Bugune kadar denenen HER aday ayni aileden — sikisma skoru, funding,
basis, seviye kirilimi, likidasyon, fade. Hepsi TEK COIN / ZAMAN SERISI sorusu
soruyor: "bu coin simdi hareket edecek mi?" Bu ailenin alti uyesi de curudu.

Bu test BASKA bir soru soruyor: "hangi coin hangisinden iyi?" — zamani degil
COINLERI karsilastirir. Girmedigimiz bolge.

KULLANICI SORUSUNUN DURUST HALI: "piyasa ayidayken boga yasayan coinleri bulup
ortak noktalarini arayalim" fikri, tahmin edilecek SONUCA gore orneklem secer
(payda kaybolur) -> bulunan sey "yukselen coin neye benzer"dir, "hangi coin
yukselecek" degil. Duzeltilmis hali: KAZANANLARI SECME, HER SEYI SIRALA.
Her tarihte tum evren gecmis veriyle siralanir; kazanan da kaybeden de
orneklemde kalir; siralamanin GELECEGI bilip bilmedigi olculur.

ON-KAYIT (kosmadan ONCE sabitlendi, sonuca gore degistirilmez):
  siralama penceresi   : 30 gun (gecmis getiri)
  ileri ufuk           : 7 gun (ust uste BINMEYEN pencereler)
  dilim                : 10 (desil)
  evren                : her tarihte, onceki 30 gunun MEDYAN hacmine gore ilk 100
  yon                  : ust desil - alt desil (POZITIF = momentum, hipotezimiz)
                         Negatif cikarsa bu "reversal" ailesidir — AYRI hipotez,
                         on-kayitli DEGIL, tek basina kanit sayilmaz.

IDAM KARARI (hepsini gecemezse aday OLUR, tekrar acilmaz):
  1. Ust-alt farki gidis-donus MALIYET cizgisini asmali
  2. HER IKI rejimde de ayni yonde olmali (BOGA ve AYI ayri ayri)
  3. Donemlerin COGUNDA ayni yonde olmali
  4. SIRAYA GORE MONOTON olmali (ust desil > orta > alt). Sadece ucta cikip
     ortada kaybolan etki gurultudur.

SIZINTI YOK: siralama, evren secimi ve rejim etiketi SADECE o tarihten ONCEKI
kapanmis gunluk mumlardan. Uydurulan/ogrenilen esik YOK — desil kesimi kuralla
tanimli, veriden ogrenilmiyor.

⚠ HAYATTA KALMA YANLILIGI: Binance'ten yalnizca BUGUN islem goren sozlesmeler
cekilebiliyor; pencere icinde delist olanlar goremiyoruz. Sonuc bu yuzden bir
UST SINIR'dir ve oyle okunmalidir. Rapor, pencerenin basinda kac sembolun var
oldugunu basar ki yanliligin buyuklugu gorunsun.

Calistirma: venv\\Scripts\\python.exe kesitsel_test.py
Canliya DOKUNMAZ — sadece okur.
"""
import json
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import olcucu
import backtest
import tarayici

# ---- ON-KAYITLI PARAMETRELER ----
GUN = 540                 # test penceresi
ISINMA = 220              # BTC 200g SMA + siralama penceresi icin on-yukleme
LOOKBACK = 30             # siralama penceresi (gun)
UFUK = 7                  # ileri getiri (gun) — ayni zamanda yeniden dengeleme araligi
DILIM = 10                # desil
EVREN_N = 100             # her tarihte en likit N coin
TREND_GUN = 200           # BTC rejim SMA (gunluk)

CACHE = Path(__file__).parent / "_cache"
GUN_MS = 86_400_000


# ============================== veri ==============================
def semboller():
    """Bugun islem goren PERPETUAL USDT sozlesmeleri (stablecoin'ler haric).
    ⚠ Delist olmuslar burada YOK — hayatta kalma yanliliginin kaynagi."""
    info = olcucu._get("/fapi/v1/exchangeInfo")
    return sorted({s["symbol"] for s in info["symbols"]
                   if s.get("contractType") == "PERPETUAL"
                   and s.get("quoteAsset") == "USDT"
                   and s.get("baseAsset") not in tarayici.STABLE_BASES
                   and s.get("status") == "TRADING"})


def _gunluk_cek(sym, n):
    raw = olcucu._get("/fapi/v1/klines",
                      {"symbol": sym, "interval": "1d", "limit": min(1500, n)})
    # idx: 0 openTime, 4 close, 7 quoteVolume
    return {k[0] // GUN_MS: (float(k[4]), float(k[7])) for k in raw}


def veri_getir():
    """{sym: {gun_idx: (kapanis, hacim)}} — gunluk onbellekli (tek dosya)."""
    p = CACHE / f"kesitsel_{GUN}g.json"
    bugun = datetime.now(timezone.utc).date().isoformat()
    if p.exists():
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            if d.get("gun") == bugun:
                return {s: {int(g): tuple(v) for g, v in m.items()}
                        for s, m in d["veri"].items()}
        except Exception:
            pass

    syms = semboller()
    print(f"  {len(syms)} sembol bulundu, gunluk mumlar cekiliyor ...", flush=True)
    out, hata = {}, 0
    for i, s in enumerate(syms, 1):
        try:
            m = _gunluk_cek(s, GUN + ISINMA)
            if m:
                out[s] = m
        except Exception:
            hata += 1
        if i % 50 == 0:
            print(f"    {i}/{len(syms)} ...", flush=True)
        time.sleep(0.2)          # agirlik limitini 1dk'ya yay
    print(f"  {len(out)} sembol cekildi ({hata} hata)", flush=True)

    CACHE.mkdir(exist_ok=True)
    try:
        p.write_text(json.dumps({"gun": bugun,
                                 "veri": {s: {str(g): list(v) for g, v in m.items()}
                                          for s, m in out.items()}}), encoding="utf-8")
    except Exception:
        pass
    return out


# ============================== olcum ==============================
def rejim_haritasi(btc):
    """{gun: "BOGA"/"AYI"} — BTC kendi 200 gunluk SMA'sinin ustunde mi (SADECE gecmis)."""
    gunler = sorted(btc)
    kap = [btc[g][0] for g in gunler]
    out = {}
    for i in range(TREND_GUN, len(gunler)):
        sma = sum(kap[i - TREND_GUN:i]) / TREND_GUN        # i HARIC -> sizinti yok
        out[gunler[i]] = "BOGA" if kap[i] > sma else "AYI"
    return out


def _medyan(x):
    return statistics.median(x) if x else 0.0


def olc(veri, rejim):
    """Her yeniden-dengeleme tarihinde evreni sirala, desillerin ileri getirisini topla."""
    tum_gun = sorted({g for m in veri.values() for g in m})
    son = tum_gun[-1]
    ilk_test = son - GUN

    kayit = []          # (gun, desil, sym, fwd, fwd_demean, rejim)
    devir = []          # ardisik tarihlerde ust/alt desil uyelik degisimi
    onceki = {}
    tarihler = []

    for d in range(ilk_test, son - UFUK + 1):
        if d not in rejim:
            continue
        if (d - ilk_test) % UFUK:            # ust uste BINMEYEN pencereler
            continue

        aday = []
        for s, m in veri.items():
            if d not in m or (d - LOOKBACK) not in m or (d + UFUK) not in m:
                continue
            c0, c_ge, c_il = m[d][0], m[d - LOOKBACK][0], m[d + UFUK][0]
            if c0 <= 0 or c_ge <= 0:
                continue
            hac = [m[g][1] for g in range(d - LOOKBACK + 1, d + 1) if g in m]
            if len(hac) < LOOKBACK * 0.8:
                continue
            aday.append((s, c0 / c_ge - 1.0, _medyan(hac), c_il / c0 - 1.0))
        if len(aday) < EVREN_N:
            continue

        evren = sorted(aday, key=lambda x: -x[2])[:EVREN_N]      # hacme gore ilk N
        evren.sort(key=lambda x: x[1])                            # gecmis getiriye gore artan
        ort_fwd = sum(x[3] for x in evren) / len(evren)           # o tarihin kesitsel ortalamasi
        rej = rejim[d]
        tarihler.append(d)

        bugun_uye = {}
        n = len(evren)
        for i, (s, gec, hac, fwd) in enumerate(evren):
            ds = min(DILIM - 1, i * DILIM // n)
            kayit.append((d, ds, s, fwd, fwd - ort_fwd, rej))
            if ds in (0, DILIM - 1):
                bugun_uye.setdefault(ds, set()).add(s)

        if onceki:
            for ds in (0, DILIM - 1):
                a, b = onceki.get(ds, set()), bugun_uye.get(ds, set())
                if a and b:
                    devir.append(1 - len(a & b) / len(b))
        onceki = bugun_uye

    return kayit, devir, tarihler


# ============================== rapor ==============================
def _ort(x):
    return sum(x) / len(x) if x else None


def desil_ozet(kayit, filtre=None):
    """{desil: (n, ort_fwd%, ort_demean%)}"""
    kova = {i: [] for i in range(DILIM)}
    for d, ds, s, fwd, dm, rej in kayit:
        if filtre and not filtre(d, rej):
            continue
        kova[ds].append((fwd, dm))
    out = {}
    for i in range(DILIM):
        v = kova[i]
        out[i] = (len(v), _ort([x[0] for x in v]), _ort([x[1] for x in v]))
    return out


def fark(ozet):
    """ust desil - alt desil (demeanlenmis, %)"""
    ust, alt = ozet[DILIM - 1][2], ozet[0][2]
    return None if ust is None or alt is None else (ust - alt) * 100


def tani(kayit, veri, ilk_test, tarihler):
    """TANI BOLUMU — buyuk bir sayi gordugumuzde SORULACAK sorular.
    GEREKCE (2026-08-11): ilk kosuda ust-alt farki +%4.5/hafta cikti. Bu rakam
    etkin bir piyasada inandirici degil; once OLCUMU sorgula, sonra bulguyu.
    Kripto getirileri asiri carpik: ORTALAMA birkac +%200'luk memecoin tarafindan
    tasinabilir. Medyan, tarih-bazinda isabet ve yogunlasma bunu aciga cikarir."""
    print("\n" + "=" * 96)
    print("  TANI — bu sayi gercek mi, birkac uc gozlem mi?")
    print("=" * 96)

    # 1) medyan vs ortalama
    kova = {i: [] for i in range(DILIM)}
    for d, ds, s, fwd, dm, rej in kayit:
        kova[ds].append(dm)
    print(f"  {'desil':<8}{'ortalama %':>13}{'MEDYAN %':>12}{'fark':>10}")
    for i in (0, DILIM // 2, DILIM - 1):
        v = sorted(kova[i])
        o, m = _ort(v) * 100, statistics.median(v) * 100
        ad = {0: "(alt)", DILIM - 1: "(ust)"}.get(i, "(orta)")
        print(f"  {str(i)+' '+ad:<8}{o:>+13.3f}{m:>+12.3f}{o-m:>+10.3f}")

    # 2) tarih bazinda: kac tarihte ust > alt?
    gun_fark = {}
    for d, ds, s, fwd, dm, rej in kayit:
        if ds in (0, DILIM - 1):
            gun_fark.setdefault(d, {0: [], DILIM - 1: []})[ds].append(fwd)
    farklar = [(_ort(v[DILIM - 1]) - _ort(v[0])) * 100
               for v in gun_fark.values() if v[0] and v[DILIM - 1]]
    poz = sum(1 for f in farklar if f > 0)
    farklar_s = sorted(farklar)
    print(f"\n  tarih bazinda ust-alt: {poz}/{len(farklar)} tarihte pozitif "
          f"(%{poz/len(farklar)*100:.0f})")
    print(f"    ortalama {_ort(farklar):+.3f}%  |  MEDYAN {statistics.median(farklar_s):+.3f}%"
          f"  |  en iyi tarih {farklar_s[-1]:+.1f}%  en kotu {farklar_s[0]:+.1f}%")

    # 3) yogunlasma: en iyi birkac tarih cikarilirsa ne kalir?
    top = sum(farklar)
    kalan3 = None
    for k in (1, 3, 5):
        kalan = sum(farklar_s[:-k])
        if k == 3:
            kalan3 = kalan
        print(f"    en iyi {k} tarih cikarilirsa: toplam {top:+.1f} -> {kalan:+.1f}"
              f"  (%{(top-kalan)/top*100:.0f}'i o {k} tarihten)")

    # 4) hayatta kalma kanali: pencere basinda VAR OLAN coinlerle tekrar
    eski_syms = {s for s, m in veri.items() if ilk_test in m}
    for ad, secim in (("pencere basinda VAR OLANLAR", lambda s: s in eski_syms),
                      ("pencere icinde LISTELENENLER", lambda s: s not in eski_syms)):
        k2 = [x for x in kayit if secim(x[2])]
        if not k2:
            continue
        kv = {i: [] for i in range(DILIM)}
        for d, ds, s, fwd, dm, rej in k2:
            kv[ds].append(dm)
        a, u = kv[0], kv[DILIM - 1]
        if not a or not u:
            continue
        print(f"\n  {ad}: n={len(k2):,}")
        print(f"    alt {_ort(a)*100:+.3f}%  ust {_ort(u)*100:+.3f}%"
              f"  ->  ust-alt {(_ort(u)-_ort(a))*100:+.3f}%"
              f"  (medyanlarla {(statistics.median(u)-statistics.median(a))*100:+.3f}%)")
    return {"toplam": top, "kalan3": kalan3, "tarih_poz": poz, "tarih_n": len(farklar),
            "medyan_ust": statistics.median(sorted(kova[DILIM - 1])) * 100}


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    bacak = backtest._bacak(True)                 # taker + kayma (oran)
    print("=" * 96)
    print("  KESITSEL GORELI GUC — 540 GUN, GENIS EVREN")
    print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} | gunluk mum")
    print(f"  ON-KAYIT: siralama {LOOKBACK}g | ufuk {UFUK}g (binmeyen) | {DILIM} desil"
          f" | evren: en likit {EVREN_N}")
    print(f"  HIPOTEZ: ust desil - alt desil > 0 (momentum). Negatif = reversal ailesi,")
    print(f"           ON-KAYITLI DEGIL, tek basina kanit sayilmaz.")
    print("=" * 96)

    veri = veri_getir()
    # EVREN modu: "tum" (varsayilan) | "eski" = yalnizca pencere basinda VAR OLAN semboller.
    # GEREKCE: "eski" bir ALT-ORNEKLEM ARAYISI DEGIL, KUSUR DUZELTMESIDIR — pencere icinde
    # listelenen coinler hayatta kalma yanliliginin girdigi kanaldir (yukselip delist olanlar
    # veride YOK, yukselip kalanlar VAR). Ayni on-kayitli sinav, temizlenmis evrende tekrar.
    mod = sys.argv[sys.argv.index("--evren") + 1] if "--evren" in sys.argv else "tum"
    if "BTCUSDT" not in veri:
        print("  BTCUSDT yok — rejim etiketi kurulamiyor, cikiliyor.")
        return
    rejim = rejim_haritasi(veri["BTCUSDT"])

    tum_gun = sorted({g for m in veri.values() for g in m})
    son, ilk_test = tum_gun[-1], tum_gun[-1] - GUN
    eski = sum(1 for m in veri.values() if ilk_test in m)
    print(f"\n  evren modu: {mod}")
    print(f"  evren: {len(veri)} sembol (bugun islem goren)")
    print(f"  bunlarin {eski} tanesi {GUN} gun once de vardi -> {len(veri) - eski} tanesi"
          f" pencere icinde LISTELENDI")
    print(f"  ⚠ pencere icinde DELIST olanlar goremiyoruz -> sonuc UST SINIR'dir")
    if mod == "eski":
        veri = {s: m for s, m in veri.items() if ilk_test in m}
        print(f"  -> KUSUR DUZELTMESI: yeni listelenenler cikarildi, {len(veri)} sembol kaldi")

    kayit, devir, tarihler = olc(veri, rejim)
    if not kayit:
        print("  yeterli veri yok")
        return
    d0 = datetime.fromtimestamp(tarihler[0] * 86400, timezone.utc).date()
    d1 = datetime.fromtimestamp(tarihler[-1] * 86400, timezone.utc).date()
    boga = sum(1 for d in tarihler if rejim[d] == "BOGA")
    print(f"  {len(tarihler)} yeniden-dengeleme tarihi | {d0} -> {d1}"
          f" | %{boga / len(tarihler) * 100:.0f} BOGA")
    print(f"  {len(kayit):,} coin-tarih gozlemi")

    # --- devir hizi + gercek maliyet ---
    ort_devir = _ort(devir) or 0.0
    # her dengelemede devir kadar pozisyon kapanip acilir = 2 taker bacagi
    mal_bacak = ort_devir * 2 * bacak * 100          # tek taraf, % / dengeleme
    mal_toplam = mal_bacak * 2                        # uzun + kisa bacak birlikte
    print(f"\n  devir hizi: her {UFUK} gunde desil uyeliginin %{ort_devir*100:.0f}'i degisiyor")
    print(f"  -> MALIYET CIZGISI: tek taraf %{mal_bacak:.3f} | ust-alt cifti "
          f"%{mal_toplam:.3f} (dengeleme basina)")

    # --- desil tablosu (monotonluk) ---
    ozet = desil_ozet(kayit)
    print("\n" + "=" * 96)
    print(f"  DESIL TABLOSU — {UFUK} gunluk ileri getiri (demean = o tarihin kesitsel ort. cikarilmis)")
    print("=" * 96)
    print(f"  {'desil':<8}{'aciklama':<22}{'n':>8}{'ham %':>10}{'demean %':>11}")
    for i in range(DILIM):
        n, ham, dm = ozet[i]
        ad = "en zayif (alt)" if i == 0 else ("en guclu (ust)" if i == DILIM - 1 else "")
        print(f"  {i:<8}{ad:<22}{n:>8,}{ham*100:>+10.3f}{dm*100:>+11.3f}")

    dm_seri = [ozet[i][2] for i in range(DILIM)]
    artis = sum(1 for i in range(DILIM - 1) if dm_seri[i + 1] > dm_seri[i])
    f_tum = fark(ozet)
    print(f"\n  ust - alt = {f_tum:+.3f}%  (maliyet cifti %{mal_toplam:.3f})")
    print(f"  monotonluk: {DILIM-1} adimin {artis}'inde artis "
          f"({'MONOTON' if artis >= DILIM - 2 else 'zikzak'})")

    # --- rejim ayrimi ---
    print("\n" + "=" * 96)
    print("  REJIM AYRIMI — ikisinde de ayni yonde mi?")
    print("=" * 96)
    print(f"  {'rejim':<10}{'tarih':>7}{'alt desil':>12}{'ust desil':>12}{'ust-alt':>11}")
    rej_fark = {}
    for rej in ("BOGA", "AYI"):
        oz = desil_ozet(kayit, lambda d, r, _r=rej: r == _r)
        n_t = sum(1 for d in tarihler if rejim[d] == rej)
        f = fark(oz)
        rej_fark[rej] = f
        if f is None:
            print(f"  {rej:<10}{n_t:>7}{'—':>12}{'—':>12}{'—':>11}")
            continue
        print(f"  {rej:<10}{n_t:>7}{oz[0][2]*100:>+12.3f}{oz[DILIM-1][2]*100:>+12.3f}{f:>+11.3f}")

    # --- donem ayrimi ---
    print("\n" + "=" * 96)
    print("  DONEM AYRIMI — yogunlasma kontrolu (B1 dersi)")
    print("=" * 96)
    blok = GUN // 6
    print(f"  {'donem':<26}{'tarih':>7}{'ust-alt':>11}")
    donem_f = []
    for b in range(6):
        g0, g1 = ilk_test + b * blok, ilk_test + (b + 1) * blok
        oz = desil_ozet(kayit, lambda d, r, a=g0, z=g1: a <= d < z)
        n_t = sum(1 for d in tarihler if g0 <= d < g1)
        f = fark(oz)
        t0 = datetime.fromtimestamp(g0 * 86400, timezone.utc).date()
        t1 = datetime.fromtimestamp(g1 * 86400, timezone.utc).date()
        if f is None or not n_t:
            print(f"  {str(t0)+' -> '+str(t1):<26}{n_t:>7}{'—':>11}")
            continue
        donem_f.append(f)
        print(f"  {str(t0)+' -> '+str(t1):<26}{n_t:>7}{f:>+11.3f}")

    tn = tani(kayit, veri, ilk_test, tarihler)

    # --- idam karari ---
    print("\n" + "=" * 96)
    print("  IDAM KARARI — dorduncusunu de gecemezse aday olur")
    print("=" * 96)
    yon = 1 if (f_tum or 0) > 0 else -1
    ayni_yon = sum(1 for f in donem_f if f * yon > 0)
    fb, fa = rej_fark.get("BOGA"), rej_fark.get("AYI")
    k1 = abs(f_tum) > mal_toplam
    k2 = (fb or 0) * yon > 0 and (fa or 0) * yon > 0
    k3 = ayni_yon > len(donem_f) / 2
    k4 = artis >= DILIM - 2 if yon > 0 else artis <= 1
    # SART 5 (2026-08-11 eklendi): B1'in yogunlasma dersi bu aracin resmi idam
    # sartlarinda YOKTU — eksikti. Basis hipotezi tam bu testte iki kez olmustu.
    # Etki bir avuc tarihten geliyorsa o etki degil, birkac olaydir.
    k5 = tn["kalan3"] is not None and tn["kalan3"] * yon > 0
    for ad, ok, detay in (
            ("1. maliyeti asiyor", k1, f"|{f_tum:+.3f}| vs %{mal_toplam:.3f}"),
            ("2. iki rejimde ayni yon", k2,
             f"BOGA {fb:+.3f} / AYI {fa:+.3f}" if fb is not None and fa is not None else "veri yok"),
            ("3. donemlerin cogunda", k3, f"{ayni_yon}/{len(donem_f)}"),
            ("4. siraya gore monoton", k4, f"{artis}/{DILIM-1} adimda artis"),
            ("5. en iyi 3 tarihsiz ayakta", k5,
             f"toplam {tn['toplam']:+.1f} -> {tn['kalan3']:+.1f}")):
        print(f"  {'GECTI ' if ok else 'KALDI '} {ad:<26} {detay}")
    hepsi = k1 and k2 and k3 and k4 and k5
    print(f"\n  HUKUM: {'ELENMEDI — pahali testi hak ediyor' if hepsi else 'ADAY OLDU'}")
    if yon < 0:
        print("  ⚠ YON NEGATIF: bu momentum degil REVERSAL. On-kayitli hipotez DEGILDI;")
        print("    bagimsiz dogrulama olmadan bulgu sayilmaz (fade dersi).")

    print("\nOKUMA:")
    print("  - Desil kesimi KURALLA tanimli, veriden ogrenilmiyor -> uydurma riski dusuk.")
    print("  - Ust uste binmeyen pencereler; yine de ayni tarihte tum coinler birlikte")
    print("    hareket eder -> tarih sayisi (dengeleme adedi) etkin ornek buyuklugudur.")
    print(f"  - ⚠ Hayatta kalma yanliligi: delist olanlar yok, sonuc UST SINIR.")
    print(f"  - ⚠ {EVREN_N} coinlik desil = {EVREN_N//DILIM} eszamanli pozisyon; ELLE")
    print("    isletilemez. Once etki var mi olculur, sonra dar hali (2-3 coin) sinanir.")


if __name__ == "__main__":
    main()
