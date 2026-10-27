#!/usr/bin/env bash
# @fontsource の CSS を、プロジェクト内パス（assets/fonts/）を参照する comp/styles/fonts.css にまとめる。
set -euo pipefail
cd "$(dirname "$0")/.."
OUT=comp/styles/fonts.css
: > $OUT
for f in node_modules/@fontsource/biz-udpgothic/400.css node_modules/@fontsource/biz-udpgothic/700.css node_modules/@fontsource/biz-udgothic/400.css node_modules/@fontsource/biz-udgothic/700.css; do
  sed -E "s#url\(\./files/([^)]*)\.woff2\) format\('woff2'\), url\(\./files/[^)]*\.woff\) format\('woff'\)#url('assets/fonts/\1.woff2') format('woff2')#; s/font-display: swap/font-display: block/" "$f" >> $OUT
done
grep -c "@font-face" $OUT
