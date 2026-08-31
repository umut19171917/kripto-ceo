# ÖN KAYIT — `mekanik`: stopumuz sinyalin ne kadarını yiyor?

**Yazım anı:** 2026-08-31 (koşumdan ÖNCE, hiçbir işlem çözülmeden)
**Durum:** DONDURULDU. Mekanik (§2), örneklem (§3), raporlanacak nicelikler (§4)
ve güç şerhi (§5) bu commit'ten sonra değiştirilmez.
**Yol haritası:** SIRA B / madde **B2** — bekleyen-isler **7.2**.
**Öncülü:** `ON-KAYIT-skor-yonu.md` → **İŞARET TERS** (ρ=+1,000, `b01d493`).

🔴 **BU AN İTİBARIYLA HİÇBİR İŞLEM ÇÖZÜLMEDİ.** Bakılanlar yalnız *sayım*
nicelikleriydi: kaç sinyal, kaç gün, sembol dağılımı. Hiçbir sonuç, getiri
ya da R hesaplanmadı.

---

## 1. Neden bu test var

Bu projede **15 aday öldü** ve hepsi **aynı mekanikle** ölçüldü: sabit
2,5 ATR stop, 5,2 ATR hedef. *"Hayatta kalan bulgu sıfır"* hükmünün ne
kadarı sinyalin, ne kadarı **kendi stopumuzun** — hiç ayrıştırılmadı.

Dış projede tam bu hata bir hücreyi *"gürültü, öldü"* diye gömdürmüştü;
ham getiride **+2,284** çıktı. Ölen sinyal değil, stoptu. Onların kaydı:
*"bizim stopumuzun öldürdüğü bir kenarı 'sinyal boş' diye kaydederiz."*

**B1 bu soruyu acil hâle getirdi:** ham sinyalde LS skoru **ters** sıralıyor
(yüksek LS → fiyat yükseliyor). Ama sistem **anlık fiyattan girmiyor** —
girişi `swing_low`, yani bir **kırılım emri**. Fiyat yükseldiyse SHORT
**hiç tetiklenmemiş** olabilir. Ham bulgunun paraya çevrilip çevrilmediği
ancak mekanik uygulanınca görülür. Bu test o adımdır.

---

## 2. Mekanik (sistemin KENDİ sabitleri — hiçbiri icat edilmedi)

| | değer | kaynak |
|---|---|---|
| sinyal | `LS ≥ 70` | `olcucu.SQUEEZE_FLAG` / `PLAN_FLAG` |
| yön | SHORT | `trade_plan`: long-squeeze → aşağı kırılım |
| giriş | `swing_low` = son **50** saatlik barın en düşüğü | `olcucu.SWING_LOOKBACK` |
| stop | giriş **+ 2,5 × ATR** | `olcucu.STOP_ATR` |
| TP1 / TP2 | giriş **− 5,2 / − 8,33 × ATR** | `olcucu.TP1_ATR/TP2_ATR` |
| ATR | 14 periyot, **1h** | `olcucu.atr`, `SWING_TF` |
| tetiklenmezse | **24 saatte** iptal | `defter.PENDING_SAAT` |
| tetiklendikten sonra | **120 saatte** zaman aşımı | `defter.ACTIVE_SAAT` |
| maliyet | `defter.maliyet_R` (maker/taker/slipaj/BNB) | `defter` |
| tekilleştirme | aynı sembole **12 saat** içinde yeni sinyal yok | `defter.COOLDOWN_SAAT` |

