'use strict';
// ---------------------------------------------------------------- special events (0.26). Methods added to Run, called
// from hook points in game.js / render.js / main.js:
//  - cinematics: the boss chest and the Dofus pickups freeze the game for a short show (startCine / tickCine / drawCine)
//  - ToT's door is a time portal in C.portal.chance of the runs; otherwise the Tofu Mutant runs around the map
//  - the Coffre Animé (every boss of the zone down before C.coffre.t), Musha l'Oni's treasure maps (C.tmap)
//  - TTG boosters near the corners of the map (C.ttg.cards: the 464 official cards since 0.34, weighted by rarity C.ttg.rw)
// the treasure's Chouque: each of his 3 bubbles stays TM_SAY s, the last one TM_SAY + TM_LAST (0.95: twice as long, 2.2 s
// before; 0.96: twice again, 4.4 s before)
const TM_SAY = 8.8, TM_LAST = 2.4;
// 0.97: a bubble's text with **names** — drawn in bold between the language's quotes, never split over two lines; rows of
// segments {t, b, w}, each row with its width (drawTreasure centres it on that: nothing shifted)
const QUOTES = { fr: ['« ', ' »'], de: ['„', '“'], es: ['«', '»'], it: ['«', '»'], pt: ['«', '»'], en: ['“', '”'], nl: ['“', '”'] };
function richWrap(ctx, text, maxW, fN, fB) {
  const q = QUOTES[LANG] || QUOTES.en, words = String(text).split(/\s+/).filter(Boolean).map(w => w.split(/\*\*(.+?)\*\*/).map((t, i) => ({ t: i % 2 ? q[0] + t + q[1] : t, b: i % 2 === 1 })).filter(s => s.t));
  const width = segs => segs.reduce((a, s) => { ctx.font = s.b ? fB : fN; s.w = ctx.measureText(s.t).width; return a + s.w; }, 0);
  ctx.font = fN; const sp = ctx.measureText(' ').width, rows = []; let cur = null;
  for (const w of words) {
    const ww = width(w);
    if (cur && cur.w + sp + ww > maxW) { rows.push(cur); cur = null; }
    if (!cur) cur = { segs: [...w], w: ww }; else { cur.segs.push({ t: ' ', b: false, w: sp }, ...w); cur.w += sp + ww; }
  }
  if (cur) rows.push(cur);
  return rows;
}
Object.assign(Run.prototype, {
  initEvents() {
    const C = this.C, S = Store.data, dbg = typeof Game !== 'undefined' && Game.debug ? Game.debug : {};
    this.cine = null; this.mutant = null; this.coffreDone = false; this.tmapDig = 0;
    this.portalRun = dbg.tot || dbg.portal || Math.random() < (C.portal ? C.portal.chance : 1);
    const TM = C.tmap; S.tmaps = S.tmaps || {};
    // 0.47: a treasure in every zone; a map drops in any zone (half as often as the Manuel du Tailleur) and leads to a
    // random zone that has none yet, secret zones too (?tmap=1, ?tmap=<zone> to pick it)
    this.tmapDrop = TM && this.tmapFree().length && (dbg.tmap || Math.random() < TM.chance) ? { t: dbg.tmap ? 5 : rand(TM.t0, TM.t1) } : null;
    this.tmapFix();
    this.tmapHere = S.tmaps[this.map.id] && !S.tmaps[this.map.id].found ? S.tmaps[this.map.id] : null;
  },
  // 0.51: a treasure not dug yet whose cross no longer lies in its zone's bounds (Dark Vlad's zone was made smaller):
  // a new spot in that zone
  tmapFix() {
    const S = Store.data.tmaps || {}; let n = 0;
    for (const id in S) {
      const e = S[id], m = this.C.maps.find(x => x.id === id), W = m && SPR.worlds[m.world];
      if (!e || e.found || !W) continue;
      const ins = W.inset || [0, 0, 0, 0];
      if (e.x >= 30 + ins[0] && e.x <= W.w - 30 - ins[1] && e.y >= 40 + ins[2] && e.y <= W.h - 20 - ins[3]) continue;
      Object.assign(e, this.tmapSpot(m)); n++;
    }
    if (n) Store.save();
  },
  eventKeys(keys) {
    const M = this.C.monsters; for (const id of ['tofu_mutant', 'coffre_anime', 'jorbak']) if (M[id]) keys.add(M[id].sprite);
    const tm = (Store.data.tmaps || {})[this.map.id], G = this.C.tmap && this.C.tmap.ghost; if (G && tm && !tm.found) keys.add(G.sprite);   // (0.68: the Chouque's ghost, when this zone's treasure is still buried)
  },
  // the boosters are placed once the world bounds are known (loadExtras time)
  placeBoosters() {
    const T_ = this.C.ttg; if (!T_ || !T_.cards || !T_.cards.length) return;
    const b = this.bounds, w = b.x1 - b.x0, h = b.y1 - b.y0, m = T_.corner || 0.12;
    const corners = [[b.x0 + w * m, b.y0 + h * m], [b.x1 - w * m, b.y0 + h * m], [b.x0 + w * m, b.y1 - h * m], [b.x1 - w * m, b.y1 - h * m]];
    // (0.35: a single booster per run, in one corner, between 3:00 and 6:00, announced)
    this.boosterSpot = pick(corners); this.boosterAt = rand(180, 360);
  },
  // 0.38: the pack's look: every design comes once before any comes again (a shuffled bag kept in the profile)
  nextPack() {
    const n = SPR.boosters.n, S = Store.data;
    if (!Array.isArray(S.packBag) || !S.packBag.length || S.packBag.some(i => i >= n)) { S.packBag = shuffle([...Array(n).keys()]); if (S.packBag[0] === S.lastPack) S.packBag.push(S.packBag.shift()); }
    const i = S.packBag.shift(); S.lastPack = i; Store.save(); return i;
  },
  dropBooster() {
    const T_ = this.C.ttg, b = this.bounds, w = b.x1 - b.x0, h = b.y1 - b.y0, [cx, cy] = this.boosterSpot; this.boosterAt = 0;
    for (let k = 0; k < 40; k++) {   // a dry spot near the corner
      let x = cx + rand(-w * 0.08, w * 0.08), y = cy + rand(-h * 0.08, h * 0.08);
      if (k === 39) { const a = rand(0, TAU); x = this.player.x + Math.cos(a) * 500; y = this.player.y + Math.sin(a) * 500; }   // 0.37: never lost in the water
      if (!this.isWater(x, y) || k === 39) { { const pk = this.nextPack(); this.dropPickup('booster', x, y, 1).pk = pk; BoosterArt.get(pk); } this.announce(T('booster_here_t'), T('booster_here'), '#9cff6a'); Audio2.play('pages', 0.6); return; }
    }
  },
  // ------------------------------------------------ 0.52: Dark Vlad beaten in Difficile in his clearing: the last zone
  // (Goultard's, unlockBy 'vlad_hard') opens at once; the first time, his fall in slow motion (red lightning, the ground
  // cracking, a red flash), then his last words and Goultard's (UI.vladScene)
  vladFall(m) {
    const S = Store.data, Z = this.C.maps.find(z => z.unlockBy === 'vlad_hard');
    if (!Z || S.unlocked.includes(Z.id)) return;
    S.unlocked.push(Z.id); Store.save(); this.unlockedNow.push(Object.assign({ secret: true }, Z));
    this.startCine('vlad', { m }, () => { if (typeof UI !== 'undefined' && UI.vladScene && !(Game.debug || {}).bot) UI.vladScene(this, Z); });
  },
  // 0.60: Goultard beaten the first time on this profile: the same fall as Dark Vlad's (slow, red lightning, cracks), then
  // his last words (UI.goultardScene); the 'VICTOIRE !' comes after them
  goultardFall(m) {
    const S = Store.data; if (S.goultardDown) return; S.goultardDown = 1; S.goultardThanks = 1; Store.save();   // (0.91: thanks + Discord on the next main menu, UI.goultardThanks)
    this.victoryFx = null;
    this.startCine('vlad', { m }, () => { if (typeof UI !== 'undefined' && UI.goultardScene && !(Game.debug || {}).bot) UI.goultardScene(this, () => this.startVictoryFx()); });
  },
  // ------------------------------------------------ cinematics
  startCine(kind, data, done) {
    const real = typeof Game !== 'undefined' && Game.ctx && !Game.debug.bot && !Game.debug.nodraw;
    if (!real) { done(); return; }
    this.cine = { kind, data, t: 0, dur: (this.C.cine || {})[kind] || 2, done, fired: {} };
    if (kind === 'dofus') { Audio2.play('stars', 0.9); Audio2.sfx('EVENT', 0.8); }
    if (kind === 'chest') Audio2.play('saut', 0.6, 1.2);
    if (kind === 'vlad') { Audio2.sfx('EVENT', 0.9); Audio2.blip('boom'); }
    if (kind === 'countdown') this.cine.dur = 3.3;
    if (kind === 'union') this.cine.dur = 3.0;   // (0.60: spell fusion, sfusions.js)
    if (kind === 'gift') this.cine.dur = 4.6;   // (0.68: Nowel's gift, nowel.js)
    if (kind === 'treasure') { this.cine.dur = 1.4 + data.lines.length * TM_SAY + TM_LAST; Audio2.sfx('EVENT', 0.8); const mu = (this.C.tmap.ghost || {}).music; if (mu) Audio2.jingle(mu); }   // (0.97: his own music while he talks, C.tmap.ghost.music)   // (0.68: the dug treasure; 30.2 s for 3 bubbles: 8.6 s until 0.94, 15.8 in 0.95)
  },
  tickCine(dt) {
    const c = this.cine, P = this.player; if (c.kind === 'countdown' && this.warming) return;   // (0.98.2: the countdown waits for what the run still prepares, Game.startRun)
    c.t += dt;
    const once = (k, f) => { if (!c.fired[k]) { c.fired[k] = true; f(); } };
    if (c.kind === 'chest') {
      if (c.t > 0.6) once('chomp', () => { Audio2.play('coffre', 0.8); Audio2.play('grrr1', 0.5); });
      if (c.t > 1.2) once('burst', () => {
        const p = c.data.p; Audio2.play('stars', 0.8); Audio2.blip('coin'); this.shake(4);
        this.rings.push({ x: p.x, y: p.y - 20, r0: 10, r1: 150, t0: this.time, dur: 0.5, color: '#ffd24a', fill: 1 });
        for (let i = 0; i < 70; i++) { const a = rand(TAU), v = rand(120, 420); this.particles.push({ x: p.x, y: p.y - 24, vx: Math.cos(a) * v, vy: Math.sin(a) * v * 0.7 - 160, t: 0, life: rand(0.6, 1.2), c: pick(['#ffd700', '#ffe866', '#ff5a5a', '#5ad1ff', '#9cff6a', '#ff9cf0']), s: rand(3, 7) }); }
      });
    } else if (c.kind === 'dofus') {
      const anim = (this.cls.casts && this.cls.casts[0]) || 'anim1', key = P.sprite.has(anim + 'R') ? anim + 'R' : null;
      if (key) { P.castAnim = key; P.castT = Math.min(c.t * 0.8, P.sprite.duration(key) * 0.45); }   // arms up, held
      if (c.t > 0.55) once('raise', () => { Audio2.ui('level', 0.9); for (let i = 0; i < 40; i++) { const a = rand(TAU); this.particles.push({ x: P.x + Math.cos(a) * 10, y: P.y - 120, vx: Math.cos(a) * rand(60, 200), vy: Math.sin(a) * rand(60, 200) - 40, t: 0, life: rand(0.6, 1.1), c: pick(['#fff6c0', '#ffffff', c.data.dof.color]), s: rand(2, 5) }); } });
    } else if (c.kind === 'countdown') {   // 0.53: 3 (0 s), 2 (0.8), 1 (1.6), GO! (2.4); one time in ten GO! is a fart
      const n = Math.min(3, Math.floor(c.t / 0.8));
      once('n' + n, () => {   // 0.60: the client's turn-start chime for 3-2-1 (a little higher each time), its fight-start for GO!
        const tk = Audio2.SND && Audio2.SND.ui && Audio2.SND.ui.turn;
        if (n < 3) { if (tk) Audio2.play(tk, 0.85, [0.9, 1.0, 1.12][n]); else Audio2.countdownSfx(3 - n); return; }
        if (Math.random() < 0.1) Audio2.play('pet', 1, 1.05); else { Audio2.ui('door', 0.95); Audio2.play('stars', 0.5, 1.1); }
        const P = this.player;   // (no ring / shake here: they run on the run's clock, frozen until GO! is over)
        for (let i = 0; i < 60; i++) { const a = rand(TAU), v = rand(160, 460); this.particles.push({ x: P.x, y: P.y - 30, vx: Math.cos(a) * v, vy: Math.sin(a) * v * 0.7 - 120, t: 0, life: rand(0.5, 1), c: pick(['#ffe066', '#fff6c8', '#9cff6a', '#5ad1ff', '#ff9cf0']), s: rand(3, 6) }); }
      });
    } else if (c.kind === 'treasure') {   // 0.68: the chest comes out of the ground, the Chouque's ghost circles around and talks
      const D = c.data;
      this.cam.x += (P.x - this.cam.x) * Math.min(1, dt * 3); this.cam.y += (P.y - 30 - this.cam.y) * Math.min(1, dt * 3);
      if (c.t > 0.15) once('chest', () => { Audio2.play('coffre', 0.7, 0.9); this.shake(3); for (let i = 0; i < 26; i++) this.particles.push({ x: D.x + rand(-20, 20), y: D.y, vx: rand(-120, 120), vy: rand(-260, -80), t: 0, life: rand(0.5, 0.9), c: pick(['#7a5a34', '#5a4026', '#a8865c']), s: rand(3, 6) }); });
      if (c.t > 0.9) once('ghost', () => { Audio2.play('stars', 0.6, 0.7); Audio2.sfx('EVENT', 0.5); });
      const n = Math.min(D.lines.length - 1, Math.floor((c.t - 1.4) / TM_SAY));
      if (c.t > 1.4 && n !== D.said) { D.said = n; Audio2.play(pick(['pose2', 'vol', 'fronde']), 0.6, rand(1.05, 1.25)); }
      if (this.particles.length < 240) { const a = rand(TAU); this.particles.push({ x: P.x + Math.cos(a) * 60, y: P.y + Math.sin(a) * 20, vx: 0, vy: rand(-90, -40), t: 0, life: rand(0.6, 1.1), c: pick(['#8ff0ff', '#c8a0ff', '#ffffff']), s: rand(2, 3.5) }); }
    } else if (c.kind === 'union') this.tickUnion(c, dt);
    else if (c.kind === 'vlad') {   // 0.52: Dark Vlad falls in slow motion; the camera goes to him
      const m = c.data.m, D = c.data;
      m.dieT = Math.min(m.dieT + dt * 0.4, 3.5); this.shakeAmt = Math.max(0, this.shakeAmt - dt * 30);
      this.cam.x += (m.x - this.cam.x) * Math.min(1, dt * 3); this.cam.y += (m.y - 50 - this.cam.y) * Math.min(1, dt * 3);
      if (!D.cracks) {   // jagged cracks from his feet, drawn growing (drawCineScreen)
        D.cracks = []; D.bolts = []; D.bt = 0.15;
        for (let i = 0; i < 10; i++) { let a = (i / 10) * TAU + rand(-0.25, 0.25), x = 0, y = 0; const pts = [[0, 0]]; for (let s = 0; s < 7; s++) { a += rand(-0.55, 0.55); const l = rand(22, 44); x += Math.cos(a) * l; y += Math.sin(a) * l * 0.55; pts.push([x, y]); } D.cracks.push(pts); }
      }
      if ((D.bt -= dt) <= 0 && c.t < 3.8) { D.bt = rand(0.22, 0.55); D.bolts.push({ t0: c.t, x: m.x + rand(-170, 170), y: m.y + rand(-70, 50), seed: randi(1, 1e6) }); this.shake(6); Audio2.blip('boom'); }
      if (this.particles.length < 260) for (let i = 0; i < 3; i++) this.particles.push({ x: m.x + rand(-60, 60), y: m.y + rand(-20, 10), vx: rand(-30, 30), vy: rand(-320, -160), t: 0, life: rand(0.8, 1.4), c: pick(['#ff3a1a', '#ff7a2a', '#ffcf6a', '#8a0a0a']), s: rand(2, 4) });
      if (c.t > 3.9) once('burst', () => {
        this.shake(14); Audio2.sfx('EVENT', 1); Audio2.blip('boom');
        this.rings.push({ x: m.x, y: m.y - 30, r0: 10, r1: 260, t0: this.time, dur: 0.6, color: '#ff2a1a', fill: 1 });
        for (let i = 0; i < 90; i++) { const a = rand(TAU), v = rand(140, 480); this.particles.push({ x: m.x, y: m.y - 40, vx: Math.cos(a) * v, vy: Math.sin(a) * v * 0.7 - 160, t: 0, life: rand(0.6, 1.3), c: pick(['#ff2a1a', '#ff6a2a', '#ffd27a', '#2a0000']), s: rand(3, 7) }); }
      });
    }
    // particles and rings keep moving during the show
    for (const p of this.particles) { p.t += dt; p.x += p.vx * dt; p.y += p.vy * dt; p.vy += 260 * dt; }
    this.particles = this.particles.filter(p => p.t < p.life);
    if (c.t >= c.dur) { this.cine = null; P.castAnim = null; c.done(); }
  },
  // world space: the chest's show is drawn by drawPickup (p.cine); nothing else here yet
  // screen space, over the HUD: the dark frame with a light on the character, the Dofus held up, the caption
  drawCineScreen(ctx, W, H) {
    const c = this.cine; if (!c) return;
    const P = this.player, z = Game.zoom, sx = (P.x - this.cam.x) * z + W / 2, sy = (P.y - this.cam.y) * z + H / 2;
    const k = Math.min(1, c.t / 0.3) * Math.min(1, (c.dur - c.t) / 0.3);
    if (c.kind === 'vlad') { ctx.save(); this.drawVladFall(ctx, W, H, c, z, k); ctx.restore(); return; }
    if (c.kind === 'countdown') { ctx.save(); this.drawCountdown(ctx, W, H, c); ctx.restore(); return; }
    if (c.kind === 'union') { ctx.save(); this.drawUnion(ctx, W, H, c); ctx.restore(); return; }
    if (c.kind === 'treasure') { ctx.save(); this.drawTreasure(ctx, W, H, c, z, k); ctx.restore(); return; }
    if (c.kind === 'gift') { ctx.save(); this.drawGift(ctx, W, H, c); ctx.restore(); return; }
    const dark = c.kind === 'dofus' ? 0.72 : 0.35, rad = (c.kind === 'dofus' ? 170 : 220) * z;
    const g = ctx.createRadialGradient(sx, sy - 40 * z, rad * 0.35, sx, sy - 40 * z, rad);
    g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, `rgba(0,0,0,${dark * k})`);
    ctx.save(); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    if (c.kind === 'dofus') {   // "Da-da-da-daaa": rays turning behind the egg, the egg held up over the head
      const dof = c.data.dof, up = Math.min(1, Math.max(0, (c.t - 0.2) / 0.4)), ex = sx, ey = sy - (95 + 40 * up) * z - Math.sin(c.t * 3) * 3 * z;
      ctx.globalAlpha = k * up; ctx.translate(ex, ey); ctx.rotate(c.t * 0.6);
      for (let i = 0; i < 12; i++) { ctx.rotate(TAU / 12); const rg = ctx.createLinearGradient(0, 0, 0, -120 * z); rg.addColorStop(0, dof.color); rg.addColorStop(1, 'rgba(255,255,255,0)'); ctx.fillStyle = rg; ctx.beginPath(); ctx.moveTo(-6 * z, 0); ctx.lineTo(-16 * z, -120 * z); ctx.lineTo(16 * z, -120 * z); ctx.lineTo(6 * z, 0); ctx.fill(); }
      ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = k * up;
      ctx.drawImage(RCache.glow('rgba(255,250,200,0.9)'), ex - 50 * z, ey - 50 * z, 100 * z, 100 * z);
      Game.icons.drawFit(ctx, 'dofus_hd_' + dof.icon, ex, ey, 56 * z * (0.6 + 0.4 * up));
      // the caption, in a Dofus-style box
      const txt = T('dofus_get', { n: L(dof.name) }); let fs = Math.round(Math.min(34, W / 28)); ctx.font = annFont(fs, 700); let tw = ctx.measureText(txt).width; if (tw > W * 0.84) { fs *= W * 0.84 / tw; tw = W * 0.84; }
      const bw = tw + fs * 1.6, bh = fs * 2.2, bx = W / 2 - bw / 2, by = H * 0.8;
      ctx.globalAlpha = Math.min(1, Math.max(0, (c.t - 0.6) / 0.3)) * k;
      annPanel(ctx, bx, by, bw, bh, Game.ui, performance.now() / 1000);
      ctx.textAlign = 'center'; annLine(ctx, txt, W / 2, by + bh / 2, fs, ANN.plate);   // (0.95: Cinzel; 0.98.2: the victory's gold, as every central message)
    }
    ctx.restore();
  },
  // 0.68: the treasure: a spotlight, the Coffre Animé coming out of the ground on the cross, the Chouque's ghost (client
  // monster 1124, see-through) turning around the character in an aura like the level 100 / 200 ones (a glowing ring
  // under him, motes rising, a halo), and his words in a bubble
  drawTreasure(ctx, W, H, c, z, k) {
    const P = this.player, D = c.data, scr = (x, y) => [(x - this.cam.x) * z + W / 2, (y - this.cam.y) * z + H / 2], [px, py] = scr(P.x, P.y);
    const g = ctx.createRadialGradient(px, py - 40 * z, 120 * z, px, py - 40 * z, 420 * z); g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, 'rgba(5,0,20,' + (0.68 * k) + ')');
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    const cs = MobSheets.c[(this.C.monsters.coffre_anime || {}).sprite], [cx, cy] = scr(D.x + 75, D.y + 10);   // (beside the character standing on the cross)
    if (cs) {
      const up = Math.min(1, c.t / 0.7), an = cs.has('appearR') && c.t < cs.duration('appearR') ? 'appearR' : 'staticR';
      ctx.globalAlpha = k; ctx.drawImage(RCache.glow('rgba(255,215,90,0.85)'), cx - 100 * z, cy - 130 * z, 200 * z, 200 * z);
      cs.draw(ctx, cs.frameAt(an, c.t, an !== 'appearR'), cx, cy + (1 - up) * 30 * z, ES * z * 1.25, false);
    }
    const G = this.C.tmap.ghost || {}, gs = MobSheets.c[G.sprite], arr = Math.min(1, Math.max(0, (c.t - 0.9) / 0.6));
    if (gs && arr > 0) {
      const a = c.t * 1.3, gx = P.x + Math.cos(a) * 120, gy = P.y + Math.sin(a) * 52 - 18 + Math.sin(c.t * 4) * 6, [sx, sy] = scr(gx, gy), front = Math.sin(a) > 0, hov = 26 * z;
      ctx.globalAlpha = 0.5 * arr * k; ctx.drawImage(RCache.glow('rgba(110,220,255,0.9)'), sx - 46 * z, sy - 14 * z, 92 * z, 28 * z);
      ctx.strokeStyle = 'rgba(170,240,255,' + (0.7 * arr * k) + ')'; ctx.lineWidth = 2 * z; ctx.beginPath(); ctx.ellipse(sx, sy, (34 + 4 * Math.sin(c.t * 5)) * z, 12 * z, 0, 0, TAU); ctx.stroke();
      for (let i = 0; i < 8; i++) {
        const q = (c.t * 0.8 + i / 8) % 1, mx = sx + Math.cos(i * 2.4 + c.t) * 26 * z, my = sy - q * 110 * z, w = (3 + 2 * Math.sin(q * Math.PI)) * z;
        ctx.globalAlpha = 0.8 * Math.sin(q * Math.PI) * arr * k; ctx.drawImage(RCache.glow(i % 2 ? 'rgba(200,150,255,0.95)' : 'rgba(140,240,255,0.95)'), mx - w * 2, my - w * 2, w * 4, w * 4);
      }
      ctx.globalAlpha = 0.45 * arr * k; ctx.drawImage(RCache.glow('rgba(150,230,255,0.9)'), sx - 60 * z, sy - hov - 110 * z, 120 * z, 120 * z);
      const gf = gs.frameAt('walkR', c.t, true), gz = ES * z * 1.6;   // (see-through, bluish, flickering a little)
      ctx.globalAlpha = (0.42 + 0.08 * Math.sin(c.t * 9)) * arr * k; gs.draw(ctx, gf, sx, sy - hov, gz, !front);
      ctx.globalAlpha = 0.5 * arr * k; gs.draw(ctx, gf, sx, sy - hov, gz, !front, tintedSheet(gs, '#7fe8ff'));
      const n = Math.floor((c.t - 1.4) / TM_SAY), line = c.t > 1.4 && D.lines[Math.min(D.lines.length - 1, n)];
      if (line) {
        const fs = Math.round(Math.max(14, Math.min(22, W / 60))), fN = fs + 'px Dofus, Verdana', fB = 'bold ' + fs + 'px DofusBold, Verdana';
        const rows = richWrap(ctx, L(line), Math.min(W * 0.5, 460), fN, fB), bw = Math.max(...rows.map(r => r.w)) + fs * 1.4, bh = rows.length * fs * 1.25 + fs;
        const bx = clamp(sx - bw / 2, 8, W - bw - 8), by = clamp(sy - hov - 150 * z - bh, 30, H - bh - 8), pop = Math.min(1, (c.t - 1.4 - Math.min(D.lines.length - 1, n) * TM_SAY) / 0.15), tx = clamp(sx, bx + 20, bx + bw - 20);
        ctx.globalAlpha = k * pop; ctx.fillStyle = 'rgba(245,252,255,0.95)'; ctx.strokeStyle = '#3a6a8a'; ctx.lineWidth = 3;
        roundRectPath(ctx, bx, by, bw, bh, 12); ctx.fill(); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(tx - 10, by + bh); ctx.lineTo(tx + 10, by + bh); ctx.lineTo(tx, by + bh + 14); ctx.closePath(); ctx.fill();
        ctx.textAlign = 'left'; ctx.textBaseline = 'top';
        rows.forEach((r, i) => { let x = bx + (bw - r.w) / 2; for (const s of r.segs) { ctx.font = s.b ? fB : fN; ctx.fillStyle = s.b ? '#0a2236' : '#1e3a52'; ctx.fillText(s.t, x, by + fs * 0.5 + i * fs * 1.25); x += s.w; } });
        ctx.font = 'bold ' + Math.round(fs * 0.75) + 'px DofusBold, Verdana'; ctx.fillStyle = '#bfe8ff'; ctx.textAlign = 'left'; ctx.textBaseline = 'bottom'; ctx.fillText(L(G.name || {}), bx + 10, by - 3);
      }
    }
    ctx.globalAlpha = 1;
  },
  // 0.85 (a countdown worthy of Dofus Retro): the numbers on the client's turn-timer ring that empties in its 0.8 s,
  // a puff of gold sparks when each lands, then GO! in the green of the logo's leaves. 0.95: the numbers and GO! in the
  // announcements' carved Cinzel (juice.js annGlyph), struck in like seals. Same timing as before (3 x 0.8 s, then GO! to
  // the end of the cine): the run starts as it did.
  drawCountdown(ctx, W, H, c) {
    const n = Math.min(3, Math.floor(c.t / 0.8)), u = (c.t - n * 0.8) / (n < 3 ? 0.8 : c.dur - 2.4), S = Math.min(W, H), cx = W / 2, cy = H * 0.42;
    ctx.fillStyle = `rgba(2,20,12,${n < 3 ? 0.3 * Math.min(1, c.t / 0.2) : 0.3 * Math.max(0, 1 - u * 3)})`; ctx.fillRect(0, 0, W, H);   // (0.98: a deep green veil)
    const vg = ctx.createRadialGradient(cx, cy, S * 0.1, cx, cy, Math.max(W, H) * 0.7); vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, `rgba(0,22,12,${n < 3 ? 0.4 : 0.4 * Math.max(0, 1 - u * 3)})`);
    ctx.fillStyle = vg; ctx.fillRect(0, 0, W, H);
    const sparks = (k, R, col, seed) => {   // gold motes thrown out when a number lands
      for (let i = 0; i < 16; i++) {
        const an = i / 16 * TAU + seed, d = R * (0.7 + 1.3 * k) * (0.8 + 0.4 * ((i * 37) % 10) / 10), r = S * 0.008 * (1 - k);
        if (r <= 0) continue; ctx.globalAlpha = (1 - k) * 0.95; ctx.fillStyle = i % 3 ? col : '#f8ffd8';
        ctx.beginPath(); for (let q = 0; q < 8; q++) { const rr = q % 2 ? r * 0.35 : r * 1.4, aa = q / 8 * TAU; ctx.lineTo(cx + Math.cos(an) * d + Math.cos(aa) * rr, cy + Math.sin(an) * d * 0.8 + Math.sin(aa) * rr); } ctx.fill();
      }
      ctx.globalAlpha = 1;
    };
    if (n < 3) {
      const R = S * 0.185, a = Math.min(1, u / 0.05) * Math.min(1, (1 - u) / 0.14);
      // 0.95 (a badass ring in the Dofus style, with the font and the logo): the turn-timer medallion (cdMedal)
      const pulse = u >= 0.12 && u < 0.27 ? 1 + 0.06 * Math.sin((u - 0.12) / 0.15 * Math.PI) : 1;
      ctx.save(); ctx.globalAlpha = a; ctx.translate(cx, cy); ctx.scale(pulse, pulse); cdMedal(ctx, R, u, n, c.t); ctx.restore();
      // 0.95: the number is struck onto the disc like a seal: it drops from big (accelerating) and hits at u 0.12 — a flash
      // in the disc, a shock ring, gold sparks, a short shake —, breathes, then sinks into the disc as the next one comes.
      // Its metal heats up as the count goes down (gold, amber, ember red), in Cinzel like the other announcements
      const HIT = 0.12, hk = u < HIT ? 0 : (u - HIT), out = u > 0.84 ? (u - 0.84) / 0.16 : 0;
      const sc = u < HIT ? 2.5 - 1.5 * Math.pow(u / HIT, 2) : 1 + 0.07 * Math.max(0, 1 - hk / 0.1) * Math.sin(hk / 0.1 * Math.PI) + 0.012 * Math.sin(c.t * 7);
      const shk = hk > 0 && hk < 0.1 ? (1 - hk / 0.1) * S * 0.006 : 0;
      ctx.save(); if (shk) ctx.translate(Math.sin(c.t * 97) * shk, Math.cos(c.t * 83) * shk);
      if (hk > 0 && hk < 0.3) {   // the impact in the disc: a flash and a shock ring
        const q = hk / 0.3; ctx.save(); ctx.globalCompositeOperation = 'lighter';
        ctx.globalAlpha = (1 - q) * 0.8; const fr = R * (0.9 + 0.5 * q); ctx.drawImage(RCache.glow(n === 2 ? 'rgba(245,200,70,0.95)' : n === 1 ? 'rgba(220,240,90,0.95)' : 'rgba(180,245,90,0.95)'), cx - fr, cy - fr, fr * 2, fr * 2);
        ctx.globalAlpha = (1 - q); ctx.strokeStyle = '#f4ffd0'; ctx.lineWidth = S * 0.012 * (1 - q) + 1; ctx.beginPath(); ctx.ellipse(cx, cy, R * (0.95 + 0.9 * q), R * (0.95 + 0.9 * q) * 0.92, 0, 0, TAU); ctx.stroke();
        ctx.restore();
      }
      ctx.globalAlpha = Math.min(1, u / 0.05) * (1 - out); ctx.translate(cx, cy); ctx.scale(sc * (1 - out * 0.3), sc * (1 - out * 0.3)); ctx.textAlign = 'center';
      // (0.95: it sat a little high: the figure's ink — and half its carved depth, annCarve — centred on the disc)
      const fs = Math.round(R * 1.5), ink = annInk(String(3 - n), fs), gx = ink.dx, gy0 = ink.dy - fs * 0.0325;
      annGlyph(ctx, String(3 - n), gx, gy0, fs, n === 2 ? ANN.retro : ANN.cream);   // (0.98: cream letters in a lime halo, the 1 in Dofus Retro's gold)
      if (hk > 0.05 && hk < 0.4) annSheen(ctx, String(3 - n), gx, gy0, fs, -fs * 0.6 + fs * 1.2 * (hk - 0.05) / 0.35, 0.7);
      ctx.restore();
      if (u >= HIT) sparks(Math.min(1, (u - HIT) / 0.45), R * 1.15, CD_HEAT[n], n * 1.3);
      return;
    }
    // GO! (0.91: something with punch instead of the client's swords picture): two vector swords whirl in from
    // both sides with motion trails and clash into an X — white flash, an impact star, two shock waves, a spray of
    // sparks, two light slashes across the whole screen along the blades, a shake — then a glint runs down the crossed
    // blades while GO! slams in. 0.95: the medallion bursts first, burning leaves (the logo's) fly out of the clash and
    // GO! in white-hot forged gold Cinzel drops in (below)
    const a = Math.min(1, u / 0.04) * Math.min(1, (1 - u) / 0.3), HIT = 0.11, hk = u < HIT ? 0 : (u - HIT) / (1 - HIT);
    const L = S * 0.44, X = cx, Y = cy - S * 0.1, TH = 0.66, D = L * 0.4;
    const shake = u >= HIT && u < HIT + 0.2 ? (1 - (u - HIT) / 0.2) * S * 0.012 : 0;
    ctx.save(); if (shake) ctx.translate(Math.sin(c.t * 91) * shake, Math.cos(c.t * 77) * shake);
    // the rays turning behind (brighter once the blades meet)
    ctx.save(); ctx.translate(cx, cy); ctx.rotate(c.t * 0.6); ctx.globalAlpha = (u < HIT ? 0.25 : 0.45) * a;
    for (let i = 0; i < 16; i++) {
      ctx.rotate(TAU / 16); const g = ctx.createLinearGradient(0, 0, 0, -S * 0.62); g.addColorStop(0, i % 2 ? 'rgba(255,230,140,0.9)' : 'rgba(200,245,110,0.9)'); g.addColorStop(1, 'rgba(200,245,110,0)');
      ctx.fillStyle = g; ctx.beginPath(); ctx.moveTo(-S * 0.014, 0); ctx.lineTo(S * 0.014, 0); ctx.lineTo(S * 0.05, -S * 0.62); ctx.lineTo(-S * 0.05, -S * 0.62); ctx.closePath(); ctx.fill();
    }
    ctx.restore();
    // 0.95: the medallion of the '1' bursts as GO! begins: a flash where it was, its bezel's shards and blades flung out
    // spinning, an ember ring racing outwards
    if (u < 0.4) {
      const k = u / 0.4, R = S * 0.185, ke = 1 - Math.pow(1 - k, 2);
      ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha = (1 - k) * 0.9; const fr = R * (1.2 + 1.6 * ke); ctx.drawImage(RCache.glow('rgba(170,240,80,0.95)'), cx - fr, cy - fr, fr * 2, fr * 2);
      ctx.globalAlpha = (1 - k); ctx.strokeStyle = '#c8f060'; ctx.lineWidth = S * 0.01 * (1 - k) + 1; ctx.beginPath(); ctx.ellipse(cx, cy, R * (1 + 3 * ke), R * (1 + 3 * ke) * 0.9, 0, 0, TAU); ctx.stroke(); ctx.restore();
      for (let i = 0; i < 14; i++) {
        const an = i / 14 * TAU + 0.2, d = R * (0.9 + 2.6 * ke * (0.7 + 0.5 * ((i * 41) % 7) / 7)), x = cx + Math.cos(an) * d, y = cy + Math.sin(an) * d + S * 0.25 * k * k, w = R * (i % 2 ? 0.24 : 0.16);
        ctx.save(); ctx.globalAlpha = a * (1 - k) * 0.7; ctx.translate(x, y); ctx.rotate(an + k * (i % 2 ? 7 : -9)); ctx.scale(1, 0.6 + 0.4 * Math.abs(Math.cos(k * 8 + i)));
        cdLeaf(ctx, w * 2.4, CD_LEAVES[i % CD_LEAVES.length]); ctx.restore();   // (0.98: the wreath's leaves flung out)
      }
    }
    // where each sword is at the moment q (0 = far away, 1 = crossed): its guard and its angle
    const pose = (side, q) => {
      const e = 1 - Math.pow(1 - Math.max(0, Math.min(1, q)), 3), th = side * TH + side * (1 - e) * -4.2, ex = X - side * W * 0.62 * (1 - e), ey = Y - S * 0.35 * (1 - e);
      return [ex - Math.sin(th) * D, ey + Math.cos(th) * D, th];   // (the guard sits D below the crossing point, along the blade)
    };
    const swordAt = (side, q, al, glint) => { const [x, y, th] = pose(side, q); ctx.save(); ctx.globalAlpha = al; ctx.translate(x, y); ctx.rotate(th); goSword(ctx, L, glint, side); ctx.restore(); };
    const q = u / HIT;
    if (u < HIT) {   // flying in: the trails, then the swords
      ctx.save(); ctx.globalCompositeOperation = 'lighter';
      for (const side of [-1, 1]) for (let i = 4; i >= 1; i--) if (q - i * 0.09 > 0) swordAt(side, q - i * 0.09, a * 0.16 * (5 - i) / 4, -1);
      ctx.restore();
      for (const side of [-1, 1]) swordAt(side, q, a, -1);
    } else {
      // the glow behind the crossing
      const gl = RCache.glow('rgba(220,245,130,0.9)'), gr = S * (0.32 + 0.04 * Math.sin(c.t * 8)) * (1 + 0.6 * Math.max(0, 1 - hk * 5));
      ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha = a * 0.75; ctx.drawImage(gl, X - gr, Y - gr, gr * 2, gr * 2); ctx.restore();
      // the two slashes across the screen, along the blades
      if (hk < 0.3) for (const side of [-1, 1]) {
        const k = hk / 0.3, len = Math.hypot(W, H) * Math.min(1, k * 4), w = S * 0.02 * (1 - k), th = side * TH;
        ctx.save(); ctx.translate(X, Y); ctx.rotate(th); ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha = a * (1 - k);
        const sg = ctx.createLinearGradient(-w, 0, w, 0); sg.addColorStop(0, 'rgba(255,255,255,0)'); sg.addColorStop(0.5, 'rgba(255,250,220,1)'); sg.addColorStop(1, 'rgba(255,255,255,0)');
        ctx.fillStyle = sg; ctx.beginPath(); ctx.moveTo(0, -len / 2); ctx.lineTo(w, 0); ctx.lineTo(0, len / 2); ctx.lineTo(-w, 0); ctx.closePath(); ctx.fill(); ctx.restore();
      }
      const glint = (hk * 1.6) % 1;   // a light running down the blades
      for (const side of [-1, 1]) swordAt(side, 1, a, hk < 0.62 ? glint : -1);
      // the impact: a star of light, two shock waves, sparks
      if (hk < 0.35) {
        const k = hk / 0.35, r = S * (0.06 + 0.22 * Math.sqrt(k));
        ctx.save(); ctx.translate(X, Y); ctx.rotate(c.t * 2); ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha = a * (1 - k);
        ctx.fillStyle = '#fff6d0'; ctx.beginPath(); for (let i = 0; i < 24; i++) { const rr = i % 2 ? r * 0.18 : r * (i % 4 ? 0.7 : 1), an = i / 24 * TAU; ctx.lineTo(Math.cos(an) * rr, Math.sin(an) * rr); } ctx.closePath(); ctx.fill(); ctx.restore();
      }
      for (const [sp, col, wd] of [[1, '#f4ffd0', 0.016], [0.6, '#a8e63a', 0.01]]) {
        const k = Math.min(1, hk * 2.4 * sp); if (k >= 1) continue;
        ctx.globalAlpha = a * (1 - k); ctx.lineWidth = S * wd * (1 - k) + 1; ctx.strokeStyle = col; ctx.beginPath(); ctx.ellipse(X, Y, S * (0.05 + 0.6 * k), S * (0.04 + 0.42 * k), 0, 0, TAU); ctx.stroke();
      }
      if (hk < 0.5) {
        const k = hk / 0.5; ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.lineCap = 'round';
        for (let i = 0; i < 30; i++) {
          const an = i / 30 * TAU + (i % 3) * 0.13, sp = 0.45 + ((i * 53) % 17) / 17 * 0.75, d0 = S * 0.05 + S * 0.42 * sp * Math.sqrt(k), d1 = d0 + S * 0.07 * (1 - k) * sp, fall = S * 0.08 * k * k * sp;
          ctx.globalAlpha = a * (1 - k); ctx.strokeStyle = i % 4 ? (i % 3 ? '#c8f060' : '#ffd35a') : '#ffffff'; ctx.lineWidth = S * 0.006 * (1 - k * 0.7);
          ctx.beginPath(); ctx.moveTo(X + Math.cos(an) * d0, Y + Math.sin(an) * d0 + fall); ctx.lineTo(X + Math.cos(an) * d1, Y + Math.sin(an) * d1 + fall); ctx.stroke();
        }
        ctx.restore();
      }
      if (hk < 0.12) { ctx.globalAlpha = (1 - hk / 0.12) * 0.7; ctx.fillStyle = '#fff8e2'; ctx.fillRect(-W, -H, W * 3, H * 3); }   // the flash
      // GO! (0.95: badass, in the logo's and the font's spirit): forged gold, white-hot, the end of the count's heat
      // (gold, amber, ember, then white-hot). It drops in at the clash with a zoom trail and hits: a dark heat-haze behind
      // it, a fire aura licking up the letters, burning leaves
      // (the logo's) flung out of the clash, a shudder, sheens; at the end the letters stretch out and burn away to embers
      const gy = cy + S * 0.21, go = T('cd_go'), out = Math.max(0, (u - 0.78) / 0.22), A = annLayout(ctx, go, S * 0.22, 0.05 + 0.1 * out, W * 0.82), fs = A.fs, goDy = annInk(go, fs).dy - fs * 0.0325;   // (0.95: the word's ink centred on gy)
      const lk = clamp(hk / 0.09, 0, 1), drop = lk < 1 ? 1.9 - 0.9 * lk * lk : 1, land = hk - 0.09, settle = land > 0 ? 1 + 0.1 * Math.exp(-land * 30) * Math.cos(land * 60) : drop;
      const glowF = RCache.glow('rgba(170,240,80,0.95)'), glowW = RCache.glow('rgba(255,248,220,0.95)');   // (0.98: lime, the verdant set)
      // leaves flying out of the clash
      if (hk < 0.9) {
        const k = hk / 0.9;
        for (let i = 0; i < 18; i++) {
          const an = i / 18 * TAU + Math.sin(i * 3.7) * 0.3, sp = 0.55 + ((i * 29) % 11) / 11 * 0.7, d = S * 0.52 * sp * (1 - Math.pow(1 - k, 2)), x = X + Math.cos(an) * d, y = Y + Math.sin(an) * d * 0.75 + S * 0.3 * k * k * sp;
          ctx.save(); ctx.globalAlpha = a * Math.min(1, (1 - k) * 2.2) * 0.7; ctx.translate(x, y); ctx.rotate(an + k * (5 + i % 4) * (i % 2 ? 1 : -1)); ctx.scale(1, 0.55 + 0.45 * Math.abs(Math.cos(k * 9 + i)));
          const s = S * (0.03 + 0.022 * ((i * 17) % 5) / 5); ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha *= 0.4; ctx.drawImage(glowF, -s, -s, s * 2, s * 2); ctx.restore();
          cdLeaf(ctx, s, CD_LEAVES[i % CD_LEAVES.length]); ctx.restore();
        }
      }
      if (land > 0) {
        // a dark haze behind the word (it reads on any ground and the glow shows); 0.98: the two blades of light out of its
        // sides gone, the screen's chromatic aberration (Run.chromaK) instead
        const k = clamp(land / 0.5, 0, 1), wa = a * (1 - k * 0.7);
        ctx.save(); ctx.globalAlpha = a * 0.75; ctx.drawImage(RCache.glow('rgba(2,26,12,0.9)'), cx - A.tw * 0.85, gy - fs * 0.95, A.tw * 1.7, fs * 1.9);
        ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha = wa * 0.7; ctx.drawImage(glowF, cx - A.tw * 0.7, gy - fs * 0.6, A.tw * 1.4, fs * 1.2); ctx.restore();
        // the glow rising off the letters (0.98: lime; was fire)
        ctx.save(); ctx.globalCompositeOperation = 'lighter';
        const nfl = Math.max(8, Math.round(A.tw / (fs * 0.28))), surge = 1 + 1.2 * Math.max(0, 1 - land / 0.35);
        for (let i = 0; i < nfl; i++) {
          const fx = cx - A.tw / 2 + (i + 0.5) / nfl * A.tw + Math.sin(c.t * 3 + i * 1.7) * fs * 0.05, fl = 0.5 + 0.5 * Math.abs(Math.sin(c.t * (6 + (i % 4)) + i * 1.9)), hh = fs * (0.5 + 0.5 * ((i * 37) % 7) / 7) * fl * surge * (1 - out * 0.6), ww = fs * 0.36;
          ctx.globalAlpha = a * (0.32 + 0.2 * ((i * 13) % 5) / 5); ctx.drawImage(glowF, fx - ww / 2, gy - fs * 0.05 - hh, ww, hh * 1.25);
        }
        ctx.restore();
      }
      // the zoom trail while it falls: fading copies, bigger and further back
      ctx.save(); ctx.textAlign = 'center';
      if (lk < 1) { ctx.globalCompositeOperation = 'lighter'; for (let j = 3; j >= 1; j--) { const sc = drop * (1 + j * 0.22); ctx.save(); ctx.globalAlpha = a * lk * 0.18 * (4 - j) / 3; ctx.translate(cx, gy); ctx.scale(sc, sc); ctx.font = annFont(fs); ctx.textBaseline = 'middle'; ctx.fillStyle = '#e8f8a0'; A.chars.forEach((ch, i) => ctx.fillText(ch, A.xs[i], goDy)); ctx.restore(); } ctx.globalCompositeOperation = 'source-over'; }
      // the letters: a shudder after the hit, then stretching out and burning away at the end
      const shud = land > 0 && land < 0.25 ? (1 - land / 0.25) * fs * 0.025 : 0;
      ctx.globalAlpha = a * Math.min(1, hk / 0.03 + 0.2) * (1 - out * out);
      ctx.translate(cx + (shud ? Math.sin(c.t * 120) * shud : 0), gy); ctx.scale(settle * (1 + out * 0.22), settle * (1 - out * 0.08));
      A.chars.forEach((ch, i) => { if (ch !== ' ') annGlyph(ctx, ch, A.xs[i], goDy, fs, ANN.retro); });   // (0.98: Dofus Retro's gold in a lime halo)
      if (land > 0) { const at = ((land * 1.5) % 1.2 - 0.1) * (A.tw + fs * 2) - A.tw / 2 - fs; A.chars.forEach((ch, i) => annSheen(ctx, ch, A.xs[i], goDy, fs, at, 0.9)); }
      ctx.restore();
      // fireflies: thrown up at the hit, then rising off the letters as they fade
      ctx.save(); ctx.globalCompositeOperation = 'lighter';
      for (let i = 0; i < 26; i++) {
        const q = ((c.t * (0.6 + 0.5 * ((i * 7) % 5) / 5)) + i / 26) % 1, ex = cx + ((i * 61) % 97 / 97 - 0.5) * A.tw * 1.2 + Math.sin(c.t * 2 + i) * fs * 0.1, ey = gy + fs * 0.3 - q * fs * (1.4 + out * 1.6), r = fs * (0.04 + 0.05 * ((i * 11) % 7) / 7);
        ctx.globalAlpha = a * Math.sin(q * Math.PI) * (land > 0 ? 0.85 : 0) * (0.5 + out); ctx.drawImage(glowF, ex - r * 2, ey - r * 2, r * 4, r * 4);
      }
      ctx.restore();
      if (hk < 0.5) sparks(hk / 0.5, S * 0.2, '#d8f870', 0.4);
    }
    ctx.restore();
    ctx.globalAlpha = 1;
  },
  // Dark Vlad's fall, over the world: a red vignette, a red glow on him, the cracks of light growing from his feet, red
  // lightning striking around, the red flash, then the screen goes dark for his words
  drawVladFall(ctx, W, H, c, z, k) {
    const m = c.data.m, D = c.data, sx = (m.x - this.cam.x) * z + W / 2, sy = (m.y - this.cam.y) * z + H / 2;
    const g = ctx.createRadialGradient(sx, sy - 40 * z, 120 * z, sx, sy - 40 * z, Math.max(W, H) * 0.75);
    g.addColorStop(0, 'rgba(40,0,0,0)'); g.addColorStop(1, `rgba(40,0,0,${0.82 * Math.min(1, c.t / 0.5)})`); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    ctx.globalCompositeOperation = 'lighter';
    const pulse = 0.55 + 0.25 * Math.sin(c.t * 9);
    ctx.globalAlpha = pulse * Math.min(1, c.t / 0.4); ctx.drawImage(RCache.glow('rgba(255,40,20,0.9)'), sx - 110 * z, sy - 150 * z, 220 * z, 220 * z);
    const grow = clamp((c.t - 0.3) / 2.6, 0, 1);
    if (D.cracks) for (const pts of D.cracks) {
      const n = pts.length - 1, upto = grow * n;
      ctx.beginPath(); ctx.moveTo(sx, sy);
      for (let i = 1; i <= Math.ceil(upto); i++) { const f = Math.min(1, upto - (i - 1)), [x0, y0] = pts[i - 1], [x1, y1] = pts[i]; ctx.lineTo(sx + (x0 + (x1 - x0) * f) * z, sy + (y0 + (y1 - y0) * f) * z); }
      ctx.globalAlpha = 0.5 * k; ctx.strokeStyle = '#ff3a12'; ctx.lineWidth = 9 * z; ctx.lineJoin = 'round'; ctx.lineCap = 'round'; ctx.stroke();
      ctx.globalAlpha = 0.95 * k; ctx.strokeStyle = '#ffd8a0'; ctx.lineWidth = 2.6 * z; ctx.stroke();
    }
    for (const b of D.bolts || []) {
      const a = (c.t - b.t0) / 0.35; if (a < 0 || a > 1) continue;
      let s = b.seed; const rnd = () => ((s = (s * 16807) % 2147483647) / 2147483647);
      const bx = (b.x - this.cam.x) * z + W / 2, by = (b.y - this.cam.y) * z + H / 2;
      ctx.beginPath(); let x = bx + (rnd() - 0.5) * 160 * z; ctx.moveTo(x, -10);
      for (let y = -10; y < by; y += 34 * z) { x += (rnd() - 0.5) * 46 * z + (bx - x) * 0.18; ctx.lineTo(x, y); }
      ctx.lineTo(bx, by);
      ctx.globalAlpha = (1 - a) * k; ctx.strokeStyle = '#ff2a1a'; ctx.lineWidth = 10 * z; ctx.stroke(); ctx.strokeStyle = '#fff0e8'; ctx.lineWidth = 3 * z; ctx.stroke();
      ctx.globalAlpha = (1 - a) * 0.8; ctx.drawImage(RCache.glow('rgba(255,60,30,0.9)'), bx - 70 * z, by - 40 * z, 140 * z, 80 * z);
      ctx.globalAlpha = (1 - a) * 0.16; ctx.fillStyle = '#ff2a1a'; ctx.fillRect(0, 0, W, H);
    }
    ctx.globalCompositeOperation = 'source-over';
    if (c.t > 3.9) { const f = clamp(1 - (c.t - 3.9) / 0.7, 0, 1); ctx.globalAlpha = f * 0.85; ctx.fillStyle = '#ffd8c8'; ctx.fillRect(0, 0, W, H); }
    ctx.globalAlpha = clamp((c.t - (c.dur - 1.1)) / 1.1, 0, 1) * 0.88; ctx.fillStyle = '#100000'; ctx.fillRect(0, 0, W, H);
  },
  // ------------------------------------------------ the Tofu Mutant / the time portal
  doorTime() {
    if (this.portalRun) return false;   // the usual door (drawn as a time portal)
    this.doorDone = true; this.spawnMutant(); return true;
  },
  // 0.95: from the zone after the 10th (C.jorbak.from, its place in C.maps), Jorbak comes instead of the Tofuzmo
  // (the same slot: this.mutant — its bar, its escape, its arrow): he keeps his distance, throws the player away when he is
  // caught up with (klepto), gives a 15 % bonus and, 1 time in 2 (C.jorbak.tmap), a treasure map (the only source of them now)
  spawnMutant() {
    const J = this.C.jorbak, jor = !!(J && this.C.monsters.jorbak && this.mapPos >= J.from);
    const [x, y] = this.spawnPos(), m = this.spawnMob(jor ? 'jorbak' : 'tofu_mutant', x, y, { force: true, noArchi: true }); if (!m) return;
    m.hp = m.maxHp = (jor ? J.hp : this.C.mutant.hp) * this.aidHp(); m.mutant = true; m.speed = m.def.speed * (this.RUN.mobSpeed || 1); this.mutant = m;
    const msg = T(jor ? 'jorbak_appears' : 'mutant_appears', { hp: fmtNum(Math.round(m.maxHp)) });   // (0.96: its real life, the beginners' help included: the Tofuzmo said 1000 with 700)
    this.announce(L(m.def.name), msg, '#9cff6a'); Audio2.sfx('EVENT', 0.8); Audio2.play(jor ? 'son_attack' : 'tofu_king', 0.7);
    this.fxAt(1100, x, y, { scale: 1.2 });
  },
  // Kleptomanie psychopathe: the player is thrown away from Jorbak like a monster by Libération (its fx, its sound)
  klepto(m, ux, uy) {
    const J = this.C.jorbak, P = this.player; m.kleptoT = J.cd; m.atkAnimT = 0;
    P.push = { x: ux * J.push, y: uy * J.push * 0.8 };
    this.fxAt(J.fx, P.x, P.y - 20, {}); Audio2.play(J.snd, 0.7); this.shake(5);
    this.text(m.x, m.y - 80, L(J.spell) + ' !', '#ffcf6a', 15);
  },
  // roam: the Tofu Mutant runs to random spots all over the map; circle: the Coffre Animé runs round its spot
  specialMove(m, dt) {
    if (m.def.beh === 'keep') {   // Jorbak: between keep[0] and keep[1] from the player, strafing round him; under `near`, klepto
      const J = this.C.jorbak, P = this.player, dx = P.x - m.x, dy = P.y - m.y, d = Math.hypot(dx, dy) || 1, [a, b] = J.keep, sd = m.side || (m.side = Math.random() < 0.5 ? -1 : 1);
      m.kleptoT = (m.kleptoT || 0) - dt;
      if (d < J.near + m.r && m.kleptoT <= 0 && !P.dead) this.klepto(m, dx / d, dy / d);
      if (d > b) return [dx / d, dy / d];   // left behind: he comes back
      if (d < a) { const k = Math.min(1, (a - d) / (a * 0.5)); return [-dx / d * k - dy / d * sd * 0.45, -dy / d * k + dx / d * sd * 0.45]; }   // too close: backs off, sideways a little (never cornered for long)
      return [-dy / d * sd * 0.35, dx / d * sd * 0.35];   // in his band: strafes slowly
    }
    if (m.def.beh === 'circle') {
      // 0.84 (it jerked): it chased a point moving round the ellipse at an angular speed, slower than the chest on the
      // flat sides: it caught it, overshot, turned back (and flipped) every few frames. Now the point moves at the chest's
      // own speed along the ellipse (arc length) and the chest takes the exact step to it (catching up after a push)
      const H = m.home || (m.home = { x: m.x, y: m.y }), R_ = this.C.coffre.radius, a0 = m.ca || 0;
      m.ca = a0 + dt * m.speed / Math.max(1, R_ * Math.hypot(Math.sin(a0), 0.6 * Math.cos(a0)));
      const tx = H.x + Math.cos(m.ca) * R_, ty = H.y + Math.sin(m.ca) * R_ * 0.6, dx = tx - m.x, dy = ty - m.y, d = Math.hypot(dx, dy);
      const k = 1 / Math.max(1e-6, dt * m.speed), n = Math.hypot(dx * k, dy * k);
      return n > 1.6 ? [dx * k / n * 1.6, dy * k / n * 1.6] : [dx * k, dy * k];
    }
    const b = this.bounds;
    if (!m.goal || Math.hypot(m.goal.x - m.x, m.goal.y - m.y) < 40 || (m.goalT -= dt) <= 0) {
      // (0.36: its runs stay around the player, never so far that it would be put back elsewhere)
      const P = this.player, W = 900, H = 520;
      for (let k = 0; k < 20; k++) { const x = clamp(P.x + rand(-W, W), b.x0 + 80, b.x1 - 80), y = clamp(P.y + rand(-H, H), b.y0 + 80, b.y1 - 80); if (!this.isWater(x, y)) { m.goal = { x, y }; break; } }
      m.goalT = 6;
    }
    const dx = m.goal.x - m.x, dy = m.goal.y - m.y, d = Math.hypot(dx, dy) || 1; return [dx / d, dy / d];
  },
  specialDeath(m) {
    const C = this.C;
    if (m.def.id === 'tofu_mutant') {
      Prog.add('mutants');
      const b = pick(C.totBuffs); this.totBuff = b; this.recompute(); this.mutant = null;
      this.announce(T('down_t', { n: L(m.def.name) }), T('mutant_down', { b: L(b.name) }), '#9cff6a', { center: true }); Audio2.ui('level', 0.9);
      const S = Store.data; S.mutants = (S.mutants || 0) + 1; Store.save();
    } else if (m.def.id === 'jorbak') {   // 0.95: his bonus (+15 %, it takes the run's bonus slot: never on top of another) and a map, C.jorbak.tmap (50 %), while one is left to find
      const J = C.jorbak, b = Object.assign({}, pick(C.totBuffs), { v: J.buff }); this.totBuff = b; this.recompute(); this.mutant = null;
      const msg = T('jorbak_down', { b: L(b.name), p: Math.round(J.buff * 100) }); this.announce(T('down_t', { n: L(m.def.name) }), msg, '#9cff6a', { center: true }); Audio2.ui('level', 0.9);
      if (this.tmapFree().length && Math.random() < J.tmap) this.dropPickup('tmap', m.x, m.y, 1);
    } else if (m.def.id === 'coffre_anime' && m.trapChest) {   // 0.40: the Minotoror trapdoor's blue chest: a relic
      const pool = C.relics.filter(r => !this.relics.includes(r)); Audio2.play('coffre', 0.8);
      if (pool.length) this.gainRelic(pick(pool).id); else { this.kamas += 500; this.text(m.x, m.y - 60, '+500 K', '#ffd700', 20); }
      Prog.add('trapChests');
    } else if (m.def.id === 'coffre_anime') {
      Prog.add('coffres');
      let r = Math.random(), got = C.coffre.drops[C.coffre.drops.length - 1][0];
      for (const [k, p] of C.coffre.drops) { if (r < p) { got = k; break; } r -= p; }
      if (got === 'manuel') this.collect({ kind: 'manuel' });
      else { const it = C.coffre.items[got]; this.kamas += it.kamas; this.text(m.x, m.y - 60, '+' + it.kamas + ' K', '#ffd700', 20); this.announce(L(it.name), T('coffre_loot', { n: L(it.name), k: it.kamas }), '#ff7a7a'); }
      Audio2.play('coffre', 0.8); Audio2.blip('coin');
      const S = Store.data; S.coffres = (S.coffres || 0) + 1; Store.save();
    }
  },
  // 0.40 secret: stepping on the trapdoor marked 'E' of the Minotoror zone (C.trap) pauses the run, a blue Coffre Animé
  // pops out of it with a comic fart, and gives a random relic when killed (once per run)
  checkTrap() {
    const K = this.C.trap; if (!K || this.trapDone || this.map.id !== K.map || this.over) return;
    const P = this.player; if (Math.hypot(P.x - K.x, P.y - K.y) > K.r) return;
    this.trapDone = true; this.trapShow = { t0: performance.now(), x: K.x, y: K.y };
    Prog.add('trapFound'); Prog.check(this);   // (0.60: the achievement 'Sous la trappe')
    this.reviveHold = performance.now() + 2200;   // (the run holds while the chest shows off)
    Audio2.ui('door', 0.6); this.shake(4);   // (0.61: 'door' is a UI event, not a pack key: it was a 404)
    setTimeout(() => {
      const cm = this.spawnMob('coffre_anime', K.x + 40, K.y - 10, { force: true, noArchi: true }); if (!cm) return;
      cm.hp = cm.maxHp = K.hp; cm.trapChest = true; cm.tint = '#3a7bff'; cm.home = { x: K.x, y: K.y }; cm.atkAnimT = 0;
      this.fxAt(1100, cm.x, cm.y, { scale: 1.2 });
      [0, 260, 600].forEach((d, i) => setTimeout(() => Audio2.play('pet', 1, [0.85, 1.25, 0.6][i]), d));   // pfffrt, prrt… PRRROUT
      for (let i = 0; i < 24; i++) { const a = rand(TAU), v = rand(30, 120); this.particles.push({ x: cm.x - 20, y: cm.y - 10, vx: Math.cos(a) * v - 40, vy: Math.sin(a) * v * 0.5 - 20, g: -10, t: 0, life: rand(0.8, 1.6), s: rand(10, 20), grow: 1.8, round: 1, c: i % 3 ? '#9ccf4a' : '#c8b04a' }); }
      this.announce(T('trap_found_t'), T('trap_found'), '#7ab8ff', { center: true });
    }, 700);
  },
  maybeCoffre(m) {
    const K = this.C.coffre; if (!K || this.coffreDone || !this.isFinalKill(m) || this.time >= K.t || this.infinite) return;
    this.coffreDone = true;
    this.announce(L(this.C.monsters.coffre_anime.name), T('coffre_appears'), '#ff9a6a');
    this.after(2, () => {   // (0.91: run time)
      const c = this.center, cm = this.spawnMob('coffre_anime', c.x, c.y, { force: true, noArchi: true }); if (!cm) return;
      cm.hp = cm.maxHp = 1; cm.home = { x: c.x, y: c.y }; this.fxAt(1100, c.x, c.y, { scale: 1.4 }); Audio2.play('coffre', 0.7);
    });
  },
  // ------------------------------------------------ treasure maps
  updateEvents(dt) {
    if (this.boosterAt && this.time >= this.boosterAt) this.dropBooster();
    if (!this.gladiaOut && this.C.gladia && this.time >= this.C.gladia.t) this.dropGladia();   // (0.98.3: gspells.js)
    this.checkTrap();
    const P = this.player, TM = this.C.tmap;
    if (this.mutant && !this.mutant.dying && this.time > this.C.mutant.escape) {   // it got away
      const m = this.mutant; m.dying = true; m.dieT = 0; m.silent = true; this.fxAt(1100, m.x, m.y, {}); this.mutant = null; this.chat(T(m.def.id === 'jorbak' ? 'jorbak_escaped' : 'mutant_escaped'), '#9cff6a');
    }
    if (this.mutant && this.mutant.dying) this.mutant = null;
    if (this.tmapDrop && this.time >= this.tmapDrop.t) {
      this.tmapDrop = null;
      for (let k = 0; k < 20; k++) { const a = rand(TAU), x = P.x + Math.cos(a) * 140, y = P.y + Math.sin(a) * 100; if (!this.isWater(x, y)) { this.dropPickup('tmap', clamp(x, this.bounds.x0, this.bounds.x1), clamp(y, this.bounds.y0, this.bounds.y1), 1); break; } }
    }
    const H = this.tmapHere;
    if (H && !H.found && !P.dead) {
      const near = Math.hypot(P.x - H.x, P.y - H.y) < TM.r;
      if (near && !this._tmapSaid) { this._tmapSaid = true; this.chat(T('tmap_here'), '#ffcf3a'); }
      this.tmapDig = near ? this.tmapDig + dt : Math.max(0, this.tmapDig - dt * 2);
      if (near && Math.random() < dt * 8) this.particles.push({ x: H.x + rand(-12, 12), y: H.y, vx: rand(-60, 60), vy: rand(-140, -60), t: 0, life: 0.5, c: pick(['#7a5a34', '#5a4026']), s: 3 });
      if (this.tmapDig >= TM.dig) {   // 0.68: epic — slow motion, then the run stops for the Chouque's ghost and the chest
        const k = (TM.prize && TM.prize[this.map.id]) || TM.kamas;
        H.found = true; Prog.add('tmapsDug'); Store.save(); this.tmapHere = null;
        const S = Store.data; S.treasures = (S.treasures || 0) + 1; Store.save();
        this.slowMo(1.1, 0.2); this.shake(4); Audio2.play('saut', 0.7, 0.8);
        this._trez = { at: this.time + 0.22, x: H.x, y: H.y, k };
      }
    }
    if (this.updateNowel) this.updateNowel();
    if (this.cawottes && this.cawottes.length) this.updateCawottes(dt);
    if (this._trez && this.time >= this._trez.at && !this.cine) {
      const Z = this._trez; this._trez = null;
      const Gh = this.C.tmap.ghost || {}, L3 = [...(Gh.lines || [])].sort(() => Math.random() - 0.5).slice(0, 3);
      // 0.92: his last line hints at a profile name's music easter egg (UI.NAME_EGGS), never the one of last time
      const EL = Gh.egglines || [], S = Store.data;
      if (EL.length) { let i = randi(0, EL.length - 1); if (EL.length > 1 && i === S.tmEgg) i = (i + 1 + randi(0, EL.length - 2)) % EL.length; S.tmEgg = i; Store.save(); L3.splice(2, 1, EL[i]); }
      this.startCine('treasure', { x: Z.x, y: Z.y, k: Z.k, lines: L3, said: -1 }, () => { Audio2.stopJingle(0.8); this.treasureGold(Z); });
    }
  },
  treasureGold(Z) {
    if (this.map.noKamas) {   // (0.68: Nowel gives no kamas: its treasure is a skin)
      const x = this.nowelSkin(['hats', 'capes', 'pets']); if (x) { this.giveSkin(x); this.announce(this.skinName(x), T('nowel_gift_got', { n: this.skinName(x) }), '#9cff6a', { center: true }); }
      for (let i = 0; i < 60; i++) this.particles.push({ x: Z.x, y: Z.y - 6, vx: rand(-190, 190), vy: rand(-460, -140), t: 0, life: rand(0.8, 1.5), c: pick(['#ff5a5a', '#7aff8a', '#ffffff']), s: rand(3, 7) });
      Audio2.play('stars', 0.8); return;
    }
    const k = Z.k; this.kamas += k;
    this.announce(T('tmap_found_t'), T('tmap_found', { k }), '#ffd700', { center: true }); this.shake(6);
    for (let i = 0; i < 90; i++) this.particles.push({ x: Z.x, y: Z.y - 6, vx: rand(-190, 190), vy: rand(-460, -140), t: 0, life: rand(0.8, 1.5), c: pick(['#ffd700', '#ffe866', '#f0b020', '#fff6c0']), s: rand(3, 7) });
    Audio2.play('coffre', 0.8); Audio2.play('stars', 0.8); for (let i = 0; i < 12; i++) setTimeout(() => Audio2.play('pok', 0.5, 0.9 + i * 0.05), i * 80);
    this.treasureBonus(Z);
  },
  // 0.97: besides the kamas, C.tmap.bonus of the chests also hold a Dofus (C.tmap.bonusDofus of them: one not found yet,
  // dropped by the chest — its pickup plays the Dofus show) or else a shield not owned yet; when one kind is all found,
  // the other; both: nothing more
  treasureBonus(Z) {
    const TM = this.C.tmap, S = Store.data; if (Math.random() >= (TM.bonus || 0)) return;
    const dofs = (this.C.dofus || []).filter(d => !(S.dofus || {})[d.id] && !this.dofus.includes(d)), sh = this.nowelSkin(['shields']);
    let kind = Math.random() < (TM.bonusDofus !== undefined ? TM.bonusDofus : 0.5) ? 'dofus' : 'shield';
    if (kind === 'dofus' && !dofs.length) kind = sh ? 'shield' : null; else if (kind === 'shield' && !sh) kind = dofs.length ? 'dofus' : null;
    if (kind === 'dofus') { this.dropPickup('dofus', Z.x + 60, Z.y + 20, pick(dofs).id); this.chat(T('tmap_dofus'), '#ffcf3a'); Audio2.sfx('EVENT', 0.6); }
    else if (kind === 'shield') {
      S.owned = S.owned || []; if (!S.owned.includes(sh.id)) S.owned.push(sh.id); Store.save();
      this.announce(this.skinName(sh), T('tmap_shield', { n: this.skinName(sh) }), '#9cff6a', { center: true }); Prog.check(this);
    }
  },
  // 0.92: the Maîtres Corbacs' reward of the minute, a Manuel du Tailleur (0.95: no more treasure maps — Jorbak is
  // their only source). A dry spot of the map away from the character and from the other pickups; the arrow at the
  // screen's edge points to it, a message in the middle says it
  doomReward() {
    const P = this.player, b = this.bounds, kind = 'manuel';
    let x = P.x, y = P.y;
    for (let k = 0; k < 60; k++) {
      x = rand(b.x0 + 100, b.x1 - 100); y = rand(b.y0 + 100, b.y1 - 100);
      if (Math.hypot(x - P.x, y - P.y) > 380 && !this.isWater(x, y) && !this.pickups.some(p => Math.hypot(p.x - x, p.y - y) < 60)) break;
    }
    this.dropPickup(kind, x, y, 1).doomRw = 1;
    const msg = T(kind === 'tmap' ? 'doom_rw_tmap' : 'doom_rw_manuel');
    this.announce(kind === 'tmap' ? T('tmap') : L(this.C.manuel.name), msg, kind === 'tmap' ? '#ffcf3a' : '#ff9cf0', { center: true, force: true });
    Audio2.sfx('EVENT', 0.6);
  },
  tmapFree() { const S = Store.data.tmaps || {}; return (this.C.tmap.maps || []).filter(id => !S[id] && this.C.maps.some(m => m.id === id && SPR.worlds[m.world])); },
  // a spot for the cross in a zone's world: inside its bounds, on land, away from where the runs start (and from the player)
  tmapSpot(m) {
    const W = SPR.worlds[m.world], here = m.id === this.map.id && this.player, wat = here && this.water ? this.water : decodeWater(W.water), ins = W.inset || [0, 0, 0, 0];
    const b = { x0: 30 + ins[0] + 150, x1: W.w - 30 - ins[1] - 150, y0: 40 + ins[2] + 150, y1: W.h - 20 - ins[3] - 150 }, cx = (b.x0 + b.x1) / 2, cy = (b.y0 + b.y1) / 2;
    const wet = (x, y) => { if (!wat) return false; const i = Math.floor(x / wat.cell), j = Math.floor(y / wat.cell); return i >= 0 && j >= 0 && i < wat.cols && j < wat.rows && wat.bits[j * wat.cols + i] === 1; };
    let p = { x: cx, y: cy };
    for (let k = 0; k < 80; k++) {
      const x = rand(b.x0, b.x1), y = rand(b.y0, b.y1);
      if (wet(x, y) || Math.hypot(x - cx, y - cy) < 400 || (here && Math.hypot(x - this.player.x, y - this.player.y) < 500)) continue;
      p = { x, y }; break;
    }
    return { x: Math.round(p.x), y: Math.round(p.y) };
  },
  gotTmap() {
    const S = Store.data, C = this.C, free = this.tmapFree(), dbg = (typeof Game !== 'undefined' && Game.debug) || {};
    S.tmaps = S.tmaps || {}; Audio2.ui('item', 0.8);
    if (!free.length) { const k = C.tmap.kamas; this.kamas += k; this.chat(T('tmap_found', { k }), '#ffd700'); return; }   // (every zone has its map already)
    const id = free.includes(dbg.tmap) ? dbg.tmap : pick(free), m = C.maps.find(x => x.id === id), e = Object.assign(this.tmapSpot(m), { found: false, t: Date.now() });
    S.tmaps[id] = e; Store.save();
    if (id === this.map.id) { this.tmapHere = e; this._tmapSaid = false; }
    this.chat(T('tmap_got', { z: tmapZoneName(m) }), '#ffcf3a');
    if (typeof UI !== 'undefined' && UI.mushaScene) UI.mushaScene(this, e, m);
  },
  // the cross of a treasure map found in an earlier run (ground)
  drawTmapCross(ctx, t) {
    const H = this.tmapHere; if (!H) return;
    const k = this.tmapDig / this.C.tmap.dig;
    ctx.save(); ctx.translate(H.x, H.y); ctx.lineCap = 'round';
    ctx.strokeStyle = 'rgba(60,10,0,0.6)'; ctx.lineWidth = 11; ctx.beginPath(); ctx.moveTo(-16, -9); ctx.lineTo(16, 9); ctx.moveTo(16, -9); ctx.lineTo(-16, 9); ctx.stroke();
    ctx.strokeStyle = '#d0201a'; ctx.lineWidth = 6; ctx.stroke();
    if (k > 0) { ctx.strokeStyle = '#ffd24a'; ctx.lineWidth = 4; ctx.beginPath(); ctx.ellipse(0, 0, 34, 20, 0, -Math.PI / 2, -Math.PI / 2 + TAU * k); ctx.stroke(); }
    ctx.restore();
  },
  // ------------------------------------------------ TTG boosters
  openBooster(pk) {
    // 0.98.3: a pack holds its theme: its family's cards, or the cards of a rarity (SPR.boosters.names: a family or r0..r3); every card is in one
    const T_ = this.C.ttg, W = T_.rw || [55, 30, 12, 3], nm = SPR.boosters.names[pk], rk = /^r\d$/.test(nm) ? +nm[1] : -1, pool = T_.cards.filter(c => rk >= 0 ? (c.r || 0) === rk : c.fam === nm);
    const has = [0, 1, 2, 3].filter(r => pool.some(c => (c.r || 0) === r)); let x = Math.random() * has.reduce((a, r) => a + W[r], 0), rr = has[0];   // (a rarity first, among those the pack holds: C.ttg.rw gives the overall odds; then one of its cards)
    for (const r of has) { x -= W[r]; if (x <= 0) { rr = r; break; } }
    const card = pick(pool.filter(c => (c.r || 0) === rr));
    const S = Store.data; S.ttg = S.ttg || {}; Prog.add('boosters');
    const n = (S.ttg[card.id] || 0) + 1; S.ttg[card.id] = n; Store.save();
    if (typeof UI !== 'undefined' && UI.boosterOpen) UI.boosterOpen(this, card, n, pk);
    else this.chat(n > 1 ? T('ttg_dup', { c: n }) : T('ttg_new', { n: L(card.name) }), '#9cff6a');
  },
});
// ToT's door, as a time portal (0.56: the client's zaap, map object 7000 in HD (tools/assets/build_zaap56.py), its opening
// filled with a turning violet / blue vortex, a Xélor clock face and sparks, a glow on the ground)
function drawTimePortal(ctx, x, y, t) {
  const Hh = 190, zf = Game.icons.get('zaap_hd'), zi = zf && Game.icons.src('zaap_hd'), Ww = zf ? Hh * zf[2] / zf[3] : 170;
  const ox = x - Ww / 2, oy = y - Hh + 18, cx = ox + 320 / 552 * Ww, cy = oy + 330 / 607 * Hh, rx = 118 / 552 * Ww, ry = 182 / 607 * Hh;
  ctx.save();
  ctx.globalAlpha = 0.55 + 0.15 * Math.sin(t * 3); ctx.drawImage(RCache.glow('rgba(120,110,255,0.7)'), cx - 120, y - 40, 240, 70); ctx.globalAlpha = 1;
  ctx.save(); ctx.beginPath(); ctx.ellipse(cx, cy, rx, ry, 0, 0, TAU); ctx.clip();
  const g = ctx.createRadialGradient(cx, cy, 4, cx, cy, ry); g.addColorStop(0, '#f4f0ff'); g.addColorStop(0.35, '#8f7bff'); g.addColorStop(0.75, '#3a2a9a'); g.addColorStop(1, '#12103a');
  ctx.fillStyle = g; ctx.fillRect(cx - rx, cy - ry, rx * 2, ry * 2);
  ctx.globalCompositeOperation = 'lighter';
  for (let i = 0; i < 5; i++) {   // the vortex arms
    ctx.save(); ctx.translate(cx, cy); ctx.scale(rx / ry, 1); ctx.rotate(t * (1.2 + i * 0.25) + i * 1.3);
    ctx.strokeStyle = ['#7fa2ff', '#c8a0ff', '#ffffff', '#5a7aff', '#e0c8ff'][i]; ctx.globalAlpha = 0.45; ctx.lineWidth = 5 - i * 0.6;
    ctx.beginPath(); for (let a = 0; a < TAU * 1.2; a += 0.12) { const r = 6 + a * ry / 7.5; ctx.lineTo(Math.cos(a) * r, Math.sin(a) * r); } ctx.stroke(); ctx.restore();
  }
  ctx.globalAlpha = 0.85; ctx.strokeStyle = '#ffe58a'; ctx.lineWidth = 2.5;   // the Xélor clock
  const cr = ry * 0.45; ctx.beginPath(); ctx.ellipse(cx, cy, cr * rx / ry, cr, 0, 0, TAU); ctx.stroke();
  for (let i = 0; i < 12; i++) { const a = i * TAU / 12; ctx.beginPath(); ctx.moveTo(cx + Math.cos(a) * cr * 0.82 * rx / ry, cy + Math.sin(a) * cr * 0.82); ctx.lineTo(cx + Math.cos(a) * cr * rx / ry, cy + Math.sin(a) * cr); ctx.stroke(); }
  ctx.lineCap = 'round'; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(cx + Math.cos(-t * 3) * cr * 0.75 * rx / ry, cy + Math.sin(-t * 3) * cr * 0.75); ctx.stroke();
  ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(cx + Math.cos(-t * 0.3) * cr * 0.45 * rx / ry, cy + Math.sin(-t * 0.3) * cr * 0.45); ctx.stroke();
  for (let i = 0; i < 14; i++) {   // motes spiralling in
    const q = (t * 0.35 + i / 14) % 1, a = i * 2.4 + t * 2, r = (1 - q) * ry;
    ctx.globalAlpha = Math.sin(q * Math.PI); ctx.fillStyle = i % 2 ? '#ffffff' : '#c8b0ff';
    ctx.beginPath(); ctx.arc(cx + Math.cos(a) * r * rx / ry, cy + Math.sin(a) * r, 1.6 + 1.6 * q, 0, TAU); ctx.fill();
  }
  ctx.restore();
  if (zi) ctx.drawImage(zi, zf[0], zf[1], zf[2], zf[3], ox, oy, Ww, Hh);
  ctx.globalAlpha = 1; ctx.font = 'bold 13px DofusBold, Verdana'; ctx.textAlign = 'center'; ctx.lineWidth = 3; ctx.strokeStyle = '#000';
  ctx.strokeText(T('portal'), x, oy - 10); ctx.fillStyle = '#c8d6ff'; ctx.fillText(T('portal'), x, oy - 10);
  ctx.restore();
}
// a treasure map's zone, as the player may know it (a secret zone not unlocked yet keeps its secret)
function tmapZoneName(m) { const S = Store.data; return m.hidden && !(S.unlocked || []).includes(m.id) ? T('secret_zone') + ' ★' : L(m.name); }

