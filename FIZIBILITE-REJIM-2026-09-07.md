# Fizibilite — rejim kapısı ölçülebilir mi?

**Tarih:** 2026-09-07
**Soru:** `rejim.py`'nin ürettiği piyasa rejimi (volatilite + korelasyon), canlı
sistemde kapı/boyut/seçicilik ayarlıyor. Bu kapının **kendisi hiç ölçülmedi**.
Ölçülebilir mi — bugün, ya da makul bir bekleyişle?

**Cevap: HAYIR (yön kolu). Bu bir "biraz daha bekle" durumu değil, yapısal.**

⚠ Bu belge **ön kayıt değildir** ve hiçbir etki tahmini içermez. Yalnızca
*ölçülebilirlik* aritmetiğidir. EK 4'ün var oluş sebebi tam olarak budur:
göremeyeceği etkiyi arayan testi **koşmadan önce** eleme.

---

## 1. Kapı ne yapıyor (canlı davranış)

`rejim.py` üç bileşen hesaplıyor, `makro.py` bunu kapıya çeviriyor:

| bileşen | formül | canlı eşik |
|---|---|---|
| volatilite | BTC son-30g getiri sd'si / taban sd (200g pencere) | `vol_orani ≥ 1,50` |
| korelasyon | BTC-ETH-SOL-LINK saatlik getiri ort. ikili korelasyonu | `≥ 0,85` |
| trend | BTC fiyat vs 50g SMA + 30g değişim | *kapıya girmiyor* |

- ikisi de yüksek → **KAPALI** (yeni giriş yok)
- biri yüksek → **DİKKAT** (boyut ×0,5 · min_skor 70→80)
- ikisi de normal → **AÇIK**

📌 Trend etiketi (boğa/ayı/yatay) hesaplanıyor ve sicile damgalanıyor ama
**hiçbir kararı etkilemiyor** — yalnız kayıt.

---

## 2. Yol A — kendi sicilimizden ölçmek: ÖLÜ

Sicilde her tahmine `rejim_durum`, `vol_orani`, `korelasyon`, `etkin_min_skor`
damgalanmış. Doğrudan "OYNAK'ta doğan sinyaller daha mı kötü?" sorulabilir.

**Ama sayılar tutmuyor:**

| | ANA | RADAR |
|---|---|---|
| `rejim_durum` dolu | 120/370 (%32) | 525/535 (%98) |
| OYNAK damgalı, **tetiklenmiş** | 6 | 15 |
| görüldüğü ayrı gün | 9 | 11 |
| **ayrı epizot** | **2** | **4** |
| `vol_orani` en yüksek değeri | **1,20** | **1,21** |
| sd(sonuç_R) | 1,464 | 1,385 |

İki bağımsız kilit:

**(a) Volatilite kolu hiç ateşlenmemiş.** Sicilin tamamında (2026-07-15 →
2026-09-07) `vol_orani` **bir kez bile 1,50'yi geçmemiş** — tepe 1,21.
Bu güç sorunu değil, **gözlem yokluğu**: n = 0.

**(b) Korelasyon kolunda 21 gözlem var ama 4 epizot.** `top_ls` dersi burada
birebir tekrarlıyor: **etkin örneklem yordayıcıya göre belirlenir.** Korelasyon
7 günlük yuvarlanan pencere; aynı epizottaki 6 sinyal 6 bağımsız gözlem değil.

> **EK 4 cümlesi:** n_eff≈4, sd=1,40 ile ancak **1,96R** büyüklüğünde bir etkiyi
> görebiliriz. Ortalama kazanç +2,08R olduğuna göre bu, "etki tüm kazancın
> büyüklüğünde olmalı" demektir. Aradığımız etki bundan küçükse bu test onu bulamaz.

**Beklemek çözmez:** ~2 ay boyunca 4 epizot görüldü. n_eff=30'a ulaşmak
bu hızda **~15 ay** sürer. Daha çok *sinyal* işe yaramaz — daha çok **epizot** gerekir.

📌 Ayrıca yapısal bir sansür var: kapı `min_skor`'u 80'e çıkardığında 70-79 arası
sinyaller **hiç kaydedilmedi**. Karşı-olgusal gözlenemiyor — kapının *maliyeti*
de bu sicilden ölçülemez.

