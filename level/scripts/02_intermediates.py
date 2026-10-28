"""中間素材の生成（水準測量パート）：素材3本から、カットごとに切り出し → 拡大(lanczos) → 色補正 → デバンド → 薄いグレイン。
出力：intermediate/<grade>/<shot>.mp4（無音、H.264 CRF12、29.97fps、GOP 15）と、静止用フレーム PNG、meta.json。
使い方：python3 scripts/02_intermediates.py [grade]   grade = A | B | C（既定 B）
素材（source/、変更しない）：S_sueru.mp4（据える-引き 848×480 24fps）、K_kansoku.mp4（観測-引き 1080p）、N_nozoki.mp4（覗き-寄り 1080p、別の場所）
"""
import subprocess, sys, json, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
GRADE = sys.argv[1] if len(sys.argv) > 1 else "B"
OUT = ROOT / "intermediate" / GRADE; OUT.mkdir(parents=True, exist_ok=True)
SRC = {"S": ROOT / "source/S_sueru.mp4", "K": ROOT / "source/K_kansoku.mp4", "N": ROOT / "source/N_nozoki.mp4"}

# カット：(素材, 元の秒 in, 元の秒 out, 切り出し窓 (x, y, w, h)＝元の画素, 目的)。窓は 16:9。
# 焼き込みテロップはない。窓は「見せたい物」に寄せるためだけに使う。S は 480p なので拡大は 1.25 倍まで（それ以上は甘い）
SHOTS = {
    "L01": ("N", 0.10, 0.95, (0, 0, 1920, 1080), "レベルだけ（斜め後ろから）。題の背景（静止して使う）"),
    "L02": ("S", 1.80, 4.90, (0, 0, 848, 477), "三脚を立てて脚を開く"),
    "L03": ("S", 50.8, 55.0, (0, 0, 848, 477), "箱から出したレベルを三脚に載せる（批評 v1：51–53.6 秒）"),
    "L04": ("K", 7.80, 9.50, (380, 300, 960, 540), "遠くで標尺を立てる人（2 倍）"),
    "L05": ("K", 3.80, 7.60, (0, 0, 1920, 1080), "のぞく人と遠くの標尺＝2人と道具（ラベルを付ける）"),
    "L06": ("N", 2.40, 4.50, (0, 0, 1920, 1080), "のぞき始める顔（B4）"),
    "L07": ("K", 15.3, 18.2, (548, 0, 1372, 772), "書きとめる人（腰から上、1.4 倍）。奥に標尺の人"),
    "L08": ("N", 7.60, 10.6, (230, 160, 1440, 810), "つまみを回す顔（1.33 倍。B4 の秒と重ならない）"),
    "L09": ("S", 167.8, 170.8, (0, 0, 848, 477), "標尺を持って次の点へ歩き出す人"),
    "L10": ("S", 172.9, 178.6, (0, 0, 848, 477), "のぞく人と遠くの人＝締め（480p なので寄らない）"),
    "L11": ("N", 12.55, 13.30, (0, 0, 1920, 1080), "人が離れたレベルだけ。目線の点線を引く静止（B4→B5 の看板）"),
}
GRADES = {
    "A": "eq=saturation=0.95:gamma=1.0",
    # B：基準点パートと同じ「落ち着いた暖かさ」
    "B": "huesaturation=hue=0:saturation=-0.18:colors=g+y:strength=1,eq=saturation=0.95:contrast=1.03:brightness=-0.01,"
         "colorbalance=rs=0.02:bs=-0.02:rm=0.025:bm=-0.02:rh=0.01:bh=-0.015,curves=all='0/0.02 0.5/0.5 0.92/0.88 1/0.93'",
    "C": "huesaturation=saturation=-0.28:colors=g+y:strength=1,eq=saturation=0.85:contrast=1.08:brightness=-0.02,"
         "colorbalance=rm=0.01:bm=0.01,curves=all='0/0.03 0.25/0.22 0.75/0.78 1/0.92'",
}
# 素材ごとの合わせ：S は 480p の拡大なので軽くシャープ。N は別の場所（生け垣の緑が強い）→ 緑をもう少し下げる。K・S は曇天で冷たい
SRC_ADJ = {
    "S": "unsharp=5:5:0.6:5:5:0.0,colorbalance=rm=0.02:bm=-0.02",
    "K": "colorbalance=rm=0.02:bm=-0.02",
    "N": "huesaturation=saturation=-0.08:colors=g+y:strength=1",
}
POST = "deband=1thr=0.015:2thr=0.015:3thr=0.015:range=16:blur=1,noise=c0s=3:c0f=t+u"

def run(cmd):
    subprocess.run(cmd, check=True)

meta = {}
for shot, (src, a, b, (x, y, w, h), why) in SHOTS.items():
    vf = f"crop={w}:{h}:{x}:{y},scale=1920:1080:flags=lanczos,{GRADES[GRADE]},{SRC_ADJ[src]},{POST},format=yuv420p"
    out = OUT / f"{shot}.mp4"
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{a:.4f}", "-to", f"{b:.4f}", "-i", str(SRC[src]),
         "-an", "-vf", vf, "-r", "30000/1001", "-c:v", "libx264", "-preset", "slow", "-crf", "12", "-g", "15",
         "-pix_fmt", "yuv420p", "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", str(out)])
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(out)],
                               capture_output=True, text=True).stdout)
    meta[shot] = {"source": src, "src_in": a, "src_out": b, "dur": round(dur - 0.04, 4), "crop": [x, y, w, h],
                  "scale": round(1920 / w, 3), "purpose": why}
    print(shot, meta[shot])

# 静止用フレーム（秒は元動画の時刻）
STILLS = {"L01_still": ("L01", 0.30), "L11_still": ("L11", 12.75), "L10_last": ("L10", 178.45)}
for name, (shot, t) in STILLS.items():
    rel = t - meta[shot]["src_in"]
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{rel:.4f}", "-i", str(OUT / f"{shot}.mp4"),
         "-frames:v", "1", str(OUT / f"{name}.png")])
    meta[name] = {"shot": shot, "src_time": t, "rel_time": round(rel, 4)}
(OUT / "meta.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False))
