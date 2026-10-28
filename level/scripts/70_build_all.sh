#!/usr/bin/env bash
# 最初から全部つくり直す（元映像 → 中間素材 → 仮ナレ → 効果音・環境音 → BGM → 書き出し → 自動QC）。
#   bash scripts/70_build_all.sh <版 例 v4.11> [draft|looks|delivery]
# 足りない素材は代わりで進む（00_doctor.sh の ⚠️）。代わりで作った版は v4.10 と同じ音にならない。qc/<版>/report.md の「音の素材」の行に残る。
# QC が FAIL でも rc=0（STRICT=1 なら rc=1）。成否は最後の行で見る。
set -euo pipefail
cd "$(dirname "$0")/.."
VER=${1:?版を指定（例 v4.11）}; Q=${2:-draft}
source scripts/lib_env.sh
for f in S_sueru K_kansoku N_nozoki; do [ -f source/$f.mp4 ] || { echo "source/$f.mp4 がありません"; exit 1; }; done
echo "■ 1/6 中間素材（切り出し・色補正 B・静止画）"; python3 scripts/02_intermediates.py B
echo "■ 2/6 仮ナレ"
if [ -n "$(ls audio/vo_temp/*.wav 2>/dev/null)" ] && [ "${REDO_VO:-0}" != 1 ]; then
  echo "  audio/vo_temp/ の wav を使う（作り直すときは REDO_VO=1）"
else
  # F版：速さ 1.0・抑揚 1.1（上限 1.4）・読点の間 1.4・高さ +0.04。文ごとの読み方は comp/narration.json の vv_kana / vv_dir
  python3 scripts/11_tts_voicevox.py 14 audio/vo_temp 1.0 1.1 1.4 0.04
fi
echo "■ 3/6 尺の計画（timeline.json）"; python3 scripts/20_plan_timeline.py
echo "■ 4/6 効果音（合成の予備）・環境音"; python3 scripts/31_make_se.py; python3 scripts/32_make_amb.py
bash scripts/04_stage_assets.sh B
echo "■ 5/6 BGM"
if [ -f source/music/01_new_departure.mp3 ]; then python3 scripts/34_prep_bgm.py source/music/01_new_departure.mp3
else echo "  WARNING: source/music/01_new_departure.mp3 が無い → 自作の仮BGM（テンポは格子どおりだが、曲の山がない確認用の音。QC の「ナレとBGMの差」は FAIL になりやすい）"; rm -f audio/bgm/bgm.wav; python3 scripts/33_make_temp_bgm.py; fi
echo "■ 6/6 書き出しと自動QC"; bash scripts/60_render.sh "$VER" "$Q"
