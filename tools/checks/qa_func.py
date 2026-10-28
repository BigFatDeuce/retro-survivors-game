"""0.94: the functional tests in the browser, built on tools/checks/stress.py's harness (the same local
server, Playwright's Chromium on the real GPU, a fresh browser profile — the player's own saves are never read nor
written —, Math.random seeded, page errors / console errors / Game._frameErr / crashes caught). Each test drives the game
as a player does (its menus, keys, a simulated controller, clicks made from inside the page) and checks what must hold.

  boot       a first start: the menu, the version shown, the web quality (1080p) and its buffer, PixiJS on
  saves      damaged / old / partial saves in localStorage: the game still starts, what is valid is kept
  import     a partly invalid save file imported, then the reload
  nav        every main-menu entry opened and closed with the keyboard (focus kept, back on its button), Tab / Shift+Tab,
             the mouse then the keys, a simulated controller (d-pad, A, B, Start)
  shop       buying (price taken once, refused without the kamas), equipping, a spell level, after a reload; the shield's
             +1 resistance in a run (once), no hat / shield for the classes that wear none
  runs       from the menus: countdown, level-up card, a boss, pause, given up, died then 'Rejouer', cancelled (< 20 s),
             won; what each one saves; after each run back in the menu: no run left, no interval left running, no run
             sound, the same number of animation-frame callbacks
  restart    six runs in a row started and left: intervals, frame callbacks, listeners, characters kept stay level
  settings   volumes, language, quality, the Canvas 2D renderer (a run on it), kept after a reload
  profiles   a second profile kept apart, a name's sound clip and its achievement
  sizes      1280x720, 1920x1080, 2560x1440, 3840x2160, 3440x1440, 2560x1080: menu scale, picture buffer, the menu inside
             the window; screenshots of the menu, the play screen, a run and the pause (for the visual review)

usage: python tools/checks/qa_func.py [test…] [--out DIR] [--renderer pixi|canvas] [--seed S] [--soft-gpu]
prints one JSON line per test ({ test, ok, fails, info, s }) then 'FUNC <n> tests, <m> failed'; exit code 1 if any failed"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import sys, os, json, time, datetime, traceback
from playwright.sync_api import sync_playwright
import stress as ST

SAVE_KEY, META_KEY = 'krosmoz-survivors-v1', 'krosmoz-survivors-profiles'

# what runs in the page before the game, on top of stress.py's INIT (test only)
QA_INIT = """(() => {
  // the intervals alive with where they were made (a closed run must leave none), the frame callbacks asked per frame
  const si = window.setInterval.bind(window), ci = window.clearInterval.bind(window), live = new Map();
  window.setInterval = (f, ms, ...a) => { const id = si(f, ms, ...a); live.set(id, ((new Error().stack || '').split('\\n')[2] || '?').trim()); return id; };
  window.clearInterval = id => { live.delete(id); return ci(id); };
  window.__intervals = () => [...live.values()];
  const raf = window.requestAnimationFrame.bind(window); let n = 0; window.__raf = [];
  window.requestAnimationFrame = f => { n++; return raf(f); };
  const tick = () => { window.__raf.push(n); n = 0; if (window.__raf.length > 120) window.__raf.shift(); raf(tick); }; raf(tick);
  // a simulated controller: the test sets window.__pad (buttons / axes of the standard mapping)
  window.__pad = null; const gp = navigator.getGamepads ? navigator.getGamepads.bind(navigator) : () => [];
  Object.defineProperty(navigator, 'getGamepads', { value: () => window.__pad ? [window.__pad] : gp(), configurable: true });
  // a seeded save (once per test page: a reload keeps what the game saved)
  const seed = %s; if (seed && !localStorage.getItem('__qa_seeded')) { for (const k in seed) { if (seed[k] === null) localStorage.removeItem(k); else localStorage.setItem(k, seed[k]); } localStorage.setItem('__qa_seeded', '1'); }
})()"""

# helpers in the page, once the game is up
QA_LIB = """(() => { if (window.QA) return 1;
  window.__snd = [];
  for (const k of ['sfx', 'thump', '_blip', 'fxFile', 'jingle', 'playMusic']) { const o = Audio2[k]; if (typeof o !== 'function') continue;
    Audio2[k] = function (...a) { window.__snd.push([k, String(a[0]).slice(0, 40), Game.state, !!Game.run, Math.round(performance.now())]); return o.apply(this, a); }; }
  window.QA = {
    nav() { const e = Nav.el, s = Nav.scope(); return { has: !!e, live: !!(e && e.isConnected), inScope: !!(e && s && s.contains(e)), text: e ? (e.textContent || e.className || '').trim().slice(0, 30) : null, screen: UI.screen, modal: !!UI.modalOpen() }; },
    raf() { const a = window.__raf.slice(-30).sort((x, y) => x - y); return a.length ? a[a.length >> 1] : 0; },
    sounds(since) { return window.__snd.filter(s => s[4] >= since); },
    build() { const R = Game.run; return R ? R.spells.reduce((a, s) => a + s.level, 0) + Object.values(R.passives).reduce((a, b) => a + b, 0) + (R.weapon ? R.weapon.level : 0) : -1; },
    pad(b, on) { if (!window.__pad) window.__pad = { id: 'qa pad', index: 0, connected: true, mapping: 'standard', timestamp: 0, axes: [0, 0, 0, 0], buttons: [...Array(17)].map(() => ({ pressed: false, value: 0 })) };
      window.__pad.buttons[b] = { pressed: on, value: on ? 1 : 0 }; window.__pad.timestamp++; },
  };
  return 1; })()"""


class QA(ST.Harness):
    def __init__(self, a):
        a.setdefault('max_min', 120)
        super().__init__(a)
        self.results = []; self.fails = []; self.info = {}

    # -------- pages
    def fresh(self, seed=None, size=None):
        """a new browser profile (empty storage, or the given localStorage values), the game not opened yet"""
        for o in ('pg', 'ctx'):
            try: getattr(self, o).close()
            except Exception: pass
        w, h = map(int, (size or self.a['size']).split('x'))
        self.ctx = self.b.new_context(viewport={'width': w, 'height': h}, accept_downloads=True)
        self.ctx.add_init_script(ST.INIT % self.a['seed']); self.ctx.add_init_script(QA_INIT % json.dumps(seed))
        self.pg = self.ctx.new_page(); self.cdp = self.ctx.new_cdp_session(self.pg); self.cdp.send('Performance.enable')
        self.pg.on('pageerror', lambda e: self.errors.append(('pageerror', str(e)[:600])))
        self.pg.on('console', lambda m: m.type == 'error' and self.errors.append(('console', m.text[:400])))
        self.pg.on('crash', lambda *_: self.errors.append(('crash', 'the page crashed')))

    def boot(self):
        s = super().boot(); self.ev(QA_LIB); return s

    def open(self, q=''):
        super().open(q); self.ev(QA_LIB)

    def reload(self):
        self.open(''); self.pg.wait_for_function("document.querySelector('.menu-buttons')", timeout=60000)

    def key(self, k, n=1, wait=0.12):
        for _ in range(n): self.pg.keyboard.press(k); time.sleep(wait)

    def pad(self, b, hold=0.15):
        self.ev(f"QA.pad({b}, true)"); time.sleep(hold); self.ev(f"QA.pad({b}, false)"); time.sleep(0.15)

    def click(self, js_find):
        """clicks the element the expression finds (from inside the page); False if nothing"""
        return self.ev(f"(() => {{ const e = ({js_find}); if (!e) return false; e.click(); return true; }})()")

    def wait(self, js, t=20): self.pg.wait_for_function(js, timeout=t * 1000)

    # -------- checks
    def expect(self, ok, what):
        if not ok: self.fails.append(what)
        return ok

    def run_test(self, name, fn):
        self.fails = []; self.info = {}; n0 = len(self.errors); t = time.time()
        try: fn(self)
        except Exception as e:
            self.fails.append(f'stopped: {type(e).__name__}: {str(e)[:400]}'); traceback.print_exc()
        try:
            fe = self.ev("typeof Game !== 'undefined' ? (Game._frameErr || null) : null")
            if fe: self.errors.append(('frameErr', str(fe)[:600]))
        except Exception: pass
        errs = [f'{k}: {m}' for k, m in self.errors[n0:] if not (k == 'console' and ('favicon' in m or 'ERR_ABORTED' in m))]
        r = dict(test=name, ok=not self.fails and not errs, fails=self.fails + errs, info=self.info, s=round(time.time() - t, 1))
        self.results.append(r); print(json.dumps(r, ensure_ascii=False), flush=True)
        return r

    # -------- a run from the menus
    def menu_run(self, cls='iop', zone='astrub', countdown=None):
        """the play screen, the class card, the zone card, start, the loading screen's Play; returns True if the countdown was seen"""
        self.ev("(([z, c]) => { const S = Store.data; if (!S.unlocked.includes(z)) S.unlocked.push(z); Store.save(); })", [zone, cls])
        self.play_screen()
        self.ev("(c => { const i = Game.C.classes.findIndex(x => x.id === c); const e = document.querySelectorAll('.class-card')[i]; if (e) e.click(); })", cls); time.sleep(0.4)
        self.ev("""(z => { const i = Game.C.maps.findIndex(m => m.id === z); const c = document.querySelectorAll('.maps .map-card')[i]; if (c) c.click(); })""", zone)
        self.ev("(() => { document.querySelector('.screen.play .start-row .btn.orange:last-child').click(); })()")
        self.wait("!!document.querySelector('.load-play')", 120)
        return self.after_load_play()

    def after_load_play(self):
        time.sleep(0.2); self.ev("(() => { document.querySelector('.load-play').click(); })()")
        seen = False
        for _ in range(80):
            k = self.ev("Game.run && Game.run.cine ? Game.run.cine.kind : (Game.run && Game.state === 'run' ? 'run' : '')")
            if k == 'countdown': seen = True
            if k == 'run' and self.ev("Game.run.time > 0.3"): break
            time.sleep(0.05)
        self.wait('Game.run && Game.state === "run" && !Game.run.cine', 30)
        return seen

    def menu_state(self):
        return self.ev("({ run: !!Game.run, state: Game.state, screen: UI.screen, intervals: window.__intervals(), raf: QA.raf(), live: CharSprite.live.size })")

    def after_menu(self, base, what):
        """back in the menu after a run: nothing of the run must go on"""
        t = self.ev("performance.now()"); time.sleep(3)
        st = self.menu_state(); snd = self.ev(f"QA.sounds({t})")
        self.expect(not st['run'] and st['state'] == 'menu', f'{what}: the run is still there ({st["state"]})')
        extra = [x for x in st['intervals'] if x not in base['intervals'] or st['intervals'].count(x) > base['intervals'].count(x)]
        self.expect(not extra, f'{what}: intervals left running: {extra[:4]}')
        if not self.ev("!!UI._kwakOn"): self.expect(st['raf'] <= base['raf'], f"{what}: frame callbacks per frame {base['raf']} -> {st['raf']}")   # (the menu's Kwak / Tofu crossing has its own loop)
        runsnd = [s for s in snd if s[0] in ('thump', 'fxFile') or (s[0] == 'sfx' and s[3])]
        self.expect(not runsnd, f'{what}: run sounds in the menu: {runsnd[:4]}')
        mus = self.ev("Audio2.musicName"); self.info.setdefault('menu_music', []).append(mus)
        return st


