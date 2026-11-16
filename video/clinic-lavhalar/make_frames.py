import json
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1920
BG = (244, 241, 235)
INK = (24, 32, 48)
GRAY = (120, 124, 134)
BLUE = (30, 78, 160)
GREEN = (52, 158, 72)
TRACK = (222, 217, 208)
F = '/usr/share/fonts/opentype/inter/'
def font(w, s): return ImageFont.truetype(F + f'Inter-{w}.otf', s)

IMG2 = '/root/.claude/uploads/07c7ce4e-efa8-59e8-b1ed-62f1304ff321/eab9ff5c-image.jpg'
src = Image.open(IMG2).convert('RGB')
logo = src.crop((410, 690, 665, 905))
qr = src.crop((845, 188, 1036, 372))

CARD = (90, 430, 990, 1555)  # 900x1125 (4:5)
NSEG = 5

def circle_logo(size):
    l = logo.resize((int(size * 0.78), int(size * 0.78 * logo.height / logo.width)), Image.LANCZOS)
    badge = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    m = Image.new('L', (size, size), 0); ImageDraw.Draw(m).ellipse((0, 0, size - 1, size - 1), fill=255)
    white = Image.new('RGBA', (size, size), (255, 255, 255, 255))
    white.paste(l, ((size - l.width) // 2, (size - l.height) // 2))
    badge.paste(white, (0, 0), m)
    return badge

def header(img, d, filled):
    b = circle_logo(78)
    img.paste(b, (60, 62), b)
    d.text((156, 66), 'Ҳабибулло Шамс', font=font('Bold', 32), fill=INK)
    d.text((156, 106), 'Физиотерапия ва реабилитация маркази', font=font('Medium', 24), fill=GRAY)
    x0, x1, y, gap = 60, 1020, 178, 12
    sw = (x1 - x0 - gap * (NSEG - 1)) / NSEG
    for i in range(NSEG):
        a = x0 + i * (sw + gap)
        d.rounded_rectangle((a, y, a + sw, y + 8), radius=4, fill=BLUE if i < filled else TRACK)

def rich(d, xy, parts, f, center=False, maxw=None):
    """parts: list of (text, color). returns width"""
    w = sum(d.textlength(t, font=f) for t, _ in parts)
    x, y = xy
    if center: x = (W - w) / 2
    for t, c in parts:
        d.text((x, y), t, font=f, fill=c); x += d.textlength(t, font=f)
    return w

def parse(s, base=INK, acc=BLUE):
    # *word* -> accent
    out, on = [], False
    for i, chunk in enumerate(s.split('*')):
        if chunk: out.append((chunk, acc if i % 2 else base))
    return out

def caption(d, text, y=1612):
    f = font('Bold', 50)
    for i, line in enumerate(text.split('\n')):
        rich(d, (0, y + i * 66), parse(line), f, center=True)

def card_shadow(img, box, r=40):
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((box[0], box[1] + 18, box[2], box[3] + 18), radius=r, fill=(60, 50, 30, 70))
    sh = sh.filter(ImageFilter.GaussianBlur(28))
    img.alpha_composite(sh)
    ImageDraw.Draw(img).rounded_rectangle(box, radius=r, fill=(255, 255, 255, 255))

def footer(d):
    t = '+998 93 963 10 95   ·   Вобкент, Бухоро'
    f = font('Medium', 26)
    d.text(((W - d.textlength(t, font=f)) / 2, 1830), t, font=f, fill=GRAY)

def scene(name, label, title, cap, filled, title_size=78):
    img = Image.new('RGBA', (W, H), BG + (255,))
    d = ImageDraw.Draw(img)
    header(img, d, filled)
    d.text((60, 232), label, font=font('Bold', 28), fill=GREEN)
    rich(d, (58, 272), parse(title), font('ExtraBold', title_size))
    card_shadow(img, CARD)
    d = ImageDraw.Draw(img)
    caption(d, cap)
    footer(d)
    img.convert('RGB').save(f'bg_{name}.png')

# rounded mask for video card
m = Image.new('L', (CARD[2] - CARD[0], CARD[3] - CARD[1]), 0)
ImageDraw.Draw(m).rounded_rectangle((0, 0, m.width - 1, m.height - 1), radius=40, fill=255)
m.save('mask.png')

scenes = json.load(open('plan.json'))
for s in scenes:
    if s['type'] == 'clip':
        scene(s['name'], s['label'], s['title'], s['cap'], s['filled'], s.get('ts', 78))

# services scene: rows appear one by one
rows = ['Кинезиотерапия', 'Катталар ва болалар массажи', 'ПМСТ магнит терапияси',
        'Юқори интенсив лазер терапияси', 'TEKAR терапияси', 'ва бошқа 50 дан ортиқ усул']
for k in range(len(rows) + 1):
    img = Image.new('RGBA', (W, H), BG + (255,))
    d = ImageDraw.Draw(img)
    header(img, d, 5)
    d.text((60, 232), 'БИЗДА', font=font('Bold', 28), fill=GREEN)
    rich(d, (58, 272), parse('Даволаш *усуллари*'), font('ExtraBold', 78))
    for i in range(k):
        y = 440 + i * 178
        last = i == len(rows) - 1
        box = (90, y, 990, y + 150)
        sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle((box[0], box[1] + 10, box[2], box[3] + 10), radius=32, fill=(60, 50, 30, 45))
        img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16)))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle(box, radius=32, fill=BLUE if last else (255, 255, 255))
        cx, cy = 165, y + 75
        d.ellipse((cx - 38, cy - 38, cx + 38, cy + 38), fill=(255, 255, 255) if last else GREEN)
        if last:
            f = font('ExtraBold', 30); t = '50+'
            d.text((cx - d.textlength(t, font=f) / 2, cy - 19), t, font=f, fill=BLUE)
        else:
            d.line([(cx - 16, cy + 1), (cx - 4, cy + 13), (cx + 18, cy - 12)], fill=(255, 255, 255), width=8, joint='curve')
        d.text((232, y + 52), rows[i], font=font('Bold', 40), fill=(255, 255, 255) if last else INK)
    caption(d, 'Замонавий физиотерапия\nва *реабилитация*', y=1560)
    footer(d)
    img.convert('RGB').save(f'svc_{k}.png')

