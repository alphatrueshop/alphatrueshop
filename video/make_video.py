import subprocess, math, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

import os
SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1]
W, H, FPS = 1080, 1920, 30
FONT = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
BLUE, ORANGE, DARK, WHITE = (14, 165, 233), (249, 115, 22), (15, 23, 42), (255, 255, 255)
LINE_GREEN = (6, 199, 85)

_fc = {}
def font(s):
    if s not in _fc: _fc[s] = ImageFont.truetype(FONT, s)
    return _fc[s]

def ease(x):
    x = max(0.0, min(1.0, x)); return 1 - (1 - x) ** 3

def cover(img, w, h, zoom=1.0, dx=0.0):
    r = max(w / img.width, h / img.height) * zoom
    im = img.resize((int(img.width * r) + 1, int(img.height * r) + 1), Image.LANCZOS)
    x = (im.width - w) / 2 + dx * (im.width - w) / 2
    y = (im.height - h) / 2
    return im.crop((int(x), int(y), int(x) + w, int(y) + h))

def gradient(c1, c2):
    g = Image.new("RGB", (1, 256))
    for i in range(256):
        t = i / 255; g.putpixel((0, i), tuple(int(a + (b - a) * t) for a, b in zip(c1, c2)))
    return g.resize((W, H))

def text(d, xy, s, size, fill=WHITE, t=1.0, stroke=3, sc=None, anchor="mm", rise=60):
    """Draw text that fades/rises in with progress t (0..1)."""
    if t <= 0: return
    a = ease(t)
    x, y = xy; y += (1 - a) * rise
    col = fill + (int(255 * a),)
    sc = (sc or DARK) + (int(255 * a),)
    d.text((x, y), s, font=font(size), fill=col, anchor=anchor,
           stroke_width=stroke, stroke_fill=sc)

def pill(d, box, color, t=1.0, r=40):
    if t <= 0: return
    a = ease(t)
    x0, y0, x1, y1 = box
    cx = (x0 + x1) / 2; hw = (x1 - x0) / 2 * a
    d.rounded_rectangle((cx - hw, y0, cx + hw, y1), r, fill=color + (int(235 * a),))

roadster = Image.open(f"{SRC}/roadster.jpg").convert("RGB")
staff = Image.open(f"{SRC}/staff.jpg").convert("RGB")
logo = Image.open(f"{SRC}/logo.jpg").convert("RGB")
bg_light = gradient((224, 242, 254), (255, 237, 213))
bg_blue = gradient((2, 132, 199), (14, 165, 233))
bg_dark = gradient((15, 23, 42), (30, 41, 59))

def circle_img(img, size):
    im = img.resize((size, size), Image.LANCZOS)
    m = Image.new("L", (size, size), 0); ImageDraw.Draw(m).ellipse((0, 0, size, size), fill=255)
    return im, m

LOGO_SZ = 380
logo_c, logo_m = circle_img(logo, LOGO_SZ)

