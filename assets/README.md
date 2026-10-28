# assets/（外部の素材。リポジトリには入れない＝.gitignore）

## 効果音（効果音ラボ）— v4.10 で使った4つ
効果音ラボ https://soundeffect-lab.info/ の規約 https://soundeffect-lab.info/agreement/ を読んでから、人がダウンロードして次の名前で置く。
要点（2026-10-27 確認）：商用・法人無料、クレジット・報告不要、改変可。**禁止：再配布（素材そのものの配布、リポジトリへの公開も含む）、直リンク、AI 学習、Content ID・音商標の登録**。

| 置く場所 | 効果音ラボのファイル名 | 中身（素材担当のメモ） | 使う所 |
|---|---|---|---|
| `assets/se/tones/decision28.mp3` | decision28.mp3 | 鉄琴の生演奏 | 章扉でアイコンが灯る、新しい点が決まる |
| `assets/se/tones/decision6.mp3` | decision6.mp3 | 控えめの電子音 | 照準が合う「ピッ」 |
| `assets/se/tones/cursor3.mp3` | cursor3.mp3 | ピッ | 測距（D1 の光の線） |
| `assets/se/foley/mechanical-pencil-write1.mp3` | mechanical-pencil-write1.mp3 | シャーペンで書く | 地図の線が描かれる間（ごく小さく） |

ファイル名は、効果音ラボでダウンロードしたときの名前。サイトの中で、このファイル名の音を探して置く（試聴して中身のメモと合っているか確かめる）。
置き場所は環境変数 `SE_DIR` で変えられる（既定 `assets/se`）。

置かなかった場合は、自作の合成音（scripts/31_make_se.py）に自動で切り替わる（`SE_SET=auto`）。合成音は声と同じ高さの帯域にあり、ナレ中は聞こえにくい（playbook/40_pitfalls.md）。
