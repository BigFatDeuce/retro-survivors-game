'use strict';
// ---------------------------------------------------------------- run extras (0.23): relics, random events, Archimonsters,
// Endless mode. Methods added to Run; game.js calls them at a few hook points (constructor, load, spawnMob, killMob,
// bossDeath, update, recompute, collect, endRun). Data: C.relics, C.randEvents, C.archi / C.archiCfg, C.infinite.
Object.assign(Run.prototype, {
  initExtras() {
    const C = this.C, E = C.randEvents;
    this.relics = []; this.souls = []; this.drains = []; this.merchant = null; this.eclipseUntil = 0; this.kamaRainUntil = 0; this._krT = 0;
    this.infinite = !!this.opts.infinite; this.cycle = 0;
    // two random events per run, at random times, never the same twice
    this.randEvents = [];
    if (E && !this.infinite) {
      const kinds = shuffle(E.list.filter(k => !(k === 'kamarain' && this.map.noKamas))).slice(0, E.n);   // (0.68: no kama rain on Nowel)
      kinds.forEach((k, i) => this.randEvents.push({ kind: k, t: rand(E.t0 + i * (E.t1 - E.t0) / E.n, E.t0 + (i + 1) * (E.t1 - E.t0) / E.n), done: false }));
    } else if (E) this.nextRandEvent = rand(E.t0, E.t0 + 120);
  },
  // sheets the extras may need (loaded with the run)
  extraKeys(keys) {
    const C = this.C;
    if (C.monsters.bwork) keys.add(C.monsters.bwork.sprite);
    keys.add(C.monsters.tofu.sprite);
    if (C.spells.cawotte) keys.add('1277_z48');   // (0.73: the Cawotte global spell's own sprite, any class may get it)
  },
  async loadExtras() { this.merchantSprite = new CharSprite(30, [[150, 110, 40], [90, 60, 20], [230, 200, 120]], null, null, null); await this.merchantSprite.load(); },

  // ------------------------------------------------ relics
  relicStats(st) {
    for (const r of this.relics) {
      for (const k in r.bonus) { if (k === 'maxhp') st.maxHp *= 1 + r.bonus[k]; else st[k] = (st[k] || 0) + r.bonus[k]; }
      for (const k in r.special) st[k] = k === 'dashCd' ? (st[k] || 1) * r.special[k] : (st[k] || 0) + r.special[k];
    }
  },
  maybeRelic(m, mini) {   // only what has a big life bar: the bosses (the final one always) and the mini-bosses (Tofuzmo, Coffre Animé); C.relicMax per run
    const C = this.C, d = m.def; if (!C.relics || m.doom || m.endless) return;
    if (this.relics.length + this.pickups.filter(p => p.kind === 'relic').length >= (C.relicMax || 6)) return;
    if ((mini || !(d.final && (!this.isFinalKill || this.isFinalKill(m)))) && Math.random() > (mini ? C.relicMini || 0.12 : C.relicRate || 0.4) * this.stats.luck) return;
    this.dropRelic(m);
  },
  // 0.60: at most C.relicDropMax relics fall in a run, whatever drops them
  dropRelic(m) {
    const C = this.C; if ((this.relicDrops || 0) >= (C.relicDropMax || 99)) return;
    const pool = C.relics.filter(r => !this.relics.includes(r) && !this.pickups.some(p => p.kind === 'relic' && p.v === r.id)); if (!pool.length) return;
    this.relicDrops = (this.relicDrops || 0) + 1; this.dropPickup('relic', m.x - 30, m.y + 6, pick(pool).id);
  },
  // 0.60: an elite (scheduled or not) drops a relic C.relicElite of the time (10 %, Chance helps)
  maybeEliteRelic(m) {
    const C = this.C; if (!C.relics || !C.relicElite || this.relics.length + this.pickups.filter(p => p.kind === 'relic').length >= (C.relicMax || 6)) return;
    if (Math.random() < C.relicElite * this.stats.luck) { const n = this.relicDrops || 0; this.dropRelic(m); if ((this.relicDrops || 0) > n) this.juiceRelic(m); }   // (0.60: a slow motion like a boss)
  },
  gainRelic(id) {
    const r = this.C.relics.find(r => r.id === id); if (!r || this.relics.includes(r)) return;
    this.relics.push(r); this.recompute();
    const S = Store.data; S.relics = S.relics || {}; S.relics[id] = (S.relics[id] || 0) + 1; Store.save();
    this.chat(T('relic_found', { n: L(r.name) }) + ' ' + L(r.desc), '#ffcf3a');
    // 0.38: a moment of its own: a fanfare, a golden burst around the character, the relic and its bonus in the middle of the screen.
    // 0.61: one second of light slow motion and a rewarding sound (Audio2.relicSfx: a rising magic chime over the fanfare)
    Audio2.fanfare(0.8); Audio2.relicSfx(); Audio2.play('stars', 0.8); this.shake(4); this.slowMo(1.0, 0.45); this.flash('255,230,150', 0.35, 0.3);
    if (!this.bossFight()) this.relicShow = { r, t0: performance.now() };   // (0.84: nothing in the middle of the screen during a boss fight)
    const P = this.player; for (let k = 0; k < 3; k++) this.rings.push({ x: P.x, y: P.y - 30, r0: 10, r1: 90 + k * 50, t0: this.time + k * 0.12, dur: 0.6, color: '#ffcf3a' });
    for (let k = 0; k < 40; k++) { const a = rand(TAU), v = rand(120, 320); this.particles.push({ x: P.x, y: P.y - 40, vx: Math.cos(a) * v, vy: Math.sin(a) * v - 80, t: 0, life: rand(0.6, 1.1), s: rand(3, 6), c: pick(['#ffe27a', '#ffcf3a', '#fff6d0']) }); }
  },

  // ------------------------------------------------ Archimonsters
  maybeArchi(m) {
    const A = this.C.archi && this.C.archi[m.def.id], K = this.C.archiCfg; if (!A || !K || m.elite || m.archi) return;
    if (Math.random() > K.rate * this.stats.luck * (this.RUN.rareK || 1)) return;   // (0.60: as frequent per minute with fewer monsters)
    const a = pick(A);
    m.archi = a; m.hp *= K.hp; m.maxHp *= K.hp; m.dmg *= K.dmg; m.speed *= K.speed; m.scale *= K.scale; m.r *= K.scale;
    this.chat(T('archi_appears', { n: L(a.name) }), '#ff9de2'); Audio2.sfx('EVENT', 0.5);
  },
  archiDeath(m) {
    const K = this.C.archiCfg, a = m.archi, S = Store.data; S.souls = S.souls || {};
    const k = String(a.id), first = !S.souls[k]; S.souls[k] = (S.souls[k] || 0) + 1; Prog.add('archis'); Store.save();
    this.souls.push(a.id);
    this.dropGem(m.x, m.y, this.bigAmber(), 1); this.addKamas(K.kamas);   // (0.60: a big amber, 1.3x a normal one)
    const all = Object.values(this.C.archi).reduce((n, l) => n + l.length, 0), got = Object.keys(S.souls).length;
    this.chat(T('archi_soul', { n: L(a.name), c: got, t: all }) + (first ? ' ★' : ''), '#ff9de2');
    Audio2.ui('level', 0.7);
  },

  // ------------------------------------------------ random events and the Endless mode
  // 0.48: life drain (life steal, vampiric weapons): the drained monster glows blood red, red streaks fly from it into
  // the character, who glows too (drawn by render.js: drawDrainMob / drawDrainPlayer / drawDrains)
  drainFx(m) {
    if (!m || m.dying) return; const t = this.time;
    if (t - (m.drainT || -9) < 0.3) return; m.drainT = t; this.player.drainT = t;
    if ((this.drains || (this.drains = [])).length < 14) this.drains.push({ m, t0: t, seed: rand(-1, 1) });
  },
  // 0.53: Sagesse: a chance to block a monster's ranged spell (projectiles, thrown spells; not arrows nor blows)
  blockSpell() {
    const c = this.stats.pblock || 0, P = this.player;
    if (!c || P.dead || Math.random() >= c) return false;
    this.text(P.x, P.y - 78, T('spell_block'), '#bfe8ff', 13); Audio2.ui('shield', 0.5);
    this.rings.push({ x: P.x, y: P.y - 24, r0: 14, r1: 46, t0: this.time, dur: 0.3, color: '#bfe8ff' });
    if (this.ps) this.ps.blocks = (this.ps.blocks || 0) + 1;
    return true;
  },
  // 0.53: once everything is maxed, a level heals with the Incroyable potion de soin de masse (C.massPotion, the bread
  // before): a share of the life, and the summons back to full
  massPotion() {
    const M = this.C.massPotion || { heal: 0.25 }, P = this.player;
    P.heal(this.stats.maxHp * M.heal);
    for (const s of this.summons) if (s.spell && s.spell.p && s.hp < s.spell.p.hp) s.hp = s.spell.p.hp;
    Audio2.play(M.snd || 'pain', 0.8);
    this.rings.push({ x: P.x, y: P.y - 20, r0: 12, r1: 110, t0: this.time, dur: 0.55, color: '#5be07a' });
    for (let i = 0; i < 22; i++) this.particles.push({ x: P.x + rand(-26, 26), y: P.y - rand(0, 50), vx: rand(-20, 20), vy: rand(-120, -50), t: 0, life: rand(0.6, 1.1), c: pick(['#5be07a', '#b8ffc4', '#e8fff0', '#ff6a8a']), s: rand(2, 4.5) });
  },
  // 0.52: elites on a schedule: one every C.elites.every s, then 2, then 3 at a time (C.elites.n), their life
  // multiplied by C.elites.grow (x2) at each wave but fitted so that the last wave reaches C.elites.cap (30 %) of the
  // zone's final boss's life, never more; a life bar and their name over their head (render.js); a chest every other wave
  updateElites() {
    const E = this.C.elites; if (!E || this.tofuMode || this.over) return;
    if (this.eliteT === undefined) {
      this.eliteT = E.t0 || E.every; this.eliteW = 0;
      const stop = (this.RUN.spawnStopT || 9.5) * 60, N = Math.max(2, Math.floor((stop - this.eliteT) / E.every) + 1);
      const fid = (this.map.bosses || []).map(b => b[1]).find(id => this.C.bosses[id] && this.C.bosses[id].final), fb = fid && this.C.bosses[fid];
      const lvl = 1 + 0.01 * (E.lvl || 40), emEnd = (stop / 60) * (this.RUN.pace || 2);   // (the final boss's life at the end of a run, as spawnBoss gives it)
      this.eliteCap = fb ? (E.cap || 0.3) * this.finalHp() * lvl * (1 + 0.04 * emEnd) * (this.zoneMul || 1) * (this.RUN.hpMul || 1) * (this.hard ? this.hard.bossHp : 1) : 1e9;
      this.eliteN = N; this.eliteHp0 = null;
    }
    if (this.time < this.eliteT || this.time > (this.infinite ? 1e9 : (this.RUN.spawnStopT || 9.5) * 60)) return;
    while (this.time >= this.eliteT + E.every) this.eliteT += E.every;   // (one wave at a time: no catching up after a jump in time)
    const w = Math.round((this.eliteT - (E.t0 || E.every)) / E.every); this.eliteT += E.every; this.eliteW = w + 1;   // (the wave's number from the clock)
    const tm = this.time / 60, n = (E.n || [[0, 1]]).reduce((a, s) => tm >= s[0] ? s[1] : a, 1) * (this.hard ? E.hardMul || 1 : 1);   // (0.60: Difficile: twice as many)
    const wave = this.map.waves.find(x => tm >= x[0] && tm < x[1]) || this.map.waves[this.map.waves.length - 1];
    let first = null;
    for (let k = 0; k < n; k++) {
      const [x, y] = this.spawnPos(), m = this.spawnMob(weighted(wave[2]), x, y, { elite: true, force: true, noArchi: true });
      if (!m) continue;
      if (this.eliteHp0 === null) {   // the growth: x2 a wave, or less if x2 would pass the cap before the last wave
        this.eliteHp0 = m.maxHp; this.eliteG = Math.max(1, Math.min(E.grow || 2, Math.pow(this.eliteCap / m.maxHp, 1 / Math.max(1, this.eliteN - 1))));
      }
      const hp = Math.min(this.eliteCap, Math.max(m.maxHp, this.eliteHp0 * Math.pow(this.eliteG, w)));
      m.hp = m.maxHp = Math.round(hp * this.aidHp()); m.timed = true; m.noChest = !!first || (w + 1) % (E.chest || 2) !== 0; m.xpm = (m.xpm || 1) * (E.xpK || 0.5);
      if (!first) first = m;
    }
    if (first) { this.chat(T('elite_comes', { n: L(first.def.name) }), '#ffb02e'); Audio2.sfx('EVENT', 0.4); }
  },
  updateExtras(dt) {
    if (this._pendingCine) { const f = this._pendingCine; this._pendingCine = null; f(); }   // (0.61: a cinematic held back while a window was open)
    const E = this.C.randEvents, P = this.player;
    this.updateElites();
    if (this.drains && this.drains.length) this.drains = this.drains.filter(d => this.time - d.t0 < 0.5);
    for (const ev of this.randEvents) if (!ev.done && this.time >= ev.t) { ev.done = true; this.startEvent(ev.kind); }
    if (this.infinite && E && this.time >= this.nextRandEvent) { this.nextRandEvent = this.time + rand(100, 160); this.startEvent(pick(E.list.filter(k => !(k === 'kamarain' && this.map.noKamas)))); }
    // kama rain: coins fall around the character
    if (this.kamaRainUntil > this.time && (this._krT -= dt) <= 0) {
      this._krT = E.kamarain.every; const a = rand(TAU), d = rand(30, 260);
      this.dropPickup('kama', clamp(P.x + Math.cos(a) * d, this.bounds.x0, this.bounds.x1), clamp(P.y + Math.sin(a) * d * 0.7, this.bounds.y0, this.bounds.y1), randi(1, 3));
    }
    // 0.33: the skin merchant comes once, after 5 minutes, somewhere on the map (shown on the minimap)
    const MC = C_MERCHANT(this.C);
    if (!this.merchantDone && this.time >= MC.t && !this.over && !this.map.noMerchant) { this.merchantDone = true; this.spawnMerchant(); }
    // the merchant: talk to him when close
    const M = this.merchant;
    if (M) {
      if (this.time > M.until) { this.fxAt(1100, M.x, M.y, {}); this.merchant = null; }
      else if (!M.open && Math.hypot(P.x - M.x, P.y - M.y) < 60 && !P.dead) { M.open = true; M.until = Math.min(M.until, this.time + (MC.after || 15)); if (typeof UI !== 'undefined' && UI.merchantMenu) UI.merchantMenu(this, M); }
      else if (M.open && Math.hypot(P.x - M.x, P.y - M.y) > 110) M.open = false;
    }
    // Endless: the bosses come back every cycle, stronger
    if (this.infinite) {
      const I = this.C.infinite, c = Math.floor(this.time / I.cycle);
      if (c > this.cycle) {
        this.cycle = c; this.zoneMul = (this.baseZoneMul || (this.baseZoneMul = this.zoneMul)) * (1 + I.grow * c);
        if (this.time < (I.bossT || 600)) for (const b of this.map.bosses || []) this.bossQueue.push({ t: this.time + b[0] * 60 * 0.5, id: b[1] });
        this.banner(T('lb_cycle', { n: c + 1 }), '#ff8a65'); this.chat(T('lb_cycle', { n: c + 1 }), '#ff8a65'); Audio2.sfx('EVENT', 0.8);
      }
      // 0.37: from 10:00 on, the zone's final boss comes back every minute, twice as many each time (2, 4, 8…)
      const fb = (this.map.bosses || []).map(b => b[1]).find(id => this.C.bosses[id] && this.C.bosses[id].final), m0 = I.bossT || 600;
      if (fb && this.time >= m0) {
        const w = Math.floor((this.time - m0) / 60);
        if (w >= (this.endlessWave || 0)) {
          if (!this.endlessWave) { this.banner(T('lb_finals', { n: L(this.C.bosses[fb].name) }), '#ff3b3b'); this.chat(T('lb_finals', { n: L(this.C.bosses[fb].name) }), '#ff3b3b'); this.shake(8); Audio2.playMusic(this.map.boss_music, 1.0); }
          this.endlessWave = w + 1; Audio2.sfx('EVENT', 0.8);
          const alive = this.mobs.filter(o => o.endless && !o.dying).length, n = Math.max(0, Math.min(2 ** (w + 1), (I.bossCap || 64) - alive));
          for (let k = 0; k < n; k++) { const b = this.spawnBoss(fb); if (b) b.endless = true; }
        }
      }
    }
  },
  startEvent(kind) {
    const P = this.player, C = this.C, E = C.randEvents; Prog.add('randEvents');
    this.banner(T('ev_' + kind), '#ffcf8a'); this.chat(T('ev_' + kind), '#ffcf8a'); Audio2.sfx('EVENT', 0.7);
    if (kind === 'bworks' && C.monsters.bwork) { this.swarm('bwork', 14); this.ring('bwork', 10); }
    else if (kind === 'tofus') { for (let i = 0; i < 40; i++) this.after(i * 0.12, () => { const a = rand(TAU), d = rand(120, 420); const m = this.spawnMob('tofu', clamp(P.x + Math.cos(a) * d, this.bounds.x0, this.bounds.x1), clamp(P.y + Math.sin(a) * d * 0.7, this.bounds.y0, this.bounds.y1), { force: true, noArchi: true }); if (m) { m.drop = 1; this.fxAt(1100, m.x, m.y, { scale: 0.5 }); } }); }
    else if (kind === 'merchant') {
      const a = rand(TAU), d = 380;
      this.merchant = { x: clamp(P.x + Math.cos(a) * d, this.bounds.x0 + 40, this.bounds.x1 - 40), y: clamp(P.y + Math.sin(a) * d * 0.6, this.bounds.y0 + 40, this.bounds.y1 - 40), until: this.time + E.merchant.stay, open: false, sold: {} };
    }
    else if (kind === 'kamarain') this.kamaRainUntil = this.time + E.kamarain.dur;
    else if (kind === 'eclipse') this.eclipseUntil = this.time + E.eclipse.dur;
  },
  spawnMerchant() {
    const MC = C_MERCHANT(this.C), S = Store.data, b = this.bounds, P = this.player;
    const pool = [...this.C.hats.map(i => ['hat', i]), ...this.C.capes.map(i => ['cape', i]), ...this.C.pets.map(i => ['pet', i])].filter(([, i]) => !(S.owned || []).includes(i.id) && i.price);
    const offers = shuffle(pool).slice(0, MC.n || 6).map(([slot, it]) => { const off = randi(5, 15) * 5; return { slot, it, off, price: Math.max(10, Math.round(it.price * (100 - off) / 100)) }; });
    if (!offers.length) return;
    let x, y, n = 0;
    do { x = rand(b.x0 + 80, b.x1 - 80); y = rand(b.y0 + 80, b.y1 - 80); } while (++n < 40 && (Math.hypot(x - P.x, y - P.y) < 500 || (this.isWater && this.isWater(x, y))));
    this.merchant = { x, y, until: this.time + MC.stay, open: false, sold: {}, offers };
    this.banner(T('ev_merchant'), '#ffcf8a'); this.chat(T('ev_merchant'), '#ffcf8a'); Audio2.sfx('EVENT', 0.7);
  },
  merchantWallet() { return this.kamas + (Store.data.kamas || 0); },   // 0.38: the run's kamas, then the profile's
  merchantBuySkin(o) {
    if (this.merchantWallet() < o.price) return false;
    const S = Store.data, fromRun = Math.min(this.kamas, o.price); this.kamas -= fromRun; S.kamas = (S.kamas || 0) - (o.price - fromRun); S.owned = S.owned || []; if (!S.owned.includes(o.it.id)) S.owned.push(o.it.id);
    Prog.add('kamasSpent', o.price); Store.save();
    const cs = this.charSprite, no = o.slot === 'pet' ? this.cls.nopets : this.cls.nohats;   // worn at once when the class can
    if (cs && !no) { cs[o.slot] = o.it.id; (S.equip = S.equip || {})[o.slot] = o.it.id; Store.save(); }
    Audio2.blip('coin'); Audio2.sfx('EVENT', 0.5); return true;
  },
  merchantPrice(k) { const M = this.C.randEvents.merchant; return Math.round(M[k] * (1 + (M.perZone || 0) * this.mapIdx / 100)); },
  merchantBuy(k) {
    const price = this.merchantPrice(k); if (this.kamas < price) return false;
    if (k === 'heal') this.player.heal(this.stats.maxHp);
    else if (k === 'upgrade') { const o = this.upgradeOptions(1, true)[0] || this.upgradeOptions(1)[0]; if (!o) return false; this.applyUpgrade(o); }
    else if (k === 'relic') { const pool = this.C.relics.filter(r => !this.relics.includes(r)); if (!pool.length) return false; this.gainRelic(pick(pool).id); }
    this.kamas -= price; Audio2.blip('coin'); return true;
  },
  // Endless mode: the result goes into the local leaderboard (per zone, best times first)
  recordEndless() {
    if (!this.infinite) return;
    const S = Store.data, I = this.C.infinite; S.board = S.board || {};
    const L_ = S.board[this.map.id] = S.board[this.map.id] || [];
    const e = { t: Math.floor(this.time), kills: this.kills, lvl: this.level, cls: this.cls.id, hard: !!this.hard, date: Date.now() };
    L_.push(e); L_.sort((a, b) => b.t - a.t || b.kills - a.kills);
    const top = I.top || 10, mode = x => !!x.hard === e.hard;   // (0.54: Normal and Difficile ranked apart, the best `top` of each kept)
    S.board[this.map.id] = [...L_.filter(x => !x.hard).slice(0, top), ...L_.filter(x => x.hard).slice(0, top)];
    this.boardRank = S.board[this.map.id].filter(mode).indexOf(e) + 1;
  },
});

// the skin merchant's settings (C.merchant: t = first second, stay = seconds he waits)
function C_MERCHANT(C) { return Object.assign({ t: 300, stay: 120 }, C.merchant || {}); }
