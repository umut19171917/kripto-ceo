"""
fade_testi.py — FADE HIPOTEZININ 540 GUNLUK REJIM SINAVI (2026-08-10)
================================================================================
NEDEN: 2026-08-09'da `sinyal_tarama.py` likidasyon kademesinde FADE isareti buldu
(zorunlu satistan sonra fiyat sekiyor, doz-tepkili, zit isaretli). Tek zayifligi:
olcum 35 gunluk TEK rejimde yapildi ve o 35 gunun tamami dusen/testere piyasaydi
— yani "dususte al" fikrinin dogal olarak calistigi ortam.

Coinalyze probu (2026-08-10) gosterdi ki likidasyon gecmisi ~60-65 gunle sinirli;
540 gunluk rejim sinavi O VERIYLE IMKANSIZ. Ama hipotezin ozu likidasyona ait
degil: "sert ve zorunlu bir hareketten sonra fiyat geri doner." Likidasyon
kademesi bunun SEBEBI; gozlenebilir izi FIYATIN KENDISINDE. Fiyat verisi 540 gun
mevcut -> hipotezi fiyat uzerinden, boga ve ayi rejimlerini AYIRARAK sinariz.

SORU: "sert ters hareketten sonra fiyat geri doner" kurali 540 gun boyunca ve
FARKLI REJIMLERDE tutuyor mu, yoksa 2026 testeresine mi ozgu?

YONTEM (sinyal_tarama.py ile AYNI iskelet; olay tanimi degisti):
  sok = son W barlik getiri, sembolun KENDI onceki-donem dagiliminin uc kuyrugunda
  edge = kosullu ileri-getiri - kosulsuz taban (AYNI fold, AYNI sembol)
  Taban fold+sembol bazinda cikarilir: 540 gun boga ve ayi iceriyor, tek bir genel
  taban kullanmak surukleniyi edge sanmaya yol acardi.

SIZINTI YOK: her fold'un esigi SADECE onceki 166 gunden. Test gorulmemis dilimde.
(aday_testi.py / ileritest.py ile ayni walk-forward iskeleti, 12 fold.)

ON-KAYITLI BIRINCIL HUCRE: W=1s sok, P95 kademe, +4s ufuk.
  Gerekce: onceki likidasyon testinin manset hucresiyle AYNI (P95, +4s). Hucre
  sonucu gorduKTEN SONRA secilmedi. Diger 26 hucre SAGLAMLIK kontrolu olarak
  raporlanir, manset olarak DEGIL (B1 dersi: 32 hucreden en parlagini secmek
  coklu-karsilastirma tuzagidir).

DURUSTLUK:
  - Islem simulasyonu DEGIL. "Sinyalde bilgi var mi" sorusu. Maliyet cizgisi
    referans olarak basilir: edge komisyonu tasimiyorsa bilgi de olsa kullanilamaz.
  - Ileri-getiri pencereleri UST USTE biniyor -> p-degeri hesaplanmaz. Karar
    isaret tutarliligina (sembol/fold/rejim) ve doz-tepkiye bakar.
  - Ayni yondeki soklar arasinda max(W,4) barlik bekleme -> ayni olayi tekrar
    saymayi kirar.

Calistirma: venv\\Scripts\\python.exe fade_testi.py
Canliya DOKUNMAZ — sadece okur, hicbir sicile/ayara yazmaz.
"""
import bisect
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import olcucu
import backtest
from kalibrasyon import percentile

GUN = 540
KAL_GUN = 166                 # ilk esik penceresi (aday_testi ile ayni)
ADIM_GUN = 30
GUN_MS = 86_400_000

SOK_PENCERE = [1, 4, 12]      # bar (1h bar) — sokun hizi
UFUKLAR = [1, 4, 24]          # saat — sinyal_tarama ile AYNI

