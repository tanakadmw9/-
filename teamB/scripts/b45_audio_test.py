"""チームB：音の試作（曲の編集＋仮ナレ＋環境音＋効果音）を1本にまとめる。
曲：緑色の木漏れ日 1〜4小節 →（無音1.53秒＝測る「間」）→ 5〜6小節 → 19〜24小節（つなぎ目1か所、6→19）。
usage: python b45_audio_test.py <out_dir> [--no-vo]
VOICEVOX エンジン（localhost:50021、冥鳴ひまり style 14）が必要。
"""
import sys, json, subprocess, urllib.request, urllib.parse, numpy as np, soundfile as sf, os
OUT = sys.argv[1]; NOVO = '--no-vo' in sys.argv
SR = 48000; DUR = 61.5
A = '/mnt/project-files/assets/se/'; BGM = '/mnt/project-files/dova/03_komorebi.mp3'
os.makedirs(OUT, exist_ok=True)
def load(p):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-f', 'f32le', '-ac', '2', '-ar', str(SR), '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()
def db(x): return 10 ** (x / 20)
mix = {k: np.zeros((int(DUR * SR), 2), np.float32) for k in ('vo', 'bgm', 'amb', 'se')}
def place(layer, x, t, gain_db=0.0, fade_in=0.01, fade_out=0.01):
    x = x.copy() * db(gain_db); n = len(x)
    fi = int(fade_in * SR); fo = int(fade_out * SR)
    if fi: x[:fi] *= np.linspace(0, 1, fi)[:, None]
    if fo: x[-fo:] *= np.linspace(1, 0, fo)[:, None]
    s = int(t * SR); e = min(s + n, len(mix[layer]))
    if s < 0: x = x[-s:]; s = 0; e = min(len(x), len(mix[layer]))
    mix[layer][s:e] += x[:e - s]
# ---- 曲 ----
song = load(BGM)
def seg(a, b): return song[int(a * SR):int(b * SR)]
BAR1_FILM = 10.800; SONG_BAR1 = 1.356
place('bgm', seg(0.0, 17.720), BAR1_FILM - SONG_BAR1, fade_in=0.02, fade_out=0.30)          # 1〜4小節（拾い音から）
place('bgm', seg(17.690, 25.930), 28.694 - 0.030, fade_in=0.03, fade_out=0.06)             # 5〜6小節（打楽器が入る）
place('bgm', seg(74.960, 102.48), 36.875 - 0.030, fade_in=0.06, fade_out=0.8)              # 19〜24小節（6→19 のつなぎ、60ms重ね）
# ---- ナレ（仮）----
LINES = [('N1', 3.6, 'この人たちは、何をしに来たのでしょう。'), ('N2', 10.1, '地面に、“住所”をつけに来たのです。'),
         ('N3', 16.2, '住所がわかっている点を、「基準点」といいます。'), ('N4', 29.0, 'わかっている点から、向きと距離をはかれば、'),
         ('N5', 33.6, '新しい点の住所が、決まります。'), ('N7', 38.4, 'いいえ。ほかの点ともつないで、確かめます。'),
         ('N8', None, 'この点から、地図や道路の測量が始まります。'), ('N9', 46.6, '道ばたで、丸い金属のしるしを、探してみてください。'),
         ('N10', None, 'だれかが“住所”をつけた点、かもしれません。')]
log = []
def tts(text):
    q = urllib.parse.urlencode({'text': text, 'speaker': 14})
    aq = json.load(urllib.request.urlopen(urllib.request.Request(f'http://localhost:50021/audio_query?{q}', method='POST')))
    aq.update(speedScale=0.92, pitchScale=-0.02, intonationScale=1.05, prePhonemeLength=0.05, postPhonemeLength=0.1, outputSamplingRate=SR, outputStereo=True)
    wav = urllib.request.urlopen(urllib.request.Request('http://localhost:50021/synthesis?speaker=14', data=json.dumps(aq).encode(), headers={'Content-Type': 'application/json'})).read()
    p = f'{OUT}/_tmp.wav'; open(p, 'wb').write(wav); return load(p)
vo_windows = []
if not NOVO:
    end = 0
    for lid, t, text in LINES:
        x = tts(text)
        if t is None: t = end + (0.3 if lid == 'N8' else 1.0)
        place('vo', x, t, gain_db=-3)
        end = t + len(x) / SR; vo_windows.append((t, end)); log.append(f'{lid} {t:.2f}–{end:.2f}（{len(x)/SR:.2f}秒）{text}')
# ---- 環境音・足音・効果音 ----
amb = load(A + 'ambience/summer-countryside1.mp3'); wind = load(A + 'ambience/plants-swaying1.mp3')
place('amb', amb[:int(46 * SR)], 0.0, gain_db=-6, fade_in=0.7, fade_out=1.5)
place('amb', np.tile(wind, (2, 1))[:int(61 * SR)], 0.0, gain_db=4, fade_in=0.7, fade_out=2.0)
place('se', load(A + 'foley/walk-soil1.mp3')[:int(3.2 * SR)], 0.70, gain_db=-4, fade_out=0.4)     # S06 歩いてくる
place('se', load(A + 'foley/mechanical-pencil-write1.mp3')[:int(2.8 * SR)], 29.9, gain_db=-8, fade_out=0.4)  # S07 記録
place('se', load(A + 'tones/cursor3.mp3'), 27.70, gain_db=-6)        # 電子音① はかる（無音の「間」の中）
place('se', load(A + 'tones/decision28.mp3'), 35.85, gain_db=-9)     # 電子音② 住所が決まる
# ---- 音量の書き込み（手で書いた変化）----
t = np.arange(len(mix['bgm'])) / SR
def env(points):  # [(時刻, dB)] の折れ線
    ts, ds = zip(*points); return db(np.interp(t, ts, ds))[:, None].astype(np.float32)
# 曲：ナレ中は −16dB、ナレがない所は −7dB。下げはナレの0.4秒前から
g = np.full(len(t), -7.0)
for s, e in vo_windows:
    m = (t > s - 0.4) & (t < e + 0.3); g[m] = -16.0
g = np.convolve(g, np.ones(int(0.25 * SR)) / int(0.25 * SR), 'same')
mix['bgm'] *= db(g)[:, None].astype(np.float32)
# 環境音：測る「間」で一度ほぼ消す（息を止める）、分割画面では下げ、金属標で薄く
mix['amb'] *= env([(0, 0), (26.9, 0), (27.3, -14), (28.6, -14), (29.0, -8), (36.6, -8), (37.1, 0), (44.8, 0), (45.6, -9), (61.5, -9)])
out = mix['vo'] + mix['bgm'] + mix['amb'] + mix['se']
fade = np.ones(len(out)); n = int(0.7 * SR); fade[-n:] = np.linspace(1, 0, n); out *= fade[:, None]
raw = f'{OUT}/_mix.wav'; sf.write(raw, out, SR, subtype='FLOAT')
name = 'teamB_audio_test_v1' + ('_novo' if NOVO else '')
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', raw, '-af', 'loudnorm=I=-24:TP=-2:LRA=11', '-ar', '48000', '-b:a', '192k', f'{OUT}/{name}.mp3'], check=True)
for k in ('_tmp.wav', '_mix.wav'):
    if os.path.exists(f'{OUT}/{k}'): os.remove(f'{OUT}/{k}')
open(f'{OUT}/{name}_vo_times.txt', 'w').write('\n'.join(log) + '\n')
print('\n'.join(log))
