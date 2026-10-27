"""中間素材の生成：カットごとに切り出し（焼き込みテロップを外す）→ 拡大(lanczos) → 色補正 → デバンド → 薄いグレイン。
出力：intermediate/<grade>/<shot>.mp4（無音、H.264 CRF12、29.97fps、GOP 15）と、静止用フレーム PNG。
使い方：python3 scripts/02_intermediates.py [grade]   grade = A | B | C（既定 B）
"""
import subprocess, sys, json, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "source/input.mp4"
GRADE = sys.argv[1] if len(sys.argv) > 1 else "B"
OUT = ROOT / "intermediate" / GRADE; OUT.mkdir(parents=True, exist_ok=True)

FPS = 30000 / 1001
# カット境界（scene_cuts.txt と一致）。in/out はフレーム端の混入を避けて1フレーム内側。
CUTS = [0, 5.739, 8.909, 14.615, 17.885, 20.354, 23.457, 26.593, 30.664, 36.670, 39.740]
# 切り出し窓 (x, y, w, h) — 16:9 を保つ。S01/S02 は下中央の大テロップ（実測 y779〜、影を含め y765 未満だけ使う）を外す＝1.412倍。
# S03以降は左上の小テロップ（y≤172＋影）を外す＝y180〜、1.2倍。x は被写体に合わせてカットごとに決める。
CROPS = {
    "S01": (150, 0, 1360, 765),
    "S02": (300, 0, 1360, 765),
    "S03": (311, 180, 1600, 900),
    "S04": (155, 180, 1600, 900),
    "S05": (155, 180, 1600, 900),
    "S06": (155, 180, 1600, 900),
    "S07": (155, 180, 1600, 900),
    "S08": (155, 180, 1600, 900),
    "S09": (311, 180, 1600, 900),
    "S10": (155, 180, 1600, 900),
}
# 色補正案（docs/04 §7：強い補正は禁止。緑の彩度をやや下げ、わずかに暖かく、黒を少し締め、ハイライトを抑える）
GRADES = {
    # A：素直（カット間の差をならすだけ・ほぼ元のまま）
    "A": "eq=saturation=0.95:gamma=1.0",
    # B：落ち着いた暖かさ（推奨）— 緑を下げ、わずかに暖色、ハイライトを抑える
    "B": "huesaturation=hue=0:saturation=-0.18:colors=g+y:strength=1,eq=saturation=0.95:contrast=1.03:brightness=-0.01,"
         "colorbalance=rs=0.02:bs=-0.02:rm=0.025:bm=-0.02:rh=0.01:bh=-0.015,curves=all='0/0.02 0.5/0.5 0.92/0.88 1/0.93'",
    # C：記録映画調 — 彩度をさらに落とし、コントラストやや強め
    "C": "huesaturation=saturation=-0.28:colors=g+y:strength=1,eq=saturation=0.85:contrast=1.08:brightness=-0.02,"
         "colorbalance=rm=0.01:bm=0.01,curves=all='0/0.03 0.25/0.22 0.75/0.78 1/0.92'",
}
POST = "deband=1thr=0.015:2thr=0.015:3thr=0.015:range=16:blur=1,noise=c0s=3:c0f=t+u"

def run(cmd):
    subprocess.run(cmd, check=True)

meta = {}
for i, (shot, (x, y, w, h)) in enumerate(CROPS.items()):
    a = CUTS[i] + 1 / FPS; b = CUTS[i + 1] - 1 / FPS
    vf = f"crop={w}:{h}:{x}:{y},scale=1920:1080:flags=lanczos,{GRADES[GRADE]},{POST},format=yuv420p"
    out = OUT / f"{shot}.mp4"
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{a:.4f}", "-to", f"{b:.4f}", "-i", str(SRC),
         "-an", "-vf", vf, "-r", "30000/1001", "-c:v", "libx264", "-preset", "slow", "-crf", "12", "-g", "15",
         "-pix_fmt", "yuv420p", "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", str(out)])
    meta[shot] = {"src_in": round(a, 4), "src_out": round(b, 4), "dur": round(b - a, 4), "crop": [x, y, w, h],
                  "scale": round(1920 / w, 3)}
    print(shot, meta[shot])

# 静止用フレーム（D1：S09、タイトル：S04 の末尾）— 秒は元動画の時刻
STILLS = {"S09_freeze": ("S09", 34.40), "S04_last": ("S04", CUTS[4] - 2 / FPS), "S10_last": ("S10", CUTS[10] - 2 / FPS)}
for name, (shot, t) in STILLS.items():
    rel = t - meta[shot]["src_in"]
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{rel:.4f}", "-i", str(OUT / f"{shot}.mp4"),
         "-frames:v", "1", str(OUT / f"{name}.png")])
    meta[name] = {"shot": shot, "src_time": round(t, 4), "rel_time": round(rel, 4)}
(OUT / "meta.json").write_text(json.dumps(meta, indent=1))
