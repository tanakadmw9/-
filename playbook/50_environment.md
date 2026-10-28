# 50 環境構築

## 1. 必要なもの

| もの | 版 | 備考 |
|---|---|---|
| OS | Linux、macOS、Windows は WSL2 | v4.10 は Ubuntu 24.04（クラウド）で作った |
| Node.js | 22 以上 | `npm ci` で HyperFrames 0.8.206・GSAP 3.15.0・@fontsource 5.3.0 が package-lock どおりに入る |
| Python | 3.10 以上 | requirements.txt（numpy、scipy、soundfile、librosa、opencv-python-headless、pillow、matplotlib） |
| FFmpeg | 6 以上 | 切り出し・色・音・書き出し・QC |
| Chromium | 何でもよい | 見つからなければ `npx hyperframes browser ensure` が用意する。場所は `HYPERFRAMES_BROWSER_PATH` でも指定できる |
| VOICEVOX エンジン | 0.26.x | 仮ナレを作り直すときだけ。§3 |
| ディスク | 約3GB | node_modules、中間素材、書き出し |

## 2. セットアップ

```bash
bash scripts/00_setup.sh      # npm ci → テレメトリ停止 → pip → フォントと GSAP → Chromium → 環境チェック
bash scripts/00_doctor.sh     # いつでも：何がそろっていて何が足りないか
```

素材（リポジトリに入れないもの）を置く：

| 置き場所 | 中身 | 入手 |
|---|---|---|
| `source/input.mp4` | 元映像（約40秒、1920×1080、29.97fps） | media の zip、または社内 |
| `source/music/01_new_departure.mp3` | BGM「New Departure」（FLASH☆BEAT） | OpenTracks https://opentracks.com/bgm/detail/6843 から人がダウンロード（source/README.md） |
| `assets/se/tones/decision28.mp3`・`decision6.mp3`・`cursor3.mp3`、`assets/se/foley/mechanical-pencil-write1.mp3` | 効果音 | 効果音ラボ https://soundeffect-lab.info/ から人がダウンロード（assets/README.md） |
| `audio/vo_temp/*.wav` | v4.10 の仮ナレ（任意） | media の zip。VOICEVOX が無い環境でもそのまま使える |

足りない素材は代わりで動く：効果音が無ければ自作の合成音（`SE_SET=synth` に自動で切り替わる）、曲が無ければ自作の仮BGM（拍の格子と合わないので確認用だけ）。代わりで作った版は v4.10 と同じ音にならない。

最初から全部つくり直す：

```bash
bash scripts/70_build_all.sh v4.11            # 下書き（draft）。約15〜20分
bash scripts/70_build_all.sh v4.11 delivery   # 納品の画質
```

## 3. VOICEVOX（仮ナレ）

`scripts/11_tts_voicevox.py` はエンジンの HTTP API（既定 `http://127.0.0.1:50021`、`VOICEVOX_URL` で変更可）を使う。どれか1つで動かす。

1. **デスクトップ版アプリ**（Windows・Mac）：https://voicevox.hiroshiba.jp/ から入れて起動するだけで、同じ API が 50021 番で開く。
2. **Docker**：`docker run -d --name vv -p 50021:50021 voicevox/voicevox_engine:cpu-latest`
   - Docker Hub が 429 を返したら `mirror.gcr.io/voicevox/voicevox_engine:cpu-latest`。
   - Claude Code のクラウド環境では、`dockerd` を長い時間制限の背景タスクで起動する（既定の30分で止まる。`&` だけだと呼び出しの終わりに止まる）。失敗したら先に `pkill containerd`。
3. **media の zip の wav を使う**：audio/vo_temp/ に置けば、エンジンなしで v4.10 と同じ声になる（原稿を変えない限り）。
4. **予備（声は変わる）**：`pip install pyopenjtalk-plus` → `python3 scripts/10_tts_temp.py`。HTS Voice "Mei"（CC BY 3.0、クレジット要）。タイミング決めだけに使う。

声と読み方：冥鳴ひまり（style 14）、F版の数値は 20_craft_rules.md §6。クレジット「VOICEVOX:冥鳴ひまり」が必要。

