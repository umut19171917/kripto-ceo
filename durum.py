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

try:
    from defter import (net_R as _net_R, RISK_TAVANI_PCT as _TAVAN,
                        mesaj_sinyal as _mesaj_sinyal, mesaj_sonuc as _mesaj_sonuc,
                        mesaj_gecersiz as _mesaj_gecersiz)
except Exception:
    _net_R = None
    _TAVAN = None
    _mesaj_sinyal = _mesaj_sonuc = _mesaj_gecersiz = None


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
    acik = [t for t in lst if t["durum"] in ("beklemede", "izleniyor")]
    # isabet paydasi TEK KAYNAK: defter._isabet_kovalari (2026-08-09 duzeltmesi;
    # zaman_asimi de girilmis islemdir -> paydaya girer, R isaretine gore siniflanir)
    from defter import _isabet_kovalari
    kazanc, kayip, girilmis = _isabet_kovalari(kapali)
    isabet = f"%{len(kazanc) / len(girilmis) * 100:.0f}" if girilmis else "-"
    R = sum((t.get("sonuc_R") or 0) for t in kapali)
    netR = sum((_net_R(t) or 0) for t in kapali) if _net_R else None
    return acik, kapali, kazanc, kayip, isabet, R, netR


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
        pr = mk.get("piyasa_rejimi")
        if pr and pr.get("durum"):
            # 🔴 Madde 5.1 (2026-09-01): eskiden tek satirdi ve basligi "piyasa
            # rejimi: SAKIN" idi. SAKIN/OYNAK yalnizca OYNAKLIK olcer, yon DEGIL —
            # ama baslik onu genel piyasa durumu gibi okutuyordu ve belgelerde
            # defalarca YON gibi yorumlandi ("dusen/testere rejim"), iki ay yorumu
            # kaydirdi. Yon etiketi (`trend`) 2026-06-28'den beri VARDI, eksik olan
            # ETIKET DEGIL GORUNURLUKTU: parantez icinde, en sonda duruyordu.
            # Cozum: ikisi AYRI SATIR ve esit agirlikta; karistirilamaz.
            print(f"  oynaklik : {pr['durum']}  (vol x{pr.get('vol_orani')}, "
                  f"korelasyon {pr.get('korelasyon')})")
            yon = pr.get("trend")
            if yon:
                print(f"  YON      : {str(yon).upper()}   <- fiyat yonu; "
                      f"yukaridaki SAKIN/OYNAK yon DEGIL, oynaklik olcer")
        for n in mk.get("notlar", []):
            print(f"  - {n}")

    # Esik saglik uyarilari (2026-08-09, dis denetim BULGU 5) — SALT BILGI, davranis
    # degismedi; dejenere esikli sembolde skorun ilgili kolu koru olabilir.
    esik = _j("esikler.json")
    if esik:
        S = esik.get("symbols") or {}
        # 2026-08-15: kalibrasyon patlayinca sistem SESSIZCE varsayilan esiklere
        # dusuyordu. Artik gorunur (bkz. kalibrasyon.write_config).
        bozuk = [s for s, d in S.items() if isinstance(d, dict) and "error" in d]
        bayat = [(s, d.get("bayat_since")) for s, d in S.items()
                 if isinstance(d, dict) and d.get("bayat_since")]
        if bozuk:
            print(f"\n!! ESIK YOK ({len(bozuk)} sembol) — VARSAYILAN esiklerle skorlaniyor: "
                  + ", ".join(bozuk))
        if bayat:
            print(f"\n!! ESIK BAYAT ({len(bayat)} sembol) — son basarili kalibrasyon korunuyor:")
            for s, t in bayat:
                print(f"  {s}: {t} tarihinden beri tazelenemedi")
        uyarili = [(s, d["saglik_uyari"]) for s, d in S.items()
                   if isinstance(d, dict) and d.get("saglik_uyari")]
        if uyarili:
            print(f"\nESIK SAGLIK UYARISI ({len(uyarili)} sembol — skor ayrim gucu dusuk):")
            for s, u in uyarili:
                print(f"  {s}: {u}")

    if sig:
        print("\nCOINLER (anlik):")
        for s, v in sig.get("symbols", {}).items():
            if "error" in v:
                print(f"  {s:9} HATA")
                continue
            sq, pl = v["squeeze"], v.get("plan", {})
            skor = max(sq["short_squeeze"], sq["long_squeeze"])
            if pl.get("yon") and pl.get("gecerli") and _mesaj_sinyal:
                print()
                print(_mesaj_sinyal(s, pl["yon"], pl["giris"], pl["stop"], pl["tp1"], pl["tp2"],
                                    pl["rr1"], skor=skor, price=v["price"],
                                    baslik_etiket="AKTIF KURULUM"))
            else:
                print(f"  {s:9} ${v['price']:<9} skor {skor}/70 - setup yok")

    dft = _j("kripto-defter.json")
    if dft:
        T = dft.get("tahminler", [])
        canli = [t for t in T if t.get("kaynak", "canli") != "geri-doldurma"
                 and t.get("sicil") != "deneysel"]
        dn = [t for t in T if t.get("sicil") == "deneysel"]      # LAB: takip var, K2'ye girmez
        bf = [t for t in T if t.get("kaynak") == "geri-doldurma"]
        acik, kapali, kazanc, kayip, isabet, R, netR = _ozet(canli)
        print("\nSICIL (gercek/canli):")
        print(f"  acik: {len(acik)}  kapali: {len(kapali)}  kazanc: {len(kazanc)}  kayip: {len(kayip)}")
        if netR is not None:
            print(f"  ISABET: {isabet}   TOPLAM R: {R:+.2f} (gross)  |  NET (komisyon dusulmus): {netR:+.2f}")
        else:
            print(f"  ISABET: {isabet}   TOPLAM R: {R:+.2f}")
        if bf:
            _, bk, _, _, bis, bR, _ = _ozet(bf)
            print(f"  [geri-doldurma/backtest: {len(bk)} kapali, isabet {bis}, R {bR:+.2f} - ayri tutulur]")
        if dn:
            da, dk, _, _, dis, dR, dnet = _ozet(dn)
            dnet_s = f", net {dnet:+.2f}" if dnet is not None else ""
            print(f"  [deneysel (LAB): {len(da)} acik, {len(dk)} kapali, isabet {dis}{dnet_s} - ana sicile girmez]")

        # acik risk TUM acik tahminlerden (deneysel dahil) — tavan mantigiyla ayni
        acik_tum = acik + [t for t in dn if t["durum"] in ("beklemede", "izleniyor")]
        if acik_tum:
            r_long = sum(t.get("risk_pct", 1.0) for t in acik_tum if t["yon"] == "LONG")
            r_short = sum(t.get("risk_pct", 1.0) for t in acik_tum if t["yon"] == "SHORT")
            tavan_s = f"  (tavan: ayni-yon <= %{_TAVAN:.0f})" if _TAVAN else ""
            print(f"  acik risk: LONG %{r_long:.1f} / SHORT %{r_short:.1f}{tavan_s}")
            print("\n  ACIK TAHMINLER:")
            for t in acik_tum:
                dn = t.get("sicil") == "deneysel"
                if _mesaj_sinyal:
                    etiket = "ACIK POZISYON (tetiklendi)" if t["durum"] == "izleniyor" \
                        else "BEKLEYEN SINYAL (henuz tetiklenmedi)"
                    print()
                    print(f"  #{t['no']}")
                    print(_mesaj_sinyal(t["token"], t["yon"], t["giris"], t["stop"], t["tp1"], t["tp2"],
                                        t["rr1"], risk_pct=t.get("risk_pct", 1.0), skor=t.get("skor"),
                                        kapi=t.get("makro_kapi"), deneysel=dn, baslik_etiket=etiket))
                else:
                    dn_s = " (deneysel)" if dn else ""
                    print(f"    #{t['no']} {t['token']} {t['yon']} [{t['durum']}] giris {t['giris']} stop {t['stop']} TP1 {t['tp1']}{dn_s}")
        sonk = [t for t in canli if t["durum"] in ("tp1", "tp2", "stop", "zaman_asimi", "tetiklenmedi")][-5:]
        if sonk:
            print("\n  SON KAPANANLAR:")
            for t in sonk:
                if t["durum"] == "tetiklenmedi" and _mesaj_gecersiz:
                    print(f"  #{t['no']} " + _mesaj_gecersiz(t).replace("\n", "\n  "))
                elif _mesaj_sonuc:
                    print(f"  #{t['no']} " + _mesaj_sonuc(t).replace("\n", "\n  "))
                else:
                    nr = _net_R(t) if _net_R else None
                    ns = f" net {nr:+.2f}" if nr is not None else ""
                    print(f"    #{t['no']} {t['token']} {t['yon']} -> {t['durum'].upper()} (gross R {t.get('sonuc_R')}{ns})")

        try:
            import radar_defter
            radar_defter.coz_tumu()   # istedigin an calistirinca ONCE guncel mumlarla ilerlet
            radar_defter.rapor_yaz()  # radar-defteri.html'i de tazele (tam gecmis, tarayicida acilir)
            ro = radar_defter.ozet()
        except Exception:
            ro = None
        if ro and (ro["acik"] or ro["kapali"]):
            print("\nRADAR SICILI (ayri defter, K2 olcumune KARISMAZ):")
            risb = f"%{ro['isabet_pct']}" if ro["isabet_pct"] is not None else "-"
            print(f"  acik: {ro['acik']}  kapali: {ro['kapali']}  kazanc: {ro['kazanc']}  kayip: {ro['kayip']}")
            if ro["kapali"]:
                print(f"  ISABET: {risb}   TOPLAM R: {ro['toplam_R']:+.2f} (gross)  |  NET: {ro['toplam_net_R']:+.2f}")
            if ro["acik_liste"] and _mesaj_sinyal:
                print("\n  RADAR ACIK POZISYONLAR:")
                for t in ro["acik_liste"]:
                    etiket = "RADAR ACIK POZISYON (tetiklendi)" if t["durum"] == "izleniyor" \
                        else "RADAR BEKLEYEN (henuz tetiklenmedi)"
                    print()
                    print(_mesaj_sinyal(t["token"], t["yon"], t["giris"], t["stop"], t["tp1"], t["tp2"],
                                        t["rr1"], skor=t.get("skor"), kapi=t.get("makro_kapi"),
                                        baslik_etiket=etiket))
            if ro["son_kapananlar"]:
                print("\n  RADAR SON KAPANANLAR:")
                for t in ro["son_kapananlar"]:
                    if t["durum"] == "tetiklenmedi" and _mesaj_gecersiz:
                        print("  " + _mesaj_gecersiz(t).replace("\n", "\n  "))
                    elif _mesaj_sonuc:
                        print("  " + _mesaj_sonuc(t).replace("\n", "\n  "))

        try:
            import radar as _radar
            r = _radar.radar_ozeti(24)
        except Exception:
            r = None
        if r and r["hareket"]:
            print("\nRADAR HAREKET (son 24 saat - bilgi katmani, Telegram'a gitmez):")
            for sym, sev in r["hareket"][:6]:
                print(f"  hareket: {sym} ~%{sev:.0f}")

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
