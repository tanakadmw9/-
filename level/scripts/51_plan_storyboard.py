"""計画段階の絵コンテ（ゲート1 用）を、元の素材のコマ（ぼかし済み）と手描きのスケッチから作る。v6.1（32小節・80.9 秒）。
秒・切り出し窓・文は plan/editing_v6.md（32小節が正本）と plan/content_v6.md（v6.1）§3・§4 の写し。v5 の版は git の履歴にある。
使い方：python3 scripts/51_plan_storyboard.py /mnt/project-files/level/storyboard_v6/
出力：storyboard_v6_p1.jpg〜p3.jpg（素材から作った画像なので、リポジトリには入れない）。幅 1080 の縦長＝スマホで縦に読む。
"""
import pathlib, subprocess, sys, io, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = pathlib.Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
SRC = {k: ROOT / f"source/{v}.mp4" for k, v in {"S": "S_sueru", "K": "K_kansoku", "N": "N_nozoki"}.items()}
FONT = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
NAVY, ORANGE, PAPER, GRID, INK, FAINT = "#1F3A5F", "#E8742A", "#F4F1EA", "#E2DCCD", "#14202E", "#B9C1CC"
TW, TH = 520, 293          # コマ1枚
W = 1080

def font(px):
    return ImageFont.truetype(FONT, px)

# ---- 素材のコマ（ぼかしは元の画素の四角。窓で切るときは窓の中へずらす）----
def frame(src, t, crop=None, masks=()):
    vf = (f"crop={crop[2]}:{crop[3]}:{crop[0]}:{crop[1]}," if crop else "")
    png = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", f"{t:.3f}", "-i", str(SRC[src]),
                          "-frames:v", "1", "-vf", vf + "null", "-f", "image2", "-c:v", "png", "-"],
                         capture_output=True, check=True).stdout
    im = Image.open(io.BytesIO(png)).convert("RGB")
    ox, oy = (crop[0], crop[1]) if crop else (0, 0)
    for x1, y1, x2, y2 in masks:
        box = (max(0, x1 - ox), max(0, y1 - oy), min(im.width, x2 - ox), min(im.height, y2 - oy))
        if box[2] > box[0] and box[3] > box[1]:
            r = 10 if src != "S" else 5
            im.paste(im.crop(box).filter(ImageFilter.GaussianBlur(r)), box[:2])
    return im.resize((TW, TH), Image.LANCZOS)

def paper():
    im = Image.new("RGB", (TW, TH), PAPER); d = ImageDraw.Draw(im)
    for x in range(0, TW, 26): d.line([(x, 0), (x, TH)], fill=GRID, width=1)
    for y in range(0, TH, 26): d.line([(0, y), (TW, y)], fill=GRID, width=1)
    return im, d

