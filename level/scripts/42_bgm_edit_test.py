"""編集計画用：BGM の小節つなぎの試聴ファイルを作る（本番の 34_prep_bgm.py とは別。聞き比べ用）。
使い方: python3 scripts/42_bgm_edit_test.py <曲.mp3> <出力.mp3> <残す小節の範囲 例 1-12,25-36> [beat0] [周期]
小節は 1 始まり。つなぎ目は 60ms の等パワーで重ねる。小節1の頭＝ファイルの 0 秒。
"""
import sys, subprocess, pathlib, tempfile
import numpy as np, soundfile as sf

src, out, spec = sys.argv[1], sys.argv[2], sys.argv[3]
B0 = float(sys.argv[4]) if len(sys.argv) > 4 else 1.9567
BP = float(sys.argv[5]) if len(sys.argv) > 5 else 0.63199
SR = 48000; BAR = 4 * BP
with tempfile.TemporaryDirectory() as td:
    wav = pathlib.Path(td) / "a.wav"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", src, "-ar", str(SR), "-ac", "2", str(wav)], check=True)
    x, _ = sf.read(wav)
xf = int(0.06 * SR); w = np.sqrt(np.linspace(0, 1, xf))[:, None]
y = None
for part in spec.split(","):
    a, b = [int(v) for v in part.split("-")]
    s = int(round((B0 + (a - 1) * BAR) * SR))
    e = len(x) if b >= 36 else int(round((B0 + b * BAR) * SR))
    seg = x[max(s - xf // 2, 0):min(e + xf // 2, len(x))].copy()
    if y is None: y = seg[xf // 2:]
    else:
        y[-xf:] = y[-xf:] * w[::-1] + seg[:xf] * w
        y = np.concatenate([y, seg[xf:]])
f = int(0.01 * SR); y[:f] *= np.linspace(0, 1, f)[:, None]
with tempfile.TemporaryDirectory() as td:
    tw = pathlib.Path(td) / "o.wav"; sf.write(tw, y, SR)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(tw), "-b:a", "192k", out], check=True)
print(f"{out}: {len(y)/SR:.2f}s, splice(s) at", end=" ")
t = 0
for part in spec.split(",")[:-1]:
    a, b = [int(v) for v in part.split("-")]; t += (b - a + 1) * BAR; print(f"{t:.2f}s", end=" ")
print()
