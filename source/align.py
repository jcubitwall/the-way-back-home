import subprocess,re,sys,json,itertools
sys.path.insert(0,'i18n');import data
SPLIT=r'(?<=[.!?。！？।۔؟])\s*'
def sils(f,n,d=0.15):
    o=subprocess.run(['ffmpeg','-hide_banner','-i',f,'-af',f'silencedetect=n={n}dB:d={d}','-f','null','-'],capture_output=True,text=True).stderr
    s=None;out=[]
    for l in o.splitlines():
        m=re.search(r'silence_start: ([\d.]+)',l)
        if m:s=float(m.group(1))
        m=re.search(r'silence_end: ([\d.]+)',l)
        if m and s is not None:out.append((s,float(m.group(1))));s=None
    return out
def dur(f): return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',f]))
RUBY=re.compile(r'\[([^\]|]+)\|[^\]]+\]')
def sentences(l,page):
    out=[]
    for para in data.L[l]['pages'][page]:
        out+= [x for x in re.split(SPLIT,RUBY.sub(r'\1',para)) if x.strip()]
    return out
def boundary_time(l,page,after_sentence,verbose=False):
    """time (s) in site/audio/l/NN.mp3 right after sentence index after_sentence (1-based count) of story page `page` (0-based)"""
    f=f'site/audio/{l}/{page+2:02d}.mp3';D=dur(f)
    sents=sentences(l,page);k=len(sents)
    allS=sils(f,-42)
    lead=allS[0][1] if allS and allS[0][0]<0.05 else 0.0
    tail=allS[-1][0] if allS and allS[-1][1]>D-0.05 else D
    S=[]
    for d in (0.15,0.1,0.06):
        for n in (-42,-38,-35,-32,-28):
            S=[x for x in sils(f,n,d) if lead+0.5<x[0]<tail-0.5]
            if len(S)>=k-1:break
        if len(S)>=k-1:break
    L=[len(s) for s in sents];T=sum(L)
    best=None
    for combo in itertools.combinations(range(len(S)),k-1):
        cuts=[lead]+[(S[i][0]+S[i][1])/2 for i in combo]+[tail]
        segs=[cuts[j+1]-cuts[j] for j in range(k)]
        rate=(tail-lead)/T
        cost=sum((segs[j]-rate*L[j])**2 for j in range(k))-0.5*sum(S[i][1]-S[i][0] for i in combo)
        if best is None or cost<best[0]:best=(cost,combo,segs)
    i=best[1][after_sentence-1]
    if verbose: print(l,'sents',k,'segs',[round(x,1) for x in best[2]],'cut',round(S[i][0],2))
    return round(S[i][0]+0.1,2)
if __name__=='__main__':
    order=[l for l in json.load(open('site/assets/book.json'))['order'] if l!='pdt']
    res={l:boundary_time(l,0,3,True) for l in order}
    json.dump(res,open('s01_at.json','w'));print(res)
