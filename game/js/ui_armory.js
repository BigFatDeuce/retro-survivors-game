'use strict';
// ---------------------------------------------------------------- 0.28: the Armurerie (weapons, characteristics,
// TTG binder, treasure maps, Archimonster souls) and the synergies shown under the level-up choices.
// Which characteristic helps which spell or weapon follows what the spell code really reads (spells.js / game.js):
// st.amount (Invocations), st.area (Intelligence), st.projspeed (Portée), st.duration (Durée)… and the damage stats.
const SYN_TYPES = {
  amount: new Set(['projectile', 'orbit', 'zone', 'strike', 'line', 'bomb', 'beam', 'summon', 'cone']),
  area: new Set(['projectile', 'orbit', 'zone', 'strike', 'line', 'dash', 'leap', 'slam', 'toss', 'beam', 'trap', 'pulse', 'cone', 'melee', 'aura', 'bomb', 'detonate', 'cawotte', 'pwcawotte']),   // (0.96: the bombs' and the Cawottes' areas grow too: throwBomb, gspells.js)
  projspeed: new Set(['projectile', 'line', 'toss', 'bomb', 'beam', 'cone', 'summon']),   // (0.68: summons too)
  duration: new Set(['orbit', 'zone', 'trap', 'heal', 'buff', 'summon', 'cawotte', 'pwcawotte']),
};
// does characteristic p (a passive) help spell / weapon def?
function statBoosts(p, def) {
  const b = def.base || {}, t = def.t, hits = b.dmg !== undefined || b.poison !== undefined;
  switch (p.stat) {
    case 'might': case 'crit': case 'leech': return hits;
    case 'cooldown': return !(b.perm || t === 'wheel' || t === 'aura');
    case 'amount': return SYN_TYPES.amount.has(t) && !(t === 'zone' && (b.count || 1) <= 1);
    case 'area': return SYN_TYPES.area.has(t);
    case 'projspeed': return SYN_TYPES.projspeed.has(t) || (!!def.weapon && (t === 'melee' || t === 'slam'));   // (0.84: the area weapons' reach)
    case 'duration': return SYN_TYPES.duration.has(t) && !b.perm;
    case 'luck': return !!(b.gamble || b.allOrNothing || b.buff === 'fortune' || b.buff === 'pandora' || t === 'wheel');
    case 'regen': return t === 'heal';
    default: return false;
  }
}
function tipIcon(name, tip, size = 26) { const im = iconImg(name, size); im.title = tip; return im; }
function boostsOf(def) { return Game.C.passives.filter(p => statBoosts(p, def)); }
Object.assign(UI, {
  // ------------------------------------------------ the line under a level-up choice: what it works with (owned)
  synergyLine(R, o) {
    const C = Game.C; let items = [];
    if (o.kind === 'spell' || o.kind === 'weapon') {
      const def = o.kind === 'spell' ? C.spells[o.id] : weaponById(C, o.id);
      items = C.passives.filter(p => R.passives[p.id] && statBoosts(p, def)).map(p => ({ icon: p.icon, name: L(p.name) }));
    } else if (o.kind === 'passive') {
      const p = C.passives.find(x => x.id === o.id);
      items = R.spells.filter(s => statBoosts(p, s.def)).map(s => ({ icon: 'sp_' + s.def.icon, name: L(s.def.name) }));
      if (R.weapon && statBoosts(p, R.weapon.def)) items.push({ icon: R.weapon.icon, name: L(R.weapon.def.name) });
    }
    if (!items.length) return null;
    return h('div', { class: 'up-syn', title: items.map(i => i.name).join(', ') }, h('span', {}, '⇄'), ...items.slice(0, 6).map(i => iconImg(i.icon, 18)), items.length > 6 ? h('small', {}, '+' + (items.length - 6)) : null);
  },
  // ------------------------------------------------ the Armurerie
  armory(tab, sel) {
    this.clear(); document.body.classList.add('menu-bg'); this.screen = 'armory';
    if (typeof Nav !== 'undefined') Nav.forget('armory');
    const C = Game.C, S = Store.data, body = h('div', { class: 'arm-body' }), tabs = h('div', { class: 'tabs' });
    const TABS = [['weapons', T('arm_weapons')], ['sfusions', T('arm_sfusions')], ['stats', T('arm_stats')], ['ttg', T('classeur')], ['tmaps', T('arm_tmaps')], ['souls', T('souls')], ['relics', T('relics')]];   // (0.94: every relic)
    const go = (k, sel) => { tabs.querySelectorAll('.btn').forEach(b => b.classList.toggle('active', b.dataset.k === k)); body.innerHTML = ''; this.previews = []; this['arm_' + k](body, sel); };
    for (const [k, name] of TABS) { const b = btn(name, () => go(k)); b.dataset.k = k; tabs.append(b); }
    this.rootEl.append(h('div', { class: 'screen armory' }, this.panel(T('armory'), tabs, body)));
    go(tab || 'weapons', sel);
  },
  // weapons: the 8 types, each with its two unique weapons and its vampiric weapons (0.48: every weapon shown, found or
  // not); the detail shows a character attacking with it
  arm_weapons(body) {
    const C = Game.C, S = Store.data, list = h('div', { class: 'arm-list' }), detail = h('div', { class: 'arm-detail' });
    // 0.60: the preview starts on the Iop, ◀ ▶ go through every class that holds weapons (as in the shop)
    const CL = C.classes.filter(c => SPR.chars[c.sprites[0] + '_x']);
    let cls = CL.find(c => c.id === S.lastClass) || CL.find(c => c.id === 'iop') || CL[0], sex = CL.find(c => c.id === S.lastClass) ? (S.lastSex || 0) : 0, curCard = null;   // (0.92: the last class played)
    const pk = Math.max(1, (window.devicePixelRatio || 1) * (Game._uiz || 1)), cv = h('canvas', { class: 'arm-prev', width: Math.round(220 * pk), height: Math.round(220 * pk) });
    let sprite = null, cur = null, t = 0;
    const clsName = h('span', { class: 'pcls' }, L(cls.name)), sexBtn = btn('', () => { sex = 1 - sex; setSex(); if (cur) show(cur, curCard); });
    const setSex = () => { sexBtn.textContent = sex ? '♀ ' + T('female') : '♂ ' + T('male'); sexBtn.style.visibility = cls.sprites[0] === cls.sprites[1] ? 'hidden' : 'visible'; };
    const stepCls = d => { cls = CL[(CL.indexOf(cls) + d + CL.length) % CL.length]; if (cls.sprites[0] === cls.sprites[1]) sex = 0; clsName.textContent = L(cls.name); setSex(); if (cur) show(cur, curCard); };
    const prevRow = h('div', { class: 'prev-opts arm-prev-opts' }, h('div', { class: 'prev-row' }, btn('◀', () => stepCls(-1), 'arrow'), clsName, btn('▶', () => stepCls(1), 'arrow')), h('div', { class: 'prev-row' }, sexBtn));
    setSex();
    const show = async (w, card) => {
      curCard = card;
      list.querySelectorAll('.arm-card').forEach(e => e.classList.toggle('sel', e === card)); cur = w; t = 0;
      const p = spellParams(w, MAX_SPELL_LV), evo = (C.weaponEvo || {})[w.id] || [], found = (S.uniques || {})[w.id] || 0, ml = (S.mastery || {})[w.of || w.id] || 0;
      const row = (k, v, kind = 'prop') => h('tr', {}, h('td', {}, k), h('td', { class: 'fx-' + kind }, v));   // (0.98: the value in the effect colours)
      detail.innerHTML = '';
      detail.append(h('h2', {}, iconImg(w.icon, 40), ' ', L(w.name), w.blood ? h('span', { class: 'tag blood' }, T('blood_tag')) : null),
        h('div', { class: 'arm-top' }, h('div', { class: 'arm-prev-box' }, cv, prevRow), h('div', {}, h('p', { class: 'fx-desc' }, L(w.desc)),
          h('table', { class: 'stats' },
            row(T('p_dmg'), Math.round(p.dmg) + (p.count > 1 ? ' ×' + p.count : ''), 'eff'), row(T('p_cd'), p.cd + ' s'),
            p.range ? row(T('p_range'), p.range) : null, p.radius ? row(T('p_radius'), p.radius) : null,
            w.leech ? row(T('p_leech'), pctLeech(w.leech[0]) + ' → ' + pctLeech(w.leech[w.leech.length - 1]), 'eff') : null,

            row(T('mastery'), L(w.masteryName) + ' +' + Math.round(ml * (C.masteryPer || 0.1) * 100) + ' %', 'eff'), w.unique ? row(T('arm_found'), found ? '×' + found : T('arm_notyet'), found ? 'prop' : 'cond') : null))),
        evo.length ? h('h3', {}, T('arm_finales')) : '',   // (0.60: '' — append(null) wrote 'null' under the preview)
        h('div', { class: 'arm-evos' }, ...evo.map(e => h('div', { class: 'arm-evo' }, iconImg(e.icon || w.icon, 26), h('div', {}, h('b', {}, L(e.name) + (e.skinName ? ' — ' + L(e.skinName) : '')), h('div', { class: 'desc fx-desc' }, L(e.desc)))))),
        h('h3', {}, T('arm_boosted')), h('div', { class: 'arm-syn' }, ...boostsOf(w).map(pp => h('span', { class: 'chip', title: L(pp.desc) }, iconImg(pp.icon, 20), L(pp.name)))));
      const sp = UI.own(new CharSprite(cls.sprites[sex], (S.colors && S.colors[cls.id]) || baseColors(cls, sex), null, null, null)); sp.weapon = w.acc || null; sprite = UI.drop(sprite); await sp.load(); if (cur === w) { UI.drop(sprite); sprite = sp; } else UI.drop(sp);   // (0.93: UI.own)
    };
    for (const base of C.weapons) {
      const U = (C.uniqueWeapons || []).filter(u => u.of === base.id), group = [...U.filter(u => !u.blood), ...U.filter(u => u.blood)];   // (0.60: no Boisaille any more)
      list.append(h('div', { class: 'sep' }, L(base.name)));
      for (const w of group) {
        const card = h('div', { class: 'arm-card' + (w.blood ? ' blood' : ''), onclick: () => { Audio2.blip('click'); show(w, card); } }, iconImg(w.icon, 44), h('div', { class: 'bname' }, L(w.name)));
        list.append(card);
      }
    }
    body.append(h('div', { class: 'best-layout' }, list, detail));
    const first = list.querySelector('.arm-card'); if (first) first.click();
    this.previews.push((dt) => {   // the attack in a loop, a short pause between two blows
      t += dt; const g = cv.getContext('2d'); g.setTransform(pk, 0, 0, pk, 0, 0); g.clearRect(0, 0, 220, 220); if (!sprite || !cur) return;
      const a = (cur.anim || 'anim1') + 'R', dur = sprite.duration(a) || 0.8, cyc = dur + 0.6, lt = t % cyc;
      g.imageSmoothingQuality = 'high'; sprite.draw(g, lt < dur && sprite.has(a) ? a : 'staticR', lt < dur ? lt : t, 104, 206, 3.5, false, { loop: lt >= dur, at: t });
    });
  },
  // characteristics: each one, what it does, and every spell / weapon it helps (by class)
  arm_stats(body) {
    const C = Game.C, wrap = h('div', { class: 'arm-stats' }), alone = [];
    for (const p of C.passives) {
      const byCls = C.classes.map(c => [c, c.spells.map(s => C.spells[s]).filter(d => d && statBoosts(p, d))]).filter(([, l]) => l.length);
      const glob = (C.globalSpells || []).map(g => C.spells[g.id]).filter(d => statBoosts(p, d)), weap = C.weapons.filter(w => statBoosts(p, w));
      const head = h('div', { class: 'arm-stat-head' }, iconImg(p.icon, 40), h('div', {}, h('b', {}, L(p.name)), h('div', { class: 'desc fx-eff' }, L(p.desc)), h('small', {}, T('arm_max', { n: p.max }))));
      if (!(byCls.length || glob.length || weap.length)) { alone.push(head); continue; }   // (0.34: grouped in one box below)
      wrap.append(h('div', { class: 'arm-stat' }, head,
        h('div', { class: 'arm-stat-list' },
          ...byCls.map(([c, l]) => h('span', { class: 'arm-cls', title: L(c.name) }, h('i', { style: { background: c.color } }), ...l.map(d => tipIcon('sp_' + d.icon, L(d.name))))),
          glob.length ? h('span', { class: 'arm-cls', title: T('g_spell') }, h('i', { style: { background: '#9a96b0' } }), ...glob.map(d => tipIcon('sp_' + d.icon, L(d.name)))) : null,
          weap.length ? h('span', { class: 'arm-cls', title: T('arm_weapons') }, h('i', { style: { background: '#b0702a' } }), ...weap.map(w => tipIcon(w.icon, L(w.name)))) : null)));
    }
    if (alone.length) {   // 0.38: in two boxes of the same size (one tall box was cut between two columns)
      const half = Math.ceil(alone.length / 2);
      wrap.append(h('div', { class: 'arm-stat wide alone' }, h('div', { class: 'desc arm-alone-t' }, T('arm_nospell')), h('div', { class: 'arm-alone' }, ...alone.slice(0, half))));
      if (alone.length > half) wrap.append(h('div', { class: 'arm-stat wide alone' }, h('div', { class: 'arm-alone' }, ...alone.slice(half))));
    }
    // 0.38: the columns run sideways: the mouse wheel scrolls them left / right
    wrap.addEventListener('wheel', (e) => { if (wrap.scrollWidth > wrap.clientWidth + 2 && !e.shiftKey) { wrap.scrollLeft += e.deltaY || e.deltaX; e.preventDefault(); } }, { passive: false });
    body.append(wrap);
  },
  // the TTG binder: every card, how many times it was found
  arm_ttg(body) {
    const C = Game.C, S = Store.data, cards = (C.ttg && C.ttg.cards) || [], got = S.ttg || {};
    if (!cards.length) { body.append(h('div', { class: 'hint arm-empty' }, T('ttg_empty'))); return; }
    const n = cards.filter(c => got[c.id]).length;
    body.append(h('div', { class: 'sub' }, `${n} / ${cards.length}`),
      h('div', { class: 'ttg-grid' }, ...cards.map(c => h('div', { class: 'ttg-slot' + (got[c.id] ? '' : ' missing') },
        got[c.id] ? ttgCard(c) : h('div', { class: 'ttg-c empty' }, h('span', {}, '?')), got[c.id] ? h('b', { class: 'ttg-nm' }, L(c.name)) : null, h('div', { class: 'ttg-no' }, 'No.' + c.id), got[c.id] > 1 ? h('i', {}, '×' + got[c.id]) : null))));
  },
  // treasure maps (0.47: one treasure per zone): each zone's map with its cross, dug up or not, or still unknown
  arm_tmaps(body) {
    if (Run.prototype.tmapFix) Run.prototype.tmapFix.call({ C: Game.C, map: {}, tmapSpot: Run.prototype.tmapSpot });   // (0.51: crosses outside a zone made smaller)
    const C = Game.C, S = Store.data, tm = S.tmaps || {}, ids = (C.tmap.maps || Object.keys(tm)).filter(id => C.maps.some(m => m.id === id));
    const dug = ids.filter(id => tm[id] && tm[id].found).length, pk = Math.min(3, (window.devicePixelRatio || 1) * (Game._uiz || 1));
    body.append(h('div', { class: 'sub' }, T('tmap_count', { n: dug, t: ids.length })), h('div', { class: 'hint' }, Object.keys(tm).length ? T('tmap_hint') : T('tmap_none')));
    const grid = h('div', { class: 'tmap-grid' });
    for (const id of ids) {
      const m = C.maps.find(x => x.id === id), e = tm[id], W = SPR.worlds[m.world]; if (!W) continue;
      const cv = document.createElement('canvas'); cv.width = Math.round(320 * pk); cv.height = Math.round(210 * pk); cv.className = 'tmap-mini' + (e ? '' : ' unknown');
      const g = cv.getContext('2d'), s = Math.min(320 / W.w, 210 / W.h), ox = (320 - W.w * s) / 2, oy = (210 - W.h * s) / 2;
      g.setTransform(pk, 0, 0, pk, 0, 0); g.fillStyle = '#d8c39a'; g.fillRect(0, 0, 320, 210);
      if (e) Assets.loadImg(`assets/worlds/${m.world}_mini.webp`).then(im => {
        if (im) { g.globalAlpha = 0.85; g.drawImage(im, ox, oy, W.w * s, W.h * s); g.globalAlpha = 1; }
        const x = ox + e.x * s, y = oy + e.y * s; g.lineCap = 'round'; g.strokeStyle = '#4a0a00'; g.lineWidth = 9; g.beginPath(); g.moveTo(x - 10, y - 10); g.lineTo(x + 10, y + 10); g.moveTo(x + 10, y - 10); g.lineTo(x - 10, y + 10); g.stroke(); g.strokeStyle = e.found ? '#8a8a8a' : '#e0201a'; g.lineWidth = 5; g.stroke();
      });
      else { g.fillStyle = 'rgba(74,52,30,.55)'; g.font = 'bold 90px DofusBold, Verdana'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText('?', 160, 110); }
      grid.append(h('div', { class: 'tmap-card' + (e && e.found ? ' found' : '') + (e ? '' : ' unknown'), onclick: e ? () => { Audio2.blip('click'); this.mushaScene(null, e, m); } : null }, cv, h('b', {}, tmapZoneName(m)),   // (0.48: Musha's scene again)
        h('small', {}, e ? (e.found ? T('tmap_done') + ' (+' + ((C.tmap.prize || {})[id] || C.tmap.kamas) + ' K)' : T('tmap_todo')) : T('tmap_unknown'))));
    }
    body.append(grid);
  },
  // Archimonster souls
  // 0.60: the spell fusions, class by class (the last class played first): recipe, result, what it does; made ones glow
  arm_sfusions(body, sel) {
    // 0.68: the rows take the controller / keyboard focus, and the picked one is cast on the right by its class
    // (the shop's spell preview), with its recipe and what it does
    const C = Game.C, S = Store.data, done = Prog.st().sfDone || {}, list = h('div', { class: 'sf-list' }), detail = h('div', { class: 'arm-detail sf-detail' });
    let cur = C.classes.find(c => c.id === sel) || C.classes[0], pick = null, sprite = null, t = 0;   // (0.92: the first class — the Féca — unless one is asked)
    const pk = Math.max(1, (window.devicePixelRatio || 1) * (Game._uiz || 1)), cv = h('canvas', { class: 'arm-prev', width: Math.round(220 * pk), height: Math.round(220 * pk) });
    const sub = h('div', { class: 'tabs subtabs' });
    const loadSprite = async () => { const c = cur, sp = UI.own(new CharSprite(c.sprites[0], (S.colors && S.colors[c.id]) || baseColors(c, 0), null, null, null)); sprite = UI.drop(sprite); await sp.load(); if (c === cur) { UI.drop(sprite); sprite = sp; } else UI.drop(sp); };   // (0.93: UI.own)
    const showOne = (f, row) => {
      if (!f || pick === f) return; pick = f; t = 0; list.querySelectorAll('.sf-row').forEach(e => e.classList.toggle('sel', e === row));
      const sp = C.spells[f.id], kind = f.kind === 'weapon' ? T('weapon_tag') : f.kind === 'global' ? T('g_spell') : T('spells'); spellPreviewLoad(sp);
      const rec = sfRecipe(null, f, 34); rec.forEach(e => { if (e.tagName === 'B') e.className = 'sf-plus'; });
      detail.innerHTML = '';
      detail.append(h('h2', {}, iconImg('sp_' + sp.icon, 40), ' ', L(sp.name), done[f.id] ? ' ✔' : null),
        h('div', { class: 'arm-top' }, h('div', { class: 'arm-prev-box' }, cv, h('div', { class: 'prev-row' }, h('span', { class: 'pcls' }, L(cur.name)))),
          h('div', {}, h('span', { class: 'sf-kind' }, kind), h('p', { class: 'fx-desc' }, L(sp.desc)), sfStats(f, cur), h('div', { class: 'sf-rec' }, ...rec),   // (0.96: its damage and cooldown)
            h('small', null, fxDesc(f.kind === 'weapon' ? T('sfusion_need_w') : T('sfusion_need'), 'cond'), ' — ', fxDesc(f.kind === 'weapon' ? T('sfusion_keep') : T('sfusion_slot'), 'spec')))));   // (0.98: the condition red, what it frees blue)
    };
    const show = () => {
      sub.querySelectorAll('.btn').forEach(b => b.classList.toggle('active', b.dataset.c === cur.id)); list.innerHTML = ''; pick = null; loadSprite();
      for (const f of (C.spellFusions || []).filter(x => sfusionOf(x, cur.id))) {   // (0.95: the class-less ones under every class)
        const sp = C.spells[f.id];
        const row = h('div', { class: 'sf-row' + (done[f.id] ? ' done' : ''), tabindex: 0, onclick: () => { Audio2.blip('click'); showOne(f, row); } },
          h('div', { class: 'sf-txt' }, h('b', null, iconImg('sp_' + sp.icon, 40), ' ', L(sp.name), done[f.id] ? ' ✔' : null)));
        row.addEventListener('mouseenter', () => showOne(f, row)); row.addEventListener('focus', () => showOne(f, row));
        list.append(row);
      }
      const first = list.querySelector('.sf-row'); if (first) first.click();
    };
    const onNav = (e) => { if (!list.isConnected) { document.removeEventListener('navfocus', onNav); return; } const r = e.target.closest && e.target.closest('.sf-row'); if (r) r.click(); };
    UI.listen(document, 'navfocus', onNav);
    for (const c of C.classes) { const b = btn([artImg(c.emblemArt || ('b' + c.breed), 'subic', 64), h('span', {}, L(c.name))], () => { cur = c; show(); }); b.dataset.c = c.id; sub.append(b); }
    body.append(h('div', { class: 'mastery-intro' }, T('sfusion_hint')), sub, h('div', { class: 'best-layout sf-layout' }, list, detail)); show();
    this.previews.push((dt) => {   // the class casts the fusion in a loop
      t += dt; const g = cv.getContext('2d'); g.setTransform(pk, 0, 0, pk, 0, 0); g.clearRect(0, 0, 220, 220); if (!sprite || !pick) return;
      g.imageSmoothingQuality = 'high'; drawSpellPreview(g, sprite, cur, C.spells[pick.id], t);
    });
  },
  // 0.94: every relic of the game (C.relics), found or not: picture, name, what it does; the ones found in a run
  // (Store.data.relics, extras.js) lit up with how many times (the achievements' cards and the souls' scrolling grid)
  arm_relics(body) {
    const C = Game.C, got = Store.data.relics || {}, all = C.relics || [], n = all.filter(r => got[r.id]).length;
    body.append(h('div', { class: 'sub' }, `${n} / ${all.length}`),
      h('div', { class: 'soul-grid relic-grid' }, ...all.map(r => h('div', { class: 'ach-card' + (got[r.id] ? ' done' : ''), tabindex: 0 },
        h('div', { class: 'ach-ic' }, iconImg(r.icon, 40)),
        h('div', { class: 'ach-txt' }, h('div', { class: 'ach-name' }, L(r.name)), h('div', { class: 'ach-desc' }, L(r.desc)),
          got[r.id] ? h('div', { class: 'ach-date' }, '✔ ×' + got[r.id]) : null)))));
  },
  arm_souls(body) {
    const C = Game.C, S = Store.data, souls = S.souls || {}, all = [];
    for (const mid in C.archi || {}) for (const a of C.archi[mid]) all.push(Object.assign({ mob: C.monsters[mid] }, a));
    all.sort((a, b) => (a.lv || 0) - (b.lv || 0) || a.id - b.id);   // (0.35: weakest first, by their level in Dofus)
    const n = all.filter(a => souls[String(a.id)]).length;
    body.append(h('div', { class: 'sub' }, `${n} / ${all.length}`),
      h('div', { class: 'soul-grid' }, ...all.map(a => { const k = souls[String(a.id)]; return h('div', { class: 'soul' + (k ? '' : ' missing'), title: k ? L(a.name) : '???', tabindex: 0, onclick: () => { if (k) toast(L(a.name) + ' — ' + T('lvl_short') + ' ' + a.lv); } }, h('div', { class: 'soul-pic' }, artImg(a.mob ? (a.mob.art || 'a' + a.mob.gfx) : '', '', 160)), h('small', {}, k ? L(a.name) : '???'), k > 1 ? h('i', {}, '×' + k) : null); })));
  },
});

