'use strict';
// ---------------------------------------------------------------- weapons (0.25): unique weapons (C.uniqueWeapons, 2 per
// weapon type, real client items with their own skin and effect) and weapon fusion (C.fusions: once the weapon has its
// finale and every spell is maxed, the weapon takes a characteristic's element). Methods added to Run; spells.js /
// game.js call onWeaponSwing (each attack) and onWeaponHit (each monster hit); render.js calls drawWeaponFx.
const FUSION_PART = {
  earth: ['#8a6234', '#b8894a', '#5a3e1e'], fire: ['#ff5a1e', '#ffb02a', '#ffe066'], water: ['#3fa8ff', '#9fdcff', '#ffffff'],
  air: ['#58d68d', '#b8f5c8', '#ffffff'], stars: ['#ffffff', '#d8c4ff', '#b07cff', '#fff3a0'], brute: ['#d8d0c0', '#8a8070', '#ffffff'], life: ['#e8d24a', '#9ccc3a', '#fff3a0'],
};
Object.assign(Run.prototype, {
  initWeapons() { this.wfx = []; this.rage = 0; this.rageT = 0; this._fT = 0; },
  // 0.60: n different weapons offered, from two different types: each type's 3 weapons (weight 1) and 2 Soifs de Sang
  // (C.bloodW, 0.6); a banished type never comes back (0.95: Bannir bans the weapon's whole type, Run.banish)
  weaponChoices(n) {
    const C = this.C, all = (C.uniqueWeapons || []).filter(w => !this.isBanned({ kind: 'weapon', id: w.id })), types = shuffle([...new Set(all.map(w => w.of))]).slice(0, n), out = [];
    for (const t of types) { const g = all.filter(w => w.of === t); out.push(weighted(g.map(w => [w, w.blood ? (C.bloodW || 0.6) * this.stats.luck : 1]))); }
    return out;
  },
  gotWeapon(def) {
    if (def.leech) this.recompute();
    this.announce(L(def.name), T(def.blood ? 'blood_found' : 'unique_found', { n: L(def.name) }), def.blood ? '#ff5a5a' : '#ffb0ff'); Audio2.sfx('EVENT', 0.7); Audio2.ui('level', 0.7);
    const S = Store.data; S.uniques = S.uniques || {}; S.uniques[def.id] = (S.uniques[def.id] || 0) + 1; Store.save();
  },
  // ------------------------------------------------ fusion
  fusionOptions(opts, ownedOnly) {
    // 0.60: as soon as the weapon is maxed (no finales any more, no need to max every spell first)
    const W = this.weapon, F = this.C.fusions; if (ownedOnly || !W || !W.maxed || W.fusion || !F) return;
    // 0.40: only the fusions of the characteristics you have, plus 'Brute' (no characteristic needed: +5 % damage)
    for (const f of F.filter(f => !f.stat || this.passives[f.stat])) opts.push({ kind: 'fusion', id: f.id, lv: 1, w: 3, isNew: true });
  },
  applyFusion(id) {
    const W = this.weapon, f = (this.C.fusions || []).find(x => x.id === id); if (!W || !f) return;
    W.fusion = f; W.recalc(); this.recompute(); Prog.add('fusions');
    if (f.stars) {   // Sagesse: stars orbiting the character (a little spell of their own, for the damage statistics)
      const st = { def: { id: 'fusion_stars', fx: [] }, p: { rotSpeed: 1.6, radius: f.stars.radius, size: 16, knock: 15, star: 1 }, dmg: () => W.dmg() * f.stars.k };
      for (let i = 0; i < f.stars.n; i++) this.orbiters.push({ spell: st, a: i * TAU / f.stars.n, until: Infinity, hit: new Map() });
    }
    const P = this.player, cols = FUSION_PART[f.fx];
    this.announce(L(f.name), T('fusion_done', { w: L(W.def.name), n: L(f.name) }), f.color, { center: true });
    for (let i = 0; i < 4; i++) this.rings.push({ x: P.x, y: P.y, r0: 10, r1: 90 + i * 60, t0: this.time + i * 0.12, dur: 0.7, color: f.color, fill: i === 0 ? 1 : 0 });
    for (let i = 0; i < 90; i++) { const a = rand(TAU), v = rand(80, 360); this.particles.push({ x: P.x, y: P.y - 30, vx: Math.cos(a) * v, vy: Math.sin(a) * v * 0.7 - 80, t: 0, life: rand(0.6, 1.3), c: pick(cols), s: rand(2, 6) }); }
    this.shake(5); Audio2.sfx('EVENT', 0.9); Audio2.ui('level', 0.9); Audio2.play('stars', 0.8);
    const S = Store.data; S.fusions = S.fusions || {}; S.fusions[id] = (S.fusions[id] || 0) + 1; Store.save();
  },
  fusionStats(st) {
    const W = this.weapon, e = W && W.finale;   // a finale's own stats
    if (e && e.stats) for (const k in e.stats) st[k] = (st[k] || 0) + e.stats[k];
    if (W && W.def.leech) st.leech = (st.leech || 0) + W.def.leech[clamp(W.level, 1, W.def.leech.length) - 1];   // 0.48: the vampiric weapons' life steal, by level
    const f = this.weapon && this.weapon.fusion; if (!f || !f.stats) return;
    for (const k in f.stats) { if (k === 'maxhp') st.maxHp *= 1 + f.stats[k]; else if (k === 'dmgK') st.might *= 1 + f.stats[k]; else if (k === 'speed' || k === 'growth') st[k] *= 1 + f.stats[k]; else st[k] = (st[k] || 0) + f.stats[k]; }
  },
  // weapon damage multiplier (Ares's rage)
  weaponK() { return 1 + this.rage; },
  // ------------------------------------------------ each attack / each hit
  onWeaponSwing(sp, x, y, a) {
    const p = sp.p, P = this.player, f = sp.fusion;
    // 0.34: the unique effects scale with their value (the unique weapons' own finales raise them): bolt = number of
    // lightnings, wave / chakram = number of crescents / discs, cloud / firePatch = size, quake = strength
    if (p.bolt) for (let i = 0; i < Math.round(p.bolt); i++) { const m = this.randomMobNear(P.x, P.y, 340); if (m) { this.damageMob(m, sp.dmg() * 0.9, sp); m.stunUntil = Math.max(m.stunUntil, this.time + (m.boss ? 0.1 : 0.4)); this.wfx.push({ k: 'bolt', x: m.x, y: m.y - m.r, t0: this.time, seed: Math.random() * 1000 }); if (!i) Audio2.play('explosion', 0.25, 1.6); } }
    for (let i = 0, n = Math.round(p.wave || 0); i < n; i++) { const aa = a + (i - (n - 1) / 2) * 0.35; this.projs.push({ x: P.x, y: P.y - 22, vx: Math.cos(aa) * 430, vy: Math.sin(aa) * 430, sp: 430, dmg: sp.dmg() * 0.6, pierce: 99, life: 0.75, size: 26, spell: sp, hit: new Set(), crescent: '#a040ff', t0: this.time, delay: 0, ox: P.x, oy: P.y, back: false, bounce: 0 }); }
    for (let i = 0, n = Math.round(p.chakram || 0); i < n; i++) { const aa = a + (i - (n - 1) / 2) * 0.5; this.projs.push({ x: P.x, y: P.y - 22, vx: Math.cos(aa) * 380, vy: Math.sin(aa) * 380, sp: 380, dmg: sp.dmg() * 0.5, pierce: 99, life: 1.6, size: 13, spell: sp, hit: new Set(), boomerang: 1, backAt: 0.45, spin: 1, drawIcon: 'it_5_8', t0: this.time, delay: 0, ox: P.x, oy: P.y, back: false, bounce: 0 }); }
    if (p.cloud) this.zones.push({ x, y, r: 55 * p.cloud * this.stats.area, until: this.time + 2 * this.stats.duration, tick: 0.4, next: 0, dmg: sp.dmg() * 0.18, color: '#8fcf3a', spell: sp, born: this.time, cloud: true, fart: true });
    if (p.firePatch) this.zones.push({ x, y, r: (p.radius || 90) * 0.8 * p.firePatch * this.stats.area, until: this.time + 3 * this.stats.duration, tick: 0.45, next: 0, dmg: sp.dmg() * 0.12, color: '#ff5a1e', spell: sp, born: this.time });
    if (p.quake) { const r = (p.radius || 100) * this.stats.area * 1.7; this.strikes.push({ x, y, r, at: this.time + 0.28, delay: 0.28, dmg: sp.dmg() * 0.55 * p.quake, spell: sp, shake: 4, nofx: true }); this.wfx.push({ k: 'quake', x, y, r, t0: this.time + 0.2 }); }
    if (f && f.fx === 'earth') this.wfx.push({ k: 'crack', x, y, r: 70 * this.stats.area, t0: this.time, seed: Math.random() * 1000 });
    if (f && f.fx === 'air') this.wfx.push({ k: 'gust', x: P.x, y: P.y - 20, a, t0: this.time });
  },
  onWeaponHit(sp, m, d) {
    const p = sp.p, f = sp.fusion;
    // 0.60: the weapons' status effects, the same on every attack (blow, ground blow, projectile)
    if (p.burnW) { m.burnUntil = this.time + 2.5; m.burnDps = Math.max(m.burnDps || 0, d * p.burnW); }
    if (p.slowW && !m.boss) { m.slowUntil = this.time + 1.5; m.slowAmt = Math.max(m.slowUntil > this.time ? m.slowAmt || 0 : 0, p.slowW); }
    if (p.poisonW) this.poisonMob(m, d * p.poisonW / 3 / Math.max(0.01, this.stats.might * this.dmgMul()), 3, sp);
    if (p.bleedW) { m.bleedUntil = this.time + 2.5; m.burnUntil = this.time + 2.5; m.burnDps = Math.max(m.burnDps || 0, d * 0.16 * p.bleedW); }
    if (p.confuse) m.confuseUntil = Math.max(m.confuseUntil || 0, this.time + p.confuse * (m.boss ? 0.2 : 1));
    if (p.stack) { this.rage = Math.min(0.6 * p.stack, this.rage + 0.06 * p.stack); this.rageT = this.time + 3; }
    if (p.cake && Math.random() < p.cake) this.dropPickup('bread', m.x, m.y, this.breadKind());
    if (!f) return;
    if (f.fx === 'fire') { m.burnUntil = this.time + 2.5; m.burnDps = Math.max(m.burnDps || 0, d * 0.25); }
    else if (f.fx === 'water' && !this._splash) {   // a splash around the monster (not chained)
      this._splash = true;
      for (const o of this.mobsInRadius(m.x, m.y, 60 * this.stats.area)) if (o !== m) this.damageMob(o, d * 0.4, sp);
      this._splash = false;
      this.rings.push({ x: m.x, y: m.y, r0: 8, r1: 60 * this.stats.area, t0: this.time, dur: 0.35, color: '#3fa8ff' });
      if (Math.random() < 0.1) this.dropPickup('kama', m.x, m.y, randi(1, 3));
    }
    else if (f.fx === 'life') for (let i = 0; i < 3; i++) this.particles.push({ x: m.x, y: m.y - m.r, vx: rand(-60, 60), vy: rand(-140, -40), t: 0, life: rand(0.5, 0.9), c: pick(FUSION_PART.life), s: rand(2, 4) });
  },
  updateWeapons(dt) {
    if (this.rage > 0 && this.time > this.rageT) this.rage = Math.max(0, this.rage - dt * 0.4);
    for (let i = this.wfx.length - 1; i >= 0; i--) if (this.time - this.wfx[i].t0 > 0.7) this.wfx.splice(i, 1);
    const f = this.weapon && this.weapon.fusion; if (!f) return;
    const P = this.player;
    // the element around the character
    if ((this._fT -= dt) <= 0) {
      this._fT = Game.lowFx ? 0.08 : 0.03; const a = rand(TAU), r = rand(20, 70), cols = FUSION_PART[f.fx];
      const up = f.fx === 'fire' ? -120 : f.fx === 'stars' ? -20 : f.fx === 'water' ? 30 : -50;
      this.particles.push({ x: P.x + Math.cos(a) * r, y: P.y - 20 + Math.sin(a) * r * 0.6, vx: f.fx === 'air' ? -Math.sin(a) * 120 : rand(-20, 20), vy: up + rand(-20, 20), t: 0, life: rand(0.5, 0.9), c: pick(cols), s: rand(3, 6) });
    }
    // Intelligence: the fire aura
    if (f.aura && (this._faT = (this._faT || 0) - dt) <= 0) {
      this._faT = f.aura.tick; const d = this.weapon.dmg() * f.aura.k;
      for (const m of this.mobsInRadius(P.x, P.y, f.aura.radius * this.stats.area)) this.damageMob(m, d, this.weapon, true);
    }
  },
  // ------------------------------------------------ drawing (called by render.js in world space)
  drawWeaponFx(ctx, t, layer) {
    const P = this.player, f = this.weapon && this.weapon.fusion;
    if (layer === 'ground') { if (f) this.drawFusionRing(ctx, t, f); return; }
    this.drawWeaponTop(ctx, t);
  },
  drawFusionRing(ctx, t, f) {
    // the element under the character: a coloured halo, two dashed rings turning opposite ways, the characteristic's
    // glows riding the ring, and the element's own touch (flames, ripples, wind, cracks, stars, leaves)
    const P = this.player, r = f.aura ? f.aura.radius * this.stats.area : 64, rgb = hexRgb(f.color), k = 0.75 + 0.25 * Math.sin(t * 4);
    ctx.save(); ctx.translate(P.x, P.y);
    ctx.save(); ctx.scale(1, 0.55); const g = ctx.createRadialGradient(0, 0, r * 0.2, 0, 0, r);
    g.addColorStop(0, `rgba(${rgb},0)`); g.addColorStop(0.75, `rgba(${rgb},${0.14 * k})`); g.addColorStop(1, `rgba(${rgb},${0.34 * k})`);
    ctx.fillStyle = g; ctx.beginPath(); ctx.arc(0, 0, r, 0, TAU); ctx.fill(); ctx.restore();
    ctx.strokeStyle = f.color; ctx.lineWidth = 3.5; ctx.globalAlpha = 0.9; ctx.setLineDash([14, 9]); ctx.lineDashOffset = -t * 40;
    ctx.beginPath(); ctx.ellipse(0, 0, r, r * 0.55, 0, 0, TAU); ctx.stroke();
    ctx.lineWidth = 2; ctx.globalAlpha = 0.6; ctx.setLineDash([5, 10]); ctx.lineDashOffset = t * 30;
    ctx.beginPath(); ctx.ellipse(0, 0, r * 0.82, r * 0.82 * 0.55, 0, 0, TAU); ctx.stroke(); ctx.setLineDash([]);
    if (f.fx === 'fire') for (let i = 0; i < 12; i++) {   // flame tongues dancing on the ring
      const a = i * TAU / 12 + t * 0.6, x = Math.cos(a) * r, y = Math.sin(a) * r * 0.55, hgt = 16 + 9 * Math.sin(t * 9 + i * 1.7);
      ctx.globalAlpha = 0.85; const fg = ctx.createLinearGradient(0, y, 0, y - hgt); fg.addColorStop(0, '#ff4a12'); fg.addColorStop(0.6, '#ffb02a'); fg.addColorStop(1, 'rgba(255,240,120,0)');
      ctx.fillStyle = fg; ctx.beginPath(); ctx.moveTo(x - 7, y); ctx.quadraticCurveTo(x - 6, y - hgt * 0.6, x + Math.sin(t * 7 + i) * 3, y - hgt); ctx.quadraticCurveTo(x + 6, y - hgt * 0.6, x + 7, y); ctx.closePath(); ctx.fill();
    }
    if (f.fx === 'water') for (let i = 0; i < 2; i++) { const q = ((t * 0.8 + i * 0.5) % 1); ctx.globalAlpha = 0.7 * (1 - q); ctx.strokeStyle = '#bfe8ff'; ctx.lineWidth = 2; ctx.beginPath(); ctx.ellipse(0, 0, r * q, r * q * 0.55, 0, 0, TAU); ctx.stroke(); }
    ctx.globalAlpha = 1;
    for (let i = 0; i < 3; i++) { const a = t * 1.2 + i * TAU / 3, x = Math.cos(a) * r, y = Math.sin(a) * r * 0.55; ctx.drawImage(RCache.glow(f.color), x - 18, y - 18, 36, 36); }   // (0.34: glows only, no characteristic picture)
    ctx.restore();
  },
  drawWeaponTop(ctx, t) {
    const P = this.player;
    if (this.rage > 0.05) { const g = this.rage / 0.6; ctx.save(); ctx.globalAlpha = 0.25 + 0.35 * g; ctx.drawImage(RCache.glow('rgba(255,40,30,0.6)'), P.x - 40 - 20 * g, P.y - 70 - 20 * g, 80 + 40 * g, 80 + 40 * g); ctx.restore(); }
    for (const e of this.wfx) {
      const k = (t - e.t0) / 0.7; if (k < 0) continue;
      ctx.save();
      if (e.k === 'bolt') {   // God Rod: a lightning bolt from the sky
        ctx.lineJoin = 'round'; ctx.beginPath(); let x = e.x, y = e.y - 260; ctx.moveTo(x, y);
        for (let i = 1; i <= 8; i++) { x = e.x + Math.sin(e.seed + i * 2.7) * 22 * (1 - i / 8); y = e.y - 260 + i * 260 / 8; ctx.lineTo(x, y); }
        // (0.95: its gold glow as two wide see-through strokes — a shadow blur sent it to a full-screen 2D layer with PixiJS)
        const lw = 5 * (1 - k) + 1.5; ctx.strokeStyle = '#ffd84a';
        for (const [w, al] of [[lw + 20, 0.12], [lw + 10, 0.22]]) { ctx.globalAlpha = (1 - k) * al; ctx.lineWidth = w; ctx.stroke(); }
        ctx.globalAlpha = 1 - k; ctx.strokeStyle = '#fff6a0'; ctx.lineWidth = lw; ctx.stroke(); ctx.lineWidth = 2; ctx.strokeStyle = '#ffffff'; ctx.stroke();
        ctx.globalAlpha = (1 - k) * 0.7; ctx.drawImage(RCache.glow('rgba(255,240,140,0.8)'), e.x - 40, e.y - 30, 80, 60);
      } else if (e.k === 'quake') {   // Kaiser: the second, wider shockwave
        ctx.globalAlpha = (1 - k) * 0.8; ctx.strokeStyle = '#d8b070'; ctx.lineWidth = 6 * (1 - k) + 1;
        ctx.beginPath(); ctx.ellipse(e.x, e.y, e.r * (0.3 + 0.7 * k), e.r * (0.3 + 0.7 * k) * 0.6, 0, 0, TAU); ctx.stroke();
      } else if (e.k === 'crack') {   // earth fusion: the ground cracks
        ctx.globalAlpha = 1 - k; ctx.strokeStyle = '#5a3e1e'; ctx.lineWidth = 3; ctx.lineCap = 'round';
        for (let i = 0; i < 7; i++) { const a = e.seed + i * TAU / 7; ctx.beginPath(); ctx.moveTo(e.x, e.y); let x = e.x, y = e.y; for (let s = 1; s <= 3; s++) { x += Math.cos(a + Math.sin(e.seed * s + i) * 0.5) * e.r / 3; y += Math.sin(a + Math.sin(e.seed * s + i) * 0.5) * e.r / 3 * 0.6; ctx.lineTo(x, y); } ctx.stroke(); }
      } else if (e.k === 'gust') {   // air fusion: wind lines along the blow
        ctx.globalAlpha = 1 - k; ctx.strokeStyle = '#d8ffe4'; ctx.lineWidth = 2.5; ctx.translate(e.x, e.y); ctx.rotate(e.a);
        for (let i = -1; i <= 1; i++) { ctx.beginPath(); ctx.moveTo(20 + k * 60, i * 14); ctx.bezierCurveTo(60 + k * 80, i * 14 - 10, 100 + k * 80, i * 14 + 10, 150 + k * 90, i * 14); ctx.stroke(); }
      }
      ctx.restore();
    }
  },
});
// a weapon definition: a weapon type or a unique weapon
function weaponById(C, id) { return C.weapons.find(w => w.id === id) || (C.uniqueWeapons || []).find(w => w.id === id) || null; }
// a weapon's type: a unique weapon's `of` (its base weapon), a base weapon's own id (0.95: Bannir bans a whole type)
function weaponType(C, id) { const w = weaponById(C, id); return (w && w.of) || id; }
// a dark crescent (Épée du Dark Vlad's wave), drawn as a projectile
function drawCrescent(ctx, p, t) {
  const a = Math.atan2(p.vy, p.vx), r = p.size * 1.4;
  // (0.95, perf sweep: its glow and gradient sent the frame to a full-screen 2D layer with PixiJS: a picture, RCache.crescent)
  const c = RCache.crescent(p.crescent, r);
  ctx.save(); ctx.translate(p.x, p.y); ctx.rotate(a); ctx.globalAlpha = clamp(p.life / 0.3, 0, 1); ctx.drawImage(c, -c.ox, -c.oy, c.ow, c.oh);
  ctx.restore();
}
// the axe's cleave: a heavy steel crescent with a red edge, sweeping across the hit strip
function drawCleave(ctx, s, t) {
  const k = clamp((t - s.t0) / 0.22, 0, 1), fade = clamp(1 - (t - s.t0 - 0.12) / 0.18, 0, 1), R = s.range, sweep = 1.6;
  ctx.save(); ctx.translate(s.x, s.y + 6); ctx.rotate(s.a); ctx.scale(1, 0.75); ctx.globalAlpha = fade;
  const a1 = -sweep / 2 + sweep * k, a0 = Math.max(-sweep / 2, a1 - 1.0);
  ctx.lineCap = 'round';
  ctx.strokeStyle = 'rgba(200,210,225,0.9)'; ctx.lineWidth = s.width * 0.32; ctx.beginPath(); ctx.arc(0, 0, R * 0.78, a0, a1); ctx.stroke();
  ctx.strokeStyle = 'rgba(255,255,255,0.95)'; ctx.lineWidth = s.width * 0.12; ctx.beginPath(); ctx.arc(0, 0, R * 0.92, a0 + 0.2, a1); ctx.stroke();
  ctx.strokeStyle = 'rgba(220,40,40,0.85)'; ctx.lineWidth = 3; ctx.beginPath(); ctx.arc(0, 0, R * 0.99, a0 + 0.3, a1); ctx.stroke();
  ctx.restore();
}
