'use strict';
// ---------------------------------------------------------------- 1.03: the ??? NPC and his card game (C.poker, poker103.py)
// From the third zone unlocked on, in a run without ToT's door, a hooded ??? (client sprite 8008) stands somewhere on the
// map at 5:30. Touching him opens his offer; the player picks a kind of weapon, is pulled into his room (the client's
// map 12332 under a red, glitching veil, black embers rising; Brâkmar's music) through a warping black screen, and plays one
// deal: 5 cards on the table, 1 in hand, the last one picked from 3; the best poker hand wins a unique weapon of that kind
// (equipped at once, its level kept), a wrong pick costs C.poker.lose kamas. Either way he sends the player back the same
// way and is gone. The Run part (spawn, drawing on the map) is here; the scene is the Poker object (drawn like ToT's).
Object.assign(Run.prototype, {
  updatePoker() {
    const PK = this.C.poker; if (!PK) return;
    // 1.08: every run gets one or the other — the ??? where he can come (half the runs), a temporary Dofus everywhere else;
    // and the Dofus at C.poker.tdLate (15:00) if neither came by then (a run started late, a path that skipped the draw)
    if (!this.pokerDone && this.time >= PK.t && !this.over) { this.pokerDone = true; const can = !this.portalRun && !this.map.noMerchant && (Store.data.unlocked || []).includes(PK.fromMap); if (can && Math.random() < (PK.chance === undefined ? 1 : PK.chance)) this.spawnPoker(); else this.dropTDofus(); }
    if (!this.pokerCame && !this.tdDropped && !this.over && this.time >= (PK.tdLate || 900)) this.dropTDofus();
    const N = this.pokerNpc, P = this.player; if (!N) return;
    const d = Math.hypot(P.x - N.x, P.y - N.y);
    if (this.time > N.until && !N.open) { this.fxAt(1100, N.x, N.y, {}); this.pokerNpc = null; return; }
    if (N.away && d > 110) N.away = false;   // (after a refusal: he asks again only once the player came back)
    if (!N.open && !N.away && d < 60 && !P.dead && typeof UI !== 'undefined') { N.open = true; UI.pokerOffer(this, N); }
  },
  spawnPoker() {
    const PK = this.C.poker, b = this.bounds, P = this.player; let x, y, n = 0;
    do { x = rand(b.x0 + 80, b.x1 - 80); y = rand(b.y0 + 80, b.y1 - 80); } while (++n < 40 && (Math.hypot(x - P.x, y - P.y) < 500 || (this.isWater && this.isWater(x, y))));
    this.pokerCame = true; this.pokerNpc = { x, y, until: this.time + PK.stay, open: false };
    MobSheets.load(PK.sprite).then(sh => { this.pokerSheet = sh; });
    this.announce(T('pk_ev_t'), T('pk_ev'), '#c9a0ff'); Audio2.sfx('EVENT', 0.6);
  },
  // 1.07: a temporary Dofus (C.tdofus, one at random) where the ??? stranger did not come: somewhere dry, far from the
  // character, on the minimap; picked up, its bonus lasts the run (Run.tdofus: recompute, damagePlayer, the HUD's column)
  dropTDofus() {
    const L_ = this.C.tdofus; if (!L_ || !L_.length) return;
    const d = pick(L_), b = this.bounds, P = this.player; let x, y, n = 0;
    do { x = rand(b.x0 + 80, b.x1 - 80); y = rand(b.y0 + 80, b.y1 - 80); } while (++n < 40 && (Math.hypot(x - P.x, y - P.y) < 500 || (this.isWater && this.isWater(x, y))));
    this.tdDropped = true; this.dropPickup('tdofus', x, y, d.id); this.announce(L(d.name), T('td_here'), d.color); Audio2.sfx('EVENT', 0.6);
  },
  gotTDofus(id) {
    const d = (this.C.tdofus || []).find(o => o.id === id); if (!d || this.tdofus) return;
    this.tdofus = d; this.recompute(); this.chat(T('td_got', { n: L(d.name) }) + ' ' + L(d.desc), d.color, 28);
    // shown like a relic (render.js relicShow), in blue with the temporary ring: its own rays, word and burst
    Audio2.fanfare(0.8); Audio2.relicSfx(); this.shake(4); this.slowMo(1.0, 0.45); this.flash('150,215,255', 0.35, 0.3);
    this.relicShow = { r: { name: d.name, desc: d.desc, icon: 'dofus_hd_' + d.icon }, td: 1, t0: performance.now(), sp: this.bossFight() ? 2 : 1 };
    const P = this.player; for (let k = 0; k < 3; k++) this.rings.push({ x: P.x, y: P.y - 30, r0: 10, r1: 90 + k * 50, t0: this.time + k * 0.12, dur: 0.6, color: '#7fd0ff' });
    for (let k = 0; k < 40; k++) { const a = rand(TAU), v = rand(120, 320); this.particles.push({ x: P.x, y: P.y - 40, vx: Math.cos(a) * v, vy: Math.sin(a) * v - 80, t: 0, life: rand(0.6, 1.1), s: rand(3, 6), c: pick(['#bdf0ff', '#7fd0ff', '#ffffff']) }); }
  },
  // the Jyfus: hit, the character lets out a cloud of poison (once a cd at most)
  tdofusHit() {
    const H = this.tdofus && this.tdofus.poisonHit, P = this.player; if (!H || this.time - (this._jyT || -9) < H.cd) return;
    this._jyT = this.time; this.poisonCloud(P.x, P.y, H.r * this.stats.area, H.dps, H.dur, 0.6, { def: { id: 'jyfus' }, p: {} });   // (the Piège Empoisonné's gas colour: the Jyfus's light green vanished on grass)
  },
  // drawn with the merchant (render.js): standing, a violet '???' over his hood
  drawPokerNpc(ctx, t) {
    const N = this.pokerNpc, sh = this.pokerSheet; if (!N || !sh) return;
    sh.draw(ctx, sh.frameAt('staticR', 0, true), N.x, N.y, ES * 1.6, N.x > this.player.x);   // (bigger than a monster: he must be found; 1.05: one still frame, its 5 copies differ a little and flickered)
    const bob = Math.sin(t * 3) * 3; outlinedText(ctx, T('pk_name'), N.x, N.y - 78 + bob, '#d9b8ff', 20, 'center');   // (1.05: just over his hood, ~64 above his feet; was 215)
  },
  // the prize: a unique weapon of that kind, at the current weapon's level (its evolutions and fusion kept within a kind)
  pokerWeapon(def) {
    const W = this.weapon, nw = new SpellInst(this, def), kind = w => w.of || w.id;
    if (W) { nw.level = W.level; if (kind(W.def) === kind(def)) { nw.evo = Object.assign({}, W.evo); nw.fusion = W.fusion; nw.finale = W.finale; } nw.recalc(); }
    this.weapon = nw; this.charSprite.weapon = def.acc || null; this.gotWeapon(def); this.recompute();
  },
});

