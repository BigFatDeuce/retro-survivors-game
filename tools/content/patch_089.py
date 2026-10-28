"""0.89 content: the Féca's glyphs are replaced (their ids kept: shop levels, statistics and achievements stay):
- glyphe_enflammee -> Armure Incandescente (client spell 1: its icon print, its flaming sphere clip 108 at the cast): a
  ring of fire that follows the Féca and burns what it touches; hit while it burns, it answers with a fire burst (`retal`)
- glyphe_immobilisation -> Trêve (client spell 5: icon print, clip 101 at the cast): a dome of peace on the Féca's spot,
  the monsters inside are frozen; when it fades it pushes them away (`push`)
- their fusion fu_feca_glyphe -> Rempart élémentaire: the dome of fire that follows the Féca, freezes, burns, answers.
game.js (zone ticks: burn, push at the end, retaliation in damagePlayer), render.js (drawFireArmor / drawDome).
usage: PYTHONUTF8=1 python tools/content/patch_089.py  (imports patch_085, writes game/data/content.json)"""
import sys as _sys, os as _os, json
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
import _root
import patch_085 as P5

C, G, T, put_ui = P5.C, P5.G, P5.T, P5.put_ui
S = C['spells']
LG = ['fr', 'en', 'de', 'es', 'it', 'nl', 'pt']
lang = {lg: (lambda d: d.get('S', d))(json.load(open(f'{_root.ROOT}/work/lang_json/spells_{lg}.json', encoding='utf-8'))) for lg in LG}

a = S['glyphe_enflammee']
a.update(t='zone', anim='anim1', fx=[108], icon='feca_1', sid=1, name={lg: lang[lg]['1']['n'] for lg in LG},
         desc=T("Une armure de feu entoure le Féca et brûle tout ce qui l'approche. Frappé, il riposte par une gerbe de flammes.",
                "A fire armour surrounds the Feca and burns whatever comes close. When hit, he strikes back with a burst of flames.",
                "Eine Feuerrüstung umgibt den Feca und verbrennt alles, was sich nähert. Getroffen, schlägt er mit einem Flammenstoß zurück.",
                "Una armadura de fuego rodea al Feca y quema todo lo que se acerca. Si lo golpean, responde con una llamarada.",
                "Un'armatura di fuoco avvolge il Feca e brucia tutto ciò che si avvicina. Se colpito, risponde con una fiammata.",
                "Een vuurharnas omringt de Feca en verbrandt alles wat dichtbij komt. Geraakt, slaat hij terug met een vlammenstoot.",
                "Uma armadura de fogo envolve o Feca e queima tudo o que se aproxima. Se atingido, responde com uma labareda."),
         base={'dmg': 6.0, 'radius': 70, 'duration': 4.0, 'tick': 0.45, 'cd': 5.524, 'count': 1, 'color': '#ff6a1e', 'follow': 1, 'armor': 1, 'burn': 1, 'retal': 2.5},
         lv=[{}, {'radius': 80, 'dmg': 6.9}, {'duration': 5.0, 'radius': 92, 'dmg': 7.7}, {'dmg': 9.5, 'duration': 5.5, 'retal': 3.2}])
a.pop('glyph', None)

b = S['glyphe_immobilisation']
b.update(t='zone', anim='anim1', fx=[101], icon='feca_5', sid=5, name={lg: lang[lg]['5']['n'] for lg in LG},
         desc=T("Un dôme de paix se pose sur le Féca : les monstres qui y entrent restent figés. Quand il s'efface, il les repousse.",
                "A dome of peace settles over the Feca: monsters that step in are frozen. When it fades, it pushes them away.",
                "Eine Friedenskuppel legt sich über den Feca: Monster darin erstarren. Wenn sie vergeht, stößt sie sie weg.",
                "Una cúpula de paz cubre al Feca: los monstruos que entran quedan congelados. Al desvanecerse, los repele.",
                "Una cupola di pace avvolge il Feca: i mostri che entrano restano immobili. Quando svanisce, li respinge.",
                "Een vredeskoepel daalt over de Feca: monsters die erin komen, verstijven. Als hij vervaagt, duwt hij ze weg.",
                "Uma cúpula de paz cobre o Feca: os monstros que entram ficam paralisados. Ao desaparecer, empurra-os para longe."),
         base={'dmg': 3, 'radius': 105, 'duration': 3.0, 'tick': 0.5, 'cd': 8.143, 'count': 1, 'color': '#ffe7a0', 'stun': 0.55, 'dome': 1, 'push': 90},
         lv=[{}, {'radius': 118, 'duration': 3.6}, {'dmg': 5, 'radius': 130}, {'cd': 6.514, 'duration': 4.2, 'push': 120}])
for k in ('glyph', 'target'): b['base'].pop(k, None)

f = S['fu_feca_glyphe']
f.update(fx=[108], fx2=212, name=T('Rempart élémentaire', 'Elemental Rampart', 'Elementarer Wall', 'Baluarte elemental', 'Baluardo elementale', 'Elementaire Wal', 'Baluarte Elemental'),
         desc=T("Un dôme de feu suit le Féca : les monstres y restent figés et brûlent. Le toucher, c'est se prendre une gerbe de flammes.",
                "A dome of fire follows the Feca: monsters inside are frozen and burn. Touch it and get a burst of flames.",
                "Eine Feuerkuppel folgt dem Feca: Monster darin erstarren und brennen. Wer sie berührt, kassiert einen Flammenstoß.",
                "Una cúpula de fuego sigue al Feca: los monstruos dentro quedan congelados y arden. Tocarla es recibir una llamarada.",
                "Una cupola di fuoco segue il Feca: i mostri dentro restano immobili e bruciano. Toccarla significa prendersi una fiammata.",
                "Een vuurkoepel volgt de Feca: monsters erin verstijven en branden. Wie hem raakt, krijgt een vlammenstoot.",
                "Uma cúpula de fogo segue o Feca: os monstros lá dentro ficam paralisados e ardem. Tocá-la é levar com uma labareda."),
         base={'dmg': 7.2, 'radius': 125, 'duration': 5.0, 'tick': 0.4, 'cd': 5.524, 'count': 1, 'color': '#ff7a2a', 'follow': 1, 'armor': 1, 'dome': 1, 'burn': 1, 'stun': 0.6, 'retal': 3.5, 'push': 130})

if __name__ == '__main__':
    json.dump(C, open(f'{G}/data/content.json', 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
    print('0.89 ok')
