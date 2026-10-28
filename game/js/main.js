'use strict';
// ---------------------------------------------------------------- input
const Input = {
  keys: new Set(), touch: { active: false, id: null, sx: 0, sy: 0, dx: 0, dy: 0 }, pad: null,
  // the last device the player used ('kb' keyboard/mouse, 'pad', 'touch'): the in-game hints follow it
  dev: (window.matchMedia && matchMedia('(pointer: coarse)').matches) ? 'touch' : 'kb', layout: null,
  init(canvas) {
    window.addEventListener('keydown', e => {
      Audio2.init(); Audio2.resume(); this.dev = 'kb';
      // keyboard layout from what the letter keys type: Q position typing 'a' (or W typing 'z') = AZERTY
      if (e.key && e.key.length === 1) { const k = e.key.toLowerCase(); if ((e.code === 'KeyQ' && k === 'a') || (e.code === 'KeyW' && k === 'z')) this.layout = 'azerty'; else if ((e.code === 'KeyQ' && k === 'q') || (e.code === 'KeyW' && k === 'w')) this.layout = 'qwerty'; }
      const tag = (e.target && e.target.tagName) || '';
      if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Space'].includes(e.code) && tag !== 'INPUT') e.preventDefault();
      this.keys.add(e.code);
      if (Nav.key(e)) return;
      const live = Game.state === 'run' && Game.run && !Game.paused && !UI.modalOpen() && !e.repeat;
      if (live && (e.code === 'Space' || e.code === 'KeyE')) Game.run.player.dodge();           // dash: Space or E
      if (live && e.code === 'KeyQ') Game.run.toggleMoveSpells();                            // Q on QWERTY = A on AZERTY (same key)
      if (live && e.code === 'KeyR') Game.toggleAutoPick();
      if (Game.state === 'run' && e.code === 'KeyF' && !e.repeat && !UI.modalOpen()) toggleFullscreen();   // 0.34                                   // 0.34: R = the bread / kamas auto-choice on / off
      Game.onKey(e);
    });
    window.addEventListener('keyup', e => this.keys.delete(e.code));
    window.addEventListener('blur', () => { this.keys.clear(); Game.autoPause(); });
    document.addEventListener('visibilitychange', () => { if (document.hidden) Game.autoPause(); });
    const ts = (e) => {
      Audio2.init(); Audio2.resume(); this.dev = 'touch';
      if (Game.state !== 'run') return;
      this.touch.used = true;
      for (const t of e.changedTouches) {
        // tap on the movement-spell icon (left of the heart): switch those spells on / off
        if (Game.run && !UI.modalOpen() && Game.run.hudHit(t.clientX * Game.dpr, t.clientY * Game.dpr)) { Game.run.toggleMoveSpells(); continue; }
        { const A = Game.run && Game.run.hudAuto, x = t.clientX * Game.dpr, y = t.clientY * Game.dpr; if (A && !UI.modalOpen() && Math.hypot(x - A.x, y - A.y) < A.r * 1.3) { Game.toggleAutoPick(); continue; } }   // (0.34: the bread / kamas icon)
        // double tap: dash towards the tapped spot
        const now = performance.now();
        if (this._lastTap && now - this._lastTap.t < 300 && Math.hypot(t.clientX - this._lastTap.x, t.clientY - this._lastTap.y) < 60 && Game.run && !UI.modalOpen()) {
          const R = Game.run, px = (R.player.x - R.cam.x) * Game.zoom + Game.cw / 2, py = (R.player.y - 30 - R.cam.y) * Game.zoom + Game.ch / 2;
          R.player.dodge(t.clientX * Game.dpr - px, t.clientY * Game.dpr - py); this._lastTap = null;
        }
        else this._lastTap = { t: now, x: t.clientX, y: t.clientY };
        if (this.touch.id === null) { this.touch = { active: true, used: true, id: t.identifier, sx: t.clientX * Game.dpr, sy: t.clientY * Game.dpr, dx: 0, dy: 0 }; }
      }
      e.preventDefault();
    };
    const tm = (e) => {
      for (const t of e.changedTouches) if (t.identifier === this.touch.id) {
        let dx = (t.clientX * Game.dpr - this.touch.sx) / (50 * Game.ui), dy = (t.clientY * Game.dpr - this.touch.sy) / (50 * Game.ui);
        const l = Math.hypot(dx, dy); if (l > 1) { dx /= l; dy /= l; }
        this.touch.dx = dx; this.touch.dy = dy;
      }
      e.preventDefault();
    };
    const te = (e) => { for (const t of e.changedTouches) if (t.identifier === this.touch.id) this.touch = { active: false, used: true, id: null, sx: 0, sy: 0, dx: 0, dy: 0 }; };
    canvas.addEventListener('touchstart', ts, { passive: false });
    canvas.addEventListener('touchmove', tm, { passive: false });
    canvas.addEventListener('touchend', te); canvas.addEventListener('touchcancel', te);
    window.addEventListener('mousedown', () => { Audio2.init(); Audio2.resume(); });
    // 0.34: hold the left mouse button in a run: the character walks towards the cursor (a click on the HUD icons still
    // switches them: the movement spells, the bread / kamas choice)
    this.mouse = { down: false, x: 0, y: 0 };
    canvas.addEventListener('wheel', (e) => { if (Game.state === 'run') Game.konamiStep(e.deltaY < 0 ? 'U' : 'D'); }, { passive: true });
    canvas.addEventListener('contextmenu', (e) => { if (Game.state === 'run') { e.preventDefault(); Game.konamiStep('R'); } });
    canvas.addEventListener('mousedown', (e) => { if (e.button === 0 && Game.state === 'run' && Game._kc >= 4) Game.konamiStep('L'); });
    canvas.addEventListener('mousedown', (e) => {
      if (e.button !== 0 || Game.state !== 'run' || !Game.run || UI.modalOpen()) return;
      const x = e.clientX * Game.dpr, y = e.clientY * Game.dpr, R = Game.run;
      if (R.hudHit(x, y)) { R.toggleMoveSpells(); return; }
      if (R.hudAuto && Math.hypot(x - R.hudAuto.x, y - R.hudAuto.y) < R.hudAuto.r) { Game.toggleAutoPick(); return; }
      this.mouse = { down: true, x, y };
    });
    window.addEventListener('mousemove', (e) => { if (this.mouse.down) { this.mouse.x = e.clientX * Game.dpr; this.mouse.y = e.clientY * Game.dpr; } });
    window.addEventListener('mouseup', (e) => { if (e.button === 0) this.mouse.down = false; });
    window.addEventListener('pointerdown', (e) => { this.dev = e.pointerType === 'touch' ? 'touch' : 'kb'; });
    // the letter printed on the toggle key (Q on QWERTY, A on AZERTY) when the browser can tell
    try { if (navigator.keyboard && navigator.keyboard.getLayoutMap) navigator.keyboard.getLayoutMap().then(m => { const k = m.get('KeyQ'); if (k) { this.keyQ = k.toUpperCase(); if (!this.layout) this.layout = k.toLowerCase() === 'a' ? 'azerty' : 'qwerty'; } }).catch(() => { }); } catch (e) { }
    canvas.addEventListener('mousedown', (e) => { if (Game.state === 'run' && Game.run && !UI.modalOpen() && Game.run.hudHit(e.clientX * Game.dpr, e.clientY * Game.dpr)) Game.run.toggleMoveSpells(); });
  },
  vector() {
    if (Game.debug.bot && Game.run) return Bot.vector(Game.run);
    let x = 0, y = 0; const k = this.keys;
    if (k.has('KeyA') || k.has('ArrowLeft')) x -= 1;
    if (k.has('KeyD') || k.has('ArrowRight')) x += 1;
    if (k.has('KeyW') || k.has('ArrowUp')) y -= 1;
    if (k.has('KeyS') || k.has('ArrowDown')) y += 1;
    if (this.touch.active) { x += this.touch.dx; y += this.touch.dy; }
    if (this.mouse && this.mouse.down && Game.run) {   // towards the cursor (full speed past 40 px, slower very close)
      const R = Game.run, px = (R.player.x - R.cam.x) * Game.zoom + Game.cw / 2, py = (R.player.y - 30 - R.cam.y) * Game.zoom + Game.ch / 2;
      const dx = this.mouse.x - px, dy = this.mouse.y - py, l = Math.hypot(dx, dy), k = Math.min(1, l / (40 * Game.dpr));
      if (l > 6) { x += dx / l * k; y += dy / l * k; }
    }
    const pads = navigator.getGamepads ? navigator.getGamepads() : [];
    for (const p of pads) {
      if (!p) continue;
      this.pad = true;
      const ax = p.axes[0] || 0, ay = p.axes[1] || 0;
      if (Math.abs(ax) > 0.4 || Math.abs(ay) > 0.4 || p.buttons.some(b => b && b.pressed)) this.dev = 'pad';
      if (Math.abs(ax) > 0.18) x += ax; if (Math.abs(ay) > 0.18) y += ay;
      if (p.buttons[14] && p.buttons[14].pressed) x -= 1; if (p.buttons[15] && p.buttons[15].pressed) x += 1;
      if (p.buttons[12] && p.buttons[12].pressed) y -= 1; if (p.buttons[13] && p.buttons[13].pressed) y += 1;
    }
    return { x, y };
  },
  // the letter of the movement-spell toggle key: A on AZERTY, Q on QWERTY (same physical key)
  toggleKey() { if (this.layout) return this.layout === 'azerty' ? 'A' : 'Q'; return this.keyQ || ((navigator.language || '').startsWith('fr') ? 'A' : 'Q'); },
  // R (RB / RT) dashes; L (LB / LT) switches the spells that move the character on and off
  padBtn(ids) {
    const pads = navigator.getGamepads ? navigator.getGamepads() : [];
    for (const p of pads) if (p) for (const i of ids) { const b = p.buttons[i]; if (b && (b.pressed || b.value > 0.5)) return true; }
    return false;
  },
  padDodge() { return this.padBtn([5, 7]); },
  padToggle() { return this.padBtn([4, 6]); },
  padAuto() { return this.padBtn([3]); },   // (0.60: Y; B is 'back' everywhere)
  // the direction pushed on the cross / left stick (one of U D L R), for the Konami code
  padDir() {
    const pads = navigator.getGamepads ? navigator.getGamepads() : [];
    for (const p of pads) if (p) {
      const b = i => p.buttons[i] && p.buttons[i].pressed, x = p.axes[0] || 0, y = p.axes[1] || 0;
      if (b(12) || y < -0.75) return 'U'; if (b(13) || y > 0.75) return 'D'; if (b(14) || x < -0.75) return 'L'; if (b(15) || x > 0.75) return 'R';
    }
    return null;
  },   // B: the bread / kamas auto-choice on / off
  padPause() {
    const pads = navigator.getGamepads ? navigator.getGamepads() : [];
    for (const p of pads) if (p && p.buttons[9] && p.buttons[9].pressed) return true;
    return false;
  },
};

