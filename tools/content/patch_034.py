"""Beta 0.36 content, applied on top of patch_033.   usage: python tools/content/patch_034.py"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
import _root
import json
import patch_033 as P3

C, T, G = P3.C, P3.T, P3.G

# credits: where the Gelano is
_ADD = T(' (Sûrement dans une poubelle.)', ' (Probably in a bin.)', ' (Wahrscheinlich in einer Mülltonne.)', ' (Seguramente en una papelera.)', ' (Probabilmente in un bidone.)', ' (Waarschijnlijk in een vuilnisbak.)', ' (Provavelmente num caixote do lixo.)')
for lg in C['ui']:
    if not C['ui'][lg]['cr7'].endswith(_ADD[lg]): C['ui'][lg]['cr7'] += _ADD[lg]

# every class hits 5 % harder
for c in C['classes']: c['base']['might'] = round(c['base'].get('might', 1.0) * 1.05, 4)

# the skin merchant: 6 skins, gone 15 s (of play) after his shop was opened
C['merchant'].update(n=6, after=15)

# staves are swung with both hands, wands with one: the two animations were the wrong way round
_SW = {'baton': 'anim11', 'baguette': 'anim13'}   # (anim11 / anim12 are the same two-handed swing in the client; anim13 = one-handed thrust)
for w in C['weapons'] + C['uniqueWeapons']:
    k = w.get('of') or w['id']
    if k in _SW: w['anim'] = _SW[k]

if __name__ == '__main__':
    json.dump(C, open(f'{G}/data/content.json', 'w'), ensure_ascii=False, separators=(',', ':'))
    print('0.36 ok')
