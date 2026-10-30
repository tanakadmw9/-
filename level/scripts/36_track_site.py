"""B5 の現場の重ね（□・線・棒・点・ラベル）を、カメラの流れに合わせて動かすための追いかけ（editing_v8.md §3.1）。
K 18.75–24.753 の窓 0,200,1200,675 の上半分（空・電柱・建物＝人と車が通らない所）を 0.1 秒ごとに位相相関で比べ、
基準のコマ（K 24.3＝絵コンテで位置を決めたコマ）からのずれを画面の画素（1920×1080、窓の 1.6 倍）で出す。
出力：comp/site_track.json（数字だけ。元映像の画は入らない）。20_plan_timeline.py が読み、b5_site に渡す。
使い方：python3 scripts/36_track_site.py
"""
import json, pathlib, subprocess
import numpy as np, cv2

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "source/K_kansoku.mp4"
A, B, REF, STEP = 18.75, 24.753, 24.3, 0.1
WIN = (0, 200, 1200, 675); SCALE = 1920 / WIN[2]
ROI = (0, 0, 1200, 250)          # 窓の中の上の帯（窓の座標）

def grab(t):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", f"{t:.3f}", "-i", str(SRC), "-frames:v", "1",
                          "-vf", f"crop={WIN[2]}:{WIN[3]}:{WIN[0]}:{WIN[1]},format=gray", "-f", "rawvideo", "-"],
                         capture_output=True, check=True).stdout
    im = np.frombuffer(raw, np.uint8).reshape(WIN[3], WIN[2]).astype(np.float32)
    x0, y0, x1, y1 = ROI
    return im[y0:y1, x0:x1]

ref = grab(REF); win = cv2.createHanningWindow(ref.shape[::-1], cv2.CV_32F)
out = []
for t in np.arange(A, B + 1e-6, STEP):
    (dx, dy), resp = cv2.phaseCorrelate(ref, grab(t), win)
    out.append([round(t - A, 3), round(dx * SCALE, 1), round(dy * SCALE, 1), round(resp, 3)])
    print(f"{t:6.2f}  dx {dx * SCALE:6.1f}  dy {dy * SCALE:6.1f}  resp {resp:.2f}")
(ROOT / "comp/site_track.json").write_text(json.dumps(
    {"note": "B5 の現場の重ねのずれ（画面の画素。基準 K 24.3）。[クリップ頭からの秒, dx, dy, 相関の強さ]。scripts/36_track_site.py が作る",
     "src": [A, B], "ref": REF, "window": WIN, "track": out}, indent=1, ensure_ascii=False))
