# QC report v4.5

- 対象: `renders/draft/v4.5.mp4`
- 計画尺: 60.6606 s（comp/timeline.json）
- 総合: **PASS**

| 項目 | 判定 | 要約 |
|---|---|---|
| 仕様（ffprobe） | ✅ PASS | すべて一致 |
| 黒コマ（blackdetect） | ✅ PASS | 意図外 0 件／全 1 件 |
| 意図しない静止（freezedetect） | ⚠️ WARN | 実写で意図外 0 件、図解の静止 3 件（目視）、意図どおり 2 件 |
| 焼き込みテロップの漏れ（4fps） | ✅ PASS | 検出 0 フレーム |
| 1コマの黒（平均輝度<8） | ✅ PASS | 0 コマ |
| 点滅（>3回/秒） | ✅ PASS | 最大 0 回/秒 |
| テロップ表示時間 | ✅ PASS | 0/0 合格 |
| hyperframes check（はみ出し・コントラスト） | ✅ PASS | exit 0 |
| ラウドネス（ebur128） | ✅ PASS | I -24.0 LUFS, TP -10.8 dBTP |
| ナレとBGMの差（ステム） | ✅ PASS | 行ごと最小 19.1 dB、短時間窓 p5 17.0 dB（audio/mix のステム。レンダーの音声が同じ mix か確認すること） |
| プチノイズ（mix.wav の不連続） | ✅ PASS | SE以外の候補 0 件（SE位置 0 件は除外） |
| カットと拍（格子） | ⚠️ WARN | 13/14 が拍の1コマ前 ±1.5コマ以内、外れ: 00:53.62(-1.97コマ) |
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
| 尺 | 60.661s | 60.661±0.1s | OK |
| 映像と音の長さ | V 60.661s / A 60.650s | 差 ≤0.1s | OK |

## 2. 黒コマ（blackdetect d≥0.1s, pix_th 0.10）

- 01:00.53–01:00.63（0.10s）意図（エンドカードのフェード） — endcard(overlay)

## 3. 静止（freezedetect n=-60dB, d≥0.5s）

timeline.intended_freezes: 00:05.64–00:07.54 S04_last; 00:23.99–00:27.76 S09_freeze（D1の背景）; 00:56.59–01:00.66 endcard（S10 最後のコマに寄り続ける）

図解（ポスター風の静止を含む）やエンドカードは、動きの合間に正当に静止しうる。実写区間の意図外の静止は不具合の疑い。

- 00:01.53–00:02.04（0.50s）図解・エンドカードの静止（要目視：動きが止まって見えないか） — chapter_door
- 00:18.65–00:19.69（1.03s）図解・エンドカードの静止（要目視：動きが止まって見えないか） — d0_marker
- 00:19.69–00:20.19（0.50s）図解・エンドカードの静止（要目視：動きが止まって見えないか） — d0_marker
- 00:25.49–00:26.86（1.37s）意図どおり（S09_freeze（D1の背景）） — d1_observe
- 00:59.03–01:00.19（1.17s）意図どおり（endcard（S10 最後のコマに寄り続ける）） — endcard(overlay)

## 4. 焼き込みテロップの漏れ

条件：4fps・全画面、HSV H 100–125, S≥150, V≥170、連結面積 ≥3000px、成分内 S 中央値 ≥190。元素材でテロップは S≈240/V≈250、実写の紺TSは S≈124/V≈157（除外）。

検出なし

## 5. 点滅

平均輝度（0–255）の隣接フレーム変化 ≥25 を遷移とし、向きが逆の遷移2つで1回。最大 0 回/秒。
大きな遷移 11 件（カット・フェード含む）: 00:02.50(-93.3), 00:10.08(-42.9), 00:17.02(+125.7), 00:20.19(-95.2), 00:35.37(-115.7), 00:50.52(-100.4), 01:00.33(-25.6), 01:00.36(-30.4), 01:00.39(-36.3), 01:00.43(-30.4), 01:00.46(-25.6)

## 6. テロップ（表示時間 ≥ 文字数÷4＋1.0秒、かつ ≥1.5秒）

| id | 文 | 文字数 | 表示 | 必要 | 判定 |
|---|---|---|---|---|---|

