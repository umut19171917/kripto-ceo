# KRİPTO SİSTEMİ — GÜNCEL SKILL (çalışan sistemin tam tarifi)

> **Bu dosya nedir:** Sistemin ŞU ANKİ gerçek halinin tam anlatımı. `kripto-SKILL.md`
> (Faz-0 doğum belgesi, LLM-merkezli eski tasarım) DEĞİL — bu, kodda fiilen çalışan
> sistemin skilli. Anlık sayılar (sicil, K2 sayacı, rejim) zamanla eskir; mimari ve
> disiplin kalıcıdır.
> **Anlık görüntü tarihi:** 2026-07-23.
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

**AÇIK KALAN:** Bu test coin SINIFI sorusunu (§12 madde 🔴 0, 31 Temmuz ayrışma bulgusu)
cevaplamaz — "bizim sinyalimiz orta ölçekte daha mı iyi çalışıyor" ayrı bir soru, hâlâ açık.

---

## 10. KARAR KAPILARI (disiplinin kalbi)

- **K1 (config onayı) — TAMAM.** Walk-forward config seçimi; canlı parametre değiştirilmedi.
- **K2 (edge testi) — BEKLİYOR.** 30+ kapanmış swing işlem dolunca monotonluk + rejim-kümelenme
  + aday filtreler tek oturumda değerlendirilir. **O güne kadar PARAMETRE DEĞİŞİKLİĞİ YASAK.**
- **K3 (gerçek para) — ÇOK İLERİDE.** Şartlar: 30+ işlem net pozitif + iki farklı rejim +
  icra gerçekçiliği (gap/kayma ölçümü). Öncesinde gerçek para YOK.

---

## 11. ANLIK DURUM (2026-07-27 — eskir)

- **Ana sicil K2 sayacı: ~13/30** girilmiş-kapanmış swing (tempo ~5/hafta → ~3 hafta kaldı).
- Ana sicil toplam: 43 kapalı, %33 isabet, brüt +2.98R / **net −12.64R**. 4 açık.
- Radar sicili: 26 kapalı, %25 isabet, net −7.37R.
- Deneysel (LAB): 1 kapalı, net +0.86R.
- Rejim: SAKIN (korelasyon 0.84-0.85, eşik dibinde salınıyor). Makro kapı: ACIK.
- Açık risk: LONG %2.0 / SHORT %2.0 → **her iki yönde tavan dolu**, yeni tahmin açılmıyor.
- **Hüküm:** kanıtlanmış edge YOK; her iki sicil negatif; disiplin = veri biriktir, K2'yi bekle.

---

## 12. K2 / K3 GÜNDEMİ (sırası gelince, veriyle)

**K2 GÜNÜ — ÖNCELİK SIRASI** (2026-07-27 aday sınavının çıktısı; §9.1'e bak):
1. ✅ **F&G kapısı** — sınavdan birinci çıktı; ön-kayıtlı, gürültü üstü, tek çoğunluk-pozitif.
   O gün: SHORT-yarısı tek başına vs tam kural + taze fold'larda tekrar.
2. ⚠ **OYNAK'ta LONG yok** — en iyi toplam ama kural VERİDEN türetildi → ön-kayıtlı tekrar şart.
   Ayrıca canlı sicilin rejim damgalı kayıtlarıyla çapraz kontrol.
3. Korelasyon histerezisi (1 veya 2 kabul edilirse önemi artar)
4. Skor tabanı 70→75 | L/S bileşenini at (ikisi de VERİ-BLOKE: derin OI/LS geçmişi yok →
   sadece canlı sicille test edilebilir)
5. Likidasyon verisinin skora katkısı | monotonluk testi tekrarı (swing verisiyle)
6. ⚠ Trend filtresi — gürültü tabanı bulgusundan sonra ŞÜPHELİ, yeniden sınanmalı

❌ **DÜŞENLER (tekrar açma):** seviye penceresi, mutlak funding tabanı, basis (iki kez),
geniş-stop/zaman-aşımı çıkışı.

⚠ **YÖNTEM UYARISI:** K2 günü hepsini birden uygulama — **1-2 değişiklik**, gerisi sonraki
tura. Aksi halde sonraki 30 işlem iyi/kötü gittiğinde hangisinin etkilediği ölçülemez.

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
