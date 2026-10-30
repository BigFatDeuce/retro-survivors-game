'use strict';
const NAV_HINTS = false;   // (0.61: the controller's button bar at the bottom of the menus, see Nav.hints)
// ---------------------------------------------------------------- menu navigation with a controller (and the keyboard: arrows, ZQSD / WASD)
// D-pad / left stick move a highlight between the clickable elements of the visible screen or pop-up, A clicks,
// B goes back / closes, LB-RB switch tabs, left-right adjust sliders and lists.
const Nav = {
  el: null, prev: [], repeatT: 0, lastDir: null, enabled: false,
  SEL: 'button:not([disabled]), .arm-card, .class-card, .map-card:not(.locked), .best-card, .up-card, .tot-spell, .tot-hint, .dofus-pick, input[type=range], input[type=checkbox], select, .shop-item .btn, .ach-card, .soul, .ttg-slot, .tmap-card:not(.unknown), .sf-row, a[href^="http"]',   // (0.91: the Discord links)
  // (0.92: an open colour palette holds the cursor too — it floats outside the window: down from its last row went to the skins)
  scope() { const p = document.querySelector('.sel-pop') || document.querySelector('.cpal.float:not(.hidden)'); return p || (UI.modal && UI.modal.isConnected ? UI.modal : null) || document.getElementById('ui'); },
  items() {
    const root = this.scope(); if (!root) return [];
    return [...root.querySelectorAll(this.SEL)].filter(e => { const r = e.getBoundingClientRect(); if (r.width < 2 || r.height < 2) return false; const cs = getComputedStyle(e); return cs.visibility !== 'hidden' && cs.display !== 'none' && !e.closest('.locked'); });
  },
  // (0.92: a menu opened from elsewhere starts on its default element, not where the cursor was the last time)
  forget(screen) { if (this.mem) delete this.mem[screen]; },
  set(e) {
    if (this.el) this.el.classList.remove('navfocus');
    if (e && e !== this.el) this.glidePop = performance.now();
    this.el = e; this.glide();
    if (e && typeof UI !== 'undefined' && UI.screen && !UI.modal) (this.mem || (this.mem = {}))[UI.screen] = { cls: e.className.replace(' navfocus', ''), txt: (e.textContent || '').slice(0, 40) };   // (0.60)
    if (e) { e.classList.add('navfocus'); e.scrollIntoView({ block: 'nearest', inline: 'nearest' }); if (typeof e.focus === 'function' && ['INPUT', 'SELECT'].includes(e.tagName)) e.focus({ preventScroll: true }); try { e.dispatchEvent(new CustomEvent('navfocus', { bubbles: true })); } catch (x) { } }
  },
  // 0.98: the cursor drawn as one glowing frame (#navglide) that slides from the last element to the new one (eased each
  // frame towards its box, so it also follows a list that scrolls or a card that grows), a light running round its edge,
  // a small pulse at each move; clipped to the list that scrolls it. Only while an element has the cursor
  glide() {
    if (!this.el) { if (this._gl) { this._gl.style.display = 'none'; this._glSt = null; } return; }
    if (!this._gl) { const g = document.createElement('div'); g.id = 'navglide';   // (0.98.1: tiny sparks round it, CSS-animated: placed once along its edge)
      const P = [[8, 0], [34, 0], [63, 0], [90, 0], [100, 30], [100, 72], [82, 100], [52, 100], [20, 100], [0, 66], [0, 24], [45, 0]];
      P.forEach(([x, y], i) => { const s = document.createElement('i'); s.style.left = x + '%'; s.style.top = y + '%'; s.style.setProperty('--d', (-i * 0.29).toFixed(2) + 's'); s.style.setProperty('--dx', ((x - 50) / 50 * 6).toFixed(1) + 'px'); s.style.setProperty('--dy', ((y - 50) / 50 * 6 - 4).toFixed(1) + 'px'); g.append(s); });
      document.body.append(g); this._gl = g; document.body.classList.add('navglide'); }
    if (this._glRaf) return;
    let last = performance.now();
    const step = (now) => {
      const e = this.el, g = this._gl;
      if (!e || !e.isConnected) { g.style.display = 'none'; this._glRaf = 0; this._glBox = null; this._glSt = null; this._glEl = null; return; }
      const r = e.getBoundingClientRect(), dt = Math.min(0.05, (now - last) / 1000); last = now;
      const B = this._glBox || (this._glBox = { x: r.left, y: r.top, w: r.width, h: r.height }), k = 1 - Math.exp(-dt * 20);
      B.x += (r.left - B.x) * k; B.y += (r.top - B.y) * k; B.w += (r.width - B.w) * k; B.h += (r.height - B.h) * k;
      const pk = Math.max(0, 1 - (now - (this.glidePop || 0)) / 260), pad = 3 + 3 * pk;
      if (this._glEl !== e) {   // (0.98.1: its scrolling list and its corner read once per element, not every frame)
        this._glEl = e; let sc = e.parentElement; while (sc && sc !== document.body) { const cs = getComputedStyle(sc); if (/(auto|scroll)/.test(cs.overflowY + cs.overflowX)) break; sc = sc.parentElement; }
        this._glSc = sc && sc !== document.body ? sc : null; this._glRad = getComputedStyle(e).borderTopLeftRadius;
      }
      const c = this._glSc ? this._glSc.getBoundingClientRect() : null, x = B.x - pad, y = B.y - pad, w = B.w + pad * 2, h = B.h + pad * 2;
      const st = `${x.toFixed(1)}|${y.toFixed(1)}|${w.toFixed(1)}|${h.toFixed(1)}|${pad.toFixed(2)}|${c ? c.top + ',' + c.left + ',' + c.right + ',' + c.bottom : ''}`;   // (pad: its corner follows the pulse to its end)
      if (st !== this._glSt) {   // (nothing written while it stands still)
        this._glSt = st;
        Object.assign(g.style, { display: 'block', transform: `translate(${x.toFixed(1)}px, ${y.toFixed(1)}px)`, width: w.toFixed(1) + 'px', height: h.toFixed(1) + 'px',
          clipPath: c ? `inset(${Math.max(0, c.top - y - 8)}px ${Math.max(0, x + w - c.right - 8)}px ${Math.max(0, y + h - c.bottom - 8)}px ${Math.max(0, c.left - x - 8)}px round 10px)` : 'none',
          borderRadius: Math.min(14, Math.max(6, this._glRad === '50%' ? h / 2 : parseFloat(this._glRad) + pad || 8)) + 'px' });
      }
      this._glRaf = requestAnimationFrame(step);
    };
    this._glRaf = requestAnimationFrame(step);
  },
  ensure() {
    const it = this.items();
    if (this.el && it.includes(this.el) && this.el.isConnected) return it;
    const M = !UI.modal && this.mem && this.mem[UI.screen], back = M && it.find(e => e.className.replace(' navfocus', '') === M.cls && (e.textContent || '').slice(0, 40) === M.txt);   // (0.60: where it was)
    // (0.92: an element marked data-nav-first takes the cursor when a menu opens: the shop's first sub-tab, the first class)
    const pref = back || it.find(e => e.hasAttribute('data-nav-first')) || it.find(e => e.classList.contains('sel')) || it.find(e => e.classList.contains('orange') || e.classList.contains('active')) || it[0] || null;   // (0.92: a '.sel' wins over an orange button met first — the run given up: Menu principal, not Rejouer)
    this.set(pref); return it;
  },
  // grid-aware spatial navigation:
  // 1) an element on the same row (left/right) or the same column (up/down) — rectangles overlapping on the other axis;
  // 2) up/down otherwise: the nearest row in that direction, then the element of that row closest horizontally;
  // 3) left/right otherwise: only an element of another panel (never a diagonal jump inside the same grid)
  move(dx, dy) {
    let it = this.ensure(); if (!this.el) return;
    // 0.60: the main menu's corner buttons (Crédits, Mode sombre): left / right goes back to Jouer, never from one to the other
    if (dx && !dy && this.el.dataset && this.el.dataset.navX === 'home') { const t = document.querySelector('#ui .menu-buttons .btn.orange'); if (t) { this.set(t); Audio2.blip('click'); return; } }
    const a = this.el.getBoundingClientRect(); const ax = a.left + a.width / 2, ay = a.top + a.height / 2;
    // 0.54: inside a list that scrolls (souls, cards, shop…), keep to it while it has something in that direction:
    // the tabs above are reached only from its first row (scrolled-out items count as being there)
    const scr = e => { for (let p = e.parentElement; p && p !== document.body; p = p.parentElement) { const cs = getComputedStyle(p); if ((dy && p.scrollHeight > p.clientHeight + 2 && /(auto|scroll)/.test(cs.overflowY)) || (dx && !dy && p.scrollWidth > p.clientWidth + 2 && /(auto|scroll)/.test(cs.overflowX))) return p; } return null; };
    const box = scr(this.el);
    if (box) {
      const inn = it.filter(e => e !== this.el && box.contains(e) && (() => { const b = e.getBoundingClientRect(); return (b.left + b.width / 2 - ax) * dx + (b.top + b.height / 2 - ay) * dy > 4; })());
      if (inn.length) it = it.filter(e => e === this.el || box.contains(e));
    }
    if (dx && dy) {   // a diagonal: the nearest element in that quarter
      let best = null, bs = Infinity;
      for (const e of it) {
        if (e === this.el) continue;
        const b = e.getBoundingClientRect(), vx = b.left + b.width / 2 - ax, vy = b.top + b.height / 2 - ay;
        if (vx * dx < 6 || vy * dy < 6) continue;
        const d = Math.hypot(vx, vy), off = Math.abs(Math.abs(vx) - Math.abs(vy)) / d, sc = d * (1 + off);
        if (sc < bs) { bs = sc; best = e; }
      }
      if (best) { this.set(best); Audio2.blip('click'); }
      return;
    }
    const par = this.el.parentElement;
    const ov = (a0, a1, b0, b1) => Math.min(a1, b1) - Math.max(a0, b0);
    let best = null, bs = Infinity, bx0 = Infinity; const rest = [];
    for (const e of it) {
      if (e === this.el) continue;
      const b = e.getBoundingClientRect(); const bx = b.left + b.width / 2, by = b.top + b.height / 2;
      const vx = bx - ax, vy = by - ay; const along = vx * dx + vy * dy; if (along <= 4) continue;
      const perp = Math.abs(vx * dy - vy * dx);
      const o = dx ? ov(a.top, a.bottom, b.top, b.bottom) : ov(a.left, a.right, b.left, b.right);
      const need = 0.3 * Math.min(dx ? a.height : a.width, dx ? b.height : b.width);
      // (0.92: for an aligned target the sideways gap runs to its edge, not its centre: a wide one — the shop's skin search
      // above the first cards — was beaten by a farther tab)
      if (o >= need) { const sc = along + (dx ? Math.max(0, b.top - ay, ay - b.bottom) : Math.max(0, b.left - ax, ax - b.right)) * 0.5; if (sc < bs - 6 || (sc < bs + 6 && bx < bx0)) { bs = Math.min(bs, sc); best = e; bx0 = bx; } }   // (a tie: the left one)
      else rest.push({ e, along, perp, b });
    }
    if (!best && rest.length) {
      if (dy) {
        const cand = rest.filter(r => r.perp <= r.along * 3 + 40);
        if (cand.length) {
          // nearest row: the smallest edge gap in the pressed direction
          const gap = r => dy > 0 ? r.b.top - a.bottom : a.top - r.b.bottom;
          const g0 = Math.min(...cand.map(gap)), row = cand.filter(r => gap(r) <= g0 + Math.max(12, a.height * 0.5));
          row.sort((p, q) => (p.perp - q.perp) || (p.b.left - q.b.left)); if (row.length > 1 && Math.abs(row[0].perp - row[1].perp) < 8) row.sort((p, q) => p.b.left - q.b.left); best = row[0].e;
        }
      } else {
        const cand = rest.filter(r => r.e.parentElement !== par && r.perp <= r.along * 1.2).sort((p, q) => (p.along + p.perp * 2) - (q.along + q.perp * 2));
        if (cand.length) best = cand[0].e;
      }
    }
    // 0.60: the main menu's column wraps around (down from the last button = Jouer, up from Jouer = the last row)
    if (!best && dy && !dx && this.el.closest && this.el.closest('.menu-buttons')) {
      const col = it.filter(e => e.closest('.menu-buttons')); if (col.length > 1) best = dy > 0 ? col[0] : col.filter(e => e.getBoundingClientRect().top >= col[col.length - 1].getBoundingClientRect().top - 4)[0];
    }
    if (best) { this.set(best); Audio2.blip('click'); }
  },
  // 0.60: the controller's button prompts at the bottom of the menus (A / B / LB-RB), like console games.
  // 0.61: removed — they crowded the screen; the bar stays hidden (NAV_HINTS = true brings it back)
  hints() {
    let bar = this._bar; const on = NAV_HINTS && Input.dev === 'pad' && this.active() && !(Game.state === 'run' && !UI.modalOpen());
    if (!on) { if (bar) bar.style.display = 'none'; return; }
    if (!bar) { bar = this._bar = document.createElement('div'); bar.id = 'padhints'; document.body.append(bar); }
    const tabs = !!(this.scope() && this.scope().querySelector('.tabs')), key = (tabs ? 't' : '') + (UI.levelUpOpen ? 'l' : '') + LANG;
    const cap = t => t.charAt(0).toUpperCase() + t.slice(1);
    if (bar._k !== key) { bar._k = key; bar.innerHTML = `<span><b class="pa">A</b>${T('nav_ok')}</span>` + (UI.levelUpOpen ? '' : `<span><b class="pb">B</b>${cap(T('ctl_back'))}</span>`) + (tabs ? `<span><b class="pl">LB</b><b class="pl">RB</b>${cap(T('ctl_tabs'))}</span>` : ''); }
    bar.style.display = '';
  },
  // right stick: scrolls the list / window under the highlight (or the biggest scrollable box of the screen)
  scrollBy(px) {
    const root = this.scope(); if (!root) return;
    const can = e => e && e.scrollHeight > e.clientHeight + 2 && /(auto|scroll)/.test(getComputedStyle(e).overflowY);
    let s = null;
    for (let e = this.el; e && e !== document.body; e = e.parentElement) { if (can(e)) { s = e; break; } if (e === root) break; }
    if (!s) {
      const c = this._sc, now = performance.now();
      if (c && c.root === root && now - c.t < 400 && c.el.isConnected) s = c.el;
      else { let bestH = 0; for (const e of [root, ...root.querySelectorAll('*')]) { if (e.clientHeight > bestH && can(e)) { bestH = e.clientHeight; s = e; } } if (s) this._sc = { root, el: s, t: now }; }
    }
    if (s) s.scrollTop += px;
  },
  adjust(dir) {
    const e = this.el; if (!e || !e.isConnected) return false;   // (0.94: a volume slider of a closed Options screen kept taking left / right — the volume changed unseen, the highlight never moved)
    if (e.tagName === 'INPUT' && e.type === 'range') { const st = +e.step || 0.05; e.value = clamp(+e.value + dir * st, +e.min, +e.max); e.dispatchEvent(new Event('input', { bubbles: true })); return true; }
    return false;   // (0.54: a select is never changed by left / right — the language changed by itself; A / Enter opens its list)
  },
  // a <select> opened from the keyboard / controller: its values as a list of buttons over the page
  selectPopup(sel) {
    const r = sel.getBoundingClientRect(), box = h('div', { class: 'sel-pop' }), close = () => { box.remove(); UI._palClose = null; this.set(sel); };
    [...sel.options].forEach((o, i) => box.append(btn(o.textContent, () => { close(); if (sel.selectedIndex !== i) { sel.selectedIndex = i; sel.dispatchEvent(new Event('change', { bubbles: true })); } }, i === sel.selectedIndex ? 'active' : '')));
    box.style.left = Math.max(8, Math.min(innerWidth - 260, r.left)) + 'px'; box.style.top = Math.max(8, Math.min(innerHeight - 40 * sel.options.length - 20, r.bottom + 4)) + 'px';
    document.body.append(box); UI._palClose = close;   // (B / Échap close it, like the colour palette)
    this.set(box.querySelector('.btn.active') || box.querySelector('.btn'));
  },
  press() {
    if (UI.modal && UI.modal.onAct && UI.modal.onAct()) return;   // (0.98: a window that takes the action key itself: the Manuel du Tailleur's reel, pressed twice, skips)
    this.ensure(); const e = this.el; if (!e) return;
    if (e.tagName === 'INPUT' && e.type === 'checkbox') { e.click(); return; }
    if (e.tagName === 'SELECT') { this.selectPopup(e); return; }   // 0.40: a list to pick from (it used to jump to the next value)
    // remember which card was pressed: when the screen re-renders (shop purchase…), the focus returns to that same card
    const holder = e.closest && e.closest('[data-nav]'), key = holder ? holder.getAttribute('data-nav') : null;
    const r0 = e.getBoundingClientRect(), cx = r0.left + r0.width / 2, cy = r0.top + r0.height / 2, tag = e.tagName, cls0 = e.className;
    e.click();
    setTimeout(() => {
      if (this.el && !this.el.isConnected) {
        this.el = null;
        const root = this.scope(), card = key && root ? root.querySelector(`[data-nav="${CSS.escape(key)}"]`) : null;
        let target = card ? (card.matches(this.SEL) ? card : card.querySelector(this.SEL)) : null;
        // otherwise (a panel redrawn around the pressed button, e.g. the sex switch): the same kind of element at the same place
        if (!target) {
          let bd = 90 * 90;
          for (const c of this.items()) {
            const r = c.getBoundingClientRect(), d = (r.left + r.width / 2 - cx) ** 2 + (r.top + r.height / 2 - cy) ** 2 + (c.tagName === tag && c.className.replace(' navfocus', '') === cls0.replace(' navfocus', '') ? 0 : 60 * 60);
            if (d < bd) { bd = d; target = c; }
          }
        }
        if (target) this.set(target);
      }
      this.ensure();
    }, 60);
  },
  // 0.94 (quality audit): back on the menu it came from, the highlight shows at once where it was (as press() does) — it
  // stayed on the closed screen's element, nothing was lit until the next key, which then moved one step from there
  back() {
    this._back();
    setTimeout(() => { if (this.el && !this.el.isConnected) { this.el = null; if (this.active()) this.ensure(); } }, 60);
  },
  _back() {
    if (Game.state === 'tot' || (Game.state === 'run' && !UI.modal)) return;   // (0.61: B no longer leaves ToT's fight or the run: the pause menu's 'Abandonner' does)
    if (UI._palClose) { const z = UI._palClose; z(); return; }
    if (UI.modal) {
      if (Game.state === 'run' && Game.paused) { Game.togglePause(); return; }
      if (UI.levelUpOpen) { if (UI._luBack) UI._luBack(); return; }   // (0.60: the cards' window: B never rerolls / picks)
      const c = UI.modal.querySelector('.close') || UI.modal.querySelector('[data-back]') || UI.modal.querySelector('.btn:not(.orange)');   // (0.97: a window's own 'back' first — the save code's Échap pressed 'Load this code')
      if (c) c.click(); return;
    }
    const cl = document.querySelector('#ui .window .close'); if (cl) cl.click(); else UI.back();
  },
  tab(dir) {
    const root = this.scope(); const tabs = root && root.querySelector('.tabs'); if (!tabs) return;
    const bs = [...tabs.querySelectorAll('.btn:not(.disabled)')]; const i = bs.findIndex(b => b.classList.contains('active'));
    const n = bs[(i + dir + bs.length) % bs.length]; if (n) { n.click(); this.el = null; }
  },
  // which UI is active: menus, pop-ups, or nothing (gameplay)
  active() { return Game.state !== 'run' || UI.modalOpen(); },
  poll(dt) {
    const pads = navigator.getGamepads ? [...navigator.getGamepads()].filter(Boolean) : [];
    if (!pads.length) return;
    const p = pads[0]; const b = i => !!(p.buttons[i] && p.buttons[i].pressed);
    if (p.buttons.some(x => x && x.pressed) || Math.abs(p.axes[0] || 0) > 0.4 || Math.abs(p.axes[1] || 0) > 0.4 || Math.abs(p.axes[3] || 0) > 0.4) Input.dev = 'pad';
    // left stick: only its dominant axis counts (a slightly tilted 'right' is not an 'up'),
    // and the bounce of a released stick toward the opposite side is ignored for a short moment
    const lx = p.axes[0] || 0, ly = p.axes[1] || 0, hor = Math.abs(lx) > Math.abs(ly);
    let sdir = null;
    if (Math.max(Math.abs(lx), Math.abs(ly)) > 0.55) sdir = hor ? (lx < 0 ? 'left' : 'right') : (ly < 0 ? 'up' : 'down');
    // 0.54: diagonals (stick between two axes, or two d-pad buttons together)
    if (sdir && Math.min(Math.abs(lx), Math.abs(ly)) > 0.45 && Math.abs(Math.abs(lx) - Math.abs(ly)) < 0.35) sdir = (ly < 0 ? 'up' : 'down') + (lx < 0 ? 'left' : 'right');
    const now = performance.now(), OPP = { up: 'down', down: 'up', left: 'right', right: 'left', upleft: 'downright', downright: 'upleft', upright: 'downleft', downleft: 'upright' };
    if (!sdir && this._sdir) { this._srel = now; this._slast = this._sdir; }
    if (sdir && !this._sdir && this._slast === OPP[sdir] && now - (this._srel || 0) < 160) sdir = null;
    else this._sdir = sdir;
    if (!sdir) this._sdir = null;
    const sel = b(8); if (sel && !this._sel) toggleFullscreen(); this._sel = sel;
    const r3 = b(11); if (r3 && !this._r3) toggleTheme(); this._r3 = r3;   // 0.97: the right stick's button = light / dark menus (F1 on a keyboard)
    const sd = sdir || '';
    const st = { a: b(0), b: b(1), lb: b(4), rb: b(5), start: b(9), up: b(12) || sd.startsWith('up'), down: b(13) || sd.startsWith('down'), left: b(14) || sd.endsWith('left'), right: b(15) || sd.endsWith('right') };
    const was = this._st || {}; this._st = st;
    this.hints();
    if (!this.active()) { this.set(null); return; }
    this.enabled = true;
    // right stick (vertical): scroll menus and lists
    const ry = p.axes.length > 3 ? p.axes[3] : 0;
    if (Math.abs(ry) > 0.2) { const k = (Math.abs(ry) - 0.2) / 0.8; this.scrollBy(Math.sign(ry) * (220 + 1300 * k * k) * dt); }
    // 0.38: right stick (horizontal): the lists that scroll sideways (the Armurerie's characteristics)
    const rx = p.axes.length > 2 ? p.axes[2] : 0, hs = document.querySelector('#ui .arm-stats');
    if (hs && Math.abs(rx) > 0.2) { const k = (Math.abs(rx) - 0.2) / 0.8; hs.scrollLeft += Math.sign(rx) * (220 + 1300 * k * k) * dt; }
    const edge = k => st[k] && !was[k];
    const vy_ = st.up ? -1 : st.down ? 1 : 0, vx_ = st.left ? -1 : st.right ? 1 : 0;
    const dir = vx_ || vy_ ? (vy_ ? (vy_ < 0 ? 'up' : 'down') : '') + (vx_ ? (vx_ < 0 ? 'left' : 'right') : '') : null;
    if (dir) {
      const fire = dir !== this.lastDir || (this.repeatT -= dt) <= 0;
      if (fire) {
        this.repeatT = dir !== this.lastDir ? 0.38 : 0.13; this.lastDir = dir;
        if ((dir === 'left' || dir === 'right') && this.adjust(dir === 'left' ? -1 : 1)) return;
        this.move(vx_, vy_);
      }
    } else this.lastDir = null;
    if (edge('a')) this.press();
    // Start on the play screen: jump to "C'est parti !" (class and zone are already picked)
    if (edge('start') && Game.state !== 'run' && UI.screen === 'play') { const go = document.querySelector('#ui .start-btn'); if (go) { this.set(go); Audio2.blip('click'); } }
    if (edge('b')) this.back();
    if (edge('lb')) this.tab(-1);
    if (edge('rb')) this.tab(1);
  },
  key(e) {
    if (!this.active()) return false;
    // (0.97: every field one types in — the save code's box too: E pressed its button, W/A/S/D moved away while typing GODMODE)
    const tg = e.target && e.target.tagName; if (tg === 'TEXTAREA' || (tg === 'INPUT' && !/^(checkbox|radio|range|button|submit|reset)$/.test(e.target.type)) || (e.target && e.target.isContentEditable)) return false;
    // physical keys: W/S/A/D is ZQSD on an AZERTY keyboard and WASD on a QWERTY one
    const m = { ArrowUp: [0, -1], ArrowDown: [0, 1], ArrowLeft: [-1, 0], ArrowRight: [1, 0], KeyW: [0, -1], KeyS: [0, 1], KeyA: [-1, 0], KeyD: [1, 0] }[e.code];
    if (m) { if ((m[0]) && this.adjust(m[0])) return true; this.move(m[0], m[1]); return true; }
    // 0.85: Tab / Shift + Tab go through the items in reading order (the same items as the arrows and the controller)
    if (e.code === 'Tab') { const it = this.ensure(); if (it.length) { const i = it.indexOf(this.el), n = it.length; this.set(it[((i < 0 ? 0 : i) + (e.shiftKey ? -1 : 1) + n) % n]); Audio2.blip('click'); } e.preventDefault(); return true; }
    // 0.84: a choice opened during a run ignores the dash keys (Space, E) for its first moments (UI.PICK_GUARD, 0.98: 0.3 s,
    // was 2 s): a dash pressed as it popped up no longer picks a card (Enter, the mouse and the controller stay immediate:
    // the controller's dash is a trigger, never its A)
    if ((e.code === 'Space' || e.code === 'KeyE') && UI.modal && UI._modalAt && Game.state === 'run' && performance.now() - UI._modalAt < UI.PICK_GUARD) { e.preventDefault(); return true; }
    // Enter, and also Space / E (0.22), validate the highlighted choice
    if (['Enter', 'NumpadEnter', 'Space', 'KeyE'].includes(e.code) && !e.repeat && (this.el && this.el.isConnected || UI.levelUpOpen || (UI.modal && UI.modal.onAct))) { this.ensure(); if (this.el || (UI.modal && UI.modal.onAct)) { e.preventDefault(); this.press(); return true; } }
    return false;
  },
};

