'use strict';
// ---------------------------------------------------------------- asset loading
let SPR = null; // merged sprite metadata (data/sprites.json)
// every data / image URL carries the build: a browser never mixes files of two versions from its cache
const BUILD = '0.96';
const vurl = (u) => u + (u.includes('?') ? '&' : '?') + 'v=' + BUILD;
// 0.93: a versioned file never changes: on the published web version (https, not this machine) the browser takes its
// cached copy without asking the server again (one revalidation round trip per file at each start); at home (the local
// server, the exe's rs://) the files may change between two builds: the normal cache rules stay
const FETCH_OPT = typeof location !== 'undefined' && location.protocol === 'https:' && !/^(localhost|127\.|\[::1\])/.test(location.hostname) ? { cache: 'force-cache' } : undefined;
// 0.44: three picture qualities instead of the performance mode. Each caps the render buffer (720p / 1080p /
// 1440p, whatever the screen), decodes the sprite sheets (characters, accessories, monsters, effects) at a share of
// their size (k), the ground tiles coarser, smooths the scaled sprites more or less finely and keeps more or fewer
// particles (fx: 0 = few, 2 = all). UHD is the game as drawn.
const QUALITY = {
  sd: { w: 1280, h: 720, k: 0.5, tile: 0.6, fx: 0, smooth: 'low' },
  hd: { w: 1920, h: 1080, k: 0.75, tile: 0.8, fx: 1, smooth: 'medium' },
  uhd: { w: 2560, h: 1440, k: 1, tile: 1, fx: 2, smooth: 'high' },
  k4: { w: 3840, h: 2160, k: 1, tile: 1, fx: 2, smooth: 'high' },   // 0.85: 4K UHD; the keys stay (saves), the labels are resolutions (QUALITY_LABEL)
};
const QUALITY_LABEL = { sd: '720p', hd: '1080p', uhd: 'QHD 1440p', k4: '4K 2160p' };
// 0.93: the Windows / Linux build (Electron, tools/win/main.js: the game served from 'rs://'): its default quality is the
// screen's own resolution (Game.quality), the web version's 1080p
const IS_APP = typeof location !== 'undefined' && location.protocol === 'rs:';
const Assets = {
  json: {}, img: {}, pending: 0,
  loadJSON(url) {
    if (this.json[url]) return Promise.resolve(this.json[url]);
    return fetch(vurl(url), FETCH_OPT).then(r => { if (!r.ok) throw new Error(url + ' ' + r.status); return r.json(); }).then(j => (this.json[url] = j));
  },
  // k < 1: decoded at a reduced size (the big map tiles on screens / devices that cannot show or hold them in full)
  // (0.44: one cache entry per size: the qualities decode the same file at different sizes)
  key(url, k) { return k < 0.999 ? url + '#' + k.toFixed(2) : url; },
  loadImg(url, k = 1) {
    const key = this.key(url, k);
    if (this.img[key]) return this.img[key].ready;
    // 0.93 (stress tests: 100-420 ms frozen frames at a run's start, each one a sheet being decoded): the file is fetched
    // and decoded from its bytes (createImageBitmap of a Blob: off the main thread in Chrome / Electron — 0 ms blocked for
    // a 4092 x 2940 sheet, against 110-320 ms through an <img> then createImageBitmap); a smaller size (k) is a second,
    // also off-thread, step. An <img> is still the way when fetch or createImageBitmap are missing or fail
    const viaImg = () => new Promise((res) => {
      const im = new Image();
      im.onload = () => {
        if (!window.createImageBitmap) return res(im);
        const done = b => { if (b && k < 0.999) b._k = b.width / im.naturalWidth; res(b); };
        const o = k < 0.999 ? { resizeWidth: Math.max(1, Math.round(im.naturalWidth * k)), resizeHeight: Math.max(1, Math.round(im.naturalHeight * k)), resizeQuality: 'high' } : undefined;
        (o ? createImageBitmap(im, o) : createImageBitmap(im)).then(done, () => createImageBitmap(im).then(b => res(b), () => res(im)));
      };
      im.onerror = () => { console.warn('img fail', url); res(null); };
      im.decoding = 'async'; im.src = vurl(url);
    });
    const p = (window.createImageBitmap && window.fetch ? fetch(vurl(url), FETCH_OPT).then(r => { if (!r.ok) throw new Error(r.status); return r.blob(); }).then(bl => createImageBitmap(bl)).then(full => {
      if (k >= 0.999) return full;
      return createImageBitmap(full, { resizeWidth: Math.max(1, Math.round(full.width * k)), resizeHeight: Math.max(1, Math.round(full.height * k)), resizeQuality: 'high' })
        .then(b => { b._k = b.width / full.width; full.close(); return b; });
    }) : Promise.reject(new Error('no createImageBitmap'))).catch(() => viaImg());
    this.img[key] = { ready: p };
    return p;
  },
  // forget images that the next run does not need (decoded bitmaps are not discarded by the browser on its own):
  // one size of it (k), or all of them
  release(url, k) {
    const keys = k !== undefined ? [this.key(url, k)] : Object.keys(this.img).filter(n => n === url || n.startsWith(url + '#'));
    for (const n of keys) { const e = this.img[n]; if (!e) continue; delete this.img[n]; e.ready.then(b => { if (b && b._pxs && typeof PX !== 'undefined') PX.forget(b); if (b && b.close) b.close(); }); }   // (0.61: its PixiJS texture too)
  },
  async all(tasks, onProgress) {
    let done = 0; const n = tasks.length;
    return Promise.all(tasks.map(t => t.then(v => { done++; onProgress && onProgress(done / n); return v; })));
  },
};

