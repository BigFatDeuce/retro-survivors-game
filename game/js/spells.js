'use strict';
// ---------------------------------------------------------------- spell runtime
// params(level) = base merged with lv overrides up to that level
function spellParams(def, level) {
  const p = Object.assign({}, def.base);
  for (let i = 0; i < level && i < def.lv.length; i++) Object.assign(p, def.lv[i]);
  return p;
}
const PULSE_LEECH_CAP = 0.12;   // a pulse's life steal heals at most this share of the max HP a wave (ui.js sfStats says it)
// 0.98: every cooldown grows with the run's level, up to C.run.cdLate.lv (50): +fast[1] for a spell whose own cooldown
// (p.cd, its level's) is fast[0] s or less, +slow[1] from slow[0] s, in between on a log scale; applied once, in
// SpellInst.cooldown (spells, weapons, fusions) and menuSpellParams (the menus: a run's first level)
function cdLateK(RUN, cd, level) {
  const L = RUN && RUN.cdLate; if (!L || !(cd > 0)) return 1;
  const f = clamp(Math.log(cd / L.fast[0]) / Math.log(L.slow[0] / L.fast[0]), 0, 1);
  return 1 + (L.fast[1] + (L.slow[1] - L.fast[1]) * f) * Math.min((level || 1) / L.lv, 1);
}
const MAX_SPELL_LV = 4;   // (0.81: spells and weapons have 4 levels, was 6 — patch_081 merged their level steps)
// the attacks whose rhythm ramps up during a run (lasting things — orbits, summons, traps, glyphs, auras, buffs — keep theirs)
const RAMPED = new Set(['projectile', 'strike', 'melee', 'slam', 'line', 'beam', 'cone', 'pulse', 'bomb', 'toss', 'leap', 'dash', 'detonate']);

