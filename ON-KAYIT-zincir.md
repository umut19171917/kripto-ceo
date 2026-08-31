# ÖN KAYIT — `zincir`: borsa akışları yön taşıyor mu?

**Yazım anı:** 2026-09-01 (koşumdan ÖNCE; getiriyle hiçbir ilişki hesaplanmadan)
**Durum:** DONDURULDU. §2–§7 bu commit'ten sonra değiştirilmez.
**Şablon:** `ON-KAYIT-SABLON.md` (`cffe57c`)
**Fizibilite:** `FIZIBILITE-YENI-BOLGE-2026-09-01.md` (`3eee014`)
**Öncülleri:** `162100b` (basis) · `9871f58` (top_ls) · `8cdc9ef` (giriş) · `7910ce7` (maliyet)

---

## 0. Bu ölçüm ne YAPAR, ne YAPMAZ

- ⛔ Kârlılık hükmü kuramaz (mekanik ve portföy aşamaları yok).
- ⛔ Canlı kuralı değiştiremez.
- ✅ Tek cevapladığı: **borsalara giren/çıkan coin akışı, ertesi günün yönü
  hakkında ölçülebilir bilgi taşıyor mu?**

Geriye dönük ama **tamamen örneklem-dışı**: bu veri bu projede hiç
kullanılmadı, canlı sistemin hiçbir parçası onu görmüyor.

## 1. Neden bu ölçüm — ve neden bu ADAY

16 aday öldü. Hepsinin ortak yanı **aynı bant**: Binance perp'te gerçekleşmiş
işlemden türeyen metrikler. `basis` (4 yıl) ve `top_ls` de dahil — ikisi de
bandın *başka bir yeriydi*, dışı değil.

**Borsa akışları gerçekten bant dışıdır:** zincir üzerinde coin hareketidir,
türev işlemi değil. Ve iktisadi olarak arzın piyasaya ulaşma mekanizmasıdır —
borsaya giren coin satılabilir hale gelir, çıkan coin gelmez.

## 2. TANIMLAR (donduruluyor)

| büyüklük | tanım |
|---|---|
| `giris_t` | `FlowInExNtv` — o gün borsalara giren BTC (CoinMetrics) |
| `cikis_t` | `FlowOutExNtv` — o gün borsalardan çıkan BTC |
| `net_t` | `cikis_t − giris_t` |
| **`z_t`** | **`net_t / sd(net_{t−30..t−1})`** — **ANA DEĞİŞKEN** |
| `ileri_t` | `(PriceUSD_{t+1} − PriceUSD_t) / PriceUSD_t × 100` |

🔴 **ANA DEĞİŞKEN NEDEN `net`, NEDEN `z`** — ikisi de veriyle seçildi,
tercihle değil (ölçüldü 2026-09-01, **yalnız marjinaller**):

| aday | ρ₁ | τ | etkin n |
|---|---|---|---|
| giriş (ham) | +0,798 | 8,88g | **631** |
| çıkış (ham) | +0,786 | 8,35g | **672** |
| **net** | **+0,003** | **1,01g** | **5.576** |
| **net / 30g sd** | **+0,005** | **1,01g** | **5.525** |

Ham giriş ve çıkış **yavaş** çünkü ikisi de ortak bir bileşen taşıyor (genel
borsa hareketliliği); farkta o bileşen sadeleşiyor. `top_ls` dersinin aynısı:
bağımsız gözlem sayısını **öngörücü** belirler.

