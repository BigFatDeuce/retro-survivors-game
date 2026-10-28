"""0.79 content: each class's ground areas in its own colour, the Pwout de Cawotte a darker orange,
'cancelled run' strings, the new credits (C.credits, the: shown in every language).
usage: PYTHONUTF8=1 python tools/content/patch_079.py  (imports patch_076, writes game/data/content.json)"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
import _root
import json
import patch_076 as P6

C, G, T, put_ui = P6.C, P6.G, P6.T, P6.put_ui
S = C['spells']

# ground areas / shock rings: one readable colour per class (pulses used one yellow / red for everyone; spells.js reads
# p.color first). Reach, targets and mechanics untouched.
COLS = {
    'epee_celeste': '#ffe04a',      # Iop: gold
    'mot_frayeur': '#ff7ad0',       # Eniripsa: pink
    'tremblement': '#c8a050',       # Sadida: earth
    'vent_empoisonne': '#8ee04a',   # Sadida: brighter poison green (was #7fbf3f)
    'attirance': '#ff5a3a',         # Sacrieur: blood orange (pull)
    'dissolution': '#d81e5e',       # Sacrieur: crimson (life drain)
    'gueule_de_bois': '#ffb04a',    # Pandawa: beer amber
    'tout_ou_rien': '#b98aff',      # Ecaflip: card violet
    'fu_sad_poison': '#8ee04a', 'fu_sac_transfert': '#d81e5e', 'fu_sac_punition': '#ff5a3a',
    'prouts': '#9a3608',            # Pwout de Cawotte: a darker orange than the Cawotte's bright zone (gspells.js)
}
for k, c in COLS.items(): S[k].setdefault('base', {})['color'] = c

put_ui({'run_cancelled': T('Partie annulée', 'Run cancelled', 'Partie abgebrochen', 'Partida cancelada', 'Partita annullata', 'Spel geannuleerd', 'Partida cancelada'),
        'run_cancelled_sub': T("Abandonnée avant 20 secondes : elle ne compte dans aucune statistique.",
                               "Given up before 20 seconds: it counts in no statistic.",
                               "Vor 20 Sekunden aufgegeben: Sie zählt in keiner Statistik.",
                               "Abandonada antes de 20 segundos: no cuenta en ninguna estadística.",
                               "Abbandonata prima di 20 secondi: non conta in nessuna statistica.",
                               "Opgegeven binnen 20 seconden: telt in geen enkele statistiek mee.",
                               "Abandonada antes de 20 segundos: não conta em nenhuma estatística.")})

# the credits, in the 7 languages (tools/content/credits079.py)
from credits079 import CREDITS
C['credits'] = CREDITS

if __name__ == '__main__':
    json.dump(C, open(f'{G}/data/content.json', 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
    print('0.79 ok')
