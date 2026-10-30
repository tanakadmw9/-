"""計画段階の絵コンテ v8.6「海からの高さ」（設計のための測量。ゲート1 用。28小節が正本）。元の素材のコマ（ぼかし済み）と、真上の地図・接眼の円のスケッチで作る。
秒は plan/editing_v8.md（v8.6）の写し。v5〜v7 の真横の図は使わない。
使い方：source .venv/bin/activate && python3 scripts/53_plan_storyboard_v8.py /mnt/project-files/level/storyboard_v8/
出力：storyboard_v8_p1〜p3.jpg と compare_v7.jpg（v7 との対応表）（素材から作った画像なので、リポジトリには入れない）。幅 1080 の縦長＝スマホで縦に読む。
日本の形は、主な岬・湾の公知の経緯度から手で打った仮の折れ線（地図の画像はなぞっていない）。本番は editing_v8.md §3.2。
"""
import json, pathlib, subprocess, sys, io, math
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
NV = [(1150, 215, 1360, 310)]
BRAND7 = [(1030, 515, 1140, 565)]       # N：機械のメーカー名（B7 の窓）
BRAND11 = [(1000, 400, 1160, 470)]      # N：機械のメーカー名（B11 の窓、仮）   # N：奥の白い車のナンバー（窓の上の端）

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
    im, d = paper()
    P = japan(d, s=11.0, ox=60 - 128.5 * 11.0 * 0.81, oy=30)
    x, y = P(TOKYO); d.ellipse([x - 6, y - 6, x + 6, y + 6], fill=NAVY)
    label(d, (14, 14), "白い紙 → 日本の形 → 東京湾に紺の点", 18, box=True)
    label(d, (250, 232), "東京湾の平均の海面", 18, box=True)
    label(d, (110, 262), "点は左へすべって 0 の線になる", 15, fill=INK)
    return tag(im, "21.49–25.07")

ZY = 214                                  # 基準の線の高さ（2つの絵で同じ。1080 の画面で y 790）
LW, BW = 3, 5                             # 線の太さ・棒の幅（2つの絵で同じ）
def framek(src, t, crop, masks, W, H):
    im = frame(src, t, crop, masks)
    return im if (W, H) == (TW, TH) else frame_big(src, t, crop, masks, W, H)

def frame_big(src, t, crop, masks, W, H):
    vf = f"crop={crop[2]}:{crop[3]}:{crop[0]}:{crop[1]},"
    png = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", f"{t:.3f}", "-i", str(SRC[src]),
                          "-frames:v", "1", "-vf", vf + "null", "-f", "image2", "-c:v", "png", "-"], capture_output=True, check=True).stdout
    im = Image.open(io.BytesIO(png)).convert("RGB")
    for x1, y1, x2, y2 in masks:
        box = (max(0, x1 - crop[0]), max(0, y1 - crop[1]), min(im.width, x2 - crop[0]), min(im.height, y2 - crop[1]))
        if box[2] > box[0] and box[3] > box[1]: im.paste(im.crop(box).filter(ImageFilter.GaussianBlur(10)), box[:2])
    return im.resize((W, H), Image.LANCZOS)

def draw_align(d, k=1.0, wob=None):
    S = lambda v: v * k
    L = (lambda pts, c, w: d.line(pts, fill=c, width=w)) if wob is None else wob
    objs = [("m", 120, 260, 104), ("b", 300, 350, 139), ("h", 390, 440, 169)]   # 0 の線にじかに立つ
    d.polygon([(S(120), S(ZY)), (S(190), S(104)), (S(260), S(ZY))], fill="#E1E5EA")
    d.rectangle([S(300), S(139), S(350), S(ZY)], fill="#E1E5EA")
    d.polygon([(S(390), S(ZY)), (S(390), S(187)), (S(415), S(169)), (S(440), S(187)), (S(440), S(ZY))], fill="#E1E5EA")
    L([(S(40), S(ZY)), (S(500), S(ZY))], NAVY, max(2, int(LW * k)))
    for bx, top in ((190, 104), (325, 139), (415, 169)):
        d.rectangle([S(bx - BW / 2), S(top), S(bx + BW / 2), S(ZY)], fill=NAVY)
    zero(d, S(40), S(ZY), S(16), int(S(22)))

