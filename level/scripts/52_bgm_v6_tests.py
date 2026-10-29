"""編集計画 v6（plan/editing_v6.md §2・§4）の曲の案を、聞き比べ用の mp3 にする（本番の 34_prep_bgm.py とは別。ナレは入れない）。
49_bgm_v5_tests.py を元に、28小節（1〜16＋25〜36）と 32小節（1〜19＋24〜36）に置き直した。
使い方:
  source .venv/bin/activate
  python3 scripts/52_bgm_v6_tests.py <曲のフォルダ> <出力フォルダ> [S の元映像（現場音の下地用。省略可）] [案の id をカンマで（省略で全部）]
  例: python3 scripts/52_bgm_v6_tests.py /mnt/project-files/dova/ /mnt/project-files/level/audio_tests_v6/ source/S_sueru.mp4
出力（出力フォルダに。リポジトリには入れない＝曲の再配布にあたるため）
  <案>.mp3        曲の編集だけ
  <案>_guide.mp3  曲＋拍の頭の印（高い「ピッ」）＋同期点の印（低い「ポン」2回）＋鉄琴の仮の音（編集計画 §4.1 の音程）＋ごく薄い現場の音
  bgm_v6_tests.md 案ごとの小節の対応表・つなぎ目・同期点・鉄琴の時刻と音
決まり（34_prep_bgm.py と同じ）：小節の頭でだけ切ってつなぐ、つなぎ目は 60ms の等パワー、最後は曲本来の終止＋最後の和音を 3 秒のばす。
「止め（stop）」＝指定した小節の頭の和音を 1 拍鳴らして減衰（時定数 0.35 秒）、残りは無音（現場の音だけ）。次の小節で曲が戻る。
"""
import sys, pathlib, subprocess, tempfile
import numpy as np, soundfile as sf

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib_audio import integrated

SR = 48000
SONGS, OUT = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
S_SRC = pathlib.Path(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3] else None
ONLY = set(sys.argv[4].split(",")) if len(sys.argv) > 4 and sys.argv[4] else None
OUT.mkdir(parents=True, exist_ok=True)

ND = {"file": "01_new_departure.mp3", "b0": 1.9567, "bp": 0.63199, "last": 36}
BAR = 4 * ND["bp"]; BEAT = ND["bp"]
T = lambda bar, beat=1: round((bar - 1) * BAR + (beat - 1) * BEAT, 3)   # 編集後の小節・拍 → 秒

# 拍 B の頭（編集後の小節）
B28 = {"B1": 1, "B2": 2, "B3": 4, "B4": 6, "B5": 9, "B6": 12, "B7": 13, "B8": 16, "B9": 18, "B10": 21, "B11": 25, "end": 29}
B32 = {"B1": 1, "B2": 2, "B3": 4, "B4": 6, "B5": 9, "B6": 13, "B7": 14, "B8": 18, "B9": 20, "B10": 24, "B11": 29, "end": 33}

# 鉄琴（ハ長調の五音 C D E G A。地面が低い＝棒が長いほど低い音）。周波数は 6 オクターブ目
C6, D6, E6, G6, A6 = 1046.5, 1174.7, 1318.5, 1568.0, 1760.0
def glock28():
    return [(T(10, 3), [G6], 0.18, "点線が標尺に当たる（線の音）"),
            (T(11, 3), [E6], 0.22, "棒1 が地面に着く（P1）"),
            (T(13, 4), [C6], 0.30, "棒2＝一番長い（P2、一番低い音）"),
            (round(T(14) + 0.948, 3), [D6], 0.24, "棒3（P3）"),
            (round(T(14) + 1.580, 3), [G6], 0.22, "棒4（P4）"),
            (round(T(14) + 2.054, 3), [A6], 0.22, "棒5＝一番短い（P5、一番高い音）"),
            (T(15, 3), [C6, E6, G6], 0.26, "点がつながりきる（和音、30ms ずつ転がす）"),
            (T(28, 2), [G6], 0.14, "点線が縮んで水準のアイコンに戻りきる")]
