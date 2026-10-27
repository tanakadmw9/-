// 画面に出る文字（タイトル、ラベル、用語カード、締めの一文、章扉の作業名など）が、いつからいつまで「読める濃さ」で出ているかを測る。
// docs/07 §1「テロップ表示時間」の入力（scripts/40_qc.py が呼ぶ）。timeline.telops だけでは、場面の中に書いた文字を数えられないため（独立レビュー v4.7）。
// HyperFrames 0.8.206（版は固定）の内部関数で、snapshot と同じページを開き、STEP 秒ごとに止めて DOM の文字と見え方を読む。
//   見え方 = 文字の要素から上の不透明度の積 ×（文字の中心の上に重なる、背景色のある要素で覆われていない割合）
//   読める = 見え方 ≥ READABLE。表示時間は、読める状態が続いた最長の区間（同じ場面・同じ文字は1つとして数える）。
//   同じ場面に同じ文字が重なっているとき（白→紺の文字の入れ替えなど）は、見え方を 1 − Π(1 − v) で合わせる（同じ形の文字が重なって見えるため）。
// 使い方：node scripts/44_text_timing.mjs <出力 json> [STEP 秒=0.05]
// 外部には何も送らない（ローカルのサーバとローカルの Chromium だけ）。
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const OUT = process.argv[2] || path.join(ROOT, "dev/text_timing.json");
const STEP = Number(process.argv[3] || 0.05);
const READABLE = 0.6;
const HF = path.join(ROOT, "node_modules/hyperframes/dist");
const imp = (f) => import(pathToFileURL(path.join(HF, f)).href);
const { bundleWithLocalizedFonts } = await imp("bundleWithLocalizedFonts-PFRVWYOO.js");
const { serveStaticProjectHtml } = await imp("chunk-2S263R6D.js");
const { openSettledCompositionPage, seekCompositionTimelineOnly, settleCompositionSeek } = await imp("chunk-CMDVJP4T.js");

const T = JSON.parse(fs.readFileSync(path.join(ROOT, "comp/timeline.json"), "utf8"));
const DUR = T.duration;
const projectDir = path.join(ROOT, "comp");
const html = await bundleWithLocalizedFonts(projectDir);
const server = await serveStaticProjectHtml(projectDir, html, undefined, [], false);
const { browser, page, renderReadyTimedOut } = await openSettledCompositionPage(html, server.url, { renderReadyTimeoutMs: 60000 });
if (renderReadyTimedOut) console.warn("warning: composition did not report ready; timings may be off");

function probe() {
  const W = 1920, H = 1080;
  const vis = (e) => {           // 要素と祖先の不透明度の積（display:none / visibility:hidden は 0）
    let o = 1;
    for (let n = e; n && n.nodeType === 1; n = n.parentElement) {
      const cs = getComputedStyle(n);
      if (cs.display === "none" || cs.visibility === "hidden") return 0;
      o *= parseFloat(cs.opacity);
      if (o < 0.01) return 0;
    }
    return o;
  };
  const bgAlpha = (e) => {
    const m = getComputedStyle(e).backgroundColor.match(/rgba?\(([^)]+)\)/);
    if (!m) return 0;
    const p = m[1].split(/[ ,/]+/).filter(Boolean);
    return p.length >= 4 ? parseFloat(p[3]) : 1;
  };
  const items = new Map();
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  const done = new Set();
  while (walker.nextNode()) {
    const el = walker.currentNode.parentElement;
    if (!el || done.has(el) || el.closest("script,style,template,title")) continue;
    done.add(el);
    const own = Array.from(el.childNodes).filter((n) => n.nodeType === 3).map((n) => n.nodeValue).join("").replace(/\s+/g, "");
    if (!own) continue;
    let o = vis(el);
    if (o < 0.05) continue;
    const r = el.getBoundingClientRect();
    if (r.width < 1 || r.right <= 0 || r.left >= W || r.bottom <= 0 || r.top >= H) continue;
    // 文字の中心の上に重なっている、背景色のある要素（紙・黒・帯など）で覆われる分を引く
    const cx = Math.min(W - 1, Math.max(0, (r.left + r.right) / 2)), cy = Math.min(H - 1, Math.max(0, (r.top + r.bottom) / 2));
    for (const top of document.elementsFromPoint(cx, cy)) {
      if (top === el || top.contains(el) || el.contains(top)) break;
      const a = bgAlpha(top);
      if (a > 0) o *= 1 - Math.min(1, a * vis(top));
    }
    const comp = el.closest("[data-composition-id]")?.getAttribute("data-composition-id") || "";
    const text = el.textContent.replace(/\s+/g, "");
    const key = comp + "|" + text;
    const prev = items.get(key);
    const box = [r.left, r.top, r.right, r.bottom].map(Math.round);
    if (!prev) items.set(key, [comp, text, o, Math.round(parseFloat(getComputedStyle(el).fontSize)), box]);
    else prev[2] = 1 - (1 - prev[2]) * (1 - o);
  }
  return Array.from(items.values()).map((r) => [r[0], r[1], Math.round(r[2] * 1000) / 1000, r[3], r[4]]);
}

