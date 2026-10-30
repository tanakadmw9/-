"""尺とタイミングの正本 comp/timeline.json を作る（水準測量パート v8.6「海からの高さ」、plan/editing_v8.md §1〜§3）。
28 小節の格子（曲 New Departure、V6b の組み方：1〜7＋8小節の止め＋9〜16＋25〜36、最後の和音を 3 秒のばす）＝70.783 秒。
場面の変わり目は小節の頭、カットは拍の頭（どちらも 1 コマ前）。秒の正本は editing_v8.md §1.2・§1.4（同期点）。
ナレは「合わせる言葉」の頭が同期点に来るように置く（言葉の頭は audio/vo_temp/vo_timing.json。本ナレは audio/vo_final/）。
入力：audio/vo_temp/vo_timing.json、intermediate/<grade>/meta.json（02_intermediates.py）、comp/site_track.json（36_track_site.py）
使い方：python3 scripts/20_plan_timeline.py
"""
import json, pathlib, os

ROOT = pathlib.Path(__file__).resolve().parent.parent
FPS = 30000 / 1001
vo_final = ROOT / "audio/vo_final/vo_timing.json"
VO_PATH = vo_final if vo_final.exists() else ROOT / "audio/vo_temp/vo_timing.json"
VO = json.loads(VO_PATH.read_text())["lines"]
VO_DIR = "assets/audio/vo"
GRADE = os.environ.get("GRADE", "Bplus")
META = json.loads((ROOT / f"intermediate/{GRADE}/meta.json").read_text())
TRACK = json.loads((ROOT / "comp/site_track.json").read_text())

BEAT = 0.63199
BAR = 4 * BEAT
BARS = 28
DUR = round(BARS * BAR, 3)          # 70.783

def f(t): return round(round(t * FPS) / FPS, 4)
def span(start, dur): return round(f(start + dur) - f(start), 4)
def at(bar, beat=1): return (bar - 1) * BAR + (beat - 1) * BEAT
def cut(bar, beat=1):
    t = at(bar, beat); return 0.0 if t == 0 else t - 1 / FPS
FR = 1 / FPS

T = {"fps": "30000/1001", "width": 1920, "height": 1080, "vo_source": str(VO_PATH.relative_to(ROOT)), "version_plan": "editing_v8.md v8.6",
     "grid": {"beat": BEAT, "bar": BAR, "bars": BARS, "cut_offset_frames": 1},
     "beats": [], "shots": [], "stills": [], "scenes": [], "telops": [], "vo": [], "se": [], "bgm": {}, "amb": [],
     "moves": [], "cuts": [], "intended_freezes": [], "sync": []}
T["grade"] = GRADE

def vo(id_, start, purpose):
    d = VO[id_]["dur"]
    T["vo"].append({"id": id_, "src": f"{VO_DIR}/{id_}.wav", "start": f(start), "dur": d, "text": VO[id_]["text"], "purpose": purpose})
    return start, start + d

def vo_at(id_, word, t, purpose):
    """言葉 word の頭が t に来るように置く。"""
    return vo(id_, t - VO[id_]["keywords"][word], purpose)

def kw(id_, word):
    v = next(x for x in T["vo"] if x["id"] == id_)
    return v["start"] + VO[id_]["keywords"][word]

def shot(id_, start, end, src_time, purpose):
    m = META[id_]; ms = max(0.0, src_time - m["src_in"]) / m.get("speed", 1.0)
    room = m["dur"] - ms
    assert end - start <= room + 0.02, f"{id_}: {end - start:.2f}s > {room:.2f}s available"
    T["shots"].append({"id": f"{id_}@{f(start)}", "shot": id_, "src": f"assets/video/{id_}.mp4", "start": f(start),
                       "dur": span(start, end - start), "media_start": round(ms, 4), "purpose": purpose})
    T["cuts"].append(f(start))

def still(name, start, end, purpose):
    T["stills"].append({"id": name, "src": f"assets/video/{name}.png", "start": f(start), "dur": span(start, end - start), "purpose": purpose})
    T["intended_freezes"].append([f(start), f(end), name])

