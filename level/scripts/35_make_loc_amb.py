"""環境音（AMB）：元の映像の現場音（道ばたの車と風）で、timeline と同じ長さの環境音を作る（計画 v3 §4、§6 問3 の ◎）。
audio/amb/amb_loc.wav（48kHz stereo 24bit、長さ = timeline.duration、timeline の 0 秒＝ファイルの 0 秒）。

  python3 scripts/35_make_loc_amb.py      （20_plan_timeline.py の後。ミックスは 30_mix.py）

つくり
- 地の音（BED）：人の声・手で触る音（カチッ）がない区間を、スペクトログラムと次の2つの数値で選んだ（dev/locsnd/、2026-10-28）。
    ・声：300–3400Hz の帯域の自己相関（2.5–10ms＝声の高さ）の最大 > 0.6 の 0.5 秒窓
    ・触る音：2kHz 以上の 5ms 包絡が、前後 2 秒の中央値より 14dB 以上高い 0.25 秒窓
  → S 42.0–82.0（40 秒）と S 163.0–184.0。耳では確かめていない（試写で人が聞く）
- 実写の下（実時間のカット）は、そのカットと同じ時刻の音（同期音）。画の車と音の車が合う。
  ただし L02（K 0.55–1.4 に人の声）、早回しのカット（L03・L08）、L01（N 0.15–0.6 に人の声・口笛）は地の音。
- 区切りはどれも 0.15 秒の等パワーのクロスフェード。カットごとの音の大きさは地の音の中央値（短時間ラウドネス）にそろえる（±8dB まで）。
- 帯域：80Hz 以下（風のボコボコ）と 8kHz 以上を切る（会場のスピーカーで耳につく高い粒を落とす）。
- 図解の区間で下げる・締めで消すのは 30_mix.py（AMB_DIAG など）。
"""
import json, pathlib, sys, subprocess
import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfiltfilt

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib_audio import SR, momentary

ROOT = pathlib.Path(__file__).resolve().parent.parent
T = json.loads((ROOT / "comp/timeline.json").read_text())
GRADE = T.get("grade", "Bplus")
META = json.loads((ROOT / f"intermediate/{GRADE}/meta.json").read_text())
DUR = T["duration"]; N = int(round(DUR * SR))
SRC = {"S": ROOT / "source/S_sueru.mp4", "K": ROOT / "source/K_kansoku.mp4", "N": ROOT / "source/N_nozoki.mp4"}
BED = [("S", 42.0, 82.0), ("S", 163.0, 184.0)]
# 同期音を使ってよい範囲（元の秒）。上の2つの数値で声・触る音がない所
SYNC_OK = {"K": [(1.5, 24.79)], "N": [(0.7, 13.25)], "S": [(42.0, 82.0), (159.5, 162.75), (163.0, 184.0)]}
XF = 0.15

_cache = {}
def src_audio(k):
    if k not in _cache:
        p = ROOT / "dev/locsnd" / f"{k}.wav"; p.parent.mkdir(parents=True, exist_ok=True)
        if not p.exists():
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(SRC[k]), "-vn", "-ac", "2", "-ar", str(SR), str(p)], check=True)
        x, sr = sf.read(str(p), always_2d=True); assert sr == SR
        sos = butter(2, [80, 8000], "bandpass", fs=SR, output="sos")
        _cache[k] = sosfiltfilt(sos, x, axis=0)
    return _cache[k]

def clip(k, a, b):
    x = src_audio(k); return x[int(round(a * SR)):int(round(b * SR))]

def level(x):
    t, st = momentary(x); st = st[st > -70]   # 短いカットもあるので 0.4 秒窓
    return float(np.median(st)) if len(st) else -70.0

def xfade_concat(parts):
    n = int(XF * SR); out = parts[0]
    for p in parts[1:]:
        w = np.sin(np.linspace(0, np.pi / 2, n))[:, None]
        out = np.concatenate([out[:-n], out[-n:] * w[::-1] + p[:n] * w, p[n:]])
    return out

bed = xfade_concat([clip(*b) for b in BED])
while len(bed) < N + SR: bed = xfade_concat([bed, bed])
bed_ref = level(bed)

# 区間：0 から DUR までを、実時間の同期音の区間と地の音の区間に分ける
segs = []        # (t0, t1, src, src_in)
last = max(T["shots"], key=lambda s: s["start"])
for s in sorted(T["shots"], key=lambda s: s["start"]):
    m = META[s["shot"]]
    if m.get("speed", 1.0) != 1.0: continue
    a = m["src_in"] + s["media_start"]; t1 = s["start"] + s["dur"]
    if s is last:   # 最後のカット（締め）は、静止画（endcard）の下でも同じカメラの音を続ける
        t1 = DUR
    if any(lo <= a and a + (t1 - s["start"]) <= hi for lo, hi in SYNC_OK[m["source"]]):
        segs.append((s["start"], t1, m["source"], a))
out = np.zeros((N, 2)); w_sync = np.zeros(N)
n = int(XF * SR)
# 同期音の区間：sin/cos の等パワーのフェードで置き、地の音はその残り（sqrt(1−w²)）で敷く
for t0, t1, k, a in segs:
    x = clip(k, a - XF / 2, a + (t1 - t0) + XF / 2)
    g = float(np.clip(bed_ref - level(x), -8, 8))
    L = len(x); w = np.ones(L); w[:n] = np.sin(np.linspace(0, np.pi / 2, n)); w[-n:] = np.cos(np.linspace(0, np.pi / 2, n))
    i0 = int(round((t0 - XF / 2) * SR)); lo, hi = max(i0, 0), min(i0 + L, N)
    out[lo:hi] += x[lo - i0:hi - i0] * (10 ** (g / 20)) * w[lo - i0:hi - i0, None]
    w_sync[lo:hi] = np.maximum(w_sync[lo:hi], w[lo - i0:hi - i0])
    print(f"sync {t0:6.2f}–{t1:6.2f}  {k} {a:7.2f}–{a + t1 - t0:7.2f}  gain {g:+.1f} dB")
out += bed[:N] * np.sqrt(np.clip(1 - w_sync ** 2, 0, 1))[:, None]
f = int(0.5 * SR); out[:f] *= np.linspace(0, 1, f)[:, None]; out[-int(0.01 * SR):] *= np.linspace(1, 0, int(0.01 * SR))[:, None]
dst = ROOT / "audio/amb/amb_loc.wav"; dst.parent.mkdir(parents=True, exist_ok=True)
sf.write(str(dst), out.astype(np.float32), SR, subtype="PCM_24")
print(f"bed {', '.join(f'{k} {a}–{b}' for k, a, b in BED)} (median {bed_ref:.1f} LUFS) -> {dst.relative_to(ROOT)} {DUR}s")
