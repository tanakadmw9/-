#!/usr/bin/env bash
# 環境チェック：何がそろっていて、何が足りないか。足りないものは「代わり」で動くかも示す。
#   bash scripts/00_doctor.sh
cd "$(dirname "$0")/.."
source scripts/lib_env.sh
ok(){ printf "  ✅ %s\n" "$1"; }; ng(){ printf "  ❌ %s\n" "$1"; }; alt(){ printf "  ⚠️  %s\n" "$1"; }
echo "■ ツール"
command -v node >/dev/null && ok "Node $(node -v)" || ng "Node.js（22 以上）"
command -v ffmpeg >/dev/null && ok "$(ffmpeg -version | head -1 | cut -c1-40)" || ng "FFmpeg"
python3 -c "import numpy,scipy,soundfile,cv2,PIL,librosa,matplotlib" 2>/dev/null && ok "Python の部品（requirements.txt）$([ -n "${VIRTUAL_ENV:-}" ] && echo "、.venv")" || ng "Python の部品：bash scripts/00_setup.sh（または python3 -m pip install -r requirements.txt）"
[ -f node_modules/hyperframes/package.json ] && v=$(node -p "require('./node_modules/hyperframes/package.json').version") && { [ "$v" = 0.8.206 ] && ok "HyperFrames $v（固定版）" || ng "HyperFrames $v（0.8.206 に固定すること。scripts/44_text_timing.mjs が内部のファイル名に依存）"; } || ng "HyperFrames：npm ci"
[ -n "${HYPERFRAMES_BROWSER_PATH:-}" ] && ok "Chromium: $HYPERFRAMES_BROWSER_PATH" || alt "Chromium を自動では見つけられない → npx hyperframes browser ensure、または HYPERFRAMES_BROWSER_PATH を指定"
[ -f comp/assets/vendor/gsap.min.js ] && [ -n "$(ls comp/assets/fonts/*.woff2 2>/dev/null)" ] && ok "フォントと GSAP（comp/assets）" || ng "フォントと GSAP：bash scripts/03_fonts_css.sh"
echo "■ 素材（リポジトリに入れないもの。置き方は source/README.md と assets/README.md）"
[ -f source/input.mp4 ] && ok "元映像 source/input.mp4" || ng "元映像 source/input.mp4（media の zip か社内から）"
[ -f source/music/01_new_departure.mp3 ] || [ -f audio/bgm/bgm.wav ] && ok "BGM（New Departure）" || alt "BGM が無い → 自作の仮BGM（scripts/33_make_temp_bgm.py）で代用。テンポは格子どおりだが曲の山がないので、QC の「ナレとBGMの差」は FAIL になりやすい（想定どおり）"
n=0; for f in tones/decision28.mp3 tones/decision6.mp3 tones/cursor3.mp3 foley/mechanical-pencil-write1.mp3; do [ -f "${SE_DIR:-assets/se}/$f" ] && n=$((n+1)); done
[ $n = 4 ] && ok "効果音ラボの効果音 4/4" || alt "効果音ラボの効果音 $n/4 → 自作の合成音（SE_SET=synth）に自動で切り替わる"
# 中身が v4.10 で使ったものと同じか（MD5。違っても動くが、同じ音・画にはならない）
md5of(){ if command -v md5sum >/dev/null; then md5sum "$1" | cut -d' ' -f1; else md5 -q "$1"; fi; }
same(){ [ -f "$1" ] && [ "$(md5of "$1")" != "$2" ] && alt "$1 の中身が v4.10 のものと違う（MD5）→ 動くが、v4.10 と同じにはならない"; }
same source/input.mp4 121a60a651d6557ff6797b6a75427578
same source/music/01_new_departure.mp3 8d7ce3d66e0150a07478bce834e37900
S=${SE_DIR:-assets/se}
same "$S/tones/decision28.mp3" 983bdc863054bee27d95cb24f2f34a70; same "$S/tones/decision6.mp3" 02103c784ed624fd7cdffa2ed59ac7b7
same "$S/tones/cursor3.mp3" 5b342ec9ef97c8c29afe31b0f7798008; same "$S/foley/mechanical-pencil-write1.mp3" 63f58b32e4d0405d359ebfad58136c79
if curl -s -m 3 "${VOICEVOX_URL:-http://127.0.0.1:50021}/version" >/dev/null 2>&1; then ok "VOICEVOX エンジン $(curl -s ${VOICEVOX_URL:-http://127.0.0.1:50021}/version)"
elif [ -n "$(ls audio/vo_temp/*.wav 2>/dev/null)" ]; then alt "VOICEVOX は動いていないが、仮ナレの wav は audio/vo_temp/ にある（そのまま使える）"
else ng "VOICEVOX が動いていない、仮ナレの wav も無い → playbook/50_environment.md §3"; fi
