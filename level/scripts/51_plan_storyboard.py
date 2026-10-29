"""計画段階の絵コンテ（ゲート1 用）を、元の素材のコマ（ぼかし済み）と手描きのスケッチから作る。
版を2つ持つ：v7「高さの目印をつくる」（既定。plan/editing_v7.md・content_v7.md の写し）と v6.1「ふたりで描く、道の横顔」（editing_v6.md）。v5 の版は git の履歴（04608e5）にある。
使い方：python3 scripts/51_plan_storyboard.py <出力フォルダ> [v7|v6] [v5 の版のスクリプト（diff_v5.jpg 用。省略可）]
  例: python3 scripts/51_plan_storyboard.py /mnt/project-files/level/storyboard_v7/ v7 /tmp/sb_v5.py
      （v5 の版は git show 04608e5:./scripts/51_plan_storyboard.py > /tmp/sb_v5.py で取り出す）
出力：storyboard_<版>_p1.jpg〜（素材から作った画像なので、リポジトリには入れない）。幅 1080 の縦長＝スマホで縦に読む。
      v7 のときは diff_v5.jpg（v5 と何が違うかの3コマ）も。
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

def sk7_side2():
    im, d = paper()
    gr = [(510, 215), (300, 222), (20, 242)]
    d.line(gr, fill=NAVY, width=3)
    eye = (322, 152)
    level(d, 300, 222, 70)
    observer(d, 352, 222, 92)
    holder(d, 66, 242, 92, staff=False); staff(d, 96, 242, 120)
    dotted(d, eye, (100, 152))
    lit(d, 96, 152, 242, ORANGE)
    label(d, (14, 14), "② 真横の図に → 目からの点線（音なし）", 19, box=True)
    label(d, (120, 108), "水平な一本の線", 22)
    return tag(im, "22.3–24.4")

def sk7_fold3(caption=True):
    im, d = paper()
    gr = [(510, 215), (300, 222), (20, 242)]
    d.line(gr, fill=NAVY, width=3)
    level(d, 300, 222, 70)
    observer_r(d, 262, 222, 92)
    holder(d, 66, 242, 92, staff=False); staff(d, 96, 242, 120)
    # まえへの線は消す（観測者の体を通さない。まえの読みは標尺の灯りで残る）
    mark(d, 452, 215, NAVY, 10); staff(d, 452, 205, 95, NAVY, dash=True)
    dotted(d, (304, 152), (448, 152))
    lit(d, 452, 152, 205, NAVY); lit(d, 96, 152, 242, ORANGE)
    for y in range(215, 242, 1): pass
    dotted(d, (446, 215), (102, 215), NAVY, 2, 8)                      # うしろの地面の高さを横へ
    d.line([(96, 215), (96, 242)], fill=GLOW, width=22); d.line([(96, 215), (96, 242)], fill=ORANGE, width=8)
    label(d, (110, 252), "段差＝まえが低い", 19, fill=ORANGE)
    label(d, (420, 228), "水準点", 16)
    label(d, (380, 66), "あらわれる", 18, fill=NAVY)
    if caption: label(d, (14, 14), "③ うしろのものさしと□があらわれる", 19, box=True)
    return tag(im, "24.4–30.3")

ST = [(470, 200), (360, 225), (250, 215), (140, 195), (40, 185)]   # S0（紺の□）→ S4（新しい□）。まえ＝左
def ground7(d, col=NAVY):
    d.line([(515, 198)] + ST + [(5, 183)], fill=col, width=3)

def arc(d, a, b, col, w=3, up=34, dashed=True):
    pts = [(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t - up * math.sin(math.pi * t)) for t in [i / 16 for i in range(17)]]
    for i in range(0, 16, 2 if dashed else 1): d.line([pts[i], pts[i + 1]], fill=col, width=w)
    d.polygon([(b[0] - 6, b[1] - 12), (b[0] + 6, b[1] - 12), (b[0], b[1] - 3)], fill=col)

def sk7_relay():
    im, d = paper(); ground7(d)
    mark(d, *ST[0], NAVY, 10)
    for i, (x, g) in enumerate(ST[1:4], 1): staff(d, x, g, g - 110, FAINT, 2)
    for x in (415, 305, 195): level(d, x, 205, 60, FAINT, 2)          # 機械のいた所（うすく）
    level(d, 90, 195, 60)
    staff(d, 140, 195, 85); staff(d, 40, 185, 75)
    for i in range(1, 4): arc(d, (ST[i][0], ST[i][1] - 8), (ST[i + 1][0], ST[i + 1][1] - 8), ORANGE)
    for x, g in ST[1:4]: d.ellipse([x - 5, g - 13, x + 5, g - 3], fill=ORANGE)
    d.line([(40, 185), (40, 185)], fill=ORANGE); mark(d, 40, 185, ORANGE, 11)
    label(d, (14, 14), "尺取り3回（0.9／0.7／0.5秒）：印がとなりへ", 19, box=True)
    label(d, (190, 56), "となりへ、となりへ", 22)
    label(d, (14, 236), "新しい高さの目印", 19, fill=ORANGE)
    label(d, (380, 236), "わかっている□", 17)
    return tag(im, "35.4–43.0")

def sk7_return():
    im, d = paper(); ground7(d)
    mark(d, *ST[0], NAVY, 10)
    for x, g in ST[1:4]: staff(d, x, g, g - 60, FAINT, 2)
    for i in range(1, 4): arc(d, (ST[i][0], ST[i][1] - 6), (ST[i + 1][0], ST[i + 1][1] - 6), "#F2C7A6", 2, 26)     # 行き（うすく）
    for i in range(4, 0, -1): arc(d, (ST[i][0], ST[i][1] - 4), (ST[i - 1][0], ST[i - 1][1] - 4), NAVY, 3, 52)       # 帰り
    d.ellipse([ST[0][0] - 22, ST[0][1] - 22, ST[0][0] + 22, ST[0][1] + 22], outline=ORANGE, width=3)               # 重なる
    mark(d, 40, 185, NAVY, 11)
    d.rectangle([28, 60, 52, 84], outline=ORANGE, width=3); d.line([(56, 72), (78, 72)], fill=INK, width=2)
    d.polygon([(78, 66), (78, 78), (88, 72)], fill=INK); mark(d, 102, 72, NAVY, 11)
    label(d, (14, 14), "帰り：逆向き・2倍の速さ。重なって□が紺に", 19, box=True)
    label(d, (210, 100), "帰り", 20); label(d, (300, 148), "行き", 17, fill=ORANGE)
    label(d, (14, 236), "高さの目印（オレンジ→紺）", 19)
    return tag(im, "48.0–53.1")

def sk7_road():
    im, d = paper()
    f = lambda x: 205 + 16 * math.sin(x / 47) + 9 * math.sin(x / 19)
    d.line([(x, f(x)) for x in range(20, TW - 10, 6)], fill=NAVY, width=2)
    mark(d, 46, f(46), NAVY, 10)
    road = [(x, 175 - 0.06 * (x - 120) + 8 * math.sin(x / 160)) for x in range(120, TW - 10, 6)]
    dotted(d, (56, f(46) - 10), road[0], NAVY, 2, 8)
    d.line(road, fill=NAVY, width=8)
    label(d, (14, 14), "目印の高さから → 新しい道の線", 19, box=True)
    label(d, (300, 120), "道の高さ", 24)
    label(d, (14, 252), "（短く。横顔は小さく、主役は□と道の線）", 16, fill=INK)
    return tag(im, "53.1–58.1")

def sk7_end():
    im, d = paper()
    mark(d, 160, 150, NAVY, 40)
    d.line([(230, 150), (330, 150)], fill=INK, width=3); d.polygon([(330, 140), (330, 160), (348, 150)], fill=INK)
    d.ellipse([370, 115, 440, 185], outline=ORANGE, width=5); d.rectangle([400, 128, 410, 172], outline=ORANGE, width=3)
    label(d, (14, 14), "終わりの画：紺の□が縮んで水準アイコンへ", 19, box=True)
    label(d, (60, 236), "“高さの目印” をつくる", 28)
    return tag(im, "78.4–80.4")

def ov_title7(im):
    band = Image.new("RGBA", (272, 120), (20, 32, 46, 150)); im.paste(band, (0, 8), band)   # x 1000 より左だけ（批評 編7）
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

K115 = (125, 70, 1670, 939)
ROWS_V7 = [
    ("B1 章扉", "1小節　0.0–2.5", [lambda: tag(sk_door(), "1.26 灯る")],
     "N1a 0.30「測量部門の仕事のひとつ、」", "章扉（共通）。3拍目で水準のアイコン（標尺）だけ灯る", "章扉の灯り（共通）", "部門の中の1作業"),
    ("B2 据える", "2–3小節　2.5–7.6", [lambda: tag(frame("S", 49.6, (70, 82, 707, 398), M1), "S 48.58– 実時間"), lambda: tag(ov_title7(frame("S", 53.3, (70, 82, 707, 398), M1)), "6.95 載る＝題")],
     "N1b 6.65「水準測量です。」", "早回しなしの1本：ケースを開ける → 持ち上げる → 6.95 に載る。題とサブ「“高さの目印”をつくる」は三脚の左の空だけ（帯は x 1000 より左）", "前奏。載る音（実音）。曲 −12 dB", "人の手が仕事を始める所から（v5 の早回しと違う手ざわり）"),
    ("B3 水平に", "4–5小節　7.6–12.6", [lambda: tag(frame("S", 66.0, (170, 40, 678, 381), M1), "S 56–74 4.75倍（早回しはここだけ）"), lambda: tag(frame("N", 2.6, (600, 180, 1200, 675)), "N 2.0–3.3")],
     "N2 8.39「地面の高さを、はかります。まず、機械を水平に。」", "整準（頭を下げて気泡を見る）→ 目を当てる寄り。ラベル「レベル」", "道の環境音", "「高さ」を声で最初に言う。水平が線の前提"),
    ("B4 ふたり", "6–8小節　12.6–20.2", [lambda: tag(frame("K", 3.0, None, MK + [TRUCK[3.0]]), "K 1.5 全画面から"), lambda: tag(ov_label(frame("K", 7.82, KW132, MK_ALL), (40, 30), "標尺", (93, 120)), "1.32倍 → K 7.82 で止める")],
     "N3 13.04「のぞく先には、仲間がひとり。長いものさしを、ゆらさずに立てています。」（〜19.31）", "歩いて来てかがむ。15.17 にラベル「標尺」。18.96（K 7.82）で止まる＝1.26 秒の止め絵", "K の実音。17.70 に曲が止まる → 声の終わりを止め絵の上で聞き、0.9 秒は現場の音だけ", "二人目の人と、その仕事（ゆらさずに立てる）"),
    ("B5 看板 1/2", "9–10小節　20.2–25.3", [sk_trace7, lambda: tag(sk_stage1(), "21.3–22.3")],
     "N4 20.62「のぞく目は、まっすぐ水平な、一本の線。」", "一番強い頭でなぞる → 溶ける（21.02–21.65）と重ねて ① 標尺手だけが観測者と同じ大きさに（21.33–22.27）→ ② 地面が先に水平になり、人と機械が着地（22.27–22.99）", "曲で一番強い頭", "1本目の「倒れる」と対：たたんで真横に"),
    ("B5 看板 2/2", "10–12小節　22.8–30.3", [sk7_side2, sk7_fold3],
     "N5 24.44「うしろと、まえ。」　N6 26.60「まえが長ければ、そのぶん、地面は低い。」", "目からの点線がまえの標尺に届く 23.60（音なし）→ まえの標尺の線から下が灯る → ③ 観測者は機械の左へ回り、右にうしろのものさしと紺の□があらわれる（24.44）→ 線から下が灯る → 28.44 段差が光る", "鉄琴は段差の所だけ（C6、28.44）", "しくみ：水平な線で、となりとの高さの差"),
    ("B6 こえる", "13–14小節　30.3–35.4", [lambda: tag(frame("S", 168.8, None, M2), "S 165.67–170.73 全画面・実時間")],
     "N7 30.74「読んだら、うしろのものさしが、機械をこえて前へ。」（「こえて」≈33.6）", "観測者が機械をのぞく → 32.87 に標尺手が右手前からあらわれ、機械の横を通って前へ（33.9）", "足音・道の音（実音）", "実写の「うしろのものさしが前へ」"),
    ("B7 運ぶ", "15–17小節　35.4–43.0", [sk7_relay],
     "N8 35.79「となりへ、となりへ、高さを運びます。」　N9 39.42「たどり着いた所に、新しい、高さの目印。」", "紺の□（右）から左へ、尺取り3回。印が渡る 37.92／39.18／39.97 → 42.34 にオレンジの□が灯る。注記「高さを大きくした図です」", "鉄琴：渡るたびに1音（D・G・A）、灯る所で和音", "なるほど：高さを、となりへ運ぶ"),
    ("B8 書く", "18–19小節　43.0–48.0", [lambda: tag(frame("K", 17.0, (720, 0, 1200, 675), MK + [TRUCK[17.0], SHOP_17, HELMET_17]), "K 16.2–21.26 1.6倍")],
     "N10 43.38「読んだ長さは、その場で手帳に。」", "立って黄色い手帳に書く手。社名・看板・ヘルメットの印刷はぼかす", "ペンの音（ごく小）", "読んだ数字は人の手で残る"),
    ("B9 確かめる", "20–21小節　48.0–53.1", [sk7_return],
     "N11 48.43「帰りもはかって、ぴったり合えば、できあがり。」", "曲のつなぎ目で帰り：紺の印が左から右へ（2倍の速さ）→ 51.19（「合えば」）に紺の□で重なる → 51.82 に左の□がオレンジ→紺。ラベル「高さの目印」", "帰りの鉄琴は逆の順（G・D・C）、重なって E", "ていねいさ：新しい目印が「わかっている高さ」に"),
    ("B10 使われる", "22–23小節　53.1–58.1", [sk7_road],
     "N12 53.49「この目印の高さをもとに、道の高さが決まります。」", "□から引くと道の横顔、□から点線が新しい道の線へ → 56.88 に描き終わる。「道の高さ」", "鉛筆の音（ごく小）", "なぜ大事か：この目印から道の高さが決まる"),
    ("B11 人", "24–28小節　58.1–70.8", [lambda: tag(frame("N", 6.0, (600, 196, 1200, 675)), "N 3.3–10.25"), lambda: tag(frame("S", 85.0, (170, 40, 678, 381), M1 + [(565, 285, 610, 315)]), "S 172–175.2 → S 81–91 4倍")],
     "（2.5秒は声なし）N13 60.60「小さな違いも、見のがさないように。」　N14 65.50「ふたりで息を合わせて、道にそって進みます。」", "ピントのつまみを回す寄り → 遠くに着いた標尺手（全画面）→ 人のいない機械と、奥を流れる車（4倍）", "N・S の実音を少し前に", "集中と、まちのすぐ横の仕事"),
    ("B12 締め", "29–32小節　70.8–80.9", [lambda: tag(frame("K", 12.0, K115, MK + [HELMET_85]), "K 8.53–16.12 等速、1.15→1.00 に引く"), sk7_end],
     "N15 71.18「ほかの測量や工事が使う、“高さの目印”をつくる。それが、水準測量です。」", "最後の一打で二人の引き。B4 の逆に、寄りから全画面へ引いて閉じる（実写の上に線なし）→ 78.37 から紺の□ → アイコン → 黒", "最後の和音のばし。アイコンで鉄琴（小）", "誇りと余韻。1本目と同じ形で閉じる"),
]

def diff_v5(v5src):
    """ゲート報告用：v5 の絵コンテの絵（左）と v7（右）を3行で並べる。"""
    ns = {"__file__": str(ROOT / "scripts/51_plan_storyboard.py"), "__name__": "v5"}
    src = pathlib.Path(v5src).read_text().split("ROWS = [")[0]
    sys_argv = sys.argv; sys.argv = [sys.argv[0], str(OUT)]
    exec(src, ns); sys.argv = sys_argv
    rows = [("1 看板のしくみ", ns["section"]("water"), sk7_fold3(False),
             "v5：水がわいて「見えない水の面」。", "v7：うしろのものさしと□があらわれ、二本の読みの段差が光る。水・たとえなし。"),
            ("2 なるほど", ns["section"]("quiz"), sk7_relay(),
             "v5：数字のクイズ（1.234／1.834）。", "v7：数字なし。オレンジの印がとなりへ渡り、新しい高さの目印が灯る。"),
            ("3 確かめる", ns["overlay_check"](frame("K", 19.0, (720, 0, 1200, 675), MK + [TRUCK[17.0], SHOP_17, HELMET_17]).resize((480, 270))), sk7_return(),
             "v5：行き・帰り・差 3 mm（例）の数字。", "v7：帰りの印が重なり、□がオレンジ→紺（わかっている高さになる）。")]
    f = font(26); H = 110 + len(rows) * (52 + TH + 96)
    im = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(im)
    d.text((PAD, 16), "v5 と何が違うか（左＝前に見せた v5、右＝v7）", font=font(34), fill=INK)
    d.text((PAD, 64), "芯は「高さの目印をつくる」。水・クイズ・数字・下水を使わない。", font=font(24), fill="#555")
    y = 110
    for name, a, b, t5, t7 in rows:
        d.rectangle([0, y, W, y + 44], fill=NAVY); d.text((PAD, y + 7), name, font=font(28), fill="white")
        a = a.resize((TW, TH)).convert("L").convert("RGB")
        im.paste(a, (PAD // 2, y + 52)); im.paste(b, (PAD // 2 + TW + PAD, y + 52))
        label(d, (PAD // 2 + 8, y + 60), "v5", 22, box=True, bg="#666666"); label(d, (PAD // 2 + TW + PAD + TW - 50, y + 60), "v7", 22, box=True, bg=ORANGE)
        d.text((PAD, y + 52 + TH + 10), t5, font=f, fill="#666"); d.text((PAD, y + 52 + TH + 48), t7, font=f, fill=INK)
        y += 52 + TH + 96
    return im

VER = sys.argv[2] if len(sys.argv) > 2 else "v7"
if VER == "v6":
    TITLE, rows_all = "v6.1", ROWS
    groups = [ROWS[0:4], ROWS[4:8], ROWS[8:12]]
else:
    GRID_ON = False
    TITLE = "v7「高さの目印をつくる」"
    groups = [ROWS_V7[0:5], ROWS_V7[5:9], ROWS_V7[9:13]]
for n, rows in enumerate(groups, 1):
    p = OUT / f"storyboard_{VER}_p{n}.jpg"
    page(rows, n, len(groups)).save(p, quality=88)
    print(p)
if VER == "v7" and len(sys.argv) > 3:
    p = OUT / "diff_v5.jpg"; diff_v5(sys.argv[3]).save(p, quality=88); print(p)
