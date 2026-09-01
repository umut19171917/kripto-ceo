# ÖN KAYIT — `ucesik`: funding UÇLARDA bilgi taşıyor mu? (U biçimi)

**Yazım anı:** 2026-09-01 (koşumdan ÖNCE; test kümesinde hiçbir ilişki hesaplanmadan)
**Durum:** DONDURULDU. §2–§7 bu commit'ten sonra değiştirilmez.
**Şablon:** `ON-KAYIT-SABLON.md` (`cffe57c`)
**Bağlı madde:** 3.2 — Madde 6 (funding eşiği), açık kalan parça
**Öncülleri:** `162100b` (basis) · `eb266a7` (zincir)

---

## 0. 🔴 KEŞİF KÜMESİ ile TEST KÜMESİ AYRI — önce bunu okuyun

**Hipotez `basis` ölçümünde DOĞDU** (`162100b`). Orada bantlar monotonik değil
**U biçimli** çıkmıştı — iki uç ortadan yüksek — ve o gözlem **post-hoc** diye
işaretlenip *"sınanmak istenirse kendi ön kaydını ve doğrusal-olmayan bir
istatistiği gerektirir"* denmişti. Bu, o ön kayıttır.

🔴 **Aynı veride sınamak `ters`teki hatanın aynısı olurdu** (`0130da6` §0:
örneklem-içi inşa, hüküm doğurmaz). Bu yüzden:

| küme | semboller | rolü |
|---|---|---|
| **KEŞİF** | `olcucu.SYMBOLS`'ün 10'u (BTC, ETH, SOL, LINK, XRP, BNB, DOGE, ZEC, ADA, NEAR) | Hipotez burada doğdu. **HÜKÜM DOĞURMAZ. Ölçüme HİÇ girmez.** |
| **TEST** | ≥3 yıl günlük verisi olan **diğer 132 USDT perp** | Hipotezin **hiç görülmediği** veri. **Hüküm YALNIZ buradan.** |

⚠ **Bu tam bağımsızlık değildir:** kripto sembolleri birlikte hareket eder,
yani test kümesi keşif kümesinden istatistiksel olarak bağımsız değil. Ama
**farklı varlıklar, farklı funding dinamikleri** — ve elimizdeki en iyi
örneklem-dışı ayrım budur. Hüküm bu şerhle yazılır.

## 1. Neden bu ölçüm

Madde 3.2 (Madde 6 / funding eşiği) yarım kalmıştı: mekanizma **doğrulanmış**
(SHORT payı %76,1 vs %47,6, p<0,00001) ama zarar **çürütülmüş** (p=0,243).
İşlem düzeyinde sınanamıyor (madde 3.3: 3.668 işlem ≈ 4 yıl gerekir).

`basis` funding'i **sinyal düzeyinde** 350 bin gözlemde ölçtü ve **monotonik**
bilgi bulamadı. Ama Madde 6 monotonik bir kural değil — **uçlarda ateşleyen bir
eşik kuralı.** Monotonik test tam da ona kördür.

## 2. TANIMLAR (donduruluyor)

| büyüklük | tanım |
|---|---|
| `f_t` | Gün `t`'nin **açılışından KESİN ÖNCE** yayımlanmış son funding oranı (%) |
| `ileri_t` | `(kapanış_t − açılış_t) / açılış_t × 100` — 1 günlük ileri getiri |
| bant | `f` sıralamasıyla **sembol içinde** 5 eşit sayılı bant |
| **`uc_orta`** | **`ort(bant 1 ∪ bant 5) − ort(bant 2 ∪ 3 ∪ 4)`** — **ANA İSTATİSTİK** |

🔴 **İleri bakış yasağı, iki kat sıkı:** `f_t` yalnız `fundingTime < gün_açılışı`
olanlardan seçilir — **kesin küçük**. Funding 00:00 UTC'de takas oluyor ve
günlük bar da 00:00'da açılıyor; eşitliği dışlamak eşzamanlılık şüphesini
tamamen kaldırır (bir önceki günün 16:00 takası kullanılır).

