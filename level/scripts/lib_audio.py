"""音の共通処理（scripts/30_mix.py と scripts/40_qc.py から使う）。
ITU-R BS.1770 の K 特性で、短時間（3秒）・瞬時（0.4秒）ラウドネスと True Peak（4倍オーバーサンプリング）を測る。
"""
import numpy as np
from scipy.signal import lfilter, resample_poly

SR = 48000
# BS.1770-4 K-weighting（48kHz の係数）
_K1 = ([1.53512485958697, -2.69169618940638, 1.19839281085285], [1.0, -1.69065929318241, 0.73248077421585])
_K2 = ([1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621])


def as2d(x):
    x = np.asarray(x, dtype=np.float64)
    return x[:, None] if x.ndim == 1 else x


def kweight(x):
    x = as2d(x)
    y = lfilter(*_K1, x, axis=0)
    return lfilter(*_K2, y, axis=0)


def sliding_loudness(x, win=3.0, hop=0.1, sr=SR):
    """窓 win 秒・hop 秒ごとのラウドネス（LUFS）。戻り値 (中心時刻[s], LUFS)。無音は -120。"""
    y = kweight(x)
    p = (y ** 2).sum(axis=1)                       # チャンネル重み 1（L, R）
    c = np.concatenate([[0.0], np.cumsum(p)])
    w = int(win * sr); h = int(hop * sr)
    starts = np.arange(0, max(len(p) - w, 0) + 1, h)
    ms = (c[starts + w] - c[starts]) / w
    lufs = np.where(ms > 1e-12, -0.691 + 10 * np.log10(np.maximum(ms, 1e-12)), -120.0)
    return (starts + w / 2) / sr, lufs


def short_term(x, sr=SR):
    return sliding_loudness(x, 3.0, 0.1, sr)


def momentary(x, sr=SR):
    return sliding_loudness(x, 0.4, 0.05, sr)


def integrated(x, sr=SR):
    """BS.1770-4 ゲーティング付き統合ラウドネス（400ms ブロック、75%重なり、-70 LUFS 絶対・-10 LU 相対ゲート）。"""
    y = kweight(x)
    p = (y ** 2).sum(axis=1)
    c = np.concatenate([[0.0], np.cumsum(p)])
    w = int(0.4 * sr); h = int(0.1 * sr)
    if len(p) < w: return -120.0
    st = np.arange(0, len(p) - w + 1, h)
    z = (c[st + w] - c[st]) / w
    l = -0.691 + 10 * np.log10(np.maximum(z, 1e-15))
    z = z[l > -70]
    if len(z) == 0: return -120.0
    rel = -0.691 + 10 * np.log10(z.mean()) - 10
    z = z[-0.691 + 10 * np.log10(z) > rel]
    return float(-0.691 + 10 * np.log10(z.mean()))


def kweight_ms(x):
    """K 特性をかけた平均二乗（ゲートなし）。LUFS = -0.691 + 10log10(これ)。"""
    y = kweight(x)
    return float((y ** 2).sum(axis=1).mean())


def true_peak_db(x):
    x = as2d(x)
    up = resample_poly(x, 4, 1, axis=0)
    return float(20 * np.log10(max(np.abs(up).max(), 1e-12)))


def db(g):
    return 10 ** (g / 20)


def fade_edges(x, fin=0.010, fout=0.010, sr=SR):
    """raised-cosine のフェード（切れ目のプチノイズ防止）。"""
    x = x.copy()
    a, b = int(fin * sr), int(fout * sr)
    if a: x[:a] *= (0.5 - 0.5 * np.cos(np.linspace(0, np.pi, a)))[(slice(None),) + (None,) * (x.ndim - 1)]
    if b: x[-b:] *= (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, b)))[(slice(None),) + (None,) * (x.ndim - 1)]
    return x


def keyframes_to_gain(points, n, sr=SR, floor_db=-90.0):
    """[(t, dB), ...] を dB で直線補間してサンプルごとのゲインにする。None は無音。"""
    t = np.arange(n) / sr
    ts = np.array([p[0] for p in points]); ds = np.array([floor_db if p[1] is None else p[1] for p in points])
    g = db(np.interp(t, ts, ds))
    g[g <= db(floor_db) * 1.0001] = 0.0
    return g


def vo_bgm_diff(vo, bgm, lines, sr=SR):
    """ナレとBGMの差（docs/07 §1）。lines = [(id, start, end)]。
    per_line : 各行で VO の統合ラウドネス − 同じ区間の BGM の平均ラウドネス（K特性・ゲートなし）。BGM無音は None。
    short    : 3秒の短時間ラウドネス窓が1つのナレ行に完全に入る時刻だけで VO−BGM を比べた分布（median/p5/min）。"""
    per = {}
    for i, s, e in lines:
        a, b = int(s * sr), int(e * sr)
        ms = kweight_ms(bgm[a:b])
        per[i] = None if ms < 1e-12 else round(integrated(vo[a:b], sr) - (-0.691 + 10 * np.log10(ms)), 1)
    t, v = short_term(vo, sr); _, g = short_term(bgm, sr)
    inside = np.zeros_like(t, bool)
    for _, s, e in lines: inside |= (t - 1.5 >= s) & (t + 1.5 <= e)
    d = (v - g)[inside & (v > -70) & (g > -100)]
    short = None if len(d) == 0 else {"median": round(float(np.median(d)), 1), "p5": round(float(np.percentile(d, 5)), 1),
                                      "min": round(float(d.min()), 1), "n_windows": int(len(d))}
    return per, short
