#!/usr/bin/env bash
# ハンドオフの zip を2つ作る（README.md「何が入っているか」）。
#   bash scripts/80_handoff_zips.sh <出力フォルダ> [参考に入れる書き出し.mp4 ...]
# 1) kijunten_kit.zip  ：コミット済みの中身（git archive HEAD）から、元映像から作った画像（*.jpg・*.png、storyboard/index.html）を除いたもの
# 2) kijunten_media.zip：元映像 source/input.mp4、仮ナレ audio/vo_temp/*.wav、除いた画像、計画の絵コンテ plan/editing_storyboard.png、
#                        引数の書き出し（reference/renders/ に入れる）
# 再配布禁止の素材（assets/se/、source/music/）はどちらにも入れない。
set -euo pipefail
cd "$(dirname "$0")/.."
OUT=$(mkdir -p "${1:?出力フォルダ}" && cd "$1" && pwd); shift
[ -z "$(git status --porcelain)" ] || echo "WARNING: コミットしていない変更は kit の zip に入らない"
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
EXCL=(':(exclude,glob)**/*.jpg' ':(exclude,glob)**/*.png' ':(exclude)storyboard/index.html')
git archive --format=tar --prefix=kijunten_kit/ HEAD -- . "${EXCL[@]}" | tar -x -C "$TMP"
(cd "$TMP" && rm -f "$OUT/kijunten_kit.zip" && zip -qr -X "$OUT/kijunten_kit.zip" kijunten_kit)
M="$TMP/media/kijunten_kit"; mkdir -p "$M"
git ls-files -- '*.jpg' '*.png' storyboard/index.html | while read -r f; do mkdir -p "$M/$(dirname "$f")"; cp "$f" "$M/$f"; done
for f in source/input.mp4 plan/editing_storyboard.png; do [ -f "$f" ] && { mkdir -p "$M/$(dirname "$f")"; cp "$f" "$M/$f"; } || echo "（無いので入れない：$f）"; done
if ls audio/vo_temp/*.wav >/dev/null 2>&1; then mkdir -p "$M/audio/vo_temp"; cp audio/vo_temp/*.wav "$M/audio/vo_temp/"; fi
mkdir -p "$M/reference/renders"; for r in "$@"; do cp "$r" "$M/reference/renders/"; done
cat > "$M/MEDIA_README.md" <<'EOF2'
# kijunten_media.zip（社内映像と、そこから作ったもの）

kijunten_kit.zip と同じ場所に展開して、同じ kijunten_kit/ フォルダに重ねる。
- source/input.mp4：元映像（変更・削除しない）
- audio/vo_temp/*.wav：v4.10 の仮ナレ（VOICEVOX:冥鳴ひまり。クレジット要）。VOICEVOX が無い環境でもこのまま使える
- reference/renders/：v4.10 と B案の書き出し（見比べ用）
- qc/・analysis/・storyboard/・plan/ の画像：各版の検査シート、素材分析のシート、絵コンテ

社内映像を含むので、AI サービスや社外に渡すかは会社の規程で判断する。
EOF2
(cd "$TMP/media" && rm -f "$OUT/kijunten_media.zip" && zip -qr -X "$OUT/kijunten_media.zip" kijunten_kit)
ls -l "$OUT"/kijunten_kit.zip "$OUT"/kijunten_media.zip
