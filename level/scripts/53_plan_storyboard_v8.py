"""計画段階の絵コンテ v8「海からの高さ」（ゲート1 用）。元の素材のコマ（ぼかし済み）と、真上の地図・接眼の円のスケッチで作る。
秒は plan/editing_v8.md の写し。v5〜v7 の真横の図は使わない。
使い方：source .venv/bin/activate && python3 scripts/53_plan_storyboard_v8.py /mnt/project-files/level/storyboard_v8/
出力：storyboard_v8_p1〜p3.jpg（素材から作った画像なので、リポジトリには入れない）。幅 1080 の縦長＝スマホで縦に読む。
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
    d = ImageDraw.Draw(im); label(d, (16, 16), "水準測量", 44, fill="white"); label(d, (18, 72), "“高さの目印” をつくる", 21, fill="white")
    return im

def ov_q(im):
    d = ImageDraw.Draw(im)
    label(d, (14, 14), "止め絵（18.96–）。曲が止まり、現場の音だけ", 18, box=True)
    return im

# ---- B5 看板：引く（4コマ） ----
def sk_pull1():
    im, d = paper(); town(d)
    k = frame("K", 7.82, KW132, MK + [HELMET_85]).resize((156, 88))
    im.paste(k, (SITE[0] - 78, SITE[1] - 44)); d.rectangle([SITE[0] - 78, SITE[1] - 44, SITE[0] + 78, SITE[1] + 44], outline=NAVY, width=2)
    for a, b in (((40, 40), (SITE[0] - 78, SITE[1] - 44)), ((480, 40), (SITE[0] + 78, SITE[1] - 44)), ((40, 260), (SITE[0] - 78, SITE[1] + 44))):
        d.line([a, b], fill=FAINT, width=1)
    label(d, (14, 14), "引く1：写真が縮みながら、紙の町の線画に", 18, box=True)
    label(d, (14, 262), "架空の町（地名・方位なし）", 15, fill=INK)
    return tag(im, "20.22–21.49")

def sk_pull2():
    im, d = paper(sea=True)
    P = japan(d)
    x, y = P(TOKYO)
    for r, a in ((26, 70), (40, 30)): d.ellipse([x - r, y - r, x + r, y + r], outline="#9FB3CC", width=2)
    d.ellipse([x - 15, y - 15, x + 15, y + 15], fill=NAVY); label(d, (x - 7, y - 15), "0", 24, fill="white")
    label(d, (14, 14), "引く2・3：町 → 地方 → 日本。東京湾に「0」", 18, box=True)
    label(d, (330, 200), "「答えは、海」", 22, fill=NAVY)
    label(d, (330, 230), "（海はうすい紺の面だけ）", 14, fill=INK)
    return tag(im, "21.49–27.8")

def sk_dots():
    im, d = paper(sea=True)
    P = japan(d)
    for road in ROADS:
        pts = [P(p) for p in road]; d.line(pts, fill="#C5CEDA", width=1)
        acc = 0
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            L = math.dist((x1, y1), (x2, y2)); t = (11 - acc) if acc else 6
            while t < L:
                sq(d, x1 + (x2 - x1) * t / L, y1 + (y2 - y1) * t / L, NAVY, 3); t += 11
            acc = (acc + L) % 11
    x, y = P(TOKYO); d.ellipse([x - 9, y - 9, x + 9, y + 9], fill=NAVY); label(d, (x - 4, y - 9), "0", 14, fill="white")
    label(d, (x + 40, y - 6), "水準点", 20, box=True)
    label(d, (14, 14), "0 から、道にそって □ が点々と灯る", 18, box=True)
    label(d, (400, 236), "イメージ", 16, fill=INK)
    return tag(im, "27.81–30.34")

def sk_back():
    im, d = paper(); town(d)
    marks = [(70, 102), (200, 110), (300, 60)]
    for x, y in marks: sq(d, x, y, NAVY, 6)
    d.ellipse([292, 52, 308, 68], outline=GLOW, width=4)
    d.line([(300, 68), (300, 120), (305, 140), (SITE[0], SITE[1] - 8)], fill=NAVY, width=4)
    sq(d, SITE[0], SITE[1], ORANGE, 8, fill=False, w=3)
    label(d, (14, 14), "町へ戻る → 近い □ から現場へ紺の線", 18, box=True)
    label(d, (SITE[0] + 14, SITE[1] - 10), "新しい目印（待つ）", 16, fill=ORANGE)
    label(d, (14, 262), "現場の点は架空の町の中（実在の場所ではない）", 15, fill=INK)
    return tag(im, "30.34–32.86")

def sk_eyepiece():
    im = Image.new("RGB", (TW, TH), DARK); d = ImageDraw.Draw(im)
    cx, cy, r = 260, 148, 118
    m = Image.new("L", (TW, TH), 0); ImageDraw.Draw(m).ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    inner = Image.new("RGB", (TW, TH), "#F2F2EE"); di = ImageDraw.Draw(inner)
    di.rectangle([cx - 48, 0, cx + 48, TH], fill="white")
    for i, y in enumerate(range(10, TH, 36)):                           # E の字の目盛り（数字は描かない）
        col = "#C8322B" if (i // 3) % 2 == 0 else "#222222"
        di.rectangle([cx - 40, y, cx - 8, y + 6], fill=col); di.rectangle([cx - 40, y + 12, cx - 22, y + 18], fill=col); di.rectangle([cx - 40, y + 24, cx - 8, y + 30], fill=col)
        di.rectangle([cx - 40, y, cx - 34, y + 30], fill=col)
    di.line([(cx - r, cy), (cx + r, cy)], fill="#111111", width=2); di.line([(cx, cy - r), (cx, cy + r)], fill="#111111", width=2)
    for dy in (-30, 30): di.line([(cx - 26, cy + dy), (cx + 26, cy + dy)], fill="#111111", width=1)
    im.paste(inner, (0, 0), m); d.ellipse([cx - r, cy - r, cx + r, cy + r], outline="#6B83A6", width=4)
    label(d, (14, 14), "描いた接眼の円：十字線が目盛りに合う", 18, box=True)
    label(d, (392, 120), "41.71", 18, fill="white"); label(d, (392, 146), "「読んで」", 18, fill="white")
    return tag(im, "40.45–42.98")

ICONS = [("地形", 110), ("路線", 260), ("工事", 410)]
def sk_link():
    im, d = paper(); town(d, fade=True)
    d.rectangle([0, 0, TW, 92], fill=PAPER); d.line([(0, 92), (TW, 92)], fill=FAINT, width=2)
    for name, x in ICONS:
        d.ellipse([x - 22, 22, x + 22, 66], outline=NAVY, width=2); label(d, (x + 26, 34), name, 18, fill=INK)
    for name, x in ICONS:
        pts = [(SITE[0] + (x - SITE[0]) * t, SITE[1] - 14 + (66 - SITE[1] + 14) * t - 50 * math.sin(math.pi * t)) for t in [i / 20 for i in range(21)]]
        d.line(pts, fill=NAVY, width=2)
    d.line([(300, 68), (300, 120), (305, 140), (SITE[0], SITE[1] - 8)], fill=NAVY, width=3)
    sq(d, SITE[0], SITE[1], NAVY, 9, fill=False, w=3); d.ellipse([SITE[0] - 16, SITE[1] - 16, SITE[0] + 16, SITE[1] + 16], outline=GLOW, width=3)
    label(d, (SITE[0] + 18, SITE[1] + 8), "高さの目印", 20, box=True)
    label(d, (14, 262), "□ がオレンジ→紺（54.98）→ アイコンへ線", 15, fill=INK)
    return tag(im, "53.09–60.67")

def sk_end8():
    im, d = paper()
    sq(d, 160, 150, NAVY, 40, fill=False, w=6)
    d.line([(230, 150), (330, 150)], fill=INK, width=3); d.polygon([(330, 140), (330, 160), (348, 150)], fill=INK)
    d.ellipse([370, 115, 440, 185], outline=ORANGE, width=5); sq(d, 405, 150, ORANGE, 13, fill=False, w=4)
    label(d, (14, 14), "終わりの画：紺の □ が縮んで章扉のアイコンへ", 18, box=True)
    label(d, (36, 236), "“海からの高さ” の目印をつくる", 26)
    return tag(im, "78.37–80.39")

# (拍, 小節・秒, [コマ], ナレ, 画・文字, 音, 目的)
ROWS = [
    ("B1 章扉", "1小節　0.0–2.5", [sk_door8], "N1a 0.30「測量部門の仕事のひとつ、」", "章扉（共通）。水準のアイコン（□）だけ灯る", "章扉の灯り", "部門の中の1作業"),
    ("B2 据える", "2–3小節　2.5–7.6", [lambda: tag(frame("S", 49.6, (70, 82, 707, 398), M1), "S 48.58– 実時間"), lambda: tag(ov_title8(frame("S", 53.3, (70, 82, 707, 398), M1)), "6.95 載る＝題")],
     "N1b 7.25「水準測量です。」", "ケースを開ける → 持ち上げる → 6.95 に載る。題とサブ「“高さの目印” をつくる」", "載る音（実音）", "人の手で始まる"),
    ("B3 はかる", "4–5小節　7.6–12.6", [lambda: tag(frame("S", 66.0, (170, 40, 678, 381), M1), "S 56–74 4.75倍"), lambda: tag(ov_lab(frame("N", 2.6, (600, 180, 1200, 675), NV), (330, 40), "レベル", (360, 120)), "N 2.0–3.3")],
     "N2 8.99「道ばたで、地面の高さを、ミリまではかります。」", "整準（気泡をのぞく）→ 目を当てる寄り。ラベル「レベル」11.40–", "道の環境音", "何をしているか"),
    ("B4 問い", "6–8小節　12.6–20.2", [lambda: tag(frame("K", 3.0, None, MK), "K 1.5 全画面から"), lambda: tag(ov_q(ov_lab(frame("K", 7.82, KW132, MK + [HELMET_85]), (40, 50), "標尺", (93, 120))), "K 7.82 で止める")],
     "N3 13.38「でも、高さって、どこからはかるのでしょう。」（〜17.18）", "歩いて来てかがむ。15.17 に「標尺」。18.96 に止まる", "17.70 に曲が止まる → 3 秒、現場の音だけ（考える間）", "問いを置く"),
    ("B5 看板 1/2", "9–12小節　20.2–27.8", [sk_pull1, sk_pull2],
     "N4 23.25「答えは、海。日本の高さの0は、海の高さです。」（「海」24.01）", "一番強い頭で、写真が縮みながら紙の町に → 地方 → 日本の形（3段、各1.26秒）→ 24.02 東京湾に「0」が灯る", "9小節の頭で引き始め。0 で C6", "なるほど：高さの0は海"),
    ("B5 看板 2/2", "12–13小節　27.8–32.9", [sk_dots, sk_back],
     "N5 27.83「海は遠いので、道ばたに、高さの目印があります。」　N6 32.41「その目印から、…」", "0 から道にそって □ が点々（「イメージ」）、「水準点」→ 30.34 町へ戻る → 近い □ から現場へ紺の線 → 32.23 オレンジの □ が待つ", "現場の □ で E6（32.23）", "目印は道ばたに。そこから現場へ"),
    ("B6 現場へ", "14–15小節　32.9–37.9", [lambda: tag(frame("S", 169.2, None, M2), "S 166.56–171.62 実時間")],
     "N6「…現場まで、高さをつないでいきます。」（〜36.78。「つないで」35.26）", "標尺手が右手前からあらわれ、35.5 に機械の横を通って奥へ", "足音・道の音", "人の仕事に戻る"),
    ("B7 読む", "16–17小節　37.9–43.0", [lambda: tag(frame("N", 4.5, (600, 180, 1200, 675), NV), "N 3.3–5.83"), sk_eyepiece],
     "N7 39.25「遠くのものさしを、目で読んで、」", "のぞいたまま、指でピントのつまみを回す → 40.45 描いた接眼の円 → 41.71「読んで」で十字線が目盛りに合う（数字は描かない）", "N の実音 → 曲だけ（十字線に音なし）", "目で読む仕事"),
    ("B8 書く", "18–19小節　43.0–48.0", [lambda: tag(frame("K", 17.0, (720, 0, 1200, 675), MK + [TRUCK17, SHOP_17, HELMET_17]), "K 16.2–21.26 1.6倍")],
     "N8 43.37「手で書きとめる。」", "立って黄色い手帳に書く手（N7 からカットで続く）", "ペンの音", "読んだ数字は人の手で残る"),
    ("B9 確かめる", "20–21小節　48.0–53.1", [lambda: tag(frame("S", 173.5, None, M2 + [CYC]), "S 172.2–174.73"), lambda: tag(frame("S", 178.0, None, M2 + [CYC]), "S 177.0–179.53")],
     "N9 48.43「行きと帰りではかって、ずれがないか確かめます。」", "遠くに着いた標尺手 → 観測者がのぞき、179.2 から歩き出す（実写だけ）", "曲のつなぎ目（48.03）", "ていねいさ"),
    ("B10 新しい目印", "22–24小節　53.1–60.7", [sk_link],
     "N10 53.49「こうしてできた、新しい高さの目印。ほかの測量や工事は、ここから高さを決めていきます。」", "地図に戻る → 54.98「新しい」で □ がオレンジ→紺、「高さの目印」→ 56.88／57.51／58.14 に地形・路線・工事のアイコンへ線（1本目と同じ渡し方）", "□ が紺で C・E・G", "ほかの測量や工事が使う"),
    ("B11 人", "25–28小節　60.7–70.8", [lambda: tag(frame("N", 7.5, (600, 196, 1200, 675), NV), "N 5.9–9.69"), lambda: tag(frame("S", 82.4, (170, 40, 678, 381), M1 + [(500, 258, 552, 296)]), "K 0–1.26 → S 81 → S 164")],
     "N11 64.86「ふたりで息を合わせて、道にそって。」", "のぞき続ける顔 → 手帳を持つ背中と遠くの標尺手（K 0–1.26）→ 人のいない機械と流れる車 → 2か所目で機械に向かう", "実音を少し前に", "まちのすぐ横で、二人で"),
    ("B12 締め", "29–32小節　70.8–80.9", [lambda: tag(frame("K", 12.0, K115, MK + [HELMET_85]), "K 8.53–16.12 等速、引く"), sk_end8],
     "N12 71.18「ほかの測量や工事が使う、“海からの高さ”の目印をつくる。それが、水準測量です。」", "最後の一打で二人の引き（実写の上に線なし）。文字 73.16–。78.37 から紺の □ → アイコン → 黒", "最後の和音のばし。G6（小）", "誇りと余韻"),
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
    d.text((PAD, 14), f"水準測量パート 絵コンテ v8「海からの高さ」　{n}/{of}", font=font(34), fill=INK)
    d.text((PAD, 62), "32小節・80.9秒・曲 V6d（8小節で止め）。コマは元の素材（ぼかし済み）、", font=font(22), fill="#555")
    d.text((PAD, 90), "図は真上の地図と接眼の円のスケッチ（日本の形は仮）。秒は完成尺。社外に出さない。", font=font(22), fill="#555")
    y = 120
    for c in cards: im.paste(c, (0, y)); y += c.height
    return im

groups = [ROWS[0:4], ROWS[4:8], ROWS[8:13]]
for n, rows in enumerate(groups, 1):
    p = OUT / f"storyboard_v8_p{n}.jpg"; page(rows, n, len(groups)).save(p, quality=88); print(p)
