"""Beta 0.60 content, applied on top of patch_059 (the balance pass after the 0.58 audit, Bannir / Passer).
usage: PYTHONUTF8=1 python tools/content/patch_060.py"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
import json, os
import patch_059 as P9
from _root import ROOT

C, G, T, put_ui = P9.C, P9.G, P9.T, P9.put_ui
R = C['run']
# fewer monsters on screen for the same difficulty (readability and speed): every wave -15 %; from 5:00 the crowd grows by
# +10 % up to +25 % at 10:00 (it doubled over one minute before) while the monsters' life goes +25 % at 5:00 up to x1.5
R['spawnMul'] = round(R['spawnMul'] * 0.85, 4)
R['spawnLateK'] = [1.10, 1.25]
R['spawnLateEnd'] = 10.0
R['hpLate'] = [5.0, 10.0, 1.25, 1.50]
# fewer monsters = fewer drops: objects on the ground +15 %, kamas twice as often and 1 to 3 coins at a time, the gold
# nugget worth twice as much (the 'kamas' choice once everything is maxed is unchanged)
R['itemDropK'] = 1.15
R['kamaDrop'] = round(R['kamaDrop'] * 2, 5)
R['kamaCoins'] = [1, 3]
C['goldKamas'] = 50
# relics: elites drop one 10 % of the time; at most 5 relics fall in a run, whatever drops them
C['relicElite'] = 0.25   # (after testing: 25 %, with a slow motion like a boss)
import relics060 as R6
R6.apply(C)   # (the relics' bonuses follow their real Dofus Retro items)
C['relicDropMax'] = 5
# Difficile: twice as many scheduled elites (its life multiplier stays x1.5 for monsters and bosses: it was not x2)
C['elites']['hardMul'] = 2
# experience: normal ambers -10 %; big ambers (elites, Archimonsters, bosses) = 1.3x a normal amber of the wave
for m in C['monsters'].values():
    if m.get('xp'):
        m['xp'] = round(m['xp'] * 0.9, 4)
R['bigAmberK'] = 1.3
# fewer monsters also meant fewer random elites (their chests carry most of a run's kamas) and Archimonsters, both rolled
# per monster: their chance per monster x1.7 keeps them about as frequent per minute as in 0.59
R['rareK'] = 1.7
# after testing: the experience cut was too strong (bots reached level 27-30 at 10:00): ambers are worth
# more and more from 3:00 (x1 -> x4.5 at 10:00) to aim at level 45-50 at 10:00
R['xpLate'] = [3.0, 10.0, 1.0, 4.5]
# Difficile: monsters and bosses x1.25 life (x1.5 before)
C['hard']['hpMin'] = C['hard']['hpMax'] = 0.25
C['hard']['bossHp'] = 1.25
# the auto-choice switch moved from B to Y on the controller (B is 'back' everywhere): the loading tip that says so
import re as _re
for _lg, _tips in C['tips'].items():
    for _i, _t in enumerate(_tips):
        if 'R' in _t and _re.search(r'\bB\b', _t) and ('kamas' in _t.lower()):
            _tips[_i] = _re.sub(r'\bB\b', 'Y', _t)
# shop (0.60): cheaper; masteries have 5 levels of +5 % (they had 10 of +10 %: the levels above 5 are refunded at boot)
C['spellCost'] = [50, 100, 150, 250, 500]
C['passCost'] = [100, 200, 400, 700, 1000]
C['scrollCost'] = [100, 200, 400, 700, 1000, 1250, 1500, 1750, 2000, 2500]
C['masteryCostOld'] = C['masteryCost']
C['masteryCost'] = [150, 300, 500, 750, 1000]
C['masteryPer'] = 0.05
# skins (0.60): the up-to-date client's hats / capes / pets (tools/assets/build_acc060.py new -> work/newskins060.json, one
# entry per look), every skin's level = the level of its item in Dofus Retro (lang files of the up-to-date client,
# work/lang_new), sorted by level then name, priced by level and rounded down to 50 kamas; pets have no level in Retro
# (175 of 177 are level 1): a flat 2 500 (+27 a level for the two level-60 ones); the Chapeau de Lonne goes
_NS = os.path.join(ROOT, 'work', 'newskins060.json')
_NEWLANG = os.path.join(ROOT, 'work', 'lang_new', 'items_fr.json')
if os.path.exists(_NEWLANG):
    _IL = json.load(open(_NEWLANG, encoding='utf-8'))['I']['u']
    _KIND = {'16': 'hats', '17': 'capes', '18': 'pets'}
    _have = {it['id'] for k in _KIND.values() for it in C[k]}
    for _e in (json.load(open(_NS, encoding='utf-8')) if os.path.exists(_NS) else []):
        if _e['sym'] not in _have: C[_KIND[_e['type']]].append({'id': _e['sym'], 'item': _e['item'], 'name': _e['name'], 'lvl': _e['lvl'], 'price': 0})
    C['hats'] = [h for h in C['hats'] if h['id'] != '16_261']
    # a few old skins wore another item's id and name (16_259 was called 'Casque du Corbeau Noir' like 16_287): the item
    # that really wears the look; a skin with no picture at all goes (17_177)
    _ILL = {lg: json.load(open(os.path.join(ROOT, 'work', 'lang_new', f'items_{lg}.json'), encoding='utf-8'))['I']['u'] for lg in ('en', 'de', 'es', 'it', 'nl', 'pt')}
    _SPR = json.load(open(os.path.join(ROOT, 'game', 'data', 'sprites.json'))).get('acci') or {}
    for _k in _KIND.values():
        if _SPR: C[_k] = [it for it in C[_k] if it['id'] in _SPR]
        for _it in C[_k]:
            _v = _IL.get(str(_it.get('item')))
            if not _v or f"{_v['t']}_{_v['g']}" == _it['id']: continue
            _c = sorted((x.get('l') or 1, int(i)) for i, x in _IL.items() if f"{x.get('t')}_{x.get('g')}" == _it['id'])
            if not _c: continue
            _it['item'] = _c[0][1]; _it['name'] = {'fr': _IL[str(_c[0][1])]['n'], **{lg: (_ILL[lg].get(str(_c[0][1])) or {}).get('n') or _IL[str(_c[0][1])]['n'] for lg in _ILL}}
    _BYG = {}   # (skins without an item id: the lowest level item wearing that look)
    for _iid, _v in _IL.items():
        if _v.get('t') in (16, 17, 18): _BYG.setdefault(f"{_v['t']}_{_v['g']}", []).append(_v.get('l') or 1)
    for _k in _KIND.values():
        for _it in C[_k]:
            _lv = (_IL.get(str(_it.get('item'))) or {}).get('l') or min(_BYG.get(_it['id'], [0]))
            if _lv: _it['lvl'] = _lv
            _lv = _it['lvl'] = _it.get('lvl') or 1
            _it['price'] = (2500 + (27 * _lv if _lv > 1 else 0)) // 50 * 50 if _k == 'pets' else (600 + 27 * _lv) // 50 * 50
            for _lg in ('fr', 'en', 'de', 'es', 'it', 'nl', 'pt'):
                if not (_it['name'].get(_lg) or '').strip(): _it['name'][_lg] = _it['name']['fr']
        C[_k].sort(key=lambda it: (it.get('lvl') or 0, (it['name'].get('fr') or '').lower()))
# weapons (0.60): only the former unique weapons, 5 per type = 3 weapons + 2 Soifs de Sang, one special effect each,
# real names (tools/content/weapons060.py)
import weapons060 as W6
W6.apply(C, put_ui)
put_ui({
    'unique_found': T('Nouvelle arme : {n} !', 'New weapon: {n}!', 'Neue Waffe: {n}!', '¡Nueva arma: {n}!', 'Nuova arma: {n}!', 'Nieuw wapen: {n}!', 'Nova arma: {n}!'),
    'blood_found': T('Soif de Sang : {n} !', 'Bloodthirst: {n}!', 'Blutdurst: {n}!', '¡Sed de Sangre: {n}!', 'Sete di Sangue: {n}!', 'Bloeddorst: {n}!', 'Sede de Sangue: {n}!'),
    'blood_tag': T('Soif de Sang', 'Bloodthirst', 'Blutdurst', 'Sed de Sangre', 'Sete di Sangue', 'Bloeddorst', 'Sede de Sangue'),
    'fusion_note': T("Une seule fusion par partie, dès que l'arme est au niveau max : elle prend l'élément pour de bon.",
                     "One fusion per run, once the weapon is maxed: it takes the element for good.",
                     "Eine Fusion pro Lauf, sobald die Waffe ausgebaut ist: sie nimmt das Element für immer an.",
                     "Una sola fusión por partida, en cuanto el arma está al máximo: adopta el elemento para siempre.",
                     "Una sola fusione per partita, appena l'arma è al massimo: prende l'elemento per sempre.",
                     "Eén fusie per run, zodra het wapen maximaal is: het neemt het element voorgoed aan.",
                     "Uma só fusão por partida, assim que a arma estiver no máximo: ela assume o elemento de vez."),
})
# three new global spells from the Dofus world (tools/content/globals060.py)
import globals060 as G6
G6.apply(C)
# spell fusions: three per class (tools/content/fusions060.py)
import fusions060 as F6
F6.apply(C, put_ui)
# Rayon Obscur (Xélor) drawn with its client clip 805 on every cell of the ray (spells.js 'beam' + p.dup; fx 805 in HD by
# tools/assets/build_fx060.py 805)
C['spells']['rayon_obscur']['base']['dup'] = 1
# the humanoid bosses walk at 60 fps (tools/assets/build_move060.py bosses: '<sprite>_w60' sheets)
_SPRM = json.load(open(os.path.join(ROOT, 'game', 'data', 'sprites.json')))['mobs']
for _b in ('dark_vlad', 'goultard', 'qutan'):
    if _b in C['bosses'] and C['bosses'][_b]['sprite'] + '_w60' in _SPRM: C['bosses'][_b]['walk60'] = C['bosses'][_b]['sprite'] + '_w60'
# Dark Vlad's and Goultard's words, serious and dramatic, and Goultard's defeat scene (tools/content/dialogues060.py)
import dialogues060 as D6
D6.apply(put_ui)
# the achievement 'Armurier du Krosmoz' (every unique weapon) becomes the Minotoror trapdoor's blue chest
for _a in C['achievements']:
    if _a['id'] == 'unique_all':
        _a.update(id='trap_chest', k='trapFound', n=1, icon='it_17_117',
                  name=T('Sous la trappe', 'Under the Trapdoor', 'Unter der Falltür', 'Bajo la trampilla', 'Sotto la botola', 'Onder het luik', 'Sob o alçapão'),
                  desc=T("Trouver le coffre bleu caché sous une trappe des terres du Minotoror. Il ne sentait pas la rose.",
                         "Find the blue chest hidden under a trapdoor in the Minotoror's lands. It didn't smell of roses.",
                         "Finde die blaue Truhe unter einer Falltür im Land des Minotoror. Sie roch nicht nach Rosen.",
                         "Encontrar el cofre azul escondido bajo una trampilla en las tierras del Minotauroro. No olía a rosas.",
                         "Trovare il forziere blu nascosto sotto una botola nelle terre del Minotoror. Non profumava di rose.",
                         "Vind de blauwe kist onder een luik in het land van de Minotoror. Hij rook niet naar rozen.",
                         "Encontrar o baú azul escondido sob um alçapão nas terras do Minotoro. Não cheirava a rosas."))
# level-up: banish a card for the rest of the run / skip a level-up, once each per run
C['banishes'] = 1
C['skips'] = 1
put_ui({
    'banish': T('Bannir', 'Banish', 'Verbannen', 'Desterrar', 'Bandisci', 'Verbannen', 'Banir'),
    'banish_pick': T('Choisissez la carte à bannir', 'Pick the card to banish', 'Wähle die Karte zum Verbannen', 'Elige la carta que desterrar',
                     'Scegli la carta da bandire', 'Kies de kaart om te verbannen', 'Escolha a carta a banir'),
    'banished': T('{n} ne sera plus proposé pendant cette partie.', '{n} will not be offered again this run.', '{n} wird in diesem Lauf nicht mehr angeboten.',
                  '{n} no se volverá a ofrecer en esta partida.', '{n} non verrà più proposto in questa partita.', '{n} wordt deze run niet meer aangeboden.',
                  '{n} não será mais oferecido nesta partida.'),
    'skip': T('Passer', 'Skip', 'Überspringen', 'Saltar', 'Salta', 'Overslaan', 'Pular'),
    'skipped': T('Niveau passé.', 'Level-up skipped.', 'Stufenaufstieg übersprungen.', 'Nivel saltado.', 'Livello saltato.', 'Niveau overgeslagen.', 'Nível pulado.'),
    'always_hint': T('Plus besoin de choisir : le jeu prendra ça pour vous à chaque niveau. Changez d’avis en partie avec R, Y ou un clic sur l’icône.',
                     'No more choosing: the game takes it for you at every level. Change your mind in a run with R, Y or a click on the icon.',
                     'Nie mehr wählen: das Spiel nimmt es bei jeder Stufe für dich. Im Lauf änderbar mit R, Y oder einem Klick auf das Symbol.',
                     'Se acabó elegir: el juego lo toma por ti en cada nivel. Cambia de idea en partida con R, Y o un clic en el icono.',
                     'Basta scegliere: il gioco lo prende per te a ogni livello. Cambia idea in partita con R, Y o un clic sull’icona.',
                     'Nooit meer kiezen: het spel neemt het elk niveau voor je. Verander van gedachten in een run met R, Y of een klik op het pictogram.',
                     'Chega de escolher: o jogo pega isso para você a cada nível. Mude de ideia na partida com R, Y ou um clique no ícone.'),
    'mastery_lv': T('Niv. {n}/{m}', 'Lv. {n}/{m}', 'St. {n}/{m}', 'Niv. {n}/{m}', 'Liv. {n}/{m}', 'Niv. {n}/{m}', 'Nív. {n}/{m}'),
    'mastery_intro': T("Chaque niveau de Maîtrise ajoute +5 % aux dégâts de ce type d'arme, jusqu'à 5 niveaux. Le mannequin d'entraînement n'a toujours rien demandé.",
                       "Each Mastery level adds +5% to this weapon type's damage, up to 5 levels. The training dummy still didn't ask for any of this.",
                       "Jede Meisterschaftsstufe gibt +5 % Schaden für diese Waffenart, bis zu 5 Stufen. Die Trainingspuppe hat immer noch nicht darum gebeten.",
                       "Cada nivel de Maestría añade +5 % al daño de este tipo de arma, hasta 5 niveles. El muñeco de entrenamiento sigue sin pedir nada.",
                       "Ogni livello di Maestria aggiunge +5% ai danni di questo tipo d'arma, fino a 5 livelli. Il manichino non ha ancora chiesto niente.",
                       "Elk niveau Meesterschap geeft +5% schade aan dit wapentype, tot 5 niveaus. De oefenpop heeft nog steeds nergens om gevraagd.",
                       "Cada nível de Maestria adiciona +5% ao dano deste tipo de arma, até 5 níveis. O boneco de treino continua sem pedir nada."),
    'trait_real': T('1 niveau en partie : {t}', '1 level in a run: {t}', '1 Stufe im Lauf: {t}', '1 nivel en partida: {t}', '1 livello in partita: {t}', '1 niveau in een run: {t}', '1 nível na partida: {t}'),
    'mastery_refund': T('Maîtrises : les niveaux au-delà de 5 vous ont été remboursés ({n} kamas). Le maître d’armes s’excuse, un peu.',
                        'Masteries: the levels above 5 were refunded ({n} kamas). The weapon master apologises, a little.',
                        'Meisterschaften: die Stufen über 5 wurden erstattet ({n} Kamas). Der Waffenmeister entschuldigt sich, ein bisschen.',
                        'Maestrías: los niveles por encima de 5 te han sido reembolsados ({n} kamas). El maestro de armas se disculpa, un poco.',
                        'Maestrie: i livelli oltre il 5 ti sono stati rimborsati ({n} kama). Il maestro d’armi si scusa, un po’.',
                        'Meesterschappen: de niveaus boven 5 zijn terugbetaald ({n} kamas). De wapenmeester verontschuldigt zich, een beetje.',
                        'Maestrias: os níveis acima de 5 foram reembolsados ({n} kamas). O mestre de armas pede desculpas, um pouco.'),
    'victory_big': T('VICTOIRE !', 'VICTORY!', 'SIEG!', '¡VICTORIA!', 'VITTORIA!', 'OVERWINNING!', 'VITÓRIA!'),
    'nav_ok': T('Valider', 'Select', 'Auswählen', 'Aceptar', 'Conferma', 'Kiezen', 'Confirmar'),
    'once_left': T('{n}× restant', '{n}× left', 'noch {n}×', '{n}× restante', '{n}× rimasto', 'nog {n}×', '{n}× restante'),
})

if __name__ == '__main__':
    json.dump(C, open(f'{G}/data/content.json', 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
    print('0.60 ok')
