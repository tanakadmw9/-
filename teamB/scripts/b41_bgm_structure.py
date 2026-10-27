"""チームB：BGM「緑色の木漏れ日」の拍・小節・音量・音色を小節ごとに計測する。
usage: python b41_bgm_structure.py <mp3> <out.md>
"""
import sys, numpy as np, librosa
path, out = sys.argv[1], sys.argv[2]
y, sr = librosa.load(path, sr=22050, mono=True)
dur = len(y) / sr
tempo, beats = librosa.beat.beat_track(y=y, sr=sr, start_bpm=86, tightness=200)
bt = librosa.frames_to_time(beats, sr=sr)
ibi = np.diff(bt)
lines = [f"# BGM 計測：{path.split('/')[-1]}", "",
         f"- 長さ {dur:.2f}秒、推定テンポ {float(np.atleast_1d(tempo)[0]):.1f}BPM、拍数 {len(bt)}",
         f"- 拍間隔 中央値 {np.median(ibi):.4f}秒、標準偏差 {ibi.std()*1000:.1f}ms、最初の拍 {bt[0]:.3f}秒", ""]
# 一定テンポとみなして格子を当てはめる（最小二乗）
k = np.arange(len(bt)); A = np.vstack([k, np.ones_like(k)]).T
period, t0 = np.linalg.lstsq(A, bt, rcond=None)[0]
res = bt - (t0 + period * k)
lines += [f"- 一定テンポの当てはめ：拍 {period:.4f}秒（{60/period:.2f}BPM）、拍0 {t0:.3f}秒、ずれ 最大 {abs(res).max()*1000:.0f}ms", ""]
# 小節の頭（4拍）の位相を、低域の立ち上がりの強さで選ぶ
onset = librosa.onset.onset_strength(y=y, sr=sr)
ot = librosa.frames_to_time(np.arange(len(onset)), sr=sr)
def strength(t): return onset[np.argmin(abs(ot - t))]
grid = t0 + period * np.arange(-4, int((dur - t0) / period) + 1)
grid = grid[grid >= -0.01]
phase_scores = [np.mean([strength(t) for t in grid[p::4]]) for p in range(4)]
p = int(np.argmax(phase_scores))
bars = grid[p::4]
lines += [f"- 小節頭の位相 {p}（各位相の立ち上がり平均 {', '.join(f'{s:.2f}' for s in phase_scores)}）、1小節 {4*period:.3f}秒", ""]
rms = librosa.feature.rms(y=y)[0]; rt = librosa.frames_to_time(np.arange(len(rms)), sr=sr)
cent = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
ct = librosa.frames_to_time(np.arange(chroma.shape[1]), sr=sr)
on_env = librosa.onset.onset_detect(y=y, sr=sr, units='time')
lines += ["| 小節 | 開始 | dB | 音の明るさHz | 発音数/小節 | 主な音 | 前の小節との似かた |", "|---|---|---|---|---|---|---|"]
names = 'C C# D D# E F F# G G# A A# B'.split()
prev = None
rows = []
for i, b in enumerate(bars):
    e = b + 4 * period
    if b > dur: break
    m = (rt >= b) & (rt < e); mc = (ct >= b) & (ct < e)
    db = 20 * np.log10(rms[m].mean() + 1e-9)
    c = cent[m].mean()
    n = int(((on_env >= b) & (on_env < e)).sum())
    ch = chroma[:, mc].mean(axis=1)
    top = '/'.join(names[j] for j in np.argsort(ch)[::-1][:3])
    sim = '' if prev is None else f"{np.dot(ch, prev)/np.linalg.norm(ch)/np.linalg.norm(prev):.2f}"
    prev = ch
    rows.append((i + 1, b, db, c, n, top, sim))
    lines.append(f"| {i+1} | {b:.2f} | {db:.1f} | {c:.0f} | {n} | {top} | {sim} |")
# 終わり：最後に音量が -50dB を下回る時刻
db_all = 20 * np.log10(rms + 1e-9)
last = rt[np.where(db_all > db_all.max() - 40)[0][-1]]
lines += ["", f"- 最後に音が最大から−40dB以内にある時刻：{last:.2f}秒"]
open(out, 'w').write('\n'.join(lines) + '\n')
np.save(out.replace('.md', '_bars.npy'), np.array([r[1] for r in rows]))
print('\n'.join(lines[:8]))
