"""0.59: the safety net — one command, real assertions, exit code 0 only when everything passed (~2-3 min).
  1. the balance sim (node, the real game logic): every class 3 min on Astrub, then the release audit (GOD, 11 min:
     bosses, elites, Doom) on Astrub + Goultard for two classes — fails on any thrown error / audit FAIL / stat check.
  2. headless Chromium: the menu boots, then 3 short bot runs through autostart (Crâ + water fusion + poison arrows,
     Féca orbiters + bouncing bubble, Iop sword + water fusion: the shared neighbour buffer's paths) — fails on a page
     error, Game._frameErr, a missing file (HTTP >= 400) or a run that does not move; prints the load times and fps.
  3. --bench (or BENCH=1): 200 monsters on screen, CPU x1 and x4 (Chromium's throttling) — median fps and the main
     thread's ms, reported only (no pass / fail: it depends on the PC). 'poison' = the 0.58 audit's scenario (plain /
     poisoned / poisoned + bleeding); 'numbers' (0.60) = damage numbers kept at the run's cap (plain / values the text
     cache finds again / every value new). --bench=poison or --bench=numbers runs one of them.
usage: python tools/check.py [--bench[=name,…]] [--only-bench[=name,…]] [--no-sim] [--no-browser]
       env: CHROME (a Chromium executable), VW / VH (viewport, default 1920x1080), SOFT_GPU=1 (draw with SwiftShader,
       a software GPU: about a weak PC's integrated graphics)
The new headless Chromium (channel 'chromium') draws with the real GPU and does not wait for the screen's refresh, so
its fps go past 60 and show the frame's real cost; elsewhere (cloud machines, SwiftShader) they stop at 60."""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from _root import ROOT
import os, sys, time, json, subprocess, threading, functools, http.server, socketserver

ARGS = {a.split('=')[0] for a in sys.argv[1:]}
BENCH = '--bench' in ARGS or '--only-bench' in ARGS or os.environ.get('BENCH') == '1'
BENCH_ONLY = [n for a in sys.argv[1:] if a.startswith(('--bench=', '--only-bench=')) for n in a.split('=', 1)[1].split(',')]
SIM = '--no-sim' not in ARGS and '--only-bench' not in ARGS
BROWSER = '--no-browser' not in ARGS and '--only-bench' not in ARGS
VW, VH = int(os.environ.get('VW', '1920')), int(os.environ.get('VH', '1080'))
SOFT_GPU = os.environ.get('SOFT_GPU') == '1'
UNCAPPED = os.environ.get('UNCAPPED') == '1'
fails, report = [], []


def say(*a):
    print(*a, flush=True)


def fail(msg):
    fails.append(msg); say('  FAIL', msg)


# ---------------------------------------------------------------- 1. the sim
def sim():
    say('== sim')
    node = ['node', f'{ROOT}/tools/checks/sim_node.js']
    t0 = time.time()
    r = subprocess.run(node + ['all', 'astrub', '3'], capture_output=True, text=True, encoding='utf8', errors='replace')
    lines = [json.loads(l) for l in r.stdout.splitlines() if l.startswith('{')]
    ncls = len(json.load(open(f'{ROOT}/game/data/content.json', encoding='utf8'))['classes'])
    if r.returncode or len(lines) != ncls or 'Error' in r.stderr:
        fail(f'sim all astrub 3: exit {r.returncode}, {len(lines)}/{ncls} classes\n{r.stderr[-1500:]}')
    else:
        dead = [l['cls'] for l in lines if l['dead']]
        say(f'  all classes 3 min on Astrub: ok ({time.time() - t0:.0f} s; levels {min(l["lvl"] for l in lines)}-{max(l["lvl"] for l in lines)}, dead: {", ".join(dead) or "none"})')
    t0 = time.time()
    env = dict(os.environ, AUDIT='1', AUDIT_MAPS='astrub,goultard', AUDIT_CLS='cra,iop')
    r = subprocess.run(node + ['x', 'x', '11'], capture_output=True, text=True, encoding='utf8', errors='replace', env=env)
    out = r.stdout
    runs = next((l for l in out.splitlines() if l.startswith('RUNS')), '')
    stats = next((l for l in out.splitlines() if l.startswith('STATS')), '')
    if r.returncode or not runs.endswith('FAILS 0') or 'every characteristic' not in stats:
        fail(f'audit sim: exit {r.returncode}\n{out[-1500:]}\n{r.stderr[-1500:]}')
    else:
        say(f'  audit (GOD, 11 min, Astrub + Goultard, Cra + Iop): ok ({time.time() - t0:.0f} s): {runs}; {stats[6:]}')


