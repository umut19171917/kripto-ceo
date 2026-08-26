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
HEDEF = Path(r"H:\Drive'ım\kripto-yedek\perp-arsiv")
TUTMA_HAFTA = 8            # ~2 ay geriye; 33 MB ham -> zip ~8-10 MB/adet
ARALIK_GUN = 7


def _yedekler():
    if not HEDEF.exists():
        return []
    return sorted(HEDEF.glob("perp-arsiv-*.zip"))


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
    try:
        HEDEF.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"hedef erisilemiyor ({type(e).__name__}) — sessiz cikis")
        return 0

    gun = datetime.now().strftime("%Y-%m-%d")
    son = HEDEF / f"perp-arsiv-{gun}.zip"
    gecici = HEDEF / f".perp-arsiv-{gun}.tmp.zip"
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
