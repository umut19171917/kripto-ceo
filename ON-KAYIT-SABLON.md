# ÖN KAYIT ŞABLONU — her yeni ölçüm buradan başlar

> **Bu dosya kopyalanır, doldurulur, TEK BAŞINA commit'lenir (madde 8.5).**
> Ölçüm aracı ancak o commit'ten SONRA yazılır ve AYRI commit'lenir.
>
> 🔴 **Aşağıdaki başlıklardan hiçbiri silinemez.** Bir başlık boş kalıyorsa
> cevap *"boş"* değil, *"o ölçüm henüz yapılamaz"*dır.
>
> Neden şablon var: bu borçlar (güç hesabı, kontrol grubu, karmaşıklık bütçesi)
> her seferinde hatırlanmaya çalışılıyordu ve bazıları unutuluyordu. Madde 8.7:
> *kuralı düzyazıyla değil yapıyla koru.*

---

## 0. Bu ölçüm ne YAPAR, ne YAPMAZ

- Örneklem-içi mi, örneklem-dışı mı, ileri-zamanlı mı? (Örneklem-içiyse
  **hüküm doğuramaz** — yalnız *"pahalı testi hak ediyor mu"* sorusunu cevaplar.)
- ⛔ Kuramayacağı cümleler.
- ✅ Cevapladığı tek soru.

## 1. Neden bu ölçüm — ve neden ŞİMDİ

Bağlı madde numarası. Hangi önceki hüküm bunu gerektirdi.

## 2. TANIMLAR (donduruluyor)

Her büyüklüğün formülü. Ayrıca:
- 🔴 **İleri bakış yasağı:** öngörücü yalnız `t` ve öncesinden üretilir; nasıl?
- 🔴 **Ölçek düzeltmesi:** bantlar sembol İÇİNDE mi kesiliyor? (Ham havuzlama
  bantları sembole göre ayırır.)
- Çözünürlük · tohum (`random.seed(11)`).

## 3. ÖRNEKLEM

Semboller (seçim ölçütü **sonuca bakılmadan**), pencere, ve **açıkça yazılmış
yanlılıklar**: hayatta kalma · örtüşen getiri · tek rejim.

## 4. RAPORLANACAK NİCELİKLER (sıra sabit)

1. Kapsama.
2. Ana soru: bantlar · Spearman ρ · uç fark · **iki çıkarım** (bootstrap + permütasyon).
3. **Uç değer denetimi:** medyan ve kırpılmış ortalama. (Ortalama geçip medyan
   geçmezse hüküm *"uç değer eseri"*dir.)
4. **KONTROL KOLU (madde 8.2) — zorunlu.** *"Aynı gözlemler o kural olmadan."*
   Kontrol kolu yoksa **neden yok** yazılır; boş bırakılmaz.
5. Sağlamlık: top-3 çıkarılmış · dönem ikiye bölünmüş.

## 5. 🔴 GÜÇ HESABI — bu bölüm olmadan ön kayıt DONDURULAMAZ (EK 4)

Ölçülmüş girdiler: n, sd, **öngörücünün otokorelasyon süresi** (bağımsız gözlem
sayısını getiri değil ÖNGÖRÜCÜ belirler), etkin bağımsız birim.

**Zorunlu cümle:**
> *n=X, sd=Y ile ancak **Z** büyüklüğünde bir etkiyi görebiliriz. Aradığımız
> etki Z'den küçükse bu test onu bulamaz; o durumda "yok" değil **"ölçülemedi"**
> denir.*

Bir kol güçsüzse hükmü **şimdiden** *"ölçülemedi"* yazılır.

## 6. 🔴 KARAR KURALI — sonucu görmeden

Eşiklerin **dayanağı** yazılır (uydurulmuş sayı yasak). Varsayılanlar
`olcum.py`den: maliyet %0,13 · uzun-kısa %0,26 · ekonomik eşik %0,5 · ρ 0,80.

| Bulgu | Sonraki adım |
|---|---|
| … | … |

⚠ Eşiği geçmek **"kârlı"** demek değildir; yalnız *"mekaniği ölçmeye değer"*.

### 🔴 MALİYET TABANI — mekanik aşamasına geçiş şartı (`7910ce7`)

Bir aday *"bilgi var"* dese bile, bulduğu kenar **hangi sicilde koşacaksa**
onun `taban_R`'sinin altındaysa **mekanik aşamasına GEÇİLMEZ**:

| sicil | `taban_R` | gürültü tabanının (0,03R) katı | sürücü |
|---|---|---|---|
| **ANA SİCİL** | **0,1736R** | 5,8× | stop_pct medyanı **%1,65** (dar) |
| **RADAR** | **0,0279R** | 0,9× | stop_pct medyanı **%7,69** (geniş) |

Ölçüldü 2026-09-01 (`ON-KAYIT-maliyet.md`): `ρ(stop_pct, maliyet_R) ≈ −0,97`,
yani maliyet ∝ 1/stop genişliği. **Radar ~6 kat ucuz taşıyıcı.**

⚠ Bu eşik **bu dönemin** ölçümüdür; stop genişliği rejimle değişir
(ana sicilde ilk yarı 0,2416R → ikinci yarı 0,0738R). Yeni bir ön kayıt
yazılırken `onkayit_maliyet.py` **yeniden koşulmalı**, sayı kopyalanmamalı.

⛔ *"Stop'u genişletelim, maliyet düşer"* **yasak** — bu bir parametre
taramasıdır ve stop genişliğinin **brüt**e etkisi ölçülmedi.

## 7. 🔴 KARMAŞIKLIK BÜTÇESİ (madde 6.2) — yeni kural EMEKLİLİK ADAYI ister

*"VERİ/ÖLÇÜM ucuzdur (karar vermez). KURAL pahalıdır — kurallar birbiriyle
etkileşir ve beklenmedik birleşimler KARESEL artar."*

Bu ölçüm bir kural doğurursa:
- **Hangi mevcut kural emekliye ayrılacak?** (Aday gösterilmeden kural eklenmez.)
- Aday yoksa gerekçesi yazılır — *"gerekmiyor"* yeterli değildir.
- Bu ölçüm kural doğurmuyorsa: **"kural doğurmaz"** yazılır ve bölüm kapanır.

## 8. BEKLENTİ (dürüstlük kaydı — sonuç görülmeden)

Ne bekliyorum ve **neden**. Ayrıca **kendime karşı argüman**.
Sonuç beklentiyi çürütürse bu **kayda geçer**, sessizce düzeltilmez (madde 6.3).

## 9. GEÇERSİZLİK KOŞULLARI

Hangi değişiklik bu ön kaydı geçersiz kılar. (Sabitler · örneklem · eşikler ·
raporlanacak nicelikler · **koşan bir kapı canlıya alınırsa**.)

## 10. ÖLÇÜM

Araç adı. **Salt okur.** `olcum.bant_raporu` kullanır (permütasyon ve kontrol
kolu şerhini kendisi basar). Bu commit'ten SONRA yazılır, AYRI commit'lenir.

---

# SONUÇ — *(koşumdan sonra buraya eklenir, yukarısı DEĞİŞMEZ)*