// A sprite sheet: atlas image + anims {key:{fps,loop,f:[[x,y,w,h,ox,oy]], anc}}
class Sheet {
  constructor(img, meta) { this.img = img; this.meta = meta; this.zoom = meta.zoom || 1; this.anims = meta.anims || {}; }
  has(a) { return !!this.anims[a]; }
  frameAt(a, t, loop) {
    const an = this.anims[a]; if (!an) return null;
    const n = an.f.length; let i = Math.floor(t * an.fps);
    if (loop === undefined ? an.loop : loop) i %= n; else i = Math.min(i, n - 1);
    return an.f[i];
  }
  frameIndex(a, t, loop) {
    const an = this.anims[a]; if (!an) return 0;
    const n = an.f.length; let i = Math.floor(t * an.fps);
    return (loop === undefined ? an.loop : loop) ? i % n : Math.min(i, n - 1);
  }
  duration(a) { const an = this.anims[a]; return an ? an.f.length / an.fps : 0; }
  draw(ctx, f, x, y, scale, flip, img) {
    if (!f) return;
    const [fx, fy, fw, fh, ox, oy] = f; const s = scale / this.zoom;
    img = img || this.img; if (!img) return;
    const kk = img.k || img._k;
    if (kk && kk !== 1) {  // reduced-resolution flash overlay, or a sheet decoded smaller (performance mode)
      const k = kk;
      if (flip) { ctx.save(); ctx.translate(x, y); ctx.scale(-1, 1); ctx.drawImage(img, fx * k, fy * k, fw * k, fh * k, -ox * s, -oy * s, fw * s, fh * s); ctx.restore(); }
      else ctx.drawImage(img, fx * k, fy * k, fw * k, fh * k, x - ox * s, y - oy * s, fw * s, fh * s);
      return;
    }
    if (flip) { // mirrored around x without save/restore (cheaper when hundreds of monsters are drawn)
      ctx.scale(-1, 1); ctx.drawImage(img, fx, fy, fw, fh, -x - ox * s, y - oy * s, fw * s, fh * s); ctx.scale(-1, 1);
    } else ctx.drawImage(img, fx, fy, fw, fh, x - ox * s, y - oy * s, fw * s, fh * s);
  }
}

// Atlas with named frames {f:{name:[x,y,w,h,ox,oy,res,full]}}; an optional second (HD) atlas overrides the first
class Atlas {
  // icons3 (HD item pictures, v1.9) > icons2 > icons. icons3 has pages (0.31: icons3.webp, icons3_1.webp…; frame[8] = page)
  constructor(img, meta, img2, meta2, img3, meta3) { this.img = img; this.f = meta.f; this.img2 = img2; this.f2 = (meta2 && meta2.f) || {}; this.img3 = img3 ? [].concat(img3) : null; this.f3 = (img3 && meta3 && meta3.f) || {}; }
  get(n) { return this.f3[n] || this.f2[n] || this.f[n]; }
  src(n) { const f3 = this.f3[n]; return f3 ? this.img3[f3[8] || 0] : this.f2[n] && this.img2 ? this.img2 : this.img; }
  draw(ctx, n, x, y, scale = 1, center = true) {
    const f = this.get(n); const img = this.src(n); if (!f || !img) return;
    if (f[7]) { // full spell icon (background + frame + print): drawn at icon size
      const s = scale * 112 / Math.max(f[2], f[3]); ctx.drawImage(img, f[0], f[1], f[2], f[3], x - f[2] * s / 2, y - f[3] * s / 2, f[2] * s, f[3] * s); return;
    }
    return this._draw(ctx, img, f, x, y, scale, center);
  }
  // 0.91: a 400-px picture of its own (game/assets/ui/hd, tools/assets/build_iconhd091.py) for an item shown bigger than the
  // atlas' 180 px: loaded on the first ask (null until then: the atlas picture is drawn meanwhile)
  hd(n) {
    if (!SPR.iconsHD || !SPR.iconsHD.includes(n)) return null;
    const H = this._hd || (this._hd = {}); if (H[n] !== undefined) return H[n];
    H[n] = null; Assets.loadImg(`assets/ui/hd/${n}.webp`).then(im => { H[n] = im || null; }); return null;
  }
  // draw any icon fitted in a size x size box centred on (cx, cy)
  drawFit(ctx, n, cx, cy, size) {
    const tr = ctx.getTransform(); if (size * Math.hypot(tr.a, tr.b) > 90) { const im = this.hd(n); if (im) { const s = size / Math.max(im.width, im.height); ctx.drawImage(im, cx - im.width * s / 2, cy - im.height * s / 2, im.width * s, im.height * s); return; } }   // (0.91: shown at over half its atlas size — ground items, the gift reveal —: its 400-px picture, downscaled with mipmaps)
    const f = this.get(n); const img = this.src(n); if (!f || !img) return;
    if (n.startsWith('sp_') && !f[7]) {   // (0.91: composed at the size it shows — it was always 128 px, blurry in the big scenes like the fusions')
      const px = Math.min(512, Math.max(128, Math.ceil(size * Math.hypot(tr.a, tr.b) / 64) * 64));
      ctx.drawImage(this.canvas(n, px), cx - size / 2, cy - size / 2, size, size); return;
    }
    const s = size / Math.max(f[2], f[3]); ctx.drawImage(img, f[0], f[1], f[2], f[3], cx - f[2] * s / 2, cy - f[3] * s / 2, f[2] * s, f[3] * s);
  }
  _draw(ctx, img, f, x, y, scale, center) {
    const [fx, fy, fw, fh, ox, oy] = f; scale /= f[6] || 1;
    if (center) ctx.drawImage(img, fx, fy, fw, fh, x - fw * scale / 2, y - fh * scale / 2, fw * scale, fh * scale);
    else ctx.drawImage(img, fx, fy, fw, fh, x - ox * scale, y - oy * scale, fw * scale, fh * scale);
  }
  // returns a small canvas (cached) for DOM usage
  canvas(n, size) {
    this._c = this._c || {};
    const k = n + '@' + size; if (this._c[k]) return this._c[k];
    const f = this.get(n); const img = this.src(n); const c = document.createElement('canvas');
    c.width = c.height = size;
    const g = c.getContext('2d'); g.imageSmoothingQuality = 'high';
    if (f && f[7] && img) { const [fx, fy, fw, fh] = f; const s = Math.min(size / fw, size / fh); g.drawImage(img, fx, fy, fw, fh, (size - fw * s) / 2, (size - fh * s) / 2, fw * s, fh * s); this._c[k] = c; return c; }
    if (n.startsWith('sp_')) { spellBg(g, size / 2, size / 2, size * 0.48); if (f && img) { const [fx, fy, fw, fh] = f; const s = Math.min(size * 0.72 / fw, size * 0.72 / fh); g.drawImage(img, fx, fy, fw, fh, (size - fw * s) / 2, (size - fh * s) / 2, fw * s, fh * s); } this._c[k] = c; return c; }
    if (f && img) {
      const [fx, fy, fw, fh] = f; const s = Math.min(size / fw, size / fh) * 0.92;
      g.drawImage(img, fx, fy, fw, fh, (size - fw * s) / 2, (size - fh * s) / 2, fw * s, fh * s);
    }
    this._c[k] = c; return c;
  }
  dataURL(n, size) { const k = 'u' + n + '@' + size; this._u = this._u || {}; if (!this._u[k]) this._u[k] = this.canvas(n, size).toDataURL(); return this._u[k]; }
}

