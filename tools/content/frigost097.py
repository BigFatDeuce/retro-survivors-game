"""0.97: the Île de Frigost zone ('frigost', world assets/worlds/frigost_* from tools/assets/build_frigost097.py), placed
right after L'île de Grobe with Grobe's difficulty (its waves normed on Grobe's, then a little over it: the next step).
Frigost exists in the Dofus Retro lang data only (area 48, the 'Créatures de Frigost' races 79–91, monsters 2837–2930), the
monsters without a picture except those listed here:
- the Boufmouths (Champs de glace, 2850–2854): the client's Boufmouth sprite 1091 (and the up-to-date client's Mastogobs
  2927 / 2929 / 2947 use it), Royalmouth = sprite 1090 (the up-to-date client's Royal Mastogob 2928);
- Frigost's resource protectors, with their own Retro gfx: Bulbeneige 2839 (1430), Epouvantail de Frostiz 2843 (1411),
  Tremble Ensorcelé 2842 (1392), Craqueboule d'Obsidienne 2844 (1389), Dévoreur de Poisskaille 2841 (1349);
- stand-ins for the Frigost monsters that have no sprite, from the client's winter monsters: Kanigrou hivernal 840 for
  the Kaniglou of the lost pines, Sakai Firefoux 864 for the Givrefoux, the Abominable Yiti 839 for the YeCh'Ti.
Music: Dofus 2's 'Frigost, la marmoréenne' (loc_frigost) and 'Le Combat de Frigost' (fig_frigost, the final boss).
Names from the lang files (nl / pt have none for Frigost: English). Sheets: build_mobs20.py <gfx>:z=3.6 (monsters),
<gfx>:boss:z=4.8 (bosses), then pack_mobs20.py --keys=… ."""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
import _root
import json
import langdata as LD, newzones20 as NZ

LG = ['fr', 'en', 'de', 'es', 'it', 'nl', 'pt']
MZ, BZ = 36, 48
LANG = {lg: json.load(open(f'{_root.ROOT}/work/lang_json/monsters_{lg}.json', encoding='utf-8'))['M'] for lg in ('fr',)}


def T(*a): return dict(zip(LG, a))


# Dutch / Portuguese names the lang files lack for Frigost, after the client's own for the same families (Kwismas'
# Boufmouth: nl Vreetschuur, pt Gobbmoth; Krakrots / Crackrock, -vreter / Devorador de, Vogelverschrikker / Espantalho)
NLPT = {2853: ('Vreetschuurtje', 'Gobbmothinho'), 2850: ('Vreetschuur', 'Gobbmoth'), 2851: ('Strijd-Vreetschuur', 'Gobbmoth de Guerra'),
        2852: ('Legendarische Vreetschuur', 'Gobbmoth Lendário'), 2854: ('Koninklijke Vreetschuur', 'Gobbmoth Real'),
        2839: ('Bulbsneeuw', 'Bulboneve'), 2843: ('Frosteez Vogelverschrikker', 'Espantalho do Frosteez'), 2842: ('Betoverde Esp', 'Choupo Encantado'),
        2844: ('Obsidiaan Krakrots', 'Crackrock de Obsidiana'), 2841: ('IJsvisvreter', 'Devorador de Peixe-gelo')}


def name(did):
    n = LD.monster(did); own = dict(zip(('nl', 'pt'), NLPT.get(did, (None, None))))
    return {lg: (n[lg] if n.get(lg) and n[lg] != 'null' else own.get(lg) or n['en']) for lg in LG}


def lore(did):   # (no emulator data for Frigost: the levels of the lang file's grades, no HP)
    m = LANG['fr'][str(did)]; lv = [m[g]['l'] for g in ('g1', 'g2', 'g3', 'g4', 'g5') if g in m]
    return dict(lv=[min(lv), max(lv)])


