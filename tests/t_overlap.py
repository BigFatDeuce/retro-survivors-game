# 0.94 (on phones, held upright or sideways, many things overlap in many places): every menu, tab, sub-tab and
# window at the window size of the run (VW x VH, MOBILE=1 for a phone): the visible pieces of content — each text (the
# box of its letters, not of its element), picture, field — that lie over one another, as the player sees them (cut by
# the lists that scroll and by the screen). Two pieces count when their overlap is at least 30 px2 and 12 % of the
# smaller one; a piece inside another (an icon in its button) is not compared with that one. Also the texts cut by
# their box without the '…' of a cut-tip. Prints PROB lines, then SUMMARY; screenshots <state>.png with the overlapping
# pieces outlined in red (and blue for a cut text).
# usage: VW=390 VH=844 DPR=3 MOBILE=1 python tools/checks/pw_test.py tests/t_overlap.py <out>   (tools/qa.py: 3 phones x 2 ways)
import json
url('fresh=1')
pg.wait_for_function("typeof Game !== 'undefined' && Game.state === 'menu'", timeout=120000); time.sleep(1.5)
pg.evaluate("""(() => { const S = Store.data, C = Game.C; S.kamas = 999999; S.unlocked = C.maps.map(m => m.id); S.seen = S.seen || {};
  for (const id in C.monsters) S.seen[id] = 1; for (const id in C.bosses) S.seen[id] = 1; Store.save(); })()""")
