# QC report v2.1

- 対象: `renders/draft/v2.1.mp4`
- 計画尺: 60.6606 s（comp/timeline.json）
- 総合: **FAIL**

| 項目 | 判定 | 要約 |
|---|---|---|
| 仕様（ffprobe） | ✅ PASS | すべて一致 |
| 黒コマ（blackdetect） | ✅ PASS | 意図外 0 件／全 1 件 |
| 意図しない静止（freezedetect） | ⚠️ WARN | 実写で意図外 0 件、図解の静止 7 件（目視）、意図どおり 2 件 |
| 焼き込みテロップの漏れ（4fps） | ❌ FAIL | 検出 2 フレーム（00:14.75〜00:15.00） |
| 1コマの黒（平均輝度<8） | ✅ PASS | 0 コマ |
| 点滅（>3回/秒） | ✅ PASS | 最大 0 回/秒 |
| 画面の文字の表示時間 | ❌ FAIL | 合格 34、例外 6（理由つき）、不合格 18／全 58 |
| hyperframes check（lint・はみ出し・コントラストほか） | ✅ PASS | exit 0、lint: ok／runtime: ok／layout: ok／motion: ok／contrast: ok／craft: ok／audio: ok |
| ラウドネス（ebur128） | ✅ PASS | I -24.0 LUFS, TP -8.4 dBTP |
| ナレとBGMの差（ステム） | ✅ PASS | 行ごと最小 17.1 dB、短時間窓 p5 15.6 dB（audio/mix のステム。レンダーの音声が同じ mix か確認すること） |
| プチノイズ（mix.wav の不連続） | ✅ PASS | 継ぎ目などの候補 0 件、声の中（子音・要試聴）0 件、SE の位置 1 件 |
| カットと拍（格子） | ✅ PASS | 12/12 が拍の1コマ前 ±1.5コマ以内 |
| 【要監修】 | ✅ PASS | 合計 0（最終版でゼロ） |
| 音の素材 | ✅ PASS | BGM：選曲（audio/bgm/bgm.wav）、効果音：効果音ラボ |
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

- 01:00.49–01:00.63（0.13s）意図（エンドカードのフェード） — endcard(overlay)

## 3. 静止（freezedetect n=-60dB, d≥0.5s）

timeline.intended_freezes: 00:02.50–00:07.54 L01_still; 00:27.76–00:28.36 d2_scope の頭：L_look_end.png（のぞく顔の最後のコマ）からのぞき穴が開く。寄りの終わりと同じ画なので止まって見えない; 00:28.86–00:29.43 d2_scope：望遠鏡の中で横線が 1.2 m を指したまま読ませる（声なし。決めの読み）; 00:56.16–01:00.66 endcard（L10 の最後のコマ。紙が覆う前後の 0.4 秒だけ見える）

図解（ポスター風の静止を含む）やエンドカードは、動きの合間に正当に静止しうる。実写区間の意図外の静止は不具合の疑い。

- 00:01.50–00:02.04（0.53s）図解・エンドカードの静止（要目視：動きが止まって見えないか） — chapter_door
- 00:15.88–00:16.68（0.80s）図解・エンドカードの静止（要目視：動きが止まって見えないか） — d0_sea
- 00:18.85–00:20.19（1.33s）図解・エンドカードの静止（要目視：動きが止まって見えないか） — d0_sea
- 00:30.60–00:32.20（1.60s）図解・エンドカードの静止（要目視：動きが止まって見えないか） — d2_scope
- 00:32.53–00:33.33（0.80s）図解・エンドカードの静止（要目視：動きが止まって見えないか） — d2_scope
- 00:33.37–00:34.00（0.63s）図解・エンドカードの静止（要目視：動きが止まって見えないか） — d2_scope
- 00:35.03–00:37.34（2.30s）図解・エンドカードの静止（要目視：動きが止まって見えないか） — d2_scope
- 00:56.76–00:58.39（1.63s）意図どおり（endcard（L10 の最後のコマ。紙が覆う前後の 0.4 秒だけ見える）） — endcard(overlay)
- 00:58.39–01:00.19（1.80s）意図どおり（endcard（L10 の最後のコマ。紙が覆う前後の 0.4 秒だけ見える）） — endcard(overlay)

## 4. 焼き込みテロップの漏れ

条件：4fps・全画面、HSV H 100–125, S≥150, V≥170、連結面積 ≥3000px、成分内 S 中央値 ≥190。元素材でテロップは S≈240/V≈250、実写の紺TSは S≈124/V≈157（除外）。

