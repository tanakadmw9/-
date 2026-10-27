"""A案 v4.6 の音の磨き込みテスト（最終制作ではない）。
前提：リポジトリで scripts/31,32,34,11（F版: 14 audio/vo_temp 1.0 1.1 1.4 0.04）と 30_mix.py を実行済み
（audio/mix/*.wav と keyframes.json が v4.6 と同じ音になる。v4.6 の書き出しと相関 0.99998 を確認）。
  python3 b47_audio_test.py <repo> <out_dir>
出力（out_dir）：
  T1_bgm_breath.mp3  … BGM のフェーダーだけ直す（ナレ下 −17 を平均で測る、すき間 −8、戻り 0.35 秒）
  T2_carve_eq.mp3    … T1 ＋ ナレの EQ（80Hz 以下カット・300Hz −2dB・3.2kHz +3dB）＋ ナレ中だけ BGM の 1〜4kHz を −4dB（ナレ下は −16。声の帯域では実質 −20）
  T3_full.mp3        … T2 ＋ 効果音を声の帯域の外の音（効果音ラボ）に替えて聞こえる大きさへ ＋ 環境音を実録（鳥＋草）に ＋ 地図の線にシャーペン
  T3_full_with_picture.mp4 … T3 を v4.6 の画に載せたもの
すべて −24 LUFS / True Peak ≤ −2 dBTP。
"""
import sys, json, pathlib, subprocess
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfiltfilt, lfilter, resample_poly
REPO = pathlib.Path(sys.argv[1]); OUT = pathlib.Path(sys.argv[2]); OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(REPO / "scripts"))
from lib_audio import SR, integrated, short_term, momentary, true_peak_db, db, fade_edges, keyframes_to_gain
ASSETS = pathlib.Path("/mnt/project-files/assets/se")
VIDEO = "/mnt/project-files/renders/kijunten_v4.6.mp4"
T = json.loads((REPO / "comp/timeline.json").read_text()); DUR = T["duration"]; N = int(round(DUR * SR))
KF = json.loads((REPO / "audio/mix/keyframes.json").read_text())
rd = lambda k: sf.read(str(REPO / f"audio/mix/{k}.wav"), always_2d=True)[0][:N]
vo, se0, amb0 = rd("vo"), rd("se"), rd("amb")
vo_iv = [(v["start"], v["start"] + v["dur"]) for v in T["vo"]]
REF = float(np.median([integrated(vo[int(s*SR):int(e*SR)]) for s, e in vo_iv]))   # ステムでの VO_REF

def load(p, mono=False):
    p = str(p)
    if p.endswith(".mp3"):
        w = OUT / "_tmp.wav"; subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", p, "-ar", str(SR), "-ac", "2", str(w)], check=True); p = str(w)
    x, sr = sf.read(p, always_2d=True)
    if sr != SR: x = resample_poly(x, SR, sr, axis=0)
    if x.shape[1] == 1: x = np.repeat(x, 2, 1)
    return x.mean(1) if mono else x[:, :2]

def put(buf, x, t):
    n0 = int(round(t * SR)); a, b = max(n0, 0), min(n0 + len(x), len(buf))
    if b > a: buf[a:b] += x[a-n0:b-n0]

def merged(iv, gap):
    out = []
    for s, e in sorted(iv):
        if out and s - out[-1][1] < gap: out[-1][1] = max(out[-1][1], e)
        else: out.append([s, e])
    return out

def peq(x, f0, gdb, q):   # RBJ peaking
    A = 10 ** (gdb / 40); w = 2*np.pi*f0/SR; al = np.sin(w)/(2*q)
    b = [1+al*A, -2*np.cos(w), 1-al*A]; a = [1+al/A, -2*np.cos(w), 1-al/A]
    return lfilter(np.array(b)/a[0], np.array(a)/a[0], x, axis=0)

def vo_eq(x):
    x = sosfiltfilt(butter(2, 80, "highpass", fs=SR, output="sos"), x, axis=0)
    x = peq(x, 300, -2.0, 1.2)
    return peq(x, 3200, 3.0, 1.0)

