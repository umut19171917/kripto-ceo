# ÖN KAYIT — `skor-yonu`: sıkışma skoru ileri getiriyi TAHMİN mi ediyor, TERS mi?

**Yazım anı:** 2026-08-31 (koşumdan ÖNCE, ilişkiye BAKILMADAN)
**Durum:** DONDURULDU. Kural (§2), örneklem (§3), kill şartları (§4) ve güç
şerhi (§5) bu commit'ten sonra değiştirilmez.
**Yol haritası:** SIRA B / madde **B1** — bekleyen-isler 8.1.

🔴 **BU AN İTİBARIYLA SKOR–GETİRİ İLİŞKİSİ HESAPLANMADI.** Bakılanlar yalnız
*marjinal* dağılımlardı (skor bantlarının payı, getirinin varyansı) ve *boş
hipotez altındaki* yayılım (gün içi etiket karıştırması). İkisi de gerçek
ilişki hakkında bilgi taşımaz — güç hesabı için gereken tam olarak budur.

---

## 1. Neden bu test var

`squeeze_scores()` sistemin **tek pozitif seçicisidir**: hangi kurulumun
"yeterince iyi" olduğuna o karar verir (`SQUEEZE_FLAG = 70`). Ve **hiç
doğrudan ölçülmedi.** Bugüne kadar ölçülen her şey skoru *veri* olarak
kullandı, *sınanacak iddia* olarak değil.

**Dış projede aynı soru soruldu ve cevap TERS çıktı** (2026-08-25, N=50.738):
skorun en yüksek bandı ileri getiride **−%2,015**, monotonluk **ρ=−0,643**,
gün-içi permütasyonda **p=1,0000** (gözlenen değer 2000 permütasyonun
hepsinden daha negatif). Onların botu o skoru **LONG kapısı** olarak
kullanıyordu.

Bizim skorumuz bağımsız yazıldı ama **aynı aileden**: funding + OI + L/S +
seviye yakınlığı — hepsi aynı bandtan (bekleyen-isler 7.4).

**Neden şimdi:** madde 3.3'te ölçüldü ki bileşen soruları **işlem düzeyinde
imkânsız** (0,095R için ~4 yıl). Aynı soru **sinyal düzeyinde** sorulunca güç
sorunu ortadan kalkıyor. Bu test o yolun ilk uygulamasıdır.

---

## 2. Kural (mekanik, yoruma kapalı)

