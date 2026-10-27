"""ゲート2用の比較シート：(1) 色補正 A/B/C を同じフレームで、(2) 焼き込みテロップの処理（切り出し vs 覆う）。
出力：analysis/compare_grades.jpg、analysis/compare_burnin.jpg
"""
import subprocess, pathlib, importlib.util
ROOT = pathlib.Path(__file__).resolve().parent.parent
src = (ROOT / "scripts/02_intermediates.py").read_text()
# 02 の設定（CROPS, GRADES, POST）だけを読み込む（実行はしない）
ns = {"__file__": str(ROOT / "scripts/02_intermediates.py")}; exec(src.split("def run(cmd)")[0].replace("OUT.mkdir(parents=True, exist_ok=True)", ""), ns)
CROPS, GRADES, POST = ns["CROPS"], ns["GRADES"], ns["POST"]
SRC = str(ROOT / "source/input.mp4"); OUT = ROOT / "analysis"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FRAMES = [("S01", 3.0), ("S04", 16.0), ("S07", 25.0), ("S09", 34.4)]

def ff(args):
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"] + args, check=True)

# (1) 色補正：行＝フレーム、列＝ 元 / A / B / C
inputs, chains, labels = [], [], []
for r, (shot, t) in enumerate(FRAMES):
    x, y, w, h = CROPS[shot]
    for c, g in enumerate(["orig", "A", "B", "C"]):
        inputs += ["-ss", str(t), "-i", SRC]
        idx = r * 4 + c
        grade = "null" if g == "orig" else GRADES[g]
        post = "" if g == "orig" else f",{POST}"
        chains.append(f"[{idx}]crop={w}:{h}:{x}:{y},scale=1920:1080:flags=lanczos,{grade}{post},scale=640:360,"
                      f"drawtext=fontfile={FONT}:text='{shot} {g}':x=10:y=10:fontsize=28:fontcolor=white:box=1:boxcolor=black@0.6[v{idx}]")
n = len(FRAMES) * 4
fc = ";".join(chains) + ";" + "".join(f"[v{i}]" for i in range(n)) + f"xstack=inputs={n}:layout=" + \
     "|".join(f"{(i%4)*640}_{(i//4)*360}" for i in range(n)) + "[out]"
ff(inputs + ["-filter_complex", fc, "-map", "[out]", "-frames:v", "1", "-q:v", "3", str(OUT / "compare_grades.jpg")])

# (2) 焼き込み処理：S01（下中央の大テロップ）と S07（左上の小テロップ）
#   列：元 / 切り出し（拡大）/ 覆う（デザイン要素で隠す案のモック）
cover_s01 = "drawbox=x=0:y=760:w=1920:h=320:color=0x14202E@1.0:t=fill"
cover_s07 = "drawbox=x=12:y=22:w=650:h=160:color=0x14202E@1.0:t=fill,drawbox=x=12:y=22:w=6:h=160:color=0xE8742A:t=fill"
rows = [("S01", 3.0, cover_s01), ("S07", 25.0, cover_s07)]
inputs, chains = [], []
for r, (shot, t, cover) in enumerate(rows):
    x, y, w, h = CROPS[shot]
    variants = [("orig", "null"), ("crop x%.2f" % (1920 / w), f"crop={w}:{h}:{x}:{y},scale=1920:1080:flags=lanczos"), ("cover", cover)]
    for c, (lab, vf) in enumerate(variants):
        idx = r * 3 + c
        inputs += ["-ss", str(t), "-i", SRC]
        chains.append(f"[{idx}]{vf},scale=800:450,drawtext=fontfile={FONT}:text='{shot} {lab}':x=10:y=10:fontsize=30:fontcolor=white:box=1:boxcolor=black@0.6[v{idx}]")
fc = ";".join(chains) + ";" + "".join(f"[v{i}]" for i in range(6)) + "xstack=inputs=6:layout=" + \
     "|".join(f"{(i%3)*800}_{(i//3)*450}" for i in range(6)) + "[out]"
ff(inputs + ["-filter_complex", fc, "-map", "[out]", "-frames:v", "1", "-q:v", "3", str(OUT / "compare_burnin.jpg")])
print("ok")
