"""尺とタイミングの正本 comp/timeline.json を作る（構成A「はじまりの点」、編集プラン docs/11 §3）。
小節の格子で作る：曲（New Departure、94.9 BPM）の小節を時間のものさしにし、場面の変わり目は小節の頭、
場面の中のカットは拍の頭に置く（どちらも 1 コマ前＝目が先に変化を感じる分）。尺は 24 小節で固定。
ナレは格子の上に置く（ナレの長さから尺を決めない）。本ナレに差し替えたら、置き場所を拍単位で直す。
入力：audio/vo_temp/vo_timing.json（本ナレ差し替え後は audio/vo_final/vo_timing.json を優先）
使い方：python3 scripts/20_plan_timeline.py
"""
import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
FPS = 30000 / 1001
vo_final = ROOT / "audio/vo_final/vo_timing.json"
VO_PATH = vo_final if vo_final.exists() else ROOT / "audio/vo_temp/vo_timing.json"
VO = json.loads(VO_PATH.read_text())["lines"]
VO_DIR = "assets/audio/vo"  # comp/ からの相対
META = json.loads((ROOT / "intermediate/B/meta.json").read_text())  # 各カットの中間素材の頭＝元動画の何秒か

BEAT = 0.63199            # 拍（秒）。曲の拍検出を直線で近似（analysis/plan/bgm_01_new_departure.md）
BAR = 4 * BEAT
BARS = 24
DUR = BARS * BAR

def f(t):  # フレームに丸める
    return round(round(t * FPS) / FPS, 4)

def span(start, dur):  # 終わりもフレームに丸めてから長さを出す（隣の要素との1コマのすき間を防ぐ）
    return round(f(start + dur) - f(start), 4)

def at(bar, beat=1):      # 小節・拍 → 秒（小節・拍は 1 始まり）
    return (bar - 1) * BAR + (beat - 1) * BEAT

def cut(bar, beat=1):     # 映像の切り替えは拍の 1 コマ前
    t = at(bar, beat)
    return 0.0 if t == 0 else t - 1 / FPS

T = {"fps": "30000/1001", "width": 1920, "height": 1080, "vo_source": str(VO_PATH.relative_to(ROOT)),
     "grid": {"beat": BEAT, "bar": BAR, "bars": BARS, "cut_offset_frames": 1},
     "beats": [], "shots": [], "stills": [], "scenes": [], "telops": [], "vo": [], "se": [], "bgm": {}, "amb": [],
     "moves": [], "cuts": [], "intended_freezes": []}

def vo(id_, start):
    d = VO[id_]["dur"]
    T["vo"].append({"id": id_, "src": f"{VO_DIR}/{id_}.wav", "start": f(start), "dur": d, "text": VO[id_]["text"]})
    return start, start + d

def kw(id_, start, word):
    return start + VO[id_]["keywords"][word]

def shot(id_, start, end, src_time, purpose=""):
    """src_time：このカットの頭に来る元動画の時刻（編集プラン §3 の「元の範囲」）。"""
    ms = max(0.0, src_time - META[id_]["src_in"])
    room = META[id_]["dur"] - ms
    assert end - start <= room + 0.02, f"{id_}: {end - start:.2f}s > {room:.2f}s available"
    T["shots"].append({"id": f"{id_}@{f(start)}", "shot": id_, "src": f"assets/video/{id_}.mp4", "start": f(start),
                       "dur": span(start, end - start), "media_start": round(ms, 4), "purpose": purpose})
    T["cuts"].append(f(start))

def still(name, start, end, purpose=""):
    T["stills"].append({"id": name, "src": f"assets/video/{name}.png", "start": f(start), "dur": span(start, end - start), "purpose": purpose})
    T["intended_freezes"].append([f(start), f(end), name])

def scene(id_, start, end, cues, purpose="", overlay=False, variables=None, template=None, diagram=True, cut_point=True):
    T["scenes"].append({"id": id_, "comp": f"compositions/{'gen/' if template else ''}{id_}.html", "template": template,
                        "start": f(start), "dur": span(start, end - start),
                        "cues": {k: round(v - start, 3) for k, v in cues.items()}, "overlay": overlay, "diagram": diagram,
                        "variables": variables or {}, "purpose": purpose})
    if cut_point: T["cuts"].append(f(start))

def move(target, start, end, scale0, scale1, origin, purpose):
    T["moves"].append({"target": target, "start": f(start), "dur": round(end - start, 4), "scale": [scale0, scale1],
                       "origin": origin, "purpose": purpose})

def se(kind, t, note="", gain_db=0.0):
    T["se"].append({"kind": kind, "start": f(t), "note": note, "gain_db": gain_db})

def beat(id_, start, end, purpose):
    T["beats"].append({"id": id_, "start": f(start), "end": f(end), "dur": round(end - start, 3), "purpose": purpose})

