# KARAR — geri-doldurma kayıtları `taban_R` örneklemine girer mi?

**Tarih:** 2026-09-10 · **Durum:** karar verildi, uygulanmayı bekliyor
**Neden şimdi:** bu karar **sonuca bakılarak verilemez**. 30 Eylül'de
`onkayit_maliyet.py` yeniden koşacak ve `taban_R` üretecek; hangi örneklemin
kullanılacağı o an seçilirse, seçim sonuca göre kırpılmış olur.

---

## 1. Bulunan defekt

`onkayit_maliyet.py` satır 40-41:

```python
if t.get("kaynak") == "backtest" or t.get("backtest"):
    continue                                   # §3: geri-doldurma haric
```

Yorum *"geri-doldurma hariç"* diyor. **Kod `"backtest"` arıyor.**
Veride `kaynak` değerleri: `{None, 'geri-doldurma'}` — **`"backtest"` hiç yok.**

→ Bu satır bugün **hiçbir şeyi dışlamıyor.** Fiilen dışlayan tek şey LAB
(`olcucu.DENEYSEL`).

## 2. Fark maddi mi — evet

ANA sicil, 171 kapalı işlem, bunun **80'i geri-doldurma**:

| örneklem | n | brüt R | net R | işlem başına net | `mean(maliyet_R)` |
|---|---|---|---|---|---|
| tümü | 171 | −5,37R | −33,49R | −0,196R | **0,1645R** |
| **yalnız ileri-kayıt** | 91 | **+5,17R** | −13,31R | −0,146R | **0,2031R** |
| yalnız geri-doldurma | 80 | −10,54R | −20,18R | −0,252R | 0,1205R |

İleri kaydedilenlerin **brütü pozitif**, sonradan kurulanların brütü belirgin
negatif. Örneklem seçimi `taban_R`'yi **0,1205R ↔ 0,2031R** aralığında değiştiriyor.

**Geri-doldurma nedir:** `bosluk.py`, PC kapalı kaldığı aralığı mumlardan
**sonradan** kuruyor. Sahte değil — aynı kurallar uygulanıyor. Ama **ileri-kayıt
da değil**; epistemik statüsü farklı ve bu fark ölçülebilir çıktı.

## 3. KARAR

**Her iki örneklem ayrı raporlanır; `taban_R` olarak DAHA YÜKSEK olan seçilir.**

Yani bugünkü veriyle: **ileri-kayıt kolu, `taban_R = 0,2031R`.**

Gerekçe:
1. **Daha yüksek eşik = daha zor kapı.** Bir adayın geçmesini zorlaştırmak, yanlış
   pozitif riskini azaltır. Kolay kapı seçmek, sonucu kendi lehine kırpmaktır.
2. **Kural sonuçtan bağımsız.** "Daha yüksek olanı al" bugün yazıldığı için,
   30 Eylül'de hangi kolun yüksek çıktığına göre seçim yapılamaz.
3. İleri-kayıt kolunun daha yüksek çıkması **tesadüf değil**: `ρ(stop_pct,
   maliyet_R) ≈ −0,97` (`7910ce7`), yani dar stop → yüksek maliyet. Canlı akışta
   üretilen sinyallerin stopları daha dar. Bu, kolun **yapısal** olarak pahalı
   olduğunu gösteriyor, gürültü olduğunu değil.

## 4. 🔴 Kapsam düzeltmesi — derinlik ölçümü ETKİLENMİYOR

Önceki oturumda bu defekti *"derinlik ön kaydının §6 kapısını etkiler"* diye
sundum. **Bu fazla genişti, düzeltiyorum:**

`ON-KAYIT-derinlik.md` §6 açıkça *"Bu aday **RADAR**'da koşacaktır"* diyor ve
RADAR'ın `taban_R`'sini kullanıyor. Ölçüldü (2026-09-10):

```
RADAR kayitlarinda 'kaynak' alani olan: 0
RADAR geri-doldurma: 0
```

**RADAR sicilinde hiç geri-doldurma kaydı yok** → RADAR `taban_R`'si bu defektten
**etkilenmiyor** (236 işlem, `mean(maliyet_R)` = 0,0283R).

→ Bu karar **ANA sicile dayanan** işler için bağlayıcıdır; derinlik ölçümünün
hükmünü değiştirmez. Aciliyeti sandığımdan düşük.

## 5. Uygulama

⛔ **`onkayit_maliyet.py` DÜZENLENMEYECEK.** Donmuş ölçüm araçları değiştirilmez
(tek-sahiplik denetimi, 2026-09-01). Sonuçları zaten kayıtlı ve o kayıt geçerli.

✅ 30 Eylül'de yeniden koşum, **iki kolu ayrı basan** bir çağrıyla yapılır ve
yukarıdaki "daha yüksek olanı al" kuralı uygulanır. Uygulayan taraf bu dosyaya
atıf verir.

⚠ `onkayit_maliyet.py`'nin **mevcut kayıtlı sonucu geçersiz değildir** — yalnız
örneklemi *"tümü"* kolu olarak okunmalıdır (`taban_R` 0,1736R o dönemin
"tümü" hesabıydı).