const samples = [];
const n = Math.floor(DUR / STEP + 1e-9);
for (let i = 0; i <= n; i++) {
  const t = Math.round(i * STEP * 1000) / 1000;
  await seekCompositionTimelineOnly(page, t, { exactTime: true });
  await settleCompositionSeek(page, { waitForVideoFrames: false, animationFrameSettle: "race", waitForFontsMs: 0 });
  samples.push([t, await page.evaluate(probe)]);
  if (i % 200 === 0) process.stderr.write(`  text timing ${t.toFixed(1)}s\n`);
}
await browser.close();
await server.close?.();

// 文字ごとに、読める状態が続いた区間をまとめる
const byKey = new Map();
for (const [t, list] of samples) {
  for (const [comp, text, v, fs_, box] of list) {
    const k = comp + "|" + text;
    if (!byKey.has(k)) byKey.set(k, { comp, text, font_px: fs_, max_vis: 0, box, on: [], track: [] });
    const it = byKey.get(k);
    if (v > it.max_vis) it.box = box;   // 文字の位置（いちばん濃く見えた最初の標本の外接矩形）
    it.max_vis = Math.max(it.max_vis, v);
    if (v >= READABLE) { it.on.push(t); it.track.push([t, box]); }   // 読める間の位置（文字が動く場面もあるので、QC の3コマシートは時刻ごとの枠を使う）
  }
}
const items = [];
for (const it of byKey.values()) {
  const runs = [];
  for (const t of it.on) {
    const last = runs[runs.length - 1];
    if (last && t - last[1] <= STEP * 1.5) last[1] = t; else runs.push([t, t]);
  }
  const rr = runs.map(([a, b]) => [a, Math.round((b + STEP) * 1000) / 1000]);   // 最後の標本から次の標本までは出ていたとみなす
  const best = rr.reduce((m, r) => (r[1] - r[0] > (m ? m[1] - m[0] : -1) ? r : m), null);
  items.push({ comp: it.comp, text: it.text, font_px: it.font_px, max_vis: it.max_vis, box: it.box, track: it.track, runs: rr,
               start: best ? best[0] : null, end: best ? best[1] : null, dur: best ? Math.round((best[1] - best[0]) * 1000) / 1000 : 0 });
}
items.sort((a, b) => (a.start ?? 1e9) - (b.start ?? 1e9));
fs.mkdirSync(path.dirname(OUT), { recursive: true });
fs.writeFileSync(OUT, JSON.stringify({ step: STEP, readable: READABLE, duration: DUR, items }, null, 1));
console.log(`text timing: ${items.length} texts -> ${path.relative(ROOT, OUT)}`);
for (const it of items) console.log(`  ${(it.start ?? -1).toFixed(2).padStart(6)}–${(it.end ?? -1).toFixed(2).padStart(6)} ${it.dur.toFixed(2).padStart(5)}s  ${it.comp.padEnd(13)} ${it.text}`);
