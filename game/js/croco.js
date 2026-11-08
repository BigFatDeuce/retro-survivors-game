'use strict';
// ---------------------------------------------------------------- 0.99: the Crocoburio's own effects (Crocodailles, fish)
// Marais Régénérant (a Cawotte zone with `swamp`, gspells.js drawCawottes): murky water instead of the Cawotte's disc —
// ripples spreading, lily pads bobbing, reeds on the rim, bubbles popping, now and then a fish jumping out and a
// Crocodaille's eyes surfacing, little fish circling instead of the cawottes. Furie Crocoburiale (pulse `croc: 'bite'`):
// water thrown out round him; Coup de Queue (`croc: 'tail'`): a whip of green smoke (the client's
// gas puff, fx_puff) swept round him, water thrown out (Furie's jaws are its own client effect, fx 2043: no drawn ones). Their pictures are drawn once into cached canvases (RCache) and laid as quads: nothing PixiJS cannot draw.
// Run.crocs: the pulses' effects (drawCroco, render.js, top layer); spells.js pulse calls crocPulse.
const CROC_DUR = { bite: 0.42, tail: 0.55 };
function crocPic(key, w, h, draw) {
  let c = RCache.m.get('croc_' + key); if (c) return c;
  c = document.createElement('canvas'); c.width = w; c.height = h; draw(c.getContext('2d'), w, h); return RCache.put('croc_' + key, c);
}
const CROC_PIC = {
  fish: () => crocPic('fish', 128, 64, (g) => {   // a little silver-blue fish, facing right
    g.fillStyle = '#4f7f9c'; g.beginPath(); g.moveTo(26, 32); g.lineTo(4, 12); g.lineTo(10, 32); g.lineTo(4, 52); g.closePath(); g.fill();   // its tail
    const gr = g.createLinearGradient(0, 14, 0, 50); gr.addColorStop(0, '#3e6f8e'); gr.addColorStop(0.55, '#9cc8dc'); gr.addColorStop(1, '#e8f4f8');
    g.fillStyle = gr; g.beginPath(); g.ellipse(66, 32, 44, 17, 0, 0, TAU); g.fill();
    g.strokeStyle = 'rgba(30,60,80,0.7)'; g.lineWidth = 2.5; g.stroke();
    g.fillStyle = '#3e6f8e'; g.beginPath(); g.moveTo(54, 16); g.lineTo(70, 4); g.lineTo(80, 17); g.closePath(); g.fill();   // its fin
    g.fillStyle = '#fff'; g.beginPath(); g.arc(94, 27, 5, 0, TAU); g.fill(); g.fillStyle = '#1a2a33'; g.beginPath(); g.arc(95.5, 27, 2.6, 0, TAU); g.fill();
  }),
  pad: (flower) => crocPic('pad' + (flower ? 'f' : ''), 128, 96, (g) => {   // a lily pad seen from above (the ground's 0.62), its notch, its veins
    g.translate(64, 48); g.scale(1, 0.62);
    g.fillStyle = '#4f8a2c'; g.beginPath(); g.moveTo(0, 0); g.arc(0, 0, 56, 0.35, TAU - 0.05); g.closePath(); g.fill();
    g.strokeStyle = '#2f5a18'; g.lineWidth = 4; g.stroke();
    g.strokeStyle = 'rgba(150,200,90,0.6)'; g.lineWidth = 2.5; for (let i = 0; i < 7; i++) { const a = 0.6 + i * 0.8; g.beginPath(); g.moveTo(0, 0); g.lineTo(Math.cos(a) * 48, Math.sin(a) * 48); g.stroke(); }
    if (flower) { g.setTransform(1, 0, 0, 1, 64, 40); for (let i = 0; i < 7; i++) { g.save(); g.rotate(i * TAU / 7); g.fillStyle = i % 2 ? '#f6b6d2' : '#fbd3e4'; g.beginPath(); g.ellipse(0, -11, 6, 13, 0, 0, TAU); g.fill(); g.restore(); } g.fillStyle = '#ffd84a'; g.beginPath(); g.arc(0, 0, 6, 0, TAU); g.fill(); }
  }),
  reeds: () => crocPic('reeds', 96, 128, (g) => {   // a tuft of reeds with two cattails
    g.lineCap = 'round';
    for (const [x, h, bend, col] of [[30, 92, -14, '#5f8a2a'], [44, 118, 6, '#4c7a22'], [56, 104, 18, '#6c9a32'], [68, 80, 26, '#557f26'], [38, 70, -24, '#6c9a32']]) {
      g.strokeStyle = col; g.lineWidth = 5; g.beginPath(); g.moveTo(x, 126); g.quadraticCurveTo(x + bend * 0.2, 126 - h * 0.6, x + bend, 126 - h); g.stroke();
    }
    g.fillStyle = '#6a4424'; for (const [x, y] of [[50, 16], [74, 40]]) { g.beginPath(); g.ellipse(x, y, 5.5, 14, 0.25, 0, TAU); g.fill(); }
  }),
  eyes: () => crocPic('eyes', 128, 64, (g) => {   // a Crocodaille's eyes and snout tip just over the water
    g.fillStyle = '#5d7a2e'; for (const x of [36, 92]) { g.beginPath(); g.ellipse(x, 36, 22, 15, 0, Math.PI, TAU); g.fill(); }
    for (const x of [36, 92]) { g.fillStyle = '#f2d23a'; g.beginPath(); g.ellipse(x, 32, 11, 8, 0, 0, TAU); g.fill(); g.fillStyle = '#1b1405'; g.beginPath(); g.ellipse(x, 32, 2.6, 7, 0, 0, TAU); g.fill(); }
    g.fillStyle = '#4c6624'; g.beginPath(); g.ellipse(64, 54, 12, 5, 0, 0, TAU); g.fill();
  }),
};
Object.assign(Run.prototype, {
  crocPulse(kind, x, y, r) {
    (this.crocs || (this.crocs = [])).push({ kind, x, y, r, t0: this.time, seed: Math.random() * 10 });
    const n = kind === 'tail' ? 16 : 10;   // (water thrown out: a few drops, the particles' own pool)
    for (let i = 0; i < n; i++) { const a = rand(TAU), v = rand(140, 300); this.particles.push({ x: x + Math.cos(a) * r * 0.5, y: y + Math.sin(a) * r * 0.3, vx: Math.cos(a) * v, vy: Math.sin(a) * v * 0.6 - 140, g: 700, t: 0, life: rand(0.35, 0.6), s: rand(2.5, 4.5), round: 1, c: pick(['#bfe6f2', '#7fc0d8', '#e8fbff']) }); }
  },
  drawCroco(ctx, t) {
    const L = this.crocs; if (!L || !L.length) return;
    for (let i = L.length - 1; i >= 0; i--) {
      const c = L[i], e = (t - c.t0) / CROC_DUR[c.kind]; if (e >= 1 || e < 0) { if (e >= 1) L.splice(i, 1); continue; }
      ctx.save(); ctx.translate(c.x, c.y - 20);
      if (c.kind === 'bite') {   // (0.99: no drawn jaws: Furie's own client effect, fx 2043, plays; only its water thrown out)
      } else {   // 0.99: a whip of green smoke swept once round him: the client's gas puff (fx_puff, the Pwout's), green, a trail of puffs fading behind its head
        const ease = 1 - Math.pow(1 - e, 2), a0 = c.seed + ease * 6.6, rr = c.r * 0.78, al = e < 0.7 ? 1 : 1 - (e - 0.7) / 0.3, pf = orangePuff('#3f8f2a'); if (!pf) { ctx.restore(); continue; }
        for (let k = 11; k >= 0; k--) {
          const a = a0 - k * 0.13, q = 1 - k / 12, x = Math.cos(a) * rr * (0.55 + 0.45 * q), y = 20 + Math.sin(a) * rr * 0.62 * (0.55 + 0.45 * q), sz = c.r * (0.22 + 0.3 * q) * (1 + 0.15 * Math.sin(k * 1.7 + e * 9));
          ctx.globalAlpha = al * (0.2 + 0.5 * q); ctx.save(); ctx.translate(x, y); ctx.rotate(a * 2 + k); ctx.drawImage(pf, -sz / 2, -sz / 2, sz, sz); ctx.restore();
        }
        ctx.globalAlpha = al * 0.3; ctx.drawImage(RCache.glow('rgba(110,200,80,0.6)'), Math.cos(a0) * rr - c.r * 0.3, 20 + Math.sin(a0) * rr * 0.62 - c.r * 0.3, c.r * 0.6, c.r * 0.6);   // its head glows
      }
      ctx.restore();
    }
    ctx.globalAlpha = 1;
  },
  // the swamp (layer 'ground' under everyone, 'top' over them: the jumping fish, the eyes); k: the zone's fade in / out
  drawSwamp(ctx, c, t, layer, k) {
    const r = c.r, age = t - c.t0, seed = c.seed || (c.seed = Math.random() * 100), hash = i => { const v = Math.sin(seed * 12.9898 + i * 78.233) * 43758.5453; return v - Math.floor(v); };
    ctx.save(); ctx.translate(c.x, c.y);
    if (layer !== 'top') {
      const disc = (s) => { ctx.beginPath(); ctx.ellipse(0, 0, r * s, r * s * 0.62, 0, 0, TAU); };
      // the murky water as soft areas (the zones' own soft disc, drawArea): no hard edge, it melts into the ground (0.99)
      drawArea(ctx, 0, 0, r * 1.05, '#2f6a44', k, true); drawArea(ctx, 0, 0, r * 0.95, '#2a5e40', k, true); drawArea(ctx, 0, 0, r * 0.7, '#1b4430', 0.8 * k, true);
      ctx.globalAlpha = 0.14 * k; ctx.drawImage(RCache.glow('rgba(140,220,200,0.6)'), -r * 0.55, -r * 0.5, r * 0.9, r * 0.5);   // the light on the water
      for (let i = 0; i < 3; i++) { const ph = (t * 0.45 + i / 3) % 1; ctx.globalAlpha = 0.22 * (1 - ph) * Math.min(1, ph * 4) * k; ctx.strokeStyle = '#cfeee0'; ctx.lineWidth = 1.4; disc(0.15 + 0.7 * ph); ctx.stroke(); }   // ripples from the middle, fading before the edge
      const R = CROC_PIC.reeds();
      for (let i = 0; i < 7; i++) { const a = Math.PI + 0.15 + i / 6 * (Math.PI - 0.3), s = r / 190 * (0.5 + 0.3 * hash(i + 40)), w = 56 * s, h = 76 * s; ctx.globalAlpha = 0.8 * k; ctx.save(); ctx.translate(Math.cos(a) * r * 0.88, Math.sin(a) * r * 0.55); ctx.rotate(Math.sin(t * 1.3 + i) * 0.04); ctx.drawImage(R, -w / 2, -h, w, h); ctx.restore(); }   // (the back half of the rim)
      for (let i = 0; i < 5; i++) {   // lily pads, bobbing, one in flower
        const P = CROC_PIC.pad(i === 2), a = hash(i) * TAU, d = r * (0.3 + 0.5 * hash(i + 10)), s = r / 190 * (0.55 + 0.3 * hash(i + 20)), w = 64 * s, h = 48 * s;
        ctx.globalAlpha = 0.85 * k; ctx.save(); ctx.translate(Math.cos(a) * d + Math.sin(t * 0.7 + i) * 2, Math.sin(a) * d * 0.62 + Math.cos(t * 0.9 + i) * 1.2); ctx.rotate(hash(i + 30) * TAU * 0.15 + Math.sin(t * 0.5 + i) * 0.06); ctx.drawImage(P, -w / 2, -h / 2, w, h); ctx.restore();
      }
      ctx.strokeStyle = '#e6fff4'; ctx.lineWidth = 1.4;
      for (let i = 0; i < 6; i++) {   // bubbles rising and popping, a small ring where they pop
        const ph = (t * (0.6 + hash(i + 50) * 0.4) + hash(i + 60)) % 1, a = hash(i + 70) * TAU + Math.floor(t * 0.6 + hash(i + 60)) * 2.1, d = r * 0.75 * Math.sqrt(hash(i + 80)), bx = Math.cos(a) * d, by = Math.sin(a) * d * 0.62;
        if (ph < 0.8) { ctx.globalAlpha = 0.7 * k; ctx.beginPath(); ctx.arc(bx, by - ph * 6, 2 + ph * 3, 0, TAU); ctx.stroke(); }
        else { const q = (ph - 0.8) / 0.2; ctx.globalAlpha = 0.5 * (1 - q) * k; ctx.beginPath(); ctx.ellipse(bx, by, 4 + q * 12, (4 + q * 12) * 0.62, 0, 0, TAU); ctx.stroke(); }
      }
    } else {
      const F = CROC_PIC.fish(), fs = r / 190;
      for (let i = 0; i < 5; i++) {   // little fish circling under the surface (the Cawotte's cawottes)
        const an = t * 0.9 + i * TAU / 5, x = Math.cos(an) * r * 0.62, y = Math.sin(an) * r * 0.38, w = 34 * fs, h = 17 * fs;
        ctx.globalAlpha = 0.55 * k; ctx.save(); ctx.translate(x, y); ctx.rotate(an + Math.PI / 2); ctx.drawImage(F, -w / 2, -h / 2, w, h); ctx.restore();
      }
      { const cyc = 1.9, n = Math.floor((age + seed) / cyc), e = ((age + seed) % cyc) / 1.1;   // one fish jumps out every 1.9 s, somewhere new
        if (e < 1) { const a = hash(n + 90) * TAU, d = r * 0.5 * hash(n + 95), x0 = Math.cos(a) * d, y0 = Math.sin(a) * d * 0.62, dir = hash(n + 99) < 0.5 ? -1 : 1, x = x0 + dir * (e - 0.5) * 70 * fs, y = y0 - Math.sin(e * Math.PI) * 60 * fs, w = 44 * fs, h = 22 * fs;
          ctx.globalAlpha = k; ctx.save(); ctx.translate(x, y); ctx.scale(dir, 1); ctx.rotate((e - 0.5) * 2.2); ctx.drawImage(F, -w / 2, -h / 2, w, h); ctx.restore();
          for (const q of [e * 2, (e - 0.55) * 2.2]) if (q > 0 && q < 1) { ctx.globalAlpha = 0.6 * (1 - q) * k; ctx.strokeStyle = '#e6fff4'; ctx.lineWidth = 1.6; const xx = q === e * 2 ? x0 - dir * 35 * fs : x0 + dir * 35 * fs; ctx.beginPath(); ctx.ellipse(xx, y0, 6 + q * 18, (6 + q * 18) * 0.62, 0, 0, TAU); ctx.stroke(); } } }
      { const cyc = 5.3, e = ((age + seed * 0.7) % cyc) / 2.4;   // a Crocodaille's eyes surface, look about, sink
        if (e < 1) { const n = Math.floor((age + seed * 0.7) / cyc), a = hash(n + 120) * TAU, d = r * 0.45, E = CROC_PIC.eyes(), w = 46 * fs, h = 23 * fs, up = Math.min(1, e * 5, (1 - e) * 5);
          ctx.globalAlpha = 0.9 * up * k; ctx.drawImage(E, Math.cos(a) * d - w / 2 + Math.sin(age * 2) * 2, Math.sin(a) * d * 0.62 - h * up, w, h * up); } }
    }
    ctx.restore(); ctx.globalAlpha = 1;
  },
});
