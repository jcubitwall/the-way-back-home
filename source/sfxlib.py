import numpy as np,wave
SR=44100
rng=np.random.default_rng(7)
def T(d):return np.arange(int(SR*d))/SR
def band(x,lo,hi):
    F=np.fft.rfft(x);f=np.fft.rfftfreq(len(x),1/SR);F[(f<lo)|(f>hi)]=0;return np.fft.irfft(F,len(x))
def noise(d):return rng.standard_normal(int(SR*d))
def env_ar(n,a,r):
    t=np.arange(n)/SR;d=n/SR;return np.clip(t/max(a,1e-3),0,1)*np.clip((d-t)/max(r,1e-3),0,1)
def place(buf,sig,at,g=1.0):
    s=int(at*SR);e=min(len(buf),s+len(sig))
    if s<len(buf):buf[s:e]+=g*sig[:e-s]
def norm(x,peak=0.9):m=np.abs(x).max();return x/m*peak if m>0 else x
def save(x,path):
    x=np.clip(x,-1,1);w=wave.open(path,'wb');w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR);w.writeframes((x*32767).astype(np.int16).tobytes());w.close()
# --- elements ---
def rustle(d,lo=1800,hi=7000):
    x=band(noise(d),lo,hi);m=np.abs(band(noise(d),0.5,9));m=m/m.max();return x*(0.3+m)*env_ar(len(x),0.3,0.5)
def sparkle(d=1.2,n=7):
    out=np.zeros(int(SR*d))
    for k in range(n):
        f=rng.uniform(3000,6500);t=T(0.5);s=np.sin(2*np.pi*f*t)*np.exp(-t*12)
        place(out,s,rng.uniform(0,d-0.5),rng.uniform(.2,.5))
    return out
def thud(f=55,d=0.8):t=T(d);return np.sin(2*np.pi*f*t*(1+0.3*np.exp(-t*8)))*np.exp(-t*5)*(1-np.exp(-t*200))
def hum(d,f=118):
    t=T(d);x=sum(np.sin(2*np.pi*f*k*t)/k**1.3 for k in (1,2,3,4));x*=1+0.15*np.sin(2*np.pi*7*t);return x+0.2*band(noise(d),2000,6000)
def hiss(d):
    x=band(noise(d),3500,11000);t=T(d);return x*np.sin(np.pi*np.clip(t/d,0,1))**1.5
def slither(d):
    x=band(noise(d),900,4000);m=0.5+0.5*np.sin(2*np.pi*3.2*T(d)+rng.uniform(0,6));return x*m*env_ar(len(x),0.4,0.6)
def crunch():
    out=np.zeros(int(SR*0.35))
    for k in range(9):
        b=band(noise(0.05),800,6000)*np.exp(-T(0.05)*60);place(out,b,k*0.03+rng.uniform(0,0.01),rng.uniform(.5,1))
    return out
def thunder(d):
    x=band(np.cumsum(noise(d))/300,20,180);t=T(d)
    e=np.zeros_like(t)
    for c in (0.15,0.55,1.1):e+=np.exp(-((t-c)/0.25)**2)*rng.uniform(.6,1)
    e+=np.exp(-t/1.2)*0.5;return x*e*env_ar(len(x),0.05,0.8)
def wind(d,lo=150,hi=900):
    x=band(noise(d),lo,hi);m=band(noise(d),0.05,0.6);m=(m-m.min())/(m.max()-m.min());return x*(0.4+0.6*m)*env_ar(len(x),0.8,0.8)
def crackle(d,density=40):
    out=0.15*band(noise(d),100,600)
    for k in range(int(d*density)):
        c=band(noise(0.02),1500,8000)*np.exp(-T(0.02)*200);place(out,c,rng.uniform(0,d-0.02),rng.uniform(.1,.6))
    return out*env_ar(len(out),0.3,0.4)
def whoosh(d=1.0):
    x=band(noise(d),300,3000);t=T(d);return x*np.sin(np.pi*t/d)**2
def step(g=1.0,soft=True):
    d=0.12;x=band(noise(d),60,900 if soft else 2500)*np.exp(-T(d)*40);return g*x
def footsteps(d,rate=1.8,jitter=0.08,fade=None):
    out=np.zeros(int(SR*d));t=rng.uniform(0,0.2)
    while t<d-0.15:
        g=1.0 if fade is None else max(0,1-t/fade);place(out,step(),t,g*rng.uniform(.6,1));t+=1/rate+rng.uniform(-jitter,jitter)
    return out
def crowd_steps(d,people=14):
    out=np.zeros(int(SR*d))
    for p in range(people):out+=footsteps(d,rate=rng.uniform(1.3,1.9),jitter=0.12)*rng.uniform(.3,.8)
    return out
def murmur(d,voices=10):
    out=np.zeros(int(SR*d))
    for v in range(voices):
        f0=rng.uniform(300,900);x=band(noise(d),f0,f0*1.8);m=np.clip(band(noise(d),0.5,4),0,None);out+=x*m/ (m.max()+1e-9)
    return out*env_ar(len(out),1.0,0.8)
def scrub(d,rate=4.5):
    x=band(noise(d),900,5000);t=T(d);m=np.clip(np.sin(2*np.pi*rate*t),0,1)**0.6;return x*m
def drip():t=T(0.25);f=700+900*t/0.25;return np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*25)
def splash(d=0.6):x=band(noise(d),400,6000);return x*np.exp(-T(d)*7)*(1-np.exp(-T(d)*300))
def trickle(d):
    out=0.25*band(noise(d),1500,5000)*(0.6+0.4*np.sin(2*np.pi*0.7*T(d)))
    for k in range(int(d*3)):place(out,drip(),rng.uniform(0,d-0.3),rng.uniform(.2,.5))
    return out
def shimmer(d=1.5):
    t=T(d);x=sum(np.sin(2*np.pi*f*t+rng.uniform(0,6)) for f in (2637,3136,3951,4699));return x*np.sin(np.pi*t/d)**2*0.25*(1+0.4*np.sin(2*np.pi*9*t))
