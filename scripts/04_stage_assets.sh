#!/usr/bin/env bash
# 中間素材を comp/assets/ に配置する（色補正案は引数、既定 B）。D1用の「彩度を落とした静止画」もここで作る。
set -euo pipefail
cd "$(dirname "$0")/.."
G=${1:-B}
mkdir -p comp/assets/video comp/assets/audio/vo
cp intermediate/$G/S*.mp4 intermediate/$G/*.png comp/assets/video/
# D1：実写の彩度と明るさを落とした版（クロスフェードで使う。CSSフィルタは使わない）
ffmpeg -hide_banner -loglevel error -y -i intermediate/$G/S09_freeze.png \
  -vf "eq=saturation=0.55:brightness=0.04:contrast=0.9" comp/assets/video/S09_freeze_desat.png
cp audio/vo_temp/*.wav comp/assets/audio/vo/ 2>/dev/null || true
ls comp/assets/video
