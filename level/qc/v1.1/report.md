# QC report v1.1

- 対象: `renders/draft/v1.1.mp4`
- 計画尺: 60.6606 s（comp/timeline.json）
- 総合: **FAIL**

| 項目 | 判定 | 要約 |
|---|---|---|
| 仕様（ffprobe） | ✅ PASS | すべて一致 |
| 黒コマ（blackdetect） | ✅ PASS | 意図外 0 件／全 1 件 |
| 意図しない静止（freezedetect） | ⚠️ WARN | 実写で意図外 0 件、図解の静止 11 件（目視）、意図どおり 4 件 |
| 焼き込みテロップの漏れ（4fps） | ✅ PASS | 検出 0 フレーム |
| 1コマの黒（平均輝度<8） | ❌ FAIL | 1 コマ（00:45.48） |
| 点滅（>3回/秒） | ✅ PASS | 最大 1 回/秒 @ 00:45.48 |
| 画面の文字の表示時間 | ❌ FAIL | 合格 25、例外 6（理由つき）、不合格 4／全 35 |
| hyperframes check（lint・はみ出し・コントラストほか） | ✅ PASS | exit 0、lint: ok／runtime: ok／layout: ok／motion: ok／contrast: ok／craft: ok／audio: ok |
| ラウドネス（ebur128） | ✅ PASS | I -24.0 LUFS, TP -9.4 dBTP |
| ナレとBGMの差（ステム） | ❌ FAIL | 行ごと最小 15.9 dB、短時間窓 p5 14.5 dB（audio/mix のステム。レンダーの音声が同じ mix か確認すること） |
| プチノイズ（mix.wav の不連続） | ✅ PASS | 継ぎ目などの候補 0 件、声の中（子音・要試聴）0 件、SE の位置 0 件 |
| カットと拍（格子） | ✅ PASS | 12/12 が拍の1コマ前 ±1.5コマ以内 |
| 【要監修】 | ⚠️ WARN | 合計 2（最終版でゼロ） |
| 音の素材 | ✅ PASS | BGM：選曲（audio/bgm/bgm.wav）、効果音：効果音ラボ |
| 素材台帳 | ❌ FAIL | 未記載: フォント BIZ UDPゴシック／UDゴシック、GSAP、HyperFrames、BGM（選曲） |

## 1. 仕様（ffprobe）

| 項目 | 実測 | 基準 | 判定 |
|---|---|---|---|
| 解像度 | 1920×1080 | 1920×1080 | OK |
| フレームレート | 30000/1001 | 30000/1001 | OK |
| 映像コーデック | h264 | h264 | OK |
| 画素形式 | yuv420p | yuv420p | OK |
| 音声コーデック | aac | aac | OK |
| サンプリング | 48000 | 48000 | OK |
| チャンネル | 2 | 2 | OK |
| 尺 | 60.661s | 60.661±0.1s | OK |
| 映像と音の長さ | V 60.661s / A 60.650s | 差 ≤0.1s | OK |

## 2. 黒コマ（blackdetect d≥0.1s, pix_th 0.10）

- 01:00.49–01:00.63（0.13s）意図（エンドカードのフェード） — endcard(overlay)

## 3. 静止（freezedetect n=-60dB, d≥0.5s）

timeline.intended_freezes: 00:02.50–00:07.54 L01_still; 00:25.89–00:29.43 L11_still（人が離れたレベルに目線の点線を引く静止）; 00:56.16–01:00.66 endcard（L10 の最後のコマ）

図解（ポスター風の静止を含む）やエンドカードは、動きの合間に正当に静止しうる。実写区間の意図外の静止は不具合の疑い。

- 00:01.50–00:02.04（0.53s）図解・エンドカードの静止（要目視：動きが止まって見えないか） — chapter_door
- 00:16.55–00:17.12（0.57s）図解・エンドカードの静止（要目視：動きが止まって見えないか） — d0_benchmark
- 00:17.12–00:18.85（1.74s）図解・エンドカードの静止（要目視：動きが止まって見えないか） — d0_benchmark
- 00:18.85–00:20.19（1.33s）図解・エンドカードの静止（要目視：動きが止まって見えないか） — d0_benchmark
- 00:26.13–00:27.89（1.77s）意図どおり（L11_still（人が離れたレベルに目線の点線を引く静止）） — d2_level
- 00:27.89–00:29.50（1.60s）意図どおり（L11_still（人が離れたレベルに目線の点線を引く静止）） — d2_level
- 00:30.90–00:31.43（0.53s）図解・エンドカードの静止（要目視：動きが止まって見えないか） — d2_level
- 00:31.66–00:33.13（1.47s）図解・エンドカードの静止（要目視：動きが止まって見えないか） — d2_level
- 00:34.10–00:36.30（2.20s）図解・エンドカードの静止（要目視：動きが止まって見えないか） — d2_level
- 00:36.30–00:37.87（1.57s）図解・エンドカードの静止（要目視：動きが止まって見えないか） — d2_level
- 00:45.81–00:47.65（1.84s）図解・エンドカードの静止（要目視：動きが止まって見えないか） — d3_relay
- 00:48.52–00:49.52（1.00s）図解・エンドカードの静止（要目視：動きが止まって見えないか） — d3_relay
- 00:49.52–00:50.52（1.00s）図解・エンドカードの静止（要目視：動きが止まって見えないか） — d3_relay
- 00:57.62–00:58.39（0.77s）意図どおり（endcard（L10 の最後のコマ）） — endcard(overlay)
- 00:58.39–01:00.19（1.80s）意図どおり（endcard（L10 の最後のコマ）） — endcard(overlay)

