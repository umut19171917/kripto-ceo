"""
arsiv_yedek.py — perp-arsiv/ icin HAFTALIK SIKISTIRILMIS yedek (2026-08-26)
================================================================================
NEDEN AYRI BIR BETIK (yedek.py'ye eklenmedi — bilincli karar):
`yedek.py` calisan, defterleri koruyan KRITIK bir betiktir ve `izleyici.py`
dongusunden gunluk cagrilir. Ona dokunup bozarsam yedekler SESSIZCE durur —
arsivdeki 8. ders tam olarak budur ("sessiz bozulma en tehlikelisi; kalibrasyon
arizasi ne coktu, ne uyardi, ne iz birakti"). Bu yuzden:
  - `yedek.py` DEGISMEDI, gunluk defter yedegi aynen calisiyor
  - bu betik BAGIMSIZ; coker ya da hedef diske erisemezse baska hicbir sey etkilenmez

NEDEN HAFTALIK VE SIKISTIRILMIS: arsiv ~33 MB ve buyuyor. Gunluk kopyalamak
14 gunde ~460 MB eder. JSON iyi sikisir; haftalik zip dogru oran.

⏰ NEDEN SIMDI DEGIL DE 24 EYLUL'DE ONEMLI: bugun arsivin TAMAMI API'den
yeniden cekilebilir (29,6 gunluk pencere icinde), yani yedeksizlik HENUZ
kayip riski degil. Dolgu 2026-08-26'da yapildi; ~29 gun sonra (2026-09-24)
en eski gunler API'den DUSER ve yeniden uretilemez hale gelir. Bu betik o
tarihten ONCE calisir durumda olsun diye simdi kuruldu.

🔴 GUVENLIK KURALLARI (bu betik veri KAYBETTIRMEZ):
  1. Kaynagi ASLA silmez/degistirmez — yalniz okur.
  2. Once gecici dosyaya yazar, ZIP BUTUNLUGUNU dogrular, sonra adini koyar.
     Bozuk yedek, yedeksizlikten KOTUDUR (yanlis guven verir).
  3. Eski yedekleri ancak YENI yedek dogrulandiktan SONRA budar.
  4. Hedef disk yoksa sessizce cikar (yedek.py ile ayni davranis).

Calistirma:
  venv\\Scripts\\python.exe arsiv_yedek.py           -> haftalik yedek (gerekiyorsa)
  venv\\Scripts\\python.exe arsiv_yedek.py --zorla   -> bugun yapilmis olsa da yap
  venv\\Scripts\\python.exe arsiv_yedek.py --durum   -> mevcut yedekler (yazmaz)
"""
import sys
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

KOK = Path(__file__).parent
KAYNAK = KOK / "perp-arsiv"

# 🔴 2026-08-31 DUZELTME — bu betik 5 gundur SESSIZCE hicbir sey yapmiyordu.
# Bulunus: gorev 30.08'de 267014 (sonlandirildi) dondu, log'a TEK satir yazmadi,
# ve hedefte SIFIR yedek vardi. Sebep: H: (Google Drive) BAGLI DEGIL.
# Eski 4. kural "hedef disk yoksa SESSIZCE cik" idi — gorunmezligin kaynagi oydu.
#
# ⏰ VE DOSYANIN KENDI HESABI YANLISTI: "24 Eylul'e kadar risk yok" deniyordu.
# Arsiv 2026-07-27'ye kadar gidiyor; 2026-08-31 eksi 29 gun = 2026-08-02.
# Yani 07-27 -> 08-02 arasi ~6 gun ZATEN API'den cekilemez. Risk BUGUN var.
#
# Cozum: sirali hedef listesi + hicbiri yazilabilir degilse GURULTULU hata.
HEDEFLER = [
    Path(r"H:\Drive'ım\kripto-yedek\perp-arsiv"),          # tercih: baska disk
    Path.home() / "kripto-yedek" / "perp-arsiv",           # yedek plan: C: (ayni disk)
]
TUTMA_HAFTA = 8            # ~2 ay geriye; 33 MB ham -> zip ~8-10 MB/adet
ARALIK_GUN = 7


def hedef_sec(yaratmadan=False):
    """Ilk YAZILABILIR hedefi dondur. Yoksa None.

    ⚠ Ikinci hedef KAYNAKLA AYNI DISKTE. Disk arizasina karsi korumaz;
    yalniz kaza sonucu silme/bozulmaya karsi korur. H: baglanirsa
    otomatik olarak ona doner (liste sirali)."""
    for h in HEDEFLER:
        try:
            if h.exists():
                return h
            if not yaratmadan and h.parent.parent.exists():
                h.mkdir(parents=True, exist_ok=True)
                return h
        except Exception:
            continue
    return None


