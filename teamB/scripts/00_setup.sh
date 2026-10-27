#!/usr/bin/env bash
# チームB 準備：元素材・フォント・GSAP をそろえ、VOICEVOX を起動する（大きなファイルは Git に入れていない）
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p ../source comp/assets/{video,audio,fonts,vendor}
[ -f ../source/input.mp4 ] || cp /mnt/project-files/source/input.mp4 ../source/
(cd .. && npm ci --silent)
cp ../node_modules/gsap/dist/gsap.min.js comp/assets/vendor/
cp -n /mnt/project-files/assets/fonts/BIZUDPGothic-{Bold,Regular}.ttf /mnt/project-files/assets/fonts/BIZUDGothic-Bold.ttf comp/assets/fonts/ || true
for w in ExtraBold; do
  f=comp/assets/fonts/ShipporiMinchoB1-$w.ttf
  [ -f "$f" ] || cp /mnt/project-files/teamB/plan/fonts/ShipporiMinchoB1-$w.ttf "$f" 2>/dev/null \
    || curl -sSfL -o "$f" "https://raw.githubusercontent.com/google/fonts/main/ofl/shipporiminchob1/ShipporiMinchoB1-$w.ttf"
done
pip install -q librosa soundfile pyloudnorm fonttools brotli opencv-python-headless
# VOICEVOX（仮ナレを作り直すときだけ必要）：dockerd を別に起動してから
#   docker run -d --name vv -p 50021:50021 mirror.gcr.io/voicevox/voicevox_engine:cpu-latest
