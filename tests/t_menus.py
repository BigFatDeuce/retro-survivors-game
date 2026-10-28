import os
lang=os.environ.get('LG','de')
url('fresh=1'); time.sleep(5)
pg.evaluate(f"setLang('{lang}')")
pg.evaluate("Nav.enabled=true")
for scr in ['mainMenu','playScreen','shop','bestiary','achievements','stats','controls','options','armory','credits']:
    pg.evaluate(f"UI.{scr}()"); time.sleep(1.2)
    pg.evaluate("Nav.el=null; Nav.ensure(); Nav.move(0,1); Nav.move(1,0)"); time.sleep(0.3)
    shot(scr)
# overlaps: elements whose boxes overflow the window or overlap siblings
print(pg.evaluate("typeof setLang"), pg.evaluate("LANG"))
print('\n'.join(l for l in logs if 'pageerror' in l))
