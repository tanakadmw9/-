#!/usr/bin/env bash
# 中間素材を comp/assets/ に配置する（色補正案は引数、既定 Bplus＝v3 で採用）。
set -euo pipefail
cd "$(dirname "$0")/.."
G=${1:-Bplus}
mkdir -p comp/assets/video comp/assets/audio/vo
rm -f comp/assets/video/*
cp intermediate/$G/L*.mp4 intermediate/$G/*.png comp/assets/video/
cp audio/vo_temp/*.wav comp/assets/audio/vo/ 2>/dev/null || true
ls comp/assets/video
