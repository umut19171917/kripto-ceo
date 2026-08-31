# ÖN KAYIT — `topls`: büyük hesapların POZİSYON KAYMASI yön taşıyor mu?

**Yazım anı:** 2026-09-01 (koşumdan ÖNCE; getiriyle hiçbir ilişki hesaplanmadan)
**Durum:** DONDURULDU. Tanımlar (§2), örneklem (§3), nicelikler (§4), güç (§5),
karar kuralı (§6) bu commit'ten sonra değiştirilmez.
**Öncülleri:** `b01d493` (B1) · `317c8d0` (B3) · `8274909` (ters) · `162100b` (basis)
**Bağlı madde:** 7.4 / B4 — TEK-BANT SORUNU

---

## 0. Bu aday neden "ölü listesinden" geri döndü

`top_ls` projenin ölü aday listesinde yazıyordu. **Yanlış sınıflanmıştı.**
Gerçek kayıt (`olcucu.py:119`, 2026-07-04):

> *"top_ls KALDIRILDI: canlı sicilde katkısız (monotonluk **ρ=−0,12, n=30**)
> + tarihsel test **İMKÂNSIZ** (uç ~30 gün tutar)"*

n=30 ile görülebilecek en küçük ilişki **|ρ| ≥ 0,38**. Ölçülen −0,12 gürültünün
tam içinde. Bu **"bilgi yok" değil, "ÖLÇÜLEMEDİ"**. Aday ölmedi, **veri
yetersizliğinden emekliye ayrıldı** — ve ölçülememe sebebi 2026-08-31'de
arşivleme başlayınca ortadan kalktı (`bae3f86`, 29 gün geri dolgu).

---

## 1. 🔴 UFKU VE BİÇİMİ VERİ SEÇTİ, BEN DEĞİL

Ön kayıttan önce değişkenin **kendi kalıcılığı** ölçüldü (28 sembol, 29,5 gün,
**yalnız marjinaller; getiriyle hiçbir ilişki hesaplanmadı**):

| biçim | ρ(1s) | ρ(24s) | bütünleşik otokor. süresi | sembol başına bağımsız gözlem |
|---|---|---|---|---|
| seviye `top_ls` | +0,995 | +0,801 | ~416 saat | **1,7** |
| fark `top_ls − ls` | +0,994 | +0,776 | ~344 saat | **2,1** |
| **değişim 1s** | **+0,284** | −0,006 | **~1,8 saat** | **394,6** |
| değişim 8s | +0,920 | −0,000 | ~23,9 saat | 29,6 |

**Seviye sınanamaz.** Yarı-ömrü ~120 saat olan bir değişken 29,5 günde sembol
başına ~2 kez bağımsız değişir; hangi ufuk seçilirse seçilsin elde ~2 deney
kalır. Seviyeyi sınamak **yıllarca** arşiv ister.

**Değişim sınanabilir.** Bu yüzden soru *"büyük hesaplar ne kadar long?"*
değil, **"büyük hesaplar pozisyonunu ne yöne kaydırdı?"**

⚠ **DÜRÜSTLÜK ŞERHİ — bu bir spesifikasyon araması DEĞİLDİR.** Seviyeden
değişime geçiş **fizibilite** üzerinde yapıldı, **sonuç** üzerinde değil:
karar anında getiriyle hiçbir ilişki hesaplanmamıştı. Aynı sınıf bir tasarım
değişikliği `ON-KAYIT-radar-tavan.md` §5'te de olmuştu (güç hesabı birincil
ölçütü getiriden düşüşe çevirdi). Güç hesabının tasarımı değiştirmesi
**kuralın gereğidir**, ihlali değil.

---

## 2. TANIMLAR (donduruluyor)

| büyüklük | tanım |
|---|---|
| `tl_t` | `top_ls`'in t saatindeki ortalaması (5dk noktaları saatlik kovaya indirilir) |
| **`d_t`** | **`tl_t − tl_{t−1}`** — 1 saatlik pozisyon kayması. **ANA DEĞİŞKEN** |
| `ileri_t` | `(perp_kapanış_{t+1s} − perp_kapanış_t) / perp_kapanış_t × 100` |

