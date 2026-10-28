"""編集計画用：plan/editing.md のカット割り案を、サムネイル付きの縦長シートにする。
使い方: python3 scripts/43_edit_storyboard.py <v4.4の書き出し.mp4> <出力.png>
実写は source/input.mp4 から（焼き込みを外す切り出し込み）、既存の図解は v4.4 の書き出しから取る。新規の図解は仮の札。
"""
import sys, subprocess, pathlib, io
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
V44, OUT = sys.argv[1], sys.argv[2]
SRC = str(ROOT / "source/input.mp4")
BAR = 4 * 0.63199
CROP = {"S01": (150, 0, 1360, 765), "S02": (300, 0, 1360, 765), "S03": (311, 180, 1600, 900), "S09": (311, 180, 1600, 900)}
FONT = next((f for f in [str(ROOT / "tools/fonts/BIZUDPGothic-Regular.ttf"), "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"] if pathlib.Path(f).exists()))
f_b, f_m, f_s = ImageFont.truetype(FONT, 30), ImageFont.truetype(FONT, 24), ImageFont.truetype(FONT, 20)

# (拍, 開始拍(小節,拍), 長さ(拍), 種類, 素材, in秒, out秒, 動き・つなぎ, 曲)
SEG = [
 ("B1", (1, 1), 4, "new", "章扉（シリーズ共通）", None, None, "アイコン列→基準点だけ灯る（3拍目）", "前奏 静か"),
 ("B1", (2, 1), 8, "S04", "S04 プリズム＋タイトル", 14.65, 17.85, "灯ったアイコンが照準に変形して重なる→2小節3拍で合う『ピッ』。最後のコマは止めて毎秒2%で寄る", "前奏 積み上がる"),
 ("B2", (4, 1), 4, "S06", "S06 農道を歩く一行", 20.45, 22.98, "素のまま（カメラ自体がゆっくりパン）", "Aメロ"),
 ("B2", (5, 1), 8, "S01", "S01 TSを据える2人", 0.30, 5.36, "素のまま。1.41倍なので寄りは足さない", "Aメロ"),
 ("B3", (7, 1), 3, "S03", "S03 プリズムを据える", 12.0, 13.9, "素のまま", "Aメロ終わり"),
 ("B3", (7, 4), 5, "v44:24.5", "D0 地面のしるし", None, None, "S03の三脚の位置からD0の三脚へ形でつなぐ", "息つぎの小節"),
 ("B4", (9, 1), 6, "S09", "S09 肩越しのTS→ピント送り", 30.70, 34.40, "一番強い頭で切替。カメラの動きはそのまま使い、止まったコマで静止", "Bメロ 全楽器"),
 ("B4", (10, 3), 6, "v44:31", "D1 ラベル＋光の線", None, None, "静止した実写の上に描く。光の線は拍に合わせて往復", "Bメロ"),
 ("B5", (12, 1), 12, "v44:38", "D2 真上から：角度→距離→新しい点", None, None, "D1の画が倒れて真上の図に（記号は連続）。1小節に1段。13小節頭が曲のつなぎ目", "Bメロ→つなぎ→Cメロ"),
 ("B6", (15, 1), 3, "S05", "S05 TSをのぞく", 18.0, 19.9, "図解から実写へは小節頭で直に切る", "Cメロ"),
 ("B6", (15, 4), 4, "S07", "S07 記録する2人（表情）", 23.8, 26.33, "素のまま", "Cメロ"),
 ("B6", (16, 4), 5, "S08", "S08 土地を見渡す背中", 26.9, 30.06, "最後の1小節で草原が地図の紙へ溶ける（意味のある唯一のディゾルブ）", "Cメロ"),
 ("B7", (18, 1), 12, "new", "点つなぎ：等高線→道路の線→アイコンが灯る", None, None, "1小節に1つずつ動く", "Cメロ"),
 ("B8", (21, 1), 5, "S02", "S02 前を指差す2人", 5.80, 8.90, "曲の最後の一打で切替", "最後の一打→伸ばし"),
 ("B8", (22, 2), 5, "S10", "S10 現場を見渡す背中", 36.70, 39.71, "毎秒1.5%でゆっくり寄る。締めの文字が出る", "伸ばし"),
 ("B8", (23, 3), 6, "v44:80", "エンドカード", None, None, "照準が縮んで章扉の基準点アイコンに戻る", "伸ばしが消える"),
]

def grab(path, t, crop=None, w=384):
    vf = (f"crop={crop[2]}:{crop[3]}:{crop[0]}:{crop[1]}," if crop else "") + f"scale={w}:-2"
    png = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", f"{t:.3f}", "-i", path, "-frames:v", "1", "-vf", vf, "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True, check=True).stdout
    return Image.open(io.BytesIO(png)).convert("RGB")

def card(text):
    im = Image.new("RGB", (384, 216), (244, 241, 234)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 383, 215], outline=(31, 58, 95), width=3)
    d.text((16, 16), "新規の図解", font=f_s, fill=(184, 84, 26))
    y = 60
    for i in range(0, len(text), 14): d.text((16, y), text[i:i + 14], font=f_m, fill=(20, 32, 46)); y += 32
    return im

ROWH = 240; W = 1900
sheet = Image.new("RGB", (W, 90 + ROWH * len(SEG)), "white"); d = ImageDraw.Draw(sheet)
d.text((20, 20), "編集のカット割り案（24小節＝約60.7秒、BGM 1〜12＋25〜36小節）", font=f_b, fill="black")
for i, (beat, (bar, bt), nb, kind, label, tin, tout, move, music) in enumerate(SEG):
    y = 90 + ROWH * i
    t0 = ((bar - 1) * 4 + bt - 1) * 0.63199; t1 = t0 + nb * 0.63199
    if kind == "new": a = b = card(label)
    elif kind.startswith("v44:"): a = b = grab(V44, float(kind[4:]))
    else:
        c = CROP.get(kind, (155, 180, 1600, 900))
        a = grab(SRC, tin + 0.05, c); b = grab(SRC, max(tout - 0.08, tin), c)
    sheet.paste(a, (20, y + 8)); sheet.paste(b, (420, y + 8))
    d.text((830, y + 10), f"{beat}  {t0:5.2f}–{t1:5.2f}秒  （{bar}小節{bt}拍から {nb}拍）", font=f_b, fill="black")
    d.text((830, y + 56), label + (f"   元 {tin:.2f}–{tout:.2f}秒" if tin is not None else ""), font=f_m, fill=(31, 58, 95))
    for k in range(0, len(move), 40): d.text((830, y + 96 + k // 40 * 30), move[k:k + 40], font=f_s, fill=(60, 60, 60))
    d.text((830, y + 190), "曲：" + music, font=f_s, fill=(184, 84, 26))
    d.line([20, y + ROWH - 2, W - 20, y + ROWH - 2], fill=(220, 220, 220), width=2)
sheet.save(OUT)
print(OUT, sheet.size)
