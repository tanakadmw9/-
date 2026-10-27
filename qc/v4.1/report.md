# QC report v4.1

- 対象: `renders/draft/v4.1.mp4`
- 計画尺: 81.1477 s（comp/timeline.json）
- 総合: **PASS**

| 項目 | 判定 | 要約 |
|---|---|---|
| 仕様（ffprobe） | ✅ PASS | すべて一致 |
| 黒コマ（blackdetect） | ✅ PASS | 意図外 0 件／全 0 件 |
| 意図しない静止（freezedetect） | ⚠️ WARN | 実写で意図外 0 件、図解の静止 19 件（目視）、意図どおり 4 件 |
| 焼き込みテロップの漏れ（4fps） | ✅ PASS | 検出 0 フレーム |
| 点滅（>3回/秒） | ✅ PASS | 最大 1 回/秒 @ 01:10.44 |
| テロップ表示時間 | ✅ PASS | 1/1 合格 |
| hyperframes check（はみ出し・コントラスト） | ✅ PASS | exit 0 |
| ラウドネス（ebur128） | ✅ PASS | I -24.0 LUFS, TP -9.5 dBTP |
| ナレとBGMの差（ステム） | ✅ PASS | 行ごと最小 18.6 dB、短時間窓 p5 16.4 dB（audio/mix のステム。レンダーの音声が同じ mix か確認すること） |
| プチノイズ（mix.wav の不連続） | ✅ PASS | SE以外の候補 0 件（SE位置 1 件は除外） |
| 【要監修】 | ⚠️ WARN | 合計 4（最終版でゼロ） |
| 素材台帳 | ✅ PASS | 漏れなし |

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
| 尺 | 81.148s | 81.148±0.1s | OK |
| 映像と音の長さ | V 81.114s / A 81.148s | 差 ≤0.1s | OK |

## 2. 黒コマ（blackdetect d≥0.1s, pix_th 0.10）

- なし

## 3. 静止（freezedetect n=-60dB, d≥0.5s）

timeline.intended_freezes: 00:10.01–00:13.21 S04_last; 00:27.56–00:33.77 S09_freeze（D1の背景）

図解（ポスター風の静止を含む）やエンドカードは、動きの合間に正当に静止しうる。実写区間の意図外の静止は不具合の疑い。

- 00:10.14–00:12.91（2.77s）意図どおり（S04_last） — title(overlay), still:S04_last
- 00:22.92–00:26.36（3.44s）図解・エンドカードの静止（要目視：動きが止まって見えないか） — d0_marker
- 00:28.53–00:29.50（0.97s）意図どおり（S09_freeze（D1の背景）） — d1_observe
- 00:29.73–00:31.40（1.67s）意図どおり（S09_freeze（D1の背景）） — d1_observe
- 00:31.40–00:33.20（1.80s）意図どおり（S09_freeze（D1の背景）） — d1_observe
- 00:35.20–00:36.80（1.60s）図解・エンドカードの静止（要目視：動きが止まって見えないか） — d2_topview
- 00:36.80–00:38.41（1.60s）図解・エンドカードの静止（要目視：動きが止まって見えないか） — d2_topview
- 00:38.41–00:39.04（0.63s）図解・エンドカードの静止（要目視：動きが止まって見えないか） — d2_topview
- 00:39.04–00:39.84（0.80s）図解・エンドカードの静止（要目視：動きが止まって見えないか） — d2_topview
- 00:39.84–00:40.74（0.90s）図解・エンドカードの静止（要目視：動きが止まって見えないか） — d2_topview
- 00:40.74–00:42.91（2.17s）図解・エンドカードの静止（要目視：動きが止まって見えないか） — d2_topview
- 00:43.78–00:45.11（1.33s）図解・エンドカードの静止（要目視：動きが止まって見えないか） — d3_traverse
- 00:45.11–00:46.58（1.47s）図解・エンドカードの静止（要目視：動きが止まって見えないか） — d3_traverse
- 00:47.55–00:49.22（1.67s）図解・エンドカードの静止（要目視：動きが止まって見えないか） — d3_traverse
- 00:49.22–00:49.95（0.73s）図解・エンドカードの静止（要目視：動きが止まって見えないか） — d3_traverse
- 00:53.52–00:54.25（0.73s）図解・エンドカードの静止（要目視：動きが止まって見えないか） — d4_bridge
- 00:54.25–00:55.62（1.37s）図解・エンドカードの静止（要目視：動きが止まって見えないか） — d4_bridge
- 00:55.62–00:56.26（0.63s）図解・エンドカードの静止（要目視：動きが止まって見えないか） — d4_bridge
- 00:56.72–01:01.26（4.54s）図解・エンドカードの静止（要目視：動きが止まって見えないか） — d4_bridge
- 01:01.63–01:02.20（0.57s）図解・エンドカードの静止（要目視：動きが止まって見えないか） — d4_bridge
- 01:02.20–01:05.40（3.20s）図解・エンドカードの静止（要目視：動きが止まって見えないか） — d4_bridge
- 01:07.77–01:10.44（2.67s）図解・エンドカードの静止（要目視：動きが止まって見えないか） — d5_everyday
- 01:17.84–01:20.41（2.57s）図解・エンドカードの静止（要目視：動きが止まって見えないか） — endcard

