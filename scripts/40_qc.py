"""書き出しの自動チェック（docs/07 §1 のうち自動化できるもの）→ qc/<版>/report.md と目視用シート。

  python3 scripts/40_qc.py renders/review/v5.1.mp4 v5.1 [--no-hf]

  --no-hf  `npx hyperframes check comp`（headless Chrome を使う）を飛ばす

出力（qc/<版>/）
  report.md               合否表（先頭）＋各項目の詳細
  contact_0p5s_<k>of<n>.jpg  0.5秒おきのコンタクトシート（タイムコード焼き込み、8列×7行）
  telop_<id>.jpg          テロップごとの「出た直後／中間／消える直前」3コマ
  caption_hits/*.jpg      焼き込みテロップ（青い光沢カプセル）検出の切り抜き（検出があれば）
  levels.png              ステムの短時間ラウドネスの推移（audio/mix/ がある場合）

焼き込みテロップ検出（4fps、全画面）：
  HSV（OpenCV：H 0–180）で H 100–125、S ≥ 150、V ≥ 170 の画素の連結成分のうち、面積 ≥ 3000px かつ
  成分内の S の中央値 ≥ 190 のもの。元素材 source/input.mp4 で調整：テロップは S 中央値 ≈ 240・V ≈ 250、
  実写の紺のTS（S09）は S ≈ 124・V ≈ 157、空・作業着・紺の図解色（#1F3A5F, V=95）は条件外。
"""
import sys, json, re, subprocess, pathlib, argparse
import numpy as np
import cv2

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib_audio import SR, short_term, vo_bgm_diff

ROOT = pathlib.Path(__file__).resolve().parent.parent
T = json.loads((ROOT / "comp/timeline.json").read_text())

CAP_H, CAP_S, CAP_V, CAP_AREA, CAP_SMED = (100, 125), 150, 170, 3000, 190


# ---------------------------------------------------------------- helpers
def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def tc(t):
    m, s = divmod(t, 60)
    return f"{int(m):02d}:{s:05.2f}"


def where(t):
    """時刻 t が入る場面／ショット（図解・エンドカード・タイトル・実写ショット・静止画）。"""
    out = []
    for s in T["scenes"]:
        if s["start"] <= t < s["start"] + s["dur"]:
            out.append(s["id"] + ("(overlay)" if s.get("overlay") else ""))
    for s in T.get("stills", []):
        if s["start"] <= t < s["start"] + s["dur"]: out.append("still:" + s["id"])
    for s in T["shots"]:
        if s["start"] <= t < s["start"] + s["dur"]: out.append("shot:" + s["shot"])
    return out or ["(timeline 外)"]


def is_diagram_hold(t):
    return any(s["start"] <= t < s["start"] + s["dur"] and not s.get("overlay") for s in T["scenes"])


def frames(path, fps=None, w=None, h=None, gray=False, at=None):
    """ffmpeg で復号した BGR（または gray）フレームを順に返す。at を与えるとその時刻のフレームだけ。"""
    if at is not None:
        for t in at:
            vf = f"scale={w}:{h}" if w else "null"
            r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", str(path), "-frames:v", "1",
                                "-vf", vf, "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True)
            W, H = (w, h) if w else probe_wh(path)
            buf = r.stdout[:W * H * 3]
            yield t, (np.frombuffer(buf, np.uint8).reshape(H, W, 3) if len(buf) == W * H * 3 else None)
        return
    W, H = (w, h) if w else probe_wh(path)
    vf = []
    if fps: vf.append(f"fps={fps}")
    if w: vf.append(f"scale={w}:{h}")
    pf, ch = ("gray", 1) if gray else ("bgr24", 3)
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(path), "-vf", ",".join(vf) or "null",
                          "-f", "rawvideo", "-pix_fmt", pf, "-"], stdout=subprocess.PIPE)
    n = W * H * ch; i = 0
    rate = fps or probe_fps(path)
    while True:
        buf = p.stdout.read(n)
        if len(buf) < n: break
        yield i / rate, np.frombuffer(buf, np.uint8).reshape(H, W, ch) if ch == 3 else np.frombuffer(buf, np.uint8).reshape(H, W)
        i += 1
    p.wait()