🔴 **Ana istatistik NEDEN `uc_orta`:** Madde 6 uçlarda ateşliyor. Monotonik
Spearman/uç-bant-farkı U biçimine **kördür** — `basis`te tam bu oldu.
`uc_orta` doğrudan U biçimini ölçer.

Ölçek: bantlar **sembol içinde** kesilir (funding ölçeği sembole göre değişir).
Tohum `olcum.TOHUM`.

## 3. ÖRNEKLEM

- **TEST kümesi:** Binance USDT perpetual, `TRADING`, **≥1.095 günlük bar**
  (3 yıl), **keşif kümesinin 11 sembolü HARİÇ**. Ölçüldü: **132 sembol,
  184.079 sembol-gün** (2026-09-01).
- Pencere: son **1.460 gün**; sembolün verisi kısaysa kendi başlangıcından.
- ⚠ **Hayatta kalma yanlılığı:** bugün `TRADING` olan semboller. Listelemeden
  kalkmış perp'ler yok. Getiri **seviyeleri** yukarı yanlı; **sıralama**
  sorusu daha az etkilenir ama muaf değil.
- ⚠ **Faz seçimi bilinçli:** gözlem günde bir, **00:00 UTC** — funding takas
  anı. Rastgele değil, **kasıtlı** ve gerekçesi funding'in yayım anı olması.

## 4. RAPORLANACAK NİCELİKLER (sıra sabit)

1. Kapsama: sembol · sembol-gün · takvim günü · funding eşleşmeyen gün.
2. **ANA:** `uc_orta` · **gün-kümeli bootstrap GA95** · **gün-içi permütasyon p**
   (ikisi birden; `olcum` deseni — biri eksikse hüküm basılmaz).
3. **Karşılaştırma için MONOTONİK istatistik:** bant5 − bant1 ve Spearman ρ.
   *"Monotonik test gerçekten kör müydü"* sorusunun cevabı.
4. Beş bandın ortalamaları (U biçimi görünüyor mu, görsel kayıt).
5. **Uç değer denetimi:** medyan ve %1-%99 kırpılmış `uc_orta`.
6. **KONTROL KOLU (8.2):** aynı makine, funding yerine **rastgele atanmış**
   bant etiketleriyle (sembol içi, aynı sayılar). *"Bu tasarım kendi başına
   pozitif üretir mi?"*
7. Sağlamlık: dönem ikiye bölünmüş · top-3 sembol çıkarılmış.

## 5. 🔴 GÜÇ HESABI

Ölçülen: 132 sembol · 184.079 sembol-gün · 1.460 takvim günü ·
`sd(günlük getiri) = %5,55` (12 sembol örneği, n=15.790).

Muhafazakâr etkin bağımsız birim: `1.460 gün × 2,5 etkin sembol = 3.650`.
`uc_orta` grupları %40 / %60 → `n₁=1.460`, `n₂=2.190`.

```
SE = 5,55 × sqrt(1/1460 + 1/2190) = %0,187
%95'te saptanabilir en küçük fark = 1,96 × 0,187 = %0,367
```

**Zorunlu cümle:** *n_eff≈3.650 ve sd=%5,55 ile ancak **%0,367** büyüklüğünde
bir uç-orta farkını görebiliriz. Aradığımız ekonomik eşik %0,5 (§6) bunun
ÜZERİNDE — test aradığımız etkiyi bulabilecek güçtedir. Daha küçük bir etki
varsa göremeyiz; "yok" değil **"ölçülemedi"** denir.*

📌 Referans: `basis`te gözlenen U genliği ~%0,15-0,25 idi. **Bu test onu
göremez** ve bunu peşinen kabul ediyorum — aranan şey *ekonomik olarak
anlamlı* bir U, gözlenen fısıltı değil.

## 6. 🔴 KARAR KURALI — sonucu görmeden

