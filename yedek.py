"""
yedek.py — Kritik dosyalarin Google Drive'a gunluk otomatik yedegi (2026-07-25)
================================================================================
GitHub KODU yedekler ama gitignore'lu KRITIK dosyalar (sicil + hafiza + anahtarlar)
hicbir yerde degildi. Disk olurse / Windows sifirlanirsa K2 ilerlemesi + tum tahmin
gecmisi GERI ALINAMAZ sekilde giderdi. Bu modul onlari kullanicinin KENDI Google
Drive'ina (H:\\Drive'im = kurtulusumut76@gmail.com) gunluk TARIHLI klasorlere kopyalar.

Tarihli klasor (ayna DEGIL): son TUTMA_GUN gun saklanir -> bir dosya bozulursa/yanlis
silinirse dunun saglam kopyasi da elde kalir. Toplam ~250KB x 14 ~ 3.5MB (onemsiz).

Cagirma:
  - Otomatik: izleyici.ozet_loop her dongude gunluk_yedek() cagirir (IDEMPOTENT:
    gunun klasoru varsa is yapmaz -> gunde 1 gercek yedek).
  - Elle: python yedek.py [--zorla]   veya   yedek.bat cift-tik.
Fail-safe: Drive bagli degilse / her hata -> sessiz atla + log; cekirdegi ASLA kirmaz.
"""
import shutil
from datetime import datetime, timezone
from pathlib import Path

import olcucu  # log_line

PROJE = Path(__file__).parent
HEDEF = Path(r"H:\Drive'ım\kripto-yedek")
HAFIZA = Path(r"C:\Users\KURTİ\.claude\projects\c--Users-KURT--Desktop-klas-rler-kripto\memory")
TUTMA_GUN = 14

# Yedeklenecek KRITIK dosyalar (gitignore'lu; yeri doldurulamaz veya yeniden-almasi zahmetli)
DOSYALAR = ["kripto-defter.json", "radar-defter.json", "telegram.json", "coinalyze.json"]


def _prune():
    """TUTMA_GUN'den eski tarihli yedek klasorlerini sil (tarih-adli olanlar)."""
    if not HEDEF.exists():
        return
    tarihli = sorted(d for d in HEDEF.iterdir() if d.is_dir() and d.name[:4].isdigit())
    for d in tarihli[:-TUTMA_GUN]:
        try:
            shutil.rmtree(d)
        except Exception:
            pass


def gunluk_yedek(zorla=False):
    """Bugunun tarihli klasorune kritik dosyalari kopyala. Idempotent: klasor zaten
    varsa (zorla=False) is yapmaz. Doner: (yapildi_mi: bool, mesaj: str)."""
    try:
        if not HEDEF.parent.exists():   # H:\Drive'im bagli degil (Drive uygulamasi kapali)
            return False, "Google Drive bagli degil (H: yok) - atlandi"
        gun = datetime.now(timezone.utc).date().isoformat()
        gun_dir = HEDEF / gun
        if gun_dir.exists() and not zorla:
            return False, f"bugun ({gun}) zaten yedekli"
        gun_dir.mkdir(parents=True, exist_ok=True)
        n = 0
        for ad in DOSYALAR:
            src = PROJE / ad
            if src.exists():
                shutil.copy2(src, gun_dir / ad)
                n += 1
        if HAFIZA.exists():
            shutil.copytree(HAFIZA, gun_dir / "memory", dirs_exist_ok=True)
            n += 1
        _prune()
        return True, f"{n} oge kopyalandi -> {gun_dir}"
    except Exception as e:
        return False, f"HATA {type(e).__name__}: {e}"


if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    yapildi, mesaj = gunluk_yedek(zorla="--zorla" in sys.argv)
    print(("YEDEK OK: " if yapildi else "YEDEK atlandi: ") + mesaj)
