'use strict';
// colours of the fireworks thrown when a Dofus falls (the Dofus and the game's elements)
const FW_COLS = ['#ff4d4d', '#ff9f1a', '#ffe14a', '#9cff6a', '#3ccf5a', '#3fd0ff', '#4f6bff', '#b05cff', '#ff5fb0', '#ffffff', '#ffd9a0', '#5af2c8'];
// ---------------------------------------------------------------- spatial hash
// (0.95: the cells' arrays are kept and emptied each frame, not rebuilt: no garbage for the collector in a crowd)
class Grid {
  constructor(cell) { this.cell = cell; this.map = new Map(); this.used = []; }
  clear() { for (const a of this.used) a.length = 0; this.used.length = 0; }
  key(cx, cy) { return (cx + 4096) * 8192 + (cy + 4096); }
  add(o) {
    const k = this.key(Math.floor(o.x / this.cell), Math.floor(o.y / this.cell));
    let a = this.map.get(k); if (!a) { a = []; this.map.set(k, a); } if (!a.length) this.used.push(a); a.push(o);
  }
  query(x, y, r, out) {
    out.length = 0;
    const c = this.cell, x0 = Math.floor((x - r) / c), x1 = Math.floor((x + r) / c), y0 = Math.floor((y - r) / c), y1 = Math.floor((y + r) / c);
    for (let cx = x0; cx <= x1; cx++) for (let cy = y0; cy <= y1; cy++) {
      const a = this.map.get(this.key(cx, cy)); if (a) for (const o of a) out.push(o);
    }
    return out;
  }
}
// neighbour buffers of Grid.query. 0.59: the loops that hurt monsters while they walk the result have their own (damageMob,
// onWeaponHit — the water fusion's splash —, a bouncing projectile's nearestOther refill _q and cut the walk short)
const _q = [], _qProj = [], _qSlash = [], _qOrb = [];
// 0.61 (the Féca shield's circles looked unevenly spaced): orbiters go round an ellipse (r x 0.6 r) and equal angles
// bunched them on its sides; ellAngle maps an orbiter's angle to the ellipse angle at the same share of the perimeter, so
// they keep even gaps and an even speed on screen (one table, made once)
const ELL_Q = 0.6, ELL_N = 720, _ellT = (() => {
  const n = 4096, len = new Float64Array(n + 1);
  for (let i = 1; i <= n; i++) { const a0 = (i - 1) / n * TAU, a1 = i / n * TAU; len[i] = len[i - 1] + Math.hypot(Math.cos(a1) - Math.cos(a0), ELL_Q * (Math.sin(a1) - Math.sin(a0))); }
  const tot = len[n], out = new Float64Array(ELL_N + 1); let j = 0;
  for (let k = 0; k <= ELL_N; k++) { const s = k / ELL_N * tot; while (j < n - 1 && len[j + 1] < s) j++; const f = (s - len[j]) / ((len[j + 1] - len[j]) || 1); out[k] = Math.min(1, (j + f) / n) * TAU; }
  return out;
})();
function ellAngle(a) { const turn = Math.floor(a / TAU), x = (a / TAU - turn) * ELL_N, i = Math.min(ELL_N - 1, Math.floor(x)); return turn * TAU + _ellT[i] + (_ellT[i + 1] - _ellT[i]) * (x - i); }

// ---------------------------------------------------------------- player
class Player {
  constructor(run, sprite) {
    this.run = run; this.sprite = sprite; this.x = 0; this.y = 0; this.vx = 0; this.vy = 0;
    this.hp = 100; this.flip = false; this.view = 'R'; this.anim = 'staticR'; this.at = 0; this.castAnim = null; this.castT = 0;
    this.faceAng = 0; this.lastHit = -10; this.hitFlash = 0; this.invisUntil = 0; this.shieldNext = 0; this.shieldUp = false;
    this.tempArmor = null; this.shieldArmor = null; this.dead = false; this.deathT = 0; this.moving = false;
    this.dodgeReady = 0; this.dash = null; this.invulnUntil = 0; this.inWater = false; this.eatT = 0; this.trail = [];
    this.lastDx = 1; this.lastDy = 0; this.lastMoveT = -9; this.leap = null; this.leapH = 0; this.immuneUntil = 0;
  }
  faceTo(cx) { if (Math.abs(cx) > 0.15) this.flip = cx < 0; }
  cast(anim) {
    if (!anim || this.eatT > 0) return;
    let key = anim + this.view;
    if (!this.sprite.has(key)) key = anim + 'R';
    if (!this.sprite.has(key)) return;
    this.castAnim = key; this.castT = 0;
  }
  // 0.91: the shadow and the blue ring are drawn with the areas on the ground (Run.groundFx): the scenery in
  // front of the character covers them too
  drawFloor(ctx) {
    const R = this.run;
    // shadow (or ripples in water)
    if (this.inWater) {
      for (let i = 0; i < 2; i++) { const k = ((R.time * 0.9 + i * 0.5) % 1); ctx.globalAlpha = 1 - k; ringAt(ctx, 'rgba(220,240,255,0.55)', this.x, this.y, 16 + k * 14, 6 + k * 6, 1.5); }
      ctx.globalAlpha = 1;
    } else { ctx.fillStyle = 'rgba(0,0,0,0.25)'; ctx.beginPath(); ctx.ellipse(this.x, this.y, 20, 9, 0, 0, TAU); ctx.fill(); }
    if (!this.dead) ringAt(ctx, R.time < this.invulnUntil ? 'rgba(200,240,255,0.95)' : 'rgba(80,170,255,0.75)', this.x, this.y, 22, 10, 2.5);   // (0.95: pictures, render.js ringAt: PixiJS draws them itself)
  }
  // bread: the class "eat" emote (bread in hands) for a moment
  eat() {
    const a = (this.run.cls.eatAnim || this.run.C.eat.anim || 'emote17') + 'R';   // (0.91: the Otomaï drinks from his bag, anim4)
    const k = this.sprite.has(a) ? a : this.sprite.has('bonusR') ? 'bonusR' : null;
    if (!k) return;
    this.castAnim = k; this.castT = 0; this.eatT = Math.min(1.5, this.sprite.duration(k) / (this.run.cls.castRate || 1));
  }
  // dodge: a quick dash with a moment of invincibility (Space / double tap / LT-RT)
  dodge() {
    const R = this.run, D = R.C.dodge;
    if (this.dead || R.over || R.time < this.dodgeReady || this.dash) return false;
    const iv = arguments.length >= 2 ? { x: arguments[0], y: arguments[1] } : Input.vector(); let dx = iv.x, dy = iv.y; let l = Math.hypot(dx, dy);
    if (l < 0.2) { dx = this.vx; dy = this.vy; l = Math.hypot(dx, dy); }
    if (l < 1e-3 || (l < 0.2 && R.time - this.lastMoveT > 0.6)) { if (R.time - this.lastMoveT < 1.5) { dx = this.lastDx; dy = this.lastDy; } else { dx = this.flip ? -1 : 1; dy = 0; } }
    else { dx /= l; dy /= l; }
    const bt = R.batofuUntil > R.time && R.C.batofu, bd = bt ? bt.dist : 1, bc = bt ? bt.cd : 1;   // Plume du Batofu: longer, quicker dashes
    this.dash = { t: 0, dur: D.dur, dx, dy, sp: D.dist * bd / D.dur };
    this.dodgeReady = R.time + D.cd * bc * (R.stats.dashCd || 1); this.invulnUntil = R.time + D.inv; this.dashNotified = false;
    if (Math.abs(dx) > 0.15) this.flip = dx < 0;
    Audio2.play(D.snd || 'dodge_604', 0.7, rand(0.95, 1.08));
    for (let i = 0; i < 10; i++) R.particles.push({ x: this.x + rand(-12, 12), y: this.y - rand(0, 40), vx: -dx * rand(40, 120), vy: -dy * rand(40, 120) - 30, t: 0, life: 0.35, c: '#cfe9ff', s: rand(2, 4) });
    if (R.ps) R.ps.dodges++;
    return true;
  }
  // 0.34: life steal too small to heal a whole HP is stored and given back 1 HP at a time (every hit counts)
  leechHeal(v) {
    if (!(v > 0) || this.dead) return;
    this._lpool = (this._lpool || 0) + v; if (this._lpool < 1) return;
    const n = Math.floor(this._lpool); this._lpool -= n; const before = this.hp; this.heal(n, true);
    if (this.hp > before) { this._lshow = (this._lshow || 0) + (this.hp - before); if (!this._lshowT || this.run.time - this._lshowT > 0.6) { this.run.text(this.x + 18, this.y - 70, '+' + Math.round(this._lshow), '#e0506a', 13); this._lshow = 0; this._lshowT = this.run.time; } }
  }
  heal(h, quiet) {
    const st = this.run.stats; const before = this.hp;
    this.hp = Math.min(st.maxHp, this.hp + h);
    const d = this.hp - before;
    if (d >= 1 && !quiet) this.run.healText(d);
    return d;
  }
  update(dt, input) {
    const R = this.run, st = R.stats;
    if (this.dead) { this.deathT += dt; return; }
    let mx = input.x, my = input.y;
    const len = Math.hypot(mx, my);
    if (len > 1) { mx /= len; my /= len; }
    this.inWater = R.isWater(this.x, this.y);
    const sp = 157.5 * st.speed * (this.inWater && !R.cleansed() ? 1 -(R.C.water ? R.C.water.slow : 0.3) : 1) * R.playerSpeedK();   // (a boss's roar slows you: bosses.js)
    this.vx = mx * sp; this.vy = my * sp;
    const ox = this.x, oy = this.y;
    if (this.leap) { // Bond: arc through the air, slam on landing
      const L = this.leap; L.t += dt; const k = Math.min(1, L.t / L.dur);
      this.x = lerp(L.x0, L.x1, k); this.y = lerp(L.y0, L.y1, k); this.leapH = Math.sin(k * Math.PI) * 90;
      if (k >= 1) {
        this.leap = null; this.leapH = 0; const sp = L.spell, p = sp.p, r = p.radius * st.area;
        for (const m of R.mobsInRadius(this.x, this.y, r)) { R.damageMob(m, sp.dmg(), sp); if (p.stun) m.stunUntil = Math.max(m.stunUntil, R.time + p.stun * (m.boss ? 0.2 : 1)); if (!m.boss) { const dx = m.x - this.x, dy = m.y - this.y, d = Math.hypot(dx, dy) || 1; m.kx += dx / d * 260; m.ky += dy / d * 260; } }
        R.rings.push({ x: this.x, y: this.y, r0: 12, r1: r, t0: R.time, dur: 0.4, color: '#ffcf70' }); if (sp.def.fx[0]) R.fxAt(sp.def.fx[0], this.x, this.y, { scale: r / 80, fit: r });
        R.shake(6); Audio2.play('impact_lourd', 0.6, rand(0.9, 1.1));
      }
    } else if (this.dash) {
      const d = this.dash; d.t += dt;
      this.x += d.dx * d.sp * dt; this.y += d.dy * d.sp * dt;
      this.trail.push({ x: this.x, y: this.y, t: R.time });
      if (d.t >= d.dur) this.dash = null;
    } else { this.x += this.vx * dt; this.y += this.vy * dt; }
    if (this.push) { const k = Math.min(1, dt * 9); this.x += this.push.x * k; this.y += this.push.y * k; this.push.x *= 1 - k; this.push.y *= 1 - k; if (Math.abs(this.push.x) + Math.abs(this.push.y) < 1) this.push = null; }   // pushed back by a monster
    while (this.trail.length && R.time - this.trail[0].t > 0.25) this.trail.shift();
    if (this.dodgeReady > 0 && !this.dashNotified && R.time >= this.dodgeReady) { this.dashNotified = true; this.dashReadyT = R.time; }
    const b = R.bounds;
    this.x = clamp(this.x, b.x0, b.x1); this.y = clamp(this.y, b.y0, b.y1);
    if (R.ps) R.ps.dist += Math.hypot(this.x - ox, this.y - oy);
    this.moving = len > 0.1;
    // standing still for 3 s: the level 100 aura (the level 200 one once every achievement is unlocked)
    if (this.moving || this.dash || this.leap) this.idleT = 0; else this.idleT = (this.idleT || 0) + dt;
    if (this.moving) {
      this.lastDx = mx / (len || 1); this.lastDy = my / (len || 1); this.lastMoveT = R.time;
      this.faceAng = Math.atan2(my, mx);
      // Dofus views: R natively faces down-right, L natively faces up-left; this.flip = "facing left"
      this.view = my < -0.3 ? 'L' : 'R';
      if (Math.abs(mx) > 0.15) this.flip = mx < 0;
      else if (this.view === 'L') this.flip = true;
    }
    this.at += dt;
    if (this.eatT > 0) this.eatT -= dt;
    if (this.castAnim) { this.castT += dt * (this.run.cls.castRate || 1); if (this.castT > this.sprite.duration(this.castAnim)) this.castAnim = null; }   // (0.91: castRate — the Otomaï's NPC casts are long: played faster)
    this.anim = this.moving ? 'run' + this.view : 'static' + this.view;
    if (this.moving && this.sprite && this.sprite.runfb) {   // 0.40 (test): a mostly vertical move runs towards / away from the camera
      const vy = Math.sin(this.faceAng || 0), vx = Math.cos(this.faceAng || 0);
      if (Math.abs(vy) > 0.82 && Math.abs(vx) < 0.5) { const a = vy > 0 ? 'runF' : 'runB'; if (this.sprite.has(a)) this.anim = a; }
      else if (Math.abs(vx) > 0.85 && Math.abs(vy) < 0.45 && this.sprite.has('runS')) this.anim = 'runS';   // 0.41: straight left / right: the side profile run
    }
    if (this.hitFlash > 0) this.hitFlash -= dt * 4;
    // regen
    if (st.regen > 0 && this.hp < st.maxHp) this.hp = Math.min(st.maxHp, this.hp + st.regen * dt);
    // feca shield
    // (0.22: the Féca no longer blocks a whole hit every 12 seconds: Armure Féca is +2 resistance, Bouclier Féca +1 per level)
  }
  draw(ctx) {
    const R = this.run;
    let anim = this.anim, t = this.at, loop;
    if (this.dead) { anim = 'dieR'; t = this.deathT; loop = false; }
    else if (this.castAnim) { anim = this.castAnim; t = this.castT; loop = false; }
    const re = R.reviveAt && typeof performance !== 'undefined' ? (performance.now() - R.reviveAt) / 1000 : 99;   // (0.36: down for the first 0.6 s of a revival)
    if (re < 0.6) { anim = 'dieR'; t = re * 1.4; loop = false; }
    const inv = R.time < this.invisUntil;
    const flip = this.dead || anim === 'runF' || anim === 'runB' ? false : (anim.endsWith('L') ? !this.flip : this.flip); // L views natively face up-left
    // dodge trail: fading copies of the character
    if (this.trail.length > 1) for (let i = 0; i < this.trail.length; i += 2) {
      const tr = this.trail[i], k = 1 - (R.time - tr.t) / 0.25;
      this.sprite.draw(ctx, anim, t, tr.x, tr.y, ES, flip, { loop, alpha: 0.28 * k, moving: true, at: R.time });
    }
    // kama boost: golden aura
    if (R.kboostUntil > R.time) drawKamaAura(ctx, this, R);
    // idle aura (3 s standing still): level 100 behind the character, the secret level 200 one (golden sparkles and light) over it
    const aura = !this.dead && this.idleT > 3 ? (Prog.auraLevel() === 200 ? 'aura2' : 'aura1') : null;
    const drawAura = () => {
      const fx = FxSheets.get(aura), it = this.idleT - 3;
      // v2.0: the client's own aura clip (its ground squash, its stop() honoured), smaller and gathered around the feet
      if (fx && fx.anims.root) { const f = fx.frameAt('root', it, true); if (f) { ctx.globalAlpha = clamp(it / 0.6, 0, 1) * (aura === 'aura2' ? 0.9 : 0.95); fx.draw(ctx, f, this.x, this.y + 2, ES * (aura === 'aura2' ? 0.72 : 0.68), false); ctx.globalAlpha = 1; } }
    };
    if (aura === 'aura1') drawAura();
    if (R.time < this.immuneUntil) { ctx.save(); ctx.globalAlpha = 0.55 + 0.2 * Math.sin(R.time * 14); ctx.strokeStyle = '#ffe27a'; ctx.lineWidth = 3; ctx.beginPath(); ctx.ellipse(this.x, this.y - 32, 30, 44, 0, 0, TAU); ctx.stroke(); ctx.restore(); }
    const mu = R.mutate && R.time < R.mutate.until ? R.mutate : null, sc = mu ? 1 + 0.2 * clamp(Math.min(R.time - mu.t0, mu.until - R.time) / 0.3, 0, 1) : 1;   // 0.91: Élixir de Mutation
    if (mu) drawMutation(ctx, this, R, sc);
    this._drawn = { anim, t, flip, loop, sc };   // (0.60: the faint silhouette drawn over everything, render.js)
    // 0.91 (the Sacrieur's / Iop's colours flickered): a hit gave a white flash up to 80 % (4 hits a second in melee)
    // and every dodge / charge / leap a 6 Hz see-through blink — now a soft flash at most every 0.6 s, and only long
    // untouchable spells (revival, Immunité) blink, slowly
    const blink = R.time < this.invulnUntil && !this.dash && this.invulnUntil - R.time > 0.6;
    this.sprite.draw(ctx, anim, t, this.x, this.y - this.leapH, ES * sc, flip, { loop, alpha: inv ? 0.35 : (blink ? 0.8 + 0.2 * Math.sin(R.time * 14) : 1), flash: re >= 0.6 && re < 0.95 ? (0.95 - re) / 0.35 : this.hitFlash > 0 ? Math.min(0.4, this.hitFlash) : 0, moving: this.moving, at: R.time });
    if (aura === 'aura2') drawAura();
    // Feca shield: the original Bouclier Féca dome (spell FX 802), idling on its fully-formed frames
    if (this.shieldUp && !this.dead) {
      const fx = FxSheets.get(802), an = fx && fx.anims.root;
      if (an) { const n = an.f.length, k = Math.floor(R.time * 7) % 10, i = Math.min(n - 1, 7 + (k < 5 ? k : 9 - k)); ctx.save(); ctx.globalAlpha = 0.5; fx.draw(ctx, an.f[i], this.x, this.y + 6, 0.4, false); ctx.restore(); }
    }
    // v2.0: the dash is ready again: a tofu feather pops up next to the character for a second
    if (!this.dead && this.dashReadyT !== undefined) {
      const k = (R.time - this.dashReadyT) / 1.0;
      if (k >= 0 && k < 1) {
        const pop = k < 0.15 ? 0.6 + 0.4 * (k / 0.15) * 1.25 : k < 0.25 ? 1.1 - (k - 0.15) : 1, fade = k > 0.75 ? (1 - k) / 0.25 : 1;
        const fx = this.x + 34, fy = this.y - this.leapH - 74 - k * 10 + Math.sin(R.time * 8) * 1.5;
        ctx.globalAlpha = 0.85 * fade; ctx.drawImage(RCache.glow('rgba(207,233,255,0.8)'), fx - 22, fy - 22, 44, 44);
        ctx.globalAlpha = fade; Game.icons.drawFit(ctx, R.C.dodge.icon, fx, fy, 30 * pop); ctx.globalAlpha = 1;
      }
    }
    // in water: a small "Slowed" debuff tag above the head
    if (this.inWater && !this.dead) {
      const y = this.y - this.leapH - 108 + Math.sin(R.time * 4) * 2;
      ctx.globalAlpha = 0.92; TextCache.draw(ctx, '▼ ' + T('slowed'), this.x, y, '#9fdcff', 12, 'center', 'rgba(8,30,60,0.95)', 3, Game.zoom); ctx.globalAlpha = 1;
    }
  }
}

