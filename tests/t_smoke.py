for c in ['iop','roublard','bandit','sram']:
    url(f'autostart=1&fresh=1&cls={c}&map=astrub&t=60'); time.sleep(8)
    print(c, pg.evaluate("Game.run && [Math.round(Game.run.time), Game.run.player.hp>0]"))
pg.evaluate("Game.paused=true; UI.pauseMenu && UI.pauseMenu()"); time.sleep(0.5); shot('pause')
print('\n'.join(l for l in logs if 'pageerror' in l))
