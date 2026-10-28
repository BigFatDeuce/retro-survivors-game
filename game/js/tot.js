'use strict';
// ---------------------------------------------------------------- ToT, the Game Master: a light-hearted quiz mini-game
// Each question sits in a card in the middle of the screen with its three answers. Between questions the Game Master
// (the big lion GM skin standing on its hind legs) clowns around on stage with a speech bubble.
// Three hearts each; a right answer hurts ToT, a wrong one hurts you.
const QUIZ_FX = { 64: null, 46: 1100, 169: 903, 434: 1052, 20: 105, 141: 806, 170: 901, 102: 601, 181: 1003, 4: 412, 133: 704, 121: 702, 184: 1001, 128: 707, 88: 1052, 101: 601, 98: 509, 52: 306, 126: 702, 69: 805 };
const TOT_LH = 69; // the lion's height in world px (sheet frame height / zoom)
const totEase = {
  io: k => k < 0.5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2,
  out: k => 1 - (1 - k) * (1 - k),
  in: k => k * k,
  back: k => { const c = 1.9; return 1 + (c + 1) * Math.pow(k - 1, 3) + c * Math.pow(k - 1, 2); },
  bounce: k => { const n = 7.5625, d = 2.75; if (k < 1 / d) return n * k * k; if (k < 2 / d) return n * (k -= 1.5 / d) * k + 0.75; if (k < 2.5 / d) return n * (k -= 2.25 / d) * k + 0.9375; return n * (k -= 2.625 / d) * k + 0.984375; },
};
// the lion's moves: fn(a, k, dt, A) runs every frame with k = 0..1 over the move's duration
const TOT_ACTS = {
  enter: { dur: 1.0, fn(a, k, dt, A) { const L = this.L; L.anim = 'runS'; L.flip = true; L.x = lerp(1.18, A.cx, totEase.out(k)); L.hop = Math.abs(Math.sin(k * 9)) * 4; this.dust(a, dt, A); } },
  // a lap of honour around the stage
  lap: { dur: 2.4, init() { Audio2.play('dodge_604', 0.4); }, fn(a, k, dt, A) {
    const L = this.L, an = k * TAU, R = 72 * A.rk;
    L.anim = 'runS'; L.dx = Math.sin(an) * R; L.dy = -(1 - Math.cos(an)) * 13; L.flip = Math.cos(an) < 0;
    L.sx = L.sy = 1 - (1 - Math.cos(an)) * 0.05; L.hop = Math.abs(Math.sin(a.t * 14)) * 3; this.dust(a, dt, A);
  } },
  // walks forward while sliding backwards, then the other way
  moonwalk: { dur: 2.6, fn(a, k, dt, A) {
    const L = this.L, D = 62 * A.rk; L.anim = 'walkR';
    if (k < 0.5) { L.flip = false; L.dx = -D * totEase.io(k * 2); } else { L.flip = true; L.dx = -D * (1 - totEase.io((k - 0.5) * 2)); }
    this.every(a, 'n', 0.3, () => this.note(A));
  } },
  // spins like a top
  spin: { dur: 1.9, init() { Audio2.play('dodge_604', 0.45, 1.2); }, fn(a, k, dt, A) {
    const L = this.L, V = ['staticF', 'staticR', 'staticB', 'staticR'], F = [false, false, false, true];
    const i = Math.floor((k * k * (3 - 2 * k)) * 30) % 4; L.anim = V[i]; L.flip = F[i]; L.hop = Math.sin(k * Math.PI) * 24;
    if (k > 0.92) this.once(a, 's', () => { this.stars(A, 8); Audio2.play('stars', 0.5); });
  } },
  // four bouncy jumps with squash and stretch
  bounce: { dur: 2.0, fn(a, k, dt, A) {
    const L = this.L, n = 4, i = Math.min(n - 1, Math.floor(k * n)), p = (k * n) - i; L.anim = 'staticF';
    if (a.s.i !== i) { a.s.i = i; Audio2.play('jump', 0.35, 1 + i * 0.08); }
    L.hop = Math.sin(p * Math.PI) * (36 - i * 5);
    const sq = p < 0.14 ? 1 - p / 0.14 : p > 0.9 ? (p - 0.9) / 0.1 * 0.5 : 0;
    L.sy = 1 - 0.2 * sq + Math.sin(p * Math.PI) * 0.06; L.sx = 1 + 0.14 * sq;
  } },
  // a backflip
  backflip: { dur: 1.7, fn(a, k, dt, A) {
    const L = this.L; L.anim = 'staticR'; L.piv = 0.5;
    if (k < 0.18) { L.sy = 1 - 0.16 * (k / 0.18); L.sx = 1 + 0.08 * (k / 0.18); return; }
    if (k < 0.82) { this.once(a, 'j', () => Audio2.play('saut', 0.5)); const q = (k - 0.18) / 0.64; L.hop = Math.sin(q * Math.PI) * 84; L.rot = -TAU * totEase.io(q) * (L.flip ? -1 : 1); L.sy = 1 + 0.06 * Math.sin(q * Math.PI); return; }
    this.once(a, 'l', () => { this.stars(A, 6); Audio2.play('stars', 0.45); });
    const q = (k - 0.82) / 0.18; L.piv = 0; L.sy = 1 - 0.18 * (1 - q); L.sx = 1 + 0.1 * (1 - q);
  } },
  // puffs up like a balloon... then deflates
  puff: { dur: 2.3, init() { Audio2.play('blop_up', 0.6, 0.55); }, fn(a, k, dt, A) {
    const L = this.L; L.anim = 'staticF';
    if (k < 0.55) { const s = 1 + 0.5 * totEase.out(k / 0.55) + Math.sin(a.t * 40) * 0.015 * k; L.sx = s; L.sy = s; return; }
    if (k < 0.74) {
      this.once(a, 'p', () => { Audio2.play('dodge_604', 0.5, 0.7); this.float(A, 'Pfffffff !', '#e8f6ff', 0, -1.05); });
      const q = (k - 0.55) / 0.19, s = lerp(1.5, 0.82, q); L.sx = s; L.sy = s; L.rot = Math.sin(a.t * 50) * 0.28 * (1 - q); L.dx = Math.sin(a.t * 37) * 8; L.hop = Math.sin(q * Math.PI) * 30; L.piv = 0.5;
      this.every(a, 'm', 0.04, () => this.smoke(A, 1)); return;
    }
    const q = (k - 0.74) / 0.26, s = lerp(0.82, 1, totEase.back(q)); L.sx = s; L.sy = s;
  } },
  // a little dance
  dance: { dur: 2.6, fn(a, k, dt, A) {
    const L = this.L, b = a.t * Math.PI * 3; L.anim = 'staticR';
    L.flip = Math.floor(a.t / 0.333) % 2 === 1; L.rot = Math.sin(b) * 0.15; L.hop = Math.abs(Math.sin(b)) * 12; L.sx = 1 + Math.abs(Math.sin(b)) * 0.04;
    this.every(a, 'n', 0.33, () => this.note(A));
  } },
  // runs off the right edge and comes back from the left, as if around the world
  zoom: { dur: 2.3, init() { Audio2.play('dodge_604', 0.5); }, fn(a, k, dt, A) {
    const L = this.L; L.anim = 'runS'; L.flip = false;
    if (k < 0.42) { L.x = lerp(a.x0, 1.25, totEase.in(k / 0.42)); this.dust(a, dt, A); }
    else if (k < 0.58) { L.x = -0.3; this.once(a, 'b', () => Audio2.play('dodge_604', 0.5, 0.9)); }
    else { L.x = lerp(-0.25, a.x0, totEase.out((k - 0.58) / 0.42)); this.dust(a, dt, A); }
    L.hop = Math.abs(Math.sin(a.t * 14)) * 3;
  } },
  // shrinks to a tiny lion and scurries around squeaking
  tiny: { dur: 2.4, init() { Audio2.play('blop_up', 0.6, 1.8); }, fn(a, k, dt, A) {
    const L = this.L;
    if (k < 0.14) { const s = lerp(1, 0.32, totEase.out(k / 0.14)); L.sx = s; L.sy = s; L.anim = 'staticF'; return; }
    if (k < 0.86) {
      const an = (k - 0.14) / 0.72 * TAU * 2; L.sx = L.sy = 0.32; L.anim = 'runS'; L.dx = Math.sin(an) * 34 * A.rk; L.dy = -(1 - Math.cos(an)) * 8; L.flip = Math.cos(an) < 0;
      this.every(a, 'q', 0.55, () => { this.float(A, pick(['hihi !', 'iiih !', 'hop !']), '#fff6c8', 0, -0.55, 0.7); Audio2.play('blop_up', 0.3, 2.2); });
      return;
    }
    this.once(a, 'p', () => { this.smoke(A, 14); Audio2.play('pok', 0.6); });
    const q = (k - 0.86) / 0.14, s = lerp(0.32, 1, totEase.back(q)); L.sx = s; L.sy = s; L.anim = 'staticF';
  } },
  // laughs at you (wrong answer)
  laugh: { dur: 1.5, fn(a, k, dt, A) {
    const L = this.L; L.anim = 'staticF'; L.dx = Math.sin(a.t * 55) * 2.2; L.sy = 1 + Math.sin(a.t * 28) * 0.035; L.hop = Math.abs(Math.sin(a.t * 14)) * 5;
    this.every(a, 'h', 0.36, () => { const out = this.L.x < A.cx - 0.05 ? -1 : this.L.x > A.cx + 0.05 ? 1 : (a.s.side = -(a.s.side || 1)); this.float(A, pick(['HA !', 'HA HA !', 'HO HO !', 'HIHIHI !']), '#ffe066', out * rand(0.05, 0.3), -1.0, 1); });
  } },
  // takes a hit (right answer)
  hurt: { dur: 1.0, init() { this.L.flash = 1; this.dizzy = 1.6; }, fn(a, k, dt, A) {
    const L = this.L, dir = A.px > L.x * A.W ? -1 : 1; L.anim = 'staticR';
    L.dx = dir * 26 * Math.sin(Math.min(1, k * 1.6) * Math.PI / 2) * (1 - k * 0.7); L.hop = Math.sin(Math.min(1, k * 2.2) * Math.PI) * 16; L.rot = dir * 0.3 * Math.sin(k * Math.PI); L.piv = 0.5;
  } },
  // knocked out (you won)
  fall: { dur: 3.4, init() { this.L.flash = 1; this.dizzy = 4; }, fn(a, k, dt, A) {
    const L = this.L, dir = A.px > L.x * A.W ? -1 : 1; L.anim = 'staticR';
    if (k < 0.25) { L.rot = Math.sin(a.t * 18) * 0.12; L.dx = Math.sin(a.t * 9) * 4; return; }
    this.once(a, 'f', () => Audio2.play('saut', 0.5, 0.8));
    const q = Math.min(1, (k - 0.25) / 0.3); L.rot = dir * Math.PI / 2 * totEase.bounce(q); L.dx = dir * 10 * q;
    if (q >= 1) this.once(a, 'l', () => { this.smoke(A, 10); Audio2.play('pok', 0.5, 0.8); });
  } },
  // small fidgets while you think
  hop: { dur: 0.42, fn(a, k) { this.L.hop = Math.sin(k * Math.PI) * 12; this.L.sy = 1 + Math.sin(k * Math.PI) * 0.04; } },
  look: { dur: 0.9, fn(a, k) { const L = this.L; L.anim = k < 0.25 || k > 0.75 ? 'staticF' : 'staticB'; } },
  wiggle: { dur: 0.8, fn(a, k) { this.L.rot = Math.sin(k * TAU * 3) * 0.08 * (1 - k); } },
};
const TOT_ANTICS = ['lap', 'moonwalk', 'spin', 'bounce', 'backflip', 'puff', 'dance', 'zoom', 'tiny'];

