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
- `backtest.py` / `ileritest.py` / `ileritest2.py` — doğrulama araçları (bkz. §9).

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
  trend filtresi hafif+tutarlı (+0.02-0.03R), K2 adayı.

---

## 10. KARAR KAPILARI (disiplinin kalbi)

- **K1 (config onayı) — TAMAM.** Walk-forward config seçimi; canlı parametre değiştirilmedi.
- **K2 (edge testi) — BEKLİYOR.** 30+ kapanmış swing işlem dolunca monotonluk + rejim-kümelenme
  + aday filtreler tek oturumda değerlendirilir. **O güne kadar PARAMETRE DEĞİŞİKLİĞİ YASAK.**
- **K3 (gerçek para) — ÇOK İLERİDE.** Şartlar: 30+ işlem net pozitif + iki farklı rejim +
  icra gerçekçiliği (gap/kayma ölçümü). Öncesinde gerçek para YOK.

---

## 11. ANLIK DURUM (2026-07-23 — eskir)

- **Ana sicil K2 sayacı: 11/30** girilmiş-kapanmış swing (tempo ~5/hafta → ~3-4 hafta kaldı).
- Ana sicil toplam: 41 kapalı, %34 isabet, brüt +3.23R / **net −12.28R**.
- Radar sicili: 26 kapalı, %25 isabet, net −7.37R.
- Deneysel (LAB): 1 kapalı, net +0.86R.
- Rejim: SAKIN (korelasyon 0.84, trend boğa). Makro kapı: ACIK.
- **Hüküm:** kanıtlanmış edge YOK; her iki sicil negatif; disiplin = veri biriktir, K2'yi bekle.

---

## 12. K2 / K3 GÜNDEMİ (sırası gelince, veriyle)

**K2 günü değerlendirilecek (canlı değişiklik değil, sorular):**
- OYNAK-kapı kuralı (kayıplar oynak rejimde mi kümeleniyor)
- Korelasyon histerezisi (0.83-0.85 bandında bayrak fır dönmesi)
- Skor tabanı 70→75 | L/S bileşenini at/kalibre et | mutlak funding tabanı
- Trend filtresi (ileritest2 OOS kanıtı) | funding+trend kombosu (ön-kayıtlı test)
- **Fear & Greed endeksi** (ileritest2'ye aday filtre olarak ekle, redundant mı bak — skill dersi)
- Likidasyon verisinin skora katkısı

**K3 günü (gerçek para öncesi zorunlu):**
- Gap/kayma nicelleştirme (sicilimizin çalkantıda iyimserliği)
- Bileşik aşınma / volatilite aşındırması (pozisyon boyutlamada varyans drenajı)
- Açık pozisyon ara-uyarıları ("stop'a yaklaştın / kâr al" — skill dersi)

**Ertelenmiş:** B2 (makro girdi: 10Y/ETH-BTC denemesi, tetik: K2 veya basis).

---

## 13. GÜVENLİK DEĞİŞMEZLERİ (asla ihlal edilmez)

- Hiçbir ajan işlem/para çekme yapmaz; emir her zaman kullanıcıda.
- API anahtarları + kişisel sicil gitignore'lu, GitHub'a gitmez.
- Bot salt-gönderim (Telegram), borsa/para yetkisi yok.
- Gerçek para: kanıtlanana kadar (K3) HAYIR.
- Otomatik/recurring her şey KOD olmalı (Claude kendi kendine çalışmaz).
