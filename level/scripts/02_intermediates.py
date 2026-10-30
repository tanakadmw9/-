"""中間素材の生成（水準測量パート v8.6、plan/editing_v8.md §1.2・§5）：素材3本から、カットごとに
ぼかし（看板・店名・ナンバー・ヘルメットの印刷・機械のメーカー名）→ 早回し → 切り出し窓 → 拡大(lanczos) → 色補正 → デバンド → 薄いグレイン。
出力：intermediate/<grade>/<shot>.mp4（無音、H.264 CRF12、29.97fps、GOP 15）と、静止用フレーム PNG、meta.json。
  → scripts/04_stage_assets.sh で comp/assets/video/ に置く（どちらも元映像から作ったものなので、リポジトリに入れない）。
使い方：python3 scripts/02_intermediates.py [grade]   grade = B | Bplus | D（既定 Bplus）
素材（source/、変更しない）：S_sueru.mp4（848×480 24fps）、K_kansoku.mp4（1080p、24.79 秒）、N_nozoki.mp4（1080p、13.35 秒）
ぼかしの窓は元の画素 (x0, y0, x1, y1)。t（元の秒）を付けたものはその間だけ、keys を付けたものは (元の秒, x0, y0) の間を直線で動く。
  動く車のナンバーは、人にかからない道の帯をまとめてぼかす（アニマティック。本制作で追いかけに替える：editing §5.2）。
"""
import subprocess, sys, json, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
GRADE = sys.argv[1] if len(sys.argv) > 1 else "Bplus"
OUT = ROOT / "intermediate" / GRADE; OUT.mkdir(parents=True, exist_ok=True)
SRC = {"S": ROOT / "source/S_sueru.mp4", "K": ROOT / "source/K_kansoku.mp4", "N": ROOT / "source/N_nozoki.mp4"}

# ---- ぼかし（editing §5.2。元の画素） ----
S1 = [(394, 30, 486, 72), (0, 232, 160, 292), (455, 262, 500, 282)]                 # S 1か所目：駅の案内・左の看板・店の看板
S2 = [(535, 0, 648, 22), (0, 170, 100, 206), (100, 200, 312, 262), (605, 205, 690, 230)]   # S 2か所目
KA, KL, KSHOP, KP = (1015, 0, 1245, 100), (0, 465, 490, 575), (1150, 470, 1300, 520), (1680, 568, 1756, 614)
KTRUCK = (1100, 555, 1240, 630)                                                      # 奥の軽トラックの文字とナンバー
K_ALL = [KA, KL, KSHOP, KP, KTRUCK]
# 観測者が手前に来て店の看板・軽トラックを隠したあとは、その窓を外す（人の背中をぼかさない：v4.1 の目視）
K_OPEN = [KA, KL, KP]
K_HELMET = {"w": 150, "h": 90, "keys": [(1.5, 1365, 0), (2.5, 1115, 195), (3.5, 1096, 252), (4.5, 1077, 245), (7.86, 1077, 245)]}  # 観測者のヘルメットの印刷（v4.1 で実測し直し）
K_HELMET_B12 = {"w": 170, "h": 110, "keys": [(8.533, 1060, 250), (13.6, 1060, 250), (14.533, 1135, 45), (15.533, 1255, 25), (16.15, 1255, 25)]}  # 立ち上がるのを追う（v4.1）

