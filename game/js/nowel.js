// 0.68: L'île de Nowel's own rules (map.nowel = { every, n }): no kamas at all (Run.kamas refuses gains when
// map.noKamas), no skin merchant (map.noMerchant); every `every` s (n times in a run) a big 'Cadeau de Nowel
// potentiellement surpuissant' falls near the character — opened in a Christmas show (snow, ribbons, the gift
// bursting), it unlocks a random hat or cape; the final boss drops a 'Ticket de la foire du Trool': picking it up stops
// the run and a Christmas wheel of skins turns, the skin under the pointer is won. Run.prototype methods (extras.js
// pattern), UI.nowelWheel below.
Object.assign(Run.prototype, {
  // a random skin the profile does not own yet (kinds: 'hats', 'capes', 'pets'); null when all are owned
  nowelSkin(kinds) {
    const S = Store.data, own = new Set(S.owned || []), C = this.C;
    const pool = kinds.flatMap(k => (C[k] || []).filter(x => !own.has(x.id) && x.price !== undefined));
    return pool.length ? pick(pool) : null;
  },
  skinName(x) { const n = x && x.name; return n ? L(n) : x ? x.id : ''; },
  updateNowel() {
    const N = this.map.nowel; if (!N || this.over) return;
    this._ngN = this._ngN || 0;
    if (this._ngN < N.n && this.time >= N.every * (this._ngN + 1)) {
      this._ngN++; const P = this.player;
      for (let k = 0; k < 20; k++) {
        const a = rand(TAU), x = clamp(P.x + Math.cos(a) * 260, this.bounds.x0, this.bounds.x1), y = clamp(P.y + Math.sin(a) * 170, this.bounds.y0, this.bounds.y1);
        if (!this.isWater(x, y) || k === 19) { this.dropPickup('nowelgift', x, y, 1); break; }
      }
      this.announce(T('nowel_gift_here_t'), T('nowel_gift_here'), '#ff5a5a', { center: true }); Audio2.play('stars', 0.8); Audio2.sfx('EVENT', 0.7);
    }
  },
  // the gift is picked up: a skin is unlocked now (saved), then the show
  nowelGift() {
    const x = this.nowelSkin(['hats', 'capes']), S = Store.data; Prog.add('nowelGifts');   // (0.92: an achievement, 3 gifts)
    if (x) { S.owned = S.owned || []; S.owned.push(x.id); Store.save(); }
    this.slowMo(0.5, 0.3);
    this.startCine('gift', { skin: x }, () => {
      if (x) this.announce(this.skinName(x), T('nowel_gift_got', { n: this.skinName(x) }), '#9cff6a', { center: true });
      else this.chat(T('nowel_all'), '#ffd24a');
    });
  },
  // the final boss's ticket: the wheel of skins
  troolTicket() {
    const won = this.nowelSkin(['hats', 'capes', 'pets']);
    if (!won) { this.chat(T('nowel_all'), '#ffd24a'); return; }
    const pool = ['hats', 'capes', 'pets'].flatMap(k => this.C[k] || []);
    if (typeof UI !== 'undefined' && UI.nowelWheel && !(Game.debug || {}).bot) UI.nowelWheel(this, won, pool, () => this.giveSkin(won));
    else this.giveSkin(won);
  },
  giveSkin(x) {
    const S = Store.data; S.owned = S.owned || []; if (!S.owned.includes(x.id)) S.owned.push(x.id); Store.save();
    this.chat(T('nowel_gift_got', { n: this.skinName(x) }), '#9cff6a');
  },
  // the gift's show (screen space): snow falling, the big gift shaking, bursting in ribbons and stars, the skin rising
  drawGift(ctx, W, H, c) {
    const S = Math.min(W, H), k = Math.min(1, c.t / 0.3) * Math.min(1, (c.dur - c.t) / 0.3), cx = W / 2, cy = H * 0.46, D = c.data;
    ctx.fillStyle = 'rgba(8,20,40,' + (0.62 * k) + ')'; ctx.fillRect(0, 0, W, H);
    D.snow = D.snow || Array.from({ length: 90 }, () => [Math.random(), Math.random(), 0.4 + Math.random(), Math.random() * TAU]);
    for (const f of D.snow) { const x = ((f[0] + Math.sin(c.t + f[3]) * 0.02) * W), y = ((f[1] + c.t * 0.08 * f[2]) % 1) * H, r = (1.5 + f[2] * 2.5) * S / 700; ctx.globalAlpha = 0.85 * k; ctx.drawImage(RCache.glow('rgba(255,255,255,0.95)'), x - r * 2, y - r * 2, r * 4, r * 4); }
    const open = c.t > 1.6, shake = !open ? Math.sin(c.t * (14 + c.t * 20)) * Math.min(1, c.t / 1.2) * 0.12 : 0;
    ctx.save(); ctx.globalAlpha = k; ctx.translate(cx, cy);
    ctx.rotate(c.t * 0.4); for (let i = 0; i < 14; i++) { ctx.rotate(TAU / 14); const rg = ctx.createLinearGradient(0, 0, 0, -S * 0.45); rg.addColorStop(0, i % 2 ? 'rgba(255,80,80,0.55)' : 'rgba(110,255,130,0.55)'); rg.addColorStop(1, 'rgba(255,255,255,0)'); ctx.fillStyle = rg; ctx.beginPath(); ctx.moveTo(-8, 0); ctx.lineTo(-S * 0.05, -S * 0.45); ctx.lineTo(S * 0.05, -S * 0.45); ctx.lineTo(8, 0); ctx.fill(); }
    ctx.restore();
    ctx.save(); ctx.globalAlpha = k; ctx.translate(cx, cy);
    if (!open) { ctx.rotate(shake); ctx.drawImage(RCache.glow('rgba(255,240,180,0.9)'), -S * 0.2, -S * 0.2, S * 0.4, S * 0.4); Game.icons.drawFit(ctx, 'gift_hd', 0, 0, S * 0.24 * (1 + 0.04 * Math.sin(c.t * 12))); }
    else {
      const q = Math.min(1, (c.t - 1.6) / 0.5), x = D.skin;
      if (!D.burst) { D.burst = 1; Audio2.play('stars', 0.9); Audio2.sfx('EVENT', 0.8); Audio2.fanfare && Audio2.fanfare(1); }
      for (let i = 0; i < 26; i++) { const a = i / 26 * TAU, d = q * S * (0.18 + 0.12 * (i % 3)), w = S * 0.014 * (1 - q * 0.5); ctx.globalAlpha = k * (1 - q * 0.6); ctx.drawImage(RCache.glow(['rgba(255,70,70,0.95)', 'rgba(90,240,120,0.95)', 'rgba(255,230,120,0.95)'][i % 3]), Math.cos(a) * d - w * 2, Math.sin(a) * d * 0.8 - w * 2, w * 4, w * 4); }
      ctx.globalAlpha = k; ctx.drawImage(RCache.glow('rgba(255,250,210,0.95)'), -S * 0.16, -S * 0.2 - q * S * 0.04, S * 0.32, S * 0.32);
      if (x) Game.icons.drawFit(ctx, 'it_' + x.id, 0, -q * S * 0.04, S * 0.2 * (0.5 + 0.5 * q));
      const txt = x ? T('nowel_gift_got', { n: this.skinName(x) }) : T('nowel_all'), fs = Math.round(Math.min(34, W / 30));
      ctx.font = 'bold ' + fs + 'px DofusBold, Verdana'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.lineJoin = 'round';
      ctx.lineWidth = fs * 0.18; ctx.strokeStyle = '#2a0808'; ctx.strokeText(txt, 0, S * 0.22); ctx.fillStyle = '#fff3d0'; ctx.fillText(txt, 0, S * 0.22);
    }
    ctx.restore(); ctx.globalAlpha = 1;
    const title = T('nowel_gift'), fs = Math.round(Math.min(28, W / 36)); ctx.font = 'bold ' + fs + 'px DofusBold, Verdana'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.globalAlpha = k; ctx.lineWidth = fs * 0.18; ctx.strokeStyle = '#0a2a14'; ctx.strokeText(title, cx, H * 0.14); ctx.fillStyle = '#ff6a6a'; ctx.fillText(title, cx, H * 0.14); ctx.globalAlpha = 1;
  },
});