3コマ（出た直後／中間／消える直前）: 

タイトルセーフ・はみ出し・コントラストは `npx hyperframes check comp`：

```
[hyperframes] check: craft 485/486
[hyperframes] check: craft 486/486
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

- 統合 -24.0 LUFS（基準 −24±1）、True Peak -10.8 dBTP（基準 ≤−2）、LRA 4.5 LU

## 8. ナレとBGMの差（audio/mix のステム）

行ごと：VO の統合ラウドネス − 同区間の BGM 平均ラウドネス（基準 ≥15 dB、設計 15〜18 dB 下）

| 行 | 差 dB |
|---|---|
| N1 | 22.9 |
| N2 | 19.2 |
| N3 | 20.5 |
| N4 | 19.3 |
| N5a | 19.2 |
| N5b | 19.5 |
| N6 | 19.1 |
| N7a | 19.5 |
| N7b | 19.1 |
| N8 | 24.3 |

3秒短時間ラウドネス（窓がナレ1行に完全に入る 155 点）：中央値 18.9 dB、p5 17.0 dB、最小 16.7 dB

ステムの推移: `levels.png`

## 9. プチノイズ候補（audio/mix/mix.wav）

- なし

## 9b. カットと拍（timeline.grid）

| カット | 小節・拍 | ずれ（コマ、拍の1コマ前＝0） |
|---|---|---|
| 00:02.50 | 2小節1拍 | +0.24 |
| 00:07.54 | 4小節1拍 | -0.29 |
| 00:10.08 | 5小節1拍 | -0.05 |
| 00:15.15 | 7小節1拍 | +0.42 |
| 00:17.02 | 7小節4拍 | -0.4 |
| 00:20.19 | 9小節1拍 | -0.11 |
| 00:23.99 | 10小節3拍 | +0.25 |
| 00:27.76 | 12小節1拍 | -0.39 |
| 00:35.37 | 15小節1拍 | +0.32 |
| 00:37.27 | 15小節4拍 | +0.5 |
| 00:39.77 | 16小節4拍 | -0.27 |
| 00:42.94 | 18小節1拍 | +0.03 |
| 00:50.52 | 21小節1拍 | -0.26 |
| 00:53.62 | 22小節2拍 | -1.97 |

## 10. 【要監修】の数

- `comp/narration.json`: 0
- `docs/03_direction_draft.md`: 4
- `docs/08_build_spec.md`: 0
- `comp/compositions/chapter_door.html`: 0
- `comp/compositions/d0_marker.html`: 0
- `comp/compositions/d1_observe.html`: 0
- `comp/compositions/d2_topview.html`: 0
- `comp/compositions/d3_traverse.html`: 0
- `comp/compositions/d4_bridge.html`: 0
- `comp/compositions/d5_everyday.html`: 0
- `comp/compositions/d_menu.html`: 0
- `comp/compositions/endcard.html`: 0
- `comp/compositions/map_link.html`: 0
- `comp/compositions/telop_keyword.html`: 0
- `comp/compositions/title.html`: 0

## 11. 素材台帳（docs/credits_and_licenses.md）

- 元映像: 記載あり（確認語: 映像）
- フォント BIZ UDPゴシック／UDゴシック: 記載あり（確認語: BIZ UDPゴシック, BIZ UDゴシック）
- GSAP: 記載あり（確認語: GSAP）
- HyperFrames: 記載あり（確認語: HyperFrames）
- 仮ナレ（音声合成）: 記載あり（確認語: VOICEVOX, 冥鳴ひまり）
- 効果音: 記載あり（確認語: 効果音）
- 環境音: 記載あり（確認語: 環境音）
- BGM（選曲）: 記載あり（確認語: bgm.wav）

## 12. 目視用シート

- `contact_0p5s_1of3.jpg`, `contact_0p5s_2of3.jpg`, `contact_0p5s_3of3.jpg`（0.5秒おき、8列×7行、左下にタイムコード）

## 自動化していない項目（人間・目視）

- 言葉と絵の同期（キーワード発話時刻 vs 図解の動き ±0.3s）：vo_timing.json と scenes.cues の比較は別途
- 音の聞こえ方（BGMの選曲・間・SEの質感・環境音の自然さ）は試写で耳で判断