**Çözünürlük: 1 saatlik bar.** `defter.coz()` 1 dakikalık mum ister
(11 sembol × 65 gün ≈ 700 API çağrısı); onun yerine 1h barın high/low'u
kullanılır.
⚠ **Bar içi yol bilinmiyor** → aynı barda hem stop hem TP değerse
**STOP kabul edilir** (temkinli kural, `coz()`'un kendi yakınsaması).
Bu, **sinyalin ALEYHİNE** yanlılıktır — güvenli yön, ve sonuç sinyal
lehine çıkarsa bu yanlılığa **rağmen** çıkmış olur.

---

## 3. Örneklem

| | |
|---|---|
| kaynak | `olcucu.log` skorları (B1 ile **aynı** veri, aynı seyreltme) |
| ham `LS ≥ 70` gözlem | 1.634 |
| 12 saat cooldown sonrası | 473 |
| **tam pencereye (24+120s) sığan** | **437** |
| dönem | 2026-06-28 → 2026-08-24, **58 gün** |
| sembol | 11 (en çok ETH %13,5 — baskın sembol yok) |
| 1h mum | 11 × 1.652 bar, 2026-06-23 → 2026-08-31 |

⚠ **Tekilleştirme neden şart:** LS 10 saat üst üste ≥70 kalırsa bu 10 sinyal
değil, **aynı sinyalin 10 kopyasıdır** (aynı `swing_low`, örtüşen pencere).
Sistem de öyle davranmıyor. Tekilleştirmeden ölçmek n'i 3,7 kat şişirirdi.

---

## 4. RAPORLANACAK NİCELİKLER (şimdi sabitleniyor)

Bu bir **ayrıştırma**dır, kill şartlı bir hipotez testi değil — ve öyle
sunulmayacak. Aşağıdaki nicelikler, sonuç görülmeden, **tam bu sırayla**
raporlanır:

**A · Mekanik ne kadarını eliyor**
1. **Tetiklenme oranı** — 437 sinyalin kaçı `swing_low`'a değdi (24s içinde)?
2. Tetiklenenlerin sonuç dağılımı: `stop` / `tp1` / `tp2` / `zaman_aşımı`.

**B · 7.2'nin ASIL sorusu**
3. **Stop olan işlemlerin kaçı, 120 saatlik ufkun sonunda KÂRDA olurdu?**
   (stop kaldırılıp aynı pencere sonuna kadar tutulsaydı)
4. Aynı soru TP'ye ulaşanlar için tersten: kaçı stopla korunmuş oldu?

**C · İşaret ve büyüklük**
5. Ortalama net R (maliyet dahil), **gün-kümeli %95 GA** ile.
6. Ham karşılaştırma: aynı 437 sinyalin **mekaniksiz** +120s getirisi
   (SHORT yönüne çevrilmiş) — *"stop ne kadarını yedi"* farkı.

**D · Sağlamlık**
7. En çok katkı veren 3 sembol çıkarılınca 5 ve 6 nasıl değişir.

---

## 5. 🔴 GÜÇ ŞERHİ (EK 4 zorunluluğu)

**Sayım nicelikleri (A ve B) İYİ güçlendirilmiş.** n=437'de bir oranın %95
GA yarı-genişliği ≈ **±%4,7**; ~130 stop olan işlemde ≈ **±%8,6**. Bu
sorular güvenle cevaplanır.

**Büyüklük (C-5) DEĞİL.** R'nin sd'si ≈1,4; 58 gün, günde ~7,5 sinyal →
gün-içi korelasyonla tasarım etkisi ~2,9 → **görülebilen fark ≈ 0,32R**.

**Zorunlu cümle:**
> *n=437 / 58 gün, gün-kümeli çıkarımla bu test ancak **~0,32R**
> büyüklüğünde bir etkiyi görebilir. B1'in ham aşamada ölçtüğü ~%0,3/24s'lik
> etki, tipik %3-5'lik stop mesafesiyle **~0,06–0,10R**'ye karşılık gelir —
> yani **bu test o büyüklüğü GÖREMEZ.*** Dolayısıyla C-5'ten *"etki yok"*
> sonucu **çıkarılamaz**; yalnız *"bu testle gösterilemedi"* denir.

⚠ **Bu testin işi büyüklük ölçmek değil, AYRIŞTIRMAK:** *"sinyal mi boştu,
stop mu öldürdü?"* Sayım nicelikleri bunu cevaplar; ortalama R cevaplamaz.

---

## 6. Beklenti (dürüstlük kaydı — sonuç görülmeden)

1. **Tetiklenme oranının DÜŞÜK çıkmasını bekliyorum** (%50'nin altı). B1'de
   yüksek LS'i yükselen fiyat izliyordu; `swing_low`'a değmek için fiyatın
   *düşmesi* gerekir. Öyleyse ham tersliğin büyük kısmı **tetiklenmeyen**
   sinyallerde kalır ve paraya dönüşmez.
2. **Stop olanların azımsanmayacak kısmının (>%20) ufuk sonunda kârda
   olacağını bekliyorum.** Dış projede bu oran %15,1 idi; bizim stopumuz
   (2,5 ATR) onlarınkine (1,5 ATR) göre geniş, yani oranın daha **düşük**
   çıkması da makul. İki yönde de şaşırmam.
3. Ortalama net R'nin negatif ama GA'sı sıfırı kapsayan bir değer olmasını
   bekliyorum — §5 gereği bu **bilgi taşımaz**.

---

## 7. Geçersizlik koşulları

- `trade_plan` sabitleri (`STOP_ATR` · `TP1_ATR` · `SWING_LOOKBACK` · `PLAN_FLAG`)
  ya da `defter` limit/maliyet sabitleri koşum öncesi/sırasında değişirse
- Çözünürlük, pencere ya da tekilleştirme kuralı sonuç görüldükten sonra oynatılırsa
- 1h mum verisi eksik/bozuk çıkarsa (kapsama koşumda raporlanır)

---

## 8. Sonuç ne olursa ne yapılır

| Bulgu | Anlamı |
|---|---|
| Tetiklenme düşük + net R sıfıra yakın | B1'in tersliği **paraya dönüşmüyor**; kırılım girişi kazara koruyor. Skor yine de yanlış sıralıyor — düzeltmek serbest kalır ama **acil değildir** |
| Tetiklenme yüksek + net R negatif | Terslik **paraya dönüşüyor**. Skor aktif zarar veriyor; §12/1 kararı aciliyet kazanır |
| Stop olanların çoğu ufukta kârda | **Stop suçlu.** 15 ölü adayın hükmü şüpheye girer, hepsi ham aşamada yeniden sorulmalı |
| Stop olanların azı ufukta kârda | Stop aklanır; *"sinyal boştu"* hükümleri ayakta kalır |

**Hiçbir durumda kural değişikliği bu testten çıkmaz** — portföy aşaması
(3. aşama) yapılmadı ve her değişiklik kendi ön kaydını ister.
**Gerçek para kapısı AÇILMAZ.**

---

## 9. Ölçüm

`onkayit_mekanik.py` — B1'in verisini ve indirilmiş 1h mumları okur,
`trade_plan` mekaniğini birebir uygular, §4'ün niceliklerini **sırayla**
basar. Salt okurdur. Ön kayıt commit'inden **sonra** yazılır, ayrı commit'lenir.

---

# SONUÇ — **STOP SUÇLU DEĞİL; SİNYAL ZATEN KAYBETTİRİYOR** (2026-08-31, `3d5df5a`)

## Örneklem şerhi (önce bu)

| | ön kayıt §3 | koşum |
|---|---|---|
| ham `LS ≥ 70` | 1.634 | **1.828** |
| 12s cooldown sonrası | 473 | **502** |
| tam pencereye sığan | 437 | **462** |
| simüle edilen | — | **456** (6'sı dejenere plan → VETO) |

**Fark neden:** §3'ün sayıları B1 veri setinden alınmıştı ve orada her
gözlemin **+24s ileri eşleşmesi** şartı vardı (getiri hesabı için). Bu araç
aynı kuralı **log'a doğrudan** uyguluyor; +24s eşleşme şartı yok, çünkü bu
test 144 saatlik pencere istiyor. **Kural aynı, ara süzgeç farklı.**
D/9 gereği kayda geçer; ölçütlere dokunulmadı.

## Sonuçlar

```
A1. tetiklenme orani : 150/456 = %32,9
A2. sonuc dagilimi   : stop 108 (%72) · tp1 29 (%19) · zaman_asimi 12 (%8) · tp2 1 (%1)
B3. STOP olanlarin ufuk sonunda KARDA olacaklari : 29/108 = %26,9
B4. TP'ye ulasanlarin ufukta ZARARA donecekleri  :  3/30  = %10,0
C5. ortalama net R   : -0,327R   gun-kumeli GA95 [-0,573, -0,090]   (n=150, 34 gun)
C6. STOPSUZ (ufuk sonu) : -0,885R   ->  STOPUN ETKISI +0,558R/islem
```

## 🔴 Asıl bulgu — beklentim ÇÜRÜDÜ

**Stop bu sinyal ailesinde katil değil, KORUYUCU.** Aynı işlemler stopsuz
tutulsaydı **−0,885R** olurdu; stopla **−0,327R**. Stop işlem başına
**+0,558R kurtarıyor**.

Bu, dış projenin vakasının **tam tersi**: orada stop gerçek bir kenarı
öldürmüştü (+2,284 → gömüldü). Burada stop, kaybettiren bir sinyalin
zararını yarıdan fazla kesiyor.

**7.2'nin sorusuna cevap (bu sinyal ailesi için):** *"15 ölü adayın kaçı
stopumuzun eseri?"* → En azından bu ailede **hiçbiri**. Sinyal ham hâliyle
de kaybettiriyor; stop onu kurtarmıyor, batmasını yavaşlatıyor.

## Ama stopun bir bedeli var

**B3: stop olan 108 işlemin 29'u (%26,9) ufuk sonunda kârda olurdu.**
Yani stop dörtte birden fazlasını erken kesiyor. Bu gerçek bir maliyet —
sadece toplamda korumanın faydasından küçük.

## İki aşama birbirini doğruluyor

| | B1 (ham sinyal) | B2 (mekanik) |
|---|---|---|
| bulgu | LS ↑ → fiyat ↑ (ρ=+1,000) | SHORT işlemleri kaybediyor (−0,327R) |

İkisi **aynı şeyi** söylüyor: skor SHORT derken piyasa yukarı gidiyor.
B1 sinyalde gördü, B2 kasada gördü.

⚠ **Ama mekanik zararın çoğunu emiyor:** sinyallerin yalnız **%32,9'u**
tetikleniyor. Kırılım girişi (`swing_low`) sinyalin üçte ikisini **kazara**
filtreliyor — fiyat yükseliyorsa SHORT hiç açılmıyor. Bu bir tasarım
başarısı değil, **şanslı bir yan etki**; ama etkisi gerçek.

## Sağlamlık (D7)

Top-3 sembol (XRP, SOL, DOGE) çıkarılınca: tetiklenme %30,4 · stopun etkisi
**+0,428R** (yön aynı) · net R −0,266R ama **GA95 [−0,594, +0,032] artık
sıfırı kapsıyor**.
→ **Yön sağlam, büyüklük birkaç sembole bağlı.** C5'in "sıfırı dışlıyor"
niteliği tüm örneklemde geçerli, alt-örneklemde değil.

## Güç şerhi (ayrılamaz)

Sayım nicelikleri (A1/A2/B3/B4) iyi güçlendirilmiş. **C5'in GA'sı sıfırı
dışlıyor ve etki (−0,327R) ilan edilen görülebilirlik eşiğinin (~0,32R)
üstünde** — yani bu bulgu testin çözebildiği bölgede. C6'nın farkı
(+0,558R) da öyle. Ama D7 gösteriyor ki büyüklük yoğunlaşmaya duyarlı.

## Ne çıkarılmaz

⛔ **"Stopu gevşetelim/sıkalım"** — bu test stop *çarpanını* taramadı, tek
bir mekaniği ölçtü. Tarama yapmak eşik araması olurdu.
⛔ **"Skoru tersine çevirelim"** — portföy aşaması (3. aşama) hâlâ yapılmadı:
korelasyon, eşzamanlı maruziyet, düşüş. Ve ters çevirmek LONG üretir; LONG
kolu (SS) bu projede **hiç güçlendirilmiş biçimde ölçülmedi** (n=85).
⛔ **Diğer 14 adayın hükmü** — bu test **tek bir sinyal ailesini** ölçtü.
Onların stop-suçluluğu ayrıca sorulmalı.
