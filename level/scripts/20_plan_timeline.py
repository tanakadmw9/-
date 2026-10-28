"""尺とタイミングの正本 comp/timeline.json を作る（水準測量パート、plan/plan_v3.md §2）。基準点パートと同じ 24 小節の格子・同じ曲の編集。
小節の格子で作る：曲（New Departure、94.9 BPM）の小節を時間のものさしにし、場面の変わり目は小節の頭、
場面の中のカットは拍の頭に置く（どちらも 1 コマ前＝目が先に変化を感じる分）。尺は 24 小節で固定。
ナレは格子の上に置く（ナレの長さから尺を決めない）。本ナレに差し替えたら、置き場所を拍単位で直す。
入力：audio/vo_temp/vo_timing.json（本ナレ差し替え後は audio/vo_final/vo_timing.json を優先）
使い方：python3 scripts/20_plan_timeline.py
"""
import json, pathlib, os, re, html as _html

ROOT = pathlib.Path(__file__).resolve().parent.parent
FPS = 30000 / 1001
vo_final = ROOT / "audio/vo_final/vo_timing.json"
VO_PATH = vo_final if vo_final.exists() else ROOT / "audio/vo_temp/vo_timing.json"
VO = json.loads(VO_PATH.read_text())["lines"]
VO_DIR = "assets/audio/vo"  # comp/ からの相対
GRADE = os.environ.get("GRADE", "Bplus")   # 色補正の案（v3 で Bplus を採用）
META = json.loads((ROOT / f"intermediate/{GRADE}/meta.json").read_text())  # 各カットの中間素材の頭＝元動画の何秒か（早回しは speed）

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
T["grade"] = GRADE

def vo(id_, start):
    d = VO[id_]["dur"]
    T["vo"].append({"id": id_, "src": f"{VO_DIR}/{id_}.wav", "start": f(start), "dur": d, "text": VO[id_]["text"]})
    return start, start + d

def kw(id_, start, word):
    return start + VO[id_]["keywords"][word]

def shot(id_, start, end, src_time, purpose=""):
    """src_time：このカットの頭に来る元動画の時刻（編集プラン §3 の「元の範囲」）。"""
    ms = max(0.0, src_time - META[id_]["src_in"]) / META[id_].get("speed", 1.0)
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

def move(target, start, end, scale0, scale1, origin, purpose, ease="none"):
    T["moves"].append({"target": target, "start": f(start), "dur": round(end - start, 4), "scale": [scale0, scale1],
                       "origin": origin, "ease": ease, "purpose": purpose})

def html_defaults(comp, names, fallback):
    """場面の HTML（グラフィック担当）の data-composition-variables の default を読む（座標の約束を1か所に）。無ければ fallback。"""
    p = ROOT / "comp/compositions" / f"{comp}.html"
    out = dict(fallback)
    if p.exists():
        m = re.search(r"data-composition-variables='([^']*)'", p.read_text())
        if m:
            for v in json.loads(_html.unescape(m.group(1))):
                if v["id"] in names: out[v["id"]] = v["default"]
    return {k: out[k] for k in names}

# 効果音の組（v4.7）："lab"＝効果音ラボの音（声の帯域より上にあり、ナレの最中でも聞こえる：音のレビュー A3）／"synth"＝v4.6 までの自作の合成音
# 効果音ラボの規約で素材の再配布は禁止 → mp3 はリポジトリに入れず、SE_DIR（既定 assets/se/、.gitignore 済み）に各自で置く（assets/README.md）
# 環境変数 SE_SET=lab|synth|auto（既定 auto：SE_DIR に必要な mp3 がそろっていれば lab、なければ synth に落として警告）
SE_ASSETS = os.environ.get("SE_DIR", "assets/se")       # 相対パスはリポジトリの根から
SE_NEED = ["tones/decision28.mp3", "tones/decision6.mp3", "tones/cursor3.mp3", "tones/sceneswitch1.mp3",
           "foley/mechanical-pencil-write1.mp3", "foley/walk-soil1.mp3"]
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

