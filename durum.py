"""
durum.py — Insan-okur DURUM RAPORU. Cift tikla (durum.bat) ya da:
    venv\\Scripts\\python.exe durum.py
signals.json + makro.json + kripto-defter.json okur, ozet basar. Claude'a sormadan bak.
"""

import sys
import json
from datetime import datetime, timezone
from pathlib import Path

KOK = Path(__file__).parent


def _j(name):
    try:
        return json.loads((KOK / name).read_text(encoding="utf-8"))
    except Exception:
        return None


def _yas_dk(iso):
    try:
        return (datetime.now(timezone.utc) - datetime.fromisoformat(iso)).total_seconds() / 60
    except Exception:
        return None


def _ozet(lst):
    kapali = [t for t in lst if t["durum"] in ("tp1", "tp2", "stop", "zaman_asimi")]
    kazanc = [t for t in kapali if t["durum"] in ("tp1", "tp2")]
    kayip = [t for t in kapali if t["durum"] == "stop"]
    acik = [t for t in lst if t["durum"] in ("beklemede", "izleniyor")]
    girilmis = kazanc + kayip
    isabet = f"%{len(kazanc) / len(girilmis) * 100:.0f}" if girilmis else "-"
    R = sum((t.get("sonuc_R") or 0) for t in kapali)
    return acik, kapali, kazanc, kayip, isabet, R


def main():
    print("=" * 58)
    print("  KRIPTO SISTEM - DURUM RAPORU   " + datetime.now().strftime("%Y-%m-%d %H:%M"))
    print("=" * 58)

    sig = _j("signals.json")
    if sig:
        yas = _yas_dk(sig.get("updated_at", ""))
        if yas is None:
            durum = "bilinmiyor"
        elif yas < 2:
            durum = f"CALISIYOR (son veri {int(yas * 60)} sn once)"
        else:
            durum = f"DURMUS OLABILIR (son veri {int(yas)} dk once)"
        print(f"\nSISTEM: {durum}")
    else:
        print("\nSISTEM: signals.json yok")

    mk = _j("makro.json")
    if mk:
        print(f"\nMAKRO KAPI: {mk['kapi']}  (boyut x{mk['boyut_carpani']})")
        t = mk.get("takvim", {})
        if t.get("sonraki"):
            print(f"  sonraki olay: {t['sonraki']} (~{t.get('saat_kala')} saat sonra)")
        for n in mk.get("notlar", []):
            print(f"  - {n}")

    if sig:
        print("\nCOINLER (anlik):")
        for s, v in sig.get("symbols", {}).items():
            if "error" in v:
                print(f"  {s:9} HATA")
                continue
            sq, pl = v["squeeze"], v.get("plan", {})
            skor = max(sq["short_squeeze"], sq["long_squeeze"])
            if pl.get("yon"):
                print(f"  {s:9} ${v['price']:<9} >>> SETUP {pl['yon']} | giris {pl['giris']} stop {pl['stop']} TP1 {pl['tp1']} R/R {pl['rr1']}")
            else:
                print(f"  {s:9} ${v['price']:<9} skor {skor}/70 - setup yok")

    dft = _j("kripto-defter.json")
    if dft:
        T = dft.get("tahminler", [])
        canli = [t for t in T if t.get("kaynak", "canli") != "geri-doldurma"]
        bf = [t for t in T if t.get("kaynak") == "geri-doldurma"]
        acik, kapali, kazanc, kayip, isabet, R = _ozet(canli)
        print("\nSICIL (gercek/canli):")
        print(f"  acik: {len(acik)}  kapali: {len(kapali)}  kazanc: {len(kazanc)}  kayip: {len(kayip)}")
        print(f"  ISABET: {isabet}   TOPLAM R: {R:+.2f}")
        if bf:
            _, bk, _, _, bis, bR = _ozet(bf)
            print(f"  [geri-doldurma/backtest: {len(bk)} kapali, isabet {bis}, R {bR:+.2f} - ayri tutulur]")

        if acik:
            print("\n  ACIK TAHMINLER:")
            for t in acik:
                print(f"    #{t['no']} {t['token']} {t['yon']} [{t['durum']}] giris {t['giris']} stop {t['stop']} TP1 {t['tp1']}")
        sonk = [t for t in canli if t["durum"] in ("tp1", "tp2", "stop", "zaman_asimi", "tetiklenmedi")][-5:]
        if sonk:
            print("\n  SON KAPANANLAR:")
            for t in sonk:
                print(f"    #{t['no']} {t['token']} {t['yon']} -> {t['durum'].upper()} (R {t.get('sonuc_R')})")

        kapanmis = len([t for t in canli if t["durum"] in ("tp1", "tp2", "stop")])
        print("\n" + "=" * 58)
        if kapanmis < 10:
            print(f"NOT: Sadece {kapanmis} kapanmis islem - sonuc icin ERKEN (>=10-20 gerekir).")
        print("Hatirlatma: kanitlanana kadar GERCEK PARAYLA girme.")
    print("=" * 58)


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    main()
