# QC report v4.2

- 対象: `renders/draft/v4.2.mp4`
- 計画尺: 70.783 s（comp/timeline.json）
- 総合: **PASS**

| 項目 | 判定 | 要約 |
|---|---|---|
| 仕様（ffprobe） | ✅ PASS | すべて一致 |
| 黒コマ（blackdetect） | ✅ PASS | 意図外 0 件／全 0 件 |
| 意図しない静止（freezedetect） | ⚠️ WARN | 実写で意図外 0 件、図解の静止 9 件（目視）、意図どおり 2 件 |
| 焼き込みテロップの漏れ（4fps） | ✅ PASS | 検出 2 フレーム（00:07.00〜00:07.25）、うち例外 2（理由つき、§4） |
| 1コマの黒（平均輝度<8） | ✅ PASS | 0 コマ |
| 点滅（>3回/秒） | ✅ PASS | 最大 0 回/秒 |
| 画面の文字の表示時間 | ✅ PASS | 合格 11、例外 6（理由つき）、不合格 0／全 17 |
| hyperframes check（lint・はみ出し・コントラストほか） | ✅ PASS | exit 0、lint: ok／runtime: ok／layout: ok／motion: ok／contrast: ok／craft: ok／audio: ok |
| ラウドネス（ebur128） | ✅ PASS | I -24.0 LUFS, TP -9.2 dBTP |
| ナレとBGMの差（ステム） | ✅ PASS | 行ごと最小 17.5 dB、短時間窓 p5 15.7 dB（audio/mix のステム。レンダーの音声が同じ mix か確認すること） |
| プチノイズ（mix.wav の不連続） | ✅ PASS | 継ぎ目などの候補 0 件、声の中（子音・要試聴）1 件、SE の位置 0 件 |
| カットと拍（格子） | ✅ PASS | 13/13 が拍の1コマ前 ±1.5コマ以内 |
| 【要監修】 | ⚠️ WARN | 合計 12（最終版でゼロ） |
| 音の素材 | ⚠️ WARN | BGM：選曲（audio/bgm/bgm.wav）、効果音：**自作の合成音**（SE_SET=synth）。v4.10 と同じ音にならない。仮BGM では「ナレとBGMの差」が FAIL になりやすい（想定どおり。曲を置けば消える） |
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
| 尺 | 70.783s | 70.783±0.1s | OK |
| 映像と音の長さ | V 70.771s / A 70.783s | 差 ≤0.1s | OK |

## 2. 黒コマ（blackdetect d≥0.1s, pix_th 0.10）

- なし

## 3. 静止（freezedetect n=-60dB, d≥0.5s）

timeline.intended_freezes: 00:18.92–00:20.19 S178_5; 00:28.13–00:28.43 b5_sea：白い紙 0.32 秒（海と現場を線・寄りでつながない）; 01:08.23–01:10.77 K16_10; 01:07.00–01:10.78 endcard（紙の上の絵 → 黒）

図解（ポスター風の静止を含む）やエンドカードは、動きの合間に正当に静止しうる。実写区間の意図外の静止は不具合の疑い。

- 00:01.50–00:02.50（1.00s）図解・エンドカードの静止（要目視：動きが止まって見えないか） — chapter_door
- 00:19.09–00:20.29（1.20s）意図どおり（S178_5） — still:S178_5
- 00:21.19–00:21.92（0.73s）図解・エンドカードの静止（要目視：動きが止まって見えないか） — b5_sea
- 00:22.19–00:23.06（0.87s）図解・エンドカードの静止（要目視：動きが止まって見えないか） — b5_sea
- 00:23.32–00:24.19（0.87s）図解・エンドカードの静止（要目視：動きが止まって見えないか） — b5_sea
- 00:25.49–00:26.59（1.10s）図解・エンドカードの静止（要目視：動きが止まって見えないか） — b5_sea
- 00:26.89–00:28.13（1.23s）図解・エンドカードの静止（要目視：動きが止まって見えないか） — b5_sea
- 00:41.41–00:42.94（1.53s）図解・エンドカードの静止（要目視：動きが止まって見えないか） — eyepiece
- 00:52.79–00:53.49（0.70s）図解・エンドカードの静止（要目視：動きが止まって見えないか） — b10_design(overlay)
- 00:53.62–00:55.59（1.97s）図解・エンドカードの静止（要目視：動きが止まって見えないか） — b10_design(overlay)
- 01:08.07–01:10.07（2.00s）意図どおり（K16_10） — endcard(overlay), still:K16_10

