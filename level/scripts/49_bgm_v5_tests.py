"""編集計画 v5.1（plan/editing_v5.md §2・§8.1）の曲の案 M1a〜M1d と 83.4 秒版 S83 を、聞き比べ用の mp3 にする（本番の 34_prep_bgm.py とは別。ナレは入れない）。
使い方:
  source .venv/bin/activate
  python3 scripts/49_bgm_v5_tests.py <曲のフォルダ> <出力フォルダ> [S の元映像（現場音の下地用。省略可）]
  例: python3 scripts/49_bgm_v5_tests.py /mnt/project-files/dova/ /mnt/project-files/level/audio_tests_v5/ source/S_sueru.mp4
出力（出力フォルダに。リポジトリには入れない＝曲の再配布にあたるため）
  <案>.mp3        曲の編集だけ
  <案>_guide.mp3  曲＋拍 B の切れ目の印の音（高い「ピッ」＝拍の切れ目、低い「ポン」2回＝見せ場の同期点）＋ごく薄い現場の音（S 42–82 秒）
  bgm_v5_tests.md 案ごとの小節の対応表・つなぎ目の時刻・印の時刻
決まり（基準点の 34_prep_bgm.py と同じ）：小節の頭でだけ切ってつなぐ、つなぎ目は 60ms の等パワー、最後は曲本来の終止。
「止め（stop）」＝前の小節の本来の続き（指定した小節）の頭の和音を 1 拍だけ鳴らして減衰させ、残りは無音（現場の音だけ）。次の小節で曲が戻る。
"""
import sys, pathlib, subprocess, tempfile, json
import numpy as np, soundfile as sf

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib_audio import integrated

SR = 48000
SONGS, OUT = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
S_SRC = pathlib.Path(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3] else None
OUT.mkdir(parents=True, exist_ok=True)

ND = {"file": "01_new_departure.mp3", "b0": 1.9567, "bp": 0.63199, "last": 36}
KO = {"file": "03_komorebi.mp3", "b0": 0.332, "bp": 0.68180, "last": 37}

# 拍 B の切れ目（編集後の小節、1 始まり）と見せ場
B_V5 = {"B0": 1, "B1": 2, "B2": 4, "B3": 7, "B4": 10, "B5": 14, "B6": 21, "B7": 26, "B8": 30, "B9": 33, "end": 37}
SYNC_V5 = {4: "曲が戻る：人が来て据える（声なし）", 9: "息つぎ：縦40倍で坂が立ち上がる", 10: "一番強い一打：「その坂をつくる前に」",
           14: "K の実写：かがんでのぞく（33.49 から）", 18: "曲が C へ（水の面：「読むのは、線から下の深さ」）", 24: "クイズの間（息つぎ／止め）",
           25: "一打：「深いほうが、低い」", 33: "最後の一打：N の顔の寄り"}
# 83.4 秒版（B8 を抜く。編集計画 §8.1）：B9 が E30 から
B_S83 = {"B0": 1, "B1": 2, "B2": 4, "B3": 7, "B4": 10, "B5": 14, "B6": 21, "B7": 26, "B9": 30, "end": 34}
SYNC_S83 = {k: v for k, v in SYNC_V5.items() if k < 30}; SYNC_S83[30] = "最後の一打：N の顔の寄り（13→33 のつなぎ目）"
DUCK_TITLE = [(2.40, 7.58, -18.0, 0.5, 0.8)]      # 題（E2–3）は曲を下げ、道の音を前に（E4 で戻す）
BED_UP = [(2.40, 15.17, 10.0)]                      # guide：題と B2（声なし・同期音が主役）は現場の音を +10 dB
HOLD = {"at_bar": 33, "after": 4.44, "len": 3.0, "xfade": 0.4}
VARIANTS = [
    {"id": "M1a_ND_hush", "song": ND, "title": "M1a New Departure・クイズは息つぎ（題で曲を下げる）",
     "plan": [("bars", 1, 3), ("bars", 3, 16), ("bars", 25, 30), ("bars", 8, 16), ("bars", 33, 36)],
     "hold": HOLD, "nbars": 36, "B": B_V5, "sync": SYNC_V5, "duck": DUCK_TITLE},
    {"id": "M1b_ND_stop", "song": ND, "title": "M1b New Departure・クイズは止め・31小節目の頭の和音（題で曲を下げる）",
     "plan": [("bars", 1, 3), ("bars", 3, 16), ("bars", 25, 30), ("stop", 1, 31), ("bars", 9, 16), ("bars", 33, 36)],
     "hold": HOLD, "nbars": 36, "B": B_V5, "sync": SYNC_V5, "duck": DUCK_TITLE},
    {"id": "M1c_ND_stop_noduck", "song": ND, "title": "M1c M1b と同じで、題で曲を下げない（比較用）",
     "plan": [("bars", 1, 3), ("bars", 3, 16), ("bars", 25, 30), ("stop", 1, 31), ("bars", 9, 16), ("bars", 33, 36)],
     "hold": HOLD, "nbars": 36, "B": B_V5, "sync": SYNC_V5, "duck": []},
    {"id": "M1d_ND_stop8", "song": ND, "title": "M1d クイズは止め・止める和音を元の8小節目の頭に（題で曲を下げる）（おすすめ。試聴で決める）",
     "plan": [("bars", 1, 3), ("bars", 3, 16), ("bars", 25, 30), ("stop", 1, 8), ("bars", 9, 16), ("bars", 33, 36)],
     "hold": HOLD, "nbars": 36, "B": B_V5, "sync": SYNC_V5, "duck": DUCK_TITLE},
    {"id": "S83_ND_stop", "song": ND, "title": "S83 83.4 秒版（B8 を抜く、M1d の止め、13→33）",
     "plan": [("bars", 1, 3), ("bars", 3, 16), ("bars", 25, 30), ("stop", 1, 8), ("bars", 9, 13), ("bars", 33, 36)],
     "hold": dict(HOLD, at_bar=30), "nbars": 33, "B": B_S83, "sync": SYNC_S83, "duck": DUCK_TITLE},
]
ONLY = set(sys.argv[4].split(",")) if len(sys.argv) > 4 else None