# ---------------------------------------------------------------- the browser
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True; daemon_threads = True
    request_queue_size = 128   # (the default 5 refused connections when a page loads many files at once)


def serve():
    httpd = Server(('127.0.0.1', int(os.environ.get('PORT', '0'))), functools.partial(Quiet, directory=f'{ROOT}/game'))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def launch(p):
    args = ['--autoplay-policy=no-user-gesture-required', '--ignore-gpu-blocklist']
    exe = os.environ.get('CHROME') or next((c for c in ['/opt/pw-browsers/chromium-1194/chrome-linux/chrome'] if os.path.exists(c)), None)
    if exe: return p.chromium.launch(executable_path=exe, args=args + ['--use-gl=swiftshader', '--enable-unsafe-swiftshader'])
    if SOFT_GPU: args = args + ['--use-angle=swiftshader', '--enable-unsafe-swiftshader']
    if UNCAPPED: args = args + ['--disable-gpu-vsync', '--disable-frame-rate-limit']
    try: return p.chromium.launch(channel='chromium', args=args)   # the new headless mode: real GPU, frames not tied to vsync
    except Exception: return p.chromium.launch(args=args)


# median fps from the frame intervals over ms milliseconds
FPS = """(async (ms) => { const t = []; let last = performance.now(); const t0 = last;
  await new Promise(res => { const f = (now) => { t.push(now - last); last = now; if (now - t0 < ms) requestAnimationFrame(f); else res(); }; requestAnimationFrame(f); });
  t.shift(); t.sort((a, b) => a - b); return { med: +(1000 / t[t.length >> 1]).toFixed(1), p90: +(1000 / t[Math.floor(t.length * 0.9)]).toFixed(1), n: t.length }; })"""
READY = "typeof Game !== 'undefined' && Game.state === 'run' && Game.run && Game.run.time > 0.2"
STATE = "JSON.stringify({ s: Game.state, t: Game.run ? +Game.run.time.toFixed(1) : -1, mobs: Game.run ? Game.run.mobs.length : 0, over: !!(Game.run && Game.run.over), lv: Game.run ? Game.run.level : 0, err: Game._frameErr || null })"

RUNS = [   # (label, query): short bot runs that go through the code the audit found fragile
    ('cra + water fusion + poison arrows', 'cls=cra&weapon=arc&fusion=chance&spells=fleche_empoisonnee:6,fleche_magique:4&t=90'),
    ('feca orbiters + bouncing bubble', 'cls=feca&spells=bouclier_feca:6,bulle:6&t=60'),
    ('iop sword + water fusion', 'cls=iop&weapon=epee&fusion=chance&spells=epee_iop:6&t=100'),
]


def page_of(ctx, base, errs, bad):
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.on('response', lambda r: r.status >= 400 and bad.append(f'{r.status} {r.url.replace(base, "")}'))
    return pg


