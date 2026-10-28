"""0.81 content: fewer level-up screens and a crescendo of ambers.
- spells and weapons: 6 levels -> 4 (MAX_SPELL_LV, spells.js). lv[0] stays, lv[1]+lv[2] and lv[3]+lv[4] are merged,
  lv[5] becomes lv[3]: every level is still cumulative (spellParams), so the maxed spell / weapon is exactly what it was.
  The vampiric weapons' life steal by level keeps the values of the old levels 1, 3, 5 and 6.
- characteristics with 5 levels -> 4, their per-level value x 5/4 (the maxed value is unchanged; Vol de vie also
  makes up for its growing factor), the '+x per level' numbers rewritten in the 7 languages.
- ambers (game.js normalAmber): worth C.run.amber.v0 x (1 + grow) ^ (30-second steps), the same on every map; each map
  drops wave[3] / ref of them a kill (game.js amberRate: the same ambers a second on every map for a player who kills
  everything); v0 / grow computed by tools/content/calc_amber081.py; the ancestral amber (elites, Archimonsters, bosses) = 5 x a normal one (bigAmberK).
usage: PYTHONUTF8=1 python tools/content/patch_081.py  (imports patch_079, writes game/data/content.json)"""
import sys as _sys, os as _os, re, json
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
import _root
import patch_079 as P9

C, G, T, put_ui = P9.C, P9.G, P9.T, P9.put_ui
LG = ['fr', 'en', 'de', 'es', 'it', 'nl', 'pt']


def merge4(lv):
    if not lv or len(lv) != 6: return lv
    m = lambda a, b: {**a, **b}
    return [lv[0], m(lv[1], lv[2]), m(lv[3], lv[4]), lv[5]]


n = 0
for s in C['spells'].values():
    if s.get('lv') and len(s['lv']) == 6: s['lv'] = merge4(s['lv']); n += 1
for w in C['weapons'] + C.get('uniqueWeapons', []):
    if len(w.get('lv') or []) == 6: w['lv'] = merge4(w['lv']); n += 1
    if isinstance(w.get('leech'), list) and len(w['leech']) == 6: w['leech'] = [w['leech'][i] for i in (0, 2, 4, 5)]
print('levels merged', n)


def fmt(v, lg):
    s = ('%.3f' % v).rstrip('0').rstrip('.')
    return s if lg == 'en' else s.replace('.', ',')


def renum(desc, old, new):
    """replace the first number equal to `old` (any language's decimal mark) by `new`, in every language"""
    for lg in LG:
        if lg not in desc: continue
        o, nn = fmt(old, lg), fmt(new, lg)
        pat = r'(?<![\d,.])' + re.escape(o) + r'(?![\d])'
        if not re.search(pat, desc[lg]): print('  !', lg, 'no', o, 'in', desc[lg][:60]); continue
        desc[lg] = re.sub(pat, nn, desc[lg], count=1)


NICE = {'pa': -0.044, 'soins': 0.31, 'prospection': 0.31}   # (x 5/4 rounded to a readable number)
for p in C['passives']:
    if p.get('max') != 5: continue
    old = p['per']
    k = 5 / 4 * (1.4 / 1.3 if p['stat'] == 'leech' else 1)   # (Vol de vie: x (1 + 0.1 (lv - 1)), 1.4 at 5, 1.3 at 4)
    p['per'] = NICE.get(p['id'], round(old * k, 6)); p['max'] = 4
    shown = {'maxhp': 100, 'growth': 100, 'might': 100, 'area': 100, 'luck': 100, 'crit': 100, 'cooldown': -100, 'speed': 100,
             'projspeed': 100, 'regen': 1, 'magnet': 100, 'armor': 1, 'duration': 100, 'leech': 100, 'reflect': 30, 'evade': 100}[p['stat']]
    a, b = abs(old * shown), abs(p['per'] * shown)
    if p['stat'] == 'area': a = 6.7; b = round(b, 1)
    if p['stat'] == 'leech': a = 0.027; b = round(b, 3)
    renum(p['desc'], round(a, 3), round(b, 3))
    if p['stat'] == 'magnet': p['greed'] = 0.125; renum(p['desc'], 10, 12.5)   # (+10 % kamas per level -> 12.5)
    print(p['id'], old, '->', p['per'], '|', p['desc']['fr'])

# ambers: see calib_amber081.py for the figures
R = C['run']
R['amber'] = {'v0': 0.0327, 'grow': 0.15, 'step': 30, 'ref': 0.34}   # (0.83, tools/content/calc_amber081.py: level 40 = everything maxed — 4 spells, the weapon, 5 characteristics — at 7:30)
R['bigAmberK'] = 5
R['rareAmberK'] = 5     # (0.82: the Ambre du Chêne Mou of the bosses = 5 x an ancestral one)
R['passiveSlots'] = 5  # (0.82: 5 characteristics, 4 spells — fusions included — and 1 weapon)
R['xpLate'] = None   # (the 30-second steps are the crescendo now)

if __name__ == '__main__':
    json.dump(C, open(f'{G}/data/content.json', 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
    print('0.81 ok')
