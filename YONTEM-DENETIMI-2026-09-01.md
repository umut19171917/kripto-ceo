# YÖNTEM DENETİMİ — gün-kümeli bootstrap fazla mı kesin?

**Yazım anı:** 2026-09-01, **koşumdan ÖNCE.** Yorum kuralı (§3) sonuç
görülmeden dondurulmuştur.
**Bağlı maddeler:** 8.4 (gün-içi permütasyon) · 8.7 (kuralı kodla koru)

---

## 1. Şüphe nereden çıktı

`ON-KAYIT-topls.md` hükmünde (`9871f58`) kayda geçti: güç hesabı **%0,29**
saptanabilir fark öngörmüştü, gerçekleşen GA yarı-genişliği **%0,087** oldu —
**3,3 kat dar**. İki açıklama var ve o an ayrıştırılamadı:

1. *"2,5 etkin bağımsız sembol"* varsayımı fazla muhafazakârdı, **ya da**
2. **gün-kümeli bootstrap yalnız ~30 blokla belirsizliği olduğundan az gösteriyor.**

İkincisi doğruysa sorun tek bir ölçümle sınırlı değildir: **aynı yöntem
`basis` (`162100b`), `mekanik` (`be56b77`), `portföy` (`317c8d0`) ve `ters`
(`8274909`) hükümlerinde de kullanıldı.**

---

## 2. Denetim nasıl yapılır

**Gün-içi etiket permütasyonu** (madde 8.4). Bootstrap ile aynı soruyu
sormaz — ikisi tamamlayıcıdır:

| yöntem | cevapladığı soru |
|---|---|
| bootstrap | *"bu tahmin ne kadar belirsiz?"* |
| **permütasyon** | *"bu kadar büyük bir fark **şans eseri** çıkar mıydı?"* |

**Sıfır hipotezi:** bant etiketi ile ileri getiri arasında bağ yoktur.
**Uygulama:** her takvim günü **içinde** bant etiketleri karıştırılır
(gün yapısı ve piyasa geneli hareket korunur, yalnız BAĞ kırılır),
uç bant farkı yeniden hesaplanır. 5.000 tur.
**p = |permütasyon farkı| ≥ |gözlenen fark| olan turların oranı.**

**Uygulanacak veri:** `onkayit_topls.py`'nin ana kolu (aynı 19.852 gözlem)
ve `onkayit_basis.py`'nin artık kolu (350.100 gözlem) — ikisi de kapanmış
ölçümler.

---

## 3. 🔴 YORUM KURALI — sonucu görmeden yazılıyor

Bu bir **yöntem denetimidir**, aday diriltme girişimi DEĞİLDİR.

| bulgu | anlamı |
|---|---|
| p büyük (>0,10), bootstrap GA sıfırı kapsıyor | ✅ İki yöntem **aynı şeyi** söylüyor. Hükümler sağlam |
| **p küçük (<0,05) ama bootstrap GA sıfırı kapsıyordu** | 🔴 **YÖNTEMLER ÇELİŞİYOR.** Bootstrap fazla geniş ya da permütasyon fazla dar. Hüküm **değişmez**; ama *"çıkarım yöntemimiz güvenilmez"* kaydı düşülür ve **her iki yöntem birlikte** zorunlu hale gelir |
| p büyük ama GA sıfırı **dışlıyordu** (başka ölçümlerde) | 🔴 O ölçümün hükmü **fazla kesin** yazılmış demektir; şerh eklenir |

🔴 **HİÇBİR DURUMDA:** *"p küçük çıktı, demek ki `top_ls` aslında yaşıyor"*
denilemez. Kapanmış bir ölçümün verisine yeni bir istatistik uygulamak
**post-hoc'tur**; aday diriltmek **yeni ve ileri-zamanlı bir ön kayıt** ister.
Bu satır tam da onu peşinen engellemek için yazılıyor.

---

## 4. Denetimin kendi sınırı

Permütasyon da kusursuz değil: gün **içi** karıştırma, gün içi otokorelasyonu
korumaz. Öngörücü gün içinde yavaşsa (ör. `top_ls` seviyesi, τ≈416 saat)
permütasyon **fazla dar** bir sıfır dağılımı üretir ve p'yi küçük gösterir.
Ana kol (`d1`, τ≈1,8 saat) bu sorundan büyük ölçüde muaftır; **seviye kolu
değildir** ve bu yüzden seviye kolunun p'si de hüküm doğurmaz.

---

## 5. Kalıcı çıktı

Denetim sonucundan bağımsız olarak: bootstrap ve permütasyon **tek bir
paylaşılan modüle** (`olcum.py`) taşınır ve bant raporu **ikisini birden
basmadan hüküm satırı yazmayı reddeder**. Madde 8.7'nin gereği:
*kuralı düzyazıyla değil KODLA koru.*
