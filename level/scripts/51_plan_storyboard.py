"""計画段階の絵コンテ（ゲート1 用）を、元の素材のコマ（ぼかし済み）と手描きのスケッチから作る。
版を2つ持つ：v7.2「高さの目印をつくる」（既定。plan/editing_v7.md・content_v7.md の写し）と v6.1「ふたりで描く、道の横顔」（editing_v6.md）。
v7.1 の版は git の履歴（67b914e）、v5 の版は 04608e5 にある。
使い方：python3 scripts/51_plan_storyboard.py <出力フォルダ> [v7|v6]
  例: python3 scripts/51_plan_storyboard.py /mnt/project-files/level/storyboard_v7/ v7
出力：storyboard_<版>_p1.jpg〜（素材から作った画像なので、リポジトリには入れない）。幅 1080 の縦長＝スマホで縦に読む。
      v7 のときは、ゲート報告用に compare_v5_12rows.jpg（v5 との12行の対応表）と changed_3.jpg（変えた所の絵3コマ）も。
"""
import pathlib, subprocess, sys, io, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = pathlib.Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
SRC = {k: ROOT / f"source/{v}.mp4" for k, v in {"S": "S_sueru", "K": "K_kansoku", "N": "N_nozoki"}.items()}
FONT = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
NAVY, ORANGE, PAPER, GRID, INK, FAINT = "#1F3A5F", "#E8742A", "#F4F1EA", "#E2DCCD", "#14202E", "#B9C1CC"
PAPER7, GLOW = "#FBF8F2", "#FFD9BC"
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

GRID_ON = True
def paper():
    """v6 は方眼。v7 は方眼なしの無地（v5 の方眼の図と見た目を分ける）。"""
    im = Image.new("RGB", (TW, TH), PAPER if GRID_ON else PAPER7); d = ImageDraw.Draw(im)
    if GRID_ON:
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
    d.text((PAD, 14), f"水準測量パート 絵コンテ {TITLE}　{n}/{of}", font=font(34), fill=INK)
    d.text((PAD, 62), "32小節・80.9秒・曲 V6d（8小節で止め）。コマは元の素材（ぼかし済み）、", font=font(22), fill="#555")
    d.text((PAD, 90), "図は手描きのスケッチ。秒は完成尺。社外に出さない。", font=font(22), fill="#555")
    y = 120
    for c in cards:
        im.paste(c, (0, y)); y += c.height
    return im


# ======================= v7「高さの目印をつくる」 =======================
def observer_r(d, x, g, h, color=NAVY, w=3):
    """観測者（右向き）：機械の左に回って、うしろのものさしをのぞく。"""
    hip = (x - h * .05, g - h * .50); sh = (x + h * .18, g - h * .78); hr = h * .07
    d.line([(x + h * .05, g), hip], fill=color, width=w); d.line([(x - h * .12, g), hip], fill=color, width=w)
    d.line([hip, sh], fill=color, width=w + 2)
    d.ellipse([sh[0] + h * .20 - hr, sh[1] - hr * 2.2, sh[0] + h * .20 + hr, sh[1] - hr * 0.2], outline=color, width=w)
    d.line([sh, (sh[0] + h * .10, g - h * .62)], fill=color, width=w)

def mark(d, x, y, col=NAVY, s=11, fill=True):   # □ に点（高さの目印）
    d.rectangle([x - s, y - s, x + s, y + s], outline=col, width=3, fill=(col if fill else None))
    d.ellipse([x - 3, y - 3, x + 3, y + 3], fill="white" if fill else col)

def staff(d, x, foot, top, col=NAVY, w=3, dash=False):
    if dash:
        for y in range(int(top), int(foot), 10): d.line([(x - 3, y), (x - 3, min(y + 5, foot))], fill=col, width=2); d.line([(x + 3, y), (x + 3, min(y + 5, foot))], fill=col, width=2)
    else:
        d.rectangle([x - 3, top, x + 3, foot], outline=col, width=2)

def lit(d, x, y0, y1, col):   # ものさしの「線から下」が灯る（別の棒は足さない）
    d.line([(x, y0), (x, y1)], fill=GLOW, width=14); d.line([(x, y0), (x, y1)], fill=col, width=6)