| Bulgu | Sonuç |
|---|---|
| `uc_orta` ≥ **%0,5** **VE** GA sıfırı dışlıyor **VE** p<0,05 **VE** medyan/kırpılmış aynı yön | ✅ **UÇLARDA BİLGİ VAR.** Madde 6 **doğrulandı**; mekanik aşaması için ayrı ön kayıt |
| GA dışlıyor, p<0,05, ama `uc_orta` %0,26–0,5 | ⚠ İstatistiksel var, **ekonomik yok.** Madde 6 kural olarak kalır ama **güçlendirilmez** |
| GA sıfırı kapsıyor **veya** p≥0,05 | ❌ **Uçlarda da bilgi yok.** Madde 6 **emeklilik adayıdır** (§7) |
| Kontrol kolu (rastgele etiket) da geçerse | 🔴 **TASARIM HATASI** — hiçbir sonuç okunmaz, araç incelenir |

🔴 **U biçiminin İŞARETİ de dondurulur:** `uc_orta` **pozitif** beklenir
(uçlar ortadan yüksek — `basis`te öyle görünmüştü). **Negatif çıkarsa**, bu
`basis`teki gözlemin **tersi**dir ve *"bulduk"* denemez; ayrı bir hipotezdir.

⚠ Madde 6 geçse bile **mekanik aşamasına geçiş için ayrıca `taban_R` şartı**
vardır (şablon §6: ana sicil 0,1736R · radar 0,0279R).

## 7. 🔴 KARMAŞIKLIK BÜTÇESİ (madde 6.2)

Bu ölçüm **yeni kural doğurmaz.** Doğrudan bir emeklilik kararı üretir:

- **Geçerse:** Madde 6 (funding eşiği) **doğrulanır** — kural sayısı **değişmez**.
- **Kalırsa:** Madde 6 **emeklilik adayı** olur ve kural sayısı **azalabilir**.

Yani bütçe artı yönde **hiç** işlemiyor; bu, 6.2'nin istediği tam olarak budur.

## 8. BEKLENTİ (dürüstlük kaydı — sonuç görülmeden)

**Bulamayacağımızı bekliyorum.** Gerekçe: `basis`te gözlenen U genliği güven
aralığının **içindeydi**, yani muhtemelen gürültüydü. Ayrıca 17 aday öldü.

**Kendime karşı argüman:** U biçimi `basis`in **üç kolunda birden** göründü
(artık, ham basis, funding). ⚠ Ama bu üç kol **aynı veriden ve ilişkili
değişkenlerden** geliyor — yani bu **bir** gözlemdir, üç değil. Karşı argümanı
yazıyorum ama **zayıf** olduğunu da yazıyorum.

**İkinci karşı argüman (daha güçlü):** funding uçları gerçek bir iktisadi olayı
işaret eder — aşırı kaldıraçlı konumlanma. Likidasyon kaskadları oradan çıkar.
Mekanizma makul; sorun büyüklüğünün ölçülebilir olup olmadığı.

## 9. GEÇERSİZLİK KOŞULLARI

- Keşif kümesinin 11 sembolünden **herhangi biri** test kümesine girerse
- `f_t`'nin **kesin-önce** seçimi gevşetilirse
- §3'ün ≥3 yıl şartı ya da pencere sonuç görüldükten sonra oynatılırsa
- §6 eşikleri ya da `uc_orta`'nın beklenen işareti sonradan değiştirilirse
- Ana istatistik `uc_orta` yerine başka bir şeye çevrilirse

## 10. ÖLÇÜM