# ---------------------------------------------------------------- tests
def t_boot(H):
    H.fresh(); H.info['menu_s'] = H.boot()
    b = H.ev("BUILD"); H.expect(b in H.ev("document.querySelector('.version').textContent"), f'version {b} not shown on the menu')
    q = H.ev("Game.quality()"); H.expect(q == 'hd', f'web quality {q} (want hd = 1080p)')
    w, h, px, dpr = H.ev("[Game.canvas.width, Game.canvas.height, PX.on, devicePixelRatio]")
    H.info.update(buffer=f'{w}x{h}', pixi=px, dpr=dpr)
    H.expect(max(w, h) <= 1920 and min(w, h) <= 1080, f'buffer {w}x{h} over 1080p')
    H.expect(px == (H.a['renderer'] == 'pixi'), f"renderer: PixiJS {'off' if not px else 'on'} with --renderer {H.a['renderer']}")
    H.expect(H.ev("Store.data.kamas === 0 && Store.data.unlocked.join() === 'astrub' && Store.data.v === Store.SAVE_V"), 'a new profile is not the defaults')
    H.expect(not H.ev("UI.modalOpen()"), 'a window is open over the first menu')


DAMAGED = {
    'settings null': ('{"v":1,"kamas":321,"unlocked":["astrub","bonta"],"settings":null}', "Store.data.kamas === 321 && Store.data.unlocked.includes('bonta') && typeof Store.data.settings.music === 'number'"),
    'tables null': ('{"kamas":55,"unlocked":["astrub"],"owned":null,"equip":null,"cleared":null,"mastery":null,"seen":null,"kills":null,"dofus":null,"best":null,"spellLv":null,"scrolls":null}', "Store.data.kamas === 55 && Array.isArray(Store.data.owned) && typeof Store.data.equip === 'object'"),
    'wrong types': ('{"kamas":"abc","unlocked":"astrub","owned":{"a":1},"equip":[],"cleared":[],"best":"x","runs":"7"}', "Store.data.kamas === 0 && Store.data.unlocked.includes('astrub') && Array.isArray(Store.data.owned) && !Array.isArray(Store.data.equip) && Store.data.runs === 0"),
    'not JSON': ('{broken', "Store.data.kamas === 0"),
    'old save (no version, 0.5x fields)': ('{"kamas":1200,"unlocked":["astrub","bonta"],"owned":["16_1"],"equip":{"hat":"16_1"},"cleared":{"astrub":1},"settings":{"music":0.3,"sfx":0.4,"lang":"fr"}}',
                                           "Store.data.kamas === 1200 && Store.data.equip.hat === '16_1' && Store.data.settings.music === 0.3 && Store.data.settings.dmgNumbers === true && Store.data.v === Store.SAVE_V"),
    'unknown skins equipped': ('{"v":1,"kamas":5,"unlocked":["astrub"],"owned":["16_99999"],"equip":{"hat":"16_99999","cape":"17_99999","pet":"18_99999","shield":"82_99999"}}', "Store.data.kamas === 5"),
}


