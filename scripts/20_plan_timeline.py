"""尺とタイミングの正本 comp/timeline.json を作る。
入力：audio/vo_temp/vo_timing.json（本ナレ差し替え後は audio/vo_final/vo_timing.json を優先）
ナレの長さが変わっても、このスクリプトを再実行すれば全体（カット・図解のきっかけ・テロップ・効果音）が追従する。
図解に渡すきっかけ（cues）は「その場面の頭からの秒」。
使い方：python3 scripts/20_plan_timeline.py
"""
import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
FPS = 30000 / 1001
vo_final = ROOT / "audio/vo_final/vo_timing.json"
VO_PATH = vo_final if vo_final.exists() else ROOT / "audio/vo_temp/vo_timing.json"
VO = json.loads(VO_PATH.read_text())["lines"]
VO_DIR = "assets/audio/vo"  # comp/ からの相対

def f(t):  # フレームに丸める
    return round(round(t * FPS) / FPS, 4)

def span(start, dur):  # 終わりもフレームに丸めてから長さを出す（隣の要素との1コマのすき間を防ぐ）
    return round(f(start + dur) - f(start), 4)

T = {"fps": "30000/1001", "width": 1920, "height": 1080, "vo_source": str(VO_PATH.relative_to(ROOT)),
     "beats": [], "shots": [], "stills": [], "scenes": [], "telops": [], "vo": [], "se": [], "bgm": {}, "amb": [],
     "intended_freezes": []}

def vo(id_, start):
    d = VO[id_]["dur"]
    T["vo"].append({"id": id_, "src": f"{VO_DIR}/{id_}.wav", "start": f(start), "dur": d, "text": VO[id_]["text"]})
    return start, start + d

def kw(id_, start, word):
    return start + VO[id_]["keywords"][word]

def shot(id_, start, dur, media_start=0.0, purpose=""):
    T["shots"].append({"id": f"{id_}@{f(start)}", "shot": id_, "src": f"assets/video/{id_}.mp4", "start": f(start),
                       "dur": span(start, dur), "media_start": round(media_start, 4), "purpose": purpose})

def still(name, start, dur, purpose=""):
    T["stills"].append({"id": name, "src": f"assets/video/{name}.png", "start": f(start), "dur": span(start, dur), "purpose": purpose})
    T["intended_freezes"].append([f(start), f(start + dur), name])

def scene(id_, start, dur, cues, purpose="", overlay=False, variables=None):
    T["scenes"].append({"id": id_, "comp": f"compositions/{id_}.html", "start": f(start), "dur": span(start, dur),
                        "cues": {k: round(v, 3) for k, v in cues.items()}, "overlay": overlay,
                        "variables": variables or {}, "purpose": purpose})

def telop(id_, text, start, dur, purpose=""):
    n = len(text.replace("\n", ""))
    need = max(1.5, n / 4 + 1.0)
    T["telops"].append({"id": id_, "kind": "keyword", "text": text, "start": f(start), "dur": span(start, dur),
                        "min_dur": round(need, 2), "ok": dur >= need, "purpose": purpose})

def se(kind, t, note=""):
    T["se"].append({"kind": kind, "start": f(t), "note": note})

def beat(id_, start, end, purpose):
    T["beats"].append({"id": id_, "start": f(start), "end": f(end), "dur": round(end - start, 3), "purpose": purpose})

# ---------------- B1 現場へ（BGMなし・環境音だけ） ----------------
b = 0.0
_, n1e = vo("N1", b + 0.6)
shot("S06", b, 3.0, 0.05, "大引き。測量の一行が現場にやってくる")
b1e = max(b + 6.8, n1e + 0.6)
shot("S08", b + 3.0, b1e - (b + 3.0), 0.0, "まだ何もない場所を見渡す2人＝ここから始まる")
beat("B1", b, b1e, "音楽なしで静かに始め、観客を現場に連れていく")
T["amb"].append({"start": 0.0, "end": None, "note": "風・草の環境音。図解区間は下げる（ミックスで指定）"})