// ---------------------------------------------------------------- 0.30: the shop's spell preview: the class casts the
// spell in a loop (1 s between two casts), with the spell's client effect, everything inside the preview box
const PREV_SELF = new Set(['heal', 'buff', 'aura', 'pulse', 'orbit', 'pioche', 'wheel']);
const PREV_SHOT = new Set(['projectile', 'line', 'beam', 'toss', 'bomb', 'detonate']);
// (0.60: a summon drawn with a character sprite, '<sid>_c' like the Brigandin's Mama: the HD CharSprite, as in the game)
const PREV_CHARS = {};
function prevChar(sk, colors) { const m = /^(\d+)_c$/.exec(sk || ''); if (!m || !SPR.chars[m[1]]) return null; if (!PREV_CHARS[m[1]]) { const cs = PREV_CHARS[m[1]] = new CharSprite(+m[1], colors || [[196, 150, 96], [120, 84, 52], [150, 40, 40]], null, null, null); cs.load(); } else if (colors && PREV_CHARS[m[1]].ready && PREV_CHARS[m[1]].colors !== colors) PREV_CHARS[m[1]].recolor(colors); return PREV_CHARS[m[1]]; }
function spellPreviewLoad(def) {
  for (const f of (def && def.fx) || []) FxSheets.load(f);
  const keys = [def && def.base && def.base.spriteKey, ...Object.values((def && def.spriteKeyBy) || {})].filter(Boolean);   // (the Mama: the Brigandin's other sprite)
  for (const sk of keys) { if (SPR.mobs[sk]) MobSheets.load(sk); else prevChar(sk); }
}
function drawSpellPreview(g, sprite, cls, def, t, W = 220, H = 220) {
  const k = 2.3, cx = W * 0.27, cy = H * 0.9, fk = k / ES;
  const anim = ((def.animBy && def.animBy[sprite.sid]) || def.anim || def.animAll || cls.casts[0] || 'anim1') + 'R';
  const has = sprite.has(anim), dur = has ? sprite.duration(anim) || 0.8 : 0.6;
  const fx = FxSheets.get(def.fx && def.fx[0]), syms = fx ? Object.keys(fx.anims) : [];
  const sym = syms.includes('shoot') ? 'shoot' : syms.includes('root') ? 'root' : syms[syms.length - 1];
  const fxDur = fx && sym ? Math.min(1.6, fx.duration(sym)) : 0.5, self = PREV_SELF.has(def.t), shot = PREV_SHOT.has(def.t);
  const near = def.t === 'melee' || def.t === 'cone' || def.t === 'dash' || def.t === 'leap', travel = shot ? 0.45 : 0;
  // (0.34: what stays after the cast is shown too: summons, the Double, traps, zones; half the old pause between casts)
  const B = def.base || {}, stays = def.t === 'summon' || def.t === 'trap' || def.t === 'zone' || def.t === 'pwcawotte';
  const t0 = dur * 0.45, cyc = Math.max(dur, t0 + travel + fxDur, stays ? t0 + 1.8 : 0) + 0.5, lt = t % cyc;
  const tx = self ? cx : near ? W * 0.58 : W * 0.78, ty = self ? cy - 4 : cy - 8;
  g.save(); g.beginPath(); g.rect(0, 0, W, H); g.clip();
  // the target: a little shadow on the ground where the spell lands
  if (!self) { g.fillStyle = 'rgba(0,0,0,0.22)'; g.beginPath(); g.ellipse(tx, ty, 22, 9, 0, 0, TAU); g.fill(); }
  sprite.draw(g, lt < dur && has ? anim : 'staticR', lt < dur ? lt : t, cx, cy, k, false, { loop: !(lt < dur), at: t });
  const e = lt - t0;
  if (e >= 0 && shot && e < travel) {   // the projectile on its way
    const q = e / travel, x = cx + 18 + (tx - cx - 18) * q, y = cy - 52 + (ty - 20 - cy + 52) * q - Math.sin(q * Math.PI) * (def.t === 'toss' || def.t === 'bomb' ? 50 : 6);
    if (def.t === 'bomb' && typeof bombBody === 'function') bombBody(g, x, y, 9, BOMB_COLS[def.id] || BOMB_COLS.explobombe, q * 5, t, true);   // (0.68: the Roublard's bombs, they showed as a dot)
    else if (fx && fx.anims.move) { const f = fx.anims.move.f[Math.floor(e * fx.anims.move.fps) % fx.anims.move.f.length]; g.save(); g.translate(x, y); g.rotate(Math.atan2(ty - cy + 32, tx - cx)); fx.draw(g, f, 0, 0, fk * 0.8, false); g.restore(); }
    else { const c = (def.base && def.base.color) || cls.color || '#ffd24a'; g.drawImage(RCache.glow(c), x - 14, y - 14, 28, 28); g.fillStyle = '#fff'; g.beginPath(); g.arc(x, y, 4, 0, TAU); g.fill(); }
  }
  if (e >= 0 && stays) {
    const a = Math.min(1, e / 0.25) * Math.min(1, (cyc - 0.5 - t0 - e) / 0.3 + 0.2);
    g.save(); g.globalAlpha = Math.max(0, a);
    if (def.t === 'summon') {
      const sk = (def.spriteKeyBy && def.spriteKeyBy[sprite.sid]) || B.spriteKey, sh = sk && MobSheets.c[sk], pc = !sh && prevChar(sk, sprite.colors);
      if (B.decoy) { g.globalAlpha *= 0.6; sprite.draw(g, 'staticR', t, tx, ty + 4, k, true, { loop: true, at: t }); }
      else if (pc && pc.ready) pc.draw(g, pc.has('runR') ? 'runR' : 'staticR', e, tx, ty + 4, k * 0.95, true, { loop: true, at: t });
      else if (sh) { const an = sh.has('walkL') ? 'walkL' : sh.has('walkR') ? 'walkR' : Object.keys(sh.anims)[0]; sh.draw(g, sh.frameAt(an, e, true), tx, ty + 4, k * 0.9, an === 'walkR'); }
    } else if (def.t === 'trap') { g.translate(tx, ty); g.scale(fk, fk); drawTrapCone(g, 0, 0, t, def.id === 'fu_sram_piege' ? TRAP_POISON : null); }
    else if (B.cloud) { g.translate(cx, cy - 6); g.scale(fk * 0.75, fk * 0.75); drawCloud(g, { x: 0, y: 0, r: B.radius || 80, fart: B.fart, born: t - e, puff: B.puff, rim: B.rim, caw: B.cawN }, Math.max(0, a), t); }
    else drawArea(g, tx, ty, (B.radius || 60) * fk * 0.6, B.color || '#ffcc33', 0.75 * a);
    g.restore();
  }
  const ef = e - travel;
  if (def.t === 'bomb' && ef >= 0 && ef < 0.35 && typeof bombBody === 'function') bombBody(g, tx, ty - 9, 9 * (1 + 0.15 * Math.sin(ef * 40)), BOMB_COLS[def.id] || BOMB_COLS.explobombe, 0, t, true);   // (the fuse, then the blast)
  if (ef >= 0.35 * (def.t === 'bomb') && ef < fxDur) {
    if (fx && sym) { const an = fx.anims[sym], f = an.f[Math.min(an.f.length - 1, Math.floor(ef * an.fps))]; fx.draw(g, f, tx, ty - (self ? 30 : 10), fk * (self ? 0.55 : 0.7), false); }
    else { const q = ef / fxDur; g.globalAlpha = 1 - q; g.strokeStyle = (def.base && def.base.color) || '#ffd24a'; g.lineWidth = 3; g.beginPath(); g.ellipse(tx, ty, 10 + 40 * q, (10 + 40 * q) * 0.45, 0, 0, TAU); g.stroke(); g.globalAlpha = 1; }
  }
  g.restore();
}