const Tot = {
  active: false,
  async start(run, done) {
    Object.assign(this, { run, done, active: true, t: 0, lives: 3, totHp: 3, round: 0, hintUsed: false, fx: [], texts: [], parts: [], timers: [], busy: true, ended: false, phase: 'load', act: null, playerAnim: null, playerT: 0, hitMe: 0, card: null, phaseSkip: null, dizzy: 0, fidT: 3, bubbleT: 0, q: null, antics: [], lines: [] });
    this.pool = shuffle(Game.C.quiz.slice());
    this.player = run.charSprite;
    this.L = { x: 1.2, dx: 0, dy: 0, hop: 0, sx: 1, sy: 1, rot: 0, piv: 0, alpha: 1, flip: true, anim: 'runS', at: 0, flash: 0 };
    Audio2.playMusic('tot', 1.0);
    UI.clear();
    const key = Game.C.totSprite || '1010_tot';
    this.reward = null; this.rays = 0; this.drago = null; this.bonusIcon = null;
    const loads = [MobSheets.load(key), MobSheets.load(Game.C.bosses.bouftou_royal.sprite), MobSheets.load(Game.C.monsters.tofu.sprite), Audio2.preload(['jump', 'saut', 'dodge_604', 'stars', 'blop_up', 'pok', 'Critical_Hit']).catch(() => { })];
    if (Game.C.drago) loads.push(MobSheets.load(Game.C.drago.sprite));
    loads.push(Assets.loadImg('assets/ui/tot_bg.webp').then(b => { this.bgImg = b; }));   // 0.41: the Astrub zaap, HD (build_totbg41)
    for (const k in QUIZ_FX) if (QUIZ_FX[k]) loads.push(FxSheets.load(QUIZ_FX[k]));
    await Promise.all(loads);
    this.sheet = MobSheets.c[key];
    this.bg = this.bgImg ? null : this.makeBg(); this.vp = [];
    this.buildUI();
    this.onKey = (e) => this.key(e); this.onTap = (e) => this.tap(e);
    window.addEventListener('keydown', this.onKey); window.addEventListener('pointerdown', this.onTap);
    this.phase = 'intro';
    this.play('enter', () => { this.say(T('tot_intro'), 3.6); this.skippable(3.6, () => { this.hideBubble(); this.question(); }); if (Game.debug.bot) this.skip(true); });
  },
  // ---------------------------------------------------------------- layout (canvas px): stage, lion size, spots
  lay() {
    const W = Game.cw, H = Game.ch, d = Game.dpr || 1, vw = W / d, vh = H / d, port = vw / vh < 1.05;
    let LH, gy, cx, qx, px;
    if (port) { LH = Math.min(0.27 * H, 0.5 * W); gy = 0.43 * H; cx = 0.5 * W; qx = 0.64 * W; px = 0.2 * W; }
    else {
      const z = Game._uiz || 1, cardW = (vh <= 520 ? Math.min(640 * z, 0.64 * vw) : Math.min(520 * z, 0.58 * vw)) * d, margin = (W - cardW) / 2;   // the card is scaled with the menus
      LH = Math.max(60 * d, Math.min(0.46 * H, (margin - 14 * d) / 0.62, TOT_LH * 5.6)); gy = 0.84 * H; cx = 0.5 * W; qx = margin / 2; px = W - margin / 2;
    }
    const k = LH / TOT_LH;
    return { W, H, d, k, gy, cx: cx / W, qx: qx / W, px, port, rk: Math.min(1, W * 0.4 / (72 * k)), u: d * (vh <= 520 ? 0.85 : 1) * (Game._uiz || 1) };
  },
  makeBg() {
    const R = this.run, Tw = R.world.tile;
    const c = document.createElement('canvas'); c.width = 900; c.height = 560;
    const g = c.getContext('2d');
    const cx = R.center.x - 450, cy = R.center.y - 280;
    for (const k in R.tiles) {
      const [tx, ty] = k.split(',').map(Number); const im = R.tiles[k];
      g.drawImage(im, tx * Tw - cx, ty * Tw - cy, im.width / (R.world.res || 1), im.height / (R.world.res || 1));
    }
    g.fillStyle = 'rgba(16,8,28,0.5)'; g.fillRect(0, 0, 900, 560);
    const v = g.createRadialGradient(450, 330, 120, 450, 300, 560); v.addColorStop(0, 'rgba(0,0,0,0)'); v.addColorStop(1, 'rgba(0,0,0,0.75)');
    g.fillStyle = v; g.fillRect(0, 0, 900, 560);
    return c;
  },
  buildUI() {
    this.meH = h('div', { class: 'hearts' }); this.totH = h('div', { class: 'hearts' });
    this.topQ = h('div', { class: 'qn' }, T('tot_gm'));
    this.bubbleEl = h('div', { class: 'tot-bubble' });
    this.skipEl = h('div', { class: 'tot-skip' }, '⏩');
    this.root = h('div', { class: 'screen tot' + (this.lay().port ? ' portrait' : '') },
      h('div', { class: 'tot-top' },
        h('div', { class: 'tot-side me' }, h('b', {}, T('you')), this.meH),
        h('div', { class: 'tot-mid' }, h('div', { class: 'gm' }, 'ToT'), this.topQ),
        h('div', { class: 'tot-side tot' }, this.totH, h('b', {}, 'ToT'))),
      this.bubbleEl, this.skipEl);
    UI.rootEl.append(this.root);
    this.renderHearts();
  },
  renderHearts(lost) {
    const mk = (n, icon, who) => Array.from({ length: 3 }, (_, i) => { const im = iconImg(icon, 22, i < n ? '' : 'lost'); if (lost === who && i === n) im.classList.add('pop'); return im; });
    this.meH.replaceChildren(...mk(this.lives, 'Heart', 'me'));
    this.totH.replaceChildren(...mk(this.totHp, 'Coeur', 'tot'));
  },
  // ---------------------------------------------------------------- flow
  question() {
    if (this.ended) return;
    if (this.totHp <= 0) return this.finish(true);
    if (this.lives <= 0) return this.finish(false);
    this.phase = 'move';
    this.moveTo(this.lay().qx, () => { this.phase = 'question'; this.fidT = rand(2, 3.5); this.showCard(); });
  },
  showCard() {
    if (!this.pool.length) this.pool = shuffle(Game.C.quiz.slice());
    const q = this.q = this.pool.shift(); this.round++;
    const C = Game.C, ids = this.ids = shuffle([q.ok, ...q.wrong.slice(0, 2)]);
    this.hintEl = h('div', { class: 'tot-hinttxt' }); this.sayEl = h('div', { class: 'tot-say' });
    const foot = h('div', { class: 'tot-foot' }, this.hintEl, this.sayEl);
    this.hintBtn = null;
    if (!this.hintUsed) { this.hintBtn = h('button', { class: 'tot-hint', onclick: (e) => { e.stopPropagation(); this.hint(); } }, '💡 ' + T('hint')); foot.prepend(this.hintBtn); }
    this.btns = ids.map((id, i) => h('button', { class: 'tot-spell', onclick: (e) => { e.stopPropagation(); this.choose(id); } },
      h('span', { class: 'key' }, String(i + 1)), iconImg('sp_' + ((C.quizIcon || {})[id] || id), 40), h('span', { class: 'nm' }, L(C.quizSpells[id]) || ('#' + id))));
    this.card = h('div', { class: 'tot-card' },
      h('div', { class: 'qtag' }, T('tot_q', { n: this.round })),
      h('div', { class: 'qtext' }, L(q.tot)),
      h('div', { class: 'qpick' }, T('tot_pick')),
      h('div', { class: 'tot-answers' }, ...this.btns), foot);
    this.root.append(this.card);
    this.topQ.textContent = T('tot_q', { n: this.round });
    Audio2.ui('turn', 0.8);
    this.busy = false;
    if (Game.debug.bot) this.after(0.4, () => this.choose(Math.random() < 0.7 ? q.ok : pick(q.wrong)));
  },
  hint() {
    if (this.hintUsed || this.busy || !this.q) return;
    this.hintUsed = true; this.hintEl.textContent = '💡 ' + L(this.q.hint);
    if (this.hintBtn) this.hintBtn.remove(); this.hintBtn = null; Audio2.blip('click');
    this.play('wiggle');
  },
  choose(id) {
    if (this.busy || this.ended || !this.q) return; this.busy = true;
    const q = this.q, C = Game.C, ok = id === q.ok;
    this.btns.forEach((b, i) => { b.disabled = true; b.classList.add(this.ids[i] === q.ok ? 'ok' : this.ids[i] === id ? 'ko' : 'dim'); });
    if (this.hintBtn) { this.hintBtn.remove(); this.hintBtn = null; }
    this.phase = 'answer';
    this.stamp(ok ? T('tot_good') : T('tot_bad'), ok ? 'good' : 'bad');
    // the player casts the chosen spell at the lion
    const ca = (this.run.cls.casts[0] || 'anim1') + 'R';
    this.playerAnim = this.player.has(ca) ? ca : null; this.playerT = 0;
    const fxId = QUIZ_FX[id];
    { const k = (Audio2.SND.fx[fxId] || [])[0] || (Audio2.charSnd(this.run.charSid, ca) || [])[0]; if (k) Audio2.play(k, 0.7); }
    this.after(0.4, () => {
      if (fxId && FxSheets.get(fxId)) this.fx.push({ sh: FxSheets.get(fxId), t: 0, at: id === 434 || id === 20 || id === 4 ? 'me' : 'tot' });
      else this.fx.push({ ring: true, t: 0, at: 'tot' });
      if (ok) {
        this.totHp--; Audio2.blip('right'); Audio2.sfx('Critical_Hit', 0.6);
        this.texts.push({ s: '-' + randi(180, 420), c: '#ff4d3d', at: 'tot', t: 0 });
        this.play('hurt');
        this.quote(L(pick(C.totWinLines || [])));
      } else {
        this.lives--; Audio2.blip('wrong');
        this.texts.push({ s: T('no_effect'), c: '#cccccc', at: 'tot', t: 0 });
        this.after(0.45, () => { this.texts.push({ s: '-' + randi(60, 140), c: '#ff4d3d', at: 'me', t: 0 }); this.hitMe = 0.5; const k = Audio2.charSnd(this.run.charSid, 'hitR'); Audio2.play(k ? k[0] : 'hit_defaut', 0.7); });
        this.play('laugh');
        this.quote(L(pick(C.totLoseLines || [])));
        this.hintEl.textContent = '💡 ' + L(q.hint);
      }
      this.renderHearts(ok ? 'tot' : 'me');
      this.after(ok ? 1.6 : 2.5, () => this.interlude());
    });
  },
  quote(s) { if (this.sayEl && s) this.sayEl.replaceChildren(h('b', {}, 'ToT : '), '« ' + s + ' »'); },
  interlude() {
    this.closeCard();
    if (this.totHp <= 0 || this.lives <= 0) { this.after(0.3, () => this.finish(this.totHp <= 0)); return; }
    this.phase = 'interlude';
    this.moveTo(this.lay().cx, () => {
      const name = this.nextAntic(), dur = this.play(name), own = (Game.C.totActLines || {})[name];
      this.say(L(own && Math.random() < 0.7 ? own : this.nextLine()), dur + 0.3);
      this.skippable(dur + 0.4, () => { this.hideBubble(); this.question(); });
      if (Game.debug.bot) this.skip(true);
    });
  },
  nextAntic() { if (!this.antics.length) { this.antics = shuffle(TOT_ANTICS.slice()); if (this.antics[0] === this.lastAntic) this.antics.push(this.antics.shift()); } return (this.lastAntic = this.antics.shift()); },
  nextLine() { if (!this.lines.length) this.lines = shuffle((Game.C.totLines || []).slice()); return this.lines.shift() || ''; },
  // the reward: his Dofus only for a flawless 3-0 (and only once); otherwise a bonus for the run, or (2%) an armoured Dragodinde
  finish(won) {
    if (this.ended) return; this.ended = true; this.phase = 'end'; this.closeCard(); this.phaseSkip = null;
    const C = Game.C, owned = this.run.dofus.some(d => d.id === 'ocre'), perfect = this.lives === 3;
    const rw = !won ? null : perfect && !owned ? { kind: 'dofus' } : Math.random() < (Game.debug.drago ? 1 : (C.dragoChance || 0.02)) ? { kind: 'drago' } : { buff: pick(C.totBuffs || [{ id: 'degats', stat: 'might', v: 0.1, icon: 'Icon_33', name: 'Dégâts' }]) };
    this.reward = rw;
    const bot = Game.debug.bot;
    this.moveTo(this.lay().cx, () => {
      if (!won) { this.play('dance', null, 3.4); this.say(T('tot_lose'), 3); this.confetti(50, ['#c58aff', '#ffd27a', '#ff6a3d']); this.after(bot ? 0.6 : 3.1, () => this.close(won)); return; }
      Audio2.sfx('EVENT', 0.9);
      if (rw.kind === 'drago') { // very lucky: golden rays, rainbow confetti, the Dragodinde runs in
        this.play('bounce', () => this.play('spin'), 2.0); this.stamp(T('tot_rare'), 'rare', 3.6); this.say(T('tot_drago', { n: L(C.drago.name) }), 4.2);
        this.rays = 0.01; this.drago = { t: 0 }; this.confetti(170, FW_COLS); this.after(1.2, () => this.confetti(120, FW_COLS)); this.after(2.4, () => this.confetti(120, FW_COLS));
        Audio2.ui('level', 0.9); this.after(0.6, () => Audio2.play('stars', 0.7)); this.after(1.6, () => Audio2.play('stars', 0.7, 1.2));
        this.after(bot ? 0.8 : 4.8, () => this.close(won)); return;
      }
      this.play('fall'); this.stamp(T('victory'), 'win', 2.6); this.confetti(110);
      if (rw.kind === 'dofus') this.say(T('tot_win'), 3);
      else { this.say((!perfect && !owned ? T('tot_noperfect') + ' ' : '') + T('tot_buff', { b: L(rw.buff.name) }), 3.4); this.bonusIcon = rw.buff.icon; }
      this.after(bot ? 0.6 : 3.4, () => this.close(won));
    });
  },
  close(won) {
    window.removeEventListener('keydown', this.onKey); window.removeEventListener('pointerdown', this.onTap);
    this.active = false; this.timers = []; UI.clear();
    this.done(won, this.reward);
  },
  // ---------------------------------------------------------------- helpers: timers, skipping, DOM bits
  after(sec, cb) { const tm = { t: sec, cb }; this.timers.push(tm); return tm; },
  skippable(sec, cb) { this.phaseSkip = { tm: this.after(sec, () => { this.phaseSkip = null; cb(); }), cb, t0: this.t }; },
  skip(force) {
    const s = this.phaseSkip; if (!s || (!force && this.t - s.t0 < 0.35)) return;
    this.phaseSkip = null; s.tm.dead = true;
    if (this.act) { this.act = null; this.pose(); }
    s.cb();
  },
  key(e) {
    if (!this.active) return;
    if (this.phase === 'question' && !this.busy) {
      const i = ['Digit1', 'Digit2', 'Digit3'].indexOf(e.code), j = ['Numpad1', 'Numpad2', 'Numpad3'].indexOf(e.code);
      if (i >= 0 || j >= 0) { e.preventDefault(); this.choose(this.ids[Math.max(i, j)]); return; }
      if (e.code === 'KeyH') { this.hint(); return; }
    }
    if ((e.code === 'Space' || e.code === 'Enter' || e.code === 'NumpadEnter') && this.phaseSkip) { e.preventDefault(); this.skip(); }
  },
  tap(e) { if (!this.active || !this.phaseSkip) return; if (e.target && e.target.closest && e.target.closest('button')) return; this.skip(); },
  stamp(txt, cls, life = 1.3) {
    if (this.stampEl) this.stampEl.remove();
    const el = this.stampEl = h('div', { class: 'tot-stamp ' + cls }, txt); this.root.append(el);
    this.after(life, () => el.classList.add('fade')); this.after(life + 0.4, () => el.remove());
  },
  closeCard() { const c = this.card; if (!c) return; this.card = null; c.classList.add('out'); this.after(0.3, () => c.remove()); },
  say(txt, dur) { if (!txt) return; this.bubbleEl.textContent = txt; this.bubbleEl.classList.add('show'); this.bubbleT = dur; this._bp = null; },
  hideBubble() { this.bubbleT = 0; this.bubbleEl.classList.remove('show'); },
  placeBubble(A) {
    const el = this.bubbleEl, L = this.L, d = A.d * (Game._uiz || 1);   // the DOM layer is zoomed with the menus
    // anchored on the standing lion (not its jumps) so the bubble stays put during the antics
    const x = (L.x * A.W + clamp(L.dx, -30, 30) * A.k) / d, foot = A.gy / d, head = foot - TOT_LH * A.k / d;
    const bw = el.offsetWidth, bh = el.offsetHeight, vw = A.W / d, vh = A.H / d;
    const left = clamp(x - bw / 2, 8, Math.max(8, vw - bw - 8)); let top = head - bh - 16, below = false;
    if (top < 54) { top = Math.min(foot + 16, vh - bh - 8); below = true; }
    const key = Math.round(left) + '|' + Math.round(top) + '|' + below;
    if (key === this._bp) return; this._bp = key;
    el.classList.toggle('below', below); el.style.left = left + 'px'; el.style.top = top + 'px';
    el.style.setProperty('--tail', clamp(x - left, 20, bw - 20) + 'px'); el.style.transformOrigin = clamp(x - left, 20, bw - 20) + 'px ' + (below ? '0' : '100%');
  },
  // ---------------------------------------------------------------- the lion's moves
  play(name, cb, dur) {
    const D = TOT_ACTS[name]; if (!D) { if (cb) cb(); return 0; }
    this.pose();
    const a = { name, t: 0, dur: dur || D.dur, fn: D.fn, cb, x0: this.L.x, s: {} };
    this.act = a; if (D.init) D.init.call(this, a);
    return a.dur;
  },
  moveTo(xf, cb) {
    const L = this.L, x0 = L.x, dd = Math.abs(xf - x0);
    if (dd < 0.01) { this.act = null; this.pose(); if (cb) cb(); return; }
    this.pose();
    this.act = { name: 'move', t: 0, dur: clamp(dd * 1.5, 0.3, 0.8), cb, s: {}, fn(a, k, dt, A) { L.anim = 'runS'; L.flip = xf < x0; L.x = lerp(x0, xf, totEase.io(k)); L.hop = Math.abs(Math.sin(k * Math.PI * 3)) * 4; Tot.dust(a, dt, A); } };
  },
  pose() {
    const L = this.L; Object.assign(L, { dx: 0, dy: 0, hop: 0, sx: 1, sy: 1, rot: 0, piv: 0, alpha: 1, anim: 'staticR' });
    const A = this.lay(), x = L.x * A.W;
    L.flip = Math.abs(L.x - A.cx) < 0.02 ? A.px < x : x > A.W / 2; // face the card, or the player when centre stage
  },
  once(a, k, f) { if (!a.s[k]) { a.s[k] = 1; f(); } },
  every(a, k, iv, f) { if (a.t >= (a.s[k] || 0)) { a.s[k] = a.t + iv; f(); } },
  lionXY(A) { const L = this.L; return [L.x * A.W + L.dx * A.k, A.gy + L.dy * A.k]; },
  dust(a, dt, A) { a.s.d = (a.s.d || 0) - dt; if (a.s.d > 0) return; a.s.d = 0.06; const [x, y] = this.lionXY(A); this.parts.push({ x: x + rand(-8, 8) * A.k, y: y - rand(0, 3) * A.k, vx: rand(-20, 20) * A.k, vy: -rand(5, 18) * A.k, g: 0, t: 0, life: 0.5, r: rand(2, 4) * A.k, c: 'rgba(220,200,160,0.5)' }); },
  smoke(A, n) { const [x, y] = this.lionXY(A); for (let i = 0; i < n; i++) this.parts.push({ x: x + rand(-14, 14) * A.k, y: y - rand(10, 50) * A.k * this.L.sy, vx: rand(-30, 30) * A.k, vy: -rand(5, 25) * A.k, g: 0, t: 0, life: rand(0.5, 0.9), r: rand(4, 8) * A.k, c: 'rgba(235,235,245,0.55)' }); },
  stars(A, n) { const [x, y] = this.lionXY(A); for (let i = 0; i < n; i++) { const an = rand(TAU); this.parts.push({ x, y: y - TOT_LH * 0.5 * A.k, vx: Math.cos(an) * rand(40, 90) * A.k, vy: Math.sin(an) * rand(30, 70) * A.k - 20 * A.k, g: 60 * A.k, t: 0, life: 0.8, txt: '✦', size: rand(14, 22) * A.u, c: pick(['#ffe066', '#fff6c8', '#ffd27a']) }); } },
  note(A) { const [x, y] = this.lionXY(A); this.parts.push({ x: x + rand(-20, 20) * A.k, y: y - (TOT_LH + 6) * A.k, vx: rand(-12, 12) * A.k, vy: -28 * A.k, g: 0, t: 0, life: 1.2, txt: pick(['♪', '♫', '♪']), size: rand(18, 26) * A.u, c: pick(['#ffe066', '#7fd0ff', '#ff9ad5', '#9cff9a']), wob: rand(TAU) }); },
  float(A, s, c, side, hk, sz = 1) { const [x, y] = this.lionXY(A); this.parts.push({ x: x + side * TOT_LH * A.k, y: y + hk * TOT_LH * A.k * Math.max(0.35, this.L.sy) - this.L.hop * A.k, vx: side * 20 * A.k, vy: -30 * A.k, g: 0, t: 0, life: 0.9, txt: s, size: 22 * A.u * sz, c }); },
  confetti(n, cols) { const A = this.lay(); cols = cols || ['#ff5fb0', '#ffe066', '#7dff9a', '#7fd0ff', '#ffffff', '#c58aff']; for (let i = 0; i < n; i++) this.parts.push({ x: rand(A.W), y: -rand(0, A.H * 0.4), vx: rand(-40, 40) * A.d, vy: rand(60, 160) * A.d, g: 40 * A.d, t: 0, life: rand(2.2, 3.4), conf: 1, w: rand(5, 9) * A.d, hh: rand(3, 5) * A.d, rot: rand(TAU), vr: rand(-8, 8), c: pick(cols) }); },
  idle(dt) {
    const L = this.L; L.sy = 1 + Math.sin(this.t * 2.4) * 0.012; L.sx = 1 - Math.sin(this.t * 2.4) * 0.006;
    if (this.phase === 'question' && !this.busy) { this.fidT -= dt; if (this.fidT <= 0) { this.fidT = rand(2.5, 4.5); this.play(pick(['hop', 'look', 'wiggle', 'hop'])); } }
  },
  // ---------------------------------------------------------------- frame
  update(dt) {
    this.t += dt;
    const L = this.L; L.at += dt * (this.q && this.q.id === 'slow' && this.phase === 'question' ? 0.35 : 1); if (L.flash > 0) L.flash -= dt * 2.5; if (this.dizzy > 0) this.dizzy -= dt;
    // timers (callbacks may add new ones)
    const due = []; for (const tm of this.timers) { if (tm.dead) continue; tm.t -= dt; if (tm.t <= 0) { tm.dead = true; due.push(tm); } }
    this.timers = this.timers.filter(tm => !tm.dead); for (const tm of due) tm.cb();
    const A = this.lay(), a = this.act;
    if (a) { a.t += dt; const k = Math.min(1, a.t / a.dur); a.fn.call(this, a, k, dt, A); if (a.t >= a.dur && this.act === a) { this.act = null; this.pose(); if (a.cb) a.cb(); } }
    else this.idle(dt);
    if (this.playerAnim && (this.playerT += dt) > 1.2) this.playerAnim = null;
    if (this.hitMe > 0) this.hitMe -= dt;
    for (const f of this.fx) f.t += dt; this.fx = this.fx.filter(f => f.t < (f.sh ? f.sh.duration(Object.keys(f.sh.anims)[0]) : 0.6));
    for (const x of this.texts) x.t += dt; this.texts = this.texts.filter(x => x.t < 1.2);
    let j = 0; for (const p of this.parts) { p.t += dt; if (p.t > p.life) continue; p.vy += (p.g || 0) * dt; p.x += p.vx * dt; p.y += p.vy * dt; if (p.vr) p.rot += p.vr * dt; this.parts[j++] = p; } this.parts.length = j;
    if (this.bubbleT > 0) { this.bubbleT -= dt; if (this.bubbleT <= 0) this.hideBubble(); }
    // controller: A skips the interlude
    const pads = navigator.getGamepads ? [...navigator.getGamepads()].filter(Boolean) : [];
    const pa = !!(pads[0] && pads[0].buttons[0] && pads[0].buttons[0].pressed); if (pa && !this._pa && this.phaseSkip) this.skip(); this._pa = pa;
  },
  draw(ctx) {
    const A = this.lay(), W = A.W, H = A.H, k = A.k, t = this.t, L = this.L;
    ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1;
    ctx.fillStyle = '#0c0a12'; ctx.fillRect(0, 0, W, H);
    ctx.imageSmoothingEnabled = true; ctx.imageSmoothingQuality = 'high';
    if (this.bgImg) this.drawPortal(ctx, A, t);
    else if (this.bg) { const s = Math.max(W / this.bg.width, H / this.bg.height); ctx.drawImage(this.bg, (W - this.bg.width * s) / 2, (H - this.bg.height * s) / 2, this.bg.width * s, this.bg.height * s); }
    const [lx, ly] = this.lionXY(A);
    // stage lights under the lion and the player
    ctx.drawImage(RCache.glow('rgba(255,215,140,0.32)'), lx - 95 * k, ly - 34 * k, 190 * k, 68 * k);
    ctx.drawImage(RCache.glow('rgba(140,190,255,0.22)'), A.px - 60 * k, A.gy - 22 * k, 120 * k, 44 * k);
    const q = this.q, scene = q && (this.phase === 'question' || this.phase === 'answer') && this.totHp > 0 ? q.id : null;
    // very rare reward: golden rays turning behind the lion
    if (this.rays) { this.rays = Math.min(1, this.rays + 0.02); ctx.save(); ctx.translate(lx, ly - TOT_LH * 0.5 * k); ctx.rotate(t * 0.5); ctx.globalAlpha = 0.28 * this.rays; ctx.fillStyle = '#ffd24a';
      for (let i = 0; i < 12; i++) { ctx.rotate(TAU / 12); ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(-22 * k, -260 * k); ctx.lineTo(22 * k, -260 * k); ctx.closePath(); ctx.fill(); } ctx.restore(); ctx.globalAlpha = 1; }
    if (scene === 'fire') { ctx.save(); ctx.translate(lx, ly); ctx.scale(k, k); drawGlyph(ctx, 0, 0, 44, '#ff7a1a', 0.9, t); ctx.restore(); }
    if (scene === 'gap') { ctx.fillStyle = 'rgba(8,4,14,0.9)'; const gx = (lx + A.px) / 2; ctx.beginPath(); ctx.ellipse(gx, A.gy + 4 * k, 34 * k, 13 * k, 0, 0, TAU); ctx.fill(); ctx.strokeStyle = 'rgba(120,90,60,0.9)'; ctx.lineWidth = 3 * A.d; ctx.stroke(); }
    if (scene === 'double') { ctx.strokeStyle = '#b388ff'; ctx.lineWidth = 2.5 * A.d; for (let i = 0; i < 8; i++) { const an = i / 8 * TAU; const x = A.px + Math.cos(an) * 34 * k * A.rk, y = A.gy + Math.sin(an) * 12 * k; ctx.fillStyle = '#2a1840'; ctx.beginPath(); ctx.ellipse(x, y, 8 * k, 4 * k, 0, 0, TAU); ctx.fill(); ctx.stroke(); } }
    // shadows
    ctx.fillStyle = 'rgba(0,0,0,0.35)'; ctx.beginPath(); ctx.ellipse(A.px, A.gy, 20 * k, 6 * k, 0, 0, TAU); ctx.fill();
    { const sh = clamp(1 - L.hop / 140, 0.35, 1); ctx.globalAlpha = sh; ctx.beginPath(); ctx.ellipse(lx + (Math.abs(L.rot) > 1 ? Math.sign(L.rot) * 30 * k : 0), ly, 26 * k * L.sx * (Math.abs(L.rot) > 1 ? 1.9 : 1), 7.5 * k, 0, 0, TAU); ctx.fill(); ctx.globalAlpha = 1; }
    // 0.61: the monsters turning around the player (and around the lion) are drawn in depth order with it — the
    // ones behind pass behind — on a rounder, wider ring, so they keep even gaps and no longer pile on the character
    const RINGS = { hide: [Game.C.bosses.bouftou_royal.sprite, 5, 0.5, 46, 18, 0.34, an => Math.cos(an) > 0], tofus: [Game.C.monsters.tofu.sprite, 7, 1.2, 44, 17, 0.9, an => Math.sin(an) > 0] };
    const ring = (cx, cy, R_, back) => { const [key, n, sp, rx, ry, sc, fl] = R_, sh = MobSheets.c[key]; if (!sh) return;
      const list = []; for (let i = 0; i < n; i++) { const an = i / n * TAU + t * sp; if ((Math.sin(an) < 0) === back) list.push([an, i]); }
      list.sort((a, b) => Math.sin(a[0]) - Math.sin(b[0]));
      for (const [an, i] of list) sh.draw(ctx, sh.frameAt('walkR', t + i, true), cx + Math.cos(an) * rx * k * A.rk, cy + Math.sin(an) * ry * k, k * sc, fl(an)); };
    if (RINGS[scene]) ring(A.px, A.gy, RINGS[scene], true);
    // the player
    this.player.draw(ctx, this.playerAnim || 'staticR', this.playerAnim ? this.playerT : t, A.px, A.gy, k * 0.95, A.px > lx, { loop: !this.playerAnim, flash: this.hitMe > 0 ? this.hitMe * 2 : 0 });
    if (scene === 'poison') { const r = (30 + Math.sin(t * 5) * 3) * k; ctx.drawImage(RCache.glow('rgba(120,230,80,0.55)'), A.px - r, A.gy - 30 * k - r, r * 2, r * 2); }
    if (RINGS[scene]) ring(A.px, A.gy, RINGS[scene], false);
    if (this.drago) { // the armoured Dragodinde runs in and stops next to the player
      const sh = MobSheets.c[Game.C.drago.sprite]; { const now = performance.now(); if (this.drago.t0 === undefined) this.drago.t0 = now - (this.drago.t || 0) * 1000; this.drago.t = (now - this.drago.t0) / 1000; }   // (real time, not 1/60 per drawn frame)
      if (sh) { const kk = Math.min(1, this.drago.t / 1.4), x = lerp(W * 1.1, A.px + (A.px > lx ? -1 : 1) * 62 * k, 1 - Math.pow(1 - kk, 2)), run = kk < 1;
        ctx.drawImage(RCache.glow('rgba(255,215,90,0.55)'), x - 40 * k, A.gy - 70 * k, 80 * k, 80 * k);
        const an = run && sh.has('runR') ? 'runR' : 'staticR'; sh.draw(ctx, sh.frameAt(an, this.drago.t, true), x, A.gy + 4 * k, k * 1.1, run ? true : A.px < lx); }
    }
    // the lion (and its friends, depending on the question)
    let la = 1, ls = 1, ldy = 0;
    if (scene === 'invis' && L.flash <= 0) la = 0.16;
    if (scene === 'far') { ls = 0.72; ldy = -14; }
    if (scene === 'fear') ls = 1.15 + Math.sin(t * 20) * 0.01;
    const CROWD = [Game.C.bosses.bouftou_royal.sprite, 5, 0.6, 50, 18, 0.36, an => Math.cos(an) > 0];
    if (scene === 'summon') { const sh = MobSheets.c[CROWD[0]]; if (sh) sh.draw(ctx, sh.frameAt('walkR', t, true), lx + Math.cos(0.6) * 40 * k * A.rk, ly + Math.sin(0.6) * 12 * k + 6 * k, k * 0.55, true); }
    if (scene === 'crowd') ring(lx, ly, CROWD, true);
    if (scene === 'armor' || scene === 'shield' || scene === 'reflect' || scene === 'ap' || scene === 'colere' || scene === 'heal') {
      const col = { armor: 'rgba(255,190,90,0.5)', shield: 'rgba(120,190,255,0.55)', reflect: 'rgba(200,170,255,0.55)', ap: 'rgba(90,170,255,0.6)', colere: 'rgba(255,70,50,0.55)', heal: 'rgba(120,255,150,0.45)' }[scene];
      const r = (46 + Math.sin(t * 4) * 3) * k * ls; ctx.drawImage(RCache.glow(col), lx - r, ly - TOT_LH * 0.55 * k * ls - r, r * 2, r * 2);
      if (scene === 'heal' && Math.random() < 0.2) this.parts.push({ x: lx + rand(-25, 25) * k, y: ly - rand(10, 60) * k, vx: 0, vy: -30 * k, g: 0, t: 0, life: 0.8, txt: '+', size: 20 * A.u, c: '#7dff9a' });
    }
    this.drawLion(ctx, A, lx, ly + ldy * k, la, ls);
    if (scene === 'crowd') ring(lx, ly, CROWD, false);
    if (this.bonusIcon) { // the run bonus floats above the player
      const bx = A.px, by = A.gy - (84 + Math.sin(t * 3) * 3) * k, s = 13 * k;
      ctx.drawImage(RCache.glow('rgba(224,176,255,0.7)'), bx - s, by - s, s * 2, s * 2); Game.icons.drawFit(ctx, this.bonusIcon, bx, by, s * 1.1);
      outlinedText(ctx, '+10%', bx, by + s * 0.95, '#e0b0ff', 16 * A.u, 'center');
    }
    // dizzy stars over his head
    if (this.dizzy > 0) {
      const hx = lx + (L.piv ? 0 : 0), hy = ly - (TOT_LH * L.sy * ls + L.hop + 4) * k, lying = Math.abs(L.rot) > 1;
      const cx2 = lying ? lx + Math.sign(L.rot) * TOT_LH * 0.85 * k : hx, cy2 = lying ? ly - 10 * k : hy;
      for (let i = 0; i < 4; i++) { const an = t * 5 + i / 4 * TAU; outlinedText(ctx, '✦', cx2 + Math.cos(an) * 16 * k, cy2 + Math.sin(an) * 5 * k, '#ffe066', 16 * A.u, 'center'); }
    }
    // a bobbing "?" while you think
    if (this.phase === 'question' && !this.busy && !this.act) outlinedText(ctx, '?', lx + 10 * k * (L.flip ? -1 : 1), ly - (TOT_LH + 12 + Math.abs(Math.sin(t * 3)) * 4) * k * ls, '#ffd27a', 30 * A.u, 'center');
    // spell effects and floating numbers
    for (const f of this.fx) {
      const x = f.at === 'me' ? A.px : lx, y = f.at === 'me' ? A.gy : ly;
      if (f.ring) { ctx.globalAlpha = 1 - f.t / 0.6; ctx.strokeStyle = '#fff'; ctx.lineWidth = 3 * A.d; ctx.beginPath(); ctx.ellipse(x, y - 30 * k, (10 + f.t * 90) * k / 2, (6 + f.t * 50) * k / 2, 0, 0, TAU); ctx.stroke(); ctx.globalAlpha = 1; continue; }
      const sym = f.sh.anims.shoot ? 'shoot' : Object.keys(f.sh.anims)[0];
      f.sh.draw(ctx, f.sh.frameAt(sym, f.t, false), x, y, k * 0.85, false);
    }
    for (const x of this.texts) {
      const px = x.at === 'me' ? A.px : lx, py = (x.at === 'me' ? A.gy - 70 * k : ly - (TOT_LH + 18) * k) - x.t * 22 * k;
      ctx.globalAlpha = 1 - Math.max(0, x.t - 0.8) / 0.4; outlinedText(ctx, x.s, px, py, x.c, 26 * A.u, 'center'); ctx.globalAlpha = 1;
    }
    // particles
    for (const p of this.parts) {
      const fade = Math.min(1, (p.life - p.t) / 0.3);
      if (p.conf) { ctx.globalAlpha = fade; ctx.save(); ctx.translate(p.x, p.y); ctx.rotate(p.rot); ctx.fillStyle = p.c; ctx.fillRect(-p.w / 2, -p.hh / 2, p.w, p.hh * Math.abs(Math.cos(p.rot * 1.7))); ctx.restore(); continue; }
      if (p.txt) { ctx.globalAlpha = fade; outlinedText(ctx, p.txt, p.x + (p.wob !== undefined ? Math.sin(p.t * 6 + p.wob) * 6 * A.d : 0), p.y, p.c, p.size, 'center'); continue; }
      ctx.globalAlpha = fade * 0.9; ctx.fillStyle = p.c; ctx.beginPath(); ctx.arc(p.x, p.y, p.r * (1 + p.t), 0, TAU); ctx.fill();
    }
    ctx.globalAlpha = 1; ctx.textAlign = 'left';
    // DOM bits that follow the stage
    if (this.root) { this.root.classList.toggle('portrait', A.port); this.skipEl.classList.toggle('show', !!this.phaseSkip); }
    if (this.bubbleT > 0) this.placeBubble(A);
  },
  // 0.41: the quiz takes place in a space-time portal over the Astrub zaap: the zaap's surroundings darkened,
  // a slow violet vortex, the zaap glowing, violet motes spiralling in, sparkles and time rifts
  drawPortal(ctx, A, t) {
    const W = A.W, H = A.H, im = this.bgImg, d = A.d, M = Math.min(W, H);
    const dt = clamp(t - (this._pt ?? t), 0, 0.05); this._pt = t;
    const s = Math.max(W / im.width, H / im.height), bx = (W - im.width * s) / 2, by = (H - im.height * s) / 2;
    const zx = bx + im.width * s * 0.5, zy = by + im.height * s * 0.227;   // the zaap in the picture
    const cx = W / 2, cy = H * 0.5;
    ctx.save();
    ctx.translate(cx, cy); const sw = 1.03 + Math.sin(t * 0.4) * 0.012; ctx.scale(sw, sw); ctx.translate(-cx, -cy);   // slow breathing
    ctx.drawImage(im, bx, by, im.width * s, im.height * s);
    ctx.restore();
    ctx.fillStyle = 'rgba(20,6,40,0.52)'; ctx.fillRect(0, 0, W, H);
    const vg = ctx.createRadialGradient(cx, cy, M * 0.25, cx, cy, Math.hypot(W, H) * 0.62);
    vg.addColorStop(0, 'rgba(40,10,70,0)'); vg.addColorStop(0.7, 'rgba(30,6,60,0.45)'); vg.addColorStop(1, 'rgba(8,0,20,0.92)');
    ctx.fillStyle = vg; ctx.fillRect(0, 0, W, H);
    const low = Game.lowFx;
    ctx.save(); ctx.globalCompositeOperation = 'lighter';
    // the vortex: spiral arms turning around the middle of the screen
    const R = Math.hypot(W, H) * 0.6, arms = 5;
    ctx.lineCap = 'round';
    for (let a = 0; a < arms; a++) {
      const a0 = t * 0.22 + a / arms * TAU;
      for (let w = 0; w < 2; w++) {
        ctx.beginPath();
        for (let i = 0; i <= 40; i++) { const u = i / 40, r = R * (0.08 + u * 0.95), an = a0 + u * 3.2 + w * 0.12; i ? ctx.lineTo(cx + Math.cos(an) * r, cy + Math.sin(an) * r * 0.62) : ctx.moveTo(cx + Math.cos(an) * r, cy + Math.sin(an) * r * 0.62); }
        ctx.strokeStyle = w ? 'rgba(120,60,255,0.05)' : 'rgba(200,110,255,0.07)'; ctx.lineWidth = (w ? 70 : 28) * d * (M / 900); ctx.stroke();
      }
    }
    // the zaap glows and pulses: the portal's way in
    const pz = 1 + Math.sin(t * 2.2) * 0.08, zr = M * 0.16 * pz;
    ctx.drawImage(RCache.glow('rgba(190,90,255,0.55)'), zx - zr, zy - zr * 0.8, zr * 2, zr * 1.6);
    ctx.drawImage(RCache.glow('rgba(120,230,255,0.35)'), zx - zr * 0.35, zy - zr * 0.35, zr * 0.7, zr * 0.7);
    for (let i = 0; i < 3; i++) { const u = (t * 0.45 + i / 3) % 1; ctx.globalAlpha = (1 - u) * 0.5; ctx.strokeStyle = '#d6a8ff'; ctx.lineWidth = 2.5 * d; ctx.beginPath(); ctx.ellipse(zx, zy, zr * 0.25 + u * zr * 1.2, (zr * 0.25 + u * zr * 1.2) * 0.45, 0, 0, TAU); ctx.stroke(); }
    ctx.globalAlpha = 1;
    // motes spiralling in towards the middle, a few bright sparkles
    const P = this.vp || (this.vp = []), want = low ? 45 : 130;
    while (P.length < want) {
      const an = rand(TAU), r = rand(0.25, 1.05) * R;
      P.push({ an, r, w: rand(0.12, 0.35), vr: rand(0.02, 0.07) * R, t: P.length < want * 0.9 && !this._vpInit ? rand(0, 4) : 0, life: rand(3, 6), sz: rand(1.5, 4.5), c: pick(['rgba(200,120,255,0.9)', 'rgba(160,100,255,0.9)', 'rgba(255,170,250,0.85)', 'rgba(130,200,255,0.8)']), spk: Math.random() < 0.12 });
    }
    this._vpInit = 1;
    let j = 0;
    for (const p of P) {
      p.t += dt; p.an += p.w * dt * (1 + 0.6 * R / (p.r + R * 0.1)); p.r -= p.vr * dt;
      if (p.t > p.life || p.r < R * 0.04) continue; P[j++] = p;
      const x = cx + Math.cos(p.an) * p.r, y = cy + Math.sin(p.an) * p.r * 0.62;
      const f = Math.min(1, p.t / 0.6, (p.life - p.t) / 0.8), z = p.sz * d * (M / 900);
      ctx.globalAlpha = f * 0.8; ctx.drawImage(RCache.glow(p.c), x - z * 4, y - z * 4, z * 8, z * 8);
      if (p.spk) { const tw = 0.5 + 0.5 * Math.sin(t * 9 + p.an * 7); ctx.globalAlpha = f * tw; ctx.strokeStyle = '#fff0ff'; ctx.lineWidth = 1.2 * d; ctx.beginPath(); ctx.moveTo(x - z * 3.2, y); ctx.lineTo(x + z * 3.2, y); ctx.moveTo(x, y - z * 3.2); ctx.lineTo(x, y + z * 3.2); ctx.stroke(); }
      else { ctx.globalAlpha = f; ctx.fillStyle = '#f4dcff'; ctx.beginPath(); ctx.arc(x, y, z * 0.55, 0, TAU); ctx.fill(); }
    }
    P.length = j;
    // time rifts: thin violet cracks that flash here and there
    const rf = this.rifts || (this.rifts = []);
    if (!low && Math.random() < dt * 0.5) rf.push({ x: rand(W), y: rand(H * 0.1, H * 0.9), t: 0, life: 0.7, pts: Array.from({ length: 6 }, () => [rand(-1, 1), rand(-1, 1)]) });
    let k2 = 0;
    for (const r of rf) {
      r.t += dt; if (r.t > r.life) continue; rf[k2++] = r;
      const f = Math.sin(r.t / r.life * Math.PI), L = M * 0.05;
      ctx.globalAlpha = f * 0.8; ctx.strokeStyle = '#e8c4ff'; ctx.lineWidth = 2 * d; ctx.beginPath(); ctx.moveTo(r.x, r.y);
      let x = r.x, y = r.y; for (const [a, b] of r.pts) { x += a * L * 0.5 + L * 0.3; y += b * L * 0.5; ctx.lineTo(x, y); }
      ctx.stroke(); ctx.globalAlpha = f * 0.5; ctx.drawImage(RCache.glow('rgba(190,100,255,0.6)'), r.x - L, r.y - L, L * 4, L * 2);
    }
    rf.length = k2;
    ctx.restore(); ctx.globalAlpha = 1;
  },
  drawLion(ctx, A, x, y, alpha = 1, ls = 1) {
    const L = this.L, sh = this.sheet; if (!sh) return;
    const f = sh.frameAt(L.anim, L.at, true) || sh.frameAt('staticR', 0, true); if (!f) return;
    const k = A.k * ls, lh = TOT_LH * k * L.sy * L.piv;
    ctx.save(); ctx.globalAlpha = alpha * L.alpha;
    ctx.translate(x, y - L.hop * A.k - lh); if (L.rot) ctx.rotate(L.rot); ctx.scale(L.sx, L.sy);
    sh.draw(ctx, f, 0, lh / L.sy, k, L.flip);
    if (L.flash > 0 && sh.white) { ctx.globalAlpha = Math.min(1, L.flash) * alpha; sh.draw(ctx, f, 0, lh / L.sy, k, L.flip, sh.white); }
    ctx.restore();
  },
};

