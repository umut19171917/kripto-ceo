# ÖN KAYIT — `maliyet`: bağlayıcı kısıt maliyet mi, yön mü?

**Yazım anı:** 2026-09-01 (koşumdan ÖNCE)
**Durum:** DONDURULDU. §2–§7 bu commit'ten sonra değiştirilmez.
**Şablon:** `ON-KAYIT-SABLON.md` (`ed4770d`)
**Öncülleri:** `8cdc9ef` (giriş — mekanik suçsuz) · `84d0c1a` (mutabakat) · `870ccb9` (ufuk fizibilitesi)

---

## 0. Bu ölçüm ne YAPAR, ne YAPMAZ

- ⛔ *"Şu stop'u kullan"* **diyemez.** Hiçbir parametre taranmayacak; tarama
  bu projede *"en iyi hücreyi seçmek"*tir ve yasaktır.
- ⛔ Kârlılık hükmü kuramaz.
- ✅ Cevapladığı: **(a)** kaybımızın ne kadarı maliyet, ne kadarı yön?
  **(b)** maliyet neden iki sicilde 6 kat farklı? **(c)** herhangi bir adayın
  net pozitif olabilmesi için gereken **en küçük brüt kenar** nedir?

🔴 **ASIL ÇIKTI BİR EŞİKTİR:** her gelecek ön kaydın §6'sına girecek olan
**maliyet tabanı**. Bugüne kadar adaylar *"bilgi var mı"* diye sınandı;
*"bilgi mekaniğin bedelini ödeyecek kadar büyük mü"* hiç sorulmadı.

## 1. Neden bu ölçüm — ve neden ŞİMDİ

`giris` ölçümü (`8cdc9ef`) giriş mekaniğini **akladı**. Geriye iki açıklama
kaldı: ham düzenlilik zaten yanlış yöndeydi **ya da** maliyet. Fizibilitede
(§5) görülen sayılar ikincisini işaret ediyor ve bu **hiç ölçülmedi**.

## 2. TANIMLAR (donduruluyor)

| büyüklük | tanım |
|---|---|
| `brut_R` | sicildeki `sonuc_R` (mevcut alan, yeniden hesaplanmaz) |
| `maliyet_R` | `defter.maliyet_R(t)` — **tek sahip** (madde 8.3) |
| `net_R` | `brut_R − maliyet_R` |
| `stop_pct` | `|giriş − stop| / giriş × 100` — maliyetin mekanik sürücüsü |
| **`taban_R`** | **`ortalama(maliyet_R)`** — net pozitif için gereken en küçük brüt kenar |

Örneklem birimi **işlem**; kümeleme **kapanış günü**. Tohum `olcum.TOHUM`.

🔴 **Maliyet DETERMİNİSTİKTİR:** giriş ve stop verildiğinde tam olarak
hesaplanır, tahmin değildir. Belirsizlik yalnız **brüt** taraftadır. Bu asimetri
hükmün merkezindedir.

## 3. ÖRNEKLEM

- **ANA SİCİL** (`kripto-defter.json`) ve **RADAR** (`radar-defter.json`),
  `durum ∈ {tp1, tp2, stop, zaman_asimi}` ve `sonuc_R` dolu olanlar.
- 🔴 **İki sicil AYRI raporlanır, TOPLANMAZ.** Farklı evren (11 major vs
  ~130 altcoin), farklı zaman dilimi, farklı oynaklık. Toplamak
  `kesitsel_test` dersindeki hatayı tekrarlar.
- ⚠ Geri-doldurma/backtest kayıtları ve `DENEYSEL` (LAB) semboller **hariç**
  (sicilin kendi ayrımı; bu ölçüme bakılarak seçilmedi).
- ⚠ **Hayatta kalma yanlılığı yok** (tüm kapanmış işlemler), ama
  **tek rejim** ve **tek dönem** sınırı var.

## 4. RAPORLANACAK NİCELİKLER (sıra sabit)

1. Kapsama: sicil başına n · kapanış günü sayısı.
2. **AYRIŞTIRMA:** brüt / maliyet / net — toplam ve işlem başına.
3. **Maliyet dağılımı:** ortalama · **medyan** · çeyrekler · en yüksek %10'un payı.
   ⚠ Ortalama birkaç dar-stop işleminden geliyorsa bu **görülmelidir**.
