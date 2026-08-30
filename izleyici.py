"""
izleyici.py — GERCEK ZAMANLI izleyici (Faz 3 cekirdek)
================================================================================
Ne yapar:
  1) WebSocket @forceOrder akisindan CANLI likidasyonlari yakalar (her olay aninda).
  2) Periyodik olarak olcucu.py'nin REST + matematigini calistirir (snapshot).
  3) Ikisini birlestirir -> signals.json'a "live_liq" + "kademe (cascade)" yazar.

Boylece sikismanin sadece KURULUMUNU degil, TETIKLENDIGI ANI da goruruz:
  - side=SELL  -> bir LONG likide oldu  -> asagi baski (long squeeze yakiti gercege dondu)
  - side=BUY   -> bir SHORT likide oldu -> yukari baski (short squeeze)

Tek process, tek pencere. Calistirma:
    venv\\Scripts\\python.exe izleyici.py            # surekli
    venv\\Scripts\\python.exe izleyici.py --seconds 60  # 60 sn calis, dur (hizli kontrol)
"""

import sys
import json
import time
import asyncio
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

import websockets

import olcucu       # REST cekiciler + matematik + log_line + OUT_FILE + SYMBOLS
import kalibrasyon  # self-kalibrasyon (esikler.json'u tazeler)
import makro        # Kanal 2: makro/jeopolitik guvenlik kapisi (makro.json)
import defter       # tahmin kaydi + sonuc takibi (kripto-defter.json)
import bosluk       # bosluk kurtarma (PC kapali kaldigi araligi tamamlar)
import bildirim     # Telegram kanali (C1); token yoksa sessiz no-op
import likidasyon   # Coinalyze REST likidasyon beslemesi (olu WS'in yerine; ~2-3dk gecikmeli)
import yedek        # kritik dosyalarin gunluk Google Drive yedegi (idempotent, fail-safe)

# ============================== CONFIG ==============================
WS_BASE = "wss://fstream.binance.com/stream"
SNAPSHOT_SEC = 30           # REST snapshot araligi
LIQ_KEEP_SEC = 3600         # likidasyon olaylarini 1 saat tut
CASCADE_WINDOW_SEC = 300    # "kademe" penceresi: son 5 dk
CASCADE_USD = 1_000_000     # son 5dk tek tarafta > bu => KADEME aktif (canli veride kalibre)
RECAL_SEC = 12 * 3600       # esikleri her 12 saatte bir yeniden kalibre et (self-kalibrasyon)
MAKRO_SEC = 120             # Kanal 2 (makro/jeopolitik) kapiyi 2 dakikada bir tazele
OZET_SAAT_UTC = 18          # gunluk Telegram ozeti (18 UTC = 21:00 TR)
OZET_DURUM_FILE = Path(__file__).parent / "ozet-durum.json"   # son gonderim gunu (restart mukerrer ozet yollamasin)

# her sembol icin likidasyon olaylari: deque[(ts, side, usd, price)]
liq_events = {s: deque() for s in olcucu.SYMBOLS}

# WS'ten gelen HAM mesaj sayisi. 2026-07-01 teshisi: bu ortamda WS akislari veri
# vermiyor (baglanti kurulur ama mesaj gelmez) -> live_liq sifirlari "olay yok"
# degil "veri yok" demek olabilir. Sayac 0 ise signals.json'a durust bayrak yazilir.
ws_mesaj_sayisi = 0

# Coinalyze beslemesi durumu (likidasyon_loop gunceller)
coinalyze_son_ok = 0.0        # son basarili cekim (epoch); 5dk'dan eskiyse veri-yok say
cascade_esik = {}             # per-symbol cascade esigi USD (likidasyon.kalibre; yoksa CASCADE_USD)


# ============================== Likidasyon toplama ==============================
def add_liq(sym, side, usd, price, ts=None):
    """ts: olayin gercek zamani (Coinalyze bar'lari gecmis damgali gelir); yoksa simdi."""
    liq_events[sym].append((ts or time.time(), side, usd, price))


