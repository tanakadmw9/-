"""仮ナレーション生成（VOICEVOX エンジン、ローカルの http://127.0.0.1:50021 ／ Docker 版 voicevox/voicevox_engine:cpu-latest）。
comp/narration.json → <out>/<id>.wav（48kHz mono）と <out>/vo_timing.json。
使い方: python3 scripts/11_tts_voicevox.py <style_id> [out_dir=audio/vo_temp] [speed=1.0] [intonation=1.0] [pause=1.6] [pitch=0]
  speed・intonation は文ごとの演出値に掛ける倍率、pitch は足す量、pause は読点の間の倍率。
narration.json の vv_kana（手で直した読み・アクセント）で合成し、vv_dir（文ごとの演出）を当てる：
  速さ・高さ・抑揚・音量、強調語（少し高く・少し長く）、語の前の間、語尾（soft＝下げて少し伸ばす／firm＝言い切る／cont＝下げずに次へ／soft_long）、
  文の中で少しずつ下がる自然な高さ（下降）、母音の長さのわずかなゆらぎ（固定シードで再現可能）。
キーワードの発話開始は、合成に使ったモーラ列の中でキーワードの読みを探し、その手前までのモーラ長の合計とする。
エンジンの起動: docker run -d --name vv -p 50021:50021 voicevox/voicevox_engine:cpu-latest
"""
import json, sys, pathlib, re, io, random, urllib.request, urllib.parse, wave
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
STYLE = int(sys.argv[1])
OUT = ROOT / (sys.argv[2] if len(sys.argv) > 2 else "audio/vo_temp")
A = sys.argv + [None] * 6
SPEED = float(A[3] or 1.0); INTON = float(A[4] or 1.0); PAUSE = float(A[5] or 1.6); PITCH = float(A[6] or 0)
API = "http://127.0.0.1:50021"
SR = 48000

def clean(t):  # 合成用に記号を落とす（読みは変えない）
    return re.sub(r"[「」“”]", "", t)

def post(path, params, body=None):
    url = f"{API}{path}?{urllib.parse.urlencode(params)}"
    data = json.dumps(body).encode() if body is not None else b""
    req = urllib.request.Request(url, data=data, method="POST", headers={"Content-Type": "application/json"})
    return urllib.request.urlopen(req, timeout=120).read()

def query(t, kana=None, d=None):
    d = d or {}
    q = json.loads(post("/audio_query", {"text": t, "speaker": STYLE}))
    if kana:
        q["accent_phrases"] = json.loads(post("/accent_phrases", {"text": kana, "speaker": STYLE, "is_kana": "true"}))
    q.update(speedScale=d.get("speed", 0.92) * SPEED, intonationScale=d.get("inton", 1.15) * INTON,
             pauseLengthScale=PAUSE, pitchScale=d.get("pitch", 0) + PITCH, volumeScale=d.get("volume", 1.0),
             prePhonemeLength=0.0, postPhonemeLength=0.0, outputSamplingRate=SR, outputStereo=False)
    return q

def kw_seq(k):  # キーワードのモーラ列
    return [t for t, _ in moras(query(clean(k), nar.get("vv_kw_kana", {}).get(k)))]

def find(txt, seq):
    for i in range(len(txt) - len(seq) + 1):
        if txt[i:i + len(seq)] == seq: return i
    raise SystemExit(f"not found in moras: {''.join(seq)}")

PAU = lambda L: {"text": "、", "consonant": None, "consonant_length": None, "vowel": "pau", "vowel_length": L, "pitch": 0.0}

