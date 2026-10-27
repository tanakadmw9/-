"""チームB：実写カットの中間素材を作る（元素材は読むだけ）。
teamB/comp/timeline.json の shots から、カットごとに
  元の範囲を切り出し → 拡大（lanczos）→ シネスコの画（1920×804）に切り出し → 色（共通の調子＋カットごとの補正）→ ごく薄いグレイン
  → 必要なら最後のコマを止めて延長（freeze_tail）
を行い、teamB/comp/assets/video/<id>.mp4 に書く（音なし、H.264 CRF 12、29.97fps）。
使い方: python3 teamB/scripts/20_cuts.py [id ...]
"""
import json, pathlib, subprocess, sys, hashlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT.parent / "source/input.mp4"
T = json.loads((ROOT / "comp/timeline.json").read_text())
OUT = ROOT / "comp/assets/video"; OUT.mkdir(parents=True, exist_ok=True)
W, H = 1920, T["frame"]["img_h"]
LOOK = T["look"]["base"]           # 全カット共通の調子
FPS = "30000/1001"
# 元素材のカットの変わり目（ffmpeg の scene 検出で実測、docs/02 のカット表と一致）
CUTS = [5.739, 8.909, 14.615, 17.885, 20.354, 23.457, 26.593, 30.664, 36.670, 39.80]

def build(s):
    sc = s.get("scale", 1.0)
    # left, top は元の画（1920×1080）の座標。そこから 1920/sc × 804/sc を切り出して 1920×804 に拡大（lanczos）
    w = s.get("w", W)   # 分割画面の左の窓は 1056 幅
    cw, ch = round(w / sc), round(H / sc)
    pre = min(1.0, s["src_in"])  # 少し手前から読み、trim でコマの時刻どおりに切る（次のカットのコマを拾わない）
    vf = [f"trim=start={pre:.4f}:duration=__DUR__", "setpts=PTS-STARTPTS",
          f"crop={cw}:{ch}:{s.get('left', 0)}:{s['top']}",
          f"scale={w}:{H}:flags=lanczos" if sc != 1.0 else None,
          s.get("grade") or None, LOOK,
          "noise=alls=3:allf=t", "format=yuv420p"]
    # 元のカットの終わり（次のカットの頭）より 0.1 秒手前までしか使わない。足りない分と止める分は最後のコマを延ばす
    nxt = min(b for b in CUTS if b > s["src_in"] + 0.05)
    live = min(s["dur"] - s.get("freeze_tail", 0), nxt - 0.1 - s["src_in"])
    vf.append(f"tpad=stop_mode=clone:stop_duration={s['dur'] - live + 0.2:.4f}")
    dur = live
    vf = ",".join(v for v in vf if v).replace("__DUR__", f"{dur:.4f}")
    key = hashlib.md5((json.dumps([s, LOOK, dur]) + pathlib.Path(__file__).read_text()).encode()).hexdigest()[:10]  # 設定かスクリプトが変われば作り直す
    out = OUT / f"{s['id']}.mp4"; stamp = OUT / f".{s['id']}.key"
    if out.exists() and stamp.exists() and stamp.read_text() == key:
        return print("skip", s["id"])
    cmd = ["ffmpeg", "-v", "error", "-y", "-ss", f"{s['src_in'] - pre:.4f}", "-i", str(SRC),
           "-vf", vf, "-r", FPS, "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "12",
           "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", str(out)]
    subprocess.run(cmd, check=True); stamp.write_text(key)
    print("made", s["id"], s["shot"], f"{s['src_in']}+{dur:.2f}s x{s.get('scale', 1.0)}")

only = set(sys.argv[1:])
for s in T["shots"]:
    if not only or s["id"] in only:
        build(s)