SHOTS = {
    # B2 据える：S 48.58–53.63、窓 70,82,707,398、実時間。右の道の車のナンバーは人の右の帯でぼかす
    "B2_S": dict(src="S", a=48.58, b=53.70, crop=(70, 82, 707, 398),
                 masks=S1 + [dict(box=(600, 268, 777, 312), t=(49.3, 53.66)),
                             (418, 203, 480, 220),                                   # 奥の黒い店の看板
                             dict(box=(450, 222, 848, 292), t=(48.58, 52.6)),        # 人の右の道（通る車のナンバー）。人が立つ前まで
                             dict(box=(540, 222, 848, 292), t=(52.6, 53.70)),
                             {"w": 44, "h": 30, "keys": [(48.58, 284, 241), (49.08, 277, 236), (49.58, 275, 233), (50.08, 274, 233),
                                                         (50.58, 277, 223), (51.08, 275, 235), (51.58, 271, 212), (52.08, 318, 88),
                                                         (52.58, 407, 73), (53.08, 453, 78), (53.70, 453, 78)]}],   # ヘルメットの印刷
                 purpose="B2：ケースを開け、持ち上げ、三脚に載せる（S 53.0 で載る）"),
    # B3 はかる：S 56–74 を 4.75 倍（窓 170,40,678,381）
    "B3_S": dict(src="S", a=56.0, b=74.05, crop=(170, 40, 678, 381), speed=4.75, blend=3,
                 masks=S1 + [(540, 270, 848, 345), (170, 270, 318, 310)],
                 purpose="B3：水平にととのえる（4.75 倍）"),
    "B3_N": dict(src="N", a=2.0, b=3.30, crop=(600, 0, 1320, 742), masks=[(1060, 200, 1200, 280)],
                 purpose="B3：機械と顔の全体（1.45 倍）"),
    # B4 問い：K 1.5–7.82 全画面（寄りは timeline の moves）
    "B4_K": dict(src="K", a=1.5, b=7.86, crop=(0, 0, 1920, 1080),
                 masks=K_OPEN + [dict(box=KSHOP, t=(1.5, 2.0)), dict(box=KTRUCK, t=(1.5, 2.0)),
                                 dict(box=(1760, 520, 1920, 700), t=(1.5, 2.9)), dict(box=(1640, 555, 1920, 625), t=(4.3, 7.86)), K_HELMET],
                 purpose="B4：歩いて来てかがむ。遠くに標尺を持って待つ人"),
    # B5 現場：K 18.75–24.753、窓 0,200,1200,675。□ が出てから（31.045＝クリップ頭から 1.657 秒）彩度を 0.3 秒で −40%（明るさ −25% は図の層で）
    "B5_K": dict(src="K", a=18.75, b=24.79, crop=(0, 200, 1200, 675), masks=[KL, KSHOP, KTRUCK],
                 sat_from=1.657, purpose="B5：現場の実写。遠くの標尺手が点に立つ（□・線・棒・点の下地）"),
    # B6 つなぐ：S 169.09–171.62 全画面
    "B6_S": dict(src="S", a=169.09, b=171.66, crop=(0, 0, 848, 477),
                 masks=S2 + [dict(box=(740, 270, 812, 305), t=(169.09, 169.7)), dict(box=(715, 235, 790, 268), t=(171.1, 171.66))],
                 purpose="B6：ものさしを持った人が機械の横を通って次の点へ"),
    "B7_N": dict(src="N", a=3.3, b=5.87, crop=(840, 200, 960, 540), masks=[(1020, 505, 1150, 575)],
                 purpose="B7：目とつまみ（2.0 倍）。メーカー名はぼかす"),
    "B8_K": dict(src="K", a=16.2, b=18.75, crop=(720, 0, 1200, 675), masks=K_OPEN + [(1270, 120, 1395, 175)],
                 purpose="B8：手帳に書く手（1.6 倍）"),
    "B9_S1": dict(src="S", a=172.2, b=174.76, crop=(0, 0, 848, 477), masks=S2 + [(630, 228, 848, 295)],
                  purpose="B9：遠くに着いた標尺手（行き）"),
    "B9_S2": dict(src="S", a=177.0, b=180.2, crop=(170, 40, 678, 381),
                  masks=S2 + [(630, 228, 848, 300), dict(w=56, h=90, keys=[(177.0, 440, 200), (178.0, 432, 212), (179.0, 330, 196), (180.2, 300, 196)])],
                  purpose="B9：のぞく人（帰り、1.25 倍）。自転車の人はぼかす"),
    "B11_S": dict(src="S", a=81.0, b=83.56, crop=(170, 40, 678, 381),
                  masks=S1 + [(170, 262, 420, 302), (470, 262, 848, 302), dict(box=(780, 236, 848, 312), t=(81.0, 81.7))],
                  purpose="B11：人のいない機械（レベル）と流れる車"),
    "B11_N": dict(src="N", a=5.9, b=8.46, crop=(600, 180, 1200, 675), masks=[(1150, 205, 1370, 320), (990, 395, 1170, 480)],
                  purpose="B11：のぞく顔（1.6 倍）"),
    "B12_K": dict(src="K", a=8.533, b=16.15, crop=(0, 0, 1920, 1080), masks=K_OPEN + [K_HELMET_B12],
                  purpose="B12：二人の引き（1.15→1.00 は timeline の moves）"),
}
GRADES = {
    "B": "huesaturation=hue=0:saturation=-0.18:colors=g+y:strength=1,eq=saturation=0.95:contrast=1.03:brightness=-0.01,"
         "colorbalance=rs=0.02:bs=-0.02:rm=0.025:bm=-0.02:rh=0.01:bh=-0.015,curves=all='0/0.02 0.5/0.5 0.92/0.88 1/0.93'",
    "Bplus": "eq=contrast=1.10:saturation=1.30:gamma=1.03,colorbalance=rs=0.02:bs=-0.03:rm=0.035:bm=-0.035:rh=0.015:bh=-0.02,"
             "curves=all='0/0 0.2/0.17 0.5/0.52 0.8/0.84 0.95/0.93 1/0.96'",
    "D": "vibrance=intensity=0.45,colortemperature=temperature=5600:mix=0.6,eq=contrast=1.08:gamma=1.05:saturation=1.08,"
         "curves=all='0/0 0.25/0.23 0.6/0.64 0.9/0.89 1/0.95'",
}
SRC_ADJ = {"S": "unsharp=5:5:0.6:5:5:0.0", "K": "null",
           "N": "huesaturation=saturation=-0.08:colors=g+y:strength=1,colorbalance=rm=-0.01:bm=0.01"}
POST = "deband=1thr=0.015:2thr=0.015:3thr=0.015:range=16:blur=1,noise=c0s=3:c0f=t+u"
FF = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]