def box(d, x, y, col, s=7, dot=False, fill=False):   # □（dot=True は出発の水準点＝□に点。新しい目印は点なし）
    d.rectangle([x - s, y - s, x + s, y + s], outline=col, width=3, fill=(col if fill else "white"))
    if dot: d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=("white" if fill else col))

def stand(d, x, g, h, color=NAVY, w=3):
    """立っている人（手前へ一歩さがった観測者）。足もと (x,g)、背 h。"""
    hr = h * .08; top = g - h
    d.ellipse([x - hr, top, x + hr, top + 2 * hr], outline=color, width=w)
    d.line([(x, top + 2 * hr), (x, g - h * .45)], fill=color, width=w + 1)
    d.line([(x, g - h * .45), (x - h * .08, g)], fill=color, width=w); d.line([(x, g - h * .45), (x + h * .08, g)], fill=color, width=w)
    d.line([(x, top + h * .28), (x - h * .10, g - h * .50)], fill=color, width=w); d.line([(x, top + h * .28), (x + h * .10, g - h * .50)], fill=color, width=w)

def dot(d, x, y, col=ORANGE, r=5):
    d.ellipse([x - r, y - r, x + r, y + r], fill=col)

def arrow(d, a, b, col, w=3):
    d.line([a, b], fill=col, width=w)
    ang = math.atan2(b[1] - a[1], b[0] - a[0]); L = 10
    p1 = (b[0] - L * math.cos(ang - .45), b[1] - L * math.sin(ang - .45)); p2 = (b[0] - L * math.cos(ang + .45), b[1] - L * math.sin(ang + .45))
    d.polygon([b, p1, p2], fill=col)

# ---- B5 の真横の図（完成画面 1920×1080 を 0.2708 倍。まえ x 640→173、機械 1180→320、うしろ 1720→466、目線 y 515→139）----
SX = TW / 1920
FX, LX, BX, LY, GB, GF = 173, 320, 466, 139, 233, 252     # まえ・機械・うしろの x、目線の y、うしろ／まえの地面
def side72(d, ground=True, front_holder=True):
    if ground: d.line([(487, GB), (LX, GB), (FX, GF), (32, 253)], fill=NAVY, width=3)
    level(d, LX, GB, 94)
    if front_holder:
        holder(d, 147, GF, 108, staff=False); staff(d, FX, GF, GF - 103)

def sk72_back():
    im, d = paper(); side72(d)
    staff(d, BX, GB, GB - 149, NAVY, dash=True)                    # 標尺1本なら点線の外形（2本なら実線）
    box(d, BX, GB + 2, NAVY, 7, dot=True, fill=True)
    observer_r(d, 252, GB, 109)
    d.line([(309, LY), (BX - 3, LY)], fill=NAVY, width=3)          # うしろへの目線：その場で現れる（のびない）
    lit(d, BX, LY, GB - 6, NAVY)
    d.ellipse([BX - 15, GB - 13, BX + 15, GB + 17], outline=GLOW, width=4)
    label(d, (14, 14), "□とうしろ → 0.4秒の弧で回る → うしろの目線（紺）", 18, box=True)
    label(d, (150, 96), "水平な一本の線", 22)
    label(d, (392, 196), "水準点", 18)
    label(d, (190, 262), "機械は二本のまんなか", 16, fill=INK)
    return tag(im, "23.0–25.9")

def sk72_front():
    im, d = paper(); side72(d)
    staff(d, BX, GB, GB - 149, NAVY, dash=True); lit(d, BX, LY, GB - 6, NAVY)
    box(d, BX, GB + 2, NAVY, 7, dot=True, fill=True)
    d.line([(331, LY), (FX + 3, LY)], fill=ORANGE, width=3)        # まえへの目線（オレンジ）
    d.line([(LX, LY), (BX - 3, LY)], fill=NAVY, width=3)           # 機械からの一本の線
    stand(d, 392, 262, 112)                                        # 手前へ一歩さがって立つ（頭は線の下）
    for x in (372, 384): dot(d, x, 272, NAVY, 2)
    label(d, (14, 14), "戻ってまえの目線（オレンジ）→ 手前へ一歩", 18, box=True)
    label(d, (286, 262), "一歩さがる", 16, fill=INK)
    return tag(im, "26.1–27.2")

