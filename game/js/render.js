'use strict';
// ---------------------------------------------------------------- rendering of a run
const ARROW_BIG = 'UI_IndicatorArrow', ARROW_BIG_BASE = Math.PI / 2, ARROW_SMALL = 'FlagDirectionBig', ARROW_SMALL_BASE = 0;
const GEM_COLORS = [[5, '#6fc3ff', '#d8f0ff'], [15, '#5ee07a', '#d8ffe0'], [50, '#ff5a5a', '#ffd8d8'], [1e9, '#ffd24a', '#fff6c8']];
// 0.59: poison / bleed in full (live gas swirl, bubbles) only on the STATUS_FULL monsters nearest to the character;
// the others get the pre-rendered swirl (GAS_FR frames a turn, GAS_PX px per gas radius) and their drop
const STATUS_FULL = 20, GAS_FR = 32, GAS_PX = 40, _statusQ = [];
// 0.95 (the big dark rings under the monsters, the bosses' above all): a monster's ground shadow. It was
// m.r x 1.15 x m.scale — m.r (the hit radius) already holds the drawing scale, so the size was counted twice (a boss's
// shadow ~3x its sprite). Now 80 % of the sprite's half-width (its first walk / standing frame), never under its body
// (0.95 x m.r) nor over m.r x 1.3, a little lighter; worked out once per monster. It is only decoration: the contact
// reach (m.r + 12, game.js) and the danger telegraphs are drawn by their own code
const MOB_SHADOW_A = 0.18;
const PIC_K = 4, STREAK_L = 16;   // (0.95: RCache.tri / streak / ring: px a world unit, a streak's length)
function mobShadowR(m) {
  if (m._shR) return m._shR;
  const sh = m.sh, an = sh && sh.anims && (sh.anims.walkR || sh.anims.staticR), f = an && an.f && an.f[0];
  const half = f ? f[2] / (sh.zoom || 1) * (m.scale || 1) / 2 : m.r;
  return (m._shR = Math.max(m.r * 0.95, Math.min(half * 0.8, m.r * 1.3)));
}
// pre-rendered sprites for things drawn many times per frame (phones: no per-frame gradients, filters or shadow blur)
const RCache = {
  m: new Map(),
  // 0.59: a cached picture is drawn from a decoded <img> copy of its canvas as soon as that copy is ready. With
  // imageSmoothingQuality 'high' (UHD) Chrome drew small canvases (and ImageBitmaps made from them) ~15 times slower than
  // images: 200 poisoned monsters (1 300 such draws a frame) = 20 fps on an RX 9070 XT, 160 with images
  // 0.93 (stress tests: a 240 ms frozen frame in a big fight, Chrome's toBlob callbacks): one copy at a time — dozens of
  // new pictures in one frame (statuses, areas, numbers) had their PNG encodings all forced into the same task
  _q: [], _busy: false,
  put(key, c) {
    this.m.set(key, c);
    if (c && c.toBlob && c.width && c.height) { this._q.push([key, c]); this._pump(); }
    return c;
  },
  _pump() {
    if (this._busy || !this._q.length) return;
    const [key, c] = this._q.shift(); if (this.m.get(key) !== c) return this._pump();
    this._busy = true; const next = () => { this._busy = false; setTimeout(() => this._pump(), 0); };
    c.toBlob(b => {
      if (!b || this.m.get(key) !== c) return next();
      const u = URL.createObjectURL(b), im = new Image(); im.src = u;
      im.decode().then(() => { URL.revokeObjectURL(u); if (this.m.get(key) === c) { for (const p of Object.keys(c)) try { im[p] = c[p]; } catch (e) { } this.m.set(key, im); } next(); }, () => { URL.revokeObjectURL(u); next(); });
    });
  },
  // 0.68: the monsters' arrow (bigger, readable on any ground): a wooden shaft outlined in dark, a steel head, red and
  // white fletching; drawn 48 x 14 world units, pointing right, centred
  arrow() {
    let c = this.m.get('arrow'); if (c) return c;
    const z = 3; c = document.createElement('canvas'); c.width = 48 * z; c.height = 14 * z; const g = c.getContext('2d'); g.scale(z, z); g.lineJoin = 'round'; g.lineCap = 'round';
    g.strokeStyle = '#1e140c'; g.lineWidth = 4.2; g.beginPath(); g.moveTo(5, 7); g.lineTo(38, 7); g.stroke();
    g.strokeStyle = '#c99a5a'; g.lineWidth = 2.2; g.beginPath(); g.moveTo(5, 7); g.lineTo(38, 7); g.stroke();
    g.fillStyle = '#e8eef4'; g.strokeStyle = '#1e140c'; g.lineWidth = 1.4; g.beginPath(); g.moveTo(47, 7); g.lineTo(36, 2); g.lineTo(38.5, 7); g.lineTo(36, 12); g.closePath(); g.fill(); g.stroke();
    for (const [dy, col] of [[-1, '#d8333a'], [1, '#f4efe4']]) { g.fillStyle = col; g.beginPath(); g.moveTo(3, 7); g.lineTo(0.5, 7 + dy * 5.5); g.lineTo(11, 7 + dy * 5); g.lineTo(13, 7); g.closePath(); g.fill(); g.stroke(); }
    return this.put('arrow', c);
  },
  glow(col) {
    let c = this.m.get('g' + col); if (c) return c;
    c = document.createElement('canvas'); c.width = c.height = 64; const g = c.getContext('2d');
    const gr = g.createRadialGradient(32, 32, 1, 32, 32, 32); gr.addColorStop(0, col); gr.addColorStop(1, 'rgba(0,0,0,0)'); g.fillStyle = gr; g.fillRect(0, 0, 64, 64);
    return this.put('g' + col, c);
  },
  gem(gi, s) {
    const k = 'm' + gi + '_' + s; let c = this.m.get(k); if (c) return c;
    const [, c1, c2] = GEM_COLORS[gi], z = 2, w = Math.ceil(s * 2 + 4), h = Math.ceil(s * 2.8 + 4);
    c = document.createElement('canvas'); c.width = w * z; c.height = h * z; const g = c.getContext('2d'); g.scale(z, z);
    const x = w / 2, y = s * 1.6 + 2;
    const path = () => { g.beginPath(); g.moveTo(x, y - s * 1.6); g.lineTo(x + s, y); g.lineTo(x, y + s * 1.2); g.lineTo(x - s, y); g.closePath(); };
    g.strokeStyle = 'rgba(255,255,255,0.75)'; g.lineWidth = 1.6; g.lineJoin = 'round'; path(); g.stroke();
    g.fillStyle = c1; path(); g.fill();
    g.fillStyle = c2; g.beginPath(); g.moveTo(x, y - s * 1.6); g.lineTo(x + s * 0.45, y); g.lineTo(x, y - s * 0.2); g.closePath(); g.fill();
    c.ox = x; c.oy = y; c.w = w; c.h = h; return this.put(k, c);
  },
  // v1.7 experience pickups: Ambre (small), Ambre Ancestrale (bigger), Ambre du Chêne Mou (rare, biggest),
  // the item pictures pre-scaled once to the size they are drawn at (hundreds of them on screen)
  // (0.92: the ancestral amber looked pixelated: drawn at least at 2x the screen's size, rounded up, then scaled down)
  amber(gi, s) {
    const z = Math.max(2, Math.min(4, Math.ceil((Game.zoom || 1) * 2) / 2 + 0.5)), k = 'a' + gi + '_' + s + '_' + z; let c = this.m.get(k); if (c) return c;
    const name = ((Game.C && Game.C.ambers) || [])[gi], IC = Game.icons, f = name && IC.get(name), im = name && IC.src(name);
    if (!f || !im) return null;
    const sc = s / Math.max(f[2], f[3]), w = f[2] * sc, h = f[3] * sc;
    c = document.createElement('canvas'); c.width = Math.max(2, Math.ceil(w * z)); c.height = Math.max(2, Math.ceil(h * z));
    const g = c.getContext('2d'); g.imageSmoothingEnabled = true; g.imageSmoothingQuality = 'high';
    g.drawImage(im, f[0], f[1], f[2], f[3], 0, 0, c.width, c.height);
    c.w = w; c.h = h; return this.put(k, c);
  },
  // v2.0 spell areas on the ground, drawn like the zones of the client: a tinted ellipse with its cells and a rim
  // outlined in dark so it reads on any ground. Pre-rendered per colour and radius (bucketed), drawn scaled
  // soft (0.98: every area that stays on the ground — spell zones, traps, the monsters' puddles): no outline, the fill
  // and the grid fading into the ground at the edge, a soft glow just inside it; the hard picture stays for the short
  // impacts and rings
  area(col, r, soft) {
    const z = Math.max(1, Math.min(3, Math.round((Game.zoom || 1) * 2) / 2)), rb = Math.max(12, Math.round(r / 6) * 6), k = 'z' + col + '_' + rb + '_' + z + (soft ? 's' : '');
    const A = soft ? AREA_SOFT : AREA_HARD;
    let c = this.m.get(k); if (c) return c;
    const w = rb * 2 + 10, h = rb * 1.24 + 10; c = document.createElement('canvas'); c.width = Math.ceil(w * z); c.height = Math.ceil(h * z);
    const g = c.getContext('2d'); g.scale(z, z); const cx = w / 2, cy = h / 2, ry = rb * 0.62;
    const ell = (rr) => { g.beginPath(); g.ellipse(cx, cy, rr, rr * 0.62, 0, 0, TAU); };
    const gr = g.createRadialGradient(cx, cy, rb * 0.15, cx, cy, rb); for (const [o, v] of A.fill) gr.addColorStop(o, col + v);
    g.save(); g.translate(cx, cy); g.scale(1, 0.62); g.translate(-cx, -cy); g.fillStyle = gr; g.beginPath(); g.arc(cx, cy, rb, 0, TAU); g.fill(); g.restore();
    // the cells (diamonds of the Dofus grid) inside the zone (0.98, soft: on their own layer, fading out towards the edge)
    const L = A.feather ? document.createElement('canvas') : null, gc = L ? L.getContext('2d') : g; if (L) { L.width = c.width; L.height = c.height; gc.scale(z, z); }
    gc.save(); gc.beginPath(); gc.ellipse(cx, cy, rb - 1, (rb - 1) * 0.62, 0, 0, TAU); gc.clip(); gc.strokeStyle = col + A.cells; gc.lineWidth = 1;
    const cw = 53 * ES * 0.25, chh = 27 * ES * 0.25;
    for (let i = -Math.ceil(rb / cw) - 1; i <= Math.ceil(rb / cw) + 1; i++) {
      gc.beginPath(); gc.moveTo(cx + i * cw * 2 - rb * 2, cy - rb * 2 * chh / cw); gc.lineTo(cx + i * cw * 2 + rb * 2, cy + rb * 2 * chh / cw); gc.stroke();
      gc.beginPath(); gc.moveTo(cx + i * cw * 2 - rb * 2, cy + rb * 2 * chh / cw); gc.lineTo(cx + i * cw * 2 + rb * 2, cy - rb * 2 * chh / cw); gc.stroke();
    }
    gc.restore();
    if (L) { const fm = gc.createRadialGradient(cx, cy, rb * 0.2, cx, cy, rb * 0.95); fm.addColorStop(0, '#000'); fm.addColorStop(1, 'rgba(0,0,0,0)'); gc.globalCompositeOperation = 'destination-in'; gc.translate(cx, cy); gc.scale(1, 0.62); gc.translate(-cx, -cy); gc.fillStyle = fm; gc.fillRect(-w, -h * 2, w * 3, h * 4); g.save(); g.setTransform(1, 0, 0, 1, 0, 0); g.drawImage(L, 0, 0); g.restore(); }
    { g.save(); ell(rb - 1); g.clip(); const eg = g.createRadialGradient(cx, cy, rb * 0.55, cx, cy, rb); for (const [o, v] of A.edge) eg.addColorStop(o, col + v);   // (0.87: a glow along the edge, deeper areas)
      g.translate(cx, cy); g.scale(1, 0.62); g.translate(-cx, -cy); g.fillStyle = eg; g.beginPath(); g.arc(cx, cy, rb, 0, TAU); g.fill(); g.restore(); }
    if (A.dark) { ell(rb - 1.5); g.lineWidth = A.dark[0]; g.strokeStyle = 'rgba(0,0,0,' + A.dark[1] + ')'; g.stroke(); }
    if (A.rim) { ell(rb - 1.5); g.lineWidth = A.rim[0]; g.strokeStyle = col + A.rim[1]; g.stroke(); }
    if (A.light) { ell(rb - 5.5); g.lineWidth = 1; g.strokeStyle = 'rgba(255,255,255,' + A.light + ')'; g.stroke(); }   // (0.87: a thin light inner rim)
    c.rb = rb; c.w = w; c.h = h; this.put(k, c); if (this.m.size > 600) this.m.delete(this.m.keys().next().value); return c;
  },
  // 0.87: a ring of runes for the areas on the ground (zoneRunes turns it, flattened): a fine circle, then marks around the
  // rim — ticks, small diamonds and dots in turn, the colour of the area with a dark edge so it reads on any ground
  runes(col, r, kind) {
    if (kind === 'knife') return this.knifeRunes(col, r);
    const z = Math.max(1, Math.min(3, Math.round((Game.zoom || 1) * 2) / 2)), rb = Math.max(18, Math.round(r / 8) * 8), k = 'rn' + col + '_' + rb + '_' + z;
    let c = this.m.get(k); if (c) return c;
    const w = rb * 2 + 8; c = document.createElement('canvas'); c.width = c.height = Math.ceil(w * z);
    const g = c.getContext('2d'); g.scale(z, z); g.translate(w / 2, w / 2); g.lineCap = 'round'; g.lineJoin = 'round';
    const n = Math.max(12, Math.min(36, Math.round(rb / 6))), R0 = rb * 0.86, R1 = rb * 0.94;
    const pass = (lw, st) => {
      g.lineWidth = lw; g.strokeStyle = st; g.beginPath(); g.arc(0, 0, rb * 0.8, 0, TAU); g.stroke();
      for (let i = 0; i < n; i++) {
        const a = i / n * TAU, ca = Math.cos(a), sa = Math.sin(a), m = i % 3;
        g.beginPath();
        if (m === 0) { g.moveTo(ca * R0, sa * R0); g.lineTo(ca * R1, sa * R1); }
        else if (m === 1) { const rm = (R0 + R1) / 2, d = (R1 - R0) * 0.55, px = -sa * d, py = ca * d; g.moveTo(ca * (rm - d), sa * (rm - d)); g.lineTo(ca * rm + px, sa * rm + py); g.lineTo(ca * (rm + d), sa * (rm + d)); g.lineTo(ca * rm - px, sa * rm - py); g.closePath(); }
        else { const rm = (R0 + R1) / 2; g.arc(ca * rm, sa * rm, (R1 - R0) * 0.18, 0, TAU); }
        g.stroke();
      }
    };
    pass(Math.max(4, rb * 0.034), 'rgba(0,0,0,0.42)'); pass(Math.max(2.2, rb * 0.019), col); pass(Math.max(0.8, rb * 0.006), 'rgba(255,255,255,0.55)');   // (dark edge, colour, a light core)
    c.rb = rb; c.w = w; this.put(k, c); if (this.m.size > 600) this.m.delete(this.m.keys().next().value); return c;
  },
  // 0.92 (the Sram's traps with runes of their own): the ring of runes made of little daggers, points out, a dot
  // between two of them (same dark edge / colour / light core passes as the other runes)
  knifeRunes(col, r) {
    const z = Math.max(1, Math.min(3, Math.round((Game.zoom || 1) * 2) / 2)), rb = Math.max(18, Math.round(r / 8) * 8), k = 'rk' + col + '_' + rb + '_' + z;
    let c = this.m.get(k); if (c) return c;
    const w = rb * 2 + 8; c = document.createElement('canvas'); c.width = c.height = Math.ceil(w * z);
    const g = c.getContext('2d'); g.scale(z, z); g.translate(w / 2, w / 2); g.lineCap = 'round'; g.lineJoin = 'round';
    const n = Math.max(6, Math.min(16, Math.round(rb / 11))), rm = rb * 0.84, L = Math.max(11, rb * 0.22);
    const pass = (lw, st, fill) => {
      g.lineWidth = lw; g.strokeStyle = st; g.beginPath(); g.arc(0, 0, rb * 0.76, 0, TAU); g.stroke();
      for (let i = 0; i < n; i++) {
        const a = i / n * TAU; g.save(); g.rotate(a); g.translate(rm, 0);   // (x: outward)
        const gw = L * 0.2, bw = L * 0.1;
        g.beginPath(); g.moveTo(-L * 0.5, 0); g.lineTo(-L * 0.18, 0);                       // the handle
        g.moveTo(-L * 0.18, -gw); g.lineTo(-L * 0.18, gw);                                   // the guard
        g.moveTo(-L * 0.12, -bw); g.lineTo(L * 0.5, 0); g.lineTo(-L * 0.12, bw); g.closePath(); // the blade
        if (fill) { g.fillStyle = fill; g.fill(); } g.stroke(); g.restore();
        const b = a + Math.PI / n; g.beginPath(); g.arc(Math.cos(b) * rm, Math.sin(b) * rm, Math.max(1, L * 0.07), 0, TAU); g.stroke();
      }
    };
    pass(Math.max(4, rb * 0.04), 'rgba(0,0,0,0.42)'); pass(Math.max(2, rb * 0.02), col, col); pass(Math.max(0.8, rb * 0.006), 'rgba(255,255,255,0.6)');
    c.rb = rb; c.w = w; this.put(k, c); if (this.m.size > 600) this.m.delete(this.m.keys().next().value); return c;
  },
  // 0.59: the monster states pre-rendered (poison and bleed cost 6 glows, 3 stroked circles and gradient-filled bezier
  // drops per monster per frame: 200 poisoned monsters = 27 fps on a fast GPU). 'poison' = the poison drop (size 6),
  // 'blood' = the three blood drops of a bleeding monster in one picture (sizes 4, 4.6, 4), with their outline and
  // highlight (drawDrop scales them)
  drop(kind) {
    const key = 'drop' + kind; let c = this.m.get(key); if (c) return c;
    const P = kind === 'blood' ? { lw: 1.2, c0: '#ff3a3a', c1: '#7a0008', st: '#2a0004', hl: [0.16, 0.3, 0.7], d: [[-7, 2, 4], [0, -3, 4.6], [7, 2, 4]] }
      : { lw: 1.6, c0: '#9dff6a', c1: '#2f9a2a', st: '#5a1a7a', hl: [0.18, 0.32, 0.75], d: [[0, 0, 6]] };
    const S = 4, x0 = Math.min(...P.d.map(([x, , k]) => x - 1.1 * k)) - P.lw, x1 = Math.max(...P.d.map(([x, , k]) => x + 1.1 * k)) + P.lw;
    const y0 = Math.min(...P.d.map(([, y, k]) => y - 1.5 * k)) - P.lw, y1 = Math.max(...P.d.map(([, y, k]) => y + k)) + P.lw, w = x1 - x0, h = y1 - y0;
    c = document.createElement('canvas'); c.width = Math.ceil(w * S); c.height = Math.ceil(h * S); const g = c.getContext('2d'); g.scale(S, S); g.translate(-x0, -y0);
    for (const [dx, dy, k] of P.d) {
      g.beginPath(); g.moveTo(dx, dy - k * 1.5); g.bezierCurveTo(dx + k * 1.1, dy - k * 0.2, dx + k, dy + k, dx, dy + k); g.bezierCurveTo(dx - k, dy + k, dx - k * 1.1, dy - k * 0.2, dx, dy - k * 1.5); g.closePath();
      const gr = g.createLinearGradient(dx, dy - k, dx, dy + k); gr.addColorStop(0, P.c0); gr.addColorStop(1, P.c1); g.fillStyle = gr; g.fill(); g.lineWidth = P.lw; g.strokeStyle = P.st; g.stroke();
      g.fillStyle = `rgba(255,255,255,${P.hl[2]})`; g.beginPath(); g.ellipse(dx - k * 0.35, dy, k * P.hl[0], k * P.hl[1], 0.3, 0, TAU); g.fill();
    }
    c.x0 = x0; c.y0 = y0; c.w = w; c.h = h; return this.put(key, c);
  },
  // 0.61: a violet aura orb (the Sagesse fusion's orbiters): a bright core fading into deep violet, a soft edge, two
  // lighter swirls inside (drawn turning)
  orb() {
    let c = this.m.get('orb'); if (c) return c;
    const n = 96, h = n / 2; c = document.createElement('canvas'); c.width = c.height = n; const g = c.getContext('2d');
    const gr = g.createRadialGradient(h - 10, h - 12, 2, h, h, h - 2);
    gr.addColorStop(0, '#ffffff'); gr.addColorStop(0.16, '#f3e2ff'); gr.addColorStop(0.42, '#bb82ff'); gr.addColorStop(0.78, '#6c26cc'); gr.addColorStop(1, 'rgba(60,10,120,0)');
    g.fillStyle = gr; g.beginPath(); g.arc(h, h, h - 2, 0, TAU); g.fill();
    g.globalCompositeOperation = 'lighter'; g.lineCap = 'round';
    g.strokeStyle = 'rgba(225,190,255,0.45)'; g.lineWidth = 4.5; g.beginPath(); g.arc(h, h, h * 0.56, -0.7, 1.5); g.stroke();
    g.strokeStyle = 'rgba(240,215,255,0.4)'; g.lineWidth = 3; g.beginPath(); g.arc(h, h, h * 0.34, 2.3, 4.3); g.stroke();
    return this.put('orb', c);
  },
  // 0.95 (perf sweep: a marked crowd, a life drain = one 2D box per monster sent to the GPU every frame with PixiJS): the
  // little paths drawn many times a frame as pictures, so PixiJS lays them as quads like the rest. PIC_K px a world unit
  // the marked monster's red triangle (12 x 10 world units, its tip at (6, 10))
  tri() {
    let c = this.m.get('tri'); if (c) return c;
    const k = PIC_K; c = document.createElement('canvas'); c.width = 15 * k; c.height = 13 * k; const g = c.getContext('2d'); g.scale(k, k);
    g.fillStyle = '#ff3b3b'; g.strokeStyle = '#3a0000'; g.lineWidth = 1.5; g.beginPath(); g.moveTo(7.5, 11.5); g.lineTo(1.5, 1.5); g.lineTo(13.5, 1.5); g.closePath(); g.fill(); g.stroke();
    return this.put('tri', c);
  },
  // a straight streak with round ends, STREAK_L world units between their centres (drawn stretched to its length): a
  // core of width w and colour col over a rim of width rw and colour rc (rw 0: no rim)
  streak(col, w, rc, rw) {
    const key = 'sk' + col + w + rc + rw; let c = this.m.get(key); if (c) return c;
    const k = PIC_K, p = Math.max(w, rw) / 2 + 0.5; c = document.createElement('canvas'); c.width = Math.ceil((STREAK_L + 2 * p) * k); c.height = Math.ceil(2 * p * k); c.p = p;
    const g = c.getContext('2d'); g.scale(k, k); g.lineCap = 'round';
    for (const [s, lw] of rw ? [[rc, rw], [col, w]] : [[col, w]]) { g.strokeStyle = s; g.lineWidth = lw; g.beginPath(); g.moveTo(p, p); g.lineTo(p + STREAK_L, p); g.stroke(); }
    return this.put(key, c);
  },
  // an ellipse's outline (rx x ry world units, line lw): sizes by steps of 2 units
  // 0.98: a spark (the areas' and frames' particles): a bright head, a tail of its colour fading down; drawn added
  spark(col) {
    const key = 'spk' + col; let c = this.m.get(key); if (c) return c;
    c = document.createElement('canvas'); c.width = 16; c.height = 48; const g = c.getContext('2d');
    const tl = g.createLinearGradient(0, 6, 0, 46); tl.addColorStop(0, col); tl.addColorStop(1, 'rgba(0,0,0,0)');
    g.fillStyle = tl; g.beginPath(); g.moveTo(8, 3); g.quadraticCurveTo(14, 12, 8, 46); g.quadraticCurveTo(2, 12, 8, 3); g.fill();
    const hd = g.createRadialGradient(8, 9, 0, 8, 9, 7); hd.addColorStop(0, 'rgba(255,255,235,1)'); hd.addColorStop(0.45, col); hd.addColorStop(1, 'rgba(0,0,0,0)'); g.fillStyle = hd; g.fillRect(0, 0, 16, 18);
    return this.put(key, c);
  },
  ring(col, rx, ry, lw) {
    rx = Math.max(2, Math.round(rx / 2) * 2); ry = Math.max(1, Math.round(ry / 2) * 2);
    const key = 'rg' + col + rx + ',' + ry + ',' + lw; let c = this.m.get(key); if (c) return c;
    const k = PIC_K, p = lw / 2 + 1; c = document.createElement('canvas'); c.width = Math.ceil((rx + p) * 2 * k); c.height = Math.ceil((ry + p) * 2 * k); c.p = p;
    const g = c.getContext('2d'); g.scale(k, k); g.strokeStyle = col; g.lineWidth = lw; g.beginPath(); g.ellipse(rx + p, ry + p, rx, ry, 0, 0, TAU); g.stroke();
    this.put(key, c); if (this.m.size > 600) this.m.delete(this.m.keys().next().value); return c;
  },
  // 0.95: a woven web (drawWeb once its rings are done: grown, still), r world units, in its own unsquashed space (drawn
  // squashed and swaying by drawWeb): its pale disc and its threads, as drawWeb lays them, at 3 px a world unit
  web(r) {
    r = Math.max(8, Math.round(r)); const key = 'web' + r; let c = this.m.get(key); if (c) return c;
    const k = 3, R = r + 4, n = 9; c = document.createElement('canvas'); c.width = c.height = Math.ceil(R * 2 * k); c.R = R;
    const g = c.getContext('2d'); g.scale(k, k); g.translate(R, R);
    g.globalAlpha = 0.18; g.fillStyle = '#d8d8ec'; g.beginPath(); g.arc(0, 0, r, 0, TAU); g.fill();
    const path = () => { g.beginPath();
      for (let i = 0; i < n; i++) { const an = i / n * TAU; g.moveTo(0, 0); g.lineTo(Math.cos(an) * r, Math.sin(an) * r); }
      for (let ring = 1; ring <= 4; ring++) { const rr = r * ring / 4.3; for (let i = 0; i <= n; i++) { const an = i / n * TAU, sag = rr * (i % 2 ? 0.92 : 1), x = Math.cos(an) * sag, y = Math.sin(an) * sag; if (i === 0) g.moveTo(x, y); else g.lineTo(x, y); } } };
    g.globalAlpha = 0.85; g.strokeStyle = 'rgba(30,30,40,0.22)'; g.lineWidth = 3.4; path(); g.stroke();   // (0.98: its dark under-line faint)
    g.strokeStyle = 'rgba(245,245,255,0.95)'; g.lineWidth = 1.6; path(); g.stroke();
    this.put(key, c); if (this.m.size > 600) this.m.delete(this.m.keys().next().value); return c;
  },
  // 0.95: a weapon's thrown crescent (weapons.js drawCrescent), r world units, its colour col: the shape, its gradient and
  // its glow (the shadow blur at the usual zoom) at 3 px a world unit; ox / oy / ow / oh = where it lies around its centre
  crescent(col, r) {
    r = Math.max(2, Math.round(r)); const key = 'cr' + col + r; let c = this.m.get(key); if (c) return c;
    const k = 3, m = 14, x0 = -r * 1.4 - m, y0 = -r - m, w = r * 2.4 + m * 2, hgt = r * 2 + m * 2;
    c = document.createElement('canvas'); c.width = Math.ceil(w * k); c.height = Math.ceil(hgt * k); c.ox = -x0; c.oy = -y0; c.ow = w; c.oh = hgt;
    const g = c.getContext('2d'); g.scale(k, k); g.translate(-x0, -y0); g.shadowColor = col; g.shadowBlur = 12 * k;
    const gr = g.createLinearGradient(-r, 0, r * 0.4, 0); gr.addColorStop(0, 'rgba(60,0,90,0)'); gr.addColorStop(0.6, col); gr.addColorStop(1, '#ffb0ff');
    g.fillStyle = gr; g.beginPath(); g.arc(0, 0, r, -1.25, 1.25); g.arc(-r * 0.45, 0, r * 0.95, 1.1, -1.1, true); g.closePath(); g.fill();
    this.put(key, c); if (this.m.size > 600) this.m.delete(this.m.keys().next().value); return c;
  },
  // 0.95: a band across a line (beams, the burning line), as their gradient was: edge colour at both sides, mid colour in
  // the middle; drawn stretched (PixiJS lays it as a quad: a gradient made every frame sent them to a 2D layer)
  band(edge, mid) {
    const key = 'bd' + edge + mid; let c = this.m.get(key); if (c) return c;
    c = document.createElement('canvas'); c.width = 4; c.height = 64; const g = c.getContext('2d'), gr = g.createLinearGradient(0, 0, 0, 64);
    gr.addColorStop(0, edge); gr.addColorStop(0.5, mid); gr.addColorStop(1, edge); g.fillStyle = gr; g.fillRect(0, 0, 4, 64);
    this.put(key, c); if (this.m.size > 600) this.m.delete(this.m.keys().next().value); return c;
  },
  // 0.95: a melee blow's strip on the ground (drawWeaponSwath), w half its width, L its reach, rgb its colour: its
  // gradient fill, its white flash and its outlines as three pictures (3 px a world unit, p units of margin)
  swath(rgb, w, L) {
    w = Math.max(2, Math.round(w)); L = Math.max(w * 2, Math.round(L)); const key = 'sw' + rgb + '|' + w + '|' + L; let S = this.m.get(key); if (S) return S;
    const k = 3, p = 4, mk = (fn) => { const c = document.createElement('canvas'); c.width = Math.ceil((L + 2 * p) * k); c.height = Math.ceil((w + p) * 2 * k); const g = c.getContext('2d'); g.scale(k, k); g.translate(p, w + p); g.lineJoin = 'round'; g.lineCap = 'round'; fn(g); return c; };
    const strip = g => { g.beginPath(); g.moveTo(w * 0.3, -w * 0.55); g.lineTo(L - w, -w); g.arc(L - w, 0, w, -Math.PI / 2, Math.PI / 2); g.lineTo(w * 0.3, w * 0.55); g.closePath(); };
    S = { p, w, L,
      fill: mk(g => { const gr = g.createLinearGradient(0, 0, L, 0); gr.addColorStop(0, `rgba(${rgb},0.04)`); gr.addColorStop(0.5, `rgba(${rgb},0.4)`); gr.addColorStop(1, `rgba(${rgb},0.78)`); g.fillStyle = gr; strip(g); g.fill(); }),
      snap: mk(g => { g.fillStyle = '#fffbe8'; strip(g); g.fill(); }),
      line: mk(g => { strip(g); g.lineWidth = 5; g.strokeStyle = 'rgba(30,14,4,0.45)'; g.stroke(); g.lineWidth = 2.6; g.strokeStyle = `rgba(${rgb},1)`; g.stroke(); g.lineWidth = 1; g.strokeStyle = 'rgba(255,255,255,0.7)'; g.stroke(); }) };
    this.m.set(key, S); if (this.m.size > 600) this.m.delete(this.m.keys().next().value);
    return S;
  },
  // 0.65: the Xelor's 'Horloge' hourglass (light violet, like his Sablier's own clip): gold frame, lilac glass, violet
  // sand — frame fi of HG_FR as the sand runs from the top bulb to the bottom one (fi / HG_FR = time run)
  hourglass(fi) {
    const key = 'hg' + fi; let c = this.m.get(key); if (c) return c;
    const W = 72, H = 104, k = fi / (HG_FR - 1); c = document.createElement('canvas'); c.width = W; c.height = H; const g = c.getContext('2d');
    const cx = W / 2, top = 14, bot = H - 14, mid = H / 2, bw = 24;   // the glass: two bulbs meeting at the neck
    const bulb = (y0, y1) => { g.beginPath(); g.moveTo(cx - bw, y0); g.bezierCurveTo(cx - bw - 2, (y0 + y1) / 2, cx - 4, y1 - 6, cx - 2.5, y1); g.lineTo(cx + 2.5, y1); g.bezierCurveTo(cx + 4, y1 - 6, cx + bw + 2, (y0 + y1) / 2, cx + bw, y0); g.closePath(); };
    const glass = () => { bulb(top + 4, mid); bulb(bot - 4, mid); };
    // glass body
    g.save(); glass(); g.fillStyle = 'rgba(232,214,255,0.28)'; g.fill(); g.restore();
    // sand: what is left in the top bulb (it sinks towards the neck), the heap in the bottom one, the thin stream
    const sand = g.createLinearGradient(0, top, 0, bot); sand.addColorStop(0, '#f6eaff'); sand.addColorStop(0.5, '#cfa6ff'); sand.addColorStop(1, '#a874f0');
    g.save(); bulb(top + 4, mid); g.clip(); g.fillStyle = sand; const ty = top + 4 + (mid - top - 4) * (0.15 + 0.85 * k); g.fillRect(0, ty, W, mid - ty + 1); g.restore();
    g.save(); bulb(bot - 4, mid); g.clip(); g.fillStyle = sand; const hy = bot - 4 - (bot - mid - 6) * (0.08 + 0.8 * k);
      g.beginPath(); g.moveTo(0, bot); g.lineTo(0, hy + 10); g.quadraticCurveTo(cx, hy - 10, W, hy + 10); g.lineTo(W, bot); g.closePath(); g.fill(); g.restore();
    if (k < 0.97) { g.fillStyle = 'rgba(214,180,255,0.95)'; g.fillRect(cx - 1, mid - 1, 2, (bot - 4 - (bot - mid - 6) * (0.08 + 0.8 * k)) - mid + 2); }
    // glass outline and its shine
    g.save(); glass(); g.lineWidth = 2; g.strokeStyle = 'rgba(120,70,190,0.9)'; g.stroke(); g.restore();
    g.strokeStyle = 'rgba(255,255,255,0.75)'; g.lineWidth = 2.2; g.lineCap = 'round';
    g.beginPath(); g.moveTo(cx - bw + 6, top + 9); g.quadraticCurveTo(cx - bw + 3, top + 22, cx - 9, mid - 10); g.stroke();
    g.beginPath(); g.moveTo(cx - bw + 6, bot - 9); g.quadraticCurveTo(cx - bw + 4, bot - 18, cx - 12, mid + 14); g.stroke();
    // the frame: two caps, two posts (gold), a violet gem on each cap
    const gold = g.createLinearGradient(0, 0, 0, H); gold.addColorStop(0, '#fff2b0'); gold.addColorStop(0.5, '#f0b93c'); gold.addColorStop(1, '#a8661a');
    g.fillStyle = gold; g.strokeStyle = '#5a2e08'; g.lineWidth = 2;
    for (const x of [cx - bw - 5, cx + bw + 1]) { g.beginPath(); g.rect(x, top, 4, bot - top); g.fill(); g.stroke(); }
    for (const y of [top - 8, bot]) { g.beginPath(); g.roundRect ? g.roundRect(cx - bw - 10, y, (bw + 10) * 2, 8, 3) : g.rect(cx - bw - 10, y, (bw + 10) * 2, 8); g.fill(); g.stroke(); }
    for (const y of [top - 4, bot + 4]) { const gem = g.createRadialGradient(cx - 1, y - 1, 0, cx, y, 5); gem.addColorStop(0, '#ffffff'); gem.addColorStop(0.4, '#d7b0ff'); gem.addColorStop(1, '#7a3ad8');
      g.fillStyle = gem; g.beginPath(); g.arc(cx, y, 4.2, 0, TAU); g.fill(); g.strokeStyle = '#4a1a8a'; g.lineWidth = 1.2; g.stroke(); }
    return this.put(key, c);
  },
  // a poison bubble (radius 3.2, dark outline)
  bubble(col) {
    const key = 'bub' + col; let c = this.m.get(key); if (c) return c;
    const S = 8, r = 3.2, h = r + 1; c = document.createElement('canvas'); c.width = c.height = Math.ceil(h * 2 * S); const g = c.getContext('2d'); g.scale(S, S);
    g.fillStyle = col; g.strokeStyle = '#2a0a3a'; g.lineWidth = 1; g.beginPath(); g.arc(h, h, r, 0, TAU); g.fill(); g.stroke();
    c.r = r; c.h = h; return this.put(key, c);
  },
  // frame fi of the poison gas's slow swirl (GAS_FR frames a turn): the six green / violet glows composed once (R0 = GAS_PX px)
  gas(fi) {
    const key = 'gas' + fi; let c = this.m.get(key); if (c) return c;
    const S = GAS_PX, n = Math.ceil(2.8 * S), o = n / 2; c = document.createElement('canvas'); c.width = c.height = n; const g = c.getContext('2d');
    g.globalAlpha = 0.6;
    for (let i = 0; i < 6; i++) { const ph = fi / GAS_FR * TAU + i * 1.7, x = o + Math.cos(ph) * S * 0.55, y = o + Math.sin(ph) * S * 0.4, r = S * (0.6 + 0.15 * Math.sin(ph * 2));
      g.drawImage(this.glow(i % 2 ? 'rgba(160,60,225,0.95)' : 'rgba(80,215,55,0.95)'), x - r, y - r, r * 2, r * 2); }
    c.o = o / S; return this.put(key, c);
  },
  // an icon frame recoloured once (grey heart, tinted arrows) instead of ctx.filter every frame
  tinted(name, kind) {
    const k = 't' + name + kind; let c = this.m.get(k); if (c !== undefined) return c;
    const IC = Game.icons, f = IC.get(name); if (!f) { this.m.set(k, null); return null; }
    const im = IC.src(name); if (!im) { this.m.set(k, null); return null; }
    c = document.createElement('canvas'); c.width = f[2]; c.height = f[3]; const g = c.getContext('2d', { willReadFrequently: true });
    g.drawImage(im, f[0], f[1], f[2], f[3], 0, 0, f[2], f[3]);
    try {
      const d = g.getImageData(0, 0, c.width, c.height), a = d.data;
      for (let i = 0; i < a.length; i += 4) {
        const r = a[i], gg = a[i + 1], b = a[i + 2];
        if (kind === 'grey') { const v = (r * 0.3 + gg * 0.59 + b * 0.11) * 0.35; a[i] = a[i + 1] = a[i + 2] = v; }
        else if (kind === 'green') { a[i] = gg * 0.6; a[i + 1] = Math.min(255, r * 0.9 + 40); a[i + 2] = b * 0.7; }
      }
      g.putImageData(d, 0, 0);
    } catch (e) { }
    c.sc = f[6] || 1; return this.put(k, c);
  },
};
const GroundBuf = { c: null, g: null, c2: null, g2: null, w: 0, h: 0, x0: 0, y0: 0, z: 0, n: -1, run: null };
// paints the world rectangle [wx0, wx1] x [wy0, wy1] of the ground into the buffer (whose origin is B.x0, B.y0)
function paintGround(R, B, wx0, wy0, wx1, wy1) {
  const g = B.g, z = B.z, T = R.world.tile, res = R.world.res || 1;
  const px0 = Math.max(0, Math.floor((wx0 - B.x0) * z)), py0 = Math.max(0, Math.floor((wy0 - B.y0) * z)), px1 = Math.min(B.w, Math.ceil((wx1 - B.x0) * z)), py1 = Math.min(B.h, Math.ceil((wy1 - B.y0) * z));
  if (px1 <= px0 || py1 <= py0) return;
  g.save(); g.setTransform(1, 0, 0, 1, 0, 0); g.beginPath(); g.rect(px0, py0, px1 - px0, py1 - py0); g.clip();
  g.fillStyle = '#0d1410'; g.fillRect(px0, py0, px1 - px0, py1 - py0);
  g.setTransform(z, 0, 0, z, -B.x0 * z, -B.y0 * z); g.imageSmoothingEnabled = true; g.imageSmoothingQuality = Game.Q().smooth;
  const x0 = B.x0 + px0 / z, y0 = B.y0 + py0 / z, x1 = B.x0 + px1 / z, y1 = B.y0 + py1 / z;
  const tx0 = Math.max(0, Math.floor(x0 / T)), tx1 = Math.floor(x1 / T), ty0 = Math.max(0, Math.floor(y0 / T)), ty1 = Math.floor(y1 / T);
  let missing = false;
  for (let ty = ty0; ty <= ty1; ty++) for (let tx = tx0; tx <= tx1; tx++) if (!R.tiles[tx + ',' + ty] && tx * T < R.world.w && ty * T < R.world.h) missing = true;
  if (missing && R.mini) g.drawImage(R.mini, 0, 0, R.world.w, R.world.h); // low-res map under tiles still streaming in
  // 0.34: whole tiles cover exactly T (a tile decoded smaller rounds its size) and overlap the next one by 2 screen px:
  // their soft edges no longer let the dark background through as thin lines
  const ov = 2 / z;
  for (let ty = ty0; ty <= ty1; ty++) for (let tx = tx0; tx <= tx1; tx++) {
    const im = R.tiles[tx + ',' + ty]; if (!im) continue; const r = res * (im._k || 1);
    const lastX = (tx + 1) * T >= R.world.w - 1, lastY = (ty + 1) * T >= R.world.h - 1;
    g.drawImage(im, tx * T, ty * T, (lastX ? im.width / r : T + ov), (lastY ? im.height / r : T + ov));
  }
  g.restore();
}
function drawGround(R, ctx, cx, cy, z, W, H, sx, sy, zk = 1) {
  const B = GroundBuf, mx = Math.ceil(W * 0.2), my = Math.ceil(H * 0.2), bw = W + mx * 2, bh = H + my * 2;
  const vx0 = cx - W / 2 / z, vy0 = cy - H / 2 / z, vx1 = cx + W / 2 / z, vy1 = cy + H / 2 / z;
  const fresh = !B.c || B.w !== bw || B.h !== bh || B.z !== z || B.run !== R || B.n !== (R.tilesN || 0);
  const inside = !fresh && vx0 - 4 >= B.x0 && vy0 - 4 >= B.y0 && vx1 + 4 <= B.x0 + bw / z && vy1 + 4 <= B.y0 + bh / z;
  if (!inside) {
    if (!B.c || B.w !== bw || B.h !== bh) {
      for (const n of ['c', 'c2']) { B[n] = B[n] || document.createElement('canvas'); B[n].width = bw; B[n].height = bh; }
      B.w = bw; B.h = bh; B.g = B.c.getContext('2d', { alpha: false }); B.g2 = B.c2.getContext('2d', { alpha: false });
    }
    // snap the buffer origin to whole screen pixels so the blit needs no filtering
    const ox = B.x0, oy = B.y0, nx = Math.round((cx - bw / 2 / z) * z) / z, ny = Math.round((cy - bh / 2 / z) * z) / z;
    const dx = Math.round((ox - nx) * z), dy = Math.round((oy - ny) * z);
    B.x0 = nx; B.y0 = ny; B.z = z; B.run = R; B.n = R.tilesN || 0;
    const x1 = nx + bw / z, y1 = ny + bh / z;
    if (fresh || Math.abs(dx) >= bw / 2 || Math.abs(dy) >= bh / 2) paintGround(R, B, nx, ny, x1, y1);
    else {
      // 0.44: the camera left the buffer: what is already drawn slides over (one blit into the second buffer) and only
      // the strips that come into view are painted from the tiles (a whole repaint stalled weak GPUs for ~0.4 s)
      B.g2.setTransform(1, 0, 0, 1, 0, 0); B.g2.drawImage(B.c, dx, dy);
      [B.c, B.c2] = [B.c2, B.c]; [B.g, B.g2] = [B.g2, B.g];
      if (dx > 0) paintGround(R, B, nx, ny, nx + (dx + 2) / z, y1); else if (dx < 0) paintGround(R, B, x1 + (dx - 2) / z, ny, x1, y1);
      if (dy > 0) paintGround(R, B, nx, ny, x1, ny + (dy + 2) / z); else if (dy < 0) paintGround(R, B, nx, y1 + (dy - 2) / z, x1, y1);
    }
  }
  if (zk === 1) ctx.drawImage(B.c, Math.round((B.x0 - cx) * z + W / 2 + sx), Math.round((B.y0 - cy) * z + H / 2 + sy));
  else ctx.drawImage(B.c, (B.x0 - cx) * z * zk + W / 2 + sx, (B.y0 - cy) * z * zk + H / 2 + sy, B.w * zk, B.h * zk);   // (0.61: the death's close-in scales the buffer: no repaint per frame)
}
// 0.87 (ground areas with more character): what every area on the ground shares — a ring of runes turning on its
// rim (pre-rendered once per colour and size, RCache.runes), motes that tell its element (embers rising from fire, frost
// glints falling from cold, bubbles from poison, sparks of light otherwise: zoneMotes, drawn from the cached glow), a pop
// when it appears (a slight overshoot and a bright rim running out) and a soft shrink when it ends. Cheap: drawImage of
// cached pictures and a few glow dots, the same on the PixiJS and the 2D renderers.
function zoneElem(col) {
  const [r, g, b] = hexToRgb(col.length === 9 ? col.slice(0, 7) : col);
  if (r > 200 && g < 150 && b < 90) return 'fire';
  if (b > 170 && r < 140) return 'cold';
  if (g > 170 && r < 180 && b < 120) return 'poison';
  if (r > 140 && b > 140 && g < 150) return 'arcane';
  if (r > 150 && g < 70 && b < 110) return 'blood';
  return 'light';
}
const ZONE_MOTE = { fire: ['rgba(255,170,60,0.95)', -42, 0.9], cold: ['rgba(200,240,255,0.95)', 14, 0.7], poison: ['rgba(170,255,110,0.9)', -26, 0.8], arcane: ['rgba(230,180,255,0.95)', -20, 0.7], blood: ['rgba(255,80,80,0.9)', 16, 0.8], light: ['rgba(255,240,170,0.95)', -24, 0.7] };
// appearing / ending: [scale, alpha, flash 0..1] for an area born at `born`, ending at `until` (s), at time t
function zoneLife(born, until, t) {
  const age = t - born, left = until - t;
  const pop = age < 0.28 ? 1 + 0.14 * Math.sin(Math.min(1, age / 0.28) * Math.PI) : 1;
  const end = left < 0.4 ? 0.82 + 0.18 * Math.max(0, left / 0.4) : 1;
  return [pop * end, Math.min(1, age * 5) * Math.min(1, Math.max(0, left) * 2.5), age < 0.45 ? 1 - age / 0.45 : 0];
}
// the turning ring of runes, flattened like the ground (x, y = centre on the ground, r = reach)
function zoneRunes(ctx, x, y, r, col, t, a, speed = 0.35, kind) {
  if (a <= 0.01 || r < 10) return; const c = RCache.runes(col, r, kind), s = r / c.rb;
  ctx.save(); ctx.globalAlpha = Math.min(1, a); ctx.translate(x, y); ctx.scale(1, 0.62); ctx.rotate(t * speed);
  ctx.drawImage(c, -c.w * s / 2, -c.w * s / 2, c.w * s, c.w * s); ctx.restore();
}
// the bright rim that runs out when an area appears
function zoneFlash(ctx, x, y, r, col, f, soft) {
  if (f <= 0.01) return; const c = RCache.area(col, r, soft), s = r / c.rb * (1 + 0.25 * (1 - f));
  ctx.save(); ctx.globalAlpha = f * 0.8; ctx.globalCompositeOperation = 'lighter'; ctx.drawImage(c, x - c.w * s / 2, y - c.h * s / 2, c.w * s, c.h * s); ctx.restore();
}
// element motes: n glow dots placed on the area by a fixed hash of `seed`, each on its own loop
function zoneMotes(ctx, x, y, r, col, t, a, seed, n = 8) {
  if (a <= 0.01 || Game.lowFx) return; const [mc, vy, sz] = ZONE_MOTE[zoneElem(col)], sp = RCache.spark(mc);   // (0.98: sparks with a white head: round dots looked dull)
  for (let i = 0; i < n; i++) {
    const h1 = Math.sin(seed * 12.9898 + i * 78.233) * 43758.5453, h2 = Math.sin(seed * 39.346 + i * 11.135) * 24634.6345;
    const fx = (h1 - Math.floor(h1)) * 2 - 1, fy = (h2 - Math.floor(h2)) * 2 - 1, ph = ((t * 0.55 + (h1 - Math.floor(h1))) % 1);
    if (fx * fx + fy * fy > 1) continue;
    const px = x + fx * r * 0.85 + Math.sin(t * 2 + i) * 3, py = y + fy * r * 0.85 * 0.62 + vy * ph, k = Math.sin(ph * Math.PI), w = (3.4 + 2 * sz) * (0.7 + 0.3 * k), h = w * 3;
    ctx.globalAlpha = a * k * 0.9; ctx.drawImage(sp, px - w / 2, py - h * 0.2, w, h);
  }
  ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
}
// 0.89 (the Féca's glyphs replaced): Armure Incandescente — a crown of flickering flame tongues standing round the
// rim (stretched glows, a white-hot core at their feet), a warm glow on the ground inside; Trêve / Rempart élémentaire —
// a translucent dome rising from the ground (its body lit from the top left, meridians, a light band sweeping over it,
// its rim on the ground), golden for the truce, fiery for the rampart (which also wears the flames)
function drawFireArmor(ctx, x, y, r, t, a) {
  if (a <= 0.01) return;
  const fl = RCache.glow('rgba(255,120,30,0.95)'), core = RCache.glow('rgba(255,236,160,1)'), n = Math.max(12, Math.min(30, Math.round(r / 6)));
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  ctx.globalAlpha = a * 0.35; ctx.drawImage(fl, x - r * 0.9, y - r * 0.56, r * 1.8, r * 1.12);   // the heat on the ground
  for (let i = 0; i < n; i++) {
    const an = i / n * TAU + t * 0.6, fx = x + Math.cos(an) * r, fy = y + Math.sin(an) * r * 0.62;
    const fk = 0.55 + 0.45 * Math.abs(Math.sin(t * 7.3 + i * 1.91)) * (0.7 + 0.3 * Math.sin(t * 3.1 + i)), hh = r * 0.42 * fk, ww = Math.max(6, r * 0.13);
    ctx.globalAlpha = a * 0.85; ctx.drawImage(fl, fx - ww / 2, fy - hh, ww, hh * 1.15);
    ctx.globalAlpha = a * 0.7; ctx.drawImage(core, fx - ww * 0.28, fy - hh * 0.45, ww * 0.56, hh * 0.55);
  }
  ctx.restore();
}
function drawDome(ctx, x, y, r, t, a, col, born) {
  if (a <= 0.01) return;
  const age = t - born, grow = age < 0.35 ? 1 - Math.pow(1 - age / 0.35, 3) : 1, H = r * 0.92 * grow, ry = r * 0.62;
  const body = () => { ctx.beginPath(); ctx.ellipse(x, y, r, H, 0, Math.PI, 0); ctx.ellipse(x, y, r, ry, 0, 0, Math.PI); ctx.closePath(); };
  ctx.save();
  const g = ctx.createRadialGradient(x - r * 0.3, y - H * 0.7, r * 0.05, x, y - H * 0.3, r * 1.1);
  g.addColorStop(0, 'rgba(255,255,255,0.5)'); g.addColorStop(0.45, col + '48'); g.addColorStop(1, col + 'a0');
  ctx.globalAlpha = a; ctx.fillStyle = g; body(); ctx.fill();
  ctx.clip();   // inside the dome: meridians and the light band sweeping over it
  ctx.globalAlpha = a * 0.35; ctx.strokeStyle = 'rgba(255,255,255,0.8)'; ctx.lineWidth = 1.2;
  for (const k of [0.33, 0.66]) { ctx.beginPath(); ctx.ellipse(x, y, r * k, H, 0, Math.PI, 0); ctx.stroke(); }
  ctx.beginPath(); ctx.ellipse(x, y - H * 0.55, r * 0.84, ry * 0.5, 0, Math.PI, 0); ctx.stroke();
  const sw = ((t * 0.45) % 1) * 2.6 - 0.8, bx = x - r + sw * r, lg = ctx.createLinearGradient(bx - r * 0.25, 0, bx + r * 0.25, 0);
  lg.addColorStop(0, 'rgba(255,255,255,0)'); lg.addColorStop(0.5, 'rgba(255,255,255,0.28)'); lg.addColorStop(1, 'rgba(255,255,255,0)');
  ctx.globalAlpha = a; ctx.fillStyle = lg; ctx.fillRect(bx - r * 0.25, y - H - 4, r * 0.5, H + ry + 8);
  ctx.restore(); ctx.save();
  ctx.globalAlpha = a * 0.45; ctx.lineWidth = 5; ctx.strokeStyle = 'rgba(40,20,0,0.2)'; ctx.beginPath(); ctx.ellipse(x, y, r, H, 0, Math.PI, 0); ctx.stroke();   // (0.98: its outline softer)
  ctx.lineWidth = 2.8; ctx.strokeStyle = col; ctx.stroke(); ctx.lineWidth = 1; ctx.strokeStyle = 'rgba(255,255,255,0.7)'; ctx.stroke();
  ctx.globalAlpha = a * 0.75; ctx.lineWidth = 2.5; ctx.strokeStyle = 'rgba(255,255,255,0.85)'; ctx.lineCap = 'round';
  ctx.beginPath(); ctx.ellipse(x, y, r * 0.9, H * 0.9, 0, Math.PI * 1.18, Math.PI * 1.42); ctx.stroke();   // the shine
  ctx.restore();
}
// 0.90 (the weapons' areas with more punch, under the scenery like the other areas): a melee blow's footprint on
// the ground — the exact strip it hits snaps out with a white flash, speed streaks run along it, the ground cracks and
// dust bursts at its tip, a dark edge and a bright rim keep it readable; its colour tells the weapon (WEAPON_RGB, or the
// fused weapon's element). Slams (hammer, shovel) split the ground in a star of cracks round the impact (drawCracks).
const WEAPON_RGB = { epee: '255,214,90', dague: '190,230,255', baton: '180,150,255', hache: '255,96,70', marteau: '255,170,60', pelle: '230,190,120', baguette: '160,255,200', arc: '200,255,140' };
function weaponRgb(sp) { if (sp.fusion) return hexRgb(sp.fusion.color); const d = sp.def, k = d.of || (d.id || '').split('_')[0]; return WEAPON_RGB[k] || '255,214,90'; }
function hash01(n) { const x = Math.sin(n * 12.9898) * 43758.5453; return x - Math.floor(x); }
function drawWeaponSwath(ctx, s, t, rgb) {
  const age = t - s.t0, dur = s.spell.def.weapon ? 0.55 : 0.3, k = age / dur; if (k >= 1 || age < 0) return;
  const w = s.width / 2, L = s.range * (age < 0.07 ? 0.7 + 0.3 * age / 0.07 : 1), fa = k < 0.55 ? 1 : 1 - (k - 0.55) / 0.45, sd = s.t0 * 97.3 + s.a * 13;
  ctx.save(); ctx.translate(s.x, s.y + 14); ctx.rotate(s.a); ctx.lineJoin = 'round'; ctx.lineCap = 'round';
  // (0.95, perf sweep: its gradient-filled strip sent the ground effects to a full-screen 2D layer at every blow: the
  // strip, its flash and its outlines are pictures made once per weapon reach and colour, RCache.swath, stretched as it
  // shoots out over its first 0.07 s)
  const SW = RCache.swath(rgb, w, s.range), kx = L / s.range, sw = (c) => ctx.drawImage(c, -SW.p * kx, -w - SW.p, (s.range + 2 * SW.p) * kx, (w + SW.p) * 2);
  ctx.globalAlpha = fa; sw(SW.fill);
  if (age < 0.12) { ctx.globalAlpha = (1 - age / 0.12) * 0.75; sw(SW.snap); }   // the snap
  ctx.globalAlpha = fa; sw(SW.line);
  if (k < 0.5) {   // speed streaks running out along the strip
    ctx.globalAlpha = (1 - k / 0.5) * 0.9; ctx.strokeStyle = 'rgba(255,255,255,0.95)'; ctx.lineWidth = 2;
    for (let i = 0; i < 3; i++) { const yy = (i - 1) * w * 0.45, p0 = ((age * 3.2 + i * 0.27) % 1) * L * 0.8; ctx.beginPath(); ctx.moveTo(p0, yy); ctx.lineTo(Math.min(L - w * 0.4, p0 + L * 0.28), yy); ctx.stroke(); }
  }
  // the tip: cracks in the ground and a burst of dust
  const tx = L - w * 0.6, ca = Math.min(1, age / 0.06) * fa;
  ctx.globalAlpha = ca; for (const [lw, st] of [[3.2, 'rgba(40,24,10,0.8)'], [1.1, 'rgba(255,240,210,0.55)']]) {
    ctx.lineWidth = lw; ctx.strokeStyle = st;
    for (let i = 0; i < 5; i++) {
      const an = i / 5 * TAU + (hash01(sd + i) - 0.5) * 0.8, len = w * (0.45 + hash01(sd + i * 7) * 0.35); ctx.beginPath(); ctx.moveTo(tx, 0);
      for (let q = 1; q <= 2; q++) { const d = len * q / 2, j = (hash01(sd + i * 3 + q) - 0.5) * w * 0.2; ctx.lineTo(tx + Math.cos(an) * d - Math.sin(an) * j, Math.sin(an) * d * 0.7 + Math.cos(an) * j); }
      ctx.stroke();
    }
  }
  if (!Game.lowFx) { const dg = RCache.glow('rgba(190,170,140,0.75)'); for (let i = 0; i < 5; i++) { const an = hash01(sd + i * 5) * TAU, d = w * (0.3 + 1.2 * k) * (0.6 + hash01(sd + i) * 0.6), rr = w * (0.5 + k * 0.9); ctx.globalAlpha = (1 - k) * 0.55; ctx.drawImage(dg, tx + Math.cos(an) * d - rr, Math.sin(an) * d * 0.6 - rr, rr * 2, rr * 2); } }
  ctx.restore();
}
function drawCracks(ctx, x, y, R, k, seed) {
  if (k >= 1) return; const fa = k < 0.5 ? 1 : 1 - (k - 0.5) / 0.5;
  ctx.save(); ctx.lineJoin = 'round'; ctx.lineCap = 'round';
  ctx.globalAlpha = fa * 0.5; ctx.fillStyle = 'rgba(40,24,10,0.6)'; ctx.beginPath(); ctx.ellipse(x, y, R * 0.28, R * 0.28 * 0.62, 0, 0, TAU); ctx.fill();   // the dent
  for (const [lw, st] of [[3.6, 'rgba(40,24,10,0.85)'], [1.2, 'rgba(255,236,200,0.6)']]) {
    ctx.globalAlpha = fa; ctx.lineWidth = lw; ctx.strokeStyle = st;
    for (let i = 0; i < 8; i++) {
      const an = i / 8 * TAU + (hash01(seed + i) - 0.5) * 0.5, len = R * (0.55 + hash01(seed + i * 3) * 0.4) * Math.min(1, k * 6);
      ctx.beginPath(); ctx.moveTo(x + Math.cos(an) * R * 0.15, y + Math.sin(an) * R * 0.15 * 0.62);
      for (let q = 1; q <= 4; q++) { const d = R * 0.15 + (len - R * 0.15) * q / 4, j = (hash01(seed + i * 5 + q) - 0.5) * R * 0.12; ctx.lineTo(x + Math.cos(an) * d - Math.sin(an) * j, y + (Math.sin(an) * d + Math.cos(an) * j) * 0.62); }
      ctx.stroke();
      if (lw > 2 && i % 2 === 0) { const d0 = len * 0.6, b = an + (hash01(seed + i) > 0.5 ? 0.6 : -0.6); ctx.beginPath(); ctx.moveTo(x + Math.cos(an) * d0, y + Math.sin(an) * d0 * 0.62); ctx.lineTo(x + Math.cos(an) * d0 + Math.cos(b) * len * 0.3, y + (Math.sin(an) * d0 + Math.sin(b) * len * 0.3) * 0.62); ctx.stroke(); }
    }
  }
  ctx.restore();
}
// the area pictures (RCache.area): hex alphas of the fill (centre, 3/4, edge), the cells, the edge glow; outline / rim (width, alpha)
// the area pictures (RCache.area): the fill's stops (offset, hex alpha), the cells' alpha, the edge glow's stops, the dark
// outline and the rim (width, alpha) or null, the inner light line's alpha; feather: the cells fade towards the edge
const AREA_HARD = { fill: [[0, '30'], [0.75, '48'], [1, '70']], cells: '66', edge: [[0, '00'], [1, '55']], dark: [4.5, 0.45], rim: [2.2, 'ff'], light: 0.32 };
const AREA_SOFT = { fill: [[0, '26'], [0.55, '34'], [0.8, '3e'], [0.93, '22'], [1, '00']], cells: '30', edge: [[0, '00'], [0.62, '2a'], [0.86, '00']], dark: null, rim: null, light: 0, feather: true };
const ZONE_A = 0.8;   // 0.98: how strongly every spell zone on the ground is drawn (was 0.9 of the hard picture)
// 0.98: particles round an area on the ground (spell zones, traps, the monsters' puddles): motes of its element rising
// off its edge, each on its own loop; fewer in lowFx, none in minFx
function zoneRim(ctx, x, y, r, col, t, a, seed, n = 9) {
  if (a <= 0.01 || r < 14 || Game.minFx) return; if (Game.lowFx) n = Math.ceil(n / 2);
  const [mc, , sz] = ZONE_MOTE[zoneElem(col)], sp = RCache.spark(mc);   // (sparks with a white head)
  for (let i = 0; i < n; i++) {
    const ph = (t * (0.45 + 0.2 * ((i * 7) % 3) / 3) + i / n + seed * 0.37) % 1, an = i / n * TAU + seed + t * 0.12 + Math.sin(t * 0.7 + i) * 0.2, rr = r * (0.9 + 0.12 * Math.sin(i * 2.3 + t));
    const px = x + Math.cos(an) * rr, py = y + Math.sin(an) * rr * 0.62 - ph * (16 + 12 * sz), k = Math.sin(ph * Math.PI), w = (3.2 + 1.8 * sz) * (0.7 + 0.3 * k), h = w * 3.2;
    ctx.globalAlpha = a * k * 0.9; ctx.drawImage(sp, px - w / 2, py - h * 0.2, w, h);
  }
  ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
}
function drawArea(ctx, x, y, r, col, a, soft) {
  if (a <= 0.01 || r < 4) return; const c = RCache.area(col, r, soft), s = r / c.rb;
  ctx.globalAlpha = Math.min(1, a); ctx.drawImage(c, x - c.w * s / 2, y - c.h * s / 2, c.w * s, c.h * s); ctx.globalAlpha = 1;
}
function drawTinted(ctx, name, kind, x, y, scale) { const c = RCache.tinted(name, kind); if (!c) { Game.icons.draw(ctx, name, x, y, scale); return; } const s = scale / c.sc; ctx.drawImage(c, x - c.width * s / 2, y - c.height * s / 2, c.width * s, c.height * s); }
Run.prototype.draw = function (ctx) {
  const G = Game, ck = this.critK ? this.critK() : 0, zk = (this.deathFx ? this.deathZoomK() : 1) * (1 + 0.75 * ck), z = G.zoom * zk, P = this.player;   // (0.61: zk, the death's close-in, juice.js; 0.98: a critical summon's)
  if (ck > 0) { const [tx, ty] = this.camTarget(); this.cam.x = tx; this.cam.y = ty; }   // (the run runs at 1 %: the camera moves in real time, eased by critK)
  const W = G.cw, H = G.ch;
  let sx = 0, sy = 0;
  if (this.shakeAmt > 0) { sx = rand(-this.shakeAmt, this.shakeAmt); sy = rand(-this.shakeAmt, this.shakeAmt); }
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  const cx = this.cam.x, cy = this.cam.y;
  // PixiJS (WebGL, under this canvas; 0.62: the default) draws the world (pixi_render.js); this canvas, transparent,
  // keeps the texts and the HUD
  const px = PX.on;
  if (px) { ctx.clearRect(0, 0, W, H); PX.begin(this, cx, cy, z, W, H, sx, sy); }
  // world ground: the map tiles are pre-composited at screen resolution into a buffer a bit larger than the view,
  // redrawn only when the camera nears its edge or new tiles arrive; each frame is then a single unscaled blit
  else drawGround(this, ctx, cx, cy, G.zoom, W, H, sx, sy, zk);
  ctx.setTransform(z, 0, 0, z, W / 2 - cx * z + sx, H / 2 - cy * z + sy);
  ctx.imageSmoothingEnabled = true; ctx.imageSmoothingQuality = G.lowFx ? 'low' : G.Q().smooth;   // (0.44: by quality)
  const vx0 = cx - G.viewW / 2 - 20, vx1 = cx + G.viewW / 2 + 20, vy0 = cy - G.viewH / 2 - 20, vy1 = cy + G.viewH / 2 + 20;
  // darken outside bounds
  const b = this.bounds;
  if (px) PX.outside(b, vx0, vy0, vx1, vy1);
  else {
    ctx.fillStyle = 'rgba(0,0,0,0.35)';
    ctx.fillRect(vx0, vy0, b.x0 - vx0, vy1 - vy0); ctx.fillRect(b.x1, vy0, vx1 - b.x1, vy1 - vy0);
    ctx.fillRect(b.x0, vy0, b.x1 - b.x0, b.y0 - vy0); ctx.fillRect(b.x0, b.y1, b.x1 - b.x0, vy1 - b.y1);
  }
  const inView = (x, y, m = 80) => x > vx0 - m && x < vx1 + m && y > vy0 - m && y < vy1 + m;
  const t = this.time;
  // 0.62: with PixiJS, each part below is drawn by the same 2D code at its place in the drawing order: as PixiJS quads
  // when it only draws pictures, rectangles and ellipses (PXCtx), else into a 2D layer / a small box of its own (PX.nat)
  const nat = px ? (key, fn, box) => PX.nat(key, fn, box) : (key, fn) => fn(ctx);
  // 0.88 (the areas on the ground under the scenery): the spells' areas, traps, impacts, rings and auras are drawn
  // in a layer of their own, erased under the world's tall scenery (Run.underDecor): the trees then stand in front of them.
  // What warns of a danger (telegraphs, hostile puddles), the treasure cross and ToT's door stay over everything.
  const groundFx = ctx => {
  P.drawFloor(ctx);   // (0.91: the character's shadow and ring, under the scenery)
  if (this.cawottes && this.cawottes.length) this.drawCawottes(ctx, t, 'ground');   // (0.74: the red zone under everyone; round since 0.76)
  // zones (glyphs)
  for (const zn of this.zones) {
    if (!inView(zn.x, zn.y, zn.r)) continue;
    const [zs, a, zf] = zoneLife(zn.born, zn.until, t), col = zn.color || '#ff7a1a', glyph = zn.spell && zn.spell.p.glyph, web = zn.spell && zn.spell.p.web, rr = zn.r * zs;   // (0.87: pops in, shrinks away)
    if (!glyph) drawArea(ctx, zn.x, zn.y, rr, col, a * ZONE_A, true);   // v2.0: the exact reach of the zone (0.98: soft, one rule for every zone)
    zoneFlash(ctx, zn.x, zn.y, zn.r, col, zf, true);
    if (zn.puff) drawPoisonPuff(ctx, zn, t); else if (zn.cloud) drawCloud(ctx, zn, a, t); else if (zn.chaos) drawChaosZone(ctx, zn, a, t); else if (glyph) drawGlyphCells(ctx, zn, a, t); else if (web) drawWeb(ctx, zn, a, t); else if (zn.armor || zn.dome) { if (zn.dome) drawDome(ctx, zn.x, zn.y, rr, t, a, col, zn.born); if (zn.armor) drawFireArmor(ctx, zn.x, zn.y, rr, t, a); } else drawGlyph(ctx, zn.x, zn.y, rr, col, a, t);   // (0.89: the Féca's armour / dome)
    if (!zn.puff && !web) zoneRim(ctx, zn.x, zn.y, rr, col, t, a, zn.born * 3.1 + zn.x);   // (0.98: sparks round its edge)
    if (!web && !zn.chaos && !zn.puff) { if (!zn.cloud && !glyph) zoneRunes(ctx, zn.x, zn.y, rr, col, t, a * 0.4, 0.4); zoneMotes(ctx, zn.x, zn.y, rr, col, t, a, zn.born * 7.3 + zn.x, zn.cloud ? 5 : 8); }   // (the Féca glyphs keep the client's own cells)
  }
  this.drawWeaponFx(ctx, t, 'ground');   // a fused weapon's element ring (weapons.js)
  // 0.90: the melee blows' footprints (the strip each blow hits) on the ground, under the scenery
  for (const s of this.slashes) { if (t < s.t0 || !(s.cleave || FxSheets.get(s.spell.def.fx[0]) || s.spell.def.weapon)) continue; drawWeaponSwath(ctx, s, t, s.cleave ? '255,96,70' : s.spell.def.weapon ? weaponRgb(s.spell) : '255,214,90'); }
  // traps
  // 0.92: quieter areas (0.4 -> 0.26) with a turning ring of little daggers (knife runes) like the other ground
  // spells; the fused Piège Empoisonné in its own colours: a dark green area and green runes, the cone green and dark red,
  // green / violet smoke and tiny streaks rising off it (drawPoisonTrapFx)
  for (const tr of this.traps) {
    const fu = tr.spell && tr.spell.def.id === 'fu_sram_piege', col = fu ? '#2f7a34' : '#b388ff';
    if (t >= tr.armed) {   // what it covers when it goes off
      drawArea(ctx, tr.x, tr.y, tr.r, col, fu ? 0.42 : 0.38, true); zoneRim(ctx, tr.x, tr.y, tr.r, col, t, 0.6, tr.x * 0.37, 6);   // (0.98: soft, its aberration, sparks)
      zoneRunes(ctx, tr.x, tr.y, tr.r, fu ? '#7ee05a' : '#c9a8ff', t, fu ? 0.55 : 0.5, fu ? -0.45 : 0.3, 'knife');
      if (fu) drawPoisonTrapFx(ctx, tr, t);
    }
    ctx.save(); ctx.globalAlpha = t < tr.armed ? 0.4 : 0.85;
    drawTrapCone(ctx, tr.x, tr.y, t, fu ? TRAP_POISON : null);
    ctx.restore();
  }
  // v2.0: spells about to land (strikes with a delay): their area is already marked on the ground
  for (const s of this.strikes) {
    if (s.at <= t || s.tgt || !inView(s.x, s.y, s.r)) continue;   // (0.98.1: s.tgt, a blow on one monster: nothing on the ground)
    const d = s.delay || 0.6, k = clamp(1 - (s.at - t) / d, 0, 1);
    const scol = (s.spell && s.spell.p && s.spell.p.color) || '#ffcc33'; drawArea(ctx, s.x, s.y, s.r, scol, 0.35 + 0.45 * k);
    { const cr = s.r * (1.6 - 0.6 * k); ctx.save(); ctx.globalAlpha = 0.25 + 0.6 * k; ctx.lineWidth = 2.5; ctx.strokeStyle = 'rgba(0,0,0,0.45)'; ctx.beginPath(); ctx.ellipse(s.x, s.y, cr, cr * 0.62, 0, 0, TAU); ctx.stroke(); ctx.lineWidth = 1.5; ctx.strokeStyle = scol; ctx.stroke(); ctx.restore(); }   // (0.87: a ring closing in on the impact)
  }
  // rings
  for (const r of this.rings) {
    if (t < r.t0) continue;
    const k = clamp((t - r.t0) / r.dur, 0, 1); const rr = lerp(r.r0, r.r1, r.r0 === r.r1 ? 1 : easeOut(k));
    const x = r.follow ? r.follow.x : r.x, y = r.follow ? r.follow.y : r.y;
    // v2.0: a spell's area (filled ring) shows its whole reach at once, then fades; the expanding rim keeps the punch
    if (r.fill) drawArea(ctx, x, y, r.r1, r.color, Math.pow(1 - k, 0.6));
    if (r.crack) drawCracks(ctx, x, y, r.r1, k, r.t0 * 31.7 + x);   // (0.90: a slam splits the ground)
    ctx.save(); ctx.lineWidth = 5 * (1 - k) + 2.5; ctx.globalAlpha = (1 - k) * 0.5; ctx.strokeStyle = 'rgba(0,0,0,0.6)';
    ctx.beginPath(); ctx.ellipse(x, y, rr, rr * 0.62, 0, 0, TAU); ctx.stroke();
    ctx.globalAlpha = (1 - k) * 0.95; ctx.strokeStyle = r.color; ctx.lineWidth = 4 * (1 - k) + 1.5; ctx.stroke(); ctx.restore();
    if (r.fill && !Game.lowFx && rr > 20) {   // 0.87: sparks riding the rim as it runs out, a light at its start
      const gl = RCache.glow(ZONE_MOTE[zoneElem(r.color)][0]), n = Math.min(18, 6 + Math.round(rr / 18)), d = 7 * (1 - k) + 2;
      for (let i = 0; i < n; i++) { const an = i / n * TAU + r.t0 * 3; ctx.globalAlpha = (1 - k) * 0.9; ctx.drawImage(gl, x + Math.cos(an) * rr - d, y + Math.sin(an) * rr * 0.62 - d, d * 2, d * 2); }
      if (k < 0.3) zoneFlash(ctx, x, y, r.r1 * 0.5, r.color, 1 - k / 0.3);
      ctx.globalAlpha = 1;
    }
  }
  // auras around the player
  for (const sp of this.spells) if (sp.def.t === 'aura' && !P.dead) {
    // 0.87 (livelier areas): the aura breathes (the area's picture), its runes turn, a second fainter ring
    // turns the other way inside, and its element's motes rise round the character
    const r = sp.p.radius * this.stats.area, col = sp.p.color || '#ffffff', pulse = 0.94 + 0.06 * Math.sin(t * 4);
    drawArea(ctx, P.x, P.y, r * pulse, col, 0.75);
    zoneRunes(ctx, P.x, P.y, r, col, t, 0.95, 0.5); zoneRunes(ctx, P.x, P.y, r * 0.62, col, t, 0.45, -0.8);
    zoneMotes(ctx, P.x, P.y, r, col, t, 0.9, sp.def.id.length * 3.1, 10);
    if (sp.p.mist) drawMist(ctx, P.x, P.y, r, col, t);   // (0.91: Brume Mutagène)
  }
  // door
  };
  this.underDecor(ctx, px, nat, groundFx);
  nat(null, ctx => {
  this.drawTmapCross(ctx, t); this.drawHzones(ctx, t);
  // telegraphs (0.95: their outlines as pictures / rectangles: PixiJS draws them itself, no 2D layer for a fight's warnings)
  for (const te of this.teles) {
    const k = clamp((t - te.t0) / te.dur, 0, 1);
    ctx.save();
    ctx.fillStyle = `rgba(255,40,40,${0.12 + 0.18 * k})`; ctx.strokeStyle = `rgba(255,80,60,${0.6})`; ctx.lineWidth = 2;
    if (te.kind === 'circle') { ctx.beginPath(); ctx.ellipse(te.x, te.y, te.r, te.r * 0.62, 0, 0, TAU); ctx.fill(); ringAt(ctx, 'rgba(255,80,60,0.6)', te.x, te.y, te.r, te.r * 0.62, 2); ctx.fillStyle = 'rgba(255,60,40,0.3)'; ctx.beginPath(); ctx.ellipse(te.x, te.y, te.r * k, te.r * 0.62 * k, 0, 0, TAU); ctx.fill(); }
    else if (te.kind === 'line') { ctx.translate(te.x, te.y); ctx.rotate(te.a); ctx.fillRect(0, -te.w / 2, te.len, te.w); edgeRect(ctx, 0, -te.w / 2, te.len, te.w, 2); ctx.fillStyle = 'rgba(255,60,40,0.3)'; ctx.fillRect(0, -te.w / 2, te.len * k, te.w); }
    else if (te.kind === 'cone') { ctx.beginPath(); ctx.moveTo(te.x, te.y); ctx.arc(te.x, te.y, te.len, te.a - te.half, te.a + te.half); ctx.closePath(); ctx.fill(); ctx.stroke(); }
    ctx.restore();
  }
  if (this.door) drawTimePortal(ctx, this.door.x, this.door.y, t);   // 0.26: ToT's door is a Xélor time portal (events.js)
  });
  // pickups
  for (const p of this.pickups) {
    if (!inView(p.x, p.y, 20)) continue;
    nat('pk' + p.kind, ctx => drawPickup(ctx, p, t));
  }
  // Roublard walls of fire between bombs
  if (this.walls.length) nat(null, ctx => { for (const [A, B] of this.walls) drawFireWall(ctx, A, B, t); });
  // entities sorted by y
  const ents = [], stq = _statusQ; stq.length = 0;
  for (const m of this.mobs) if (inView(m.x, m.y, 160)) { ents.push(m); if (!m.dying && (m.poisonUntil > t || m.bleedUntil > t)) stq.push(m); }
  if (stq.length > STATUS_FULL) { for (const m of stq) m._d2 = dist2(m.x, m.y, P.x, P.y); stq.sort((a, b) => a._d2 - b._d2); }   // (0.59: the nearest ones in full)
  for (let i = 0; i < stq.length; i++) stq[i]._fullFx = i < STATUS_FULL;
  if (P.dash || P.trail.length) for (const tr of P.trail) { /* drawn by the player */ }
  for (const s of this.summons) ents.push(s);
  for (const a of this.allies) ents.push(a);
  for (const b of this.bombs) if (!b.done) ents.push(b);
  ents.push(P);
  ents.sort((a, b) => a.y - b.y);
  const frozen = t < this.freezeUntil;
  // all ground shadows in one path (one fill instead of one per monster)
  if (Game.minFx) { }   // (0.95: no monster shadows in the minimal effects)
  else if (px) PX.shadows(this.mobs, inView);
  else {
    ctx.fillStyle = `rgba(0,0,0,${MOB_SHADOW_A})`; ctx.beginPath();
    for (const m of this.mobs) { if (m.dying || m.carried || !inView(m.x, m.y, 60)) continue; const rx = mobShadowR(m); ctx.moveTo(m.x + rx, m.y); ctx.ellipse(m.x, m.y, rx, rx * 0.42, 0, 0, TAU); }
    ctx.fill();
  }
  const drawP = (c) => { if (this.reviveAt) { const re = (performance.now() - this.reviveAt) / 1000; if (re < 2.8) drawReviveBack(c, P, re); } if (t - (P.drainT || -9) < 0.6) drawDrainPlayer(c, P, t, 0); P.draw(c); if (t - (P.drainT || -9) < 0.6) drawDrainPlayer(c, P, t, 1); this.occludePlayer(c); drawPlayerBars(c, this); };   // (0.91: behind the scenery)
  for (const e of ents) {
    if (e === P) { if (px) PX.player(P, drawP); else drawP(ctx); continue; }
    // (0.62: bombs, allies, the Double and the Mama at their depth among the monsters with PixiJS too)
    if (e.bomb) { nat('bomb', ctx => drawBomb(ctx, e, t, this), [e.x - 150, e.y - 190, e.x + 150, e.y + 70]); continue; }   // (before summons: a bomb also carries its spell)
    if (e.spell) { if (px && e.sh && !e.decoy && !e.cs) PX.summon(e, t); else nat(e.decoy ? 'decoy' : 'csum', ctx => drawSummon(ctx, e, t), [e.x - 110, e.y - 200, e.x + 110, e.y + 40]); continue; }
    if (e.kind && this.allies.includes(e)) { nat('ally', ctx => drawAlly(ctx, e, t, this), [e.x - 150, e.y - 230, e.x + 150, e.y + 60]); continue; }
    if (px) PX.mob(e, t, frozen); else drawMob(ctx, e, t, frozen);
  }
  nat(null, ctx => {
  // the Enutrof merchant (random event): standing, with a sign
  if (this.merchant && this.merchantSprite && this.merchantSprite.ready) {
    const M = this.merchant; this.merchantSprite.draw(ctx, 'staticR', t, M.x, M.y, ES, M.x > P.x, { loop: true });
    const bob = Math.sin(t * 3) * 3; ctx.drawImage(Game.icons.canvas('KamaSymbol', 64), M.x - 13, M.y - 104 + bob, 26, 26);
    outlinedText(ctx, T('merchant'), M.x, M.y - 112 + bob, '#ffd27a', 12, 'center');
  }
  // a dropped Dofus: a big animated red arrow above it, drawn over the monsters
  for (const q of this.pickups) if (q.kind === 'dofus') {
    const by = q.y - 62 - Math.abs(Math.sin(t * 5)) * 14;
    ctx.save(); ctx.translate(q.x, by); ctx.fillStyle = '#ff2a2a'; ctx.strokeStyle = '#3a0000'; ctx.lineWidth = 3; ctx.lineJoin = 'round';
    ctx.beginPath(); ctx.moveTo(-9, -26); ctx.lineTo(9, -26); ctx.lineTo(9, -6); ctx.lineTo(19, -6); ctx.lineTo(0, 14); ctx.lineTo(-19, -6); ctx.lineTo(-9, -6); ctx.closePath(); ctx.stroke(); ctx.fill();
    ctx.restore();
  }
  });
  // orbiters
  for (const o of this.orbiters) nat('orb' + (o.spell.p.star ? 's' : o.spell.p.hourglass ? 'h' : o.spell.p.drawIcon ? 'i' : o.spell.def.weapon ? 'w' : 'f'), ctx => {
    if (o.spell.p.star) { drawAuraOrb(ctx, o, t, this); return; }   // Sagesse fusion (0.61: violet aura orbs, no more star icons)
    if (o.spell.p.hourglass) { drawHourglassOrb(ctx, o, t, this); return; }   // Horloge fusion (0.65: light violet hourglasses)
    if (o.spell.p.drawIcon) { // Faux qui Spin: the cursed scythe, spinning on itself, with a blood-red wake
      const sz = o.spell.p.size * 2.9, sp = o.spell.p.rotSpeed, r = o.spell.p.radius * this.stats.area;
      ctx.save(); ctx.globalAlpha = 0.35; ctx.strokeStyle = '#b0182a'; ctx.lineCap = 'round';
      for (let k = 1; k <= 3; k++) { ctx.lineWidth = 7 - k * 1.6; ctx.beginPath(); ctx.ellipse(this.player.x, this.player.y - 20, r, r * 0.6, 0, ellAngle(o.a - 0.22 * k), ellAngle(o.a - 0.22 * (k - 1))); ctx.stroke(); }
      ctx.globalAlpha = 1; ctx.translate(o.x, o.y); ctx.rotate(t * sp * 3.2 + o.a);
      Game.icons.drawFit(ctx, o.spell.p.drawIcon, 0, 0, sz); ctx.restore(); return;
    }
    if (o.spell.def.weapon) { // spinning weapon (staff)
      ctx.save(); ctx.translate(o.x, o.y); ctx.rotate(o.a * 2.5);
      const sz = o.spell.p.size * 2.4; ctx.drawImage(Game.icons.canvas(o.spell.icon || o.spell.def.icon, 96), -sz / 2, -sz / 2, sz, sz); ctx.restore(); return;
    }
    // Bouclier Féca: the client's glyph (fx 802) tinted red, on a red glow, so it reads well on every ground
    const fx = FxSheets.get(802), sz = o.spell.p.size, pulse = 0.8 + 0.2 * Math.sin(t * 7 + o.a);
    ctx.save(); ctx.translate(o.x, o.y);
    ctx.drawImage(RCache.glow('rgba(255,60,40,0.8)'), -sz * 2.3, -sz * 2.3, sz * 4.6, sz * 4.6);
    ctx.globalAlpha = pulse; ctx.strokeStyle = '#ff5a3c'; ctx.lineWidth = 2.5; ctx.beginPath(); ctx.arc(0, 0, sz + 5, 0, TAU); ctx.stroke(); ctx.globalAlpha = 1;
    const tc = fx && fx.anims.root && redGlyph(fx, fx.anims.root.f[0]);
    if (tc) { ctx.rotate(o.a); ctx.drawImage(tc, -tc.width / 2, -tc.height / 2); }
    else { ctx.strokeStyle = '#ff6a4a'; ctx.lineWidth = 3; ctx.beginPath(); ctx.arc(0, 0, sz, 0, TAU); ctx.stroke(); }
    ctx.restore();
  });
  nat(null, ctx => {
  // La bonne Pioche: the pick swings down beside the character
  if (this.cawottes && this.cawottes.length) nat(null, ctx => this.drawCawottes(ctx, t, 'top'));   // (0.71: gspells.js; the Cawotte and the spinning cawottes)
  for (const d of this.digs) {
    const k = clamp((t - d.t0) / 0.25, 0, 1), fade = clamp(1 - (t - d.t0 - 0.4) / 0.2, 0, 1);
    ctx.save(); ctx.globalAlpha = fade; ctx.translate(d.x, d.y - 18); ctx.scale(d.side, 1); ctx.rotate(-1.9 + 2.1 * k * k);
    Game.icons.drawFit(ctx, 'it_21_1', 14, -14, 44); ctx.restore();
  }
  this.drawWeaponFx(ctx, t, 'top');   // lightning, shockwaves, cracks, gusts, Ares's rage
  });
  // projectiles
  // (0.71: a projectile fades out blinking in its last 0.45 s instead of vanishing at once)
  const fade = (q) => q.lob || !(q.life < 0.45) ? 1 : Math.max(0, q.life / 0.45) * (0.6 + 0.4 * Math.cos(t * 38));
  for (const p of this.projs) { if (p.delay > 0 || !inView(p.x, p.y)) continue; const f = fade(p); nat('pr' + p.spell.def.id, ctx => { if (f < 1) { ctx.save(); ctx.globalAlpha *= f; } drawProj(ctx, p, t); if (f < 1) ctx.restore(); }); }
  // 0.92 (the monsters' projectiles still vanished abruptly): the old games' blink — fully on / fully off, faster and
  // faster over its last 0.8 s (the count of switches grows as a power of the time spent blinking)
  const blink = (q) => q.lob || !(q.life < 0.8) ? 1 : Math.floor(Math.pow(0.8 - q.life, 1.35) * 30) % 2 ? 0 : 1;
  for (const e of this.eprojs) { if (!inView(e.x, e.y)) continue; const f = blink(e); if (!f) continue; nat(null, ctx => { if (f < 1) { ctx.save(); ctx.globalAlpha *= f; } drawEProj(ctx, e, t); if (f < 1) ctx.restore(); }); }
  nat(null, ctx => {
  // slashes
  for (const s of this.slashes) {
    if (t < s.t0) continue; const k = clamp((t - s.t0) / (s.spell.def.weapon ? 0.55 : 0.25), 0, 1);
    if (s.cleave) { drawCleave(ctx, s, t); continue; }   // (0.90: the strip it hits is drawn on the ground, drawWeaponSwath)
    if (FxSheets.get(s.spell.def.fx[0]) || s.spell.def.weapon) continue;   // the weapon's animation is drawn by the fx; its strip is on the ground
    ctx.save(); ctx.translate(s.x, s.y); ctx.rotate(s.a); ctx.globalAlpha = 1 - k;
    const g = ctx.createLinearGradient(0, 0, s.range, 0); g.addColorStop(0, 'rgba(255,255,255,0)'); g.addColorStop(1, 'rgba(255,240,200,0.85)');
    ctx.fillStyle = g; ctx.beginPath(); ctx.ellipse(s.range * 0.5, 0, s.range * 0.55, s.width * 0.5 * (0.5 + k), 0, 0, TAU); ctx.fill();
    ctx.restore();
  }
  // beams
  for (const bm of this.beams) {
    if (bm.fire) { drawFireLine(ctx, bm, t); continue; }
    if (bm.wave) { bm.dim = FxSheets.get(bm.spell && bm.spell.def.fx[0]) ? 0.35 : 1; drawWave(ctx, bm, t); continue; }   // (0.61: the client's waves carry it, the drawn breaker only faint under them)
    const k = clamp((bm.until - t) / 0.35, 0, 1) * (bm.dup ? 0.35 : 1);   // (0.60: Rayon Obscur: its columns of light carry it, a faint streak under them)
    ctx.save(); ctx.translate(bm.x, bm.y); ctx.rotate(bm.a); ctx.globalAlpha = k;
    ctx.drawImage(RCache.band('rgba(0,0,0,0)', bm.color || '#fff'), 0, -bm.w / 2, bm.len, bm.w);   // (0.95: its gradient as a picture, RCache.band)
    ctx.fillStyle = 'rgba(255,255,255,0.8)'; ctx.fillRect(0, -bm.w * 0.12, bm.len, bm.w * 0.24);
    ctx.restore();
  }
  // cones
  for (const c of this.cones) {
    const k = clamp((t - c.t0) / (c.until - c.t0), 0, 1);
    ctx.save(); ctx.globalAlpha = 0.7 * (1 - k);
    const g = ctx.createRadialGradient(c.x, c.y, 5, c.x, c.y, c.range);
    g.addColorStop(0, c.color || '#d9f5a0'); g.addColorStop(1, 'rgba(180,230,120,0)');
    ctx.fillStyle = g; ctx.beginPath(); ctx.moveTo(c.x, c.y); ctx.arc(c.x, c.y, c.range * (0.6 + 0.4 * k), c.a - c.half, c.a + c.half); ctx.closePath(); ctx.fill();
    ctx.globalAlpha = 0.9 * (1 - k); ctx.strokeStyle = c.color || '#e8ffb8'; ctx.lineWidth = 2.5; ctx.beginPath(); ctx.moveTo(c.x, c.y); ctx.arc(c.x, c.y, c.range, c.a - c.half, c.a + c.half); ctx.closePath(); ctx.stroke();
    ctx.restore();
  }
  if (this.reviveAt) { const e = (performance.now() - this.reviveAt) / 1000; if (e < 2.8) drawReviveFront(ctx, P, e); }
  if (this.drains && this.drains.length) drawDrains(ctx, this, t);
  });
  nat(null, ctx => {
  // fx animations
  for (const e of this.effects) {
    if (e.t < 0 || !inView(e.x, e.y, 200)) continue;   // (0.60: t < 0 = not started yet, Rayon Obscur's wave)
    const f = e.sh.frameAt(e.sym, e.t, false);
    if (!f) continue;
    if (e.off) {   // (0.54: drawn from a point of the picture, e.g. the whip's handle, stretched across by sy)
      ctx.save(); ctx.translate(e.x, e.y); ctx.rotate(e.flip ? e.rot + Math.PI : e.rot); ctx.scale(1, e.sy || 1);
      for (const dy of [-0.55, 0.55, 0]) e.sh.draw(ctx, f, (e.flip ? 1 : -1) * e.off[0] * e.scale, -e.off[1] * e.scale + dy, e.scale, !!e.flip);   // (three passes: the thin client lash, thicker)
      ctx.restore();
    } else if (e.rot) {
      ctx.save(); ctx.translate(e.x, e.y); ctx.rotate(e.flip ? e.rot + Math.PI : e.rot);
      e.sh.draw(ctx, f, 0, 0, e.scale, !!e.flip, e.tint && tintedSheet(e.sh, e.tint)); ctx.restore();
    } else e.sh.draw(ctx, f, e.x, e.y, e.scale, e.flip, e.tint && tintedSheet(e.sh, e.tint));
  }
  // 0.60: Éboulement du Craqueleur: the rocks falling on their marks
  for (const st of this.strikes) if (st.rock && st.at > t && inView(st.x, st.y, 60)) { const k = clamp(1 - (st.at - t) / (st.delay || 0.7), 0, 1); drawRock(ctx, st.x, st.y - (1 - k * k) * 320, st.r * 0.55, t * 6 + st.x); }
  });
  // 0.91: the effects behind scenery: the scenery in front of their foot drawn again over them (6 a frame at most;
  // 0.95: 3 with the reduced effects, none with the minimal ones)
  if (this.depth && !Game.minFx) {
    let n = 0; const nMax = Game.lowFx ? 3 : 6;
    for (const e of this.effects) {
      if (e.t < 0 || e.off || e.rot || n >= nMax || !inView(e.x, e.y, 200)) continue;
      const f = e.sh.frameAt(e.sym, e.t, false); if (!f) continue;
      const s = e.scale / (e.sh.zoom || 1), bx0 = e.x - f[4] * s, by0 = e.y - f[5] * s, bx1 = bx0 + f[2] * s, by1 = by0 + f[3] * s;
      if (!this.frontMask(bx0, by0, bx1, by1, e.y + 6)) continue;
      n++; const fn = c => this.decorFront(c, bx0, by0, bx1, by1, e.y + 6, 0.85, g => e.sh.draw(g, f, e.x, e.y, e.scale, e.flip));
      if (px) PX.proxy(bx0, by0, bx1, by1, fn); else fn(ctx);
    }
  }
  // particles
  if (px) PX.particles(this.particles, inView);
  else for (const p of this.particles) { if (!inView(p.x, p.y, 10)) continue; const k = 1 - p.t / p.life; ctx.globalAlpha = k; ctx.fillStyle = p.c; if (p.star) { const r = p.s * (0.6 + k * 0.6); ctx.globalAlpha = k; ctx.beginPath(); for (let i = 0; i < 8; i++) { const rr = i % 2 ? r * 0.28 : r, aa = i / 8 * TAU; ctx.lineTo(p.x + Math.cos(aa) * rr, p.y + Math.sin(aa) * rr); } ctx.closePath(); ctx.fill(); } else if (p.round) { ctx.globalAlpha = k * 0.55; ctx.beginPath(); ctx.arc(p.x, p.y, p.s / 2 * (1 + (p.grow || 0) * (1 - k)), 0, TAU); ctx.fill(); } else ctx.fillRect(p.x - p.s / 2, p.y - p.s / 2, p.s, p.s); }
  ctx.globalAlpha = 1;
  // 0.60: the character is never lost under the crowd or the effects: a faint copy of it over everything
  { const D = P._drawn; if (D && !P.dead && !(this.time < P.invisUntil)) P.sprite.draw(ctx, D.anim, D.t, P.x, P.y - P.leapH, ES * (D.sc || 1), D.flip, { loop: D.loop, alpha: 0.32, moving: P.moving, at: this.time }); }
  if (this.deathFx) drawSoul(ctx, this, this.deathE());
  // texts
  for (const tx of this.texts) { // cached bitmaps rendered at screen resolution; the pop-in is a scale of the bitmap
    if (!inView(tx.x, tx.y, 30)) continue;
    const k = tx.t / tx.life; ctx.globalAlpha = k > 0.7 ? (1 - k) / 0.3 : 1;
    if (tx.num) {   // 0.85: a damage number as the client plays it (clips/points): it pops in big and pale, settles, rises, fades
      const p = k < 0.12 ? (0.12 - k) / 0.12 : 0; NumCache.draw(ctx, tx.s, tx.color, tx.size * z, tx.x, tx.y, (1 + p * 0.8) / z, p);
      continue;
    }
    const c = tx.c || (tx.c = TextCache.get(tx.s, tx.color, tx.size * z, 'rgba(0,0,0,0.85)', 3 * z));
    const sc = (k < 0.12 ? 1 + (0.12 - k) * 4 : 1) / z, ax = c.tw / 2;
    ctx.drawImage(c, tx.x - (c.bx + ax) * sc, tx.y - c.by * sc, c.width * sc, c.height * sc);
  }
  ctx.globalAlpha = 1;
  if (frozen) { ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.fillStyle = 'rgba(120,200,255,0.12)'; ctx.fillRect(0, 0, W, H); }
  // HUD
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  this.drawJuice(ctx, W, H);   // (0.60: flashes, low-life vignette: juice.js)
  drawHud(ctx, this);
  if (this.cine) this.drawCineScreen(ctx, W, H);
  if (this.tofuShowUntil) drawKonami(ctx, this, W, H);
  { const ca = this.chromaK ? this.chromaK() : 0; if (px) { PX.ca = ca; PX.end(); } }   // (0.98: PX.ca, the chromatic aberration of the moment; read every frame: its clocks start on their own)
};
// 0.88: draws fn (the areas on the ground) under the world's tall scenery: into a full-screen 2D layer of its own (PixiJS:
// a fresh PX layer; 2D: an offscreen canvas), then erases it where the decor mask (assets/worlds/<world>_decor.webp,
// tools/assets/decormask087.py) says a tree / rock / wall stands — the ground picture under it already shows that scenery.
// Without a mask (not loaded yet) it draws as before.
Run.prototype.underDecor = function (ctx, px, nat, fn) {
  const M = this.decorImg, K = this.world && this.world.decor && this.world.decor[1];
  if (px) { PX.groundStart(M && K ? M : null, K); try { nat(null, fn); } finally { PX.groundEnd(); } return; }   // (0.95: the GPU hides them under the scenery)
  if (!M || !K) { fn(ctx); return; }
  const off = this._udc || (this._udc = document.createElement('canvas')); if (off.width !== ctx.canvas.width || off.height !== ctx.canvas.height) { off.width = ctx.canvas.width; off.height = ctx.canvas.height; }
  const g = this._udg || (this._udg = off.getContext('2d')); g.setTransform(1, 0, 0, 1, 0, 0); g.globalAlpha = 1; g.globalCompositeOperation = 'source-over'; g.clearRect(0, 0, off.width, off.height);
  g.setTransform(ctx.getTransform()); g.imageSmoothingEnabled = true; g.imageSmoothingQuality = ctx.imageSmoothingQuality;
  fn(g);
  // the part of the mask on screen, in world units (the inverse of the layer's transform at the screen corners)
  const T = g.getTransform(), inv = T.inverse(), W = g.canvas.width, H = g.canvas.height, p0 = inv.transformPoint({ x: 0, y: 0 }), p1 = inv.transformPoint({ x: W, y: H });
  const x0 = Math.max(0, Math.floor(Math.min(p0.x, p1.x) * K)), y0 = Math.max(0, Math.floor(Math.min(p0.y, p1.y) * K)), x1 = Math.min(M.width, Math.ceil(Math.max(p0.x, p1.x) * K) + 1), y1 = Math.min(M.height, Math.ceil(Math.max(p0.y, p1.y) * K) + 1);
  if (x1 > x0 && y1 > y0) { g.save(); g.globalAlpha = 1; g.globalCompositeOperation = 'destination-out'; g.drawImage(M, x0, y0, x1 - x0, y1 - y0, x0 / K, y0 / K, (x1 - x0) / K, (y1 - y0) / K); g.restore(); }
  ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over'; ctx.drawImage(off, 0, 0); ctx.restore();
};
function easeOut(k) { return 1 - (1 - k) * (1 - k); }
// 0.91 (the characters pass behind trees and buildings, the hidden part showing through little by little; the
// same for the effects): the world's depth map (tools/assets/decormask087.py: per pixel, the foot line — the world y of the
// cell it stands on — of the standing object drawn there, and its cover) says which scenery stands in front of a point
// of the ground. The ground picture already holds the scenery: after the character (or an effect) is drawn, the
// pixels of the scenery in front of it are drawn again over it, from the map tiles, cut by that mask; they fade to
// see-through over 0.3 s while it stays behind (the faint copy of the character over everything still shows it).
function loadDepth(url, k) {
  return fetch(url).then(r => r.blob()).then(b => createImageBitmap(b, { premultiplyAlpha: 'none', colorSpaceConversion: 'none' })).then(im => {
    const c = document.createElement('canvas'); c.width = im.width; c.height = im.height; const g = c.getContext('2d', { willReadFrequently: true });
    g.drawImage(im, 0, 0); const d = g.getImageData(0, 0, im.width, im.height).data, n = im.width * im.height, foot = new Uint16Array(n), cov = new Uint8Array(n);
    for (let i = 0; i < n; i++) { foot[i] = d[i * 4] << 8 | d[i * 4 + 1]; cov[i] = d[i * 4 + 2]; }
    const w = im.width, h = im.height; if (im.close) im.close();   // (a closed bitmap reads 0 x 0)
    return { w, h, k, foot, cov };
  });
}
// the scenery in front of the foot line `fy` inside the world box: a small mask canvas (or null when nothing is in front)
// 0.95 (perf): the box is snapped outwards to FM_Q mask px and the foot line to 4 world units, and the masks (with the
// scenery already cut out of the tiles, decorFront) are kept in a small cache: a walking character or a playing effect
// finds its mask again most frames instead of rebuilding it pixel by pixel (it was ~1.5 ms a crowded frame on a slow CPU)
const FM_Q = 8, FM_MAX = 16;
Run.prototype.frontMask = function (x0, y0, x1, y1, fy) {
  const D = this.depth; if (!D) return null;
  const k = D.k, ix0 = Math.max(0, Math.floor(x0 * k / FM_Q) * FM_Q), iy0 = Math.max(0, Math.floor(y0 * k / FM_Q) * FM_Q), ix1 = Math.min(D.w, Math.ceil(x1 * k / FM_Q) * FM_Q), iy1 = Math.min(D.h, Math.ceil(y1 * k / FM_Q) * FM_Q);
  const w = ix1 - ix0, h = iy1 - iy0; if (w <= 0 || h <= 0) return null;
  const lim = Math.round(fy / 4) * 4 + 2, key = ix0 + ',' + iy0 + ',' + ix1 + ',' + iy1 + ',' + lim, C = this._fmCache || (this._fmCache = new Map());
  if (C.has(key)) { const v = C.get(key); C.delete(key); C.set(key, v); return v; }   // (most recently used last)
  let any = false;
  for (let y = iy0; y < iy1 && !any; y++) for (let i = y * D.w + ix0, e = y * D.w + ix1; i < e; i++) if (D.cov[i] > 24 && D.foot[i] > lim) { any = true; break; }
  let v = null;
  if (any) {
    const pool = this._fmPool || (this._fmPool = []), c = pool.pop() || document.createElement('canvas'); c.width = w; c.height = h;
    const g = c.getContext('2d'), id = g.createImageData(w, h), o = id.data;
    for (let y = iy0, j = 3; y < iy1; y++) for (let i = y * D.w + ix0, e = y * D.w + ix1; i < e; i++, j += 4) if (D.cov[i] > 24 && D.foot[i] > lim) o[j] = D.cov[i];
    g.putImageData(id, 0, 0);
    v = { c, w, h, x0: ix0 / k, y0: iy0 / k, x1: ix1 / k, y1: iy1 / k, front: null };
  }
  if (C.size >= FM_MAX) { const [k0, v0] = C.entries().next().value; C.delete(k0); if (v0) { (this._fmPool || (this._fmPool = [])).push(v0.c); if (v0.front) this._fmPool.push(v0.front); } }
  C.set(key, v); return v;
};
// draws the scenery in front of fy over what ctx (world transform) holds in the box, at `alpha`, only where sil(g) —
// the thing itself, drawn in world units on g — has pixels (the hidden part only); true when it did
Run.prototype.decorFront = function (ctx, x0, y0, x1, y1, fy, alpha, sil) {
  const M = this.frontMask(x0, y0, x1, y1, fy); if (!M) return false;
  const T = this.world.tile, res = this.world.res || 1, tr = ctx.getTransform(), s = Math.min(4, Math.hypot(tr.a, tr.b) || 1);
  const W = Math.max(1, Math.ceil((M.x1 - M.x0) * s)), H = Math.max(1, Math.ceil((M.y1 - M.y0) * s));
  // the scenery in front, cut out of the tiles by the mask: made once per mask and scale (0.95: kept with the mask)
  let F = M.front;
  if (!F || F.width !== W || F.height !== H || F._s !== s) {
    F = M.front = (F && F.width === W && F.height === H) ? F : ((this._fmPool && this._fmPool.pop()) || document.createElement('canvas')); F.width = W; F.height = H; F._s = s;
    const f = F.getContext('2d'); f.imageSmoothingEnabled = true; f.imageSmoothingQuality = 'medium';
    let got = false;
    for (let ty = Math.max(0, Math.floor(M.y0 / T)); ty * T < M.y1; ty++) for (let tx = Math.max(0, Math.floor(M.x0 / T)); tx * T < M.x1; tx++) {
      const im = this.tiles[tx + ',' + ty]; if (!im) continue; const r = res * (im._k || 1); got = true;
      const wx0 = Math.max(M.x0, tx * T), wy0 = Math.max(M.y0, ty * T), wx1 = Math.min(M.x1, (tx + 1) * T), wy1 = Math.min(M.y1, (ty + 1) * T); if (wx1 <= wx0 || wy1 <= wy0) continue;
      f.drawImage(im, (wx0 - tx * T) * r, (wy0 - ty * T) * r, (wx1 - wx0) * r, (wy1 - wy0) * r, (wx0 - M.x0) * s, (wy0 - M.y0) * s, (wx1 - wx0) * s, (wy1 - wy0) * s);
    }
    f.globalCompositeOperation = 'destination-in'; f.drawImage(M.c, 0, 0, M.w, M.h, 0, 0, W, H); f.globalCompositeOperation = 'source-over';
    if (!got) F._s = -1;   // (tiles not decoded yet: made again next time)
  }
  const c = this._fdC || (this._fdC = document.createElement('canvas')); if (c.width < W || c.height < H) { c.width = Math.max(c.width, W); c.height = Math.max(c.height, H); this._fdG = null; }
  const g = this._fdG || (this._fdG = c.getContext('2d')); g.setTransform(1, 0, 0, 1, 0, 0); g.globalCompositeOperation = 'source-over'; g.globalAlpha = 1; g.clearRect(0, 0, W, H);
  g.drawImage(F, 0, 0);
  if (sil) {
    const c2 = this._fsC || (this._fsC = document.createElement('canvas')); if (c2.width < W || c2.height < H) { c2.width = Math.max(c2.width, W); c2.height = Math.max(c2.height, H); this._fsG = null; }
    const g2 = this._fsG || (this._fsG = c2.getContext('2d')); g2.setTransform(1, 0, 0, 1, 0, 0); g2.globalAlpha = 1; g2.clearRect(0, 0, W, H);
    g2.setTransform(s, 0, 0, s, -M.x0 * s, -M.y0 * s); g2.imageSmoothingEnabled = true; sil(g2); g2.setTransform(1, 0, 0, 1, 0, 0);
    g.globalCompositeOperation = 'destination-in'; g.drawImage(c2, 0, 0, W, H, 0, 0, W, H); g.globalCompositeOperation = 'source-over';
  }
  ctx.save(); ctx.globalAlpha = alpha; ctx.drawImage(c, 0, 0, W, H, M.x0, M.y0, M.x1 - M.x0, M.y1 - M.y0); ctx.restore();
  return true;
};
// the character: its scenery in front, fading in 0.3 s from opaque to see-through while it stays behind
Run.prototype.occludePlayer = function (ctx) {
  const P = this.player, sc = (P._drawn && P._drawn.sc) || 1, now = this.time;
  const k = P._occK || 0, dt = Math.min(0.1, now - (P._occT || now)); P._occT = now;
  const D = P._drawn, sil = D ? g => P.sprite.draw(g, D.anim, D.t, P.x, P.y - P.leapH, ES * sc, D.flip, { loop: D.loop, moving: P.moving, at: this.time }) : null;
  const hit = !P.dead && !!sil && this.decorFront(ctx, P.x - 80 * sc, P.y - P.leapH - 250 * sc, P.x + 80 * sc, P.y + 16, P.y, 1 - 0.45 * k, sil);   // (0.91: a bit more hidden: 55 % of the scenery stays)
  P._occK = hit ? Math.min(1, k + dt / 0.3) : Math.max(0, k - dt / 0.2);
};
// 0.61: the death: the character's soul leaves the body once it has fallen — its pale silhouette (standing), in a cold
// glow, rising and swaying, fading away
function drawSoul(ctx, R, e) {
  const q = (e - 0.95) / 2.1; if (q <= 0 || q >= 1) return;
  const P = R.player, cs = P.sprite, sh = cs && cs.sheetFor('staticR'); if (!sh || !sh.img) return;
  const f = sh.anims.staticR.f[0], w = cs.getWhite(sh); if (!w) return;
  const a = Math.min(1, Math.sin(q * Math.PI) * 1.4) * 0.8, x = P.x + Math.sin(e * 2.6) * 7, y = P.y - 8 - q * 95, s = ES / sh.zoom, kw = w.k || 1;
  ctx.save(); ctx.globalAlpha = a; const gr = 58 + 10 * Math.sin(e * 5);
  ctx.drawImage(RCache.glow('rgba(170,210,255,0.9)'), x - gr, y - 50 - gr, gr * 2, gr * 2);
  ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha = a;
  ctx.translate(x, y); if (P.flip) ctx.scale(-1, 1);
  ctx.drawImage(w, f[0] * kw, f[1] * kw, f[2] * kw, f[3] * kw, -f[4] * s, -f[5] * s, f[2] * s, f[3] * s);
  ctx.restore();
}

