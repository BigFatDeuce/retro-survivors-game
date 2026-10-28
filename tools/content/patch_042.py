"""Beta 0.47 content, applied on top of patch_041.   usage: python tools/content/patch_042.py"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
import json
import patch_041 as P1
from _root import ROOT

C, T, G, put_ui = P1.C, P1.T, P1.G, P1.put_ui

# the Dofus pictures: the client's item gfx (items_*.json, type 23) — Emeraude 2 (it showed the Kaliptus, 10), Pourpre 1
# (it showed the Vulbis, 4), Vulbis 4 (it showed 16); colours of the real eggs
FIX = {'emeraude': (2, '#a8d61e'), 'pourpre': (1, '#ff5a1e'), 'vulbis': (4, '#d8262c')}
for d in C['dofus']:
    if d['id'] in FIX: d['icon'], d['color'] = FIX[d['id']]
# the achievements with a Dofus picture: the same 440-px eggs as everywhere else
DHD = {d['id']: f"dofus_hd_{d['icon']}" for d in C['dofus']}
for a in C['achievements']:
    a['icon'] = {'dofus_1': DHD['emeraude'], 'dofus_all': DHD['pourpre'], 'tot_win': DHD['ocre']}.get(a['id'], a['icon'])

# Musha l'Oni's treasure maps: a treasure in every zone; a map drops in any zone, half as often as the Manuel du Tailleur,
# and leads to a random zone that has none yet (secret zones too); the bigger the zone, the bigger the treasure
TM = C['tmap']
TM['maps'] = [m['id'] for m in C['maps']]
TM['chance'] = round(C['manuel']['chance'] / 2, 4)
TM['prize'] = {m['id']: 5000 if m.get('hidden') else int(round(1500 + 250 * i, -2)) for i, m in enumerate(C['maps'])}
TM['musha']['sprite'] = '1153_z120'   # tools/assets/build_npc57.py (GFX=1153, Musha's recipe): the scene's animations at zoom 12 (the 4.8 sheet was blurry there)

put_ui({
    'tmap_none': T("Aucune carte au trésor pour l'instant. Musha l'Oni en perd dans toutes les zones… sans le faire exprès, évidemment.",
                   "No treasure map yet. Musha the Oni drops them in every zone… by accident, of course.",
                   "Noch keine Schatzkarte. Musha der Oni verliert sie in allen Zonen… natürlich aus Versehen.",
                   "Aún no hay mapas del tesoro. Musha el Oni los pierde en todas las zonas… sin querer, claro.",
                   "Ancora nessuna mappa del tesoro. Musha l'Oni le perde in tutte le zone… per sbaglio, ovviamente.",
                   "Nog geen schatkaart. Musha de Oni verliest ze in alle zones… per ongeluk, natuurlijk.",
                   "Ainda nenhum mapa do tesouro. Musha, o Oni, perde-os em todas as zonas… sem querer, claro."),
    'tmap_hint': T("Un trésor par zone. Une carte trouvée dans une zone peut mener à n'importe quelle autre, même secrète.",
                   "One treasure per zone. A map found in one zone can lead to any other, even a secret one.",
                   "Ein Schatz pro Zone. Eine Karte aus einer Zone kann zu jeder anderen führen, auch zu einer geheimen.",
                   "Un tesoro por zona. Un mapa hallado en una zona puede llevar a cualquier otra, incluso secreta.",
                   "Un tesoro per zona. Una mappa trovata in una zona può portare a qualsiasi altra, anche segreta.",
                   "Eén schat per zone. Een kaart uit een zone kan naar elke andere leiden, zelfs een geheime.",
                   "Um tesouro por zona. Um mapa encontrado numa zona pode levar a qualquer outra, mesmo secreta."),
    'tmap_count': T('{n} / {t} trésors déterrés', '{n} / {t} treasures dug up', '{n} / {t} Schätze ausgegraben', '{n} / {t} tesoros desenterrados',
                    '{n} / {t} tesori dissotterrati', '{n} / {t} schatten opgegraven', '{n} / {t} tesouros desenterrados'),
    'tmap_unknown': T('Pas encore de carte', 'No map yet', 'Noch keine Karte', 'Aún sin mapa', 'Ancora nessuna mappa', 'Nog geen kaart', 'Ainda sem mapa'),
    'tmap_dest': T('La croix est dans : {z}', 'The cross is in: {z}', 'Das Kreuz liegt in: {z}', 'La cruz está en: {z}', 'La croce è in: {z}', 'Het kruis ligt in: {z}', 'A cruz está em: {z}'),
    'tmap_now': T('Ici même ! Suivez la croix rouge sur la mini-carte.', 'Right here! Follow the red cross on the minimap.', 'Genau hier! Folge dem roten Kreuz auf der Minikarte.',
                  '¡Aquí mismo! Sigue la cruz roja del minimapa.', 'Proprio qui! Segui la croce rossa sulla minimappa.', 'Precies hier! Volg het rode kruis op de minikaart.',
                  'Aqui mesmo! Segue a cruz vermelha no minimapa.'),
    # the life-steal finales on their own (Armurerie tab, level-up card)
    'arm_blood': T('Soif de sang', 'Bloodthirst', 'Blutdurst', 'Sed de sangre', 'Sete di sangue', 'Bloeddorst', 'Sede de sangue'),
    'blood_tag': T('Arme vampirique', 'Vampiric weapon', 'Vampirwaffe', 'Arma vampírica', 'Arma vampirica', 'Vampierwapen', 'Arma vampírica'),
    'blood_hint': T("Une finale à part : l'arme devient une vraie arme à vol de vie de Dofus Retro. Proposée avec les autres finales quand l'arme est au niveau max (une seule finale par partie).",
                    "A finale of its own: the weapon becomes a real Dofus Retro life-steal weapon. Offered with the other finales once the weapon is maxed (one finale per run).",
                    "Ein eigenes Finale: Die Waffe wird zu einer echten Lebensraub-Waffe aus Dofus Retro. Wird mit den anderen Finalen angeboten, sobald die Waffe die Höchststufe hat (ein Finale pro Lauf).",
                    "Un final aparte: el arma se vuelve una auténtica arma de robo de vida de Dofus Retro. Se ofrece con los demás finales cuando el arma está al máximo (un final por partida).",
                    "Un finale a parte: l'arma diventa una vera arma con furto di vita di Dofus Retro. Proposto con gli altri finali quando l'arma è al massimo (un finale per partita).",
                    "Een aparte finale: het wapen wordt een echt levensroofwapen uit Dofus Retro. Aangeboden met de andere finales zodra het wapen maximaal is (één finale per run).",
                    "Um final à parte: a arma torna-se uma verdadeira arma de roubo de vida de Dofus Retro. Oferecido com os outros finais quando a arma está no máximo (um final por partida)."),
    'blood_of': T('Finale de : {w}', 'Finale of: {w}', 'Finale von: {w}', 'Final de: {w}', 'Finale di: {w}', 'Finale van: {w}', 'Final de: {w}'),
})

if __name__ == '__main__':
    json.dump(C, open(f'{G}/data/content.json', 'w'), ensure_ascii=False, separators=(',', ':'))
    print('0.47 ok', [(d['id'], d['icon']) for d in C['dofus']], TM['chance'], TM['prize'])