SITE_LINE = (300, 440, 228)               # □ の x（線の左の端＝標尺手の足もと）、線の右の端、y（K 18.75– 窓 0,200,1200,675 の 520 幅で。1080 の画面で y 841）
SITE_BARS = ((334, 30), (402, 38), (432, 32))   # 足もとから三脚の手前の舗装までの3点（道に沿ってカメラの方へ）。人・コーンにかけない
LAB_RIGHT, LAB_Y = 271, 150               # ラベルの右の端（標尺手の脚から 40 px 以上＝520 幅で 11 以上）と上の端（コーンの棒の上の端 y 185 にかけない）
def px(k, v):                             # 1920 の画面の画素 → この絵の画素（k は 520 幅に対する倍率）
    return v * k * TW / 1920
def outlined_line(d, pts, col, w, ow):
    d.line(pts, fill="white", width=w + 2 * ow); d.line(pts, fill=col, width=w)
def dot(d, x, y, k, col=ORANGE):           # 棒の上の点（直径 18 px、白い縁 3 px）。B10 の点も同じ形
    r, ow = max(px(k, 9), 0.8 * BW * k), max(1, round(px(k, 3)))   # 絵コンテは小さいので棒の太さに合わせて大きめに描く
    d.ellipse([x - r - ow, y - r - ow, x + r + ow, y + r + ow], fill="white"); d.ellipse([x - r, y - r, x + r, y + r], fill=col)
def draw_site(d, k=1.0, stage=3):
    S = lambda v: v * k
    ow = max(1, round(px(k, 3))); lw = max(2, int(LW * k))
    xs, x1, y = SITE_LINE
    if stage >= 2: outlined_line(d, [(S(xs + 9), S(y)), (S(x1), S(y))], ORANGE, lw, ow)     # 一本の線（三脚の脚の手前を通る）
    if stage >= 3:
        for bx, h in SITE_BARS:
            d.rectangle([S(bx - BW / 2) - ow, S(y - h) - ow, S(bx + BW / 2) + ow, S(y)], fill="white")
            d.rectangle([S(bx - BW / 2), S(y - h), S(bx + BW / 2), S(y)], fill=ORANGE)
        for bx, h in SITE_BARS: dot(d, S(bx), S(y - h), k)
        if stage >= 2: outlined_line(d, [(S(xs + 9), S(y)), (S(x1), S(y))], ORANGE, lw, ow)
    for o, col in ((ow, "white"), (0, ORANGE)):
        d.rectangle([S(xs - 9) - o, S(y - 9) - o, S(xs + 9) + o, S(y + 9) + o], outline=col, width=lw + 2 * o if o else lw)
    if stage >= 3 or stage == 2.5:
        f = font(int(S(18))); w = d.textlength("高さの目印", font=f)
        x0, y0, x1b, y1b = d.textbbox((S(LAB_RIGHT) - w, S(LAB_Y)), "高さの目印", font=f)
        d.rectangle([x0 - 5 - ow, y0 - 4 - ow, x1b + 5 + ow, y1b + 4 + ow], fill="white")
        label(d, (S(LAB_RIGHT) - w, S(LAB_Y)), "高さの目印", int(S(18)), box=True, bg=ORANGE)

