"""
radar_defter.py — Radar kurulum adaylari icin AYRI sicil (2026-07-09)
================================================================================
[RADAR-KURULUM] adaylari eskiden bilgi-verip-unutuluyordu. Kullanici (2026-07-09)
"bu tavsiyelerin sonucunu gormek istiyorum, istedigim an kontrol edebilmeliyim"
dedi -> bu modul o istegi karsilar: radar-defter.json (AYRI dosya) + istenince
(durum.py) ozet.

KRITIK SINIR: bu sicil ANA sicile (kripto-defter.json, K2 edge olcumu) ASLA
KARISMAZ. Iki dosya tamamen bagimsiz. Radar ~45-50 coin tarar; hepsini K2'ye
eklemek olcumu sulardi (D1 tasarim karari, degismedi) — bu yuzden AYRI defter.

COZUMLEME MOTORU tekrar yazilmadi: defter.coz() + defter.k1m_kapanmis() ithal
edilip AYNEN kullanilir (fitil-tabanli, kapanmis-1dk-mum, idempotent — ayni
kod, ayni garanti). Zaman limitleri de ayni: kayitlara "konfig":"swing-1h"
etiketi konur -> defter._limitler() otomatik PENDING=24s/ACTIVE=120s uygular
(radar adaylari da ayni ATR-tabanli trade_plan mekanizmasindan geldigi icin
bu sureler dogru, keyfi degil).

NOT (durustluk): bu modulden ONCEKI radar kurulum uyarilari (bugune kadarki
FIL/PAXG/UNI/UAI/O gibi) GERIYE DONUK EKLENMEDI - o zamanki tam giris/stop/tp
degerleri sadece radar.log metninde, guvenilir geri-doldurma icin kirilgan.
Sicil BUNDAN SONRAKI adaylarla baslar.

Kontrol: durum.py (istedigin an calistir, cift-tikla) "RADAR SICILI" bolumu.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

import olcucu
import defter  # coz(), k1m_kapanmis(), net_R(), _limitler() (KONFIG="swing-1h" ile)

RADAR_DEFTER_FILE = Path(__file__).parent / "radar-defter.json"
RADAR_DEFTERI_HTML = Path(__file__).parent / "radar-defteri.html"


def _yukle():
    try:
        d = json.loads(RADAR_DEFTER_FILE.read_text(encoding="utf-8"))
        d.setdefault("tahminler", [])
        return d
    except Exception:
        return {"tahminler": []}


def _kaydet(d):
    olcucu.atomik_yaz(RADAR_DEFTER_FILE, d)


def _acik_var_mi(T, token, yon):
    return any(t["token"] == token and t["yon"] == yon and t["durum"] in ("beklemede", "izleniyor")
               for t in T)


def kaydet(sym, yon, giris, stop, tp1, tp2, rr1, skor, kapi):
    """Radar'in buldugu GECERLI kurulum adayini radar-sicili'ne ekler.
    Ayni coin+yonde ZATEN acik kayit varsa tekrar EKLEMEZ (coklu takip olmasin,
    12s alarm-tekrar cooldown'uyla zaten buyuk olcude ortusur ama bagimsiz
    kontrol edilir -> alarm mantigi degisirse sicil butunlugu bozulmaz)."""
    d = _yukle()
    T = d["tahminler"]
    if _acik_var_mi(T, sym, yon):
        return None
    no = max([t.get("no", 0) for t in T], default=0) + 1
    now = datetime.now(timezone.utc)
    kayit = {
        "no": no, "tarih": now.isoformat(timespec="seconds"),
        "token": sym, "yon": yon, "skor": skor,
        "giris": giris, "stop": stop, "tp1": tp1, "tp2": tp2, "rr1": rr1,
        "makro_kapi": kapi, "konfig": "swing-1h", "sicil": "radar",
        "durum": "beklemede", "tetik_tarih": None, "son_mum_ts": None,
        "sonuc_fiyat": None, "sonuc_R": None, "kapanis_tarih": None,
    }
    kayit.update(defter.rejim_damga())   # kayit anindaki rejim baglami (ana sicille ayni damga)
    T.append(kayit)
    _kaydet(d)
    return kayit


def coz_tumu():
    """Acik radar-sicili kayitlarini GERCEK kapanmis 1dk mumlarla ilerlet.
    defter.coz()/k1m_kapanmis() ile AYNI motor (kod tekrari yok). Normal
    gece-uykusu araliklarini (~<24s) k1m_kapanmis'in 1440dk tavani otomatik
    kapsar; 24s'ten uzun bosluklarda kucuk bir kor nokta olabilir (ana sicilin
    bosluk.py'si gibi ozel bir geri-doldurma bu ikinci sicil icin YOK - bilincli,
    bu gozlemsel/ikincil bir defter, K2 olcumu degil)."""
    d = _yukle()
    T = d["tahminler"]
    acik = [t for t in T if t["durum"] in ("beklemede", "izleniyor")]
    if not acik:
        return d
    now = datetime.now(timezone.utc)
    degisti = False
    for sym in sorted({t["token"] for t in acik}):
        grup = [t for t in acik if t["token"] == sym]
        eski = min((t.get("son_mum_ts") or int(datetime.fromisoformat(t["tarih"]).timestamp() * 1000))
                   for t in grup)
        dk = int((now.timestamp() * 1000 - eski) / 60_000) + 2
        try:
            k1m = defter.k1m_kapanmis(sym, dk)
        except Exception as e:
            olcucu.log_line(f"[RADAR-SICIL] {sym} 1dk mum alinamadi ({type(e).__name__}) - bu tur atlandi")
            continue
        for t in grup:
            onceki_ts = t.get("son_mum_ts")
            if defter.coz(t, k1m) or t.get("son_mum_ts") != onceki_ts:
                degisti = True
    if degisti:
        _kaydet(d)
    return d


def ozet():
    """Radar sicili ozeti. ANA K2 olcumunden TAMAMEN BAGIMSIZ rakamlar."""
    d = _yukle()
    T = d["tahminler"]
    acik = [t for t in T if t["durum"] in ("beklemede", "izleniyor")]
    kapali = [t for t in T if t["durum"] in ("tp1", "tp2", "stop", "zaman_asimi")]
    # isabet paydasi TEK KAYNAK: defter._isabet_kovalari (2026-08-09 duzeltmesi)
    kazanc, kayip, girilmis = defter._isabet_kovalari(kapali)
    gross = round(sum((t.get("sonuc_R") or 0) for t in kapali), 2)
    net = round(sum((defter.net_R(t) or 0) for t in kapali), 2)
    isabet = round(len(kazanc) / len(girilmis) * 100, 1) if girilmis else None
    return {"acik": len(acik), "kapali": len(kapali), "kazanc": len(kazanc),
            "kayip": len(kayip), "isabet_pct": isabet, "toplam_R": gross, "toplam_net_R": net,
            "acik_liste": acik, "son_kapananlar": kapali[-8:]}


def tum_kayitlar():
    """TUM radar-sicili kayitlari, en yeni en ustte (2026-07-09: kullanici
    'tum gecmisi listeleyelim' dedi; ozet()'in son_kapananlar[-8:] siniri
    burada YOK, bu rapor icin tam liste."""
    d = _yukle()
    return sorted(d["tahminler"], key=lambda t: t["no"], reverse=True)


_DURUM_ETIKET = {
    "beklemede": ("bekleniyor", "Bekleniyor"),
    "izleniyor": ("acik", "Açık Pozisyon"),
    "tp1": ("kar", "Sonuçlandı: Kâr"),
    "tp2": ("kar", "Sonuçlandı: Kâr"),
    "stop": ("zarar", "Sonuçlandı: Zarar"),
    "tetiklenmedi": ("gecersiz", "Geçersiz"),
}


def _sozel(yon):
    """Rapor icin DUZGUN Turkce (defter._yon_sozel'in ASCII/terminal-uyumlu
    halinden farkli — bu sayfa tarayicida acilir, aksan sorunsuz gorunur)."""
    if yon == "LONG":
        return "yükseleceğini", "ALIŞ (long)", "inerse", "çıkarsa"
    return "düşeceğini", "SATIŞ (short)", "çıkarsa", "inerse"


def _kart_html(t):
    yon = t["yon"]
    ongoru, islem, stop_yon, tp_yon = _sozel(yon)
    durum = t["durum"]
    if durum == "zaman_asimi":
        nr = defter.net_R(t) or 0
        sinif, etiket = ("kar" if nr >= 0 else "zarar"), "Sonuçlandı: Süre Doldu"
    else:
        sinif, etiket = _DURUM_ETIKET.get(durum, ("gecersiz", durum))

    baslik = t["token"][:-4] + "/USDT" if t["token"].endswith("USDT") else t["token"]
    skor_s = f" · skor {t['skor']}/100" if t.get("skor") is not None else ""

    if durum == "beklemede":
        anlatim = (f"Sistem {baslik}'in <strong>{ongoru}</strong> öngörüyor ama henüz fiyat girmesi "
                   f"gereken seviyeye ulaşmadı. Kayıt açıldı, sistem fiyatı izliyor.")
        rakamlar = (f'<div class="rakamlar">'
                    f'<div class="rakam"><span class="etiket">Giriş beklenen fiyat</span>'
                    f'<span class="deger">{t["giris"]}</span></div>'
                    f'<div class="rakam"><span class="etiket">Zararı-kes (Stop)</span>'
                    f'<span class="deger">{t["stop"]}</span>'
                    f'<div class="yardim">Fiyat buraya {stop_yon} vazgeçilir</div></div>'
                    f'<div class="rakam"><span class="etiket">Hedef</span>'
                    f'<span class="deger">{t["tp1"]}</span>'
                    f'<div class="yardim">Fiyat buraya {tp_yon} kâr alınır</div></div>'
                    f'</div>')
        sonuc = ""
    elif durum == "izleniyor":
        anlatim = ('Fiyat giriş seviyesine <strong>ulaştı</strong>. Kayıt şimdi "açık pozisyon" oldu — '
                   'henüz sonuçlanmadı, gerçek takip sürüyor.')
        rakamlar = (f'<div class="rakamlar">'
                    f'<div class="rakam"><span class="etiket">Giriş fiyatı (gerçekleşti)</span>'
                    f'<span class="deger">{t["giris"]}</span></div>'
                    f'<div class="rakam"><span class="etiket">Zararı-kes (Stop)</span>'
                    f'<span class="deger">{t["stop"]}</span></div>'
                    f'<div class="rakam"><span class="etiket">Hedef</span>'
                    f'<span class="deger">{t["tp1"]}</span></div>'
                    f'</div>')
        sonuc = ""
    elif durum == "tetiklenmedi":
        anlatim = ("Fiyat hiçbir zaman giriş seviyesine <strong>ulaşmadı</strong>, süre doldu. "
                   "Ne kâr ne zarar — işlem hiç açılmadı.")
        rakamlar = (f'<div class="rakamlar">'
                    f'<div class="rakam"><span class="etiket">Beklenen giriş</span>'
                    f'<span class="deger">{t["giris"]}</span></div>'
                    f'<div class="rakam"><span class="etiket">Sonuç</span><span class="deger">—</span>'
                    f'<div class="yardim">Süre doldu, hiç değmedi</div></div>'
                    f'</div>')
        sonuc = ""
    else:   # tp1/tp2/stop/zaman_asimi -> kapali, sonuc var
        gross = t.get("sonuc_R")
        nr = defter.net_R(t)
        r_sinif = "kar" if (gross or 0) >= 0 else "zarar"
        gross_s = f"{gross:+.2f}R" if gross is not None else "—"
        nr_s = f"{nr:+.2f}R" if nr is not None else "—"
        durum_aciklama = {
            "tp1": "Fiyat hedefe ulaştı.", "tp2": "Fiyat ikinci hedefe ulaştı.",
            "stop": "Fiyat, hedefe değil zararı-kes noktasına ulaştı.",
            "zaman_asimi": "Süre doldu; kayıt son fiyattan kapatıldı.",
        }.get(durum, "")
        anlatim = f"{durum_aciklama} Aynı kayıt, aynı başlık altında sonucunu gösteriyor."
        rakamlar = (f'<div class="rakamlar">'
                    f'<div class="rakam"><span class="etiket">Giriş</span>'
                    f'<span class="deger">{t["giris"]}</span></div>'
                    f'<div class="rakam"><span class="etiket">Kapanış</span>'
                    f'<span class="deger">{t.get("sonuc_fiyat", "—")}</span></div>'
                    f'</div>')
        sonuc = (f'<div class="sonuc-satiri"><span class="r-degeri {r_sinif}">{gross_s}</span>'
                 f'<span class="r-aciklama">ham sonuç · komisyon dahil net <strong>{nr_s}</strong>'
                 f'</span></div>')

    return (f'<div class="kayit"><div class="kayit-ust"><div><h2>{baslik}</h2>'
            f'<div class="coin-yon">{yon}{skor_s}</div></div>'
            f'<span class="durum-etiketi {sinif}">{etiket}</span></div>'
            f'<p class="anlatim">{anlatim}</p>{rakamlar}{sonuc}</div>')


_SAYFA_CSS = """<style>
  :root {
    --paper: #E4E1D6; --paper-raised: #EDEAE0; --ink: #1A2130; --ink-soft: #4B5160;
    --line: #C9C3B2; --accent: #8A6A2F; --acik: #4A5A73; --kar: #3C6E47;
    --zarar: #A23E2E; --gecersiz: #8B8377; --chip-fg: #F4F2EC;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --paper: #14171C; --paper-raised: #1B1F26; --ink: #E7E3D6; --ink-soft: #A9A597;
      --line: #33362F; --accent: #C9A227; --acik: #7C93B0; --kar: #5C9B6C;
      --zarar: #C25A46; --gecersiz: #6E6A5E; --chip-fg: #14171C;
    }
  }
  * { box-sizing: border-box; }
  body { background: var(--paper); color: var(--ink); font-family: "Segoe UI", system-ui, sans-serif;
         line-height: 1.55; padding: 3rem 1.25rem 5rem; -webkit-font-smoothing: antialiased; }
  .sayfa { max-width: 720px; margin: 0 auto; }
  h1, h2 { font-family: Georgia, "Iowan Old Style", "Palatino Linotype", serif;
           text-wrap: balance; font-weight: 400; color: var(--ink); margin: 0; }
  .ust { border-bottom: 2px solid var(--ink); padding-bottom: 1.75rem; margin-bottom: 1.5rem; }
  .ust .etiket { font-size: 0.72rem; letter-spacing: 0.12em; text-transform: uppercase;
                 color: var(--accent); font-weight: 600; }
  .ust h1 { font-size: 2rem; margin-top: 0.5rem; }
  .guncelleme { font-family: "Consolas", "SF Mono", monospace; font-size: 0.78rem;
                color: var(--ink-soft); margin-top: 0.6rem; }
  .aciklama { font-size: 1rem; color: var(--ink-soft); max-width: 62ch; }
  .ozet-cubuk { display: grid; grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
                gap: 1rem; margin: 1.75rem 0; padding: 1.1rem 1.3rem;
                background: var(--paper-raised); border: 1px solid var(--line); border-radius: 3px; }
  .ist .etiket { font-size: 0.68rem; letter-spacing: 0.08em; text-transform: uppercase;
                 color: var(--ink-soft); display: block; margin-bottom: 0.2rem; }
  .ist .deger { font-family: "Consolas", "SF Mono", monospace; font-variant-numeric: tabular-nums;
                font-size: 1.2rem; color: var(--ink); }
  .zaman-cizgisi { display: flex; flex-direction: column; gap: 1.1rem; }
  .kayit { background: var(--paper-raised); border: 1px solid var(--line); border-radius: 3px;
           padding: 1.35rem 1.5rem; }
  .kayit-ust { display: flex; align-items: baseline; justify-content: space-between; gap: 1rem;
               flex-wrap: wrap; border-bottom: 1px solid var(--line); padding-bottom: 0.85rem;
               margin-bottom: 0.85rem; }
  .kayit-ust h2 { font-size: 1.25rem; }
  .kayit-ust .coin-yon { font-family: "Consolas", "SF Mono", monospace; font-size: 0.82rem;
                         color: var(--ink-soft); }
  .durum-etiketi { font-size: 0.68rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase;
                   padding: 0.3rem 0.65rem; border-radius: 2px; color: var(--chip-fg); white-space: nowrap; }
  .durum-etiketi.bekleniyor, .durum-etiketi.gecersiz { background: var(--gecersiz); }
  .durum-etiketi.acik { background: var(--acik); }
  .durum-etiketi.kar { background: var(--kar); }
  .durum-etiketi.zarar { background: var(--zarar); }
  .anlatim { font-size: 0.95rem; color: var(--ink-soft); margin-bottom: 1rem; }
  .anlatim strong { color: var(--ink); font-weight: 600; }
  .rakamlar { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 0.9rem 1.5rem; }
  .rakam .etiket { font-size: 0.66rem; letter-spacing: 0.08em; text-transform: uppercase;
                   color: var(--ink-soft); display: block; margin-bottom: 0.2rem; }
  .rakam .deger { font-family: "Consolas", "SF Mono", monospace; font-variant-numeric: tabular-nums;
                  font-size: 1.02rem; color: var(--ink); }
  .rakam .yardim { font-size: 0.76rem; color: var(--ink-soft); margin-top: 0.15rem; }
  .sonuc-satiri { margin-top: 1.1rem; padding-top: 1rem; border-top: 1px dashed var(--line);
                  display: flex; align-items: center; gap: 0.9rem; flex-wrap: wrap; }
  .sonuc-satiri .r-degeri { font-family: "Consolas", "SF Mono", monospace; font-variant-numeric: tabular-nums;
                            font-size: 1.1rem; font-weight: 700; }
  .sonuc-satiri .r-degeri.kar { color: var(--kar); }
  .sonuc-satiri .r-degeri.zarar { color: var(--zarar); }
  .sonuc-satiri .r-aciklama { font-size: 0.82rem; color: var(--ink-soft); }
