# 最初に AI エージェント（Codex など）に渡す指示文

使い方：一式の根（AGENTS.md がある所）でエージェントを起動し、目的に合う指示文を1つ貼る。【　】は自分の状況に書き換える。

---

## A. まず再現して確かめる（最初の1回におすすめ）

```
AGENTS.md を読み、そこに書かれた順で docs/decisions.md と playbook/ を読んでください。
次に、フェーズ0として環境を確かめます：bash scripts/00_doctor.sh を実行し、足りないものと、その代わりに何で動くかを短く報告してください。
インストールなど私の操作が要るものは、手順を示して待ってください。
そろったら bash scripts/70_build_all.sh v4.10r を実行してください（約20分。時間制限で切られるなら nohup … > v4.10r.log 2>&1 & で走らせてログを見る）。
次に bash scripts/46_compare_ref.sh renders/draft/v4.10r.mp4 で v4.10 の書き出しと比べ、
qc/v4.10r/report.md の結果と qc/v4.10/report.md との違いと合わせて報告してください。
合格は「音がビット一致、映像は全コマ PSNR 45 dB 以上、QC 総合 PASS」です。
次の違いは想定どおりなので、原因を探さなくてよい：
- 別の機械では、27.4〜35.4 秒（D1→D2 の写真が倒れる区間）の映像だけ、目に見えない差（PSNR 46 dB 以上）が出る
- hyperframes check のコントラストの数が 5 と 6 の間で揺れる
- 【要監修】の表に d3_traverse・d4_bridge・d5_everyday・d_menu の行がない（reference/history/obsolete/ に移した。合計は同じ 16）
- 「音の素材」の行が増えている（v4.10 の後に足した検査）
- BGM・効果音を置いていなければ、「ナレとBGMの差」が FAIL、「音の素材」が WARN になる
それ以外の違いがあれば、原因の見当も書いてください。作品の中身はまだ変えないでください。
```

## B. v4.10 の続き（試写1の準備と改善）

```
AGENTS.md と playbook/70_beyond.md を読んでください。v4.10 は試写1に出す版です。
今回やってほしいこと：【例：依頼者の選択の結果「N6 は案2、環境音は鳥＋草」を反映した v4.11 を作る ／ 試写1の指摘（下に貼る）に対応する】
進め方：
1. 変える前に、変える所・理由・影響する時刻を短く示してください（原則と矛盾がないか、playbook/00_summary.md で確かめる）。
2. scripts/ と comp/ を直し、bash scripts/60_render.sh v4.11 で書き出してください。
3. qc/v4.11/report.md と目視用シートを自分で見て直してください。
4. bash scripts/45_review_pack.sh v4.11 を実行し、qc/v4.11/request.md を書いて、45 をもう一度実行してください。独立レビューは別のセッションで行うので、私に「qc/v4.11/review_pack を開いて、その AGENTS.md に従ってレビューし、review.md をそのフォルダに書いて」と頼む文を用意して止まってください。
5. レビューが返ったら bash scripts/45_review_pack.sh v4.11 --collect で qc/v4.11/review.md に移し、指摘ごとの対応を docs/decisions.md に書き、直してから私に出してください。
【試写1の指摘：　】
```

## C. シリーズの次のパートを新しく作る（ゲート1まで。3回に分けて貼る）

最初の計画は弱いのが普通（A案も構成を2回作り直した）。**作り手のセッション → 別のセッションで批評 → 作り手が直す**の順で、批評を通してから人に出す。いきなり書き出させない。

### C-1 作り手のセッション
```
AGENTS.md、playbook/00_summary.md、playbook/10_process.md、playbook/25_plan_quality.md、playbook/60_next_part.md を読んでください。
お手本として、承認された前のパートの計画 reference/plans/content.md と reference/plans/editing.md を最後まで読んでください。
この一式は「基準点測量」パートの完成プロジェクトです。これを型にして【水準測量】パートを作ります。

素材と状況：
- 元動画：【source/ に置いた◯本。約◯秒。テロップや BGM の焼き込み：あり／なし】
- 技術監修（測量士）：【◯◯さん／未定】
- 本ナレーションを読む人：【決まっている／未定】
- 曲：【基準点パートと同じ New Departure を使う／別の曲を選ぶ】
- 部門の作業の名前と並び：【基準点／水準／地形／路線／用地 で合っている／違う：　】

今回やってほしいこと（ゲート1まで。まだ書き出さない）：
1. フェーズ0（環境）と1（素材分析：analysis/shot_log.md とシート、足りない画、私への依頼）。
2. 事実の調べ：reference/research/【suijun】.md に、この作業の目的・手順・用語・子どもが誤解しそうな所を出典つきで。
3. 中心の絵（たとえ）の候補を3つ（playbook/25_plan_quality.md §3）。それぞれ、持ち帰る言葉3つ・締めの一文・看板の動き・ナレの見本2文。1つを推す。
4. 内容計画（templates/content_plan.md）を書く。次に、編集担当になったつもりで編集計画（templates/editing_plan.md）を書く。突き合わせて、絵コンテ（templates/storyboard.md の全列：時間・画・ナレ・文字・図解・音・目的）とナレ原稿（字数と推定秒）を作る。
5. playbook/25_plan_quality.md の10項目で自己採点（点と理由）を plan/self_check.md に。
6. ここで止まり、私に「別のセッションで prompts/15_plan_critique.md を使って批評して」と頼む文を用意してください。
進める前に、作業の計画を短く示してください。
```

### C-2 別のセッション（批評）
prompts/15_plan_critique.md の指示文を貼る（【　】を C-1 で書いたファイルに書き換える）。結果は reviews/plan_v1/critique.md。

### C-3 作り手のセッションに戻る
```
reviews/plan_v1/critique.md を読み、指摘ごとに「直した／直さない（理由）／依頼者に聞く」を docs/decisions.md に書いて、計画・原稿・絵コンテを直してください。
playbook/25_plan_quality.md の採点を付け直し、16点以上・0点なしになったら、prompts/10_gate_report.md の形でゲート1の報告を書いてください。
中心の絵は3案を並べて比べられる形に（それぞれナレの見本と、看板の動きのラフ1枚）、おすすめに◎。決めてほしいことは5問以内、選択肢つき。
ここで止まって、私の確認を待ってください。
```

もっと良くするなら：C-1 の4を2つのセッションに分ける（内容計画のセッションと編集計画のセッション。A案はこの形で作った。10_process.md §2.3）。

## D. 対抗案をつくる（比べたいとき）

prompts/50_rival_version.md を使う。

## E. チームで磨く（いくつかの視点で洗い出したいとき）

prompts/20_role_reviews.md（担当ごとに別のセッション）→ prompts/30_director_synthesis.md（監督のセッション）。
