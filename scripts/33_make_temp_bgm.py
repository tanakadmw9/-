"""仮BGM（TEMPORARY PLACEHOLDER）を数式で合成する。AI音楽生成は使わない。
目的は「リズムと『間』（bgm.pause）を監督が判断できること」だけ。本番は人間が選んだ曲を
audio/bgm/bgm.wav に置く（置けば scripts/30_mix.py はそちらを使う）。

出力：
  audio/bgm/temp_bgm.wav        48kHz stereo 24bit。ファイルの0秒 = timeline の bgm.start、長さ = bgm.end − bgm.start
  audio/bgm/temp_bgm_beats.json 拍・小節の時刻（timeline 上の秒とファイル内の秒の両方）

音楽の設計（comp/timeline.json から毎回計算）：
- テンポ：bgm.start〜bgm.pause.end がちょうど整数小節になるよう 85〜100BPM の中で 92BPM に最も近い値を選ぶ
  → 「間」明けの答え（N7b）がちょうど小節の頭（主和音）に来る。
- 調：D major。進行は I–V–vi–IV。「間」の前は ii–V、「間」の小節は V で宙づりにして止め、明けて I に着地。
- 構成：静かな入り（パッドのみ）→ アルペジオ（4分）→ 一定のテンポ（8分＋ベース、図解区間）
  → 「間」の前で少し積み上がる → 間明けで開く（広いパッド、対旋律、シェイカー）
  → IV–V(sus4→V)–I で終止。最後の主和音は最後のナレ終了直後の拍に置き、bgm.end までに自然に減衰。
- 声の帯域（1〜4kHz）を避ける：旋律・アルペジオの基音は D3〜D5（147〜587Hz）、倍音は弱く、低域通過。

  python3 scripts/33_make_temp_bgm.py
"""
import json, pathlib
import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "audio/bgm"
SR = 48000
rng = np.random.default_rng(33)
T = json.loads((ROOT / "comp/timeline.json").read_text())

B0 = T["bgm"]["start"]; BEND = T["bgm"]["end"]
BEND = BEND or T["duration"]
LEN = BEND - B0
N = int(round(LEN * SR))

if T["bgm"].get("pause"):
    PS, PE = T["bgm"]["pause"]["start"], T["bgm"]["pause"]["end"]
    # ---- テンポ：B0〜PE が整数小節 --------------------------------------------------------
    cands = []
    for nb in range(4, 60):
        bpm = 60 * 4 * nb / (PE - B0)
        if 85 <= bpm <= 100: cands.append((abs(bpm - 92), nb, bpm))
    _, PAUSE_BAR, BPM = min(cands)
else:
    # 「間」のない構成（v4.5 以降の24小節の格子）：timeline の格子の拍をそのまま使い、
    # 9小節目（いちばん強い頭＝「はかる」）から「開く」。曲を選ぶまでのつなぎ（New Departure の代わり）
    PS = PE = -1.0
    BPM = 60 / T["grid"]["beat"]
    PAUSE_BAR = 8
BEAT = 60 / BPM; BAR = 4 * BEAT
NBEATS = int(LEN / BEAT) + 1

# 最後の主和音：最後のナレ終了＋0.3秒以降で、残りが2.0秒以上ある最初の拍
last_vo_end = max(v["start"] + v["dur"] for v in T["vo"])
FINAL = None
for b in range(NBEATS):
    tb = B0 + b * BEAT
    if tb >= last_vo_end + 0.3 and BEND - tb >= 2.0:
        FINAL = b; break
if FINAL is None:  # 収まらなければ、残り2秒を確保できる最後の拍
    FINAL = int((BEND - 2.0 - B0) / BEAT)
FINAL_T = B0 + FINAL * BEAT
TAIL = BEND - FINAL_T

# 区間の境目（timeline の場面から）
def scene_start(prefix, default):
    for s in T["scenes"]:
        if s["id"].startswith(prefix): return s["start"]
    return default
D1 = scene_start("d1", B0 + 8 * BAR)
bar_of = lambda t: int(np.floor((t - B0) / BAR + 1e-6))
BAR_D1 = max(2, bar_of(D1))
BAR_BUILD = max(BAR_D1, PAUSE_BAR - 3)   # 「間」の前の3小節で積み上げ
FINAL_BAR = FINAL // 4

