"""チームB：色補正の候補を、帯を当てた同じコマに並べて比べる。
usage: python b44_grade_compare.py <input.mp4> <outdir>
出力：<outdir>/grade_compare.png（行＝カット、列＝補正案）と、案ごとの1920×1080の背景コマ（テストフレーム用）
"""
import sys, subprocess, io, os
from PIL import Image, ImageDraw, ImageFont
SRC, OUT = sys.argv[1], sys.argv[2]
FONT = ImageFont.truetype('/mnt/project-files/assets/fonts/BIZUDPGothic-Bold.ttf', 28)
# 帯：上下138px。S01/S02 は1.06倍・上端y4・左端x54、ほかは等倍・上端y177
def scope(s, top, left):
    w, h = 1920 / s, 804 / s
    return f"crop={w:.0f}:{h:.0f}:{left}:{top},scale=1920:804:flags=lanczos,pad=1920:1080:0:138:black"
GRADES = {
    'G0 補正なし': '',
    'GB1 映画寄り・弱（推奨）': "selectivecolor=greens='0 0.08 0 0':yellows='0 0.03 -0.04 0',eq=saturation=0.92,curves=all='0/0.035 0.25/0.24 0.75/0.76 1/0.955',colorbalance=rm=0.03:gm=0.0:bm=-0.03:rh=0.02:bh=-0.02",
    'GB2 澄んだ朝（影を青く）': "selectivecolor=greens='0 0.10 0 0',eq=saturation=0.90,curves=all='0/0.04 1/0.96',colorbalance=rs=-0.03:bs=0.035:rh=0.035:bh=-0.03",
    'GB3 あたたかい午後': "selectivecolor=greens='0 0.12 0.05 0':yellows='0 0.04 0 0',eq=saturation=0.95,curves=all='0/0.03 1/0.97',colorbalance=rm=0.06:gm=0.01:bm=-0.06:rh=0.03:bh=-0.04",
}
FRAMES = [('S01', 2.5, 1.06, 4, 54), ('S04', 15.6, 1.0, 177, 0), ('S07', 25.0, 1.0, 177, 0), ('S10', 38.0, 1.0, 177, 0), ('S06', 22.0, 1.0, 177, 0)]
os.makedirs(OUT, exist_ok=True)
def render(t, vf):
    png = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{t}', '-i', SRC, '-frames:v', '1', '-vf', vf, '-f', 'image2pipe', '-vcodec', 'png', '-'], capture_output=True, check=True).stdout
    return Image.open(io.BytesIO(png)).convert('RGB')
TW, TH = 576, 324
cols = list(GRADES)
sheet = Image.new('RGB', (10 + len(cols) * (TW + 10), 50 + len(FRAMES) * (TH + 10)), (40, 40, 40))
d = ImageDraw.Draw(sheet)
for c, g in enumerate(cols):
    d.text((10 + c * (TW + 10), 10), g, font=FONT, fill=(235, 235, 235))
for r, (sid, t, s, top, left) in enumerate(FRAMES):
    for c, g in enumerate(cols):
        vf = scope(s, top, left) + (',' + GRADES[g] if GRADES[g] else '')
        im = render(t, vf)
        im.save(f"{OUT}/bg_{sid}_{g.split()[0]}.png")
        sheet.paste(im.resize((TW, TH), Image.LANCZOS), (10 + c * (TW + 10), 50 + r * (TH + 10)))
sheet.save(f"{OUT}/grade_compare.png")
print('ok')
