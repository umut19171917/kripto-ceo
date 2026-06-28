# Kripto Sistemi — Kullanım Kılavuzu

Bu klasör, Binance'den **canlı veri çekip matematiksel analiz yapan** yerel sistemdir.
Veri çekme + tüm hesaplama bilgisayarında çalışır (token harcamaz). Karar/rapor kısmı Claude'a (CEO) aittir.

## Dosyalar ne işe yarar?

| Dosya | Açıklama |
|---|---|
| `olcucu.py` | Motor: REST veri + matematik (ATR, RSI, VWAP, CVD, OI, funding, sıkışma skoru) |
| `izleyici.py` | Gerçek zamanlı katman: canlı likidasyonları (WebSocket) yakalar + snapshot alır |
| `signals.json` | **Çıktı** — son taramanın özeti. Claude bunu okur |
| `kripto-defter.json` | Hafıza: pozisyonlar / tahminler / dersler |
| `olcucu.log` | Tüm taramaların geçmiş kaydı (VS Code'da açıp incele) |
| `kalibrasyon.py` / `esikler.json` | Per-symbol eşik kalibrasyonu (otomatik, 12s'te bir) |
| `makro.py` / `makro.json` | **Kanal 2:** makro/jeopolitik güvenlik kapısı (DXY rejim + ekonomik takvim + şok tespiti) |
| `makro-takvim.json` | Ekonomik olaylar (FOMC/CPI/PPI/NFP) — **otomatik güncellenir** |
| `durum.bat` / `durum.py` | **Çift tıkla → anlık özet** (sistem, makro kapı, setup'lar, sicil) |
| `venv/` | İzole Python + kütüphaneler. **Dokunma** |

## Nasıl çalıştırırım? (3 yol)

**1) Çift tıkla (en kolay)**
- `calistir.bat` → bir kez tara
- `canli-izleyici.bat` → sürekli + canlı likidasyon (önerilen)
- `surekli-calistir.bat` → sürekli (sadece REST, likidasyonsuz)

**2) VS Code terminali** (Terminal → New Terminal, Ctrl+`)
```
.\venv\Scripts\python.exe izleyici.py            # sürekli canlı
.\venv\Scripts\python.exe izleyici.py --seconds 60   # 60 sn çalış, dur
.\venv\Scripts\python.exe olcucu.py              # tek tarama
```

**3) Logları izle**
- Canlı: yukarıdaki komutu terminalde çalıştır → akış orada
- Geçmiş: `olcucu.log` dosyasını VS Code'da aç (Ctrl+End = en güncel)

## Sistemi nasıl KULLANIRIM?

```
1. canli-izleyici.bat'a çift tıkla   → signals.json güncel kalır
2. Claude'a "rapor ver" / "ne durumda?" de
3. Claude signals.json + defteri okur → AL/SAT/BEKLE + sıkışma raporu sunar
```

`signals.json`'u kendin okumana gerek yok — o Claude için. Sen motoru çalıştır, Claude'a sor.

## Otomatik arka plan çalışması (KURULDU)
İzleyici artık **her açılışta kendiliğinden, penceresiz** başlar — elle terminal açmana gerek yok.
- Başlatıcı: `Başlangıç` klasöründe `KriptoIzleyici.vbs` (pythonw ile gizli çalıştırır, admin gerekmez).
- **Çalışıyor mu?** Görev Yöneticisi (Ctrl+Shift+Esc) → `pythonw.exe` ara; ya da Claude'a "çalışıyor mu?" de.
- **Durdurmak:** Görev Yöneticisi → `pythonw.exe` → Görevi sonlandır.
- **Otomatik başlamayı kaldır:** `Win+R` → `shell:startup` yaz → `KriptoIzleyici.vbs` dosyasını sil.
- Veri sessizce `olcucu.log` + `signals.json`'a akar; sen Claude'a "durum?" dersin.

## Önemli notlar
- Hiçbir şey otomatik emir VERMEZ. Karar ve emir her zaman sende.
- Eşikler (funding, sıkışma) ilk sürümde tahminîdir; canlı veriyle kalibre edilecek.
- Şu an izlenen coinler: BTC, ETH. Genişletmek için `olcucu.py` içindeki `SYMBOLS` satırı.
