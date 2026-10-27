# 基準点測量パート 映像制作キット（Claude Code 用）

家族参観ミニシアターの「基準点測量」パートを、Claude Code に制作させるための一式です。
このフォルダをそのまま Claude Code の作業フォルダにして、`prompts/00_kickoff.md` を貼り付ければ始められます。

## 中身

| ファイル | 内容 | 主な読み手 |
|---|---|---|
| CLAUDE.md | Claude Code が毎回読む作業ルール（優先順位、フェーズとゲート、禁止事項） | Claude Code |
| docs/01_brief.md | 目的・観客・伝えること・仕様 | 両方 |
| docs/02_material_analysis.md | 手元の動画の分析（カット表、焼き込みテロップ、足りない画） | 両方 |
| docs/03_direction_draft.md | 構成・ナレーション・図解の叩き台 | 両方 |
| docs/04_design_system.md | 色・文字・配置・動きの規定と「やってはいけないこと」 | Claude Code |
| docs/05_audio_design.md | ナレーション・BGM・効果音・環境音の設計、収録のしかた | 両方 |
| docs/06_tech_stack.md | 使うツール、セットアップ、フォルダ構成 | 両方 |
| docs/07_qc_and_review.md | 自動チェック、試写のしかた、アンケート、検収基準 | 両方 |
| docs/decisions.md・credits_and_licenses.md | 決定の記録、素材の権利台帳（空のひな形） | Claude Code |
| .claude/agents/video-reviewer.md | 書き出しを第三者目線で審査するサブエージェント | Claude Code |
| prompts/ | 最初のプロンプトと、ゲートごとのプロンプト | あなた |

## 始める前に用意するもの（大事な順）

1. **テロップとBGMが入っていない元の映像**（撮影データ、または制作した部署・会社にある編集前の素材）。手元の動画はテロップが焼き込まれた完成品なので、これがあるかどうかで仕上がりが大きく変わります。無くても作れますが、画面の切り出しや覆い隠しで逃げることになります。
2. **会社や会場の近くにある基準点の標識**をスマホで撮った写真か10秒の動画（横向き、手ぶれなく）。物語の主役「最初の一点」の実物で、家族が帰り道で探したくなる「発見」になります。
3. 完成した道路や橋など、自社が関わった現場の写真（掲載してよいもの）。無ければ図解で表現します。
4. **技術監修**をお願いする測量士。ナレーションと図解の正しさを確認してもらいます。
5. 本番のナレーションを読む社員（若手の測量技術者がおすすめ）。録音は編集が固まってからで大丈夫です。
6. 上映環境の情報（画面、スピーカー、再生するPC、全体の尺と音量のそろえ方）。

## 手順

1. `docs/06_tech_stack.md` §3 のソフトを入れる（社用PCなら社内ルールを先に確認）。
2. このフォルダを、日本語や空白を含まない場所に置く（例：`C:\work\kijunten`）。
3. `source/` フォルダを作り、動画を `source/input.mp4`、参考メモを `source/reference.docx` という名前で入れる。
4. このフォルダで Claude Code を起動し、`prompts/00_kickoff.md` の【　】を埋めて貼り付ける。
5. 各ゲートで止まったら、出てきたものを確認して `prompts/10_gate_prompts.md` の該当プロンプトで返す。

## 全体の流れと、あなたの役割

| ゲート | Claude Code が出すもの | あなたが判断すること |
|---|---|---|
| 1 | 素材分析、構成案の比較、ナレーション原稿、絵コンテ | 構成とナレーションの承認（技術監修にも見てもらう） |
| 2 | スタイルフレーム、色補正の比較、焼き込みテロップの処理 | 見た目、色、BGMの選曲 |
| 3 | アニマティック（仮ナレ・粗い図解の通し） | 構成・リズム・わかりやすさ |
| 4 | ほぼ完成版 | 技術監修の確認、若手社員3〜5名での理解度テスト |
| 5 | マスターと納品物一式 | 会場相当の環境での最終確認 |

Claude Code は動画を「見る」ことも音を「聞く」こともできず、静止画と数値で確認します。そのため、**リズム・音の聞こえ方・感情の動きは、あなたの試写が最終判断**です。

## 安全と権利について

- 使うツールはすべて無料で、自分のPCの中で処理します。HyperFrames のクラウド機能など、素材を外部に送る機能は使わないよう CLAUDE.md で禁止しています。
- Claude Code で作業するとき、確認のために書き出した静止画や原稿は Claude に送られて処理されます。会社のAI利用ルールの範囲で使ってください。
- 元動画のBGMは権利が不明なので使いません。新しく使う音楽・効果音・音声合成は、規約を確認して台帳に記録します。
- ヘルメットに社名が映っています。自社（または許諾を得た）映像であることを確認してください。

## 参考にした主な情報

- HyperFrames（Apache-2.0）：https://github.com/heygen-com/hyperframes
- Remotion のライセンス（企業利用の条件）：https://www.remotion.dev/docs/pricing
- GSAP の無償化：https://webflow.com/blog/gsap-becomes-free
- BIZ UDPゴシック（SIL OFL 1.1）：https://github.com/googlefonts/morisawa-biz-ud-gothic
- VOICEVOX：https://voicevox.hiroshiba.jp/ （キャラクターごとの規約を確認）
- AivisSpeech：https://github.com/Aivis-Project/AivisSpeech
- Claude Code の CLAUDE.md・スキル・サブエージェントの使い分け：https://claude.com/ja/blog/steering-claude-code-skills-hooks-rules-subagents-and-more
- Claude Code サブエージェント：https://code.claude.com/docs/en/sub-agents
- Richard E. Mayer『Multimedia Learning』（マルチメディア学習の原則）
- ARIB TR-B32（デジタルテレビ放送番組のラウドネス運用規定）