## 4. 焼き込みテロップの漏れ

条件：4fps・全画面、HSV H 100–125, S≥150, V≥170、連結面積 ≥3000px、成分内 S 中央値 ≥190。元素材でテロップは S≈240/V≈250、実写の紺TSは S≈124/V≈157（除外）。

検出なし

## 5. 点滅

平均輝度（0–255）の隣接フレーム変化 ≥25 を遷移とし、向きが逆の遷移2つで1回。最大 1 回/秒。
大きな遷移 15 件（カット・フェード含む）: 00:02.50(-113.9), 00:13.88(-25.1), 00:15.15(+143.7), 00:20.19(-123.2), 00:37.87(-115.8), 00:45.48(-111.0), 00:45.51(+58.5), 00:45.55(+50.5), 00:45.58(+38.5), 00:45.61(+30.3), 00:50.52(-122.9), 00:56.82(+25.1), 01:00.36(-32.4), 01:00.39(-33.8), 01:00.43(-31.6)

## 6. 画面の文字（表示時間 ≥ 文字数÷4＋1.0秒、かつ ≥1.5秒）

`scripts/44_text_timing.mjs` で書き出しと同じページを 0.05 秒ごとに止め、文字が読める濃さ（見え方 ≥0.6：不透明度の積と、上に重なる紙・黒などの覆い）で出ている最長の区間を測った（`text_timing.json`）。文字数は引用符・括弧・句読点を数えない。