def t_saves(H):
    for name, (raw, ok_js) in DAMAGED.items():
        n0 = len(H.fails)
        H.fresh(seed={SAVE_KEY: raw})
        try: H.boot()
        except Exception as e: H.expect(False, f'{name}: the game did not reach its menu ({type(e).__name__})'); continue
        H.expect(H.ev(ok_js), f'{name}: the save was not read as it should: ' + json.dumps(H.ev("({ kamas: Store.data.kamas, unlocked: Store.data.unlocked, equip: Store.data.equip, settings: Store.data.settings })"))[:300])
        H.expect(H.ev("(() => { Store.save(); const d = JSON.parse(localStorage.getItem(Store.key)); return typeof d.settings === 'object' && d.settings !== null && Array.isArray(d.owned); })()"), f'{name}: the save written back is still damaged')
        if name == 'unknown skins equipped':
            H.menu_run('iop', 'astrub'); H.play(3); H.give_up()
        H.info[name] = 'ok' if len(H.fails) == n0 else 'FAIL'
    H.fresh(seed={META_KEY: '{"cur":"x","names":null}', SAVE_KEY: '{"v":1,"kamas":9,"unlocked":["astrub"]}'})
    H.boot(); H.expect(H.ev("Store.prof === 1 && Store.data.kamas === 9"), 'a damaged profile list: profile 1 not loaded')