def scene(id_, start, end, cues, purpose, overlay=False, variables=None, template=None, diagram=True, cut_point=True):
    T["scenes"].append({"id": id_, "comp": f"compositions/{'gen/' if template else ''}{id_}.html", "template": template,
                        "start": f(start), "dur": span(start, end - start),
                        "cues": {k: round(v - f(start), 3) for k, v in cues.items()}, "overlay": overlay, "diagram": diagram,
                        "variables": variables or {}, "purpose": purpose})
    if cut_point: T["cuts"].append(f(start))

def move(target, start, end, scale0, scale1, origin, purpose, ease="none"):
    T["moves"].append({"target": target, "start": f(start), "dur": round(end - start, 4), "scale": [scale0, scale1],
                       "origin": origin, "ease": ease, "purpose": purpose})

def se(kind, t, note, gain_db=0.0):
    T["se"].append({"kind": kind, "start": f(t), "note": note, "gain_db": gain_db})

def beat(id_, start, end, purpose):
    T["beats"].append({"id": id_, "start": f(start), "end": f(end), "dur": round(end - start, 3), "purpose": purpose})

def sync(t, what):
    T["sync"].append([round(t, 3), what])

ICON = (650, 470)        # 章扉の水準測量のアイコンの中心（chapter_door.html の XS[1], ICON_Y）

# ================= B1 章扉（1小節） =================
scene("chapter_door", 0, cut(2), {"icons_in": at(1, 2), "lit": at(1, 3)},
      "部門の中の1作業だと、形で示す（全パート共通）。灯るのは水準測量。照準には変えない（このパートの終わりの □ がここへ戻る）",
      variables={"active": 1})
se("glow", at(1, 3), "章扉で水準測量のアイコンが灯る")
vo("N1a", 0.30, "部門の中の1作業だと声で言う")
beat("B1", 0, at(2), "章扉：部門の中の1作業")

# ================= B2 据える（2〜3小節） =================
shot("B2_S", cut(2), cut(4), 48.58, "人の手で始まる：ケースを開け、持ち上げ、三脚に載せる（S 53.0 で載る）")
LAND = 6.952
scene("title_lv", LAND, 11.40, {"title_in": LAND, "sub_in": 7.15, "title_out": 9.75, "out": 11.40 - 0.3},
      "題「水準測量」を機械が載る拍で、サブ「“高さの土台” をはかる」（運ぶもの）。B3 の寄りの顔にかけないよう左上", overlay=True, diagram=False, cut_point=False,
      variables={"pos": "top"})
vo("N1b", 7.24, "題と同じ拍で、作業の名前を言う")
sync(LAND, "機械が載る＝題")
beat("B2", at(2), at(4), "据える：人の手で始まる")

# ================= B3 はかる（4〜5小節） =================
shot("B3_N", cut(4), cut(6), 2.0, "接眼に目を当て、つまみを回す（N、1.45 倍）＝何をしている人か")
_, e2 = vo("N2", 9.03, "道ばたで、高さを、ミリまではかる仕事だと言う")
assert e2 <= at(6) + 0.01, f"N2 が B3 をこえる（{e2:.2f}）"
beat("B3", at(4), at(6), "はかる：何をしている人か")

# ================= B4 問い（6〜8小節） =================
shot("B4_S", cut(6), cut(8, 3), 172.2, "標尺手が遠くの点まで歩いて立つ。機械のそばに観測者（SF）。問いを置く画")
still("S178_5", cut(8, 3), cut(9), "S 178.5 で止める（問いのあと、曲が止まって現場の音だけ。考える間）")
_, e3 = vo("N3", 13.38, "問い「高さって、どこからはかるのでしょう」")
assert e3 <= 17.696 - 0.2, f"N3 が曲の止めに近い（{e3:.2f}）"
STAFF0 = (902, 452)                                # 遠くの標尺のてっぺん（S 全画面を 1920 にした画素。S 175.5 から点に立つ）
scene("label_staff", 16.00, 18.40, {"in": 16.00, "out": 18.40 - 0.3},
      "道具の名前「標尺」（遠くの点に立つ人の持つものさし）。線は空だけを通す", overlay=True, diagram=False, cut_point=False,
      template="label_pointer", variables={"text": "標尺", "box_dx": -300, "box_dy": -250, "keys": json.dumps([[0, *STAFF0]])})