def sk72_climb():
    im, d = paper(); side72(d)
    staff(d, BX, GB, GB - 149, FAINT, dash=True)
    box(d, BX, GB + 2, NAVY, 7, dot=True, fill=True)
    d.line([(FX + 3, LY), (BX - 3, LY)], fill=FAINT, width=2)
    stand(d, 392, 262, 112, FAINT)
    arrow(d, (BX + 14, GB - 8), (BX + 14, LY + 6), ORANGE, 4)
    arrow(d, (BX - 10, LY - 12), (FX + 12, LY - 12), ORANGE, 4)
    arrow(d, (FX - 14, LY + 6), (FX - 14, GF - 6), ORANGE, 4)
    dot(d, FX, GF - 4, ORANGE, 7)
    dotted(d, (BX - 8, GB), (FX + 6, GB), NAVY, 2, 8)               # うしろの地面の高さ
    d.line([(FX, GB), (FX, GF)], fill=GLOW, width=18); d.line([(FX, GB), (FX, GF)], fill=ORANGE, width=7)
    label(d, (392, 52), "①のぼって", 20, fill=ORANGE)
    label(d, (250, 104), "②わたって", 20, fill=ORANGE)
    label(d, (20, 150), "③おりる", 20, fill=ORANGE)
    label(d, (14, 262), "段差が光る＝まえが低い", 17, fill=ORANGE)
    label(d, (14, 14), "高さのしるしが、のぼって、わたって、おりる", 18, box=True)
    return tag(im, "27.2–29.7")

# ---- B7・B9：5つの立つ場所（まえ＝左）。人は描かない ----
ST72 = [(460, 206), (363, 222), (265, 214), (168, 196), (70, 180)]   # S0（紺の□に点）→ S4（新しい□、点なし）
LV72 = [(412, 150), (314, 158), (216, 148), (119, 130)]              # 機械の x と目線の y（L1〜L4）
def ground72(d, col=NAVY):
    d.line([(515, 204)] + ST72 + [(8, 178)], fill=col, width=3)

def hop(d, i, col, w=3, off=0):
    (xa, ga), (xb, gb), (_, ly) = ST72[i], ST72[i + 1], LV72[i]
    d.line([(xa + off, ga - 4), (xa + off, ly + off), (xb + off, ly + off), (xb + off, gb - 4)], fill=col, width=w)

