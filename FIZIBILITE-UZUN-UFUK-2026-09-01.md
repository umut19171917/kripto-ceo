# FİZİBİLİTE — uzun ufuklar ölçülebilir mi?

**Tarih:** 2026-09-01 · **Tür:** fizibilite envanteri, **hipotez testi DEĞİL**
**Neden:** *"7 günden uzun ufuk · zincir-üstü veri · makro"* bölgesi listede
*"hiç girilmedi"* diye duruyordu. Girmeden önce **girilebilir mi** diye bakıldı.

⚠ Bu belge bir ölçüm hükmü değildir. Getiriyle **hiçbir ilişki hesaplanmadı**;
yalnız marjinaller (örtüşmesiz pencere sayısı, getiri sd'si) ölçüldü.

---

## Ölçüm

10 sembol · **1.461 gün (4,0 yıl)** · günlük kapanış · örtüşmesiz pencereler ·
muhafazakâr **2,5 etkin bağımsız sembol** (kripto birlikte hareket eder).

| ufuk | örtüşmesiz pencere | etkin birim | sd(getiri) | **saptanabilir en küçük bant farkı** |
|---|---|---|---|---|
| **1 gün** | 1.461 | 3.652 | %4,35 | **%0,45** |
| **7 gün** | 208 | 520 | %11,60 | **%3,15** |
| 30 gün | 48 | 120 | %32,96 | **%18,65** |
| 90 gün | 16 | 40 | %130,29 | **%127,68** |
| 180 gün | 8 | 20 | %95,20 | **%131,95** |

Gidiş-dönüş maliyet **%0,13** — ufka göre değişmez.

---

## 🔴 SONUÇ: 7 günden uzun ufuklar ÖLÇÜLEMEZ

30 günlük ufukta görebileceğimiz en küçük fark **%18,65**. Böyle bir etki
piyasada olsaydı zaten herkes görürdü. Yani bu ufukta *"bulamadık"* demek
**hiçbir şey ifade etmez** — testin kendisi kör.

**Bu bir fikir eksikliği değil, ARİTMETİK:** 4 yıl, 30 günlük ufukta yalnız
**48 örtüşmesiz pencere** demektir.

### Kurtarma denemeleri de çalışmıyor

| deneme | sonuç |
|---|---|
| **Daha çok sembol** | Kripto birlikte hareket ediyor; etkin bağımsız sembol ~2,5. 100 sembolle etkin 5 olsa bile 30g'de saptanabilirlik ancak %13,2'ye iner |
| **Daha uzun geçmiş** | Binance perp'in kendisi ~2019'da başladı; altcoinlerin çoğu çok daha yeni. 8 yıl olsa saptanabilirlik √2 kat iyileşir → 30g'de ~%13. Hâlâ kör |
| **Örtüşen pencere** | Bağımsız birim sayısını **artırmaz**, yalnız gizler. Gün-kümeli bootstrap zaten bunu düzeltiyor |

---

## 📌 PROJENİN ÖLÇÜLEBİLİR PENCERESİ

| ufuk | durum |
|---|---|
| **1 saat – 1 gün** | ✅ Ölçülebilir (%0,45 ve altı saptanabilir) |
| **1 – 7 gün** | ⚠ Sınırda (%3,15 — ancak çok güçlü bir etki görülür) |
| **7 günden uzun** | ❌ **Ölçülemez.** Bu projenin yöntem standardıyla kapalı |

🔴 **Kalıcı sonuç:** *"uzun vadeli bir sinyal arayalım"* önerisi bundan sonra
**fizibilite gerekçesiyle reddedilir**, fikir beğenilmediği için değil.
Reddin dayanağı bu tablodur.

⚠ **Bunun söylemediği şey:** uzun ufukta etki **yoktur** demiyor. *"Varsa da
biz göremeyiz"* diyor. Fark, bu projenin en çok önem verdiği ayrım:
**ölçülemedi ≠ yok.**

---

## Bunun diğer sorulara etkisi

1. **Kesitsel momentum (7 gün) hükmü sağlamlaşıyor.** O test 7 günlük ufuktaydı
   ve yoğunlaşma + hayatta kalma yanlılığından düştü. Bu tablo gösteriyor ki
   o ufukta **zaten ancak %3,15'lik bir etki görülebilirdi** — hüküm
   *"etki yok"* değil, *"varsa bile bu veriyle gösterilemez"* olarak okunmalı.

2. **Emir defteri derinliği için ufuk seçimi doğrulanıyor.** O aday için
   **1 saatlik** ufuk seçilmişti (`derinlik_arsiv.py` başlığı). Bu tablo aynı
   yöne bakıyor: ölçülebilir bölge kısa uçta.

3. **Maliyet sorusu açık kalıyor.** Kısa ufukta maliyet (%0,13) getiri sd'sine
   (%4,35/gün) göre küçük görünüyor, ama işlem **sıklığı** yüksek olduğu için
   toplamda baskın olabiliyor — mutabakat ölçümünde görüldü: 352 pozisyonda
   brüt −91 $, komisyon −327 $. **Bu ayrı bir ön kayıt hak ediyor** ve
   fizibilitesi bu tabloya göre AÇIK (kısa ufuk ölçülebilir).
