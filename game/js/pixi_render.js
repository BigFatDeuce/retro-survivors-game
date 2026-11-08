'use strict';
// ---------------------------------------------------------------- the runs drawn by PixiJS (WebGL)
// 0.61 prototype, 0.62 the default renderer (0.95: the only one asked for; the 2D canvas when WebGL fails), or
// ?pixi=1 / ?pixi=0 in the address (tests); without WebGL the 2D canvas draws everything. PixiJS 8
// (game/lib/pixi.min.js, MIT, a local file: no CDN, the game works offline and in the exe) draws on a WebGL canvas
// (#pixi) under the game's 2D canvas (#game, then transparent). Natively: the ground tiles, the darkened outside of the
// zone, the shadows, the monsters (glow, body, tint, hit flash, Archimonster sheen and stars, poison / bleed), the
// summons drawn from a monster sheet, the particles. 0.62: everything else of the world keeps its exact place in the
// drawing order (Run.draw's nat()): the same 2D drawing code runs on PXCtx (its pictures, rectangles and ellipses become
// quads: pickups, projectiles, effects, the marks over the monsters, the merchant…), and what PixiJS cannot draw that
// way (paths, strokes, gradients, texts) is drawn by the 2D code into a full-screen 2D layer that becomes a texture
// there (PX.layer: zones, glyphs, traps, telegraphs, rings, slashes, beams…), or a small box of its own for what stands
// among the monsters (PX.proxy: the player, allies, bombs, the Double, the Mama, a monster's drain / marks). The 2D
// canvas on top keeps the texts, the faint silhouette of the character, the HUD and the cinematics.
// docs/reports/pixijs-renderer.md = the plan and the measures.
// Drawing model: every frame the scene is a list of quads in drawing order (PX.q), laid on a pool of PIXI.Sprite that
// stays in the same order; PixiJS batches them (one draw call for many sprites of the same textures).
// 0.62: a stand-in for the 2D context. The game's own 2D drawing code (pickups, projectiles, effects, the marks over the
// monsters, the merchant…) runs on it unchanged: each drawImage becomes a PixiJS quad with the same transform, opacity
// and 'lighter' blending, and so do rectangles and whole ellipses / circles filled with one colour. Anything else (paths,
// strokes, gradients, texts, filters, shadows) throws PXMiss at once: PX.nat takes back what that drawing had laid and
// draws it with the real 2D code into a texture at the same place in the drawing order (PX.layer / PX.proxy)
const PXMiss = { miss: true };
class PXCtx {
  constructor() { this.st = []; this.el = []; this.canvas = { width: 1, height: 1 }; this.reset(1, 0, 0); }
  reset(z, wx, wy) {
    this.a = z; this.b = 0; this.c = 0; this.d = z; this.e = wx; this.f = wy; this.ga = 1;
    this.globalCompositeOperation = 'source-over'; this.fillStyle = '#000'; this.strokeStyle = '#000'; this.lineWidth = 1;
    this.filter = 'none'; this.shadowBlur = 0; this.shadowColor = 'rgba(0,0,0,0)'; this.shadowOffsetX = 0; this.shadowOffsetY = 0;
    this.font = '10px sans-serif'; this.textAlign = 'start'; this.textBaseline = 'alphabetic'; this.lineCap = 'butt'; this.lineJoin = 'miter';
    this.lineDashOffset = 0; this.imageSmoothingEnabled = true; this.imageSmoothingQuality = 'low'; this.st.length = 0; this.el.length = 0; this.pok = true; this.dash = null; this.pl = []; this.cur = null;
  }
  get globalAlpha() { return this.ga; }
  set globalAlpha(v) { if (v >= 0 && v <= 1) this.ga = v; }
  save() { this.st.push([this.a, this.b, this.c, this.d, this.e, this.f, this.ga, this.globalCompositeOperation, this.fillStyle, this.strokeStyle, this.lineWidth, this.filter, this.shadowBlur, this.font, this.textAlign, this.textBaseline, this.lineCap, this.lineJoin, this.dash, this.lineDashOffset]); }
  restore() {
    const v = this.st.pop(); if (!v) return;
    [this.a, this.b, this.c, this.d, this.e, this.f, this.ga, this.globalCompositeOperation, this.fillStyle, this.strokeStyle, this.lineWidth, this.filter, this.shadowBlur, this.font, this.textAlign, this.textBaseline, this.lineCap, this.lineJoin, this.dash, this.lineDashOffset] = v;
  }
  translate(x, y) { this.e += this.a * x + this.c * y; this.f += this.b * x + this.d * y; }
  scale(x, y) { this.a *= x; this.b *= x; this.c *= y; this.d *= y; }
  rotate(r) { const co = Math.cos(r), si = Math.sin(r), a = this.a, b = this.b; this.a = a * co + this.c * si; this.b = b * co + this.d * si; this.c = this.c * co - a * si; this.d = this.d * co - b * si; }
  transform(a, b, c, d, e, f) {
    const A = this.a, B = this.b, C = this.c, D = this.d;
    this.e += A * e + C * f; this.f += B * e + D * f; this.a = A * a + C * b; this.b = B * a + D * b; this.c = A * c + C * d; this.d = B * c + D * d;
  }
  setTransform(a, b, c, d, e, f) { if (typeof a === 'object') ({ a, b, c, d, e, f } = a); this.a = a; this.b = b; this.c = c; this.d = d; this.e = e; this.f = f; }
  resetTransform() { this.setTransform(1, 0, 0, 1, 0, 0); }
  getTransform() { return { a: this.a, b: this.b, c: this.c, d: this.d, e: this.e, f: this.f }; }
  // the blending PixiJS can do here ('lighter' = add); filters and visible shadows it cannot
  blend() {
    const g = this.globalCompositeOperation;
    if ((g !== 'source-over' && g !== 'lighter') || (this.filter && this.filter !== 'none') || (this.shadowBlur > 0 && !/^rgba\([^)]*,\s*0\)$/.test(this.shadowColor))) throw PXMiss;
    return g === 'lighter' ? 'add' : 'normal';
  }
  drawImage(img, sx, sy, sw, sh, dx, dy, dw, dh) {
    if (!img) return;
    const bm = this.blend(), iw = img.naturalWidth || img.width, ih = img.naturalHeight || img.height; if (!iw || !ih) return;
    let tex;
    if (dx === undefined) { dx = sx; dy = sy; dw = sw === undefined ? iw : sw; dh = sh === undefined ? ih : sh; sx = 0; sy = 0; sw = iw; sh = ih; tex = PX.whole(img); }
    else if (!sw || !sh) return;
    else if (!img._pxBig && iw * ih > 4e6) {   // a small piece of a big atlas (an icon): copied once into a picture of its own (no 60 MB texture)
      const x0 = Math.floor(sx), y0 = Math.floor(sy), k = x0 + ',' + y0 + ',' + Math.ceil(sx + sw - x0) + ',' + Math.ceil(sy + sh - y0), cr = PX.crop(img, k);
      tex = PX.frame(cr, sx - x0, sy - y0, sw, sh, 'p' + (sx - x0) + ',' + (sy - y0) + ',' + sw + ',' + sh, true);
      if (tex) { const kx = dw / sw, ky = dh / sh, fr = tex.frame, ox = dx + (fr.x - (sx - x0)) * kx, oy = dy + (fr.y - (sy - y0)) * ky;
        PX.qm(tex, this.a * kx, this.b * kx, this.c * ky, this.d * ky, this.a * ox + this.c * oy + this.e, this.b * ox + this.d * oy + this.f, this.ga, 0xffffff, bm); }
      return;
    }
    else tex = PX.frame(img, sx, sy, sw, sh, sx + ',' + sy + ',' + sw + ',' + sh, true);
    if (!tex) return;
    const kx = dw / sw, ky = dh / sh, fr = tex.frame, ox = dx + (fr.x - sx) * kx, oy = dy + (fr.y - sy) * ky;
    PX.qm(tex, this.a * kx, this.b * kx, this.c * ky, this.d * ky, this.a * ox + this.c * oy + this.e, this.b * ox + this.d * oy + this.f, this.ga, 0xffffff, bm);
  }
  fillRect(x, y, w, h) {
    if (!w || !h) return;
    const bm = this.blend(), c = PX.col(this.fillStyle); if (!c) throw PXMiss;
    PX.qm(PIXI.Texture.WHITE, this.a * w, this.b * w, this.c * h, this.d * h, this.a * x + this.c * y + this.e, this.b * x + this.d * y + this.f, this.ga * c[1], c[0], bm);
  }
  // paths: filled = whole ellipses / circles only (a filled shadow, a stunned monster's dots; a moveTo before one is
  // allowed). 0.95 (perf sweep: an outline anywhere sent a full-screen 2D layer to the GPU — the impact rings, the
  // strikes' circles, the webs, the clouds' dashed edges): stroked = ellipses, arcs and lines, laid as thin quads with
  // soft edges (PX.seg), dashes included. The lines' points are taken to the screen when given, as the 2D context does
  beginPath() { this.el.length = 0; this.pok = true; this.pl.length = 0; this.cur = null; }
  pt(x, y) { return [this.a * x + this.c * y + this.e, this.b * x + this.d * y + this.f]; }
  moveTo(x, y) { this.cur = { p: this.pt(x, y), closed: false }; this.pl.push(this.cur); }
  lineTo(x, y) { if (!this.cur) return this.moveTo(x, y); this.cur.p.push(...this.pt(x, y)); }
  closePath() { if (this.cur && this.cur.p.length > 2) { this.cur.closed = true; this.cur = { p: this.cur.p.slice(0, 2), closed: false }; this.pl.push(this.cur); } }
  ellipse(x, y, rx, ry, rot, a0, a1, ccw) {
    rot = rot || 0;
    if (Math.abs(a1 - a0) >= TAU - 1e-4) { this.el.push(x, y, rx, ry, rot); return; }
    this.pok = false;   // (a piece of an ellipse: strokable, not fillable here)
    if (!ccw) { while (a1 < a0) a1 += TAU; } else { while (a1 > a0) a1 -= TAU; }
    const n = Math.max(2, Math.ceil(Math.abs(a1 - a0) / TAU * PX.nEll(this, rx, ry))), co = Math.cos(rot), si = Math.sin(rot);
    for (let i = 0; i <= n; i++) {
      const t = a0 + (a1 - a0) * i / n, ex = rx * Math.cos(t), ey = ry * Math.sin(t), [X, Y] = this.pt(x + ex * co - ey * si, y + ex * si + ey * co);
      if (!this.cur) { this.cur = { p: [X, Y], closed: false }; this.pl.push(this.cur); } else this.cur.p.push(X, Y);
    }
  }
  arc(x, y, r, a0, a1, ccw) { this.ellipse(x, y, r, r, 0, a0, a1, ccw); }
  stroke() {
    const bm = this.blend(), c = PX.col(this.strokeStyle); if (!c) throw PXMiss;
    const k = Math.sqrt(Math.abs(this.a * this.d - this.b * this.c)), w = this.lineWidth * k, al = this.ga * c[1]; if (!(w > 0) || al <= 0.003) return;
    const dash = this.dash ? this.dash.map(v => v * k) : null, off = this.lineDashOffset * k, E = this.el;
    for (let i = 0; i < E.length; i += 5) {   // whole ellipses: their outline as a closed line
      const n = PX.nEll(this, E[i + 2], E[i + 3]), co = Math.cos(E[i + 4]), si = Math.sin(E[i + 4]), p = [];
      for (let j = 0; j < n; j++) { const t = j / n * TAU, ex = E[i + 2] * Math.cos(t), ey = E[i + 3] * Math.sin(t); p.push(...this.pt(E[i] + ex * co - ey * si, E[i + 1] + ex * si + ey * co)); }
      PX.line(p, true, w, c[0], al, bm, dash, off, false);
    }
    for (const L of this.pl) if (L.p.length > 2) PX.line(L.p, L.closed, w, c[0], al, bm, dash, off, this.lineCap === 'round' || this.lineJoin === 'round');
  }
  fill() {
    if (!this.pok || !this.el.length || this.pl.some(L => L.p.length > 2)) throw PXMiss;
    const bm = this.blend(), c = PX.col(this.fillStyle); if (!c) throw PXMiss;
    const t = PX.whole(PX._el, true), E = this.el;
    for (let i = 0; i < E.length; i += 5) {
      const co = Math.cos(E[i + 4]), si = Math.sin(E[i + 4]), sx = E[i + 2] / 127, sy = E[i + 3] / 63;
      // current · translate(x, y) · rotate(rot) · scale(sx, sy) · translate(-128, -64)
      const a = (this.a * co + this.c * si) * sx, b = (this.b * co + this.d * si) * sx, cc = (this.c * co - this.a * si) * sy, d = (this.d * co - this.b * si) * sy;
      const ex = this.a * E[i] + this.c * E[i + 1] + this.e - a * 128 - cc * 64, ey = this.b * E[i] + this.d * E[i + 1] + this.f - b * 128 - d * 64;
      PX.qm(t, a, b, cc, d, ex, ey, this.ga * c[1], c[0], bm);
    }
  }
  // what the 2D code may set without drawing
  setLineDash(a) { this.dash = a && a.length ? (a.length % 2 ? [...a, ...a] : a.slice()) : null; } getLineDash() { return this.dash ? this.dash.slice() : []; }
  // everything else draws in a way PixiJS does not here: the 2D code draws that part
  rect() { throw PXMiss; } roundRect() { throw PXMiss; } bezierCurveTo() { throw PXMiss; } quadraticCurveTo() { throw PXMiss; } arcTo() { throw PXMiss; }
  strokeRect() { throw PXMiss; } clearRect() { throw PXMiss; } clip() { throw PXMiss; } fillText() { throw PXMiss; } strokeText() { throw PXMiss; }
  measureText() { throw PXMiss; } createLinearGradient() { throw PXMiss; } createRadialGradient() { throw PXMiss; } createConicGradient() { throw PXMiss; } createPattern() { throw PXMiss; }
  getImageData() { throw PXMiss; } putImageData() { throw PXMiss; } isPointInPath() { throw PXMiss; }
}
const PX = {
  want: false, on: false, r: null, cv: null, stage: null, groundC: null, worldC: null, z: 1, wx: 0, wy: 0, mip: true,
  pool: [], n: 0, used: 0, srcs: new Set(), tiles: [], mini: null, gRun: null, gN: -1, shown: false, proxies: [], np: 0, _st: null, _st2: null, _el: null,
  sh: null, missK: new Set(), layers: [], nl: 0, L: null, _cc: new Map(), _pg: null, W: 1, H: 1, _m: null, gpool: [], gused: 0, gTouched: false, cont: null, gMask: null,
  // the renderer asked for: the address (?pixi=1 / ?pixi=0) first, then the profile's setting
  wanted() {
    const q = new URLSearchParams(location.search).get('pixi');
    if (q !== null) return q === '1';
    return true;   // (0.62: PixiJS by default; 0.95: always — the options' 'Renderer' row is gone, a saved 'canvas' is ignored)
  },
  // loads PixiJS and opens the WebGL canvas under the 2D one; false (and the 2D canvas draws everything) if it fails
  async init(top) {
    try {
      if (typeof PIXI === 'undefined') await new Promise((res, rej) => { const s = document.createElement('script'); s.src = vurl('lib/pixi.min.js'); s.onload = res; s.onerror = () => rej(new Error('lib/pixi.min.js')); document.head.append(s); });
      const cv = document.createElement('canvas'); cv.id = 'pixi'; cv.style.visibility = 'hidden'; top.parentNode.insertBefore(cv, top); this.cv = cv;
      const r = new PIXI.WebGLRenderer();
      // (no garbage collector: a texture let go after a minute unused came back with an upload hitch; textures are freed
      // with their images, Assets.release / PX.sweep)
      await r.init({ canvas: cv, width: Math.max(1, top.width), height: Math.max(1, top.height), resolution: 1, autoDensity: false, antialias: false, backgroundColor: 0x0d1410, backgroundAlpha: 1,
        powerPreference: 'high-performance', preferWebGLVersion: 2, hello: false, gcActive: false, textureGCActive: false, renderableGCActive: false });
      // 0.93: the GPU the browser really draws with (shown in the options: a PC with two GPUs may give a browser its
      // integrated one, where the exe asks for the high-performance one — tools/win/main.js)
      try { const gl = r.gl, ex = gl.getExtension('WEBGL_debug_renderer_info'), s = String(ex ? gl.getParameter(ex.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER)), m = /ANGLE \([^,]+, ([^,(]+?)\s*(\(|Direct3D|,|$)/.exec(s); let g = (m ? m[1] : s).trim(); const api = /^(Vulkan|OpenGL|Metal)/.test(g) && /(?:Vulkan|OpenGL ES|OpenGL|Metal)[\d. ]*\(([^()]+?)\s*(?:\(0x|\))/.exec(s); if (api) g = api[1].trim();
        this.gpu = /SwiftShader|llvmpipe|Software/i.test(s) ? 'SwiftShader (software)' : g.slice(0, 48); } catch (e) { this.gpu = null; }   // (0.94: through Vulkan / OpenGL the name is inside the API's brackets — it said 'Vulkan 1.3.0' —, a software renderer says so)
      this.r = r; this.stage = new PIXI.Container(); this.groundC = new PIXI.Container(); this.worldC = new PIXI.Container(); this.gfxC = new PIXI.Container();
      this.stage.addChild(this.groundC, this.gfxC, this.worldC);   // (0.95: gfxC, the ground effects under the scenery: PX.groundStart)
      this.on = true;
      // 0.91 (a Roublard run 'glitched', then every character was see-through, the spells invisible, icons gone,
      // until the game was closed): the GPU took the WebGL context back (driver reset, memory) and PixiJS drew nothing any
      // more — only the 2D layer on top was left (the character's faint copy, the HUD). Now the 2D canvas draws
      // everything from that moment on (the 'Canvas 2D' renderer), for the rest of the session
      cv.addEventListener('webglcontextlost', (e) => { e.preventDefault(); this.lose(); }, false);
    } catch (e) {
      console.warn('PixiJS unavailable: the 2D canvas draws everything', e); this.on = false;
      if (this.cv) { this.cv.remove(); this.cv = null; }
    }
    return this.on;
  },
  hide() { if (this.shown) { this.cv.style.visibility = 'hidden'; this.shown = false; } },
  lose() {
    if (!this.on) return;
    this.hide(); this.on = false; this.lost = true; GroundBuf.n = -1;   // (the 2D ground buffer is painted again)
    console.warn('WebGL context lost: the 2D canvas draws everything from now on');
    // (0.94: lost during the loading, before the game's texts are read, the message showed its key 'gl_lost': shown once
    // they are, main.js boot)
    const say = () => { try { if (typeof toast === 'function') toast(T('gl_lost')); } catch (e) { } };
    if (typeof Game !== 'undefined' && Game.C) say(); else this._lostMsg = say;
  },
  // ------------------------------------------------ textures
  // one TextureSource per picture (ImageBitmap, <img> or <canvas>), kept on it (img._pxs); mip: mipmaps (sprites drawn
  // smaller than their sheet, as the 'medium' / 'high' smoothing of the 2D canvas; never for the ground tiles, decoded
  // at about the size the screen shows them)
  src(img, mip = true) {
    let s = img._pxs; if (s && !s.destroyed) return s;
    const w = img.naturalWidth || img.width, h = img.naturalHeight || img.height; if (!w || !h) return null;
    const o = { resource: img, width: w, height: h, resolution: 1, autoGenerateMipmaps: mip && this.mip, scaleMode: 'linear' };
    s = img instanceof HTMLCanvasElement ? new PIXI.CanvasSource(o) : new PIXI.ImageSource(o);
    s.autoGarbageCollect = false; s._ft = new Map(); img._pxs = s; this.srcs.add(s);
    return s;
  },
  // a rectangle of a picture (a sheet frame), cached per picture and key
  frame(img, x, y, w, h, key, mip) {
    const s = this.src(img, mip); if (!s) return null;
    let t = s._ft.get(key);
    if (!t) {
      x = Math.min(Math.max(0, x), s.width - 1); y = Math.min(Math.max(0, y), s.height - 1);
      t = new PIXI.Texture({ source: s, frame: new PIXI.Rectangle(x, y, Math.max(0.01, Math.min(w, s.width - x)), Math.max(0.01, Math.min(h, s.height - y))) });
      s._ft.set(key, t);
    }
    return t;
  },
  whole(img, mip) {
    const s = this.src(img, mip); if (!s) return null;
    let t = s._ft.get('all'); if (!t) { t = new PIXI.Texture({ source: s }); s._ft.set('all', t); }
    return t;
  },
  forgetSrc(s) {
    this.srcs.delete(s); if (s.resource) s.resource._pxs = null;
    for (const sp of this.pool) if (sp.texture && sp.texture.source === s) { sp.texture = PIXI.Texture.EMPTY; sp.visible = false; }
    for (const sp of this.tiles) if (sp.texture && sp.texture.source === s) sp.texture = PIXI.Texture.EMPTY;
    if (this.mini && this.mini.texture.source === s) this.mini.texture = PIXI.Texture.EMPTY;
    for (const t of s._ft.values()) t.destroy(false);
    s.destroy();
  },
  // a picture let go (Assets.release): its texture goes with it
  forget(img) { const s = img && img._pxs; if (s && !s.destroyed) this.forgetSrc(s); },
  // a new run: the textures of pictures nothing uses any more go (white / tinted copies of dropped sheets, old caches)
  sweep(run) {
    const live = new Set([...RCache.m.values()]);
    for (const sh of Object.values(MobSheets.c)) if (sh) { live.add(sh.img); live.add(sh.white); for (const n in sh) if (n.startsWith('_tint')) live.add(sh[n]); }
    for (const im of Object.values(run.tiles || {})) live.add(im); live.add(run.mini);
    for (const im of this.common(run)) live.add(im);   // (0.62: the effect sheets stay on the GPU; 0.95: the run's own)
    for (const s of [...this.srcs]) if (!live.has(s.resource) && !(s.resource && s.resource._pxKeep)) this.forgetSrc(s);
    this.gRun = null;
  },
  // behind the loading screen: the run's sheets and tiles go to the GPU now, not mid-fight
  warm(run) {
    this.sweep(run); this.mip = Game.Q().smooth !== 'low';
    const ups = [];
    for (const im of Object.values(run.tiles)) if (im) ups.push(this.src(im, false));
    if (run.mini) ups.push(this.src(run.mini, false));
    for (const sh of Object.values(MobSheets.c)) if (sh && sh.img) { sh.img._pxBig = true; ups.push(this.src(sh.img, true)); if (sh.white) { sh.white._pxBig = true; ups.push(this.src(sh.white, true)); } }
    for (const im of this.common(run)) ups.push(this.src(im, true));
    for (const s of ups) if (s) try { this.r.texture.initSource(s); } catch (e) { }
    if (this.caF === undefined && !Game.minFx) this.caF = pxChroma(this.r);   // (0.98.2: its shader made now: it shows from the countdown's first frame)
  },
  // 0.62: what the parts drawn through PXCtx use most: the loaded effect sheets (icons come as pieces: PX.crop)
  // 0.95 (memory audit: the menu's idle loading decodes all 87 effect sheets; every one went to the GPU at a run's start,
  // the other classes' spells too — 350 MB at 1080p): only the sheets the run loads for itself (run.fxNeed: its class's
  // spells and fusions, the weapons, the global spells, the monsters' effects). Another one is sent on its first use
  common(run) {
    const out = [], need = run && run.fxNeed;
    for (const id in FxSheets.c) { const sh = FxSheets.c[id]; if (sh && sh.img && (!need || need.has(id))) { sh.img._pxBig = true; out.push(sh.img); } }
    return out;
  },
  // pictures made once here: a white ellipse (shadows), a four-point star (the Archimonsters' twinkles)
  pics() {
    if (this._el) return;
    const mk = (w, h, fn) => { const c = document.createElement('canvas'); c.width = w; c.height = h; fn(c.getContext('2d')); c._pxKeep = true; return c; };
    this._ln = mk(4, 16, g => { for (let j = 0; j < 16; j++) { const v = (j + 0.5) / 16; g.fillStyle = `rgba(255,255,255,${Math.min(1, Math.min(v, 1 - v) / 0.25).toFixed(3)})`; g.fillRect(0, j, 4, 1); } });   // (0.95: PX.seg's soft line)
    this._el = mk(256, 128, g => { g.fillStyle = '#fff'; g.beginPath(); g.ellipse(128, 64, 127, 63, 0, 0, TAU); g.fill(); });
    this._st2 = mk(68, 68, g => { g.fillStyle = '#fff'; g.beginPath(); for (let j = 0; j < 8; j++) { const an = j / 8 * TAU, rr = j % 2 ? 32 * 0.28 : 32; g.lineTo(34 + Math.cos(an) * rr, 34 + Math.sin(an) * rr); } g.closePath(); g.fill(); });
    this._st = mk(68, 68, g => { g.fillStyle = '#fffbe6'; g.beginPath(); for (let j = 0; j < 8; j++) { const an = j * Math.PI / 4, rr = j % 2 ? 32 * 0.22 : 32; j ? g.lineTo(34 + Math.cos(an) * rr, 34 + Math.sin(an) * rr) : g.moveTo(34 + Math.cos(an) * rr, 34 + Math.sin(an) * rr); } g.closePath(); g.fill(); });
  },
  // ------------------------------------------------ the frame
  begin(R, cx, cy, z, W, H, sx, sy) {
    if (this.r.width !== W || this.r.height !== H) this.r.resize(W, H);
    this.pics(); this.z = z; this.mip = Game.Q().smooth !== 'low';
    this.ground(R, cx, cy, z, W, H, sx, sy);
    this.wx = W / 2 - cx * z + sx; this.wy = H / 2 - cy * z + sy;
    this.worldC.position.set(this.wx, this.wy); this.worldC.scale.set(z); this.gfxC.position.set(this.wx, this.wy); this.gfxC.scale.set(z);
    this.n = 0; this.nl = 0; this.L = null; this.np = 0; this.W = W; this.H = H; this.gTouched = false;
    if (!this.sh) { this.sh = new PXCtx(); this._m = new PIXI.Matrix(); }
    this.sh.canvas.width = W; this.sh.canvas.height = H;
  },
  end() {
    for (let i = 0; i < this.nl; i++) this.layers[i].src.update();
    if (!this.gTouched) { for (let i = 0; i < this.gused; i++) this.gpool[i].visible = false; this.gused = 0; }   // (no ground effects drawn this frame)
    for (let i = this.n; i < this.used; i++) this.pool[i].visible = false;
    this.used = this.n;
    // 0.98: the chromatic aberration of the moment (this.ca 0..1, Run.chromaK), only while it shows: the frame is drawn into
    // a texture, then on the screen through the filter (a filter on the stage itself broke with the scenery's alpha mask)
    let ca = false;
    if (this.ca > 0.01 && this.caF !== false) {
      if (!this.caF) this.caF = pxChroma(this.r);
      if (this.caF) {
        // (made again at each new size — the adaptive resolution, a window resized, full screen: RenderTexture.resize left
        // the sprite showing it at the old size, the picture shifted and stretched until the effect ended; the old ones are
        // destroyed a few frames later, the renderer still holds the last target for a frame)
        if (!this.caRT || this.caRT.width !== this.W || this.caRT.height !== this.H) {
          if (this.caRT) (this.caOld || (this.caOld = [])).push([this.caRT, this.caRoot, 3]);
          this.caRT = PIXI.RenderTexture.create({ width: this.W, height: this.H, resolution: 1 }); this.caS = new PIXI.Sprite(this.caRT); this.caS.filters = [this.caF]; this.caRoot = new PIXI.Container(); this.caRoot.addChild(this.caS);
        }
        this.caF.resources.caU.uniforms.uStrength = 0.03 * Math.pow(Math.min(1, this.ca / 2.6), 0.75);   // (the smear's reach: ~1.5 % of the screen at the edge at most, the victory)
        this.r.render({ container: this.stage, target: this.caRT, clear: true }); this.r.render(this.caRoot); ca = true;
      }
    }
    if (!ca) this.r.render(this.stage);
    if (this.caOld && this.caOld.length) this.caOld = this.caOld.filter(o => { if (--o[2] > 0) return true; o[1].destroy({ children: true }); o[0].destroy(true); return false; });
    if (!this.shown) { this.cv.style.visibility = 'visible'; this.shown = true; }
  },
  // the next quad of the frame: texture tex at (x, y) (its top-left corner, or its centre with ax 0.5), scale sx / sy
  // (negative sx = mirrored), opacity a, tint (0xffffff = none), rotation rot
  q(tex, x, y, sx, sy, a, tint = 0xffffff, ax = 0, rot = 0) {
    if (!tex || a <= 0.003) return null;
    let s = this.pool[this.n];
    if (!s) { s = new PIXI.Sprite(); (this.cont || this.worldC).addChild(s); this.pool.push(s); }
    this.n++;
    // (0.95, profiles: the tint / anchor / rotation setters did their work even unchanged — set only what changed)
    if (s.texture !== tex) s.texture = tex; s.position.set(x, y); s.scale.set(sx, sy); const al = a > 1 ? 1 : a; if (s.alpha !== al) s.alpha = al;
    if (s._tn !== tint) { s.tint = tint; s._tn = tint; } if (s._ax !== ax) { s.anchor.set(ax); s._ax = ax; } if (s.rotation !== rot) s.rotation = rot; s.visible = true;
    if (s._sk) { s.skew.set(0, 0); s._sk = false; } if (s._bm) { s.blendMode = 'normal'; s._bm = false; }
    return s;
  },
  // a quad from a 2D-context transform (screen pixels, PXCtx): texture pixel (u, v) lands at (a u + c v + e, b u + d v + f)
  qm(tex, a, b, c, d, e, f, al, tint, bm) {
    if (al <= 0.003) return;
    const z = this.z;
    if (b === 0 && c === 0) { const s = this.q(tex, (e - this.wx) / z, (f - this.wy) / z, a / z, d / z, al, tint); if (s && bm === 'add') { s.blendMode = 'add'; s._bm = true; } return; }   // (0.95: not rotated: no decomposition)
    const M = this._m; M.a = a / z; M.b = b / z; M.c = c / z; M.d = d / z; M.tx = (e - this.wx) / z; M.ty = (f - this.wy) / z;
    const s = this.q(tex, 0, 0, 1, 1, al, tint); if (!s) return;
    s.setFromMatrix(M); if (s.skew.x || s.skew.y) s._sk = true;
    if (bm === 'add') { s.blendMode = 'add'; s._bm = true; }
  },
  // a piece x0,y0,w,h of a big picture as a canvas of its own (cached on the picture)
  crop(img, k) {
    const m = img._pxc || (img._pxc = new Map()); let c = m.get(k); if (c) return c;
    const [x0, y0, w, h] = k.split(',').map(Number); c = document.createElement('canvas'); c.width = Math.max(1, w); c.height = Math.max(1, h);
    c.getContext('2d').drawImage(img, x0, y0, w, h, 0, 0, w, h); c._pxKeep = true; m.set(k, c); return c;
  },
  // a CSS colour -> [tint, alpha] (cached; null for gradients / patterns)
  col(v) {
    if (typeof v !== 'string') return null;
    let c = this._cc.get(v); if (c) return c;
    const g = this._pg || (this._pg = document.createElement('canvas').getContext('2d'));
    g.fillStyle = '#000'; g.fillStyle = v; const w = g.fillStyle;
    if (w[0] === '#') c = [parseInt(w.slice(1, 7), 16), 1];
    else { const m = w.match(/[\d.]+/g) || [0, 0, 0, 1]; c = [(+m[0] << 16) | (+m[1] << 8) | +m[2], m[3] === undefined ? 1 : +m[3]]; }
    if (this._cc.size > 4000) this._cc.clear();
    this._cc.set(v, c); return c;
  },
  // 0.62: a part of the scene drawn by the game's 2D code, at its place in the drawing order: first on PXCtx (quads);
  // if it draws something PixiJS cannot, what it laid is taken back and it draws again with the 2D code, into the
  // current full-screen 2D layer (or a small box of its own, box = [x0, y0, x1, y1] in world units: things standing
  // among the monsters). key: that kind of drawing is remembered as 2D only (no first try any more)
  nat(key, fn, box) {
    if (!key || !this.missK.has(key)) {
      const m = this.n; this.sh.reset(this.z, this.wx, this.wy);
      try { fn(this.sh); return; } catch (e) {
        if (e !== PXMiss) throw e;
        for (let i = m; i < this.n; i++) this.pool[i].visible = false;
        this.n = m; if (key) this.missK.add(key);
      }
    }
    if (box) this.proxy(box[0], box[1], box[2], box[3], fn); else fn(this.layer());
  },
  // 0.95 (perf sweep: every frame sent a full-screen 2D layer to the GPU — the ground effects, if only the character's
  // ring — erased under the scenery by the 2D code): the ground effects (Run.underDecor) are laid as quads in a container
  // of their own (gfxC, between the ground and the world), hidden under the world's tall scenery by the GPU: the part of
  // the decor mask on screen (M, K px a world unit) as an inverted alpha mask. What they draw that PixiJS cannot still goes
  // into a 2D layer, inside that container (masked the same way)
  groundStart(M, K) {
    const z = this.z, wx0 = -this.wx / z, wy0 = -this.wy / z, wx1 = (this.W - this.wx) / z, wy1 = (this.H - this.wy) / z;
    const x0 = Math.max(0, Math.floor(wx0 * K)), y0 = Math.max(0, Math.floor(wy0 * K)), x1 = M ? Math.min(M.width, Math.ceil(wx1 * K) + 1) : 0, y1 = M ? Math.min(M.height, Math.ceil(wy1 * K) + 1) : 0;
    const src = M && x1 > x0 && y1 > y0 ? this.src(M, false) : null, ms = this.gMask || (this.gMask = this.gfxC.addChild(new PIXI.Sprite()));
    if (src) {
      const old = ms.texture; ms.texture = new PIXI.Texture({ source: src, frame: new PIXI.Rectangle(x0, y0, x1 - x0, y1 - y0) }); if (old && old._pxGm) old.destroy(false); ms.texture._pxGm = true;
      ms.position.set(x0 / K, y0 / K); ms.scale.set(1 / K); if (this.gfxC.mask !== ms) this.gfxC.setMask({ mask: ms, inverse: true });
    } else if (this.gfxC.mask) this.gfxC.mask = null;
    const B = this.gfxC.boundsArea || (this.gfxC.boundsArea = new PIXI.Rectangle()); B.x = wx0; B.y = wy0; B.width = wx1 - wx0; B.height = wy1 - wy0;   // (the screen: PixiJS no longer measures every quad to size the mask's pass)
    this._mp = [this.pool, this.n]; this.pool = this.gpool; this.n = 0; this.cont = this.gfxC; this.L = null;
  },
  groundEnd() {
    for (let i = this.n; i < this.gused; i++) this.gpool[i].visible = false;
    this.gused = this.n; this.gTouched = true; this.gpool = this.pool; [this.pool, this.n] = this._mp; this.cont = null; this.L = null;
  },
  // 0.88: a full-screen 2D layer of its own at this point of the order, even if the last one could be reused (Run.underDecor
  // erases in it: nothing drawn before may share it)
  freshLayer() { this.L = null; return this.layer(); },
  // the full-screen 2D layer at this point of the drawing order (the same one while nothing else was laid since; at most
  // 8 a frame, then the last one); its context comes in world units, as the run's 2D canvas
  layer() {
    let L = this.L;
    if (!L || L.at !== this.n) {
      if (this.nl >= 8) L = this.layers[this.nl - 1];
      else {
        L = this.layers[this.nl];
        if (!L || L.c.width !== this.W || L.c.height !== this.H) {
          if (L) { L.tex.destroy(false); L.src.destroy(); }
          const c = L ? L.c : document.createElement('canvas'); c.width = this.W; c.height = this.H;
          L = this.layers[this.nl] = { c, g: c.getContext('2d'), src: null, tex: null, at: -1 };
          L.src = new PIXI.CanvasSource({ resource: c, width: c.width, height: c.height, resolution: 1, autoGenerateMipmaps: false, scaleMode: 'linear' }); L.src.autoGarbageCollect = false;
          L.tex = new PIXI.Texture({ source: L.src });
        }
        const g = L.g; g.setTransform(1, 0, 0, 1, 0, 0); g.globalAlpha = 1; g.globalCompositeOperation = 'source-over'; g.clearRect(0, 0, this.W, this.H);
        this.nl++;
        this.q(L.tex, -this.wx / this.z, -this.wy / this.z, 1 / this.z, 1 / this.z, 1); L.at = this.n;
      }
      this.L = L;
    }
    const g = L.g; g.setTransform(this.z, 0, 0, this.z, this.wx, this.wy); g.globalAlpha = 1; g.globalCompositeOperation = 'source-over';
    g.imageSmoothingEnabled = true; g.imageSmoothingQuality = Game.lowFx ? 'low' : Game.Q().smooth;
    return g;
  },
  // the particles (Run.draw's loop): squares, round puffs, eight-point stars
  particles(list, inView) {
    const st = this.whole(this._st2, true);
    for (const p of list) {
      if (!inView(p.x, p.y, 10)) continue;
      const k = 1 - p.t / p.life, c = this.col(p.c); if (!c) continue;
      if (p.star) { const r = p.s * (0.6 + k * 0.6); this.q(st, p.x, p.y, r / 32, r / 32, k * c[1], c[0], 0.5); }
      else if (p.round) { const r = p.s / 2 * (1 + (p.grow || 0) * (1 - k)); this.ell(p.x, p.y, r, r, c[0], k * 0.55 * c[1]); }
      else this.rect(p.x - p.s / 2, p.y - p.s / 2, p.s, p.s, c[0], k * c[1]);
    }
  },
  // a whole picture in the box (dx, dy, dw, dh), like ctx.drawImage(im, dx, dy, dw, dh)
  pic(im, dx, dy, dw, dh, a, tint) { if (!im) return; const t = this.whole(im); if (t) this.q(t, dx, dy, dw / t.width, dh / t.height, a, tint); },
  // a sheet frame, like Sheet.draw (sheets decoded smaller: img._k; the white flash copies: img.k)
  sheet(sh, f, x, y, scale, flip, img, a) {
    img = img || sh.img; if (!f || !img) return;
    const k = img.k || img._k || 1, s = scale / sh.zoom, t = this.frame(img, f[0] * k, f[1] * k, f[2] * k, f[3] * k, f, true); if (!t) return;
    this.q(t, flip ? x + f[4] * s : x - f[4] * s, y - f[5] * s, (flip ? -s : s) / k, s / k, a);
  },
  ell(x, y, rx, ry, tint, a) { const t = this.whole(this._el, true); this.q(t, x, y, rx / 127, ry / 63, a, tint, 0.5); },
  // 0.95: how many straight pieces an ellipse's outline takes on screen (one per ~8 px, 12 to 96)
  nEll(g, rx, ry) { const sx = Math.hypot(g.a, g.b), sy = Math.hypot(g.c, g.d), p = TAU * Math.sqrt(((rx * sx) ** 2 + (ry * sy) ** 2) / 2); return Math.max(12, Math.min(96, Math.ceil(p / 8))); },
  // a stroked line through the screen points p (x, y, x, y…), cut by the dash pattern (screen px); round: dots at its
  // points (round caps / joins) when it is thick and opaque enough for the gaps to show
  line(p, closed, w, tint, al, bm, dash, off, round) {
    const n = p.length / 2, m = closed ? n : n - 1; if (m < 1) return;
    const tot = dash ? dash.reduce((s, v) => s + v, 0) : 0, pat = tot > 0.5 ? dash : null; let di = 0, left = 0, on = true;
    if (pat) { let o = ((off % tot) + tot) % tot; while (o >= pat[di]) { o -= pat[di]; di = (di + 1) % pat.length; on = !on; } left = pat[di] - o; }
    for (let i = 0; i < m; i++) {
      const x0 = p[i * 2], y0 = p[i * 2 + 1], j = (i + 1) % n, x1 = p[j * 2], y1 = p[j * 2 + 1], L = Math.hypot(x1 - x0, y1 - y0); if (L < 1e-3) continue;
      if (!pat) { this.seg(x0, y0, x1, y1, L, w, tint, al, bm); continue; }
      let u = 0;
      while (u < L) {
        const v = Math.min(L, u + left);
        if (on && v - u > 0.05) this.seg(x0 + (x1 - x0) * u / L, y0 + (y1 - y0) * u / L, x0 + (x1 - x0) * v / L, y0 + (y1 - y0) * v / L, v - u, w, tint, al, bm);
        left -= v - u; u = v; if (left <= 1e-6) { di = (di + 1) % pat.length; left = pat[di]; on = !on; }
      }
    }
    if (round && !pat && w > 2.5 && al > 0.85) for (let i = 0; i < n; i++) this.qd(p[i * 2], p[i * 2 + 1], w, tint, al, bm);
  },
  // one piece of a line, x0,y0 -> x1,y1 (screen px, L long), w px thick: the soft line picture (_ln: an opaque middle
  // half, its edges fading over a quarter each side: as thick on the whole as w) stretched along it
  seg(x0, y0, x1, y1, L, w, tint, al, bm) {
    const t = this.whole(this._ln, false), h = w / 0.75, nx = -(y1 - y0) / L, ny = (x1 - x0) / L, z = this.z;   // (a rotation and a scale: no matrix decomposition)
    const s = this.q(t, (x0 - nx * h / 2 - this.wx) / z, (y0 - ny * h / 2 - this.wy) / z, L / 4 / z, h / 16 / z, al, tint, 0, Math.atan2(y1 - y0, x1 - x0)); if (s && bm === 'add') { s.blendMode = 'add'; s._bm = true; }
  },
  qd(x, y, w, tint, al, bm) { const t = this.whole(this._el, true); this.qm(t, w / 254, 0, 0, w / 126, x - w / 2, y - w / 2, al, tint, bm); },   // (a round dot, w px across)
  rect(x, y, w, h, tint, a) { if (w > 0 && h > 0) this.q(PIXI.Texture.WHITE, x, y, w, h, a, tint); },
  // ------------------------------------------------ what PixiJS draws
  // the map tiles (whole tiles overlapping the next one by 2 screen px, as paintGround), the small map under tiles still
  // streaming in; the ground snaps to whole screen pixels like the 2D ground buffer
  ground(R, cx, cy, z, W, H, sx, sy) {
    const Wd = R.world, T = Wd.tile, res = Wd.res || 1, G = this.groundC;
    let fresh = this.gRun !== R || this.gN !== (R.tilesN || 0);
    if (!fresh) for (const sp of this.tiles) if (R.tiles[sp._key] !== sp._im) { fresh = true; break; }
    if (fresh) {
      G.removeChildren(); this.tiles = []; this.gRun = R; this.gN = R.tilesN || 0;
      this.mini = R.mini ? new PIXI.Sprite(this.whole(R.mini, false)) : null;
      if (this.mini) { this.mini.width = Wd.w; this.mini.height = Wd.h; G.addChild(this.mini); }
      for (const key in R.tiles) {
        const im = R.tiles[key], t = im && this.whole(im, false); if (!t) continue;
        const [tx, ty] = key.split(',').map(Number), sp = new PIXI.Sprite(t); sp._key = key; sp._im = im; sp._tx = tx; sp._ty = ty;
        G.addChild(sp); this.tiles.push(sp);
      }
    }
    G.position.set(Math.round(W / 2 - cx * z + sx), Math.round(H / 2 - cy * z + sy)); G.scale.set(z);
    const vx0 = cx - W / 2 / z, vy0 = cy - H / 2 / z, vx1 = cx + W / 2 / z, vy1 = cy + H / 2 / z, ov = 2 / z;
    for (const sp of this.tiles) {
      const x0 = sp._tx * T, y0 = sp._ty * T, im = sp._im, r = res * (im._k || 1);
      const w = (sp._tx + 1) * T >= Wd.w - 1 ? im.width / r : T + ov, h = (sp._ty + 1) * T >= Wd.h - 1 ? im.height / r : T + ov;
      sp.visible = x0 < vx1 && x0 + w > vx0 && y0 < vy1 && y0 + h > vy0;
      if (sp.visible) { sp.position.set(x0, y0); sp.width = w; sp.height = h; }
    }
    if (this.mini) {
      let missing = false;
      const tx0 = Math.max(0, Math.floor(vx0 / T)), tx1 = Math.floor(vx1 / T), ty0 = Math.max(0, Math.floor(vy0 / T)), ty1 = Math.floor(vy1 / T);
      for (let ty = ty0; ty <= ty1 && !missing; ty++) for (let tx = tx0; tx <= tx1; tx++) if (!R.tiles[tx + ',' + ty] && tx * T < Wd.w && ty * T < Wd.h) { missing = true; break; }
      this.mini.visible = missing;
    }
  },
  outside(b, vx0, vy0, vx1, vy1) {
    this.rect(vx0, vy0, b.x0 - vx0, vy1 - vy0, 0, 0.35); this.rect(b.x1, vy0, vx1 - b.x1, vy1 - vy0, 0, 0.35);
    this.rect(b.x0, vy0, b.x1 - b.x0, b.y0 - vy0, 0, 0.35); this.rect(b.x0, b.y1, b.x1 - b.x0, vy1 - b.y1, 0, 0.35);
  },
  shadows(mobs, inView) {
    for (const m of mobs) { if (m.dying || m.carried || !inView(m.x, m.y, 60)) continue; const rx = mobShadowR(m); this.ell(m.x, m.y, rx, rx * 0.42, 0, MOB_SHADOW_A); }   // (0.95: render.js mobShadowR)
  },
  // a monster, as drawMob: glow, body, flash, sheen, poison / bleed here; the life drain and the marks over it on the 2D canvas
  mob(m, t, frozen) {
    const q = mobPose(m, t, frozen); if (!q) return;
    const { sh, shD, f, flip, a, ly, sc, anim } = q;
    if (!m.dying && (m.elite || m.confuseUntil > t)) { const r = m.r * 2.6 * sc; this.pic(RCache.glow(m.elite ? 'rgba(255,210,74,0.75)' : m.poisonUntil > t ? 'rgba(120,230,80,0.6)' : 'rgba(156,255,106,0.6)'), m.x - r, ly - m.r * 1.6 * sc - r, r * 2, r * 2, a * 0.8); }
    this.sheet(shD, f, m.x, ly, sc, flip, m.tint ? tintedSheet(shD, m.tint) : undefined, a);
    if (m.flash > 0 && !m.dying && shD.white) this.sheet(shD, f, m.x, ly, sc, flip, shD.white, Math.min(0.85, m.flash) * a);
    if (m.archi && !m.dying) this.shiny(m, sh, f, ly, sc, flip, a, t);
    if (!m.dying && (m.bleedUntil > t || m.poisonUntil > t)) this.status(m, sh, anim, ly, sc, t);
    if (t - (m.drainT || -9) < 0.5 && !m.dying) { const R0 = (m.r * 1.6 * sc + 8) * 1.35; this.nat('drain', g => drawDrainMob(g, m, t, ly, sc), [m.x - R0 - 4, ly - m.r * 1.5 * sc - R0 - 4, m.x + R0 + 4, m.y + m.r * 0.6 * sc + 10]); }
    // (0.62: the marks / names / life bars over it at its depth too, no longer over every effect)
    const mw = Math.max(90, m.r * 2 * sc + 20), mt = Math.max(m.r * 3.6 * sc, mobTop(m, sh, anim, sc) + 30); this.nat(null, g => drawMobMarks(g, m, t, sh, anim, ly, sc, false), [m.x - mw, ly - mt - 60, m.x + mw, m.y + 16]);
  },
  // drawShiny: a pale sheen over the monster, little four-point stars twinkling around it
  shiny(m, sh, f, ly, sc, flip, a, t) {
    if (sh.white) this.sheet(sh, f, m.x, ly, sc, flip, sh.white, a * (0.1 + 0.16 * Math.max(0, Math.sin(t * 3.2 + m.x * 0.01))));
    const R = m.r * sc, st = this.whole(this._st, true);
    for (let i = 0; i < 4; i++) {
      const q = t * 1.1 + i / 4, ph = q % 1, k = Math.floor(q) * 2.7 + i * 1.9;
      const x = m.x + Math.cos(k) * R * 1.3, y = ly - R * 1.7 + Math.sin(k * 1.3) * R * 1.3, s = (4 + 5 * Math.sin(ph * Math.PI)) * Math.max(1, sc * 0.8), al = a * Math.sin(ph * Math.PI);
      this.pic(RCache.glow('rgba(255,236,150,0.9)'), x - s * 1.6, y - s * 1.6, s * 3.2, s * 3.2, al);
      this.q(st, x, y, s / 32, s / 32, al, 0xffffff, 0.5, t * 1.5);
    }
  },
  // drawStatus (0.68: the subtle auras of render.js drawStatus, same maths)
  status(m, sh, anim, ly, sc, t) {
    const wf = (sh.anims.walkR || sh.anims[anim]).f[0], top = (m._top || (m._top = wf[5] * sc / sh.zoom));
    const ph0 = m._gph || (m._gph = Math.random() * 10), full = m._fullFx && !Game.lowFx, R0 = Math.max(m.r * 1.2 * sc, top * 0.45);
    const aura = (c1, c2, n, rise, speed) => {
      this.pic(RCache.glow(c1), m.x - R0 * 1.15, ly - R0 * 0.42, R0 * 2.3, R0 * 0.84, 0.32 * (0.75 + 0.25 * Math.sin(t * 3 + ph0)));
      for (let i = 0; i < n; i++) {
        const q = (t * speed + i / n + ph0) % 1, a = ph0 * 3 + i * 2.399, sx = m.x + Math.cos(a + t * 0.8) * R0 * 0.55;
        const y = rise ? ly - q * top * 1.05 : ly - top * 0.75 + q * top * 0.7, w = (rise ? 2.6 + 2.4 * Math.sin(q * Math.PI) : 3.4 - 1.6 * q) * Math.max(1, sc * 0.9);
        this.pic(RCache.glow(i % 3 === 2 ? c2 : c1), sx - w * 2.2, y - w * 2.2, w * 4.4, w * 4.4, 0.7 * Math.sin(q * Math.PI));
      }
    };
    if (m.poisonUntil > t) aura('rgba(95,230,70,0.95)', 'rgba(175,95,240,0.95)', full ? 6 : 2, true, 0.55);
    if (m.bleedUntil > t) aura('rgba(225,25,45,0.95)', 'rgba(140,0,20,0.95)', full ? 5 : 2, false, 0.75);
  },
  drop(kind, x, y, a) { const c = RCache.drop(kind); this.pic(c, x + c.x0, y + c.y0, c.w, c.h, a); },
  // a summon drawn from a monster sheet (drawSummon's last case)
  summon(s, t) {
    const sh = s.sh, k = clamp((s.until - t) / 0.4, 0, 1);
    let anim = 'walkR', at = s.t, loop = true;
    if (s.atkT !== undefined && sh.has('atkR') && s.atkT < sh.duration('atkR')) { anim = 'atkR'; at = s.atkT; loop = false; }
    const f = sh.frameAt(anim, at, loop); if (!f) return;
    const ga = Math.min(1, (t - s.born) * 4) * k;
    const sk = s.spell.p.sumK || 1;   // (0.98.3: the Bomberfus)
    this.ell(s.x, s.y, 16 * sk, 6 * sk, s.healer ? 0x78ff96 : 0x50a0ff, (s.healer ? 0.3 : 0.25) * ga);
    this.sheet(sh, f, s.x, s.fly ? s.y - 8 + Math.sin(t * 5) * 3 : s.y, 0.9 * ES * sk, s.flip, undefined, ga);
  },
  // the player at its depth among the monsters: everything its 2D drawing paints around it (dash trail, auras,
  // revival wings, drain, life bar) in one box
  player(P, draw) {
    let x0 = P.x, x1 = P.x, y0 = P.y - (P.leapH || 0), y1 = P.y;
    for (const tr of P.trail) { if (tr.x < x0) x0 = tr.x; if (tr.x > x1) x1 = tr.x; if (tr.y < y0) y0 = tr.y; if (tr.y > y1) y1 = tr.y; }
    const k = (P._drawn && P._drawn.sc) || 1;   // (0.91: the Otomaï grown by his mutation)
    this.proxy(x0 - 150 * k, y0 - 240 * k, x1 + 150 * k, y1 + 60, draw);
  },
  // a part of the scene still drawn by the 2D code, kept at its place in the drawing order: drawn into a small canvas of
  // its own (the world box bx0..bx1 x by0..by1 at screen resolution, on whole screen pixels so the texture lands 1:1)
  // that becomes a texture this frame
  proxy(bx0, by0, bx1, by1, draw) {
    const z = this.z, X0 = Math.floor(this.wx + bx0 * z), Y0 = Math.floor(this.wy + by0 * z), w = Math.ceil(this.wx + bx1 * z) - X0, h = Math.ceil(this.wy + by1 * z) - Y0;
    if (w <= 0 || h <= 0) return;
    let P = this.proxies[this.np++];
    if (!P) P = this.proxies[this.np - 1] = { c: document.createElement('canvas'), g: null, src: null, tex: null };
    const c = P.c;
    // 0.93 (stress tests: ~13 new GPU textures a second in a big fight — the box of each slot changes size every frame: the
    // character's dash trail, the monsters' marks): sizes by steps of 128 px, grown when needed, shrunk only after 90
    // frames in a row far too big (after a dash)
    P.small = P.src && w * h * 6 < c.width * c.height ? (P.small || 0) + 1 : 0;
    if (!P.src || w > c.width || h > c.height || P.small > 90) {
      if (P.src) { P.tex.destroy(false); P.src.destroy(); }
      const grow = P.src && P.small <= 90, st = n => Math.ceil((n + 16) / 128) * 128;
      c.width = grow ? Math.max(c.width, st(w)) : st(w); c.height = grow ? Math.max(c.height, st(h)) : st(h); P.g = c.getContext('2d'); P.small = 0;
      P.src = new PIXI.CanvasSource({ resource: c, width: c.width, height: c.height, resolution: 1, autoGenerateMipmaps: false, scaleMode: 'linear' }); P.src.autoGarbageCollect = false;
      P.tex = new PIXI.Texture({ source: P.src });
    }
    const g = P.g; g.setTransform(1, 0, 0, 1, 0, 0); g.globalAlpha = 1; g.globalCompositeOperation = 'source-over'; g.clearRect(0, 0, c.width, c.height);
    g.setTransform(z, 0, 0, z, this.wx - X0, this.wy - Y0);   // world -> this canvas (its corner is the screen pixel X0, Y0)
    g.imageSmoothingEnabled = true; g.imageSmoothingQuality = Game.lowFx ? 'low' : Game.Q().smooth;
    draw(g);
    P.src.update();
    this.q(P.tex, (X0 - this.wx) / z, (Y0 - this.wy) / z, 1 / z, 1 / z, 1);
  },
};
// 0.98: the chromatic aberration (PX.end, Run.chromaK), like a lens: the centre stays sharp, towards the edges the picture
// is smeared along the radius over 9 taps weighted by colour (red outwards, green in the middle, blue inwards): a soft
// blur with small colour fringes. (A first version sampled red and blue apart by an offset growing with the strength:
// strong, it showed two shifted copies of the screen, jumping with the screen shake.) False when PixiJS cannot make it. (The frame's sizes stay in the vertex shader:
// a uniform in both shaders at different precisions does not link — the screen went black, the context lost)
function pxChroma(r) {
  try {
    const vertex = `in vec2 aPosition;
out vec2 vTextureCoord;
out vec2 vCenter;
uniform vec4 uInputSize;
uniform vec4 uOutputFrame;
uniform vec4 uOutputTexture;
void main(void) {
  vec2 position = aPosition * uOutputFrame.zw + uOutputFrame.xy;
  position.x = position.x * (2.0 / uOutputTexture.x) - 1.0;
  position.y = position.y * (2.0 * uOutputTexture.z / uOutputTexture.y) - uOutputTexture.z;
  gl_Position = vec4(position, 0.0, 1.0);
  vTextureCoord = aPosition * (uOutputFrame.zw * uInputSize.zw);
  vCenter = uOutputFrame.zw * uInputSize.zw * 0.5;
}`;
    const fragment = `in vec2 vTextureCoord;
in vec2 vCenter;
out vec4 finalColor;
uniform sampler2D uTexture;
uniform float uStrength;
uniform vec4 uInputClamp;
void main(void) {
  vec2 dir = vTextureCoord - vCenter;
  float edge = smoothstep(0.25, 1.15, length(dir / vCenter));
  vec2 d = dir * uStrength * edge;
  vec3 acc = vec3(0.0), ws = vec3(0.0);
  for (int i = 0; i < 9; i++) {
    float t = float(i) / 8.0;
    vec3 s = texture(uTexture, clamp(vTextureCoord + d * (t * 2.0 - 1.0), uInputClamp.xy, uInputClamp.zw)).rgb;
    vec3 w = vec3(t * t, 1.0 - abs(t * 2.0 - 1.0) * 0.8, (1.0 - t) * (1.0 - t));
    acc += s * w; ws += w;
  }
  finalColor = vec4(acc / ws, texture(uTexture, vTextureCoord).a);
}`;
    const f = new PIXI.Filter({ glProgram: PIXI.GlProgram.from({ vertex, fragment, name: 'rs-chroma' }), resources: { caU: { uStrength: { value: 0, type: 'f32' } } }, resolution: 1 });   // (resolution 1: 'inherit' on the stage itself found no parent to read)
    // a trial on a tiny texture first: a GPU that cannot run it gets no effect rather than a broken picture
    const gl = r.gl; while (gl.getError()) { }
    const c = new PIXI.Container(), sp = c.addChild(new PIXI.Sprite(PIXI.Texture.WHITE)), rt = PIXI.RenderTexture.create({ width: 8, height: 8 }); sp.width = sp.height = 8; c.filters = [f];
    r.render({ container: c, target: rt }); const bad = gl.getError() || gl.isContextLost(); f._trial = [c, rt];   // (kept: destroyed at once, the renderer still read its target next frame)
    if (bad) { console.warn('chromatic aberration unavailable on this GPU'); return false; }
    return f;
  } catch (e) { console.warn('chromatic aberration unavailable', e); return false; }
}
