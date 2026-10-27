#!/usr/bin/env python3
"""Generates comp/compositions/d4_bridge.html and d5_everyday.html from one geometry
(d5 starts on exactly d4's last frame)."""
import json, math, pathlib
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "comp/compositions"
T = json.loads((ROOT / "comp/timeline.json").read_text())
SC = {s["id"]: s for s in T["scenes"]}

# ---------------- geometry (1920x1080) ----------------
RIVER = "M1290.5 -159 L1239 -40 C1079 330 889 700 699 1120 L645 1238"     # centerline; band = stroke
RIVER_W = 250                                     # grid band; banks are 3px navy outside it
ROAD = "M-30 704 C330 704 520 560 760 560 L1180 560 C1400 560 1580 452 1950 452"
ROAD_Y = 560
BANK_L, BANK_R = 819.4, 1104.1                    # river edges on the road line
BR_L0, BR_R0 = 794, 1130                          # bridge ends on land (abutments)
MID = 962.0                                       # where the halves meet
GAP = 84
TIP_L, TIP_R = MID - GAP / 2, MID + GAP / 2
BR_H = 50
S = (760, 340)                                    # 同じ基準点（d4）
HERE_I = 5                                        # 道路わきの基準点（d5「ここから」）
POINTS = [S, (690, 130), (300, 380), (520, 800), (230, 870), (680, 650),          # 左岸
          (1330, 260), (1640, 200), (1700, 600), (1300, 690), (1160, 920), (1560, 890)]  # 右岸
HERE = POINTS[HERE_I]
LINKS = [(0, 1), (0, 5), (1, 2), (2, 5), (2, 4), (4, 3), (3, 5),
         (6, 7), (7, 8), (6, 9), (8, 9), (9, 10), (10, 11), (11, 8), (9, 11)]
CROSS = [(0, 6), (5, 9), (3, 10)]                 # 川越しの観測線：両岸は1つの網
CENTER = (MID, ROAD_Y)
RING_R = 46


def cubic_pts(p, n=4000):
    p = np.array(p, float)
    t = np.linspace(0, 1, n)[:, None]
    return (1 - t) ** 3 * p[0] + 3 * (1 - t) ** 2 * t * p[1] + 3 * (1 - t) * t ** 2 * p[2] + t ** 3 * p[3]


ROAD_PTS = np.vstack([cubic_pts([(-30, 704), (330, 704), (520, 560), (760, 560)]),
                      np.linspace((760, 560), (1180, 560), 400),
                      cubic_pts([(1180, 560), (1400, 560), (1580, 452), (1950, 452)])])


def road_y(x):
    i = np.argmin(abs(ROAD_PTS[:, 0] - x))
    return float(ROAD_PTS[i, 1])


def tri(side=52):
    # same shape as d2 (M0 -38 L32.9 19 L-32.9 19 Z) scaled to ~0.8
    k = side / 65.8
    return f"M0 {-38*k:.1f} L{32.9*k:.1f} {19*k:.1f} L{-32.9*k:.1f} {19*k:.1f} Z"


TRI = tri()


def ring_pt(tip):
    dx, dy = tip[0] - S[0], tip[1] - S[1]
    L = math.hypot(dx, dy)
    return S[0] + dx / L * (RING_R + 4), S[1] + dy / L * (RING_R + 4)


RL = ring_pt((TIP_L, ROAD_Y))
RR = ring_pt((TIP_R, ROAD_Y))


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


# ---------------- shared markup ----------------
def grid(pfx):
    return f'''      <defs>
        <pattern id="{pfx}-gridpat" x="0" y="40" width="80" height="80" patternUnits="userSpaceOnUse">
          <path d="M80 0 H0 V80" fill="none" stroke="var(--grid)" stroke-width="1.5"/>
        </pattern>
        <mask id="{pfx}-roadmask" maskUnits="userSpaceOnUse" x="0" y="0" width="1920" height="1080">
          <path id="{pfx}-roadmask-path" d="{ROAD}" fill="none" stroke="#fff" stroke-width="24" pathLength="100" stroke-dasharray="100 120" stroke-dashoffset="{{MASKOFF}}"/>
        </mask>
      </defs>
      <rect x="0" y="0" width="1920" height="1080" fill="url(#{pfx}-gridpat)"/>
      <!-- 川：紺の細い岸線（下の太い線）＋ --grid の帯 -->
      <path d="{RIVER}" fill="none" stroke="var(--navy)" stroke-width="{RIVER_W + 7}"/>
      <path d="{RIVER}" fill="none" stroke="var(--grid)" stroke-width="{RIVER_W}"/>
'''