def t_import(H):
    H.fresh(); H.boot()
    bad = json.dumps({'game': 'retro-survivors', 'v': 1, 'data': {'v': 1, 'kamas': 4321, 'unlocked': ['astrub', 'bonta'], 'owned': None, 'equip': 'x', 'cleared': {'astrub': 2}, 'settings': None}})
    r = H.ev("(t => { const r = Store.parseImport(t); if (r.data) Store.importData(r.data); return r.err || 'ok'; })", bad)
    H.expect(r == 'ok', f'a save file with damaged fields refused: {r}')
    H.reload()
    H.expect(H.ev("Store.data.kamas === 4321 && Store.data.cleared.astrub === 2 && Array.isArray(Store.data.owned) && typeof Store.data.equip === 'object'"), 'after the import and the reload the profile is not right: ' + json.dumps(H.ev("({ k: Store.data.kamas, o: Store.data.owned, e: Store.data.equip })")))
    for txt, want in [('hello', 'save_bad'), ('{"a":1}', 'save_bad'), (json.dumps({'game': 'retro-survivors', 'v': 99, 'data': {'v': 99, 'kamas': 1, 'unlocked': []}}), 'save_newer')]:
        H.expect(H.ev("t => Store.parseImport(t).err", txt) == want, f'import of {txt[:20]}… not refused as {want}')


MAIN_ENTRIES = ['play', 'bestiary', 'armory', 'shop', 'achievements', 'stats', 'controls', 'options']


def t_nav(H):
    H.fresh(); H.boot(); H.key('ArrowDown')
    btns = H.ev("[...document.querySelectorAll('.menu-buttons .btn')].map(b => b.textContent.trim().slice(0, 24))")
    H.info['main_buttons'] = len(btns)
    for i, label in enumerate(btns[:-1]):   # (the last one quits the game)
        H.ev("(i => Nav.set(document.querySelectorAll('.menu-buttons .btn')[i]))", i); time.sleep(0.15)
        H.key('Enter', wait=0.6)
        sc = H.ev("UI.screen"); H.expect(sc != 'main', f'Enter on "{label}" opened nothing')
        for k in ['ArrowDown', 'ArrowRight', 'ArrowDown', 'Tab', 'Shift+Tab', 'ArrowUp', 'ArrowLeft']:
            H.key(k, wait=0.15); s = H.ev("QA.nav()")
            if not H.expect(s['has'] and s['live'] and s['inScope'], f'{sc}: after {k} the highlight is lost ({s})'): break
        for _ in range(4):
            if H.ev("UI.screen") == 'main' and not H.ev("UI.modalOpen()"): break
            H.key('Escape', wait=0.5)
        s = H.ev("QA.nav()")
        H.expect(s['screen'] == 'main', f'{sc}: Escape did not lead back to the main menu ({s["screen"]})')
        H.expect(s['has'] and s['text'] and s['text'][:8] == label[:8], f'{sc}: back on the main menu the highlight is on "{s["text"]}", not "{label}"')
    # a volume slider highlighted, the Options left with the mouse's 'back': left / right on the menu must not change it
    H.ev("UI.options()"); time.sleep(0.5)
    H.ev("Nav.set(document.querySelector('#ui input[type=range]'))"); v0 = H.ev("[Store.data.settings.music, Store.data.settings.sfx]")
    H.ev("UI.mainMenu()"); time.sleep(0.4); H.key('ArrowRight', 3); H.key('ArrowLeft')
    H.expect(H.ev("[Store.data.settings.music, Store.data.settings.sfx]") == v0, 'a volume slider of the closed Options still took left / right: ' + json.dumps(H.ev("[Store.data.settings.music, Store.data.settings.sfx]")))
    s = H.ev("QA.nav()"); H.expect(s['has'] and s['live'] and s['screen'] == 'main', f'left / right after the Options: no highlight on the menu ({s})')
    # the mouse, then the keys
    H.play_screen(); box =H.ev("(() => { const r = document.querySelectorAll('.class-card')[3].getBoundingClientRect(); return [r.x + r.width / 2, r.y + r.height / 2]; })()")
    H.pg.mouse.move(box[0], box[1]); time.sleep(0.2); H.pg.mouse.down(); H.pg.mouse.up(); time.sleep(0.3)
    H.key('ArrowRight'); s = H.ev("QA.nav()"); H.expect(s['has'] and s['live'] and s['inScope'], f'mouse then keys: no highlight ({s})')
    H.pg.mouse.move(box[0] + 40, box[1] + 30); time.sleep(0.2); H.key('ArrowDown'); s = H.ev("QA.nav()")
    H.expect(s['has'] and s['live'] and s['inScope'], f'keys after a mouse move: no highlight ({s})')
    H.key('Escape', wait=0.5)
    # a controller: d-pad, A, B, Start on the play screen
    H.ev("UI.mainMenu()"); time.sleep(0.4)
    H.pad(13); H.pad(12); s0 = H.ev("QA.nav()"); H.expect(s0['has'] and s0['screen'] == 'main', f'controller d-pad: no highlight on the menu ({s0})')
    H.ev("Nav.set(document.querySelector('.menu-buttons .btn'))"); H.pad(0); time.sleep(0.5)
    H.expect(H.ev("UI.screen") == 'play', 'controller A on Jouer: the play screen did not open')
    H.pad(15); H.pad(13); s = H.ev("QA.nav()"); H.expect(s['has'] and s['inScope'], f'controller on the play screen: highlight lost ({s})')
    H.pad(9); s = H.ev("QA.nav()"); H.expect('start-btn' in H.ev("Nav.el ? Nav.el.className : ''") or s['text'], 'controller Start on the play screen: not on the start button')
    H.pad(1); time.sleep(0.5); H.expect(H.ev("UI.screen") == 'main', 'controller B on the play screen: not back on the main menu')
    H.ev("window.__pad = null")