## 4. 焼き込みテロップの漏れ

条件：4fps・全画面、HSV H 100–125, S≥150, V≥170、連結面積 ≥3000px、成分内 S 中央値 ≥190。元素材でテロップは S≈240/V≈250、実写の紺TSは S≈124/V≈157（除外）。

検出なし

## 5. 点滅

平均輝度（0–255）の隣接フレーム変化 ≥25 を遷移とし、向きが逆の遷移2つで1回。最大 1 回/秒。
大きな遷移 8 件（カット・フェード含む）: 00:06.81(+31.6), 00:13.21(-65.9), 00:20.75(+127.3), 00:26.36(-97.4), 00:49.95(-118.7), 00:52.95(+116.4), 01:10.44(-226.1), 01:10.47(+145.8)

## 6. テロップ（表示時間 ≥ 文字数÷4＋1.0秒、かつ ≥1.5秒）

| id | 文 | 文字数 | 表示 | 必要 | 判定 |
|---|---|---|---|---|---|
| kw_ichi | 正確な位置 | 5 | 2.64s | 2.25s | OK |

3コマ（出た直後／中間／消える直前）: `telop_kw_ichi.jpg`

タイトルセーフ・はみ出し・コントラストは `npx hyperframes check comp`：

```
[hyperframes] check: craft 598/599
[hyperframes] check: craft 599/599
[hyperframes] check: overlap 1/23
[hyperframes] check: overlap 2/23
[hyperframes] check: overlap 3/23
[hyperframes] check: overlap 4/23
[hyperframes] check: overlap 5/23
[hyperframes] check: overlap 6/23
[hyperframes] check: overlap 7/23
[hyperframes] check: overlap 8/23
[hyperframes] check: overlap 9/23
[hyperframes] check: overlap 10/23
[hyperframes] check: overlap 11/23
[hyperframes] check: overlap 12/23
[hyperframes] check: overlap 13/23
[hyperframes] check: overlap 14/23
[hyperframes] check: overlap 15/23
[hyperframes] check: overlap 16/23
[hyperframes] check: overlap 17/23
[hyperframes] check: overlap 18/23
[hyperframes] check: overlap 19/23
[hyperframes] check: overlap 20/23
[hyperframes] check: overlap 21/23
[hyperframes] check: overlap 22/23
[hyperframes] check: overlap 23/23
```

## 7. ラウドネス（ffmpeg ebur128=peak=true）

- 統合 -24.0 LUFS（基準 −24±1）、True Peak -9.5 dBTP（基準 ≤−2）、LRA 9.5 LU

## 8. ナレとBGMの差（audio/mix のステム）

行ごと：VO の統合ラウドネス − 同区間の BGM 平均ラウドネス（基準 ≥15 dB、設計 15〜18 dB 下）

| 行 | 差 dB |
|---|---|
| N1 | BGMなし |
| N2 | 19.9 |
| N3 | 19.4 |
| N4 | 19.3 |
| N5a | 20.2 |
| N5b | 19.0 |
| N6 | 20.1 |
| N7a | 19.2 |
| N7b | 19.9 |
| N8 | 19.4 |
| N9a | 18.6 |
| N9b | 18.9 |

3秒短時間ラウドネス（窓がナレ1行に完全に入る 139 点）：中央値 18.0 dB、p5 16.4 dB、最小 15.5 dB

ステムの推移: `levels.png`

## 9. プチノイズ候補（audio/mix/mix.wav）

- 00:40.54 (SE の位置：意図した打音)

## 10. 【要監修】の数

- `comp/narration.json`: 0
- `docs/03_direction_draft.md`: 4
- `docs/08_build_spec.md`: 0
- `comp/compositions/d0_marker.html`: 0
- `comp/compositions/d1_observe.html`: 0
- `comp/compositions/d2_topview.html`: 0
- `comp/compositions/d3_traverse.html`: 0
- `comp/compositions/d4_bridge.html`: 0
- `comp/compositions/d5_everyday.html`: 0
- `comp/compositions/endcard.html`: 0
- `comp/compositions/telop_keyword.html`: 0
- `comp/compositions/title.html`: 0

## 11. 素材台帳（docs/credits_and_licenses.md）

- 元映像: 記載あり（確認語: 映像）
- フォント BIZ UDPゴシック／UDゴシック: 記載あり（確認語: BIZ UDPゴシック, BIZ UDゴシック）
- GSAP: 記載あり（確認語: GSAP）
- HyperFrames: 記載あり（確認語: HyperFrames）
- 仮ナレ（音声合成）: 記載あり（確認語: pyopenjtalk, Mei）
- 効果音: 記載あり（確認語: 効果音）
- 環境音: 記載あり（確認語: 環境音）
- 仮BGM: 記載あり（確認語: 仮BGM）

## 12. 目視用シート

- `contact_0p5s_1of3.jpg`, `contact_0p5s_2of3.jpg`, `contact_0p5s_3of3.jpg`（0.5秒おき、8列×7行、左下にタイムコード）

## 自動化していない項目（人間・目視）

- 言葉と絵の同期（キーワード発話時刻 vs 図解の動き ±0.3s）：vo_timing.json と scenes.cues の比較は別途
- 音の聞こえ方（BGMの選曲・間・SEの質感・環境音の自然さ）は試写で耳で判断