_probe = {}
def probe(path):
    if path not in _probe:
        _probe[path] = json.loads(run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)]).stdout)
    return _probe[path]


def probe_wh(path):
    v = [s for s in probe(path)["streams"] if s["codec_type"] == "video"][0]
    return int(v["width"]), int(v["height"])


def probe_fps(path):
    v = [s for s in probe(path)["streams"] if s["codec_type"] == "video"][0]
    a, b = v["r_frame_rate"].split("/"); return int(a) / int(b)


def detect_intervals(path, vf, key_start, key_end, key_dur):
    err = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-vf", vf, "-an", "-f", "null", "-"]).stderr
    starts = [float(x) for x in re.findall(key_start + r"\s*:?\s*(-?[\d.]+)", err)]
    ends = [float(x) for x in re.findall(key_end + r"\s*:?\s*(-?[\d.]+)", err)]
    out = []
    for i, s in enumerate(starts):
        e = ends[i] if i < len(ends) else float(probe(path)["format"]["duration"])
        out.append((s, e))
    return out


# ---------------------------------------------------------------- checks
def check_spec(path):
    P = probe(path); v = [s for s in P["streams"] if s["codec_type"] == "video"]; a = [s for s in P["streams"] if s["codec_type"] == "audio"]
    rows = []
    def add(name, got, ok, want):
        rows.append((name, got, want, ok))
    if v:
        v = v[0]
        add("解像度", f"{v['width']}×{v['height']}", (v["width"], v["height"]) == (1920, 1080), "1920×1080")
        add("フレームレート", v["r_frame_rate"], v["r_frame_rate"] == "30000/1001", "30000/1001")
        add("映像コーデック", v["codec_name"], v["codec_name"] == "h264", "h264")
        add("画素形式", v.get("pix_fmt"), v.get("pix_fmt") == "yuv420p", "yuv420p")
    else:
        add("映像", "なし", False, "あり")
    if a:
        a = a[0]
        add("音声コーデック", a["codec_name"], a["codec_name"] == "aac", "aac")
        add("サンプリング", a["sample_rate"], a["sample_rate"] == "48000", "48000")
        add("チャンネル", str(a["channels"]), a["channels"] == 2, "2")
    else:
        add("音声", "なし", False, "あり")
    dur = float(P["format"]["duration"])
    add("尺", f"{dur:.3f}s", abs(dur - T["duration"]) <= 0.1, f"{T['duration']:.3f}±0.1s")
    if v and a:
        vd = float(v.get("duration", dur)); ad = float(a.get("duration", dur))
        add("映像と音の長さ", f"V {vd:.3f}s / A {ad:.3f}s", abs(vd - ad) <= 0.1, "差 ≤0.1s")
    return rows


def check_black(path):
    iv = detect_intervals(path, "scale=480:-2,blackdetect=d=0.1:pic_th=0.98:pix_th=0.10", "black_start", "black_end", "black_duration")
    end = [s for s in T["scenes"] if s["id"] == "endcard"]
    fade_from = end[0]["start"] + end[0]["cues"].get("fade", 1e9) if end else 1e9
    rows = []
    for s, e in iv:
        intended = s >= fade_from - 0.1 and e >= T["duration"] - 0.2
        rows.append((s, e, intended, where(s)))
    return rows


def check_freeze(path):
    iv = detect_intervals(path, "scale=480:-2,freezedetect=n=-60dB:d=0.5", "freeze_start", "freeze_end", "freeze_duration")
    intended = [(a - 0.2, b + 0.2, n) for a, b, n in T.get("intended_freezes", [])]
    rows = []
    for s, e in iv:
        ok = next((n for a, b, n in intended if s >= a and e <= b), None)
        mid = (s + e) / 2
        if ok: kind = f"意図どおり（{ok}）"
        elif is_diagram_hold(mid): kind = "図解・エンドカードの静止（要目視：動きが止まって見えないか）"
        else: kind = "**意図しない静止の疑い（実写）**"
        rows.append((s, e, kind, where(mid)))
    return rows


