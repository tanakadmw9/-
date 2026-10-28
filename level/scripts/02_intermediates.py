"""中間素材の生成（水準測量パート、計画 v3）：素材3本から、カットごとに切り出し → （早回し）→ 拡大(lanczos) → 色補正 → デバンド → 薄いグレイン。
出力：intermediate/<grade>/<shot>.mp4（無音、H.264 CRF12、29.97fps、GOP 15）と、静止用フレーム PNG、meta.json。
使い方：python3 scripts/02_intermediates.py [grade]   grade = B | Bplus | D（既定 Bplus。比較は scripts/05_compare_sheets.py ではなく下の GRADES を同じフレームに当てて見る）
素材（source/、変更しない）：S_sueru.mp4（据える-引き 848×480 24fps）、K_kansoku.mp4（観測-引き 1080p）、N_nozoki.mp4（覗き-寄り 1080p、別の場所）
早回し：tmix（隣り合うコマを平均＝シャッターを開けた時間のぶんだけ動きがぶれる。180°相当）→ setpts。
  コマを間引くだけだと人が飛び飛びに動く、tmix を長くすると人が溶ける（v3 で3案を並べて確認：5 コマ平均を採用）。
手持ちの揺れ：L08（S 158.3–166.0）は撮影者がカメラを置き直した直後で、画がゆっくり流れる → vidstab（2パス）で滑らかにしてから早回し。
"""
import subprocess, sys, json, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
GRADE = sys.argv[1] if len(sys.argv) > 1 else "Bplus"
OUT = ROOT / "intermediate" / GRADE; OUT.mkdir(parents=True, exist_ok=True)
SRC = {"S": ROOT / "source/S_sueru.mp4", "K": ROOT / "source/K_kansoku.mp4", "N": ROOT / "source/N_nozoki.mp4"}

# カット（計画 v3 §2。秒はコンタクトシートで確かめた値。計画の秒と違うものは理由を書く）
#   src・in・out：元の秒、crop：切り出し窓 (x, y, w, h)＝元の画素（16:9）、speed：早回しの倍率、blend：tmix のコマ数、stab：手持ちの揺れを滑らかに
# S は 480p なので拡大は 1.25 倍まで
SHOTS = {
    "L01": dict(src="N", a=0.10, b=0.95, crop=(0, 0, 1920, 1080), purpose="レベルだけ（斜め後ろから）。題の背景（静止して使う）"),
    "L02": dict(src="K", a=0.00, b=2.62, crop=(0, 0, 1920, 1080),
                purpose="B2：野帳を持って三脚へ歩いてくる人（計画 0.0–2.5。4小節の 2.53 秒を埋めるため 2.62 まで。歩いて三脚に手をかける所まで）"),
    "L03": dict(src="S", a=2.00, b=32.80, crop=(0, 0, 848, 477), speed=12.0, blend=5,
                purpose="B2：三脚を立て、脚を何度も合わせる（12 倍の早回し。計画 32.4 → 32.8：1小節を埋める）"),
    "L04": dict(src="S", a=51.00, b=53.60, crop=(70, 82, 707, 398),
                purpose="B2：レベルを箱から出して三脚に載せる（実時間、1.2 倍。計画 50.8–53.4 → 51.0–53.6：載せ終わる 53.4–53.5 を入れる）"),
    "L05": dict(src="K", a=3.80, b=7.65, crop=(0, 0, 1920, 1080),
                purpose="B4：かがんでのぞく人と遠くの標尺の人（切り出しなし、上に k_sight）"),
    "L06": dict(src="N", a=2.00, b=5.85, crop=(0, 0, 1920, 1080),
                purpose="B4：のぞく顔。最後の 1.2 秒で接眼レンズへ寄る（寄りは timeline の moves）"),
    "L07": dict(src="K", a=15.30, b=17.85, crop=(548, 0, 1372, 772), purpose="B6：立って野帳に書きとめる（腰から上 1.4 倍）。奥に標尺の人"),
    "L08": dict(src="S", a=158.30, b=166.00, crop=(0, 0, 848, 477), speed=3.0, blend=2, stab=True,
                purpose="B6：次の場所で野帳に書き、三脚の機械をのぞく（3 倍の早回し。計画 157.0–166.0・3.6 倍 → 158.3–166.0・3.0 倍："
                        "157.0–158.2 は撮影者がカメラに触れて画が跳ぶ。手持ちの流れは vidstab でならす）"),
    "L09": dict(src="S", a=168.00, b=170.60, crop=(0, 0, 848, 477),
                purpose="B7：標尺を持った人が手前から機械の横を通って先へ歩く（168.5–170.0 で機械の横を通る）"),
    "L10": dict(src="S", a=172.90, b=178.60, crop=(0, 0, 848, 477), purpose="B8：のぞく人と遠くの標尺の人＝締め（480p なので寄らない）"),
}
GRADES = {
    # B：v1.3 まで（基準点パートと同じ「落ち着いた暖かさ」）。曇天ではさらに沈む
    "B": "huesaturation=hue=0:saturation=-0.18:colors=g+y:strength=1,eq=saturation=0.95:contrast=1.03:brightness=-0.01,"
         "colorbalance=rs=0.02:bs=-0.02:rm=0.025:bm=-0.02:rh=0.01:bh=-0.015,curves=all='0/0.02 0.5/0.5 0.92/0.88 1/0.93'",
    # Bplus（v3 で採用）：コントラストと彩度を上げ、中間を少し暖かく。空は白く飛ばさずハイライトを丸める。肌はオレンジにしない
    "Bplus": "eq=contrast=1.10:saturation=1.30:gamma=1.03,colorbalance=rs=0.02:bs=-0.03:rm=0.035:bm=-0.035:rh=0.015:bh=-0.02,"
             "curves=all='0/0 0.2/0.17 0.5/0.52 0.8/0.84 0.95/0.93 1/0.96'",
    # D：くすんだ色だけを持ち上げる（vibrance）＋色温度を暖かく。色は一番にぎやかだが、顔とコーンがオレンジに寄る
    "D": "vibrance=intensity=0.45,colortemperature=temperature=5600:mix=0.6,eq=contrast=1.08:gamma=1.05:saturation=1.08,"
         "curves=all='0/0 0.25/0.23 0.6/0.64 0.9/0.89 1/0.95'",
}
# 素材ごとの合わせ：S は 480p の拡大なので軽くシャープ。N は別の場所（生け垣の緑が強い・顔が暖かく出る）→ 緑と暖かさを少し戻す
SRC_ADJ = {
    "B": {"S": "unsharp=5:5:0.6:5:5:0.0,colorbalance=rm=0.02:bm=-0.02", "K": "colorbalance=rm=0.02:bm=-0.02",
          "N": "huesaturation=saturation=-0.08:colors=g+y:strength=1"},
    "Bplus": {"S": "unsharp=5:5:0.6:5:5:0.0", "K": "null",
              "N": "huesaturation=saturation=-0.08:colors=g+y:strength=1,colorbalance=rm=-0.01:bm=0.01"},
    "D": {"S": "unsharp=5:5:0.6:5:5:0.0", "K": "null", "N": "huesaturation=saturation=-0.08:colors=g+y:strength=1"},
}[GRADE]
POST = "deband=1thr=0.015:2thr=0.015:3thr=0.015:range=16:blur=1,noise=c0s=3:c0f=t+u"

