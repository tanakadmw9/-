"""計画段階の絵コンテ（ゲート1 用）を、元の素材のコマと簡単な図のスケッチから作る。
秒・切り出し窓・文は plan/editing_v4.md §3.3・§9 と plan/content_v4.md §8 の写し。
使い方：python3 scripts/51_plan_storyboard.py /mnt/project-files/level/storyboard_v4/
出力：storyboard_v4_p1.jpg・p2.jpg（素材から作った画像なので、リポジトリには入れない）
"""
import pathlib, subprocess, sys, io
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = pathlib.Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
SRC = {k: ROOT / f"source/{v}.mp4" for k, v in {"S": "S_sueru", "K": "K_kansoku", "N": "N_nozoki"}.items()}
FONT = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
NAVY, ORANGE, PAPER, GRID, INK = "#1F3A5F", "#E8742A", "#F4F1EA", "#D9D3C4", "#14202E"
TW, TH = 480, 270

def font(px):
    return ImageFont.truetype(FONT, px)

def frame(src, t, crop=None):
    vf = (f"crop={crop[2]}:{crop[3]}:{crop[0]}:{crop[1]}," if crop else "") + f"scale={TW}:{TH}"
    jpg = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", f"{t:.3f}", "-i", str(SRC[src]),
                          "-frames:v", "1", "-vf", vf, "-q:v", "3", "-f", "image2", "-c:v", "mjpeg", "-"],
                         capture_output=True, check=True).stdout
    return Image.open(io.BytesIO(jpg)).convert("RGB")

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
        drop = 0 if mode == "ask" else 48                                               # 1600px→480px に縮めた 192px
        a, b = (0, 190 - drop / 2), (TW, 190 + drop / 2)
        d.line([a, b], fill=NAVY, width=3); d.line([(a[0], a[1] + 14), (b[0], b[1] + 14)], fill=NAVY, width=3)
        for i in range(5):
            x = 160 + i * 60; y = a[1] + (b[1] - a[1]) * x / TW + 7
            d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=NAVY)
        if mode == "ask40":
            label(d, (360, 10), "縦に40倍", 18, box=True); label(d, (16, 228), "1 m で 3 mm", 26)
        else:
            label(d, (16, 228), "（管はまっすぐに見える）", 18)
    elif mode == "answer":
        drop = 48
        for i in range(5):
            x = 60 + i * 90; y = 190 - drop / 2 + drop * x / TW
            d.line([(x, gy), (x, y)], fill=ORANGE, width=3); d.line([(x - 8, y), (x + 8, y)], fill=ORANGE, width=3)
        a, b = (0, 190 - drop / 2 + 2), (TW, 190 + drop / 2 + 2)
        d.line([a, b], fill=NAVY, width=3); d.line([(a[0], a[1] + 14), (b[0], b[1] + 14)], fill=NAVY, width=3)
        label(d, (360, 10), "縦に40倍", 18, box=True); label(d, (16, 236), "杭（はかった高さ）に沿って管 → 水が流れ出す", 17)
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
        label(d, (190, 205), "まんなかに置く", 15)
        if mode != "quiz_ans":
            scope(d, (90, 60), 28, "後ろ 1.2"); scope(d, (390, 60), 28, "前 1.8")
            label(d, (138, 14), "低いのは、どっち？", 24)
            if mode == "quiz_wait": label(d, (150, 238), "（声なし 約1.5秒・曲が息つぎ）", 16, fill=INK)
        else:
            d.line([(0, 220), (240, 220)], fill=NAVY, width=3); d.line([(240, 220), (240, 250)], fill=NAVY, width=3)
            d.line([(240, 250), (TW, 250)], fill=NAVY, width=3)
            d.line([(60, lv[1]), (60, 220)], fill=ORANGE, width=6); d.line([(420, lv[1]), (420, 250)], fill=ORANGE, width=6)
            label(d, (20, 20), "目盛りが大きいほうが、低い", 26); label(d, (330, 222), "0.6 m 低い", 16)
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
        label(d, (20, 220), "見えない高さを、ミリでつなぐ", 22); label(d, (300, 250), "VOICEVOX:冥鳴ひまり", 13)
    return im

def overlay_title(im):
    d = ImageDraw.Draw(im); x, y = 318, 127   # N 0.30 の対物レンズ（1318,497）を窓 520,180,1200,675 に換算
    d.ellipse([x - 22, y - 22, x + 22, y + 22], outline=ORANGE, width=3)
    d.line([(x - 32, y), (x + 32, y)], fill=ORANGE, width=2); d.line([(x, y - 32), (x, y + 32)], fill=ORANGE, width=2)
    label(d, (20, 196), "水準測量", 40, fill="white"); label(d, (22, 242), "“高さ”をはかる", 18, fill="white")
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
    scope(d, (385, 125), 72, "1.2 → 1.234 m"); label(d, (330, 6), "イメージ・数字は例", 13, box=True)
    return im

def overlay_check(im):
    d = ImageDraw.Draw(im)
    d.rectangle([130, 14, 330, 104], fill=NAVY)
    for i, s in enumerate(["行き 0.854 m", "帰り 0.851 m", "差 3 mm ✓"]):
        d.text((140, 20 + i * 28), s, font=font(20), fill="white" if i < 2 else "#FFD3B0")
    return im