def sk_align(W=TW, H=TH, cap=True):
    im = Image.new("RGB", (W, H), PAPER); d = ImageDraw.Draw(im); draw_align(d, W / TW)
    k = W / TW; f = font(int(17 * k)); w = d.textlength("東京湾の平均の海面", font=f)
    label(d, ((W - w) / 2, 236 * k), "東京湾の平均の海面", int(17 * k), box=True)      # 補足は白い紙まで出したまま（下の帯）
    if cap:
        label(d, (14, 14), "「ゼロ」で 0 の線 →「はかります」で3本の棒", 17, box=True)
        return tag(im, "25.07–29.07")
    return im

def sk_whitecut():
    im, d = paper()
    label(d, (14, 14), "29.07 白い紙で切る（0.32秒）", 18, box=True)
    label(d, (40, 110), "「道路を設計するときも、」の読点", 22, fill=INK)
    label(d, (40, 146), "海と現場は線・寄りでつながない", 18, fill=INK)
    label(d, (14, 262), "つなぐのは「も」「ひとつの基準」と、同じ形の絵", 15, fill=INK)
    return tag(im, "29.07–29.39")

def site_photo(t, W, H):
    from PIL import ImageEnhance
    im = framek("K", t, (0, 200, 1200, 675), MK + [TRUCK17, SHOP_17], W, H)
    return ImageEnhance.Color(ImageEnhance.Brightness(im).enhance(0.75)).enhance(0.6)   # □ が出てから B5 の終わりまで：明るさ −25%、彩度 −40%

def sk_sitesq(W=TW, H=TH, cap=True):
    im = site_photo(21.2, W, H); d = ImageDraw.Draw(im); draw_site(d, W / TW, stage=2)
    if cap:
        label(d, (14, 14), "「ひとつ」で □（C6）と写真が暗く →「基準」で実線", 17, box=True)
        return tag(im, "31.05–33.14")
    return im

def sk_siteform(W=TW, H=TH, cap=True):
    im = site_photo(24.3, W, H); d = ImageDraw.Draw(im); draw_site(d, W / TW, stage=3)
    if cap:
        label(d, (14, 14), "「高さの目印」でラベル →「から」で3本の棒と点", 17, box=True)
        return tag(im, "33.14–35.39")
    return im

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

def grid(d):
    d.rectangle([0, 0, TW, TH], fill="#EAF1F8")
    for gx in range(0, TW, 20): d.line([(gx, 0), (gx, TH)], fill="#D6E2EE", width=1)
    for gy in range(0, TH, 20): d.line([(0, gy), (TW, gy)], fill="#D6E2EE", width=1)
def tri(d, x, y, s=10):
    d.polygon([(x, y - s), (x - s, y + s * 0.8), (x + s, y + s * 0.8)], outline=NAVY, fill="#EAF1F8"); d.line([(x, y - s), (x - s, y + s * 0.8), (x + s, y + s * 0.8), (x, y - s)], fill=NAVY, width=3)
def draw_design(d, k=1.0, stage=2):
    S = lambda v: v * k
    d.rectangle([0, 0, S(TW), S(TH)], fill="#EAF1F8")
    for gx in range(0, TW, 20): d.line([(S(gx), 0), (S(gx), S(TH))], fill="#D6E2EE", width=1)
    for gy in range(0, TH, 20): d.line([(0, S(gy)), (S(TW), S(gy))], fill="#D6E2EE", width=1)
    if stage >= 2:
        for off in (-8, 8):
            q = [(x, y + off) for x, y in RC]
            for (x1, y1), (x2, y2) in zip(q, q[1:]):
                L = math.dist((x1, y1), (x2, y2)); t = 0
                while t < L:
                    t2 = min(L, t + 9)
                    d.line([(S(x1 + (x2 - x1) * t / L), S(y1 + (y2 - y1) * t / L)), (S(x1 + (x2 - x1) * t2 / L), S(y1 + (y2 - y1) * t2 / L))], fill=NAVY, width=max(2, int(2 * k)))
                    t += 15
    bh = 24 * TW / 1920                                     # 短い棒 24 px（足もとから上へ。てっぺんに点）
    ow = max(1, round(px(k, 3)))
    for x, y in PTS:
        d.rectangle([S(x - 1) - ow, S(y - bh), S(x + 1) + ow, S(y) + ow], fill="white")
        d.rectangle([S(x - 1), S(y - bh), S(x + 1), S(y)], fill=ORANGE)
        r = px(k, 9)                                      # 現場の棒の上の点と同じ形（直径 18 px、白い縁 3 px）
        d.ellipse([S(x) - r - ow, S(y - bh) - r - ow, S(x) + r + ow, S(y - bh) + r + ow], fill="white"); d.ellipse([S(x) - r, S(y - bh) - r, S(x) + r, S(y - bh) + r], fill=ORANGE)
    for x, y in TRI:
        sz = 10
        pts = [(S(x), S(y - sz)), (S(x - sz), S(y + sz * 0.8)), (S(x + sz), S(y + sz * 0.8))]
        d.polygon(pts, fill="#EAF1F8"); d.line(pts + [pts[0]], fill=NAVY, width=max(2, int(3 * k)))