## 4. 焼き込みテロップの漏れ

条件：4fps・全画面、HSV H 100–125, S≥150, V≥170、連結面積 ≥3000px、成分内 S 中央値 ≥190。元素材でテロップは S≈240/V≈250、実写の紺TSは S≈124/V≈157（除外）。

検出 2 フレーム。切り抜き: `caption_hits/`（連続検出の先頭のみ保存）

| 時刻 | 場所 | 成分（x,y,w,h,面積,S中央値） |
|---|---|---|
| 00:07.00 | title_lv(overlay), shot:B2_S | 1732,524,188,97,9090,194（例外：水準の元素材（S・K・N）には焼き込みテロップがない。この検査は基準点パートの青いテロップ用で、青い車を拾う） |
| 00:07.25 | title_lv(overlay), shot:B2_S | 1404,490,516,142,41307,225（例外：水準の元素材（S・K・N）には焼き込みテロップがない。この検査は基準点パートの青いテロップ用で、青い車を拾う） |

## 5. 点滅

平均輝度（0–255）の隣接フレーム変化 ≥25 を遷移とし、向きが逆の遷移2つで1回。最大 0 回/秒。
大きな遷移 13 件（カット・フェード含む）: 00:02.50(-122.9), 00:07.54(+42.0), 00:12.61(-25.7), 00:28.40(-110.8), 00:37.87(+44.0), 00:40.41(-90.5), 00:42.94(+42.0), 00:55.59(-106.0), 01:10.60(-25.0), 01:10.64(-26.0), 01:10.67(-29.0), 01:10.70(-31.0), 01:10.74(-29.0)

## 6. 画面の文字（表示時間 ≥ 文字数÷4＋1.0秒、かつ ≥1.5秒）

`scripts/44_text_timing.mjs` で書き出しと同じページを 0.05 秒ごとに止め、文字が読める濃さ（見え方 ≥0.6：不透明度の積と、上に重なる紙・黒などの覆い）で出ている最長の区間を測った（`text_timing.json`）。文字数は引用符・括弧・句読点を数えない。