PROBE = r"""(async () => {
  const root = (UI.modal && UI.modal.isConnected) ? UI.modal : document.getElementById('ui'), W = innerWidth, H = innerHeight;
  const shown = e => { for (let p = e; p && p !== document.body; p = p.parentElement) { const cs = getComputedStyle(p); if (cs.display === 'none' || cs.visibility === 'hidden' || +cs.opacity < 0.05) return false; } return true; };
  const clipOf = (e, self) => { let r = { l: 0, t: 0, r: W, b: H }; for (let p = self ? e : e.parentElement; p && p !== document.body; p = p.parentElement) { const cs = getComputedStyle(p);
      if (cs.overflowX !== 'visible' || cs.overflowY !== 'visible') { const q = p.getBoundingClientRect(); r = { l: Math.max(r.l, q.left), t: Math.max(r.t, q.top), r: Math.min(r.r, q.right), b: Math.min(r.b, q.bottom) }; } } return r; };
  const cut = (a, c) => ({ l: Math.max(a.l, c.l), t: Math.max(a.t, c.t), r: Math.min(a.r, c.r), b: Math.min(a.b, c.b) });
  const area = a => Math.max(0, a.r - a.l) * Math.max(0, a.b - a.t);
  const name = e => { const c = (e.className && e.className.baseVal !== undefined ? e.className.baseVal : e.className) || ''; const t = (e.textContent || e.alt || '').trim().replace(/\s+/g, ' ').slice(0, 22);
    const pc = e.parentElement && e.parentElement.className && typeof e.parentElement.className === 'string' ? e.parentElement.className.split(' ')[0] : '';
    return e.tagName.toLowerCase() + (c ? '.' + String(c).split(' ').filter(x => x && x !== 'navfocus').slice(0, 2).join('.') : pc ? ' in .' + pc : '') + (t ? ' "' + t + '"' : ''); };
  const atoms = [];
  const walk = (e) => {
    for (const ch of e.children) {
      if (!shown(ch)) continue;
      const tag = ch.tagName;
      if (['IMG', 'SVG', 'CANVAS', 'INPUT', 'SELECT', 'VIDEO'].includes(tag) || tag.toLowerCase() === 'svg') {
        const b = ch.getBoundingClientRect(); if (b.width >= 3 && b.height >= 3) atoms.push({ e: ch, r: { l: b.left + 1, t: b.top + 1, r: b.right - 1, b: b.bottom - 1 }, text: false });
        continue;
      }
      walk(ch);
    }
    // the letters of this element's own text
    let u = null;
    for (const n of e.childNodes) if (n.nodeType === 3 && n.textContent.trim()) { const rg = document.createRange(); rg.selectNodeContents(n);
      for (const q of rg.getClientRects()) { if (q.width < 1) continue; u = u ? { l: Math.min(u.l, q.left), t: Math.min(u.t, q.top), r: Math.max(u.r, q.right), b: Math.max(u.b, q.bottom) } : { l: q.left, t: q.top, r: q.right, b: q.bottom }; } }
    if (u) { const fs = parseFloat(getComputedStyle(e).fontSize) || 12, pad = fs * 0.12; atoms.push({ e, r: { l: u.l + 1, t: u.t + pad, r: u.r - 1, b: u.b - pad }, text: true }); }
  };
  walk(root);
  const out = [], cuts = [];
  for (const a of atoms) { a.c = clipOf(a.e, a.text); a.v = cut(a.r, a.c); a.va = area(a.v); }   // (a text is cut by its own box too: the letters past an ellipsis do not show)
  // which of two pieces is drawn over the other where they meet, and is the lower one hidden there by a pinned / floating
  // opaque layer (a sticky bar, a pop-up: it is meant to cover what passes under it)? A gradient is not taken as opaque
  const opaque = e => { const cs = getComputedStyle(e), m = /rgba?\(([^)]+)\)/.exec(cs.backgroundColor), al = m ? (m[1].split(',')[3] === undefined ? 1 : +m[1].split(',')[3]) : 0; if (al > 0.9) return true;
    const g = cs.backgroundImage; return g && g !== 'none' && g.includes('gradient') && !/transparent|rgba\([^)]*,\s*0(\.\d+)?\)/.test(g); };   // (a gradient with no see-through stop is opaque)
  const pinned = e => { for (let p = e; p && p !== document.body; p = p.parentElement) { const ps = getComputedStyle(p).position; if (ps === 'sticky' || ps === 'fixed' || ps === 'absolute') return true; } return false; };
  const covered = (a, b, I) => { const st = document.elementsFromPoint((I.l + I.r) / 2, (I.t + I.b) / 2), ia = st.findIndex(e => a.e === e || a.e.contains(e)), ib = st.findIndex(e => b.e === e || b.e.contains(e));
    if (ia < 0 || ib < 0) return false; const lo = ia < ib ? b : a, i0 = Math.min(ia, ib), i1 = Math.max(ia, ib);
    for (const e of st.slice(i0 + 1, i1)) if (!e.contains(lo.e) && opaque(e) && pinned(e)) return true; return false; };
  // a picture's see-through parts are not there: the share of its opaque pixels where the other piece lies
  // (an inline drawing — the controls' keyboard, pad — is drawn once from its own markup to find where it really paints)
  const alphaC = new Map(); const raster = (src) => { const c = document.createElement('canvas'); c.width = c.height = 64; const g = c.getContext('2d'); try { g.drawImage(src, 0, 0, 64, 64); return g.getImageData(0, 0, 64, 64).data; } catch (x) { return 1; } };
  for (const a of atoms) if (a.e.tagName.toLowerCase() === 'svg' && area(a.r) > 4000) { try { const sv = a.e.cloneNode(true), b = a.e.getBoundingClientRect(); sv.setAttribute('width', Math.round(b.width)); sv.setAttribute('height', Math.round(b.height)); sv.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
    const im = new Image(); im.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(new XMLSerializer().serializeToString(sv)); await im.decode(); alphaC.set(a.e, raster(im)); } catch (x) { alphaC.set(a.e, 1); } }
  const solid = (a, I) => { const e = a.e; let d = alphaC.get(e); if (!d) { if (e.tagName !== 'IMG' || !e.complete || !e.naturalWidth) return 1; d = raster(e); alphaC.set(e, d); }
    if (d === 1) return 1; const b = e.getBoundingClientRect(); let n = 0, k = 0;
    for (let y = I.t; y < I.b; y += Math.max(1, (I.b - I.t) / 8)) for (let x = I.l; x < I.r; x += Math.max(1, (I.r - I.l) / 8)) { const u = Math.floor((x - b.left) / b.width * 64), v = Math.floor((y - b.top) / b.height * 64); if (u < 0 || v < 0 || u > 63 || v > 63) continue; n++; if (d[(v * 64 + u) * 4 + 3] > 40) k++; }
    return n ? k / n : 1; };
  const DESIGNED = '.pl-over, .qa-mark';
  // a window that floats over the menu when opened (the music menu, a list, the palette, a tip): meant to cover what is under it
  const FLOAT = '.music-pop, .sel-pop, .cpal.float, .cut-tip, .toast', fl = e => e.closest(FLOAT);   // (drawn over a picture on purpose: the controls screen's phone overlay)
  const vis = atoms.filter(a => a.va >= 6);
  for (let i = 0; i < vis.length; i++) for (let j = i + 1; j < vis.length; j++) {
    const a = vis[i], b = vis[j]; if (a.e.contains(b.e) || b.e.contains(a.e)) continue;
    const I = cut(a.v, b.v), x = area(I); if (x < 30 || x < 0.12 * Math.min(a.va, b.va)) continue;
    if (a.e.closest(DESIGNED) || b.e.closest(DESIGNED) || fl(a.e) !== fl(b.e) || covered(a, b, I) || solid(a, I) < 0.08 || solid(b, I) < 0.08) continue;
    out.push({ a: name(a.e), b: name(b.e), px: Math.round(x), k: Math.round(100 * x / Math.min(a.va, b.va)), ra: a.v, rb: b.v });
  }
  // a text cut by its box: part of its letters outside what shows, without an ellipsis
  for (const a of atoms) if (a.text && area(a.r) > 0 && a.va < area(a.r) * 0.9 && a.va > 0) { const cs = getComputedStyle(a.e); if (cs.textOverflow === 'ellipsis' || a.e.closest('.cut-tip')) continue;
    let p = a.e; while (p && p !== root && !(getComputedStyle(p).overflowY !== 'visible' && p.scrollHeight > p.clientHeight + 2)) p = p.parentElement;
    if (p && p !== root) continue;   // (in a list that scrolls: it shows when scrolled to)
    cuts.push({ a: name(a.e), k: Math.round(100 * a.va / area(a.r)), r: a.r }); }
  // a list squeezed to a strip: it has things to show but under 70 px to show them
  const squeezed = [...root.querySelectorAll('*')].filter(e => { const cs = getComputedStyle(e); if (!/(auto|scroll|hidden)/.test(cs.overflowY) || cs.display === 'none') return false; const b = e.getBoundingClientRect();
    return b.width > 120 && e.clientHeight > 0 && e.clientHeight < 70 && e.scrollHeight > e.clientHeight + 60 && e.children.length > 2; }).map(e => ({ a: name(e), h: e.clientHeight, sh: e.scrollHeight, r: (b => ({ l: b.left, t: b.top, r: b.right, b: b.bottom }))(e.getBoundingClientRect()) }));
  for (const q of squeezed) cuts.push({ a: 'squeezed list ' + q.a + ` (${q.h} of ${q.sh} px show)`, k: 0, r: q.r });
  return { overlaps: out.slice(0, 40), n: out.length, cuts: cuts.slice(0, 20), nc: cuts.length, atoms: atoms.length };
})()"""
MARK = """(o => { for (const d of document.querySelectorAll('.qa-mark')) d.remove();
  const box = (r, c) => { const d = document.createElement('div'); d.className = 'qa-mark'; Object.assign(d.style, { position: 'fixed', left: r.l + 'px', top: r.t + 'px', width: (r.r - r.l) + 'px', height: (r.b - r.t) + 'px', outline: '2px solid ' + c, zIndex: 99999, pointerEvents: 'none' }); document.body.append(d); };
  for (const p of o.overlaps) { box(p.ra, 'red'); box(p.rb, 'red'); } for (const c of o.cuts) box(c.r, '#29f'); })"""