// 0.65 (the Xelor's 'Horloge' clock dials → hourglasses in the style of the Sagesse orbs, a lighter violet, as his
// Sablier spell): a fading lilac trail along the orbit, a soft halo, the hourglass (RCache.hourglass, its sand running)
// that flips over with a little bounce every HG_T seconds, sand motes and sparkles turning round it
const HG_FR = 12, HG_T = 1.6;
function drawHourglassOrb(ctx, o, t, R) {
  const P = R.player, sp = o.spell.p, rr = sp.radius * R.stats.area, s = sp.size, dir = Math.sign(sp.rotSpeed || 1), pulse = 1 + 0.07 * Math.sin(t * 5 + o.a * 3);
  ctx.save();
  for (let i = 5; i >= 1; i--) {
    const a = ellAngle(o.a - i * 0.11 * dir), x = P.x + Math.cos(a) * rr, y = P.y - 20 + Math.sin(a) * rr * 0.6, k = 1 - i / 6, r = s * (0.45 + 0.55 * k);
    ctx.globalAlpha = 0.34 * k; ctx.drawImage(RCache.glow('rgba(196,150,255,0.9)'), x - r * 1.6, y - r * 1.6, r * 3.2, r * 3.2);
  }
  const g = s * 2.5 * pulse; ctx.globalAlpha = 0.7; ctx.drawImage(RCache.glow('rgba(205,165,255,0.85)'), o.x - g, o.y - g, g * 2, g * 2);
  // the run of its sand, then a flip: 0..1 over HG_T, each hourglass at its own phase
  const ph = (t / HG_T + o.a / TAU) % 1, run = Math.min(1, ph / 0.82), fl = Math.max(0, (ph - 0.82) / 0.18);
  const ease = fl < 1 ? 1 - Math.pow(1 - fl, 3) : 1, rot = Math.PI * ease + Math.sin(fl * Math.PI) * 0.18, bob = Math.sin(t * 3 + o.a) * s * 0.12;
  const c = RCache.hourglass(Math.min(HG_FR - 1, Math.floor(run * HG_FR))), h = s * 2.2 * pulse, w = h * c.width / c.height;
  ctx.globalAlpha = 1; ctx.translate(o.x, o.y + bob); ctx.rotate(rot + Math.sin(t * 1.7 + o.a) * 0.08); ctx.drawImage(c, -w / 2, -h / 2, w, h);
  ctx.restore(); ctx.save(); ctx.globalCompositeOperation = 'lighter';
  for (let i = 0; i < 4; i++) {   // sand motes and sparkles circling it
    const a = t * 3.6 + i * TAU / 4 + o.a, x = o.x + Math.cos(a) * s * 1.35, y = o.y + bob + Math.sin(a) * s * 0.55, w2 = 2.6 + Math.sin(t * 8 + i) * 1;
    ctx.globalAlpha = 0.8; ctx.drawImage(RCache.glow(i % 2 ? 'rgba(245,230,255,0.95)' : 'rgba(210,175,255,0.95)'), x - w2 * 2, y - w2 * 2, w2 * 4, w2 * 4);
  }
  if (fl > 0 && fl < 1) { const fr = s * (1.2 + fl * 1.6); ctx.globalAlpha = 0.6 * (1 - fl); ctx.drawImage(RCache.glow('rgba(235,215,255,0.9)'), o.x - fr, o.y - fr, fr * 2, fr * 2); }   // a flash as it flips
  ctx.restore();
}
// 0.61 (the Sagesse stars looked like icons): a violet aura orb — a fading trail along its orbit, a pulsing halo,
// the turning core (RCache.orb), little wisps circling it
function drawAuraOrb(ctx, o, t, R) {
  const P = R.player, sp = o.spell.p, rr = sp.radius * R.stats.area, s = sp.size, pulse = 1 + 0.08 * Math.sin(t * 6 + o.a * 3), dir = Math.sign(sp.rotSpeed || 1);
  ctx.save();   // (normal blending for the trail and halo: added light washed the violet out on bright grass)
  for (let i = 5; i >= 1; i--) {
    const a = ellAngle(o.a - i * 0.11 * dir), x = P.x + Math.cos(a) * rr, y = P.y - 20 + Math.sin(a) * rr * 0.6, k = 1 - i / 6, r = s * (0.45 + 0.55 * k);
    ctx.globalAlpha = 0.38 * k; ctx.drawImage(RCache.glow('rgba(140,60,235,0.9)'), x - r * 1.6, y - r * 1.6, r * 3.2, r * 3.2);
  }
  const g = s * 2.4 * pulse; ctx.globalAlpha = 0.75; ctx.drawImage(RCache.glow('rgba(150,60,240,0.8)'), o.x - g, o.y - g, g * 2, g * 2);
  ctx.globalAlpha = 1;
  const c = RCache.orb(), d = s * 1.2 * pulse; ctx.translate(o.x, o.y); ctx.rotate(t * 3.2 + o.a); ctx.drawImage(c, -d, -d, d * 2, d * 2);
  ctx.restore(); ctx.save(); ctx.globalCompositeOperation = 'lighter';
  for (let i = 0; i < 3; i++) {
    const a = t * 4.5 + i * TAU / 3 + o.a, x = o.x + Math.cos(a) * s * 1.4, y = o.y + Math.sin(a) * s * 0.6, w = 3.2 + Math.sin(t * 9 + i) * 1.2;
    ctx.globalAlpha = 0.85; ctx.drawImage(RCache.glow('rgba(235,210,255,0.95)'), x - w * 2, y - w * 2, w * 4, w * 4);
  }
  ctx.restore();
}
// 0.87 (livelier areas): the generic area — a soft breathing heart of light and three swirling arms turning
// slowly inside the runes (zoneRunes / zoneMotes do the rim and the element's motes)
function drawGlyph(ctx, x, y, r, color, a, t) {
  ctx.save(); ctx.translate(x, y); ctx.scale(1, 0.62);
  // (0.95: its halo from the cached glow picture — a gradient made every frame sent the ground effects to a 2D layer)
  const br = 0.85 + 0.15 * Math.sin(t * 3.2), gr = r * 0.75 * br; ctx.globalAlpha = a * 0.8; ctx.drawImage(RCache.glow(`rgba(${hexRgb(color)},0.4)`), -gr, -gr, gr * 2, gr * 2);
  ctx.rotate(-t * 0.9); ctx.lineCap = 'round';
  for (const [lw, st, al] of [[4, 'rgba(0,0,0,0.12)', 0.4], [2, color, 0.55]]) {   // (0.98: quieter lines, the dark one faint)
    ctx.lineWidth = lw; ctx.strokeStyle = st; ctx.globalAlpha = a * al;
    for (let i = 0; i < 3; i++) { ctx.beginPath(); for (let k = 0; k <= 12; k++) { const q = k / 12, an = i / 3 * TAU + q * 2.4, rr = r * (0.12 + 0.6 * q); k ? ctx.lineTo(Math.cos(an) * rr, Math.sin(an) * rr) : ctx.moveTo(Math.cos(an) * rr, Math.sin(an) * rr); } ctx.stroke(); }
  }
  ctx.restore();
}
function drawPickup(ctx, p, t) {
  const bob = Math.sin(t * 4 + p.x) * 2, R_ = Game.run;
  if (p.kind === 'gem') {
    // Ambre (small), Ambre Ancestrale (bigger, more xp), Ambre du Chêne Mou (rare: bosses and the strongest elites)
    // v2.0: 40% smaller on the ground (they used to cover it)
    const NA = R_ && R_.RUN.amber, ai = p.rare || (!NA && p.v >= 100) ? 2 : (p.anc || p.big || (!NA && p.v >= 12)) ? 1 : 0, as = ai === 2 ? (NA ? 48 : 12) : ai === 1 ? (p.anc ? 16.9 : p.big ? 20 : 19) : (!NA && p.v >= 5) ? 16 : 14;   // (0.82: ancestral 32 px = 20 % smaller than 0.81's 40, the Chêne Mou 3x it = 96 px; 0.92: the ancestral 15 % smaller, 27 px; 0.98: the Chêne Mou half, 48 px)
    const c = RCache.amber(ai, as);
    if (c && p.anc) ctx.drawImage(RCache.glow('rgba(255,170,50,0.55)'), p.x - 19, p.y + bob - c.h * 0.45 - 19, 38, 38);   // (0.98: the ancestral 27 -> 13.5 -> 16.9 px, a soft glow)
    if (c) {
      if (ai === 2) { const r = (19 + Math.sin(t * 5 + p.x) * 2) * as / 24; ctx.drawImage(RCache.glow('rgba(255,190,60,0.7)'), p.x - r, p.y + bob - c.h * 0.45 - r, r * 2, r * 2); }   // the rare one glows
      ctx.drawImage(c, p.x - c.w / 2, p.y + bob - c.h * 0.8, c.w, c.h); return;
    }
    const gi = p.v < 5 ? 0 : p.v < 15 ? 1 : p.v < 50 ? 2 : 3, s = p.big ? 13 : p.v >= 5 ? 9.5 : 7.5;
    const g = RCache.gem(gi, s); ctx.drawImage(g, p.x - g.ox, p.y + bob - g.oy, g.w, g.h);
    return;
  }
  const IC = Game.icons;
  const glow = (col, r) => { ctx.drawImage(RCache.glow(col), p.x - r, p.y - 8 - r, r * 2, r * 2); };
  switch (p.kind) {
    case 'kama': glow('rgba(255,215,0,0.35)', 16); IC.draw(ctx, 'KamaSymbol', p.x, p.y - 8 + bob, 0.72); break;
    // v1.7: ground objects a bit smaller (their pickup range is larger instead)
    // every object fitted in a box of a fixed size (world units; the character is ~62 tall), a bit smaller since v1.7
    case 'bread': { const B = (Game.C.breads || {})[p.v]; glow(B && B.hp < 0 ? 'rgba(255,200,60,0.8)' : 'rgba(255,220,150,0.55)', 22); IC.drawFit(ctx, B ? B.icon : 'it_33_7', p.x, p.y - 10 + bob, 34); } break;
    case 'rappel': glow('rgba(120,220,255,0.65)', 26); IC.drawFit(ctx, 'it_12_17', p.x, p.y - 14 + bob, 40); break;   // a real Potion de Rappel
    case 'gold': glow('rgba(255,215,60,0.75)', 26 + Math.sin(t * 6) * 3); IC.drawFit(ctx, 'it_39_22', p.x, p.y - 12 + bob, 36); break;   // Minerai d'Or
    case 'batofu': glow('rgba(150,220,255,0.75)', 28); IC.drawFit(ctx, 'it_53_120', p.x, p.y - 14 + bob, 40); break;
    case 'relic': { const r = Game.C.relics.find(r => r.id === p.v); glow('rgba(255,200,60,0.85)', 34 + Math.sin(t * 6) * 4); if (r) IC.drawFit(ctx, r.icon, p.x, p.y - 16 + bob, 44);
      for (let i = 0; i < 4; i++) { const a = t * 2.5 + i * TAU / 4; IC.draw(ctx, 'Star', p.x + Math.cos(a) * 30, p.y - 18 + Math.sin(a) * 10 + bob, 0.25); } } break;
    case 'plumec': glow('rgba(190,140,255,0.8)', 30); IC.drawFit(ctx, 'it_53_362', p.x, p.y - 14 + bob, 40); break;
    case 'fee': glow('rgba(255,120,220,0.75)', 28); IC.drawFit(ctx, 'it_74_30', p.x, p.y - 15 + bob, 46); break;
    case 'houx': glow('rgba(120,230,140,0.7)', 28); IC.drawFit(ctx, Game.C.houx.item, p.x, p.y - 15 + bob, 44); break;   // 0.97: the Bague Houx: one more reroll
    case 'sablier': glow('rgba(140,220,255,0.65)', 30); IC.drawFit(ctx, Game.C.sablierItem || 'sp_100', p.x, p.y - 16 + bob, 50); break;   // an hourglass: time stops
    case 'manuel': { glow('rgba(255,120,255,0.8)', 32 + Math.sin(t * 6) * 3); IC.drawFit(ctx, Game.C.manuel.icon, p.x, p.y - 16 + bob, 48); // the Manuel du Tailleur: sparkles
      for (let i = 0; i < 3; i++) { const a = t * 2.2 + i * TAU / 3; IC.draw(ctx, 'Star', p.x + Math.cos(a) * 28, p.y - 18 + Math.sin(a) * 10 + bob, 0.28); } } break;
    case 'kamaboost': { // the magic purse: a bag of kamas, spinning coins and a golden halo
      glow('rgba(255,215,0,0.8)', 34 + Math.sin(t * 7) * 3);
      IC.drawFit(ctx, Game.C.kamaBoost.icon, p.x, p.y - 16 + bob, 56);
      for (let i = 0; i < 6; i++) { const a = t * 3 + i * TAU / 6; IC.draw(ctx, 'KamaSymbol', p.x + Math.cos(a) * 34, p.y - 18 + Math.sin(a) * 11 + bob, 0.28); }
    } break;
    case 'power': { const d = Game.C.drops[p.v]; glow(d.color + 'bb', 32 + Math.sin(t * 6) * 3); // an object from the game (spell scrolls, the Arakne and Chaferfu items)
      if (d.item) IC.drawFit(ctx, d.item, p.x, p.y - 18 + bob, d.itemSize || 56); else ctx.drawImage(IC.canvas('sp_' + d.icon, 128), p.x - 20, p.y - 34 + bob, 40, 40); } break;
    case 'dofus': { const d = Game.C.dofus.find(d => d.id === p.v); glow(d ? d.color + 'cc' : '#fff', 34 + Math.sin(t * 5) * 4); if (d) IC.drawFit(ctx, 'dofus_hd_' + d.icon, p.x, p.y - 14 + bob, 38); } break;
    case 'tmap': glow('rgba(255,210,90,0.7)', 26 + Math.sin(t * 6) * 4); Game.icons.drawFit(ctx, Game.C.tmap.icon, p.x, p.y - 14 + bob, 40); break;
    case 'nowelgift': glow('rgba(255,90,90,0.75)', 48 + Math.sin(t * 5) * 6); glow('rgba(120,255,140,0.45)', 34); Game.icons.drawFit(ctx, 'gift_hd', p.x, p.y - 28 + bob, 80); break;   // (0.68: twice an item's size; 0.91: the client's gift at 512 px, build_iconhd091 gift)
    case 'trool': glow('rgba(255,220,120,0.8)', 32 + Math.sin(t * 6) * 4); Game.icons.drawFit(ctx, 'it_24_94', p.x, p.y - 16 + bob, 52); break;
    case 'gladia': glow('rgba(70,120,255,0.85)', 50 + Math.sin(t * 5) * 5); IC.drawFit(ctx, Game.C.gladia.icon, p.x, p.y - 26 + bob, 68); break;   // (0.98.3: twice a whole bread's 34)
    case 'booster': { // a TTG booster: one of the 20 packs (0.37: the: a client monster on each)
      glow('rgba(255,230,120,0.75)', 34 + Math.sin(t * 6) * 4); ctx.save(); ctx.translate(p.x, p.y - 26 + bob); ctx.rotate(Math.sin(t * 2) * 0.12);
      if (!boosterPack(ctx, p.pk || 0, -18, -29, 36)) { ctx.fillStyle = '#3fbf5a'; ctx.fillRect(-12, -16, 24, 32); }
      ctx.restore();
    } break;
    case 'chest': {   // a boss chest (p.boss) is bigger, in a red aura (and on the minimap)
      const sh = MobSheets.c[Game.C.chestSprite], B = p.boss;
      if (p.cine && R_ && R_.cine && R_.cine.data.p === p && sh) { // 0.26: its show — hops with a '!', chomps, then bursts
        const c = R_.cine, k = c.t; let y = p.y, sc = 2.4, anim = 'walkR', at = 0, sx = 1;
        if (k < 0.6) { const h = Math.abs(Math.sin(k * Math.PI * 5)); y -= h * 22; sx = 1 + (1 - h) * 0.15; sc = 2.4 + k * 0.8; }
        else if (k < 1.2) { anim = sh.anims.atkR ? 'atkR' : 'walkR'; at = k - 0.6; sc = 2.9 + Math.sin(k * 30) * 0.08; }
        else { sc = 2.9 * Math.max(0, 1 - (k - 1.2) / 0.3); }
        if (sc > 0.05) { const f = sh.frameAt(anim, at, true) || sh.anims.walkR.f[0]; ctx.save(); ctx.translate(p.x, y); ctx.scale(sx, 2 - sx); sh.draw(ctx, f, 0, 0, sc, false); ctx.restore(); }
        if (k < 0.9) { ctx.save(); ctx.font = 'bold 34px DofusBold, Verdana'; ctx.textAlign = 'center'; ctx.lineWidth = 5; ctx.strokeStyle = '#3a0000'; const by = y - 95 - Math.sin(k * 12) * 4; ctx.strokeText('!', p.x, by); ctx.fillStyle = '#ffdf3a'; ctx.fillText('!', p.x, by); ctx.restore(); }
        break;
      }
      if (B) { const r = 44 + Math.sin(t * 5) * 5; ctx.drawImage(RCache.glow('rgba(255,40,30,0.75)'), p.x - r, p.y - 14 - r, r * 2, r * 2); }
      else glow('rgba(255,215,80,0.6)', 26 + Math.sin(t * 6) * 3);
      if (sh && sh.anims.walkR) sh.draw(ctx, sh.anims.walkR.f[0], p.x, p.y, B ? 2.4 : 1.5, false);
      else { ctx.fillStyle = '#8b5a2b'; ctx.fillRect(p.x - 12, p.y - 18, 24, 16); ctx.fillStyle = '#ffd24a'; ctx.fillRect(p.x - 2, p.y - 14, 4, 6); }
    } break;
  }
}
// the Konami code: the run stops, the screen goes dark, every monster is a Tofu, and 'Tofu !' dances in the middle
function drawKonami(ctx, R, W, H) {
  const e = (performance.now() - (R.tofuShowAt || 0)) / 1000, out = Math.max(0, (R.tofuShowUntil - performance.now()) / 1000);
  const a = Math.min(1, e / 0.35, out / 0.4), u = Game.ui;
  ctx.save(); ctx.globalAlpha = a * 0.62; ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, H); ctx.globalAlpha = a;
  const txt = T('konami_tofu'), fs = Math.min(W / (txt.length * 0.62), 150 * u), cols = ['#ffe066', '#ff9a3c', '#ff6a8a', '#9cff6a', '#7fd8ff', '#c99bff'];
  ctx.font = `${fs}px DofusBold, Verdana, sans-serif`; const tw = ctx.measureText(txt).width; let x = (W - tw) / 2;
  const pop = Math.min(1, e / 0.5), sc = 0.4 + 0.6 * (1 - Math.pow(1 - pop, 3)) + (pop >= 1 ? 0.04 * Math.sin(e * 6) : 0);
  ctx.translate(W / 2, H / 2); ctx.scale(sc, sc); ctx.translate(-W / 2, -H / 2);
  [...txt].forEach((c, i) => {
    const cw = ctx.measureText(c).width, y = H / 2 + fs * 0.35 - Math.abs(Math.sin(e * 5 + i * 0.6)) * fs * 0.22;
    ctx.save(); ctx.translate(x + cw / 2, y); ctx.rotate(Math.sin(e * 4 + i) * 0.12);
    outlinedText(ctx, c, 0, 0, cols[i % cols.length], fs, 'center'); ctx.restore(); x += cw;
  });
  ctx.restore();
}
// 0.36: the Phoenix's revival, in the spirit of the old games' "you died… and you're back": the character falls, a
// swirl of orange powder gathers on it, a burst of light, then two phoenix wings of flame open on its back, beat a few
// times and crumble into embers. Particles are computed from their index (no state), times in seconds of real time
const REV_COLS = ['#fff3b0', '#ffd24a', '#ffa62a', '#ff7a1a', '#ff4a12'];
function rh(i, k) { const x = Math.sin(i * 127.1 + k * 311.7) * 43758.5453; return x - Math.floor(x); }
function drawPhoenixWing(ctx, x, y, side, open, flap, a, e) {
  // a bird's wing seen from behind: an arched arm (shoulder -> wrist -> tip), long flight feathers hanging from it
  // outwards (the longest at the tip), shorter brighter coverts on top, a dark-red rim so it reads on any ground
  ctx.save(); ctx.translate(x + side * 4, y); ctx.scale(side * 0.5 * (0.25 + 0.75 * open), 0.5 * (0.8 + 0.2 * open)); ctx.rotate(-0.3 * flap);
  const arm = u => { const v = 1 - u; return [2 * v * u * 40 + u * u * 92, 2 * v * u * -78 + u * u * -96]; };   // (raised in a V, close to the body)
  const feather = (u, len, w, ang, c0, c1, c2) => {
    const [px, py] = arm(u); ctx.save(); ctx.translate(px, py); ctx.rotate(ang + Math.sin(e * 10 + u * 9) * 0.04);
    const g = ctx.createLinearGradient(0, 0, 0, len); g.addColorStop(0, c0); g.addColorStop(0.55, c1); g.addColorStop(1, c2);
    ctx.fillStyle = g; ctx.beginPath(); ctx.moveTo(-w * 0.5, 0); ctx.quadraticCurveTo(-w * 0.75, len * 0.6, 0, len); ctx.quadraticCurveTo(w * 0.75, len * 0.6, w * 0.5, 0); ctx.closePath();
    ctx.fill(); ctx.strokeStyle = 'rgba(140,30,6,0.55)'; ctx.lineWidth = 1.4; ctx.stroke(); ctx.restore();
  };
  ctx.globalAlpha = a;
  for (let k = 11; k >= 0; k--) { const u = 0.12 + k * 0.08; feather(u, 30 + 62 * u * u, 13 + 5 * u, -0.25 - 0.85 * u + 0.12 * flap, 'rgba(255,214,90,0.95)', 'rgba(255,128,30,0.92)', 'rgba(205,40,10,0.85)'); }
  for (let k = 8; k >= 0; k--) { const u = 0.1 + k * 0.1; feather(u, 18 + 24 * u, 12, -0.1 - 0.7 * u, 'rgba(255,248,200,0.98)', 'rgba(255,200,70,0.95)', 'rgba(255,140,30,0.9)'); }
  ctx.strokeStyle = 'rgba(255,240,170,0.9)'; ctx.lineWidth = 4; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(0, 0); ctx.quadraticCurveTo(40, -78, 92, -96); ctx.stroke();
  ctx.restore();
}
function drawReviveBack(ctx, P, e) {   // behind the character: a warm glow and the wings
  if (e < 0.6 || e > 2.8) return;
  const open = easeOut(Math.min(1, (e - 0.6) / 0.35)), fade = Math.min(1, (2.8 - e) / 0.7), flap = Math.sin((e - 0.6) * 9) * open;
  ctx.save();
  const gl = 48 + 8 * Math.sin(e * 9); ctx.globalAlpha = 0.6 * fade; ctx.drawImage(RCache.glow('rgba(255,140,30,0.8)'), P.x - gl * 1.6, P.y - 70 - gl * 1.3, gl * 3.2, gl * 2.6);
  for (const side of [-1, 1]) drawPhoenixWing(ctx, P.x, P.y - 50, side, open, flap, fade, e);
  ctx.restore();
}
function drawReviveFront(ctx, P, e) {   // over the character: the powder, the burst, the embers
  const cx = P.x, cy = P.y - 34;
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  if (e < 0.6) {   // the powder spirals in
    const k = e / 0.6;
    for (let i = 0; i < 54; i++) {
      const a = rh(i, 1) * TAU + e * (5 + 4 * rh(i, 2)), r = (60 + 110 * rh(i, 3)) * (1 - k) * (1 - k) + 4;
      ctx.globalAlpha = Math.min(1, e / 0.15) * (0.6 + 0.4 * rh(i, 4)); ctx.fillStyle = REV_COLS[i % 5];
      const s = 2 + 3 * rh(i, 5); ctx.fillRect(cx + Math.cos(a) * r - s / 2, cy + Math.sin(a) * r * 0.65 - s / 2, s, s);
    }
    const g = 14 + 46 * k; ctx.globalAlpha = 0.5 + 0.4 * k; ctx.drawImage(RCache.glow('rgba(255,200,80,0.9)'), cx - g, cy - g, g * 2, g * 2);
  } else {
    const b = e - 0.6;
    if (b < 0.3) { ctx.globalAlpha = (0.3 - b) / 0.3; const g = 70 + 160 * b; ctx.drawImage(RCache.glow('rgba(255,250,210,1)'), cx - g, cy - g, g * 2, g * 2); }
    if (b < 0.55) {   // the shockwave
      const r = 30 + 170 * easeOut(b / 0.55); ctx.globalAlpha = 1 - b / 0.55; ctx.strokeStyle = '#ffb02a'; ctx.lineWidth = 7 * (1 - b / 0.55) + 2;
      ctx.beginPath(); ctx.ellipse(P.x, P.y, r, r * 0.55, 0, 0, TAU); ctx.stroke();
    }
    for (let i = 0; i < 80; i++) {   // embers: thrown out, then floating up and fading
      const life = 1.2 + 1.0 * rh(i, 6), tau = b - 0.4 * rh(i, 7) * (b > 0.9 ? 1 : 0); if (tau < 0 || tau > life) continue;
      const a = rh(i, 8) * TAU, v = 50 + 170 * rh(i, 9), d = v * tau * (1 - Math.min(1, tau / life) * 0.5);
      const x = cx + Math.cos(a) * d + Math.sin(tau * 6 + i) * 4, y = cy + Math.sin(a) * d * 0.55 - 55 * tau * tau;
      ctx.globalAlpha = (1 - tau / life) * (0.7 + 0.3 * Math.sin(e * 20 + i)); ctx.fillStyle = REV_COLS[i % 5];
      const s = 2 + 3.5 * rh(i, 10) * (1 - tau / life * 0.5); ctx.fillRect(x - s / 2, y - s / 2, s, s);
    }
  }
  ctx.restore();
}
// 0.98: the messages in the middle of the screen (monsters, bosses, events) in Lilita, rounder and easier to read; the
// titles, names and the victory keep the announcements' font. 0.98.1: they are names now (what they do goes in the chat,
// Run.announce), in the chat's lettering (hudFont)
const BAN_FONT = px => hudFont(Math.max(4, Math.round(px)));
// 0.95: the frame of the banners (and the relic's caption): x, y its top-left corner; t = a clock. 0.98.2 (green with leaves, it
// stood out from everything else): Dofus Retro's brown, the HUD's wood and gold: a dark rim, a body lit from the top, a gold
// bevel, a beige inner line, a stud at each corner, a gold diamond at each end; round it the magic of the menus' cursor
// (Nav.glide): two lights running along the edge, tiny sparks born on it and drifting out. Styles (PANEL): the banners; 'boss'
// redder, a bigger blurred shade, more sparks; 'relic' more sparks yet and two sprays out of its sides. fxK: the magic's opacity
// against the frame's (the relic's frame is see-through, not its sparks). The caller sets its opacity
const PANEL = {
  wood: { glow: 'rgba(90,225,225,0.8)', glowA: 0.22, body: ['#6e4e2a', '#452c14', '#28170a'], edge: ['#fff1b8', '#e2a53a', '#7a4210'], spark: 'rgba(90,235,235,0.95)', star: '70,230,235', run: 'rgba(215,255,250,0.95)', n: 20 },
  boss: { glow: 'rgba(255,190,90,0.85)', glowA: 0.4, blur: 'rgba(24,10,2,0.75)', body: ['#7c4a24', '#512a12', '#2e1408'], edge: ['#fff6cc', '#f5b52e', '#8a4a10'], spark: 'rgba(255,205,110,0.95)', star: '255,190,80', run: 'rgba(255,245,205,0.95)', n: 34 },
  relic: { glow: 'rgba(90,225,225,0.85)', glowA: 0.4, blur: 'rgba(24,10,2,0.55)', body: ['#6e4e2a', '#452c14', '#28170a'], edge: ['#fffbe0', '#f5c542', '#7a4210'], spark: 'rgba(90,235,235,0.95)', star: '70,230,235', run: 'rgba(215,255,250,0.95)', n: 30, sides: 30, fxK: 1.6 },
};
const panelHash = x => { const v = Math.sin(x * 127.1 + 311.7) * 43758.5453; return v - Math.floor(v); };
// a spark: a white four-pointed star in a soft halo of its colour ('r,g,b'), made once (a round glow turned to a muddy disc on bright ground)
function panelStar(rgb) {
  const key = 'star' + rgb; let c = RCache.m.get(key); if (c) return c; const S = 48; c = document.createElement('canvas'); c.width = c.height = S; const g = c.getContext('2d'); g.translate(S / 2, S / 2);
  const gl = g.createRadialGradient(0, 0, 0, 0, 0, S / 2); gl.addColorStop(0, `rgba(${rgb},0.9)`); gl.addColorStop(0.32, `rgba(${rgb},0.34)`); gl.addColorStop(1, `rgba(${rgb},0)`); g.fillStyle = gl; g.fillRect(-S / 2, -S / 2, S, S);
  g.fillStyle = '#ffffff'; g.beginPath(); for (let i = 0; i < 8; i++) { const r = i % 2 ? 2.8 : S * 0.44, an = i / 8 * TAU; g.lineTo(Math.cos(an) * r, Math.sin(an) * r); } g.closePath(); g.fill();
  return RCache.put(key, c);
}
function annPanel(ctx, px, py, tw, ph, u, t = 0, style) {
  const S = PANEL[style] || PANEL.wood, cx = px + tw / 2, cy = py + ph / 2, a0 = ctx.globalAlpha, fa = Math.min(1, a0 * (S.fxK || 1));
  ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha = a0 * (S.glowA + 0.08 * Math.sin(t * 2.2)); ctx.drawImage(RCache.glow(S.glow), px - 30 * u, py - 26 * u, tw + 60 * u, ph + 52 * u); ctx.restore();
  if (S.blur) { ctx.save(); ctx.shadowColor = S.blur; ctx.shadowBlur = (30 + 6 * Math.sin(t * 3)) * u; ctx.fillStyle = S.blur; ctx.beginPath(); ctx.roundRect(px - 6 * u, py - 5 * u, tw + 12 * u, ph + 10 * u, 14 * u); ctx.fill(); ctx.fill(); ctx.fill(); ctx.restore(); }   // (a blurred shade round it, under the body: it stands out on any ground)
  ctx.beginPath(); ctx.roundRect(px - 2 * u, py - 2 * u, tw + 4 * u, ph + 4 * u, 8.5 * u); ctx.fillStyle = '#1c0d03'; ctx.fill();   // (the dark rim)
  const gr = ctx.createLinearGradient(0, py, 0, py + ph); gr.addColorStop(0, S.body[0]); gr.addColorStop(0.45, S.body[1]); gr.addColorStop(1, S.body[2]);
  const gd = ctx.createLinearGradient(0, py, 0, py + ph); gd.addColorStop(0, S.edge[0]); gd.addColorStop(0.5, S.edge[1]); gd.addColorStop(1, S.edge[2]);
  ctx.beginPath(); ctx.roundRect(px, py, tw, ph, 7 * u); ctx.fillStyle = gr; ctx.fill(); ctx.strokeStyle = gd; ctx.lineWidth = 2 * u; ctx.stroke();
  ctx.strokeStyle = 'rgba(255,225,160,0.24)'; ctx.lineWidth = 1 * u; ctx.beginPath(); ctx.roundRect(px + 4 * u, py + 4 * u, tw - 8 * u, ph - 8 * u, 4 * u); ctx.stroke();
  ctx.fillStyle = 'rgba(255,240,205,0.07)'; ctx.beginPath(); ctx.roundRect(px + 3 * u, py + 3 * u, tw - 6 * u, ph * 0.36, 5 * u); ctx.fill();   // (the light on its top)
  for (const [x, y] of [[px + 7 * u, py + 7 * u], [px + tw - 7 * u, py + 7 * u], [px + 7 * u, py + ph - 7 * u], [px + tw - 7 * u, py + ph - 7 * u]]) { ctx.fillStyle = '#1c0d03'; ctx.beginPath(); ctx.arc(x, y, 2 * u, 0, TAU); ctx.fill(); ctx.fillStyle = '#ffd56a'; ctx.beginPath(); ctx.arc(x, y, 1.2 * u, 0, TAU); ctx.fill(); }   // (studs)
  if (!Game.minFx) {
    // two lights running along the edge, one stroke with a long dash (0.98.3: under the gold diamonds)
    const per = 2 * (tw + ph) - 8 * u, dash = Math.min(per * 0.12, 90 * u); ctx.save(); ctx.beginPath(); ctx.roundRect(px, py, tw, ph, 7 * u); ctx.setLineDash([dash, per / 2 - dash]); ctx.lineDashOffset = -t * 110 * u; ctx.lineCap = 'round';
    ctx.globalAlpha = fa * 0.3; ctx.strokeStyle = S.spark; ctx.lineWidth = 5 * u; ctx.stroke(); ctx.globalAlpha = fa * 0.9; ctx.strokeStyle = S.run; ctx.lineWidth = 2 * u; ctx.stroke(); ctx.restore();
  }
  for (const sd of [-1, 1]) {   // a gold diamond at each end
    const r = Math.min(7 * u, ph * 0.2); ctx.save(); ctx.translate(cx + sd * tw / 2, cy); ctx.rotate(Math.PI / 4); ctx.fillStyle = '#1c0d03'; ctx.fillRect(-r - 1.6 * u, -r - 1.6 * u, (r + 1.6 * u) * 2, (r + 1.6 * u) * 2);
    const dg = ctx.createLinearGradient(-r, -r, r, r); dg.addColorStop(0, S.edge[0]); dg.addColorStop(0.5, S.edge[1]); dg.addColorStop(1, S.edge[2]); ctx.fillStyle = dg; ctx.fillRect(-r, -r, r * 2, r * 2); ctx.restore();
  }
  if (!Game.minFx) {
    // sparks, as #navglide's: born on the edge, growing, drifting out, gone; each born somewhere else every time
    const gl = panelStar(S.star), gg = panelStar('255,205,90'), n = Game.lowFx ? S.n >> 1 : S.n, TT = 1.6;
    const spark = (x, y, q, r0, g) => { const k = q < 0.2 ? 0.4 + 4.5 * q : 1.3 - (q - 0.2) * 1.25, r = r0 * k * u * 3.2; ctx.globalAlpha = fa * (q < 0.2 ? q * 5 : q > 0.6 ? (1 - q) * 2.5 : 1); ctx.drawImage(g, x - r, y - r, r * 2, r * 2); };
    ctx.save();
    for (let i = 0; i < n; i++) {
      const cyc = t / TT + i * 0.381966, c0 = Math.floor(cyc), q = cyc - c0, h0 = panelHash(i * 13 + c0), h1 = panelHash(i * 7 + c0 * 3), s0 = h0 * 2 * (tw + ph), d = (5 + 12 * h1) * u * q;
      let x, y;
      if (s0 < tw) { x = px + s0; y = py - d; } else if (s0 < tw + ph) { x = px + tw + d; y = py + s0 - tw; } else if (s0 < 2 * tw + ph) { x = px + s0 - tw - ph; y = py + ph + d; } else { x = px - d; y = py + s0 - 2 * tw - ph; }
      spark(x, y - 4 * u * q, q, i % 3 ? 2 : 1.5, i % 4 ? gl : gg);
    }
    // the relics: a spray out of each side
    if (S.sides) for (const sd of [-1, 1]) for (let i = 0, m = Game.lowFx ? S.sides >> 1 : S.sides; i < m; i++) {
      const T2 = 1.1 + 0.5 * panelHash(i + 40), cyc = t / T2 + i * 0.618034 + (sd > 0 ? 0.37 : 0), c0 = Math.floor(cyc), q = cyc - c0, h0 = panelHash(i * 11 + c0 + sd), h1 = panelHash(i * 5 + c0 * 7 + sd);
      spark(cx + sd * (tw / 2 + (6 + 62 * h1) * u * Math.sqrt(q)), py + ph * h0 - (10 + 26 * h1) * u * q, q, 1.4 + 1.4 * h0, i % 3 ? gg : gl);
    }
    ctx.restore();
  }
  ctx.globalAlpha = a0;
}
// 0.95: the XP bar's frame (drawHud), made once per size: a bronze body with a gold bevel, a dark track, the level's plate
// at the left (pw wide, standing out 2 u above and below) with two rivets, its right end round (0.98.3: was a gold diamond). Drawn m px out
const _xpF = new Map();
function xpFrame(wb, hb, pw, u) {
  const key = Math.round(wb) + '|' + Math.round(hb) + '|' + pw + '|' + u.toFixed(3); let c = _xpF.get(key); if (c) return c;
  if (_xpF.size > 6) _xpF.clear();
  const m = Math.ceil(4 * u); c = document.createElement('canvas'); c.width = Math.ceil(wb + 2 * m); c.height = Math.ceil(hb + 2 * m); c.m = m;
  const g = c.getContext('2d'); g.translate(m, m);
  const gold = (y0, y1) => { const gr = g.createLinearGradient(0, y0, 0, y1); gr.addColorStop(0, '#fff1b8'); gr.addColorStop(0.45, '#e2a53a'); gr.addColorStop(1, '#7a4210'); return gr; };
  const rr = (x, y, w, h, r) => { g.beginPath(); g.roundRect(x, y, w, h, r); };
  rr(0, 0, wb, hb, [hb * 0.32, hb / 2, hb / 2, hb * 0.32]); g.fillStyle = '#1c0d03'; g.fill();   // the body
  rr(1.1 * u, 1.1 * u, wb - 2.2 * u, hb - 2.2 * u, [hb * 0.26, hb / 2 - 1.1 * u, hb / 2 - 1.1 * u, hb * 0.26]); g.strokeStyle = gold(0, hb); g.lineWidth = 1.5 * u; g.stroke();   // its gold bevel
  const tx = pw + 2 * u, tw = wb - pw - 5 * u, ty = 3 * u, th = hb - 6 * u;   // the track
  const wl = g.createLinearGradient(0, ty, 0, ty + th); wl.addColorStop(0, '#080401'); wl.addColorStop(1, '#2a1708'); rr(tx, ty, tw, th, [0, th / 2, th / 2, 0]); g.fillStyle = wl; g.fill();
  // the level's plate
  rr(0, -2 * u, pw, hb + 4 * u, 4 * u); const pl = g.createLinearGradient(0, -2 * u, 0, hb + 2 * u); pl.addColorStop(0, '#6a4a26'); pl.addColorStop(0.55, '#3a2410'); pl.addColorStop(1, '#22140a');
  g.fillStyle = pl; g.fill(); g.strokeStyle = '#1c0d03'; g.lineWidth = 2.6 * u; g.stroke(); g.strokeStyle = gold(-2 * u, hb + 2 * u); g.lineWidth = 1.3 * u; g.stroke();
  rr(2.4 * u, -0.4 * u, pw - 4.8 * u, hb + 0.8 * u, 2.6 * u); g.strokeStyle = 'rgba(255,225,160,0.22)'; g.lineWidth = 0.8 * u; g.stroke();
  for (const x of [3.6 * u, pw - 3.6 * u]) { g.fillStyle = '#1c0d03'; g.beginPath(); g.arc(x, hb / 2, 1.9 * u, 0, TAU); g.fill(); g.fillStyle = '#ffd56a'; g.beginPath(); g.arc(x, hb / 2, 1.2 * u, 0, TAU); g.fill(); }   // rivets
  _xpF.set(key, c); return c;
}
// its amber fill (the ambers' colour, the countdown's gold): a vertical gradient with a light top edge, th px high
const _xpFill = new Map();
function xpFill(th) {
  const h = Math.max(2, Math.round(th)); let c = _xpFill.get(h); if (c) return c;
  c = document.createElement('canvas'); c.width = 4; c.height = h; const g = c.getContext('2d');
  const gr = g.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, '#fff4c0'); gr.addColorStop(0.32, '#ffd04a'); gr.addColorStop(0.7, '#f0961e'); gr.addColorStop(1, '#a8500a');
  g.fillStyle = gr; g.fillRect(0, 0, 4, h); g.fillStyle = 'rgba(255,252,230,0.75)'; g.fillRect(0, 0, 4, Math.max(1, Math.round(h * 0.14)));
  _xpFill.set(h, c); return c;
}
// 0.98.3: a boss's bar at the top of the screen, of the XP bar's family: the same bronze and gold round a dark track, made
// once per size (m px out); `bossFill`, its colour (a vertical gradient, a light top edge). The track is bh high at by
const _bbF = new Map();
function bossFrame(bw, bh, u) {
  const key = Math.round(bw) + '|' + Math.round(bh); let c = _bbF.get(key); if (c) return c;
  if (_bbF.size > 8) _bbF.clear();
  const m = Math.ceil(5 * u), e = 3 * u; c = document.createElement('canvas'); c.width = Math.ceil(bw + 2 * m); c.height = Math.ceil(bh + 2 * m); c.m = m;
  const g = c.getContext('2d'); g.translate(m, m);
  const rr = (x, y, w, h, r) => { g.beginPath(); g.roundRect(x, y, w, h, r); };
  const gold = g.createLinearGradient(0, -e, 0, bh + e); gold.addColorStop(0, '#fff1b8'); gold.addColorStop(0.45, '#e2a53a'); gold.addColorStop(1, '#7a4210');
  rr(-e, -e, bw + 2 * e, bh + 2 * e, bh / 2 + e); g.fillStyle = '#1c0d03'; g.fill();   // the body
  rr(-e + 1.1 * u, -e + 1.1 * u, bw + 2 * e - 2.2 * u, bh + 2 * e - 2.2 * u, bh / 2 + e - 1.1 * u); g.strokeStyle = gold; g.lineWidth = 1.5 * u; g.stroke();   // its gold bevel
  const wl = g.createLinearGradient(0, 0, 0, bh); wl.addColorStop(0, '#080401'); wl.addColorStop(1, '#2a1708'); rr(0, 0, bw, bh, bh / 2); g.fillStyle = wl; g.fill();   // the track
  _bbF.set(key, c); return c;
}
const _bbFill = new Map();
function bossFill(th, sub) {
  const h = Math.max(2, Math.round(th)), key = h * 2 + (sub ? 1 : 0); let c = _bbFill.get(key); if (c) return c;
  c = document.createElement('canvas'); c.width = 4; c.height = h; const g = c.getContext('2d');
  const gr = g.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, sub ? '#84e658' : '#ff6b5a'); gr.addColorStop(1, sub ? '#277a0e' : '#a8160c');
  g.fillStyle = gr; g.fillRect(0, 0, 4, h); g.fillStyle = 'rgba(255,255,255,0.32)'; g.fillRect(0, 0, 4, Math.max(1, Math.round(h * 0.14)));
  _bbFill.set(key, c); return c;
}
// the bar: its frame, the life just lost melting away in a lighter band, the colour, a light sweeping across, a few embers
// rising inside it (placed from the time alone: nothing to keep), quarter marks, a glow at the tip
function drawBossHud(ctx, b, bx, by, bw, bh, u, t) {
  const F = bossFrame(bw, bh, u), k = clamp(b.hp / b.maxHp, 0, 1), sub = !b.boss, fw = bw * k;
  b._hudLag = b._hudLag === undefined || b._hudLag < k ? k : b._hudLag + (k - b._hudLag) * 0.06;
  ctx.drawImage(F, bx - F.m, by - F.m);
  ctx.save(); ctx.beginPath(); ctx.roundRect(bx, by, bw, bh, bh / 2); ctx.clip();
  if (b._hudLag > k) { ctx.fillStyle = sub ? 'rgba(214,255,180,0.6)' : 'rgba(255,208,160,0.7)'; ctx.fillRect(bx + fw - 1, by, bw * (b._hudLag - k) + 1, bh); }
  if (fw > 0.5) {
    ctx.drawImage(bossFill(bh, sub), bx, by, fw, bh);
    const sx = (t * 0.45 % 1.5) - 0.25, sw = 26 * u;
    if (sx > -0.1 && sx < 1.1) { const g = ctx.createLinearGradient(bx + fw * sx - sw, 0, bx + fw * sx + sw, 0); g.addColorStop(0, 'rgba(255,255,255,0)'); g.addColorStop(0.5, 'rgba(255,255,255,0.3)'); g.addColorStop(1, 'rgba(255,255,255,0)'); ctx.fillStyle = g; ctx.fillRect(bx, by, fw, bh); }
    ctx.globalCompositeOperation = 'lighter'; const em = RCache.glow(sub ? 'rgba(210,255,170,0.95)' : 'rgba(255,200,130,0.95)'), sz = 5.5 * u;
    for (let i = 0; i < 7; i++) { const p = (t * (0.32 + 0.09 * (i % 3)) + i * 0.29) % 1; ctx.globalAlpha = 0.75 * Math.sin(p * Math.PI); ctx.drawImage(em, bx + fw * ((i * 0.618 + t * 0.012 * (1 + i % 3)) % 1) - sz / 2, by + bh * (1 - p) - sz / 2, sz, sz); }
    ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
  }
  ctx.fillStyle = 'rgba(30,10,4,0.32)'; for (let i = 1; i < 4; i++) ctx.fillRect(Math.round(bx + bw * i / 4), by, Math.max(1, u * 0.8), bh);
  ctx.restore();
  if (fw > bh && k < 1) { ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha = 0.5; ctx.drawImage(RCache.glow(sub ? 'rgba(170,255,120,0.9)' : 'rgba(255,150,100,0.9)'), bx + fw - bh, by - bh * 0.5, bh * 2, bh * 2); ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over'; }
}
// the capitals' height of the HUD font at px (outlinedText / TextCache write on the baseline)
function hudCap(px) { const g = annInk.g || (annInk.g = document.createElement('canvas').getContext('2d')); g.font = hudFont(100); g.textBaseline = 'alphabetic'; return g.measureText('H').actualBoundingBoxAscent / 100 * px; }
function wrapLines(ctx, text, maxW) {
  const out = []; let cur = '';
  for (const w of String(text).split(' ')) { const t = cur ? cur + ' ' + w : w; if (cur && ctx.measureText(t).width > maxW) { out.push(cur); cur = w; } else cur = t; }
  if (cur) out.push(cur); return out;
}
// 0.48: life drain. The monster: a blood-red glow and short streaks torn out of it; the character: a red aura, a
// transparent red cloud and streaks sucked into it; between them, red streaks flying from the monster to the character
function drainLine(ctx, x0, y0, x1, y1, w, col = '#ff3a5a', rc = '#5a0010', rw = w + 1.25) {   // a streak: dark rim, bright core
  // (0.95: a stretched picture, RCache.streak — PixiJS lays it as a quad; it was a 2D box per drained monster)
  const c = RCache.streak(col, w, rc, rw), len = Math.hypot(x1 - x0, y1 - y0), sx = len / STREAK_L, p = c.p; if (len < 0.01) return;
  ctx.save(); ctx.translate(x0, y0); ctx.rotate(Math.atan2(y1 - y0, x1 - x0)); ctx.drawImage(c, -p * sx, -p, (STREAK_L + 2 * p) * sx, 2 * p); ctx.restore();
}
function edgeRect(ctx, x, y, w, h, lw) { const f = ctx.fillStyle; ctx.fillStyle = ctx.strokeStyle; ctx.fillRect(x - lw / 2, y - lw / 2, w + lw, lw); ctx.fillRect(x - lw / 2, y + h - lw / 2, w + lw, lw); ctx.fillRect(x - lw / 2, y + lw / 2, lw, h - lw); ctx.fillRect(x + w - lw / 2, y + lw / 2, lw, h - lw); ctx.fillStyle = f; }   // (0.95: strokeRect as four rectangles)
function ringAt(ctx, col, x, y, rx, ry, lw) { const c = RCache.ring(col, rx, ry, lw), p = c.p; ctx.drawImage(c, x - rx - p, y - ry - p, (rx + p) * 2, (ry + p) * 2); }   // (0.95: an ellipse's outline as a picture)
function drawDrainMob(ctx, m, t, ly, sc) {
  const k = 1 - (t - m.drainT) / 0.5, R0 = m.r * 1.6 * sc + 8, cy = ly - m.r * 1.5 * sc; ctx.save();
  ctx.globalAlpha = 0.6 * k; ctx.drawImage(RCache.glow('rgba(255,0,40,0.95)'), m.x - R0 * 1.3, cy - R0 * 1.3, R0 * 2.6, R0 * 2.6);
  ctx.globalAlpha = 0.9 * k; ringAt(ctx, '#ff2040', m.x, m.y, m.r * 1.3 * sc + 4, (m.r * 1.3 * sc + 4) * 0.42, 2.5);
  for (let i = 0; i < 6; i++) { const a = i * TAU / 6 + m.x * 0.01, q = (1 - k), r1 = R0 * (0.35 + q * 0.9), r2 = r1 + R0 * 0.35;
    drainLine(ctx, m.x + Math.cos(a) * r1, cy + Math.sin(a) * r1 * 0.75, m.x + Math.cos(a) * r2, cy + Math.sin(a) * r2 * 0.75, 1); }
  ctx.restore();
}
function drawDrainPlayer(ctx, P, t, front) {
  const k = 1 - (t - P.drainT) / 0.6, cy = P.y - 40; ctx.save();
  if (!front) {   // behind: the aura, the red and dark pink smoke (0.50: more visible), a ring at the feet
    ctx.globalAlpha = 0.5 * k; ctx.drawImage(RCache.glow('rgba(255,0,50,0.95)'), P.x - 58, cy - 66, 116, 116);
    for (let i = 0; i < 6; i++) { const ph = t * 1.3 + i * 1.05, x = P.x + Math.cos(ph) * 20, y = cy + 4 + Math.sin(ph * 1.2) * 18, r = 26 + 7 * Math.sin(ph * 2);
      ctx.globalAlpha = 0.48 * k; ctx.drawImage(RCache.glow(i % 2 ? 'rgba(170,20,100,0.95)' : 'rgba(230,20,40,0.95)'), x - r, y - r, r * 2, r * 2); }
    ctx.globalAlpha = 0.85 * k; ringAt(ctx, '#ff2040', P.x, P.y, 30, 12, 3);
  } else {        // in front: faint streaks drawn into the character, little red drops falling onto it
    ctx.globalAlpha = 0.4 * k;
    for (let i = 0; i < 7; i++) { const a = i * TAU / 7 + Math.floor(t * 8) * 0.7, q = ((t * 3 + i / 7) % 1), r1 = 48 - q * 30, r2 = r1 + 13;
      drainLine(ctx, P.x + Math.cos(a) * r1, cy + Math.sin(a) * r1 * 0.9, P.x + Math.cos(a) * r2, cy + Math.sin(a) * r2 * 0.9, 1); }
    ctx.fillStyle = '#e8102e';
    for (let i = 0; i < 9; i++) { const q = (t * 1.7 + i * 0.37) % 1, x = P.x + Math.sin(i * 2.7) * 22, y = cy - 62 + q * 70;
      ctx.globalAlpha = k * Math.min(1, (1 - q) * 3) * 0.9; ctx.beginPath(); ctx.ellipse(x, y, 1.6, 2.4, 0, 0, TAU); ctx.fill(); }
  }
  ctx.restore();
}
function drawDrains(ctx, R, t) {
  const P = R.player, px = P.x, py = P.y - 40; ctx.save();
  for (const d of R.drains) {
    const m = d.m, sc = m.scale || 1, x0 = m.x, y0 = m.y - (m.liftH || 0) - m.r * 1.5 * sc, k = (t - d.t0) / 0.5; if (k < 0 || k > 1) continue;
    const cx = (x0 + px) / 2 + (py - y0) * 0.25 * d.seed, cy = (y0 + py) / 2 - 30 - (px - x0) * 0.25 * d.seed;   // a little arc
    const at = (u) => { const v = 1 - u; return [v * v * x0 + 2 * v * u * cx + u * u * px, v * v * y0 + 2 * v * u * cy + u * u * py]; };
    // 0.50: one short, see-through streak sucked along the arc, dark pink smoke whirling around its head
    const u1 = clamp(k * 1.15, 0, 1), u0 = clamp(u1 - 0.11, 0, 1); if (u1 <= 0 || u0 >= 1) continue;
    const [hx, hy] = at(u1), fade = 1 - k * 0.5;
    for (let i = 0; i < 3; i++) { const a = t * 11 + i * 2.1 + d.seed * 3, r = 9 + 2 * Math.sin(t * 7 + i);
      ctx.globalAlpha = 0.42 * fade; ctx.drawImage(RCache.glow('rgba(170,20,100,0.95)'), hx + Math.cos(a) * r - 9, hy + Math.sin(a) * r * 0.8 - 9, 18, 18); }
    ctx.globalAlpha = 0.5 * fade;
    for (let s = 0; s < 4; s++) { const [x0, y0] = at(u0 + (u1 - u0) * s / 4), [x1, y1] = at(u0 + (u1 - u0) * (s + 1) / 4); drainLine(ctx, x0, y0, x1, y1, 1.2, '#ff4a66', '#5a0010', 2.2); }   // (0.95: four streak pictures)
    ctx.globalAlpha = 0.6 * fade; ctx.fillStyle = '#ffd0d8'; ctx.beginPath(); ctx.arc(hx, hy, 1.4, 0, TAU); ctx.fill();
  }
  ctx.restore();
}
function drawShiny(ctx, m, sh, f, ly, sc, flip, a, t) {
  // a pale shimmer passing over the monster, and little four-point stars twinkling around it (one after the other)
  if (sh.white) { ctx.globalAlpha = a * (0.1 + 0.16 * Math.max(0, Math.sin(t * 3.2 + m.x * 0.01))); sh.draw(ctx, f, m.x, ly, sc, flip, sh.white); }
  const R = m.r * sc;
  for (let i = 0; i < 4; i++) {
    const q = t * 1.1 + i / 4, ph = q % 1, k = Math.floor(q) * 2.7 + i * 1.9;
    const x = m.x + Math.cos(k) * R * 1.3, y = ly - R * 1.7 + Math.sin(k * 1.3) * R * 1.3, s = (4 + 5 * Math.sin(ph * Math.PI)) * Math.max(1, sc * 0.8);
    ctx.globalAlpha = a * Math.sin(ph * Math.PI); ctx.drawImage(RCache.glow('rgba(255,236,150,0.9)'), x - s * 1.6, y - s * 1.6, s * 3.2, s * 3.2);
    ctx.fillStyle = '#fffbe6'; ctx.beginPath();
    for (let j = 0; j < 8; j++) { const an = j * Math.PI / 4 + t * 1.5, rr = j % 2 ? s * 0.22 : s; j ? ctx.lineTo(x + Math.cos(an) * rr, y + Math.sin(an) * rr) : ctx.moveTo(x + Math.cos(an) * rr, y + Math.sin(an) * rr); }
    ctx.closePath(); ctx.fill();
  }
  ctx.globalAlpha = a;
}
// 0.61: what a monster shows this frame (sheet, frame, mirror, opacity, height), shared by drawMob and the PixiJS
// drawing (pixi_render.js); one object reused, read at once
const _mp = {};
function mobPose(m, t, frozen) {
  const sh = m.sh; if (!sh) return null;
  const sc = m.scale || 1;
  let anim, at, loop;
  if (m.dying) { anim = 'dieR'; at = m.dieT; loop = false; if (!sh.has('dieR') || m.fastDie) { anim = 'walkR'; at = 0; } }
  else if (m.atkAnimT !== undefined && sh.has('atkR') && m.atkAnimT < sh.duration('atkR')) { anim = 'atkR'; at = m.atkAnimT; loop = false; }   // (0.59: m.atkAnimT advances in updateMobs)
  else { anim = m.view === 'L' && sh.has('walkL') ? 'walkL' : 'walkR'; at = frozen || m.stunUntil > t ? 0 : (m.wt !== undefined ? m.wt : m.t); loop = true; }   // (0.36: walks always loop — sheets from build_mobs20 have no loop flag: the Tofuzmo slid)
  // 0.60: the humanoid bosses walk at 60 fps (their own small sheet from the up-to-date client, build_move060)
  const s6 = anim.startsWith('walk') && m.def.walk60 ? MobSheets.c[m.def.walk60] : null, shD = s6 && s6.img && s6.has(anim) ? s6 : sh;
  const f = shD.frameAt(anim, at, loop); if (!f) return null;
  const flip = m.dying ? false : (anim.endsWith('L') ? !m.flip : m.flip); // L views natively face up-left
  let a = m.alpha !== undefined ? m.alpha : 1;
  if (m.dying) { const dd = m.fastDie ? 0.05 : Math.min(sh.duration('dieR') || 0.5, m.boss ? 4 : 1.3); a *= clamp(1 - (m.dieT - dd) / 0.25, 0, 1); }
  _mp.sh = sh; _mp.shD = shD; _mp.f = f; _mp.flip = flip; _mp.a = a; _mp.ly = m.y - (m.liftH || 0); _mp.sc = sc; _mp.anim = anim;
  return _mp;
}
function drawMob(ctx, m, t, frozen) {
  const q = mobPose(m, t, frozen); if (!q) return;
  const { sh, shD, f, flip, a, ly, sc, anim } = q;
  if (!m.dying && (m.elite || m.confuseUntil > t)) { const r = m.r * 2.6 * sc; ctx.globalAlpha = a * 0.8; ctx.drawImage(RCache.glow(m.elite ? 'rgba(255,210,74,0.75)' : m.poisonUntil > t ? 'rgba(120,230,80,0.6)' : 'rgba(156,255,106,0.6)'), m.x - r, ly - m.r * 1.6 * sc - r, r * 2, r * 2); }
  ctx.globalAlpha = a;
  shD.draw(ctx, f, m.x, ly, sc, flip, m.tint ? tintedSheet(shD, m.tint) : undefined);
  if (m.flash > 0 && !m.dying && shD.white) { ctx.globalAlpha = Math.min(0.85, m.flash) * a; shD.draw(ctx, f, m.x, ly, sc, flip, shD.white); }
  if (t - (m.drainT || -9) < 0.5 && !m.dying) drawDrainMob(ctx, m, t, ly, sc);
  if (m.archi && !m.dying) drawShiny(ctx, m, sh, f, ly, sc, flip, a, t);   // 0.34: an Archimonster is 'shiny' (sheen + twinkling stars), no more pink aura
  ctx.globalAlpha = 1;
  drawMobMarks(ctx, m, t, sh, anim, ly, sc, true);
}
// the marks over a monster: target, slow, stun, names and life bars, poison / bleed (status false: PixiJS drew those)
// 0.65: the top of a monster's own drawing (its first walk frame's height): the bars and names sit just over it (they
// were placed from its collision radius: far above the big bosses and the Maitres Corbacs)
function mobTop(m, sh, anim, sc) {
  if (m._top) return m._top;
  const a = sh.anims.walkR || sh.anims[anim]; if (!a) return m.r * 2.4 * sc;
  if (sh._oyTop === undefined && sh.img) {   // (once per sheet: the walk's opaque tops, its lower poses — frames keep some empty
    try {                                    // margin, and a jumping walk would put the bar at its highest point)
      const k = sh.img._k || 1, c = document.createElement('canvas'), g = c.getContext('2d', { willReadFrequently: true }); const tops = [];
      for (const f of a.f) {
        const w = Math.max(1, Math.round(f[2] * k)), hh = Math.max(1, Math.round(f[3] * k)); c.width = w; c.height = hh;
        g.drawImage(sh.img, f[0] * k, f[1] * k, f[2] * k, f[3] * k, 0, 0, w, hh);
        const d = g.getImageData(0, 0, w, hh).data; let row = 0;
        search: for (; row < hh; row++) for (let x = 0; x < w; x++) if (d[(row * w + x) * 4 + 3] > 60) break search;
        tops.push(f[5] - row / k);
      }
      tops.sort((x, y) => x - y); sh._oyTop = tops.length ? tops[Math.floor(tops.length * 0.3)] : null;   // (the lower poses: a hop goes over it)
    } catch (e) { sh._oyTop = null; }
  }
  return (m._top = (sh._oyTop || a.f[0][5]) * sc / sh.zoom);
}
// 0.65: a boss's own life bar over its head (besides the big one at the top of the screen): bright red, a lighter
// band where the life just went (it melts away), a light sweeping across, a pulsing glow behind
function drawBossBar(ctx, m, t, y) {
  const w = clamp(m.r * 2.4 * (m.scale || 1), 74, 130), h = 9, x = m.x - w / 2, k = clamp(m.hp / m.maxHp, 0, 1);
  m._hpLag = m._hpLag === undefined || m._hpLag < k ? k : m._hpLag + (k - m._hpLag) * 0.06;   // (the lost life melts away)
  const pulse = 0.5 + 0.5 * Math.sin(t * 5);
  ctx.globalAlpha = 0.55 + 0.35 * pulse; ctx.drawImage(RCache.glow('rgba(255,30,40,0.95)'), x - 20, y - 16, w + 40, h + 32); ctx.globalAlpha = 1;
  ctx.fillStyle = '#1a0003'; ctx.fillRect(x - 2, y - 2, w + 4, h + 4);
  ctx.fillStyle = '#4a0a10'; ctx.fillRect(x, y, w, h);
  ctx.fillStyle = '#ffd0a0'; ctx.fillRect(x, y, w * m._hpLag, h);
  ctx.fillStyle = pulse > 0.85 ? '#ff4a52' : '#ff1f2e'; ctx.fillRect(x, y, w * k, h);
  ctx.fillStyle = 'rgba(255,140,120,0.85)'; ctx.fillRect(x, y, w * k, 2);   // its light top edge
  const sx = (t * 0.7 % 1.4) - 0.2;   // a light sweeping across the red
  if (sx > 0 && sx < 1) { const bx = x + w * k * sx; ctx.fillStyle = 'rgba(255,255,255,0.45)'; ctx.fillRect(Math.max(x, bx - 5), y, Math.min(10, x + w * k - bx + 5), h); }
  ctx.fillStyle = 'rgba(255,255,255,0.18)'; for (let i = 1; i < 4; i++) ctx.fillRect(x + w * i / 4, y, 1, h);   // quarter marks
}
function drawMobMarks(ctx, m, t, sh, anim, ly, sc, status) {
  if (m.markUntil > t && !m.dying) { const yy = ly - m.r * 3.2 * sc - 6; ctx.drawImage(RCache.tri(), m.x - 7.5, yy - 4.5, 15, 13); }   // (0.95: a picture: PixiJS draws it itself)
  if (m.slowUntil > t && !m.dying) { ctx.fillStyle = 'rgba(120,210,255,0.35)'; ctx.beginPath(); ctx.ellipse(m.x, m.y - 2, m.r * 1.1, m.r * 0.45, 0, 0, TAU); ctx.fill(); }
  if (m.stunUntil > t && !m.dying) { ctx.fillStyle = '#ffe066'; for (let i = 0; i < 3; i++) { const an = t * 6 + i * 2.1; ctx.beginPath(); ctx.arc(m.x + Math.cos(an) * 10, m.y - m.r * 2.8 + Math.sin(an) * 3, 2.2, 0, TAU); ctx.fill(); } }
  if (m.archi && !m.dying) {   // its name and its life
    const by = ly - mobTop(m, sh, anim, sc) - 9, w = 60; outlinedText(ctx, L(m.archi.name), m.x, by - 6, '#ffe89a', 11, 'center');
    ctx.fillStyle = '#000c'; ctx.fillRect(m.x - w / 2 - 1, by - 1, w + 2, 6); ctx.fillStyle = '#f2c230'; ctx.fillRect(m.x - w / 2, by, w * clamp(m.hp / m.maxHp, 0, 1), 4);
  }
  if (m.boss && !m.dying && !m.doom) drawBossBar(ctx, m, t, ly - mobTop(m, sh, anim, sc) - 11);
  if (m.doom && !m.dying) { const w = 70, by = ly - mobTop(m, sh, anim, sc) - 7; ctx.fillStyle = '#000c'; ctx.fillRect(m.x - w / 2 - 1, by - 1, w + 2, 7); ctx.fillStyle = '#c0283a'; ctx.fillRect(m.x - w / 2, by, w * m.hp / m.maxHp, 5); }   // the Maîtres Corbacs can be killed
  if (status && !m.dying && (m.bleedUntil > t || m.poisonUntil > t)) drawStatus(ctx, m, sh, anim, ly, sc, t);
  if (m.timed && !m.dying) {   // 0.52: the scheduled elites: their name and their life over their head, like the Archimonsters
    const by = ly - mobTop(m, sh, anim, sc) - 9, w = 64;
    outlinedText(ctx, L(m.def.name), m.x, by - 6, '#ffcf6a', 11, 'center');
    ctx.fillStyle = '#000c'; ctx.fillRect(m.x - w / 2 - 1, by - 1, w + 2, 7); ctx.fillStyle = '#ff9a1e'; ctx.fillRect(m.x - w / 2, by, w * clamp(m.hp / m.maxHp, 0, 1), 5);
  } else if ((m.elite) && !m.dying && m.hp < m.maxHp) { const w = 36; ctx.fillStyle = '#000a'; ctx.fillRect(m.x - w / 2, m.y + 6, w, 4); ctx.fillStyle = '#ffb02e'; ctx.fillRect(m.x - w / 2, m.y + 6, w * m.hp / m.maxHp, 4); }
}
function drawDrop(ctx, kind, x, y) { const c = RCache.drop(kind); ctx.drawImage(c, x + c.x0, y + c.y0, c.w, c.h); }
// 0.54: bleeding = a see-through dark red aura and three little blood drops over the head. 0.40: poisoned = a green /
// violet gas on the monster and a little poison drop above it; 0.45: the drop sits just over the sprite's own head (its
// height in the sheet: the first walk frame's origin), the gas is denser, with bubbles rising out of it.
// 0.59: drawn from pre-rendered pieces (RCache.drop / bubble / gas, no gradient, path or save / restore per monster);
// the live gas swirl and the bubbles only on the STATUS_FULL nearest monsters (m._fullFx, set by Run.draw)
function drawStatus(ctx, m, sh, anim, ly, sc, t) {
  // 0.68: no more drops / gas balls over the monsters: a subtle animated aura in the spirit of the level 100 / 200
  // auras and the Sagesse orbs — a soft glow on the ground and luminous wisps rising (poison: green, a touch of violet) or
  // dripping (bleeding: dark red) along the body; the 20 nearest get every wisp (m._fullFx), the others a few
  const wf = (sh.anims.walkR || sh.anims[anim]).f[0], top = (m._top || (m._top = wf[5] * sc / sh.zoom));
  const ph0 = m._gph || (m._gph = Math.random() * 10), full = m._fullFx && !Game.lowFx, R0 = Math.max(m.r * 1.2 * sc, top * 0.45);
  const aura = (c1, c2, n, rise, speed) => {
    const p = 0.75 + 0.25 * Math.sin(t * 3 + ph0);
    ctx.globalAlpha = 0.32 * p; ctx.drawImage(RCache.glow(c1), m.x - R0 * 1.15, ly - R0 * 0.42, R0 * 2.3, R0 * 0.84);   // (the glow on the ground)
    for (let i = 0; i < n; i++) {
      const q = (t * speed + i / n + ph0) % 1, a = ph0 * 3 + i * 2.399, sx = m.x + Math.cos(a + t * 0.8) * R0 * 0.55;
      const y = rise ? ly - q * top * 1.05 : ly - top * 0.75 + q * top * 0.7, w = (rise ? 2.6 + 2.4 * Math.sin(q * Math.PI) : 3.4 - 1.6 * q) * Math.max(1, sc * 0.9);
      ctx.globalAlpha = 0.7 * Math.sin(q * Math.PI); ctx.drawImage(RCache.glow(i % 3 === 2 ? c2 : c1), sx - w * 2.2, y - w * 2.2, w * 4.4, w * 4.4);
    }
  };
  if (m.poisonUntil > t) aura('rgba(95,230,70,0.95)', 'rgba(175,95,240,0.95)', full ? 6 : 2, true, 0.55);
  if (m.bleedUntil > t) aura('rgba(225,25,45,0.95)', 'rgba(140,0,20,0.95)', full ? 5 : 2, false, 0.75);
  ctx.globalAlpha = 1;
}
function drawSummon(ctx, s, t) {
  const k = clamp((s.until - t) / 0.4, 0, 1);
  if (s.decoy) { // Sram's Double: the player's own look, a little ghostly
    const R = Game.run, sp = R && R.charSprite; if (!sp) return;
    ctx.save(); ctx.globalAlpha = (0.55 + 0.15 * Math.sin(t * 8)) * Math.min(1, (t - s.born) * 4) * k;
    ctx.fillStyle = 'rgba(150,100,255,0.35)'; ctx.beginPath(); ctx.ellipse(s.x, s.y, 20, 8, 0, 0, TAU); ctx.fill();
    sp.draw(ctx, 'staticR', t, s.x, s.y, ES, s.flipP, { loop: true, alpha: 1 }); ctx.restore(); return;
  }
  if (s.cs) { // a character-sheet summon (the Mama): runs, hits with anim0
    const cs = s.cs; let anim = 'runR', at = s.t;
    if (s.atkT !== undefined && s.atkT < cs.duration('anim0R')) { anim = 'anim0R'; at = s.atkT; }
    ctx.save(); ctx.globalAlpha = Math.min(1, (t - s.born) * 4) * k;
    ctx.fillStyle = 'rgba(80,160,255,0.25)'; ctx.beginPath(); ctx.ellipse(s.x, s.y, 16, 6, 0, 0, TAU); ctx.fill();
    cs.draw(ctx, anim, at, s.x, s.y, 0.9 * ES, s.flip, { loop: anim === 'runR' }); ctx.restore(); return;
  }
  const sh = s.sh; if (!sh) return;
  let anim = 'walkR', at = s.t, loop = true;
  if (s.atkT !== undefined && sh.has('atkR') && s.atkT < sh.duration('atkR')) { anim = 'atkR'; at = s.atkT; loop = false; }   // (0.59: s.atkT advances in updateSummons)
  const f = sh.frameAt(anim, at, loop); if (!f) return;
  ctx.save(); ctx.globalAlpha = Math.min(1, (t - s.born) * 4) * k;
  ctx.fillStyle = s.healer ? 'rgba(120,255,150,0.3)' : 'rgba(80,160,255,0.25)'; ctx.beginPath(); ctx.ellipse(s.x, s.y, 16, 6, 0, 0, TAU); ctx.fill();
  sh.draw(ctx, f, s.x, s.fly ? s.y - 8 + Math.sin(t * 5) * 3 : s.y, 0.9 * ES, s.flip);
  ctx.restore();
}
// 0.25: the exact strip a melee blow hits (all weapons): a swept area brighter toward the tip, with a clear rim
// 0.60: the kill combo (juice.js), fading out when it breaks. 0.62: left of the pause button (it covered it), a pop on
// each kill and a bigger one at each step, a glow of the step's colour, a bar showing the time left before it breaks,
// the broken combo's number falling away
function drawCombo(ctx, R, W, u) {
  const n = R._combo || 0, dt = R.time - (R._comboT || -9), x = W - 66 * u, y = 116 * u;
  const E = R._comboEnd, ee = E ? (performance.now() - E.t0) / 1000 : 9;
  if (n >= 10 && dt < 1.6) {
    let mi = -1; while (mi + 1 < COMBO_MS.length && n >= COMBO_MS[mi + 1]) mi++;
    const col = mi < 0 ? '#f3e3c3' : COMBO_COLS[mi], ca = clamp((1.6 - dt) / 0.4, 0, 1), big = R.bumpK('combo', 420), pop = R.bumpK('ckill', 110);
    const fs = Math.round(21 * u * (1 + 0.07 * Math.max(0, mi) + 0.12 * pop + 0.5 * big));
    ctx.save(); ctx.globalAlpha = ca;
    if (mi >= 0) { const r = (34 + 6 * mi) * u * (1 + 0.4 * big); ctx.globalAlpha = ca * (0.35 + 0.35 * big); ctx.drawImage(RCache.glow(`rgba(${hexRgb(col)},0.85)`), x - 36 * u - r, y - 8 * u - r, r * 2, r * 2); ctx.globalAlpha = ca; }
    outlinedText(ctx, T('combo_word').toUpperCase(), x, y - fs * 0.95, '#f3e3c3', Math.round(10 * u), 'right');
    ctx.translate(x, y); if (mi >= 2) ctx.rotate(Math.sin(R.time * 22) * 0.025 * (mi - 1) * (0.4 + big));
    outlinedText(ctx, '×' + n, 0, 0, col, fs, 'right');
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    const bw = 74 * u, bh = 4 * u, k = clamp(1 - dt / 1.6, 0, 1);   // the time left before it breaks
    ctx.fillStyle = 'rgba(20,12,6,0.7)'; ctx.fillRect(x - bw, y + 5 * u, bw, bh); ctx.fillStyle = col; ctx.fillRect(x - bw * k, y + 5 * u, bw * k, bh);
    ctx.restore();
  } else if (E && ee < 0.9) {   // broken: the last number drops and fades
    ctx.save(); ctx.globalAlpha = (1 - ee / 0.9) * 0.9; outlinedText(ctx, '×' + E.n, x, y + ee * 26 * u, '#b8a67e', Math.round(21 * u * (1 - 0.2 * ee)), 'right'); ctx.restore();
  }
}
function hexRgb(h) { const n = parseInt(h.slice(1), 16); return `${n >> 16 & 255},${n >> 8 & 255},${n & 255}`; }
// 0.98.3: a thrown shovel (spell `coins`), lost among the effects: a halo of gold under it and kamas turning round it, on
// a ring wider than the shovel so none hides it; its own wake of gold is in game.js. The sprite is drawn bigger, a gold rim round it
function shovelCoins(ctx, p, t) {
  const r = p.size * 2.5, h = p.size * 3.1; ctx.globalAlpha *= 0.8; ctx.drawImage(RCache.glow('rgba(255,205,70,0.95)'), -h, -h, h * 2, h * 2); ctx.globalAlpha /= 0.8;
  const c = kamaCoin();
  for (let i = 0; i < 5; i++) { const a = t * 6 + i * TAU / 5, s = Math.sin(a), d = 15 + 3 * s, w = d * (0.45 + 0.55 * Math.abs(Math.cos(t * 9 + i))); ctx.drawImage(c, Math.cos(a) * r - w / 2, s * r * 0.55 - d / 2, w, d); }
}
// a gold coin with the Kama symbol on it (made once: the symbol alone reads as a small blue star at this size); it turns by its width
function kamaCoin() {
  if (kamaCoin.c) return kamaCoin.c;
  const c = document.createElement('canvas'), S = 40, g = c.getContext('2d'); c.width = c.height = S;
  const gr = g.createRadialGradient(S * 0.38, S * 0.32, 2, S / 2, S / 2, S / 2); gr.addColorStop(0, '#fff3b0'); gr.addColorStop(0.55, '#ffcc33'); gr.addColorStop(1, '#c98410');
  g.beginPath(); g.arc(S / 2, S / 2, S / 2 - 2, 0, TAU); g.fillStyle = gr; g.fill(); g.lineWidth = 3; g.strokeStyle = '#7a4a08'; g.stroke();
  const k = Game.icons.canvas('KamaSymbol', 24); if (k) g.drawImage(k, S / 2 - 12, S / 2 - 12, 24, 24);
  return (kamaCoin.c = c);
}
function drawProj(ctx, p, t) {
  if (p.crescent) return drawCrescent(ctx, p, t);
  const fx = FxSheets.get(p.spell.def.fx[0]);
  const ang = Math.atan2(p.vy, p.vx);
  ctx.save(); ctx.translate(p.x, p.y);
  if (p.chaos) { drawChaosBall(ctx, p, t, ang); ctx.restore(); return; }   // (0.96: the Boule de Chaos)
  if (p.coins) shovelCoins(ctx, p, t);
  if (p.dagger) { // Dagues Boomerang: the dagger itself, spinning
    const A = drawAccSym(ctx, (p.spell && p.spell.finale && p.spell.finale.skin) || '5_10', 'R', 0.55, p.rot || 0); if (A) { ctx.restore(); return; }
  }
  if (p.drawIcon) { // spinning object (rolling shovel, thrown hatchet)
    if (p.col) { const r = p.size * 2.2; ctx.drawImage(RCache.glow(p.col), -r, -r, r * 2, r * 2); }   // (0.91: the Otomaï's flask glows)
    ctx.rotate(p.rot || t * 10); Game.icons.drawFit(ctx, p.drawIcon, 0, 0, p.size * (p.coins ? 3.4 : 2.6)); ctx.restore(); return;
  }
  if (p.fireball || (p.col && !p.arrow && !(fx && fx.anims.move))) { // coloured magic orb
    const r = p.size * 1.8; ctx.drawImage(RCache.glow(p.col), -r, -r, r * 2, r * 2); ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(0, 0, p.size * 0.45, 0, TAU); ctx.fill(); ctx.restore(); return;
  }
  if (p.spell.def.id === 'aiguille') { // Xélor's needle: a golden clock hand with a blue time trail, along its path
    ctx.rotate(ang); const L = 34, g = ctx.createLinearGradient(-L * 1.6, 0, 0, 0);
    g.addColorStop(0, 'rgba(120,200,255,0)'); g.addColorStop(1, 'rgba(140,215,255,0.75)');
    ctx.fillStyle = g; ctx.beginPath(); ctx.moveTo(-L * 1.6, 0); ctx.lineTo(-4, -5); ctx.lineTo(-4, 5); ctx.closePath(); ctx.fill();
    const r = 15; ctx.drawImage(RCache.glow('rgba(120,200,255,0.55)'), -r, -r, r * 2, r * 2);
    ctx.fillStyle = '#ffd86a'; ctx.strokeStyle = '#5a3a08'; ctx.lineWidth = 1.6;
    ctx.beginPath(); ctx.moveTo(L * 0.55, 0); ctx.lineTo(0, -4.5); ctx.lineTo(-L * 0.45, -1.6); ctx.lineTo(-L * 0.45, 1.6); ctx.lineTo(0, 4.5); ctx.closePath(); ctx.fill(); ctx.stroke();
    ctx.fillStyle = '#fff6c8'; ctx.beginPath(); ctx.moveTo(L * 0.5, 0); ctx.lineTo(0, -1.6); ctx.lineTo(0, 1.6); ctx.closePath(); ctx.fill();
    ctx.fillStyle = '#5a3a08'; ctx.beginPath(); ctx.arc(-L * 0.3, 0, 2.6, 0, TAU); ctx.fill();
    ctx.restore(); return;
  }
  if (p.stone) { // sling stone
    ctx.rotate(p.rot || t * 8); ctx.fillStyle = '#8d8478'; ctx.strokeStyle = '#3b352e'; ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.ellipse(0, 0, p.size * 0.9, p.size * 0.7, 0.4, 0, TAU); ctx.fill(); ctx.stroke();
    ctx.fillStyle = 'rgba(255,255,255,0.35)'; ctx.beginPath(); ctx.ellipse(-2, -2, 2.5, 1.6, 0, 0, TAU); ctx.fill(); ctx.restore(); return;
  }
  if (fx && fx.anims.move) {
    // the client's travelling clips are drawn head to the right: they follow the trajectory (Flamiche, arrows, needles…)
    if (fx.anims.trail) {   // (Marteau de Moon: the arcs it leaves on its way, behind it, along the path)
      ctx.save(); ctx.rotate(ang + Math.PI); fx.draw(ctx, fx.frameAt('trail', t - p.t0, true), 0, 0, 1, false, p.tint && tintedSheet(fx, p.tint)); ctx.restore();
    }
    if (p.tint) { const r = p.size * 2.6; ctx.globalAlpha *= 0.55; ctx.drawImage(RCache.glow('rgba(150,60,255,0.85)'), -r, -r, r * 2, r * 2); ctx.globalAlpha /= 0.55; }   // (0.96: the Marteau du Chaos, a violet aura)
    if (p.rot) ctx.rotate(p.rot); else ctx.rotate(ang);
    const f = fx.frameAt('move', t - p.t0, true);
    if (p.fxScale) { const r = p.size * 2.2; ctx.drawImage(RCache.glow('rgba(255,140,40,0.75)'), -r, -r, r * 2, r * 2); }   // Flamiche: bigger, with a glow
    if (p.coins) { fx.draw(ctx, f, 0, 0, 1.5, false, tintedSheet(fx, '#ffd24a')); fx.draw(ctx, f, 0, 0, 1.32, false); } else
    fx.draw(ctx, f, 0, 0, p.fxScale || 1, false);
  } else if (fx && fx.anims.bulle) {
    const f = fx.frameAt('bulle', 0, true); fx.draw(ctx, f, 0, 0, 1.1, false);
  } else {
    const c = p.col || { pile_ou_face: '#ffd24a', lancer_pieces: '#ffd24a', sablier_xelor: '#7fe0ff', fleche_enflammee: '#ff7a2a', flasque_explosive: '#a5ff7a', baguette: '#c58aff', flamiche: '#ff8a2a' }[p.spell.def.id] || '#ffffff';
    if (p.arrow) { ctx.rotate(ang); ctx.strokeStyle = c; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(-14, 0); ctx.lineTo(8, 0); ctx.stroke(); ctx.fillStyle = c; ctx.beginPath(); ctx.moveTo(12, 0); ctx.lineTo(4, -4); ctx.lineTo(4, 4); ctx.fill(); }
    else {
      const r = p.size * 1.6; ctx.drawImage(RCache.glow(c), -r, -r, r * 2, r * 2); ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(0, 0, p.size * 0.4, 0, TAU); ctx.fill();
      if (p.spell.def.id === 'pile_ou_face' || p.spell.def.id === 'lancer_pieces') { ctx.scale(Math.cos(t * 12), 1); ctx.fillStyle = '#e6b422'; ctx.beginPath(); ctx.arc(0, 0, p.size * 0.8, 0, TAU); ctx.fill(); ctx.fillStyle = '#fff2a0'; ctx.fillRect(-1, -p.size * 0.5, 2, p.size); }
    }
  }
  ctx.restore();
}
function drawEProj(ctx, e, t) {
  ctx.save(); ctx.translate(e.x, e.y);
  const fx = e.fx && FxSheets.get(e.fx);
  if (e.crow) { // the Maîtres Corbacs throw corbacs
    const sh = MobSheets.c[Game.C.doom.crowSprite];
    if (sh) { const f = sh.frameAt('walkR', t * 1.5 + e.t0, true); ctx.restore(); ctx.save(); ctx.globalAlpha = 0.95; sh.draw(ctx, f, e.x, e.y + 14, ES * 0.85, e.vx < 0); ctx.restore(); return; }
  }
  if (fx && fx.anims.move) { const r = (e.size || 8) * 2.4; ctx.globalAlpha = 0.55; ctx.drawImage(RCache.glow(e.color || 'rgba(255,210,120,0.9)'), -r, -r, r * 2, r * 2); ctx.globalAlpha = 1; ctx.rotate(Math.atan2(e.vy || 0, e.vx || 1)); fx.draw(ctx, fx.frameAt('move', t, true), 0, 0, 1.2, false); }   // (0.68: 20 % bigger, a halo)
  else if (e.arrow) {   // (0.68: bigger, a faint streak behind; the hitbox is unchanged)
    ctx.rotate(Math.atan2(e.vy, e.vx));
    ctx.globalAlpha = 0.35; ctx.drawImage(RCache.glow('rgba(255,245,220,0.9)'), -40, -5, 40, 10); ctx.globalAlpha = 1;
    ctx.drawImage(RCache.arrow(), -30, -7, 48, 14);
  } else {   // (0.68: a spell orb: a trail of glows, a halo, sparks turning around a bright core)
    const col = e.color || '#f55', r = e.size * 1.9, sp = Math.hypot(e.vx || 0, e.vy || 0) || 1, ux = (e.vx || 0) / sp, uy = (e.vy || 0) / sp;
    for (let i = 3; i >= 1; i--) { const d = i * e.size * 1.15, w = r * (1 - i * 0.2); ctx.globalAlpha = 0.5 - i * 0.12; ctx.drawImage(RCache.glow(col), -ux * d - w, -uy * d - w, w * 2, w * 2); }
    const p = 1 + 0.12 * Math.sin(t * 14 + (e.t0 || 0) * 7); ctx.globalAlpha = 1; ctx.drawImage(RCache.glow(col), -r * p, -r * p, r * 2 * p, r * 2 * p);
    for (let i = 0; i < 3; i++) { const a = t * 7 + i * TAU / 3 + (e.t0 || 0), x = Math.cos(a) * e.size * 0.95, y = Math.sin(a) * e.size * 0.95, w = e.size * 0.42; ctx.drawImage(RCache.glow('rgba(255,250,235,0.95)'), x - w, y - w, w * 2, w * 2); }
    const cr = e.size * 0.75; ctx.drawImage(RCache.glow('rgba(255,255,255,1)'), -cr, -cr, cr * 2, cr * 2);
  }
  ctx.restore();
}
function drawPlayerBars(ctx, R) {
  const P = R.player; if (P.dead) return;
  const w = 44, x = P.x - w / 2, y = P.y + 8;
  ctx.fillStyle = 'rgba(0,0,0,0.6)'; ctx.fillRect(x - 1, y - 1, w + 2, 6);
  ctx.fillStyle = '#d92b2b'; ctx.fillRect(x, y, w * clamp(P.hp / R.stats.maxHp, 0, 1), 4);
}
// ---------------------------------------------------------------- HUD (screen space)
// the shortcut under a HUD button, for the device the player last used: a shoulder trigger (L / R) on a gamepad,
// key caps on a keyboard (A or Q depending on AZERTY / QWERTY), the gesture on a touch screen
function roundRectPath(ctx, x, y, w, h, r) { const rr = Array.isArray(r) ? r : [r, r, r, r]; ctx.beginPath(); ctx.moveTo(x + rr[0], y); ctx.lineTo(x + w - rr[1], y); ctx.quadraticCurveTo(x + w, y, x + w, y + rr[1]); ctx.lineTo(x + w, y + h - rr[2]); ctx.quadraticCurveTo(x + w, y + h, x + w - rr[2], y + h); ctx.lineTo(x + rr[3], y + h); ctx.quadraticCurveTo(x, y + h, x, y + h - rr[3]); ctx.lineTo(x, y + rr[0]); ctx.quadraticCurveTo(x, y, x + rr[0], y); ctx.closePath(); }
function drawTrigger(ctx, letter, cx, cy, u) {
  const w = 26 * u, h = 16 * u, x = cx - w / 2, y = cy - h / 2, big = 9 * u, sm = 3 * u;
  const g = ctx.createLinearGradient(0, y, 0, y + h); g.addColorStop(0, '#5a5a66'); g.addColorStop(1, '#1d1d24');
  roundRectPath(ctx, x, y, w, h, letter === 'L' ? [big, sm, sm, sm] : [sm, big, sm, sm]);
  ctx.fillStyle = g; ctx.fill(); ctx.lineWidth = 1.5 * u; ctx.strokeStyle = '#e6e6ee'; ctx.stroke();
  TextCache.draw(ctx, letter, cx, cy + 4.5 * u, '#ffffff', 12 * u, 'center', 'rgba(0,0,0,0.6)', 2 * u);
}
function drawKeyCap(ctx, label, cx, cy, u, w) {
  w = (w || 17) * u; const h = 16 * u, x = cx - w / 2, y = cy - h / 2;
  roundRectPath(ctx, x, y + 2 * u, w, h, 4 * u); ctx.fillStyle = '#0e0a06'; ctx.fill();   // key side
  roundRectPath(ctx, x, y, w, h, 4 * u); ctx.fillStyle = '#3a2c1e'; ctx.fill(); ctx.lineWidth = 1.2 * u; ctx.strokeStyle = '#e8d9b0'; ctx.stroke();
  TextCache.draw(ctx, label, cx, cy + 4 * u, '#fff4d8', 10.5 * u, 'center', 'rgba(0,0,0,0.6)', 1.5 * u);
}
// 0.98: the HUD's round buttons (the dash, the moving spell's switch, the auto-pick) in the verdant style: a deep green
// plate lit from the top left, a gold rim, a lime inner line; ready = a breathing lime glow and a spark running round
// the rim; pop (0..1) = just ready again, a ring going out
function hudPlate(ctx, x, y, r, u, t, ready, pop = 0) {
  if (ready) { ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha = 0.26 + 0.14 * Math.sin(t * 3); const gr = r * 1.75; ctx.drawImage(RCache.glow('rgba(170,240,80,0.8)'), x - gr, y - gr, gr * 2, gr * 2); ctx.restore(); }
  const g = ctx.createRadialGradient(x - r * 0.35, y - r * 0.4, r * 0.1, x, y, r); g.addColorStop(0, '#4caa58'); g.addColorStop(0.55, '#1f5a34'); g.addColorStop(1, '#0c2c18');
  ctx.globalAlpha = 0.92; ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); ctx.fill(); ctx.globalAlpha = 1;
  ctx.lineWidth = 3.6 * u; ctx.strokeStyle = '#132a0c'; ctx.stroke();
  const gd = ctx.createLinearGradient(0, y - r, 0, y + r); gd.addColorStop(0, '#fff1b0'); gd.addColorStop(0.5, '#f2b83a'); gd.addColorStop(1, '#9a6010'); ctx.lineWidth = 2.1 * u; ctx.strokeStyle = gd; ctx.stroke();
  ctx.lineWidth = 1 * u; ctx.strokeStyle = 'rgba(200,250,120,0.45)'; ctx.beginPath(); ctx.arc(x, y, r - 3.2 * u, 0, TAU); ctx.stroke();
  if (ready && !Game.lowFx) { const an = t * 2.2, s = 5 * u; ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.drawImage(RCache.glow('rgba(255,255,200,0.95)'), x + Math.cos(an) * r - s, y + Math.sin(an) * r - s, s * 2, s * 2); ctx.restore(); }
  if (pop > 0) { ctx.save(); ctx.globalAlpha = pop; ctx.strokeStyle = '#d8f870'; ctx.lineWidth = 3 * u * pop; ctx.beginPath(); ctx.arc(x, y, r + (1 - pop) * 14 * u, 0, TAU); ctx.stroke(); ctx.restore(); }
}
// 0.98: a fusion's icon in the run's spell bar: two lights running round its violet / gold edge and three twinkling stars
// (cached glows and sparks only: 5 small pictures an icon, nothing kept between frames)
function hudFusionSparks(ctx, x, y, s, u, t, seed) {
  const gl = RCache.glow('rgba(255,236,170,0.95)'), vi = RCache.glow('rgba(200,140,255,0.95)'), per = s * 4;
  const at = q => { q = ((q % 1) + 1) % 1; const d = q * per; return d < s ? [x + d, y] : d < 2 * s ? [x + s, y + d - s] : d < 3 * s ? [x + 3 * s - d, y + s] : [x, y + 4 * s - d]; };
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  for (const [q, img, r] of [[t * 0.35, gl, 7], [t * 0.35 + 0.5, vi, 6]]) { const [px, py] = at(q); ctx.globalAlpha = 0.95; ctx.drawImage(img, px - r * u, py - r * u, r * 2 * u, r * 2 * u); }
  for (let i = 0; i < (Game.lowFx ? 1 : 3); i++) {
    const tw = Math.max(0, Math.sin(t * 3 + i * 2.1 + seed * 0.01)); if (tw < 0.05) continue;
    const sx = x + s * (0.2 + 0.6 * ((i * 0.37 + seed * 0.013) % 1)), sy = y + s * (0.15 + 0.3 * i), r = (3 + 4 * tw) * u;
    ctx.globalAlpha = tw; ctx.fillStyle = '#fff6d0'; ctx.beginPath(); for (let k = 0; k < 8; k++) { const rr = k % 2 ? r * 0.18 : r, a = k / 8 * TAU; ctx.lineTo(sx + Math.cos(a) * rr, sy + Math.sin(a) * rr); } ctx.closePath(); ctx.fill();
  }
  ctx.restore();
}
function drawKeyHint(ctx, kind, cx, cy, u, off) {
  const d = Input.dev;
  if (off) ctx.globalAlpha = 0.6;
  if (d === 'pad') drawTrigger(ctx, kind === 'dash' ? 'R' : 'L', cx, cy, u);
  else if (d === 'touch') TextCache.draw(ctx, kind === 'dash' ? '2× ☝' : '☝', cx, cy + 7 * u, off ? '#ff9a7a' : '#f4ffd0', 16 * u, 'center', 'rgba(0,0,0,0.85)', 3 * u);   // (0.98: bigger on phones and tablets: 11 -> 16)
  else if (kind === 'dash') { drawKeyCap(ctx, '␣', cx - 12 * u, cy, u, 22); drawKeyCap(ctx, 'E', cx + 11 * u, cy, u); }
  else drawKeyCap(ctx, Input.toggleKey(), cx, cy, u);
  ctx.globalAlpha = 1;
}
function hudFont(px, bold = true) { return `${bold ? 'bold ' : ''}${px}px ${bold ? 'DofusBold' : 'Dofus'}, Verdana, sans-serif`; }
// outlined texts are rendered once into small cached canvases: strokeText every frame is one of the costliest canvas calls.
// 0.98.1, measured on a phone's CPU: a cached text costs ~0.06 ms to draw, a new one ~3 ms (a canvas, its context, the
// measure, the stroke); a text that changes often is made again 10 times a second at most (the boss bars). Tried and
// dropped: <img> copies of the texts (drawn at their size, a canvas costs the same; the copies' toBlob cost more) and the
// numbers drawn glyph by glyph from strips (more draws: 0.99 -> 1.38 ms a frame on a crowded fight)
const TextCache = {
  m: new Map(), g0: null,
  get(s, fill, px, stroke, lw) {
    s = String(s); px = Math.max(4, Math.round(px * 2) / 2);
    const k = s + '\u0001' + fill + '\u0001' + px + '\u0001' + stroke + '\u0001' + lw;
    let c = this.m.get(k);
    if (c) { this.m.delete(k); this.m.set(k, c); return c; }
    const g0 = this.g0 || (this.g0 = document.createElement('canvas').getContext('2d'));
    const font = hudFont(px); g0.font = font;
    const pad = Math.ceil(lw) + 2, tw = g0.measureText(s).width;
    c = document.createElement('canvas'); c.width = Math.max(1, Math.ceil(tw + pad * 2)); c.height = Math.max(1, Math.ceil(px * 1.32 + pad * 2));
    const g = c.getContext('2d'); g.font = font; g.lineJoin = 'round'; g.lineWidth = lw; g.strokeStyle = stroke; g.fillStyle = fill;
    c.bx = pad; c.by = Math.round(pad + px * 0.98); c.tw = tw;
    g.strokeText(s, c.bx, c.by); g.fillText(s, c.bx, c.by);
    this.m.set(k, c); if (this.m.size > 700) this.m.delete(this.m.keys().next().value);
    return c;
  },
  // draw at (x, y) = text anchor on the baseline; k = extra scale (e.g. render at zoom for world-space texts)
  draw(ctx, s, x, y, fill, px, align, stroke, lw, k = 1) {
    const c = this.get(s, fill, px * k, stroke, lw * k), sc = 1 / k;
    const ax = align === 'center' ? c.tw / 2 : align === 'right' ? c.tw : 0;
    if (k === 1) ctx.drawImage(c, Math.round(x - c.bx - ax), Math.round(y - c.by));   // screen-space texts on whole pixels: sharp
    else ctx.drawImage(c, x - (c.bx + ax) * sc, y - c.by * sc, c.width * sc, c.height * sc);
  },
};
// 0.85 (damage numbers as in Dofus Retro): the client's numbers (clips/points/1/*.swf) are its embedded Verdana Bold
// (game/assets/fonts/retronum.woff2, 'RetroNum': the same glyphs, tools/assets/build_retronum085.py), the colour, and a drop
// shadow of that colour x 0.6 a little down and right — no black outline. A very faint dark rim keeps them readable on
// light grounds. Each bitmap has a pale twin (the client's pop-in starts big and whitened). Rendered at screen size, cached.
// 0.95 (perf sweep: a monster's number grows with each hit — new text, new size —, and each change made two new canvases:
// a crowd under damage zones made hundreds a second): one strip of the characters per colour and size (the digits, !, -,
// +), a number drawn glyph by glyph from it (RetroNum's figures all have one width, as the font laid them before)
const NumCache = {
  m: new Map(), ready: false, CH: '0123456789!-+',
  strip(fill, px) {
    px = Math.max(4, Math.round(px * 2) / 2);
    if (!this.ready && document.fonts && document.fonts.check) { this.ready = document.fonts.check('12px RetroNum'); if (this.ready) this.m.clear(); }
    const k = fill + '\u0001' + px; let S = this.m.get(k); if (S) return S;
    const font = `${px}px RetroNum, Verdana, DofusBold, sans-serif`, g0 = TextCache.g0 || (TextCache.g0 = document.createElement('canvas').getContext('2d')); g0.font = font;
    const ox = Math.max(1, px * 0.05), oy = Math.max(1, px * 0.09), pad = Math.ceil(px * 0.12) + 2, h = Math.ceil(px * 1.25 + oy + pad * 2), by = Math.round(pad + px * 0.98), G = {};
    let x = 0; for (const ch of this.CH) { const w = g0.measureText(ch).width, cw = Math.ceil(w + ox + pad * 2); G[ch] = { x, w, cw }; x += cw + 1; }
    const mk = (f, sh) => {
      const cv = document.createElement('canvas'); cv.width = x; cv.height = h; const g = cv.getContext('2d'); g.font = font; g.lineJoin = 'round'; g.lineWidth = Math.max(1, px * 0.1);
      for (const ch of this.CH) { const X = G[ch].x + pad; g.strokeStyle = 'rgba(30,6,0,0.32)'; g.strokeText(ch, X + ox, by + oy); g.strokeText(ch, X, by); g.fillStyle = sh; g.fillText(ch, X + ox, by + oy); g.fillStyle = f; g.fillText(ch, X, by); }
      return cv;
    };
    const rgb = hexToRgb(fill), mix = (a, t) => `rgb(${a.map(v => Math.round(v + (255 - v) * t)).join(',')})`, dark = a => `rgb(${a.map(v => Math.round(v * 0.6)).join(',')})`;
    S = { c: mk(fill, dark(rgb)), pale: mk(mix(rgb, 0.7), mix(rgb.map(v => v * 0.6), 0.6)), G, h, by, pad, sp: G['0'].w };
    this.m.set(k, S); if (this.m.size > 120) this.m.delete(this.m.keys().next().value);
    return S;
  },
  // s centred on x, its baseline on y, scaled by sc (world -> screen), the pale twin over it at opacity pale
  draw(ctx, s, fill, px, x, y, sc, pale) {
    const S = this.strip(fill, px); s = String(s); let w = 0; for (const ch of s) w += S.G[ch] ? S.G[ch].w : S.sp;
    const y0 = y - S.by * sc, h = S.h * sc, a0 = ctx.globalAlpha; let gx = x - w / 2 * sc;
    for (const ch of s) {
      const g = S.G[ch];
      if (g) { ctx.drawImage(S.c, g.x, 0, g.cw, S.h, gx - S.pad * sc, y0, g.cw * sc, h); if (pale > 0) { ctx.globalAlpha = a0 * pale; ctx.drawImage(S.pale, g.x, 0, g.cw, S.h, gx - S.pad * sc, y0, g.cw * sc, h); ctx.globalAlpha = a0; } }
      gx += (g ? g.w : S.sp) * sc;
    }
  },
};
function outlinedText(ctx, s, x, y, fill, px, align = 'left', stroke = 'rgba(0,0,0,0.85)') {
  const k = Math.abs(ctx.getTransform().a);   // (0.53: in world space (zoomed), the text is rendered at its size on screen: sharp names over elites / Archimonsters)
  TextCache.draw(ctx, s, x, y, fill, px, align, stroke, Math.max(2, px / 5), k > 1.02 || k < 0.98 ? k : 1);
}
function drawHud(ctx, R) {
  const W = Game.cw, H = Game.ch, u = Game.ui; // ui scale
  const IC = Game.icons;
  // Eclipse (random event): darkness all around, a circle of light around the character
  if (R.eclipseUntil > R.time) {
    const left = R.eclipseUntil - R.time, k = Math.min(1, (R.C.randEvents.eclipse.dur - left) / 1.5, left / 1.5);
    const px = (R.player.x - R.cam.x) * Game.zoom + W / 2, py = (R.player.y - 30 - R.cam.y) * Game.zoom + H / 2, rr = Math.min(W, H) * 0.32;
    const gr = ctx.createRadialGradient(px, py, rr * 0.35, px, py, rr * 1.4); gr.addColorStop(0, 'rgba(8,4,20,0)'); gr.addColorStop(1, `rgba(8,4,20,${0.88 * k})`);
    ctx.fillStyle = gr; ctx.fillRect(0, 0, W, H);
  }
  // XP bar (0.95: in the spirit of the countdown's medallion — the same place, height and font): a bronze frame with
  // a gold bevel and rivets (xpFrame, made once per size), the level on a small plate at its left, an amber fill with a
  // light top edge, tenths marks and a glow at its tip
  const xb = 6 * u, yb = 6 * u, wb = W - 12 * u, hb = 14 * u, lvT = `${T('level')} ${R.level}`;
  ctx.font = hudFont(11 * u); const lw = Math.ceil(Math.max(ctx.measureText(`${T('level')} 88`).width, ctx.measureText(lvT).width) + 16 * u);
  const F = xpFrame(wb, hb, lw, u); ctx.drawImage(F, xb - F.m, yb - F.m);
  { // 0.60: the bar slides to its value and shines when ambers come in
    const want = clamp(R.xp / R.xpNext, 0, 1); R._xpShow = R._xpShow === undefined || want < R._xpShow - 0.5 ? want : R._xpShow + (want - R._xpShow) * 0.25;
    const tx = xb + lw + 2 * u, tw = wb - lw - 5 * u, ty = yb + 3 * u, th = hb - 6 * u, fw = tw * R._xpShow;
    if (fw > 0.5) {
      const xk = R.bumpK('xp', 220);
      ctx.save(); ctx.beginPath(); ctx.roundRect(tx, ty, tw, th, [0, th / 2, th / 2, 0]); ctx.clip();   // (0.98.3: the fill follows the track's round end)
      ctx.drawImage(xpFill(th), tx, ty, fw, th);
      if (xk > 0) { ctx.fillStyle = `rgba(255,250,225,${(0.5 * xk).toFixed(3)})`; ctx.fillRect(tx, ty, fw, th); }
      ctx.restore();
      ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha = 0.55 + 0.25 * xk; ctx.drawImage(RCache.glow('rgba(255,200,90,0.9)'), tx + fw - th * 1.6, ty - th * 1.1, th * 3.2, th * 3.2); ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
    }
    ctx.fillStyle = 'rgba(40,18,2,0.35)'; for (let i = 1; i < 10; i++) ctx.fillRect(Math.round(tx + tw * i / 10), ty, Math.max(1, u * 0.8), th);   // (tenths)
  }
  outlinedText(ctx, lvT, xb + lw / 2, Math.round(yb + hb / 2 + hudCap(11 * u) / 2), '#fff', 11 * u, 'center');
  // timer
  outlinedText(ctx, fmtTime(R.time), W / 2, yb + hb + 26 * u, R.doom ? '#ff5a4a' : R.time >= (Game.C.doom ? Game.C.doom.t : 600) - 30 ? '#ffb070' : '#fff', 22 * u, 'center');
  // kills & kamas
  outlinedText(ctx, `☠ ${fmtNum(R.kills)}`, W - 14 * u, yb + hb + 20 * u, '#f3e3c3', Math.round(14 * u * (1 + 0.18 * R.bumpK('kills', 160))), 'right');   // (0.60: bumps on each kill)
  IC.draw(ctx, 'KamaSymbol', W - 24 * u, yb + hb + 40 * u, 0.4 * u);
  outlinedText(ctx, fmtNum(R.kamas), W - 38 * u, yb + hb + 45 * u, '#ffd700', Math.round(14 * u * (1 + 0.25 * R.bumpK('kamas', 220))), 'right');
  drawCombo(ctx, R, W, u);
  // spells (0.98.2: on an upright screen under the timer and the boss bars: no room beside them)
  const narrow = W / u < 760;
  let x = 10 * u, y = yb + hb + (narrow ? 38 + Math.min(6, R.bossAlive.length + (R.mutant ? 1 : 0)) * 24 : 10) * u; const s = 50 * u;
  for (const sp of R.spells) {
    ctx.fillStyle = 'rgba(40,30,15,0.8)'; ctx.fillRect(x, y, s, s);
    ctx.drawImage(IC.canvas('sp_' + sp.def.icon, 128), x, y, s, s);
    if (sp.def.t !== 'aura') {
      const cdk = clamp(sp.cd / sp.cooldown(), 0, 1);
      if (cdk > 0) { ctx.fillStyle = 'rgba(0,0,0,0.45)'; ctx.fillRect(x, y + s * (1 - cdk), s, s * cdk); }
    }
    ctx.strokeStyle = sp.def.sfusion ? '#d4a0ff' : sp.maxed ? '#ffd24a' : '#c8a46a'; ctx.lineWidth = 2 * u; ctx.strokeRect(x, y, s, s);
    if (sp.def.sfusion) hudFusionSparks(ctx, x, y, s, u, R.time, x);   // (0.98: a fusion tells itself from a spell at a glance)
    else outlinedText(ctx, String(sp.level), x + s - 4 * u, y + s - 4 * u, sp.maxed ? '#ffd24a' : '#fff', 14 * u, 'right');
    x += s + 5 * u;
  }
  if (R.weapon) {
    const w = R.weapon; x += 6 * u;
    ctx.fillStyle = 'rgba(60,40,10,0.85)'; ctx.fillRect(x, y, s, s);
    const F = w.fusion, tt = R.time;
    if (F) { // 0.25: a fused weapon's slot glows in its element, with a turning ring and the characteristic
      ctx.save(); ctx.translate(x + s / 2, y + s / 2); ctx.globalAlpha = 0.55 + 0.25 * Math.sin(tt * 5); ctx.drawImage(RCache.glow(F.color), -s * 0.9, -s * 0.9, s * 1.8, s * 1.8);
      ctx.globalAlpha = 1; ctx.rotate(tt * 1.5); ctx.strokeStyle = F.color; ctx.lineWidth = 3 * u; ctx.setLineDash([6 * u, 5 * u]); ctx.beginPath(); ctx.arc(0, 0, s * 0.56, 0, TAU); ctx.stroke(); ctx.restore();
    }
    ctx.drawImage(IC.canvas(w.icon, 128), x + 3, y + 3, s - 6, s - 6);
    if (F) IC.drawFit(ctx, F.icon, x + s * 0.2, y + s * 0.2, s * 0.42);
    if (w.def.unique) outlinedText(ctx, '✦', x + 6 * u, y + 15 * u, '#ffb0ff', 13 * u, 'left');
    const cdk = clamp(w.cd / w.cooldown(), 0, 1); if (cdk > 0) { ctx.fillStyle = 'rgba(0,0,0,0.4)'; ctx.fillRect(x, y + s * (1 - cdk), s, s * cdk); }
    ctx.strokeStyle = w.maxed ? '#ffd24a' : '#e8a040'; ctx.lineWidth = 2 * u; ctx.strokeRect(x, y, s, s);
    outlinedText(ctx, String(w.level), x + s - 4 * u, y + s - 4 * u, w.maxed ? '#ffd24a' : '#fff', 14 * u, 'right');
  }
  if (R.hasted()) outlinedText(ctx, '⚡×2', x + s + 10 * u, y + s / 2 + 5 * u, '#ffcf3a', 14 * u, 'left');
  if (R.weakUntil > R.time) outlinedText(ctx, '💢 -50% ' + Math.ceil(R.weakUntil - R.time) + 's', x + s + 10 * u, y + s / 2 + (R.hasted() ? 24 : 5) * u, '#ff6a6a', 14 * u, 'left');   // ToT's slap
  // passives
  x = 10 * u; y += s + 6 * u; const ps = 30 * u;
  for (const p of Game.C.passives) {
    const lv = R.passives[p.id]; if (!lv || p.id === R.bonusPassive) continue;
    ctx.fillStyle = 'rgba(40,30,15,0.7)'; ctx.fillRect(x, y, ps, ps);
    IC.drawFit(ctx, p.icon, x + ps / 2, y + ps / 2, ps * 0.9);
    outlinedText(ctx, String(lv), x + ps - 2 * u, y + ps - 2 * u, lv >= p.max ? '#ffd24a' : '#fff', 9 * u, 'right');
    x += ps + 3 * u;
  }
  if (R.bonusPassive) {   // 0.98.3: the Gladiatrool's characteristic: its own place, after the five's, wherever they stand; dark blue
    const p = Game.C.passives.find(q => q.id === R.bonusPassive), lv = R.passives[p.id], bx = 10 * u + 5 * (ps + 3 * u) + 4 * u;
    ctx.fillStyle = 'rgba(12,30,92,0.85)'; ctx.fillRect(bx, y, ps, ps);
    ctx.strokeStyle = '#12296e'; ctx.lineWidth = 3 * u; ctx.strokeRect(bx - u, y - u, ps + 2 * u, ps + 2 * u);
    ctx.strokeStyle = 'rgba(140,180,255,0.9)'; ctx.lineWidth = u; ctx.strokeRect(bx - 2.5 * u, y - 2.5 * u, ps + 5 * u, ps + 5 * u);
    IC.drawFit(ctx, p.icon, bx + ps / 2, y + ps / 2, ps * 0.9);
    outlinedText(ctx, String(lv), bx + ps - 2 * u, y + ps - 2 * u, lv >= p.max ? '#ffd24a' : '#fff', 9 * u, 'right');
  }
  // dofus eggs: a column on the right side, under the kamas
  if (R.dofus.length) { const step = 34 * u; let dy = H / 2 - (R.dofus.length * step) / 2 + step / 2;
    for (const d of R.dofus) { const x = W - 24 * u; ctx.drawImage(RCache.glow('rgba(255,230,150,0.45)'), x - 19 * u, dy - 19 * u, 38 * u, 38 * u); IC.drawFit(ctx, 'dofus_hd_' + d.icon, x, dy, 28 * u); dy += step; } }
  // 0.38: a relic just picked up: it rises in golden rays, with its bonus written in a frame.
  // (0.95: the caption hid the character — the relic in the middle, its message above it, smaller, lighter, shorter):
  // the relic springs out of the character and settles over its head (cy, 112 u above the screen's middle), the frame
  // slides down into place above the relic, its wood 78 % opaque; 3 s on screen instead of 3.8; under a banner shown at
  // the same time (Jorbak defeated…) both move down below it (R._banBot, the banner's bottom of the last frame)
  if (R.relicShow) { const D = 3, k = (performance.now() - R.relicShow.t0) / 1000; if (k > D) R.relicShow = null; else {
    const r = R.relicShow.r, a = Math.min(1, k * 3.5, (D - k) * 2.5), cx = W / 2, sc = 1 + Math.max(0, 0.45 - k) * 0.7;
    const e1 = 1 - Math.pow(1 - Math.min(1, k / 0.42), 3), out = Math.max(0, k - (D - 0.4)) / 0.4 * 10 * u;   // e1: the rise; out: a small lift as it fades
    const maxW = Math.min(W * 0.9, 600 * u) - 44 * u, f1 = 14 * u; let f2 = 20 * u; ctx.font = BAN_FONT(f2); const nw = ctx.measureText(L(r.name)).width; if (nw > maxW) f2 *= maxW / nw;   // (0.98.1: its name in the chat's lettering, BAN_FONT)
    const f3 = 15 * u, F3 = px_ => `${px_}px Lilita, DofusBold, sans-serif`; ctx.font = F3(f3); const dl = wrapLines(ctx, L(r.desc), maxW), d3 = f3 * 1.22;   // (0.98: the bonus in Lilita: rounder, easier to read than the announcements' font)
    ctx.font = BAN_FONT(f1); const w1 = ctx.measureText(T('relic_got')).width; ctx.font = BAN_FONT(f2); const w2 = ctx.measureText(L(r.name)).width; ctx.font = F3(f3);
    const bw = Math.min(W * 0.94, Math.max(w1, w2, ...dl.map(l => ctx.measureText(l).width)) + 44 * u), gap = 5 * u, h1 = f1 * 1.15, h2 = f2 * 1.2, h3 = dl.length * d3, pad = 9 * u, bh = pad * 2 + h1 + h2 + gap + h3;
    const top = Math.max(H / 2 - 112 * u - 40 * u - bh, R.bannerMsg && R._banBot ? R._banBot + 6 * u : 0, 8 * u), cy = top + bh + 40 * u - out;
    const py0 = (R.player.y - 30 - R.cam.y) * Game.zoom + H / 2, ry = lerp(py0, cy, e1);   // the relic's height: from the character to its place
    ctx.save(); ctx.globalAlpha = a * e1; ctx.translate(cx, ry); ctx.rotate(k * 0.6);
    for (let i = 0; i < 12; i++) { ctx.rotate(TAU / 12); ctx.fillStyle = i % 2 ? 'rgba(255,230,130,0.26)' : 'rgba(170,240,90,0.26)'; ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(-13 * u, -62 * u); ctx.lineTo(13 * u, -62 * u); ctx.closePath(); ctx.fill(); }
    ctx.restore(); ctx.save(); ctx.globalAlpha = a;
    ctx.drawImage(RCache.glow('rgba(255,230,140,0.85)'), cx - 50 * u, ry - 50 * u, 100 * u, 100 * u);
    IC.drawFit(ctx, IC.get('relic_hd_' + r.icon) ? 'relic_hd_' + r.icon : r.icon, cx, ry - Math.sin(Math.min(1, k * 2) * Math.PI) * 6 * u, 58 * u * sc);   // (0.61: its 400-px picture, build_iconhd091 relics)
    // (0.95: 'RELIQUE' over the relic's name, not beside it, all centred in a frame): three blocks in a banner's
    // frame — the word, the name (bigger, shrunk to fit), the bonus (wrapped), all in the announcements' font —, each centred by its ink
    const e2 = 1 - Math.pow(1 - Math.min(1, k / 0.3), 2), bx = cx - bw / 2, byy = top - (1 - e2) * 12 * u - out;
    ctx.globalAlpha = a * e2 * 0.6; annPanel(ctx, bx, byy, bw, bh, u, performance.now() / 1000, 'relic'); ctx.globalAlpha = a * e2;   // (see-through, not its sparks)
    ctx.textAlign = 'center'; let yy = byy + pad;
    annLine(ctx, T('relic_got'), cx, yy + h1 / 2 + annInk('H', f1, 700, BAN_FONT(100)).dy, f1, ANN.plate, BAN_FONT); yy += h1;   // (0.98.2: the victory's gold, the chat's lettering)
    { const ny = yy + h2 / 2 + annInk('H', f2, 700, BAN_FONT(100)).dy;
      annLine(ctx, L(r.name), cx, ny, f2, ANN.plate, BAN_FONT); } yy += h2 + gap;
    const i3 = annInk('H', f3, 700, F3(100)).dy; ctx.font = F3(f3); ctx.textBaseline = 'middle'; ctx.lineJoin = 'round'; ctx.lineWidth = Math.max(2, f3 * 0.24); ctx.strokeStyle = 'rgba(30,8,0,0.92)';
    dl.forEach((l, i) => { const ly = yy + d3 * (i + 0.5) + i3; ctx.strokeText(l, cx, ly); ctx.fillStyle = '#fff6dc'; ctx.fillText(l, cx, ly); });
    ctx.textAlign = 'left';
    ctx.restore(); } }
  // relics: a column on the left side, at the Dofus' height (0.38)
  if (R.relics && R.relics.length) { const step = 34 * u; let ry = H / 2 - (R.relics.length * step) / 2 + step / 2, x = 24 * u;
    for (const r of R.relics) { ctx.fillStyle = 'rgba(40,28,12,0.7)'; ctx.beginPath(); ctx.arc(x, ry, 14 * u, 0, TAU); ctx.fill(); ctx.strokeStyle = '#ffcf3a'; ctx.lineWidth = 1.5 * u; ctx.stroke(); IC.drawFit(ctx, r.icon, x, ry, 24 * u); ry += step; } }
  const pw = [];
  for (const k in R.powers) { const pr = R.powers[k]; pw.push([Game.C.drops[k], Math.max(0, pr.until - R.time), pr.charges]); }
  for (const a of R.allies) if (a.kind !== 'drago') pw.push([a.kind === 'arakne' || a.kind === 'majeure' ? Game.C.drops.arakne : Game.C.drops.chaferfu, Math.max(0, a.until - R.time), undefined, a.kind === 'lancier' ? '#ffcf3a' : a.kind === 'majeure' ? '#c47bff' : null]);   // the Dragodinde stays all run: no timer
  if (R.batofuUntil > R.time) pw.push([{ icon: null, it: 'it_53_120', color: '#9fe0ff' }, R.batofuUntil - R.time, undefined, '#9fe0ff']);
  if (R.kboostUntil > R.time) pw.push([{ icon: null, it: Game.C.kamaBoost.icon, color: '#ffd700' }, R.kboostUntil - R.time, undefined, '#ffd700']);
  if (pw.length) {
    x = 10 * u; y += ps + 10 * u; const is = 34 * u;
    for (const [d, left, ch, col] of pw) {
      ctx.drawImage(IC.canvas(d.it || d.item || ('sp_' + d.icon), 96), x, y, is, is);
      if (!d.it && !d.item && !(IC.get('sp_' + d.icon) || [])[7]) { ctx.strokeStyle = col || d.color; ctx.lineWidth = 2 * u; ctx.strokeRect(x, y, is, is); }
      outlinedText(ctx, Math.ceil(left) + 's', x + is / 2, y + is + 11 * u, '#fff', 10 * u, 'center');
      if (ch !== undefined) outlinedText(ctx, '×' + ch, x + is - 2 * u, y + 10 * u, d.color, 10 * u, 'right');
      x += is + 8 * u;
    }
  }
  // boss bar
  // one bar per living boss (Minotot and Minotoror together: two bars), at most three
  // (0.34: the sub-bosses too, the Tofu Mutant: a green bar under the bosses' red ones)
  const bars = R.bossAlive.slice(0, 5); if (R.mutant && !R.mutant.dying && R.mutant.hp > 0 && bars.length < 6) bars.push(R.mutant);   // (0.71: up to 5 boss bars)
  for (let bi = 0; bi < bars.length; bi++) {
    const b = bars[bi], sub = !b.boss; const bw = Math.min((sub ? 380 : 520) * u, W * 0.6), bx = (W - bw) / 2, by = yb + hb + 36 * u + bi * 24 * u;
    drawBossHud(ctx, b, bx, by, bw, 16 * u, u, performance.now() / 1000);
    if (!(R.time - (b._hpT || -9) < 0.1) || b.hp <= 0) { b._hpT = R.time; b._hpS = `${L(b.def.name)} — ${fmtNum(Math.max(0, b.hp))} / ${fmtNum(b.maxHp)}`; }   // (0.98.1: its text made again 10 times a second at most, not on every hit: a new picture each time)
    outlinedText(ctx, b._hpS, W / 2, by + 13 * u, '#fff', 12 * u, 'center');
  }
  // heart (HP) bottom center, Dofus style
  const P = R.player, st = R.stats;
  // 0.60: the client's banner heart as a jar of life: the red liquid fills it up to the life left, its surface waves,
  // bubbles rise in it, the empty part is the heart in grey; it beats (faster and harder under 30 %), swells and flashes
  // white for a moment when hit, and glows green when healed
  const hk = clamp(P.hp / st.maxHp, 0, 1), tt = performance.now() / 1000;
  if (R._hpPrev !== undefined && P.hp > R._hpPrev + 0.5) R._healT = tt; R._hpPrev = P.hp;
  const bpm = hk < 0.3 ? 2.2 + (0.3 - hk) * 6 : 1.1, ph = (tt * bpm) % 1, beat = (ph < 0.12 ? Math.sin(ph / 0.12 * Math.PI) : ph > 0.2 && ph < 0.3 ? 0.5 * Math.sin((ph - 0.2) / 0.1 * Math.PI) : 0) * (hk < 0.3 ? 0.09 : 0.035);
  const hitK = clamp(1 - (R.time - P.lastHit) / 0.3, 0, 1), HS = 1.25 * u * (1 + beat + hitK * 0.08), hx = W / 2, hy = H - 56 * u;
  const hf = IC.get('Heart');
  if (hf && hk < 1) {
    const hh = hf[3] / (hf[6] || 1) * HS, hw = hf[2] / (hf[6] || 1) * HS, x0 = hx - hw / 2, x1 = hx + hw / 2, y1 = hy + hh / 2;
    const top = y1 - hh * (0.06 + 0.9 * hk), amp = hk > 0.02 ? 2.2 * u * (1 + hitK * 2) : 0;
    ctx.save(); ctx.globalAlpha = 0.3; IC.draw(ctx, 'Heart', hx, hy, HS); ctx.globalAlpha = 0.8; drawTinted(ctx, 'Heart', 'grey', hx, hy, HS); ctx.restore();   // (the empty part: grey glass, a little pink)
    ctx.save(); ctx.beginPath(); ctx.moveTo(x0 - 2, y1 + 2);
    for (let x = x0 - 2; x <= x1 + 2; x += 3 * u) ctx.lineTo(x, top + Math.sin(x / (9 * u) + tt * 3.2) * amp + Math.sin(x / (5 * u) - tt * 4.6) * amp * 0.4);
    ctx.lineTo(x1 + 2, y1 + 2); ctx.closePath(); ctx.clip();
    IC.draw(ctx, 'Heart', hx, hy, HS);
    ctx.fillStyle = 'rgba(255,190,190,0.55)';   // (bubbles rising in the liquid)
    for (let i = 0; i < 5; i++) { const bp = (tt * (0.35 + i * 0.07) + i * 0.37) % 1, bx = x0 + hw * (0.25 + 0.5 * ((i * 0.618) % 1)) + Math.sin(tt * 2 + i) * 2 * u, by = y1 - hh * 0.08 - bp * (y1 - top); if (by > top + 2 * u) { ctx.beginPath(); ctx.arc(bx, by, (1 + (i % 3) * 0.6) * u, 0, TAU); ctx.fill(); } }
    ctx.restore();
  } else IC.draw(ctx, 'Heart', hx, hy, HS);
  if (hitK > 0) { ctx.save(); ctx.globalAlpha = hitK * 0.7; ctx.globalCompositeOperation = 'lighter'; IC.draw(ctx, 'Heart', hx, hy, HS); ctx.restore(); }
  { const hl = clamp(1 - (tt - (R._healT || -9)) / 0.6, 0, 1); if (hl > 0) { ctx.save(); ctx.globalAlpha = hl * 0.8; ctx.drawImage(RCache.glow('rgba(120,255,140,0.9)'), hx - 46 * u, hy - 46 * u, 92 * u, 92 * u); ctx.restore(); } }
  outlinedText(ctx, `${Math.ceil(P.hp)}`, hx, hy + 6 * u, '#fff', 20 * u, 'center');
  outlinedText(ctx, `/${st.maxHp}`, hx, hy + 23 * u, '#ffd9d9', 11 * u, 'center');
  // dodge (Space / double tap / triggers), next to the heart
  { const D = Game.C.dodge, ds = 46 * u, dx = hx + 78 * u, dyy = hy - ds / 2 + 4 * u, left = Math.max(0, P.dodgeReady - R.time);
    // an item (feather) on a round dark plate with a gold rim, so it reads on any ground
    if (left > 0) R._dashWait = true; else if (R._dashWait) { R._dashWait = false; R._dashPop = R.time; }   // (0.98: verdant, a pop when it is ready again)
    hudPlate(ctx, dx, dyy + ds / 2, ds / 2, u, R.time, left <= 0, clamp(1 - (R.time - (R._dashPop || -9)) / 0.45, 0, 1));
    const bat = R.batofuUntil > R.time;   // 0.34: the Batofu feather replaces the Tofu's while it is active
    ctx.save(); ctx.translate(dx, dyy + ds / 2); if (left <= 0) { ctx.rotate(Math.sin(R.time * 2.4) * 0.09); ctx.translate(0, Math.sin(R.time * 3.1) * 1.2 * u); }   // (it sways while ready)
    ctx.drawImage(IC.canvas(bat ? 'it_53_120' : D.icon, 96), -ds * 0.36, -ds * 0.36, ds * 0.72, ds * 0.72); ctx.restore();
    if (bat) { ctx.strokeStyle = '#9fe0ff'; ctx.lineWidth = 2.5 * u; ctx.beginPath(); ctx.arc(dx, dyy + ds / 2, ds / 2 + 2 * u, -Math.PI / 2, -Math.PI / 2 + TAU * clamp((R.batofuUntil - R.time) / (R.batofuDur || 10), 0, 1)); ctx.stroke(); }
    if (left > 0) { const cyy = dyy + ds / 2; ctx.fillStyle = 'rgba(4,22,10,0.62)'; ctx.beginPath(); ctx.moveTo(dx, cyy); ctx.arc(dx, cyy, ds / 2, -Math.PI / 2, -Math.PI / 2 + TAU * left / D.cd); ctx.closePath(); ctx.fill();
      ctx.strokeStyle = '#c8f060'; ctx.lineWidth = 2.6 * u; ctx.lineCap = 'round'; ctx.beginPath(); ctx.arc(dx, cyy, ds / 2 - 1.2 * u, -Math.PI / 2 + TAU * left / D.cd, Math.PI * 1.5); ctx.stroke(); ctx.lineCap = 'butt';   // (what has come back, lime)
      ctx.textAlign = 'center'; annLine(ctx, String(Math.ceil(left)), dx, cyy + annInk('8', 19 * u, 700).dy, 19 * u, '#f4ffd0'); ctx.textAlign = 'left'; }
    drawKeyHint(ctx, 'dash', dx, dyy + ds + 17 * u, u, false);
    // 0.34: the potion (0.53; bread before) / kamas auto-choice (when every upgrade is maxed), on / off with R / Y (0.60) / a click
    const ap = Store.data.settings.autoPick, ak = ap || Store.data.settings.lastAutoPick;
    if (ak && R.maxedAll) { const as = 36 * u, ax = dx + 62 * u, ay = dyy + ds / 2;
      R.hudAuto = { x: ax, y: ay, r: as / 2 };
      hudPlate(ctx, ax, ay, as / 2, u, R.time, !!ap);   // (0.98: verdant)
      if (!ap) ctx.globalAlpha = 0.45; ctx.drawImage(IC.canvas(ak === 'kamas' ? 'KamaSymbol' : potionIcon(), 96), ax - as * 0.32, ay - as * 0.32, as * 0.64, as * 0.64); ctx.globalAlpha = 1;
      if (!ap) { ctx.strokeStyle = '#ff4a3a'; ctx.lineWidth = 3 * u; ctx.beginPath(); ctx.moveTo(ax - as * 0.3, ay - as * 0.3); ctx.lineTo(ax + as * 0.3, ay + as * 0.3); ctx.stroke(); }
      const d = Input.dev; if (d === 'pad') drawPadBtn(ctx, 'Y', ax, ay + as / 2 + 13 * u, u); else if (d !== 'touch') drawKeyCap(ctx, 'R', ax, ay + as / 2 + 13 * u, u);
    } else R.hudAuto = null; }
  // spells that move the character (Bond, Assaut, Vol de Pièces): on/off switch to the left of the heart (Q / A / L / tap)
  { const ms = R.moveSpell();
    if (ms) {
      const ds = 46 * u, dx = hx - 78 * u, dyy = hy - ds / 2 + 4 * u;
      R.hudMove = { x: dx, y: dyy + ds / 2, r: ds / 2 };
      hudPlate(ctx, dx, dyy + ds / 2, ds / 2 + 2 * u, u, R.time, !R.moveOff);   // (0.98: on its verdant plate)
      if (R.moveOff) ctx.globalAlpha = 0.45;
      ctx.drawImage(IC.canvas('sp_' + ms.def.icon, 96), dx - ds * 0.44, dyy + ds * 0.06, ds * 0.88, ds * 0.88);
      ctx.globalAlpha = 1;
      if (R.moveOff) { ctx.strokeStyle = '#ff4a3a'; ctx.lineWidth = 4 * u; ctx.beginPath(); ctx.moveTo(dx - ds * 0.34, dyy + ds * 0.16); ctx.lineTo(dx + ds * 0.34, dyy + ds * 0.84); ctx.stroke(); }
      drawKeyHint(ctx, 'move', dx, dyy + ds + 17 * u, u, R.moveOff);
    } else R.hudMove = null; }
  // minimap
  if (R.mini) {
    const mw = Math.min(240 * u, W * 0.28, H * 0.42), mh = mw * R.world.h / R.world.w, mx = W - mw - 10 * u, my = H - mh - 10 * u;   // (0.98.2: H: a phone lying down)
    ctx.globalAlpha = 0.85; ctx.drawImage(R.mini, mx, my, mw, mh); ctx.globalAlpha = 1;
    ctx.strokeStyle = '#c8a46a'; ctx.lineWidth = 2; ctx.strokeRect(mx, my, mw, mh);
    const k = mw / R.world.w;
    ctx.strokeStyle = 'rgba(255,255,255,0.7)'; ctx.lineWidth = 1; ctx.strokeRect(mx + (R.cam.x - Game.viewW / 2) * k, my + (R.cam.y - Game.viewH / 2) * k, Game.viewW * k, Game.viewH * k);
    for (const b of R.bossAlive) { ctx.fillStyle = '#ff3030'; ctx.beginPath(); ctx.arc(mx + b.x * k, my + b.y * k, 4 * u, 0, TAU); ctx.fill(); }
    for (const q of R.pickups) if ((q.kind === 'chest' && q.boss) || q.kind === 'dofus') {   // the boss chests and dropped Dofus, blinking
      const bl = 0.6 + 0.4 * Math.sin(R.time * 8); ctx.fillStyle = q.kind === 'dofus' ? `rgba(255,60,60,${bl})` : `rgba(255,200,40,${bl})`;
      ctx.strokeStyle = '#000'; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.arc(mx + q.x * k, my + q.y * k, 4.5 * u, 0, TAU); ctx.fill(); ctx.stroke();
    }
    for (const q of R.pickups) if (q.kind === 'booster' || q.kind === 'relic' || q.kind === 'gladia') {   // 0.37: the TTG booster (green) and the relics (orange), on the minimap too
      const x = mx + q.x * k, y = my + q.y * k, r = 4.5 * u + Math.sin(R.time * 6); ctx.fillStyle = q.kind === 'booster' ? '#9cff6a' : q.kind === 'gladia' ? '#6fa0ff' : '#ffb03a'; ctx.strokeStyle = '#000'; ctx.lineWidth = 1.5;
      if (q.kind === 'booster') { ctx.fillRect(x - r * 0.7, y - r, r * 1.4, r * 2); ctx.strokeRect(x - r * 0.7, y - r, r * 1.4, r * 2); } else { ctx.beginPath(); ctx.moveTo(x, y - r); ctx.lineTo(x + r, y); ctx.lineTo(x, y + r); ctx.lineTo(x - r, y); ctx.closePath(); ctx.fill(); ctx.stroke(); }
    }
    if (R.door) { ctx.fillStyle = '#d7a6ff'; ctx.beginPath(); ctx.arc(mx + R.door.x * k, my + R.door.y * k, 4 * u + Math.sin(R.time * 6), 0, TAU); ctx.fill(); }
    // 0.26: the Tofu Mutant, the Coffre Animé (green / red dots) and the cross of a treasure map
    for (const m of R.mobs) if (m.def.special && !m.dying) { ctx.fillStyle = m.def.id === 'coffre_anime' ? '#ff6a4a' : '#9cff6a'; ctx.beginPath(); ctx.arc(mx + m.x * k, my + m.y * k, 4 * u + Math.sin(R.time * 8), 0, TAU); ctx.fill(); }
    if (R.merchant) { const x = mx + R.merchant.x * k, y = my + R.merchant.y * k; ctx.fillStyle = '#ffd24a'; ctx.strokeStyle = '#3a2408'; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.arc(x, y, 4.5 * u + Math.sin(R.time * 6), 0, TAU); ctx.fill(); ctx.stroke(); ctx.fillStyle = '#3a2408'; ctx.font = `bold ${7 * u}px sans-serif`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText('K', x, y + 0.5); }   // 0.33: the skin merchant
    if (R.tmapHere) { const x = mx + R.tmapHere.x * k, y = my + R.tmapHere.y * k, a = 4 * u; ctx.strokeStyle = '#ff2a1a'; ctx.lineWidth = 2.5 * u; ctx.beginPath(); ctx.moveTo(x - a, y - a); ctx.lineTo(x + a, y + a); ctx.moveTo(x + a, y - a); ctx.lineTo(x - a, y + a); ctx.stroke(); }
    ctx.fillStyle = '#fff'; ctx.strokeStyle = '#000'; ctx.beginPath(); ctx.arc(mx + P.x * k, my + P.y * k, 3.5 * u, 0, TAU); ctx.fill(); ctx.stroke();
  }
  drawEdgeArrows(ctx, R, W, H, u);
  // door arrow indicator
  if (R.door) {
    const dx = (R.door.x - R.cam.x) * Game.zoom, dy = (R.door.y - R.cam.y) * Game.zoom;
    if (Math.abs(dx) > W / 2 - 40 || Math.abs(dy) > H / 2 - 40) {
      const a = Math.atan2(dy, dx); const rx = W / 2 - 50 * u, ry = H / 2 - 50 * u;
      const k = Math.min(rx / Math.abs(Math.cos(a) || 1e-6), ry / Math.abs(Math.sin(a) || 1e-6));
      const ax = W / 2 + Math.cos(a) * k, ay = H / 2 + Math.sin(a) * k;
      ctx.save(); ctx.translate(ax, ay); ctx.rotate(a); ctx.fillStyle = '#d7a6ff'; ctx.strokeStyle = '#000'; ctx.lineWidth = 2;
      ctx.beginPath(); ctx.moveTo(18 * u, 0); ctx.lineTo(-10 * u, -12 * u); ctx.lineTo(-4 * u, 0); ctx.lineTo(-10 * u, 12 * u); ctx.closePath(); ctx.fill(); ctx.stroke(); ctx.restore();
    }
  }
  // chat
  if (Store.data.settings.chat) {
    // (0.98.2: an upright screen: over the bottom row, the screen's whole width; beside the heart it wrapped every 3 words)
    const cb = narrow ? H - Math.max(112 * u, (R.mini ? Math.min(240 * u, W * 0.28, H * 0.42) * R.world.h / R.world.w : 0) + 18 * u) : H;
    let cy = cb - 24 * u; const now = R.time;   // v2.0: a bit bigger
    // 0.94 (quality audit): a long line ran under the heart and the potion (their '/62' hidden): lines wrap before the
    // bottom-centre HUD (the heart at W / 2, the move-spell switch left of it)
    const cw = narrow ? W - 24 * u : Math.max(160 * u, W / 2 - 116 * u), f0 = ctx.font; ctx.font = hudFont(13 * u);
    { let n = 0, al = 0; for (const c of R.chats) { const age = now - c.t, lf = c.life || 14; if (age > lf) continue; n += c._w === cw ? c._ls.length : 1; al = Math.max(al, age > lf - 3 ? (lf - age) / 3 : 1); }   // (0.98: a soft shade behind the lines: they read on bright grass)
      if (n) { const hh = n * 18 * u + 26 * u; ctx.globalAlpha = 0.55 * al; ctx.drawImage(RCache.glow('rgba(0,10,4,0.85)'), -cw * 0.25, cb - hh - 6 * u, cw * 1.45, hh * 1.6); ctx.globalAlpha = 1; } }
    for (let i = R.chats.length - 1; i >= 0; i--) {
      const c = R.chats[i]; const age = now - c.t, lf = c.life || 14; if (age > lf) continue;   // (0.98.1: lf, an announcement's explanation 28 s)
      ctx.globalAlpha = age > lf - 3 ? (lf - age) / 3 : 1;
      const ls = c._w === cw ? c._ls : (c._w = cw, c._ls = wrapLines(ctx, c.msg, cw));
      for (let j = ls.length - 1; j >= 0; j--) { outlinedText(ctx, ls[j], 12 * u, cy, c.color, 13 * u, 'left', 'rgba(0,0,0,0.9)'); cy -= 18 * u; }
    }
    ctx.font = f0;
    ctx.globalAlpha = 1;
  }
  // achievement toasts: stacked one above the other when several unlock together
  if (R.achToasts && R.achToasts.length) {
    R.achToasts = R.achToasts.filter(a => a.t <= 4.4);
    const bw = 300 * u, bh = 46 * u, bx = (W - bw) / 2;
    R.achToasts.forEach((a, i) => {
      if (i > 0 && R.achToasts[i - 1].t < 0.25) return;                 // they arrive one after the other
      const now = performance.now(); if (a.t0 === undefined) a.t0 = now - (a.t || 0) * 1000; a.t = (now - a.t0) / 1000;   // (real time: it was 1/60 per drawn frame, shorter on 144 Hz screens)
      const k = a.t < 0.3 ? a.t / 0.3 : a.t > 3.9 ? (4.4 - a.t) / 0.5 : 1; ctx.globalAlpha = clamp(k, 0, 1);
      const by = H - 150 * u - i * (bh + 6 * u);
      ctx.fillStyle = 'rgba(30,20,8,0.88)'; ctx.fillRect(bx, by, bw, bh); ctx.strokeStyle = '#ffd24a'; ctx.lineWidth = 2; ctx.strokeRect(bx, by, bw, bh);
      IC.drawFit(ctx, a.a.icon, bx + 24 * u, by + bh / 2, 34 * u);
      outlinedText(ctx, '🏆 ' + T('achievements'), bx + 48 * u, by + 17 * u, '#ffd24a', 11 * u); outlinedText(ctx, L(a.a.name), bx + 48 * u, by + 35 * u, '#fff', 14 * u);
      ctx.globalAlpha = 1;
    });
  }
  // banner
  if (R.bannerMsg) {
    const b = R.bannerMsg; const k = b.t < 0.3 ? b.t / 0.3 : b.t > 2.6 ? (3.2 - b.t) / 0.6 : 1, BS = b.kind === 'boss' ? 1.1 : 1;   // (0.98: a boss's arrival 10 % bigger, its light green frame)
    ctx.globalAlpha = clamp(k, 0, 1);
    // a Dofus Retro style ribbon: dark wood panel, gold edge, the message (centre of the screen for ToT's rewards)
    // (0.34: a long message — the Batofu feather in every language, a phone screen — wraps on several lines inside the box)
    // (0.95: the message in the announcements' Cinzel, juice.js annLine; it slides down a little as it comes in)
    const nb = Math.min(4, R.bossAlive.length + (R.mutant ? 1 : 0)), by0 = Math.max(b.center ? H * 0.24 : H * 0.17, 118 * u + nb * 24 * u) - (b.t < 0.3 ? (1 - b.t / 0.3) * (1 - b.t / 0.3) * 14 * u : 0); let fs = 22 * u * BS;   // (0.35: higher, out of the middle of the view, under the boss bars)
    ctx.font = BAN_FONT(fs);
    const full = b.pre ? b.pre[0] + ' ' + b.text : b.text;   // (0.98.1: b.pre, a word before the name in its own colour)
    const maxW = Math.min(W * 0.92, 900 * u) - 70 * u; let lines = wrapLines(ctx, full, maxW);
    if (lines.length > 2) { fs = 19 * u * BS; ctx.font = BAN_FONT(fs); lines = wrapLines(ctx, full, maxW); }
    // (0.95: the messages sat low and off-centre in their frame: the frame was laid from a guess of the text's
    // height; now the block of lines — line height lh, the capitals' ink centred on each line, annInk — is centred in it)
    const lh = fs * 1.2, tw = Math.max(...lines.map(l => ctx.measureText(l).width)) + 70 * u * BS, ph = 46 * u * BS + (lines.length - 1) * lh, px = (W - tw) / 2, py = by0 - 46 * u * BS * 0.68;
    ctx.globalAlpha = clamp(k, 0, 1) * (b.kind === 'boss' ? 0.9 : 1); annPanel(ctx, px, py, tw, ph, u, performance.now() / 1000, b.kind === 'boss' ? 'boss' : null); R._banBot = py + ph; ctx.globalAlpha = clamp(k, 0, 1);
   // (0.95: a relic's caption shown meanwhile goes under it)
    const dy = annInk('H', fs, 700, BAN_FONT(100)).dy, y0 = py + ph / 2 - (lines.length - 1) * lh / 2 + dy;
    ctx.textAlign = 'center';
    if (b.kind === 'boss' && !Game.lowFx) { ctx.save(); ctx.font = BAN_FONT(fs); ctx.textBaseline = 'middle'; ctx.shadowColor = '#f5b52e'; ctx.shadowBlur = (16 + 5 * Math.sin(R.time * 5)) * u; ctx.fillStyle = '#f5b52e'; lines.forEach((l, i) => { ctx.fillText(l, W / 2, y0 + i * lh); ctx.fillText(l, W / 2, y0 + i * lh); }); ctx.restore(); }   // (its words glowing in their colour, under the outline)
    lines.forEach((l, i) => {
      if (!(b.pre && i === 0 && l.startsWith(b.pre[0] + ' '))) { annLine(ctx, l, W / 2, y0 + i * lh, fs, ANN.plate, BAN_FONT); return; }   // (0.98.2: every central message in the victory's gold, b.color stays the chat's)
      ctx.font = BAN_FONT(fs); const x0 = W / 2 - ctx.measureText(l).width / 2, w0 = ctx.measureText(b.pre[0] + ' ').width; ctx.textAlign = 'left';
      annLine(ctx, b.pre[0], x0, y0, fs, b.pre[1], BAN_FONT); annLine(ctx, l.slice(b.pre[0].length + 1), x0 + w0, y0, fs, ANN.plate, BAN_FONT); ctx.textAlign = 'center';
    }); ctx.textAlign = 'left';
    ctx.globalAlpha = 1;
  }
  // 0.98.2: the Sablier's freeze, what is left of it read from the freeze itself (Run.freezeUntil: every source of it)
  if (R.sandFreeze) { const left = R.freezeUntil - R.time; if (left <= 0) { R.sandFreeze = false; R._sandA = 0; } else { R._sandA = Math.min(1, (R._sandA || 0) + 0.05); drawSandTimer(ctx, R, W, H, u, left); } }
  // touch joystick
  if (Input.touch.active) {
    ctx.globalAlpha = 0.35; ctx.fillStyle = '#fff';
    ctx.beginPath(); ctx.arc(Input.touch.sx, Input.touch.sy, 55 * u, 0, TAU); ctx.fill();
    ctx.globalAlpha = 0.6; ctx.beginPath(); ctx.arc(Input.touch.sx + Input.touch.dx * 50 * u, Input.touch.sy + Input.touch.dy * 50 * u, 22 * u, 0, TAU); ctx.fill(); ctx.globalAlpha = 1;
  }
}

