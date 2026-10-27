"""編集計画用：カットごとのカメラの動き・明るさ・色を測り analysis/plan/shot_motion.json と .md に書く。
使い方: python3 scripts/40_shot_motion.py
カメラの動きは 0.25 秒ごとの位相相関（全体の平行移動 px/秒）と、フレーム差（被写体の動き）で近似する。
"""
import json, pathlib
import cv2, numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
CUTS = [0.0, 5.739, 8.909, 14.615, 17.885, 20.354, 23.457, 26.593, 30.664, 36.670, 39.74]
cap = cv2.VideoCapture(str(ROOT / "source/input.mp4"))
fps = cap.get(cv2.CAP_PROP_FPS)
frames = []
ok = True
while ok:
    ok, f = cap.read()
    if ok: frames.append(cv2.resize(f, (480, 270), interpolation=cv2.INTER_AREA))
step = int(round(fps / 4))
rows = []
for i in range(10):
    a, b = int(CUTS[i] * fps) + 3, int(CUTS[i + 1] * fps) - 3
    samples = []
    for k in range(a, b - step, step):
        g0 = cv2.cvtColor(frames[k], cv2.COLOR_BGR2GRAY).astype(np.float32)
        g1 = cv2.cvtColor(frames[k + step], cv2.COLOR_BGR2GRAY).astype(np.float32)
        # 焼き込みテロップを避けて中央部で測る
        (dx, dy), _ = cv2.phaseCorrelate(g0[60:220, 40:440], g1[60:220, 40:440])
        diff = float(np.abs(g1 - g0).mean())
        samples.append((round(CUTS[i] + (k - a) / fps, 2), dx * 4 * 4, dy * 4 * 4, diff))  # 1920 基準 px/秒
    s = np.array([x[1:] for x in samples])
    mid = frames[(a + b) // 2]
    hsv = cv2.cvtColor(mid, cv2.COLOR_BGR2HSV)
    lab = cv2.cvtColor(mid, cv2.COLOR_BGR2LAB)
    rows.append({
        "id": f"S{i+1:02d}", "in": CUTS[i], "out": CUTS[i + 1], "len": round(CUTS[i + 1] - CUTS[i], 2),
        "pan_px_s_med": round(float(np.median(np.hypot(s[:, 0], s[:, 1]))), 1),
        "pan_px_s_max": round(float(np.max(np.hypot(s[:, 0], s[:, 1]))), 1),
        "pan_dir": "左右" if abs(np.median(s[:, 0])) > abs(np.median(s[:, 1])) else "上下",
        "pan_dx_med": round(float(np.median(s[:, 0])), 1), "pan_dy_med": round(float(np.median(s[:, 1])), 1),
        "subject_diff": round(float(s[:, 2].mean()), 2),
        "luma": round(float(lab[..., 0].mean() / 2.55), 1),
        "sat": round(float(hsv[..., 1].mean() / 2.55), 1),
        "warm_b": round(float(lab[..., 2].mean() - 128), 1),
        "clip_pct": round(float((lab[..., 0] > 250).mean() * 100), 2),
        "trace": [[t, round(dx, 1), round(dy, 1)] for t, dx, dy, _ in samples],
    })
out = ROOT / "analysis/plan"; out.mkdir(parents=True, exist_ok=True)
(out / "shot_motion.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1))
md = ["| ID | 長さ | カメラの動き 中央値/最大 (px/秒) | 方向 dx,dy | 被写体の動き | 明るさ | 彩度 | 暖色(b) | 白飛び% |", "|---|---|---|---|---|---|---|---|---|"]
for r in rows:
    md.append(f"| {r['id']} | {r['len']} | {r['pan_px_s_med']} / {r['pan_px_s_max']} | {r['pan_dx_med']},{r['pan_dy_med']} | {r['subject_diff']} | {r['luma']} | {r['sat']} | {r['warm_b']} | {r['clip_pct']} |")
(out / "shot_motion.md").write_text("\n".join(md) + "\n")
print("\n".join(md))
