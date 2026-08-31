# FİZİBİLİTE — zincir-üstü ve makro bölgeleri girilebilir mi?

**Tarih:** 2026-09-01 · **Tür:** fizibilite envanteri, **hipotez testi DEĞİL**
**Neden:** 16 aday öldü; kuyrukta tek aday kaldı (emir defteri, ~30 gün uzakta).
Bölge boş çıkarsa sıfırdan başlamamak için, **hiç girilmemiş** iki bölge
girmeden önce ölçüldü.

⚠ Getiriyle **hiçbir ilişki hesaplanmadı**. Yalnız: veri var mı, ne kadar
geriye, ve **değişkenin kendi kalıcılığı** ölçülebilir bir örneklem bırakıyor mu.

---

## Yöntem — `top_ls` dersi genelleştirildi

`top_ls`te öğrenildi (`9871f58`): bağımsız gözlem sayısını **getiri değil
ÖNGÖRÜCÜ** belirler. Seviyesi çok yavaş bir değişken (τ ≫ 1 gün) hiçbir ufukta
sınanamaz; **değişimine** bakılır. Aynı süzgeç buraya da uygulandı.

---

## 1. ZİNCİR ÜSTÜ — ✅ **AÇIK ve YETERLİ GÜÇ**

| kaynak / metrik | n | kapsam | ρ₁(seviye) | τ(seviye) | **etkin n (değişim)** |
|---|---|---|---|---|---|
| blockchain.com aktif adres | 1.814 | 5,0 yıl | +0,827 | 10,6g | **1.814** |
| blockchain.com işlem sayısı | 1.815 | 5,0 yıl | +0,866 | 14,0g | **1.815** |
| blockchain.com tahmini hacim | 1.817 | 5,0 yıl | +0,646 | 4,6g | **1.817** |
| blockchain.com madenci geliri | 1.818 | 5,0 yıl | +0,924 | 25,2g | **1.818** |
| blockchain.com hash oranı | 1.815 | 5,0 yıl | +0,970 | 66,5g | **1.815** |
| CoinMetrics aktif adres | 2.068 | 5,7 yıl | +0,828 | 10,6g | **2.068** |
| **CoinMetrics borsaya GİRİŞ** | 2.068 | 5,7 yıl | +0,507 | 3,1g | **2.068** |
| **CoinMetrics borsadan ÇIKIŞ** | 2.068 | 5,7 yıl | +0,499 | 3,0g | **2.068** |
| CoinMetrics dolaşımdaki arz | 2.068 | 5,7 yıl | +1,000 | **∞** | **78** ❌ |

