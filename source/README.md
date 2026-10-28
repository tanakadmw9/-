# source/（元素材。リポジトリには入れない＝.gitignore）

ここに置いたものは**変更・削除しない**。

| ファイル | 中身 | 入手 |
|---|---|---|
| `input.mp4` | 元映像（基準点測量、約40秒、1920×1080、29.97fps、テロップと BGM の焼き込みあり。音声は使わない） | media の zip（kijunten_media.zip）の `source/input.mp4`、または社内 |
| `music/01_new_departure.mp3` | BGM「New Departure」（FLASH☆BEAT、約93.5秒） | 下の手順で人がダウンロード |

## BGM の入手（OpenTracks、旧 DOVA-SYNDROME）
1. https://opentracks.com/bgm/detail/6843 を開き、規約（音源利用ライセンス）を読む。要点（2026-10-27 確認）：商用・法人可、クレジット表示不要（任意で「FLASH☆BEAT」）、編集・フェード可。**禁止：音源を主役にする使い方、再配布、AI 学習**。
2. ダウンロードして `source/music/01_new_departure.mp3` という名前で置く。
3. 規約の確認日を docs/credits_and_licenses.md に書く（書いてある行の日付を更新）。

曲を置かなくても、自作の仮BGM（scripts/33_make_temp_bgm.py、同じテンポで合成）で全体は動く。ただし v4.10 と同じ音にはならない。
