#!/usr/bin/env bash
# 書き出し一式：index生成 → HyperFrames で映像 → ミックスと合わせて MP4 → 自動QC
# 使い方：scripts/60_render.sh <版 例 v4.1> [draft|looks|delivery]
set -euo pipefail
cd "$(dirname "$0")/.."
VER=${1:?版を指定（例 v4.1）}; Q=${2:-draft}
DIR=renders/$([ "$Q" = delivery ] && echo master || ([ "$Q" = looks ] && echo review || echo draft))
mkdir -p "$DIR"
# Chromium の場所：環境変数 → scripts/lib_env.sh が探す（無ければ HyperFrames 自身に任せる）
source scripts/lib_env.sh
python3 scripts/20_plan_timeline.py
python3 scripts/30_mix.py   # timeline が変わったら音も必ず作り直す（古い mix を合わせない）
python3 scripts/21_build_index.py
npx hyperframes lint comp
npx hyperframes render comp -q "$Q" --fps 30000/1001 -o "$DIR/${VER}_video.mp4"
# 音：scripts/30_mix.py の出力（−24 LUFS / −2 dBTP に調整済み）を AAC 48kHz 320kbps で合わせる
ffmpeg -hide_banner -loglevel error -y -i "$DIR/${VER}_video.mp4" -i audio/mix/mix.wav \
  -map 0:v:0 -map 1:a:0 -c:v libx264 -preset slow -crf $([ "$Q" = delivery ] && echo 14 || echo 18) -profile:v high -pix_fmt yuv420p \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 \
  -c:a aac -b:a 320k -ar 48000 -ac 2 -shortest -movflags +faststart "$DIR/${VER}.mp4"
ffprobe -v error -show_entries format=duration -of csv=p=0 "$DIR/${VER}.mp4"
# 自動QC：FAIL でも書き出しは残す（rc=0）。STRICT=1 なら FAIL で rc=1。結果は最後の行と qc/<版>/report.md の「総合」
rc=0; python3 scripts/40_qc.py "$DIR/${VER}.mp4" "$VER" || rc=$?
echo "================================================================"
if [ "$rc" = 0 ]; then echo "自動QC 総合 PASS：qc/$VER/report.md（WARN の行も読む）"
else echo "自動QC 総合 FAIL：qc/$VER/report.md の ❌ の行を読む（代わりの音で作った場合の「ナレとBGMの差」は想定どおり）"; fi
echo "================================================================"
[ "${STRICT:-0}" = 1 ] && exit "$rc"
exit 0