# ---------------- B2 現場へ（4〜6小節）：人と現場の到着 → 早回しの据え付け → 機械を載せる ----------------
shot("L02", cut(4), cut(5), 0.00, "野帳を持って三脚へ歩いてくる人。人と現場の到着")
shot("L03", cut(5), cut(6), 2.00, "三脚を立て、脚を何度も合わせる（12 倍の早回し）＝準備に手間をかける仕事")
shot("L04", cut(6), cut(7), 51.00, "レベルを箱から出して三脚に載せる（実時間、1.2 倍）＝主役の機械を据える")
vo("N2", at(4) + 0.37)
beat("B2", at(4), at(7), "人と現場の到着。問い（雨の水はなぜ道のはしへ流れる）を置く")

# ---------------- B3 水準点と海（7〜8小節） ----------------
s3, n3e = vo("N3", at(7) + 0.13)
assert n3e <= at(9) - 0.1, f"N3 が 9 小節にかかる（{n3e:.2f}）"
term = kw("N3", s3, "水準点")
# v2.2（監督）：「海から 10.00 m」をできるだけ早く。言葉より 0.3 秒前までは可（docs/04 ±0.3）。海の面（0.6 秒）・海の高さの点線（0.75 秒で描く）を
# 用語カードの 0.35 秒後から詰めて出し、点線が描き終わる手前で高さの矢印
sea_in = term + 0.35
height = max(kw("N3", s3, "海から") - 0.3, sea_in + 0.3 + 0.4)
scene("d0_sea", cut(7), cut(9), {"ground_in": cut(7), "stone_in": kw("N3", s3, "目印") - 0.1, "term_in": term,
                                 "sea_in": sea_in, "sea_line": sea_in + 0.3, "height": height, "out": cut(9) - 0.05},
      "用語「水準点」と、高さの「0」が海であること（地面の断面・標石 → 海の面 → 海から 10.00 m）")
beat("B3", at(7), at(9), "水準点とは（高さの目印。海からの高さ）")

# ---------------- B4 はかる（9〜11小節） ----------------
# 9 小節頭（曲でいちばん強い一打）で、のぞく人と遠くの標尺の人が1つの画に入るカット。本物のレベルから本物の標尺へ目線の点線
shot("L05", cut(9), cut(10, 3), 3.80, "かがんでのぞく人と遠くの標尺の人。道具の名前と、目線が人と人をつなぐこと")
s4, n4e = vo("N4", at(9) + 0.38)
# v2.2（監督）：ラベルを早く出し、遅く消す（「高さをはかる機械」8 字に 3.0 秒）。標尺の補足は「ものさし」（声と同じ言葉）
scene("k_sight", cut(9), cut(10, 3), {"level": cut(9) + 0.4, "staff": cut(9) + 0.85, "line": kw("N4", s4, "向こうに立てた"), "out": cut(10, 3) - 0.1},
      "道具の名前（レベル・標尺）と、本物のレベルから本物の標尺へ引く目線の点線（中心の絵を実写に置く）",
      overlay=True, diagram=False, cut_point=False,
      variables=html_defaults("k_sight", ["lv_x", "lv_y", "st_x", "st_y"], {"lv_x": 1060, "lv_y": 382, "st_x": 712, "st_y": 462}))
shot("L06", cut(10, 3), cut(12), 2.00, "のぞく顔（「のぞいて」が顔の頭に来る）。最後に接眼レンズへ寄る＝看板の動きの助走")
assert abs(kw("N4", s4, "のぞいて") - at(10, 3)) < 0.3, "「のぞいて」が顔のカットの頭に来ない"
LOOK = META["look"]                      # 02_intermediates.py の接眼レンズの位置と寄りの倍率（L_look_end.png と同じ値）
EYE = tuple(LOOK["eye"])
move("v_L06", cut(12) - 1.2, cut(12), 1.0, LOOK["scale"], f"{EYE[0] / 19.2:.2f}% {EYE[1] / 10.8:.2f}%",
     "のぞき穴の中へ入る看板の動き（接眼レンズへ寄る。d2_scope の最初のコマ L_look_end.png と同じ倍率・中心）", ease="power2.in")
