"""チームB：comp/timeline.json（尺とタイミングの唯一の正本）を書く。
時間は曲の拍から計算する（緑色の木漏れ日：1拍 1.0227秒、1小節 4.091秒。映像の 10.80秒＝曲の1小節目の頭）。
編集の決め（teamB/plan/editing.md v1、content.md v1、監督の決定 teamB/docs/decisions.md）をここに数値で書く。
使い方: python3 teamB/scripts/15_timeline.py"""
import json, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
BEAT = 1.0227; BAR = 4 * BEAT
B1 = 10.80                          # 映像の中の曲の1小節目の頭
def bb(bar, beat=1):                # 映像の中の「小節.拍」→秒（5小節目以降は無音の間 1.53秒ぶん後ろ）
    t = B1 + (bar - 1) * BAR + (beat - 1) * BEAT
    return round(t + (1.53 if bar >= 5 else 0), 3)
GB1 = ("selectivecolor=greens='0 0.08 0 0':yellows='0 0.03 -0.04 0',eq=saturation=0.92,"
       "curves=all='0/0.035 0.25/0.24 0.75/0.76 1/0.955',colorbalance=rm=0.03:gm=0.0:bm=-0.03:rh=0.02:bh=-0.02")
# カットごとの明るさ・暖かさの合わせ（GB1 の前に当てる。弱く）
MATCH = {
    "S02": "eq=gamma=0.97,colorbalance=rh=0.02:bh=-0.02",          # 空が白く冷たい → 少し下げて暖かく
    "S04": "eq=gamma=0.97,colorbalance=rh=0.02:bh=-0.02",
    "S10": "eq=gamma=0.98,colorbalance=rm=0.01:bm=-0.01",
    "S06": "colorbalance=rm=-0.015:bm=0.015",                       # 暖かすぎ → 少し引く
    "S08": "colorbalance=rm=-0.015:bm=0.015",
    "S09": "colorbalance=rm=0.015:bm=-0.015",                       # 冷たい → 少し足す
}
SC = dict(scale=1.06, left=54, top=4)   # S01・S02：下のカプセルを外す
EQ = dict(scale=1.0, left=0, top=177)   # S03以降：左上のカプセルを外す
def shot(id, sh, start, end, src_in, geo, freeze=0.0, **kw):
    d = dict(id=id, shot=sh, start=start, dur=round(end - start, 3), src_in=src_in, grade=MATCH.get(sh, ""), **geo, **kw)
    if freeze: d["freeze_tail"] = round(freeze, 3)
    return d
split = bb(5)            # 28.69 分割画面が開く
s10 = bb(7)              # 36.87 曲のつなぎ目 → S10
s06b = bb(8)             # 40.96 S06 にもう一度（地図・道路の線）
mark = bb(9, 1) + BEAT * 2   # 47.09 金属標へ
end_card = bb(12)        # 57.32 曲の最後の一音
S09_IN = round(bb(3, 3) + (14.60 - 11.95), 3)
shots = [
    shot("c01", "S06", 0.70, 3.77, 20.38, EQ),
    shot("c02", "S03", 3.77, 5.24, 8.93, EQ),
    shot("c03", "S05", 5.24, 7.67, 17.90, EQ),
    shot("c04", "S02", 7.67, B1, 5.76, SC),
    shot("c05", "S04", B1, bb(2, 2), 14.63, EQ, freeze=bb(2, 2) - B1 - 3.20),
    shot("c06", "S01", bb(2, 2), bb(3, 3), 0.62, SC),
    shot("c07", "S03", bb(3, 3), S09_IN, 11.95, EQ),                 # S03 は 14.61 で終わるので拍の格子より 0.4 秒早く切る
    shot("c08", "S09", S09_IN, split, 30.66, EQ),                    # 元のパン・ピント送りは 33.6 で止まる（映像 26.6）
    shot("c09", "S09", split, bb(5, 2), round(30.66 + split - S09_IN, 3), EQ, freeze=0.05, slide=-600),   # 全幅のまま、GSAP で左へ 600px 寄せて窓にする
    shot("c10", "S07", bb(5, 2), bb(6, 1), 23.46, dict(EQ, left=300), win=True),
    shot("c11", "S08", bb(6, 1), s10, 26.61, dict(EQ, left=560), win=True, freeze=0.07),
    shot("c12", "S10", s10, s06b, 36.69, EQ, freeze=s06b - s10 - 3.00),
    shot("c13", "S06", s06b, mark + 1.0, 20.38, EQ, freeze=mark + 1.0 - s06b - 3.07),   # 金属標へ溶ける1秒ぶん長く
]
for s in shots:
    if s.get("win"): s.update(w=1056)   # 分割画面の左の窓（1056×804）。left は窓に入れる元の画の横位置