// the Sablier's timer: see-through ice, high up under the banners' place, time standing still round it: a slow frost halo, the
// drop's own hourglass gone blue turning round it on a tilted orbit (behind the figures, then in front), crystals hanging in the
// air, barely moving, each twinkling in its turn. Cached pictures only
function sandIce() {   // the hourglass of the drop in ice blue, made once
  let c = RCache.m.get('sandIce'); if (c) return c; const src = Game.icons && Game.icons.canvas(Game.C.sablierItem || 'sp_100', 96); if (!src) return null;
  c = document.createElement('canvas'); c.width = src.width; c.height = src.height; const g = c.getContext('2d');
  g.drawImage(src, 0, 0); g.globalCompositeOperation = 'source-atop'; g.fillStyle = 'rgba(95,195,255,0.5)'; g.fillRect(0, 0, c.width, c.height);
  return RCache.put('sandIce', c);
}
function drawSandTimer(ctx, R, W, H, u, left) {
  const fs = 36 * u, nb = Math.min(4, R.bossAlive.length + (R.mutant ? 1 : 0)), y = Math.max(H * 0.17, 118 * u + nb * 24 * u) + 54 * u, t = performance.now() / 1000, a = 0.74 * R._sandA * Math.min(1, left / 0.4), s = left.toFixed(2).replace('.', LANG === 'en' ? '.' : ',') + ' s';
  ctx.save(); ctx.font = hudFont(fs); ctx.textAlign = 'left'; ctx.textBaseline = 'middle'; ctx.lineJoin = 'round';
  const tw = ctx.measureText('8,88 s').width, x = W / 2 - tw / 2, rx = tw * 0.82, ry = fs * 1.02, ice = sandIce(), star = panelStar('120,200,255'), hs = fs * 0.78;   // (a fixed left edge: the figures' widths differ, a centred text shook)
  ctx.globalAlpha = a * (0.5 + 0.08 * Math.sin(t * 1.3)); ctx.drawImage(RCache.glow('rgba(110,195,255,0.8)'), W / 2 - rx * 1.5, y - ry * 1.5, rx * 3, ry * 3);
  ctx.globalAlpha = a * 0.28; ctx.strokeStyle = '#bfe8ff'; ctx.lineWidth = 1.2 * u; ctx.setLineDash([3 * u, 7 * u]); ctx.lineDashOffset = t * 4 * u; ctx.beginPath(); ctx.ellipse(W / 2, y, rx, ry, -0.1, 0, TAU); ctx.stroke(); ctx.setLineDash([]);
  const orbit = back => { if (!ice || Game.minFx) return; for (let i = 0, N = Game.lowFx ? 3 : 5; i < N; i++) { const an = t * 0.42 + i / N * TAU, sy = Math.sin(an); if ((sy < 0) !== back) continue;
    const c = Math.cos(an), ox = c * rx, oy = sy * ry, px = W / 2 + ox * Math.cos(0.1) + oy * Math.sin(0.1), py = y - ox * Math.sin(0.1) + oy * Math.cos(0.1), k = 0.8 + 0.28 * sy, sz = hs * k;
    ctx.save(); ctx.globalAlpha = Math.min(1, a * (1.1 + 0.25 * sy)); ctx.translate(px, py); ctx.rotate(Math.sin(t * 0.7 + i * 1.7) * 0.5 + i); ctx.drawImage(ice, -sz / 2, -sz / 2, sz, sz); ctx.restore(); } };
  orbit(true);
  const g = ctx.createLinearGradient(0, y - fs * 0.48, 0, y + fs * 0.42); for (const [o, c] of ANN.ice.stops) g.addColorStop(o, c);
  ctx.globalAlpha = a; ctx.lineWidth = fs * 0.13; ctx.strokeStyle = ANN.ice.edge; ctx.strokeText(s, x, y); ctx.fillStyle = g; ctx.fillText(s, x, y);
  orbit(false);
  if (!Game.minFx) for (let i = 0, N = Game.lowFx ? 10 : 22; i < N; i++) {
    const h0 = panelHash(i + 200), h1 = panelHash(i + 230), h2 = panelHash(i + 260), an = h0 * TAU, d = 0.55 + 0.85 * h1, sx = W / 2 + Math.cos(an) * rx * d * 1.15 + Math.sin(t * 0.18 + i) * 4 * u, sy = y + Math.sin(an) * ry * d * 1.25 + Math.cos(t * 0.15 + i * 1.3) * 3 * u - ((t * 0.05 + h2) % 1) * 6 * u;
    const tw2 = Math.pow(0.5 + 0.5 * Math.sin(t * (0.7 + h2) + i * 2.1), 3), sz = (7 + 11 * h2) * u * (0.55 + 0.45 * tw2); ctx.globalAlpha = Math.min(1, a * 1.3) * (0.12 + 0.88 * tw2); ctx.drawImage(star, sx - sz / 2, sy - sz / 2, sz, sz);
  }
  ctx.restore();
}