def t_shop(H):
    H.fresh(); H.boot()
    H.ev("(() => { Store.data.kamas = 300000; Store.save(); })()")
    snap = "({ k: Store.data.kamas, owned: Store.data.owned.slice(), equip: Object.assign({}, Store.data.equip), lv: JSON.stringify([Store.data.spellLv, Store.data.passLv || {}, Store.data.scrolls, Store.data.mastery]) })"
    bought = {}
    for kind, slot, lst in [('hats', 'hat', 'hats'), ('capes', 'cape', 'capes'), ('pets', 'pet', 'pets'), ('shields', 'shield', 'shields')]:
        H.ev(f"(() => {{ UI._shopKind = '{kind}'; UI.shop(); }})()"); time.sleep(0.6)
        it = H.ev(f"""(() => {{ const S = Store.data; for (const c of document.querySelectorAll('.shop-item[data-nav^="{slot}:"]')) {{ const id = c.dataset.nav.split(':')[1]; if (id === 'none' || S.owned.includes(id)) continue;
            const d = Game.C.{lst}.find(x => x.id === id); if (d && d.price <= S.kamas) return [id, d.price]; }} return null; }})()""")
        if not H.expect(it, f'{kind}: no item to buy'): continue
        a = H.ev(snap); H.click(f"""document.querySelector('.shop-item[data-nav="{slot}:{it[0]}"] .btn')"""); time.sleep(0.3); b = H.ev(snap)
        H.expect(a['k'] - b['k'] == it[1], f"{kind}: {it[0]} cost {a['k'] - b['k']} instead of {it[1]}")
        H.expect(it[0] in b['owned'] and b['equip'].get(slot) == it[0], f'{kind}: {it[0]} not owned / worn after buying')
        H.click(f"""document.querySelector('.shop-item[data-nav="{slot}:{it[0]}"] .btn')"""); time.sleep(0.3)
        H.expect(H.ev(snap)['k'] == b['k'], f'{kind}: a second click on a bought item took kamas')
        bought[slot] = it[0]
    # not enough kamas
    H.ev("(() => { Store.data.kamas = 10; Store.save(); UI._shopKind = 'hats'; UI.shop(); })()"); time.sleep(0.5)
    poor = H.ev("""(() => { for (const c of document.querySelectorAll('.shop-item[data-nav^="hat:"]')) { const id = c.dataset.nav.split(':')[1]; if (id !== 'none' && !Store.data.owned.includes(id)) { c.querySelector('.btn').click(); return id; } } })()""")
    time.sleep(0.3); H.expect(H.ev("Store.data.kamas") == 10 and poor not in H.ev("Store.data.owned"), 'a hat was bought without the kamas')
    # the levels (spells, characteristics, scrolls, masteries): one level, its price once
    H.ev("(() => { Store.data.kamas = 300000; Store.save(); })()")
    for kind in ['spells', 'traits', 'scrolls', 'mastery']:
        H.ev(f"(() => {{ UI._shopKind = '{kind}'; UI.shop(); }})()"); time.sleep(0.6)
        a = H.ev(snap)
        ok = H.click("[...document.querySelectorAll('.shop-item .btn.orange, .shop-grid .btn.orange')].find(b => b.querySelector('img') && !b.classList.contains('disabled'))")
        time.sleep(0.3); b = H.ev(snap)
        if not H.expect(ok, f'{kind}: no level to buy'): continue
        H.expect(b['k'] < a['k'] and b['lv'] != a['lv'], f'{kind}: a level bought changed {a["k"] - b["k"]} kamas, levels changed: {b["lv"] != a["lv"]}')
        H.info[f'{kind}_cost'] = a['k'] - b['k']
    H.info['bought'] = bought
    keep = H.ev(snap); H.reload(); after = H.ev(snap)
    H.expect(after == keep, 'after a reload the purchases are not the same')
    # the shield in a run: +1 resistance once; none for the Roublard (no hats nor shields)
    if bought.get('shield'):
        H.menu_run('iop', 'astrub')
        a, b0, c = H.ev("(() => { const R = Game.run, a = R.stats.armor, s = R.opts.shield; R.opts.shield = null; R.recompute(); const b = R.stats.armor; R.opts.shield = s; R.recompute(); R.recompute(); return [a, b, R.stats.armor]; })()")
        H.expect(abs(a - b0 - 1) < 1e-9 and abs(c - a) < 1e-9, f'shield: resistance {b0} without, {a} with, {c} after rebuilding (want +1 once)')
        H.expect(H.ev("Game.run.charSprite.shield") == bought['shield'] and H.ev("Game.run.charSprite.hat") == bought.get('hat'), 'the Iop does not wear the bought shield / hat')
        H.give_up()
        H.menu_run('roublard', 'astrub')
        H.expect(H.ev("!Game.run.shieldOn() && !Game.run.charSprite.shield && !Game.run.charSprite.hat && !Game.run.charSprite.cape"), 'the Roublard wears a hat / cape / shield')
        H.give_up()


