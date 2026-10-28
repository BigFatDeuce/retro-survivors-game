"""Beta 0.30 content (lot 5H), applied on top of patch_028: menu strings (colours, controls, statistics, music, …).
->  game/data/content.json      usage: python tools/content/patch_029.py"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
import _root
import json
import patch_028 as P8

C, T, G = P8.C, P8.T, P8.G

UI = {
    'col_hair': T('Couleur 1 (cheveux, peau)', 'Colour 1 (hair, skin)', 'Farbe 1 (Haare, Haut)', 'Color 1 (pelo, piel)', 'Colore 1 (capelli, pelle)', 'Kleur 1 (haar, huid)', 'Cor 1 (cabelo, pele)'),
    'col_outfit': T('Couleur 2 (tenue)', 'Colour 2 (outfit)', 'Farbe 2 (Kleidung)', 'Color 2 (ropa)', 'Colore 2 (abiti)', 'Kleur 2 (kleding)', 'Cor 2 (roupa)'),
    'ctl_sh_dash': T('Esquive', 'Dash', 'Sprint', 'Esquiva', 'Scatto', 'Dash', 'Esquiva'),
    'ctl_sh_spells': T('Sorts dépl.', 'Move spells', 'Beweg.-Zauber', 'Hech. mov.', 'Inc. movim.', 'Bew.-spreuken', 'Feit. mov.'),
    'mus_default': T('musique du menu', 'menu music', 'Menümusik', 'música del menú', 'musica del menu', 'menumuziek', 'música do menu'),
    'mus_mute': T('Silence, on joue !', 'Silence, we\'re playing!', 'Ruhe, wir spielen!', '¡Silencio, que jugamos!', 'Silenzio, si gioca!', 'Stilte, we spelen!', 'Silêncio, estamos a jogar!'),
    'col_accent': T('Couleur 3 (détails)', 'Colour 3 (details)', 'Farbe 3 (Details)', 'Color 3 (detalles)', 'Colore 3 (dettagli)', 'Kleur 3 (details)', 'Cor 3 (detalhes)'),
}
for k, v in UI.items():
    for lg, txt in v.items(): C['ui'][lg][k] = txt

if __name__ == '__main__':
    json.dump(C, open(f'{G}/data/content.json', 'w'), ensure_ascii=False, separators=(',', ':'))
    print('0.30 ok')