# ---- 和音 ------------------------------------------------------------------------------
CH = {  # pad voicing (MIDI), bass, arp pool
    "I":   dict(pad=[50, 57, 62, 66, 69], bass=38, arp=[62, 66, 69, 74, 69, 66, 62, 57]),
    "V":   dict(pad=[45, 52, 57, 61, 64], bass=45, arp=[61, 64, 69, 73, 69, 64, 61, 57]),
    "vi":  dict(pad=[47, 54, 59, 62, 66], bass=47, arp=[59, 62, 66, 71, 66, 62, 59, 54]),
    "IV":  dict(pad=[43, 50, 55, 59, 62], bass=43, arp=[59, 62, 67, 71, 67, 62, 59, 55]),
    "Vs":  dict(pad=[45, 52, 57, 62, 64], bass=45, arp=[62, 64, 69, 74, 69, 64, 62, 57]),
    "ii":  dict(pad=[52, 55, 59, 64, 67], bass=40, arp=[59, 64, 67, 71, 67, 64, 59, 55]),
}
MEL = {"I": [66, 69], "V": [64, 61], "vi": [62, 66], "IV": [62, 67], "Vs": [62, 61], "ii": [67, 64]}
CYCLE = ["I", "V", "vi", "IV"]

def chord_of_bar(b):
    if b < 2: return "I"
    if b == PAUSE_BAR - 1: return "V"
    if b == PAUSE_BAR - 2: return "ii"
    if b < PAUSE_BAR: return CYCLE[(b - 2) % 4]
    if b == FINAL_BAR: return "Vs"
    if b == FINAL_BAR - 1: return "IV"
    if b == FINAL_BAR - 2: return "vi"
    return CYCLE[(b - PAUSE_BAR) % 4]

def section(b):
    if b >= PAUSE_BAR: return "open"
    if b >= BAR_BUILD: return "build"
    if b >= BAR_D1: return "steady"
    if b >= 2: return "arp"
    return "intro"

mtof = lambda m: 440.0 * 2 ** ((m - 69) / 12)

# ---- 音源 ------------------------------------------------------------------------------
L = np.zeros(N); R = np.zeros(N)

def place(sig_l, sig_r, t):
    """t（ファイル内秒）に置く。「間」の中に入る分は 120ms で切ってフェード。"""
    n0 = int(round(t * SR))
    if n0 >= N: return
    n = min(len(sig_l), N - n0)
    a, b = sig_l[:n].copy(), sig_r[:n].copy()
    ps, pe = int((PS - B0) * SR), int((PE - B0) * SR)
    if n0 < ps < n0 + n:              # 「間」に食い込む音は手前で減衰させて止める
        k = ps - n0; r = int(0.12 * SR)
        env = np.ones(n); env[k:k + r] = np.linspace(1, 0, len(env[k:k + r])); env[k + r:] = 0
        a *= env; b *= env
    if ps <= n0 < pe:
        return
    L[n0:n0 + n] += a; R[n0:n0 + n] += b

def adsr(n, att, rel_start, rel, decay_tau=None):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(att, 1e-4))
    if decay_tau: e *= np.exp(-t / decay_tau)
    e *= np.clip(1 - (t - rel_start) / rel, 0, 1)
    return e

def pad_note(m, dur, gain, width, att=0.7, rel=0.9, cutoff=900.0, tau=None):
    f = mtof(m); n = int((dur + rel) * SR); t = np.arange(n) / SR
    env = adsr(n, att, dur, rel, tau)
    out = []
    for side, det in ((0, -1), (1, +1)):
        y = np.zeros(n)
        for k, cents in enumerate((0.0, 7.0 * det, -4.0 * det)):
            ff = f * 2 ** (cents / 1200)
            ph = rng.uniform(0, 2 * np.pi)
            h = 1
            while ff * h < 2600:
                w = (1 / h) / (1 + (ff * h / cutoff) ** 2)
                y += w * np.sin(2 * np.pi * ff * h * t + ph * h)
                h += 1
        out.append(y * env * gain / 3)
    l, r = out
    mid = (l + r) / 2
    return mid + width * (l - mid), mid + width * (r - mid)

def pluck(m, gain, pan=0.0, tau0=1.1, bright=1.0, dur=None):
    f = mtof(m); d = dur or 2.5; n = int(d * SR); t = np.arange(n) / SR
    y = np.zeros(n); h = 1
    while f * h < 3200 and h <= 14:
        a = bright ** (h - 1) / h ** 1.7
        tau = tau0 / (1 + 0.9 * (h - 1))
        y += a * np.sin(2 * np.pi * f * h * t) * np.exp(-t / tau)
        h += 1
    y *= np.minimum(1, t / 0.002)
    y[-int(0.03 * SR):] *= np.linspace(1, 0, int(0.03 * SR))
    y *= gain
    return y * np.sqrt(0.5 * (1 - pan)), y * np.sqrt(0.5 * (1 + pan))

