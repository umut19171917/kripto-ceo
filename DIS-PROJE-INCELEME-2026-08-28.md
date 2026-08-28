# Dış Proje İncelemesi — `irisphotofethiye-bocici/kripto-trade`

**İnceleme tarihi:** 2026-08-28
**İncelenen sürüm:** `df96b83` (son commit 2026-08-25 19:44 +0300)
**İnceleyen:** Claude (Opus 5), kullanıcı talebiyle
**Yöntem:** Depo yerel bir kopyaya klonlandı ve **salt okundu**. Hiçbir betiği
çalıştırmadım — bulgularımın tamamı kaynak kodu ve belge okumasına dayanır.
Rakamların bir kısmı onların kendi ölçüm kütüğünden alıntıdır (kaynağı belirtildi),
bir kısmı benim bağımsız tespitimdir (satır numarası verildi).

---

## 1. Bir cümlede

Bu proje, **olağanüstü iyi bir ölçüm aleti** ile **o aletin çoktan çürüttüğü bir bot**
inşa etmiş; ikisi arasında, botu düzeltmeyi yasaklayan bir kural duruyor.

Yani asıl mesele "bot kötü mü" değil. Bot kötü olduğunu **kendisi ölçtü** —
ve düzeltilemiyor.

---

## 2. Sistem ne

Claude Code üstünde koşan iki katmanlı bir kripto analiz sistemi:

| katman | ne yapar |
|---|---|
| **CEO beyni** (`.claude/skills/kripto/SKILL.md`) | LLM; insan yüzlü analiz, senaryo, karar önerisi |
| **Deterministik Python** | Radar, ölçücü, makro, nöbetçi, panel — 0 LLM tokeni |
| **`testbot.py`** (1.941 satır) | **SANAL** $10.000 kâğıt bot; 7,5 dakikada bir tur |

Gerçek emir gönderen kod **yok** ve eklenmeyeceği yazılı. Bizim sistemle aynı
duruş.

**Ölçek:** 910 takipli dosya · kökte ~22.000 satır Python+Markdown ·
`olcumler.md` **5.015 satır** · `fikir-defteri.md` **3.908 satır** ·
`scratchpad/` altında **131 ölçüm betiği** · `.git` 12 MB (temiz).

**Bot tezi:** momentum takipçisi değil — **ortalamaya dönüş + rejim okuyucu**.
Aşırılık tespit et, seçili SHORT'la fade'le, rejim kapılarıyla frenle.

### Çalışan zamanlanmış görevler
`KriptoTestBot` (7,5 dk) · `KriptoRadar` (15 dk) · `KriptoNobetci` (5 dk) ·
`KriptoIzleyici` (5 dk) · `KriptoPiyasa` (günlük) · `KriptoPerpSeri` (03:30) ·
`KriptoDefter2` · `KriptoDefter3` (7,5 dk).

---

## 3. Altı defter — projenin en zeki tarafı

Her defter **tek bir değişkeni yalıtmak** için var. Bu, ölçüm tasarımı olarak
gerçekten iyi bir fikir ve bizde karşılığı yok:

| defter | cevapladığı soru |
|---|---|
| `testbot` | Bot ne yaptı? (ölçünün temeli) |
| `golge` | Reddettiği girişlere girseydi ne olurdu? |
| `benim` | Kararı kullanıcı verseydi? |
| `ayna` | Bot girsin, çıkışa kullanıcı karar versin |
| `defter2` | **Bot yanlış evrende mi avlanıyor?** |
| `defter3` | Aynı evren, **iki yön** — kayıp evrenden mi yön kısıtından mı? |

En güzeli `defter3 − defter2` kurgusu: iki defterin evreni, çıkışı, boyutlandırması
**birebir aynı**, tek fark yön. Fark ne çıkarsa **yönün etkisidir**. Üstelik
`chg24 < 0` alt kümesinde aynı coinler üzerinde biri LONG biri SHORT açıyor —
doğrudan yön kıyası.