def run(cmd):
    subprocess.run(cmd, check=True)

FF = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
meta = {}
for shot, d in SHOTS.items():
    src, a, b, (x, y, w, h) = d["src"], d["a"], d["b"], d["crop"]
    sp, blend = d.get("speed", 1.0), d.get("blend", 0)
    pre = []
    if d.get("stab"):
        trf = OUT / f"{shot}.trf"
        run(FF + ["-ss", f"{a:.4f}", "-to", f"{b:.4f}", "-i", str(SRC[src]), "-an",
                  "-vf", f"vidstabdetect=shakiness=8:accuracy=15:result={trf}", "-f", "null", "-"])
        pre.append(f"vidstabtransform=input={trf}:smoothing=60:optzoom=1:interpol=bicubic")
    if blend > 1: pre.append(f"tmix=frames={blend}")
    if sp != 1.0: pre.append(f"setpts=PTS/{sp}")
    vf = ",".join(pre + [f"crop={w}:{h}:{x}:{y}", "scale=1920:1080:flags=lanczos", GRADES[GRADE], SRC_ADJ[src], POST, "format=yuv420p"])
    out = OUT / f"{shot}.mp4"
    run(FF + ["-ss", f"{a:.4f}", "-to", f"{b:.4f}", "-i", str(SRC[src]),
              "-an", "-vf", vf, "-r", "30000/1001", "-c:v", "libx264", "-preset", "slow", "-crf", "12", "-g", "15",
              "-pix_fmt", "yuv420p", "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", str(out)])
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(out)],
                               capture_output=True, text=True).stdout)
    meta[shot] = {"source": src, "src_in": a, "src_out": b, "speed": sp, "dur": round(dur - 0.04, 4), "crop": [x, y, w, h],
                  "scale": round(1920 / w, 3), "purpose": d["purpose"]}
    print(shot, meta[shot])

# 静止用フレーム（秒は元動画の時刻。早回しのカットには使わない）
# L_look_end：L06 の最後のコマを、接眼レンズへの寄りの終わり（LOOK_SCALE 倍、中心 LOOK_EYE）で切り出したもの＝d2_scope の最初のコマ
LOOK_EYE, LOOK_SCALE = (960, 548), 1.5      # 接眼レンズと目が合う所（N 5.8 秒のコマで確かめた）。20_plan_timeline.py も同じ値を読む
STILLS = {"L01_still": ("L01", 0.30, None), "L10_last": ("L10", 178.45, None),
          "L05_first": ("L05", 3.80, None), "L10_first": ("L10", 172.90, None),   # 実写の上の図の座標合わせ用（グラフィック担当）
          "L_look_end": ("L06", 5.76, LOOK_SCALE)}   # 5.76＝本編で L06 の最後に見えるコマ（cut(12) の 1 コマ前）
for name, (shot, t, zoom) in STILLS.items():
    rel = (t - meta[shot]["src_in"]) / meta[shot]["speed"]
    vf = []
    if zoom:   # 中心 (ex, ey) で zoom 倍した画＝左上 (ex(1−1/z), ey(1−1/z)) から 1920/z × 1080/z を切り出して拡大
        ex, ey = LOOK_EYE; cw, ch = round(1920 / zoom), round(1080 / zoom)
        vf = ["-vf", f"crop={cw}:{ch}:{round(ex * (1 - 1 / zoom))}:{round(ey * (1 - 1 / zoom))},scale=1920:1080:flags=lanczos"]
    run(FF + ["-ss", f"{rel:.4f}", "-i", str(OUT / f"{shot}.mp4"), "-frames:v", "1"] + vf + [str(OUT / f"{name}.png")])
    meta[name] = {"shot": shot, "src_time": t, "rel_time": round(rel, 4), "zoom": zoom}
meta["look"] = {"eye": list(LOOK_EYE), "scale": LOOK_SCALE}
(OUT / "meta.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False))