function spellBg(g, x, y, r) {
  const gr = g.createRadialGradient(x - r * 0.3, y - r * 0.3, r * 0.1, x, y, r);
  gr.addColorStop(0, '#8a6a44'); gr.addColorStop(1, '#3b2a17');
  g.fillStyle = gr; g.beginPath(); g.arc(x, y, r, 0, Math.PI * 2); g.fill();
  g.lineWidth = Math.max(1.5, r * 0.09); g.strokeStyle = '#e0b04a'; g.beginPath(); g.arc(x, y, r - g.lineWidth / 2, 0, Math.PI * 2); g.stroke();
}
// Recolor a character atlas: out = base + mask_k * color_k (per zone, mask stored in RGB)
function recolorAtlas(base, mask, colors) {
  const w = base.width, h = base.height;
  const c = document.createElement('canvas'); c.width = w; c.height = h;
  const g = c.getContext('2d', { willReadFrequently: true });
  g.drawImage(base, 0, 0);
  const bd = g.getImageData(0, 0, w, h);
  const mc = document.createElement('canvas'); mc.width = w; mc.height = h;
  const mg = mc.getContext('2d', { willReadFrequently: true });
  mg.drawImage(mask, 0, 0);
  const md = mg.getImageData(0, 0, w, h).data;
  const d = bd.data;
  const [c1, c2, c3] = colors;
  for (let i = 0; i < d.length; i += 4) {
    if (d[i + 3] === 0) continue;
    const m1 = md[i] / 255, m2 = md[i + 1] / 255, m3 = md[i + 2] / 255;
    if (m1 + m2 + m3 === 0) continue;
    d[i] = Math.min(255, d[i] + m1 * c1[0] + m2 * c2[0] + m3 * c3[0]);
    d[i + 1] = Math.min(255, d[i + 1] + m1 * c1[1] + m2 * c2[1] + m3 * c3[1]);
    d[i + 2] = Math.min(255, d[i + 2] + m1 * c1[2] + m2 * c2[2] + m3 * c3[2]);
  }
  g.putImageData(bd, 0, 0);
  // 0.44: copied into a plain canvas: the one above reads back pixels (CPU-backed); the copy is the GPU-friendly one
  // the game draws from every frame
  const o = document.createElement('canvas'); o.width = w; o.height = h; o.getContext('2d').drawImage(c, 0, 0);
  if (base._k) o._k = base._k;   // (a sheet decoded smaller: SD / HD)
  c.width = c.height = mc.width = mc.height = 0;   // (0.93: the two CPU-side work canvases freed now, not at the next garbage collection)
  return o;
}

// A white silhouette version of an image (for hit flashes)
function whiteVersion(img, k = 1) {
  const c = document.createElement('canvas'); c.width = Math.ceil(img.width * k); c.height = Math.ceil(img.height * k);
  const g = c.getContext('2d'); c.k = k * (img._k || 1);
  g.drawImage(img, 0, 0, c.width, c.height);
  g.globalCompositeOperation = 'source-in';
  g.fillStyle = '#fff'; g.fillRect(0, 0, c.width, c.height);
  return c;
}

