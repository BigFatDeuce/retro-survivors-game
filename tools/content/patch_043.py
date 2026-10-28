"""Beta 0.48 content, applied on top of patch_042.   usage: python tools/content/patch_043.py"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
import json, copy
import patch_042 as P2
from _root import ROOT

C, T, G, put_ui = P2.C, P2.T, P2.G, P2.put_ui
P1 = P2.P1

# the 'Soif de sang' weapons are no longer finales but unique weapons of their own: one vampiric version of every
# weapon and unique weapon (the real Retro life-steal weapon of 0.46), same blows, life steal growing with its level up
# to 0.100 %; offered in place of their type (C.bloodRate), red cards; their finales are their source's, keeping their look
for evo in C['weaponEvo'].values(): evo[:] = [e for e in evo if not e['id'].endswith('_sang')]
LEECH = [0.00025, 0.0004, 0.00055, 0.0007, 0.00085, 0.001]
pc = lambda v, lg: (f'{v * 100:.3f}' if lg == 'en' else f'{v * 100:.3f}'.replace('.', ','))
SRC = {w['id']: w for w in C['weapons'] + C['uniqueWeapons'] if not w.get('blood')}
C['uniqueWeapons'] = [w for w in C['uniqueWeapons'] if not w.get('blood')]
for wid, (item, skin) in P1.SKIN.items():
    s = SRC[wid]; nm = {lg: P1.ITEMS[lg][str(item)]['n'] for lg in P1.LG}; sn = s['name']
    a, b = LEECH[0], LEECH[-1]
    desc = T(f"Version vampirique de {sn['fr']} : mêmes coups, plus un vol de vie qui monte avec les niveaux ({pc(a, 'fr')} % → {pc(b, 'fr')} % des dégâts infligés).",
             f"Vampiric version of {sn['en']}: same blows, plus life steal that grows with its level ({pc(a, 'en')}% → {pc(b, 'en')}% of the damage dealt).",
             f"Vampirversion von {sn['de']}: gleiche Schläge, dazu Lebensraub, der mit der Stufe steigt ({pc(a, 'de')} % → {pc(b, 'de')} % des verursachten Schadens).",
             f"Versión vampírica de {sn['es']}: mismos golpes, más un robo de vida que sube con el nivel ({pc(a, 'es')} % → {pc(b, 'es')} % del daño infligido).",
             f"Versione vampirica di {sn['it']}: stessi colpi, più un furto di vita che sale con il livello ({pc(a, 'it')}% → {pc(b, 'it')}% dei danni inflitti).",
             f"Vampierversie van {sn['nl']}: dezelfde klappen, plus levensroof die stijgt met het niveau ({pc(a, 'nl')}% → {pc(b, 'nl')}% van de aangerichte schade).",
             f"Versão vampírica de {sn['pt']}: os mesmos golpes, mais um roubo de vida que sobe com o nível ({pc(a, 'pt')}% → {pc(b, 'pt')}% do dano causado).")
    w = copy.deepcopy(s)
    w.update(id=f'{wid}_sang', item=item, name=nm, itemName=nm, desc=desc, icon=f'it_{skin}', acc=skin, of=s.get('of', s['id']), unique=1, blood=1, src=wid, leech=LEECH)
    C['uniqueWeapons'].append(w)
    C['weaponEvo'][w['id']] = [dict(copy.deepcopy(e), skin=skin, icon=f'it_{skin}', skinName=None) for e in C['weaponEvo'].get(wid, [])]
    for e in C['weaponEvo'][w['id']]: e.pop('skinName', None)
C['bloodRate'] = 0.1

# shop scrolls: the cumulated bonus under the per-level one: the description cut before 'per level', its numbers
# as {0}, {1}… (sc.totN = the per-level numbers, times the level in the shop)
import re
CUT = {'fr': ' par niveau', 'en': ' per level', 'de': ' pro Stufe', 'es': ' por nivel', 'it': ' per livello', 'nl': ' per niveau', 'pt': ' por nível'}
for sc in C['scrolls']:
    sc['totN'] = [int(x) for x in re.findall(r'\+(\d+)', sc['desc']['fr'])]
    tot = {}
    for lg, d in sc['desc'].items():
        n = iter(range(9)); tot[lg] = re.sub(r'\+\d+', lambda mo: '+{%d}' % next(n), d.split(CUT[lg])[0])
    sc['tot'] = tot

# the characteristics without the client's framed look get one (tools/assets/build_staticons48.py: Icon_s_<stat>)
NEWIC = {'leech': 'Icon_s_leech', 'reflect': 'Icon_s_reflect', 'evade': 'Icon_s_evade', 'revive': 'Icon_s_revive', 'spellslot': 'Icon_s_spellslot', 'magnet': 'Icon_s_magnet'}
for pa in C['passives']:
    if pa.get('stat') in NEWIC: pa['icon'] = NEWIC[pa['stat']]

put_ui({
    'scroll_total': T('Total : {t}', 'Total: {t}', 'Gesamt: {t}', 'Total: {t}', 'Totale: {t}', 'Totaal: {t}', 'Total: {t}'),
    'blood_tag': T('Arme vampirique', 'Vampiric weapon', 'Vampirwaffe', 'Arma vampírica', 'Arma vampirica', 'Vampierwapen', 'Arma vampírica'),
    'blood_of': T('Origine', 'Origin', 'Ursprung', 'Origen', 'Origine', 'Oorsprong', 'Origem'),
    'p_leech': T('Vol de vie', 'Life steal', 'Lebensraub', 'Robo de vida', 'Furto di vita', 'Levensroof', 'Roubo de vida'),
    'blood_found': T('Arme vampirique : {n} !', 'Vampiric weapon: {n}!', 'Vampirwaffe: {n}!', '¡Arma vampírica: {n}!', 'Arma vampirica: {n}!', 'Vampierwapen: {n}!', 'Arma vampírica: {n}!'),
})
for lg in C['ui']:
    for k in ('arm_blood', 'blood_hint'): C['ui'][lg].pop(k, None)

if __name__ == '__main__':
    json.dump(C, open(f'{G}/data/content.json', 'w'), ensure_ascii=False, separators=(',', ':'))
    print('0.48 ok', sum(1 for w in C['uniqueWeapons'] if w.get('blood')), 'vampiric weapons', len(C['uniqueWeapons']), 'unique weapons')