// ---------------------------------------------------------------- game
const Bot = {
  vector(R) {
    const P = R.player; let x = 0, y = 0;
    for (const m of R.mobs) {
      if (m.dying) continue; const dx = P.x - m.x, dy = P.y - m.y, d2 = dx * dx + dy * dy;
      if (d2 > 260 * 260) continue; const d = Math.sqrt(d2) || 1; const w = (m.boss ? 3 : 1) * 3000 / (d2 + 400);
      x += dx / d * w; y += dy / d * w;
    }
    for (const e of R.eprojs) { const dx = P.x - e.x, dy = P.y - e.y, d2 = dx * dx + dy * dy; if (d2 < 120 * 120) { const d = Math.sqrt(d2) || 1; x += dx / d * 2; y += dy / d * 2; } }
    for (const t of R.teles) { if (t.kind === 'circle') { const dx = P.x - t.x, dy = P.y - t.y, d = Math.hypot(dx, dy) || 1; if (d < t.r + 30) { x += dx / d * 4; y += dy / d * 4; } } }
    // gems
    let best = null, bd = 380 * 380;
    for (const g of R.pickups) { const d = dist2(P.x, P.y, g.x, g.y); if (d < bd) { bd = d; best = g; } }
    if (best) { const dx = best.x - P.x, dy = best.y - P.y, d = Math.hypot(dx, dy) || 1; x += dx / d * 0.6; y += dy / d * 0.6; }
    if (R.door && Game.debug.tot) { const dx = R.door.x - P.x, dy = R.door.y - P.y, d = Math.hypot(dx, dy) || 1; x += dx / d * 3; y += dy / d * 3; }
    // bounds
    const b = R.bounds, m = 220;
    if (P.x < b.x0 + m) x += (b.x0 + m - P.x) / m * 2; if (P.x > b.x1 - m) x -= (P.x - b.x1 + m) / m * 2;
    if (P.y < b.y0 + m) y += (b.y0 + m - P.y) / m * 2; if (P.y > b.y1 - m) y -= (P.y - b.y1 + m) / m * 2;
    // circle around center when calm
    if (Math.hypot(x, y) < 0.3) { const a = R.time * 0.3; x += Math.cos(a) * 0.5; y += Math.sin(a) * 0.5; }
    const l = Math.hypot(x, y); return l > 1 ? { x: x / l, y: y / l } : { x, y };
  },
};
const Game = {
  debug: {},
  state: 'boot', run: null, C: null, icons: null, cw: 0, ch: 0, dpr: 1, zoom: 1, ui: 1, viewW: 1200, viewH: 700,
  // adaptive quality: the canvas resolution drops (and heavy effects thin out) when frames get slow, then climbs back
  resScale: 1, lowFx: false, minFx: false, _ft: 16.7, _adT: 0, _okT: 0, _cap: 1, zoomBase: 1, _zk: 0,
  async boot() {
    Store.load(); applyTheme();
    const S = Store.data.settings;
    LANG = (S.lang && LANGS.includes(S.lang)) ? S.lang : detectLang();
    document.documentElement.lang = LANG;
    this.canvas = document.getElementById('game');
    // with the PixiJS renderer (pixi_render.js, 0.62: the default) this canvas lies over the WebGL one: transparent
    PX.want = PX.wanted();
    this.ctx = this.canvas.getContext('2d', { alpha: PX.want });
    this.resize(); window.addEventListener('resize', () => this.resize());
    Input.init(this.canvas);
    UI.loading(0);
    const pxReady = PX.want ? PX.init(this.canvas) : null;
    const [C, spr, icimg, snd, icimg2] = await Promise.all([Assets.loadJSON('data/content.json'), Assets.loadJSON('data/sprites.json'), Assets.loadImg('assets/ui/icons.webp'), Assets.loadJSON('data/sounds.json'), Assets.loadImg('assets/ui/icons2.webp')]);
    const icimg3 = spr.icons3 ? await Promise.all([...Array(spr.icons3pages || 1)].map((_, i) => Assets.loadImg(`assets/ui/icons3${i ? '_' + i : ''}.webp`))) : null;
    // 0.92 (the Brigandin 'teleported' on his melee blows): some client casts end in a leap away from the spot (the
    // Brigandin's anim0: frames 10+ right, 8+ left), then snap back when the next pose starts: C.animCut keeps their start
    for (const sid in C.animCut || {}) for (const a in C.animCut[sid]) { const A = spr.chars[sid] && spr.chars[sid].anims[a]; if (A) A.f = A.f.slice(0, C.animCut[sid][a]); }
    SPR = spr; this.C = C; this.icons = new Atlas(icimg, { f: spr.icons }, icimg2, { f: spr.icons2 || {} }, icimg3, { f: spr.icons3 || {} });
    Object.assign(I18N, C.ui); Object.assign(TIPS, C.tips);
    if (PX._lostMsg) { const f = PX._lostMsg; PX._lostMsg = null; setTimeout(f, 0); }   // (0.94: WebGL lost while loading, pixi_render.js lose)
    Audio2.SND = snd;
    { // 0.53: Invocations left the shop: the kamas paid for its levels are given back
      const S = Store.data, lv = (S.passLv || {}).invocations || 0;
      const COST = C.spellCost || [180, 400, 680, 1000, 1380], refund = n => COST.slice(0, n).reduce((a, b) => a + b, 0);
      if (lv) { S.kamas += refund(lv); delete S.passLv.invocations; Store.save(); }
      for (const id in C.spells) if (C.spells[id].t === 'wheel' && (S.spellLv || {})[id]) { S.kamas += refund(S.spellLv[id]); delete S.spellLv[id]; Store.save(); }   // (and the Trool's token)
    }
    { // 0.60: masteries have 5 levels (they had 10): the levels above 5 are refunded at the price they were bought
      const S = Store.data, OLD = C.masteryCostOld || [], MAX = (C.masteryCost || []).length || 10; let back = 0;
      for (const w in S.mastery || {}) if (S.mastery[w] > MAX) { back += OLD.slice(MAX, S.mastery[w]).reduce((a, b) => a + b, 0); S.mastery[w] = MAX; }
      if (back) { S.kamas += back; Store.save(); this._bootNote = T('mastery_refund', { n: fmtNum(back) }); }
    }
    if (Store.data.equip && Store.data.equip.hat === '16_261') { Store.data.equip.hat = null; Store.save(); }   // (0.60: the Chapeau de Lonne left the game)
    this.unlockByTot(false);   // (0.68: profiles that beat ToT before the Kwak Nest existed get it)
    { // 0.65: the Polykrome skins left the game (C.removedSkins = id -> shop price): refunded, taken off
      const S = Store.data, RM = C.removedSkins || {}; let back = 0;
      if (S.owned && S.owned.some(i => i in RM)) { for (const i of S.owned) if (i in RM) back += RM[i]; S.owned = S.owned.filter(i => !(i in RM)); }
      for (const k in S.equip || {}) if (S.equip[k] in RM) S.equip[k] = null;
      if (back) { S.kamas += back; this._bootNote = T('skins_refund', { n: fmtNum(back) }); }
      Store.save();
    }
    { // zones were reordered by level: anything before an unlocked zone is unlocked too
      const S = Store.data, vis = C.maps.filter(m => !m.hidden); let top = -1;
      vis.forEach((m, i) => { if (S.unlocked.includes(m.id)) top = i; });
      let ch = false; for (let i = 0; i <= top; i++) if (!S.unlocked.includes(vis[i].id)) { S.unlocked.push(vis[i].id); ch = true; }
      if (ch) Store.save();
    }
    UI.loading(0.5);
    try { await Promise.all([document.fonts.load('12px Dofus'), document.fonts.load('bold 12px DofusBold'), document.fonts.load('12px RetroNum'), document.fonts.load('900 12px Cinzel'), document.fonts.load('700 12px Cinzel')]); } catch (e) { }   // (0.85: RetroNum = the damage numbers; 0.95: Cinzel = the announcements, drawn on canvases)
    if (pxReady) await pxReady;
    UI.loading(1);   // (0.44: the boss chest's sheet loads with the runs, no longer before the menu)
    Audio2.setVolumes(S.musicOff ? 0 : S.music, S.sfx);
    this._uiSnd = () => { Audio2.init(); Audio2.preload(Object.values(Audio2.SND.ui)); };
    window.addEventListener('pointerdown', this._uiSnd, { once: true }); window.addEventListener('keydown', this._uiSnd, { once: true });
    this.state = 'menu';
    const q = new URLSearchParams(location.search);
    for (const [k, v] of q) this.debug[k] = isNaN(+v) ? v : +v;
    if (this.debug.autostart && this.debug.fresh) Store.data = Store.defaults();
    // (?q=sd|hd|uhd|k4: Game.quality reads it first, the profile's setting is left alone)
    this.setFxFlags(); this.resize();
    if (this.debug.autostart) {
      Store.data.unlocked = Game.C.maps.map(m => m.id);
      this.startRun({ cls: this.debug.cls || 'iop', sex: this.debug.sex || 0, colors: baseColors(Game.C.classes.find(c => c.id === (this.debug.cls || 'iop')), this.debug.sex || 0), hat: this.debug.hat || null, cape: this.debug.cape || null, pet: this.debug.pet || null, shield: this.debug.shield || null, map: this.debug.map || 'astrub', hard: !!this.debug.hard, infinite: !!this.debug.infinite });
    } else { UI.mainMenu(); if (this._bootNote) { const n = this._bootNote; setTimeout(() => toast(n), 900); } }
    this.preloadIdle();
    let last = performance.now();
    const loop = (now) => {
      // (0.34: the performance mode no longer caps at 30 fps — it felt choppy; its savings are the smaller buffer, the
      // half-size sheets and the lighter effects, and the adaptive resolution below still steps in on a slow machine)
      requestAnimationFrame(loop);   // (0.48: first, so that an error in one frame never stops the game)
      const raw = (now - last) / 1000, dt = Math.min(0.05, raw); last = now;
      try { this.adapt(raw); this.frame(dt); } catch (e) { if (!this._frameErr) { this._frameErr = String((e && e.stack) || e); console.error(e); } }   // (tests read Game._frameErr)
    };
    requestAnimationFrame(loop);
  },
  // 0.32: every spell / weapon effect (58 small sheets) and the last played class are loaded in the background once the
  // menu is up, three at a time, so no animation pops in late the first time it plays (shop previews, the first run)
  preloadIdle() {
    const S = Store.data || {}, ids = Object.keys(SPR.fx || {}).filter(k => !k.startsWith('ui')), cls = Game.C.classes.find(c => c.id === S.lastClass);   // (0.61: not the dice scene's big copies, loaded by it)
    // (0.44: paused during a run: its loads are the run's own, decoding more mid-fight caused hitches)
    const next = () => { if (this.state === 'run') { setTimeout(next, 2000); return; } const id = ids.shift(); if (id === undefined) return; FxSheets.load(isNaN(+id) ? id : +id).then(next, next); };
    // 0.93 (stress tests: the last class's sheets were decoded in the first seconds of a run started right away, frozen
    // frames): only while a menu shows
    const chars = () => { if (this.state === 'run' || this.state === 'loading') return; if (cls) for (const sid of new Set(cls.sprites)) new CharSprite(sid, randomColors(), null, null, null).load().then(sp => sp.dispose(), () => { }); };
    setTimeout(() => { next(); next(); next(); chars(); }, 1200);   // (0.93: only the sheets decoded ahead, kept a while by CharSprite.idle; the sprite itself let go)
  },
  // 0.34: once everything is maxed, a level gives bread or kamas. The choice made can be kept (auto) or asked again:
  // R / B / a click on its icon by the dash feather switches between the two
  toggleAutoPick() {
    const S = Store.data.settings, R = this.run;
    if (S.autoPick) { S.lastAutoPick = S.autoPick; S.autoPick = null; }
    else S.autoPick = S.lastAutoPick || 'bread';
    Store.save(); Audio2.blip('click');
    if (R) R.chat(S.autoPick ? T('auto_on', { n: S.autoPick === 'kamas' ? T('take_kamas') : T('take_bread') }) : T('auto_off2'), '#ffd27a');
  },
  // 0.44: the picture quality (options: SD / HD / UHD, see QUALITY in assets.js) instead of the performance mode
  // 0.93: by default the exe draws at the screen's own resolution (4K cap: native up to 2160p) and the web version
  // at 1080p (its buffer never larger, whatever the devicePixelRatio: resize caps it by QUALITY); a quality picked in the
  // options (settings.qualityUser) or asked in the address (?q=) wins. The menus keep their 16:9 layout either way (--uiz)
  quality() {
    const S = Store.data && Store.data.settings, d = this.debug && this.debug.q;
    if (QUALITY[d]) return d;
    if (S && S.qualityUser && QUALITY[S.quality]) return S.quality;
    return IS_APP ? 'k4' : 'hd';
  },
  Q() { return QUALITY[this.quality()]; },
  setQuality(q) {
    if (!QUALITY[q] || q === this.quality()) return;
    Store.data.settings.quality = q; Store.data.settings.qualityUser = 1; Store.save();   // (0.93: the player's own choice from now on)
    this.setFxFlags(); this.resScale = 1; this._cap = 1; this.resize();
    this.requality();
  },
  // 0.95 (simple options for low-end machines): the visual effects, apart from the picture quality — 'full' (the
  // adaptive step below may still lighten them), 'low' (Game.lowFx for good: fewer particles, glows and sparks), 'min'
  // (also no monster shadows, no effects redrawn behind the scenery, fewer particles and numbers). Telegraphs, projectiles
  // and ranges are never cut. ?fx=full|low|min reads first (perf_probe)
  fxLevel() {
    const d = this.debug && this.debug.fx, S = Store.data && Store.data.settings, ok = v => v === 'full' || v === 'low' || v === 'min';
    return ok(d) ? d : S && ok(S.fx) ? S.fx : 'full';
  },
  setFxFlags() { const l = this.fxLevel(); this.lowFx = this.Q().fx === 0 || l !== 'full'; this.minFx = l === 'min'; },
  setFx(v) { Store.data.settings.fx = v; Store.save(); this.setFxFlags(); },
  // 0.95: three camera distances in the options, 10 % further / the usual one / 10 % closer, eased in ~0.4 s
  zoomK() { const S = Store.data && Store.data.settings, z = S && S.zoom; return z === 'far' ? 0.9 : z === 'close' ? 1.1 : 1; },
  setZoom(v) { Store.data.settings.zoom = v; Store.save(); },
  applyZoom() { this.zoom = this.zoomBase * this._zk; this.viewW = this.cw / this.zoom; this.viewH = this.ch / this.zoom; },
  easeZoom(dt) { const k = this.zoomK(); if (this._zk === k) return; this._zk = Math.abs(k - this._zk) < 0.002 ? k : this._zk + (k - this._zk) * Math.min(1, dt * 9); this.applyZoom(); },
  // every sheet already loaded again at the new size, in place (the monsters, effects and characters on screen keep
  // their sheet objects); the old sizes are freed
  async requality() {
    const k = lowK(), jobs = [], whites = {};
    for (const key in MobSheets.c) {
      const sh = MobSheets.c[key]; if (!sh || !sh.img || (sh.img._k || 1) === k) continue;
      const u = MobSheets.url(key), old = sh.img._k || 1;
      jobs.push(Assets.loadImg(u, k).then(img => { if (!img) return; sh.img = img; for (const n of Object.keys(sh)) if (n.startsWith('_tint')) delete sh[n]; sh.white = whites[u] || (whites[u] = MobSheets.whites[u] = whiteVersion(img, 0.5)); Assets.release(u, old); }));
    }
    for (const id in FxSheets.c) {
      const sh = FxSheets.c[id]; if (!sh || !sh.img || (sh.img._k || 1) === k) continue;
      const u = `assets/fx/${id}.webp`, old = sh.img._k || 1;
      jobs.push(Assets.loadImg(u, k).then(img => { if (img) { sh.img = img; Assets.release(u, old); } }));
    }
    const now = performance.now();
    for (const cs of CharSprite.live) { if (now - (cs._seen || 0) > 8000) { CharSprite.live.delete(cs); continue; } jobs.push(cs.requality()); }
    jobs.push(AccLib.requality());
    const R = this.run;
    if (R && R.reloadTiles) jobs.push(R.reloadTiles());
    await Promise.all(jobs);
    if (typeof _redGlyph !== 'undefined') _redGlyph.clear();
  },
  adapt(raw) {
    const R = this.run;
    if (this.state !== 'run' || !R || this.paused || UI.modalOpen() || raw > 0.25 || document.hidden || this.debug.speed > 1) { this._adT = 0; return; }
    this._ft = this._ft * 0.94 + raw * 1000 * 0.06; this._adT += raw;
    if (this._adT < 2.5) return;
    const base = Math.min(2, window.devicePixelRatio || 1), minS = Math.max(0.7, 0.75 / base);   // (0.38: never blurrier than 70 %)
    if (this._ft > 23 && (this.resScale > minS + 0.01 || !this.lowFx)) { // under ~43 fps: cheaper frames
      if (!this.lowFx) this.lowFx = true;
      else { this._cap = this.resScale; this.resScale = Math.max(minS, this.resScale - 0.15); this.resize(); }
      this._adT = 0; this._okT = 0;
    } else if (this._ft < 17.8) { // comfortably fast: climb back slowly, never above a level that was too slow before
      this._okT += raw;
      if (this._okT > 10) { this._okT = 0; this._adT = 0;
        if (this.resScale < Math.min(1, this._cap - 0.01)) { this.resScale = Math.min(1, this._cap - 0.05, this.resScale + 0.1); this.resize(); }
        else if (this.lowFx && this.resScale >= 0.99 && this.Q().fx > 0 && this.fxLevel() === 'full') this.lowFx = false;
        this._cap = Math.min(1, this._cap + 0.05);
      }
    } else this._okT = 0;
  },
  resize() {
    const old = this.dpr;
    const w = window.innerWidth, h = window.innerHeight, Q = this.Q();
    // 0.44: the render buffer never goes past the quality's size (720p / 1080p / 1440p, on the screen's long / short sides)
    this.dpr = Math.min(Math.min(2, window.devicePixelRatio || 1), Q.w / Math.max(w, h), Q.h / Math.min(w, h)) * (this.resScale || 1);
    if (Input.touch && Input.touch.id !== null && old && old !== this.dpr) { const k = this.dpr / old; Input.touch.sx *= k; Input.touch.sy *= k; }
    this.canvas.width = Math.round(w * this.dpr); this.canvas.height = Math.round(h * this.dpr);
    this.cw = this.canvas.width; this.ch = this.canvas.height;
    // world zoom: show ~680 world px vertically (min 560 wide)
    this.zoomBase = Math.min(this.ch / 600, this.cw / 620) * 0.76;   // 0.22: about 25% more of the world around the character (0.65: 5 % further out)
    if (!this._zk) this._zk = this.zoomK(); this.applyZoom();   // (0.95: × the options' camera distance, easeZoom)
    this.ui = clamp(Math.min(this.cw / 1280, this.ch / 720) * 1.0, 0.7, 3);   // (0.85: up to 4K = x3, the same proportions as QHD)
    // DOM menus: designed for 1280x720 (16:9), scaled up uniformly on bigger screens (never shrunk: phones keep their layout)
    const uiz = clamp(Math.min(w / 1280, h / 720), 1, 3);   // (0.85: 3 = 4K UHD, every menu keeps its 16:9 proportions)
    if (uiz !== this._uiz) { this._uiz = uiz; document.documentElement.style.setProperty('--uiz', uiz.toFixed(3)); }
  },
  // clickable pause / menu button (same as Esc) shown during a run
  pauseBtn() {
    if (!this._pb) {
      const b = document.createElement('button'); b.id = 'pausebtn'; b.textContent = '❚❚';
      b.addEventListener('click', (e) => { e.preventDefault(); e.stopPropagation(); if (this.state === 'run' && !UI.levelUpOpen) { Audio2.blip('click'); this.togglePause(); } });
      b.addEventListener('pointerdown', (e) => e.stopPropagation());
      document.body.append(b); this._pb = b;
    }
    const R = this.run, show = this.state === 'run' && R && !R.over && !this.paused && !UI.modalOpen();
    const k = this.ui / this.dpr, want = show ? `${Math.round(84 * k)}|${Math.round(12 * k)}|${Math.round(42 * k)}` : 'none';
    if (want !== this._pbState) {
      this._pbState = want;
      if (!show) this._pb.style.display = 'none';
      else { const [tp, rt, sz] = want.split('|'); Object.assign(this._pb.style, { display: 'block', top: tp + 'px', right: rt + 'px', width: sz + 'px', height: sz + 'px', lineHeight: (sz - 4) + 'px', fontSize: Math.round(sz * 0.38) + 'px' }); this._pb.title = T('pause_btn'); }
    }
    // 0.34: the fullscreen button under it, with the key / button that does it on this device (F, the pad's View button)
    if (!this._fb) {
      const b = document.createElement('button'); b.id = 'fsbtn'; b.innerHTML = '<span class="fs-ic">⛶</span><span class="fs-key"></span>';
      b.addEventListener('click', (e) => { e.preventDefault(); e.stopPropagation(); Audio2.blip('click'); toggleFullscreen(); });
      b.addEventListener('pointerdown', (e) => e.stopPropagation());
      document.body.append(b); this._fb = b;
    }
    const fw = show ? want + '|' + Input.dev : 'none';
    if (fw !== this._fbState) {
      this._fbState = fw;
      if (!show) this._fb.style.display = 'none';
      else { const [tp, rt, sz] = want.split('|').map(Number); Object.assign(this._fb.style, { display: 'block', top: (tp + sz + 8 * k) + 'px', right: rt + 'px', width: sz + 'px', height: sz + 'px', fontSize: Math.round(sz * 0.42) + 'px' });
        this._fb.querySelector('.fs-key').textContent = Input.dev === 'pad' ? '⧉' : Input.dev === 'touch' ? '' : 'F'; this._fb.title = T('fullscreen'); }
    }
  },
  frame(dt) {
    if (PX.shown && this.state !== 'run') PX.hide();   // (0.61: the WebGL layer shows the runs only)
    this.pauseBtn(); this.easeZoom(dt);
    Nav.poll(dt);
    const ctx = this.ctx;
    if (this.state === 'run' && this.run) {
      const R = this.run;
      const sp = this.debug.speed || 1;
      if (sp > 1) { for (let i = 0; i < sp; i++) { if (UI.modalOpen() && this.debug.bot) UI.botPick(); if (!this.paused && !UI.modalOpen()) R.update(1 / 60); } this._fc = (this._fc || 0) + 1; if (this._fc % 4 === 0 || !this.debug.nodraw) R.draw(ctx); }
      else {
        if (R.tofuShowUntil && performance.now() >= R.tofuShowUntil) { R.tofuShowUntil = 0; Audio2.stopJingle(0.6); for (const m of R.mobs) if (m._sh) { m.sh = m._sh; m._sh = null; } }
        if (UI.modalOpen() && this.debug.bot) UI.botPick(); if (R.cine && !this.paused) R.tickCine(dt); else if (!this.paused && !UI.modalOpen() && !R.tofuShowUntil && !(R.reviveHold > performance.now()) && !R.frozenByHit()) R.update(dt * R.timeK()); R.draw(ctx);   // (0.60: hit-stop / slow motion, juice.js)   // (a cinematic freezes the run: events.js)
      }
      if (Input.padPause() && !this._padP) { this._padP = true; this.togglePause(); } else if (!Input.padPause()) this._padP = false;
      const pd = Input.padDodge(); if (pd && !this._padD && !this.paused && !UI.modalOpen()) R.player.dodge(); this._padD = pd;
      const pt = Input.padToggle(); if (pt && !this._padT && !this.paused && !UI.modalOpen()) R.toggleMoveSpells(); this._padT = pt;
      { const pd2 = Input.padDir(); if (pd2 && pd2 !== this._padK) this.konamiStep(pd2); this._padK = pd2; }   // (Konami with the controller)
      const pa = Input.padAuto(); if (pa && !this._padA && !this.paused && !UI.modalOpen()) this.toggleAutoPick(); this._padA = pa;
      if (this._pendingEx && !UI.modalOpen() && !this.paused) { const [d, f] = this._pendingEx; this._pendingEx = null; UI.exploitMenu(d, f); }
      if (this._pendingTailor && !UI.modalOpen() && !this.paused) { const p = this._pendingTailor; this._pendingTailor = null; UI.tailorMenu(p); }
    } else if (this.state === 'tot' && Tot.active) {
      Tot.update(dt); Tot.draw(ctx);
    } else {
      UI.drawMenuBg(ctx, dt);
    }
  },
  // Konami code (up up down down left right left right) during a run: 5 seconds where the game stops and everyone is a Tofu
  // (0.36: arrows or ZQSD / WASD, the controller's cross or stick, or the mouse: wheel up up down down, then left / right
  // clicks for left / right)
  konami(e) {
    const d = { ArrowUp: 'U', ArrowDown: 'D', ArrowLeft: 'L', ArrowRight: 'R', KeyW: 'U', KeyS: 'D', KeyA: 'L', KeyD: 'R' }[e.code];
    if (d && !e.repeat) this.konamiStep(d);
  },
  konamiStep(d) {
    const SEQ = 'UUDDLRLR', R = this.run;
    if (this.state !== 'run' || !R || R.konamiDone || this.paused || UI.modalOpen()) { this._kc = 0; return; }
    this._kc = d === SEQ[this._kc || 0] ? (this._kc || 0) + 1 : (d === SEQ[0] ? 1 : 0);
    if (this._kc < SEQ.length) return;
    this._kc = 0; R.konamiDone = true; R.tofuShowUntil = performance.now() + 5000;
    const sh = MobSheets.c[this.C.monsters.tofu.sprite];
    if (sh) for (const m of R.mobs) { m._sh = m.sh; m.sh = sh; }
    R.tofuShowAt = performance.now(); Audio2.sfx('EVENT', 0.8); Audio2.jingle('cls_roublard');   // (0.34: dark screen, the Trool fair tune, a big 'Tofu !': render.js drawKonami)
  },
  onKey(e) {
    this.konami(e);
    if (e.code === 'Escape' || e.code === 'KeyP') {
      if (this.state === 'run') { if (UI.levelUpOpen) { if (e.code === 'Escape' && UI._luBack) UI._luBack(); } else this.togglePause(); }   // (0.60: Échap leaves the Bannir mode)
      else if (this.state === 'menu') Nav.back();   // (0.85: like the controller's B: an open window closes first, then the screen)
    }
    // 0.68: A (AZERTY) / Q (QWERTY) — the same key — closes a window / goes back in the menus, like the controller's
    // B (Échap also leaves the full screen); during a run it only closes the open windows (outside them: the move spells)
    else if (e.code === 'KeyQ' && !e.repeat && !e.ctrlKey && !e.metaKey && !e.altKey && !(e.target && /INPUT|SELECT|TEXTAREA/.test(e.target.tagName))
      && (this.state === 'menu' || (this.state === 'run' && UI.modalOpen() && !UI.levelUpOpen))) { e.preventDefault(); Nav.back(); }
    UI.secretKey(e);
  },
  // 0.68: the zones opened by beating ToT once (unlockBy 'tot': the Hidden Kwak Nest)
  unlockByTot(say) {
    const S = Store.data; if (!(S.tot > 0)) return;
    for (const m of this.C.maps.filter(m => m.unlockBy === 'tot' && !(S.unlocked || []).includes(m.id))) { S.unlocked.push(m.id); Store.save(); if (say) toast(T('kwak_found'), 6000); }
  },
  autoPause() { if (this.state === 'run' && !this.paused && !UI.modalOpen() && this.run && !this.run.over) this.togglePause(); },
  togglePause() {
    if (!this.run || this.run.over) return;
    if (this.paused) { this.paused = false; UI.closeModal(); }
    else if (!UI.modalOpen()) { this.paused = true; for (const c of this.run.chats) c.t = this.run.time; UI.pauseMenu(); }   // (0.36: pausing shows the chat again)
  },
  async startRun(opts) {
    if (opts.hard && !Store.hardOk() && !this.debug.hard) opts.hard = false;   // 0.95: Difficile opens once Grobe is won — every way into a run checks it here (the play screen greys it)
    this.state = 'loading';
    Audio2.stopJingle(0, true);
    UI.clear(); UI.loading(0, true);
    const t0 = performance.now();
    if (this.run) { this.run.dispose(); this.run = null; }   // (0.93: 'Rejouer': the last run's characters let go first)
    const run = new Run(this.C, opts);
    await run.load(p => UI.loading(p, true));
    this.warmTextures(run); AccLib.trim();   // (0.44: the run's accessories live in their own small atlases: the big sheets are freed)
    // the loading screen stays at least 2 s, then waits for the Play button (time to read the tip)
    if (!this.debug.autostart) {
      const wait = 2000 - (performance.now() - t0); if (wait > 0) await new Promise(r => setTimeout(r, wait));
      await UI.loadingReady();
    }
    this.run = run; this.paused = false;
    if (this.debug.t) run.time = this.debug.t;
    if (this.debug.lv) { for (let i = 0; i < this.debug.lv; i++) { const o = run.upgradeOptions(1)[0]; if (o) run.applyUpgrade(o); } }
    if (this.debug.weapon && weaponById(run.C, this.debug.weapon)) {   // ?weapon=god_rod&fusion=intelligence (level 6, finale, fusion)
      run.applyUpgrade({ kind: 'weapon', id: this.debug.weapon }); for (let i = 1; i < 6; i++) run.weapon.levelUp();
      const E = ((run.C.weaponEvo || {})[this.debug.weapon] || [])[0]; if (E && this.debug.fusion) run.applyUpgrade({ kind: 'wevo', id: E.id });
      if (this.debug.fusion) run.applyFusion(this.debug.fusion);
    }
    if (this.debug.spells) for (const sp of String(this.debug.spells).split(',')) { const [id, lv] = sp.split(':'); if (!run.C.spells[id]) continue; if (run.C.spells[id].t === 'wheel') { run.trool(); continue; } const s = run.spells.find(s => s.def.id === id) || run.addSpell(id); for (let i = 1; i < (+lv || 1); i++) s.levelUp(); }   // ?spells=kokoko:6,prouts
    UI.clear();
    this.state = 'run';
    // 0.53: everything is loaded (loading screen): a 3, 2, 1, GO! over the frozen map, the music starts on GO
    if (!this.debug.autostart || this.debug.cd) { [run.cam.x, run.cam.y] = run.camTarget(); run.startCine('countdown', {}, () => Audio2.playMusic(run.map.music)); }
    else Audio2.playMusic(run.map.music);
    Store.data.lastClass = opts.cls; Store.data.lastSex = opts.sex; Store.data.lastMap = opts.map; Store.save();
    // 0.94: once at the start, in the chat: what Difficile changes; on Nowel's zone that it gives no kamas, again
    // every 2:30 of run time (Run.after: it goes with the run — paused with it, gone when it ends, one chain per run)
    if (run.hard) run.chat(T('hard_info'), '#ff8a6a');
    if (run.map.nowel) { const note = () => { if (this.run !== run || run.over) return; run.chat(T('nowel_info', { n: L(run.map.name) }), '#9fe0ff'); run.after(150, note); }; note(); }
    // 0.95: the beginners' help, once in the chat; Ganymède's tutorial 5 s of run time into the zone (after the
    // countdown: the run clock is frozen during it), until seen to its end (Store.data.tuto); ?gany=<zone|hard> shows one
    const tut = id => run.after(this.debug.gany ? 1 : 5, () => { if (this.run === run && !run.over && !run.player.dead && !UI.modalOpen()) UI.ganyScene(run, id); });
    if (run.aid) {
      run.chat(T('aid_info', { g: L(this.C.gany.name), map: L(run.map.name), h: Math.round((1 - run.aid.hp) * 100), d: Math.round((1 - run.aid.dmg) * 100) }), '#9cff9a');
      if (!(Store.data.tuto || {})[run.map.id] && !this.debug.bot && !this.debug.gany && (!this.debug.autostart || this.debug.tuto)) tut(run.map.id);   // (the tests' autostart runs: only with ?tuto=1 — it covered t_pixicmp's scenes)
    }
    if (this.debug.gany) tut(this.debug.gany);
  },
  // draw every texture of the run once, tiny, behind the loading screen: the GPU upload happens now, not mid-fight
  warmTextures(run) {
    const ctx = this.ctx; ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 0.01;
    // (0.61: with PixiJS the ground and the monster sheets go to its own textures, not the 2D canvas's: they would sit
    // twice in the video memory; the 2D canvas still draws the chests and the Doom's corbacs from monster sheets)
    if (PX.on) PX.warm(run);
    const imgs = PX.on ? [Game.icons && Game.icons.img, Game.icons && Game.icons.img2, run.charSprite && run.charSprite.sheet && run.charSprite.sheet.img] : [...Object.values(run.tiles), run.mini, Game.icons && Game.icons.img, Game.icons && Game.icons.img2, run.charSprite && run.charSprite.sheet && run.charSprite.sheet.img];
    for (const [key, sh] of Object.entries(MobSheets.c)) if (sh && (!PX.on || key === Game.C.chestSprite || key === (Game.C.doom || {}).crowSprite)) imgs.push(sh.img, sh.white);
    for (const sh of Object.values(FxSheets.c)) if (sh) imgs.push(sh.img);
    for (const c of AccLib.cache.values()) imgs.push(c.img);
    for (const im of imgs) if (im && im.width) try { ctx.drawImage(im, 0, 0, 2, 2); } catch (e) { }
    ctx.globalAlpha = 1;
  },
  levelUp() {
    const R = this.run; R.juiceLevel();
    R.rings.push({ x: R.player.x, y: R.player.y, r0: 10, r1: 90, t0: R.time, dur: 0.6, color: '#ffe066' });
    for (let i = 0; i < 24; i++) R.particles.push({ x: R.player.x + rand(-20, 20), y: R.player.y - rand(0, 60), vx: rand(-30, 30), vy: rand(-140, -60), t: 0, life: rand(0.5, 1), c: pick(['#ffe066', '#fff6c8', '#ffd24a']), s: rand(2, 4) });
    Audio2.blip('level');
    const luck = R.stats.luck;
    const n = Math.random() < (luck - 1) * 0.5 + 0.1 ? 4 : 3;
    Prog.check(R);
    const opts = R.upgradeOptions(n);
    if (!opts.length) {
      R.maxedAll = true;   // (the bread / kamas icon shows up in the HUD)
      const auto = Store.data.settings.autoPick;
      if (auto) { R.applyUpgrade({ kind: auto }); return; }
      UI.levelUpMaxed(R);
    } else UI.levelUpMenu(R, opts);
  },
  openChest(n) {
    const R = this.run; const got = []; const before = R.kamas;
    const count = n >= 5 ? (Math.random() < 0.3 * R.stats.luck ? 5 : 3) : n >= 3 ? 3 : 1;
    for (let i = 0; i < count; i++) {
      const o = R.upgradeOptions(1, true)[0];   // chests only improve what was already picked
      if (o) { R.applyUpgrade(o); got.push(o); }
      else { const k = { kind: 'kamas' }; R.applyUpgrade(k); got.push(k); }
    }
    const k = R.addKamas(randi(4, 12) * (1 + R.mapIdx) * (n >= 3 ? 2 : 1));
    if (R.ps) R.ps.chests++;
    const kamasOnly = got.every(o => o.kind === 'kamas');
    if (kamasOnly) { // nothing left to learn: no pop-up, just a line in the chat
      R.chat(T('chest_kamas', { n: fmtNum(R.kamas - before) }), '#ffd700'); Audio2.blip('coin'); return;
    }
    Audio2.sfx('EVENT', 0.6);
    UI.chestMenu(R, got, k);
  },
  doorPrompt() {
    if (this.debug.bot) { this.run.door = null; this.run.doorDone = true; this.enterTot(); return; }
    // once his Dofus was won (in any run), ToT also offers a shortcut: his bonus at once, with a 30 s slap (-50% damage)
    const won = ((Store.data.dofus || {}).ocre || 0) > 0;
    UI.doorMenu(() => { this.run.door = null; this.run.doorDone = true; this.enterTot(); }, won ? () => { this.run.door = null; this.run.doorDone = true; this.totShortcut(); } : null);
  },
  totShortcut() {
    const R = this.run, C = this.C, buff = pick(C.totBuffs || [{ id: 'degats', stat: 'might', v: 0.1, icon: 'Icon_33', name: 'Dégâts' }]);
    R.totBuff = buff; R.weakUntil = R.time + 30; R.recompute();
    R.banner(T('tot_slap'), '#ff9a8a', true); R.chat(T('tot_buff', { b: L(buff.name) }), '#e0b0ff'); R.chat(T('tot_slap'), '#ff8a65');
    R.text(R.player.x, R.player.y - 80, '-50%', '#ff6a6a', 18); Audio2.sfx('EVENT', 0.7);
  },
  enterTot() {
    const R = this.run; if (R.portalRun) Prog.add('portals');
    this.state = 'tot';
    Tot.start(R, (won, rw) => {
      this.state = 'run';
      if (won) {
        rw = rw || {};
        // ToT's Dofus only for a flawless 3-0; once it is owned (or after a mistake) he gives a bonus for the run, or very rarely a Dragodinde
        const dof = this.C.dofus.find(d => d.id === 'ocre');
        // ToT hands his Dofus over at once (nothing to pick up)
        if (rw.kind === 'dofus' && dof && !R.dofus.includes(dof)) { R.collect({ kind: 'dofus', v: 'ocre' }); R.celebrateDofus(dof, R.player.x, R.player.y, 'ToT'); }
        else if (rw.kind === 'drago') { R.spawnDrago(); R.banner(T('tot_rare'), '#ffd24a'); R.chat(T('tot_drago', { n: L(this.C.drago.name) }), '#ffd24a'); }
        else if (rw.buff) { R.totBuff = rw.buff; R.recompute(); R.banner('ToT : +10% ' + L(rw.buff.name), '#e0b0ff', true); R.chat(T('tot_buff', { b: L(rw.buff.name) }), '#e0b0ff'); }
        R.dropPickup('chest', R.player.x - 30, R.player.y, 3);
        const k = this.C.totKamas || 50; R.kamas += k; R.text(R.player.x, R.player.y - 80, '+' + k + ' K', '#ffd700', 16);
        Store.data.tot = (Store.data.tot || 0) + 1; Store.save(); Prog.check(R);
        Game.unlockByTot(true);   // (0.68: the Hidden Kwak Nest)
        if (rw.kind === 'dofus') R.chat(T('tot_win'), '#e0b0ff');
      } else {
        R.chat(T('tot_lose'), '#e0b0ff');
        R.player.hp = Math.max(1, R.player.hp * 0.7);
      }
      Audio2.playMusic(R.doom || R.bossAlive.some(b => b.def.final) ? R.map.boss_music : R.map.music);
    });
  },
  dofusExploit(dof, from) {
    if (this.state !== 'run' || !this.run || this.run.over) return;
    if (UI.modalOpen() || this.paused) { this._pendingEx = [dof, from]; return; }   // shown once the level-up / pause closes
    UI.exploitMenu(dof, from);
  },
  // Manuel du Tailleur picked up: the slot machine pauses the game (after any level-up / pause screen)
  tailorWin(prize) {
    if (this.state !== 'run' || !this.run || this.run.over) return;
    if (UI.modalOpen() || this.paused) { this._pendingTailor = prize; return; }
    UI.tailorMenu(prize);
  },
  runOver(victory, unlocked) {
    const R = this.run;
    window.RESULT = { victory, time: R.time, level: R.level, kills: R.kills, kamas: R.kamas, cls: R.cls.id, map: R.map.id, spells: R.spells.map(s => s.def.id + ':' + s.level), dofus: R.dofus.map(d => d.id) };
    const show = () => UI.runOverMenu(this.run, victory, unlocked);
    if (R.hardUnlockedNow && this.C.gany && !this.debug.bot) { R.hardUnlockedNow = false; setTimeout(() => UI.ganyScene(R, 'hard', show), 600); }   // (0.95: Grobe won the first time: Ganymède opens Difficile)
    else setTimeout(show, victory ? 300 : 0);
  },
  toMenu() {
    if (this.run) this.run.dispose(); this.run = null; this.state = 'menu'; this.paused = false;
    UI.clear(); UI.mainMenu();
  },
};
window.addEventListener('load', () => Game.boot().catch(e => { console.error(e); const el = document.getElementById('loading-text'); if (el) el.textContent = 'Erreur: ' + e.message; }));

