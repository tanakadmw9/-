"""絵コンテ（1ページのHTML）を timeline.json と書き出し済みの映像から作る。
使い方：python3 scripts/50_storyboard.py renders/draft/v4.1.mp4
出力：storyboard/index.html（サムネイルは埋め込み。単体で開ける）
"""
import json, pathlib, subprocess, sys, base64, html

ROOT = pathlib.Path(__file__).resolve().parent.parent
T = json.loads((ROOT / "comp/timeline.json").read_text())
VIDEO = ROOT / sys.argv[1]
OUT = ROOT / "storyboard"; OUT.mkdir(exist_ok=True)

SCENE_DESC = {   # v4.10 の場面（scene の purpose と合わせて読む）
    "chapter_door": "紙の上に部門の作業アイコンが横一列（紺の線画）→ 基準点だけオレンジに灯る → 灯ったアイコンが照準に変わって動き出す",
    "title": "照準が S04 のプリズムに合う（「ピッ」）→ 小見出し「測量部門のしごと」＋「基準点測量」＋サブ「位置の“目印”をつくる」",
    "d0_marker": "S03 の三脚の大きさから縮む形のつなぎ → 地面のしるし（金属標）→ 三脚が真上に立つ → 言葉「基準点」でしるしが灯る",
    "d1_observe": "S09 の静止（彩度を落とす）→ 札「はかる機械／トータルステーション」「プリズム」→ 光の線と測距 → 写真が奥へ倒れる",
    "d2_topview": "真上から：わかっている点A（機械）→ 点B と向き → 角度の線が回る → 距離 → 新しい点（◎）が決まる",
    "map_link": "草原が地図の紙に溶ける → 基準点の△ → 等高線・道路の線が描かれる → 章扉のアイコン列が戻り、線を受けて灯る",
    "endcard": "締めの一文「ほかの測量が使う“はじまりの点”」→ 照準が一点に縮み、章扉の基準点アイコンに戻る → 黒へ",
}
SE_NAME = {"lock": "照準が合う「ピッ」", "measure": "測距の電子音", "click": "点が決まる音", "join": "低めの「カチッ」", "glow": "アイコンが灯る音", "foley": "鉛筆で描く音"}

def thumb(t):
    p = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", f"{t:.3f}", "-i", str(VIDEO),
                        "-frames:v", "1", "-vf", "scale=400:-1", "-q:v", "5", "-f", "image2", "-c:v", "mjpeg", "-"],
                       capture_output=True, check=True).stdout
    return "data:image/jpeg;base64," + base64.b64encode(p).decode()

def tc(t):
    return f"{int(t // 60)}:{t % 60:04.1f}"

def overlap(a0, a1, b0, b1):
    return a0 < b1 and b0 < a1

rows = []
for bt in T["beats"]:
    a, b = bt["start"], bt["end"]
    items = [x for x in T["shots"] if overlap(a, b, x["start"], x["start"] + x["dur"])]
    items += [x for x in T["scenes"] if overlap(a, b, x["start"], x["start"] + x["dur"]) and x["start"] >= a - 0.01]
    items.sort(key=lambda x: x["start"])
    pics = []
    for x in items:
        mid = x["start"] + min(x["dur"] * 0.6, x["dur"] - 0.2)
        label = x.get("shot") or x["id"]
        pics.append(f'<figure><img src="{thumb(mid)}" alt=""><figcaption>{tc(x["start"])} {html.escape(label)}</figcaption></figure>')
    vo = [v for v in T["vo"] if a <= v["start"] < b]
    vo_html = "".join(f'<p><b>{v["id"]}</b> <span class="t">{tc(v["start"])}</span><br>{html.escape(v["text"])}</p>' for v in vo) or "<p class='muted'>（ナレなし）</p>"
    words = [t for t in T["telops"] if a <= t["start"] < b]
    words_html = "".join(f"<p>キーワード「{html.escape(t['text'])}」{t['dur']:.1f}秒</p>" for t in words)
    dg = [x for x in T["scenes"] if a <= x["start"] < b]
    dg_html = "".join(f"<p><b>{x['id']}</b><br>{html.escape(SCENE_DESC.get(x['id'], ''))}</p>" for x in dg) or "<p class='muted'>—</p>"
    snd = []
    if bt["id"] == "B1": snd.append("環境音（風・草）のみ。BGMなし")
    for s in T["se"]:
        if a <= s["start"] < b: snd.append(f"{tc(s['start'])} {SE_NAME.get(s['kind'], s['kind'])}")
    if a <= T["bgm"]["start"] < b: snd.append(f"{tc(T['bgm']['start'])} BGM開始")
    pz = T["bgm"].get("pause")
    if pz and a <= pz["start"] < b: snd.append(f"{tc(pz['start'])}–{tc(pz['end'])} BGMを抜く（間）")
    if a <= T["bgm"]["end"] <= b + 0.01: snd.append("BGMはフレーズの終わりで終止")
    purposes = [x.get("purpose", "") for x in items if x.get("purpose")]
    rows.append(f"""
<section class="beat">
  <header><span class="id">{bt['id']}</span><span class="time">{tc(a)}–{tc(b)}（{bt['dur']:.1f}秒）</span></header>
  <div class="goal">目的：{html.escape(bt['purpose'])}</div>
  <div class="pics">{''.join(pics)}</div>
  <div class="cols">
    <div><h4>ナレーション</h4>{vo_html}</div>
    <div><h4>文字・図解</h4>{words_html}{dg_html}</div>
    <div><h4>音</h4>{''.join(f'<p>{html.escape(s)}</p>' for s in snd) or "<p class='muted'>BGM・環境音（ナレ中は下げる）</p>"}</div>
  </div>
  <details><summary>各要素の目的</summary><ul>{''.join(f'<li>{html.escape(p)}</li>' for p in purposes)}</ul></details>
</section>""")

