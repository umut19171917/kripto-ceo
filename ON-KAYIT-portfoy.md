# ÖN KAYIT — `portfoy`: bu sinyal ailesi bir KASADA ne yapardı?

**Yazım anı:** 2026-08-31 (koşumdan ÖNCE, hiçbir kasa eğrisi hesaplanmadan)
**Durum:** DONDURULDU. Kurallar (§2), örneklem (§3), nicelikler (§4) ve
sınır şerhi (§5) bu commit'ten sonra değiştirilmez.
**Yol haritası:** SIRA B / **3. ve son aşama** (*ham → mekanik → portföy*).
**Öncülleri:** `ON-KAYIT-skor-yonu.md` (ham: ρ=+1,000, `b01d493`) ·
`ON-KAYIT-mekanik.md` (mekanik: −0,327R/işlem, `be56b77`).

🔴 **BU AN İTİBARIYLA HİÇBİR KASA EĞRİSİ HESAPLANMADI.** Bakılan tek şey
*sayım*dı: risk tavanı 456 sinyalin **%80,7'sini** reddediyor, tepe eşzamanlı
2. Hiçbir bakiye, düşüş ya da kıyas hesaplanmadı.

---

## 1. Neden bu aşama var

B2 **işlem başına** ölçtü: −0,327R. Ama bir kasa işlem başına yaşamaz —
eşzamanlı maruziyet, korelasyon, bileşiklenme ve **düşüş** ancak portföy
düzeyinde görünür. Projenin kendi kıstası da (TASARIM-BOT **G4**) portföy
diliyle yazılı:

> *"maliyetten sonra, DAHA AZ DÜŞÜŞLE, al-tutmayı geçmek"*

Bu aşama o cümleyi ilk kez bu sinyal ailesine uyguluyor.

---

## 2. Kurallar (sistemin KENDİ sabitleri — hiçbiri icat edilmedi)

| | değer | kaynak |
|---|---|---|
| işlem başına risk | **%1** (güncel bakiyenin) | `olcucu.RISK_PCT` |
| aynı yön risk tavanı | **%2** → en fazla **2 eşzamanlı** | `defter.RISK_TAVANI_PCT` |
| tavan `beklemede`yi de sayar | evet | `defter.py:57` (bekleyen-emir semantiği) |
| slot ömrü | sinyalden çözüme; tetiklenmezse **24s** sonra boşalır | `defter.PENDING_SAAT` |
| işlem sonucu | B2'nin `simule()`'si, **aynı fonksiyon** | `onkayit_mekanik.py` |
| başlangıç kasa | **1000 $** | `panel._bilesik` ile aynı |

🔴 **Mantık kopyalanmıyor:** B3, B2'nin `simule()` fonksiyonunu **doğrudan
çağırır**. İki aşama arasında sapma bu yüzden imkânsız. (B2'ye eklenen tek
şey zaman damgasıydı; ekleme sonrası B2 yeniden koşuldu ve çıktı **birebir
aynı** çıktı — `7f6eec8`.)

