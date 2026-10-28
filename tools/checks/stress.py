"""0.93: stress tests of Retro Survivors — crashes, frozen states, memory that keeps growing, stutters.
Reuses what the project has: the local web server and Playwright's Chromium (as tools/check.py and tools/checks/pw_test.py),
launched with the real GPU (the new headless mode) like check.py's bench, so PixiJS runs on WebGL as for a player. The
game itself is not changed for the tests: the scenarios drive it from outside (its menus, Game / UI / Run objects through
page.evaluate), and nothing is added to the shipped game.

Safe by construction: every run is a fresh browser profile (empty localStorage: the player's own saves, in their
browser or in the exe, are never read nor written), the shop's kamas are test kamas of that profile, no network but
the local server. Math.random is replaced by a seeded generator (--seed) before the game starts, so a scenario plays
the same way again (--replay <log.json> runs it again with the seed, renderer, size and step it failed at).

Measures, per step: its duration; the JS heap after a forced garbage collection, DOM nodes, event listeners (Chrome
DevTools protocol); the memory of the browser's renderer and GPU processes (Windows working set / private bytes: these
hold the decoded images, canvases and video memory mirrors that the JS heap does not show — an indirect measure, the
video memory itself cannot be read); the game's own counters (CharSprite.live, decoded images and their pixels, PixiJS
texture sources, monster / effect sheets, accessory cache, picture cache, sprite pools); and during play the frame times
(p50 / p95 / p99, frames over 33.3 ms and 50 ms, long tasks). Errors: page errors, console errors, Game._frameErr,
WebGL context losses, a crashed page, a run that stops moving.

Scenarios (each repeated --reps times, at most --max-min minutes in all; a failed or interrupted scenario is a FAIL):
  menus      every menu and tab of the main menu, back, again
  charswap   a reported crash: the play screen, 10 character changes (cards, sexes), the shop's preview classes, then
             Astrub started from the menus, 20 s of play, given up, back to the menu — again and again
  runs       runs one after another: classes and zones (light and heavy) in turn, ended by giving up, dying or winning
             (the final boss killed, the victory screen, back to the menu)
  fight      a long fight: hundreds of monsters, every spell at its top level, bosses, numbers, then the frame times
  pause      in a run: pause / resume quickly, the tab hidden and shown again, bursts of keys
  firstuse   the first appearance of spells / monsters / effects of the session: the frames over 50 ms they cause
Not automated (need a person): the controller's buttons on a real pad, a screen recorder (Mirillis Action…) running
beside the game, the exe's own window (full screen / F11), the feel of the sound.

usage: python tools/checks/stress.py [scenario…] [--reps N] [--seed S] [--max-min M] [--renderer pixi|canvas] [--size WxH]
                              [--soft-gpu] [--out DIR] [--replay LOG.json]
       (no scenario = all; reports in work/stress/<date>/: log.json + report.md)"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import sys, os, json, time, threading, functools, http.server, socketserver, subprocess, statistics, traceback, datetime
from playwright.sync_api import sync_playwright

SCEN = ['menus', 'charswap', 'runs', 'fight', 'pause', 'firstuse']


def args():
    a = dict(scen=[], reps=3, seed=1234, max_min=40, renderer='pixi', size='1920x1080', soft=False, out=None, replay=None, step=None, quality=None)
    it = iter(sys.argv[1:])
    for x in it:
        if x == '--reps': a['reps'] = int(next(it))
        elif x == '--seed': a['seed'] = int(next(it))
        elif x == '--max-min': a['max_min'] = float(next(it))
        elif x == '--renderer': a['renderer'] = next(it)
        elif x == '--size': a['size'] = next(it)
        elif x == '--soft-gpu': a['soft'] = True
        elif x == '--quality': a['quality'] = next(it)
        elif x == '--out': a['out'] = next(it)
        elif x == '--replay': a['replay'] = next(it)
        elif x in SCEN: a['scen'].append(x)
        else: sys.exit(f'unknown argument {x}\n' + __doc__)
    if a['replay']:
        L = json.load(open(a['replay'], encoding='utf-8')); C = L['config']
        a.update(scen=[L['failed']['scenario']] if L.get('failed') else C['scen'], reps=C['reps'], seed=C['seed'], renderer=C['renderer'], size=C['size'], soft=C['soft'], quality=C.get('quality'))
    a['scen'] = a['scen'] or SCEN
    return a


# ---------------------------------------------------------------- the local server (the game folder, as check.py)
class Quiet(http.server.SimpleHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'   # (kept-alive connections: one new socket per file ran Windows out of them, ERR_NO_BUFFER_SPACE)
    def log_message(self, *a): pass
    def handle(self):
        try: super().handle()
        except Exception: pass


class Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def serve():
    httpd = Server(('127.0.0.1', int(os.environ.get('PORT', '0'))), functools.partial(Quiet, directory=f'{ROOT}/game'))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


# ---------------------------------------------------------------- what runs in the page before the game (test only)
INIT = """(() => {
  // a seeded Math.random: the same scenario plays the same way again
  let s = %d >>> 0; Math.random = () => { s = (s + 0x6D2B79F5) >>> 0; let t = s; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  // frame intervals and long tasks, read and emptied by the harness
  window.__ft = []; let last = 0; const f = (now) => { if (last) window.__ft.push(now - last); last = now; if (window.__ft.length > 40000) window.__ft.splice(0, 20000); requestAnimationFrame(f); }; requestAnimationFrame(f);
  window.__lt = []; try { new PerformanceObserver(l => { for (const e of l.getEntries()) window.__lt.push([Math.round(e.startTime), Math.round(e.duration)]); }).observe({ entryTypes: ['longtask'] }); } catch (e) { }
  window.__glLost = 0; document.addEventListener('webglcontextlost', () => { window.__glLost++; }, true);
  // the long animation frames (over 50 ms) and the script that took the time (Chrome's attribution)
  window.__loaf = []; try { new PerformanceObserver(l => { for (const e of l.getEntries()) { const sc = (e.scripts || []).slice().sort((a, b) => b.duration - a.duration)[0];
    window.__loaf.push({ at: Math.round(e.startTime), ms: Math.round(e.duration), render: Math.round(e.renderStart ? e.startTime + e.duration - e.renderStart : 0), fn: sc ? (sc.sourceFunctionName || sc.invoker || '?') + ' ' + (sc.sourceURL || '').split('/').pop().split('?')[0] + ':' + (sc.sourceCharPosition || '') : '-', sms: sc ? Math.round(sc.duration) : 0 }); if (window.__loaf.length > 400) window.__loaf.shift(); } }).observe({ type: 'long-animation-frame', buffered: false }); } catch (e) { }
})()"""

# kills the character at once; True if he died. Run.damagePlayer ignores a blow while he is invulnerable or invisible,
# 0.22 s of run time after the last one (a monster's touch just before: the old loop of 40 calls, all at the same run
# time, did nothing then — the 'runs' test of qa_func waited 30 s for a death that never came), a dodge (Esquive), a
# shield or a Libération charge, and the Phénix revives him: all are cleared first
KILL = """(() => { const R = Game.run, P = R.player; P.invulnUntil = 0; P.invisUntil = 0; P.lastHit = -10; P.shieldUp = false;
  R.stats.revive = 0; R.stats.evade = 0; if (R.powers) delete R.powers.liberation; R.damagePlayer(1e9, null); return P.dead; })()"""

# the game's own counters (async: the decoded images are promises)
COUNTERS = """(async () => {
  const out = { screen: (typeof UI !== 'undefined' && UI.screen) || null, state: (typeof Game !== 'undefined' && Game.state) || null };
  if (typeof Game === 'undefined' || !Game.C) return out;
  let n = 0, px = 0; const keys = Object.keys(Assets.img), vals = await Promise.all(keys.map(k => Assets.img[k].ready.catch(() => null))), by = {};
  vals.forEach((b, i) => { if (!b || !b.width) return; n++; px += b.width * b.height; const f = keys[i].split('/').slice(0, 2).join('/'); by[f] = (by[f] || 0) + b.width * b.height; });
  out.images = n; out.imageMpx = +(px / 1e6).toFixed(1); out.imageBy = Object.fromEntries(Object.entries(by).map(([k, v]) => [k, +(v / 1e6).toFixed(1)]));
  out.charLive = CharSprite.live.size; let cpx = 0; const seen = new Set();
  for (const cs of CharSprite.live) for (const p of cs.parts()) { const im = p && p.sheet && p.sheet.img; if (im && im.width && !seen.has(im) && im instanceof HTMLCanvasElement) { seen.add(im); cpx += im.width * im.height; } }
  out.charCanvasMpx = +(cpx / 1e6).toFixed(1);
  out.mobSheets = Object.keys(MobSheets.c).length; out.fxSheets = Object.keys(FxSheets.c).length; out.accCache = AccLib.cache.size; out.rcache = RCache.m.size;
  if (typeof PX !== 'undefined') { let tp = 0; for (const s of PX.srcs) tp += (s.width || 0) * (s.height || 0); out.pxOn = PX.on; out.pxLost = !!PX.lost; out.pxSrcs = PX.srcs.size; out.pxMpx = +(tp / 1e6).toFixed(1); out.pxPool = PX.pool.length; out.pxProxies = PX.proxies.length; out.pxLayers = PX.layers.length; }
  out.previews = UI.previews.length; out.canvases = document.querySelectorAll('canvas').length; out.glLost = window.__glLost;
  const R = Game.run; if (R) Object.assign(out, { time: +R.time.toFixed(1), mobs: R.mobs.length, projs: R.projs.length, eprojs: R.eprojs.length, particles: R.particles.length, pickups: R.pickups.length, effects: R.effects.length, texts: R.texts.length });
  out.frameErr = Game._frameErr || null;
  return out; })()"""

FRAMES = """(() => { const t = window.__ft.splice(0), lt = window.__lt.splice(0); if (t.length < 5) return { n: t.length };
  const s = [...t].sort((a, b) => a - b), q = p => +s[Math.min(s.length - 1, Math.floor(s.length * p))].toFixed(1);
  return { n: t.length, p50: q(0.5), p95: q(0.95), p99: q(0.99), max: +s[s.length - 1].toFixed(1), over33: t.filter(x => x > 33.4).length, over50: t.filter(x => x > 50).length,
    fps: +(1000 * t.length / t.reduce((a, b) => a + b, 0)).toFixed(1), longTasks: lt.length, longMs: lt.reduce((a, b) => a + b[1], 0),
    slow: window.__loaf.splice(0).filter(e => e.ms > 50).slice(-8).map(e => e.ms + 'ms ' + e.fn + ' (' + e.sms + ' ms, render ' + e.render + ')') }; })()"""


class Harness:
    def __init__(self, a):
        self.a = a; self.log = []; self.errors = []; self.t0 = time.time(); self.failed = None
        d = a['out'] or f"{ROOT}/work/stress/{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
        os.makedirs(d, exist_ok=True); self.dir = d

    # -------- browser
    def launch(self, p):
        args = ['--autoplay-policy=no-user-gesture-required', '--ignore-gpu-blocklist', '--enable-precise-memory-info', '--js-flags=--expose-gc']
        if self.a['soft']: args += ['--use-angle=swiftshader', '--enable-unsafe-swiftshader']
        try: self.b = p.chromium.launch(channel=os.environ.get('QA_CHANNEL', 'chromium'), args=args)   # (the new headless mode: the real GPU; 0.94: QA_CHANNEL=msedge = the installed Edge)
        except Exception: self.b = p.chromium.launch(args=args)
        self.bcdp = self.b.new_browser_cdp_session()
        w, h = map(int, self.a['size'].split('x'))
        self.ctx = self.b.new_context(viewport={'width': w, 'height': h})
        self.ctx.add_init_script(INIT % self.a['seed'])
        self.pg = self.ctx.new_page(); self.cdp = self.ctx.new_cdp_session(self.pg)
        self.cdp.send('Performance.enable')
        self.pg.on('pageerror', lambda e: self.errors.append(('pageerror', str(e)[:600])))
        self.pg.on('console', lambda m: m.type == 'error' and self.errors.append(('console', m.text[:400])))
        self.pg.on('crash', lambda *_: self.errors.append(('crash', 'the page crashed')))
        self.base = f'http://127.0.0.1:{self.httpd.server_address[1]}/index.html'

    # (clicks and waits from inside the page, never Playwright's element actions: the handles they leave made the old end
    # screens and loading screens look leaked — retained by DevTools, not by the game; checked with a heap snapshot)
    def open(self, q=''):
        self.pg.goto(self.base + '?' + '&'.join(x for x in (q, 'pixi=' + ('1' if self.a['renderer'] == 'pixi' else '0'), 'q=' + self.a['quality'] if self.a['quality'] else '') if x))
        self.pg.wait_for_function("typeof Game !== 'undefined' && (Game.state === 'menu' || Game.state === 'run')", timeout=120000)

    def boot(self):
        t = time.time(); self.open(''); self.pg.wait_for_function("document.querySelector('.menu-buttons')", timeout=120000); return round(time.time() - t, 2)

    def ev(self, js, arg=None): return self.pg.evaluate(js, arg) if arg is not None else self.pg.evaluate(js)

    # -------- measures
    def procmem(self):
        """the working set / private bytes (MB) of this browser's renderer and GPU processes (Windows)"""
        try:
            info = self.bcdp.send('SystemInfo.getProcessInfo')['processInfo']
            ids = {p['id']: p['type'] for p in info}
            if not ids or os.name != 'nt': return {}
            ps = "Get-Process -Id %s -ErrorAction SilentlyContinue | ForEach-Object { '{0} {1} {2}' -f $_.Id, $_.WorkingSet64, $_.PrivateMemorySize64 }" % ','.join(map(str, ids))
            out = subprocess.run(['powershell', '-NoProfile', '-Command', ps], capture_output=True, text=True, timeout=20).stdout
            agg = {}
            for line in out.split('\n'):
                parts = line.split()
                if len(parts) != 3: continue
                t = ids.get(int(parts[0]), '?'); ws, pv = int(parts[1]) / 2**20, int(parts[2]) / 2**20
                tl = t.lower(); k = 'gpu' if 'gpu' in tl else 'renderer' if tl == 'renderer' else 'browser' if tl == 'browser' else 'other'
                a = agg.setdefault(k, [0, 0]); a[0] += ws; a[1] += pv
            return {k: {'ws': round(v[0]), 'priv': round(v[1])} for k, v in agg.items()}
        except Exception as e:
            return {'err': str(e)[:120]}

    def measure(self, gc=True):
        m = {}
        try:
            if gc:
                self.cdp.send('HeapProfiler.collectGarbage'); self.cdp.send('HeapProfiler.collectGarbage')
            pm = {x['name']: x['value'] for x in self.cdp.send('Performance.getMetrics')['metrics']}
            m['heapMB'] = round(pm.get('JSHeapUsedSize', 0) / 2**20, 1); m['nodes'] = int(pm.get('Nodes', 0)); m['listeners'] = int(pm.get('JSEventListeners', 0))
            m['game'] = self.ev(COUNTERS)
        except Exception as e:
            m['err'] = str(e)[:200]
        m['proc'] = self.procmem()
        return m

    def frames(self): return self.ev(FRAMES)

    # -------- steps
    def step(self, scen, rep, name, fn, *fa, measure=True):
        if (time.time() - self.t0) / 60 > self.a['max_min']: raise TimeoutError('the time limit (--max-min) was reached')
        n0 = len(self.errors); t = time.time(); ok = True; info = None
        try: info = fn(*fa)
        except Exception as e:
            ok = False; self.errors.append(('step', f'{scen} #{rep} {name}: {type(e).__name__}: {str(e)[:500]}'))
        dur = round(time.time() - t, 2)
        st = self.ev("typeof Game !== 'undefined' ? (Game._frameErr || null) : null") if ok else None
        if st: self.errors.append(('frameErr', str(st)[:600]))
        errs = self.errors[n0:]
        e = dict(scenario=scen, rep=rep, step=name, dur=dur, ok=ok and not errs, info=info, errors=errs)
        if measure: e['m'] = self.measure()
        self.log.append(e)
        flag = 'ok ' if e['ok'] else 'ERR'
        g = (e.get('m') or {}).get('game') or {}; pr = (e.get('m') or {}).get('proc') or {}
        print(f"  {flag} {scen} #{rep} {name:22s} {dur:6.1f}s  heap {(e.get('m') or {}).get('heapMB', '-')} MB  renderer {pr.get('renderer', {}).get('priv', '-')} MB  gpu {pr.get('gpu', {}).get('priv', '-')} MB"
              f"  chars {g.get('charLive', '-')} img {g.get('imageMpx', '-')}Mpx tex {g.get('pxMpx', '-')}Mpx" + (f"  frames {info.get('frames')}" if isinstance(info, dict) and info.get('frames') else '')
              + (f"  !! {errs[0][1][:160]}" if errs else ''), flush=True)
        if not e['ok'] and not self.failed: self.failed = dict(scenario=scen, rep=rep, step=name)
        if any(k in ('crash',) for k, _ in errs): raise RuntimeError('the page crashed')
        return e

    # -------- game actions (the menus, as a player)
    def to_menu(self):
        self.ev("(() => { if (UI.modal) UI.closeModal(); Game.toMenu(); })()")   # (the game's own way back: the run let go)
        time.sleep(0.4)

    def play_screen(self):
        self.ev("UI.playScreen()"); time.sleep(0.5)

    def pick_class(self, i):
        """a class card of the play screen (and its other sex when it has one), as a click"""
        return self.ev("""(i => { const cards = [...document.querySelectorAll('.class-card')]; if (!cards.length) throw new Error('no class cards');
          const c = cards[i % cards.length]; c.click(); const sx = document.querySelector('.sex-btn, .play-sex .btn'); return (c.textContent || '').trim().slice(0, 14); })""", i)

    def start_from_menu(self, map_id):
        """the play screen's zone card, start, the loading screen's Play button, the countdown"""
        self.ev("""(z => { const i = Game.C.maps.findIndex(m => m.id === z); const c = document.querySelectorAll('.maps .map-card')[i]; if (c) c.click(); })""", map_id)
        self.ev("(() => { document.querySelector('.screen.play .start-row .btn.orange:last-child').click(); })()")
        self.pg.wait_for_function("!!document.querySelector('.load-play')", timeout=120000); time.sleep(0.2)
        self.ev("(() => { document.querySelector('.load-play').click(); })()")
        self.pg.wait_for_function('Game.run && Game.state === "run" && !Game.run.cine', timeout=60000)

    def autostart(self, q):
        self.open('autostart=1&' + q)
        self.pg.wait_for_function('Game.run && Game.state === "run" && Game.run.time > 0.2', timeout=120000)

    def bot(self, on=True):
        self.ev(f"(() => {{ Game.debug.bot = {1 if on else 0}; }})()")

    def play(self, sec, god=True):
        """play sec seconds (the game's own bot moves and picks); the run must move on"""
        self.bot(True)
        if god: self.ev("(() => { const R = Game.run; R.__god = setInterval(() => { if (R.player && !R.over) R.player.hp = R.stats.maxHp; }, 50); })()")
        self.frames(); t0 = self.ev("Game.run.time"); time.sleep(sec)
        f = self.frames(); t1 = self.ev("Game.run ? Game.run.time : -1")
        if god: self.ev("(() => { if (Game.run) clearInterval(Game.run.__god); })()")
        if t1 <= t0 + 0.5 and not self.ev("!!(Game.paused || UI.modal || (Game.run && Game.run.cine))"): raise RuntimeError(f'the run did not move ({t0} -> {t1})')
        return dict(frames=f, t=[round(t0, 1), round(t1, 1)])

    def close_windows(self):
        """a level-up / chest window the bot had no time to close (the run waits behind it, a death never ends): its levels
        dropped, the window closed"""
        for _ in range(20):
            if not self.ev("(() => { if (Game.run) Game.run.pendingLevels = 0; if (!UI.modal) return false; if (UI.botPick) UI.botPick(); if (UI.modal) UI.closeModal(); Game.paused = false; return true; })()"): return
            time.sleep(0.15)

    def give_up(self):
        """the pause menu's 'Abandonner' (asked twice), the end screen, its 'Menu principal' button"""
        self.bot(False)
        for _ in range(20):   # (a level-up / chest / tailor window may be open: closed first, then the pause menu)
            st = self.ev("(() => { if (document.querySelector('.pause-left')) return 'pause'; if (UI.modal) { if (UI.botPick) UI.botPick(); if (UI.modal && !document.querySelector('.pause-left')) UI.closeModal(); Game.paused = false; return 'closed'; } Game.togglePause(); return 'asked'; })()")
            if st == 'pause': break
            time.sleep(0.25)
        else: raise RuntimeError('the pause menu never opened')
        for _ in range(2):
            self.ev("""(() => { const r = UI.modal && [...UI.modal.querySelectorAll('.start-row .btn')]; const b = r && r[r.length - 2]; if (!b) throw new Error('no give-up button'); b.click(); })()""")   # (Quitter, then its confirmation)
            time.sleep(0.25)
        self.end_screen()

    def end_screen(self):
        self.pg.wait_for_function("!!document.querySelector('.modal.over')", timeout=20000); time.sleep(0.4)
        self.ev("""(() => { const b = [...document.querySelectorAll('.modal.over .ov-buttons .btn')].pop(); b.click(); })()""")
        self.pg.wait_for_function("Game.state === 'menu' && UI.screen === 'main'", timeout=20000)

    def die(self):
        self.bot(False); self.close_windows()
        if not self.ev(KILL): raise RuntimeError('the character could not be killed')
        self.pg.wait_for_function("!Game.run || Game.run.over", timeout=30000)
        self.end_screen()

    def win(self):
        """the zone's final boss killed (its real death: rewards, VICTOIRE !), then the run ended from the pause menu"""
        self.ev("""(() => { const R = Game.run; const ids = R.bossQueue.map(b => b.id).filter(id => R.C.bosses[id] && R.C.bosses[id].final);
          if (!ids.length) throw new Error('no final boss in this zone');
          for (const id of ids) { R.spawnBoss(id); const b = R.bossAlive[R.bossAlive.length - 1]; b.x = R.player.x + 120; b.y = R.player.y; R.damageMob(b, 1e12, { def: { id: 'stress' }, p: {} }, true); } })()""")   # (in range: Run.damageMob hits only what is on screen)
        self.pg.wait_for_function("Game.run && Game.run.finalKilled", timeout=20000); time.sleep(4.5)
        self.give_up()


# ---------------------------------------------------------------- scenarios
def sc_menus(H, rep):
    if 'autostart' in H.pg.url: H.open('')
    H.to_menu()
    for name, js in [('play', "UI.playScreen()"), ('bestiary', "UI.bestiary()"), ('armory', "UI.armory()"), ('shop', "UI.shop()"),
                     ('achievements', "UI.achievements()"), ('stats', "UI.stats()"), ('options', "UI.options()"), ('controls', "UI.controls()"), ('credits', "UI.credits()")]:
        def f(js=js):
            H.ev(js); time.sleep(0.5)
            tabs = H.ev("document.querySelectorAll('.tabs .btn').length")
            for k in range(min(tabs, 9)): H.ev(f"(() => {{ const b = document.querySelectorAll('.tabs .btn')[{k}]; if (b) b.click(); }})()"); time.sleep(0.25)
            H.ev("UI.mainMenu()"); time.sleep(0.3)
        H.step('menus', rep, name, f, measure=(name in ('shop', 'credits')))
    H.step('menus', rep, 'profiles', lambda: (H.ev("UI.profilesMenu()"), time.sleep(0.4), H.ev("UI.closeModal()")))


def sc_charswap(H, rep):
    """a reported crash: about ten character changes, then Astrub, several times"""
    if 'autostart' in H.pg.url: H.open('')
    H.to_menu()
    def swap():
        H.play_screen(); names = []
        for i in range(10): names.append(H.pick_class(i * 3 + rep)); time.sleep(0.45)
        H.ev("UI.shop()"); time.sleep(0.5)
        for i in range(6): H.ev("(() => { const b = document.querySelectorAll('.prev-row .arrow')[1]; if (b) b.click(); })()"); time.sleep(0.35)
        H.play_screen(); H.pick_class(rep * 7); time.sleep(0.4)
        return dict(classes=names)
    H.step('charswap', rep, 'ten changes', swap)
    H.step('charswap', rep, 'start astrub', lambda: H.start_from_menu('astrub'))
    H.step('charswap', rep, 'play 20 s', H.play, 20)
    H.step('charswap', rep, 'give up', H.give_up)


def sc_runs(H, rep):
    if 'autostart' in H.pg.url: H.open('')   # (a page opened by an autostart scenario skips the loading screen's Play button)
    zones = ['astrub', 'kwismas', 'sidimote', 'astrub', 'otomai_jungle', 'chafer']
    classes = ['iop', 'cra', 'feca', 'sram', 'osamodas', 'roublard', 'otomai', 'eniripsa', 'pandawa', 'bandit']
    for k, end in enumerate(['give up', 'die', 'win']):
        i = rep * 3 + k; z, c = zones[i % len(zones)], classes[i % len(classes)]
        H.to_menu()
        H.ev("(([z, c]) => { const S = Store.data; S.unlocked = Game.C.maps.map(m => m.id); S.lastClass = c; Store.save(); })", [z, c])
        H.step('runs', rep, f'{c} {z} start', lambda: (H.play_screen(), H.ev("(c => { const i = Game.C.classes.findIndex(x => x.id === c); const e = document.querySelectorAll('.class-card')[i]; if (e) e.click(); })", c), time.sleep(0.4), H.start_from_menu(z)))
        H.step('runs', rep, f'{c} play', H.play, 12)
        H.step('runs', rep, f'{c} {end}', {'give up': H.give_up, 'die': H.die, 'win': H.win}[end])


FIGHT = """(() => { const R = Game.run, P = R.player, ids = Object.keys(R.C.monsters).filter(k => !R.C.monsters[k].special && !R.C.monsters[k].boss).slice(0, 40); let n = 0;
  for (let i = 0; i < 260; i++) { const a = i * 2.399, r = 160 + (i % 13) * 34; if (R.spawnMob(ids[i % ids.length], P.x + Math.cos(a) * r, P.y + Math.sin(a) * r * 0.7, { force: true })) n++; }
  for (const b of Object.keys(R.C.bosses).filter(k => !R.C.bosses[k].doom && !R.C.bosses[k].unused).slice(0, 3)) R.spawnBoss(b);
  return n; })()"""


def sc_fight(H, rep):
    cls = ['iop', 'cra', 'feca', 'roublard'][rep % 4]
    spells = {'iop': 'epee_iop:4,colere_iop:4,epee_celeste:4,tempete_puissance:4,pression:4', 'cra': 'fleche_explosive:4,fleche_magique:4,fleche_enflammee:4,fleche_glacee:4,fleche_empoisonnee:4',
              'feca': 'bouclier_feca:4,bulle:4,glyphe_enflammee:4,attaque_nuageuse:4,glyphe_immobilisation:4', 'roublard': 'explobombe:4,dagues_boomerang:4,tromblon:4,kaboom:4,grisou:4'}[cls]
    H.step('fight', rep, f'{cls} start', H.autostart, f'cls={cls}&map=astrub&t=200&spells={spells}')
    H.step('fight', rep, 'spawn 260 + bosses', lambda: dict(spawned=H.ev(FIGHT)))
    H.step('fight', rep, 'fight 25 s', H.play, 25)
    H.step('fight', rep, 'back to the menu', H.to_menu)


def sc_pause(H, rep):
    H.step('pause', rep, 'start', H.autostart, 'cls=sram&map=astrub&t=60')
    def flick():
        for i in range(20): H.ev("Game.togglePause()"); time.sleep(0.05)
        H.ev("(() => { if (Game.paused) Game.togglePause(); })()")
        for k in ['ArrowLeft', 'ArrowUp', 'Space', 'Escape', 'Escape', 'KeyQ', 'KeyE', 'Tab']: H.pg.keyboard.press(k)
        H.ev("(() => { if (UI.modal) UI.closeModal(); Game.paused = false; })()")
    H.step('pause', rep, 'pause x20 + keys', flick)
    def tab():
        other = H.ctx.new_page(); other.goto('about:blank'); other.bring_to_front(); time.sleep(2.0); H.pg.bring_to_front(); other.close(); time.sleep(0.5)
        H.ev("(() => { if (UI.modal) UI.closeModal(); Game.paused = false; })()")
    H.step('pause', rep, 'tab away and back', tab)
    H.step('pause', rep, 'play 8 s', H.play, 8)
    H.step('pause', rep, 'give up', H.give_up)


def sc_firstuse(H, rep):
    """fresh page: every new spell / monster family / effect shown for the first time, the frames over 50 ms"""
    H.step('firstuse', rep, 'start', H.autostart, 'cls=iop&map=astrub&t=30')
    def burst():
        H.bot(True); H.frames(); out = []
        for i, sid in enumerate(H.ev("Game.C.classes.flatMap(c => c.spells).filter((s, i, a) => a.indexOf(s) === i).slice(%d, %d)" % (rep * 12, rep * 12 + 12))):
            H.ev("(id => { const R = Game.run; if (R.spells.length >= 12) R.spells.splice(1, 1); const s = R.addSpell(id); s.level = 4; s.recalc(); s.cd = 0; })", sid); time.sleep(0.9)
            f = H.frames(); out.append((sid, f.get('max'), f.get('over50')))
        return dict(spells=out, frames={'max': max(x[1] or 0 for x in out), 'over50': sum(x[2] or 0 for x in out)})
    H.step('firstuse', rep, 'new spells', burst)
    H.step('firstuse', rep, 'back to the menu', H.to_menu)


SCENARIOS = dict(menus=sc_menus, charswap=sc_charswap, runs=sc_runs, fight=sc_fight, pause=sc_pause, firstuse=sc_firstuse)


# ---------------------------------------------------------------- report
def report(H):
    a = H.a; L = H.log
    ok = all(e['ok'] for e in L) and not H.failed and H.done
    first = next((e for e in L if e.get('m') and e['m'].get('heapMB')), None); last = next((e for e in reversed(L) if e.get('m') and e['m'].get('heapMB')), None)
    def mem(e):
        if not e: return '-'
        m = e['m']; pr = m.get('proc') or {}; g = m.get('game') or {}
        return f"heap {m.get('heapMB')} MB, DOM {m.get('nodes')} nodes / {m.get('listeners')} listeners, renderer {pr.get('renderer', {}).get('priv', '-')} MB, GPU process {pr.get('gpu', {}).get('priv', '-')} MB, CharSprite {g.get('charLive')}, images {g.get('images')} ({g.get('imageMpx')} Mpx), textures {g.get('pxSrcs')} ({g.get('pxMpx')} Mpx)"
    lines = [f"# Stress tests — {datetime.datetime.now():%Y-%m-%d %H:%M}", '',
             f"Result: **{'PASS' if ok else 'FAIL'}** — {len(L)} steps, {sum(1 for e in L if not e['ok'])} failed, {round((time.time() - H.t0) / 60, 1)} min" + ('' if H.done else ' (interrupted: not a pass)'),
             f"Config: scenarios {', '.join(a['scen'])}; {a['reps']} repetitions; seed {a['seed']}; renderer {a['renderer']}; viewport {a['size']}; quality {a['quality'] or 'the default'}; {'software GPU' if a['soft'] else 'real GPU'}", '',
             f"Memory, first measure: {mem(first)}", f"Memory, last measure: {mem(last)}", '']
    if H.failed: lines += [f"First failure: {H.failed['scenario']} #{H.failed['rep']} '{H.failed['step']}' — replay: `python tools/checks/stress.py --replay {H.dir}/log.json`", '']
    lines += ['| scenario | rep | step | s | ok | heap MB | renderer MB | GPU MB | CharSprite | images Mpx | textures Mpx | frames (p50/p95/p99 ms, >33, >50) |', '|---|---|---|---|---|---|---|---|---|---|---|---|']
    for e in L:
        m = e.get('m') or {}; pr = m.get('proc') or {}; g = m.get('game') or {}; f = (e.get('info') or {}).get('frames') if isinstance(e.get('info'), dict) else None
        fr = f"{f.get('p50')}/{f.get('p95')}/{f.get('p99')}, {f.get('over33')}, {f.get('over50')}" if f and f.get('p50') is not None else ''
        lines.append(f"| {e['scenario']} | {e['rep']} | {e['step']} | {e['dur']} | {'ok' if e['ok'] else '**ERR**'} | {m.get('heapMB', '')} | {pr.get('renderer', {}).get('priv', '')} | {pr.get('gpu', {}).get('priv', '')} | {g.get('charLive', '')} | {g.get('imageMpx', '')} | {g.get('pxMpx', '')} | {fr} |")
    errs = [(e['scenario'], e['rep'], e['step'], er) for e in L for er in e['errors']]
    if errs: lines += ['', '## Errors'] + [f"- {s} #{r} {st}: {k}: {msg}" for s, r, st, (k, msg) in errs[:80]]
    open(f'{H.dir}/report.md', 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
    json.dump(dict(config=a, ok=ok, done=H.done, failed=H.failed, steps=L), open(f'{H.dir}/log.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(('PASS' if ok else 'FAIL'), '->', f'{H.dir}/report.md')
    return ok


def main():
    a = args(); H = Harness(a); H.done = False
    H.httpd = serve()
    print(f"stress: {', '.join(a['scen'])} x{a['reps']}, seed {a['seed']}, {a['renderer']}, {a['size']}, out {H.dir}", flush=True)
    try:
        with sync_playwright() as p:
            H.launch(p)
            H.step('boot', 0, 'cold start', lambda: dict(menu_s=H.boot()))   # (an empty cache: every file from the server)
            H.step('boot', 0, 'warm start', lambda: dict(menu_s=H.boot()))   # (the same files again: the browser's cache)
            for s in a['scen']:
                for rep in range(a['reps']):
                    SCENARIOS[s](H, rep)
                    if H.failed and any(k in ('crash', 'frameErr') for _, _, _, (k, _) in [(e['scenario'], 0, 0, er) for e in H.log for er in e['errors']]): raise RuntimeError('critical error: stopped')
            H.done = True
            H.b.close()
    except Exception as e:
        H.errors.append(('harness', f'{type(e).__name__}: {e}')); print('stopped:', e); traceback.print_exc()
        H.log.append(dict(scenario='harness', rep=0, step='stopped', dur=0, ok=False, info=None, errors=[('harness', str(e)[:500])]))
    finally:
        H.httpd.shutdown()
    return 0 if report(H) else 1


if __name__ == '__main__':
    sys.exit(main())
