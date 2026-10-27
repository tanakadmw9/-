"""ミックス：comp/timeline.json から VO / BGM / SE / AMB のステムと mix を作る（docs/05 §3, docs/08 §5）。

  python3 scripts/30_mix.py

入力
  VO  : timeline.vo[].src（comp/ からの相対。無ければ audio/vo_temp/<id>.wav）
  BGM : audio/bgm/bgm.wav（人間が選んだ曲。あればこちらを優先）／無ければ audio/bgm/temp_bgm.wav
        どちらもファイルの0秒を timeline.bgm.start に置く
  SE  : audio/se/<kind>.wav（timeline.se[]）
  AMB : audio/amb/amb.wav（timeline.amb[]）
出力
  audio/mix/{vo,bgm,se,amb}.wav, audio/mix/mix.wav（48kHz stereo 24bit、長さ = timeline.duration）
  audio/mix/keyframes.json（BGM・AMB の音量キーフレーム、各SEのゲイン、測定値）
  comp/assets/audio/mix.wav（mix のコピー）

レベル設計（すべて「ナレ基準 VO_REF」からの相対で、手書きのキーフレーム。サイドチェインは使わない）
  BGM : ナレ中 BGM_UNDER（区間の大きい所で −16dB、「間」明けは −15.5dB）、ナレ無し BGM_FREE（−7dB）。
        区間（ナレ区間／すき間）ごとに、曲のその区間の大きさ（短時間ラウドネス90%点）を測ってフェーダー位置を1つ決める
        ＝エンジニアが区間ごとにフェーダーを書くのと同じ。静かな所の持ち上げは最大 +8dB（曲の盛り上がりを残す）。
        下げ始めはナレ開始の 0.45 秒前、0.05 秒前に下げ終わる。上げはナレ終了 0.1 秒後から 0.6 秒かけて。
        間隔 1.5 秒未満のナレは1つの区間として扱う（ポンピング防止）。
        bgm.start より前は無音。bgm.pause の間は 0.12 秒で −40dB まで下げ、pause.end で戻す。
  AMB : 実写 約−20dB（校正値 −18.5：突風で上下するため実測の中央値が約−20になる値）、図解（id が d で始まる場面、2秒未満のすき間は結合）さらに −10dB、タイトル下 −6dB、
        エンドカードで下げて最後に無音へ。
  SE  : 種類ごとの目標（0.1秒窓ラウドネスの最大値で、ナレ VO_REF より lock −10 / join −12 / measure・click −16 dB）。
        短い音は 0.4 秒窓だと小さく測られ過大になりやすいので 0.1 秒窓で決める。ナレより大きくしない。
  切れ目：VO・BGM・AMB はすべての端に 10ms 以上のフェード。SE は合成時に 0 から立ち上がる（編集点ではない）＋末尾 10ms フェード。
仕上げ
  統合ラウドネスを測って −24 LUFS に合わせ（同じゲインを全ステムに）、True Peak が −2.0 dBTP を超える場合のみ
  先読みリミッター（ゲイン包絡を全ステムにも掛ける）→ ステムの和 = mix。最後に ffmpeg ebur128 で再測定（2パス目の確認）。
"""
import json, pathlib, shutil, subprocess, re, sys
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly
from scipy.ndimage import minimum_filter1d, uniform_filter1d

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib_audio import (SR, integrated, short_term, momentary, sliding_loudness, true_peak_db, db, fade_edges, keyframes_to_gain, vo_bgm_diff)

ROOT = pathlib.Path(__file__).resolve().parent.parent
T = json.loads((ROOT / "comp/timeline.json").read_text())
DUR = T["duration"]; N = int(round(DUR * SR))
MIX = ROOT / "audio/mix"

