# KRİPTO SİSTEMİ — GÜNCEL SKILL (çalışan sistemin tam tarifi)

> **Bu dosya nedir:** Sistemin ŞU ANKİ gerçek halinin tam anlatımı. `kripto-SKILL.md`
> (Faz-0 doğum belgesi, LLM-merkezli eski tasarım) DEĞİL — bu, kodda fiilen çalışan
> sistemin skilli. Anlık sayılar (sicil, K2 sayacı, rejim) zamanla eskir; mimari ve
> disiplin kalıcıdır.
> **Anlık görüntü tarihi:** 2026-08-19 (§11 anlık durum; §9 bulgular kalıcı).
> **Proje yolu:** `c:\Users\KURTİ\Desktop\klasörler\kripto`

---

## 0. ÇEKİRDEK FELSEFE (sistemin keşfettiği tez)

Eski tasarımın tezi "akıllı bir LLM CEO çok sinyali iyi kararlara sentezler"di.
Kurup ölçünce bunun yanlış olduğu görüldü. Sistemin bugünkü tezi:

1. **LLM işlem döngüsünde YOK.** Tüm matematik ve karar deterministik Python'da.
   Claude sadece durumu okur, açıklar, sistemi geliştirir — canlı işlem kararını VERMEZ.
2. **Edge (kazanç üstünlüğü) kanıtlanana kadar gerçek para YOK.** Kanıt = istatistik
   kapıları (K2/K3), sezgi veya iyi görünen backtest değil.
3. **Dürüstlük çekirdektir.** Komisyon dahil net sonuç saklanmaz; girilmeyen işlem
   kayıp sayılmaz; "bilmiyoruz"u "biliyoruz" gibi göstermeyiz.
4. **Emir her zaman kullanıcıda.** Hiçbir ajan para/emir yetkisine sahip değil.

**Agresiflik tanımı:** "Bilgide agresif, riskte disiplinli." Çok aday tara, ama
pozisyon boyutu ve kanıt eşiği sabit kalsın.

---

## 1. MİMARİ + VERİ AKIŞI (token-0)

```
Binance public REST ─┐
Coinalyze REST ──────┼─> olcucu.py (TÜM matematik) ─> signals.json (özet)
Yahoo DXY / FF takvim─┘         │
                                 ├─> izleyici.py (30sn döngü) ─> defter.py ─> kripto-defter.json
                                 │        └─> Telegram (bildirim.py)
                                 └─> radar.py (ayrı süreç) ─> radar_defter.py ─> radar-defter.json
```

- **Veri + matematik %100 yerel Python.** Claude'a token yük bindirmez. WebSocket bu
  ağda ölü (bölge engeli) → likidasyon Coinalyze REST'ten periyodik çekilir; fiyat/OI/
  funding Binance REST'ten.
- **İki bağımsız süreç:** `izleyici.py` (ana 11 coin, sicil yazar) ve `radar.py` (geniş
  tarama, ayrı sicil). Ayrılar ki ağır tarama işi sicil-yazan süreci riske atmasın.

---

## 2. SÜREÇLER (otomatik çalışma)

| Süreç | Ne yapar | Ritim |
|---|---|---|
| **izleyici.py** | 11 coin paralel snapshot, defter.guncelle, likidasyon çekimi, makro tazeleme, günlük özet | 30 sn |
| **radar.py** | (1) hareket radarı, (2) kurulum taraması, (3) duyuru nöbetçisi | 5dk / 2s / 6s |

- Başlatma: `Başlangıç` klasöründe `KriptoIzleyici.vbs` + `KriptoRadar.vbs` (her logon'da
  pythonw ile penceresiz başlar; admin gerekmez). PC kapalı/uykuda veri akmaz.
- **Not:** venv pythonw bir shim+gerçek yorumlayıcı çifti başlatır → Görev Yöneticisi'nde
  2 pythonw = 1 mantıksal süreç (kopya değil).

---

## 3. DOSYA HARİTASI

