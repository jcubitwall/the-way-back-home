import json,pathlib,os,sys,html
sys.path.insert(0,'i18n');import data
import img2pdf
from playwright.sync_api import sync_playwright
imgs=json.load(open('imgs.json'));F=pathlib.Path('fonts').resolve()
M=dict(garden="#2E7D4F",dusk="#6B3F8C",night="#2A2340",hope="#C8641E",sky="#2F7FD9")
MOODS=["garden"]*3+["dusk"]*2+["night"]*3+["hope"]*4+["sky"]*3
FOC={0:(0.28,0.70),1:(0.18,0.70),2:(0.18,0.62),3:(0.12,0.60),4:(0.15,0.72),5:(0.0,0.0),6:(0.505,0.505),7:(0.30,0.95),8:(0.05,0.62),9:(0.06,0.75),10:(0.08,0.80),11:(0.09,0.82),12:(0.14,0.85),13:(0.12,0.70),14:(0.05,0.78)}
FONT={ # body, display, line-height, display weight
 "latin":("Andika","Grand",1.36,900),"ru":("Andika","Andika",1.36,700),
 "zh":("NotoSC","NotoSC",1.62,900),"hi":("Deva","Deva",1.62,800),"bn":("Beng","Beng",1.62,800),
 "ar":("Naskh","Naskh",1.8,700),"ur":("Nast","Nast",2.15,700),"he":("Hebr","Hebr",1.55,800),"pa":("Guru","Guru",1.62,800),"ko":("Kore","Kore",1.6,800)}
def fam(k): return FONT.get(k,FONT["latin"])
faces=f"""@font-face{{font-family:Andika;src:url('file://{F}/Andika-Regular.ttf')}}@font-face{{font-family:Andika;font-weight:700;src:url('file://{F}/Andika-Bold.ttf')}}
@font-face{{font-family:Grand;font-weight:100 900;src:url('file://{F}/Grandstander.ttf')}}@font-face{{font-family:NotoSC;font-weight:100 900;src:url('file://{F}/NotoSansSC.ttf')}}
@font-face{{font-family:Deva;font-weight:100 900;src:url('file://{F}/NotoSansDevanagari.ttf')}}@font-face{{font-family:Beng;font-weight:100 900;src:url('file://{F}/NotoSansBengali.ttf')}}
@font-face{{font-family:Naskh;font-weight:400 700;src:url('file://{F}/NotoNaskhArabic.ttf')}}@font-face{{font-family:Kore;font-weight:100 900;src:url('file://{F}/NotoSansKR.ttf')}}@font-face{{font-family:Guru;font-weight:100 900;src:url('file://{F}/NotoSansGurmukhi.ttf')}}@font-face{{font-family:Hebr;font-weight:100 900;src:url('file://{F}/NotoSansHebrew.ttf')}}@font-face{{font-family:Nast;font-weight:400 700;src:url('file://{F}/NotoNastaliqUrdu.ttf')}}"""
def fr(s): # French typographic spaces
    for a,b in [(" ?","\u202f?"),(" !","\u202f!"),(" :","\u00a0:"),(" ;","\u202f;"),("« ","«\u00a0"),(" »","\u00a0»")]: s=s.replace(a,b)
    return s
def refs(lang,items):
    rtl=data.L[lang].get("rtl");sep=data.SEP.get(lang,"; ")
    cv=(lambda c:c.replace(', ','.').replace(':',',')) if lang in ('de','pdt') else (lambda c:c)
    return sep.join(f'{data.BOOKS[lang][b]} ' + (f'<span dir="ltr">{cv(c)}</span>' if rtl else cv(c)) for b,c in items)
