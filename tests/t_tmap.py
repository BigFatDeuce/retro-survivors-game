# 0.52: Musha l'Oni's treasure maps from end to end: a map drops (?tmap=<zone>), the player picks it up, Musha's scene
# shows the zone's mini map with the red cross; in the next run of that zone the cross is on the ground and digging on it
# gives the treasure; a cross saved outside a zone's bounds (Dark Vlad's zone was made smaller) is moved inside.
# usage: PORT=8799 python tools/checks/pw_test.py tests/t_tmap.py <out>   (env ZONE=astrub)
import json, os as _o
Z = _o.environ.get('ZONE', 'astrub'); fails = []
url(f'autostart=1&fresh=1&cls=iop&sex=0&map={Z}&tmap={Z}&god=1&t=3')
pg.wait_for_function('Game.run && Game.state === "run"', timeout=180000)
for _ in range(60):   # the map drops a few seconds in: walk onto it
    got = pg.evaluate("""(() => { const R = Game.run, p = R.pickups.find(p => p.kind === 'tmap'); if (p) { R.player.x = p.x; R.player.y = p.y; }
      return !!(Store.data.tmaps || {})[%r]; })()""" % Z)
    if got: break
    time.sleep(0.5)
time.sleep(1.5)
e = pg.evaluate("JSON.stringify((Store.data.tmaps || {})[%r] || null)" % Z); e = json.loads(e)
if not e: fails.append('no treasure map saved')
shot('tmap_musha')
red = pg.evaluate("""(() => { const c = document.querySelector('.musha .tmap-mini'); if (!c) return -1; const g = c.getContext('2d'), d = g.getImageData(0, 0, c.width, c.height).data;
  let n = 0; for (let i = 0; i < d.length; i += 4) if (d[i] > 200 && d[i + 1] < 60 && d[i + 2] < 60) n++; return n; })()""")
print('musha scene: red cross pixels', red, 'treasure', e)
if red <= 20: fails.append(f'no cross on the mini map ({red})')
for _ in range(6):
    if not pg.evaluate("!!document.querySelector('.musha')"): break
    pg.click('.musha .start-row .btn'); time.sleep(0.4)
# the next run of that zone: the cross on the ground, dig it
url(f'autostart=1&cls=iop&sex=0&map={Z}&god=1&t=3')
pg.wait_for_function('Game.run && Game.state === "run" && Game.run.time > 1', timeout=180000)
here = json.loads(pg.evaluate("JSON.stringify(Game.run.tmapHere)"))
print('next run: tmapHere', here)
if not here: fails.append('no cross in the next run')
else:
    k0 = pg.evaluate("Game.run.kamas")
    pg.evaluate("(() => { const R = Game.run; R.player.x = R.tmapHere.x + 150; R.player.y = R.tmapHere.y + 40; R.mobs.length = 0; })()")
    time.sleep(0.8); shot('tmap_cross')   # (the cross on the ground, the player next to it)
    for _ in range(40):
        pg.evaluate("(() => { const R = Game.run; if (R.tmapHere) { R.player.x = R.tmapHere.x + 4; R.player.y = R.tmapHere.y; } })()")
        if json.loads(pg.evaluate("JSON.stringify(Store.data.tmaps[%r])" % Z)).get('found'): break
        time.sleep(0.25)
    for _ in range(160):   # (0.68: the gold comes at the end of the 'treasure' cinematic, which starts 0.22 s after the dig; 30.2 s since 0.96)
        if pg.evaluate("Game.run.kamas") > k0: break
        time.sleep(0.25)
    k1 = pg.evaluate("Game.run.kamas"); found = json.loads(pg.evaluate("JSON.stringify(Store.data.tmaps[%r])" % Z)).get('found')
    print('dug', found, 'kamas', k0, '->', k1)
    if not found or k1 <= k0: fails.append('the treasure could not be dug')
    shot('tmap_dug')
# a cross saved outside Dark Vlad's smaller zone is moved inside its bounds
pg.evaluate("(() => { Store.data.tmaps.vlad = { x: 3500, y: 2050, found: false, t: 1 }; Store.data.unlocked = Game.C.maps.map(m => m.id); Store.save(); })()")
url('autostart=1&cls=iop&sex=0&map=vlad&god=1&t=3')
pg.wait_for_function('Game.run && Game.state === "run" && Game.run.time > 1', timeout=180000)
v = json.loads(pg.evaluate("JSON.stringify({h: Game.run.tmapHere, b: Game.run.bounds})"))
print('vlad cross', v)
if not v['h'] or not (v['b']['x0'] <= v['h']['x'] <= v['b']['x1'] and v['b']['y0'] <= v['h']['y'] <= v['b']['y1']): fails.append('vlad cross outside the zone')
pg.evaluate("UI.armory && UI.armory('tmaps')"); time.sleep(1.5); shot('tmap_armory')
print('FAILS', len(fails), fails)
