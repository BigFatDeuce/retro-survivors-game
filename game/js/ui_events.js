'use strict';
// ---------------------------------------------------------------- 0.26 event screens (added to UI): Musha l'Oni's
// treasure map, the TTG booster opening, the Dofawa ending with ToT, and the title (with the Dofawa as its 'O')
// a small canvas playing a monster sheet's animations in a loop (anims: [[anim, seconds], …])
function sheetStage(key, w, h, anims, scale) {
  const c = document.createElement('canvas'), k = Math.min(3, (window.devicePixelRatio || 1) * ((typeof Game !== 'undefined' && Game._uiz) || 1)); c.width = w * k; c.height = h * k; c.style.width = w + 'px'; c.style.height = h + 'px';   // (0.47: x --uiz, the menus' zoom)
  const g = c.getContext('2d'); let raf = 0, t0 = performance.now(), sh = null, cur = 0, ct = 0;
  MobSheets.load(key).then(s => { sh = s; if (s && !scale) { const f = s.frameAt('staticR', 0, true) || s.frameAt('walkR', 0, true); scale = f ? (h - 24) * 0.92 / (f[3] / s.zoom) : 1; } });   // (no scale: fit the height)
  const st = { set(i) { cur = i; ct = (performance.now() - t0) / 1000; }, stop() { cancelAnimationFrame(raf); } };
  const step = () => {
    if (!c.isConnected && performance.now() - t0 > 3000) return;
    raf = requestAnimationFrame(step);
    if (!sh) return;
    const t = (performance.now() - t0) / 1000, [a, mode] = anims[cur] || anims[0], an = sh.anims[a] ? a : 'staticR', f = sh.frameAt(an, t - ct, mode !== 'hold') || sh.frameAt('walkR', 0, true);   // (0.60: [anim, 'hold'] stops on its last frame)
    g.setTransform(k, 0, 0, k, 0, 0); g.clearRect(0, 0, w, h); if (f) sh.draw(g, f, w / 2, h - 12, scale, false);
  };
  raf = requestAnimationFrame(step); c._stage = st; return c;
}
Object.assign(UI, {
  // 0.68: the title is the original picture (work/art068/83.webp cut out of its black background, upscaled by
  // tools/lib/esrgan.py -> assets/ui/logo.webp); it floats and a light sweeps over it now and then (CSS). The
  // 0.26 Dofawa egg as the title's 'O' is gone with the old vector logo.
  // 0.71: the title is the original 'Retro Survivors' title picture (work/art068/logo2.webp, ×2 by tools/lib/esrgan.py →
  // assets/ui/logo.webp); the end-game menu (endGame()) shows his Goultard version (logo_end.webp). One <img> per picture is
  // kept for the whole session and moved back into the menu (no decoding delay when coming back to the main menu)
  logo(big) {
    const end = this.endGame(), key = end ? 'logo_end' : 'logo', C = this._logoEls || (this._logoEls = {});
    if (!C[key]) {
      const url = 'assets/ui/' + key + '.webp?v=' + (typeof BUILD !== 'undefined' ? BUILD : '');
      const art = h('div', { class: 'logo-art' + (end ? ' end' : ''), role: 'img', 'aria-label': 'Retro Survivors' }, h('img', { src: url, alt: '', draggable: 'false' }), h('span', { class: 'logo-shine' }));
      art.querySelector('.logo-shine').style.setProperty('--logo', 'url("' + url + '")');
      if (end) for (let i = 0; i < 14; i++) art.append(h('i', { class: 'ember', style: { '--x': (8 + Math.random() * 84) + '%', '--d': (2 + Math.random() * 3).toFixed(2) + 's', '--w': (-Math.random() * 4).toFixed(2) + 's' } }));
      C[key] = art;
    }
    return h('div', { class: 'logo' + (big ? ' big' : '') + (end ? ' end' : '') }, C[key]);
  },
  // 0.71: the end-game main menu (Goultard's logo, the burning wasteland): one launch in 20, always once Goultard's zone is
  // unlocked or the profile is named 'Goultard'
  endGame() {
    const S = Store.data;
    // (0.92: no random 1-in-20 any more — only Goultard unlocked or the profile named Goultard)
    return (S.unlocked || []).includes('goultard') || /^goultard$/i.test((Store.pname && Store.pname(Store.prof)) || '');
  },
  dofawaReady() { const S = Store.data, A = Game.C.achievements || []; return !!Game.C.dofawa && !S.dofawa && A.length && A.every(a => S.ach && S.ach[a.id]); },
  // ------------------------------------------------ Musha l'Oni hands over a treasure map (and swears it's nothing)
  mushaScene(R, tm, m) {   // (0.48: R = null when the Armurerie replays it)
    const M = Game.C.tmap.musha, anims = [['bonusR'], ['staticR'], ['anim1R'], ['anim2R']];
    m = m || R.map;
    // 0.68: he changes the subject with a true anecdote about the cross's zone (C.tmap.anec, tools/content/anec068.py)
    const base = Game.C.tmap.lines, an = (Game.C.tmap.anec || {})[m.id], lines = an ? [...base.slice(0, 2), an, ...base.slice(2)] : base;
    const stage = sheetStage(M.sprite, 260, 300, anims);
    // 0.47: the map of the zone the cross is in (any zone, not always this one)
    const pk = Math.min(3, (window.devicePixelRatio || 1) * (Game._uiz || 1)), map = document.createElement('canvas'); map.width = Math.round(300 * pk); map.height = Math.round(200 * pk); map.className = 'tmap-mini';
    const Wd = SPR.worlds[m.world], paint = (im) => {
      const g = map.getContext('2d'), W = Wd.w, H = Wd.h, s = Math.min(300 / W, 200 / H); g.setTransform(pk, 0, 0, pk, 0, 0);
      g.fillStyle = '#d8c39a'; g.fillRect(0, 0, 300, 200); if (im) { g.globalAlpha = 0.85; g.drawImage(im, (300 - W * s) / 2, (200 - H * s) / 2, W * s, H * s); g.globalAlpha = 1; }
      const x = (300 - W * s) / 2 + tm.x * s, y = (200 - H * s) / 2 + tm.y * s; g.lineCap = 'round'; g.strokeStyle = '#4a0a00'; g.lineWidth = 9; g.beginPath(); g.moveTo(x - 10, y - 10); g.lineTo(x + 10, y + 10); g.moveTo(x + 10, y - 10); g.lineTo(x - 10, y + 10); g.stroke(); g.strokeStyle = '#e0201a'; g.lineWidth = 5; g.stroke();
    };
    if (R && Wd === R.world && R.mini) paint(R.mini); else { paint(null); Assets.loadImg(`assets/worlds/${m.world}_mini.webp`).then(paint); }
    const dest = h('div', { class: 'tmap-dest' }, T('tmap_dest', { z: tmapZoneName(m) }), R && m.id === R.map.id ? h('small', {}, T('tmap_now')) : null);
    const bubble = h('div', { class: 'musha-bubble' }), next = btn(T('musha_next'), () => say(i + 1), 'orange');
    let i = -1;
    const say = (n) => {
      if (n >= lines.length) { stage._stage.stop(); this.closeModal(); return; }
      i = n; bubble.textContent = L(lines[i]); stage._stage.set(i % anims.length); Audio2.play(M.snd[i % M.snd.length], 0.7);
      bubble.classList.remove('pop'); void bubble.offsetWidth; bubble.classList.add('pop');
    };
    const el = h('div', { class: 'window modal musha' }, h('div', { class: 'title' }, iconImg(Game.C.tmap.icon, 26), ' ', T('tmap'), ' — ', L(M.name)),
      h('div', { class: 'content' }, h('div', { class: 'musha-row' }, stage, h('div', { class: 'musha-side' }, bubble, map, dest)), h('div', { class: 'start-row' }, next)));
    this.openModal(el); if (R) this.levelUpOpen = true; say(0);
  },
  // ------------------------------------------------ 0.52: Dark Vlad's last words, then Goultard's (Dark Vlad beaten in
  // Difficile): the last zone opens
  vladScene(R, Z) {
    const V = Game.C.bosses.dark_vlad, Gt = Game.C.bosses.goultard;
    const lines = [[V, 'vlad_d1'], [V, 'vlad_d2'], [V, 'vlad_d3'], [V, 'vlad_d4'], [V, 'vlad_d5'], [Gt, 'goultard_d1'], [Gt, 'goultard_d2'], [Gt, 'goultard_d3']];   // (0.60: serious and dramatic)
    const stages = new Map([[V, sheetStage(V.sprite, 260, 300, [['staticR']])], [Gt, sheetStage(Gt.sprite, 260, 300, [['atkR'], ['staticR']])]]);
    const holder = h('div', { class: 'vlad-stage' }), who = h('b', { class: 'vlad-who' }), bubble = h('div', { class: 'musha-bubble' }), end = h('div', { class: 'vlad-end' });
    const next = btn(T('next'), () => say(i + 1), 'orange');
    let i = -1;
    const say = (n) => {
      if (n > lines.length) { for (const s of stages.values()) s._stage.stop(); this.closeModal(); return; }
      i = n;
      if (n === lines.length) { end.textContent = T('goultard_open', { n: L(Z.name) }); end.classList.add('on'); Audio2.ui('level', 0.9); next.textContent = T('continue'); return; }
      const [b, key] = lines[n], st = stages.get(b);
      if (holder.firstChild !== st) { holder.replaceChildren(st); if (b === Gt) { el.classList.add('gt'); title.textContent = '☠ ' + L(Z.name); Audio2.blip('boom'); Audio2.sfx('EVENT', 0.8); } }
      st._stage.set(b === Gt ? (n - 5) % 2 : 0); who.textContent = L(b.name); bubble.textContent = T(key); bubble.classList.toggle('gt', b === Gt); Audio2.blip('click');
      bubble.classList.remove('pop'); void bubble.offsetWidth; bubble.classList.add('pop');
    };
    const title = h('div', { class: 'title' }, '☠ ' + L(V.name)), el = h('div', { class: 'window modal musha vladscene' }, title,
      h('div', { class: 'content' }, h('div', { class: 'musha-row' }, holder, h('div', { class: 'musha-side' }, who, bubble, end)), h('div', { class: 'start-row' }, next)));
    this.openModal(el); if (R) this.levelUpOpen = true; say(0);
  },
  // 0.60: Goultard beaten (the first time): he falls, his last words, then the clearing falls silent
  goultardScene(R, done) {
    const Gt = Game.C.bosses.goultard, keys = ['goultard_x1', 'goultard_x2', 'goultard_x3', 'goultard_x4'];
    const st = sheetStage(Gt.sprite, 260, 300, [['staticR'], ['dieR', 'hold']]);
    const who = h('b', { class: 'vlad-who' }, L(Gt.name)), bubble = h('div', { class: 'musha-bubble gt' }), end = h('div', { class: 'vlad-end' });
    let i = -1;
    const next = btn(T('next'), () => say(i + 1), 'orange');
    const say = (n) => {
      if (n > keys.length) { st._stage.stop(); this.closeModal(); if (done) done(); return; }
      i = n;
      if (n === keys.length) { st._stage.set(1); end.textContent = T('goultard_fell'); end.classList.add('on'); bubble.style.opacity = 0.35; Audio2.blip('boom'); Audio2.sfx('EVENT', 0.8); next.textContent = T('continue'); return; }
      bubble.textContent = T(keys[n]); Audio2.blip('click'); bubble.classList.remove('pop'); void bubble.offsetWidth; bubble.classList.add('pop');
    };
    const el = h('div', { class: 'window modal musha vladscene gt' }, h('div', { class: 'title' }, '☠ ' + L(Gt.name)),
      h('div', { class: 'content' }, h('div', { class: 'musha-row' }, h('div', { class: 'vlad-stage' }, st), h('div', { class: 'musha-side' }, who, bubble, end)), h('div', { class: 'start-row' }, next)));
    this.openModal(el); if (R) this.levelUpOpen = true; say(0);
  },
  // ------------------------------------------------ 0.95: Ganymède, the eagle-headed guide of Incarnam (client NPC 378,
  // sprite 9059, sheet C.gany.sprite): his tutorial on each of the first three zones (Normal, 5 s in, until seen to its end:
  // Store.data.tuto[zone]) and his congratulations when Grobe's win opens Difficile (Game.runOver). One canvas: the floating
  // isle of Incarnam over the clouds, the player on the left listening (its run CharSprite, a nod at each line), Ganymède
  // walking in from the right then gesturing as he talks (one gesture per line, back to standing when it ends); the text is
  // written out in a bubble of fixed size. The run is frozen by the modal (levelUpOpen: no pause menu on top); Échap / B
  // skips, Suite / A / clicking the bubble goes on (the whole line first). key = a zone id or 'hard'
  ganyScene(R, key, done) {
    const G = Game.C.gany, lines = G && G.scenes[key]; if (!lines) { if (done) done(); return; }
    const M = R && R.map, A = R && R.aid, mapOf = id => Game.C.maps.find(m => m.id === id) || {}, fin = m => { const b = (m.bosses || []).slice(-1)[0]; return b ? L(Game.C.bosses[b[1]].name) : ''; };
    const zone = key === 'hard' ? mapOf(G.unlockHard) : M || mapOf(key), pos = Game.C.maps.indexOf(zone);
    const vars = { g: L(G.name), map: L(zone.name || {}), b: fin(zone), p: pos > 0 ? fin(Game.C.maps[pos - 1]) : '', h: A ? Math.round((1 - A.hp) * 100) : 0, d: A ? Math.round((1 - A.dmg) * 100) : 0, v: L(Game.C.bosses.dark_vlad.name) };
    const say = s => s.replace(/\{(\w+)\}/g, (m, k) => vars[k] !== undefined ? vars[k] : m);
    const GEST = ['attitude2R', 'emote3R', 'attitude1R', 'attitude3R'];
    const W = 600, H = 280, k = Math.min(3, (window.devicePixelRatio || 1) * (Game._uiz || 1)), cv = document.createElement('canvas'); cv.width = W * k; cv.height = H * k; cv.className = 'gany-stage';
    const g = cv.getContext('2d'), t0 = performance.now(), cs = R && R.player && R.player.sprite;
    let sh = null, raf = 0, i = -1, lineT = 0, shown = 0, closed = false;
    MobSheets.load(G.sprite).then(s => { sh = s; });
    const clouds = Array.from({ length: 9 }, (_, n) => ({ x: (n * 137) % W, y: 30 + (n * 53) % 150, r: 18 + (n * 29) % 26, v: 6 + (n % 4) * 3 }));
    const draw = () => {
      if (closed || !cv.isConnected && performance.now() - t0 > 2000) return; raf = requestAnimationFrame(draw);
      const t = (performance.now() - t0) / 1000, lt = t - lineT;
      g.setTransform(k, 0, 0, k, 0, 0);
      const sky = g.createLinearGradient(0, 0, 0, H); sky.addColorStop(0, '#9fd2f2'); sky.addColorStop(0.65, '#f4e8c8'); sky.addColorStop(1, '#e8d6a8'); g.fillStyle = sky; g.fillRect(0, 0, W, H);
      g.fillStyle = 'rgba(255,255,255,0.75)';   // the clouds of Incarnam, drifting
      for (const c of clouds) { const x = (c.x + t * c.v) % (W + 120) - 60; g.beginPath(); g.arc(x, c.y, c.r, 0, TAU); g.arc(x + c.r * 0.9, c.y + 4, c.r * 0.75, 0, TAU); g.arc(x - c.r * 0.9, c.y + 6, c.r * 0.65, 0, TAU); g.fill(); }
      // the floating isle: grass on top, earth hanging under it
      g.fillStyle = '#8a5a2c'; g.beginPath(); g.moveTo(40, H - 46); g.quadraticCurveTo(W / 2, H + 40, W - 40, H - 46); g.fill();
      const gr = g.createLinearGradient(0, H - 70, 0, H - 30); gr.addColorStop(0, '#9ed05a'); gr.addColorStop(1, '#5f9a2c'); g.fillStyle = gr; g.beginPath(); g.ellipse(W / 2, H - 50, W / 2 - 34, 26, 0, 0, TAU); g.fill();
      g.fillStyle = 'rgba(0,0,0,0.18)'; for (const x of [W * 0.27, W * 0.7]) { g.beginPath(); g.ellipse(x, H - 50, 34, 9, 0, 0, TAU); g.fill(); }
      // the player, listening (a small nod when a line starts)
      if (cs) { const nod = lt < 0.35 ? Math.sin(lt / 0.35 * Math.PI) * 0.035 : 0; g.save(); g.translate(W * 0.27, H - 50); g.scale(1, 1 - nod); cs.draw(g, 'staticR', t, 0, 0, 2.75, false, { loop: true, at: t }); g.restore(); }
      // Ganymède: walks in, then one gesture per line
      if (sh) {
        const walk = Math.min(1, t / 0.9), x = W * 0.7 + (1 - walk) ** 2 * W * 0.35, f0 = sh.frameAt('staticR', 0, true);   // (eased in from the right edge)
        const sc = f0 ? 172 / (f0[3] / sh.zoom) : 1;
        let f;
        if (walk < 1) f = sh.frameAt('walkR', t, true);
        else { const a = GEST[i % GEST.length], an = i >= 0 && sh.anims[a], dur = an ? an.f.length / an.fps : 0; f = an && lt < dur ? sh.frameAt(a, lt, false) : sh.frameAt('staticR', t, true); }
        if (f) sh.draw(g, f, x, H - 50, sc, true);
      }
      // the line, written out
      if (i >= 0) { const full = lineTxt; shown = Math.min(full.length, Math.floor(lt * 55)); if (shown !== txtSpan.textContent.length) { txtSpan.textContent = full.slice(0, shown); restSpan.textContent = full.slice(shown); } }
    };
    let lineTxt = '';
    const who = h('b', { class: 'vlad-who' }, L(G.name)), txtSpan = h('span'), restSpan = h('span', { class: 'gany-rest' }), bubble = h('div', { class: 'musha-bubble gany-bubble' }, txtSpan, restSpan);
    const finish = () => { if (closed) return; closed = true; cancelAnimationFrame(raf); if (key !== 'hard') { const S = Store.data; S.tuto = S.tuto || {}; S.tuto[key] = 1; Store.save(); } this._luBack = null; this.closeModal(); Audio2.blip('click'); if (done) done(); };
    const next = (n) => {
      if (i >= 0 && shown < lineTxt.length) { lineT = (performance.now() - t0) / 1000 - lineTxt.length / 55; return; }   // (the whole line first)
      if (n >= lines.length) return finish();
      i = n; lineTxt = say(L(lines[n])); lineT = (performance.now() - t0) / 1000; txtSpan.textContent = ''; restSpan.textContent = lineTxt;
      nextB.textContent = n === lines.length - 1 ? T('continue') : T('next');
      bubble.classList.remove('pop'); void bubble.offsetWidth; bubble.classList.add('pop');
      const last = n === lines.length - 1; Audio2.blip('click');
      if (last && (key === 'hard' || A)) Audio2.ui('level', 0.7);   // (the line that says what it gives)
    };
    const nextB = btn(T('next'), () => next(i + 1), 'orange'), skipB = btn(T('gany_skip'), finish);
    bubble.addEventListener('click', () => next(i + 1));
    const el = h('div', { class: 'window modal gany' }, h('div', { class: 'title' }, '✦ ' + L(G.name) + (key === 'hard' ? ' — ' + T('hard_unlocked') : ' — ' + L(zone.name || {}))),
      h('div', { class: 'content' }, cv, h('div', { class: 'gany-side' }, who, bubble), h('div', { class: 'start-row' }, skipB, nextB)));
    this.openModal(el); this.levelUpOpen = true; this._luBack = finish;
    if (typeof Nav !== 'undefined') Nav.set(nextB);
    Audio2.play('son_anim_ailes_dragondinde', 0.35, 0.9); if (key === 'hard' && Audio2.fanfare) Audio2.fanfare(0.8);   // (his arrival: wings; Difficile: a fanfare)
    raf = requestAnimationFrame(draw);
    setTimeout(() => { if (!closed && i < 0) next(0); }, 950);   // (the first line once he has walked in)
  },
  // ------------------------------------------------ 0.40-0.41: useless but cute visitors on the main menu, one every 5 minutes,
  // taking turns: a Kwak de Flamme (1042) flaps across, stops, spits fire and flies off; a Tofu (1558) runs along the
  // bottom, pecks, and runs back where it came from. (?kwak=1 / ?tofu=1 show one at once)
  kwakTimer() {
    const dbg = Game.debug || {};
    if ((dbg.kwak || dbg.tofu) && !this._kwakDbg) { this._kwakDbg = 1; setTimeout(() => dbg.tofu ? this.tofuRun() : this.kwakFly(), 1500); }
    if (this._kwakIv) return;
    this._kwakIv = setInterval(() => {
      if (this.screen !== 'main' || this.modalOpen() || document.hidden || this._kwakOn) return;
      const S = Store.data, now = Date.now(); if (now - (S.lastCritter || 0) < 5 * 60e3) return;
      S.lastCritter = now; const k = S.nextCritter === 'tofu' ? 'tofu' : 'kwak'; S.nextCritter = k === 'tofu' ? 'kwak' : 'tofu'; Store.save();
      k === 'tofu' ? this.tofuRun() : this.kwakFly();
    }, 15e3);
  },
  // a canvas over the menu and a smooth real-time loop (dt-based, eased moves)
  critterStage(draw) {
    this._kwakOn = true;
    const cv = h('canvas', { class: 'kwak-fly' }), ctx = cv.getContext('2d'), dpr = Math.min(2, devicePixelRatio || 1);
    document.body.append(cv); const W = innerWidth, H = innerHeight; cv.width = W * dpr; cv.height = H * dpr; ctx.scale(dpr, dpr);
    let last = 0;
    const end = () => { cv.remove(); this._kwakOn = false; };
    const step = (now) => {
      const dt = Math.min(0.04, (now - (last || now)) / 1000); last = now;
      if (this.screen !== 'main') return end();
      ctx.clearRect(0, 0, W, H); ctx.imageSmoothingQuality = 'high';
      if (draw(ctx, dt, W, H) === false) return end();
      requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  },
  async kwakFly() {
    const sh = await MobSheets.load('1042_z48'); if (!sh || this.screen !== 'main' || this._kwakOn) return;
    Audio2.preload(['son_anim_ailes_dragondinde', 'lance', 'pose2']);
    let phase = 'in', pt = 0, wt = 0, x = -80, flap = 0, said = false, fire = [], y0 = 0, sc = 0, stopX = 0;
    const ease = k => k * k * (3 - 2 * k);
    this.critterStage((ctx, dt, W, H) => {
      if (!sc) { sc = Math.max(1, H / 330); y0 = H * (0.2 + Math.random() * 0.25); stopX = W * (0.45 + Math.random() * 0.2); }
      pt += dt; let anim = 'walkR', at = (wt += dt), y = y0;
      if (phase === 'in') { const k = Math.min(1, (stopX - x) / (W * 0.18)); x += W * 0.26 * dt * Math.max(0.12, ease(Math.max(0, k))); y = y0 + Math.sin(pt * 3) * 10 * sc; if (stopX - x < 2) { phase = 'stop'; pt = 0; } }
      else if (phase === 'stop') { anim = sh.has('staticR') ? 'staticR' : 'walkR'; y = y0 + Math.sin(pt * 2) * 4 * sc; if (!said) { said = true; Audio2.play('pose2', 0.7); } if (pt > 0.9) { phase = 'atk'; pt = 0; Audio2.play('lance', 0.8); } }
      else if (phase === 'atk') { anim = 'atkR'; at = pt; if (pt > 0.25 && pt < 0.9 && Math.random() < 0.6) fire.push({ x: x + 22 * sc, y: y - 12 * sc, vx: (220 + Math.random() * 140) * sc / 2, vy: (Math.random() - 0.5) * 50, t: 0 });
        if (pt > (sh.duration('atkR') || 1.4)) { phase = 'out'; pt = 0; wt = 0; } }
      else { x += W * 0.34 * dt * ease(Math.min(1, 0.15 + pt)); y = y0 - pt * H * 0.05 + Math.sin(pt * 3) * 10 * sc; if (x > W + 120) return false; }
      if (phase === 'in' || phase === 'out') { if ((flap -= dt) <= 0) { flap = 0.42; Audio2.play('son_anim_ailes_dragondinde', 0.35, 0.95 + Math.random() * 0.1); } }
      for (const p of fire) { p.t += dt; p.x += p.vx * dt; p.y += p.vy * dt; const k = 1 - p.t / 0.7; if (k <= 0) continue; const r = (10 * k + 4) * sc / 2; ctx.globalAlpha = k; ctx.drawImage(RCache.glow(p.t < 0.25 ? 'rgba(255,230,120,0.95)' : 'rgba(255,110,30,0.85)'), p.x - r, p.y - r, r * 2, r * 2); }
      fire = fire.filter(p => p.t < 0.7); ctx.globalAlpha = 1;
      const f = sh.frameAt(anim, at, true); if (f) sh.draw(ctx, f, x, y, sc, false);
    });
  },
  async tofuRun() {
    const sh = await MobSheets.load('1558_z48'); if (!sh || this.screen !== 'main' || this._kwakOn) return;
    Audio2.preload(['tofu2']);
    let phase = 'in', pt = 0, wt = 0, x = -40, stopX = 0, sc = 0, yb = 0, back = false, peep = 0;
    const run = sh.has('runR') ? 'runR' : 'walkR';
    this.critterStage((ctx, dt, W, H) => {
      if (!sc) { sc = Math.max(1.2, H / 260); yb = H - 26 * sc; stopX = W * (0.3 + Math.random() * 0.35); }
      pt += dt; wt += dt; let anim = run, at = wt * 1.3, flip = back;
      if (phase === 'in') { x += W * 0.3 * dt * Math.max(0.25, Math.min(1, (stopX - x) / (W * 0.12))); if ((peep -= dt) <= 0) { peep = 0.9; } if (stopX - x < 2) { phase = 'atk'; pt = 0; Audio2.play('tofu2', 0.7); } }
      else if (phase === 'atk') { anim = sh.has('atkR') ? 'atkR' : 'staticR'; at = pt; if (pt > (sh.duration(anim) || 1) + 0.25) { phase = 'out'; pt = 0; back = true; Audio2.play('tofu2', 0.55, 1.2); } }
      else { x -= W * 0.4 * dt * Math.min(1, 0.25 + pt * 1.5); if (x < -60) return false; }
      ctx.globalAlpha = 0.22; ctx.fillStyle = '#000'; ctx.beginPath(); ctx.ellipse(x, yb + 2, 12 * sc, 4 * sc, 0, 0, TAU); ctx.fill(); ctx.globalAlpha = 1;
      const f = sh.frameAt(anim, at, true); if (f) sh.draw(ctx, f, x, yb, sc, flip);
    });
  },
  // ------------------------------------------------ a TTG booster (0.37: the real pack picture; it glows and shakes harder
  // and harder in turning light rays, bursts open in a flash and sparks, the card rises spinning out of it, then flips
  // in rays of its rarity's colour)
  boosterOpen(R, card, n, pk = 0) {
    const dup = n > 1, B = SPR.boosters || { cols: 5, n: 14 }, rows = Math.ceil(B.n / B.cols), i = pk % B.n;
    const pos = `${(i % B.cols) / (B.cols - 1) * 100}% ${Math.floor(i / B.cols) / (rows - 1) * 100}%`;
    const half = (c) => h('div', { class: 'bp-half ' + c, style: { backgroundImage: `url(${vurl('assets/ui/boosters.webp')})`, backgroundSize: `${B.cols * 100}% ${rows * 100}%`, backgroundPosition: pos } });
    const face = h('div', { class: 'ttg-face' }, ttgCard(card));
    const cardEl = h('div', { class: 'ttg-card' }, h('div', { class: 'ttg-back' }, 'TTG'), face);
    const pack = h('div', { class: 'ttg-pack' }, half('top'), half('body'));
    const rays = h('div', { class: 'bp-rays' }), flash = h('div', { class: 'bp-flash' }), sparks = h('div', { class: 'bp-sparks' });
    for (let k = 0; k < 28; k++) { const a = Math.random() * TAU, d = 120 + Math.random() * 160; sparks.appendChild(h('i', { style: { '--dx': Math.cos(a) * d + 'px', '--dy': Math.sin(a) * d + 'px', '--s': (0.5 + Math.random()).toFixed(2), animationDelay: (Math.random() * 0.15).toFixed(2) + 's' } })); }
    const RC = ['#d8d8d8', '#5fb8ff', '#c77dff', '#ffd24a'];
    const stage = h('div', { class: 'ttg-stage', style: { '--rc': RC[card.r || 0] } }, rays, pack, cardEl, sparks, flash);
    const msg = h('div', { class: 'ttg-msg' + (dup ? ' dup' : '') }), ok = btn(T('continue'), () => this.closeModal(), 'orange big'); ok.style.visibility = 'hidden';
    const el = h('div', { class: 'window modal booster' }, h('div', { class: 'title' }, T('booster')), h('div', { class: 'content' }, stage, msg, h('div', { class: 'start-row' }, ok)));
    this.openModal(el); this.levelUpOpen = true; Audio2.play('pages', 0.7); stage.classList.add('charge');
    setTimeout(() => { Audio2.play('rapid_swish', 0.5); Audio2.boosterSfx('riser'); }, 200);
    setTimeout(() => { stage.classList.add('burst'); pack.classList.add('torn'); Audio2.play('rapid_swish', 0.8); Audio2.boosterSfx('burst'); Audio2.sfx('EVENT', 0.7); }, 1700);
    setTimeout(() => { cardEl.classList.add('flip'); stage.classList.add('reveal', 'r' + (card.r || 0)); Audio2.play('pages', 0.6); }, 2500);
    setTimeout(() => {
      msg.textContent = dup ? T('ttg_dup', { c: n }) : T('ttg_new', { n: L(card.name) });
      if (dup) { el.classList.add('angry'); Audio2.play('grrr2', 0.7); Audio2.blip('wrong'); } else { Audio2.play('stars', 0.8); Audio2.ui('level', 0.7); }
      ok.style.visibility = 'visible'; Nav.el = null;
    }, 3200);
  },
  // ------------------------------------------------ the Dofawa ending: ToT on stage, one line at a time (each can be
  // skipped only after C.dofawa.skipDelay seconds), then the Dofawa takes the 'O' of the title
  dofawaScene() {
    const D = Game.C.dofawa; if (!this.dofawaReady()) return;
    const stage = sheetStage(Game.C.totSprite, 300, 320, [['staticR'], ['walkR'], ['staticF'], ['runS'], ['staticR'], ['walkF']]);
    const bubble = h('div', { class: 'musha-bubble tot' }), egg = h('div', { class: 'dofawa-egg' }, iconImg(D.icon, 96));
    const bar = h('i', { class: 'skip-bar' }), next = btn([T('dofawa_next'), bar], () => { if (!next.classList.contains('disabled')) say(i + 1); }, 'orange');
    let i = -1, timer = 0;
    const say = (n) => {
      if (n >= D.lines.length) {   // the reward: once per profile
        Store.data.dofawa = Date.now(); Store.save(); stage._stage.stop(); this.closeModal(); Audio2.ui('level', 0.9); toast(T('dofawa_got')); this.mainMenu(); return;
      }
      i = n; bubble.textContent = L(D.lines[i]); stage._stage.set(i); bubble.classList.remove('pop'); void bubble.offsetWidth; bubble.classList.add('pop');
      egg.classList.toggle('show', i >= 3); if (i === 3) { Audio2.play('stars', 0.9); Audio2.sfx('EVENT', 0.8); } else Audio2.blip('click');
      next.classList.add('disabled'); bar.style.transition = 'none'; bar.style.width = '0%'; void bar.offsetWidth; bar.style.transition = `width ${D.skipDelay}s linear`; bar.style.width = '100%';
      clearTimeout(timer); timer = setTimeout(() => next.classList.remove('disabled'), D.skipDelay * 1000);
    };
    const el = h('div', { class: 'window modal dofawa' }, h('div', { class: 'title' }, '★ ', T('dofawa_btn')),
      h('div', { class: 'content' }, h('div', { class: 'musha-row' }, h('div', { class: 'tot-stage' }, stage, egg), h('div', { class: 'musha-side' }, bubble)), h('div', { class: 'start-row' }, next)));
    this.openModal(el); Audio2.sfx('EVENT', 0.7); say(0);
  },
});