// 0.71: the fart puff in a very dark orange (the client's 'Lâcher les gaz' puff, multiplied once, cached)
function orangePuff(col = '#b0420c') {   // (0.95: col, the Pwout + Cawotte fusion's red-brown)
  const key = 'puffOr' + col; let c = RCache.m.get(key); if (c) return c; const src = Game.icons && Game.icons.canvas && Game.icons.canvas('fx_puff', 256); if (!src) return null;
  c = document.createElement('canvas'); c.width = src.width; c.height = src.height; const g = c.getContext('2d');
  g.drawImage(src, 0, 0); g.globalCompositeOperation = 'multiply'; g.fillStyle = col; g.fillRect(0, 0, c.width, c.height); g.globalCompositeOperation = 'destination-in'; g.drawImage(src, 0, 0);
  return RCache.put(key, c);
}
// 0.96 (a big violet fireball of chaos and void, LoL / Aion-like): a dark void core with a bright rim inside a
// violet blaze, light and dark violet flame tongues turning, flickering and streaming backwards, a see-through halo,
// sparks circling the core, and a trail of fading glows along its path (p.trail, world points). About four times the
// Flamiche's fireball. The violet is laid normally (added light turned it white on bright grounds), only the sparks and
// highlights add light. Cached glows and one-colour arcs only (PixiJS quads)
function drawChaosBall(ctx, p, t, ang) {
  const s = p.size, e = t - p.t0, tr = p.trail || [], GL = RCache.glow('rgba(176,92,255,0.95)'), GD = RCache.glow('rgba(84,16,176,0.95)');
  for (let i = 0; i < tr.length; i++) { const q = (i + 1) / (tr.length + 1), w = s * (0.3 + 0.7 * q); ctx.globalAlpha = 0.34 * q; ctx.drawImage(i % 2 ? GL : GD, tr[i][0] - p.x - w, tr[i][1] - p.y - w, w * 2, w * 2); }
  const pu = 1 + 0.07 * Math.sin(e * 11), H = s * 2.1 * pu;
  ctx.globalAlpha = 0.5; ctx.drawImage(RCache.glow('rgba(118,36,214,0.8)'), -H, -H, H * 2, H * 2);   // the halo
  for (let i = 0; i < 10; i++) {   // flame tongues: half round the ball, half streaming behind it
    const back = i % 2, fl = 0.65 + 0.35 * Math.abs(Math.sin(e * (7 + i) + i * 1.7)), an = back ? ang + Math.PI + (i - 5) * 0.16 + Math.sin(e * 5 + i) * 0.15 : i * TAU / 10 + e * 2.2;
    const L = s * (back ? 1.55 : 1.0) * fl, W = s * (back ? 0.46 : 0.55) * fl;
    ctx.save(); ctx.rotate(an); ctx.globalAlpha = back ? 0.7 : 0.8; ctx.drawImage(i % 4 < 2 ? GL : GD, s * 0.2, -W / 2, L, W); ctx.restore();
  }
  const B = s * 1.1; ctx.globalAlpha = 0.95; ctx.drawImage(GL, -B, -B, B * 2, B * 2);   // the blaze
  ctx.globalAlpha = 0.9; ctx.drawImage(GD, -B * 0.8, -B * 0.8, B * 1.6, B * 1.6);
  const V = s * 0.6 * (1 + 0.05 * Math.sin(e * 17)); ctx.globalAlpha = 0.9; ctx.drawImage(RCache.glow('rgba(20,0,40,0.98)'), -V, -V, V * 2, V * 2);   // the void inside
  ctx.globalAlpha = 0.6 + 0.25 * Math.sin(e * 9); ctx.strokeStyle = '#e6c6ff'; ctx.lineWidth = 2.5; ctx.beginPath(); ctx.arc(0, 0, s * 0.48, 0, TAU); ctx.stroke();   // its bright rim
  ctx.globalCompositeOperation = 'lighter';
  for (let i = 0; i < 3; i++) { const a = -e * 6 + i * TAU / 3, w = s * 0.2; ctx.globalAlpha = 0.85; ctx.drawImage(RCache.glow('rgba(240,214,255,0.95)'), Math.cos(a) * s * 0.42 - w, Math.sin(a) * s * 0.42 - w, w * 2, w * 2); }
  { const w = s * 0.5, fx = Math.cos(ang) * s * 0.55, fy = Math.sin(ang) * s * 0.55; ctx.globalAlpha = 0.45; ctx.drawImage(RCache.glow('rgba(214,170,255,0.9)'), fx - w, fy - w, w * 2, w * 2); }   // (its front lit)
  ctx.globalCompositeOperation = 'source-over'; ctx.globalAlpha = 1;
}
// 0.96: the Marteau du Chaos's little void rifts (0.5 s): a see-through dark well in a violet glow, violet swirls turning
// fast, light wisps
function drawChaosZone(ctx, z, a, t) {
  const r = z.r, e = t - z.born, k = Math.min(1, e / 0.08) * a;
  ctx.save(); ctx.translate(z.x, z.y);
  ctx.globalAlpha = 0.45 * k; ctx.drawImage(RCache.glow('rgba(140,60,240,0.85)'), -r * 1.15, -r * 0.72, r * 2.3, r * 1.44);
  ctx.globalAlpha = 0.42 * k; ctx.drawImage(RCache.glow('rgba(22,0,44,0.95)'), -r * 0.85, -r * 0.53, r * 1.7, r * 1.06);   // (0.98: softer, like the ground areas: a lighter core, fainter arcs)
  ctx.globalCompositeOperation = 'lighter'; ctx.lineWidth = 2;
  for (let i = 0; i < 3; i++) { const a0 = e * (9 + i * 3) * (i % 2 ? -1 : 1) + i * 2.1, rr = r * (0.45 + i * 0.2); ctx.globalAlpha = 0.35 * k; ctx.strokeStyle = i === 1 ? '#e2c4ff' : '#9a46ff'; ctx.beginPath(); ctx.ellipse(0, 0, rr, rr * 0.62, 0, a0, a0 + 2.2); ctx.stroke(); }
  for (let i = 0; i < 3; i++) { const an = e * 7 + i * TAU / 3, w = r * 0.32; ctx.globalAlpha = 0.6 * k; ctx.drawImage(RCache.glow('rgba(200,140,255,0.9)'), Math.cos(an) * r * 0.5 - w, Math.sin(an) * r * 0.31 - w - 6, w * 2, w * 2); }
  ctx.restore();
}
// 0.98: a poisoned spell's impact (Run.poisonPuff): a few green puffs swell out of the monster and fade with the zone
function drawPoisonPuff(ctx, z, t) {
  const k = clamp((t - z.born) / Math.max(0.01, z.until - z.born), 0, 1), gl = RCache.glow('rgba(150,220,60,0.55)'), n = Game.lowFx ? 3 : 5;
  for (let i = 0; i < n; i++) { const an = i / n * TAU + z.born * 7, rr = z.r * (0.15 + 0.55 * k), pr = z.r * (0.35 + 0.3 * k); ctx.globalAlpha = (1 - k) * 0.9; ctx.drawImage(gl, z.x + Math.cos(an) * rr - pr, z.y - 8 + Math.sin(an) * rr * 0.55 - pr - k * 10, pr * 2, pr * 2); }
  ctx.globalAlpha = 1;
}
function drawCloud(ctx, z, a, t) {
  // Vent Empoisonné: a toxic cloud wrapped around the caster
  ctx.save(); ctx.translate(z.x, z.y - 10);
  for (let i = 0; i < (z.fart ? 0 : 9); i++) {
    const an = i / 9 * TAU + t * 1.6, rr = z.r * (0.45 + 0.35 * Math.sin(t * 2 + i));
    const px = Math.cos(an) * rr, py = Math.sin(an) * rr * 0.55, pr = z.r * (0.35 + 0.1 * Math.sin(t * 3 + i * 2));
    ctx.globalAlpha = a; ctx.drawImage(RCache.glow(z.fart ? 'rgba(170,70,10,0.5)' : 'rgba(150,220,60,0.45)'), px - pr, py - pr, pr * 2, pr * 2);
  }
  if (z.fart) { // Pwout de Cawotte (0.34; ex 6 Millions de Prouts): the client's own gas puff (the 'Lâcher les gaz' emote, clips/sprites) billowing
    // out of the caster: puffs born at the centre drift outwards, swell and fade, the zone always full of them
    ctx.setLineDash([]);
    const N = Game.lowFx ? 7 : 12;
    for (let i = 0; i < N; i++) {
      const ph = (t * 0.55 + i / N) % 1, an = i * 2.399 + Math.floor(t * 0.55 + i / N) * 1.3, rr = z.r * (0.12 + 0.72 * Math.sqrt(ph));
      const px = Math.cos(an) * rr, py = 4 + Math.sin(an) * rr * 0.55 - ph * 14, sz = z.r * (0.42 + 0.5 * ph);
      ctx.globalAlpha = a * Math.min(1, ph * 5) * (1 - ph * ph);
      const pf = orangePuff(z.puff); if (pf) { ctx.drawImage(pf, px - sz / 2, py - sz / 2, sz, sz); if (ph < 0.6) ctx.drawImage(pf, px - sz * 0.35, py - sz * 0.35, sz * 0.7, sz * 0.7); }   // (twice: the client's puff is very see-through)
    }
    const pf = orangePuff(z.puff), s0 = z.r * (0.62 + 0.06 * Math.sin(t * 4)); ctx.globalAlpha = a; if (pf) ctx.drawImage(pf, -s0 / 2, 2 + Math.sin(t * 3) * 2 - s0 / 2, s0, s0);
    // 0.71: cawottes spinning round the zone (0.95: z.caw of them, 12 for the Pwout + Cawotte fusion)
    const nc = z.caw || 6; for (let i = 0; i < nc; i++) { const an = t * 1.8 + i * TAU / nc, x = Math.cos(an) * z.r * 0.8, y = 4 + Math.sin(an) * z.r * 0.44; ctx.save(); ctx.translate(x, y); ctx.rotate(t * 5 + i); ctx.globalAlpha = a; Game.icons.drawFit(ctx, 'it_68_31', 0, 0, 22); ctx.restore(); }
  }
  ctx.globalAlpha = 0.2 * a; ctx.strokeStyle = z.fart ? z.rim || '#c0500e' : '#a8e05a'; ctx.lineWidth = 2; ctx.setLineDash([6, 8]);   // (0.98: a faint rim) ctx.lineDashOffset = -t * 40;
  ctx.beginPath(); ctx.ellipse(0, 10, z.r, z.r * 0.55, 0, 0, TAU); ctx.stroke();
  const fx = z.fart ? null : FxSheets.get(1011);
  if (fx) { const k = Object.keys(fx.anims)[0]; const f = fx.frameAt(k, (t - z.born), true); if (f) { ctx.setLineDash([]); ctx.globalAlpha = 0.8 * a; fx.draw(ctx, f, 0, 0, 0.8, false); } }
  ctx.restore();
}
function drawAlly(ctx, A, t, R) {
  const sh = A.sh; if (!sh) return;
  let anim = A.atkT !== undefined && sh.has('atkR') && A.atkT < sh.duration('atkR') ? 'atkR' : (A.view === 'L' && sh.has('walkL') ? 'walkL' : 'walkR');
  if (A.kind === 'drago' && anim !== 'atkR' && !A.moving && sh.has('staticR')) anim = 'staticR';
  const f = sh.frameAt(anim, anim === 'atkR' ? A.atkT : A.t, anim !== 'atkR'); if (!f) return;
  const D = R.C.drops, cfg = R.allyCfg(A.kind);
  const k = clamp((A.until - t) / 0.5, 0, 1), sc = ES * (cfg.scale || 1), col = cfg.color || D.chaferfu.color;
  ctx.save(); ctx.globalAlpha = Math.min(1, (t - A.born) * 3) * k;
  ctx.fillStyle = col + '55'; ctx.beginPath(); ctx.ellipse(A.x, A.y, 26, 10, 0, 0, TAU); ctx.fill();
  if (A.kind === 'chaferfu' || A.kind === 'lancier') { ctx.strokeStyle = col + '99'; ctx.lineWidth = 2; ctx.setLineDash([6, 8]); ctx.lineDashOffset = -t * 40; ctx.beginPath(); ctx.ellipse(A.x, A.y, cfg.radius, cfg.radius * 0.6, 0, 0, TAU); ctx.stroke(); ctx.setLineDash([]); }
  { const gs = 70 * sc / ES; ctx.drawImage(RCache.glow(col + 'aa'), A.x - gs / 2, A.y - gs * 0.75, gs, gs); }
  sh.draw(ctx, f, A.x, A.y, sc, anim.endsWith('L') ? !A.flip : A.flip);
  ctx.restore();
}
// Roublard bombs (0.21): drawn as vectors (crisp at any resolution), after the Dofus 2.0 ones: a black ball with a
// coloured spotted coat (Explobombe yellow, Bombe Aqueuse blue, Grisou mint), a grey cap and a wooden fuse
const BOMB_COLS = { explobombe: ['#ffc21a', '#f08a12'], bombe_aqueuse: ['#46b4ff', '#1f78d6'], grisou: ['#42e6a8', '#1fae78'] };
function bombBody(ctx, x, y, r, cols, spin, t, lit) {
  ctx.save(); ctx.translate(x, y);
  ctx.beginPath(); ctx.arc(0, 0, r, 0, TAU); ctx.fillStyle = '#1d1b1a'; ctx.fill();
  ctx.save(); ctx.clip();
  // the coloured coat: a cap of colour over the upper two thirds, with a wavy lower edge
  ctx.rotate(spin);
  const g = ctx.createLinearGradient(0, -r, 0, r * 0.4); g.addColorStop(0, cols[0]); g.addColorStop(1, cols[1]);
  ctx.fillStyle = g; ctx.beginPath(); ctx.moveTo(-r * 1.1, -r * 1.2); ctx.lineTo(r * 1.1, -r * 1.2); ctx.lineTo(r * 1.1, r * 0.18);
  for (let i = 0; i <= 6; i++) { const xx = r * 1.1 - i * r * 2.2 / 6; ctx.quadraticCurveTo(xx + r * 0.18, r * (i % 2 ? 0.42 : 0.05), xx, r * (i % 2 ? 0.3 : 0.18)); }
  ctx.closePath(); ctx.fill();
  // the dark spots
  ctx.fillStyle = '#2a2726';
  for (const [sx, sy, sr] of [[-0.42, -0.5, 0.3], [0.32, -0.62, 0.26], [0.62, 0.02, 0.28], [-0.02, -0.02, 0.27], [-0.74, 0.12, 0.22]]) { ctx.beginPath(); ctx.ellipse(sx * r, sy * r, sr * r, sr * r * 0.85, 0.3, 0, TAU); ctx.fill(); }
  ctx.rotate(-spin);
  // shading: light from the top left, dark rim at the bottom right
  const sh = ctx.createRadialGradient(-r * 0.35, -r * 0.4, r * 0.1, 0, 0, r * 1.05);
  sh.addColorStop(0, 'rgba(255,255,255,0.28)'); sh.addColorStop(0.45, 'rgba(255,255,255,0)'); sh.addColorStop(1, 'rgba(0,0,0,0.5)');
  ctx.fillStyle = sh; ctx.fillRect(-r, -r, r * 2, r * 2);
  ctx.restore();
  ctx.lineWidth = Math.max(1.2, r * 0.09); ctx.strokeStyle = '#0d0c0b'; ctx.beginPath(); ctx.arc(0, 0, r, 0, TAU); ctx.stroke();
  // the cap and the wooden fuse
  const cw = r * 0.62, ch = r * 0.34;
  ctx.fillStyle = '#5d5a57'; ctx.strokeStyle = '#1b1a19'; ctx.lineWidth = Math.max(1, r * 0.07);
  ctx.beginPath(); ctx.ellipse(0, -r * 0.92, cw / 2, ch * 0.45, 0, 0, TAU); ctx.fill(); ctx.stroke();
  ctx.fillRect(-cw / 2, -r * 0.92 - ch * 0.55, cw, ch * 0.55); ctx.strokeRect(-cw / 2, -r * 0.92 - ch * 0.55, cw, ch * 0.55);
  ctx.fillStyle = '#77736f'; ctx.beginPath(); ctx.ellipse(0, -r * 0.92 - ch * 0.55, cw / 2, ch * 0.45, 0, 0, TAU); ctx.fill(); ctx.stroke();
  const fx = r * 0.18 + Math.sin(t * 6) * r * 0.04, fy = -r * 1.75;
  ctx.strokeStyle = '#3d2410'; ctx.lineWidth = Math.max(2, r * 0.2); ctx.lineCap = 'round';
  ctx.beginPath(); ctx.moveTo(0, -r * 1.05); ctx.quadraticCurveTo(-r * 0.05, -r * 1.45, fx, fy); ctx.stroke();
  ctx.strokeStyle = '#a5753e'; ctx.lineWidth = Math.max(1.2, r * 0.12);
  ctx.beginPath(); ctx.moveTo(0, -r * 1.05); ctx.quadraticCurveTo(-r * 0.05, -r * 1.45, fx, fy); ctx.stroke();
  if (lit) { // the burning tip
    const k = 0.75 + 0.25 * Math.sin(t * 31);
    ctx.drawImage(RCache.glow('rgba(255,170,40,0.9)'), fx - r * 0.5 * k, fy - r * 0.5 * k, r * k, r * k);
    ctx.fillStyle = '#fff3b0'; ctx.beginPath(); ctx.arc(fx, fy, r * 0.11, 0, TAU); ctx.fill();
  }
  ctx.restore();
}
function drawBomb(ctx, b, t, R) {
  let x = b.x, y = b.y, h = 0, k = 1;
  if (!b.landed) { k = clamp((t - b.t0) / b.fly, 0, 1); x = lerp(b.x0, b.x, k); y = lerp(b.y0, b.y, k); h = Math.sin(k * Math.PI) * 70; }
  const cols = BOMB_COLS[b.spell && b.spell.def.id] || BOMB_COLS.explobombe, r = 17;
  ctx.save();
  ctx.fillStyle = 'rgba(0,0,0,0.28)'; ctx.beginPath(); ctx.ellipse(x, y, r * 1.05, r * 0.42, 0, 0, TAU); ctx.fill();
  let pulse = 1;
  if (b.landed) { // fuse: the danger ring fills up and turns red, the bomb swells a little before the blast
    const left = b.boomAt ? 0 : Math.max(0, b.t0 + b.fly + b.fuse - t), q = 1 - left / Math.max(0.01, b.fuse);
    ctx.strokeStyle = `rgba(255,${Math.round(190 - 150 * q)},60,${0.3 + 0.45 * q})`; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.ellipse(x, y, b.r, b.r * 0.6, 0, 0, TAU); ctx.stroke();
    pulse = 1 + 0.06 * q * Math.sin(t * (10 + 20 * q));
  }
  bombBody(ctx, x, y - r * 0.95 - h, r * pulse, cols, b.landed ? 0 : k * 5, t, true);
  ctx.restore();
}
function drawFireWall(ctx, A, B, t) {
  ctx.save(); ctx.lineCap = 'round';
  const fl = 0.75 + 0.25 * Math.sin(t * 17 + A.x * 0.01);
  ctx.strokeStyle = `rgba(255,120,30,${0.35 * fl})`; ctx.lineWidth = 22; ctx.beginPath(); ctx.moveTo(A.x, A.y - 6); ctx.lineTo(B.x, B.y - 6); ctx.stroke();
  ctx.strokeStyle = `rgba(255,220,90,${0.8 * fl})`; ctx.lineWidth = 6; ctx.setLineDash([10, 7]); ctx.lineDashOffset = -t * 90;
  ctx.beginPath(); ctx.moveTo(A.x, A.y - 6); ctx.lineTo(B.x, B.y - 6); ctx.stroke();
  const n = Math.floor(Math.hypot(B.x - A.x, B.y - A.y) / 26);
  ctx.fillStyle = 'rgba(255,170,40,0.85)';
  for (let i = 1; i < n; i++) { const k = i / n, h = 8 + 7 * Math.abs(Math.sin(t * 9 + i * 1.7)); ctx.beginPath(); ctx.ellipse(lerp(A.x, B.x, k), lerp(A.y, B.y, k) - 6 - h / 2, 4, h / 2, 0, 0, TAU); ctx.fill(); }
  ctx.restore();
}
// screen-edge arrows (in-game arrow textures) pointing at off-screen special monsters and items
const ARROW_SPECIAL_MOBS = new Set(['bandit_manchot', 'wabbit_gm', 'tiwabbit_kiafin', 'tofu_mutant', 'coffre_anime', 'jorbak']);
const ARROW_ITEMS = new Set(['chest', 'dofus', 'power', 'fee', 'sablier', 'rappel', 'kamaboost', 'booster', 'tmap', 'relic', 'nowelgift', 'trool', 'gladia', 'manuel', 'houx']);   // (0.92: the Manuel too, the Maîtres Corbacs' rewards fall anywhere)
function drawEdgeArrows(ctx, R, W, H, u) {
  const IC = Game.icons, z = Game.zoom;
  const one = (wx, wy, icon, scale, base, col, pulse) => {
    const dx = (wx - R.cam.x) * z, dy = (wy - R.cam.y) * z;
    if (Math.abs(dx) < W / 2 - 10 && Math.abs(dy) < H / 2 - 10) return;
    const a = Math.atan2(dy, dx); const rx = W / 2 - 46 * u, ry = H / 2 - 46 * u;
    const k = Math.min(rx / Math.abs(Math.cos(a) || 1e-6), ry / Math.abs(Math.sin(a) || 1e-6));
    const ax = W / 2 + Math.cos(a) * k, ay = H / 2 + Math.sin(a) * k;
    // (0.95: the transform set straight, no save / restore per arrow: they cost ~1 ms a crowded frame on a slow CPU)
    const p = pulse ? 1 + 0.08 * Math.sin(R.time * 8) : 1, c = Math.cos(a - base) * p, s = Math.sin(a - base) * p;
    ctx.setTransform(c, s, -s, c, ax, ay);
    if (IC.get(icon)) { if (icon === ARROW_SMALL) drawTinted(ctx, icon, 'green', 0, 0, scale * u); else IC.draw(ctx, icon, 0, 0, scale * u); }
    else { ctx.fillStyle = col; ctx.strokeStyle = '#000'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(16 * u, 0); ctx.lineTo(-8 * u, -10 * u); ctx.lineTo(-8 * u, 10 * u); ctx.closePath(); ctx.fill(); ctx.stroke(); }
    ctx.setTransform(1, 0, 0, 1, 0, 0);
  };
  for (const m of R.mobs) {
    if (m.dying) continue;
    if (m.doom) continue;
    if (m.boss || m.elite || ARROW_SPECIAL_MOBS.has(m.def.id)) one(m.x, m.y - m.r, ARROW_BIG, m.boss ? 0.62 : 0.48, ARROW_BIG_BASE, m.boss ? '#ff4040' : '#ffd24a', m.boss);
  }
  if (R.merchant) one(R.merchant.x, R.merchant.y - 40, ARROW_SMALL, 1.3, ARROW_SMALL_BASE, '#ffd24a', true);
  for (const p of R.pickups) if (ARROW_ITEMS.has(p.kind)) one(p.x, p.y, ARROW_SMALL, 1.1, ARROW_SMALL_BASE, '#ffe9a8', p.kind === 'dofus');
}

