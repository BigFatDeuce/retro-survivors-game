"""0.65 content: the 'Polykrome' skins leave the game (21 hats, 13 capes). Their ids and shop prices stay in
C.removedSkins: at boot an owned one is refunded and an equipped one taken off (main.js).
usage: PYTHONUTF8=1 python tools/content/patch_065.py  (imports patch_062, writes game/data/content.json)"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
import _root
import json
import patch_062 as P2

C, G, T, put_ui = P2.C, P2.G, P2.T, P2.put_ui

POLY = 'olykrom'
# (the chain only builds skins that still have a picture in sprites.json: once their pictures are gone, the Polykrome
# skins are not made at all; their ids and prices are kept here for the refund)
removed = {"16_262": 800, "16_270": 1150, "16_263": 1400, "16_264": 1400, "16_268": 1550, "16_267": 1550, "16_266": 1550, "16_269": 1700, "16_280": 2050, "16_272": 2950, "16_281": 3100, "16_271": 3200, "16_273": 3550, "16_275": 3800, "16_425": 4050, "16_274": 4150, "16_300": 4400, "16_276": 4500, "16_277": 4500, "16_279": 4700, "16_278": 5450, "17_257": 600, "17_277": 750, "17_259": 750, "17_260": 1150, "17_191": 1150, "17_190": 1200, "17_258": 1700, "17_248": 1700, "17_192": 1700, "17_253": 3200, "17_194": 4350, "17_193": 4400, "17_317": 5750}
for cat in ('hats', 'capes', 'pets'):
    keep = []
    for x in C.get(cat) or []:
        if POLY in str((x.get('name') or {}).get('fr', '')).lower(): removed[x['id']] = x.get('price', 0)
        else: keep.append(x)
    C[cat] = keep
C['removedSkins'] = dict(sorted({**C.get('removedSkins', {}), **removed}.items()))
put_ui({'skins_refund': T('Les skins Polykrome ont quitté le jeu : {n} kamas remboursés.', 'The Polykrome skins left the game: {n} kamas refunded.',
                          'Die Polykrom-Skins wurden entfernt: {n} Kamas erstattet.', 'Los skins Polikromo dejan el juego: {n} kamas reembolsados.',
                          'Le skin Polikrome lasciano il gioco: {n} kama rimborsati.', 'De Polykrome-skins verlaten het spel: {n} kama terugbetaald.',
                          'As skins Polikromáticas saíram do jogo: {n} kamas reembolsados.')})

# the shop's skin search: typed on the keyboard or on the on-screen one, like the profile names
put_ui({
    'search_ph': T('Rechercher…', 'Search…', 'Suchen…', 'Buscar…', 'Cerca…', 'Zoeken…', 'Pesquisar…'),
    'search_title': T('Rechercher un skin', 'Search a skin', 'Skin suchen', 'Buscar un skin', 'Cerca una skin', 'Skin zoeken', 'Pesquisar uma skin'),
    'search_hint': T('Tape le nom au clavier, ou avec les touches ci-dessous : la liste se filtre en direct.', 'Type the name on your keyboard or with the keys below: the list filters as you type.',
                     'Tippe den Namen auf der Tastatur oder mit den Tasten unten: die Liste filtert sofort.', 'Escribe el nombre con el teclado o con las teclas de abajo: la lista se filtra al instante.',
                     'Scrivi il nome sulla tastiera o con i tasti qui sotto: la lista si filtra subito.', 'Typ de naam op je toetsenbord of met de toetsen hieronder: de lijst filtert meteen.',
                     'Digite o nome no teclado ou com as teclas abaixo: a lista filtra na hora.'),
    'search_none': T('Aucun skin ne correspond.', 'No skin matches.', 'Kein Skin passt.', 'Ningún skin coincide.', 'Nessuna skin corrisponde.', 'Geen skin gevonden.', 'Nenhuma skin corresponde.'),
})

# the Xelor's 'Horloge' fusion: no more clock-dial icons; light violet turning hourglasses in the style of the
# Sagesse fusion's aura orbs (render.js drawHourglassOrb)
hb = C['spells']['fu_xel_horloge']['base']; hb.pop('drawIcon', None); hb['hourglass'] = 1
for lv in C['spells']['fu_xel_horloge'].get('lv') or []:
    if isinstance(lv, dict): lv.pop('drawIcon', None)

if __name__ == '__main__':
    json.dump(C, open(f'{G}/data/content.json', 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
    print('0.65 ok', len(removed), 'skins removed')
