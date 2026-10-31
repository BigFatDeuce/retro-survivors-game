'use strict';
// ---------------------------------------------------------------- DOM UI
const $ = (sel, root = document) => root.querySelector(sel);
function h(tag, attrs = {}, ...kids) {
  const e = document.createElement(tag);
  for (const k in attrs) {
    const v = attrs[k];
    if (k === 'class') e.className = v; else if (k === 'style' && typeof v === 'object') { for (const s in v) if (s.startsWith('--')) e.style.setProperty(s, v[s]); else e.style[s] = v[s]; }   // (CSS variables need setProperty)
    else if (k.startsWith('on')) e.addEventListener(k.slice(2), v); else if (v !== undefined && v !== null && v !== false) e.setAttribute(k, v);
  }
  for (const kid of kids.flat()) if (kid !== null && kid !== undefined && kid !== false) e.append(kid.nodeType ? kid : document.createTextNode(String(kid)));
  return e;
}
function btn(label, onclick, cls = '') { return h('button', { class: 'btn ' + cls, onclick: (e) => { Audio2.init(); Audio2.resume(); Audio2.blip('click'); onclick(e); } }, label); }
// item pictures are drawn at the pixel size they are shown at (menus are zoomed on big screens): never upscaled in the page
// (0.60: drawn at the exact device size: the page never resamples the picture again)
function iconPx(size) { const k = Math.min(4, Math.max(1, (Game._uiz || 1) * (window.devicePixelRatio || 1))); return Math.max(16, Math.round(size * k)); }
function iconImg(name, size = 40, cls = '') { const im = h('img', { src: Game.icons.dataURL(name, iconPx(size)), width: size, height: size, class: 'ic ' + cls, draggable: 'false' }); return im; }
// 0.98.1 (the first level-up froze the game ~0.25 s: each card picture was made and PNG-encoded on the spot): the pictures a
// level-up card of this run may show — its class's spells, the common spells, the fusions, the characteristics, the
// weapons, at the sizes the cards show them (iconImg) — and the reroll die's sheets, made ahead in the idle moments of the
// run's first seconds (the countdown gives plenty)
// 0.98.2: from the loading screen on (Game.startRun); its promise ends when all is made: the countdown waits for it
function warmIcons(R) {
  const C = R.C, todo = [], add = (n, s) => { if (n) todo.push([n, s]); };
  for (const sid of [...R.cls.spells, ...(C.globalSpells || []).map(g => g.id)]) { const sp = C.spells[sid]; if (sp) for (const z of [48, 24, 20, 18]) add('sp_' + sp.icon, z); }
  for (const f of (C.spellFusions || []).filter(f => sfusionOf(f, R.cls.id))) { const sp = C.spells[f.id]; if (sp) for (const z of [54, 24, 20]) add('sp_' + sp.icon, z); }
  for (const p of C.passives) { add(p.icon, 44); add(p.icon, 18); }
  for (const w of C.weapons || []) add(w.icon, 50);
  let done;
  const step = (dl) => {   // (as many as the idle moment allows — the countdown gives plenty —; 2 when a busy run makes it wait)
    if (R._disposed || !todo.length) return done();
    let n = 0; do { const [nm, s] = todo.shift(); try { Game.icons.dataURL(nm, iconPx(s)); } catch (e) { } n++; } while (todo.length && (dl && !dl.didTimeout ? dl.timeRemaining() > 4 : n < 2));
    if (todo.length) idle(step); else done();
  };
  const idle = fn => (window.requestIdleCallback ? requestIdleCallback(fn, { timeout: 250 }) : setTimeout(fn, 60));
  return new Promise(res => { done = res; idle(async () => { if (R.rerolls > 0) await Promise.all(['ui603', 'ui611', 'ui605'].map(f => FxSheets.load(f))); idle(step); }); });   // (the reroll's die too: its sheets' decoding was 0.14 s of the first level-up on a phone)
}
// artworks are packed in a few atlases (assets/art/art_N.webp, SPR.art); each <img> gets a cached data URL of its frame
const ArtAtlas = {
  imgs: {}, urls: {}, dir: 'art', meta: () => SPR.art,
  sheet(i) { return this.imgs[i] || (this.imgs[i] = Assets.loadImg(`assets/${this.dir}/${this.dir}_${i}.webp`)); },
  async url(name, max) {
    const k = name + '@' + max; if (this.urls[k]) return this.urls[k];
    const M = this.meta(), f = M && M.f[name]; if (!f) return null;
    const im = await this.sheet(f[0]); if (!im) return null;
    const [, x, y, w, h] = f, s = Math.min(1, max / Math.max(w, h));
    const c = document.createElement('canvas'); c.width = Math.max(1, Math.round(w * s)); c.height = Math.max(1, Math.round(h * s));
    const g = c.getContext('2d'); g.imageSmoothingQuality = 'high'; g.drawImage(im, x, y, w, h, 0, 0, c.width, c.height);
    return (this.urls[k] = c.toDataURL('image/webp', 0.92));
  },
};
// a TTG card: Ankama's official picture (0.98.3: tools/assets/build_ttg098.py, one file a card; no text on it: name and number beside it)
function ttgCard(c, cls = '') {
  return h('div', { class: 'ttg-c off r' + (c.r || 0) + ' ' + cls }, h('img', { src: vurl(`assets/ttg/c${c.id}.webp`), loading: 'lazy', decoding: 'async', draggable: 'false', alt: L(c.name) }));
}
function artImg(name, cls = '', max = 380) {
  const im = h('img', { class: cls, draggable: 'false', alt: '' });
  const k = Math.min(3, Math.max(1, (Game._uiz || 1) * (window.devicePixelRatio || 1)));   // 0.34: at the size it is shown on this screen (no blur)
  ArtAtlas.url(name, Math.round(max * k)).then(u => { if (u) im.src = u; });
  return im;
}