def bass_note(m, dur, gain, tau=1.4):
    f = mtof(m); n = int((dur + 0.1) * SR); t = np.arange(n) / SR
    y = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(4 * np.pi * f * t) + 0.12 * np.sin(6 * np.pi * f * t)
    y *= adsr(n, 0.012, dur, 0.1, tau) * gain
    return y * 0.707, y * 0.707

def soft_line(m, dur, gain, pan):
    """対旋律：柔らかいフルート／弦の中間のような音（ゆるいビブラート、強い低域通過）。"""
    f = mtof(m); n = int((dur + 0.5) * SR); t = np.arange(n) / SR
    vib = 1 + 0.003 * np.sin(2 * np.pi * 5.0 * t) * np.minimum(1, t / 0.6)
    ph = 2 * np.pi * np.cumsum(f * vib) / SR
    y = np.sin(ph) + 0.18 * np.sin(2 * ph) + 0.05 * np.sin(3 * ph)
    y *= adsr(n, 0.25, dur, 0.5) * gain
    return y * np.sqrt(0.5 * (1 - pan)), y * np.sqrt(0.5 * (1 + pan))

HP6K = butter(2, 6000, "highpass", fs=SR, output="sos")
def shaker(gain, pan):
    n = int(0.07 * SR); t = np.arange(n) / SR
    y = sosfilt(HP6K, rng.standard_normal(n)) * np.minimum(1, t / 0.008) * np.exp(-t / 0.018) * gain
    return y * np.sqrt(0.5 * (1 - pan)), y * np.sqrt(0.5 * (1 + pan))

# ---- 配置 ------------------------------------------------------------------------------
LEVEL = {"intro": 0.8, "arp": 0.8, "steady": 0.85, "build": 0.92, "open": 1.0}
for b in range(0, FINAL_BAR + 1):
    ch = chord_of_bar(b); sec = section(b); c = CH[ch]; g = LEVEL[sec]
    t0 = b * BAR
    last_bar = b == FINAL_BAR
    bar_beats = (FINAL - 4 * b) if last_bar else 4
    if bar_beats <= 0: break
    # 最終小節前半：Vsus4（2拍）→ V（残り）
    segs = [(0, bar_beats, ch)]
    if last_bar and bar_beats >= 2:
        segs = [(0, bar_beats / 2, "Vs"), (bar_beats / 2, bar_beats / 2, "V")]
    for sb, nbt, cc in segs:
        cv = CH[cc]; ts = t0 + sb * BEAT; d = nbt * BEAT
        width = 1.0 if sec == "open" else 0.6
        cut = 1100.0 if sec in ("open", "build") else 800.0
        if b == 0: att = 1.2
        else: att = 0.5
        for m in cv["pad"]:
            l, r = pad_note(m, d, 0.10 * g, width, att=att, cutoff=cut)
            place(l, r, ts)
        if sec == "build":  # 低い弦のふくらみ（小節ごとにクレッシェンド）
            k = b - BAR_BUILD + 1
            l, r = pad_note(cv["pad"][0], d, 0.05 * k, 0.4, att=d * 0.8, rel=0.3, cutoff=500.0)
            place(l, r, ts)
    # アルペジオ
    if sec != "intro":
        step = 1.0 if sec == "arp" else 0.5
        nsteps = int(bar_beats / step)
        for i in range(nsteps):
            m = c["arp"][int(i * step * 2) % 8] if step == 0.5 else c["arp"][(i * 2) % 8]
            if last_bar: m = (CH["Vs"] if i * step < bar_beats / 2 else CH["V"])["arp"][int(i * step * 2) % 8]
            acc = 1.0 if (i * step) % 2 == 0 else 0.75
            pan = -0.35 if i % 2 == 0 else 0.35
            l, r = pluck(m, 0.075 * g * acc, pan, tau0=0.9 if sec != "open" else 1.2,
                         bright=0.55 if sec != "open" else 0.62)
            place(l, r, t0 + i * step * BEAT)
    # ベース（1・3拍）
    if sec in ("steady", "build", "open"):
        for i in range(0, int(bar_beats), 2):
            m = c["bass"] if not last_bar else 45
            l, r = bass_note(m, 1.8 * BEAT, 0.16 * g)
            place(l, r, t0 + i * BEAT)
    # 対旋律（開いた区間のみ。2分音符、基音 D4〜A4 = 294〜440Hz）
    if sec == "open" and not last_bar:
        for i, m in enumerate(MEL[ch]):
            l, r = soft_line(m, 1.9 * BEAT, 0.05, 0.15)
            place(l, r, t0 + i * 2 * BEAT)
    if last_bar:
        l, r = soft_line(64, bar_beats * BEAT * 0.95, 0.05, 0.15); place(l, r, t0)
    # シェイカー（開いた区間：16分、強弱つき）
    if sec == "open":
        for i in range(int(bar_beats * 4)):
            acc = [1.0, 0.35, 0.6, 0.35][i % 4]
            l, r = shaker(0.010 * acc, 0.3)
            place(l, r, t0 + i * BEAT / 4 + rng.normal(0, 0.004))