4. **BRÜT SIFIRDAN AYIRT EDİLEBİLİYOR MU:** brüt için gün-kümeli GA95 **ve**
   işaret permütasyonu p (`olcum.py` deseni — ikisi birden).
5. **SÜRÜCÜ:** `maliyet_R` ile `stop_pct` ilişkisi. ⚠ Bu **mekanik olarak
   zorunlu** bir ilişkidir (maliyet ∝ 1/stop_pct); **bulgu değil, doğrulamadır.**
   Amaç: iki sicil arasındaki 6 kat farkın stop genişliğinden mi geldiğini
   göstermek. Beklenen ilişki çıkmazsa **hesapta hata var** demektir.
6. **TABAN:** `taban_R` sicil başına. Ve şu karşılaştırma: bu taban, projenin
   **gürültü tabanı 0,03R**'nin kaç katı?
7. Sağlamlık: dönem ikiye bölünmüş · en pahalı %10 işlem çıkarılmış.

## 5. 🔴 GÜÇ HESABI

**Fizibilitede ölçüldü (2026-09-01) ve bu sayılar §6 yazılmadan ÖNCE görüldü:**

```
ANA SICIL  n=165  brut +2,50R (+0,0152R/islem)  maliyet 27,49R (0,1666R/islem)
RADAR      n=187  brut -11,53R (-0,0617R/islem) maliyet  5,22R (0,0279R/islem)
```

🔴 **Dürüstlük şerhi:** brüt toplamları **görüldü**. Bu yüzden §6'nın karar
kuralı *"brüt pozitif mi"* üzerine kurulamaz — o soru kirlendi. §6 bunun
yerine **kirlenmemiş** soru üzerine kuruludur: *brüt sıfırdan **ayırt
edilebiliyor mu**?* Bunun cevabı (GA ve p) henüz **hesaplanmadı**.

Güç: ana sicilde n=165, R'nin sd'si ~1,4 (proje teamülü), kapanış günü ~60 →
etkin birim ~60×1 (tek evren) → `SE ≈ 1,4/√60 = 0,181R` →
**saptanabilir en küçük brüt kenar ≈ 0,354R.**

**Zorunlu cümle:** *n=165, sd≈1,4R ile ancak **0,354R** büyüklüğünde bir brüt
kenarı sıfırdan ayırt edebiliriz. Gözlenen brüt 0,0152R/işlem bunun **23 kat
altında** — yani bu örneklemle brüt kenar **ölçülemez**. "Brüt pozitif" de
"brüt sıfır" da GÖSTERİLEMEZ.*

🔴 **Bu, hükmün kendisini belirliyor:** maliyet **kesin ve ölçülü**, brüt kenar
**ölçülemez**. Karar kuralı bu asimetri üzerine kurulur, brütün işareti üzerine
değil.

## 6. 🔴 KARAR KURALI — sonucu (GA/p) görmeden

| Bulgu | Sonuç |
|---|---|
| `taban_R` > saptanabilir brüt kenar (0,354R) | ❌ **Bu sicil yapısal olarak kârlı olamaz**: ödediği maliyet, ölçebileceğimiz en küçük kenardan büyük |
| `taban_R` ≤ 0,354R **ve** brüt GA sıfırı dışlıyor **ve** p<0,05 | ✅ Kenar var ve maliyeti karşılıyor olabilir → ayrı ön kayıt |
| `taban_R` ≤ 0,354R ama brüt GA sıfırı kapsıyor | ⚠ **BAĞLAYICI KISIT MALİYET DEĞİL BELİRSİZLİK.** Maliyet ödenebilir büyüklükte ama kenarın varlığı gösterilemiyor |
| Maliyet ortalaması en pahalı %10 çıkarılınca yarıdan fazla düşüyor | ⚠ **Maliyet birkaç işlemin eseri** — genel sonuç yazılamaz |

🔴 **HER DURUMDA ÜRETİLECEK ÇIKTI:** `taban_R` sayısı **her gelecek ön kaydın
§6'sına girer**. Bir aday *"bilgi var"* dese bile, bulduğu kenar `taban_R`'nin
altındaysa **mekanik aşamasına geçilmez.**