sync(17.696, "問いを言い終わる → 曲が止まる")
beat("B4", at(6), at(9), "問い：高さって、どこからはかる？")

# ================= B5 ひとつの基準（9〜14小節） =================
SITE = at(12, 2)                                   # v4.2：現場の実写を拍の頭（12小節2拍 28.44）に。N5 は現場の画の上で始める
GL = 0.22                                          # 鉄琴は言葉の直前の間に（言葉と重ねない：独立レビュー v4.1）。図もいっしょに出す
_, e4 = vo_at("N4", "ゼロ", 25.12, "日本の高さの基準：東京湾の海の高さを0にしてはかる【要監修】")
assert next(v for v in T["vo"] if v["id"] == "N4")["start"] >= 21.45, "N4 は 21.49 より早くしない（editing §1.3）"
s5 = vo("N5", SITE + 0.11, "道路を設計するときも、まず、ひとつの基準を決める（芯）。現場の画の上で始める")[0]
assert s5 >= SITE and s5 - e4 >= 0.38, f"N5 の置き場所（{s5:.2f}）"
LINE0 = kw("N4", "ゼロ") - GL
BARS0 = kw("N4", "はかります")
WHITE2 = SITE - 0.32
scene("b5_sea", cut(9), SITE - FR,
      {"shrink": at(9), "white": 21.18, "japan": 21.488, "japan_end": 22.4, "supp": kw("N4", "東京湾") - 0.30, "dot": kw("N4", "東京湾"),
       "slide": 24.1, "line": LINE0, "objs": LINE0 + 0.33, "bars": BARS0, "white2": WHITE2},
      "なるほど①：写真が縮み、白い紙、日本の形と東京湾の点 → 0 の線から山・建物・家へ3本の棒（背くらべ）。0 は海にだけ使う",
      variables={"photo": "assets/video/S178_5.png"})
T["intended_freezes"].append([f(WHITE2), f(SITE), "b5_sea：白い紙 0.32 秒（海と現場を線・寄りでつながない）"])
se("glock_c6", LINE0, "0 の線（「ゼロ」の直前の間）")
sync(LINE0, "0 の線＋C6（「ゼロ」の 0.22 秒前）"); sync(BARS0, "「はかります」で 0 の線から3本の棒")

B6C = cut(15, 3)
shot("B5_K", SITE - FR, B6C, 16.52, "現場：遠くの標尺手が点に立つ（K-left）。□・線・棒の下地")
SQ = kw("N5", "ひとつ") - GL
LINE1 = kw("N5", "基準")
BARS1 = kw("N5", "決めます")
s6 = vo("N6", s5 + VO["N5"]["dur"] + 0.40, "近くの“高さの目印”から高さをつなぐ【要監修】")[0]
LAB = kw("N6", "高さの目印") - 0.45
assert B6C - LAB >= 2.35, f"ラベルの表示が短い（{B6C - LAB:.2f}）"
assert B6C - (BARS1 + 0.7) >= 2.0, f"棒がそろって見える時間が 2 秒ない（{B6C - BARS1 - 0.7:.2f}）"
scene("b5_site", SITE - FR, B6C,
      {"sq": SQ, "dark": SQ, "line": LINE1, "bars": BARS1, "label": LAB},
      "なるほど②：現場でも、まずひとつの基準（近くの目印）。□・一本の実線・3本の棒と点（0 の絵と同じ形、0 の字は出さない）→ 紺の札「高さの目印」を □ の横に",
      overlay=True, diagram=False, cut_point=False, variables={"track": json.dumps([[0, 0, 0]])})
se("glock_c6", SQ, "現場の □（「ひとつ」の直前の間。0 の線と同じ音）")
sync(SQ, "「ひとつ」の直前で □＋C6＋写真が暗く"); sync(LINE1, "「基準」で実線"); sync(BARS1, "「決めます」で3本の棒（そろって 2 秒以上）")
sync(LAB, "紺の札「高さの目印」（声の 0.45 秒前）")
beat("B5", at(9), at(15), "ひとつの基準：日本は海の0、現場はまず近くの目印")

