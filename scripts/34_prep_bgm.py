"""選んだ曲を映像の尺に合わせて小節単位で編集し、audio/bgm/bgm.wav（48kHz stereo）を作る。
使い方: python3 scripts/34_prep_bgm.py <曲.mp3> [bpm_fit_beat0 秒] [beat 周期 秒]
timeline.bgm.bars（例 "1-12,25-36"）があれば、その小節範囲だけを順につなぐ（小節1の頭＝映像の bgm.start）。
  最後の範囲が曲の最後の小節（36 以上）なら、曲の余韻まで残す。つなぎ目は 60ms の等パワーで重ねる。
無いときは以下の自動モード：
  - 曲の頭は最初の拍（照準が合う拍＝timeline.bgm.start に置く）から始める
  - 必要な長さ（timeline.bgm.end − start）になるよう、本編の途中から 2 小節単位（4 の倍数を優先）で抜き、曲の終わりを映像の終わりの 0〜1.5 秒前に置く。
    抜く位置は、つなぎ目の前後の音色（メルスペクトル）が最も似ている小節の頭を選び、60ms で重ねてつなぐ
  - 曲の本来の終わり（余韻）をそのまま映像の終わりに合わせる（最大 1.5 秒早く終わるのは可）（途中でフェードアウトしない：docs/05 §2）
拍の位置は librosa の拍検出を直線で近似した値（New Departure：beat0 1.9567 秒、周期 0.63199 秒＝94.9 BPM）。
"""
import json, sys, pathlib, subprocess
import numpy as np, soundfile as sf

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = pathlib.Path(sys.argv[1])
B0 = float(sys.argv[2]) if len(sys.argv) > 2 else 1.9567
BP = float(sys.argv[3]) if len(sys.argv) > 3 else 0.63199
SR = 48000; BAR = 4 * BP
T = json.loads((ROOT / "comp/timeline.json").read_text())
NEED = (T["bgm"]["end"] or T["duration"]) - T["bgm"]["start"]

tmp = ROOT / "dev/bgm"; tmp.mkdir(parents=True, exist_ok=True)
wav = tmp / (SRC.stem + ".wav")
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(SRC), "-ar", str(SR), "-ac", "2", str(wav)], check=True)
x, _ = sf.read(wav)
x = x[int(round(B0 * SR)):]                      # 最初の拍から
rest = len(x) / SR
# 曲の終わりの無音を除いた実際の長さ
env = np.sqrt(np.convolve(x.mean(1) ** 2, np.ones(SR // 20) / (SR // 20), "same"))
end_s = (np.where(env > 10 ** (-70 / 20))[0][-1]) / SR
over = end_s - NEED
# 2 小節単位で、曲の終わりが映像の終わりの 0〜1.5 秒前に来る最小の数（できれば 4 の倍数＝フレーズ単位を優先）
cands = [] if T["bgm"].get("bars") else [n for n in range(2, 40, 2) if 0 <= n * BAR - over <= 1.5]
if not cands and not T["bgm"].get("bars"): raise SystemExit(f"no bar count fits: over {over:.2f}s, bar {BAR:.3f}s")
nbars = next((n for n in cands if n % 4 == 0), cands[0]) if cands else 0
cut = nbars * BAR
print(f"need {NEED:.2f}s, song from beat0 {end_s:.2f}s (audible), remove {nbars} bars = {cut:.2f}s -> {end_s - cut:.2f}s")

if T["bgm"].get("bars"):
    xf = int(0.06 * SR); w = np.sqrt(np.linspace(0, 1, xf))[:, None]
    y = None; splices = []
    for part in T["bgm"]["bars"].split(","):
        a, b = [int(v) for v in part.split("-")]
        s0 = int(round((a - 1) * BAR * SR)); e0 = len(x) if b >= 36 else int(round(b * BAR * SR))
        seg = x[max(s0 - xf // 2, 0):min(e0 + xf // 2, len(x))].copy()
        if y is None: y = seg[xf // 2:] if s0 >= xf // 2 else seg
        else:
            splices.append(round((len(y) - xf // 2) / SR, 3))
            y[-xf:] = y[-xf:] * w[::-1] + seg[:xf] * w
            y = np.concatenate([y, seg[xf:]])
    n = int(round(NEED * SR))
    if len(y) > n: print(f"warning: edited song {len(y)/SR:.2f}s > need {NEED:.2f}s, tail cut")
    y = y[:n] if len(y) >= n else np.concatenate([y, np.zeros((n - len(y), 2))])
    f = int(0.01 * SR); y[:f] *= np.linspace(0, 1, f)[:, None]
    out = ROOT / "audio/bgm/bgm.wav"; out.parent.mkdir(parents=True, exist_ok=True)
    sf.write(out, y, SR, subtype="PCM_24")
    meta = {"source": SRC.name, "beat0": B0, "beat_period": BP, "bars": T["bgm"]["bars"], "splices": splices,
            "length": round(len(y) / SR, 3), "need": round(NEED, 3)}
    (ROOT / "audio/bgm/bgm_edit.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1))
    print(meta); raise SystemExit(0)

import librosa
mel = librosa.power_to_db(librosa.feature.melspectrogram(y=x.mean(1), sr=SR, n_fft=4096, hop_length=1200, n_mels=64))
fps = SR / 1200
def frame(t): return mel[:, int(t * fps):int(t * fps) + int(0.6 * fps)].mean(1)
best = None
for k in range(8, int((end_s - cut - 12) / BAR)):  # 頭 8 小節と最後の 12 秒は残す
    a = k * BAR; b = a + cut
    pre = np.linalg.norm(frame(a - 0.6) - frame(b - 0.6)); post = np.linalg.norm(frame(a) - frame(b))
    score = pre + post
    if best is None or score < best[0]: best = (score, a, b)
_, a, b = best
print(f"splice: keep 0–{a:.2f}s, jump from {b:.2f}s (song time {a + B0:.2f} -> {b + B0:.2f}), score {best[0]:.1f}")
ia, ib, xf = int(round(a * SR)), int(round(b * SR)), int(0.06 * SR)
w = np.linspace(0, 1, xf)[:, None] ** 0.5
y = np.concatenate([x[:ia - xf // 2], x[ia - xf // 2:ia + xf - xf // 2] * w[::-1] + x[ib - xf // 2:ib + xf - xf // 2] * w,
                    x[ib + xf - xf // 2:]])
n = int(round(NEED * SR))
y = y[:n] if len(y) >= n else np.concatenate([y, np.zeros((n - len(y), 2))])  # 足りない分は無音（余韻の後）
f = int(0.01 * SR); y[:f] *= np.linspace(0, 1, f)[:, None]
out = ROOT / "audio/bgm/bgm.wav"
sf.write(out, y, SR, subtype="PCM_24")
meta = {"source": SRC.name, "beat0": B0, "beat_period": BP, "bars_removed": nbars, "splice_at": round(a, 3),
        "resume_from": round(b, 3), "length": round(len(y) / SR, 3), "need": round(NEED, 3)}
(ROOT / "audio/bgm/bgm_edit.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1))
print(meta)
