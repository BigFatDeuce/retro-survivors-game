'use strict';
// ---------------------------------------------------------------- global spells (0.23): spells offered to every class
// (C.globalSpells, silver icons). Most use the usual spell types (projectile, orbit, zone); this file holds what is
// their own: La bonne Pioche (kamas, the 1000-kama vein) and the Jeton de la Foire du Trool (a wheel that gives a spell
// of another class). Methods added to Run; game.js offers them in upgradeOptions and routes the Jeton in applyUpgrade.
const WHEEL_TYPES = new Set(['projectile', 'orbit', 'zone', 'strike', 'line', 'dash', 'leap', 'slam', 'melee', 'toss', 'beam', 'trap', 'heal', 'buff', 'pulse', 'cone', 'aura']);
Object.assign(Run.prototype, {
  // new global spells for the level-up choices (they take a spell slot like the class spells)
  globalOptions(opts, ownedIds) {
    for (const g of this.C.globalSpells || []) {
      if (ownedIds.includes(g.id) || (g.id === 'jeton_trool' && this.troolUsed)) continue;
      opts.push({ kind: 'spell', id: g.id, lv: 1, w: g.w * (this.level < 12 ? 0.9 : 0.6), isNew: true, glob: true });
    }
  },
  // 0.71: Cawotte — a Cawotte springs up on a red zone under the character (a cross until 0.75, round since 0.76),
  // cawottes spin round it; standing in the zone heals p.heal HP a second for p.duration s (the shop's power scales heal, cooldown and duration)
  cawotte(sp) {
    const P = this.player, p = sp.p, st = this.stats;
    const s = sp.shopT();   // (1 HP/s, 25 s, 5 s → 1.75 HP/s, 18 s, 8 s with the whole shop)
    this.cawottes.push({ x: P.x, y: P.y, t0: this.time, until: this.time + lerp(p.duration, p.durShop || p.duration, s) * st.duration, heal: lerp(p.heal, p.healShop || p.heal, s) * (1 + st.healBonus), r: (p.radius || 70) * st.area, tick: 0 });
    for (let i = 0; i < 14; i++) this.particles.push({ x: P.x + rand(-20, 20), y: P.y, vx: rand(-90, 90), vy: rand(-220, -80), t: 0, life: rand(0.4, 0.7), c: pick(['#7a5a34', '#a07a48', '#f08c1e']), s: rand(2, 4) });
    Audio2.play('saut', 0.5, 1.2);
    return true;
  },
  // 0.95: the Pwout de Cawotte + Cawotte fusion — the Pwout's cloud (its radius, red-brown, twice its cawottes)
  // follows the character, hurts the monsters in it and heals him and his summons (zoneHeal, every second); four Cawottes
  // (the Cawotte's own zone, sprite and spinning cawottes, radius p.satR) spring up on the diagonals around where it was
  // cast and stay there, like traps (0.97: they followed him), hurting the monsters on them at p.satK of the cloud's blow
  // until they wither with the cloud. All five are one group (grpHit): a monster under two of them is hit
  // once a tick; a new cast replaces the last one (shorter cooldowns than the 4 s: never two clouds, two heals) and keeps
  // its hit clock and heal timer (sp.state.grp, the old cloud's healT): no second blow, no lost heal at the swap
  pwcawotte(sp) {
    const P = this.player, p = sp.p, st = this.stats, t = this.time, until = t + p.duration * st.duration, r = p.radius * st.area, sr = p.satR * st.area;
    const old = this.zones.find(z => z.spell === sp), grp = sp.state.grp || (sp.state.grp = { tick: p.tick, hit: new Map() }), dmg = sp.dmg();
    for (const [m, l] of grp.hit) if (m.dying || t - l >= grp.tick) grp.hit.delete(m);   // (only the monsters hit this tick stay)
    this.zones = this.zones.filter(z => z.spell !== sp); this.cawottes = this.cawottes.filter(c => c.spell !== sp);
    this.zones.push({ x: P.x, y: P.y, r, until, tick: p.tick, next: 0, dmg, color: p.color, spell: sp, born: t, follow: P, cloud: 1, fart: 1, puff: p.puff, rim: p.rim, caw: p.cawN, grp,
      heal: lerp(p.heal, p.healShop || p.heal, sp.shopT()) * (1 + st.healBonus), healT: old ? old.healT : 0.5 });
    for (let i = 0; i < p.sat; i++) {
      const a = Math.PI / 4 + i * TAU / p.sat, d = r + sr * 0.9;   // (outside the cloud, apart from each other: four distinct zones)
      this.cawottes.push({ x: P.x + Math.cos(a) * d, y: P.y + Math.sin(a) * d, t0: t + i * 0.08, until, heal: 0, r: sr, tick: 0, dmg: dmg * p.satK, dtick: p.tick, next: t + i * 0.08, grp, spell: sp });
    }
    Audio2.play('saut', 0.5, 1.2);
    return true;
  },
  // 0.96: Boule de Chaos — a big violet fireball thrown straight at the nearest monster (no homing), exploding on the
  // first one it touches (projectile `aoe`: Run.explode): the trail it leaves (drawChaosBall) and a few violet sparks
  chaosTrail(p, dt) {
    if ((p._trT = (p._trT || 0) - dt) <= 0) { p._trT = 0.035; p.trail.push([p.x, p.y]); if (p.trail.length > 9) p.trail.shift(); }
    if (Math.random() < dt * 12) { const s = p.size; this.particles.push({ x: p.x + rand(-s, s) * 0.5, y: p.y + rand(-s, s) * 0.5, vx: -p.vx * 0.15 + rand(-30, 30), vy: -p.vy * 0.15 + rand(-40, 10), t: 0, life: rand(0.35, 0.6), s: rand(5, 9), round: 1, grow: 1.2, c: pick(['#c38cff', '#7a2ad8', '#ead6ff']) }); }
  },
  // its explosion (with the Flamiche's own client burst, fx 4600, tinted violet by Run.explode): a dark implosion ring, a
  // violet shockwave, a light rim, chaos sparks thrown out (few, see-through: the monsters stay visible)
  chaosBurst(x, y, r) {
    const t = this.time;
    this.rings.push({ x, y, r0: r * 0.25, r1: r, t0: t, dur: 0.42, color: '#9b3dff', fill: 1 });
    this.rings.push({ x, y, r0: r * 0.15, r1: r * 0.8, t0: t + 0.05, dur: 0.32, color: '#f0dcff' });
    this.rings.push({ x, y, r0: r * 0.9, r1: r * 0.2, t0: t, dur: 0.25, color: '#2a0650', fill: 1 });
    for (let i = 0; i < 18; i++) { const a = rand(TAU), v = rand(120, 320); this.particles.push({ x, y: y - 10, vx: Math.cos(a) * v, vy: Math.sin(a) * v * 0.6 - 60, t: 0, life: rand(0.35, 0.7), s: rand(4, 8), round: 1, grow: 0.8, c: pick(['#b46bff', '#6a1ec8', '#efdcff', '#8a3ae0']) }); }
    this.shake(2);
  },
  // one hit a tick for a monster under several areas of one group (the fusion's cloud and its Cawottes)
  grpHit(g, m) { const l = g.hit.get(m); if (l !== undefined && this.time - l < g.tick * 0.9) return false; g.hit.set(m, this.time); return true; },
  // a zone that heals the character in it (the fusion's cloud follows him), every second, and the summons in it that
  // can be hurt (the taunting ones: Run.update hits them), up to the life they came with
  zoneHeal(z) {
    const P = this.player, dx = P.x - z.x, dy = P.y - z.y, r2 = z.r * z.r;
    for (const s of this.summons) if (s.taunt && s.hp > 0 && s.hp < s.spell.p.hp && dist2(s.x, s.y, z.x, z.y) <= r2) s.hp = Math.min(s.spell.p.hp, s.hp + z.heal);
    if (P.dead || dx * dx + dy * dy > r2 || P.hp >= this.stats.maxHp) return;
    const d = P.heal(z.heal, true); if (d > 0) this.healText(d);   // (0.97: one number, Run.healText — heal() wrote its own too)
  },
  updateCawottes(dt) {
    const P = this.player;
    for (let i = this.cawottes.length - 1; i >= 0; i--) {
      const c = this.cawottes[i]; if (this.time > c.until) { this.cawottes.splice(i, 1); continue; }
      if (c.dmg && this.time >= c.next) { c.next = this.time + c.dtick; for (const m of this.mobsInRadius(c.x, c.y, c.r)) if (this.grpHit(c.grp, m)) this.damageMob(m, c.dmg, c.spell, true); }   // (0.95: the fusion's Cawottes)
      if (!c.heal) continue;
      const dx = (P.x - c.x) / c.r, dy = (P.y - c.y) / (c.r * 0.62);   // (0.76: a round zone, the ground's 0.62 ellipse)
      if (dx * dx + dy * dy < 1 && !P.dead && (c.tick -= dt) <= 0) { c.tick = 1; if (P.hp < this.stats.maxHp) { const d = P.heal(c.heal, true); if (d > 0) this.healText(d); } }
    }
  },
  // 0.74: a '+' on the screen (not the client's X), twice as wide, the summoned Cawotte (its client idle pose, HD
  // sheet 1277_z48) springing up in the middle with the client's summoning puff (fx 1100), cawottes spinning round
  drawCawottes(ctx, t, layer) {
    const sh = MobSheets.c['1277_z48'] || MobSheets.c['1277_z36'];
    for (const c of this.cawottes) {
      const age = t - c.t0, k = Math.min(1, age / 0.25) * Math.min(1, (c.until - t) / 0.4), r = c.r;
      if (age < 0) continue;   // (0.95: the fusion's Cawottes spring up one after the other)
      if (!c.fx) { c.fx = 1; this.fxAt(1100, c.x, c.y, { scale: 1.2 * Math.min(1, c.r / 120) }); }
      ctx.save(); ctx.translate(c.x, c.y);
      if (layer !== 'top') {   // 0.76: a round zone instead of the '+', the red far more see-through
      const disc = () => { ctx.beginPath(); ctx.ellipse(0, 0, r, r * 0.62, 0, 0, TAU); };
      ctx.globalAlpha = 0.15 * k; ctx.fillStyle = 'rgb(245,95,30)'; disc(); ctx.fill();   // (0.79: brighter, more orange than the Pwout's dark orange)
      ctx.globalAlpha = 0.4 * k; ctx.strokeStyle = 'rgb(170,55,10)'; ctx.lineWidth = 2.5; disc(); ctx.stroke();
      ctx.globalAlpha = (0.15 + 0.1 * Math.sin(t * 5)) * k; ctx.strokeStyle = '#ffd0a0'; ctx.lineWidth = 1.5; disc(); ctx.stroke();
      ctx.restore(); continue; }
      ctx.globalAlpha = k;
      if (sh) { const up = Math.min(1, age / 0.35), an = sh.has('staticR') ? 'staticR' : Object.keys(sh.anims)[0]; sh.draw(ctx, sh.frameAt(an, age, true), 0, 4 + (1 - up) * 30, ES * 1.25 * (0.5 + 0.5 * up), false); }
      for (let i = 0; i < 8; i++) { const an = t * 1.4 + i * TAU / 8, x = Math.cos(an) * r * 0.9, y = Math.sin(an) * r * 0.5; ctx.save(); ctx.translate(x, y); ctx.rotate(t * 4 + i); Game.icons.drawFit(ctx, 'it_68_31', 0, 0, 24); ctx.restore(); }
      ctx.restore();
    }
  },
  // La bonne Pioche: a pickaxe blow beside the character digs up kamas; 1/2000 (1/1000 after 5 min): the vein
  pickaxe(sp) {
    const P = this.player, p = sp.p, side = P.flip ? -1 : 1;
    const x = P.x + side * 26, y = P.y + 4;
    this.digs.push({ x, y, side, t0: this.time });
    const odds = this.time >= 300 ? p.odds5 : p.odds;
    this.after(0.23, () => {   // the kamas come out when the pick hits the ground (0.91: run time)
      for (let i = 0; i < 8; i++) this.particles.push({ x, y: y - 2, vx: rand(-70, 70), vy: rand(-150, -50), t: 0, life: rand(0.35, 0.6), c: pick(['#7a5a34', '#5a4026', '#a07a48']), s: rand(2, 4) });
      if (Math.random() < 1 / odds) return this.jackpot(x, y, p.jackpot);
      const v = p.kamas; this.kamas += v; this.text(x, y - 34, '+' + v + ' K', '#ffd700', 13);
      Audio2.blip('coin');
    });
    return true;
  },
  jackpot(x, y, n) {
    const v = n; this.kamas += v;
    this.announce(T('pioche_jackpot_t'), T('pioche_jackpot', { n: fmtNum(v) }), '#ffd700', { center: true });
    this.shake(4); this.rings.push({ x, y, r0: 10, r1: 160, t0: this.time, dur: 0.8, color: '#ffd700', fill: 1 });
    // a fountain of coins and the sound of money flowing
    for (let i = 0; i < 70; i++) this.particles.push({ x, y: y - 6, vx: rand(-160, 160), vy: rand(-420, -140), t: 0, life: rand(0.8, 1.5), c: pick(['#ffd700', '#ffe866', '#f0b020', '#fff6c0']), s: rand(3, 6), g: 520 });
    for (let i = 0; i < 16; i++) setTimeout(() => Audio2.play('pok', 0.55, 0.9 + i * 0.04), i * 75);
    Audio2.play('stars', 0.8); Audio2.sfx('EVENT', 0.6);
    if (this.ps) this.ps.jackpots = (this.ps.jackpots || 0) + 1;
    const S = Store.data; S.jackpots = (S.jackpots || 0) + 1; Store.save();
  },
  // Jeton de la Foire du Trool: a random spell of another class (one the run can draw: no summons or bombs)
  troolPool() {
    const own = new Set(this.spells.map(s => s.def.id)), mine = new Set(this.cls.spells), out = [];
    for (const c of this.C.classes) {
      if (c.id === this.cls.id) continue;
      for (const id of c.spells) { const s = this.C.spells[id]; if (s && !own.has(id) && !mine.has(id) && WHEEL_TYPES.has(s.t) && !s.spriteKeyBy && !out.some(o => o.id === id)) out.push({ id, cls: c }); }
    }
    return out;
  },
  trool() {
    this.troolUsed = true; Prog.add('wheels');
    const pool = this.troolPool(); if (!pool.length) { this.applyUpgrade({ kind: 'kamas' }); return; }
    const won = pick(pool);
    const give = () => {
      const s = this.addSpell(won.id); for (const f of s.def.fx || []) FxSheets.load(f);
      const k = Audio2.spellKeys(s.def); if (k.length) Audio2.preload(k);
      this.chat(T('wheel_won', { n: L(s.def.name), c: L(won.cls.name) }), '#ffcf3a');
    };
    if (typeof UI !== 'undefined' && UI.troolWheel && !(typeof Game !== 'undefined' && Game.debug && Game.debug.bot)) this.pendingWheel = { pool, won, give };
    else give();
  },
  // drawn by render.js: the pickaxe swing beside the character
  updateGlobals() {
    if (this.pendingWheel && !UI.modalOpen()) { const w = this.pendingWheel; this.pendingWheel = null; UI.troolWheel(this, w); }
    for (let i = this.digs.length - 1; i >= 0; i--) if (this.time - this.digs[i].t0 > 0.6) this.digs.splice(i, 1);
  },
});
