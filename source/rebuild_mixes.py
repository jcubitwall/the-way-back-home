import json,subprocess
S='/home/claude/book/site'
def dur(f): return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',f]))
def run(a): subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y']+a,check=True)
LV={'s01':-27,'s02':-28,'s03':-26,'s04':-25,'s05':-27,'s06':-28,'s07':-27}
# scene sounds are prepared separately (original clip audio at half level)
def mix_pause(l,page,k,p1src,p1,v,r,restsrc,reststart=None):
    out=f'{S}/audio/{l}/{page:02d}-mix.mp3'
    if reststart is None:
        run(['-i',p1src,'-i',f'{S}/scenes/{k}.mp3','-i',restsrc,'-filter_complex',f"[0]atrim=0:{p1+0.05}[a];[2]silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.02,adelay={int(r*1000)}[b];[1]adelay={int(v*1000)}[s];[a][s][b]amix=inputs=3:normalize=0:duration=longest",'-ar','44100','-ac','1','-c:a','libmp3lame','-b:a','96k',out])
    else:
        run(['-i',p1src,'-i',f'{S}/scenes/{k}.mp3','-filter_complex',f"[0]atrim=0:{p1+0.05}[a];[0]atrim=start={reststart},asetpts=PTS-STARTPTS,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.02[b0];[b0]adelay={int(r*1000)}[b];[1]adelay={int(v*1000)}[s];[a][s][b]amix=inputs=3:normalize=0:duration=longest",'-ar','44100','-ac','1','-c:a','libmp3lame','-b:a','96k',out])
def mix_over(l,page,k,v):
    run(['-i',f'{S}/audio/{l}/{page:02d}.mp3','-i',f'{S}/scenes/{k}.mp3','-filter_complex',f"[1]adelay={int(v*1000)}[s];[0][s]amix=inputs=2:normalize=0:duration=first",'-ar','44100','-ac','1','-c:a','libmp3lame','-b:a','96k',f'{S}/audio/{l}/{page:02d}-mix.mp3'])
J=lambda n:json.load(open(n))
v1,v2,v3,v4,v5,v6,v7=[J(f's0{i}_vs.json') for i in range(1,8)];a3,a4=J('s03_at.json'),J('s04_at.json')
M1=dur(f'{S}/scenes/s01.mp4');M3=dur(f'{S}/scenes/s03.mp4')
for l in v1:
    a=f'{S}/audio/{l}/02-1.mp3';mix_pause(l,2,'s01',a,dur(a)-0.12,v1[l],round(v1[l]+M1-0.35,2),f'{S}/audio/{l}/02-2.mp3')
    mix_over(l,3,'s02',v2[l])
    t=a3[l];mix_pause(l,4,'s03',f'{S}/audio/{l}/04.mp3',t-0.1,v3[l],round(v3[l]+M3-0.45,2),None,reststart=t)
    t=a4[l];mix_pause(l,5,'s04',f'{S}/audio/{l}/05.mp3',t-0.1,v4[l],round(v4[l]+5.4,2),None,reststart=t)
    mix_over(l,6,'s05',v5[l]);mix_over(l,7,'s06',v6[l]);mix_over(l,8,'s07',v7[l])
    print(l,end=' ',flush=True)
