"""
sicil_analiz.py — CANLI SICILIN KIRILIMLARI (B4 rejim-kumelenme + B6 monotonluk)
================================================================================
NEDEN: Temmuz'dan beri her yeni kayda REJIM DAMGASI isleniyor (rejim_durum,
korelasyon, vol_orani, etkin_min_skor) — "K2 gunu kayiplar nerede kumeleniyor
diye bakariz" diye. Bugune kadar HIC OKUNMADI. Bu arac okur.

Ayrica B6: skor <-> net_R monotonlugu. Eski monotonluk testi 5dk doneminden
kalmaydi; konfig swing-1h'e gecti, hic tekrarlanmadi.

EVREN: defter.ozet() ile AYNI kanonik suzgec — geri-doldurma ve deneysel HARIC.
(2026-08-15 dersi: bu suzgec atlaninca sicil ~2 katina sisiyor ve tum yorum kayiyor.)

⚠ ISTATISTIKSEL GUC UYARISI: ana sicilde ~58 kapali islem var. 4-5 kovaya
bolununce kova basina 10-15 kalir. Bu ORNEKLEM HICBIR SEYI KANITLAMAZ; amac
hipotez uretmek ve K2 gununde nereye bakilacagini belirlemek. Hicbir kirilim
tek basina parametre degistirmeye gerekce olamaz (B1 dersi).

Calistirma: venv\\Scripts\\python.exe sicil_analiz.py
Canliya DOKUNMAZ — sadece okur.
"""
import json
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

KOK = Path(__file__).parent
KAPALI = ("tp1", "tp2", "stop", "zaman_asimi")
KAZANC = ("tp1", "tp2")


def yukle(dosya):
    """defter.ozet() ile AYNI evren."""
    d = json.loads((KOK / dosya).read_text(encoding="utf-8"))
    return [t for t in d.get("tahminler", [])
            if t.get("kaynak", "canli") != "geri-doldurma" and t.get("sicil") != "deneysel"]


def kapalilar(kayitlar):
    return [k for k in kayitlar if k.get("durum") in KAPALI]


def _kazanc_mi(k):
    return k["durum"] in KAZANC or (k["durum"] == "zaman_asimi" and (k.get("sonuc_R") or 0) > 0)


def kova_raporu(kap, ad, anahtar_fn, sirala=None):
    """anahtar_fn(kayit) -> kova adi (None ise atlanir)."""
    kova = defaultdict(list)
    for k in kap:
        a = anahtar_fn(k)
        if a is not None:
            kova[a].append(k)
    if not kova:
        print(f"\n  {ad}: veri yok")
        return
    print(f"\n  --- {ad} ---")
    print(f"  {'kova':<26}{'islem':>7}{'isabet':>9}{'netR':>10}{'ortR':>9}{'medyanR':>10}")
    anahtarlar = sirala(kova) if sirala else sorted(kova)
    for a in anahtarlar:
        v = kova[a]
        r = [x.get("sonuc_R") or 0 for x in v]
        kz = sum(1 for x in v if _kazanc_mi(x))
        print(f"  {str(a):<26}{len(v):>7}{f'%{kz/len(v)*100:.0f}':>9}"
              f"{sum(r):>+10.2f}{sum(r)/len(v):>+9.3f}{statistics.median(r):>+10.3f}")


def _band(v, kenarlar, etiketler):
    if v is None:
        return None
    for e, et in zip(kenarlar, etiketler):
        if v < e:
            return et
    return etiketler[-1]


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print("=" * 92)
    print("  CANLI SICIL KIRILIMLARI — B4 rejim kumelenme + B6 monotonluk")
    print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("  ⚠ ORNEKLEM KUCUK: hipotez uretir, KANITLAMAZ. Tek basina parametre")
    print("    degistirmeye gerekce OLAMAZ (B1 dersi).")
    print("=" * 92)

    for dosya, ad in (("kripto-defter.json", "ANA SICIL"), ("radar-defter.json", "RADAR")):
        try:
            kay = yukle(dosya)
        except Exception as e:
            print(f"\n{ad}: okunamadi ({type(e).__name__})")
            continue
        kap = kapalilar(kay)
        r = [k.get("sonuc_R") or 0 for k in kap]
        kz = sum(1 for k in kap if _kazanc_mi(k))
        print("\n" + "=" * 92)
        print(f"  {ad} — {len(kap)} kapali | isabet %{kz/len(kap)*100:.0f} | "
              f"net {sum(r):+.2f}R | islem basina {sum(r)/len(kap):+.3f}R")
        print("=" * 92)

        # ---------- B4: REJIM KIRILIMLARI ----------
        kova_raporu(kap, "rejim durumu (damga)", lambda k: k.get("rejim_durum"))
        kova_raporu(kap, "makro kapisi", lambda k: k.get("makro_kapi"))
        kova_raporu(kap, "korelasyon bandi",
                    lambda k: _band(k.get("korelasyon"), [0.70, 0.80, 0.85],
                                    ["<0.70", "0.70-0.80", "0.80-0.85", ">=0.85"]))
        kova_raporu(kap, "BTC vol orani",
                    lambda k: _band(k.get("vol_orani"), [0.8, 1.0, 1.5],
                                    ["<0.8 (sakin)", "0.8-1.0", "1.0-1.5", ">=1.5 (oynak)"]))
        kova_raporu(kap, "yon", lambda k: k.get("yon"))
        kova_raporu(kap, "cikis bicimi", lambda k: k.get("durum"))

        # ---------- B6: MONOTONLUK ----------
        kova_raporu(kap, "SKOR kovasi (B6 monotonluk)",
                    lambda k: _band(k.get("skor"), [75, 85, 95],
                                    ["70-74", "75-84", "85-94", "95-100"]))
        skorlu = [(k.get("skor"), k.get("sonuc_R") or 0) for k in kap
                  if isinstance(k.get("skor"), (int, float))]
        if len(skorlu) >= 10:
            xs = [x for x, _ in skorlu]
            ys = [y for _, y in skorlu]
            mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
            pay = sum((a - mx) * (b - my) for a, b in skorlu)
            payda = (sum((a - mx) ** 2 for a in xs) * sum((b - my) ** 2 for b in ys)) ** 0.5
            rho = pay / payda if payda else 0
            print(f"\n  skor-netR korelasyonu: rho = {rho:+.3f} (n={len(skorlu)})")
            print(f"  -> {'skor yuksekken sonuc daha iyi' if rho > 0.15 else ('TERS iliski' if rho < -0.15 else 'iliski YOK (|rho|<0.15)')}")

        # ---------- zaman icinde ----------
        kova_raporu(kap, "ay", lambda k: (k.get("kapanis_tarih") or k.get("tarih") or "")[:7])

    print("\n" + "=" * 92)
    print("OKUMA:")
    print("  - Kova basina 10-15 islemde %20'lik isabet farki SANSTIR. Egilim ara,")
    print("    esik arama.")
    print("  - B6: rho ~ 0 ise skorun buyuklugu sonucla ilgisiz demektir — bu,")
    print("    skor_gucu.py'nin 964k kayitla buldugunun canli siciildeki karsiligidir.")
    print("  - Damgalar 2026-07 sonrasi kayitlarda var; oncekilerde bos cikabilir.")


if __name__ == "__main__":
    main()