# outro
img = Image.new('RGBA', (W, H), BG + (255,))
d = ImageDraw.Draw(img)
header(img, d, 5)
b = circle_logo(300)
sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
ImageDraw.Draw(sh).ellipse((390, 330, 690, 630), fill=(60, 50, 30, 60))
img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(24)))
img.paste(b, (390, 310), b)
d = ImageDraw.Draw(img)
f = font('ExtraBold', 92); t = 'ФИЗИОТЕРАПИЯ'
d.text(((W - d.textlength(t, font=f)) / 2, 660), t, font=f, fill=BLUE)
f = font('Bold', 52); t = 'Ҳабибулло Шамс клиникаси'
d.text(((W - d.textlength(t, font=f)) / 2, 780), t, font=f, fill=INK)
info = [('Манзил', 'Бухоро вилояти, Вобкент тумани'), ('Телефон', '+998 93 963 10 95'), ('Telegram', 't.me/HabibulloShams')]
for i, (k, v) in enumerate(info):
    y = 900 + i * 118
    d.rounded_rectangle((90, y, 990, y + 98), radius=28, fill=(255, 255, 255))
    d.text((130, y + 12), k.upper(), font=font('Bold', 22), fill=GREEN)
    d.text((130, y + 42), v, font=font('Bold', 38), fill=INK)
# QR
q = qr.resize((300, int(300 * qr.height / qr.width)), Image.LANCZOS)
qy = 1265
d.rounded_rectangle((W / 2 - 175, qy - 20, W / 2 + 175, qy + q.height + 64), radius=30, fill=(255, 255, 255))
img.paste(q, (int(W / 2 - 150), qy))
f = font('Bold', 24); t = 'TELEGRAM КАНАЛИ'
d.text(((W - d.textlength(t, font=f)) / 2, qy + q.height + 12), t, font=f, fill=BLUE)
f = font('SemiBoldItalic', 44)
for i, t in enumerate(['«Жонга шифо ҳам оро,', 'насиб этса топасиз!»']):
    d.text(((W - d.textlength(t, font=f)) / 2, 1700 + i * 60), t, font=f, fill=BLUE)
img.convert('RGB').save('outro.png')
print('ok')