def glock32():   # 32小節：B5 が 9–12、B7 が 14–17 小節（編集計画 §1.6）
    return [(T(10, 3), [G6], 0.18, "点線が標尺に当たる"),
            (T(11, 3), [E6], 0.22, "棒1 が地面に着く（P1）"),
            (T(15, 1), [C6], 0.30, "棒2＝一番長い（P2）"),
            (T(16, 1), [D6], 0.24, "棒3"),
            (T(16, 2), [G6], 0.22, "棒4"),
            (round(T(16, 2) + 0.474, 3), [A6], 0.22, "棒5"),
            (T(17, 1), [C6, E6, G6], 0.26, "点がつながりきる（和音）"),
            (T(32, 4), [G6], 0.14, "終わりの画の点線がアイコンに戻りきる")]

SYNC28 = [(T(3, 4), "機械が三脚に載る（S 53.0）＝題"), (T(8), "8小節：息つぎ／止め（N3 の「待っています」が終わる所）"),
          (T(9), "曲で一番強い頭＝なぞり始め"), (T(10, 3), "「一本の線」＝点線が標尺に当たる"), (T(11, 3), "「地面まで」＝棒が着く"),
          (T(13, 4), "「長く」＝一番長い棒"), (T(15, 3), "「つなぐと……」の間＝点がつながりきる"), (T(17), "曲のつなぎ目（K の手元の上）"),
          (T(20, 3), "「坂」＝新しい道の線が描き終わる"), (T(25), "最後の一打＝K の全画面"), (T(28), "終わりの画")]
SYNC32 = [(T(3, 4), "機械が三脚に載る＝題"), (T(8), "息つぎ／止め"), (T(9), "なぞり始め"), (T(10, 3), "点線が標尺に当たる"),
          (T(11, 3), "棒が着く"), (T(15, 1), "「長く」＝一番長い棒"), (T(17, 1), "点がつながりきる"), (T(20), "曲のつなぎ目（19→24）＝横顔が戻る（B9）"),
          (T(22, 3), "「坂」＝新しい道の線"), (55.90, "「自転車」＝上りの所が一度灯る"), (T(29), "最後の一打＝K の全画面"), (T(32), "終わりの画（紙の上の二人と点線）")]

