"""計画段階の絵コンテ（ゲート1 用）を、元の素材のコマと簡単な図のスケッチから作る。
秒・切り出し窓・文は plan/editing_v5.md（v5.2）§3.2・§3.3・§9 と plan/content_v5.md の写し（v4 の絵コンテは git の履歴にある版で作った）。
使い方：python3 scripts/51_plan_storyboard.py /mnt/project-files/level/storyboard_v5/
出力：storyboard_v5_p1.jpg・p2.jpg（素材から作った画像なので、リポジトリには入れない）
"""
import pathlib, subprocess, sys, io
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = pathlib.Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
SRC = {k: ROOT / f"source/{v}.mp4" for k, v in {"S": "S_sueru", "K": "K_kansoku", "N": "N_nozoki"}.items()}
FONT = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
NAVY, ORANGE, PAPER, GRID, INK = "#1F3A5F", "#E8742A", "#F4F1EA", "#D9D3C4", "#14202E"
TW, TH = 480, 270

def font(px):
    return ImageFont.truetype(FONT, px)

def frame(src, t, crop=None, masks=()):
    vf = (f"crop={crop[2]}:{crop[3]}:{crop[0]}:{crop[1]}," if crop else "") + f"scale={TW}:{TH}"
    jpg = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", f"{t:.3f}", "-i", str(SRC[src]),
                          "-frames:v", "1", "-vf", vf, "-q:v", "3", "-f", "image2", "-c:v", "mjpeg", "-"],
                         capture_output=True, check=True).stdout
    im = Image.open(io.BytesIO(jpg)).convert("RGB")
    sw, sh = (848, 480) if src == "S" else (1920, 1080)   # マスクは元の画素。全画面のときだけ
    for x1, y1, x2, y2 in masks:
        box = (int(x1 * TW / sw), int(y1 * TH / sh), int(x2 * TW / sw), int(y2 * TH / sh))
        im.paste(im.crop(box).filter(ImageFilter.GaussianBlur(4)), box[:2])
    return im

