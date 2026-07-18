"""
bildirim.py — Telegram bildirim kanali (C1, 2026-07-04)
================================================================================
Canli olaylari (yeni tahmin / tetik / sonuc / makro kapi degisimi / gunluk ozet)
Telegram'a gonderir. TASARIM ILKESI: bildirim SUSTUR, cekirdek degil —
config yoksa/agla sorun varsa SESSIZ no-op; canli donguyu ASLA kirmaz.

Kurulum (bir kez, kullanici):
  1) Telegram'da @BotFather -> /newbot -> isim ver -> TOKEN'i kopyala
  2) telegram.json dosyasina yapistir: {"token": "123456:ABC...", "chat_id": null}
  3) Telegram'da kendi botunu bul, ona herhangi bir mesaj at ("merhaba")
     -> chat_id ILK gonderimde OTOMATIK kesfedilir ve dosyaya yazilir.
Test: venv\\Scripts\\python.exe bildirim.py

telegram.json GITIGNORE'ludur (token kisisel). Bot SALT-GONDERIM icin kullanilir;
para/borsa yetkisi yoktur.
"""

import sys
import json
import time
from pathlib import Path

import requests

import olcucu  # log_line + atomik_yaz

CONF_FILE = Path(__file__).parent / "telegram.json"
API = "https://api.telegram.org/bot{token}/{metot}"
_son_hata_log = 0.0   # hata logunu saatte 1 sinirla (30sn dongude spam olmasin)


def _conf():
    try:
        c = json.loads(CONF_FILE.read_text(encoding="utf-8"))
        return c if c.get("token") else None
    except Exception:
        return None


def aktif():
    """Token girilmis mi? (chat_id sart degil; ilk gonderimde kesfedilir)"""
    return _conf() is not None


def _chat_id(c):
    """chat_id yoksa getUpdates'ten kesfet (kullanici bota mesaj atmis olmali) + kaydet.
    Token gecersizse (401) burada patlamadan once yakalanir -> yaniltici 'chat_id
    yok' mesaji yerine gercek sebep raporlanir (2026-07-06 hata ayiklama dersi)."""
    if c.get("chat_id"):
        return c["chat_id"]
    resp = requests.get(API.format(token=c["token"], metot="getUpdates"), timeout=10)
    r = resp.json()
    if not r.get("ok"):
        raise RuntimeError(f"Telegram API hatasi: {r.get('description', resp.status_code)}")
    for u in reversed(r.get("result", [])):
        msg = u.get("message") or u.get("channel_post")
        if msg and "chat" in msg:
            c["chat_id"] = msg["chat"]["id"]
            olcucu.atomik_yaz(CONF_FILE, c)
            olcucu.log_line(f"[BILDIRIM] chat_id kesfedildi: {c['chat_id']}")
            return c["chat_id"]
    return None


def gonder(text):
    """Metni gonder. Basari True/False; hata hicbir zaman yukselmez."""
    global _son_hata_log
    c = _conf()
    if not c:
        return False
    try:
        cid = _chat_id(c)
        if not cid:
            raise RuntimeError("chat_id yok - Telegram'da bota bir mesaj atin")
        r = requests.post(API.format(token=c["token"], metot="sendMessage"),
                          json={"chat_id": cid, "text": text}, timeout=10)
        r.raise_for_status()
        return True
    except Exception as e:
        if time.time() - _son_hata_log > 3600:
            _son_hata_log = time.time()
            olcucu.log_line(f"[BILDIRIM] gonderilemedi: {type(e).__name__}: {str(e)[:70]}")
        return False


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    if not aktif():
        print("telegram.json'da token YOK. Kurulum (dosya basindaki docstring):")
        print("  1) @BotFather -> /newbot -> TOKEN")
        print('  2) telegram.json: {"token": "TOKEN-BURAYA", "chat_id": null}')
        print("  3) bota bir mesaj at, sonra bu testi tekrar calistir")
        sys.exit(1)
    ok = gonder("Test: kripto sistem bildirim kanali CALISIYOR.")
    print("gonderildi - telefonunu kontrol et" if ok else
          "GONDERILEMEDI - olcucu.log'daki [BILDIRIM] satirina bak")
    sys.exit(0 if ok else 1)
