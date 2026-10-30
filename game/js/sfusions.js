'use strict';
// 0.95: a fusion of two global spells has no class (cls null): every class can make it
function sfusionOf(f, cls) { return !f.cls || f.cls === cls; }
// ---------------------------------------------------------------- spell fusions (0.60)
// C.spellFusions: three per class (tools/content/fusions060.py): two of its spells, a spell + its favourite weapon type, a spell
// + a global spell. Offered (always among the choices) once both are at their maximum level; the fused spell (C.spells
// [id], sfusion: 1, src: [a, b]) replaces its spells (the weapon stays) and frees their slot, then the 'union' cinematic
// plays. On every hit a fused spell adds its rider (r* params: burn, poison, slow, stun, bleed, mark, blast, web, cloud,
// rock, kamas) and its real Dofus spell's effect (def.fx2). Run.prototype methods, same pattern as extras.js.
Object.assign(Run.prototype, {
  // the fusions this run could make now
  sfusionOptions(opts) {
    for (const f of this.C.spellFusions || []) {
      if (!sfusionOf(f, this.cls.id) || this.sfused.has(f.id) || this.banned.has('sfusion:' + f.id)) continue;
      const a = this.spells.find(s => s.def.id === f.src[0]); if (!a || !a.maxed) continue;
      if (f.kind === 'weapon') { const W = this.weapon; if (!W || !W.maxed || (W.def.of || W.def.id) !== f.src[1]) continue; }
      else { const b = this.spells.find(s => s.def.id === f.src[1]); if (!b || !b.maxed) continue; }
      opts.push({ kind: 'sfusion', id: f.id, lv: 1, w: 6, isNew: true });
    }
  },
  // what a fusion needs, for the menus: [{ id, icon, name, have }] (have: owned and maxed in this run, when there is one)
  applySFusion(id) {
    const C = this.C, d = C.spells[id], f = (C.spellFusions || []).find(x => x.id === id);
    if (!d || !f || this.sfused.has(id)) return;
    const gone = f.kind === 'weapon' ? [f.src[0]] : f.src.slice(), old = this.spells.filter(s => gone.includes(s.def.id));
    const icons = old.map(s => 'sp_' + s.icon); if (f.kind === 'weapon' && this.weapon) icons.push(this.weapon.icon);
    this.spells = this.spells.filter(s => !gone.includes(s.def.id));
    this.orbiters = this.orbiters.filter(o => !old.includes(o.spell));   // (a permanent orbit leaves with its spell)
    for (const g of gone) this.consumed.add(g);
    const s = this.addSpell(id); s.level = MAX_SPELL_LV; s.recalc(); s.cd = 0.4;   // (it starts right after the show: the run is frozen during it)
    for (const fx of d.fx || []) FxSheets.load(fx);
    this.sfused.add(id); Prog.add('sfusions'); Prog.bump('sfDone', id); if (this.ps) this.ps.sfusions = (this.ps.sfusions || 0) + 1;
    this.chat('✦ ' + T('sfusion_union') + ' ' + L(d.name), '#ffcf6a');
    // (0.61: made by a chest, the show waits for its window to close: it played unseen behind it)
    const big = this.chestN >= 3;   // (0.98: made by a boss chest: no slow motion after the show)
    const show = () => this.startCine('union', { def: d, icons, kind: f.kind }, () => {
      const P = this.player; if (!big) this.slowMo(0.9, 0.4); this.flash('255,240,200', 0.4, 0.5); this.shake(6);
      this.rings.push({ x: P.x, y: P.y, r0: 20, r1: 300, t0: this.time, dur: 0.7, color: '#ffcf6a', fill: 1 });
      if (d.fx2) this.fxAt(d.fx2, P.x, P.y - 10, { scale: 1.6 });
      for (const m of this.mobsInRadius(P.x, P.y, 260)) if (!m.boss) { const dx = m.x - P.x, dy = m.y - P.y, dd = Math.hypot(dx, dy) || 1; m.kx += dx / dd * 500; m.ky += dy / dd * 500; }
    });
    if (typeof UI !== 'undefined' && UI.modalOpen && UI.modalOpen()) this._pendingCine = show; else show();
  },
  // the fused spell's effect on every hit (sp.bare: the rider's own damage, no rider again)
  riderHit(m, d, sp) {
    if (sp.bare) return;
    const p = sp.p, t = this.time, st = this.stats;
    const bare = sp._bare || (sp._bare = { def: sp.def, p: {}, bare: true, level: MAX_SPELL_LV });
    if (!m.dying) {
      if (p.rBurn) { m.burnUntil = t + 3; m.burnDps = Math.max(m.burnDps || 0, d * p.rBurn); }
      if (p.rPoison) this.poisonPuff(m, d * p.rPoison / 4 / Math.max(0.01, st.might * this.dmgMul()), 4, bare);   // (0.98: through a little poison zone)
      if (p.rSlow && !m.boss) { m.slowAmt = Math.max(m.slowUntil > t ? m.slowAmt || 0 : 0, p.rSlow); m.slowUntil = t + 1.6; }
      if (p.rStun && Math.random() < (p.rStunP || 1)) m.stunUntil = Math.max(m.stunUntil || 0, t + p.rStun * (m.boss ? 0.2 : 1));
      if (p.rBleed) { m.bleedUntil = t + 2.5; m.burnUntil = t + 2.5; m.burnDps = Math.max(m.burnDps || 0, d * 0.16 * p.rBleed); }
      if (p.rMark) { m.markAmt = Math.max(m.markUntil > t ? m.markAmt || 0 : 0, p.rMark); m.markUntil = t + 5; }
    }
    if (p.rKama && m.dying && !m._rk && Math.random() < p.rKama) { m._rk = 1; this.dropPickup('kama', m.x, m.y, randi(1, 3 + this.mapIdx)); }
    let shown = false;
    if (p.rBlast && t - (sp._bT || -9) > 0.12 && Math.random() < (p.rBlastP || 1)) {   // a small explosion around the monster hit
      sp._bT = t; shown = true; const r = (p.rBlastR || 60) * st.area;
      for (const o of this.mobsInRadius(m.x, m.y, r)) if (o !== m) this.damageMob(o, d * p.rBlast, bare, true);
      if (sp.def.fx2) this.fxAt(sp.def.fx2, m.x, m.y - m.r * 0.5, { scale: r / 70, fit: r });
      this.rings.push({ x: m.x, y: m.y, r0: r * 0.3, r1: r, t0: t, dur: 0.3, color: '#ffd27a', fill: 1 });
    }
    if (p.rWeb && t - (sp._wT || -9) > 0.35) {   // an Arakne web where it hit
      sp._wT = t; const wsp = sp._webSp || (sp._webSp = { def: sp.def, p: { web: 1 }, bare: true, level: MAX_SPELL_LV });
      this.zones.push({ x: m.x, y: m.y, r: p.rWeb * st.area, until: t + 3 * st.duration, tick: 0.5, next: 0, dmg: d * 0.08, color: '#e4e4f0', spell: wsp, born: t, slow: p.rWebSlow || 0.5 });
    }
    if (p.rCloud && t - (sp._cT || -9) > 0.5) {   // a boozy cloud where it hit
      sp._cT = t; this.zones.push({ x: m.x, y: m.y, r: (p.rCloudR || 80) * st.area, until: t + 3 * st.duration, tick: 0.35, next: 0, dmg: d * p.rCloud, color: '#b0420c', spell: bare, born: t, cloud: 1, fart: 1 });   // (0.73: the Pwout de Cawotte's orange cloud and cawottes)
    }
    if (p.rChaos && t - (sp._chT || -9) > 0.06 && this.zones.filter(z => z.chaos).length < 18) {   // 0.96: Marteau du Chaos, little void rifts round the blow
      sp._chT = t; const g = sp._chG || (sp._chG = { tick: 0.25, hit: new Map() }), r = (p.rChaosR || 36) * st.area, dmg = sp.dmg() * p.rChaos;
      if (g.hit.size > 64) for (const [o, l] of g.hit) if (o.dying || t - l >= g.tick) g.hit.delete(o);
      // (0.5 s, one blow at 0.25 and one at 0.5 s: never in the frame of the hammer's own; one clock for all of them, grpHit:
      // a monster under several rifts is hit once a tick)
      for (let i = 0; i < 2; i++) { const a = rand(TAU), d = rand(28, 44); this.zones.push({ x: m.x + Math.cos(a) * d, y: m.y + Math.sin(a) * d * 0.62, r, until: t + 0.5, tick: 0.25, next: t + 0.25, dmg, color: '#8a3ae0', spell: bare, born: t, chaos: 1, grp: g }); }
    }
    if (p.rRock && !m.dying && t - (sp._rT || -9) > 0.15 && Math.random() < (p.rRockP || 1)) {   // a Crackler rock falls on it
      sp._rT = t; this.strikes.push({ x: m.x, y: m.y, r: 48 * st.area, at: t + 0.6, delay: 0.6, dmg: d * p.rRock, spell: bare, stun: 0.5, rock: 1, shake: 1, nofx: true });
    }
    if (p.rCraq && t - (sp._qT || -9) > (p.rCraqCd || 0.45)) {   // 0.68: Crackler strikes (the Osamodas spell's own client clip) on the crowd
      sp._qT = t; shown = true; const r = (p.rCraqR || 70) * st.area, near = this.mobsInRadius(m.x, m.y, 260).filter(o => !o.dying);
      const tg = [m]; while (tg.length < (p.rCraqN || 3) + (st.amount || 0) && near.length) { const o = near.splice(randi(0, near.length - 1), 1)[0]; if (!tg.includes(o)) tg.push(o); }
      tg.forEach((o, k) => this.strikes.push({ x: o.x, y: o.y, r, at: t + 0.18 + k * 0.12, delay: 0.18 + k * 0.12, dmg: d * p.rCraq * (k >= (p.rCraqN || 3) ? this.RUN.extraK || 1 : 1), spell: bare, stun: p.rCraqStun || 0.4, shake: 2, fx: sp.def.fx2, crack: 1 }));
    }
    if (!shown && sp.def.fx2 && t - (sp._fxT || -9) > 0.22) { sp._fxT = t; this.fxAt(sp.def.fx2, m.x, m.y - m.r, { scale: 0.8 }); }
  },
  // ------------------------------------------------ the union (cinematic, ~2.6 s, the run frozen)
  // the two spells' icons circle the character, faster and closer, meet in a white flash and a shockwave; the fused
  // spell's icon rises with turning rays, 'FUSION !' and its name in a Dofus box
  tickUnion(c, dt) {
    const P = this.player, once = (k, f) => { if (!c.fired[k]) { c.fired[k] = true; f(); } };
    const anim = (this.cls.casts && this.cls.casts[0]) || 'anim1', key = P.sprite.has(anim + 'R') ? anim + 'R' : null;
    if (key) { P.castAnim = key; P.castT = Math.min(c.t * 0.7, P.sprite.duration(key) * 0.45); }
    once('riser', () => { Audio2.boosterSfx && Audio2.boosterSfx('riser'); });
    if (c.t < 1.25 && this.particles.length < 300) {   // sparks drawn in by the icons
      const a = rand(TAU), r = rand(90, 180); this.particles.push({ x: P.x + Math.cos(a) * r, y: P.y - 40 + Math.sin(a) * r * 0.6, vx: -Math.cos(a) * r * 1.4, vy: -Math.sin(a) * r * 0.9, g: 0, t: 0, life: 0.6, c: pick(['#ffe27a', '#fff6d0', '#c89cff']), s: rand(2, 4) });
    }
    if (c.t > 1.25) once('burst', () => {
      Audio2.boosterSfx && Audio2.boosterSfx('burst'); Audio2.play('stars', 0.9); Audio2.ui('level', 0.9); this.shake(10);
      for (let i = 0; i < 90; i++) { const a = rand(TAU), v = rand(160, 520); this.particles.push({ x: P.x, y: P.y - 40, vx: Math.cos(a) * v, vy: Math.sin(a) * v * 0.7 - 120, t: 0, life: rand(0.6, 1.3), c: pick(['#ffd700', '#fff3a0', '#ffffff', '#c89cff', '#ff9cf0']), s: rand(3, 7), star: i % 7 === 0 ? 1 : 0 }); }
    });
    if (c.t > 1.75) once('name', () => { Audio2.sfx('EVENT', 0.7); Audio2.play('impact_lourd', 0.6, 1.15); this.shake(5); });   // (0.92: the name slams in)
  },
  drawUnion(ctx, W, H, c) {
    const P = this.player, z = Game.zoom, sx = (P.x - this.cam.x) * z + W / 2, sy = (P.y - 40 - this.cam.y) * z + H / 2, S = Math.min(W, H);
    const k = Math.min(1, c.t / 0.3) * Math.min(1, (c.dur - c.t) / 0.35), d = c.data;
    // darkness with a light on the character
    const g = ctx.createRadialGradient(sx, sy, S * 0.08, sx, sy, S * 0.75); g.addColorStop(0, 'rgba(20,8,30,0)'); g.addColorStop(1, `rgba(20,8,30,${0.8 * k})`);
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    const meet = 1.25, isz = S * 0.085;
    if (c.t < meet) {   // the ingredients spiral in, leaving ghost trails
      const u = c.t / meet, rad = S * 0.26 * (1 - u * u), n = d.icons.length || 2;
      ctx.globalCompositeOperation = 'lighter';
      for (let i = 0; i < n; i++) for (let tr = 5; tr >= 0; tr--) {
        const uu = Math.max(0, u - tr * 0.025), rr = S * 0.26 * (1 - uu * uu), a = i * TAU / n + uu * uu * 9;
        const x = sx + Math.cos(a) * rr, y = sy + Math.sin(a) * rr * 0.62;
        ctx.globalAlpha = tr ? 0.12 * (6 - tr) / 6 * k : 0.9 * k;
        ctx.drawImage(RCache.glow(i ? 'rgba(200,150,255,0.9)' : 'rgba(255,220,120,0.9)'), x - isz, y - isz, isz * 2, isz * 2);
      }
      ctx.globalCompositeOperation = 'source-over';
      for (let i = 0; i < n; i++) {
        const a = i * TAU / n + u * u * 9, x = sx + Math.cos(a) * rad, y = sy + Math.sin(a) * rad * 0.62;
        ctx.globalAlpha = k; Game.icons.drawFit(ctx, d.icons[i], x, y, isz * (1 - 0.3 * u));
      }
    } else {   // the burst, then the fused spell's icon
      const v = c.t - meet;
      if (v < 0.5) { ctx.globalAlpha = (1 - v / 0.5) * 0.9; ctx.fillStyle = '#fffaf0'; ctx.fillRect(0, 0, W, H); }
      for (let i = 0; i < 2; i++) {   // shockwaves
        const w = clamp((v - i * 0.12) / 0.6, 0, 1); if (w <= 0 || w >= 1) continue;
        ctx.globalAlpha = (1 - w) * 0.8; ctx.strokeStyle = i ? '#c89cff' : '#ffe27a'; ctx.lineWidth = S * 0.02 * (1 - w);
        ctx.beginPath(); ctx.ellipse(sx, sy, S * 0.6 * w, S * 0.37 * w, 0, 0, TAU); ctx.stroke();
      }
      const up = clamp(v / 0.35, 0, 1), pop = up < 1 ? 0.4 + 0.8 * Math.sin(up * Math.PI * 0.75) : 1, ix = sx, iy = sy - S * 0.13 * up;
      ctx.save(); ctx.translate(ix, iy); ctx.rotate(c.t * 0.7); ctx.globalAlpha = 0.55 * k * up;   // turning rays
      for (let i = 0; i < 14; i++) { ctx.rotate(TAU / 14); const rg = ctx.createLinearGradient(0, 0, 0, -S * 0.3); rg.addColorStop(0, i % 2 ? 'rgba(200,150,255,0.95)' : 'rgba(255,225,120,0.95)'); rg.addColorStop(1, 'rgba(255,255,255,0)'); ctx.fillStyle = rg; ctx.beginPath(); ctx.moveTo(-S * 0.01, 0); ctx.lineTo(-S * 0.035, -S * 0.3); ctx.lineTo(S * 0.035, -S * 0.3); ctx.lineTo(S * 0.01, 0); ctx.fill(); }
      ctx.restore();
      ctx.globalAlpha = k; ctx.drawImage(RCache.glow('rgba(255,245,210,0.95)'), ix - isz * 1.6, iy - isz * 1.6, isz * 3.2, isz * 3.2);
      Game.icons.drawFit(ctx, 'sp_' + d.def.icon, ix, iy, isz * 1.5 * pop);
      // 0.92 (the brown box was too plain): the name's reveal (drawUnionName)
      this.drawUnionName(ctx, W, H, S, d, v, k);
    }
    ctx.globalAlpha = 1;
  },
  // 0.92: violet energy gathers along a line, the name slams in big and settles (a white flash band, a crack of light,
  // sparks thrown out, a shake from tickUnion), violet flames lick up behind its letters while a light sweeps across
  // them, a few sparks drift round it, then it rises a little and fades into embers. Cached glows only (no particles). 0.95: in the
  // announcements' Cinzel (juice.js annFont). 0.98.1: in capitals, carved in Dofus Retro's gold like the victory (ANN.retro),
  // its energy, flames and sparks gold and orange
  drawUnionName(ctx, W, H, S, d, v, k) {
    const cy = H * 0.66, name = L(d.def.name).toLocaleUpperCase(LANG), kick = T('sfusion_union'), HIT = 0.5;
    const hash = i => { const x = Math.sin(i * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
    const glowV = RCache.glow('rgba(255,150,40,0.95)'), glowP = RCache.glow('rgba(255,200,80,0.9)'), glowW = RCache.glow('rgba(255,244,214,0.95)'), glowG = RCache.glow('rgba(255,214,110,0.95)');
    let fs = Math.round(S * 0.105); ctx.font = annFont(fs); const tw0 = ctx.measureText(name).width; if (tw0 > W * 0.84) fs = Math.floor(fs * W * 0.84 / tw0);   // (big, never wider than the screen)
    ctx.font = annFont(fs); const tw = ctx.measureText(name).width, half = tw / 2 + fs * 0.3;
    const y = cy - (k < 1 && v > 1 ? (1 - k) * S * 0.03 : 0);
    // 1) energy gathering on the line, before the hit
    if (v > 0.2 && v < HIT + 0.1) {
      const g = clamp((v - 0.2) / (HIT - 0.2), 0, 1), w = half * 1.25 * g;
      ctx.save(); ctx.globalCompositeOperation = 'lighter';
      ctx.globalAlpha = 0.9 * k; ctx.drawImage(glowV, W / 2 - w, y - fs * 0.3, w * 2, fs * 0.6);
      ctx.globalAlpha = 0.8 * k * g; ctx.drawImage(glowW, W / 2 - w * 0.7, y - fs * 0.08, w * 1.4, fs * 0.16);
      for (let i = 0; i < 18; i++) {   // wisps drawn into the line
        const side = i % 2 ? 1 : -1, q = (g * 1.6 + hash(i)) % 1, sx0 = W / 2 + side * (half * 1.6 + hash(i + 9) * S * 0.2), sy0 = y + (hash(i + 3) - 0.5) * fs * 2.2;
        const px = sx0 + (W / 2 + side * w * hash(i + 5) - sx0) * q, py = sy0 + (y - sy0) * q, r = fs * (0.08 + 0.1 * (1 - q));
        ctx.globalAlpha = k * Math.sin(q * Math.PI); ctx.drawImage(i % 3 ? glowV : glowP, px - r, py - r, r * 2, r * 2);
      }
      ctx.restore();
    }
    if (v < HIT) return;
    const u = v - HIT;
    // 2) the hit: a flash band, a crack of light across the screen, sparks thrown out
    if (u < 0.35) {
      const q = u / 0.35, cw = half * 0.4 + W * 0.6 * Math.sqrt(q); ctx.save(); ctx.globalCompositeOperation = 'lighter';
      ctx.globalAlpha = (1 - q) * 0.95 * k; ctx.drawImage(glowW, W / 2 - half * 1.6, y - fs * 0.9, half * 3.2, fs * 1.8);
      ctx.globalAlpha = (1 - q) * k; ctx.fillStyle = '#fff8e8'; ctx.fillRect(W / 2 - cw, y - fs * 0.025 * (1 - q) - 1, cw * 2, fs * 0.05 * (1 - q) + 2);
      for (let i = 0; i < 26; i++) {
        const an = hash(i + 40) * TAU, sp = 0.4 + hash(i + 70) * 0.9, dd = fs * (0.4 + 3.2 * sp * Math.sqrt(q)), px = W / 2 + Math.cos(an) * dd * (half / fs), py = y + Math.sin(an) * dd * 0.55 + q * q * fs * 0.6, r = fs * 0.07 * (1 - q);
        if (r < 0.5) continue; ctx.globalAlpha = (1 - q) * k; ctx.drawImage(i % 4 ? glowG : glowW, px - r * 2, py - r * 2, r * 4, r * 4);
      }
      ctx.restore();
    }
    // 3) violet flames behind the letters, flickering, taller just after the hit
    { const n = Math.max(10, Math.round(tw / (fs * 0.32))), surge = 1 + 0.8 * Math.max(0, 1 - u / 0.4);
      ctx.save(); ctx.globalCompositeOperation = 'lighter';
      for (let i = 0; i < n; i++) {   // (each tongue its own width, height, sway and flicker: no picket fence)
        const fx = W / 2 - tw / 2 + (i + 0.2 + 0.6 * hash(i + 300)) * tw / n + Math.sin(u * 2.3 + i * 1.7) * fs * 0.05;
        const fl = 0.45 + 0.55 * Math.abs(Math.sin(u * (5 + 4 * hash(i + 310)) + i * 1.91)), hh = fs * (0.55 + 0.75 * hash(i + 320)) * fl * surge, ww = fs * (0.28 + 0.32 * hash(i + 330));
        ctx.globalAlpha = (0.35 + 0.3 * hash(i + 340)) * k; ctx.drawImage(i % 3 ? glowV : glowP, fx - ww / 2, y - fs * 0.12 - hh, ww, hh * 1.2);
        if (i % 2) { ctx.globalAlpha = 0.3 * k; ctx.drawImage(glowP, fx - ww * 0.22, y - fs * 0.2 - hh * 0.45, ww * 0.44, hh * 0.55); }   // (a hotter core)
      }
      ctx.restore(); }
    // 4) 'FUSION !' above, then the name: it slams from big to its size with a slight overshoot; relief + outline
    const sl = clamp(u / 0.14, 0, 1), sc = sl < 1 ? 1.9 - 0.9 * (1 - Math.pow(1 - sl, 3)) : 1 + 0.035 * Math.sin(clamp((u - 0.14) / 0.2, 0, 1) * Math.PI);
    const kfs = Math.round(fs * 0.42), ky = y - fs * 0.92, ktxt = '✦ ' + kick + ' ✦';
    ctx.font = annFont(kfs, 700); ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.lineJoin = 'round';
    ctx.globalAlpha = k * clamp((v - 0.3) / 0.25, 0, 1); ctx.lineWidth = kfs * 0.22; ctx.strokeStyle = '#1c0d03'; ctx.strokeText(ktxt, W / 2, ky);
    const kg = ctx.createLinearGradient(0, ky - kfs / 2, 0, ky + kfs / 2); kg.addColorStop(0, '#fff6c8'); kg.addColorStop(1, '#ffb43a'); ctx.fillStyle = kg; ctx.fillText(ktxt, W / 2, ky);
    // (composed whole in a canvas of its own, then laid at its opacity once: the stacked relief no longer stays dark
    // while the letters fade)
    const pad = fs * 0.5, cw = Math.ceil(tw + pad * 2), chh = Math.ceil(fs * 1.7), cv = this._unC || (this._unC = document.createElement('canvas'));
    if (cv.width < cw || cv.height < chh) { cv.width = Math.max(cv.width, cw); cv.height = Math.max(cv.height, chh); this._unG = null; }
    const g = this._unG || (this._unG = cv.getContext('2d')); g.setTransform(1, 0, 0, 1, 0, 0); g.globalAlpha = 1; g.globalCompositeOperation = 'source-over'; g.clearRect(0, 0, cv.width, cv.height);
    g.translate(cw / 2, chh * 0.45); g.textAlign = 'center';
    annCarve(g, name, 0, 0, fs, ANN.retro, 900);   // (0.98.1: the victory's carved gold, its lime halo)
    const sw = clamp((u - 0.2) / 0.55, 0, 1);   // a light sweeping across the letters once they have settled
    if (sw > 0 && sw < 1) { g.globalCompositeOperation = 'source-atop'; const lx = -tw / 2 - fs + (tw + fs * 2) * sw, lg = g.createLinearGradient(lx - fs * 0.6, 0, lx + fs * 0.6, 0);
      lg.addColorStop(0, 'rgba(255,255,255,0)'); lg.addColorStop(0.5, 'rgba(255,250,235,0.75)'); lg.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = lg; g.fillRect(-cw / 2, -chh, cw, chh * 2); g.globalCompositeOperation = 'source-over'; }
    ctx.save(); ctx.translate(W / 2, y); ctx.scale(sc, sc); ctx.globalAlpha = k * clamp(u / 0.06, 0, 1);
    ctx.drawImage(cv, 0, 0, cw, chh, -cw / 2, -chh * 0.45, cw, chh);
    ctx.restore();
    // 5) sparks drifting round the name, embers rising off it as it fades
    ctx.save(); ctx.globalCompositeOperation = 'lighter';
    for (let i = 0; i < 14; i++) {
      const an = hash(i + 100) * TAU + u * (0.6 + hash(i + 120)), rx = half * (0.85 + 0.3 * hash(i + 140)), ry = fs * (0.75 + 0.35 * hash(i + 160));
      const px = W / 2 + Math.cos(an) * rx, py = y + Math.sin(an) * ry - fs * 0.1, tw2 = 0.5 + 0.5 * Math.sin(u * 9 + i * 2.3), r = fs * (0.035 + 0.04 * tw2);
      ctx.globalAlpha = k * clamp((u - 0.1) / 0.3, 0, 1) * (0.5 + 0.5 * tw2); ctx.drawImage(i % 2 ? glowG : glowP, px - r * 2, py - r * 2, r * 4, r * 4);
    }
    if (k < 1) for (let i = 0; i < 16; i++) {
      const q = 1 - k, px = W / 2 - tw / 2 + hash(i + 200) * tw, py = y - q * fs * (1 + hash(i + 220) * 1.5), r = fs * 0.06 * (1 - q * 0.5);
      ctx.globalAlpha = k * 0.9; ctx.drawImage(i % 2 ? glowV : glowG, px - r * 2, py - r * 2, r * 4, r * 4);
    }
    ctx.restore(); ctx.globalAlpha = 1;
  },
});