def direct(q, d, rng):
    """文ごとの演出をモーラに当てる。"""
    aps = q["accent_phrases"]
    flat = [(i, m) for i, ap in enumerate(aps) for m in ap["moras"]]
    txt = [m["text"] for _, m in flat]
    # 文の中の自然な下降（最初の句から最後の句へ約 0.04 下げる。cont は下げ幅を半分に）
    fall = 0.02 if d.get("end") == "cont" else 0.04
    for i, m in flat:
        if m["pitch"] > 0: m["pitch"] -= fall * i / max(1, len(aps) - 1)
        m["vowel_length"] *= 1 + rng.uniform(-0.04, 0.04)
    # 強調語：少し高く、少し長く
    for k in d.get("emph", []):
        seq = kw_seq(k); a = find(txt, seq)
        for j in range(a, a + len(seq)):
            m = flat[j][1]
            if m["pitch"] > 0: m["pitch"] += 0.045
            m["vowel_length"] *= d.get("slow_kw", 1.08)
            if m.get("consonant_length"): m["consonant_length"] *= 1.05
    # 語の前の間（直前の句の後ろに置く。秒は pauseLengthScale で割り戻して指定どおりに）
    for k, sec in d.get("pause_before", {}).items():
        a = find(txt, kw_seq(k)); ai = flat[a][0]
        if ai == 0 or flat[a - 1][0] == ai: continue  # 句の途中なら置かない
        prev = aps[ai - 1]
        L = sec / q["pauseLengthScale"]
        if prev.get("pause_mora"): prev["pause_mora"]["vowel_length"] += L
        else: prev["pause_mora"] = PAU(L)
    # 語尾
    end = d.get("end", "soft")
    voiced = [m for _, m in flat if m["pitch"] > 0]
    last = flat[-1][1]
    if end in ("soft", "soft_long"):
        for m, dp in zip(voiced[-2:], (0.02, 0.05)): m["pitch"] -= dp
        voiced[-1]["vowel_length"] *= 1.35 if end == "soft_long" else 1.15
        if last["pitch"] == 0: last["vowel_length"] *= 1.3
    elif end == "cont":
        for m in voiced[-2:]: m["pitch"] += 0.03
        voiced[-1]["vowel_length"] *= 1.1
    elif end == "firm":
        voiced[-1]["pitch"] -= 0.02
    return q

def moras(q):  # [(読み, 開始秒)]。pause は PAUSE 倍、全体は速さで割る
    out, s = [], 0.0
    for ap in q["accent_phrases"]:
        for m in ap["moras"]:
            out.append((m["text"], s / q["speedScale"]))
            s += (m.get("consonant_length") or 0) + m["vowel_length"]
        if ap.get("pause_mora"): s += ap["pause_mora"]["vowel_length"] * q["pauseLengthScale"]
    return out

def kw_start(q, k):
    ms = moras(q)
    return ms[find([t for t, _ in ms], kw_seq(k))][1]

def synth(q):
    b = post("/synthesis", {"speaker": STYLE}, q)
    with wave.open(io.BytesIO(b)) as w:
        assert w.getframerate() == SR
        return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64)

def trim(x, thr=200):
    idx = np.where(np.abs(x) > thr)[0]
    if len(idx) == 0: return x
    return x[max(idx[0] - int(0.01 * SR), 0):min(idx[-1] + int(0.03 * SR), len(x))]

speakers = json.loads(urllib.request.urlopen(f"{API}/speakers").read())
who = next(f"{s['name']}（{st['name']}）" for s in speakers for st in s["styles"] if st["id"] == STYLE)
ver = json.loads(urllib.request.urlopen(f"{API}/version").read())
nar = json.loads((ROOT / "comp/narration.json").read_text())
OUT.mkdir(parents=True, exist_ok=True)
timing = {"speed_mul": SPEED, "engine": f"VOICEVOX engine {ver} / VOICEVOX:{who} style {STYLE}",
          "params": {"intonation": INTON, "pause": PAUSE, "pitch": PITCH}, "lines": {}}
for ln in nar["lines"]:
    t = clean(ln["text"])
    d = ln.get("vv_dir", {})
    q = direct(query(t, ln.get("vv_kana"), d), d, random.Random(ln["id"]))
    x = synth(q); lead = (np.where(np.abs(x) > 200)[0][:1] / SR).tolist(); x = trim(x)
    lead = max((lead[0] if lead else 0) - 0.01, 0)
    x = np.clip(x / max(1, np.abs(x).max()) * 0.89 * 32767, -32767, 32767).astype(np.int16)
    with wave.open(str(OUT / f"{ln['id']}.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(x.tobytes())
    kws = {}
    for k in ln["keywords"]:
        st = kw_start(q, k)
        kws[k] = 0.0 if st < 0.05 else round(st - lead + 0.03, 2)
    timing["lines"][ln["id"]] = {"text": ln["text"], "chars": len(clean(ln["text"])),
                                 "dur": round(len(x) / SR, 2), "keywords": kws}
    print(ln["id"], timing["lines"][ln["id"]]["dur"], kws)
(OUT / "vo_timing.json").write_text(json.dumps(timing, ensure_ascii=False, indent=1))
tot = sum(v["dur"] for v in timing["lines"].values()); chars = sum(v["chars"] for v in timing["lines"].values())
print(f"{who}: total speech {tot:.1f}s, {chars} chars, {chars/tot*60:.0f} chars/min")
