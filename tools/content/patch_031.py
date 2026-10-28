"""Beta 0.32 content (lot 5J), applied on top of patch_030: the performance mode's hint (it now also loads the monster
and effect pictures at half size and the ground coarser).  ->  game/data/content.json   usage: python tools/content/patch_031.py"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
import _root
import json
import patch_030 as P0

C, T, G = P0.C, P0.T, P0.G

UI = {
    'perf_hint': T('Pour les petits PC et téléphones : effets réduits, monstres et sol en qualité allégée, 30 images/s. Prend effet à la prochaine partie.',
                   'For small PCs and phones: fewer effects, lighter monsters and ground, 30 fps. Takes effect from the next run.',
                   'Für schwache PCs und Handys: weniger Effekte, leichtere Monster und Böden, 30 fps. Gilt ab dem nächsten Lauf.',
                   'Para PC y móviles modestos: menos efectos, monstruos y suelo más ligeros, 30 fps. Se aplica en la próxima partida.',
                   'Per PC e telefoni poco potenti: meno effetti, mostri e terreno più leggeri, 30 fps. Vale dalla prossima partita.',
                   "Voor zwakke pc's en telefoons: minder effecten, lichtere monsters en grond, 30 fps. Geldt vanaf de volgende run.",
                   'Para PCs e telemóveis fracos: menos efeitos, monstros e chão mais leves, 30 fps. Aplica-se na próxima partida.'),
}
for k, v in UI.items():
    for lg, txt in v.items(): C['ui'][lg][k] = txt

if __name__ == '__main__':
    json.dump(C, open(f'{G}/data/content.json', 'w'), ensure_ascii=False, separators=(',', ':'))
    print('0.32 ok')
