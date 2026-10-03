import subprocess,sys,os,json,glob
from PIL import Image,ImageDraw
SITE='/home/claude/book/site'
SCN={1:[('s01','clipframes/s01_')],2:[('s02','clipframes/s02_')],3:[('s03','clipframes/s03_')],4:[('s04','clipframes/s04_')],5:[('s05','clipframes/s05_')],6:[('s06','clipframes/s06_')],7:[('s07','clipframes/s07_')],8:[('s08','clipframes/s08_')],10:[('s10','clipframes/s10_')],11:[('s11','clipframes/s11_')]}
VS={'s01':json.load(open('/home/claude/book/s01_vs.json')),'s02':json.load(open('/home/claude/book/s02_vs.json')),'s03':json.load(open('/home/claude/book/s03_vs.json')),'s04':json.load(open('/home/claude/book/s04_vs.json')),'s05':json.load(open('/home/claude/book/s05_vs.json')),'s06':json.load(open('/home/claude/book/s06_vs.json')),'s07':json.load(open('/home/claude/book/s07_vs.json')),'s08':json.load(open('/home/claude/book/s08_vs.json')),'s10':json.load(open('/home/claude/book/s10_vs.json')),'s11':json.load(open('/home/claude/book/s11_vs.json'))}  # page index -> scenes (sfx name, frame prefix)
mask=Image.new('L',(992,1290),0);ImageDraw.Draw(mask).rounded_rectangle((0,0,991,1289),46,fill=255)
def dur(f): return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',f]))
MOODS=['c1','c1','c1','c2','c3','c3','c4','c4','c5','c6','c6','c6','c7','c7','c7','c7','c8','c8']
_MW={}
def mood_wave(m):
    import numpy as np,wave
    if m not in _MW:
        w=wave.open(f'/home/claude/book/cues/{m}.wav');_MW[m]=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)/32768;w.close()
    return _MW[m]
def music_track(pd,out):
    import numpy as np,wave
    SR=44100;total=sum(pd)+1;N=int(total*SR);mix=np.zeros(N,np.float32);XF=3.0
    starts=[0];[starts.append(starts[-1]+d) for d in pd]
    segs=[];m0=MOODS[0];s0=0.0
    for i in range(1,18):
        if MOODS[i]!=m0:segs.append((m0,s0,starts[i]));m0=MOODS[i];s0=starts[i]
    segs.append((m0,s0,total))
    for k,(m,a,b) in enumerate(segs):
        lo=max(0,a-XF/2) if k>0 else 0;hi=min(total,b+XF/2) if k<len(segs)-1 else total
        n=int((hi-lo)*SR);w=mood_wave(m);x=np.tile(w,n//len(w)+2)[:n]
        g=np.ones(n,np.float32);f=int(XF*SR)
        if k>0:g[:f]*=np.sin(np.linspace(0,np.pi/2,f))**2
        if k<len(segs)-1:g[-f:]*=np.cos(np.linspace(0,np.pi/2,f))**2
        s=int(lo*SR);mix[s:s+n]+=x*g
    fi=int(2*SR);mix[:fi]*=np.linspace(0,1,fi);fo=int(4*SR);mix[-fo:]*=np.linspace(1,0,fo)
    o=wave.open(out,'wb');o.setnchannels(1);o.setsampwidth(2);o.setframerate(SR);o.writeframes((np.clip(mix,-1,1)*32767).astype(np.int16).tobytes());o.close()
def build(l):
    U=l.upper();tmp=f'/tmp/v_{l}';os.makedirs(tmp,exist_ok=True)
    vl=open(f'{tmp}/v.txt','w');al=open(f'{tmp}/a.txt','w');pd=[]
    for i in range(18):
        n=f'{i+1:02d}';pg=f'{SITE}/pages/{l}/{n}.jpg';last=pg
        mix=f'{SITE}/audio/{l}/{n}-mix.mp3'
        if i in SCN and os.path.exists(mix):
            sname,pref=SCN[i][0];v0=VS[sname][l]
            vl.write(f"file '{last}'\nduration {v0}\n")
            base=Image.open(pg).convert('RGB');frames=sorted(glob.glob(pref+'*.png'))
            for j,fr in enumerate(frames):
                im=base.copy();im.paste(Image.open(fr).convert('RGB'),(44,44),mask)
                out=f'{tmp}/p{i:02d}_{j:03d}.jpg';im.save(out,quality=90);vl.write(f"file '{out}'\nduration {1/12:.5f}\n");last=out
            rest=dur(mix)-v0-len(frames)/12
            vl.write(f"file '{last}'\nduration {rest}\n");al.write(f"file '{mix}'\n");pd.append(dur(mix))
        else:
            d_=dur(f'{SITE}/audio/{l}/{n}.mp3');vl.write(f"file '{pg}'\nduration {d_}\n");al.write(f"file '{SITE}/audio/{l}/{n}.mp3'\n");pd.append(d_)
    vl.write(f"file '{SITE}/pages/{l}/18.jpg'\n");vl.close();al.close()
    out=f'{SITE}/video/The-Way-Back-Home_{U}.mp4'
    music_track(pd,f'{tmp}/music.wav')
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',f'{tmp}/v.txt','-f','concat','-safe','0','-i',f'{tmp}/a.txt','-i',f'{tmp}/music.wav',
      '-filter_complex','[1:a]aresample=44100,asplit[n1][n2];[2:a]volume=0.32[mu];[mu][n1]sidechaincompress=threshold=0.02:ratio=5:attack=120:release=900[md];[n2][md]amix=inputs=2:normalize=0:duration=first[a];[0:v]scale=720:1280:flags=lanczos,fps=12,format=yuv420p[v]',
      '-map','[v]','-map','[a]','-c:v','libx264','-preset','veryfast','-crf','26','-tune','stillimage','-g','120','-c:a','aac','-b:a','96k','-ac','1','-shortest','-movflags','+faststart',out],check=True)
    print(l,f'{os.path.getsize(out)/1e6:.1f}MB',round(dur(out),1),flush=True)
for l in sys.argv[1:]: build(l)