---

## 3. Yol B — mumlardan tarihsel yeniden kurmak: yön kolu yine ÖLÜ

Rejim tamamen BTC mumlarından hesaplanıyor; sicile muhtaç değil. `/fapi/v1/klines`
`startTime` ile sayfalanarak **futures başlangıcına** kadar çekildi.

**Veri:** 2.557 günlük mum · **2019-09-08 → 2026-09-07 (7 yıl)** ·
`vol_orani` serisi 2.357 gün (200g pencere ısınması düşülmüş) ·
canlı formülün **aynısı** kullanıldı.

**Dağılım:** min 0,24 · medyan 0,87 · max 3,11

**Canlı eşik 1,50 tarihsel olarak: 146 gün (%6,2), 10 AYRI EPİZOT**

| epizot | süre |
|---|---|
| 2020-03-26 → 2020-04-10 | 16 gün |
| 2020-12-01 → 2020-12-04 | 4 gün |
| 2020-12-18 → 2020-12-25 | 8 gün |
| 2021-01-11 → 2021-03-09 | 58 gün |
| 2023-11-21 | 1 gün |
| 2024-03-16 → 2024-04-03 | 19 gün |
| 2024-04-09 → 2024-04-14 | 6 gün |
| 2025-03-17 → 2025-03-27 | 11 gün |
| 2025-12-02 → 2025-12-03 | 2 gün |
| 2026-02-05 → 2026-03-06 | 30 gün |

✅ **Eşik kalibrasyonu makul görünüyor** — %6,2 sıklık, ve tepeler gerçek
olaylara oturuyor (2020 Mart çöküşü, 2021 Ocak-Mart, 2024 Mart, 2026 Şubat).
Kapı bozuk değil; sicil dönemimiz (Tem-Eyl 2026) sadece **sakin bir aralık**.
Son yüksek-vol epizodu ~6 ay önce bitmiş.

### Israr ve etkin örneklem

```
lag-1 otokorelasyon  phi = 0,9776
tau = (1+phi)/(1-phi) = 88,3 gün
n_eff = 2.357 / 88,3 = 26,7
```

Yüksek kolun bağımsız birimi **epizot sayısıdır: 10**. Sakin kol ≈ 2.211/88,3 ≈ 25.

### Güç hesabı — yön kolu

İleri getirilerin yayılımı (ortalamalara **bakılmadı**):
`1 gün sd = %3,02` · `7 gün sd = %8,07`

```
SE ≈ sd × sqrt(1/10 + 1/25) = sd × 0,374
1 gün : SE = %1,13  ->  görülebilen en küçük etki ≈ 2,8×SE = %3,16 / gün
7 gün : SE = %3,02  ->  görülebilen en küçük etki ≈ %8,45 / 7 gün
```

> **EK 4 cümlesi:** n_eff=10 epizot, sd=%3,02 ile ancak **%3,16 günlük** bir
> etkiyi görebiliriz. Projenin ekonomik eşiği **%0,5**. Aradığımız etki
> bundan küçükse — ki mertebe olarak öyle — **bu test onu bulamaz.**

Detektör tabanı, aranan etkinin **~6 katı**. Test ölü doğar.

### Neden daha fazla veri kurtarmıyor

- **Daha çok sembol İŞE YARAMAZ.** Rejim piyasa-geneli bir değişken (BTC'den
  hesaplanıyor). Sembol eklemek epizot sayısını artırmaz — aynı 10 epizottur.
  (`FIZIBILITE-UZUN-UFUK` ile aynı yapı: yordayıcı ortaksa n artmaz.)
- **Daha uzun tarih marjinal.** Spot 2017'ye gider (+2 yıl, belki +3 epizot).
  13 epizot → taban %3,16'dan ancak **%2,77**'ye iner. Hâlâ %0,5'in ~5 katı.
- **Tek kurtarıcı: daha çok kriz.** Talep edilecek bir şey değil.

---

## 4. Ölçülebilir olan tek kol — ve neden bulgu sayılmaz