// 0.91: the countdown's sword, as vectors, pointing up from its guard at (0, 0), blade about 0.8 L long: a silver blade
// with its fuller, a gold crossguard with a red gem, a leather grip, a gold pommel, a dark outline; glint in 0..1 = a
// light running down the blade (-1: none)
// 0.98 (the old bronze medallion was not Dofus enough: Dofus Retro's and Dofus Unity's logos, green and alive): the
// countdown's emblem, drawn around 0 (R = its outer radius): a lime aurora behind, a wreath of leaves turning slowly (and an
// inner one the other way), a gold ring carrying the time left as a glowing vine that empties clockwise with a spark at
// its head, a Dofus egg glowing lime in the middle with the logo's swirl turning in it, fireflies drifting up around it.
// Its glow warms as the count goes down (lime, yellow-green, gold); the egg flares when the number strikes (u 0.12).
const CD_HEAT = ['#b6f04a', '#d8ec4a', '#f5c542'];
const CD_LEAVES = ['#5aa45a', '#83bb68', '#4f9460', '#9cc47c', '#6db064'];   // (0.98.2: softer greens, the pure ones jumped out of the emblem)
function cdEgg(ctx, w, h) {   // an egg, its widest part low, drawn around 0 (top -h, bottom h * 0.85)
  ctx.beginPath(); ctx.moveTo(0, -h); ctx.bezierCurveTo(w * 0.62, -h, w, -h * 0.25, w, h * 0.18); ctx.bezierCurveTo(w, h * 0.62, w * 0.55, h * 0.85, 0, h * 0.85);
  ctx.bezierCurveTo(-w * 0.55, h * 0.85, -w, h * 0.62, -w, h * 0.18); ctx.bezierCurveTo(-w, -h * 0.25, -w * 0.62, -h, 0, -h); ctx.closePath();
}
function cdMedal(ctx, R, u, n, t) {
  const heat = CD_HEAT[n], flare = u >= 0.12 && u < 0.5 ? 1 - (u - 0.12) / 0.38 : 0;
  // the aurora behind: a lime glow and a deeper teal one, breathing
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  const br = 1 + 0.05 * Math.sin(t * 2.4) + 0.25 * flare;
  ctx.globalAlpha *= 0.55; let gr = R * 1.75 * br; ctx.drawImage(RCache.glow('rgba(40,170,120,0.8)'), -gr, -gr, gr * 2, gr * 2);
  gr = R * 1.3 * br; ctx.drawImage(RCache.glow(n === 2 ? 'rgba(245,200,70,0.85)' : 'rgba(170,236,60,0.85)'), -gr, -gr, gr * 2, gr * 2);
  ctx.restore();
  ctx.fillStyle = 'rgba(0,20,8,0.35)'; ctx.beginPath(); ctx.ellipse(0, R * 0.14, R * 1.12, R * 1.04, 0, 0, TAU); ctx.fill();   // (its shadow)
  // the wreaths: big leaves turning one way, smaller ones the other, each swaying a little
  const wreath = (N, rr, s, spin, off) => {
    for (let i = 0; i < N; i++) {
      const an = i / N * TAU + t * spin + off, sw = Math.sin(t * 2.2 + i * 1.7) * 0.18;
      ctx.save(); ctx.globalAlpha *= 0.72; ctx.rotate(an); ctx.translate(0, -rr); ctx.rotate(-0.55 + sw); cdLeaf(ctx, s * (0.85 + 0.3 * ((i * 7) % 5) / 5), CD_LEAVES[(i * 3) % CD_LEAVES.length]); ctx.restore();
    }
  };
  wreath(20, R * 0.98, R * 0.36, 0.22, 0);
  wreath(14, R * 0.86, R * 0.24, -0.35, 0.2);
  // the gold ring (dark rim, gold body, a light top)
  ctx.lineWidth = R * 0.12; ctx.strokeStyle = '#1e2a0e'; ctx.beginPath(); ctx.arc(0, 0, R * 0.78, 0, TAU); ctx.stroke();
  const gz = ctx.createLinearGradient(0, -R, 0, R); gz.addColorStop(0, '#fff3b8'); gz.addColorStop(0.4, '#f5c542'); gz.addColorStop(1, '#8a560c');
  ctx.lineWidth = R * 0.075; ctx.strokeStyle = gz; ctx.beginPath(); ctx.arc(0, 0, R * 0.78, 0, TAU); ctx.stroke();
  ctx.fillStyle = 'rgba(8,36,22,0.92)'; ctx.beginPath(); ctx.arc(0, 0, R * 0.73, 0, TAU); ctx.fill();   // (the deep green inside)
  // the time left: a glowing vine on the ring, clockwise from the top, its head a spark throwing motes and tiny leaves back
  const a0 = -Math.PI / 2 + TAU * Math.min(1, u), a1 = -Math.PI / 2 + TAU, rr = R * 0.78, gl = RCache.glow('rgba(200,250,110,0.95)');
  if (u < 1) {
    ctx.lineCap = 'round'; ctx.strokeStyle = '#0e2a0a'; ctx.lineWidth = R * 0.085; ctx.beginPath(); ctx.arc(0, 0, rr, a0, a1); ctx.stroke();
    const ag = ctx.createLinearGradient(-R, -R, R, R); ag.addColorStop(0, '#f4ffc8'); ag.addColorStop(1, heat); ctx.strokeStyle = ag; ctx.lineWidth = R * 0.05; ctx.beginPath(); ctx.arc(0, 0, rr, a0, a1); ctx.stroke();
    for (let i = 0; i < 9; i++) {   // little leaves sprouting along the vine
      const an = a0 + (a1 - a0) * (i + 0.5) / 9; if (an >= a1) break;
      ctx.save(); ctx.rotate(an + Math.PI / 2); ctx.translate(0, -rr - R * 0.05 * (i % 2 ? 1 : -1)); ctx.rotate(i % 2 ? 0.6 : -0.6); cdLeaf(ctx, R * 0.12, CD_LEAVES[i % CD_LEAVES.length]); ctx.restore();
    }
    const hx = Math.cos(a0) * rr, hy = Math.sin(a0) * rr;
    ctx.save(); ctx.globalCompositeOperation = 'lighter'; const hr = R * (0.24 + 0.04 * Math.sin(t * 30)); ctx.drawImage(gl, hx - hr, hy - hr, hr * 2, hr * 2);
    for (let i = 0; i < 7; i++) {
      const q = (t * 2.2 + i / 7) % 1, an = a0 - q * 0.5, d = rr + Math.sin(i * 7.3) * 0.5 * R * 0.12 * q, er = R * 0.03 * (1 - q);
      ctx.globalAlpha = (1 - q) * 0.9; ctx.drawImage(gl, Math.cos(an) * d - er * 2, Math.sin(an) * d - er * 2 - q * R * 0.1, er * 4, er * 4);
    }
    ctx.restore();
  }
  // the Dofus egg: dark outline, lime body lit from the top left, the logo's swirl turning in it, a light rim, a flare
  const ew = R * 0.56, eh = R * 0.66;
  ctx.save(); ctx.translate(0, R * 0.04);
  ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha *= 0.5 + 0.5 * flare; const eg0 = R * (0.95 + 0.25 * flare); ctx.drawImage(RCache.glow('rgba(190,250,90,0.9)'), -eg0, -eg0, eg0 * 2, eg0 * 2); ctx.restore();
  ctx.lineWidth = R * 0.06; ctx.strokeStyle = '#14300c'; cdEgg(ctx, ew, eh); ctx.stroke();
  const eg = ctx.createRadialGradient(-ew * 0.35, -eh * 0.45, R * 0.04, 0, 0, eh * 1.1); eg.addColorStop(0, '#f4ffb0'); eg.addColorStop(0.35, '#c8f060'); eg.addColorStop(0.75, '#7cc42e'); eg.addColorStop(1, '#3a7a16');
  ctx.fillStyle = eg; cdEgg(ctx, ew, eh); ctx.fill();
  ctx.save(); cdEgg(ctx, ew, eh); ctx.clip(); ctx.rotate(-t * 0.5); ctx.lineCap = 'round';
  for (const [lw, col, al] of [[R * 0.08, '#4a8a16', 0.55], [R * 0.03, '#2e6a10', 0.7]]) {
    ctx.globalAlpha *= al; ctx.strokeStyle = col; ctx.lineWidth = lw; ctx.beginPath();
    for (let k = 0; k <= 60; k++) { const th = k / 60 * 2.6 * TAU, r = R * 0.52 * k / 60; ctx.lineTo(Math.cos(th) * r, Math.sin(th) * r); }
    ctx.stroke(); ctx.globalAlpha /= al;
  }
  ctx.restore();
  ctx.strokeStyle = 'rgba(250,255,220,0.55)'; ctx.lineWidth = R * 0.02; ctx.beginPath(); ctx.ellipse(-ew * 0.32, -eh * 0.42, ew * 0.32, eh * 0.2, -0.5, Math.PI * 1.05, Math.PI * 1.75); ctx.stroke();   // (its shine)
  if (flare) { ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha *= flare * 0.6; ctx.fillStyle = '#f4ffd0'; cdEgg(ctx, ew, eh); ctx.fill(); ctx.restore(); }
  ctx.restore();
  // fireflies drifting up around the emblem
  ctx.save(); ctx.globalCompositeOperation = 'lighter'; const ff = RCache.glow('rgba(220,255,120,0.95)');
  for (let i = 0; i < 14; i++) {
    const q = (t * (0.18 + 0.1 * ((i * 7) % 5) / 5) + i / 14) % 1, an = i * 2.4, fx = Math.cos(an) * R * (0.95 + 0.45 * ((i * 13) % 7) / 7) + Math.sin(t * 1.7 + i) * R * 0.06, fy = Math.sin(an) * R * 0.9 - q * R * 0.7, fr = R * (0.035 + 0.03 * ((i * 11) % 5) / 5) * (0.6 + 0.4 * Math.sin(t * 5 + i));
    ctx.globalAlpha = Math.sin(q * Math.PI) * 0.9; ctx.drawImage(ff, fx - fr * 2, fy - fr * 2, fr * 4, fr * 4);
  }
  ctx.restore();
}
// a leaf (the logos' leaves: the countdown's wreath, GO!'s burst, the victory), drawn around 0, length s. 0.98.2 (a dark outline
// round a flat colour: raw, they jumped out): a picture made once per colour: feathered edges, lit along one side, a faint midrib
const _cdLeafC = new Map();
function cdLeafPic(col) {
  let c = _cdLeafC.get(col); if (c) return c;
  const W = 128, H = 72, shape = (g, k) => { g.beginPath(); g.moveTo(-W * 0.48 * k, 0); g.quadraticCurveTo(0, -H * 0.6 * k, W * 0.48 * k, 0); g.quadraticCurveTo(0, H * 0.6 * k, -W * 0.48 * k, 0); };
  c = document.createElement('canvas'); c.width = W; c.height = H; const g = c.getContext('2d'); g.translate(W / 2, H / 2);
  g.fillStyle = col; g.globalAlpha = 0.2; for (let i = 0; i < 6; i++) { shape(g, 1 - i * 0.055); g.fill(); }   // (shrinking layers: an edge that fades out)
  g.globalAlpha = 1; g.globalCompositeOperation = 'source-atop';
  const lit = g.createLinearGradient(0, -H * 0.3, 0, H * 0.3); lit.addColorStop(0, 'rgba(255,255,225,0.34)'); lit.addColorStop(0.5, 'rgba(255,255,225,0)'); lit.addColorStop(1, 'rgba(10,40,20,0.3)'); g.fillStyle = lit; g.fillRect(-W / 2, -H / 2, W, H);
  g.strokeStyle = 'rgba(245,255,215,0.22)'; g.lineWidth = 2.5; g.lineCap = 'round'; g.beginPath(); g.moveTo(-W * 0.38, 0); g.lineTo(W * 0.38, 0); g.stroke();
  _cdLeafC.set(col, c); return c;
}
function cdLeaf(ctx, s, col) { ctx.drawImage(cdLeafPic(col), -s * 0.56, -s * 0.315, s * 1.12, s * 0.63); }
// 0.98: GO!'s swords are the Épée Royale du Bouftou (client item 2440, picture 6/30, rendered from its vector art at 640 px:
// icons3 'go_sword', tools/assets/build_iconhd091.py gosword), drawn like cdSword around its guard, blade up, tip at
// -0.8 L; the left one mirrored; the glint = the picture again, added, flashing as the light runs. cdSword if it is missing
const GO_SWORD = { gx: 165, gy: 470, cx: 316, cy: 320, len: 650, size: 640 };   // (in the picture: its guard, its centre, guard to tip, its size)
function goSword(ctx, L, glint, side) {
  const IC = Game.icons; if (!IC || !IC.get('go_sword')) { cdSword(ctx, L, glint); return; }
  const G = GO_SWORD, k = L * 0.8 / G.len, x = (G.cx - G.gx) * k, y = (G.cy - G.gy) * k;
  ctx.save(); if (side < 0) ctx.scale(-1, 1); ctx.rotate(-Math.PI / 4);   // (its blade runs to the top right: turned up)
  IC.drawFit(ctx, 'go_sword', x, y, G.size * k);
  if (glint >= 0) { ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha *= 0.2 * Math.sin(glint * Math.PI); IC.drawFit(ctx, 'go_sword', x, y, G.size * k); }
  ctx.restore();
}
function cdSword(ctx, L, glint) {
  const O = 'rgba(28,16,6,0.95)', bw = L * 0.05, tip = -L * 0.8, base = -L * 0.03;
  const blade = () => { ctx.beginPath(); ctx.moveTo(-bw, base); ctx.lineTo(-bw * 0.92, tip + L * 0.12); ctx.lineTo(0, tip); ctx.lineTo(bw * 0.92, tip + L * 0.12); ctx.lineTo(bw, base); ctx.closePath(); };
  ctx.lineJoin = 'round'; ctx.lineCap = 'round';
  let g = ctx.createLinearGradient(-bw, 0, bw, 0); g.addColorStop(0, '#8d9cb0'); g.addColorStop(0.42, '#ffffff'); g.addColorStop(0.58, '#dfe8f2'); g.addColorStop(1, '#6c7b90');
  blade(); ctx.fillStyle = g; ctx.fill(); ctx.lineWidth = L * 0.016; ctx.strokeStyle = O; ctx.stroke();
  ctx.strokeStyle = 'rgba(90,104,124,0.85)'; ctx.lineWidth = L * 0.008; ctx.beginPath(); ctx.moveTo(0, base - L * 0.03); ctx.lineTo(0, tip + L * 0.16); ctx.stroke();   // the fuller
  if (glint >= 0) {
    ctx.save(); blade(); ctx.clip(); const gy = base + (tip - base) * glint, lg = ctx.createLinearGradient(0, gy - L * 0.12, 0, gy + L * 0.12);
    lg.addColorStop(0, 'rgba(255,255,255,0)'); lg.addColorStop(0.5, 'rgba(255,255,230,0.95)'); lg.addColorStop(1, 'rgba(255,255,255,0)');
    ctx.globalCompositeOperation = 'lighter'; ctx.fillStyle = lg; ctx.fillRect(-bw * 2, gy - L * 0.12, bw * 4, L * 0.24); ctx.restore();
  }
  // the crossguard and its gem
  g = ctx.createLinearGradient(0, -L * 0.07, 0, L * 0.03); g.addColorStop(0, '#fff2b0'); g.addColorStop(0.5, '#e0a12c'); g.addColorStop(1, '#8a520e');
  ctx.beginPath(); ctx.moveTo(-L * 0.17, -L * 0.03); ctx.quadraticCurveTo(-L * 0.2, -L * 0.05, -L * 0.21, -L * 0.07); ctx.lineTo(-L * 0.06, -L * 0.03); ctx.lineTo(L * 0.06, -L * 0.03); ctx.lineTo(L * 0.21, -L * 0.07); ctx.quadraticCurveTo(L * 0.2, -L * 0.05, L * 0.17, -L * 0.03); ctx.lineTo(L * 0.17, L * 0.025); ctx.lineTo(-L * 0.17, L * 0.025); ctx.closePath();
  ctx.fillStyle = g; ctx.fill(); ctx.lineWidth = L * 0.014; ctx.strokeStyle = O; ctx.stroke();
  ctx.beginPath(); ctx.arc(0, 0, L * 0.028, 0, TAU); ctx.fillStyle = '#d42a3a'; ctx.fill(); ctx.lineWidth = L * 0.01; ctx.stroke();
  ctx.beginPath(); ctx.arc(-L * 0.009, -L * 0.009, L * 0.009, 0, TAU); ctx.fillStyle = '#ffd0d6'; ctx.fill();
  // the grip and the pommel
  g = ctx.createLinearGradient(-L * 0.03, 0, L * 0.03, 0); g.addColorStop(0, '#3a1e0c'); g.addColorStop(0.5, '#8a5428'); g.addColorStop(1, '#2e1608');
  ctx.beginPath(); ctx.rect(-L * 0.03, L * 0.025, L * 0.06, L * 0.15); ctx.fillStyle = g; ctx.fill(); ctx.lineWidth = L * 0.012; ctx.strokeStyle = O; ctx.stroke();
  ctx.strokeStyle = 'rgba(255,214,150,0.35)'; ctx.lineWidth = L * 0.006;
  for (let i = 0; i < 4; i++) { const y = L * (0.045 + i * 0.035); ctx.beginPath(); ctx.moveTo(-L * 0.03, y); ctx.lineTo(L * 0.03, y + L * 0.02); ctx.stroke(); }
  g = ctx.createRadialGradient(-L * 0.012, L * 0.19, L * 0.004, 0, L * 0.2, L * 0.04); g.addColorStop(0, '#fff6c8'); g.addColorStop(1, '#b8750f');
  ctx.beginPath(); ctx.arc(0, L * 0.205, L * 0.037, 0, TAU); ctx.fillStyle = g; ctx.fill(); ctx.lineWidth = L * 0.013; ctx.strokeStyle = O; ctx.stroke();
}