def t_runs(H):
    H.fresh(); H.boot(); time.sleep(1.5)
    base = H.menu_state(); H.info['menu_base'] = dict(raf=base['raf'], intervals=len(base['intervals']), live=base['live'])
    S0 = H.ev("({ runs: Store.data.runs, cleared: Object.assign({}, Store.data.cleared), kamas: Store.data.kamas })")
    # A: countdown, music, a level-up card, a boss, pause, given up after 20 s
    H.expect(H.menu_run('iop', 'astrub'), 'no countdown when a run starts from the menus')
    mus = H.ev("[Audio2.musicName, Game.run.map.music]"); H.info['run_music'] = mus
    H.expect(mus[0] and (mus[0].split(':')[-1] == mus[1] or '/' in mus[0]), f'run music {mus}')   # (musicName = '<style>:<track>')
    b0 = H.ev("QA.build()"); H.ev("(() => { Game.run.pendingLevels++; })()")
    H.wait("document.querySelectorAll('.up-card').length >= 3", 10); n = H.ev("document.querySelectorAll('.up-card').length")
    H.expect(3 <= n <= 4, f'{n} level-up cards'); time.sleep(0.3)
    H.click("document.querySelector('.up-card')"); time.sleep(0.6)
    H.expect(H.ev("!UI.modalOpen() && !Game.paused"), 'the level-up window stayed open after a card')
    H.info['build'] = [b0, H.ev("QA.build()")]
    boss = H.ev("""(() => { const R = Game.run, id = (R.bossQueue.find(b => !(R.C.bosses[b.id] || {}).final) || R.bossQueue[0] || {}).id; if (!id) return null; R.spawnBoss(id); const b = R.bossAlive[R.bossAlive.length - 1]; b.x = R.player.x + 140; b.y = R.player.y; return [id, R.bossFight()]; })()""")
    if H.expect(boss and boss[1], f'a boss did not come ({boss})'):
        H.ev("(() => { const R = Game.run; for (const b of R.bossAlive) R.damageMob(b, 1e12, { def: { id: 'qa' }, p: {} }, true); })()")
        H.wait("Game.run.bossAlive.length === 0", 10)
    H.play(3); H.bot(False)   # (the bot closes windows: off for the pause)
    t0 = H.ev("Game.run.time"); H.key('Escape', wait=1.0); t1 = H.ev("Game.run.time")
    H.expect(H.ev("Game.paused") and abs(t1 - t0) < 0.1, f'pause: run time {t0} -> {t1}')
    H.key('Escape', wait=0.6); H.expect(not H.ev("Game.paused"), 'Escape did not resume the run')
    H.ev("(() => { Game.run.time = Math.max(Game.run.time, 30); })()")
    H.give_up()
    H.expect(H.ev("Store.data.runs") == S0['runs'] + 1, 'a run given up after 20 s did not count')
    H.after_menu(base, 'given up')
    # B: died, then 'Rejouer' straight away, then cancelled before 20 s
    H.menu_run('cra', 'astrub'); H.play(2); runs1 = H.ev("Store.data.runs")
    H.ev("window.__old = Game.run"); H.bot(False); H.close_windows()   # (0.96: a level-up opened in the bot's last frame held the run: no end)
    H.expect(H.ev(ST.KILL), 'the character could not be killed')   # (0.95: ST.KILL; the old loop missed after a monster's touch)
    H.wait("!Game.run || Game.run.over", 30); H.wait("!!document.querySelector('.modal.over')", 20); time.sleep(0.5)
    H.expect(H.ev("Store.data.runs") == runs1 + 1, 'a death did not count as a run')
    ok = H.click("[...document.querySelectorAll('.modal.over .btn')].find(b => b.textContent.includes('↻'))")
    if H.expect(ok, "no 'Rejouer' button after a death"):
        H.wait("!!document.querySelector('.load-play')", 120); H.after_load_play()
        H.expect(H.ev("Game.run !== window.__old && window.__old.charSprite && window.__old.charSprite.disposed"), "'Rejouer': the old run was not let go")
        H.expect(H.ev("Game.run.cls.id") == 'cra', "'Rejouer' did not start the same class")
        H.play(3); r2 = H.ev("Store.data.runs"); H.give_up()
        H.expect(H.ev("Store.data.runs") == r2, 'a run given up before 20 s counted')
        H.expect(H.ev("!!(window.RESULT)") , 'no result after the cancelled run')
    H.ev("window.__old = null")
    H.after_menu(base, 'died / Rejouer / cancelled')
    # C: won
    k0 = H.ev("Store.data.kamas"); c0 = H.ev("Store.data.cleared.astrub || 0")
    H.menu_run('feca', 'astrub'); H.play(2); H.ev("(() => { Game.run.time = 30; })()"); H.win()   # (a run left before 20 s is 'cancelled', even won)
    H.expect(H.ev("RESULT.victory === true"), 'the win did not end as a victory')
    H.expect(H.ev("Store.data.cleared.astrub || 0") == c0 + 1, 'the won zone did not count as cleared')
    H.expect(H.ev("Store.data.kamas") > k0, 'no kamas after a win')
    H.after_menu(base, 'won')
    # what was saved survives a reload, the last class too
    keep = H.ev("({ runs: Store.data.runs, cleared: Store.data.cleared, kamas: Store.data.kamas, last: Store.data.lastClass })")
    H.reload(); H.expect(H.ev("({ runs: Store.data.runs, cleared: Store.data.cleared, kamas: Store.data.kamas, last: Store.data.lastClass })") == keep, 'after a reload the runs / cleared zones / kamas / last class differ')
    H.expect(keep['last'] == 'feca', f"last class played {keep['last']} (want feca)")