DUCK_LAND = [(6.00, 7.70, -12.0, 0.4, 0.35)]   # 機械が載る音（7.06）を聞かせる（7.58 の 4 小節目で戻る）
HOLD28 = {"at_bar": 25, "after": 4.44, "len": 3.0, "xfade": 0.4}
HOLD32 = dict(HOLD28, at_bar=29)
VARIANTS = [
    {"id": "V6a_28_plain", "title": "V6a 28小節・止めなし（1〜16＋25〜36）",
     "plan": [("bars", 1, 16), ("bars", 25, 36)], "hold": HOLD28, "nbars": 28, "B": B28, "sync": SYNC28, "glock": glock28(),
     "duck": DUCK_LAND, "bedup": [(5.9, 7.7, 8.0)]},
    {"id": "V6b_28_stop8", "title": "V6b 28小節・8小節目で止め（K の静止の上。おすすめ）",
     "plan": [("bars", 1, 7), ("stop", 1, 8), ("bars", 9, 16), ("bars", 25, 36)], "hold": HOLD28, "nbars": 28, "B": B28, "sync": SYNC28,
     "glock": glock28(), "duck": DUCK_LAND, "bedup": [(5.9, 7.7, 8.0), (T(8), T(9), 8.0)]},
    {"id": "V6c_28_stop15", "title": "V6c 28小節・15小節目で止め（「つなぐと……」の間）",
     "plan": [("bars", 1, 14), ("stop", 1, 15), ("bars", 16, 16), ("bars", 25, 36)], "hold": HOLD28, "nbars": 28, "B": B28, "sync": SYNC28,
     "glock": glock28(), "duck": DUCK_LAND, "bedup": [(5.9, 7.7, 8.0), (T(15), T(16), 6.0)]},
    {"id": "V6d_32_stop8", "title": "V6d 32小節（80.9 秒）・8小節目で止め（1〜7＋止め＋9〜19＋24〜36）",
     "plan": [("bars", 1, 7), ("stop", 1, 8), ("bars", 9, 19), ("bars", 24, 36)], "hold": HOLD32, "nbars": 32, "B": B32, "sync": SYNC32,
     "glock": glock32(), "duck": DUCK_LAND, "bedup": [(5.9, 7.7, 8.0), (T(8), T(9), 8.0)]},
    {"id": "V6e_32_stop16", "title": "V6e 32小節・16小節目で止め（立ち替わりと「つなぐと……」が無音の中、つながる 40.45 で曲が戻る）",
     "plan": [("bars", 1, 15), ("stop", 1, 16), ("bars", 17, 19), ("bars", 24, 36)], "hold": HOLD32, "nbars": 32, "B": B32, "sync": SYNC32,
     "glock": glock32(), "duck": DUCK_LAND, "bedup": [(5.9, 7.7, 8.0), (T(16), T(17), 6.0)]},
    {"id": "V6f_32_plain", "title": "V6f 32小節・止めなし（1〜19＋24〜36）",
     "plan": [("bars", 1, 19), ("bars", 24, 36)], "hold": HOLD32, "nbars": 32, "B": B32, "sync": SYNC32,
     "glock": glock32(), "duck": DUCK_LAND, "bedup": [(5.9, 7.7, 8.0)]},
]

# ---- v7「高さの目印をつくる」（編集計画 editing_v7.md §4.1）。曲は V6d と同じ、鉄琴と同期点だけ違う ----
B7G = {"B1": 1, "B2": 2, "B3": 4, "B4": 6, "B5": 9, "B6": 13, "B7": 15, "B8": 18, "B9": 20, "B10": 22, "B11": 24, "B12": 29, "end": 33}
def glock_v7():
    return [(T(12, 2), [C6], 0.30, "B5 段差が光る（まえの地面が低い）"),
            (T(16, 1), [D6], 0.24, "B7 運ぶ印が S2 へ"),
            (T(16, 3), [G6], 0.22, "B7 運ぶ印が S3 へ"),
            (round(T(16, 3) + 0.790, 3), [A6], 0.22, "B7 運ぶ印が S4 に着く"),
            (T(17, 4), [C6, E6, G6], 0.26, "B7 オレンジの□が灯る（和音）"),
            (T(20, 3), [G6], 0.20, "B9 帰りの印が S3 へ"),
            (T(20, 4), [D6], 0.20, "B9 帰りの印が S2 へ"),
            (T(21, 1), [C6], 0.22, "B9 帰りの印が S1 へ"),
            (T(21, 2), [E6], 0.26, "B9 紺の□で行きと帰りが重なる（「合えば」。行きの最初と同じ音）"),
            (T(32, 4), [G6], 0.14, "終わりの画の□がアイコンに戻りきる")]
SYNC_V7 = [(6.952, "機械が載る＝題"), (T(8), "止め（8小節の和音）"), (18.96, "K 7.82 で止まる"), (T(9), "なぞり始め"),
           (23.60, "目からの点線がまえの標尺に届く（音なし）"), (24.44, "「うしろと」うしろのものさしがあらわれる"), (T(12, 2), "段差が光る"),
           (T(13), "実写 S 165.67"), (T(17, 4), "新しい高さの目印（オレンジの□）"), (T(18), "K の手元"), (T(20), "曲のつなぎ目＝帰り"),
           (T(21, 2), "「合えば」行きと帰りが重なる"), (T(21, 3), "□がオレンジ→紺"), (T(23, 3), "新しい道の線が描き終わる"), (T(29), "最後の一打＝K 8.53"), (T(32), "終わりの画")]