VO_REF = -20.0          # 各ナレ行をこの統合ラウドネスにそろえてから並べる（最後に全体を −24 に移す）
BGM_UNDER, BGM_FREE, BGM_PAUSE = -16.0, -7.0, -40.0
BGM_UNDER_OPEN_BONUS = 0.5   # 「間」明け（開く区間）はナレ下でも 0.5dB だけ上げる
SHORT_GAP, SHORT_GAP_RISE = 3.0, 5.0
BGM_MAX_BOOST = 8.0          # 曲の静かな所（入り）を持ち上げる上限。曲のダイナミクスをつぶし切らない
DUCK_PRE, DUCK_PRE_END, REL_DELAY, REL_LEN, MERGE_GAP = 0.45, 0.05, 0.10, 0.60, 1.5
AMB_LIVE, AMB_DIAG, AMB_TITLE = -18.5, -10.0, -6.0      # AMB_DIAG / AMB_TITLE は AMB_LIVE からの追加分
SE_TARGET = {"lock": -10.0, "join": -12.0, "measure": -16.0, "click": -16.0, "glow": -14.0}   # 0.1秒窓ラウドネスの最大値、VO_REF 比
TARGET_LUFS, TP_MAX = -24.0, -2.0


def load(path, want_stereo=True):
    x, sr = sf.read(str(path), always_2d=True, dtype="float64")
    if sr != SR:
        g = np.gcd(sr, SR); x = resample_poly(x, SR // g, sr // g, axis=0)
    if want_stereo and x.shape[1] == 1: x = np.repeat(x, 2, axis=1)
    if want_stereo and x.shape[1] > 2: x = x[:, :2]
    return x


def put(buf, x, t):
    n0 = int(round(t * SR))
    a, b = max(n0, 0), min(n0 + len(x), len(buf))
    if b > a: buf[a:b] += x[a - n0:b - n0]


def write(path, x):
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(path), x.astype(np.float32), SR, subtype="PCM_24")


def ff_ebur128(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", "ebur128=peak=true",
                        "-f", "null", "-"], capture_output=True, text=True).stderr
    tail = r[r.rfind("Summary:"):]
    I = float(re.search(r"I:\s+(-?[\d.]+) LUFS", tail).group(1))
    tp = float(re.search(r"Peak:\s+(-?[\d.inf]+) dBFS", tail).group(1))
    return I, tp


def merged(intervals, gap):
    out = []
    for s, e in sorted(intervals):
        if out and s - out[-1][1] < gap: out[-1][1] = max(out[-1][1], e)
        else: out.append([s, e])
    return out


def interval_env(intervals, pre, pre_end, rel_delay, rel_len, ts):
    """0..1 の区間包絡（区間の手前で上がり、後で下がる）を時刻 ts で評価。"""
    v = np.zeros_like(ts)
    for s, e in intervals:
        up = np.clip((ts - (s - pre)) / max(pre - pre_end, 1e-6), 0, 1)
        dn = np.clip(1 - (ts - (e + rel_delay)) / rel_len, 0, 1)
        v = np.maximum(v, np.minimum(up, dn))
    return v


def limiter(x, ceiling_db, look=0.005, release=0.08):
    """True Peak 用の簡易先読みリミッター。戻り値はゲイン包絡（全ステムに掛ける）。"""
    up = resample_poly(x, 4, 1, axis=0)
    pk = np.abs(up).max(axis=1).reshape(-1, 4).max(axis=1)[:len(x)]
    pk = np.pad(pk, (0, len(x) - len(pk)), mode="edge")
    need = np.minimum(1.0, db(ceiling_db) / np.maximum(pk, 1e-12))
    L = int(look * SR)
    g = minimum_filter1d(need, size=2 * L + 1, origin=0)
    g = np.minimum(g, uniform_filter1d(g, size=L, origin=0))
    # 戻りをなめらかに（指数リリース）
    out = g.copy(); a = np.exp(-1 / (release * SR))
    for i in range(1, len(out)):
        if out[i] > out[i - 1]: out[i] = a * out[i - 1] + (1 - a) * out[i]
    return out


