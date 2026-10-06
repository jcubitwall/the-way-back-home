import numpy as np
from sfxlib import SR,save,band,rng
BPM=72;BEAT=60/BPM;BAR=4*BEAT;BARS=16;L=BAR*BARS
def mid(n):return 440*2**((n-69)/12)
def piano(f,d,v):
    t=np.arange(int(SR*d))/SR;x=np.zeros_like(t)
    for k in range(1,7):x+=np.sin(2*np.pi*f*k*(1+0.0004*k*k)*t)/k**1.6*np.exp(-t*(1.2+0.7*k))
    return v*x*(1-np.exp(-t*250))
def bell(f,d,v):
    t=np.arange(int(SR*d))/SR;return v*(np.sin(2*np.pi*f*t)*np.exp(-t*1.6)+0.3*np.sin(2*np.pi*f*2.76*t)*np.exp(-t*4))*(1-np.exp(-t*400))
def pad(notes,d,v,dark=False):
    t=np.arange(int(SR*d))/SR;x=np.zeros_like(t)
    for n in notes:
        f=mid(n)
        for det in (-0.003,0,0.003):
            x+=np.sin(2*np.pi*f*(1+det)*t+rng.uniform(0,6));x+=(0.15 if dark else 0.3)*np.sin(2*np.pi*2*f*(1+det)*t)
    e=np.clip(t/1.4,0,1)*np.clip((d-t)/1.4,0,1);return v*x*e/len(notes)/3
def bass(f,d,v):
    t=np.arange(int(SR*d))/SR;return v*(np.sin(2*np.pi*f*t)+0.2*np.sin(2*np.pi*2*f*t))*np.exp(-t*0.9)*(1-np.exp(-t*80))
CH={'C':[48,52,55,60,64],'Am':[45,52,57,60,64],'F':[41,53,57,60,65],'G':[43,50,55,59,62],'E':[40,52,56,59,64],'Dm':[38,50,53,57,62],
    'Bb':[46,53,58,62,65],'Em':[40,52,55,59,64],'C/E':[40,52,55,60,64]}
MOODS={
 'garden':dict(prog=['C','Am','F','G'],arp='eighth',pv=.30,padv=.22,bells=True,bv=.12,oct=12,bassv=.25),
 'fall':  dict(prog=['Am','F','C','E'],arp='half',pv=.28,padv=.26,bells=False,oct=0,bassv=.22,dark=True),
 'wall':  dict(prog=['Am','Dm','Am','E'],arp='whole',pv=.22,padv=.30,bells=False,oct=-12,bassv=.30,dark=True),
 'hope':  dict(prog=['F','C/E','Dm','C'],arp='quarter',pv=.30,padv=.24,bells=True,bv=.10,oct=12,bassv=.24),
 'joy':   dict(prog=['C','G','Am','F'],arp='eighth',pv=.32,padv=.22,bells=True,bv=.16,oct=24,bassv=.28),
 'tender':dict(prog=['F','Am','Bb','C'],arp='quarter',pv=.26,padv=.24,bells=True,bv=.08,oct=12,bassv=.20),
}
def render(m):
    cfg=MOODS[m];N=int(SR*L);OFF=2.0;buf=np.zeros(N*3+SR*10)
    def put(sig,t):
        s=int((t+OFF)*SR);e=min(len(buf),s+len(sig));buf[s:e]+=sig[:e-s]
    for cyc in range(3):
        for b in range(BARS):
            t0=cyc*L+b*BAR;ch=CH[cfg['prog'][b%4]];top=[n+cfg['oct'] for n in ch[1:]]
            put(pad(ch[1:],BAR+1.4,cfg['padv'],cfg.get('dark',False)),t0-0.7)
            put(bass(mid(ch[0]),BAR*1.2,cfg['bassv']),t0)
            a=cfg['arp'];seq=top+[top[1],top[2]] if a!='whole' else top
            step={'eighth':BEAT/2,'quarter':BEAT,'half':BEAT*2,'whole':BAR}[a]
            n=int(BAR/step)
            for k in range(n):
                note=seq[(k+(b//4))%len(seq)]
                v=cfg['pv']*(0.85+0.3*rng.random())*(1.0 if k%2==0 else 0.75)
                if a=='half' and k%2==1:note=top[0]
                put(piano(mid(note),min(4.5,step*3),v),t0+k*step+rng.uniform(0,0.012))
            if cfg['bells'] and b%4==3:
                for j,nn in enumerate(sorted(top)[-2:]):put(bell(mid(nn+12),3.0,cfg['bv']),t0+BEAT*2+j*BEAT*0.5)
    o=int(OFF*SR);x=buf[o+N:o+2*N].copy();x=band(x,40,9000)
    return x/np.abs(x).max()*0.85
for m in MOODS:
    x=render(m);save(x,f'audio2/m_{m}.wav');print(m,round(len(x)/SR,2))
