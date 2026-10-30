"""計画段階の絵コンテ v8.3「海からの高さ」（設計のための測量。ゲート1 用。28小節が正本）。元の素材のコマ（ぼかし済み）と、真上の地図・接眼の円のスケッチで作る。
秒は plan/editing_v8.md（v8.3）の写し。v5〜v7 の真横の図は使わない。
使い方：source .venv/bin/activate && python3 scripts/53_plan_storyboard_v8.py /mnt/project-files/level/storyboard_v8/
出力：storyboard_v8_p1〜p3.jpg と compare_v7.jpg（v7 との対応表）（素材から作った画像なので、リポジトリには入れない）。幅 1080 の縦長＝スマホで縦に読む。
日本の形は、主な岬・湾の公知の経緯度から手で打った仮の折れ線（地図の画像はなぞっていない）。本番は editing_v8.md §3.2。
"""
import pathlib, subprocess, sys, io, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = pathlib.Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
SRC = {k: ROOT / f"source/{v}.mp4" for k, v in {"S": "S_sueru", "K": "K_kansoku", "N": "N_nozoki"}.items()}
FONT = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
NAVY, ORANGE, INK, FAINT = "#1F3A5F", "#E8742A", "#14202E", "#B9C1CC"
PAPER, SEA, ROAD, BLOCK, GLOW, DARK = "#FBF8F2", "#DCE5EF", "#C9CED6", "#EEE9DE", "#FFD9BC", "#0E1A2B"
TW, TH, W = 520, 293, 1080

def font(px): return ImageFont.truetype(FONT, px)

def frame(src, t, crop=None, masks=()):
    vf = (f"crop={crop[2]}:{crop[3]}:{crop[0]}:{crop[1]}," if crop else "")
    png = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", f"{t:.3f}", "-i", str(SRC[src]),
                          "-frames:v", "1", "-vf", vf + "null", "-f", "image2", "-c:v", "png", "-"], capture_output=True, check=True).stdout
    im = Image.open(io.BytesIO(png)).convert("RGB")
    ox, oy = (crop[0], crop[1]) if crop else (0, 0)
    for x1, y1, x2, y2 in masks:
        box = (max(0, x1 - ox), max(0, y1 - oy), min(im.width, x2 - ox), min(im.height, y2 - oy))
        if box[2] > box[0] and box[3] > box[1]:
            im.paste(im.crop(box).filter(ImageFilter.GaussianBlur(10 if src != "S" else 5)), box[:2])
    return im.resize((TW, TH), Image.LANCZOS)

def label(d, xy, s, px=22, fill=NAVY, box=False, bg=NAVY):
    f = font(px)
    if box:
        x0, y0, x1, y1 = d.textbbox(xy, s, font=f); d.rectangle([x0 - 5, y0 - 4, x1 + 5, y1 + 4], fill=bg); fill = "white"
    d.text(xy, s, font=f, fill=fill)

def tag(im, s):
    d = ImageDraw.Draw(im); f = font(18); w = d.textlength(s, font=f)
    label(d, (TW - w - 10, TH - 28), s, 18, box=True, bg="#000000"); return im

def ov_lab(im, xy, s, to):
    d = ImageDraw.Draw(im); label(d, xy, s, 20, box=True); d.line([(xy[0] + 20, xy[1] + 28), to], fill=NAVY, width=2); return im

def sq(d, x, y, col, s=6, fill=True, w=2):
    d.rectangle([x - s, y - s, x + s, y + s], outline=col, width=w, fill=(col if fill else None))

# ---- ぼかし（editing_v8.md §5.2） ----
M1 = [(394, 30, 486, 72), (0, 232, 150, 292), (455, 262, 500, 282), (808, 312, 845, 340)]
M2 = [(535, 0, 648, 22), (0, 172, 70, 206), (100, 200, 312, 262), (605, 208, 685, 228)]
CYC = (330, 205, 400, 300)
MK = [(1015, 0, 1245, 100), (0, 465, 490, 575), (1680, 568, 1756, 614)]
HELMET_85 = (1090, 290, 1160, 350); TRUCK17 = (1125, 555, 1200, 625); SHOP_17 = (1150, 478, 1275, 515); HELMET_17 = (1245, 60, 1385, 118)
KW132 = (465, 60, 1455, 818); K115 = (125, 70, 1670, 939)
NV = [(1150, 215, 1360, 310)]   # N：奥の白い車のナンバー（窓の上の端）