def main():
    MIX.mkdir(parents=True, exist_ok=True)
    report = {"duration": DUR, "samples": N}

    # ---------------- VO ----------------
    vo = np.zeros((N, 2)); vo_iv = []
    for v in T["vo"]:
        p = ROOT / "comp" / v["src"]
        if not p.exists(): p = ROOT / "audio/vo_temp" / f"{v['id']}.wav"
        x = load(p, want_stereo=False)[:, 0]
        n = min(len(x), int(round(v["dur"] * SR))) if v.get("dur") else len(x)
        x = x[:n]
        g = VO_REF - integrated(x)
        x = fade_edges(x * db(g))
        put(vo, np.repeat(x[:, None], 2, 1), v["start"])
        vo_iv.append((v["start"], v["start"] + n / SR))
    report["vo_lines"] = len(vo_iv)

    # ---------------- BGM ----------------
    human = ROOT / "audio/bgm/bgm.wav"
    bgm_src = human if human.exists() else ROOT / "audio/bgm/temp_bgm.wav"
    b = load(bgm_src)
    B0, BEND = T["bgm"]["start"], T["bgm"]["end"] or DUR
    pause = T["bgm"].get("pause")                        # 曲を止める間（無いときは映像の外に置いて無効にする）
    PS, PE = (pause["start"], pause["end"]) if pause else (DUR + 10.0, DUR + 11.0)
    nb = min(len(b), int(round((BEND - B0) * SR)))
    b = b[:nb]
    b = fade_edges(b, 0.010, 0.050)
    if human.exists():
        tail = 20 * np.log10(np.sqrt((b[-int(0.5 * SR):] ** 2).mean()) + 1e-12) - integrated(b)
        if tail > -25:
            print(f"WARNING: bgm.wav is still loud at bgm.end ({tail:.1f} dB re its own loudness) — "
                  "edit the track by bars so it ends there (docs/05 §2: no fade-out mid-phrase).")
    bgm_raw = np.zeros((N, 2)); put(bgm_raw, b, B0)
    t_st, st = short_term(bgm_raw)

    def local_level(s, e):
        """区間 [s,e] の曲の大きさ（短時間ラウドネスの90%点）。BGM が鳴っていない区間は VO_REF（＝補正なし）。"""
        if e <= s: return VO_REF
        m = (t_st >= s) & (t_st <= e) & (st > -70)
        if not m.any():
            m = (np.abs(t_st - (s + e) / 2) == np.abs(t_st - (s + e) / 2).min()) & (st > -70)
        return float(np.percentile(st[m], 90)) if m.any() else VO_REF

    # ナレ区間（「間」で分けてから、1.5秒未満のすき間を結合）
    duck_iv = (merged([iv for iv in vo_iv if iv[1] <= PS + 0.2], MERGE_GAP)
               + merged([iv for iv in vo_iv if iv[1] > PS + 0.2], MERGE_GAP))
    # 区間ごとの目標レベル（VO_REF からの相対）→ 曲のその区間の大きさで割り戻した「フェーダー位置」
    under = [BGM_UNDER + (BGM_UNDER_OPEN_BONUS if s >= PE - 0.01 else 0) for s, e in duck_iv]
    duck_fader = [min(u + VO_REF - local_level(max(s, B0), e), BGM_MAX_BOOST) for u, (s, e) in zip(under, duck_iv)]
    gaps = [(B0, duck_iv[0][0] - DUCK_PRE)] + [(duck_iv[i][1] + REL_DELAY + REL_LEN, duck_iv[i + 1][0] - DUCK_PRE)
                                              for i in range(len(duck_iv) - 1)] + [(duck_iv[-1][1] + REL_DELAY + REL_LEN, BEND)]
    free_fader = []
    for s, e in gaps:
        s = max(s, B0)
        free_fader.append(None if e - s < 0.3 else min(BGM_FREE + VO_REF - local_level(s, e), BGM_MAX_BOOST))
    # 短いすき間（ナレ間 3 秒未満）は上げ幅を +5dB までに抑える（ポンピングに聞こえないように）
    for i in range(1, len(gaps) - 1):
        if free_fader[i] is not None and duck_iv[i][0] - duck_iv[i - 1][1] < SHORT_GAP:
            free_fader[i] = min(free_fader[i], max(duck_fader[i - 1], duck_fader[i]) + SHORT_GAP_RISE)
    base = []                                            # 手書き相当のキーフレーム (t, fader dB)
    for i, (s, e) in enumerate(duck_iv):
        if free_fader[i] is not None: base.append((s - DUCK_PRE, free_fader[i]))
        base += [(s - DUCK_PRE_END, duck_fader[i]), (e + REL_DELAY, duck_fader[i])]
        if free_fader[i + 1] is not None: base.append((e + REL_DELAY + REL_LEN, free_fader[i + 1]))
    if free_fader[0] is not None: base.insert(0, (0.0, free_fader[0]))
    if free_fader[-1] is not None: base.append((DUR, free_fader[-1]))
    else: base.append((DUR, duck_fader[-1]))
    base = sorted(base)
    kt = np.array(sorted({p[0] for p in base} | {PS, PS + 0.12, PE - 0.03, PE, B0}))
    kt = kt[(kt >= 0) & (kt <= DUR)]
    kdb = np.interp(kt, [p[0] for p in base], [p[1] for p in base])
    kdb += (BGM_PAUSE - BGM_FREE) * np.interp(kt, [PS, PS + 0.12, PE - 0.03, PE], [0, 1, 1, 0], left=0, right=0)
    bgm_kf = [(round(float(t), 4), round(float(d), 2)) for t, d in zip(kt, kdb)]
    gain = keyframes_to_gain(bgm_kf, N)
    gain[: int(round(B0 * SR))] = 0.0
    bgm = bgm_raw * gain[:, None]
    report["bgm_source"] = str(bgm_src.relative_to(ROOT))
    report["bgm_regions"] = ([{"type": "under_vo", "start": round(s, 3), "end": round(e, 3), "fader_db": round(f, 2)}
                              for (s, e), f in zip(duck_iv, duck_fader)]
                             + [{"type": "free", "start": round(s, 3), "end": round(e, 3),
                                 "fader_db": None if f is None else round(f, 2)} for (s, e), f in zip(gaps, free_fader)])

    # ---------------- AMB ----------------
    a = load(ROOT / "audio/amb/amb.wav")
    amb_ref = float(np.median(short_term(a)[1]))          # 突風で上下するので中央値で校正
    amb = np.zeros((N, 2))
    for seg in T["amb"]:
        s0 = seg["start"]; e0 = seg["end"] if seg["end"] is not None else DUR
        n = min(len(a), int(round((e0 - s0) * SR)))
        put(amb, fade_edges(a[:n], 0.5, 0.010), s0)
    amb *= db(VO_REF - amb_ref)
    diag = merged([(s["start"], s["start"] + s["dur"]) for s in T["scenes"] if s.get("diagram", s["id"].startswith("d"))], 2.0)
    title = [(s["start"], s["start"] + s["dur"]) for s in T["scenes"] if s["id"] == "title"]
    endc = [s for s in T["scenes"] if s["id"] == "endcard"]
    kt = {0.0, DUR}
    for s, e in diag + title: kt |= {s - 0.3, s + 0.5, e - 0.5, e + 0.3}
    kt = np.array(sorted(t for t in kt if 0 <= t <= DUR) + [DUR])
    if endc:
        es = endc[0]["start"]; kt = np.array(sorted(set(kt[kt < es]) | {es, es + 1.0, DUR - 0.3, DUR}))
    lvl = (AMB_LIVE + AMB_DIAG * interval_env(diag, 0.3, -0.5, -0.5, 0.8, kt)
           + AMB_TITLE * interval_env(title, 0.3, -0.5, -0.5, 0.8, kt))
    if endc:
        es = endc[0]["start"]
        lvl = np.where(kt >= es + 1.0, AMB_LIVE - 10, lvl)
        lvl = np.where(kt >= DUR - 0.3, -90.0, lvl)
    amb_kf = [(round(float(t), 4), round(float(d), 2)) for t, d in zip(kt, lvl)]
    amb *= keyframes_to_gain(amb_kf, N)[:, None]
    amb = fade_edges(amb, 0.0, 0.010)

    # ---------------- SE ----------------
    se = np.zeros((N, 2)); se_gain = []
    for e in T["se"]:
        x = load(ROOT / f"audio/se/{e['kind']}.wav", want_stereo=False)[:, 0]
        pad = np.concatenate([np.zeros(int(0.2 * SR)), x, np.zeros(int(0.4 * SR))])
        mmax = sliding_loudness(pad, 0.1, 0.01)[1].max()   # 短い音は 0.1 秒窓で（耳の積分時間に近い）
        g = VO_REF + SE_TARGET.get(e["kind"], -12.0) - mmax + e.get("gain_db", 0.0)   # gain_db：その回だけ小さく
        x = fade_edges(x * db(g), 0.0, 0.010)
        put(se, np.repeat(x[:, None], 2, 1), e["start"])
        se_gain.append({"kind": e["kind"], "t": e["start"], "gain_db": round(g, 2),
                        "loudness100ms_re_vo_ref_db": SE_TARGET.get(e["kind"], -12.0)})

    # ---------------- 合成・ラウドネス合わせ ----------------
    stems = {"vo": vo, "bgm": bgm, "se": se, "amb": amb}
    mix = vo + bgm + se + amb
    for it in range(2):                                   # 2パス：測る → 合わせる → もう一度測る
        I = integrated(mix); g = db(TARGET_LUFS - I)
        mix *= g
        for k in stems: stems[k] *= g
    tp = true_peak_db(mix); lim = None
    if tp > TP_MAX - 0.2:
        env = limiter(mix, TP_MAX - 0.5)
        mix *= env[:, None]
        for k in stems: stems[k] *= env[:, None]
        lim = float(20 * np.log10(env.min()))
        I = integrated(mix); g = db(TARGET_LUFS - I); mix *= g
        for k in stems: stems[k] *= g
    final_gain_db = 20 * np.log10(np.abs(mix).max() / max(np.abs(vo + bgm + se + amb).max(), 1e-12))  # 参考
    for k, x in stems.items(): write(MIX / f"{k}.wav", x)
    write(MIX / "mix.wav", mix)
    dst = ROOT / "comp/assets/audio/mix.wav"; dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(MIX / "mix.wav", dst)

    # ---------------- レポート ----------------
    I_py = integrated(mix); tp = true_peak_db(mix)
    I_ff, tp_ff = ff_ebur128(MIX / "mix.wav")
    resid = np.abs(mix - sum(stems.values())).max()
    t, vo_st = short_term(stems["vo"]); _, bg_st = short_term(stems["bgm"])
    in_vo = np.zeros_like(t, bool)
    for s, e in vo_iv: in_vo |= (t >= s) & (t <= e)
    per_line, diff = vo_bgm_diff(stems["vo"], stems["bgm"], [(v["id"], s, e) for v, (s, e) in zip(T["vo"], vo_iv)])
    tm, vo_m = momentary(stems["vo"]); _, se_m = momentary(stems["se"]); _, am_st = short_term(stems["amb"])
    vo_level = np.median(vo_st[in_vo])
    live = np.ones_like(t, bool)
    for s, e in diag + title: live &= ~((t >= s) & (t <= e))
    endc_s = endc[0]["start"] if endc else DUR
    rep = {
        "integrated_lufs_py": round(I_py, 2), "integrated_lufs_ffmpeg": I_ff,
        "true_peak_dbtp_py": round(tp, 2), "true_peak_dbtp_ffmpeg": tp_ff, "limiter_max_gr_db": lim,
        "stems_sum_residual": float(resid),
        "vo_minus_bgm_per_line_db": per_line,
        "vo_minus_bgm_short_term_inside_lines": diff,
        "vo_median_short_term_lufs": round(float(vo_level), 1),
        "bgm_free_max_short_term_re_vo": round(float(bg_st[~in_vo & (t > B0)].max() - vo_level), 1),
        "amb_re_vo_live_median": round(float(np.median(am_st[live & (t < endc_s) & (t > 1.6)]) - vo_level), 1),
        "amb_re_vo_diagram_median": round(float(np.median(am_st[~live]) - vo_level), 1),
        "se_max_100ms_re_vo_max_100ms": round(float(sliding_loudness(stems["se"], 0.1, 0.01)[1].max()
                                                     - sliding_loudness(stems["vo"], 0.1, 0.01)[1].max()), 1),
        "se_max_100ms_re_vo_integrated": round(float(sliding_loudness(stems["se"], 0.1, 0.01)[1].max()
                                                     - integrated(stems["vo"])), 1),
        "se_peak_re_vo_peak_db": round(float(20 * np.log10(np.abs(stems["se"]).max() / np.abs(stems["vo"]).max())), 1),
        "bgm_in_pause_short_term_lufs": (round(float(momentary(stems["bgm"])[1][(tm > PS + 0.25) & (tm < PE - 0.25)].max()), 1)
                                         if pause else None),
    }
    report.update(rep)
    (MIX / "keyframes.json").write_text(json.dumps(
        {"note": "dB は VO_REF（各ナレ行の統合ラウドネス）からの相対。ラウドネス合わせ前の値。",
         "bgm_keyframes": bgm_kf, "amb_keyframes": amb_kf, "se": se_gain, "report": report}, ensure_ascii=False, indent=1))

    print(f"BGM source : {report['bgm_source']}")
    print(f"length     : {len(mix)} samples = {len(mix)/SR:.4f} s (timeline {DUR})")
    print(f"Integrated : {I_py:.2f} LUFS (ffmpeg ebur128 {I_ff:.1f})   target {TARGET_LUFS} ±1")
    print(f"True peak  : {tp:.2f} dBTP (ffmpeg {tp_ff:.1f})   max {TP_MAX}   limiter GR: {lim}")
    d = rep["vo_minus_bgm_short_term_inside_lines"]
    print(f"VO−BGM (3s short-term windows fully inside a VO line): median {d['median']} dB, p5 {d['p5']} dB, min {d['min']} dB  (need ≥15)")
    pl = rep["vo_minus_bgm_per_line_db"]
    print("VO−BGM per line (VO integrated − BGM mean level over the line): "
          + ", ".join(f"{k} {'no BGM' if v is None else v}" for k, v in pl.items()))
    print(f"BGM max between lines (re VO median): {rep['bgm_free_max_short_term_re_vo']} dB   BGM in pause: {rep['bgm_in_pause_short_term_lufs']} LUFS")
    print(f"AMB re VO (median short-term): live {rep['amb_re_vo_live_median']} dB, diagrams {rep['amb_re_vo_diagram_median']} dB")
    print(f"SE loudest (0.1s window) re VO integrated: {rep['se_max_100ms_re_vo_integrated']} dB; re VO loudest 0.1s: "
          f"{rep['se_max_100ms_re_vo_max_100ms']} dB; SE sample peak re VO peak {rep['se_peak_re_vo_peak_db']} dB")
    print(f"stems sum residual: {resid:.2e}")
    print(f"-> {MIX}/{{vo,bgm,se,amb,mix}}.wav, {dst}")


if __name__ == "__main__":
    main()