def run(cmd):
    subprocess.run(cmd, check=True)

def lerp_expr(keys, a, k):
    """keys [(元の秒, x, y)] → クリップの時刻 t（0＝元の a 秒）での x（k=1）または y（k=2）の式（区間ごとの直線）。"""
    ks = [(round(t - a, 3), p[k - 1]) for t, *p in keys]
    e = str(ks[-1][1])
    for (t0, v0), (t1, v1) in reversed(list(zip(ks, ks[1:]))):
        e = f"if(lt(t,{t1}),{v0}+({v1}-{v0})*(t-{t0})/{t1 - t0},{e})"
    return f"if(lt(t,{ks[0][0]}),{ks[0][1]},{e})"

def mask_chain(masks, a, src, W, H):
    """ぼかしの filter_complex の断片。入力 [m0]、出力 [mz]。"""
    parts, cur = [], "m0"
    rad = 5 if src == "S" else 14
    for i, m in enumerate(masks):
        if isinstance(m, tuple): m = dict(box=m)
        if "box" in m:
            x0, y0, x1, y1 = m["box"]; x1, y1 = min(x1, W), min(y1, H); w, h = x1 - x0, y1 - y0
            xe, ye = str(x0), str(y0)
        else:
            w, h = m["w"], m["h"]; xe, ye = lerp_expr(m["keys"], a, 1), lerp_expr(m["keys"], a, 2)
            xe = f"max(0,min({W - w},{xe}))"; ye = f"max(0,min({H - h},{ye}))"
        r = max(1, min(rad, min(w, h) // 4 - 1))     # 色差は半分の大きさなので 1/4 まで
        en = f":enable='between(t,{m['t'][0] - a:.3f},{m['t'][1] - a:.3f})'" if "t" in m else ""
        parts.append(f"[{cur}]split[b{i}][c{i}];[c{i}]crop={w}:{h}:'{xe}':'{ye}',boxblur={r}:3[k{i}];"
                     f"[b{i}][k{i}]overlay=x='{xe}':y='{ye}'{en}[n{i}]")
        cur = f"n{i}"
    parts.append(f"[{cur}]null[mz]")
    return ";".join(parts)

meta = {}
for shot, d in SHOTS.items():
    src, a, b, (x, y, w, h) = d["src"], d["a"], d["b"], d["crop"]
    W, H = (848, 480) if src == "S" else (1920, 1080)
    sp, blend = d.get("speed", 1.0), d.get("blend", 0)
    post = []
    if blend > 1: post.append(f"tmix=frames={blend}")
    if sp != 1.0: post.append(f"setpts=PTS/{sp}")
    post += [f"crop={w}:{h}:{x}:{y}", "scale=1920:1080:flags=lanczos", GRADES[GRADE], SRC_ADJ[src]]
    if "sat_from" in d:
        t0 = d["sat_from"]
        post.append(f"hue=s='if(lt(t,{t0}),1,if(lt(t,{t0 + 0.3}),1-0.4*(t-{t0})/0.3,0.6))'")
    post += [POST, "format=yuv420p"]
    fc = "[0:v]null[m0];" + mask_chain(d.get("masks", []), a, src, W, H) + ";[mz]" + ",".join(post) + "[out]"
    out = OUT / f"{shot}.mp4"
    run(FF + ["-ss", f"{a:.4f}", "-to", f"{b:.4f}", "-i", str(SRC[src]), "-an", "-filter_complex", fc, "-map", "[out]",
              "-r", "30000/1001", "-c:v", "libx264", "-preset", "slow", "-crf", "12", "-g", "15",
              "-pix_fmt", "yuv420p", "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", str(out)])
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(out)],
                               capture_output=True, text=True).stdout)
    meta[shot] = {"source": src, "src_in": a, "src_out": b, "speed": sp, "dur": round(dur - 0.04, 4), "crop": [x, y, w, h],
                  "scale": round(1920 / w, 3), "purpose": d["purpose"]}
    print(shot, meta[shot])

# 静止用フレーム（元の秒）。K7_82：B4 の終わりの止め絵（1.32 倍の寄りの窓 465,60,1455,818 と同じ画）。B5 の写真が縮む図の頭にも使う
STILLS = {"K7_82": ("B4_K", 7.82, (465, 60, 1455, 818)), "K16_10": ("B12_K", 16.10, None)}
for name, (shot, t, win) in STILLS.items():
    rel = (t - meta[shot]["src_in"]) / meta[shot]["speed"]
    vf = []
    if win:   # 全画面の中間素材（1920×1080）から窓を切り出して拡大
        vf = ["-vf", f"crop={win[2]}:{win[3]}:{win[0]}:{win[1]},scale=1920:1080:flags=lanczos"]
    run(FF + ["-ss", f"{rel:.4f}", "-i", str(OUT / f"{shot}.mp4"), "-frames:v", "1"] + vf + [str(OUT / f"{name}.png")])
    meta[name] = {"shot": shot, "src_time": t, "rel_time": round(rel, 4), "window": win}
(OUT / "meta.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False))