// ---------------------------------------------------------------- Run
class Run {
  // 0.68: L'île de Nowel gives no kamas at all (map.noKamas): the run's purse refuses every gain
  get kamas() { return this._kamas || 0; }
  set kamas(v) { if (v > (this._kamas || 0) && this.map && this.map.noKamas) return; this._kamas = v; }
  constructor(C, opts) {
    this.C = C; this.opts = opts;
    if ((C.maps.find(m => m.id === opts.map) || {}).hardOnly) opts.hard = true;   // (0.91: Goultard's zone is played in Difficile only)
    // 0.20: Difficile mode (C.hard): sturdier (the bigger the monster, the more), harder hitting, faster monsters; bosses x2 HP
    this.hard = opts.hard ? (C.hard || { hpMin: 0.5, hpMax: 0.75, dmg: 1.5, speed: 1.05, atk: 1.15, bossHp: 2 }) : null;
    if (this.hard) { const pw = Object.values(C.monsters).map(d => Math.log(d.hp * (1 + d.dmg / 10))); this.hardPw = [Math.min(...pw), Math.max(...pw)]; }
    // 0.95: the beginners' help — the first three zones in Normal (not Endless), until won there in Normal
    // (Store.data.clearedNormal): every monster's HP x aid.hp at its spawn (aidHp) and every blow x aid.dmg (damagePlayer)
    const AID = (C.beginnerAid || {})[opts.map];
    this.aid = AID && !this.hard && !opts.infinite && typeof Store !== 'undefined' && Store.data && !(Store.data.clearedNormal || {})[opts.map] ? AID : null;
    this.cls = C.classes.find(c => c.id === opts.cls);
    this.map = C.maps.find(m => m.id === opts.map);
    this.mapPos = C.maps.indexOf(this.map); this.mapIdx = this.map.tier !== undefined ? this.map.tier : this.mapPos;   // (0.50: the zone's tier, its place before the new zones: kamas, XP gems, merchant, zone multiplier)
    // the first zones are gentler (new players have no Dofus, mastery or experience yet)
    this.zoneMul = this.map.hidden ? 1 : 0.8 + 0.025 * Math.min(6, Math.max(0, this.mapIdx));   // v1.6: a bit gentler (life steal was cut by 15)
    this.time = 0; this.kills = 0; this.kamas = 0; this.level = 1; this.xp = 0; this.xpNext = Math.round(5 * (((C.run || {}).xpEarly || [])[0] || 1));
    this.mobs = []; this.projs = []; this.eprojs = []; this.zones = []; this.strikes = []; this.slashes = []; this.beams = [];
    this.cones = []; this.digs = []; this.cawottes = []; this.orbiters = []; this.summons = []; this.traps = []; this.pickups = []; this.effects = []; this.particles = [];
    this.texts = []; this.rings = []; this.teles = []; this.chats = [];
    this.grid = new Grid(72); this.dmgBy = {}; this.dmgTaken = 0;
    this.spells = []; this.passives = {};
    // every Dofus found once stays active in all later runs (like the shop scrolls)
    { const own = (typeof Store !== 'undefined' && Store.data && Store.data.dofus) || {}; this.dofus = (C.dofus || []).filter(d => own[d.id]); }
    this.totBuff = null; this.moveOff = false; this.achToasts = [];
    { const M = C.manuel, dbg = typeof Game !== 'undefined' && Game.debug && Game.debug.manuel; this.manuelAt = M && (dbg || Math.random() < M.chance) ? (dbg ? 3 : rand(M.t0, M.t1)) : null; }
    this.idleT = 0;
    this.pendingLevels = 0; this.over = false; this.victory = false; this.paused = false;
    this.spawnT = 0; this.bossQueue = (this.map.bosses || []).map(b => ({ t: b[0] * 60, id: b[1] }));
    this.events = (this.map.events || []).map(e => ({ t: e[0] * 60, kind: e[1], mob: e[2], n: e[3] }));
    this.secret = this.map.secret ? { t: this.map.secret[0] * 60, id: this.map.secret[1] } : null;
    this.door = null; this.doorDone = false; this.freezeUntil = 0; this.shakeAmt = 0; this.bossAlive = [];
    this.tofuMode = !!opts.tofuMode; this.finalKilled = false; this.bossesDown = new Set();
    this.rerolls = 3; this.banishes = C.banishes !== undefined ? C.banishes : 1; this.skips = C.skips !== undefined ? C.skips : 1; this.banned = new Set();   // 0.60: Bannir / Passer, once each
    this.sfused = new Set(); this.consumed = new Set(); this._startedAt = Date.now();   // 0.60: spell fusions made, and the spells they took (sfusions.js)
    this.weapon = null; this.powers = {}; this.allies = []; this.bombs = []; this.walls = []; this.tosses = [];
    this.RUN = C.run || { len: 600, finalT: 510, doorT: 150, doorEnd: 270, kamaRate: 1, unlockT: 510 };
    this.doom = null; this.kboostUntil = 0; this.revived = false; this.unlockedNow = []; this.dashes = [];
    this.charSid = this.cls.sprites[opts.sex || 0];
    this.cam = { x: 0, y: 0 };
    this.initExtras(); this.initWeapons(); this.initEvents(); this.initBosses();   // relics, random events, Archimonsters, Endless mode (extras.js)
  }
  // the size the ground tiles are decoded at: as big as this screen shows them, coarser with the SD / HD qualities
  // (0.44, before: the performance mode) and on phones / low-memory devices
  tileK() {
    const coarse = typeof matchMedia === 'function' && matchMedia('(pointer: coarse)').matches, lowMem = navigator.deviceMemory && navigator.deviceMemory <= 4;
    return clamp((Game.zoom || 1.5) * 1.08 / (this.world.res || 1), 0.3, (coarse || lowMem) ? 0.62 : 1) * Game.Q().tile;
  }
  async reloadTiles() {
    const tk = this.tileK(), old = this._tk; if (Math.abs(tk - old) < 0.01) return;
    this._tk = tk;
    await Promise.all(this.world.tiles.map(([tx, ty, fn]) => Assets.loadImg(`assets/worlds/${fn}`, tk).then(im => { if (im && this._tk === tk) { this.tiles[tx + ',' + ty] = im; Assets.release(`assets/worlds/${fn}`, old); } })));
    this.tilesN = (this.tilesN || 0) + 1000;   // (the ground buffer is redrawn)
  }
  async load(progress) {
    const C = this.C, mapId = this.map.world;
    const tasks = [];
    this.world = SPR.worlds[mapId];
    this.tiles = {};
    // v2.0 sharper maps (rendered at 2.5 px per Dofus px): decoded only as big as this screen shows them, and smaller
    // on phones / low-memory devices (they keep the v1.9 sharpness)
    const tk = this.tileK(); this._tk = tk;
    for (const [tx, ty, fn] of this.world.tiles) tasks.push(Assets.loadImg(`assets/worlds/${fn}`, tk).then(im => { if (im) { this.tiles[tx + ',' + ty] = im; this.tilesN = (this.tilesN || 0) + 1; } }));
    tasks.push(Assets.loadImg(`assets/worlds/${mapId}_mini.webp`).then(im => { this.mini = im; this.tilesN = (this.tilesN || 0) + 1; }));
    this.decorImg = null; if (this.world.decor) tasks.push(Assets.loadImg(`assets/worlds/${this.world.decor[0]}`).then(im => { this.decorImg = im; }));   // (0.88: the tall scenery's mask, Run.underDecor)
    this.depth = null; if (this.world.depth) tasks.push(loadDepth(vurl(`assets/worlds/${this.world.depth[0]}`), this.world.depth[1]).then(d => { this.depth = d; }).catch(() => { }));   // (0.91: who stands in front of whom, Run.decorFront)
    // sprites used by this map
    const keys = new Set();
    for (const w of this.map.waves) for (const [m] of w[2]) keys.add(C.monsters[m].sprite);
    for (const e of this.map.events) keys.add(C.monsters[e[2]].sprite);
    for (const b of this.map.bosses) { const bd = C.bosses[b[1]]; keys.add(bd.sprite); if (bd.walk60 && SPR.mobs[bd.walk60]) keys.add(bd.walk60); for (const ab of bd.abilities) { if (ab.mob) keys.add(C.monsters[ab.mob].sprite); if (ab.pool) ab.pool.forEach(p => keys.add(C.monsters[p].sprite)); } }
    if (this.map.secret) keys.add(C.bosses[this.map.secret[1]].sprite);
    for (const [r] of this.map.rare || []) keys.add(C.monsters[r].sprite);
    keys.add(C.monsters.tofu.sprite);
    keys.add(C.chestSprite); this.extraKeys(keys); this.eventKeys(keys);
    // summons drawn from a character sheet ('<sid>_c', e.g. the Brigandin's Mama) use the HD character renderer (tinted)
    this.summonChars = {};
    const fus = (C.spellFusions || []).filter(f => sfusionOf(f, this.cls.id)).map(f => f.id);   // (0.68: a fusion's own summon, the Boufcouls)
    for (const sid of [...this.cls.spells, ...fus]) { const s = C.spells[sid]; if (!s || s.t !== 'summon') continue; const k = (s.spriteKeyBy && s.spriteKeyBy[this.charSid]) || s.base.spriteKey, cm = /^(\d+)_c$/.exec(k || '');
      if (cm && SPR.chars[cm[1]]) this.summonChars[k] = new CharSprite(+cm[1], this.opts.colors, null, null, null); else if (k) keys.add(k); }   // (0.61: the Sram's Double has no sheet: 'no mob undefined')
    if (C.doom) { keys.add(C.bosses[C.doom.boss].sprite); keys.add(C.doom.crowSprite); }
    for (const a of Object.values(C.allies)) keys.add(a.sprite);
    if (this.cls.spells.some(s => ['bomb', 'detonate'].includes(C.spells[s].t))) keys.add(C.bombSprite);
    { // free the decoded monster sheets and map tiles of earlier runs that this one does not use
      const keep = new Set([...keys, C.chestSprite, C.totSprite || '1010_tot', C.bosses.bouftou_royal.sprite]);
      for (const k of Object.keys(MobSheets.c)) if (!keep.has(k)) MobSheets.drop(k);
      for (const u of Object.keys(Assets.img)) if (u.startsWith('assets/worlds/') && !u.startsWith(`assets/worlds/${mapId}_`)) Assets.release(u);
    }
    for (const k of keys) tasks.push(MobSheets.load(k));
    // 0.44: every weapon's look (types, unique weapons, finales' skins) cut into its small atlas now, behind the loading
    // screen: picking a weapon mid-run no longer decodes the big accessory sheets during the fight
    tasks.push(AccLib.ensure(C.uniqueWeapons.map(w => w.acc)));   // (0.60: the 40 weapons' looks, small pictures)
    // fx
    const fx = new Set();
    for (const sid of this.cls.spells) C.spells[sid].fx.forEach(f => fx.add(f));
    for (const f of C.spellFusions || []) if (sfusionOf(f, this.cls.id)) (C.spells[f.id].fx || []).forEach(x => fx.add(x));   // (0.60: its spell fusions' effects)
    for (const m of Object.values(C.monsters)) if (m.atk && m.atk.fx) fx.add(m.atk.fx);
    [2004, 2014, 1100, 1011, 902, 901, 808, 802, 707, 4600, ...(C.extraFx || [])].forEach(f => fx.add(f));
    fx.add(Prog.auraLevel() === 200 ? 'aura2' : 'aura1');
    for (const w of C.weapons) w.fx.forEach(f => fx.add(f));
    for (const u of C.uniqueWeapons || []) (u.fx || []).forEach(f => fx.add(f));   // 0.32: no late loading in the run
    for (const g of C.globalSpells || []) ((C.spells[g.id] || {}).fx || []).forEach(f => fx.add(f));
    for (const f of fx) tasks.push(FxSheets.load(f));
    this.fxNeed = new Set([...fx].map(String));   // (0.95: the sheets PX.warm sends to the GPU)
    // character
    const sid = this.cls.sprites[this.opts.sex || 0];
    this.charSprite = new CharSprite(sid, this.opts.colors, this.cls.nohats ? null : this.opts.hat, this.cls.nohats ? null : this.opts.cape, this.cls.nopets ? null : this.opts.pet, this.shieldOn() ? this.opts.shield : null);
    tasks.push(this.charSprite.load()); tasks.push(this.loadExtras());
    for (const cs of Object.values(this.summonChars)) tasks.push(cs.load());
    // sfx (original client sounds)
    const S = Audio2.SND, snd = ['Critical_Hit', 'EVENT', 'explosion', 'son_attack', 'son_die', 'hit_defaut', 'punch'];
    for (const k of Object.values(S.ui)) snd.push(k);
    const cs = S.chars[sid] || {}; for (const a in cs) snd.push(...cs[a]);
    for (const id of this.cls.spells) snd.push(...Audio2.spellKeys(C.spells[id]));
    for (const w of C.weapons) snd.push(w.snd);
    for (const d of Object.values(C.drops)) if (d.snd) snd.push(d.snd);
    { const lb = C.drops.liberation, k = lb && lb.anim && (Audio2.charSnd(sid, lb.anim + 'R') || Audio2.charSnd(80, lb.anim + 'R')); if (k) snd.push(k[0]); }   // Libération's original sound
    snd.push(...(C.hitSnd || []), 'pain', 'dodge_604', 'stars', 'coffre', 'licrounch_1001b');
    for (const sid of this.cls.spells) if (C.spells[sid].snd) snd.push(C.spells[sid].snd);
    for (const g of C.globalSpells || []) if (C.spells[g.id].snd) snd.push(C.spells[g.id].snd);
    snd.push('pok', 'stars');
    const gfxs = new Set([...Object.values(C.monsters), ...Object.values(C.bosses)].filter(m => keys.has(m.sprite)).map(m => m.gfx));
    for (const g of gfxs) { const m = S.mobs[g]; if (m) for (const k in m) snd.push(...m[k]); else snd.push(...SFX_DIE_ALL.filter(Boolean).slice(0, 0)); }
    for (const n of SFX_DIE_ALL) snd.push(n);
    for (const k of Object.values(C.bossDie || {})) snd.push(k); // boss death sounds must be ready the moment a boss falls
    const flat = o => Object.values(o || {}).forEach(v => Object.values(v).forEach(k => snd.push(...[].concat(k))));
    flat(C.allySnd); flat(Object.fromEntries(Object.entries(C.summonSnd || {}).filter(([k]) => this.cls.spells.includes(k))));
    tasks.push(Audio2.preload(snd));
    await Assets.all(tasks, progress);
    this.water = decodeWater(this.world.water);
    // setup
    const ins = this.world.inset || [0, 0, 0, 0];
    this.bounds = { x0: 30 + ins[0], x1: this.world.w - 30 - ins[1], y0: 40 + ins[2], y1: this.world.h - 20 - ins[3] };
    this.center = { x: (this.bounds.x0 + this.bounds.x1) / 2, y: (this.bounds.y0 + this.bounds.y1) / 2 };
    this.player = new Player(this, this.charSprite);
    this.player.x = this.center.x; this.player.y = this.center.y;
    this.addSpell(this.cls.spells[0]);
    this.recompute();
    this.player.hp = this.stats.maxHp;
    this.placeBoosters();   // TTG boosters near the corners (events.js)
    this.chat(L(this.map.name) + ' — ' + T('difficulty') + ' ' + this.map.lvl, '#ffd27a');
    this.chat(pick(TIPS[LANG] || TIPS.en || TIPS.fr), '#9fd3ff');
    Prog.runStart(this);
  }
  // water (30% slower): a coarse mask baked from the world tiles
  isWater(x, y) {
    const W = this.water; if (!W) return false;
    const cx = Math.floor(x / W.cell), cy = Math.floor(y / W.cell);
    if (cx < 0 || cy < 0 || cx >= W.cols || cy >= W.rows) return false;
    return W.bits[cy * W.cols + cx] === 1;
  }
  inRange(m) { const P = this.player, g = this.C.range || { x: 800, y: 450 }; return Math.abs(m.x - P.x) <= g.x && Math.abs(m.y - P.y) <= g.y; }
  // ------------------------------------------------ stats
  camTarget() {   // (0.53: also used to place the camera before the countdown)
    const ck = this.critK ? this.critK() : 0, zk = 1 + 0.75 * ck, P = this.player, vw = Game.viewW / zk, vh = Game.viewH / zk;
    let cx = P.x, cy = P.y - 30;
    if (ck > 0) { const F = this.critFx; if (F.A && this.allies.includes(F.A)) { F.x = F.A.x; F.y = F.A.y - 40; } cx = lerp(cx, F.x, ck); cy = lerp(cy, F.y, ck); }   // (0.98: a critical summon's show: towards it)
    if (this.world.w > vw) cx = clamp(cx, vw / 2, this.world.w - vw / 2); else cx = this.world.w / 2;
    if (this.world.h > vh) cy = clamp(cy, vh / 2, this.world.h - vh / 2); else cy = this.world.h / 2;
    return [cx, cy];
  }
  recompute() {
    const b = this.cls.base, st = {
      maxHp: b.hp, speed: b.speed, might: b.might, armor: b.armor, regen: b.regen, area: 1, cooldown: 1, amount: 0, duration: 1,
      projspeed: 1, wreach: 1, magnet: 1, luck: 1, growth: 1, greed: 1, crit: 0.05, critMult: 2, healBonus: 0,
    };
    const id = this.cls.id;
    if (id === 'enutrof') { st.greed += 0.4; st.magnet += 0.3; }
    if (id === 'sram') st.crit += 0.12;
    if (id === 'xelor') st.cooldown *= 0.9;
    if (id === 'ecaflip') { st.critMult = 2.5; st.luck += 0.15; }
    if (id === 'eniripsa') st.healBonus += 0.3;
    if (id === 'cra') st.projspeed += 0.25;
    if (id === 'sadida') st.area += 0.15;
    if (id === 'roublard') st.area += 0.2;
    const ps = this.cls.passiveStats || {}; for (const k in ps) st[k] = (st[k] || 0) + ps[k];
    if (this.shieldOn()) st.armor += this.C.shieldArmor || 1;   // 0.92: a worn shield, +1 resistance (the stats are rebuilt each time: never twice)
    // characteristic scrolls bought in the shop (every character)
    const SC = (Store.data && Store.data.scrolls) || {};
    for (const sc of this.C.scrolls || []) { const lv = SC[sc.id] || 0; if (!lv) continue; for (const k in sc.per) { if (k === 'maxhp') st.maxHp *= 1 + sc.per[k] * lv; else st[k] = (st[k] || 0) + sc.per[k] * lv; } }
    for (const p of this.C.passives) {
      const lv = this.passives[p.id] || 0; if (!lv) continue;
      const v = passivePer(this.C, p, ((typeof Store !== 'undefined' && Store.data && Store.data.passLv) || {})[p.id]) * lv * (p.stat === 'leech' ? 1 + 0.1 * (lv - 1) : 1);   // + the shop levels
      if (p.block) st.pblock = (st.pblock || 0) + p.block[0] + (p.block[1] - p.block[0]) * (lv - 1) / Math.max(1, p.max - 1);   // 0.53: Sagesse blocks ranged spells
      switch (p.stat) {
        case 'maxhp': st.maxHp *= 1 + v; break;
        case 'cooldown': st.cooldown *= 1 + v; break;
        case 'magnet': st.magnet += v; st.greed += (p.greed || 0.1) * lv; break;   // (0.81: p.greed, 4 levels)
        case 'armor': st.armor += v; break;
        case 'regen': st.regen += v; break;
        case 'amount': st.amount += v; break;
        case 'crit': st.crit += v; break;
        default: st[p.stat] = (st[p.stat] || 0) + v;
      }
      if (p.reachW) st.wreach += p.reachW * lv + (p.reachShop || 0) * ((((typeof Store !== 'undefined' && Store.data && Store.data.passLv) || {})[p.id]) || 0);   // 0.84: Portée lengthens the area weapons' reach (after Intelligence)
    }
    for (const d of this.dofus) {
      const bo = d.bonus; const a = bo.all || 0;
      st.maxHp *= 1 + a; st.might += a; st.speed += a * 0.5; st.area += a; st.luck += a; st.growth += a; st.armor += a * 10; st.cooldown *= 1 - a * 0.5;
      for (const k in bo) if (k !== 'all') { if (k === 'maxhp') st.maxHp *= 1 + bo[k]; else if (k === 'cooldown') st.cooldown *= 1 + bo[k]; else st[k] = (st[k] || 0) + bo[k]; }
    }
    this.relicStats(st); this.fusionStats(st);
    if (Store.data && Store.data.dofawa && this.C.dofawa) st.maxHp += this.C.dofawa.hp;   // the Dofawa (every achievement)
    if (this.totBuff) st[this.totBuff.stat] = (st[this.totBuff.stat] || 0) + this.totBuff.v;   // ToT's bonus for this run
    st.maxHp = Math.round(st.maxHp);
    const oldMax = this.stats ? this.stats.maxHp : st.maxHp;
    this.stats = st;
    if (this.player && st.maxHp > oldMax) this.player.hp += st.maxHp - oldMax;
  }
  // 0.92: the shield worn this run (a class that wears hats / capes, a shield of the game)
  shieldOn() { const id = this.opts && this.opts.shield; return !!id && !this.cls.nohats && (this.C.shields || []).some(s => s.id === id); }
  // 0.93: the run is over (back to the menu, or another run): its characters are let go (CharSprite.dispose)
  dispose() {
    if (this._disposed) return; this._disposed = true;
    for (const cs of [this.charSprite, this.merchantSprite, ...Object.values(this.summonChars || {})]) if (cs) cs.dispose();
  }
  addSpell(id) { const s = new SpellInst(this, this.C.spells[id]); this.spells.push(s); return s; }
  // v2.0: attacks start slower and speed up as the run goes (x1.5 cooldown at the start; normal speed from level 15,
  // or after 3:20 at the latest so that a slow start never stays slow)
  cdRamp() { const R = this.RUN, k = R.cdEarly || 0; return k ? 1 + k * clamp(Math.min(1 - (this.level - 1) / ((R.cdEarlyLv || 15) - 1), 1 - this.time / (R.cdEarlyT || 200)), 0, 1) : 1; }
  // temporary damage buffs: Cri de l'Ours (rally), Roue de la Fortune
  hardHp(d) { const H = this.hard; if (!H) return 1; const [a, b] = this.hardPw, k = clamp((Math.log(d.hp * (1 + d.dmg / 10)) - a) / ((b - a) || 1), 0, 1); return 1 + H.hpMin + (H.hpMax - H.hpMin) * k; }
  spellSlots() { return (this.C.spellSlots || 4) + (this.passives.borne || 0); }   // 0.20: 4 attack spells, a 5th with 'Borné'
  aidHp() { return this.aid ? this.aid.hp : 1; }   // 0.95: the beginners' help
  atkK() { return this.hard ? 1 / this.hard.atk : 1; }   // monsters' attack intervals (Difficile: 15% faster)
  // 0.68: is this boss's death the zone's final kill? (a finalGroup is down when none of its bosses is left alive)
  isFinalKill(m) { const d = m.def; return !!d.final && (!d.finalGroup || !this.bossAlive.some(b => b !== m && !b.dying && b.hp > 0 && b.def.finalGroup === d.finalGroup)); }
  // the zone's final boss life (a group's: all of them together), for the scheduled elites' cap
  finalHp() { const B = (this.map.bosses || []).map(b => this.C.bosses[b[1]]).filter(b => b && b.final); return B.length ? (B[0].finalGroup ? B.reduce((a, b) => a + b.hp, 0) : B[0].hp) : 0; }
  dmgMul() { let k = 1 + Math.min(this.RUN.lvDmgMax || 0, (this.RUN.lvDmg || 0) * (this.level - 1)); if (this.weakUntil > this.time) k *= 0.5; if (this.rally && this.time < this.rally.until) k *= 1 + this.rally.bonus; if (this.fortune && this.time < this.fortune.until) k *= 1 + this.fortune.bonus; if (this.mutate && this.time < this.mutate.until) k *= 1 + this.mutate.power; if (this.allies.some(a => a.kind === 'majeure')) k *= 2; return k; }   // (0.98: an Arakne majeure on the field: x2, once however many — it goes when it goes)
  // ------------------------------------------------ helpers
  chat(msg, color = '#fff') { const l = this.chats[this.chats.length - 1]; if (l && l.msg === msg && l.t === this.time) return; this.chats.push({ msg, color, t: this.time }); if (this.chats.length > 7) this.chats.shift(); }
  text(x, y, s, color, size = 14, life = 0.9) { if (this.texts.length < ((typeof Game !== 'undefined' && Game.lowFx) ? (Game.minFx ? 30 : 45) : typeof Game !== 'undefined' && Game.Q && Game.Q().fx === 1 ? 70 : 100)) { const o = { x, y, s, color, size, t: 0, life }; this.texts.push(o); return o; } return null; }
  // 0.97: the heals that land together (the Cawotte's tick, Potagew Pwoutant's cloud, a potion…) add up in one green number
  // over the character for 0.4 s — each wrote its own at the same spot, and the Cawotte's two (heal + its own) overlapped
  healText(v) {
    const P = this.player, o = this._hText, f = n => '+' + (n < 10 ? Math.round(n * 10) / 10 : Math.round(n));
    if (o && o.t < 0.4 && this.texts.includes(o)) { o.v += v; o.s = f(o.v); o.x = P.x; return o; }
    const n = this.text(P.x, P.y - 70, f(v), '#3ddc5a', 15); if (n) n.v = v; this._hText = n; return n;
  }
  shake(a) { if (Store.data.settings.shake) this.shakeAmt = Math.min(7, this.shakeAmt + a * 0.5); }   // 0.22: half as strong
  fxAt(id, x, y, o = {}) {
    const sh = FxSheets.get(id); if (!sh) return;
    let sym = o.sym; if (!sym) { const ks = Object.keys(sh.anims); sym = ks.includes('shoot') ? 'shoot' : ks.includes('root') ? 'root' : ks[ks.length - 1]; }
    if (!sh.anims[sym]) return;
    if (this.effects.length > 90) return;
    // 0.61: a spell spammed with a lot of attack speed no longer floods the screen (8 copies of one clip at most)
    let same = 0; for (const e of this.effects) if (e.sh === sh && ++same >= 8) return;
    let scale = o.scale || 1;
    // 0.61: never drawn bigger than the spell's real reach (o.fit = that radius, world units)
    if (o.fit) { const vr = fxRadius(sh, sym); if (vr > 0) scale = Math.min(scale, o.fit / vr); }
    // 0.61: the client's animation plays faster when its spell attacks faster (cooldown shortened), up to x3
    const rate = o.rate || this.fxRate(id);
    this.effects.push({ sh, sym, x, y, t: -(o.delay || 0), dur: sh.duration(sym), follow: o.follow, scale, rot: o.rot || 0, flip: o.flip, off: o.off, sy: o.sy, rate, tint: o.tint });   // (0.96: tint, a clip in another colour)
  }
  fxRate(id) {
    for (const s of this.weapon ? [...this.spells, this.weapon] : this.spells) {
      if (!s.def.fx || !s.def.fx.includes(id) || !(s.p && s.p.cd > 0) || s.p.perm) continue;
      return clamp(s.p.cd / Math.max(0.05, s.cooldown()), 1, 3);
    }
    return 1;
  }
  nearestMob(x, y, r) {
    let best = null, bd = r * r;
    for (const m of this.grid.query(x, y, r, _q)) { if (m.dying || !this.inRange(m)) continue; const d = dist2(x, y, m.x, m.y); if (d < bd) { bd = d; best = m; } }
    return best;
  }
  mobsInRadius(x, y, r) {
    const out = [];
    for (const m of this.grid.query(x, y, r + 40, _q)) if (!m.dying && dist2(x, y, m.x, m.y) <= (r + m.r) * (r + m.r)) out.push(m);
    return out;
  }
  randomMobNear(x, y, r) { const a = this.mobsInRadius(x, y, r); return a.length ? pick(a) : null; }
  pickTargets(mode, n, r) {
    const P = this.player;
    const cand = this.mobsInRadius(P.x, P.y, r).filter(m => this.inRange(m));
    if (!cand.length) return [];
    if (mode === 'nearest') { cand.sort((a, b) => dist2(P.x, P.y, a.x, a.y) - dist2(P.x, P.y, b.x, b.y)); return cand.slice(0, n); }
    if (mode === 'strongest') { cand.sort((a, b) => b.hp - a.hp); return cand.slice(0, n); }
    if (mode === 'cluster') {
      const out = [];
      for (let k = 0; k < n; k++) {
        let best = null, bc = -1;
        for (let i = 0; i < Math.min(14, cand.length); i++) {
          const c = cand[(Math.random() * cand.length) | 0]; let cnt = 0;
          for (const o of cand) if (dist2(c.x, c.y, o.x, o.y) < 70 * 70) cnt++;
          if (cnt > bc) { bc = cnt; best = c; }
        }
        if (best) out.push(best);
      }
      return out;
    }
    shuffle(cand); return cand.slice(0, n);
  }
  // ------------------------------------------------ spawning
  // 10-minute runs: the difficulty follows the 20-minute curve of v1.3 at twice the pace
  // effective minute: the difficulty clock (pace × minutes), eased in the first half so the 3–6 min stretch is not a wall
  em() { const m = this.time / 60; return m * (this.RUN.pace || 2) * (0.7 + 0.3 * Math.min(1, m / 10)); }
  scaleHp() { const R = this.RUN; return (R.hpBase || 1) + (R.hpGrow || 0.075) * this.em(); }   // v1.7: sturdier mobs (fewer one-shots), fewer of them
  scaleDmg() { return 1 + (this.RUN.dmgGrow || 0.03) * this.em(); }
  // 0.60: the monsters' life from the second half of the run: hpLate = [from min, to min, x at the start, x at the end]
  // (+25 % at 5:00 growing to x1.5 at 10:00): fewer monsters on screen for the same difficulty
  // 0.60: ambers worth more as the run goes (fewer, sturdier monsters late): xpLate = [from min, to min, x start, x end]
  xpLateK() { const H = this.RUN.xpLate; if (!H) return 1; const tm = this.time / 60; return tm < H[0] ? H[2] : lerp(H[2], H[3], clamp((tm - H[0]) / Math.max(0.01, H[1] - H[0]), 0, 1)); }
  hpLateK() { const H = this.RUN.hpLate; if (!H) return 1; const tm = this.time / 60; return tm < H[0] ? 1 : lerp(H[2], H[3], clamp((tm - H[0]) / Math.max(0.01, H[1] - H[0]), 0, 1)); }
  // per-zone normalisation baked by the content build: [start, end, hpMul, dmgMul, xpMul] per wave
  norm() {
    const N = this.map.norm; if (!N || !N.length) return [1, 1, 1];
    const tm = this.time / 60; const w = N.find(n => tm >= n[0] && tm < n[1]) || N[N.length - 1];
    return [w[2], w[3], w[4]];
  }
  spawnPos(minR = 0) {
    const P = this.player, b = this.bounds;
    const vw = Game.viewW / 2 + 60, vh = Game.viewH / 2 + 60;
    // 0.40: the waves come mostly from one side (it turns every 8-14 s), easier to herd than monsters from everywhere
    if (!(this.time < this._wdT)) { this._wd = rand(TAU); this._wdT = this.time + rand(8, 14); }
    for (let i = 0; i < 12; i++) {
      const a = i < 8 && Math.random() < 0.78 ? this._wd + rand(-0.55, 0.55) : rand(TAU);
      let x = P.x + Math.cos(a) * vw * rand(1.0, 1.25), y = P.y + Math.sin(a) * vh * rand(1.0, 1.25);
      if (Math.abs(Math.cos(a)) * vh > Math.abs(Math.sin(a)) * vw) x = P.x + Math.sign(Math.cos(a)) * vw * rand(1, 1.15); else y = P.y + Math.sign(Math.sin(a)) * vh * rand(1, 1.15);
      if (x >= b.x0 && x <= b.x1 && y >= b.y0 && y <= b.y1) return [x, y];
    }
    // fallback: anywhere inside bounds far enough
    for (let i = 0; i < 20; i++) {
      const x = rand(b.x0, b.x1), y = rand(b.y0, b.y1);
      if (Math.abs(x - P.x) > vw * 0.9 || Math.abs(y - P.y) > vh * 0.9) return [x, y];
    }
    return [clamp(P.x + vw, b.x0, b.x1), clamp(P.y, b.y0, b.y1)];
  }
  spawnMob(id, x, y, o = {}) {
    if (this.mobs.length >= (this.RUN.mobCap || 420) && !o.force) return null;   // (0.59: C.run.mobCap; spawnCap is what the waves aim for)
    let def = this.C.monsters[id]; if (!def) return null;
    if (this.tofuMode && !o.keep) def = this.C.monsters.tofu;
    const sh = MobSheets.c[def.sprite]; if (!sh) return null;
    const nm = this.norm();
    // v2.0: sturdier (+15% HP) and harder hitting monsters: +20% for melee blows, +10% for ranged attacks (C.run)
    const RU = this.RUN, zm = this.zoneMul || 1, hpm = this.scaleHp() * nm[0] * zm * (o.elite ? 5 : 1) * (RU.hpMul || 1) * this.hardHp(def) * this.hpLateK() * this.aidHp(), dmul = this.scaleDmg() * nm[1] * zm;
    const m = {
      dmul: dmul * (RU.rangedMul || 1), xpm: nm[2],
      def, sh, x, y, hp: def.hp * hpm, maxHp: def.hp * hpm, dmg: def.dmg * dmul * (o.elite ? 1.5 : 1) * (RU.meleeMul || 1), speed: def.speed * (this.RUN.mobSpeed || 1) * (o.elite ? 0.95 : 1) * (this.hard ? this.hard.speed : 1) * rand(0.92, 1.08),
      r: def.size * ES * (o.elite ? 1.3 : 1), kx: 0, ky: 0, t: rand(1), flip: false, view: 'R', dying: false, dieT: 0, flash: 0,
      slowUntil: 0, slowAmt: 0, stunUntil: 0, confuseUntil: 0, burnUntil: 0, burnDps: 0, poisonT: 0, hitCd: new Map(), atkT: rand(1, 3) * (this.RUN.firstAtk || 1),
      elite: !!o.elite, boss: false, dirT: 0, ex: 0, ey: 0, scale: ES * (def.scale || 1) * (o.elite ? 1.3 : 1), state: 'move', alpha: 1, born: this.time,
    };
    if (def.beh === 'erratic') { m.ex = rand(-1, 1); m.ey = rand(-1, 1); }
    this.mobs.push(m);
    if (!o.noArchi && !o.keep && !o.force) this.maybeArchi(m);
    this.seen(def.id);
    return m;
  }
  spawnBoss(id) {   // boss HP are always a round number (bossHp)
    const d = this.C.bosses[id]; const sh = MobSheets.c[d.sprite]; if (!sh) return;
    const [x, y] = this.spawnPos();
    if (d.doom) {
      const ramp = 1 + 0.12 * Math.max(0, this.time - (this.doom ? this.doom.t0 : 600));  // the Doom only gets worse
      if (!this._doomHp) this._doomHp = Math.max(...Object.values(this.C.bosses).filter(b => !b.doom).map(b => b.hp));   // as strong as the strongest boss
      const bhp = bossHp(this._doomHp * (this.C.doomHpK || 1) * (this.hard ? this.hard.bossHp : 1) * this.aidHp()), m = { def: d, sh, x, y, hp: bhp, maxHp: bhp, dmg: d.dmg * this.scaleDmg() * ramp * (this.RUN.meleeMul || 1), speed: d.speed * (this.RUN.mobSpeed || 1) * (this.hard ? this.hard.speed : 1) * rand(0.9, 1.1), r: d.size * ES, kx: 0, ky: 0, t: rand(1), flip: false,
        view: 'R', dying: false, dieT: 0, flash: 0, slowUntil: 0, slowAmt: 0, stunUntil: 0, confuseUntil: 0, burnUntil: 0, burnDps: 0, hitCd: new Map(),
        atkT: 2, elite: false, boss: true, doom: true, dirT: 0, ex: 0, ey: 0, ab: d.abilities.map(a => ({ a, t: (a.cd || 5) * rand(0.2, 1.0) })), state: 'move', scale: ES * d.scale, alpha: 1, born: this.time };
      this.mobs.push(m); this.seen(d.id); return m;
    }
    const hpm = (1 + 0.01 * this.level) * (1 + 0.04 * this.em()) * (this.zoneMul || 1) * (this.RUN.hpMul || 1);
    const bhp = bossHp(d.hp * hpm * (this.hard ? this.hard.bossHp : 1) * this.aidHp()), m = {
      def: d, sh, x, y, hp: bhp, maxHp: bhp, dmg: d.dmg * this.scaleDmg() * (this.zoneMul || 1) * (this.RUN.meleeMul || 1), dmul: this.scaleDmg() * (this.zoneMul || 1), speed: d.speed * (this.RUN.mobSpeed || 1) * (this.hard ? this.hard.speed : 1), r: d.size * ES, kx: 0, ky: 0, t: 0, flip: false,
      view: 'R', dying: false, dieT: 0, flash: 0, slowUntil: 0, slowAmt: 0, stunUntil: 0, confuseUntil: 0, burnUntil: 0, burnDps: 0, hitCd: new Map(),
      atkT: 2, elite: false, boss: true, dirT: 0, ex: 0, ey: 0, ab: d.abilities.map(a => ({ a, t: (a.cd || 5) * rand(0.4, 0.9) })), state: 'move', scale: ES * d.scale, alpha: 1, born: this.time,
    };
    this.mobs.push(m); this.bossAlive.push(m);
    this.seen(d.id);
    this.banner(T('boss_appears', { n: L(d.name) }), d.final ? '#ff5050' : '#ffb347', false, true, 'boss');
    this.chat(T('boss_appears', { n: L(d.name) }), '#ff8a65');
    Audio2.sfx('EVENT', 0.7); Audio2.bossSfx(d.final);   // (0.54: loud enough to be heard over the fight)
    if (d.final) Audio2.playMusic(this.map.boss_music, 2.0);
    return m;
  }
  // 0.84: while a boss fights (its bar at the top of the screen) no message in the middle of the screen: it goes
  // to the chat only (chat() drops the caller's own copy). force = the boss's own arrival.
  bossFight() { return this.bossAlive.some(b => !b.dying && b.hp > 0); }
  banner(text, color, center, force, kind) { if (!force && this.bossFight()) { this.chat(text, color); return; } this.bannerMsg = { text, color, t: 0, center: !!center, kind }; }   // (kind 'boss': its frame, render.js annPanel)
  seen(id) { const s = Store.data.seen; if (!s[id]) { s[id] = 1; } }
  spawner(dt) {
    const tm = this.time / 60;
    const wave = this.map.waves.find(w => tm >= w[0] && tm < w[1]) || this.map.waves[this.map.waves.length - 1];
    const em = this.em();
    // 0.20: the crowd keeps growing every minute (spawnGrow); from spawnLateT it grows a bit more (0.60: spawnLateK = x1.10 at
    // 5:00 up to x1.25 at spawnLateEnd 10:00; before: spawnLate = x2 over one minute);
    // nothing new comes after spawnStopT (9:30): only the Maîtres Corbacs (the Doom) and the bosses
    const RU = this.RUN, lt = RU.spawnLateT || 1e9, late = RU.spawnLateK ? (tm < lt ? 1 : lerp(RU.spawnLateK[0], RU.spawnLateK[1], clamp((tm - lt) / Math.max(0.01, (RU.spawnLateEnd || 10) - lt), 0, 1))) : 1 + ((RU.spawnLate || 1) - 1) * clamp(tm - lt, 0, 1), grow = (1 + (RU.spawnGrow || 0) * tm) * late;
    if (tm >= lt && !this.lateWarned) { this.lateWarned = true; this.banner(T('crowd_grows'), '#ff9a3c'); this.chat(T('crowd_grows'), '#ff9a3c'); Audio2.sfx('EVENT', 0.7); }
    const stopped = !this.infinite && tm >= (RU.spawnStopT || 1e9);
    const target = Math.min(RU.spawnCap || 380, Math.round((wave[4] * (tm >= 3 && tm < 5.5 ? 0.88 : 1) + Math.floor(em * 1.5)) * (RU.spawnMul || 1) * grow));
    this.spawnT -= dt;
    const alive = this.mobs.length;
    if (this.spawnT <= 0 && !stopped) {
      // 0.68: fewer, irregular, bigger waves — the same monsters per minute on average, but every packT[0..1] times
      // the old interval, all of a wave out of ONE spot, packed together, of one or two kinds
      const pk = RU.packT ? rand(RU.packT[0], RU.packT[1]) : 1;
      this.spawnT = wave[3] * pk * (alive < target * 0.5 ? 0.5 : 1);
      if (alive < target) {
        const batch = Math.min(target - alive, Math.round((2 + Math.floor(em / 3)) * late * pk));
        const ids = RU.packT ? [weighted(wave[2]), weighted(wave[2])] : null, [cx, cy] = this.spawnPos(), b = this.bounds, rr = 60 + 26 * Math.sqrt(batch);   // (0.71: a wider spread)
        for (let i = 0; i < batch; i++) {
          const id = ids ? ids[i % 3 === 2 ? 1 : 0] : weighted(wave[2]);
          let x, y;
          if (ids) { const a = rand(TAU), d = rr * Math.sqrt(Math.random()); x = clamp(cx + Math.cos(a) * d, b.x0, b.x1); y = clamp(cy + Math.sin(a) * d * 0.7, b.y0, b.y1); }
          else [x, y] = this.spawnPos();
          const elite = em > 6 && Math.random() < (0.006 + 0.0006 * em) * (RU.rareK || 1);   // (0.60: rareK keeps the random elites as frequent per minute with fewer monsters)
          this.spawnMob(id, x, y, { elite });
        }
      }
    }
    // rare monsters
    if (!stopped) for (const [id, p] of this.map.rare || []) if (Math.random() < p * dt * 60 / 60 && !this.mobs.some(m => m.def.id === id)) {
      const [x, y] = this.spawnPos(); const m = this.spawnMob(id, x, y, { keep: true });
      if (m) this.chat(T('lurking', { n: L(m.def.name) }), '#ffd700');
    }
    // events
    for (const e of this.events) if (!e.done && this.time >= e.t && !stopped) {
      e.done = true;
      if (e.kind === 'swarm') this.swarm(e.mob, e.n); else this.ring(e.mob, e.n);
    }
    for (const b of this.bossQueue) if (!b.done && this.time >= b.t) { b.done = true; this.spawnBoss(b.id); }
    if (this.secret && !this.secret.done && this.time >= this.secret.t) {
      this.secret.done = true; const d = this.C.bosses[this.secret.id];
      this.chat(T('secret_boss', { n: L(d.name) }), '#ff3b3b'); this.spawnBoss(this.secret.id);
    }
    // ToT's door
    if (!this.door && !this.doorDone && this.time >= this.RUN.doorT && !this.doorTime()) {   // 0.26: a time portal in 10% of the runs, else the Tofu Mutant (events.js)
      this.door = { x: this.center.x, y: this.center.y, t0: this.time };
      this.chat(T('door_appears'), '#e0b0ff'); this.banner(T('door_appears'), '#d7a6ff'); Audio2.blip('door');
    }
    if (this.door && this.time > this.RUN.doorEnd) { this.door = null; this.doorDone = true; }
    // the Doom (0.22): the Maîtres Corbacs come at 11:00 (DM.t), or at 10:00 (DM.tWon) once the zone's final boss is down;
    // a wave every DM.every s, half as many each time (1, 1, 2, 4…); they can be killed now (hp of the strongest boss)
    const DM = this.infinite ? null : this.C.doom, doomT = this.finalKilled ? (DM && DM.tWon) || 600 : (DM && DM.t) || 660;
    if (DM) {
      if (!this.doomWarned && this.time >= doomT - 30) { this.doomWarned = true; this.chat(T('doom_soon', { t: fmtTime(doomT) }), '#ff8a65'); }   // (0.96: their real time: it said 10:00 at 10:30 when they come at 11:00)
      if (this.time >= doomT) {
        if (!this.doom) {
          this.doom = { next: this.time, wave: 0, t0: this.time };
          this.banner(T('doom'), '#ff3b3b'); this.chat(T('doom'), '#ff3b3b'); Audio2.sfx('EVENT', 0.9); this.shake(8);
          Prog.st().doomSeen = 1; Audio2.playMusic(this.map.boss_music, 1.0);
        }
        if (this.ps) this.ps.doomT = this.time - this.doom.t0;
        if (this.time >= this.doom.next) {
          const alive = this.mobs.filter(m => m.doom && !m.dying).length;
          const n = Math.min(Math.max(1, 2 ** (this.doom.wave - 1)), DM.cap - alive);
          for (let k = 0; k < n; k++) this.spawnBoss(DM.boss);
          this.doom.wave++; this.doom.next += DM.every;
        }
        // 0.92: every minute of the Maîtres Corbacs (11:00, 12:00…, run time: pauses and slow frames change nothing),
        // a Manuel du Tailleur somewhere on the map (events.js doomReward; 0.95: no more maps, Jorbak gives them); one per minute mark
        if (this.doom.rwNext === undefined) this.doom.rwNext = Math.max(660, Math.ceil((this.doom.t0 - 0.5) / 60) * 60);   // (they come at 11:00: the first one then)
        if (this.time >= this.doom.rwNext) { this.doom.rwNext = Math.floor(this.time / 60) * 60 + 60; this.doomReward(); }
      }
    }
  }
  swarm(id, n) {
    const P = this.player; const a = rand(TAU); const vw = Game.viewW / 2 + 80;
    const sx = P.x + Math.cos(a) * vw * 1.1, sy = P.y + Math.sin(a) * Game.viewH * 0.6;
    for (let i = 0; i < n; i++) {
      const m = this.spawnMob(id, clamp(sx + rand(-60, 60), this.bounds.x0, this.bounds.x1), clamp(sy + rand(-90, 90), this.bounds.y0, this.bounds.y1));
      if (m) { m.swarm = { vx: -Math.cos(a), vy: -Math.sin(a) * 0.4, until: this.time + 9 }; m.speed *= 1.25; }
    }
  }
  ring(id, n) {
    const P = this.player; const r = Math.max(Game.viewW, Game.viewH) * 0.55;
    for (let i = 0; i < n; i++) {
      const a = i / n * TAU;
      const m = this.spawnMob(id, clamp(P.x + Math.cos(a) * r, this.bounds.x0, this.bounds.x1), clamp(P.y + Math.sin(a) * r * 0.75, this.bounds.y0, this.bounds.y1), { force: true });
      if (m) { m.ringer = true; }
    }
  }
  // ------------------------------------------------ damage
  // 0.84: one impact sound per real hit, each kind with its own sound and its own short throttle (the old shared
  // 85 ms throttle let any zone / poison tick eat a projectile's sound): 'spin' = orbiting spells (paf, paf, paf), 'dash'
  // = charges through the monsters (+ a tiny hit-stop), 'proj' = projectiles (C.hitSfx overrides the keys)
  hitSfx(kind) {
    const H = Object.assign({ spin: ['cybwork_hit_punch', 0.34, 1.15, 1.4, 0.05], dash: ['krak_impact', 0.42, 1.0, 1.25, 0.04], proj: [null, 0.2, 0.85, 1.25, 0.045] }, this.C.hitSfx || {})[kind]; if (!H) return;
    Audio2.hit(H[0] || pick(this.C.hitSnd || ['pok']), H[1], rand(H[2], H[3]), H[4]);
    if (kind === 'dash' && this.time - (this._dashStop || -9) > 0.06) { this._dashStop = this.time; this.hitStop(22); }
  }
  damageMob(m, dmg, src, quiet) {
    if (m.dying || !this.inRange(m)) return;
    const st = this.stats;
    if (src && src.p && src.p.execute && !m.boss && m.hp < m.maxHp * src.p.execute) dmg = Math.max(dmg, m.hp + 1);
    let crit = Math.random() < st.crit + (src && src.p && src.p.crit ? src.p.crit : 0) + (this.pandora && this.time < this.pandora.until ? this.pandora.crit : 0);
    if (m.markUntil > this.time) dmg *= 1 + m.markAmt;
    if (crit) dmg *= st.critMult;
    if (src && src.p && src.p.gamble && !quiet) { if (Math.random() < 0.5) { dmg *= 2; crit = true; } }
    dmg *= rand(0.9, 1.1);
    const real = Math.min(dmg, Math.max(0, m.hp));
    if (src && src.def) { const k = src.def.id; this.dmgBy[k] = (this.dmgBy[k] || 0) + real; }
    if (st.burn && Math.random() < st.burn && !m.dying) { m.burnUntil = this.time + 3; m.burnDps = Math.max(m.burnDps || 0, dmg * 0.25); }   // Kwakanneau de Flammes
    { const sc = Math.floor(this.time); if (sc !== this._dpsSec) { this.bestDps = Math.max(this.bestDps || 0, this._dpsCur || 0); this._dpsSec = sc; this._dpsCur = 0; } this._dpsCur += real; }   // DPS record (best single second)
    Prog.dealt(this, src, real, crit);
    if (st.leech && !this.player.dead && (this._leechN = (this._leechN || 0) + 1) <= 10) { this.player.leechHeal(real * st.leech); this.drainFx(m); }   // 0.22: 10 monsters per blow at most
    // tiny original hit sound (throttled); 0.84: projectiles, spinning spells and charges play their own (hitSfx)
    if (!(src && src._hitKind) && this.time - (this._hitSnd || -9) > 0.085 && (!quiet || Math.random() < 0.25)) { this._hitSnd = this.time; Audio2.play(pick(this.C.hitSnd || ['pok']), 0.184, rand(0.85, 1.25)); }
    m.hp -= dmg; m.flash = 1;
    if (!quiet || Math.random() < 0.35) { const n = crit ? 9 : 5, hy = m.y - m.r * 1.5; this.particles.push({ x: m.x + rand(-5, 5), y: hy, vx: 0, vy: 0, g: 0, t: 0, life: 0.12, s: crit ? 24 : 15.5, star: 1, c: crit ? '#ffe27a' : '#fff6d0' }); for (let k = 0; k < n; k++) { const a = rand(TAU), v = rand(140, 300); this.particles.push({ x: m.x + rand(-6, 6), y: hy + rand(-6, 6), vx: Math.cos(a) * v, vy: Math.sin(a) * v - 60, t: 0, life: rand(0.2, 0.36), s: rand(3.3, 6), c: crit ? pick(['#ffe27a', '#ff9a3a']) : pick(['#fff6d0', '#ffd27a', '#ffb14a']) }); } }   // hit sparks (0.38: bigger, a flash star + a burst)
    if (m.boss && this.time - (m._hitSnd || -9) > 0.7) { m._hitSnd = this.time; const k = Audio2.mobSnd(m.def.gfx, 'hit'); if (k) Audio2.play(k[k.length - 1], 0.4, rand(0.95, 1.05)); }
    if (this.cls.id === 'pandawa' && Math.random() < 0.1 && !m.boss) m.confuseUntil = this.time + 1.5;
    // 0.60: the hits on a monster within 0.35 s add up in ONE number that grows and pops (far fewer numbers on screen);
    // a crit keeps its own big orange number
    const tx = m._tx;
    // (0.67: the numbers hid the life bars: over a monster with a bar — boss, Maitre Corbac, Archimonster, scheduled
    // elite — they start above its bar and name: mobTop, render.js)
    const ny = (m.boss || m.doom || m.archi || m.timed) && m._top ? m.y - (m.liftH || 0) - m._top - 40 : m.y - m.r * 2.6 - 6;
    if (Store.data.settings.dmgNumbers && !crit && tx && tx.t < 0.35) {
      tx.v += dmg; tx.s = String(Math.round(tx.v)); tx.c = null; tx.t = 0.02; tx.n++; tx.size = Math.min(19, 14 + tx.n * 0.4); tx.x = m.x + tx.dx; tx.y = ny;
    } else if (Store.data.settings.dmgNumbers && (!quiet || crit || Math.random() < 0.3)) {
      if (crit) { const o = this.text(m.x + rand(-6, 6), ny - 4, Math.round(dmg) + '!', '#ffb02e', 18); if (o) o.num = 1; }   // (0.85: num = drawn like the client's damage numbers, NumCache)
      else { const dx = rand(-6, 6), o = this.text(m.x + dx, ny, Math.round(dmg), '#ff3300', 14); if (o) { o.v = dmg; o.n = 1; o.dx = dx; o.num = 1; m._tx = o; } }   // (the client's life-loss colour, clips/points/1/0.swf)
    }
    if (crit && Math.random() < 0.3) Audio2.sfx('Critical_Hit', 0.35, rand(0.9, 1.1));
    if (m.hp <= 0) this.killMob(m);
    if (src && src.def && src.def.sfusion && src.p) this.riderHit(m, dmg, src);   // 0.60: a fused spell's effect on every hit (sfusions.js)
  }
  // 0.98: a short poison zone (R.zones, z.dose): every monster in it or entering it before it fades is poisoned once
  // (z.dosed) with poisonMob(dps, dur) — the one way a poison reaches a monster from a single hit (the Piège Empoisonné's
  // gas, cloud 1; the poisoned spells' impacts, poisonPuff); dps as poisonMob takes it (before might / level)
  poisonCloud(x, y, r, dps, dur, life, spell, o = {}) { const z = { x, y, r, until: this.time + life, tick: 0.05, next: 0, dmg: 0, dose: { dps, dur }, dosed: new Set(), color: o.color || '#5fbf3a', spell, born: this.time, cloud: o.puff ? 0 : 1, puff: o.puff ? 1 : 0 }; this.zones.push(z); return z; }
  // a poisoned spell's impact on one monster: a little zone of PUFF.life s around it (C.run.poisonPuff can override);
  // an impact inside a fresh zone of the same spell leaves it to that one (its next tick doses the monster): an area
  // fusion's riders make one zone, not one a monster
  poisonPuff(m, dps, dur, spell) {
    const P = Object.assign({ r: 38, life: 0.25 }, this.RUN.poisonPuff), r = P.r * this.stats.area, T_ = this.time;
    for (const z of this.zones) if (z.puff && z.spell === spell && T_ - z.born < 0.1 && dist2(z.x, z.y, m.x, m.y) < z.r * z.r) { z.dose.dps = Math.max(z.dose.dps, dps); return; }
    this.poisonCloud(m.x, m.y, r, dps, dur, P.life, spell, { puff: 1 });
  }
  poisonMob(m, dps, dur, src) { const v = dps * this.stats.might * this.dmgMul(); m.poisonDps = m.poisonUntil > this.time ? Math.max(m.poisonDps || 0, v) : v; m.poisonUntil = this.time + (dur || 4); m.poisonSrc = src; }
  // 0.91: Transmutation (the Otomaï): an ordinary monster under `s.transmute` of its life is turned into gold at once;
  // any monster it kills drops kamas `s.gold` of the time
  transmute(m, s) {
    if (!m.dying && !(m.boss || m.doom || m.archi || m.timed || m.elite || m.def.special) && m.hp < m.maxHp * s.transmute) {
      const d = m.hp; m.hp = 0; if (s.spell) Prog.dealt(this, s.spell, d); this.killMob(m);
      for (let k = 0; k < 7; k++) { const a = rand(TAU), v = rand(60, 170); this.particles.push({ x: m.x, y: m.y - m.r, vx: Math.cos(a) * v, vy: -rand(80, 220), g: 500, t: 0, life: rand(0.4, 0.7), s: rand(2.5, 4.5), c: pick(['#ffe27a', '#ffd23a', '#fff4c0']) }); }
      if (!m._gold) { m._gold = 1; this.fxAt(806, m.x, m.y - m.r, { scale: 0.45 }); }
    }
    if (m.dying && !m._gk && s.gold && Math.random() < s.gold) { m._gk = 1; this.dropPickup('kama', m.x, m.y, randi(1, 3 + this.mapIdx)); }
  }
  killMob(m) {
    if (m.dying) return;
    m.dying = true; m.dieT = 0; this.kills++; if (m.doomCrow) Prog.add('doomCrows');
    this.juiceKill(m);   // (0.60: hit-stop, slow motion, flashes: juice.js)
    this.dyingN = (this.dyingN || 0) + 1;
    if (this.dyingN > 60 && !m.boss) m.fastDie = true;
    const d = m.def;
    Store.data.kills[d.id] = (Store.data.kills[d.id] || 0) + 1;
    // sound
    const own = Audio2.mobSnd(d.gfx, 'die'), bd = m.boss && !m.doom && this.C.bossDie ? this.C.bossDie[d.id] : null;
    if (bd) Audio2.play(bd, this.C.bossDieVol || 1.5, 1);
    else if (own) Audio2.play(own[0], m.boss ? (m.doom ? 0.5 : 0.95 * (this.C.bossDieVol || 1.5)) : 0.345, rand(0.92, 1.1));
    else Audio2.sfx(dieSoundFor(d), m.boss ? (m.doom ? 0.5 : 0.9 * (this.C.bossDieVol || 1.5)) : 0.368, rand(0.92, 1.12));
    // particles
    const n = m.boss ? 30 : 6;
    for (let i = 0; i < n && this.particles.length < 300; i++) this.particles.push({ x: m.x, y: m.y - m.r, vx: rand(-90, 90), vy: rand(-160, -30), t: 0, life: rand(0.4, 0.8), c: pick(['#fff6c8', '#ffd27a', '#ffffff', '#c8f0ff']), s: rand(2, 4) });
    // drops
    if (m.archi) this.archiDeath(m);
    if (m.def.special) this.specialDeath(m);   // Tofu Mutant, Coffre Animé (events.js)
    if (m.boss) return this.bossDeath(m);
    if (m.elite && this.ps) this.ps.elites++;
    if (d.id === 'bandit_manchot' || d.jackpot) { const J = d.jackpot || [30, 60], k = this.addKamas(randi(J[0], J[1])); this.banner(T('jackpot', { n: k }), '#ffd700'); this.chat(T('jackpot', { n: k }), '#ffd700'); }
    if (d.id === 'wabbit_gm') { this.addKamas(100); this.chat(T('gm_banned'), '#ff9de2'); this.banner('Wabbit GM', '#ff9de2'); Store.data.easter.gm = 1; }
    if (d.xp > 0) { if (m.elite) this.dropGem(m.x, m.y, this.bigAmber(), 1); else if (!this.RUN.amber) this.dropGem(m.x, m.y, d.xp * (m.xpm || 1)); else for (let r = this.amberRate(); r > 0; r--) if (r >= 1 || Math.random() < r) this.dropGem(m.x + rand(-8, 8), m.y + rand(-6, 6), this.normalAmber()); }   // 0.81: an amber's worth = the run's clock only (same on every map), each map drops them at its own rate   // 0.60: an elite's amber = a big amber
    const luck = this.stats.luck, IK = luck * (this.RUN.itemDropK || 1);   // (0.60: itemDropK = every object on the ground x1.15)
    if (!this.map.noKamas && Math.random() < (this.RUN.kamaDrop || 0.05) * (this.hard ? this.hard.kamaDrop || 1 : 1) * luck) {   /* (0.94: Difficile x1.5, C.hard.kamaDrop) */ const KC = this.RUN.kamaCoins || [1, 1], n = randi(KC[0], KC[1]); for (let k = 0; k < n; k++) this.dropPickup('kama', m.x + rand(-14, 14), m.y + rand(-10, 10), randi(1, 3 + this.mapIdx)); }   // 0.60: 1 to 3 coins
    if (Math.random() < (this.RUN.breadRate || 0.006) * IK) this.dropPickup('bread', m.x, m.y, this.breadKind());
    if (!this.map.noKamas && Math.random() < (this.RUN.goldRate || 0) * IK) this.dropPickup('gold', m.x, m.y);   // Minerai d'Or (rare object: Chance helps)
    if (Math.random() < 0.0012 * IK && !this.pickups.some(p => p.kind === 'batofu')) this.dropPickup('batofu', m.x, m.y);   // Plume du Batofu
    const KB = this.C.kamaBoost;
    if (KB && Math.random() < KB.rate * IK && this.kboostUntil < this.time && !this.pickups.some(p => p.kind === 'kamaboost')) this.dropPickup('kamaboost', m.x, m.y);
    if (Math.random() < 0.0012 * IK) this.dropPickup('rappel', m.x, m.y);
    if (Math.random() < 0.0008 * IK) this.dropPickup('fee', m.x, m.y);
    if (Math.random() < 0.0009 * IK) this.dropPickup('sablier', m.x, m.y);
    { const H = this.C.houx; if (H && Math.random() < H.rate * IK) this.dropPickup('houx', m.x, m.y); }   // 0.97: the Bague Houx (C.houx.rate: a third of a spell scroll's)
    for (const k in this.C.drops) { const dr = this.C.drops[k]; if (Math.random() < dr.rate * IK && !this.pickups.some(p => p.kind === 'power' && p.v === k)) this.dropPickup('power', m.x, m.y, k); }
    if (m.elite && !m.noChest) { this.dropPickup('chest', m.x, m.y, 1); }
    if (m.elite) this.maybeEliteRelic(m);   // 0.60: elites may drop a relic (extras.js)
    if (d.special) this.maybeRelic(m, true);   // 0.38: the mini-bosses with a big life bar (Tofuzmo, Coffre Animé)
    // the Manuel du Tailleur: rolled once per run (about one full run in ten), dropped by the first monster killed after its time
    if (this.manuelAt !== null && this.time >= this.manuelAt) {
      this.manuelAt = null; this.dropPickup('manuel', m.x, m.y);
      this.chat(T('tailor_drop', { n: L(this.C.manuel.name) }), '#ff9cf0'); Audio2.sfx('EVENT', 0.45);
      this.rings.push({ x: m.x, y: m.y, r0: 10, r1: 70, t0: this.time, dur: 0.6, color: '#ff9cf0' });
    }
  }
  // a random look (hat, cape or pet) not owned yet; everything owned: kamas instead. Saved at once (the show comes after)
  tailorPrize() {
    const S = Store.data, C = this.C;
    const pool = [...C.hats.map(i => ['hats', i]), ...C.capes.map(i => ['capes', i]), ...C.pets.map(i => ['pets', i])].filter(([, i]) => !S.owned.includes(i.id));
    if (!pool.length) { const v = (C.manuel && C.manuel.kamas) || 2500; S.kamas += v; Store.save(); return { kind: 'kamas', v }; }
    const [kind, item] = pick(pool); S.owned.push(item.id); Prog.add('tailor'); Store.save(); Prog.check(null);
    return { kind, item };
  }
  bossDeath(m) {
    const d = m.def; Prog.bump('bossById', d.id);
    this.bossAlive = this.bossAlive.filter(b => b !== m);
    if (d.doom) { this.shake(4); Audio2.blip('boom'); this.dropPickup('plumec', m.x, m.y); if (this.ps) this.ps.corbacs = (this.ps.corbacs || 0) + 1; return; }   // a Plume du Maître Corbac
    if (this.ps) this.ps.bosses++;
    this.bossesDown.add(d.id);
    this.shake(10); Audio2.blip('boom');
    this.dropGem(m.x, m.y, this.rareAmber(), 2);   // 0.82: the Ambre du Chêne Mou = 5x an ancestral amber
    const fin = this.isFinalKill(m);   // (0.68: a group of final bosses — the four Kwakeres — counts when the last one falls)
    this.dropPickup('chest', m.x, m.y + 10, fin ? 5 : 3).boss = true;   // the boss chest: bigger, red aura, on the minimap
    this.maybeRelic(m); this.maybeCoffre(m);
    if (m.endless) Prog.add('endlessBosses');
    // 0.37: the Endless final bosses drop the Manuel du Tailleur; 0.95 (was 50 %): 5 % from 10:00, +2.5 % per minute after (C.infinite.manuelP / manuelStep)
    // 0.98: every boss may drop it, by its place in the game (C.manuel.boss: Bouftou Royal 1 % ... Goultard 5 %; a boss of
    // no zone's list: its zone's final boss's chance); an Endless one keeps the better of the two
    const IM = this.C.infinite, mw = Math.max(0, Math.floor((this.time - (IM.bossT || 600)) / 60)), MB = (this.C.manuel && this.C.manuel.boss) || {};
    const mp = d.finalGroup && !fin ? 0 : MB[d.id] !== undefined ? MB[d.id] : MB[(this.map.bosses[this.map.bosses.length - 1] || [])[1]] || 0;   // (the four Kwakeres: one roll, the last one)
    if (this.C.manuel && Math.random() < Math.max(mp, m.endless ? (IM.manuelP || 0.05) + (IM.manuelStep || 0.025) * mw : 0)) {
      this.dropPickup('manuel', m.x + 30, m.y); this.chat(T('tailor_drop', { n: L(this.C.manuel.name) }), '#ff9cf0'); Audio2.sfx('EVENT', 0.45);
    }
    for (let i = 0; i < 6; i++) this.dropPickup('kama', m.x + rand(-40, 40), m.y + rand(-30, 30), randi(2, 5) * (1 + this.mapIdx));   // v1.6: kamas /5
    // Dofus eggs
    const luck = this.stats.luck;
    for (const dof of this.C.dofus) {
      let rate = 0;
      if (dof.from.includes(d.id)) rate = dof.rate;
      if (dof.from.includes('any_final') && fin) rate = Math.max(rate, dof.rate);
      if (rate && Math.random() < rate * luck && !this.dofus.includes(dof) && !this.pickups.some(p => p.kind === 'dofus' && p.v === dof.id)) { this.dropPickup('dofus', m.x + 20, m.y, dof.id); this.celebrateDofus(dof, m.x + 20, m.y, L(d.name)); }
    }
    if (fin && !this.finalKilled) {
      // zone cleared: the rewards are secured now, and the run goes on until the end (10:00 brings the Maîtres Corbacs)
      this.finalKilled = true;
      this.claimVictory();
      if (this.map.troolTicket) this.dropPickup('trool', m.x, m.y, 1);   // (0.68: Nowel's final boss drops the Trool fair ticket)
      this.chat(T('final_down'), '#ffe066');   // (0.60: the big 'VICTOIRE !' is drawn by juice.js during the slow motion)
      Audio2.sfx('EVENT', 0.9);
    }
    if (d.id === 'dark_vlad' && this.hard && !m.endless && this.map.id === 'vlad') this.vladFall(m);   // 0.52: the Goultard secret (events.js)
    if (d.id === 'goultard' && !m.endless) this.goultardFall(m);   // 0.60: his defeat scene, the first time (events.js)
  }
  // big: 1 = a big amber (elites, Archimonsters), 2 = the rare glowing one (bosses); merged gems are big too
  dropGem(x, y, v, big) {
    if (this.pickups.length > 520) { // merge into nearest big gem
      const g = this.pickups.find(p => p.kind === 'gem' && !p.big); if (g) { g.v += v; g.big = true; return; }
    }
    this.placeDrop(this.pickups[this.pickups.push({ kind: 'gem', x: x + rand(-4, 4), y: y + rand(-4, 4), v, t: 0, mag: false, big: !!big || (!this.RUN.amber && v >= 25), anc: big === 1, rare: big === 2 }) - 1]);   // (0.81: anc = an ancestral amber, drawn twice as big)
  }
  // 0.60: a normal amber = what the monsters of the current wave give on average; a big amber (elites, Archimonsters,
  // bosses) = C.run.bigAmberK (1.3) of it
  normalAmber() {
    const A = this.RUN.amber; if (A) return A.v0 * Math.pow(1 + A.grow, Math.floor(this.time / (A.step || 30)));   // 0.81: a little more every 30 s
    const tm = this.time / 60, w = this.map.waves.find(x => tm >= x[0] && tm < x[1]) || this.map.waves[this.map.waves.length - 1];
    let s = 0, n = 0; for (const [id, wt] of w[2]) { const d = this.C.monsters[id]; if (d && d.xp > 0) { s += d.xp * wt; n += wt; } }
    return (n ? s / n : 0.2) * this.norm()[2];
  }
  // 0.81: ambers per kill = the wave's spawn interval / C.run.amber.ref: a player who kills everything gets the same
  // number of ambers a second on every map (monsters come every wave[3] s; tools/content/calc_amber081.py)
  amberRate() { const A = this.RUN.amber, tm = this.time / 60, w = this.map.waves.find(x => tm >= x[0] && tm < x[1]) || this.map.waves[this.map.waves.length - 1]; return w[3] / (A.ref || 0.55); }
  bigAmber() { return this.normalAmber() * (this.RUN.bigAmberK || 1.3); }
  rareAmber() { return this.bigAmber() * (this.RUN.rareAmberK || 1); }   // (0.81: the ancestral amber = 5x a normal one, C.run.bigAmberK)
  dropPickup(kind, x, y, v) { const p = { kind, x, y, v, t: 0, mag: false }; this.pickups.push(p); this.placeDrop(p); return p; }
  // 0.92: what falls never lies on another drop, nor out of the ground the character can walk (Run.bounds, a little
  // inside): a drop touching another moves to the nearest free spot on rings around (flattened like the ground); the
  // drops being pulled to the character don't count. Its size by kind (the ambers by their picture's size, render.js)
  dropR(p) { if (p.kind === 'gem') return p.rare ? 30 : p.anc ? 13 : p.big ? 10 : 7; return DROP_R[p.kind] || 12; }
  placeDrop(p) {
    const b = this.bounds, M = 14, r = p._r = this.dropR(p);
    p.x = clamp(p.x, b.x0 + M, b.x1 - M); p.y = clamp(p.y, b.y0 + M, b.y1 - M);
    const reach = r + 12 * 11 + 34, near = [];
    for (const q of this.pickups) if (q !== p && !q.mag && Math.abs(q.x - p.x) < reach && Math.abs(q.y - p.y) < reach) near.push(q);
    if (!near.length) return;
    const free = (x, y) => { for (const q of near) { const d = r + (q._r || 12), dx = q.x - x, dy = (q.y - y) / 0.75; if (dx * dx + dy * dy < d * d) return false; } return true; };
    if (free(p.x, p.y)) return;
    const x0 = p.x, y0 = p.y, a0 = rand(TAU);
    for (let ring = 1; ring <= 11; ring++) {
      const rr = ring * 12, n = 6 + ring * 3;
      for (let i = 0; i < n; i++) {
        const an = a0 + i / n * TAU, x = clamp(x0 + Math.cos(an) * rr, b.x0 + M, b.x1 - M), y = clamp(y0 + Math.sin(an) * rr * 0.75, b.y0 + M, b.y1 - M);
        if (free(x, y)) { p.x = x; p.y = y; return; }
      }
    }
  }
  // the purse (kamaboost) simply doubles what you pick up
  addKamas(k) { const v = Math.max(1, Math.round(k * this.stats.greed * (this.RUN.kamaRate || 1))) * (this.time < this.kboostUntil ? 2 : 1); this.kamas += v; return v; }
  // 0.22: four breads by time: Amakna (10) until 4:00, then Blé Complet (20) half the time, from 8:00 a third each
  // (+1% Chapain, full life), after 10:00 only Pains des Champs (30)
  breadKind() { const m = this.time / 60; if (m < 4) return 'amakna'; if (m < 8) return Math.random() < 0.5 ? 'ble' : 'amakna'; if (m < 10) { if (Math.random() < 0.01) return 'chapain'; return pick(['amakna', 'ble', 'champs']); } return 'champs'; }
  // final boss down: the zone counts as cleared, the next zone opens; once every zone is cleared, the secret zones open
  claimVictory() {
    const S = Store.data;
    S.cleared[this.map.id] = (S.cleared[this.map.id] || 0) + 1;
    if (this.hard) { const CH = S.clearedHard = S.clearedHard || {}; CH[this.map.id] = (CH[this.map.id] || 0) + 1; }   // (0.92: the zone won in Difficile, its mark on the play screen)
    else if (!this.infinite) { const CN = S.clearedNormal = S.clearedNormal || {}; CN[this.map.id] = (CN[this.map.id] || 0) + 1; }   // (0.95: won in Normal: the zone's beginners' help ends)
    if (this.map.id === (this.C.gany || {}).unlockHard && !S.hardUnlocked) { S.hardUnlocked = 1; this.hardUnlockedNow = true; }   // (0.95: Grobe won: Difficile opens; Ganymède says so at the end, Game.runOver)
    this.unlockNext();
    const vis = this.C.maps.filter(m => !m.hidden);
    if (vis.every(m => S.cleared[m.id])) for (const m of this.C.maps.filter(m => m.hidden && !m.unlockAch && !m.unlockBy)) if (!S.unlocked.includes(m.id)) { S.unlocked.push(m.id); this.unlockedNow.push(Object.assign({ secret: true }, m)); }
    Store.save();
  }
  // 0.34: the next zone opens only once this one is done AND every one of its bosses fell in the same run
  // (the secret zones keep their own rules)
  unlockNext() {
    const S = Store.data;
    if (!this.finalKilled || !(this.map.bosses || []).every(b => this.bossesDown.has(b[1]))) return;
    const next = this.C.maps.slice(this.mapPos + 1).find(m => !m.hidden);
    if (next && !S.unlocked.includes(next.id)) { S.unlocked.push(next.id); this.unlockedNow.push(next); }
  }
  damagePlayer(dmg, src, area) {   // area: a ground area hit (telegraphs, puddles, spins), which reaches an invisible Sram
    const P = this.player, st = this.stats;
    if (P.dead || this.over) return;
    if (this.hard) dmg *= this.hard.dmg;   // Difficile: every enemy blow +50%
    if (this.aid) dmg *= this.aid.dmg;   // 0.95: the beginners' help (the first three zones until won in Normal)
    if (this.time < P.invulnUntil || (this.time < P.invisUntil && !area)) return;   // (0.98: invisible = no projectile nor contact blow, the areas he stands in still hit)
    if (st.evade && Math.random() < st.evade && this.time - P.lastHit > 0.22) { P.lastHit = this.time; this.text(P.x, P.y - 72, T('dodge') + ' !', '#9fe0ff', 13); return; }
    if (this.time - P.lastHit < 0.22) return;
    const lib = this.powers.liberation;
    if (lib && this.time < lib.until && lib.charges > 0) { this.liberation(); P.lastHit = this.time; if (this.slowMo) { this.slowMo(0.45, 0.45); this._libCA = performance.now(); } return; }   // (0.98: a short slow motion and its aberration as it saves him)
    if (src && src.def && !src.boss) { const a = Audio2.mobSnd(src.def.gfx, 'atk'); Audio2.play(a ? a[0] : 'son_attack', 0.45, rand(0.92, 1.08)); }
    else if (src && src.boss) { const a = Audio2.mobSnd(src.def.gfx, 'atk'); if (a) Audio2.play(a[0], 0.6); }
    if (P.shieldUp) { P.shieldUp = false; P.shieldNext = this.time + 12; this.text(P.x, P.y - 70, T('blocked'), '#7fd0ff', 14); P.lastHit = this.time; this.fxAt(802, P.x, P.y + 6, { follow: P, scale: 0.45, sym: 'root' }); Audio2.ui('shield', 0.7); return; }
    let armor = st.armor + (P.tempArmor && this.time < P.tempArmor.until ? P.tempArmor.v : 0) + (P.shieldArmor && this.time < P.shieldArmor.until ? P.shieldArmor.v : 0);
    const d = Math.max(1, dmg - armor);
    if (st.thorns && src && src.def && !src.dying && !src.proj) this.damageMob(src, d * st.thorns, null, true);   // Ceinture du Prespic
    P.hp -= d; P.lastHit = this.time; if (this.time - (P._flashT || -9) > 0.6) { P.hitFlash = 1; P._flashT = this.time; } this.dmgTaken += d; this.juiceHurt(d);
    Prog.taken(this, d, src);
    if (st.reflect && src && src.def && !src.dying && !src.doom) { // Renvoi de dommages
      this.damageMob(src, Math.min((d + 4) * (1 + st.reflect) * 1.5, 150 * Math.min(1, st.reflect / 5), src.maxHp * 0.5), { def: { id: 'renvoi' }, p: {} }, true);   // 0.37: at most 30 per level (150 at level 5) and half the monster's life
      if (src.dying) Prog.add('reflectKills');
      if (!src.boss) { const dx = src.x - P.x, dy = src.y - P.y, dd = Math.hypot(dx, dy) || 1; src.kx += dx / dd * 260; src.ky += dy / dd * 260; }
    }
    { const o = this.text(P.x + rand(-8, 8), P.y - 76, '-' + Math.round(d), '#ff3300', 16); if (o) o.num = 1; }   // (0.85: the client's life-loss number, NumCache)
    // 0.89: Armure Incandescente / Rempart élémentaire: hit while the armour burns, the Féca answers with a burst of fire
    if (!(this.time - (this._retalT || -9) < 0.6)) for (const z of this.zones) if (z.retal && z.follow === P) {
      this._retalT = this.time; const r = z.r * 1.2;
      for (const m of this.mobsInRadius(P.x, P.y, r)) { this.damageMob(m, z.dmg * z.retal, z.spell); m.burnUntil = this.time + 2.5; m.burnDps = Math.max(m.burnDps || 0, z.dmg * 0.8 * this.stats.might); if (!m.boss) { const dx = m.x - P.x, dy = m.y - P.y, d = Math.hypot(dx, dy) || 1; m.kx += dx / d * 160; m.ky += dy / d * 160; } }
      this.rings.push({ x: P.x, y: P.y, r0: 12, r1: r, t0: this.time, dur: 0.4, color: '#ffb040', fill: 1 }); for (let k = 0; k < 22; k++) { const an = rand(TAU), v = rand(160, 340); this.particles.push({ x: P.x + Math.cos(an) * 14, y: P.y - 18, vx: Math.cos(an) * v, vy: Math.sin(an) * v * 0.6 - 60, g: 260, t: 0, life: rand(0.35, 0.6), s: rand(3, 6), c: pick(['#ffb040', '#ff6a1e', '#ffe08a']) }); }   // (a burst of embers: the sphere of the cast hid the character)
      Audio2.play('explosion', 0.35, rand(1.1, 1.3)); this.shake(3);
      break;
    }
    if (this.time - (this._hurtSnd || -9) > 0.35) { this._hurtSnd = this.time; const k = Audio2.charSnd(this.charSid, 'hitR'); Audio2.play(k ? k[0] : 'hit_defaut', 0.55); }
    if (P.hp <= 0 && st.revive && !this.revived) { // Phénix: back to life once
      this.revived = true; P.hp = Math.round(st.maxHp * 0.5); P.invulnUntil = this.time + 3.5;
      // 0.36: a retro-style revival (render.js drawReviveBack / drawReviveFront): the character falls, orange powder
      // spirals in, a burst, phoenix wings open on its back and beat, then crumble into embers. The run holds 1.4 s
      this.reviveAt = typeof performance !== 'undefined' ? performance.now() : 0; this.reviveHold = this.reviveAt + 1400;
      for (const m of this.mobsInRadius(P.x, P.y, 220)) if (!m.boss) this.damageMob(m, st.maxHp * 2, { def: { id: 'phenix' }, p: {} }, true);
      Audio2.play(this.C.revive.snd, 0.9);
      this.banner(T('revived'), '#ffcf3a'); this.chat(T('revived'), '#ffcf3a'); this.shake(6);
      for (const m of this.mobsInRadius(P.x, P.y, 260)) if (!m.boss) { const dx = m.x - P.x, dy = m.y - P.y, dd = Math.hypot(dx, dy) || 1; m.kx += dx / dd * 700; m.ky += dy / dd * 700; }
      Prog.add('revived'); return;
    }
    if (P.hp <= 0) { P.hp = 0; P.dead = true; P.deathT = 0; if (src && src.def && /^tofu/.test(src.def.id)) Prog.add('tofuDeaths'); if (this.time < 60) Prog.add('quickDeaths'); this.shake(8); const k = Audio2.charSnd(this.charSid, 'dieR'); if (k) Audio2.play(k[k.length - 1], 0.8); this.juiceDeath(); }   // (0.59: the run ends in update, 2.2 s after the fall; 0.61: the dramatic fall, juice.js)
  }
  // ------------------------------------------------ xp / levels
  addXP(v) {
    this.xp += v * this.stats.growth * (this.RUN.xpPace || 1.8) * this.xpLateK();
    while (this.xp >= this.xpNext) {
      this.xp -= this.xpNext; this.level++;
      // v2.0: the first levels need more experience (no more spam of choices in the first minute), the rest is unchanged
      const XE = this.RUN.xpEarly || [];
      const XB = this.RUN.xpBack;   // (0.98: the experience taken off the first levels, given back level by level: xpBack.add[level - from])
      this.xpNext = Math.round((this.level < 20 ? 5 + (this.level - 1) * 10 : this.level < 40 ? 195 + (this.level - 20) * 22 : 640 + (this.level - 40) * 40) * (XE[this.level - 1] || 1)) + ((XB && XB.add[this.level - XB.from]) || 0);
      this.pendingLevels++; if (this.ps) this.ps.levelups++;
    }
  }
  // ownedOnly: chests only improve what was already picked (no new spell, weapon, evolution or characteristic)
  upgradeOptions(n, ownedOnly) {
    const opts = [];
    const ownedIds = [...this.spells.map(s => s.def.id), ...this.consumed];   // (a fused spell's ingredients never come back)
    for (const s of this.spells) if (!s.maxed) opts.push({ kind: 'spell', id: s.def.id, lv: s.level + 1, w: 1.0 });
    if (!ownedOnly && this.spells.length < this.spellSlots()) for (const id of this.cls.spells) if (!ownedIds.includes(id)) opts.push({ kind: 'spell', id, lv: 1, w: this.level < 12 ? 2.4 : 1.4, isNew: true });
    if (!ownedOnly && this.spells.length < this.spellSlots()) this.globalOptions(opts, ownedIds);   // 0.23: global spells (gspells.js)
    if (this.weapon) {
      if (!this.weapon.maxed) opts.push({ kind: 'weapon', id: this.weapon.def.id, lv: this.weapon.level + 1, w: ownedOnly ? 1.0 : 1.3 });
    }
    else if (!ownedOnly && this.level >= 3) for (const d of this.weaponChoices(2)) opts.push({ kind: 'weapon', id: d.id, lv: 1, w: 0.715, isNew: true });   // (0.60: two of the 40 weapons, weapons.js)
    // (0.95: weapons offered 25 % more often — weights x1.3 (1.0 / 0.55 before): measured on bot runs' level-ups, x1.3
    // shows a weapon in +24 to +27 % more of them; x1.25 gave only +20 %, the cards being drawn without replacement). The
    // chests (ownedOnly) keep the old weight: only the level-up choices are concerned
    this.fusionOptions(opts, ownedOnly);   // 0.25 (weapons.js)
    this.sfusionOptions(opts);   // 0.60: spell fusions (sfusions.js), chests included
    const pcount = Object.keys(this.passives).length;
    for (const p of this.C.passives) {
      const lv = this.passives[p.id] || 0;
      if (lv >= p.max) continue;
      if (p.stat === 'spellslot' && this.cls.spells.length <= (this.C.spellSlots || 4)) continue;   // Borné: only when the class has a spell left to learn
      if (!lv && (pcount >= (this.RUN.passiveSlots || 6) || ownedOnly)) continue;   // (0.82: 5 characteristics, C.run.passiveSlots)
      opts.push({ kind: 'passive', id: p.id, lv: lv + 1, w: (lv ? 0.9 : 0.6) * (p.offerK || 1), isNew: !lv });   // (0.95: offerK — Démultiplication 0.5)
    }
    const out = [];
    const pool = opts.filter(o => !this.isBanned(o));   // (0.60: what was banished never comes back this run)
    { const sf = pool.find(o => o.kind === 'sfusion'); if (sf && n > 0) { out.push(sf); pool.splice(pool.indexOf(sf), 1); } }   // (0.60: a ready spell fusion is always offered)
    while (out.length < n && pool.length) {
      const it = weighted(pool.map(o => [o, o.w]));
      out.push(it); pool.splice(pool.indexOf(it), 1);
    }
    return out;
  }
  // 0.60: Bannir — a card never comes back this run; 0.95: a weapon bans its whole type (C.uniqueWeapons' `of`, the
  // base weapons' id), its level-ups included
  banKey(o) { return o.kind === 'weapon' ? 'wtype:' + weaponType(this.C, o.id) : o.kind + ':' + o.id; }
  banish(o) { this.banned.add(this.banKey(o)); }
  isBanned(o) { return this.banned.has(this.banKey(o)); }
  applyUpgrade(o) {
    if (o.kind === 'spell' && this.C.spells[o.id].t === 'wheel') { this.trool(); return; }   // Jeton de la Foire du Trool
    if (o.kind === 'spell') {
      const s = this.spells.find(s => s.def.id === o.id);
      if (s) s.levelUp(); else this.addSpell(o.id);
    } else if (o.kind === 'weapon') {
      if (this.weapon) this.weapon.levelUp(); else { this.weapon = new SpellInst(this, weaponById(this.C, o.id)); this.charSprite.weapon = this.weapon.def.acc || null; this.chat(T('weapon_one'), '#ffd27a'); this.gotWeapon(this.weapon.def); }
    } else if (o.kind === 'wevo') {
      if (this.weapon && !this.weapon.finale) {
        this.weapon.evoUp(o.id);
        const e = ((this.C.weaponEvo || {})[this.weapon.def.id] || []).find(x => x.id === o.id);
        if (e) { this.weapon.finale = e; if (e.skin) this.charSprite.weapon = e.skin; if (e.stats) this.recompute(); this.chat('✦ ' + L(e.name) + ' — ' + L(e.skinName || e.name), '#ffd27a'); }
      }
    }
    else if (o.kind === 'fusion') this.applyFusion(o.id);
    else if (o.kind === 'sfusion') this.applySFusion(o.id);
    else if (o.kind === 'passive') { this.passives[o.id] = (this.passives[o.id] || 0) + 1; this.recompute(); }
    else if (o.kind === 'kamas') { const v = this.addKamas(this.C.maxKamas || 10); this.text(this.player.x, this.player.y - 80, '+' + v + ' K', '#ffd700', 16); }
    else if (o.kind === 'bread') this.massPotion();   // (0.53: the mass healing potion; the kind keeps its old name, saved in the settings)
  }
  // ------------------------------------------------ summons
  summonBlow(s) { return s.spell.dmg ? s.spell.dmg() * (this.cls.id === 'osamodas' ? 1.4 : 1) * (s.k || 1) : s.dmg * this.dmgMul(); }   // one melee blow of a summon, read now
  spawnSummon(spell, x, y, k = 1) {   // (k: 0.96, a copy added by Démultiplication hits at C.run.extraK)
    const p = spell.p; const by = spell.def.spriteKeyBy, key = (by && by[this.charSid]) || p.spriteKey, cs = this.summonChars && this.summonChars[key];
    const sh = p.decoy || cs ? null : MobSheets.c[key]; if (!sh && !p.decoy && !(cs && cs.ready)) return;
    const st = this.stats;
    // (0.68: Portée makes the summons faster and lets them see / go farther; their blows hit around them with p.aoe)
    this.summons.push({ spell, sh, x, y, hp: p.hp, k, dmg: spell.dmg() / (this.dmgMul() || 1) * (this.cls.id === 'osamodas' ? 1.4 : 1) * k, speed: p.speed * st.projspeed, aoe: p.aoe || 0, until: this.time + p.duration * st.duration,
      t: rand(1), flip: false, hitT: 0, target: null, kamikaze: p.kamikaze, taunt: p.taunt, radius: p.radius || 0, kamas: p.kamas, fly: p.fly, born: this.time,
      decoy: p.decoy, ranged: p.ranged, healer: p.healer, view: 'R', flipP: this.player.flip, cs, cad: p.hitJit ? rand(1 - p.hitJit, 1 + p.hitJit) : 1 });   // (0.98: cad, its blows' rhythm drawn once)
    this.fxAt(1100, x, y, {});
    const sm = this.summons[this.summons.length - 1];
    sm.snd = (this.C.summonSnd || {})[spell.def.id]; this.sndOf(sm.snd, 'spawn', 0.5);
    for (let i = 0; i < 6; i++) this.particles.push({ x, y: y - 10, vx: rand(-60, 60), vy: rand(-80, -10), t: 0, life: 0.5, c: '#e8f6ff', s: 3 });
    return sm;
  }
  // ------------------------------------------------ main update
  // 0.91: an action `sec` seconds of run time later (paused with the run; a real-time setTimeout kept spawning monsters
  // and giving kamas during the pause / a cinematic, and after the run's end)
  after(sec, fn) { (this._later || (this._later = [])).push({ at: this.time + sec, fn }); }
  update(dt) {
    if (this.over) return;
    this._leechN = 0;
    const P = this.player;
    this.time += dt;
    if (this._later && this._later.length) { const due = this._later.filter(l => l.at <= this.time); if (due.length) { this._later = this._later.filter(l => l.at > this.time); for (const l of due) l.fn(); } }
    // grid
    this.grid.clear();
    for (const m of this.mobs) if (!m.dying) this.grid.add(m);
    P.update(dt, Input.vector());
    if (P.dead && P.deathT >= 2.2) { this.endRun(false); return; }   // (0.59: 2.2 s of run time after the fall; a real-time setTimeout ended the run during the pause / a cinematic)
    if (!P.dead) {
      this.spawner(dt);
      this.updateExtras(dt); this.updateGlobals(); this.updateWeapons(dt); this.updateEvents(dt); this.updateBosses(dt);
      for (const s of this.spells) s.update(dt);
      if (this.weapon) this.weapon.update(dt);
      this.updatePowers(dt);
    }
    this.updateMobs(dt);
    this.updateProjectiles(dt);
    this.updateAttacks(dt);
    this.updateBombs(dt);
    this.updateTosses(dt);
    this.updateSummons(dt);
    this.updatePickups(dt);
    this.updateFx(dt);
    if (this.fw) this.updateFireworks();
    // door
    if (this.door && !P.dead) {
      const near = dist2(P.x, P.y, this.door.x, this.door.y) < 42 * 42;
      if (near && !this.door.asked) { this.door.asked = true; Game.doorPrompt(); }
      if (!near && dist2(P.x, P.y, this.door.x, this.door.y) > 90 * 90) this.door.asked = false;
    }
    // level ups
    if (this.pendingLevels > 0 && !P.dead && !UI.modalOpen()) { this.pendingLevels--; Game.levelUp(); }
    // camera
    const [cx, cy] = this.camTarget();
    this.cam.x = lerp(this.cam.x || cx, cx, Math.min(1, dt * 10)); this.cam.y = lerp(this.cam.y || cy, cy, Math.min(1, dt * 10));
    this.shakeAmt = Math.max(0, this.shakeAmt - dt * 30);
    if (this.bannerMsg) { this.bannerMsg.t += dt; if (this.bannerMsg.t > 3.2) this.bannerMsg = null; }
  }
  updateMobs(dt) {
    const P = this.player, frozen = this.time < this.freezeUntil;
    const invis = this.time < P.invisUntil;
    const taunts = this.summons.filter(s => s.taunt);
    const vw = Game.viewW, vh = Game.viewH, kdec = Math.pow(0.02, dt);
    for (let i = this.mobs.length - 1; i >= 0; i--) {
      const m = this.mobs[i];
      m.t += dt; if (m.flash > 0) m.flash -= dt * 6;
      if (m.atkAnimT !== undefined) m.atkAnimT += dt;   // (0.59: was + 1/60 per drawn frame in drawMob: faster on 144 Hz screens, running on during the pause)
      if (m.dying) {
        m.dieT += dt;
        const dd = m.fastDie ? 0.05 : (m.sh.duration('dieR') || 0.5);
        if (m.dieT > Math.min(dd, m.boss ? 4 : 1.3) + 0.25) { this.mobs.splice(i, 1); this.dyingN--; }
        continue;
      }
      if (m.carried) continue;
      // dot
      if (m.burnUntil > this.time) { m.hp -= m.burnDps * dt; if (m.hp <= 0) { this.killMob(m); continue; } }
      if (m.poisonUntil > this.time) { const d = Math.min(m.hp, m.poisonDps * dt); m.hp -= m.poisonDps * dt; if (m.poisonSrc) Prog.dealt(this, m.poisonSrc, d); if (m.hp <= 0) { this.killMob(m); continue; } }   // 0.23: poison counted in the spell's damage
      if (frozen && !m.boss) { m.kx *= 0.8; m.ky *= 0.8; continue; }
      if (m.flingUntil > this.time) { m.x = clamp(m.x + m.kx * dt, this.bounds.x0, this.bounds.x1); m.y = clamp(m.y + m.ky * dt, this.bounds.y0, this.bounds.y1); m.kx *= kdec; m.ky *= kdec; continue; }   // thrown far away (Libération)
      if (m.stunUntil > this.time) { m.x += m.kx * dt; m.y += m.ky * dt; m.kx *= 0.85; m.ky *= 0.85; continue; }
      let tx = P.x, ty = P.y;
      if (taunts.length && !m.boss) { let best = null, bd = 170 * 170; for (const s of taunts) { const d = dist2(m.x, m.y, s.x, s.y); if (d < bd) { bd = d; best = s; } } if (best) { tx = best.x; ty = best.y; } }
      let dx = tx - m.x, dy = ty - m.y; let d = Math.hypot(dx, dy) || 1;
      let mx = dx / d, my = dy / d;
      let sp = m.speed * (m.slowUntil > this.time ? 1 - m.slowAmt : 1) * (this.eclipseUntil > this.time ? this.C.randEvents.eclipse.speed : 1);
      const beh = m.boss ? 'boss' : m.def.beh;
      if (invis && !m.boss) { mx = Math.cos(m.t * 0.7 + i); my = Math.sin(m.t * 0.9 + i); sp *= 0.4; }
      else if (m.confuseUntil > this.time) { mx = Math.cos(m.t * 3 + i); my = Math.sin(m.t * 2.3 + i); sp *= 0.6; }
      else if (m.swarm && this.time < m.swarm.until) { mx = m.swarm.vx; my = m.swarm.vy; }
      else if (beh === 'erratic') {
        m.dirT -= dt;
        if (m.dirT <= 0) { m.dirT = rand(0.25, 0.7); const a = Math.atan2(dy, dx) + rand(-1.5, 1.5); m.ex = Math.cos(a); m.ey = Math.sin(a); if (Math.random() < 0.15) { m.ex = rand(-1, 1); m.ey = rand(-1, 1); } }
        mx = m.ex; my = m.ey;
      } else if (beh === 'ranged') {
        const a = m.def.atk; const rr = a.range * 0.75;
        if (d < rr * 0.7) { mx = -mx; my = -my; sp *= 0.7; } else if (d < rr) { const tmx = mx; mx = -my * 0.6; my = tmx * 0.6; sp *= 0.5; }
        m.atkT -= dt;
        if (m.atkT <= 0 && d < a.range + 60) { m.atkT = a.cd * this.atkK() * rand(0.85, 1.2); this.mobAttack(m, a); }
      } else if (beh === 'charge') {
        if (m.state === 'move') { m.atkT -= dt; if (m.atkT <= 0 && d < 300) { m.state = 'wind'; m.st = 0.55; m.cdir = [mx, my]; this.teles.push({ kind: 'line', x: m.x, y: m.y, a: Math.atan2(my, mx), len: 260, w: m.r * 1.6, t0: this.time, dur: 0.55 }); } }
        if (m.state === 'wind') { m.st -= dt; sp = 0; if (m.st <= 0) { m.state = 'dash'; m.st = 0.55; } }
        if (m.state === 'dash') { m.st -= dt; mx = m.cdir[0]; my = m.cdir[1]; sp = m.speed * 3.4; if (m.st <= 0) { m.state = 'move'; m.atkT = rand(3, 5); } }
      } else if (beh === 'flee') {
        mx = -mx; my = -my; sp *= d < 400 ? 1 : 0.3;
        if (m.t > 30) { m.dying = true; m.dieT = 0; m.silent = true; }
      } else if (beh === 'summoner') {
        m.atkT -= dt; if (d < 500 && m.atkT <= 0) { m.atkT = m.def.atk.cd * this.atkK(); for (let k = 0; k < m.def.atk.count; k++) this.spawnMob(m.def.atk.mob, m.x + rand(-30, 30), m.y + rand(-20, 20)); this.fxAt(1100, m.x, m.y); }
        if (d < 180 && !m.def.melee) { mx = -mx; my = -my; sp *= 0.6; }   // (a melee summoner, the Wo Wabbit, comes to hit you)
      } else if (beh === 'healer') {   // (0.95: a monster is healed once per run at most, by a healer or by its own heal — m.healed)
        m.atkT -= dt; if (m.atkT <= 0) { m.atkT = 4; for (const o of this.mobsInRadius(m.x, m.y, 120)) if (o.hp < o.maxHp && !o.boss && !o.healed) { o.healed = true; o.hp = Math.min(o.maxHp, o.hp + o.maxHp * 0.15); } this.rings.push({ x: m.x, y: m.y, r0: 10, r1: 120, t0: this.time, dur: 0.4, color: '#7dff9a' }); }
      } else if (beh === 'invisible') {
        m.alpha = 0.25 + 0.75 * Math.max(0, Math.sin(m.t * 1.3 + i)) ** 4;
      } else if (beh === 'roam' || beh === 'circle' || beh === 'keep') { const r = this.specialMove(m, dt); mx = r[0]; my = r[1]; }   // (0.95: keep = Jorbak)
      else if (beh === 'boss') { const r = this.updateBoss(m, dt, dx, dy, d); if (r) { mx = r[0]; my = r[1]; sp = r[2]; } }
      // 0.37: far off screen, monsters never teleport any more: they walk straight back towards you, a bit faster
      if (!m.boss && !m.ringer && !m.def.special && beh !== 'flee' && !(m.swarm && this.time < m.swarm.until) && (Math.abs(m.x - P.x) > vw * 0.7 || Math.abs(m.y - P.y) > vh * 0.75)) { mx = dx / d; my = dy / d; sp = Math.max(sp, m.speed * 1.6); }
      // separation
      let sx = 0, sy = 0;
      const near = beh === 'circle' ? [] : this.grid.query(m.x, m.y, m.r * 2.2, _q);   // (0.84: the Coffre Animé keeps its round, the crowd no longer jostles it)
      let cnt = 0;
      for (const o of near) {
        if (cnt > 6) break; if (o === m) continue;
        const ox = m.x - o.x, oy = m.y - o.y, dd = ox * ox + oy * oy, rr = (m.r + o.r) * 0.9;
        if (dd < rr * rr && dd > 0.01) { const k = (rr - Math.sqrt(dd)) / rr; sx += ox * k; sy += oy * k; cnt++; }
      }
      m.x += (mx * sp + sx * 3 + m.kx) * dt; m.y += (my * sp + sy * 3 + m.ky) * dt;
      m.wt = (m.wt || 0) + dt * clamp(Math.hypot(mx, my) * sp / Math.max(40, m.def.speed || 100), 0.35, 1.8);   // 0.27: the legs follow the real walking speed (no sliding)
      m.kx *= kdec; m.ky *= kdec;
      if (Math.abs(mx) > 0.1) m.flip = mx < 0;
      m.view = my < -0.35 ? 'L' : 'R';
      // keep inside bounds (soft)
      const b = this.bounds;
      if (m.x < b.x0 - 80) m.x = b.x0 - 80; if (m.x > b.x1 + 80) m.x = b.x1 + 80; if (m.y < b.y0 - 80) m.y = b.y0 - 80; if (m.y > b.y1 + 80) m.y = b.y1 + 80;
      // contact damage
      if (!P.dead && m.dmg > 0 && !(m.def.beh === 'flee')) {
        const rr = m.r + 12;
        if (dist2(m.x, m.y, P.x, P.y - 10) < rr * rr) {
          const last = m.lastHitP || -9;
          if (this.time - last > (m.boss ? 1.0 : 0.75) * this.atkK()) {
            m.lastHitP = this.time; this.damagePlayer(m.dmg, m);
            // monsters that push their enemies back in Dofus (Wo Wabbit, Bouftous…): about 5 cells
            if (m.def.push && !P.dead) { const dx = P.x - m.x, dy = P.y - m.y, dd = Math.hypot(dx, dy) || 1; P.push = { x: dx / dd * m.def.push, y: dy / dd * m.def.push * 0.8 }; }
          }
        }
      }
      // summons get hit (coffre)
      for (const s of taunts) if (dist2(m.x, m.y, s.x, s.y) < (m.r + 16) ** 2) { if (!m.lastHitS || this.time - m.lastHitS > 0.6) { m.lastHitS = this.time; s.hp -= m.dmg; } }
    }
  }
  mobAttack(m, a) {
    const P = this.player;
    if (a.kind === 'proj') {
      const ang = Math.atan2(P.y - 20 - (m.y - m.r), P.x - m.x);
      this.eprojs.push({ x: m.x, y: m.y - m.r, vx: Math.cos(ang) * a.speed, vy: Math.sin(ang) * a.speed, dmg: a.dmg * (m.dmul || this.scaleDmg()), life: 2.6, size: 7, color: a.color || '#fff', fx: a.fx, arrow: a.arrow, slow: a.slow, src: { proj: 1 } });
      m.atkAnimT = 0;
      if (this.time - (this._mobAtkSnd || -9) > 0.25) { this._mobAtkSnd = this.time; const k = Audio2.mobSnd(m.def.gfx, 'atk'); if (k) Audio2.play(k[0], 0.22, rand(0.9, 1.1)); }
    } else if (a.kind === 'lob') {
      const tx = P.x + rand(-30, 30), ty = P.y + rand(-20, 20);
      this.lob(m.x, m.y - m.r, tx, ty, a.aoe, a.dmg * (m.dmul || this.scaleDmg()), a.fx);
      m.atkAnimT = 0;
    }
  }
  lob(x, y, tx, ty, aoe, dmg, fx, mob) {
    const dur = Math.max(0.6, Math.hypot(tx - x, ty - y) / 280);
    this.eprojs.push({ lob: true, x, y, sx: x, sy: y, tx, ty, t: 0, dur, aoe, dmg, fx, mob, life: dur + 0.1, size: 9, color: '#ff9a3c' });
    this.teles.push({ kind: 'circle', x: tx, y: ty, r: aoe, t0: this.time, dur });
  }
  updateBoss(m, dt, dx, dy, d) {
    const P = this.player, def = m.def;
    let mx = dx / d, my = dy / d, sp = m.speed;
    if (m.state === 'wind') { m.st -= dt; if (m.st <= 0) { m.state = 'dash'; m.st = 0.6; } return [0, 0, 0]; }
    if (m.state === 'dash') { m.st -= dt; if (m.st <= 0) { m.state = 'move'; } return [m.cdir[0], m.cdir[1], m.speed * 3.6]; }
    if (m.state === 'spin') { m.st -= dt; m.spinT = (m.spinT || 0) - dt; if (m.st <= 0) m.state = 'move'; if (m.spinT <= 0 && dist2(m.x, m.y, P.x, P.y) < m.spinR * m.spinR) { m.spinT = 0.5; this.damagePlayer(m.spinDmg, m, true); } return [mx, my, sp * 0.8]; }
    if (m.state === 'leap') { m.st -= dt; const k = 1 - m.st / m.leapDur; m.x = lerp(m.lx0, m.lx1, k); m.y = lerp(m.ly0, m.ly1, k) - Math.sin(k * Math.PI) * 120; if (m.st <= 0) { m.state = 'move'; m.y = m.ly1; this.areaHitPlayer(m.x, m.y, m.leapR, m.leapDmg); this.rings.push({ x: m.x, y: m.y, r0: 20, r1: m.leapR, t0: this.time, dur: 0.4, color: '#ff8a50' }); this.shake(6); } return [0, 0, 0]; }
    if (def.abilities.some(a => a.k === 'erratic')) { m.dirT -= dt; if (m.dirT <= 0) { m.dirT = rand(0.3, 0.8); const a = Math.atan2(dy, dx) + rand(-1.2, 1.2); m.ex = Math.cos(a); m.ey = Math.sin(a); } mx = m.ex; my = m.ey; }
    const SD = this.scaleDmg(), MEL = SD * (this.RUN.meleeMul || 1), RNG = SD * (this.RUN.rangedMul || 1);   // melee / ranged blows
    for (const s of m.ab) {
      s.t -= dt; if (s.t > 0) continue;
      const a = s.a; s.t = (a.cd || 5) * this.atkK() * rand(0.9, 1.15);
      m.atkAnimT = 0;
      if (this.time - (m._snd || -9) > 1.2) { m._snd = this.time; const k = Audio2.mobSnd(def.gfx, 'atk'); if (k) Audio2.play(k[a.k === 'summon' && k.length > 1 ? 1 : 0], 0.75); }
      switch (a.k) {
        case 'charge': if (d < 520) { m.state = 'wind'; m.st = 0.7; m.cdir = [mx, my]; this.teles.push({ kind: 'line', x: m.x, y: m.y, a: Math.atan2(my, mx), len: m.speed * 3.6 * 0.6 + 40, w: m.r * 1.8, t0: this.time, dur: 0.7 }); return [0, 0, 0]; } break;
        case 'summon': {   // 0.38: at most 12 of a boss's summons alive at once, and never past the crowd cap (the Gelées Royales flooded the map: big slowdowns)
          const pool = a.pool || [a.mob], mine = this.mobs.filter(o => o.summoner === m && !o.dying).length, room = Math.min(12 - mine, (this.RUN.mobCap || 420) - this.mobs.length);   // (0.61: the crowd cap is mobCap since 0.59; spawnCap (600) let Endless reach 600 monsters)
          for (let k = 0; k < Math.min(a.count, room); k++) { const mm = this.spawnMob(pick(pool), m.x + rand(-60, 60), m.y + rand(-40, 40), { force: true, keep: true }); if (mm) mm.summoner = m; }
          if (room > 0) this.fxAt(1100, m.x, m.y, { scale: 1.5 }); } break;
        case 'heal': if (!m.healed && m.hp < m.maxHp) { m.healed = true; const h = m.maxHp * a.amount; m.hp = Math.min(m.maxHp, m.hp + h); this.text(m.x, m.y - m.r * 3, '+' + Math.round(h), '#3ddc5a', 18); this.rings.push({ x: m.x, y: m.y, r0: 20, r1: 90, t0: this.time, dur: 0.6, color: '#7dff9a' }); } break;
        case 'slam': { const tx = d < 200 ? m.x : P.x, ty = d < 200 ? m.y : P.y; this.teles.push({ kind: 'circle', x: tx, y: ty, r: a.radius, t0: this.time, dur: 0.95, cb: () => { this.areaHitPlayer(tx, ty, a.radius, a.dmg * MEL); this.rings.push({ x: tx, y: ty, r0: 20, r1: a.radius, t0: this.time, dur: 0.4, color: '#ffcf70' }); this.shake(7); Audio2.blip('boom'); } }); } break;
        case 'nova': { for (let k = 0; k < a.count; k++) { const an = k / a.count * TAU + m.t; this.eprojs.push({ x: m.x, y: m.y - m.r, vx: Math.cos(an) * 160, vy: Math.sin(an) * 160, dmg: a.dmg * RNG, life: 3.2, size: 8, color: a.color || '#fff' }); } } break;
        case 'leap': if (d < 600) { m.state = 'leap'; m.leapDur = 0.9; m.st = 0.9; m.lx0 = m.x; m.ly0 = m.y; m.lx1 = P.x; m.ly1 = P.y; m.leapR = a.radius; m.leapDmg = a.dmg * MEL; this.teles.push({ kind: 'circle', x: P.x, y: P.y, r: a.radius, t0: this.time, dur: 0.9 }); return [0, 0, 0]; } break;
        case 'slash': if (d < a.range + 60) { const an = Math.atan2(dy, dx); const x0 = m.x, y0 = m.y; this.teles.push({ kind: 'line', x: x0, y: y0, a: an, len: a.range, w: 70, t0: this.time, dur: 0.6, cb: () => { this.lineHitPlayer(x0, y0, an, a.range, 70, a.dmg * MEL); this.fxAt(805, x0 + Math.cos(an) * a.range / 2, y0 + Math.sin(an) * a.range / 2, { scale: 1.3 }); } }); } break;
        case 'blink': { const an = rand(TAU); m.x = clamp(P.x + Math.cos(an) * 220, this.bounds.x0, this.bounds.x1); m.y = clamp(P.y + Math.sin(an) * 160, this.bounds.y0, this.bounds.y1); this.rings.push({ x: m.x, y: m.y, r0: 5, r1: 60, t0: this.time, dur: 0.4, color: '#5a3a8a' }); } break;
        case 'spin': { m.state = 'spin'; m.st = 2.0; m.spinR = a.radius; m.spinDmg = a.dmg * MEL; this.rings.push({ x: m.x, y: m.y, r0: a.radius, r1: a.radius, t0: this.time, dur: 2.0, color: '#ffd24a', follow: m }); } break;
        case 'lob': { const n = a.count || 1; for (let k = 0; k < n; k++) this.lob(m.x, m.y - m.r * 2, P.x + rand(-70, 70), P.y + rand(-50, 50), a.aoe, a.dmg * RNG, 2004, a.mob); } break;
        case 'beam': { const an = Math.atan2(dy, dx); const x0 = m.x, y0 = m.y - m.r; this.teles.push({ kind: 'line', x: x0, y: y0, a: an, len: a.length, w: a.width, t0: this.time, dur: 1.0, cb: () => { this.lineHitPlayer(x0, y0, an, a.length, a.width, a.dmg * RNG); this.beams.push({ x: x0, y: y0, a: an, len: a.length, w: a.width, until: this.time + 0.4, dmg: 0, color: a.color, hostile: true, done: true }); this.shake(5); } }); return [0, 0, 0]; }
        case 'crow': this.doomCrows(m, a, dx, dy, RNG); break;   // 0.27: real corbacs with the life of the elites (bosses.js)
        case 'crow_old': { // (0.22: thrown corbacs that home in on you)
          const ramp = 1 + 0.12 * Math.max(0, this.time - (this.C.doom ? this.C.doom.t : 600));
          for (let k = 0; k < (a.count || 1); k++) { const an = Math.atan2(dy, dx) + rand(-0.6, 0.6); this.eprojs.push({ x: m.x, y: m.y - m.r * 1.6, vx: Math.cos(an) * a.speed, vy: Math.sin(an) * a.speed, sp: a.speed, homing: a.homing, dmg: a.dmg * RNG * ramp, life: 4.5, size: 11, crow: true, t0: this.time, src: m }); }
        } break;
        default: this.bossAbility(m, a, d, dx, dy, MEL, RNG); break;   // 0.27: rain, ring, fissure, roar, puddle, pull (bosses.js)
        case 'breath': { const an = Math.atan2(dy, dx); this.teles.push({ kind: 'cone', x: m.x, y: m.y, a: an, len: a.range, half: 0.5, t0: this.time, dur: 0.7, cb: () => { const pd = Math.hypot(P.x - m.x, P.y - m.y); const pa = Math.atan2(P.y - m.y, P.x - m.x); let da = Math.abs(((pa - an + Math.PI * 3) % TAU) - Math.PI); if (pd < a.range && da < 0.5) this.damagePlayer(a.dmg * RNG, m, true); this.cones.push({ x: m.x, y: m.y - m.r, a: an, range: a.range, half: 0.5, ticks: 0, next: 1e9, dt: 1, dmg: 0, hostile: true, until: this.time + 0.4, t0: this.time, color: a.color }); } }); } break;
      }
    }
    return [mx, my, sp];
  }
  areaHitPlayer(x, y, r, dmg, proj) { const P = this.player; if (dist2(x, y, P.x, P.y) < (r + 10) ** 2) this.damagePlayer(dmg, null, !proj); }
  lineHitPlayer(x, y, a, len, w, dmg) {
    const P = this.player; const dx = P.x - x, dy = P.y - 15 - y; const ca = Math.cos(a), sa = Math.sin(a);
    const along = dx * ca + dy * sa, perp = Math.abs(-dx * sa + dy * ca);
    if (along > -10 && along < len && perp < w / 2 + 10) this.damagePlayer(dmg, null, true);
  }
  updateProjectiles(dt) {
    const P = this.player;
    for (let i = this.projs.length - 1; i >= 0; i--) {
      const p = this.projs[i];
      if (p.delay > 0) { p.delay -= dt; p.x = P.x; p.y = P.y - 22; continue; }
      p.life -= dt;
      if (p.poison && (p._sm = (p._sm || 0) - dt) <= 0) { p._sm = 0.045; this.particles.push({ x: p.x + rand(-4, 4), y: p.y + rand(-4, 4), vx: rand(-14, 14), vy: rand(-26, -8), g: -6, t: 0, life: rand(0.45, 0.8), s: rand(7, 12), grow: 1.6, round: 1, c: Math.random() < 0.55 ? '#5fd43a' : '#a347d6' }); }   // 0.37: green and purple smoke behind the poisons
      if (p.lob) {
        if (!p.lobTo) { p.lobTo = { x: p.x + p.vx * 0.8, y: p.y + p.vy * 0.8 }; p.lobT = 0; p.lobDur = 0.8; p.ox = p.x; p.oy = p.y; }
        p.lobT += dt; const k = Math.min(1, p.lobT / p.lobDur);
        p.x = lerp(p.ox, p.lobTo.x, k); p.y = lerp(p.oy, p.lobTo.y, k) - Math.sin(k * Math.PI) * 90; p.rot = (p.rot || 0) + dt * 10;
        if (k >= 1) { this.explode(p, p.lobTo.x, p.lobTo.y); this.projs.splice(i, 1); }
        continue;
      }
      if (p.homing && (!p.target || p.target.dying)) p.target = this.nearestMob(p.x, p.y, 300);
      if (p.homing && p.target) {
        const a = Math.atan2(p.target.y - p.target.r - p.y, p.target.x - p.x), ca = Math.atan2(p.vy, p.vx);
        let da = ((a - ca + Math.PI * 3) % TAU) - Math.PI; const na = ca + clamp(da, -p.homing * dt, p.homing * dt);
        p.vx = Math.cos(na) * p.sp; p.vy = Math.sin(na) * p.sp;
      }
      if (p.boomerang) {
        const age = this.time - p.t0;
        if (p.curve && !p.back) { const c = Math.cos(p.curve * dt), s_ = Math.sin(p.curve * dt), vx = p.vx; p.vx = vx * c - p.vy * s_; p.vy = vx * s_ + p.vy * c; }   // Marteau de Moon: a random arc
        if (age > (p.backAt || 0.55) && !p.back) { p.back = true; p.hit.clear(); }
        if (p.back) { const a = Math.atan2(P.y - 22 - p.y, P.x - p.x); p.vx = lerp(p.vx, Math.cos(a) * p.sp * 1.2, dt * 6); p.vy = lerp(p.vy, Math.sin(a) * p.sp * 1.2, dt * 6); if (dist2(p.x, p.y, P.x, P.y - 22) < 30 * 30) { this.projs.splice(i, 1); continue; } }
      }
      p.x += p.vx * dt; p.y += p.vy * dt;
      if (p.spin) p.rot = (p.rot || 0) + dt * 14;
      if (p.trail) this.chaosTrail(p, dt);   // (0.96: the Boule de Chaos, gspells.js)
      let removed = false;
      for (const m of this.grid.query(p.x, p.y + 10, p.size + 30, _qProj)) {
        if (m.dying || p.hit.has(m)) continue;
        const rr = m.r + p.size;
        if (dist2(p.x, p.y, m.x, m.y - m.r) < rr * rr) {
          p.hit.add(m);
          if (p.aoe) { this.explode(p, p.x, p.y); removed = true; break; }
          const hp0 = m.hp;
          { const sp_ = p.spell, was = sp_._hitKind; sp_._hitKind = 'proj'; this.damageMob(m, p.dmg, sp_); sp_._hitKind = was; this.hitSfx('proj'); } if (p.spell.def.weapon) this.onWeaponHit(p.spell, m, p.dmg);   // (0.84: its own impact sound, hitSfx)
          // 0.22: a little push (half a cell) + the spell's own (knock x3, else 40); 0.92: a spell with `push` sets its whole push
          // itself (the Crâ's arrows, patch_091: 25 % less)
          if (!m.boss && p.push !== undefined) { const v = Math.hypot(p.vx, p.vy) || 1; m.kx += p.vx / v * p.push; m.ky += p.vy / v * p.push; }
          else if (!m.boss) { const v = Math.hypot(p.vx, p.vy) || 1, kb = this.RUN.projKnock || 0; m.kx += p.vx / v * kb; m.ky += p.vy / v * kb; }
          if (p.slow) { m.slowUntil = this.time + (p.slowDur || 1.5); m.slowAmt = p.slow; }
          if (p.burn) { m.burnUntil = this.time + 2.5; m.burnDps = p.burn * this.stats.might; }
          if (p.poison) this.poisonPuff(m, p.poison, p.poisonDur, p.spell);   // (0.98: a little poison zone at the impact)
          if (p.leech) { this.player.leechHeal(Math.max(0, hp0 - Math.max(0, m.hp)) * p.leech * (1 + this.stats.healBonus)); this.drainFx(m); }
          if (!m.boss && p.push === undefined) { const k = p.knock || 40; m.kx += p.vx / p.sp * k * (p.knock ? 3 : 1); m.ky += p.vy / p.sp * k * (p.knock ? 3 : 1); }
          if (p.bounce > 0) {
            p.bounce--; const n = this.nearestOther(m, p.hit, 220);
            if (n) { const a = Math.atan2(n.y - n.r - p.y, n.x - p.x); p.vx = Math.cos(a) * p.sp; p.vy = Math.sin(a) * p.sp; p.life = Math.max(p.life, 0.8); continue; }
          }
          p.pierce--;
          if (p.pierce <= 0) { removed = true; this.hitFx(p, m.x, m.y - m.r); break; }
        }
      }
      if (removed || p.life <= 0) { if (!removed && p.aoe) this.explode(p, p.x, p.y); this.projs.splice(i, 1); }
    }
    // enemy projectiles
    for (let i = this.eprojs.length - 1; i >= 0; i--) {
      const e = this.eprojs[i];
      e.life -= dt;
      if (this.time < this.freezeUntil) { if (e.life < 0) this.eprojs.splice(i, 1); continue; }
      if (e.lob) {
        e.t += dt; const k = Math.min(1, e.t / e.dur);
        e.x = lerp(e.sx, e.tx, k); e.y = lerp(e.sy, e.ty, k) - Math.sin(k * Math.PI) * 110;
        if (k >= 1) {
          if (!(dist2(P.x, P.y, e.tx, e.ty) < e.aoe * e.aoe && this.blockSpell())) this.areaHitPlayer(e.tx, e.ty, e.aoe, e.dmg, true);   // (a thrown projectile: misses an invisible Sram)   // (0.53: Sagesse may block a thrown spell)
          if (e.fx) this.fxAt(e.fx, e.tx, e.ty);
          this.rings.push({ x: e.tx, y: e.ty, r0: 8, r1: e.aoe, t0: this.time, dur: 0.3, color: '#ffae5a' });
          if (e.mob) this.spawnMob(e.mob, e.tx, e.ty, { force: true });
          this.eprojs.splice(i, 1);
        }
        continue;
      }
      if (e.homing) { const ta = Math.atan2(P.y - 22 - e.y, P.x - e.x), ca = Math.atan2(e.vy, e.vx); const da = ((ta - ca + Math.PI * 3) % TAU) - Math.PI; const na = ca + clamp(da, -e.homing * dt, e.homing * dt); e.vx = Math.cos(na) * e.sp; e.vy = Math.sin(na) * e.sp; }
      e.x += e.vx * dt; e.y += e.vy * dt;
      if (dist2(e.x, e.y, P.x, P.y - 22) < (e.size + 12) ** 2) {
        if (!e.arrow && !e.crow && this.blockSpell()) { this.eprojs.splice(i, 1); continue; }   // (0.53: Sagesse blocks the spells, not the arrows nor the corbacs)
        this.damagePlayer(e.dmg, e.src || null);
        if (e.slow) { /* chill: brief speed loss */ }
        this.eprojs.splice(i, 1); continue;
      }
      if (e.life <= 0) this.eprojs.splice(i, 1);
    }
  }
  nearestOther(m0, set, r) { let best = null, bd = r * r; for (const m of this.grid.query(m0.x, m0.y, r, _q)) { if (m === m0 || m.dying || set.has(m)) continue; const d = dist2(m0.x, m0.y, m.x, m.y); if (d < bd) { bd = d; best = m; } } return best; }
  hitFx(p, x, y) {
    const sh = FxSheets.get(p.spell.def.fx[0]);
    if (sh && sh.anims.shoot && !p.arrow) this.fxAt(p.spell.def.fx[0], x, y, { sym: 'shoot', scale: 0.6 });
    for (let i = 0; i < 3; i++) this.particles.push({ x, y, vx: rand(-60, 60), vy: rand(-60, 20), t: 0, life: 0.25, c: '#fff', s: 2 });
  }
  explode(p, x, y) {
    const r = p.aoe || 50;
    for (const m of this.mobsInRadius(x, y + 10, r)) {
      this.damageMob(m, p.dmg, p.spell);
      if (p.slow) { m.slowUntil = this.time + (p.slowDur || 1.5); m.slowAmt = p.slow; }
    }
    const id = p.spell.def.fx[0]; const sh = FxSheets.get(id);
    const sym = sh ? (sh.anims.shoot ? 'shoot' : sh.anims.root ? 'root' : null) : null;
    if (sym) this.fxAt(id, x, y, { sym, scale: r / 60, fit: r, tint: p.tint });
    if (p.chaos) this.chaosBurst(x, y, r);   // (0.96: the Boule de Chaos's own burst, gspells.js)
    else this.rings.push({ x, y, r0: r * 0.5, r1: r, t0: this.time, dur: 0.45, color: p.puddlePoison ? p.puddleColor : '#ffa033', fill: 1 });
    if (p.puddle) this.zones.push({ x, y, r: r * 0.8, until: this.time + (p.puddleDur ? p.puddleDur * this.stats.duration : 2.5), tick: 0.4, next: 0, dmg: p.dmg * 0.08, color: p.puddleColor || '#ff8a2a', spell: p.spell, born: this.time, slow: p.puddleColor ? (p.slow || 0.3) : 0, poison: p.puddlePoison });   // (0.91: puddlePoison / puddleDur, the Otomaï's Fiole Corrosive)
    Audio2.blip('boom');
  }
  updateAttacks(dt) {
    const T_ = this.time;
    // zones
    for (let i = this.zones.length - 1; i >= 0; i--) {
      const z = this.zones[i];
      if (z.follow) { z.x = z.follow.x; z.y = z.follow.y; }
      if (z.heal && (z.healT = (z.healT || 0) - dt) <= 0) { z.healT = 1; this.zoneHeal(z); }   // (0.95: the Pwout + Cawotte fusion's cloud, gspells.js)
      if (z.dose) { if (T_ >= z.next) { z.next = T_ + z.tick; for (const m of this.mobsInRadius(z.x, z.y, z.r)) if (!m.dying && !z.dosed.has(m)) { z.dosed.add(m); this.poisonMob(m, z.dose.dps, z.dose.dur, z.spell); } } if (T_ > z.until) this.zones.splice(i, 1); continue; }
      if (T_ >= z.next) { z.next = T_ + z.tick; for (const m of this.mobsInRadius(z.x, z.y, z.r)) { if (z.grp && !this.grpHit(z.grp, m)) continue; this.damageMob(m, z.dmg, z.spell, true); if (z.poison && !m.dying) this.poisonMob(m, z.poison, 2 * this.stats.duration, z.spell); if (z.slow) { m.slowUntil = T_ + 0.5; m.slowAmt = z.slow; } if (z.stun) m.stunUntil = Math.max(m.stunUntil, T_ + z.stun * (m.boss ? 0.2 : 1)); if (z.burn) { m.burnUntil = T_ + 2; m.burnDps = Math.max(m.burnDps || 0, z.dmg * 0.6 * this.stats.might); } } }   // (0.89: the fire armour sets them burning — at the tick: it was looked for in the 50 ms after it, missed at low frame rates)
      if (T_ > z.until) {
        if (z.push) {   // 0.89: Trêve / Rempart: the dome pushes everything out when it fades
          for (const m of this.mobsInRadius(z.x, z.y, z.r * 1.15)) { if (m.boss) continue; const dx = m.x - z.x, dy = m.y - z.y, d = Math.hypot(dx, dy) || 1; m.kx += dx / d * z.push * 4; m.ky += dy / d * z.push * 4; }
          this.rings.push({ x: z.x, y: z.y, r0: z.r * 0.4, r1: z.r * 1.3, t0: T_, dur: 0.5, color: z.color, fill: 1 }); this.shake(3);
        }
        this.zones.splice(i, 1);
      }
    }
    // strikes
    for (let i = this.strikes.length - 1; i >= 0; i--) {
      const s = this.strikes[i];
      if (s.tgt && !s.tgt.dying) { s.x = s.tgt.x; s.y = s.tgt.y; }   // (0.98: a single blow follows its monster)
      if (T_ >= s.at) {
        let dmg = s.dmg;
        if (s.gamble) dmg *= Math.random() < 0.3 ? 0 : rand(0.8, 1.8);
        for (const m of s.tgt ? (s.tgt.dying ? [] : [s.tgt]) : this.mobsInRadius(s.x, s.y, s.r)) {
          this.damageMob(m, dmg * (m.boss && s.bossK ? s.bossK : 1), s.spell);   // (0.98: s.bossK, more on a boss)
          if (s.slow) { m.slowUntil = T_ + (s.slowDur || 2); m.slowAmt = s.slow; }
          if (s.mark) { m.markUntil = T_ + (s.markDur || 4); m.markAmt = s.mark; }
          if (s.stun) m.stunUntil = Math.max(m.stunUntil, T_ + s.stun * (m.boss ? 0.2 : 1));   // (0.60: Éboulement du Craqueleur)
          if (s.transmute) this.transmute(m, s);   // (0.91: the Otomaï, game.js below)
        }
        if (!s.nofx) this.fxAt(s.fx || s.spell.def.fx[0], s.x, s.y, { scale: s.r / 45, fit: s.r });
        if (s.crack) for (let k = 0; k < 10; k++) { const a = rand(TAU), v = rand(80, 220); this.particles.push({ x: s.x + rand(-8, 8), y: s.y, vx: Math.cos(a) * v, vy: -rand(120, 300), g: 900, t: 0, life: rand(0.45, 0.8), s: rand(3, 6.5), c: pick(['#8a6a4a', '#a8865c', '#6b5038', '#c9a27a']) }); }   // (Crackler strike: earth chunks)
        // the real reach of the blow, always shown on the ground (the spell animation alone can be smaller or larger)
        this.rings.push({ x: s.x, y: s.y, r0: s.r * 0.55, r1: s.r, t0: T_, dur: s.spell && s.spell.def && s.spell.def.weapon ? 0.9 : 0.5, color: (s.spell && s.spell.p && s.spell.p.color) || (s.nofx ? '#ffaa33' : '#ffcc33'), fill: 1 });
        if (s.nofx) Audio2.play('impact_lourd', 0.5, rand(0.9, 1.1));
        if (s.shake) this.shake(s.shake);
        this.strikes.splice(i, 1);
      }
    }
    // slashes
    for (let i = this.slashes.length - 1; i >= 0; i--) {
      const s = this.slashes[i];
      if (!s.done && T_ >= s.at) {
        s.done = true;
        const ca = Math.cos(s.a), sa = Math.sin(s.a);
        for (const m of this.grid.query(s.x + ca * s.range / 2, s.y + sa * s.range / 2, s.range, _qSlash)) {
          if (m.dying) continue;
          const dx = m.x - s.x, dy = m.y - m.r - s.y;
          const along = dx * ca + dy * sa, perp = Math.abs(-dx * sa + dy * ca);
          let hit = along > -m.r && along < s.range + m.r && perp < s.width / 2 + m.r;
          if (!hit && s.cross) { const cx = s.x + ca * s.range * 0.75, cy = s.y + sa * s.range * 0.75; const a2 = dx - (cx - s.x), b2 = dy - (cy - s.y); hit = Math.abs(-a2 * sa + b2 * ca) < s.range * 0.35 && Math.abs(a2 * ca + b2 * sa) < s.width / 2 + m.r; }
          if (hit) {
            this.damageMob(m, s.dmg, s.spell); if (s.spell.def.weapon) this.onWeaponHit(s.spell, m, s.dmg);
            if (s.stun) m.stunUntil = Math.max(m.stunUntil, T_ + s.stun * (m.boss ? 0.2 : 1));
            if (s.leech) { this.player.leechHeal(s.dmg * s.leech * 0.25); this.drainFx(m); }
            if (!m.boss) { const kb = s.knock ? s.knock * 3 : 60; m.kx += ca * kb; m.ky += sa * kb; }   // (0.46: the weapons' little default push is back; their big knock-backs stay gone)
            if (s.bleed) { m.bleedUntil = T_ + 2.5; m.burnUntil = T_ + 2.5; m.burnDps = Math.max(m.burnDps || 0, s.dmg * 0.12 * s.bleed); }
            if (s.burn) { m.burnUntil = T_ + 2.5; m.burnDps = Math.max(m.burnDps || 0, s.burn * this.stats.might); }
            if (s.poison) this.poisonMob(m, s.poison, s.poisonDur, s.spell);
          }
        }
        const fx = s.spell.def.fx[0];
        const wh = s.spell.def.whip;   // (0.54: the Fouet's lash drawn from its handle, in the hand, toward the target)
        if (wh && FxSheets.get(fx)) this.fxAt(fx, s.x, s.y - 12, { rot: s.a, scale: s.range / wh[2], flip: ca < 0, off: wh, sy: 1.5 });
        else if (FxSheets.get(fx)) this.fxAt(fx, s.x + ca * s.range * 0.55, s.y + sa * s.range * 0.55, { rot: s.a, scale: s.range / 120, flip: ca < 0, fit: Math.max(s.range * 0.55, s.width * 0.6) });
      }
      if (T_ > s.t0 + (s.spell.def.weapon ? 0.6 : 0.3)) this.slashes.splice(i, 1);   // (0.34: a weapon's hit zone stays longer)
    }
    // beams
    for (let i = this.beams.length - 1; i >= 0; i--) {
      const b = this.beams[i];
      if (!b.done) {
        b.done = true; const ca = Math.cos(b.a), sa = Math.sin(b.a);
        for (const m of this.mobs) {
          if (m.dying) continue; const dx = m.x - b.x, dy = m.y - m.r - b.y; const along = dx * ca + dy * sa, perp = Math.abs(-dx * sa + dy * ca);
          if (along > 0 && along < b.len && perp < b.w / 2 + m.r) { this.damageMob(m, b.dmg, b.spell); if (b.burn) { m.burnUntil = this.time + 2.5; m.burnDps = Math.max(m.burnDps || 0, b.burn * this.stats.might); } if (b.knock && !m.boss) { m.kx += ca * b.knock * 4; m.ky += sa * b.knock * 4; } }
        }
      }
      if (T_ > b.until) this.beams.splice(i, 1);
    }
    // cones
    for (let i = this.cones.length - 1; i >= 0; i--) {
      const c = this.cones[i];
      if (!c.hostile && c.ticks > 0 && T_ >= c.next) {
        c.ticks--; c.next = T_ + c.dt;
        for (const m of this.mobsInRadius(c.x, c.y, c.range)) {
          const a = Math.atan2(m.y - m.r - c.y, m.x - c.x); const da = Math.abs(((a - c.a + Math.PI * 3) % TAU) - Math.PI);
          if (da < c.half + 0.1) {
            this.damageMob(m, c.dmg, c.spell, true); if (c.confuse && !m.boss) m.confuseUntil = T_ + c.confuse;
            if (c.knock && !m.boss) { const dx = m.x - c.x, dy = m.y - c.y, d = Math.hypot(dx, dy) || 1; m.kx += dx / d * c.knock * 4; m.ky += dy / d * c.knock * 4; }
          }
        }
      }
      if (T_ > c.until) this.cones.splice(i, 1);
    }
    // orbiters
    const P = this.player;
    for (let i = this.orbiters.length - 1; i >= 0; i--) {
      const o = this.orbiters[i]; const sp = o.spell.p;
      if (T_ > o.until) { this.orbiters.splice(i, 1); continue; }
      o.a += sp.rotSpeed * dt;
      const r = sp.radius * this.stats.area;
      const th = ellAngle(o.a); o.x = P.x + Math.cos(th) * r; o.y = P.y - 20 + Math.sin(th) * r * 0.6;
      for (const m of this.grid.query(o.x, o.y + 10, sp.size + 30, _qOrb)) {
        if (m.dying) continue;
        if (dist2(o.x, o.y, m.x, m.y - m.r) < (sp.size + m.r) ** 2) {
          const last = o.hit.get(m) || -9; if (T_ - last < 0.5) continue; o.hit.set(m, T_);
          const was = o.spell._hitKind; o.spell._hitKind = 'spin'; this.damageMob(m, o.spell.dmg() * (o.k || 1), o.spell); o.spell._hitKind = was; this.hitSfx('spin');
          const dx = m.x - P.x, dy = m.y - P.y, d = Math.hypot(dx, dy) || 1;
          if (!m.boss && sp.knock) { m.kx += dx / d * sp.knock * 3; m.ky += dy / d * sp.knock * 3; }
        }
      }
    }
    // traps
    for (let i = this.traps.length - 1; i >= 0; i--) {
      const t = this.traps[i];
      if (t.dead || T_ > t.until) { this.traps.splice(i, 1); continue; }
      if (T_ < t.armed) continue;
      const hit = this.mobsInRadius(t.x, t.y, t.r).filter(m => { const dx = m.x - t.x, dy = (m.y - t.y) / 0.62, rr = t.r + m.r; return dx * dx + dy * dy <= rr * rr; });   // (0.98: the drawn ellipse triggers and hits; was 0.6 of the radius as a circle)
      const tg = t.spell.p.trig, on = tg ? hit.some(m => { const dx = m.x - t.x, dy = (m.y - t.y) / 0.62, rr = tg + m.r * 0.5; return dx * dx + dy * dy <= rr * rr; }) : hit.length;   // (0.98: p.trig, a trap that goes off only when a monster steps on its cone, render.js drawTrapCone's base)
      if (on) {
        for (const mm of hit) this.damageMob(mm, t.dmg, t.spell);
        if (t.gas) { const D = t.spell.p.gasPoison || 4; this.poisonCloud(t.x, t.y, t.r, t.gas / D / Math.max(0.01, this.stats.might * this.dmgMul()), D, t.spell.p.gasDur || 0.5, t.spell); }   // (0.98: the Piège Empoisonné's gas: t.gas went through dmg())
        this.rings.push({ x: t.x, y: t.y, r0: t.r * 0.5, r1: t.r, t0: T_, dur: 0.45, color: '#b388ff', fill: 1 });
        this.fxAt(412, t.x, t.y, { scale: 0.6 });
        Audio2.blip('boom');
        this.traps.splice(i, 1);
      }
    }
  }
  updateSummons(dt) {
    const T_ = this.time;
    for (let i = this.summons.length - 1; i >= 0; i--) {
      const s = this.summons[i]; s.t += dt; if (s.atkT !== undefined) s.atkT += dt;   // (0.59: the attack animation's clock, was advanced in drawSummon)
      if (T_ > s.until || s.hp <= 0) {
        this.sndOf(s.snd, 'die', 0.4);
        if (s.kamas) for (let k = 0; k < s.kamas; k++) this.dropPickup('kama', s.x + rand(-30, 30), s.y + rand(-20, 20), 1);
        if (s.decoy) { // the Double explodes
          for (const m of this.mobsInRadius(s.x, s.y, s.radius * this.stats.area)) this.damageMob(m, s.dmg * this.dmgMul(), s.spell);
          this.rings.push({ x: s.x, y: s.y, r0: 8, r1: s.radius * this.stats.area, t0: T_, dur: 0.35, color: '#b388ff' }); this.fxAt(412, s.x, s.y, { scale: 0.7 }); Audio2.blip('boom');
        }
        if (s.spell.p.boom) { // 0.98: the Boufcouls burst once, dead or gone: p.boom of their blows, p.boomR x their melee reach (16 + the monster's size)
          const r = s.spell.p.boomR * 16 * this.stats.area, d = this.summonBlow(s) * s.spell.p.boom;
          for (const m of this.mobsInRadius(s.x, s.y, r)) this.damageMob(m, d, s.spell, true);
          this.rings.push({ x: s.x, y: s.y, r0: 6, r1: r, t0: T_, dur: 0.3, color: '#c9a27a', fill: 1 }); this.fxAt(2004, s.x, s.y, { fit: r }); Audio2.play('explosion', 0.3, rand(1.05, 1.25));
        }
        this.particles.push({ x: s.x, y: s.y - 10, vx: 0, vy: -30, t: 0, life: 0.5, c: '#fff', s: 6 });
        this.summons.splice(i, 1); continue;
      }
      if (s.taunt) continue;
      if (s.healer) { // Lapino: follows the player and heals him regularly
        const a = i * 2.399 + T_ * 0.6, tx = this.player.x + Math.cos(a) * 46, ty = this.player.y + Math.sin(a) * 28, dx = tx - s.x, dy = ty - s.y, d = Math.hypot(dx, dy) || 1;
        if (d > 6) { s.x += dx / d * Math.min(d * 4, s.speed) * dt; s.y += dy / d * Math.min(d * 4, s.speed) * dt; s.flip = dx < 0; }
        s.hitT -= dt;
        if (s.hitT <= 0) { s.hitT = s.spell.p.healTick || 2; s.atkT = 0; const P = this.player; this.sndOf(s.snd, 'atk', 0.35); if (P.hp < this.stats.maxHp) { P.heal(s.spell.p.heal * (1 + this.stats.healBonus) * (s.spell.shopK || 1)); this.rings.push({ x: P.x, y: P.y, r0: 6, r1: 40, t0: T_, dur: 0.4, color: '#7dff9a' }); } }
        continue;
      }
      if (!s.target || s.target.dying || T_ - (s.retarget || 0) > 0.8) { const see = 420 * this.stats.projspeed; s.target = this.nearestMob(s.x, s.y, see) || this.nearestMob(this.player.x, this.player.y, see); s.retarget = T_; }
      let tx = this.player.x + Math.cos(T_ + i) * 60, ty = this.player.y + Math.sin(T_ + i) * 40;
      if (s.target) { tx = s.target.x; ty = s.target.y; }
      if (!s.target) { const a = (i * 2.399) + T_ * 0.4; tx = this.player.x + Math.cos(a) * 70; ty = this.player.y + Math.sin(a) * 45; }
      else if (s.ranged) { const rr = Math.min(s.spell.p.range * 0.6, 150), a = i * 2.399 + Math.atan2(s.y - s.target.y, s.x - s.target.x) * 0.5; tx += Math.cos(a) * rr; ty += Math.sin(a) * rr * 0.7; }
      else { const a = i * 2.399; tx += Math.cos(a) * (s.target.r + 14); ty += Math.sin(a) * (s.target.r + 8); } // each summon takes its own side
      const dx = tx - s.x, dy = ty - s.y, d = Math.hypot(dx, dy) || 1;
      let px = 0, py = 0;
      for (const o of this.summons) { if (o === s) continue; const ox = s.x - o.x, oy = s.y - o.y, dd = ox * ox + oy * oy; if (dd < 34 * 34 && dd > 0.01) { const k = (34 - Math.sqrt(dd)) / 34; px += ox * k; py += oy * k; } }
      for (const o of this.allies) { const ox = s.x - o.x, oy = s.y - o.y, dd = ox * ox + oy * oy; if (dd < 40 * 40 && dd > 0.01) { const k = (40 - Math.sqrt(dd)) / 40; px += ox * k; py += oy * k; } }
      s.x += px * 4 * dt; s.y += py * 4 * dt;
      if (d > 8) { s.x += dx / d * s.speed * dt; s.y += dy / d * s.speed * dt; s.flip = dx < 0; }
      s.hitT -= dt;
      if (s.ranged && s.target && s.hitT <= 0 && dist2(s.x, s.y, s.target.x, s.target.y) < (s.spell.p.range * this.stats.projspeed) ** 2) { // Dragonnet: fireballs
        s.hitT = s.spell.p.hitcd || 1; s.atkT = 0; s.flip = s.target.x < s.x; this.sndOf(s.snd, 'atk', 0.35, rand(0.95, 1.1));
        const a = Math.atan2(s.target.y - s.target.r - s.y + 20, s.target.x - s.x), sp = s.spell.p.projSpeed || 300;
        this.projs.push({ x: s.x, y: s.y - 20, vx: Math.cos(a) * sp, vy: Math.sin(a) * sp, sp, dmg: s.dmg * this.dmgMul(), pierce: 1, life: 1.4, size: 9, spell: s.spell, hit: new Set(), target: s.target, homing: 3,
          bounce: 0, aoe: 0, t0: T_, delay: 0, back: false, burn: 3, col: '#ff6a1e', fireball: 1 });
        continue;
      }
      if (s.target && d < s.target.r + 16 && s.hitT <= 0 && !s.ranged) {
        if (s.kamikaze) {
          for (const m of this.mobsInRadius(s.x, s.y, s.radius * this.stats.area)) this.damageMob(m, s.dmg * this.dmgMul(), s.spell);
          this.rings.push({ x: s.x, y: s.y, r0: 6, r1: s.radius, t0: T_, dur: 0.3, color: '#ffe066' });
          const bsh = MobSheets.c[this.C.bombSprite];
          if (bsh && bsh.has('dieR')) this.effects.push({ sh: bsh, sym: 'dieR', x: s.x, y: s.y + 6, t: 0, dur: Math.min(1.2, bsh.duration('dieR')), scale: ES * s.radius / 78, rot: 0 });
          Audio2.play('explosion', 0.35, rand(0.95, 1.2)); this.shake(2);
          this.summons.splice(i, 1); continue;
        }
        s.hitT = (s.spell.p.hitcd || 0.5) * s.cad; s.atkT = 0;
        // (0.68: the damage is read at every blow — the levels and buffs gained since the summoning count —, and a summon
        // with an area hits every monster around its target)
        const sd = this.summonBlow(s);
        if (s.aoe) {
          const r = s.aoe * this.stats.area;
          for (const m of this.mobsInRadius(s.target.x, s.target.y, r)) this.damageMob(m, sd, s.spell, true);
          this.rings.push({ x: s.target.x, y: s.target.y, r0: r * 0.4, r1: r, t0: T_, dur: 0.25, color: '#c9a27a' });
        } else this.damageMob(s.target, sd, s.spell, true);
        if (Math.random() < 0.55) this.sndOf(s.snd, 'atk', 0.32, rand(0.95, 1.12));
      }
    }
  }
  updatePickups(dt) {
    const P = this.player, st = this.stats;
    if (P.dead) return;   // (0.96: nothing picked up during the 2.2 s of the fall: a chest under the body opened its window and held the end screen)
    const mr = 80 * st.magnet, ir = 62;   // gems and kamas are pulled by the magnet; objects keep the same (wider since v1.7) pickup range all run
    for (let i = this.pickups.length - 1; i >= 0; i--) {
      const p = this.pickups[i]; p.t += dt;
      const d2 = dist2(p.x, p.y, P.x, P.y - 15);
      if (!p.mag && p.kind !== 'chest' && d2 < ((p.kind === 'gem' || p.kind === 'kama') ? mr * mr : ir * ir)) { p.mag = true; p.mt = 0; }
      if (p.kind === 'chest' && d2 < 46 * 46 && !p.cine) {   // 0.26: a boss chest has its little show first (events.js)
        if (p.boss) { p.cine = true; this.startCine('chest', { p }, () => { const k = this.pickups.indexOf(p); if (k >= 0) this.pickups.splice(k, 1); Game.openChest(p.v || 1); }); continue; }
        this.pickups.splice(i, 1); Game.openChest(p.v || 1); continue;
      }
      if (p.mag) {
        // speed grows with the time since the pull started (not the item's age: old gems/bread used to overshoot and jitter)
        p.mt = (p.mt || 0) + dt;
        const d = Math.sqrt(d2) || 1, step = (260 + p.mt * 520) * dt;
        if (d < 16 || step >= d) { this.collect(p); this.pickups.splice(i, 1); continue; }
        p.x += (P.x - p.x) / d * step; p.y += (P.y - 15 - p.y) / d * step;
      }
    }
  }
  collect(p) {
    const P = this.player;
    if (p.doomRw) Prog.add('doomRewards');   // (0.92: a Maîtres Corbacs' reward picked up, an achievement)
    switch (p.kind) {
      case 'gem': {
        this.addXP(p.v); this.amberSound(); this.bump('xp'); if (this.ps) this.ps.gems++;
        const GF = this.C.gemFx; if (GF && this.effects.length < 70 && this.time - (this._gemFx || -9) > 0.06) { this._gemFx = this.time; this.fxAt(GF.id, P.x + rand(-6, 6), P.y - 30, { scale: GF.scale, follow: null }); }
      } break;
      case 'kama': { const v = this.addKamas(p.v || 1); Audio2.blip('coin'); this.bump('kamas'); if (v > 3) this.text(P.x, P.y - 70, '+' + v + ' K', '#ffd700', 13); } break;
      case 'bread': {
        const E = this.C.eat, B = (this.C.breads || {})[p.v]; P.heal(B ? (B.hp < 0 ? st0(this).maxHp : B.hp) : E.flat + st0(this).maxHp * E.heal); P.eat(); Audio2.play(E.snd || 'pain', 0.8);
        for (let i = 0; i < 12; i++) this.particles.push({ x: P.x + rand(-10, 10), y: P.y - 40 + rand(-6, 6), vx: rand(-50, 50), vy: rand(-90, -20), t: 0, life: rand(0.4, 0.8), c: pick(['#e8b864', '#c88a3a', '#f6d79a']), s: rand(2, 3.5) });
        if (this.ps) this.ps.breads++;
      } break;
      case 'kamaboost': {
        const KB = this.C.kamaBoost; this.kboostUntil = this.time + KB.dur;
        this.banner(T('kamaboost'), '#ffd700'); this.chat(T('kamaboost'), '#ffd700'); Audio2.play(KB.snd, 0.9); Audio2.sfx('EVENT', 0.5);
        this.fxAt(KB.fx, P.x, P.y, { follow: P, scale: 1.0 }); this.shake(3);
        for (let i = 0; i < 40; i++) this.particles.push({ x: P.x + rand(-30, 30), y: P.y - rand(0, 60), vx: rand(-120, 120), vy: rand(-260, -80), t: 0, life: rand(0.6, 1.2), c: pick(['#ffd700', '#fff3a0', '#e6b422']), s: rand(2.5, 5) });
        Prog.add('kamaBoosts');
      } break;
      case 'rappel': for (const q of this.pickups) if (q.kind === 'gem' || q.kind === 'kama') q.mag = true; this.chat(T('recall'), '#9fe0ff'); Audio2.ui('item', 0.7); break;
      case 'fee': this.fireworks(); break;
      case 'gold': { const v = this.C.goldKamas || 25; this.kamas += v; this.text(P.x, P.y - 80, '+' + v + ' K', '#ffd700', 18); this.chat(T('gold_found', { n: v }), '#ffd700'); Audio2.blip('coin'); Audio2.ui('item', 0.6); if (this.ps) this.ps.gold = (this.ps.gold || 0) + 1; } break;
      case 'batofu': { const D = this.C.batofu; this.batofuUntil = this.time + D.dur; this.batofuDur = D.dur; this.banner(T('batofu'), '#9fe0ff'); this.chat(T('batofu'), '#9fe0ff'); Audio2.ui('item', 0.8); P.dodgeReady = Math.min(P.dodgeReady, this.time); } break;
      case 'relic': this.gainRelic(p.v); break;
      case 'tmap': this.gotTmap(); break;
      case 'nowelgift': this.nowelGift(); break;   // (0.68: nowel.js)
      case 'trool': this.troolTicket(); break;
      case 'booster': this.openBooster(p.pk || 0); break;
      case 'plumec': { Store.data.plumes = (Store.data.plumes || 0) + 1; Store.save(); this.chat(T('plumec', { n: Store.data.plumes }), '#c9a0ff'); Audio2.ui('item', 0.8); Prog.check(this); } break;
      case 'manuel': {
        const prize = this.tailorPrize();
        this.chat(prize.kind === 'kamas' ? T('tailor_kamas', { n: prize.v }) : T('tailor_got', { n: L(prize.item.name) }), '#ff9cf0');
        Audio2.ui('item', 0.8); if (typeof Game !== 'undefined' && Game.tailorWin) Game.tailorWin(prize);
      } break;
      case 'houx': this.rerolls++; this.chat(T('houx_got', { n: this.rerolls }), '#7fe08a'); this.banner(L(this.C.houx.name), '#7fe08a'); Audio2.ui('item', 0.8); break;   // 0.97: one more reroll, added to the run's (UI.levelUpMenu)
      case 'sablier': this.freezeUntil = this.time + 8; this.chat(T('sandglass'), '#9fe0ff'); this.banner(T('time_stops'), '#9fe0ff'); Audio2.spell(this.C.spells.sablier_xelor, 0.8); break;
      case 'power': this.activatePower(p.v); break;
      case 'dofus': {   // 0.26: the 'item get' show first, then the Dofus (events.js)
        const dof = this.C.dofus.find(d => d.id === p.v); if (!dof || this.dofus.includes(dof)) break;
        this.startCine('dofus', { dof }, () => {
        this.dofus.push(dof); this.recompute(); this.player.heal(this.stats.maxHp);
        Store.data.dofus[dof.id] = (Store.data.dofus[dof.id] || 0) + 1;
        this.banner(T('dofus_found', { n: L(dof.name) }), dof.color); this.chat(T('dofus_found', { n: L(dof.name) }) + ' ' + L(dof.desc), dof.color);
        this.kamas += 500; this.text(P.x, P.y - 90, '+500 K', '#ffd700', 20); this.chat(T('dofus_kamas'), '#ffd700');
        Audio2.sfx('EVENT', 0.9); Audio2.blip('level');
        });
      } break;
    }
  }
  // ------------------------------------------------ rare power-ups (original spells) and the Arakne ally
  activatePower(id) {
    const d = this.C.drops[id]; if (!d) return;
    const P = this.player, t = this.time;
    this.banner(T('pw_' + id), d.color); this.chat(T('pw_' + id), d.color);
    Audio2.sfx('EVENT', 0.6);
    if (id === 'foudre') this.powers.foudre = { until: t + d.dur, next: t + 0.3 };
    else if (id === 'flamiche') this.powers.flamiche = { until: t + d.dur, next: t };
    else if (id === 'liberation') { this.powers.liberation = { until: t + d.dur, charges: d.charges }; this.fxAt(d.fx, P.x, P.y, { follow: P, scale: 0.6 }); }
    else if (id === 'arakne' || id === 'chaferfu') {
      let kind = id, crit = false;
      // critical summon (a fixed 1 in 30, never boosted): the Chaferfu Lancier, or the Arakne Majeure
      if (Math.random() < (d.crit || 1 / 30)) {
        kind = id === 'chaferfu' ? 'lancier' : 'majeure'; const cc = id === 'chaferfu' ? '#ffcf3a' : '#c47bff';
        this.banner(T('pw_' + kind), cc); this.chat(T('pw_' + kind), cc); this.shake(6); Audio2.ui('level', 0.8); Audio2.play('stars', 0.6); Prog.add(kind); crit = true;   // (0.61: 'crit' is no UI sound)   // (the 'lancier' achievement counts it)
      }
      const cfg = this.allyCfg(kind), al = this.C.allies[kind];
      this.allies = this.allies.filter(a => a.kind !== kind);
      const A = { kind, x: P.x + 40, y: P.y + 10, until: t + cfg.dur, t: 0, hitT: 0, target: null, flip: false, sh: MobSheets.c[al.sprite] || null, born: t, view: 'R', wx: P.x, wy: P.y, wT: 0 };
      if (!A.sh) MobSheets.load(al.sprite).then(sh => { A.sh = sh; });
      this.allies.push(A);
      this.fxAt(1100, P.x + 40, P.y + 10, { scale: 1.4 });
      this.allySnd(kind, 'spawn', 0.6);
      if (crit && this.critSeq) { A.born = t - 1; this.critSeq(A); }   // (0.98: its show: slow motion, confetti, the camera on it, juice.js; seen at once — its fade-in, run time, lasted 33 s at 1 %)
    }
  }
  powerDmg(base) { return base * (1 + 0.05 * this.level) * this.stats.might; }
  updatePowers(dt) {
    const t = this.time, P = this.player, D = this.C.drops;
    const fo = this.powers.foudre;
    if (fo) {
      if (t > fo.until) delete this.powers.foudre;
      else if (t >= fo.next) {
        fo.next = t + D.foudre.every;
        const ms = this.mobsInRadius(P.x, P.y, D.foudre.radius * this.stats.area);
        const dmg = this.powerDmg(D.foudre.dmg);
        for (const m of ms) this.damageMob(m, dmg * (m.boss ? 0.6 : 1), { def: { id: 'foudroiement' }, p: {} });
        for (let i = 0; i < Math.min(4, ms.length); i++) { const m = ms[(Math.random() * ms.length) | 0]; this.fxAt(D.foudre.fx, m.x, m.y, { scale: 0.9 }); } // a few bolts are enough to read it
        this.fxAt(D.foudre.fx, P.x, P.y, { scale: 1.3 });
        this.rings.push({ x: P.x, y: P.y, r0: 20, r1: D.foudre.radius * this.stats.area, t0: t, dur: 0.4, color: '#ffe14a' });
        Audio2.play(D.foudre.snd, 0.7); this.shake(5);
      }
    }
    const fl = this.powers.flamiche;
    if (fl) {
      if (t > fl.until) delete this.powers.flamiche;
      else if (t >= fl.next) {
        fl.next = t + D.flamiche.every;
        const m = this.randomMobNear(P.x, P.y, 430);
        if (m) {
          const a = Math.atan2(m.y - m.r - P.y + 22, m.x - P.x), sp = 520;
          this.projs.push({ x: P.x, y: P.y - 22, vx: Math.cos(a) * sp, vy: Math.sin(a) * sp, sp, dmg: this.powerDmg(D.flamiche.dmg), pierce: 1, life: 1.2, size: 12,
            spell: FLAMICHE, hit: new Set(), target: m, homing: 6, bounce: 0, aoe: 0, t0: t, delay: 0, back: false, burn: 2, fxScale: 2.1 });
          if (Math.random() < 0.3) Audio2.play(D.flamiche.snd, 0.25, rand(0.9, 1.2));
        }
      }
    }
    const lb = this.powers.liberation;
    if (lb && (t > lb.until || lb.charges <= 0)) delete this.powers.liberation;
    // allies
    for (let ai = this.allies.length - 1; ai >= 0; ai--) {
      const A = this.allies[ai];
      A.t += dt; if (A.atkT !== undefined) A.atkT += dt;   // (0.59: was advanced in drawAlly)
      if (t > A.until) { this.fxAt(1100, A.x, A.y, {}); this.allySnd(A.kind, 'die', 0.45); this.allies.splice(ai, 1); continue; }
      if (A.kind === 'drago') { this.updateDrago(A, dt); continue; }
      if (A.kind === 'chaferfu' || A.kind === 'lancier') { this.updateChaferfu(A, dt); continue; }
      const cfg = this.allyCfg(A.kind);
      if (!A.target || A.target.dying || t - (A.retarget || 0) > 0.6) { A.target = this.nearestMob(P.x, P.y, 480) || this.nearestMob(A.x, A.y, 480); A.retarget = t; }
      let tx = P.x + 50, ty = P.y + 20;
      if (A.target) { tx = A.target.x; ty = A.target.y; }
      const dx = tx - A.x, dy = ty - A.y, d = Math.hypot(dx, dy) || 1, spd = cfg.speed;
      if (d > 6) { A.x += dx / d * spd * dt; A.y += dy / d * spd * dt; if (Math.abs(dx) > 2) A.flip = dx < 0; A.view = dy < -0.35 * d ? 'L' : 'R'; }
      A.hitT -= dt;
      if (A.target && d < A.target.r + 22 * (cfg.scale || 2.3) / 2.3 && A.hitT <= 0) {
        A.hitT = cfg.every || 0.35; A.atkT = 0;
        const m = A.target, src = { def: { id: A.kind === 'majeure' ? 'arakne_majeure' : 'arakne_agressive' }, p: {} }, dm = this.powerDmg(cfg.dmg);
        this.damageMob(m, dm, src);
        if (cfg.aoe) { for (const o of this.mobsInRadius(m.x, m.y, cfg.aoe)) if (o !== m) this.damageMob(o, dm * 0.5, src, true); this.rings.push({ x: m.x, y: m.y, r0: cfg.aoe * 0.4, r1: cfg.aoe, t0: t, dur: 0.3, color: cfg.color, fill: 1 }); }
        // (0.95: the Arakne majeure pushes once per summon, three times as far: cfg.pushOnce, its knock x3 in content)
        if (!m.boss && !(cfg.pushOnce && A.pushed)) { m.kx += dx / d * cfg.knock * 3; m.ky += dy / d * cfg.knock * 3; if (cfg.pushOnce) A.pushed = true; }
        if (Math.random() < 0.5) this.allySnd(A.kind, 'atk', 0.38, rand(1.0, 1.2));
        A.target = null;
      }
    }
  }
  // spells that move the character (Bond, Assaut, Vol de Pièces): the player can switch them off and on
  moveSpell() { return this.spells.find(s => s.def.t === 'leap' || s.def.t === 'dash') || null; }
  toggleMoveSpells() {
    if (!this.moveSpell()) return;
    this.moveOff = !this.moveOff;
    this.chat(T(this.moveOff ? 'move_off' : 'move_on'), this.moveOff ? '#ff9a7a' : '#9cff9a'); Audio2.blip('click');
  }
  hudHit(x, y) { const b = this.hudMove; return !!(b && Math.hypot(x - b.x, y - b.y) < b.r * 1.15); }
  // ToT's very rare gift: an armoured Dragodinde that fights at your side for the whole run
  spawnDrago() {
    const D = this.C.drago, P = this.player; if (!D || this.allies.some(a => a.kind === 'drago')) return;
    const A = { kind: 'drago', x: P.x - 60, y: P.y + 20, t: 0, born: this.time, until: Infinity, hitT: 0, flip: false, view: 'R', sh: MobSheets.c[D.sprite] || null };
    if (!A.sh) MobSheets.load(D.sprite).then(sh => { A.sh = sh; });
    this.allies.push(A);
    for (let i = 0; i < 30; i++) this.particles.push({ x: A.x + rand(-20, 20), y: A.y - rand(0, 50), vx: rand(-90, 90), vy: rand(-200, -60), t: 0, life: rand(0.6, 1.1), c: pick(['#ffd700', '#fff3a0', '#d4a640', '#ffffff']), s: rand(2.5, 4.5) });
    this.rings.push({ x: A.x, y: A.y, r0: 10, r1: 110, t0: this.time, dur: 0.6, color: '#ffd24a' });
    this.allySnd('drago', 'spawn', 0.7);
  }
  updateDrago(A, dt) {
    const t = this.time, P = this.player, D = this.C.drago;
    if (Math.hypot(A.x - P.x, A.y - P.y) > 650) { A.x = P.x - 50; A.y = P.y + 20; A.target = null; }   // never left behind
    if (!A.target || A.target.dying || t - (A.retarget || 0) > 0.5) { A.target = this.nearestMob(P.x, P.y, 460); A.retarget = t; }
    let tx = P.x - 55, ty = P.y + 18;
    if (A.target) { tx = A.target.x; ty = A.target.y; }
    const dx = tx - A.x, dy = ty - A.y, d = Math.hypot(dx, dy) || 1;
    A.moving = d > 8;
    if (A.moving) { const sp = D.speed * (A.target ? 1 : Math.min(1, d / 120)); A.x += dx / d * sp * dt; A.y += dy / d * sp * dt; if (Math.abs(dx) > 2) A.flip = dx < 0; A.view = dy < -0.35 * d ? 'L' : 'R'; }
    A.hitT -= dt;
    if (A.target && d < A.target.r + 28 && A.hitT <= 0) {
      A.hitT = D.hitEvery; A.atkT = 0;
      const m = A.target;
      this.damageMob(m, this.powerDmg(D.dmg) * (m.boss ? 0.7 : 1), { def: { id: 'dragodinde' }, p: {} });
      if (!m.boss) { m.kx += dx / d * D.knock * 3; m.ky += dy / d * D.knock * 3; }
      if (Math.random() < 0.35) Audio2.play('punch', 0.3, rand(0.9, 1.15));
      if (Math.random() < 0.3) this.allySnd('drago', 'atk', 0.45, rand(0.9, 1.1));
    }
  }
  // Chaferfu (and its critical form, the Chaferfu Lancier): runs around at random, hitting everything it passes
  updateChaferfu(A, dt) {
    const t = this.time, P = this.player, D = this.C.drops.chaferfu, cfg = A.kind === 'lancier' ? D.lancier : D, b = this.bounds;
    A.wT -= dt;
    if (A.wT <= 0 || Math.hypot(A.wx - A.x, A.wy - A.y) < 18) {
      A.wT = rand(0.45, 1.3);
      const m = Math.random() < (A.kind === 'lancier' ? 0.45 : 0.2) ? this.randomMobNear(P.x, P.y, 420) : null;
      if (m) { A.wx = m.x; A.wy = m.y; }
      else { const an = rand(TAU), rr = rand(40, 340); A.wx = clamp(P.x + Math.cos(an) * rr, b.x0, b.x1); A.wy = clamp(P.y + Math.sin(an) * rr * 0.7, b.y0, b.y1); }
    }
    const dx = A.wx - A.x, dy = A.wy - A.y, d = Math.hypot(dx, dy) || 1;
    A.x += dx / d * cfg.speed * dt; A.y += dy / d * cfg.speed * dt;
    if (Math.abs(dx) > 2) A.flip = dx < 0; A.view = dy < -0.35 * d ? 'L' : 'R';
    A.hitT -= dt;
    if (A.hitT <= 0) {
      const ms = this.mobsInRadius(A.x, A.y, cfg.radius);
      if (ms.length) {
        A.hitT = cfg.every; A.atkT = 0;
        const src = { def: { id: A.kind === 'lancier' ? 'chaferfu_lancier' : 'chaferfu' }, p: {} };
        for (const m of ms) this.damageMob(m, this.powerDmg(cfg.dmg) * (m.boss ? 0.6 : 1), src, true);
        if (Math.random() < 0.4) this.allySnd(A.kind, 'atk', 0.3, rand(0.95, 1.2));
      }
    }
  }
  hasted() { return this.allies.some(a => a.kind === 'lancier'); }
  allyCfg(kind) { const D = this.C.drops; return kind === 'drago' ? this.C.drago : kind === 'arakne' ? D.arakne : kind === 'majeure' ? D.arakne.majeure : kind === 'lancier' ? D.chaferfu.lancier : D.chaferfu; }
  // sounds of the allies and summons that have none of their own in the client (data: C.allySnd / C.summonSnd)
  allySnd(kind, ev, vol = 0.5, rate = 1) { const S = (this.C.allySnd || {})[kind]; this.sndOf(S, ev, vol, rate); }
  sndOf(S, ev, vol = 0.5, rate = 1) {
    const k = S && S[ev]; if (!k) return;
    const key = Array.isArray(k) ? pick(k) : k;
    const id = ev + key; if (this.time - ((this._sndT || (this._sndT = {}))[id] || -9) < (ev === 'atk' ? 0.28 : 0.12)) return;
    this._sndT[id] = this.time; Audio2.play(key, vol, rate);
  }
  // ------------------------------------------------ Roublard: Boumbombes (Tic Tac... Badaboum), chain reactions and fire walls
  throwBomb(spell, x, y, o = {}) {
    const P = this.player, st = this.stats, p = spell.p;
    const live = this.bombs.filter(b => !b.done && !b.boomAt);
    if (live.length >= (p.max || 6)) this.detonate(live[0], 1);
    const b = this.bounds; x = clamp(x, b.x0, b.x1); y = clamp(y, b.y0, b.y1);
    this.bombs.push({ bomb: 1, x0: P.x, y0: P.y - 24, x, y, t0: this.time, fly: o.fly || 0.38, fuse: o.fuse !== undefined ? o.fuse : p.fuse, dmg: o.dmg || spell.dmg(),
      r: (o.r || p.radius) * st.area, spell, wall: p.wall, wallDmg: p.wallDmg ? spell.dmg(p.wallDmg) : 0, done: false, landed: false, t: rand(1), slow: p.slow, slowDur: p.slowDur, pull: p.pull, tint: p.tint });
  }
  detonate(b, mult = 1, delay = 0) { if (b.done || b.boomAt) return; b.boomAt = this.time + delay; b.mult = Math.max(b.mult || 1, mult); }
  updateBombs(dt) {
    const T_ = this.time, sh = MobSheets.c[this.C.bombSprite];
    for (let i = this.bombs.length - 1; i >= 0; i--) {
      const b = this.bombs[i]; b.t += dt;
      if (b.done) { this.bombs.splice(i, 1); continue; }
      if (!b.landed && T_ >= b.t0 + b.fly) b.landed = true;
      if (b.landed && !b.boomAt && T_ >= b.t0 + b.fly + b.fuse) b.boomAt = T_;
      if (b.boomAt && T_ >= b.boomAt && b.landed) {
        b.done = true;
        const dmg = b.dmg * (b.mult || 1);
        for (const m of this.mobsInRadius(b.x, b.y, b.r)) {
          this.damageMob(m, dmg, b.spell);
          if (b.slow) { m.slowUntil = T_ + (b.slowDur || 2); m.slowAmt = b.slow; }
          if (!m.boss) { const dx = m.x - b.x, dy = m.y - b.y, d = Math.hypot(dx, dy) || 1, k = b.pull ? -Math.min(b.pull, d - 10) * 4 : 150; m.kx += dx / d * k; m.ky += dy / d * k; }
        }
        this.rings.push({ x: b.x, y: b.y, r0: b.pull ? b.r : 10, r1: b.pull ? 10 : b.r, t0: T_, dur: 0.35, color: b.tint || '#ffb347' });
        if (b.tint) for (let k = 0; k < 14; k++) { const an = rand(TAU); this.particles.push({ x: b.x, y: b.y - 10, vx: Math.cos(an) * rand(60, 200), vy: Math.sin(an) * rand(40, 120) - 60, t: 0, life: 0.45, c: b.tint, s: rand(2, 4) }); }
        if (sh && sh.has('dieR')) this.effects.push({ sh, sym: 'dieR', x: b.x, y: b.y + 6, t: 0, dur: Math.min(1.2, sh.duration('dieR')), scale: ES * 1.1 * b.r / 90, rot: 0 });
        Audio2.play('explosion', 0.4, rand(0.9, 1.15)); this.shake(3);
        // explosions set off the bombs around (chain reaction, +20% each link)
        for (const o of this.bombs) if (!o.done && o.landed && !o.boomAt && dist2(o.x, o.y, b.x, b.y) < (b.r + 70) ** 2) this.detonate(o, (b.mult || 1) * 1.2, 0.12);
      }
    }
    // walls of fire between nearby landed bombs (Bombombe level 4+)
    this.walls.length = 0;
    const live = this.bombs.filter(b => b.landed && !b.done && b.wall);
    for (let a = 0; a < live.length; a++) for (let c = a + 1; c < live.length; c++) {
      const d2 = dist2(live[a].x, live[a].y, live[c].x, live[c].y);
      if (d2 < 250 * 250 && d2 > 25 * 25) this.walls.push([live[a], live[c]]);
    }
    this.wallT = (this.wallT || 0) - dt;
    if (this.wallT <= 0 && this.walls.length) {
      this.wallT = 0.3;
      for (const [A, B] of this.walls) {
        const cx = (A.x + B.x) / 2, cy = (A.y + B.y) / 2, rr = Math.hypot(A.x - B.x, A.y - B.y) / 2 + 30;
        for (const m of this.mobsInRadius(cx, cy, rr)) if (segDist(m.x, m.y, A.x, A.y, B.x, B.y) < m.r + 14) this.damageMob(m, A.wallDmg, A.spell, true);
      }
    }
  }
  // ------------------------------------------------ Pandawa: Karcham (lift) then Chamrak (throw onto the densest group)
  updateTosses(dt) {
    const T_ = this.time, P = this.player;
    for (let i = this.tosses.length - 1; i >= 0; i--) {
      const o = this.tosses[i], m = o.m;
      if (m.dying || P.dead) { m.carried = false; m.liftH = 0; this.tosses.splice(i, 1); continue; }
      if (o.phase === 'lift') {
        const k = Math.min(1, (T_ - o.t0) / o.lift);
        m.x = lerp(o.sx, P.x, k); m.y = lerp(o.sy, P.y - 2, k); m.liftH = 66 * k;
        if (k >= 1) {
          let best = null, bn = 0;
          for (const c of this.mobsInRadius(P.x, P.y, o.throw)) {
            if (c === m || c.dying || c.carried) continue;
            const n = this.mobsInRadius(c.x, c.y, o.aoe).length; if (n > bn) { bn = n; best = c; }
          }
          let tx, ty;
          if (best) { tx = best.x; ty = best.y; } else { const a = P.faceAng || 0; tx = P.x + Math.cos(a) * o.throw * 0.6; ty = P.y + Math.sin(a) * o.throw * 0.4; }
          const b = this.bounds; tx = clamp(tx, b.x0, b.x1); ty = clamp(ty, b.y0, b.y1);
          o.phase = 'fly'; o.t1 = T_; o.x0 = P.x; o.y0 = P.y; o.x1 = tx; o.y1 = ty; o.dur = clamp(Math.hypot(tx - P.x, ty - P.y) / 650, 0.25, 0.55);
          P.faceTo(tx - P.x); P.cast(o.spell.def.anim);
          Audio2.play('saut', 0.45, rand(0.9, 1.1));
        }
      } else {
        const k = Math.min(1, (T_ - o.t1) / o.dur);
        m.x = lerp(o.x0, o.x1, k); m.y = lerp(o.y0, o.y1, k); m.liftH = 66 * (1 - k) + Math.sin(k * Math.PI) * 110;
        if (k >= 1) {
          m.carried = false; m.liftH = 0; m.stunUntil = Math.max(m.stunUntil || 0, T_ + 0.6);
          for (const c of this.mobsInRadius(m.x, m.y, o.aoe)) {
            if (c === m) continue;
            this.damageMob(c, o.dmg, o.spell);
            if (!c.boss) { const dx = c.x - m.x, dy = c.y - m.y, d = Math.hypot(dx, dy) || 1; c.kx += dx / d * o.knock * 4; c.ky += dy / d * o.knock * 4; c.stunUntil = Math.max(c.stunUntil || 0, T_ + 0.35); }
          }
          this.damageMob(m, o.dmg * 1.5, o.spell);
          this.rings.push({ x: m.x, y: m.y, r0: 10, r1: o.aoe, t0: T_, dur: 0.35, color: '#e8c27a' });
          this.fxAt(o.spell.def.fx[0], m.x, m.y, { scale: o.aoe / 70, fit: o.aoe });
          this.shake(5); Audio2.play('impact_lourd', 0.6, rand(0.9, 1.1));
          this.tosses.splice(i, 1);
        }
      }
    }
  }
  liberation() {
    const P = this.player, d = this.C.drops.liberation, lb = this.powers.liberation;
    lb.charges--;
    const r = d.radius * this.stats.area;
    for (const m of this.mobsInRadius(P.x, P.y, r)) {
      this.damageMob(m, this.powerDmg(d.dmg), { def: { id: 'liberation' }, p: {} });
      const dx = m.x - P.x, dy = m.y - P.y, dd = Math.hypot(dx, dy) || 1;
      // thrown about ten times the character's height away (the throw ignores the stun that follows)
      if (!m.boss) { const v = (d.push || 650) * 3.912; m.kx = dx / dd * v; m.ky = dy / dd * v * 0.8; m.flingUntil = this.time + 0.9; m.stunUntil = Math.max(m.stunUntil, this.time + 1.1); }
    }
    this.rings.push({ x: P.x, y: P.y, r0: 10, r1: r, t0: this.time, dur: 0.45, color: d.color });
    this.fxAt(d.fx, P.x, P.y, { scale: 0.7 }); this.shake(4);
    // original sound: Libération has no spell clip, the client only plays the caster's cast animation (d.anim) and its sound
    const ck = d.anim && (Audio2.charSnd(this.charSid, d.anim + 'R') || Audio2.charSnd(80, d.anim + 'R')); Audio2.play(ck ? ck[0] : d.snd, 0.8);
    this.text(P.x, P.y - 80, L(d.name) + ' (' + lb.charges + ')', d.color, 15);
  }
  // a Dofus fell from a monster: the monsters freeze, fireworks of every colour go off, then a message pauses the game
  celebrateDofus(dof, x, y, from) {
    const t = this.time;
    this.freezeUntil = Math.max(this.freezeUntil || 0, t + 2.4);
    this.player.invulnUntil = Math.max(this.player.invulnUntil || 0, t + 3);
    this.fw = { next: t, until: t + 2.0, modalAt: t + 1.7, dof, from };
    this.banner(T('exploit'), dof.color); Audio2.sfx('EVENT', 0.9); Audio2.blip('level');
  }
  updateFireworks() {
    const F = this.fw, t = this.time;
    if (t < F.until && t >= F.next) {
      F.next = t + 0.11;
      const vw = Game.viewW * 0.42, vh = Game.viewH * 0.36, cx = this.cam.x + rand(-vw, vw), cy = this.cam.y + rand(-vh, vh * 0.4);
      const c1 = pick(FW_COLS), c2 = pick(FW_COLS), n = Game.lowFx ? 16 : 26;
      for (let i = 0; i < n; i++) { const a = i / n * TAU + rand(-0.08, 0.08), sp = rand(150, 260); this.particles.push({ x: cx, y: cy, vx: Math.cos(a) * sp, vy: Math.sin(a) * sp * 0.8 - 40, t: 0, life: rand(0.7, 1.1), c: i % 3 ? c1 : c2, s: rand(3, 5) }); }
      this.rings.push({ x: cx, y: cy, r0: 6, r1: rand(50, 90), t0: t, dur: 0.45, color: c1 });
      if (Math.random() < 0.5) Audio2.play('pok', 0.35, rand(0.8, 1.3));
    }
    if (F.modalAt && t >= F.modalAt) { F.modalAt = 0; if (typeof Game !== 'undefined' && Game.dofusExploit) Game.dofusExploit(F.dof, F.from); }
    if (t > F.until + 0.5 && !F.modalAt) this.fw = null;
  }
  fireworks() {
    const P = this.player; const vw = Game.viewW / 2, vh = Game.viewH / 2;
    this.banner(T('fireworks'), '#ff9de2');
    for (const m of this.mobs) {
      if (m.dying || m.boss) continue;
      if (Math.abs(m.x - P.x) < vw + 40 && Math.abs(m.y - P.y) < vh + 40) this.damageMob(m, 1e6, null, true);
    }
    for (let i = 0; i < 160; i++) this.particles.push({ x: P.x + rand(-vw, vw), y: P.y + rand(-vh, vh), vx: rand(-50, 50), vy: rand(-120, 0), t: 0, life: rand(0.6, 1.4), c: pick(['#ff5fb0', '#ffe066', '#7dff9a', '#7fd0ff', '#ffffff', '#c58aff']), s: rand(2, 5) });
    for (let i = 0; i < 8; i++) this.rings.push({ x: P.x + rand(-vw, vw) * 0.8, y: P.y + rand(-vh, vh) * 0.8, r0: 5, r1: rand(60, 120), t0: this.time + i * 0.08, dur: 0.5, color: pick(['#ff5fb0', '#ffe066', '#7dff9a', '#7fd0ff']) });
    this.shake(10); Audio2.blip('boom'); Audio2.sfx('EVENT', 0.6);
  }
  updateFx(dt) {
    for (let i = this.effects.length - 1; i >= 0; i--) { const e = this.effects[i]; e.t += dt * (e.rate || 1); if (e.follow) { e.x = e.follow.x; e.y = e.follow.y; } if (e.t > e.dur) this.effects.splice(i, 1); }
    { // in-place compaction (no splice) and a cap that drops the oldest when a phone is struggling
      const A = this.particles, cap = ((typeof Game !== 'undefined' && Game.lowFx) ? (Game.minFx ? 60 : 110) : typeof Game !== 'undefined' && Game.Q && Game.Q().fx === 1 ? 220 : 340) + (this.fw ? 260 : 0); let j = 0;
      for (let i = 0; i < A.length; i++) { const p = A[i]; p.t += dt; if (p.t > p.life) continue; p.x += p.vx * dt; p.y += p.vy * dt; p.vy += (p.g === undefined ? 260 : p.g) * dt; A[j++] = p; }
      A.length = j; if (j > cap) A.splice(0, j - cap);
      const X = this.texts; j = 0;
      for (let i = 0; i < X.length; i++) { const t = X[i]; t.t += dt; if (t.t > t.life) continue; t.y -= 34 * dt; X[j++] = t; }
      X.length = j;
    }
    for (let i = this.rings.length - 1; i >= 0; i--) { const r = this.rings[i]; if (this.time > r.t0 + r.dur) this.rings.splice(i, 1); }
    for (let i = this.teles.length - 1; i >= 0; i--) { const t = this.teles[i]; if (this.time > t.t0 + t.dur) { if (t.cb) t.cb(); this.teles.splice(i, 1); } }
  }
  endRun() {
    if (this.over) return;
    const victory = this.finalKilled;
    this.over = true; this.victory = victory;
    const S = Store.data;
    if (this.abandoned && this.time < 20) {   // 0.61: given up in the first 20 s: no statistic counts it (the kamas picked up stay)
      this.cancelled = true; S.kamas += this.kamas; Prog.voidRun(this); Store.save(); Game.runOver(false, []); return;   // (0.79: the end screen says 'cancelled', not 'dead')
    }
    this.bonusKamas = victory ? Math.round(20 * (1 + this.mapIdx)) : 0;
    S.kamas += this.kamas + this.bonusKamas;
    S.runs++; S.totalKills += this.kills;
    const best = S.best[this.map.id] || 0; this.newBest = this.time > best; if (this.newBest) S.best[this.map.id] = Math.floor(this.time);
    this.unlockNext();   // (0.34: only with every boss of the zone down, see unlockNext)
    this.recordEndless();
    Prog.runEnd(this);
    Store.save();
    Game.runOver(victory, this.unlockedNow);
  }
}
function st0(run) { return run.stats; }
// 0.61: the half-size an effect animation is drawn at with scale 1 (world units), its typical big frames (cached)
function fxRadius(sh, sym) {
  const c = sh._vr || (sh._vr = {}); if (c[sym] !== undefined) return c[sym];
  const a = sh.anims[sym], s = (a && a.f || []).map(f => Math.max(f[2], f[3]) / 2).filter(v => v > 1).sort((x, y) => x - y);
  return (c[sym] = s.length ? s[Math.floor(s.length * 0.8)] / (sh.zoom || 1) : 0);
}
const FLAMICHE = { def: { id: 'flamiche', fx: [4600] }, p: {} };

