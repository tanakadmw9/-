# source/（元素材。リポジトリには入れない＝.gitignore）

ここに置いたものは**変更・削除しない**。

| ファイル | 中身 | 入手 | v4.10 で使ったものの MD5 |
|---|---|---|---|
| `input.mp4` | 元映像（基準点測量、約40秒、1920×1080、29.97fps、テロップと BGM の焼き込みあり。音声は使わない） | media の zip（kijunten_media.zip）の `source/input.mp4`、または社内 | `121a60a651d6557ff6797b6a75427578` |
| `music/01_new_departure.mp3` | BGM「New Departure」（FLASH☆BEAT、約93.5秒） | 下の手順で人がダウンロード | `8d7ce3d66e0150a07478bce834e37900` |

確かめ方：`md5sum source/input.mp4 source/music/01_new_departure.mp3`（Mac は `md5`）。`bash scripts/00_doctor.sh` も比べる。違っても動くが、v4.10 と同じ音・画にはならない（配布元で差し替えられた、など）。

## BGM の入手（OpenTracks、旧 DOVA-SYNDROME）
1. https://opentracks.com/bgm/detail/6843 を開き、規約（音源利用ライセンス）を読む。要点（2026-10-27 確認）：商用・法人可、クレジット表示不要（任意で「FLASH☆BEAT」）、編集・フェード可。**禁止：音源を主役にする使い方、再配布、AI 学習**。
2. ダウンロードして `source/music/01_new_departure.mp3` という名前で置く（`mkdir -p source/music`）。
3. 規約の確認日を docs/credits_and_licenses.md に書く（書いてある行の日付を更新）。

曲を置かなくても、自作の仮BGM（scripts/33_make_temp_bgm.py、同じテンポで合成）で全体は動く。ただし v4.10 と同じ音にはならず、自動QC の「ナレとBGMの差」が FAIL になる（想定どおり）。
