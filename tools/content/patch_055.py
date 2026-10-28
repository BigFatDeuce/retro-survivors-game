"""Beta 0.55 content, applied on top of patch_054.   usage: python tools/content/patch_055.py"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
import _root
import json
import patch_054 as P4

C, G, T, put_ui = P4.C, P4.G, P4.T, P4.put_ui
mp = {m['id']: m for m in C['maps']}
# the HD musics (tools/assets/music55.py): Grobe gets the Pandala village, Goultard's cursed clearing Qu'tan's dungeon
mp['grobe']['music'] = 'loc_pandavillage'
mp['goultard']['music'] = 'loc_kutan'
put_ui({
    'mus_style': T('Style de musique', 'Music style', 'Musikstil', 'Estilo de música', 'Stile musicale', 'Muziekstijl', 'Estilo de música'),
    'mus_classic': T('Classique', 'Classic', 'Klassisch', 'Clásica', 'Classica', 'Klassiek', 'Clássica'),
})

if __name__ == '__main__':
    json.dump(C, open(f'{G}/data/content.json', 'w'), ensure_ascii=False, separators=(',', ':'))
    print('0.55 ok')
