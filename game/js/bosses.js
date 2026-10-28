'use strict';
// ---------------------------------------------------------------- boss attacks added in 0.27 (methods added to Run;
// updateBoss calls bossAbility for the kinds it doesn't know). Each is telegraphed, like the others:
//  rain     objects fall on marked spots around you (cannonballs, gifts, fire, snowballs… a.color, a.mob = spawns one)
//  ring     a ring of slow projectiles with a gap to slip through
//  fissure  the ground bursts in a line toward you, one step after the other
//  roar     a cry around the boss: slowed (and a little hurt) if you stand in it
//  puddle   blobs that leave toxic puddles on the ground for a while
//  pull     a whirlpool: you are dragged toward the boss for a moment
// Also: the hostile puddles, the player's slow / pull, the Doom's crows as real monsters (elite life).
Object.assign(Run.prototype, {
  initBosses() { this.hzones = []; this.pSlowUntil = 0; this.pSlowAmt = 1; this.pull = null; },
  bossAbility(m, a, d, dx, dy, MEL, RNG) {
    const P = this.player, T0 = this.time, col = a.color || '#ffcf70';
    switch (a.k) {
      case 'rain': {
        const n = a.count || 6, sp = a.spread || 170;
        for (let i = 0; i < n; i++) {
          const x = clamp(P.x + rand(-sp, sp), this.bounds.x0, this.bounds.x1), y = clamp(P.y + rand(-sp, sp) * 0.7, this.bounds.y0, this.bounds.y1), r = a.radius || 55, delay = 0.9 + i * 0.12;
          this.teles.push({ kind: 'circle', x, y, r, t0: T0, dur: delay, cb: () => {
            this.areaHitPlayer(x, y, r, a.dmg * RNG); this.rings.push({ x, y, r0: 8, r1: r, t0: this.time, dur: 0.35, color: col, fill: 1 });
            for (let k = 0; k < 8; k++) this.particles.push({ x, y: y - 6, vx: rand(-90, 90), vy: rand(-200, -60), t: 0, life: 0.5, c: col, s: rand(2, 4) });
            if (a.mob && Math.random() < 0.35) this.spawnMob(a.mob, x, y, { force: true, keep: true });
            Audio2.play('explosion', 0.25, rand(1.1, 1.4));
          } });
        }
      } break;
      case 'ring': {
        const n = a.count || 18, gap = Math.floor(rand(0, n)), w = a.gap || 3, s = a.speed || 120;
        for (let k = 0; k < n; k++) {
          if (((k - gap + n) % n) < w) continue;   // the way out
          const an = k / n * TAU + Math.atan2(dy, dx); this.eprojs.push({ x: m.x, y: m.y - m.r, vx: Math.cos(an) * s, vy: Math.sin(an) * s, dmg: a.dmg * RNG, life: 4, size: 9, color: col });
        }
        this.rings.push({ x: m.x, y: m.y, r0: 10, r1: 70, t0: T0, dur: 0.4, color: col });
      } break;
      case 'fissure': {
        const an = Math.atan2(dy, dx), steps = a.steps || 7, gap = a.step || 60, r = a.radius || 45;
        for (let i = 1; i <= steps; i++) {
          const x = m.x + Math.cos(an) * gap * i, y = m.y + Math.sin(an) * gap * i * 0.8, delay = 0.6 + i * 0.1;
          this.teles.push({ kind: 'circle', x, y, r, t0: T0, dur: delay, cb: () => {
            this.areaHitPlayer(x, y, r, a.dmg * MEL); this.rings.push({ x, y, r0: 6, r1: r, t0: this.time, dur: 0.3, color: col, fill: 1 }); if (i % 2) this.shake(2);
            for (let k = 0; k < 6; k++) this.particles.push({ x, y, vx: rand(-60, 60), vy: rand(-220, -90), t: 0, life: 0.55, c: pick(['#6a4a2a', '#8a6a3a', col]), s: rand(3, 5) });
          } });
        }
        Audio2.play('impact_lourd', 0.5);
      } break;
      case 'roar': {
        const r = a.radius || 220;
        this.teles.push({ kind: 'circle', x: m.x, y: m.y, r, t0: T0, dur: 0.8, cb: () => {
          if (dist2(P.x, P.y, m.x, m.y) < r * r) { this.damagePlayer(a.dmg * MEL, m); this.pSlowUntil = this.time + (a.slowDur || 2); this.pSlowAmt = 1 - (a.slow || 0.45); this.text(P.x, P.y - 80, '💢', '#ff8a50', 18); }
          for (let i = 0; i < 3; i++) this.rings.push({ x: m.x, y: m.y, r0: 20, r1: r, t0: this.time + i * 0.1, dur: 0.5, color: col });
          this.shake(6); const k = Audio2.mobSnd(m.def.gfx, 'atk'); Audio2.play(k ? k[k.length - 1] : 'growl', 0.9, 0.85);
        } });
      } break;
      case 'puddle': {
        const n = a.count || 3;
        for (let i = 0; i < n; i++) {
          const tx = clamp(P.x + rand(-110, 110), this.bounds.x0, this.bounds.x1), ty = clamp(P.y + rand(-80, 80), this.bounds.y0, this.bounds.y1), r = a.radius || 60, dur = Math.max(0.6, Math.hypot(tx - m.x, ty - m.y) / 280);
          this.eprojs.push({ lob: true, x: m.x, y: m.y - m.r * 2, sx: m.x, sy: m.y - m.r * 2, tx, ty, t: 0, dur, aoe: 0, dmg: 0, life: dur + 0.1, size: 9, color: col });
          this.teles.push({ kind: 'circle', x: tx, y: ty, r, t0: T0, dur, cb: () => this.hzones.push({ x: tx, y: ty, r, until: this.time + (a.dur || 6), born: this.time, tick: 0.5, next: 0, dmg: a.dmg * RNG, color: col }) });
        }
      } break;
      case 'pull': {
        if (d > (a.range || 520)) return false;
        this.pull = { m, until: T0 + (a.dur || 1.6), str: a.str || 120 };
        this.rings.push({ x: m.x, y: m.y, r0: a.range || 400, r1: 30, t0: T0, dur: a.dur || 1.6, color: col });
        Audio2.play('aspiration', 0.8);
      } break;
      default: return false;
    }
    return true;
  },
  // the hostile puddles, the slow and the pull (called by update)
  updateBosses(dt) {
    const P = this.player;
    for (let i = this.hzones.length - 1; i >= 0; i--) {
      const z = this.hzones[i]; if (this.time > z.until) { this.hzones.splice(i, 1); continue; }
      if ((z.next -= dt) <= 0 && dist2(P.x, P.y, z.x, z.y) < z.r * z.r * 0.8) { z.next = z.tick; if (!this.cleansed()) this.damagePlayer(z.dmg); }
    }
    const pl = this.pull;
    if (pl && this.cleansed()) this.pull = null;
    else if (pl) {
      if (this.time > pl.until || pl.m.dying) this.pull = null;
      else if (!P.dead && !P.dash) { const dx = pl.m.x - P.x, dy = pl.m.y - P.y, dd = Math.hypot(dx, dy) || 1; if (dd > 40) { P.x += dx / dd * pl.str * dt; P.y += dy / dd * pl.str * dt; } }
    }
  },
  playerSpeedK() {
    const P = this.player, h = P.haste && this.time < P.haste.until ? 1 + P.haste.v : 1, mu = this.mutate && this.time < this.mutate.until ? 1 + this.mutate.haste : 1;   // (0.91: Élixir de Mutation)
    return (this.pSlowUntil > this.time && !this.cleansed() ? this.pSlowAmt : 1) * h * mu;
  },
  // 0.68: Lait de Bambou: the slow, the pull and ToT's slap end, and none of them (nor puddles, nor water) holds for `dur` s
  cleanse(dur) {
    this.pSlowUntil = 0; this.pull = null; if (this.weakUntil > this.time) this.weakUntil = this.time;
    this.cleanUntil = Math.max(this.cleanUntil || 0, this.time + dur);
    this.rings.push({ x: this.player.x, y: this.player.y, r0: 20, r1: 110, t0: this.time, dur: 0.5, color: '#bff5c8', fill: 1 });
  },
  cleansed() { return (this.cleanUntil || 0) > this.time; },
  // the Doom's Maîtres Corbacs call corbacs: real monsters, with the life of the end-of-zone elites
  doomCrows(m, a, dx, dy, RNG) {
    const ramp = 1 + 0.12 * Math.max(0, this.time - (this.C.doom ? this.C.doom.t : 600));
    if (this.mobs.filter(o => o.doomCrow && !o.dying).length > (a.max || 24)) return;
    if (a.range && Math.hypot(dx, dy) > a.range) return;   // 0.37: they call their corbacs only from that close
    for (let k = 0; k < (a.count || 1); k++) {
      const an = Math.atan2(dy, dx) + rand(-0.8, 0.8), c = this.spawnMob('corbac_doom', m.x + Math.cos(an) * 40, m.y + Math.sin(an) * 30, { force: true, keep: true, noArchi: true });
      if (!c) continue;
      c.hp = c.maxHp = c.maxHp * (this.C.doomCrowHp || 5); c.dmg = a.dmg * RNG * ramp * 0.5; c.doomCrow = true; c.drop = 0;
      this.fxAt(1100, c.x, c.y, { scale: 0.6 });
    }
  },
  // drawn on the ground, under everything that walks
  drawHzones(ctx, t) {
    for (const z of this.hzones) {
      const k = Math.min(1, (t - z.born) * 3) * Math.min(1, (z.until - t) * 2);
      drawArea(ctx, z.x, z.y, z.r, z.color, k * 0.9);
      ctx.save(); ctx.globalAlpha = 0.55 * k; ctx.fillStyle = z.color; ctx.beginPath(); ctx.ellipse(z.x, z.y, z.r * 0.85, z.r * 0.5, 0, 0, TAU); ctx.fill();
      ctx.globalAlpha = 0.7 * k; ctx.fillStyle = 'rgba(255,255,255,0.5)';
      for (let i = 0; i < 4; i++) { const ph = (t * 0.8 + i / 4) % 1, a = i * 1.7 + z.x; ctx.beginPath(); ctx.arc(z.x + Math.cos(a) * z.r * 0.5, z.y + Math.sin(a) * z.r * 0.25, 3 + ph * 4, 0, TAU); ctx.fill(); }
      ctx.restore();
    }
    if (this.pull) {   // the whirlpool
      const m = this.pull.m; ctx.save(); ctx.translate(m.x, m.y); ctx.strokeStyle = 'rgba(90,170,255,0.7)'; ctx.lineWidth = 3;
      for (let i = 0; i < 3; i++) { ctx.beginPath(); for (let a = 0; a < TAU * 1.5; a += 0.2) { const r = 20 + a * 26 + i * 18; ctx.lineTo(Math.cos(a - t * 4 + i) * r, Math.sin(a - t * 4 + i) * r * 0.55); } ctx.stroke(); }
      ctx.restore();
    }
  },
});