LINK_O, CROSS_O = 0.68, 1.0


def network(pfx, vis):
    o = 1 if vis else 0
    s = [f'      <g id="{pfx}-links" stroke="var(--navy)" stroke-linecap="round">\n']
    for k, (a, b) in enumerate(LINKS):
        pa, pb = POINTS[a], POINTS[b]
        s.append(f'        <line id="{pfx}-ln{k}" x1="{pa[0]}" y1="{pa[1]}" x2="{pb[0]}" y2="{pb[1]}" stroke-width="3.5" opacity="{LINK_O*o}"/>\n')
    s.append('        <!-- 川越しの観測線（少し強く） -->\n')
    for k, (a, b) in enumerate(CROSS):
        pa, pb = POINTS[a], POINTS[b]
        s.append(f'        <line id="{pfx}-xl{k}" x1="{pa[0]}" y1="{pa[1]}" x2="{pb[0]}" y2="{pb[1]}" stroke-width="5" opacity="{CROSS_O*o}"/>\n')
    s.append('      </g>\n')
    return "".join(s)


def points(pfx, vis, s_scale=1.0):
    o = 1 if vis else 0
    s = []
    for k, (x, y) in enumerate(POINTS):
        sc = ""
        s.append(f'      <g transform="translate({x} {y})"><g id="{pfx}-p{k}" opacity="{o}"{sc}>'
                 f'<path d="{TRI}" fill="var(--paper)" stroke="var(--navy)" stroke-width="5" stroke-linejoin="round"/>'
                 f'<circle r="5" fill="var(--navy)"/></g></g>\n')
    return "".join(s)


def bridge(pfx, scale, seam_o):
    """two ink halves growing from the banks; scale = fraction of (abutment -> MID)."""
    wl = MID - BR_L0
    wr = BR_R0 - MID
    y0 = ROAD_Y - BR_H / 2
    # 地形図の橋の記号の「はね」（橋台の印）
    f = 16
    wings = (f"M{BR_L0} {y0} l{-f} {-f} M{BR_L0} {y0+BR_H} l{-f} {f} "
             f"M{BR_R0} {y0} l{f} {-f} M{BR_R0} {y0+BR_H} l{f} {f}")
    return f'''      <path id="{pfx}-wings" d="{wings}" fill="none" stroke="var(--ink)" stroke-width="5" stroke-linecap="round" opacity="{1 if scale > 0 else 0}"/>
      <rect id="{pfx}-brL" x="{BR_L0}" y="{y0}" width="{wl}" height="{BR_H}" fill="var(--ink)"/>
      <rect id="{pfx}-brR" x="{MID}" y="{y0}" width="{wr}" height="{BR_H}" fill="var(--ink)"/>
      <line id="{pfx}-seam" x1="{MID}" y1="{y0+6}" x2="{MID}" y2="{y0+BR_H-6}" stroke="var(--paper)" stroke-width="2" opacity="{seam_o}"/>
'''


