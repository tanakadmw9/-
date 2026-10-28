# 50 環境構築

## 1. 必要なもの

| もの | 版 | 備考 |
|---|---|---|
| OS | Linux、macOS、Windows は WSL2 | v4.10 は Ubuntu 24.04（クラウド）で作った |
| Node.js | 22 以上 | `npm ci` で HyperFrames 0.8.206・GSAP 3.15.0・@fontsource 5.3.0 が package-lock どおりに入る |
| Python | 3.10 以上 | 部品は `.venv/` に入る（00_setup.sh が作る。Ubuntu・WSL は `python3-venv` が要る）。版は requirements.lock（v4.10 で音がビット一致した版）、入らなければ requirements.txt（下限だけ） |
| FFmpeg | 6 以上 | 切り出し・色・音・書き出し・QC |
| Chromium | 何でもよい | 見つからなければ `npx hyperframes browser ensure` が用意する。場所は `HYPERFRAMES_BROWSER_PATH` でも指定できる |
| VOICEVOX エンジン | 0.26.x | 仮ナレを作り直すときだけ。§3 |
| ディスク | 約3GB | node_modules、中間素材、書き出し |

## 2. セットアップ

```bash
bash scripts/00_setup.sh      # npm ci → テレメトリ停止 → Python の部品（.venv）→ フォントと GSAP → Chromium → 環境チェック
bash scripts/00_doctor.sh     # いつでも：何がそろっていて何が足りないか
```

- Python の部品が入っていなければ `.venv/` を作ってそこに入れる（Ubuntu 24.04 や Mac の Homebrew の Python は、全体への pip を `externally-managed-environment` で断るため）。`scripts/*.sh` は `.venv` を自動で使う。`python3 scripts/…` を直接呼ぶ前は `source .venv/bin/activate`。
- 初回は回線しだいで 5〜15 分（librosa が numba・scikit-learn など約 90MB を連れてくる）。

素材（リポジトリに入れないもの）を置く：

| 置き場所 | 中身 | 入手 |
|---|---|---|
| `source/input.mp4` | 元映像（約40秒、1920×1080、29.97fps） | media の zip、または社内 |
| `source/music/01_new_departure.mp3` | BGM「New Departure」（FLASH☆BEAT） | OpenTracks https://opentracks.com/bgm/detail/6843 から人がダウンロード（source/README.md。MD5 で確かめる） |
| `assets/se/tones/decision28.mp3`・`decision6.mp3`・`cursor3.mp3`、`assets/se/foley/mechanical-pencil-write1.mp3` | 効果音 | 効果音ラボ https://soundeffect-lab.info/ から人がダウンロード（assets/README.md） |
| `audio/vo_temp/*.wav` | v4.10 の仮ナレ（任意） | media の zip。VOICEVOX が無い環境でもそのまま使える |

足りない素材は代わりで動く：効果音が無ければ自作の合成音（`SE_SET=synth` に自動で切り替わる）、曲が無ければ自作の仮BGM（テンポは格子どおりだが、曲の山がない確認用の音）。代わりで作った版は v4.10 と同じ音にならず、qc/<版>/report.md の「音の素材」が WARN になる。**仮BGM では「ナレとBGMの差」が FAIL になる**（試した値：短時間窓の p5 13.9 dB、基準 15 dB）。想定どおりなので 30_mix.py を直さない。曲を置けば消える。

最初から全部つくり直す：

```bash
bash scripts/70_build_all.sh v4.11            # 下書き（draft）。約20分（中間素材 5、書き出し 5、音と合わせる 1.5、QC 7.5）
bash scripts/70_build_all.sh v4.11 delivery   # 納品の画質
```

QC が FAIL でも終了コードは 0（書き出しを残すため）。成否は最後の行か report.md の「総合」で見る。`STRICT=1` を付けると FAIL で 1 を返す。

再現の確認：`bash scripts/46_compare_ref.sh renders/draft/<版>.mp4`（参考は media の `reference/renders/kijunten_v4.10.mp4`）。音はビット一致する。映像は同じ機械なら全コマ一致、別の機械では D1→D2 の写真が倒れる区間（27.4〜35.4 秒）にだけ目に見えない差（PSNR 46〜60 dB）が出る（Chromium のソフトウェア描画が CPU などで少し変わるため、と考えている）。合格は「音のビット一致＋映像の全コマ PSNR 45 dB 以上＋QC 総合 PASS」。

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
- Codex は起動したフォルダの AGENTS.md を読む。この一式の根で起動する。先に `git init` してコミットしておく（README「使い方」）。
- 書き出し（約14分）や全部の作り直し（約20分）は、1回のコマンドの時間制限で切られることがある。`nohup … > log 2>&1 &` で走らせてログを見るか、人が端末で実行する。Codex のサンドボックスの中で Chromium が起動できるかは確かめていない。起動できなければ書き出しだけ人が端末で行う。

### Codex クラウド（ブラウザのタスク）で使うとき
- GitHub のリポジトリが入口になる。**社内映像や購入・ダウンロードした音をリポジトリに入れるかは、会社の規程と各サイトの規約（再配布の禁止）で判断する**。入れない場合、クラウドでできるのは計画・原稿・図解のコード・QC の仕組みの作業までで、音つきの書き出しは PC で行う。
- 環境の設定（セットアップスクリプト）に `bash scripts/00_setup.sh` を入れる。セットアップ中だけネットワークが要る（npm、PyPI、Chrome の取得）。
- Docker は使えないことが多い。仮ナレは media の wav を使う。
- 独立レビューのフォルダ（qc/<版>/review_pack/）は映像とシートを含むので git に入らない（.gitignore）。クラウドの別タスクからは見えないので、独立レビューは PC の新しいセッションで行う。

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
| 曲の山が画の山と合わない、「ナレとBGMの差」が FAIL | 仮BGM で作っている（00_doctor.sh の ⚠️、report の「音の素材」）。New Departure を置く |
| `externally-managed-environment` で pip が止まる | `bash scripts/00_setup.sh` を使う（.venv に入れる）。`python3 -m venv` が失敗するなら `sudo apt-get install -y python3-venv` |
| 再現したのに映像の数コマが参考と違う | 27.4〜35.4 秒だけで PSNR 45 dB 以上なら、機械の違い（§2）。それ以外の区間なら原因を探す |
