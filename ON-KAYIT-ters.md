# ÖN KAYIT — `ters`: "LS ≥ 70 iken LONG" ne yapardı?

**Yazım anı:** 2026-08-31 (koşumdan ÖNCE, hiçbir LONG işlemi çözülmeden)
**Durum:** DONDURULDU. Kural (§2), örneklem (§3), nicelikler (§4), sınır
şerhi (§5) bu commit'ten sonra değiştirilmez.
**Öncülleri:** `b01d493` (ham: ρ=+1,000) · `be56b77` (mekanik) · `317c8d0` (portföy).

---

## 0. 🔴 BU BİR HÜKÜM TESTİ DEĞİLDİR — önce bunu okuyun

Tersleşmeyi **bu veride gördük**. Şimdi ters kuralı **aynı veride** sınıyoruz.
Bu, tanımı gereği **ÖRNEKLEM-İÇİ İNŞADIR** ve bu projenin daha önce yandığı
yerdir (`ON-KAYIT-radar-v2.md` §5: *"post-hoc hücreler ortalamaya geri döner"*;
dış proje: *"2 yılın tamamı kullanıldı → tek geçerli hakem İLERİ ZAMAN"*).

**Bu yüzden bu ölçüm:**
- ⛔ Kural değişikliği **doğuramaz**
- ⛔ *"Ters kural çalışıyor"* cümlesini **kurduramaz**
- ✅ Yalnızca şunu söyleyebilir: *"ileri-zamanlı bir test kurmaya değer mi?"*

**Ön kaydın işlevi burada hipotez dondurmak değil, NİCELİKLERİ dondurmaktır** —
sonucu görüp "şuna bakalım" diyememek için.

---

## 1. Neden bu ölçüm

15 aday öldü, hiçbiri ayakta kalmadı. **Ayakta kalan tek düzenlilik**, skorun
kendisinin ters sıralaması: ρ=+1,000, beş bandın beşinde, 65 günde, sembol
çıkarmaya dayanıklı. Bu projenin şimdiye kadar ölçtüğü **en güçlü ve en
tutarlı ilişki** — sadece ters yönde.

Eğer bu sistemde bir yerde bilgi varsa, en güçlü adayı budur. İleri-zamanlı
bir test kurmadan önce, mekanik ve portföy aşamalarından geçip geçmediğine
bakmak ucuzdur (veri hazır).

---

## 2. Kural (mekanik — `trade_plan`'in LONG dalı, BİREBİR)

🔴 **Ters çevirmek yön değiştirmek DEĞİLDİR.** SHORT `swing_low`'un altına
kırılımdan girer; LONG `swing_high`'ın **üstüne** kırılımdan. **Farklı işlem,
farklı giriş, farklı stop.**

| | değer | kaynak |
|---|---|---|
| sinyal | `LS ≥ 70` (aynı sinyal) | `olcucu.SQUEEZE_FLAG` |
| yön | **LONG** (mevcut kuralın tersi) | — |
| giriş | `swing_high` = son 50 saatlik barın en yükseği | `trade_plan` LONG dalı |
| stop | giriş **− 2,5 × ATR** | `olcucu.STOP_ATR` |
| TP1 / TP2 | giriş **+ 5,2 / + 8,33 × ATR** | `olcucu.TP1/TP2_ATR` |
| tetiklenme | bar **high ≥ giriş** (yukarı kırılım) | — |
| pencere · maliyet · tekilleştirme · tavan | **B2/B3 ile birebir aynı** | `defter` |

Çözünürlük 1h; aynı barda stop+TP → **STOP** (temkinli, kuralın aleyhine).

---

## 3. Örneklem

B2/B3 ile **aynı sinyaller**: `LS ≥ 70`, 12s cooldown, tam pencereye sığan.
Fark yalnız yön ve giriş seviyesi.