T = {
    "title": "基準点測量（チームB）地面に“住所”をつける",
    "fps": "30000/1001", "duration": 61.5,
    "frame": {"bar": 138, "img_h": 804},
    "look": {"base": GB1, "name": "GB1 映画寄り・弱"},
    "music": {"file": "/mnt/project-files/dova/03_komorebi.mp3", "beat": BEAT, "bar1_film": B1, "song_bar1": 1.356,
              "segments": [  # [曲の始め, 曲の終わり, 映像の置き場所, fade_in, fade_out]
                  [0.0, 17.72, round(B1 - 1.356, 3), 0.02, 0.30],
                  [17.69, 25.93, round(split - 0.03, 3), 0.03, 0.06],
                  [74.96, 102.48, round(s10 - 0.03, 3), 0.06, 0.8]]},
    "cues": {
        "split": split, "split_arc": bb(5, 3), "split_dist": bb(5, 4), "split_p": bb(6, 4), "s10": s10, "s10_net": round(s10 + 2.05, 3),
        "s10_loop": s06b, "s06_pts": round(s06b + 0.3, 3), "contour": 44.85, "road": 45.30, "mark": mark,
        "shoes": 53.25, "end": end_card, "credit": round(end_card + 1.0, 3), "silence": [27.16, split], "pi": 27.70,
        "title": round(B1 + BEAT, 3), "q": 8.0, "s01_known": bb(2, 3), "s01_new": bb(2, 4), "s01_label": bb(3, 1)},
    "shots": shots,
    "narration": [  # 声の入り（秒）。長さは audio/vo/vo_timing.json
        {"id": "N1", "start": 3.60}, {"id": "N2", "start": 10.10}, {"id": "N3", "start": 16.20},
        {"id": "N4", "start": 29.25}, {"id": "N5", "start": 33.60}, {"id": "N7", "start": 37.90},
        {"id": "N8", "start": 43.35}, {"id": "N9", "start": 48.00}, {"id": "N10", "start": 53.75}],
    "texts": [  # 画面の文字（表示時間は QC で 字数÷4＋1秒 以上を確かめる）
        {"id": "hdr", "text": "測量部門のしごと", "start": B1, "end": bb(2, 2), "where": "bar_top"},
        {"id": "title", "text": "基準点測量", "start": round(B1 + BEAT, 3), "end": bb(2, 2) - 0.3, "where": "sky"},
        {"id": "sub", "text": "地面に“住所”をつける", "start": round(B1 + BEAT + 0.4, 3), "end": bb(2, 2) - 0.3, "where": "sky"},
        {"id": "def", "text": "“住所”＝ 正確な位置と高さ", "start": bb(3, 3), "end": bb(4, 3), "where": "bar_bottom"},
        {"id": "q2", "text": "一度で、おしまい？", "start": s10, "end": s06b, "where": "bar_bottom"},
        {"id": "end_title", "text": "基準点測量", "start": end_card, "end": 61.5, "where": "center"},
    ],
    # 意図した静止（QC の freezedetect で除外する）
    "intended_freezes": [],
}
for s in shots:
    if s.get("freeze_tail"):
        T["intended_freezes"].append([round(s["start"] + s["dur"] - s["freeze_tail"], 3), round(s["start"] + s["dur"], 3), s["id"]])
(ROOT / "comp/timeline.json").write_text(json.dumps(T, ensure_ascii=False, indent=1))
print("cues", T["cues"]); print("shots", [(s["id"], s["start"], s["dur"], s.get("freeze_tail")) for s in shots])