**Kod (GitHub'da, push edilir):**
- `olcucu.py` — veri çekme + tüm göstergeler (ATR/RSI/VWAP/CVD/OI/funding) + sıkışma
  skoru + `trade_plan` (ATR-tabanlı giriş/stop/TP + vetolar). Sistemin beyni.
- `izleyici.py` — ana canlı döngü (snapshot + sicil + bildirim + özet).
- `defter.py` — tahmin kaydı + sonuç çözme motoru (`coz`, kapanmış-1dk-mum, fitil-tabanlı)
  + net-R muhasebesi + sözel mesaj katmanı + risk tavanı + rejim damgası.
- `radar.py` — geniş tarama süreci (3 görev).
- `radar_defter.py` — radar adayları için AYRI sicil + `radar-defteri.html` üretimi.
- `tarayici.py` — on-demand piyasa tarayıcı (Mod 1, ~48 coin).
- `kalibrasyon.py` — per-symbol eşik hesabı (her coin kendi funding/OI geçmişinden).
- `makro.py` — makro güvenlik kapısı (DXY + takvim + şok ayak izi).
- `rejim.py` — piyasa havası (4 majör korelasyon + BTC vol rejimi + trend).
- `likidasyon.py` — Coinalyze REST likidasyon beslemesi + per-symbol cascade eşiği.
- `bosluk.py` — PC kapalıyken oluşan boşluğu geri-doldurma (açık tahminleri kesin çözer).
- `bildirim.py` — Telegram gönderimi (fail-safe no-op).
- `durum.py` — anlık durum raporu (çift-tık, sözel format).
- `backtest.py` / `ileritest.py` / `ileritest2.py` / `aday_testi.py` — doğrulama araçları (bkz. §9).
- `yedek.py` + `yedek.bat` — kritik dosyaların günlük Google Drive yedeği (tarihli klasör,
  son 14 gün, idempotent + fail-safe; izleyici günde 1 kez otomatik çağırır).

**Veri/sicil (gitignore'lu, PUSH EDİLMEZ):**
- `kripto-defter.json` — ana sicil (K2 ölçümü, kişisel).
- `radar-defter.json` — radar sicili.
- `telegram.json` / `coinalyze.json` — API kimlikleri (salt-veri, para yetkisi yok).
- `signals.json`, `makro.json`, `rejim.json`, `esikler.json`, `likidasyon-esik.json` — çalışma-anı (kod yeniden üretir).

---

## 4. KARAR MANTIĞI (deterministik)

### 4.1 Sıkışma skoru (0-100)
`olcucu.py` her coin için SHORT-squeeze ve LONG-squeeze skoru üretir (yakınlık +
funding + OI + yapı bileşenleri). Plan ancak skor ≥ **70** (PLAN_FLAG) olunca üretilir.

### 4.2 İşlem planı (`trade_plan`) — SWING-1H konfig
- Yön: LONG-squeeze → SHORT (aşağı kırılım) | SHORT-squeeze → LONG (yukarı kırılım).
- Giriş = 1h 50-bar yapısal seviye. ATR = 1h ATR.
- **STOP = giriş ∓ 2.5·ATR | TP1 = ∓ 5.2·ATR | TP2 = ∓ 8.33·ATR** → R/R1 = 2.08.
- Risk = portföyün **%1'i** (RISK_PCT). İma kaldıraç = %1 / stop% (gösterilir, dayatılmaz).

### 4.3 Vetolar (plan geçersiz sayılır)
- **R/R < 2.0** → veto.
- **min(stop, tp1, tp2) ≤ 0** → dejenere plan (negatif fiyat; LAB #110 dersi).
- **stop mesafesi < %0.1 VEYA yuvarlamada stop==giriş** → "stop girişe yapışık"
  (stablecoin/ölü oynaklık; USDC dersi). `STOP_PCT_TABAN=0.1`.

### 4.4 Makro kapısı (`makro.json`)
- Çıktı: **ACIK / DIKKAT / KAPALI** + boyut çarpanı + `min_skor`.
- Bileşenler: DXY rejim + ekonomik takvim (ForexFactory) + şok ayak izi.
- KAPALI'da yeni tahmin açılmaz; DIKKAT'te boyut x0.5 + min_skor 80.

### 4.5 Rejim katmanı (`rejim.json` → makro'ya katılır)
- 4 majör (BTC/ETH/SOL/LINK) SABİT korelasyon + BTC vol rejimi + trend.
- Korelasyon ≥ **0.85** VEYA vol ≥ 1.5 → OYNAK → DIKKAT/x0.5/min_skor 80.
- **Skora KARIŞMAZ** (yalnız kapı + boyut). Her hata → nötr rejim (kısıtlama eklemez).

---

## 5. SİCİL SİSTEMİ (üç ayrı defter)

| Sicil | Ne | K2'ye sayılır mı |
|---|---|---|
| **Ana sicil** (11 coin) | Canlı listenin K2 ölçümü — gerçek karne | EVET |
| **Deneysel** (LAB) | LAB tam üye ama `sicil:"deneysel"` etiketli | HAYIR (ayrı raporlanır) |
| **Radar sicili** | Geniş taramanın ~45 coinlik adayları | HAYIR (tamamen bağımsız) |

- **Durum akışı:** beklemede → izleniyor (tetiklendi) → tp1/tp2 (kâr) | stop (zarar) |
  zaman_asimi (süre doldu, son fiyattan mark-to-market) | tetiklenmedi (girişe hiç ulaşmadı = ne kâr ne zarar).
- **Çözme motoru:** kapanmış 1dk mumların high/low'u (bekleyen-emir semantiği; fitil
  dokunuşu emri doldurur). Aynı mumda stop+TP → temkinli STOP sayılır. Canlı + geri-doldurma
  AYNI motoru kullanır (tek muhasebe).
- **Her yeni kayda rejim damgası** işlenir (rejim_durum/korelasyon/vol_orani/etkin_min_skor)
  — davranışı etkilemez, K2 günü "kayıplar nerede kümeleniyor" analizi için.

---

## 6. MALİYET MODELİ (net-R — belirleyici mercek)

- **Kaynak:** Binance USDⓈ-M VIP0 — maker %0.02, taker %0.05 (+ BNB ile %10 indirim → çarpan 0.90).
- Per-bacak: giriş=taker, TP=maker, stop=taker; slippage %0.02/taker bacak.
- `net_R = brüt R − maliyet_R`. **Brüt pozitif ama net negatif** = bu sistemin bugünkü
  gerçeği; strateji breakout girişi olduğu için giriş doğası gereği taker (maker illüzyonuna güvenilmez).

---

## 7. RİSK KONTROLLERİ

- **Risk tavanı:** aynı yönde eşzamanlı toplam risk ≤ **%2** (beklemede+izleniyor sayılır).
  Korelasyonlu yığılma freni; canlıda ateşliyor.
- **Cooldown:** aynı coine 12 saat içinde yeni tahmin yok.
- **Dejenere vetolar** (§4.3).

---

## 8. BİLDİRİM (Telegram — `@at101claude_bot`)

**Gider (tavsiye niteliğinde):** ana 11 coin sinyalleri (YENI/TETIK/SONUC/GECERSIZ,
LAB dahil), [RADAR-KURULUM] adayları, [MAKRO] kapı değişimi, [ONEMLI DUYURU] (delisting),
günlük özet.
**Gitmez:** [RADAR-HAREKET] (bilgi katmanı → sadece radar.log + durum.py + günlük özet satırı).
Mesajlar jargonsuz sözel format ("Sistem fiyatın DÜŞECEĞİNİ öngörüyor... SATIŞ... stop...
kâr hedefi"). Telegram ve durum.py AYNI fonksiyonları kullanır (iki çıktı sapmaz).

---

## 9. DOĞRULAMA ARAÇLARI (canlıya dokunmaz)

- `backtest.py` — geçmiş klines'ta plan mekaniğini A/B test eder (in-sample).
- `ileritest.py` — **walk-forward** (eşikler sadece fold öncesinden, test görülmemiş
  dilimde). B1 dersi: in-sample "funding 6/6 pozitif" bulgusu OOS'ta çöktü → tek geçerli
  edge testi canlı K2 sicili.
- `ileritest2.py` — trend filtresi + geniş-stop walk-forward. Sonuç: geniş-stop çürüdü;
  trend filtresi +0.02-0.03R (⚠ aşağıdaki gürültü tabanı bulgusundan sonra ŞÜPHELİ).
- `aday_testi.py` — **K2 aday sınavı** (2026-07-27). Yöntem: her aday TEK DEĞİŞKEN olarak
  canlı config'e karşı, EŞLİ, aynı fold'larda; dev kombinasyon ızgarası kurulmaz.
  `_cache/` günlük veri önbelleği → tekrar koşular anında.
- `skor_gucu.py` — canlı skorun ileri-tahmin gücü (964k kayıt). §9.3-A.
- `sinyal_tarama.py` — aday sinyal eleme (koşullu getiri − koşulsuz taban). §9.3-B.
- `fade_testi.py` — fade hipotezinin 540g rejim sınavı; `--bant uc|orta`. §9.3-D.
- `fade_kontrol.py` — likidasyon olayı vs frekans-eşlenmiş fiyat şoku, eşli. §9.3-E.

### 9.1 ADAY SINAVI SONUÇLARI (2026-07-27, 11 coin × 540g × 12 fold)
Baz (canlı config): 3210 işlem, %34 isabet, netR **+64.1**, işlem başına **+0.020R**, pozitif fold **4/12**

| Aday | İşlem | netR | İşlem başına | pozF | Hüküm |
|---|---|---|---|---|---|
| **F&G kapısı** (≥75 LONG yok, ≤25 SHORT yok) | 2300 | **+130.7** | **+0.057** | **8/12** | ✅ EN GÜÇLÜ |
| **OYNAK'ta LONG yok** (SHORT serbest) | 2377 | +90.3 | +0.038 | 5/12 | ⚠ umutlu, veri-türetilmiş |
| SAKIN-only (OYNAK tamamen atlanır) | 1360 | +55.5 | +0.041 | 6/12 | işlemlerin %58'ini keser |
| basis persentil | 531 | +21.5 | +0.041 | 6/12 | ❌ yoğunlaşma %235 |
| lookback 200 (seviye penceresi) | 1338 | +44.4 | +0.033 | 5/12 | ❌ zikzak, monoton yön yok |
| funding persentil | 631 | −8.3 | −0.013 | 7/12 | ❌ bazın altında |

**F&G neden birinci:** (a) kural ÖN-KAYITLI — dış skill'den alındı, kendi verimizden
türetilmedi; (b) fark (+0.037) gürültü tabanının ÜSTÜNDE; (c) çoğunluk-pozitif fold'a ulaşan
TEK aday (8/12); (d) yoğunlaşma %68 — baz %141 (baz en iyi fold'suz NEGATİF, F&G'li değil).
Mekanizma: kazancın tamamı SHORT yarısından (filtreli SHORT +0.139 = bazın 4.6 katı) =
"aşırı korkuda dibi satma". ⚠ LONG yarısı fiilen test edilmemiş (8 işlem engelledi);
⚠⚠ ortalamaya-dönüş bahsi — uzun süreli çöküşte en kârlı short dönemini kaçırtabilir.

**Basis kapandı:** B1'de tek OOS-pozitif adaydı; tazeleme testinde yoğunlaşma %235 çıktı
(toplam +21.5, tek fold +50.6 → o fold'suz −29.1). Fold-konsantrasyon şüphesi ikinci kez
bağımsız doğrulandı → iki kez çürümüş.

### 9.2 ⚠ GÜRÜLTÜ TABANI (kalan tüm kararları etkiler)
Aynı baz config, 10 gün arayla: **+0.05 (07-17) vs +0.020 (07-27)** — hiçbir şey değişmeden
ölçüm yarıya indi (tek fark: 540g pencerenin 10 gün kayması). **Sonuç: 0.03R'den küçük
farklar ANLAMSIZ.** Doğrudan etkisi: trend filtresinin "+0.02-0.03R" bulgusu artık şüpheli.
(Eşli/aynı-veri karşılaştırmalar pencere-kaymasından güvenilir, ama yine de temkin.)

### 9.3 EDGE ARAMA (2026-08-09/10) — çekirdek tez ölçüldü, fade adayı sınandı
**Neden:** K2 sayacı 25/30'a geldiğinde canlı sicil 3 kazanç / 22 kayıp (net −15,59R); binom
hesabıyla "şanssızlık" ihtimali %1,5. Karar: **strateji ayarlamayı bırak, önce sinyalde bilgi
var mı diye ölç.**

**A. `skor_gucu.py` — ÇEKİRDEK TEZ DESTEKLENMEDİ.** 964k canlı skor kaydı (42g, 11 coin):
skor yükseldikçe öngörü gücü artmıyor; "düşecek" denen anlarda fiyat rastgele bir ana göre
DAHA AZ düşüyor. Ek: **21:1 yön asimetrisi** — SHORT sinyali 21 kat fazla; BTC/ETH/SOL/XRP/DOGE
42 günde tek LONG vermedi.

**B. `sinyal_tarama.py` — FADE adayı elemeyi geçti.** Likidasyon kademesi (35g, 933 olay):
zorunlu SATIŞ'tan sonra fiyat YÜKSELİYOR, zorunlu ALIM'dan sonra DÜŞÜYOR — zıt işaretli,
doz-tepkili. **Sistemin varsayımının TERSİ yön.**

**C. ⛔ Coinalyze veri sınırı (2026-08-10 probu) — TEKRAR DENEME.** Likidasyon geçmişi:
1saat granül ~60-65 gün, 5dk ~10-15 gün, 120g ve ötesi BOŞ. 540g walk-forward likidasyon
verisiyle **imkânsız**.

**D. `fade_testi.py` — GENEL FADE ÇÜRÜDÜ.** Hipotez fiyat üzerinden sınandı (likidasyon
kademesi sebep, gözlenebilir iz fiyatta): 10 coin × 540g × 12 fold, walk-forward eşik,
fold+sembol bazında taban çıkarımı, BOĞA/AYI ayrımı (BTC 50g SMA, %50/%50).

| Band | Ön-kayıtlı hücre | düş EDGE | yük EDGE | Hüküm | Sembol | Fold |
|---|---|---|---|---|---|---|
| uç (P90/95/99) | W=1s, P95, +4s | −0,001% | +0,044% | DEVAM | 1/10 | 2/12 |
| orta (P70/80/85) | W=1s, P80, +4s | −0,024% | +0,002% | DEVAM | **0/10** | 2/12 |

Rejim ayrımı: BOĞA'da DEVAM, AYI'da sayısal olarak sıfır (±0,004%). 54 hücrede tutarlı FADE
yok; +4s ufkunda baskın örüntü zayıf DEVAM (momentum). **Tüm büyüklükler %0,130 maliyet
çizgisinin ALTINDA** → iki yönde de işlenebilir edge yok.

**E. `fade_kontrol.py` + örtüşme probu — likidasyon ≠ "büyük hareket".** Aynı 35 günde,
frekans eşlenmiş kontrol: likidasyon 3 ufukta da FADE (+4s: +0,063/−0,199 | +24s:
+0,332/−0,589); eşit sayıda en-sert fiyat hareketi karışık/zayıf. Sembol bazında FADE:
likidasyon 6/10, fiyat 3/10. Örtüşme yalnız **%5** (±1 barla %19-36). Likidasyon olayları
5dk hareket dağılımının **medyan %77'sinde** oturuyor, %27'si medyanın ALTINDA → ayrı olay
sınıfı. Bu yüzden D bulgusu B'yi **doğrudan çürütmez**, ama genel mekanizmayı elinden alır.

**HÜKÜM (2026-08-10):**
1. Genel "sert hareket → geri dönüş" mekanizması 540 günde çürüdü — **üstüne strateji kurulmaz.**
2. Likidasyona-özgü fade çürütülmedi ama **doğrulanamaz**: 35 gün, tek rejim, geçmiş veri yok.
3. Tek dürüst yol **İLERİYE DÖNÜK doğrulama**: log zaten akıyor; `sinyal_tarama.py` pencere
   büyüdükçe tekrar koşulur (~6 ayda 200+ gün, iki rejim). Sıfır maliyet, gerçek OOS.
4. O güne kadar likidasyon fade'i üzerine **parametre/strateji değişikliği YOK.**

### 9.4 KESİTSEL GÖRELİ GÜÇ (2026-08-11) — ilk zaman-serisi-DIŞI aile, düştü
**Neden:** Bugüne kadarki her aday tek-coin/zaman-serisi sorusu soruyordu ("bu coin hareket
edecek mi?") ve altısı da çürüdü. Bu test farklı bir aile: **"hangi coin hangisinden iyi?"**
Kullanıcının "ayıda boğa yaşayan coinleri bulup ortak noktalarını arayalım" fikrinin
yanlılıksız hali — kazananları seçmek yerine **her tarihte tüm evreni sırala**, kaybedeni de
örneklemde tut, sıralamanın geleceği bilip bilmediğini ölç.

`kesitsel_test.py` — ÖN-KAYIT koşmadan önce sabitlendi: sıralama 30g, ufuk 7g (üst üste
binmeyen), 10 desil, evren = her tarihte önceki 30g medyan hacme göre en likit 100.
Öğrenilen eşik YOK (desil kesimi kuralla tanımlı) → uydurma riski yapısal olarak düşük.
525 sembol, 77 yeniden dengeleme, 7.700 coin-tarih gözlemi, %40 BOĞA.

| Evren | üst−alt | 1 maliyet | 2 rejim | 3 dönem | 4 monoton | 5 yoğunlaşma | Hüküm |
|---|---|---|---|---|---|---|---|
| tüm (525) | +4,513% | ✅ | ✅ | ❌ 3/6 | ❌ 6/9 | ✅ | **düştü** |
| eski (292) | +0,747% | ✅ | ✅ | ✅ 4/6 | ❌ 5/9 | ❌ | **düştü** |

**+%4,5/hafta neden gerçek değil — teşhis üç bağımsız yoldan aynı yeri gösterdi:**
1. **Medyan negatif.** Üst desil ortalaması +3,17% ama **medyanı −4,46%**. Tipik "güçlü" coin
   ertesi hafta kaybediyor; ortalamayı bir avuç dev kazanan taşıyor.
2. **Yoğunlaşma.** 77 tarihin en iyi 5'i toplam etkinin **%91'ini** taşıyor (en iyi tek tarih
   +%133,6). Temizlenmiş evrende en iyi 3 tarih çıkarılınca toplam **işaret değiştiriyor**
   (+57,5 → −20,6, yani %136). Basis'i iki kez öldüren örüntünün en uç hali.
3. **Hayatta kalma kanalı.** Etkinin tamamı pencere içinde listelenen coinlerden: yeni
   listelenenlerde üst−alt +10,43%, pencere başında var olanlarda +0,52% — ve medyanlarla
   ikisi de negatif (−0,11% / −1,40%). Yükselip delist olanlar veride YOK.

**Temizlenmiş evrende asıl bulgu momentum değil:** desil 1-8 hafifçe pozitif, **desil 0 ve
desil 9 ikisi de negatif** (−1,33 / −0,59). Yani "her iki uçtaki sert hareket edenler
sonradan geri kalıyor" — yönlü bilgi değil, oynaklık cezası.

**ARAÇ DÜZELTMESİ:** B1'in yoğunlaşma dersi bu aracın resmi idam şartlarında YOKTU (5. şart
sonradan eklendi). "tüm" evreni 5. şartı geçmişti — eksik ölçü aleti onu ayakta tutuyordu.
Yeni testlerde yoğunlaşma şartı zorunlu.

**AÇIK KALAN:** Bu test coin SINIFI sorusunu cevaplamaz → §9.5'te kapatıldı.

### 9.5 COİN SINIFI (2026-08-11) — §12 madde 🔴 0 KAPANDI, hipotezin TERSİ çıktı
**Önce kritik düzeltme:** 31 Temmuz'un "27 kat fark" bulgusu (çekirdek 11 majör −0,794R/işlem
vs radar geniş evren −0,029R/işlem) **ÇİFT DEĞİŞKENLİYDİ.** 2026-08-11'de kodda doğrulandı:
ana sicil sıkışma skoru ≥70 → seviye kırılımı planı kullanıyor; radar ise `|24s değişim| ≥ %20
VE hacim ≥ 30M` alarmı. **İki sicil aynı sinyali kullanmıyor** → farkın coin sınıfından
geldiği söylenemezdi. Hipotez çürük değil, **fiilen hiç test edilmemişti.**

`sinif_testi.py` tek değişkenli halidir: CANLI config sabit (seviye-2.5, lookback 50,
filtresiz), değişen tek şey coin sınıfı. Evren pencere BAŞINDAKİ 30g medyan hacme göre
sıralanıp sabitlendi (sınıf ataması geleceğe bakmaz), 20'şerli üç kademe, 12 fold, 17.695 işlem.

| Kademe | Medyan hacim | İşlem | İsabet | netR | **ortNetR** | pozFold |
|---|---|---|---|---|---|---|
| BÜYÜK (1-20) | $585M | 5.925 | %32 | −150,6 | **−0,025** | 8/12 |
| ORTA (21-40) | $175M | 5.866 | %31 | −267,0 | **−0,046** | 7/12 |
| KÜÇÜK (41-60) | $113M | 5.904 | %31 | −375,7 | **−0,064** | 5/12 |

**Sıralama MONOTON ve hipotezin TERSİ yönünde:** coin büyüdükçe sonuç *iyileşiyor*.
"Majörlerde kırılım kalıpları yutuluyor, ince coinlerde çalışır" beklentisi veriyle
çelişiyor. Coin bazında da aynı: pozitif coin oranı 6/20 → 5/20 → 4/20, medyanlar
−0,029 → −0,036 → −0,071.

**İdam sınavı:** 1 ✅ (|−0,038| > 0,03 gürültü) · 2 ❌ **rejim** (BOĞA +0,002 / AYI −0,066 —
fark yalnız ayıda var) · 3 ✅ 8/12 · 4 ✅ monoton · 5 ⚠ teknik olarak geçti ama toplam
−0,509 → en iyi 3 fold çıkınca −0,016, yani farkın **%97'si 3 fold'dan**. **HÜKÜM: DESTEKLENMEDİ.**

**ASIL SONUÇ — sorunun kendisini geçersiz kılan bulgu: üç kademe de NEGATİF.** "Hangisi daha
az kötü" bir kârlılık sorusu değildir. Bu sinyalin kâr ettiği bir coin sınıfı yok → **havuz
değiştirmek çözüm değil.**

⚠ Kapsam sınırı: test en likit 60 coini kapsar (en ince kademe medyanı $113M); radarın
evreni $30M'a kadar iniyor. O bant test edilmedi — ama (a) eğilimin yönü inceye gittikçe
kötüleşiyor, (b) ince coinlerde delist yanlılığı ve spread en yüksek (spread verimiz hiç yok).
İkisi birlikte "daha inceye inelim" beklentisini desteklemiyor.

---

### 9.6 NAKİT-TAŞIMA / CARRY (2026-08-15) — ilk POZİTİF sonuç, ama yetersiz
**Neden bu aile:** §9.7'deki harita gösterdi ki ölçülen 13 adayın hepsi tek aileden —
**tahmin**. `carry_testi.py` başka bir aileyi ölçer: spot'tan al + perp'ten sat, birim
bazında tam delta-nötr, getiri fiyattan değil **funding ödemesinden** gelir. Tahmin yok.

İroni kayda değer: funding'in yapısal tek yönlülüğünü aylardır görüyorduk (sistem 5:1 SHORT
üretiyor çünkü funding çoğunlukla pozitif) ve onu *tahmin sinyali* sanıp kullanmaya çalıştık.
Oysa o bir gelir akışı.

30 coin (spot+perp kesişimi, pencere başındaki hacme göre), 540 gün, gerçek iki ayrı tarife
(spot taker %0,095 — perp'ten PAHALI), sermaye = spot notional × 1,5 (perp marjı dahil):

| Strateji | Brüt | Maliyet | Net | **Sermayeye göre yıllık** |
|---|---|---|---|---|
| A) Hep-açık, eşit ağırlık | +1,12% | −0,32% | +0,80% | **+0,40%** |
| B) Seçici (önceki 30g funding>0) | +2,91% | −0,32% | +2,59% | **+1,37%** |
| C) Kesitsel ilk 10 (haftalık) | +4,17% | −3,62% | +0,56% | +0,29% |