</style>"""


def rapor_yaz():
    """radar-defteri.html'i TAM GECMISLE (yeniden) uretir — yerel dosya, tarayicida
    acilir, internet/Claude gerekmez. radar.py her turda (5dk) + durum.py cagirinca
    tazelenir -> 'istedigim an kontrol ederim' TAM anlamiyla saglanir."""
    kayitlar = tum_kayitlar()
    o = ozet()
    simdi = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    if not kayitlar:
        icerik = ('<p class="aciklama">Henüz hiçbir radar kurulum adayı bulunmadı. '
                   'Radar bir aday bulduğunda burada otomatik bir kayıt açılacak.</p>')
    else:
        isb = f"%{o['isabet_pct']:.0f}" if o["isabet_pct"] is not None else "—"
        stats = (f'<div class="ozet-cubuk">'
                 f'<div class="ist"><span class="etiket">Açık</span><span class="deger">{o["acik"]}</span></div>'
                 f'<div class="ist"><span class="etiket">Kapalı</span><span class="deger">{o["kapali"]}</span></div>'
                 f'<div class="ist"><span class="etiket">Kazanç</span><span class="deger">{o["kazanc"]}</span></div>'
                 f'<div class="ist"><span class="etiket">Kayıp</span><span class="deger">{o["kayip"]}</span></div>'
                 f'<div class="ist"><span class="etiket">İsabet</span><span class="deger">{isb}</span></div>'
                 f'<div class="ist"><span class="etiket">Toplam (net)</span>'
                 f'<span class="deger">{o["toplam_net_R"]:+.2f}R</span></div></div>')
        kartlar = "".join(_kart_html(t) for t in kayitlar)
        icerik = stats + f'<div class="zaman-cizgisi">{kartlar}</div>'

    html = (f'<!doctype html><html lang="tr"><head><meta charset="utf-8">'
            f'<title>Radar Sicili</title>{_SAYFA_CSS}</head><body><div class="sayfa">'
            f'<div class="ust"><div class="etiket">Radar Sicili · K2 ölçümünden ayrı</div>'
            f'<h1>Radar Kurulum Kayıtları</h1>'
            f'<div class="guncelleme">Son güncelleme: {simdi}</div></div>'
            f'<p class="aciklama">Radar\'ın bulduğu her kurulum adayının nasıl sonuçlandığını gösterir. '
            f'Ana 11 coin\'in sicilinden (K2 ölçümü) tamamen ayrıdır. Bu dosya radar her turda kendiliğinden '
            f'tazelenir — istediğin an açıp bakabilirsin.</p>'
            f'{icerik}</div></body></html>')
    olcucu.atomik_yaz_metin(RADAR_DEFTERI_HTML, html)
    return RADAR_DEFTERI_HTML


if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    coz_tumu()
    print("RADAR SICILI OZET:", ozet())
