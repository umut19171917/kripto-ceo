# ÖN KAYIT — `radar-v2`: kanıtlanmış kaybeden koşulların çıkarılması

> **Kayıt anı (dondurulmuş):** `2026-08-18T20:14:04Z`
> **Durum:** AÇIK — veri toplanıyor
> **Bu belge koşmadan ÖNCE yazıldı ve git'e işlendi. Kill şartları sonradan değiştirilemez.**
> Değiştirilirse test geçersizdir; commit geçmişi tanıktır.

---

## 1. Neden bu test var

2026-08-18'de `metrikler.py` ile yapılan istatistiksel sınav şunu gösterdi:

**Kanıtlanmış NEGATİF hücreler** (bootstrap %95 GA sıfırı dışlıyor):

| Hücre | n | işlem başına |
|---|---|---|
| K2 (swing-1h) | 32 | −0,539R |
| radar / DİKKAT | 23 | −0,673R |
| radar / SHORT | 43 | −0,441R |

**Kanıtlanmış POZİTİF hücre: YOK.**

Yani sistem **kaybettireni güvenilir biçimde tespit ediyor, kazandıranı hiç tespit edemiyor.**
Bu asimetri bir strateji önerir: *kazananı bulmaya çalışma, kanıtlanmış kaybedeni ele.*

İki kanıtlanmış kaybeden koşul (DİKKAT, SHORT) radar evreninden çıkarıldığında kalan:

| | n | işlem başına | isabet | PSR |
|---|---|---|---|---|
| radar / ACIK + LONG | 60 | +0,313R | %43 | %95 |

⚠ **Bu bir KANIT DEĞİLDİR.** 21. hipotezdir ve iki post-hoc filtrenin kesişimidir.
~20 kırılıma bakıldığında bir hücrenin bu düzeye ulaşması **şansla beklenen** bir olaydır.
Bonferroni eşiği (0,05/20 = 0,0025) aşılmamıştır. Bu yüzden **yalnızca ön kayıt adayıdır.**

**Mekanizma (uydurma değil, ayrı ölçülmüş):** funding yapısal olarak pozitif → sistem
SHORT üretmeye eğilimli → SHORT, BTC'nin yukarı sürüklenmesine karşı kaybediyor.
"LONG only" rastgele bir dilim değil, **ölçülmüş yapısal bir yanlılığın düzeltmesidir.**
DİKKAT ise yüksek makro riskli pencereleri dışlar — muhafazakâr bir risk kuralıdır,
kenar iddiası değil.

---

## 2. Kural (mekanik, yoruma kapalı)

Kayıt anından **sonra oluşturulan** radar tahminlerinden şu üçünü birden sağlayanlar sayılır:

1. `sicil` = radar (radar-defter.json)
2. `yon` = **LONG**
3. `makro_kapi` = **ACIK** (tahminin OLUŞTURULDUĞU andaki damga)

Ek şart: kanonik evren — `kaynak` ≠ `geri-doldurma`, `sicil` ≠ `deneysel`.
Kapanmış sayılır: `durum` ∈ {tp1, tp2, stop, zaman_asimi}.

**Değişmeyen her şey:** radar eşikleri (%20/24s, %8/30dk, vol≥30M), plan mekaniği
(2,5 ATR stop, R/R 2,08), cooldown, risk tavanı, maliyet modeli.

**CANLI SİSTEME DOKUNULMAZ.** Radar tüm sinyalleri üretmeye devam eder; kural yalnızca
*değerlendirme anında filtre* olarak uygulanır. Kayıt anı veriden önce geldiği için test
gerçek anlamda görülmemiş-veri testidir.

---

## 3. Örneklem

- **Hedef: 30 kapanmış işlem.**
- Beklenen süre: radar 2,97 işlem/gün kapatıyor, uygun oran %53 → ~1,58/gün → **~19 gün**
  (tahmini bitiş ~2026-09-06).
