"""Beta 0.56 content, applied on top of patch_055.   usage: python tools/content/patch_056.py"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
import _root
import json
import patch_055 as P5

C, G, T, put_ui = P5.C, P5.G, P5.T, P5.put_ui
mp = {m['id']: m for m in C['maps']}
# the project's own musics for the secret / special zones (game/assets/audio/music)
mp['goultard'].update(music='goultard', boss_music='goultard2')
mp['vlad']['music'] = 'darkvlad'
mp['minotoror'].update(music='minotoror', boss_music='minotororfinal')
mp['kwismas']['music'] = 'nowel2'
# every class 3 % faster; Sacrieur 95 HP, Enutrof 67
for c in C['classes']:
    c['base']['speed'] = round(c['base']['speed'] * 1.03, 4)
    if c['id'] == 'sacrieur': c['base']['hp'] = 95
    if c['id'] == 'enutrof': c['base']['hp'] = 67
put_ui({'goultard_lock': T('Le Dark Vlad garde un secret... Un secret Difficile à garder.',
                           'Dark Vlad keeps a secret... A Hard secret to keep.',
                           'Dark Vlad hütet ein Geheimnis... Ein Schwieriges Geheimnis.',
                           'Dark Vlad guarda un secreto... Un secreto Difícil de guardar.',
                           'Dark Vlad custodisce un segreto... Un segreto Difficile da mantenere.',
                           'Dark Vlad bewaart een geheim... Een Moeilijk geheim om te bewaren.',
                           'O Dark Vlad guarda um segredo... Um segredo Difícil de guardar.')})

# ToT in HD (tools/assets/build_npc57.py: the client sprite 1010 at zoom 8, was 5)
C['totSprite'] = '1010_z80'

if __name__ == '__main__':
    json.dump(C, open(f'{G}/data/content.json', 'w'), ensure_ascii=False, separators=(',', ':'))
    print('0.56 ok')