def t_restart(H):
    H.fresh(); H.boot(); time.sleep(1.5)
    rows = []
    for i in range(6):
        H.menu_run(['iop', 'sram', 'eniripsa'][i % 3], 'astrub'); H.play(3); H.give_up(); time.sleep(1.5)
        m = H.measure(); st = H.menu_state()
        rows.append(dict(intervals=len(st['intervals']), raf=st['raf'], live=st['live'], listeners=m.get('listeners'), nodes=m.get('nodes'), heap=m.get('heapMB')))
    H.info['rows'] = rows
    a, b = rows[1], rows[-1]
    H.expect(b['intervals'] <= a['intervals'], f"intervals {a['intervals']} -> {b['intervals']}")
    H.expect(b['raf'] <= a['raf'], f"frame callbacks {a['raf']} -> {b['raf']}")
    H.expect(b['live'] <= max(a['live'], 2), f"characters kept {a['live']} -> {b['live']}")
    H.expect(b['listeners'] <= a['listeners'] * 1.05 + 10, f"listeners {a['listeners']} -> {b['listeners']}")
    H.expect(b['nodes'] <= a['nodes'] * 1.05 + 50, f"DOM nodes {a['nodes']} -> {b['nodes']}")


def t_settings(H):
    H.fresh(); H.boot()
    H.ev("UI.options()"); time.sleep(0.6)
    n = H.ev("(() => { const r = [...document.querySelectorAll('.screen input[type=range], .modal input[type=range]')]; for (const e of r) { e.value = 0; e.dispatchEvent(new Event('input', { bubbles: true })); } return r.length; })()")
    H.expect(n >= 2, f'{n} volume sliders in the options')
    H.expect(H.ev("Store.data.settings.music === 0 && Store.data.settings.sfx === 0"), 'the volumes at 0 were not saved')
    H.expect(H.ev("!Audio2.sfxGain || Audio2.sfxGain.gain.value === 0"), 'the effects volume at 0 is not applied')
    H.ev("setLang('en')"); time.sleep(0.4)
    H.click("[...document.querySelectorAll('.qbtn[data-q]')].find(b => b.dataset.q === 'sd')"); time.sleep(0.5)
    H.expect(H.ev("Game.quality()") == 'sd', 'the 720p button did not change the quality')
    H.reload()
    H.expect(H.ev("Store.data.settings.music === 0 && Store.data.settings.sfx === 0 && LANG === 'en' && Game.quality() === 'sd'"), 'after a reload the volumes / language / quality are not kept: ' + json.dumps(H.ev("[Store.data.settings.music, Store.data.settings.sfx, LANG, Game.quality()]")))
    w, h = H.ev("[Game.canvas.width, Game.canvas.height]"); H.expect(max(w, h) <= 1280 and min(w, h) <= 720, f'720p chosen: buffer {w}x{h}')
    H.expect(H.ev("document.querySelector('.menu-buttons .btn').textContent.includes('Play')"), 'English chosen: the menu is not in English')
    # the Canvas 2D renderer, the fallback when WebGL fails (0.95: no longer in the options; ?pixi=0 forces it)
    H.pg.goto(H.base + '?pixi=0'); H.wait("typeof Game !== 'undefined' && Game.state === 'menu' && document.querySelector('.menu-buttons')", 60); H.ev(QA_LIB)
    H.expect(not H.ev("PX.on"), 'Canvas 2D chosen: PixiJS still draws')
    H.menu_run('iop', 'astrub'); f = H.play(5); H.info['canvas_frames'] = f.get('frames'); H.give_up()