**Yayılım kolu:** "yüksek `vol_orani` sonraki gerçekleşen volatiliteyi öngörür mü?"
Bu kol iyi güçlendirilmiş, çünkü varyans karesel getirilerden tahmin edilir ve
epizot içi günler bilgi taşır.

⚠ **Ama bu bir bulgu değil, tautoloji kontrolüdür.** Volatilite kümelenmesi
finansın en sağlam olgularından biri. Sonucu pozitif çıkarsa hiçbir şey
öğrenmiş olmayız; **negatif çıkarsa boru hattımız bozuktur**. Yani değeri
yalnızca **kontrol kolu** (madde 8.2 tasarım doğrulaması) olarak vardır.

📌 Ve kapının asıl davranışına (boyut ×0,5) dair açık bir soru bırakıyor:
**R zaten volatiliteye göre normalize ediyorsa** (stop mesafesi oynaklıkla
genişliyorsa), yüksek volde boyutu ayrıca yarıya indirmek **çifte sayım**
olabilir — sistemi sistematik olarak *az riskli* hale getirir. Bu soru
sicile muhtaç (§2) ve şu an ölçülemez.

---

## 5. Hüküm

**Rejim kapısının yön gerekçesi, eldeki hiçbir veriyle yanlışlanabilir değil.**
İki bağımsız yol da güç tabanına takıldı:

| yol | etkin n | görülebilen en küçük etki | aranan etki | sonuç |
|---|---|---|---|---|
| kendi sicilimiz | ~4 epizot | 1,96R | «1R | ❌ ölü |
| 7 yıllık mumlar | 10 epizot | %3,16/gün | ~%0,5 | ❌ ölü |

**Bu bir "ölçtük, bilgi yok" hükmü DEĞİLDİR** — `basis` ve `zincir`de olduğu gibi
"yokluğun kanıtı" diyemeyiz. Buradaki ifade daha zayıf ve daha dürüst:
**ÖLÇÜLEMEDİ.** (`top_ls`'in seviye kolu ile aynı statü.)

### Pratik sonuç

1. **Kapı canlıda kalsın.** Kaldırmak için de gerekçemiz yok — ölçemiyoruz.
   Ve yapısı zaten temkinli: skora karışmıyor, hatada nötre düşüyor,
   yalnız yumuşatıyor. **Sınanmamış bir varsayım olarak etiketlensin, o kadar.**
2. **Ön kayıt YAZILMADI — bilerek.** Göremeyeceği etkiyi arayan bir teste
   ölçüm yuvası harcamak, EK 4'ün önlemek için var olduğu hatanın ta kendisi.
   Bu belge o kararın gerekçesidir.
3. **Yeniden açılma şartı:** yüksek-vol epizot sayısı ~30'a ulaşırsa (bugünkü
   tarihsel hızla **on yıllar**), ya da kapı bir gün gerçekten `KAPALI`
   konumuna geçip ölçülebilir bir maliyet üretirse.

---

## 6. Yöntem notu — bu belgenin kendi sınırı

- Güç hesapları **tek kuyruklu değil**, 2,8×SE (≈%80 güç, α=0,05) kestirmesiyle
  yapıldı. Kesin bir güç eğrisi değil, **mertebe** hesabıdır. Mertebe 6 kat
  olduğu için kesinlik gerekmedi.
- Etkin örneklem için yüksek kolda **epizot sayısı** kullanıldı; bu, τ tabanlı
  n_eff'ten (26,7) daha muhafazakâr. τ tüm seriden hesaplandığı ve uzun sakin
  aralıkları içerdiği için epizot sayımı daha dürüst kabul edildi.
- Hiçbir aşamada ileri getirilerin **ortalaması** hesaplanmadı; yalnız sd.
  Betik bu kısıtı kendi başlığında taşıyor.
- ⚠ Korelasyon kolunun tarihsel yeniden kurulumu **yapılmadı**: saatlik mumlar
  1000 ile sınırlı (2026-07-28'e kadar). Sayfalayıcıyla çekilebilir; ama yön
  kolunun tabanı volatilite kolununkiyle aynı mertebede olacağı için
  (aynı 10 civarı epizot, aynı piyasa-geneli yapı) **öncelik verilmedi.**
  Bu bir varsayımdır ve öyle işaretlenmiştir.
