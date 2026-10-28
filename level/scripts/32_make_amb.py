"""環境音（AMB）：夏の草原の「やわらかな風＋ゆっくりした突風＋草のそよぎ」を合成する。
audio/amb/amb.wav（48kHz stereo, 24bit, 約90秒）。鳥は合成だと不自然になりやすいので入れない。

つくり：
- 突風の包絡 g(t)：0.02〜0.25Hz の帯域に絞った乱数（固定シード）。L/R で一部共通・一部独立。
- 風：ピンク寄りのノイズを複数の帯域（80Hz〜1.6kHz）に分け、包絡が強いほど高い帯域の比率を上げる
  （＝風の「ヒュー」の明るさが突風に合わせて上下する）。L/R は独立ノイズ（無相関）。
- 草：2.5〜9kHz のノイズを、突風に少し遅れて追従する包絡×速いランダムな揺らぎ（葉擦れの粒）で変調。
- ループはしない（全長を一度に生成）。両端は 0.5 秒のフェード（ミックス側でも切れ目にフェード）。

  python3 scripts/32_make_amb.py [秒数=90]
"""
import sys, pathlib
import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfiltfilt, sosfilt

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "audio/amb"
SR = 48000
DUR = float(sys.argv[1]) if len(sys.argv) > 1 else 90.0
N = int(DUR * SR)
rng = np.random.default_rng(32)


def band_noise(lo, hi, n=N, order=2):
    x = rng.standard_normal(n)
    if lo is None:
        sos = butter(order, hi, "lowpass", fs=SR, output="sos")
    elif hi is None:
        sos = butter(order, lo, "highpass", fs=SR, output="sos")
    else:
        sos = butter(order, [lo, hi], "bandpass", fs=SR, output="sos")
    y = sosfilt(sos, x)
    return y / y.std()


def slow_env(lo, hi, n=N, ctrl_sr=200):
    """lo〜hi Hz に絞った滑らかな乱数（制御レートで作って補間）。平均0・標準偏差1。"""
    m = int(n / SR * ctrl_sr) + 2
    x = rng.standard_normal(m + 4000)
    sos = butter(2, [lo, hi], "bandpass", fs=ctrl_sr, output="sos")
    y = sosfiltfilt(sos, x)[2000:2000 + m]
    y = (y - y.mean()) / y.std()
    return np.interp(np.arange(n) / SR, np.arange(m) / ctrl_sr, y)


def channel(common):
    own = slow_env(0.02, 0.25)
    gust = 0.75 * common + 0.45 * own                  # L/R で少しずれる突風
    g = 1 / (1 + np.exp(-1.6 * gust))                   # 0..1 にソフトに収める
    g = 0.25 + 0.75 * g                                 # 無風にはしない
    # 風：帯域ごとに、包絡が強いほど上の帯域が開く
    bands = [(None, 120, 1.0, 0.0), (120, 260, 0.8, 0.2), (260, 520, 0.55, 0.45),
             (520, 950, 0.35, 0.7), (950, 1600, 0.18, 0.9)]
    wind = np.zeros(N)
    for lo, hi, amp, thr in bands:
        open_ = np.clip((g - thr * 0.75) / 0.35, 0, 1) ** 1.5 if thr > 0 else np.ones(N)
        wind += amp * band_noise(lo, hi) * open_ * g
    # 草：突風に 0.4〜0.8 秒遅れて追従、速い不規則な揺らぎ（2〜12Hz）で葉擦れの粒感
    lag = int(rng.uniform(0.4, 0.8) * SR)
    g_l = np.concatenate([np.full(lag, g[0]), g[:-lag]])
    flutter = slow_env(2.0, 12.0)
    flutter = np.clip(0.55 + 0.45 * flutter, 0, None) ** 2
    grass = band_noise(2500, 9000) * flutter * np.clip(g_l - 0.3, 0, None) ** 1.3
    grass += 0.35 * band_noise(1200, 2500) * flutter * np.clip(g_l - 0.45, 0, None) ** 1.5
    return wind * 0.55 + grass * 0.30


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    common = slow_env(0.02, 0.25)
    L, R = channel(common), channel(common)
    x = np.stack([L, R], 1)
    f = int(0.5 * SR); r = np.linspace(0, 1, f)[:, None]
    x[:f] *= r; x[-f:] *= r[::-1]
    x = x / np.abs(x).max() * 10 ** (-3 / 20)
    sf.write(OUT / "amb.wav", x.astype(np.float32), SR, subtype="PCM_24")
    c = np.corrcoef(L, R)[0, 1]
    print(f"amb.wav {DUR:.0f}s stereo, L/R correlation {c:+.2f} -> {OUT/'amb.wav'}")


if __name__ == "__main__":
    main()
