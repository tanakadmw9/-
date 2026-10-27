#!/usr/bin/env bash
# フェーズ1：素材解析（仕様・シーン検出・カットごとのコンタクトシート）。何度実行しても同じ結果。
set -euo pipefail
cd "$(dirname "$0")/.."
SRC=source/input.mp4
OUT=analysis
mkdir -p $OUT/sheets
ffprobe -v error -show_format -show_streams -of json $SRC > $OUT/ffprobe.json
# シーン検出（しきい値0.3）
ffmpeg -hide_banner -nostats -i $SRC -vf "select='gt(scene,0.3)',showinfo" -an -f null - 2>&1 \
  | grep -o 'pts_time:[0-9.]*' | cut -d: -f2 > $OUT/scene_cuts.txt
# 全体のコンタクトシート（1fps）
ffmpeg -hide_banner -loglevel error -y -i $SRC -vf "fps=1,scale=384:-1,drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text='%{pts\:hms}':x=6:y=6:fontsize=20:fontcolor=yellow:box=1:boxcolor=black@0.6,tile=5x8" -frames:v 1 $OUT/sheets/overview_1fps.png
# カットごとのコンタクトシート（4fps、タイムコード入り）
CUTS=(0 5.739 8.909 14.615 17.885 20.354 23.457 26.593 30.664 36.670 39.74)
for i in $(seq 0 9); do
  a=${CUTS[$i]}; b=${CUTS[$((i+1))]}; id=$(printf "S%02d" $((i+1)))
  ffmpeg -hide_banner -loglevel error -y -ss $a -to $b -i $SRC -vf "fps=4,scale=320:-1,drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text='$id %{pts\:hms\:$a}':x=4:y=4:fontsize=16:fontcolor=yellow:box=1:boxcolor=black@0.6,tile=6x4" -frames:v 1 $OUT/sheets/${id}_4fps.png
done
