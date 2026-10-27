"""チームB：木漏れ日の小節つなぎ候補ごとに「つなぎ目の不自然さ」を数値化する。
つなぎ目 a→b（a小節の次に b小節を置く）のコスト＝ 本来 b の前にある小節(b-1)の最後の1拍と、a の最後の1拍の音色・和音の距離。
小さいほど自然（0＝本来のつながり）。usage: python b42_splice_cost.py <mp3>
"""
import sys, numpy as np, librosa
P = 1.02270; T0 = 0.333; BAR1 = T0 + P   # 小節1の頭（b41 の計測）
y, sr = librosa.load(sys.argv[1], sr=22050)
hop = 512
C = librosa.util.normalize(librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop), axis=0)
M = librosa.feature.mfcc(y=y, sr=sr, hop_length=hop, n_mfcc=13)[1:8] / 40
t = librosa.frames_to_time(np.arange(C.shape[1]), sr=sr, hop_length=hop)
def lastbeat(bar):
    b = BAR1 + (bar - 1) * 4 * P
    m = (t >= b + 3 * P) & (t < b + 4 * P)
    return np.r_[C[:, m].mean(1), M[:, m].mean(1)]
def firstbeat(bar):
    b = BAR1 + (bar - 1) * 4 * P
    m = (t >= b) & (t < b + P)
    return np.r_[C[:, m].mean(1), M[:, m].mean(1)]
def cost(a, b):
    return float(np.linalg.norm(lastbeat(a) - lastbeat(b - 1)) * 0.6 + np.linalg.norm(firstbeat(a + 1) - firstbeat(b)) * 0.4) * 100
cands = [(8, 20), (8, 21), (6, 19), (7, 19), (7, 20), (9, 20), (12, 21), (4, 13), (6, 21), (5, 21), (16, 21), (20, 21)]
for a, b in cands:
    print(f"{a:>2}→{b:<2}  cost {cost(a, b):6.1f}")

# 全組み合わせ：5小節目から始めて n 小節、最後が20（その次に21〜24）になる並びを、つなぎ目の合計で比べる
import itertools
NB = 24
cache = {}
def c(a, b):
    if b == a + 1: return 0.0
    if (a, b) not in cache: cache[(a, b)] = cost(a, b)
    return cache[(a, b)]
for n in (4, 5, 6):
    best = []
    def rec(seq, tot, splices):
        if len(seq) == n:
            if seq[-1] == 20: best.append((tot, seq[:]))
            return
        for nb in range(5, 21):
            if nb == seq[-1]: continue
            s = 0 if nb == seq[-1] + 1 else 1
            if splices + s > 1: continue
            rec(seq + [nb], tot + c(seq[-1], nb), splices + s)
    rec([5], 0.0, 0)
    best.sort()
    print(f"n={n}: " + "  ".join(f"{'-'.join(map(str,s))}({t:.0f})" for t, s in best[:5]))
# 前奏の短縮
for a, b in [(1, 3), (1, 4), (2, 4)]:
    print(f"前奏 {a}→{b} cost {cost(a, b):.1f}")