if (typeof UI !== 'undefined') Object.assign(UI, {
  // the Christmas wheel: 12 skins (red / green / white slices, a star in the hub), the won one under the pointer at the end
  nowelWheel(R, won, pool, give) {
    const N = 12, others = shuffle(pool.filter(o => o.id !== won.id)).slice(0, N - 1);
    const P = randi(0, N - 1), segs = others.slice(); segs.splice(P, 0, won);
    const size = 340, wheel = document.createElement('canvas'), kk = Math.min(3, window.devicePixelRatio || 1) * (Game._uiz || 1);
    wheel.width = wheel.height = Math.round(size * kk); wheel.style.width = wheel.style.height = size + 'px';
    const g = wheel.getContext('2d'), Rr = wheel.width / 2; g.translate(Rr, Rr);
    const COLS = ['#c8202a', '#1f8a3a', '#f4efe4'];
    for (let i = 0; i < N; i++) {
      const a0 = i * TAU / N - Math.PI / 2 - Math.PI / N, a1 = a0 + TAU / N;
      g.beginPath(); g.moveTo(0, 0); g.arc(0, 0, Rr * 0.96, a0, a1); g.closePath(); g.fillStyle = COLS[i % 3]; g.fill(); g.strokeStyle = '#3a1a08'; g.lineWidth = Rr * 0.02; g.stroke();
      g.save(); g.rotate(a0 + Math.PI / N + Math.PI / 2); const s = Rr * 0.26; g.drawImage(Game.icons.canvas('it_' + segs[i].id, Math.round(s * 1.5)), -s / 2, -Rr * 0.86, s, s); g.restore();
    }
    g.beginPath(); g.arc(0, 0, Rr * 0.96, 0, TAU); g.lineWidth = Rr * 0.05; g.strokeStyle = '#e8c34a'; g.stroke();
    for (let i = 0; i < N; i++) { const a = i * TAU / N - Math.PI / 2 - Math.PI / N; g.beginPath(); g.arc(Math.cos(a) * Rr * 0.96, Math.sin(a) * Rr * 0.96, Rr * 0.03, 0, TAU); g.fillStyle = i % 2 ? '#ff4a4a' : '#7aff8a'; g.fill(); }
    g.beginPath(); g.arc(0, 0, Rr * 0.15, 0, TAU); g.fillStyle = '#1f5a2a'; g.fill(); g.lineWidth = Rr * 0.025; g.strokeStyle = '#ffd24a'; g.stroke();
    const box = h('div', { class: 'troll-wheel nowel-wheel' }, wheel, h('div', { class: 'troll-ptr' }), h('div', { class: 'troll-hub' }, iconImg('it_24_94', 44)));
    const status = h('div', { class: 't-status' }, T('wheel_spin'));
    const prizeEl = h('div', { class: 't-prize' }, iconImg('it_' + won.id, 48), ' ', T('nowel_gift_got', { n: R.skinName(won) }));
    let raf = 0, given = false;
    const done = () => { if (given) return; given = true; cancelAnimationFrame(raf); give(); this.closeModal(); };
    const okBtn = btn(T('wheel_ok'), done, 'orange big'); okBtn.style.visibility = 'hidden';
    const el = h('div', { class: 'window modal tailor trool nowel' }, h('div', { class: 'title' }, iconImg('it_24_94', 26), ' ', T('nowel_wheel')), h('div', { class: 'content' },
      box, h('div', { class: 'troll-side' }, status, prizeEl, h('div', { class: 'start-row' }, okBtn))));
    this.openModal(el); this.levelUpOpen = true;
    const turns = 5 + randi(0, 2), end = -(P * TAU / N) + rand(-0.32, 0.32) * TAU / N - turns * TAU, T1 = 5.2, start = performance.now(); let last = -1;
    const ease = q => 1 - Math.pow(1 - q, 3.4);
    const step = () => {
      if (!el.isConnected) { if (!given) { given = true; give(); } return; }
      const q = Math.min(1, (performance.now() - start) / 1000 / T1), a = end * ease(q);
      wheel.style.transform = 'rotate(' + a + 'rad)';
      const sl = Math.floor((-a / TAU * N) + 0.5); if (sl !== last) { last = sl; Audio2.play('click3', 0.4, 1.3); }
      if (q >= 1) { el.classList.add('jackpot'); status.textContent = ''; prizeEl.classList.add('show'); okBtn.style.visibility = 'visible'; Audio2.sfx('EVENT', 0.8); Audio2.play('stars', 0.8); Nav.el = null; return; }
      raf = requestAnimationFrame(step);
    };
    Audio2.play('pages', 0.6); raf = requestAnimationFrame(step);
  },
});