def grid(frames):   # 2×2 の小さなコマ
    im = Image.new("RGB", (TW, TH), "white")
    for i, f in enumerate(frames):
        im.paste(f.resize((TW // 2 - 2, TH // 2 - 2)), ((i % 2) * TW // 2 + 1, (i // 2) * TH // 2 + 1))
    return im

def paper():
    im = Image.new("RGB", (TW, TH), PAPER); d = ImageDraw.Draw(im)
    for x in range(0, TW, 24): d.line([(x, 0), (x, TH)], fill=GRID, width=1)
    for y in range(0, TH, 24): d.line([(0, y), (TW, y)], fill=GRID, width=1)
    return im, d

def dotted(d, a, b, color=ORANGE, w=3, step=10):
    n = max(1, int(((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5 // step))
    for i in range(0, n, 2):
        p = (a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n)
        q = (a[0] + (b[0] - a[0]) * (i + 1) / n, a[1] + (b[1] - a[1]) * (i + 1) / n)
        d.line([p, q], fill=color, width=w)

def label(d, xy, s, px=18, fill=NAVY, box=False):
    f = font(px)
    if box:
        x0, y0, x1, y1 = d.textbbox(xy, s, font=f)
        d.rectangle([x0 - 5, y0 - 4, x1 + 5, y1 + 4], fill=NAVY); fill = "white"
    d.text(xy, s, font=f, fill=fill)

def scope(d, c, r, reading):   # のぞいた世界の小窓
    x, y = c
    d.ellipse([x - r, y - r, x + r, y + r], fill="#FBFAF6", outline=NAVY, width=3)
    for k in range(-4, 5):   # E 字の目盛り（簡略）
        d.rectangle([x - r * 0.25, y + k * r * 0.2 - 3, x + (r * 0.1 if k % 2 else r * 0.25), y + k * r * 0.2 + 3], fill=NAVY)
    d.line([(x, y - r + 4), (x, y + r - 4)], fill=NAVY, width=1)
    d.line([(x - r + 4, y), (x + r - 4, y)], fill=ORANGE, width=3)
    label(d, (x - r * 0.6, y + r + 6), reading, 20, box=True)

# ---- 図のスケッチ（同じ道の断面。右が低い、水は左から右へ）----
def section(mode):
    im, d = paper()
    gy = 120
    d.line([(0, gy), (TW, gy)], fill=NAVY, width=3)                     # 地面
    d.rectangle([0, gy + 2, TW, TH], fill="#ECE7DC")
    if mode in ("ask", "ask40"):
        d.polygon([(30, gy), (30, gy - 50), (60, gy - 75), (90, gy - 50), (90, gy)], outline=NAVY, width=2)   # 家
        d.line([(75, gy + 2), (75, gy + 50), (120, gy + 75)], fill=NAVY, width=2)        # 家からの短い管（合流だけ）
        label(d, (36, gy - 40), "トイレ", 13)
        drop = 0 if mode == "ask" else 48                                               # 1600px→480px に縮めた 192px
        a, b = (0, 190 - drop / 2), (TW, 190 + drop / 2)
        d.line([a, b], fill=NAVY, width=3); d.line([(a[0], a[1] + 14), (b[0], b[1] + 14)], fill=NAVY, width=3)
        for i in range(5):
            x = 160 + i * 60; y = a[1] + (b[1] - a[1]) * x / TW + 7
            d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=NAVY)
        if mode == "ask40":
            label(d, (330, 10), "縦に40倍", 22, box=True); label(d, (16, 228), "1 m で 3 mm（例）", 24)
            d.line([(462, 60), (462, 250)], fill=NAVY, width=2); d.polygon([(456, 68), (468, 68), (462, 56)], fill=NAVY); d.polygon([(456, 242), (468, 242), (462, 254)], fill=NAVY)
        else:
            label(d, (16, 228), "（管はまっすぐに見える）", 18)
    elif mode == "answer":
        drop = 48
        d.rectangle([0, 0, TW, TH], fill=PAPER)
        for y in range(0, TH, 24): d.line([(0, y), (TW, y)], fill=GRID, width=1)
        import math
        gyx = lambda x: 100 + 34 * x / TW + 6 * math.sin(x / 37)   # 右へゆるく下がり、小さく波打つ
        d.line([(x, gyx(x)) for x in range(0, TW + 1, 4)], fill=NAVY, width=3)
        for i in range(5):
            x = 60 + i * 90; y = 190 - drop / 2 + drop * x / TW
            g = gyx(x); d.ellipse([x - 6, g - 6, x + 6, g + 6], fill=ORANGE); d.line([(x, g + 6), (x, y)], fill=NAVY, width=1)
        a, b = (0, 190 - drop / 2 + 2), (TW, 190 + drop / 2 + 2)
        d.line([a, b], fill=NAVY, width=3); d.line([(a[0], a[1] + 14), (b[0], b[1] + 14)], fill=NAVY, width=3)
        label(d, (330, 10), "縦に40倍", 22, box=True); label(d, (16, 236), "はかった点（深さはばらばら）→ 管 → 実写へ", 17)
    elif mode == "sea":
        d.rectangle([0, 0, TW, TH], fill=PAPER)
        d.line([(0, 200), (120, 200)], fill=NAVY, width=3)                # 海
        for x in range(0, 120, 16): d.arc([x, 192, x + 16, 208], 180, 360, fill=NAVY, width=2)
        d.line([(120, 200), (200, 150), (230, 150)], fill=NAVY, width=3)
        label(d, (232, 136), "≈", 24)
        d.line([(260, 120), (TW, 120)], fill=NAVY, width=3)               # 現場の地面
        d.rectangle([380, 112, 396, 150], outline=NAVY, width=2); d.ellipse([382, 104, 394, 116], fill=NAVY)
        label(d, (402, 82), "水準点", 22); label(d, (402, 108), "高さの目印", 15)
        dotted(d, (0, 200), (388, 200), NAVY, 2); label(d, (150, 206), "海の面", 18)
        d.line([(388, 198), (388, 120)], fill=NAVY, width=2); d.polygon([(382, 128), (394, 128), (388, 118)], fill=NAVY)
        label(d, (300, 160), "10.000 m", 26); label(d, (318, 236), "（数字は例）", 15)
    elif mode in ("quiz", "quiz_wait", "quiz_ans"):
        d.rectangle([0, gy + 2, TW, TH], fill=PAPER)
        d.line([(0, gy), (TW, gy)], fill=PAPER, width=3)
        lv = (240, 120)
        d.rectangle([lv[0] - 18, lv[1] - 8, lv[0] + 18, lv[1] + 8], outline=NAVY, width=2)
        d.line([(lv[0], lv[1] + 8), (lv[0] - 20, lv[1] + 70)], fill=NAVY, width=2); d.line([(lv[0], lv[1] + 8), (lv[0] + 20, lv[1] + 70)], fill=NAVY, width=2)
        dotted(d, (60, lv[1]), (420, lv[1]))
        for x in (60, 420): d.rectangle([x - 5, 70, x + 5, 250 if x == 420 else 220], fill="white", outline=NAVY)
        d.line([(80, 200), (225, 200)], fill=NAVY, width=2); d.line([(255, 200), (400, 200)], fill=NAVY, width=2)
        if mode != "quiz_ans":
            scope(d, (90, lv[1]), 28, "1.234"); scope(d, (390, lv[1]), 28, "1.834")
            label(d, (20, 226), "水準点 10.000 m", 15, box=True); label(d, (400, 226), "となり", 15, box=True)
            label(d, (110, 30), "地面が低いのは、どっち？", 22)
            if mode == "quiz_wait": label(d, (16, 178), "（声なし 2.5秒・曲が止まる）", 14, fill=INK)
        else:
            g1, g2 = lv[1] + 80, lv[1] + 120   # 1.2：1.8＝2：3
            d.rectangle([66, lv[1], 240, g1], fill="#D3D8DF"); d.rectangle([240, lv[1], 414, g2], fill="#D3D8DF")   # 1枚の水（標尺のあいだだけ）
            d.rectangle([240, g1, 414, g2], fill="#9FB0C4", outline="white", width=2)   # 左の地面より下の水＝差 0.600 が一度明るくなる
            d.line([(0, g1), (240, g1)], fill=NAVY, width=3); d.line([(240, g1), (240, g2)], fill=NAVY, width=3)
            d.line([(240, g2), (TW, g2)], fill=NAVY, width=3); d.line([(66, lv[1]), (414, lv[1])], fill=NAVY, width=2)
            d.line([(70, g1 - 8), (232, g1 - 8), (232, g2 - 8), (330, g2 - 8)], fill=ORANGE, width=3); d.polygon([(330, g2 - 14), (330, g2 - 2), (342, g2 - 8)], fill=ORANGE)
            label(d, (40, 20), "深いほうが、低い", 30); label(d, (344, g2 - 22), "9.400 m（例）", 16); label(d, (16, g1 + 6), "水準点 10.000 m", 14, box=True)
    elif mode == "bench":
        d.rectangle([0, gy + 2, TW, TH], fill="#ECE7DC")
        d.rectangle([228, 112, 252, 170], outline=NAVY, width=2); d.ellipse([232, 104, 248, 120], fill=NAVY)
        label(d, (270, 60), "水準点", 26); label(d, (270, 92), "高さの目印", 16)
        label(d, (150, 180), "10.000 m（例）", 28); label(d, (150, 222), "（海抜）", 16)
    elif mode in ("unfold", "water"):
        d.rectangle([0, 0, TW, TH], fill=PAPER)
        g2 = 200
        d.line([(0, g2), (TW, g2)], fill=NAVY, width=3)
        sx, lv = 100, (330, 110)
        d.rectangle([sx - 6, 40, sx + 6, g2], fill="white", outline=NAVY)
        d.rectangle([lv[0] - 22, lv[1] - 9, lv[0] + 22, lv[1] + 9], outline=NAVY, width=2)
        d.line([(lv[0], lv[1] + 9), (lv[0] - 24, g2)], fill=NAVY, width=2); d.line([(lv[0], lv[1] + 9), (lv[0] + 24, g2)], fill=NAVY, width=2)
        if mode == "unfold":
            for y0 in (150, 170, 185): d.line([(10, y0 + 30), (TW - 10, y0 - 10)], fill=GRID, width=2)
            label(d, (12, 236), "なぞった斜めの絵 → 横から見た形にほどく", 17, box=True)
            dotted(d, (lv[0] - 22, lv[1]), (sx + 6, lv[1]))
        else:
            d.rectangle([sx + 7, lv[1], lv[0] + 26, g2 - 2], fill="#D3D8DF")   # 機械と標尺のあいだだけ
            d.line([(sx + 7, lv[1]), (lv[0] + 26, lv[1])], fill=NAVY, width=2)
            dotted(d, (lv[0] - 22, lv[1] - 1), (sx + 9, lv[1] - 1))
            for k in range(1, 9): d.rectangle([sx - 6, lv[1] + k * 10 - 2, sx + (2 if k % 2 else 6), lv[1] + k * 10 + 2], fill=NAVY)
            d.line([(sx + 16, lv[1]), (sx + 16, g2)], fill=NAVY, width=2)
            label(d, (sx + 22, 140), "深さ 1.2", 22); label(d, (sx + 112, 146), "34", 14, fill="#7a8aa0")
            label(d, (330, 60), "見えない水の面", 20)
            label(d, (12, 236), "水がわいて目線で止まる → 引いて線だけ残る", 17, box=True)
    elif mode == "stairs":   # 締め：機械2台・水の面2枚の階段
        d.line([(0, 150), (230, 150), (230, 190), (TW, 190)], fill=NAVY, width=3)
        st = [(50, 150), (230, 190), (430, 190)]; hs = [80, 120]
        for (x, g) in st: d.rectangle([x - 4, g - 110, x + 4, g], fill="white", outline=ORANGE if x == 230 else NAVY, width=3 if x == 230 else 1)
        for i, (lx, h) in enumerate([(140, hs[0]), (330, hs[1])]):
            a, b = st[i][0] + 5, st[i + 1][0] - 5
            d.rectangle([a, h, b, (st[i][1] if i == 0 else 190)], fill="#D3D8DF")
            d.line([(a, h), (b, h)], fill=NAVY, width=2); dotted(d, (a, h - 1), (b, h - 1))
            d.rectangle([lx - 14, h - 6, lx + 14, h + 6], outline=NAVY, width=2)
        label(d, (20, 10), "据えるたびに新しい水の面 → となりへつなぐ", 17); label(d, (20, 236), "見えない水の面で、高さをつなぐ", 20)
    elif mode == "door":
        for i in range(5):
            x = 60 + i * 90
            d.ellipse([x - 26, 110, x + 26, 162], outline=ORANGE if i == 1 else NAVY, width=4 if i == 1 else 2)
        label(d, (150, 40), "測量部門のしごと", 24)
    elif mode == "end":
        for i in range(5):
            x = 60 + i * 90
            d.ellipse([x - 26, 110, x + 26, 162], outline=ORANGE if i == 1 else NAVY, width=4 if i == 1 else 2)
        d.ellipse([136, 118, 164, 154], outline=ORANGE, width=2); d.line([(150, 108), (150, 164)], fill=ORANGE); d.line([(124, 136), (176, 136)], fill=ORANGE)
        label(d, (20, 220), "見えない水の面で、高さをつなぐ", 22); label(d, (300, 250), "VOICEVOX:冥鳴ひまり", 13)
    return im

def overlay_title(im):
    d = ImageDraw.Draw(im); x, y = 318, 127   # N 0.30 の対物レンズ（1318,497）を窓 520,180,1200,675 に換算
    d.ellipse([x - 22, y - 22, x + 22, y + 22], outline=ORANGE, width=3)
    d.line([(x - 32, y), (x + 32, y)], fill=ORANGE, width=2); d.line([(x, y - 32), (x, y + 32)], fill=ORANGE, width=2)
    label(d, (20, 196), "水準測量", 40, fill="white"); label(d, (22, 242), "“高さ”の目印をつなぐ", 18, fill="white")
    return im

def overlay_lines(im):   # 実写の上を紺の線がなぞる
    d = ImageDraw.Draw(im)
    for y in (150, 138, 168): d.line([(0, y), (TW, y + 4)], fill=NAVY, width=3)
    label(d, (12, 236), "止め → 線がなぞる → 写真が紙に → 地面が開く", 17, box=True)
    return im

def overlay_k_sight(im):
    d = ImageDraw.Draw(im); dotted(d, (244, 108), (97, 134))
    label(d, (60, 150), "標尺（ものさし）", 15, box=True); label(d, (250, 80), "レベル", 15, box=True)
    return im

def overlay_scope(im):
    d = ImageDraw.Draw(im); dotted(d, (300, 140), (318, 135), NAVY, 2)
    scope(d, (385, 125), 72, "1.23 → 1.234"); label(d, (330, 6), "イメージ・数字は例", 13, box=True)
    return im

def overlay_check(im):
    d = ImageDraw.Draw(im)
    d.rectangle([130, 14, 330, 104], fill=NAVY)
    for i, s in enumerate(["行き →", "← 帰り", "差 3 mm（例）✓"]):
        d.text((140, 20 + i * 28), s, font=font(20), fill="white" if i < 2 else "#FFD3B0")
    return im

def side(a, b):
    im = Image.new("RGB", (TW, TH), "white")
    w = TW // 2 - 2   # 縦横比を保ち、まんなかを切り出す
    im.paste(a.crop((TW // 4, 0, TW // 4 + w, TH)), (0, 0)); im.paste(b.crop((TW // 4, 0, TW // 4 + w, TH)), (TW // 2 + 2, 0))
    return im

KW = (470, 100, 1200, 675)
M1 = [(394, 30, 486, 72), (0, 232, 150, 292), (455, 262, 500, 282)]                         # S の1か所目のぼかし（editing §3.2）
MK = [(1015, 0, 1245, 100), (0, 465, 490, 575), (1680, 568, 1756, 614)]                       # K 全画面
M2 = [(535, 0, 648, 22), (0, 172, 70, 206), (100, 200, 312, 262), (605, 208, 685, 228)]      # 2か所目
ROWS = [
    ("B0 0.0–2.5", lambda: section("door"), "N1a 測量部門の仕事のひとつ、", "章扉。水準のアイコンが灯る→照準へ", "曲1小節、灯る音", "部門の中の1作業（シリーズの型）"),
    ("B1 2.5–7.6", lambda: overlay_title(frame("N", 0.30, (520, 180, 1200, 675))), "N1b 水準測量です。", "照準が対物レンズに合う。水準測量／“高さ”の目印をつなぐ", "ピッ。曲 −18 dB、道の音が前", "主役の機械と名前"),
    ("B2 7.6–15.2", lambda: grid([frame("S", 2.6, None, M1), frame("S", 20.0, None, M1), frame("S", 53.2, None, M1), frame("S", 66.0, None, M1)]),
     "（声なし。14.2 から N2 が J で入る）", "S 全画面・1本のスピードランプ：三脚を拾う（実時間）→約25倍→機械が載る（実時間）→約10倍で整準。右下に気泡。看板は固定のぼかし", "金具の音・載る音が主役", "人の仕事の手触り。人を早く出す"),
    ("B3a 15.2–17.7", lambda: overlay_lines(frame("S", 85.0, None, M1)), "N2 トイレやおふろの水は、ひとりでに流れていきます。", "観測者が出ていき機械だけの道に車 → 止め → 線 → 写真が紙に", "道の音 → 地面の下へ沈む", "暮らしの水"),
    ("B3b 17.7–22.8", lambda: section("ask40"), "N3 道の下の管に、目に見えない坂があるからです。", "地面が開き、家のトイレから道の下の管へ。息つぎで縦に40倍：管が傾き、方眼も縦に広がり、右に縦の両矢印", "曲の息つぎ", "なぜ高さが要るか"),
    ("B4a 22.8–26.5", lambda: frame("S", 165.5, None, M2 + [(690, 205, 848, 275)]), "N4 その坂をつくる前に、まず、まちの高さを、ミリまではかります。", "一番強い一打で S 2か所目（全画面）：観測者が機械を合わせてのぞく", "一打、同期音", "はかる人"),
    ("B4b 26.5–33.5", lambda: section("bench"), "N4 …ミリまではかります。 N5 高さの目印「水準点」。高さは、もうわかっています。", "水準点にゆっくり寄る。10.000 m（例）が数え上がる。（海抜）", "地の音を下げる", "用語1つ、はじまりの高さ"),
    ("B5a 33.5–36.5", lambda: overlay_k_sight(frame("K", 4.5, KW)), "N6 この機械は、", "K（1.6倍の窓）かがんでのぞく。遠くに標尺の人。35.3 に札「レベル」「標尺（ものさし）」", "K の同期音（足音・カチッ）", "二人と道具（1080p の観測）"),
    ("B5b 36.5–38.8", lambda: section("unfold"), "（声なし）", "止め → 線 → 写真が紙に → 斜めの絵を 0.4 秒 → 真横へ回る 0.6 秒 → 寄せる 0.4 秒（1つずつ。基準点の「倒れる」と対）", "現場の音が残る → 静か", "横から見る"),
    ("B5c 38.8–46.1", lambda: section("water"), "N6 …プールの水の面のように、平らな線を引きます。 N7 読むのは、線から下の“深さ”。", "目線は標尺の手前まで → 機械と標尺のあいだに水がわいて止まり一度ゆれる → 深さ 1.2(34) → 水が引き、目線と札「見えない水の面」が残る（45.95 まで）", "こもった音、43.0 から曲が静かな C", "看板：見えない水の面"),
    ("B5d 46.1–50.6", lambda: overlay_scope(frame("N", 4.5, (600, 190, 1200, 675))), "N8 目盛りのあいだを目で見わけて、ミリまで。", "小窓：N の対物レンズから点線 → ピント → センチの帯のあいだ4割 → 10等分の目安 → 1.234", "読む音", "ミリまで読む技"),
    ("B6a 50.6–58.1", lambda: section("quiz"), "N9 水準点の上は1.2、となりは1.8。 N10 地面が低いのは、どっち？", "左は水準点の上、右はとなり。地面は霧。小窓は目線の高さ。読み 1.234／1.834", "読む音×2、曲C", "問い"),
    ("B6b 58.1–60.7", lambda: section("quiz_wait"), "（声なし 2.5秒）", "何も動かさない（意図した静止）", "曲が止まる（M1d：8小節目の和音）。現場の音だけ", "観客が自分で考える"),
    ("B6c 60.7–63.2", lambda: section("quiz_ans"), "N11 深いほうが、低い。", "4つの動きを1つずつ：霧が晴れる → 標尺のあいだに1枚の水 → 左の地面より下の水（差 0.600）が一度明るく → 矢印が段差を下りて 9.400 m（例）", "一番強い一打", "なるほど。水準点＋差＝となりの高さ"),
    ("B7a 63.2–69.5", lambda: side(frame("K", 16.5, KW), frame("S", 169.5, None, M2)), "N12 わかった高さを書きとめて、となりへ、となりへ。 N13 来た道を戻って、", "K 野帳に書く（9.400 が野帳の横へ）→ S 標尺の人が先へ", "ペンの音・足音", "書きとめて、となりへ"),
    ("B7b 69.5–73.3", lambda: overlay_check(frame("K", 21.0, (720, 0, 1200, 675))), "N13 …行きと帰りが、ほとんど同じか、確かめます。", "野帳の手元に 行き→ ←帰り 差 3 mm（例）✓", "確かめの音、次の道の車の音（J）", "戻って確かめる丁寧さ（敬意）"),
    ("B8 73.3–80.9", lambda: section("answer"), "N14 はかった高さをもとに、水の流れる坂が、まちの下につくられます。", "同じ道→止め→波打って下がる地面に点5つ→深さはばらばら→まっすぐな管→実写に戻り管の線が残って消える", "沈む音 → 戻る", "問いの答え。はかったから深さが決まる"),
    ("B9a 80.9–84.7", lambda: frame("N", 8.0, (600, 200, 1200, 675)), "N15 見えない水の面で、まちの高さを、", "最後の一打で N の顔の寄り（1080p）", "最後の一打、のびる和音", "人で終える"),
    ("B9b 84.7–86.9", lambda: frame("K", 7.0, None, MK), "N15 つないでいく。", "K 全画面の二人の引き（1080p、寄らない）。85.3 に目線（観測者の体は通らない、標尺手の手前で止める）", "和音", "人で終える"),
    ("B9c 86.9–88.5", lambda: section("stairs"), "N15 それが、水準測量です。", "紙：機械2台・水の面2枚の階段。真ん中の標尺が一度灯る", "和音、一瞬こもる", "据えるたびに新しい水の面＝つなぐ"),
    ("B9d 88.5–91.0", lambda: section("end"), "—", "紙→章扉→照準が水準のアイコンへ→黒。締めの文字", "ピッ（小）、和音が消える", "シリーズの型で閉じる"),
]

COLS = [("拍・秒", 150), ("画", TW), ("ナレ", 420), ("画の中身・文字・図解", 400), ("音", 230), ("目的", 260)]
W = sum(c[1] for c in COLS) + 20
RH = TH + 16

def wrap(s, f, width, d):
    lines, cur = [], ""
    for ch in s:
        if d.textlength(cur + ch, font=f) > width:
            lines.append(cur); cur = ch
        else:
            cur += ch
    return lines + [cur]

def page(rows, n, of):
    H = 110 + RH * len(rows) + 20
    im = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(im)
    d.text((10, 10), f"水準測量パート 絵コンテ v5.2（計画・ゲート1用） {n}/{of}　約91秒・36小節・曲 M1d の場合", font=font(30), fill=INK)
    d.text((10, 50), "コマは元の素材（切り出し窓は計画の値）、図は手描きのスケッチ。数字はすべて例。社外に出さない。", font=font(18), fill="#555")
    x = 10
    for name, w in COLS:
        d.rectangle([x, 80, x + w, 108], fill=NAVY); d.text((x + 6, 84), name, font=font(18), fill="white"); x += w
    f = font(19)
    for i, (beat, img, vo, pic, snd, why) in enumerate(rows):
        y = 110 + i * RH
        d.line([(10, y + RH - 2), (W - 10, y + RH - 2)], fill="#ccc")
        x = 10
        for j, (name, w) in enumerate(COLS):
            if j == 1:
                im.paste(img(), (x, y + 6))
            else:
                s = [beat, None, vo, pic, snd, why][j]
                for k, line in enumerate(wrap(s, f, w - 14, d)[:11]):
                    d.text((x + 8, y + 10 + k * 24), line, font=f, fill=INK if j != 0 else NAVY)
            x += w
    return im

half = 11
for n, rows in enumerate([ROWS[:half], ROWS[half:]], 1):
    p = OUT / f"storyboard_v5_p{n}.jpg"
    page(rows, n, 2).save(p, quality=85)
    print(p)
