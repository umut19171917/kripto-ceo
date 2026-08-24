"""
panel.py — KAGIT BOT ARAYUZU + DURUST OLCUM PANOSU
================================================================================
TASARIM-BOT.md §7 sira 2. Emsal: `radar_defter.py`'nin HTML uretimi (yerel dosya,
tarayicida acilir, internet/Claude gerekmez).

--------------------------------------------------------------------------------
BU PANEL NEDEN FARKLI: iki BAGLAYICI kural altinda yazildi
--------------------------------------------------------------------------------
KURAL 5 (kullanici, 2026-08-23): "PANEL TEK SAYI GOSTERMESIN. Her P&L rakaminin
  yaninda bootstrap guven araligi ve 0,03R gurultu tabani gorunsun.
  '+2,1R' degil, '+2,1R [-0,4, +4,6]'."
  -> `_R()` fonksiyonu TEK SAYI URETEMEZ. Guven araligi olmadan R basilamaz.
     Gurultu tabaninin altindaki degerler gorsel olarak SIFIR gibi gosterilir.

G4 / KIYAS (2026-08-23 denetimi): sistemin tek gecerli kistasi
  "AL-TUT'tan daha iyisini yapmak — maliyetten sonra, daha az dusuşle".
  -> Her sicil ozeti, AYNI PENCEREDE al-tut ile yan yana basilir. Panelin en
     ustundeki kutu budur; kar/zarar rakami ondan SONRA gelir.
  Gerekce: bu proje iki ay boyunca "hangi sinyal calisiyor" diye sordu, "hic bir
  sey yapmamaya kiyasla ne yaptik" diye HIC sormadi. Sordugumuzda sistem
  -%9,6 iken BTC +%28,5, sepet +%45,3 cikti. Bir daha gorunmez olmasin.

--------------------------------------------------------------------------------
UC KAYNAGI DA AYNI MERCEKTEN GOSTERIR
--------------------------------------------------------------------------------
  bot   : `bot-defter.json` — kagit botun kendi pozisyonlari (pozisyon.py)
  ana   : `kripto-defter.json` — canli 11 coin sicili
  radar : `radar-defter.json` — radar sicili
Ana/radar SALT OKUNUR gosterilir; bu modul onlara yazmaz (kullanici kurali 1).

Calistirma: venv\\Scripts\\python.exe panel.py          -> panel.html uretir
            venv\\Scripts\\python.exe panel.py --offline -> kiyas verisini agdan CEKMEZ
Canliya DOKUNMAZ.
"""
import json
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

KOK = Path(__file__).parent
sys.path.insert(0, str(KOK))
import defter
import metrikler as M
import olcucu
import pozisyon as P

PANEL_HTML = KOK / "panel.html"
KIYAS_CACHE = KOK / "panel-kiyas.json"

# SISTEM.md §9.2 — ayni konfig 10 gun arayla +0,05 vs +0,02 verdi.
# Bunun altindaki farklar OLCUM GURULTUSUDUR, bulgu degil.
GURULTU_TABANI = 0.03

# Kiyas sepeti: sistemin BASINDAN BERI izledigi 10 coin (LAB deneysel, disarida).
# Sabit liste -> hayatta kalma yanliligi YOK (sonradan eklenen coin secilmedi).
SEPET = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "LINKUSDT", "XRPUSDT",
         "BNBUSDT", "DOGEUSDT", "ZECUSDT", "ADAUSDT", "NEARUSDT"]

KAYNAKLAR = (
    ("bot", "Kâğıt Bot", "bot-defter.json"),
    ("ana", "Ana Sicil (11 coin)", "kripto-defter.json"),
    ("radar", "Radar Sicili", "radar-defter.json"),
)


# ==============================================================================
#  KURAL 5 — TEK SAYI BASILAMAZ
# ==============================================================================
def _ga(degerler):
    """Ortalamanin bootstrap %95 guven araligi (metrikler.py'den — kopya degil).
    n<10 ise None: ders 13 (2026-08-23) — kucuk hucreye aralik yazmak YANILTIR,
    cunku bootstrap o birkac gozlemin esiri olur. Sayiyi ver, araligi verme."""
    if len(degerler) < 10:
        return None
    return M.bootstrap_ga(degerler)


