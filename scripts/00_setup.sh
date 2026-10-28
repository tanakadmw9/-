#!/usr/bin/env bash
# フェーズ0：環境を整える（何度実行してもよい）。外部に素材は送らない。
#   bash scripts/00_setup.sh
# やること：npm ci（HyperFrames 0.8.206 などを package-lock どおりに）→ テレメトリ停止 → Python の部品 →
#           フォントと GSAP を comp/ に置く → Chromium を用意 → 環境チェック（00_doctor.sh）
set -euo pipefail
cd "$(dirname "$0")/.."
command -v node >/dev/null || { echo "Node.js 22 以上を入れてください（https://nodejs.org）"; exit 1; }
command -v ffmpeg >/dev/null || { echo "FFmpeg を入れてください（Ubuntu: sudo apt-get install -y ffmpeg ／ Mac: brew install ffmpeg）"; exit 1; }
npm ci --no-audit --no-fund
npx hyperframes telemetry disable || true
python3 -m pip install -r requirements.txt
bash scripts/03_fonts_css.sh
source scripts/lib_env.sh
if [ -z "${HYPERFRAMES_BROWSER_PATH:-}" ]; then
  echo "Chromium が見つからないので HyperFrames に用意させます（npx hyperframes browser ensure）"
  npx hyperframes browser ensure || echo "WARNING: Chrome を用意できませんでした。HYPERFRAMES_BROWSER_PATH に Chrome/Chromium の実行ファイルを指定してください"
fi
mkdir -p source/music assets/se
bash scripts/00_doctor.sh