| 出 | 消 | 場面 | 文 | 文字数 | 表示 | 必要 | 判定 |
|---|---|---|---|---|---|---|---|
| 00:00.25 | 00:07.55 | chapter_door→title | 測量部門のしごと | 8 | 7.30s | 3.0s | OK |
| 00:00.75 | 00:02.15 | chapter_door | 基準点測量 | 5 | 1.40s | 2.25s | 例外：章扉の作業名は「5つのうち1つが灯る」形を見せる1回目。締めの章扉でもう一度読める |
| 00:00.85 | 00:02.10 | chapter_door | 水準測量 | 4 | 1.25s | 2.0s | 例外：章扉の作業名は「5つのうち1つが灯る」形を見せる1回目。締めの章扉でもう一度読める |
| 00:00.95 | 00:02.15 | chapter_door | 地形測量 | 4 | 1.20s | 2.0s | 例外：章扉の作業名は「5つのうち1つが灯る」形を見せる1回目。締めの章扉でもう一度読める |
| 00:01.05 | 00:02.15 | chapter_door | 路線測量 | 4 | 1.10s | 2.0s | 例外：章扉の作業名は「5つのうち1つが灯る」形を見せる1回目。締めの章扉でもう一度読める |
| 00:01.15 | 00:02.15 | chapter_door | 用地測量 | 4 | 1.00s | 2.0s | 例外：章扉の作業名は「5つのうち1つが灯る」形を見せる1回目。締めの章扉でもう一度読める |
| 00:04.15 | 00:07.55 | title | 水準測量 | 4 | 3.40s | 2.0s | OK |
| 00:04.25 | 00:07.55 | title | “高さ”をはかる | 6 | 3.30s | 2.5s | OK |
| 00:16.45 | 00:20.20 | d0_benchmark | 水準点 | 3 | 3.75s | 1.75s | OK |
| 00:16.45 | 00:20.20 | d0_benchmark | 高さがわかっている点 | 10 | 3.75s | 3.5s | OK |
| 00:20.75 | 00:23.85 | k_labels | レベル | 3 | 3.10s | 1.75s | OK |
| 00:20.75 | 00:23.85 | k_labels | 高さをはかる機械 | 8 | 3.10s | 3.0s | OK |
| 00:21.00 | 00:23.85 | k_labels | 標尺 | 2 | 2.85s | 1.5s | OK |
| 00:21.00 | 00:23.85 | k_labels | 目盛りのついたものさし | 11 | 2.85s | 3.75s | NG |
| 00:30.45 | 00:37.90 | d2_level | 水準点 | 3 | 7.45s | 1.75s | OK |
| 00:32.40 | 00:37.90 | d2_level | 0 | 1 | 5.50s | 1.5s | OK |
| 00:33.20 | 00:37.90 | d2_level | 数字は例です | 6 | 4.70s | 2.5s | OK |
| 00:33.50 | 00:37.90 | d2_level | 1.2m | 4 | 4.40s | 2.0s | OK |
| 00:33.90 | 00:37.90 | d2_level | 目盛りが大きいほうが、低い | 12 | 4.00s | 4.0s | OK |
| 00:34.10 | 00:37.90 | d2_level | 1.8m | 4 | 3.80s | 2.0s | OK |
| 00:36.40 | 00:37.90 | d2_level | 0.6m | 4 | 1.50s | 2.0s | NG |
| 00:36.40 | 00:37.90 | d2_level | 0.6m低い | 6 | 1.50s | 2.5s | NG |
| 00:45.60 | 00:50.55 | d3_relay | 10.00m | 6 | 4.95s | 2.5s | OK |
| 00:45.60 | 00:50.55 | d3_relay | 水準点 | 3 | 4.95s | 1.75s | OK |
| 00:45.60 | 00:50.55 | d3_relay | 数字は例です | 6 | 4.95s | 2.5s | OK |
| 00:46.05 | 00:50.55 | d3_relay | 9.40m | 5 | 4.50s | 2.25s | OK |
| 00:49.60 | 00:50.55 | d3_relay | 9.75m | 5 | 0.95s | 2.25s | NG |
| 00:50.80 | 01:00.40 | endcard | 見えない水平の線で、 | 9 | 9.60s | 3.25s | OK |
| 00:50.80 | 01:00.40 | endcard | 高さをつないでいく | 9 | 9.60s | 3.25s | OK |
| 00:57.10 | 01:00.40 | endcard | 水準測量 | 4 | 3.30s | 2.0s | OK |
| 00:57.35 | 01:00.40 | endcard | 基準点測量 | 5 | 3.05s | 2.25s | OK |
| 00:57.35 | 01:00.40 | endcard | 地形測量 | 4 | 3.05s | 2.0s | OK |
| 00:57.45 | 01:00.40 | endcard | 路線測量 | 4 | 2.95s | 2.0s | OK |
| 00:57.50 | 01:00.40 | endcard | ナレーション（仮）VOICEVOX:冥鳴ひまり | 20 | 2.90s | 6.0s | 例外：仮ナレの規約上の表示。本ナレに差し替えたら消す |
| 00:57.50 | 01:00.40 | endcard | 用地測量 | 4 | 2.90s | 2.0s | OK |

3コマ（出た直後／中間／消える直前、上の表の順に番号。オレンジの枠＝測った文字の位置）: `text_strips_1of5.jpg`, `text_strips_2of5.jpg`, `text_strips_3of5.jpg`, `text_strips_4of5.jpg`, `text_strips_5of5.jpg`

`npx hyperframes check comp --json` の要約：

```
lint: ok（エラー 0・警告 0・情報 0）
runtime: ok（エラー 0・警告 0・情報 0）
layout: ok（エラー 0・警告 0・情報 0）
motion: ok（エラー 0・警告 0・情報 0）
contrast: ok（エラー 0・警告 3・情報 0、コントラスト 3/6 合格）
  - [warning] contrast_aa_failure @57.29s div > div:nth-of-type(7) > div > div:nth-of-type(1) > div:nth-of-type(4) > div:nth-of-type(2) > div：Contrast is 1.54:1; WCAG AA requires 3:1.
  - [warning] contrast_aa_failure @57.29s div > div:nth-of-type(7) > div > div:nth-of-type(1) > div:nth-of-type(6) > div:nth-of-type(3) > div:nth-of-type(1)：Contrast is 2:1; WCAG AA requires 3:1.
  - [warning] contrast_aa_failure @57.29s div > div:nth-of-type(7) > div > div:nth-of-type(1) > div:nth-of-type(6) > div:nth-of-type(3) > div:nth-of-type(2)：Contrast is 1.6:1; WCAG AA requires 3:1.
craft: ok（エラー 0・警告 1・情報 0）
  - [warning] line_unread @49.57s #d3-h2："9.75 m" (3 words) is on screen 0.97 s (±0.01 s), under its 1.05 s floor: hold it about 0.5 s + 0.3 s a word (1.40 s here) before it leaves or changes; see refe
audio: ok（エラー 0・警告 0・情報 0）
```

## 7. ラウドネス（ffmpeg ebur128=peak=true）

