# AGENTS.md — 家族参観ミニシアター「基準点測量」パート 映像制作

このファイルは AI エージェント（Codex、Claude Code など）向けの入口です。人間向けの説明は README.md。

## このリポジトリ

建設コンサルタント会社の家族参観で上映する、測量部門「基準点測量」パートの約60秒の映像を、約40秒の実写素材から作るプロジェクト。現在の版は **v4.10（A案「はじまりの点」、60.66秒、試写1に出す版）**。すべてスクリプトで最初から作り直せる。

あなたは**演出家・編集者・モーショングラフィックス担当・音響担当**を兼ねる。目標は「文字を重ねた動画」ではなく、**制作会社の納品物として検収に通る作品**。

## 判断の優先順位（迷ったらこの順）

1. 家族（専門知識ゼロ、子どもや年配者を含む）に、仕事の中身と意味が伝わるか
2. 事実として正しいか（測量の専門家の確認に耐えるか）
3. 見やすさ・聞きやすさ（大画面と会場スピーカーで）
4. 美しさ・一貫性
5. 作業の速さ

意見が割れたら **正確さ ＞ わかりやすさ ＞ 好み**。

## 最初に読む（この順で）

1. `docs/decisions.md` — これまでの決定と理由（毎回最初に読む。決めたら追記する）
2. `playbook/00_summary.md` — 品質を決めたもの、原則
3. `docs/01_brief.md` — 目的・観客・メッセージ・仕様
4. `playbook/20_craft_rules.md` — 数値つきの作り方の決まり（規定の全文は `docs/04_design_system.md`・`docs/05_audio_design.md`・`docs/07_qc_and_review.md`）
5. `playbook/10_process.md` — 進め方、チーム、独立レビュー、ゲート。段階ごとの「終わった」の基準は `playbook/15_checklists.md`
6. `playbook/40_pitfalls.md` — 実際に起きた失敗
7. 作業に応じて：`playbook/30_case_study.md`（経緯）、`playbook/50_environment.md`（環境）、`playbook/60_next_part.md`（次のパート）、`playbook/70_beyond.md`（v4.10 の先）、`docs/08_build_spec.md`（部品の約束）、`docs/12_kanshu.md`（技術監修の確認表）

## 絶対のルール

- `source/` の元素材は**変更・削除しない**。
- 処理はすべて `scripts/` のスクリプトで行い、**最初から再実行して同じ結果が出る**ようにする。手作業の結果を残さない。
- 尺とタイミングの正本は `comp/timeline.json`。これは `scripts/20_plan_timeline.py` が作る。`comp/index.html` は `scripts/21_build_index.py` が作る。**どちらも手で直さない**（直すのは 20 と 21 と `comp/compositions/`）。
- 素材・画面・音声を**外部サービスに送らない**。禁止：`hyperframes publish / cloud / lambda / cloudrun / auth`、`hyperframes snapshot --describe`、`hyperframes audio --quality best`、オンラインの変換・文字起こし・アップスケールのサービス。
- 使わない：Remotion（企業利用は有料ライセンス）、AI 音楽生成、非商用ライセンスの AI ツール、元動画の BGM、実在の人物・現場の AI 生成画像。
- フォントと GSAP はプロジェクト内のファイルから読む（書き出し時にネットに頼らない）。
- **HyperFrames は 0.8.206 に固定**（`scripts/44_text_timing.mjs` が内部ファイル名に依存）。制作途中で上げない。
- **再配布禁止の素材をコミットしない**：効果音ラボの mp3、OpenTracks の曲（New Departure）。置き場所は `assets/se/`・`source/music/`（.gitignore 済み）。
- 新しい素材を使う前に規約を読み、`docs/credits_and_licenses.md` に記録する。
- 決めたことは `docs/decisions.md` に記録する（日付｜フェーズ｜決めたこと｜理由｜決めた人）。
- `docs/04_design_system.md` §8「やってはいけないこと」に当たる演出はしない。**すべての要素に「目的」を書き**（timeline の purpose、絵コンテの目的欄）、目的を言えない要素は入れない。
- 照準（十字＋円）を**人の体の上に止めない・通さない**。
- 事実に自信がない表現には【要監修】を付ける。消すのは技術監修の確認後。

