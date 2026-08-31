# ÖN KAYIT — `giris`: kırılım girişi kenarı mı yiyor? (TERS SEÇİLİM)

**Yazım anı:** 2026-09-01 (koşumdan ÖNCE; hiçbir kol karşılaştırılmadan)
**Durum:** DONDURULDU. §2–§7 bu commit'ten sonra değiştirilmez.
**Şablon:** `ON-KAYIT-SABLON.md` (`ed4770d`)
**Bağlı madde:** 5.2 — ters seçilim ölçümü
**Öncülleri:** `be56b77` (B2 mekanik) · `8274909` (ters) · `162100b` (basis)

---

## 0. Bu ölçüm ne YAPAR, ne YAPMAZ

Geriye dönük, **aynı 462 sinyal** üzerinde üç farklı giriş kuralının
karşılaştırılması. Sinyalin kendisi sorgulanmıyor — **giriş mekaniği** sorgulanıyor.

- ⛔ *"Sinyal iyidir/kötüdür"* diyemez (o B1/B2/B3'te ölçüldü: kötü).
- ⛔ Kârlılık hükmü kuramaz.
- ✅ Tek cevapladığı: **kırılımı beklemek, beklememekten daha mı kötü?**

⚠ **Örneklem-içi sınır:** bu sinyaller ve bu pencere daha önce incelendi.
Ama karşılaştırılan şey **hiç ölçülmedi** — B2 yalnız A kolunu koştu.
Yine de hüküm *"ileri-zamanlı doğrulama gerekir"* şerhiyle yazılır.

## 1. Neden bu ölçüm — ve neden ŞİMDİ

İki bağımsız ölçümde **aynı desen** çıktı:

| ölçüm | ham sinyalde | mekanikten sonra |
|---|---|---|
| B1 → B2 | ρ=+1,000 (güçlü düzenlilik) | **−0,327R** |
| `ters` | boğa öncesi +%0,392 (daha güçlü) | **−0,134R** |

İkisinde de **kenarı yiyen şey giriş mekaniği.** `ters` hükmünde yazılmıştı:
*"kırılım girişi ham kenarı yiyor."* Bu, o cümlenin sınanmasıdır.

🔴 **Neden ŞİMDİ önemli:** emir defteri derinliği adayı ~30 gün sonra
sınanacak. Giriş mekaniği kenarı yiyorsa, o testi **aynı bozuk mekanikle**
kurmak onu da baştan öldürür. Bu ölçüm o tasarımı düzeltir.

## 2. TANIMLAR (donduruluyor)

Üç kol, **AYNI 462 sinyal**, aynı stop/TP mesafeleri (`STOP_ATR=2,5`,
`TP1=5,2`, `TP2=8,33`), aynı pencereler (`PENDING=24s`, `ACTIVE=120s`),
aynı maliyet (`defter.maliyet_R`), aynı temkinli çözüm (aynı barda stop+TP → STOP):

| kol | giriş kuralı |
|---|---|
| **A — KIRILIM** (mevcut) | `swing_low`'a kırılım; 24s içinde dokunulmazsa **işlem YOK** |
| **B — ANINDA** (kontrol) | sinyal barının **kapanışından** hemen gir; her sinyal işlem olur |
| **C — RASTGELE** (plasebo) | 24s bekleme penceresi içinde **rastgele bir saatin** kapanışından gir |

🔴 **C kolu neden var:** A ile B'yi karşılaştırmak *"beklemek mi, beklememek mi"*
sorusunu cevaplar; ama beklemenin **kendisi** mi yoksa **kırılım şartı** mı
zarar veriyor ayırt edemez. C aynı süreyi bekler, kırılım şartını **uygulamaz**.
- A ≈ C → kırılım şartı bir şey eklemiyor (ne iyi ne kötü)
- A < C → kırılım şartı **aktif olarak zararlı** = ters seçilim
- A > C → kırılım şartı **koruyucu**

Rastgele saat için `random.Random(11)`, sinyal başına **tek** çekiliş
(sonuç görüldükten sonra yeniden çekilmez).

## 3. ÖRNEKLEM

- **462 sinyal · 58 takvim günü · 11 sembol** (ölçüldü 2026-09-01).
- Sinyaller `onkayit_mekanik.sinyaller()`'den **birebir** alınır; yeniden
  tanımlanmaz (madde 8.3 sahiplik).
- ⚠ **Tek yön (SHORT), tek pencere, tek rejim.** Genelleme yapılamaz.
- ⚠ **B ve C kolları A'dan ~3 kat fazla işlem üretir** (A tetiklenme ~%33).
  Birincil ölçüt **işlem başına** ortalamadır; portföy sonucu ayrı raporlanır.

## 4. RAPORLANACAK NİCELİKLER (sıra sabit)

1. Kapsama: kol başına işlem sayısı · tetiklenme oranı · sonuç dağılımı.
2. **ANA:** kol başına ortalama net R · **gün-kümeli GA95** · **gün-içi permütasyon p**
   (`olcum.py` — ikisi birden, biri eksikse hüküm basılmaz).
3. **EŞLEŞTİRİLMİŞ FARK:** aynı sinyalde `B − A` ve `C − A`.
   ⚠ A tetiklenmemişse A'nın katkısı **0R'dir** (işlem yok, kayıp da yok) —
   bu, kolların **doğru** karşılaştırmasıdır, eksik veri değil.
4. Uç değer denetimi: medyan ve %1-%99 kırpılmış ortalama.
5. **KONTROL KOLU (8.2):** B ve C zaten kontrol kollarıdır. ✅
6. Sağlamlık: top-3 sembol çıkarılmış · dönem ikiye bölünmüş.
7. Portföy: `onkayit_portfoy` mantığıyla üç kol yan yana (ikincil).

## 5. 🔴 GÜÇ HESABI

Girdiler (B2'nin **yayımlanmış** sayılarından): 150 tetiklenen işlem,
ortalama −0,327R, gün-kümeli GA yarı-genişliği 0,2415R → `SE ≈ 0,1232R`.
58 gün × ~2,5 etkin bağımsız sembol → `n_eff ≈ 145` → `sd ≈ 1,48R`.

Eşleştirilmiş tasarımda farkın sd'si bundan **küçük** olur (kollar aynı
sinyalleri paylaşır); muhafazakâr olarak 1,48R kullanılıyor.

```
SE(fark) = 1,48 / sqrt(145) = 0,123R
%95'te saptanabilir en küçük fark = 1,96 × 0,123 = 0,241R
```

**Zorunlu cümle:** *n_eff≈145 ve sd=1,48R ile ancak **0,241R** büyüklüğünde bir
kol farkını görebiliriz. B2'nin mekanik kaybı 0,327R idi — yani o büyüklükte
bir etkiyi bulabiliriz. Daha küçüğünü göremeyiz; o durumda "yok" değil
**"ölçülemedi"** denir.* Gürültü tabanı 0,03R olduğundan, bu test **ince ayar
farklarını göremez** ve iddia da etmez.

## 6. 🔴 KARAR KURALI — sonucu görmeden

| Bulgu | Sonuç |
|---|---|
| `C − A` ≥ **+0,241R** ve GA sıfırı dışlıyor ve p<0,05 | ✅ **TERS SEÇİLİM VAR.** Kırılım şartı aktif olarak zararlı |
| `B − A` ≥ +0,241R ama `C − A` küçük | ⚠ Zararlı olan **beklemenin kendisi**, kırılım şartı değil |
| Üç kol da GA'sı sıfırı kapsayacak kadar yakın | ❌ Giriş mekaniği **suçsuz** — kenarı yiyen başka bir şey |
| İki çıkarım çelişiyor | Muhafazakâr okuma; `olcum` kendi basar |

⚠ **Hiçbir sonuç "şu girişi kullanalım" demez.** Üç kolun üçü de negatif
çıkabilir (sinyal zaten ters). Bu ölçüm **sıralama** hakkındadır, kârlılık değil.

## 7. 🔴 KARMAŞIKLIK BÜTÇESİ (madde 6.2)

Bu ölçüm **yeni kural doğurmaz** — mevcut bir kuralı **emekliye ayırabilir**.
Emeklilik adayı önceden bellidir: **kırılım girişi** (`swing_low`/`swing_high`
kırılımı bekleme şartı). Ters seçilim doğrulanırsa aday odur.
Yani bütçe **eksi yönde** işliyor: kural sayısı artmaz, azalabilir.

## 8. BEKLENTİ (dürüstlük kaydı — sonuç görülmeden)

**`C − A` pozitif çıkacak, yani ters seçilim bulacağımızı bekliyorum** — ama
0,241R eşiğini geçecek kadar büyük olmayabilir. Gerekçe: B2'de tetiklenen
işlemlerin **%72'si stop** oldu ve stop olanların **%26,9'u ufuk sonunda
kârdaydı**; bu, girişin sistematik olarak kötü anda yapıldığına işaret.

**Kendime karşı argüman:** B2'de stop **koruyucu** çıktı (+0,558R). Kırılım
şartı da bir tür filtredir ve sinyallerin %67'sini eliyor. Eğer o eleme
kötüleri eliyorsa, A **daha iyi** çıkar ve beklentim çürür. Ayrıca B ve C
3 kat fazla işlem açar; ters sinyalde bu **daha çok kayıp** demektir —
işlem başına iyi görünse bile portföyde kötü olabilir.

## 9. GEÇERSİZLİK KOŞULLARI

- `onkayit_mekanik`'in sabitleri (`STOP_ATR`/`TP*`/`PENDING`/`ACTIVE`) değişirse
- Rastgele tohum sonuç görüldükten sonra değiştirilirse
- Kol tanımları (§2) ya da eşik (0,241R) sonradan oynatılırsa
- Sinyal kümesi yeniden tanımlanırsa

## 10. ÖLÇÜM

`onkayit_giris.py` — **salt okur**. `onkayit_mekanik`'in veri yolunu ve
`olcum.py`'nin çıkarım katmanını kullanır. Bu commit'ten SONRA yazılır.
