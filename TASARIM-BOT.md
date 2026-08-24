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

**✅ BU GÖREV YAPILDI (2026-08-23 akşam).** Pivot güncel veriyle yeniden tartıldı:
**karar korundu, gerekçesi baştan yazıldı, sırası değiştirildi.** §1 ve §7 güncellendi;
§8'in açık sorusu (c) olarak kapatıldı. Bu notu tekrar açma — aşağısı zaten güncel.

---

## 1. ÜRÜN HEDEFİ DEĞİŞTİ

**Eski hedef (14 aday, K2 kapısı):** *"Sistem sinyal üretir, kullanıcı uygular."*
Bu üründe sistemin **kanıtlanmış öngörü gücü** olmak zorundaydı.

### ⚠ 2026-08-23: GEREKÇE BAŞTAN YAZILDI — eskisi çöktü, karar korundu

**Çöken gerekçe (20 Ağu):** *"K2 haklı olarak geçilemedi (33 işlem, −15,19R, PSR %4,7 →
kayıp sistematik)."* **Bu cümle artık kullanılamaz.** 23 Ağu ölçümü: 39 işlem, −5,92R,
PSR %26,4, bootstrap %95 GA [−0,579, +0,295] → sıfırı KAPSIYOR. Hüküm "kayıp sistematik"
değil, **"belli değil"**.

⚠ Ama bu bir terfi değil, **hükümsüzlük**. K2'nin şartı "30+ işlem **net pozitif**"ti;
sayaç doldu (39), net hâlâ negatif. Kapı geçilmedi — sadece kesin kalınmış olmaktan çıktı.
Yani ne eski gerekçe ("kanıtlanmış kaybediyor") ne de tersi ("kanıtlanmış kazanıyor")
ayakta. **Pivot bu boşluktan yeniden gerekçelendirildi:**

**G1 — Bozuk olan tahmin değil, ÖLÇÜ ALETİ.** Sicil R-katı ölçüyor; funding ve likidasyon
hiç modellenmiyor. Bu projede "kârlı mı" sorusunun cevabını en az bir kez tahmin değil
maliyet modeli belirledi — 2026-08-23'te ana sicil konfige göre ayrıştırıldı:

| Konfig | n | brüt | maliyet | net | maliyet/işlem |
|---|---|---|---|---|---|
| swing-1h | 39 | −3,33R | 2,56R | −5,89R | 0,066R |
| 5dk dönemi (eski) | 30 | **+11,15R** | **14,82R** | **−3,67R** | **0,494R** |

5dk dönemi **brüt kârlıydı**, maliyet %133'ünü yedi. Eksik olan öngörü değil, muhasebe.

#### 🔴 G1 DÜZELTİLDİ (2026-08-23 akşam, `pozisyon.py` ilk koşusu)

G1 ilk yazıldığında şöyle diyordu: *"funding üç majörde de tavanda → boğadaki LONG
kazançları kaldıraçlı gerçek pozisyonda sürekli maliyet öderdi ve sicil bunu görmüyor."*
**Simülatör kurulup gerçek veriyle koşturulunca bu yanlış çıktı.** Boğada kapanan
**16 gerçek radar LONG'u**, gerçek 1dk mumları ve gerçek funding ödemeleriyle
(`/fapi/v1/fundingRate`, gerçek ödeme anları) yeniden koşuldu:

