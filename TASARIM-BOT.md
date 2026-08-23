# TASARIM KARARI — Kâğıt İşlem Botu + Arayüz (2026-08-20)

> **Bu belge nedir:** Ürün hedefinin değiştiği ve yeni mimarinin kararlaştırıldığı oturumun
> kaydı. **Yeni oturum önce bunu, sonra `SISTEM.md`'yi okumalı.**
> Buradaki kararlar tartışıldı ve onaylandı; yeniden türetilmesine gerek yok.

---

## 🔴 EK NOT — 2026-08-23: BU BELGENİN VERİSİ ESKİDİ, ÖNCE BUNU OKU

Bu belge 20 Ağustos'ta, **"K2 haklı olarak geçilemedi (33 işlem, −15,19R, PSR %4,7 →
kayıp sistematik)"** verisine dayanarak yazıldı. Üç gün sonra tablo değişti:

| Ölçüt | 20 Ağu (bu belgenin dayanağı) | 23 Ağu |
|---|---|---|
| İşlem | 33 | **39 — K2 kapısı AŞILDI** |
| Net | −15,19R | **−5,92R** |
| PSR (gerçek Sharpe>0 olasılığı) | %4,7 | **%26,4** |
| Bootstrap %95 GA | [−0,842, −0,029] | **[−0,591, +0,299]** ← sıfırı kapsıyor |

**Sebep: 20-23 Ağustos, sistemin ölçüm tarihindeki İLK GERÇEK BOĞA** (BTC +%10,8/3g,
ZEC +%44,2, SOL +%10; korelasyon 0,69 = sağlıklı, kontajyon yok). Çekirdek o üç günde
**6 işlem, 5 kazanç, +9,27R — hepsi LONG.**

**Ne değişti:** "kayıp sistematik" hükmü çöktü. Yerine geçen hüküm *"kazandığı da
kaybettiği de kanıtlanamıyor"* (net hâlâ negatif).

**⚠ Ne DEĞİŞMEDİ:** 6 işlem / 3 gün / tek ve çok elverişli rejim. +1,545R/işlem
sürdürülebilir değil; boğada yukarı kırılımın çalışması neredeyse totolojik. Bu proje
14 kez "buldum" deyip çöken bulgu gördü. **Gerçek sınav: boğa bitince ne olacağı.**