⛔ **YASAK:** *"stop'u genişletirsek maliyet düşer, deneyelim."* Bu bir
parametre taramasıdır. Stop genişletmenin **brüt** üzerindeki etkisi
ölçülmeden böyle bir cümle kurulamaz ve o ayrı bir ön kayıttır.

## 7. 🔴 KARMAŞIKLIK BÜTÇESİ (madde 6.2)

Bu ölçüm **yeni bir işlem kuralı doğurmaz.** Doğurduğu tek şey bir **ön kayıt
şartıdır** (`taban_R` eşiği) — yani gelecekteki adayları **eleyen** bir kural.
Bütçe eksi yönde: kural sayısı artmaz, adayların geçmesi zorlaşır.

## 8. BEKLENTİ (dürüstlük kaydı)

**Ana sicilde `taban_R` > 0,354R çıkmasını BEKLEMİYORUM** — gözlenen 0,1666R,
eşiğin altında. Yani beklentim: *maliyet ödenebilir büyüklükte, ama kenarın
varlığı gösterilemiyor* satırı. Bu, *"maliyet suçlu"* demekten **daha zayıf**
bir sonuçtur ve onu peşinen kabul ediyorum.

**Kendime karşı argüman:** maliyet dağılımı çarpıksa (birkaç çok dar stop),
ortalama yanıltıcıdır ve medyan çok daha düşük çıkabilir; o zaman *"maliyet
sorun değil"* sonucuna varırım ve 11 kat farkı başka bir şey açıklıyor demektir.

⚠ **Şunu beklemiyorum ve beklemediğimi yazıyorum:** iki sicil arasındaki 6 kat
maliyet farkının **tamamen** stop genişliğinden gelmesi. Kısmen sembol
fiyatından/tick'ten de gelebilir.

## 9. GEÇERSİZLİK KOŞULLARI

- `defter.maliyet_R` ya da fee sabitleri (`TAKER_FEE`/`BNB_CARPAN`/`SLIPPAGE`) değişirse
- İki sicil **toplanırsa**
- `taban_R` tanımı (ortalama maliyet_R) sonradan değiştirilirse
- §6'nın 0,354R eşiği sonuç görüldükten sonra oynatılırsa

## 10. ÖLÇÜM

`onkayit_maliyet.py` — **salt okur**. `defter.maliyet_R` ve `olcum.py`
kullanılır; hiçbir hesap kopyalanmaz. Bu commit'ten SONRA yazılır.

---

# SONUÇ — **BAĞLAYICI KISIT MALİYET DEĞİL, BELİRSİZLİK** (2026-09-01)

## ⚠ Önce bir düzeltme: §5'te gördüğüm brüt sayısı KİRLİYDİ

§5'te *"ana sicil brüt +2,50R"* yazmıştım. **Yanlış.** O hesap geri-doldurma ve
LAB kayıtlarını da içeriyordu; §3'ün dışladığı kayıtlar. Temiz örneklemde
(n=158) **brüt −4,69R.**

🔴 Ön kaydın §3'ü bu kayıtları **sonucu görmeden** dışlamıştı. Dışlamasaydım
*"brüt pozitifti, maliyet yedi"* diye yanlış bir hikâye kurardım.

## Ayrıştırma — iki sicil, ayrı

```
              n   BRUT toplam  MALIYET  NET      islem basina
ANA SICIL   158    -4,69R      27,43R  -32,12R   brut -0,0297R · mal 0,1736R
RADAR       187   -11,53R       5,22R  -16,75R   brut -0,0617R · mal 0,0279R
```

## §6'nın hükmü: **ikisinde de aynı satır**

| | ANA SİCİL | RADAR |
|---|---|---|
| `taban_R` | **0,1736R** | **0,0279R** |
| saptanabilir kenarın (0,354R) katı | 0,49× | 0,08× |
| brüt GA95 | [−0,3487, +0,2818] | [−0,3149, +0,2096] |
| işaret-permütasyon p | 0,8635 | 0,6556 |

> ⚠ **BAĞLAYICI KISIT MALİYET DEĞİL BELİRSİZLİK:** maliyet ödenebilir
> büyüklükte, ama kenarın **varlığı** gösterilemiyor.

