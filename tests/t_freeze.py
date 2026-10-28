# 0.50: hunts the bugs that freeze a run (like 0.48's: the run starts, nothing moves). Every zone is started through the
# real menus (play screen -> zone card -> start -> 'Play' on the loading screen) with a profile that has everything
# (Dofus, treasure maps, relics' shop levels…), then the run must move: time going on, monsters, no frame error; the
# in-run screens are opened on the way (level-up, dice, pause, Musha, chest…). Prints FAIL lines; screenshots in out.
# usage: PORT=8799 python tools/checks/pw_test.py tests/t_freeze.py <out>   (env ZONES=a,b to test only some zones)
import json, os as _o
fails = []
def check(tag):
    st = pg.evaluate("JSON.stringify({ s: Game.state, t: Game.run ? +Game.run.time.toFixed(2) : -1, mobs: Game.run ? Game.run.mobs.length : 0, err: Game._frameErr || null })")
    st = json.loads(st); return st
url('fresh=1'); pg.wait_for_function('Game.state === "menu" && document.querySelector(".menu-buttons")', timeout=120000)
zones = pg.evaluate("Game.C.maps.map(m => m.id)")
only = _o.environ.get('ZONES'); zones = [z for z in zones if not only or z in only.split(',')]
classes = pg.evaluate("Game.C.classes.map(c => c.id)")
for i, z in enumerate(zones):
    cls = classes[i % len(classes)]
    pg.evaluate("""(([z, cls]) => { const S = Store.data, C = Game.C; S.unlocked = C.maps.map(m => m.id); S.lastClass = cls; S.lastMap = z;
      S.dofus = Object.fromEntries(C.dofus.map(d => [d.id, 1])); S.scrolls = Object.fromEntries(C.scrolls.map(s => [s.id, 4]));
      S.tmaps = { [z]: { x: 1500, y: 1200, found: false, t: 1 } }; S.kamas = 99999; Store.save(); UI.playScreen(); })""", [z, cls])
    time.sleep(0.8)
    pg.evaluate("(z => { const i = Game.C.maps.findIndex(m => m.id === z); const c = document.querySelectorAll('.maps .map-card')[i]; if (c) c.click(); })", z)
    pg.evaluate("(cls => { const c = [...document.querySelectorAll('.class-card')].find(e => e.textContent.trim().length && e.dataset && (e.dataset.id === cls)); if (c) c.click(); })", cls)
    pg.click('.screen.play .start-row .btn.orange:last-child')
    try:
        pg.wait_for_selector('.load-play', timeout=120000); time.sleep(0.3); pg.click('.load-play')
    except Exception as e: fails.append(f'{z}: no loading screen ({e})'); continue
    try: pg.wait_for_function('Game.run && Game.state === "run" && !Game.run.cine', timeout=30000)   # (0.53: the 3-2-1-GO countdown holds the run's clock)
    except Exception as e: fails.append(f'{z}: countdown never ended ({e})')
    time.sleep(3)
    a = check(z)
    if a['s'] != 'run' or a['t'] < 2 or a['err']: fails.append(f"{z} ({cls}): run did not move {a}")
    zid = pg.evaluate("Game.run && Game.run.map.id")
    if zid != z: fails.append(f'{z}: started {zid}')
    if i < 3 or z in ('bonta', 'koalak', 'grobe'): shot(f'run_{z}')
    # the in-run screens, one after the other
    for js in ["const R = Game.run; R.xp = R.xpNext; ", "UI.closeModal(); UI.levelUpOpen = false; Game.run.rerolls = 1; UI.levelUpMenu(Game.run, Game.run.upgradeOptions(3)); setTimeout(() => { const b = document.querySelector('.levelup .btn.reroll'); if (b) b.click(); }, 300);",
               "UI.closeModal(); UI.levelUpOpen = false; UI.pauseMenu();", "UI.closeModal(); Game.run.gotTmap && Game.run.gotTmap();",
               "UI.closeModal(); UI.levelUpOpen = false; Game.run.drainFx && Game.run.mobs[0] && Game.run.drainFx(Game.run.mobs[0]);"]:
        try: pg.evaluate(js + ' 0')
        except Exception as e: fails.append(f'{z}: {js[:40]} -> {e}')
        time.sleep(1.6)
    pg.evaluate("UI.closeModal(); UI.levelUpOpen = false; 0"); time.sleep(1.5)
    b = check(z)
    if b['err'] or b['t'] <= a['t']: fails.append(f"{z}: frozen after the screens {b}")
    print(z, cls, a, b, flush=True)
    pg.evaluate("Game.run && (Game.run.over = 'quit'); Game.endRun ? Game.endRun(false) : UI.mainMenu(); 0"); time.sleep(0.5)
    url('fresh=1'); pg.wait_for_function('Game.state === "menu" && document.querySelector(".menu-buttons")', timeout=120000)
print('FAILS', len(fails)); [print('FAIL', f) for f in fails]
