# Synthesizes background music + sound effects for the promo (no external samples).
import numpy as np, wave, sys
SR=48000; DUR=36.4; N=int(SR*DUR)
L=np.zeros(N); R=np.zeros(N)
rng=np.random.default_rng(7)
def note(f): return 440*2**((f-69)/12)
def add(buf,start,sig,gain=1.0):
    i=int(start*SR)
    if i<0: sig=sig[-i:]; i=0
    j=min(N,i+len(sig))
    if i<N: buf[i:j]+=sig[:j-i]*gain
def env(n,a=.01,r=.3):
    t=np.arange(n)/SR; e=np.minimum(1,t/a)*np.exp(-t/r); return e
bpm=100; beat=60/bpm
# chords: C G Am F (midi)
CH=[[48,60,64,67],[43,59,62,67],[45,60,64,69],[41,60,65,69]]
chord_len=4*beat
t=0; k=0
while t<DUR:
    ch=CH[k%4]; n=int(chord_len*SR)+SR//2; tt=np.arange(n)/SR
    pad=np.zeros(n)
    for m in ch[1:]:
        f=note(m)
        for h,a in [(1,1),(2,.35),(3,.15)]:
            pad+=a*np.sin(2*np.pi*f*h*tt+ h)*(1+0.003*np.sin(2*np.pi*5*tt))
    e=np.minimum(1,tt/.6)*np.minimum(1,np.maximum(0,(n/SR-tt)/.6))
    add(L,t,pad*e,.035); add(R,t,pad*e,.035)
    # bass
    bn=int(beat*SR); bt=np.arange(bn)/SR
    for b in range(4):
        bs=np.sin(2*np.pi*note(ch[0])*bt)*env(bn,.005,.35)
        add(L,t+b*beat,bs,.10); add(R,t+b*beat,bs,.10)
    # arpeggio plucks (eighths)
    arp=[ch[1]+12,ch[2]+12,ch[3]+12,ch[2]+12]
    pn=int(.5*SR); pt=np.arange(pn)/SR
    for s8 in range(8):
        f=note(arp[s8%4]); pl=(np.sin(2*np.pi*f*pt)+.3*np.sin(4*np.pi*f*pt))*env(pn,.003,.18)
        pan=.3+.4*(s8%2)
        add(L,t+s8*beat/2,pl,.045*(1-pan)*2); add(R,t+s8*beat/2,pl,.045*pan*2)
    t+=chord_len; k+=1
# drums
kn=int(.35*SR); kt=np.arange(kn)/SR
kick=np.sin(2*np.pi*(50+90*np.exp(-kt*30))*kt)*np.exp(-kt*9)
hn=int(.06*SR); hat=rng.standard_normal(hn)*np.exp(-np.arange(hn)/SR*70); hat=np.diff(hat,prepend=0)
b=0
while b*beat<DUR:
    if b*beat>1.0:
        if b%2==0: add(L,b*beat,kick,.22); add(R,b*beat,kick,.22)
        add(L,b*beat+beat/2,hat,.05); add(R,b*beat+beat/2,hat,.04)
    b+=1
# ---- SFX ----
def whoosh(d=.35):
    n=int(d*SR); x=rng.standard_normal(n); y=np.zeros(n); a=0
    cut=np.linspace(.02,.35,n)
    for i in range(n): a+=cut[i]*(x[i]-a); y[i]=a
    return y*np.sin(np.pi*np.arange(n)/n)**2
def pop():
    n=int(.09*SR); tt=np.arange(n)/SR; return np.sin(2*np.pi*(900-5500*tt)*tt)*np.exp(-tt*40)
def ding(f=1320):
    n=int(.6*SR); tt=np.arange(n)/SR; return (np.sin(2*np.pi*f*tt)+.5*np.sin(2*np.pi*f*2.01*tt))*np.exp(-tt*6)
def zap():
    n=int(.18*SR); tt=np.arange(n)/SR; return np.sign(np.sin(2*np.pi*(180+60*np.sin(tt*90))*tt))*np.exp(-tt*18)*.5
def click():
    n=int(.02*SR); return rng.standard_normal(n)*np.exp(-np.arange(n)/SR*300)
W=whoosh()
for s in [0.1,4.4,8.5,12,14,16,18,20.2,24.1,28.1,31.5,32.0]: add(L,s-.12,W,.25); add(R,s-.12,W,.25)
for s in [0.35,4.15,8.15,24.1,31.15,8.5,8.95,9.4,9.85,10.3,25,25.25,25.5,25.75,24.8,12.3,14.3,16.3,18.3]:
    add(L,s,pop(),.18); add(R,s,pop(),.18)
for s in [20.4,21.2,22.0,22.8]: add(L,s,ding(),.10); add(R,s,ding(),.10)
add(L,34.4,ding(1760),.12); add(R,34.4,ding(1760),.12)
for s in [1.8,2.15,2.5,2.85]: add(L,s,zap(),.06); add(R,s,zap(),.06)
for i,s in enumerate(np.arange(32.6,34.2,.085)): add(L,s,click(),.10); add(R,s,click(),.10)
# master fade
tt=np.arange(N)/SR; fade=np.minimum(1,tt/.4)*np.minimum(1,(DUR-tt)/1.2)
st=np.stack([L*fade,R*fade],1); st/=max(1e-9,np.abs(st).max()/0.89)
with wave.open(sys.argv[1] if len(sys.argv)>1 else 'audio.wav','wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st*32767).astype('<i2').tobytes())
print('ok')
