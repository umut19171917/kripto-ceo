# ÖN KAYIT — emir defteri derinliği (madde 7.4 / B4 · son aday)

**Dondurulma anı:** 2026-09-07
**Koşum hedefi:** ~2026-09-30 (arşiv 30 güne ulaştığında)
**Bağlı madde:** 7.4 (tek-bant sorunu) · 5.3 (derinlik/spread)

> 🔴 **BU ÖN KAYIT VERİ TAMAMLANMADAN YAZILDI.** Arşiv 2026-08-31'de başladı;
> bugün 7. gün. Koşum ~30. günde. Yordayıcı ile sonuç arasındaki **hiçbir ilişki
> hesaplanmadı** — §5'in girdileri yalnız (a) yordayıcının ısrarı, (b) getirinin
> yayılımı, (c) gözlem sayısıdır. Bu dosyanın git zaman damgası, ölçütlerin
> sonuçtan **önce** yazıldığının kanıtıdır. Madde 8.7: *kuralı düzyazıyla değil
> yapıyla koru.*

---

## 0. Bu ölçüm ne YAPAR, ne YAPMAZ

**İleri-zamanlı ve örneklem-dışı.** Veri 2026-08-31'den itibaren **ileriye doğru**
toplandı; hipotez (bant dışında bilgi var mı) veriden doğmadı, `basis`/`topls`
hükümlerinden doğdu. Ana kol, önceki hiçbir ölçümün koşmadığı sembollerde koşar.

⛔ **Kuramayacağı cümleler:**
- *"Emir defteri kârlı bir strateji taşır."* — bu ölçüm **bilgi** arar, strateji değil.
- *"Derinlik hiçbir ufukta bilgi taşımaz."* — yalnız **1 saatlik** ufuk sınanır.
- *"Kenar yok."* — yalnız `imb50`'nin sembol-içi sıra biçimi sınanır.
- *"Bu kural canlıya alınmalı."* — §6'nın maliyet tabanı geçilmeden mekaniğe geçilmez.

✅ **Cevapladığı tek soru:**
> Emir defteri dengesizliği (`imb50`), sonraki 1 saatlik **kesitsel** getiri farkı
> hakkında, işlem maliyetini aşacak büyüklükte bilgi taşıyor mu?

---

## 1. Neden bu ölçüm — ve neden ŞİMDİ

18 aday öldü. Hepsinin ortak özelliği: **aynı bant** — gerçekleşmiş pozisyonlanma
(funding, OI, likidasyon, long-short oranı, basis, zincir akışları). `basis`
hükmünde (`162100b`) bu şüphe yazıya geçti; `topls` hükmü (`9871f58`) onu
güçlendirdi: `top_ls` de sonuçta gerçekleşmiş pozisyonlanmadır.

**Emir defteri farklı bir şey ölçer: NİYET.** Duran emirler, henüz
gerçekleşmemiş arz-talebi gösterir. Bu, projenin sınamadığı **son bant**.

**Neden şimdi değil de 30 Eylül'de koşacak:** `/fapi/v1/depth` yalnız anlık
döner, **geçmişi yok**. Koşulmadığı her an kalıcı kayıp. Bu yüzden arşivci
2026-08-31'de kuruldu (`ed19c8f`) ve 30 gün birikmesi bekleniyor.

**Neden ön kayıt bugün donuyor:** son adayın hükmü, ölçüt-sonuç sıralamasının
kanıtlanabilir olmasını hak ediyor. 30 Eylül'de yazılırsa "sonuca bakmadım"
bir güven beyanı olur; bugün yazılırsa **zaman damgasıyla kanıt**.

---

## 2. TANIMLAR (donduruluyor)

### Ham veri
`derinlik_arsiv.py` her ~10 dakikada bir, sembol başına 7 sayı yazar:

```
[0] spread_bps   (en_iyi_satis - en_iyi_alis) / orta * 10000
[1] imb5         5 kademede  (alis_notional - satis_notional) / toplam
[2] imb50        50 kademede aynısı
[3] imbN         tüm defterde aynısı
[4] notN         defterin toplam notional'ı
[5] span_bps     defterin ULAŞTIĞI fiyat aralığı
[6] orta         (en_iyi_alis + en_iyi_satis) / 2
```

### Yordayıcı (ana kol) — **`z`**

`z` = `imb50`'nin **sembol içinde, geriye dönük 72 saatlik** yüzdelik sırası.

