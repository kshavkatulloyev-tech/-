# Generates Uzbek voice-over (Latin script — the uz-UZ voices do not read Cyrillic),
# each line placed at its scene start and sped up slightly if it would overrun its slot.
# Usage: python3 voice.py <workdir> <voice>
#   voice: uz-UZ-SardorNeural | uz-UZ-MadinaNeural (Edge TTS) or el:<ElevenLabs voice_id>
import asyncio, os, subprocess, sys, json
import edge_tts

LINES = [  # (start, end, text)
    (0.25, 4.0,  "Bel va bo'yin og'rig'idan qiynalyapsizmi?"),
    (4.15, 8.0,  "Yechimi bor...|Habibullo Shams klinikasi!"),
    (8.1, 12.1, "Zamonaviy fizioterapiya|va reabilitatsiya markazi."),
    (12.05, 14.0, "Kinezioterapiya."),
    (14.05, 16.0, "Massaj."),
    (16.05, 18.0, "TEKAR terapiya."),
    (18.05, 20.0, "Pressoterapiya."),
    (20.2, 24.0, "Malakali mutaxassislar,|zamonaviy apparatlar."),
    (24.2, 28.0, "Jami ellikdan ortiq fizioterapiya usuli!"),
    (28.1, 31.3, "Jonga shifo ham oro,|nasib etsa topasiz!"),
    (31.2, 36.2, "Hoziroq qo'ng'iroq qiling,|yoki Telegramda yozing!"),
]

# Phrase schedule matching the on-screen captions (used for ElevenLabs voices)
LINES_PHRASES = [
    (0.25, 4.0,   "Bel va bo'yin og'rig'idan qiynalyapsizmi?"),
    (4.2, 6.1,    "Yechimi bor!"),
    (6.2, 8.0,    "Habibullo Shams klinikasi!"),
    (8.05, 10.15, "Zamonaviy fizioterapiya"),
    (10.2, 12.45, "va reabilitatsiya markazi."),
    (12.6, 14.3,  "Kinezioterapiya."),
    (14.4, 16.2,  "Massaj."),
    (16.3, 18.3,  "TEKAR terapiya."),
    (18.4, 20.2,  "Pressoterapiya."),
    (20.3, 22.3,  "Malakali mutaxassislar,"),
    (22.3, 24.3,  "zamonaviy apparatlar."),
    (24.9, 28.2,  "Jami ellikdan ortiq fizioterapiya usuli!"),
    (28.4, 30.5,  "Jonga shifo ham oro,"),
    (30.55, 32.5, "nasib etsa topasiz!"),
    (32.5, 34.5,  "Hoziroq qo'ng'iroq qiling,"),
    (34.5, 36.3,  "yoki Telegramda yozing!"),
]

def dur(p):
    return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                                          '-of', 'csv=p=0', p]).decode().strip())

VOICE_CFG = {  # rate, pitch: slightly slower and lower than default sounds less robotic
    'uz-UZ-SardorNeural': ('-4%', '-6Hz'),
    'uz-UZ-MadinaNeural': ('-4%', '-2Hz'),
}
PAUSE = 0.22  # seconds of silence between phrases
TRIM = 'silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.03,areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.06,areverse'  # strip the padding the TTS adds around each phrase
# warm EQ, gentle compression and a short room reflection to soften the dry TTS sound
FX = ('highpass=f=75,equalizer=f=200:t=q:w=1:g=2.5,equalizer=f=3200:t=q:w=1.5:g=-2.5,'
      'equalizer=f=8000:t=q:w=2:g=1.5,acompressor=threshold=-20dB:ratio=3:attack=8:release=150:makeup=2,'
      'aecho=0.85:0.6:35|60:0.10|0.06')

def synth_elevenlabs(text, voice_id, out):
    """ElevenLabs TTS (eleven_v4 supports Uzbek). The API key is injected by the network proxy."""
    import urllib.request
    req = urllib.request.Request(
        f'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}?output_format=mp3_44100_128',
        data=json.dumps({'text': text, 'model_id': 'eleven_v4', 'language_code': 'uz',
                         'voice_settings': {'stability': 0.5, 'similarity_boost': 0.8, 'style': 0.3}}).encode(),
        headers={'xi-api-key': 'proxy-injected', 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=120) as r, open(out, 'wb') as f:
        f.write(r.read())

async def synth(text, voice, out, proxy):
    if voice.startswith('el:'):
        return synth_elevenlabs(text, voice[3:], out)
    rate, pitch = VOICE_CFG.get(voice, ('+0%', '+0Hz'))
    await edge_tts.Communicate(text, voice, rate=rate, pitch=pitch, proxy=proxy).save(out)

async def main(work, voice):
    os.makedirs(work, exist_ok=True)
    proxy = os.environ.get('HTTPS_PROXY')
    parts = []
    lines = LINES_PHRASES if voice.startswith('el:') else LINES
    for i, (a, b, text) in enumerate(lines):
        phrases = [text.replace('|', ' ')] if voice.startswith('el:') else text.split('|'); files = []
        for j, ph in enumerate(phrases):
            f = os.path.join(work, f'{voice.replace(":", "_")}_{i:02d}_{j}.mp3')
            if not (os.path.exists(f) and os.path.getsize(f) > 1000):  # cache: don't re-spend TTS credits
                await synth(ph, voice, f, proxy)
            files.append(f)
        raw = os.path.join(work, f'{voice.replace(":", "_")}_{i:02d}.wav')
        if len(files) == 1:
            subprocess.check_call(['ffmpeg', '-v', 'error', '-y', '-i', files[0], '-af', TRIM, '-ar', '48000', '-ac', '1', raw])
        else:
            ins = sum([['-i', f] for f in files], [])
            fc = ''.join(f'[{k}:a]aresample=48000,aformat=channel_layouts=mono,{TRIM}' + (f',apad=pad_dur={PAUSE}' if k < len(files)-1 else '') + f'[p{k}];' for k in range(len(files)))
            fc += ''.join(f'[p{k}]' for k in range(len(files))) + f'concat=n={len(files)}:v=0:a=1[o]'
            subprocess.check_call(['ffmpeg', '-v', 'error', '-y', *ins, '-filter_complex', fc, '-map', '[o]', raw])
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
    fx = FX.rsplit(',aecho', 1)[0] if voice.startswith('el:') else FX
    filters.append(f'{mix}amix=inputs={len(parts)}:normalize=0,{fx},apad=whole_dur=36.4,atrim=0:36.4[out]')
    out = os.path.join(work, f'voice_{voice.replace(":", "_")}.wav')
    subprocess.check_call(['ffmpeg', '-v', 'error', '-y', *inputs, '-filter_complex', ';'.join(filters),
                           '-map', '[out]', '-ac', '2', out])
    print('->', out)

asyncio.run(main(sys.argv[1], sys.argv[2]))