const Poker = {
  active: false,
  async start(run, kind, done) {   // (1.05: lost / keep / gotIt reset too: a loss or a 'keep mine' of an earlier game came back on a win as '-100 K' / no weapon)
    const PK = Game.C.poker, deal = pick(PK.deals), pool = (Game.C.uniqueWeapons || []).filter(w => w.of === kind);
    Object.assign(this, { run, kind, done, deal, prize: weighted(pool.map(w => [w, w.blood ? (Game.C.bloodW || 0.6) : 1])), active: true, t: 0, parts: [], timers: [], won: null, lost: 0, keep: false, gotIt: false, fly: null, glitch: 0, gNext: 1.5, trans: { t: 0, dir: 'in' } });
    Audio2.playMusic(PK.music, 1.2); Audio2.preload(['pages', 'stars', 'error', 'rapid_swishes_shorter']).catch(() => { });
    UI.clear();
    const loads = [MobSheets.load(PK.sprite).then(s => { this.npc = s; }), Assets.loadImg('assets/ui/poker/room.webp').then(b => { this.bg = b; }), Assets.loadImg('assets/ui/poker/cards.webp').then(c => { this.cards = c; })];
    await Promise.all(loads);
    this.after(1.5, () => { this.trans = null; this.buildUI(); this.dealCards(); });
  },
  after(sec, cb) { this.timers.push({ t: sec, cb }); },
  // ---------------------------------------------------------------- the cards (DOM: sprites of cards.webp, 13 x 5)
  cardEl(code, cls = '') {
    const el = h('div', { class: 'pk-card ' + cls });
    if (code) { const c = POKER_RANK.indexOf(code[0]), r = 'dhsc'.indexOf(code[1]); el.style.backgroundPosition = `${c * 100 / 12}% ${r * 25}%`; }
    else el.style.backgroundPosition = '0% 100%';   // (the back)
    return el;
  },
  buildUI() {
    const D = this.deal;
    this.say = h('div', { class: 'pk-say' }, h('b', {}, T('pk_name') + ' : '), '« ' + T('pk_rules') + ' »');
    this.board = h('div', { class: 'pk-board' }, ...D.b.map(c => this.cardEl(c, 'deal')));
    this.hand = h('div', { class: 'pk-hand' }, h('small', {}, T('pk_yours')), this.cardEl(D.h, 'deal'));
    this.opts = h('div', { class: 'pk-opts' }, ...D.o.map((c, i) => { const b = h('button', { class: 'pk-opt', disabled: true, onclick: () => this.choose(i) }, this.cardEl(c), h('span', { class: 'pk-hn' })); return b; }));
    this.root = h('div', { class: 'screen poker' }, this.say, this.board, h('div', { class: 'pk-row' }, this.hand, this.opts));
    UI.rootEl.append(this.root);
  },
  dealCards() {
    const all = [...this.board.children, this.hand.querySelector('.pk-card')];
    all.forEach((el, i) => this.after(0.15 + i * 0.22, () => { el.classList.remove('deal'); Audio2.sfx('pages', 0.5, rand(0.95, 1.1)); }));
    this.after(0.4 + all.length * 0.22, () => { for (const b of this.opts.children) b.disabled = false; this.opts.children[0].focus(); if (Game.debug.bot) this.choose(this.deal.a); });
  },
  choose(i) {
    if (this.won !== null) return;
    const D = this.deal, PK = Game.C.poker; this.won = i === D.a;
    [...this.opts.children].forEach((b, j) => { b.disabled = true; b.classList.add(j === D.a ? 'best' : j === i ? 'bad' : 'other'); b.querySelector('.pk-hn').textContent = T('pk_hand_' + PK.hands[D.k[j]]); });
    if (this.won) {
      Audio2.play('stars', 0.8); Audio2.ui('level', 0.7);
      this.sayLine(T('pk_win'));
      this.after(1.2, () => { this.fly = { t: 0 }; Audio2.sfx('rapid_swishes_shorter', 0.7); });
      this.after(2.3, () => this.prizeWindow());
    } else {
      const R = this.run, k = Math.min(R.kamas, PK.lose); R.kamas -= k; this.lost = k;
      Audio2.sfx('error', 0.7); this.glitch = 0.5;
      this.sayLine(T('pk_lose', { n: fmtNum(PK.lose) }));
      this.after(1.0, () => this.root.appendChild(h('div', { class: 'start-row pk-go' }, btn(T('continue'), () => this.leave(), 'orange big'))));
    }
  },
  sayLine(s) { this.say.replaceChildren(h('b', {}, T('pk_name') + ' : '), '« ' + s + ' »'); },
  // the won weapon: what it does, as the level-up cards say it
  prizeWindow() {
    const R = this.run, w = this.prize; if (!w) { this.leave(); return; }
    this.fly = null; this.gotIt = true;
    const W = R.weapon, lv = W ? W.level : 1;   // (a weapon in hand: he offers the swap, at that weapon's level; or keep it)
    const el = h('div', { class: 'pk-prize' }, iconImg(w.icon, 72), h('h2', {}, T('pk_won', { n: L(w.name) })),
      h('div', { class: 'pk-fx' }, fxNodes(realSummaryParts(R, w, lv))), w.desc ? h('p', { class: 'sub' }, fxDesc(L(w.desc))) : null,
      W ? h('p', { class: 'pk-cur' }, iconImg(W.def.icon, 28), ' ' + T('pk_current', { n: L(W.def.name), l: W.level })) : null,
      W ? h('div', { class: 'start-row' }, btn(T('pk_swap'), () => this.leave(), 'orange big'), btn(T('pk_keep'), () => { this.keep = true; this.leave(); }, 'big'))
        : h('div', { class: 'start-row' }, btn(T('continue'), () => this.leave(), 'orange big')));
    this.root.appendChild(el); el.querySelector('button').focus();
    if (Game.debug.bot) this.after(0.5, () => this.leave());
  },
  leave() {
    if (this.trans) return;
    if (this.root) { this.root.remove(); this.root = null; }   // (its buttons gone at once: a controller's cursor no longer stays on the teleport)
    if (typeof Nav !== 'undefined') Nav.set(null);
    this.trans = { t: 0, dir: 'out' };
    this.after(1.5, () => this.close());
  },
  close() {
    this.active = false; this.timers = []; if (this.root) this.root.remove(); this.root = null; UI.clear();
    this.done(this.won && !this.keep ? this.prize : null, this.lost || 0);
  },
  // ---------------------------------------------------------------- the scene (canvas)
  update(dt) {
    this.t += dt; if (this.trans) this.trans.t += dt;
    for (let i = this.timers.length - 1; i >= 0; i--) { const tm = this.timers[i]; if ((tm.t -= dt) <= 0) { this.timers.splice(i, 1); tm.cb(); } }
    if (this.fly) this.fly.t += dt;
    if (this.glitch > 0) this.glitch -= dt; else if ((this.gNext -= dt) <= 0) { this.glitch = rand(0.08, 0.22); this.gNext = rand(3, 8); }   // (a glitch every 3-8 s)
    const W = Game.cw, H = Game.ch, d = Game.dpr || 1;   // black embers rising from the floor
    if (this.parts.length < 90 && Math.random() < dt * 40) this.parts.push({ x: rand(W), y: H + 10, vx: rand(-15, 15) * d, vy: -rand(30, 90) * d, t: 0, life: rand(3, 6), r: rand(1.5, 4.5) * d, w: rand(TAU) });
    for (const p of this.parts) { p.t += dt; p.x += (p.vx + Math.sin(p.t * 2 + p.w) * 18 * d) * dt; p.y += p.vy * dt; }
    this.parts = this.parts.filter(p => p.t < p.life);
  },
  lay() { const W = Game.cw, H = Game.ch, k = Math.min(W / 1280, H / 720); return { W, H, k, nx: W * 0.84, px: W * 0.16, gy: H * 0.8 }; },
  draw(ctx) {
    const A = this.lay(), { W, H } = A; ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, H);
    const tr = this.trans, tk = tr ? Math.min(1, tr.t / 1.5) : 1, sceneA = !tr ? 1 : tr.dir === 'in' ? Math.max(0, (tk - 0.55) / 0.45) : Math.max(0, 1 - tk / 0.45);
    if (sceneA > 0 && this.bg) {
      ctx.globalAlpha = sceneA;
      const s = Math.max(W / this.bg.width, H / this.bg.height); ctx.drawImage(this.bg, (W - this.bg.width * s) / 2, (H - this.bg.height * s) / 2, this.bg.width * s, this.bg.height * s);
      ctx.globalCompositeOperation = 'multiply'; ctx.fillStyle = '#c23a3a'; ctx.fillRect(0, 0, W, H); ctx.globalCompositeOperation = 'source-over';   // the red veil
      if (!this.vig || this.vigH !== H || this.vigW !== W) { this.vigW = W; this.vigH = H; this.vig = ctx.createRadialGradient(W / 2, H / 2, H * 0.25, W / 2, H / 2, H * 0.85); this.vig.addColorStop(0, 'rgba(0,0,0,0)'); this.vig.addColorStop(1, 'rgba(10,0,0,0.75)'); } ctx.fillStyle = this.vig; ctx.fillRect(0, 0, W, H);
      if (this.npc) this.npc.draw(ctx, this.npc.frameAt('staticR', 0, true), A.nx, A.gy, 5.6 * A.k, true);   // (1.05: one still frame: its copies flickered)
      const P = this.run.charSprite; if (P) P.draw(ctx, 'staticR', this.t, A.px, A.gy, 3.6 * A.k, false, { loop: true });
      const glow = RCache.glow('rgba(255,70,20,0.7)');
      for (const p of this.parts) {   // black embers: a dark core in a soft red glow, flickering
        const a = Math.min(1, p.t / 0.5, (p.life - p.t) / 1) * (0.7 + 0.3 * Math.sin(p.t * 9 + p.w)), g = p.r * 4;
        ctx.globalAlpha = sceneA * a * 0.6; ctx.drawImage(glow, p.x - g, p.y - g, g * 2, g * 2);
        ctx.globalAlpha = sceneA * a; ctx.fillStyle = '#0a0000'; ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, TAU); ctx.fill();
      }
      ctx.globalAlpha = 1;
      this.drawFly(A);
      if (this.glitch > 0) this.glitchFx(ctx, W, H);
    }
    if (tr) this.warp(ctx, W, H, tk, tr.dir);
  },
  // the won weapon flies from him to the player, over the cards: on a canvas laid over the scene's DOM
  drawFly(A) {
    const { W, H } = A;
    if (!this.fly || !this.prize || !this.root) { if (this.flyC) { this.flyC.remove(); this.flyC = null; } return; }
    let c = this.flyC; if (!c) { c = this.flyC = h('canvas', { class: 'pk-fly' }); this.root.append(c); }
    if (c.width !== W || c.height !== H) { c.width = W; c.height = H; }
    const g = c.getContext('2d'); g.clearRect(0, 0, W, H);
    const q = Math.min(1, this.fly.t / 1.0), e = q * q * (3 - 2 * q), x = A.nx + (A.px - A.nx) * e, y = A.gy - 160 * A.k - Math.sin(q * Math.PI) * 120 * A.k, s = (70 + 40 * Math.sin(q * Math.PI)) * A.k;
    g.drawImage(RCache.glow('rgba(255,210,120,0.8)'), x - s, y - s, s * 2, s * 2); Game.icons.drawFit(g, this.prize.icon, x, y, s);
  },
  // a few bands of the picture shifted sideways, a red / cyan split
  glitchFx(ctx, W, H) {
    for (let i = 0; i < 6; i++) { const y = rand(H), hh = rand(4, 40) * (Game.dpr || 1), dx = rand(-40, 40) * (Game.dpr || 1); ctx.drawImage(ctx.canvas, 0, y, W, hh, dx, y, W, hh); }
    ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha = 0.18; ctx.fillStyle = Math.random() < 0.5 ? '#ff0030' : '#00e0ff'; ctx.fillRect(0, rand(H), W, rand(10, 80)); ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
  },
  // the teleport: on black, rings of violet / blood light warped by moving waves, swelling then collapsing into the middle
  warp(ctx, W, H, k, dir) {
    const cx = W / 2, cy = H / 2, R = Math.hypot(W, H) / 2, f = Math.sin(k * Math.PI), t = this.t;
    ctx.globalAlpha = dir === 'in' ? Math.min(1, k * 3) * (k < 0.55 ? 1 : 1 - (k - 0.55) / 0.45) : Math.min(1, k / 0.3) * (k < 0.8 ? 1 : 1 - (k - 0.8) / 0.2);
    ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, H);
    ctx.lineWidth = 6 * (Game.dpr || 1); ctx.globalCompositeOperation = 'lighter';
    for (let r = 0; r < 14; r++) {
      const base = ((r / 14 + t * 0.35 * (dir === 'in' ? 1 : -1)) % 1) * R * (0.3 + f);
      ctx.strokeStyle = r % 2 ? `rgba(160,60,255,${0.5 * f})` : `rgba(255,40,60,${0.45 * f})`; ctx.beginPath();
      for (let a = 0; a <= 64; a++) { const an = a / 64 * TAU, dr = Math.sin(an * 5 + t * 6 + r) * 18 * f + Math.sin(an * 3 - t * 4) * 26 * f; const x = cx + Math.cos(an) * (base + dr), y = cy + Math.sin(an) * (base + dr) * 0.7; a ? ctx.lineTo(x, y) : ctx.moveTo(x, y); }
      ctx.stroke();
    }
    ctx.globalCompositeOperation = 'source-over'; ctx.globalAlpha = 1;
  },
};
const POKER_RANK = '23456789TJQKA';