# ---- 架空の町（自作。地名・方位・縮尺なし。K・S の道の形には似せない） ----
SITE = (318, 150)
def town(d, scale=1.0, cx=260, cy=146, fade=False):
    T = lambda x, y: (cx + (x - 260) * scale, cy + (y - 146) * scale)
    c = lambda col: FAINT if fade else col
    for bx, by, bw, bh in ((40, 30, 90, 50), (150, 30, 70, 60), (360, 20, 120, 50), (40, 190, 110, 70), (360, 190, 130, 60), (180, 200, 120, 60)):
        a, b = T(bx, by), T(bx + bw, by + bh); d.rectangle([a, b], fill=BLOCK)
    river = [T(x, 120 + 30 * math.sin(x / 70)) for x in range(-40, 580, 10)]
    d.line(river, fill=SEA if not fade else "#E6EBF1", width=max(2, int(12 * scale)))
    d.line([T(-40, 100), T(200, 110), T(560, 90)], fill=c(ROAD), width=max(2, int(9 * scale)))     # 太い道
    d.line([T(280, -40), T(300, 140), T(330, 330)], fill=c(ROAD), width=max(2, int(7 * scale)))
    d.line([T(-40, 260), T(560, 230)], fill=c(ROAD), width=max(2, int(6 * scale)))
    for x in (120, 430): d.line([T(x, -40), T(x + 20, 330)], fill=c("#DDE1E6"), width=max(1, int(3 * scale)))

def paper(sea=False):
    im = Image.new("RGB", (TW, TH), SEA if sea else PAPER); return im, ImageDraw.Draw(im)

# ---- 日本の形（仮の折れ線。公知の経緯度から手で打った。本番は Natural Earth か、同じ方法の自作 SVG） ----
HOK = [(141.9, 45.5), (142.9, 44.6), (144.3, 44.1), (145.3, 44.3), (145.2, 43.6), (145.8, 43.4), (144.4, 42.95), (143.3, 41.95), (142.1, 42.4),
       (141.4, 42.6), (140.95, 42.3), (141.2, 41.8), (140.7, 41.75), (140.1, 41.4), (139.95, 42.0), (140.4, 42.6), (140.4, 43.3), (141.3, 43.2),
       (141.7, 44.3), (141.6, 45.2)]
HON = [(140.9, 41.5), (141.45, 41.4), (141.5, 40.5), (142.0, 39.6), (141.6, 38.5), (141.0, 38.25), (141.0, 37.0), (140.6, 36.3), (140.85, 35.7),
       (140.4, 35.15), (139.85, 34.9), (139.95, 35.45), (139.75, 35.65), (139.65, 35.3), (139.7, 35.15), (139.15, 35.25), (138.85, 34.6),
       (138.75, 35.05), (138.2, 34.6), (137.3, 34.65), (136.85, 34.75), (136.85, 34.3), (136.4, 34.2), (135.8, 33.45), (135.1, 33.9),
       (135.15, 34.3), (135.45, 34.65), (134.7, 34.75), (133.9, 34.5), (132.5, 34.3), (131.3, 33.95), (130.9, 33.95), (131.0, 34.4), (131.6, 34.7),
       (132.6, 35.4), (133.4, 35.55), (134.4, 35.55), (135.3, 35.6), (136.0, 35.7), (136.0, 36.1), (136.7, 36.85), (136.75, 37.3), (137.3, 37.55),
       (137.0, 37.0), (137.3, 36.75), (138.2, 37.05), (138.9, 37.9), (139.55, 38.6), (139.8, 39.4), (140.0, 39.9), (139.7, 40.0), (140.0, 40.6),
       (140.3, 41.25), (140.65, 40.85), (140.9, 41.2)]
SHI = [(132.95, 32.75), (132.45, 33.3), (132.65, 33.85), (133.4, 34.2), (134.2, 34.3), (134.65, 34.05), (134.75, 33.85), (134.2, 33.25),
       (133.6, 33.5), (133.25, 33.4)]
KYU = [(130.9, 33.95), (131.55, 33.6), (132.0, 33.15), (131.7, 32.6), (131.45, 31.55), (131.1, 31.25), (130.7, 31.0), (130.2, 31.25), (130.2, 31.9),
       (130.6, 32.6), (130.2, 32.75), (129.85, 32.7), (129.65, 33.1), (129.85, 33.35), (130.35, 33.6)]
OKI = [(127.65, 26.1), (127.95, 26.4), (128.3, 26.85), (128.0, 26.65), (127.7, 26.4)]
TOKYO = (139.82, 35.52)
ROADS = [[TOKYO, (140.1, 36.4), (140.5, 37.8), (141.0, 38.4), (141.2, 39.7), (140.8, 40.8)],
         [TOKYO, (139.0, 35.3), (138.0, 34.9), (137.0, 35.1), (136.0, 35.0), (135.5, 34.7), (134.3, 34.7), (132.6, 34.45), (131.0, 34.0)],
         [(131.0, 34.0), (130.5, 33.6), (130.6, 32.8), (130.55, 31.7)],
         [TOKYO, (139.1, 36.4), (138.9, 37.8)],
         [(140.75, 41.8), (141.35, 43.0), (142.4, 43.8)]]