RC = [(30, 147), (500, 137)]   # 道路の下書きのまん中（△ の間を通る。点を結ぶ線ではない）
PTS = [(70, 133), (115, 148), (180, 163), (235, 130), (300, 144), (350, 159), (395, 126), (455, 141)]   # 高さの点の足もと：道の上わき（−16）・まん中（0）・下わき（+16）に散らす（1080 で ±60 px）。坂に見えないよう上下させる
TRI = [(140, 200), (280, 95), (430, 184)]
def sk_design1(W=TW, H=TH, cap=True):
    im = Image.new("RGB", (W, H), PAPER); d = ImageDraw.Draw(im); draw_design(d, W / TW, stage=1)
    if cap:
        d.line([(150, 255), (210, 255)], fill=NAVY, width=2); d.polygon([(210, 249), (210, 261), (222, 255)], fill=NAVY)
        label(d, (14, 14), "高さの点（行き→帰り）→「位置」で △ →「あわせて」重なる", 17, box=True)
        label(d, (14, 262), "△ は1本目の基準点の印", 15, fill=INK)
        return tag(im, "51.19–53.72")
    return im

def sk_design2(W=TW, H=TH, cap=True):
    im = Image.new("RGB", (W, H), PAPER); d = ImageDraw.Draw(im); draw_design(d, W / TW, stage=2)
    if cap:
        label(d, (14, 14), "「道路の設計に」で道路の点線の下書き", 17, box=True)
        label(d, (14, 262), "下書き（これから決める線）。坂の線・文字なし", 15, fill=INK)
        return tag(im, "53.72–55.62")
    return im

def stick(d, x, y, col=INK, staff=False):
    d.ellipse([x - 5, y - 26, x + 5, y - 16], outline=col, width=2); d.line([(x, y - 16), (x, y)], fill=col, width=2)
    d.line([(x, y), (x - 6, y + 12)], fill=col, width=2); d.line([(x, y), (x + 6, y + 12)], fill=col, width=2)
    if staff: d.line([(x + 9, y - 34), (x + 9, y + 12)], fill="#C8322B", width=3)

def sk_child():
    im, d = paper()
    zy = 168
    d.line([(20, zy), (230, zy)], fill=NAVY, width=4); zero(d, 20, zy, 9, 13)
    d.polygon([(45, zy), (90, zy - 72), (135, zy)], outline=INK, width=3); d.rectangle([155, zy - 48, 190, zy], outline=INK, width=3)
    for bx, top in ((90, zy - 72), (172, zy - 48)): d.rectangle([bx - 3, top, bx + 3, zy], fill=NAVY)
    d.line([(282, zy + 12), (510, zy + 12)], fill="#9AA5B4", width=6)            # 道（右の絵も左と同じ幅 210）
    osq(d, 290, zy, 9)
    d.line([(300, zy), (500, zy)], fill=ORANGE, width=4)
    for bx, h in ((335, 40), (400, 52)):
        d.rectangle([bx - 3, zy - h, bx + 3, zy], fill=ORANGE); dot(d, bx, zy - h, 1.0)
    stick(d, 445, zy - 12, staff=True)
    stick(d, 488, zy - 12); d.line([(480, zy - 30), (494, zy - 30)], fill=INK, width=3)
    label(d, (14, 14), "終わりの画：子どもが描く絵（0.6秒で並ぶ）", 18, box=True)
    label(d, (262, 192), "左右は線でつながない（同じ形・同じ幅）", 13, fill=INK)
    label(d, (60, 222), "“高さの土台” をはかる", 26)
    return tag(im, "68.26–70.78")