**Sınanan iddia:** *"LS skoru yükseldikçe ileri getiri DÜŞER."*
(LS = long-squeeze = aşağı risk = **SHORT sinyali**. Skor çalışıyorsa yüksek
LS'i düşen fiyat izlemeli.)

**Veri:** `olcucu.log` — sistemin **fiilen hesapladığı** skorlar. Yeniden
kurulum YOK: eşik geçmişi sorunu, ileriye bakma ve yeniden-hesap hatası
bu sayede tamamen dışarıda kalır.

**Seyreltme:** her `(sembol, saat)` kovasından **ilk** gözlem.
⚠ Her N'inci kaydı almak **faz kilitler** — dış projede bir kova örneklemin
%62'sini taşımıştı. Saat kovası 24 saatin hepsini temsil eder.

**İleri getiri:** aynı kaynaktan (log fiyatı), **+24 saat**, ±30 dk tolerans.

**Eşik:** `olcucu.SQUEEZE_FLAG = 70` — 🔴 **İCAT EDİLMEDİ**, sistemin kendi
"bu bir kurulumdur" eşiği. Bant sınırları da tarama ile seçilmedi.

**Çıkarım ölçeği: GÜN.** Karşıtlık **gün içinde** kurulur (aynı gün, aynı
piyasa) → piyasa geneli hareket her iki kolda da aynı olduğu için götürür.
1,57 milyon log satırı **1,57 milyon bağımsız gözlem DEĞİLDİR** (kayıtlar
~36 saniyede bir); etkin ölçek gün sayısıdır.

---

## 3. Örneklem

| | |
|---|---|
| kaynak | `olcucu.log`, 1.568.225 skor satırı, ayrıştırma hatası **0** |
| dönem | 2026-06-27 → 2026-08-30, **65 gün** |
| sembol | 11 (ana sicil evreni) |
| seyreltme sonrası | 14.061 gözlem |
| +24s getirisi eşleşen | **12.913** |
| **BİRİNCİL KOL — LS ≥ 70** | **1.634 gözlem, 64/65 günde** |
| İKİNCİL KOL — SS ≥ 70 | 85 gözlem, 20/65 günde |

---

## 4. KILL ŞARTLARI (şimdi donduruldu — BİRİNCİL KOL: LS)

**Dördü de gerekli.** Eşikler dış projenin S1-S4 setinden **ödünç alındı**
(işaret çevrilerek), bu veriye bakılarak seçilmedi.

| # | Şart | Eşik |
|---|---|---|
| **S1** | Monotonluk: LS bantlarının ortalama getirisi, LS arttıkça **düşmeli** | Spearman **ρ ≤ −0,75** |
| **S2** | İşaret tutarlılığı: günlük karşıtlık beklenen işarette | **≥ %60 gün** |
| **S3** | Şans: gün-içi etiket permütasyonu | **p ≤ 0,05** (2000 tur) |
| **S4** | Yoğunlaşma: en çok katkı veren **3 sembol** çıkarılınca işaret korunmalı | işaret aynı |

**Bantlar (şimdi sabitleniyor):** `[0,20) · [20,40) · [40,60) · [60,80) · [80,100]`
— eşit genişlik, veriye bakılmadan.

### HÜKÜM

- **Dördü de geçer** → *"LS skoru SHORT yönünde bilgi taşıyor"*. ⚠ Kural
  değişikliği **doğurmaz**: bu **ham sinyal** aşamasıdır; mekanik ve portföy
  aşamaları ayrıca gerekir (bekleyen-isler 7.2).
- **Biri bile kalır** → iddia düşer. Kısmi geçiş geçiş değildir.
- 🔴 **İŞARET TERS ÇIKARSA** (ρ ≥ +0,75 ve S2-S4 ters yönde) bu **ayrı ve
  daha ağır bir bulgudur**: skor SHORT sinyali üretirken fiyat YÜKSELİYOR
  demektir. Bu hâlde hüküm *"skor ölü"* değil, ***"skor ters"*** yazılır ve
  `SISTEM.md` §12 madde 1 (*"sıkışma skoru korunacak mı?"*) **doğrudan** bu
  bulguya bağlanır.

### İKİNCİL KOL (SS) — keşifsel, hüküm doğurmaz
n=85 / 20 gün. §5'e göre yalnız **%1,93**'ten büyük farkı görebilir. Ayrı
raporlanır, **kill şartına dahil değildir**, ve tek başına hiçbir karar
gerekçesi olamaz.

---

## 5. 🔴 GÜÇ HESABI (EK 4 zorunluluğu — bu cümle olmadan dondurulamaz)

Boş hipotez altında, gün içi etiket karıştırmasıyla ölçüldü (400 tur):

| kol | null sd | görülebilen fark | katkı veren gün |
|---|---|---|---|
| **LS ≥ 70** | %0,175 | **%0,489** | 64 |
| SS ≥ 70 | %0,690 | %1,933 | 20 |

**Zorunlu cümle:**
> *n=1.634 gözlem / 64 gün, gün-içi karşıtlık kurgusuyla bu test ancak
> **%0,489** büyüklüğünde bir 24 saatlik getiri farkını görebilir. Aradığımız
> etki %0,489'dan küçükse **bu test onu bulamaz.*** Kıyas: dış projede
> gözlenen bant farkı **%2,14** idi — o büyüklükteki bir etki rahatça görünür.
> İkincil kol (SS) **%1,93**'ün altını göremez ve bu yüzden hüküm doğurmaz.

⚠ **Neden gün içi karşıtlık:** gün ortalamalarının sd'si %2,78, ham getirinin
%6,06. Karşıtlık gün içinde kurulunca null sd **%0,175**'e iniyor — piyasa
geneli hareket iki kolda da aynı olduğu için götürüyor. Tasarımın gücü
buradan geliyor, örneklem büyüklüğünden değil.

---

## 6. Beklenti (dürüstlük kaydı — sonuç görülmeden yazıldı)

**Öncül tahminim: S1 KALIR (monotonluk sağlanmaz), ve işaret muhtemelen
TERS çıkar.** Üç dayanak, üçü de ölçülmüş:
1. Dış projede aynı aileden bir skor ters çıktı.
2. Bizim sistemimiz ağırlıkla SHORT üretiyor (103 tahminin 73'ü) ve radar
   SHORT **boğa öncesi bile** kaybediyordu (n=48, −0,378R, GA sıfırı dışlıyor).
3. LS dağılımı SS'e göre çok sıcak (medyan 50 vs 25; ≥70'te 1.634 vs 85) —
   yani bileşenler LS'i kolayca dolduruyor. Kolay dolan bir eşik, ayırt
   etmeyen bir eşiktir (madde 7'nin simetrisizlik bulgusu).

**Ama üçü de dolaylı.** Doğrudan ölçüm yapılmadı; bu yüzden test var.
S2/S3/S4'ün de kalmasını bekliyorum. **Yanılmayı bekliyorum sayılmaz —
tahminim düşerse bu, skorun lehine gerçek bir bulgudur ve öyle yazılır.**

---

## 7. Geçersizlik koşulları (test iptal olur)

- `olcucu.squeeze_scores()` ya da `SQUEEZE_FLAG` koşum öncesi/sırasında değişirse
- `olcucu.log` biçimi değişir ve ayrıştırma bozulursa
- Seyreltme, ufuk (+24s) veya bant sınırları sonuç görüldükten sonra oynatılırsa

---

## 8. Sonuç ne olursa ne yapılır

| Sonuç | Eylem |
|---|---|
| **4/4 geçer** | *"Sinyalde bilgi var"* kaydedilir. Sonraki adım **mekanik aşama** (7.2) — kural değişikliği YOK |
| **Biri kalır** | İddia düşer. Skor "kanıtlanmamış" kalır; bileşen ayarı (3.2/3.3) **anlamsızlaşır** ve o maddeler bu bulguya bağlanır |
| **İşaret TERS** | En ağır sonuç. `SISTEM.md` §12/1 doğrudan bağlanır; **kural değişikliği yine ayrı ön kayıt ister** — ters çıkması "tersine çevir" demek değildir (mekanik ve maliyet aşamaları yapılmadan) |

**Her üç durumda da gerçek para kapısı AÇILMAZ.**
Ve *"eşiği 70 yerine X yapıp yeniden deneyelim"* **YASAKTIR** — eşik taraması
olur ve §2'nin sıfır-serbestlik-derecesi gerekçesini yok eder.

---

## 9. Ölçüm

`onkayit_skor.py` — log'u akıtarak okur, seyreltir, +24s getiriyi eşler,
S1-S4'ü **sırayla** değerlendirir. Salt okurdur. Ön kayıt commit'inden
**sonra** yazılır ve ayrı commit'lenir.
