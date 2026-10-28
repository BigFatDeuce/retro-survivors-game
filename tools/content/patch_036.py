"""Beta 0.38 content, applied on top of patch_035.   usage: python tools/content/patch_036.py"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
import _root
import json
import patch_035 as P5
import langdata as LD
import patch_023 as P23

C, T, G, put_ui = P5.C, P5.T, P5.G, P5.put_ui

# the ambers give half as much XP again (levels came too fast)
for m in C['monsters'].values(): m['xp'] = round(m['xp'] * 0.5, 3)

# kamas fall from the monsters 25 % more often
C['run']['kamaDrop'] = round(C['run']['kamaDrop'] * 1.25, 5)

# relics: only the bosses and mini-bosses (the big life bars), 6 at most per run
C['relicMax'] = 6
C['relicMini'] = 0.5   # (the Tofuzmo and the Coffre Animé: one chance in two)
# the Ceinture du Prespic is already the Renvoi de dommages' picture: the relic is the Anneau du Prespic
for r in C['relics']:
    if r['id'] == 'ceinture_prespic':
        info = LD.item_info(6928)
        r.update(id='anneau_prespic', item=6928, icon=f"it_{info['t']}_{info['g']}", name=LD.item(6928), flavor=P23.flavor(6928))

put_ui({
    'dofus_from': T('Droppé par : {b}', 'Dropped by: {b}', 'Gedroppt von: {b}', 'Lo dropea: {b}', 'Droppato da: {b}', 'Gedropt door: {b}', 'Dropado por: {b}'),
    # when nobody knows yet who drops it: a joke (picked at random)
    'dofus_joke1': T('Droppé par : ??? — même le Bouftou Royal fait semblant de ne pas savoir.', 'Dropped by: ??? — even the Royal Gobball pretends not to know.', 'Gedroppt von: ??? — sogar der Königliche Fresssack tut so, als wüsste er nichts.', 'Lo dropea: ??? — hasta el Jalató Real se hace el loco.', 'Droppato da: ??? — perfino il Gobbo Reale fa finta di niente.', 'Gedropt door: ??? — zelfs de Koninklijke Boefto doet alsof hij het niet weet.', 'Dropado por: ??? — até o Papatudo Real se faz de desentendido.'),
    'dofus_joke2': T('Droppé par : ??? — demandez à un Enutrof, il ne vous dira rien.', 'Dropped by: ??? — ask an Enutrof, he won\'t tell you a thing.', 'Gedroppt von: ??? — frag einen Enutrof, er verrät dir nichts.', 'Lo dropea: ??? — pregúntale a un Anutrof, no soltará prenda.', 'Droppato da: ??? — chiedi a un Enutrof, non ti dirà nulla.', 'Gedropt door: ??? — vraag het een Enutrof, hij zegt niks.', 'Dropado por: ??? — pergunta a um Enutrof, não te dirá nada.'),
    'dofus_joke3': T('Droppé par : ??? — un Tofu l\'a peut-être couvé. Ou mangé.', 'Dropped by: ??? — a Tofu may have hatched it. Or eaten it.', 'Gedroppt von: ??? — vielleicht hat ein Tofu es ausgebrütet. Oder gefressen.', 'Lo dropea: ??? — quizá un Tofu lo incubó. O se lo comió.', 'Droppato da: ??? — forse un Tofu l\'ha covato. O mangiato.', 'Gedropt door: ??? — misschien heeft een Tofu het uitgebroed. Of opgegeten.', 'Dropado por: ??? — talvez um Tofu o tenha chocado. Ou comido.'),
    'dofus_joke4': T('Droppé par : ??? — le Wa Wabbit jure que ce n\'est pas une cawotte.', 'Dropped by: ??? — the Wa Wabbit swears it isn\'t a cawwot.', 'Gedroppt von: ??? — der Wa Wabbit schwört, es sei keine Kawotte.', 'Lo dropea: ??? — el Wa Wabbit jura que no es una zanahowia.', 'Droppato da: ??? — il Wa Wabbit giura che non è una cawota.', 'Gedropt door: ??? — de Wa Wabbit zweert dat het geen wortew is.', 'Dropado por: ??? — o Wa Wabbit jura que não é uma cenouwa.'),
    'relic_got': T('Relique !', 'Relic!', 'Relikt!', '¡Reliquia!', 'Reliquia!', 'Relikwie!', 'Relíquia!'),
})

if __name__ == '__main__':
    json.dump(C, open(f'{G}/data/content.json', 'w'), ensure_ascii=False, separators=(',', ':'))
    print('0.38 ok', [r['id'] for r in C['relics']][:4], C['run']['kamaDrop'])