# 最後の主和音：パッド＋低いD＋ゆっくりしたストラム。bgm.end で約 −40dB まで減衰
tau = TAIL / 4.6
t_fin = FINAL * BEAT
for m in CH["I"]["pad"] + [74]:
    l, r = pad_note(m, TAIL, 0.11, 1.0, att=0.06, rel=0.05, cutoff=1000.0, tau=tau)
    place(l, r, t_fin)
l, r = bass_note(38, TAIL, 0.18, tau=tau); place(l, r, t_fin)
for i, m in enumerate([50, 57, 62, 66, 69, 74]):
    l, r = pluck(m, 0.07, -0.4 + 0.16 * i, tau0=min(1.2, tau * 1.2), bright=0.6, dur=TAIL)
    place(l, r, t_fin + i * 0.035)
l, r = soft_line(66, TAIL * 0.7, 0.05, 0.15); place(l, r, t_fin)

# ---- 仕上げ ----------------------------------------------------------------------------
x = np.stack([L, R], 1)
# 声の帯域を少しだけ空ける：2.5kHz 中心に −4dB のゆるいピーキングEQ（RBJ biquad, Q=0.7）＋ 12kHz 低域通過
def peaking(f0, gain_db, q):
    A = 10 ** (gain_db / 40); w = 2 * np.pi * f0 / SR; al = np.sin(w) / (2 * q)
    b = np.array([1 + al * A, -2 * np.cos(w), 1 - al * A]); a = np.array([1 + al / A, -2 * np.cos(w), 1 - al / A])
    return np.concatenate([b / a[0], a / a[0]])[None, :]
x = sosfilt(peaking(2500, -4.0, 0.7), x, axis=0)
x = sosfilt(butter(2, 12000, "lowpass", fs=SR, output="sos"), x, axis=0)   # シェイカー（6kHz〜）は通す
# 終端：最後の主和音は自然減衰済み。残りを 40ms で 0 に
f = int(0.04 * SR); x[-f:] *= np.linspace(1, 0, f)[:, None]
x[:int(0.01 * SR)] *= np.linspace(0, 1, int(0.01 * SR))[:, None]
x = x / np.abs(x).max() * 10 ** (-3 / 20)
OUT.mkdir(parents=True, exist_ok=True)
sf.write(OUT / "temp_bgm.wav", x.astype(np.float32), SR, subtype="PCM_24")

beats = []
for b in range(NBEATS):
    tf = b * BEAT
    if tf > LEN: break
    beats.append({"bar": b // 4 + 1, "beat": b % 4 + 1, "t": round(B0 + tf, 4), "t_file": round(tf, 4)})
info = {
    "note": "TEMPORARY placeholder BGM (algorithmic). t = timeline seconds, t_file = seconds in temp_bgm.wav",
    "bpm": round(BPM, 3), "beat_sec": round(BEAT, 5), "bar_sec": round(BAR, 5), "meter": "4/4", "key": "D major",
    "file_offset_in_timeline": B0,
    "pause": {"start": PS, "end": PE, "end_is_bar": PAUSE_BAR + 1} if PE > 0 else None, "open_bar": PAUSE_BAR + 1,
    "final_chord": {"t": round(FINAL_T, 4), "bar": FINAL // 4 + 1, "beat": FINAL % 4 + 1, "tail_sec": round(TAIL, 3)},
    "sections": [{"bar": b + 1, "t": round(B0 + b * BAR, 4), "chord": chord_of_bar(b), "section": section(b)}
                 for b in range(FINAL_BAR + 1)],
    "beats": beats,
}
(OUT / "temp_bgm_beats.json").write_text(json.dumps(info, ensure_ascii=False, indent=1))
print(f"temp_bgm.wav {LEN:.2f}s  {BPM:.2f} BPM  bar {BAR:.3f}s  pause→bar {PAUSE_BAR+1} @ {PE:.3f}s  "
      f"final I @ {FINAL_T:.3f}s (bar {FINAL//4+1} beat {FINAL%4+1}, tail {TAIL:.2f}s)")