VARIANTS.append({"id": "V7d_32_stop8", "title": "V7d 32小節・8小節で止め（曲は V6d と同じ。鉄琴と同期点が v7）",
     "plan": [("bars", 1, 7), ("stop", 1, 8), ("bars", 9, 19), ("bars", 24, 36)], "hold": HOLD32, "nbars": 32, "B": B7G, "sync": SYNC_V7,
     "glock": glock_v7(), "duck": DUCK_LAND, "bedup": [(5.9, 7.7, 8.0), (T(8), T(9), 8.0)]})

# ---- v7.2「のぼって、わたって、おりる」（editing_v7.md v7.2 §4.1・§9）。32小節は曲が V6d と同じ。24小節は 1〜7＋止め＋9〜20＋33〜36 ----
def glock_v72():
    return [(T(12, 4), [C6], 0.30, "B5 しるしがまえのものさしをおりきる＝段差が光る（「おりる」の終わり）"),
            (T(15, 3), [D6], 0.24, "B7 着地1（1つ目の「となりへ」の終わり）"),
            (T(16, 1), [G6], 0.22, "B7 着地2（2つ目の「となりへ」）"),
            (T(16, 4), [A6], 0.22, "B7 着地3（「たどり着いた」）"),
            (T(17, 4), [C6, E6, G6], 0.26, "B7 新しい目印（線の□）が点線から実線に（「目印」）"),
            (T(21, 3), [E6], 0.26, "B9 帰りの線が右の□の高さに着く（「合えば」）"),
            (T(32, 4), [G6], 0.14, "終わりの画の□がアイコンに戻りきる")]
SYNC_V72 = [(6.952, "機械が載る＝題"), (T(8), "止め（8小節の和音）"), (18.96, "K 7.82 で止まる"), (T(9), "なぞり始め"),
            (20.99, "写真の上に目線（白の点線）"), (22.27, "「まっすぐ」目線が水平にたたまれる"), (23.80, "うしろへの目線（音なし）"), (T(11), "「目印」□が灯る"),
            (26.20, "「高さが」しるしが生まれる"), (26.95, "「のぼって」"), (27.95, "「わたって」機械で止まる"), (28.60, "わたって（後半）"), (29.00, "「おりる」"),
            (T(12, 4), "段差が光る"), (T(13), "実写 S 165.67"), (33.87, "「こえて」標尺手が機械の横を通る"), (T(15, 3), "着地1"), (T(16), "着地2"),
            (T(16, 4), "着地3「たどり着いた」"), (T(17, 4), "新しい□が実線に"), (T(18), "K の手元"), (T(20), "曲のつなぎ目＝実写 S 177"), (T(21), "帰りの図（据え直し）"),
            (T(21, 3), "「合えば」帰りの線が同じ高さに着く"), (T(21, 4), "「できあがり」□の線が紺に"), (T(22), "B10 □から引く"), (T(23, 3), "「道がつくられます」道の線が描き終わる"),
            (T(29), "最後の一打＝K 8.53"), (T(32), "終わりの画")]
VARIANTS.append({"id": "V72d_32_stop8", "title": "V72d 32小節・8小節で止め（曲は V6d と同じ。鉄琴 9 音と同期点が v7.2）",
     "plan": [("bars", 1, 7), ("stop", 1, 8), ("bars", 9, 19), ("bars", 24, 36)], "hold": HOLD32, "nbars": 32, "B": B7G, "sync": SYNC_V72,
     "glock": glock_v72(), "duck": DUCK_LAND, "bedup": [(5.9, 7.7, 8.0), (T(8), T(9), 8.0)]})