def _R(toplam, degerler, birim="R"):
    """R degerini GUVEN ARALIGI ile birlikte HTML olarak basar. KURAL 5.

    Tek sayi donmez — ya aralik ya da "aralik yok (n<10)" damgasi tasir.
    Gurultu tabaninin altindaki ORTALAMA degerler 'gurultu' sinifi alir ve
    gorsel olarak sifirdan ayrilmaz.
    """
    if not degerler:
        return '<span class="rq yok">—</span>'
    n = len(degerler)
    ort = toplam / n
    ga = _ga(degerler)
    sinif = "kar" if toplam > 0 else ("zarar" if toplam < 0 else "notr")
    if abs(ort) < GURULTU_TABANI:
        sinif = "gurultu"
    if ga is None:
        ek = f'<span class="ga yok">n={n} · aralık yok</span>'
    else:
        # Toplam degil ORTALAMA icin aralik; toplama olceklenmis hali de verilir.
        ek = (f'<span class="ga">işlem başına {ort:+.3f} '
              f'[{ga[0]:+.3f}, {ga[1]:+.3f}]</span>')
        if ga[0] <= 0 <= ga[1]:
            ek += '<span class="rozet notr-r">sıfırı kapsıyor</span>'
        elif ga[0] > 0:
            ek += '<span class="rozet iyi">sıfırın üstünde</span>'
        else:
            ek += '<span class="rozet kotu">sıfırın altında</span>'
    return f'<span class="rq {sinif}">{toplam:+.2f}{birim}</span>{ek}'


def _yuzde(v):
    return f"{v:+.1f}%"


# ==============================================================================
#  KIYAS — AL-TUT (G4)
# ==============================================================================
def _fiyat_at(sym, dt):
    raw = olcucu._get("/fapi/v1/klines", {"symbol": sym, "interval": "1h",
                                          "startTime": int(dt.timestamp() * 1000), "limit": 1})
    return float(raw[0][4]) if raw else None


def _simdi(sym):
    k = olcucu.get_klines(sym, "1h", 2)
    return k[-1]["c"] if k else None


def _btc_dusus(dt):
    """BTC'nin ayni penceredeki maksimum dusuşu (saatlik high/low)."""
    kl, cur = [], int(dt.timestamp() * 1000)
    while True:
        raw = olcucu._get("/fapi/v1/klines", {"symbol": "BTCUSDT", "interval": "1h",
                                              "startTime": cur, "limit": 1500})
        if not raw:
            break
        kl += raw
        if len(raw) < 1500:
            break
        cur = raw[-1][0] + 3_600_000
    tepe, dd = -1e18, 0.0
    for k in kl:
        tepe = max(tepe, float(k[2]))
        dd = min(dd, float(k[3]) / tepe - 1)
    return dd * 100