# ---- kademe bandi: "uc" (ilk kosu) / "orta" (eslenmis bolge) ----
# GEREKCE (2026-08-10, ilk kosudan SONRA eklendi ama sonuca bakilarak DEGIL):
# `ortusme_probu` bagimsiz olarak olctu ki likidasyon olaylari 5dk fiyat hareketi
# dagiliminin MEDYAN %77'sinde oturuyor — %20'si en sert %5'te, %27'si medyanin
# ALTINDA. Yani ilk kosunun P90/95/99 bandi, sinyalin fiilen YASADIGI bolgeyi hic
# olcmemis. Orta band bu bosluğu kapatir. Esik olcumden geliyor, sonuctan degil.
BANTLAR = {"uc": ([90, 95, 99], (1, 95, 4)),
           "orta": ([70, 80, 85], (1, 80, 4))}
BANT = sys.argv[sys.argv.index("--bant") + 1] if "--bant" in sys.argv else "uc"
KADEMELER, BIRINCIL = BANTLAR[BANT]

TREND_BAR = 1200              # ~50 gun saatlik SMA — rejim ayrimi (ileritest2 ile ayni ruh)
CACHE = Path(__file__).parent / "_cache"


# ============================== veri ==============================
def fiyat_getir(sym):
    """540g 1h klines — gunluk onbellekli. AYRI anahtar: aday_testi'nin funding
    onbellegine dokunmaz (bayat funding'e taze damga vurmak tuzak olurdu)."""
    p = CACHE / f"{sym}_fiyat{GUN}g.json"
    bugun = datetime.now(timezone.utc).date().isoformat()
    if p.exists():
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            if d.get("gun") == bugun:
                return d["K"]
        except Exception:
            pass
    K = backtest.klines_history(sym, "1h", GUN)
    CACHE.mkdir(exist_ok=True)
    try:
        p.write_text(json.dumps({"gun": bugun, "K": K}), encoding="utf-8")
    except Exception:
        pass
    return K


def trend_rejimi(K_btc):
    """{ts: "BOGA"/"AYI"} — BTC kendi 50 gunluk SMA'sinin ustunde mi?
    SADECE GECMIS barlar (i haric) -> sizinti yok."""
    out = {}
    c = [k["c"] for k in K_btc]
    if len(c) <= TREND_BAR:
        return out
    kum = sum(c[:TREND_BAR])                  # i=TREND_BAR icin onceki TREND_BAR bar
    for i in range(TREND_BAR, len(c)):
        if i > TREND_BAR:
            kum += c[i - 1] - c[i - 1 - TREND_BAR]
        out[K_btc[i]["t"]] = "BOGA" if c[i] > kum / TREND_BAR else "AYI"
    return out


# ============================== olcum ==============================
def _ort(x):
    return sum(x) / len(x) if x else None


def _yeni():
    return {"n": 0, "top": 0.0}


def _ekle(h, deger):
    h["n"] += 1
    h["top"] += deger


def _ort_h(h):
    return h["top"] / h["n"] if h["n"] else None


