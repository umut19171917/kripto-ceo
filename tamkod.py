"""
tamkod.py — "KRIPTO TAM KOD" tek-dosya paketi uretici (2026-07-27, rev 2026-08-17)
================================================================================
Masaustune `kripto-tam-kod.md` yazar: sistemin GUNCEL tam tarifi + yapilacaklar
listesi + anlik sicil ozeti + TUM kaynak kod + anlik JSON durumu + degisim gecmisi.

Kullanim amaci: tek dosyada butun sistem — ikinci gorus almak, arsivlemek,
baska bir makineye tasimak, ya da uzun aradan sonra "sistem neydi" diye bakmak.

TEK KAYNAK ilkesi: anlati SISTEM.md'den, yapilacaklar hafiza defterinden OKUNUR
(elle kopyalanmaz) -> ikisi guncellenince bu dosya da guncel uretilir.

--------------------------------------------------------------------------------
2026-08-17 REVIZYONU — SESSIZ EKSIK KAPATILDI
--------------------------------------------------------------------------------
Kusur: `KOD_SIRASI` elle yazilmis SABIT bir listeydi. Dosya eklendiginde liste
guncellenmezse dosya pakete SESSIZCE girmiyordu — ne hata, ne uyari.
Denetim (2026-08-17): diskte 31 .py, listede 19 -> 12 dosya / 2.783 satir pakete
GIRMIYORDU. Girmeyenler projenin KENAR ARAMA calismasinin TAMAMIYDI (skor_gucu,
sinyal_tarama, fade_testi, fade_kontrol, kesitsel_test, sinif_testi, carry_testi,
spread_olcum, sicil_analiz, fng_sinavi, funding_saati, _hat_testi).
Yani SISTEM.md §9.3-9.8'in anlattigi bulgulari ureten kodun hicbiri pakette yoktu:
anlati vardi, kaniti yoktu. (A1 kalibrasyon arizasiyla AYNI SINIF kusur.)

Duzeltme — allow-list yerine TARAMA + ARTIK YAKALAMA:
  - kaynak: klasordeki tum *.py taranir; KOD_SIRASI yalnizca OKUNABILIR SIRA verir.
    Sirada olmayan her dosya "SINIFLANDIRILMAMIS" basligina otomatik duser + uyari.
  - JSON: allow-list yerine DENY-LIST. Yeni durum dosyalari otomatik girer.
  - Deny-list bir siri kacirirsa diye SIZINTI GUARD'i: gercek sir DEGERLERI
    ciktida aranir; bulunursa dosya YAZILMAZ (fail-closed).

GUVENLIK / KAPSAM KURALI:
  GIRER  : sistemi tarif eden her sey — kod, baslaticilar, calisma-ani durumu,
           SISTEM.md, bekleyenler defteri, degisim gecmisi, kurulum dosyalari.
  GIRMEZ : sirlar (telegram.json, coinalyze.json) ve kisisel veri
           (kripto-defter.json, radar-defter.json, kullanici profili).
           Sicilden yalniz OZET yazilir.

Calistirma: venv\\Scripts\\python.exe tamkod.py   veya   tamkod.bat cift-tik
"""
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJE = Path(__file__).parent
MASAUSTU = Path.home() / "Desktop"
CIKTI = MASAUSTU / "kripto-tam-kod.md"
HAFIZA = Path(r"C:\Users\KURTİ\.claude\projects\c--Users-KURT--Desktop-klas-rler-kripto\memory")

# Kaynak kod SIRASI: cekirdekten cevreye (okuyan mantigi bu sirayla anlar).
# ⚠ Bu liste artik EKSIKSIZLIK icin degil, yalniz SIRA icin. Listede olmayan
#   dosyalar taramayla yakalanip sona eklenir (bkz. _kod_bolumleri).
KOD_SIRASI = [
    ("ÇEKİRDEK — veri + matematik + plan", ["olcucu.py", "kalibrasyon.py"]),
    ("KARAR KAPILARI — makro + rejim", ["makro.py", "rejim.py"]),
    ("SİCİL — tahmin kaydı + sonuç çözme", ["defter.py", "bosluk.py"]),
    ("CANLI DÖNGÜ", ["izleyici.py", "likidasyon.py", "bildirim.py"]),
    ("GENİŞ TARAMA — radar + tarayıcı", ["radar.py", "radar_defter.py", "tarayici.py"]),
    ("DOĞRULAMA ARAÇLARI — walk-forward iskeleti",
     ["backtest.py", "ileritest.py", "ileritest2.py", "aday_testi.py"]),
    ("KENAR ARAMA — 'sinyalde bilgi var mı?' (§9.3-9.7)",
     ["skor_gucu.py", "sinyal_tarama.py", "fade_testi.py", "fade_kontrol.py",
      "kesitsel_test.py", "carry_testi.py", "funding_saati.py"]),
    ("SINAV ARAÇLARI — tek değişkenli/ön-kayıtlı testler (§9.5, §9.8)",
     ["sinif_testi.py", "fng_sinavi.py", "spread_olcum.py", "sicil_analiz.py"]),
    ("YARDIMCI", ["durum.py", "yedek.py", "tamkod.py", "_hat_testi.py"]),
]

