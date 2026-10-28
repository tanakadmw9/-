# チーム検討の共通ブリーフ（A案「はじまりの点」v4.6 → v4.7）

家族参観ミニシアター（建設コンサルタント会社）で上映する、測量部門のうち「基準点測量」1作業を伝える約61秒の映像。
観客：専門知識ゼロの家族（子ども・年配者含む）。大画面・会場スピーカー。依頼者はB案よりA案を「圧倒的に良い」と評価し、A案を磨きたい。
前提：測量部門の複数作業の1つとして基準点測量を伝える（このパートで会社全体の意味を背負わない）。

## 見るもの
- 完成版 v4.6: /mnt/project-files/renders/kijunten_v4.6.mp4（60.66秒）
- 1秒ごとのシート（時刻入り）: /tmp/claude-0/review47/a_sheet_1..4.jpg ／ 0.5秒ごとの単コマ: /tmp/claude-0/review47/a/f_NNN.jpg（NNN=1始まり、時刻=(NNN-1)*0.5秒、640px）
- 計画（承認済み）: /mnt/project-files/plan/content.md, /mnt/project-files/plan/editing.md
- 原稿: /home/user/-/comp/narration.json、タイミング: /home/user/-/comp/timeline.json（shots/vo/se/telops/scenes）
- 規定: /home/user/-/docs/01_brief.md, 04_design_system.md（§8 やってはいけないこと）, 05_audio_design.md, 07_qc_and_review.md
- 決定記録: /home/user/-/docs/decisions.md（直近の行）、前回レビュー: /home/user/-/qc/v4.5/review.md、QC: /home/user/-/qc/v4.6/report.md, levels.png
- 事実確認メモ: /mnt/project-files/research/kijunten.md
- 参考B案: /mnt/project-files/teamB/kijunten_teamB_B1.3.mp4、シート /tmp/claude-0/review47/b_sheet_1..4.jpg（1秒ごと）、計画 /mnt/project-files/teamB/plan/
- 未決事項：ヘルメットの社名（S02/S10 に「K」マークや社名が読める）、ナレ「ひとつ」とアイコンが灯るタイミングのずれ（灯り1.27秒、「ひとつ」2.53秒）

## 制約（守ること）
- 実写素材は約40秒の焼き込みテロップ入り完成品のみ。新規撮影なし。スロー・水増しなし。尺は24小節=60.66秒の格子（BGM New Departure 94.9BPM、1小節2.528秒）が基本。大幅に伸ばす案は別案扱い。
- 動画は見られない→画像で判断。音は聞けない→ffmpeg/numpy で数値分析可（ffmpeg あり）。
- リポジトリ /home/user/- のファイルは編集しない（読むだけ）。自分の作業ファイルは /tmp/claude-0/review47/work_<担当>/ に。
- /mnt/project-files はネットワークマウント：パスに末尾スラッシュ、フォルダ全体を検索しない。
- 画像は読みすぎない（シート優先、必要な単コマだけ）。

## 返すもの
/tmp/claude-0/review47/reports/<担当>.md に書き、最終返答にも同じ内容を返す：
1. 現状の良い点（壊してはいけないもの）3つ以内
2. 改善案の表：| ID | 優先度（A=必ず/B=やると良い/C=余裕があれば） | 時刻 | 問題 | 具体的な直し方（数値・文言・秒まで） | 効果 | 手間（小/中/大） |
   直し方は、実装者がそのまま作業できる粒度で。好みが分かれるものは「依頼者に選んでもらう」と明記し2案示す。
3. B案から取り入れられる要素（あれば、担当視点で）
全体で 60 行程度まで。水増ししない。
