#!/usr/bin/env bash
# チームB 書き出し一式：timeline → カット → 音 → index → HyperFrames → 音と合わせて MP4 → 自動QC
# 使い方：teamB/scripts/60_render.sh <版 例 B1.1> [draft|looks|delivery]
set -euo pipefail
cd "$(dirname "$0")/.."
VER=${1:?版を指定（例 B1.1）}; Q=${2:-draft}
OUT=renders; mkdir -p "$OUT"
export HYPERFRAMES_BROWSER_PATH=${HYPERFRAMES_BROWSER_PATH:-/opt/pw-browsers/chromium-1243/chrome-linux64/chrome}
python3 scripts/15_timeline.py > /dev/null
python3 scripts/20_cuts.py
python3 scripts/30_mix.py
python3 scripts/05_fonts.py > /dev/null 2>&1
python3 scripts/25_build_index.py
npx --prefix .. hyperframes lint comp
npx --prefix .. hyperframes render comp -q "$Q" --fps 30000/1001 -o "$OUT/${VER}_video.mp4"
ffmpeg -hide_banner -loglevel error -y -i "$OUT/${VER}_video.mp4" -i comp/assets/audio/mix.wav \
  -map 0:v:0 -map 1:a:0 -c:v libx264 -preset slow -crf $([ "$Q" = delivery ] && echo 14 || echo 18) -profile:v high -pix_fmt yuv420p \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 \
  -c:a aac -b:a 320k -ar 48000 -ac 2 -shortest -movflags +faststart "$OUT/${VER}.mp4"
ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT/${VER}.mp4"
python3 scripts/40_qc.py "$OUT/${VER}.mp4" "$VER"