DOOR_ICON = (340, 470)          # 章扉の基準点アイコンの中心（chapter_door.html と同じ）
PRISM = (820, 268)              # S04 のプリズム（タイトルの照準の行き先）

# ---------------- B1 章扉 → タイトル（1〜3小節） ----------------
scene("chapter_door", 0, cut(2), {"icons_in": at(1, 2), "lit": at(1, 3), "morph": at(1, 4)},
      "部門の中の1作業だと、言葉でなく形で示す（全パート共通）", variables={"active": 0})
se("glow", at(1, 3), "章扉で基準点のアイコンが灯る")
s04_live = META["S04"]["dur"] - 0.05
shot("S04", cut(2), cut(2) + s04_live, 14.65, "ローアングルのプリズム。照準モチーフ")
still("S04_last", cut(2) + s04_live, cut(4), "タイトルのための静止（固定カメラ）。ゆっくり寄る")
move("still_S04_last", cut(2) + s04_live, cut(4), 1.0, 1.0 + 0.02 * (cut(4) - cut(2) - s04_live),
     f"{PRISM[0] / 19.2:.2f}% {PRISM[1] / 10.8:.2f}%", "静止を感じさせず、照準へ視線を集める（毎秒2%）")
lock = at(2, 3)
s, _ = vo("N1", lock - VO["N1"]["keywords"]["基準点測量"])
scene("title", cut(2), cut(4), {"reticle_in": cut(2) + 0.05, "lock": lock, "title_in": lock + 0.2, "out": cut(4) - 0.3},
      "章の提示。照準がプリズムに合う", overlay=True, diagram=False, cut_point=False,
      variables={"target_x": PRISM[0], "target_y": PRISM[1], "from_x": DOOR_ICON[0], "from_y": DOOR_ICON[1]})
se("lock", lock, "照準が合う電子音（シリーズ共通の合図）")
beat("B1", 0, at(4), "章扉→タイトル")

# ---------------- B2 現場へ（4〜6小節） ----------------
shot("S06", cut(4), cut(5), 20.45, "農道を歩く一行。人と現場の空気")
shot("S01", cut(5), cut(7), 0.30, "TSを据える2人。道具と仕事の全体像")
vo("N2", at(4) + 0.4)
beat("B2", at(4), at(7), "人と現場。目印が要る理由")

# ---------------- B3 基準点とは（7〜8小節） ----------------
shot("S03", cut(7), cut(7, 4), 12.00, "プリズムを据える＝目印の上に立てる")
s, _ = vo("N3", at(8) + 0.3 - VO["N3"]["keywords"]["基準点"])   # 「基準点」を 8 小節（曲の息つぎ）に
scene("d0_marker", cut(7, 4), cut(9), {"marker_in": cut(7, 4), "tripod_in": cut(7, 4) + 0.35, "term_in": kw("N3", s, "基準点"),
                                       "out": cut(9) - 0.05}, "用語「基準点」を、地面のしるしの形と一緒に")
beat("B3", at(7), at(9), "基準点とは")

# ---------------- B4 はかる（9〜11小節） ----------------
shot("S09", cut(9), cut(10, 3), 30.70, "肩越しのTS。パンとピント送りで機械の視点に入る")
d1s, d1e = cut(10, 3), cut(12)
# 9 小節頭の強い一打の後を開け、「角度」が D1 のラベルの後（D1 の頭 +1.0 秒）に来るように置く
s, n4e = vo("N4", max(at(9) + 0.55, d1s + 1.0 - VO["N4"]["keywords"]["角度"]))
scene("d1_observe", d1s, d1e, {"desat": d1s, "ts_label": d1s + 0.1, "prism_label": d1s + 0.5,
                                "angle": kw("N4", s, "角度"), "distance": kw("N4", s, "距離"), "to_paper": d1e - 1.0},
      "何をどの道具ではかるか（ラベルと光の線）。最後に写真が倒れて真上の図へ",
      variables={"ts_x": 613, "ts_y": 572, "prism_x": 1446, "prism_y": 137})
T["intended_freezes"].append([f(d1s), f(d1e), "S09_freeze（D1の背景）"])
se("measure", kw("N4", s, "距離"), "測距の短い電子音")
beat("B4", at(9), at(12), "はかる")

# ---------------- B5 しくみ（12〜14小節） ----------------
s, e = vo("N5a", at(13) - VO["N5a"]["keywords"]["距離"])   # 「距離」を 13 小節頭（曲のつなぎ目）に
s2, _ = vo("N5b", e + 0.26)
d2s, d2e = cut(12), cut(15)
scene("d2_topview", d2s, d2e, {"setup": d2s, "known": max(d2s + 0.3, kw("N5a", s, "わかっている点")), "angle": kw("N5a", s, "角度"),
                               "distance": kw("N5a", s, "距離"), "new_point": kw("N5b", s2, "新しい点"),
                               "fix": kw("N5b", s2, "決まります")}, "しくみの核心。角度→距離→新しい点の3段")