def same_point(pfx, drawn):
    off = 0 if drawn else 100
    o = 1 if drawn else 0
    return f'''      <circle id="{pfx}-ring" cx="{S[0]}" cy="{S[1]}" r="{RING_R}" fill="none" stroke="var(--orange)" stroke-width="5"
              pathLength="100" stroke-dasharray="100 120" stroke-dashoffset="{off}" transform="rotate(-90 {S[0]} {S[1]})"/>
      <g id="{pfx}-tie" stroke="var(--orange)" stroke-linecap="round" fill="none">
        <path id="{pfx}-glowL" d="M{TIP_L} {ROAD_Y} L{RL[0]:.1f} {RL[1]:.1f}" stroke-width="16" opacity="{0.18*o}" pathLength="100" stroke-dasharray="100 120" stroke-dashoffset="{off}"/>
        <path id="{pfx}-glowR" d="M{TIP_R} {ROAD_Y} L{RR[0]:.1f} {RR[1]:.1f}" stroke-width="16" opacity="{0.18*o}" pathLength="100" stroke-dasharray="100 120" stroke-dashoffset="{off}"/>
        <path id="{pfx}-tieL" d="M{TIP_L} {ROAD_Y} L{RL[0]:.1f} {RL[1]:.1f}" stroke-width="5" pathLength="100" stroke-dasharray="100 120" stroke-dashoffset="{off}"/>
        <path id="{pfx}-tieR" d="M{TIP_R} {ROAD_Y} L{RR[0]:.1f} {RR[1]:.1f}" stroke-width="5" pathLength="100" stroke-dasharray="100 120" stroke-dashoffset="{off}"/>
        <circle id="{pfx}-tipL" cx="{TIP_L}" cy="{ROAD_Y}" r="6" fill="var(--orange)" stroke="none" opacity="{o}"/>
        <circle id="{pfx}-tipR" cx="{TIP_R}" cy="{ROAD_Y}" r="6" fill="var(--orange)" stroke="none" opacity="{o}"/>
      </g>
'''


LABEL_CSS = '''    .{p}-label {{ position: absolute; font-family: var(--font-ja); font-weight: 700; color: var(--ink);
      font-feature-settings: "palt"; line-height: 1.2; white-space: nowrap; }}
    #{p}-same {{ right: {r}px; top: {t}px; font-size: 52px; padding: 2px 14px; background: var(--paper); border-radius: 6px; }}
    #{p}-river {{ left: {rx}px; top: {ry}px; font-size: 44px; }}'''


RIVER_LABEL_Y = 960


def river_label_pos():
    # centerline x at y=RIVER_LABEL_Y
    pts = cubic_pts([(1239, -40), (1079, 330), (889, 700), (699, 1120)])
    i = np.argmin(abs(pts[:, 1] - RIVER_LABEL_Y))
    return float(pts[i, 0])


RX = river_label_pos()


def head(sid, extra_vars=""):
    sc = SC[sid]
    cues = json.dumps(sc["cues"], separators=(",", ":"))
    v = [{"id": "cues", "type": "string", "label": "cues", "default": cues},
         {"id": "dur", "type": "number", "label": "dur", "default": sc["dur"]}]
    return f"<html data-composition-variables='{json.dumps(v, ensure_ascii=False)}'>\n<body>\n<template>\n"


def label_css(p):
    return LABEL_CSS.format(p=p, r=1920 - (S[0] - RING_R - 10), t=S[1] - 33, rx=RX - 22, ry=RIVER_LABEL_Y - 27)


