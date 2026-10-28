# 0.62: every level-up card the game can deal (each spell new and at levels 2-6, each weapon, characteristic, weapon
# fusion, spell fusion, finale) shown four at a time: none may have a cut text (description taller than its box, or
# content past the card), on a PC as on a phone (fitCards, ui.js). Prints FAIL lines and FAILS <n>.
# usage: [VW=390 VH=844 MOBILE=1] [LG=en] python tools/checks/pw_test.py tests/t_cards.py <out>
import json, os
url('autostart=1&fresh=1&cls=sacrieur&map=astrub&t=30&weapon=epee&spells=furie:5,attirance:5,absorption:5,epee_volante:5,assaut:5,faux_spin:3')   # (many spells owned: long synergy lines, as in a real run)
pg.wait_for_function("typeof Game !== 'undefined' && Game.state === 'run' && Game.run && Game.run.time > 0.3", timeout=120000)
time.sleep(1)
n = pg.evaluate("""(lg => { setLang(lg); const R = Game.run, C = Game.C, o = [];
  for (const id in C.spells) { const sp = C.spells[id]; if (!sp.lv && !sp.base) continue; o.push({ kind: 'spell', id, lv: 1 }); for (let l = 2; l <= MAX_SPELL_LV; l++) o.push({ kind: 'spell', id, lv: l }); }
  for (const w of [...(C.weapons || []), ...(C.uniqueWeapons || [])]) { o.push({ kind: 'weapon', id: w.id, lv: 1 }); o.push({ kind: "weapon", id: w.id, lv: MAX_SPELL_LV }); }
  for (const p of C.passives) for (let l = 1; l <= Math.min(4, p.max || 4); l++) o.push({ kind: 'passive', id: p.id, lv: l });
  for (const f of C.fusions || []) o.push({ kind: 'fusion', id: f.id, lv: 1 });
  for (const f of C.spellFusions || []) o.push({ kind: 'sfusion', id: f.id, lv: 1 });
  window._cards = o; return o.length; })""" + f"('{os.environ.get('LG', 'fr')}')")
print('cards', n)
CHECK = """JSON.stringify([...document.querySelectorAll('.up-cards .up-card')].map(c => { const d = c.querySelector('.up-desc'), n = c.querySelector('.up-name');
  const cut = d && !c.classList.contains('scrolly') && d.scrollHeight > d.clientHeight + 1, past = c.scrollHeight > c.clientHeight + 1;
  return [cut, past, n ? n.textContent : '?', d ? parseFloat(getComputedStyle(d).fontSize) : 0, c.className.replace('up-card', '').trim(), c.offsetHeight]; }))"""
fails, sizes, heights = [], [], []
for i in range(0, n, 4):
    try:
        pg.evaluate(f"(() => {{ const R = Game.run; if (UI.levelUpOpen) UI.closeModal(); UI.levelUpMenu(R, window._cards.slice({i}, {i + 4}).map(o => ({{ ...o }}))); }})()")
    except Exception as e:
        fails.append(f'cards {i}-{i + 3}: {str(e)[:160]}'); continue
    time.sleep(0.7)
    for cut, past, name, fs, cls, hh in json.loads(pg.evaluate(CHECK)):
        sizes.append(fs); heights.append(hh)
        if cut or past: fails.append(f'{name} ({cls}): ' + ('description cut' if cut else 'content past the card'))
    if i == 0: shot('cards0')
print('font sizes: min', min(sizes), 'median', sorted(sizes)[len(sizes) // 2], '| card heights: min', min(heights), 'max', max(heights))
for f in fails[:60]: print('FAIL', f)
print('FAILS', len(fails))
print('\n'.join(l for l in logs if 'pageerror' in l))