def t_profiles(H):
    H.fresh(); H.boot()
    H.ev("(() => { Store.data.kamas = 111; Store.save(); Store.switchTo(2); Store.data.kamas = 222; Store.save(); })()")
    H.ev("(() => { Store.setName(2, 'Macron'); UI.nameEgg('Macron'); })()"); time.sleep(0.5)
    H.expect(any(s[0] == 'jingle' and s[1] == 'macron' for s in H.ev("QA.sounds(0)")), "the name 'Macron' played no clip")
    H.expect(H.ev("!!Prog.st().nameEgg"), "the name's achievement counter is not set")
    H.ev("(() => { Store.switchTo(1); })()"); H.reload()
    H.expect(H.ev("Store.prof === 1 && Store.data.kamas === 111 && JSON.parse(localStorage.getItem(Store.keyOf(2))).kamas === 222"), 'the profiles are not kept apart')
    H.ev("(() => { Store.switchTo(2); })()"); H.reload()
    H.expect(H.ev("Store.prof === 2 && Store.data.kamas === 222 && Store.pname(2) === 'Macron'"), 'profile 2 not loaded with its name after a reload')


SIZES = ['1280x720', '1920x1080', '2560x1440', '3840x2160', '3440x1440', '2560x1080']


def t_sizes(H):
    for sz in SIZES:
        w, h = map(int, sz.split('x'))
        H.fresh(size=sz); H.boot(); time.sleep(1)
        # the menus follow the window (--uiz), the picture's own interface follows the picture (Game.ui, its buffer)
        uiz = float(H.ev("getComputedStyle(document.documentElement).getPropertyValue('--uiz')") or 0); want = max(1, min(3, min(w / 1280, h / 720)))
        H.expect(abs(uiz - want) < 0.02, f'{sz}: menu scale --uiz {uiz} (want {want:.2f})')
        bw, bh = H.ev("[Game.canvas.width, Game.canvas.height]"); gu = H.ev("Game.ui"); gw = max(0.7, min(3, min(bw / 1280, bh / 720)))
        H.expect(abs(gu - gw) < 0.02, f'{sz}: in-run interface scale {gu} (want {gw:.2f} for a {bw}x{bh} picture)')
        H.expect(max(bw, bh) <= 1920 and min(bw, bh) <= 1080, f'{sz}: buffer {bw}x{bh} over the web quality (1080p)')
        box = H.ev("(() => { const out = []; for (const e of document.querySelectorAll('.menu-buttons, .top-bar, .version, .flags')) { const r = e.getBoundingClientRect(); if (r.left < -1 || r.top < -1 || r.right > innerWidth + 1 || r.bottom > innerHeight + 1) out.push(e.className); } return out; })()")
        H.expect(not box, f'{sz}: cut by the window: {box}')
        H.pg.screenshot(path=f'{H.dir}/{sz}_menu.png')
        H.play_screen(); time.sleep(0.8); H.pg.screenshot(path=f'{H.dir}/{sz}_play.png')
        H.ev("UI.mainMenu()"); time.sleep(0.3)
        H.menu_run('sram', 'astrub'); H.play(4); H.pg.screenshot(path=f'{H.dir}/{sz}_run.png')
        H.key('Escape', wait=0.8); H.pg.screenshot(path=f'{H.dir}/{sz}_pause.png'); H.key('Escape', wait=0.4)
        H.info[sz] = dict(uiz=uiz, ui=gu, buffer=f'{bw}x{bh}')
        H.give_up()


TESTS = dict(boot=t_boot, saves=t_saves, import_=t_import, nav=t_nav, shop=t_shop, runs=t_runs, restart=t_restart, settings=t_settings, profiles=t_profiles, sizes=t_sizes)


def main():
    try: sys.stdout.reconfigure(encoding='utf-8', errors='replace')   # (the menus' texts have emoji: the Windows console's code page cannot print them)
    except Exception: pass
    a = dict(scen=[], reps=1, seed=1234, max_min=120, renderer='pixi', size='1920x1080', soft=False, out=None, replay=None, step=None, quality=None)
    names = []; it = iter(sys.argv[1:])
    for x in it:
        if x == '--out': a['out'] = next(it)
        elif x == '--renderer': a['renderer'] = next(it)
        elif x == '--seed': a['seed'] = int(next(it))
        elif x == '--soft-gpu': a['soft'] = True
        elif x in TESTS or x + '_' in TESTS: names.append(x if x in TESTS else x + '_')
        else: sys.exit(f'unknown argument {x}\n' + __doc__)
    a['out'] = a['out'] or f"{ROOT}/work/qa/func-{datetime.datetime.now():%Y%m%d-%H%M%S}"
    H = QA(a); H.httpd = ST.serve()
    try:
        with sync_playwright() as p:
            H.launch(p)
            for n in names or list(TESTS):
                H.run_test(n.rstrip('_'), TESTS[n])
            H.b.close()
    finally:
        H.httpd.shutdown()
    bad = [r for r in H.results if not r['ok']]
    json.dump(H.results, open(f'{H.dir}/func.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'FUNC {len(H.results)} tests, {len(bad)} failed -> {H.dir}')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
