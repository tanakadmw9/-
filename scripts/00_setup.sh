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
source scripts/lib_env.sh   # 前に作った .venv があれば、ここで使い始める
# Python の部品：すでに入っていればそのまま。無ければ .venv を作ってそこに入れる（PEP 668 の「外部管理」の Python でも止まらない）。
# 版は v4.10 と同じ requirements.lock を先に試し、入らなければ下限だけの requirements.txt
if ! python3 -c "import numpy,scipy,soundfile,cv2,PIL,librosa,matplotlib" 2>/dev/null; then
  [ -x .venv/bin/python ] || python3 -m venv .venv || { echo "venv を作れません。Ubuntu／WSL では sudo apt-get install -y python3-venv（版つきなら python3.12-venv）"; exit 1; }
  .venv/bin/python -m pip install -r requirements.lock || .venv/bin/python -m pip install -r requirements.txt
  echo "Python の部品は .venv に入れた。scripts/*.sh は自動で使う。python3 を直接呼ぶ前に：source .venv/bin/activate"
  source scripts/lib_env.sh
fi
bash scripts/03_fonts_css.sh
if [ -z "${HYPERFRAMES_BROWSER_PATH:-}" ]; then
  echo "Chromium が見つからないので HyperFrames に用意させます（npx hyperframes browser ensure）"
  npx hyperframes browser ensure || echo "WARNING: Chrome を用意できませんでした。HYPERFRAMES_BROWSER_PATH に Chrome/Chromium の実行ファイルを指定してください"
fi
mkdir -p source/music assets/se/tones assets/se/foley
bash scripts/00_doctor.sh