検出 2 フレーム。切り抜き: `caption_hits/`（連続検出の先頭のみ保存）

| 時刻 | 場所 | 成分（x,y,w,h,面積,S中央値） |
|---|---|---|
| 00:14.75 | shot:L04 | 1604,520,316,101,21746,229 |
| 00:15.00 | shot:L04 | 1376,492,544,142,43323,222 |

## 5. 点滅

平均輝度（0–255）の隣接フレーム変化 ≥25 を遷移とし、向きが逆の遷移2つで1回。最大 0 回/秒。
大きな遷移 9 件（カット・フェード含む）: 00:02.50(-105.3), 00:15.15(+131.0), 00:20.19(-108.1), 00:37.87(-98.2), 00:45.48(+120.2), 00:50.52(-111.1), 01:00.36(-32.6), 01:00.39(-33.8), 01:00.43(-31.6)

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
| 00:17.15 | 00:20.20 | d0_sea | 水準点 | 3 | 3.05s | 1.75s | OK |
| 00:17.15 | 00:20.20 | d0_sea | 高さの目印 | 5 | 3.05s | 2.25s | OK |
| 00:17.80 | 00:20.20 | d0_sea | 海 | 1 | 2.40s | 1.5s | OK |
| 00:18.40 | 00:20.20 | d0_sea | 海から | 3 | 1.80s | 1.75s | OK |
| 00:18.40 | 00:20.20 | d0_sea | （数字は例） | 4 | 1.80s | 2.0s | NG |
| 00:18.40 | 00:18.45 | d0_sea | 4.50m | 5 | 0.05s | 2.25s | NG |
| 00:18.45 | 00:18.50 | d0_sea | 6.02m | 5 | 0.05s | 2.25s | NG |
| 00:18.50 | 00:18.55 | d0_sea | 7.22m | 5 | 0.05s | 2.25s | NG |
| 00:18.55 | 00:18.60 | d0_sea | 8.16m | 5 | 0.05s | 2.25s | NG |
| 00:18.60 | 00:18.65 | d0_sea | 8.85m | 5 | 0.05s | 2.25s | NG |
| 00:18.65 | 00:18.70 | d0_sea | 9.35m | 5 | 0.05s | 2.25s | NG |
| 00:18.70 | 00:18.75 | d0_sea | 9.67m | 5 | 0.05s | 2.25s | NG |
| 00:18.75 | 00:18.80 | d0_sea | 9.87m | 5 | 0.05s | 2.25s | NG |
| 00:18.80 | 00:18.85 | d0_sea | 9.96m | 5 | 0.05s | 2.25s | NG |
| 00:18.85 | 00:20.20 | d0_sea | 10.00m | 6 | 1.35s | 2.5s | NG |
| 00:21.05 | 00:23.90 | k_sight | レベル | 3 | 2.85s | 1.75s | OK |
| 00:21.05 | 00:23.90 | k_sight | 高さをはかる機械 | 8 | 2.85s | 3.0s | NG |
| 00:21.50 | 00:23.90 | k_sight | 標尺 | 2 | 2.40s | 1.5s | OK |
| 00:21.50 | 00:23.90 | k_sight | 目盛りのついたものさし | 11 | 2.40s | 3.75s | NG |
| 00:27.80 | 00:37.90 | d2_scope | 1.1 | 3 | 10.10s | 1.75s | OK |
| 00:27.80 | 00:37.90 | d2_scope | 1.2 | 3 | 10.10s | 1.75s | OK |
| 00:29.15 | 00:37.90 | d2_scope | 1.2m | 4 | 8.75s | 2.0s | OK |
| 00:29.85 | 00:37.90 | d2_scope | 1.7 | 3 | 8.05s | 1.75s | OK |
| 00:29.85 | 00:37.90 | d2_scope | 1.8 | 3 | 8.05s | 1.75s | OK |
| 00:29.85 | 00:37.90 | d2_scope | 1.9 | 3 | 8.05s | 1.75s | OK |
| 00:30.00 | 00:37.90 | d2_scope | 1.3 | 3 | 7.90s | 1.75s | OK |
| 00:30.05 | 00:37.90 | d2_scope | 水準点 | 3 | 7.85s | 1.75s | OK |
| 00:30.05 | 00:37.90 | d2_scope | 10.00m | 6 | 7.85s | 2.5s | OK |
| 00:30.45 | 00:37.90 | d2_scope | 数字は例です | 6 | 7.45s | 2.5s | OK |
| 00:32.45 | 00:37.90 | d2_scope | 1.8m | 4 | 5.45s | 2.0s | OK |
| 00:34.40 | 00:37.90 | d2_scope | 目盛りが大きいほうが、低い | 12 | 3.50s | 4.0s | NG |
| 00:37.55 | 00:37.90 | d2_scope | 0.6m | 4 | 0.35s | 2.0s | NG |
| 00:37.55 | 00:37.90 | d2_scope | 低い | 2 | 0.35s | 1.5s | NG |
| 00:45.90 | 00:50.55 | d3_relay | 水準点 | 3 | 4.65s | 1.75s | OK |
| 00:45.90 | 00:50.55 | d3_relay | 10.00m | 6 | 4.65s | 2.5s | OK |
| 00:46.50 | 00:50.55 | d3_relay | 9.40m | 5 | 4.05s | 2.25s | OK |
| 00:46.50 | 00:50.55 | d3_relay | 9.75m | 5 | 4.05s | 2.25s | OK |
| 00:46.55 | 00:50.55 | d3_relay | 数字は例です | 6 | 4.00s | 2.5s | OK |
| 00:47.50 | 00:50.55 | d3_relay | 9.20m | 5 | 3.05s | 2.25s | OK |
| 00:48.20 | 00:50.55 | d3_relay | 9.60m | 5 | 2.35s | 2.25s | OK |
| 00:52.05 | 01:00.40 | endcard | 目に見えない“高さ”を、 | 9 | 8.35s | 3.25s | OK |
| 00:52.05 | 01:00.40 | endcard | つないでいく | 6 | 8.35s | 2.5s | OK |
| 00:56.15 | 01:00.40 | endcard | 水準測量 | 4 | 4.25s | 2.0s | OK |
| 00:56.40 | 01:00.40 | endcard | 基準点測量 | 5 | 4.00s | 2.25s | OK |
| 00:56.40 | 01:00.40 | endcard | 地形測量 | 4 | 4.00s | 2.0s | OK |
| 00:56.50 | 01:00.40 | endcard | 路線測量 | 4 | 3.90s | 2.0s | OK |
| 00:56.55 | 01:00.40 | endcard | ナレーション（仮）VOICEVOX:冥鳴ひまり | 20 | 3.85s | 6.0s | 例外：仮ナレの規約上の表示。本ナレに差し替えたら消す |
| 00:56.55 | 01:00.40 | endcard | 用地測量 | 4 | 3.85s | 2.0s | OK |
| — | — | d0_sea | 0.42m | 5 | 0.00s | 2.25s | NG |
| — | — | d0_sea | 2.65m | 5 | 0.00s | 2.25s | NG |