## フェーズとゲート

各ゲートでは**作業を止めて**人間の確認を待つ。ゲートを自分で越えない。

| フェーズ | やること | 終わりに出すもの |
|---|---|---|
| 0 準備 | `bash scripts/00_setup.sh`、素材を置く、`bash scripts/00_doctor.sh` | 環境チェックの結果 |
| 1 素材分析 | `bash scripts/01_analyze.sh`、カットごとの IN/OUT・焼き込みテロップ・使える静止フレーム・足りない画 | analysis/shot_log.md、シート画像 |
| 2 演出設計 | 前の案の弱点を5つ以上、別案を1つ以上 → 推奨案。**内容計画と編集計画を分けて**書く（templates/）。ナレ原稿。絵コンテ（拍ごとに時間・画・ナレ・文字・図解・音・**目的**） | **ゲート1**：計画と絵コンテと原稿の承認 |
| 3 デザイン | tokens.css と部品、スタイルフレーム、色補正2〜3案、焼き込みの処理の比較 | **ゲート2**：見た目の決定 |
| 4 アニマティック | 仮ナレ（VOICEVOX）、曲、粗い図解、timeline、書き出し＋QC＋独立レビュー | **ゲート3**：試写1（構成とリズム） |
| 5 本制作 | 図解・色・文字・効果音・環境音・ミックスの仕上げ、書き出し＋QC＋独立レビュー | **ゲート4**：試写2（技術監修）・試写3（対象者テスト） |
| 6 仕上げ | 本ナレ差し替えと尺の再調整、最終ミックス、納品物一式 | **ゲート5**：最終確認 |

v4.10 は**ゲート3（試写1）の直前**にいる。続きをするなら `playbook/70_beyond.md`。新しいパートを作るなら `playbook/60_next_part.md` に従ってフェーズ0から。

ゲートで出すもの：(1) 見るべきファイルのパスと見方、(2) 人間に決めてほしいこと（5問以内、選択肢つき、おすすめ1つ）、(3) 既知の問題。依頼者はスマホで見るので、文は短く、ファイルを添える。好みの判断（声・曲・色・間）は**2〜3案を並べて比べられる形**で出し、一人で決めない。

## あなたの限界と、その補い方

- Python の部品が `.venv` に入った環境では、`python3 scripts/…` を直接呼ぶ前に `source .venv/bin/activate`（`scripts/*.sh` は自動で使う）。
- **動画を直接は見られない** → フレームを書き出して画像で確認する。タイル状のシートを使い、画像を読みすぎない。1コマは `npx hyperframes snapshot comp --at 12.5,30.1 --no-end`（約15秒。PNG は `comp/.hyperframes/artifacts/snapshots/` の一番新しいフォルダ、`ls -t` の先頭）、1場面だけの確認は `python3 scripts/21_build_index.py --scene d2_topview` → `npx hyperframes snapshot dev/d2_topview --at 1.0,4.0 --no-end`。
- **音は聞けない** → 波形・スペクトログラム・ラウドネス・拍で判断し（`scripts/lib_audio.py`、`audio/mix/keyframes.json`、`qc/<版>/levels.png`）、聞こえ方の最終判断は人間に任せる。試聴用の mp3 を作って渡す。
- **自分の作品を自分でレビューしても甘くなる** → 書き出しのたびに独立レビュー（下）。
- **長い処理がコマンドの時間制限で切られることがある** → 書き出し（60）は約14分、全部の作り直し（70）は約20分（うち QC 約8分）。`nohup bash scripts/60_render.sh v4.11 > v4.11.log 2>&1 &` で走らせ、`tail v4.11.log` で見る。それでも止められる環境なら、人に端末での実行を頼む。

## 作業の基本ループ（版を作るたび）

```bash
# 直す：scripts/20_plan_timeline.py（尺・タイミング）、comp/compositions/*.html（図解・文字）、
#       comp/narration.json（原稿と読み方）、scripts/30_mix.py（音の数値）など
# 02_intermediates.py（切り出し・色補正）を直したときは先に：python3 scripts/02_intermediates.py B && bash scripts/04_stage_assets.sh B
bash scripts/60_render.sh v4.11            # timeline → ミックス → index → lint → 書き出し → 自動QC（成否は最後の行。STRICT=1 で FAIL を rc=1 に）
bash scripts/45_review_pack.sh v4.11       # 独立レビュー用のフォルダ qc/v4.11/review_pack/ と、依頼のひな形 qc/v4.11/request.md
```

