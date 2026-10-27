#!/usr/bin/env bash
# フォント・GSAP をプロジェクト内に配置し、@fontsource の CSS を、プロジェクト内パス（assets/fonts/）を参照する comp/styles/fonts.css にまとめる。
set -euo pipefail
cd "$(dirname "$0")/.."
OUT=comp/styles/fonts.css
mkdir -p comp/assets/fonts comp/assets/vendor
cp node_modules/@fontsource/biz-udpgothic/files/*.woff2 node_modules/@fontsource/biz-udgothic/files/*.woff2 comp/assets/fonts/
cp node_modules/@fontsource/biz-udpgothic/LICENSE comp/assets/fonts/OFL-biz-udpgothic.txt
cp node_modules/@fontsource/biz-udgothic/LICENSE comp/assets/fonts/OFL-biz-udgothic.txt
cp node_modules/gsap/dist/gsap.min.js comp/assets/vendor/
: > $OUT
for f in node_modules/@fontsource/biz-udpgothic/400.css node_modules/@fontsource/biz-udpgothic/700.css node_modules/@fontsource/biz-udgothic/400.css node_modules/@fontsource/biz-udgothic/700.css; do
  sed -E "s#url\(\./files/([^)]*)\.woff2\) format\('woff2'\), url\(\./files/[^)]*\.woff\) format\('woff'\)#url('assets/fonts/\1.woff2') format('woff2')#; s/font-display: swap/font-display: block/" "$f" >> $OUT
done
grep -c "@font-face" $OUT