# JSON: DENY-LIST (allow-list degil) -> yeni durum dosyalari otomatik girer.
JSON_YASAK = {"telegram.json",        # API anahtari
              "coinalyze.json",       # API anahtari
              "kripto-defter.json",   # kisisel sicil
              "radar-defter.json"}    # kisisel sicil

# Baslaticilar: cift-tik bat'lar + Startup VBS'leri (otomatik baslama)
BASLATICILAR = ["calistir.bat", "surekli-calistir.bat", "canli-izleyici.bat", "durum.bat",
                "tarayici.bat", "radar-defteri.bat", "yedek.bat", "tamkod.bat", "hat-testi.bat"]
STARTUP = Path.home() / "AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup"
VBSLER = [STARTUP / "KriptoIzleyici.vbs", STARTUP / "KriptoRadar.vbs"]

# Kurulum/tanitim dosyalari (baska makinede kurulabilirlik icin)
KURULUM = [("requirements.txt", "text"), (".gitignore", "text")]

# BELGELER: .py tarafinda oldugu gibi ALLOW-LIST YERINE DENY-LIST (2026-08-18).
# Gerekce: 08-17 duzeltmesi yalniz .py tarafini kurtarmisti; .md tarafi HALA sabit
# listeydi ve ON-KAYIT-radar-v2.md gibi YENI BELGE TURLERI pakete hic girmiyordu.
# Ayni sessiz-eksik kusuru, ikinci bir kapidan. (Kullanici sordugunda bulundu.)
MD_YASAK = {"SISTEM.md",              # zaten BOLUM 1
            "SISTEM-DEVIR-LLM.md",    # 111 KB uretilmis artefakt, eskir
            "kripto-SKILL.md"}        # kullanici "dokunma" dedi; SISTEM.md yerini aldi


def _oku(p, sinir=None):
    try:
        s = Path(p).read_text(encoding="utf-8")
        if sinir and len(s) > sinir:
            s = s[:sinir] + f"\n... [KISALTILDI - tam hali: {p}]"
        return s
    except Exception as e:
        return f"[okunamadi: {type(e).__name__}]"


def _kod_bolumleri():
    """(bolumler, artik) — SIRA KOD_SIRASI'ndan, EKSIKSIZLIK taramadan.
    Listede olmayan hicbir .py sessizce dusemez."""
    diskte = sorted(p.name for p in PROJE.glob("*.py"))
    listeli = {d for _, ds in KOD_SIRASI for d in ds}
    artik = [d for d in diskte if d not in listeli]
    bolumler = [(b, [d for d in ds if (PROJE / d).exists()]) for b, ds in KOD_SIRASI]
    if artik:
        bolumler.append(("⚠ SINIFLANDIRILMAMIŞ — taramayla otomatik yakalandı", artik))
    return bolumler, artik


def _belge_dosyalari():
    """Proje .md belgeleri — DENY-LIST. Yeni belge türleri otomatik girer."""
    return sorted(p.name for p in PROJE.glob("*.md") if p.name not in MD_YASAK)


def _json_dosyalari():
    return sorted(p.name for p in PROJE.glob("*.json") if p.name not in JSON_YASAK)


def _sizinti_denetimi(metin):
    """Uretilen metinde GERCEK sir DEGERLERI geciyor mu?
    Desen tahmini degil, sir dosyalarindaki degerlerin BIREBIR aranmasi
    -> yanlis alarm yok, kacirma riski dusuk."""
    bulunan = []
    for gizli in ("telegram.json", "coinalyze.json"):
        p = PROJE / gizli
        if not p.exists():
            continue
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(d, dict):
            for k, v in d.items():
                if isinstance(v, str) and len(v) >= 8 and v in metin:
                    bulunan.append(f"{gizli} -> alan '{k}'")
    # Telegram bot token bicimi (sir dosyasi silinmis olsa bile yakalar)
    if re.search(r"bot\d{8,}:[A-Za-z0-9_-]{30,}", metin):
        bulunan.append("telegram bot token biçimi")
    return bulunan