3コマ（出た直後／中間／消える直前、上の表の順に番号。オレンジの枠＝測った文字の位置）: `text_strips_1of7.jpg`, `text_strips_2of7.jpg`, `text_strips_3of7.jpg`, `text_strips_4of7.jpg`, `text_strips_5of7.jpg`, `text_strips_6of7.jpg`, `text_strips_7of7.jpg`

`npx hyperframes check comp --json` の要約：

```
lint: ok（エラー 0・警告 0・情報 0）
runtime: ok（エラー 0・警告 0・情報 0）
layout: ok（エラー 0・警告 2・情報 2）
  - [warning] container_overflow @30.33s #ds-scope-b：Element extends outside a clipping layout container.
  - [warning] container_overflow @30.33s #ds-scope-a：Element extends outside a clipping layout container.
  - [info] content_overlap @55.58s #ec-text > div:nth-of-type(1)：Two text blocks overlap and may render unreadable.
  - [info] content_overlap @55.58s #ec-text > div:nth-of-type(2)：Two text blocks overlap and may render unreadable.
motion: ok（エラー 0・警告 0・情報 0）
contrast: ok（エラー 0・警告 0・情報 0、コントラスト 10/10 合格）
craft: ok（エラー 0・警告 2・情報 0）
  - [warning] text_below_floor @30.08s #ds-staffview-a > g:nth-of-type(1) > text:nth-of-type(1)：Type floor is 28 px (2.6% of the 1080 px short side, what a phone can read) and 3 text elements stay under it for 0.5 s or more, the smallest "1.1" at 23 px: se
  - [warning] line_unread @37.51s #ds-low-n："0.6 m" (3 words) is on screen 0.40 s (±0.01 s), under its 1.05 s floor: hold it about 0.5 s + 0.3 s a word (1.40 s here) before it leaves or changes; see refer
audio: ok（エラー 0・警告 0・情報 0）
```