# ================= B6 つなぐ（15小節） =================
shot("B6_S", B6C, cut(16), 169.09, "ものさしを持った人が機械の横を通って次の点へ（SF）＝目印から高さをつなぐ")
sync(kw("N6", "つないで"), "「つないで」で次の点へ歩く")
beat("B6", at(15), at(16), "つなぐ")

# ================= B7 読む（16〜17小節） =================
shot("B7_N", cut(16), cut(17), 7.10, "目とつまみ（N、2.0 倍）＝目で読む仕事")
scene("label_level", 37.95, 40.30, {"in": 37.95, "out": 40.30 - 0.3},
      "道具の名前「レベル」（のぞいている機械に引き出し線。顔にかけない）", overlay=True, diagram=False, cut_point=False,
      template="label_pointer", variables={"text": "レベル", "box_dx": 320, "box_dy": -380, "keys": json.dumps([[0, 880, 600]])})
vo_at("N7", "読んで", 41.711, "遠くのものさしを目で読む")
BAND = at(17, 3)
scene("eyepiece", cut(17), cut(18), {"in": at(17), "stop": 41.0, "focus": 41.5, "band": BAND},
      "望遠鏡の中：標尺が横から来て縦の線で止まり、ピントが合い、「読んで」で横の線のところにうすい帯（数字は描かない）")
sync(BAND, "「読んで」で横の線の帯（音なし）")
beat("B7", at(16), at(18), "読む")

# ================= B8 書く（18小節） =================
shot("B8_S", cut(18), cut(19), 159.5, "三脚の左で野帳に書く（SE）＝読んだ数字は人の手で残る")
vo("N8", 43.37, "手で書きとめる")
beat("B8", at(18), at(19), "書く")

# ================= B9 確かめる（19〜20小節） =================
shot("B9_K", cut(19), cut(21, 2), 2.80, "歩いて来て、かがんで遠くの標尺をのぞく（K-w、一続き）。B10 の紙が溶けるまで下に続く")
vo("N9", 45.90, "行きと帰りではかって確かめる（ていねいさ）")
beat("B9", at(19), at(21), "行きと帰りで確かめる")

# ================= B10 設計へ（21〜22小節） =================
vo_at("N10", "位置", 52.12, "高さは位置とあわせて道路の設計に使われる【要監修】")
ROAD = kw("N10", "道路") - GL
scene("b10_design", cut(21), cut(23),
      {"paper": at(21), "paper_end": at(21, 2), "pts": at(21, 2), "tri": kw("N10", "位置"), "merge": at(21, 4), "road": ROAD},
      "位置の層（△）と高さの層（棒つきの点）に札を1回ずつ。重なってから、△ の間に道路の点線の下書き（完成の図面・坂には見せない）",
      overlay=True)
se("glock_ceg", ROAD, "道路の下書き（「道路」の直前の間）")
sync(kw("N10", "位置"), "「位置」で △"); sync(at(21, 4), "「あわせて」で重なる"); sync(ROAD, "「道路」の直前で点線の下書き＋C・E・G")
assert next(v for v in T["vo"] if v["id"] == "N10")["start"] + VO["N10"]["dur"] <= at(23) - 0.1, "N10 が B10 をこえる"
beat("B10", at(21), at(23), "設計へ")

# ================= B11 人（23〜24小節） =================
shot("B11_S", cut(23), cut(25), 126.6, "ケースから黄色の野帳を取り、カメラの方へ歩いて来る人（SA、一続き）")
beat("B11", at(23), at(25), "人：声なし")

# ================= B12 締め（25〜28小節） =================
shot("B12_K", cut(25), cut(28), 8.533, "最後の一打で二人の引き＝誇りと余韻（K-w）")
move("v_B12_K", cut(25), cut(28), 1.15, 1.0, "50% 50%", "1.15 倍から全画面へ等速で引く（締めの広がり）")
still("K16_10", cut(28), DUR, "終わりの画の下（紙の下で見えない。書き出しの穴埋め）")
vo("N12", 61.07, "締めの一文")
TXT = kw("N12", "高さの土台") - 0.30
scene("endcard", TXT, DUR,
      {"text_in": TXT, "credit": at(26), "text_out": 70.00, "paper": at(27, 3), "paper_end": at(27, 4), "draw": at(27, 4),
       "shrink": at(28, 3), "icon": at(28, 4), "fade": 70.283},
      "締め：文字「“高さの土台” をはかる」→ 子どもが描く絵（海の絵と現場の絵を左右に離して並べる。線でつながない。2 秒以上）→ オレンジの □ が章扉のアイコンへ",
      overlay=True, diagram=False, cut_point=False, variables={"icon_x": ICON[0], "icon_y": ICON[1]})
