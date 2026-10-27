"""チームB：書き出しの自動チェック（docs/07 §1 のうち自動化できるもの）→ qc/<版>/report.md と目視用シート。
使い方: python3 teamB/scripts/40_qc.py <mp4> <版>
焼き込みテロップの検出条件は A案の scripts/40_qc.py と同じ（元素材で調整済み：HSV H100–125, S≥150, V≥170, 面積≥3000px, S中央値≥190）。
"""
import sys, json, re, subprocess, pathlib
import numpy as np, cv2, soundfile as sf, pyloudnorm as pyln
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
T = json.loads((ROOT / "comp/timeline.json").read_text()); C = T["cues"]
MP4, VER = pathlib.Path(sys.argv[1]), sys.argv[2]
OUT = ROOT / "qc" / VER; OUT.mkdir(parents=True, exist_ok=True)
FONT = ImageFont.truetype("/mnt/project-files/assets/fonts/BIZUDPGothic-Bold.ttf", 22)
rows, sections = [], []
def tc(t): m, s = divmod(t, 60); return f"{int(m):02d}:{s:05.2f}"
def res(name, ok, summary, warn=False):
    rows.append((name, "✅ PASS" if ok and not warn else ("⚠️ WARN" if ok else "❌ FAIL"), summary))
def run(cmd): return subprocess.run(cmd, capture_output=True, text=True)
P = json.loads(run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(MP4)]).stdout)
V = next(s for s in P["streams"] if s["codec_type"] == "video"); A = next(s for s in P["streams"] if s["codec_type"] == "audio")
DUR = float(P["format"]["duration"])

# 1 仕様
spec = [("解像度", f'{V["width"]}×{V["height"]}', "1920×1080"), ("フレームレート", V["r_frame_rate"], "30000/1001"),
        ("映像", V["codec_name"], "h264"), ("画素形式", V["pix_fmt"], "yuv420p"), ("音声", A["codec_name"], "aac"),
        ("サンプリング", A["sample_rate"], "48000"), ("チャンネル", str(A["channels"]), "2")]
bad = [r for r in spec if r[1] != r[2]]
dok = abs(DUR - T["duration"]) <= 0.1
res("仕様（ffprobe）", not bad and dok, f"尺 {DUR:.2f}s（計画 {T['duration']}s）" + ("" if not bad else f"、不一致 {bad}"))
sections.append("## 1. 仕様\n\n| 項目 | 実測 | 基準 |\n|---|---|---|\n" + "\n".join(f"| {a} | {b} | {c} |" for a, b, c in spec) + f"\n| 尺 | {DUR:.3f} | {T['duration']}±0.1 |\n")

# 2 黒コマ
err = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(MP4), "-vf", "blackdetect=d=0.1:pix_th=0.10", "-an", "-f", "null", "-"]).stderr
blk = [(float(a), float(b)) for a, b in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", err)]
intended_blk = lambda s, e: (s < 0.75) or (s >= C["end"] - 0.2)   # 冒頭0.7秒の黒（音から入る）とエンドカード（黒地）
ub = [b for b in blk if not intended_blk(*b)]
res("黒コマ（blackdetect）", not ub, f"意図外 {len(ub)} 件／全 {len(blk)} 件")
sections.append("## 2. 黒コマ\n\n" + "\n".join(f"- {tc(s)}–{tc(e)} {'意図（冒頭／終わり）' if intended_blk(s, e) else '**意図外**'}" for s, e in blk) + "\n")

# 3 静止
err = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(MP4), "-vf", "freezedetect=n=-60dB:d=0.5", "-an", "-f", "null", "-"]).stderr
fs = [float(x) for x in re.findall(r"freeze_start: ([\d.]+)", err)]; fe = [float(x) for x in re.findall(r"freeze_end: ([\d.]+)", err)]
fz = list(zip(fs, fe + [DUR] * (len(fs) - len(fe))))
IF = [(a, b, n) for a, b, n in T["intended_freezes"]] + [(C["mark"] - 0.2, T["duration"], "marker/end")]
def why(s, e):
    for a, b, n in IF:
        if s >= a - 0.3 and e <= b + 0.3: return f"意図（{n}：上で文字・線が動く）"
    if s < 0.75: return "意図（冒頭の黒）"
    return None
