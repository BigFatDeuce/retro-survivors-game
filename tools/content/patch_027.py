"""Beta 0.27 content (lot 5E), applied on top of patch_026: bosses and monsters. Ogivol Scalarcin replaces the Maître
Corbac as the Landes de Sidimote's second boss (the Maître Corbac stays the end-of-run Doom), Ougah replaces the
Kralamoure (a static clip: only its mouth moves) as Otomaï's final boss, the Doom's corbacs are real monsters with the
life of the elites, every boss gets one or two new attacks that suit it (game/js/bosses.js), the summons get the sounds
of their own client clip (tools/lib/sndanim27.py).  ->  game/data/content.json
usage: python tools/content/patch_027.py"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
import _root
import json, copy
import patch_026 as P6
import langdata as LD

C, T, G = P6.C, P6.T, P6.G
B = C['bosses']



# ---------------------------------------------------------------- Ogivol Scalarcin (Landes de Sidimote, 2nd boss)
mc = B['maitre_corbac']
B['ogivol'] = dict(copy.deepcopy(mc), id='ogivol', did=462, gfx=1245, sprite='1245_z40', name=LD.monster(462), speed=105, scale=1.4, size=32,
    abilities=[dict(k='charge', cd=5.5), dict(k='ring', count=20, gap=3, speed=125, dmg=12, cd=5, color='#7ad07a'),
               dict(k='puddle', count=3, radius=60, dmg=6, dur=6, cd=8, color='#5aa83a'), dict(k='summon', mob='corbac', count=4, cd=9)],
    flavor=T('Un dragon d\'écailles et de mauvaise humeur. Il ne crache pas de feu : il crache tout le reste.', 'A dragon of scales and bad temper. It doesn\'t breathe fire: it spits everything else.', 'Ein Drache aus Schuppen und schlechter Laune. Er speit kein Feuer, sondern alles andere.', 'Un dragón de escamas y mal humor. No escupe fuego: escupe todo lo demás.', 'Un drago di scaglie e malumore. Non sputa fuoco: sputa tutto il resto.', 'Een draak van schubben en slecht humeur. Hij spuwt geen vuur: hij spuwt al het andere.', 'Um dragão de escamas e mau humor. Não cospe fogo: cospe tudo o resto.'),
    lore=dict(lv=[50, 50], hp=[300, 300]))
for m in C['maps']:
    if m['id'] == 'foret': m['bosses'] = [[t, 'ogivol' if b == 'maitre_corbac' else b] for t, b in m['bosses']]

# ---------------------------------------------------------------- Ougah (Otomaï, final boss)
kr = B['kralamoure']
B['ougah'] = dict(copy.deepcopy(kr), id='ougah', did=1159, gfx=1258, sprite='1258_z40', name=LD.monster(1159), speed=95, scale=1.3, size=40,
    abilities=[dict(k='pull', range=480, str=110, dur=1.6, cd=9, color='#5aa0ff'), dict(k='fissure', steps=8, step=62, radius=48, dmg=30, cd=6, color='#8a6a3a'),
               dict(k='slam', radius=150, dmg=34.6, cd=7), dict(k='summon', pool=kr['abilities'][1]['pool'], count=3, cd=8),
               dict(k='puddle', count=4, radius=65, dmg=9, dur=7, cd=10, color='#3a2a1a')],
    flavor=T('Le maître de la tourbière d\'Otomaï. Il vous attire à lui comme un aimant… un aimant qui frappe très fort. Il peut lâcher le Dofus Cawotte.', 'The master of Otomaï\'s peat bog. He draws you in like a magnet… a magnet that hits very hard. He can drop the Cawwot Dofus.', 'Der Herr des Moors von Otomai. Er zieht dich an wie ein Magnet… ein Magnet, der sehr hart zuschlägt. Er kann das Cawwot-Dofus fallen lassen.', 'El amo de la turbera de Otomai. Te atrae como un imán… un imán que pega muy fuerte. Puede soltar el Dofus Zanahowia.', 'Il padrone della torbiera di Otomai. Ti attira come una calamita… una calamita che picchia fortissimo. Può lasciare il Dofus Carota.', 'De heer van het veen van Otomaï. Hij trekt je aan als een magneet… een magneet die heel hard slaat. Hij kan de Wortel-Dofus laten vallen.', 'O senhor da turfeira de Otomai. Atrai-te como um íman… um íman que bate com muita força. Pode largar o Dofus Cenoura.'),
    lore=dict(lv=[900, 940], hp=[16000, 18000]))
for m in C['maps']:
    if m['id'] == 'otomai_coast': m['bosses'] = [[t, 'ougah' if b == 'kralamoure' else b] for t, b in m['bosses']]
for d in C['dofus']: d['from'] = ['ougah' if f == 'kralamoure' else f for f in d['from']]

# ---------------------------------------------------------------- the Doom's corbacs: real monsters (elite life)
C['monsters']['corbac_doom'] = dict(copy.deepcopy(C['monsters']['corbac']), id='corbac_doom', beh='chase', speed=185, xp=4, sprite=C['doom']['crowSprite'])
C['doomCrowHp'] = 5   # x the HP a monster has at that moment (what an elite gets)
for a in B['maitre_corbac_doom']['abilities']:
    if a['k'] == 'crow': a.update(count=2, max=24, cd=2.6)

# ---------------------------------------------------------------- more attacks, fitting each boss (k, factor of the
# boss's strongest hit, extra parameters)
NEW = {
    'chef_bouftou': [('roar', 0.35, dict(radius=200, cd=8, color='#e8d0a0'))],
    'tofu_royal': [('rain', 0.5, dict(count=7, mob='tofu', cd=7, color='#ffe14a'))],
    'bouftou_royal': [('roar', 0.4, dict(radius=230, cd=9, color='#e8d0a0')), ('fissure', 0.7, dict(cd=7, color='#a08050'))],
    'bworkette': [('rain', 0.6, dict(count=6, cd=7, color='#ff6a2a'))],
    'chene_mou': [('fissure', 0.8, dict(steps=8, cd=6.5, color='#5a8a2a'))],
    'dark_vlad': [('pull', 0, dict(cd=10, color='#a040ff')), ('ring', 0.5, dict(count=22, cd=5, color='#8a30c0'))],
    'blop_royal': [('puddle', 0.2, dict(count=4, cd=8, color='#3aa0ff'))],
    'dragon_cochon': [('rain', 0.6, dict(count=8, cd=7.5, color='#ff7a2a'))],
    'wobot': [('ring', 0.5, dict(count=18, cd=5.5, color='#c0c8d0'))],
    'grand_pa_elite': [('rain', 0.55, dict(count=7, cd=7, color='#ff9a2a'))],
    'wa_wabbit': [('ring', 0.45, dict(count=24, cd=6, color='#ffb03a'))],
    'mominotor': [('roar', 0.4, dict(radius=210, cd=8, color='#d08a5a'))],
    'deminoboule': [('fissure', 0.75, dict(cd=6.5, color='#9a7a5a'))],
    'minotoror': [('roar', 0.4, dict(radius=240, cd=9, color='#d06a3a')), ('fissure', 0.8, dict(steps=9, cd=7, color='#9a6a3a'))],
    'minotot': [('ring', 0.5, dict(count=26, cd=5, color='#ff5a3a')), ('fissure', 0.8, dict(steps=10, cd=6, color='#7a4a2a'))],
    'bworker': [('roar', 0.4, dict(radius=230, cd=8.5, color='#ff8a4a'))],
    'abraknyde_ancestral': [('puddle', 0.22, dict(count=3, cd=8, color='#6a9a3a')), ('fissure', 0.7, dict(cd=7, color='#5a7a2a'))],
    'vampire_dupyr': [('ring', 0.45, dict(count=20, cd=5.5, color='#c02040'))],
    'la_ouassingue': [('roar', 0.35, dict(radius=190, cd=8, color='#c0a080'))],
    'kruorre': [('ring', 0.45, dict(count=20, cd=5.5, color='#d04040'))],
    'don_dorgan': [('puddle', 0.2, dict(count=3, cd=8, color='#7a5a3a'))],
    'don_duss_ang': [('rain', 0.5, dict(count=6, cd=7.5, color='#e0b0ff'))],
    'gelee_royale_bleue': [('puddle', 0.2, dict(count=3, cd=8, color='#3a8aff'))],
    'gelee_royale_fraise': [('puddle', 0.2, dict(count=3, cd=8, color='#ff4a6a'))],
    'gelee_royale_citron': [('puddle', 0.22, dict(count=4, cd=8, color='#e8e03a'))],
    'rat_blanc': [('ring', 0.45, dict(count=20, cd=5.5, color='#e8e8e8'))],
    'koulosse': [('fissure', 0.85, dict(steps=9, cd=6, color='#8a8a9a')), ('roar', 0.4, dict(radius=240, cd=9, color='#b0b0c0'))],
    'bulbig': [('puddle', 0.22, dict(count=3, cd=8, color='#7ac05a'))],
    'tanukoui_san': [('rain', 0.5, dict(count=7, cd=7, color='#e8a0c0'))],
    'maitre_pandore': [('roar', 0.4, dict(radius=230, cd=9, color='#e0c080'))],
    'gourlo': [('rain', 0.55, dict(count=7, cd=7, color='#5a5a5a'))],
    'maitre_zoth': [('ring', 0.45, dict(count=22, cd=5.5, color='#9a6aff'))],
    'rasboul': [('roar', 0.4, dict(radius=220, cd=8.5, color='#c0a060'))],
    'tynril': [('puddle', 0.22, dict(count=4, cd=8, color='#a0d040')), ('ring', 0.45, dict(count=20, cd=6, color='#c0e060'))],
    'kimbo': [('pull', 0, dict(cd=10, color='#40c0a0'))],
    'yiti': [('rain', 0.5, dict(count=7, cd=7, color='#e0f0ff'))],
    'pere_fwetar': [('ring', 0.45, dict(count=20, cd=5.5, color='#a0c0ff'))],
    'papa_nowel': [('rain', 0.55, dict(count=8, cd=7, color='#ff3a3a'))],
    'boombata': [('rain', 0.55, dict(count=6, cd=7, color='#5a4a3a'))],
    'flib_capitaine': [('rain', 0.6, dict(count=8, cd=7.5, color='#4a4a4a'))],
    'le_chouque': [('pull', 0, dict(cd=10, color='#4aa0d0'))],
}
for bid, adds in NEW.items():
    b = B.get(bid)
    if not b: continue
    ref = max([a.get('dmg', 0) for a in b['abilities']] + [b['dmg']])
    for k, f, extra in adds:   # x0.65 after the Otomaï sims (the new attacks made the late zones a minute shorter)
        if k == 'rain': extra = dict(extra, count=min(6, extra.get('count', 6)))
        b['abilities'].append(dict(dict(k=k, dmg=round(ref * f * 0.65, 1)), **extra))

# ---------------------------------------------------------------- summons with the sounds of their own client clip
C['summonSnd']['dragonnet_rouge'] = dict(spawn='grrr1', atk=['machouille', 'grrr1'], die=None)   # (no death sound in its clip; it used the Dragodinde's)
C['summonSnd']['griffe_invocatrice'] = dict(spawn='cc_arty', atk=['cc_arty'], die='death')       # (it used the Ecaflip's own cries)

if __name__ == '__main__':
    json.dump(C, open(f'{G}/data/content.json', 'w'), ensure_ascii=False, separators=(',', ':'))
    print('0.27 ok', sum(len(v) for v in NEW.values()), 'new boss attacks')
