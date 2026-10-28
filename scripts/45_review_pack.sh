#!/usr/bin/env bash
# 独立レビュー用のフォルダを作る：qc/<版>/review_pack/
#   bash scripts/45_review_pack.sh <版 例 v4.11> [書き出し.mp4]
# レビュアーはこのフォルダだけを開く（コードと scripts/ は入れない＝画面と音の結果だけで判断させる）。
# 中の AGENTS.md がレビュアーへの指示（prompts/40_independent_review.md と同じ）。request.md は作り手が書く。
set -euo pipefail
cd "$(dirname "$0")/.."
VER=${1:?版を指定（例 v4.11）}
MP4=${2:-$(ls renders/*/"$VER".mp4 2>/dev/null | head -1)}
Q=qc/$VER; P=$Q/review_pack
[ -f "$Q/report.md" ] || { echo "$Q/report.md がありません。先に scripts/60_render.sh $VER"; exit 1; }
rm -rf "$P"; mkdir -p "$P/sheets" "$P/rules"
cp prompts/40_independent_review.md "$P/AGENTS.md"
cp docs/01_brief.md "$P/rules/01_brief.md"
cp docs/04_design_system.md "$P/rules/04_design_system.md"
cp docs/05_audio_design.md "$P/rules/05_audio_design.md"
cp docs/07_qc_and_review.md "$P/rules/07_qc_and_review.md"
cp docs/12_kanshu.md "$P/rules/12_kanshu.md" 2>/dev/null || true
cp "$Q/report.md" "$P/report.md"
for f in "$Q"/*.jpg "$Q"/*.png "$Q"/text_timing.json; do [ -f "$f" ] && cp "$f" "$P/sheets/"; done
[ -d "$Q/hf_review" ] && cp -r "$Q/hf_review" "$P/sheets/"
[ -n "$MP4" ] && [ -f "$MP4" ] && cp "$MP4" "$P/video.mp4"
# 原稿と、画面に出る時刻（timeline から）
python3 - "$P/script.md" <<'PY'
import json, sys, pathlib
T = json.loads(pathlib.Path("comp/timeline.json").read_text())
out = ["# 原稿と時刻（comp/timeline.json から自動）", "", f"尺 {T['duration']} 秒。", "",
       "## 拍（構成）", "", "| 拍 | 始 | 終 | 目的 |", "|---|---|---|---|"]
out += [f"| {b['id']} | {b['start']:.2f} | {b['end']:.2f} | {b['purpose']} |" for b in T["beats"]]
out += ["", "## ナレーション", "", "| id | 始 | 終 | 文 |", "|---|---|---|---|"]
out += [f"| {v['id']} | {v['start']:.2f} | {v['start'] + v['dur']:.2f} | {v.get('text', '')} |" for v in T["vo"]]
out += ["", "## 場面（図解・文字）", "", "| 場面 | 始 | 終 | 目的 |", "|---|---|---|---|"]
out += [f"| {s['id']} | {s['start']:.2f} | {s['start'] + s['dur']:.2f} | {s.get('purpose', '')} |" for s in T["scenes"]]
out += ["", "## 実写", "", "| カット | 始 | 終 | 目的 |", "|---|---|---|---|"]
out += [f"| {s['shot']} | {s['start']:.2f} | {s['start'] + s['dur']:.2f} | {s.get('purpose', '')} |" for s in T["shots"]]
out += ["", "## 効果音", "", "| 種類 | 時刻 | ねらい |", "|---|---|---|"]
out += [f"| {e['kind']} | {e['start']:.2f} | {e.get('note', '')} |" for e in T["se"]]
pathlib.Path(sys.argv[1]).write_text("\n".join(out) + "\n", encoding="utf-8")
PY
# 前の版のレビュー（指摘が直ったかを見てもらう）
PREV=$(ls -d qc/v*/ 2>/dev/null | xargs -n1 basename | sort -Vu | awk -v v="$VER" '$0==v{print p; exit} {p=$0}')
for d in qc; do
  if [ -n "$PREV" ] && [ -f "$d/$PREV/review.md" ]; then cp "$d/$PREV/review.md" "$P/previous_review_$PREV.md"; break; fi
done
[ -f "$P/request.md" ] || cat > "$P/request.md" <<EOF2
# 作り手からの依頼（$VER）

## 前の版からの変更（何を、なぜ）
- （書く）

## 特に見てほしい所（3つまで、タイムコードつき）
1. （書く）

## 前回の指摘への対応（対応した／据え置いた理由）
- （書く。docs/decisions.md の行と同じでよい）
EOF2
echo "作った：$P（request.md を書いてから、このフォルダだけを開いた別のセッションでレビューさせる）"
ls "$P"