# ---------------- d4_bridge ----------------
def d4():
    p = "d4"
    HOLD = ' data-hold="true"'
    order = sorted(range(len(POINTS)), key=lambda k: dist(POINTS[k], CENTER))
    dmax = max(dist(q, CENTER) for q in POINTS)
    pt_delay = {k: 0.5 * dist(POINTS[k], CENTER) / dmax for k in range(len(POINTS))}
    link_delay = [max(pt_delay[a], pt_delay[b]) + 0.12 for a, b in LINKS]
    cross_delay = [max(pt_delay[a], pt_delay[b]) + 0.18 for a, b in CROSS]
    html = head("d4_bridge") + f'''  <style>
    #root {{ position: absolute; inset: 0; background: var(--paper); overflow: hidden; }}
    #{p}-svg {{ position: absolute; inset: 0; width: 1920px; height: 1080px; }}
{label_css(p)}
  </style>
  <div id="root" data-composition-id="d4_bridge" data-width="1920" data-height="1080">
    <svg id="{p}-svg" viewBox="0 0 1920 1080" aria-hidden="true" data-layout-allow-overflow{HOLD}>
{grid(p).replace("{MASKOFF}", "100")}{network(p, False)}
      <!-- 道路の設計線（紺の点線6px）。マスクで左から右へ描く -->
      <path id="{p}-road" d="{ROAD}" fill="none" stroke="var(--navy)" stroke-width="6" stroke-linecap="round" stroke-dasharray="0 16" mask="url(#{p}-roadmask)"/>
{points(p, False)}{bridge(p, 0, 0)}{same_point(p, False)}    </svg>
    <div id="{p}-river" class="{p}-label">川</div>
    <div id="{p}-same" class="{p}-label" style="opacity:0">同じ基準点</div>
  </div>
  <script>
    (function () {{
      const v = window.__hyperframes.getVariables();
      const c = JSON.parse(v.cues);
      const tl = gsap.timeline({{ paused: true }});
      const MIDSCALE = {(TIP_L - BR_L0) / (MID - BR_L0):.5f};   // 橋の先が中央の手前で止まる位置

      // network：基準点が中心から外へ波のように広がって網になる（0.9秒）
      const ptDelay = {json.dumps([round(pt_delay[k], 3) for k in range(len(POINTS))])};
      ptDelay.forEach((d, k) => {{
        tl.fromTo("#{p}-p" + k, {{ opacity: 0, scale: 0.4, transformOrigin: "50% 64%" }},
          {{ opacity: 1, scale: 1, transformOrigin: "50% 64%", duration: 0.36, ease: "power3.out" }}, c.network + d);
      }});
      const lnDelay = {json.dumps([round(x, 3) for x in link_delay])};
      lnDelay.forEach((d, k) => {{
        tl.fromTo("#{p}-ln" + k, {{ opacity: 0 }}, {{ opacity: {LINK_O}, duration: 0.3, ease: "power1.out" }}, c.network + d);
      }});
      // 川越しの観測線：両岸の点は1つの網
      const xlDelay = {json.dumps([round(x, 3) for x in cross_delay])};
      xlDelay.forEach((d, k) => {{
        tl.fromTo("#{p}-xl" + k, {{ opacity: 0 }}, {{ opacity: {CROSS_O}, duration: 0.3, ease: "power1.out" }}, c.network + d);
      }});

      // road：網の点をたどるように、設計線が左から右へ（川を横切る）
      tl.fromTo("#{p}-roadmask-path", {{ strokeDashoffset: 100 }}, {{ strokeDashoffset: 0, duration: 1.4, ease: "power2.inOut" }}, c.road);

      // banks → pause：両岸から橋が同時にのび、ゆっくり減速しながら「真ん中で…」の間ものび続け、
      // pause でちょうど止まる（すき間が残る）。middle は「止まり始める」目安（減速カーブで自然に通過）
      tl.fromTo("#{p}-wings", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.3, ease: "power2.out" }}, c.banks);
      tl.fromTo("#{p}-brL", {{ scaleX: 0, transformOrigin: "0% 50%" }}, {{ scaleX: MIDSCALE, transformOrigin: "0% 50%", duration: c.pause - c.banks, ease: "power1.out" }}, c.banks);
      tl.fromTo("#{p}-brR", {{ scaleX: 0, transformOrigin: "100% 50%" }}, {{ scaleX: MIDSCALE, transformOrigin: "100% 50%", duration: c.pause - c.banks, ease: "power1.out" }}, c.banks);

      // pause：何も動かさない（c.pause 〜 c.same_point の 1.0 秒だけが完全な静止）

      // same_point：網の中の基準点を1つ強調 → 両側の橋の先からオレンジの線が結ばれて光る
      const sp = c.same_point;
      tl.fromTo("#{p}-p0", {{ scale: 1, transformOrigin: "50% 64%" }}, {{ scale: 1.2, transformOrigin: "50% 64%", duration: 0.45, ease: "power3.out", immediateRender: false }}, sp);
      tl.fromTo("#{p}-ring", {{ strokeDashoffset: 100 }}, {{ strokeDashoffset: 0, duration: 0.45, ease: "power2.out" }}, sp);
      tl.fromTo("#{p}-same", {{ opacity: 0, y: 16 }}, {{ opacity: 1, y: 0, duration: 0.5, ease: "power3.out" }}, sp + 0.1);
      tl.fromTo(["#{p}-tipL", "#{p}-tipR"], {{ opacity: 0 }}, {{ opacity: 1, duration: 0.15, ease: "power1.out" }}, sp + 0.22);
      tl.fromTo(["#{p}-tieL", "#{p}-tieR", "#{p}-glowL", "#{p}-glowR"], {{ strokeDashoffset: 100 }},
        {{ strokeDashoffset: 0, duration: 0.5, ease: "power2.inOut" }}, sp + 0.22);
      tl.fromTo(["#{p}-glowL", "#{p}-glowR"], {{ opacity: 0 }}, {{ opacity: 0.34, duration: 0.3, ease: "power2.out" }}, sp + 0.5);
      tl.fromTo(["#{p}-glowL", "#{p}-glowR"], {{ opacity: 0.34 }}, {{ opacity: 0.18, duration: 0.6, ease: "power2.inOut", immediateRender: false }}, c.join + 0.05);

      // join：すき間が閉じて1本に（接する瞬間 = c.join、効果音「カチッ」）
      tl.fromTo(["#{p}-brL", "#{p}-brR"], {{ scaleX: MIDSCALE }}, {{ scaleX: 1, duration: 0.22, ease: "power2.in", immediateRender: false }}, c.join - 0.22);
      tl.fromTo(["#{p}-tipL", "#{p}-tipR"], {{ opacity: 1 }}, {{ opacity: 0, duration: 0.12, ease: "power1.in", immediateRender: false }}, c.join - 0.12);
      tl.fromTo("#{p}-seam", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.05, ease: "none" }}, c.join);

      window.__timelines["d4_bridge"] = tl;
    }})();
  </script>
</template>
</body>
</html>
'''
    (OUT / "d4_bridge.html").write_text(html)


