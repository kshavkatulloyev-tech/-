import json, subprocess, os
U='/root/.claude/uploads/07c7ce4e-efa8-59e8-b1ed-62f1304ff321/'
def run(c): subprocess.run(c, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
ENC=['-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','-r','30','-an']
plan=json.load(open('plan.json'))
for s in plan:
    T=s['t']
    fc=(f"[1:v]setpts=PTS-STARTPTS,fps=30,crop=1072:1340:0:290,scale=954:1192,crop=900:1125:x='27*t/{T}':y='33*t/{T}',format=rgba[v];"
        f"[2:v]format=gray[m];[v][m]alphamerge[vm];[0:v]setpts=PTS-STARTPTS[bg];[bg][vm]overlay=90:430:shortest=1,format=yuv420p")
    run(['ffmpeg','-y','-loop','1','-framerate','30','-i',f"bg_{s['name']}.png",'-ss',str(s['ss']),'-t',str(T),'-i',U+s['src'],
         '-loop','1','-i','mask.png','-filter_complex',fc,'-t',str(T)]+ENC+[f"seg_{s['name']}.mp4"])
chaps={}
for s in plan: chaps.setdefault(s['chap'],[]).append(f"seg_{s['name']}.mp4")
parts=[]
for c,files in sorted(chaps.items()):
    open(f'ch{c}.txt','w').write(''.join(f"file '{f}'\n" for f in files))
    run(['ffmpeg','-y','-f','concat','-safe','0','-i',f'ch{c}.txt','-c','copy',f'chap{c}.mp4']); parts.append((f'chap{c}.mp4',sum(x['t'] for x in plan if x['chap']==c)))
# services: rows appear
lines=["file 'svc_0.png'\nduration 0.5\n"]+[f"file 'svc_{k}.png'\nduration 0.35\n" for k in range(1,6)]+["file 'svc_6.png'\nduration 2.6\n","file 'svc_6.png'\n"]
open('svc.txt','w').write(''.join(lines))
run(['ffmpeg','-y','-f','concat','-safe','0','-i','svc.txt','-vf','fps=30,format=yuv420p','-t','4.85']+ENC+['svc.mp4']); parts.append(('svc.mp4',4.85))
run(['ffmpeg','-y','-loop','1','-framerate','30','-i','outro.png','-vf',"zoompan=z='1+0.0006*on':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=1:s=1080x1920:fps=30,format=yuv420p",'-t','5.5']+ENC+['outro.mp4']); parts.append(('outro.mp4',5.5))
X=0.4
inp=[]; fc=[]; off=0; prev='[0:v]'
for i,(f,d) in enumerate(parts): inp+=['-i',f]
for i in range(1,len(parts)):
    off+=parts[i-1][1]-X
    out=f'[x{i}]'
    fc.append(f"{prev}[{i}:v]xfade=transition=fade:duration={X}:offset={off:.3f}{out}"); prev=out
total=sum(d for _,d in parts)-X*(len(parts)-1)
run(['ffmpeg','-y']+inp+['-filter_complex',';'.join(fc),'-map',prev]+ENC+['video_noaudio.mp4'])
json.dump({'total':total},open('total.json','w')); print('total',total)