def lvl(x, s, e):   # 区間の平均の大きさ（短時間ラウドネスの平均。p90 だと大きく見積もり、下げすぎる）
    t, st = short_term(x); m = (t >= s) & (t <= e) & (st > -70)
    return float(10*np.log10(np.mean(10**(st[m]/10)))) if m.any() else REF

def bgm_fader(raw, under, free, pre=0.35, rel=0.35, rel_delay=0.10, merge=1.2):
    """手書き相当のキーフレーム。ナレ区間＝under、すき間＝free（どちらも REF 比）。曲の大きさは区間ごとの平均で割り戻す。"""
    iv = merged(vo_iv, merge); pts = []
    for i, (s, e) in enumerate(iv):
        fu = min(under + REF - lvl(raw, s, e), 8.0)
        pts += [(s - 0.05, fu), (e + rel_delay, fu)]
        nxt = iv[i+1][0] if i+1 < len(iv) else DUR + 1
        g0, g1 = e + rel_delay + rel, nxt - pre
        if g1 - g0 >= 0.25:                     # 上げきって 0.25 秒以上保てるすき間だけ上げる
            ff = min(free + REF - lvl(raw, g0, min(g1, DUR)), 8.0)
            pts += [(g0, ff), (min(g1, DUR), ff)]
    s0 = iv[0][0]; pts = [(0.0, min(free + REF - lvl(raw, 0, s0 - pre), 8.0)), (s0 - pre, min(free + REF - lvl(raw, 0, s0 - pre), 8.0))] + pts
    pts = sorted(p for p in pts if 0 <= p[0] <= DUR); pts.append((DUR, pts[-1][1]))
    return keyframes_to_gain(pts, N), pts, iv

def env01(iv, pre=0.35, rel=0.35, rel_delay=0.10):
    t = np.arange(N) / SR; v = np.zeros(N)
    for s, e in iv:
        up = np.clip((t - (s - pre)) / (pre - 0.05), 0, 1); dn = np.clip(1 - (t - (e + rel_delay)) / rel, 0, 1)
        v = np.maximum(v, np.minimum(up, dn))
    return v

def finish(name, stems, mp4=False):
    mix = sum(stems.values()); g = db(-24.0 - integrated(mix)); mix = mix * g
    tp = true_peak_db(mix)
    if tp > -2.0: mix *= db(-2.0 - tp - 0.3)
    wav = OUT / f"{name}.wav"; sf.write(str(wav), mix.astype(np.float32), SR, subtype="PCM_24")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(wav), "-c:a", "libmp3lame", "-b:a", "192k", str(OUT / f"{name}.mp3")], check=True)
    if mp4:
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", VIDEO, "-i", str(wav), "-map", "0:v:0", "-map", "1:a:0",
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-shortest", "-movflags", "+faststart",
                        str(OUT / f"{name}_with_picture.mp4")], check=True)
    # 計測：すき間の BGM、ナレ下の BGM、SE の見え方
    b = stems["bgm"] * g; v = stems["vo"] * g; s_ = stems["se"] * g
    tm, bm = momentary(b); _, vm = momentary(v); vref = np.median(vm[vm > -60])
    gaps = []; prev = 0.0
    for s, e in vo_iv + [(DUR, DUR)]:
        if s - prev >= 1.5:
            m = (tm > prev + 0.3) & (tm < s - 0.3); gaps.append(f"{prev:.1f}-{s:.1f}:{np.median(bm[m]) - vref:+.1f}")
        prev = e
    under = [np.median(vm[(tm > s) & (tm < e) & (vm > -60)]) - np.median(bm[(tm > s) & (tm < e)]) for s, e in vo_iv]
    se_rel = []
    for x in T["se"]:
        a = int(x["start"]*SR); w = int(0.15*SR)
        se_rel.append(f"{x['start']:.1f}:{10*np.log10(np.mean(s_[a:a+w]**2)+1e-20) - 10*np.log10(np.mean(v[a:a+w]**2)+1e-20):+.1f}")
    print(f"{name}: I {integrated(mix):.1f} LUFS TP {true_peak_db(mix):.1f} | VO−BGM under lines {np.min(under):.1f}..{np.max(under):.1f} dB"
          f" | BGM in gaps re VO: {' '.join(gaps)} | SE−VO(150ms): {' '.join(se_rel)}")
    wav.unlink()

