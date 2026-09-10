"""
portfoy.py — CANLI PORTFOY EKRANI (prototip)
================================================================================
Binance pozisyon ekrani duzeninde tek dosya HTML uretir: portfoy.html

  Sekme 1  ACIK      : izleniyor + beklemede kayitlar, fiyatlar CANLI yenilenir
  Sekme 2  KAPANMIS  : ilk islemden bugune kapanmis her islem, detayli

KULLANICI KARARLARI (2026-09-10):
  - kaldirac: GERCEK deger + "ya X kat olsaydi" dugmesi
  - sermaye : degistirilebilir, ilk kurulum $1000
  - kapanmis islemlerde HEM R HEM DOLAR (her islem AYRI hesap, bilesik DEGIL)
  - tek sayfa iki sekme
  - tarih araligi: EN BASTAN bugune (954 kayit sorun degil)

🔴 SALT OKUR. Hicbir deftere yazmaz, hicbir canli surece dokunmaz.
   Elle calistirilir; izleyici.py dongusune BAGLANMAZ.

Yeniden kullanilanlar (yeni matematik YAZILMADI):
  pozisyon.likidasyon_fiyati · pozisyon.MMR_VARSAYILAN · defter.maliyet_R
  defter.kaldirac_hesapla · olcucu.get_klines / RISK_PCT

ZORUNLU DISIPLIN (panel.py G4 + TASARIM-BOT §4):
  - al-tut kiyasi kar rakaminin USTUNDE durur
  - tetiklenmedi / geri-doldurma / deneysel kayitlar toplamlara KARISMAZ
  - gap/kayma modellenmedi, MMR tahmindir -> serh basilir

Calistirma: venv\\Scripts\\python.exe portfoy.py
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import olcucu
import defter
import pozisyon

KOK = Path(__file__).parent
CIKTI = KOK / "portfoy.html"

SICILLER = [("ANA", KOK / "kripto-defter.json"),
            ("RADAR", KOK / "radar-defter.json")]

KAPALI_SONUCLU = ("tp1", "tp2", "stop", "zaman_asimi")
ACIK_DURUMLAR = ("izleniyor", "beklemede")
DENEYSEL = set(getattr(olcucu, "DENEYSEL", set()))

BASLANGIC_BAKIYE = 1000.0
MMR = pozisyon.MMR_VARSAYILAN


# ============================== veri toplama ==============================
def _yukle():
    acik, kapali = [], []
    for ad, yol in SICILLER:
        try:
            T = json.loads(yol.read_text(encoding="utf-8"))["tahminler"]
        except Exception as e:
            print(f"  ! {yol.name} okunamadi: {type(e).__name__}: {e}")
            continue
        for t in T:
            g, s = t.get("giris"), t.get("stop")
            if not g or not s or g <= 0 or abs(g - s) <= 0:
                continue
            temel = {
                "sicil": ad, "no": t.get("no"), "token": t.get("token"),
                "yon": t.get("yon"), "giris": g, "stop": s,
                "tp1": t.get("tp1"), "tp2": t.get("tp2"),
                "risk_pct": t.get("risk_pct") or olcucu.RISK_PCT,
                "durum": t.get("durum"), "tarih": (t.get("tarih") or "")[:16],
                "skor": t.get("skor"), "setup": t.get("setup"),
                "rejim": t.get("rejim_durum"),
                # 🔴 sinif rozetleri — toplamlar bunlara gore suzulur
                "geri_doldurma": t.get("kaynak") == "geri-doldurma",
                "deneysel": t.get("token") in DENEYSEL,
                "ima_kald": defter.kaldirac_hesapla(g, s, t.get("risk_pct")),
                "stop_pct": round(abs(g - s) / g * 100, 3),
            }
            if t.get("durum") in ACIK_DURUMLAR:
                acik.append(temel)
            elif t.get("durum") in KAPALI_SONUCLU:
                brut = t.get("sonuc_R")
                if brut is None:
                    continue
                try:
                    mal = defter.maliyet_R(t)
                except Exception:
                    mal = None
                temel.update({
                    "cikis": t.get("sonuc_fiyat"),
                    "kapanis": (t.get("kapanis_tarih") or "")[:16],
                    "brut_R": brut,
                    "maliyet_R": round(mal, 4) if mal is not None else None,
                    "net_R": round(brut - mal, 4) if mal is not None else None,
                    "tetiklendi": True,
                })
                kapali.append(temel)
            elif t.get("durum") == "tetiklenmedi":
                temel.update({
                    "cikis": None, "kapanis": (t.get("kapanis_tarih") or "")[:16],
                    "brut_R": None, "maliyet_R": None, "net_R": None,
                    "tetiklendi": False,
                })
                kapali.append(temel)
    return acik, kapali


def _fiyatlar(tokenlar):
    """Uretim anindaki fiyatlar — sayfa cevrimdisi acilirsa bunlar gorunur."""
    out = {}
    for t in sorted(set(tokenlar)):
        try:
            out[t] = olcucu.get_klines(t, "1m", 1)[-1]["c"]
        except Exception:
            out[t] = None
    return out


def _al_tut(ilk_tarih):
    """G4: ayni pencerede BTC al-tut. Basarisizsa None (ekran 'alinamadi' basar)."""
    try:
        kl = olcucu.get_klines("BTCUSDT", "1d", 400)
        hedef = datetime.fromisoformat(ilk_tarih + "T00:00:00+00:00").timestamp() * 1000
        bas = next((k["c"] for k in kl if k["t"] >= hedef), None)
        son = kl[-1]["c"]
        if bas and son:
            return {"bas": bas, "son": son, "getiri_pct": (son / bas - 1) * 100}
    except Exception as e:
        print(f"  ! al-tut alinamadi: {type(e).__name__}")
    return None


# ============================== HTML ==============================
CSS = """
:root{--bg:#0e1116;--kart:#161b22;--cizgi:#252c37;--yazi:#c9d1d9;--soluk:#7d8590;
--yesil:#2ea043;--kirmizi:#e5534b;--sari:#d29922;--mavi:#388bfd;--gurultu:#6e7681}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--yazi);
font:13px/1.5 -apple-system,Segoe UI,Roboto,sans-serif}
.sar{max-width:1680px;margin:0 auto;padding:14px}
h1{font-size:16px;margin:0 0 2px}
.alt{color:var(--soluk);font-size:11px;margin-bottom:12px}
.kutu{background:var(--kart);border:1px solid var(--cizgi);border-radius:8px;
padding:12px 14px;margin-bottom:10px}
.kontrol{display:flex;gap:22px;flex-wrap:wrap;align-items:center}
.kontrol label{color:var(--soluk);font-size:11px;display:block;margin-bottom:3px}
input[type=number]{background:#0d1117;border:1px solid var(--cizgi);color:var(--yazi);
border-radius:5px;padding:5px 8px;width:110px;font:600 14px ui-monospace,monospace}
.kbtn{display:inline-flex;gap:4px}
.kbtn button{background:#0d1117;border:1px solid var(--cizgi);color:var(--soluk);
border-radius:5px;padding:5px 11px;cursor:pointer;font:600 12px ui-monospace,monospace}
.kbtn button.aktif{background:var(--mavi);border-color:var(--mavi);color:#fff}
.uyari{border-left:3px solid var(--kirmizi);background:#2a1618}
.dikkat{border-left:3px solid var(--sari);background:#2a2416}
.kiyas{border-left:3px solid var(--mavi);background:#111d2e}
.kutu h3{margin:0 0 6px;font-size:12px;letter-spacing:.4px;text-transform:uppercase;
color:var(--soluk)}
.buyuk{font:700 22px ui-monospace,monospace}
.satirlar{display:flex;gap:30px;flex-wrap:wrap}
.sekme{display:flex;gap:6px;margin:14px 0 10px}
.sekme button{background:var(--kart);border:1px solid var(--cizgi);color:var(--soluk);
padding:8px 16px;border-radius:6px 6px 0 0;cursor:pointer;font:600 13px inherit}
.sekme button.aktif{background:var(--mavi);border-color:var(--mavi);color:#fff}
table{width:100%;border-collapse:collapse;font:12px ui-monospace,monospace}
th{position:sticky;top:0;background:#1c2128;color:var(--soluk);text-align:right;
padding:7px 8px;border-bottom:1px solid var(--cizgi);font-weight:600;
font-size:10.5px;text-transform:uppercase;letter-spacing:.3px;white-space:nowrap}
th.sol,td.sol{text-align:left}
td{padding:6px 8px;border-bottom:1px solid #1b2027;text-align:right;white-space:nowrap}
tr:hover td{background:#1a2029}
tr.tehlike td{background:#2a1618}
.k{color:var(--yesil)}.z{color:var(--kirmizi)}.n{color:var(--gurultu)}
.rz{display:inline-block;padding:1px 6px;border-radius:9px;font-size:9.5px;
font-weight:700;letter-spacing:.3px}
.rz-ana{background:#1f3b57;color:#79c0ff}.rz-radar{background:#3b2f57;color:#d2a8ff}
.rz-gd{background:#4d3800;color:#e3b341}.rz-dn{background:#4a1f24;color:#ff8f8f}
.rz-tt{background:#30363d;color:#8b949e}
.rz-tp1,.rz-tp2{background:#12331d;color:#56d364}.rz-stop{background:#4a1f24;color:#ff8f8f}
.rz-zaman_asimi{background:#3d2f00;color:#d29922}
.rz-izleniyor{background:#0d3868;color:#79c0ff}.rz-beklemede{background:#30363d;color:#8b949e}
.suz{display:flex;gap:14px;flex-wrap:wrap;align-items:center;margin-bottom:8px;
font-size:11px;color:var(--soluk)}
.suz select,.suz input[type=text]{background:#0d1117;border:1px solid var(--cizgi);
color:var(--yazi);border-radius:5px;padding:4px 7px;font:12px inherit}
.suz label{display:flex;gap:5px;align-items:center;cursor:pointer}
.serh{color:var(--soluk);font-size:11px;line-height:1.7}
.serh b{color:var(--sari)}
.gizli{display:none}
.tablo-sar{max-height:70vh;overflow:auto;border:1px solid var(--cizgi);border-radius:8px}
.canli{display:inline-block;width:7px;height:7px;border-radius:50%;
background:var(--yesil);margin-right:5px}
.canli.kapali{background:var(--kirmizi)}
"""

JS = r"""
const MMR = __MMR__, BAS_BAKIYE = __BAKIYE__;
const ACIK = __ACIK__, KAPALI = __KAPALI__, FIYAT0 = __FIYAT0__;
let fiyat = Object.assign({}, FIYAT0);
let bakiye = BAS_BAKIYE, kald = 1.0, canli = false;

const f = (x,d=2)=> x==null||!isFinite(x) ? "—" : x.toLocaleString("tr-TR",
  {minimumFractionDigits:d, maximumFractionDigits:d});
const fp = x => x==null||!isFinite(x) ? "—" :
  (Math.abs(x)>=1000 ? x.toFixed(2) : Math.abs(x)>=1 ? x.toFixed(4) :
   Math.abs(x)>=0.01 ? x.toFixed(5) : x.toPrecision(4));
const sinif = x => x==null ? "" : x>0 ? "k" : x<0 ? "z" : "n";
const imza = (x,d=2)=> x==null||!isFinite(x) ? "—" : (x>0?"+":"") + f(x,d);

// --- tek islem icin dolar/teminat/likidasyon: pozisyon.py ile AYNI formul ---
function hesap(r){
  const risk_usd = bakiye * r.risk_pct/100;
  const birim = Math.abs(r.giris - r.stop);
  const miktar = risk_usd / birim;
  const notional = miktar * r.giris;
  const teminat = notional / kald;
  const mesafe = 1.0/kald - MMR;
  const liq = mesafe <= 0 ? r.giris
    : (r.yon === "LONG" ? r.giris*(1-mesafe) : r.giris*(1+mesafe));
  // stop mu likidasyon mu ONCE gelir (pozisyon.uyarilar mantigi)
  const tehlike = Math.abs(r.giris - liq) <= birim;
  return {risk_usd, miktar, notional, teminat, liq, tehlike,
          ima: notional/bakiye};
}

// --- GERCEKLESMIS: temiz kume (canli kayit + tetiklenmis + deneysel disi) ---
// Bu kume SABIT: KAPANMIS sekmesinin suzgecleri buna DOKUNMAZ.
const TEMIZ = KAPALI.filter(r => r.tetiklendi && !r.geri_doldurma
                                 && !r.deneysel && r.net_R != null);
const GERCEKLESMIS_R = TEMIZ.reduce((s,r)=> s + r.net_R, 0);
// risk_pct kayit basina degisebilir -> dolar toplami kayit kayit hesaplanir
const gerceklesmisUsd = () =>
  TEMIZ.reduce((s,r)=> s + r.net_R * bakiye * r.risk_pct/100, 0);

function hesapOzeti(pnlAcik, acikSay){
  const ger = gerceklesmisUsd();
  const cuzdan = bakiye + ger;
  const toplam = cuzdan + pnlAcik;
  const yaz = (id, deger, on="") => {
    const e = document.getElementById(id);
    e.textContent = on + imza(deger); e.className = "buyuk " + sinif(deger);
  };
  document.getElementById("h-bas").textContent = "$" + f(bakiye);
  yaz("h-ger", ger, "$");
  document.getElementById("h-gerR").textContent = imza(GERCEKLESMIS_R,2) + "R";
  const c = document.getElementById("h-cuzdan");
  c.textContent = "$" + f(cuzdan); c.className = "buyuk " + sinif(cuzdan - bakiye);
  document.getElementById("h-acikn").textContent = acikSay;
  yaz("t-pnl", pnlAcik, "$");
  document.getElementById("t-pnlpct").textContent =
    imza(pnlAcik / (bakiye*0.01), 2) + "R";
  const t = document.getElementById("h-toplam");
  t.textContent = "$" + f(toplam); t.className = "buyuk " + sinif(toplam - bakiye);
  document.getElementById("h-toplampct").textContent =
    "bastan beri " + imza((toplam-bakiye)/bakiye*100,2) + "%";
}

function acikCiz(){
  const izl = ACIK.filter(r=>r.durum==="izleniyor");
  const bek = ACIK.filter(r=>r.durum==="beklemede");
  let tNot=0, tTem=0, tPnl=0, tRisk=0, tehlikeSay=0;

  let g = "";
  for(const r of izl){
    const h = hesap(r), p = fiyat[r.token];
    const isaret = r.yon==="LONG" ? 1 : -1;
    const pnl = p==null ? null : isaret*(p-r.giris)*h.miktar;
    const pnlR = pnl==null ? null : pnl/h.risk_usd;
    tNot+=h.notional; tTem+=h.teminat; tRisk+=h.risk_usd;
    if(pnl!=null) tPnl+=pnl;
    if(h.tehlike) tehlikeSay++;
    g += `<tr class="${h.tehlike?"tehlike":""}">
      <td class="sol"><span class="rz rz-${r.sicil.toLowerCase()}">${r.sicil}</span></td>
      <td class="sol"><b>${r.token}</b></td>
      <td class="sol ${r.yon==="LONG"?"k":"z"}">${r.yon}</td>
      <td>${f(h.notional)}</td><td>${f(h.ima,2)}x</td><td>${f(h.teminat)}</td>
      <td>${fp(r.giris)}</td><td><b>${fp(p)}</b></td><td>${fp(r.stop)}</td>
      <td>${fp(r.tp1)}</td><td>${fp(r.tp2)}</td>
      <td class="${h.tehlike?"z":"n"}">${fp(h.liq)}</td>
      <td class="${sinif(pnl)}"><b>${pnl==null?"—":imza(pnl)}</b></td>
      <td class="${sinif(pnlR)}">${pnlR==null?"—":imza(pnlR,3)}</td></tr>`;
  }
  document.getElementById("acik-govde").innerHTML = g ||
    `<tr><td colspan="14" class="sol n">tetiklenmis acik pozisyon yok</td></tr>`;

  let b = "";
  for(const r of bek){
    const p = fiyat[r.token];
    const uz = p==null ? null : (p-r.giris)/r.giris*100;
    b += `<tr><td class="sol"><span class="rz rz-${r.sicil.toLowerCase()}">${r.sicil}</span></td>
      <td class="sol"><b>${r.token}</b></td>
      <td class="sol ${r.yon==="LONG"?"k":"z"}">${r.yon}</td>
      <td>${fp(r.giris)}</td><td><b>${fp(p)}</b></td><td>${fp(r.stop)}</td>
      <td class="n">${uz==null?"—":imza(uz)+"%"}</td>
      <td class="sol n">${r.tarih}</td></tr>`;
  }
  document.getElementById("bek-govde").innerHTML = b ||
    `<tr><td colspan="8" class="sol n">beklemede kayit yok</td></tr>`;

  // --- toplamlar ---
  document.getElementById("t-risk").textContent = "$"+f(tRisk);
  document.getElementById("t-not").textContent = "$"+f(tNot);
  document.getElementById("t-tem").textContent = "$"+f(tTem);
  hesapOzeti(tPnl, izl.length);

  // --- KAPASITE: pozisyonlar sermayeye siginiyor mu ---
  const oran = tTem/bakiye*100;
  const gerekli = tNot/bakiye;
  const ku = document.getElementById("kapasite");
  if(oran > 100){
    ku.className = "kutu uyari";
    ku.innerHTML = `<h3>Kapasite sorunu</h3>
      Bagli teminat <b>$${f(tTem)}</b> = sermayenin <b>%${f(oran,1)}</b>'i.
      Bu kaldiracta (<b>${f(kald,0)}x</b>) bu pozisyonlar <b>tasinamaz</b> —
      hepsini tutmak icin en az <b>${f(gerekli,2)}x</b> kaldirac gerekir.
      <div class="serh" style="margin-top:6px">Sebep: risk sabit (%1) ama pozisyon
      buyuklugu stop mesafesine BOLUNEREK cikiyor — stop daraldikca pozisyon buyur.
      panel.py bunu "sirali islem" varsayarak es geciyor ve dipnotunda oyle etiketliyor;
      bu ekran ilk kez esZamanli gercegi gosteriyor.</div>`;
  } else {
    ku.className = "kutu";
    ku.innerHTML = `<h3>Kapasite</h3>Bagli teminat sermayenin
      <b>%${f(oran,1)}</b>'i — <b>${f(kald,0)}x</b>'te sigiyor.`;
  }

  // --- YOGUNLASMA ---
  const sh = ACIK.filter(r=>r.yon==="SHORT").length, tp = ACIK.length;
  const yg = document.getElementById("yogunlasma");
  const bskn = Math.max(sh, tp-sh), yon = sh >= tp-sh ? "SHORT" : "LONG";
  if(tp && bskn/tp >= 0.7){
    yg.className = "kutu uyari";
    yg.innerHTML = `<h3>Yogunlasma uyarisi</h3>
      ${tp} acik kayittan <b>${bskn}'i ${yon}</b>. Bu ${bskn} ayri bahis <b>DEGIL</b>,
      tek korelasyonlu bahis: "kripto ${yon==="SHORT"?"duser":"cikar"}".
      Hepsi ayni anda kazanir, hepsi ayni anda kaybeder.`;
  } else {
    yg.className = "kutu";
    yg.innerHTML = `<h3>Yogunlasma</h3>${tp} acik kayit: ${sh} SHORT / ${tp-sh} LONG.`;
  }

  const tu = document.getElementById("tehlike-serh");
  tu.innerHTML = tehlikeSay
    ? `<span class="z"><b>${tehlikeSay} pozisyonda LIKIDASYON STOP'UN ICINDE</b> —
       bu kaldiracta stop KORUMAZ; kayip 1R degil teminatin tamami olur.</span>`
    : `<span class="n">Yapisal uyari yok: ${f(kald,0)}x'te likidasyon stop'un
       DISINDA, stop koruyor.</span>`;

  kaldTabloCiz(tNot);
}

function kaldTabloCiz(tNot){
  const stopMed = __STOP_MED__;
  let g = "";
  for(const k of [1,2,5,10,20,50]){
    const mesafe = (1/k - MMR)*100;
    const korur = mesafe > stopMed;
    g += `<tr class="${korur?"":"tehlike"}"><td>${k}x</td>
      <td>${f(tNot/k)}</td><td>${f(mesafe,1)}%</td>
      <td class="sol ${korur?"k":"z"}">${korur?"EVET":"HAYIR — stop islevsiz"}</td></tr>`;
  }
  document.getElementById("kald-govde").innerHTML = g;
}

// ================== KAPANMIS ==================
function kapaliCiz(){
  const fs = document.getElementById("f-sicil").value;
  const fd = document.getElementById("f-durum").value;
  const fq = document.getElementById("f-ara").value.trim().toUpperCase();
  const gd = document.getElementById("f-gd").checked;
  const dn = document.getElementById("f-dn").checked;
  const tt = document.getElementById("f-tt").checked;

  let liste = KAPALI.filter(r=>{
    if(fs!=="hepsi" && r.sicil!==fs) return false;
    if(fd!=="hepsi" && r.durum!==fd) return false;
    if(fq && !r.token.includes(fq)) return false;
    if(!gd && r.geri_doldurma) return false;
    if(!dn && r.deneysel) return false;
    if(!tt && !r.tetiklendi) return false;
    return true;
  });
  liste.sort((a,b)=> (b.kapanis||"").localeCompare(a.kapanis||""));

  let brut=0, mal=0, net=0, usd=0, kaz=0, kay=0, n=0;
  let g = "";
  for(const r of liste){
    const risk_usd = bakiye * r.risk_pct/100;
    const netUsd = r.net_R==null ? null : r.net_R*risk_usd;
    if(r.net_R!=null){
      brut+=r.brut_R; mal+=r.maliyet_R; net+=r.net_R; usd+=netUsd; n++;
      if(r.brut_R>0) kaz++; else if(r.brut_R<0) kay++;
    }
    const rozet = [];
    if(r.geri_doldurma) rozet.push('<span class="rz rz-gd">GERI-DOLDURMA</span>');
    if(r.deneysel) rozet.push('<span class="rz rz-dn">DENEYSEL</span>');
    if(!r.tetiklendi) rozet.push('<span class="rz rz-tt">ISLEM OLMADI</span>');
    g += `<tr>
      <td class="sol"><span class="rz rz-${r.sicil.toLowerCase()}">${r.sicil}</span></td>
      <td class="sol">${r.no??""}</td>
      <td class="sol"><b>${r.token}</b></td>
      <td class="sol ${r.yon==="LONG"?"k":"z"}">${r.yon}</td>
      <td class="sol"><span class="rz rz-${r.durum}">${r.durum}</span> ${rozet.join(" ")}</td>
      <td class="sol n">${r.tarih}</td><td class="sol n">${r.kapanis||"—"}</td>
      <td>${fp(r.giris)}</td><td>${fp(r.cikis)}</td><td>${fp(r.stop)}</td>
      <td>${fp(r.tp1)}</td>
      <td class="n">${f(r.stop_pct,2)}%</td>
      <td class="${sinif(r.brut_R)}">${r.brut_R==null?"—":imza(r.brut_R,3)}</td>
      <td class="n">${r.maliyet_R==null?"—":f(r.maliyet_R,4)}</td>
      <td class="${sinif(r.net_R)}"><b>${r.net_R==null?"—":imza(r.net_R,3)}</b></td>
      <td class="${sinif(netUsd)}">${netUsd==null?"—":imza(netUsd)}</td></tr>`;
  }
  document.getElementById("kapali-govde").innerHTML = g ||
    `<tr><td colspan="16" class="sol n">suzgece uyan kayit yok</td></tr>`;

  document.getElementById("k-sayi").textContent = n + " islem (" + liste.length + " satir)";
  const set = (id,v,d=2)=>{const e=document.getElementById(id);
    e.textContent=imza(v,d); e.className=sinif(v);};
  set("k-brut", brut, 2); set("k-net", net, 2); set("k-usd", usd, 2);
  document.getElementById("k-mal").textContent = f(mal,2);
  document.getElementById("k-oran").textContent = n ? f(kaz/n*100,1)+"%" : "—";
  document.getElementById("k-kk").textContent = kaz+" / "+kay;
  document.getElementById("k-basi").textContent = n ? imza(net/n,4) : "—";
}

// ================== canli fiyat ==================
async function fiyatCek(){
  try{
    const r = await fetch("https://fapi.binance.com/fapi/v1/ticker/price");
    if(!r.ok) throw new Error(r.status);
    const d = await r.json();
    const ihtiyac = new Set(ACIK.map(x=>x.token));
    for(const x of d) if(ihtiyac.has(x.symbol)) fiyat[x.symbol] = parseFloat(x.price);
    canli = true;
  }catch(e){ canli = false; }
  const g = document.getElementById("canli-durum");
  g.innerHTML = canli
    ? `<span class="canli"></span>canli — ${new Date().toLocaleTimeString("tr-TR")}`
    : `<span class="canli kapali"></span>cevrimdisi — uretim anindaki fiyatlar`;
  acikCiz();
}

// ================== baglama ==================
function sekmeSec(ad){
  for(const s of ["acik","kapali"]){
    document.getElementById("sekme-"+s).classList.toggle("aktif", s===ad);
    document.getElementById("bolum-"+s).classList.toggle("gizli", s!==ad);
  }
  if(ad==="kapali") kapaliCiz();
}
function kaldSec(k){
  kald = k;
  for(const b of document.querySelectorAll(".kbtn button"))
    b.classList.toggle("aktif", parseFloat(b.dataset.k)===k);
  acikCiz();
}
// ================== ayarlari HATIRLA ==================
// Sayfa kendini yenilediginde sermaye/kaldirac/sekme/kaydirma KAYBOLMASIN.
const AY = "portfoy.ayar";
function ayarKaydet(){
  try{
    localStorage.setItem(AY, JSON.stringify({
      bakiye, kald,
      sekme: document.getElementById("bolum-kapali").classList.contains("gizli")
             ? "acik" : "kapali",
      kaydir: window.scrollY,
      f_sicil: document.getElementById("f-sicil").value,
      f_durum: document.getElementById("f-durum").value,
      f_ara: document.getElementById("f-ara").value,
      f_gd: document.getElementById("f-gd").checked,
      f_dn: document.getElementById("f-dn").checked,
      f_tt: document.getElementById("f-tt").checked,
    }));
  }catch(e){}
}
function ayarGeriYukle(){
  let a = null;
  try{ a = JSON.parse(localStorage.getItem(AY) || "null"); }catch(e){}
  if(!a) return null;
  if(isFinite(a.bakiye) && a.bakiye > 0){
    bakiye = a.bakiye; document.getElementById("bakiye").value = a.bakiye;
  }
  if(isFinite(a.kald) && a.kald > 0) kald = a.kald;
  for(const b of document.querySelectorAll(".kbtn button"))
    b.classList.toggle("aktif", parseFloat(b.dataset.k) === kald);
  const g = (id,v)=>{ if(v!=null) document.getElementById(id).value = v; };
  g("f-sicil", a.f_sicil); g("f-durum", a.f_durum); g("f-ara", a.f_ara);
  const c = (id,v)=>{ if(v!=null) document.getElementById(id).checked = v; };
  c("f-gd", a.f_gd); c("f-dn", a.f_dn); c("f-tt", a.f_tt);
  return a;
}

// ================== baglamalar ==================
document.getElementById("bakiye").addEventListener("input", e=>{
  const v = parseFloat(e.target.value);
  if(isFinite(v) && v>0){ bakiye = v; acikCiz(); ayarKaydet();
    if(!document.getElementById("bolum-kapali").classList.contains("gizli")) kapaliCiz(); }
});
for(const id of ["f-sicil","f-durum","f-gd","f-dn","f-tt"])
  document.getElementById(id).addEventListener("change", ()=>{kapaliCiz(); ayarKaydet();});
document.getElementById("f-ara").addEventListener("input", ()=>{kapaliCiz(); ayarKaydet();});

// ================== veri yasi + OTOMATIK YENILEME ==================
// 🔴 Sayfa file:// ile acildigi icin defter dosyalarini OKUYAMAZ (tarayici
//    guvenlik kisiti). Bu yuzden "yeni sinyal geldi mi" diye bakamaz.
//    Cozum: portfoy.py'yi zamanlanmis gorev tazeler, sayfa da kendini yeniler.
const URETIM = new Date(__URETIM__);
function yasGoster(){
  const dk = (Date.now() - URETIM.getTime()) / 60000;
  const e = document.getElementById("veri-yasi");
  if(!e) return;
  e.textContent = dk < 1.5 ? "veri taze" : `veri ${Math.round(dk)} dk once uretildi`;
  e.className = dk > 8 ? "z" : dk > 4 ? "" : "n";
}
yasGoster();
setInterval(yasGoster, 20000);

const a0 = ayarGeriYukle();
acikCiz();
if(a0 && a0.sekme === "kapali") sekmeSec("kapali");
if(a0 && a0.kaydir) window.scrollTo(0, a0.kaydir);
fiyatCek();
setInterval(fiyatCek, 5000);

// Sayfayi 2 dakikada bir yenile -> zamanlanmis gorevin urettigi TAZE dosya gelir.
// Yazi yazarken/secim yaparken yenilemez; ayarlar localStorage'da korunur.
setInterval(()=>{
  const o = document.activeElement;
  if(o && (o.tagName === "INPUT" || o.tagName === "SELECT")) return;
  if(window.getSelection && String(window.getSelection())) return;
  ayarKaydet();
  location.reload();
}, 120000);

window.addEventListener("beforeunload", ayarKaydet);
"""


def _html(acik, kapali, fiyat0, kiyas, ilk_tarih, ozet):
    stop_med = ozet["stop_med"]
    js = (JS.replace("__MMR__", repr(MMR))
            .replace("__BAKIYE__", repr(BASLANGIC_BAKIYE))
            .replace("__ACIK__", json.dumps(acik, ensure_ascii=False))
            .replace("__KAPALI__", json.dumps(kapali, ensure_ascii=False))
            .replace("__FIYAT0__", json.dumps(fiyat0))
            .replace("__URETIM__", json.dumps(
                datetime.now(timezone.utc).isoformat(timespec="seconds")))
            .replace("__STOP_MED__", repr(stop_med)))

    if kiyas:
        kiyas_html = (
            f'BTC al-tut (ayni pencere, {ilk_tarih} -> bugun): '
            f'<b class="{"k" if kiyas["getiri_pct"]>0 else "z"}">'
            f'{kiyas["getiri_pct"]:+.1f}%</b>'
            f' &nbsp;·&nbsp; Sistem (tum donem, iki sicil, %1 risk, bilesik DEGIL): '
            f'<b class="z">{ozet["net_R_toplam"] * olcucu.RISK_PCT:+.1f}%</b>'
            f' ({ozet["net_R_toplam"]:+.2f}R)')
    else:
        kiyas_html = ('BTC al-tut verisi <b>alinamadi</b> (ag yok). '
                      f'Sistem (tum donem): <b class="z">{ozet["net_R_toplam"]:+.2f}R</b>')

    return f"""<title>Portfoy — canli</title>
<style>{CSS}</style>
<div class="sar">
<h1>PORTFOY <span style="font-weight:400;color:var(--soluk)">— {ozet['acik_n']} acik ·
{ozet['kapali_n']} kapanmis islem</span></h1>
<div class="alt">uretim: {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC ·
<span id="veri-yasi"></span> · <span id="canli-durum"></span> ·
sayfa 2 dk'da bir kendini yeniler · 🔴 GERCEK PARA YOK, EMIR GONDEREN KOD YOK</div>

<div class="kutu kiyas"><h3>Ayni donemde hicbir sey yapmasaydin (zorunlu kiyas · G4)</h3>
{kiyas_html}
<div class="serh" style="margin-top:6px">Bu kutu kar rakaminin <b>USTUNDE</b> durur.
Sebep yazili: 23 Agustos olcumunde sistem −%9,6 iken BTC +%28,5'ti ve bu daha once
hic gorunmuyordu.</div></div>

<div class="kutu"><div class="kontrol">
<div><label>Sermaye ($)</label><input type="number" id="bakiye" value="{BASLANGIC_BAKIYE:.0f}" min="1" step="100"></div>
<div><label>Kaldirac (borsada secilen)</label><div class="kbtn">
<button data-k="1" class="aktif" onclick="kaldSec(1)">gercek 1x</button>
<button data-k="2" onclick="kaldSec(2)">2x</button>
<button data-k="5" onclick="kaldSec(5)">5x</button>
<button data-k="10" onclick="kaldSec(10)">10x</button>
<button data-k="20" onclick="kaldSec(20)">20x</button>
<button data-k="50" onclick="kaldSec(50)">50x</button>
</div></div>
<div><label>Risk / islem</label><div class="buyuk" style="font-size:15px">%{olcucu.RISK_PCT:g}</div></div>
</div></div>

<div class="kutu"><h3>Hesap durumu</h3>
<div class="satirlar">
<div><label class="serh">Baslangic sermayesi</label>
  <div class="buyuk" style="font-size:16px" id="h-bas">—</div></div>
<div><label class="serh">GERCEKLESMIS · {ozet['temiz_n']} kapanmis islem</label>
  <div class="buyuk" style="font-size:16px" id="h-ger">—</div>
  <div class="serh" id="h-gerR"></div></div>
<div><label class="serh">= Cuzdan bakiyesi</label>
  <div class="buyuk" style="font-size:16px" id="h-cuzdan">—</div></div>
<div><label class="serh">GERCEKLESMEMIS · <span id="h-acikn">—</span> acik pozisyon</label>
  <div class="buyuk" style="font-size:16px" id="t-pnl">—</div>
  <div class="serh" id="t-pnlpct"></div></div>
<div><label class="serh">= TOPLAM</label>
  <div class="buyuk" id="h-toplam">—</div>
  <div class="serh" id="h-toplampct"></div></div>
</div>
<div class="serh" style="margin-top:8px">
⚠ <b>GERCEKLESMIS</b> yalniz <b>temiz kume</b>dir: canli kaydedilmis + tetiklenmis +
deneysel-disi ({ozet['temiz_n']} islem). Disarida kalanlar: {ozet['gd_n']} geri-doldurma,
{ozet['tt_n']} "islem olmadi". Bunlari KAPANMIS sekmesinde suzgecle acabilirsin —
<b>o sekmenin toplamlari degisir, buradaki rakam DEGISMEZ</b> (ust kutu hesabin sabit
fotografi olmali).<br>
⚠ <b>Bilesik DEGIL</b>: her islem <b>baslangic</b> sermayesinin
%{olcucu.RISK_PCT:g}'i ile ayri hesaplandi. Gercek hesapta kazanc/kayip sonraki
islemin buyuklugunu degistirirdi; o egri <code>panel.py</code>'de var ve orada
"sirali islem varsayar" diye etiketli — 15 pozisyon ayni anda acikken o varsayim
zaten yanlis, o yuzden burada ikinci kez basilmadi.</div></div>

<div class="kutu" id="yogunlasma"></div>
<div class="kutu" id="kapasite"></div>

<div class="sekme">
<button id="sekme-acik" class="aktif" onclick="sekmeSec('acik')">ACIK ({ozet['acik_n']})</button>
<button id="sekme-kapali" onclick="sekmeSec('kapali')">KAPANMIS ({ozet['kapali_n']})</button>
</div>

<div id="bolum-acik">
  <div class="serh" style="margin-bottom:8px">
  <b>ima</b> = pozisyon buyuklugu / sermaye (sistemin GERCEK deger; kaldirac degil).
  <b>teminat</b> ve <b>likidasyon</b> yukaridaki kaldirac dugmesine gore degisir —
  ama <b>PNL DEGISMEZ</b>. Kaldirac sonucu ancak likidasyona carparsa degistirir.</div>
  <div class="tablo-sar"><table><thead><tr>
  <th class="sol">sicil</th><th class="sol">coin</th><th class="sol">yon</th>
  <th>boyut $</th><th>ima</th><th>teminat $</th>
  <th>giris</th><th>ANLIK</th><th>stop</th><th>TP1</th><th>TP2</th><th>likidasyon</th>
  <th>PNL $</th><th>PNL R</th>
  </tr></thead><tbody id="acik-govde"></tbody></table></div>
  <div class="serh" id="tehlike-serh" style="margin-top:8px"></div>

  <div class="kutu" style="margin-top:12px"><div class="satirlar">
  <div><label class="serh">Riske atilan</label><div class="buyuk" style="font-size:15px" id="t-risk">—</div></div>
  <div><label class="serh">Toplam pozisyon</label><div class="buyuk" style="font-size:15px" id="t-not">—</div></div>
  <div><label class="serh">Bagli teminat</label><div class="buyuk" style="font-size:15px" id="t-tem">—</div></div>
  </div></div>

  <h3 style="color:var(--soluk);font-size:12px;margin:16px 0 6px">BEKLEMEDE —
  giris fiyatina deginmedi, risk BAGLANMADI, teminat AYRILMADI</h3>
  <div class="tablo-sar"><table><thead><tr>
  <th class="sol">sicil</th><th class="sol">coin</th><th class="sol">yon</th>
  <th>giris</th><th>ANLIK</th><th>stop</th><th>uzaklik</th><th class="sol">acilis</th>
  </tr></thead><tbody id="bek-govde"></tbody></table></div>

  <div class="kutu dikkat" style="margin-top:12px"><h3>Kaldirac ne degistirir</h3>
  <table style="max-width:640px"><thead><tr><th>kaldirac</th><th>bagli teminat $</th>
  <th>likidasyon mesafesi</th><th class="sol">stop koruyor mu</th></tr></thead>
  <tbody id="kald-govde"></tbody></table>
  <div class="serh" style="margin-top:6px">Kiyas tabani: radar stop medyani
  <b>%{stop_med:.1f}</b>. Likidasyon mesafesi bunun altina inince stop islevsiz kalir.
  Olculdu (<code>TASARIM-BOT</code>): sicilin +2,08R yazdigi gercek bir ACEUSDT islemi
  10x'te <b>likidasyonla −0,654R</b>'dir.</div></div>
</div>

<div id="bolum-kapali" class="gizli">
  <div class="suz">
  <span>sicil <select id="f-sicil"><option value="hepsi">hepsi</option>
  <option>ANA</option><option>RADAR</option></select></span>
  <span>sonuc <select id="f-durum"><option value="hepsi">hepsi</option>
  <option>tp1</option><option>tp2</option><option>stop</option>
  <option>zaman_asimi</option><option>tetiklenmedi</option></select></span>
  <span>coin ara <input type="text" id="f-ara" placeholder="BTC" size="8"></span>
  <label><input type="checkbox" id="f-gd"> geri-doldurma dahil</label>
  <label><input type="checkbox" id="f-dn"> deneysel dahil</label>
  <label><input type="checkbox" id="f-tt"> islem olmayanlar dahil</label>
  <span id="k-sayi" style="margin-left:auto"></span>
  </div>

  <div class="kutu"><div class="satirlar">
  <div><label class="serh">Brut R</label><div class="buyuk" style="font-size:15px" id="k-brut">—</div></div>
  <div><label class="serh">Maliyet R</label><div class="buyuk" style="font-size:15px" id="k-mal">—</div></div>
  <div><label class="serh">NET R</label><div class="buyuk" id="k-net">—</div></div>
  <div><label class="serh">Net $ (her islem AYRI, bilesik DEGIL)</label>
  <div class="buyuk" style="font-size:15px" id="k-usd">—</div></div>
  <div><label class="serh">Islem basi net R</label><div class="buyuk" style="font-size:15px" id="k-basi">—</div></div>
  <div><label class="serh">Kazanma orani</label><div class="buyuk" style="font-size:15px" id="k-oran">—</div></div>
  <div><label class="serh">Kazanan / kaybeden</label><div class="buyuk" style="font-size:15px" id="k-kk">—</div></div>
  </div></div>

  <div class="tablo-sar"><table><thead><tr>
  <th class="sol">sicil</th><th class="sol">#</th><th class="sol">coin</th>
  <th class="sol">yon</th><th class="sol">sonuc</th>
  <th class="sol">acilis</th><th class="sol">kapanis</th>
  <th>giris</th><th>cikis</th><th>stop</th><th>TP1</th><th>stop %</th>
  <th>brut R</th><th>maliyet R</th><th>NET R</th><th>net $</th>
  </tr></thead><tbody id="kapali-govde"></tbody></table></div>
</div>

<div class="kutu" style="margin-top:14px"><h3>Serhler — bu ekran neyi gizlemiyor</h3>
<div class="serh">
🔴 <b>Bu sinyallere gore islem YAPILMAZ.</b> Cekirdek secici olculmus bicimde
bilgisiz/ters (18 aday oldu). Ekran performans iddiasi degil, <b>durum gostergesidir</b>.<br>
· <b>Gerçek para yok</b>, emir gonderen kod yok, gerceklesmis pozisyon yok.
Gosterilen her dolar rakami <b>varsayimsal</b>.<br>
· <b>Gap/kayma modellenmedi</b> (madde E1): stop tam seviyeden doldu varsayiliyor;
calkantida gercek dolum daha kotu olur.<br>
· <b>MMR (surdurme teminat orani) tahmindir</b> — %{MMR*100:g} varsayildi, muhafazakar
(likidasyonu girise YAKLASTIRIR). Kesin deger imzali Binance ucu ister.<br>
· <b>Funding dahil DEGIL</b> — kapanmis islemlerin maliyeti komisyon+kayma;
funding odemeleri yalniz <code>pozisyon.py</code> simulatorunde modelli.<br>
· <b>Net $ bilesik DEGIL</b>: her islem baslangic sermayesinin %1'i ile ayri
hesaplandi. Bilesik bakiye <code>panel.py</code>'de var ve orada "sirali islem
varsayar" diye etiketli — burada ikinci kez basilmadi.<br>
· <b>Geri-doldurma</b> ({ozet['gd_n']} kayit) bilgisayar kapaliyken olusan bosluktan
sonradan kuruldu; ileri-kayit DEGIL ve olculmus bicimde farkli davraniyor
(<code>KARAR-gerdoldurma-ornekleme-2026-09-10.md</code>). Varsayilan olarak <b>disaridadir</b>.<br>
· <b>Islem olmayanlar</b> ({ozet['tt_n']} kayit, "tetiklenmedi"): fiyat giris
seviyesine hic degmedi, kar/zarari yok. Varsayilan olarak <b>disaridadir</b>.
</div></div>
</div>
<script>{js}</script>
"""


KIYAS_ONBELLEK = KOK / "portfoy-kiyas.json"


def _kiyas_onbellekli(ilk, hizli):
    """--hizli: agdan CEKME, onbellekten oku (al-tut yavas degisir).
    Tam kosum: yeniden hesapla ve onbellegi tazele."""
    if hizli and KIYAS_ONBELLEK.exists():
        try:
            return json.loads(KIYAS_ONBELLEK.read_text(encoding="utf-8"))
        except Exception:
            pass
    if hizli:
        return None
    k = _al_tut(ilk)
    if k:
        try:
            olcucu.atomik_yaz(KIYAS_ONBELLEK, k)
        except Exception:
            pass
    return k


def main():
    import sys
    hizli = "--hizli" in sys.argv
    print(f"portfoy.py — canli portfoy ekrani{' (HIZLI: ag yok)' if hizli else ''}")
    acik, kapali = _yukle()
    print(f"  acik: {len(acik)}  ·  kapanmis kayit: {len(kapali)}")

    # 🔴 --hizli'da fiyat CEKILMEZ: sayfa Binance'ten kendisi canli cekiyor,
    #    gomulu fiyatlar yalnizca cevrimdisi yedegi. Zamanlanmis gorev bu modda
    #    kosar -> API yuku SIFIR, uretim ~anlik.
    fiyat0 = {} if hizli else _fiyatlar([r["token"] for r in acik])
    if not hizli:
        alinan = sum(1 for v in fiyat0.values() if v)
        print(f"  uretim ani fiyati alinan sembol: {alinan}/{len(fiyat0)}")

    tetik = [r for r in kapali if r["tetiklendi"]]
    temiz = [r for r in tetik if not r["geri_doldurma"] and not r["deneysel"]]
    net_top = sum(r["net_R"] for r in temiz if r["net_R"] is not None)
    radar_stop = sorted(r["stop_pct"] for r in kapali if r["sicil"] == "RADAR")
    stop_med = radar_stop[len(radar_stop) // 2] if radar_stop else 7.7

    ozet = {
        "acik_n": len(acik), "kapali_n": len(tetik), "temiz_n": len(temiz),
        "gd_n": sum(1 for r in kapali if r["geri_doldurma"]),
        "tt_n": sum(1 for r in kapali if not r["tetiklendi"]),
        "net_R_toplam": net_top, "stop_med": stop_med,
    }
    print(f"  temiz kume net: {net_top:+.2f}R  ·  radar stop medyani %{stop_med:.2f}")

    ilk = min((r["tarih"][:10] for r in kapali + acik if r["tarih"]), default="2026-06-28")
    kiyas = _kiyas_onbellekli(ilk, hizli)
    if kiyas:
        print(f"  BTC al-tut ({ilk} -> bugun): {kiyas['getiri_pct']:+.1f}%"
              f"{' [onbellek]' if hizli else ''}")

    CIKTI.write_text(_html(acik, kapali, fiyat0, kiyas, ilk, ozet), encoding="utf-8")
    kb = CIKTI.stat().st_size / 1024
    print(f"\n  -> {CIKTI.name} yazildi ({kb:.0f} KB)")
    print(f"     tarayicida ac: {CIKTI}")


if __name__ == "__main__":
    main()