def side(a, b):
    im = Image.new("RGB", (TW, TH), "white")
    w = TW // 2 - 2   # 縦横比を保ち、まんなかを切り出す
    im.paste(a.crop((TW // 4, 0, TW // 4 + w, TH)), (0, 0)); im.paste(b.crop((TW // 4, 0, TW // 4 + w, TH)), (TW // 2 + 2, 0))
    return im

KW = (470, 100, 1200, 675)
ROWS = [
    ("B0 0.0–2.5", lambda: section("door"), "N1a 測量部門の仕事のひとつ、", "章扉。水準のアイコンが灯る→照準へ", "曲1小節（静か）、灯る音", "部門の中の1作業（シリーズの型）"),
    ("B1 2.5–7.6", lambda: overlay_title(frame("N", 0.30, (520, 180, 1200, 675))), "N1b 水準測量です。", "照準が対物レンズに合う。水準測量／“高さ”をはかる", "ピッ", "主役の機械と名前"),
    ("B2a 7.6–11.4", lambda: frame("S", 88.0), "N2 雨の水も、家で使った水も、ひとりでに流れていきます。", "S 81–95 を3.6倍。人のいない機械、奥を車が流れる", "道の音（J カット）、曲A", "暮らしの水と、この道"),
    ("B2b 11.4–15.0", lambda: overlay_lines(frame("S", 90.0)), "（声なし 約2秒）", "道が透ける（問い）。家・ます・道の下の管。管はまっすぐに見える", "町の音が地面の下へ沈む", "見えない所に水の道がある"),
    ("B2c 15.0–20.2", lambda: section("ask40"), "N3 道の下の管には、1メートルで数ミリの、目に見えない坂があるからです。", "曲の息つぎの小節で縦に40倍。管が傾き、しずくが速くなる", "曲の息つぎ（8小節目）", "なぜ流れるか＝ミリの坂（問い）"),
    ("B3 20.2–27.8", lambda: grid([frame("S", 2.6), frame("S", 15.0), frame("S", 53.2, (70, 82, 707, 398)), frame("S", 66.0, (300, 40, 678, 381))]),
     "N4 その坂をつくるために、地面の高さを、ミリまではかります。", "一打で三脚を拾う→12倍→載せる→整準9.5倍。右下に気泡", "曲で一番強い一打、金具の音", "人の仕事の手触り、準備の丁寧さ"),
    ("B4 27.8–35.4", lambda: section("sea"), "N5 高さの目印「水準点」。高さは、海の面からはかります。", "同じ断面を引いて海へ。≈で遠くを縮める。10.000 m（例）", "地の音を紙に残して消す（L）", "用語1つと、高さの0が海"),
    ("B5a 35.4–40.4", lambda: overlay_k_sight(frame("K", 5.0, KW)), "（声なし 約3秒）→ N6 向こうに立てた“ものさし”を、水平にのぞいて、", "K を1.6倍の窓で（看板・ナンバーを外す）。来る→かがむ→のぞく", "K の同期音", "二人が見えない線でつながる"),
    ("B5b 40.4–45.5", lambda: overlay_scope(frame("N", 4.5, (600, 190, 1200, 675))), "N7 ミリの目盛りまで読みます。", "小窓：本人がつまみを回すとピントが合う→1.2→寄って1.234", "曲がCへ（静か）、読む音", "ミリまで読む技（人と仕組みが同じ画）"),
    ("B6a 45.5–50.6", lambda: section("quiz"), "N8 後ろは1.2、前は1.8。 N9 さて、低いのは、どっち？", "まんなかに機械、同じ長さの矢印。地面は隠す", "読む音×2、曲C", "プロの工夫（まんなか）と問い"),
    ("B6b 50.6–53.1", lambda: section("quiz_wait"), "（声なし 約1.5秒）", "何も動かさない（意図した静止）", "曲の息つぎ（8小節目・2回目）", "観客が自分で考える"),
    ("B6c 53.1–58.1", lambda: section("quiz_ans"), "N10 答えは、目盛りが大きいほう。", "一打で地面が現れ、目線から地面へオレンジの棒", "一打、曲B", "なるほど（大きいほうが低い）"),
    ("B7a 58.1–62.6", lambda: side(frame("K", 16.5, KW), frame("S", 169.5)), "N11 書きとめたら、となりへ、となりへ。", "K 野帳に書く → S 標尺の人が先へ", "足音・ペンの音", "書きとめて、次へつなぐ"),
    ("B7b 62.6–68.3", lambda: side(frame("S", 165.2), overlay_check(frame("K", 21.0, (480, 100, 1200, 675)))), "N12 最後は来た道を戻って、行きと帰りの差が数ミリか、確かめます。", "野帳の手元の上に 行き／帰り／差 3 mm ✓（数字は例）", "確かめの音、次の道の車の音（J）", "戻って確かめる丁寧さ（敬意）"),
    ("B8 68.3–75.8", lambda: section("answer"), "N13 はかった高さをもとに、水の流れる坂が、まちの下につくられます。", "同じ道→止め→道が透ける（答え）。杭5本→杭に沿って管", "町の音が沈む、曲Bの頭で流れ出す", "問いの答え。暮らしとつながる"),
    ("B9 75.8–83.4", lambda: frame("S", 178.0), "N14 目に見えない高さを、ミリまでつないでいく。それが、水準測量です。", "S の二人へゆっくり寄る。自転車の後、二人の間にオレンジの点線（B5 と対）", "最後の一打、のびる和音", "人で終える"),
    ("B9 83.4–86.0", lambda: section("end"), "—", "紙→章扉→照準が水準のアイコンへ→黒。締めの文字", "ピッ（小）、和音が消える", "シリーズの型で閉じる"),
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
    d.text((10, 10), f"水準測量パート 絵コンテ v4（計画・ゲート1用） {n}/{of}　約86秒・34小節・曲 M1 の場合", font=font(30), fill=INK)
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

half = (len(ROWS) + 1) // 2
for n, rows in enumerate([ROWS[:half], ROWS[half:]], 1):
    p = OUT / f"storyboard_v4_p{n}.jpg"
    page(rows, n, 2).save(p, quality=85)
    print(p)
