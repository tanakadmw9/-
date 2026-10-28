# 素材・ライセンス台帳

使ったすべての素材（映像・写真・音楽・効果音・環境音・音声合成・フォント・ソフト）を記録する。規約は改定されることがあるので、確認した日付も残す。

| 種別 | 素材名 | 入手元URL | ライセンス／規約 | 規約確認日 | クレジット要否と表記 | 使った場所 |
| 映像 | 水準測量の実写3本（レベル据える-引き／観測-引き／覗き-寄り） | 社内（依頼者から 2026-10-28） | 自社映像。**外部に送らない・公開しない**（公開リポジトリにコミットしない）。**要確認**：ヘルメットのロゴ・出演者の上映同意 | 2026-10-28 | | 実写の全カット。**音声も使う（v3）**：現場音を環境音に（scripts/35_make_loc_amb.py。人の声がある所は使わない：analysis/shot_log.md §3） |
| 効果音 | 効果音ラボ：tones/sceneswitch1（場面転換・木琴） | https://soundeffect-lab.info/ | 上の行と同じ（再配布禁止） | 2026-10-27 | 不要 | のぞき穴が開く所（水準 v3。v1 は目線の点線） |
| フォント | BIZ UDPゴシック（npm @fontsource/biz-udpgothic 5.x 経由） | https://github.com/googlefonts/morisawa-biz-ud-gothic | SIL OFL 1.1（comp/assets/fonts/OFL-biz-udpgothic.txt） | 2026-10-27 | 不要 | テロップ・図解の文字 |
| フォント | BIZ UDゴシック（npm @fontsource/biz-udgothic 経由） | 同上 | SIL OFL 1.1（comp/assets/fonts/OFL-biz-udgothic.txt） | 2026-10-27 | 不要 | 図解の座標の数字 |
| ソフト | HyperFrames 0.8.206（npm、ローカル実行のみ。クラウド機能は不使用） | https://github.com/heygen-com/hyperframes | Apache-2.0 | 2026-10-27 | 不要 | 組み立て・書き出し |
| ソフト | GSAP 3（npm、ローカル読み込み） | https://gsap.com | Standard "no charge" License | 2026-10-27 | 不要 | 図解・テロップの動き |
| ソフト | FFmpeg 6.1（Ubuntu パッケージ） | https://ffmpeg.org | LGPL/GPL | 2026-10-27 | 不要 | 切り出し・色補正・音・書き出し |
| 図解の部品 | 線画アイコン（基準点測量・水準・地形・路線・用地・照準）、点つなぎ用の架空の地図（方眼・等高線・道路・基準点。地名・方位・縮尺なし） | 自作（素材スレッドの scripts/make_icons.py・make_tentsunagi_map.py。原本は制作時の共有フォルダ assets/icons/custom・assets/map、台帳 assets/LICENSES.md） | 第三者の権利なし（自社制作） | 2026-10-27 | 不要 | comp/compositions/chapter_door.html・map_link.html・endcard.html に線をそのまま埋め込み（c2pa の metadata は除去） |
| 環境音 | 夏の草原の風・草（自作・フィルタしたノイズを合成） | 自作（scripts/32_make_amb.py） | 第三者の権利なし（自社制作） | 2026-10-27 | 不要 | 水準 v3 では予備（AMB=synth のとき）。v1 は全編 |
| 環境音 | 水準測量の実写の現場音（道ばたの車と風） | 社内（上の映像の行と同じ） | 自社映像の音。外部に送らない・公開しない | 2026-10-28 | 不要 | audio/amb/amb_loc.wav → mix（水準 v3、全編。図解区間は下げる） |
| ソフト | ミックス・QC スクリプト（numpy / scipy / soundfile / pyloudnorm / OpenCV / FFmpeg） | PyPI ほか | BSD・MIT 等（ツールとして使用、成果物に同梱しない） | 2026-10-27 | 不要 | scripts/30_mix.py, 40_qc.py |
| 音声合成（仮ナレ） | VOICEVOX エンジン 0.26.0（Docker イメージ voicevox/voicevox_engine:cpu-latest、ローカル実行） | https://github.com/VOICEVOX/voicevox_engine | LGPL-3.0（エンジン）。音声ライブラリは各キャラクターの規約に従う | 2026-10-27 | 不要（ソフト） | scripts/11_tts_voicevox.py |
| 音声合成（仮ナレ・声） | VOICEVOX:冥鳴ひまり（ノーマル、style 14） | https://meimeihimari.wixsite.com/himari/terms-of-use | エンジン同梱の規約（/speaker_info）：「VOICEVOX:冥鳴ひまり」とクレジットを記載すれば商用・非商用で利用可。詳細規約は上記URL（このクラウドからは未読、**要確認**） | 2026-10-27 | **要**：「VOICEVOX:冥鳴ひまり」 | 仮ナレ N1〜N8（audio/vo_temp、narration.json v3） |
| BGM | New Departure — FLASH☆BEAT（OpenTracks、旧DOVA-SYNDROME） | https://opentracks.com/bgm/detail/6843 | OpenTracks 音源利用ライセンス（OpenTracks の規約。2026-10-27 に保存した全文は制作時の共有フォルダ dova/terms.txt）：商用・法人可、表示不要、編集・フェード可。禁止：音源を主役にする使い方・再配布・AI学習。作曲者の追加条件なし | 2026-10-27 | 不要（任意で「FLASH☆BEAT」） | source/music/01_new_departure.mp3 → audio/bgm/bgm.wav（scripts/34_prep_bgm.py。v4.5 から 1〜12＋25〜36 小節をつなぐ。最後の和音の伸ばしを v4.8 で2秒、v4.9 から3秒のばす＝規約の「編集可」の範囲） |
| 効果音 | 効果音ラボ：tones/decision28（鉄琴）・tones/decision6（電子音）・tones/cursor3・foley/mechanical-pencil-write1・foley/walk-soil1（水準 v3 で追加：標尺の人の足音） | https://soundeffect-lab.info/ （規約 https://soundeffect-lab.info/agreement/ を 2026-10-27 に素材スレッドが原文確認、制作時の共有フォルダ assets/se/README.md。入手は assets/README.md） | 商用・法人無料、クレジット不要、改変可。**再配布禁止**（mp3・wav をリポジトリに入れない）、Content ID 登録禁止、AI学習禁止 | 2026-10-27 | 不要 | v4.7〜：章扉の灯り・点が決まる・アイコンが灯る（decision28）、照準が合う（decision6）、測距（cursor3）、地図の線が描かれる間（シャーペン）。assets/se/（SE_DIR。各自で入手：assets/README.md）から scripts/30_mix.py が直接読む（timeline.json の se[].src）。自作の合成音は SE_SET="synth" で戻せる |

水準測量パートの注：仮ナレは VOICEVOX:冥鳴ひまり（narration.json L3）。pyopenjtalk・仮BGM は使っていない。