🔴 **İleri bakış yasağı:** `d_t` yalnız `t` ve öncesindeki arşiv noktalarından
üretilir. Arşiv damgaları Binance'in yayım anıdır; `t` saatinin kovası
`t` içinde kapanır, getiri `t`'den SONRA başlar.

🔴 **Ölçek düzeltmesi:** `d`'nin sd'si sembole göre değişir. Bantlar
**sembol içinde** beşe bölünür (eşit sayılı), sonra havuzlanır — B1 ve
basis ile aynı desen.

Çözünürlük 1 saat. Tohum `random.seed(11)`.

---

## 3. ÖRNEKLEM

- **Semboller:** `perp-arsiv/`de hem `top_ls` hem `ls` serisi **≥20 gün** olan
  semboller. Ölçüldü: **28 sembol**. (Liste sonuca bakılarak seçilmedi;
  şart veri uzunluğudur.)
- **Pencere:** arşivin kapsadığı ~29,5 gün (2026-08-02 → 2026-09-01 civarı).
- ⚠ **Hayatta kalma yanlılığı:** arşiv evreni hacim liderlerinden üretiliyor;
  bugün listede olmayan semboller yok.
- ⚠ **Tek rejim:** 29,5 gün tek bir piyasa döneminden ibaret. Bu ölçüm
  **rejimler arası genelleme yapamaz** ve iddia da etmez.

---

## 4. RAPORLANACAK NİCELİKLER (sıra sabit)

1. Kapsama: sembol · saatlik gözlem · pencere · eşleşen getiri sayısı.
2. **ANA SORU:** `d` beş bandı × ortalama `ileri` · Spearman ρ ·
   uç bantlar farkı (bant5 − bant1) · **gün-kümeli %95 GA**.
3. 🔴 **UÇ DEĞER DENETİMİ (zorunlu, aşağıya bak):** aynı tablo **medyan** ile
   ve **%1-%99 kırpılmış ortalama** ile.
4. Paralel kol — **seviye `tl`** aynı makine ile. ⚠ §5'e göre **güçsüz**;
   hüküm doğurmaz, yalnız kayda geçer.
5. Paralel kol — **`d8` = 8 saatlik kayma**, ufuk 8 saat. ⚠ Sınırda güçlü.
6. Sağlamlık: top-3 sembol çıkarılmış sürüm · ilk yarı / ikinci yarı ayrımı.

### 🔴 Neden uç değer denetimi ZORUNLU

Marjinallerde ölçüldü: `sd(1s getiri) = %1,475` ama `sd(24s getiri) = %15,736`.
Rastgele yürüyüşte oran **√24 = 4,9** olmalıydı; gerçekleşen **10,7**.
Yani dağılım birkaç uç hareketin egemenliğinde. Ortalama temelli bant kıyası
bu koşulda **tek bir coin'in tek bir gününü** ölçebilir. Medyan ve kırpılmış
ortalama bu yüzden ana tabloyla **birlikte** raporlanır.

⚠ **Üçü çelişirse hüküm "belirsiz"dir**, en hoşa gideni seçilmez.

---

## 5. 🔴 GÜÇ HESABI (EK 4 zorunluluğu — donmadan önce yapıldı)

Ölçülen girdiler: sembol başına **394,6** bağımsız gözlem (bütünleşik
otokorelasyon süresi ~1,8 saat, 708 saatlik pencere) · **28 sembol**, kripto
birlikte hareket ettiği için muhafazakâr **2,5 etkin bağımsız sembol** →
`n_eff ≈ 986`, bant başına **~197**. `sd(1s ileri getiri) = %1,475`.

```
SE(uç bant farkı) = 1,475 × sqrt(2/197) = %0,149
%95'te saptanabilir en küçük fark = 1,96 × 0,149 = %0,29
```

**Zorunlu cümle:** *n≈986 bağımsız birim ve sd=%1,475 ile ancak **%0,29**
büyüklüğünde bir bant farkını görebiliriz. Aradığımız ekonomik eşik %0,5 (§6)
bunun ÜZERİNDE — test aradığımız etkiyi bulabilecek güçtedir. Bundan küçük bir
etki varsa göremeyiz; o durumda "yok" değil, **"ölçülemedi"** denir.*

