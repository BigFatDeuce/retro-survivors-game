# 0.65 (what fits a 16:9 screen must not scroll): opens the menus on a 16:9 window and lists every element that
# scrolls (scrollHeight > clientHeight + 2 with overflow auto / scroll) and anything cut by the screen. Menus: options,
# bestiary (the longest monster description), end screen (victory, every stat, 8 damage rows, achievements, relics),
# shop, armory, achievements, statistics, controls, credits, pause.
# usage: [VW=1920 VH=1080] python tools/checks/pw_test.py tests/t_noscroll.py <out>   (prints SCROLL / CUT lines, shots per menu)
import json
url('fresh=1')
pg.wait_for_function("typeof Game !== 'undefined' && Game.state === 'menu'", timeout=120000); time.sleep(1.5)
CHECK = """JSON.stringify((() => { const out = [], W = innerWidth, H = innerHeight;
  for (const e of document.querySelectorAll('#ui *, .modal *, .modal')) {
    const cs = getComputedStyle(e); if (cs.display === 'none' || cs.visibility === 'hidden') continue;
    const b = e.getBoundingClientRect(); if (b.width < 4 || b.height < 4) continue;
    if (/(auto|scroll)/.test(cs.overflowY) && e.scrollHeight > e.clientHeight + 2) out.push('SCROLL ' + (e.className || e.tagName) + ' ' + e.scrollHeight + '>' + e.clientHeight);
    if (e.classList.contains('window') && (b.bottom > H + 1 || b.top < -1)) out.push('CUT ' + e.className + ' ' + Math.round(b.top) + '..' + Math.round(b.bottom) + ' / ' + H);
  }
  return out; })())"""
def check(name, js, wait=1.2):
    pg.evaluate(js); time.sleep(wait); shot(name)
    r = json.loads(pg.evaluate(CHECK))
    print(f'== {name}: ' + ('ok' if not r else ''))
    for l in r[:12]: print('   ' + l)
check('options', "UI.options()")
check('credits', "UI.credits()")
check('bestiary', """(() => { UI.bestiary(); const C = Game.C; const ms = Object.values(C.monsters || {});
  Store.data.seen = Store.data.seen || {}; for (const m of ms) Store.data.seen[m.id] = 1;
  UI.bestiary(); const it = [...document.querySelectorAll('.best-item, .best-list > *')]; const lens = it.map(e => e.textContent.length);
  const pick = it.find(e => /Kralamoure|Craqueleur|Dark Vlad|Goultard/.test(e.textContent)) || it[0]; if (pick) pick.click(); })()""")
check('shop', "UI.shop()")
check('armory', "UI.armory()")
check('achievements', "UI.achievements()")
check('stats', "UI.stats()")
check('controls', "UI.controls()")
url('autostart=1&fresh=1&cls=iop&map=astrub&t=30')
pg.wait_for_function("Game.state === 'run' && Game.run && Game.run.time > 0.3", timeout=120000); time.sleep(1)
check('pause', "Game.togglePause()")
pg.evaluate("Game.togglePause()"); time.sleep(0.3)
check('runover', """(() => { const R = Game.run, C = Game.C; R.ps = R.ps || {}; Object.assign(R.ps, { bosses: 5, elites: 12, chests: 3, bestCombo: 187, kills: 2400 });
  R.kills = 2400; R.kamas = 12345; R.level = 41; R.time = 612; R.dmgBy = {}; Object.keys(C.spells).slice(0, 10).forEach((k, i) => R.dmgBy[k] = 100000 / (i + 1));
  R._startedAt = 0; Store.data.ach = Store.data.ach || {}; (C.achievements || []).slice(0, 6).forEach(a => Store.data.ach[a.id] = Date.now() + 1e9);
  R.relics = (C.relics || []).slice(0, 6); R.dofus = (C.dofus || []).slice(0, 3); UI.runOverMenu(R, true, null); })()""", 3.5)
print('\n'.join(l for l in logs if 'pageerror' in l))
