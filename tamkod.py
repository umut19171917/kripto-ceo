"""
tamkod.py — "KRIPTO TAM KOD" tek-dosya paketi uretici (2026-07-27)
================================================================================
Masaustune `kripto-tam-kod.md` yazar: sistemin GUNCEL tam tarifi + aday testi
sonuclari + yapilacaklar listesi + TUM kaynak kod + anlik JSON durumu.

Kullanim amaci: tek dosyada butun sistem — ikinci gorus almak, arsivlemek,
baska bir makineye tasimak, ya da uzun aradan sonra "sistem neydi" diye bakmak.

TEK KAYNAK ilkesi: anlati SISTEM.md'den, yapilacaklar hafiza defterinden OKUNUR
(elle kopyalanmaz) -> ikisi guncellenince bu dosya da guncel uretilir.

GUVENLIK: telegram.json / coinalyze.json (API anahtarlari) BILINCLI DISLANIR —
bu dosya paylasilabilir olmali. Kisisel sicil (kripto-defter.json) de gomulmez,
sadece OZETI yazilir (dosya sisirmesin + gizlilik).

Calistirma: venv\\Scripts\\python.exe tamkod.py   veya   tamkod.bat cift-tik
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJE = Path(__file__).parent
MASAUSTU = Path.home() / "Desktop"
CIKTI = MASAUSTU / "kripto-tam-kod.md"
HAFIZA = Path(r"C:\Users\KURTİ\.claude\projects\c--Users-KURT--Desktop-klas-rler-kripto\memory")

# Kaynak kod sirasi: cekirdekten cevreye (okuyan mantigi bu sirayla anlar)
KOD_SIRASI = [
    ("ÇEKİRDEK — veri + matematik + plan", ["olcucu.py", "kalibrasyon.py"]),
    ("KARAR KAPILARI — makro + rejim", ["makro.py", "rejim.py"]),
    ("SİCİL — tahmin kaydı + sonuç çözme", ["defter.py", "bosluk.py"]),
    ("CANLI DÖNGÜ", ["izleyici.py", "likidasyon.py", "bildirim.py"]),
    ("GENİŞ TARAMA — radar + tarayıcı", ["radar.py", "radar_defter.py", "tarayici.py"]),
    ("DOĞRULAMA ARAÇLARI", ["backtest.py", "ileritest.py", "ileritest2.py", "aday_testi.py"]),
    ("YARDIMCI", ["durum.py", "yedek.py", "tamkod.py"]),
]

# Anlik durum JSON'lari (ANAHTAR DOSYALARI YOK - bilincli)
JSON_DURUM = ["signals.json", "makro.json", "rejim.json", "esikler.json",
              "likidasyon-esik.json", "radar-durum.json"]


def _oku(p, sinir=None):
    try:
        s = Path(p).read_text(encoding="utf-8")
        if sinir and len(s) > sinir:
            s = s[:sinir] + f"\n... [KISALTILDI - tam hali: {p}]"
        return s
    except Exception as e:
        return f"[okunamadi: {type(e).__name__}]"


def sicil_ozeti():
    """Kisisel sicili GOMMEDEN ozet (gizlilik + dosya boyutu)."""
    try:
        sys.path.insert(0, str(PROJE))
        import defter, radar_defter
        a, r = defter.ozet(), radar_defter.ozet()
        return (f"- **Ana sicil (K2):** {a['acik']} açık, {a['kapali']} kapalı, "
                f"isabet %{a.get('isabet_pct')}, brüt {a['toplam_R']:+.2f}R / "
                f"**net {a['toplam_net_R']:+.2f}R**\n"
                f"- **Radar sicili:** {r['acik']} açık, {r['kapali']} kapalı, "
                f"isabet %{r.get('isabet_pct')}, net {r['toplam_net_R']:+.2f}R\n"
                + (f"- **Deneysel (LAB):** {a['deneysel']['kapali']} kapalı, "
                   f"net {a['deneysel']['toplam_net_R']:+.2f}R\n"
                   if a.get("deneysel") else ""))
    except Exception as e:
        return f"- [sicil özeti alınamadı: {type(e).__name__}]\n"


def uret():
    simdi = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    P = []
    P.append(f"""# KRİPTO SİSTEMİ — TAM KOD PAKETİ

