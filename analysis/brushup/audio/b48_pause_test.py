"""読点の間の聞き比べ（ナレだけ）。VOICEVOX F版の各行（audio/vo_temp/<id>.wav）の 0.15 秒以上の無音を検出し、
間ごとに長さを指定し直す（無音の真ん中を切る／足す。声そのものは触らない）。
各行：今の読み → 1秒の無音 → 間を変えた読み、の順。行の間は 2 秒。
  python3 b48_pause_test.py <repo> <out_dir>
"""
import sys, pathlib, subprocess, numpy as np, soundfile as sf
REPO = pathlib.Path(sys.argv[1]); OUT = pathlib.Path(sys.argv[2])
# 行ごとの新しい間（秒、無音の検出順）。並列の読点は短く、意味の切れ目は長めに、言い切り前の「ため」は残す
PLAN = {"N2": [0.30, 0.55],         # つくるには、(0.56→0.30) まず、(0.79→0.55)
        "N4": [0.30, 0.42],         # この機械で、(0.53→0.30) プリズムまでの、(0.52→0.42)
        "N6": [0.42, 0.55],         # はかり、(0.60→0.42) つないで、(0.65→0.55)
        "N7b": [0.22, 0.42],        # 地図や、(0.62→0.22) 図面が、(0.61→0.42)
        "N8": [0.45, 0.90, 0.40]}   # 使う、(0.67→0.45) つくる。(1.04→0.90) それが、(0.64→0.40)
SR = 48000
def pauses(x):
    hop = 480; r = np.sqrt(np.convolve(x**2, np.ones(hop)/hop, "same"))[::hop]; sil = r < r.max() * 0.03
    out = []; c = 0
    for i, s in enumerate(sil):
        if s: c += 1
        else:
            if c >= 15 and i - c > 0: out.append(((i - c) * hop, i * hop))
            c = 0
    return out
seq = []; log = []
for lid, new in PLAN.items():
    x, sr = sf.read(str(REPO / f"audio/vo_temp/{lid}.wav")); assert sr == SR
    ps = pauses(x); y = []; pos = 0
    for (a, b), L in zip(ps, new):
        mid = (a + b) // 2; half = int(L * SR / 2)
        y += [x[pos:a], np.zeros(int(L * SR))]; pos = b
        log.append(f"{lid}: {(b-a)/SR:.2f}→{L:.2f}")
    y.append(x[pos:]); y = np.concatenate(y)
    seq += [x, np.zeros(SR), y, np.zeros(2 * SR)]
    log.append(f"{lid}: {len(x)/SR:.2f}s → {len(y)/SR:.2f}s")
w = OUT / "_p.wav"; sf.write(str(w), np.concatenate(seq).astype(np.float32), SR)
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(w), "-af", "loudnorm=I=-20:TP=-2", "-ar", "48000", "-b:a", "192k", str(OUT / "T4_vo_pauses_before_after.mp3")], check=True)
w.unlink(); print("\n".join(log))