probs, states = [], 0
seen_pairs = set()
def state(name):
    global states; states += 1
    time.sleep(0.45)
    # (what is still arriving — the end screen's stamp, a window popping in — is judged once its animation ended, 4 s at most)
    try: pg.wait_for_function("document.getAnimations().every(a => a.playState !== 'running' || !isFinite(a.effect && a.effect.getComputedTiming().endTime))", timeout=4000)
    except Exception: pass
    o = pg.evaluate(PROBE)
    for p in o['overlaps']:
        key = (name.split(' tab')[0], p['a'], p['b'])
        if key in seen_pairs: continue
        seen_pairs.add(key); probs.append(f"{name}: overlap {p['a']} <-> {p['b']} ({p['px']} px2, {p['k']} %)")
    for c in o['cuts']:
        key = (name.split(' tab')[0], 'cut', c['a'])
        if key in seen_pairs: continue
        seen_pairs.add(key); probs.append(f"{name}: text cut {c['a']} ({c['k']} % shows)")
    if o['overlaps'] or o['cuts']:
        pg.evaluate(MARK, o); shot(name.replace(' ', '_')); pg.evaluate("for (const d of document.querySelectorAll('.qa-mark')) d.remove()")
    return o
def scroll_states(name):
    """the main scrolling list scrolled to its middle and its end: what hides down there shows"""
    n = pg.evaluate("""(() => { const s = [...document.querySelectorAll('#ui *, .modal *')].filter(e => /(auto|scroll)/.test(getComputedStyle(e).overflowY) && e.scrollHeight > e.clientHeight + 40); window.__qs = s.sort((a, b) => b.clientHeight * b.clientWidth - a.clientHeight * a.clientWidth)[0] || null; return window.__qs ? 1 : 0; })()""")
    if not n: return
    for k in (0.5, 1.0):
        pg.evaluate(f"(() => {{ const s = window.__qs; s.scrollTop = (s.scrollHeight - s.clientHeight) * {k}; }})()"); state(f'{name} scrolled {int(k * 100)}%')
    pg.evaluate("(() => { const s = window.__qs; if (s) s.scrollTop = 0; window.__qs = null; })()")
