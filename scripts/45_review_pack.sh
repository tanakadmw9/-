#!/usr/bin/env bash
# 独立レビュー用のフォルダを作る：qc/<版>/review_pack/
#   bash scripts/45_review_pack.sh <版 例 v4.11> [書き出し.mp4]   フォルダを作る（作り直す）
#   bash scripts/45_review_pack.sh <版> --collect                  レビュアーが書いた review_pack/review.md を qc/<版>/review.md に移す
# レビュアーはこのフォルダだけを開く（コードと scripts/ は入れない＝画面と音の結果だけで判断させる）。
# 中の AGENTS.md がレビュアーへの指示（prompts/40_independent_review.md と同じ）。
# 作り手の依頼は qc/<版>/request.md に書く（無ければひな形を作る）。このフォルダは作り直すたびに消えるので、中に書いたものは残らない。
# 残すもの（コミットする）：qc/<版>/request.md と qc/<版>/review.md。
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/lib_env.sh
VER=${1:?版を指定（例 v4.11）}
Q=qc/$VER; P=$Q/review_pack
collect(){  # review_pack/review.md → qc/<版>/review.md（前のものは review_<時刻>.md に残す）
  [ -f "$P/review.md" ] || return 0
  if [ -f "$Q/review.md" ] && ! cmp -s "$P/review.md" "$Q/review.md"; then
    mv "$Q/review.md" "$Q/review_$(date +%Y%m%d-%H%M%S).md"
  fi
  cp "$P/review.md" "$Q/review.md"
  echo "レビューを $Q/review.md に移した（コミットする）"
}
if [ "${2:-}" = "--collect" ]; then
  [ -f "$P/review.md" ] || { echo "$P/review.md がありません（レビュアーはこのフォルダに review.md を書く）"; exit 1; }
  collect; exit 0
fi
MP4=${2:-$(ls renders/*/"$VER".mp4 2>/dev/null | head -1)}
[ -f "$Q/report.md" ] || { echo "$Q/report.md がありません。先に scripts/60_render.sh $VER"; exit 1; }
collect   # 作り直す前に、書かれたレビューを逃がす
[ -f "$Q/request.md" ] || cat > "$Q/request.md" <<EOF2
# 作り手からの依頼（$VER）

## 前の版からの変更（何を、なぜ）
- （書く）

## 特に見てほしい所（3つまで、タイムコードつき）
1. （書く）

## 前回の指摘への対応（対応した／据え置いた理由）
- （書く。docs/decisions.md の行と同じでよい）
EOF2
rm -rf "$P"; mkdir -p "$P/sheets" "$P/rules"
cp prompts/40_independent_review.md "$P/AGENTS.md"
cp docs/01_brief.md "$P/rules/01_brief.md"
cp docs/04_design_system.md "$P/rules/04_design_system.md"
cp docs/05_audio_design.md "$P/rules/05_audio_design.md"
cp docs/07_qc_and_review.md "$P/rules/07_qc_and_review.md"
cp docs/12_kanshu.md "$P/rules/12_kanshu.md" 2>/dev/null || true
cp "$Q/report.md" "$P/report.md"
cp "$Q/request.md" "$P/request.md"
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
# 前の版のレビュー（指摘が直ったかを見てもらう）：この版より前で、review.md がある一番新しい版
PREV=$(ls -d qc/v*/ 2>/dev/null | xargs -n1 basename | sort -Vu | awk -v v="$VER" '$0==v{exit} {print}' \
  | while read -r d; do if [ -f "qc/$d/review.md" ]; then echo "$d"; fi; done | tail -1)
[ -n "$PREV" ] && cp "qc/$PREV/review.md" "$P/previous_review_$PREV.md"
grep -q "（書く" "$P/request.md" && echo "注意：$Q/request.md がひな形のまま。書いてから、もう一度このスクリプトを実行する"
echo "作った：$P（前の版のレビュー：${PREV:-なし}）"
echo "次：このフォルダだけを開いた別のセッションに「AGENTS.md に従ってレビューし、review.md をこのフォルダに書いて」と頼む → 終わったら bash scripts/45_review_pack.sh $VER --collect"
ls "$P"