def browser_runs(p, base):
    say('== browser')
    b = launch(p)
    ctx = b.new_context(viewport={'width': VW, 'height': VH})
    errs, bad = [], []
    pg = page_of(ctx, base, errs, bad)
    t0 = time.time(); pg.goto(f'{base}/index.html?fresh=1')
    pg.wait_for_function("typeof Game !== 'undefined' && Game.state === 'menu' && document.querySelector('.menu-buttons')", timeout=120000)
    say(f'  main menu up in {time.time() - t0:.1f} s'); report.append(f'menu boot {time.time() - t0:.1f} s')
    gpu = pg.evaluate("(() => { try { const g = document.createElement('canvas').getContext('webgl'), e = g && g.getExtension('WEBGL_debug_renderer_info'); return e ? g.getParameter(e.UNMASKED_RENDERER_WEBGL) : '?'; } catch (e) { return '?'; } })()")
    say('  renderer:', gpu)
    for label, q in RUNS:
        t0 = time.time()
        pg.goto(f'{base}/index.html?autostart=1&fresh=1&map=astrub&bot=1&{q}')
        try: pg.wait_for_function(READY, timeout=120000)
        except Exception as e: fail(f'{label}: the run never started ({e})'); continue
        load = time.time() - t0
        if not pg.evaluate('PX.on'): fail(f'{label}: PixiJS did not start (the 2D canvas drew the run)')
        a = json.loads(pg.evaluate(STATE))
        f = pg.evaluate(FPS + '(12000)')
        time.sleep(3)
        z = json.loads(pg.evaluate(STATE))
        moved = z['t'] - a['t']
        say(f"  {label}: load {load:.1f} s, median {f['med']} fps (10 % slowest frames under {f['p90']}), run {a['t']} -> {z['t']} s, {z['mobs']} monsters, level {z['lv']}{', over' if z['over'] else ''}")
        report.append(f"{label}: load {load:.1f} s, median {f['med']} fps")
        if z['err']: fail(f'{label}: frame error {z["err"][:600]}')
        if moved < 8 and not z['over']: fail(f'{label}: the run did not move ({a} -> {z})')
        if z['mobs'] == 0 and not z['over']: fail(f'{label}: no monsters')
    for e in errs: fail(f'page error: {e[:400]}')
    for x in sorted(set(bad)): fail(f'missing file: {x}')
    b.close()


# ---------------------------------------------------------------- 3. the poison bench
SCENE = """(() => {
  const R = Game.run, P = R.player;
  Game.adapt = () => { }; Game.resScale = 1; Game.lowFx = Game.Q().fx === 0; Game.resize();   // full size, no adaptive resolution
  Game.debug.bot = 0; R.spawner = () => { }; R.spells = []; R.weapon = null; R.pendingLevels = 0;   // nobody moves, nothing new comes, nobody fights
  R.player.invulnUntil = 1e12; R.freezeUntil = 1e12; R.mobs.length = 0; R.bossQueue = [];
  const f0 = Game.frame; window._fw = []; Game.frame = function (dt) { const a = performance.now(); window._num && numbers(); f0.call(this, dt); window._fw.push(performance.now() - a); };   // the main thread's share
  const d0 = Run.prototype.draw; window._dw = []; Run.prototype.draw = function (c) { const a = performance.now(); d0.call(this, c); window._dw.push(performance.now() - a); };   // (0.61: of which drawing)
  // the numbers bench: damage numbers over random monsters, kept at the run's cap (R.text), 15 % crits; 'numbers' =
  // values 20-399 (the cache finds most of them again), 'numbers, all new' = every value new (a fresh bitmap each)
  let seq = 1000; const numbers = () => { for (let i = 0; i < 12; i++) { const m = R.mobs[Math.floor(Math.random() * R.mobs.length)], crit = Math.random() < 0.15;
    const v = window._num === 'new' ? seq++ : 20 + Math.floor(Math.random() * 380);
    if (crit) R.text(m.x, m.y - m.r * 2.6 - 10, v + '!', '#ffb02e', 18); else R.text(m.x, m.y - m.r * 2.6 - 6, v, '#ff4d3d', 14); } };
  const W = R.map.waves[R.map.waves.length - 1][2];
  for (let i = 0; i < 200; i++) { const x = P.x - 620 + (i % 20) * 65, y = P.y - 330 + Math.floor(i / 20) * 70 + (i % 2) * 20;
    const m = R.spawnMob(weighted(W), x, y, { force: true }); if (m) { m.hp = m.maxHp = 1e12; } }
  return R.mobs.length; })()"""
