#!/usr/bin/env bash
# 書き出し一式：index生成 → HyperFrames で映像 → ミックスと合わせて MP4 → 自動QC
# 使い方：scripts/60_render.sh <版 例 v4.1> [draft|looks|delivery]
set -euo pipefail
cd "$(dirname "$0")/.."
VER=${1:?版を指定（例 v4.1）}; Q=${2:-draft}
DIR=renders/$([ "$Q" = delivery ] && echo master || ([ "$Q" = looks ] && echo review || echo draft))
mkdir -p "$DIR"
export HYPERFRAMES_BROWSER_PATH=${HYPERFRAMES_BROWSER_PATH:-/opt/pw-browsers/chromium-1243/chrome-linux64/chrome}
python3 scripts/21_build_index.py
npx hyperframes lint comp
npx hyperframes render comp -q "$Q" --fps 30000/1001 -o "$DIR/${VER}_video.mp4"
# 音：scripts/30_mix.py の出力（−24 LUFS / −2 dBTP に調整済み）を AAC 48kHz 320kbps で合わせる
ffmpeg -hide_banner -loglevel error -y -i "$DIR/${VER}_video.mp4" -i audio/mix/mix.wav \
  -map 0:v:0 -map 1:a:0 -c:v libx264 -preset slow -crf $([ "$Q" = delivery ] && echo 14 || echo 18) -profile:v high -pix_fmt yuv420p \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 \
  -c:a aac -b:a 320k -ar 48000 -ac 2 -shortest -movflags +faststart "$DIR/${VER}.mp4"
ffprobe -v error -show_entries format=duration -of csv=p=0 "$DIR/${VER}.mp4"
[ -f scripts/40_qc.py ] && python3 scripts/40_qc.py "$DIR/${VER}.mp4" "$VER" || true
