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