B24 = {"B1": 1, "B2": 2, "B3": 4, "B4": 6, "B5": 9, "B8": 13, "B7": 14, "B10": 17, "B11": 19, "B12": 21, "end": 25}
def glock_v72_24():
    return [(T(12, 4), [C6], 0.30, "B5 段差が光る"), (T(14, 4), [D6], 0.24, "B7 着地1"), (T(15, 1), [G6], 0.22, "B7 着地2"),
            (T(16, 1), [A6], 0.22, "B7 着地3「たどり着いた」"), (T(17, 1), [C6, E6, G6], 0.26, "新しい□が灯る＝B10 の頭"),
            (T(24, 4), [G6], 0.14, "終わりの画の□がアイコンに戻りきる")]
SYNC_V72_24 = [(6.952, "機械が載る＝題"), (T(8), "止め（8小節の和音）"), (18.96, "K 7.82 で止まる"), (T(9), "なぞり始め"),
               (22.27, "目線が水平にたたまれる"), (T(11), "「目印」□が灯る"), (26.95, "「のぼって」"), (27.95, "「わたって」"), (29.00, "「おりる」"), (T(12, 4), "段差が光る"),
               (T(13), "K 書く"), (T(14, 4), "着地1"), (T(15), "着地2"), (T(16), "着地3"), (T(17), "新しい□が実線に＝B10"),
               (T(18, 3), "道の線が描き終わる"), (T(19), "N の寄り"), (T(21), "最後の一打（曲 33）"), (T(23, 1), "終わりの画：□がオレンジ→紺"), (T(24), "アイコンへ")]
VARIANTS.append({"id": "V72s_24_stop8", "title": "V72s 24小節（60.67 秒、1本目と同じ尺）・8小節で止め（1〜7＋止め＋9〜20＋33〜36。つなぎ目 20→33）",
     "plan": [("bars", 1, 7), ("stop", 1, 8), ("bars", 9, 20), ("bars", 33, 36)], "hold": dict(HOLD28, at_bar=21), "nbars": 24, "B": B24,
     "sync": SYNC_V72_24, "glock": glock_v72_24(), "duck": DUCK_LAND, "bedup": [(5.9, 7.7, 8.0), (T(8), T(9), 8.0)]})

def glock_v72_b():   # 批評 v7.2 P1 の (b)：着地は3回目の A6 だけ、□は単音 C6
    return [g for g in glock_v72() if g[0] not in (T(15, 3), T(16, 1), T(17, 4))] + [(T(17, 4), [C6], 0.24, "B7 新しい□が実線に（単音）")]
