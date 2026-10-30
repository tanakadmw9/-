"""効果音（SE）を numpy で合成する（素材のダウンロードなし・権利の心配なし）。
audio/se/{lock,measure,click,join,glow}.wav（48kHz mono, 24bit）。
方針（docs/05 §6）：控えめ・漫画的にしない。すべて短いフェード付き、ピークは −6 dBFS に正規化
（実際の音量は scripts/30_mix.py がナレ基準で決める）。乱数は固定シードで再現可能。

  python3 scripts/31_make_se.py
"""
import pathlib
import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "audio/se"
SR = 48000
rng = np.random.default_rng(31)


def t_axis(dur):
    return np.arange(int(round(dur * SR))) / SR


def fade(x, fin=0.003, fout=0.010):
    """端のプチノイズ防止（raised-cosine）。"""
    x = x.copy()
    a, b = int(fin * SR), int(fout * SR)
    if a: x[:a] *= 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, a))
    if b: x[-b:] *= 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, b))
    return x


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], "bandpass", fs=SR, output="sos"), x)


def lp(x, fc, order=2):
    return sosfilt(butter(order, fc, "lowpass", fs=SR, output="sos"), x)


def norm(x, peak_db=-6.0):
    return x / np.abs(x).max() * 10 ** (peak_db / 20)


def lock():
    """照準が合う「ピッ」：計測機器の電子音。約90ms、正弦波＋ごく弱い倍音、角を丸めた矩形エンベロープ。"""
    d = 0.095; t = t_axis(d)
    f = 2350.0  # 計器ビープらしい高さ。純音に近いので耳に刺さらないよう倍音は弱く
    x = np.sin(2 * np.pi * f * t) + 0.08 * np.sin(2 * np.pi * 2 * f * t) + 0.04 * np.sin(2 * np.pi * 3 * f * t)
    env = np.minimum(1, t / 0.004) * np.exp(-t / 0.20)       # ほぼ平らで、わずかに減衰
    x = lp(x * env, 6000)
    return fade(x, 0.004, 0.018)


def measure():
    """測距（EDM）風の、ごく短く小さい2連ブリップ。ナレ「距離」と重なるので短く・細く。"""
    d = 0.20; t = t_axis(d); x = np.zeros_like(t)
    for i, (t0, f) in enumerate([(0.0, 3150.0), (0.085, 3150.0)]):
        n0 = int(t0 * SR); n = int(0.034 * SR); tt = np.arange(n) / SR
        e = np.sin(np.pi * np.clip(tt / 0.034, 0, 1)) ** 2   # Hann型の柔らかい粒
        x[n0:n0 + n] += (0.85 if i else 1.0) * e * np.sin(2 * np.pi * f * tt)
    return fade(lp(x, 7000), 0.002, 0.010)


def click():
    """点が決まる小さな機械的クリック：ごく短いノイズの立ち上がり＋小さな筐体の共鳴（減衰数ms）。"""
    d = 0.06; t = t_axis(d)
    n = rng.standard_normal(len(t))
    trans = bp(n, 2500, 7000) * np.exp(-t / 0.0025)
    body = sum(a * np.sin(2 * np.pi * f * t + p) * np.exp(-t / tau)
               for a, f, tau, p in [(0.6, 1850, 0.006, 0.3), (0.35, 3300, 0.004, 1.1), (0.25, 920, 0.009, 0.0)])
    x = trans * 0.9 + body * 0.5
    return fade(x, 0.0005, 0.012)


def join():
    """橋がつながる低めの「カチッ」：木質の非整数倍音モード（短い減衰）＋柔らかい打撃のノイズ。"""
    d = 0.22; t = t_axis(d)
    modes = [(1.0, 310, 0.045), (0.55, 742, 0.028), (0.35, 1318, 0.016), (0.18, 2105, 0.009), (0.10, 2990, 0.006)]
    x = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t / tau) for a, f, tau in modes)
    n = rng.standard_normal(len(t))
    x = x + 0.5 * bp(n, 600, 3500) * np.exp(-t / 0.003)
    # 2つの部品が噛み合う感じ：12ms後にごく小さな2打目
    k = int(0.012 * SR)
    x2 = np.zeros_like(x); x2[k:] = 0.35 * x[:-k]
    x = lp(x + x2, 5000)
    return fade(x, 0.0008, 0.030)


def glow():
    """章扉でアイコンが灯るやわらかい音：高めの2音の和音（5度）、やわらかい立ち上がり、約0.5秒で消える。"""
    d = 0.55; t = t_axis(d)
    x = sum(a * np.sin(2 * np.pi * f * t) for a, f in [(1.0, 1318.5), (0.55, 1975.5), (0.12, 2637.0)])
    env = np.minimum(1, t / 0.025) ** 2 * np.exp(-t / 0.16)
    return fade(lp(x * env, 5000), 0.002, 0.040)


def glock(freqs, roll=0.03):
    """鉄琴（水準 v8.6、editing_v8.md §2）：部分音 1・2.756・5.404 倍、約 2 秒で消える。和音は 30ms ずつ転がす。52_bgm_v6_tests.py の仮の音と同じ形。"""
    d = 2.0 + roll * len(freqs); t = t_axis(d); x = np.zeros_like(t)
    for k, f in enumerate(freqs):
        n0 = int(k * roll * SR); tt = t[:len(t) - n0]
        z = (np.sin(2 * np.pi * f * tt) * np.exp(-tt / 0.9) + 0.30 * np.sin(2 * np.pi * f * 2.756 * tt) * np.exp(-tt / 0.25)
             + 0.10 * np.sin(2 * np.pi * f * 5.404 * tt) * np.exp(-tt / 0.08)) * np.clip(tt / 0.002, 0, 1)
        x[n0:] += z
    return fade(x, 0.0, 0.05)


C6, E6, G6 = 1046.5, 1318.5, 1568.0


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in [("lock", lock), ("measure", measure), ("click", click), ("join", join), ("glow", glow),
                     ("glock_c6", lambda: glock([C6])), ("glock_ceg", lambda: glock([C6, E6, G6])), ("glock_g6", lambda: glock([G6]))]:
        x = norm(fn())
        sf.write(OUT / f"{name}.wav", x.astype(np.float32), SR, subtype="PCM_24")
        print(f"{name:8s} {len(x)/SR*1000:6.1f} ms  -> {OUT/name}.wav")


if __name__ == "__main__":
    main()