// 0.68: the main menu's button pictures, flat vectors in the button text's colour
const MENU_IC = {
  play: '<path d="M7 4 L20 12 L7 20 Z" fill="currentColor"/>',
  sword: '<path d="M19 3 L21 5 L11 15 L9 13 Z M8 14 L10 16 L7 19 L5 17 Z M4 18 L6 20 L4 22 L2 20 Z" fill="currentColor"/>',
  shield: '<path d="M12 2 L20 5 V11 C20 16 16.5 20 12 22 C7.5 20 4 16 4 11 V5 Z" fill="currentColor"/><path d="M12 4.5 V19.5" stroke="rgba(0,0,0,.35)" stroke-width="1.6"/>',
  bag: '<path d="M9 3 H15 L13.6 6.5 C17.5 8 20 11.5 20 15.5 C20 19.5 16.5 21 12 21 C7.5 21 4 19.5 4 15.5 C4 11.5 6.5 8 10.4 6.5 Z" fill="currentColor"/><path d="M9.5 7 H14.5" stroke="rgba(0,0,0,.4)" stroke-width="1.6"/>',
  bars: '<rect x="4" y="13" width="4" height="8" rx="1" fill="currentColor"/><rect x="10" y="8" width="4" height="13" rx="1" fill="currentColor"/><rect x="16" y="3" width="4" height="18" rx="1" fill="currentColor"/>',
  doc: '<path d="M6 2 H14 L19 7 V22 H6 Z" fill="currentColor"/><path d="M9 11 H16 M9 14.5 H16 M9 18 H14" stroke="rgba(0,0,0,.45)" stroke-width="1.6"/>',
  gear: '<path d="M10.3 2 H13.7 L14.2 4.7 L16.4 5.6 L18.7 4.1 L21 6.4 L19.4 8.7 L20.3 10.9 L23 11.4 V14.6 L20.3 15.1 L19.4 17.3 L21 19.6 L18.7 21.9 L16.4 20.4 L14.2 21.3 L13.7 24 H10.3 L9.8 21.3 L7.6 20.4 L5.3 21.9 L3 19.6 L4.6 17.3 L3.7 15.1 L1 14.6 V11.4 L3.7 10.9 L4.6 8.7 L3 6.4 L5.3 4.1 L7.6 5.6 L9.8 4.7 Z" transform="translate(0 -1) scale(.92) translate(1 1)" fill="currentColor"/><circle cx="12" cy="12" r="3.4" fill="rgba(0,0,0,.45)"/>',
  door: '<path d="M5 2 H17 V22 H5 Z" fill="currentColor"/><path d="M7.5 4.5 H14.5 V19.5 H7.5 Z" fill="rgba(0,0,0,.35)"/><circle cx="13" cy="12.5" r="1.2" fill="currentColor"/>',
  pad: '<path d="M6.5 7 H17.5 C20.5 7 22.5 10 22.5 14 C22.5 17.5 20.5 19 18.8 19 C17.2 19 16.4 17.2 15 16 H9 C7.6 17.2 6.8 19 5.2 19 C3.5 19 1.5 17.5 1.5 14 C1.5 10 3.5 7 6.5 7 Z" fill="currentColor"/><path d="M7 10.5 V14.5 M5 12.5 H9" stroke="rgba(0,0,0,.5)" stroke-width="1.8"/><circle cx="16.5" cy="11.5" r="1.2" fill="rgba(0,0,0,.5)"/><circle cx="18.5" cy="13.8" r="1.2" fill="rgba(0,0,0,.5)"/>',
  music: '<path d="M9 17.5 V5 L20 3 V15.5" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linejoin="round"/><ellipse cx="6.5" cy="17.5" rx="3" ry="2.4" fill="currentColor"/><ellipse cx="17.5" cy="15.5" rx="3" ry="2.4" fill="currentColor"/>',
  user: '<circle cx="12" cy="7.5" r="4.6" fill="#8a5ae0"/><path d="M3 21 C3 15.5 7 13 12 13 C17 13 21 15.5 21 21 Z" fill="#8a5ae0"/><circle cx="12" cy="7.5" r="4.6" fill="none" stroke="#3a1a6a" stroke-width="1.4"/><path d="M3 21 C3 15.5 7 13 12 13 C17 13 21 15.5 21 21 Z" fill="none" stroke="#3a1a6a" stroke-width="1.4"/>',
  // 0.92: Discord's mascot (its logo), for the top bar's Discord button
  discord: '<path transform="translate(1.2 2) scale(.9)" fill="currentColor" d="M20.317 4.37a19.79 19.79 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.865-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.74 19.74 0 0 0 3.677 4.37a.07.07 0 0 0-.032.028C.533 9.046-.32 13.58.099 18.058a.082.082 0 0 0 .031.056 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028c.462-.63.874-1.295 1.226-1.994a.076.076 0 0 0-.042-.106 13.1 13.1 0 0 1-1.872-.892.077.077 0 0 1-.008-.128c.126-.094.252-.192.372-.291a.074.074 0 0 1 .078-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.009c.12.1.246.198.373.292a.077.077 0 0 1-.007.128 12.3 12.3 0 0 1-1.873.891.077.077 0 0 0-.041.107c.36.698.772 1.363 1.225 1.993a.076.076 0 0 0 .084.029 19.84 19.84 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z"/>',
};
function menuIc(k) { const s = document.createElement('span'); s.className = 'mic'; s.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true">' + (MENU_IC[k] || '') + '</svg>'; return s; }
const UI = {
  root: null, modal: null, levelUpOpen: false, screen: null, history: [], previews: [],
  get rootEl() { return this.root || (this.root = document.getElementById('ui')); },
  // 0.93: the character previews of a screen (UI.own) are let go with it (CharSprite.dispose)
  own(sp) { (this._own || (this._own = new Set())).add(sp); return sp; },
  // 0.93 (stress tests: ~300 event listeners more after each shop visit): a screen's listeners on the window / document go
  // with it (they were dropped only at the next key / controller move, holding the whole old screen until then)
  listen(t, type, fn, o) { t.addEventListener(type, fn, o); (this._ls || (this._ls = [])).push([t, type, fn, o]); },
  onClear(fn) { (this._oc || (this._oc = [])).push(fn); },
  drop(sp) { if (sp) { sp.dispose(); if (this._own) this._own.delete(sp); } return null; },
  clear() { if (this._own) { for (const sp of this._own) sp.dispose(); this._own.clear(); } if (this._ls) { for (const [t, ty, fn, o] of this._ls) t.removeEventListener(ty, fn, o); this._ls = []; } if (this._oc) { const f = this._oc; this._oc = []; for (const fn of f) try { fn(); } catch (e) { } } const had = !!this.modal; this.rootEl.innerHTML = ''; this.modal = null; if (had) this._refocus(); else this._opener = null; this.levelUpOpen = false; this.previews = []; document.body.classList.remove('menu-bg', 'endgame', 'endname'); },
  modalOpen() { return !!this.modal; },
  // 0.85: when a window closes (closeModal, or the screen rebuilt under it by clear()), the focus goes back to what opened
  // it, or to its twin (same class and text) when the screen was rebuilt
  _refocus() {
    if (!this._opener || typeof Nav === 'undefined') return;
    const o = this._opener, sig = (o.className || '').replace(' navfocus', '') + '|' + (o.textContent || '').slice(0, 40); this._opener = null;
    requestAnimationFrame(() => { if (this.modal) return; const t = o.isConnected ? o : Nav.items().find(e => (e.className || '').replace(' navfocus', '') + '|' + (e.textContent || '').slice(0, 40) === sig); if (t) Nav.set(t); });
  },
  closeModal() { const had = !!this.modal; if (this.modal) { this.modal.remove(); this.modal = null; }
    if (had) { this._refocus(); if (typeof Game !== 'undefined' && Game.state === 'run' && Game.run && !Game.run.over) Game.run.easeIn(); }   // (0.98.3: juice.js)
    this.levelUpOpen = false; this._luBack = null; if (this._doorJ) { this._doorJ = false; Audio2.stopJingle(0.3); } },
  // (0.60: a menu that set levelUpOpen just before keeps it: openModal used to clear it, so B / Échap acted on the cards' window)
  PICK_GUARD: 300,   // 0.98: ms a choice opened in a run ignores the dash keys (Space, E) — was 2000, it blocked real picks
  openModal(el) { if (typeof Game !== 'undefined' && Game.state === 'run') this._modalAt = performance.now();   // (0.84: Nav.key, the dash keys wait UI.PICK_GUARD)
    if (!this.modal && typeof Nav !== 'undefined' && Nav.el && Nav.el.isConnected) this._opener = Nav.el;
    const lu = this.levelUpOpen, back = this._luBack, opener = this._opener; this.closeModal(); this._opener = opener; this.levelUpOpen = lu; this._luBack = back; this.modal = h('div', { class: 'modal-wrap' }, el); this.rootEl.append(this.modal); if (typeof Nav !== 'undefined' && Nav.el && !this.modal.contains(Nav.el)) Nav.set(null); return this.modal; },   // (0.98.3: the cursor's frame stayed over the window, on the button behind it)
  loading(p, inRun) {
    let el = $('#loading');
    if (!el) {
      const ban = inRun && Game.run === null ? pick(['17', '1', '7', '12', '14', '5']) : '4';
      el = h('div', { id: 'loading', class: 'screen loading' },
        this.logo(false),
        h('img', { class: 'loading-banner', src: `assets/banners/${ban}.webp` }),
        h('div', { class: 'bar' }, h('div', { class: 'fill' })),
        h('div', { id: 'loading-text', class: 'tip' }, (T('tip') + ' : ') + pick(TIPS[LANG] || TIPS.fr)));
      this.rootEl.append(el);
    }
    $('.fill', el).style.width = Math.round(p * 100) + '%';
    if (p >= 1 && !inRun) el.remove();
  },
  // loading done: a Play button replaces the bar
  loadingReady() {
    return new Promise(res => {
      const el = $('#loading'); if (!el) return res();
      const bar = $('.bar', el); if (bar) bar.style.display = 'none';
      const b = btn('▶ ' + T('play'), () => { window.removeEventListener('keydown', key, true); Audio2.init(); Audio2.resume(); el.remove(); res(); }, 'orange big load-play');   // (0.93: its key listener goes with it — a click left it, and the loading screen, for good)
      el.append(b); Nav.set(b);
      const key = (e) => { if (e.code === 'Enter' || e.code === 'Space' || e.code === 'NumpadEnter') { window.removeEventListener('keydown', key, true); e.preventDefault(); e.stopPropagation(); b.click(); } };
      window.addEventListener('keydown', key, true);
    });
  },
  // ------------------------------------------------ main menu
  mainMenu() {
    this.kwakTimer();   // 0.40: now and then a Kwak de Flamme flies over the main menu (ui_events.js)
    this.clear(); document.body.classList.add('menu-bg'); this.screen = 'main'; this.history = [];
    document.body.classList.toggle('endgame', this.endGame()); document.body.classList.toggle('endname', /^goultard$/i.test(Store.pname(Store.prof)));   // (0.71: the burning wasteland, ui_events.js)
    { const S0 = Store.data, perm = (S0.unlocked || []).includes('goultard') || /^goultard$/i.test(Store.pname(Store.prof));
      if (perm && !S0.endMenuSeen) { S0.endMenuSeen = 1; S0.settings.menuMusic = 'loc_brakmar'; S0.settings.musicOff = false; Store.save(); setTimeout(() => Audio2.fxFile('laugh_goultard', 1), 600); } }   // (the first time: Brakmar's music and his laugh)
    const S = Store.data;
    Audio2.playMusic((S.settings.menuMusic !== 'loc_bonta' && S.settings.menuMusic) || 'loc_incarnam', 1.0, { menu: true });
    const dofusOwned = Game.C.dofus.filter(d => S.dofus[d.id]);
    const muted = !!S.settings.musicOff;
    // 0.30: the music button opens a little menu: the menu's track (Incarnam), Astrub, Bonta, Brakmar, or silence
    const TRACKS = [['loc_incarnam', 'Incarnam'], ['loc_amakna', 'Astrub'], ['loc_brakmar', 'Brâkmar']];   // (0.60: no 'menu music' tag)
    const pop = h('div', { class: 'music-pop hidden' });
    const mute = h('button', { class: 'mute-btn' + (muted ? ' off' : ''), title: T('music'), onclick: (e) => { e.stopPropagation(); Audio2.init(); Audio2.resume(); Audio2.blip('click'); fillPop(); pop.classList.toggle('hidden'); if (!pop.classList.contains('hidden') && Nav.enabled) Nav.set(pop.querySelector('.btn.active') || pop.querySelector('.btn')); } }, menuIc('music'));   // (0.68: a drawn note; .off crosses it)
    const pick = (track) => {
      S.settings.musicOff = !track; if (track) S.settings.menuMusic = track; Store.save(); Audio2.init(); Audio2.resume();
      Audio2.setVolumes(S.settings.musicOff ? 0 : S.settings.music, S.settings.sfx); if (track) Audio2.playMusic(track, 0.6, { menu: true });
      mute.classList.toggle('off', !track); pop.classList.add('hidden'); toast(track ? '♪ ' + TRACKS.find(t => t[0] === track)[1] : T('music_off'));
    };
    const fillPop = () => {
      const cur = S.settings.musicOff ? null : S.settings.menuMusic || 'loc_incarnam'; pop.innerHTML = '';
      // 0.48: the two volumes too (as in the options)
      const vol = (label, key) => h('label', { class: 'mp-vol' }, h('span', {}, label), h('input', { type: 'range', min: 0, max: 1, step: 0.05, value: S.settings[key], oninput: (e) => {
        const St = S.settings; St[key] = +e.target.value;
        if (key === 'music' && St.musicOff && St.music > 0) { St.musicOff = false; Audio2.playMusic(St.menuMusic || 'loc_incarnam', 0.6, { menu: true }); mute.classList.remove('off'); }
        Audio2.setVolumes(St.musicOff ? 0 : St.music, St.sfx); Store.save();
      }, onchange: () => { if (key === 'sfx') Audio2.blip('click'); } }));
      pop.append(h('div', { class: 'mp-title' }, menuIc('music'), T('music')), ...TRACKS.map(([k, n, sub]) => btn([h('span', {}, n), sub ? h('small', {}, sub) : null], () => pick(k), k === cur ? 'active' : '')),
        btn(T('mus_mute'), () => pick(null), cur ? 'mute' : 'mute active'), styleRow(), vol(T('music'), 'music'), vol(T('sfx'), 'sfx'));
    };
    const closePop = (e) => { if (!pop.isConnected) { document.removeEventListener('click', closePop); return; } if (!pop.contains(e.target)) pop.classList.add('hidden'); };
    this.listen(document, 'click', closePop);
    const nach = Object.keys(S.ach || {}).length;
    const el = h('div', { class: 'screen main' },
      this.logo(true), this.dofawaReady() ? btn(['★ ', T('dofawa_btn'), ' ★'], () => this.dofawaScene(), 'dofawa-btn') : null,   // 0.26 (ui_events.js)
      h('div', { class: 'menu-buttons' },
        btn([menuIc('play'), h('span', {}, T('play'))], () => this.playScreen(), 'big orange bloody'),
        h('div', { class: 'menu-row' }, btn([menuIc('sword'), h('span', {}, T('bestiary'))], () => this.bestiary(), 'bloody b2'), btn([menuIc('shield'), h('span', {}, T('armory'))], () => this.armory())),   // 0.28 (ui_armory.js)
        btn([menuIc('bag'), h('span', {}, T('shop'))], () => this.shop(), 'shopbtn'),   // (0.60: a lighter button, the shop stands out)
        btn([menuIc('bars'), h('span', {}, `${T('achievements')} (${nach}/${(Game.C.achievements || []).length})`)], () => this.achievements()),
        h('div', { class: 'menu-row' }, btn([menuIc('doc'), h('span', {}, T('stats'))], () => this.stats()), btn([menuIc('pad'), h('span', {}, T('ctl_title'))], () => this.controls())),
        h('div', { class: 'menu-row' }, btn([menuIc('gear'), h('span', {}, T('options'))], () => this.options()), btn([menuIc('door'), h('span', {}, T('quit_game'))], () => this.quitGame(), 'bloody b3'))),
      h('div', { class: 'wallet main-wallet' }, iconImg('KamaSymbol', 22), ' ', h('b', {}, fmtNum(S.kamas))),   // (0.92: no 'kamas' word, the K says it)
      h('div', { class: 'dofus-coll', title: T('dofus_coll') }, ...Game.C.dofus.map(d => {
        const i = iconImg('dofus_hd_' + d.icon, 30, S.dofus[d.id] ? '' : 'locked');
        return h('button', { class: 'dofus-pick', title: S.dofus[d.id] ? L(d.name) : '???', onclick: () => { Audio2.blip('click'); this.dofusInfo(d); } }, i);
      })),
      h('div', { class: 'main-foot' }, h('div', { class: 'version' }, T('beta') + ' ' + BUILD)),   // (the fan-made note is in the credits and on the loading screen)
      this.flags(), mute, pop,
      h('button', { class: 'prof-btn', title: T('profiles'), onclick: () => { Audio2.init(); Audio2.resume(); Audio2.blip('click'); this.profilesMenu(); } }, menuIc('user'), h('span', { class: 'pn' }, Store.pname(Store.prof)), h('span', { class: 'pnum' }, String(Store.prof))),
      h('button', { class: 'credits-btn', 'data-nav-x': 'home', onclick: () => { Audio2.blip('click'); this.credits(); } }, T('credits')),   // (0.60: left / right from it: back to Jouer)
      this.themeToggle());
    // 0.68: the music button, the profile and the kamas in one wooden bar, top left
    // 0.92: a Discord button at the bar's right end: a little panel (what it is for, a joke), its button opens the link
    const dc = h('button', { class: 'dc-btn', title: T('dc_tip'), 'aria-label': 'Discord', onclick: () => { Audio2.init(); Audio2.resume(); Audio2.blip('click'); this.discordInfo(); } }, menuIc('discord'));
    el.append(h('div', { class: 'top-bar' }, mute, el.querySelector('.prof-btn'), h('i', { class: 'tb-sep' }), el.querySelector('.main-wallet'), h('i', { class: 'tb-sep' }), dc));
    // 0.92: on a phone / narrow window the bar ran over the language flags: smaller flags first (a landscape
    // phone), under the bar if still too wide (checked on every resize)
    const fl = el.querySelector('.flags'), tb = el.querySelector('.top-bar'), fitFlags = () => {
      if (!el.isConnected) return removeEventListener('resize', fitFlags);
      const hit = () => { const a = tb.getBoundingClientRect(), b = fl.getBoundingClientRect(); return a.right + 6 > b.left && a.bottom > b.top; };
      fl.classList.remove('compact', 'low');
      if (hit()) { fl.classList.add('compact'); if (hit()) fl.classList.add('low'); }
      el.classList.toggle('flags-low', fl.classList.contains('low'));   // (0.94: the logo makes room for them, index.html)
    };
    if (this._fitFlags) removeEventListener('resize', this._fitFlags); this._fitFlags = fitFlags; addEventListener('resize', fitFlags);   // (0.93: one listener, the last menu's — they piled up, each holding an old menu)
    this.rootEl.append(el); fitFlags();   // (0.71: one fixed size for every language: no fitWidth here, the CSS sets one size)   // (long words: Waffenkammer…)
    if (S.goultardThanks === 1) setTimeout(() => { if (this.screen === 'main' && !this.modal) this.goultardThanks(); }, 700);   // (0.91: Goultard beaten)
    if (this.updateCheck) this.updateCheck(el);   // (0.95: the installed builds: a newer version on GitHub, ui_update.js)
  },
  // 0.91: back on the main menu after Goultard's first defeat: thanks, a joke of Dofus and the Discord link (once)
  goultardThanks() {
    const S = Store.data, url = Game.C.discord || 'https://discord.gg/N8f62M2eaK';
    const done = () => { S.goultardThanks = 2; Store.save(); this.closeModal(); };
    const el = h('div', { class: 'window modal gt-thanks' }, h('div', { class: 'title' }, T('gt_title'), h('button', { class: 'close', onclick: done }, '×')),
      h('div', { class: 'content' },
        h('div', { class: 'gt-icon' }, iconImg('it_47_26', 72)),
        ...T('gt_text').split('\n').map(t => h('p', {}, t)),
        h('p', { class: 'gt-join' }, T('gt_join')),
        h('a', { class: 'btn discord-btn', href: url, target: '_blank', rel: 'noopener', onclick: () => Audio2.blip('click') }, '💬 Discord — ' + url.replace(/^https?:\/\//, '')),
        h('div', { class: 'start-row' }, btn(T('gt_ok'), done, 'orange'))));
    this.openModal(el); if (Audio2.fanfare) Audio2.fanfare(1);
  },
  // 0.92: the top bar's Discord panel: what the Discord is for (news, updates, bugs, ideas, the local version's
  // download link, which is given there), a joke of Dofus, the link (a new tab; the desktop app opens the browser, main.js)
  discordInfo() {
    const url = Game.C.discord || 'https://discord.gg/N8f62M2eaK', close = () => { Audio2.blip('click'); this.closeModal(); };
    const li = (ic, k) => h('li', {}, h('span', { class: 'dc-ic' }, ic), h('span', {}, T(k)));
    const el = h('div', { class: 'window modal dc-info' }, h('div', { class: 'title' }, menuIc('discord'), ' ', T('dc_title'), h('button', { class: 'close', onclick: close }, '×')),
      h('div', { class: 'content' },
        h('p', { class: 'dc-joke' }, T('dc_joke'), ' 🐑'),
        h('ul', { class: 'dc-list' }, li('📜', 'dc_news'), li('✨', 'dc_new'), li('🐞', 'dc_bugs'), li('💡', 'dc_ideas'), li('💾', 'dc_dl')),
        h('p', { class: 'dc-lag' }, T('dc_lag')),
        h('a', { class: 'btn discord-btn', href: url, target: '_blank', rel: 'noopener', 'data-nav-first': '', onclick: (e) => { Audio2.blip('click');
          // (a controller's A is no user gesture for the browser, which may block the tab: then the address in a toast; the
          // desktop app's window.open is always null, main.js opens the browser)
          if (!e.isTrusted) { e.preventDefault(); const w = window.open(url, '_blank'); if (w) w.opener = null; else if (!/Electron\//.test(navigator.userAgent)) toast(url.replace(/^https?:\/\//, '')); } } }, menuIc('discord'), ' ', T('dc_join')),
        h('div', { class: 'dc-url' }, url.replace(/^https?:\/\//, ''))));
    this.openModal(el);
  },
  // v2.0 three profiles on the same device, and a full reset of the current one (asked twice)
  profilesMenu() {
    const rows = [];
    for (let n = 1; n <= Store.NPROF; n++) {
      const inf = Store.info(n), cur = n === Store.prof;
      const txt = inf && (inf.runs || inf.kamas || inf.ach) ? T('profile_info', { r: fmtNum(inf.runs), k: fmtNum(inf.kamas), a: inf.ach }) : T('profile_empty');
      rows.push(h('div', { class: 'prof-row' + (cur ? ' cur' : ''), 'data-nav': 'prof:' + n },
        h('div', { class: 'prof-ic' }, String(n)),
        h('div', { class: 'prof-txt' }, h('b', {}, Store.pname(n)), h('small', {}, txt)),
        btn('✎', () => this.renameMenu(n), 'prof-ren'),
        cur ? h('span', { class: 'prof-cur' }, '✔ ' + T('profile_current'))
          : btn(T('profile_pick'), () => { Store.switchTo(n); applyTheme(); this.closeModal(); this.mainMenu(); toast(T('profile_switched', { n })); this.nameEgg(Store.pname(n)); }, 'orange')));   // (0.92: a name's easter egg)
    }
    const reset = btn('⟲ ' + T('reset_progress'), (e) => {
      const b = e.currentTarget;
      if (b.dataset.armed) { Store.reset(); applyTheme(); Audio2.blip('wrong'); this.closeModal(); this.mainMenu(); toast(T('reset_done')); return; }
      b.dataset.armed = '1'; b.textContent = '⚠ ' + T('reset_confirm'); b.classList.add('danger');
    }, 'reset-btn');
    const el = h('div', { class: 'window modal profiles' }, h('div', { class: 'title' }, '👤 ' + T('profiles'), h('button', { class: 'close', onclick: () => this.closeModal() }, '×')),
      h('div', { class: 'content' }, h('p', { class: 'sub' }, T('profiles_hint')), ...rows,
        h('div', { class: 'reset-box' }, h('p', { class: 'sub' }, T('reset_hint', { n: Store.prof })), reset),
        h('div', { class: 'start-row' }, btn(T('back'), () => this.closeModal()))));
    this.openModal(el);
  },
  // 0.34: name a profile (8 characters): an on-screen keyboard for the controller / phone, the PC keyboard types
  // straight in (letters, Backspace, Enter = OK, Escape = back), and a random name from the client's NPCs
  // 0.65: the on-screen keyboard (profile names, the shop's skin search): AZERTY / QWERTY rows, accents, space, shift
  // (caps: start in capitals), backspace, then any extra buttons
  keyPad(type, del, caps = true, ...extra) {
    const az = Input.layout === 'azerty' || (!Input.layout && LANG === 'fr');
    const rows = (az ? ['AZERTYUIOP', 'QSDFGHJKLM', 'WXCVBN'] : ['QWERTYUIOP', 'ASDFGHJKL', 'ZXCVBNM']).map(r => [...r]);
    rows[2].push('-', "'"); rows.push(['É', 'È', 'Ê', 'À', 'Ï', 'Ô', 'Ç', ' ']);
    const keys = [], face = c => c === ' ' ? '␣' : caps ? c : c.toLowerCase();
    return h('div', { class: 'ren-kb' }, ...rows.map(r => h('div', { class: 'ren-row' }, ...r.map(c => { const b = btn(face(c), () => type(c === ' ' ? ' ' : caps ? c : c.toLowerCase()), 'ren-key' + (c === ' ' ? ' wide' : '')); b.dataset.c = c; keys.push(b); return b; }))),
      h('div', { class: 'ren-row' },
        btn('⇧', (e) => { caps = !caps; e.currentTarget.classList.toggle('on', caps); keys.forEach(b => { b.textContent = face(b.dataset.c); }); }, 'ren-key wide' + (caps ? ' on' : '')),
        btn('⌫', del, 'ren-key wide'), ...extra));
  },
  // 0.65: the shop's skin search on the on-screen keyboard: the list behind filters at each key (onChange)
  searchMenu(q, onChange) {
    const MAX = 24; const shown = h('div', { class: 'ren-name' });
    const draw = () => { shown.textContent = ''; shown.append(h('span', {}, q), h('i', { class: 'ren-caret' })); };
    const set = (v) => { q = v; draw(); onChange(q); };
    const type = (c) => { if (q.length < MAX) { Audio2.blip('click'); set(q + c); } else Audio2.blip('wrong'); };
    const del = () => set(q.slice(0, -1));
    const done = () => { off(); this.closeModal(); };
    const onKey = (e) => {
      if (!this.modal || !this.modal.contains(el)) return off();
      if (e.ctrlKey || e.metaKey || e.altKey) return;
      if (e.key === 'Backspace') del(); else if (e.key === 'Enter' || e.key === 'Escape') done();
      else if (e.key && e.key.length === 1 && /[\p{L}\p{N} '\-]/u.test(e.key)) type(e.key);
      else return;
      e.preventDefault(); e.stopPropagation();
    };
    const off = () => window.removeEventListener('keydown', onKey, true);
    window.addEventListener('keydown', onKey, true);
    const el = h('div', { class: 'window modal rename' }, h('div', { class: 'title' }, '🔍 ' + T('search_title'), h('button', { class: 'close', onclick: done }, '×')),
      h('div', { class: 'content' }, h('p', { class: 'sub' }, T('search_hint')), shown, this.keyPad(type, del, false, btn('✕', () => set(''), 'ren-key wide')),
        h('div', { class: 'start-row' }, btn('✔ OK', done, 'orange'))));
    draw(); this.openModal(el);
  },
  // 0.92: some profile names play a little clip when saved or picked (assets/audio/fx, the music paused
  // meanwhile: Audio2.jingle fx). The whole name compared, without case, accents, spaces, hyphens or apostrophes
  NAME_EGGS: { bardella: 'bardella', jordan: 'bardella', lassalle: 'lassalle', zemmour: 'zemmour', meluche: 'meluche', jeanluc: 'meluche',
    sardoche: 'sardoche', lisnard: 'lisnard', sarkozy: 'sarkozy', hollande: 'hollande', lepen: 'lepen', marine: 'marine', ntm: 'marine', macron: 'macron',
    messi: 'messi', morsay: 'morsay', booba: 'booba', biden: 'biden', trump: 'trump', wallah: 'wallah' },   // (0.97)
  nameKey(name) { return String(name || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim().replace(/[\s\-'’_.]+/g, ''); },
  nameEgg(name) {
    const k = this.nameKey(name), clip = this.NAME_EGGS[k]; if (k === 'goultard') this.nameEggAch(); if (!clip) return false;   // (Goultard: his own egg, the menu — the achievement too)
    Audio2.init(); Audio2.resume(); Audio2.jingle(clip, { fx: true }); this.nameEggAch(); return true;
  },
  nameEggAch() { const st = Prog.st(); if (!st.nameEgg) { st.nameEgg = 1; Store.save(); Prog.check(null); } },   // (0.92: the achievement 'a name that sings', Goultard too)
  renameMenu(n) {
    const MAX = 8; let name = Store.meta().names && Store.meta().names[n] || '';
    const shown = h('div', { class: 'ren-name' });
    const draw = () => { shown.textContent = ''; shown.append(h('span', {}, name), h('i', { class: 'ren-caret' }), h('small', {}, name.length + ' / ' + MAX)); };
    const type = (c) => { if (name.length < MAX) { name += c; Audio2.blip('click'); } else Audio2.blip('wrong'); draw(); };
    const del = () => { name = name.slice(0, -1); draw(); };
    const done = () => { const wasEnd = this.endGame(); Store.setName(n, name); off();
      if (/^goultard$/i.test(name) && n === Store.prof) { Store.data.settings.menuMusic = 'loc_brakmar'; Store.data.settings.musicOff = false; Store.data.endMenuSeen = 1; Store.save(); Audio2.fxFile('laugh_goultard', 1); }   /* (0.71: the Goultard easter egg) */
      if (this.screen === 'main' && this.endGame() !== wasEnd) this.mainMenu();   // (0.87: the Goultard menu shows at once when the name brings it — or takes it away — no need to leave the menu)
      this.nameEgg(name);   // (0.92: after the menu's music restarted, else it would stop the clip)
      const pb = document.querySelector('.prof-btn .pn'); if (pb) pb.textContent = Store.pname(Store.prof); this.profilesMenu(); };
    const back = () => { off(); this.profilesMenu(); };
    const kb = this.keyPad(type, del, true, btn('🎲 ' + T('ren_random'), () => { const L8 = (Game.C.npcNames || []).filter(x => x.length <= MAX && x !== name); if (L8.length) { name = pick(L8); Audio2.blip('click'); draw(); } }, 'ren-key wider'));
    const onKey = (e) => {
      if (!this.modal || !this.modal.contains(el)) return off();
      if (e.ctrlKey || e.metaKey || e.altKey) return;
      if (e.key === 'Backspace') { del(); } else if (e.key === 'Enter') { done(); } else if (e.key === 'Escape') { back(); }
      else if (e.key && e.key.length === 1 && /[\p{L}\p{N} '\-]/u.test(e.key)) type(e.key);
      else return;
      e.preventDefault(); e.stopPropagation();
    };
    const off = () => window.removeEventListener('keydown', onKey, true);
    window.addEventListener('keydown', onKey, true);
    const el = h('div', { class: 'window modal rename' }, h('div', { class: 'title' }, '✎ ' + T('ren_title', { n }), h('button', { class: 'close', onclick: back }, '×')),
      h('div', { class: 'content' }, h('p', { class: 'sub' }, T('ren_hint')), shown, kb,
        h('div', { class: 'start-row' }, btn(T('back'), back), btn('✔ ' + T('ren_ok'), done, 'orange'))));
    draw(); this.openModal(el);
  },
  // a collected Dofus: what it does in a run, and who drops it
  dofusInfo(d) {
    const S = Store.data, C = Game.C, n = S.dofus[d.id] || 0;
    const from = d.from.map(id => id === 'any_final' ? T('dofus_anyfinal') : id === 'tot' ? T('dofus_tot') : C.bosses[id] ? L(C.bosses[id].name) : null).filter(Boolean);
    if (d.id === 'ocre' && !from.length) from.push(T('dofus_tot'));
    const el = h('div', { class: 'window modal dofus-info', style: { '--c': d.color } }, h('div', { class: 'title' }, n ? L(d.name) : '???', h('button', { class: 'close', onclick: () => this.closeModal() }, '×')),
      h('div', { class: 'content' },
        h('div', { class: 'dofus-big' }, iconImg('dofus_hd_' + d.icon, 110, n ? '' : 'locked')),
        n ? h('p', { class: 'dofus-effect', style: { color: d.color } }, T('dofus_effect') + ' : ' + L(d.desc)) : h('p', { class: 'dofus-effect' }, T('dofus_none')),
        n ? h('p', { class: 'sub' }, T('dofus_times', { n })) : null,
        h('p', { class: 'sub' }, n || from.length < 2 || C.maps.filter(m => !m.hidden).every(m => S.cleared[m.id]) ? T('dofus_from', { b: from.join(', ') }) : T(I18N.fr['dofus_joke_' + d.id] ? 'dofus_joke_' + d.id : 'dofus_joke' + (1 + d.id.length % 4))),   // 0.38: known once dropped (or every zone won), else a joke (0.92: its own if it has one)
        h('div', { class: 'start-row' }, btn(T('continue'), () => this.closeModal(), 'orange big'))));
    this.openModal(el);
  },
  // light / dark menus (saved); the switch sits at the bottom right of the main menu
  // closes the game: the desktop build closes its window; a browser only lets a script close a tab it opened itself
  quitGame() {
    Audio2.blip('click');
    if (window.RSAndroid) { Audio2.halt(); RSAndroid.quit(); return; }   // (0.94: the Android app, tools/android/MainActivity.java)
    try { window.close(); } catch (e) { }
    setTimeout(() => { if (!window.closed) toast(T('quit_tab')); }, 250);
  },
  themeToggle() {
    const sw = h('span', { class: 'switch' + (Store.data.settings.theme === 'dark' ? ' on' : '') });
    const lab = h('span', {}, T('theme_dark'));
    return h('button', { class: 'theme-btn', 'data-nav-x': 'home', title: T('theme_hint'), onclick: () => toggleTheme() }, lab, sw);   // (toggleTheme: F1 / R3 too)
  },
  flags() {
    return h('div', { class: 'flags', title: T('flags_hint') }, ...LANGS.map(lg => {
      const im = iconImg('Flag_' + lg, 30, LANG === lg ? 'cur' : '');
      const b = h('button', { class: 'flag' + (LANG === lg ? ' cur' : ''), title: Game.C.langNames[lg], onclick: () => { Audio2.init(); Audio2.resume(); Audio2.blip('click'); setLang(lg); this.mainMenu(); } }, im, h('span', {}, lg.toUpperCase()));
      return b;
    }));
  },
  back() {
    if (this._palClose) { this._palClose(); return; }
    if (Game.state === 'run' || Game.state === 'tot' || Game.state === 'loading') return;   // (0.61: never out of a run to the main menu)
    if (this.screen && this.screen !== 'main') { Audio2.blip('click'); this.mainMenu(); }
  },
  panel(title, ...content) {
    return h('div', { class: 'window' }, h('div', { class: 'title' }, title, h('button', { class: 'close', onclick: () => this.mainMenu() }, '×')), h('div', { class: 'content' }, ...content));
  },
  // ------------------------------------------------ play screen
  playScreen() {
    this.clear(); document.body.classList.add('menu-bg'); this.screen = 'play';
    if (typeof Nav !== 'undefined') Nav.forget('play');   // (0.92: the cursor starts on the first class — the preview keeps the last one played)
    const S = Store.data, C = Game.C;
    let cls = C.classes.find(c => c.id === S.lastClass) || C.classes[7];
    let sex = S.lastSex || 0; let colors = (S.colors || {})[cls.id] || baseColors(cls, sex);
    const visMaps = C.maps.filter(m => !m.hidden), allCleared = visMaps.every(m => S.cleared[m.id]);
    let map = S.unlocked.includes(S.lastMap) ? S.lastMap : 'astrub';
    const pk1 = Math.max(1, (window.devicePixelRatio || 1) * (Game._uiz || 1) * 170 / 260);  // backing store at screen resolution (menus are zoomed by --uiz)
    const prevCanvas = h('canvas', { class: 'preview', width: Math.round(260 * pk1), height: Math.round(260 * pk1) });
    let sprite = null; let spriteKey = '';
    const loadSprite = async () => {
      const sid = cls.sprites[sex]; const eq = S.equip || {};
      const key = sid + '|' + eq.hat + '|' + eq.cape + '|' + eq.pet;
      spriteKey = key;
      const sp = this.own(new CharSprite(sid, colors, cls.nohats ? null : eq.hat || null, cls.nohats ? null : eq.cape || null, cls.nopets ? null : eq.pet || null, cls.nohats ? null : eq.shield || null));
      await sp.load();
      if (spriteKey === key) { if (sprite && sprite !== sp) this.drop(sprite); sprite = sp; } else this.drop(sp);   // (0.93: the class shown before is let go)
    };
    const right = h('div', { class: 'class-info' });
    const grid = h('div', { class: 'class-grid' });
    const renderInfo = () => {
      right.innerHTML = '';
      const b = cls.base;
      right.append(
        h('h2', { style: { color: cls.color } }, L(cls.name)),
        h('div', { class: 'preview-wrap' }, prevCanvas,
          h('div', { class: 'preview-btns' },
            cls.sprites[0] === cls.sprites[1] ? null : btn(sex ? T('female') : T('male'), () => { sex = 1 - sex; sprite = null; loadSprite(); renderInfo(); }),
            cls.nocolors ? null : this.colorRow(() => colors, c => { colors = c; (S.colors = S.colors || {})[cls.id] = c; Store.save(); if (sprite) sprite.recolor(c); }, () => baseColors(cls, sex)))),
        h('div', { class: 'stats-row' },
          h('span', {}, iconImg('Heart', 18), ' ', b.hp), h('span', {}, iconImg('Icon_c_mp', 18), ' ', Math.round(b.speed * 100) + '%'),
          h('span', {}, iconImg('Icon_33', 18), ' ', Math.round(b.might * 100) + '%'), h('span', {}, iconImg('Icon_c_neutral', 18), ' ', b.armor)),
        h('div', { class: 'passive' }, h('b', {}, T('class_passive') + ' : '), L(cls.passive)),
        h('div', { class: 'spell-list' }, ...cls.spells.map((sid, i) => {
          const sp = C.spells[sid];
          return h('div', { class: 'spell' + (i === 0 ? ' sig' : '') }, iconImg('sp_' + sp.icon, 34), h('div', {}, h('b', {}, L(sp.name) + (i === 0 ? ' ★' : '')), h('div', { class: 'desc fx-desc' }, L(sp.desc)), h('div', { class: 'syn-mini', title: T('arm_boosted') }, h('small', {}, T('arm_boosted') + ' :'), ...boostsOf(sp).map(p => tipIcon(p.icon, L(p.name), 16)))));
        })));
    };
    C.classes.forEach(c => {
      const card = h('div', { class: 'class-card' + (c === cls ? ' sel' : ''), 'data-nav-first': c === C.classes[0] ? '' : null, onclick: () => {
        cls = c; colors = (S.colors || {})[c.id] || baseColors(c, sex); sprite = null; loadSprite();
        grid.querySelectorAll('.class-card').forEach(e => e.classList.remove('sel')); card.classList.add('sel');
        renderInfo(); Audio2.blip('click');
        const j = c.theme || 'cls_' + c.id; Audio2.jingle(j); // every class has its theme (Pandawa: Pandala city, Roublard: the Trool fair, Brigandin: the cobbler's tune, Sacrieur: Kutan)
      } }, artImg(c.emblemArt || ('b' + c.breed), 'breed', 200), h('div', { class: 'cname' }, L(c.name)));
      grid.append(card);
    });
    const mapsEl = h('div', { class: 'maps' }, ...C.maps.map((m, i) => {
      const unlocked = S.unlocked.includes(m.id);
      if (m.hidden && !unlocked) return h('div', { class: 'map-card locked secret' }, h('div', { class: 'mini qmark' }, '?'), h('div', { class: 'mname' }, (i + 1) + '. ' + T('secret_zone')), h('div', { class: 'mlvl' }, '🔒 ' + T(m.lockKey || (m.unlockAch ? 'nowel_lock' : m.unlockBy ? 'goultard_lock' : 'secret_hint'))));
      const card = h('div', { class: 'map-card' + (m.id === map ? ' sel' : '') + (unlocked ? '' : ' locked'), onclick: () => {
        if (!unlocked) return; map = m.id; mapsEl.querySelectorAll('.map-card').forEach(e => e.classList.remove('sel')); card.classList.add('sel'); Audio2.blip('click'); syncMode();
      } },
        h('img', { src: `assets/worlds/${m.world}_mini.webp`, class: 'mini' }),
        h('div', { class: 'mname' }, (i + 1) + '. ' + L(m.name) + (m.hidden ? ' ★' : '')),
        h('div', { class: 'mlvl' }, unlocked ? (T('difficulty') + ' ' + m.lvl + (S.best[m.id] ? ' — ' + T('best') + ' ' + fmtTime(S.best[m.id]) : '')) : '🔒 ' + T('locked_hint')),
        unlocked && m.hardOnly ? h('div', { class: 'mlvl hard-only' }, '☠ ' + T('hard_only')) : null,
        S.cleared[m.id] ? h('div', { class: 'map-done', title: T('st_won') }, '✔') : null,   // 0.34: zone already won
        (S.clearedHard || {})[m.id] ? h('div', { class: 'map-hard', title: T('hard_won') }, iconImg('it_47_26', 18)) : null);   // 0.92: won in Difficile (Run.claimVictory)
      return card;
    }));
    // 0.20: Normale / Difficile (remembered)
    // (Difficile: the client's Crâ skull, top right, red when picked)
    // (0.91: a zone `hardOnly` — Goultard's — is played in Difficile only: Normale greyed while it is picked)
    const hardOnly = () => !!(C.maps.find(m => m.id === map) || {}).hardOnly;
    // (0.95: Difficile is locked until Grobe is won — Store.hardOk; Game.startRun checks it too)
    const hardLock = () => !Store.hardOk(), lockMsg = () => T('hard_locked', { map: L((C.maps.find(m => m.id === C.gany.unlockHard) || {}).name || {}) });
    if (hardLock()) S.hard = false;
    const modeBtn = (hard) => btn(hard ? [hardLock() ? '🔒 ' : '', T('mode_hard'), iconImg('it_47_26', 26, 'skull')] : T('mode_normal'), () => { if ((!hard && hardOnly()) || (hard && hardLock())) { Audio2.blip('wrong'); if (hard) toast(lockMsg()); return; } S.hard = hard; Store.save(); syncMode(); }, hard ? 'hard' : '');
    const nBtn = modeBtn(false), hBtn = modeBtn(true), modeSel = h('div', { class: 'mode-sel', title: T('mode_hint') }, nBtn, hBtn);
    const syncMode = () => { const ho = hardOnly(), hd = ho || !!S.hard; nBtn.classList.toggle('active', !hd); nBtn.classList.toggle('disabled', ho); hBtn.classList.toggle('active', hd); hBtn.classList.toggle('disabled', hardLock()); nBtn.title = ho ? T('hard_only') : ''; hBtn.title = hardLock() ? lockMsg() : ''; };
    syncMode();
    // Endless mode (0.23): a switch of its own, and the local leaderboard of the zone
    const infBtn = btn('∞ ' + T('mode_infinite'), (e) => { S.infinite = !S.infinite; Store.save(); e.currentTarget.classList.toggle('active', !!S.infinite); }, 'inf-btn' + (S.infinite ? ' active' : ''));
    infBtn.title = T('mode_inf_hint');
    const el = h('div', { class: 'screen play' },
      this.panel(T('choose_class'),
        h('div', { class: 'play-layout' }, h('div', { class: 'play-left' }, grid, h('h3', {}, T('choose_map')), mapsEl), right),
        h('div', { class: 'start-row' },
          btn(T('back'), () => this.mainMenu()),
          btn('🏆 ' + T('leaderboard'), () => this.leaderboard(map)),
          modeSel, infBtn,
          btn(T('start'), () => {
            const eq = S.equip || {};
            Game.startRun({ cls: cls.id, sex, colors, hat: eq.hat || null, cape: eq.cape || null, pet: eq.pet || null, shield: eq.shield || null, map, tofuMode: this.tofuMode, hard: (!!S.hard && !hardLock()) || hardOnly(), infinite: !!S.infinite });
          }, 'big orange start-btn'))));
    this.rootEl.append(el);
    renderInfo(); loadSprite();
    // preview animation
    let t = 0;
    this.previews.push((dt) => {
      t += dt; const g = prevCanvas.getContext('2d'); g.setTransform(pk1, 0, 0, pk1, 0, 0); g.clearRect(0, 0, 260, 260);
      if (!sprite) return;
      const phase = Math.floor(t / 3) % 4; const anims = ['staticR', 'runR', cls.casts[0] + 'R', 'runL'];
      let a = anims[phase]; if (!sprite.has(a)) a = 'staticR';
      const lt = t % 3;
      g.imageSmoothingQuality = 'high';
      sprite.draw(g, a, lt, 130, 232, 3.2, phase === 3, { loop: true, moving: phase === 1 || phase === 3, at: t });
    });
  },
  // ------------------------------------------------ bestiary
  bestiary() {
    this.clear(); document.body.classList.add('menu-bg'); this.screen = 'bestiary';
    const C = Game.C, S = Store.data;
    const detail = h('div', { class: 'best-detail' }, h('div', { class: 'hint' }, T('bestiary_hint')));
    const list = h('div', { class: 'best-list' });
    const tabs = h('div', { class: 'tabs' });
    const show = (d, isBoss, mapName) => {
      const seen = S.seen[d.id];
      detail.innerHTML = '';
      if (!seen) { detail.append(h('div', { class: 'hint' }, T('unknown') + ' — ' + T('bestiary_hint'))); return; }
      const drops = C.dofus.filter(x => x.from.includes(d.id));
      const lore = d.lore || {};
      detail.append(...[   // (nulls filtered: Element.append writes them out as the text "null")
        h('h2', {}, L(d.name), isBoss ? h('span', { class: 'tag boss' }, d.final ? 'BOSS' : 'Mini-boss') : null),
        h('div', { class: 'art-wrap' }, artImg(d.art || ('a' + d.gfx), 'best-art')),
        d.flavor ? h('p', { class: 'flavor' }, '« ' + L(d.flavor) + ' »') : null,
        h('table', { class: 'stats' },
          h('tr', {}, h('td', {}, T('zone')), h('td', {}, mapName)),
          lore.lv ? h('tr', {}, h('td', {}, T('lvl_dofus')), h('td', {}, lore.lv[0] === lore.lv[1] ? lore.lv[0] : lore.lv[0] + ' - ' + lore.lv[1])) : null,
          lore.hp ? h('tr', {}, h('td', {}, T('hp_dofus')), h('td', {}, lore.hp[0] === lore.hp[1] ? fmtNum(lore.hp[0]) : fmtNum(lore.hp[0]) + ' - ' + fmtNum(lore.hp[1]))) : null,
          h('tr', {}, h('td', {}, T('attacks')), h('td', {}, (d.attacks || []).map(a => L(a)).join(', ') || '—')),
          h('tr', {}, h('td', {}, T('killed')), h('td', {}, fmtNum(S.kills[d.id] || 0))),
          drops.length ? h('tr', {}, h('td', {}, T('drops')), h('td', {}, ...drops.map(x => h('span', { class: 'drop' }, iconImg('dofus_hd_' + x.icon, 22), ' ', L(x.name))))) : null),
        h('p', { class: 'beh' }, behText(d))].filter(Boolean));
    };
    const showMap = (m) => {
      list.innerHTML = '';
      const ids = new Set();
      for (const w of m.waves) for (const [id] of w[2]) ids.add(id);
      for (const e of m.events) ids.add(e[2]);
      for (const [id] of m.rare || []) ids.add(id);
      const power = d => d.hp * (1 + d.dmg / 10) * (d.lore && d.lore.lv ? 1 + d.lore.lv[1] / 50 : 1);
      const mobs = [...ids].map(id => C.monsters[id]).filter(Boolean).sort((a, b) => power(a) - power(b));
      const bosses = m.bosses.map(b => C.bosses[b[1]]); if (m.secret) bosses.push(C.bosses[m.secret[1]]);
      bosses.sort((a, b) => (a.final ? 1 : 0) - (b.final ? 1 : 0) || power(a) - power(b));
      // 0.95: the mini-boss ToT's door lets out in this zone, first: the Tofuzmo, or Jorbak from C.jorbak.from on (events.js spawnMutant)
      { const J = C.jorbak, mu = J && C.monsters.jorbak && C.maps.indexOf(m) >= J.from ? C.monsters.jorbak : C.monsters.tofu_mutant; if (mu) bosses.unshift(mu); }
      const card = (d, isBoss) => {
        const seen = S.seen[d.id];
        const c = h('div', { class: 'best-card' + (seen ? '' : ' unseen') + (isBoss ? ' boss' : ''), onclick: () => { list.querySelectorAll('.best-card').forEach(e => e.classList.remove('sel')); c.classList.add('sel'); show(d, isBoss, L(m.name)); Audio2.blip('click'); } },
          artImg(d.art || ('a' + d.gfx), '', 240), h('div', { class: 'bname' }, seen ? L(d.name) : '???'));
        return c;
      };
      list.append(...mobs.map(d => card(d, false)), h('div', { class: 'sep' }, T('bosses')), ...bosses.map(d => card(d, true)));
    };
    C.maps.forEach((m, i) => {
      if (m.hidden && !S.unlocked.includes(m.id)) { tabs.append(h('button', { class: 'btn disabled', title: T('secret_hint') }, '🔒 ???')); return; }
      const t = btn(L(m.name), () => { tabs.querySelectorAll('.btn').forEach(e => e.classList.remove('active')); t.classList.add('active'); showMap(m); }, i === 0 ? 'active' : '');
      tabs.append(t);
    });
    showMap(C.maps[0]);
    const bossIds = Object.keys(C.bosses).filter(k => !C.bosses[k].doom && !C.bosses[k].unused);   // (0.61: not the bosses no zone shows)
    const total = Object.keys(C.monsters).length + bossIds.length;
    const seenN = [...Object.keys(C.monsters), ...bossIds].filter(k => S.seen[k]).length;
    this.rootEl.append(h('div', { class: 'screen bestiary' }, this.panel(`${T('bestiary')} — ${seenN}/${total}`, tabs, h('div', { class: 'best-layout' }, list, detail))));
  },
  // ------------------------------------------------ shop
  // tabs (left to right): spells, masteries, scrolls, hats, capes, pets. The preview under the grid can show any class,
  // sex and colours; items preview when the mouse is over them or when the controller / keyboard focus is on them
  shop() {
    this.clear(); document.body.classList.add('menu-bg'); this.screen = 'shop';
    if (typeof Nav !== 'undefined') Nav.forget('shop');   // (0.92: on the spells, the cursor starts on the first sub-tab, not on the Iop)
    const C = Game.C, S = Store.data;
    S.equip = S.equip || {}; S.spellLv = S.spellLv || {};
    const KINDS = ['spells', 'traits', 'mastery', 'scrolls', 'hats', 'capes', 'shields', 'pets'];   // (0.92: the shields)
    let kind = KINDS.includes(this._shopKind) ? this._shopKind : 'spells';
    let query = '';   // (0.65: the skin search, typed on the keyboard or the on-screen one)
    const ownedOn = {};   // (0.98.3: the 'Owned' filter, one for each skin tab)
    const norm = v => String(v || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim();
    const wallet = h('div', { class: 'wallet' });
    const grid = h('div', { class: 'shop-grid' });
    // 0.92 (the skin search scrolled with the list): the search sits above the list, outside the scrolling grid
    const searchSlot = h('div', { class: 'skin-search-slot' }), gridCol = h('div', { class: 'shop-gridcol' }, searchSlot, grid);
    const pk2 = Math.max(1, (window.devicePixelRatio || 1) * (Game._uiz || 1));
    const prevCanvas = h('canvas', { class: 'preview', width: Math.round(220 * pk2), height: Math.round(220 * pk2) });
    // the preview character: every class for pets; classes that wear no hats / capes are skipped on those tabs
    // (spells tab: every class, the preview follows the class picked in the sub-tabs)
    const skinList = () => kind === 'spells' ? C.classes : C.classes.filter(c => !c.nopets && (kind === 'pets' || !c.nohats)), skinCls = C.classes.filter(c => !c.nopets);
    let spellCls = (C.classes.find(c => c.id === 'iop') || C.classes[0]).id;   // (0.60: the Iop in every preview at first)
    let cls = kind === 'spells' ? C.classes.find(c => c.id === spellCls) : skinCls.find(c => c.id === 'iop') || skinCls[0];
    S.colors = S.colors || {};
    const colorsOf = c => S.colors[c.id] || baseColors(c, sex);
    let sex = cls.sprites[0] === cls.sprites[1] ? 0 : (S.lastSex || 0), colors = colorsOf(cls);
    let sprite = null, spriteKey = '';
    const loadSprite = async () => { const key = cls.id + '|' + sex; spriteKey = key; const sp = this.own(new CharSprite(cls.sprites[sex], colors, cls.nohats ? null : S.equip.hat || null, cls.nohats ? null : S.equip.cape || null, cls.nopets ? null : S.equip.pet || null, cls.nohats ? null : S.equip.shield || null)); await sp.load(); if (spriteKey === key) { if (sprite && sprite !== sp) this.drop(sprite); sprite = sp; } else this.drop(sp); };   // (0.93: UI.own)
    let previewItem = null, prevSpell = null, spT = 0;
    const setSpell = sid => { const d = sid ? C.spells[sid] : null; if (d === prevSpell) return; prevSpell = d; spT = 0; spellPreviewLoad(d); };
    const prevOf = el => { const c = el && el.closest && el.closest('[data-prev]'); if (!c) return null; const [slot, id] = c.getAttribute('data-prev').split(':'); return [slot, id]; };
    const buyFail = (card) => { Audio2.blip('wrong'); card.classList.add('shake'); setTimeout(() => card.classList.remove('shake'), 400); };
    const refresh = () => {
      wallet.innerHTML = ''; wallet.append(iconImg('KamaSymbol', 22), ' ', h('b', {}, fmtNum(S.kamas)), ' kamas');
      grid.innerHTML = ''; searchSlot.innerHTML = ''; previewItem = null;
      grid.classList.toggle('mastery-grid', kind === 'mastery' || kind === 'scrolls' || kind === 'spells' || kind === 'traits');
      grid.classList.toggle('spells-grid', kind === 'spells');   // (0.34: a class's six spells on one row, no scrolling)
      if (kind === 'spells') { // v2.0: every class spell, 5 levels each, sorted by class
        // 0.34: the global spells (every class gets them) first, before the Féca
        const GLOB = { id: 'glob', name: { fr: 'Sorts communs' }, spells: (C.globalSpells || []).map(g => g.id).filter(id => C.spells[id] && C.spells[id].t !== 'wheel'), emblemArt: 'b0' };   // (0.53: the Jeton de la Foire du Trool has nothing to level: not sold)
        const cur = spellCls === 'glob' ? GLOB : C.classes.find(c => c.id === spellCls) || C.classes[0];
        grid.append(h('div', { class: 'tabs subtabs' }, ...[GLOB, ...C.classes].map(c => {
          const done = c.spells.reduce((a, id) => a + (S.spellLv[id] || 0), 0), all = c.spells.length * 5;
          const b = btn([artImg(c.emblemArt || ('b' + c.breed), 'subic', 64), h('span', {}, c === GLOB ? T('shop_glob') : L(c.name)), done ? h('small', {}, done >= all ? '★' : done + '/' + all) : null], () => { spellCls = c.id; if (c !== GLOB && cls !== c) setCls(c); refresh(); }, c.id === cur.id ? 'active' : '');
          b.setAttribute('data-nav', 'scls:' + c.id); if (c === GLOB) b.setAttribute('data-nav-first', ''); return b;
        })));
        grid.append(h('div', { class: 'mastery-intro' }, T('spell_intro')));
        const COST = C.spellCost || [180, 400, 680, 1000, 1380], MAX = COST.length, per = Math.round((C.spellPer || 0.1) * 100);
        for (const sid of cur.spells) {
          const sp = C.spells[sid]; if (!sp) continue;
          const lv = S.spellLv[sid] || 0, cost = COST[lv];
          const card = h('div', { class: 'shop-item mastery spellshop' + (lv >= MAX ? ' equipped' : ''), 'data-nav': 'spell:' + sid, 'data-prev': 'spell:' + sid },
            h('div', { class: 'micons' }, iconImg('sp_' + sp.icon, 52)),
            h('div', { class: 'iname' }, L(sp.name)), h('div', { class: 'syn-mini', title: T('arm_boosted') }, ...boostsOf(sp).map(p => tipIcon(p.icon, L(p.name), 15))), sfMini(cur === GLOB ? null : cur.id, sid), h('div', { class: 'isub' }, T('spell_lv', { n: lv, m: MAX })),
            h('div', { class: 'mbar' }, h('div', { style: { width: (lv * 100 / MAX) + '%' } })),
            h('div', { class: 'isub' }, T('spell_bonus', { n: lv * per }) + (lv < MAX ? ' → ' + (lv + 1) * per + '%' : '')),
            h('div', { class: 'isub stot' }, ...fxNodes(shopSpellParts(sp, cur, lv, lv < MAX ? lv + 1 : null))),   // 0.60: what it really gives
            lv >= MAX ? h('div', { class: 'maxed' }, T('maxed')) : btn([iconImg('KamaSymbol', 14), ' ' + fmtNum(cost)], () => {
              if (S.kamas < cost) return buyFail(card);
              S.kamas -= cost; S.spellLv[sid] = lv + 1; Prog.add('kamasSpent', cost); Prog.add('spellBuys'); Store.save(); Audio2.blip('coin'); Audio2.ui('level', 0.6); Prog.check(null); refresh();
            }, S.kamas >= cost ? 'orange' : 'disabled'));
          grid.append(card);
        }
        return;
      }
      if (kind === 'traits') { // 0.22: the in-run characteristics get stronger too: +10% of their effect per level, same prices as the spells
        S.passLv = S.passLv || {};
        grid.append(h('div', { class: 'mastery-intro' }, T('traits_intro')));
        const COST = C.passCost || C.spellCost || [180, 400, 680, 1000, 1380], MAX = COST.length, per = Math.round((C.spellPer || 0.1) * 100);   // (0.60: passCost)
        for (const pa of C.passives) {
          if (pa.max <= 1 || pa.stat === 'amount') continue;   // (Phénix, Borné: nothing to scale; 0.53: Invocations is not sold)
          const lv = S.passLv[pa.id] || 0, cost = COST[lv];
          const card = h('div', { class: 'shop-item mastery' + (lv >= MAX ? ' equipped' : ''), 'data-nav': 'trait:' + pa.id },
            h('div', { class: 'micons' }, iconImg(pa.icon, 48)), h('div', { class: 'iname' }, L(pa.name)), h('div', { class: 'isub' }, T('spell_lv', { n: lv, m: MAX })),
            h('div', { class: 'mbar' }, h('div', { style: { width: (lv * 100 / MAX) + '%' } })),
            pa.perShop ? null : h('div', { class: 'isub' }, T('spell_bonus', { n: lv * per }) + (lv < MAX ? ' → ' + (lv + 1) * per + '%' : '')),   // (0.94: Vitalité / PA: the real value below says it)
            h('div', { class: 'isub stot' }, ...fxAround('trait_real', passiveShopParts(pa, lv, lv < MAX ? lv + 1 : null))),   // 0.60: one level in a run, really
            lv >= MAX ? h('div', { class: 'maxed' }, T('maxed')) : btn([iconImg('KamaSymbol', 14), ' ' + fmtNum(cost)], () => {
              if (S.kamas < cost) return buyFail(card);
              S.kamas -= cost; S.passLv[pa.id] = lv + 1; Prog.add('kamasSpent', cost); Store.save(); Audio2.blip('coin'); Audio2.ui('level', 0.6); Prog.check(null); refresh();
            }, S.kamas >= cost ? 'orange' : 'disabled'));
          grid.append(card);
        }
        return;
      }
      if (kind === 'scrolls') { // characteristic scrolls, up to 10 each, shared by every character
        S.scrolls = S.scrolls || {};
        grid.append(h('div', { class: 'mastery-intro' }, T('scroll_intro')));
        for (const sc of C.scrolls || []) {
          const lv = S.scrolls[sc.id] || 0, cost = C.scrollCost[lv], SMAX = C.scrollCost.length;
          const card = h('div', { class: 'shop-item mastery scroll' + (lv >= SMAX ? ' equipped' : ''), 'data-nav': 'scroll:' + sc.id },
            h('div', { class: 'micons' }, iconImg(sc.icon, 56)),
            h('div', { class: 'iname' }, L(sc.name)), h('div', { class: 'isub' }, T('scroll_lv', { n: lv })),
            h('div', { class: 'mbar' }, h('div', { style: { width: (lv * 100 / SMAX) + '%' } })),
            h('div', { class: 'isub' }, L(sc.desc)),
            lv && sc.tot ? h('div', { class: 'isub stot' }, T('scroll_total', { t: L(sc.tot).replace(/\{(\d)\}/g, (_, i) => ((sc.totN[+i] || 0) * lv).toFixed(1).replace(/\.0$/, '').replace('.', LANG === 'en' ? '.' : ',')) })) : null,   // 0.48: the cumulated bonus
            lv >= SMAX ? h('div', { class: 'maxed' }, T('maxed')) : btn([iconImg('KamaSymbol', 14), ' ' + fmtNum(cost)], () => {
              if (S.kamas < cost) return buyFail(card);
              S.kamas -= cost; S.scrolls[sc.id] = lv + 1; Prog.add('kamasSpent', cost); Store.save(); Audio2.blip('coin'); Audio2.ui('level', 0.6); Prog.check(null); refresh();
            }, S.kamas >= cost ? 'orange' : 'disabled'));
          grid.append(card);
        }
        return;
      }
      if (kind === 'mastery') {
        grid.append(h('div', { class: 'mastery-intro' }, T('mastery_intro')));
        for (const w of C.weapons) {
          const MMAX = C.masteryCost.length, mper = Math.round((C.masteryPer || 0.1) * 100), lv = Math.min(MMAX, S.mastery[w.id] || 0), cost = C.masteryCost[lv];
          const card = h('div', { class: 'shop-item mastery' + (lv >= MMAX ? ' equipped' : ''), 'data-nav': 'mastery:' + w.id },
            h('div', { class: 'micons' }, iconImg(w.masteryIcon || 'sp_' + w.mastery, 56)),   // (0.60: the mastery's picture alone)
            h('div', { class: 'iname' }, L(w.masteryName)), h('div', { class: 'isub' }, L(w.typeName || w.name) + ' — ' + T('mastery_lv', { n: lv, m: MMAX })),
            h('div', { class: 'mbar' }, h('div', { style: { width: (lv * 100 / MMAX) + '%' } })),
            h('div', { class: 'isub' }, T('mastery_bonus', { n: lv * mper }) + (lv < MMAX ? ' → ' + (lv + 1) * mper + '%' : '')),
            lv >= MMAX ? h('div', { class: 'maxed' }, T('maxed')) : btn([iconImg('KamaSymbol', 14), ' ' + fmtNum(cost)], () => {
              if (S.kamas < cost) return buyFail(card);
              S.kamas -= cost; S.mastery[w.id] = lv + 1; Prog.add('kamasSpent', cost); Store.save(); Audio2.blip('coin'); Audio2.play(w.snd, 0.8); Prog.check(null); refresh();
            }, S.kamas >= cost ? 'orange' : 'disabled'));
          grid.append(card);
        }
        return;
      }
      const all = kind === 'hats' ? C.hats : kind === 'pets' ? C.pets : kind === 'shields' ? C.shields || [] : C.capes; const slot = kind === 'hats' ? 'hat' : kind === 'pets' ? 'pet' : kind === 'shields' ? 'shield' : 'cape';
      const nq = norm(query), mine = ownedOn[kind] ? all.filter(it => S.owned.includes(it.id)) : all, list = nq ? mine.filter(it => norm(L(it.name)).includes(nq) || Object.values(it.name || {}).some(v => norm(v).includes(nq))) : mine;
      const fb = btn(T('owned_f'), () => { ownedOn[kind] = !ownedOn[kind]; refresh(); grid.scrollTop = 0; }, 'owned-f' + (ownedOn[kind] ? ' orange' : '')); fb.setAttribute('data-nav', 'owned-f');   // (data-nav: the cursor stays on it, Nav.press)
      searchSlot.append(h('div', { class: 'skin-search' }, fb, btn(['🔍 ', h('span', { class: query ? 'sq' : 'sq ph' }, query || T('search_ph'))], () => this.searchMenu(query, v => { query = v; refresh(); }), 'search-btn'),
        query ? btn('✕', () => { query = ''; refresh(); }, 'search-clear') : null, h('small', null, list.length + ' / ' + all.length)));
      if (!list.length) grid.append(h('div', { class: 'mastery-intro' }, T('search_none')));
      if (kind === 'pets' && !query) grid.append(h('div', { class: 'mastery-intro' }, T('pet_bonus')));
      if (kind === 'shields' && !query) grid.append(h('div', { class: 'mastery-intro' }, T('shield_bonus')));   // (0.92: +1 resistance, Run.shieldOn)
      if (!query) {
      const none = h('div', { class: 'shop-item' + (!S.equip[slot] ? ' equipped' : ''), 'data-nav': slot + ':none', 'data-prev': slot + ':' }, h('div', { class: 'noitem' }, iconImg('ui_none', 46)), h('div', { class: 'iname' }, T('none')),
        btn(!S.equip[slot] ? T('equipped') : T('equip'), () => { S.equip[slot] = null; Store.save(); if (sprite) sprite[slot] = null; refresh(); }, !S.equip[slot] ? 'orange' : ''));
      grid.append(none);
      }
      for (const it of list) {
        const owned = S.owned.includes(it.id); const eq = S.equip[slot] === it.id;
        const [t, n] = it.id.split('_');
        const card = h('div', { class: 'shop-item' + (owned ? ' owned' : '') + (eq ? ' equipped' : ''), 'data-nav': slot + ':' + it.id, 'data-prev': slot + ':' + it.id },
          iconImg(`it_${t}_${n}`, 52), h('div', { class: 'iname' }, L(it.name)), kind === 'shields' ? h('div', { class: 'isub' }, T('shield_res')) : null,
          owned ? btn(eq ? T('equipped') : T('equip'), () => { S.equip[slot] = it.id; Store.save(); if (sprite) sprite[slot] = it.id; refresh(); }, eq ? 'orange' : '')
            : btn([iconImg('KamaSymbol', 14), ' ' + fmtNum(it.price)], () => {
              if (S.kamas < it.price) return buyFail(card);
              S.kamas -= it.price; S.owned.push(it.id); S.equip[slot] = it.id; Prog.add('kamasSpent', it.price); Store.save(); if (sprite) sprite[slot] = it.id; Audio2.blip('coin'); Audio2.sfx('EVENT', 0.5); Prog.check(null); refresh();
            }, S.kamas >= it.price ? 'orange' : 'disabled'));
        grid.append(card);
      }
    };
    // preview follows the mouse, the keyboard focus and the controller highlight (Nav dispatches 'navfocus')
    // (a spell card: the class casts it)
    const take = p => { if (p && p[0] === 'spell') { setSpell(p[1]); previewItem = null; } else { setSpell(null); previewItem = p ? [p[0], p[1] || null] : null; } };
    const follow = (e) => { const p = prevOf(e.target); if (p) take(p); };
    grid.addEventListener('mouseover', follow); grid.addEventListener('focusin', follow);
    grid.addEventListener('mouseleave', () => { previewItem = null; setSpell(null); });
    // (0.92: off the skins — tabs, the preview's options, the palette — the preview wears what is equipped again; a spell
    // being cast keeps casting while the class arrows change the caster)
    const onNav = (e) => { if (!grid.isConnected) { document.removeEventListener('navfocus', onNav); return; } if (e.target.closest && (e.target.closest('.shop-preview') || e.target.closest('.cpal'))) { previewItem = null; return; } take(prevOf(e.target)); };
    this.listen(document, 'navfocus', onNav);
    const onType = (e) => {   // (0.65: on a skin tab, typing filters the list at once; Backspace / Escape edit the search)
      if (!grid.isConnected) { window.removeEventListener('keydown', onType, true); return; }
      if (this.modalOpen() || !['hats', 'capes', 'shields', 'pets'].includes(kind) || e.ctrlKey || e.metaKey || e.altKey) return;
      if (e.target && /INPUT|SELECT|TEXTAREA/.test(e.target.tagName)) return;
      if (e.key === 'Backspace' && query) query = query.slice(0, -1);
      else if (e.key === 'Escape' && query) query = '';
      else if ((e.key && e.key.length === 1 && /[\p{L}\p{N}'\-]/u.test(e.key)) || (e.key === ' ' && query)) { if (query.length < 24) query += e.key; }
      else return;
      e.preventDefault(); e.stopPropagation(); refresh(); grid.scrollTop = 0;
    };
    this.listen(window, 'keydown', onType, true);
    const LABEL = { traits: T('passives'), spells: T('spells'), mastery: T('mastery'), scrolls: T('scrolls'), hats: T('hats'), capes: T('capes'), shields: T('shields'), pets: T('pets') };
    const tabs = h('div', { class: 'tabs' }, ...KINDS.map(k => btn(LABEL[k], (e) => { kind = this._shopKind = k; tabs.querySelectorAll('.btn').forEach(b => b.classList.remove('active')); e.currentTarget.classList.add('active'); refresh(); grid.scrollTop = 0; if (!skinList().includes(cls)) stepCls(1); }, k === kind ? 'active' : '')));
    // preview options: class (◀ ▶), sex, colours
    const ptitle = h('div', { class: 'ptitle' });
    const setTitle = () => { ptitle.textContent = T('preview') + ' — ' + L(cls.name); };
    const sexBtn = btn('', () => { sex = 1 - sex; sprite = null; loadSprite(); setSex(); });
    const setSex = () => { sexBtn.textContent = sex ? '♀ ' + T('female') : '♂ ' + T('male'); sexBtn.style.visibility = cls.sprites[0] === cls.sprites[1] ? 'hidden' : 'visible'; };
    const setCls = (c) => { cls = c; if (cls.sprites[0] === cls.sprites[1]) sex = 0; colors = colorsOf(cls); sprite = null; loadSprite(); setTitle(); setSex(); clsName.textContent = L(cls.name); colorBox.style.display = cls.nocolors ? 'none' : ''; colorBox.redraw(); };
    const stepCls = (d) => { const l = skinList(); let i = l.indexOf(cls); setCls(l[(i + d + l.length) % l.length]); if (kind === 'spells' && spellCls !== cls.id) { spellCls = cls.id; refresh(); } };
    const clsName = h('span', { class: 'pcls' }, L(cls.name));
    const colorBox = this.colorRow(() => colors, c => { colors = c; S.colors[cls.id] = c; Store.save(); if (sprite) sprite.recolor(c); }, () => baseColors(cls, sex)); if (cls.nocolors) colorBox.style.display = 'none';
    const popts = h('div', { class: 'prev-opts' },
      h('div', { class: 'prev-row' }, btn('◀', () => stepCls(-1), 'arrow'), clsName, btn('▶', () => stepCls(1), 'arrow')),
      h('div', { class: 'prev-row' }, sexBtn), colorBox);
    setTitle(); setSex();
    this.rootEl.append(h('div', { class: 'screen shop' }, this.panel(T('shop'), h('div', { class: 'shop-top' }, tabs, wallet), h('div', { class: 'shop-layout' }, gridCol, h('div', { class: 'shop-preview' }, ptitle, prevCanvas, popts)))));
    refresh(); loadSprite();
    this._shopPrev = () => previewItem;   // (tests: what the shop's preview shows besides the equipped skins)
    let t = 0;
    this.previews.push((dt) => {
      t += dt; spT += dt; const g = prevCanvas.getContext('2d'); g.setTransform(pk2, 0, 0, pk2, 0, 0); g.clearRect(0, 0, 220, 220); if (!sprite) return;
      g.imageSmoothingQuality = 'high';
      if (prevSpell && kind === 'spells') return drawSpellPreview(g, sprite, cls, prevSpell, spT);
      const oh = sprite.hat, oc = sprite.cape, op = sprite.pet, os = sprite.shield;
      if (previewItem) sprite[previewItem[0]] = previewItem[1];
      const phase = Math.floor(t / 2.5) % 3; const a = ['staticR', 'runR', 'runL'][phase];
      sprite.draw(g, a, t, 120, 200, 2.6, false, { loop: true, moving: phase > 0, at: t });
      sprite.hat = oh; sprite.cape = oc; sprite.pet = op; sprite.shield = os;
    });
  },
  // ------------------------------------------------ achievements (succès)
  achievements() {
    this.clear(); document.body.classList.add('menu-bg'); this.screen = 'achievements';
    const S = Store.data; Prog.st(); const list = Game.C.achievements || [];
    const got = list.filter(a => S.ach[a.id]).length;
    const cards = list.map(a => {
      const ok = !!S.ach[a.id], v = Math.min(a.n, Prog.value(a.k));
      return h('div', { class: 'ach-card' + (ok ? ' done' : '') }, h('div', { class: 'ach-ic' }, iconImg(a.icon, 46, ok ? '' : 'locked')),
        h('div', { class: 'ach-txt' }, h('div', { class: 'ach-name' }, L(a.name)), h('div', { class: 'ach-desc' }, L(a.desc)),
          h('div', { class: 'mbar' }, h('div', { style: { width: Math.round(100 * v / a.n) + '%' } })), h('div', { class: 'ach-num' }, ok ? '✔ ' + new Date(S.ach[a.id]).toLocaleDateString(LOCALES[LANG]) : `${fmtNum(v)} / ${fmtNum(a.n)}`)));
    });
    this.rootEl.append(h('div', { class: 'screen achievements' }, this.panel(`🏆 ${T('achievements')} — ${T('ach_count', { a: got, b: list.length })}`, h('div', { class: 'ach-grid' }, ...cards))));
  },
  // ------------------------------------------------ nerd stats
  stats() {
    this.clear(); document.body.classList.add('menu-bg'); this.screen = 'stats';
    const S = Store.data, st = Prog.st(), C = Game.C;
    const top = (m) => { let b = null, bv = 0; for (const k in (m || {})) if (m[k] > bv) { bv = m[k]; b = k; } return b; };
    const dur = (s) => { s = Math.floor(s || 0); const hh = Math.floor(s / 3600), mm = Math.floor(s % 3600 / 60); return hh ? `${hh} h ${String(mm).padStart(2, '0')}` : fmtTime(s); };
    const fc = top(st.clsRuns), fw = top(st.weaponRuns), fs = top(Prog.mainSpellDmg(st, C)), nm = top(st.hurtBy);
    const nameOf = id => { if (!id) return T('st_none'); const c = C.classes.find(c => c.id === id); if (c) return L(c.name); const w = weaponById(C, id); if (w) return L(w.name); const sp = C.spells[id]; if (sp) return L(sp.name); const m = C.monsters[id] || C.bosses[id]; if (m) return L(m.name); const dk = { foudroiement: 'foudre' }[id] || id, dr = C.drops && C.drops[dk]; if (dr && dr.name) return L(dr.name); const pa = (C.passives || []).find(p => p.id === id); if (pa) return L(pa.name); const u = T('pn_' + id); return u !== 'pn_' + id ? u : id.charAt(0).toUpperCase() + id.slice(1).replace(/_/g, ' '); };   // (0.36: powers / bonus damage have real names, always capitalised)
    // 0.30: Dofus character-sheet look: boxes with a brown title strip, dotted leaders, and two tables with the same
    // fixed columns (they used to size their columns each on its own, so the numbers didn't line up)
    const row = (k, v) => h('div', { class: 'sb-row' }, h('span', {}, T(k)), h('i'), h('b', {}, v));
    const sec = (icon, title, ...rows) => h('div', { class: 'stat-box' }, h('div', { class: 'sb-title' }, iconImg(icon, 22), h('span', {}, title)), h('div', { class: 'sb-rows' }, ...rows));
    const runs = S.runs || 0;
    const table = (icon, title, head, rows) => h('div', { class: 'stat-box wide' }, h('div', { class: 'sb-title' }, iconImg(icon, 22), h('span', {}, title)),
      h('table', { class: 'stat-table' }, h('colgroup', {}, h('col', { class: 'c-name' }), h('col'), h('col'), h('col', { class: 'c-bar' }), h('col')),
        h('thead', {}, h('tr', {}, h('th', {}, head), h('th', {}, T('st_played')), h('th', {}, T('st_won')), h('th', {}, '%'), h('th', {}, T('st_dps_col')))),
        h('tbody', {}, ...rows.map(([pic, name, pl, won, dps]) => { const pc = pl ? Math.round(100 * Math.min(won, pl) / pl) : 0;
          return h('tr', { class: pl ? '' : 'none' }, h('td', {}, pic, h('span', {}, name)), h('td', {}, fmtNum(pl)), h('td', {}, fmtNum(won)), h('td', {}, h('div', { class: 'wbar' }, h('div', { style: { width: pc + '%' } }), h('span', {}, pl ? pc + ' %' : '—'))), h('td', {}, dps ? fmtNum(dps) : '—')); }))));
    const el = h('div', { class: 'stat-grid stats2' },
      sec('it_25_7', T('st_general'), row('st_runs', fmtNum(runs)), row('st_wins', fmtNum(st.wins || 0)), row('st_deaths', fmtNum(st.deaths || 0)), row('st_playtime', dur(st.playtime)),
        row('st_avgtime', runs ? fmtTime((st.playtime || 0) / runs) : '—'), row('st_distance', T('st_cells', { n: fmtNum((st.dist || 0) / 60) })), row('st_levelups', fmtNum(st.levelups || 0)), row('st_rerolls', fmtNum(st.rerolls || 0))),
      sec('it_6_1', T('st_combat'), row('st_kills', fmtNum(S.totalKills || 0)), row('st_elites', fmtNum(st.elites || 0)), row('st_bosses', fmtNum(st.bossKills || 0)),
        row('st_kpm', st.playtime ? (S.totalKills / (st.playtime / 60)).toFixed(1) : '—'), row('st_dmg_dealt', fmtNum(st.dmgDealt || 0)), row('st_dmg_taken', fmtNum(st.dmgTaken || 0)),
        row('st_best_hit', fmtNum(st.bestHit || 0)), row('st_crits', fmtNum(st.crits || 0)), row('st_dodges', fmtNum(st.dodges || 0)), row('st_revives', fmtNum(st.revived || 0))),
      sec('KamaSymbol', T('st_economy'), row('st_kamas_earned', fmtNum(st.kamasEarned || 0)), row('st_kamas_spent', fmtNum(st.kamasSpent || 0)), row('st_gems', fmtNum(st.gems || 0)),
        row('st_chests', fmtNum(st.chests || 0)), row('st_breads', fmtNum(st.breads || 0)), row('st_dofus', fmtNum(Object.values(S.dofus || {}).reduce((a, b) => a + b, 0))), row('st_tot', fmtNum(S.tot || 0))),
      sec('it_1_23', T('st_records'), row('st_best_kills', fmtNum(st.bestKills || 0)), row('st_best_level', fmtNum(st.bestLevel || 0)), row('st_best_dps', fmtNum(st.bestDps || 0)),
        row('st_best_kamas', fmtNum(st.bestKamas || 0)), row('st_doom', fmtTime(st.bestDoom || 0)), row('st_fav_class', nameOf(fc)), row('st_fav_weapon', nameOf(fw)), row('st_fav_spell', nameOf(fs)), row('st_nemesis', nameOf(nm))),
      table('Heart', T('st_classes'), T('st_class'), C.classes.map(c => [artImg(c.emblemArt || ('b' + c.breed), 'st-emb', 48), L(c.name), (st.clsRuns || {})[c.id] || 0, (st.clsWins || {})[c.id] || 0, (st.clsDps || {})[c.id] || 0])),
      table('it_24_7', T('st_zones'), T('st_zone'), C.maps.filter(m => !m.hidden || S.unlocked.includes(m.id)).map(m => [null, L(m.name), (st.mapRuns || {})[m.id] || 0, S.cleared[m.id] || 0, (st.mapDps || {})[m.id] || 0])));
    this.rootEl.append(h('div', { class: 'screen stats-screen' }, this.panel('📊 ' + T('stats'), el)));
  },
  // ------------------------------------------------ options
  optionsContent(inRun) {
    const S = Store.data.settings;
    const slider = (label, key) => h('label', { class: 'opt' }, h('span', {}, label), h('input', { type: 'range', min: 0, max: 1, step: 0.05, value: S[key], oninput: (e) => { S[key] = +e.target.value; if (key === 'music' && S.musicOff && S.music > 0) S.musicOff = false; Audio2.setVolumes(S.musicOff ? 0 : S.music, S.sfx); Store.save(); } }));
    const check = (label, key) => h('label', { class: 'opt' }, h('span', {}, label), h('input', { type: 'checkbox', ...(S[key] ? { checked: 'checked' } : {}), onchange: (e) => { S[key] = e.target.checked; Store.save(); } }));
    const autoSel = h('select', { onchange: (e) => { S.autoPick = e.target.value || null; Store.save(); } },
      h('option', { value: '' }, T('auto_off')), h('option', { value: 'kamas' }, T('take_kamas')), h('option', { value: 'bread' }, T('take_bread')));
    autoSel.value = S.autoPick || '';
    const langSel = h('select', { onchange: (e) => { setLang(e.target.value); if (!inRun) this.options(); else { this.closeModal(); this.pauseMenu(); } } }, ...LANGS.map(lg => h('option', { value: lg }, Game.C.langNames[lg])));
    langSel.value = LANG;
    return h('div', { class: 'options' },
      slider(T('music'), 'music'), slider(T('sfx'), 'sfx'),
      h('label', { class: 'opt' }, h('span', {}, T('auto_pick')), autoSel),
      check(T('dmg_numbers'), 'dmgNumbers'), check(T('shake'), 'shake'), check(T('chat'), 'chat'),
      // 0.44: three picture qualities (SD 720p / HD 1080p / UHD 1440p), one button each
      styleRow(),
      h('div', { class: 'opt', title: T('quality_hint') }, h('span', {}, T('quality')), h('span', { class: 'qrow' }, ...Object.keys(QUALITY).map(q =>
        (b => (b.dataset.q = q, b))(btn(QUALITY_LABEL[q] || q, () => { Game.setQuality(q); for (const e of document.querySelectorAll('.qbtn[data-q]')) e.classList.toggle('on', e.dataset.q === q); }, 'qbtn' + (Game.quality() === q ? ' on' : '')))))),
      // 0.95 (simple settings for low-end machines; the 'Renderer' row is gone: PixiJS always, the 2D canvas only
      // by itself when WebGL is missing or lost)
      this.pickRow('opt_fx', ['full', 'low', 'min'], Game.fxLevel(), v => Game.setFx(v), T('opt_fx_hint')),
      this.pickRow('opt_zoom', ['far', 'normal', 'close'], S.zoom || 'normal', v => Game.setZoom(v)),
      h('label', { class: 'opt' }, h('span', {}, T('lang')), langSel),
      h('label', { class: 'opt' }, h('span', {}, T('fullscreen')), btn('⛶', () => toggleFullscreen())),
      inRun ? null : h('label', { class: 'opt' }, h('span', {}, T('profiles') + ' — ' + Store.pname(Store.prof)), btn('👤 ' + T('profiles'), () => this.profilesMenu())),
      inRun ? null : this.saveRow());
  },
  // a row of buttons, one lit (the quality's look): T(key + '_' + value) on each
  pickRow(key, vals, cur, set, hint) {
    const row = h('span', { class: 'qrow' }, ...vals.map(v => (b => (b.dataset.v = v, b))(btn(T(key + '_' + v), () => { set(v); for (const e of row.children) e.classList.toggle('on', e.dataset.v === v); }, 'qbtn' + (cur === v ? ' on' : '')))));
    return h('div', { class: 'opt', ...(hint ? { title: hint } : {}) }, h('span', {}, T(key)), row);
  },
  // the renderer of the runs (0.62: PixiJS by default) — PixiJS (WebGL, pixi_render.js), or the 2D canvas as a fallback
  // (a PC without WebGL falls back by itself). The game starts again to switch (the 2D canvas is made transparent or not
  // at its creation). ?pixi=1 / ?pixi=0 in the address wins over it. 0.95: no longer in the options (unused)
  rendererRow() {
    const S = Store.data.settings, cur = S.renderer === 'canvas' ? 'canvas' : 'pixi';
    const W = { fr: ['Rendu', 'PixiJS (WebGL) : le plus fluide, recommandé. Canvas 2D : de secours, si l’image a un souci. Le jeu redémarre.'],
      en: ['Renderer', 'PixiJS (WebGL): the smoothest, recommended. Canvas 2D: a fallback, if the picture has a problem. The game restarts.'],
      de: ['Renderer', 'PixiJS (WebGL): am flüssigsten, empfohlen. Canvas 2D: Notlösung, falls das Bild Probleme macht. Das Spiel startet neu.'],
      es: ['Renderizado', 'PixiJS (WebGL): el más fluido, recomendado. Canvas 2D: de respaldo, si la imagen falla. El juego se reinicia.'],
      it: ['Rendering', 'PixiJS (WebGL): il più fluido, consigliato. Canvas 2D: di riserva, se l’immagine ha problemi. Il gioco si riavvia.'],
      nl: ['Weergave', 'PixiJS (WebGL): het vloeiendst, aanbevolen. Canvas 2D: reserve, als het beeld problemen geeft. Het spel start opnieuw.'],
      pt: ['Renderização', 'PixiJS (WebGL): o mais fluido, recomendado. Canvas 2D: de reserva, se a imagem tiver problemas. O jogo reinicia.'] }[LANG] || ['Renderer', ''];
    const pick = (v) => { if (v === cur) return; S.renderer = v; Store.save(); Audio2.blip('click'); setTimeout(() => location.reload(), 150); };
    return h('div', { class: 'opt', title: W[1] }, h('span', {}, W[0]), h('span', { class: 'qrow' },
      btn('PixiJS', () => pick('pixi'), 'qbtn' + (cur === 'pixi' ? ' on' : '')), btn('Canvas 2D', () => pick('canvas'), 'qbtn' + (cur === 'canvas' ? ' on' : '')),
      PX.on && PX.gpu ? h('small', { class: 'gpu-name', title: 'GPU' }, PX.gpu) : null));   // (0.93: the GPU really used)
  },
  // 0.59: the profile's save as a file: Exporter downloads it (.json); Importer reads one, checks it, asks once (the button
  // turns red: 'Replace Profile 1?'), then replaces the profile and reloads the game (the boot's refunds / migrations run)
  saveRow() {
    const file = h('input', { type: 'file', accept: '.json,application/json' }); file.hidden = true;
    let pending = null;
    const imp = btn('📂 ' + T('save_import'), () => {
      if (pending) { Store.importData(pending); pending = null; Audio2.blip('click'); toast(T('save_imported')); setTimeout(() => location.reload(), 700); return; }
      file.value = ''; file.click();
    });
    file.addEventListener('change', () => {
      const f = file.files && file.files[0]; if (!f) return;
      f.text().then(txt => {
        const r = Store.parseImport(txt);
        if (r.err) { pending = null; Audio2.blip('wrong'); toast(T(r.err)); return; }
        pending = r.data; imp.textContent = '⚠ ' + T('save_confirm', { p: Store.pname(Store.prof) }); imp.classList.add('danger');
      }, () => toast(T('save_bad')));
    });
    const exp = btn('💾 ' + T('save_export'), () => {
      const day = new Date().toISOString().slice(0, 10), who = Store.pname(Store.prof).replace(/[^\w-]+/g, '_');
      downloadText(`retro-survivors_${who}_${day}.json`, Store.exportText()); Audio2.blip('click'); toast(T('save_exported'));
    });
    const code = btn('🔢 ' + T('save_code'), () => this.saveCodeMenu());   // (0.60: the same save as a code)
    return h('div', { class: 'opt save-opt', title: T('save_hint') }, h('span', {}, T('save_label')), h('span', { class: 'qrow' }, exp, imp, code, file));
  },
  // 0.60: the save as a code (digits and lowercase letters): shown and copied, or pasted to replace the profile
  saveCodeMenu() {
    const box = h('textarea', { class: 'save-code', spellcheck: 'false', rows: 7 }), info = h('p', { class: 'sub' }, T('save_code_hint'));
    let pending = null;
    const copy = btn('📋 ' + T('save_code_copy'), async () => {
      const c = await Store.exportCode(); box.value = c; box.select(); pending = null; use.textContent = '⌨ ' + T('save_code_use'); use.classList.remove('danger');
      try { await navigator.clipboard.writeText(c); toast(T('save_code_copied', { n: fmtNum(c.length) })); } catch (e) { toast(T('save_code_shown', { n: fmtNum(c.length) })); }
      Audio2.blip('click');
    }, 'orange');
    const use = btn('⌨ ' + T('save_code_use'), async () => {
      if (pending === 'god') { Store.godMode(Game.C); pending = null; Audio2.blip('click'); toast(T('god_mode_on')); setTimeout(() => location.reload(), 900); return; }
      if (pending) { Store.importData(pending); pending = null; Audio2.blip('click'); toast(T('save_imported')); setTimeout(() => location.reload(), 700); return; }
      if (/^\s*godmode\s*$/i.test(box.value)) { pending = 'god'; use.textContent = '⚠ ' + T('god_mode_confirm', { p: Store.pname(Store.prof) }); use.classList.add('danger'); return; }   // (0.97: the test code, Store.godMode)
      const r = await Store.parseCode(box.value);
      if (r.err) { Audio2.blip('wrong'); toast(T(r.err)); return; }
      pending = r.data; use.textContent = '⚠ ' + T('save_confirm', { p: Store.pname(Store.prof) }); use.classList.add('danger');
    });
    box.addEventListener('input', () => { if (pending) { pending = null; use.textContent = '⌨ ' + T('save_code_use'); use.classList.remove('danger'); } });
    const el = h('div', { class: 'window modal savecode' }, h('div', { class: 'title' }, '🔢 ' + T('save_code')),
      h('div', { class: 'content' }, info, box, h('div', { class: 'start-row' }, copy, use, (() => { const b = btn(T('back'), () => this.closeModal()); b.setAttribute('data-back', ''); return b; })())));
    box.placeholder = T('save_code_paste'); this.openModal(el);
  },
  // ------------------------------------------------ controls: keyboard, controller and touch, side by side
  options() {
    this.clear(); document.body.classList.add('menu-bg'); this.screen = 'options';
    this.rootEl.append(h('div', { class: 'screen options-screen' }, this.panel(T('options'), this.optionsContent(false))));
  },
  credits() {
    this.clear(); document.body.classList.add('menu-bg'); this.screen = 'credits';
    // 0.61: no font line, no thanks line, no counters (patch_061 proofread the texts)
    // 0.79: his own text (C.credits: 'h' heading, 'p' paragraph, 'k' the Konami hint; **bold**, *italics*, a new line = line break)
    const link = x => x.split(/(https?:\/\/\S+)/).map(u => /^https?:\/\//.test(u) ? h('a', { href: u, target: '_blank', rel: 'noopener' }, u.replace(/^https?:\/\//, '')) : u);   // (0.91: the Discord link, clickable)
    const md = s => s.split('\n').flatMap((ln, i) => [i ? h('br') : null, ...ln.split(/(\*\*[^*]+\*\*|\*[^*]+\*)/).flatMap(x => /^\*\*/.test(x) ? [h('b', {}, x.slice(2, -2))] : /^\*.+\*$/.test(x) ? [h('i', {}, x.slice(1, -1))] : link(x))]).filter(x => x !== null && x !== '');
    const body = (Game.C.credits || []).map(([k, s]) => k === 'h' ? h('h3', {}, ...md(L(s))) : h('p', { class: k === 'k' ? 'konami' : null }, ...md(L(s))));
    this.rootEl.append(h('div', { class: 'screen credits' }, this.panel(T('credits'), ...body)));
  },
  // ------------------------------------------------ in-run modals
  pauseMenu() {
    const R = Game.run; const C = Game.C;
    const build = h('div', { class: 'build' },
      h('div', { class: 'brow' }, ...R.spells.map(s => h('div', { class: 'bitem', title: L(s.def.name) }, iconImg('sp_' + s.def.icon, 36), h('span', {}, s.level + '/' + MAX_SPELL_LV))),
        R.weapon ? h('div', { class: 'bitem weapon' + (R.weapon.def.blood ? ' blood' : R.weapon.def.unique ? ' unique' : ''), title: L(R.weapon.def.name) }, iconImg(R.weapon.icon, 36), h('span', {}, R.weapon.level + '/' + MAX_SPELL_LV)) : null,
        R.weapon && R.weapon.finale ? h('div', { class: 'bitem weapon evo', title: L(R.weapon.finale.name) + ' — ' + L(R.weapon.finale.desc) }, h('b', { class: 'evo-mini' }, '✦'), h('small', {}, L(R.weapon.finale.name))) : null,
        R.totBuff ? h('div', { class: 'bitem evo', title: T('tot_bonus') }, iconImg(R.totBuff.icon, 26), h('small', {}, '+' + (Math.round(R.totBuff.v * 1000) / 10).toLocaleString(LANG) + '% ' + L(R.totBuff.name))) : null,
        R.allies.some(a => a.kind === 'drago') ? h('div', { class: 'bitem evo', title: L(Game.C.drago.name) }, iconImg(Game.C.drago.icon, 30), h('small', {}, L(Game.C.drago.name))) : null),
      h('div', { class: 'brow' }, ...C.passives.filter(p => R.passives[p.id] && p.id !== R.bonusPassive).concat(C.passives.filter(p => p.id === R.bonusPassive)).map(p => h('div', { class: 'bitem' + (p.id === R.bonusPassive ? ' sp-blue' : ''), title: L(p.name) }, iconImg(p.icon, 28), h('span', {}, R.passives[p.id] + '/' + p.max)))),
      this.relicSummary(R),   // 0.85: what the relics give, between the characteristics and the Dofus
      h('div', { class: 'brow' }, ...R.dofus.map(d => h('div', { class: 'bitem', title: L(d.name) + ' — ' + L(d.desc) }, iconImg('dofus_hd_' + d.icon, 30)))),
      h('div', { class: 'brow sf-brow' }, ...(C.spellFusions || []).filter(f => sfusionOf(f, R.cls.id)).map(f => h('div', { class: 'bitem sf' + (R.sfused.has(f.id) ? ' done' : ''), title: L(C.spells[f.id].name) + ' — ' + L(C.spells[f.id].desc) }, ...sfRecipe(R, f), h('b', null, '→'), iconImg('sp_' + C.spells[f.id].icon, 28)))));   // 0.60: the spell fusions
    const st = R.stats;
    // two columns (the run on the left, the options on the right): the whole menu fits a 16:9 screen without scrolling
    const el = h('div', { class: 'window modal pause' }, h('div', { class: 'title' }, T('paused')), h('div', { class: 'content' },
      h('div', { class: 'pause-cols' },
        h('div', { class: 'pause-left' },
          h('div', { class: 'run-stats' }, `${T('time')} ${fmtTime(R.time)} — ${T('level')} ${R.level} — ${T('kills')} ${fmtNum(R.kills)} — ${fmtNum(R.kamas)} K`),
          h('div', { class: 'run-stats small' }, `${T('stats_hp')} ${Math.ceil(R.player.hp)}/${st.maxHp} · ${T('stats_might')} ${Math.round(st.might * 100)}% · ${T('stats_armor')} ${st.armor.toFixed(0)} · PA ${Math.round((1 - st.cooldown) * 100)}% · PM ${Math.round(st.speed * 100)}% · Crit ${Math.round(st.crit * 100)}%`),
          build),
        this.optionsContent(true)),
      h('div', { class: 'start-row' },
        btn(T('quit'), (e) => {
          const b = e.currentTarget;
          if (b.dataset.armed) { this.closeModal(); Game.paused = false; R.abandoned = true; R.endRun(false); return; }
          b.dataset.armed = '1'; b.textContent = T('confirm_quit'); b.classList.add('orange', 'dark');
        }),
        btn(T('resume'), () => Game.togglePause(), 'orange big'))));
    this.openModal(el);
  },
  // 0.85: the bonuses of the run's relics, summed by the game's own rule (Run.relicStats: added up, max HP
  // multiplied), named after the characteristic of the same stat (its icon too) or C.ui 'rb_<stat>'; a new relic or a new
  // kind of bonus shows without any change here. Formats: RB_FMT (pct = a share shown in %, n = a plain number, s = a second)
  relicSummary(R) {
    const rel = R.relics || []; if (!rel.length) return null;
    const tot = {}, C = Game.C;
    for (const r of rel) {
      for (const k in r.bonus || {}) tot[k] = k === 'maxhp' ? (1 + (tot[k] || 0)) * (1 + r.bonus[k]) - 1 : (tot[k] || 0) + r.bonus[k];
      for (const k in r.special || {}) if (k !== 'dashCd') tot[k] = (tot[k] || 0) + r.special[k]; else tot[k] = (tot[k] || 1) * r.special[k];
    }
    const RB_FMT = { armor: 'n', amount: 'n', reflect: 'n', regen: 's', dashCd: 'mul' };
    const val = (k, v) => { const f = RB_FMT[k] || 'pct', sg = v < 0 ? '−' : '+', a = Math.abs(v);
      if (f === 'n') return sg + fmtNum(Math.round(a * 100) / 100); if (f === 's') return sg + String(Math.round(a * 100) / 100).replace('.', LANG === 'en' ? '.' : ',') + '/s';
      if (f === 'mul') return '×' + String(Math.round(v * 100) / 100); return sg + String(Math.round(a * 1000) / 10).replace('.', LANG === 'en' ? '.' : ',') + ' %'; };
    const chips = Object.keys(tot).filter(k => Math.abs(tot[k] - (k === 'dashCd' ? 1 : 0)) > 1e-9).map(k => {
      const p = C.passives.find(x => x.stat === k), nm = p ? L(p.name) : T('rb_' + k);
      return h('div', { class: 'rb-chip', title: nm }, p ? iconImg(p.icon, 20) : h('i', { class: 'rb-dot' }), h('span', { class: 'rb-n' }, nm), h('b', null, val(k, tot[k])));
    });
    return h('div', { class: 'relic-sum' }, h('div', { class: 'rb-head' }, h('b', null, T('relic_bonuses')), h('span', { class: 'rb-icons' }, ...rel.map(r => tipIcon(r.icon, L(r.name) + ' — ' + L(r.desc), 24)))),
      h('div', { class: 'rb-grid' }, ...chips));
  },
  // a Dofus fell from a monster: the game pauses on a little celebration
  exploitMenu(dof, from) {
    const sparks = h('div', { class: 'ex-sparks' }, ...Array.from({ length: 18 }, (_, i) => h('i', { style: { '--a': (i * 20) + 'deg', '--c': FW_COLS[i % FW_COLS.length], '--d': (i % 6) * 0.12 + 's' } })));
    const el = h('div', { class: 'window modal exploit', style: { '--c': dof.color } }, h('div', { class: 'title' }, T('exploit')), h('div', { class: 'content' },
      h('div', { class: 'ex-dofus' }, sparks, iconImg('dofus_hd_' + dof.icon, 104)),
      h('h2', { style: { color: dof.color } }, L(dof.name)),
      h('p', {}, T(from === 'ToT' ? 'exploit_tot' : 'exploit_dofus', { m: from, d: L(dof.name) })),
      h('p', { class: 'dofus-effect', style: { color: dof.color } }, L(dof.desc)),
      h('p', { class: 'sub' }, T('dofus_forever')),
      h('div', { class: 'start-row' }, btn(T('continue'), () => this.closeModal(), 'orange big'))));
    this.openModal(el);
    if (Game.debug.bot) setTimeout(() => this.closeModal(), 300);
  },
  // v1.7 Manuel du Tailleur: a slot machine with suspense, then the random look it unlocked (already saved before the show)
  tailorMenu(prize) {
    const C = Game.C, CELL = 140, all = [...C.hats, ...C.capes, ...C.pets];
    const ic = it => { const [t, n] = it.id.split('_'); return `it_${t}_${n}`; };
    const N = 46, P = 40;   // reel length, index of the prize
    const items = Array.from({ length: N }, (_, i) => i === P ? prize.item : pick(all));
    if (prize.kind === 'kamas') items[P] = null;
    const reel = h('div', { class: 'reel' }, ...items.map(it => h('div', { class: 'cell' }, it ? iconImg(ic(it), 104) : iconImg('KamaSymbol', 90))));
    const slot = h('div', { class: 'slot' }, reel, h('div', { class: 'pointer' }));
    const status = h('div', { class: 't-status' }, T('tailor_spin'));
    const kindName = { hats: T('hats'), capes: T('capes'), pets: T('pets') }[prize.kind] || '';
    const prizeEl = h('div', { class: 't-prize' }, prize.kind === 'kamas' ? T('tailor_kamas', { n: fmtNum(prize.v) }) : L(prize.item.name) + (kindName ? ' — ' + kindName : ''));
    const sub = h('p', { class: 'sub', style: { opacity: 0 } }, prize.kind === 'kamas' ? T('tailor_all') : T('tailor_won'));
    let raf = 0;   // (0.59: declared before the button: the bot's click came before 'let raf' further down — a page error)
    const okBtn = btn(T('tailor_ok'), () => { cancelAnimationFrame(raf); this.closeModal(); }, 'orange big'); okBtn.style.visibility = 'hidden';
    const lights = () => h('div', { class: 'lights' }, ...Array.from({ length: 9 }, () => h('i')));
    const el = h('div', { class: 'window modal tailor' }, h('div', { class: 'title' }, L(C.manuel.name)), h('div', { class: 'content' },
      h('div', { class: 'ex-dofus' }, iconImg(C.manuel.icon, 74)), lights(), slot, lights(), status, prizeEl, sub, h('div', { class: 'start-row' }, okBtn)));
    this.openModal(el);
    if (Game.debug.bot) { setTimeout(() => this.closeModal(), 300); return; }
    // 0.98: the action key (A, Enter, Space, E — Nav.press) pressed twice within 0.6 s skips to the prize, already saved
    // before the show (tailorPrize): skipping only draws the end; once it is there, the key goes back to the OK button
    let done = false, tapAt = -1e9;
    const finish = () => {
      done = true; cancelAnimationFrame(raf);
      reel.style.transform = `translateX(${xAt(P)}px)`;
      slot.classList.add('win'); el.classList.add('jackpot'); status.textContent = T('tailor_jackpot');
      prizeEl.classList.add('show'); sub.style.opacity = 1; okBtn.style.visibility = 'visible';
      Audio2.sfx('EVENT', 0.9); Audio2.blip('level'); Audio2.play('coffre', 0.7);
      const sp = h('div', { class: 'ex-sparks' }, ...Array.from({ length: 18 }, (_, i) => h('i', { style: { '--a': (i * 20) + 'deg', '--c': FW_COLS[i % FW_COLS.length], '--d': (i % 6) * 0.12 + 's' } })));
      slot.parentElement.querySelector('.ex-dofus').append(sp);
      Nav.el = null;
    };
    const act = this.modal.onAct = () => { if (done) return false; const n = performance.now(); if (n - tapAt < 600) finish(); else tapAt = n; return true; };
    slot.addEventListener('click', act);   // (a mouse or a finger: two taps on the reel)
    // the reel: a long spin that slows down, stops one cell short ("so close…"), then clicks onto the prize
    const W = () => slot.clientWidth || 420, x0 = 0;
    const xAt = i => -(i * CELL) + W() / 2 - CELL / 2;
    const T1 = 5.2, start = performance.now(); let last = -1, phase = 0, nudgeT = 0;
    const ease = k => 1 - Math.pow(1 - k, 4);
    const step = () => {
      if (!el.isConnected || done) return;
      const t = (performance.now() - start) / 1000;
      let x;
      if (phase === 0) {
        const k = Math.min(1, t / T1); x = x0 + (xAt(P - 1) - x0) * ease(k);
        if (k > 0.72 && status.textContent !== T('tailor_slow')) status.textContent = T('tailor_slow');
        if (k >= 1) { phase = 1; nudgeT = t; status.textContent = T('tailor_almost'); Audio2.blip('wrong'); }
      } else if (phase === 1) {
        x = xAt(P - 1) + Math.sin((t - nudgeT) * 30) * 3 * Math.max(0, 1 - (t - nudgeT) / 0.9);   // it trembles…
        if (t - nudgeT > 0.95) { phase = 2; nudgeT = t; }
      } else {
        const k = Math.min(1, (t - nudgeT) / 0.38), b = k < 1 ? 1 - Math.pow(1 - k, 3) * Math.cos(k * 9) : 1;
        x = xAt(P - 1) + (xAt(P) - xAt(P - 1)) * b;
        if (k >= 1) { finish(); return; }
      }
      reel.style.transform = `translateX(${x}px)`;
      const cell = Math.floor((W() / 2 - x) / CELL);   // a tick each time a picture passes the frame
      if (cell !== last) { last = cell; Audio2.blip('click'); }
      raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
  },
  upgradeCard(R, o, onPick) {
    const C = Game.C;
    let icon, name, desc, lvtxt;
    let extra = '';
    if (o.kind === 'spell') {
      const sp = C.spells[o.id]; icon = iconImg('sp_' + sp.icon, 48); name = L(sp.name);
      desc = o.lv === 1 ? [fxDesc(L(sp.desc)), h('div', { class: 'up-real' }, fxNodes(realSummaryParts(R, sp)))] : diffNodes(R, sp, o.lv);   // 0.53: the real numbers (0.98: coloured, fxNodes)
      lvtxt = o.lv === 1 ? T('new_') : `${T('level')} ${o.lv}`;
    } else if (o.kind === 'weapon') {
      const w = weaponById(C, o.id); icon = iconImg(w.icon, 50); name = L(w.name);   // (0.60: a Soif de Sang's picture has blood on its blade)
      desc = o.lv === 1 ? [fxDesc(L(w.desc)), h('div', { class: 'up-real' }, fxNodes(realSummaryParts(R, w)))]   // 0.53: real numbers (the mastery is in them)
        : diffNodes(R, w, o.lv, w.leech ? [fxPart('leech', T('p_leech'), `${pctLeech(w.leech[o.lv - 2])} → ${pctLeech(w.leech[o.lv - 1])}`)] : []);   // 0.48: what the level adds to the life steal
      lvtxt = o.lv === 1 ? (w.blood ? T('blood_tag') : T('weapon_tag')) : `${T('level')} ${o.lv}`; extra = ' weapon' + (w.blood ? ' blood' : '');   // (0.60: every weapon is special: no purple 'unique' frame)
    } else if (o.kind === 'fusion') {
      // 0.25 weapon fusion: the weapon's picture inside an animated ring of the element, the characteristic on top
      const f = C.fusions.find(x => x.id === o.id), W = R.weapon;
      icon = h('span', { class: 'fusion-ic', style: { '--fc': f.color } }, h('i', { class: 'f-ring' }), iconImg(W.icon, 46), h('span', { class: 'f-stat' }, iconImg(f.icon, 26)), ...Array.from({ length: 6 }, (_, i) => h('b', { class: 'f-spark', style: { '--i': i } })));
      name = L(f.name); desc = [fxDesc(L(f.desc)), ' ', fxDesc(T('fusion_note'), 'spec')]; lvtxt = T('fusion_tag'); extra = ' weapon fusion';
    } else if (o.kind === 'sfusion') {
      // 0.60 spell fusion: the fused spell's picture in a turning gold / violet ring, its recipe, what it really does
      const sp = C.spells[o.id], f = (C.spellFusions || []).find(x => x.id === o.id);
      icon = h('span', { class: 'sf-ic' }, h('i', { class: 'f-ring' }), iconImg('sp_' + sp.icon, 54), ...Array.from({ length: 8 }, (_, i) => h('b', { class: 'f-spark', style: { '--i': i } })));
      name = L(sp.name); lvtxt = T('sfusion_tag'); extra = ' sfusion';
      desc = [h('div', { class: 'sf-recipe' }, ...sfRecipe(R, f)), fxDesc(L(sp.desc)), h('div', { class: 'up-real' }, fxNodes(realSummaryParts(R, sp))), h('div', { class: 'sf-note fx-spec' }, f.kind === 'weapon' ? T('sfusion_keep') : T('sfusion_slot'))];
    } else if (o.kind === 'wevo') {
      // weapon finale: one single pick that also gives the weapon its own look (a real weapon of the same kind)
      const E = evoDef(o.id);
      icon = h('span', { class: 'evo-ic' }, iconImg(E.e.icon || E.w.icon, 50), h('b', { class: 'evo-star' }, '✦')); name = L(E.e.name) + ' — ' + L(E.e.skinName || E.w.name);
      desc = [fxDesc(L(E.e.desc)), ' ', fxDesc(T('final_note', { n: L(E.e.skinName || E.w.name) }), 'spec')];
      lvtxt = T('final_tag'); extra = ' weapon evo' + (E.w.blood ? ' blood' : '');
    } else {
      const p = C.passives.find(p => p.id === o.id); icon = iconImg(p.icon, 44); name = L(p.name);
      const pp = passiveParts(p, o.lv), pn = pp ? fxNodes(pp) : fxDesc(L(p.desc));
      desc = ['reflect', 'revive', 'spellslot', 'luck', 'evade', 'amount', 'growth'].includes(p.stat) ? [fxDesc(L(p.desc)), h('div', { class: 'up-real' }, pn)] : pn;   // 0.53: the real totals (shop included)
      if (p.stat === 'revive' || p.stat === 'spellslot') desc = fxDesc(L(p.desc));
      lvtxt = o.lv === 1 ? T('new_') : `${T('level')} ${o.lv}`;
    }
    const kindTxt = o.kind === 'spell' ? (C.spells[o.id].glob ? T('g_spell') : T('spells')) : o.kind === 'sfusion' ? T('sfusion_tag') : o.kind === 'fusion' ? T('fusion_tag') : o.kind === 'weapon' ? (weaponById(C, o.id).blood ? T('blood_tag') : T('weapon_tag')) : o.kind === 'wevo' ? T('evo_tag') : T('passives');
    const maxLv = o.kind === 'passive' ? (C.passives.find(p => p.id === o.id) || {}).max || 5 : o.kind === 'wevo' || o.kind === 'fusion' || o.kind === 'sfusion' ? 1 : MAX_SPELL_LV;   // (0.91: 4 levels since 0.81 — the cards still showed 6 stars)
    const stars = h('div', { class: 'up-stars' }, ...Array.from({ length: maxLv }, (_, i) => h('span', { class: i < o.lv ? 'on' : '' }, '★')));
    if (o.kind === 'spell' && C.spells[o.id].glob) extra += ' glob';
    { const hint = R && (o.kind === 'spell' || o.kind === 'weapon') ? sfHint(R, o) : null; if (hint) desc = [].concat(desc, hint); }   // (0.60: what it fuses into)
    if (R && (o.kind === 'spell' || o.kind === 'weapon') && sfReady(R, o)) extra += ' fusable';   // (0.91: it fuses with something already owned)
    // 0.98.3: the special ones stand out from the other cards: the Trool's token and the Gladiatrool's characteristic, a dark blue rim and sparks (#navglide's, CSS-animated)
    const blue = (o.kind === 'spell' && C.spells[o.id].t === 'wheel') || (o.kind === 'passive' && R && R.bonusPassive === o.id);
    if (blue) { extra += ' sp-blue'; icon = [icon, ...Array.from({ length: 10 }, (_, i) => { const a = i * TAU / 10, dx = Math.cos(a), dy = Math.sin(a); return h('i', { style: { left: 50 + dx * 50 + '%', top: 50 + dy * 50 + '%', '--d': (-i * 0.17 * 3 % 1.6).toFixed(2) + 's', '--dx': (dx * 12).toFixed(1) + 'px', '--dy': (dy * 12 - 4).toFixed(1) + 'px' } }); })]; }
    return h('div', { class: 'up-card' + (o.lv === 1 ? ' new' : '') + extra + (o.kind === 'passive' ? ' passive' : ''), onclick: () => onPick(o) },
      h('div', { class: 'up-kind' + (kindTxt.length > 13 ? ' long' : '') }, kindTxt), h('div', { class: 'up-icon' }, ...[].concat(icon)), h('div', { class: 'up-name' }, name), h('div', { class: 'up-lv' }, lvtxt), stars, h('div', { class: 'up-desc' }, ...[].concat(desc)), R ? this.synergyLine(R, o) : null);   // 0.28: what it works with (ui_armory.js)
  },
  levelUpMenu(R, opts, rolled) {
    this.levelUpOpen = true;
    if (R.rerolls > 0) ['ui603', 'ui611', 'ui605'].forEach(f => FxSheets.load(f));   // (0.95: the die ready before a reroll: an emoji die showed first)
    let busy = false;
    const pick_ = (o) => { if (busy) return; busy = true; R.applyUpgrade(o); Audio2.blip('click'); this.closeModal(); };
    // 0.60: Bannir (C.banishes a run, shared by the spells, weapons and characteristics): the next card clicked never comes back this run, new cards are dealt; Passer (once a run)
    let banishing = false;
    const onCard = (o) => {
      if (!banishing) return pick_(o);
      if (busy) return; busy = true; R.banishes--; R.banish(o); if (R.ps) R.ps.banishes = (R.ps.banishes || 0) + 1;
      const card = el.querySelectorAll('.up-card')[opts.indexOf(o)], name = ((card && card.querySelector('.up-name')) || {}).textContent || '';
      R.chat('✖ ' + (o.kind === 'weapon' ? T('banished_w', { t: L(weaponById(R.C, weaponType(R.C, o.id)).name) }) : T('banished', { n: name })), '#ff9a8a'); Audio2.play('saut', 0.5, 0.8);   // (0.95: a weapon, its whole type)
      deckVars(el); el.classList.add('rolling');
      setTimeout(() => { this._luSize = [el.offsetWidth, el.offsetHeight]; const fresh = R.upgradeOptions(opts.length); if (!fresh.length) { this.closeModal(); return; } this.levelUpMenu(R, fresh, true); }, 450);
    };
    const banish = R.banishes > 0 ? btn([h('span', { class: 'lu-ic' }, '✖'), ' ' + T('banish'), h('small', null, ' ' + T('once_left', { n: R.banishes }))], () => {
      if (busy) return; setBanish(!banishing);
    }, 'banish') : null;
    if (banish) banish.title = T('banish_w');   // (0.95: the weapon rule, also on the button)
    const setBanish = (on) => { banishing = on; el.classList.toggle('banishing', on); if (banish) banish.classList.toggle('on', on); $('.sub', el).textContent = on ? T('banish_pick') + (opts.some(o => o.kind === 'weapon') ? ' — ' + T('banish_w') : '') : T('choose_upgrade'); };   // (0.95: a weapon bans its whole type: said when one is offered)
    const skip = R.skips > 0 ? btn([h('span', { class: 'lu-ic' }, '»'), ' ' + T('skip'), h('small', null, ' ' + T('once_left', { n: R.skips }))], () => {
      if (busy) return; busy = true; R.skips--; if (R.ps) R.ps.skips = (R.ps.skips || 0) + 1; R.chat('» ' + T('skipped'), '#c9d6e8'); this.closeModal();
    }, 'skip') : null;
    const reroll = R.rerolls > 0 ? btn([h('span', { class: 'dice' }, diceFace(R.rerolls)), ' ' + T('rerolls', { n: R.rerolls })], () => {
      if (R.rerolls <= 0 || busy) return; busy = true; R.rerolls--; if (R.ps) R.ps.rerolls++;
      // 0.60: the cards are gathered (0.95: into a deck, deckVars), then the client's Écaflip die
      // (spell clip 603, Chance d'Écaflip) is thrown in big, bounces three times in a whirl of the Bluff cards' suits (611),
      // lands in a golden flash with the lucky clover (605); the new choices are dealt after (1.55 s)
      deckVars(el); el.classList.add('rolling'); Audio2.play('saut', 0.5, 1.3);
      const stage = h('canvas', { class: 'dice-stage' }); $('.content', el).append(stage);
      diceStage(stage, R);
      setTimeout(() => { this._luSize = [el.offsetWidth, el.offsetHeight]; const fresh = R.upgradeOptions(opts.length); this.levelUpMenu(R, fresh.length ? fresh : opts, true); }, 1550);
    }, 'reroll') : null;
    const el = h('div', { class: 'window modal levelup' + (rolled ? ' rolled' : '') }, h('div', { class: 'title' }, h('span', { class: 'lvl-star' }, '★'), T('levelup') + ` — ${T('level')} ${R.level}`),
      h('div', { class: 'content' }, h('div', { class: 'sub' }, T('choose_upgrade')), h('div', { class: 'up-cards' }, ...opts.map((o, i) => { const c = this.upgradeCard(R, o, onCard); if (rolled) { c.style.setProperty('--d', (i * 0.09) + 's'); c.append(h('span', { class: 'up-sheen' })); } else c.style.animationDelay = (i * 0.07) + 's'; return c; })), (reroll || banish || skip) ? h('div', { class: 'reroll-row' }, reroll, banish, skip) : null));
    if (rolled && this._luSize) { el.style.minWidth = this._luSize[0] + 'px'; el.style.minHeight = this._luSize[1] + 'px'; }   // 0.37: a dice roll never resizes the window
    this._luBack = () => { if (banishing) { setBanish(false); Audio2.blip('click'); } };   // (B / Échap: only out of the Bannir mode)
    this.openModal(el); fitCardsSoon(el);   // (0.62: no card text is ever cut)
    if (rolled) { deckVars(el); el.classList.add('dealing'); setTimeout(() => el.classList.remove('dealing'), (1.1 + 0.09 * opts.length) * 1000 + 100); }   // (0.95: dealt from the deck, index.html cardDeal: 1.1 s each)
    this._keyPick = null;
  },
  levelUpMaxed(R) {
    this.levelUpOpen = true;
    let always = false;
    const choose = (kind) => { R.applyUpgrade({ kind }); Store.data.settings.lastAutoPick = kind; if (always) { Store.data.settings.autoPick = kind; Store.save(); R.chat(T('always_pick') + ' ✔ (' + (kind === 'kamas' ? T('take_kamas') : T('take_bread')) + ')', '#ffd27a'); } this.closeModal(); };
    const el = h('div', { class: 'window modal levelup' }, h('div', { class: 'title' }, T('levelup') + ` — ${T('level')} ${R.level}`),
      h('div', { class: 'content' }, h('div', { class: 'sub' }, T('nothing_left')), h('div', { class: 'up-cards' },
        h('div', { class: 'up-card', onclick: () => choose('kamas') }, h('div', { class: 'up-icon' }, iconImg('KamaSymbol', 44)), h('div', { class: 'up-txt' }, h('div', { class: 'up-name' }, T('take_kamas')), h('div', { class: 'up-desc' }, T('take_kamas_d', { n: R.C.maxKamas || 10 })))),
        h('div', { class: 'up-card', onclick: () => choose('bread') }, h('div', { class: 'up-icon' }, iconImg(potionIcon(), 44)), h('div', { class: 'up-txt' }, h('div', { class: 'up-name' }, T('take_bread')), h('div', { class: 'up-desc' }, T('take_bread_d'))))),
        h('label', { class: 'always-sw' }, h('input', { type: 'checkbox', onchange: (e) => { always = e.target.checked; } }), h('span', { class: 'sw-box' }, h('b', null, '✔')), h('span', { class: 'sw-txt' }, T('always_pick')), h('small', null, T('always_hint')))));
    this.openModal(el);
  },
  // ToT's door: the run's music pauses on a festive tune while the choice is open (onBonus: once his Dofus was won)
  doorMenu(onEnter, onBonus) {
    this.levelUpOpen = true;
    const go = (f) => { this.closeModal(); if (f) f(); };
    this._luBack = () => go();   // (0.60: B / Échap = later)
    const el = h('div', { class: 'window modal door' }, h('div', { class: 'title' }, T('door')), h('div', { class: 'content' },
      h('p', { class: 'sub' }, T(onBonus ? 'door_text2' : 'door_text')),
      onBonus ? h('p', { class: 'door-bonus' }, T('door_bonus_desc')) : null,
      h('div', { class: 'start-row' }, btn(T('later'), () => go()),
        onBonus ? btn(T('door_bonus'), () => go(onBonus)) : null,
        btn(T(onBonus ? 'door_fight' : 'enter'), () => go(onEnter), 'orange big'))));
    this.openModal(el);
    const j = Audio2.jingle('cls_roublard'); if (j) { j.loop = true; this._doorJ = true; }
  },
  chestMenu(R, got, kamas) {
    this.levelUpOpen = true;
    const C = Game.C;
    const items = got.map(o => {
      if (o.kind === 'spell') { const sp = C.spells[o.id]; const lv = R.spells.find(s => s.def.id === o.id).level; return h('div', { class: 'chest-item' }, iconImg('sp_' + sp.icon, 40), h('div', {}, L(sp.name), h('br'), h('small', {}, T('level') + ' ' + lv))); }
      if (o.kind === 'weapon') { const w = weaponById(C, o.id); return h('div', { class: 'chest-item' }, iconImg(w.icon, 40), h('div', {}, L(w.name), h('br'), h('small', {}, T('level') + ' ' + R.weapon.level))); }
      if (o.kind === 'passive') { const p = C.passives.find(p => p.id === o.id); return h('div', { class: 'chest-item' }, iconImg(p.icon, 36), h('div', {}, L(p.name), h('br'), h('small', {}, T('level') + ' ' + R.passives[o.id]))); }
      if (o.kind === 'sfusion') { const sp = C.spells[o.id]; return h('div', { class: 'chest-item' }, iconImg('sp_' + sp.icon, 40), h('div', {}, '✦ ' + L(sp.name), h('br'), h('small', {}, T('sfusion_union')))); }   // (0.61: a fusion the chest made was shown as kamas)
      if (o.kind === 'wevo') { const E = evoDef(o.id); return h('div', { class: 'chest-item' }, iconImg(E.w.icon, 40), h('div', {}, L(E.e.name), h('br'), h('small', {}, T('evo_rank', { n: R.weapon.evo[o.id] || 0 })))); }
      return h('div', { class: 'chest-item' }, iconImg('KamaSymbol', 36), h('div', {}, T('take_kamas')));
    });
    const el = h('div', { class: 'window modal chest' }, h('div', { class: 'title' }, T('chest')), h('div', { class: 'content' },
      h('div', { class: 'chest-items' }, ...items),
      h('div', { class: 'chest-kamas' }, iconImg('KamaSymbol', 22), ' +' + fmtNum(kamas)),
      h('div', { class: 'start-row' }, btn(T('continue'), () => this.closeModal(), 'orange big'))));
    this.openModal(el);
  },
  // the Enutrof merchant (random event): three offers paid with the run's kamas
  // 0.23 Jeton de la Foire du Trool: a fair wheel (12 slices in the class colours) that stops on a spell of another class
  trollWheelCanvas(segs, size) {
    const c = document.createElement('canvas'), k = Math.min(3, window.devicePixelRatio || 1) * (Game._uiz || 1); c.width = c.height = Math.round(size * k);
    c.style.width = c.style.height = size + 'px'; const g = c.getContext('2d'), R = c.width / 2, n = segs.length;
    g.translate(R, R);
    for (let i = 0; i < n; i++) {
      const a0 = i * TAU / n - Math.PI / 2 - Math.PI / n, a1 = a0 + TAU / n;
      g.beginPath(); g.moveTo(0, 0); g.arc(0, 0, R * 0.96, a0, a1); g.closePath();
      g.fillStyle = segs[i].cls.color || '#888'; g.fill(); g.fillStyle = i % 2 ? 'rgba(0,0,0,0.18)' : 'rgba(255,255,255,0.12)'; g.fill();
      g.strokeStyle = '#3a2410'; g.lineWidth = R * 0.02; g.stroke();
      g.save(); g.rotate(a0 + Math.PI / n + Math.PI / 2); const s = R * 0.2;   // (0.34: smaller, inside its slice)
      g.drawImage(Game.icons.canvas(segs[i].ic || 'sp_' + Game.C.spells[segs[i].id].icon, Math.round(s * 1.5)), -s / 2, -R * 0.82, s, s); g.restore();
    }
    g.beginPath(); g.arc(0, 0, R * 0.96, 0, TAU); g.lineWidth = R * 0.05; g.strokeStyle = '#8a5a1e'; g.stroke();
    for (let i = 0; i < n; i++) { const a = i * TAU / n - Math.PI / 2 - Math.PI / n; g.beginPath(); g.arc(Math.cos(a) * R * 0.96, Math.sin(a) * R * 0.96, R * 0.028, 0, TAU); g.fillStyle = '#ffe9a0'; g.fill(); }
    g.beginPath(); g.arc(0, 0, R * 0.15, 0, TAU); g.fillStyle = '#5a3a14'; g.fill(); g.lineWidth = R * 0.025; g.strokeStyle = '#ffd24a'; g.stroke();
    return c;
  },
  // (0.98.3: w.pop: the Gladiatrool's wheel: its own texts, every possible prize on a slice)
  troolWheel(R, w) {
    const C = Game.C, N = w.pop ? w.pool.length : 12;
    const others = shuffle(w.pool.filter(o => o.id !== w.won.id)).slice(0, N - 1);
    while (others.length < N - 1) others.push(pick(w.pool));
    const P = randi(0, N - 1), segs = others.slice(); segs.splice(P, 0, w.won);
    const size = 340, wheel = this.trollWheelCanvas(segs, size);
    const box = h('div', { class: 'troll-wheel' }, wheel, h('div', { class: 'troll-ptr' }), h('div', { class: 'troll-hub' }, iconImg('it_15_737', 44)));
    const status = h('div', { class: 't-status' }, w.pop ? w.pop.spin : T('wheel_spin'));
    const sp = C.spells[w.won.id], prizeEl = h('div', { class: 't-prize' }, iconImg(w.pop ? w.pop.icon : 'sp_' + sp.icon, 40), ' ', w.pop ? w.pop.won : T('wheel_won', { n: L(sp.name), c: L(w.won.cls.name) }));
    const desc = h('p', { class: 'sub fx-desc', style: { opacity: 0 } }, w.pop ? w.pop.desc : L(sp.desc));   // (0.98: a spell's description in the effect colours)
    let raf = 0, given = false;
    const done = () => { if (given) return; given = true; cancelAnimationFrame(raf); w.give(); this.closeModal(); };
    const okBtn = btn(T('wheel_ok'), done, 'orange big'); okBtn.style.visibility = 'hidden';
    const el = h('div', { class: 'window modal tailor trool' }, h('div', { class: 'title' }, w.pop ? w.pop.title : T('wheel_title')), h('div', { class: 'content' },
      box, h('div', { class: 'troll-side' }, status, prizeEl, desc, h('div', { class: 'start-row' }, okBtn))));
    this.openModal(el); this.levelUpOpen = true;
    // several turns, slowing down, the pointer on top: slice P ends under it
    const turns = 5 + randi(0, 2), end = -(P * TAU / N) + rand(-0.32, 0.32) * TAU / N - turns * TAU;
    const T1 = 4.6, start = performance.now(); let last = -1;
    const ease = k => 1 - Math.pow(1 - k, 3.4);
    const step = () => {
      if (!el.isConnected) { if (!given) { given = true; w.give(); } return; }
      const k = Math.min(1, (performance.now() - start) / 1000 / T1), a = end * ease(k);
      wheel.style.transform = `rotate(${a}rad)`;
      const sl = Math.floor((-a / TAU * N) + 0.5); if (sl !== last) { last = sl; Audio2.play('click3', 0.4, 1.2); }
      if (k >= 1) {
        el.classList.add('jackpot'); status.textContent = ''; prizeEl.classList.add('show'); desc.style.opacity = 1; okBtn.style.visibility = 'visible';
        Audio2.sfx('EVENT', 0.8); Audio2.play('stars', 0.8); Nav.el = null; return;
      }
      raf = requestAnimationFrame(step);
    };
    Audio2.play('pages', 0.6); raf = requestAnimationFrame(step);
  },
  merchantMenu(R, M) {
    if (this.modalOpen()) { M.open = false; return; }
    this.levelUpOpen = true;
    const offer = (k, icon) => {
      const price = R.merchantPrice(k), sold = M.sold[k];
      const b = btn([iconImg(icon, 30), h('span', {}, T('m_' + k)), h('b', {}, ' ' + fmtNum(price) + ' K')], () => {
        if (M.sold[k]) return;
        if (!R.merchantBuy(k)) { msg.textContent = T('m_broke'); Audio2.blip('wrong'); return; }
        M.sold[k] = 1; b.classList.add('disabled'); wal.textContent = fmtNum(R.kamas) + ' K';
      }, 'merchant-offer' + (sold || R.kamas < price ? ' disabled' : ''));
      return b;
    };
    const msg = h('p', { class: 'sub' }, T('merchant_hello')), wal = h('b', {}, fmtNum(R.merchantWallet ? R.merchantWallet() : R.kamas) + ' K');
    const el = h('div', { class: 'window modal merchant' }, h('div', { class: 'title' }, T('merchant')), h('div', { class: 'content' },
      msg, h('div', { class: 'merchant-wallet' }, iconImg('KamaSymbol', 18), ' ', wal),
      h('div', { class: 'merchant-offers skins' }, ...(M.offers || []).map((o, i) => {
        const [t, g] = o.it.id.split('_'), owned = M.sold[i];
        const b = btn([h('span', { class: 'm-promo' }, '-' + o.off + ' %'), iconImg(`it_${t}_${g}`, 44), h('span', { class: 'm-name' }, L(o.it.name)), h('small', {}, T(o.slot === 'hat' ? 'hats' : o.slot === 'cape' ? 'capes' : 'pets')),
          h('span', { class: 'm-price' }, h('s', {}, fmtNum(o.it.price)), ' ', h('b', {}, fmtNum(o.price) + ' K'))], () => {
          if (M.sold[i]) return;
          if (!R.merchantBuySkin(o)) { msg.textContent = T('m_broke'); Audio2.blip('wrong'); return; }
          M.sold[i] = 1; b.classList.add('disabled', 'sold'); wal.textContent = fmtNum(R.merchantWallet()) + ' K'; msg.textContent = T('m_kept');
        }, 'merchant-offer skin' + (owned || R.merchantWallet() < o.price ? ' disabled' : ''));
        return b;
      })),
      h('div', { class: 'start-row' }, btn(T('m_leave'), () => this.closeModal(), 'orange'))));
    this.openModal(el);
  },
  // the local leaderboard of the Endless mode (one table per zone)
  leaderboard(mapId) {
    const C = Game.C, S = Store.data; let cur = mapId || 'astrub';
    const body = h('div', { class: 'lb-body' });
    const draw = () => {
      body.innerHTML = '';
      const all = ((S.board || {})[cur] || []);   // (0.54: the Normal and the Difficile runs in two tables)
      for (const hard of [false, true]) {
        const L_ = all.filter(e => !!e.hard === hard);
        body.append(h('div', { class: 'lb-head' + (hard ? ' hard' : '') }, hard ? '💀 ' + T('mode_hard') : T('mode_normal')));
        if (!L_.length) { body.append(h('p', { class: 'sub' }, T('lb_empty'))); continue; }
        body.append(h('table', { class: 'stats grid lb' }, h('tr', {}, h('th', {}, '#'), h('th', {}, T('st_class')), h('th', {}, T('time')), h('th', {}, T('kills')), h('th', {}, T('level'))),
          ...L_.map((e, i) => { const c = C.classes.find(c => c.id === e.cls); return h('tr', {}, h('td', {}, i < 3 ? ['🥇', '🥈', '🥉'][i] : String(i + 1)), h('td', {}, c ? L(c.name) : e.cls), h('td', {}, fmtTime(e.t)), h('td', {}, fmtNum(e.kills)), h('td', {}, String(e.lvl))); })));
      }
    };
    const tabs = h('div', { class: 'tabs' }, ...C.maps.filter(m => S.unlocked.includes(m.id)).map(m => btn(L(m.name), (e) => { cur = m.id; tabs.querySelectorAll('.btn').forEach(b => b.classList.remove('active')); e.currentTarget.classList.add('active'); draw(); }, m.id === cur ? 'active' : '')));
    const el = h('div', { class: 'window modal leaderboard' }, h('div', { class: 'title' }, '🏆 ' + T('leaderboard') + ' — ∞'), h('div', { class: 'content' }, tabs, body,
      h('div', { class: 'start-row' }, btn(T('back'), () => this.closeModal(), 'orange'))));
    this.openModal(el); draw();
  },
  // 0.60: the title pops (rays turning behind a victory), a grade stamp slams in
  // (S to D, with its Dofus joke), the numbers count up, the damage of every spell / weapon grows as bars (the best
  // first), then what the run brought: unlocked zones, achievements, relics, Dofus, records. Replay / main menu.
  runOverMenu(R, victory, unlocked) {
    this.levelUpOpen = true;
    const C = Game.C, S = Store.data, ps = R.ps || {}, earned = R.kamas + (R.bonusKamas || 0);
    const ul = Array.isArray(unlocked) ? unlocked : unlocked ? [unlocked] : [];
    const allBoss = (R.map.bosses || []).every(([, id]) => (R.bossesDown || new Set()).has ? R.bossesDown.has(id) : true);
    const grade = victory ? (R.hard && allBoss ? 'A' : 'B') : R.time >= 480 ? 'C' : R.time >= 240 ? 'D' : R.time >= 120 ? 'E' : 'F';   // (0.73: A to F, the)
    const ach = (C.achievements || []).filter(a => S.ach[a.id] && S.ach[a.id] >= (R._startedAt || Date.now()));
    // the damage by spell / weapon (fused spells and Soifs de Sang in their colours)
    const rows = Object.entries(R.dmgBy || {}).map(([k, v]) => { const d = C.spells[k] || weaponById(C, k); return d && v > 0 ? { d, v, k } : null; }).filter(Boolean).sort((a, b) => b.v - a.v).slice(0, 8);
    const tot = rows.reduce((a, r) => a + r.v, 0) || 1, top = rows.length ? rows[0].v : 1;
    const icOf = d => d.weapon ? d.icon : 'sp_' + d.icon;
    const bars = h('div', { class: 'ov-bars' }, ...rows.map((r, i) => h('div', { class: 'ov-bar' + (r.d.sfusion ? ' sf' : r.d.blood ? ' blood' : r.d.weapon ? ' wpn' : ''), style: { '--w': (r.v / top * 100).toFixed(1) + '%', '--d': (0.9 + i * 0.12) + 's' } },
      iconImg(icOf(r.d), 26), h('span', { class: 'ov-bn' }, L(r.d.name)), h('i', null), h('b', null, fmtNum(Math.round(r.v)) + ' · ' + Math.round(r.v / tot * 100) + ' %'))));
    const cnt = (v, f = fmtNum) => { const e = h('b', { class: 'ov-n', 'data-v': v }, f(0)); e._f = f; return e; };
    const stat = (ic, k, v, f) => h('div', { class: 'ov-stat' }, ic ? iconImg(ic, 22) : null, h('span', null, k), cnt(v, f));
    const stats = h('div', { class: 'ov-stats' },
      stat(null, T('time'), Math.floor(R.time), fmtTime), stat(null, T('level'), R.level), stat(null, T('kills'), R.kills),
      stat('KamaSymbol', T('earned'), earned), stat(null, T('ov_dealt'), Math.round(ps.dmgDealt || 0)), stat(null, T('ov_best_hit'), Math.round(ps.bestHit || 0)),
      stat(null, T('ov_dps'), Math.round(R.bestDps || 0)), stat(null, T('ov_taken'), Math.round(ps.dmgTaken || 0)),
      stat(null, T('ov_bosses'), ps.bosses || 0), stat(null, T('ov_elites'), ps.elites || 0), stat(null, T('ov_chests'), ps.chests || 0), stat(null, T('ov_combo'), ps.bestCombo || 0));
    const loot = h('div', { class: 'ov-loot' },
      ...ul.map(u => h('p', { class: 'unlock' + (u.secret ? ' secret' : '') }, '🔓 ' + (u.secret ? T('secret_unlocked', { z: L(u.name) }) : T('new_zone', { z: L(u.name) })))),
      R.infinite && R.boardRank ? h('p', { class: 'unlock' }, '🏆 ' + T('lb_rank', { n: R.boardRank }) + ' — ' + fmtTime(R.time)) : null,
      (R.dofus.length || (R.relics || []).length) ? h('div', { class: 'ov-items' }, ...R.dofus.map(d => tipIcon('dofus_hd_' + d.icon, L(d.name), 34)), ...(R.relics || []).map(r => tipIcon(r.icon, L(r.name), 30))) : null,
      ach.length ? h('div', { class: 'ov-ach' }, h('small', null, T('ov_ach')), ...ach.map(a => h('span', { class: 'ov-a' }, iconImg(a.icon, 24), L(a.name)))) : null);
    const stamp = h('div', { class: 'ov-grade g' + grade }, rankMedal(grade), h('small', null, T('ov_grade_' + grade)));
    const head = victory ? h('div', { class: 'ov-head win' }, h('div', { class: 'ov-title' }, T('victory_big')))   // (0.98: written in Verdance, verdant; was the banner picture)
      : h('div', { class: 'ov-head lose' }, iconImg('phoenix_statue', 130), h('div', { class: 'ov-title' }, T(R.cancelled ? 'run_cancelled' : 'dead_title')));   // (0.79: given up before 20 s)
    // 0.61: no 'Rejouer' after a victory; the buttons stay at the bottom of the window, its content scrolls
    const replay = victory ? null : btn('↻ ' + T('replay'), () => { this.closeModal(); Game.startRun(Object.assign({}, R.opts)); }, 'orange big');
    // 0.98: behind a victory's whole window, rays turning round the title and leaves drifting (under the content: .ov-sky)
    const sky = victory ? h('div', { class: 'ov-sky' }, h('div', { class: 'ov-rays' }), ...Array.from({ length: 16 }, (_, i) => h('i', { class: 'ov-leaf', style: { '--i': i, left: (4 + (i * 37) % 92) + '%', top: (6 + (i * 53) % 86) + '%' } }))) : null;
    const el = h('div', { class: 'window modal over ' + (victory ? 'win' : 'lose') }, sky, h('div', { class: 'title' }, L(R.cls.name) + ' — ' + L(R.map.name)),
      h('div', { class: 'content' }, victory ? h('div', { class: 'ov-confetti' }, ...Array.from({ length: 36 }, (_, i) => h('i', { style: { '--x': ((i * 37) % 100) + '%', '--c': FW_COLS[i % FW_COLS.length], '--d': ((i % 9) * 0.23) + 's', '--r': (i * 47 % 360) + 'deg' } }))) : null,
        head, h('p', { class: 'sub' }, victory ? (R.doom ? T('victory_doom') : T('victory_sub')) : T(R.cancelled ? 'run_cancelled_sub' : 'dead_sub')),
        h('div', { class: 'ov-cols' }, h('div', { class: 'ov-left' }, R.cancelled ? null : stamp, R.newBest && !R.infinite ? h('p', { class: 'unlock ov-record' }, '🏅 ' + T('new_record') + ' ' + fmtTime(R.time)) : null, stats), h('div', { class: 'ov-right' }, rows.length ? h('h3', null, T('ov_dmg')) : null, bars, loot))),
      h('div', { class: 'start-row ov-buttons' }, replay, btn(T('main_menu'), () => { this.closeModal(); Game.toMenu(); }, victory ? 'orange big' : R.abandoned ? 'big sel' : 'big')));
    this.openModal(el);
    if (victory) { Audio2.sfx('EVENT', 0.9); Audio2.fanfare && Audio2.fanfare(0.8); }
    // the numbers count up (1.3 s, a tick now and then, coins for the kamas), then the stamp
    const nums = [...el.querySelectorAll('.ov-n')], t0 = performance.now(); let lastTick = 0;
    const step = () => {
      if (!el.isConnected) return;
      const k = Math.min(1, (performance.now() - t0) / 1300), e = 1 - Math.pow(1 - k, 3);
      for (const n of nums) n.textContent = n._f(Math.round(+n.dataset.v * e));
      if (k < 1) { if (performance.now() - lastTick > 90) { lastTick = performance.now(); Audio2.blip('click'); } requestAnimationFrame(step); }
      else { Audio2.blip('coin'); setTimeout(() => { if (!el.isConnected || R.cancelled) return; stamp.classList.add('on'); Audio2.play('impact_lourd', 0.7, grade === 'A' ? 0.85 : 1); if (grade === 'A' || grade === 'B') Audio2.play('stars', 0.7); }, 250); }
    };
    requestAnimationFrame(step);
  },
  botPick() {
    if (!this.modal) return;
    if (this.modal.querySelector('.dice-tray, .dice-stage')) return;
    const cards = this.modal.querySelectorAll('.up-card');
    if (cards.length) { cards[0].click(); return; }
    const b = this.modal.querySelector('.btn.orange'); if (b && !Game.run.over) b.click();
  },
  // ------------------------------------------------ menu background / previews
  drawMenuBg(ctx, dt) {
    ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.fillStyle = '#120d08'; ctx.fillRect(0, 0, Game.cw, Game.ch);
    for (const p of this.previews) p(dt);
  },
  // ------------------------------------------------ secrets
  secretKey(e) {
    if (this.levelUpOpen && this._keyPick) this._keyPick(e);
    const seq = ['ArrowUp', 'ArrowUp', 'ArrowDown', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'ArrowLeft', 'ArrowRight', 'KeyB', 'KeyA'];
    this._seq = (this._seq || []).concat(e.code).slice(-10);
    if (this._seq.join() === seq.join()) {
      this.tofuMode = !this.tofuMode; Store.data.easter.konami = 1; Store.save();
      Audio2.sfx('Poolay_Die', 1); Audio2.blip('level');
      toast(this.tofuMode ? T('tofumode') : T('tofumode_off'));
    }
    this._typed = ((this._typed || '') + (e.key || '')).slice(-8).toLowerCase();
    if (this._typed.endsWith('tot') && Game.state === 'menu') toast(T('secret_tot', { t: fmtTime((Game.C.run && Game.C.run.doorT) || 150) }));   // (0.61: in every language, at the door's real time)
    if (this._typed.endsWith('ankama') && Game.state === 'menu') toast(T('secret_ankama'));
  },
};
// toasts stack one under the other (several achievements can unlock at once)
// 0.59: a text given to the player as a file (the profile's save)
function downloadText(name, text, type = 'application/json') {
  const u = URL.createObjectURL(new Blob([text], { type })), a = h('a', { href: u, download: name });
  document.body.append(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(u), 5000);
}
function toast(msg) {
  let box = document.getElementById('toasts'); if (!box) { box = h('div', { id: 'toasts' }); document.body.append(box); }
  const t = h('div', { class: 'toast' }, msg); box.append(t);
  setTimeout(() => t.classList.add('show'), 10); setTimeout(() => { t.classList.remove('show'); setTimeout(() => t.remove(), 500); }, 3800 + box.children.length * 300);
}
function behText(d) {
  if (d.boss) return T('beh_boss');
  const J = Game.C.jorbak || {}, k = 'beh_' + (d.beh || 'chase');   // (0.95: Jorbak's line takes his numbers)
  const v = T(k, { d0: Math.round((J.keep || [0, 0])[0] / 45), d1: Math.round((J.keep || [0, 0])[1] / 45), s: L(J.spell || {}), b: Math.round((J.buff || 0) * 100), m: Math.round((J.tmap || 0) * 100) });
  return v === k ? T('beh_chase') : v;
}
// 0.48: the vampiric weapons ('Soif de sang', unique weapons with life steal): a blood drop, their % of life steal
// 0.55: the music style buttons (Classique / Phonk / Lofi), in the options and the main menu's music menu
function styleRow() {
  const cur = Audio2.style(), row = h('span', { class: 'qrow mstyle' });
  for (const [k, lab] of [['phonk', 'Phonk'], ['classic', T('mus_classic')], ['lofi', 'Lofi']])   // (0.60: Classique in the middle)
    row.append((b => (b.dataset.st = k, b))(btn(lab, (e) => { e && e.stopPropagation && e.stopPropagation(); Audio2.setStyle(k); for (const x of document.querySelectorAll('.mstyle .btn')) x.classList.toggle('on', x.dataset.st === k); }, 'sbtn' + (cur === k ? ' on' : ''))));
  return h('div', { class: 'opt mstyle-opt' }, h('span', {}, T('mus_style')), row);
}
function potionIcon() { return (Game.C.massPotion || {}).icon || 'it_33_7'; }   // 0.53: the max-level heal (bread before)
function pctLeech(v) { return (Math.round(v * 100000) / 1000).toLocaleString(LANG, { minimumFractionDigits: 3 }) + ' %'; }
function evoDef(id) { const C = Game.C, cur = Game.run && Game.run.weapon && Game.run.weapon.def.id;   // the current weapon first (a unique weapon has its type's finales)
  if (cur && C.weaponEvo[cur]) { const e = C.weaponEvo[cur].find(x => x.id === id); if (e) return { e, w: weaponById(C, cur) }; }
  for (const wid in C.weaponEvo || {}) { const e = C.weaponEvo[wid].find(x => x.id === id); if (e) return { e, w: C.weapons.find(w => w.id === wid) }; } return null; }
// 0.53: the real numbers of a spell / weapon at a level in this run (the cards show what it really does now, the
// shop, the characteristics, the mastery and the run's bonuses included): damage, heal and cooldown as the spell code
// computes them, its area / count / duration with the run's stats where its type reads them (SYN_TYPES, ui_armory.js)
function realParams(R, def, lv) {
  if (!R || !R.stats) return spellParams(def, lv);
  const s = new SpellInst(R, def); s.level = lv;
  const cur = (R.weapon && R.weapon.def === def) ? R.weapon : (R.spells || []).find(x => x.def === def);
  if (cur) { s.evo = Object.assign({}, cur.evo); s.fusion = cur.fusion; s.finale = cur.finale; }
  s.recalc();
  const p = Object.assign({}, s.p), st = R.stats, t = def.t, SY = typeof SYN_TYPES !== 'undefined' ? SYN_TYPES : null;
  if (typeof p.dmg === 'number') p.dmg = s.dmg(p.dmg);
  if (typeof p.heal === 'number' && t === 'heal') p.heal = p.heal * (R.cls.id === 'eniripsa' ? 1.3 : 1) * (1 + st.healBonus) * s.shopK;
  if (typeof p.healShop === 'number') p.heal = lerp(p.heal, p.healShop, s.shopT()) * (1 + st.healBonus);   // (0.96: the shop's own ends, as the spell casts: the Cawotte)
  if (typeof p.durShop === 'number') p.duration = lerp(p.duration, p.durShop, s.shopT());   // (the Cawotte, the Immunité)
  if (typeof p.cd === 'number' && !p.perm) p.cd = s.cooldown();
  if (SY && SY.area.has(t)) for (const k of ['radius', 'width', 'aoe', 'dist']) if (typeof p[k] === 'number') p[k] *= st.area;
  if (SY && SY.amount.has(t) && typeof p.count === 'number') p.count += st.amount;
  if (SY && SY.duration.has(t)) for (const k of ['duration', 'buffDur']) if (typeof p[k] === 'number') p[k] *= st.duration;
  return p;
}
function fmtParam(k, v) {
  if (typeof v !== 'number') return v;
  const n = x => x.toLocaleString(LANG, { maximumFractionDigits: 1 });
  if (k === 'slow' || k === 'crit' || k === 'execute' || k === 'mark' || k === 'power' || k === 'haste' || k === 'transmute' || k === 'gold') return n(v * 100) + '\u00a0%';   // (0.59: no-break spaces: a unit alone on the next line of a card)
  if (k === 'leech') return pctLeech(v);
  if ((k === 'duration' || k === 'buffDur') && v >= 1e6) return T('permanent');   // (0.59: a permanent spell, p.perm: the Faux's orbit lasts 1e9 s)
  if (k === 'cd' || k === 'duration' || k === 'buffDur' || k === 'slowDur' || k === 'stun' || k === 'fuse') return n(v) + '\u00a0s';
  return v >= 20 ? String(Math.round(v)) : n(v);
}
// 0.98: the effect colour code of Dofus 2's tooltips: a spell's description orange (fx-desc), what it does green (fx-eff:
// damage, heals, bonuses), its properties in the text's colour with the value bold (fx-prop: cooldown, reach, area,
// duration, count), a drawback red (fx-neg), a special effect blue (fx-spec), a condition red (fx-cond). The lines are
// built as parts { k, lab, val, kind }: fxNodes draws them, fxText keeps the plain text (titles, tests)
const FX_EFF = new Set(['dmg', 'heal', 'shield', 'armorBuff', 'leech', 'poison', 'burn', 'slow', 'stun', 'mark', 'execute', 'crit', 'power', 'haste', 'gold', 'transmute', 'bonus', 'retal']);
const FX_NEG = new Set(['cost']);
function fxPart(k, lab, val, kind) { return { k, lab, val, kind: kind || (FX_NEG.has(k) ? 'neg' : FX_EFF.has(k) ? 'eff' : 'prop') }; }
function fxText(parts) { return parts.map(p => `${p.lab} ${p.val}`).join(' · '); }
function fxNodes(parts) { const out = []; parts.forEach((p, i) => { if (i) out.push(h('span', { class: 'fx-sep' }, ' · ')); out.push(h('span', { class: 'fx-' + p.kind }, p.lab + ' ', h('b', {}, p.val))); }); return out; }
function fxDesc(t, kind = 'desc') { return t ? h('span', { class: 'fx-' + kind }, t) : null; }
// the main numbers of a spell / weapon now (a new one)
function realSummaryParts(R, def) {
  const p = realParams(R, def, 1), out = [];
  if (def.t === 'wheel') return out;   // (0.60: the Jeton de la Foire du Trool is used at once: no recharge to show)
  for (const k of ['dmg', 'heal', 'count', 'radius', 'aoe', 'range', 'width', 'duration', 'cd']) if (p[k] !== undefined && typeof p[k] === 'number' && p[k] > 0 && !(k === 'cd' && (p.perm || p.cd >= 900))) { const lab = T('p_' + k); if (lab !== 'p_' + k) out.push(fxPart(k, lab, fmtParam(k, p[k]))); }
  return out;
}
function realSummary(R, def) { return fxText(realSummaryParts(R, def)); }
// what one more level changes, in real numbers (damage always shown)
function realDiffParts(R, def, lv) {
  const a = realParams(R, def, lv - 1), b = realParams(R, def, lv), parts = [];
  for (const k in b) {
    if (typeof b[k] !== 'number' || (Math.abs((a[k] || 0) - b[k]) < 1e-6 && k !== 'dmg')) continue;
    const lab = T('p_' + k); if (lab === 'p_' + k) continue;
    parts.push(fxPart(k, lab, Math.abs((a[k] || 0) - b[k]) < 1e-6 ? fmtParam(k, b[k]) : `${fmtParam(k, a[k] || 0)} → ${fmtParam(k, b[k])}`));   // (0.60: no '5,5 → 5,5')
  }
  return parts;
}
function realDiff(R, def, lv) { return fxText(realDiffParts(R, def, lv)) || L(def.desc); }
// a level-up card's lines of a spell / weapon at a level above 1: the changes, or its description when nothing shows
function diffNodes(R, def, lv, pre = []) { const d = pre.concat(realDiffParts(R, def, lv)); return d.length ? fxNodes(d) : fxDesc(L(def.desc)); }
// 0.96: a spell's real numbers out of a run (the shop's cards, the Armurerie's fusions) at a shop level, as SpellInst gives
// them at the start of a run (dmg, cooldown, the heal), with the ends a spell may set for the whole shop (cdShop, durShop,
// healShop: the Cawotte, the Immunité, Élagage de cou), without the run's own bonuses
function menuSpellParams(sp, cls, shopLv, lv = 1) {
  const C = Game.C, R = C.run || {}, p = Object.assign({}, spellParams(sp, lv)), k = 1 + (C.spellPer || 0.1) * shopLv, s = Math.min(1, shopLv / 5), might = cls && cls.base ? (cls.base.might || 1) + ((cls.passiveStats || {}).might || 0) : 1;   // (0.96: + a class bonus kept apart from the base, the Iop's +12 %)
  if (p.dmg) p.dmg *= might * (R.spellDmgMul || 1) * (cls && cls.id === 'feca' && !sp.weapon ? R.fecaDmg || 1 : 1) * k;
  if (p.heal) p.heal = p.healShop ? lerp(p.heal, p.healShop, s) : p.heal * k;
  if (p.cd) p.cd = (p.cdShop ? lerp(p.cd, p.cdShop, s) : p.cd / (1 + (k - 1) * 0.5)) * (R.cdMul || 1) * cdLateK(R, p.cd, 1);   // (0.98: as SpellInst.cooldown at a run's first level)
  if (p.duration) p.duration = p.durShop ? lerp(p.duration, p.durShop, s) : p.duration * k;
  return p;
}
// 0.60 (shop): what the spell power bought really changes, on the spell at its first level: damage / heal, durations,
// cooldown (the shop power shortens it by half its value: SpellInst.cooldown; 0.96: or its cdShop / durShop / healShop)
function shopSpellParts(sp, cls, lv, next) {
  const n = x => (Math.round(x * 10) / 10).toLocaleString(LANG), parts = [], a = menuSpellParams(sp, cls, lv), b = next !== null ? menuSpellParams(sp, cls, next) : null;
  const pair = (k, lab, f) => parts.push(fxPart(k, lab, `${f(a[k])}${b ? ' → ' + f(b[k]) : ''}`));
  if (a.dmg) pair('dmg', T('p_dmg'), n);
  if (a.heal) pair('heal', T('p_heal'), n);
  if (a.cd && !a.perm) pair('cd', T('p_cd'), x => n(x) + ' s');
  if (a.duration && !a.perm && !a.dmg) pair('duration', T('p_duration'), x => n(x) + ' s');
  return parts;
}
function shopSpellReal(sp, cls, lv, next) { return fxText(shopSpellParts(sp, cls, lv, next)); }
// 0.96: a fusion's damage and cooldown in the Armurerie, the game's own numbers (menuSpellParams at its spells' best
// shop level, as SpellInst.shopK; a fusion is always at its top): per blow, x its count, per tick for an area, the reach of
// its explosion, and a line when its effects add damage of their own (riders, the Cawottes); 0.97: its life steal (a
// share of the damage dealt, a pulse's cap a wave) and its heal over time (a second in its cloud, while it lasts)
const SF_EXTRA = ['rBurn', 'rPoison', 'rBleed', 'rBlast', 'rWeb', 'rCloud', 'rRock', 'rCraq', 'rChaos', 'sat'];
function sfStats(f, cls) {
  const C = Game.C, SL = (Store.data && Store.data.spellLv) || {}, sp = C.spells[f.id], p = menuSpellParams(sp, cls, Math.max(...f.src.map(k => SL[k] || 0)));
  const n = x => (Math.round(x * 10) / 10).toLocaleString(LANG), parts = [];
  if (p.dmg) parts.push(fxPart('dmg', T('p_dmg'), `${n(p.dmg)}${p.count > 1 ? ' × ' + p.count : ''}${p.tick ? ' / ' + n(p.tick) + '\u00a0s' : ''}${p.aoe ? ' (' + T('p_aoe') + ' ' + Math.round(p.aoe) + ')' : ''}`));
  if (p.perm) parts.push(fxPart('duration', T('p_duration'), T('permanent'))); else if (p.cd) parts.push(fxPart('cd', T('p_cd'), `${n(p.cd)}\u00a0s`));
  const pc = x => n(x * 100) + ' %', heal = [];
  if (p.leech) heal.push(T('sf_leech', { n: pc(p.leech) }) + (sp.t === 'pulse' ? ' (' + T('sf_leech_cap', { n: pc(PULSE_LEECH_CAP) }) + ')' : ''));
  if (p.heal && sp.t === 'pwcawotte') heal.push(T('sf_hot', { n: n(p.heal), d: n(p.duration) }));
  return h('div', { class: 'sf-stats' }, ...fxNodes(parts), heal.length ? h('span', { class: 'sf-heal fx-eff' }, heal.join(' · ')) : null, SF_EXTRA.some(k => p[k]) ? h('small', null, T('sf_extra')) : null);
}
// 0.60 (shop): one level of a characteristic in a run, at this shop level → the next one
function passiveShopParts(p, lv, next) {
  const d = PASSIVE_FMT(p); if (!d) return [];
  const v = l => passivePer(Game.C, p, l);
  return [fxPart('bonus', d.lab, `${d.f(v(lv))}${next !== null ? ' → ' + d.f(v(next)) : ''}`, 'eff')];   // (a characteristic's bonus: an effect)
}
function passiveShopReal(p, lv, next) { return fxText(passiveShopParts(p, lv, next)); }
// a translated line around coloured parts ('1 level in a run: {t}' in every language, {t} anywhere in it)
function fxAround(key, parts) { const [a, b] = T(key, { t: '\u0001' }).split('\u0001'); return [a, ...fxNodes(parts), b || '']; }
function PASSIVE_FMT(p) {
  const pc = x => (x >= 0 ? '+' : '') + (Math.round(x * 1000) / 10).toLocaleString(LANG) + ' %', nb = x => '+' + (Math.round(x * 100) / 100).toLocaleString(LANG);
  const LAB = { maxhp: ['ps_maxhp', pc], growth: ['ps_growth', pc], might: ['p_dmg', pc], area: ['p_radius', pc], luck: [null, pc], crit: ['p_crit', pc], cooldown: ['p_cd', pc],
    speed: ['p_speed', pc], projspeed: ['ps_projspeed', pc], amount: ['ps_amount', nb], regen: ['ps_regen', nb], magnet: ['ps_magnet', pc], armor: ['p_armorBuff', nb],
    duration: ['p_duration', pc], leech: ['p_leech', x => pctLeech(x)], reflect: ['ps_reflect', x => '≤ ' + Math.round(30 * x)], evade: [null, pc] };
  const d = LAB[p.stat]; return d ? { lab: d[0] ? T(d[0]) : L(p.name), f: d[1] } : null;
}
// 0.53: a characteristic's real total before → after this level (the shop's levels included)
function passiveReal(p, lv) { const d = passiveParts(p, lv); return d ? fxText(d) : L(p.desc); }
function passiveParts(p, lv) {
  const C = Game.C, per = passivePer(C, p, (Store.data.passLv || {})[p.id]);   // (0.94: the shop's levels, util.js)
  const v = l => l > 0 ? per * l * (p.stat === 'leech' ? 1 + 0.1 * (l - 1) : 1) : 0;
  const pc = x => (x >= 0 ? '+' : '') + (Math.round(x * 1000) / 10).toLocaleString(LANG) + ' %', nb = x => '+' + (Math.round(x * 100) / 100).toLocaleString(LANG);
  const LAB = { maxhp: ['ps_maxhp', pc], growth: ['ps_growth', pc], might: ['p_dmg', pc], area: ['p_radius', pc], luck: [null, pc], crit: ['p_crit', pc], cooldown: ['p_cd', pc],
    speed: ['p_speed', pc], projspeed: ['ps_projspeed', pc], amount: ['ps_amount', nb], regen: ['ps_regen', nb], magnet: ['ps_magnet', pc], armor: ['p_armorBuff', nb],
    duration: ['p_duration', pc], leech: ['p_leech', x => pctLeech(x)], reflect: ['ps_reflect', x => '≤ ' + Math.round(30 * x)], evade: [null, pc] };
  const d = LAB[p.stat]; if (!d) return null;
  const E = (lab, val) => fxPart('bonus', lab, val, 'eff');   // (every characteristic line is a bonus: green)
  const lab = d[0] ? T(d[0]) : L(p.name), f = d[1], parts = [E(lab, `${lv > 1 ? f(v(lv - 1)) + ' → ' : ''}${f(v(lv))}`)];
  if (p.stat === 'magnet') parts.push(E(T('ps_kamas'), `${lv > 1 ? pc(0.1 * (lv - 1)) + ' → ' : ''}${pc(0.1 * lv)}`));
  if (p.reachW) { const w = l => p.reachW * l + (p.reachShop || 0) * ((Store.data.passLv || {})[p.id] || 0); parts.push(E(T('ps_wreach'), `${lv > 1 ? pc(w(lv - 1)) + ' → ' : ''}${pc(w(lv))}`)); }   // (0.92: Portée's weapon reach shown, as Run.recompute st.wreach)
  if (p.block) { const b = l => p.block[0] + (p.block[1] - p.block[0]) * (l - 1) / Math.max(1, p.max - 1); parts.push(E(T('ps_block'), `${lv > 1 ? pc(b(lv - 1)) + ' → ' : ''}${pc(b(lv))}`)); }
  return parts;
}
function setLang(lg) {
  if (!LANGS.includes(lg)) return;
  LANG = lg; Store.data.settings.lang = lg; Store.save();
  document.documentElement.lang = lg;
}

// 0.23: a text that overflows its fixed box (level-up cards in German / Portuguese) gets a smaller font until it fits
// 0.62 (texts still cut on many cards): a level-up card's text is never cut. Its description shrinks (fitText),
// then the card tightens (smaller picture, smaller gaps), then — still too long — every card of the row grows to the
// tallest one (PC) or that description scrolls (phones, whose rows share the window's height). Done again once the
// cards' pictures and fonts are in, and when the window changes size (they change the heights)
function fitCards(root) {
  const cards = [...root.querySelectorAll('.up-cards .up-card')]; if (!cards.length) return;
  const phone = getComputedStyle(cards[0]).display === 'grid';
  for (const c of cards) { c.classList.remove('tight', 'tighter', 'scrolly'); c.style.height = ''; const d = c.querySelector('.up-desc'); if (d) { d.style.fontSize = ''; d.style.lineHeight = ''; d.style.flex = ''; } }
  let grow = 0;
  for (const c of cards) {
    const d = c.querySelector('.up-desc'); if (!d) continue;
    const over = () => d.scrollHeight > d.clientHeight + 1 || c.scrollHeight > c.clientHeight + 1;
    fitText(d, 10); if (!over()) continue;
    c.classList.add('tight'); fitText(d, 9); if (!over()) continue;
    c.classList.add('tighter'); fitText(d, 8.5); if (!over()) continue;
    if (phone) { c.classList.add('scrolly'); continue; }
    c.style.height = 'auto'; d.style.flex = '0 0 auto'; grow = Math.max(grow, c.offsetHeight + 1);
  }
  if (grow) for (const c of cards) c.style.height = grow + 'px';
}
function fitCardsSoon(el) {
  let q = false; const go = () => { if (q) return; q = true; requestAnimationFrame(() => { q = false; if (el.isConnected) fitCards(el); }); };   // (0.98.1: the asks of one frame — each card picture's load — fitted once)
  requestAnimationFrame(go); setTimeout(go, 450);
  for (const im of el.querySelectorAll('.up-cards img')) if (!im.complete) im.addEventListener('load', go, { once: true });
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(go);
}
window.addEventListener('resize', () => { const el = document.querySelector('.levelup'); if (el) fitCardsSoon(el); });
// 0.65 (what fits a 16:9 screen must not scroll): a window or list that overflows by a little (at most 45 % of
// its height: the options, the end screen, a zone of the bestiary…) gets its content scaled down — CSS zoom on its
// children, down to 0.72 — until nothing scrolls; the long lists (achievements, statistics, armory) keep their scroll.
// Done on every new screen / content (a MutationObserver, debounced) and when the window changes size
const FIT_SEL = '#ui .window > .content, .modal .content, .best-list, .best-detail, .shop-grid, .arm-detail';
function fitNoScroll(el, min = 0.72) {
  if (!el || !el.isConnected || el.closest('.levelup')) return;
  const cs = getComputedStyle(el); if (!/(auto|scroll)/.test(cs.overflowY)) return;
  const kids = [...el.children]; if (!kids.length) return;
  const cur = parseFloat(kids[0].style.zoom) || 1;
  const over = () => el.scrollHeight > el.clientHeight + 2;
  if (cur < 1 && !over()) {   // (it may fit at a larger size again: grow back a step at a time)
    let k = cur; while (k < 1) { const n = Math.min(1, k + 0.03); for (const c of kids) c.style.zoom = n === 1 ? '' : n.toFixed(2); if (over()) { for (const c of kids) c.style.zoom = k.toFixed(2); break; } k = n; }
    return;
  }
  if (!over() || el.scrollHeight * cur > el.clientHeight * 1.45) return;
  for (let k = cur - 0.03; k >= min - 1e-6 && over(); k -= 0.03) for (const c of kids) c.style.zoom = k.toFixed(2);
}
const fitAll = () => { if (typeof Game !== 'undefined' && Game.state === 'run' && !UI.modalOpen()) return; for (const el of document.querySelectorAll(FIT_SEL)) fitNoScroll(el); };   // (never during play: the chat changes the DOM)
// 0.85 (a scrollbar showed for a moment, then went): the fit ran 90 ms after the change, so the browser painted the
// overflow first. It now runs in the MutationObserver itself (before the next paint), again once images / fonts load.
{ let tm = 0; const soon = () => { clearTimeout(tm); tm = setTimeout(fitAll, 90); };
  new MutationObserver(() => { fitAll(); soon(); }).observe(document.body, { childList: true, subtree: true }); window.addEventListener('resize', soon); }
function fitText(el, min = 9) {
  // (0.98.1: the largest size that fits, by halves — 3 or 4 layouts instead of one per half pixel)
  const fs0 = parseFloat(getComputedStyle(el).fontSize) || 12.5, over = () => el.scrollHeight > el.clientHeight + 1;
  if (!over() || fs0 <= min) return;
  const set = v => { el.style.fontSize = v + 'px'; el.style.lineHeight = '1.2'; };
  let lo = min, hi = fs0 - 0.5;   // (sizes by 0.5 px, as before)
  set(lo); if (over()) return;
  while (hi - lo > 0.25) { const mid = Math.round((lo + hi)) / 2; if (mid <= lo) break; set(mid); if (over()) hi = mid - 0.5; else lo = mid; }
  set(lo);
}
// 0.28: a button whose label is wider than the button gets a smaller font until it fits
function fitWidth(el, min = 11) {
  let fs = parseFloat(getComputedStyle(el).fontSize) || 16;
  let n = 0; while (el.scrollWidth > el.clientWidth && fs > min) { fs -= 0.5; n++; el.style.fontSize = fs + 'px'; }
  if (n) el.style.fontSize = (fs - 0.5) + 'px';   // (one more step: the ellipsis shows at a 1 px overflow)
}
// 0.85 (the grade medallions were blurry): the end screen's grade drawn as a vector medallion in the look of the
// original pictures (assets/ui/rank_<L>.webp, kept as the reference): a segmented gold ring with a dark rim, a coloured
// disc with brushed shading, the cream letter in Lilita with a thick dark outline and a carved shadow. Sharp at any size.
const RANK_COL = { A: ['#ffd25a', '#e39a14', '#8a5208'], B: ['#5aa6e8', '#2a68b4', '#123a70'], C: ['#6ccc4a', '#2f8a2a', '#145018'], D: ['#a46ad8', '#6a2f9a', '#381454'], E: ['#ec6a52', '#b8322a', '#661410'], F: ['#8a8a8a', '#4e4e4e', '#262626'] };
function rankMedal(g) {
  const c = RANK_COL[g] || RANK_COL.F, id = 'rk' + g + Math.floor(Math.random() * 1e6);
  let notches = ''; for (let i = 0; i < 7; i++) { const a = (i / 7) * Math.PI * 2 + 0.4, x1 = 50 + Math.cos(a) * 38.5, y1 = 50 + Math.sin(a) * 38.5, x2 = 50 + Math.cos(a) * 46.5, y2 = 50 + Math.sin(a) * 46.5; notches += `<line x1='${x1.toFixed(1)}' y1='${y1.toFixed(1)}' x2='${x2.toFixed(1)}' y2='${y2.toFixed(1)}' stroke='#7a4a0c' stroke-width='1.3' opacity='.75'/>`; }
  let brush = ''; for (let i = 0; i < 9; i++) brush += `<path d='M${18 + i * 7} ${30 + (i % 3) * 3} q 6 18 -2 40' stroke='#fff' stroke-width='1' fill='none' opacity='.06'/>`;
  const svg = `<svg class='ov-rank' viewBox='0 0 100 100' xmlns='http://www.w3.org/2000/svg' role='img' aria-label='${g}'><defs>
    <linearGradient id='${id}r' x1='0' y1='0' x2='.3' y2='1'><stop offset='0' stop-color='#fff1b0'/><stop offset='.35' stop-color='#f0bc48'/><stop offset='.75' stop-color='#c8861e'/><stop offset='1' stop-color='#8a5410'/></linearGradient>
    <radialGradient id='${id}d' cx='.38' cy='.32' r='.8'><stop offset='0' stop-color='${c[0]}'/><stop offset='.55' stop-color='${c[1]}'/><stop offset='1' stop-color='${c[2]}'/></radialGradient>
    <linearGradient id='${id}l' x1='0' y1='0' x2='0' y2='1'><stop offset='0' stop-color='#fffaf0'/><stop offset='1' stop-color='#ead6a8'/></linearGradient>
    <clipPath id='${id}c'><circle cx='50' cy='50' r='37.5'/></clipPath></defs>
    <circle cx='50' cy='52' r='49' fill='rgba(0,0,0,.35)'/><circle cx='50' cy='50' r='48.5' fill='#2e1806'/>
    <circle cx='50' cy='50' r='46.5' fill='url(#${id}r)'/>${notches}
    <path d='M16 34 A37 37 0 0 1 60 9' stroke='#fff8d0' stroke-width='2.2' fill='none' opacity='.6' stroke-linecap='round'/>
    <circle cx='50' cy='50' r='38.5' fill='#3a1e06'/><circle cx='50' cy='50' r='37.5' fill='url(#${id}d)'/>
    <g clip-path='url(#${id}c)'>${brush}<circle cx='50' cy='50' r='37.5' fill='none' stroke='rgba(0,0,0,.35)' stroke-width='5'/></g>
    <g transform='rotate(-8 50 50)' font-family='Lilita, DofusBold, Verdana' font-size='64' text-anchor='middle'>
      <text x='51.8' y='75.5' fill='#2a1406' stroke='#2a1406' stroke-width='9' stroke-linejoin='round'>${g}</text>
      <text x='50' y='72.5' fill='url(#${id}l)' stroke='#2a1406' stroke-width='6' stroke-linejoin='round' paint-order='stroke'>${g}</text></g></svg>`;
  const w = document.createElement('div'); w.innerHTML = svg; return w.firstElementChild;
}
function diceFace(n) { return ['⚀', '⚁', '⚂', '⚃', '⚄', '⚅'][clamp(Math.round(n), 1, 6) - 1]; }

// 0.56: in the menus, a text cut by its box (ellipsis, clipped cell…) shows whole in a tip at the mouse
(() => {
  let tip = null, cur = null;
  const clipped = e => e && e.textContent && e.textContent.trim().length > 1 && e.children.length === 0 && (e.scrollWidth > e.clientWidth + 1 || e.scrollHeight > e.clientHeight + 2);
  const hide = () => { if (tip) tip.style.display = 'none'; cur = null; };
  document.addEventListener('mousemove', ev => {
    if (Game.state === 'run' && !UI.modalOpen()) return hide();
    let e = ev.target;
    for (let k = 0; e && k < 3 && !clipped(e); k++) e = e.parentElement && e.parentElement.closest && e.parentElement.closest('#ui, .modal') ? e.parentElement : null;
    if (!clipped(e)) return hide();
    if (!tip) { tip = document.createElement('div'); tip.className = 'cut-tip'; document.body.appendChild(tip); }
    if (cur !== e) { cur = e; tip.textContent = e.textContent.trim(); }
    tip.style.display = 'block';
    const r = tip.getBoundingClientRect(), x = Math.min(ev.clientX + 14, innerWidth - r.width - 6), y = ev.clientY + 18 + r.height > innerHeight ? ev.clientY - r.height - 10 : ev.clientY + 18;
    tip.style.left = x + 'px'; tip.style.top = y + 'px';
  }, { passive: true });
  document.addEventListener('mousedown', hide, true);
})();

// 0.60: a spell fusion's recipe: [picture a] + [picture b] (the weapon: the one held in the run, else its type's picture)
function sfRecipe(R, f, size = 24) {   // (0.61: size = as big as it is shown: the Armurerie's rows show them at 40 px)
  const C = Game.C, pic = (k, i) => i && f.kind === 'weapon' ? ((R && R.weapon && (R.weapon.def.of || R.weapon.def.id) === k) ? R.weapon.icon : (C.weapons.find(w => w.id === k) || {}).icon) : 'sp_' + C.spells[k].icon;
  const nm = (k, i) => i && f.kind === 'weapon' ? L((C.weapons.find(w => w.id === k) || {}).name) : L(C.spells[k].name);
  return [tipIcon(pic(f.src[0], 0), nm(f.src[0], 0), size), h('b', null, '+'), tipIcon(pic(f.src[1], 1), nm(f.src[1], 1), size)];
}
// 0.60: a level-up card's spell / weapon that has a fusion in this run's class: '✦ + [partner] → [fused] Name'
// 0.91: does this spell / weapon fuse with a spell or weapon the character already has? (the card is animated)
function sfReady(R, o) {
  const C = Game.C, isW = o.kind === 'weapon', wt = isW ? (weaponById(C, o.id) || {}).of || o.id : null;
  const has = id => R.spells.some(s => s.def.id === id), W = R.weapon && (R.weapon.def.of || R.weapon.def.id);
  return (C.spellFusions || []).some(f => sfusionOf(f, R.cls.id) && !R.sfused.has(f.id) && !(R.banned && R.banned.has('sfusion:' + f.id)) && (isW
    ? f.kind === 'weapon' && f.src[1] === wt && has(f.src[0])
    : f.src[0] === o.id ? (f.kind === 'weapon' ? W === f.src[1] : has(f.src[1])) : f.src[1] === o.id && f.kind !== 'weapon' && has(f.src[0])));
}
function sfHint(R, o) {
  const C = Game.C, isW = o.kind === 'weapon', wt = isW ? (weaponById(C, o.id) || {}).of || o.id : null;
  const f = (C.spellFusions || []).find(f => sfusionOf(f, R.cls.id) && !R.sfused.has(f.id) && (isW ? f.kind === 'weapon' && f.src[1] === wt : f.src.includes(o.id)));
  if (!f) return null;
  const sp = C.spells[f.id], other = isW ? f.src[0] : f.src.find(k => k !== o.id), otherW = f.kind === 'weapon' && other === f.src[1];
  const oi = otherW ? (C.weapons.find(w => w.id === other) || {}).icon : 'sp_' + C.spells[other].icon;
  const tip = T('sfusion_with', { a: isW ? L(weaponById(C, o.id).name) : L(C.spells[o.id].name), b: otherW ? L(C.weapons.find(w => w.id === other).name) : L(C.spells[other].name), n: L(sp.name) });
  return h('div', { class: 'sf-recipe sf-hint', title: tip }, '✦ +', iconImg(oi, 20), '→', iconImg('sp_' + sp.icon, 20), h('small', null, L(sp.name)));
}
// 0.60: the shop's spell card: its fusions (cls null: a global spell, the fusions of every class using it)
function sfMini(cls, sid) {
  const C = Game.C, fs = (C.spellFusions || []).filter(f => (!cls || sfusionOf(f, cls)) && f.src.includes(sid)); if (!fs.length) return null;
  // (0.98.3: three columns: the fusion's picture stays in the middle, the star on its left, on its right the weapon a fusion needs)
  const wps = [...new Set(fs.filter(f => f.kind === 'weapon').map(f => C.weapons.find(w => w.id === f.src[1])))];
  return h('div', { class: 'sf-recipe sf-mini' }, h('span', { class: 'sf-star' }, '✦'), h('span', { class: 'sf-ics' }, ...fs.map(f => {
    const cl = C.classes.find(c => c.id === f.cls), b = f.kind === 'weapon' ? L(C.weapons.find(w => w.id === f.src[1]).name) : L(C.spells[f.src[1]].name);
    return tipIcon('sp_' + C.spells[f.id].icon, L(C.spells[f.id].name) + (cls || !cl ? '' : ' (' + L(cl.name) + ')') + ' — ' + T('sfusion_with', { a: L(C.spells[f.src[0]].name), b, n: L(C.spells[f.id].name) }), 18);
  })), h('span', { class: 'sf-wps' }, ...wps.map(w => tipIcon(w.icon, L(w.name), 18))));
}

// 0.95: the level-up cards' way to their centre (--dx, --dy, in their own layout px) and their tilt in the deck (--rz),
// for the reroll's gathering and dealing (index.html cardGather / cardDeal)
function deckVars(el) {
  const cards = [...el.querySelectorAll('.up-card')], P = cards.map(c => [c.offsetLeft + c.offsetWidth / 2, c.offsetTop + c.offsetHeight / 2]); if (!cards.length) return;
  const cx = P.reduce((s, p) => s + p[0], 0) / P.length, cy = P.reduce((s, p) => s + p[1], 0) / P.length;
  cards.forEach((c, i) => { c.style.setProperty('--dx', Math.round(cx - P[i][0]) + 'px'); c.style.setProperty('--dy', Math.round(cy - P[i][1]) + 'px'); c.style.setProperty('--rz', ((i - (cards.length - 1) / 2) * 5) + 'deg'); });
}
// 0.60: the reroll's show on a canvas over the level-up window (see levelUpMenu): the client's Écaflip die thrown in,
// three bounces (higher clacks each time), the card suits whirling around, a golden landing with the clover
// 0.61 (the dice were pixelated): the die, the suits and the clover come from big copies of their sheets made for
// this scene (ui603 / ui611 / ui605, tools/assets/build_fxhd061.py: the scene shows them ~10 times bigger than in a run), and the
// canvas is as sharp as the screen (it was drawn at the menus' layout size, then zoomed by --uiz)
// the client's die clip (fx 603, 74 frames): only its first 7 poses are one die whole — every later one draws a second,
// half-turned cube behind it (0.95: the first list kept some) —, played back
// and forth, landing on pose 0; and the die's centre from the clip's origin in Dofus px (27.5 / 5.5 px at zoom 8)
const DIE_POSES = [0, 1, 2, 3, 4, 5, 6, 5, 4, 3, 2, 1], DIE_C = [3.44, 0.69];
function diceStage(cv, R) {
  ['ui603', 'ui611', 'ui605', 603, 611, 605].forEach(f => FxSheets.load(f));
  const fx = (n) => FxSheets.get('ui' + n) || FxSheets.get(n);
  const box = cv.parentElement.getBoundingClientRect(), uz = Game._uiz || 1, dpr = Math.min(2, window.devicePixelRatio || 1) * uz, W = Math.max(200, box.width / uz), H = Math.max(160, box.height / uz);
  cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr); cv.style.width = W + 'px'; cv.style.height = H + 'px';
  const g = cv.getContext('2d'), t0 = performance.now(), cx = W / 2, cy = H * 0.5, S = Math.min(W, H), fired = {};
  const once = (k, f) => { if (!fired[k]) { fired[k] = 1; f(); } };
  const keys = Audio2.spellKeys({ fx: [603] }); Audio2.diceSfx('roll');
  const B = [0.22, 0.52, 0.76, 0.95];   // bounces (s)
  const step = () => {
    if (!cv.isConnected) return;
    const t = (performance.now() - t0) / 1000; if (t > 1.6) return;
    requestAnimationFrame(step);
    g.setTransform(dpr, 0, 0, dpr, 0, 0); g.clearRect(0, 0, W, H);
    const fade = Math.min(1, t / 0.15) * Math.min(1, (1.6 - t) / 0.2);
    const v = g.createRadialGradient(cx, cy, S * 0.1, cx, cy, S * 0.75); v.addColorStop(0, `rgba(40,20,60,${0.35 * fade})`); v.addColorStop(1, `rgba(10,4,16,${0.8 * fade})`); g.fillStyle = v; g.fillRect(0, 0, W, H);
    // the card suits, whirling around the middle
    const su = fx(611);
    if (su && su.anims.shoot) { const an = su.anims.shoot, f = an.f[Math.floor(t * an.fps * 1.4) % an.f.length]; g.save(); g.globalAlpha = 0.85 * fade; g.translate(cx, cy); g.rotate(t * 2.4); su.draw(g, f, 0, 0, S / 95, false); g.rotate(Math.PI); su.draw(g, f, 0, 0, S / 130, false); g.restore(); }
    // the die: thrown from the left, three bounces, settles in the middle
    const sc = S / 52, G0 = cy + S * 0.12, X = [-0.1, 0.28, 0.42, 0.5, 0.5].map(v => v * W), HH = [0, 0.3, 0.15, 0.05];
    let x, y;
    if (t < B[0]) { const u = t / B[0]; x = X[0] + (X[1] - X[0]) * u; y = G0 - S * 0.5 * (1 - u * u); }   // the throw, falling in
    else if (t < B[3]) { let i = 1; while (i < 3 && t > B[i]) i++; const u = (t - B[i - 1]) / (B[i] - B[i - 1]); x = X[i] + (X[i + 1] - X[i]) * u; y = G0 - Math.sin(u * Math.PI) * S * HH[i]; }   // three bounces, lower each time
    else { x = cx; y = G0; }
    for (let i = 0; i < 3; i++) if (t > B[i]) once('b' + i, () => Audio2.diceSfx('clack', (i + 1) / 3));
    const die = fx(603);
    if (die && die.anims.root) {
      // 0.95 (the dice looked like they overlapped): the client clip turns its one die by drawing two half-turned
      // cubes over each other between its square poses, and the whole picture was spun round the clip's origin, off the
      // die's centre. Only the clean poses are shown now (DIE_POSES), spun round the die's own centre (DIE_C, Dofus px)
      const an = die.anims.root, P = DIE_POSES.filter(n => n < an.f.length), q = t < B[3] ? Math.floor(t * 20) % P.length : 0, f = an.f[P[q]];
      g.save(); g.globalAlpha = fade; g.fillStyle = 'rgba(0,0,0,0.35)'; g.beginPath(); g.ellipse(x, cy + S * 0.15, S * 0.09, S * 0.025, 0, 0, TAU); g.fill();
      g.translate(x, y); g.rotate(t < B[3] ? t * 9 : 0); die.draw(g, f, -DIE_C[0] * sc, -DIE_C[1] * sc, sc, false); g.restore();
    } else if (t > 0.5) { g.save(); g.translate(x, y); g.rotate(t * 9); g.font = `${Math.round(S * 0.2)}px serif`; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText('🎲', 0, 0); g.restore(); }
    // the landing: a golden flash, a ring, the clover rising
    if (t >= B[3]) {
      once('land', () => { Audio2.diceSfx('land'); if (keys.length) Audio2.play(keys[0], 0.5, 1.05); Audio2.play('stars', 0.6, 1.1); });
      const u = (t - B[3]) / 0.6;
      g.save(); g.globalCompositeOperation = 'lighter'; g.globalAlpha = Math.max(0, 1 - u) * 0.9; g.drawImage(RCache.glow('rgba(255,220,120,0.95)'), cx - S * 0.3, cy - S * 0.3, S * 0.6, S * 0.6); g.restore();
      g.save(); g.globalAlpha = Math.max(0, 0.8 * (1 - u)); g.strokeStyle = '#ffd24a'; g.lineWidth = S * 0.012; g.beginPath(); g.ellipse(cx, cy + S * 0.12, S * (0.08 + 0.5 * u), S * (0.03 + 0.18 * u), 0, 0, TAU); g.stroke(); g.restore();
      const cl = fx(605); if (cl && cl.anims.root) { const an = cl.anims.root, f = an.f[Math.min(an.f.length - 1, Math.floor((t - B[3]) * an.fps * 1.5))]; g.save(); g.globalAlpha = fade; cl.draw(g, f, cx, cy - S * 0.24 - u * S * 0.06, S / 70, false); g.restore(); }
    }
  };
  requestAnimationFrame(step);
}