_cache = {}
def load(song):
    if song["file"] not in _cache:
        with tempfile.TemporaryDirectory() as td:
            w = pathlib.Path(td) / "a.wav"
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(SONGS / song["file"]), "-ar", str(SR), "-ac", "2", str(w)], check=True)
            _cache[song["file"]], _ = sf.read(w)
    return _cache[song["file"]]

def fade(n, kind):
    u = np.linspace(0, 1, max(n, 1))[:, None]
    return np.sin(u * np.pi / 2) if kind == "in" else np.cos(u * np.pi / 2)

def build(v):
    s = v["song"]; x = load(s); BAR = 4 * s["bp"]; xf = int(0.06 * SR)
    bar_s = lambda n: int(round((s["b0"] + (n - 1) * BAR) * SR))
    y = np.zeros((0, 2)); joins = []; table = []; ebar = 1
    for op in v["plan"]:
        kind = op[0]
        if kind in ("bars", "fadein_bars", "bars_fadeout"):
            a, b = op[1], op[2]
            s0 = bar_s(a); e0 = len(x) if b >= s["last"] else bar_s(b + 1)
            seg = x[max(s0 - xf // 2, 0):min(e0 + xf // 2, len(x))].copy()
            if kind == "fadein_bars":
                n = int(op[3] * SR); seg[:n] *= fade(n, "in")
            if kind == "bars_fadeout":
                n = int(op[3] * SR); seg[-n - xf // 2:] *= np.concatenate([fade(n, "out"), np.zeros((xf // 2, 1))])
            if len(y) == 0:
                y = seg[xf // 2:] if s0 >= xf // 2 else seg
            else:
                joins.append(round((len(y) - xf // 2) / SR, 3))
                w = np.sqrt(np.linspace(0, 1, xf))[:, None]
                y[-xf:] = y[-xf:] * w[::-1] + seg[:xf] * w
                y = np.concatenate([y, seg[xf:]])
            for n_ in range(a, b + 1):
                table.append((ebar, f"曲 {n_}")); ebar += 1
        elif kind in ("stop", "rest"):
            nb = op[1]; L = int(round(nb * BAR * SR))
            seg = np.zeros((L, 2))
            if kind == "stop":   # 次に戻る小節の頭の和音を 1 拍＋減衰で鳴らす
                h = op[2]; hit = x[bar_s(h):bar_s(h) + int(1.6 * SR)].copy()
                env = np.exp(-np.linspace(0, 1.6, len(hit)) / 0.35)[:, None]; env[:int(0.25 * SR)] = 1.0
                seg[:len(hit)] = hit * env
            # 前の音の末尾 10ms を落とし、無音へ
            f10 = int(0.01 * SR); y[-f10:] *= fade(f10, "out")
            joins.append(round(len(y) / SR, 3)); y = np.concatenate([y, seg])
            for _ in range(nb):
                table.append((ebar, "止め（和音1拍→無音）" if kind == "stop" else "曲なし（現場の音だけ）")); ebar += 1
    if v["hold"]:
        hd = v["hold"]; at = ((hd["at_bar"] - 1) * BAR + hd["after"])
        ia, L, h = int(round(at * SR)), int(round(hd["len"] * SR)), int(round(hd["xfade"] * SR))
        u = np.linspace(0, 1, h)[:, None]
        y = np.concatenate([y[:ia - h // 2], y[ia - h // 2:ia + h - h // 2] * np.cos(u * np.pi / 2) + y[ia - L - h // 2:ia - L + h - h // 2] * np.sin(u * np.pi / 2),
                            y[ia - L + h - h // 2:]])
        joins.append(round(at, 3))
    n = int(round(v["nbars"] * BAR * SR))
    y = y[:n] if len(y) >= n else np.concatenate([y, np.zeros((n - len(y), 2))])
    f = int(0.01 * SR); y[:f] *= fade(f, "in")
    fo = int(0.45 * SR); y[-fo:] *= fade(fo, "out")
    g = np.zeros(len(y))
    for t0, t1, db, r_in, r_out in v.get("duck", []):
        tt = np.arange(len(y)) / SR
        a = np.clip((tt - t0) / r_in, 0, 1) * np.clip((t1 - tt) / r_out, 0, 1)
        g = np.minimum(g, db * a)
    y = y * (10 ** (g / 20))[:, None]
    return y, BAR, joins, table

def tick(freq, dur, amp):
    t = np.arange(int(dur * SR)) / SR
    return (amp * np.sin(2 * np.pi * freq * t) * np.exp(-t / (dur / 4)))[:, None] * np.ones((1, 2))

def bed(n):
    if not S_SRC or not S_SRC.exists(): return np.zeros((n, 2))
    with tempfile.TemporaryDirectory() as td:
        w = pathlib.Path(td) / "s.wav"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", "42", "-t", "40", "-i", str(S_SRC), "-vn", "-ar", str(SR), "-ac", "2",
                        "-af", "highpass=f=80,lowpass=f=8000", str(w)], check=True)
        b, _ = sf.read(w)
    reps = int(np.ceil(n / len(b))); b = np.concatenate([b] * reps)[:n]
    return b

def write_mp3(y, path):
    with tempfile.TemporaryDirectory() as td:
        w = pathlib.Path(td) / "o.wav"; sf.write(w, y, SR)
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(w), "-b:a", "192k", str(path)], check=True)

md = ["# 曲の案 M1a〜M1d と 83.4 秒版 S83 の聞き比べ（編集計画 v5.1 §2・§8.1）", "",
      "作り方：`python3 scripts/49_bgm_v5_tests.py /mnt/project-files/dova/ /mnt/project-files/level/audio_tests_v5/ source/S_sueru.mp4`", "",
      "- `<案>.mp3`：曲の編集だけ。`<案>_guide.mp3`：＋拍 B の切れ目に高い「ピッ」、見せ場の同期点に低い「ポン」、ごく薄い現場の音（S 42–82 秒）。",
      "- guide では題と B2（2.4–15.2 秒）の現場の音を +10 dB（声なし・同期音が主役の区間の聞こえ方の見本）。",
      "- 音量は聞き比べのため、どれも曲の統合ラウドネス −20 LUFS にそろえた（本番のミックスは −24 LUFS、ナレの下でさらに下げる）。", ""]
for v in VARIANTS:
    if ONLY and v["id"] not in ONLY: continue
    y, BAR, joins, table = build(v)
    g = 10 ** ((-20 - integrated(y)) / 20); y = y * g
    pk = np.abs(y).max()
    if pk > 0.89: y *= 0.89 / pk
    write_mp3(y, OUT / f"{v['id']}.mp3")
    b = bed(len(y))
    if np.abs(b).max() > 0:
        b *= 10 ** ((-38 - integrated(b)) / 20)    # 曲より約 18 dB 下
        tt = np.arange(len(b)) / SR; up = np.zeros(len(b))
        for t0, t1, db in BED_UP:
            up = np.maximum(up, db * np.clip((tt - t0) / 0.5, 0, 1) * np.clip((t1 - tt) / 0.8, 0, 1))
        b *= (10 ** (up / 20))[:, None]
    gd = y + b
    marks = []
    for name, eb in v["B"].items():
        t0 = (eb - 1) * BAR; i = int(round(t0 * SR)); k = tick(1760, 0.09, 0.30)
        if i + len(k) <= len(gd): gd[i:i + len(k)] += k
        marks.append((name, round(t0, 2)))
    for eb, what in v["sync"].items():
        t0 = (eb - 1) * BAR
        for dt in (0.0, 0.16):
            i = int(round((t0 + dt) * SR)); k = tick(440, 0.12, 0.35)
            if i + len(k) <= len(gd): gd[i:i + len(k)] += k
    pk = np.abs(gd).max()
    if pk > 0.95: gd *= 0.95 / pk
    write_mp3(gd, OUT / f"{v['id']}_guide.mp3")
    md += [f"## {v['title']}（`{v['id']}.mp3`）", "",
           f"- 曲 {v['song']['file']}、1小節 {BAR:.3f} 秒、編集後 {v['nbars']} 小節 = {v['nbars'] * BAR:.2f} 秒",
           f"- 組み方：{' ＋ '.join(str(op) for op in v['plan'])}" + (f"、最後の和音のばし {v['hold']}" if v["hold"] else ""),
           f"- つなぎ目・止めの時刻（秒）：{', '.join(f'{j:.2f}' for j in joins)}",
           f"- 拍 B の頭（ピッ）：{', '.join(f'{n} {t:.2f}' for n, t in marks)}",
           "- 見せ場（ポン）：" + "、".join(f"{eb}小節 {(eb - 1) * BAR:.2f} 秒 {w}" for eb, w in v["sync"].items()), "",
           "| 編集後の小節 | 時刻 | 中身 |", "|---|---|---|"]
    md += [f"| {eb} | {(eb - 1) * BAR:.2f} | {what} |" for eb, what in table]
    md.append("")
    print(v["id"], f"{len(y) / SR:.2f}s joins {joins}")
(OUT / "bgm_v5_tests.md").write_text("\n".join(md) + "\n")