# ---------------- B2 タイトル（照準が合う → ピッ → BGM） ----------------
b = b1e
s04_dur = 3.2
shot("S04", b, s04_dur, 0.0, "ローアングルのプリズム。照準モチーフの導入")
b2e = b + 6.4
still("S04_last", b + s04_dur, b2e - (b + s04_dur), "タイトル表示のための意図的な静止（固定カメラ）")
lock = b + 1.6
scene("title", b, b2e - b, {"reticle_in": 0.3, "lock": lock - b, "title_in": 1.8, "sub_in": 2.0, "out": (b2e - b) - 0.35},
      "章の提示。照準がプリズムに合い『最初の一点』のモチーフを示す", overlay=True,
      variables={"target_x": 820, "target_y": 268})
se("lock", lock, "照準が合う電子音")
T["bgm"] = {"start": f(lock), "note": "照準が合う拍からBGM開始"}
beat("B2", b, b2e, "章の提示とモチーフの導入")

# ---------------- B3 正確な位置 ----------------
b = b2e
s, n2e = vo("N2", b + 0.4)
k = kw("N2", s, "正確な位置")
b3e = max(n2e + 0.6, k + 2.6)
shot("S01", b, b3e - b, 0.3, "TSとプリズムの関係が1画面で見える唯一のカット")
telop("kw_ichi", "正確な位置", k, b3e - 0.3 - k, "キーワードを耳と目で同時に")
beat("B3", b, b3e, "『位置』がすべての出発点だと示す")

# ---------------- B4 基準点＝目印（用語の事前学習） ----------------
b = b3e
s, n3e = vo("N3", b + 0.3)
k_mark = kw("N3", s, "目印")
shot("S03", b, k_mark - b, 3.0, "プリズムを据える手元＝目印の上に機械を立てる")
d0s = k_mark
d0e = max(n3e + 1.0, d0s + 5.6)
scene("d0_marker", d0s, d0e - d0s, {"marker_in": 0.0, "tripod_in": 0.9, "term_in": kw("N3", s, "基準点測量") - d0s,
                                    "out": (d0e - d0s) - 0.3},
      "物語の主役『基準点の標識』を一度見せ、用語を仕組みの前に紹介する")
beat("B4", b, d0e, "用語『基準点』を、実物の形と一緒に覚えてもらう")

# ---------------- B5 実写→図解 D1（何をはかるか） ----------------
b = d0e
s09_live = 1.2
freeze_media = 3.7  # S09 のこの時刻のフレームで静止（02_intermediates.py の S09_freeze と一致）
shot("S09", b, s09_live, freeze_media - s09_live, "肩越しのTSと奥のプリズム。はかる瞬間")
d1s = b + s09_live
s, n4e = vo("N4", d1s + 0.2)
d1e = n4e + 1.0
scene("d1_observe", d1s, d1e - d1s, {
    "desat": 0.0, "ts_label": kw("N4", s, "トータルステーション") - d1s, "prism_label": kw("N4", s, "プリズム") - d1s,
    "angle": kw("N4", s, "角度") - d1s, "distance": kw("N4", s, "距離") - d1s, "to_paper": (d1e - d1s) - 0.7},
    "実写から図解へ橋渡し。何をはかるかを対象のそばで見せる",
    variables={"ts_x": 613, "ts_y": 572, "prism_x": 1446, "prism_y": 137})
T["intended_freezes"].append([f(d1s), f(d1e), "S09_freeze（D1の背景）"])
se("measure", kw("N4", s, "距離"), "測距の短い電子音")
beat("B5", b, d1e, "実写の観測から図解への橋渡し")

# ---------------- B6 D2 真上から（しくみの核心） ----------------
b = d1e
s, e = vo("N5a", b + 1.2)
s2, n5e = vo("N5b", e + 0.5)
d2e = n5e + 0.9
scene("d2_topview", b, d2e - b, {
    "setup": 0.0, "known": kw("N5a", s, "わかっている点") - b, "angle": kw("N5a", s, "角度") - b,
    "distance": kw("N5a", s, "距離") - b, "new_point": kw("N5b", s2, "新しい点") - b,
    "fix": kw("N5b", s2, "決まります") - b}, "観測から位置が決まる因果を『動き』で理解させる")
