#!/usr/bin/env bash
# 書き出しを参考の書き出し（既定は v4.10）と比べる。再現の確認に使う（prompts/00 の指示文 A）。
#   bash scripts/46_compare_ref.sh <新しい.mp4> [参考.mp4 既定 reference/renders/kijunten_v4.10.mp4] [出力フォルダ]
# 合格：音がビット一致（デコードした PCM の MD5 が同じ）、映像は全コマ PSNR 45 dB 以上、コマ数が同じ。
# 同じ機械なら映像も全コマ一致する。別の機械では D1→D2 の写真が倒れる区間（27.4〜35.4 秒）に
# 目では区別できない差（PSNR 46〜60 dB）が出る。Chromium の描画が機械で少し変わるため（推測）。QC の総合 PASS は qc/<版>/report.md で別に見る。
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/lib_env.sh
NEW=${1:?比べる mp4 を指定}; REF=${2:-reference/renders/kijunten_v4.10.mp4}
OUT=${3:-qc/compare/$(basename "${NEW%.*}")}
[ -f "$REF" ] || { echo "参考の書き出し $REF がありません（media の zip の reference/renders/）"; exit 1; }
mkdir -p "$OUT"
ffmpeg -hide_banner -nostats -loglevel error -i "$NEW" -i "$REF" \
  -lavfi "[0:v]setpts=PTS-STARTPTS[a];[1:v]setpts=PTS-STARTPTS[b];[a][b]psnr=stats_file=$OUT/psnr.log" -f null -
ffmpeg -hide_banner -loglevel error -i "$NEW" -map 0:v -f framemd5 "$OUT/new_v.md5"
ffmpeg -hide_banner -loglevel error -i "$REF" -map 0:v -f framemd5 "$OUT/ref_v.md5"
ffmpeg -hide_banner -loglevel error -i "$NEW" -map 0:a -f md5 "$OUT/new_a.md5"
ffmpeg -hide_banner -loglevel error -i "$REF" -map 0:a -f md5 "$OUT/ref_a.md5"
python3 - "$OUT" <<'PY'
import sys, math, pathlib
o = pathlib.Path(sys.argv[1])
h = lambda p: [l.split(',')[-1].strip() for l in open(o / p) if not l.startswith('#')]
a, b = h("new_v.md5"), h("ref_v.md5")
n = min(len(a), len(b)); diff = [i for i in range(n) if a[i] != b[i]]
ps = []
for l in open(o / "psnr.log"):
    kv = dict(x.split(":", 1) for x in l.split())
    v = kv.get("psnr_avg", "inf"); ps.append(math.inf if v == "inf" else float(v))
fps = 30000 / 1001
low = [i for i, v in enumerate(ps) if v < 45]
fin = [v for v in ps if v != math.inf]
same_a = (o / "new_a.md5").read_text().strip() == (o / "ref_a.md5").read_text().strip()
lines = [f"コマ数：{len(a)} / 参考 {len(b)}",
         f"映像：同一のコマ {n - len(diff)}、違うコマ {len(diff)}" + (f"（{diff[0]}〜{diff[-1]} コマ＝{diff[0]/fps:.2f}〜{diff[-1]/fps:.2f} 秒）" if diff else ""),
         f"映像の PSNR：最低 {min(fin):.1f} dB（{ps.index(min(fin))} コマ）、45 dB 未満 {len(low)} コマ" if fin else "映像の PSNR：全コマ同一",
         f"音（デコードした PCM の MD5）：{'一致' if same_a else '違う'}"]
ok = len(a) == len(b) and not low and same_a
lines.append(f"判定：{'合格' if ok else '不合格'}（音のビット一致、映像の全コマ PSNR 45 dB 以上、コマ数が同じ）")
(o / "result.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
sys.exit(0 if ok else 1)
PY
