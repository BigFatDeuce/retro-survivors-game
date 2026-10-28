"""0.95 (performance with crowds of monsters and effects): a repeatable heavy scene and where its main-thread time goes.
Starts a run (real GPU, Chromium of check.py, a fresh profile), fills the map with N monsters (immortal: life x400), then
for D seconds measures, per frame, the game's own JavaScript time (Game.frame, split into Run.update and Run.draw) and
the frame interval; optionally a CPU profile (top functions by self time).
  python tools/checks/perf_probe.py [--n 380] [--secs 10] [--cpu 1|4] [--cls cra] [--renderer pixi|canvas] [--q uhd]
                                    [--fx full|low|min] [--profile] [--label before]
    the class's five spells at the top level and 3 bosses in the crowd; prints one JSON line (medians / p95 in ms, fps)
  python tools/checks/perf_probe.py --each spells|weapons|systems [--only id,id] [--n 300] [--secs 3.5] [--cpu 4]
    (0.95: 'which spells or other things slow the game down'): one run per class, the crowd kept the same, then
    every spell of the game alone at its top level (class spells with their class, the fusions with theirs, the global
    spells), or every weapon (level max + a finale), or the run's systems (bosses' attacks, elites, Archimonsters,
    statuses on the whole crowd…); each measured after a warm-up, with the entities it keeps alive (projectiles, zones,
    effects, particles, texts, summons…). Prints a table sorted by the extra main-thread time over the crowd alone, and
    writes work/perf/<each>-<date>.json
Compare lines of one session (the machine's state moves between days). CPU 4 = Chrome's CPU throttling, a stand-in for
a weak PC or a phone's main thread."""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import os, json, time, argparse, statistics, collections, datetime
from playwright.sync_api import sync_playwright
import check

SPELLS = {'cra': 'fleche_explosive:4,fleche_magique:4,fleche_enflammee:4,fleche_glacee:4,fleche_empoisonnee:4',
          'iop': 'epee_iop:4,colere_iop:4,epee_celeste:4,tempete_puissance:4,pression:4',
          'feca': 'bouclier_feca:4,bulle:4,glyphe_enflammee:4,attaque_nuageuse:4,glyphe_immobilisation:4',
          'roublard': 'explobombe:4,dagues_boomerang:4,tromblon:4,kaboom:4,grisou:4'}
FILL = """(n) => { const R = Game.run, P = R.player, ids = Object.keys(R.C.monsters).filter(k => !R.C.monsters[k].special).slice(0, 40); let k = 0;
  P.hp = P.maxHp = 1e9; R.stats.maxHp = 1e9;   // (the scene must last: the character never dies)
  R.doorDone = true; R.door = null; R.portalRun = false;   // (no door: the bot would walk into ToT's quiz)
  for (let i = 0; i < n; i++) { const a = i * 2.399, r = 140 + (i % 15) * 32; if (R.spawnMob(ids[i % ids.length], P.x + Math.cos(a) * r, P.y + Math.sin(a) * r * 0.7, { force: true })) k++; }
  for (const b of Object.keys(R.C.bosses).filter(b => !R.C.bosses[b].doom && !R.C.bosses[b].unused).slice(0, 3)) R.spawnBoss(b);
  for (const m of R.mobs) { m.hp = m.maxHp = m.maxHp * 400; }   // (they must not all die in the first seconds)
  return k; }"""
PROBE = """() => { const G = Game, R = Run.prototype, w = window.__pp = { f: [], u: [], d: [], dt: [], last: 0, cnt: {}, cntN: 0 };
  const F = G.frame, U = R.update, D = R.draw;
  const ARR = ['mobs', 'projs', 'eprojs', 'zones', 'strikes', 'slashes', 'beams', 'cones', 'orbiters', 'summons', 'traps', 'pickups', 'effects', 'particles', 'texts', 'rings', 'teles', 'allies', 'bombs', 'walls', 'tosses', 'dashes'];
  G.frame = function (dt) { const t0 = performance.now(); if (w.last) w.dt.push(t0 - w.last); w.last = t0; const r = F.call(this, dt); w.f.push(performance.now() - t0);
    const Rn = this.run; if (Rn && (w.f.length % 4 === 0)) { w.cntN++; for (const k of ARR) { const n = (Rn[k] || []).length; const c = w.cnt[k] || (w.cnt[k] = [0, 0]); c[0] += n; if (n > c[1]) c[1] = n; }
      if (typeof PX !== 'undefined' && PX.on) for (const [k, n] of [['LAYERS', PX.nl], ['boxes', PX.np]]) { const c = w.cnt[k] || (w.cnt[k] = [0, 0]); c[0] += n; if (n > c[1]) c[1] = n; } }   // (full-screen 2D layers / small 2D boxes sent to the GPU this frame)
    return r; };
  R.update = function (dt) { const t0 = performance.now(); const r = U.call(this, dt); w.u.push(performance.now() - t0); return r; };
  R.draw = function (c) { const t0 = performance.now(); const r = D.call(this, c); w.d.push(performance.now() - t0); return r; }; }"""