def jp(lon, lat, s=19.0, ox=-2300, oy=0):
    return (ox + (lon - 0) * s * 0.81 * 1.0 + 0, oy + (46.2 - lat) * s)

def japan(d, s=17.5, ox=None, oy=4, land=PAPER, line=NAVY):
    ox = ox if ox is not None else 150 - 128.5 * s * 0.81
    P = lambda p: (ox + p[0] * s * 0.81, oy + (46.2 - p[1]) * s)
    for poly in (HOK, HON, SHI, KYU):
        d.polygon([P(p) for p in poly], fill=land, outline=line)
        d.line([P(p) for p in poly + [poly[0]]], fill=line, width=2)
    d.rectangle([12, 196, 92, 270], outline=FAINT, width=2)                       # 沖縄は左下の枠に
    Q = lambda p: (52 + (p[0] - 127.95) * 40, 233 - (p[1] - 26.45) * 40)
    d.polygon([Q(p) for p in OKI], fill=land, outline=line)
    return P

import random
def nsq(d, x, y, s=6):            # 国の水準点：紺の □＋中心の点
    d.rectangle([x - s, y - s, x + s, y + s], outline=NAVY, width=2, fill=PAPER); r = max(1, s // 3); d.ellipse([x - r, y - r, x + r, y + r], fill=NAVY)

def osq(d, x, y, s=8, dotted=False):   # 現場の高さの目印：オレンジの □（点なし）
    if not dotted: d.rectangle([x - s, y - s, x + s, y + s], outline=ORANGE, width=3)
    else:
        for (a, b) in (((x - s, y - s), (x + s, y - s)), ((x + s, y - s), (x + s, y + s)), ((x + s, y + s), (x - s, y + s)), ((x - s, y + s), (x - s, y - s))):
            for k in range(0, 4, 2):
                t0, t1 = k / 4, (k + 1) / 4
                d.line([(a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0), (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1)], fill=ORANGE, width=3)

def sk_door8():
    im, d = paper()
    label(d, (150, 40), "測量部門のしごと", 26, fill=INK)
    for i, x in enumerate((80, 170, 260, 350, 440)):
        lit = i == 1
        d.ellipse([x - 32, 120, x + 32, 184], outline=(ORANGE if lit else NAVY), width=4 if lit else 2)
        if lit: sq(d, x, 152, ORANGE, 13, fill=False, w=4)
    return tag(im, "1.26 水準の□が灯る")

def ov_title8(im):
    band = Image.new("RGBA", (272, 120), (20, 32, 46, 150)); im.paste(band, (0, 8), band)
    d = ImageDraw.Draw(im); label(d, (16, 16), "水準測量", 44, fill="white"); label(d, (18, 72), "“高さの土台” をはかる", 21, fill="white")
    return im

def ov_q(im):
    d = ImageDraw.Draw(im)
    label(d, (14, 14), "止め絵（18.96–）。曲が止まり、現場の音だけ", 18, box=True)
    return im

# ---- B5 看板（v8.2：写真が縮む → 白い紙 → 日本の0 → 戻って現場の足もとに目印） ----
def sk_pull1():
    im, d = paper()
    k = frame("K", 7.82, KW132, MK + [HELMET_85]).resize((130, 73))
    im.paste(k, (195, 100)); d.rectangle([195, 100, 325, 173], outline=NAVY, width=2)
    for a_, b_ in (((20, 20), (195, 100)), ((500, 20), (325, 100)), ((20, 275), (195, 173)), ((500, 275), (325, 173))):
        d.line([a_, b_], fill=FAINT, width=1)
    label(d, (14, 14), "写真が縮む → 白い紙 0.3秒", 18, box=True)
    label(d, (14, 262), "どこから引いたか見せない（地方の絵は出さない）", 15, fill=INK)
    return tag(im, "20.22–21.49")

def zero(d, x, y, r=17, px=26):
    d.ellipse([x - r, y - r, x + r, y + r], fill=NAVY); w = d.textlength("0", font=font(px)); label(d, (x - w / 2, y - px * 0.55), "0", px, fill="white")

def sk_pull2():
    im, d = paper(sea=True)
    P = japan(d)
    x, y = P(TOKYO); zero(d, x, y)
    label(d, (x - 12, y + 30), "東京湾の平均の海面", 17, box=True)
    label(d, (14, 14), "日本の形 →「ゼロ」で東京湾に「0」", 18, box=True)
    label(d, (236, 262), "海は面の色だけ", 15, fill=INK)
    return tag(im, "21.49–26.54")

def sk_whitecut():
    im, d = paper()
    label(d, (14, 14), "26.54 白い紙で切る（0.32秒）", 18, box=True)
    label(d, (60, 110), "日本の形から現場へは寄らない", 22, fill=INK)
    label(d, (60, 146), "（線・点の移動でもつながない）", 18, fill=INK)
    label(d, (14, 262), "日本の0と現場の目印は別の話", 15, fill=INK)
    return tag(im, "26.54–26.86")

def sk_sitemark():
    im = frame("K", 7.82, KW132, MK + [HELMET_85]); d = ImageDraw.Draw(im)
    fx, fy = 106, 222                                   # 遠くの標尺手の足もとの横（体には重ねない）
    osq(d, fx, fy, 9); d.rectangle([fx - 15, fy - 15, fx + 15, fy + 15], outline=GLOW, width=2)
    label(d, (fx - 20, fy + 16), "高さの目印", 20, box=True, bg=ORANGE)
    label(d, (14, 14), "現場の写真（止め絵）、足もとにオレンジの □", 18, box=True)
    return tag(im, "26.86–32.86 止め絵")

def sk_eyepiece():
    im = Image.new("RGB", (TW, TH), DARK); d = ImageDraw.Draw(im)
    cx, cy, r = 260, 148, 118
    m = Image.new("L", (TW, TH), 0); ImageDraw.Draw(m).ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    inner = Image.new("RGB", (TW, TH), "#F2F2EE"); di = ImageDraw.Draw(inner)
    sx = cx                                                              # 標尺のまん中が縦の線に来る
    di.rectangle([sx - 48, 0, sx + 48, TH], fill="white")
    for i, y in enumerate(range(10, TH, 36)):                           # E の字の目盛り（数字は描かない）
        col = "#C8322B" if (i // 3) % 2 == 0 else "#222222"
        di.rectangle([sx - 40, y, sx - 8, y + 6], fill=col); di.rectangle([sx - 40, y + 12, sx - 22, y + 18], fill=col); di.rectangle([sx - 40, y + 24, sx - 8, y + 30], fill=col)
        di.rectangle([sx - 40, y, sx - 34, y + 30], fill=col)
    band = Image.new("RGBA", (96, 8), (255, 200, 120, 120)); inner.paste(band, (sx - 48, cy - 4), band)
    di.line([(cx - r, cy), (cx + r, cy)], fill="#111111", width=2); di.line([(cx, cy - r), (cx, cy + r)], fill="#111111", width=2)
    for dy in (-30, 30): di.line([(cx - 26, cy + dy), (cx + 26, cy + dy)], fill="#111111", width=1)
    im.paste(inner, (0, 0), m); d.ellipse([cx - r, cy - r, cx + r, cy + r], outline="#6B83A6", width=4)
    label(d, (14, 14), "接眼の円：標尺が横から来て縦の線で止まる", 18, box=True)
    label(d, (392, 112), "41.71「読んで」", 16, fill="white"); label(d, (392, 136), "横の線のところに", 16, fill="white"); label(d, (392, 158), "うすい帯（8px）", 16, fill="white")
    d.line([(150, 70), (180, 70)], fill="#9FB3CC", width=2); d.polygon([(150, 64), (150, 76), (140, 70)], fill="#9FB3CC")
    return tag(im, "40.45–42.98")

PTS = [(70, 104), (110, 106), (150, 108), (190, 110), (230, 108), (270, 104), (300, 100), (330, 96)]
def sk_design1():
    im, d = paper(); town(d, fade=True)
    osq(d, 40, 112, 9)
    for i, (x, y) in enumerate(PTS): d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=NAVY if i < 6 else FAINT)
    label(d, (14, 14), "紙の町：点が右へ灯り（行き）、目印へ戻る（帰り）", 18, box=True)
    d.line([(320, 122), (60, 126)], fill="#9FB3CC", width=2); d.polygon([(60, 120), (60, 132), (48, 126)], fill="#9FB3CC")
    d.rectangle([28, 100, 52, 124], outline=GLOW, width=3)
    label(d, (14, 262), "点に数字は付けない。戻った所で □ に小さな輪", 15, fill=INK)
    return tag(im, "50.56–52.46")

def sk_design2():
    im, d = paper(); town(d, fade=True)
    osq(d, 40, 112, 9)
    for x, y in PTS: d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=NAVY)
    sx0 = 300; d.rectangle([sx0, 40, TW - 8, 250], fill="#EAF1F8", outline="#9FB3CC", width=2)
    for gx in range(sx0, TW - 8, 18): d.line([(gx, 40), (gx, 250)], fill="#D6E2EE", width=1)
    for gy in range(40, 250, 18): d.line([(sx0, gy), (TW - 8, gy)], fill="#D6E2EE", width=1)
    road = [(sx0 + 10, 210), (360, 175), (430, 130), (TW - 18, 95)]
    for off, col, w in ((-14, NAVY, 2), (14, NAVY, 2)): d.line([(x, y + off) for x, y in road], fill=col, width=w)
    for (x1, y1), (x2, y2) in zip(road, road[1:]):
        L = math.dist((x1, y1), (x2, y2)); t = 0
        while t < L:
            t2 = min(L, t + 10); d.line([(x1 + (x2 - x1) * t / L, y1 + (y2 - y1) * t / L), (x1 + (x2 - x1) * t2 / L, y1 + (y2 - y1) * t2 / L)], fill=ORANGE, width=2); t += 16
    for (px, py), (tx, ty) in zip([PTS[0], PTS[3], PTS[5]], road[:3]):
        arc = [(px + (tx - px) * t, py + (ty - py) * t - 45 * math.sin(math.pi * t)) for t in [i / 20 for i in range(21)]]
        d.line(arc, fill=NAVY, width=2)
    label(d, (sx0 + 12, 48), "設計", 24, box=True)
    label(d, (14, 14), "点の高さが図面へ → 道路の線", 18, box=True)
    label(d, (14, 262), "図面は真上の道の線だけ（手・数字なし）", 15, fill=INK)
    return tag(im, "52.46–55.62")

