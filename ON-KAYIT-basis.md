# ÖN KAYIT — `basis`: spot-perp farkı BANT DIŞI mı, yoksa funding'in başka adı mı?

**Yazım anı:** 2026-08-31 (koşumdan ÖNCE; hiçbir ilişki hesaplanmadan, yalnız ölçeğe bakıldı)
**Durum:** DONDURULDU. Tanımlar (§2), örneklem (§3), nicelikler (§4), güç (§5),
karar kuralı (§6) bu commit'ten sonra değiştirilmez.
**Öncülleri:** `b01d493` (B1) · `be56b77` (B2) · `317c8d0` (B3) · `8274909` (ters)
**Bağlı madde:** 7.4 / B4 — TEK-BANT SORUNU

---

## 0. Bu ölçüm ne YAPAR, ne YAPMAZ

`ters` (`0130da6`) örneklem-içiydi ve hüküm doğuramıyordu. **Bu farklı:**
pencere 4 yıl; canlı sistemin 65 günlük çalışma penceresi bunun içinde küçük
bir dilim. Yani bu, geriye dönük ama büyük ölçüde **örneklem-dışı** bir ölçümdür.

**Yine de yapamayacağı şey var:**
- ⛔ Kârlılık hükmü kuramaz (mekanik ve portföy aşamaları yapılmadan).
- ⛔ Canlı kuralı değiştiremez.
- ✅ Tek cevapladığı: **bandın dışında ölçülebilir bilgi var mı, ve mekanik
  aşamasına geçmeye değer mi?**

---

## 1. Neden bu ölçüm

15 aday öldü. `squeeze_scores()` hiçbir yönde bilgi taşımıyor (`8274909`).
Madde 7.4'ün açıklaması: **skorun bütün bileşenleri (funding · OI · L/S ·
seviye) aynı bandan** — Binance perp'te gerçekleşmiş işlemden. 14 farklı
hipotez değil, aynı bilginin 14 kılığı olabilir.

Bandın dışındaki adaylar fizibiliteden geçti (2026-08-31, ölçüldü):

