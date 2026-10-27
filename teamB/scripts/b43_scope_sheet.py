"""チームB：シネスコ（2.39:1）の帯を当てたときの各カットの見え方を、カットごとに3コマ並べたシートにする。
帯：上下138px、画は y138〜942（1920×804）。焼き込み：S01/S02 は下 y≥765、S03〜 は左上 y≤176。
usage: python b43_scope_sheet.py <input.mp4> <out.png>
"""
import sys, subprocess, io
from PIL import Image, ImageDraw, ImageFont
SRC, OUT = sys.argv[1], sys.argv[2]
W, H, BAR = 1920, 1080, 138
AH = H - 2 * BAR  # 804
FONT = ImageFont.truetype('/mnt/project-files/assets/fonts/BIZUDPGothic-Bold.ttf', 30)
# ID, 使う範囲(秒), 拡大, 元の画で使う上端y, 左端x
SHOTS = [
    ('S06', 20.40, 23.42, 1.00, 177, 0), ('S03', 8.95, 10.38, 1.00, 177, 0),
    ('S05', 17.92, 20.32, 1.00, 177, 0), ('S02', 5.78, 8.88, 1.06, 4, 54),
    ('S04', 14.65, 17.86, 1.00, 177, 0), ('S01', 0.70, 4.79, 1.06, 4, 54),
    ('S03', 10.45, 14.54, 1.00, 177, 0), ('S09', 30.80, 36.60, 1.00, 177, 0),
    ('S07', 23.50, 26.55, 1.00, 177, 0), ('S08', 26.62, 30.62, 1.00, 177, 0),
    ('S10', 36.70, 39.75, 1.00, 177, 0),
]
def grab(t):
    png = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{t:.3f}', '-i', SRC, '-frames:v', '1', '-f', 'image2pipe', '-vcodec', 'png', '-'], capture_output=True).stdout
    return Image.open(io.BytesIO(png)).convert('RGB')
def scope(img, s, top, left):
    sw, sh = W / s, AH / s
    crop = img.crop((left, top, left + sw, top + sh)).resize((W, AH), Image.LANCZOS)
    out = Image.new('RGB', (W, H), (0, 0, 0)); out.paste(crop, (0, BAR))
    return out
TW = 640; TH = 360
sheet = Image.new('RGB', (TW * 3 + 40, (TH + 50) * len(SHOTS) + 20), (40, 40, 40))
d = ImageDraw.Draw(sheet)
for r, (sid, a, b, s, top, left) in enumerate(SHOTS):
    for c, t in enumerate((a + 0.1, (a + b) / 2, b - 0.1)):
        fr = scope(grab(t), s, top, left).resize((TW, TH), Image.LANCZOS)
        sheet.paste(fr, (10 + c * (TW + 10), 10 + r * (TH + 50)))
    d.text((12, 10 + r * (TH + 50) + TH + 6), f'{sid}  元 {a:.2f}–{b:.2f}秒  拡大 {s:.2f}倍  元の上端 y{top}', font=FONT, fill=(230, 230, 230))
sheet.save(OUT)
print(OUT, sheet.size)