se("click", kw("N5b", s2, "決まります"), "新しい点が決まる")
beat("B5", at(12), at(15), "しくみ")

# ---------------- B6 確かめる人（15〜17小節） ----------------
shot("S05", cut(15), cut(15, 4), 18.00, "TSをのぞく人。図解から人に戻る")
shot("S07", cut(15, 4), cut(16, 4), 23.80, "記録する2人の表情")
map_s = at(18) - 1.3
shot("S08", cut(16, 4), cut(18), 26.90, "土地を見渡す背中。草原が地図に変わるつなぎの起点")
vo("N6", at(15) + 0.45)
beat("B6", at(15), at(18), "確かめる人")

# ---------------- B7 ほかの測量へ（18〜20小節） ----------------
s, _ = vo("N7a", at(18) + 0.35)
s2, _ = vo("N7b", at(19) + 0.1)
scene("map_link", map_s, cut(21), {"dissolve": map_s, "points": at(18) - 0.1, "contours": kw("N7b", s2, "地図"),
                                    "road": kw("N7b", s2, "道路の図面"), "icons": at(20), "links": at(20) + 0.8,
                                    "out": cut(21) - 0.05},
      "部門の中での役割＝ほかの測量の土台（点をたよりに地図と道路の図面ができる）", overlay=True, cut_point=False,
      variables={"active": 0})
T["cuts"].append(f(cut(18)))
se("click", at(20) + 0.8 + 0.35, "アイコンが灯る（小さめ）", gain_db=-6.0)
beat("B7", at(18), at(21), "ほかの測量へ")

# ---------------- B8 締め（21〜24小節） ----------------
# S02 は元の長さが 5 拍に 2 コマ足りない。曲の最後の一打（21 小節頭）は動かさず、S10 を 2 コマ早く入れる
s02_room = META["S02"]["dur"] - 0.005
shot("S02", cut(21), min(cut(22, 2), cut(21) + s02_room), 5.70, "前を指差す2人＝次へ向かう人。曲の最後の一打で切り替え")
s10s = min(cut(22, 2), cut(21) + s02_room); s10e = s10s + META["S10"]["dur"] - 0.05
shot("S10", s10s, s10e, 36.70, "現場を見渡す背中＝誇りと余韻")
push0, push_rate = 1.0, 0.015
push1 = push0 + push_rate * (s10e - s10s)
move("v_S10", s10s, s10e, push0, push1, "50% 40%", "見渡す先へ気持ちを運ぶ（毎秒1.5%）")
s, n8e = vo("N8", at(21) + 0.9)   # 「はじまりの点」を締めの文字が出る瞬間に合わせる（独立レビュー v4.5）
end = DUR
scene("endcard", s10s, end, {"text_in": s10s + 0.15, "bg_in": s10e, "reticle": at(23, 3), "door": at(23, 3) + 1.45,
                             "fade": end - 0.5},
      "締めの一文。照準が縮んで章扉の基準点アイコンに戻る（章扉と同じ形で閉じる）", overlay=True, diagram=False, cut_point=False,
      variables={"push_from": round(push1, 4), "push_rate": push_rate, "icon_x": DOOR_ICON[0], "icon_y": DOOR_ICON[1],
                 "active": 0})
T["intended_freezes"].append([f(s10e), f(end), "endcard（S10 最後のコマに寄り続ける）"])
se("lock", at(23, 3) + 1.45, "照準が章扉のアイコンに戻る（小さめ）", gain_db=-6.0)
beat("B8", at(21), end, "締め")

T["bgm"] = {"start": 0.0, "end": f(end), "pause": None, "bars": "1-12,25-36",
            "note": "曲の小節1の頭＝映像の0秒。1〜12＋25〜36小節（つなぎ目は 13 小節頭）"}
T["amb"].append({"start": 0.0, "end": None, "note": "風・草の環境音。図解区間は下げる（ミックスで指定）"})
T["duration"] = f(end)
T["speech_ratio"] = round(sum(v["dur"] for v in T["vo"]) / end, 3)

# ナレどうしが重ならないこと
vs = sorted(T["vo"], key=lambda v: v["start"])
for a, b in zip(vs, vs[1:]):
    assert a["start"] + a["dur"] <= b["start"] + 0.01, f"VO overlap {a['id']} / {b['id']}"
assert vs[-1]["start"] + vs[-1]["dur"] <= end - 1.5, "N8 が終わりに近すぎる"

(ROOT / "comp/timeline.json").write_text(json.dumps(T, ensure_ascii=False, indent=1))
print(f"duration {T['duration']}s  speech ratio {T['speech_ratio']}")
for bt in T["beats"]:
    print(f"  {bt['id']:4} {bt['start']:6.2f}–{bt['end']:6.2f} ({bt['dur']:.1f}s) {bt['purpose']}")
for v in T["vo"]:
    print(f"  {v['id']:4} {v['start']:6.2f}–{v['start'] + v['dur']:6.2f}")