def _git_log(n=25):
    try:
        r = subprocess.run(["git", "log", f"-{n}", "--pretty=format:%h  %ad  %s",
                            "--date=short"], cwd=str(PROJE), capture_output=True,
                           text=True, encoding="utf-8", timeout=25)
        return r.stdout.strip() if r.returncode == 0 else f"[git log alınamadı: {r.stderr[:120]}]"
    except Exception as e:
        return f"[git log alınamadı: {type(e).__name__}]"


def sicil_ozeti():
    """Kisisel sicili GOMMEDEN ozet (gizlilik + dosya boyutu).
    K2 sayaci ayrica yazilir — projenin merkezi metrigi odur."""
    try:
        sys.path.insert(0, str(PROJE))
        import defter, radar_defter
        a, r = defter.ozet(), radar_defter.ozet()
        out = (f"- **Ana sicil:** {a['acik']} açık, {a['kapali']} kapalı, "
               f"isabet %{a.get('isabet_pct')}, brüt {a['toplam_R']:+.2f}R / "
               f"**net {a['toplam_net_R']:+.2f}R**\n"
               f"- **Radar sicili:** {r['acik']} açık, {r['kapali']} kapalı, "
               f"isabet %{r.get('isabet_pct')}, net {r['toplam_net_R']:+.2f}R\n")
        if a.get("deneysel"):
            out += (f"- **Deneysel (LAB):** {a['deneysel']['kapali']} kapalı, "
                    f"net {a['deneysel']['toplam_net_R']:+.2f}R\n")

        # --- K2 sayaci (swing-1h alt kumesi) — defter'in KENDI kanonik suzgeciyle ---
        d = defter._yukle()
        K = [t for t in d["tahminler"]
             if t.get("kaynak", "canli") != "geri-doldurma"
             and t.get("sicil") != "deneysel"
             and t.get("konfig") == "swing-1h"
             and t["durum"] in ("tp1", "tp2", "stop", "zaman_asimi")]
        if K:
            kaz, kay, girilmis = defter._isabet_kovalari(K)
            net = sum((defter.net_R(t) or 0) for t in K)
            isb = f"%{len(kaz)/len(girilmis)*100:.0f}" if girilmis else "—"
            hkm = ("**KAPI GEÇİLEMEDİ**" if net < 0 else "kapı geçildi") if len(K) >= 30 \
                  else f"sürüyor ({30-len(K)} kaldı)"
            out += (f"- **K2 sayacı (swing-1h):** {len(K)}/30 — {len(kaz)} kazanç / "
                    f"{len(kay)} kayıp, isabet {isb}, **net {net:+.2f}R** → {hkm}\n"
                    f"  - başabaş için gereken isabet (R/R 2,08): **%32,5**\n")
        return out
    except Exception as e:
        return f"- [sicil özeti alınamadı: {type(e).__name__}: {e}]\n"