beat("B4", at(9), at(12), "はかる（道具・目線・のぞく）")

# ---------------- B5 しくみ（12〜15小節）：のぞき穴の中 → 横から見た図 ----------------
d2s, d2e = cut(12), cut(16, 2)   # v2.2（監督）：決め「0.6 m 低い」を 2 秒読ませるため、16 小節 2 拍まで延ばす（書きとめるカットが短くなる）
GAP5 = 0.25                                              # N5a（語尾を下げずに次へ）と N5b のあいだ
cross = d2s + 1.0
c5 = {"open": d2s, "cross": cross, "shrink": d2s + 1.9, "ground": d2s + 2.2, "level": d2s + 2.45, "staff_b": d2s + 2.7}
s5 = c5["staff_b"] + 0.2 - VO["N5a"]["keywords"]["水平な線"]   # 「水平な線」は右の標尺が出た 0.2 秒後
line5 = kw("N5a", s5, "水平な線")
_, n5e = vo("N5a", s5)
s5b, n5be = vo("N5b", n5e + GAP5)
c5.update({"line": line5, "read_b": kw("N5a", s5, "2本"), "fill": kw("N5a", s5, "読みくらべる"), "caption": s5b - 0.3,
           "low": kw("N5b", s5b, "低い") - 0.3})
assert d2e - c5["caption"] >= 4.0, f"「目盛りが大きいほうが、低い」が 4 秒読めない（{d2e - c5['caption']:.2f}）"
assert d2e - c5["low"] >= 2.0, f"「0.6 m 低い」が 2 秒読めない（{d2e - c5['low']:.2f}）"
assert n5be <= d2e - 0.3, f"N5b が場面の終わりに近い（{n5be:.2f}）"
scene("d2_scope", d2s, d2e, c5,
      "しくみの核心：のぞき穴の中の十字線 → 横線が 1.2 m を指す → そのまま水平な線になり右の標尺 1.8 m へ → 目盛りが大きいほうが低い",
      variables={"eye_x": EYE[0], "eye_y": EYE[1]})
T["intended_freezes"].append([f(d2s), f(d2s + 0.6), "d2_scope の頭：L_look_end.png（のぞく顔の最後のコマ）からのぞき穴が開く。寄りの終わりと同じ画なので止まって見えない"])
T["intended_freezes"].append([f(cross), f(c5["shrink"]), "d2_scope：望遠鏡の中で横線が 1.2 m を指したまま読ませる（声なし。決めの読み）"])
foley("tones/sceneswitch1.mp3", d2s, 1.0, -32.0, "のぞき穴が開く（やわらかい場面転換音、低く）", highpass=150, fade_out=0.35)
se("measure", cross + 0.15, "十字の横線が 1.2 m を読む（声なしの区間）", gain_db=-4.0)
se("measure", c5["read_b"] - 0.14, "右の標尺 1.8 m を読む（「2本」の前の読点の間に置く。声の語にかぶせない）", gain_db=-6.0)
beat("B5", at(12), at(16, 2), "しくみ（同じ水平な線で2本を読みくらべる。目盛りが大きいほうが低い）")

# ---------------- B6 確かめる人（16〜17小節） ----------------
shot("L07", cut(16, 2), cut(17), 15.50, "立って野帳に書きとめる（腰から上、ペンが動いている所から）。図解から人へ戻る")
shot("L08", cut(17), cut(18), 158.30, "次の場所で書き、機械をのぞく（3 倍の早回し）＝B2 の早回しと韻を踏む（また据える＝くり返す仕事）")
s6, n6e = vo("N6", cut(16, 2) + 0.23)   # v2.2：書きとめるカットに入ってから
assert cut(17) <= kw("N6", s6, "次の場所") <= cut(18) - 0.6, "「次の場所へ」が早回しに来ない"
foley("foley/mechanical-pencil-write1.mp3", kw("N6", s6, "書きとめ") - 0.2, 1.4, -28.0, "書く音（ごく小さく）", highpass=400, fade_in=0.1, fade_out=0.3)
beat("B6", at(16, 2), at(18), "確かめる人と、次の場所へ")