# ---------------- d5_everyday ----------------
def house(x, base, w, h, r):
    door = min(9, w * 0.13)
    return (f"M{x-w/2:.0f} {base:.0f} V{base-h:.0f} L{x:.0f} {base-h-r:.0f} L{x+w/2:.0f} {base-h:.0f} V{base:.0f} Z "
            f"M{x-door:.0f} {base:.0f} V{base-h*0.48:.0f} H{x+door:.0f} V{base:.0f}")


def tree(x, base, r=19, trunk=20):
    return f"M{x:.0f} {base:.0f} V{base-trunk:.0f} M{x+r:.0f} {base-trunk-r:.0f} A{r} {r} 0 1 1 {x-r:.0f} {base-trunk-r:.0f} A{r} {r} 0 1 1 {x+r:.0f} {base-trunk-r:.0f}"


_RIV = None


def bank_x(y):
    """outer edges of the river (left, right) at height y."""
    global _RIV
    if _RIV is None:
        P = np.array([[1239, -40], [1079, 330], [889, 700], [699, 1120]], float)
        B = cubic_pts(P, 8000)
        d = np.gradient(B, axis=0); d /= np.linalg.norm(d, axis=1)[:, None]
        n = np.stack([d[:, 1], -d[:, 0]], 1)
        _RIV = (B - n * (RIVER_W / 2 + 4), B + n * (RIVER_W / 2 + 4))
    out = []
    for E in _RIV:
        i = np.argmin(abs(E[:, 1] - y)); out.append(float(E[i, 0]))
    return out


HOUSES = [(76, 50, 32), (66, 44, 28), (84, 54, 34), (70, 46, 30), (60, 42, 26), (80, 50, 32)]
TREES = [22, 18, 24, 20]
# row pattern: H = house, T = tree
ROWS = [  # (side, gap from road centre, pattern, start x)  H = house, T = tree, - = empty
    (-1, 50, "HTH-HT-HHT-", 40), (1, 50, "HH-THT-HH-T", 70),
    (-1, 175, "--T-H--TH---", 60), (1, 180, "-T--HT--H-T-", 20),
]


def town():
    items = []  # (kind, x, y_mid, path)
    for side, gap, pat, off in ROWS:
        x = 40 + off
        k = 0
        hi = ti = 0
        while x < 1890:
            kind = pat[k % len(pat)]
            if kind == "-":
                x += 70; k += 1
                continue
            if kind == "H":
                w, h, r = HOUSES[(hi + k) % len(HOUSES)]; hi += 1
                half, tall = w / 2, h + r
            else:
                tr = TREES[(ti + k) % len(TREES)]; ti += 1
                half, tall = tr, 2 * tr + 20
                w = 2 * tr
            cx = x + half
            ry = road_y(cx)
            if side < 0:
                base = ry - gap; top = base - tall
            else:
                top = ry + gap; base = top + tall
            ok = top > 70 and base < 1030 and cx - half > 30 and cx + half < 1890
            for yy in (top, base):
                L, R = bank_x(yy)
                if not (cx + half + 26 < L or cx - half - 26 > R):
                    ok = False
            if abs(cx - HERE[0]) < half + 80 and top < HERE[1] + 80 and base > HERE[1] - 80:
                ok = False
            if side < 0 and gap < 100 and 690 < cx < 1350:
                ok = False
            if ok:
                if kind == "H":
                    items.append(("h", cx, (top + base) / 2, house(cx, base, w, h, r)))
                else:
                    items.append(("t", cx, (top + base) / 2, tree(cx, base, tr)))
            x += 2 * half + (34 if kind == "H" else 26)
            k += 1
    return items