- **30'a ulaşınca DERHAL değerlendirilir.** "Biraz daha veri toplayalım" YASAK —
  örneklemi sonuca göre uzatmak testin kendisini geçersiz kılar.

---

## 4. KILL ŞARTLARI (şimdi donduruldu — beşi de geçmeli)

| # | Şart | Eşik |
|---|---|---|
| 1 | Ortalama net R pozitif **ve** bootstrap %95 GA sıfırı **dışlıyor** | GA alt sınırı > 0 |
| 2 | İsabet başabaşı aşıyor | > %32,5 |
| 3 | PSR (gerçek Sharpe > 0 olasılığı) | ≥ %95 |
| 4 | Yoğunlaşma: en iyi **3** işlem çıkarılınca ortalama hâlâ pozitif | > 0 |
| 5 | İki yarı aynı işarette: ilk 15 ve son 15 işlemin ortalaması ikisi de pozitif | ikisi de > 0 |

**BEŞİ DE geçmeli.** Dördü geçip biri kalırsa **kural ÖLÜR** ve tekrar açılmaz.
Kısmi geçiş, geçiş değildir. (Bu projede F&G tam olarak 4/5 ile düşmüştür.)

---

## 5. Beklenti (dürüstlük kaydı)

Post-hoc hücreler **ortalamaya geri döner.** Gözlenen +0,313R'nin aynen tekrarlanmasını
beklemiyorum. Gerçek bir etki varsa büyüklüğünün belirgin biçimde küçülmesi normaldir;
şartlar bu yüzden büyüklüğe değil **işaret + tutarlılık + yoğunlaşma**ya bakıyor.

Öncül tahminim: **kural düşer.** 21 hipotez sonrası ayakta kalan bir hücrenin ileriye
dönük doğrulamayı geçme olasılığı düşüktür. Bu kayıt, o ihtimali *dürüstçe sınamak* içindir
— doğrulamak için değil.

---

## 6. Geçersizlik koşulları (test iptal olur, başa döner)

- Radar eşikleri (%20/24s, %8/30dk, vol≥30M) veya plan mekaniği koşu sırasında değişirse
- Makro kapı mantığı (`makro.py`) değişirse
- Kanonik süzgeç tanımı değişirse
- 30 işleme ulaşılmadan kill şartlarına dokunulursa

---

## 7. Sonuç ne olursa ne yapılır

| Sonuç | Eylem |
|---|---|
| **5/5 geçer** | Projenin ilk ayakta kalan bulgusu. **Yine de gerçek para YOK** — ikinci ve daha uzun bir doğrulama turu (60+ işlem, iki makro rejim) açılır |
| **Herhangi biri kalır** | Kural ölür, `G — KAPALI` listesine yazılır, tekrar açılmaz. Tahmin ailesi kesin kapanır |

**Her iki durumda da K3 (gerçek para) kapısı bu testle AÇILMAZ.**

---

## 8. Ölçüm

`onkayit_radar.py` — kayıt anını okur, kuralı uygular, 5 şartı sırayla değerlendirir.
Ara koşularda yalnız **sayaç** gösterir (n/30); 30'a ulaşmadan hüküm basmaz — erken
bakıp karar vermeyi engellemek için.

---

## EK — 2026-08-18, kayıttan ~30 dk sonra (KURAL VE KILL ŞARTLARI DEĞİŞMEDİ)

> ⚠ **Bu ek YALNIZCA §1'deki KANIT değerlendirmesini zayıflatır.** Kural (§2), örneklem
> (§3) ve kill şartları (§4) **hiç dokunulmadan** durmaktadır ve dokunulmayacaktır.
> Ön kaydı güçlendirmek için değil, **zayıflığını kayda geçirmek** için yazıldı.

Kullanıcının "bu yöntem analize eklendi mi?" sorusu üzerine hücrelerin bağımsızlığı
kontrol edildi ve iki zayıflık bulundu:

1. **İki eleme bağımsız değil.** `radar/DİKKAT` (n=23) ile `radar/SHORT` (n=43)
   **13 işlemi paylaşıyor** — DİKKAT'in %57'si aynı zamanda SHORT. Yani "iki bağımsız
   kanıtlanmış kaybeden" ifadesi fazla iyimserdi; kısmen tek bulgunun iki adı.

2. **DİKKAT elemesinin artımlı katkısı ince.** SHORT elendikten sonra kalan `radar/LONG`
   n=70, +0,175R, PSR %84. DİKKAT elemesi bunun üzerine yalnız **10 işlem** çıkarıyor
   (ort. −0,653R) ve hücreyi +0,313R / PSR %95'e taşıyor. **Manşet rakamı 10 işleme
   dayanıyor.**

**Etkisi:** §1'deki "kanıt değil, ön kayıt adayı" hükmü **daha da güçlenir**; öncül
tahminim (kural düşer) değişmez, hatta pekişir. Testin değeri aynen sürer — çünkü
testin amacı bu zayıf kanıtı ileriye dönük olarak sınamaktı, güçlü olduğunu iddia etmek
değil.

**Yöntemsel not:** en kötü alt kümeleri çıkarmak, kalanın ortalamasını **her zaman**
yükseltir — bu aritmetiktir, keşif değil. Bu yüzden örneklem-içi +0,313R hiçbir şeyin
kanıtı sayılmaz; yalnız 30 işlemlik ileriye dönük sonuç sayılır.

---

## EK 2 — 2026-08-20: REJİM DEĞİŞTİ (KURAL VE KILL ŞARTLARI YİNE DEĞİŞMEDİ)

> ⚠ **Bu ek de yalnızca YORUM uyarısıdır.** Kural (§2), örneklem (§3) ve kill şartları (§4)
> dokunulmadan duruyor. **Sonuç görülmeden yazıldı** — bilerek, çünkü sonradan yazılsaydı
> her iki yönde de bahane olarak kullanılabilirdi.

**Olay:** Kayıttan ~1,5 gün sonra piyasa sert şekilde yukarı döndü.
Ölçüm (2026-08-20 11:20 UTC): BTC +%11,4/24s (+%13,2/7g), ETH +%19,1/24s (+%21,5/7g),
fiyatlar 30 günlük bandın %91-97'sinde. Son 24 saatte **SHORT likidasyon $356,6M'a karşı
LONG likidasyon $24,8M = 14,4:1** → ralli **kısa kapatmayla** beslendi. ETH ve SOL'de açık
pozisyon DÜŞERKEN fiyat yükseldi (−%3,5 / −%8,8) = pozisyon kapanışı, yeni talep değil.
Funding üç majörde de tavanda (%0,0100, kendi son 500 ödemesinin **100. persentili**).
Sistemin rejim etiketi: trend **BOĞA** (önceki 540 günlük ölçüm penceresinin tamamı
düşen/testereydi — BTC o pencerede −%34,5).

**Testi neden etkiler:** Kural **"yalnız LONG"**. Test artık büyük ölçüde bir BOĞA
rejiminde koşacak. LONG kuralının boğada iyi görünmesi **beklenen** bir şeydir ve kuralın
kendisiyle ilgili bilgi taşımayabilir.

**Bağlayıcı yorum kuralı (şimdi sabitleniyor):**

1. **Kural 5/5 geçerse** → tek başına "bulgu doğrulandı" DENMEZ. Zorunlu ek adım:
   sonucun rejim kırılımı yazılır (örneklem içindeki BOĞA/AYI günleri ayrılır) ve
   ikinci doğrulama turu **mutlaka farklı bir rejimi** kapsayacak şekilde açılır.
   §7'deki "60+ işlem, iki makro rejim" şartı bu yüzden zaten yazılıydı; burada
   **zorunlu** hale gelir.