class SpellInst {
  constructor(run, def) { this.run = run; this.def = def; this.level = 1; this.cd = rand(0.2, 0.8); this.evo = {}; this.state = {}; this.recalc(); }   // (0.96: recalc from the first level: the shop's duration / summons' life / shield bonus only came with the first level-up)
  levelUp() { this.level = Math.min(MAX_SPELL_LV, this.level + 1); this.recalc(); if (this.def.leech) this.run.recompute(); }   // (0.48: a vampiric weapon's life steal goes up with it)
  // weapons: once level 6 is reached, three evolutions (3 ranks each) change the weapon's parameters
  evoUp(id) { this.evo[id] = (this.evo[id] || 0) + 1; this.recalc(); }
  recalc() {
    const p = spellParams(this.def, this.level);
    const E = this.def.weapon && this.run.C.weaponEvo ? this.run.C.weaponEvo[this.def.id] : null;
    if (E) for (const e of E) {
      const r = this.evo[e.id] || 0; if (!r) continue;
      if (e.set) Object.assign(p, e.set);
      if (e.add) for (const k in e.add) p[k] = (p[k] || 0) + e.add[k] * r;
      if (e.mul) for (const k in e.mul) p[k] = (p[k] || 0) * (1 + e.mul[k] * r);
      if (p.dmg) p.dmg *= 1.2;   // every finale also makes the weapon 20% stronger
    }
    const F = this.fusion;   // 0.25: the fused characteristic (weapons.js)
    if (F && F.mul) for (const k in F.mul) if (p[k]) p[k] *= 1 + F.mul[k];
    // 0.34: the shop's spell power works on everything the spell does, not only its damage (damage and heals: dmg() /
    // the heal; here: how long it lasts, its summons' life, its shields; the cooldown: cooldown())
    const sk = this.shopK;
    if (sk > 1) for (const k of ['duration', 'hp', 'armorBuff', 'shield', 'buffDur', 'slowDur', 'stun']) if (typeof p[k] === 'number' && !(k === 'duration' && p.durShop)) p[k] *= sk;   // (0.96: a spell with durShop says its shop duration itself)
    this.p = p;
  }
  get maxed() { return this.level >= MAX_SPELL_LV; }
  // 0.96: the copies Démultiplication and the Craqueleur's belt add (st.amount, beyond the spell's own count) hit
  // at C.run.extraK (0.5): as many things on screen, the damage kept in check
  extraK(i, base = this.p.count || 1) { return i >= base ? (this.run.RUN.extraK || 1) : 1; }
  get icon() { return (this.finale && this.finale.icon) || this.def.icon; }   // a weapon finale has its own skin
  shopT() { return Math.min(1, (this.shopK - 1) / (5 * (this.run.C.spellPer || 0.1))); }   // (0.71: 0 → 1 over the shop's 5 levels)
  cooldown() { const st = this.run.stats, R = this.run; return Math.max(0.1, (this.p.cdShop ? lerp(this.p.cd, this.p.cdShop, this.shopT()) : this.p.cd / (1 + (this.shopK - 1) * 0.5)) * st.cooldown * (R.RUN.cdMul || 1) * (R.hasted && R.hasted() ? 0.5 : 1) * (R.cdRamp && RAMPED.has(this.def.t) ? R.cdRamp() : 1) * cdLateK(R.RUN, this.p.cd, R.level)); }
  // v2.0 spell levels bought in the shop: +10% power per level (damage and heals), class spells only
  get shopK() { if (this._shopK === undefined) { const C = this.run.C, SL = (typeof Store !== 'undefined' && Store.data && Store.data.spellLv) || {}, lv = this.def.weapon ? 0 : this.def.sfusion ? Math.max(...this.def.src.map(k => SL[k] || 0)) : (SL[this.def.id] || 0); this._shopK = 1 + (C.spellPer || 0.1) * lv; } return this._shopK; }   // (0.60: a spell fusion keeps the best shop level of its spells)
  update(dt) {
    const t = this.def.t;
    if (t === 'aura') return this.updateAura(dt);
    this.cd -= dt;
    if (this.cd <= 0) {
      // spells that move the character (Bond, Assaut, Vol de Pièces) can be switched off (Q / A / L / their icon)
      if (this.run.moveOff && (t === 'leap' || t === 'dash')) { this.cd = 0.2; return; }
      const ok = this.cast();
      this.cd = ok === false ? 0.25 : this.cooldown();
      if (ok !== false) this.sound();
    }
  }
  // original spell sound (from the spell's FX clip), or the caster animation's sound, or the weapon's sound
  sound() {
    const R = this.run; if (R.time - (this.lastSnd || -9) < Math.max(0.35, this.cooldown() * 0.9)) return;
    this.lastSnd = R.time;
    let keys = Audio2.spellKeys(this.def);
    if (!keys.length && this.def.anim) keys = Audio2.charSnd(R.charSid, this.def.anim + 'R') || [];
    if (keys.length) Audio2.play(keys[0], this.def.weapon ? 0.6 : 0.5, rand(0.94, 1.06));
  }
  dmg(base) {
    const st = this.run.stats; let d = (base !== undefined ? base : this.p.dmg) * st.might;
    if (this.run.cls.id === 'sacrieur') { const r = 1 - this.run.player.hp / st.maxHp; d *= 1 + 0.6 * r; }
    if (this.def.weapon) d *= (1 + (this.run.C.masteryPer || 0.1) * Math.min((this.run.C.masteryCost || []).length || 10, (Store.data.mastery || {})[this.def.of || this.def.id] || 0)) * this.run.weaponK();   // (0.60: masteryPer 5 %, 5 levels)   // (a unique weapon uses its type's mastery)
    if (this.def.t === 'leap' || this.def.t === 'dash') d *= this.run.RUN.dashMul || 1;
    d *= this.run.RUN.spellDmgMul || 1;   // 0.22: every spell and weapon hits half as hard
    if (this.run.cls.id === 'feca' && !this.def.weapon) d *= this.run.RUN.fecaDmg || 1;
    return d * this.run.dmgMul() * this.shopK;
  }
  playAnim() {
    if (this.p.noanim) return;
    const by = this.def.animBy, R = this.run; R.player.cast((by && by[R.charSid]) || this.def.anim || this.def.animAll || (this.def.glob && R.cls.casts[0]));
  }
  fx() { return FxSheets.get(this.def.fx[0]); }
  // ------------------------------------------------ casting
  cast() {
    const R = this.run, P = R.player, st = R.stats, p = this.p, t = this.def.t;
    switch (t) {
      case 'projectile': return this.castProjectile();
      case 'orbit': {
        const n = p.count + st.amount;
        if (p.perm) { // Faux qui Spin: always there; recast only when the number of scythes changes
          if (this.state.n === n && R.orbiters.some(o => o.spell === this)) return false;   // (no sound every second)
          R.orbiters = R.orbiters.filter(o => o.spell !== this); this.state.n = n;
          for (let i = 0; i < n; i++) R.orbiters.push({ spell: this, a: i * TAU / n, until: Infinity, hit: new Map(), k: this.extraK(i) });
          return true;
        }
        if (this.state.until && R.time < this.state.until) return true;
        const dur = p.duration * st.duration;
        this.state.until = R.time + dur;
        for (let i = 0; i < n; i++) R.orbiters.push({ spell: this, a: i * TAU / n, until: R.time + dur, hit: new Map(), k: this.extraK(i) });
        this.playAnim();
        if (this.def.id === 'bouclier_feca') { P.shieldArmor = { until: R.time + dur, v: this.level }; R.fxAt(802, P.x, P.y + 6, { follow: P, scale: 0.42, sym: 'root' }); }   // 0.22: +1 resistance per level
        this.cdExtra = dur;
        return true;
      }
      case 'zone': {
        const n = p.count + (p.count > 1 ? st.amount : 0);
        const cl = p.target === 'cluster' ? R.pickTargets('cluster', n, 360) : null;
        if (cl && !cl.length) return false;
        for (let i = 0; i < n; i++) {
          let x = P.x, y = P.y;
          if (cl) { const m = cl[i % cl.length]; x = m.x; y = m.y; }
          else if (p.target === 'random' || i > 0) { const m = R.randomMobNear(P.x, P.y, 320); if (m) { x = m.x; y = m.y; } else { x += rand(-80, 80); y += rand(-60, 60); } }
          R.zones.push({ x, y, r: p.radius * st.area, until: R.time + p.duration * st.duration, tick: p.tick, next: 0, dmg: this.dmg() * this.extraK(i), color: p.color, spell: this, born: R.time, slow: p.slow, stun: p.stun, follow: p.follow ? P : null, cloud: p.cloud, fart: p.fart, burn: p.burn, push: p.push, retal: p.retal, dome: p.dome, armor: p.armor });   // (0.89: the Féca's armour / dome)
          if (p.armor || p.dome) { if (this.def.fx[0]) R.fxAt(this.def.fx[0], x, y - 10, { scale: p.radius * st.area / 60, follow: p.follow ? P : null }); R.rings.push({ x, y, r0: 10, r1: p.radius * st.area, t0: R.time, dur: 0.45, color: p.color, fill: 1 }); R.shake(2); }
        }
        this.playAnim(); return true;
      }
      case 'strike': {
        const n = p.single ? 1 : p.count + st.amount;   // (0.98: p.single, one blow on one monster — Attaque Mortelle)
        const targets = R.pickTargets(p.target || 'random', n, p.range || 360);   // (0.98: p.range, a strike's reach — Attaque Mortelle)
        if (!targets.length) return false;
        for (const [ti, tg] of targets.entries()) {
          const x = tg.x + rand(-6, 6), y = tg.y + rand(-6, 6), kd = this.dmg() * this.extraK(ti);
          if (p.fist) { // 0.74: Frappe du Craqueleur — the client's stone fist (fx 212f) falls and smashes (ground at frame ~28 of 20 fps, played ×1.6)
            const r = p.radius * st.area; R.fxAt('212f', x, y, { scale: r / 120, rate: 1.6 });   // (0.76: a third of the size)
            R.strikes.push({ x, y, r, at: R.time + 0.88, delay: 0.88, dmg: kd, spell: this, shake: p.shake || 3, stun: p.stun, nofx: true });
          } else if (p.shovel) { // Pelle Massacrante: the client's giant shovel rises above the target, then crashes down (impact on frame ~25)
            R.fxAt(this.def.fx[0], x, y, { scale: p.radius * st.area / 70, fit: p.radius * st.area });
            R.strikes.push({ x, y, r: p.radius * st.area, at: R.time + 1.2, delay: 1.2, dmg: kd, spell: this, shake: 5, nofx: true });
          } else if (p.single) R.strikes.push({ x: tg.x, y: tg.y, r: tg.r * 1.2, tgt: tg, bossK: p.bossK, at: R.time, delay: 0, dmg: kd, spell: this });   // (it hits its monster alone; 0.98.1: at once — no delay to step out of, no mark on the ground)
          else R.strikes.push({ x, y, r: p.radius * st.area, at: R.time + p.delay, delay: p.delay, dmg: kd, spell: this, gamble: p.gamble, shake: p.shake, slow: p.slow, slowDur: p.slowDur, mark: p.mark, markDur: p.markDur, stun: p.stun, rock: p.rock, transmute: p.transmute, gold: p.gold });
        }
        this.playAnim(); return true;
      }
      case 'line': { // Flèche Enflammée: a fire arrow sets the whole line in the facing direction ablaze
        const n = p.count + Math.min(1, st.amount);
        // 0.37: aimed along the line that holds the most monsters (24 directions tried); the extra arrows go left and right of it
        const len = p.length * st.projspeed, w = p.width * st.area, near = R.mobsInRadius(P.x, P.y - 20, len);
        let base = P.faceAng, best = 0;
        for (let k = 0; k < 24 && near.length; k++) {
          const a = k / 24 * TAU, ca = Math.cos(a), sa = Math.sin(a); let c = 0;
          for (const m of near) { if (m.dying) continue; const ox = m.x - P.x, oy = m.y - P.y + 20, al = ox * ca + oy * sa; if (al > 0 && al < len && Math.abs(-ox * sa + oy * ca) < w / 2 + m.r) c++; }
          if (c > best) { best = c; base = a; }
        }
        for (let i = 0; i < n; i++) {
          const a = base + Math.ceil(i / 2) * (i % 2 ? 1 : -1) * 0.32;
          R.beams.push({ x: P.x, y: P.y - 20, a, len: p.length * st.projspeed, w: p.width * st.area, until: R.time + 0.7, t0: R.time, dmg: this.dmg() * this.extraK(i), burn: p.burn, knock: p.knock, spell: this, done: false, fire: !p.wave, wave: !!p.wave });
          // 0.61: Vague à Lame as the client casts it: its clip 1210 ('duplicate', a breaking wave) on every cell of the line,
          // one after the other from the Pandawa outwards, facing where it goes
          if (p.wave && this.def.fx[0]) { const L_ = p.length * st.projspeed, n = Math.max(3, Math.round(L_ / 52)); for (let k = 1; k <= n; k++) { const d = L_ * k / n; R.fxAt(this.def.fx[0], P.x + Math.cos(a) * d, P.y + Math.sin(a) * d * 0.9, { scale: 0.6 * Math.sqrt(st.area), delay: k * 0.035, flip: Math.cos(a) < 0 }); } }
        }
        P.faceTo(Math.cos(base)); this.playAnim(); return true;
      }
      case 'dash': { // Vol de Pièces: dash through the enemies and steal their kamas
        const tg = R.nearestMob(P.x, P.y, p.dist * 1.6);
        if (!tg) return false;
        const a = Math.atan2(tg.y - P.y, tg.x - P.x), len = p.dist * st.area;
        const x0 = P.x, y0 = P.y, x1 = P.x + Math.cos(a) * len, y1 = P.y + Math.sin(a) * len;
        P.dash = { t: 0, dur: 0.18, dx: Math.cos(a), dy: Math.sin(a), sp: len / 0.18 }; P.invulnUntil = Math.max(P.invulnUntil, R.time + 0.18 + 0.2);   // 0.37: untouchable during the dash and 0.2 s after
        P.faceTo(Math.cos(a));
        // each monster killed by the dash: 10% chance to steal 1 kama, at most 1 kama per cast
        let stolen = false;
        for (const m of R.mobsInRadius((x0 + x1) / 2, (y0 + y1) / 2, len / 2 + 30)) {
          if (segDist(m.x, m.y, x0, y0, x1, y1) > p.width / 2 * st.area + m.r) continue;
          const alive = !m.dying;
          this._hitKind = 'dash'; R.damageMob(m, this.dmg(), this); this._hitKind = null;
          { const along = clamp(((m.x - x0) * Math.cos(a) + (m.y - y0) * Math.sin(a)) / len, 0, 1); setTimeout(() => { if (!R.over) R.hitSfx('dash'); }, along * 180); }   // (0.84: one impact per monster crossed, when the dash reaches it, + a tiny hit-stop)
          if (alive && m.dying && !stolen && Math.random() < (p.steal1 || 0.1)) {
            stolen = true; R.kamas += 1; if (R.ps) R.ps.kamas = (R.ps.kamas || 0) + 1;
            R.text(m.x, m.y - m.r * 2.6 - 22, '+1 K', '#ffd700', 15); Audio2.blip('coin');
          }
        }
        Audio2.play('dodge_607b', 0.5, rand(0.95, 1.1));
        if (this.def.fx[0]) R.fxAt(this.def.fx[0], x1, y1, { scale: 0.8 });
        this.playAnim(); return true;
      }
      case 'leap': { // Bond: jump into the densest group and slam the ground on landing
        const tg = R.pickTargets('cluster', 1, p.range * st.area)[0];
        if (!tg) return false;
        const b = R.bounds, x1 = clamp(tg.x, b.x0, b.x1), y1 = clamp(tg.y, b.y0, b.y1);
        P.leap = { t: 0, dur: 0.42, x0: P.x, y0: P.y, x1, y1, spell: this };
        P.invulnUntil = Math.max(P.invulnUntil, R.time + 0.42 + 0.2);   // 0.37: untouchable in the air and 0.2 s after landing
        P.faceTo(x1 - P.x); this.playAnim(); Audio2.play('saut', 0.5, rand(0.95, 1.1));
        return true;
      }
      case 'slam': { // hammer / shovel: a blow on the ground in front of you
        const tg = R.nearestMob(P.x, P.y, p.reach + p.radius * 1.4);
        const a = tg ? Math.atan2(tg.y - P.y, tg.x - P.x) : (P.flip ? Math.PI : 0);
        const rch = p.reach * (this.def.weapon ? st.wreach : 1), cx = P.x + Math.cos(a) * rch, cy = P.y + Math.sin(a) * rch * 0.7, r = p.radius * st.area;   // (0.84: Portée: the blow lands further)
        const hits = R.mobsInRadius(cx, cy, r);
        for (const m of hits) {
          const d = this.dmg(); R.damageMob(m, d, this); if (this.def.weapon) R.onWeaponHit(this, m, d);
          if (p.stun) m.stunUntil = Math.max(m.stunUntil, R.time + p.stun * (m.boss ? 0.2 : 1));
          if (p.knock && !m.boss) { const dx = m.x - cx, dy = m.y - cy, d = Math.hypot(dx, dy) || 1; m.kx += dx / d * p.knock * 4; m.ky += dy / d * p.knock * 4; }
        }
        if (p.dig && hits.length && Math.random() < p.dig) R.dropPickup('kama', cx + rand(-15, 15), cy + rand(-10, 10), randi(1, 3 + R.mapIdx));
        R.rings.push({ x: cx, y: cy, r0: r * 0.5, r1: r, t0: R.time, dur: this.def.weapon ? 0.8 : 0.48, color: this.def.weapon && typeof weaponRgb === 'function' ? '#' + weaponRgb(this).split(',').map(v => (+v).toString(16).padStart(2, '0')).join('') : '#ffaa33', fill: 1, crack: !!this.def.weapon });   // (0.90: the weapon's colour, the ground split)
        if (this.def.weapon) for (let k = 0; k < 14; k++) { const an = rand(TAU), v = rand(90, 240); R.particles.push({ x: cx + rand(-8, 8), y: cy, vx: Math.cos(an) * v, vy: -rand(140, 320), g: 900, t: 0, life: rand(0.45, 0.8), s: rand(3, 6.5), c: pick(['#8a6a44', '#a88a5a', '#6a4e30', '#c8b08a']) }); }   // (debris)
        R.fxAt(this.def.fx[0], cx, cy, { scale: r / 90, fit: r }); R.shake(this.def.weapon ? 4 : 2.5);
        if (this.def.weapon) R.onWeaponSwing(this, cx, cy, a);
        P.faceTo(Math.cos(a)); this.playAnim(); return true;
      }
      case 'melee': return this.castMelee();
      case 'toss': { // Karcham: lift the nearest enemy (bosses are too heavy: headbutt instead)
        const r = p.range * st.area;
        let best = null, bd = r * r;
        for (const m of R.mobsInRadius(P.x, P.y, r)) { if (m.boss || m.carried || m.dying) continue; const d = dist2(m.x, m.y, P.x, P.y); if (d < bd) { bd = d; best = m; } }
        if (!best) {
          const bm = R.nearestMob(P.x, P.y, r); if (!bm) return false;
          R.damageMob(bm, this.dmg() * 1.2, this); R.fxAt(this.def.fx[0], bm.x, bm.y, {}); P.faceTo(bm.x - P.x); this.playAnim(); return true;
        }
        best.carried = true; best.liftH = 0;
        R.tosses.push({ m: best, t0: R.time, lift: p.lift, phase: 'lift', dmg: this.dmg(), aoe: p.aoe * st.area, throw: p.throw * st.projspeed, knock: p.knock, spell: this, sx: best.x, sy: best.y });
        P.faceTo(best.x - P.x); this.playAnim(); return true;
      }
      case 'bomb': {
        const n = p.count + st.amount;
        const tgs = R.pickTargets('nearest', n, p.range * st.projspeed + 40);
        if (!tgs.length) return false;
        for (let i = 0; i < n; i++) { const m = tgs[i % tgs.length]; R.throwBomb(this, m.x + rand(-28, 28), m.y + rand(-18, 18), { dmg: this.dmg() * this.extraK(i) }); }
        P.faceTo(tgs[0].x - P.x); this.playAnim(); return true;
      }
      case 'detonate': {
        const live = R.bombs.filter(b => !b.done && !b.boomAt);
        if (live.length) live.forEach((b, k) => R.detonate(b, 1 + p.bonus, k * 0.05));
        else { const m = R.nearestMob(P.x, P.y, 320); if (!m) return false; R.throwBomb(this, m.x, m.y, { fuse: 0.25, fly: 0.3, dmg: this.dmg(), r: p.radius }); P.faceTo(m.x - P.x); }
        this.playAnim(); return true;
      }
      case 'beam': {
        const n = p.count + Math.min(1, st.amount);
        const tg = R.nearestMob(P.x, P.y, 420);
        let ang = tg ? Math.atan2(tg.y - P.y, tg.x - P.x) : P.faceAng;
        for (let i = 0; i < n; i++) {
          const a = ang + (i - (n - 1) / 2) * 0.5;
          R.beams.push({ x: P.x, y: P.y - 18, a, len: p.length * st.projspeed, w: p.width * st.area, until: R.time + 0.35, dmg: this.dmg() * this.extraK(i), color: p.color || '#fff', spell: this, done: false, dup: p.dup });
          // 0.60: Rayon Obscur as the client casts it: its clip 805 ('duplicate') on every cell of the line, a wave
          // running from the Xélor to the end of the ray
          if (p.dup && this.def.fx[0]) { const L_ = p.length * st.projspeed, n = Math.max(3, Math.round(L_ / 46)); for (let k = 1; k <= n; k++) { const d = L_ * k / n; R.fxAt(this.def.fx[0], P.x + Math.cos(a) * d, P.y + Math.sin(a) * d * 0.9, { scale: 0.55 * Math.sqrt(st.area), delay: k * 0.028 }); } }
        }
        this.playAnim(); return true;
      }
      case 'summon': {
        const own = p.count + (R.cls.id === 'osamodas' ? 1 : 0);   // (the Osamodas's +1 is his own: full damage)
        let n = own + st.amount;
        const mine = R.summons.filter(s => s.spell === this).length;
        n = Math.max(0, Math.min(n, (p.count + st.amount + 2) - mine));
        if (!n) return true;
        for (let i = 0; i < n; i++) R.spawnSummon(this, P.x + rand(-40, 40), P.y + rand(-30, 30), this.extraK(mine + i, own));
        this.playAnim(); return true;
      }
      case 'trap': {
        while (R.traps.length >= p.max) R.traps.shift();   // (0.98: one trap a cast; p.max on the ground for every trap spell together — the Piège Sournois 1, the oldest goes)
        R.traps.push({ x: P.x, y: P.y, r: p.radius * st.area, dmg: this.dmg(), gas: p.gas ? this.dmg(p.gas) : 0, spell: this, until: R.time + p.duration * st.duration, armed: R.time + 0.4 });
        return true;
      }
      case 'heal': {
        let h = p.heal * (R.cls.id === 'eniripsa' ? 1.3 : 1) * (1 + st.healBonus) * this.shopK;
        if (P.hp >= st.maxHp && !p.armorBuff) return false;
        P.heal(h);
        if (p.armorBuff) P.tempArmor = { until: R.time + p.buffDur * st.duration, v: p.armorBuff };
        // 0.68 (Lait de Bambou): every debuff of the monsters / the ground goes, faster for a while, immune to them a moment
        if (p.haste) P.haste = { until: R.time + p.buffDur * st.duration, v: p.haste };
        if (p.cleanse) R.cleanse(Math.min(1.5, p.cleanse * st.duration));
        R.fxAt(this.def.fx[0], P.x, P.y - 10, { follow: P });
        this.playAnim(); return true;
      }
      case 'buff': {
        const dur = (p.durShop ? lerp(p.duration, p.durShop, this.shopT()) : p.duration || 0) * st.duration;   // (0.96: durShop, the Immunité's 1.5 -> 2 s over the shop)
        if (p.buff === 'immune') { P.invulnUntil = Math.max(P.invulnUntil, R.time + dur); P.immuneUntil = R.time + dur; R.text(P.x, P.y - 80, T('immune'), '#ffe27a', 14); }
        else if (p.buff === 'mutate') {   // 0.91: Élixir de Mutation (the Otomaï): bigger, stronger, faster for a while (dmgMul, playerSpeedK, Player.draw)
          R.mutate = { until: R.time + dur, t0: R.mutate && R.time < R.mutate.until ? R.mutate.t0 : R.time, power: p.power, haste: p.haste };
          R.text(P.x, P.y - 92, T('mutate'), '#9be86a', 15); R.rings.push({ x: P.x, y: P.y, r0: 20, r1: 150, t0: R.time, dur: 0.5, color: '#7ed957', fill: 1 }); R.shake(2);
        }
        else if (p.buff === 'rally') { R.rally = { until: R.time + dur, bonus: p.bonus }; R.text(P.x, P.y - 80, T('rally'), '#ffb26a', 14); R.rings.push({ x: P.x, y: P.y, r0: 20, r1: 160, t0: R.time, dur: 0.5, color: '#ffb26a' }); }
        else if (p.buff === 'fortune') { const c = Math.min(P.hp - 1, P.hp * p.cost); if (c > 0) P.hp -= c; R.fortune = { until: R.time + dur, bonus: p.bonus }; R.text(P.x, P.y - 80, T('fortune'), '#ffd24a', 15); }
        else if (p.buff === 'pandora') {
          if (P.hp < st.maxHp * 0.7 || Math.random() < 0.5) { P.heal(st.maxHp * p.heal * (1 + st.healBonus)); R.text(P.x, P.y - 92, T('pandora_heal'), '#7dff9a', 13); }
          else { R.pandora = { until: R.time + dur, crit: p.crit }; R.text(P.x, P.y - 92, T('pandora_crit'), '#ffcf3a', 13); }
        }
        else P.invisUntil = R.time + dur;
        if (this.def.fx[0]) R.fxAt(this.def.fx[0], P.x, P.y, { follow: P });
        this.playAnim(); return true;
      }
      case 'pulse': {
        const r = p.radius * st.area;
        const mobs = R.mobsInRadius(P.x, P.y, r);
        if (!mobs.length && (p.knock > 0 || p.leech || p.allOrNothing)) return false;
        let k = 1;
        if (p.allOrNothing) { // Tout ou Rien: a huge wave, or a little heal
          if (Math.random() < 0.6) { k = 1.5; R.text(P.x, P.y - 86, T('all_win'), '#ffd24a', 16); R.shake(4); }
          else { k = 0.3; P.heal(st.maxHp * p.heal * (1 + st.healBonus)); R.text(P.x, P.y - 86, T('all_lose'), '#7dff9a', 12); }
        }
        let drained = 0;
        for (const m of mobs) {
          const before = m.hp; R.damageMob(m, this.dmg() * k, this); drained += Math.max(0, before - Math.max(0, m.hp));
          const dx = m.x - P.x, dy = m.y - P.y, d = Math.hypot(dx, dy) || 1;
          const kb = p.knock * (m.def.kb !== undefined ? m.def.kb : 1) * (m.boss ? 0.15 : 1);
          if (p.knock < 0) { const pull = Math.min(-p.knock, d - 20); m.kx += dx / d * -pull * 4; m.ky += dy / d * -pull * 4; }
          else { m.kx += dx / d * kb * 4; m.ky += dy / d * kb * 4; }
          if (p.stun) m.stunUntil = Math.max(m.stunUntil, R.time + p.stun * (m.boss ? 0.2 : 1));
        }
        if (p.leech && drained > 0) P.leechHeal(Math.min(st.maxHp * PULSE_LEECH_CAP, drained * p.leech * (1 + st.healBonus)));
        R.rings.push({ x: P.x, y: P.y, r0: 10, r1: r, t0: R.time, dur: 0.48, color: p.color || (p.leech ? '#e0204a' : p.knock < 0 ? '#e04a2b' : '#ffcc33'), fill: 1 });   // (0.79: each class's own colour, content)
        R.fxAt(this.def.fx[0], P.x, P.y, { fit: r });
        if (p.shake) R.shake(p.shake);
        this.playAnim(); return true;
      }
      case 'pioche': this.playAnim(); return R.pickaxe(this);
      case 'wheel': return true;
      case 'cawotte': this.playAnim(); return R.cawotte(this);   // (0.71: gspells.js)
      case 'pwcawotte': this.playAnim(); return R.pwcawotte(this);   // (0.95: the Pwout de Cawotte + Cawotte fusion, gspells.js)
      case 'cone': {
        const tg = R.nearestMob(P.x, P.y, p.range * 1.6);
        const ang = tg ? Math.atan2(tg.y - P.y, tg.x - P.x) : P.faceAng;
        P.faceTo(Math.cos(ang));
        R.cones.push({ x: P.x, y: P.y - 20, a: ang, range: p.range * st.area, half: p.angle * 0.5, ticks: p.ticks, next: R.time, dt: 0.12, dmg: this.dmg(), spell: this, confuse: p.confuse, knock: p.knock, until: R.time + p.ticks * 0.12 + 0.2, t0: R.time, color: p.blast ? '#ffd28a' : null });
        if (p.blast) { R.shake(2); for (let i = 0; i < 14; i++) R.particles.push({ x: P.x + Math.cos(ang) * 30, y: P.y - 20 + Math.sin(ang) * 20, vx: Math.cos(ang + rand(-0.4, 0.4)) * rand(150, 380), vy: Math.sin(ang + rand(-0.4, 0.4)) * rand(150, 380) - 40, t: 0, life: 0.35, c: pick(['#ffcf6a', '#ff8a2a', '#5a4a3a']), s: rand(2, 4) }); }
        R.fxAt(this.def.fx[0], P.x + Math.cos(ang) * 40, P.y - 20 + Math.sin(ang) * 30, {});
        this.playAnim(); return true;
      }
    }
    return true;
  }
  castProjectile() {
    const R = this.run, P = R.player, st = R.stats, p = this.p;
    const n = p.count + st.amount;
    let targets = [];
    if (p.target === 'facing') {
      const tg = R.nearestMob(P.x, P.y, 300);
      const a = tg ? Math.atan2(tg.y - P.y, tg.x - P.x) : P.faceAng;
      for (let i = 0; i < n; i++) targets.push({ a: a + (n > 1 ? (i - (n - 1) / 2) * (p.spread || 0.3) / Math.max(1, (n - 1) / 2) * 0.5 * 2 : 0) });
    } else {
      const mobs = R.pickTargets(p.target === 'random' ? 'random' : p.target === 'strongest' ? 'strongest' : 'nearest', n, 520 * st.projspeed);
      if (!mobs.length) return false;
      for (let i = 0; i < n; i++) {
        const m = mobs[i % mobs.length];
        const spread = mobs.length < n ? (i - (n - 1) / 2) * 0.18 : 0;
        targets.push({ a: Math.atan2(m.y - P.y, m.x - P.x) + spread, m });
      }
    }
    const sp = p.speed * st.projspeed;
    targets.forEach((tg, i) => {
      const vx = Math.cos(tg.a) * sp, vy = Math.sin(tg.a) * sp;
      const pr = {
        x: P.x, y: P.y - 22, vx, vy, sp, dmg: this.dmg() * this.extraK(i), pierce: p.pierce, life: p.life * st.projspeed, size: p.size * Math.sqrt(st.area),
        spell: this, hit: new Set(), homing: p.homing, target: tg.m, boomerang: p.boomerang, bounce: p.bounce || 0,
        aoe: p.aoe ? p.aoe * st.area : 0, chaos: p.chaos, trail: p.chaos ? [] : null, tint: p.tint, slow: p.slow, slowDur: p.slowDur, burn: p.burn, gamble: p.gamble, arrow: p.arrow, spin: p.spin, stone: p.stone, dagger: p.dagger, ice: p.ice,
        lob: p.lob, puddle: p.puddle, puddleColor: p.puddleColor, puddlePoison: p.puddlePoison, puddleDur: p.puddleDur, poison: p.poison, poisonDur: p.poisonDur, knock: p.knock, push: p.push, leech: p.leech, drawIcon: p.drawIcon, coins: p.coins, col: p.col, backAt: p.backAt,
        curve: p.curve ? p.curve * rand(0.6, 1.1) * (Math.random() < 0.5 ? -1 : 1) : 0, t0: R.time, delay: i * 0.05, ox: P.x, oy: P.y, back: false,
      };
      if (p.lob && tg.m) { pr.lobTo = { x: tg.m.x, y: tg.m.y }; pr.lobT = 0; pr.lobDur = Math.max(0.35, Math.hypot(tg.m.x - P.x, tg.m.y - P.y) / sp); }
      R.projs.push(pr);
    });
    P.faceTo(Math.cos(targets[0].a));
    if (this.def.weapon) R.onWeaponSwing(this, P.x, P.y, targets[0].a);
    if (!p.noanim) this.playAnim();
    return true;
  }
  castMelee() {
    const R = this.run, P = R.player, st = R.stats, p = this.p;
    const tg = R.nearestMob(P.x, P.y, p.range * 2.2);
    let base = tg ? Math.atan2(tg.y - P.y, tg.x - P.x) : (P.flip ? Math.PI : 0);
    if (!tg && !this.def.id.startsWith('griffe')) base = P.flip ? Math.PI : 0;
    P.faceTo(Math.cos(base));
    const dirs = [base];
    if (p.sides >= 2) dirs.push(base + Math.PI);
    if (p.sides >= 4) { dirs.push(base + Math.PI / 2); dirs.push(base - Math.PI / 2); }
    if (p.cross) { /* Épée de Iop: cross pattern at the end of the blade */ }
    const range = p.range * st.area * (this.def.weapon ? st.wreach : 1), width = p.width * st.area;   // (0.84: Portée lengthens a weapon's blow, not its width)
    dirs.forEach((a, k) => {
      R.slashes.push({ x: P.x, y: P.y - 18, a, range, width, at: R.time + k * 0.08, done: false, dmg: this.dmg(), spell: this, t0: R.time + k * 0.08, crit: p.crit, stun: p.stun, leech: p.leech, cross: p.cross, knock: p.knock, bleed: p.bleed, burn: p.burn, poison: p.poison, poisonDur: p.poisonDur, cleave: p.cleave });
    });
    if (this.def.weapon) R.onWeaponSwing(this, P.x + Math.cos(base) * range * 0.7, P.y + Math.sin(base) * range * 0.5, base);
    this.playAnim();
    return true;
  }
  updateAura(dt) {
    const R = this.run, P = R.player, st = R.stats, p = this.p;
    this.state.t = (this.state.t || 0) - dt;
    if (this.state.t > 0) return;
    this.state.t = p.tick;
    const r = p.radius * st.area;
    for (const m of R.mobsInRadius(P.x, P.y, r)) {
      R.damageMob(m, this.dmg(), this, true);
      if (p.slow) { m.slowUntil = R.time + 0.6; m.slowAmt = Math.max(m.slowAmt || 0, p.slow); }
      if (p.mark) { m.markAmt = Math.max(m.markUntil > R.time ? m.markAmt || 0 : 0, p.mark); m.markUntil = R.time + p.tick + 0.3; }   // (0.91: Brume Mutagène: the monsters in it take more damage)
    }
  }
}