def mon(C, mid, did, gfx, hp, dmg, sp, xp, beh, size, atk, flavor, scale=1.0, extra=None, db=False):
    d = NZ.dbmon(did) if db else None
    o = dict(id=mid, did=did, gfx=gfx, name=name(did), hp=hp, dmg=dmg, speed=sp, xp=xp, beh=beh, size=size, atk=atk,
             attacks=d['attacks'] if d else [], colors=None, scale=scale, flavor=flavor, lore=d['lore'] if d else lore(did), sprite=f'{gfx}_z{MZ}', kb=1.0, rz=MZ / 10)
    if extra: o.update(extra)
    C['monsters'][mid] = o


def boss(C, bid, did, gfx, hp, dmg, sp, size, scale, final, xp, ab, flavor, db=False):
    d = NZ.dbmon(did) if db else None
    C['bosses'][bid] = dict(id=bid, did=did, gfx=gfx, name=name(did), hp=hp, dmg=dmg, speed=sp, abilities=ab, drops=[], scale=scale, size=size,
                            final=final, xp=xp, boss=1, rz=BZ / 10, sprite=f'{gfx}_z{BZ}', _norm=1, lore=d['lore'] if d else lore(did),
                            attacks=d['attacks'] if d else [], flavor=flavor)


ICE = '#cfeaff'