def liq_summary(sym, now):
    dq = liq_events[sym]
    while dq and now - dq[0][0] > LIQ_KEEP_SEC:   # eski olaylari at
        dq.popleft()
    long5 = short5 = long1h = short1h = 0.0
    for ts, side, usd, _ in dq:
        is_long = (side == "SELL")  # long likide edildi
        if now - ts <= CASCADE_WINDOW_SEC:
            if is_long:
                long5 += usd
            else:
                short5 += usd
        if is_long:
            long1h += usd
        else:
            short1h += usd
    esik = cascade_esik.get(sym, CASCADE_USD)   # per-symbol kalibre (Coinalyze P99.5); yoksa eski sabit
    cascade = None
    if long5 >= esik and long5 >= short5:
        cascade = "long"    # longlar likide oluyor -> ASAGI kademe
    elif short5 >= esik:
        cascade = "short"   # shortlar likide oluyor -> YUKARI kademe
    return {
        "long_liq_5m_usd": round(long5),
        "short_liq_5m_usd": round(short5),
        "long_liq_1h_usd": round(long1h),
        "short_liq_1h_usd": round(short1h),
        "cascade": cascade,
    }


# ============================== WebSocket tuketici ==============================
async def ws_consumer():
    global ws_mesaj_sayisi
    streams = "/".join(f"{s.lower()}@forceOrder" for s in olcucu.SYMBOLS)
    url = f"{WS_BASE}?streams={streams}"
    while True:
        try:
            async with websockets.connect(url, ping_interval=None) as ws:
                olcucu.log_line(f"[WS] baglandi -> {streams}")
                async for raw in ws:
                    ws_mesaj_sayisi += 1
                    msg = json.loads(raw)
                    o = msg.get("data", {}).get("o")
                    if not o:
                        continue
                    sym = o.get("s")
                    if sym not in liq_events:
                        continue
                    side = o["S"]
                    price = float(o.get("ap") or o["p"])
                    usd = price * float(o["q"])
                    add_liq(sym, side, usd, price)
                    yon = "LONG likide" if side == "SELL" else "SHORT likide"
                    olcucu.log_line(f"    [LIKIDASYON] {sym} {yon} ${usd:,.0f} @ {price}")
        except Exception as e:
            olcucu.log_line(f"[WS] koptu, 5sn sonra yeniden baglanilacak: {type(e).__name__}: {e}")
            await asyncio.sleep(5)