RESET = "() => { const w = window.__pp; w.f = []; w.u = []; w.d = []; w.dt = []; w.last = 0; w.cnt = {}; w.cntN = 0; }"
COLLECT = "() => { const w = window.__pp; const c = {}; for (const k in w.cnt) c[k] = [+(w.cnt[k][0] / Math.max(1, w.cntN)).toFixed(1), w.cnt[k][1]]; return { f: w.f, u: w.u, d: w.d, dt: w.dt, cnt: c, err: Game._frameErr }; }"
# --each: the run kept steady (no waves, elites, bosses, events, level-ups; the character takes no damage), then per item
# a clean slate: every entity of the previous item gone, a fresh crowd of N plain monsters around the character
STEADY = """() => { const R = Game.run, P = R.player;
  R.spawner = () => { }; R.updateElites = () => { }; R.bossQueue = []; R.events = []; R.secret = null; R.doorDone = true; R.door = null; R.portalRun = false;
  R.damagePlayer = () => { }; R.xpNext = 1e12; R.manuelAt = null; R.randEvents = []; R.nextRandEvent = 1e9; if (R.doom) R.doom = null;
  P.hp = P.maxHp = 1e9; return true; }"""
CLEAN = """(n) => { const R = Game.run, P = R.player;
  R.spells = []; R.weapon = null; R.charSprite.weapon = null; R.pendingLevels = 0; R.xp = 0; R.xpNext = 1e12; R.totBuff = null; R.fusion = null;
  for (const k of ['mobs', 'projs', 'eprojs', 'zones', 'strikes', 'slashes', 'beams', 'cones', 'digs', 'cawottes', 'orbiters', 'summons', 'traps', 'pickups', 'effects', 'particles', 'texts', 'rings', 'teles', 'allies', 'bombs', 'walls', 'tosses', 'dashes']) if (Array.isArray(R[k])) R[k].length = 0;
  R.bossAlive = []; R.mutant = null; R.dyingN = 0; R.freezeUntil = 0; R.recompute(); P.hp = P.maxHp = 1e9;
  const ids = Object.keys(R.C.monsters).filter(k => !R.C.monsters[k].special && !R.C.monsters[k].boss).slice(0, 40); let k = 0;
  for (let i = 0; i < n; i++) { const a = i * 2.399, r = 140 + (i % 15) * 32; const m = R.spawnMob(ids[i % ids.length], P.x + Math.cos(a) * r, P.y + Math.sin(a) * r * 0.7, { force: true, noArchi: true }); if (m) { m.hp = m.maxHp = m.maxHp * 400; k++; } }
  return k; }"""
GIVE = """([kind, id]) => { const R = Game.run, C = R.C;
  if (kind === 'spell') { const d = C.spells[id]; if (!d) return 'no spell'; if (d.t === 'wheel') { R.trool(); return 'wheel'; }
    const s = R.addSpell(id); for (const f of d.fx || []) FxSheets.load(f); while (s.level < MAX_SPELL_LV) s.levelUp(); s.cd = 0.05; return d.t; }
  if (kind === 'weapon') { R.applyUpgrade({ kind: 'weapon', id }); for (let i = 1; i < MAX_SPELL_LV; i++) R.weapon.levelUp();
    const E = ((C.weaponEvo || {})[id] || [])[0]; if (E) R.applyUpgrade({ kind: 'wevo', id: E.id }); R.weapon.cd = 0.05; return R.weapon.def.t; }
  return SYSTEMS[id] ? SYSTEMS[id](R) : 'no system'; }"""
