"""comp/timeline.json から comp/index.html を生成する（index.html は手で直さない）。
使い方：
  python3 scripts/21_build_index.py                 # 本編 comp/index.html
  python3 scripts/21_build_index.py --scene d2_topview   # 1場面だけの確認用プロジェクト dev/d2_topview/
"""
import json, pathlib, sys, html, os, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
COMP = ROOT / "comp"
T = json.loads((COMP / "timeline.json").read_text())

HEAD = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<!-- 生成ファイル：scripts/21_build_index.py が comp/timeline.json から作る。手で直さない。 -->
<link rel="stylesheet" href="styles/fonts.css">
<link rel="stylesheet" href="styles/tokens.css">
<script src="assets/vendor/gsap.min.js"></script>
<style>
  #root { background: #000; }
  .full { position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; object-fit: cover; }
</style>
</head>
<body>
"""
TAIL = """<script>
  window.__timelines = window.__timelines || {};
  window.__timelines["main"] = gsap.timeline({ paused: true });
</script>
</body>
</html>
"""

def attr(v):
    return html.escape(v, quote=True)

def scene_host(sc, start=None, z=5):
    vals = dict(sc.get("variables", {}))
    vals["cues"] = json.dumps(sc["cues"], ensure_ascii=False)
    vals["dur"] = sc["dur"]
    st = sc["start"] if start is None else start
    return (f'  <div id="{sc["id"]}" data-composition-id="{sc["id"]}" data-composition-src="{sc["comp"]}"'
            f" data-variable-values='{attr(json.dumps(vals, ensure_ascii=False))}'"
            f' data-start="{st}" data-duration="{sc["dur"]}" data-track-index="2" data-track-kind="graphics"'
            f' data-width="1920" data-height="1080" style="z-index:{z}"></div>\n')

def telop_files():
    """キーワードテロップは部品テンプレートから id ごとにファイルを作る（host id と composition id を一致させるため）。"""
    tpl = (COMP / "compositions/telop_keyword.html").read_text()
    gen = COMP / "compositions/gen"; gen.mkdir(exist_ok=True)
    for t in T["telops"]:
        s = tpl.replace("telop_keyword", t["id"]).replace("kw-", f"{t['id']}-")
        (gen / f"{t['id']}.html").write_text(s)

def build_main():
    telop_files()
    out = [HEAD, f'<div id="root" data-composition-id="main" data-start="0" data-duration="{T["duration"]}"'
                 f' data-width="1920" data-height="1080" data-fps="30000/1001">\n']
    z = 1
    for i, s in enumerate(T["shots"]):
        out.append(f'  <video id="v{i:02d}_{s["shot"]}" class="clip full" src="{s["src"]}" muted playsinline'
                   f' data-start="{s["start"]}" data-duration="{s["dur"]}" data-media-start="{s["media_start"]}"'
                   f' data-track-index="0" style="z-index:{z}"></video>\n')
    for s in T["stills"]:
        out.append(f'  <img id="still_{s["id"]}" class="clip full" src="{s["src"]}" alt=""'
                   f' data-start="{s["start"]}" data-duration="{s["dur"]}" data-track-index="0" style="z-index:{z}">\n')
    for sc in T["scenes"]:
        out.append(scene_host(sc, z=6 if sc.get("overlay") else 4))
    for t in T["telops"]:
        vals = {"text": t["text"]}
        out.append(f'  <div id="{t["id"]}" data-composition-id="{t["id"]}" data-composition-src="compositions/gen/{t["id"]}.html"'
                   f" data-variable-values='{attr(json.dumps(vals, ensure_ascii=False))}'"
                   f' data-start="{t["start"]}" data-duration="{t["dur"]}" data-track-index="3" data-track-kind="graphics"'
                   f' data-width="1920" data-height="1080" style="z-index:8"></div>\n')
    if (COMP / "assets/audio/mix.wav").exists():
        out.append(f'  <audio id="mix" class="clip" src="assets/audio/mix.wav" data-start="0" data-duration="{T["duration"]}"'
                   f' data-volume="1" data-track-index="5"></audio>\n')
    out.append("</div>\n")
    out.append(TAIL)
    (COMP / "index.html").write_text("".join(out))
    print("wrote comp/index.html", T["duration"], "s")

def build_scene(sid):
    """1場面だけを 0 秒から再生する確認用プロジェクト。assets/styles/compositions は comp/ へのリンク。"""
    sc = next(s for s in T["scenes"] if s["id"] == sid)
    d = ROOT / "dev" / sid; d.mkdir(parents=True, exist_ok=True)
    for name in ("assets", "styles", "compositions"):
        p = d / name
        if not p.exists():
            os.symlink(os.path.relpath(COMP / name, d), p)
    bg = ""
    if sc.get("overlay"):  # 実写の上に乗る場面は、本編で下にある画を敷く
        for s in T["shots"]:
            if s["start"] < sc["start"] + sc["dur"] and s["start"] + s["dur"] > sc["start"]:
                rel = s["start"] - sc["start"]
                bg += (f'  <video id="bg_{s["shot"]}" class="clip full" src="{s["src"]}" muted playsinline'
                       f' data-start="{max(0, rel):.4f}" data-duration="{s["dur"] + min(0, rel):.4f}"'
                       f' data-media-start="{s["media_start"] - min(0, rel):.4f}" data-track-index="0" style="z-index:1"></video>\n')
        for s in T["stills"]:
            if s["start"] < sc["start"] + sc["dur"] and s["start"] + s["dur"] > sc["start"]:
                rel = s["start"] - sc["start"]
                bg += (f'  <img id="bgs_{s["id"]}" class="clip full" src="{s["src"]}" alt=""'
                       f' data-start="{max(0, rel):.4f}" data-duration="{s["dur"]:.4f}" data-track-index="0" style="z-index:1">\n')
    out = [HEAD, f'<div id="root" data-composition-id="main" data-start="0" data-duration="{sc["dur"]}"'
                 f' data-width="1920" data-height="1080" data-fps="30000/1001">\n', bg, scene_host(sc, start=0), "</div>\n", TAIL]
    (d / "index.html").write_text("".join(out))
    print(f"wrote dev/{sid}/index.html ({sc['dur']}s)")

if __name__ == "__main__":
    if "--scene" in sys.argv:
        build_scene(sys.argv[sys.argv.index("--scene") + 1])
    else:
        build_main()