CAR = ("M-54 -12 V-34 Q-54 -40 -48 -40 H-30 L-17 -60 H20 L34 -40 H48 Q54 -40 54 -34 V-12 Z "
       "M2 -60 V-40")
CAR_WHEELS = [(-30, -10), (30, -10)]
CAR_X0, CAR_X1, CAR_Y = 640, 1262, ROAD_Y + 14


def d5():
    p = "d5"
    HOLD = ""
    items = town()
    order = sorted(range(len(items)), key=lambda k: dist((items[k][1], items[k][2]), CENTER))
    town_svg = []
    for k, (kind, x, ym, d) in enumerate(items):
        stroke = "var(--ink)" if kind == "h" else "var(--navy)"
        town_svg.append(f'      <path id="{p}-t{k}" class="{p}-town" d="{d}" fill="var(--paper)" stroke="{stroke}" stroke-width="4" stroke-linejoin="round" stroke-linecap="round" opacity="0"/>\n')
    town_delay = {k: 0.6 * i / max(1, len(order) - 1) for i, k in enumerate(order)}
    car = (f'      <g transform="translate({CAR_X0} {CAR_Y})"><g id="{p}-car" opacity="0">'
           f'<path d="{CAR}" fill="var(--paper)" stroke="var(--ink)" stroke-width="4" stroke-linejoin="round"/>'
           + "".join(f'<circle cx="{cx}" cy="{cy}" r="10" fill="var(--paper)" stroke="var(--ink)" stroke-width="4"/>' for cx, cy in CAR_WHEELS)
           + '</g></g>\n')
    html = head("d5_everyday") + f'''  <style>
    #root {{ position: absolute; inset: 0; background: var(--paper); overflow: hidden; }}
    #{p}-svg {{ position: absolute; inset: 0; width: 1920px; height: 1080px; }}
{label_css(p)}
  </style>
  <div id="root" data-composition-id="d5_everyday" data-width="1920" data-height="1080">
    <svg id="{p}-svg" viewBox="0 0 1920 1080" aria-hidden="true" data-layout-allow-overflow{HOLD}>
{grid(p).replace("{MASKOFF}", "0")}{network(p, True)}
      <!-- 実線の道（縁取り）とオレンジの細い縁（road_glow） -->
      <path id="{p}-glow" d="{ROAD}" fill="none" stroke="var(--orange)" stroke-width="{BR_H + 12}" opacity="0"/>
      <g id="{p}-street" opacity="0">
        <path d="{ROAD}" fill="none" stroke="var(--ink)" stroke-width="{BR_H}"/>
        <path d="{ROAD}" fill="none" stroke="var(--paper)" stroke-width="{BR_H - 8}"/>
      </g>
      <!-- d4 の設計線（はじめは d4 の最後のコマと同じ） -->
      <path id="{p}-road" d="{ROAD}" fill="none" stroke="var(--navy)" stroke-width="6" stroke-linecap="round" stroke-dasharray="0 16" mask="url(#{p}-roadmask)"/>
{"".join(town_svg)}{points(p, True, s_scale=1.3)}{bridge(p, 1, 1)}{same_point(p, True)}
      <circle id="{p}-here" cx="{HERE[0]}" cy="{HERE[1]}" r="{RING_R + 4}" fill="none" stroke="var(--navy)" stroke-width="5"
              pathLength="100" stroke-dasharray="100 120" stroke-dashoffset="100" transform="rotate(-90 {HERE[0]} {HERE[1]})"/>
{car}    </svg>
    <div id="{p}-river" class="{p}-label">川</div>
    <div id="{p}-same" class="{p}-label">同じ基準点</div>
  </div>
  <script>
    (function () {{
      const v = window.__hyperframes.getVariables();
      const c = JSON.parse(v.cues);
      const dur = Number(v.dur);
      const tl = gsap.timeline({{ paused: true }});
      const L = c.life_in, G = c.road_glow;
      const HS = 1.25;   // 道路わきの基準点の大きさ（d4 の 1.25 倍）

      // life_in：図解の記号（網・オレンジの線・ラベル）が退き、道路と橋が暮らしの線画になる
      // 残すのは道路わきの基準点1つ（少し大きくする）
      const fade = ["#{p}-links", "#{p}-tie", "#{p}-ring", "#{p}-same", {", ".join(f'"#{p}-p{k}"' for k in range(1, len(POINTS)) if k != HERE_I)}];
      tl.fromTo(fade, {{ opacity: 1 }}, {{ opacity: 0, duration: 0.3, ease: "power2.in" }}, L);
      tl.fromTo("#{p}-p0", {{ scale: 1.2, opacity: 1, transformOrigin: "50% 64%" }}, {{ scale: 1.2, opacity: 0, transformOrigin: "50% 64%", duration: 0.3, ease: "power2.in" }}, L);
      tl.fromTo("#{p}-p{HERE_I}", {{ scale: 1, transformOrigin: "50% 64%" }}, {{ scale: HS, transformOrigin: "50% 64%", duration: 0.45, ease: "power2.inOut" }}, L + 0.1);
      tl.fromTo("#{p}-seam", {{ opacity: 1 }}, {{ opacity: 0, duration: 0.3, ease: "power2.in" }}, L);
      tl.fromTo("#{p}-road", {{ opacity: 1 }}, {{ opacity: 0, duration: 0.35, ease: "power1.inOut" }}, L + 0.08);
      tl.fromTo("#{p}-street", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.35, ease: "power1.inOut" }}, L + 0.08);
      const townDelay = {json.dumps([round(town_delay[k], 3) for k in range(len(items))])};
      townDelay.forEach((d, k) => {{
        tl.fromTo("#{p}-t" + k, {{ opacity: 0, y: 16 }}, {{ opacity: 1, y: 0, duration: 0.4, ease: "power3.out" }}, L + 0.15 + d);
      }});
      tl.fromTo("#{p}-car", {{ opacity: 0, y: 16 }}, {{ opacity: 1, y: 0, duration: 0.4, ease: "power3.out" }}, L + 0.3);

      // road_glow：道路がゆっくり一度だけ明るくなり、車が橋を渡る（このとき動くのは車だけ）
      tl.fromTo("#{p}-glow", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.8, ease: "power2.inOut" }}, G);
      tl.fromTo("#{p}-glow", {{ opacity: 1 }}, {{ opacity: 0, duration: 1.1, ease: "power2.inOut", immediateRender: false }}, G + 1.0);
      tl.fromTo("#{p}-car", {{ x: 0 }}, {{ x: {CAR_X1 - CAR_X0}, duration: 1.8, ease: "power1.inOut" }}, G + 0.4);

      // 最後に：道路わきの基準点が一度だけ強調される（N8「ここから」の発話 ≈ road_glow + 2.4 秒）
      const H = Math.min(G + 2.4, dur - 1.2);
      tl.fromTo("#{p}-p{HERE_I}", {{ scale: HS }}, {{ scale: HS * 1.3, transformOrigin: "50% 64%", duration: 0.35, ease: "power2.out", immediateRender: false }}, H);
      tl.fromTo("#{p}-p{HERE_I}", {{ scale: HS * 1.3 }}, {{ scale: HS, transformOrigin: "50% 64%", duration: 0.5, ease: "power2.inOut", immediateRender: false }}, H + 0.35);
      tl.fromTo("#{p}-here", {{ strokeDashoffset: 100 }}, {{ strokeDashoffset: 0, duration: 0.55, ease: "power2.out" }}, H + 0.05);

      window.__timelines["d5_everyday"] = tl;
    }})();
  </script>
</template>
</body>
</html>
'''
    (OUT / "d5_everyday.html").write_text(html)


if __name__ == "__main__":
    d4()
    d5()
    print("ok", RL, RR, RX)