# ---------------- B7 となりへ（18〜20小節） ----------------
shot("L09", cut(18), cut(19), 168.00, "標尺を持った人が機械の横を通って先へ歩く（本物の尺取り）")
PASS = 169.0 - 168.0                       # 標尺の人がレベルの横を通り始める（元 169.0–169.8 秒。コンタクトシートで確認）
# v2.2（監督）：hop1 は場面の頭から 0.6 秒以上あと（紙がまだ白い）。ホップは「高さを」「つないで」「いきます」に合わせる
s7 = max(cut(18) + PASS - 0.2, cut(19) + 0.62 - VO["N7"]["keywords"]["高さを"])
assert s7 <= cut(18) + PASS + 0.3, "1回目の「となりへ」が標尺の人の通過からずれる"
s7, n7e = vo("N7", s7)
foley("foley/walk-soil1.mp3", cut(18) + 0.05, 1.6, -34.0, "標尺の人の足音（ごく小さく。画の手前を歩く）", highpass=120, fade_in=0.05, fade_out=0.4)
road = n7e
drop = road + 0.5
drop_end = min(drop + 1.0, cut(21) - 0.7)                 # しずくが止まってから 0.6 秒以上見せて次へ
scene("d3_relay", cut(19), cut(21), {"in": cut(19), "hop1": kw("N7", s7, "高さを"), "hop2": kw("N7", s7, "つないで"),
                                     "hop3": kw("N7", s7, "いきます"), "road": road, "drop": drop, "drop_end": drop_end,
                                     "out": cut(21) - 0.05},
      "見返り：つないだ高さで、水が流れる道がつくれる（N2 の問いの答え。しずくは声なし）")
assert kw("N7", s7, "高さを") - cut(19) >= 0.6, "1回目のホップが場面の頭に近すぎる"
assert cut(21) - drop_end >= 0.6, "しずくが止まってから次のカットまでが短い"
se("measure", drop_end, "しずくが低い点（排水の口）で止まる（ごく小さく1回）", gain_db=-10.0)
beat("B7", at(18), at(21), "高さを、となりへつなぐ → 水が流れる道（見返り）")

# ---------------- B8 締め（21〜24小節） ----------------
l10s = cut(21); l10e = l10s + META["L10"]["dur"] - 0.08
shot("L10", l10s, l10e, 172.9, "のぞく人と遠くの標尺の人。仕事は続く。曲の最後の一打で切り替え（480p なので寄りはごく弱く）")
push0, push_rate = 1.0, 0.004
push1 = push0 + push_rate * (l10e - l10s)
move("v_L10", l10s, l10e, push0, push1, "50% 40%", "止まって見えないための、ごく弱い寄り（毎秒0.4%）")
s8, n8e = vo("N8", at(21) + 0.84)
end = DUR
GROUND = (1600, 760)  # 右の路面（人・締めの文字にかからない：独立レビュー v1.1）
door = kw("N8", s8, "水準測量"); ec_lock = n8e + 0.12
sight = at(21) + 0.44
scene("endcard", l10s, end, {"sight": sight, "text_in": max(sight + 0.9, s8 + 0.1), "bg_in": l10e - 1 / FPS, "reticle": door - 1.75,
                             "paper": door - 0.8, "door": door, "lock": ec_lock, "fade": end - 0.5},
      "締め：B4 と同じ目線の点線（ブックエンド）→ 締めの一文 → 照準が章扉の水準測量アイコンに戻る", overlay=True, diagram=False, cut_point=False,
      variables=dict({"push_from": round(push1, 4), "push_rate": push_rate, "icon_x": DOOR_ICON[0], "icon_y": DOOR_ICON[1],
                      "point_x": GROUND[0], "point_y": GROUND[1], "active": 1},
                     **html_defaults("endcard", ["lv_x", "lv_y", "st_x", "st_y"], {"lv_x": 1268, "lv_y": 350, "st_x": 884, "st_y": 490})))
