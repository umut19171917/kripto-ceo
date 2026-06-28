# Kripto CEO — Yerel Analiz Sistemi

Binance futures verisini **yerel olarak** çekip net matematiksel formüllerle analiz eden, sıkışma (long/short squeeze) odaklı bir karar-destek sistemi. Veri çekme + tüm hesaplama bilgisayarda çalışır (API anahtarı gerekmez); analiz/rapor katmanı bir Claude Code skill'idir (`kripto-SKILL.md`).

> ⚠️ **Sorumluluk reddi:** Bu yazılım eğitim/araştırma amaçlıdır, **yatırım tavsiyesi değildir.** Gerçek parayla kullanım tüm riski size aittir. Hiçbir bileşen otomatik emir vermez; karar ve emir her zaman kullanıcıdadır.

## Mimari (iki kanal + beyin)
- **Kanal 1 — Sinyal:** teknik + türev veri (ATR, RSI, VWAP, CVD, OI, funding) → sıkışma skoru → ATR-tabanlı işlem planı (giriş / stop / TP1 / TP2 / R-R / pozisyon boyutu).
- **Kanal 2 — Güvenlik kapısı:** makro + jeopolitik (DXY rejim + otomatik ekonomik takvim + eşzamanlı risk-off şok tespiti) → girilir mi / boyut ne (skora karışmaz, filtreler).
- **Defter:** her geçerli tahmini kaydeder, sonucunu (TP/stop) gerçek mumlarla takip eder, R-multiple ile puanlar.
- **Ek:** per-symbol self-kalibrasyon, boşluk-kurtarma (offline aralığı tamamlar), otomatik takvim.

## Kurulum
```bash
python -m venv venv
venv\Scripts\python -m pip install -r requirements.txt
```

## Çalıştırma
```bash
venv\Scripts\python izleyici.py     # canlı izleyici (arka plan motoru)
venv\Scripts\python durum.py        # anlık durum raporu
venv\Scripts\python kalibrasyon.py  # eşikleri tarihsel veriyle kalibre et
```
Windows'ta `.bat` dosyalarına çift tıklayarak da çalışır. Ayrıntılı kullanım: [`OKU-BENI.md`](OKU-BENI.md).

## Dosyalar
| Dosya | İş |
|---|---|
| `olcucu.py` | Veri + matematik + sıkışma skoru + işlem planı üreteci |
| `izleyici.py` | Gerçek zamanlı izleyici (WebSocket likidasyon + snapshot + tüm döngüler) |
| `kalibrasyon.py` | Per-symbol eşik kalibrasyonu (funding/OI dağılımından) |
| `makro.py` | Kanal 2: makro/jeopolitik güvenlik kapısı |
| `defter.py` | Tahmin kaydı + sonuç takibi (kendi kendini ölçme) |
| `bosluk.py` | Boşluk kurtarma (PC kapalı kaldığı aralığı tamamlar) |
| `durum.py` | İnsan-okur durum raporu |
| `kripto-SKILL.md` | Claude Code skill — CEO beyni (analiz + karar) |

Veri kaynakları (hepsi anahtarsız): Binance USDT-M Futures public API, Yahoo Finance (DXY), ForexFactory (ekonomik takvim).

İzlenen örnek semboller: BTC, ETH, SOL, LINK (`olcucu.py` → `SYMBOLS`).