uf = [(s, e) for s, e in fz if not why(s, e)]
res("意図しない静止（freezedetect）", not uf, f"意図外 {len(uf)} 件／全 {len(fz)} 件")
sections.append("## 3. 静止（n=-60dB, d≥0.5s）\n\n" + "\n".join(f"- {tc(s)}–{tc(e)}（{e - s:.2f}s）{why(s, e) or '**意図外**'}" for s, e in fz) + "\n")

# 4 焼き込みテロップ・5 点滅・コンタクトシート（1回の復号で）
p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(MP4), "-vf", "fps=4", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
hits, thumbs, lum = [], [], []
i = 0
while True:
    buf = p.stdout.read(1920 * 1080 * 3)
    if len(buf) < 1920 * 1080 * 3: break
    f = np.frombuffer(buf, np.uint8).reshape(1080, 1920, 3); t = i / 4
    hsv = cv2.cvtColor(f, cv2.COLOR_BGR2HSV)
    m = ((hsv[..., 0] >= 100) & (hsv[..., 0] <= 125) & (hsv[..., 1] >= 150) & (hsv[..., 2] >= 170)).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    for k in range(1, n):
        if st[k, 4] >= 3000 and np.median(hsv[..., 1][lab == k]) >= 190: hits.append(t)
    if i % 2 == 0:
        im = Image.fromarray(f[..., ::-1]).resize((320, 180)); d = ImageDraw.Draw(im)
        d.rectangle((0, 0, 92, 26), fill=(0, 0, 0)); d.text((4, 2), tc(t), font=FONT, fill=(255, 255, 255)); thumbs.append(im)
    i += 1
p.wait()
res("焼き込みテロップの漏れ（4fps）", not hits, f"検出 {len(set(hits))} フレーム" + (f"：{sorted(set(hits))[:8]}" if hits else ""))
# 点滅：全コマの平均輝度
p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(MP4), "-vf", "scale=96:54,format=gray", "-f", "rawvideo", "-"], stdout=subprocess.PIPE)
while True:
    b = p.stdout.read(96 * 54)
    if len(b) < 96 * 54: break
    lum.append(np.frombuffer(b, np.uint8).mean())
p.wait()
lum = np.array(lum); dl = np.diff(lum); fps = 30000 / 1001
ev = [(k / fps, d) for k, d in enumerate(dl) if abs(d) >= 25]
worst = 0
for t0, _ in ev:
    w = [d for t, d in ev if t0 <= t < t0 + 1]
    worst = max(worst, sum(1 for a, b in zip(w, w[1:]) if np.sign(a) != np.sign(b)))
res("点滅（>3回/秒）", worst <= 3, f"最大 {worst} 回/秒")
onef = [k / fps for k in range(1, len(lum) - 1) if lum[k] < 8 and lum[k - 1] > 30 and lum[k + 1] > 30]
res("1コマの黒", not onef, f"{len(onef)} コマ")
per = 48
for k in range(0, len(thumbs), per):
    sheet = Image.new("RGB", (320 * 8, 180 * 6), (20, 20, 20))
    for j, im in enumerate(thumbs[k:k + per]): sheet.paste(im, ((j % 8) * 320, (j // 8) * 180))
    sheet.save(OUT / f"contact_0p5s_{k // per + 1}.jpg", quality=82)

# 6 文字の表示時間（字数÷4＋1秒、かつ≥1.5秒。帯の中の文字とタイトル）
tl = []
for x in T["texts"]:
    n = len(re.sub(r"[\s“”「」、。？！＝]", "", x["text"])); need = max(1.5, n / 4 + 1.0); have = x["end"] - x["start"]
    tl.append((x["id"], x["text"], n, have, need, have >= need - 0.05))
res("文字の表示時間", all(r[-1] for r in tl), f"{sum(r[-1] for r in tl)}/{len(tl)} 合格（注記ラベルは2〜4字で各2秒以上）")
sections.append("## 6. 文字の表示時間\n\n| id | 文 | 字数 | 表示 | 必要 | 判定 |\n|---|---|---|---|---|---|\n" +
                "\n".join(f"| {a} | {b} | {c} | {d:.2f} | {e:.2f} | {'OK' if f else 'NG'} |" for a, b, c, d, e, f in tl) + "\n")

# 7 ラウドネス（書き出したファイルを実測）
err = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(MP4), "-af", "ebur128=peak=true", "-f", "null", "-"]).stderr
I = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", err)[-1]); TPk = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", err)[-1])
res("ラウドネス（ebur128）", abs(I + 24) <= 1 and TPk <= -2, f"I {I:.1f} LUFS, TP {TPk:.1f} dBTP")

