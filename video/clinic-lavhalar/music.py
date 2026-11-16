import numpy as np, wave
SR=44100; T=32.0; N=int(SR*T); out=np.zeros((N,2))
def hz(m): return 440*2**((m-69)/12)
def piano(m, dur, vel):
    n=int(SR*dur); t=np.arange(n)/SR; f=hz(m)
    s=sum(a*np.sin(2*np.pi*f*k*t)*np.exp(-t*(2.2+1.4*k)) for k,a in [(1,1),(2,.45),(3,.18),(4,.08)])
    s*=np.minimum(1,t/0.004)*vel
    return s
def add(sig,start,pan=0.0):
    i=int(start*SR)
    if i>=N: return
    j=min(N,i+len(sig)); s=sig[:j-i]
    out[i:j,0]+=s*(1-pan)*0.5; out[i:j,1]+=s*(1+pan)*0.5
beat=60/92; bar=beat*4
prog=[(60,[0,4,7]),(55,[0,4,7]),(57,[0,3,7]),(53,[0,4,7])]  # C G Am F
mel=[[76,74,72,74],[74,71,74,79],[76,72,72,76],[77,76,74,72]]
nb=int(T/bar)+1
for b in range(nb):
    root,iv=prog[b%4]; t0=b*bar
    # bass
    for k in (0,2): add(piano(root-24,beat*2.2,.55),t0+k*beat,0)
    # arpeggio
    notes=[root+x for x in iv]+[root+12]
    pat=[0,1,2,3,2,1,2,3]
    for k,p in enumerate(pat): add(piano(notes[p],beat*1.6,.22),t0+k*beat/2,(-.3 if k%2 else .3))
    # pad
    n=int(SR*bar); t=np.arange(n)/SR
    env=np.minimum(1,t/0.8)*np.minimum(1,(bar-t)/0.6)
    pad=sum(np.sin(2*np.pi*hz(root+x+12)*t)+.3*np.sin(2*np.pi*hz(root+x+12)*2.003*t) for x in iv)*env*.035
    add(pad,t0,0)
    # melody from bar 4
    if b>=4:
        for k,m in enumerate(mel[b%4]): add(piano(m,beat*2,.3),t0+k*beat,.1)
out/=np.abs(out).max()*1.15
pcm=(out*32767).astype(np.int16)
w=wave.open('music_raw.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes()); w.close()