En iyi coinler CRV +2,83% · LINK +2,54% · BTC +2,34% (yıllık). En kötü ENA −3,82% ·
TRUMP −3,50% (bu coinlerde funding çoğunlukla NEGATİF — kısa taraf ödeyen taraf olur).

**AYNI PENCEREDE BAĞLAM (belirleyici):** BTC al-tut **−34,5%** (yıllık −24,9%), 293 coinin
**medyanı −81,7%**, yalnız 10'u pozitif. Yani carry, her şeyin çöktüğü 18 ayda **pozitif
kalan ilk şey** — ve en kötü çekilmesi **−0,78%**.

**HÜKÜM: tasarlandığı gibi çalışıyor, ama getiri yetersiz.**
- ✅ Delta-nötr vaadini tuttu: −82% medyan piyasada +0,4…+1,4%, çekilme %1'in altında.
- ❌ Büyüklük risksiz faizin ALTINDA. Borsa riski (FTX dersi) ve perp bacağı likidasyon
  riski **modellenmedi** — %1,4 için bu riskler alınmaz.
- ❌ Rejim ayrımı getiri profilini bitiriyor: BOĞA'da funding +2,65%/yıl, AYI'da −0,08%.
  **En çok boğada ödüyor — yani sadece long olmanın çok daha fazla ödediği anda.**