`onkayit_ucesik.py` — **salt okur**. `olcum.py` çıkarım katmanını kullanır.
İndirilen veri `_cache/ucesik/` altına yazılır (gitignore'lu).
Bu commit'ten SONRA yazılır, AYRI commit'lenir.

---

# SONUÇ — **UÇLARDA DA BİLGİ YOK** (2026-09-01)

**Test kümesi:** 132 sembol · **183.972 sembol-gün** · 1.460 takvim günü.
🔴 **Keşif kümesi sızıntısı: 0** — §9'un geçersizlik şartı temiz.

## §6'nın karar kuralı

```
  bant ortalamalari: +0,132%  -0,019%  +0,001%  -0,050%  -0,029%
  uc_orta = +0,074%
  [1] gun-kumeli bootstrap GA95 : [-0,128%, +0,266%]   (1.460 gun)
  [2] gun-ici permutasyon       : p = 0,2229
```

**❌ UÇLARDA DA BİLGİ YOK.** GA sıfırı **kapsıyor**, p=0,22.
Gözlenen +0,074%, §5'in saptanabilirlik eşiği %0,367'nin **beşte biri**.

**Sağlamlık:** ilk yarı +0,170% (p=0,44) · ikinci yarı +0,060% (p=0,18).
İki dönem de aynı yerde.

## ✅ KONTROL KOLU TASARIMI DOĞRULADI — ilk kez

Rastgele atanmış bant etiketleriyle: `uc_orta = −0,023%`,
GA [−0,071%, +0,027%], **p=0,6546**. Yani bu tasarım **kendi başına pozitif
üretmiyor.** §6'nın *"kontrol kolu da geçerse TASARIM HATASI"* satırı
tetiklenmedi.

📌 Madde 8.2 (kontrol grubu zorunlu) bu sabah kapatılmıştı; **ilk gerçek
kullanımında işini gördü.**

## 🔴 U BİÇİMİ REPLİKE OLMADI — asıl bulgu bu

`basis`in keşif kümesinde funding bantları **U biçimliydi** (uçlar ortadan
yüksek, ρ=+0,300). Test kümesinde çıkan desen **başka**:

| | keşif kümesi (`basis`, 10 sembol) | test kümesi (132 sembol) |
|---|---|---|
| desen | **U biçimi** (uçlar yüksek) | **monotonik azalan** |
| Spearman ρ | +0,300 | **−0,800** |
| uç bant farkı | +0,025% | −0,162% |
| anlamlı mı | hayır | hayır |

**Farklı varlıklarda farklı desen, ikisi de anlamsız.** Bu, U biçiminin
gürültü olduğunun en doğrudan kanıtıdır — post-hoc bir gözlemin başka veride
tutmaması.

⚠ Test kümesindeki ρ=−0,800 da **bulgu değildir**: uç bant farkı −0,162%,
güven aralığının içinde ve §6 monotonik istatistiği ana ölçüt olarak
tanımlamıyor. Post-hoc bir deseni ikinci kez kovalamak, ilk hatanın tekrarı olur.

## Madde 6 (funding eşiği) → **EMEKLİLİK ADAYI**

§7'nin karmaşıklık bütçesi devreye girdi:

> *"Kalırsa: Madde 6 **emeklilik adayı** olur ve kural sayısı **azalabilir**."*

Madde 3.2'nin iki parçası artık kapandı:
- **Mekanizma çalışıyor** (SHORT payı %76,1 vs %47,6, p<0,00001) — ölçülmüştü
- **Ama taşıdığı bilgi yok** — bu ölçüm

Yani kural **tasarlandığı gibi ateşliyor ama ateşlemesinin bir değeri yok.**

⚠ **Emeklilik adayı ≠ emekli.** Kuralı canlıdan çıkarmak ayrı bir karardır ve
kullanıcıya aittir. Aciliyeti de düşük: skorun bütünü zaten ölçülmüş biçimde
ters (`b01d493`), bir bileşenini çıkarmak o gerçeği değiştirmez.

## Beklentim tuttu

§8'de *"bulamayacağımızı bekliyorum, çünkü `basis`teki U genliği güven
aralığının içindeydi"* yazmıştım. Tuttu. §8'de zayıf olduğunu **kendim
belirttiğim** karşı argüman (U'nun üç kolda birden görünmesi) da haklı
çıkmadı — nitekim orada *"bu üç kol aynı veriden geliyor, yani bir gözlemdir"*
diye şerh düşmüştüm.
