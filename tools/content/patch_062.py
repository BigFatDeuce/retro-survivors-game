"""0.62 content: the kill combo's words (more juice on the combos) — the HUD's 'Combo' label, the word shown over
the character at each step (25, 50, 100, 200, 400, 800 kills in a row) and 'Nouveau record !' when the profile's best
combo falls (juice.js, render.js drawCombo).
usage: PYTHONUTF8=1 python tools/content/patch_062.py  (imports patch_061, writes game/data/content.json)"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
import _root
import json
import patch_061 as P1

C, G, T, put_ui = P1.C, P1.G, P1.T, P1.put_ui

WORDS = [   # fr, en, de, es, it, nl, pt
    ('Joli !', 'Nice!', 'Schön!', '¡Bien!', 'Bello!', 'Mooi!', 'Boa!'),
    ('Carnage !', 'Carnage!', 'Gemetzel!', '¡Carnicería!', 'Carneficina!', 'Slachting!', 'Carnificina!'),
    ('Massacre !', 'Massacre!', 'Massaker!', '¡Masacre!', 'Massacro!', 'Bloedbad!', 'Massacre!'),
    ('Inarrêtable !', 'Unstoppable!', 'Unaufhaltsam!', '¡Imparable!', 'Inarrestabile!', 'Onstuitbaar!', 'Imparável!'),
    ('Légendaire !', 'Legendary!', 'Legendär!', '¡Legendario!', 'Leggendario!', 'Legendarisch!', 'Lendário!'),
    ('Divin !', 'Godlike!', 'Göttlich!', '¡Divino!', 'Divino!', 'Goddelijk!', 'Divino!'),
]
put_ui({f'combo_{i + 1}': T(*w) for i, w in enumerate(WORDS)})
put_ui({
    'combo_word': T('Combo', 'Combo', 'Kombo', 'Combo', 'Combo', 'Combo', 'Combo'),
    'combo_record': T('Nouveau record !', 'New record!', 'Neuer Rekord!', '¡Nuevo récord!', 'Nuovo record!', 'Nieuw record!', 'Novo recorde!'),
})

if __name__ == '__main__':
    json.dump(C, open(f'{G}/data/content.json', 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
    print('0.62 ok')