// Féca glyph: lit cells on the ground, like the glyphs of the client
function drawGlyphCells(ctx, z, a, t) {
  const cw = 53 * ES * 0.5, chh = 27 * ES * 0.5, n = Math.max(1, Math.round(z.r / cw));
  const col = z.color || '#ff5a1e', pulse = 0.75 + 0.25 * Math.sin(t * 6);
  ctx.save(); ctx.globalAlpha = a;
  for (let i = -n; i <= n; i++) for (let j = -n; j <= n; j++) {
    if (Math.abs(i) + Math.abs(j) > n) continue;   // circle of cells (Dofus shape)
    const x = z.x + (i - j) * cw, y = z.y + (i + j) * chh;
    ctx.beginPath(); ctx.moveTo(x, y - chh + 1); ctx.lineTo(x + cw - 1, y); ctx.lineTo(x, y + chh - 1); ctx.lineTo(x - cw + 1, y); ctx.closePath();
    ctx.fillStyle = col + (Math.round(0x55 * pulse)).toString(16).padStart(2, '0'); ctx.fill();
    ctx.strokeStyle = col; ctx.lineWidth = 1.5; ctx.stroke();
  }
  // embers
  for (let k = 0; k < 6; k++) { const ph = (t * 0.8 + k / 6) % 1, an = k * 2.1 + Math.floor(t * 0.8 + k / 6) * 1.7; const rr = z.r * 0.7 * ((k * 37) % 10) / 10;
    ctx.globalAlpha = a * (1 - ph); ctx.fillStyle = z.spell && z.spell.p.glyph === 'immo' ? (k % 2 ? '#dff0ff' : '#6aa8ff') : (k % 2 ? '#ffd24a' : '#ff7a1a'); ctx.beginPath(); ctx.arc(z.x + Math.cos(an) * rr, z.y + Math.sin(an) * rr * 0.5 - ph * 40, 2.5, 0, TAU); ctx.fill(); }
  ctx.restore();
}
// Flèche Enflammée: the arrow flies along the line and leaves it burning
function drawFireLine(ctx, b, t) {
  const age = t - b.t0, life = b.until - b.t0, k = clamp(age / 0.15, 0, 1), fade = clamp((b.until - t) / 0.3, 0, 1);
  ctx.save(); ctx.translate(b.x, b.y); ctx.rotate(b.a);
  const len = b.len * k;
  { const a0 = ctx.globalAlpha; ctx.globalAlpha = a0 * fade; ctx.drawImage(RCache.band('rgba(255,90,20,0)', 'rgba(255,140,40,0.55)'), 0, -b.w / 2, len, b.w); ctx.globalAlpha = a0; }   // (0.95: RCache.band)
  const n = Math.floor(len / 22);
  for (let i = 1; i < n; i++) { const h = (10 + 9 * Math.abs(Math.sin(t * 11 + i * 1.9))) * fade; ctx.fillStyle = i % 3 ? `rgba(255,170,40,${0.85 * fade})` : `rgba(255,236,140,${0.9 * fade})`; ctx.beginPath(); ctx.ellipse(i * 22, -h / 2 + 4, 5, h / 2, 0, 0, TAU); ctx.fill(); }
  const fx = FxSheets.get(909), ff = fx && fx.anims.root && fx.frameAt('root', age, true);
  if (k < 1 && ff) fx.draw(ctx, ff, len, 0, ES * 0.95, false);   // (0.61: the client's flaming arrow, spell clip 909, flies along the line)
  else if (k < 1) { ctx.fillStyle = '#ffe9a8'; ctx.beginPath(); ctx.moveTo(len + 10, 0); ctx.lineTo(len - 8, -5); ctx.lineTo(len - 8, 5); ctx.fill(); ctx.strokeStyle = '#ff8a2a'; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(len - 30, 0); ctx.lineTo(len - 6, 0); ctx.stroke(); }
  ctx.restore();
}
// accessory symbol drawn on its own (weapon thrown, pets in menus)
function drawAccSym(ctx, sym, dir, scale, rot) {
  const A0 = Game.run && Game.run.charSprite && Game.run.charSprite.acc; if (!A0) return null;
  const cp = AccLib.compact(sym), A = cp ? [cp] : A0;   // (0.44: the accessory's own small atlas)
  for (const a of A) { let fr = a.f[sym + '|' + dir]; if (!fr) continue; if (Array.isArray(fr[0])) fr = fr[0];
    if (!a.img) { AccLib.need(a); return null; }   // (0.44: accessory sheets load when first needed)
    const k = a.img._k || 1;
    ctx.save(); ctx.rotate(rot || 0); const s = scale * 3.2 / a.zoom; ctx.drawImage(a.img, fr[0] * k, fr[1] * k, fr[2] * k, fr[3] * k, -fr[2] * s / 2, -fr[3] * s / 2, fr[2] * s, fr[3] * s); ctx.restore(); return a; }
  return null;
}
// 0.91: the Otomaï's Élixir de Mutation — a green glow breathing behind the grown character, bubbles rising round him
function drawMutation(ctx, P, R, sc) {
  const t = R.time, a = Math.min(1, (sc - 1) / 0.2), y = P.y - P.leapH - 34 * sc, g = RCache.glow('rgba(126,217,87,0.6)');
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  const rr = (52 + 6 * Math.sin(t * 6)) * sc; ctx.globalAlpha = 0.85 * a; ctx.drawImage(g, P.x - rr, y - rr * 1.25, rr * 2, rr * 2.5);
  const b = RCache.glow('rgba(190,255,140,0.95)');
  for (let i = 0; i < 6; i++) {
    const k = (t * 0.7 + i / 6) % 1, an = i * 2.1 + t * 1.3, bx = P.x + Math.cos(an) * 26 * sc, by = P.y - P.leapH - k * 90 * sc, br = (4 + 4 * Math.sin(k * Math.PI)) * sc;
    ctx.globalAlpha = a * (1 - k) * 0.9; ctx.drawImage(b, bx - br * 2, by - br * 2, br * 4, br * 4);
  }
  ctx.restore();
}
// 0.91: Brume Mutagène (aura `mist`) — soft puffs of the cached glow drifting round the character
function drawMist(ctx, x, y, r, col, t) {
  const g = RCache.glow(`rgba(${hexRgb(col)},0.5)`), n = Game.lowFx ? 6 : 10;
  ctx.save();
  for (let i = 0; i < n; i++) {
    const an = i / n * TAU + t * (0.25 + (i % 3) * 0.08), d = r * (0.35 + 0.45 * ((Math.sin(t * 0.9 + i * 1.7) + 1) / 2)), pr = r * (0.38 + 0.08 * Math.sin(t * 1.4 + i));
    ctx.globalAlpha = 0.8; ctx.drawImage(g, x + Math.cos(an) * d - pr, y + Math.sin(an) * d * 0.62 - pr * 0.75 - 10, pr * 2, pr * 1.5);
  }
  ctx.restore();
}
// golden aura of the magic purse (kamas x2)
function drawKamaAura(ctx, P, R) {
  const t = R.time;
  ctx.save();
  const g = ctx.createRadialGradient(P.x, P.y - 30, 6, P.x, P.y - 30, 70); g.addColorStop(0, 'rgba(255,215,0,0.35)'); g.addColorStop(1, 'rgba(255,215,0,0)');
  ctx.fillStyle = g; ctx.beginPath(); ctx.arc(P.x, P.y - 30, 70, 0, TAU); ctx.fill();
  ctx.strokeStyle = 'rgba(255,220,90,0.8)'; ctx.lineWidth = 2; ctx.setLineDash([5, 7]); ctx.lineDashOffset = -t * 50;
  ctx.beginPath(); ctx.ellipse(P.x, P.y, 34, 14, 0, 0, TAU); ctx.stroke(); ctx.setLineDash([]);
  for (let i = 0; i < 5; i++) { const a = t * 2.4 + i * TAU / 5; Game.icons.draw(ctx, 'KamaSymbol', P.x + Math.cos(a) * 34, P.y - 30 + Math.sin(a) * 14 - Math.sin(t * 3 + i) * 6, 0.24); }
  ctx.restore();
}

