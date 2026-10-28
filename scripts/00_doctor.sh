#!/usr/bin/env bash
# 環境チェック：何がそろっていて、何が足りないか。足りないものは「代わり」で動くかも示す。
#   bash scripts/00_doctor.sh
cd "$(dirname "$0")/.."
source scripts/lib_env.sh
ok(){ printf "  ✅ %s\n" "$1"; }; ng(){ printf "  ❌ %s\n" "$1"; }; alt(){ printf "  ⚠️  %s\n" "$1"; }
echo "■ ツール"
command -v node >/dev/null && ok "Node $(node -v)" || ng "Node.js（22 以上）"
command -v ffmpeg >/dev/null && ok "$(ffmpeg -version | head -1 | cut -c1-40)" || ng "FFmpeg"
python3 -c "import numpy,scipy,soundfile,cv2,PIL,librosa" 2>/dev/null && ok "Python の部品（requirements.txt）" || ng "Python の部品：python3 -m pip install -r requirements.txt"
[ -f node_modules/hyperframes/package.json ] && v=$(node -p "require('./node_modules/hyperframes/package.json').version") && { [ "$v" = 0.8.206 ] && ok "HyperFrames $v（固定版）" || ng "HyperFrames $v（0.8.206 に固定すること。scripts/44_text_timing.mjs が内部のファイル名に依存）"; } || ng "HyperFrames：npm ci"
[ -n "${HYPERFRAMES_BROWSER_PATH:-}" ] && ok "Chromium: $HYPERFRAMES_BROWSER_PATH" || alt "Chromium を自動では見つけられない → npx hyperframes browser ensure、または HYPERFRAMES_BROWSER_PATH を指定"
[ -f comp/assets/vendor/gsap.min.js ] && [ -n "$(ls comp/assets/fonts/*.woff2 2>/dev/null)" ] && ok "フォントと GSAP（comp/assets）" || ng "フォントと GSAP：bash scripts/03_fonts_css.sh"
echo "■ 素材（リポジトリに入れないもの。置き方は source/README.md と assets/README.md）"
[ -f source/input.mp4 ] && ok "元映像 source/input.mp4" || ng "元映像 source/input.mp4（media の zip か社内から）"
[ -f source/music/01_new_departure.mp3 ] || [ -f audio/bgm/bgm.wav ] && ok "BGM（New Departure）" || alt "BGM が無い → 自作の仮BGM（scripts/33_make_temp_bgm.py）で代用できるが、拍の格子は New Departure 前提"
n=0; for f in tones/decision28.mp3 tones/decision6.mp3 tones/cursor3.mp3 foley/mechanical-pencil-write1.mp3; do [ -f "${SE_DIR:-assets/se}/$f" ] && n=$((n+1)); done
[ $n = 4 ] && ok "効果音ラボの効果音 4/4" || alt "効果音ラボの効果音 $n/4 → 自作の合成音（SE_SET=synth）に自動で切り替わる"
if curl -s -m 3 "${VOICEVOX_URL:-http://127.0.0.1:50021}/version" >/dev/null 2>&1; then ok "VOICEVOX エンジン $(curl -s ${VOICEVOX_URL:-http://127.0.0.1:50021}/version)"
elif [ -n "$(ls audio/vo_temp/*.wav 2>/dev/null)" ]; then alt "VOICEVOX は動いていないが、仮ナレの wav は audio/vo_temp/ にある（そのまま使える）"
else ng "VOICEVOX が動いていない、仮ナレの wav も無い → playbook/50_environment.md §3"; fi