🔴 **Teşhis işini gördü:** *dolaşımdaki arz* neredeyse deterministik
(ρ₁ = 1,000; değişimin ρ₁'i bile +0,927) → etkin n **78**. Bu değişken
**kullanılamaz** ve süzgeç onu koşumdan önce ayıkladı.

**Derin geçmiş doğrulandı:** CoinMetrics `AdrActCnt` **2011-01-01'den itibaren
5.721 günlük nokta** (15,7 yıl), anahtarsız ve ücretsiz. blockchain.com 12 yıl.

### Güç (günlük ufuk, tek seri öngörücü, sd(1g getiri)=%4,35)

| n | kapsam | saptanabilir bant farkı | ekonomik eşik %0,5 |
|---|---|---|---|
| 1.800 | 5 yıl | %0,635 | ❌ yetersiz |
| 2.068 | 5,7 yıl | %0,593 | ❌ sınırda |
| **3.650** | **10 yıl** | **%0,446** | ✅ **yeter** |
| 5.721 | 15,7 yıl | %0,356 | ✅ yeter |

**Sonuç: bölge AÇIK — ama en az ~10 yıllık pencere gerekir.**

### 🔴 Tasarım uyarısı (ön kayıtta çözülmeli)

15,7 yıllık BTC penceresi **taban tabana farklı rejimler** içeriyor (2011'de
BTC 1 $). Ham havuzlama, `kesitsel_test` dersindeki hatanın aynısıdır. Ön kayıt
ya rejim ayrımı yapmalı ya da pencereyi (ör. 2017 sonrası) **sonuca bakmadan**
sabitlemelidir.

### 📌 En umut verici aday: **borsa giriş/çıkış akışları**

Bunlar **gerçekten bant dışıdır**: zincir üzerinde gerçekleşen coin
hareketleri, Binance perp'te gerçekleşmiş işlem değil. Ayrıca kalıcılıkları
düşük (τ ≈ 3 gün), yani değişimleri bol bağımsız gözlem bırakıyor.

---

## 2. MAKRO — 🟡 **KISMEN AÇIK, GÜÇ SINIRDA (kaynak kısıtı)**

| Yahoo serisi | n | kapsam | ρ₁(seviye) | τ(seviye) | etkin n (değişim) |
|---|---|---|---|---|---|
| DXY dolar endeksi | 1.257 | 5,0 yıl | +0,994 | **311,6g** | 1.247 |
| ABD 10 yıllık faiz | 1.255 | 5,0 yıl | +0,998 | **819,7g** | 1.255 |
| VIX | 1.256 | 5,0 yıl | +0,943 | 34,2g | 1.256 |
| altın | 1.257 | 5,0 yıl | +0,999 | **2.160,8g** | 1.257 |
| S&P 500 | 1.254 | 5,0 yıl | +0,999 | **1.808,4g** | 1.254 |

🔴 **Makro SEVİYELERİ kesinlikle kullanılamaz** — τ 311-2.161 gün. Bu, `top_ls`
seviyesinin (τ≈416g) aynısı ve daha beteri. **Yalnız değişimler.**

### Kaynak kısıtı — ölçüldü

| kaynak | sonuç |
|---|---|
| Yahoo `range=5y` günlük | ✅ 1.255 nokta |
| Yahoo `range=max` | ❌ **aylığa düşüyor** (168 nokta / 41,7 yıl) |
| **FRED** açık CSV ucu | ❌ **ConnectionError** — bu makineden erişilemiyor |
| **Stooq** | ❌ bot koruması (JS challenge döndürüyor) |

**Sonuç: makro günlük derinliği ~5 yılla sınırlı → saptanabilir %0,635,
ekonomik eşik %0,5'in ÜSTÜNDE.** Bölge kapalı değil ama **yeterince güçlü
değil**; bugün sınanırsa hüküm *"ölçülemedi"* olur.

🔓 **Açılma şartı:** günlük ve ≥10 yıllık bir makro kaynağı erişilebilir hale
gelirse (FRED API anahtarı, farklı ağ, ya da başka sağlayıcı) bölge güçlenir.
O zamana kadar **makro sınamaya alınmaz** ve gerekçesi budur.

---

## 🔴 SONUÇ

| bölge | durum | gerekçe |
|---|---|---|
| **Zincir üstü** | ✅ **AÇIK** | 15,7 yıl günlük, ücretsiz; değişimlerde etkin n ≈ 2.000-5.700; 10 yılda güç yeter |
| **Makro** | 🟡 **BEKLEMEDE** | Bölge uygun ama günlük derinlik ~5 yıl → güç yetmiyor. Kaynak sorunudur, fikir sorunu değil |
| Uzun ufuk (>7 gün) | ❌ KAPALI | `FIZIBILITE-UZUN-UFUK-2026-09-01.md` |

**Kuyruğa giren aday:** zincir-üstü **borsa giriş/çıkış akışları** — bant dışı,
derin geçmişli, düşük kalıcılıklı. Emir defteri beklerken sınanabilir.

⚠ **Bu belge bir hüküm değildir.** *"Zincir üstünde bilgi var"* demiyor;
*"zincir üstünde bilgi olup olmadığı SORULABİLİR"* diyor. 16 ölü adaydan sonra
önsel olasılık düşüktür ve bu, ön kaydın beklenti bölümüne yazılacaktır.