def caption_blobs(fr):
    hsv = cv2.cvtColor(fr, cv2.COLOR_BGR2HSV)
    m = cv2.inRange(hsv, (CAP_H[0], CAP_S, CAP_V), (CAP_H[1], 255, 255))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    out = []
    for i in range(1, n):
        if st[i, 4] < CAP_AREA: continue
        x, y, w, h, a = st[i]
        smed = float(np.median(hsv[y:y + h, x:x + w, 1][lab[y:y + h, x:x + w] == i]))
        if smed >= CAP_SMED: out.append((int(x), int(y), int(w), int(h), int(a), smed))
    return out


def check_captions(path, outdir):
    hits = []; d = outdir / "caption_hits"
    prev = False
    for t, fr in frames(path, fps=4):
        b = caption_blobs(fr)
        if b:
            hits.append((t, b))
            if not prev:  # 連続した検出の最初の1枚だけ切り抜きを保存
                d.mkdir(exist_ok=True)
                x0 = max(min(x for x, *_ in b) - 40, 0); y0 = max(min(y for _, y, *_ in b) - 40, 0)
                x1 = min(max(x + w for x, _, w, *_ in b) + 40, fr.shape[1]); y1 = min(max(y + h for _, y, _, h, *_ in b) + 40, fr.shape[0])
                crop = fr[y0:y1, x0:x1].copy()
                cv2.imwrite(str(d / f"hit_{t:07.2f}s.jpg"), crop, [cv2.IMWRITE_JPEG_QUALITY, 85])
        prev = bool(b)
    return hits


def check_flash(path, thr=25.0):
    """隣接フレームの平均輝度（0–255）の変化が thr（約10%）以上を「遷移」とし、向きが逆の遷移2つで1回の明滅と数える。"""
    ys = [];
    for t, fr in frames(path, w=160, h=90, gray=True):
        ys.append(float(fr.mean()))
    ys = np.array(ys); fps = probe_fps(path)
    dy = np.diff(ys); ev = np.where(np.abs(dy) >= thr)[0]
    sgn = np.sign(dy[ev]); times = (ev + 1) / fps
    worst, worst_t = 0, None
    for i, t0 in enumerate(times):
        m = (times >= t0) & (times < t0 + 1.0)
        s = sgn[m]; flips = int(np.sum(s[1:] != s[:-1])) if len(s) > 1 else 0
        flashes = (flips + 1) // 2 if len(s) > 1 else 0
        if flashes > worst: worst, worst_t = flashes, t0
    # 1コマだけの黒（blackdetect は 0.1秒未満を拾わない）：平均輝度 < 8 のフレーム。最後のフェードは除く
    end = [s for s in T["scenes"] if s["id"] == "endcard"]
    fade_from = end[0]["start"] + end[0]["cues"].get("fade", 1e9) if end else 1e9
    dark = [round(i / fps, 3) for i, y in enumerate(ys) if y < 8 and i / fps < fade_from - 0.05]
    return {"transitions": [(round(float(t), 2), round(float(dy[e]), 1)) for t, e in zip(times, ev)],
            "max_flashes_per_s": worst, "at": worst_t, "dark_frames": dark}


def check_telops():
    rows = []
    for tp in T.get("telops", []):
        text = tp["text"]; chars = len(re.sub(r"\s", "", text))
        need = max(chars / 4 + 1.0, 1.5)
        rows.append((tp["id"], text, chars, tp["dur"], round(need, 2), tp["dur"] >= need - 1e-6))
    return rows


