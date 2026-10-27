"""チームB：音を組み立てる（ナレ／曲／環境音／効果音）→ ステム4本と mix.wav（−24 LUFS、True Peak −2 dBTP 以下）。
元は編集担当の試作 teamB/plan/scripts/b45_audio_test.py。時刻はすべて comp/timeline.json から読む。
効果音ラボの素材は再配布禁止なので、出力（audio/、comp/assets/audio/）は Git に入れない。
使い方: python3 teamB/scripts/30_mix.py"""
import json, pathlib, subprocess, numpy as np, soundfile as sf, pyloudnorm as pyln
ROOT = pathlib.Path(__file__).resolve().parent.parent
T = json.loads((ROOT / "comp/timeline.json").read_text()); C = T["cues"]
VT = json.loads((ROOT / "audio/vo/vo_timing.json").read_text())["lines"]
SR = 48000; DUR = T["duration"]; N = int(DUR * SR)
A = "/mnt/project-files/assets/se/"
def load(p):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()
db = lambda x: 10 ** (x / 20)
mix = {k: np.zeros((N, 2), np.float32) for k in ("vo", "bgm", "amb", "se")}
def place(layer, x, t, gain=0.0, fi=0.01, fo=0.01):
    x = x.copy() * db(gain); fi, fo = int(fi * SR), int(fo * SR)   # 切れ目には必ず 10ms 以上のフェード
    if fi: x[:fi] *= np.linspace(0, 1, fi)[:, None]
    if fo: x[-fo:] *= np.linspace(1, 0, fo)[:, None]
    s = int(round(t * SR)); e = min(s + len(x), N)
    if e > s: mix[layer][s:e] += x[:e - s]
# ---- 曲（つなぎ目1か所＋測る「間」） ----
song = load(T["music"]["file"])
for a, b, at, fi, fo in T["music"]["segments"]:
    place("bgm", song[int(a * SR):int(b * SR)], at, fi=fi, fo=fo)
# ---- ナレ ----
win = []
for n in T["narration"]:
    x = load(ROOT / f"audio/vo/{n['id']}.wav"); place("vo", x, n["start"], gain=-3)
    win.append((n["id"], n["start"], n["start"] + len(x) / SR))
# ---- 環境音・現場の音・電子音（2つだけ） ----
place("amb", load(A + "ambience/summer-countryside1.mp3")[:int((C["mark"] + 1.5) * SR)], 0.0, gain=-6, fi=0.7, fo=1.5)
wind = load(A + "ambience/plants-swaying1.mp3"); place("amb", np.tile(wind, (3, 1))[:int((DUR - 0.5) * SR)], 0.0, gain=4, fi=0.7, fo=2.5)
place("se", load(A + "foley/walk-soil1.mp3")[:int(3.2 * SR)], 0.70, gain=-4, fo=0.4)                       # S06 歩いてくる
place("se", load(A + "ambience/plants-swaying2.mp3")[:int(1.6 * SR)], 3.77, gain=-6, fi=0.1, fo=0.4)        # S03 三脚の脚と草
place("se", load(A + "foley/mechanical-pencil-write1.mp3")[:int(2.8 * SR)], 29.9, gain=-8, fo=0.4)          # S07 記録
place("se", load(A + "foley/walk-soil1.mp3")[int(1.0 * SR):int(3.6 * SR)], C["s10_loop"] + 0.1, gain=-14, fi=0.3, fo=0.5)  # S06 2回目（遠く）
place("se", load(A + "tones/cursor3.mp3"), C["pi"], gain=-6)            # ① はかる「ピッ」（無音の間の中）
place("se", load(A + "tones/decision28.mp3"), C["split_p"], gain=-9)    # ② 住所が決まる
# ---- 音量の書き込み（手で書いた変化） ----
t = np.arange(N) / SR
env = lambda pts: db(np.interp(t, *zip(*pts)))[:, None].astype(np.float32)
g = np.full(N, -8.0)
DUCK = {"N4": -26.5, "N7": -25.5, "N10": -22.5}   # 打楽器が入る小節（N4・N7）と曲の終わり（N10）はもう少し下げる
for nid, s, e in win:   # ナレ中は −23dB（ステムでナレより15dB以上小さく。曲の終わりの静かな部分にかかる N10 は −18dB）。下げはナレの0.4秒前から
    g[(t > s - 0.4) & (t < e + 0.3)] = DUCK.get(nid, -23.0)
k = int(0.25 * SR); g = np.convolve(np.pad(g, (k, k), mode="edge"), np.ones(k) / k, "same")[k:-k]
mix["bgm"] *= db(g)[:, None].astype(np.float32)
s0, s1 = C["silence"]
mix["amb"] *= env([(0, 0), (s0 - 0.25, 0), (s0 + 0.15, -14), (s1 - 0.1, -14), (s1 + 0.3, -8), (C["s10"] - 0.3, -8), (C["s10"] + 0.2, 0),
                   (C["mark"], 0), (C["mark"] + 0.8, -9), (DUR, -9)])
# ---- ラウドネス：線形の利得だけで −24 LUFS に合わせ、True Peak を確かめる ----
out = sum(mix.values())
meter = pyln.Meter(SR); L = meter.integrated_loudness(out.astype(np.float64)); gain = -24.0 - L
# 4倍に補間して True Peak を見積もる（書き出し後に ebur128 で実測する）
up = np.stack([np.interp(np.arange(N * 4) / 4, np.arange(N), out[:, c]) for c in range(2)], 1)
tp = 20 * np.log10(np.abs(up).max() + 1e-12) + gain
if tp > -2.0:
    raise SystemExit(f"True Peak {tp:.1f} dBTP > -2：効果音か曲を下げること")
stem_dir = ROOT / "audio/stems"; stem_dir.mkdir(parents=True, exist_ok=True)
for k, v in mix.items():
    sf.write(stem_dir / f"{k}.wav", v * db(gain), SR, subtype="PCM_24")
dst = ROOT / "comp/assets/audio"; dst.mkdir(parents=True, exist_ok=True)
sf.write(dst / "mix.wav", out * db(gain), SR, subtype="PCM_24")
json.dump({"vo_windows": win, "gain_db": round(gain, 2), "integrated": -24.0, "true_peak_est": round(tp, 2)},
          open(ROOT / "audio/mix_info.json", "w"), ensure_ascii=False, indent=1)
print(f"mix: {L:.1f} LUFS -> -24.0 (gain {gain:+.1f} dB), TP≈{tp:.1f} dBTP")
for w in win: print(w)
