"""Beta 0.39 content, applied on top of patch_036 (the release check of 0.39).   usage: python tools/content/patch_037.py"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
import _root
import json
import patch_036 as P6

C, T, G, put_ui = P6.C, P6.T, P6.G, P6.put_ui

# Bouclier Féca (the Féca's first spell): its glyphs pushed the monsters out of their own circle, so they barely hit
# (bench: 2 damage / s at level 1, the other first spells 15-22). Wider circle, softer push, longer, a little stronger
sp = C['spells']['bouclier_feca']
sp['base'].update(radius=56, size=30, knock=10, duration=5.0, rotSpeed=4.2, count=3, cd=4.8, dmg=round(sp['base']['dmg'] * 1.0, 1))
for l in sp['lv']:   # (the levels set their own damage / circle: scaled the same way)
    if 'dmg' in l: l['dmg'] = round(l['dmg'] * 1.0, 1)
    if 'radius' in l: l['radius'] = 64
sp['lv'][1] = {'rotSpeed': 4.8}   # (level 2 gave the 3rd glyph, now there from the start)

if __name__ == '__main__':
    json.dump(C, open(f'{G}/data/content.json', 'w'), ensure_ascii=False, separators=(',', ':'))
    print('0.39 ok', C['spells']['bouclier_feca']['base'])