- 統合 -24.0 LUFS（基準 −24±1）、True Peak -9.4 dBTP（基準 ≤−2）、LRA 4.6 LU

## 8. ナレとBGMの差（audio/mix のステム）

行ごと：VO の統合ラウドネス − 同区間の BGM 平均ラウドネス（基準 ≥15 dB、設計 15〜18 dB 下）

| 行 | 差 dB |
|---|---|
| N1a | 20.2 |
| N1b | 18.4 |
| N2 | 17.4 |
| N3 | 17.7 |
| N4 | 16.2 |
| N5a | 15.9 |
| N5b | 17.0 |
| N6 | 16.7 |
| N7 | 16.7 |
| N8 | 21.8 |

3秒短時間ラウドネス（窓がナレ1行に完全に入る 154 点）：中央値 16.1 dB、p5 14.5 dB、最小 14.1 dB

ステムの推移: `levels.png`

## 9. プチノイズ候補（audio/mix/mix.wav）

- なし

## 9b. カットと拍（timeline.grid）

| カット | 小節・拍 | ずれ（コマ、拍の1コマ前＝0） |
|---|---|---|
| 00:07.54 | 4小節1拍 | -0.29 |
| 00:10.08 | 5小節1拍 | -0.05 |
| 00:13.88 | 6小節3拍 | +0.3 |
| 00:15.15 | 7小節1拍 | +0.42 |
| 00:20.19 | 9小節1拍 | -0.11 |
| 00:23.99 | 10小節3拍 | +0.25 |
| 00:25.89 | 11小節2拍 | +0.43 |
| 00:37.87 | 16小節1拍 | -0.44 |
| 00:40.41 | 17小節1拍 | -0.21 |
| 00:42.94 | 18小節1拍 | +0.03 |
| 00:45.48 | 19小節1拍 | +0.27 |
| 00:50.52 | 21小節1拍 | -0.26 |

## 10. 【要監修】の数

- `comp/narration.json`: 0
- `docs/08_build_spec.md`: 0
- `comp/compositions/chapter_door.html`: 0
- `comp/compositions/d0_benchmark.html`: 0
- `comp/compositions/d2_level.html`: 1
- `comp/compositions/d3_relay.html`: 1
- `comp/compositions/endcard.html`: 0
- `comp/compositions/k_labels.html`: 0
- `comp/compositions/telop_keyword.html`: 0
- `comp/compositions/title.html`: 0

## 11. 素材台帳（docs/credits_and_licenses.md）

- フォント BIZ UDPゴシック／UDゴシック: **未記載**（確認語: BIZ UDPゴシック, BIZ UDゴシック）
- GSAP: **未記載**（確認語: GSAP）
- HyperFrames: **未記載**（確認語: HyperFrames）
- 仮ナレ（音声合成）: 記載あり（確認語: VOICEVOX, 冥鳴ひまり）
- 効果音: 記載あり（確認語: 効果音）
- 環境音: 記載あり（確認語: 環境音）
- BGM（選曲）: **未記載**（確認語: bgm.wav）

## 12. 目視用シート

- `contact_0p5s_1of3.jpg`, `contact_0p5s_2of3.jpg`, `contact_0p5s_3of3.jpg`（0.5秒おき、8列×7行、コマの下にタイムコード）
- 画面の文字の3コマ（§6）: `text_strips_1of5.jpg`, `text_strips_2of5.jpg`, `text_strips_3of5.jpg`, `text_strips_4of5.jpg`, `text_strips_5of5.jpg`
- 絵コンテとの比較・`snapshot --review`（場面の頭＋0.3秒と中間、カットの前後5コマ、スマホ幅）: `hf_review/review-beats-1.jpg`, `hf_review/review-beats-2.jpg`, `hf_review/review-phone-1.jpg`, `hf_review/review-phone-2.jpg`, `hf_review/review-seam-01.jpg`, `hf_review/review-seam-02.jpg`, `hf_review/review-seam-03.jpg`, `hf_review/review-seam-04.jpg`, `hf_review/review-seam-05.jpg`, `hf_review/review-seam-06.jpg`, `hf_review/review-seam-07.jpg`, `hf_review/review-seam-08.jpg`, `hf_review/review-seam-09.jpg`, `hf_review/review-seam-10.jpg`, `hf_review/review-seam-11.jpg`, `hf_review/review-seam-12.jpg`, `hf_review/review-seam-13.jpg`, `hf_review/review-seam-14.jpg`

## 自動化していない項目（人間・目視）

- 言葉と絵の同期（キーワード発話時刻 vs 図解の動き ±0.3s）：vo_timing.json と scenes.cues の比較は別途
- 音の聞こえ方（BGMの選曲・間・SEの質感・環境音の自然さ）は試写で耳で判断