def dotted(d, a, b, color=ORANGE, w=4, step=12):
    n = max(1, int(math.dist(a, b) // step))
    for i in range(0, n, 2):
        p = (a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n)
        q = (a[0] + (b[0] - a[0]) * (i + 1) / n, a[1] + (b[1] - a[1]) * (i + 1) / n)
        d.line([p, q], fill=color, width=w)

def label(d, xy, s, px=22, fill=NAVY, box=False, bg=NAVY):
    f = font(px)
    if box:
        x0, y0, x1, y1 = d.textbbox(xy, s, font=f)
        d.rectangle([x0 - 5, y0 - 4, x1 + 5, y1 + 4], fill=bg); fill = "white"
    d.text(xy, s, font=f, fill=fill)

def tag(im, s):   # コマの右下に小さな札（何のコマか）。スケッチの説明（左上）と重ならないように
    d = ImageDraw.Draw(im); f = font(18); w = d.textlength(s, font=f)
    label(d, (TW - w - 10, TH - 28), s, 18, box=True, bg="#000000"); return im

# ---- 人と機械の外形（線だけ。顔は描かない）----
def holder(d, x, g, h, color=NAVY, w=3, staff=True):
    """標尺手：足もと (x,g)、背の高さ h。標尺は体の右（機械の側）に出して持つ。"""
    hr = h * 0.075; top = g - h
    d.ellipse([x - hr, top, x + hr, top + 2 * hr], outline=color, width=w)
    d.polygon([(x - h * .13, top + 2.2 * hr), (x + h * .13, top + 2.2 * hr), (x + h * .11, g - h * .45), (x - h * .11, g - h * .45)], outline=color, width=w)
    d.line([(x - h * .07, g - h * .45), (x - h * .08, g)], fill=color, width=w); d.line([(x + h * .07, g - h * .45), (x + h * .08, g)], fill=color, width=w)
    sx = x + h * .24
    d.line([(x + h * .12, top + h * .30), (sx, top + h * .36)], fill=color, width=w)     # 腕
    if staff:
        d.rectangle([sx - 3, g - h * 1.30, sx + 3, g], outline=color, width=2)
    return sx, g - h * 1.30

def observer(d, x, g, h, color=NAVY, w=3):
    """観測者：背中を丸めてのぞく。足もと (x,g)、まっすぐ立った時の背 h。目は左を向く。"""
    hip = (x + h * .05, g - h * .50); sh = (x - h * .18, g - h * .78); hr = h * .07
    d.line([(x - h * .05, g), hip], fill=color, width=w); d.line([(x + h * .12, g), hip], fill=color, width=w)
    d.line([hip, sh], fill=color, width=w + 2)
    d.ellipse([sh[0] - h * .20 - hr, sh[1] - hr * 1.2 - hr, sh[0] - h * .20 + hr, sh[1] - hr * 1.2 + hr], outline=color, width=w)
    d.line([sh, (sh[0] - h * .10, g - h * .62)], fill=color, width=w)

def level(d, x, g, ih, color=NAVY, w=3):
    """三脚と機械。足もと中心 x、機械の高さ ih。対物レンズ（左の端）の位置を返す。"""
    hy = g - ih
    for dx in (-ih * .28, 0, ih * .28): d.line([(x, hy + 8), (x + dx, g)], fill=color, width=w)
    d.rectangle([x - ih * .16, hy - 9, x + ih * .16, hy + 7], outline=color, width=w)
    return (x - ih * .16, hy - 1)

# ---- 図のスケッチ ----
G = 230   # 真横の図の地面（コマの中の y）

def sk_door(mode="door"):
    im, d = paper()
    for i in range(5):
        x = 70 + i * 95
        on = (i == 1)
        d.ellipse([x - 30, 116, x + 30, 176], outline=ORANGE if on else NAVY, width=5 if on else 2)
        if on: d.rectangle([x - 4, 126, x + 4, 166], outline=ORANGE, width=3)
    label(d, (150, 40), "測量部門のしごと", 30)
    if mode == "end":
        label(d, (40, 220), "道の “横顔” をはかる", 30)
    return im

def sk_trace():
    im = frame("K", 8.5, KW132, MK_ALL)
    d = ImageDraw.Draw(im); s = TW / 1455
    P = lambda x, y: ((x - 465) * s, (y - 60) * s)
    wh = "white"
    d.line([P(735, 630), P(1013, 878)], fill=wh, width=4)                              # 縁石
    for fx, fy in ((720, 830), (1075, 878), (1150, 878)): d.line([P(1085, 400), P(fx, fy)], fill=wh, width=3)   # 三脚
    d.rectangle([*P(665, 405), *P(748, 685)], outline=wh, width=3)                     # 標尺手（外形のかわりに四角で）
    d.rectangle([*P(1090, 278), *P(1430, 878)], outline=wh, width=3)                   # 観測者
    label(d, (14, 14), "なぞる：外形の線だけ（顔は描かない）", 20, box=True)
    return tag(im, "20.2 K 8.5 で止めて、なぞる")

def sk_stage1():
    im, d = paper()
    d.line([(40, 190), (230, TH)], fill=NAVY, width=3)                                  # 縁石はまだ斜め
    level(d, 330, TH - 6, 150)
    observer(d, 440, TH - 4, 230)
    holder(d, 120, 196, 66, FAINT, 2)                                                    # もとの大きさ（うすく）
    holder(d, 120, TH - 6, 185)                                                          # 観測者と同じ大きさへ
    d.line([(178, 150), (178, 104)], fill=ORANGE, width=3); d.polygon([(170, 112), (186, 112), (178, 98)], fill=ORANGE)
    label(d, (14, 14), "① 標尺手だけ大きくなる（約2倍）", 21, box=True)
    label(d, (230, 50), "観測者はそのまま", 19)
    return tag(im, "21.6–22.4")

def side_base(d, hx=140, lx=395, line=True, rod=None):
    d.line([(20, G), (TW - 20, G)], fill=NAVY, width=3)
    obj = level(d, lx, G, 72)
    observer(d, lx + 45, G, 80)
    sx, _ = holder(d, hx, G, 82)
    if line: dotted(d, obj, (sx + 4, obj[1]))
    if rod: d.rectangle([sx + 8, obj[1], sx + 14, G], fill=ORANGE)
    return obj, sx

def sk_side():
    im, d = paper()
    obj, sx = side_base(d, rod=True)
    label(d, (150, 60), "水平な一本の線", 26)
    label(d, (14, 14), "② 全体が引いて真横の図に", 21, box=True)
    d.ellipse([sx + 5, G - 6, sx + 17, G + 6], fill=ORANGE)
    return tag(im, "22.4–28.0")

PTS = [(300, 0), (240, 22), (180, 12), (120, -4), (60, -16)]   # P1〜P5（x、地面の上下。＋が低い）
def sk_swaps():
    im, d = paper()
    d.line([(20, G), (TW - 20, G)], fill=FAINT, width=2)                                # 見た目の平らな地面（うすく）
    obj = level(d, 440, G, 72); observer(d, 482, G, 80)
    y0 = obj[1]
    for i, (x, dy) in enumerate(PTS):
        col = ORANGE if i == 4 else NAVY
        d.rectangle([x - 3, y0, x + 3, G + dy], fill=col); d.ellipse([x - 6, G + dy - 6, x + 6, G + dy + 6], fill=col)
    holder(d, 60 - 24, G - 16, 82, NAVY, 2, staff=False)
    dotted(d, obj, (66, y0))
    label(d, (190, 64), "長いほど 低い", 24, box=True)
    for i, (x, dy) in enumerate(PTS):
        label(d, (x - 10, G + dy + 10), "CDEGA"[[2, 0, 1, 3, 4][i]], 16, fill=ORANGE)
    label(d, (14, 14), "立ち替わり：0.8／0.6／0.5秒", 20, box=True)
    return tag(im, "33.5–39.0")

def sk_connect():
    im, d = paper()
    d.line([(20, G), (TW - 20, G)], fill=FAINT, width=2)
    obj = level(d, 440, G, 72, FAINT, 2); observer(d, 482, G, 80, FAINT, 2)
    for x, dy in PTS: d.rectangle([x - 3, obj[1], x + 3, G + dy], fill="#D8DEE6")
    pts = [(x, G + dy) for x, dy in PTS]
    d.line(pts, fill=NAVY, width=5)
    for p in pts: d.ellipse([p[0] - 6, p[1] - 6, p[0] + 6, p[1] + 6], fill=NAVY)
    label(d, (90, 70), "道の横顔", 34)
    label(d, (14, 14), "つながる＋和音 C・E・G", 20, box=True)
    return tag(im, "40.45")

def sk_profile():
    im, d = paper()
    f = lambda x: 190 + 22 * math.sin(x / 55) + 14 * math.sin(x / 23) - 0.06 * x
    pts = [(x, f(x)) for x in range(40, TW - 20, 22)]
    d.line(pts, fill=NAVY, width=3)
    for p in pts: d.ellipse([p[0] - 3, p[1] - 3, p[0] + 3, p[1] + 3], fill=NAVY)
    d.rectangle([22, f(40) - 10, 42, f(40) + 10], outline=NAVY, width=3); d.ellipse([29, f(40) - 3, 35, f(40) + 3], fill=NAVY)
    label(d, (18, f(40) + 18), "水準点", 20)
    road = [(x, 200 - 0.10 * x + 10 * math.sin(x / 140)) for x in range(40, TW - 20, 6)]
    d.line(road, fill=NAVY, width=7)
    up = [p for p in road if 330 <= p[0] <= 460]
    d.line(up, fill=ORANGE, width=9)
    label(d, (330, 120), "「自転車」で一度灯る", 18, fill=ORANGE)
    label(d, (14, 14), "新しい道の線（「坂」で描き終わる）", 20, box=True)
    label(d, (14, 262), "高さは大きく、距離は縮めて描いています", 17, fill=INK)
    return tag(im, "48.0–58.1")

def sk_end():
    im, d = paper()
    obj, sx = side_base(d, hx=120, lx=360)
    label(d, (14, 50), "→ 点線が縮んで水準のアイコンへ → 黒", 18, fill=INK)
    d.ellipse([440, 30, 500, 90], outline=ORANGE, width=4); d.rectangle([466, 40, 474, 80], outline=ORANGE, width=2)
    label(d, (14, 14), "終わりの画：看板と同じ絵", 20, box=True)
    return tag(im, "78.4–80.4")

def ov_title(im):
    band = Image.new("RGBA", (TW, 110), (20, 32, 46, 150)); im.paste(band, (0, 8), band)
    d = ImageDraw.Draw(im)
    label(d, (24, 18), "水準測量", 44, fill="white"); label(d, (26, 72), "地面の“高さ”をはかる", 22, fill="white")
    return im

def ov_label(im, xy, s, to):
    d = ImageDraw.Draw(im); label(d, xy, s, 20, box=True); d.line([(xy[0] + 20, xy[1] + 28), to], fill=NAVY, width=2)
    return im

KW132 = (465, 60, 1455, 818)
TRUCK = {3.0: (0, 0, 0, 0), 8.5: (0, 0, 0, 0), 12.0: (0, 0, 0, 0),   # K 3〜12 は軽トラックの後ろが観測者の陰（K 1.5–2.6 は本番で追いかけてぼかす）
         17.0: (1125, 555, 1200, 625)}   # K 15–20：荷台の社名とナンバー
SHOP_17 = (1150, 478, 1275, 515)   # K 15–20：奥の店の看板
HELMET_85 = (1090, 290, 1160, 350); HELMET_17 = (1245, 60, 1385, 118)
MK = [(1015, 0, 1245, 100), (0, 465, 490, 575), (1680, 568, 1756, 614)]
MK_ALL = MK + [TRUCK[8.5], HELMET_85]
M1 = [(394, 30, 486, 72), (0, 232, 150, 292), (455, 262, 500, 282)]
M2 = [(535, 0, 648, 22), (0, 172, 70, 206), (100, 200, 312, 262), (605, 208, 685, 228)]

# (拍, 小節・秒, [コマ], ナレ（秒）, 画・文字, 音, 目的)
ROWS = [
    ("B1 章扉", "1小節　0.0–2.5", [lambda: tag(sk_door(), "1.26 灯る")],
     "N1a 0.30「測量部門の仕事のひとつ、」", "章扉（共通）。3拍目で水準のアイコン（標尺）だけ灯る。文字「測量部門のしごと」", "章扉の灯り（共通）", "部門の中の1作業だと形で示す"),
    ("B2 据える", "2–3小節　2.5–7.6", [lambda: tag(frame("S", 20.0, None, M1), "S 2–40 を15倍"), lambda: tag(ov_title(frame("S", 53.3, (70, 82, 707, 398), M1)), "6.95 載る＝題")],
     "N1b 6.85「水準測量です。」", "早回しで三脚が立つ → 実時間で機械が載る（6.95）。その瞬間に題とサブ（空の部分に）", "前奏。載る音（実音）を聞かせるため曲を −12 dB", "人の手が仕事を始める所から"),
    ("B3 水平に", "4–5小節　7.6–12.6", [lambda: tag(frame("S", 66.0, (170, 40, 678, 381), M1), "S 56–74 を4.75倍"), lambda: tag(frame("N", 2.6, (600, 180, 1200, 675)), "N 2.0–3.3")],
     "N2 8.60「まず、機械を、ぴったり水平に。」", "整準の手元、頭を下げて気泡を見る → 目を当てる寄り。ラベル「レベル」", "道の環境音", "人の手間。「まず水平」＝線の前提"),
    ("B4 ふたり", "6–8小節　12.6–20.2", [lambda: tag(frame("K", 3.0, None, MK + [TRUCK[3.0]]), "K 1.5 全画面から"), lambda: tag(ov_label(frame("K", 8.5, KW132, MK_ALL), (40, 30), "標尺", (93, 120)), "1.32倍へ寄る → 8.5 で止める")],
     "N3 13.04「のぞく先には、仲間がひとり。長いものさしを立てて、待っています。」（〜18.93）", "歩いて来てかがむ。15.17 に寄りきってラベル「標尺」（引き出し線は標尺の上の端へ）。19.64 に止まる", "K の実音（足音）。17.70 に曲が止まる（8小節の和音）→ 止まった写真と現場の音だけ 1.8秒", "二人目の人。動かずに待つ仕事。看板の前の息"),
    ("B5 看板 1/2", "9小節　20.2–22.8", [sk_trace, sk_stage1],
     "N4 20.62「機械がつくるのは、まっすぐ水平な、一本の線。」", "一番強い頭でなぞる（20.19–20.99）→ 紙に溶ける（21.02–21.65）→ ① 観測者はそのまま、標尺手だけが同じ大きさまで大きくなる（21.65–22.45）", "曲で一番強い頭（9小節）", "このパートの唯一のしくみ。1本目の「倒れる」と対"),
    ("B5 看板 2/2", "10–12小節　22.8–30.3", [sk_side, lambda: tag(sk_door_free(), "12小節：ゆっくり見せる")],
     "N5 25.01「その線から、地面までの長さを、ものさしで読みます。」（〜29.55）", "② 全体が引いて真横の図に（22.45–23.38）→ 点線が標尺に当たる 24.02 → 文字「水平な一本の線」→ 棒が地面に着く 26.54 → 28.7 読む所に小さな印", "鉄琴 G6（24.02）・E6（26.54）", "水平な線から下へ、をはかる"),
    ("B6 歩く", "13小節　30.3–32.9", [lambda: tag(frame("S", 169.4, (170, 0, 678, 381), M2), "S 168.2–170.7 1.25倍")],
     "N6 30.74「読んだら、次の場所へ。」", "標尺手がものさしを持って機械の横を通り、奥へ", "足音・道の音（実音）を前に", "しくみの真ん中に人の歩き"),
    ("B7 横顔", "14–17小節　32.9–43.0", [sk_swaps, sk_connect],
     "N7 33.26「地面が低いところほど、長く読めます。」　N8 39.30「つなぐと……道の、横顔。」", "低い所で一番長い棒（35.39）＋文字「長いほど 低い」→ 立ち替わり3回（点 37.92／38.55／39.03）→ つながる 40.45 → 棒と人は30%、文字「道の横顔」40.8–42.9", "鉄琴：低い地面ほど低い音（C D E G A）、つながると和音", "人が歩いた跡が、道の横顔になる（なるほど）"),
    ("B8 書く", "18–19小節　43.0–48.0", [lambda: tag(frame("K", 17.0, (720, 0, 1200, 675), MK + [TRUCK[17.0], SHOP_17, HELMET_17]), "K 15.5–20.6 1.6倍")],
     "N9 43.38「読んだ長さは、その場で手帳に。」", "立って黄色い手帳に書く手。ヘルメットの印刷はぼかす", "ペンの音（ごく小）", "読んだ長さは人の手で残る"),
    ("B9 坂", "20–23小節　48.0–58.1", [sk_profile],
     "N10a 48.33「平らな道にも、上り下り。」　N10 51.01「この横顔をもとに、道をつくる人が、坂を決めます。」　N11 55.78「自転車でのぼる坂も、ここから。」", "曲のつなぎ目（48.03）で横顔が戻り、引いて長くなる。左端に □「水準点」。新しい道の線が「坂」で描き終わる（54.35）。「自転車」で上りの所が一度灯る（55.9）。注記は1つ", "鉛筆の音（ごく小）", "なぜ大事か：この横顔で坂のかたむきが決まる"),
    ("B10 人", "24–28小節　58.1–70.8", [lambda: tag(frame("N", 6.0, (600, 196, 1200, 675)), "N 3.3–10.3 1.6倍"), lambda: tag(frame("S", 173.6, None, M2), "S 172–175 → 177–179.5")],
     "（はじめ2.5秒は声なし）N12 60.60「ミリの違いも、見のがさないように。」　N13 65.50「ふたりで息を合わせて、道にそって進みます。」", "のぞいたままピントのつまみを回す寄り → 遠くに着いた標尺手 → 観測者がのぞく・書く（時間がたつディゾルブ）", "N・S の実音を少し前に。曲は C のあたたかい所", "ミリを見のがさない集中と、二人で進むこと"),
    ("B11 締め", "29–32小節　70.8–80.9", [lambda: tag(frame("K", 12.0, None, MK + [TRUCK[12.0], HELMET_85]), "K 8.53–15.5 全画面"), sk_end],
     "N14 71.18「ふたりで、道の“横顔”をはかる。それが、水準測量です。」", "最後の一打で二人の引き、ゆっくり寄る（実写の上に線は引かない）。文字「道の “横顔” をはかる」。78.37 から終わりの画 → アイコン → 最後0.5秒は黒", "曲の最後の和音のばし。アイコンに戻る所で鉄琴（小）", "誇りと余韻。看板の絵と章扉の形で閉じる"),
]

def sk_door_free():   # B5 の12小節：読む所の印
    im, d = paper()
    obj, sx = side_base(d, rod=True)
    d.line([(sx - 10, obj[1]), (sx + 18, obj[1])], fill=ORANGE, width=5)
    label(d, (150, 60), "水平な一本の線", 26)
    label(d, (sx + 24, obj[1] + 10), "← 読む所", 18, fill=ORANGE)
    return im

PAD, FS, LH = 20, 26, 36
FIELDS = [("ナレ", 3), ("画・文字", 4), ("音", 5), ("目的", 6)]

def wrap(s, f, width, d):
    lines, cur = [], ""
    for ch in s:
        if d.textlength(cur + ch, font=f) > width:
            lines.append(cur); cur = ch
        else:
            cur += ch
    return lines + [cur]

def card(row, d0):
    f = font(FS); lab = font(22)
    blocks = []
    for name, k in FIELDS:
        blocks.append((name, wrap(row[k], f, W - 2 * PAD - 110, d0)))
    h = 52 + TH + 14 + sum(len(b) * LH + 10 for _, b in blocks) + 18
    im = Image.new("RGB", (W, h), "white"); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 46], fill=NAVY)
    d.text((PAD, 8), row[0], font=font(30), fill="white"); d.text((330, 12), row[1], font=font(26), fill="white")
    imgs = [g() for g in row[2]]
    if len(imgs) == 1:
        im.paste(imgs[0], ((W - TW) // 2, 52))
    else:
        for i, g in enumerate(imgs[:2]): im.paste(g, (PAD // 2 + i * (TW + PAD), 52))
    y = 52 + TH + 14
    for name, lines in blocks:
        d.rectangle([PAD, y + 2, PAD + 96, y + 32], fill="#E9EDF2"); d.text((PAD + 8, y + 5), name, font=lab, fill=NAVY)
        for k, line in enumerate(lines):
            d.text((PAD + 110, y + k * LH), line, font=f, fill=INK)
        y += len(lines) * LH + 10
    d.line([(0, h - 4), (W, h - 4)], fill="#BBBBBB", width=3)
    return im

def page(rows, n, of):
    tmp = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    cards = [card(r, tmp) for r in rows]
    H = 120 + sum(c.height for c in cards)
    im = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(im)
    d.text((PAD, 14), f"水準測量パート 絵コンテ v6.1　{n}/{of}", font=font(34), fill=INK)
    d.text((PAD, 62), "32小節・80.9秒・曲 V6d（8小節で止め）。コマは元の素材（ぼかし済み）、", font=font(22), fill="#555")
    d.text((PAD, 90), "図は手描きのスケッチ。秒は完成尺。社外に出さない。", font=font(22), fill="#555")
    y = 120
    for c in cards:
        im.paste(c, (0, y)); y += c.height
    return im

groups = [ROWS[0:4], ROWS[4:8], ROWS[8:12]]
for n, rows in enumerate(groups, 1):
    p = OUT / f"storyboard_v6_p{n}.jpg"
    page(rows, n, len(groups)).save(p, quality=88)
    print(p)
