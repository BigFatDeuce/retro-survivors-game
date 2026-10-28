"""Beta 0.46 content, applied on top of patch_040.   usage: python tools/content/patch_041.py"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
import json
import patch_040 as P0
from _root import ROOT

C, T, G, put_ui = P0.C, P0.T, P0.G, P0.put_ui
LG = ('fr', 'en', 'de', 'es', 'it', 'nl', 'pt')

# the mini-bosses (Tofuzmo, Coffre Animé: the 'special' monsters) give half as much XP
for m in C['monsters'].values():
    if m.get('special'): m['xp'] = round(m['xp'] * 0.5, 4)

# every explanation (spells, characteristics, class bonuses, weapons, fusions, scrolls, relics, Dofus) rewritten short
# and clear: tools/content/text46_*.json, [fr, en, de, es, it, nl, pt] per entry
TX = {}
for part in 'abcd':
    for sec, d in json.load(open(f'{ROOT}/tools/content/text46_{part}.json')).items(): TX.setdefault(sec, {}).update(d)
def L7(v): return dict(zip(LG, v))
for sid, v in TX['spells'].items(): C['spells'][sid]['desc'] = L7(v)
for c in C['classes']:
    if c['id'] in TX['classPassive']: c['passive'] = L7(TX['classPassive'][c['id']])
for sec in ('passives', 'scrolls', 'relics', 'dofus', 'weapons', 'uniqueWeapons', 'fusions'):
    for o in C[sec]:
        if o['id'] in TX.get(sec, {}): o['desc'] = L7(TX[sec][o['id']])
for w in C['uniqueWeapons']:
    if w['id'] == 'canne_bonbon': w['itemName']['pt'] = 'Bengala de Granny Candy'   # (the client text had a typo, '=+')

# one more weapon finale for every weapon and unique weapon: life steal (at most 0.050 % of the damage dealt), with
# the look of a real Dofus Retro weapon that steals life (its effects 91-95 in the server DB), skins in acc12
LEECH = {'dague': 0.0003, 'arc': 0.00035, 'baguette': 0.00035, 'epee': 0.0004, 'baton': 0.0004, 'marteau': 0.0005, 'pelle': 0.0005, 'hache': 0.0005}
SKIN = {   # weapon -> (client item id, skin T_G)
    'epee': (8931, '6_79'), 'epee_dark_vlad': (8596, '6_72'), 'epee_qui_pete': (8094, '6_66'),
    'dague': (8929, '5_68'), 'dagues_rat_noir': (6983, '5_47'), 'chakra_style': (3650, '5_34'),
    'marteau': (9117, '7_67'), 'kaiser': (8616, '7_62'), 'marteau_dragoeuf': (7197, '7_53'),
    'baton': (8275, '4_67'), 'god_rod': (9136, '4_80'), 'canne_bonbon': (8838, '4_77'),
    'baguette': (6495, '3_42'), 'pieu_vampirique': (7103, '3_53'), 'baguette_glace': (9135, '3_66'),
    'arc': (7162, '2_46'), 'arc_ange': (7163, '2_47'), 'arc_feugeuf': (7187, '2_50'),
    'pelle': (8419, '8_42'), 'ares': (8936, '8_49'), 'pelle_gateau': (8420, '8_45'),
    'hache': (8868, '19_48'), 'bardiche': (8293, '19_43'), 'hache_zoth': (7255, '19_32'),
}
ITEMS = {lg: json.load(open(f'{ROOT}/work/lang_json/items_{lg}.json'))['I']['u'] for lg in LG}
of = {w['id']: w['id'] for w in C['weapons']}; of.update({w['id']: w['of'] for w in C['uniqueWeapons']})
NAME = T('Soif de sang', 'Bloodthirst', 'Blutdurst', 'Sed de sangre', 'Sete di sangue', 'Bloeddorst', 'Sede de sangue')
for wid, (item, skin) in SKIN.items():
    v = LEECH[of[wid]]; pc = f'{v * 100:.3f}'
    desc = T(f'Vol de vie : vous soigne de {pc.replace(".", ",")} % des dégâts infligés.', f'Life steal: heals you for {pc}% of the damage you deal.',
             f'Lebensraub: heilt dich um {pc.replace(".", ",")} % des verursachten Schadens.', f'Robo de vida: te cura un {pc.replace(".", ",")} % del daño infligido.',
             f'Furto di vita: ti cura dello {pc.replace(".", ",")}% dei danni inflitti.', f'Levensroof: geneest je voor {pc.replace(".", ",")}% van de aangerichte schade.',
             f'Roubo de vida: cura-te {pc.replace(".", ",")}% do dano causado.')
    e = dict(id=f'{wid}_sang', name=NAME, desc=desc, max=1, stats={'leech': v}, skin=skin, icon=f'it_{skin}',
             skinName={lg: ITEMS[lg][str(item)]['n'] for lg in LG})
    evo = C['weaponEvo'].setdefault(wid, [])
    evo[:] = [x for x in evo if x['id'] != e['id']] + [e]

if __name__ == '__main__':
    json.dump(C, open(f'{G}/data/content.json', 'w'), ensure_ascii=False, separators=(',', ':'))
    print('0.46 ok', sum(len(v) for v in TX.values()), 'texts', len(SKIN), 'finales', round(C['monsters']['tofu_mutant']['xp'], 3))