**`z` (30 günlük sd'ye bölme) ZORUNLU:** BTC arzı ve piyasa büyüklüğü pencerede
kat kat değişti; ham BTC adedi dönemler arasında kıyaslanamaz ve bantlar
**takvime göre** ayrılırdı. Bölen **yalnız geçmiş 30 günden** hesaplanır →
**ileri bakış yok.**

Tohum `olcum.TOHUM`.

## 3. ÖRNEKLEM

- **Kaynak:** CoinMetrics community API (anahtarsız). Akış serileri
  **2011-04-24'ten itibaren 5.608 gün, SIFIR eksik** (ölçüldü).
- 🔴 **PENCERE: 2017-01-01 → bugün** (~3.528 gün). **Gerekçe güç değil,
  türdeşliktir:** tüm geçmiş (5.608 gün, sd %4,49) ile 2017+ (3.528 gün,
  sd %3,55) **aynı saptanabilirliği** veriyor (%0,372 vs %0,370) — uzun
  pencerenin kazandırdığını yüksek oynaklık geri alıyor. Güç eşitse **daha
  türdeş** pencere seçilir. 2011-2013 BTC'si (fiyat ~1 $, birkaç borsa)
  bugünkü piyasayla aynı şey değildir.
- ⚠ **Tek varlık (BTC).** Gözlem birimi **gün**; kümeleme yok, çünkü
  gözlemin kendisi gün.
- ⚠ **Hayatta kalma yanlılığı yok** (BTC hep vardı), ama **tek varlık** sınırı
  var: sonuç BTC hakkındadır, kripto geneli hakkında değil.

## 4. RAPORLANACAK NİCELİKLER (sıra sabit)

1. Kapsama: gün sayısı · pencere · eksik gün.
2. **ANA SORU:** `z` beş bandı × ortalama `ileri` · Spearman ρ · uç bant farkı ·
   **bootstrap GA95** ve **etiket permütasyonu p** (ikisi birden — `olcum` deseni).
   ⚠ **Kümeleme uyarlaması:** gözlem = gün olduğu için "gün-kümeli" bootstrap
   sıradan bootstrap'a indirgenir; permütasyon etiketleri **tüm günler arasında**
   karıştırır. Bu, tasarımın gereğidir, yöntemden sapma değildir.
3. **Uç değer denetimi:** medyan ve %1-%99 kırpılmış ortalama.
4. **KONTROL KOLU (8.2):** `AdrActCnt` günlük değişimi — aynı makine, aynı ufuk.
   *"Herhangi bir zincir-üstü seri bu kadarını verir mi?"* sorusunun cevabı.
5. **GÜÇSÜZ KOL (kayda geçer, hüküm doğurmaz):** ham `giris` ve `cikis`.
6. Sağlamlık: dönem ikiye bölünmüş (2017-2021 / 2022-2026) · en uç %1 kırpılmış.

## 5. 🔴 GÜÇ HESABI

Ölçülen girdiler: `n = 3.528` gün (2017+), `τ(z) = 1,01` → **etkin n ≈ 3.493**,
bant başına ~699. `sd(BTC 1g getiri, 2017+) = %3,55`.

```
SE(uç bant farkı) = 3,55 × sqrt(2/699) = %0,190
%95'te saptanabilir en küçük fark = 1,96 × 0,190 = %0,372
```

**Zorunlu cümle:** *n≈3.493 bağımsız gün ve sd=%3,55 ile ancak **%0,372**
büyüklüğünde bir bant farkını görebiliriz. Aradığımız ekonomik eşik %0,5 (§6)
bunun ÜZERİNDE — test aradığımız etkiyi bulabilecek güçtedir. Daha küçük bir
etki varsa göremeyiz; "yok" değil **"ölçülemedi"** denir.*

⚠ **Güçsüz kol (§4.5) için aynı cümle olumsuz:** ham akışların etkin n'i
631-672 → saptanabilir ≈ **%0,88**. O kolun hükmü sonuç ne olursa olsun
**"ölçülemedi"**dir ve bu **şimdiden** yazılıdır.

## 6. 🔴 KARAR KURALI — sonucu görmeden

Eşik dayanağı (`olcum.py`): gidiş-dönüş %0,13 · uzun-kısa %0,26 · ekonomik
eşik **%0,5** — `basis` ve `topls` ile aynı, karşılaştırılabilirlik için.

| Bulgu | Sonraki adım |
|---|---|
| Bantlar monotonik (\|ρ\|≥0,8) **VE** uç fark ≥ **%0,5** **VE** GA sıfırı dışlıyor **VE** p<0,05 **VE** medyan/kırpılmış aynı yön | ✅ **BANT DIŞINDA BİLGİ VAR.** Mekanik aşaması için AYRI ön kayıt |
| GA sıfırı dışlıyor ama uç fark %0,26–0,5 | ⚠ İstatistiksel var, **ekonomik yok** |
| Ortalama geçiyor, medyan/kırpılmış geçmiyor | ❌ **UÇ DEĞER ESERİ** |
| GA sıfırı kapsıyor **veya** p≥0,05 | ❌ Bilgi yok |

🔴 **KONTROL KOLU KURALI (peşinen):** `AdrActCnt` kolu da geçerse, ana kolun
sonucu **zayıflar** — o zaman bulunan şey *"borsa akışına özgü bilgi"* değil,
*"herhangi bir zincir-üstü serinin taşıdığı genel bilgi"*dir ve ayrıca
sınanması gerekir.

🔴 **ÇOKLU KARŞILAŞTIRMA (peşinen):** ana kol düşüp **ikincil bir kol geçerse
bu BULGU DEĞİLDİR.** Altı kol raporlanıyor; birinin p<0,05 çıkması beklenir.

⚠ **%0,5'i geçmek "kârlı" demek DEĞİLDİR.** Mekanik aşamasına geçiş için
ayrıca `taban_R` şartı vardır (şablon §6): ana sicil **0,1736R** · radar
**0,0279R**.

## 7. 🔴 KARMAŞIKLIK BÜTÇESİ (madde 6.2)

Bu ölçüm **kural doğurmaz** — bir adayı mekanik aşamasına **terfi ettirebilir**.
Terfi ederse ve sonunda bir kural doğarsa, o ön kayıtta emeklilik adayı
gösterilecektir. Bu aşamada bütçe **değişmiyor**.

## 8. BEKLENTİ (dürüstlük kaydı — sonuç görülmeden)

**Bulamayacağımızı bekliyorum.** Gerekçe: 16 aday öldü; `basis` 4 yılda,
`top_ls` 30 günde hiçbir şey taşımadı; ve borsa akışları piyasanın **en çok
izlenen** zincir-üstü göstergelerinden biri — kolayca görülebilen bir bilgi
kalıcı olarak fiyatlanmamış olamaz.

**Kendime karşı argüman (zayıf değil):** bu, projenin sınadığı **ilk gerçek
bant dışı** değişkendir. Önceki 16 adayın hepsi aynı bandın kılığıydı ve
başarısızlıkları bu adayın önsel olasılığını **düşürmez** — farklı bir yere
bakıyoruz. Ayrıca `net` akışın kalıcılığı neredeyse sıfır (τ=1,01), yani
gürültü değil **olay** taşıyor olabilir.

**Beklemediğim ve beklemediğimi yazdığım şey:** kontrol kolunun (`AdrActCnt`)
ana koldan güçlü çıkması. Çıkarsa, bulduğumuz şey akışa özgü değildir.

## 9. GEÇERSİZLİK KOŞULLARI

- §2 tanımları (özellikle `z`'nin **yalnız geçmiş 30 günden** hesaplanması) değişirse
- §3 penceresi (2017-01-01) sonuç görüldükten sonra oynatılırsa
- §6 eşikleri (%0,5 · %0,26 · ρ 0,8) sonradan değiştirilirse
- Ana değişken `z` yerine başka bir biçime çevrilirse
- CoinMetrics metrik tanımını değiştirirse (seri yeniden indirilip karşılaştırılır)

## 10. ÖLÇÜM

`onkayit_zincir.py` — **salt okur**, canlı hiçbir dosyaya yazmaz. `olcum.py`
çıkarım katmanını kullanır. İndirilen ham veri `_cache/zincir/` altına yazılır
(gitignore'lu). Bu commit'ten SONRA yazılır, AYRI commit'lenir.

---

# SONUÇ — **BORSA AKIŞLARI DA BİLGİ TAŞIMIYOR** (2026-09-01)

**Örneklem:** 3.528 gün · 2017-01-01 → 2026-08-29 · tek varlık (BTC).

## Ana kol — §6'nın karar kuralı

```
  z = net akış / 30g sd  ->  ERTESI GUN getirisi
  ortalama   -0,050  +0,485  +0,002  +0,300  +0,197     uc fark +0,247%
  MEDYAN     +0,151  +0,233  -0,044  +0,111  +0,165
  KIRPILMIS  -0,011  +0,465  -0,012  +0,270  +0,174
  rho = +0,300     bootstrap GA95 [-0,146%, +0,653%]     permutasyon p = 0,1855
```

**❌ BİLGİ YOK.** Üç şartın üçü de kalıyor: GA sıfırı **kapsıyor** ·
p **0,19** · ρ=**0,300** (eşik 0,8; bantlar monotonik değil — 2. bant en yüksek,
3. bant sıfıra yakın).

**Sağlamlık:** ilk yarı uç fark **+0,564%** (p=0,079), ikinci yarı **−0,140%**
(p=0,477). **İşaret dönüyor.** Gürültüyle uyumlu.

## Kontrol kolu da düştü

`AdrActCnt` günlük değişimi: uç fark +0,315%, GA [−0,049%, +0,686%], p=0,1037.
**Hiçbir zincir-üstü seri bilgi göstermedi** — yani ana kolun düşmesi
"yanlış seri seçtik" ile açıklanamaz.

## 🔴 ÖN KAYIT TAM DA BURADA İŞE YARADI

**Ham çıkış kolu istatistiksel olarak GEÇTİ:**

```
5b. HAM CIKIS   uc fark +0,407%   GA95 [+0,004%, +0,818%]   p = 0,0260
```

GA sıfırı **dışlıyor** ve p<0,05. Ön kayıt olmasaydı bugün *"borsadan çıkış
ertesi günü öngörüyor"* diye yazardım. **Yazamıyorum, üç bağımsız nedenle:**

**1. Peşinen güçsüz ilan edilmişti (§5).** Ham çıkışın τ'su 8,35 gün →
etkin n **672**, saptanabilir fark **~%0,88**. Gözlenen +0,407% bunun yarısı.
Hükmü sonuç ne olursa olsun **"ölçülemedi"** yazılıydı.

**2. Çoklu karşılaştırma (§6, peşinen).** Altı kol raporlandı. Sıfır hipotezi
altında en az birinin p<0,05 çıkma olasılığı ≈ **%26**. *"Ana kol düşüp
ikincil bir kol geçerse bu BULGU DEĞİLDİR"* satırı tam bunun için yazılmıştı.

**3. 🔴 Ve p'nin kendisi şişkin.** `olcum.py`'de 2026-09-01 denetiminde
ölçülerek yazılan şerh: *"öngörücü yavaşsa (τ ≫ 1 gün) gün-içi/etiket
permütasyonu **fazla dar** bir sıfır dağılımı üretir ve p'yi küçük gösterir."*
Ham çıkışın τ'su **8,35 gün**; etiketleri tüm günler arasında karıştırmak o
kalıcılığı yok sayıyor. **Yani p=0,026 yöntemin bir eseri, verinin değil.**

⚠ Aynı gerekçe ana kol için **geçerli değil**: `z`'nin τ'su **1,01 gün**, yani
orada permütasyon güvenilir — ve orada p=0,1855.

## 🔴 PROJE İÇİN ASIL SONUÇ

Bu, projenin sınadığı **ilk gerçek bant dışı** değişkendi. Önceki 16 aday
Binance perp'te gerçekleşmiş işlemden türüyordu; `basis` ve `top_ls` dahil.
Borsa akışı zincir üzerinde coin hareketidir — **bandın dışı.**

**Ve o da boş çıktı.**

Madde 7.4'ün tek-bant hipotezi `basis`te zayıflamıştı (`162100b`: basis'in
%63'ü funding'den farklıydı ve o kısım da boştu). Bu ölçüm onu **daha da**
zayıflatıyor: *"hep aynı bilgiye baktığımız için bulamıyoruz"* açıklaması artık
iki bağımsız ölçümle desteklenmiyor.

Geriye daha sert olasılık kalıyor — ve her ölçümle biraz daha güçleniyor:
**bu ölçekte, günlük/saatlik ufukta, halka açık veriyle yön bilgisi
bulunamıyor.** ⚠ Kanıtlanmadı; *"aradık, bu araçlarla bulamadık"* deniyor.

## Beklentim tuttu — ama karşı argümanım da yanlış çıkmadı

§8'de *"bulamayacağımızı bekliyorum"* yazmıştım: tuttu. Ama aynı yerde
*"bu ilk gerçek bant dışı değişken, önceki başarısızlıklar bunun önsel
olasılığını düşürmez"* diye kendime karşı argüman da yazmıştım — **o da
haklıydı ve ölçmeye değerdi.** Ölçmeseydik bilemezdik.

## Sıradaki

Kuyrukta **emir defteri derinliği** kaldı (~30 gün). Makro bölgesi kaynak
kısıtıyla beklemede. Bu ölçüm **17. ölü aday**dır.