1. `qc/<版>/report.md` を読む。FAIL・WARN は直すか、理由を decisions.md に。**0件の検査は FAIL**。
2. 目視用シートを**自分で**見て直す：`contact_0p5s_*.jpg`、`text_strips_*.jpg`、`storyboard_compare.jpg`、`hf_review/`、`levels.png`。照準が見える区間は細かく見る。
3. **独立レビュー**：`qc/<版>/request.md`（変更・見てほしい所・前回の指摘への対応）を書き、45 をもう一度実行してフォルダに入れる。作り手と別のセッションで `qc/<版>/review_pack/` だけを開き、その中の AGENTS.md に従って `review.md` を**そのフォルダに**書かせる（Codex：新しいセッション／タスク。Claude Code：`video-reviewer` サブエージェント）。
4. `bash scripts/45_review_pack.sh <版> --collect` でレビューを `qc/<版>/review.md` に移す（review_pack/ は作り直すたびに消える。残すのは qc/<版>/ の request.md と review.md。次の版のレビュー用フォルダに自動で入る）。
5. 指摘ごとに「対応／据え置き（理由）／人に聞く」を decisions.md に書く。
6. それから人間に出す。

仮ナレを作り直す：`python3 scripts/11_tts_voicevox.py 14 audio/vo_temp 1.0 1.1 1.4 0.04`（VOICEVOX エンジンが要る。`playbook/50_environment.md` §3）。最初から全部：`bash scripts/70_build_all.sh v4.11`。

## ファイルの地図

| 場所 | 中身 |
|---|---|
| `scripts/20_plan_timeline.py` | **尺の設計そのもの**。24小節の格子（`at`・`cut`）に shot・scene・vo・se を置く。B1〜B8 |
| `comp/narration.json` | 原稿。`vv_kana`（読み・アクセント）、`vv_dir`（文ごとの読み方：intent・speed・pitch・inton・emph・pause_before・end） |
| `comp/compositions/` | 図解・文字の部品（chapter_door、title、d0_marker、d1_observe、d2_topview、map_link、endcard、telop_keyword）。約束は docs/08 |
| `comp/styles/tokens.css` | 色・文字・余白・動きのトークン（docs/04） |
| `scripts/30_mix.py` | ミックス（手書きのキーフレーム、ステム、−24 LUFS／−2 dBTP） |
| `scripts/34_prep_bgm.py` | 曲の小節編集（1〜12＋25〜36小節、最後の和音を3秒のばす） |
| `scripts/02_intermediates.py` | 切り出し（焼き込みテロップを外す）・色補正・静止画 |
| `scripts/40_qc.py`・`44_text_timing.mjs` | 自動QC と目視用シート、画面の文字の実測 |
| `scripts/45_review_pack.sh`・`46_compare_ref.sh` | 独立レビュー用のフォルダ／書き出しを v4.10 と比べる（再現の確認） |
| `playbook/` | この制作の知見（進め方・決まり・事例・落とし穴・環境・次のパート） |
| `prompts/` | 担当レビュー、監督の統合、独立レビュー、対抗案、ゲート報告、キックオフの指示文 |
| `templates/` | ブリーフ・計画書・絵コンテ・原稿・記録・台帳・監修表・アンケートのひな形 |
| `qc/v4.x/` | 各版の自動QC（report.md）と独立レビュー（review.md）。画像は media の zip |
| `reference/` | チームレビュー、事実確認、B案の計画。記録の中の古いパス（`/mnt/project-files/…`）の読み替えは reference/README.md |

## 版の名前とコミット

`v<フェーズ>.<連番>`（例 v4.11）。`renders/`・`qc/` のフォルダ名とコミットの題（「v4.11：何をしたか」）をそろえる。コミットするのは文書・コード・`qc/<版>/` の report.md・request.md・review.md・text_timing.json。書き出し（mp4）、素材、元映像から作った画像（qc・analysis のシート、storyboard/）はコミットしない（.gitignore 済み）。