def sembol_isle(sym, K, rejim_map, t_ilk_fold, n_fold, kutu):
    """Bir sembolu gez; tum (W, kademe, ufuk) hucrelerine demeanlenmis katkiyi yaz.
    kutu: ic ice defaultdict yerine acikca kurulmus sozlukler (bkz. bos_kutu)."""
    n = len(K)
    ts = [k["t"] for k in K]
    cl = [k["c"] for k in K]

    fold = [int((t - t_ilk_fold) // (ADIM_GUN * GUN_MS)) for t in ts]

    # ileri-getiriler (%)
    fwd = {h: [None] * n for h in UFUKLAR}
    for h in UFUKLAR:
        F = fwd[h]
        for i in range(n - h):
            if cl[i]:
                F[i] = (cl[i + h] - cl[i]) / cl[i] * 100

    # --- 1. gecis: fold+sembol tabanlari (kosulsuz ortalama) ---
    taban = {}          # (f, h) -> [toplam, adet]
    for i in range(n):
        f = fold[i]
        if f < 0 or f >= n_fold:
            continue
        for h in UFUKLAR:
            v = fwd[h][i]
            if v is None:
                continue
            t = taban.setdefault((f, h), [0.0, 0])
            t[0] += v
            t[1] += 1
    tb = {k: (v[0] / v[1]) for k, v in taban.items() if v[1]}

    # --- 2. gecis: her sok penceresi icin esik + olay ---
    for W in SOK_PENCERE:
        r = [None] * n
        for i in range(W, n):
            if cl[i - W]:
                r[i] = (cl[i] - cl[i - W]) / cl[i - W] * 100

        # fold basina esikler: SADECE onceki KAL_GUN'den
        esik = {}
        for f in range(n_fold):
            t0 = t_ilk_fold + f * ADIM_GUN * GUN_MS
            onceki = sorted(r[i] for i in range(n)
                            if r[i] is not None and t0 - KAL_GUN * GUN_MS <= ts[i] < t0)
            if len(onceki) < 500:
                esik[f] = None
                continue
            esik[f] = {p: (percentile(onceki, 100 - p), percentile(onceki, p))
                       for p in KADEMELER}      # (dus_esigi, yuk_esigi)

        CD = max(W, 4)
        son = {p: {"dus": -10 ** 9, "yuk": -10 ** 9} for p in KADEMELER}
        for i in range(n):
            f = fold[i]
            if f < 0 or f >= n_fold or r[i] is None or esik.get(f) is None:
                continue
            rej = rejim_map.get(ts[i])
            for p in KADEMELER:
                d_e, y_e = esik[f][p]
                if d_e is None or y_e is None:
                    continue
                for yon, kosul in (("dus", r[i] <= d_e), ("yuk", r[i] >= y_e)):
                    if not kosul or i - son[p][yon] < CD:
                        continue
                    son[p][yon] = i
                    for h in UFUKLAR:
                        v = fwd[h][i]
                        b = tb.get((f, h))
                        if v is None or b is None:
                            continue
                        d = v - b                       # demeanlenmis katki = edge katkisi
                        anahtar = (W, p, h, yon)
                        _ekle(kutu["top"][anahtar], d)
                        _ekle(kutu["sym"][anahtar].setdefault(sym, _yeni()), d)
                        _ekle(kutu["fold"][anahtar].setdefault(f, _yeni()), d)
                        if rej:
                            _ekle(kutu["rejim"][anahtar].setdefault(rej, _yeni()), d)


def bos_kutu():
    anahtarlar = [(W, p, h, yon) for W in SOK_PENCERE for p in KADEMELER
                  for h in UFUKLAR for yon in ("dus", "yuk")]
    return {"top": {a: _yeni() for a in anahtarlar},
            "sym": {a: {} for a in anahtarlar},
            "fold": {a: {} for a in anahtarlar},
            "rejim": {a: {} for a in anahtarlar}}


# ============================== rapor ==============================
def yorumla(ed, ey):
    if ed is None or ey is None:
        return "—"
    if ed > 0 and ey < 0:
        return "FADE"
    if ed < 0 and ey > 0:
        return "DEVAM"
    return "karisik"


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    haric = set(getattr(olcucu, "DENEYSEL", set()))
    semboller = [s for s in olcucu.SYMBOLS if s not in haric]
    simdi = int(datetime.now(timezone.utc).timestamp() * 1000)
    t_ilk_fold = simdi - GUN * GUN_MS + KAL_GUN * GUN_MS
    n_fold = (GUN - KAL_GUN) // ADIM_GUN
    maliyet = backtest._bacak(True) * 2 * 100      # 2 taker bacak + kayma (%)

    print("=" * 96)
    print("  FADE HIPOTEZI — 540 GUNLUK REJIM SINAVI")
    print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} | 1h | "
          f"{n_fold} fold x {ADIM_GUN}g | esik penceresi {KAL_GUN}g (walk-forward)")
    print(f"  BAND: {BANT} (kademeler {KADEMELER})"
          + ("  <- likidasyon olaylarinin oturdugu bolge (medyan P77)" if BANT == "orta" else ""))
    print(f"  ON-KAYITLI BIRINCIL HUCRE: W={BIRINCIL[0]}s sok, P{BIRINCIL[1]}, +{BIRINCIL[2]}s ufuk")
    print(f"  gidis-donus maliyet cizgisi: %{maliyet:.3f} (2 taker bacak + kayma)")
    print(f"  HARIC (deneysel): {', '.join(sorted(haric)) or '—'}")
    print("=" * 96)

    print("\n  veri cekiliyor (ilk kosuda yavas, sonra gunluk onbellekli) ...")
    K_btc = fiyat_getir("BTCUSDT")
    rejim_map = trend_rejimi(K_btc)
    boga = sum(1 for v in rejim_map.values() if v == "BOGA")
    print(f"  BTC {len(K_btc):,} bar | trend rejimi {len(rejim_map):,} barda tanimli"
          f" | %{boga / max(1, len(rejim_map)) * 100:.0f} BOGA")

    kutu = bos_kutu()
    print(f"\n  {'sembol':<11}{'bar':>8}  {'kapsam'}")
    for sym in semboller:
        try:
            K = fiyat_getir(sym) if sym != "BTCUSDT" else K_btc
        except Exception as e:
            print(f"  {sym:<11}{'—':>8}  HATA {type(e).__name__} - atlandi", flush=True)
            continue
        if len(K) < (KAL_GUN + ADIM_GUN) * 24:
            print(f"  {sym:<11}{len(K):>8}  YETERSIZ gecmis - atlandi", flush=True)
            continue
        a = datetime.fromtimestamp(K[0]["t"] / 1000, timezone.utc).date()
        b = datetime.fromtimestamp(K[-1]["t"] / 1000, timezone.utc).date()
        print(f"  {sym:<11}{len(K):>8}  {a} -> {b}", flush=True)
        sembol_isle(sym, K, rejim_map, t_ilk_fold, n_fold, kutu)

    # ---------- doz-tepki ----------
    print("\n" + "=" * 96)
    print("  DOZ-TEPKI — kademe sertlestikce etki gucleniyor mu? (gercek etki gucleNMELI)")
    print("  FADE  = dus-sok EDGE pozitif VE yuk-sok EDGE negatif (zit isaretler)")
    print("  DEVAM = tersi | karisik = ayni isaret -> yon bilgisi degil ortak suruklenme")
    print("=" * 96)
    for W in SOK_PENCERE:
        for h in UFUKLAR:
            print(f"\n  --- sok penceresi {W}s | ufuk +{h}s ---")
            print(f"  {'kademe':<9}{'dus n':>8}{'dus EDGE':>11}{'yuk n':>8}"
                  f"{'yuk EDGE':>11}{'|ort|':>9}{'yorum':>10}")
            for p in KADEMELER:
                hd = kutu["top"][(W, p, h, "dus")]
                hy = kutu["top"][(W, p, h, "yuk")]
                ed, ey = _ort_h(hd), _ort_h(hy)
                if ed is None or ey is None:
                    print(f"  P{p:<8}{hd['n']:>8,}{'—':>11}{hy['n']:>8,}{'—':>11}{'—':>9}{'—':>10}")
                    continue
                ort = (abs(ed) + abs(ey)) / 2
                yildiz = " *" if (yorumla(ed, ey) == "FADE" and ort > maliyet) else ""
                print(f"  P{p:<8}{hd['n']:>8,}{ed:>+11.3f}{hy['n']:>8,}{ey:>+11.3f}"
                      f"{ort:>9.3f}{yorumla(ed, ey):>10}{yildiz}")

    # ---------- birincil hucre detayi ----------
    W0, p0, h0 = BIRINCIL
    print("\n" + "=" * 96)
    print(f"  BIRINCIL HUCRE DETAYI — W={W0}s, P{p0}, +{h0}s (ON-KAYITLI)")
    print("=" * 96)
    ad = (W0, p0, h0, "dus")
    ay = (W0, p0, h0, "yuk")
    ed, ey = _ort_h(kutu["top"][ad]), _ort_h(kutu["top"][ay])
    print(f"  toplam: dus n={kutu['top'][ad]['n']:,} EDGE {ed:+.3f}%"
          f" | yuk n={kutu['top'][ay]['n']:,} EDGE {ey:+.3f}%"
          f" | yorum {yorumla(ed, ey)}")
    print(f"  maliyet cizgisi %{maliyet:.3f} -> "
          f"dus {'ASIYOR' if ed and abs(ed) > maliyet else 'ALTINDA'}, "
          f"yuk {'ASIYOR' if ey and abs(ey) > maliyet else 'ALTINDA'}")

    print(f"\n  --- REJIM AYRIMI (asil soru: 2026 testeresine mi ozgu?) ---")
    print(f"  {'rejim':<8}{'dus n':>8}{'dus EDGE':>11}{'yuk n':>8}{'yuk EDGE':>11}{'yorum':>10}")
    for rej in ("BOGA", "AYI"):
        hd = kutu["rejim"][ad].get(rej, _yeni())
        hy = kutu["rejim"][ay].get(rej, _yeni())
        rd, ry = _ort_h(hd), _ort_h(hy)
        if rd is None or ry is None:
            print(f"  {rej:<8}{hd['n']:>8,}{'—':>11}{hy['n']:>8,}{'—':>11}{'—':>10}")
            continue
        print(f"  {rej:<8}{hd['n']:>8,}{rd:>+11.3f}{hy['n']:>8,}{ry:>+11.3f}"
              f"{yorumla(rd, ry):>10}")

    print(f"\n  --- SEMBOL TUTARLILIGI ---")
    print(f"  {'sembol':<11}{'dus n':>8}{'dus EDGE':>11}{'yuk n':>8}{'yuk EDGE':>11}{'yorum':>10}")
    say = 0
    tum = 0
    for sym in semboller:
        hd = kutu["sym"][ad].get(sym)
        hy = kutu["sym"][ay].get(sym)
        if not hd or not hy:
            continue
        sd, sy = _ort_h(hd), _ort_h(hy)
        y = yorumla(sd, sy)
        tum += 1
        if y == "FADE":
            say += 1
        print(f"  {sym:<11}{hd['n']:>8,}{sd:>+11.3f}{hy['n']:>8,}{sy:>+11.3f}{y:>10}")
    print(f"\n  -> {say}/{tum} sembolde FADE yonu (zit isaret) tutuyor")

    print(f"\n  --- FOLD DOKUMU (yogunlasma kontrolu — B1 dersi) ---")
    print(f"  {'dilim basi':<13}{'dus n':>8}{'dus EDGE':>11}{'yuk n':>8}{'yuk EDGE':>11}{'yorum':>10}")
    fade_fold = 0
    kat = []
    for f in range(n_fold):
        t0 = t_ilk_fold + f * ADIM_GUN * GUN_MS
        tar = datetime.fromtimestamp(t0 / 1000, timezone.utc).strftime("%Y-%m-%d")
        hd = kutu["fold"][ad].get(f, _yeni())
        hy = kutu["fold"][ay].get(f, _yeni())
        fd, fy = _ort_h(hd), _ort_h(hy)
        y = yorumla(fd, fy)
        if y == "FADE":
            fade_fold += 1
        kat.append(hd["top"] - hy["top"])       # fold'un toplam edge katkisi (dus - yuk)
        if fd is None or fy is None:
            print(f"  {tar:<13}{hd['n']:>8,}{'—':>11}{hy['n']:>8,}{'—':>11}{'—':>10}")
            continue
        print(f"  {tar:<13}{hd['n']:>8,}{fd:>+11.3f}{hy['n']:>8,}{fy:>+11.3f}{y:>10}")
    top_kat = sum(kat)
    enb = max(kat) if kat else 0
    pay = (enb / top_kat * 100) if top_kat > 0 else 0
    print(f"\n  -> {fade_fold}/{n_fold} fold'da FADE yonu")
    print(f"  -> yogunlasma: toplam katki {top_kat:+.1f} | en iyi fold {enb:+.1f} (%{pay:.0f})")

    print("\n" + "=" * 96)
    print("OKUMA:")
    print("  (1) REJIM AYRIMI belirleyici. Sadece AYI'da FADE cikiyorsa bulgu 'dusen")
    print("      piyasada al' demektir; boga rejiminde ne yapacagini bilmiyoruz.")
    print("  (2) Isaret ZIT olmali. Iki tarafta ayni isaret = ortak suruklenme.")
    print("  (3) DOZ-TEPKI sart: P90 -> P99 giderken etki buyumeli.")
    print(f"  (4) BUYUKLUK: |EDGE| < %{maliyet:.3f} ise bilgi olsa da islenemez.")
    print("  (5) Ust uste binen ufuklar -> p-degeri YOK; karar isaret tutarliligina bakar.")
    print("  (6) Bu test 'edge kanitlandi' demez; 'elenmedi, pahali testi hak ediyor' der.")


if __name__ == "__main__":
    main()