// die sounds per monster family
const SFX_DIE = {
  tofu: 'Poolay_Die', piou: 'Poolay_Die', moskito: 'Kilibriss_Die', minoskito: 'Kilibriss_Die', corbac: 'Conardorf_Die', kwak: 'Conardorf_Die',
  bouftou: 'Bitouf_Des_Plaines_Die', boufton: 'Bitouf_Des_Plaines_Die', larve: 'Kaskargo_Die', blop: 'Ti_Molusque_Die', biblop: 'Ti_Molusque_Die', serpentin: 'Kaskargo_Die', serpiplume: 'Kaskargo_Die',
  pissenlit: 'Chiendent_Die', rose: 'Floribombe_Die', tournesol: 'Palmifleur_Die', champ: 'Chiendent_Die', mandrine: 'Floribombe_Die', maitre_bolet: 'Palmifleur_Die',
  arakne: 'Brouture_Die', scaratos: 'Brouture_Die', kramelehon: 'Brouture_Die',
  bwork: 'Guerrier_Zoth_Die', chafer: 'Sergent_Zoth_Die', gobelin: 'Disciple_Zoth_Die', chevaucheur: 'Le_Flib_Die', vampire: 'Gamine_Zoth_Die', maitre_vampire: 'Maitre_Zoth_Die', rib: 'Sergent_Zoth_Die', kwoan: 'Musafa_Die', boo: 'Invoc_Rasboul_Die',
  craqueleur: 'Craqueleur_Poli_Die', craqueboule: 'Krakboule_Poli_Die', noeul: 'Fecorce_Die',
  wabbit: 'Roissingue_Die', tiwabbit: 'Bourbassingue_Die', black: 'Roissingue_Die', wo: 'Barbroussa_Die', grand: 'Barbroussa_Die',
  cochon: 'Meupette_Die', cavalier: 'Meupette_Die', berger: 'Meupette_Die', kanigrou: 'Musafa_Die', sanglier: 'Meupette_Die', prespic: 'Kaskargo_Die', gamino: 'Abrakleur_Sombre_Die',
  bandit: 'Tonneau_Die',
  // v2.0 the shipwreck island
  tikokoko: 'Palmifleur_Die', kokoko: 'Palmifleur_Die', nodkoko: 'Palmifleur_Die', boomba: 'Musafa_Die', nakunbra: 'Sergent_Zoth_Die', canon: 'Tonneau_Die', coffre: 'Tonneau_Die',
};
// 0.92: a drop's room on the ground (world px, its picture's half-size), Run.placeDrop
const DROP_R = { kama: 8, bread: 11, chest: 22, nowelgift: 30, booster: 18, manuel: 18, tmap: 16, dofus: 16, relic: 16, power: 13, plumec: 14, trool: 16, kamaboost: 13, rappel: 13, fee: 13, sablier: 13, houx: 13 };
const SFX_BOSS_DIE = { le_chouque: 'Le_Flib_Die', flib_capitaine: 'Le_Flib_Die', boombata: 'Musafa_Die', chene_mou: 'Fecorce_Die', minotoror: 'Kimbo_Die', minotot: 'Kimbo_Die', dark_vlad: 'Tynril_Die', wa_wabbit: 'Rasboul_Majeur_Die', dragon_cochon: 'Kimbo_Die', bouftou_royal: 'Bitouf_Des_Plaines_Die' };
const SFX_DIE_ALL = [...new Set([...Object.values(SFX_DIE), ...Object.values(SFX_BOSS_DIE), 'Kralamour_Die', 'Tynril_Die'])];
function dieSoundFor(d) {
  if (d.boss) return SFX_BOSS_DIE[d.id] || 'Kralamour_Die';
  for (const k in SFX_DIE) if (d.id.startsWith(k)) return SFX_DIE[k];
  return 'Kido_Die';
}
SFX_DIE_ALL.push('Kido_Die');

// water mask: run-length encoded rows of 0/1 cells (built from the world tiles)
function decodeWater(w) {
  if (!w || !w.rle) return null;
  const bits = new Uint8Array(w.cols * w.rows); let i = 0, v = 0;
  for (const n of w.rle) { if (v) bits.fill(1, i, i + n); i += n; v ^= 1; }
  return { cell: w.cell, cols: w.cols, rows: w.rows, bits };
}