se("click", kw("N5b", s2, "決まります"), "新しい点が決まる小さなクリック")
beat("B6", b, d2e, "角度→距離→位置が決まる、の3拍")

# ---------------- B7 D3 はかりつなぐ・確かめる → S07 ----------------
b = d2e
s, n6e = vo("N6", b + 0.4)
k_check = kw("N6", s, "確かめます")
d3e = max(n6e + 0.6, k_check + 0.3 + 2.5)  # 「新しい基準点」（6字）を 2.5秒見せる
scene("d3_traverse", b, d3e - b, {
    "chain": kw("N6", s, "はかりつなぎ") - b, "last": kw("N6", s, "最後に") - b,
    "check": kw("N6", s, "確かめます") - b}, "正確さに責任を持つ仕事だと伝える")
se("click", kw("N6", s, "確かめます"), "確認の✓")
shot("S07", d3e, 2.2, 0.0, "記録する2人＝人が責任を持って確かめている")
b7e = d3e + 2.2
beat("B7", b, b7e, "はかりつなぎと確認。最後は人の顔に戻す")

# ---------------- B8 D4 基準点から道路と橋へ（観客の発見） ----------------
b = b7e
s, n7ae = vo("N7a", b + 1.9)
gap = 1.0
s2, n7be = vo("N7b", n7ae + gap)
join = s2 + 1.0
d4e = n7be + 0.7
scene("d4_bridge", b, d4e - b, {
    "network": 0.0, "road": 0.9, "banks": kw("N7a", s, "両岸") - b, "middle": kw("N7a", s, "真ん中") - b,
    "pause": n7ae - b, "same_point": kw("N7b", s2, "同じ基準点") - b, "join": join - b},
    "答えを先に言わず、観客自身に生活とのつながりを気づかせる")
se("join", join, "橋がつながる低めのカチッ")
T["bgm"]["pause"] = {"start": f(n7ae - 0.1), "end": f(s2), "note": "答えの前の『間』。BGMを抜く"}
beat("B8", b, d4e, "観客自身の発見（同じ基準点だから、つながる）")

# ---------------- B9 D5 図から日常へ ----------------
b = d4e
s, n8e = vo("N8", b + 0.5)
d5e = n8e + 0.7
scene("d5_everyday", b, d5e - b, {"life_in": 0.0, "road_glow": kw("N8", s, "毎日通る道") - b},
      "日常の風景に着地する")
beat("B9", b, d5e, "毎日の道につながる")

# ---------------- B10 締め ----------------
b = d5e
s, n9ae = vo("N9a", b + 0.4)
shot("S02", b, 3.1, 0.0, "指差して指示する2人＝チームで最初の一点をつくる")
shot("S10", b + 3.1, 2.6, 0.0, "現場を見渡す背中＝誇りと余韻（冒頭と対）")
s2, n9be = vo("N9b", max(n9ae + 0.6, b + 4.3))
endc = b + 5.7
text_in = n9be + 0.3          # 締めの一文は N9b を言い終えてから（耳と目の言葉をずらさない）
fade = text_in + 3.2          # 12字 → 表示 4.0秒（フェード込み）
end = fade + 0.8
scene("endcard", endc, end - endc, {"reticle": 0.0, "point": 0.6, "text_in": text_in - endc, "fade": fade - endc},
      "締めの一文。照準が一点に戻り、冒頭と閉じる")
T["bgm"]["end"] = f(end)
beat("B10", b, end, "誇りと余韻")

T["duration"] = f(end)
T["speech_ratio"] = round(sum(v["dur"] for v in T["vo"]) / end, 3)
(ROOT / "comp/timeline.json").write_text(json.dumps(T, ensure_ascii=False, indent=1))
print(f"duration {T['duration']}s  speech ratio {T['speech_ratio']}")
for bt in T["beats"]:
    print(f"  {bt['id']:4} {bt['start']:6.2f}–{bt['end']:6.2f} ({bt['dur']:.1f}s) {bt['purpose']}")
for t in T["telops"]:
    print("  telop", t["text"], t["dur"], "≥", t["min_dur"], "OK" if t["ok"] else "NG")