FIT="""(()=>{for(const c of document.querySelectorAll('.card')){let s=1;c.style.setProperty('--s',s);while(c.scrollHeight>c.clientHeight+1&&s>.55){s-=.02;c.style.setProperty('--s',s)}}})()"""
def css(lang):
    body,disp,lh,dw=fam(lang);wb=("keep-all" if lang=="ko" else "normal")
    return faces+f"""
*{{box-sizing:border-box}}body{{margin:0;font-family:{body},Andika,sans-serif;color:#2B2233}}
.pg{{width:1080px;height:1920px;padding:44px;display:flex;flex-direction:column;gap:26px;overflow:hidden;position:relative}}
.art{{height:1290px;border-radius:46px;overflow:hidden;flex:none;box-shadow:0 12px 36px rgba(0,0,0,.3);position:relative}}
.art img{{width:100%;height:100%;object-fit:cover;display:block}}
.card{{--s:1;flex:1;min-height:0;background:#FFFDF8;border-radius:46px;padding:30px 50px;display:flex;flex-direction:column;justify-content:center;overflow:hidden}}
.num{{font-family:Grand;font-weight:900;font-size:30px;margin:0 0 4px}}
.t{{font-size:calc(var(--s)*37px);line-height:{lh};margin:0}}body{{word-break:{wb}}}.t+.t{{margin-top:calc(var(--s)*12px)}}
.ref{{font-size:calc(var(--s)*22px);color:#6B6275;margin:calc(var(--s)*12px) 0 0;line-height:1.5}}
.cover .art{{height:100%}}.shade{{position:absolute;inset:0;background:linear-gradient(180deg,transparent 42%,rgba(20,20,50,.88))}}
.ttl{{position:absolute;left:40px;right:40px;bottom:110px;text-align:center;color:#fff}}
.ttl h1{{font-family:{disp};font-weight:{dw};font-size:132px;line-height:1.08;margin:0;text-shadow:0 8px 0 rgba(0,0,0,.25)}}
.ttl p{{font-size:44px;margin:26px 0 30px}}
.hint{{display:inline-block;background:#FFD166;color:#2B2233;font-family:{disp};font-weight:700;font-size:34px;padding:16px 40px;border-radius:99px}}
.lang{{position:absolute;top:36px;left:36px;right:auto;background:rgba(255,255,255,.92);color:#2B2233;font-weight:700;font-size:28px;padding:10px 24px;border-radius:99px}}
[dir=rtl] .lang{{left:auto;right:36px}}
.plain .card{{padding:60px 64px}}
.plain h2{{font-family:{disp};font-weight:{dw};font-size:calc(var(--s)*72px);line-height:1.15;margin:0 0 calc(var(--s)*16px)}}
.small{{font-size:calc(var(--s)*32px);color:#6B6275;line-height:{lh}}}
.abc{{list-style:none;padding:0;margin:calc(var(--s)*18px) 0 calc(var(--s)*30px)}}
.abc li{{display:flex;gap:28px;font-size:calc(var(--s)*40px);line-height:{lh};margin:calc(var(--s)*26px) 0;align-items:flex-start}}
.abc b.m{{font-family:{'Grand' if lang in ('en',) else disp};font-weight:900;font-size:56px;width:96px;height:96px;flex:none;display:grid;place-items:center;border-radius:28px;color:#fff;line-height:1}}
.prayer{{font-size:calc(var(--s)*38px);line-height:{lh};background:#FFF1CC;border-radius:34px;padding:calc(var(--s)*32px) 40px;margin:0}}
.plain .ref{{font-size:calc(var(--s)*28px)}}
.qs{{font-size:calc(var(--s)*38px);line-height:{lh};padding-inline-start:1.3em;margin:0}}.qs li{{margin:calc(var(--s)*20px) 0}}
"""
def pages(lang):
    d=data.L[lang];t=(lambda s:fr(s)) if lang=="fr" else (lambda s:s)
    sp="" if lang=="zh" else " "
    out=[]
    c=M["sky"]
    out.append(f'<section class="pg cover" style="background:{c}"><div class="art"><img src="{imgs[13]}"><div class="shade"></div><span class="lang">{d["name"]}</span><div class="ttl"><h1>{d["title"]}</h1><p>{t(d["sub"])}</p><span class="hint">{t(d["hint"])}</span></div></div></section>')
    for i in range(15):
        c=M[MOODS[i]];a,z=FOC[i];v=min(1,(1290/992)/(1792/1008));cc=(a+z)/2;top=min(max(cc-v/2,0),1-v);pos=top/(1-v)*100
        ts=''.join(f'<p class="t">{t(x)}</p>' for x in d["pages"][i])
        out.append(f'<section class="pg" style="background:{c}"><div class="art"><img src="{imgs[i]}" style="object-position:50% {pos:.1f}%"></div><div class="card"><p class="num" style="color:{c}">{i+1}</p>{ts}<p class="ref">{refs(lang,data.REFS[i])}</p></div></section>')
    c=M["hope"]
    lis=''.join(f'<li><b class="m" style="background:{c}">{m}</b><span><strong>{t(w)}</strong>{sp}{t(r)}</span></li>' for m,(w,r) in zip(d["marks"],d["abc"]))
    out.append(f'<section class="pg plain" style="background:{c}"><div class="card"><h2 style="color:{c}">{t(d["abc_h"])}</h2><p class="small">{t(d["abc_s"])}</p><ul class="abc">{lis}</ul><p class="prayer">{t(d["prayer"])}</p><p class="ref">{t(d["note"])} {refs(lang,data.ABCREF)}</p></div></section>')
    c=M["garden"]
    qs=''.join(f'<li>{t(q)}</li>' for q in d["qs"])
    out.append(f'<section class="pg plain" style="background:{c}"><div class="card"><h2 style="color:{c}">{t(d["gu_h"])}</h2><p class="small">{t(d["gu_s"])}</p><ol class="qs">{qs}</ol><p class="ref">{t(d["gu_note"])}</p></div></section>')
    return out
os.makedirs('ml',exist_ok=True)
langs=sys.argv[1:] or data.ORDER
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page(viewport={'width':1080,'height':1920})
    for lang in langs:
        d=data.L[lang];dr='rtl' if d.get('rtl') else 'ltr'
        files=[]
        ONLY=[int(x) for x in os.environ.get('ONLY','').split(',') if x]
        for n,sec in enumerate(pages(lang)):
            if ONLY and (n+1) not in ONLY: continue
            open('tmp.html','w').write(f'<!doctype html><html lang="{lang}" dir="{dr}"><head><meta charset="utf-8"><style>{css(lang)}</style></head><body>{sec}</body></html>')
            pg.goto('file://'+str(pathlib.Path('tmp.html').resolve()));pg.evaluate('document.fonts.ready');pg.wait_for_timeout(200)
            bad=pg.evaluate("[...document.fonts].filter(f=>f.status==='error').map(f=>f.family)")
            if bad: print('FONT ERR',lang,bad)
            pg.evaluate(FIT)
            f=f'ml/{lang}-{n+1:02d}.jpg';pg.screenshot(path=f,type='jpeg',quality=85);files.append(f)
        if ONLY: print(lang,'pages',ONLY);continue
        lay=img2pdf.get_layout_fun((img2pdf.in_to_pt(6),img2pdf.in_to_pt(6*1920/1080)))
        name=f'/mnt/user-data/outputs/The-Way-Back-Home_{lang.upper()}.pdf'
        open(name,'wb').write(img2pdf.convert(files,layout_fun=lay,title='The Way Back Home'))
        print(lang,os.path.getsize(name)//1024,'KB')
    b.close()