VARIANTS.append(dict(VARIANTS[-2], id="V72d_32_stop8_b", title="V72d (b) 32小節・鉄琴は着地3の A6 と□の単音 C6 だけ（批評 v7.2 P1）", glock=glock_v72_b()))

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
    s = ND; x = load(s); xf = int(0.06 * SR)
    bar_s = lambda n: int(round((s["b0"] + (n - 1) * BAR) * SR))
    y = np.zeros((0, 2)); joins = []; table = []; ebar = 1
    for op in v["plan"]:
        kind = op[0]
        if kind == "bars":
            a, b = op[1], op[2]
            s0 = bar_s(a); e0 = len(x) if b >= s["last"] else bar_s(b + 1)
            seg = x[max(s0 - xf // 2, 0):min(e0 + xf // 2, len(x))].copy()
            if len(y) == 0:
                y = seg[xf // 2:] if s0 >= xf // 2 else seg
            else:
                joins.append(round((len(y) - xf // 2) / SR, 3))
                w = np.sqrt(np.linspace(0, 1, xf))[:, None]
                y[-xf:] = y[-xf:] * w[::-1] + seg[:xf] * w
                y = np.concatenate([y, seg[xf:]])
            for n_ in range(a, b + 1):
                table.append((ebar, f"曲 {n_}")); ebar += 1
        elif kind == "stop":
            nb, h = op[1], op[2]; L = int(round(nb * BAR * SR)) + xf // 2; seg = np.zeros((L, 2))
            y = y[:len(y) - xf // 2]   # 前の区間の重ねしろ（30ms）を落とし、和音を小節の頭ちょうどに置く
            hit = x[bar_s(h):bar_s(h) + int(1.6 * SR)].copy()
            env = np.exp(-np.linspace(0, 1.6, len(hit)) / 0.35)[:, None]; env[:int(0.25 * SR)] = 1.0
            seg[:len(hit)] = hit * env
            f10 = int(0.01 * SR); y[-f10:] *= fade(f10, "out")
            joins.append(round(len(y) / SR, 3)); y = np.concatenate([y, seg])
            table.append((ebar, f"止め（曲 {h} の頭の和音1拍→減衰→無音）")); ebar += 1
    hd = v["hold"]; at = (hd["at_bar"] - 1) * BAR + hd["after"]
    ia, L, h = int(round(at * SR)), int(round(hd["len"] * SR)), int(round(hd["xfade"] * SR))
    u = np.linspace(0, 1, h)[:, None]
    y = np.concatenate([y[:ia - h // 2], y[ia - h // 2:ia + h - h // 2] * np.cos(u * np.pi / 2) + y[ia - L - h // 2:ia - L + h - h // 2] * np.sin(u * np.pi / 2),
                        y[ia - L + h - h // 2:]])
    joins.append(round(at, 3))
    n = int(round(v["nbars"] * BAR * SR))
    y = y[:n] if len(y) >= n else np.concatenate([y, np.zeros((n - len(y), 2))])
    f = int(0.01 * SR); y[:f] *= fade(f, "in")
    fo = int(0.45 * SR); y[-fo:] *= fade(fo, "out")
    tt = np.arange(len(y)) / SR; g = np.zeros(len(y))
    for t0, t1, db, r_in, r_out in v.get("duck", []):
        a = np.clip((tt - t0) / r_in, 0, 1) * np.clip((t1 - tt) / r_out, 0, 1)
        g = np.minimum(g, db * a)
    y = y * (10 ** (g / 20))[:, None]
    return y, joins, table

def tick(freq, dur, amp):
    t = np.arange(int(dur * SR)) / SR
    return (amp * np.sin(2 * np.pi * freq * t) * np.exp(-t / (dur / 4)))[:, None] * np.ones((1, 2))

def glock_note(freq, amp):
    """鉄琴の仮の音（合成。本番は効果音の素材か同じ合成を 31_make_se.py に）。部分音 1・2.76・5.40 倍。"""
    t = np.arange(int(2.0 * SR)) / SR
    z = (np.sin(2 * np.pi * freq * t) * np.exp(-t / 0.9) + 0.30 * np.sin(2 * np.pi * freq * 2.756 * t) * np.exp(-t / 0.25)
         + 0.10 * np.sin(2 * np.pi * freq * 5.404 * t) * np.exp(-t / 0.08))
    z *= np.clip(t / 0.002, 0, 1) * amp
    return z[:, None] * np.ones((1, 2))

def add(buf, t0, z):
    i = int(round(t0 * SR)); j = min(i + len(z), len(buf))
    if 0 <= i < len(buf): buf[i:j] += z[:j - i]

def bed(n):
    if not S_SRC or not S_SRC.exists(): return np.zeros((n, 2))
    with tempfile.TemporaryDirectory() as td:
        w = pathlib.Path(td) / "s.wav"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", "44", "-t", "38", "-i", str(S_SRC), "-vn", "-ar", str(SR), "-ac", "2",
                        "-af", "highpass=f=80,lowpass=f=8000", str(w)], check=True)
        b, _ = sf.read(w)
    reps = int(np.ceil(n / len(b))); return np.concatenate([b] * reps)[:n]

def write_mp3(y, path):
    with tempfile.TemporaryDirectory() as td:
        w = pathlib.Path(td) / "o.wav"; sf.write(w, y, SR)
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(w), "-b:a", "192k", str(path)], check=True)

NAMES = {C6: "C6", D6: "D6", E6: "E6", G6: "G6", A6: "A6"}
md = ["# 曲の案 V6a〜V6f の聞き比べ（編集計画 v6 §2。正本は 32小節の V6d、比べる版 V6e・V6f。V6a〜c は 28小節の別案）", "",
      "作り方：`python3 scripts/52_bgm_v6_tests.py /mnt/project-files/dova/ /mnt/project-files/level/audio_tests_v6/ source/S_sueru.mp4`", "",
      "- `<案>.mp3`：曲の編集だけ。`<案>_guide.mp3`：＋拍 B の頭に高い「ピッ」、同期点に低い「ポン」2回、鉄琴の仮の音、ごく薄い現場の音（S 44–82 秒）。",
      "- guide では、機械が載る所（5.9–7.7 秒）と止めの小節の現場の音を上げた（声なし・同期音が主役の区間の見本）。",
      "- 音量は聞き比べのため曲の統合ラウドネス −20 LUFS にそろえた（本番は −24 LUFS、ナレの下でさらに −16.5 dB）。",
      f"- 1小節 {BAR:.3f} 秒、1拍 {BEAT:.3f} 秒。曲の調はハ長調（クロマの相関 0.91）。鉄琴は C D E G A だけを使う。", ""]
for v in VARIANTS:
    if ONLY and v["id"] not in ONLY: continue
    y, joins, table = build(v)
    y = y * 10 ** ((-20 - integrated(y)) / 20)
    pk = np.abs(y).max()
    if pk > 0.89: y *= 0.89 / pk
    write_mp3(y, OUT / f"{v['id']}.mp3")
    b = bed(len(y))
    if np.abs(b).max() > 0:
        b *= 10 ** ((-38 - integrated(b)) / 20)
        tt = np.arange(len(b)) / SR; up = np.zeros(len(b))
        for t0, t1, db in v["bedup"]:
            up = np.maximum(up, db * np.clip((tt - t0) / 0.4, 0, 1) * np.clip((t1 - tt) / 0.4, 0, 1))
        b *= (10 ** (up / 20))[:, None]
    gd = y + b
    for name, eb in v["B"].items():
        add(gd, T(eb), tick(1760, 0.09, 0.22))
    for t0, _ in v["sync"]:
        for dt in (0.0, 0.16): add(gd, t0 + dt, tick(440, 0.12, 0.30))
    for t0, fs, amp, _ in v["glock"]:
        for k, f_ in enumerate(fs): add(gd, t0 + 0.03 * k, glock_note(f_, amp))
    pk = np.abs(gd).max()
    if pk > 0.95: gd *= 0.95 / pk
    write_mp3(gd, OUT / f"{v['id']}_guide.mp3")
    md += [f"## {v['title']}（`{v['id']}.mp3`）", "",
           f"- 編集後 {v['nbars']} 小節 = {v['nbars'] * BAR:.2f} 秒。組み方：{' ＋ '.join(str(op) for op in v['plan'])}、最後の和音のばし {v['hold']}",
           f"- つなぎ目・止め・のばしの時刻（秒）：{', '.join(f'{j:.2f}' for j in joins)}",
           f"- 拍 B の頭（ピッ）：{', '.join(f'{n} {T(eb):.2f}' for n, eb in v['B'].items())}",
           "- 同期点（ポン）：" + "、".join(f"{t0:.2f} {w}" for t0, w in v["sync"]),
           "- 鉄琴：" + "、".join(f"{t0:.2f} {'+'.join(NAMES[f_] for f_ in fs)}（{w}）" for t0, fs, _, w in v["glock"]), "",
           "| 編集後の小節 | 時刻 | 中身 |", "|---|---|---|"]
    md += [f"| {eb} | {T(eb):.2f} | {what} |" for eb, what in table]
    md.append("")
    print(v["id"], f"{len(y) / SR:.2f}s joins {joins}")
(OUT / ("bgm_v7_tests.md" if ONLY and all(i.startswith("V7") for i in ONLY) else "bgm_v6_tests.md")).write_text("\n".join(md) + "\n")
