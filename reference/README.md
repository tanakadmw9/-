# reference/（経緯の資料。読むだけ）

| 場所 | 中身 |
|---|---|
| `plans/content.md`・`plans/editing.md` | 承認された内容計画と編集計画（構成A「はじまりの点」、24小節） |
| `plans/from_production.md` | 制作から計画担当への引き継ぎメモ（素材と制約） |
| `plans/brushup/` | v4.6→v4.7 のチームレビュー：**00_director.md（監督メモ：統合の判断、見送った案、依頼者に選んでもらうこと、v4.8〜v4.10 で直したこと）**、director_team/（共通ブリーフと5担当）、content・editing・accuracy・audio（担当4つ。聴き比べの音源は入っていない） |
| `research/kijunten.md` | 事実確認のメモ（基準点・基準点測量・用語・参考） |
| `teamB/` | 対抗案 B「地面に“住所”をつける」の指示・計画・原稿・QC |
| `history/` | 最初のキットの README・CLAUDE.md・プロンプト、v1 の演出案、v4.2 のゲート資料、廃止した部品 |

各版の自動QC（qc/v4.x/report.md）と独立レビュー（qc/v4.x/review.md）は、根の qc/ にある。

映像（v4.10 と B案の書き出し）は media の zip の `reference/renders/`。各版のシート画像（qc/）、素材分析のシート（analysis/）、v4.2 の絵コンテ（storyboard/）、計画の絵コンテ画像（plan/）も、元映像から作ったものなので media の zip の同じ場所に入っている。

## 文書の中の古いパスの読み替え

記録（docs/decisions.md、reference/ の文書）には、制作時のクラウド環境のパスが残っている。この一式では次の場所にある。

| 文書の中のパス | この一式での場所 |
|---|---|
| `/home/user/-/…`（制作時のリポジトリ） | この一式の根 |
| `/mnt/project-files/plan/`（content.md・editing.md・brushup/） | `reference/plans/`（絵コンテ画像は media の `plan/`） |
| `plan/brushup/00_director.md`、Claude Docs の「監督メモ」 | `reference/plans/brushup/00_director.md` |
| `/mnt/project-files/research/` | `reference/research/` |
| `/mnt/project-files/teamB/` | `reference/teamB/`（B案の映像は media の `reference/renders/`） |
| `/mnt/project-files/renders/` | media の `reference/renders/`（v4.10 だけ） |
| `/mnt/project-files/source/input.mp4` | `source/input.mp4`（media） |
| `/mnt/project-files/assets/se/` | `assets/se/`（各自で入手：assets/README.md） |
| `/mnt/project-files/dova/` | `source/music/`（各自で入手：source/README.md） |
| `/tmp/claude-0/…`（レビュー担当の作業フォルダ） | 残っていない（結果は reference/ の文書に書かれている） |
| `qc/v4.x/…` | 同じ場所。文書（report.md・review.md）はこの一式に、画像は media の zip に入っていて、重ねて展開すると元どおりになる |