def kiyas(baslangic_iso, offline=False):
    """AYNI PENCEREDE al-tut ne yapardi? Sonuc cache'lenir (offline calisabilsin)."""
    cache = {}
    if KIYAS_CACHE.exists():
        try:
            cache = json.loads(KIYAS_CACHE.read_text(encoding="utf-8"))
        except Exception:
            cache = {}
    if offline:
        return cache.get(baslangic_iso)
    d0 = datetime.fromisoformat(baslangic_iso)
    try:
        b0, b1 = _fiyat_at("BTCUSDT", d0), _simdi("BTCUSDT")
        btc = (b1 / b0 - 1) * 100
        tot, k = 0.0, 0
        for c in SEPET:
            try:
                p0, p1 = _fiyat_at(c, d0), _simdi(c)
                if p0 and p1:
                    tot += (p1 / p0 - 1) * 100
                    k += 1
            except Exception:
                pass
        sonuc = {"btc_pct": btc, "sepet_pct": tot / k if k else None,
                 "sepet_n": k, "btc_dusus_pct": _btc_dusus(d0),
                 "olcum": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    except Exception as e:
        return cache.get(baslangic_iso)
    cache[baslangic_iso] = sonuc
    try:
        olcucu.atomik_yaz(KIYAS_CACHE, cache)
    except Exception:
        pass
    return sonuc


# ==============================================================================
#  SICIL OKUMA — uc kaynak, tek mercek
# ==============================================================================
def _bot_kayitlari():
    try:
        d = json.loads((KOK / "bot-defter.json").read_text(encoding="utf-8"))
    except Exception:
        return [], []
    poz = d.get("pozisyonlar", [])
    kapali = [p for p in poz if p.get("durum") in P.KAPALI_DURUMLAR]
    acik = [p for p in poz if p.get("durum") in P.ACIK_DURUMLAR]
    return kapali, acik


def _sicil_kayitlari(dosya):
    """Ana/radar: kanonik kapanmis + acik. SALT OKUNUR."""
    try:
        ham = json.loads((KOK / dosya).read_text(encoding="utf-8"))["tahminler"]
    except Exception:
        return [], []
    kan = [t for t in ham if t.get("kaynak", "canli") != "geri-doldurma"
           and t.get("sicil") != "deneysel"]
    kapali = [t for t in kan if t.get("durum") in M.KAPALI]
    acik = [t for t in kan if t.get("durum") in ("beklemede", "izleniyor")]
    return kapali, acik


def _R_listesi(kayitlar, kaynak):
    if kaynak == "bot":
        return [p["pnl_R"] for p in kayitlar if p.get("pnl_R") is not None]
    return [x for x in (M.net_r(t) for t in kayitlar) if x is not None]


def _bilesik(rler, risk_pct=1.0):
    """1000 dolar bu sicili takip etseydi: her islem GUNCEL bakiyenin %1'i.
    ⚠ SIRALI varsayim — gercekte pozisyonlar ORTUSUR (radar'da tepe 10 esZamanli).
    Bu yuzden yaklasiktir ve panelde oyle etiketlenir."""
    b, tepe, dd = 1000.0, 1000.0, 0.0
    egri = [b]
    for r in rler:
        b *= (1 + risk_pct / 100.0 * r)
        tepe = max(tepe, b)
        dd = min(dd, b / tepe - 1)
        egri.append(b)
    return b, dd * 100, egri


def ozet(kaynak, ad, dosya, offline=False):
    kapali, acik = (_bot_kayitlari() if kaynak == "bot" else _sicil_kayitlari(dosya))
    if kaynak != "bot":
        kapali = sorted(kapali, key=lambda t: t.get("kapanis_tarih") or "")
    else:
        kapali = sorted(kapali, key=lambda p: p.get("kapanis_tarih") or "")
    rler = _R_listesi(kapali, kaynak)
    o = {"kaynak": kaynak, "ad": ad, "kapali": len(kapali), "acik": len(acik),
         "rler": rler, "kayitlar": kapali, "acik_kayitlar": acik}
    if not rler:
        return o
    o["net"] = sum(rler)
    o["ort"] = o["net"] / len(rler)
    o["ga"] = _ga(rler)
    o["psr"] = M.psr(rler) if len(rler) >= 10 else None
    o["isabet"] = 100 * sum(1 for x in rler if x > 0) / len(rler)
    o["bakiye"], o["dusus"], o["egri"] = _bilesik(rler)
    tarihler = [t.get("tarih") for t in kapali if t.get("tarih")]
    o["baslangic"] = min(tarihler) if tarihler else None
    if o["baslangic"]:
        o["kiyas"] = kiyas(o["baslangic"], offline=offline)
    # maliyet muhasebesi
    if kaynak == "bot":
        o["komisyon"] = sum(p.get("komisyon_usd") or 0 for p in kapali)
        o["funding"] = sum(p.get("funding_toplam_usd") or 0 for p in kapali)
    else:
        o["komisyon"] = sum(defter.maliyet_R(t) for t in kapali) * 10.0  # 1000$ @ %1
        o["funding"] = None                                              # sicilde YOK
    return o


# ==============================================================================
#  HTML
# ==============================================================================
_CSS = """<style>
 :root{--paper:#E4E1D6;--raised:#EDEAE0;--ink:#1A2130;--soft:#4B5160;--line:#C9C3B2;
  --accent:#8A6A2F;--kar:#3C6E47;--zarar:#A23E2E;--gurultu:#8B8377;--uyari:#8A4B2F;--chip:#F4F2EC;}
 @media (prefers-color-scheme:dark){:root{--paper:#14171C;--raised:#1B1F26;--ink:#E7E3D6;
  --soft:#A9A597;--line:#33362F;--accent:#C9A227;--kar:#5C9B6C;--zarar:#C25A46;
  --gurultu:#6E6A5E;--uyari:#D08A5C;--chip:#14171C;}}
 *{box-sizing:border-box}
 body{background:var(--paper);color:var(--ink);font-family:"Segoe UI",system-ui,sans-serif;
  line-height:1.55;padding:2.5rem 1.1rem 5rem;-webkit-font-smoothing:antialiased;margin:0}
 .sayfa{max-width:940px;margin:0 auto}
 h1,h2,h3{font-family:Georgia,"Palatino Linotype",serif;font-weight:600;margin:0 0 .4rem}
 h1{font-size:1.75rem} h2{font-size:1.2rem;margin-top:2.2rem}
 .ust{border-bottom:2px solid var(--line);padding-bottom:1rem;margin-bottom:1.4rem}
 .etiket{font-size:.72rem;letter-spacing:.13em;text-transform:uppercase;color:var(--soft)}
 .aciklama{color:var(--soft);font-size:.9rem;margin:.4rem 0 1rem}
 .kutu{background:var(--raised);border:1px solid var(--line);border-radius:9px;
  padding:1rem 1.15rem;margin:.9rem 0}
 .kiyas{border-left:5px solid var(--accent)}
 table{width:100%;border-collapse:collapse;font-size:.9rem;margin:.5rem 0}
 th,td{text-align:left;padding:.42rem .5rem;border-bottom:1px solid var(--line)}
 th{font-size:.72rem;letter-spacing:.08em;text-transform:uppercase;color:var(--soft);font-weight:600}
 td.sag,th.sag{text-align:right;font-variant-numeric:tabular-nums}
 .rq{font-weight:700;font-variant-numeric:tabular-nums}
 .rq.kar{color:var(--kar)} .rq.zarar{color:var(--zarar)}
 .rq.gurultu{color:var(--gurultu)} .rq.notr,.rq.yok{color:var(--soft)}
 .ga{display:inline-block;margin-left:.5rem;font-size:.78rem;color:var(--soft);
  font-variant-numeric:tabular-nums}
 .ga.yok{font-style:italic}
 .rozet{display:inline-block;margin-left:.4rem;padding:.06rem .42rem;border-radius:999px;
  font-size:.68rem;letter-spacing:.05em;background:var(--gurultu);color:var(--chip)}
 .rozet.iyi{background:var(--kar)} .rozet.kotu{background:var(--zarar)}
 .rozet.notr-r{background:var(--soft)}
 .uyari-kutu{border-left:5px solid var(--uyari);background:var(--raised)}
 .uyari-kutu li{margin:.3rem 0;font-size:.88rem}
 .kucuk{font-size:.8rem;color:var(--soft)}
 .taban{border-top:1px dashed var(--line);margin-top:.6rem;padding-top:.5rem;
  font-size:.78rem;color:var(--soft)}
 .kaz{display:flex;flex-wrap:wrap;gap:1.4rem;margin:.5rem 0}
 .kaz div{min-width:110px} .kaz .deger{font-size:1.15rem;font-weight:700;display:block;
  font-variant-numeric:tabular-nums}
 .sar{overflow-x:auto}
</style>"""


def _kiyas_html(o):
    k = o.get("kiyas")
    if not k:
        return ('<div class="kutu kiyas"><div class="etiket">Kıyas</div>'
                '<p class="kucuk">Al-tut verisi çekilemedi (ağ yok / önbellek boş). '
                'Panel çevrimiçi bir kez çalıştırılınca dolar.</p></div>')
    sis = (o["bakiye"] / 1000 - 1) * 100
    sepet = k.get("sepet_pct")
    satirlar = [
        ("Sistem (bileşik, 1000$ @ %1 risk)", sis, o.get("dusus")),
        ("BTC alıp tut", k.get("btc_pct"), k.get("btc_dusus_pct")),
        (f"{k.get('sepet_n', 0)} coin eşit ağırlık alıp tut", sepet, None),
    ]
    tr = ""
    for ad, deg, dd in satirlar:
        if deg is None:
            continue
        vurgu = ' style="font-weight:700"' if ad.startswith("Sistem") else ""
        ddm = f"{dd:.1f}%" if dd is not None else "—"
        renk = "kar" if deg > 0 else "zarar"
        tr += (f'<tr{vurgu}><td>{ad}</td>'
               f'<td class="sag"><span class="rq {renk}">{_yuzde(deg)}</span></td>'
               f'<td class="sag">{ddm}</td></tr>')
    fark = (sis - sepet) if sepet is not None else None
    hkm = ""
    if fark is not None:
        iyi = fark > 0
        hkm = (f'<p class="kucuk" style="margin-top:.6rem">'
               f'<strong>Hüküm:</strong> sistem, sepeti alıp tutmaya kıyasla '
               f'<span class="rq {"kar" if iyi else "zarar"}">{fark:+.1f} puan</span> '
               f'{"ÖNDE" if iyi else "GERİDE"}. '
               f'{"" if iyi else "Bir işlem sisteminin var olma sebebi bunu geçmektir."}</p>')
    return (f'<div class="kutu kiyas"><div class="etiket">Kıyas — tek geçerli kıstas</div>'
            f'<h3>Al-tutmaktan iyisini yapabildi mi?</h3>'
            f'<p class="kucuk">Aynı pencere: {o["baslangic"][:10]} → bugün. '
            f'Komisyon: sistemde var, al-tutta ~yok.</p>'
            f'<div class="sar"><table><tr><th>Yaklaşım</th><th class="sag">Sonuç</th>'
            f'<th class="sag">Maks düşüş</th></tr>{tr}</table></div>{hkm}</div>')


def _ozet_html(o):
    if not o["rler"]:
        return (f'<div class="kutu"><h2>{o["ad"]}</h2>'
                f'<p class="kucuk">Henüz kapanmış işlem yok'
                f'{" — kâğıt bot çalıştırılmadı." if o["kaynak"] == "bot" else "."}</p></div>')
    psr = f'%{100 * o["psr"]:.1f}' if o["psr"] is not None else "n<10"
    kom = o.get("komisyon") or 0
    fnd = o.get("funding")
    fnd_s = f'{fnd:+.2f}$' if fnd is not None else '<span class="kucuk">sicilde yok</span>'
    return (
        f'<div class="kutu"><h2>{o["ad"]}</h2>'
        f'<div class="kaz">'
        f'<div><span class="etiket">Kapalı</span><span class="deger">{o["kapali"]}</span></div>'
        f'<div><span class="etiket">Açık</span><span class="deger">{o["acik"]}</span></div>'
        f'<div><span class="etiket">İsabet</span><span class="deger">%{o["isabet"]:.0f}</span></div>'
        f'<div><span class="etiket">PSR</span><span class="deger">{psr}</span></div>'
        f'<div><span class="etiket">1000$ → </span><span class="deger">{o["bakiye"]:.0f}$</span></div>'
        f'<div><span class="etiket">Maks düşüş</span><span class="deger">{o["dusus"]:.1f}%</span></div>'
        f'</div>'
        f'<p style="margin:.5rem 0"><span class="etiket">Net sonuç</span><br>'
        f'{_R(o["net"], o["rler"])}</p>'
        f'<div class="taban">Gürültü tabanı <strong>{GURULTU_TABANI}R</strong> — '
        f'işlem başına bundan küçük farklar ölçüm gürültüsüdür, bulgu değildir '
        f'(SİSTEM.md §9.2). · Komisyona giden: <strong>{kom:.2f}$</strong> '
        f'(1000$ hesapta) · Funding: {fnd_s}</div>'
        f'<div class="taban">⚠ Bileşik bakiye <em>sıralı</em> işlem varsayar; '
        f'gerçekte pozisyonlar örtüşür (radar tepe: 10 eşzamanlı, 7\'si aynı yön). '
        f'Gerçek hesap eğrisi ancak kâğıt bot koşunca çıkar.</div>'
        f'</div>')


def _acik_html(o):
    if not o["acik_kayitlar"]:
        return ""
    tr = ""
    for x in o["acik_kayitlar"][:20]:
        if o["kaynak"] == "bot":
            liq = x.get("likidasyon_fiyati")
            uy = P.uyarilar(x)
            tehlike = any("STOP'UN ICINDE" in u for u in uy)
            tr += (f'<tr><td>{x.get("sembol")}</td><td>{x.get("yon")}</td>'
                   f'<td class="sag">{x.get("giris")}</td><td class="sag">{x.get("stop")}</td>'
                   f'<td class="sag">{liq if liq else "—"}</td>'
                   f'<td class="sag">{x.get("kaldirac")}x</td>'
                   f'<td>{"<span class=\"rozet kotu\">LİKİDASYON STOP İÇİNDE</span>" if tehlike else ""}</td></tr>')
        else:
            tr += (f'<tr><td>{x.get("token")}</td><td>{x.get("yon")}</td>'
                   f'<td class="sag">{x.get("giris")}</td><td class="sag">{x.get("stop")}</td>'
                   f'<td class="sag">—</td><td class="sag">—</td>'
                   f'<td>{x.get("durum")}</td></tr>')
    return (f'<div class="kutu"><h3>Açık — {o["ad"]}</h3><div class="sar"><table>'
            f'<tr><th>Sembol</th><th>Yön</th><th class="sag">Giriş</th>'
            f'<th class="sag">Stop</th><th class="sag">Likidasyon</th>'
            f'<th class="sag">Kaldıraç</th><th>Not</th></tr>{tr}</table></div></div>')


def _durustluk_html():
    """Panelin gizlemedigi seyler. TASARIM-BOT §4-5 + denetim bulgulari."""
    try:
        import onkayit_radar as OK
        n = len(OK.uygun_islemler())
        onk = f"{n}/30 — hüküm basılmadı"
    except Exception:
        onk = "okunamadı"
    md = [
        f"<strong>Ön kayıt `radar-v2` açık:</strong> {onk}. Kapanana kadar "
        "`defter.py` · `radar_defter.py` · `squeeze_scores` <strong>dokunulmaz</strong>.",
        "<strong>Gap/kayma modellenmedi (E1):</strong> stop tam seviyeden dolduruldu "
        "varsayılıyor; çalkantıda gerçek dolum daha kötü olur.",
        "<strong>MMR tahmindir</strong> (%1, muhafazakâr) — kesin değer imzalı "
        "Binance endpoint'i ister.",
        "<strong>Hayatta kalan tahmin bulgusu: 0/14.</strong> Sıkışma skorunun yön "
        "bilgisi taşımadığı iki bağımsız yöntemle ölçüldü (964k kayıt + canlı ρ≈0).",
        "<strong>K2 gündeminde iki açık arıza:</strong> funding eşiği tavana yapışması "
        "(ana %55, radar %35) ve L/S bileşeninin simetrisizliği (+20 puan short "
        "sinyaline 3 kat daha sık). İkisi de <em>test edilmedi</em>.",
        "<strong>Radar'da risk tavanı ve cooldown YOK</strong> (ana sicilde var). "
        "Tepe: 10 eşzamanlı pozisyon, 7'si aynı yönde, korelasyon 0,69.",
        "<strong>Sistem hiç düşen piyasada ölçülmedi.</strong> BTC canlı ölçümün ilk "
        "gününden beri düşmedi (60.044 → bugün).",
    ]
    return ('<div class="kutu uyari-kutu"><div class="etiket">Panelin gizlemediği şeyler</div>'
            '<h3>Bu rakamları okurken bilmen gerekenler</h3><ul>'
            + "".join(f"<li>{x}</li>" for x in md) + "</ul></div>")


def panel_html(offline=False):
    ozetler = [ozet(k, ad, dosya, offline=offline) for k, ad, dosya in KAYNAKLAR]
    simdi = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    ana = next((o for o in ozetler if o["kaynak"] == "ana"), None)
    bot = next((o for o in ozetler if o["kaynak"] == "bot"), None)
    bas = bot if (bot and bot["rler"]) else ana
    kiyas_blok = _kiyas_html(bas) if bas and bas["rler"] else ""
    govde = "".join(_ozet_html(o) + _acik_html(o) for o in ozetler)
    return (
        f'<!doctype html><html lang="tr"><head><meta charset="utf-8">'
        f'<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>Kripto Panel</title>{_CSS}</head><body><div class="sayfa">'
        f'<div class="ust"><div class="etiket">Kâğıt bot · ölçüm panosu · gerçek para YOK</div>'
        f'<h1>Panel</h1><div class="kucuk">Son güncelleme: {simdi}</div></div>'
        f'<p class="aciklama">Hiçbir kâr/zarar rakamı tek başına gösterilmez — her birinin '
        f'yanında <strong>bootstrap %95 güven aralığı</strong> ve <strong>{GURULTU_TABANI}R '
        f'gürültü tabanı</strong> vardır. Bir sayının aralığı sıfırı kapsıyorsa, o sayı '
        f'"kazandık" demek değildir; "ayırt edemiyoruz" demektir.</p>'
        f'{kiyas_blok}{govde}{_durustluk_html()}'
        f'<p class="kucuk" style="margin-top:2rem">panel.py · canlı sicillere yazmaz · '
        f'ana ve radar salt okunur</p>'
        f'</div></body></html>')


def yaz(offline=False):
    olcucu.atomik_yaz_metin(PANEL_HTML, panel_html(offline=offline))
    return PANEL_HTML


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    off = "--offline" in sys.argv
    yol = yaz(offline=off)
    print(f"panel yazildi: {yol}")
    for k, ad, dosya in KAYNAKLAR:
        o = ozet(k, ad, dosya, offline=True)
        if o["rler"]:
            ga = o["ga"]
            gs = f"[{ga[0]:+.3f}, {ga[1]:+.3f}]" if ga else "aralik yok"
            print(f"  {ad:22s} n={o['kapali']:3d}  net {o['net']:+7.2f}R  "
                  f"islem basina {o['ort']:+.3f} {gs}")
        else:
            print(f"  {ad:22s} kapanmis islem yok")