T["intended_freezes"].append([f(l10e), f(end), "endcard（L10 の最後のコマ。紙が覆う前後の 0.4 秒だけ見える）"])
se("lock", ec_lock, "照準が章扉のアイコンに戻り、文が終わった後の合図（小さめ）", gain_db=-6.0)
beat("B8", at(21), end, "締め（目に見えない高さを、つないでいく）")

T["bgm"] = {"start": 0.0, "end": f(end), "pause": None, "bars": "1-12,25-36", "hold": {"at": 55.0, "len": 3.0, "xfade": 0.4},
            # 9 小節（曲でいちばん強い所）の下の N3・N4（1つの区間に結合される）：ナレとBGMの差 p5 が 14 dB だった → −19（QC ≥15 に余裕）
            "under": [{"t": round(s4 + 0.5, 3), "db": -19.0}],
            "note": "基準点パートと同じ曲・同じ編集（シリーズで統一）。1〜12＋25〜36小節、最後の和音を 3 秒のばす"}
AMB_LOC = ROOT / "audio/amb/amb_loc.wav"   # 元の映像の現場音（scripts/35_make_loc_amb.py）。無ければ合成の風
T["amb"].append({"start": 0.0, "end": None, "src": "audio/amb/amb_loc.wav" if os.environ.get("AMB", "loc") == "loc" else "audio/amb/amb.wav",
                 "note": "環境音。実写の下は元の映像の現場音（道ばたの車と風）、図解区間は下げる（ミックスで指定）"})
JOB_NAMES = ["基準点測量", "水準測量", "地形測量", "路線測量", "用地測量"]
T["text_exceptions"] = (
    [{"comp": "chapter_door", "text": n, "reason": "章扉の作業名は「5つのうち1つが灯る」形を見せる1回目。締めの章扉でもう一度読める"}
     for n in JOB_NAMES]
    + [{"comp": "endcard", "text": "ナレーション（仮）VOICEVOX:冥鳴ひまり", "reason": "仮ナレの規約上の表示。本ナレに差し替えたら消す"}]
    + [{"comp": "d0_sea", "pattern": r"\d\.\d\dm",
        "reason": "「海から 10.00 m」へ数え上がる途中の数字（0.5 秒で数え上がる動き。読ませる文字ではない）"},
       {"comp": "d0_sea", "text": "10.00m",
        "reason": "N3 の尺（9 小節の手前）で 2.5 秒に届かない。同じ「水準点 10.00 m」が d2_scope（約 8 秒）と d3_relay（約 4.5 秒）でもう一度読める"},
       {"comp": "d0_sea", "text": "（数字は例）",
        "reason": "小さな注記（補足）。同じ注記「数字は例です」が d2_scope・d3_relay で長く出る"},
       {"comp": "d2_scope", "text": "9.40m",
        "reason": "場面の終わりに出る新しい点の高さ（補足）。同じ「9.40 m」が d3_relay の1回目のホップで約 4 秒読める"},
       {"comp": "d2_scope", "pattern": r"9\.\d\dm",
        "reason": "「10.00 m」から「9.40 m」へ数え下がる途中の数字（読ませる文字ではない）"}])
T["caption_exceptions"] = [{"shots": sorted({s["shot"] for s in T["shots"]}),
                            "reason": "水準の元素材（S・K・N）には焼き込みテロップがない（analysis/shot_log.md）。この検査は基準点パートの青いテロップ用で、"
                                      "L04 の青い車（Bplus で彩度が上がる）を拾う。検出は表に残す"}]
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
