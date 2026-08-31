# ÖN KAYIT — `radar-tavan`: korelasyonlu yığılma freni düşüşü azaltıyor mu?

**Yazım anı:** 2026-08-30 (koşumdan ÖNCE, sonuç görülmeden)
**Durum:** DONDURULDU. Kural (§2), örneklem (§3), kill şartları (§4) ve güç
şerhi (§5) bu commit'ten sonra değiştirilmez.
**Önceki ön kayıt:** `ON-KAYIT-radar-v2.md` — 2026-08-30'da **1/5 ile kapandı**
(kural öldü). Bu belge onun yöntem dersini uygulamak zorundadır (§5).

---

## 1. Neden bu test var

`SISTEM.md` §12/8 (2026-08-23 denetimi): radar sicilinde **risk tavanı da
cooldown da yok**. Ana sicilde ikisi de var (`defter.RISK_TAVANI_PCT = 2.0`,
`defter.COOLDOWN_SAAT = 12`).

**Ölçülen sorun:** radar tepe noktada **10 açık pozisyon**, **7'si aynı yönde**.
Coinler arası korelasyon **0,69**. O yedi pozisyon yedi ayrı bahis değil,
**tek bahsin yedi kopyasıdır.**

**Bu testin sorusu ŞU DEĞİL:** *"tavan daha çok kazandırır mı?"*
**Sorusu şudur:** *"tavan, DÜŞÜŞ yoğunlaşmasını azaltıyor mu?"*
Bir korelasyon freninin işi getiriyi artırmak değil, aynı getiriyi daha az
acıyla almaktır. Kıstasımız da bunu söylüyor (TASARIM-BOT G4: *"maliyetten
sonra, DAHA AZ DÜŞÜŞLE, al-tutmayı geçmek"*).

---

## 2. Kural (mekanik, yoruma kapalı)

Bir radar kurulumu, `radar_defter.kaydet()` çağrılmadan **önce** iki kapıdan geçer:

```
(a) COOLDOWN : ayni coine (token) son `defter.COOLDOWN_SAAT` saat icinde
               KABUL EDILMIS bir kayit varsa  -> RED
(b) TAVAN    : o an ACIK olan AYNI YONDEKI kabullerin toplam riski
               + olcucu.RISK_PCT > defter.RISK_TAVANI_PCT  -> RED
```

🔴 **EŞİK İCAT EDİLMEDİ — sıfır serbestlik derecesi.** Üç sayının üçü de
sistemde **zaten yürürlükte** olan ana sicil değerleridir:
`COOLDOWN_SAAT = 12` · `RISK_TAVANI_PCT = 2.0` · `RISK_PCT = 1.0`.
Hiçbir tarama yapılmadı, "en iyi tavan" aranmadı. Radar'a özel bir sayı
uydurmak *"en iyi hücre seçilmez"* kuralının ihlali olurdu.

**Radar kayıtlarında `risk_pct` alanı yoktur** (459/459). `defter.acik_risk_pct`
ile aynı varsayım kullanılır: **1.0**. Sonucu: tavan fiilen **yön başına
2 açık pozisyon** demektir.

**Kod:** `radar.py`, `radar_defter.kaydet()` çağrısından önce. Yazıldı, derleniyor.

---

## 3. Örneklem — ve testin koştuğu biçim

🔴 **RADAR'IN DAVRANIŞI TEST BOYUNCA DEĞİŞMEZ.** Kapı `radar.py`'de yazılı
ama **devrede değildir**; radar her kurulumu bugünkü gibi kaydetmeye devam eder.

**Neden böyle:** kapı, kabul edilmiş kümenin **deterministik fonksiyonudur** —
tam kayıttan **birebir simüle edilebilir**. Yani iki kolu da gözlemek için
davranışı değiştirmeye gerek yok:

| kol | tanım |
|---|---|
| **A (kabul)** | kapı uygulansaydı kaydedilecek olanlar |
| **B (red)** | kapının eleyecekleri — **ama gerçekte kaydedildi, sonucu biliniyor** |
| **A∪B** | bugünkü davranış (kapısız) |

**Kazanç:** (a) canlı sisteme hiç dokunulmaz, test riski sıfır; (b) B kolunun
sonucu **varsayım değil ölçüm** — gölge defter yazmaya gerek yok; (c) kapı
açılırsa geri alınacak bir şey olmaz.

**Örneklem:** ön kaydın commit'inden **SONRA** oluşturulmuş radar kayıtları.
Bu tarihten önceki 459 kayıt **kullanılmaz** (onlar üzerinde 2026-08-30'da
keşifsel bir geriye oynatma yapıldı — o örneklem içidir ve hüküm doğurmaz).

**Bitiş:** **72 KABUL (A kolu) veya 30 gün** — hangisi önce.
Gerekçe §5'te (güç hesabı). Gözlenen üretim hızı 9,0 kayıt/gün ve kabul oranı
~%27 → ~2,4 kabul/gün → 72 kabul ≈ 30 gün. İki ölçüt de aynı yeri gösteriyor.

---

## 4. KILL ŞARTLARI (şimdi donduruldu)

Getiriler %1 risk ile bileşiklenir (`panel._bilesik` ile aynı yöntem, 1000 $).

### BİRİNCİL — düşüş (kapının ASIL amacı)

| # | Şart | Eşik |
|---|---|---|
| **P1** | A yolunun en derin düşüşü, A∪B yolununkinden **küçük** | yön; büyüklük şartı YOK |
| **P2** | Pencere **6 eşit zaman bloğuna** bölünür; her blokta `dd(A) < dd(A∪B)` | **6/6** |

**P2 neden 6/6:** yazı-tura altında P(6/6) = 1/64 = **0,016**. 5/6 kabul
edilseydi p = 0,109 olurdu — anlamlılık iddia edilemezdi. Blok sayısı da
sonuca bakılarak seçilmedi: 6, p<0,05 veren **en küçük** bölünmedir.

### İKİNCİL — getiri güvenlik freni

| # | Şart | Eşik |
|---|---|---|
| **G1** | `ort(A) − ort(B)` bootstrap GA95'i, A'nın **anlamlı biçimde kötü** olduğunu göstermemeli | GA95 üst sınırı > 0 |

⚠ **G1 bir doğrulama DEĞİL, yalnızca felaket freni.** §5'e göre bu test
0,5R'den küçük hiçbir getiri farkını göremez. G1'in geçmesi *"getiri
bozulmadı"* demek DEĞİLDİR; *"bozulduğunu gösteremedik"* demektir.

### HÜKÜM

**P1 ve P2'nin İKİSİ de geçmeli, VE G1 kalmamalı.** Biri bile düşerse kapı
açılmaz ve `G — KAPALI`'ya yazılır. Kısmi geçiş geçiş değildir.

⚠ **Alt-küme tuzağı (madde 7.8):** A, A∪B'nin **alt kümesidir** → aralarında
eşleşmiş fark yoktur ve t hesaplanamaz. Bu yüzden getiri karşılaştırması
**A ile B arasında** (ayrık kümeler, iki-örneklemli) yapılır, A ile A∪B
arasında değil. Düşüş karşılaştırması ise **yol istatistiğidir**, ortalama
değildir; alt-küme sorunu ona işlemez.

---

## 5. 🔴 GÜÇ HESABI — EK 4'ün bıraktığı ZORUNLULUK

`ON-KAYIT-radar-v2.md` → EK 4 → *"Bundan sonraki her ön kayıt, örneklem
büyüklüğünü kill şartıyla birlikte gerekçelendirmek zorundadır… Bu cümle
yazılmadan hiçbir ön kayıt dondurulmamalıdır."* Aşağısı o cümledir.

**Girdi (radar sicilinin gözlenen dağılımı, N=184 kapanmış):**
ortalama **−0,072R** · standart sapma **1,377R** · üretim **9,0 kayıt/gün**.

**İki-örneklemli testin görebileceği en küçük fark** (güç %80, α=0,05):

| gün | nA | nB | görülebilir fark |
|---|---|---|---|
| 14 | 34 | 91 | 0,775R |
| 21 | 51 | 137 | 0,632R |
| **30** | **72** | **196** | **0,531R** |
| 60 | 145 | 392 | 0,375R |
| 90 | 217 | 588 | 0,306R |

**Zorunlu cümle:**
> *n=72/196, sd=1,377 varsayımıyla bu test ancak **0,531R** büyüklüğünde bir
> getiri farkını görebilir. Aradığımız etki 0,531R'den küçükse **bu test onu
> bulamaz.*** Gürültü tabanı 0,03R olduğuna göre, getiri ekseni bu örneklemle
> **fiilen ölçülemezdir** — 90 güne çıksak bile 0,306R'de kalır.

🔴 **TASARIMI DEĞİŞTİREN SONUÇ:** getiri **birincil ölçüt OLAMAZ.** Yazsaydık,
radar-v2'nin hatasını tekrarlardık: göremeyeceğimiz bir şeyi ölçüt yapmak.
Birincil ölçüt bu yüzden **düşüş**tür — yol istatistiği olduğu için ortalamanın
güç sınırına tabi değildir ve zaten kapının amacı odur.

⚠ **Düşüş tarafının kendi sınırı:** P1/P2 **işaret** testleridir, büyüklük
iddia etmezler. "Düşüş %36 azaldı" gibi bir cümle bu testten **çıkmaz**.

---

## 6. Beklenti (dürüstlük kaydı — sonuç görülmeden yazıldı)

**Keşifsel geriye oynatma (2026-08-30, örneklem içi, N=459):**
kabul %27 · düşüş **−%15,4** (kapılı) vs **−%24,2** (kapısız) · bakiye
863,98 $ vs 861,42 $ · ort R farkı −0,261R, **GA95 [−0,662, +0,158] → gürültü**.

**Öncül tahminim: P1 GEÇER, P2 SINIRDA.** Düşüş yönünün korunmasını
bekliyorum (mekanizma gerçek: aynı yönde 2'den fazla pozisyon tutmayınca
korelasyonlu dip daha sığ olur). Ama 6/6 blok şartı katıdır ve az işlemli
bloklarda düşüş gürültülüdür — **P2'de kalmasını şaşırtıcı bulmam.**
G1'in geçmesini bekliyorum, ama §5 gereği bu **bilgi taşımaz**.

⚠ Yukarıdaki −%15,4 / −%24,2 rakamları **örneklem içidir ve tekrarlanmalarını
beklemiyorum.** Ölçütler bu yüzden büyüklüğe değil **işarete** bakıyor.

---

## 7. Geçersizlik koşulları (test iptal olur, başa döner)

- `defter.COOLDOWN_SAAT`, `defter.RISK_TAVANI_PCT` veya `olcucu.RISK_PCT`
  koşu sırasında değişirse
- Radar eşikleri / plan mekaniği / `radar_defter.kaydet` mantığı değişirse
- Kapı test bitmeden **canlıya alınırsa** (A kolu gözlemlenemez hâle gelir)
- 72 kabule ulaşılmadan kill şartlarına dokunulursa

---

## 8. Sonuç ne olursa ne yapılır

| Sonuç | Eylem |
|---|---|
| **P1+P2 geçer, G1 kalmaz** | Kapı `radar.py`'de **açılır** (radar yeniden başlatılır). Hüküm yazılırken §5'in güç şerhi ve P1/P2'nin *işaret testi* olduğu **birlikte** kaydedilir |
| **Herhangi biri kalır** | Kapı açılmaz, `G — KAPALI`'ya yazılır. *"Ölçüm zayıftı, yine de açalım"* **YASAK** |

**Her iki durumda da:** bu test **gerçek para kapısını AÇMAZ.**
Ve *"tavanı gevşetip yeniden deneyelim"* **YASAKTIR** — o bir eşik taraması
olur ve §2'nin sıfır-serbestlik-derecesi gerekçesini yok eder.

---

## 9. Ölçüm

`onkayit_tavan.py` — ön kayıt commit'inden sonraki radar kayıtlarını okur,
kapıyı simüle eder, A ve B kollarını ayırır, P1/P2/G1'i **sırayla** değerlendirir.
Ara koşularda yalnız **sayaç** gösterir (n/72); 72'ye ulaşmadan hüküm basmaz —
erken bakıp karar vermeyi engellemek için (radar-v2'de bu kural **fiilen işe
yaradı**: kural ilk 15 işlemde kazanıyordu, sonunda düştü).

---

# 🔴 1. KURULUM İPTAL — §7 gereği (2026-08-31)

## Ne oldu

Kapı **canlıya girdi.** §3'ün *"kapı `radar.py`'de yazılı ama devrede
değildir"* şartı ihlal edildi; §7'nin *"Kapı test bitmeden canlıya alınırsa
(A kolu gözlemlenemez hâle gelir)"* koşulu tetiklendi.

**Kanıt (yorum değil, günlüğün kendisi):**
```
[2026-08-30T21:24:07] [BASLA] radar ...            <- yeniden baslatma
[2026-08-30T23:28:25] [RADAR-TAVAN] SKRUSDT LONG atlandi: ...  <- kapi SUZUYOR
```

## Neden oldu — varsayım hatası

Kod 2026-08-30'da commit'lenirken *"radar.py'yi yeniden başlatmıyorum, o yüzden
canlıya girmez"* diye kayda geçmişti. **Bu bir üretim kapısı değilmiş.**
Radar 3 günde **5 kez** yeniden başladı; zamanlanmış görev yok, yani yeniden
başlatma anı denetimimiz dışında (makine ya da kullanıcı).

**Ders:** *"Yeniden başlatmıyorum" bir bayrak değildir.* Commit'lenen kod, süreç
bir sonraki kez kalktığında canlıya girer. Kapatmak isteniyorsa **koda bayrak**
konmalı. Yapıldı: `radar.TAVAN_CANLI = False` (`afd28b2`).

## Hasar

- **19 aday** kapıdan atıldı → B kolu olacaklardı, deftere hiç girmediler, **kalıcı kayıp**
- A kolunda **0 kayıt** — örneklem hiç başlamadı
- Defter **29 saat** boyunca hiç büyümedi (ölçüm tabanı durdu)

## Yan bulgu (iptalden bağımsız, ölçülmüş)

Kapı canlıyken **her iki yönü birden tıkadı:** LONG 3 açık = %3,0 ·
SHORT 4 açık = %4,0 · tavan %2,0. Kayıt başına %1 riskle %2 tavan, yön başına
**en fazla 2 açık kayıt** demektir — 50 coinlik bir evrende.

⚠ Bu, kill şartlarına **dokunmaz** ve hiçbir eşiği değiştirmez. Ama §3'ün
varsaydığı **%27 kabul oranını** riske sokar: gerçek oran çok daha düşükse
72 kabul 30 günde dolmaz, "30 gün" ölçütü bağlar ve **güç §5'in verdiğinden
de düşük** olur. Hüküm yazılırken bu şerh **birlikte** yazılacaktır.

---

# 2. KURULUM — yeniden donduruldu (2026-08-31)

**Değişen tek şey `KAYIT_ANI`'dır.** §2 kural · §4 kill şartları · §5 güç
hesabı · §6 beklenti · §7 geçersizlik · §8 sonuç eylemleri **aynen geçerlidir**
ve **değiştirilmemiştir**. Meşruiyeti: 1. kurulumda **hiçbir sonuç
görülmedi** (A=0, B=0), dolayısıyla ölçütler kirlenmedi.

| | değer |
|---|---|
| yeni `KAYIT_ANI` | **2026-08-31T19:33:13+00:00** (radar'ın tavansız kalktığı an) |
| kapı durumu | `radar.TAVAN_CANLI = False` — **devrede DEĞİL**, simülasyonda uygulanır |
| örneklem | bu andan SONRA oluşan radar kayıtları; öncesi **kullanılmaz** |
| bitiş | 72 kabul **veya** 30 gün — hangisi önce |

🔴 **`TAVAN_CANLI`'yı `True` yapmak bu ön kaydı İKİNCİ kez geçersiz kılar.**
