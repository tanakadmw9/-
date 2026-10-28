"""編集計画用：BGM の小節ごとの音量・明るさ・音の密度を測り、曲の構成（セクション）を推定する。
使い方: python3 scripts/41_bgm_structure.py <曲.mp3> [beat0 秒] [拍の周期 秒]
出力: analysis/plan/bgm_<曲名>.md / .png
"""
import sys, pathlib
import numpy as np, librosa
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

ROOT = pathlib.Path(__file__).resolve().parent.parent
src = pathlib.Path(sys.argv[1])
y, sr = librosa.load(src, sr=22050, mono=True)
tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
bt = librosa.frames_to_time(beats, sr=sr)
if len(sys.argv) > 3: B0, BP = float(sys.argv[2]), float(sys.argv[3])
else:
    k = np.arange(len(bt)); BP, B0 = np.polyfit(k, bt, 1)
BAR = 4 * BP
hop = 512
rms = librosa.feature.rms(y=y, hop_length=hop)[0]
cen = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=hop)[0]
ons = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
low = librosa.feature.melspectrogram(y=y, sr=sr, hop_length=hop, n_mels=64)
t = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop)
chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop)
nb = int((len(y) / sr - B0) / BAR)
rows = []; feats = []
for i in range(nb):
    a, b = B0 + i * BAR, B0 + (i + 1) * BAR
    m = (t >= a) & (t < b)
    db = 20 * np.log10(rms[m].mean() + 1e-9)
    bass = 10 * np.log10(low[:8, m].mean() + 1e-12)
    rows.append((i + 1, a, db, cen[m].mean(), ons[m].mean(), bass))
    feats.append(np.concatenate([chroma[:, m].mean(1), [db / 10]]))
feats = np.array(feats)
# 8 小節前とのクロマ類似（繰り返しの検出）
lines = [f"# BGM 構成：{src.name}", "", f"- 拍の周期 {BP:.5f} 秒（{60/BP:.1f} BPM）、最初の拍 {B0:.3f} 秒、1小節 {BAR:.3f} 秒、小節数 {nb}", "",
         "| 小節 | 開始(秒) | 音量 dB | 明るさ Hz | 音の密度 | 低音 dB | 8小節前との類似 |", "|---|---|---|---|---|---|---|"]
for (i, a, db, c, o, bs), f in zip(rows, feats):
    sim = ""
    if i > 8:
        g = feats[i - 9]; sim = f"{np.dot(f[:12], g[:12]) / (np.linalg.norm(f[:12]) * np.linalg.norm(g[:12])):.2f}"
    lines.append(f"| {i} | {a:.2f} | {db:.1f} | {c:.0f} | {o:.2f} | {bs:.1f} | {sim} |")
out = ROOT / "analysis/plan"; out.mkdir(parents=True, exist_ok=True)
(out / f"bgm_{src.stem}.md").write_text("\n".join(lines) + "\n")
fig, ax = plt.subplots(3, 1, figsize=(14, 7), sharex=True)
ax[0].plot(t, 20 * np.log10(rms + 1e-9), lw=.6); ax[0].set_ylabel("RMS dB")
ax[1].plot(t, cen, lw=.6); ax[1].set_ylabel("centroid")
ax[2].plot(t, ons, lw=.4); ax[2].set_ylabel("onset")
for i in range(nb + 1):
    for a_ in ax: a_.axvline(B0 + i * BAR, color="k" if i % 4 == 0 else "0.8", lw=.8 if i % 4 == 0 else .4)
    if i < nb and i % 2 == 0: ax[0].text(B0 + i * BAR + .1, ax[0].get_ylim()[1] - 3, str(i + 1), fontsize=7)
fig.tight_layout(); fig.savefig(out / f"bgm_{src.stem}.png", dpi=90)
print("\n".join(lines))