// Vague à Lame: a wave of water rolls along the line
function drawWave(ctx, b, t) {
  // Vague à Lame: a cartoon breaker (flat colours, dark outline, foam) rolls along the line and leaves a wet trail
  const age = t - b.t0, k = clamp(age / 0.35, 0, 1), e = 1 - (1 - k) * (1 - k), fade = clamp((b.until - t) / 0.35, 0, 1) * (b.dim || 1);
  const len = b.len * e, W = b.w, ca = Math.cos(b.a), sa = Math.sin(b.a);
  ctx.save(); ctx.translate(b.x, b.y + 14); ctx.rotate(b.a);
  // the trail: water that thins out behind the wave
  const g = ctx.createLinearGradient(0, 0, len, 0); g.addColorStop(0, 'rgba(60,150,230,0)'); g.addColorStop(0.6, `rgba(60,150,230,${0.35 * fade})`); g.addColorStop(1, `rgba(120,200,255,${0.6 * fade})`);
  ctx.fillStyle = g; ctx.beginPath();
  for (let x = 0; x <= len; x += 6) { const h = W * 0.42 * (0.35 + 0.65 * x / Math.max(1, len)); ctx.lineTo(x, -h + Math.sin(x * 0.09 - t * 12) * 3); }
  for (let x = len; x >= 0; x -= 6) { const h = W * 0.42 * (0.35 + 0.65 * x / Math.max(1, len)); ctx.lineTo(x, h + Math.sin(x * 0.09 - t * 12 + 2) * 3); }
  ctx.closePath(); ctx.fill();
  ctx.globalAlpha = 0.8 * fade; ctx.strokeStyle = '#e6f6ff'; ctx.lineWidth = 2; ctx.lineCap = 'round';
  for (let row = -1; row <= 1; row += 2) { ctx.beginPath(); for (let x = len * 0.25; x <= len; x += 7) { const y = row * W * 0.2 + Math.sin(x * 0.15 - t * 16 + row) * 2.5; if (x <= len * 0.25 + 1) ctx.moveTo(x, y); else ctx.lineTo(x, y); } ctx.stroke(); }
  ctx.restore();
  // the breaker itself, upright (the ground is seen from the side), facing where it goes
  const fx = b.x + ca * len, fy = b.y + 14 + sa * len, H = W * 0.95 * (0.7 + 0.3 * fade), sx = ca >= 0 ? 1 : -1;
  ctx.save(); ctx.translate(fx, fy); ctx.scale(sx, 1); ctx.globalAlpha = fade;
  ctx.fillStyle = 'rgba(0,30,70,0.25)'; ctx.beginPath(); ctx.ellipse(0, 2, W * 0.75, W * 0.22, 0, 0, TAU); ctx.fill();
  const body = new Path2D(), wob = Math.sin(t * 18) * 2;
  body.moveTo(-W * 0.75, 0);
  body.bezierCurveTo(-W * 0.55, -H * 0.35, -W * 0.25, -H * 0.95, W * 0.12, -H + wob);
  body.bezierCurveTo(W * 0.42, -H * 1.02, W * 0.6, -H * 0.72, W * 0.48, -H * 0.5);
  body.bezierCurveTo(W * 0.4, -H * 0.66, W * 0.22, -H * 0.66, W * 0.18, -H * 0.5);
  body.bezierCurveTo(W * 0.14, -H * 0.3, W * 0.3, -H * 0.12, W * 0.5, 0);
  body.closePath();
  const bg = ctx.createLinearGradient(0, -H, 0, 0); bg.addColorStop(0, '#9be3ff'); bg.addColorStop(0.45, '#3c9be6'); bg.addColorStop(1, '#1d5fae');
  ctx.fillStyle = bg; ctx.fill(body); ctx.strokeStyle = '#123c6e'; ctx.lineWidth = 2.5; ctx.lineJoin = 'round'; ctx.stroke(body);
  ctx.strokeStyle = 'rgba(255,255,255,0.7)'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(-W * 0.5, -H * 0.2); ctx.bezierCurveTo(-W * 0.35, -H * 0.5, -W * 0.15, -H * 0.75, W * 0.05, -H * 0.85); ctx.stroke();
  // foam on the crest and at the foot
  ctx.fillStyle = '#ffffff'; ctx.strokeStyle = '#123c6e'; ctx.lineWidth = 1.5;
  const foam = [[W * 0.1, -H], [W * 0.3, -H * 0.97], [W * 0.46, -H * 0.8], [-W * 0.08, -H * 0.93], [W * 0.5, -H * 0.58]];
  foam.forEach(([x, y], i) => { const r = W * (0.09 + 0.03 * Math.sin(t * 15 + i * 2)); ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); ctx.fill(); ctx.stroke(); });
  for (let i = 0; i < 4; i++) { const x = -W * 0.6 + i * W * 0.38, r = W * (0.08 + 0.02 * Math.sin(t * 13 + i)); ctx.beginPath(); ctx.ellipse(x, -1, r * 1.4, r * 0.7, 0, 0, TAU); ctx.fill(); }
  // spray
  for (let i = 0; i < 7; i++) { const ph = (t * 2.5 + i / 7) % 1, x = W * (0.2 + 0.5 * ((i * 37) % 10) / 10) + ph * W * 0.5, y = -H * (0.9 + ph * 0.35) + ph * ph * H * 0.9;
    ctx.globalAlpha = fade * (1 - ph); ctx.beginPath(); ctx.arc(x, y, 2.4 - ph * 1.2, 0, TAU); ctx.fill(); }
  ctx.restore();
}