page = f"""<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>基準点測量 絵コンテ</title>
<style>
:root {{ --ink:#14202E; --navy:#1F3A5F; --paper:#F4F1EA; --grid:#D9D3C4; --orange:#E8742A; --orange-dark:#B8541A; --bg:#F4F1EA; --card:#fff; --muted:#5b6673; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --bg:#11171f; --card:#1a222d; --ink:#e8edf2; --navy:#9fb7d6; --grid:#2c3744; --muted:#9aa6b2; }} }}
:root[data-theme="dark"] {{ --bg:#11171f; --card:#1a222d; --ink:#e8edf2; --navy:#9fb7d6; --grid:#2c3744; --muted:#9aa6b2; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--ink); font-family:"BIZ UDPGothic","Hiragino Sans","Noto Sans JP",sans-serif; line-height:1.6; }}
main {{ max-width:1180px; margin:0 auto; padding:24px 16px 64px; }}
h1 {{ font-size:1.6rem; margin:0 0 4px; }} .lead {{ color:var(--muted); margin:0 0 20px; }}
.beat {{ background:var(--card); border-left:6px solid var(--orange); border-radius:6px; padding:16px; margin:0 0 18px; }}
.beat header {{ display:flex; gap:12px; align-items:baseline; flex-wrap:wrap; }}
.id {{ font-weight:700; font-size:1.3rem; color:var(--navy); }} .time {{ color:var(--muted); font-variant-numeric:tabular-nums; }}
.goal {{ font-weight:700; margin:4px 0 10px; }}
.pics {{ display:flex; gap:8px; overflow-x:auto; padding-bottom:4px; }}
figure {{ margin:0; flex:0 0 auto; }} figure img {{ width:260px; max-width:70vw; border-radius:4px; display:block; }}
figcaption {{ font-size:.8rem; color:var(--muted); }}
.cols {{ display:grid; grid-template-columns:repeat(3,1fr); gap:14px; margin-top:10px; }}
@media (max-width:760px) {{ .cols {{ grid-template-columns:1fr; }} }}
h4 {{ margin:0 0 4px; font-size:.85rem; color:var(--navy); border-bottom:1px solid var(--grid); }}
.cols p {{ margin:0 0 6px; font-size:.95rem; }} .t {{ color:var(--muted); font-size:.8rem; }} .muted {{ color:var(--muted); }}
details {{ margin-top:8px; font-size:.9rem; }} summary {{ cursor:pointer; color:var(--muted); }}
</style></head><body><main>
<h1>基準点測量 絵コンテ（構成 A'・v4.2）</h1>
<p class="lead">全{T['duration']:.1f}秒・{len(T['beats'])}拍。画はアニマティック v4.2 の書き出しから。ナレは仮（合成音声）。正本は comp/timeline.json。</p>
{''.join(rows)}
</main></body></html>"""
(OUT / "index.html").write_text(page)
print("wrote storyboard/index.html", len(page) // 1024, "KB")