| 1x vadeli, risk %1, bakiye 1000 | |
|---|---|
| Sicilin R-katı hükmü | **+11,69R** |
| Tam USD muhasebesi (funding + komisyon dahil) | **+11,536R** (1000 → 1115,36) |
| **Sicilin görmediği kısım** | **−0,154R toplam = −0,0096R/işlem** |
| — funding bileşeni | **+0,147R** (POZİTİF: LONG'lar funding ALDI) |
| — komisyon bileşeni | −0,298R |
| funding alan / ödeyen pozisyon | **4 / 10** |

**Neden yanlıştı:** §5'in ölçümü BTC/ETH/SOL üzerindeydi ve orada funding tavandaydı.
Ama radar **altcoin** işliyor ve o altcoinler boğada yoğun biçimde SHORT'lanıyordu →
funding **negatif** → LONG tutan **para aldı** (ACEUSDT: 13 ödeme, %−0,24'e varan oran,
+1,96 USD). **Funding'in işareti rejime değil SEMBOLE bağlı.** "Boğada long tutmak
sürekli maliyettir" cümlesi majörler için doğru, radar evreni için yanlıştı.

**G1'in ayakta kalan hâli — kaldıraç, funding değil.** Aynı ACEUSDT işlemi kaldıraçla:

| kaldıraç | sonuç | net R |
|---|---|---|
| 1x / 2x / 5x | tp1 | **+2,270R** |
| **10x** | **LİKİDASYON** (liq 0,1859, stop 0,1757'ye gelmeden) | **−0,654R** |
| **20x** | **LİKİDASYON** (liq 0,1961) | −0,297R |

Sicilin **+2,08R kazanç** yazdığı işlem, 10x'te **kayıp**tır. Sicil bunu göremez, çünkü
sicilde likidasyon fiyatı diye bir kavram yok. Ayrıca 1x/2x/5x'in **aynı** çıkması
tesadüf değil: risk-tabanlı boyutlamada kaldıraç, likidasyona yol açmadığı sürece
sonucu HİÇ değiştirmez — yalnız bağlanan teminatı değiştirir.

**Yani G1 şuna daralır:** sicil, mevcut 1x boyutlamada yalan söylemiyor (fark 0,01R/işlem).
Yalan, **kaldıraç devreye girdiğinde** başlıyor — ve ürün hedefi tam olarak "kaldıraçlı
işlem" olduğu için bu boşluk ürünün merkezinde. `pozisyon.py` bunu kapatıyor.

⚠ Örneklem: 16 işlem, tek rejim, tek yön. Genelleme değil, ölçüm.

**G2 — Kanıtlanmış pozitif hücre hâlâ YOK.** Boğa ayrıştırılınca (23 Ağu ölçümü):
radar LONG **boğa öncesi** n=73, +0,168R/işlem, GA [−0,168, +0,513] → **sıfırı kapsıyor.**
Boğadaki +9,27R'lik çekirdek kazanç 6 işlemden geliyor. Sinyal ürünü kanıtlanmış pozitif
ister; simülatör istemez — simülatör bir **alettir**, ve şu an bozuk olan tam da alet.

**G3 — Sistem, kanıtlanmış KAYBEDEN yöne eğilimli.** SHORT iki rejimde birden sıfırın
altında: radar SHORT boğa ÖNCESİ (kendi lehine olan rejimde) n=48, −0,378R/işlem,
GA [−0,696, −0,020] **sıfırı dışlıyor**; boğada da kaybetti.

⚠ **2026-08-23 AKŞAM DÜZELTMESİ — bu madde ilk yazıldığında ABARTILIYDI.** İlk hâli
*"ön kayıttan beri 103 tahmin: LONG 30 / SHORT 73"* diyordu; o bir **5 günlük pencereydi**
ve genel özellik gibi sunulmuştu. Tüm canlı dönem:

| Sicil | Üretilen tahmin | SHORT payı | Aylık seyir |
|---|---|---|---|
| **Ana** | 159 | **%79** | Haz %95 → Tem %83 → Ağu %63 |
| **Radar** | 360 | **%52** | Tem %47 → Ağu %55 |

**Radar dengeli; yapısal short eğilimi YOK** — ve radar hacmin çoğu. Hüküm ana sicil
için doğru, radar için değil.

**Madde yine de ölmüyor, çünkü fark MEKANİZMAYLA TUTARLI:** short'a yapışık sicil
(ana %79) daha çok kaybetti (−9,57R); dengeli sicil (radar %52) daha az (−7,92R,
sonra boğayla +0,86R). Mekanizma 23 Ağu denetiminde ölçüldü — `SISTEM.md` §12 madde 6-7.

**Değerlendirilen ve reddedilen ucuz alternatif:** *"SHORT kanıtlanmış negatifse,
5 modül yazma, SHORT'u kapat"* — sicildeki etkisi büyük görünüyor (radar +0,86R → +23,62R).
**Reddedildi, çünkü bu tam olarak koşan ön kaydın test ettiği kuraldır** (`LONG + ACIK`,
23 Ağu'da 12/30). Şimdi uygulamak testi öldürür. Ucuz alternatif zaten sınanıyor;
pivotun yerine geçemez.

**G4 — ASIL GEREKÇE (2026-08-23 akşam denetimi): sistem, HİÇBİR ŞEY YAPMAMAYI geçemiyor.**
Bu proje iki ay boyunca "hangi sinyal işe yarıyor" diye sordu; "alıp tutmaya kıyasla ne
yaptı" diye hiç sormadı. Ölçüldü:

| Aynı pencere | Sistem | BTC al-tut | 10 coin eşit al-tut |
|---|---|---|---|
| Ana (28 Haz →) | **−%9,6** | +%28,5 | +%45,3 |
| Radar (10 Tem →) | +%0,9 | +%19,9 | +%30,5 |
| **Maks düşüş** | **−%22,6 … −%25,3** | **−%7,0** | — |

Sistemin **en iyi alt kümesi** bile (radar LONG-only +%23,6 — 21 hipotez sonrası
seçilmiş, kanıt değil) sepeti geçemiyor. Maliyeti yılda %30-35; al-tutunki ~%0.

⚠ Ayrıca: BTC canlı ölçümün ilk gününden beri **hiç düşmedi** (60.044 → 77.184; boğa
etiketinden ÖNCE bile +%15,6). "Düşen/testere rejim" tarifi 540 günlük *backtest*
penceresine aitti ve canlı pencereye yanlışlıkla taşınmış. Sistem, **koşulların en
elverişli olduğu dönemde** kaybetti.

**Bundan sonraki tek geçerli kıstas:**
> *Alıp tutmaktan daha iyisini yapmak — maliyetten sonra, daha az düşüşle.*

"Zarar etmemek" kıstas değildir: hiçbir şey yapmayarak zaten sağlanıyor ve şu an
sistemden daha iyi. `panel.py` bu kıstası her rakamın yanında gösterecek.

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

## 1.5 🔴 BAĞLAYICI ÇALIŞMA KURALLARI (kullanıcı, 2026-08-23)

Bu altı kural bu aşamanın tamamı için bağlayıcıdır. Yeni oturum bunları okumadan
kod yazmamalı.

| # | Kural | Durum |
|---|---|---|
| 1 | **DONDURULMUŞ DOSYALAR:** `defter.py` ve `radar_defter.py`'ye dokunma. `izleyici.py` ve `radar.py` süreçlerini durdurma. Ön kayıt kapanana kadar. | ✅ uyuldu — git diff sıfır |
| 2 | **ÇÖZME MOTORUNU YENİDEN YAZMA:** `defter.coz()` ve `k1m_kapanmis()` import edilecek, kopyalanmayacak. | ✅ uyuldu — `pozisyon.py` yalnız import eder |
| 3 | **SİMÜLATÖR DOĞRULANACAK:** geçmiş kapanmış işlemler üzerinde koştur; funding ve likidasyon KAPALIYKEN mevcut net-R'yi **birebir** üretmeli. Üretmiyorsa motor bozuktur. | ✅ `pozisyon_dogrulama.py` — 211/211 + 32/32 |
| 4 | **YALAN SÖYLEMEYEN SİMÜLATÖR:** funding ödemesi, likidasyon fiyatı ve spot/vadeli maliyet farkı modellenmeden "çalışıyor" deme. | ✅ üçü de modelli |
| 5 | **PANEL TEK SAYI GÖSTERMESİN:** her P&L rakamının yanında bootstrap güven aralığı ve 0,03R gürültü tabanı görünsün. "+2,1R" değil, **"+2,1R [−0,4, +4,6]"**. | ⬜ `panel.py`'de uygulanacak |
| 6 | **ADIM ADIM:** bir modül bitince DUR, göster, onay al. İkisi bitince atölyeye geçme — ön kayıt kapansın. | ⬜ sürekli |

**Kural 4'ün gerekçesi (kullanıcının kendi sözü):** *"5dk döneminde brüt +11R'yi maliyet
tamamen yemişti, o hatayı tekrarlama."* Ölçüm §1'de: brüt +11,15R, maliyet 14,82R
(%133), net −3,67R.

**Kural 5'in gerekçesi:** §4'ün aşırı-uydurma uyarısının panele uygulanmış hâli. Tek
sayı, güven aralığı olmadan gösterildiğinde kanıt gibi okunur; bu projede tam olarak
böyle 14 aday ayakta kaldı.

---

## 1.6 GELİŞTİRME SIRASI — NET (kullanıcı, 2026-08-23)

1. **ÖNCE ÖLÇÜM:** `pozisyon.py`. **Strateji geliştirilmiyor, muhasebe düzeltiliyor.**
2. **K2 OTURUMU ERTELENDİ, İPTAL DEĞİL.** 14 maddelik gündem duruyor; ön kayıt kapanınca
   **doğru maliyet modeliyle** yapılacak. (`SISTEM.md` §12.)
3. **K2 gündemine yeni madde eklendi:** funding bileşeninin ayrım gücü (6 sembolde eşik
   tavana yapışmış → koşulsuz +30 puan → SHORT'a sabit eğilim). **Şimdi test edilmedi**,
   gündeme yazıldı. Ayrıntı: `SISTEM.md` §12 madde 6.

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

- **Funding ödemeleri modellenecek.** ✅ `pozisyon.py`'de yapıldı — gerçek ödeme anları
  `/fapi/v1/fundingRate`'ten alınır, 8 saatlik ritim **varsayılmaz** (ACEUSDT'de ölçüldü:
  4 saatlik, 54,7 saatte 13 ödeme; 8s varsayımı maliyeti ~2 kat yanlış hesaplardı).
  ⚠ **2026-08-23 DÜZELTMESİ:** bu maddenin eski hâli *"boğada vadelide long tutmak sürekli
  maliyettir"* diyordu. Ölçüm bunu ÇÜRÜTTÜ. O ölçüm (BTC/ETH/SOL, %0,0100 = 100. persentil)
  yalnız **majörler** içindi. Radar'ın işlediği altcoinlerde funding boğada **negatifti**
  (yoğun SHORT baskısı) → LONG tutan **para aldı**: 16 işlemde 4 alan / 10 ödeyen, net
  **+0,147R**. **Funding'in işareti rejime değil sembole bağlıdır** ve her iki yöne de
  gidebilir. Modellenmemesi hâlâ yalandır — ama yalanın yönü baştan bilinemez.
- **Likidasyon fiyatı** hesaplanacak ve tetiklenecek. ✅ `pozisyon.py`'de yapıldı
  (izole marjin, MMR varsayılan %1 = muhafazakâr). **Bulunan en önemli şey bu:** sicilin
  +2,08R yazdığı gerçek bir işlem 10x'te likidasyonla **−0,654R**'dir, çünkü likidasyon
  fiyatı stop'un İÇİNDE kalır. `uyarilar()` bunu pozisyon açılışında isimle bildirir.
  ⚠ Aynı mumda stop+likidasyon kuralı: `defter.coz`'un "aynı mumda stop+TP → temkinli
  STOP" kuralının **aynı-taraf** hâli — girişe yakın olan önce dolar (yol belirsiz değil).
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

**⚠ 2026-08-23'te DEĞİŞTİ — 3 ve 4 arasına sert bir durak kondu (kullanıcı onayladı).**

| # | İş | Tahmin | Durum |
|---|---|---|---|
| 1 | `pozisyon.py` — simülatör çekirdeği + gerçekçi maliyet | 2-3 gün | ▶ başlandı 23 Ağu |
| 2 | `panel.py` — HTML arayüz (açık pozisyonlar, equity, işlem defteri) | 2 gün | sırada |
| — | ⛔ **DURAK: `radar-v2` ön kaydı kapanana kadar İLERLEME YOK** | — | ~30 Ağu tahmini |
| 3 | **`strateji/`** — eklenti arayüzü: `f(snapshot, portfoy) -> emirler` | 1-2 gün | duraktan SONRA |
| 4 | **`bot.py`** — pozisyon yöneten döngü (`bot-defter.json`'a YAZAN tek şey) | 2 gün | duraktan sonra |
| 5 | `atolye.py` — config atölyesi + **deneme sayacı** + güven aralıkları | 2 gün | duraktan sonra |
| 6 | Terfi kapısı (walk-forward + 5 şart) | 1 gün | duraktan sonra |

🔴 **2026-08-24 DENETİMİ — 3 ve 4 SONRADAN EKLENDİ, PLANDA HİÇ YOKTULAR.**
§2 beş modül sayıyor ama §7'nin ilk hâli yalnız 4 madde içeriyordu ve `strateji/`
ile `bot.py` **hiç girmemişti.** Sonuç sessiz ve ağır olurdu: `pozisyon.py` bir
pozisyonu *hesaplayabilir* ama *yaratamaz* — `bot-defter.json`'a yazan hiçbir şey
olmazdı, panelin "Kâğıt Bot" bölümü sonsuza kadar boş kalırdı ve kullanıcının
istediği **kâğıt işlem botu hiç doğmazdı.** Simülatör ile arayüz arasındaki halka
eksikti. ⚠ Sıra önemli: `strateji/` önce gelir, çünkü `bot.py` ondan emir alır.

**Durağın gerekçesi (§4'ün kendi mantığının bu haftaya uygulanması):** §4 diyor ki
*"parametre oynatma arayüzü aşırı-uydurma makinesidir."* 20-23 Ağustos'ta ekranda
**projenin tarihindeki en baştan çıkarıcı P&L** duruyor: çekirdek 6 işlem, 5 kazanç,
+1,545R/işlem. Atölyeyi tam bu pencerede yazmak, güvenlikleri eksiksiz yazsan bile en
kötü zamanlamadır — çünkü aracın göstereceği İLK sayı bir boğa P&L'i olur ve o sayı
kalibrasyon noktası hâline gelir.

Durak beklendiğinde atölyenin gösterdiği ilk sayı **ön kayıtlı bir hüküm** olur.
Fark psikolojik değil yapısaldır: birincisinde araç "şuna bak ne güzel" diye açılır,
ikincisinde "işte kanıt böyle görünür" diye.

⚠ **3'ü atlayıp parametre oynatmaya başlamak, aracı kumar makinesine çevirir.**
Kullanıcının açıkça istemediği şey tam olarak budur.
⚠ **3'ü ERKEN yapmak da aynı kapıya çıkar.** Yeni kısıt: atölye, `radar-v2` hüküm
basmadan yazılmaz.

---

## 8. AÇIK SORU — ✅ KAPANDI (2026-08-23, kullanıcı kararı: **c**)

**Soru:** bot hangi stratejiyle başlasın? (a) mevcut sıkışma skoru · (b) basit/şeffaf bir
başlangıç (ör. trend takibi) · (c) önce simülatörü kur, strateji seçimini sonraya bırak.

**Karar: (c).** Strateji seçimi `radar-v2` testine bırakıldı.

**Gerekçe — 20 Ağu'da olmayan, 23 Ağu'da ortaya çıkan somut sebep:** veri bakılırsa
"LONG only" cevabı neredeyse kendiliğinden geliyor (SHORT iki rejimde de kanıtlanmış
negatif). Ama **"LONG + ACIK" tam olarak koşan ön kaydın kuralıdır.** Botu şimdi o
kuralın etrafında kurmak, testi önden yemek olur: kural henüz sınanırken ürünün
varsayımı hâline gelir, sonra test ne derse desin geri alınamaz.

Yani (c) yalnızca "temkinli" seçenek değil, **ön kaydı korumanın tek yolu.**

⚠ Bunun pratik sonucu: `pozisyon.py` **stratejiden bağımsız** yazılmalı. Simülatör
"hangi sinyal" bilmemeli; yalnızca *emir gelir → pozisyon açılır/kapanır → maliyet
işler* zincirini modellemeli. `strateji/` eklenti arayüzü bu yüzden 1. adımda değil,
ayrı bir katman olarak durur.

---

## 9. YENİ OTURUM İÇİN OKUMA SIRASI

1. **Bu belge** (ürün hedefi + mimari + güvenlikler)
2. `SISTEM.md` §9.9, §9.10, §11 (ne ölçüldü, ne ayakta, anlık durum)
3. `ON-KAYIT-radar-v2.md` (koşan test — **dokunma**)
4. Hafıza: `bekleyen-isler-defteri.md` (A-G + 12 ders)

**Üç şeyi doğrulamadan kod yazma:** (1) hayatta kalan bulgu sıfır, (2) eleme yöntemi
kabul edilmiş değil sınanıyor, (3) `defter.py`/`radar_defter.py` 2026-09-06'ya kadar
dokunulmaz.