**Rejim ayrımı (şimdi sabitleniyor):** boğa başlangıcı **2026-08-20**
(`SISTEM.md` kaydı, bu ölçüme bakılmadan belirlenmiş tarih).
Pencere: boğa ÖNCESİ ~54 gün · boğa ~11 gün.

---

## 4. RAPORLANACAK NİCELİKLER (sıra sabit)

1. Tetiklenme oranı · sonuç dağılımı · ortalama net R (gün-kümeli GA).
2. **REJİM KIRILIMI — bu ölçümün ASIL sorusu:** aynı nicelikler **boğa
   öncesi** ve **boğa** için ayrı ayrı.
3. Portföy: açılan işlem · son bakiye · en derin düşüş · BTC al-tut kıyası (G4).
4. Sağlamlık: top-3 sembol çıkarılınca 1 ve 3.
5. **Yan yana tablo:** mevcut kural (SHORT) vs ters kural (LONG), aynı sinyaller.

---

## 5. 🔴 KARAR KURALI — sonucu görmeden yazılıyor

Bu ölçüm **tek bir soruyu** cevaplar: *ileri-zamanlı test kurmaya değer mi?*

| Bulgu | Sonraki adım |
|---|---|
| **Boğa öncesinde DE pozitif** ve G4'ü geçiyor | ✅ İleri-zamanlı ön kayıt yazılır. Kural **yine değişmez** — canlıda sınanır |
| Yalnız **boğada** pozitif | ❌ **DEĞMEZ.** Boğada LONG tanımı gereği kazanır; bu bulgu değil totolojidir |
| Boğa öncesinde de negatif | ❌ Ters kural da ölü. Skor **hiçbir yönde** bilgi taşımıyor demektir |

🔴 **En kritik satır ikincisidir.** Ters çevirmek LONG üretir ve pencerenin
son 11 günü boğadır. **Boğa performansı tek başına HİÇBİR ŞEY kanıtlamaz** ve
bu satır tam da onu kayda geçirmek için sonucu görmeden yazılıyor.

⚠ **Boğa öncesi n küçük olabilir** (LS≥70 sinyalleri o döneme nasıl dağıldığı
bilinmiyor). n<20 çıkarsa hüküm *"ölçülemedi"* olur, *"geçti/kaldı"* değil.

---

## 6. Beklenti (dürüstlük kaydı — sonuç görülmeden)

**Ters kuralın boğa öncesinde de pozitif çıkmasını bekliyorum, ama zayıf.**
Gerekçe: B1'in tersleşmesi boğa öncesinde **daha güçlüydü** (+%0,392 vs tüm
pencere +%0,318). Yani ham sinyal boğa öncesinde de aynı yönü gösteriyordu.

**Ama mekanikte kaybedebilir:** LONG girişi `swing_high` kırılımı — yani
tepeden alım. B2'de SHORT'un `swing_low` girişi sinyallerin %67'sini
elemişti; LONG'da eleme oranı farklı olacak ve **tepeden alıp stop yeme**
riski gerçek. Mekaniğin ham kenarı yiyip yemediğini bilmiyorum.

**G4'ü geçmesini BEKLEMİYORUM.** Pencerede BTC +%30 yaptı; bir LONG
stratejisinin onu geçmesi için çok güçlü olması gerekir.

---

## 7. Geçersizlik koşulları

- `trade_plan` LONG dalının sabitleri değişirse
- Rejim tarihi (2026-08-20) sonuç görüldükten sonra oynatılırsa
- Nicelikler ya da karar kuralı (§5) sonradan değiştirilirse

---

## 8. Ölçüm

`onkayit_ters.py` — B2'nin veri yolunu ve `simule()` desenini kullanır,
yalnız yön/giriş/stop LONG dalına çevrilir. Salt okurdur. Ön kayıt
commit'inden **sonra** yazılır, ayrı commit'lenir.

---

# SONUÇ — **TERS KURAL DA ÖLÜ** (2026-08-31)