- C'de devir maliyeti brütün %87'sini yiyor → sık dengeleme carry'yi öldürür.

⚠ Kaldıraçla büyütülebilir görünüyor (çekilme küçük) — **ama kaldıraç, modellenmemiş iki
riski çarpar.** Kripto tarihinde bu tam olarak insanların patladığı yerdir. Kaldıraçlı carry
K3 öncesi gündeme ALINMAZ.

### 9.7 HARİTA — nerede aradık, nerede aranmadı (2026-08-15)
**Yapısal teşhis:** ölçülen 13 adayın hepsi *"fiyat bundan sonra ne yapacak?"* diye soruyordu.
Sinyali 13 kez değiştirdik, **oyunu hiç değiştirmedik.** Tahmin, hız/veri/sermaye
üstünlüğümüzün olmadığı en kalabalık masa — ve maliyet orada en çok ısırır.

| Aile | Durum |
|---|---|
| **Tahmin** (skor, funding, basis×2, seviye, geniş stop, trend, rejim, fade×2, kesitsel, coin sınıfı, F&G) | ❌ 13 aday, canlı doğrulanmış 0 |
| **Carry** (nakit-taşıma) | ⚠ Çalışıyor ama +0,4…1,4%/yıl — risksiz faizin altında (§9.6) |
| **Zorunlu akış** (likidasyon) | ⏳ Tek hayatta kalan aday; ~Aralık'ta ileriye dönük doğrulama |
| **Takvim/zorunlu arz** (unlock, funding saati, vade) | 🔲 Test edilmedi — funding saati bedava ölçülebilir |
| **Market making / borsalar arası arbitraj** | ⛔ Hız + altyapı + çoklu-borsa sermayesi yok |
| **Opsiyon / varyans primi** | ⛔ Veri yok (Deribit), ayrı beceri, kuyruk riski |

**Sistemi kapatan veri eksikleri** (her biri bir aileyi kapatıyor): spot verisi yoktu →
§9.6'da açıldı · emir defteri/spread YOK → icra gerçekçiliği ölçülemiyor · unlock takvimi
YOK (DefiLlama ücretli) · opsiyon YOK · likidasyon 2-4dk gecikmeli · icra ELLE
(eşzamanlı pozisyon sayısını sınırlar).

**Katman katman sistem:** veri toplama ✅ · sıkışma skoru ❌ ölü · plan üretimi ⚠ başabaş-negatif
· risk kapıları ❓ ölçülmedi · sicil/muhasebe ✅ · ölçüm araçları ✅ · teslimat ✅.
**Ölü kısım kodun ~%20'si; kalan %80 hangi fikirle çalışılırsa çalışılsın yeniden kullanılabilir.**

### 9.8 K2 ÖNCESİ HAZIRLIK TURU (2026-08-15) — F&G düştü, makro kapısı öne çıktı
Altı hazırlık işi tek turda yapıldı. **Sonuç: son tahmin adayı da düştü; buna karşılık
canlı sicilden beklenmedik bir bulgu çıktı.**

**B1 — F&G KAPISI ❌ DÜŞTÜ** (`fng_sinavi.py`). 2026-07-27'de +0,037 ile birinci çıkmıştı,
ama o sınavda **2. (rejim) ve 5. (yoğunlaşma) şartları YOKTU.** Taze fold'larla, beş şartla:

| Şart | Sonuç |
|---|---|
| 1. Gürültü tabanını aşıyor | ✅ +0,033 vs 0,030 — **kıl payı** |
| 2. İki rejimde aynı yön | ⚠ BOĞA **+0,000** / AYI +0,063 — boğada hiçbir şey yapmıyor |
| 3. Fold'ların çoğunda | ✅ 8/12 |
| 4. İki bacak da fiilen kesiyor | ❌ **LONG bacağı %0 kesiyor** (1537→1532). Kural iki taraflı değil |
| 5. En iyi 3 fold'suz ayakta | ❌ toplam +0,555 → **+0,001**. Avantajın **%100'ü 3 fold'dan** |

Aynı yoğunlaşma örüntüsü basis'i (%235) ve kesitsel momentumu da öldürmüştü. **Tahmin ailesi
artık 14 aday / 0 hayatta kalan.** ⚠ Ders: ölçü aletimiz aylarca eksikti (2, 4, 5 yoktu) ve
bu eksiklik **iki adayı birden** hayatta tutmuştu.

**B2 — SPREAD ✅ SORUN YOK** (`spread_olcum.py`). Aylardır açık duran ve üç denetimde K3'e
ertelenen madde. 737 sembol, 5 örnek: medyan spread %0,021-0,028 → yarım spread %0,011-0,014.
**Varsayımımız (%0,02/bacak) gerçeğin 1,4-1,9 KATI — yani muhafazakâr.** Spread/1R oranı:
büyük %0,16 · orta %0,61 · küçük %0,43 (endişe eşiği %5). **Negatif sonuçlarımız gizli
maliyetten değil.** ⚠ Sakin anda, top-of-book; derinlik ölçülmedi.