## 7. ラウドネス（ffmpeg ebur128=peak=true）

- 統合 -24.0 LUFS（基準 −24±1）、True Peak -8.4 dBTP（基準 ≤−2）、LRA 5.7 LU

## 8. ナレとBGMの差（audio/mix のステム）

行ごと：VO の統合ラウドネス − 同区間の BGM 平均ラウドネス（基準 ≥15 dB、設計 15〜18 dB 下）

| 行 | 差 dB |
|---|---|
| N1a | 20.7 |
| N1b | 18.9 |
| N2 | 17.8 |
| N3 | 22.3 |
| N4 | 17.8 |
| N5a | 17.1 |
| N5b | 17.8 |
| N6 | 17.5 |
| N7 | 18.0 |
| N8 | 18.8 |

3秒短時間ラウドネス（窓がナレ1行に完全に入る 132 点）：中央値 16.6 dB、p5 15.6 dB、最小 15.3 dB

ステムの推移: `levels.png`

## 9. プチノイズ候補（audio/mix/mix.wav）

- 00:38.81 (SE の位置：意図した打音)

## 9b. カットと拍（timeline.grid）

| カット | 小節・拍 | ずれ（コマ、拍の1コマ前＝0） |
|---|---|---|
| 00:07.54 | 4小節1拍 | -0.29 |
| 00:10.08 | 5小節1拍 | -0.05 |
| 00:12.61 | 6小節1拍 | +0.18 |
| 00:15.15 | 7小節1拍 | +0.42 |
| 00:20.19 | 9小節1拍 | -0.11 |
| 00:23.99 | 10小節3拍 | +0.25 |
| 00:27.76 | 12小節1拍 | -0.39 |
| 00:37.87 | 16小節1拍 | -0.44 |
| 00:40.41 | 17小節1拍 | -0.21 |
| 00:42.94 | 18小節1拍 | +0.03 |
| 00:45.48 | 19小節1拍 | +0.27 |
| 00:50.52 | 21小節1拍 | -0.26 |

## 10. 【要監修】の数

- `comp/narration.json`: 0
- `docs/08_build_spec.md`: 0
- `comp/compositions/chapter_door.html`: 0
- `comp/compositions/d0_sea.html`: 0
- `comp/compositions/d2_scope.html`: 0
- `comp/compositions/d3_relay.html`: 0
- `comp/compositions/endcard.html`: 0
- `comp/compositions/k_sight.html`: 0
- `comp/compositions/telop_keyword.html`: 0
- `comp/compositions/title.html`: 0

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
- 画面の文字の3コマ（§6）: `text_strips_1of7.jpg`, `text_strips_2of7.jpg`, `text_strips_3of7.jpg`, `text_strips_4of7.jpg`, `text_strips_5of7.jpg`, `text_strips_6of7.jpg`, `text_strips_7of7.jpg`
- 絵コンテとの比較・`snapshot --review`（場面の頭＋0.3秒と中間、カットの前後5コマ、スマホ幅）: `hf_review/review-beats-1.jpg`, `hf_review/review-beats-2.jpg`, `hf_review/review-phone-1.jpg`, `hf_review/review-phone-2.jpg`, `hf_review/review-seam-01.jpg`, `hf_review/review-seam-02.jpg`, `hf_review/review-seam-03.jpg`, `hf_review/review-seam-04.jpg`, `hf_review/review-seam-05.jpg`, `hf_review/review-seam-06.jpg`, `hf_review/review-seam-07.jpg`, `hf_review/review-seam-08.jpg`, `hf_review/review-seam-09.jpg`, `hf_review/review-seam-10.jpg`, `hf_review/review-seam-11.jpg`, `hf_review/review-seam-12.jpg`, `hf_review/review-seam-13.jpg`, `hf_review/review-seam-14.jpg`

## 自動化していない項目（人間・目視）

- 言葉と絵の同期（キーワード発話時刻 vs 図解の動き ±0.3s）：vo_timing.json と scenes.cues の比較は別途
- 音の聞こえ方（BGMの選曲・間・SEの質感・環境音の自然さ）は試写で耳で判断
