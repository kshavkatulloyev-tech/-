# Generates Uzbek voice-over (Latin script — the uz-UZ voices do not read Cyrillic),
# each line placed at its scene start and sped up slightly if it would overrun its slot.
# Usage: python3 voice.py <workdir> <voice>   (voice: uz-UZ-SardorNeural | uz-UZ-MadinaNeural)
import asyncio, os, subprocess, sys, json
import edge_tts

LINES = [  # (start, end, text)
    (0.25, 4.0,  "Bel va bo'yin og'rig'idan qiynalyapsizmi?"),
    (4.15, 8.0,  "Yechimi bor — Habibullo Shams klinikasi!"),
    (8.1, 12.1, "Zamonaviy fizioterapiya va reabilitatsiya markazi."),
    (12.2, 14.0, "Kinezioterapiya."),
    (14.2, 16.0, "Massaj."),
    (16.2, 18.0, "TEKAR terapiya."),
    (18.2, 20.0, "Pressoterapiya."),
    (20.2, 24.0, "Malakali mutaxassislar, zamonaviy apparatlar."),
    (24.2, 28.0, "Jami ellikdan ortiq fizioterapiya usuli!"),
    (28.1, 31.3, "Jonga shifo ham oro — nasib etsa topasiz!"),
    (31.2, 36.2, "Hoziroq qo'ng'iroq qiling yoki Telegramda yozing!"),
]

def dur(p):
    return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                                          '-of', 'csv=p=0', p]).decode().strip())

async def main(work, voice):
    os.makedirs(work, exist_ok=True)
    proxy = os.environ.get('HTTPS_PROXY')
    parts = []
    for i, (a, b, text) in enumerate(LINES):
        raw = os.path.join(work, f'{voice}_{i:02d}.mp3')
        await edge_tts.Communicate(text, voice, rate='+5%', proxy=proxy).save(raw)
        d = dur(raw); slot = (b - a) - 0.1
        tempo = max(1.0, d / slot)
        parts.append((a, raw, tempo, d))
        print(f'{i:02d} {d:5.2f}s slot {slot:4.2f}s tempo {tempo:.2f}  {text}')
    inputs, filters = [], []
    for k, (a, raw, tempo, d) in enumerate(parts):
        inputs += ['-i', raw]
        tf = f'atempo={min(tempo, 2.0):.3f},' if tempo > 1.0 else ''
        filters.append(f'[{k}:a]{tf}aresample=48000,adelay={int(a*1000)}|{int(a*1000)}[v{k}]')
    mix = ''.join(f'[v{k}]' for k in range(len(parts)))
    filters.append(f'{mix}amix=inputs={len(parts)}:normalize=0,apad=whole_dur=36.4,atrim=0:36.4[out]')
    out = os.path.join(work, f'voice_{voice}.wav')
    subprocess.check_call(['ffmpeg', '-v', 'error', '-y', *inputs, '-filter_complex', ';'.join(filters),
                           '-map', '[out]', '-ac', '2', out])
    print('->', out)

asyncio.run(main(sys.argv[1], sys.argv[2]))
