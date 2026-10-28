"""尺とタイミングの正本 comp/timeline.json を作る（水準測量パート、plan/plan_v2.md §5）。基準点パートと同じ 24 小節の格子・同じ曲の編集。
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

# 効果音の組（v4.7）："lab"＝効果音ラボの音（声の帯域より上にあり、ナレの最中でも聞こえる：音のレビュー A3）／"synth"＝v4.6 までの自作の合成音
# 効果音ラボの規約で素材の再配布は禁止 → mp3 はリポジトリに入れず、SE_DIR（既定 assets/se/、.gitignore 済み）に各自で置く（assets/README.md）
# 環境変数 SE_SET=lab|synth|auto（既定 auto：SE_DIR に必要な mp3 がそろっていれば lab、なければ synth に落として警告）
import os
SE_ASSETS = os.environ.get("SE_DIR", "assets/se")       # 相対パスはリポジトリの根から
SE_NEED = ["tones/decision28.mp3", "tones/decision6.mp3", "tones/cursor3.mp3", "foley/mechanical-pencil-write1.mp3"]
_se_root = pathlib.Path(SE_ASSETS) if os.path.isabs(SE_ASSETS) else ROOT / SE_ASSETS
_missing = [n for n in SE_NEED if not (_se_root / n).exists()]
SE_SET = os.environ.get("SE_SET", "auto")
if SE_SET == "auto":
    SE_SET = "synth" if _missing else "lab"
    if _missing:
        print(f"WARNING: 効果音ラボの素材が {_se_root} にない（{', '.join(_missing)}）→ 自作の合成音（SE_SET=synth）で作る。"
              " v4.10 と同じ音にするには assets/README.md の手順で置く")
SE_LAB = {"glow": ("tones/decision28.mp3", -12.0), "lock": ("tones/decision6.mp3", -9.0),
          "measure": ("tones/cursor3.mp3", -10.0), "click": ("tones/decision28.mp3", -8.0)}   # (素材, 0.4秒窓の最大の VO_REF 比)

def se(kind, t, note="", gain_db=0.0):
    e = {"kind": kind, "start": f(t), "note": note, "gain_db": gain_db}
    if SE_SET == "lab" and kind in SE_LAB:
        src, tgt = SE_LAB[kind]
        e.update({"src": f"{SE_ASSETS}/{src}", "target": tgt, "gain_db": gain_db * 0.5})
    T["se"].append(e)

def foley(src, t, dur, target, note="", **kw):
    if SE_SET != "lab":   # 合成音の組には「描く音」がない（v4.6 まで無し）
        return
    T["se"].append({"kind": "foley", "start": f(t), "note": note, "src": f"{SE_ASSETS}/{src}", "dur": dur, "target": target,
                    "level": "p90", **kw})

def beat(id_, start, end, purpose):
    T["beats"].append({"id": id_, "start": f(start), "end": f(end), "dur": round(end - start, 3), "purpose": purpose})


DOOR_ICON = (650, 470)          # 章扉の水準測量アイコンの中心（chapter_door.html の XS[1]）
LENS = (1318, 497)              # L01（レベルだけの静止）の対物レンズ＝タイトルの照準の行き先（人はいない）
HAND = (round(DOOR_ICON[0] + 0.45 * (LENS[0] - DOOR_ICON[0])), round(DOOR_ICON[1] + 0.45 * (LENS[1] - DOOR_ICON[1])))

# ---------------- B1 章扉 → タイトル（1〜3小節） ----------------
scene("chapter_door", 0, cut(2), {"icons_in": at(1, 2), "lit": at(1, 3), "morph": at(1, 4), "fly": at(1, 4) + 0.1},
      "部門の中の1作業だと、形で示す（全パート共通）。灯るのは水準測量", variables={"active": 1, "to_x": HAND[0], "to_y": HAND[1]})
se("glow", at(1, 3), "章扉で水準測量のアイコンが灯る")
still("L01_still", cut(2), cut(4), "主役の機械（レベル）だけの静止。固定カメラなので止めても不自然でない。ゆっくり寄る")
move("still_L01_still", cut(2), cut(4), 1.0, 1.0 + 0.02 * (cut(4) - cut(2)), f"{LENS[0] / 19.2:.2f}% {LENS[1] / 10.8:.2f}%",
     "照準とレンズへ視線を集める（毎秒2%）")
lock = at(2, 3)
vo("N1a", at(1, 3) + 0.55 - VO["N1a"]["keywords"]["ひとつ"])
vo("N1b", lock + 0.12 - VO["N1b"]["keywords"]["水準測量"])
scene("title", cut(2), cut(4), {"reticle_in": cut(2), "lock": lock, "title_in": lock + 0.2, "sub_in": lock + 0.32, "out": cut(4) - 0.2},
      "章の提示。照準がレベルの対物レンズに合う", overlay=True, diagram=False, cut_point=False,
      variables={"target_x": LENS[0], "target_y": LENS[1], "from_x": HAND[0], "from_y": HAND[1]})
se("lock", lock, "照準が合う電子音（シリーズ共通の合図。このパートでは照準の2か所だけ）")
beat("B1", 0, at(4), "章扉→タイトル")

# ---------------- B2 現場へ（4〜6小節） ----------------
shot("L02", cut(4), cut(5), 2.00, "三脚を立てて脚を開く。人と現場")
shot("L03", cut(5), cut(6, 3), 51.0, "箱から出したレベルを三脚に載せる（批評 v1：51–53.6 秒）")
shot("L04", cut(6, 3), cut(7), 7.95, "遠くで標尺を立てる人。次の用語（水準点）の前ぶれ（批評 v1）")
vo("N2", at(4) + 0.4)
beat("B2", at(4), at(7), "人と現場。前のパート（位置）と対の「高さ」")

# ---------------- B3 水準点とは（7〜8小節） ----------------
s, _ = vo("N3", at(7) + 0.45)
scene("d0_benchmark", cut(7), cut(9), {"stone_in": cut(7), "staff_in": cut(7) + 0.6, "term_in": cut(7) + 1.1,
                                       "pulse": kw("N3", s, "水準点"), "out": cut(9) - 0.05},
      "用語「水準点」を、標石の形と標尺が立つ姿と一緒に（L04 の標尺から形でつなぐ）")
beat("B3", at(7), at(9), "水準点とは")

# ---------------- B4 はかる（9〜11小節） ----------------
# 9 小節頭（曲でいちばん強い一打）で 2 人と道具が 1 つの画に入るカットへ。ラベルだけ（線は引かない：低い画では水平の線が斜めに写る）
shot("L05", cut(9), cut(10, 3), 3.80, "のぞく人と遠くの標尺の人。道具の名前（ラベル）")
scene("k_labels", cut(9), cut(10, 3), {"level": at(9) + 0.3, "staff": at(9) + 0.45, "out": cut(10, 3) - 0.3},
      "何をどの道具ではかるか（レベル・標尺＝ものさし）", overlay=True, diagram=False, cut_point=False,
      variables={"lv_x": 1080, "lv_y": 368, "st_x": 714, "st_y": 610})
shot("L06", cut(10, 3), cut(11, 2), 2.50, "のぞき始める顔。「のぞくと」の言葉に合わせる")
s4, n4e = vo("N4", at(10, 3) + 0.25 - VO["N4"]["keywords"]["のぞく"] + 0.55)
line_t = kw("N4", s4, "水平な線")
# ---------------- B5 しくみ（12〜15小節）：看板の動き。d2_level は B4 の終わりの静止から始まる ----------------
d2s, d2e = cut(11, 2), cut(16)
shrink = line_t + 0.75   # 点線が伸びきってから縮める（N4 の終わりを待たない。縮む→溶ける→地面→標尺を1つずつ：独立レビュー v1.1）
s5, n5e = vo("N5a", n4e + 0.25)
s5b, _ = vo("N5b", n5e + 0.5)
scene("d2_level", d2s, d2e, {"line": line_t - 0.1, "shrink": shrink, "zero": kw("N5a", s5, "ものさし"), "read_a": kw("N5a", s5, "2本"),
                             "read_b": kw("N5a", s5, "ものさし") + 0.2, "caption": s5b - 0.3, "diff": s5b + 0.2, "low": kw("N5b", s5b, "低い")},
      "しくみの核心：目線＝水平の線 → 横から見た図 → 2本のものさし → 目盛りが大きいほうが低い",
      variables={"eye_x": 912, "eye_y": 520, "mid_x": 1125})
T["intended_freezes"].append([f(d2s), f(shrink), "L11_still（人が離れたレベルに目線の点線を引く静止）"])
foley("tones/sceneswitch1.mp3", line_t - 0.1, 1.2, -30.0, "目線の点線が伸びる（電子音にしない＝光と区別：批評 v1）", fade_out=0.3)
# 差の段のクリックは外した（決めの言葉「低い」の頭に重なる：独立レビュー v1.1）
beat("B4", at(9), at(12), "はかる（道具と目線）")
beat("B5", at(12), at(16), "しくみ（目盛りが大きいほうが低い）")

# ---------------- B6 確かめる人（16〜17小節） ----------------
shot("L07", cut(16), cut(17), 15.40, "書きとめる人（腰から上）。奥に標尺の人")
shot("L08", cut(17), cut(18), 7.80, "つまみを回してのぞく顔。図解から人へ戻る")
s6, _ = vo("N6", at(16) + 0.4)
foley("foley/mechanical-pencil-write1.mp3", kw("N6", s6, "書きとめ") - 0.2, 1.4, -28.0, "書く音（ごく小さく）", highpass=400, fade_in=0.1, fade_out=0.3)
beat("B6", at(16), at(18), "確かめる人")

# ---------------- B7 高さのバトン（18〜20小節） ----------------
shot("L09", cut(18), cut(18, 3), 168.0, "標尺を持って次の点へ歩き出す人＝「目で読める所まで」")
s7, _ = vo("N7", at(18))
scene("d3_relay", cut(18, 3), cut(21), {"in": cut(18, 3), "reach": kw("N7", s7, "目で読める") - 0.2, "p1": kw("N7", s7, "目で読める") + 1.0, "move": kw("N7", s7, "前へ移して") - 0.9,
                                      "leap": kw("N7", s7, "前へ移して") + 0.35, "line2": kw("N7", s7, "前へ移して") + 0.65,
                                      "p2": kw("N7", s7, "前へ移して") + 0.65, "out": cut(21) - 0.05},   # v1.3：入れ替えを声の切れ目へ（独立レビュー v1.2）
      "高さのバトン：機械を前へ移し、高さを次の点へつなぐ（部門の中での役割＝高さのもと）")
se("click", kw("N7", s7, "前へ移して") + 0.65, "次の点に高さが灯る（9.75 m を 2 秒以上読ませる：QC v1.1）", gain_db=-6.0)
beat("B7", at(18), at(21), "高さをつなぐ")

# ---------------- B8 締め（21〜24小節） ----------------
l10s = cut(21); l10e = l10s + META["L10"]["dur"] - 0.08
shot("L10", l10s, l10e, 172.9, "のぞく人と遠くの人。仕事は続く。曲の最後の一打で切り替え（480p なので寄りはごく弱く）")
push0, push_rate = 1.0, 0.004
push1 = push0 + push_rate * (l10e - l10s)
move("v_L10", l10s, l10e, push0, push1, "50% 45%", "止まって見えないための、ごく弱い寄り（毎秒0.4%）")
s, n8e = vo("N8", at(21) + 0.9)
end = DUR
GROUND = (1600, 760)  # 右の路面（人・締めの文字にかからない：独立レビュー v1.1）
door = kw("N8", s, "水準測量"); ec_lock = n8e + 0.12
scene("endcard", l10s, end, {"text_in": l10s + 0.15, "bg_in": l10e - 1 / FPS, "reticle": door - 1.75, "paper": door - 0.8, "door": door,
                             "lock": ec_lock, "fade": end - 0.5},
      "締めの一文。照準が縮んで章扉の水準測量アイコンに戻る（章扉と同じ形で閉じる）", overlay=True, diagram=False, cut_point=False,
      variables={"push_from": round(push1, 4), "push_rate": push_rate, "icon_x": DOOR_ICON[0], "icon_y": DOOR_ICON[1],
                 "point_x": GROUND[0], "point_y": GROUND[1], "active": 1})
T["intended_freezes"].append([f(l10e), f(end), "endcard（L10 の最後のコマ）"])
se("lock", ec_lock, "照準が章扉のアイコンに戻り、文が終わった後の合図（小さめ）", gain_db=-6.0)
beat("B8", at(21), end, "締め")

T["bgm"] = {"start": 0.0, "end": f(end), "pause": None, "bars": "1-12,25-36", "hold": {"at": 55.0, "len": 3.0, "xfade": 0.4},
            "note": "基準点パートと同じ曲・同じ編集（シリーズで統一）。1〜12＋25〜36小節、最後の和音を 3 秒のばす"}
T["amb"].append({"start": 0.0, "end": None, "note": "環境音。図解区間は下げる（ミックスで指定）"})
JOB_NAMES = ["基準点測量", "水準測量", "地形測量", "路線測量", "用地測量"]
T["text_exceptions"] = (
    [{"comp": "chapter_door", "text": n, "reason": "章扉の作業名は「5つのうち1つが灯る」形を見せる1回目。締めの章扉でもう一度読める"}
     for n in JOB_NAMES]
    + [{"comp": "endcard", "text": "ナレーション（仮）VOICEVOX:冥鳴ひまり", "reason": "仮ナレの規約上の表示。本ナレに差し替えたら消す"}])
T["duration"] = f(end)
T["speech_ratio"] = round(sum(v["dur"] for v in T["vo"]) / end, 3)

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
