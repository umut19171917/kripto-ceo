"""
olcum.py — ORTAK ÇIKARIM KATMANI (2026-09-01)
================================================================================
NEDEN VAR: madde 8.7 — *"kuralı düzyazıyla değil KODLA koru."*

Bu proje aynı yöntem borçlarını her ölçümde yeniden yazıyordu ve bazıları
unutuluyordu. Bu modül onları **varsayılan** hâline getirir: doğru olanı
yapmak, yanlış olanı yapmaktan kolay olsun.

--------------------------------------------------------------------------------
KAPATTIĞI BORÇLAR
--------------------------------------------------------------------------------
8.2  KONTROL GRUBU  -> `bant_raporu(..., kontrol=...)`; kontrol verilmezse
                       hüküm satırı "kontrol kolu YOK" şerhiyle basılır.
8.4  PERMÜTASYON    -> `gun_ici_permutasyon()`. 🔴 `bant_raporu` permütasyon
                       p'si HESAPLANMADAN hüküm satırı YAZMAZ. Bootstrap
                       "ne kadar belirsiz", permütasyon "şans mı" der.
7.8  ALT-KÜME       -> kural kolu kontrolün alt kümesiyse eşleşmiş fark yoktur;
                       `bant_raporu` bunu tespit edip hükmü "iki-örneklemli
                       DEĞİL" diye işaretler.
6.3  DEĞİŞİKLİK     -> `ESIKLER` sözlüğü tek kaynak; değişirse `[DEĞİŞTİ tarih]`
                       satırı eklenir, eski değer SİLİNMEZ (aşağıya bak).

--------------------------------------------------------------------------------
🔴 SAHİPLİK HARİTASI (madde 8.3) — YENİ ARAÇ YAZMADAN ÖNCE BURAYA BAK
--------------------------------------------------------------------------------
Denetlendi 2026-09-01: canlı modüllerde HİÇBİR hesabın iki sahibi yok.
Yeni bir ölçüm aracı bunları YENİDEN YAZMAZ, buradan çağırır:

    bileşik bakiye / düşüş / getiri eğrisi ...... `panel._bilesik`
    R listesi (sicilden) ......................... `panel._R_listesi`
    al-tut kıyası ................................ `panel.kiyas`
    PSR ve dağılım ölçütleri ..................... `metrikler.psr`
    ATR ve fiyat matematiği ...................... `olcucu.atr`
    işlem maliyeti (R cinsinden) ................. `defter.maliyet_R`
    USD muhasebesi + likidasyon .................. `pozisyon.muhasebe`
    mutabakat denklemi ........................... `pozisyon.mutabakat`
    bantlama · bootstrap · permütasyon · hüküm ... **bu modül**

⚠ `onkayit_*.py` araçları bu kuralın DIŞINDADIR: her biri bir hükme bağlı
donmuş bir enstantanedir ve sonradan düzenlenmez. İçlerindeki kopya kodu
"düzeltmek" hükmü geçersiz kılar.

--------------------------------------------------------------------------------
🔴 EŞİKLER — TEK KAYNAK (madde 8.3: her olgunun TEK sahibi)
--------------------------------------------------------------------------------
Bu sayılar ön kayıtlarda tekrar tekrar yazılıyordu; artık buradan okunur.
Değiştirilirse ESKİSİ SİLİNMEZ, altına `[DEĞİŞTİ tarih]` satırı eklenir.
"""
import math
import random
import statistics as st
from collections import defaultdict

# Ölçülmüş maliyet: TAKER 0,05 × BNB 0,90 + SLIPPAGE 0,02, iki bacak = %0,13
MALIYET_GIDIS_DONUS = 0.13
MALIYET_UZUN_KISA = 0.26          # uç bantlarda iki gidiş-dönüş
EKONOMIK_ESIK = 0.50              # maliyet + benzer büyüklükte pay
RHO_ESIK = 0.80                   # monotonluk
TUR_BOOTSTRAP = 3000
TUR_PERMUTASYON = 5000
TOHUM = 11                        # proje teamülü