**Kıstas:** aynı pencerede **BTC al-tut** ve **11 coin eşit ağırlık al-tut**
(`panel.py`'nin kullandığı kıyas mantığı, aynı 1h mumlardan).

---

## 3. Örneklem

B2 ile **birebir aynı**: 456 simüle edilmiş sinyal, 2026-06-28 → 2026-08-24,
11 sembol. Kasa eğrisi 1h mumlarla 2026-08-31'e kadar taşınır.

Risk tavanı uygulanınca: **88 sinyal kabul, 368 red (%80,7)**, tepe eşzamanlı 2.

---

## 4. RAPORLANACAK NİCELİKLER (şimdi sabitleniyor)

Bu bir **betimlemedir**, kill şartlı test değil — tek bir yol gerçekleşmesi
var. Sıra sabit:

1. **Kaç işlem fiilen açıldı** (tavanı geçen ∧ tetiklenen).
2. **Son bakiye** (1000 $'dan) ve **en derin düşüş**.
3. **Kıstas:** aynı pencerede BTC al-tut ve 11-coin sepeti — bakiye + düşüş.
4. **G4 hükmü:** strateji, al-tutu **daha az düşüşle** geçiyor mu? (iki koşul
   birden; biri bile sağlanmazsa "geçmedi")
5. **Gün-bloklu bootstrap** ile son bakiyenin %95 aralığı — tek yolun ne kadar
   şanslı/şanssız olabileceği.
6. **Sağlamlık:** en çok işlem veren 3 sembol çıkarılınca 2 ve 4.
7. **Tavanın etkisi:** tavan olmasaydı (tüm 150 tetiklenen işlem) bakiye ve
   düşüş ne olurdu — *tavan koruyor mu?*

---

## 5. 🔴 SINIR ŞERHİ

**Bu tek bir yol gerçekleşmesidir.** Bakiye ve düşüş **nokta tahminidir**;
ön kayıtlı bir eşiği geçip geçmediği sorusu sorulmuyor çünkü sorulamaz.
Gün-bloklu bootstrap (nicelik 5) bunun için var: yolun ne kadar oynak
olduğunu gösterir, ama **anlamlılık iddiası doğurmaz**.

**Kıyas dönemi kısa (2 ay) ve tek rejimli sayılır** — içinde 20 Ağustos
boğası var. Al-tut o dönemde tanımı gereği güçlü. Bu, kıyası strateji
aleyhine zorlaştırır ve **öyle olması gerekir**: G4 zaten *"al-tutu geç"*
diyor, kolay dönem seçmek onu anlamsızlaştırır.

⚠ **B2'nin güç sınırı burada da geçerli:** −0,327R/işlem tahmini ~0,32R
görülebilirlik eşiğinin sınırında. Portföy sonucu o belirsizliği **taşır**,
azaltmaz.

---

## 6. Beklenti (dürüstlük kaydı — sonuç görülmeden)

1. **Kasa kaybeder.** B2 negatif, tavan işlem sayısını azaltır ama işaretini
   değiştirmez. Kayıp **büyük olmaz** çünkü sadece ~%1 risk ve az işlem var.
2. **Al-tutun çok gerisinde kalır.** Pencerede BTC yükseldi; SHORT ağırlıklı
   bir strateji tanım gereği geride kalır. **G4 hükmü: GEÇMEZ.**
3. **Düşüş al-tuttan KÜÇÜK çıkabilir** — %1 risk ve 2 pozisyon tavanı çok
   sıkı. Yani *"daha az düşüş"* şartı sağlanabilir ama *"al-tutu geç"*
   şartı sağlanmaz → **G4 yine geçmez** (ikisi birden gerekli).
4. **Tavan koruyucudur** (nicelik 7): tavansız hâlin daha kötü olmasını
   bekliyorum, çünkü daha çok kaybeden işlem alınır.

---

## 7. Geçersizlik koşulları

- `olcucu.RISK_PCT` · `defter.RISK_TAVANI_PCT` · `PENDING_SAAT` değişirse
- `onkayit_mekanik.simule()` mantığı değişirse (B2 çıktısı değişmemeli)
- Başlangıç kasa, risk yüzdesi ya da kıstas tanımı sonuç görüldükten sonra oynatılırsa

---

## 8. Sonuç ne olursa ne yapılır

| Bulgu | Anlamı |
|---|---|
| G4 geçmez (beklenen) | *Ham → mekanik → portföy* zincirinin üçü de aynı yöne işaret eder: bu sinyal ailesi **çalışmıyor**. Zincir kapanır |
| G4 geçer | Beklenmedik. **Kural değişikliği yine çıkmaz** — ön kayıtsız bir portföy betimlemesi terfi gerekçesi olamaz; ayrı ve ileri-zamanlı bir test gerekir |
| Tavan zararlı çıkarsa | Ayrı bir bulgu; `SISTEM.md` §12/8 ile birlikte değerlendirilir (radar tavanı ön kaydı 2.4 zaten koşuyor) |

**Gerçek para kapısı AÇILMAZ.**

---

## 9. Ölçüm

`onkayit_portfoy.py` — `onkayit_mekanik.simule()`'yi çağırır, tavanı
kronolojik uygular, kasayı bileşikler, kıstası aynı mumlardan hesaplar.
Salt okurdur. Ön kayıt commit'inden **sonra** yazılır, ayrı commit'lenir.

---

# SONUÇ — **G4 GEÇMEDİ; zincir kapandı** (2026-08-31)

```
1. acilan islem   :  27   (456 sinyalden; tavan + tetik suzgeci)
2. son bakiye     :   895,74 $   en derin dusus  -13,7%
3. BTC al-tut     :  1302,37 $   en derin dusus   -6,4%
   11-coin sepeti :  1274,50 $   en derin dusus  -23,2%
4. G4 HUKMU       : getiri GECMEDI · dusus DAHA COK  ->  GECMEDI
5. gun-bloklu %95 : [784,41 $ , 1037,02 $]     (tek yol 895,74 $)
6. saglamlik      : top-3 cikinca 900,95 $ / -13,8%  (yok denecek fark)
7. TAVANIN ETKISI : tavanLI 27 islem 895,74 $ / -13,7%
                    tavanSIZ 150 islem 604,63 $ / -40,0%   -> tavan +291,12 $
```

## 🔴 Beklentim ÇÜRÜDÜ — düşüş tarafında

§6'da *"düşüş al-tuttan küçük çıkabilir"* yazmıştım. **Çıkmadı:**
strateji **−%13,7**, BTC **−%6,4**. Yani strateji hem daha az kazandırdı
hem **iki kat derin** düşüş yaşattı. (Sepete göre düşüş daha sığ —
−%13,7 vs −%23,2 — ama G4'ün kıstası BTC.)

G4'ün iki koşulu birden gerekiyordu; **ikisi de sağlanmadı.**

## Üç aşama birbirini doğruluyor

| aşama | bulgu |
|---|---|
| **B1** ham sinyal | LS ↑ → fiyat ↑ (**ρ = +1,000**) |
| **B2** mekanik | −0,327R/işlem, GA sıfırı dışlıyor |
| **B3** portföy | **−%10,4** vs BTC **+%30,2**, düşüş 2 kat derin |

Üç bağımsız ölçüm, tek sonuç: **bu sinyal ailesi ters yönde çalışıyor ve
paraya da öyle dönüşüyor.**

## ⭐ Bağımsız doğrulama — simülasyon canlıyla örtüşüyor

Simüle edilen kasa **−%10,4**. Canlı sistemin panelde ölçülen gerçek sonucu
(2026-08-30) **−%13,8**. Farklı veri yolu, farklı hesap, **aynı cevap**.
Bu, simülasyonun gerçeği tarif ettiğinin bağımsız kanıtıdır — ve aynı
zamanda canlı sicilin bu ölçümle tutarlı olduğunun.

## İki "kazara koruma" nicelendi

1. **Kırılım girişi** sinyallerin **%67'sini** eliyor (B2): fiyat yükseliyorsa
   SHORT hiç açılmıyor.
2. **Risk tavanı** kalanın **%80,7'sini** eliyor ve **+291,12 $** kurtarıyor;
   düşüşü **−%40 → −%13,7**'ye indiriyor.

⚠ İkisi de **tasarlanmış koruma değil**. Tavan korelasyon için kondu, kırılım
girişi işlem mantığı gereği var. Ters bir sinyali frenlemeleri **yan etki**.
Ama etkileri büyük: bu iki fren olmasaydı kasa 604 $ ve −%40 düşüşte olurdu.

## Sağlamlık

Top-3 sembol çıkarılınca sonuç **neredeyse aynı** (900,95 $ vs 895,74 $).
Kayıp birkaç sembolden gelmiyor — **yaygın**. Bu, B2'deki zayıflığın
(orada büyüklük top-3'e duyarlıydı) portföy düzeyinde **olmadığını** gösterir.

## Bootstrap

Gün-bloklu %95 aralık **[784 $, 1037 $]**. Yani bu stratejinin *şanslı*
versiyonu bile ancak başabaş; BTC'nin 1302 $'ına hiçbir kolda yaklaşmıyor.

## Ne çıkar, ne çıkmaz

✅ **Çıkar:** *ham → mekanik → portföy* zinciri bu sinyal ailesi için
**kapandı**. Üç aşamanın üçü de olumsuz ve birbirini doğruluyor.
✅ **Çıkar:** iki frenin (kırılım girişi, risk tavanı) koruyucu etkisi
nicel olarak biliniyor.

⛔ **Çıkmaz:** *"skoru tersine çevir"* — LONG kolu (SS) hiç güçlendirilmiş
ölçülmedi (n=85) ve ters çevirmek onu üretir.
⛔ **Çıkmaz:** *"tavanı/stopu şu yapalım"* — hiçbir parametre taranmadı.
⛔ **Çıkmaz:** diğer 14 adayın hükmü — bu zincir **tek aile** ölçtü.