| aday | geriye çekilebilir mi | karar |
|---|---|---|
| **spot-perp basis** | ✅ 4 yıl (`/api/v3/klines` 2022-09'a kadar döndü) | **BU ÖLÇÜM** |
| çapraz borsa | ✅ Bybit · OKX · Coinbase yanıt verdi | sonraki aday |
| emir defteri derinliği | ❌ yalnız anlık; `startTime` geçmiş vermiyor | ileriye arşivlenmeli |
| pozisyon kompozisyonu (`top_ls`) | ⚠ 25 gün OK · 40 gün HTTP 400 → 30 günlük sınıf, arşivde YOK | bugünden arşivlenmeli |

Basis seçildi çünkü **hem bedava hem derin** — ve çünkü onu öldürebilecek somut
bir şüphe var (§7).

---

## 2. TANIMLAR (donduruluyor)

| büyüklük | tanım |
|---|---|
| `basis_t` | `(perp_kapanış_t − spot_kapanış_t) / spot_kapanış_t × 100` (%) |
| `funding_t` | `t` anında **yayımlanmış EN SON** funding oranı (`fundingTime ≤ t`) |
| `ileri_t` | `(perp_kapanış_{t+24s} − perp_kapanış_t) / perp_kapanış_t × 100` |
| `artık_t` | `basis_t − (a + b·funding_t)`, **sembol başına ayrı** EKK |

🔴 **İleri bakış yasağı:** `funding_t` yalnız `fundingTime ≤ t` olanlardan seçilir.
Funding 8 saatte bir yayımlanır; aradaki saatlerde **en son yayımlanan** kullanılır.

🔴 **Ölçek düzeltmesi zorunlu:** basis'in sd'si sembole göre 2,7 kat değişiyor
(BTC %0,0101 · SOL %0,0270 — pilot, 2026-08-31). Ham havuzlama bantları
sembole göre ayırır. Bu yüzden bantlar **sembol içinde** beşe bölünür
(eşit sayılı), sonra havuzlanır. B1'in deseniyle aynı.

Çözünürlük 1 saat. Tohum `random.seed(11)` (proje teamülü).

---

## 3. ÖRNEKLEM

- **Semboller:** `olcucu.SYMBOLS`'ün 11'i — BTC, ETH, SOL, LINK, XRP, BNB,
  DOGE, ZEC, ADA, NEAR, LAB. (Canlı sistemin listesi; bu ölçüme bakılarak
  seçilmedi.)
- **Pencere:** son 4 yıl **ya da** sembolün listelenme tarihi — hangisi geç ise.
- ⚠ **Hayatta kalma yanlılığı, kayda geçiyor:** bu 11 sembol bugün yaşıyor.
  Ölen coinler örneklemde yok. Getiri SEVİYELERİ bu yüzden yukarı yanlı;
  **sıralama** sorusu (bantlar arası fark) bundan daha az etkilenir ama muaf değil.
- ⚠ **Örtüşen ileri getiri:** saatlik gözlemlerde 24s pencereler örtüşür.
  Birincil çıkarım **gün-kümeli bootstrap** (takvim günü yeniden örneklenir);
  ek olarak örtüşmesiz günlük sürüm sağlamlık kontrolü olarak raporlanır.

---

## 4. RAPORLANACAK NİCELİKLER (sıra sabit)

1. Kapsama: sembol · eşleşen saat sayısı · pencere başlangıcı.
2. **S1 — ARTIKLIK:** sembol başına ρ(`basis`, `funding`) ve EKK R². Havuz medyanı.
3. `artık`'ın sd'si — ve fiyatın **tick büyüklüğüne** oranı (gürültü tabanı kontrolü).
4. **S2 — ARTIKTA BİLGİ:** `artık` beş bandı × ortalama `ileri` · Spearman ρ ·
   uç bantlar farkı (bant5 − bant1) · **gün-kümeli %95 GA**.
5. **Paralel kol — HAM BASIS:** aynı nicelikler `artık` yerine ham `basis` ile.
6. **Paralel kol — FUNDING:** aynı nicelikler `funding` ile.
   (Bu üçü yan yana: bilgi bantta mı, artıkta mı, hiçbirinde mi?)
7. Sağlamlık: örtüşmesiz günlük sürüm · top-3 sembol çıkarılmış sürüm.

---

## 5. 🔴 GÜÇ HESABI (EK 4 zorunluluğu — donmadan önce yapıldı)

Pilot ölçüm (2026-08-31, 3 sembol × 365 gün, **yalnız marjinaller; ilişki
hesaplanmadı**): `sd(basis) = %0,0158` · `sd(24s ileri getiri) = %3,02`.

Muhafazakâr bağımsız birim sayımı: 4 yıl = **1.460 örtüşmesiz gün**; kripto
sembolleri birlikte hareket ettiği için 11 sembol ≈ **2,5 bağımsız birim**
→ `n_eff ≈ 3.650`, bant başına ~730.

```
SE(uç bant farkı) = 3,02 × sqrt(1/730 + 1/730) = %0,158
%95'te saptanabilir en küçük fark = 1,96 × 0,158 = %0,31
```

**Zorunlu cümle:** *n≈3.650 bağımsız birim ve sd=%3,02 ile ancak **%0,31**
büyüklüğünde bir bant farkını görebiliriz. Aradığımız ekonomik eşik %0,5
(§6) bunun ÜZERİNDE — yani bu test, aradığımız etkiyi bulabilecek güçtedir.
Bundan küçük bir etki varsa göremeyiz; o durumda "yok" değil, "ölçülemedi" denir.*

⚠ **Ek güç şartı:** `artık` sıralamayla bantlandığı için bant sayıları sd'den
bağımsızdır; asıl risk artığın **tick gürültüsünden ibaret** olmasıdır.
Madde 4.3 bunu ölçer: `sd(artık)` fiyatın tick oranının altındaysa hüküm
**ÖLÇÜLEMEDİ**'dir.

---

## 6. 🔴 KARAR KURALI — sonucu görmeden yazılıyor

**Ekonomik eşiğin dayanağı (uydurulmuş değil, ölçülmüş):** gidiş-dönüş taker
maliyeti **%0,13** (`defter`: TAKER 0,05 × BNB 0,90 + SLIPPAGE 0,02, iki bacak).
Uç bantlarda uzun-kısa iki gidiş-dönüş = **%0,26**. Eşik **%0,5** = maliyet +
benzer büyüklükte pay.

| Bulgu | Sonraki adım |
|---|---|
| `artık` bantları monotonik (\|ρ\|≥0,8) **VE** uç fark ≥ **%0,5** **VE** GA sıfırı dışlıyor | ✅ **Bant dışında bilgi VAR.** Mekanik aşaması için AYRI ön kayıt yazılır |
| GA sıfırı dışlıyor ama uç fark **%0,26–0,5** arası | ⚠ İstatistiksel var, **ekonomik yok.** Mekanik YAZILMAZ; kayda geçer |
| GA sıfırı kapsıyor | ❌ Artıkta bilgi yok |
| `sd(artık)` tick gürültüsü seviyesinde | ❌ **ÖLÇÜLEMEDİ** (geçti/kaldı DEĞİL) |

**Üç kol birlikte okunur (madde 4.4 / 4.5 / 4.6):**

| ham basis | artık | okuma |
|---|---|---|
| bilgi var | bilgi var | Bant dışında **gerçekten** yeni bilgi |
| bilgi var | bilgi YOK | Bilgi funding'in **içindeydi** → bant DIŞI değil, bant İÇİ |
| bilgi YOK | bilgi YOK | ❌ Basis dalı ölü |

🔴 **En kritik satır ortadaki.** "Basis çalışıyor" görünüp artığın boş çıkması
**bant dışı bir bulgu değildir** — funding'in zaten taşıdığı şeyi yeniden
keşfetmiş oluruz. Bu satır tam da onu peşinen kayda geçirmek için yazılıyor.

⚠ **%0,5'i geçmek "kârlı" demek DEĞİLDİR.** B1'in ham bant farkı **%2,06**'ydı
ve mekanik uygulanınca **−0,327R** oldu (`be56b77`). Bu eşiği geçmek yalnız
*"mekaniği ölçmeye değer"* anlamına gelir.

---

## 7. BEKLENTİ (dürüstlük kaydı — sonuç görülmeden)

**Bu dalın ÖLECEĞİNİ bekliyorum.** Gerekçe: Binance funding'i zaten premium
index'ten, yani perp ile spot arasındaki farktan üretiliyor. Basis'i ayrıca
hesaplamak, funding'i uzun yoldan yeniden hesaplamak olabilir. Yani
ρ(basis, funding) **yüksek** (≥0,8) ve artık **boş** çıkacak diye bekliyorum.

**Kendime karşı argüman:** funding üç şey kaybeder — 8 saatlik ortalama alır
(anlık sıçrama silinir), uçları kırpar, 8 saatte bir yenilenir. Likidasyon
kaskadlarında basis hızla açılır ve funding bunu **saatler sonra** görür.
Bir şey kalacaksa **uçlarda** kalır. Pilot bunu kısmen destekliyor:
sd(basis) %0,0158 iken Binance funding tavanı %0,05 — yani kırpma çoğu zaman
devrede değil, ama TWAP gecikmesi **her zaman** devrede.

---

## 8. GEÇERSİZLİK KOŞULLARI

- §2'nin tanımları (özellikle `funding_t`'nin ileri-bakışsız seçimi) değişirse
- §3'ün sembol listesi ya da penceresi sonuç görüldükten sonra oynatılırsa
- §6'nın eşikleri (%0,5 · %0,26 · ρ 0,8) sonradan değiştirilirse
- Bantlar sembol içi yerine havuzlanmış olarak kesilirse

---

## 9. ÖLÇÜM

`onkayit_basis.py` — **salt okurdur**, hiçbir canlı dosyaya yazmaz, çalışan
süreçlere dokunmaz. Bu commit'ten **sonra** yazılır, ayrı commit'lenir.
İndirilen ham veri `_cache/basis/` altına yazılır (gitignore'lu; silinmesi
ölçümü bozmaz, yalnız yeniden koşumu yavaşlatır).