# 8 ナレと曲の差（ステム、ナレ区間の短時間ラウドネス 3秒窓）
SR = 48000; meter = pyln.Meter(SR, block_size=0.4)
vo, _ = sf.read(ROOT / "audio/stems/vo.wav"); bg, _ = sf.read(ROOT / "audio/stems/bgm.wav")
info = json.loads((ROOT / "audio/mix_info.json").read_text()); diffs = []
for nid, s, e in info["vo_windows"]:
    a, b = int(s * SR), int(e * SR)
    lv, lb = meter.integrated_loudness(vo[a:b]), meter.integrated_loudness(bg[a:b])
    diffs.append((nid, lv - lb))
mn = min(d for _, d in diffs)
res("ナレと曲の差（ステム）", mn >= 15, f"文ごと最小 {mn:.1f} dB")
sections.append("## 8. ナレと曲の差\n\n" + ", ".join(f"{n} {d:.1f}dB" for n, d in diffs) + "\n")

# 9 言葉と絵の同期（キーワードの発話時刻 vs 図の動き）
VT = json.loads((ROOT / "audio/vo/vo_timing.json").read_text())["lines"]
ns = {n["id"]: n["start"] for n in T["narration"]}
pairs = [("N2", "住所", C["title"], "タイトル"), ("N3", "基準点", C["s01_label"], "ラベル「基準点」"),
         ("N4", "向き", C["split_arc"] + 0.3, "向きの弧（描き途中）"), ("N4", "距離", C["split_dist"], "距離の線"),
         ("N5", "決まります", C["split_p"], "新しい点"), ("N8", "地図", C["contour"], "等高線"), ("N8", "道路", C["road"], "道路の線")]
sy = [(f"{n}「{k}」", ns[n] + VT[n]["keywords"][k], t, w) for n, k, t, w in pairs]
okp = [abs(a - b) <= 0.3 for _, a, b, _ in sy]
res("言葉と絵の同期（±0.3秒）", all(okp), f"{sum(okp)}/{len(okp)}")
sections.append("## 9. 言葉と絵の同期\n\n| 語 | 発話 | 図 | 差 |\n|---|---|---|---|\n" + "\n".join(f"| {a}→{w} | {b:.2f} | {c:.2f} | {b - c:+.2f} |" for a, b, c, w in sy) + "\n")

# 10 【要監修】の数（原稿と画面）
nar = (ROOT / "comp/narration.json").read_text(); plan = pathlib.Path("/mnt/project-files/teamB/plan/content.md").read_text()
k = plan.count("【要監修】")
res("【要監修】", True, f"内容プランに {k} か所（最終版でゼロ。技術監修待ち）", warn=k > 0)

# 11 台帳
led = (ROOT / "docs/credits.md").read_text() if (ROOT / "docs/credits.md").exists() else ""
need = ["03_komorebi", "summer-countryside1", "plants-swaying1", "plants-swaying2", "walk-soil1", "mechanical-pencil-write1", "cursor3", "decision28",
        "冥鳴ひまり", "BIZ UDPゴシック", "Shippori Mincho B1", "GSAP", "HyperFrames"]
miss = [x for x in need if x not in led]
res("素材台帳", not miss, "漏れなし" if not miss else f"漏れ {miss}")

rep = [f"# QC report {VER}（チームB）\n", f"- 対象: `{MP4.name}`\n- 計画尺: {T['duration']} s\n",
       f"- 総合: **{'PASS' if all(r[1] != '❌ FAIL' for r in rows) else 'FAIL'}**\n",
       "| 項目 | 判定 | 要約 |\n|---|---|---|\n" + "\n".join(f"| {a} | {b} | {c} |" for a, b, c in rows) + "\n"] + sections
(OUT / "report.md").write_text("\n".join(rep))
print("\n".join(f"{a}: {b} {c}" for a, b, c in rows))