// Character renderer (recolored atlas + accessories: 0 weapon, 1 hat, 2 cape, 3 pet)
class CharSprite {
  // (0.92: shield = the Dofus shields' slot 4, tools/shield_anc092 + build_shields092)
  constructor(sid, colors, hat, cape, pet, shield) {
    this.sid = sid; this.colors = colors; this.hat = hat; this.cape = cape; this.pet = pet || null; this.shield = shield || null; this.weapon = null; this.ready = false;
  }
  async load() {
    const urls = this._urls = [], use = (u, q) => { urls.push([u, q]); CharSprite.ref(u, q, 1); };   // (0.93: the decoded sheets it holds, CharSprite.ref — counted as soon as asked, so a sheet being loaded is never freed under it)
    const ld = async (k) => {
      const meta = SPR.chars[k]; if (!meta) return null;
      const q = lowK(), u = `assets/chars/${k}.webp`, mu = `assets/chars/${k}_m.webp`; use(u, q); if (!meta.nomask) use(mu, q);
      const [b, m] = await Promise.all([Assets.loadImg(u, q), meta.nomask ? Promise.resolve(null) : Assets.loadImg(mu, q)]);
      return { sheet: new Sheet(null, meta), base: b, mask: m, key: k, q };
    };
    const sk = this.sid + (this.hat && SPR.chars[this.sid + '_h_s'] ? '_h_s' : '_s');   // (0.63: the client's standing / cast / death poses, build_still063)
    // (0.63: an old sheet whose every animation that sheet has again — runs: the '_r' one — is not loaded: its data only)
    const S3 = SPR.chars[sk], meta0 = (k) => ({ sheet: new Sheet(null, SPR.chars[k]), base: null, mask: null, key: k, q: lowK() });
    const old = (k) => !SPR.chars[k] ? Promise.resolve(null) : S3 && Object.keys(SPR.chars[k].anims).every(a => S3.anims[a] || a.startsWith('run')) ? Promise.resolve(meta0(k)) : ld(k);
    const [n, hh, x, e, r, xh, eh, st] = await Promise.all([old(this.sid), old(this.sid + '_h'), ld(this.sid + '_x'), ld(this.sid + '_e'), ld(this.sid + (this.hat && SPR.chars[this.sid + '_h_r'] ? '_h_r' : '_r')), ld(this.sid + '_h_x'), ld(this.sid + '_h_e'), ld(sk)]);   // (the Sram's hat variant has its own)
    this.runfb = r && r.base ? r : null;   // 0.40 (test): runs towards / away from the camera (0.60: the runs of the `_r` sheets, tools/assets/build_move060.py)
    // 0.63: the standing poses, casts, blows without a weapon and the death rendered again from the up-to-date client
    // with its accessory anchors (build_still063)
    this.stillfb = st && st.base ? st : null;
    // front layers of these client sheets (what the client paints over the cape — the Enutrof's sack… 0.61 — and over the
    // hat — the bun / the ponytail seen from behind, a hand… 0.62), build_accfront061 [SLOT=1] [SHEET=_s]
    const layer = async (P, k) => {
      const fm = P && SPR.chars[P.key][k]; if (!fm) return null;
      const q = lowK(), u = `assets/chars/${fm.src}.webp`, mu = `assets/chars/${fm.src}_m.webp`; use(u, q); use(mu, q);
      const [fb, fk] = await Promise.all([Assets.loadImg(u, q), Assets.loadImg(mu, q)]);
      return fb ? { sheet: { img: null }, base: fb, mask: fk, key: fm.src, q, fa: 1 } : null;
    };
    await Promise.all([this.runfb, this.stillfb].filter(Boolean).map(async P => { [P.faP, P.fhP] = await Promise.all([layer(P, 'fa'), layer(P, 'fh')]); P.sheet._part = P; }));
    this.main = n; this.hatv = hh && (hh.base || hh.sheet.meta) ? hh : null; this.extra = x && x.base ? x : null; this.emo = e && e.base ? e : null;   // _e: extra emotes (build_emote23)
    // 0.61: the weapon blows and emotes with the short hair under a hat (the Iop 80: his spikes showed over it)
    this.extraH = xh && xh.base ? xh : null; this.emoH = eh && eh.base ? eh : null;
    if (this.disposed) { this._unref(); return this; }   // (0.93: let go while loading: the screen changed)
    this.sheetN = n.sheet; this.sheetH = this.hatv ? this.hatv.sheet : null;
    this.recolor(this.colors);
    this.acc = await loadAcc();
    await AccLib.ensure([this.hat, this.cape, this.pet, this.weapon, this.shield]);   // (0.44: only the accessory sheets it wears)
    if (this.disposed) { this.dispose(true); return this; }
    this.ready = true; CharSprite.live.add(this); this._seen = performance.now();
    return this;
  }
  // 0.93 (stress tests, tools/checks/stress.py: a reported crash after about ten character changes and a few Astrub runs): every
  // character drawn once — each class card clicked, each shop / armoury preview, each run — stayed in CharSprite.live with
  // its recoloured copies of every sheet (~50 Mpx a character), and its decoded sheets stayed in Assets.img: 30 changes =
  // 5 GB in the page's process, then the tab / the exe ran out of memory. A sprite nothing shows any more is let go now
  // (UI.own: the menus' previews when their screen goes or the class changes; Run.dispose: the run's character, summons
  // and merchant), its copies emptied at once; the sheets it shares with other sprites (Assets.img, by file and size) are
  // counted (CharSprite.refs) and freed only when no sprite uses them, the last few kept a while (CharSprite.IDLE) so that
  // going back to a class just seen does not decode it again
  dispose(late) {
    if (this.disposed && !late) return; this.disposed = true; this.ready = false; CharSprite.live.delete(this);
    const free = c => { if (c && c instanceof HTMLCanvasElement) { if (c._pxs && typeof PX !== 'undefined') PX.forget(c); c.width = 0; c.height = 0; } };
    for (const p of this.parts()) if (p && p.sheet && p.sheet.img && p.sheet.img !== p.base) { free(p.sheet.img); p.sheet.img = null; }
    for (const k in this._tint || {}) { const t = this._tint[k]; if (t) free(t.img); }
    if (this.whites) for (const w of this.whites.values()) free(w);
    this._tint = {}; this.whites = new Map();
    this._unref();
  }
  _unref() { const u = this._urls || []; this._urls = []; for (const [url, q] of u) CharSprite.ref(url, q, -1); }
  static ref(url, q, d) {
    const k = Assets.key(url, q), R = CharSprite.refs, n = (R.get(k) || 0) + d, I = CharSprite.idle;
    if (n > 0) { R.set(k, n); const i = I.findIndex(e => e.k === k); if (i >= 0) I.splice(i, 1); return; }
    R.delete(k); if (d > 0) return;
    I.push({ k, url, q });
    while (I.length > CharSprite.IDLE) { const e = I.shift(); if (!R.has(e.k)) Assets.release(e.url, e.q); }
  }
  // 0.44: the quality changed: the sheets again at the new size (the sprites drawn lately; the others are forgotten)
  async requality() {
    const q = lowK(), parts = this.parts().filter(p => p && p.base && p.q !== q);
    await Promise.all(parts.map(async p => {
      const meta = SPR.chars[p.key] || {}, u = `assets/chars/${p.key}.webp`, mu = `assets/chars/${p.key}_m.webp`;
      const old = this._urls.filter(([x, xq]) => (x === u || x === mu) && xq !== q), add = [[u, q], ...(meta.nomask ? [] : [[mu, q]])];   // (0.93: the new size counted, the old one let go)
      for (const [x, xq] of add) CharSprite.ref(x, xq, 1);
      const [b, m] = await Promise.all([Assets.loadImg(u, q), meta.nomask ? Promise.resolve(null) : Assets.loadImg(mu, q)]);
      if (b && !this.disposed) {
        this._urls = this._urls.filter(e => !old.includes(e)).concat(add); for (const [x, xq] of old) CharSprite.ref(x, xq, -1);
        p.base = b; p.mask = m; p.q = q;
      } else for (const [x, xq] of add) CharSprite.ref(x, xq, -1);
    }));
    if (!this.disposed) this.recolor(this.colors);
  }
  parts() { const out = [this.main, this.hatv, this.extra, this.emo, this.runfb, this.extraH, this.emoH, this.stillfb]; for (const P of [this.runfb, this.stillfb]) if (P) out.push(P.faP, P.fhP); return out; }
  get sheet() { return this.hat && this.sheetH && this.sheetH.img ? this.sheetH : this.sheetN; }
  // the sheet that holds an animation (weapon attacks and eating live in the extra sheet)
  sheetFor(anim) {
    const xp = this.hat && this.extraH ? this.extraH : this.extra, ep = this.hat && this.emoH ? this.emoH : this.emo;
    const m = this.sheet, x = xp && xp.sheet, rf = this.runfb && this.runfb.sheet;
    if (rf && anim.startsWith('run') && rf.has(anim)) return rf;   // (0.60: the runs at 60 fps of the up-to-date client, build_move060)
    // with a weapon equipped, attack animations come from the sheet that anchors the weapon in the hand (as in Dofus)
    if (this.weapon && x && x.has(anim) && x.anims[anim].anc) return x;
    const sf = this.stillfb && this.stillfb.sheet; if (sf && sf.img && sf.has(anim)) return sf;   // (0.63: from the client, build_still063)
    if (m && m.has(anim)) return m; if (x && x.has(anim)) return x;
    const e = ep && ep.sheet; if (e && e.has(anim)) return e;
    const r = this.runfb && this.runfb.sheet; if (r && r.has(anim)) return r; return null;
  }
  has(anim) { return !!this.sheetFor(anim); }
  duration(anim) { const sh = this.sheetFor(anim); return sh ? sh.duration(anim) : 0; }
  recolor(colors) {
    this.colors = colors; this.whites = new Map(); this._tint = {};
    for (const p of this.parts()) {
      if (!p || !p.base) continue;
      p.sheet.img = p.mask ? recolorAtlas(p.base, p.mask, colors) : p.base;
    }
  }
  getWhite(sh) { if (!sh.img) return null; if (!this.whites.has(sh)) this.whites.set(sh, whiteVersion(sh.img, 0.5)); return this.whites.get(sh); }
  // accessories that take the character's colours in the client (GAC.applyBody/Bottom/HeadColor): base + colour mask,
  // recoloured once per character and per colour set into a small atlas of their own
  tintAcc(sym) {
    const c = AccLib.compact(sym); if (!c || !c.mask) return null;
    this._tint = this._tint || {};
    const key = sym + '@' + c.q; if (this._tint[key] !== undefined) return this._tint[key];
    const cols = this.colors || [[196, 150, 96], [120, 84, 52], [150, 40, 40]];
    const img = recolorAtlas(c.img, c.mask, cols); if (c.img._k) img._k = c.img._k;
    return (this._tint[key] = { f: c.f, img, zoom: c.zoom, fps: c.fps });
  }
  accFrame(sym, dir, t) {
    if (!this.acc) return null;
    const cp = AccLib.compact(sym); if (!cp) return null;   // (0.60: its own picture, loading the first frames)
    const M = AccLib.meta(sym); if (M && M.none && M.none.includes(dir)) return null;   // (0.61: a view the client's accessory lacks shows nothing there, as in the client: accfix061)
    const ti = this.tintAcc(sym), A = ti ? [ti] : [cp];
    let wait = false;
    const look = (k) => { for (const a of A) { const fr = a.f[k]; if (fr) return [a, fr]; } return null; };
    let r = look(sym + '|' + dir) || (dir[0] === 'W' && /[FBS]$/.test(dir) ? look(sym + '|' + dir.slice(1)) : null) || look(sym + '|' + (dir.endsWith('L') ? (dir[0] === 'W' ? 'WL' : 'L') : (dir[0] === 'W' ? 'WR' : 'R'))) || look(sym + '|' + (dir.endsWith('L') ? 'L' : 'R'));
    if (!r || wait) return null;   // (0.44: a view whose sheet is not loaded yet shows from the next frames)
    let [a, fr] = r;
    if (Array.isArray(fr[0])) fr = fr[Math.floor(t * (fr.fps || a.fps || 12)) % fr.length];   // animated: pets walking, capes flapping while running
    return [a, fr];
  }
  // draw character frame with accessories. flip mirrors
  // 0.92 (the head / body showed through capes and hats): a see-through character (the faint copy drawn over
  // everything, the dodge trail, the blink, invisibility) is composed whole at full opacity in a canvas of its own, then
  // laid at that opacity once — the layers took it one by one, so the body under a cape showed through it
  draw(ctx, anim, t, x, y, scale, flip, opts = {}) {
    if (this.disposed) return;   // (0.93: let go, CharSprite.dispose)
    const a = opts.alpha;
    if (a !== undefined && a < 0.999 && !opts._whole && ctx.canvas && ctx.canvas.getContext && ctx.getTransform) {
      if (a <= 0.003) return;
      const m = ctx.getTransform();
      const x0 = x - 260 * scale, y0 = y - 330 * scale, x1 = x + 260 * scale, y1 = y + 80 * scale;   // (the character, its hat, cape and pet)
      const p0 = m.transformPoint({ x: x0, y: y0 }), p1 = m.transformPoint({ x: x1, y: y1 });
      const dx = Math.floor(Math.min(p0.x, p1.x)), dy = Math.floor(Math.min(p0.y, p1.y)), w = Math.ceil(Math.max(p0.x, p1.x)) - dx, h = Math.ceil(Math.max(p0.y, p1.y)) - dy;
      if (w > 0 && h > 0 && w * h < 9e6) {
        const c = CharSprite._grp || (CharSprite._grp = document.createElement('canvas'));
        if (c.width < w || c.height < h) { c.width = Math.max(c.width, w); c.height = Math.max(c.height, h); CharSprite._grpG = null; }
        const g = CharSprite._grpG || (CharSprite._grpG = c.getContext('2d'));
        g.setTransform(1, 0, 0, 1, 0, 0); g.globalAlpha = 1; g.globalCompositeOperation = 'source-over'; g.clearRect(0, 0, w, h);
        g.imageSmoothingEnabled = ctx.imageSmoothingEnabled; g.imageSmoothingQuality = ctx.imageSmoothingQuality;
        g.setTransform(m.a, m.b, m.c, m.d, m.e - dx, m.f - dy);
        this.draw(g, anim, t, x, y, scale, flip, Object.assign({}, opts, { alpha: undefined, _whole: true }));
        ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha *= a; ctx.drawImage(c, 0, 0, w, h, dx, dy, w, h); ctx.restore();
        return;
      }
    }
    if (anim === 'anim1L' && (this.sid === 1155 || this.sid === 1150)) anim = 'anim2L';   // 0.37: the Brigandin's shovel blow seen from behind floats away from his hand in the client clip: the other blow, shovel in hand
    const sh = this.sheetFor(anim); if (!sh || !sh.img) return;
    this._seen = performance.now();
    const an = sh.anims[anim], kk = sh.img._k || 1;   // (0.44: sheets decoded smaller in SD / HD)
    const idx = sh.frameIndex(anim, t, opts.loop);
    const f = an.f[idx]; let anc = an.anc ? an.anc[idx] : null;
    // 0.45: an emote frame without anchors (the Roublard's emote clip carries none) keeps the skins where they sit standing
    if ((!anc || !anc.length) && ((this.emo && sh === this.emo.sheet) || (this.emoH && sh === this.emoH.sheet))) { const st = this.sheetN.anims.staticR; anc = st && st.anc ? st.anc[0] : null; }
    const s = scale / sh.zoom;
    ctx.save(); ctx.translate(x, y); if (flip) ctx.scale(-1, 1);
    if (opts.alpha !== undefined) ctx.globalAlpha *= opts.alpha;
    const accs = [];
    // a sheet without pet anchors (the Brigandin, any new class): the pet stands where it does for the original classes
    let al = anc;
    if (this.pet && this.acc && !(anc && anc.some(a => a[0] === 3))) {
      const L = anim.endsWith('L'), run = anim.startsWith('run'), z = sh.zoom / 4.8;
      al = (anc || []).concat([[3, (run ? 'W' : '') + (L ? 'L' : 'R'), 0.24 * z, 0, 0, 0.24 * z, (run ? (L ? -53.76 : -95.52) : (L ? -62.88 : -54.96)) * z, 0, 1]]);
    }
    if (al && this.acc) for (const a of al) {
      const sym = a[0] === 1 ? this.hat : a[0] === 2 ? this.cape : a[0] === 0 ? this.weapon : a[0] === 3 ? this.pet : a[0] === 4 ? this.shield : null;
      if (!sym) continue;
      let dir = a[1];
      if (a[0] === 3 && !opts.petStill && opts.moving) dir = 'W' + (/[FBS]$/.test(dir) ? dir.slice(-1) : dir.endsWith('L') ? 'L' : 'R');   // (0.40: front / back walks too)
      const r = this.accFrame(sym, dir, opts.at !== undefined ? opts.at : t);
      if (r) accs.push([a, r[0], r[1]]);
    }
    // 0.29: as in Dofus, the pet follows behind: facing the camera (R views) it walks behind and a little higher,
    // seen from the back (L views) it is the one closer to the camera, down-right and in front
    const back = anim.endsWith('L'), zz = sh.zoom / 4.8, pdx = (back ? 16 : -30) * zz, pdy = (back ? 10 : -22) * zz;
    // 0.60: a weapon attack with its front layers (build_wfront060): body, weapon, then what the client paints over the
    // weapon at that frame (the near arm, or the whole body when the weapon is behind) — no more weapon over the head
    const ffr = an.ff ? an.ff[idx] : undefined, wsplit = !!(an.ff && this.weapon);
    // 0.61: a run with the capes' front layers (build_accfront061): body, cape, then what the client paints over the cape
    // 0.91 (videos of the official client, every direction): running towards the camera or sideways (runR, runF,
    // runS) the cape always stays behind the body; only seen from the back (runL, runB) does it come over it. The client's
    // timeline puts the cape holder in front of the body on some frames of the front runs (the wool cape over the belly):
    // the real client does not show that, so there the cape is drawn first, under the body
    const capeBehind = anim.startsWith('run') && !anim.endsWith('L') && anim !== 'runB';
    const P = sh._part, far = an.fa ? an.fa[idx] : undefined, csplit = !!(an.fa && this.cape && P && P.faP) && !capeBehind;
    // 0.62: the same for the hat (build_accfront061 SLOT=1): body, hat, then what the client paints over the hat
    // (0.92: standing, the hats went behind every head: the still sheets' hat front layer holds the whole head now
    // that no hair is hidden — it is only used in the runs, and the hat is always over the head)
    const fhr = an.fh ? an.fh[idx] : undefined, hsplit = !!(an.fh && this.hat && P && P.fhP) && anim.startsWith('run');
    const drawAcc = (front, weaponOnly, capeOnly, hatMode) => {
      for (const [a, A, fr] of accs) {
        if (wsplit && (a[0] === 0) !== !!weaponOnly) continue;
        if (csplit && (a[0] === 2) !== !!capeOnly) continue;
        if (hatMode && (a[0] === 1) !== (hatMode === 'hat')) continue;
        if ((a[0] === 4) !== (hatMode === 'shield')) continue;   // (0.92: the shield in its own last pass)
        const isFront = a[0] === 4 ? a[1] !== 'L' : a[0] === 3 ? back : a[0] === 0 ? (wsplit ? front : a[8] >= 0.15) : a[0] === 2 && capeBehind ? false : a[0] === 1 ? true : a[8] >= 0.5;   // (0.53: the weapon, held by the far hand (depth ~0.24), went behind the whole flat body: the wands / daggers vanished)
        if (!capeOnly && isFront !== front) continue;
        const k = 20 / A.zoom;
        // 0.34: a cape seen from behind while running ('RL'): the client's anchors turn it up to 60° from one frame to
        // the next while its own flapping frames run on their own clock, so it jumped from the shoulders to the feet.
        // It keeps the run's average orientation instead (still pinned to the shoulders)
        let m = a;
        // (0.61: only for the old 20-fps runs of the main sheets; the 60-fps runs of the '_r' sheets keep each frame's own
        // matrix, as the client draws it — averaged, the cape stuck out sideways instead of hanging behind: acccompare061)
        if (a[0] === 2 && a[1] === 'RL' && !P) { const M = sh._rlM || (sh._rlM = avgAnc(sh, anim, 'RL')); if (M) m = [a[0], a[1], M[0], M[1], M[2], M[3], a[6], a[7]]; }
        ctx.save();
        ctx.scale(s, s);
        ctx.transform(m[2] * k, m[3] * k, m[4] * k, m[5] * k, a[6] + (a[0] === 3 ? pdx : 0), a[7] + (a[0] === 3 ? pdy : 0));
        const ka = A.img._k || 1;
        ctx.drawImage(A.img, fr[0] * ka, fr[1] * ka, fr[2] * ka, fr[3] * ka, -fr[4], -fr[5], fr[2], fr[3]);
        ctx.restore();
      }
    };
    if (this.shield) drawAcc(false, false, false, 'shield');   // (0.92: seen from the back, the shield behind the whole character)
    drawAcc(false);
    ctx.drawImage(sh.img, f[0] * kk, f[1] * kk, f[2] * kk, f[3] * kk, -f[4] * s, -f[5] * s, f[2] * s, f[3] * s);
    if (opts.flash) {
      const w = this.getWhite(sh), kw = w && (w.k || 1); ctx.globalAlpha *= opts.flash;
      if (w) ctx.drawImage(w, f[0] * kw, f[1] * kw, f[2] * kw, f[3] * kw, -f[4] * s, -f[5] * s, f[2] * s, f[3] * s);
      ctx.globalAlpha /= opts.flash;
    }
    if (wsplit) {
      drawAcc(true, true);
      if (ffr) {
        ctx.drawImage(sh.img, ffr[0] * kk, ffr[1] * kk, ffr[2] * kk, ffr[3] * kk, -ffr[4] * s, -ffr[5] * s, ffr[2] * s, ffr[3] * s);
        if (opts.flash) { const w = this.getWhite(sh), kw = w && (w.k || 1); ctx.globalAlpha *= opts.flash; if (w) ctx.drawImage(w, ffr[0] * kw, ffr[1] * kw, ffr[2] * kw, ffr[3] * kw, -ffr[4] * s, -ffr[5] * s, ffr[2] * s, ffr[3] * s); ctx.globalAlpha /= opts.flash; }
      }
    }
    if (hsplit) {
      drawAcc(true, false, false, 'other'); drawAcc(true, false, false, 'hat');
      const im = P.fhP.sheet.img;
      if (fhr && im) {
        const kf = im._k || 1; ctx.drawImage(im, fhr[0] * kf, fhr[1] * kf, fhr[2] * kf, fhr[3] * kf, -fhr[4] * s, -fhr[5] * s, fhr[2] * s, fhr[3] * s);
        if (opts.flash) { const w = this.getWhite(P.fhP.sheet), kw = w && (w.k || 1); ctx.globalAlpha *= opts.flash; if (w) ctx.drawImage(w, fhr[0] * kw, fhr[1] * kw, fhr[2] * kw, fhr[3] * kw, -fhr[4] * s, -fhr[5] * s, fhr[2] * s, fhr[3] * s); ctx.globalAlpha /= opts.flash; }
      }
    } else drawAcc(true, false, false, csplit ? 'other' : undefined);   // (0.92: with a cape split, the hat comes last, below)
    // 0.92 (with a hat, capes went behind the body seen from the back): the hat's front layer (what the client
    // paints over the hat: most of the body in the back runs) is drawn first, then the cape and its own front layer —
    // the cape used to come before it and was covered
    if (csplit) {
      drawAcc(true, false, true);
      const im = P.faP.sheet.img;
      if (far && im) {
        const kf = im._k || 1; ctx.drawImage(im, far[0] * kf, far[1] * kf, far[2] * kf, far[3] * kf, -far[4] * s, -far[5] * s, far[2] * s, far[3] * s);
        if (opts.flash) { const w = this.getWhite(P.faP.sheet), kw = w && (w.k || 1); ctx.globalAlpha *= opts.flash; if (w) ctx.drawImage(w, far[0] * kw, far[1] * kw, far[2] * kw, far[3] * kw, -far[4] * s, -far[5] * s, far[2] * s, far[3] * s); ctx.globalAlpha /= opts.flash; }
      }
    }
    if (csplit && !hsplit) drawAcc(true, false, false, 'hat');   // (0.92: the hat over everything — the cape's front layer of the still poses holds the head)
    // 0.92 (the shield went behind the Féca's arm): its front view (R) is always in front, over the body and its front
    // layers (the client puts it behind the whole body on some blows: a flat sheet hid it under the arm); its back view (L,
    // the character seen from the back) is always behind the whole character, drawn first
    if (this.shield) drawAcc(true, false, false, 'shield');
    ctx.restore();
  }
}
// the mean of a cape anchor's linear part over an animation (see the 'RL' note in CharSprite.draw)
function avgAnc(sh, anim, dir) {
  const an = sh.anims[anim]; if (!an || !an.anc) return null; const m = [0, 0, 0, 0]; let n = 0;
  for (const al of an.anc) for (const a of al || []) if (a[0] === 2 && a[1] === dir) { for (let i = 0; i < 4; i++) m[i] += a[2 + i]; n++; }
  return n ? m.map(v => v / n) : null;
}
CharSprite.live = new Set();
CharSprite.refs = new Map(); CharSprite.idle = []; CharSprite.IDLE = 24;   // (0.93: about the sheets of two characters kept decoded once unused)
// v2.0: the HD accessories span several sheets (SPR.accSheets, 13 atlases of ~4096 px). 0.44: they are no longer all
// decoded up front (hundreds of MB of video memory): an entry per sheet, its image loaded the first time one of its
// frames is needed (what the character wears, a hat shown in the shop…), at the quality's size
let _accP = null, _accMask = null;
// 0.60: one small picture per accessory (assets/acc/i/<sym>.webp + <sym>_m.webp for the hats that take the character's
// colours), described in SPR.acci (tools/assets/build_acc060.py): a run loads only what it wears, nothing big is decoded or cut
// any more (the 14 sheets of 0.44 were decoded then cut at the start of a run: micro-freezes)
const AccLib = {
  cache: new Map(),
  meta(sym) { return sym && SPR.acci ? SPR.acci[sym] : null; },
  load(sym) {
    const M = this.meta(sym); if (!M) return Promise.resolve(null);
    const q = lowK(); let c = this.cache.get(sym);
    if (c && c.img && c.q === q) return Promise.resolve(c);
    if (c && c.p) return c.p;
    if (!c) {
      c = { k: 'i_' + sym, f: {}, img: null, mask: null, q: 0, p: null, zoom: M.zoom || 4.8, fps: 12 };
      for (const v in M.f) { const fr = M.f[v]; if (Array.isArray(fr[0])) { const a = fr.slice(); a.fps = (M.vf && M.vf[v]) || 12; c.f[sym + '|' + v] = a; } else c.f[sym + '|' + v] = fr; }
      this.cache.set(sym, c);
    }
    const url = `assets/acc/i/${sym}.webp`, murl = `assets/acc/i/${sym}_m.webp`;
    c.p = Promise.all([Assets.loadImg(url, q), M.m ? Assets.loadImg(murl, q) : Promise.resolve(null)]).then(([im, mk]) => {
      c.p = null; if (im) { if (c.img && c.q !== q) { Assets.release(url, c.q); if (M.m) Assets.release(murl, c.q); } c.img = im; c.mask = mk; c.q = q; c.tints = null; } return c;
    });
    return c.p;
  },
  // the accessory's picture once loaded (null the first frames: its loading starts)
  compact(sym) { if (!sym) return null; const c = this.cache.get(sym); if (c && c.img) { if (c.q !== lowK()) this.load(sym); return c; } this.load(sym); return null; },
  ensure(syms) { return Promise.all([...new Set(syms)].filter(Boolean).map(s => this.load(s))); },
  need(a) { return Promise.resolve(a); },
  requality() { return Promise.all([...this.cache.keys()].map(s => this.load(s))); },
  trim() {}, init() { return []; },
};
function loadAcc() { return Promise.resolve([]); }   // (0.60: nothing to load up front)