⚠ **Seviye kolu (madde 4.4) için aynı cümle olumsuzdur:** sembol başına 1,7
bağımsız gözlemle `n_eff ≈ 4`. **Hiçbir etki büyüklüğü saptanamaz.** O kol
sonuç ne olursa olsun **"ölçülemedi"** hükmü alır ve bu şimdiden yazılıdır.

---

## 6. 🔴 KARAR KURALI — sonucu görmeden yazılıyor

Maliyet dayanağı (ölçülmüş): gidiş-dönüş taker **%0,13**; uç bantlarda
uzun-kısa iki bacak **%0,26**. Eşik **%0,5** = maliyet + benzer büyüklükte pay.
(basis ön kaydıyla aynı eşik — karşılaştırılabilirlik için bilinçli.)

| Bulgu | Sonraki adım |
|---|---|
| Bantlar monotonik (\|ρ\|≥0,8) **VE** uç fark ≥ **%0,5** **VE** GA sıfırı dışlıyor **VE** medyan/kırpılmış aynı yönü gösteriyor | ✅ Mekanik aşaması için AYRI ön kayıt |
| GA sıfırı dışlıyor ama uç fark **%0,26–0,5** | ⚠ İstatistiksel var, **ekonomik yok.** Mekanik YAZILMAZ |
| Ortalama geçiyor ama **medyan/kırpılmış geçmiyor** | ❌ **UÇ DEĞER ESERİ.** Bulgu sayılmaz |
| GA sıfırı kapsıyor | ❌ Bilgi yok |

⚠ **%0,5'i geçmek "kârlı" demek DEĞİLDİR.** B1'in ham bant farkı %2,06'ydı ve
mekanik uygulanınca −0,327R oldu (`be56b77`). Eşiği geçmek yalnız
*"mekaniği ölçmeye değer"* anlamına gelir.

⚠ **Tek rejim şerhi:** 29,5 gün tek dönemdir. Geçse bile hüküm
*"bu dönemde"* kaydıyla yazılır ve ileri-zamanlı doğrulama gerektirir.

---

## 7. BEKLENTİ (dürüstlük kaydı — sonuç görülmeden)

**Zayıf ya da hiç bulamayacağımızı bekliyorum.** Gerekçe: 14 aday öldü, basis
4 yılda hiçbir şey taşımadı, ve `top_ls` da sonuçta **aynı bandın** bir
ölçüsü — Binance perp'te gerçekleşmiş pozisyonlanma. Madde 7.4'ün "bant dışı"
tanımına tam girmiyor: emir defteri **niyeti** ölçer, `top_ls` **gerçekleşmiş
pozisyonu**. Yani gerçek bant dışı aday hâlâ derinliktir.

**Kendime karşı argüman:** `d` bir **akış** değişkeni, seviye değil. Büyük
hesapların pozisyon *kaydırması*, fiyat oluşmadan önceki bir karardır ve
kalabalığın (`ls`) tersine hareket ediyorsa bilgi taşıyabilir. Ayrıca bu
aday hiç düzgün sınanmadı (n=30) — "önceden öldü" diyemeyiz.

---

## 8. GEÇERSİZLİK KOŞULLARI