STATUS = """(k => { const R = Game.run; for (const m of R.mobs) { m.poisonUntil = k.includes('poison') ? 1e12 : 0; m.poisonDps = 0; m.bleedUntil = k.includes('bleed') ? 1e12 : 0; } return k; })"""
NUMBERS = """(k => { window._num = k === 'plain' ? 0 : k.includes('new') ? 'new' : 'mix'; Game.run.texts.length = 0; return k; })"""
BENCHES = {   # name: (setter, keys)
    'poison': (STATUS, ('plain', 'poison', 'poison+bleed')),
    'numbers': (NUMBERS, ('plain', 'numbers', 'numbers, all new')),
}
MED = '(k => { const a = window[k].slice().sort((x, y) => x - y); return a.length ? +a[a.length >> 1].toFixed(2) : 0; })'


def bench(p, base, name):
    setter, keys = BENCHES[name]
    say('== %s bench (200 monsters on screen, %dx%d, UHD%s%s)' % (name, VW, VH, ', software GPU' if SOFT_GPU else '', ', no frame cap' if UNCAPPED else ''))
    b = launch(p); rows = []
    for mode, mq in (('', ''),):
        ctx = b.new_context(viewport={'width': VW, 'height': VH})
        errs, bad = [], []
        pg = page_of(ctx, base, errs, bad)
        pg.goto(f'{base}/index.html?autostart=1&fresh=1&map=astrub&cls=iop&bot=1&q=uhd{mq}')   # (0.93: the web's default is 1080p now: the bench stays at UHD, comparable)
        pg.wait_for_function(READY, timeout=120000); time.sleep(1)
        if mq == '&pixi=1' and not pg.evaluate('PX.on'): fail('bench: PixiJS did not start')
        n = pg.evaluate(SCENE); say(f'  {n} monsters placed' + (f' ({mode})' if mode else ''))
        cdp = ctx.new_cdp_session(pg); lab = mode + ' ' if mode else ''
        for cpu in (1, 4):
            cdp.send('Emulation.setCPUThrottlingRate', {'rate': cpu})
            for k in keys:
                pg.evaluate(setter + f"('{k}')"); time.sleep(1)
                pg.evaluate('window._fw.length = 0; window._dw.length = 0')
                f = pg.evaluate(FPS + '(5000)')
                f['js'] = pg.evaluate(MED + "('_fw')"); f['draw'] = pg.evaluate(MED + "('_dw')")
                tx = f", {pg.evaluate('Game.run.texts.length')} numbers" if name == 'numbers' else ''
                rows.append((cpu, lab + k, f)); say(f"  CPU x{cpu} {lab + k:22s} median {f['med']:6.1f} fps   (10 % slowest frames under {f['p90']:.1f}; game code {f['js']:.2f} ms a frame, drawing {f['draw']:.2f}{tx})")
        cdp.send('Emulation.setCPUThrottlingRate', {'rate': 1})
        err = pg.evaluate('Game._frameErr || null')
        if err: fail(f'bench: frame error {err[:600]}')
        for e in errs: fail(f'bench page error: {e[:400]}')
        ctx.close()
    b.close()
    report.append(f'{name} bench: ' + ', '.join(f"x{c} {k} {f['med']} fps / {f['js']} ms" for c, k, f in rows))


def main():
    t0 = time.time()
    if SIM: sim()
    if BROWSER or BENCH:
        from playwright.sync_api import sync_playwright
        httpd = serve(); base = f'http://127.0.0.1:{httpd.server_address[1]}'
        try:
            with sync_playwright() as p:
                if BROWSER: browser_runs(p, base)
                for name in BENCH_ONLY or (BENCHES if BENCH else ()): bench(p, base, name)
        finally: httpd.shutdown()
    say(f'== {"PASS" if not fails else "FAIL"} ({len(fails)} failure{"s" if len(fails) != 1 else ""}, {time.time() - t0:.0f} s)')
    for f in fails: say('  -', f.splitlines()[0])
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    main()