**✅ Boğada BİLE doğrulanan tek sağlam bulgu: SHORT çalışmıyor** (radar boğada SHORT
0/4, −4,19R; tüm geçmişte de negatif; F&G sınavının kazancı da tamamen "aşırı korkuda
satmayı engellemek"ten geliyordu — üç bağımsız kaynak aynı yeri gösteriyor).

**Yeni oturumun ilk işi:** §1'deki pivot kararını (sinyal sistemi → kâğıt bot) bu güncel
tabloyla yeniden tartmak. Karar yanlış olmayabilir — ama gerekçesi artık geçerli değil,
yeniden gerekçelendirilmeli. Ayrıntı: hafızadaki `bekleyen-isler-defteri.md` en üst bölüm.

---

## 1. ÜRÜN HEDEFİ DEĞİŞTİ

**Eski hedef (14 aday, K2 kapısı):** *"Sistem sinyal üretir, kullanıcı uygular."*
Bu üründe sistemin **kanıtlanmış öngörü gücü** olmak zorundaydı. K2 haklı olarak geçilemedi
(33 işlem, −15,19R, PSR %4,7 → kayıp sistematik).

**Yeni hedef (kullanıcının 2026-08-20 tarifi):**
> *"Bir işlem botu istiyorum. Sanalda kendi işlemine girsin çıksın — long, short, kaldıraçlı.
> Ben bunları temiz ve detaylı bir arayüzden takip edeyim, parametrelerle manuel oynayıp
> değişiklik yapabileyim."*

Ek olarak kullanıcı şunu vurguladı:
> *"Ben bir kumar aracı kurmak istemiyorum. Belirli bir riski göze alarak coin piyasasında
> işlem yapacağım, bana analizleriyle destek olacak bir sisteme ihtiyacım var."*

**İşlem biçimi:** spot **ve** vadeli birlikte.
**Gerçek para hedefi:** boğa piyasası geldiğinde hazır olmak.

---

## 2. MİMARİ KARARI — "yeni çekirdek nesne, mevcut katmanlar"

Kod tabanı ölçüldü (2026-08-20):

| Kategori | Satır | Pay |
|---|---|---|
| **Aynen kullanılır** — veri, göstergeler, rejim/makro, ölçüm+sınav, altyapı | 6.846 | **%79** |
| Parçalı — çözme motoru + maliyet modeli | 1.108 | %13 |
| Yeniden yazılır — pozisyon döngüsü | 727 | %8 |

**Karar: sıfırdan kurulmayacak, `defter.py` de revize edilmeyecek. Yeni çekirdek nesne
ayrı yazılacak.**

Gerekçe: `defter.py`'nin çekirdek nesnesi bir **tahmin**, yeninin çekirdek nesnesi bir
**pozisyon**. `defter.py` şunların hiçbirini taşımıyor (2026-08-20'de kodda doğrulandı):
`leverage` · `miktar` · `notional` · `funding_odenen` · `likidasyon_fiyati` ·
`spot/vadeli` · `kismi_cikis`. Bunları mevcut şemaya zorlamak melez ve kırılgan olur.

### Dokunulmaz (mevcut ölçüm sistemi çalışmaya devam eder)
`defter.py` · `radar_defter.py` · `izleyici.py` · `radar.py`

### Yeni yazılacak
| Modül | İş |
|---|---|
| `pozisyon.py` | Pozisyon nesnesi + simülatör: spot/vadeli, kaldıraç, **funding ödemeleri**, **likidasyon fiyatı**, gerçek komisyon+spread. Kendi defteri: `bot-defter.json` |
| `strateji/` | Eklenti arayüzü. Strateji = `f(snapshot, portfoy) -> emirler`. Mevcut sıkışma skoru **bir eklenti** olur (ve arayüz onun ölü olduğunu gösterir) |
| `bot.py` | Pozisyon yöneten döngü |
| `panel.py` | HTML arayüz (`radar_defter.py`'nin HTML üretimi emsal) |
| `atolye.py` | Config atölyesi + deneme sayacı + terfi kapısı |

### Import edilir, KOPYALANMAZ
`olcucu` · `makro` · `rejim` · `metrikler` · `backtest` · `ileritest` · `kalibrasyon` · `spread_olcum`

⚠ **Özellikle `defter.py`'nin ÇÖZME MOTORU import edilecek, yeniden yazılmayacak.**
(kapanmış 1dk mum, fitil semantiği, aynı mumda stop+TP → temkinli STOP). O mantık aylarca
düzeltildi; yeniden yazmak bu projenin yapabileceği en pahalı hatadır.

---

## 3. ⛔ TARİHLİ KISIT — 2026-09-06'ya kadar

`ON-KAYIT-radar-v2.md` **şu anda açık** ve §6'sı diyor ki: *"kanonik süzgeç tanımı
değişirse test iptal."*

**`defter.py` veya `radar_defter.py`'ye dokunmak koşan testi GEÇERSİZ KILAR.**

Yeni modüller ayrı yazıldığı için bu sorun doğmuyor — ama yeni oturum bunu bilmezse
"şunu da temizleyeyim" diye dokunabilir. **Dokunma.**

Aynı sebeple `olcucu.log` akışı ve radar süreci kesilmemeli: Aralık'taki likidasyon
doğrulaması (D1) o pencerenin birikmesine bağlı.

---

## 4. 🔴 ATÖLYENİN GÜVENLİKLERİ — PAZARLIK KONUSU DEĞİL

Bu bölüm belgenin en önemli kısmı. Yeni oturum bunu okumadan atölyeyi yazmamalı.

**Tehlike:** parametre oynatma arayüzü, aşırı-uydurma makinesidir. Kullanıcı parametreleri
değiştirir, sanal P&L anında güncellenir, iyi görünen bir kombinasyon bulur, "buldum" der.

**Bu projede bu tam 14 kez oldu.** İki somut vaka:
- **Kesitsel momentum** ham haliyle **+%4,5/hafta** gösterdi — maliyetin 36 katı, iki rejimde
  de pozitif. Yoğunlaşma + medyan + hayatta kalma kontrolü eklenince ÇÖKTÜ.
- **F&G kapısı** aylarca "en güçlü aday" diye taşındı. Beş şartlı sınavda **4/5 ile** düştü.

O 14 test günler sürdü ve ön kayıtlıydı. **Arayüzle bir öğleden sonrada 100 kombinasyon
denenebilir** — ve 100 denemede en iyisinin şans eseri parlak görünmesi neredeyse garantidir.

**Yanlış kurulursa bu araç, aylarca kurulan disiplini bir haftada yok eder.**

### Arayüzde DAİMA görünecekler

| Zorunlu öğe | Neden |
|---|---|
| **"Bugüne kadar N config denendi"** sayacı | 40 deneme sonrası en iyiyi seçmek seçim değil şanstır. Sayı gözün önünde dursun |
| **Gürültü tabanı çizgisi (0,03R)** | Altındaki farklar görsel olarak EŞİT gösterilsin |
| **Bootstrap %95 güven aralığı** — asla tek sayı değil | "+0,3R" değil, "+0,3R [−0,1, +0,7]" |
| **PSR** (gerçek Sharpe > 0 olasılığı) | `metrikler.py`'de hazır |
| **"Ön kayıtlı mı?"** rozeti (kırmızı/yeşil) | Ön kayıtsız hiçbir config "onaylı" görünmesin |
| **Terfi kapısı** | Bir config'in aday olması için walk-forward + 5 şart zorunlu |

**Parametre oynatmak YASAK DEĞİL** — öğrenmek için değerli. Yasak olan, oynamanın sonucunu
**kanıt saymak.** Arayüz bu çizgiyi görünür kılmalı.

---

## 5. GERÇEKÇİLİK ŞARTLARI (simülatör yalan söylememeli)

- **Funding ödemeleri modellenecek.** Boğada funding tavana yapışır — 2026-08-20 ölçümü:
  BTC/ETH/SOL üçünde de %0,0100, kendi son 500 ödemesinin **100. persentili**. Yani boğada
  vadelide long tutmak **sürekli maliyet**tir. Modellenmezse sanal kâr yalandır.
- **Likidasyon fiyatı** hesaplanacak ve tetiklenecek.
- **Maliyet:** spot taker ≠ vadeli taker. Ölçülmüş spread (`spread_olcum.py`): medyan
  %0,021–0,028; mevcut kayma varsayımımız (%0,02) gerçeğin 1,4–1,9 katı = muhafazakâr.
- **Spot ve vadeli AYRI takip**, toplam risk birleştirilerek gösterilecek.
- **Gap/kayma** (E1) hâlâ ölçülmedi — simülatör bu konuda iyimser olduğunu BELİRTMELİ.

---

## 6. K3 KAPISI YENİDEN TANIMLANMALI

Mevcut K3: *"30+ işlem net pozitif olana kadar gerçek para yok"* — **botun** kenarını şart
koşuyor. Yeni ürün için doğru kapı:

> **Risk altyapısı kanıtlanana kadar gerçek para yok:** boyutlama doğru çalışıyor,
> maliyetler gerçek ölçülmüş (funding + gap dahil), limitler fiilen ateşliyor,
> ve N kâğıt işlem aynı disiplinden geçmiş.

⚠ Bu, "edge şartı kalktı" demek DEĞİL. Bot bir strateji öneriyorsa o stratejinin sınavı
hâlâ 5 şarttır. Kapı, **altyapı** için yeniden tanımlandı.

---

## 7. SIRA (bozulmamalı)

| # | İş | Tahmin |
|---|---|---|
| 1 | `pozisyon.py` — simülatör çekirdeği + gerçekçi maliyet | 2-3 gün |
| 2 | `panel.py` — HTML arayüz (açık pozisyonlar, equity, işlem defteri) | 2 gün |
| 3 | `atolye.py` — config atölyesi + **deneme sayacı** + güven aralıkları | 2 gün |
| 4 | Terfi kapısı (walk-forward + 5 şart) | 1 gün |

⚠ **3'ü atlayıp parametre oynatmaya başlamak, aracı kumar makinesine çevirir.**
Kullanıcının açıkça istemediği şey tam olarak budur.

---

## 8. AÇIK SORU

**Bot hangi stratejiyle başlasın?**
- (a) Mevcut sıkışma skoru — "çalışan bir şey görmek" için iyi ama sonuç baştan negatif
  (964k kayıtla ölü olduğu ölçüldü)
- (b) Basit/şeffaf bir başlangıç (ör. trend takibi) — ama bu da sınanmamış bir aday
- (c) Önce simülatörü kur, strateji seçimini sonraya bırak

Kullanıcıya soruldu, cevap bekliyor.

---

## 9. YENİ OTURUM İÇİN OKUMA SIRASI

1. **Bu belge** (ürün hedefi + mimari + güvenlikler)
2. `SISTEM.md` §9.9, §9.10, §11 (ne ölçüldü, ne ayakta, anlık durum)
3. `ON-KAYIT-radar-v2.md` (koşan test — **dokunma**)
4. Hafıza: `bekleyen-isler-defteri.md` (A-G + 12 ders)

**Üç şeyi doğrulamadan kod yazma:** (1) hayatta kalan bulgu sıfır, (2) eleme yöntemi
kabul edilmiş değil sınanıyor, (3) `defter.py`/`radar_defter.py` 2026-09-06'ya kadar
dokunulmaz.