**B3 — VETO KATMANI: ölçülecek bir şey yok.** R/R vetosu (`rr1 < 2.0`) **yapısal olarak hiç
ateşlenemiyor**: rr1 = TP1_ATR/STOP_ATR = 5,2/2,5 = 2,08 sabit. Kalan iki veto (negatif
fiyat, stop'un girişe yapışması) matematiksel saçmalığı engelleyen emniyet kontrolleri —
seçicilik filtresi değil. **Vetolar "iyi işlemleri kesmiyor", çünkü normal kurulumda hiç
ateşlenmiyorlar.** Ayrıca hiçbir yerde loglanmıyorlar (log'da 0 kayıt).

**B4 — REJİM KÜMELENME ⭐ TEK POZİTİF BULGU** (`sicil_analiz.py`). Temmuz'dan beri işlenen
rejim damgaları ilk kez okundu:

| Makro kapısı | Ana sicil | Radar |
|---|---|---|
| ACIK | 41 işlem, %37, **+0,142R** | 87 işlem, %38, **+0,162R** |
| DIKKAT | 17 işlem, %24, **−0,325R** | 23 işlem, %13, **−0,630R** |

**İki BAĞIMSIZ sinyal (sıkışma skoru ve hareket alarmı) aynı yönü gösteriyor.** Birleşik:
ACIK 128 işlem **+19,96R** · DIKKAT 40 işlem **−20,01R**. OYNAK/SAKIN ve korelasyon uçları da
aynı yönde. ⚠ DIKKAT zaten boyutu yarıya indiriyor ve min_skor'u 80'e çekiyor — **buna rağmen**
bu kadar kötü. ⚠⚠ Kural VERİDEN türetildi ve n=40 → ön-kayıtlı doğrulama şart, tek başına
parametre değiştirmez.

**B5 — FUNDING ÖDEME SAATİ ❌ DÜŞTÜ** (`funding_saati.py`). Ön-kayıtlı hipotez (yüksek
funding'de ödeme öncesi baskı) **iki bacakta da tutmadı** (konum 7: +0,016% beklenen negatif;
konum 1: −0,003% beklenen pozitif). En büyük etki %0,016 vs maliyet %0,130 — **8 kat altında**.
En iyi 3 fold çıkınca işaret dönüyor. ⚠ İlk koşuda **birim hatası** etkiyi 100 kat büyük
gösterip "maliyeti aşıyor" dedirtmişti; düzeltildi.

**B6 — MONOTONLUK ❌ İLİŞKİ YOK.** skor↔netR korelasyonu: ana sicil **rho = −0,028** (n=58),
radar **rho = −0,119** (n=110). Skor kovaları zikzak; en yüksek kova (95-100) **iki sicilde de
en kötü**. Bu, `skor_gucu.py`'nin 964k kayıtla bulduğunun **canlı sicildeki bağımsız
doğrulaması** — iki ayrı yöntem, aynı sonuç.

**Yapısal not:** çıkış dağılımı tasarım gibi çalışıyor (stop medyanı tam −1,000R, tp1 +2,2R).
İsabet %33, başabaş ~%32,5 → **sistem tam başabaş noktasında salınıyor.** Kâr da etmiyor,
çökmüyor da; sonuçların ay-ay savrulması (Haz +9,4R · Tem −11,4R · Ağu +2,3R) bununla tutarlı.

### 9.9 İSTATİSTİKSEL SINAV (2026-08-18) — K2 hükmü sertleşti, makro bulgusu DÜŞTÜ
İki dış denetim belgesi de "risk-düzeltilmiş ölçüm yok" dedi ve haklıydılar. `metrikler.py`
kuruldu: equity eğrisi, Sharpe/Sortino/Calmar/maks çekilme, **PSR**, **bootstrap GA**,
**etiket permütasyonu**. Bağımlılık yok (saf Python).

**⚠ Dış belgenin önerdiği test yanlış kurulmuştu.** *"İşlemlerin SIRASINI karıştır, p<0,05
ise gerçek edge"* — sıra permütasyonu **toplamı değiştirmez**, ortalama R ona karşı
değişmezdir; o test edge'i ölçemez. Doğru araçlar kullanıldı: ortalama için **bootstrap**,
Sharpe için **PSR**, grup farkı için **etiket permütasyonu**.

| Küme | n | işlem başına | PSR (Sharpe>0) | Bootstrap %95 GA | Hüküm |
|---|---|---|---|---|---|
| **K2 (swing-1h)** | 32 | **−0,539R** | **%3,1** | **[−0,903 , −0,109]** | **sıfır DIŞINDA → sistematik** |
| Ana sicil (tümü) | 62 | −0,337R | %6,0 | [−0,718 , +0,057] | kararsız |
| Radar | 113 | −0,060R | %33,2 | [−0,319 , +0,205] | kararsız |

**K2 hükmü artık istatistiksel olarak sağlam.** Daha önce binom yaklaşımıyla "şanssızlık
olabilir (p≈%10)" demiştim; net-R üzerinden bootstrap sıfırı **dışlıyor** ve PSR %3,1.
Büyüklüğü de kullanan test, yalnız isabet sayan testten güçlüdür. Aykırı değer: en iyi ve
en kötü 5 işlem çıkarılınca gövde **−0,983R/işlem** — yani sonuç birkaç kötü işlemden değil.

**🔴 MAKRO KAPISI BULGUSU DÜŞTÜ (§9.8-B4 ve §12 madde 2 geçersiz).**
Bulgu VERİDEN türetilmişti ve şans olasılığı hiç ölçülmemişti. Etiket permütasyonu
(20.000 tekrar) ilk kez ölçtü:

| Sicil | ACIK | DIKKAT | fark | **p** |
|---|---|---|---|---|
| Ana | −0,288R (n=45) | −0,468R (n=17) | +0,180 | **0,695** ❌ |
| Radar | +0,097R (n=90) | −0,673R (n=23) | +0,770 | **0,021** ✅ |
| **Fisher birleşik** | | | | **0,073** ❌ |

Brüt R ile de aynı (Ana p=0,398 · Radar p=0,023) → muhasebe farkı değil.

**Neden düştü:** (a) ana sicilde fark hiçbir zaman anlamlı olmadı ve veri artınca **küçüldü**
(brüt fark 0,467 → 0,366); (b) tek anlamlı sonuç radar'da ve **~16 kırılım** incelendi
(rejim, makro, korelasyon, vol, yön, çıkış, skor, ay × 2 sicil) — bu sayıda testte p≈0,02
şans eseri yaklaşık bir kez beklenir. Bonferroni eşiği 0,05/16 ≈ 0,003.

⚠ **Kendi hatam:** 2026-08-17'de "bulgu zamanla güçleniyor" demiştim. Kümülatif görünüm
öyleydi ama doğru test uygulanmamıştı; gürültülü bir serinin kümülatif görüntüsüne
bakmışım. Düzeltildi.

**SONUÇ: hayatta kalan bulgu SIFIR.** Tahmin ailesi 14/14 düştü, carry yetersiz, makro
kapısı istatistiksel sınavı geçemedi. Bu, ikinci dış belgenin haklı olduğu noktadır —
**çoklu-karşılaştırma düzeltmesi (SPA / Reality Check) hiç uygulanmamıştı; uygulanınca
elde kalan bulgu kalmadı.**

### 9.10 YÖNTEM ADAYI (2026-08-18) — "kazananı arama, kanıtlanmış kaybedeni ele"
**Bu bir bulgu değil, bir ARAMA YÖNTEMİ önerisidir ve kendisi de sınanmaktadır.**

**Gözlem:** 14 aday "pozitif kenar" aradı, 0'ı bulundu. Ama istatistiksel sınav
**üç hücrede kanıtlanmış NEGATİF** buldu (bootstrap %95 GA sıfırı dışlıyor):
K2 −0,539R · radar/DİKKAT −0,673R · radar/SHORT −0,441R. **Kanıtlanmış pozitif hücre yok.**

Asimetri: sistem *kaybettireni* güvenilir tespit ediyor, *kazandıranı* hiç edemiyor.
Önerilen duruş: kazananı aramak yerine **kanıtlanmış kaybeden koşulları elemek.**

**Lehine olan:** eleme bir risk-azaltma duruşudur, kenar iddiası değildir; ve bu projede
kaybedenin yapısal sebebi ÖLÇÜLMÜŞTÜR (funding yapısal pozitif → SHORT eğilimi → BTC
sürüklenmesine karşı kayıp).

**⚠ ALEYHİNE OLANLAR — yöntemi kabul etmeden önce okunacak:**

1. **Aritmetik tuzak (en önemlisi).** En kötü alt kümeleri çıkarmak, kalan örneklemin
   ortalamasını **her zaman** yükseltir. Bu keşif değil, **aritmetiktir.** Örneklem-içi
   iyileşme hiçbir şeyin kanıtı değildir.
2. **Aynı çoklu-karşılaştırma riski.** Negatif hücreler, daha önce sahte pozitif üreten
   TARAMANIN AYNISI ile bulundu. ~20 hipotezde %95 GA ile ~1 hücrenin şans eseri sıfırı
   dışlaması beklenir.
3. **Hücreler bağımsız değil.** radar/DİKKAT ∩ radar/SHORT = **13 işlem** (DİKKAT'in %57'si).
   "İki bağımsız eleme" değil, kısmen tek bulgunun iki adı.
4. **Artımlı katkı ince.** LONG içinden DİKKAT elemesi yalnız **10 işlem** çıkarıyor
   (ort. −0,653R) — ve PSR'yi %84 → %95'e taşıyan tam olarak bu 10 işlem.
5. **Eleme kenar YARATMAZ, kaybı azaltır.** −0,337R'den −0,060R'ye gitmek sıfıra
   yaklaşmaktır, kâra değil. Kalanın gerçekten pozitif olması ayrıca kanıtlanmalıdır
   ve kanıtlanmamıştır (radar/ACIK+LONG'un GA'sı sıfırı hâlâ içeriyor).

**Durum: SINANIYOR.** `ON-KAYIT-radar-v2.md` yalnız bir kuralı değil, **bu yöntemi**
test eder. Eleme yaklaşımı ileriye dönük doğrulamayı geçerse yöntem meşrulaşır;
geçmezse yöntem de düşer. **O güne kadar yöntem olarak KULLANILMAZ** — tek uygulaması
ön kayıtlı testtir.


### 9.11 ÖLÇÜM YÖNTEMİ — İKİ KUSUR (2026-08-25, dış proje incelemesinden doğdu)

Kaynak: `github.com/irisphotofethiye-bocici/kripto-trade` ikinci incelemesi. İkisi de
**bizim kayıtlı hükümlerimizi** etkiliyor; ikisi de bu projede ÖLÇÜLDÜ.

**A — HAM GETİRİ HİÇ ÖLÇÜLMEDİ: "14/14 düştü" hükmü kısmen stopumuzun eseri olabilir.**

Dış projenin en pahalı dersi: *"bizim stopumuzun öldürdüğü bir kenarı 'sinyal boş' diye
kaydederiz."* Somut vakaları: `>40 LONG` hücresini "gürültü, öldü" diye gömmüşler; ham
ileri getiride **+2,284**, takip eden stopla **+2,379 (t=+3,24)**. Ölen sinyal değil,
stopları.

⚠ **Bize doğrudan uyuyor.** 14 adayın **tamamı** sabit **2,5 ATR stop + R/R 2,08** ile
ölçüldü. Ham ileri getiriyi hiç ölçmedik. Dolayısıyla §9.7'deki *"tahmin ailesi kapandı,
hayatta kalan sıfır"* hükmünün ne kadarı sinyalin, ne kadarı **mekaniğin** — bilmiyoruz.

**Ölçüm sırası (bundan sonra bağlayıcı):** `ham ileri getiri → ticaret mekaniği → portföy`.

**Somut sınama — hüküm yazmadan önce koşulur:** karşılaştırılan hücrelerde *stop genişliği*
ve *stop-olma oranı* eşit mi? Dış projede 3,3 kat değişiyordu; o tabloyla *"mekanik her
hücrede aynı"* savunması çöker. Ayrışıyorsa **ham getiri zorunlu.**

⚠ **Güven de şişer:** stop varyansı kırdığı için anlamlılık büyür — onlarda ham t=−0,90
iken stopla t=−4,11. **Yön aynı, güven yalan.** Bizim bootstrap aralıklarımız da
stop-kırpılmış R üzerinde: *"strateji para kazanıyor mu"* için doğru, *"sinyalde bilgi
var mı"* için değil. İki soru ayrı; aralıklar yalnız birincisini cevaplıyor.

**B — ALAN TANIMI PENCERE ORTASINDA DEĞİŞTİ (ölçüldü).**

`rejim.py`, **2026-07-18** (commit `55e137a`) — canlı ölçüm penceresinin ortasında:

```
- for s in olcucu.SYMBOLS:      # o gun 5 sembol: BTC/ETH/SOL/LINK + LAB
+ for s in KOR_SYMS:            # sabit 4 major
```

Aynı commit `SYMBOLS`'ü 5→11 yaptı; sabitleme metrik kaymasın diye eklenmişti — ama
**LAB, kırılmadan önceki korelasyona dahildi**, sonra değil.

| | kırılma öncesi damgalı | sonrası | korelasyon medyanı |
|---|---|---|---|
| Ana sicil | **4** | 84 | **0,85 → 0,70** |
| Radar | **28** | 361 | **0,84 → 0,70** |

⚠ **Dürüst sınır:** farkın tanımdan mı piyasadan mı geldiği bu veriyle **ayrıştırılamaz** —
iki dönemi tek tabloda toplamayı geçersiz kılan da tam olarak budur.

**Etkilenen:** `sicil_analiz.py`'nin "rejim durumu (damga)" ve "korelasyon bandı" tabloları
(32 kayıt kirli, %5,7). **Etkilenmeyen ve bu oturumun hükümleri buna dayanıyor:** boğa
öncesi/sonrası ayrımı (tarihe göre), al-tut kıyası (fiyata göre), G2/G4 gerekçeleri.

**Refleks (bağlayıcı):** bir alanla uzun pencere bölmeden önce `git log -S"<alan>"` koştur.

**C — YAN BULGU: `/futures/data/*` UÇLARI ~30 GÜNLÜK (kendi ölçümümüz).**
`globalLongShortAccountRatio` · `openInterestHist` · `takerlongshortRatio`:
**gerçek derinlik 29,6 gün** (ölçüldü 2026-08-26: BTCUSDT 2026-07-27 18:30 →
2026-08-26 08:10, uç başına 8.500 nokta). `klines` ve `fundingRate` kalıcı.

🔴 **İLK ÖLÇÜMÜM YANLIŞ OKUNMUŞTU — düzeltme (2026-08-26).** 25 Ağustos'ta
"29 gün geriye OK, 32 günde HTTP 400" yazmıştım. Doğrusu: **bu uçlar `startTime`
parametresini YOK SAYIYOR.** 2, 10 ve 25 gün öncesi verilen üç ayrı istek
**aynı pencereyi** döndürdü (2026-08-24 14:35 → 2026-08-26 08:10). "32 günde
400" ise veri derinliği değil, **parametre doğrulaması** — 30 günü aşan
`startTime` reddediliyor, o kadar.
**Sayfalama YALNIZ `endTime` ile geriye doğru yapılır.** İlk `perp_arsiv.py`
sürümü `startTime` kullandı ve her sembolde yalnız son 500 noktayı (~41 saat)
aldı; "29 günlük dolgu yapıldı" sanıldı. `endTime` ile yeniden yazıldı, gerçek
kapsama 29,6 gün çıktı.
→ **`ls_ratio` sonradan çekilemez**, yalnız o an arşivlenirse vardır. §12 madde 7'nin
(L/S simetrisizliğinin ZARARI) testi, arşivleme başlamadan **hiçbir zaman** yapılamaz.
Bekleyenler listesi madde **7.1** — acil, dondurulmuş dosyalara dokunmadan yapılabilir.

---

---

## 10. KARAR KAPILARI (disiplinin kalbi)

- **K1 (config onayı) — TAMAM.** Walk-forward config seçimi; canlı parametre değiştirilmedi.
- **K2 (edge testi) — BEKLİYOR.** 30+ kapanmış swing işlem dolunca monotonluk + rejim-kümelenme
  + aday filtreler tek oturumda değerlendirilir. **O güne kadar PARAMETRE DEĞİŞİKLİĞİ YASAK.**
- **K3 (gerçek para) — ÇOK İLERİDE.** Şartlar: 30+ işlem net pozitif + iki farklı rejim +
  icra gerçekçiliği (gap/kayma ölçümü). Öncesinde gerçek para YOK.

---

## 11. ANLIK DURUM (2026-08-19 — eskir)

Sayılar **kanonik evrenden**: geri-doldurma ve deneysel kayıtlar HARİÇ (`defter.ozet()` ile
aynı süzgeç). ⚠ Bu süzgeci atlayan sayımlar sicili ~2 katına şişirir — 2026-08-15'te bir kez
yapıldı ve düzeltildi.

**K2 KAPANDI ve GEÇİLEMEDİ.** 33 işlem · 7 kazanç / 26 kayıp · isabet **%21,2** ·
net **−15,19R** (−0,460R/işlem). Bootstrap %95 GA **[−0,839, −0,028] sıfırı DIŞLIYOR**,
PSR %4,7 → kayıp **sistematik, şanssızlık değil**. Başabaş için gereken isabet %32,5.

| Sicil | Kayıt | Kapalı | İsabet | Net | İşlem başına | Bootstrap GA | PSR |
|---|---|---|---|---|---|---|---|
| Ana | 146 | 63 | %31,7 | −18,84R | −0,299R | [−0,680, +0,094] içeriyor | %8,2 |
| Radar | 266 | 120 | %32,5 | −7,92R | −0,066R | [−0,313, +0,186] içeriyor | %30,8 |

Açık/bekleyen: ana 3, radar 11.

**Hayatta kalan bulgu SIFIR.** 14 tahmin adayı düştü; son aday (makro kapısı) 2026-08-18'de
etiket permütasyonuyla düştü (§9.9). Carry ölçüldü ama risksiz faizin altında (§9.6).

**AÇIK ÖN KAYIT — `radar-v2`** (`ON-KAYIT-radar-v2.md`, kayıt anı 2026-08-18T20:14:04Z,
commit `a3f949e`). Kural: kayıttan sonra oluşan radar tahminleri, `LONG` **ve** `ACIK`.
Hedef 30 kapanmış işlem. **Durum: 0/30, 21 saat.** Sebep: FOMC penceresi boyunca makro kapı
DİKKAT'te kaldı; üretilen 7 tahminin 7'si de DİKKAT damgalı. **Test durmadı, sıra bekliyor**
— kapı ACIK'a dönünce sayaç işler. ⚠ ~19 günlük tahmin bir TABAN'dır, takvim değil: makro
pencereler kümelenir. Ölçüm `onkayit_radar.py` (30'a kadar hüküm basmaz).

**BEKLEYEN KARAR (kullanıcıda):** K2 geçilemedi, sistem tahmin üretmeye devam etsin mi?
(A) aynen devam · (C) tahmin üretimi dursun/veri aksın · (D) tamamen durdur.
(B — makro sertleştirme — §9.9 ile düştü, artık geçersiz.)

**Sistem sağlığı:** izleyici + radar çalışıyor · eşikler 11/11 sağlam (0 hatalı, 0 bayat —
15 Ağustos düzeltmesi tutuyor) · makro DİKKAT (FOMC) · rejim SAKIN.

---

## 12. K2 / K3 GÜNDEMİ (sırası gelince, veriyle)

**⚠ BU GÜNDEM 2026-08-15'TE BAŞTAN YAZILDI.** Eski sıralama ("hangi filtreyi ekleyelim")
geçersiz: `skor_gucu.py` (964k kayıt) + B6 (canlı sicil, rho≈0) skorun yön bilgisi
taşımadığını **iki bağımsız yöntemle** gösterdi, B1'de son filtre adayı (F&G) da düştü.

**K2 GÜNÜ — GERÇEK SIRALAMA:**
1. 🔴 **Sıkışma skoru korunacak mı?** Diğer her şey buna bağlı. "Hayır" ise aşağıdaki
   sekiz madde tek kararla kapanır: skor tabanı 70→75 · L/S bileşeni · korelasyon
   histerezisi · OYNAK'ta-LONG-yok · trend filtresi · funding+trend kombosu ·
   likidasyonun skora katkısı · skor ağırlıkları validasyonu.

   🔴🔴 **ÖLÇÜLDÜ — 2026-08-31. `ON-KAYIT-skor-yonu.md` (ön kayıt `64fb19e`,
   araç `c0456ee`, sonuç `b01d493`). HÜKÜM: İŞARET TERS, 1/4.**

   Skorun ileri getiriyle ilişkisi **ilk kez doğrudan** ölçüldü — daha önce her
   ölçümde skor *veri* olarak kullanılmıştı, *sınanacak iddia* olarak değil.
   Kaynak: `olcucu.log`'un fiilen hesaplanmış skorları (yeniden kurulum YOK →
   eşik geçmişi / ileriye bakma sorunu yok). 65 gün · 11 sembol · 12.913 gözlem.

   | LS bandı | n | ort +24s getiri |
   |---|---|---|
   | [0,20) | 589 | **−1,615%** |
   | [20,40) | 2.729 | −0,245% |
   | [40,60) | 5.167 | +0,018% |
   | [60,80) | 4.096 | +0,259% |
   | [80,100] | 332 | **+0,441%** |

   **Spearman ρ = +1,000** — beş bandın beşinde düzenli. Skor *"LONG sıkışması
   var, SHORT'la"* dedikçe fiyat ertesi 24 saatte **daha çok yükseliyor**.
   S1 kaldı (ρ=+1,000 vs gereken ≤−0,75) · S2 kaldı (%42 vs ≥%60) ·
   S3 kaldı (p=0,9715) · S4 geçti.

   ⚠ **Kapsam (post-hoc):** tersleşme **boğa ürünü DEĞİL** — boğa öncesi 54
   günde **en güçlü** (+0,392%, ρ=+1,000); boğada sıfıra yakın (11 gün, hüküm yok).
   ⚠ **Dürüstlük:** S4 *işaret* olarak geçti ama büyüklük +0,318% → +0,073%
   düştü ve o değer testin **kendi görülebilirlik tabanının (%0,489) altında**.
   **Yön güvenilir, büyüklük gösterilemez.** En sağlam parça monotonluk.

   ⛔ **"Skoru tersine çevir" DEMEK DEĞİLDİR** — bu **ham sinyal** aşamasıdır;
   mekanik ve maliyet aşamaları yapılmadan kural değişikliği çıkarılamaz.

   📌 **Bu maddenin cevabı artık ölçülü bir dayanağa sahip.** Alt sekiz maddenin
   (skor tabanı · L/S bileşeni · ağırlık validasyonu …) **önceliği düştü**:
   bütünün yönü tersken bileşen ince ayarı ikincil bir sorudur.
2. ❌ **Makro kapısı DIKKAT'te kapansın mı? — DÜŞTÜ (2026-08-18, §9.9).** Etiket
   permütasyonu: ana sicil p=0,695 · radar p=0,021 · Fisher birleşik p=0,073.
   ~16 kırılım incelendiğinden tek anlamlı sonuç çoklu-karşılaştırmayla açıklanabilir.
   Gündemden düştü; tekrar açma. **Hayatta kalan bulgu artık SIFIR.**
3. **Eşik dejenerasyonu fallback'i** — tespit edildi, uygulanmadı (BNB'nin SHORT kolu ölü,
   6 sembolde funding tavanına yapışma). Konfig etiketiyle birlikte.
4. **"SHORT çalışmıyor" maddesini sicil bazında yeniden kur** (eski hali iki sicili
   topluyordu — §11'deki düzeltmeye bak).
5. **Meta karar: sistem tahmin üretmeye devam etsin mi?** Etmezse veri toplama sürer
   (likidasyon doğrulaması buna bağlı).
6. 🆕 **FUNDING BİLEŞENİNİN AYRIM GÜCÜ** (2026-08-23'te eklendi — **HENÜZ TEST EDİLMEDİ**).

   **Ölçülen olgu:** 11 sembolün **6'sında** `long_crowded` eşiği funding tavanına
   yapışmış — beşi tam %0,0100'de (LINK, DOGE, ZEC, ADA, NEAR), LAB kendi tavanında
   (0,000257). `olcucu.squeeze_scores()` şunu yapıyor:

   ```
   if funding >= long_c:   ls += 30      # LONG SQUEEZE bileşeni
   ```

   Eşiğin kendisi tavandayken ve funding de tavandayken bu koşul **koşulsuz doğru**
   olur → LONG-squeeze skoruna **sabit +30 puan**. Ve LONG squeeze = aşağı risk =
   **SHORT sinyali**.

   **Neden önemli:** bu, B6'da bulunan "skorun yön bilgisi taşımaması" hastalığının
   aynısı olabilir — ama **daha kötüsü**, çünkü ölü ağırlık nötr değil, sistemi
   **kanıtlanmış kaybeden yöne** itiyor. Canlı sayım destekliyor: ön kayıttan beri
   üretilen 103 radar tahmininin **73'ü SHORT, 30'u LONG** — hem de boğada.
   Ve radar SHORT boğa öncesi bile n=48, −0,378R, GA [−0,696, −0,020] (sıfırı dışlıyor).

   **Test (L/S bileşeninde kullanılan yöntemin aynısı):** işlemleri *funding bileşeni
   ateşledi / ateşlemedi* diye ayır, net-R'leri karşılaştır (bootstrap + etiket
   permütasyonu). **Ayrım yoksa bileşen ölüdür** ve skordan çıkarılması gerekir.

   🔴 **ÖLÇÜLDÜ — 2026-08-24, `ariza_olcum.py`. HİPOTEZ DOĞRULANMADI.**

   Yöntem: vekil değil **birebir yeniden kurulum**. `premiumIndex.lastFundingRate`
   = son ödenen funding; tam geçmişi `/fapi/v1/fundingRate`'te. `long_crowded` =
   son 500 ödemenin 85. persentili. İkisi de tahmin anına göre yeniden hesaplandı
   → "bileşen ateşledi mi" sorusu kodun yaptığı hesabın aynısıyla cevaplandı.
   **530/537 tahmin yeniden kurulabildi.**

   **6a — MEKANİZMA: DOĞRULANDI, ezici biçimde.**

   | Küme | n | LONG | SHORT | SHORT payı |
   |---|---|---|---|---|
   | +30 ateşledi | 259 | 62 | 197 | **%76,1** |
   | ateşlemedi | 271 | 142 | 129 | %47,6 |

   Fark **+28,5 puan**, permütasyon **p < 0,00001** → Bonferroni eşiğini (0,00217)
   **GEÇİYOR.** Bileşenin yönü sürüklediği artık ölçülmüş bir olgudur.

   **6b — ZARAR: DOĞRULANMADI. Üstelik işaret TERS.**

   | Küme | n | net R | işlem başına | %95 GA |
   |---|---|---|---|---|
   | +30 ateşledi | 259 | **+7,89** | +0,030 | [−0,071, +0,137] |
   | ateşlemedi | 271 | **−17,58** | −0,065 | [−0,183, +0,058] |

   Fark **+0,095R ateşleyenin LEHİNE**, p=0,243 → eşiği geçmiyor. İki aralık da
   sıfırı kapsıyor: hiçbiri kanıtlanmış değil ve **birbirlerinden ayrılamıyorlar.**

   **6c — YAYGINLIK:** eşik tavanda %34, funding tavanda %25, **ikisi birden
   (+30 kaçınılmaz) %16.** Yani "6/11 sembolde eşik yapışmış" ifadesi operasyonel
   etkiyi ABARTIYORDU — sembol değil, sembol-zaman kombinasyonu sayılmalı.

   ⚠ **BETİMLEYİCİ AYRIŞTIRMA (test DEĞİL, hücre seçimi — ders 5):**
   +30/LONG n=62 **+0,172** · +30/SHORT n=197 **−0,014** ·
   ateşlemedi/LONG n=141 +0,138 · ateşlemedi/SHORT n=129 **−0,279**.
   Yani LONG iki grupta da benzer; fark tamamen SHORT'ta: bileşen ateşlediğinde
   SHORT'lar **başabaşa yakın**, ateşlemediğinde **ağır kaybediyor**. Bu, sistemin
   kurulduğu tezin ta kendisi (kalabalık long → long squeeze → aşağı). **Post-hoc
   hücredir, bulgu değildir** — ama "bileşeni çıkaralım" fikrini zayıflatır.

   **HÜKÜM: madde yeniden yazıldı.** Eski hâli *"muhtemelen ölü ağırlık, test et
   ve çıkar"* diyordu. Ölçüm sonrası: **mekanizma kanıtlandı, zarar çürütüldü,
   olası DEĞER var. Sınanmadan ÇIKARILMAZ.** K2'de yapılacak iş "çıkarmak" değil,
   "eşik tavana yapıştığında ne oluyor" sorusunu ayrıca sınamak.

   ⚠ Bu ölçüm 22. hipotezdir. Hiçbir şey düzeltilmedi; düzeltme `squeeze_scores`a
   dokunmayı gerektirir → ön kayıt kapanınca.

   🔴 **AYNI GÜN AKŞAM DÜZELTİLDİ — kapsam ana sicille sınırlı sanılandan farklı.**
   İlk yazıldığında bu madde radar'ın short eğilimini de açıklıyor sanılmıştı. **Radar
   `esikler.json`'ı KULLANMIYOR** — `tarayici.kalibre()` ile her sembol için taze eşik
   üretir (funding'in 15/50/85 persentili). Ölçüldü: eşiğin tavana yapışma oranı
   **ana sicil %55 (6/11), radar evreni %35 (14/40)**. Yani mekanizma radarda da var
   ama zayıf — ve bu, ana sicilin neden %79 SHORT, radar'ın neden %52 (dengeli)
   olduğunu tutarlı biçimde açıklıyor. Madde geçerli; kapsamı ana sicil ağırlıklı.

7. 🆕 **L/S BİLEŞENİNİN SİMETRİSİZLİĞİ** (2026-08-23 akşam denetiminde bulundu —
   **HENÜZ TEST EDİLMEDİ**). Madde 6'dan daha genel, çünkü **her iki sicili de** etkiler.

   `olcucu.squeeze_scores()` içinde iki dal:

   ```
   SHORT-squeeze (LONG sinyali) :  if ls_ratio < 1.0  ->  ss += 20
   LONG-squeeze  (SHORT sinyali):  if ls_ratio > 1.5  ->  ls += 20
   ```

   Eşikler **koda gömülü sabit** (1,0 ve 1,5). Canlı ölçüm (60 sembol, radar evreni):
   **medyan ls_ratio = 1,50.**

   | ls_ratio | Hangi dala +20 | Sembol payı |
   |---|---|---|
   | < 1,0 | LONG sinyali | **%17** |
   | 1,0 – 1,5 | hiçbiri | %33 |
   | > 1,5 | **SHORT sinyali** | **%50** |

   → **+20 puan, SHORT sinyaline 3 kat daha sık gidiyor.** Eşikler dağılımın etrafında
   simetrik değil; medyan tam olarak üst eşiğin üzerinde duruyor.

   **Asıl tutarsızlık:** `funding` persentille kalibre ediliyor (15/50/85), `oi_rising`
   persentille kalibre ediliyor (80), ama **`ls_ratio` hiç kalibre edilmiyor.** Bu bir
   tasarım kararı gibi değil, gözden kaçmış gibi duruyor. (Kalabalık-taraf mantığı
   gereği ikisinin de persentil olması beklenirdi.)

   **Test (madde 6 ile aynı yöntem):** işlemleri L/S bileşeni ateşledi/ateşlemedi diye
   ayır, net-R karşılaştır. Ayrıca: eşikleri persentile çevirmek yön dağılımını
   değiştiriyor mu, geriye dönük ölç.

   🔵 **ÖLÇÜLDÜ — 2026-08-24. GEÇMİŞE DÖNÜK TEST KURULAMIYOR.**
   `ls_ratio` **hiçbir yerde saklanmıyor**: defterde yok, `olcucu.log`'da yok
   (log yalnız SS/LS toplamını yazıyor, bileşenleri değil), `signals.json` anlık.
   Ve funding'den farklı olarak **API geçmişi de yetersiz** (~30 gün).
   Bu bir **veri eksiği**, yöntem eksiği değil.

   **Arızanın büyüklüğü bugünün evreninde ölçüldü (69 sembol):** medyan ls_ratio
   **1,46**; mevcut eşiklerle `<1,0` %19 (LONG'a +20) vs `>1,5` %46 (SHORT'a +20)
   → **+20 puan SHORT'a 2,5 kat daha sık.** Persentille (15/85) kalibre edilseydi
   %16 / %16 — tanım gereği simetrik.

   ⚠ **ZARAR ÖLÇÜLEMEDİ.** Madde 6'nın dersi burada da geçerli: simetrisizlik
   ölçülmüş bir OLGU, ama zarar verdiği **kanıtlanmadı** ve kanıtlanmadan
   düzeltilmemeli. Madde 6'da tam olarak bu varsayım çürüdü.

   ~~**YAPILACAK (ön kayıt kapanınca): önce `ls_ratio`'yu loglamaya başla.**~~
   ~~Düzeltme değil, ÖLÇÜM açar — ileriye dönük test ancak öyle mümkün olur.~~

   ✅ **VERİ ARTIK VAR (2026-08-30).** Loglama gerekmedi: `perp_arsiv.py` (2026-08-26'da
   zamanlandı) **aynı ucu** arşivliyor — `globalLongShortAccountRatio`, 5dk, 66 sembol.
   Geri okuma kanıtlandı: API'den çekilen taze seri ile arşiv, örtüşen damgalarda
   **808/808 birebir eşit** (fark 0,000000).

   🔴 **AMA TEST YİNE KURULAMIYOR — bu kez SEBEP DEĞİŞTİ: veri değil, GÜÇ.**
   Ölçüldü (2026-08-30):

   | | ana sicil | radar |
   |---|---|---|
   | `ls_ratio` geri kurulabilen kapanmış işlem | 71/164 (%43) | 66/187 (%35) |
   | görülebilen en küçük fark | **~0,97R** | **~0,95R** |
   | madde 6'da ölçülen gerçek fark | \_ | **0,095R** |
   | 0,095R'yi görmek için gereken işlem | **3.668** | 3.294 |
   | ana sicilin üretim hızı (2,7 işlem/gün) ile | **~4 YIL** | — |

   ⚠ **Yanlılık ayrıca var:** radar kolunda 91 sembolün **49'u arşivde yok** (arşiv
   hacim liderlerini seçti) → likidite yanlılığı hipotezle etkileşebilir. Ana sicil
   (11 sembolün 11'i arşivde) yalnız zaman yanlılığı taşır.

   🔴🔴 **BUNUN MADDE 7'DEN BÜYÜK ANLAMI — K2 GÜNDEMİNİN TAMAMINI İLGİLENDİRİR:**
   *"Zarar kanıtlanmadan düzeltme yapma"* kuralı, **işlem-bazlı R farkı** üzerinden
   uygulandığında **yanlışlanamaz** hâle geliyor. Katkısı ~0,1R olan hiçbir skor
   bileşeni bu defterle ne zararlı ne faydalı gösterilebilir — ne bugün, ne 2030'da.
   Kural, bileşenleri sonsuza kadar dondurur.

   ✅ **ÇIKIŞ YOLU — soruyu İŞLEME değil SİNYALE sor.** Bileşen sorusu ileri getiri
   üzerinde, tüm sembol-saatlerde sorulursa örneklem işlem sayısına bağlı olmaz:
   66 sembol × ~9.564 nokta ≈ **630.000 gözlem**. Bu, projeye 2026-08-25'te alınan
   *"ham ileri getiri → ticaret mekaniği → portföy"* sırasının (bekleyen-isler 7.2)
   madde 7'ye uygulanmış hâlidir. **Doğru sıra: önce sinyal aşaması.**
   ⚠ Ve o aşamada bile hüküm ancak *sinyalde bilgi var mı* sorusunu cevaplar;
   *"bileşeni çıkaralım mı"* kararı portföy aşamasını bekler.

   ⚠ **ŞİMDİ DÜZELTİLMEYECEK** — `squeeze_scores` değişirse koşan ön kayıt
   geçersiz olur (ON-KAYIT-radar-v2.md §6: "plan mekaniği değişirse iptal").

8. 🆕 **RADAR'DA RİSK TAVANI VE COOLDOWN YOK** (2026-08-23 denetimi). Ana sicilde
   ikisi de var (`defter.RISK_TAVANI_PCT = 2.0`, `COOLDOWN_SAAT = 12`); `radar_defter.py`'de
   **hiçbiri yok**. Ölçüldü: radar tepe noktada **10 pozisyon birden**, **7'si aynı yönde**.
   Coinler arası korelasyon 0,69 → o 7 pozisyon 7 ayrı bahis değil, tek bahsin 7 kopyası.
   ⚠ Korumasız olan sicil, ön kaydın test ettiği sicil. **Ön kayıt kapanır kapanmaz ilk iş.**
❌ **F&G kapısı** — 2026-08-15'te beş şartlı sınavda DÜŞTÜ (§9.8-B1). Tekrar açma.

❌ **DÜŞENLER (tekrar açma):** seviye penceresi, mutlak funding tabanı, basis (iki kez),
geniş-stop/zaman-aşımı çıkışı.

⚠ **YÖNTEM UYARISI:** K2 günü hepsini birden uygulama — **1-2 değişiklik**, gerisi sonraki
tura. Aksi halde sonraki 30 işlem iyi/kötü gittiğinde hangisinin etkilediği ölçülemez.

🔵 **K2 OTURUMU ERTELENDİ — İPTAL DEĞİL (2026-08-23, kullanıcı kararı).** Gündem aynen
duruyor. Tetik: `radar-v2` ön kaydı kapanınca (~30 Ağu tahmini) ve **doğru maliyet
modeliyle** (`pozisyon.py` — 2026-08-23'te kuruldu ve 211 geçmiş işlemde doğrulandı).
Gerekçe: K2 kararlarının hepsi net-R'ye bakıyor; net-R'nin muhasebesi yenilendiği için
oturumu eski aletle açmak yanlış olurdu.

**K3 günü (gerçek para öncesi zorunlu):**
- Gap/kayma nicelleştirme (sicilimizin çalkantıda iyimserliği)
- Bileşik aşınma / volatilite aşındırması (pozisyon boyutlamada varyans drenajı)
- Açık pozisyon ara-uyarıları ("stop'a yaklaştın / kâr al" — skill dersi)
- Defter GERÇEK işlemleri de kaydetsin (`pozisyonlar` dizisi kullanılmıyor)
- Otonom kâğıt-ticaret botu (dış skill dersi) | BTC min-notional kısmi-TP kontrolü

**Ertelenmiş:** B2 (makro girdi: 10Y/ETH-BTC denemesi; basis düştüğü için tetik artık yalnız K2).

**Küçük açık sınırlar:** spread/likidite kontrolü YOK | takvim hafta-devri boşluğu (yalnız
`thisweek` çekiliyor) | tarayici.kalibre ~200 funding kaydı | kademe tespiti ~2-4dk gecikmeli.

---

## 13. GÜVENLİK DEĞİŞMEZLERİ (asla ihlal edilmez)

- Hiçbir ajan işlem/para çekme yapmaz; emir her zaman kullanıcıda.
- API anahtarları + kişisel sicil gitignore'lu, GitHub'a gitmez.
- Bot salt-gönderim (Telegram), borsa/para yetkisi yok.
- Gerçek para: kanıtlanana kadar (K3) HAYIR.
- Otomatik/recurring her şey KOD olmalı (Claude kendi kendine çalışmaz).