def menu(name, js, tabsel='.tabs:not(.subtabs) > .btn, .tabs:not(.subtabs) > button', sub=True):
    pg.evaluate(js); time.sleep(0.8)
    state(name); scroll_states(name)
    n = pg.evaluate(f"document.querySelectorAll('{tabsel}').length")
    for i in range(n):
        pg.evaluate(f"document.querySelectorAll('{tabsel}')[{i}].click()"); time.sleep(0.3)
        state(f'{name} tab {i}'); scroll_states(f'{name} tab {i}')
        if not sub: continue
        m = pg.evaluate("document.querySelectorAll('.tabs.subtabs > .btn, .tabs.subtabs > button').length")
        for j in range(m):
            pg.evaluate(f"document.querySelectorAll('.tabs.subtabs > .btn, .tabs.subtabs > button')[{j}].click()"); time.sleep(0.25)
            state(f'{name} tab {i} sub {j}')
menu('main', "UI.mainMenu()", '.nothing')
menu('play', "UI.playScreen()", '.nothing')
pg.evaluate("(() => { const b = document.querySelector('.color-row .swatch, .cpal-btn, .col-sw'); if (b) b.click(); })()"); time.sleep(0.4); state('play palette')
menu('bestiary', "UI.bestiary()")
menu('shop', "UI.shop()")
menu('armory', "UI.armory()")
menu('achievements', "UI.achievements()")
menu('stats', "UI.stats()")
menu('options', "UI.options()", '.nothing')
menu('controls', "UI.controls()")
menu('credits', "UI.credits()", '.nothing')
menu('profiles', "UI.mainMenu(), UI.profilesMenu()", '.nothing')
menu('rename', "UI.renameMenu(1)", '.nothing')
menu('discord', "UI.closeModal(), UI.mainMenu(), UI.discordInfo()", '.nothing')
menu('dofus', "UI.closeModal(), UI.dofusInfo(Game.C.dofus[0])", '.nothing')
menu('music', "UI.closeModal(), UI.mainMenu(), document.querySelector('.mute-btn').click()", '.nothing')
url('autostart=1&fresh=1&cls=iop&map=astrub&t=30')
pg.wait_for_function("Game.state === 'run' && Game.run && Game.run.time > 0.3", timeout=120000); time.sleep(4)
menu('pause', "Game.togglePause()", '.nothing'); pg.evaluate("Game.togglePause()"); time.sleep(0.3)
menu('levelup', "UI.levelUpMenu(Game.run, Game.run.upgradeOptions(4))", '.nothing'); pg.evaluate("UI.closeModal()")
menu('runover', """(() => { const R = Game.run, C = Game.C; R.relics = (C.relics || []).slice(0, 6); R.dofus = (C.dofus || []).slice(0, 3); R.time = 400; R.kills = 900; UI.runOverMenu(R, false, null); })()""", '.nothing')
for p in probs: print('PROB', p)
print('SUMMARY menus', states, 'problems', len(probs))
print('\n'.join(l for l in logs if 'pageerror' in l))