# the run's systems, one at a time over the same crowd (with the class's first spell at its top level, as in a real run)
SYSTEMS_JS = """window.SYSTEMS = {
  none: R => 'crowd',
  spell1: R => { const s = R.addSpell(R.cls.spells[0]); while (s.level < MAX_SPELL_LV) s.levelUp(); return 'first spell'; },
  boss: R => { const id = R.map.bosses[R.map.bosses.length - 1][1]; R.spawnBoss(id); return id; },
  bosses3: R => { for (const b of R.map.bosses.slice(0, 3)) R.spawnBoss(b[1]); return 'x3'; },
  elites: R => { const E = R.C.elites; delete R.updateElites; R.eliteT = 0.5; return 'elites'; },
  archi: R => { const K = R.C.archiCfg, r0 = K.rate; K.rate = 1e9; for (const m of R.mobs) if (Math.random() < 0.25) R.maybeArchi(m); K.rate = r0; return 'archi ' + R.mobs.filter(m => m.archi).length; },
  poison: R => { for (const m of R.mobs) { m.poisonUntil = R.time + 60; m.poisonDps = 1; } return 'poison all'; },
  burn: R => { for (const m of R.mobs) { m.burnUntil = R.time + 60; m.burnDps = 1; } return 'burn all'; },
  bleed: R => { for (const m of R.mobs) { m.bleedUntil = R.time + 60; m.bleedDps = 1; } return 'bleed all'; },
  slow: R => { for (const m of R.mobs) { m.slowUntil = R.time + 60; m.slowAmt = 0.4; } return 'slow all'; },
  stun: R => { for (const m of R.mobs) { m.stunUntil = R.time + 60; } return 'stun all'; },
  confuse: R => { for (const m of R.mobs) { m.confuseUntil = R.time + 60; } return 'confuse all'; },
  pickups: R => { const P = R.player; for (let i = 0; i < 300; i++) R.dropGem(P.x + Math.cos(i) * (80 + i), P.y + Math.sin(i) * (60 + i * 0.7), 1); return 'ambers ' + R.pickups.length; },
  bworks: R => { R.startEvent('bworks'); return 'event'; }, tofus: R => { R.startEvent('tofus'); return 'event'; },
  kamarain: R => { R.startEvent('kamarain'); return 'event'; }, eclipse: R => { R.startEvent('eclipse'); return 'event'; },
  texts: R => { R._txT = setInterval(() => { const P = R.player; for (let i = 0; i < 12; i++) R.text(P.x + Math.random() * 600 - 300, P.y + Math.random() * 400 - 200, String(Math.floor(Math.random() * 99999)), '#fff', 14); }, 50); return 'damage numbers'; },
  mutant: R => { R.spawnMutant(); return R.mutant ? R.mutant.def.id : 'none'; },
};"""
EACH_SYSTEMS = ['none', 'spell1', 'boss', 'bosses3', 'elites', 'archi', 'poison', 'burn', 'bleed', 'slow', 'stun', 'confuse', 'pickups', 'texts', 'mutant',
                'bworks', 'tofus', 'kamarain', 'eclipse']


def top_profile(prof, n=30, nat=25, indent=''):
    """self time by function (samples x interval), then the natives by caller (who draws / uploads)"""
    nodes = {nd['id']: nd for nd in prof['nodes']}; self_t = collections.Counter(); dts = prof.get('timeDeltas') or []
    for sid, d in zip(prof.get('samples') or [], dts):
        cf = nodes[sid]['callFrame']; self_t[f"{cf['functionName'] or '(anon)'} {cf['url'].split('/')[-1].split('?')[0]}:{cf['lineNumber'] + 1}"] += d / 1000
    tot = sum(v for k, v in self_t.items() if not k.startswith('(idle)')) or 1
    for k, v in self_t.most_common(n):
        if not k.startswith('(idle)'): print(f'{indent}{v:8.1f} ms {100 * v / tot:5.1f} %  {k}')
    par = {c: nd['id'] for nd in prof['nodes'] for c in nd.get('children', [])}; via = collections.Counter()
    for sid, d in zip(prof.get('samples') or [], dts):
        cf = nodes[sid]['callFrame']
        if cf['url'] or cf['functionName'] in ('(idle)', '(program)', '(garbage collector)', ''): continue
        pc = nodes.get(par.get(sid), {}).get('callFrame', {}); via[f"{cf['functionName']} <- {pc.get('functionName') or '(anon)'} {pc.get('url', '').split('/')[-1].split('?')[0]}:{pc.get('lineNumber', 0) + 1}"] += d / 1000
    print(f'{indent}-- natives by caller'); [print(f'{indent}{v:8.1f} ms  {k}') for k, v in via.most_common(nat)]


