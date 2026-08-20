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