def apply(C):
    # ---------------------------------------------------------------- monsters (Grobe's range: 200–560 HP, 16–27 damage)
    mon(C, 'bouftonmouth', 2853, 1091, 220, 17.0, 140, 1.0, 'erratic', 13, None,
        T('Un jeune Boufmouth. Il court partout dans la neige.', 'A young Mastogob. It runs all over the snow.', 'Ein junger Fressmut. Er rennt überall durch den Schnee.', 'Un Jalamut joven. Corre por toda la nieve.',
          'Un giovane Pappabuk. Corre ovunque nella neve.', 'Een jonge Mastogob. Hij rent overal door de sneeuw.', 'Um Mastogob jovem. Corre por toda a neve.'), scale=0.78)
    mon(C, 'boufmouth', 2850, 1091, 330, 21.0, 105, 1.7, 'charge', 16, None,
        T('Le Bouftou des champs de glace. Sa laine épaisse amortit les coups.', 'The Gobball of the ice fields. Its thick wool softens the blows.', 'Das Fressmut der Eisfelder. Seine dicke Wolle dämpft die Schläge.', 'El Jalamut de los campos de hielo. Su lana espesa amortigua los golpes.',
          'Il Pappabuk dei campi di ghiaccio. La sua lana spessa attutisce i colpi.', 'De Mastogob van de ijsvelden. Zijn dikke wol vangt de klappen op.', 'O Mastogob dos campos de gelo. A sua lã espessa amortece os golpes.'))
    mon(C, 'bulbeneige', 2839, 1430, 300, 20.0, 90, 1.6, 'healer', 15, None,
        T('Il protège les Perce-neige de Frigost et soigne ses voisins.', "It guards Frigost's snowdrops and heals its neighbours.", 'Er beschützt Frigosts Schneeglöckchen und heilt seine Nachbarn.', 'Protege las campanillas de invierno de Frigost y cura a sus vecinos.',
          'Protegge i bucaneve di Frigost e cura i vicini.', 'Hij beschermt de sneeuwklokjes van Frigost en geneest zijn buren.', 'Protege as campainhas-de-inverno de Frigost e cura os vizinhos.'))
    mon(C, 'devoreur_poisskaille', 2841, 1349, 330, 21.0, 125, 1.7, 'chase', 15, None,
        T('Il garde les trous de pêche du lac gelé. Il mord tout ce qui approche.', "It guards the frozen lake's fishing holes. It bites anything that comes near.", 'Er bewacht die Eislöcher des gefrorenen Sees. Er beißt alles, was näher kommt.', 'Vigila los agujeros de pesca del lago helado. Muerde todo lo que se acerca.',
          'Sorveglia i buchi da pesca del lago gelato. Morde tutto ciò che si avvicina.', 'Hij bewaakt de vis-wakken van het bevroren meer. Hij bijt alles wat dichtbij komt.', 'Guarda os buracos de pesca do lago gelado. Morde tudo o que se aproxima.'))
    mon(C, 'epouvantail_frostiz', 2843, 1411, 340, 22.0, 80, 1.9, 'ranged', 16, dict(kind='proj', fx=None, dmg=17, speed=170, cd=3.0, range=300, color=ICE),
        T('Il veille sur les champs de Frostiz et lance des grains gelés.', 'It watches over the Frosteez fields and throws frozen grains.', 'Er wacht über die Frostizz-Felder und wirft gefrorene Körner.', 'Vigila los campos de sucaritazz y lanza granos helados.',
          'Veglia sui campi di Frostiss e lancia chicchi gelati.', 'Hij waakt over de Frosteez-velden en gooit bevroren korrels.', 'Vigia os campos de Frosteez e atira grãos gelados.'))
    mon(C, 'tremble_ensorcele', 2842, 1392, 400, 24.0, 80, 2.1, 'ranged', 16, dict(kind='lob', fx=2004, dmg=19, speed=150, cd=3.4, range=300, aoe=60),
        T('Un tremble ensorcelé. Ses branches projettent des blocs de givre.', 'A bewitched aspen. Its branches hurl chunks of frost.', 'Eine verzauberte Zitterpappel. Ihre Äste schleudern Frostbrocken.', 'Un álamo temblón embrujado. Sus ramas lanzan bloques de escarcha.',
          'Un pioppo tremulo stregato. I suoi rami scagliano blocchi di brina.', 'Een betoverde esp. Zijn takken slingeren brokken rijp.', 'Um choupo-tremedor enfeitiçado. Os seus ramos atiram blocos de geada.'))
    mon(C, 'kanigrou_frigost', 840, 1497, 360, 23.0, 130, 2.0, 'chase', 16, None,
        T('Un Kanigrou à la fourrure d\'hiver. Il chasse en meute entre les pins.', 'A Kaniger in its winter coat. It hunts in packs among the pines.', 'Ein Kanigrou im Winterfell. Er jagt im Rudel zwischen den Kiefern.', 'Un Kanugro con pelaje de invierno. Caza en manada entre los pinos.',
          'Un Kanigrù dal manto invernale. Caccia in branco tra i pini.', 'Een Kaniger in zijn wintervacht. Hij jaagt in roedels tussen de dennen.', 'Um Kaniger com pelagem de inverno. Caça em matilha entre os pinheiros.'), db=True)
    mon(C, 'sakai_frigost', 864, 1504, 330, 22.0, 95, 1.9, 'ranged', 15, dict(kind='proj', fx=None, dmg=17, speed=190, cd=2.8, range=290, color='#9fe8ff'),
        T('Un Firefoux des neiges. Il souffle des éclats de glace.', 'A snow Firefoux. It blows shards of ice.', 'Ein Schnee-Feuerfux. Er bläst Eissplitter.', 'Un Firefux de las nieves. Sopla esquirlas de hielo.',
          'Un Focopaz delle nevi. Soffia schegge di ghiaccio.', 'Een sneeuw-Firefoux. Hij blaast ijssplinters.', 'Uma raposa das neves. Sopra estilhaços de gelo.'), db=True)
    mon(C, 'craqueboule_obsidienne', 2844, 1389, 560, 27.0, 75, 2.7, 'tank', 18, None,
        T('Il garde les filons d\'obsidienne. Lent, lourd et presque incassable.', 'It guards the obsidian veins. Slow, heavy and nearly unbreakable.', 'Er bewacht die Obsidianadern. Langsam, schwer und fast unzerbrechlich.', 'Vigila las vetas de obsidiana. Lento, pesado y casi irrompible.',
          'Sorveglia le vene di ossidiana. Lento, pesante e quasi indistruttibile.', 'Hij bewaakt de obsidiaanaders. Traag, zwaar en bijna onbreekbaar.', 'Guarda os filões de obsidiana. Lento, pesado e quase inquebrável.'), extra=dict(kb=0.4))
    mon(C, 'boufmouth_guerre', 2851, 1091, 540, 27.0, 100, 2.6, 'charge', 18, None,
        T('Le chef d\'un troupeau de Boufmouths. Il charge tête baissée.', 'The leader of a Mastogob herd. It charges head down.', 'Der Anführer einer Fressmut-Herde. Er stürmt mit gesenktem Kopf los.', 'El jefe de una manada de Jalamuts. Embiste con la cabeza gacha.',
          'Il capo di un branco di Pappabuk. Carica a testa bassa.', 'De leider van een kudde Mastogobs. Hij stormt met gebogen kop.', 'O chefe de uma manada de Mastogobs. Investe de cabeça baixa.'), scale=1.2, extra=dict(kb=0.6))

    # ---------------------------------------------------------------- bosses (Grobe's: 10 000 / 15 000 / 23 000 HP)
    boss(C, 'boufmouth_legendaire', 2852, 1091, 10500, 23.0, 100, 30, 1.6, False, 14.0,
         [dict(k='charge', cd=4.5), dict(k='summon', pool=['bouftonmouth', 'boufmouth'], count=3, cd=9), dict(k='slam', radius=145, dmg=30.0, cd=6), dict(k='roar', dmg=10.0, radius=230, cd=8.5, color=ICE)],
         T('Le doyen des Boufmouths. Il appelle son troupeau et piétine tout.', 'The eldest of the Mastogobs. It calls its herd and tramples everything.', 'Das älteste der Fressmuts. Es ruft seine Herde und zertrampelt alles.', 'El más viejo de los Jalamuts. Llama a su manada y lo aplasta todo.',
           'Il più anziano dei Pappabuk. Chiama il branco e calpesta tutto.', 'De oudste van de Mastogobs. Hij roept zijn kudde en vertrapt alles.', 'O mais velho dos Mastogobs. Chama a manada e espezinha tudo.'))
    boss(C, 'yiti_frigost', 839, 1472, 15500, 27.0, 95, 32, 1.6, False, 18.0,
         [dict(k='charge', cd=4), dict(k='slam', radius=150, dmg=34.0, cd=5.5), dict(k='summon', pool=['kanigrou_frigost', 'devoreur_poisskaille'], count=3, cd=9), dict(k='rain', dmg=15.0, count=7, cd=8, color='#e0f0ff')],
         T('Une bête des neiges qui descend des hauteurs quand le froid mord.', 'A snow beast that comes down from the heights when the cold bites.', 'Ein Schneeungeheuer, das von den Höhen herabsteigt, wenn die Kälte beißt.', 'Una bestia de las nieves que baja de las alturas cuando muerde el frío.',
           'Una bestia delle nevi che scende dalle alture quando il freddo morde.', 'Een sneeuwbeest dat van de hoogten afdaalt als de kou bijt.', 'Uma fera das neves que desce das alturas quando o frio morde.'), db=True)
    boss(C, 'royalmouth', 2854, 1090, 24000, 32.0, 100, 34, 1.7, True, 45.0,
         [dict(k='charge', cd=4.5), dict(k='summon', pool=['boufmouth', 'boufmouth_guerre', 'bouftonmouth'], count=3, cd=9), dict(k='slam', radius=160, dmg=40.0, cd=6),
          dict(k='nova', count=18, dmg=24.0, cd=4.5, color=ICE), dict(k='ring', dmg=8.0, count=22, cd=6, color='#e6f4ff'), dict(k='rain', dmg=16.0, count=8, cd=8.5, color='#bfe0ff')],
         T('Le roi des Boufmouths. Sa couronne a gelé sur sa tête il y a longtemps.', 'The king of the Mastogobs. Its crown froze to its head long ago.', 'Der König der Fressmuts. Seine Krone ist ihm vor langer Zeit auf dem Kopf festgefroren.', 'El rey de los Jalamuts. Su corona se le congeló en la cabeza hace mucho.',
           'Il re dei Pappabuk. La corona gli si è gelata in testa tanto tempo fa.', 'De koning van de Mastogobs. Zijn kroon is lang geleden op zijn kop vastgevroren.', 'O rei dos Mastogobs. A coroa congelou-lhe na cabeça há muito tempo.'))

    # ---------------------------------------------------------------- the zone, right after Grobe
    zone = NZ.make_map(C, 'frigost', 'frigost', T('Île de Frigost', 'Frigost Island', 'Insel Frigost', 'Isla de Frigost', 'Isola di Frigost', 'Eiland Frigost', 'Ilha de Frigost'),
                       '180 - 480', 'loc_frigost', 'fig_frigost', [
        [('bouftonmouth', 5), ('devoreur_poisskaille', 3)],
        [('bouftonmouth', 3), ('boufmouth', 4), ('bulbeneige', 3)],
        [('boufmouth', 3), ('devoreur_poisskaille', 3), ('epouvantail_frostiz', 3), ('bulbeneige', 2)],
        [('kanigrou_frigost', 4), ('epouvantail_frostiz', 3), ('sakai_frigost', 2), ('tremble_ensorcele', 2)],
        [('kanigrou_frigost', 3), ('tremble_ensorcele', 3), ('sakai_frigost', 3), ('craqueboule_obsidienne', 1), ('boufmouth_guerre', 2)],
        [('tremble_ensorcele', 3), ('craqueboule_obsidienne', 2), ('kanigrou_frigost', 3), ('sakai_frigost', 3), ('boufmouth_guerre', 2)],
        [('craqueboule_obsidienne', 3), ('boufmouth_guerre', 3), ('tremble_ensorcele', 3), ('kanigrou_frigost', 4)],
    ], [[1.25, 'swarm', 'bouftonmouth', 30], [3.25, 'ring', 'boufmouth', 16], [5.0, 'swarm', 'devoreur_poisskaille', 30], [7.5, 'ring', 'kanigrou_frigost', 12], [9.0, 'swarm', 'bouftonmouth', 55]],
        [[3.0, 'boufmouth_legendaire'], [5.5, 'yiti_frigost'], [8.0, 'royalmouth']], [], ('grobe', 'grobe'), 0.0)
    for n in zone['norm']: n[2], n[3], n[4] = round(n[2] * 1.05, 4), round(n[3] * 1.03, 4), round(n[4] * 1.03, 4)   # (one step over Grobe)
    zone['fill'] = None; zone['tier'] = 12.5
    at = [m['id'] for m in C['maps']].index('grobe') + 1; C['maps'][at:at] = [zone]
    TM = C['tmap']; TM['maps'] = [m['id'] for m in C['maps'] if m['id'] in TM['maps'] or m['id'] == 'frigost']
    TM['prize']['frigost'] = 5200
    TM.setdefault('anec', {})['frigost'] = T(
        "Pour aller sur Frigost, il faut monter sur le bateau du Capitaine Ardier. Il appelle ça une croisière. Les Frigostiens, eux, appellent ça un naufrage annoncé.",
        "To reach Frigost you board Captain Ardier's ship. He calls it a cruise. The Frigostians call it a shipwreck waiting to happen.",
        "Nach Frigost kommt man mit dem Schiff von Kapitän Ardier. Er nennt es eine Kreuzfahrt. Die Frigostianer nennen es einen angekündigten Schiffbruch.",
        "Para ir a Frigost hay que subir al barco del Capitán Ardier. Él lo llama crucero. Los frigostianos lo llaman un naufragio anunciado.",
        "Per andare a Frigost si sale sulla nave del Capitano Ardier. Lui la chiama crociera. I frigostiani la chiamano un naufragio annunciato.",
        "Naar Frigost ga je met het schip van Kapitein Ardier. Hij noemt het een cruise. De Frigostianen noemen het een aangekondigde schipbreuk.",
        "Para ir a Frigost sobe-se ao barco do Capitão Ardier. Ele chama-lhe um cruzeiro. Os frigostianos chamam-lhe um naufrágio anunciado.")
    return zone
