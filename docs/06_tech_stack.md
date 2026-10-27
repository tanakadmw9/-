# 06 技術構成（無料・安全なツールだけで組む）

## 1. 採用するツール

| 用途 | ツール | ライセンス／費用 | 採用理由 |
|---|---|---|---|
| 素材解析・切り出し・色補正・音の処理・最終書き出し | **FFmpeg** | LGPL/GPL・無料 | 映像処理の業界標準。コマンドで正確に再現できる |
| 編集の組み立て（テロップ・図解・合成・音の配置） | **HyperFrames**（HeyGen製） | Apache-2.0・無料 | HTML/CSS/SVGで画面を作り、ローカルのChromeで1フレームずつ書き出す。AIエージェント向けに作られており、Claude Codeが最も得意な書き方で作れる。29.97fps指定、コマ撮りスナップショット、レイアウト・コントラスト検査、拍検出など検査機能が揃う |
| アニメーション | **GSAP** | 無料（Standard "no charge" License） | HyperFramesの標準。npmから入れてローカルで読み込む |
| フォント | **BIZ UDPゴシック／BIZ UDゴシック** | SIL OFL 1.1・無料 | UD書体で読みやすい。npm `@fontsource/biz-udpgothic` 等でも入手可 |
| 仮ナレーション | **VOICEVOX**（またはAivisSpeech） | 無料。キャラクター／モデルごとの規約に従う | ローカルで動く日本語音声合成 |
| 解析スクリプト | Python 3（numpy, opencv-python） | 無料 | フレームの色や焼き込み領域の自動チェック |
| 版管理 | Git | 無料 | ゲートごとに保存・巻き戻し |

キット作成時に、HyperFrames 0.8.206 で「実写カット＋日本語テロップ＋SVGアニメーション」を 1920×1080・29.97fps で書き出せることを確認済み。

## 2. 採用しないもの（と理由）

| ツール／機能 | 理由 |
|---|---|
| Remotion | 無料なのは個人・従業員3人以下の営利企業などに限られ、それ以外の企業は有料のCompany Licenseが必要 |
| AIによる映像のテロップ消去（ProPainter等） | 主要なものは非商用ライセンスが多く、動くカメラ・大面積では破綻しやすい |
| AI音楽生成（MusicGen等） | 公開されている重みが非商用ライセンス（CC BY-NC） |
| HyperFrames のクラウド系機能（`publish` / `cloud` / `lambda` / `cloudrun` / `auth`、`snapshot --describe`、`audio --quality best`） | 素材や画面を外部サービスに送ってしまう |
| HyperFrames 内蔵の `tts`（Kokoro） | 英語中心のモデル。日本語は実績のある VOICEVOX / AivisSpeech を優先する |
| オンラインの変換・編集サービス | 社内映像を外部にアップロードしない |
| 実在の人物・現場のAI生成画像／映像 | 記録映像としての信頼を損なう |

## 3. セットアップ

社用PCの場合は、ソフト導入とAI利用に関する社内ルールを先に確認すること。

### Windows（PowerShell）
```powershell
winget install --id Git.Git -e
winget install --id Gyan.FFmpeg -e
winget install --id OpenJS.NodeJS.LTS -e   # Node.js 22以上が必要
winget install --id Python.Python.3.12 -e
```
- プロジェクトは**日本語や空白を含まないパス**に置く（例：`C:\work\kijunten`）。
- VOICEVOX は公式サイトから入手して起動しておく（ローカルのエンジンが `http://127.0.0.1:50021` で待ち受ける）。

### Mac（Homebrew）
```bash
brew install git ffmpeg node python
```

### プロジェクト内（Claude Code に実行させてよい）
```bash
npm init -y
npm i -D hyperframes gsap @fontsource/biz-udpgothic @fontsource/biz-udgothic
npx hyperframes telemetry disable      # 匿名の利用統計を止める
npx hyperframes browser ensure         # 書き出し用Chromeの準備
npx hyperframes doctor                 # 環境チェック（FFmpeg / Chrome が ✓ ならよい）
```
- HyperFrames は更新が非常に速い。**作業開始時点の版で固定し、制作途中で上げない**（`package.json` に厳密な版を書く）。
- 社内ネットワークで Chrome のダウンロードが通らない場合は、インストール済みの Chrome を `HYPERFRAMES_BROWSER_PATH` で指定する。
- HyperFrames の Claude Code 用スキル（作り方の手引き）：
  ```bash
  claude plugin marketplace add heygen-com/hyperframes
  claude plugin install hyperframes@hyperframes
  ```
  スキルの見た目の既定値より、このキットの docs/04 を優先する。

