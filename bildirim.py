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


# ==============================================================================
#  MESAJ SUZGECI (2026-08-23, kullanici karari "A")
# ==============================================================================
# KARAR: coin bazli ANLIK sinyaller telefona itilmeyi birakir; risk/olcum
# bilgisi kalir. Tahminler URETILMEYE DEVAM EDER (defter'e yazilir, panelde
# gorunur) — yalnizca "itilen tavsiye" olmaktan cikar.
#
# GEREKCE: itilen mesaj bir DAVETTIR ("su fiyattan al, stop suraya"). Elimizde
# o tavsiyenin al-tutmayi gectigine dair olcum YOK; gecemedigine dair iki aylik
# olcum VAR. Kullanicinin kendi ifadesi: "kumar araci kurmak istemiyorum."
#
# NEDEN BURADA, cagri yerlerinde DEGIL: sinyal mesajlarinin 4'u `defter.py`'de,
# 1'i `radar.py`'de. `defter.py` kosan on kayit yuzunden DONDURULMUS. Suzgeci
# tasima katmanina koymak, dondurulmus dosyalara hic dokunmadan ayni sonucu
# verir — ve tek yerden yonetilir.
#
# ⚠ SUSTURULAN MESAJ `True` DONER. Bu bir detay degil, ZORUNLULUK:
#   izleyici.py:302 -> `ok = bildirim.gonder(gunluk_ozet); if ok: <gun damgasi yaz>`
#   False donseydi sistem "ozeti gonderemedim" sanip GUN BOYU TEKRAR ederdi.
#   True'nun anlami "bildirim yapilandirildigi gibi ISLENDI", "iletildi" degil.
#
# ⚠ BILINMEYEN ONEK GECER (fail-open). Yeni bir uyari turu sessizce kaybolmasin;
#   fazladan gurultu, kacirilan alarmdan iyidir.
SUZGEC_FILE = Path(__file__).parent / "bildirim-suzgec.json"

_ONEKLER = {
    "[SINYAL]": "SINYAL",
    "[TETIKLENDI]": "TETIK",
    "[SONUC]": "SONUC",
    "[GECERSIZ]": "GECERSIZ",
    "[RADAR-KURULUM]": "RADAR_KURULUM",
    "[RADAR-HAREKET": "RADAR_HAREKET",     # eskalasyon varyantini da yakalar
    "[MAKRO]": "MAKRO",
    "[GUNLUK OZET": "GUNLUK_OZET",         # basliginda tarih var
    "[SISTEM]": "SISTEM",
    "[ONEMLI DUYURU]": "DUYURU",
}


def tur(text):
    """Mesaj turu (onekten). Taninmayan -> None (gecer)."""
    t = (text or "").lstrip()
    for onek, ad in _ONEKLER.items():
        if t.startswith(onek):
            return ad
    return None


def _suzgec():
    try:
        s = json.loads(SUZGEC_FILE.read_text(encoding="utf-8"))
        return s if s.get("aktif") else None
    except Exception:
        return None


def gecer_mi(text):
    """Bu mesaj Telegram'a gitmeli mi? Suzgec yoksa/kapaliysa HER SEY gecer
    (mevcut davranis birebir korunur)."""
    s = _suzgec()
    if not s:
        return True, None
    t = tur(text)
    if t is None:
        return True, None                  # fail-open
    return bool(s.get("gonderilecek", {}).get(t, True)), t


def gonder(text):
    """Metni gonder. Basari True/False; hata hicbir zaman yukselmez.

    Suzgec tarafindan susturulan mesaj: log'a yazilir, Telegram'a GITMEZ,
    ve `True` doner (bkz. yukaridaki uyari)."""
    global _son_hata_log
    gecer, t = gecer_mi(text)
    if not gecer:
        olcucu.log_line(f"[BILDIRIM] susturuldu ({t}): {text.splitlines()[0][:60]}")
        return True
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