// the Sram trap's marker as the client shows it on its cells (a black spike on a turquoise and gold base, a light on top)
const TRAP_PAL = { base: '#c99a1e', baseD: '#7a5a10', band: '#22b3b0', bandD: '#0d4a48', glow: '255,240,170', core: '#fff6c8' };
const TRAP_POISON = { base: '#7a1414', baseD: '#3e0606', band: '#3fae3a', bandD: '#164a1a', glow: '150,255,110', core: '#e8ffd0' };   // (0.92: the fused trap)
// 0.92: the fused Piège Empoisonné's poison: green and violet smoke puffs swelling up off its area, tiny green / violet
// streaks shooting up from it (cached glows and short lines, placed from the time: nothing kept per frame)
function drawPoisonTrapFx(ctx, tr, t) {
  if (Game.lowFx) return; const r = tr.r, sd = tr.x * 0.37 + tr.y * 0.61, gG = RCache.glow('rgba(80,210,60,0.9)'), gV = RCache.glow('rgba(170,70,240,0.85)');
  for (let i = 0; i < 6; i++) {
    const h = hash01(sd + i * 3.1), ph = (t * 0.35 + h) % 1, an = hash01(sd + i * 7.7) * TAU, d = r * 0.6 * hash01(sd + i * 1.3);
    const px = tr.x + Math.cos(an) * d + Math.sin(t * 0.9 + i) * 6, py = tr.y + Math.sin(an) * d * 0.62 - ph * 40, rr = r * (0.26 + 0.34 * ph);
    ctx.globalAlpha = 0.75 * Math.sin(ph * Math.PI); ctx.drawImage(i % 2 ? gV : gG, px - rr, py - rr * 0.8, rr * 2, rr * 1.6);
  }
  ctx.lineCap = 'round'; ctx.lineWidth = 2.2;
  for (let i = 0; i < 12; i++) {
    const h = hash01(sd + i * 5.3), ph = (t * 0.9 + h) % 1, an = hash01(sd + i * 2.9) * TAU, d = r * 0.85 * Math.sqrt(hash01(sd + i * 9.1));
    const px = tr.x + Math.cos(an) * d, py = tr.y + Math.sin(an) * d * 0.62 - ph * 30, ln = 5 + 5 * (1 - ph);
    ctx.globalAlpha = Math.sin(ph * Math.PI); ctx.strokeStyle = i % 2 ? '#d49cff' : '#a8ff70';
    ctx.beginPath(); ctx.moveTo(px, py); ctx.lineTo(px, py - ln); ctx.stroke();
  }
  ctx.globalAlpha = 1;
}
function drawTrapCone(ctx, x, y, t, pal) {
  const H = 30, R = 8.5, Q = pal || TRAP_PAL;
  ctx.save(); ctx.translate(x, y);
  ctx.fillStyle = 'rgba(0,0,0,0.35)'; ctx.beginPath(); ctx.ellipse(0, 1, R + 3, (R + 3) * 0.45, 0, 0, TAU); ctx.fill();
  const band = (y0, y1, r0, r1, c) => { ctx.fillStyle = c; ctx.beginPath(); ctx.moveTo(-r0, y0); ctx.ellipse(0, y0, r0, r0 * 0.42, 0, Math.PI, 0, true); ctx.lineTo(r1, y1); ctx.ellipse(0, y1, r1, r1 * 0.42, 0, 0, Math.PI, true); ctx.closePath(); ctx.fill(); };
  const rAt = h => R * (1 - h / H);
  band(0, -4, R, rAt(4), Q.base);                 // gold base ring
  band(-4, -5.5, rAt(4), rAt(5.5), Q.baseD);
  band(-5.5, -10, rAt(5.5), rAt(10), Q.band);     // turquoise band
  band(-10, -11, rAt(10), rAt(11), Q.bandD);
  ctx.fillStyle = '#121014'; ctx.beginPath(); ctx.moveTo(-rAt(11), -11); ctx.ellipse(0, -11, rAt(11), rAt(11) * 0.42, 0, Math.PI, 0, true); ctx.lineTo(0, -H); ctx.closePath(); ctx.fill();
  ctx.fillStyle = 'rgba(255,255,255,0.18)'; ctx.beginPath(); ctx.moveTo(-rAt(11) * 0.55, -11.5); ctx.lineTo(-0.6, -H + 2); ctx.lineTo(-rAt(11) * 0.1, -11.8); ctx.closePath(); ctx.fill();
  ctx.fillStyle = 'rgba(255,255,255,0.3)'; ctx.fillRect(-R * 0.75, -3, 2, 2.2); ctx.fillRect(-rAt(6) * 0.75, -9, 1.6, 2.4);
  const g = 0.75 + 0.25 * Math.sin(t * 6);
  ctx.fillStyle = `rgba(${Q.glow},${0.35 * g})`; ctx.beginPath(); ctx.arc(0, -H - 1, 4, 0, TAU); ctx.fill();
  ctx.fillStyle = Q.core; ctx.beginPath(); ctx.arc(0, -H - 1, 1.8, 0, TAU); ctx.fill();
  ctx.restore();
}