def stats(a):
    a = sorted(a); return {'med': round(statistics.median(a), 2), 'mean': round(statistics.fmean(a), 2), 'p95': round(a[int(len(a) * 0.95)], 2)} if a else {}


def open_run(p, a, cls, extra=''):
    b = check.launch(p); pg = b.new_page(viewport={'width': 1920, 'height': 1080})
    cdp = pg.context.new_cdp_session(pg)
    # (--each starts at 2:20, before ToT's door at 2:30: the bot walked into its portal before the run was made steady)
    q = f"autostart=1&fresh=1&bot=1&cls={cls}&map={a.map}&t={140 if a.each else 200}&q={a.q}&pixi={1 if a.renderer == 'pixi' else 0}" + (f'&fx={a.fx}' if a.fx else '') + extra
    pg.goto(f'http://127.0.0.1:{a.port}/index.html?{q}'); pg.wait_for_function('typeof Game !== "undefined" && Game.run && Game.state === "run"', timeout=90000)
    return b, pg, cdp


def each(a):
    """every spell / weapon / system alone over the same crowd; a table of the extra main-thread time per item"""
    C = json.load(open(f'{ROOT}/game/data/content.json', encoding='utf8'))
    only = set(a.only.split(',')) if a.only else None
    if a.each == 'spells':
        plan = collections.OrderedDict()
        for c in C['classes']: plan.setdefault(c['id'], []).extend(('spell', s) for s in c['spells'])
        for f in C.get('spellFusions', []): plan.setdefault(f['cls'] or C['classes'][0]['id'], []).append(('spell', f['id']))   # (0.95: cls None: any class)
        plan.setdefault(C['classes'][0]['id'], []).extend(('spell', g['id']) for g in C.get('globalSpells', []))
    elif a.each == 'weapons':
        plan = {'iop': [('weapon', w['id']) for w in C['weapons'] + C.get('uniqueWeapons', [])]}
    else:
        plan = {a.cls: [('system', s) for s in EACH_SYSTEMS]}
    for k in plan: plan[k] = [('system', 'none')] + [it for it in plan[k] if not only or it[1] in only]   # (each class's own baseline: the crowd alone)
    plan = {k: v for k, v in plan.items() if len(v) > 1 or a.each == 'systems'}
    rows = []
    with sync_playwright() as p:
        for cls, items in plan.items():
            b, pg, cdp = open_run(p, a, cls)
            time.sleep(1.5); pg.evaluate(STEADY); pg.evaluate(SYSTEMS_JS); pg.evaluate(PROBE)
            # (a boss due before t=200 came at once with its intro cinematic: the run is frozen until it ends)
            pg.wait_for_function('Game.state === "run" && !Game.run.cine && !UI.modalOpen() && !Game.run.tofuShowUntil', timeout=60000)
            if a.cpu > 1: cdp.send('Emulation.setCPUThrottlingRate', {'rate': a.cpu})
            base = None
            for kind, iid in items:
                pg.evaluate("() => { if (Game.run._txT) { clearInterval(Game.run._txT); Game.run._txT = null; } }")
                n = pg.evaluate(CLEAN, a.n); what = pg.evaluate(GIVE, [kind, iid])
                time.sleep(a.warm); pg.evaluate(RESET)
                if a.profile: cdp.send('Profiler.enable'); cdp.send('Profiler.setSamplingInterval', {'interval': 200}); cdp.send('Profiler.start')
                time.sleep(a.secs)
                prof = cdp.send('Profiler.stop')['profile'] if a.profile else None
                w = pg.evaluate(COLLECT)
                if w['err']: print('FRAME ERROR', cls, iid, w['err'][:300]); pg.evaluate('Game._frameErr = null')
                if len(w['u']) < len(w['f']) * 0.8: print('FROZEN (run not updated: a cinematic or a window)', cls, iid)
                r = {'cls': cls, 'kind': kind, 'id': iid, 't': what, 'mobs': n, 'frames': len(w['f']), 'frame_js': stats(w['f'][3:]), 'update': stats(w['u'][3:]),
                     'draw': stats(w['d'][3:]), 'interval': stats(w['dt'][3:]), 'cnt': {k: v for k, v in w['cnt'].items() if v[1] and k != 'mobs'}, 'err': bool(w['err'])}
                if iid == 'none' and kind == 'system': base = r
                r['extra'] = round(r['frame_js'].get('mean', 0) - (base or r)['frame_js'].get('mean', 0), 2)   # (the mean: the median moves by 0.1 ms steps)
                r['extra95'] = round(r['frame_js'].get('p95', 0) - (base or r)['frame_js'].get('p95', 0), 2)
                name = C['spells'].get(iid, {}).get('name', {}).get('fr', '') if kind == 'spell' else ''
                r['name'] = name
                rows.append(r); print(f"{cls:9} {iid:26} {str(what)[:12]:12} js {r['frame_js'].get('mean')} ms (+{r['extra']}, p95 +{r['extra95']})  upd {r['update'].get('med')}  draw {r['draw'].get('med')}  "
                                      + ' '.join(f'{k}:{v[0]}/{v[1]}' for k, v in r['cnt'].items()), flush=True)
                if prof and iid != 'none': top_profile(prof, 18, 12, '      ')
            b.close()
    os.makedirs(f'{ROOT}/work/perf', exist_ok=True)
    out = f"{ROOT}/work/perf/{a.each}-{datetime.datetime.now():%Y%m%d-%H%M}.json"
    json.dump({'args': vars(a), 'rows': rows}, open(out, 'w', encoding='utf8'), ensure_ascii=False, indent=1)
    print('\n== sorted by extra main-thread time (mean, ms over the crowd alone)')
    for r in sorted((r for r in rows if r['id'] != 'none'), key=lambda r: -r['extra'])[:40]:
        print(f"{r['extra']:+7.2f}  p95 {r['extra95']:+7.2f}  upd {r['update'].get('med', 0):5.2f} draw {r['draw'].get('med', 0):5.2f}  {r['cls']:9} {r['id']:26} {r['name'][:28]}")
    print('->', out)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--n', type=int, default=None); ap.add_argument('--secs', type=float, default=None)
    ap.add_argument('--cpu', type=int, default=None); ap.add_argument('--cls', default='cra'); ap.add_argument('--renderer', default='pixi')
    ap.add_argument('--q', default=None); ap.add_argument('--profile', action='store_true'); ap.add_argument('--label', default='')
    ap.add_argument('--fx', default=''); ap.add_argument('--map', default='astrub')
    ap.add_argument('--each', choices=['spells', 'weapons', 'systems']); ap.add_argument('--only', default=''); ap.add_argument('--warm', type=float, default=1.5)
    a = ap.parse_args()
    # (--each defaults: a smaller crowd, shorter windows, CPU x4 and 1080p — many items to go through)
    E = bool(a.each); a.n = a.n or (300 if E else 380); a.secs = a.secs or (3.5 if E else 10); a.cpu = a.cpu or (4 if E else 1); a.q = a.q or ('hd' if E else 'uhd')
    httpd = check.serve(); a.port = httpd.server_address[1]
    if E: each(a); httpd.shutdown(); return
    with sync_playwright() as p:
        b, pg, cdp = open_run(p, a, a.cls, f"&spells={SPELLS[a.cls]}" if a.cls in SPELLS else '')
        time.sleep(2); n = pg.evaluate(FILL, a.n); time.sleep(1.5)
        if a.cpu > 1: cdp.send('Emulation.setCPUThrottlingRate', {'rate': a.cpu})
        pg.evaluate(PROBE)
        if a.profile: cdp.send('Profiler.enable'); cdp.send('Profiler.setSamplingInterval', {'interval': 200}); cdp.send('Profiler.start')
        time.sleep(a.secs)
        prof = cdp.send('Profiler.stop')['profile'] if a.profile else None
        w = pg.evaluate('({ f: __pp.f, u: __pp.u, d: __pp.d, dt: __pp.dt, mobs: Game.run.mobs.length, parts: Game.run.particles.length, err: Game._frameErr })')
        b.close()
    httpd.shutdown()
    dt = stats(w['dt'][5:])
    out = {'label': a.label, 'renderer': a.renderer, 'cpu': a.cpu, 'q': a.q, 'mobs': w['mobs'], 'frames': len(w['f']),
           'fps': round(1000 / dt['med'], 1) if dt else 0, 'interval': dt, 'frame_js': stats(w['f'][5:]), 'update': stats(w['u'][5:]), 'draw': stats(w['d'][5:]), 'err': w['err']}
    print(json.dumps(out))
    if prof: top_profile(prof)


if __name__ == '__main__':
    main()