# ---------- scenes: (duration_sec, fn(t_local, dur) -> RGB image) ----------
def s_intro(t, D):
    f = bg_light.copy().convert("RGBA")
    d = ImageDraw.Draw(f)
    a = ease(t / 0.8)
    sz = int(LOGO_SZ * (0.6 + 0.4 * a))
    if sz > 10:
        lc = logo_c.resize((sz, sz)); lm = logo_m.resize((sz, sz)).point(lambda p: int(p * a))
        f.paste(lc, (W // 2 - sz // 2, 620 - sz // 2), lm)
    d.text((W // 2 - 10, 950), "alpha", font=font(130), fill=BLUE + (int(255 * ease((t - .5) / .6)),), anchor="rm")
    d.text((W // 2 + 10, 950), "true", font=font(130), fill=ORANGE + (int(255 * ease((t - .5) / .6)),), anchor="lm")
    text(d, (W // 2, 1090), "shop", 90, fill=DARK, t=(t - .7) / .6, stroke=0)
    text(d, (W // 2, 1300), "中古車の高価買取・販売", 64, fill=DARK, t=(t - 1.1) / .6, stroke=0)
    text(d, (W // 2, 1400), "東京都八王子市", 54, fill=(100, 116, 139), t=(t - 1.4) / .6, stroke=0)
    return f

def s_question(t, D):
    f = cover(roadster, W, H, zoom=1.05 + 0.12 * t / D, dx=-0.4 + 0.5 * t / D).convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    for y in range(H):  # bottom darkening
        od.line((0, y, W, y), fill=(0, 0, 0, int(200 * max(0, (y - 700) / 1220))))
    f = Image.alpha_composite(f, ov); d = ImageDraw.Draw(f)
    text(d, (W // 2, 1250), "あなたの愛車", 110, t=(t - .2) / .5, stroke=6)
    text(d, (W // 2, 1420), "いくらで売れる？", 120, fill=(251, 191, 36), t=(t - .7) / .5, stroke=6)
    pill(d, (180, 1600, 900, 1700), ORANGE, t=(t - 1.6) / .5)
    text(d, (W // 2, 1650), "買取実績：マツダ ロードスター", 46, t=(t - 1.8) / .4, stroke=0, rise=0)
    return f

def steps_scene(title, sub, items, bg, accent):
    def fn(t, D):
        f = bg.copy().convert("RGBA"); d = ImageDraw.Draw(f)
        text(d, (W // 2, 330), sub, 56, fill=WHITE if bg is not bg_light else DARK, t=t / .4, stroke=0)
        text(d, (W // 2, 470), title, 120, fill=WHITE, t=(t - .2) / .5, stroke=8, sc=accent)
        for i, (n, s1, s2) in enumerate(items):
            st = (t - 0.9 - i * 0.7) / .5
            if st <= 0: continue
            a = ease(st); y = 720 + i * 330 + (1 - a) * 80
            card = Image.new("RGBA", (W, H), (0, 0, 0, 0)); cd = ImageDraw.Draw(card)
            cd.rounded_rectangle((90, y, W - 90, y + 270), 36, fill=(255, 255, 255, int(245 * a)))
            cd.ellipse((130, y + 60, 280, y + 210), fill=accent + (int(255 * a),))
            cd.text((205, y + 135), n, font=font(80), fill=(255, 255, 255, int(255 * a)), anchor="mm")
            cd.text((320, y + 95), s1, font=font(62), fill=DARK + (int(255 * a),), anchor="lm", stroke_width=1, stroke_fill=DARK + (int(255 * a),))
            cd.text((320, y + 180), s2, font=font(42), fill=(100, 116, 139, int(255 * a)), anchor="lm")
            f = Image.alpha_composite(f, card); d = ImageDraw.Draw(f)
        return f
    return fn

s_line = steps_scene("LINE無料査定", "スマホでかんたん", [
    ("1", "LINE友だち追加", "公式LINEを追加するだけ"),
    ("2", "車検証の写真を送信", "個人情報はマスクでOK"),
    ("3", "概算金額をご連絡", "オークション相場をもとに査定"),
], bg_blue, LINE_GREEN)

s_buy = steps_scene("高価買取", "alpha true shop が選ばれる理由", [
    ("¥", "相場に基づく公正価格", "業者オークションの最新相場"),
    ("即", "契約当日に即日振込", "ネット振込でその日のうちに"),
    ("◎", "他社比較 大歓迎", "出張査定も都内・近郊対応"),
], bg_dark, ORANGE)

def s_staff(t, D):
    f = bg_light.copy().convert("RGBA"); d = ImageDraw.Draw(f)
    a = ease(t / .6)
    ph = cover(staff, 640, 900, zoom=1.0 + 0.06 * t / D)
    mask = Image.new("L", ph.size, 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, 640, 900), 40, fill=int(255 * a))
    f.paste(ph, (220, 250 + int((1 - a) * 60)), mask)
    text(d, (W // 2, 1290), "車のお悩みを", 92, fill=DARK, t=(t - .5) / .5, stroke=0)
    text(d, (W // 2, 1420), "真摯に解決します", 104, fill=ORANGE, t=(t - .9) / .5, stroke=2, sc=ORANGE)
    for i, s in enumerate(["オークション代行", "パーツ取付"]):
        x0 = 110 + i * 440
        pill(d, (x0, 1580, x0 + 420, 1690), BLUE, t=(t - 1.5 - i * .3) / .4)
        text(d, (x0 + 210, 1635), s, 50, t=(t - 1.6 - i * .3) / .4, stroke=0, rise=0)
    text(d, (W // 2, 1780), "シートカバー・ドラレコ取付もお任せ", 44, fill=(100, 116, 139), t=(t - 2.3) / .5, stroke=0)
    return f

def s_cta(t, D):
    f = cover(roadster, W, H, zoom=1.25 - 0.08 * t / D).filter(ImageFilter.GaussianBlur(14)).convert("RGBA")
    f = Image.alpha_composite(f, Image.new("RGBA", (W, H), (15, 23, 42, 170))); d = ImageDraw.Draw(f)
    f.paste(logo_c.resize((260, 260)), (W // 2 - 130, 260), logo_m.resize((260, 260)))
    text(d, (W // 2, 700), "まずは", 80, t=(t - .2) / .5, stroke=0)
    text(d, (W // 2, 840), "LINEで無料査定", 118, t=(t - .5) / .5, stroke=8, sc=LINE_GREEN)
    text(d, (W // 2, 990), "個人情報不要・キャンセル自由", 52, fill=(251, 191, 36), t=(t - 1.0) / .5, stroke=0)
    pulse = 1 + 0.04 * math.sin(t * 6) if t > 1.6 else 1
    bw, bh = 760 * pulse, 170 * pulse
    pill(d, (W / 2 - bw / 2, 1180 - bh / 2, W / 2 + bw / 2, 1180 + bh / 2), LINE_GREEN, t=(t - 1.4) / .4, r=85)
    text(d, (W // 2, 1180), "LINE友だち追加 ▶", 66, t=(t - 1.6) / .4, stroke=0, rise=0)
    text(d, (W // 2, 1420), "alphatrue.shop", 78, t=(t - 2.0) / .5, stroke=0)
    text(d, (W // 2, 1530), "東京都八王子市南大沢", 48, fill=(203, 213, 225), t=(t - 2.3) / .5, stroke=0)
    text(d, (W // 2, 1600), "古物商 東京都公安委員会 第308762416476号", 34, fill=(148, 163, 184), t=(t - 2.5) / .5, stroke=0)
    return f

SCENES = [(3.0, s_intro), (4.5, s_question), (6.0, s_line), (6.0, s_buy), (5.0, s_staff), (6.0, s_cta)]
XF = 0.4  # crossfade seconds

ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                       "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                       "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-shortest",
                       "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                       "-c:a", "aac", "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
starts, acc = [], 0.0
for D, _ in SCENES: starts.append(acc); acc += D
total = acc
for fi in range(int(total * FPS)):
    T = fi / FPS
    k = max(i for i, s in enumerate(starts) if s <= T)
    D, fn = SCENES[k]; tl = T - starts[k]
    img = fn(tl, D).convert("RGB")
    if k + 1 < len(SCENES) and tl > D - XF:  # crossfade into next scene
        D2, fn2 = SCENES[k + 1]
        img = Image.blend(img, fn2(0.0, D2).convert("RGB"), (tl - (D - XF)) / XF)
    if T > total - 0.5:  # fade out
        img = Image.blend(img, Image.new("RGB", (W, H)), (T - (total - 0.5)) / 0.5)
    ff.stdin.write(img.tobytes())
    if fi % 150 == 0: print(f"{T:.1f}s / {total:.1f}s", flush=True)
ff.stdin.close(); ff.wait()
print("done", OUT)