def sk72_relay():
    im, d = paper(); ground72(d)
    box(d, *ST72[0], NAVY, 8, dot=True, fill=True)
    hop(d, 0, "#F2C7A6", 2)
    for i, (x, ly) in enumerate(LV72):
        level(d, x, (ST72[i][1] + ST72[i + 1][1]) // 2, (ST72[i][1] + ST72[i + 1][1]) // 2 - ly + 1, NAVY if i == 3 else FAINT, 2)
    for x, g in ST72[1:4]: staff(d, x, g, g - 90, FAINT, dash=True)
    staff(d, ST72[4][0], ST72[4][1], ST72[4][1] - 90, NAVY)
    for i in (1, 2, 3): hop(d, i, ORANGE, 3)
    for x, g in ST72[2:4]: dot(d, x, g - 6, ORANGE, 5)
    box(d, ST72[4][0], ST72[4][1] + 2, ORANGE, 9)
    dot(d, ST72[4][0], ST72[4][1] - 6, ORANGE, 5)
    label(d, (14, 14), "3回「のぼって・わたって・おりる」。新しい□", 18, box=True)
    label(d, (190, 54), "となりへ、となりへ", 22)
    for (x, g), s in zip(ST72[2:5], ("36.66", "37.92", "39.82")): label(d, (x - 22, g + 10), s, 14, fill=ORANGE)
    label(d, (20, 252), "新しい目印（□、点なし）", 17, fill=ORANGE)
    label(d, (380, 236), "わかっている□", 16)
    return tag(im, "35.4–43.0")

def sk72_return():
    im, d = paper(); ground72(d, FAINT)
    box(d, *ST72[0], NAVY, 8, dot=True, fill=True)
    for i, (x, ly) in enumerate(LV72):
        level(d, x, (ST72[i][1] + ST72[i + 1][1]) // 2, (ST72[i][1] + ST72[i + 1][1]) // 2 - ly + 1, FAINT, 2)
    for x, g in ST72[1:5]: staff(d, x, g, g - 90, FAINT, dash=True)
    for i in range(4): hop(d, i, "#F2C7A6", 2)
    for i in range(4): hop(d, i, NAVY, 3, off=-5)
    d.ellipse([ST72[0][0] - 17, ST72[0][1] - 33, ST72[0][0] + 17, ST72[0][1] + 1], outline=ORANGE, width=3)
    dotted(d, (ST72[0][0] - 12, ST72[0][1] + 18), (ST72[4][0] + 16, ST72[4][1] + 18), NAVY, 3, 10)
    arrow(d, (ST72[4][0] + 40, ST72[4][1] + 18), (ST72[4][0] + 16, ST72[4][1] + 18), NAVY, 3)
    box(d, ST72[4][0], ST72[4][1] + 2, NAVY, 9, fill=True)
    label(d, (14, 14), "帰り（紺、逆向き）→ 重なる → 紺の線が左へ", 18, box=True)
    label(d, (392, 232), "合えば", 18, fill=ORANGE)
    label(d, (14, 252), "高さの目印（オレンジ→紺）", 19)
    return tag(im, "50.6–52.5")

def sk72_road():
    im, d = paper()
    f = lambda x: 196 + 22 * math.sin(x / 41) + 10 * math.sin(x / 17)
    d.line([(x, f(x)) for x in range(18, 408, 4)], fill=NAVY, width=2)
    road = lambda x: 196 + 0.045 * (410 - x) - 4
    d.line([(x, road(x)) for x in range(18, 410, 4)], fill=NAVY, width=8)
    box(d, 420, road(410), NAVY, 9, fill=True)
    for x in range(18, 406, 2):
        if (f(x) - road(x)) * (f(x + 2) - road(x + 2)) < 0: d.ellipse([x - 5, road(x) - 5, x + 5, road(x) + 5], outline=ORANGE, width=2)
    label(d, (14, 14), "□から左へ：地面の線と、それを横切る道の線", 18, box=True)
    label(d, (150, 128), "新しい道", 26)
    label(d, (14, 252), "（○＝交わる所。道は地面に浮かせない）", 16, fill=INK)
    return tag(im, "53.1–58.1")

def sk7_end():
    im, d = paper()
    box(d, 160, 150, NAVY, 40, fill=True)
    d.line([(230, 150), (330, 150)], fill=INK, width=3); d.polygon([(330, 140), (330, 160), (348, 150)], fill=INK)
    d.ellipse([370, 115, 440, 185], outline=ORANGE, width=5); d.rectangle([400, 128, 410, 172], outline=ORANGE, width=3)
    label(d, (14, 14), "終わりの画：紺の□（点なし）が縮んでアイコンへ", 18, box=True)
    label(d, (60, 236), "“高さの目印” をつくる", 28)
    return tag(im, "78.4–80.4")

def ov_title7(im):
    band = Image.new("RGBA", (272, 120), (20, 32, 46, 150)); im.paste(band, (0, 8), band)   # x 1000 より左だけ
    d = ImageDraw.Draw(im)
    label(d, (16, 16), "水準測量", 44, fill="white"); label(d, (18, 72), "“高さの目印”をつくる", 22, fill="white")
    return im

def sk_trace7():
    im = frame("K", 7.82, KW132, MK_ALL)
    d = ImageDraw.Draw(im); s = TW / 1455
    P = lambda x, y: ((x - 465) * s, (y - 60) * s)
    d.line([P(735, 630), P(1013, 878)], fill="white", width=4)
    for fx, fy in ((720, 830), (1075, 878), (1150, 878)): d.line([P(1085, 400), P(fx, fy)], fill="white", width=3)
    d.rectangle([*P(665, 405), *P(748, 685)], outline="white", width=3)
    d.rectangle([*P(1090, 278), *P(1430, 878)], outline="white", width=3)
    label(d, (14, 14), "なぞる：外形の線だけ（顔は描かない）", 19, box=True)
    return tag(im, "18.96 止め → 20.2 なぞる")

def ov_lab(im, xy, s, to):
    d = ImageDraw.Draw(im); label(d, xy, s, 20, box=True); d.line([(xy[0] + 20, xy[1] + 28), to], fill=NAVY, width=2)
    return im

K115 = (125, 70, 1670, 939)
M1P = M1 + [(808, 312, 845, 340)]                     # S 56–74：止まっている軽自動車のナンバー
CYC = (330, 205, 400, 300)                            # S 177–179.5：奥の自転車の人（本番は追いかける）
ROWS_V7 = [
    ("B1 章扉", "1小節　0.0–2.5", [lambda: tag(sk_door(), "1.26 灯る")],
     "N1a 0.30「測量部門の仕事のひとつ、」", "章扉（共通）。3拍目で水準のアイコン（標尺）だけ灯る", "章扉の灯り（共通）", "部門の中の1作業"),
    ("B2 据える", "2–3小節　2.5–7.6", [lambda: tag(frame("S", 49.6, (70, 82, 707, 398), M1), "S 48.58– 実時間"), lambda: tag(ov_title7(frame("S", 53.3, (70, 82, 707, 398), M1)), "6.95 載る＝題")],
     "N1b 7.25「水準測量です。」（題の0.3秒あと）", "ケースを開ける → 持ち上げる → 6.95 に載る。題とサブ「“高さの目印”をつくる」（7.15–11.80）は三脚の左の空だけ", "載る音（実音）。曲 −12 dB", "人の手が仕事を始める所から"),
    ("B3 前置き", "4–5小節　7.6–12.6", [lambda: tag(frame("S", 66.0, (170, 40, 678, 381), M1P), "S 56–74 4.75倍（実時間と比べる）"), lambda: tag(frame("N", 2.6, (600, 180, 1200, 675)), "N 2.0–3.3")],
     "N2 8.99「道をつくる前に、高さの目印をつくります。」（「高さの目印」10.51 はサブが出ている間）", "整準（頭を下げて気泡を見る）→ 目を当てる寄り。文字はサブだけ（ラベル「レベル」は B6 へ）", "道の環境音", "何のための仕事かを先に言う"),
    ("B4 ふたり", "6–8小節　12.6–20.2", [lambda: tag(frame("K", 3.0, None, MK + [TRUCK[3.0]]), "K 1.5 全画面から"), lambda: tag(ov_lab(frame("K", 7.82, KW132, MK_ALL), (40, 30), "標尺", (93, 120)), "1.32倍 → K 7.82 で止める")],
     "N3 13.44「のぞく先に、仲間がひとり。ものさしを、ゆらさずに立てています。」（〜19.14）", "歩いて来てかがむ。15.17 に「標尺」（撮り足し③が来たら顔に）。18.96 で止まる", "17.70 に曲が止まる → 声の終わりを止め絵の上で。1秒は現場の音だけ", "二人目の人と、その仕事"),
    ("B5 看板 1/3", "9–10小節　20.2–23.0", [sk_trace7, lambda: tag(sk_stage1(), "21.3–22.3")],
     "N4 21.10「目線は、まっすぐ水平。」（20.2–21.1 は声なしでなぞる）", "なぞる → 溶ける＋① 標尺手だけが同じ大きさに → ② 地面が先に水平（「まっすぐ」22.27）、人と機械が着地。文字「水平な一本の線」22.32–", "曲で一番強い頭（9小節）", "1本目の「倒れる」と対：たたんで真横に"),
    ("B5 看板 2/3", "10–11小節　23.0–27.2", [sk72_back, sk72_front],
     "N5 23.60「うしろは、高さのわかる目印。」（「目印」25.69）", "□とうしろのものさし（1本なら点線の外形）→ 観測者が0.4秒の弧で回る → うしろの目線（紺）がその場で現れる → 25.91 □が灯る、「水準点」→ 戻ってまえの目線（オレンジ）→ 手前へ一歩さがる", "目線には音なし（光線に見せない）", "わかっている目印から読む"),
    ("B5 看板 3/3", "11–12小節　26.5–30.3", [sk72_climb],
     "N6 26.47「高さが、のぼって、わたって、おりる。」（27.23／28.18／29.13）", "しるし（オレンジの小さな丸）が、うしろのものさしをのぼり、水平な線をわたり、まえのものさしをおりる。29.70 段差が光る（おりるほうが長い）", "鉄琴 C6（29.70）だけ", "しくみ：のぼって、わたって、おりる"),
    ("B6 こえる", "13–14小節　30.3–35.4", [lambda: tag(ov_lab(frame("S", 168.8, None, M2), (300, 40), "レベル", (300, 128)), "S 165.67–170.73 全画面・実時間")],
     "N7 31.60「ものさしが、機械をこえて、まえへ。」（「こえて」33.31–33.88）", "標尺手が右手前からあらわれ、33.87 に機械の横を通ってまえへ。ラベル「レベル」30.70–32.45", "足音・道の音（実音）", "実写で、ものさしが次の場所へ"),
    ("B7 運ぶ", "15–17小節　35.4–43.0", [sk72_relay],
     "N8 35.79「となりへ、となりへ、高さを運びます。」　N9 39.42「たどり着いた所に、新しい、高さの目印。」", "道具だけで立ち替わり（機械とものさしが交互にこえる）→ そのたびに、のぼって・わたって・おりる。着地 36.66／37.92／39.82 → 42.34 新しい□（オレンジ、点なし）", "鉄琴：着地で D・G・A、□で和音", "なるほど：高さを、となりへ運ぶ"),
    ("B8 書く", "18–19小節　43.0–48.0", [lambda: tag(frame("K", 17.0, (720, 0, 1200, 675), MK + [TRUCK[17.0], SHOP_17, HELMET_17]), "K 16.2–21.26 1.6倍（短くする案と比べる）")],
     "N10 43.38「読んだ長さは、その場で手帳に。」", "立って黄色い手帳に書く手。社名・看板・ヘルメットの印刷はぼかす", "ペンの音（ごく小）", "読んだ長さは人の手で残る"),
    ("B9 確かめる", "20–21小節　48.0–53.1", [lambda: tag(frame("S", 178.0, None, M2 + [CYC]), "20小節：S 177.0–179.53 実時間"), sk72_return],
     "N11 50.15「帰りもはかって、合えば、できあがり。」（「合えば」51.67、「できあがり」52.43）", "実写で観測者がのぞく → 50.56 図：道具はうすく止めて置き、紺のしるしが逆向きに → 51.82 右の□で重なる → 紺の線が左へ走る → 52.46 新しい□がオレンジ→紺。「高さの目印」", "曲のつなぎ目（48.03）。鉄琴は重なりの E6 だけ", "ていねいさ：行きと帰りで確かめる"),
    ("B10 使われる", "22–23小節　53.1–58.1", [sk72_road],
     "N12 53.78「この目印をもとに、道がつくられます。」", "紺の□から左へ、地面の線 → それを横切る新しい道の線（55.62–56.88）。「新しい道」55.19–。撮り足し①②が来たら頭の1.26秒に目印の実物", "鉛筆の音（ごく小）", "なぜ大事か：この目印をもとに道がつくられる"),
    ("B11 人", "24–28小節　58.1–70.8", [lambda: tag(frame("N", 6.0, (600, 196, 1200, 675)), "N 3.3–10.25"), lambda: tag(frame("S", 82.4, (170, 40, 678, 381), M1 + [(500, 258, 552, 296)]), "S 172–175.2 → S 81.0–83.53 実時間")],
     "（2.5秒は声なし）N13 60.60「小さな違いも、見のがさないように。」　N14 65.50「ふたりで息を合わせて、道にそって進みます。」", "ピントのつまみを回す寄り → 遠くに着いた標尺手（全画面）→ 人のいない機械と、奥を流れる車（実時間）", "N・S の実音を少し前に", "集中と、二人で進むこと"),
    ("B12 締め", "29–32小節　70.8–80.9", [lambda: tag(frame("K", 12.0, K115, MK + [HELMET_85]), "K 8.53–16.12 等速、1.15→1.00"), sk7_end],
     "N15 71.18「ほかの測量や工事が使う、“高さの目印”をつくる。それが、水準測量です。」", "最後の一打で二人の引き（実写の上に線なし）。文字 73.16–。78.37 から紺の□ → アイコン → 黒", "最後の和音のばし。アイコンで鉄琴（小）", "誇りと余韻。1本目と同じ形で閉じる"),
]

# ---- ゲート報告の1枚目：v5 との12行の対応表 ----
CMP = [("B0 章扉", "B1 章扉", "同じ", "共通の章扉"),
       ("B2 据える・載る（早回し＋実時間）", "B2 据える（実時間の1本）", "同じ画", "早回しをやめ、題のサブを「“高さの目印”をつくる」に"),
       ("B2 整準／B5d N の目の寄り", "B3 前置き（整準 → 目の寄り）", "同じ画", "声で先に「道をつくる前に、高さの目印をつくります」"),
       ("B5a K の二人、ラベル", "B4 ふたり（K、ラベル「標尺」）", "同じ", "止め絵で曲が止まる"),
       ("B5b〜B6 横の図、深いほうが低い（数字・水）", "B5 看板：のぼって・わたって・おりる", "変えた", "出発の□から読む。数字・水・クイズなし。差は動きで見せる"),
       ("B7a 右の S「標尺の人が先へ」", "B6 こえる（S 実時間）", "同じ画", "声「ものさしが、機械をこえて、まえへ」"),
       ("B9c「となりへつなぐ」", "B7 運ぶ", "変えた", "3回「のぼって・わたって・おりる」。新しい□が灯る"),
       ("B7a 左の K「野帳に書く」", "B8 書く（K）", "同じ", "短くする案を試作で比べる"),
       ("B7b 行き・帰りの数字", "B9 確かめる（実写 → 図）", "変えた", "数字なし。重なる → 紺の線 → □がオレンジ→紺"),
       ("B8「高さをもとに…つくられます」", "B10 使われる", "変えた", "地面を横切る道の線。撮り足しの目印の実物"),
       ("B9a N の顔の寄り", "B11 人（N の寄り → S → S 81）", "同じ画", "人のいない機械と流れる車を足した"),
       ("B9b K 全画面 → 紙 → アイコン", "B12 締め（K の引き → □ → アイコン）", "同じ形", "締めの言葉と、紺の□（高さの目印）")]

def compare12():
    f, fs = font(26), font(23)
    RH = 128; H = 190 + len(CMP) * RH + 110
    im = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(im)
    d.text((PAD, 16), "v5 と v7.2 の対応（12行）", font=font(36), fill=INK)
    d.text((PAD, 66), "拍の並びと実写の画は、7行が v5 と同じ。変えたのは5行（しくみ・運ぶ・確かめる・使われる、", font=font(21), fill="#555")
    d.text((PAD, 94), "そして中身：水・数字・クイズ・下水をやめた）。撮り足しが来れば B4・B10・B12 に新しい画が入る。", font=font(21), fill="#555")
    y = 140
    d.rectangle([0, y, W, y + 40], fill=NAVY)
    for x, s in ((PAD, "v5（前に見せた版）"), (430, "v7.2"), (900, "")): d.text((x, y + 6), s, font=font(24), fill="white")
    y += 48
    for i, (a, b, k, why) in enumerate(CMP, 1):
        bg = "#FFF3EA" if k == "変えた" else "white"
        d.rectangle([0, y, W, y + RH - 4], fill=bg)
        d.text((PAD, y + 8), f"{i}", font=font(28), fill=NAVY)
        for k2, line in enumerate(wrap(a, fs, 330, d)[:2]): d.text((PAD + 50, y + 10 + k2 * 30), line, font=fs, fill="#666")
        for k2, line in enumerate(wrap(b, f, 530, d)[:2]): d.text((430, y + 8 + k2 * 32), line, font=f, fill=INK)
        col = ORANGE if k == "変えた" else "#7A8696"
        tw = d.textlength(k, font=font(22))
        d.rectangle([W - PAD - tw - 16, y + 10, W - PAD, y + 42], fill=col); d.text((W - PAD - tw - 8, y + 13), k, font=font(22), fill="white")
        d.text((430, y + RH - 40), "→ " + why, font=font(21), fill=(ORANGE if k == "変えた" else "#444"))
        d.line([(0, y + RH - 4), (W, y + RH - 4)], fill="#DDDDDD", width=2)
        y += RH
    d.text((PAD, y + 14), "同じ 7／変えた 5。変えた所の絵は changed_3.jpg に。", font=font(22), fill=INK)
    return im

# ---- 変えた所の絵3コマ ----
def sk72_shoot():
    im, d = paper()
    d.rectangle([30, 60, 250, 215], outline=ORANGE, width=3)
    for x in range(30, 250, 14): d.line([(x, 60), (x + 7, 60)], fill="white", width=3)
    label(d, (48, 100), "撮り足し①②", 22, fill=ORANGE)
    label(d, (48, 134), "目印（くぎ・鋲・", 18, fill=INK); label(d, (48, 158), "ペンキ）の寄り／", 18, fill=INK)
    label(d, (48, 182), "標尺の底を立てる手元", 18, fill=INK)
    arrow(d, (262, 145), (330, 145), INK, 3)
    box(d, 400, 145, NAVY, 24, fill=True)
    label(d, (344, 190), "→ 紺の□へ", 18)
    y0 = 232; d.line([(20, y0), (500, y0)], fill=INK, width=2)
    for t, s, c in ((15.17, "③顔 B4", ORANGE), (53.09, "①② B10", ORANGE), (70.78, "③顔 B12", ORANGE)):
        x = 20 + 480 * t / 80.894; d.line([(x, y0 - 8), (x, y0 + 8)], fill=c, width=4); label(d, (x - 30, y0 + 10), s, 15, fill=c)
    label(d, (14, 14), "撮り足しの目印の実物を入れる位置", 18, box=True)
    return tag(im, "53.09–54.35 ほか")

def changed3():
    rows = [("1 しくみ：のぼって・わたって・おりる（B5、27.2–29.7）", sk72_climb(),
             ["v5：数字の差と「深いほうが低い」。", "v7.2：高さのしるしが、□のうしろのものさしを", "のぼり、水平な線をわたり、まえをおりる。", "おりるほうが長い＝まえが低い。数字なし。"]),
            ("2 □がオレンジ→紺（B9、50.6–52.5）", sk72_return(),
             ["v5：行き・帰り・差の数字。", "v7.2：帰りのしるしが右の□で重なる（合えば）", "→ 紺の線が左へ走る → 新しい□が紺に", "（「できあがり」）。わかっている高さになる。"]),
            ("3 撮り足しの目印の実物を入れる位置", sk72_shoot(),
             ["素材には目印の実物がない（v5 も同じ）。", "5分の撮り足しで：①目印の寄り ②標尺を立てる手元", "→ B10 の頭。③標尺手の顔 → B4・B12 の頭。", "来なければ、紙の上の□だけになる。"])]
    f = font(23); RH = 52 + TH + 20
    im = Image.new("RGB", (W, 100 + len(rows) * RH), "white"); d = ImageDraw.Draw(im)
    d.text((PAD, 18), "v7.2 で変えた所（絵3コマ）", font=font(34), fill=INK)
    d.text((PAD, 62), "左が絵コンテのスケッチ、右がその説明。秒は完成尺。", font=font(22), fill="#555")
    y = 100
    for title, sk, lines in rows:
        d.rectangle([0, y, W, y + 44], fill=NAVY); d.text((PAD, y + 8), title, font=font(26), fill="white")
        im.paste(sk, (PAD // 2, y + 52))
        wl = [w_ for line in lines for w_ in wrap(line, f, W - TW - PAD - 24, d)]
        for k, line in enumerate(wl[:7]): d.text((TW + PAD + 4, y + 60 + k * 38), line, font=f, fill=INK)
        y += RH
    return im

VER = sys.argv[2] if len(sys.argv) > 2 else "v7"
if VER == "v6":
    TITLE, rows_all = "v6.1", ROWS
    groups = [ROWS[0:4], ROWS[4:8], ROWS[8:12]]
else:
    GRID_ON = False
    TITLE = "v7.2「高さの目印をつくる」"
    groups = [ROWS_V7[0:5], ROWS_V7[5:9], ROWS_V7[9:14]]
for n, rows in enumerate(groups, 1):
    p = OUT / f"storyboard_{VER}_p{n}.jpg"
    page(rows, n, len(groups)).save(p, quality=88)
    print(p)
if VER == "v7":
    for name, fn in (("compare_v5_12rows.jpg", compare12), ("changed_3.jpg", changed3)):
        p = OUT / name; fn().save(p, quality=90); print(p)