HEDEF = hedef_sec(yaratmadan=True) or HEDEFLER[-1]      # geriye donuk uyum


def _yedekler():
    h = hedef_sec(yaratmadan=True)
    if h is None or not h.exists():
        return []
    return sorted(h.glob("perp-arsiv-*.zip"))


def _son_yedek_yasi():
    y = _yedekler()
    if not y:
        return None
    try:
        d = datetime.strptime(y[-1].stem.replace("perp-arsiv-", ""), "%Y-%m-%d")
        return (datetime.now() - d).days
    except Exception:
        return None


def durum():
    print(f"kaynak : {KAYNAK}")
    if KAYNAK.exists():
        n = list(KAYNAK.glob("*.json"))
        print(f"         {len(n)} dosya · {sum(f.stat().st_size for f in n)/1e6:.1f} MB")
    else:
        print("         YOK")
    print(f"hedef  : {HEDEF}")
    y = _yedekler()
    if not y:
        print("         henuz yedek yok")
    for f in y:
        print(f"         {f.name}  {f.stat().st_size/1e6:.1f} MB")
    yas = _son_yedek_yasi()
    print(f"son yedek yasi: {yas if yas is not None else '—'} gun (aralik {ARALIK_GUN})")


def yedekle(zorla=False):
    if not KAYNAK.exists() or not list(KAYNAK.glob("*.json")):
        print("kaynak bos/yok — yapilacak is yok")
        return 0
    yas = _son_yedek_yasi()
    if not zorla and yas is not None and yas < ARALIK_GUN:
        print(f"son yedek {yas} gun once — {ARALIK_GUN} gun dolmadi, atlandi")
        return 0
    # 🔴 ESKI DAVRANIS: "hedef erisilemiyor -> sessiz cikis, kod 0".
    # 5 gun boyunca hicbir yedek alinmadi ve HIC KIMSE FARK ETMEDI.
    # Yeni davranis: hedef yoksa GURULTULU hata + SIFIRDAN FARKLI cikis kodu.
    hedef = hedef_sec()
    if hedef is None:
        print("🔴 HICBIR YEDEK HEDEFI YAZILABILIR DEGIL:")
        for h in HEDEFLER:
            print(f"     {h}  ->  {'var' if h.exists() else 'YOK'}")
        print("   YEDEK ALINAMADI. Bu sessiz gecilmez — arsiv yeniden URETILEMEZ.")
        return 2

    gun = datetime.now().strftime("%Y-%m-%d")
    son = hedef / f"perp-arsiv-{gun}.zip"
    gecici = hedef / f".perp-arsiv-{gun}.tmp.zip"
    if hedef != HEDEFLER[0]:
        print(f"⚠ TERCIH EDILEN HEDEF ({HEDEFLER[0]}) YOK — yedek plana yaziliyor:")
        print(f"   {hedef}")
        print("   ⚠ Bu KAYNAKLA AYNI DISKTE. Disk arizasina karsi KORUMAZ.")
    dosyalar = sorted(KAYNAK.glob("*.json"))

    # 1) gecici dosyaya yaz — KAYNAGA DOKUNULMAZ
    try:
        with zipfile.ZipFile(gecici, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
            for f in dosyalar:
                z.write(f, arcname=f.name)
    except Exception as e:
        gecici.unlink(missing_ok=True)
        print(f"YEDEK YAZILAMADI: {type(e).__name__}: {e}")
        return 1

    # 2) BUTUNLUK DOGRULAMASI — bozuk yedek yedeksizlikten kotudur
    try:
        with zipfile.ZipFile(gecici) as z:
            if z.testzip() is not None:
                raise RuntimeError("zip icerik dogrulamasi basarisiz")
            if len(z.namelist()) != len(dosyalar):
                raise RuntimeError(f"dosya sayisi tutmuyor: "
                                   f"{len(z.namelist())} != {len(dosyalar)}")
    except Exception as e:
        gecici.unlink(missing_ok=True)
        print(f"YEDEK DOGRULANAMADI, ATILDI: {e}")
        return 1

    gecici.replace(son)
    mb = son.stat().st_size / 1e6
    ham = sum(f.stat().st_size for f in dosyalar) / 1e6
    print(f"yedek: {son.name}  {len(dosyalar)} dosya · {ham:.1f} MB -> {mb:.1f} MB "
          f"(%{100*(1-mb/ham):.0f} sikisma)")

    # 3) budama — YALNIZ dogrulanmis yeni yedek varken
    eski = _yedekler()[:-TUTMA_HAFTA]
    for f in eski:
        try:
            f.unlink()
            print(f"  budandi: {f.name}")
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    if "--durum" in sys.argv:
        durum()
        sys.exit(0)
    sys.exit(yedekle(zorla="--zorla" in sys.argv))