def stick(d, x, y, col=INK, staff=False):
    d.ellipse([x - 5, y - 26, x + 5, y - 16], outline=col, width=2); d.line([(x, y - 16), (x, y)], fill=col, width=2)
    d.line([(x, y), (x - 6, y + 12)], fill=col, width=2); d.line([(x, y), (x + 6, y + 12)], fill=col, width=2)
    if staff: d.line([(x + 9, y - 34), (x + 9, y + 12)], fill="#C8322B", width=3)

def sk_child():
    im, d = paper()
    rnd = random.Random(3)
    def wob(pts, col, w=4):
        q = [(x + rnd.uniform(-1.5, 1.5), y + rnd.uniform(-1.5, 1.5)) for x, y in pts]; d.line(q + [q[0]], fill=col, width=w, joint="curve")
    s_, ox, oy = 9.5, 30 - 129.5 * 9.5 * 0.81, 40
    P = lambda p: (ox + p[0] * s_ * 0.81, oy + (46.2 - p[1]) * s_)
    for poly in (HOK, HON, SHI, KYU): wob([P(p) for p in poly], NAVY, 3)
    zx, zy = P(TOKYO); zero(d, zx, zy, 9, 13)
    d.line([(310, 160), (400, 150), (500, 140)], fill="#9AA5B4", width=6)
    osq(d, 360, 142, 10)
    stick(d, 390, 136, staff=True)
    stick(d, 470, 124); d.line([(462, 106), (476, 106)], fill=INK, width=3)
    label(d, (14, 14), "終わりの画：子どもが描く絵（0.6秒で並ぶ）", 18, box=True)
    label(d, (300, 176), "左右に離す・線でつながない", 14, fill=INK)
    label(d, (60, 222), "“高さの土台” をはかる", 26)
    return tag(im, "68.26–70.78")

