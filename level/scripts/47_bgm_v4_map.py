"""編集計画 v4 用：曲の小節の地図と、つなぎ目の候補の「音色の近さ」を測る（41_bgm_structure.py の拡張。曲そのものは書き出さない）。
使い方:
  python3 scripts/47_bgm_v4_map.py <曲.mp3> <出力フォルダ> [beat0 秒] [拍の周期 秒] [拍子 既定4]
出力: <出力フォルダ>/map_<曲名>.md（小節ごとの音量・明るさ・密度・低音・8小節前との類似、拍の揺れ、つなぎ目の表）
つなぎ目の点数：「つなぐ前の小節の終わり 0.6 秒」と「つなぐ先の本来の直前の小節の終わり 0.6 秒」、
  「本来の次の小節の頭 0.6 秒」と「つなぐ先の小節の頭 0.6 秒」のメルスペクトル（dB）の距離の和。小さいほど自然（基準点の 12→25 は 69）。
  ＋クロマ（和音）の距離×100 も足した値を「和音込み」として出す。
出力は計画用の数字だけ（音は書き出さない）。出力フォルダは /mnt/project-files/level/audio_tests_v4/ を想定（リポジトリに入れない）。
"""
import sys, pathlib, itertools
import numpy as np, librosa

src = pathlib.Path(sys.argv[1]); out = pathlib.Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
SR = 22050
y, sr = librosa.load(src, sr=SR, mono=True)
tempo, beats = librosa.beat.beat_track(y=y, sr=sr, units="time")
bt = np.asarray(beats)
k = np.arange(len(bt)); p_fit, b_fit = np.polyfit(k, bt, 1)
resid = bt - (b_fit + p_fit * k)
B0 = float(sys.argv[3]) if len(sys.argv) > 3 else float(b_fit)
BP = float(sys.argv[4]) if len(sys.argv) > 4 else float(p_fit)
METER = int(sys.argv[5]) if len(sys.argv) > 5 else 4
BAR = METER * BP
hop = 512
rms = librosa.feature.rms(y=y, hop_length=hop)[0]
cen = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=hop)[0]
ons = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
mel = librosa.power_to_db(librosa.feature.melspectrogram(y=y, sr=sr, hop_length=hop, n_mels=64))
chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop)
t = librosa.frames_to_time(np.arange(mel.shape[1]), sr=sr, hop_length=hop)
nb = int((len(y) / sr - B0) / BAR)

def win(t0, t1, M):
    m = (t >= t0) & (t < t1)
    return M[:, m].mean(1) if m.any() else np.zeros(M.shape[0])

rows, feats = [], []
for i in range(nb):
    a, b = B0 + i * BAR, B0 + (i + 1) * BAR
    m = (t >= a) & (t < b)
    rows.append((i + 1, a, 20 * np.log10(rms[m].mean() + 1e-9), cen[m].mean(), ons[m].mean(), mel[:6, m].mean()))
    feats.append(chroma[:, m].mean(1))

def bar_t(n): return B0 + (n - 1) * BAR          # 小節 n の頭（曲の秒）

def splice(a_end, b_start):
    """a_end 小節の終わり → b_start 小節の頭へ跳ぶ。"""
    ta = bar_t(a_end + 1); tb = bar_t(b_start)
    pre = np.linalg.norm(win(ta - 0.6, ta, mel) - win(tb - 0.6, tb, mel))
    post = np.linalg.norm(win(ta, ta + 0.6, mel) - win(tb, tb + 0.6, mel))
    ch = np.linalg.norm(win(ta - 0.6, ta, chroma) / (np.linalg.norm(win(ta - 0.6, ta, chroma)) + 1e-9)
                        - win(tb - 0.6, tb, chroma) / (np.linalg.norm(win(tb - 0.6, tb, chroma)) + 1e-9))
    return pre + post, pre + post + 100 * ch

L = [f"# 曲の地図（編集計画 v4 用）：{src.name}", "",
     f"- 拍の周期 {BP:.5f} 秒（{60 / BP:.1f} BPM）、最初の拍 {B0:.3f} 秒、{METER}拍子、1小節 {BAR:.3f} 秒、小節数 {nb}、曲の長さ {len(y) / sr:.1f} 秒",
     f"- 拍検出の直線からのずれ：標準偏差 {resid.std() * 1000:.0f} ms、最大 {np.abs(resid).max() * 1000:.0f} ms"
     f"（前半 1/3 の周期 {np.polyfit(k[:len(k)//3], bt[:len(k)//3], 1)[0]:.4f}、後半 1/3 {np.polyfit(k[-len(k)//3:], bt[-len(k)//3:], 1)[0]:.4f} 秒）", "",
     "| 小節 | 開始(秒) | 音量 dB | 明るさ Hz | 音の密度 | 低音 dB | 8小節前との和音の類似 |", "|---|---|---|---|---|---|---|"]
for (i, a, db, c, o, bs), f in zip(rows, feats):
    sim = ""
    if i > 8:
        g = feats[i - 9]; sim = f"{np.dot(f, g) / (np.linalg.norm(f) * np.linalg.norm(g)):.2f}"
    L.append(f"| {i} | {a:.2f} | {db:.1f} | {c:.0f} | {o:.2f} | {bs:.1f} | {sim} |")

# つなぎ目の候補（曲ごとに引数で渡すより、ここに並べる。小節は 1 始まり：(つなぐ前の最後の小節, つなぐ先の最初の小節)）
CANDS = {
    "01_new_departure": [(12, 25), (16, 4), (16, 5), (16, 8), (16, 29), (12, 29), (28, 33), (29, 33), (24, 33), (10, 25), (10, 26),
                         (11, 25), (12, 26), (10, 29), (16, 25), (20, 25), (16, 21), (20, 33), (8, 8), (7, 8), (12, 8), (16, 9)],
    "02_shinryoku": [],
    "03_komorebi": [],
}
cands = CANDS.get(src.stem) or [(a, b) for a, b in itertools.product(range(4, nb, 4), range(5, nb, 4)) if b > a + 2][:40]
L += ["", "## つなぎ目の候補（小さいほど自然。基準点 v4.10 の 12→25 と比べる）", "",
      "| つなぎ（前の最後の小節 → 先の最初の小節） | 音色の距離 | 和音込み |", "|---|---|---|"]
for a, b in cands:
    if max(a + 1, b) <= nb:
        s, s2 = splice(a, b); L.append(f"| {a} → {b} | {s:.0f} | {s2:.0f} |")
(out / f"map_{src.stem}.md").write_text("\n".join(L) + "\n")
print("\n".join(L))
