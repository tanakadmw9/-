"""チームB：comp/timeline.json と comp/src/main.html（ひな形）から comp/index.html を作る（index.html は手で直さない）。
使い方: python3 teamB/scripts/25_build_index.py"""
import json, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
C = ROOT / "comp"
T = json.loads((C / "timeline.json").read_text())
vids = []
for s in T["shots"]:
    cls = "clip v" + (" win" if s.get("w") else "")
    vids.append(f'  <video id="v_{s["id"]}" class="{cls}" src="assets/video/{s["id"]}.mp4" muted playsinline'
                f' data-start="{s["start"]}" data-duration="{s["dur"]}" data-media-start="0" data-track-index="0"'
                f' style="z-index:1"></video>')
audio = ""
if (C / "assets/audio/mix.wav").exists():
    audio = (f'  <audio id="mix" class="clip" src="assets/audio/mix.wav" data-start="0" data-duration="{T["duration"]}"'
             f' data-volume="1" data-track-index="5"></audio>')
html = (C / "src/main.html").read_text()
html = (html.replace("{{DURATION}}", str(T["duration"])).replace("{{VIDEOS}}", "\n".join(vids))
            .replace("{{AUDIO}}", audio).replace("{{TL}}", json.dumps(T, ensure_ascii=False)))
html = html.replace("<!-- チームB 本編のひな形。", "<!-- 生成ファイル（teamB/scripts/25_build_index.py）。元はひな形 comp/src/main.html。")
(C / "index.html").write_text(html)
print("wrote teamB/comp/index.html", T["duration"], "s,", len(vids), "clips")