🔴 **Neden ham `imb50` değil:** `span_bps` teşhisi kurulumda gösterdi ki defterler
sembole göre vahşice farklı fiyat aralığına uzanıyor (BTC 34 bps · ADA 14.128 bps).
Ham `imb50` **semboller arası kıyaslanabilir değildir**. Sembol içi sıra bunu düzeltir.

🔴 **İleri bakış yasağı:** sıra **yalnız `t` ve öncesindeki 72 saatten** hesaplanır.
Tüm örneklemin dağılımı **kullanılmaz** (bu ileri bakış olurdu). Bedeli: her
sembolün ilk 72 saati ana koldan düşer, ve bu **şimdiden kabul edilmiştir**.

🔴 **Ölçek düzeltmesi:** bantlar her saat **kesitsel olarak** kesilir (o saatte
nitelikli sembollerin `z`'leri sıralanır), sembol havuzu ham karıştırılmaz.

### Sonuç — **`getiri`**

`getiri(t)` = `orta(t+1s) / orta(t) − 1`, burada `t+1s`, saatlik ızgarada bir
sonraki nokta; gerçek zaman farkı **3600±600 sn** dışındaysa gözlem **düşer**.

### Ana istatistik — **`uc_fark`** (piyasa-nötr)

Her saatte nitelikli semboller `z`'ye göre **5 banda** kesilir. O saatin
kesitsel ortalama getirisi her gözlemden çıkarılır (**fazla getiri**), böylece
piyasa geneli hareket **farkla yok edilir**.

```
uc_fark = ortalama(bant5 fazla getirisi) − ortalama(bant1 fazla getirisi)
```

Bu bir **uzun-kısa** büyüklüktür → maliyeti `olcum.MALIYET_UZUN_KISA` = **%0,26**.

### Çözünürlük ve tohum
Saatlik ızgara · `random.seed(olcum.TOHUM)` = **11** · bant sayısı **5** ·
bootstrap **10.000** · permütasyon **10.000**.

---

## 3. ÖRNEKLEM

### Sembol seçimi — **liste değil ÖLÇÜT** (rotasyon sürüyor)

`derinlik_arsiv.semboller()` her turda **ana 11'i (`olcucu.SYMBOLS`) sabit**
tutar, üstüne `tarayici.evren(30M)` hacim liderlerini `SEMBOL_TAVANI=30`'a
kadar ekler. Hacim liderleri **her gün değişir** → panel **dengesiz ve rotasyonlu**.
Bu yüzden aşağısı sembol *listesi* değil sembol *ölçütüdür*:

| kol | ölçüt |
|---|---|
| **ANA KOL (temiz)** | `olcucu.SYMBOLS` **DIŞINDAKİ** semboller, **≥20 gün** kapsama, **≥300** nitelikli saatlik gözlem |
| **REFERANS KOL (kirli)** | ana 11 — **ayrı raporlanır, TEK BAŞINA HÜKÜM DOĞURMAZ** |

🔴 **Ana 11 neden kirli:** önceki **tüm** ölçümler orada koştu; sonuç verileri
defalarca incelendi. `ucesik`'in kurduğu keşif/test ayrımı (`55309bd`) burada
da uygulanır. 2026-09-07 itibarıyla ana dışı **13 sembol** ≥6 güne ulaşmıştı;
30 Eylül'de daha fazlası beklenir ama **sayı garanti edilmez** (bkz. §9).

### Pencere
2026-08-31 → koşum günü. Her sembolün **ilk 72 saati** düşer (sıra penceresi).

### 🔴 Açıkça yazılmış yanlılıklar

1. **Hayatta kalma yanlılığı — VAR ve giderilemiyor.** Arşivci *bugünkü* hacim
   liderlerini topluyor; listeden düşen sembolün verisi donuyor. Borsadan kalkan
   semboller eksik temsil edilir. ⚠ Bu, `ileritest`'te kesitsel momentumu düşüren
   yanlılığın **aynısı** — orada teşhis edilmişti, burada **baştan ilan ediliyor**.
2. **Örtüşen getiri — YOK (bilerek).** Saatte sembol başına **tek** gözlem alınır;
   1 saatlik ufukla örtüşme sıfırdır. `basis`'te permütasyon nullünü 0,13× daraltan
   sorun (`YONTEM-DENETIMI`) burada **tasarımla** kapatılmıştır.
3. **Tek rejim.** 30 gün tek piyasa rejimidir. `FIZIBILITE-REJIM-2026-09-07`:
   bu dönemde `vol_orani` 1,50'yi hiç geçmedi — yani **sakin rejim**. Sonuç
   oynak rejime genellenemez ve genellenmeyecek.
4. **Tek borsa.** Yalnız Binance perp defteri.

---

## 4. RAPORLANACAK NİCELİKLER (sıra sabit)

1. **Kapsama:** nitelikli sembol sayısı · toplam saatlik gözlem · düşen gözlem
   ve **düşme sebebi dağılımı** · UTC saat histogramı.
2. **Ana soru:** 5 bandın fazla getiri ortalaması · Spearman **ρ** · `uc_fark` ·
   **iki çıkarım**: gün-kümeli bootstrap **ve** saat-içi permütasyon
   (`olcum.bant_raporu` ikisi olmadan hüküm satırı basmaz).
3. **Uç değer denetimi:** `uc_fark`'ın medyanı ve **kırpılmış ortalaması** (%10).
   ⚠ Ortalama geçip kırpılmış geçmezse hüküm **"uç değer eseri"**dir.
   (Medyan burada geçerlidir — `giris`'teki sıfır-kütle sorunu bu tasarımda yok.)
4. **KONTROL KOLU (madde 8.2) — zorunlu.** Aynı gözlemler, `z` etiketleri
   **saat içinde rastgele karıştırılmış**. Beklenen: `uc_fark ≈ 0`, p yüksek.
   Kontrol kolu sıfırdan anlamlı sapıyorsa **boru hattı bozuktur, hüküm basılmaz.**
5. **Sağlamlık:** (a) en çok gözlem veren **3 sembol çıkarılmış**,
   (b) dönem **ikiye bölünmüş** (ilk 15 gün / son 15 gün),
   (c) `spread_bps` en yüksek %10 çıkarılmış (likidite kırıntısı denetimi).
6. **Referans kol:** ana 11 üzerinde aynı hesap — **ayrı tabloda, hükümsüz.**

---

## 5. 🔴 GÜÇ HESABI (EK 4)

### Ölçülmüş girdiler (2026-09-07, 7 günlük veriden — **ilişkiye bakılmadan**)

| girdi | değer |
|---|---|
| örtüşmeyen saatlik gözlem (7 gün, 44 sembol) | **3.780** |
| 30 güne doğrusal ölçek | **~16.200** |
| **`imb50` otokorelasyon süresi τ** (saatlik ızgara) | **medyan 1,06 sa** · ortalama 1,26 · aralık 0,56–7,78 |
| ileri 1 saatlik getiri **sd** | medyan **%1,52** · ortalama %2,67 · aralık %0,38–10,56 |

🔴 **τ = 1,06 saat — bu ölçümün en önemli sayısı.** `top_ls`'in seviye kolunu
öldüren şey τ≈416 saatti (n_eff≈1,7/sembol). Burada yordayıcı **hızlı**:
saatlik gözlemler neredeyse bağımsız. **Bağımsız birim = SAAT.**

### Etkin bağımsız birim

```
30 gün = 720 saat  ->  bağımsız saat ≈ 720 / 1,06 ≈ 680
```

Kesitsel tasarım piyasa geneli hareketi farkla yok ettiği için, kripto
korelasyonu (`FIZIBILITE-UZUN-UFUK`: ~2,5 etkin sembol) **bağlayıcı kısıt
değildir** — o ortak bileşen zaten çıkarılıyor.

### Kestirim

`uc_fark`'ın saatlik sd'si **%1,0 varsayıldı** (sembol başına medyan sd %1,52,
bant başına ~4-5 sembol ortalaması, kesitsel korelasyon varyansı ayrıca düşürür).

```
SE ≈ %1,0 / sqrt(680) = %0,038
görülebilen en küçük etki ≈ 2,8 × SE = %0,107 / saat
```

> **ZORUNLU CÜMLE:** n=~680 bağımsız saat, sd≈%1,0 ile ancak **%0,107** büyüklüğünde
> bir saatlik etkiyi görebiliriz. Uzun-kısa maliyet **%0,26**, ekonomik eşik **%0,50**.
> Saptama tabanı ikisinin de **altında** olduğu için, buradan çıkacak bir "yok"
> hükmü **ekonomik olarak anlamlı büyüklükte yokluğun kanıtıdır** (`basis` ile aynı
> statü). Aradığımız etki %0,107'den küçükse bu test onu bulamaz; o durumda
> "yok" değil **"ölçülemedi"** denir.

### 🔴 KOŞUM ANINDA YENİDEN HESAPLAMA (erken dondurmanın şartı)

`sd(uc_fark)` **varsayım**dır, ölçüm değil — ölçmek bantları kurmak, yani etkiye
bakmak olurdu. Bu yüzden:

1. τ ve `sd(uc_fark)` **koşum anında yeniden hesaplanır**.
2. Gerçekleşen saptama tabanı **%0,26'yı (uzun-kısa maliyet) aşarsa**, nokta
   tahmini ne olursa olsun hüküm **"ÖLÇÜLEMEDİ"**dir.
3. Bağımsız saat sayısı **<200** çıkarsa hüküm **"ÖLÇÜLEMEDİ"**dir.

Bu üç kural **şimdi** yazıldı; koşumda seçilemez.

---

## 6. 🔴 KARAR KURALI — sonucu görmeden

Eşiklerin dayanağı `olcum.py`: gidiş-dönüş %0,13 (TAKER 0,05 × BNB 0,90 +
SLIPPAGE 0,02, iki bacak) · **uzun-kısa %0,26** · ekonomik eşik %0,50 · ρ 0,80.

| Bulgu | Sonraki adım |
|---|---|
| Kontrol kolu ≠ 0 (anlamlı) | 🛑 **Boru hattı bozuk.** Hüküm basılmaz, araç onarılır, yeniden koşulur. |
| Saptama tabanı > %0,26 **veya** bağımsız saat < 200 | **ÖLÇÜLEMEDİ.** "Yok" denmez. |
| GA sıfırı içeriyor **ve** üst sınır < %0,26 | ❌ **ÖLÜ — ekonomik büyüklükte bilgi YOK** (`basis` statüsü, güçlü olumsuz). |
| GA sıfırı içeriyor, üst sınır > %0,26 | ⚠️ **Sonuçsuz** — yön yok ama dışlanamıyor da. |
| `uc_fark` > %0,26, **ama** ρ < 0,80 | ⚠️ **Tek bant eseri** — monotonluk yok, hüküm doğurmaz. |
| `uc_fark` > %0,26 · ρ ≥ 0,80 · permütasyon p < 0,05 · kırpılmış ortalama da geçer · top-3 ve yarı-dönem sağlam | ✅ **Mekaniği ölçmeye değer** → aşağıdaki maliyet tabanı kapısı |
| Yukarıdakini geçer ama **sağlamlık kollarından biri** düşer | ⚠️ **Kırılgan** — hüküm doğurmaz, kayda geçer. |

⚠ Eşiği geçmek **"kârlı"** demek değildir; yalnız *"mekaniği ölçmeye değer"*.

### 🔴 MALİYET TABANI — mekanik aşamasına geçiş şartı (`7910ce7`)

Bu aday **RADAR**'da koşacaktır (geniş stop → ~6 kat ucuz taşıyıcı).

| sicil | `taban_R` |
|---|---|
| RADAR | **0,0279R** |
| ANA SİCİL | 0,1736R |

🔴 **`onkayit_maliyet.py` koşumdan önce YENİDEN KOŞULACAK** ve güncel `taban_R`
kullanılacaktır — yukarıdaki sayı **kopyalanmayacak** (şablon §6 şerhi: eşik
dönem ölçümüdür, stop genişliği rejimle değişir).

⛔ *"Stop'u genişletelim, maliyet düşer"* **yasak**.

---

## 7. 🔴 KARMAŞIKLIK BÜTÇESİ (madde 6.2)

**Bu ölçüm kural doğurabilir** (önceki 18'in aksine, ilk kez iyi güçlendirilmiş
bir kolla). O yüzden emeklilik adayı **şimdi** gösteriliyor:

**Emeklilik adayı: rejim kapısının `min_skor` 70→80 yükseltmesi.**

Gerekçe: bu, canlı sistemdeki **ölçülmemiş bir seçicilik kuralıdır**
(`FIZIBILITE-REJIM-2026-09-07`: yön gerekçesi ölçülemez, n_eff≈4 / 10 epizot).
Derinlik **ölçülmüş** bir seçicilik kuralı doğurursa, ölçülmemiş olan yerini ona
bırakır. İki seçicilik kuralını birlikte taşımak, karmaşıklık bütçesinin
tam olarak yasakladığı şeydir.

⚠ Madde 6 (funding eşiği) **bu bütçeye sayılmaz** — o zaten bağımsız olarak
emekliye ayrılıyor (madde 3.5, `55309bd`), burada ikinci kez sayılamaz.

---

## 8. BEKLENTİ (dürüstlük kaydı — sonuç görülmeden)

**Beklentim: NULL. Güvenim ~%80** (kesin değil, ve bu bilerek yazıldı).

Gerekçeler:
1. **Taban oran 18/18.** Sınanan her aday öldü.
2. **Mikroyapı yazını**, defter dengesizliğinin **saniye-dakika** ölçeğinde
   öngörücü olduğunu, hızla söndüğünü söyler. Biz **1 saatte** ölçüyoruz.
3. **τ = 1,06 saat bunu doğruluyor:** değişkenin kendisi bir saat zor yaşıyor.
   Yordayıcının ömrü ufka eşitse, ufkun sonunda geriye pek bir şey kalmaz.
4. Bu ölçekte 1 saatlik bir kenar varsa **arbitraja uğramış olmalıydı.**

**🔴 Kendime karşı argüman (zayıf değil):**
- Bu, projenin sınadığı **ilk gerçek niyet göstergesi**. Önceki 18'in hepsi
  gerçekleşmiş pozisyonlanmaydı. Farklı bant olduğu için taban oran **aynen
  geçerli değildir**.
- Bu, projenin **en iyi güçlendirilmiş** ölçümü (saptama tabanı %0,107, maliyetin
  yarısından az). Önceki bazı "yok"lar güç yetersizliğinden de olabilirdi;
  buradaki "yok" öyle olmayacak.
- Küçük hacimli semboller arbitraj için pahalıdır; kenar oralarda **yaşayabilir**.
  ⚠ Ama tam da orada işlem maliyeti yüksektir — §6 bunu maliyet eşiğiyle zaten
  cezalandırıyor.

**Beklenti çürürse kayda geçer** (madde 6.3), sessizce düzeltilmez.
`basis`'te ρ beklentim (0,8 bekledim, 0,558 çıktı) ve `giris`'te ters seçilim
beklentim çürümüştü — ikisi de yazıldı.

---

## 9. GEÇERSİZLİK KOŞULLARI

Aşağıdakilerden **herhangi biri** olursa bu ön kayıt geçersizdir ve yeniden
dondurulmadan koşulamaz:

1. 🔴 **`z` ile `getiri` arasındaki herhangi bir ilişki, araç commit'lenmeden
   önce hesaplanırsa** — nokta tahmini, korelasyon, bant ortalaması, grafik dahil.
2. §2'deki tanımlar (τ penceresi 72 sa · ufuk 1 sa · 5 bant · `imb50` seçimi ·
   kesitsel fazla getiri) değişirse.
3. §3'teki sembol **ölçütü** (≥20 gün, ≥300 gözlem, ana 11 dışı) değişirse.
4. §4'teki raporlanacak nicelikler veya §6'daki eşikler değişirse.
5. `derinlik_arsiv.py`'nin 7 sayı biçimi veya `semboller()` mantığı değişirse.
6. 🔴 **Derinliğe dayalı bir kapı koşum öncesi canlıya alınırsa.**
   (Radar-tavan dersi, `afd28b2`: *"yeniden başlatmıyorum" bir üretim kapısı
   değildir.*) Şu an derinliğe bağlı **hiçbir canlı davranış yok** ve koşuma
   kadar eklenmeyecek.
7. Nitelikli sembol **<8** veya kapsama **<20 gün** kalırsa → koşulur ama
   hüküm **"ÖLÇÜLEMEDİ"**dir (§5'in yeniden hesaplama kuralı).

⚠ **Geçersizlik ≠ başarısızlık.** Geçersiz olursa yeni ön kayıt yazılır ve
eskisi **silinmez**, "iptal" damgasıyla durur (`1758a3b` örneği).

---

## 10. ÖLÇÜM

**Araç:** `onkayit_derinlik.py` — **bu commit'ten SONRA yazılır, AYRI commit'lenir.**

- **Salt okur.** `derinlik-arsiv/` ve `olcum.py` dışında hiçbir şeye dokunmaz.
- Canlı sisteme yazmaz, süreç başlatmaz/durdurmaz.
- `olcum.bant_raporu` kullanır — permütasyon hesaplanmadan hüküm satırı basmaz,
  kontrol kolu yoksa uyarır (madde 8.2), altküme testini işaretler (madde 7.8).
- `olcum.TOHUM` (=11) kullanır, kendi tohumunu tanımlamaz.
- Çıktı bu dosyanın **SONUÇ** bölümüne eklenir; **yukarısı değişmez.**

---

# SONUÇ — *(koşumdan sonra buraya eklenir, yukarısı DEĞİŞMEZ)*