## 4. フォルダ構成

```
kijunten/
├─ CLAUDE.md
├─ docs/            このキットの設計書（＋ decisions.md・credits_and_licenses.md）
├─ prompts/         Claude Code に渡すプロンプト
├─ .claude/agents/  レビュー用サブエージェント
├─ source/          元素材（読み取り専用。上書き・削除しない）
├─ analysis/        カット表、コンタクトシート、音声分析
├─ intermediate/    切り出し・色補正済みのカット（スクリプトで再生成できること）
├─ comp/            HyperFrames プロジェクト
│   ├─ timeline.json   尺・タイミングの唯一の正本
│   ├─ index.html      timeline.json から生成
│   ├─ compositions/   タイトル、図解D1〜D5、テロップ部品
│   ├─ styles/tokens.css
│   └─ assets/         フォント、GSAP、映像、音
├─ audio/           vo_temp/ vo_final/ bgm/ se/ amb/ ／ ミックス・マスター
├─ scripts/         解析・中間生成・ビルド・QC（すべて再実行可能に）
├─ renders/         draft/ review/ master/
├─ qc/              QCの出力（シート、レポート）
└─ deliver/         納品物
```
- 大きな映像・音声ファイルは Git に入れない（`.gitignore`）。スクリプトと設計書とコンポジションを Git で管理する。

## 5. 制作パイプライン

1. **解析**：`ffprobe` で仕様、シーン検出、カットごとのコンタクトシート（4fps程度をタイル状に）、焼き込みテロップ領域の確認。
2. **中間素材**：カットごとに、前後0.5秒の余裕をつけてフレーム単位で切り出し（ストリームコピーではなく再エンコード）、切り出し・拡大（lanczos）・色補正・デバンド・グレインを適用。音なし、高画質（H.264 CRF 10〜12 または ProRes 422 HQ）、29.97fps。
3. **組み立て**：HyperFrames のルートに `data-fps="30000/1001"`、1920×1080。各要素の開始・長さは **timeline.json から index.html を生成**する（ナレーション差し替えで尺が変わっても数値の修正だけで全体が追従する）。図解・タイトル・テロップは部品（sub-composition）にして変数で中身を渡す。
4. **音**：ナレ・BGM・効果音・環境音を `<audio>` として配置し、音量の変化はキーフレームで書く。書き出し後、FFmpeg の loudnorm（2パス）で −24 LUFS／True Peak −2 dBTP に整える。
5. **書き出し**：
   - 確認用：`npx hyperframes render comp -q draft --fps 30000/1001 -o renders/draft/<name>.mp4`
   - 試写用：`-q looks`、納品用：`-q delivery`
   - 最終は FFmpeg で、整えた音と合わせて MP4（H.264 High、yuv420p、BT.709 のタグ、AAC 48kHz 320kbps、`+faststart`）にする。
6. **検査**：docs/07 の自動チェックを毎回実行し、`qc/` に結果を残す。

## 6. Claude Code の使い方のコツ

- **動画は直接見られない**。必ずフレームを書き出して画像で確認する。1枚ずつより、タイル状のコンタクトシートで見るほうが効率がよい（読み込む画像が多すぎると会話の記憶を圧迫する）。
- **音は聞けない**。波形・スペクトログラム・ラウドネス・拍の検出結果で判断し、聞こえ方の最終判断は人間に任せる。
- ブラウザで時間軸を動かせるプレビュー（`npx hyperframes preview comp`）を人間の確認用に立ち上げる。人間がプレビュー上で選んだ要素は `--selection` で読み取れる。
- フェーズごとに新しいセッションで始めても困らないよう、決定事項は `docs/decisions.md` に必ず書く。
- 重い処理（書き出し）は、プレビューで十分に詰めてから。下書きは `-q draft` で。
