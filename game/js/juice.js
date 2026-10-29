'use strict';
// 0.60 game feel (the "juice"): short freezes on big hits (hit-stop), slow motion when a boss falls, screen flashes,
// a pickup sound that climbs when ambers are picked in a row, the low-life vignette and heartbeat, counters that bump.
// Run.prototype methods (same pattern as extras.js), called from hook points in game.js / main.js / render.js.
// Everything is cheap: no per-monster work, one cached full-screen picture at most.
// 0.62: the combo's steps and their colours (juice.js, the HUD in render.js)
const COMBO_MS = [25, 50, 100, 200, 400, 800], COMBO_COLS = ['#ffe27a', '#ffb02e', '#ff7a3a', '#ff4d8a', '#c050ff', '#5ad1ff'];
Object.assign(Run.prototype, {
  // the game stops for a few milliseconds (the run is drawn, not updated): the impact reads as heavy
  hitStop(ms) { const S = Store.data.settings; if (S.shake === false) ms *= 0.5; const t = performance.now() + ms; if (!(this.hitStopUntil > t)) this.hitStopUntil = t; },
  frozenByHit() { return this.hitStopUntil > performance.now(); },
  // the run's clock runs at k for a moment (real seconds)
  slowMo(sec, k) { if (this.critFx && performance.now() < this.critFx.t0 + 2000) return; this.slowUntil = performance.now() + sec * 1000; this.slowK = k; },   // (a critical summon's slow motion is not cut short)
  // 0.98: a critical summon (the Chaferfu Lancier, the Arakne majeure): the run at 1 % for 2 s with confetti and a strong
  // aberration, the camera closing in on it (x1.75 in 1 s, held 2 s, back in 1 s: 4 s, real time); one at a time — a
  // second one meanwhile has its banner, not a second show
  critSeq(A) {
    const now = performance.now(); if (this.critFx && now - this.critFx.t0 < 4000) return;
    this.critFx = { t0: now, A, x: A.x, y: A.y - 40, conf: makeConfetti() }; this.slowUntil = now + 2000; this.slowK = 0.01;   // (set here: slowMo() now waits for it)
  },
  critK() {
    const F = this.critFx; if (!F) return 0; const e = (performance.now() - F.t0) / 1000;
    if (e >= 4) { this.critFx = null; return 0; }
    const s = x => x * x * (3 - 2 * x); return e < 1 ? s(e) : e < 3 ? 1 : s(4 - e);
  },
  // 0.98: the chromatic aberration of the moment, 0..2.6 (PX.end: a lens blur of the world's edges with colour fringes;
  // the strength widens the blur, it never shifts the picture): strong from the countdown's '2' to 0.5 s after GO!, the slow
  // motions, a boss's fall, a relic picked up, Libération taking a blow, the victory (the strongest); less in lowFx,
  // none in minFx
  chromaK() {
    let k = 0; const now = performance.now(), c = this.cine, fade = (t0, dur, k0) => t0 ? k0 * Math.max(0, 1 - (now - t0) / dur) : 0;
    if (c && c.kind === 'countdown' && c.t >= 0.8) this._goCA = now;   // (from the countdown's '2' to GO!'s end: its clock held at now: full)
    k = Math.max(k, fade(this._goCA, 500, 2.4));   // then gone 0.5 s after GO!
    if (this.slowUntil > now) k = Math.max(k, 0.9 * Math.min(1, (this.slowUntil - now) / 350));   // the slow motions
    k = Math.max(k, fade(this._bossCA, 1800, 1.6));   // a boss's fall
    k = Math.max(k, fade(this._libCA, 700, 1.1));   // Libération taking a blow
    if (this.critFx) { const e = (now - this.critFx.t0) / 1000; k = Math.max(k, e < 2 ? 2.2 : 2.2 * Math.max(0, 1 - (e - 2) / 1.2)); }   // a critical summon
    if (this.relicShow) { const e = (now - this.relicShow.t0) / 1000; k = Math.max(k, e < 1 ? 1.3 - 0.8 * e : 0.5 * Math.max(0, 1 - (e - 2.4) / 0.6)); }   // a relic picked up
    const V = this.victoryFx; if (V) { const e = (now - V.t0) / 1000; k = Math.max(k, e < 0.7 ? 1 + 2 * e : e < 3.2 ? 2 + 0.35 * Math.sin(e * 4) : Math.max(0, 2 * (1 - (e - 3.2) / 0.7))); }   // the victory: the strongest
    return clamp(k, 0, 2.6) * (Game.minFx ? 0 : Game.lowFx ? 0.6 : 1);
  },
  timeK() { if (!(this.slowUntil > performance.now())) return 1; const left = (this.slowUntil - performance.now()) / 1000; return lerp(this.slowK, 1, clamp(1 - left / 0.35, 0, 1) * (left < 0.35 ? 1 : 0)); },   // (eases back the last 0.35 s)
  flash(color, sec, a) { this.flashFx = { color, t0: performance.now(), dur: sec * 1000, a }; },
  // ambers picked within 0.6 s of each other: the pickup sound goes up a step each time (up to an octave)
  amberSound() {
    const now = performance.now(); this._gemN = now - (this._gemT || 0) < 600 ? Math.min(14, (this._gemN || 0) + 1) : 0; this._gemT = now;
    const k = Audio2.SND && Audio2.SND.ui && Audio2.SND.ui.gem; if (k) Audio2.play(k, 0.22, Math.pow(2, this._gemN / 14)); else Audio2.blip('gem');
  },
  bump(what) { (this._bumps || (this._bumps = {}))[what] = performance.now(); },
  bumpK(what, dur = 260) { const t = this._bumps && this._bumps[what]; if (!t) return 0; const k = (performance.now() - t) / dur; return k < 1 ? Math.sin(k * Math.PI) : 0; },
  // hook points
  juiceKill(m) {
    this.bump('kills');
    // the kill combo: kills less than 1.6 s apart chain; 25 / 50 / 100 / 200 / 400 / 800 pop over the character
    if (this.time - (this._comboT || -9) > 1.6) { this._combo = 0; this._comboDone = false; }
    this._combo = (this._combo || 0) + 1; this._comboT = this.time; this.bump('ckill');
    const n = this._combo, mi = COMBO_MS.indexOf(n);
    // 0.62 (more juice to make combos wanted): a soft tick every 5 kills climbing a scale, a show at each step,
    // 'Nouveau record !' when the profile's best combo falls
    if (mi >= 0) this.comboTier(mi);
    else if (n >= 10 && n % 5 === 0) Audio2.comboSfx('tick', n);
    if (this.ps && n > (this.ps.bestCombo || 0)) this.ps.bestCombo = n;
    if (this._bestAtStart === undefined) this._bestAtStart = Store.data.bestCombo || 0;
    if (n > (Store.data.bestCombo || 0)) Store.data.bestCombo = n;
    if (!this._recShown && this._bestAtStart >= 25 && n === this._bestAtStart + 1) {
      this._recShown = true; const P = this.player; this.text(P.x, P.y - 146, T('combo_record'), '#5ad1ff', 19, 1.6); Audio2.comboSfx('record');
    }
    if (m.boss && !m.doom) {   // a boss falls: freeze, slow motion, white flash, a fountain of gold (the zone's final boss: 3 s and a 'VICTOIRE !')
      const fin = this.isFinalKill ? this.isFinalKill(m) : !!m.def.final, late = this.time >= (this.RUN.bossSlowT || 660) ? (this.RUN.bossSlowK || 0.25) : 1;   // (0.98: from 11:00 the slow motion lasts a quarter as long)
      this.hitStop(fin ? 220 : 140); this.slowMo((fin ? 3.0 : 1.5) * late, fin ? 0.25 : 0.3); this.flash('255,250,230', fin ? 0.7 : 0.45, 0.6); this._bossCA = performance.now();   // (0.98: its chromatic aberration)
      if (fin && !m.endless && !this.victoryShown) { this.victoryShown = true; this.startVictoryFx(); }
      for (let i = 0; i < 46 && this.particles.length < 380; i++) { const a = rand(TAU), v = rand(120, 420); this.particles.push({ x: m.x, y: m.y - m.r * 1.5, vx: Math.cos(a) * v, vy: Math.sin(a) * v - 160, t: 0, life: rand(0.7, 1.4), c: pick(['#ffd700', '#fff3a0', '#ffb02e', '#ffffff']), s: rand(3, 6), star: i % 6 === 0 ? 1 : 0 }); }
      this.rings.push({ x: m.x, y: m.y, r0: 20, r1: 260, t0: this.time, dur: 0.7, color: '#fff3a0' });
    } else if (m.def && m.def.special) {   // a mini-boss (Tofuzmo, Coffre Animé): 1.5 s of slow motion
      this.hitStop(110); this.slowMo(1.5, 0.35); this.flash('255,250,230', 0.35, 0.4);
      this.rings.push({ x: m.x, y: m.y, r0: 20, r1: 200, t0: this.time, dur: 0.6, color: '#fff3a0' });
    } else if (m.elite || m.archi) {   // an elite / Archimonster: a short freeze and a golden ring
      this.hitStop(m.archi ? 80 : 50); this.rings.push({ x: m.x, y: m.y, r0: 10, r1: 90, t0: this.time, dur: 0.45, color: '#ffd24a' });
    }
  },
  juiceHurt(d) {
    const st = this.stats; if (d >= st.maxHp * 0.1) { this.hitStop(45); this.flash('255,40,30', 0.22, 0.28); }
  },
  // an elite drops a relic: the same kind of moment as a boss falling, shorter
  juiceRelic(m) {
    this.hitStop(120); this.slowMo(1.0, 0.3); this.flash('255,215,90', 0.4, 0.45);
    this.rings.push({ x: m.x, y: m.y, r0: 10, r1: 160, t0: this.time, dur: 0.6, color: '#ffd24a' });
    for (let i = 0; i < 26 && this.particles.length < 380; i++) { const a = rand(TAU), v = rand(100, 300); this.particles.push({ x: m.x, y: m.y - m.r, vx: Math.cos(a) * v, vy: Math.sin(a) * v - 120, t: 0, life: rand(0.6, 1.1), c: pick(['#ffd700', '#fff3a0', '#ffb02e']), s: rand(2.5, 5), star: i % 5 === 0 ? 1 : 0 }); }
  },
  juiceLevel() { this.flash('255,226,122', 0.25, 0.22); this.bump('xp'); },
  // 0.61 (a more dramatic death): a heavy freeze and a red flash, the world in slow motion while the camera
  // closes in on the character and the screen darkens around it, its soul rising from the body (render.js drawSoul),
  // 'Vous êtes mort...' in big red letters; Audio2.deathSfx and the music fading out. The run still ends 2.2 s of run
  // time after the fall (Run.update), i.e. about 3.5 s with the slow motion
  juiceDeath() {
    this.hitStop(320); this.slowMo(2.2, 0.28); this.flash('130,0,4', 0.9, 0.7); if (Store.data.settings.shake) this.shakeAmt = Math.max(this.shakeAmt, 9);
    this.deathFx = { t0: performance.now() };
    Audio2.deathSfx(); Audio2.stopMusic(1.8);
  },
  deathE() { return this.deathFx ? (performance.now() - this.deathFx.t0) / 1000 : -1; },
  // the camera closes in (x1.35 over 1.6 s, then stays)
  deathZoomK() { const e = this.deathE(); if (e < 0) return 1; const k = clamp((e - 0.2) / 1.6, 0, 1); return 1 + 0.35 * k * k * (3 - 2 * k); },
  // a combo step (25, 50, 100, 200, 400, 800): its word over the character, a ring and stars around it, a flash of its
  // colour, a rising chord
  comboTier(mi) {
    const P = this.player, col = COMBO_COLS[mi];
    this.text(P.x, P.y - 118, '×' + this._combo + ' ' + T('combo_' + (mi + 1)), col, 20 + mi * 2, 1.2);
    Audio2.comboSfx('tier', mi); this.bump('combo');
    this.rings.push({ follow: P, x: P.x, y: P.y, r0: 30, r1: 150 + mi * 30, t0: this.time, dur: 0.55, color: col });
    for (let i = 0; i < 18 + mi * 6 && this.particles.length < 380; i++) { const a = rand(TAU), v = rand(140, 320 + mi * 40); this.particles.push({ x: P.x, y: P.y - 40, vx: Math.cos(a) * v, vy: Math.sin(a) * v - 120, t: 0, life: rand(0.5, 1.0), c: pick([col, '#fff3a0', '#ffffff']), s: rand(3, 6), star: i % 3 === 0 ? 1 : 0 }); }
    const n = parseInt(col.slice(1), 16); this.flash(`${n >> 16 & 255},${n >> 8 & 255},${n & 255}`, 0.3, 0.12 + mi * 0.02);   // (no hexRgb here: the node sim has no render.js)
  },
  // screen-space layer drawn before the HUD: the flash and the low-life vignette
  // the big 'VICTOIRE !' (drawVictory) with its confetti; 0.92: one roll per victory, 1 in 4 the 'fah' clip plays
  // once, a little after the fanfare
  startVictoryFx() {
    this.victoryFx = { t0: performance.now(), conf: makeConfetti(), fah: Math.random() < 0.25 };
    Audio2.fanfare && Audio2.fanfare(1);
  },
  drawJuice(ctx, W, H) {
    if (this._combo >= 25 && !this._comboDone && this.time - this._comboT > 1.6) { this._comboDone = true; this._comboEnd = { n: this._combo, t0: performance.now() }; Audio2.comboSfx('end'); }   // (0.62: a big combo broken)
    const F = this.flashFx;
    if (F) { const k = (performance.now() - F.t0) / F.dur; if (k >= 1) this.flashFx = null; else { ctx.fillStyle = `rgba(${F.color},${(F.a * (1 - k) * (1 - k)).toFixed(3)})`; ctx.fillRect(0, 0, W, H); } }
    const V = this.victoryFx;
    if (V) { const e = (performance.now() - V.t0) / 1000; if (V.fah && e > 0.7) { V.fah = false; Audio2.fxFile('fah', 1); Prog.add('fahHeard'); Prog.check(this); }
      if (e > 3.9) this.victoryFx = null; else drawVictory(ctx, W, H, e, T('victory_big'), V.conf); }
    if (this.critFx) { const e = (performance.now() - this.critFx.t0) / 1000; if (e < 2.6) drawConfetti(ctx, W, H, e, this.critFx.conf, e > 2 ? Math.max(0, 1 - (e - 2) / 0.6) : 1); }   // (0.98: a critical summon's confetti)
    if (this.deathFx) drawDeath(ctx, this, W, H, this.deathE());
    const P = this.player; if (!P || P.dead || this.over) return;
    const low = P.hp / this.stats.maxHp;
    if (low < 0.3) {   // low life: a red vignette that beats like a heart (faster when lower), a soft thump on each beat
      // 0.91: the beat's phase moves on by the frame's time (it was the clock x bpm: a life that changed by a hair every
      // frame — regeneration, hits — changed bpm and made the phase jump, so the thump restarted every ~40 ms: a dull buzz)
      const bpm = 70 + (0.3 - low) / 0.3 * 70, now = performance.now(), dt = this._hbT ? Math.min(0.1, (now - this._hbT) / 1000) : 0;
      this._hbT = now; this._hbPh = (this._hbPh || 0) + dt * bpm / 60;
      if (this._hbPh >= 1) { this._hbPh %= 1; Audio2.thump && Audio2.thump(0.25 + 0.25 * (1 - low / 0.3)); }
      const ph = this._hbPh, beat = ph < 0.12 ? ph / 0.12 : Math.max(0, 1 - (ph - 0.12) / 0.5);
      const V = this._vig && this._vig.width === W && this._vig.height === H ? this._vig : (this._vig = juiceVignette(W, H));
      ctx.globalAlpha = (0.35 + 0.45 * beat) * (1 - low / 0.3 * 0.5); ctx.drawImage(V, 0, 0); ctx.globalAlpha = 1;
    } else { this._hbT = 0; this._hbPh = 0.9; }   // (the first beat comes right after the life drops under 30 %)
  },
});
// 0.95 (announcements more mature and badass, in the spirit of the logo): the big centre-screen words — the
// countdown, GO!, the victory, the death, the fusion names, the banners — are set in Cinzel (assets/fonts/cinzel.woff2,
// OFL, weights 700-900): flared Roman capitals close to the logo's carved letters, its lower case drawn as small caps.
// annGlyph draws one string as carved metal: a deep extrusion under it, a dark outline, a thin bevel line, a light top
// edge, the gradient. Per-letter animations lay letters out with annLayout and draw each with annGlyph.
// 0.98: in Verdance (assets/fonts/verdance.woff2), the angular, flared lettering of Dofus Unity's logo; Cinzel stays behind
// it for the few signs Verdance has not (emoji, arrows)
const ANN_FONT = "Verdance, Cinzel, DofusBold, Verdana, sans-serif";
function annFont(px, w = 900) { return `${w} ${Math.max(4, Math.round(px))}px ${ANN_FONT}`; }
// palettes: gradient stops (top to bottom), outline, bevel line, extrusion, top-edge light
const ANN = {
  gold: { stops: [[0, '#fff8d8'], [0.36, '#ffd65a'], [0.62, '#f2a024'], [1, '#9c4e08']], edge: '#1c0d03', bevel: '#7a4210', deep: '#3a1d05', hi: '#fffbe8' },
  ember: { stops: [[0, '#fff1c8'], [0.34, '#ffb03a'], [0.64, '#e8601a'], [1, '#8a1e06']], edge: '#1c0703', bevel: '#7a2a0c', deep: '#3a0f04', hi: '#fff4dc' },
  blood: { stops: [[0, '#ff9a86'], [0.34, '#e2262c'], [0.68, '#9c0a12'], [1, '#3e0206']], edge: '#0d0002', bevel: '#4c0409', deep: '#1a0003', hi: '#ffcabc' },
  // 0.98, the verdant set (the Dofus Unity logo: cream letters on a gold rim in a lime halo; Dofus Retro's: gold letters among
  // leaves): halo = a soft lime outline around everything
  cream: { stops: [[0, '#ffffff'], [0.45, '#f7f0dc'], [0.8, '#e2d2a6'], [1, '#c4ab72']], edge: '#2a2414', bevel: '#f2b24a', deep: '#173a1c', hi: '#ffffff', halo: 'rgba(170,236,60,0.55)' },
  retro: { stops: [[0, '#fffbe0'], [0.32, '#ffe27a'], [0.62, '#f5b52e'], [1, '#a8650c']], edge: '#2a1a06', bevel: '#7a4a10', deep: '#1c3a16', hi: '#fffbe8', halo: 'rgba(160,232,60,0.55)' },
  lime: { stops: [[0, '#fbffe0'], [0.35, '#d8f870'], [0.66, '#9ad83a'], [1, '#4a8a16']], edge: '#14300c', bevel: '#f2e27a', deep: '#0e2a0c', hi: '#ffffff', halo: 'rgba(255,226,110,0.5)' },
};
// (centred on x; while see-through — fades — the layers are composed whole in a scratch canvas at the size on screen and
// laid at that opacity once: drawn one by one, the dark extrusion showed through the face)
function annGlyph(ctx, s, x, y, fs, P, w = 900) {
  if (ctx.globalAlpha > 0.995 || typeof document === 'undefined') { annCarve(ctx, s, x, y, fs, P, w); return; }
  const m = ctx.getTransform(), k = Math.min(4, Math.max(0.25, Math.hypot(m.a, m.b))), C = annGlyph.c || (annGlyph.c = document.createElement('canvas')), g = annGlyph.g || (annGlyph.g = C.getContext('2d'));
  const f = fs * k; g.font = annFont(f, w); const pw = Math.ceil(g.measureText(s).width + f * 0.9), ph = Math.ceil(f * 1.9);   // (0.98: room for the halo)
  if (C.width < pw || C.height < ph) { C.width = Math.max(C.width, pw); C.height = Math.max(C.height, ph); }
  g.setTransform(1, 0, 0, 1, 0, 0); g.globalAlpha = 1; g.globalCompositeOperation = 'source-over'; g.clearRect(0, 0, pw, ph); g.textAlign = 'center';
  annCarve(g, s, pw / 2, ph * 0.44, f, P, w);
  ctx.drawImage(C, 0, 0, pw, ph, x - pw / 2 / k, y - ph * 0.44 / k, pw / k, ph / k);
}
function annCarve(ctx, s, x, y, fs, P, w) {
  ctx.font = annFont(fs, w); ctx.textBaseline = 'middle'; ctx.lineJoin = 'round';
  const d = fs * 0.065, st = Math.max(1, fs * 0.016);
  if (P.halo) { ctx.strokeStyle = P.halo; ctx.lineWidth = fs * 0.34; ctx.strokeText(s, x, y + d * 0.5); ctx.lineWidth = fs * 0.24; ctx.strokeText(s, x, y + d * 0.5); }   // (0.98: the lime halo, two widths: a soft edge)
  ctx.fillStyle = P.deep; ctx.strokeStyle = P.deep; ctx.lineWidth = fs * 0.15;
  for (let k = d; k > 0; k -= st) { ctx.strokeText(s, x, y + k); ctx.fillText(s, x, y + k); }   // (the extrusion)
  ctx.strokeStyle = P.edge; ctx.strokeText(s, x, y);
  ctx.lineWidth = fs * 0.06; ctx.strokeStyle = P.bevel; ctx.strokeText(s, x, y);
  ctx.fillStyle = P.hi; ctx.fillText(s, x, y - fs * 0.022);   // (shows as a thin light line along the top edges)
  const g = ctx.createLinearGradient(0, y - fs * 0.48, 0, y + fs * 0.42); for (const [o, c] of P.stops) g.addColorStop(o, c);
  ctx.fillStyle = g; ctx.fillText(s, x, y);
}
// 0.95 ('3, 2, 1, GO!' a little high in its ring, the banners' messages off-centre in their frames): text is placed
// by its ink, not its em box — textBaseline 'middle' puts the em box's middle on y, and in Cinzel the capitals' and
// figures' ink sits elsewhere. annInk(s, fs, w): the offsets (dx, dy) to draw s at (x + dx, y + dy), centred ('center',
// 'middle'), so that the middle of its ink lands on (x, y). For a line of words pass 'H' (the capitals' middle: every line
// sits alike). Measured once per string and weight at 100 px, once the font is ready
const _annInk = new Map();
function annInk(s, fs, w = 900, font = null) {
  const f = font || annFont(100, w), key = f + '|' + s; let v = _annInk.get(key);
  if (!v) {
    const g = annInk.g || (annInk.g = document.createElement('canvas').getContext('2d')); g.font = f; g.textBaseline = 'middle'; g.textAlign = 'center';
    const m = g.measureText(s), k = parseFloat(f.match(/(\d+(?:\.\d+)?)px/)[1]);
    v = { dx: (m.actualBoundingBoxLeft - m.actualBoundingBoxRight) / 2 / k, dy: (m.actualBoundingBoxAscent - m.actualBoundingBoxDescent) / 2 / k };
    if (!document.fonts || document.fonts.check(f)) _annInk.set(key, v);
  }
  return { dx: v.dx * fs, dy: v.dy * fs };
}
// a light band sweeping across the letters only ('lighter' with the glyphs as the shape); at: the band's centre (px)
function annSheen(ctx, s, x, y, fs, at, a = 0.8, w = 900) {
  ctx.save(); ctx.font = annFont(fs, w); ctx.textBaseline = 'middle'; ctx.globalCompositeOperation = 'lighter';
  const g = ctx.createLinearGradient(at - fs * 0.7, 0, at + fs * 0.7, 0); g.addColorStop(0, 'rgba(255,250,225,0)'); g.addColorStop(0.5, `rgba(255,250,225,${a})`); g.addColorStop(1, 'rgba(255,250,225,0)');
  ctx.fillStyle = g; ctx.fillText(s, x, y); ctx.restore();
}
// the letters of a word laid out around 0 with a spacing (em): their widths and centres; the size shrinks to fit maxW
function annLayout(ctx, txt, fs, sp, maxW, w = 900) {
  const chars = [...txt]; let ws, tw;
  for (let i = 0; i < 2; i++) {
    ctx.font = annFont(fs, w); ws = chars.map(c => ctx.measureText(c).width); tw = ws.reduce((a, b) => a + b, 0) + sp * fs * (chars.length - 1);
    if (tw <= maxW || i) break; fs *= maxW / tw;
  }
  const xs = []; let x = -tw / 2; for (let i = 0; i < chars.length; i++) { xs.push(x + ws[i] / 2); x += ws[i] + sp * fs; }
  return { chars, ws, xs, tw, fs };
}
// a gold rule with a diamond in its middle, grown out from the centre (k 0..1), for the victory
function annRule(ctx, x, y, half, k, u, col = '#ffd65a') {
  if (k <= 0) return; const L = half * k;
  const g = ctx.createLinearGradient(x - L, 0, x + L, 0); g.addColorStop(0, 'rgba(255,214,90,0)'); g.addColorStop(0.5, col); g.addColorStop(1, 'rgba(255,214,90,0)');
  ctx.fillStyle = '#1c0d03'; ctx.fillRect(x - L, y - 2.2 * u, L * 2, 4.4 * u); ctx.fillStyle = g; ctx.fillRect(x - L, y - 1.1 * u, L * 2, 2.2 * u);
  const r = 7 * u * Math.min(1, k * 2); ctx.save(); ctx.translate(x, y); ctx.rotate(Math.PI / 4);
  ctx.fillStyle = '#1c0d03'; ctx.fillRect(-r - 2 * u, -r - 2 * u, (r + 2 * u) * 2, (r + 2 * u) * 2); ctx.fillStyle = col; ctx.fillRect(-r, -r, r * 2, r * 2);
  ctx.fillStyle = '#fff6d0'; ctx.fillRect(-r, -r, r, r * 0.6); ctx.restore();
}
// one line of a smaller announcement (banners, the relic's and the Dofus' captions): Cinzel 700, a dark outline, a
// light top edge, its colour; align as ctx.textAlign
function annLine(ctx, s, x, y, fs, color, font) {   // (0.98: font, another lettering for this line — the banners' Lilita, render.js BAN_FONT)
  ctx.font = font ? font(fs) : annFont(fs, 700); ctx.textBaseline = 'middle'; ctx.lineJoin = 'round';
  ctx.lineWidth = Math.max(2, fs * 0.2); ctx.strokeStyle = 'rgba(16,8,2,0.92)'; ctx.strokeText(s, x, y + fs * 0.03);
  ctx.fillStyle = 'rgba(255,248,226,0.8)'; ctx.fillText(s, x, y - fs * 0.03); ctx.fillStyle = color; ctx.fillText(s, x, y);
}
const annHash = i => { const x = Math.sin(i * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };

// 0.61: the death's screen layer: the world darkens around the character (a spotlight closing on it, a red rim).
// 0.95: then a thin crimson cut runs across the screen, a dark band opens behind it and 'Vous êtes mort...' comes in
// letter by letter, each sinking heavily into place in blood red Cinzel, blood slowly dripping from a few letters while
// ash falls through the band; the letters keep drifting apart slowly (screen space, before the HUD)
function drawDeath(ctx, R, W, H, e) {
  const P = R.player, z = Game.zoom * R.deathZoomK(), u = Math.min(W, H) / 720;
  const px = (P.x - R.cam.x) * z + W / 2, py = (P.y - 40 - R.cam.y) * z + H / 2;
  const k = clamp((e - 0.15) / 1.5, 0, 1), ke = k * k * (3 - 2 * k), far = Math.hypot(W, H);
  if (ke > 0) {
    const r1 = lerp(far, 210 * u, ke), r0 = r1 * 0.45, g = ctx.createRadialGradient(px, py, r0, px, py, r1);
    g.addColorStop(0, 'rgba(8,0,2,0)'); g.addColorStop(0.55, 'rgba(40,0,4,' + (0.45 * ke).toFixed(3) + ')'); g.addColorStop(1, 'rgba(6,0,1,' + (0.86 * ke).toFixed(3) + ')');
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  }
  const T0 = 1.0, t = e - T0; if (t <= 0) return;
  const y = H * 0.3;
  ctx.save();
  // the cut: a thin bright line racing across, then the band opening from it
  const cut = clamp(t / 0.18, 0, 1), open = clamp((t - 0.1) / 0.45, 0, 1), oe = 1 - Math.pow(1 - open, 3);
  const L = annLayout(ctx, T('dead_title'), Math.min(76 * u, W * 0.1), 0.05 + 0.06 * clamp((t - 0.3) / 2.5, 0, 1), W * 0.9);
  const fs = L.fs, bh = fs * 1.9 * oe;
  if (bh > 0) {
    const bg = ctx.createLinearGradient(0, y - bh / 2, 0, y + bh / 2);
    bg.addColorStop(0, 'rgba(0,0,0,0)'); bg.addColorStop(0.25, 'rgba(10,0,2,0.55)'); bg.addColorStop(0.75, 'rgba(10,0,2,0.55)'); bg.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = bg; ctx.fillRect(0, y - bh / 2, W, bh);
  }
  if (t < 0.7) {
    const a = t < 0.18 ? 1 : 1 - (t - 0.18) / 0.52, x1 = W * cut;
    const lg = ctx.createLinearGradient(0, 0, x1, 0); lg.addColorStop(0, 'rgba(160,0,10,0)'); lg.addColorStop(Math.max(0.01, 1 - 0.25 / Math.max(0.25, cut)), 'rgba(200,10,20,0.9)'); lg.addColorStop(1, 'rgba(255,200,190,1)');
    ctx.globalAlpha = a; ctx.fillStyle = lg; const th = 2.5 * u + bh * 0.04; ctx.fillRect(0, y - th / 2, x1, th);
    ctx.globalAlpha = 1;
  }
  // ash drifting down through the band
  for (let i = 0; i < 26; i++) {
    const q = ((t * (0.05 + 0.04 * annHash(i)) + annHash(i + 50)) % 1), ax = (annHash(i + 7) + Math.sin(t * 0.7 + i) * 0.02) * W, ay = y - fs * 1.4 + q * fs * 2.8, r = (1 + 2 * annHash(i + 9)) * u;
    ctx.globalAlpha = clamp(t / 0.8, 0, 1) * Math.sin(q * Math.PI) * 0.5; ctx.fillStyle = i % 4 ? '#6a5a58' : '#d04030'; ctx.fillRect(ax, ay, r, r);
  }
  // the letters: one by one, each sinking into place with its weight, then settled; blood dripping from a few
  const cx = W / 2;
  L.chars.forEach((c, i) => {
    if (c === ' ') return;
    const lk = clamp((t - 0.22 - i * 0.045) / 0.42, 0, 1); if (lk <= 0) return;
    const ee = 1 - Math.pow(1 - lk, 3), dy = -(1 - ee) * fs * 0.32, sc = 1 + (1 - ee) * 0.18;
    ctx.globalAlpha = Math.min(1, lk * 1.6);
    ctx.save(); ctx.translate(cx + L.xs[i], y + dy); ctx.scale(sc, sc); ctx.textAlign = 'center';
    annGlyph(ctx, c, 0, 0, fs, ANN.blood); ctx.restore();
    if (annHash(i + 21) < 0.34 && lk >= 1) {   // a drip: it grows slowly under the letter, a drop at its end
      const dk = clamp((t - 0.7 - i * 0.045 - annHash(i) * 0.6) / 2.4, 0, 1), len = fs * (0.18 + 0.45 * annHash(i + 4)) * Math.sqrt(dk), dx = cx + L.xs[i] + (annHash(i + 2) - 0.5) * L.ws[i] * 0.5, dy0 = y + fs * 0.3;
      if (len > 1) { ctx.globalAlpha = 0.95; ctx.fillStyle = '#5a0006'; ctx.fillRect(dx - 1.6 * u, dy0, 3.2 * u, len); ctx.fillStyle = '#9c0a12'; ctx.fillRect(dx - 0.8 * u, dy0, 1.6 * u, len);
        ctx.beginPath(); ctx.arc(dx, dy0 + len, 2.8 * u, 0, TAU); ctx.fillStyle = '#7a0008'; ctx.fill(); }
    }
  });
  ctx.restore();
}
// the vignette: a red frame fading to nothing in the middle (drawn once per screen size)
function juiceVignette(W, H) {
  const c = document.createElement('canvas'); c.width = W; c.height = H; const g = c.getContext('2d');
  const r = Math.hypot(W, H) / 2, gr = g.createRadialGradient(W / 2, H / 2, r * 0.45, W / 2, H / 2, r);
  gr.addColorStop(0, 'rgba(150,0,10,0)'); gr.addColorStop(0.7, 'rgba(150,0,10,0.35)'); gr.addColorStop(1, 'rgba(110,0,5,0.85)');
  g.fillStyle = gr; g.fillRect(0, 0, W, H); return c;
}

// 0.60: the zone's final boss is down: a big golden 'VICTOIRE !' in the Dofus style during the slow motion (the letters
// fall in one by one and bounce, light rays turn behind, sparkles), then everything fades back to the game
// 0.92: confetti over the whole screen: two cannons from the bottom corners, then a shower from the top; each piece
// a little card turning over (its height by its spin) and swaying as it flutters down, its path worked out from the time
// (drag towards a slow fall, no per-frame state); behind the letters, gone with the 'VICTOIRE !'
const CONFETTI_COL = ['#ffd24a', '#fff3c0', '#e8402a', '#3aa0ff', '#5ad16a', '#ff7ad0', '#b07aff', '#ffffff'];
function makeConfetti() {
  const P = [];
  for (let i = 0; i < 150; i++) {
    const side = i % 3, top = side === 2;   // (0, 1: the cannons, 2: the shower)
    const a = top ? 0 : (side === 0 ? 1 : -1) * rand(0.18, 0.62), v = top ? 0 : rand(1.1, 1.9);   // (the left cannon shoots up-right, the right one up-left)
    P.push({ x0: top ? rand(-0.05, 1.05) : side === 0 ? -0.02 : 1.02, y0: top ? rand(-0.14, -0.02) : 1.02, vx: top ? rand(-0.05, 0.05) : Math.sin(a) * v * 0.62, vy: top ? rand(0.15, 0.35) : -Math.cos(a) * v,
      d: top ? rand(0.35, 1.3) : rand(0, 0.25), vt: rand(0.1, 0.2), sw: rand(0.008, 0.022), sf: rand(2, 4.5), sp: rand(5, 12), r0: rand(TAU), w: rand(10, 15), h: rand(6, 9), c: pick(CONFETTI_COL) });
  }
  return P;
}
function drawConfetti(ctx, W, H, e, P, fade) {
  const u = Math.min(W, H) / 720, k = 1.7;
  for (const p of P) {
    const t = e - p.d; if (t <= 0) continue;
    const ex = (1 - Math.exp(-k * t)) / k, x = (p.x0 + p.vx * ex + Math.sin(t * p.sf + p.r0) * p.sw) * W, y = (p.y0 + p.vt * t + (p.vy - p.vt) * ex) * H;
    if (y > H + 20 || x < -20 || x > W + 20) continue;
    const r = p.r0 + t * p.sp, fl = Math.cos(r * 1.3);
    ctx.globalAlpha = fade * 0.95; ctx.fillStyle = p.c;
    ctx.setTransform(Math.cos(r), Math.sin(r), -Math.sin(r) * fl, Math.cos(r) * fl, x, y);
    ctx.fillRect(-p.w * u / 2, -p.h * u / 2, p.w * u, p.h * u);
  }
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1;
}
// 0.95: a blade of light opens across the middle, the letters strike in from the centre outwards (each from big to its
// size with a short overshoot and a golden flare), a burst of light when the last one lands, two gold rules with their
// diamonds grow out above and below, then the word breathes in the god rays, a sheen running over it, embers rising.
// 0.98 (verdant, like the Dofus logos): a deep green veil, lime and gold rays, Dofus Retro's gold letters in a lime halo,
// leaves on the rules' diamonds, leaves twirling down with the confetti, fireflies instead of embers
function drawVictory(ctx, W, H, e, txt, conf) {
  const fade = e < 0.25 ? e / 0.25 : e > 3.2 ? Math.max(0, 1 - (e - 3.2) / 0.7) : 1, cx = W / 2, cy = H * 0.4, u = Math.min(W, H) / 720;
  ctx.save();
  ctx.fillStyle = `rgba(2,22,12,${(0.42 * fade).toFixed(3)})`; ctx.fillRect(0, 0, W, H);
  // god rays: long soft beams turning slowly
  ctx.translate(cx, cy); ctx.rotate(e * 0.16); ctx.globalAlpha = 0.3 * fade * clamp(e / 0.6, 0, 1);
  for (let i = 0; i < 12; i++) {
    ctx.rotate(TAU / 12); const L = (i % 2 ? 520 : 400) * u, g = ctx.createLinearGradient(0, 0, 0, -L); g.addColorStop(0, i % 2 ? 'rgba(255,226,140,0.95)' : 'rgba(190,245,100,0.95)'); g.addColorStop(1, 'rgba(190,245,100,0)');
    ctx.fillStyle = g; ctx.beginPath(); ctx.moveTo(-6 * u, 0); ctx.lineTo(6 * u, 0); ctx.lineTo(40 * u, -L); ctx.lineTo(-40 * u, -L); ctx.closePath(); ctx.fill();
  }
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  if (conf) drawConfetti(ctx, W, H, e, conf, e > 3.2 ? fade : 1);
  for (let i = 0; i < 16; i++) {   // leaves twirling down
    const q = (e * (0.16 + 0.08 * annHash(i + 80)) + annHash(i + 81)) % 1, lx = (annHash(i + 82) + Math.sin(e * 1.4 + i) * 0.04) * W, ly = -40 * u + q * (H + 80 * u);
    ctx.save(); ctx.globalAlpha = fade * 0.95; ctx.translate(lx, ly); ctx.rotate(e * (1.5 + annHash(i + 83)) * (i % 2 ? 1 : -1) + i); ctx.scale(1, 0.4 + 0.6 * Math.abs(Math.sin(e * 3 + i)));
    cdLeaf(ctx, (16 + 12 * annHash(i + 84)) * u, CD_LEAVES[i % CD_LEAVES.length]); ctx.restore();
  }
  const out = e > 3.2 ? (e - 3.2) / 0.7 : 0, A = annLayout(ctx, txt, 112 * u, 0.18 + out * 0.12, W * 0.88)   /* (0.98: wider: 0.04 -> 0.18 em, the halo takes some) */, fs = A.fs, mid = (A.chars.length - 1) / 2;
  const y = cy - Math.min(e, 3.2) * 3 * u, glowG = RCache.glow('rgba(255,214,110,0.95)'), glowW = RCache.glow('rgba(255,248,220,0.95)');
  // the blade of light that opens the moment
  if (e < 0.75) {
    const k = clamp(e / 0.3, 0, 1), w = (A.tw / 2 + fs * 0.6) * (1 - Math.pow(1 - k, 3)), a = e < 0.3 ? 1 : 1 - (e - 0.3) / 0.45;
    ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha = a; ctx.drawImage(glowG, cx - w, y - fs * 0.35, w * 2, fs * 0.7);
    ctx.fillStyle = '#fff8e4'; ctx.fillRect(cx - w, y - 1.5 * u, w * 2, 3 * u); ctx.restore();
  }
  // the burst when the last letter lands
  const land = 0.12 + mid * 0.05 + 0.3, bk = (e - land) / 0.5;
  if (bk > 0 && bk < 1) { ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha = (1 - bk) * 0.85; const r = A.tw * (0.45 + 0.4 * bk); ctx.drawImage(glowW, cx - r, y - r * 0.45, r * 2, r * 0.9); ctx.restore(); }
  // the rules above and below
  const rk = clamp((e - land + 0.1) / 0.45, 0, 1), re = 1 - Math.pow(1 - rk, 3);
  ctx.globalAlpha = fade; annRule(ctx, cx, y + fs * 0.78, A.tw * 0.5 + fs * 0.4, re, u); annRule(ctx, cx, y - fs * 0.78, A.tw * 0.32, re, u * 0.8);
  if (re > 0) for (const [ry, k] of [[y + fs * 0.78, 1], [y - fs * 0.78, 0.8]]) for (const sd of [-1, 1]) {   // (0.98: two leaves on each diamond)
    ctx.save(); ctx.translate(cx + sd * 12 * u * k, ry); ctx.scale(sd, 1); ctx.rotate(-0.25 + Math.sin(e * 2 + ry) * 0.08); ctx.translate(13 * u * k * re, 0); cdLeaf(ctx, 26 * u * k * re, sd > 0 ? '#7cd04a' : '#3fae3a'); ctx.restore();
  }
  // the letters, from the centre outwards
  const br = 1 + 0.012 * Math.sin(e * 2.6);
  A.chars.forEach((c, i) => {
    if (c === ' ') return;
    const k = clamp((e - 0.12 - Math.abs(i - mid) * 0.05) / 0.3, 0, 1); if (k <= 0) return;
    const sc = (k < 0.7 ? 2.1 - 1.16 * (1 - Math.pow(1 - k / 0.7, 3)) : 0.94 + 0.06 * Math.sin((k - 0.7) / 0.3 * Math.PI / 2)) * br * (1 + out * 0.08);
    ctx.globalAlpha = fade * Math.min(1, k * 2.2);
    ctx.save(); ctx.translate(cx + A.xs[i] * (1 + out * 0.1), y); ctx.scale(sc, sc); ctx.textAlign = 'center';
    if (k < 1) { ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha *= (1 - k) * 0.9; ctx.drawImage(glowG, -fs * 0.6, -fs * 0.6, fs * 1.2, fs * 1.2); ctx.restore(); }   // (its flare)
    annGlyph(ctx, c, 0, 0, fs, ANN.retro); ctx.restore();
  });
  // a sheen running over the word now and then
  const sw = (e - land - 0.2) % 1.7; if (e > land + 0.2 && sw < 0.8) { ctx.globalAlpha = fade; ctx.textAlign = 'center'; const at = -A.tw / 2 - fs + (A.tw + fs * 2) * sw / 0.8; A.chars.forEach((c, i) => annSheen(ctx, c, cx + A.xs[i] * (1 + out * 0.1), y, fs * br * (1 + out * 0.08), cx + at, 0.75)); }
  // fireflies rising around the word, sparkles twinkling on it
  ctx.save(); ctx.globalCompositeOperation = 'lighter'; const glowL = RCache.glow('rgba(200,250,110,0.95)');
  for (let i = 0; i < 22; i++) {
    const q = (e * (0.18 + 0.12 * annHash(i)) + annHash(i + 30)) % 1, ex = cx + (annHash(i + 3) - 0.5) * A.tw * 1.3 + Math.sin(e * 1.3 + i) * 8 * u, ey = y + fs * 0.9 - q * fs * 2.4, r = (6 + 8 * annHash(i + 5)) * u;
    ctx.globalAlpha = fade * Math.sin(q * Math.PI) * 0.8 * clamp((e - land) / 0.4, 0, 1); ctx.drawImage(i % 3 ? glowL : glowG, ex - r, ey - r, r * 2, r * 2);
  }
  for (let i = 0; i < 7; i++) {
    const tw2 = Math.max(0, Math.sin(e * 2.2 + i * 2.1)), sx = cx + (annHash(i + 60) - 0.5) * A.tw * 0.95, sy = y + (annHash(i + 61) - 0.5) * fs * 0.7, s = (4 + 9 * tw2) * u;
    if (tw2 < 0.05 || e < land) continue; ctx.globalAlpha = fade * tw2; ctx.fillStyle = '#fffbe6';
    ctx.beginPath(); for (let k = 0; k < 8; k++) { const rr = k % 2 ? s * 0.16 : s, aa = k / 8 * TAU; ctx.lineTo(sx + Math.cos(aa) * rr, sy + Math.sin(aa) * rr); } ctx.closePath(); ctx.fill();
  }
  ctx.restore();
  ctx.restore();
}
