for lvl in (100, 200):
    if lvl == 200: pg.evaluate("Store.data.aura200=1; Store.data.ach = Object.fromEntries(Game.C.achievements.map(a=>[a.id,1])); Store.save()")
    url('autostart=1&cls=iop&map=astrub&t=20' + ('' if lvl == 200 else '&fresh=1'))
    pg.wait_for_function('Game.run && Game.state==="run"', timeout=60000); time.sleep(1)
    pg.evaluate("const R=Game.run; R.spawner=()=>{}; R.mobs.length=0; R.spells.length=0;")
    time.sleep(3.2)
    for i in range(6):
        shot(f'a{lvl}_{i}', clip={'x':540,'y':230,'width':200,'height':200}); time.sleep(0.45)
