'use strict';
// ---------------------------------------------------------------- 0.99: the main menu's picture hung like a cloth
// The menu's picture (assets/banners/4.webp, the CSS body.menu-bg::before) drawn by WebGL on a grid pinned along its top
// edge, after canvasui.dev's Cloth: a damped wave equation on the grid's heights, pushed by a slow travelling wind with
// gusts (stronger toward the free bottom edge) and by the pointer moving over it; each node comes toward the viewer by
// its height (a perspective divide) and the folds are lit from the upper left. Kept subtle: folds of a few px, the light
// moving by a tenth; the wind keeps it moving a little without the pointer. On every screen that shows the picture
// (body.menu-bg, not Goultard's wasteland), one cloth kept from screen to screen (the picture never jumps: the CSS one is
// scaled by the same bleed); without WebGL, with reduced motion or the lowest effects the CSS picture stays.
// MenuCloth.watch (once, at load) starts / stops it with body.menu-bg.
const MenuCloth = {
  NX: 48, NY: 28, AMP: 9, FOCAL: 1400, BLEED: 0.03, SRC: 'assets/banners/4.webp', IW: 2968, IH: 1490,
  on: false,
  wanted() { const c = document.body.classList; return c.contains('menu-bg') && !c.contains('endgame'); },
  // the body's classes change on every screen (UI.clear takes menu-bg off, the next screen puts it back in the same task):
  // the observer sees the final state, so the cloth goes on between two menu screens
  watch() { new MutationObserver(() => { if (this.wanted()) this.start(); else this.stop(); }).observe(document.body, { attributes: true, attributeFilter: ['class'] }); if (this.wanted()) this.start(); },
  start() {
    if (this.on || !this.wanted()) return;
    if ((window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches) || (typeof Game !== 'undefined' && Game.minFx)) return;
    const cv = document.createElement('canvas'); cv.className = 'menu-cloth';
    const gl = cv.getContext('webgl', { alpha: false, antialias: true, premultipliedAlpha: false, powerPreference: 'low-power' }); if (!gl) return;
    const sh = (type, src) => { const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s); return s; };
    const pr = gl.createProgram();
    gl.attachShader(pr, sh(gl.VERTEX_SHADER, 'attribute vec2 p; attribute vec2 uv; attribute float l; uniform vec2 res; varying vec2 vu; varying float vl;' +
      'void main() { vu = uv; vl = l; gl_Position = vec4(p.x / res.x * 2.0 - 1.0, 1.0 - p.y / res.y * 2.0, 0.0, 1.0); }'));
    gl.attachShader(pr, sh(gl.FRAGMENT_SHADER, 'precision mediump float; uniform sampler2D tex; varying vec2 vu; varying float vl;' +
      'void main() { vec3 c = texture2D(tex, vu).rgb; float g = dot(c, vec3(0.2126, 0.7152, 0.0722)); c = mix(vec3(g), c, 1.1) * 0.45 * vl; gl_FragColor = vec4(c, 1.0); }'));   // (the CSS picture's brightness(0.45) saturate(1.1))
    gl.linkProgram(pr); if (!gl.getProgramParameter(pr, gl.LINK_STATUS)) return;
    const NX = this.NX, NY = this.NY, NV = (NX + 1) * (NY + 1);
    const idx = new Uint16Array(NX * NY * 6); let k = 0;
    for (let j = 0; j < NY; j++) for (let i = 0; i < NX; i++) { const a = j * (NX + 1) + i, b = a + 1, c = a + NX + 1, d = c + 1; idx.set([a, b, c, b, d, c], k); k += 6; }
    const S = this.s = { cv, gl, pr, NV, dyn: new Float32Array(NV * 3), uvs: new Float32Array(NV * 2), h: new Float32Array(NV), hp: new Float32Array(NV), t: 0, last: 0, acc: 0,
      px: -1, py: -1, pvx: 0, pvy: 0, ready: false, raf: 0, W: 0, H: 0, rect: null };
    S.vb = gl.createBuffer(); S.ub = gl.createBuffer(); S.ib = gl.createBuffer();
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, S.ib); gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, idx, gl.STATIC_DRAW);
    S.nIdx = idx.length;
    gl.useProgram(pr); S.uRes = gl.getUniformLocation(pr, 'res'); S.aP = gl.getAttribLocation(pr, 'p'); S.aUv = gl.getAttribLocation(pr, 'uv'); S.aL = gl.getAttribLocation(pr, 'l');
    const tex = S.tex = gl.createTexture(), im = new Image();
    im.onload = () => {
      if (this.s !== S) return;
      gl.bindTexture(gl.TEXTURE_2D, tex); gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGB, gl.RGB, gl.UNSIGNED_BYTE, im);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);   // (any size: no mipmaps)
      S.ready = true;
    };
    im.src = this.SRC;
    S.onMove = e => { const x = e.clientX, y = e.clientY; if (S.px >= 0) { S.pvx += x - S.px; S.pvy += y - S.py; } S.px = x; S.py = y; };
    S.onLeave = () => { S.px = S.py = -1; };
    S.onResize = () => this.resize();
    addEventListener('pointermove', S.onMove, { passive: true }); document.addEventListener('pointerleave', S.onLeave); addEventListener('resize', S.onResize);
    document.body.prepend(cv); this.on = true; this.resize();
    const loop = now => { if (this.s !== S) return; S.raf = requestAnimationFrame(loop); if (!this.wanted()) { this.stop(); return; } this.frame(now); };
    S.raf = requestAnimationFrame(loop);
  },
  resize() {
    const S = this.s; if (!S) return;
    const W = innerWidth, H = innerHeight, dpr = Math.min(2, window.devicePixelRatio || 1);
    S.cv.width = Math.round(W * dpr); S.cv.height = Math.round(H * dpr); S.W = W; S.H = H; S.gl.viewport(0, 0, S.cv.width, S.cv.height);
    // the picture as background-size: cover, centred, a little larger (BLEED) so a fold never shows the edge
    const ia = this.IW / this.IH, sw = W / H > ia ? W : H * ia, sh = W / H > ia ? W / ia : H, b = 1 + this.BLEED * 2;
    S.rect = { x: (W - sw * b) / 2, y: (H - sh * b) / 2, w: sw * b, h: sh * b };
    const NX = this.NX, NY = this.NY;
    for (let j = 0; j <= NY; j++) for (let i = 0; i <= NX; i++) { const v = j * (NX + 1) + i; S.uvs[v * 2] = i / NX; S.uvs[v * 2 + 1] = j / NY; }
    S.gl.bindBuffer(S.gl.ARRAY_BUFFER, S.ub); S.gl.bufferData(S.gl.ARRAY_BUFFER, S.uvs, S.gl.STATIC_DRAW);
  },
  // the cloth: heights on the grid (in cell units), a fixed step of 1/60 s; the top row pinned
  step() {
    const S = this.s, NX = this.NX, NY = this.NY, W1 = NX + 1, h = S.h, hp = S.hp, t = (S.t += 1 / 60);
    const gust = 0.55 + 0.45 * Math.sin(t * 0.37) * Math.sin(t * 0.23 + 1.3), wind = 0.009 * gust;   // (0.99: 0.0035 before: folds under 5 px without the pointer, hardly seen)
    // the pointer: a soft push where it moves, by its speed (canvasui's brush), spread over a few cells
    let bx = -1, by = -1, bk = 0;
    if (S.px >= 0 && S.rect) { const sp = Math.min(40, Math.hypot(S.pvx, S.pvy)); bk = sp * 0.0016; bx = (S.px - S.rect.x) / S.rect.w * NX; by = (S.py - S.rect.y) / S.rect.h * NY; }
    S.pvx *= 0.6; S.pvy *= 0.6;
    for (let j = 1; j <= NY; j++) {
      const hang = Math.pow(j / NY, 1.3);
      for (let i = 0; i <= NX; i++) {
        const v = j * W1 + i, c = h[v];
        const l = i > 0 ? h[v - 1] : c, r = i < NX ? h[v + 1] : c, u = h[v - W1], d = j < NY ? h[v + W1] : c;
        let a = 0.22 * (l + r + u + d - 4 * c) - 0.035 * (c - hp[v]);   // (the wave equation, damped)
        a += wind * hang * Math.sin(i * 0.31 + j * 0.17 - t * 1.7) + wind * 0.6 * hang * Math.sin(i * 0.13 - j * 0.29 - t * 1.1 + 2);
        if (bk) { const dx = i - bx, dy = j - by, q = dx * dx + dy * dy; if (q < 16) a += bk * Math.exp(-q / 4); }
        hp[v] = c + (c - hp[v]) + a;   // (Verlet: the next height, kept in the previous one's place, swapped below)
      }
    }
    for (let v = W1; v < S.NV; v++) { const n = hp[v]; hp[v] = h[v]; h[v] = n > 2.5 ? 2.5 : n < -2.5 ? -2.5 : n; }
  },
  frame(now) {
    const S = this.s, gl = S.gl; if (!S.ready) return;
    const dt = S.last ? Math.min(0.1, (now - S.last) / 1000) : 1 / 60; S.last = now; S.acc += dt;
    let n = 0; while (S.acc >= 1 / 60 && n < 4) { this.step(); S.acc -= 1 / 60; n++; } if (n === 4) S.acc = 0;
    const NX = this.NX, NY = this.NY, W1 = NX + 1, R = S.rect, cx = S.W / 2, cy = S.H / 2, F = this.FOCAL, A = this.AMP, h = S.h, D = S.dyn;
    const cw = R.w / NX, ch = R.h / NY;
    for (let j = 0; j <= NY; j++) for (let i = 0; i <= NX; i++) {
      const v = j * W1 + i, z = A * Math.tanh(h[v]), x = R.x + i * cw, y = R.y + j * ch, k = F / (F - z);
      const zl = A * Math.tanh(h[i > 0 ? v - 1 : v]), zr = A * Math.tanh(h[i < NX ? v + 1 : v]), zu = A * Math.tanh(h[j > 0 ? v - W1 : v]), zd = A * Math.tanh(h[j < NY ? v + W1 : v]);
      const gx = (zr - zl) / (2 * cw), gy = (zd - zu) / (2 * ch);   // (the slope: the light from the upper left, a tenth or so)
      D[v * 3] = cx + (x - cx) * k; D[v * 3 + 1] = cy + (y - cy) * k; D[v * 3 + 2] = 1 + (gx * 0.6 + gy * 0.8) * 2.2 + z * 0.006;
    }
    gl.useProgram(S.pr); gl.uniform2f(S.uRes, S.W, S.H);
    gl.bindBuffer(gl.ARRAY_BUFFER, S.vb); gl.bufferData(gl.ARRAY_BUFFER, D, gl.DYNAMIC_DRAW);
    gl.enableVertexAttribArray(S.aP); gl.vertexAttribPointer(S.aP, 2, gl.FLOAT, false, 12, 0);
    gl.enableVertexAttribArray(S.aL); gl.vertexAttribPointer(S.aL, 1, gl.FLOAT, false, 12, 8);
    gl.bindBuffer(gl.ARRAY_BUFFER, S.ub); gl.enableVertexAttribArray(S.aUv); gl.vertexAttribPointer(S.aUv, 2, gl.FLOAT, false, 0, 0);
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, S.ib); gl.drawElements(gl.TRIANGLES, S.nIdx, gl.UNSIGNED_SHORT, 0);
    if (!document.body.classList.contains('cloth-on')) document.body.classList.add('cloth-on');   // (the CSS picture hidden once the cloth is drawn)
  },
  stop() {
    const S = this.s; if (!S) return; this.s = null; this.on = false;
    cancelAnimationFrame(S.raf); removeEventListener('pointermove', S.onMove); document.removeEventListener('pointerleave', S.onLeave); removeEventListener('resize', S.onResize);
    document.body.classList.remove('cloth-on'); S.cv.remove();
    const gl = S.gl; gl.deleteTexture(S.tex); gl.deleteBuffer(S.vb); gl.deleteBuffer(S.ub); gl.deleteBuffer(S.ib); gl.deleteProgram(S.pr);   // (its GPU memory freed now: a run's PixiJS comes next; no loseContext, which PixiJS's own context listener could mistake)
  },
};
MenuCloth.watch();