// ---------------------------------------------------------------- 0.30: the character's three colours (hair / outfit
// / accents), chosen on a palette like the client's character creation (buttons, so the controller reaches them too)
const PALETTE = (() => { const out = []; for (const l of [0.22, 0.38, 0.55, 0.72]) for (let i = 0; i < 12; i++) out.push(hsl2rgb(i * 30, l > 0.7 ? 0.6 : 0.7, l)); for (const l of [0.1, 0.3, 0.5, 0.7, 0.85, 0.97]) out.push(hsl2rgb(0, 0, l)); return out; })();
const rgbCss = c => `rgb(${c[0]},${c[1]},${c[2]})`;
UI.colorRow = function (get, set, base) {   // (0.91: base = the class's own colours, the ↺ button)
  // 0.34: the palette is a floating panel placed on the page (fixed, kept inside the screen): a window's edge or a
  // scrolling list can't cut it any more, every colour can be reached with the mouse and the controller
  const row = h('div', { class: 'color-row' }), pal = h('div', { class: 'cpal float hidden' });
  let zone = -1, anchor = null;
  // (0.92: closing — B, Échap, ✔ — puts the cursor back on the swatch of the colour just chosen; draw() rebuilds the row)
  const close = () => { if (UI._palClose === close) UI._palClose = null; const z = zone, wasIn = typeof Nav !== 'undefined' && !!Nav.el && pal.contains(Nav.el); zone = -1; pal.classList.add('hidden'); if (pal.parentNode) pal.remove(); draw(); const s = z >= 0 && row.children[z]; if (s && s.isConnected && wasIn) Nav.set(s); };
  const place = () => {
    const host = UI.rootEl || document.body; if (pal.parentNode !== host) host.append(pal);
    pal.classList.remove('hidden'); pal.style.left = '0px'; pal.style.top = '0px';
    const p0 = pal.getBoundingClientRect(), k = p0.width / (pal.offsetWidth || 1) || 1;   // (the menus' zoom, as the page sees it)
    const a = anchor.getBoundingClientRect(), pw = p0.width, ph = p0.height, m = 8;
    let x = a.left + a.width / 2 - pw / 2, y = a.bottom + 6;
    if (y + ph > innerHeight - m) y = a.top - ph - 6;
    x = clamp(x, m, innerWidth - pw - m); y = clamp(y, m, innerHeight - ph - m);
    pal.style.left = (x - p0.left) / k + 'px'; pal.style.top = (y - p0.top) / k + 'px';
  };
  const draw = () => {
    row.innerHTML = ''; const cols = get();
    ['col_hair', 'col_outfit', 'col_accent'].forEach((key, i) => {
      const b = btn(h('i', { style: { background: rgbCss(cols[i]) } }), () => {
        if (zone === i) { close(); return; }
        zone = i; draw(); anchor = row.children[i]; place(); UI._palClose = close;   // 0.37: B / Échap close the palette only
        const f = pal.querySelector('.btn'); if (f && Nav.enabled) Nav.set(f);
      }, 'swatch' + (zone === i ? ' active' : ''));
      b.title = T(key); b.setAttribute('data-nav', 'col:' + i); row.append(b);
    });
    row.append(btn('🎲', () => { set(randomColors()); close(); draw(); }, 'swatch dice'));
    if (base) { const r = btn('↺', () => { set(base()); close(); draw(); }, 'swatch reset'); r.title = T('col_reset'); row.append(r); }
  };
  PALETTE.forEach((c, j) => { const b = btn(h('i', { style: { background: rgbCss(c) } }), () => { if (zone < 0) return; const cols = get().slice(); cols[zone] = c; set(cols); Audio2.blip('click'); const z = zone; draw(); zone = z; }, 'pcol'); b.setAttribute('data-nav', 'pal:' + j); pal.append(b); });
  pal.append(btn('✔', () => close(), 'pcol ok'));
  const outside = (e) => { if (!row.isConnected) { document.removeEventListener('pointerdown', outside, true); pal.remove(); return; } if (zone >= 0 && !pal.contains(e.target) && !row.contains(e.target)) close(); };
  UI.listen(document, 'pointerdown', outside, true); UI.onClear(() => pal.remove());   // (0.93: the floating palette with its screen)
  draw();
  const box = h('div', { class: 'color-pick' }, row); box.redraw = draw;   // (0.91: the shop's class arrows / tabs show the new class's colours)
  return box;
};