| 出 | 消 | 場面 | 文 | 文字数 | 表示 | 必要 | 判定 |
|---|---|---|---|---|---|---|---|
| 00:00.25 | 00:02.55 | chapter_door | 測量部門のしごと | 8 | 2.30s | 3.0s | 例外：章扉の見出し（全パート共通の型、1小節）。声 N1a が同じことを言う |
| 00:00.75 | 00:02.55 | chapter_door | 基準点測量 | 5 | 1.80s | 2.25s | 例外：章扉の作業名は「5つのうち1つが灯る」形を見せる（全パート共通の型、1小節） |
| 00:00.85 | 00:02.55 | chapter_door | 水準測量 | 4 | 1.70s | 2.0s | 例外：章扉の作業名は「5つのうち1つが灯る」形を見せる（全パート共通の型、1小節） |
| 00:00.95 | 00:02.55 | chapter_door | 地形測量 | 4 | 1.60s | 2.0s | 例外：章扉の作業名は「5つのうち1つが灯る」形を見せる（全パート共通の型、1小節） |
| 00:01.05 | 00:02.55 | chapter_door | 路線測量 | 4 | 1.50s | 2.0s | 例外：章扉の作業名は「5つのうち1つが灯る」形を見せる（全パート共通の型、1小節） |
| 00:01.15 | 00:02.55 | chapter_door | 用地測量 | 4 | 1.40s | 2.0s | 例外：章扉の作業名は「5つのうち1つが灯る」形を見せる（全パート共通の型、1小節） |
| 00:07.10 | 00:10.00 | title_lv | 水準測量 | 4 | 2.90s | 2.0s | OK |
| 00:07.30 | 00:11.35 | title_lv | “高さの土台”をはかる | 9 | 4.05s | 3.25s | OK |
| 00:16.20 | 00:18.35 | label_staff | 標尺 | 2 | 2.15s | 1.5s | OK |
| 00:23.15 | 00:28.15 | b5_sea | 東京湾の平均の海面 | 9 | 5.00s | 3.25s | OK |
| 00:25.00 | 00:28.15 | b5_sea | 0 | 1 | 3.15s | 1.5s | OK：0 の丸（記号。声「ゼロ」と同時に出て、白い紙まで約 4 秒） |
| 00:34.30 | 00:36.65 | b5_site | 高さの目印 | 5 | 2.35s | 2.25s | OK |
| 00:38.15 | 00:40.25 | label_level | レベル | 3 | 2.10s | 1.75s | OK |
| 00:51.60 | 00:55.60 | b10_design | 高さ | 2 | 4.00s | 1.5s | OK |
| 00:52.55 | 00:55.60 | b10_design | 位置 | 2 | 3.05s | 1.5s | OK |
| 01:02.55 | 01:10.25 | endcard | “高さの土台”をはかる | 9 | 7.70s | 3.25s | OK |
| 01:03.50 | 01:10.15 | endcard | ナレーション（仮）VOICEVOX:冥鳴ひまり | 20 | 6.65s | 6.0s | OK：仮ナレの規約上の表示。本ナレに差し替えたら消す |

3コマ（出た直後／中間／消える直前、上の表の順に番号。オレンジの枠＝測った文字の位置）: `text_strips_1of3.jpg`, `text_strips_2of3.jpg`, `text_strips_3of3.jpg`

`npx hyperframes check comp --json` の要約：

```
lint: ok（エラー 0・警告 0・情報 0）
runtime: ok（エラー 0・警告 0・情報 0）
layout: ok（エラー 0・警告 0・情報 0）
motion: ok（エラー 0・警告 0・情報 0）
contrast: ok（エラー 0・警告 0・情報 0、コントラスト 3/3 合格）
craft: ok（エラー 0・警告 0・情報 0）
audio: ok（エラー 0・警告 0・情報 0）
```

## 7. ラウドネス（ffmpeg ebur128=peak=true）

- 統合 -24.0 LUFS（基準 −24±1）、True Peak -9.2 dBTP（基準 ≤−2）、LRA 7.5 LU

## 8. ナレとBGMの差（audio/mix のステム）

行ごと：VO の統合ラウドネス − 同区間の BGM 平均ラウドネス（基準 ≥15 dB、設計 15〜18 dB 下）

| 行 | 差 dB |
|---|---|
| N1a | 20.8 |
| N1b | 18.5 |
| N2 | 18.0 |
| N3 | 17.6 |
| N4 | 17.5 |
| N5 | 19.4 |
| N6 | 19.7 |
| N7 | 17.6 |
| N8 | 17.9 |
| N9 | 17.6 |
| N10 | 17.6 |
| N12 | 18.6 |

3秒短時間ラウドネス（窓がナレ1行に完全に入る 124 点）：中央値 17.3 dB、p5 15.7 dB、最小 15.2 dB

ステムの推移: `levels.png`

## 9. プチノイズ候補（audio/mix/mix.wav）

- 01:06.56 (ナレのステムの中＝声の子音の立ち上がり。継ぎ目ではない。試写でヘッドホンで確認)

## 9b. カットと拍（timeline.grid）