# ============================== Periyodik snapshot ==============================
async def snapshot_loop():
    loop = asyncio.get_event_loop()
    while True:
        t0 = time.time()
        now = time.time()
        out = {"updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "source": "binance-rest + coinalyze-likidasyon(1dk,~2-3dk gecikme)", "symbols": {}}
        # 11 coin siralı islenirse 30sn'lik turu asar -> REST+matematik PARALEL
        # (thread executor; her sembolun hatasi kendi hucresinde kalir).
        async def _analiz(sym):
            try:
                return sym, await loop.run_in_executor(None, olcucu.analyze_symbol, sym)
            except Exception as e:
                return sym, {"error": f"{type(e).__name__}: {e}"}

        for sym, d in await asyncio.gather(*[_analiz(s) for s in olcucu.SYMBOLS]):
            if "error" not in d:
                d["live_liq"] = liq_summary(sym, now)
                # Durustluk bayragi: WS canli mi > Coinalyze mi (1dk bar, ~2-3dk gecikme) > veri yok.
                if ws_mesaj_sayisi > 0:
                    d["live_liq"]["veri"] = "canli-ws"
                elif time.time() - coinalyze_son_ok < 300:
                    d["live_liq"]["veri"] = "coinalyze-1dk"
                else:
                    d["live_liq"]["veri"] = "pasif/veri-yok"
                cas = d["live_liq"]["cascade"]
                sq = d["squeeze"]
                if cas == "short" and sq["short_squeeze"] >= 50:
                    sq["note"] = (f"SHORT SQUEEZE TETIKLENDI (canli: short likidasyon "
                                  f"${d['live_liq']['short_liq_5m_usd']:,}/5dk) -> yukari")
                elif cas == "long" and sq["long_squeeze"] >= 50:
                    sq["note"] = (f"LONG SQUEEZE TETIKLENDI (canli: long likidasyon "
                                  f"${d['live_liq']['long_liq_5m_usd']:,}/5dk) -> asagi")
            out["symbols"][sym] = d

        olcucu.atomik_yaz(olcucu.OUT_FILE, out)

        try:
            # guncelle artik 1dk mum ceker (fitil-tabanli takip) -> bloklamasin
            await loop.run_in_executor(None, defter.guncelle, out)
        except Exception as e:
            olcucu.log_line(f"[DEFTER] hata: {type(e).__name__}: {e}")

        stamp = out["updated_at"]
        for sym, d in out["symbols"].items():
            if "error" in d:
                olcucu.log_line(f"[{stamp}] {sym}: HATA {d['error']}")
                continue
            ll, sq = d["live_liq"], d["squeeze"]
            kademe = f" | KADEME: {ll['cascade'].upper()}" if ll["cascade"] else ""
            if ll.get("veri") == "pasif/veri-yok":
                likid = "| likid VERI-YOK (WS pasif)"
            else:
                likid = f"| 5dk likid L${ll['long_liq_5m_usd']:,} S${ll['short_liq_5m_usd']:,}{kademe}"
            olcucu.log_line(f"[{stamp}] {sym} ${d['price']} | SS {sq['short_squeeze']} LS {sq['long_squeeze']} {likid}")
            if sq["note"] != "yok":
                olcucu.log_line(f"    >>> ALARM: {sq['note']}")

        await asyncio.sleep(max(1, SNAPSHOT_SEC - (time.time() - t0)))


async def recalib_loop():
    """Acilista + her RECAL_SEC'te esikleri tarihsel veriyle yeniden hesapla (esikler.json)."""
    loop = asyncio.get_event_loop()
    while True:
        try:
            cfg = await loop.run_in_executor(None, kalibrasyon.write_config)
            syms = [s for s in cfg["symbols"] if "error" not in cfg["symbols"][s]]
            olcucu.log_line(f"[KALIBRASYON] esikler guncellendi ({len(syms)} sembol): {', '.join(syms)}")
        except Exception as e:
            olcucu.log_line(f"[KALIBRASYON] hata: {type(e).__name__}: {e}")
        await asyncio.sleep(RECAL_SEC)


async def makro_loop():
    """Kanal 2: makro.json'u periyodik tazeler (DXY rejim + takvim + sok ayak izi).
    Telegram'a sadece kapi DEGISIMI bildirilir (2dk'da bir durum spami degil)."""
    loop = asyncio.get_event_loop()
    onceki_kapi = None
    while True:
        try:
            m = await loop.run_in_executor(None, makro.write_makro)
            if m["kapi"] != "ACIK":
                olcucu.log_line(f"[MAKRO] KAPI {m['kapi']} (boyut {m['boyut_carpani']}): " + " ; ".join(m["notlar"]))
            if onceki_kapi is not None and m["kapi"] != onceki_kapi:
                bildirim.gonder(f"[MAKRO] kapi degisti: {onceki_kapi} -> {m['kapi']} "
                                f"(boyut x{m['boyut_carpani']})\n" + " ; ".join(m["notlar"][:2]))
            onceki_kapi = m["kapi"]
        except Exception as e:
            olcucu.log_line(f"[MAKRO] hata: {type(e).__name__}: {e}")
        await asyncio.sleep(MAKRO_SEC)


async def likidasyon_loop():
    """Coinalyze'dan 60 sn'de bir KAPANMIS 1dk likidasyon barlarini cek (TEK istek,
    tum semboller) -> liq_events'e bar zaman damgasiyla isle. Ilk turda 60dk geriye
    bakar (1s penceresi hemen isinir). Gunde 1 cascade esigi kalibrasyonu.
    Config yoksa donguden cikar; her hata cekirdegi ETKILEMEZ (throttled log)."""
    global coinalyze_son_ok, cascade_esik
    if not likidasyon.aktif():
        olcucu.log_line("[LIKIDASYON] coinalyze.json yok - besleme PASIF (WS de olu -> likid veri-yok)")
        return
    loop = asyncio.get_event_loop()
    cursor = {}          # sym -> islenen son bar ts (cift sayim olmasin)
    son_hata_log = 0.0
    ilk = True
    son_kalibrasyon = 0.0
    while True:
        try:
            if time.time() - son_kalibrasyon > 3600:   # dosya-mtime throttle asil fren (24s)
                son_kalibrasyon = time.time()
                e = await loop.run_in_executor(None, likidasyon.kalibre, olcucu.SYMBOLS)
                if e:
                    cascade_esik = e
                    olcucu.log_line(f"[LIKIDASYON] cascade esikleri ({len(e)} sembol, P{likidasyon.KAL_PCT}): "
                                    + ", ".join(f"{s} ${v/1e3:,.0f}k" for s, v in list(e.items())[:4]) + " ...")
            bars = await loop.run_in_executor(None, likidasyon.taze_bars,
                                              olcucu.SYMBOLS, 60 if ilk else 10)
            ilk = False
            n_yeni = 0
            for sym, satirlar in bars.items():
                for t, l_usd, s_usd in satirlar:
                    if t <= cursor.get(sym, 0):
                        continue
                    cursor[sym] = t
                    if l_usd > 0:
                        add_liq(sym, "SELL", l_usd, 0, ts=t)   # long likide -> asagi baski
                    if s_usd > 0:
                        add_liq(sym, "BUY", s_usd, 0, ts=t)    # short likide -> yukari baski
                    n_yeni += 1
            if bars:
                coinalyze_son_ok = time.time()
        except Exception as ex:
            if time.time() - son_hata_log > 3600:
                son_hata_log = time.time()
                olcucu.log_line(f"[LIKIDASYON] cekim hatasi: {type(ex).__name__}: {str(ex)[:70]}")
        await asyncio.sleep(60)


async def ozet_loop():
    """Gunde bir Telegram ozeti (OZET_SAAT_UTC sonrasi ilk kontrol). Token yoksa no-op.
    Son gonderim gunu DOSYADA tutulur (2026-07-06 duzeltmesi): izleyici 18 UTC
    sonrasi yeniden baslarsa ayni gunun ozeti MUKERRER gitmez. Gonderim basarisizsa
    'gonderildi' sayilmaz -> 5 dk sonra yeniden denenir."""
    try:
        son_gun = json.loads(OZET_DURUM_FILE.read_text(encoding="utf-8")).get("son_ozet_gun")
    except Exception:
        son_gun = None
    panel_gun = None          # panel'in ONLINE tazelendigi son gun (madde 2.5)
    while True:
        try:
            now = datetime.now(timezone.utc)
            gun = now.date().isoformat()
            if now.hour >= OZET_SAAT_UTC and son_gun != gun and bildirim.aktif():
                o = defter.ozet()
                T = defter._yukle()["tahminler"]
                rl = defter.acik_risk_pct(T, "LONG")
                rs = defter.acik_risk_pct(T, "SHORT")
                isb = f"%{o['isabet_pct']}" if o["isabet_pct"] is not None else "-"
                radar_s = ""
                try:
                    import radar as _radar   # ayri surec ama radar_ozeti sadece json okur
                    r = _radar.radar_ozeti(24)
                    if r:
                        en = f" (en buyuk: {r['hareket'][0][0]} %{r['hareket'][0][1]:.0f})" if r["hareket"] else ""
                        radar_s = (f"\nradar 24s: {len(r['hareket'])} hareket alarmi{en} | "
                                   f"{len(r['kurulum'])} kurulum adayi - detay: radar.log")
                except Exception:
                    pass
                # G4 KIYAS (madde 2.3, 2026-08-30). "Sistem calisiyor mu" sorusu
                # R toplamiyla CEVAPLANMAZ; ancak AYNI PENCEREDE al-tut ile yan
                # yana konunca cevaplanir. Iki ay tam bu satir olmadigi icin
                # kacti (TASARIM-BOT G4).
                # 🔴 OLGUNUN TEK SAHIBI panel.kiyas() — burasi HESAPLAMAZ, CAGIRIR.
                #    Ikinci bir yerde hesaplansaydi iki rakam kacinilmaz olarak
                #    ayrisirdi (bkz. bekleyen-isler madde 8.3).
                # Hata halinde ozet YINE GIDER (kiyas eksik gider) — bu satir
                # gunluk ozeti bloke etmemeli.
                kiyas_s = ""
                try:
                    import panel as _panel
                    _o = _panel.ozet("ana", "Ana Sicil (11 coin)", "kripto-defter.json")
                    _k, _b = _o.get("kiyas"), _o.get("bakiye")
                    if _k and _b:
                        _sis = (_b / 1000 - 1) * 100
                        kiyas_s = (f"\nkiyas (ayni pencere): sistem %{_sis:+.1f} "
                                   f"(dusus %{_o.get('dusus') or 0:.1f}) | "
                                   f"BTC %{_k['btc_pct']:+.1f} "
                                   f"(dusus %{_k.get('btc_dusus_pct') or 0:.1f})")
                        if _k.get("sepet_pct") is not None:
                            kiyas_s += f" | {_k.get('sepet_n', 0)} coin %{_k['sepet_pct']:+.1f}"
                except Exception as e:
                    olcucu.log_line(f"[OZET] kiyas alinamadi: {type(e).__name__}: {e}")
                ok = bildirim.gonder(f"[GUNLUK OZET {gun}]\n"
                                     f"acik {o['acik']} | kapali {o['kapali']} | isabet {isb}\n"
                                     f"gross {o['toplam_R']:+.2f}R | net {o['toplam_net_R']:+.2f}R\n"
                                     f"acik risk: LONG %{rl:.1f} / SHORT %{rs:.1f} (tavan %{defter.RISK_TAVANI_PCT:g})"
                                     + kiyas_s + radar_s)
                if ok:
                    son_gun = gun
                    olcucu.atomik_yaz(OZET_DURUM_FILE, {"son_ozet_gun": gun})
        except Exception as e:
            olcucu.log_line(f"[OZET] hata: {type(e).__name__}: {e}")
        # ---- PANEL TAZELEME (madde 2.5, 2026-08-30) --------------------------
        # Panel bugune kadar ELLE calisiyordu; bakilmadigi surece bayat kaliyordu.
        # Emsal: radar.py her turda radar_defter.rapor_yaz() cagiriyor.
        #
        # 🔴 SIKLIK OLCULDU, TAHMIN EDILMEDI (2026-08-30):
        #     offline=True :  1,2 sn ·  0 ag cagrisi
        #     offline=False: 41,5 sn · 47 ag cagrisi
        #   Her turda ONLINE kosmak gunde ~13.500 ek cagri ve tur basina 41 sn
        #   bloklama demekti -> reddedildi.
        # KARAR: her tur OFFLINE (defter rakamlari her zaman taze), kiyas icin
        #   gunde BIR KEZ online. Kiyas al-tut yuzdesidir; gun icinde birkac
        #   puan oynar, panelin ustundeki hukmu degistirmez.
        # ⚠ Onbellegi ozet blogunun YAN ETKISINE birakmadim: ozet
        #   bildirim.aktif() false ise hic kosmaz ve kiyas sonsuza kadar bayatlardi.
        #   Burada KENDI gun damgasi var (panel_gun), ozetten BAGIMSIZ.
        # ⚠ panel.py sicillere YAZMAZ (salt okur) — bu cagri veri bozamaz.
        # ⚠ `gun` yukaridaki try icinde atanir; o try patlarsa TANIMSIZ kalirdi.
        #   Bu blok ondan BAGIMSIZ olmali -> gunu burada yeniden hesapla.
        # ⚠ panel modul basinda DEGIL burada import edilir (ozet blogundaki
        #   `import radar as _radar` deseniyle ayni): calisan surece acilista
        #   ek yuk/surpriz bindirmez.
        try:
            import panel as _panel
            _gun = datetime.now(timezone.utc).date().isoformat()
            _online = (panel_gun != _gun)
            _panel.yaz(offline=not _online)
            if _online:
                panel_gun = _gun
                olcucu.log_line("[PANEL] online tazelendi (kiyas onbellegi guncel)")
        except Exception as e:
            olcucu.log_line(f"[PANEL] hata: {type(e).__name__}: {e}")
        # Gunluk Google Drive yedegi (Telegram'dan BAGIMSIZ; idempotent: gunun
        # klasoru varsa is yapmaz -> gunde 1 gercek yedek. Drive kapaliysa sessiz atlar).
        try:
            yapildi, mesaj = yedek.gunluk_yedek()
            if yapildi:
                olcucu.log_line(f"[YEDEK] {mesaj}")
        except Exception as e:
            olcucu.log_line(f"[YEDEK] hata: {type(e).__name__}: {e}")
        await asyncio.sleep(300)


# ============================== main ==============================
async def amain():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    runtime = None
    if "--seconds" in sys.argv:
        try:
            runtime = int(sys.argv[sys.argv.index("--seconds") + 1])
        except (IndexError, ValueError):
            runtime = 60

    olcucu.log_line(f"[BASLA] gercek zamanli izleyici — {', '.join(olcucu.SYMBOLS)} "
                    f"| snapshot {SNAPSHOT_SEC}s" + (f" | sure {runtime}s" if runtime else ""))

    # PC kapali kaldigi araligi tamamla (bosluk kurtarma) - acilista bir kez
    try:
        ozet = await asyncio.get_event_loop().run_in_executor(None, bosluk.tamamla)
        olcucu.log_line(f"[BOSLUK] {ozet}")
    except Exception as e:
        olcucu.log_line(f"[BOSLUK] hata: {type(e).__name__}: {e}")

    if bildirim.aktif():
        bildirim.gonder("[SISTEM] izleyici basladi (" + ", ".join(olcucu.SYMBOLS) + ")")

    tasks = [asyncio.create_task(ws_consumer()),
             asyncio.create_task(snapshot_loop()),
             asyncio.create_task(recalib_loop()),
             asyncio.create_task(makro_loop()),
             asyncio.create_task(ozet_loop()),
             asyncio.create_task(likidasyon_loop())]
    if runtime:
        await asyncio.sleep(runtime)
        for t in tasks:
            t.cancel()
        olcucu.log_line(f"[DUR] {runtime}s doldu, kapaniyor.")
    else:
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    try:
        asyncio.run(amain())
    except KeyboardInterrupt:
        print("durduruldu")
