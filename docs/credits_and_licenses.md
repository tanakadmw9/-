# 素材・ライセンス台帳

使ったすべての素材（映像・写真・音楽・効果音・環境音・音声合成・フォント・ソフト）を記録する。規約は改定されることがあるので、確認した日付も残す。

| 種別 | 素材名 | 入手元URL | ライセンス／規約 | 規約確認日 | クレジット要否と表記 | 使った場所 |
|---|---|---|---|---|---|---|
| 映像 | 基準点測量（元動画、YouTube 再圧縮版） | 社内 | 自社映像（**要確認**：ヘルメットの社名・出演者の上映同意） | | | 実写の全カット（音声は破棄） |
| フォント | BIZ UDPゴシック（npm @fontsource/biz-udpgothic 5.x 経由） | https://github.com/googlefonts/morisawa-biz-ud-gothic | SIL OFL 1.1（comp/assets/fonts/OFL-biz-udpgothic.txt） | 2026-10-27 | 不要 | テロップ・図解の文字 |
| フォント | BIZ UDゴシック（npm @fontsource/biz-udgothic 経由） | 同上 | SIL OFL 1.1（comp/assets/fonts/OFL-biz-udgothic.txt） | 2026-10-27 | 不要 | 図解の座標の数字 |
| ソフト | HyperFrames 0.8.206（npm、ローカル実行のみ。クラウド機能は不使用） | https://github.com/heygen-com/hyperframes | Apache-2.0 | 2026-10-27 | 不要 | 組み立て・書き出し |
| ソフト | GSAP 3（npm、ローカル読み込み） | https://gsap.com | Standard "no charge" License | 2026-10-27 | 不要 | 図解・テロップの動き |
| ソフト | FFmpeg 6.1（Ubuntu パッケージ） | https://ffmpeg.org | LGPL/GPL | 2026-10-27 | 不要 | 切り出し・色補正・音・書き出し |
| 音声合成（仮ナレ） | pyopenjtalk-plus 0.4.1.post10（Python パッケージ、ローカル実行） | https://github.com/tsukumijima/pyopenjtalk-plus （PyPI） | MIT（"pyopenjtalk" © 2018 Ryuichi Yamamoto。同梱 `pyopenjtalk_plus-0.4.1.post10.dist-info/licenses/LICENSE.md`） | 2026-10-27 | 不要（ソフト） | 仮ナレ N1〜N9b（audio/vo_temp, scripts/10_tts_temp.py） |
| 音声合成（仮ナレ・辞書） | Open JTalk 辞書（pyopenjtalk-plus 同梱 `pyopenjtalk/dictionary`） | 同上 | 修正BSD（© 2009 Nara Institute of Science and Technology。同梱 `pyopenjtalk/dictionary/COPYING`） | 2026-10-27 | 不要 | 仮ナレの読み・アクセント |
| 音声合成（仮ナレ・声） | HTS Voice "Mei"（`mei_normal.htsvoice`、MMDAgent Project Team 公開。pyopenjtalk-plus 同梱の既定音声） | http://www.mmdagent.jp/ | **CC BY 3.0**（© 2009-2013 Nagoya Institute of Technology, Department of Computer Science。同梱 `pyopenjtalk/htsvoice/LICENSE_mei_normal.htsvoice`）。※ 指示書・vo_timing.json には「nitech_jp_atr503_m001」とあるが、インストール済みパッケージに m001 は同梱されておらず、10_tts_temp.py は音声を指定していないため、実際の声は Mei（女声、ナレの基本周波数の実測でも確認） | 2026-10-27 | **要**（仮ナレのまま上映・配布する場合）。表記例：「音声合成：HTS Voice "Mei" © Nagoya Institute of Technology（CC BY 3.0）」。本ナレ（社員の声）に差し替えれば不要 | 仮ナレ（試写用） |
| 効果音 | lock / measure / click / join（自作・numpy で合成） | 自作（scripts/31_make_se.py） | 第三者の権利なし（自社制作） | 2026-10-27 | 不要 | audio/se/*.wav → mix（照準・測距・点が決まる・確認・橋がつながる） |
| 環境音 | 夏の草原の風・草（自作・フィルタしたノイズを合成） | 自作（scripts/32_make_amb.py） | 第三者の権利なし（自社制作） | 2026-10-27 | 不要 | audio/amb/amb.wav → mix（全編、図解区間は下げる） |
| BGM（仮BGM） | temp_bgm（自作・アルゴリズム合成。AI音楽生成は不使用。**仮**：人間が選曲した audio/bgm/bgm.wav に差し替える） | 自作（scripts/33_make_temp_bgm.py） | 第三者の権利なし（自社制作） | 2026-10-27 | 不要 | audio/bgm/temp_bgm.wav → mix（8.4秒〜） |
| ソフト | ミックス・QC スクリプト（numpy / scipy / soundfile / pyloudnorm / OpenCV / FFmpeg） | PyPI ほか | BSD・MIT 等（ツールとして使用、成果物に同梱しない） | 2026-10-27 | 不要 | scripts/30_mix.py, 40_qc.py |
| 音声合成（仮ナレ） | VOICEVOX エンジン 0.26.0（Docker イメージ voicevox/voicevox_engine:cpu-latest、ローカル実行） | https://github.com/VOICEVOX/voicevox_engine | LGPL-3.0（エンジン）。音声ライブラリは各キャラクターの規約に従う | 2026-10-27 | 不要（ソフト） | scripts/11_tts_voicevox.py |
| 音声合成（仮ナレ・声） | VOICEVOX:冥鳴ひまり（ノーマル、style 14） | https://meimeihimari.wixsite.com/himari/terms-of-use | エンジン同梱の規約（/speaker_info）：「VOICEVOX:冥鳴ひまり」とクレジットを記載すれば商用・非商用で利用可。詳細規約は上記URL（このクラウドからは未読、**要確認**） | 2026-10-27 | **要**：「VOICEVOX:冥鳴ひまり」 | 仮ナレ N1〜N9b（audio/vo_temp） |
| | | | | | | |