def ov_level(im):
    return ov_lab(im, (330, 30), "レベル", (300, 118))

# (拍, 小節・秒, [コマ], ナレ, 画・文字, 音, 目的)
ROWS = [
    ("B1 章扉", "1小節　0.0–2.5", [sk_door8], "N1a 0.30「測量部門の仕事のひとつ、」", "章扉（共通）。水準のアイコン（□）だけ灯る", "章扉の灯り", "部門の中の1作業"),
    ("B2 据える", "2–3小節　2.5–7.6", [lambda: tag(frame("S", 49.6, (70, 82, 707, 398), M1), "S 48.58– 実時間"), lambda: tag(ov_title8(frame("S", 53.3, (70, 82, 707, 398), M1)), "6.95 載る＝題")],
     "N1b 7.24「水準測量です。」", "ケースを開ける → 持ち上げる → 6.95 に載る。題とサブ「“高さの土台” をはかる」", "載る音（実音）", "人の手で始まる"),
    ("B3 はかる", "4–5小節　7.6–12.6", [lambda: tag(frame("S", 66.0, (170, 40, 678, 381), M1), "S 56–74 4.75倍"), lambda: tag(frame("N", 2.6, (600, 0, 1320, 742), [(1060, 200, 1200, 280)] + NV), "N 2.0–3.26 窓 1.45倍")],
     "N2 9.03「道ばたで、高さを、ミリまではかります。」（速さ 1.05、〜12.63）", "整準（気泡をのぞく）→ 機械と顔の全体（1.45倍）。文字なし", "道の環境音", "何をしているか"),
    ("B4 問い", "6–8小節　12.6–20.2", [lambda: tag(frame("K", 3.0, None, MK), "K 1.5 全画面から"), lambda: tag(ov_q(ov_lab(frame("K", 7.82, KW132, MK + [HELMET_85]), (40, 50), "標尺", (93, 120))), "K 7.82 で止める")],
     "N3 13.38「でも、高さって、どこからはかるのでしょう。」（「どこから」15.77、〜17.29）", "歩いて来てかがむ。「標尺」14.50–16.50。18.96 に止まる", "17.70 に曲が止まる → 3 秒、現場の音だけ（考える間）", "問いを置く"),
    ("B5 ひとつの基準 1/3", "9–11小節　20.2–25.1", [sk_pull1, sk_pull2],
     "N4 21.49「日本の高さは、東京湾の海の高さを0にして、はかります。」（「東京湾」23.32）", "一番強い頭で写真が縮む → 白い紙 → 21.49 小さな日本の形 → 23.32 東京湾に紺の点 → 点が左へすべる。補足「東京湾の平均の海面」23.02–29.07（白い紙まで）", "曲のみ", "日本の高さの基準を一つ見せる"),
    ("B5 ひとつの基準 2/3", "11–12小節　25.1–29.4", [sk_align, sk_whitecut],
     "N4 の続き：「ゼロ」25.12、「はかります」26.46　N5 27.57「道路を設計するときも、…」", "25.07 横一本の 0 の線（C6）→ 物が線にじかに立つ（背くらべの形。地面の線・目盛り・数字は描かない）→ 26.46 3本の棒 → 29.07 白い紙 0.32秒。補足は白い紙まで", "0 の線で C6（−3 dB、「ゼロ」の 0.05秒前）", "なるほど：高さはひとつの基準からはかる"),
    ("B5 ひとつの基準 3/3", "12–14小節　29.4–35.4", [sk_sitesq, sk_siteform],
     "N5「…まず、ひとつの基準を決めます。」（「まず」29.80、「ひとつの基準」31.05、〜32.66）　N6 33.06「近くの“高さの目印”から、…」（「高さの目印」33.62、「から」34.71）", "K 18.75– の実写（左の窓）→ 31.05 □（C6）と写真が暗く → 31.57 一本の実線 → 33.14 ラベル「高さの目印」→ 34.76 3本の棒と点（0 の絵と同じ太さ・数）。白い縁 3 px。0 の字は出さない", "□ で C6（0 の線と同じ音）", "現場も、まずひとつの基準（近くの目印）を決める"),
    ("B6 つなぐ", "15小節　35.4–37.9", [lambda: tag(frame("S", 169.2, None, M2), "S 169.09–171.62 実時間")],
     "N6「…高さをつないでいきます。」（「つないで」36.09、〜37.13）", "ものさしを持った人が 35.5 に機械の横を通って次の点へ", "足音・道の音", "目印から高さをつなぐ"),
    ("B7 読む", "16–17小節　37.9–43.0", [lambda: tag(frame("N", 4.5, (840, 200, 960, 540), BRAND7), "N 3.3–5.83 窓 2.0倍"), sk_eyepiece],
     "N7 39.75「遠くのものさしを、目で読んで、」（「読んで」41.71、〜42.12）", "目とつまみの寄り（2.0倍）→ 40.45（曲のつなぎ目）接眼の円 → 41.0–41.5 ピント → 41.71 横の線にうすい帯（標尺は動かさない、数字なし）", "N の実音 → 曲だけ", "目で読む仕事"),
    ("B8 書く", "18小節　43.0–45.5", [lambda: tag(frame("K", 17.0, (720, 0, 1200, 675), MK + [TRUCK17, SHOP_17, HELMET_17]), "K 16.2–18.73 1.6倍")],
     "N8 43.37「手で書きとめる。」（〜44.35）", "立って黄色い手帳に書く手（N7 からカットで続く）", "ペンの音", "読んだ数字は人の手で残る"),
    ("B9 確かめる", "19–20小節　45.5–50.6", [lambda: tag(frame("S", 173.5, None, M2 + [CYC]), "S 172.2–174.73 全画面"), lambda: tag(frame("S", 178.0, (170, 40, 678, 381), M2 + [CYC]), "S 177.0– 窓 1.25倍")],
     "N9 45.90「行きと帰りではかって、ずれがないか確かめます。」（〜49.69）", "遠くに着いた標尺手 → 寄りの大きさで、観測者がのぞき 179.2 から歩き出す（実写だけ）", "S の実音", "行きと帰りで確かめる"),
    ("B10 設計へ", "21–22小節　50.6–55.6", [sk_design1, sk_design2],
     "N10 50.96「高さは、位置とあわせて、道路の設計に使われます。」（速さ 1.05。「位置」52.12、「道路」53.65、〜55.44）", "設計の紙 → 51.19 高さの点（短い棒と点。散らす。行き→帰り）→ 52.12「位置」で △ → 52.46「あわせて」重なる → 53.72「道路」で点線の下書き（△ の間を通る）→ 55.62 まで保つ", "C・E・G（53.72、小）", "位置とあわせて、道路の設計に使われる"),
    ("B11 人", "23–24小節　55.6–60.7", [lambda: tag(ov_level(frame("S", 81.6, (170, 40, 678, 381), M1 + [(500, 258, 552, 296)])), "S 81.0–83.53 窓"), lambda: tag(frame("N", 8.2, (600, 200, 1200, 675), NV + BRAND11), "N 5.9–8.43 顔 1.6倍")],
     "声なし（実音 +3 dB）", "人のいない機械と流れる車に「レベル」→ 58.14 のぞく寄りの顔で終える（K の引きは使わない）", "実音 +3 dB", "まちのすぐ横で。寄りの顔で終える"),
    ("B12 締め", "25–28小節　60.7–70.8", [lambda: tag(frame("K", 12.0, K115, MK + [HELMET_85]), "K 8.53–16.12 等速、引く"), sk_child],
     "N12 61.07「設計が使う、“高さの土台”をはかる。それが、水準測量です。」（「高さの土台」62.69、〜67.19）", "N の顔から、最後の一打で二人の引き。文字「“高さの土台” をはかる」62.39–。68.26 子どもの絵（同じ形を左右に離す）→ 70.15 オレンジの □ だけ縮んでアイコン → 黒", "最後の和音のばし。G6（小）", "誇りと余韻。中心の絵をもう一度"),
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
    d.text((PAD, 8), row[0], font=font(30), fill="white"); d.text((390, 12), row[1], font=font(26), fill="white")
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
    d.text((PAD, 14), f"水準測量パート 絵コンテ v8.6「海からの高さ」　{n}/{of}", font=font(34), fill=INK)
    d.text((PAD, 62), "28小節・70.8秒・曲 V6b（8小節で止め）。コマは元の素材（ぼかし済み）、", font=font(22), fill="#555")
    d.text((PAD, 90), "図は 0 の線・接眼の円・設計の紙・子どもの絵のスケッチ。秒は完成尺。社外に出さない。", font=font(22), fill="#555")
    y = 120
    for c in cards: im.paste(c, (0, y)); y += c.height
    return im

# 拍ごとの計画の画（各行の1コマ目）と秒：scripts/40_qc.py の storyboard_compare が書き出しと並べる（plan/editing_storyboard.png が無いとき）
RD = OUT / "plan_rows"; RD.mkdir(exist_ok=True); meta_rows = []
for i, r in enumerate(ROWS):
    t0, t1 = [float(x) for x in r[1].split("　")[-1].split("–")]
    r[2][0]().convert("RGB").save(RD / f"row_{i:02d}.png")
    meta_rows.append({"beat": r[0], "bars": r[1], "start": t0, "end": t1, "img": f"row_{i:02d}.png", "picture": r[4]})
(RD / "rows.json").write_text(json.dumps(meta_rows, ensure_ascii=False, indent=1))

groups = [ROWS[0:4], ROWS[4:9], ROWS[9:]]
for n, rows in enumerate(groups, 1):
    p = OUT / f"storyboard_v8_p{n}.jpg"; page(rows, n, len(groups)).save(p, quality=88); print(p)

# ---- ゲートの1枚目：v7（v7.4）との対応表。変えた画を先に、同じ画はその理由と ----
CMP = [
    ("変", "尺と曲", "32小節・80.9秒（V6d）", "28小節・70.8秒（V6b）。32小節は別案"),
    ("変", "芯の考え", "高さのバトンを、となりへつなぐ", "設計のための測量。高さはひとつの基準からはかる（日本は海の0、現場は近くの目印）"),
    ("変", "B4 ナレ", "仲間がひとり、ものさしを…", "問い「高さって、どこからはかるのでしょう」"),
    ("変", "B5 看板", "真横の図：目線・のぼって・わたって・おりる", "0 の線から3本の棒 → 白い紙 → 現場の実写で □ の線から3本の棒と点（同じ形）"),
    ("変", "B7", "真横の図「となりへ、となりへ」", "N の顔 → 描いた接眼の円（横の線を読む）"),
    ("変", "B9", "S 177 全画面 → 図（帰りの線）", "実写だけ：S 172 全画面 → S 177 を 1.25倍の窓"),
    ("変", "B10", "真横の図「新しい道」", "設計の紙：散らした高さの点と位置の △ が重なる → △ の間に道路の点線の下書き"),
    ("変", "B11", "N の顔（長い）→ S 172 → S 81", "声なし。S 81「レベル」→ N の顔で終える"),
    ("変", "N の寄り", "同じ窓", "B3 機械と顔／B7 目とつまみ／B11 顔（窓を変えた）"),
    ("変", "終わりの画", "紺の □ が縮んでアイコン", "子どもが描く絵（同じ形を左右に離す）→ □ だけ縮む"),
    ("変", "締め", "“高さの目印” をつくる", "設計が使う “高さの土台” をはかる"),
    ("変", "「レベル」", "B6 の S の機械", "B11 の S 81 の機械（人のいない画）"),
    ("同", "B1 章扉", "共通の型", "同じ（シリーズの型）"),
    ("同", "B2 据える", "S 48.58–53.63、題", "同じ（素材）"),
    ("同", "B3 はかる", "S 56–74 4.75倍 → N 2.0", "同じ（素材）"),
    ("同", "B4 の画", "K 1.5–7.82、寄り、止め絵、8小節の止め", "同じ（素材）。「標尺」は 14.5 に早めた"),
    ("同", "B6 歩く", "S 165.67– 標尺手が歩く", "ほぼ同じ（S 169.09– の1小節、素材）"),
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
    d.text((PAD, 16), "v7 との対応表（v7.4 → v8.6）", font=font(36), fill=INK)
    d.text((PAD, 70), "変えた画を先に。同じ画が残るのは、素材が約40秒（S・K・N の3本）で、", font=font(22), fill="#555")
    d.text((PAD, 100), "人の仕事が映る所がそこしかないため。図・ナレ・終わりの画・B9〜B11 の並びは変えた。", font=font(22), fill="#555")
    n_ch = sum(1 for r in CMP if r[0] == "変")
    d.text((PAD, 140), f"変えた {n_ch} か所／同じ {len(CMP) - n_ch} か所（同じ所は素材の都合）", font=fb, fill=ORANGE)
    d.text((PAD, 180), "絵コンテは p2（看板）から見てください。社外に出さない。", font=font(22), fill="#555")
    y = 230
    d.rectangle([0, y, W, y + 44], fill="#2C4A3E")
    for (x, _), h in zip(cols, ("", "どこ", "v7.4", "v8.6")): d.text((x + 6, y + 8), h, font=fb, fill="white")
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

# ---- 2コマの見本（editing_v8.md §8 の一番大事な所）：b5_pair.jpg（0 の絵と現場の絵）・b10.jpg ----
def mock(pair, name, caps, title):
    W2, H2 = 960, 540
    ims = [f(W2, H2, cap=False) for f in pair]
    out = Image.new("RGB", (W2 * len(ims) + 20 * (len(ims) - 1), H2 + 120), "white"); d = ImageDraw.Draw(out)
    d.text((PAD, 14), title, font=font(32), fill=INK)
    for i, (im, c) in enumerate(zip(ims, caps)):
        x = i * (W2 + 20); out.paste(im, (x, 60)); d.text((x + 12, H2 + 70), c, font=font(24), fill="#333")
    p = OUT / name; out.save(p, quality=90); print(p)
mock([sk_align, sk_siteform], "b5_pair.jpg",
     ["27.0 秒：日本の高さは、…0にして、はかります。", "35.0 秒：近くの“高さの目印”から、…"],
     "B5 の2つの絵（同じ形・違う色。線・寄りでつながない）　v8.6")
mock([sk_design1, sk_design2], "b10.jpg",
     ["52.8 秒：「位置」で △、「あわせて」で重なる", "54.5 秒：「道路の設計に」で点線の下書き"],
     "B10 設計へ（高さは位置とあわせて、道路の設計に使われる）　v8.6")