def check_loudness(path):
    err = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-map", "0:a:0", "-af", "ebur128=peak=true", "-f", "null", "-"]).stderr
    tail = err[err.rfind("Summary:"):]
    try:
        I = float(re.search(r"I:\s+(-?[\d.]+) LUFS", tail).group(1))
        tp = float(re.search(r"Peak:\s+(-?[\d.inf]+) dBFS", tail).group(1))
        lra = float(re.search(r"LRA:\s+(-?[\d.]+) LU", tail).group(1))
    except AttributeError:
        return None
    return {"I": I, "TP": tp, "LRA": lra}


def check_vo_bgm():
    import soundfile as sf
    pv, pb = ROOT / "audio/mix/vo.wav", ROOT / "audio/mix/bgm.wav"
    if not (pv.exists() and pb.exists()): return None
    vo, _ = sf.read(str(pv), always_2d=True); bgm, _ = sf.read(str(pb), always_2d=True)
    lines = [(v["id"], v["start"], v["start"] + v["dur"]) for v in T["vo"]]
    return vo_bgm_diff(vo, bgm, lines)


def check_clicks():
    """mix.wav の波形の不連続（プチノイズ）候補：2階差分が局所RMSの12倍超かつ十分大きい所。SE の位置は除外表示。"""
    import soundfile as sf
    p = ROOT / "audio/mix/mix.wav"
    if not p.exists(): return None
    x, sr = sf.read(str(p), always_2d=True); x = x.mean(1)
    d2 = np.abs(np.diff(x, 2))
    w = int(0.05 * sr)
    rms = np.sqrt(np.convolve(d2 ** 2, np.ones(w) / w, mode="same")) + 1e-9
    idx = np.where((d2 > 12 * rms) & (d2 > 0.01))[0]
    ts = []
    for i in idx:
        t = i / sr
        if not ts or t - ts[-1] > 0.05: ts.append(t)
    se_t = [e["start"] for e in T["se"]]
    return [(round(t, 3), any(-0.01 <= t - s <= 0.3 for s in se_t)) for t in ts]


def count_kanshu():
    files = [ROOT / "comp/narration.json", ROOT / "docs/03_direction_draft.md", ROOT / "docs/08_build_spec.md"]
    files += sorted((ROOT / "comp/compositions").glob("*.html")) if (ROOT / "comp/compositions").exists() else []
    out = []
    for f in files:
        if f.exists():
            n = f.read_text(encoding="utf-8").count("【要監修】")
            out.append((str(f.relative_to(ROOT)), n))
    return out


def check_credits():
    led = (ROOT / "docs/credits_and_licenses.md").read_text(encoding="utf-8")
    classes = []
    def need(name, present, keys):
        if present: classes.append((name, keys, all(k in led for k in keys)))
    need("元映像", (ROOT / "source/input.mp4").exists(), ["映像"])
    need("フォント BIZ UDPゴシック／UDゴシック", any((ROOT / "comp/assets/fonts").glob("biz-ud*")), ["BIZ UDPゴシック", "BIZ UDゴシック"])
    need("GSAP", (ROOT / "comp/assets/vendor/gsap.min.js").exists(), ["GSAP"])
    need("HyperFrames", (ROOT / "node_modules/hyperframes").exists(), ["HyperFrames"])
    need("仮ナレ（音声合成）", any((ROOT / "audio/vo_temp").glob("*.wav")), ["pyopenjtalk", "Mei"])
    need("本ナレ（社員の声）", any((ROOT / "audio/vo_final").glob("*.wav")), ["本ナレ"])
    need("効果音", any((ROOT / "audio/se").glob("*.wav")), ["効果音"])
    need("環境音", (ROOT / "audio/amb/amb.wav").exists(), ["環境音"])
    need("仮BGM", (ROOT / "audio/bgm/temp_bgm.wav").exists() and not (ROOT / "audio/bgm/bgm.wav").exists(), ["仮BGM"])
    need("BGM（選曲）", (ROOT / "audio/bgm/bgm.wav").exists(), ["bgm.wav"])
    return classes


