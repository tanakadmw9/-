"""中間素材の生成（水準測量パート v4.2、plan/editing_v8.md §1.2）：素材3本から、カットごとに
早回し → 切り出し窓 → 拡大(lanczos) → 色補正 → デバンド → 薄いグレイン。ぼかしは v4.2 で外した（依頼者の判断）。
出力：intermediate/<grade>/<shot>.mp4（無音、H.264 CRF12、29.97fps、GOP 15）と、静止用フレーム PNG、meta.json。
  → scripts/04_stage_assets.sh で comp/assets/video/ に置く（どちらも元映像から作ったものなので、リポジトリに入れない）。
使い方：python3 scripts/02_intermediates.py [grade]   grade = B | Bplus | D（既定 Bplus）
素材（source/、変更しない）：S_sueru.mp4（848×480 24fps）、K_kansoku.mp4（1080p、24.79 秒）、N_nozoki.mp4（1080p、13.35 秒）
masks（任意）：ぼかしの窓は元の画素 (x0, y0, x1, y1)。t（元の秒）を付けたものはその間だけ、keys を付けたものは (元の秒, x0, y0) の間を直線で動く。
"""
import subprocess, sys, json, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
GRADE = sys.argv[1] if len(sys.argv) > 1 else "Bplus"
OUT = ROOT / "intermediate" / GRADE; OUT.mkdir(parents=True, exist_ok=True)
SRC = {"S": ROOT / "source/S_sueru.mp4", "K": ROOT / "source/K_kansoku.mp4", "N": ROOT / "source/N_nozoki.mp4"}

# ---- ぼかし：v4.2 で全部外した（依頼者「ぼかしも要らない」2026-10-30）。仕組み（mask_chain）は残し、masks は空 ----
# ---- 構図の重なりを減らす（v4.2、依頼者「同じ映像使いすぎを正して」）：同じ素材・同じカメラ位置・似た画角は全体で2回まで、となりの拍で続けない ----
#   構図の名前：SA＝S 1か所目の道ばた（コーンとバー）／SE＝S 2か所目に置いた直後（コーンが中央）／SF＝S 2か所目の固定（遠くに標尺手）
#              K-w＝K の引き／K-left＝K の左の窓（遠くの標尺手と足もと）／N＝N の寄り
SHOTS = {
    # B2 据える：SA。ケースを開け、持ち上げ、三脚に載せる（S 53.0 で載る）
    "B2_S": dict(src="S", a=48.58, b=53.70, crop=(70, 82, 707, 398), purpose="B2：ケースを開け、持ち上げ、三脚に載せる（SA）"),
    # B3 はかる：N。接眼に目を当て、つまみを回す（1.45 倍）
    "B3_N": dict(src="N", a=2.0, b=7.10, crop=(600, 0, 1320, 742), purpose="B3：のぞいて、つまみを回す（N、1.45 倍）"),
    # B4 問い：SF。標尺手が遠くへ歩いて点に立つ。観測者は機械のそば（全画面）
    "B4_S": dict(src="S", a=172.2, b=178.56, crop=(0, 0, 848, 477), purpose="B4：遠くの点に立つ標尺手と機械の人（SF）"),
    # B5 現場：K-left。K の左の窓 0,200,1200,675（遠くの標尺手と足もと）。□ が出たら彩度を 0.3 秒で −40%（sat_from は 20 から）
    "B5_K": dict(src="K", a=16.52, b=24.79, crop=(0, 200, 1200, 675), sat_from=3.43,
                 purpose="B5：現場の実写。遠くの標尺手が点に立つ（□・線・棒の下地、K-left）"),
    # B6 つなぐ：SF。標尺を持った人が機械の横を通って次の点へ
    "B6_S": dict(src="S", a=169.09, b=171.66, crop=(0, 0, 848, 477), purpose="B6：ものさしを持った人が機械の横を通って次の点へ（SF）"),
    # B7 読む：N。目とつまみ（2.0 倍）。B3 と別の秒・別の画角
    "B7_N": dict(src="N", a=7.10, b=9.70, crop=(840, 200, 960, 540), purpose="B7：目とつまみ（N、2.0 倍）"),
    # B8 書く：SE。2か所目に置いた直後、三脚の左で立って野帳に書く（159.5–161.5 は止まっている）
    "B8_S": dict(src="S", a=159.5, b=162.10, crop=(0, 0, 848, 477), purpose="B8：三脚の左で野帳に書く（SE）"),
    # B9 確かめる：K-w。歩いて来て、かがんで遠くの標尺をのぞく（一続き）
    "B9_K": dict(src="K", a=2.80, b=8.50, crop=(0, 0, 1920, 1080), purpose="B9：歩いて来てのぞく。遠くに標尺手（K-w）"),
    # B11 人：SA。ケースから黄色の野帳を取り、カメラの方へ歩いて来る
    "B11_S": dict(src="S", a=126.6, b=131.70, crop=(0, 0, 848, 477), purpose="B11：野帳を取って歩いて来る人（SA）"),
    # B12 締め：K-w。二人の引き（1.15→1.00 は timeline の moves）
    "B12_K": dict(src="K", a=8.533, b=16.15, crop=(0, 0, 1920, 1080), purpose="B12：二人の引き（K-w）"),
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
STILLS = {"S178_5": ("B4_S", 178.50, None), "K16_10": ("B12_K", 16.10, None)}
for name, (shot, t, win) in STILLS.items():
    rel = (t - meta[shot]["src_in"]) / meta[shot]["speed"]
    vf = []
    if win:   # 全画面の中間素材（1920×1080）から窓を切り出して拡大
        vf = ["-vf", f"crop={win[2]}:{win[3]}:{win[0]}:{win[1]},scale=1920:1080:flags=lanczos"]
    run(FF + ["-ss", f"{rel:.4f}", "-i", str(OUT / f"{shot}.mp4"), "-frames:v", "1"] + vf + [str(OUT / f"{name}.png")])
    meta[name] = {"shot": shot, "src_time": t, "rel_time": round(rel, 4), "window": win}
(OUT / "meta.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False))