- §2 tanımları (özellikle `d`'nin ileri-bakışsız üretimi) değişirse
- §3 sembol şartı (≥20 gün) sonuç görüldükten sonra oynatılırsa
- §6 eşikleri (%0,5 · %0,26 · ρ 0,8) sonradan değiştirilirse
- Uç değer denetimi (§4.3) rapordan çıkarılırsa
- Bantlar sembol içi yerine havuzlanmış kesilirse

---

## 9. ÖLÇÜM

`onkayit_topls.py` — **salt okurdur**, canlı hiçbir dosyaya yazmaz, çalışan
süreçlere dokunmaz. Bu commit'ten **sonra** yazılır, ayrı commit'lenir.

---

# SONUÇ — **POZİSYON KAYMASI DA BİLGİ TAŞIMIYOR** (2026-09-01)

**Örneklem:** 28 sembol · **19.852** saatlik gözlem · 30 takvim günü.

## Ana kol — §6 karar kuralı devreye girdi

```
  d1 -> 1 saatlik ileri getiri
  ortalama   +0,063  +0,031  +0,049  +0,080  +0,073   uc fark +0,010%
  MEDYAN     +0,000  +0,000  +0,000  +0,010  +0,022           +0,022%
  KIRPILMIS  +0,043  +0,021  +0,022  +0,060  +0,054           +0,012%
  gun-kumeli GA95  [-0,083%, +0,091%]        rho = +0,600
```

**GA sıfırı kapsıyor → bilgi yok.** ρ=0,600, eşiğin (0,8) altında.

Ve GA'nın üst sınırı **+0,091%**, ekonomik eşiğin (%0,5) çok altında →
basis'te olduğu gibi bu **kanıt yokluğu değil, yokluğun kanıtı** (o büyüklükte).

## Sağlamlık kolları aynı yeri gösteriyor — biri daha da sert

| kol | uç fark | GA95 |
|---|---|---|
| top-3 çıkarıldı | **−0,048%** (işaret DÖNDÜ) | [−0,137, +0,038] |
| ilk yarı | −0,018% | [−0,073, +0,036] |
| ikinci yarı | −0,017% | [−0,210, +0,140] |

🔴 **Top-3 çıkarılınca uç farkın işaretinin dönmesi belirleyici:** ana koldaki
+0,010%'luk fark birkaç sembolde yoğunlaşmış gürültüydü, düzenlilik değil.

## §5'in "ölçülemedi" hükmü aynen uygulandı

Seviye kolu (`top_ls`) **sonucu görülmeden** güçsüz ilan edilmişti
(sembol başına 1,7 bağımsız gözlem → `n_eff ≈ 4`). Koşumda uç farkı +0,057%
çıktı ve GA'sı [−0,020%, +0,136%] oldu. **Bu sayılar hüküm doğurmaz** —
ön kayıt bunu peşinen yazmıştı. **Seviye hâlâ ÖLÇÜLMEMİŞTİR.**

## 8 saatlik kol — en büyük nokta tahmini, ama bulgu değil

Uç fark **+0,380%** (şimdiye kadarki en büyük), ama GA [−0,296%, +1,075%]
sıfırı kapsıyor ve bantlar monotonik değil (ρ=0,600; ortada çukur var).
§6'nın ilk satırının **üç şartından ikisi** karşılanmıyor. Bulgu değildir.

## ⚠ GÜÇ HESABI ÖNGÖRÜLENDEN İYİ ÇIKTI — dürüstlük kaydı

§5 saptanabilir en küçük farkı **%0,29** öngörmüştü; gerçekleşen GA
yarı-genişliği **%0,087** — yaklaşık **3,3 kat dar**. İki açıklama var ve
**ayrıştıramıyorum**:
1. "2,5 etkin bağımsız sembol" varsayımım fazla muhafazakârdı, ya da
2. gün-kümeli bootstrap **yalnız 30 blokla** belirsizliği olduğundan az gösteriyor.

⚠ **Muhafazakâr okuma seçiliyor:** saptama tabanı olarak §5'in **%0,29**
rakamı kullanılır. Hüküm iki okumada da aynı: %0,5'lik bir etki yok.

## 🔴 BU ADAYIN DURUMU

| biçim | hüküm |
|---|---|
| **1 saatlik kayma (`d1`)** | ❌ **ÖLÇÜLDÜ, BİLGİ YOK** — yeterince güçlü test |
| 8 saatlik kayma | ❌ GA sıfırı kapsıyor, monotonluk yok |
| **seviye (`top_ls`)** | ⚠ **HÂLÂ ÖLÇÜLMEDİ** — yıllarca arşiv ister, ölü DEĞİL |

📌 **Sayım düzeltmesi:** `top_ls` bu sabah ölü listesinden **çıkarılmıştı**
(yanlış sınıflanmıştı, n=30 ile "ölçülemedi"ydi). Şimdi **gerçek bir gerekçeyle**
geri giriyor — ama yalnız **kayma biçimiyle**. Seviye biçimi listede değildir.

## Sıradaki

Arşivleme **sürüyor** (günlük, ücretsiz): seviye biçimi ancak yıllarca birikimle
sınanabilir, önceliği düşük ama kapı açık tutuluyor.

**Bant dışı gerçek aday hâlâ emir defteri derinliği** — §7'de koşumdan önce
yazıldığı gibi: *"top_ls de sonuçta aynı banttan (gerçekleşmiş pozisyonlanma);
emir defteri ise NİYET ölçer."* Verisi 2026-08-31'den beri toplanıyor.