2. **Kural kalırsa** → "rejim kötüydü / şanssızdık" BAHANESİ KULLANILAMAZ. Aksine:
   LONG kuralı kendi lehine olan bir rejimde bile geçemediyse, hüküm **daha da ağırdır.**

**Not:** Bu rejim değişimi projenin başka bir açık maddesi için İYİ HABER — `D1`
(likidasyon fade'inin ileriye dönük doğrulaması) aylardır ikinci bir rejim bekliyordu.

---

## EK 3 — 2026-08-23: HÜKMÜN REJİM ŞERHİ (KURAL VE KILL ŞARTLARI YİNE DEĞİŞMEDİ)

> ⚠ **Bu ek de yalnızca YORUM şerhidir.** Kural (§2), örneklem (§3) ve kill şartları (§4)
> dokunulmadan duruyor. **Sonuç görülmeden yazıldı.** Şerhi yazarken örneklemin yalnızca
> **tarih ve damga metaverisine** bakıldı; hiçbir işlemin `sonuc_R`'sine BAKILMADI —
> ara sonuca bakma yasağı (§8) korundu.

**Kullanıcının 2026-08-23'te koyduğu şerh, aynen:**

> *"Koşan ön kayıt 18 Ağustos'ta açıldı, boğa 20'sinde başladı. Yani test neredeyse
> tamamen boğada tamamlanacak ve test edilen kural 'ACIK + LONG'. Geçerse bunun
> filtreden mi rejimden mi geldiğini ayıramayacağız."*

**Şerh haklıdır ve EK 2'nin söylediğinden daha ağırdır.** EK 2 (20 Ağu) "test artık
büyük ölçüde bir BOĞA rejiminde koşacak" demişti — o an bu bir öngörüydü. Bugün ölçüldü:

| Örneklem bileşimi (12/30) | |
|---|---|
| Boğa döneminde (≥20 Ağu) oluşturulan | **11 / 12** |
| Boğa öncesi oluşturulan | 1 / 12 |
| Rejim damgası SAKIN | 12 / 12 (OYNAK: 0) |
| Makro damgası ACIK | 12 / 12 |

Kalan 18 işlem aynı rejimde gelirse hüküm **fiilen %100 boğa örneklemiyle** verilecek.

**🔴 İKİNCİ VE DAHA CİDDİ SORUN — kuralın ACIK bacağı sınanmıyor.**
Kayıttan beri üretilen 103 radar tahmininin **95'i ACIK, yalnız 8'i DİKKAT** damgalı.
Yani DİKKAT süzgeci örneklemin ~%8'ini eliyor. Oysa EK 1'de kaydedildiği gibi, özgün
analizde **manşet rakamı tam olarak DİKKAT elemesine dayanıyordu** (10 işlem çıkarıyor,
PSR'yi %84 → %95 taşıyan o 10 işlem). Bu koşuda o bacak neredeyse hiç iş yapmıyor.

**Sonuç: bu test ne söylerse söylesin, hükmü "ACIK + LONG" kuralı hakkında değil,
pratikte "LONG" hakkında olacaktır.**

### Bağlayıcı yorum kuralı — EK 2'nin 1. maddesine EKLENİR (şimdi sabitleniyor)

3. **Kural 5/5 geçerse, hüküm şu cümleyle kayda geçer ve başka türlü yazılamaz:**
   *"Kural, boğa rejiminde ve makro kapının sürekli ACIK olduğu bir pencerede geçti;
   diğer rejimde ve kapının fiilen ayrım yaptığı bir pencerede SINANMADI."*
   Boğadaki bir LONG kuralının geçmesi ile rejimin kendisi ayrıştırılamaz — bu örneklemle
   ayrıştırma **imkânsızdır**, sonradan yapılacak hiçbir alt-kırılım bunu düzeltmez.
   §7'deki ikinci tur (60+ işlem, iki makro rejim) bu yüzden **şart değil, zorunluluktur**
   ve ikinci tur **ayı/testere rejimini kapsamadan kapanamaz.**
4. **Kural kalırsa** EK 2'nin 2. maddesi aynen geçerli: "rejim kötüydü" bahanesi
   kullanılamaz, hüküm daha da ağırdır.

**Not (yöntem):** Bu şerh testin değerini düşürmez, **hükmün kapsamını daraltır.**
Test hâlâ koşmaya değer — çünkü asıl işlevi, zayıf bir post-hoc hücrenin ileriye dönük
olarak sınanmasıdır. Değişen şey, geçtiği takdirde ne kadar şey iddia edebileceğimizdir.

---

## EK 4 — 2026-08-24: TESTİN İSTATİSTİKSEL GÜCÜ (KURAL VE KILL ŞARTLARI YİNE DEĞİŞMEDİ)

> ⚠ **Bu ek de yalnızca YORUM şerhidir.** Kural (§2), örneklem (§3) ve kill şartları (§4)
> dokunulmadan duruyor. **Sonuç görülmeden yazıldı** — 14/30'da, hiçbir ara sonuca
> bakılmadan. Şerhi yazarken yalnızca *dağılımın genişliği* kullanıldı; koşan testin
> kendi işlemlerinin R'lerine BAKILMADI.
>
> **Bu ek bir MAZERET DEĞİLDİR.** Aşağıdaki 5. madde, onu mazeret olarak kullanmayı
> açıkça yasaklar. Erken yazılmasının sebebi tam olarak budur: sonradan yazılsaydı
> mazerete dönüşürdü.

### Neden yazıldı

Testin **istatistiksel gücü hiç hesaplanmamıştı.** Ön kayıt yazılırken "30 işlem"
hedefi konuldu ama *"30 işlem ne büyüklükte bir etkiyi görebilir?"* sorusu sorulmadı.
2026-08-24'te soruldu ve cevap testin kapsamını daraltıyor.

### Ölçüm

Net R'nin standart sapması, testin evrenine en yakın geçmiş kümeden (radar LONG+ACIK,
n=76): **sd = 1,545**. Buradan n=30 için:

- standart hata = 1,545 / √30 = **0,282**
- **1. kill şartının** (bootstrap %95 GA alt sınırı > 0) geçmesi için gözlenen
  ortalamanın **+0,553R/işlem**'i aşması gerekir
- Bu, ana sicil sıklığında kabaca **yılda %252** demektir

**Gerçek etki şu büyüklükteyse, 1. şartı geçme olasılığı:**

| Gerçek edge | Geçme olasılığı |
|---|---|
| +0,05R | %3,7 |
| +0,10R | %5,4 |
| +0,15R | %7,7 |
| +0,20R | %10,6 |
| **+0,313R** ← §1'de gözlenen hücrenin kendi değeri | **%19,8** |
| +0,40R | %29,4 |
| +0,55R | %49,6 |

⚠ Bunlar **yalnız 1. şart** içindir. §4 **beş şartın BEŞİNİ birden** ister (isabet,
PSR ≥ %95, yoğunlaşma, iki yarı). Dolayısıyla gerçek geçme olasılığı bu tablodakinden
**daha düşüktür**; tablo bir ÜST SINIRDIR.

### Bunun anlamı

**Test, "edge var mı?" sorusunu değil, "DEVASA bir edge var mı?" sorusunu soruyor.**

En çarpıcı satır sonuncusundan biri: §1'de gözlenen **+0,313R** hücresi *tamamen
gerçek olsa ve aynen sürse bile*, bu test onu ancak **beşte bir** ihtimalle
doğrulayabilir. Yani testin başarısızlığı, hipotezin yanlışlığından çok testin
küçüklüğünden kaynaklanabilir.

### Bağlayıcı yorum kuralı — EK 3'ün 3. ve 4. maddelerine EKLENİR

5. **Kural KALIRSA (beklenen sonuç), hüküm şu iki cümleyle birlikte kaydedilir ve
   ayrılamaz:**
   - *"Kural, §4'ün beş şartını geçemedi ve §7 gereği ölmüştür."* — **bu aynen geçerlidir.**
     Bu şerh kuralı DİRİLTMEZ, `G — KAPALI` listesine yazılmasını engellemez.
   - *"Testin gücü, gözlenen dağılımla +0,553R/işlem'dir; bu başarısızlık 'edge yoktur'
     değil, 'DEVASA edge gösterilememiştir' anlamına gelir."*

   ⛔ **Bu şerh, EK 2 madde 2'yi geçersiz kılmaz.** "Rejim kötüydü / şanssızdık"
   bahanesi hâlâ **YASAK**. Ve "test zayıftı, o yüzden kuralı tekrar açalım" da
   **YASAK** — kural §7'ye göre ölür ve tekrar açılmaz. Şerhin izin verdiği tek şey,
   hükmün KAPSAMINI doğru yazmaktır: ölen şey *"büyük edge iddiası"*dır, *"edge
   ihtimali"* değil.

6. **Kural GEÇERSE**, düşük güç hükmü **güçlendirmez, aksine daraltır**: %20'lik bir
   pencereden geçmiş olmak, etkinin gerçekten +0,553R olduğunu değil, gözlenen
   ortalamanın o eşiği aştığını gösterir. Post-hoc hücrelerin ortalamaya geri döndüğü
   (§5) hatırlanmalı; ikinci tur (EK 3 madde 3) **zaten zorunluydu, öyle kalır.**

### 🔴 YÖNTEM DERSİ (arşive geçer)

**Ön kayıt yazılırken güç hesabı yapılmadı.** "30 işlem" sayısı, ne kadar sürede
toplanacağına göre seçildi — ne göreceğine göre değil. Bu, ön kaydın kendisinin bir
tasarım kusurudur ve bu projede ilk kez tespit ediliyor.

**Bundan sonraki her ön kayıt, örneklem büyüklüğünü kill şartıyla birlikte
gerekçelendirmek zorundadır:** *"n=X, sd=Y varsayımıyla ancak Z büyüklüğünde bir
etkiyi görebilir; aradığımız etki Z'den küçükse bu test onu bulamaz."*

Bu cümle yazılmadan hiçbir ön kayıt dondurulmamalıdır.

---

## SONUÇ — 2026-08-30: **KURAL ÖLDÜ (1/5)**

> ⚠ **Kural (§2), örneklem (§3) ve kill şartları (§4) bu bölüm yazılırken de DEĞİŞMEDİ.**
> Bu bölüm testin çıktısıdır, sözleşmenin değişikliği değil. Ek 1-4 gibi **eklemedir**;
> yukarıdaki hiçbir satır silinmedi.

**Örneklem doldu:** 30/30 kapanmış işlem. Girişler 2026-08-19 19:28 → 2026-08-27 09:42,
son kapanış 2026-08-28 16:13. Ölçüm `onkayit_radar.py`, 2026-08-30'da koşuldu.

```
toplam net -1.20R | islem basina -0.040R | isabet %33.3

KALDI  1. ort>0 VE bootstrap GA sifiri disliyor   ort -0.040 | GA[-0.504,+0.474]
GECTI  2. isabet basabasi asiyor                  %33.3 vs %32.5
KALDI  3. PSR >= %95                              %44.1
KALDI  4. en iyi 3 cikinca hala pozitif           -0.040 -> -0.274
KALDI  5. iki yari da pozitif                     ilk 15 +0.419 | son 15 -0.499
```

**Örneklemin bileşimi (ham sayım, `uygun_islemler()` ile aynı tanım):**

| | |
|---|---|
| kapanış biçimi | **stop 20** · tp1 9 · zaman aşımı 1 |
| kazanan / kaybeden | 10 / 20 |
| en iyi 3 işlem | üçü de **+2,08R** (hedefin kendisi) |
| en kötü 3 işlem | üçü de **−1,00R** (temiz stop) |
| `makro_kapi` | 30/30 **ACIK** — kapı örneklem boyunca hiç ayrım yapmadı |
| `rejim_durum` | 30/30 **SAKIN** |

### Hüküm — EK 4 madde 5 gereği, iki cümle AYRILAMAZ

1. **"Kural, §4'ün beş şartını geçemedi ve §7 gereği ölmüştür."**
2. **"Testin gücü, gözlenen dağılımla +0,553R/işlem'dir; bu başarısızlık 'edge yoktur'
   değil, 'DEVASA edge gösterilememiştir' anlamına gelir."**

⛔ İkinci cümle kuralı **diriltmez**. §7 uygulanır: `G — KAPALI` listesine yazılır,
**tekrar açılmaz**, tahmin ailesi kesin kapanır. "Test zayıftı, yeniden açalım" **YASAK**
(EK 4 madde 5). Ölen şey *"büyük edge iddiası"*dır, *"edge ihtimali"* değil.

### EK 2 madde 2 — bahane yolu kapalı, hüküm daha ağır

*"Rejim kötüydü / şanssızdık"* bahanesi **kullanılamaz.** Ve bu vakada zaten
kullanılamazdı: kural **yalnız LONG** açıyor ve test, LONG için elverişli bir dönemde koştu.

⚠ **Dürüstlük şerhi — bu cümle defterden DEĞİL fiyattan kuruluyor.** Radar defteri
boğa/ayı damgası taşımıyor; `rejim_durum` alanı oynaklık durumunu (SAKIN/OYNAK) ölçer,
trendi değil. Dolayısıyla "örneklemin %X'i boğadaydı" diye bir sayım **yapılamaz**.
Söylenebilecek olan, **pencerenin kendisinin ölçümüdür** (BTCUSDT günlük,
`fapi/v1/klines`, 2026-08-30'da çekildi):

| | |
|---|---|
| BTC, 18 Ağu açılış → 28 Ağu kapanış | **+%22,5** |
| yükselen gün | 11 günün **8'i** |
| en sert üç gün | 19 Ağu **+%7,1** · 20 Ağu **+%5,3** · 21 Ağu **+%7,3** |

30 girişin **29'u** 20 Ağustos ve sonrasında açıldı; `rejim.json → trend` alanı
**boğa** okuyordu (EK 2'de 2026-08-20'de ölçülmüştü, bugün de aynı).

**Sonuç:** LONG kuralı, kendi lehine olan bir rejimde bile geçemedi → EK 2 madde 2 gereği
hüküm **daha da ağırdır.**

### 5. şart en çok şeyi söylüyor

İlk 15 işlem **+0,419R**, son 15 işlem **−0,499R**. Kural yarı yolda kazanıyordu.
Ön kaydın varlık sebebi tam olarak budur: 15. işlemde durup *"tuttu"* deseydik, ortalamaya
geri dönüşü (§5'te önceden yazılmıştı) kendi lehimize yorumlamış olacaktık.

4. şart aynı şeyi başka yerden söylüyor: artının tamamı üç adet hedef vuruşundan geliyor;
onlar çıkınca ortalama **−0,274R**'ye düşüyor.

### Öncül tahmin tuttu

§5'te *"öncül tahminim: kural düşer"* yazılıydı ve **düştü.** Bu, kaydın kendisini
doğrular: sonuç sürpriz değil, sınav dürüsttü.

### §7 gereği yapılanlar

- Kural `G — KAPALI` listesine yazıldı (hafıza: `bekleyen-isler-defteri.md`).
- Tahmin ailesi kapandı — **artık 15 aday / 0 hayatta kalan.**
- **K3 (gerçek para) bu testle AÇILMADI** (§7, her iki sonuçta da geçerliydi).
- Dondurulmuş dönem bitti; `radar.py`/`defter.py` üzerindeki çalışma yasağı kalktı.