raw = np.zeros((N, 2)); put(raw, load(REPO / "audio/bgm/bgm.wav")[:N], T["bgm"]["start"])
raw = fade_edges(raw, 0.01, 0.05)
gref = REF - (-20.0)     # ステムは 30_mix の最終ゲイン分ずれている
raw *= db(gref)

finish("T0_v46_reference", {"vo": vo, "bgm": rd("bgm"), "se": se0, "amb": amb0})
# T1
gain, pts1, iv = bgm_fader(raw, -17.0, -8.0)
finish("T1_bgm_breath", {"vo": vo, "bgm": raw * gain[:, None], "se": se0, "amb": amb0})
# T2
voe = vo_eq(vo); voe *= db(integrated(vo) - integrated(voe))
mid = sosfiltfilt(butter(2, [1000, 4000], "bandpass", fs=SR, output="sos"), raw, axis=0)
carve = 1 + (db(-4.0) - 1) * env01(iv)
raw_c = raw + mid * (carve - 1)[:, None]
gain2, pts2, _ = bgm_fader(raw_c, -16.0, -8.0)
bgm2 = raw_c * gain2[:, None]
finish("T2_carve_eq", {"vo": voe, "bgm": bgm2, "se": se0, "amb": amb0})
# T3
SE_MAP = {"glow": ("tones/decision28.mp3", -12), "lock": ("tones/decision6.mp3", -9),
          "measure": ("tones/cursor3.mp3", -10), "click": ("tones/decision28.mp3", -8)}
se = np.zeros((N, 2))
for x in T["se"]:
    f, tgt = SE_MAP[x["kind"]]; s = load(ASSETS / f, mono=True)
    nz = np.where(np.abs(s) > np.abs(s).max() * 0.02)[0]; s = s[nz[0]:]          # 頭の無音を詰めて画に合わせる
    _, m = momentary(np.r_[np.zeros(SR//5), s, np.zeros(SR//2)])                 # 0.4秒窓の最大を REF+tgt に
    s = fade_edges(s * db(REF + tgt + x.get("gain_db", 0.0) * 0.5 - m.max()), 0.0, 0.02)
    put(se, np.repeat(s[:, None], 2, 1), x["start"])
akf = [(t, d) for t, d in KF["amb_keyframes"]]
def real_amb(path, off, rel):
    a = load(ASSETS / path); a = a[int(off*SR):int(off*SR)+N]
    if len(a) < N: a = np.r_[a, a[:N-len(a)]]
    a = fade_edges(a, 0.5, 0.01); a *= db(REF - float(np.median(short_term(a)[1])) + rel)
    return a * keyframes_to_gain([(t, d + 18.5) for t, d in akf], N)[:, None]      # 30_mix の AMB_LIVE を 0 に戻して形だけ使う
amb = real_amb("ambience/karuizawa-birds-1.mp3", 30.0, -24.0) + real_amb("ambience/plants-swaying1.mp3", 0.0, -24.0)
pen = load(ASSETS / "foley/mechanical-pencil-write1.mp3")
pen = sosfiltfilt(butter(2, 400, "highpass", fs=SR, output="sos"), pen, axis=0)[:int(2.4*SR)]
pen = fade_edges(pen * db(REF - 26 - float(np.percentile(momentary(pen)[1], 90))), 0.15, 0.3)
put(se, pen, 45.60)                                                              # 等高線→道路の線が描かれる間
finish("T3_full", {"vo": voe, "bgm": bgm2, "se": se, "amb": amb}, mp4=True)
(OUT / "_tmp.wav").unlink(missing_ok=True)
json.dump({"T1_bgm_keyframes": pts1, "T2_bgm_keyframes": pts2}, open(OUT / "keyframes_T1_T2.json", "w"), indent=1)