def hf_check():
    try:
        r = run(["npx", "--no-install", "hyperframes", "check", "comp"], cwd=ROOT, timeout=600)
        return r.returncode, (r.stdout + r.stderr).strip().splitlines()[-25:]
    except Exception as e:  # noqa
        return None, [f"実行できず: {e}"]


# ---------------------------------------------------------------- sheets
def contact_sheets(path, outdir, step=0.5, tw=320, th=180, cols=8, rows=7):
    dur = float(probe(path)["format"]["duration"])
    tiles = []
    for t, fr in frames(path, fps=1 / step, w=tw, h=th):
        if t > dur: break
        fr = fr.copy()
        cv2.rectangle(fr, (0, th - 24), (112, th), (0, 0, 0), -1)
        cv2.putText(fr, tc(t), (5, th - 7), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
        tiles.append(fr)
    per = cols * rows; n = (len(tiles) + per - 1) // per; paths = []
    for k in range(n):
        chunk = tiles[k * per:(k + 1) * per]
        sheet = np.full((rows * (th + 4) + 4, cols * (tw + 4) + 4, 3), 40, np.uint8)
        for i, im in enumerate(chunk):
            r, c = divmod(i, cols)
            sheet[4 + r * (th + 4):4 + r * (th + 4) + th, 4 + c * (tw + 4):4 + c * (tw + 4) + tw] = im
        used_rows = (len(chunk) + cols - 1) // cols
        sheet = sheet[:4 + used_rows * (th + 4)]
        p = outdir / f"contact_0p5s_{k + 1}of{n}.jpg"
        cv2.imwrite(str(p), sheet, [cv2.IMWRITE_JPEG_QUALITY, 82]); paths.append(p.name)
    return paths


def telop_strips(path, outdir, tw=640, th=360):
    out = []
    for tp in T.get("telops", []):
        s, d = tp["start"], tp["dur"]
        ts = [s + min(0.6, d * 0.25), s + d / 2, s + d - min(0.4, d * 0.15)]
        ims = []
        for (t, fr), lab in zip(frames(path, w=tw, h=th, at=ts), ["just in", "middle", "before out"]):
            fr = np.zeros((th, tw, 3), np.uint8) if fr is None else fr.copy()
            cv2.rectangle(fr, (0, 0), (250, 26), (0, 0, 0), -1)
            cv2.putText(fr, f"{tc(t)} {lab}", (6, 19), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
            ims.append(fr)
        p = outdir / f"telop_{tp['id']}.jpg"
        cv2.imwrite(str(p), np.hstack(ims), [cv2.IMWRITE_JPEG_QUALITY, 85]); out.append(p.name)
    return out


def levels_plot(outdir, W=1600, H=420):
    import soundfile as sf
    cols = {"vo": (60, 60, 230), "bgm": (200, 120, 30), "amb": (60, 170, 60), "se": (0, 160, 230)}
    if not (ROOT / "audio/mix/vo.wav").exists(): return None
    img = np.full((H, W, 3), 255, np.uint8); dur = T["duration"]
    X = lambda t: int(50 + (W - 70) * t / dur); Y = lambda l: int(20 + (H - 60) * (-(l + 10)) / 60)  # -10..-70 LUFS
    for v in T["vo"]: cv2.rectangle(img, (X(v["start"]), 20), (X(v["start"] + v["dur"]), H - 40), (238, 238, 238), -1)
    ps = T["bgm"]["pause"]; cv2.rectangle(img, (X(ps["start"]), 20), (X(ps["end"]), H - 40), (220, 220, 255), -1)
    for l in range(-10, -71, -10):
        cv2.line(img, (50, Y(l)), (W - 20, Y(l)), (210, 210, 210), 1)
        cv2.putText(img, str(l), (8, Y(l) + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (90, 90, 90), 1)
    for s in range(0, int(dur) + 1, 5):
        cv2.putText(img, f"{s}", (X(s) - 6, H - 22), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (90, 90, 90), 1)
    for k, c in cols.items():
        x, _ = sf.read(str(ROOT / f"audio/mix/{k}.wav"), always_2d=True)
        t, l = short_term(x)
        pts = np.array([[X(a), Y(max(b, -70))] for a, b in zip(t, l)], np.int32)
        cv2.polylines(img, [pts], False, c, 2, cv2.LINE_AA)
    for i, (k, c) in enumerate(cols.items()):
        cv2.putText(img, k, (60 + i * 70, H - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.5, c, 2)
    cv2.putText(img, "short-term LUFS (3s). grey = VO lines, pink = bgm.pause", (360, H - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (90, 90, 90), 1)
    cv2.imwrite(str(outdir / "levels.png"), img); return "levels.png"


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("render"); ap.add_argument("version"); ap.add_argument("--no-hf", action="store_true")
    a = ap.parse_args()
    path = pathlib.Path(a.render).resolve(); outdir = ROOT / "qc" / a.version; outdir.mkdir(parents=True, exist_ok=True)
    final = a.version.startswith("v6")
    print("spec…"); spec = check_spec(path)
    print("blackdetect…"); black = check_black(path)
    print("freezedetect…"); frz = check_freeze(path)
    print("captions…"); caps = check_captions(path, outdir)
    print("flash…"); fl = check_flash(path)
    tel = check_telops()
    print("loudness…"); loud = check_loudness(path)
    vb = check_vo_bgm(); clicks = check_clicks()
    kan = count_kanshu(); cred = check_credits()
    hf = (None, ["--no-hf で省略"]) if a.no_hf else (print("hyperframes check…") or hf_check())
    print("sheets…"); sheets = contact_sheets(path, outdir); strips = telop_strips(path, outdir); lv = levels_plot(outdir)

    R = []  # (項目, 判定, 要約)
    R.append(("仕様（ffprobe）", all(r[3] for r in spec), "; ".join(f"{r[0]} {r[1]}" for r in spec if not r[3]) or "すべて一致"))
    bad_black = [b for b in black if not b[2]]
    R.append(("黒コマ（blackdetect）", not bad_black, f"意図外 {len(bad_black)} 件／全 {len(black)} 件"))
    un_live = [f for f in frz if f[2].startswith("**")]; un_diag = [f for f in frz if f[2].startswith("図解")]
    R.append(("意図しない静止（freezedetect）", "WARN" if (un_diag and not un_live) else not un_live,
              f"実写で意図外 {len(un_live)} 件、図解の静止 {len(un_diag)} 件（目視）、意図どおり {len(frz) - len(un_live) - len(un_diag)} 件"))
    R.append(("焼き込みテロップの漏れ（4fps）", not caps, f"検出 {len(caps)} フレーム" + (f"（{tc(caps[0][0])}〜{tc(caps[-1][0])}）" if caps else "")))
    R.append(("1コマの黒（平均輝度<8）", not fl["dark_frames"], f"{len(fl['dark_frames'])} コマ" + (f"（{', '.join(tc(t) for t in fl['dark_frames'][:5])}）" if fl["dark_frames"] else "")))
    R.append(("点滅（>3回/秒）", fl["max_flashes_per_s"] <= 3, f"最大 {fl['max_flashes_per_s']} 回/秒" + (f" @ {tc(fl['at'])}" if fl["at"] is not None else "")))
    R.append(("テロップ表示時間", all(r[5] for r in tel), f"{sum(r[5] for r in tel)}/{len(tel)} 合格"))
    hf_ok = None if hf[0] is None else hf[0] == 0
    R.append(("hyperframes check（はみ出し・コントラスト）", "N/A" if hf_ok is None else hf_ok, "省略／実行不可" if hf_ok is None else f"exit {hf[0]}"))
    if loud:
        R.append(("ラウドネス（ebur128）", abs(loud["I"] + 24) <= 1 and loud["TP"] <= -2.0, f"I {loud['I']} LUFS, TP {loud['TP']} dBTP"))
    else:
        R.append(("ラウドネス（ebur128）", False, "音声なし／測定不可"))
    if vb:
        per, st = vb; vals = [v for v in per.values() if v is not None]
        ok = bool(vals) and min(vals) >= 15 and (st is None or st["p5"] >= 15)
        R.append(("ナレとBGMの差（ステム）", ok, f"行ごと最小 {min(vals) if vals else '—'} dB、短時間窓 p5 {st['p5'] if st else '—'} dB"
                  + "（audio/mix のステム。レンダーの音声が同じ mix か確認すること）"))
    else:
        R.append(("ナレとBGMの差（ステム）", "N/A", "audio/mix/ のステムなし"))
    if clicks is not None:
        nonse = [c for c in clicks if not c[1]]
        R.append(("プチノイズ（mix.wav の不連続）", not nonse, f"SE以外の候補 {len(nonse)} 件（SE位置 {len(clicks) - len(nonse)} 件は除外）"))
    nk = sum(n for _, n in kan)
    R.append(("【要監修】", (nk == 0) if final else ("WARN" if nk else True), f"合計 {nk}（最終版でゼロ）"))
    miss = [c[0] for c in cred if not c[2]]
    R.append(("素材台帳", not miss, "漏れなし" if not miss else "未記載: " + "、".join(miss)))

    def mark(v):
        return {True: "✅ PASS", False: "❌ FAIL", "WARN": "⚠️ WARN", "N/A": "— N/A"}[v]
    overall = all(v is True or v in ("WARN", "N/A") for _, v, _ in R)
    L = [f"# QC report {a.version}", "", f"- 対象: `{path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}`",
         f"- 計画尺: {T['duration']} s（comp/timeline.json）", f"- 総合: **{'PASS' if overall else 'FAIL'}**", "",
         "| 項目 | 判定 | 要約 |", "|---|---|---|"]
    L += [f"| {n} | {mark(v)} | {s} |" for n, v, s in R]
    L += ["", "## 1. 仕様（ffprobe）", "", "| 項目 | 実測 | 基準 | 判定 |", "|---|---|---|---|"]
    L += [f"| {n} | {g} | {w} | {'OK' if ok else 'NG'} |" for n, g, w, ok in spec]
    L += ["", "## 2. 黒コマ（blackdetect d≥0.1s, pix_th 0.10）", ""]
    L += [f"- {tc(s)}–{tc(e)}（{e - s:.2f}s）{'意図（エンドカードのフェード）' if ok else '**意図外**'} — {', '.join(w)}" for s, e, ok, w in black] or ["- なし"]
    L += ["", "## 3. 静止（freezedetect n=-60dB, d≥0.5s）", "",
          "timeline.intended_freezes: " + "; ".join(f"{tc(a_)}–{tc(b_)} {n}" for a_, b_, n in T.get("intended_freezes", [])), "",
          "図解（ポスター風の静止を含む）やエンドカードは、動きの合間に正当に静止しうる。実写区間の意図外の静止は不具合の疑い。", ""]
    L += [f"- {tc(s)}–{tc(e)}（{e - s:.2f}s）{k} — {', '.join(w)}" for s, e, k, w in frz] or ["- なし"]
    L += ["", "## 4. 焼き込みテロップの漏れ", "",
          f"条件：4fps・全画面、HSV H {CAP_H[0]}–{CAP_H[1]}, S≥{CAP_S}, V≥{CAP_V}、連結面積 ≥{CAP_AREA}px、成分内 S 中央値 ≥{CAP_SMED}。"
          "元素材でテロップは S≈240/V≈250、実写の紺TSは S≈124/V≈157（除外）。", ""]
    if caps:
        L += [f"検出 {len(caps)} フレーム。切り抜き: `caption_hits/`（連続検出の先頭のみ保存）", "", "| 時刻 | 場所 | 成分（x,y,w,h,面積,S中央値） |", "|---|---|---|"]
        shown = caps if len(caps) <= 40 else caps[:20] + caps[-20:]
        L += [f"| {tc(t)} | {', '.join(where(t))} | " + "; ".join(f"{x},{y},{w},{h},{ar},{sm:.0f}" for x, y, w, h, ar, sm in b) + " |" for t, b in shown]
        if len(caps) > 40: L.append(f"（中略：全 {len(caps)} フレーム）")
    else:
        L.append("検出なし")
    L += ["", "## 5. 点滅", "", f"平均輝度（0–255）の隣接フレーム変化 ≥25 を遷移とし、向きが逆の遷移2つで1回。最大 {fl['max_flashes_per_s']} 回/秒。",
          f"大きな遷移 {len(fl['transitions'])} 件（カット・フェード含む）: " + ", ".join(f"{tc(t)}({d:+})" for t, d in fl["transitions"][:40])]
    L += ["", "## 6. テロップ（表示時間 ≥ 文字数÷4＋1.0秒、かつ ≥1.5秒）", "", "| id | 文 | 文字数 | 表示 | 必要 | 判定 |", "|---|---|---|---|---|---|"]
    L += [f"| {i} | {t} | {c} | {d:.2f}s | {n}s | {'OK' if ok else 'NG'} |" for i, t, c, d, n, ok in tel]
    L += ["", "3コマ（出た直後／中間／消える直前）: " + ", ".join(f"`{s}`" for s in strips),
          "", "タイトルセーフ・はみ出し・コントラストは `npx hyperframes check comp`：", "", "```", *hf[1], "```"]
    L += ["", "## 7. ラウドネス（ffmpeg ebur128=peak=true）", ""]
    L += [f"- 統合 {loud['I']} LUFS（基準 −24±1）、True Peak {loud['TP']} dBTP（基準 ≤−2）、LRA {loud['LRA']} LU"] if loud else ["- 測定不可"]
    L += ["", "## 8. ナレとBGMの差（audio/mix のステム）", ""]
    if vb:
        per, st = vb
        L += ["行ごと：VO の統合ラウドネス − 同区間の BGM 平均ラウドネス（基準 ≥15 dB、設計 15〜18 dB 下）", "",
              "| 行 | 差 dB |", "|---|---|"] + [f"| {k} | {'BGMなし' if v is None else v} |" for k, v in per.items()]
        if st: L += ["", f"3秒短時間ラウドネス（窓がナレ1行に完全に入る {st['n_windows']} 点）：中央値 {st['median']} dB、p5 {st['p5']} dB、最小 {st['min']} dB"]
    else:
        L.append("ステムなし")
    if lv: L += ["", "ステムの推移: `levels.png`"]
    L += ["", "## 9. プチノイズ候補（audio/mix/mix.wav）", ""]
    if clicks is None: L.append("mix.wav なし")
    else: L += [f"- {tc(t)} {'(SE の位置：意図した打音)' if se else '**要確認**'}" for t, se in clicks] or ["- なし"]
    L += ["", "## 10. 【要監修】の数", ""] + [f"- `{f}`: {n}" for f, n in kan]
    L += ["", "## 11. 素材台帳（docs/credits_and_licenses.md）", ""] + [f"- {n}: {'記載あり' if ok else '**未記載**'}（確認語: {', '.join(k)}）" for n, k, ok in cred]
    L += ["", "## 12. 目視用シート", "", "- " + ", ".join(f"`{s}`" for s in sheets) + "（0.5秒おき、8列×7行、左下にタイムコード）",
          "", "## 自動化していない項目（人間・目視）", "",
          "- 言葉と絵の同期（キーワード発話時刻 vs 図解の動き ±0.3s）：vo_timing.json と scenes.cues の比較は別途",
          "- 音の聞こえ方（BGMの選曲・間・SEの質感・環境音の自然さ）は試写で耳で判断"]
    (outdir / "report.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(f"{mark(v):8s} {n}: {s}" for n, v, s in R))
    print(f"overall: {'PASS' if overall else 'FAIL'} -> {outdir / 'report.md'}")
    return 0 if overall else 1


if __name__ == "__main__":
    sys.exit(main())
