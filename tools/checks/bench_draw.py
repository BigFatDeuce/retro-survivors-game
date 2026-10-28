"""0.60: what drawing small cached bitmaps costs in Chrome, by source and smoothing — the micro-bench behind the
damage-number measurements (CLAUDE.md, 0.60 notes). The menu page is loaded for its fonts and TextCache, then a
full-screen canvas draws N damage-number bitmaps (90 % red 14 px, 10 % orange crits 18 px, 12 % in their pop-in)
REP times a frame, with the run's world transform (zoom 1.6, net scale 1 like the game's texts):
  canvas_high / _low / _medium / _nosmooth   the TextCache canvases, imageSmoothingQuality per pass (switched and restored)
  canvas_high_int                             the same at whole pixels with no transform (the HUD's way)
  img_high                                    decoded <img> copies (what RCache.put swaps in since 0.59)
  *_down                                      drawn at 0.6 of their size: the downscaled case where 'high' builds mipmaps
  atlas_canvas_high / _dirty / atlas_img      all bitmaps in one 1024 x 1024 canvas (dirty = written to every frame) / <img>
  glyphs_img_high                             numbers drawn digit by digit from a stroke strip then a fill strip (<img>)
prints median fps, frame ms and the drawing code's ms per variant, then what a new bitmap costs (create_ms) and how long
50 canvas -> <img> copies take to be ready (img50_ms).
usage: python tools/checks/bench_draw.py     env: N (120), REP (30), CPU (1,4), ONLY (variants, comma list),
       UNCAPPED=1 (no vsync: fps past the screen's refresh), SOFT_GPU=1 (SwiftShader), VW / VH"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
import _root
import os, time
from check import serve, launch, VW, VH

N, REP = int(os.environ.get('N', '120')), int(os.environ.get('REP', '30'))
ONLY = os.environ['ONLY'].split(',') if os.environ.get('ONLY') else None

JS = r"""
(async ({ N, REP, ONLY }) => {
  const W = Game.canvas.width, H = Game.canvas.height, z = 1.6;
  const cv = document.createElement('canvas'); cv.width = W; cv.height = H;
  Object.assign(cv.style, { position: 'fixed', left: 0, top: 0, width: '100vw', height: '100vh', zIndex: 99999 });
  document.body.appendChild(cv);
  const ctx = cv.getContext('2d', { alpha: false });
  const rnd = (a, b) => a + Math.floor(Math.random() * (b - a));
  const items = Array.from({ length: N }, () => { const crit = Math.random() < 0.1;
    return { s: rnd(20, 400) + (crit ? '!' : ''), col: crit ? '#ffb02e' : '#ff4d3d', size: crit ? 18 : 14, x: Math.random() * W / z, y: Math.random() * H / z, k: Math.random() }; });
  for (const it of items) it.c = TextCache.get(it.s, it.col, it.size * z, 'rgba(0,0,0,0.85)', 3 * z);
  const toImg = c => new Promise(res => c.toBlob(b => { const u = URL.createObjectURL(b), im = new Image(); im.src = u; im.decode().then(() => { for (const p of Object.keys(c)) im[p] = c[p]; res(im); }); }));
  for (const it of items) it.im = await toImg(it.c);
  const A = document.createElement('canvas'); A.width = A.height = 1024; const ag = A.getContext('2d'); let ax = 0, ay = 0, rowH = 0;
  for (const it of items) { const c = it.c; if (ax + c.width > 1024) { ax = 0; ay += rowH + 1; rowH = 0; } ag.drawImage(c, ax, ay); it.ax = ax; it.ay = ay; ax += c.width + 1; rowH = Math.max(rowH, c.height); }
  const Aim = await toImg(A);
  const strip = async (col, px, lw) => {
    const g0 = document.createElement('canvas').getContext('2d'), font = hudFont(px); g0.font = font;
    const chars = '0123456789!', pad = Math.ceil(lw) + 2, h = Math.ceil(px * 1.32 + pad * 2), by = Math.round(pad + px * 0.98);
    const ws = [...chars].map(ch => g0.measureText(ch).width), cw = Math.ceil(Math.max(...ws) + pad * 2);
    const mk = (stroke) => { const c = document.createElement('canvas'); c.width = cw * chars.length; c.height = h; const g = c.getContext('2d');
      g.font = font; g.lineJoin = 'round'; g.lineWidth = lw; g.strokeStyle = 'rgba(0,0,0,0.85)'; g.fillStyle = col;
      [...chars].forEach((ch, i) => stroke ? g.strokeText(ch, i * cw + pad, by) : g.fillText(ch, i * cw + pad, by)); return toImg(c); };
    return { chars, ws, cw, h, pad, by, s: await mk(true), f: await mk(false) };
  };
  const G = { '#ff4d3d': await strip('#ff4d3d', 14 * z, 3 * z), '#ffb02e': await strip('#ffb02e', 18 * z, 3 * z) };
  const world = () => ctx.setTransform(z, 0, 0, z, 13.37, 7.21);
  const geo = (it, c) => { const sc = (it.k < 0.12 ? 1 + (0.12 - it.k) * 4 : 1) / z, ax = c.tw / 2; return [it.x - (c.bx + ax) * sc, it.y - c.by * sc, c.width * sc, c.height * sc]; };
  const pass = (q, src, down = 1) => () => { ctx.imageSmoothingQuality = q; world();
    for (const it of items) { const c = src(it), g = geo(it, it.c); ctx.drawImage(c, g[0], g[1], g[2] * down, g[3] * down); } ctx.imageSmoothingQuality = 'high'; };
  const atlas = (src, dirty) => () => { if (dirty) { ag.fillStyle = '#' + rnd(0, 4096).toString(16).padStart(3, '0'); ag.fillRect(1020, 1020, 2, 2); }
    ctx.imageSmoothingQuality = 'high'; world(); for (const it of items) { const c = it.c, g = geo(it, c); ctx.drawImage(src, it.ax, it.ay, c.width, c.height, g[0], g[1], g[2], g[3]); } };
  const M = {
    none: () => { },
    canvas_high: pass('high', it => it.c), canvas_low: pass('low', it => it.c), canvas_medium: pass('medium', it => it.c),
    canvas_nosmooth: () => { ctx.imageSmoothingEnabled = false; pass('high', it => it.c)(); ctx.imageSmoothingEnabled = true; },
    canvas_high_int: () => { ctx.setTransform(1, 0, 0, 1, 0, 0); for (const it of items) ctx.drawImage(it.c, Math.round(it.x * z), Math.round(it.y * z)); },
    img_high: pass('high', it => it.im),
    canvas_high_down: pass('high', it => it.c, 0.6), canvas_low_down: pass('low', it => it.c, 0.6), img_high_down: pass('high', it => it.im, 0.6),
    atlas_canvas_high: atlas(A), atlas_canvas_dirty: atlas(A, true), atlas_img: atlas(Aim),
    glyphs_img_high: () => { ctx.imageSmoothingQuality = 'high'; world();
      for (const it of items) { const S = G[it.col], sc = (it.k < 0.12 ? 1 + (0.12 - it.k) * 4 : 1) / z; let tw = 0; for (const ch of it.s) tw += S.ws[S.chars.indexOf(ch)];
        for (const L of [S.s, S.f]) { let x = it.x - tw / 2 * sc; for (const ch of it.s) { const i = S.chars.indexOf(ch); ctx.drawImage(L, i * S.cw, 0, S.cw, S.h, x - S.pad * sc, it.y - S.by * sc, S.cw * sc, S.h * sc); x += S.ws[i] * sc; } } } },
  };
  const run = (name, ms) => new Promise(res => {
    const t = [], js = []; let last = performance.now(); const t0 = last;
    const f = (now) => { t.push(now - last); last = now; const a = performance.now();
      ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.fillStyle = '#304030'; ctx.fillRect(0, 0, W, H); for (let r = 0; r < REP; r++) M[name](); ctx.setTransform(1, 0, 0, 1, 0, 0);
      js.push(performance.now() - a); if (now - t0 < ms) requestAnimationFrame(f); else res({ t, js }); };
    requestAnimationFrame(f); });
  const med = a => { a = a.slice(1).sort((x, y) => x - y); return a[a.length >> 1]; };
  const out = {};
  for (const name of ONLY || Object.keys(M)) { await run(name, 300); const { t, js } = await run(name, 2500); out[name] = { fps: +(1000 / med(t)).toFixed(1), ms: +med(t).toFixed(2), js: +med(js).toFixed(2) }; }
  let a = performance.now(); for (let i = 0; i < 200; i++) TextCache.get(String(Math.random()).slice(2, 8), '#ff4d3d', 14 * z, 'rgba(0,0,0,0.85)', 3 * z); out.create_ms = +((performance.now() - a) / 200).toFixed(3);
  a = performance.now(); await Promise.all(Array.from({ length: 50 }, () => toImg(TextCache.get(String(Math.random()).slice(2, 8), '#ff4d3d', 14 * z, 'rgba(0,0,0,0.85)', 3 * z)))); out.img50_ms = +(performance.now() - a).toFixed(1);
  cv.remove(); return out;
})
"""


def main():
    from playwright.sync_api import sync_playwright
    httpd = serve(); base = f'http://127.0.0.1:{httpd.server_address[1]}'
    try:
        with sync_playwright() as p:
            b = launch(p); ctx = b.new_context(viewport={'width': VW, 'height': VH}); pg = ctx.new_page()
            pg.goto(f'{base}/index.html?fresh=1')
            pg.wait_for_function("typeof Game !== 'undefined' && Game.state === 'menu' && document.querySelector('.menu-buttons')", timeout=120000)
            time.sleep(2); cdp = ctx.new_cdp_session(pg)
            for cpu in [int(c) for c in os.environ.get('CPU', '1,4').split(',')]:
                cdp.send('Emulation.setCPUThrottlingRate', {'rate': cpu})
                r = pg.evaluate(JS, {'N': N, 'REP': REP, 'ONLY': ONLY})
                print(f'CPU x{cpu}: {N} bitmaps x {REP} a frame ({N * REP} draws)', flush=True)
                for k, v in r.items():
                    print(f'  {k:20s} ' + (f"{v['fps']:7.1f} fps  {v['ms']:6.2f} ms a frame  drawing code {v['js']:6.2f} ms" if isinstance(v, dict) else str(v)), flush=True)
            b.close()
    finally: httpd.shutdown()


if __name__ == '__main__':
    main()