// the Féca glyph (fx 802) drawn once in red on its own canvas
const _redGlyph = new Map();
function redGlyph(fx, f) {
  let c = _redGlyph.get(f); if (c) return c;
  c = document.createElement('canvas'); c.width = c.height = 128; const g = c.getContext('2d');
  fx.draw(g, f, 64, 64, 0.95, false);
  g.globalCompositeOperation = 'source-atop'; g.fillStyle = 'rgba(235,40,25,0.7)'; g.fillRect(0, 0, 128, 128);
  g.globalCompositeOperation = 'lighter'; g.globalAlpha = 0.4; g.drawImage(c, 0, 0);
  _redGlyph.set(f, c); return c;
}

// a round face button of the controller (B: red)
function drawPadBtn(ctx, l, x, y, u) {
  ctx.fillStyle = l === 'B' ? '#c8281e' : l === 'A' ? '#3a9a3a' : '#555'; ctx.strokeStyle = '#1e1208'; ctx.lineWidth = 1.5 * u;
  ctx.beginPath(); ctx.arc(x, y, 8 * u, 0, TAU); ctx.fill(); ctx.stroke();
  TextCache.draw(ctx, l, x, y + 4 * u, '#fff', 10 * u, 'center', 'rgba(0,0,0,0.6)', 1.5 * u);
}

// the booster packs (0.98.3: tools/assets/build_ttg098.py: SPR.boosters)
const BoosterArt = { c: {}, get(i) {   // (0.98.3: each pack its file, assets/ttg/p<i>.webp; a smaller copy for the ground: no mipmaps there)
  let e = this.c[i]; if (e) return e.t;
  e = this.c[i] = { t: null }; const im = new Image(); im.onload = () => { const c = document.createElement('canvas'); c.width = 120; c.height = Math.round(120 * im.height / im.width); const g = c.getContext('2d'); g.imageSmoothingQuality = 'high'; g.drawImage(im, 0, 0, c.width, c.height); e.t = c; }; im.src = vurl(`assets/ttg/p${i}.webp`); return null;
} };
function boosterPack(ctx, i, x, y, w) {
  const B = SPR.boosters, t = BoosterArt.get(i % B.n); if (!t) return false;
  ctx.drawImage(t, x, y, w, w * B.h / B.w); return true;
}

// a sheet recoloured once (0.40: the blue chest of the Minotoror trapdoor): the colour over its pixels, keeping the shading
function tintedSheet(sh, col) {
  const k = '_tint' + col; if (sh[k] !== undefined) return sh[k] || sh.img; if (!sh.img || !sh.img.width) return sh.img;
  const c = document.createElement('canvas'); c.width = sh.img.width; c.height = sh.img.height; const g = c.getContext('2d');
  g.drawImage(sh.img, 0, 0); g.globalCompositeOperation = 'color'; g.fillStyle = col; g.fillRect(0, 0, c.width, c.height);
  g.globalCompositeOperation = 'destination-in'; g.drawImage(sh.img, 0, 0); if (sh.img._k) c._k = sh.img._k;
  return (sh[k] = c);
}

// 0.60: an Arakne web on the ground (Toile d'Arakne): spokes and a spiral, a little sway
// 0.92 (livelier, like the other ground spells, with tiny Araknes): it is woven in (the spokes shoot out, the rings
// follow one by one), its threads quiver (hard at the landing, then gently), dewdrops twinkle on the crossings, and tiny
// Araknes let themselves down on a thread, then scuttle along the rings, stopping and starting, legs going
function drawWeb(ctx, z, a, t) {
  const r = z.r, n = 9, age = t - z.born, seed = z.born * 7.31 + z.x * 0.13;
  const grow = clamp(age / 0.22, 0, 1), shake = 0.05 + 0.5 * Math.max(0, 1 - age / 0.6);
  const ringK = ring => clamp((age - 0.1 - ring * 0.08) / 0.14, 0, 1);   // (each ring woven after the last)
  const wob = (i, ring) => 1 + shake * 0.06 * Math.sin(t * 13 + i * 1.7 + ring * 2.3 + seed);
  ctx.save(); ctx.translate(z.x, z.y); ctx.scale(1, 0.62); ctx.rotate(Math.sin(t * 0.7 + z.x) * 0.05);
  // 0.95 (perf sweep: Herbe Folle keeps up to 15 webs, ~100 strokes each, every frame): once woven (0.6 s) a web no
  // longer changes but for its sway — it is drawn from its picture, made once per radius (RCache.web)
  if (age >= 0.6) { const W = RCache.web(r); ctx.globalAlpha = a; ctx.drawImage(W, -W.R, -W.R, W.R * 2, W.R * 2); }
  else {
  ctx.globalAlpha = 0.18 * a * grow; ctx.fillStyle = '#d8d8ec'; ctx.beginPath(); ctx.arc(0, 0, r * grow, 0, TAU); ctx.fill();
  const path = () => { ctx.beginPath();
    for (let i = 0; i < n; i++) { const an = i / n * TAU, rr = r * easeOut(grow) * wob(i, 0); ctx.moveTo(0, 0); ctx.lineTo(Math.cos(an) * rr, Math.sin(an) * rr); }
    for (let ring = 1; ring <= 4; ring++) { const k = ringK(ring); if (!k) break; const rr = r * ring / 4.3, m = Math.max(1, Math.ceil(n * k));
      for (let i = 0; i <= m; i++) { const an = Math.min(i, n * k) / n * TAU, sag = rr * (i % 2 ? 0.92 : 1) * wob(i, ring); const x = Math.cos(an) * sag, y = Math.sin(an) * sag; if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y); } } };
  ctx.globalAlpha = 0.85 * a; ctx.strokeStyle = 'rgba(30,30,40,0.22)'; ctx.lineWidth = 3.4; path(); ctx.stroke();
  ctx.strokeStyle = 'rgba(245,245,255,0.95)'; ctx.lineWidth = 1.6; path(); ctx.stroke();
  }
  // dewdrops twinkling on the crossings (cached glow)
  if (!Game.lowFx && age > 0.5) { const gl = RCache.glow('rgba(235,245,255,0.95)');
    for (let i = 0; i < 7; i++) { const ring = 1 + (i * 3 + Math.floor(seed)) % 4, sp = (i * 5 + Math.floor(seed * 3)) % n, an = sp / n * TAU, rr = r * ring / 4.3 * (sp % 2 ? 0.92 : 1);
      const tw = Math.max(0, Math.sin(t * 2.3 + i * 2.1 + seed)), d = 2 + 4 * tw; if (tw < 0.05) continue;
      ctx.globalAlpha = a * tw; ctx.drawImage(gl, Math.cos(an) * rr - d, Math.sin(an) * rr - d, d * 2, d * 2); } }
  ctx.restore();
  // the tiny Araknes (drawn upright, not squashed with the web)
  const ns = Math.min(6, 2 + Math.round(r / 45));
  for (let i = 0; i < ns; i++) {
    const h1 = (Math.sin(i * 91.7 + seed) * 43758.5) % 1, hh = Math.abs(h1), ring = 1 + (i % 4), rr = r * ring / 4.3 * 0.96;
    const drop = clamp((age - 0.15 - i * 0.12) / 0.45, 0, 1); if (!drop) continue;
    const dir = i % 2 ? 1 : -1, tt = Math.max(0, age - 0.6 - i * 0.12);
    const go = tt + 0.35 * Math.sin(tt * 2.2 + i * 1.9), an = hh * TAU + dir * go * (0.9 + hh * 0.6) * 42 / rr;   // (stop-and-go, ~42 px/s)
    const x = z.x + Math.cos(an) * rr, y = z.y + Math.sin(an) * rr * 0.62, lift = (1 - easeOut(drop)) * 70;
    const moving = drop >= 1 && Math.cos(tt * 2.2 + i * 1.9) > -0.6;
    if (lift > 0.5) { ctx.globalAlpha = a * 0.7; ctx.strokeStyle = 'rgba(245,245,255,0.9)'; ctx.lineWidth = 0.8; ctx.beginPath(); ctx.moveTo(x, y - lift - 90); ctx.lineTo(x, y - lift - 4); ctx.stroke(); }   // (its thread)
    const vx = -Math.sin(an) * dir, vy = Math.cos(an) * dir * 0.62;
    ctx.globalAlpha = a; drawMiniArakne(ctx, x, y - lift, Math.atan2(vy, vx), moving ? t * 14 + i : 0, 1 - 0.2 * (lift / 70));
  }
  ctx.globalAlpha = 1;
}
// 0.92: a tiny Arakne seen from above (Toile d'Arakne): brown-black round body, a white cross on the back, red eyes,
// eight legs stepping in two sets; 4 leg poses drawn once at 3x into a strip, then blitted (about 24 px across, legs included)
const _miniArakne = { c: null, S: 48 };
function drawMiniArakne(ctx, x, y, ang, step, sc = 1) {
  const M = _miniArakne, S = M.S;
  if (!M.c) {
    const c = document.createElement('canvas'); c.width = S * 4; c.height = S; const g = c.getContext('2d'); g.lineCap = 'round'; g.lineJoin = 'round';
    for (let f = 0; f < 4; f++) {
      g.save(); g.translate(S * f + S / 2, S / 2); const ph = f / 4 * TAU;
      for (let s = -1; s <= 1; s += 2) for (let l = 0; l < 4; l++) {   // legs fanned round the body, the front ones bent forward,
        const sw = 0.22 * Math.sin(ph + (l % 2 ? Math.PI : 0) + (s > 0 ? Math.PI : 0));   // the back ones backward; two sets swing
        const A = s * (0.5 + l * 0.66) + sw, B = A + s * (l < 2 ? -0.45 : 0.45);
        const kx = Math.cos(A) * 11, ky = Math.sin(A) * 11, ex = kx + Math.cos(B) * 10, ey = ky + Math.sin(B) * 10;
        for (const [col, lw] of [['#1a0f08', 4.4], ['#6a4428', 2]]) { g.strokeStyle = col; g.lineWidth = lw; g.beginPath(); g.moveTo(Math.cos(A) * 3, Math.sin(A) * 3); g.lineTo(kx, ky); g.lineTo(ex, ey); g.stroke(); }
      }
      g.fillStyle = '#1a0f08'; g.beginPath(); g.ellipse(-5, 0, 10, 8.5, 0, 0, TAU); g.fill(); g.beginPath(); g.ellipse(7, 0, 6, 5.5, 0, 0, TAU); g.fill();   // (outline)
      const gb = g.createRadialGradient(-8, -3, 1, -5, 0, 9); gb.addColorStop(0, '#8a5a34'); gb.addColorStop(1, '#3a2414');
      g.fillStyle = gb; g.beginPath(); g.ellipse(-5, 0, 8.5, 7, 0, 0, TAU); g.fill();
      g.fillStyle = '#4a2e1a'; g.beginPath(); g.ellipse(7, 0, 4.6, 4.2, 0, 0, TAU); g.fill();
      g.strokeStyle = 'rgba(240,232,210,0.9)'; g.lineWidth = 1.6; g.beginPath(); g.moveTo(-10, 0); g.lineTo(-1, 0); g.moveTo(-5.5, -3.5); g.lineTo(-5.5, 3.5); g.stroke();   // (the cross)
      g.fillStyle = '#ff4a3a'; g.beginPath(); g.arc(9.5, -1.8, 1.3, 0, TAU); g.arc(9.5, 1.8, 1.3, 0, TAU); g.fill();
      g.restore();
    }
    M.c = c;
  }
  const f = ((Math.floor(step) % 4) + 4) % 4, w = 24 * sc;
  ctx.save(); ctx.translate(x, y); ctx.scale(1, 0.75); ctx.rotate(ang);
  ctx.drawImage(M.c, f * S, 0, S, S, -w / 2, -w / 2, w, w); ctx.restore();
}
// a grey Crackler rock (Éboulement du Craqueleur)
function drawRock(ctx, x, y, r, rot) {
  ctx.save(); ctx.translate(x, y); ctx.rotate(rot * 0.15);
  ctx.fillStyle = '#6f6458'; ctx.strokeStyle = '#2a221b'; ctx.lineWidth = 2.5; ctx.beginPath();
  for (let i = 0; i < 8; i++) { const an = i / 8 * TAU, rr = r * (0.78 + 0.22 * Math.sin(i * 2.7 + 1.3)); ctx.lineTo(Math.cos(an) * rr, Math.sin(an) * rr); } ctx.closePath(); ctx.fill(); ctx.stroke();
  ctx.fillStyle = 'rgba(255,240,215,0.35)'; ctx.beginPath(); ctx.ellipse(-r * 0.25, -r * 0.3, r * 0.4, r * 0.22, -0.5, 0, TAU); ctx.fill();
  ctx.fillStyle = 'rgba(0,0,0,0.25)'; ctx.beginPath(); ctx.ellipse(r * 0.2, r * 0.3, r * 0.45, r * 0.2, 0.3, 0, TAU); ctx.fill();
  ctx.restore();
}
