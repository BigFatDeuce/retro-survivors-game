import json
for cls in ['eniripsa', 'sacrieur', 'iop']:
    url(f'autostart=1&fresh=1&cls={cls}&map=astrub&t=90&lv=10')
    time.sleep(7)
    shot(f'run_{cls}')
    pg.keyboard.press('Space'); time.sleep(5.3)
    shot(f'run_{cls}_b')
url('autostart=1&fresh=1&cls=cra&map=astrub&t=30')
time.sleep(5)
pg.keyboard.press('Escape'); time.sleep(1)
shot('pause1280')
pg.evaluate("Game.togglePause(); Game.toMenu(); UI.shop()"); time.sleep(2)
shot('shop')
