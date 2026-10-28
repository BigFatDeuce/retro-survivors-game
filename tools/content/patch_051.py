"""Beta 0.51 content, applied on top of patch_044: Dark Vlad's zone is his clearing now (build_vlad51.py: one grass
plain, half the area of the other zones), named as in the game ('clairière de Dark Vlad', quests lang 367; the Dutch
and Portuguese lang texts are machine-translated, written here).   usage: python tools/content/patch_051.py"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
import _root
import json
import patch_044 as P4

C, G = P4.C, P4.G
V = next(m for m in C['maps'] if m['id'] == 'vlad')
V['name'] = {'fr': 'Clairière de Dark Vlad', 'en': "Dark Vlad's Clearing", 'de': 'Lichtung des Dark Vlad', 'es': 'Claro de Dark Vlad',
             'it': 'Radura di Dark Vlad', 'nl': 'Open plek van Dark Vlad', 'pt': 'Clareira de Dark Vlad'}

if __name__ == '__main__':
    json.dump(C, open(f'{G}/data/content.json', 'w'), ensure_ascii=False, separators=(',', ':'))
    print('0.51 ok', len(C['maps']), 'zones')