> **Üretim:** {simdi} · `tamkod.py` ile otomatik üretildi (elle düzenleme, bir dahaki
> üretimde kaybolur — kalıcı değişiklik için `SISTEM.md` veya hafıza defterini güncelle).
> **Proje:** `c:\\Users\\KURTİ\\Desktop\\klasörler\\kripto` · **GitHub:** umut19171917/kripto-ceo
>
> **İÇİNDEKİLER**
> 1. Sistemin tam tarifi (mimari, karar mantığı, sicil, kapılar) — `SISTEM.md`'den
> 2. Yapılacaklar listesi (K2/K3/koşullu/açık sınırlar) — hafıza defterinden
> 3. Anlık sicil özeti
> 4. EK A — tüm kaynak kod
> 5. EK B — anlık çalışma-anı JSON durumu
>
> **GÜVENLİK:** API anahtarları (`telegram.json`, `coinalyze.json`) ve kişisel tahmin
> geçmişi (`kripto-defter.json`) bu dosyaya BİLİNÇLİ dahil edilmedi — paylaşılabilir olsun diye.

---

# BÖLÜM 1 — SİSTEMİN TAM TARİFİ

""")
    P.append(_oku(PROJE / "SISTEM.md"))

    P.append("\n\n---\n\n# BÖLÜM 2 — YAPILACAKLAR LİSTESİ (ertelenmiş işlerin tek adresi)\n\n")
    defter_md = _oku(HAFIZA / "bekleyen-isler-defteri.md")
    if defter_md.startswith("---"):          # frontmatter'i at (ic kullanim metadatasi)
        parcalar = defter_md.split("---", 2)
        defter_md = parcalar[2] if len(parcalar) > 2 else defter_md
    P.append(defter_md)

    P.append(f"\n\n---\n\n# BÖLÜM 3 — ANLIK SİCİL ÖZETİ ({simdi})\n\n")
    P.append(sicil_ozeti())
    P.append("\n> Tam sicil bu dosyada YOK (gizlilik). Detay için: `durum.py` çalıştır "
             "veya `radar-defteri.bat` ile tarayıcıda aç.\n")

    P.append("\n\n---\n\n# EK A — TÜM KAYNAK KOD\n")
    for baslik, dosyalar in KOD_SIRASI:
        P.append(f"\n## {baslik}\n")
        for d in dosyalar:
            yol = PROJE / d
            if not yol.exists():
                continue
            satir = len(yol.read_text(encoding="utf-8").splitlines())
            # 4 backtick: gomulen kaynak 3-backtick icerebilir (tamkod.py'nin kendisi
            # markdown uretiyor) -> uzun cit kisa citi yutar, render kirilmaz.
            P.append(f"\n### `{d}` ({satir} satır)\n\n" + "````python\n" + _oku(yol) + "\n````\n")

    P.append("\n\n---\n\n# EK B — ANLIK ÇALIŞMA-ANI DURUMU (JSON)\n")
    P.append("\n> Bu dosyalar kod tarafından sürekli yeniden üretilir; anlık fotoğraftır.\n")
    for j in JSON_DURUM:
        yol = PROJE / j
        if not yol.exists():
            continue
        P.append(f"\n### `{j}`\n\n" + "````json\n" + _oku(yol, sinir=6000) + "\n````\n")

    metin = "".join(P)
    CIKTI.write_text(metin, encoding="utf-8")
    return CIKTI, len(metin)


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    yol, boyut = uret()
    print(f"YAZILDI: {yol}")
    print(f"Boyut: {boyut/1024:.0f} KB ({len(yol.read_text(encoding='utf-8').splitlines())} satir)")
