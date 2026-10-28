#!/usr/bin/env bash
# 環境の差（クラウド／Mac／Windows の WSL）を吸収する共通設定。ほかのスクリプトから source する。
# 外部には何も送らない。HyperFrames のテレメトリは止める。
export HYPERFRAMES_NO_TELEMETRY=1 DO_NOT_TRACK=1 HYPERFRAMES_NO_UPDATE_CHECK=1
# 1) Chromium：HYPERFRAMES_BROWSER_PATH が空なら、よくある場所を順に探す。見つからなければ HyperFrames 自身の探し方に任せる
if [ -z "${HYPERFRAMES_BROWSER_PATH:-}" ]; then
  for c in /opt/pw-browsers/chromium-*/chrome-linux64/chrome /opt/pw-browsers/chromium \
           "$HOME"/.cache/ms-playwright/chromium-*/chrome-linux*/chrome \
           "$HOME"/.cache/puppeteer/chrome-headless-shell/*/chrome-headless-shell-*/chrome-headless-shell \
           /usr/bin/chromium /usr/bin/chromium-browser /usr/bin/google-chrome \
           "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"; do
    if [ -x "$c" ]; then export HYPERFRAMES_BROWSER_PATH="$c"; break; fi
  done
fi
# 2) タイムコードを焼く欧文フォント（ffmpeg drawtext 用）
if [ -z "${FONT_LATIN:-}" ]; then
  for c in /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf /System/Library/Fonts/Supplemental/Arial.ttf \
           /mnt/c/Windows/Fonts/arial.ttf "$(dirname "${BASH_SOURCE[0]}")/../tools/fonts/BIZUDPGothic-Regular.ttf"; do
    if [ -f "$c" ]; then export FONT_LATIN="$c"; break; fi
  done
fi
