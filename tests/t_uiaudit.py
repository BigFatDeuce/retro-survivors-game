# 0.85: every menu and every tab, at the window size of the run (VW x VH): the window's box (it must
# not change between the tabs of one menu), the elements that scroll (at most one per tab, never nested), a scrollbar
# that shows for a moment after a change (sampled at 30 / 120 / 500 ms), windows cut by the screen, and clickable things
# the keyboard / controller navigation cannot reach (not in Nav.SEL). Prints one line per problem, then SUMMARY.
# usage: VW=2560 VH=1440 python tools/checks/pw_test.py tests/t_uiaudit.py <out>
import json
url('fresh=1')
pg.wait_for_function("typeof Game !== 'undefined' && Game.state === 'menu'", timeout=120000); time.sleep(1.5)
pg.evaluate("""(() => { const S = Store.data, C = Game.C; S.kamas = 999999; S.unlocked = C.maps.map(m => m.id); S.seen = S.seen || {};
  for (const id in C.monsters) S.seen[id] = 1; for (const id in C.bosses) S.seen[id] = 1; Store.save(); })()""")
PROBE = """JSON.stringify((() => { const W = innerWidth, H = innerHeight, win = document.querySelector('.modal .window') || document.querySelector('#ui .window') || document.querySelector('#ui .screen');
  const sc = []; for (const e of document.querySelectorAll('#ui *, .modal *')) { const cs = getComputedStyle(e); if (cs.display === 'none' || cs.visibility === 'hidden') continue;
    const b = e.getBoundingClientRect(); if (b.width < 4 || b.height < 4) continue;
    if (/(auto|scroll)/.test(cs.overflowY) && e.scrollHeight > e.clientHeight + 2) sc.push(e); }
  const nested = sc.filter(e => sc.some(o => o !== e && o.contains(e))).length;
  const b = win ? win.getBoundingClientRect() : null;
  const cut = [...document.querySelectorAll('.window')].filter(w => { const r = w.getBoundingClientRect(); return r.width > 4 && (r.bottom > H + 1 || r.top < -1 || r.right > W + 1 || r.left < -1); }).length;
  const SEL = Nav.SEL, unreach = [];
  for (const e of document.querySelectorAll('#ui *, .modal *')) { const cs = getComputedStyle(e); if (cs.cursor !== 'pointer' || cs.display === 'none' || cs.visibility === 'hidden') continue;
    const r = e.getBoundingClientRect(); if (r.width < 4 || r.height < 4) continue; if (e.matches(SEL) || e.closest(SEL)) continue;
    if ([...e.querySelectorAll(SEL)].length) continue; unreach.push((e.className || e.tagName).toString().slice(0, 40)); }
  return { box: b ? [Math.round(b.left), Math.round(b.top), Math.round(b.width), Math.round(b.height)] : null, scroll: sc.map(e => (e.className || e.tagName).toString().slice(0, 30)), nested, cut, unreach: [...new Set(unreach)].slice(0, 6), focus: !!(Nav.el && Nav.el.isConnected) }; })())"""
probs, menus = [], 0
def probe():
    return json.loads(pg.evaluate(PROBE))
def state(name):
    seen = []
    for dt in (0.03, 0.09, 0.38):
        time.sleep(dt); seen.append(probe())
    last = seen[-1]
    flick = any(len(s['scroll']) > len(last['scroll']) for s in seen[:-1])
    if flick: probs.append(f'{name}: scrollbar shows a moment ({[len(s["scroll"]) for s in seen]})')
    if len(last['scroll']) > 1: probs.append(f'{name}: {len(last["scroll"])} scrolling areas {last["scroll"]}')
    if last['nested']: probs.append(f'{name}: nested scrolling')
    if last['cut']: probs.append(f'{name}: window cut by the screen')
    if last['unreach']: probs.append(f'{name}: not reachable by keyboard / controller: {last["unreach"]}')
    return last
def menu(name, js, tabsel='.tabs:not(.subtabs) > .btn, .tabs:not(.subtabs) > button'):
    global menus; menus += 1
    pg.evaluate(js); time.sleep(0.8)
    base = state(name); shot(name)
    n = pg.evaluate(f"document.querySelectorAll('{tabsel}').length")
    boxes = {str(base['box'])}; print('MENU', name, 'tabs', n, 'box', base['box'], 'scroll', base['scroll'])
    for i in range(n):
        pg.evaluate(f"document.querySelectorAll('{tabsel}')[{i}].click()"); time.sleep(0.25)
        s = state(f'{name} tab {i}'); boxes.add(str(s['box']))
        sub = pg.evaluate("document.querySelectorAll('.tabs.subtabs > .btn, .tabs.subtabs > button').length")
        for j in range(min(sub, 3)):
            pg.evaluate(f"document.querySelectorAll('.tabs.subtabs > .btn, .tabs.subtabs > button')[{j}].click()"); time.sleep(0.2)
            s = state(f'{name} tab {i} sub {j}'); boxes.add(str(s['box']))
    # (0.94: within 1 px — the window's height is a fraction of the screen, a tab without a scrollbar rounds it 0.2 px
    # apart: not a visible change)
    bx = [json.loads(x) for x in boxes if x != 'None']
    if len(bx) > 1 and any(abs(a[k] - c[k]) > 1 for a in bx for c in bx for k in range(4)): probs.append(f'{name}: the window changes size between tabs {sorted(boxes)}')
menu('main', "UI.mainMenu()", '.nothing')
menu('play', "UI.playScreen()", '.nothing')
menu('bestiary', "UI.bestiary()")
menu('shop', "UI.shop()")
menu('armory', "UI.armory()")
menu('achievements', "UI.achievements()")
menu('stats', "UI.stats()")
menu('options', "UI.options()", '.nothing')
menu('controls', "UI.controls()")
menu('credits', "UI.credits()", '.nothing')
menu('profiles', "UI.profilesMenu()", '.nothing')
url('autostart=1&fresh=1&cls=iop&map=astrub&t=30')
pg.wait_for_function("Game.state === 'run' && Game.run && Game.run.time > 0.3", timeout=120000); time.sleep(4)
menu('pause', "Game.togglePause()", '.nothing'); pg.evaluate("Game.togglePause()"); time.sleep(0.3)
menu('levelup', "UI.levelUpMenu(Game.run, Game.run.upgradeOptions(4))", '.nothing'); pg.evaluate("UI.closeModal()")
menu('runover', """(() => { const R = Game.run, C = Game.C; R.relics = (C.relics || []).slice(0, 6); R.dofus = (C.dofus || []).slice(0, 3); R.time = 400; R.kills = 900; UI.runOverMenu(R, false, null); })()""", '.nothing')
for p in probs: print('PROB', p)
print('SUMMARY menus', menus, 'problems', len(probs))
print('\n'.join(l for l in logs if 'pageerror' in l))