se("glock_g6", at(28, 4), "オレンジの □ がアイコンに（小さく）")
T["intended_freezes"].append([f(at(27, 3)), DUR, "endcard（紙の上の絵 → 黒）"])
beat("B12", at(25), DUR, "締め")

# ================= 音 =================
T["bgm"] = {"start": 0.0, "end": DUR, "pause": None,
            "plan": [["bars", 1, 7], ["stop", 1, 8], ["bars", 9, 16], ["bars", 25, 36]],
            "hold": {"at": round(at(25) + 4.44, 3), "len": 3.0, "xfade": 0.4},
            "duck": [[6.00, 7.70, -12.0, 0.4, 0.35]],
            "under": [{"t": 30.0, "db": -19.0}],  # N4〜N6 の区間（30 秒を含む区間）   # v4.1：N4〜N6 のナレ下を −17→−19 dB（N5 の 3 秒窓の差が最小 13.3 dB。曲が盛り上がる所）
            "note": "V6b の組み方（editing_v8.md §2、ガイド V8_28 と同じ）：8小節は和音1拍→減衰→無音（現場の音だけ）。つなぎ目 16→25 は 40.447（接眼の円）"}
T["amb"].append({"start": 0.0, "end": None, "src": "audio/amb/amb_loc.wav",
                 "note": "環境音。実写の下は元の映像の現場音、図解区間は下げる（ミックスで指定）"})

JOB_NAMES = ["基準点測量", "水準測量", "地形測量", "路線測量", "用地測量"]
T["text_exceptions"] = (
    [{"comp": "chapter_door", "text": n, "reason": "章扉の作業名は「5つのうち1つが灯る」形を見せる（全パート共通の型、1小節）"} for n in JOB_NAMES]
    + [{"comp": "chapter_door", "text": "測量部門のしごと", "reason": "章扉の見出し（全パート共通の型、1小節）。声 N1a が同じことを言う"},
       {"comp": "endcard", "text": "ナレーション（仮）VOICEVOX:冥鳴ひまり", "reason": "仮ナレの規約上の表示。本ナレに差し替えたら消す"},
       {"comp": "b5_sea", "text": "0", "reason": "0 の丸（記号。声「ゼロ」と同時に出て、白い紙まで約 4 秒）"}])
T["caption_exceptions"] = [{"shots": sorted({s["shot"] for s in T["shots"]}),
                            "reason": "水準の元素材（S・K・N）には焼き込みテロップがない。この検査は基準点パートの青いテロップ用で、青い車を拾う"}]
T["duration"] = DUR
T["speech_ratio"] = round(sum(v["dur"] for v in T["vo"]) / DUR, 3)

vs = sorted(T["vo"], key=lambda v: v["start"])
for a, b in zip(vs, vs[1:]):
    assert a["start"] + a["dur"] + 0.38 <= b["start"] + 0.01, f"VO の間が 0.4 秒ない {a['id']} / {b['id']}"
for s in T["scenes"] + T["shots"] + T["stills"]:
    assert s.get("purpose"), f"目的がない：{s['id']}"
assert vs[-1]["start"] + vs[-1]["dur"] <= at(28), "N12 が終わりの画にかかる"

(ROOT / "comp/timeline.json").write_text(json.dumps(T, ensure_ascii=False, indent=1))
print(f"duration {T['duration']}s  speech ratio {T['speech_ratio']}")
for bt in T["beats"]:
    print(f"  {bt['id']:4} {bt['start']:6.2f}–{bt['end']:6.2f} ({bt['dur']:.1f}s) {bt['purpose']}")
for v in T["vo"]:
    print(f"  {v['id']:4} {v['start']:6.2f}–{v['start'] + v['dur']:6.2f}")
for t, w in sorted(T["sync"]):
    print(f"  sync {t:6.2f} {w}")