⚠️ Ama `defter2` **yarım riskle** koşuyor ve bu kıyası bozuyor: `smart_giriste`
o evrende neredeyse hep LONG çıktığı için bot ters-yön kuralıyla riski yarıya
indiriyor (10 pozisyonun 10'unda). İki kasa **aynı risk seviyesinde değil**.
Kendileri bunu yazmış — ama düzeltmemişler.

---

## 4. Yöntem disiplini — asıl değerli olan burası

`CLAUDE.md` (446 satır) 45 günde pahalıya öğrenilmiş kuralların kütüğü. Bunların
çoğu bizim de uyduğumuz ilkeler, ama **birkaçı bizde yok ve almaya değer**:

- **Ön kayıt koşumdan önce yazılır VE commit edilir.** Commit hash'i hükmün
  yanında duruyor — yani "sonucu görüp ölçütü değiştirmedim"in kanıtı git.
- **Kontrol grubu zorunlu.** "Kural kârlı" yetmez; *aynı işlemler kuralsız*
  ne yapardı, o da ölçülür.
- **Ölçüm sırası: `ham ileri getiri → ticaret mekaniği → portföy simülasyonu`.**
  Aksi hâlde "bizim stopumuzun öldürdüğü kenarı 'sinyal boş' diye kaydederiz."
- **Karıştırıcı kontrolü zorunlu — monotonluk tek başına yetmez.** Dilimler
  kusursuz sıralı çıksa bile *"aynı fiyat hareketi içinde de ayırıyor mu"*
  sorulmadan hüküm yazılmaz. İki kez ısırmış.
- **Hücreler oynaklıkta ayrışıyorsa ham getiri ZORUNLU.** Somut sınama:
  karşılaştırılan hücrelerde *stop genişliği* ve *stop-olma oranı* eşit mi?
  Ölçmüşler: bantlar arasında stop genişliği **3,3 kat** değişiyor.
- **D/9 değişiklik protokolü:** eski ölçüt **silinmez**, yanına `[DEĞİŞTİ tarih]`
  eklenir. Şüphede **daima statüko**.
- **HER OLGUNUN TEK SAHİBİ VAR.** Bir olgu tek dosyada yazılır; diğerleri
  **işaret eder, kopyalamaz**. Gerekçe çarpıcı: indeks kurulduktan sonra bulunan
  **20 hatanın çoğu** bu sınıftanmış — aynı olgu iki dosyada, biri düzeltilmiş
  öbürü unutulmuş.
- **Hızlı değişen rakam dosyaya yazılmaz** — kaynağı ve **okuma komutunu** yaz,
  değeri yazma. Bir kez sabah yazılan rakamlar aynı gün öğlen yalan söylemiş.
- **Başarısızlık aynen raporlanır.** Çıkış tarafında **29 varyant** denenmiş,
  **1'i** geçmiş. Ve geçen tek varyant çıkışı *gevşetiyordu*; sıkılaştıran
  **28 varyantın 28'i de kalmış**.
- **Araçla kapatılan disiplin:** Windows konsolu cp1254 olduğu için emoji içeren
  `print()` çıktı yönlendirilince betiği öldürüyormuş — beş kez ısırmış, bir kez
  **uydurma p-değeri** ürettirmiş. Çözüm dikkat değil, her betiğin başına konan
  `stdout.reconfigure(encoding="utf-8")` bloğu.
- **`pyflakes`, `py_compile`'a EK olarak.** `py_compile` tanımsız ismi görmez;
  bu sınıf üç kez ısırmış (`radar.HERE`, `ayna.time`).

---

## 5. Ölçümlerin söylediği — ve bu, projenin kendi hükmü

Aşağıdakilerin hepsi **kendi kütüklerinden** alıntı. Benim yorumum değil.

### 5.1 Botun açan kapılarının ikisi de zararlı

Kapı karnesi, kontrol gruplu, çift mekanikli, **N=189.134**, 2 yıl (2026-08-20):

```
kosul                  MEKANIKLI fark  ay-t     HAM fark   ay-t    ISARET
funding <= -0,05          -0,0956     -3,15     -0,5430   -4,96    AYNI
MA50+ucuz                 -0,1084     -0,75     -0,1574   -0,11    AYNI
fiyat <= $0,07            -0,0880     -2,44     -0,2827   -2,14    AYNI
chg24 >= %20 (pump)       -0,5134     -2,14     -2,1799   -1,90    AYNI
chg24 >= %40 (blowoff)    -1,3889     -2,41     -4,4757   -1,88    AYNI
```

Kendi hükümleri: **"bot NE ALMAYACAĞINI biliyor, NE ALACAĞINI bilmiyor."**
Engelleyen kapılar (pump, blowoff) doğru çalışıyor; **açan kapıların ikisi de
anlamlı zararlı.**

### 5.2 Çekirdek kapı kenarı buluyor ama ödeyerek buluyor

```
kume                     N       BRUT    fonlama       NET
KAPI (fund<=-0,05)   18832    +0,2155   -0,1519   -0,1090
KONTROL (fund>-0,05) 49258    +0,1231   +0,0199   -0,0295
```

Kapı brüt kenarı gerçekten yükseltiyor — **sinyal var**. Ama o kenarı bulmak için
fonlama **ödüyor**, kontrol grubu ise fonlama **tahsil ediyor**. Net: kapı
0,08 puan zarar ettiriyor. Bu, projenin en merkezî varsayımına ait **ilk kontrol
gruplu ölçüm**. Orijinal kapı ölçümünde N=201 ve **kontrol grubu yoktu**.

### 5.3 Holdout: dört hükmün dördü de ayakta kalmadı

11–18 Ağustos, N=53.354, ön kayıtlı:

```
hukum                          2 yil      holdout    top-3 sembol CIKINCA
1 SHORT yigini                +0,2340    +0,1798        -0,2777  ISARET DONDU
2 funding kapisi ZARARLI    fark +0,54  fark -1,14      +0,0439  sifirlandi
3 pump engeli DOGRU            -2,18    +0,9106         -0,0252  sifirlandi
4 >40 LONG + trailing         +2,379    -1,6660         -2,9154
```

Üçü ters döndü; **dördü de yoğunlaşma kontrolünde çöktü**. SHORT yığınının artısı
138 sembolün **3'ünden** geliyormuş.

### 5.4 Rejim etiketi 8 gün geç ve rastgeleden kötü

BTC günlük, 741 gün. Gerçek "yükseliş günü" tanımı etiketten bağımsız
(sonraki 7 gün ≥ +%3). Taban oran **%30**.

```
kural                    kesinlik  kapsama  gecikme-medyan  kacirilan
MEVCUT (sezon VE hava)      8,4%     4,5%       8,0 gun       36/49
ONERI  (yalniz sezon)      22,5%    29,9%       0,0 gun       30/49
```

**Mevcut etiket BOĞA dediğinde o günün yükseliş günü olma ihtimali, rastgele bir
günden DÜŞÜK** (%8,4 vs %30). Ve 8 gün gecikme, 7 günlük bir hareket için
"hareket bittikten sonra açılmak" demek. Canlı doğrulama: bot BOĞA'yı 2 gün geç
gördü, o iki günde SHORT'taydı, BTC **+%7,6** yaptı.

### 5.5 En sert bulgu: `skor` ters tahmin ediyor

`skor` botun **tek pozitif seçicisi** ve LONG kapısı `skor ≥ 45`'e dayanıyor.
Hiç doğrudan ölçülmemiş. 2026-08-25'te ölçüldü (N=50.738, 441 sembol, 60 gün):

```
bant      N       ort +24s    pozitif
<2      5870      +0,126%      %47
5-10   11876      +0,249%      %49
20-30   5513      -0,001%      %45
>=45    1371      -2,015%      %35   <- BOTUN LONG KAPISI
```

- Monotonluk **ρ = −0,643** (6 saatlik ufukta −0,893) — beklenen `+0,75` yerine.
- Şans testi: **p = 1,0000** — gözlenen değer 2000 permütasyonun **hepsinden**
  daha negatif.
- Karıştırıcı kapısı **negatif işaretle ayakta kaldı** → skor sadece oynaklığın
  vekili değil, gerçekten ters.
- Zaman yarılarında, üç rejimde de **aynı işaret**.

Yani bot, **iyi bir SHORT seçicisini LONG kapısı olarak kullanıyor.**

### 5.6 Stop, sinyalin üçte ikisini yiyor

Stop 1,5 ATR uzakta = 72 saatlik ufkun doğal menzilinin **%17,7'si**. İşlemlerin
**%15,1'i kazanacakken** stopla ölüyor, bunların **%64'ü ilk 6 saatte**.
30 çıkış varyantı denenmiş, hepsi **hedef** ve **kısmi kâr** tarafında —
**stopun kendisi hiç sorgulanmamış.**

### 5.7 Ölçüm yönteminin kendisinde kusur bulundu

Kullanıcı sormuş: *"bu ölçümlerin doğruluğuna güvenmemi gerektirecek sebep ne?"*
Haklı çıkmış: aynı 117 işlem, ölçüm mekaniğiyle **−2.400 $**; botun gerçek sonucu
**−489 $**. Ölçümler botu değil **başka bir sistemi** tarif ediyormuş.

Ayrıca `funding_gecmis` içinde bir **birim kırılması** bulunmuş: fonlama bir
dönem **100 kat** büyük hesaplanmış ve bunu **ölçümün kendisi** yakalamış.

---

## 6. Yapısal sorun — projenin göremediği şey

Yukarıdakileri yan yana koyunca ortaya şu çıkıyor:

> **Ölçüm aleti botu geçti. Bot, ölçüm öncesi inançların fosili hâline geldi.**

- `MA50+ucuz`: ölçüm **reddetti** (t=−4,05, üç rejimde negatif) → **açık**
- `notr_long_acik`: *"ölçüm bunu desteklemiyor"* yazılı → **açık**
- `skor ≥ 45` LONG kapısı: artık **ters tahmin ettiği ölçüldü** → **açık**
- `funding ≤ −0,05` A+B kapısı: kontrol grubundan kötü → **açık**

Neden düzeltilmiyor? Çünkü **"hakem penceresi"** kuralı parametreleri donduruyor:
*"parametre değişmez, kapı eklenmez, eşik oynatılmaz"* — 138 pozisyon veya 30 gün
dolana kadar. Altı ayrı karar bu tek hakeme bağlanmış.

**Ama hakem artık hüküm veremez.** 19 Ağustos'ta `btc_pay_short_freni` **üç kez**
değişti (1→0→1→0), pencerenin **92. pozisyonunda**. Pencere şimdi **dört dilim**
taşıyor:

```
12 Agu 01:17 - 19 Agu 13:44   FRENLI    (92 pozisyon)
19 Agu 13:44 - 19 Agu 19:30   FRENSIZ
19 Agu 19:30 - 19 Agu 21:40   FRENLI
19 Agu 21:40 - pencere sonu   FRENSIZ
```

Ön kayıtlı ölçüt *"toplam net > 0 **ve** ikinci yarı > 0"* idi. "İkinci yarı"
artık **farklı bir botu** ölçüyor. Kendi belgeleri bunu *"uygulanabilirliği
tartışmalı"* diye kaydetmiş.

**Sonuç:** altı karar, hüküm veremeyecek bir hakemi bekliyor. Bu, projenin en
büyük yapısal riski ve kendi belgelerinde **neredeyse** yazıyor.

### Ve daha derindeki soru — kendi teşhisleri

> *"Ölçtüğümüz her şey tek banttan türüyor. Fiyat · hacim · işlem sayısı · taker
> oranı · OI · oynaklık · sıkışma: hepsi Binance perp'te gerçekleşmiş işlemden
> çıkıyor. O yüzden her yeni aday 'erken fiyat hareketinin başka bir ifadesi'
> çıkıyor."*

Bu teşhis doğru ve bizim için de geçerli. Önerdikleri çıkış yolu da doğru:
gerçekten yeni bilgi **bandın dışındadır** — emir defteri likiditesi, spot-perp
basis, çapraz borsa, pozisyon kompozisyonu. Bir tanesini (`top_ls − glob_ls`)
denemişler, bulgu çıkmamış.

---

## 7. Bulduğum kod kusurları — bağımsız, satır numaralı

Aşağıdakiler onların belgelerinde **yazmıyor**. Kodu okuyarak buldum.

### 7.1 🔴 TP1 kaydında teminat İKİ KEZ yarılanıyor

`testbot.py:845` teminatı yarıya indiriyor:

```python
pos["marjin"] = round(pos["marjin"] / 2.0, 2)
```

Ama hemen altındaki kayıt bloğu **bir daha** yarılıyor:

```python
845:  pos["marjin"] = round(pos["marjin"] / 2.0, 2)        # yari
859:  "marjin": round(pos["marjin"] / 2.0, 2),             # CEYREK
861:  "roi_pct": round(pnl_net / (pos["marjin"] / 2.0) * 100, 1)   # 2 KAT sisik
```

**Sonuç:** `TP1_KISMI` satırlarında `marjin` alanı giriş teminatının **çeyreği**,
`roi_pct` ise **iki kat şişik**.

**Ne bozulmuyor:** `sonuc_usdt` ve `equity` doğru — yani **kâr/zarar muhasebesi
sağlam**. Bozulan yalnız raporlama alanları.

**Ne bozuluyor:** bu alanları okuyan her çözümleme. Ve `TP1_KISMI` satırları
defterin **yaklaşık üçte biri** (kendi kayıtları: pozisyon başına 45–50 fazla
kayıt). `scratchpad/pnl_tepe_raporu.py:112` bu alanı okuyor.

**Kaynağı:** 2026-08-11'deki "Bulgu 4" onarımı `:845` satırını eklerken kayıttaki
`/2.0`'ı kaldırmayı unutmuş. Yani **bir hata düzeltilirken bir başkası doğmuş.**

### 7.2 🟡 Fonlama, pozisyon kapandıktan SONRAKİ döneme de işleniyor

`funding_events_since` (`testbot.py:229`) `startTime` alıyor, **`endTime` almıyor**:

```python
d = _get(f"{FAPI}/fapi/v1/fundingRate?symbol={sym}USDT&startTime={start_ms}&limit=50")
```

Ve `funding_uygula`, kapanıştan **bağımsız** çağrılıyor (`:1075` — başka bir hatayı
düzeltmek için bilerek böyle yapılmış). Pozisyon, oynatılan pencerenin başında
stop olduysa, **kapanış ile "şimdi" arasındaki fonlama olayları da ona yazılıyor.**

**Neden normalde görünmez:** pencere bir tur = 7,5 dakika; fonlama 8 saatte bir.
Çakışma olasılığı küçük.

**Neden yine de önemli:** kesinti sonrası döngü **500 dakikaya kadar (8+ saat)**
mum geri oynatıyor — ve 8 saat, tam olarak fonlama periyodu. Yani hata
**normal işleyişte uyuyor, kesintide uyanıyor**; onların 13–16 Ağustos'ta
**~10 saatlik** kesintileri olmuş.

**Onarım:** kapanış barının zaman damgasını üst sınır olarak geçirmek.

### 7.3 🟡 Likidasyon formülü kaldıraçla küçülen bir MMR varsayıyor

`testbot.py:258`:

```python
def likidasyon_fiyati(giris, yon, kaldirac):
    frac = 0.95 / kaldirac
```

Bu, sürdürme teminat oranının (MMR) **`0,05 / kaldıraç`** olduğunu varsayar —
yani kaldıraç arttıkça MMR *küçülür*. Borsada MMR **notional kademesine bağlı
sabit bir orandır** (BTC ~%0,4; alt coinlerde %1–2,5), kaldıraçla değişmez.

| kaldıraç | modelin varsaydığı MMR | tipik gerçek (alt) | yön |
|---|---|---|---|
| 3 | %1,67 | %1–2,5 | temkinli/doğru |
| 10 | **%0,5** | %1–2,5 | **iyimser** — gerçekte daha erken likit olur |

**Bugünkü pratik etkisi ~sıfır:** `kaldirac_guvenlik_kirp` stopun likidasyondan
%30 marjla önce tetiklenmesini garantiliyor ve bugüne kadar **hiç likidasyon
olmamış**. Ama `kaldirac_max` yükseltilirse ya da ince likiditeli alt'lara
girilirse model **tam da riskin arttığı yerde** iyimser.

**Ucuz onarım:** `/fapi/v1/leverageBracket` ucundan gerçek MMR okumak.

*(Bizim `pozisyon.py`'de bu açıkça `mmr_oran` parametresi olarak duruyor ve
`uyarilar()` tahmin olduğunu her pozisyonda isimle bildiriyor.)*

### 7.4 🟡 Zaman-stopu "o anki" fiyattan kapatıyor

`testbot.py:1085` civarı: 48 saat dolduğunda `fiyat_fapi()` ile **anlık** fiyattan
kapatıyor — stop/TP'de yapıldığı gibi *zamanı gelen mumdan* değil. Kesinti
sonrasında, saatler önce kapanması gereken bir pozisyon bugünün fiyatından
kapanıyor. Yönlü bir sapma değil ama **hakem defterine gürültü** ekliyor.

### 7.5 🟡 Kilit hâlâ "kontrol et sonra yap"

`_kilit_al` (`testbot.py:1624`) `os.path.exists()` → `open(...,"w")` deseni.
Kendi `CLAUDE.md`'leri bunu bir **hata sınıfı** olarak listeliyor ("üç kez oldu")
ve bu örnek için *"henüz ısırmadı"* diyor. İki satırlık onarımı da kendileri
yazmış (`os.O_CREAT | os.O_EXCL`) — uygulanmamış.

### 7.6 🟡 `golge.py` hâlâ atomik yazmıyor

2026-08-11'de defteri **314 $** saptıran kök neden. Onarım önerilmiş,
uygulanmamış. 2026-08-17'de **ağırlaşmış**: gölge pozisyonları artık yalnız
state'te yaşayan `funding_toplam`/`funding_yazilan` sayaçları taşıyor — yırtık bir
yazım artık toplamı tutmayan fonlama dilimleri üretebilir.

---

## 8. Güvenlik ve hijyen

### 8.1 🔴 En sert kural, hiçbir şey tarafından uygulanmıyor

`CLAUDE.md`'nin ilk maddesi: **"BOTA HABER VERMEDEN KARIŞILMAZ"** — kod, state,
açık pozisyonlar, zamanlanmış görevler; onay alınmadan değiştirilmez.

Ama `.claude/settings.json`'da:

```json
"allow": [ "Bash(python -c ' *)", ... ],
"additionalDirectories": [ "C:\\Users\\alper\\.claude" ]
```

- `python -c '...` **kayıtsız şartsız serbest** → keyfi Python çalıştırma.
  Bununla `testbot_state.json` yeniden yazılabilir, pozisyon kapatılabilir,
  `testbot.py` değiştirilebilir — **onay sorulmadan.**
- **`deny` listesi hiç yok.**
- Ajana `.claude` yapılandırma dizininin tamamı açılmış.

Yani projenin en sert kuralı **düzyazıyla** yazılmış, **kodla** korunmuyor.

*(Biz 25 Ağustos'ta tam bu boşluğu kapattık: `python -c`, `git commit/push`, `rm`,
`Stop-Process` artık `ask`; dondurulmuş dört dosya `deny` ile kilitli.)*

### 8.2 🟢 Sızıntı yok

`kripto-config.json` ve `kripto_portfoy.json` geçmişte **0 commit** — anahtarlar
temiz. `.git` 12 MB. Bu konudaki eski endişeleri kendileri ölçüp çürütmüşler.

### 8.3 🟡 Depo şişkinliği

910 takipli dosyanın **394'ü** `scratchpad/short_kayip/mum1h/` altında önbelleğe
alınmış 1 saatlik mum JSON'ları — yani **ölçüm girdisi** git'e commit edilmiş.
`.gitignore` diğer bütün mum önbelleklerini dışlıyor; bu bir gözden kaçma.
Ayrıca boş bir `panel_err.log` takipte.

### 8.4 ⚪ Kullanıcı adı sızıntısı

`YAPILACAKLAR.md` ve `.claude/settings.json` `C:\Users\alper\...` yolunu taşıyor.
Zararsız ama kamuya açık bir depoda makine kullanıcı adını açık ediyor.

---

## 9. Bizim sistemle karşılaştırma

### Ortak olan
Kâğıt üstü çalışma · ön kayıt disiplini · Türkçe belgeler · Windows Görev
Zamanlayıcı · anahtarsız Binance REST · **fonlama dersinin pahalıya öğrenilmesi**
(onlarda kenarın %83'ünü yemiş, bizde 5 dk döneminde brüt +11R'yi maliyet
tamamen yemişti) · "tek banttan türeyen sinyal" teşhisi.

### Onlarda güçlü, bizde eksik

| konu | onlar | biz |
|---|---|---|
| **Kontrol grubu** | Zorunlu kural; *aynı işlemler kuralsız* ölçülür | Yok — biz gürültü tabanıyla kıyaslıyoruz |
| **Defter çeşitliliği** | 6 defter, her biri tek değişken yalıtıyor | 2 (ana + radar) |
| **Tarihsel derinlik** | 566 sembol × 2 yıl 1s mum + fonlama | Kalıcı uçlar + **yeni kurulan** 30 günlük perp arşivi |
| **Şans ölçümü** | Gün-içi permütasyon (2000 tur), ay-kümeli t | Bootstrap GA, PSR |
| **Ham getiri aşaması** | Uygulanıyor (ve kuralı bir kez ihlal edip yakalamışlar) | Kural alındı, **henüz koşulmadı** (madde 7.2) |
| **Ön kayıt kanıtı** | Ayrı commit; hash hükmün yanında | Dosyada, commit ayrı değil |

### Bizde güçlü, onlarda eksik

| konu | biz | onlar |
|---|---|---|
| **Al-tut kıstası** | `panel.py`'nin en üst kutusu; ana −%9,6 vs BTC +%28,5 vs sepet +%45,3 | **Yok.** Tüm depoda tek bir "hiç işlem yapmasaydık" kıyası aramadım — bulamadım |
| **Teknik kilit** | `deny` ile dondurulmuş dosyalar | Düzyazı kural, uygulama yok |
| **Kısmi kapanış muhasebesi** | Değişmezden türetiliyor: `notional = miktar×giriş`, `teminat = notional/kaldıraç` → çifte yarılama **imkânsız** | Yerinde mutasyon → **7.1'deki hata** |
| **MMR açıklığı** | `mmr_oran` parametresi + her pozisyonda "bu bir tahmindir" uyarısı | Kaldıraca gömülü sabit `0,95` |
| **Bildirim süzgeci** | Susturulan mesaj `True` döner (döngü kilitlenmesin) | Yalnız olay bazlı açma/kapama |

### En önemli ortak eksik

**İkimiz de "kural A kural B'den iyi mi" ölçtük; "bunların hiçbiri BTC'yi tutmaktan
iyi mi" diye sormadık.** Biz bunu 23 Ağustos'ta fark edip `panel.py`'ye koyduk ve
cevap acıydı. Onlarda bu soru **hâlâ sorulmamış** — ve kendi rakamlarıyla
(117 işlem = −489 $, yani $10.000 kasada ~−%4,9) aynı dönemde BTC yükselirken.

---

## 10. Ne alacağız

Sırayla, ön kayıt kapandıktan sonra:

1. **🔴 SKOR YÖN TESTİ — en yüksek öncelikli.**
   Onların `skor_tahmin.py`'sinin bizdeki karşılığı. Bizim radar skorumuz da
   **hiç bu şekilde ölçülmedi**. Onlarda sonuç **ters** çıktı (ρ=−0,643,
   p=1,0000) ve skor bizde de aynı aileden bir bileşik. Ölçütler koşumdan önce
   yazılacak: monotonluk ρ ≥ +0,75 · işaret tutarlılığı ≥ %60 gün · karıştırıcı
   (ATR eşitliği) · gün-içi permütasyon p ≤ 0,05.
   → **Yapılacaklar 7.2'nin yanına, aynı önem sırasında.**

2. **🔴 Kontrol grubu zorunluluğu.**
   Şu an "kural vs gürültü tabanı" kıyaslıyoruz. Onlarınki *"aynı işlemler bu
   kural olmadan"* — bizde eksik olan karşı-olgu tam bu. Çekirdek kapı ölçümleri
   bunsuz yapılmışsa yeniden yapılmalı.

3. **🟡 "Her olgunun tek sahibi var" kuralı.**
   `TASARIM-BOT.md` / `SISTEM.md` / hafıza üçgeninde aynı olgu birden fazla yerde
   duruyor ve bu sınıftan **bir çelişkiyi zaten yaşadık** (liste ikiye bölünmüştü).
   Her olgu için tek sahip dosya belirlenip diğerleri **işaretçiye** çevrilecek.

4. **🟡 Oynaklık eşitliği sınaması.**
   Ham getiri kuralını aldık ama **uygulama mekanizmasını** almadık. Somut sınama:
   karşılaştırılan hücrelerde stop genişliği ve stop-olma oranı eşit mi? Eşit
   değilse ham getiri zorunlu.

5. **🟡 Gün-içi permütasyon testi.**
   Bootstrap GA "bu sayı ne kadar belirsiz" der; permütasyon "bu şans eseri
   olabilir mi" der. İkisi farklı soru. Ucuz, ekleyelim.

6. **🟢 Ön kaydı ayrı commit yapmak.**
   Zaten ön kayıt yazıyoruz; ayrı commit'lersek "sonucu görüp ölçütü değiştirmedim"
   iddiasının kanıtı git olur. Sıfır maliyet.

### Ne almayacağız

- **Altı defterin tamamını.** Bizim iki defterimiz var ve bir tanesi zaten koşan
  ön kayıt. Defter çoğaltmak, ölçülecek şey netleşmeden karmaşıklık bütçesini
  yakar (kural 8).
- **Hakem penceresine altı kararı birden bağlamayı.** Onlarda tam bu yapı kilide
  dönüştü. Bizde `radar-v2` tek soruyu sınıyor — öyle kalsın.
- **`skor ≥ 45` benzeri bileşik eşikleri** yeni kapı olarak eklemeyi. Onlarınki
  ölçülünce ters çıktı; bizimki ölçülmeden hiçbir yere eklenmeyecek.

---

## 11. Onlara söylenecek tek şey olsaydı

> Botunuzu değil, **hakeminizi** onarın.

Altı karar, dört dilime bölünmüş ve ön kayıtlı ölçütü artık uygulanamayan bir
pencereye bağlı. O pencere hüküm veremez. Yeni bir ön kayıt yazıp **temiz bir
pencere** açmak — ve bu kez ölçüte *"al-tut kıstasını geçmek"* koymak — altı
kararı da çözer. Aksi hâlde ölçüm aleti çalışmaya, bot da ölçümün çürüttüğü
kurallarla işlem açmaya devam edecek.

İkinci söylenecek şey: **`skor` ters çıktı ve bot onu LONG kapısı olarak
kullanmaya devam ediyor.** Bu, pencere kuralının koruduğu değil, **maliyeti
ölçülmüş** bir gecikme.

---

## 12. Doğrulama — bu raporu sınamak isteyen için

```bash
git clone https://github.com/irisphotofethiye-bocici/kripto-trade
cd kripto-trade && git log -1 --format='%h %ci'      # df96b83 / 2026-08-25 olmali

sed -n '843,862p' testbot.py        # 7.1: cifte yarilama
sed -n '229,235p' testbot.py        # 7.2: endTime yok
sed -n '258,261p' testbot.py        # 7.3: 0.95/kaldirac
sed -n '1624,1640p' testbot.py      # 7.5: kontrol-et-sonra-yap
cat .claude/settings.json           # 8.1: "python -c ' *" ve deny yoklugu
git ls-files | wc -l                # 910
git ls-files | grep -c mum1h        # 394
grep -rniE "al-tut|buy.and.hold" --include=*.md .   # 8.3: bos donmeli
```

Alıntı yaptığım hükümlerin tamamı `olcumler.md` içinde, tarih ve betik adıyla
kayıtlı. Bu projenin en saygıdeğer tarafı da bu: **kendi aleyhine olan her
bulguyu yazmış.**

---

*Bu rapor bizim sistemimize hiçbir değişiklik yapmadan hazırlandı. Dış proje
salt okundu, hiçbir betiği çalıştırılmadı. Koşan ön kayıt `radar-v2`
etkilenmedi.*