def ov_level(im):
    return ov_lab(im, (330, 30), "レベル", (300, 118))

# (拍, 小節・秒, [コマ], ナレ, 画・文字, 音, 目的)
ROWS = [
    ("B1 章扉", "1小節　0.0–2.5", [sk_door8], "N1a 0.30「測量部門の仕事のひとつ、」", "章扉（共通）。水準のアイコン（□）だけ灯る", "章扉の灯り", "部門の中の1作業"),
    ("B2 据える", "2–3小節　2.5–7.6", [lambda: tag(frame("S", 49.6, (70, 82, 707, 398), M1), "S 48.58– 実時間"), lambda: tag(ov_title8(frame("S", 53.3, (70, 82, 707, 398), M1)), "6.95 載る＝題")],
     "N1b 7.25「水準測量です。」", "ケースを開ける → 持ち上げる → 6.95 に載る。題とサブ「“高さの土台” をはかる」", "載る音（実音）", "人の手で始まる"),
    ("B3 はかる", "4–5小節　7.6–12.6", [lambda: tag(frame("S", 66.0, (170, 40, 678, 381), M1), "S 56–74 4.75倍"), lambda: tag(frame("N", 2.6, (600, 180, 1200, 675), NV), "N 2.0–3.3")],
     "N2 8.99「道ばたで、高さを、ミリまではかります。」（〜12.41）", "整準（気泡をのぞく）→ 目を当てる寄り。文字なし（「レベル」は B11 へ）", "道の環境音", "何をしているか"),
    ("B4 問い", "6–8小節　12.6–20.2", [lambda: tag(frame("K", 3.0, None, MK), "K 1.5 全画面から"), lambda: tag(ov_q(ov_lab(frame("K", 7.82, KW132, MK + [HELMET_85]), (40, 50), "標尺", (93, 120))), "K 7.82 で止める")],
     "N3 13.38「でも、高さって、どこからはかるのでしょう。」（〜17.18）", "歩いて来てかがむ。「標尺」14.50–16.50（「どこから」の前）。18.96 に止まる", "17.70 に曲が止まる → 3 秒、現場の音だけ（考える間）", "問いを置く"),
    ("B5 看板 1/2", "9–11小節　20.2–25.9", [sk_pull1, sk_pull2],
     "N4 21.61「日本の高さの0は、東京湾の海の高さ。」（「ゼロ」22.75）", "一番強い頭で写真が縮む → 白い紙 0.3秒 → 日本の形 → 22.75「0」→ 補足「東京湾の平均の海面」23.21–26.50", "9小節の頭で引き始め。0 で C6（−3 dB）", "なるほど：高さには0がいる。日本の0は海"),
    ("B5 看板 2/2", "11–13小節　26.5–32.9", [sk_whitecut, sk_sitemark],
     "N5 25.89「道路を設計する場所では、近くに高さの目印を決めて、そこを高さの基準にします。」（〜32.92）", "26.54 白い紙で切る → 26.86 現場の写真（止め絵、1.00→1.08 に寄る）→ 28.44 足もとにオレンジの □ と「高さの目印」→ 30.64「そこを」で □ に輪", "□ で E6", "現場では、近くの目印が高さの基準（日本の0とは別の話）"),
    ("B6 はかる人", "14–15小節　32.9–37.9", [lambda: tag(frame("S", 169.2, None, M2), "S 166.56–171.62 実時間")],
     "N6 33.26「その目印から、高さを、次々につないでいきます。」（〜37.44）", "ものさしを持った人が右手前からあらわれ、35.5 に機械の横を通って次の点へ", "足音・道の音", "目印から、高さを次々につなぐ"),
    ("B7 読む", "16–17小節　37.9–43.0", [lambda: tag(frame("N", 4.5, (600, 180, 1200, 675), NV), "N 3.3–5.83"), sk_eyepiece],
     "N7 39.25「遠くのものさしを、目で読んで、」", "のぞいて指でつまみを回す → 40.45（曲のつなぎ目）接眼の円 → 41.0–41.5 ピント → 41.71 横の線にうすい帯（標尺は動かさない、数字なし）", "N の実音 → 曲だけ", "目で読む仕事"),
    ("B8 書く", "18小節　43.0–45.5", [lambda: tag(frame("K", 17.0, (720, 0, 1200, 675), MK + [TRUCK17, SHOP_17, HELMET_17]), "K 16.2–18.73 1.6倍")],
     "N8 43.37「手で書きとめる。」", "立って黄色い手帳に書く手（N7 からカットで続く）", "ペンの音", "読んだ数字は人の手で残る"),
    ("B9 確かめる", "19–20小節　45.5–50.6", [lambda: tag(frame("S", 173.5, None, M2 + [CYC]), "S 172.2–174.73 全画面"), lambda: tag(frame("S", 178.0, (170, 40, 678, 381), M2 + [CYC]), "S 177.0– 窓 1.25倍")],
     "N9 45.90「行きと帰りではかって、ずれがないか確かめます。」", "遠くに着いた標尺手 → 寄りの大きさで、観測者がのぞき 179.2 から歩き出す（実写だけ）", "S の実音", "ていねいさ"),
    ("B10 設計へ", "21–22小節　50.6–55.6", [sk_design1, sk_design2],
     "N10 50.96「はかった高さをもとに、道路の図面がかかれます。」（〜55.14）", "紙の町で点が目印から右へ（行き）→ 目印へうすく戻る（帰り）→ 図面の紙 → 点から弧が3本 → 54.35 道路の線。文字「設計」53.32–", "C・E・G（54.35、小）", "はかった高さで、道路の図面ができる"),
    ("B11 人", "23–24小節　55.6–60.7", [lambda: tag(ov_level(frame("S", 81.6, (170, 40, 678, 381), M1 + [(500, 258, 552, 296)])), "S 81.0–83.53 窓"), lambda: tag(frame("N", 8.2, (600, 200, 1200, 675), NV), "N 5.9–8.43 顔")],
     "声なし（実音 +3 dB）", "人のいない機械と流れる車に「レベル」→ 58.14 のぞく寄りの顔で終える（K の引きは使わない）", "実音 +3 dB", "まちのすぐ横で。寄りの顔で終える"),
    ("B12 締め", "25–28小節　60.7–70.8", [lambda: tag(frame("K", 12.0, K115, MK + [HELMET_85]), "K 8.53–16.12 等速、引く"), sk_child],
     "N12 61.07「設計が使う、“高さの土台”をはかる。それが、水準測量です。」（〜66.01）", "N の顔から、最後の一打で二人の引き。文字「“高さの土台” をはかる」61.91–。68.26 子どもの絵（日本の0と現場の目印を離す）→ 70.15 オレンジの □ だけ縮んでアイコン → 黒", "最後の和音のばし。G6（小）", "誇りと余韻。中心の絵をもう一度"),
]