🔴 **Bu, "maliyeti düşürelim" fikrini de öldürüyor.** Maliyet **sıfır** olsaydı
bile ana sicilde brüt −0,0297R/işlem ve GA'sı [−0,349, +0,282] — yani hâlâ
hiçbir şey. Sorun ödediğimiz bedel değil, **karşılığında bir şey almıyor
olmamız.**

## 🔴 6 KAT MALİYET FARKI AÇIKLANDI — stop genişliği

`ρ(stop_pct, maliyet_R)` ana sicilde **−0,970**, radarda **−0,977**.
Mekanik doğrulandı: maliyet ∝ 1/stop genişliği.

| | stop_pct medyan | taban_R |
|---|---|---|
| ANA SİCİL | **%1,65** | 0,1736R |
| RADAR | **%7,69** | 0,0279R |

Stop genişliği **4,7 kat** farklı, maliyet **6,2 kat**. §8'de yazdığım
*"farkın tamamının stop genişliğinden gelmesini beklemiyorum"* şerhi tuttu —
büyük kısmı oradan, tamamı değil.

**Sebep basit:** ana sicil 11 majör coini 1 saatlik dilimde işliyor; 2,5 ATR
stop, düşük oynaklıklı bir coinde fiyatın **%1,65'i** kadar dar oluyor.
Komisyon fiyatın sabit bir oranı olduğu için, R cinsinden maliyet patlıyor.

📌 **Kullanılabilir sonuç:** bir kenar bulunursa **radar daha ucuz taşıyıcı**.
Radar'ın tabanı (0,0279R) projenin gürültü tabanının (0,03R) **altında** —
yani radar için maliyet fiilen ihmal edilebilir.

## Maliyet dağılımı çarpık — ama hükmü değiştirmiyor

Ana sicil: ortalama 0,1736R, **medyan 0,0738R** (2,4 kat), en pahalı %10 toplam
maliyetin **%37,5**'ini oluşturuyor. En pahalı %10 çıkarılınca taban 0,1207R'ye
iniyor — **yarıya inmiyor**, o yüzden §6'nın *"birkaç işlemin eseri"* satırı
tetiklenmedi. Yine de dürüst okuma: **tipik işlem 0,07R öder, pahalı kuyruk
ortalamayı 0,17R'ye çekiyor.**

## Dönem kırılımı — kayda geçiyor, hüküm doğurmuyor

| | ilk yarı | ikinci yarı |
|---|---|---|
| ANA taban_R | 0,2416R | 0,0738R |
| ANA brüt | −0,1006R | +0,0745R |

Maliyet ikinci yarıda **üçte bire** düşmüş (stoplar genişlemiş — oynaklık artışı).
📌 Bu **bulgu değildir**: iki alt-örneklemin hiçbirinde GA hesaplanmadı ve
dönem ikiye bölme **sonuç görüldükten sonra** anlamlandırılırsa post-hoc olur.

## 🔴 ÜRETİLEN EŞİK — her gelecek ön kayda girer

| sicil | `taban_R` | anlamı |
|---|---|---|
| **ANA SİCİL** | **0,1736R** | gürültü tabanının **5,8 katı** |
| **RADAR** | **0,0279R** | gürültü tabanının **0,9 katı** |

**Bundan sonra:** bir aday *"bilgi var"* dese bile, bulduğu kenar ilgili sicilin
`taban_R`'sinin altındaysa **mekanik aşamasına geçilmez.** Bu, `ON-KAYIT-SABLON.md`
§6'ya girecek bir şarttır.

⛔ *"Stop'u genişletelim, maliyet düşer"* **hâlâ yasak.** Bu ölçüm stop
genişliğinin **maliyete** etkisini gösterdi; **brüt**e etkisini göstermedi.
Geniş stop daha az maliyet ama daha çok zarar da olabilir. O ayrı bir ön kayıt.

## Beklentim tuttu

§8'de *"`taban_R` > 0,354R çıkmasını beklemiyorum, beklentim 'maliyet ödenebilir
ama kenar gösterilemiyor' satırı"* yazmıştım. **Gerçekleşen tam olarak bu.**
İki oturumda ilk kez beklentim çürümedi.
