# 0.59: the level-up window with 4 cards (and the reroll) must fit the screen without scrolling, on a phone held upright
# (390x844) as on a PC; also checks that a permanent spell's duration reads 'permanent' on its card.
# (0.95: 'scrolls' = overflow auto / scroll and taller content, as t_noscroll / t_uiaudit: the modal windows' corner
# diamonds, .window.modal::after at inset -13px, stick out of a window that cannot scroll and counted as 13 px of scroll)
# The 4 cards are the long kind (French by default: env LG): a new spell, a new unique weapon, a new global spell and a
# characteristic with its description + real numbers.
# usage: VW=390 VH=844 DPR=3 MOBILE=1 python tools/checks/pw_test.py tests/t_levelup.py <out>   (prints FAIL lines; shot levelup.png)
import json, os
url('autostart=1&fresh=1&cls=sacrieur&map=astrub&t=30')
pg.wait_for_function("typeof Game !== 'undefined' && Game.state === 'run' && Game.run && Game.run.time > 0.3", timeout=120000)
time.sleep(1)
pg.evaluate("""(lg => { setLang(lg); const R = Game.run, C = Game.C; R.rerolls = 2;
  const uw = C.uniqueWeapons.slice().sort((a, b) => (L(b.desc).length + L(b.name).length) - (L(a.desc).length + L(a.name).length))[0];
  const gs = C.globalSpells.map(g => C.spells[g.id]).filter(Boolean).sort((a, b) => L(b.desc).length - L(a.desc).length)[0];
  const ps = C.passives.filter(p => ['reflect', 'luck', 'evade', 'amount', 'growth'].includes(p.stat)).sort((a, b) => L(b.desc).length - L(a.desc).length)[0];
  const opts = [{ kind: 'spell', id: R.cls.spells[1], lv: 1, isNew: true }, { kind: 'weapon', id: uw.id, lv: 1 },
    { kind: 'spell', id: gs.id, lv: 1, isNew: true }, { kind: 'passive', id: ps.id, lv: 1 }];
  UI.levelUpMenu(R, opts); })""" + f"('{os.environ.get('LG', 'fr')}')")
time.sleep(1.2)
shot('levelup')
r = json.loads(pg.evaluate("""JSON.stringify((() => { const W = innerWidth, H = innerHeight, el = document.querySelector('.window.modal.levelup');
  const cards = [...document.querySelectorAll('.up-card')].map(c => c.getBoundingClientRect()), w = el.getBoundingClientRect(), rr = document.querySelector('.reroll-row');
  const out = cards.map((b, i) => (b.top < -1 || b.bottom > H + 1 || b.left < -1 || b.right > W + 1) ? `card ${i + 1} outside the screen (${Math.round(b.left)},${Math.round(b.top)} - ${Math.round(b.right)},${Math.round(b.bottom)}) in ${W}x${H}` : null).filter(Boolean);
  if (w.bottom > H + 1 || w.top < -1) out.push(`window ${Math.round(w.top)}-${Math.round(w.bottom)} taller than the screen ${H}`);
  for (const e of [el, el.querySelector('.content'), document.querySelector('.modal-wrap')]) if (e && /(auto|scroll)/.test(getComputedStyle(e).overflowY) && e.scrollHeight > e.clientHeight + 2) out.push(`${e.className} scrolls (${e.scrollHeight} > ${e.clientHeight})`);
  if (rr) { const b = rr.getBoundingClientRect(); if (b.bottom > H + 1) out.push('the reroll button is below the screen'); }
  const tiny = [...document.querySelectorAll('.up-name')].filter(n => parseFloat(getComputedStyle(n).fontSize) < 10).length; if (tiny) out.push(tiny + ' card names under 10 px');
  return { fails: out, cards: cards.map(b => [Math.round(b.width), Math.round(b.height)]), win: [Math.round(w.width), Math.round(w.height)] }; })())"""))
print('cards', r['cards'], 'window', r['win'])
perm = pg.evaluate("realSummary(Game.run, Game.C.spells.faux_spin)")
print('faux_spin:', perm)
if '000' in perm: r['fails'].append('permanent duration shown as a number: ' + perm)
for f in r['fails']: print('FAIL', f)
print('FAILS', len(r['fails']))
print('\n'.join(l for l in logs if 'pageerror' in l))