PAD, FS, LH = 20, 26, 36
FIELDS = [("ナレ", 3), ("画・文字", 4), ("音", 5), ("目的", 6)]
def wrap(s, f, width, d):
    lines, cur = [], ""
    for ch in s:
        if d.textlength(cur + ch, font=f) > width and ch not in "。、）」』":
            lines.append(cur); cur = ch
        else:
            cur += ch
    return lines + [cur]

def card(row, d0):
    f = font(FS); lab = font(22)
    blocks = [(name, wrap(row[k], f, W - 2 * PAD - 110, d0)) for name, k in FIELDS]
    h = 52 + TH + 14 + sum(len(b) * LH + 10 for _, b in blocks) + 18
    im = Image.new("RGB", (W, h), "white"); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 46], fill="#2C4A3E")                       # v8 は深い緑の帯（v5〜v7 の紺の帯と分ける）
    d.text((PAD, 8), row[0], font=font(30), fill="white"); d.text((330, 12), row[1], font=font(26), fill="white")
    imgs = [g() for g in row[2]]
    if len(imgs) == 1: im.paste(imgs[0], ((W - TW) // 2, 52))
    elif len(imgs) == 3:
        for i, g in enumerate(imgs): im.paste(g.resize((340, 192), Image.LANCZOS), (10 + i * 350, 52 + (TH - 192) // 2))
    else:
        for i, g in enumerate(imgs[:2]): im.paste(g, (PAD // 2 + i * (TW + PAD), 52))
    y = 52 + TH + 14
    for name, lines in blocks:
        d.rectangle([PAD, y + 2, PAD + 96, y + 32], fill="#E7EEEA"); d.text((PAD + 8, y + 5), name, font=lab, fill="#2C4A3E")
        for k, line in enumerate(lines): d.text((PAD + 110, y + k * LH), line, font=f, fill=INK)
        y += len(lines) * LH + 10
    d.line([(0, h - 4), (W, h - 4)], fill="#BBBBBB", width=3)
    return im

def page(rows, n, of):
    tmp = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    cards = [card(r, tmp) for r in rows]
    H = 120 + sum(c.height for c in cards)
    im = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(im)
    d.text((PAD, 14), f"水準測量パート 絵コンテ v8.3「海からの高さ」　{n}/{of}", font=font(34), fill=INK)
    d.text((PAD, 62), "28小節・70.8秒・曲 V6b（8小節で止め）。コマは元の素材（ぼかし済み）、", font=font(22), fill="#555")
    d.text((PAD, 90), "図は真上の地図・接眼の円・子どもの絵のスケッチ（日本の形は仮）。秒は完成尺。社外に出さない。", font=font(22), fill="#555")
    y = 120
    for c in cards: im.paste(c, (0, y)); y += c.height
    return im

groups = [ROWS[0:4], ROWS[4:8], ROWS[8:13]]
for n, rows in enumerate(groups, 1):
    p = OUT / f"storyboard_v8_p{n}.jpg"; page(rows, n, len(groups)).save(p, quality=88); print(p)

# ---- ゲートの1枚目：v7（v7.4）との対応表。変えた画を先に、同じ画はその理由と ----
CMP = [
    ("変", "尺と曲", "32小節・80.9秒（V6d）", "28小節・70.8秒（V6b）。32小節は別案"),
    ("変", "芯の考え", "高さのバトンを、となりへつなぐ", "設計のための測量。高さには0がいる（日本の0は海）、現場では近くの目印が基準"),
    ("変", "B4 ナレ", "仲間がひとり、ものさしを…", "問い「高さって、どこからはかるのでしょう」"),
    ("変", "B5 看板", "真横の図：目線・のぼって・わたって・おりる", "写真が縮む → 白い紙 → 日本の形と東京湾の0 → 白い紙で切って現場の足もとに □"),
    ("変", "B7", "真横の図「となりへ、となりへ」", "N の顔 → 描いた接眼の円（横の線を読む）"),
    ("変", "B9", "S 177 全画面 → 図（帰りの線）", "実写だけ：S 172 全画面 → S 177 を 1.25倍の窓"),
    ("変", "B10", "真横の図「新しい道」", "紙の町：点の行きと帰り → 図面 → 道路の線（設計へ）"),
    ("変", "B11", "N の顔（長い）→ S 172 → S 81", "声なし。S 81「レベル」→ N の顔で終える"),
    ("変", "終わりの画", "紺の □ が縮んでアイコン", "子どもが描く絵（日本の0と現場の目印を離す）→ □ だけ縮む"),
    ("変", "締め", "“高さの目印” をつくる", "設計が使う “高さの土台” をはかる"),
    ("変", "「レベル」", "B6 の S の機械", "B11 の S 81 の機械（人のいない画）"),
    ("同", "B1 章扉", "共通の型", "同じ（シリーズの型）"),
    ("同", "B2 据える", "S 48.58–53.63、題", "同じ（素材）"),
    ("同", "B3 はかる", "S 56–74 4.75倍 → N 2.0", "同じ（素材）"),
    ("同", "B4 の画", "K 1.5–7.82、寄り、止め絵、8小節の止め", "同じ（素材）。「標尺」は 14.5 に早めた"),
    ("同", "B6 歩く", "S 165.67– 標尺手が歩く", "ほぼ同じ（S 166.56–、素材）"),
    ("同", "B8 書く", "K 16.2–21.26", "同じ手（K 16.2–18.73、1小節に）"),
    ("同", "B12 締め", "K 8.53–16.12 の引き", "同じ（素材）"),
]
def compare():
    f, fb = font(22), font(24)
    cols = [(PAD, 60), (PAD + 66, 150), (PAD + 222, 350), (PAD + 578, W - PAD - 578 - PAD)]
    tmp = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    rows = []
    for r in CMP:
        cells = [wrap(r[i], f, cols[i][1] - 12, tmp) for i in range(4)]
        rows.append((r, cells, max(len(c) for c in cells) * 32 + 14))
    H = 230 + 44 + sum(h for _, _, h in rows) + 30
    im = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(im)
    d.text((PAD, 16), "v7 との対応表（v7.4 → v8.3）", font=font(36), fill=INK)
    d.text((PAD, 70), "変えた画を先に。同じ画が残るのは、素材が約40秒（S・K・N の3本）で、", font=font(22), fill="#555")
    d.text((PAD, 100), "人の仕事が映る所がそこしかないため。図・ナレ・終わりの画・B9〜B11 の並びは変えた。", font=font(22), fill="#555")
    n_ch = sum(1 for r in CMP if r[0] == "変")
    d.text((PAD, 140), f"変えた {n_ch} か所／同じ {len(CMP) - n_ch} か所（同じ所は素材の都合）", font=fb, fill=ORANGE)
    d.text((PAD, 180), "絵コンテは p2（看板）から見てください。社外に出さない。", font=font(22), fill="#555")
    y = 230
    d.rectangle([0, y, W, y + 44], fill="#2C4A3E")
    for (x, _), h in zip(cols, ("", "どこ", "v7.4", "v8.3")): d.text((x + 6, y + 8), h, font=fb, fill="white")
    y += 44
    for r, cells, h in rows:
        ch = r[0] == "変"
        d.rectangle([0, y, W, y + h], fill=("#FFF4EC" if ch else "#F3F4F6"))
        d.rectangle([cols[0][0], y + 8, cols[0][0] + 52, y + 40], fill=(ORANGE if ch else "#8A94A3"))
        d.text((cols[0][0] + 4, y + 10), "変えた" if ch else "同じ", font=font(16 if ch else 20), fill="white")
        for i in (1, 2, 3):
            for k, line in enumerate(cells[i]): d.text((cols[i][0] + 6, y + 8 + k * 32), line, font=(fb if i == 1 else f), fill=INK if i != 2 else "#555")
        d.line([(0, y + h), (W, y + h)], fill="#DDDDDD", width=1); y += h
    p = OUT / "compare_v7.jpg"; im.save(p, quality=90); print(p)
compare()