def uret():
    simdi = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    bolumler, artik = _kod_bolumleri()
    jsonlar = _json_dosyalari()
    toplam_py = sum(len(ds) for _, ds in bolumler)

    P = []
    P.append(f"""# KRİPTO SİSTEMİ — TAM KOD PAKETİ

> **Üretim:** {simdi} · `tamkod.py` ile otomatik üretildi (elle düzenleme, bir dahaki
> üretimde kaybolur — kalıcı değişiklik için `SISTEM.md` veya hafıza defterini güncelle).
> **Proje:** `c:\\Users\\KURTİ\\Desktop\\klasörler\\kripto` · **GitHub:** umut19171917/kripto-ceo
>
> **İÇİNDEKİLER**
> 1. Sistemin tam tarifi (mimari, karar mantığı, sicil, kapılar) — `SISTEM.md`'den
> 2. Yapılacaklar listesi (K2/K3/koşullu/açık sınırlar) — hafıza defterinden
> 3. Anlık sicil özeti + K2 sayacı
> 4. EK A — tüm kaynak kod ({toplam_py} dosya)
> 5. EK B — anlık çalışma-anı JSON durumu ({len(jsonlar)} dosya)
> 6. EK C — değişim geçmişi (git)
> 7. EK D — proje belgeleri + kurulum dosyaları
>
> **KAPSAM KURALI**
> **Girer:** sistemi tarif eden her şey — kod, başlatıcılar, çalışma-anı durumu, tarif,
> yapılacaklar, değişim geçmişi, kurulum dosyaları.
> **Girmez:** sırlar (`telegram.json`, `coinalyze.json`) ve kişisel veri
> (`kripto-defter.json`, `radar-defter.json`). Sicilden yalnız **özet** yazılır.
> Üretim öncesi sızıntı denetimi yapılır; gerçek bir anahtar değeri metinde bulunursa
> **dosya yazılmaz**.
""")
    if artik:
        P.append(f">\n> ⚠ **{len(artik)} dosya `KOD_SIRASI`'nda sınıflandırılmamış** ve"
                 f" taramayla yakalandı: {', '.join('`'+a+'`' for a in artik)}."
                 f" Pakete dahildir; bir sonraki düzenlemede sıraya yerleştirilmeli.\n")

    P.append("\n---\n\n# BÖLÜM 1 — SİSTEMİN TAM TARİFİ\n\n")
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

    P.append(f"\n\n---\n\n# EK A — TÜM KAYNAK KOD ({toplam_py} dosya)\n")
    for baslik, dosyalar in bolumler:
        if not dosyalar:
            continue
        P.append(f"\n## {baslik}\n")
        for d in dosyalar:
            yol = PROJE / d
            if not yol.exists():
                continue
            satir = len(yol.read_text(encoding="utf-8").splitlines())
            # 4 backtick: gomulen kaynak 3-backtick icerebilir (tamkod.py'nin kendisi
            # markdown uretiyor) -> uzun cit kisa citi yutar, render kirilmaz.
            P.append(f"\n### `{d}` ({satir} satır)\n\n" + "````python\n" + _oku(yol) + "\n````\n")

    P.append("\n## BAŞLATICILAR — çift-tık bat'lar + Startup VBS'leri\n")
    for d in BASLATICILAR:
        yol = PROJE / d
        if not yol.exists():
            continue
        P.append(f"\n### `{d}`\n\n" + "````bat\n" + _oku(yol) + "\n````\n")
    for v in VBSLER:
        if v.exists():
            P.append(f"\n### `{v.name}` (Startup klasörü — her logon'da otomatik başlatır)\n\n"
                     + "````vb\n" + _oku(v) + "\n````\n")

    P.append(f"\n\n---\n\n# EK B — ANLIK ÇALIŞMA-ANI DURUMU ({len(jsonlar)} JSON)\n")
    P.append("\n> Bu dosyalar kod tarafından sürekli yeniden üretilir; anlık fotoğraftır.\n"
             "> API anahtarları ve kişisel siciller bilinçli olarak dışarıda.\n")
    for j in jsonlar:
        P.append(f"\n### `{j}`\n\n" + "````json\n" + _oku(PROJE / j, sinir=6000) + "\n````\n")

    P.append("\n\n---\n\n# EK C — DEĞİŞİM GEÇMİŞİ (son 25 commit)\n\n")
    P.append("````text\n" + _git_log(25) + "\n````\n")

    belgeler = _belge_dosyalari()
    P.append(f"\n\n---\n\n# EK D — PROJE BELGELERİ ({len(belgeler)}) + KURULUM\n")
    P.append("\n> Belgeler TARAMAYLA toplanır (deny-list) — yeni belge türleri"
             " otomatik girer.\n")
    for ad in belgeler:
        P.append(f"\n### `{ad}`\n\n" + "````markdown\n" + _oku(PROJE / ad) + "\n````\n")
    for ad, dil in KURULUM:
        yol = PROJE / ad
        if not yol.exists():
            continue
        P.append(f"\n### `{ad}`\n\n" + f"````{dil}\n" + _oku(yol) + "\n````\n")

    metin = "".join(P)

    # --- FAIL-CLOSED: sir sizdirmaktansa uretimi durdur ---
    sizinti = _sizinti_denetimi(metin)
    if sizinti:
        return None, 0, artik, sizinti

    CIKTI.write_text(metin, encoding="utf-8")
    return CIKTI, len(metin), artik, []


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    yol, boyut, artik, sizinti = uret()

    if sizinti:
        print("!! DOSYA YAZILMADI — sizinti denetimi takildi:")
        for s in sizinti:
            print(f"   - {s}")
        print("   JSON_YASAK listesini genislet ve tekrar calistir.")
        sys.exit(1)

    satir = len(yol.read_text(encoding="utf-8").splitlines())
    print(f"YAZILDI: {yol}")
    print(f"Boyut: {boyut/1024:.0f} KB ({satir} satir)")
    print(f"Sizinti denetimi: TEMIZ")
    if artik:
        print(f"UYARI: {len(artik)} dosya KOD_SIRASI'nda sinifsiz (pakete GIRDI): "
              + ", ".join(artik))
    else:
        print("Kapsama: tum .py dosyalari siniflandirilmis")
