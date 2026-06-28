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

import websockets

import olcucu       # REST cekiciler + matematik + log_line + OUT_FILE + SYMBOLS
import kalibrasyon  # self-kalibrasyon (esikler.json'u tazeler)
import makro        # Kanal 2: makro/jeopolitik guvenlik kapisi (makro.json)
import defter       # tahmin kaydi + sonuc takibi (kripto-defter.json)
import bosluk       # bosluk kurtarma (PC kapali kaldigi araligi tamamlar)

# ============================== CONFIG ==============================
WS_BASE = "wss://fstream.binance.com/stream"
SNAPSHOT_SEC = 30           # REST snapshot araligi
LIQ_KEEP_SEC = 3600         # likidasyon olaylarini 1 saat tut
CASCADE_WINDOW_SEC = 300    # "kademe" penceresi: son 5 dk
CASCADE_USD = 1_000_000     # son 5dk tek tarafta > bu => KADEME aktif (canli veride kalibre)
RECAL_SEC = 12 * 3600       # esikleri her 12 saatte bir yeniden kalibre et (self-kalibrasyon)
MAKRO_SEC = 120             # Kanal 2 (makro/jeopolitik) kapiyi 2 dakikada bir tazele

# her sembol icin likidasyon olaylari: deque[(ts, side, usd, price)]
liq_events = {s: deque() for s in olcucu.SYMBOLS}


# ============================== Likidasyon toplama ==============================
def add_liq(sym, side, usd, price):
    liq_events[sym].append((time.time(), side, usd, price))


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
    cascade = None
    if long5 >= CASCADE_USD and long5 >= short5:
        cascade = "long"    # longlar likide oluyor -> ASAGI kademe
    elif short5 >= CASCADE_USD:
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
    streams = "/".join(f"{s.lower()}@forceOrder" for s in olcucu.SYMBOLS)
    url = f"{WS_BASE}?streams={streams}"
    while True:
        try:
            async with websockets.connect(url, ping_interval=None) as ws:
                olcucu.log_line(f"[WS] baglandi -> {streams}")
                async for raw in ws:
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
               "source": "binance-futures-rest+ws", "symbols": {}}
        for sym in olcucu.SYMBOLS:
            try:
                # REST + matematik bloklayici -> ayri thread'de calistir
                d = await loop.run_in_executor(None, olcucu.analyze_symbol, sym)
                d["live_liq"] = liq_summary(sym, now)
                cas = d["live_liq"]["cascade"]
                sq = d["squeeze"]
                if cas == "short" and sq["short_squeeze"] >= 50:
                    sq["note"] = (f"SHORT SQUEEZE TETIKLENDI (canli: short likidasyon "
                                  f"${d['live_liq']['short_liq_5m_usd']:,}/5dk) -> yukari")
                elif cas == "long" and sq["long_squeeze"] >= 50:
                    sq["note"] = (f"LONG SQUEEZE TETIKLENDI (canli: long likidasyon "
                                  f"${d['live_liq']['long_liq_5m_usd']:,}/5dk) -> asagi")
                out["symbols"][sym] = d
            except Exception as e:
                out["symbols"][sym] = {"error": f"{type(e).__name__}: {e}"}

        olcucu.OUT_FILE.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

        try:
            defter.guncelle(out)
        except Exception as e:
            olcucu.log_line(f"[DEFTER] hata: {type(e).__name__}: {e}")

        stamp = out["updated_at"]
        for sym, d in out["symbols"].items():
            if "error" in d:
                olcucu.log_line(f"[{stamp}] {sym}: HATA {d['error']}")
                continue
            ll, sq = d["live_liq"], d["squeeze"]
            kademe = f" | KADEME: {ll['cascade'].upper()}" if ll["cascade"] else ""
            olcucu.log_line(f"[{stamp}] {sym} ${d['price']} | SS {sq['short_squeeze']} LS {sq['long_squeeze']} "
                            f"| 5dk likid L${ll['long_liq_5m_usd']:,} S${ll['short_liq_5m_usd']:,}{kademe}")
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
    """Kanal 2: makro.json'u periyodik tazeler (DXY rejim + takvim + sok ayak izi)."""
    loop = asyncio.get_event_loop()
    while True:
        try:
            m = await loop.run_in_executor(None, makro.write_makro)
            if m["kapi"] != "ACIK":
                olcucu.log_line(f"[MAKRO] KAPI {m['kapi']} (boyut {m['boyut_carpani']}): " + " ; ".join(m["notlar"]))
        except Exception as e:
            olcucu.log_line(f"[MAKRO] hata: {type(e).__name__}: {e}")
        await asyncio.sleep(MAKRO_SEC)


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

    tasks = [asyncio.create_task(ws_consumer()),
             asyncio.create_task(snapshot_loop()),
             asyncio.create_task(recalib_loop()),
             asyncio.create_task(makro_loop())]
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