| カット | 小節・拍 | ずれ（コマ、拍の1コマ前＝0） |
|---|---|---|
| 00:02.50 | 2小節1拍 | +0.24 |
| 00:07.54 | 4小節1拍 | -0.29 |
| 00:12.61 | 6小節1拍 | +0.18 |
| 00:20.19 | 9小節1拍 | -0.11 |
| 00:28.39 | 12小節2拍 | -0.34 |
| 00:36.64 | 15小節3拍 | +0.44 |
| 00:37.87 | 16小節1拍 | -0.44 |
| 00:40.41 | 17小節1拍 | -0.21 |
| 00:42.94 | 18小節1拍 | +0.03 |
| 00:45.48 | 19小節1拍 | +0.27 |
| 00:50.52 | 21小節1拍 | -0.26 |
| 00:55.59 | 23小節1拍 | +0.21 |
| 01:00.63 | 25小節1拍 | -0.31 |

## 10. 【要監修】の数

- `docs/12_kanshu.md`: 7
- `comp/narration.json`: 4
- `docs/08_build_spec.md`: 0
- `comp/compositions/b10_design.html`: 0
- `comp/compositions/b5_sea.html`: 1
- `comp/compositions/b5_site.html`: 0
- `comp/compositions/chapter_door.html`: 0
- `comp/compositions/endcard.html`: 0
- `comp/compositions/eyepiece.html`: 0
- `comp/compositions/label_pointer.html`: 0
- `comp/compositions/telop_keyword.html`: 0
- `comp/compositions/title_lv.html`: 0

監修の対象表（`docs/12_kanshu.md`）で未確認の項目：

## 11. 素材台帳（docs/credits_and_licenses.md）

- フォント BIZ UDPゴシック／UDゴシック: 記載あり（確認語: BIZ UDPゴシック, BIZ UDゴシック）
- GSAP: 記載あり（確認語: GSAP）
- HyperFrames: 記載あり（確認語: HyperFrames）
- 仮ナレ（音声合成）: 記載あり（確認語: VOICEVOX, 冥鳴ひまり）
- 効果音: 記載あり（確認語: 効果音）
- 環境音: 記載あり（確認語: 環境音）
- BGM（選曲）: 記載あり（確認語: bgm.wav）

## 12. 目視用シート

- `contact_0p5s_1of3.jpg`, `contact_0p5s_2of3.jpg`, `contact_0p5s_3of3.jpg`（0.5秒おき、8列×7行、コマの下にタイムコード）
- 画面の文字の3コマ（§6）: `text_strips_1of3.jpg`, `text_strips_2of3.jpg`, `text_strips_3of3.jpg`
- 絵コンテとの比較・`snapshot --review`（場面の頭＋0.3秒と中間、カットの前後5コマ、スマホ幅）: `storyboard_compare.jpg`, `hf_review/review-beats-1.jpg`, `hf_review/review-beats-2.jpg`, `hf_review/review-beats-3.jpg`, `hf_review/review-phone-1.jpg`, `hf_review/review-phone-2.jpg`, `hf_review/review-phone-3.jpg`, `hf_review/review-seam-01.jpg`, `hf_review/review-seam-02.jpg`, `hf_review/review-seam-03.jpg`, `hf_review/review-seam-04.jpg`, `hf_review/review-seam-05.jpg`, `hf_review/review-seam-06.jpg`, `hf_review/review-seam-07.jpg`, `hf_review/review-seam-08.jpg`, `hf_review/review-seam-09.jpg`, `hf_review/review-seam-10.jpg`, `hf_review/review-seam-11.jpg`, `hf_review/review-seam-12.jpg`, `hf_review/review-seam-13.jpg`, `hf_review/review-seam-14.jpg`, `hf_review/review-seam-15.jpg`, `hf_review/review-seam-16.jpg`, `hf_review/review-seam-17.jpg`, `hf_review/review-seam-18.jpg`, `hf_review/review-seam-19.jpg`, `hf_review/review-seam-20.jpg`, `hf_review/review-seam-21.jpg`, `hf_review/review-seam-22.jpg`, `hf_review/review-seam-23.jpg`

## 自動化していない項目（人間・目視）

- 言葉と絵の同期（キーワード発話時刻 vs 図解の動き ±0.3s）：vo_timing.json と scenes.cues の比較は別途
- 音の聞こえ方（BGMの選曲・間・SEの質感・環境音の自然さ）は試写で耳で判断