// 0.32 performance mode: monster and effect sheets decoded at half size (less video memory, faster drawing; the
// files are the same, Sheet.draw scales the frames by img._k)
function lowK() { return typeof Game !== 'undefined' && Game.Q ? Game.Q().k : 1; }   // (0.44: SD 0.5, HD 0.75, UHD 1)
// Monster sheets cache
// v2.0: several monsters can share one image (SPR.mobs[key].src = a pack of the monsters of a zone): the image and its
// white flash copy are shared and freed when the last monster using them is dropped
const MobSheets = {
  c: {}, p: {}, refs: {}, whites: {},
  url(key) { const m = SPR.mobs[key]; return m && m.src ? `assets/${m.src}` : `assets/mobs/${key}.webp`; },
  load(key) {
    if (this.c[key]) return Promise.resolve(this.c[key]);
    if (this.p[key]) return this.p[key];
    const meta = SPR.mobs[key]; if (!meta) { console.warn('no mob', key); return Promise.resolve(null); }
    const u = this.url(key); this.refs[u] = (this.refs[u] || 0) + 1;
    return (this.p[key] = Assets.loadImg(u, lowK()).then(img => {
      delete this.p[key];
      const sh = new Sheet(img, meta);
      if (img) { if (!this.whites[u]) this.whites[u] = whiteVersion(img, 0.5); sh.white = this.whites[u]; }
      return (this.c[key] = sh);
    }));
  },
  drop(key) {
    const sh = this.c[key]; delete this.c[key]; if (!sh) return;
    const u = this.url(key); this.refs[u] = (this.refs[u] || 1) - 1; sh.white = null;
    if (this.refs[u] <= 0) { delete this.refs[u]; delete this.whites[u]; Assets.release(u); }
  },
};
const FxSheets = {
  c: {},
  async load(id) {
    if (this.c[id] !== undefined) return this.c[id];
    const meta = SPR.fx[id];
    if (!meta) { this.c[id] = null; return null; }
    const img = await Assets.loadImg(`assets/fx/${id}.webp`, lowK());
    this.c[id] = img ? new Sheet(img, meta) : null;
    return this.c[id];
  },
  get(id) { return this.c[id] || null; },
};

