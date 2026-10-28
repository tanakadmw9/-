"""仮ナレーション生成（ローカルの pyopenjtalk-plus / 同梱の HTS音声 "Mei"（名古屋工業大学、CC BY 3.0・クレジット要））。
comp/narration.json → audio/vo_temp/<id>.wav（48kHz mono）と audio/vo_temp/vo_timing.json。
キーワードの発話開始は「キーワード直前までの文」を単独合成した長さで近似する（±0.1秒程度）。
"""
import json, sys, pathlib, re
import numpy as np, pyopenjtalk, wave

ROOT = pathlib.Path(__file__).resolve().parent.parent
SPEED = float(sys.argv[1]) if len(sys.argv) > 1 else 0.78
nar = json.loads((ROOT / "comp/narration.json").read_text())
out = ROOT / "audio/vo_temp"; out.mkdir(parents=True, exist_ok=True)

def clean(t):  # 合成用に記号を落とす（読みは変えない）
    return re.sub(r"[「」“”]", "", t)

def synth(t):
    x, sr = pyopenjtalk.tts(clean(t), speed=SPEED)
    return x, sr

def trim(x, sr, thr=200):
    idx = np.where(np.abs(x) > thr)[0]
    if len(idx) == 0: return x, 0.0
    a = max(idx[0] - int(0.01 * sr), 0); b = min(idx[-1] + int(0.03 * sr), len(x))
    return x[a:b], a / sr

timing = {"speed": SPEED, "engine": "pyopenjtalk-plus (HTS voice Mei, CC BY 3.0)", "lines": {}}
for ln in nar["lines"]:
    x, sr = synth(ln["text"]); x, lead = trim(x, sr)
    x = np.clip(x / max(1, np.abs(x).max()) * 0.89 * 32767, -32767, 32767).astype(np.int16)
    with wave.open(str(out / f"{ln['id']}.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(x.tobytes())
    kws = {}
    for k in ln["keywords"]:
        pos = clean(ln["text"]).find(clean(k))
        if pos <= 0: kws[k] = 0.0; continue
        px, _ = synth(clean(ln["text"])[:pos]); px, plead = trim(px, sr)
        kws[k] = round(len(px) / sr + 0.05, 2)
    timing["lines"][ln["id"]] = {"text": ln["text"], "chars": len(clean(ln["text"])),
                                 "dur": round(len(x) / sr, 2), "keywords": kws}
    print(ln["id"], timing["lines"][ln["id"]]["dur"], kws)
(out / "vo_timing.json").write_text(json.dumps(timing, ensure_ascii=False, indent=1))
tot = sum(v["dur"] for v in timing["lines"].values()); chars = sum(v["chars"] for v in timing["lines"].values())
print(f"total speech {tot:.1f}s, {chars} chars, {chars/tot*60:.0f} chars/min")