## §5'in karar kuralı devreye girdi

```
                    sinyal  tetik   ort net R   gun-kumeli GA95      portfoy
TUM PENCERE           456    168     +0,075R   [-0,320, +0,473]     933,58 $ / -20,2%
BOGA ONCESI (<08-20)  404    140     -0,134R   [-0,447, +0,209]     915,92 $ / -20,2%
BOGA        (>=08-20)  52     28     +1,122R   [-0,594, +1,795]    1052,33 $ /  -2,1%
```

**Ters kuralın tüm artısı 11 günlük boğa penceresinden geliyor. Boğa öncesi
54 günde NEGATİF.**

§5'te, sonucu görmeden şu yazılmıştı:

> *"Yalnız boğada pozitif → ❌ **DEĞMEZ.** Boğada LONG tanımı gereği kazanır;
> bu bulgu değil **totolojidir**."*

**Gerçekleşen tam olarak budur. İleri-zamanlı test kurulmayacak.**

## Üstelik istatistik de yok

Üç kesitin **üçünde de** güven aralığı sıfırı kapsıyor — boğa kolu dahil
(28 işlem, ~11 gün). Yani *"boğada kazandı"* bile gösterilemiş değil,
sadece gözlenmiş.

## Yan yana — iki yön de kaybediyor

```
MEVCUT (SHORT)   tetik 150 · ort -0,327R · portfoy 27 islem  895,74 $ · dusus -13,7%
TERS   (LONG)    tetik 168 · ort +0,075R · portfoy 41 islem  933,58 $ · dusus -20,2%
                                                    BTC al-tut 1302,37 $ · dusus  -6,4%
```

**İkisi de 1000 $'ın altında bitiyor**, ikisi de al-tutun çok gerisinde,
ve ters kural **daha derin düşüş** yaşatıyor (−%20,2 vs −%13,7).

## Beklentim kısmen tuttu — mekanik ham kenarı yedi

§6'da *"mekanikte kaybedebilir: LONG girişi `swing_high` kırılımı, yani
**tepeden alım**"* yazmıştım. Olan bu: ham sinyalde boğa öncesi tersleşme
**daha güçlüydü** (+%0,392), ama mekanik uygulanınca boğa öncesi **−0,134R**
oldu. **Kırılım girişi ham kenarı yiyor.**

⚠ **Not:** B2'de stop **koruyucu** çıkmıştı; burada mekanik (giriş seviyesi)
**yıkıcı**. İkisi çelişmiyor — farklı bileşenler. Stop zararı kesiyor,
tepeden-alım girişi kenarı yiyor.

## Top-3 çıkarılınca "pozitif" görünüyor — bu KANIT DEĞİL

Top-3 sembol (SOL, ETH, BNB) çıkarılınca +0,135R ve 1035,57 $ çıkıyor.
🔴 **Bu bir bulgu değildir:** hangi sembollerin çıkarılacağı **sonuca
bakılarak** belirlendi ve GA hâlâ sıfırı kapsıyor [−0,309, +0,543].
*"En iyi hücre seçilmez"* kuralının ta kendisi.

## 🔴 PROJE İÇİN ASIL SONUÇ

`squeeze_scores()` **hiçbir yönde kullanılabilir bilgi taşımıyor**:

| yön | sonuç |
|---|---|
| mevcut (SHORT) | ters sıralıyor, −0,327R, portföy −%10,4 |
| ters (LONG) | boğa öncesi negatif; artısı totoloji |

Skor **yanlış yönde değil — kullanılamaz durumda.** Yönü çevirmek çözüm
değil, çünkü çevirince de mekanik onu yiyor.

**Sıradaki adım (b) — B4, tek-bant sorunu:** bandın dışında bilgi var mı?
Bu artık "iyileştirme" sorusu değil, **"bu veri bir strateji taşıyabilir mi"**
sorusudur.