## 4. Codex で使うとき

### おすすめ：Codex CLI を自分の PC で
- 素材（社内映像・BGM・効果音）が PC の外に出ない。VOICEVOX アプリも Docker も使える。書き出しも PC で行う。
- 先に人が端末で `bash scripts/00_setup.sh` を実行しておく（Codex のサンドボックスはネットワークを止めていることが多く、npm や pip が通らない）。
- サンドボックスでは `localhost:50021`（VOICEVOX）に届かないことがある。そのときは仮ナレの作り直しだけ人が端末で実行するか、承認して実行する。
- Codex は起動したフォルダの AGENTS.md を読む。この一式の根で起動する。

### Codex クラウド（ブラウザのタスク）で使うとき
- GitHub のリポジトリが入口になる。**社内映像や購入・ダウンロードした音をリポジトリに入れるかは、会社の規程と各サイトの規約（再配布の禁止）で判断する**。入れない場合、クラウドでできるのは計画・原稿・図解のコード・QC の仕組みの作業までで、音つきの書き出しは PC で行う。
- 環境の設定（セットアップスクリプト）に `bash scripts/00_setup.sh` を入れる。セットアップ中だけネットワークが要る（npm、PyPI、Chrome の取得）。
- Docker は使えないことが多い。仮ナレは media の wav を使う。

### 共通
- AGENTS.md は短く保つ（Codex は既定でおよそ 32KiB までしか読まない）。詳しいことは playbook/ と docs/ に置き、AGENTS.md から指す。
- 画像を見られる設定で使う（フレームやシートの画像を見て判断するため）。
- 独立レビューは別のセッションで（10_process.md §8）。

### Claude Code で使うとき
- CLAUDE.md が AGENTS.md を読み込む。独立レビューは `.claude/agents/video-reviewer.md` のサブエージェントでもよい。

## 5. ネットワーク

使うのはセットアップと素材の入手のときだけ。書き出しはネットに頼らない（フォントと GSAP はプロジェクト内のファイル）。

| 先 | 用途 |
|---|---|
| registry.npmjs.org | npm ci |
| pypi.org、files.pythonhosted.org | pip |
| Chrome for Testing の配布元 | `hyperframes browser ensure`（Chromium が無いときだけ） |
| Docker Hub または mirror.gcr.io | VOICEVOX の Docker イメージ |
| opentracks.com、dova-worker.tracks-cid.workers.dev | BGM の入手（人が行う） |
| soundeffect-lab.info | 効果音の入手（人が行う） |

## 6. 外部に送らない

- 禁止：`hyperframes publish / cloud / lambda / cloudrun / auth`、`hyperframes snapshot --describe`、`hyperframes audio --quality best`、オンラインの変換・文字起こし・アップスケールのサービス。
- HyperFrames のテレメトリは止める（`npx hyperframes telemetry disable`。scripts/lib_env.sh も `HYPERFRAMES_NO_TELEMETRY=1` を設定）。
- AI エージェント（Codex・Claude）自身は、読んだファイルやフレーム画像をそのサービスに送って処理する。社内映像を AI に見せてよいかは、会社の AI 利用の規程で確認する。

## 7. よくあるつまずき

| 症状 | 対処 |
|---|---|
| `44_text_timing.mjs` が import で落ちる | HyperFrames の版が 0.8.206 でない。`npm ci` をやり直す |
| 書き出しで Chrome が見つからない | `npx hyperframes browser ensure`、または `HYPERFRAMES_BROWSER_PATH` |
| `intermediate/B/meta.json` が無い | `python3 scripts/02_intermediates.py B`（source/input.mp4 が要る） |
| `audio/vo_temp/vo_timing.json` と wav が合わない | 原稿（comp/narration.json）を変えたら仮ナレを作り直す（`REDO_VO=1 bash scripts/70_build_all.sh …`） |
| QC のシートの文字が豆腐（□） | tools/fonts/BIZUDPGothic-Regular.ttf がある場所で実行しているか |
| 曲が拍に合わない | 仮BGM で作っている（00_doctor.sh の ⚠️）。New Departure を置く |