# ==========================================================================
# 1. BANTLAMA
# ==========================================================================
def bantla(G, alan, bant=5):
    """Bantlar SEMBOL İÇİNDE eşit sayılı bölünür, sonra havuzlanır.

    Neden sembol içinde: değişkenin sd'si sembole göre değişir; ham havuzlama
    bantları sembole göre ayırır (B1/basis/topls ile aynı desen)."""
    per = defaultdict(list)
    for g in G:
        per[g["sym"]].append(g)
    for lst in per.values():
        lst.sort(key=lambda g: g[alan])
        n = len(lst)
        for i, g in enumerate(lst):
            g["bant"] = min(bant - 1, i * bant // n)
    return G


def bant_ortalamalari(G, bant=5):
    b = defaultdict(list)
    for g in G:
        b[g["bant"]].append(g["ileri"])
    return ([st.fmean(b[k]) if b[k] else float("nan") for k in range(bant)],
            [st.median(b[k]) if b[k] else float("nan") for k in range(bant)],
            [_kirp(b[k]) for k in range(bant)])


def _kirp(v, pay=0.01):
    """%1-%99 kırpılmış ortalama — uç değer denetiminin ASIL ölçütü.

    🔴 MEDYAN HER TASARIMDA GEÇERLİ DEĞİL (ölçüldü 2026-09-01, `giris`):
    Eşleştirilmiş bir farkta bir kol sık sık **tam 0** katıyorsa (ör. tetiklenmeyen
    sinyal = işlem yok = 0R), farkın medyanı o **sıfır kütlesine** oturur ve
    ortalamayla taban tabana zıt görünür. Ölçülen örnek: `B−A` ortalaması
    **−0,022R** iken medyanı **−1,025R** — çünkü A, sinyallerin %67'sinde 0R.
    Böyle tasarımlarda **medyan bir sağlamlık ölçütü değildir**; kırpılmış
    ortalama (o örnekte −0,041R) doğru olanıdır ve ortalamayla uyumludur."""
    if not v:
        return float("nan")
    if len(v) < 20:
        return st.fmean(v)
    s = sorted(v)
    a = int(len(s) * pay)
    return st.fmean(s[a:len(s) - a])


def spearman(x, y):
    def sira(v):
        s = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(s):
            j = i
            while j + 1 < len(s) and v[s[j + 1]] == v[s[i]]:
                j += 1
            o = (i + j) / 2.0 + 1
            for k in range(i, j + 1):
                r[s[k]] = o
            i = j + 1
        return r
    rx, ry = sira(x), sira(y)
    mx, my = st.fmean(rx), st.fmean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return num / den if den > 0 else 0.0


# ==========================================================================
# 2. İKİ ÇIKARIM — BİRLİKTE ZORUNLU
# ==========================================================================
def gun_kumeli_bootstrap(G, bant=5, tur=TUR_BOOTSTRAP):
    """*"Bu tahmin ne kadar belirsiz?"* Takvim günü yeniden örneklenir.

    ⚠ SINIR (2026-09-01 denetimi): blok sayısı azsa (~30 gün) belirsizliği
    OLDUĞUNDAN AZ gösterebilir. Bu yüzden tek başına yeterli sayılmaz."""
    ozet = defaultdict(lambda: [[0.0, 0] for _ in range(bant)])
    for g in G:
        h = ozet[g["gun"]][g["bant"]]
        h[0] += g["ileri"]
        h[1] += 1
    bl = list(ozet.values())
    n = len(bl)
    if n < 10:
        return None, n
    rnd = random.Random(TOHUM)
    fark = []
    for _ in range(tur):
        t0 = a0 = t4 = a4 = 0.0
        for _ in range(n):
            b = bl[rnd.randrange(n)]
            t0 += b[0][0]; a0 += b[0][1]
            t4 += b[bant - 1][0]; a4 += b[bant - 1][1]
        if a0 and a4:
            fark.append(t4 / a4 - t0 / a0)
    if len(fark) < 100:
        return None, n
    fark.sort()
    return (fark[int(0.025 * len(fark))], fark[int(0.975 * len(fark))]), n


def gun_ici_permutasyon(G, bant=5, tur=TUR_PERMUTASYON):
    """*"Bu kadar büyük bir fark ŞANS ESERİ çıkar mıydı?"* (madde 8.4)

    Sıfır hipotezi: bant etiketi ile ileri getiri arasında bağ YOK.
    Etiketler her takvim günü İÇİNDE karıştırılır -> gün yapısı ve piyasa
    geneli hareket KORUNUR, yalnız BAĞ kırılır.

    🔴 SINIR — 2026-09-01 denetiminde ÖLÇÜLDÜ, varsayım değil:

    | durum | hangi yöntem güvenilir |
    |---|---|
    | ufuk ≈ örnekleme aralığı (örtüşme yok) | ikisi de; uyuşmaları gerçek kontrol |
    | **ufuk >> örnekleme aralığı** | **bootstrap**; permütasyon FAZLA DAR |
    | **öngörücü çok yavaş (τ >> 1 gün)** | **bootstrap**; permütasyon FAZLA DAR |

    Ölçülen örnek: `basis` (ufuk 24s, örnekleme 1s -> ardışık 24 gözlem
    neredeyse aynı ileri pencereyi paylaşıyor) permütasyon bootstrap'tan
    **7 kat dar** çıktı (0,13x). `topls` (ufuk 1s = örnekleme) **0,86x** —
    yani orada iki yöntem uyuştu. Bu yüzden permütasyon evrensel bir
    yükseltme DEĞİLDİR; ikisi BİRLİKTE okunur, çelişirse muhafazakâr olan alınır.

    Döner: (p, gozlenen_fark, sifir_dagiliminin_sd'si)
    """
    gunler = defaultdict(list)
    for g in G:
        gunler[g["gun"]].append(g)
    if len(gunler) < 5:
        return None, None, None

    def fark_hesapla(etiketler):
        t = [0.0] * bant
        a = [0] * bant
        i = 0
        for lst in gunler.values():
            for g in lst:
                b = etiketler[i]
                t[b] += g["ileri"]
                a[b] += 1
                i += 1
        if not a[0] or not a[bant - 1]:
            return None
        return t[bant - 1] / a[bant - 1] - t[0] / a[0]

    duz = [g["bant"] for lst in gunler.values() for g in lst]
    gozlenen = fark_hesapla(duz)
    if gozlenen is None:
        return None, None, None

    sinirlar, i = [], 0
    for lst in gunler.values():
        sinirlar.append((i, i + len(lst)))
        i += len(lst)

    rnd = random.Random(TOHUM)
    sifir = []
    calisma = list(duz)
    for _ in range(tur):
        for a, b in sinirlar:                 # 🔴 GÜN İÇİNDE karıştır
            dilim = calisma[a:b]
            rnd.shuffle(dilim)
            calisma[a:b] = dilim
        f = fark_hesapla(calisma)
        if f is not None:
            sifir.append(f)
    if len(sifir) < 100:
        return None, gozlenen, None
    asan = sum(1 for f in sifir if abs(f) >= abs(gozlenen))
    return (asan + 1) / (len(sifir) + 1), gozlenen, st.pstdev(sifir)


# ==========================================================================
# 3. RAPOR — hüküm satırı ŞARTLARI SAĞLANMADAN BASILMAZ
# ==========================================================================
def bant_raporu(G, alan, ad, bant=5, guclu=True, kontrol=None,
                alt_kume=False, esik=None):
    """Bantlar + iki çıkarım + uç değer denetimi + hüküm.

    🔴 Hüküm satırı, permütasyon p'si hesaplanmadan YAZILMAZ (madde 8.4).
    🔴 `kontrol` verilmezse hüküm "kontrol kolu YOK" şerhiyle basılır (8.2).
    🔴 `alt_kume=True` ise hüküm "iki-örneklemli DEĞİL" işaretlenir (7.8).
    """
    esik = EKONOMIK_ESIK if esik is None else esik
    bantla(G, alan, bant)
    ort, med, kir = bant_ortalamalari(G, bant)
    rho = spearman(list(range(bant)), ort)
    fark = ort[bant - 1] - ort[0]
    f_med = med[bant - 1] - med[0]
    f_kir = kir[bant - 1] - kir[0]
    ga, blok = gun_kumeli_bootstrap(G, bant)
    p, gozlenen, sifir_sd = gun_ici_permutasyon(G, bant)

    print(f"\n  {ad}   (n={len(G):,})")
    print("  " + "-" * 72)
    print("    ortalama : " + "  ".join(f"{v:+7.3f}%" for v in ort))
    print("    MEDYAN   : " + "  ".join(f"{v:+7.3f}%" for v in med))
    print("    KIRPILMIS: " + "  ".join(f"{v:+7.3f}%" for v in kir))
    print(f"    rho={rho:+.3f}   uc fark: ort {fark:+.3f}%  "
          f"medyan {f_med:+.3f}%  kirp {f_kir:+.3f}%")
    gs = f"[{ga[0]:+.3f}%, {ga[1]:+.3f}%]" if ga else "hesaplanamadi"
    print(f"    [1] gun-kumeli bootstrap GA95 : {gs}   ({blok} blok)")
    ps = f"p = {p:.4f}" if p is not None else "hesaplanamadi"
    ss = f"   (sifir dagilimi sd {sifir_sd:.3f}%)" if sifir_sd else ""
    print(f"    [2] gun-ici permutasyon       : {ps}{ss}")

    if kontrol is not None:
        print(f"    [3] KONTROL KOLU              : {kontrol}")
    else:
        print("    [3] KONTROL KOLU              : ⚠ YOK (madde 8.2 karsilanmadi)")

    # ---- hüküm ----
    if p is None:
        print("    🔴 HUKUM BASILMADI — permutasyon hesaplanamadi (madde 8.4).")
        print("       Iki cikarim birlikte olmadan hukum yazilmaz.")
        return _sonuc(ort, med, kir, rho, fark, ga, p)
    if not guclu:
        print("    HUKUM: ⚠ OLCULEMEDI — bu kol yeterince guclu DEGIL")
        return _sonuc(ort, med, kir, rho, fark, ga, p)

    ga_sifir_disi = bool(ga) and (ga[0] > 0 or ga[1] < 0)
    perm_anlamli = p < 0.05
    ayni_yon = (fark > 0) == (f_med > 0) and (fark > 0) == (f_kir > 0)

    if ga_sifir_disi != perm_anlamli:
        print(f"    🔴 YONTEMLER CELISIYOR: bootstrap "
              f"{'sifiri disliyor' if ga_sifir_disi else 'sifiri kapsiyor'}, "
              f"permutasyon p={p:.4f}")
        print("       Hukum EN MUHAFAZAKAR okumaya gore yazilir.")
    karar_var = ga_sifir_disi and perm_anlamli

    if not karar_var:
        h = "❌ BILGI YOK (iki cikarimin ikisi birden gerekli)"
    elif not ayni_yon:
        h = "❌ UC DEGER ESERI — ortalama ile medyan/kirpilmis ayni yonde degil"
    elif abs(fark) >= esik and abs(rho) >= RHO_ESIK:
        h = f"✅ BILGI VAR — |fark|>=%{esik:.2f} · |rho|>={RHO_ESIK} · uc deger denetimi gecti"
    elif abs(fark) >= MALIYET_UZUN_KISA:
        h = f"⚠ istatistiksel VAR, ekonomik YOK (%{MALIYET_UZUN_KISA}-%{esik:.2f} bandi)"
    else:
        h = f"⚠ istatistiksel VAR ama fark maliyetin (%{MALIYET_UZUN_KISA}) ALTINDA"
    if alt_kume:
        h += "  ⚠ ALT-KUME: iki-orneklemli DEGIL (madde 7.8)"
    if kontrol is None:
        h += "  ⚠ kontrol kolu YOK"
    print(f"    HUKUM: {h}")
    return _sonuc(ort, med, kir, rho, fark, ga, p)


def _sonuc(ort, med, kir, rho, fark, ga, p):
    return {"ort": ort, "medyan": med, "kirpilmis": kir, "rho": rho,
            "fark": fark, "ga": ga, "p": p}
