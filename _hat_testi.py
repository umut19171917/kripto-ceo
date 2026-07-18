"""
_hat_testi.py — "Canli hat" (WebSocket) senin agında calisiyor mu?
Binance'e baglanip 15 saniye dinler; veri gelirse CALISIYOR, gelmezse OLU der.
Cift tikla: hat-testi.bat
"""
import asyncio
import time

try:
    import websockets
except ImportError:
    print("HATA: websockets kurulu degil. Once: venv\\Scripts\\python -m pip install websockets")
    raise SystemExit


async def main():
    url = "wss://fstream.binance.com/stream?streams=btcusdt@aggTrade"
    n = 0
    t0 = time.time()
    print("Binance canli hattina baglaniyor... (15 saniye dinlenecek)")
    try:
        async with websockets.connect(url, ping_interval=None, open_timeout=15) as ws:
            print("Baglandi. Veri bekleniyor...\n")
            while time.time() - t0 < 15:
                try:
                    await asyncio.wait_for(ws.recv(), timeout=15 - (time.time() - t0))
                    n += 1
                except asyncio.TimeoutError:
                    break
    except Exception as e:
        print("BAGLANTI HATASI:", type(e).__name__, str(e)[:150])

    print("\n" + "=" * 52)
    if n > 0:
        print(f"   SONUC: CANLI HAT CALISIYOR  ({n} mesaj geldi)")
    else:
        print("   SONUC: CANLI HAT OLU  (0 mesaj - hic veri gelmedi)")
    print("=" * 52)


if __name__ == "__main__":
    try:
        import sys
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    asyncio.run(main())
