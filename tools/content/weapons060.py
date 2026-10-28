"""0.60 weapons (the): the basic weapon types (Boisaille) and their finales are gone; the weapons are the former
unique weapons and 'Soifs de Sang': 5 per weapon type = 3 weapons + 2 Soifs de Sang (they also steal life and deal ~20 %
less damage), each with ONE special effect of its own (a type keeps its natural trait: daggers crit, hammers / staffs /
shovels stun, axes bleed, wands home…), each with its own look; names = the real Dofus Retro item wearing that look
(lang files of the up-to-date client, work/lang_new). C.weapons stays as the list of TYPES (masteries, names), never offered.
apply(C, T, put_ui) is called by patch_060."""
import json, os, copy
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT

LG = ('fr', 'en', 'de', 'es', 'it', 'nl', 'pt')
# (id, type, look, effect, Soif de Sang, keeps the params of this 0.59 weapon)
TABLE = [
    ('epee_dark_vlad', 'epee', '6_61', 'wave', 0, 'epee_dark_vlad'),
    ('epee_qui_pete', 'epee', '6_75', 'cloud', 0, 'epee_qui_pete'),
    ('tranchant_infernal', 'epee', '6_13', 'execute', 0, None),
    ('epee_dark_vlad_sang', 'epee', '6_72', 'bleedW', 1, None),
    ('epee_qui_pete_sang', 'epee', '6_66', 'crit', 1, None),
    ('dagues_rat_noir', 'dague', '5_59', 'crit', 0, 'dagues_rat_noir'),
    ('chakra_style', 'dague', '5_8', 'chakram', 0, 'chakra_style'),
    ('dague_feukuluf', 'dague', '5_27', 'burnW', 0, None),
    ('dagues_rat_noir_sang', 'dague', '5_47', 'bleedW', 1, None),
    ('dague_sang', 'dague', '5_68', 'slowW', 1, None),
    ('kaiser', 'marteau', '7_10', 'quake', 0, 'kaiser'),
    ('marteau_craqueleur', 'marteau', '7_58', 'wave', 0, None),
    ('marteau_tohlo', 'marteau', '7_15', 'firePatch', 0, None),
    ('marteau_dragoeuf', 'marteau', '7_59', 'burnW', 1, None),
    ('kaiser_sang', 'marteau', '7_62', 'confuse', 1, None),
    ('god_rod', 'baton', '4_7', 'bolt', 0, 'god_rod'),
    ('baton_oubli', 'baton', '4_11', 'confuse', 0, None),
    ('baton_akwadala', 'baton', '4_61', 'slowW', 0, None),
    ('canne_bonbon', 'baton', '4_48', 'cake', 1, None),
    ('god_rod_sang', 'baton', '4_80', 'poisonW', 1, None),
    ('baguette_glace', 'baguette', '3_2', 'slow', 0, 'baguette_glace'),
    ('tison_fute', 'baguette', '3_12', 'burnW', 0, None),
    ('baguette_sylvien', 'baguette', '3_15', 'bounce', 0, None),
    ('pieu_vampirique', 'baguette', '3_14', 'pierce', 1, None),
    ('baguette_sang', 'baguette', '3_42', 'poisonW', 1, None),
    ('arc_ange', 'arc', '2_31', 'pierceAll', 0, 'arc_ange'),
    ('arc_feugeuf', 'arc', '2_27', 'burn', 0, 'arc_feugeuf'),
    ('arc_lalamu', 'arc', '2_26', 'slowW', 0, None),
    ('arc_ange_sang', 'arc', '2_47', 'bounce', 1, None),
    ('arc_sang', 'arc', '2_46', 'poisonW', 1, None),
    ('ares', 'pelle', '8_9', 'stack', 0, 'ares'),
    ('pelle_gateau', 'pelle', '8_43', 'cake', 0, 'pelle_gateau'),
    ('pelle_mineur', 'pelle', '8_34', 'quake', 0, None),
    ('pelle_sang', 'pelle', '8_42', 'slowW', 1, None),
    ('pelle_gateau_sang', 'pelle', '8_45', 'burnW', 1, None),
    ('hache_zoth', 'hache', '19_47', 'execute', 0, 'hache_zoth'),
    ('bardiche', 'hache', '19_3', 'stun', 0, 'bardiche'),
    ('trancheuse_bambou', 'hache', '19_33', 'wave', 0, None),
    ('hache_sang', 'hache', '19_48', 'crit', 1, None),
    ('bardiche_sang', 'hache', '19_43', 'burnW', 1, None),
]
# the effect's own parameters, and what it costs in direct damage (x the type's damage) for the weapons built from a type
EFF = {
    'wave': ({'wave': 1}, 0.42), 'cloud': ({'cloud': 1}, 0.4), 'execute': ({'execute': 0.15}, 0.8), 'bleedW': ({'bleedW': 1.5}, 0.8),
    'crit': ({'crit': 0.25}, 0.85), 'chakram': ({'chakram': 1}, 0.5), 'burnW': ({'burnW': 0.3}, 0.75), 'slowW': ({'slowW': 0.4}, 0.8),
    'quake': ({'quake': 1}, 0.34), 'firePatch': ({'firePatch': 1}, 0.5), 'confuse': ({'confuse': 1.5}, 0.85), 'bolt': ({'bolt': 1}, 0.62),
    'cake': ({'cake': 0.04}, 0.95), 'poisonW': ({'poisonW': 0.6}, 0.7), 'pierce': ({'pierce': 4}, 0.9), 'bounce': ({'bounce': 2}, 0.75),
    'slow': ({}, 1), 'pierceAll': ({}, 1), 'burn': ({}, 1), 'stack': ({}, 1), 'stun': ({'stun': 0.6}, 1),
}
SECONDARY = {'dagues_rat_noir': ['bleed'], 'chakra_style': ['crit'], 'kaiser': ['stun'], 'god_rod': [], 'bardiche': [], 'hache_zoth': []}
LEECH = [0.00025, 0.0004, 0.00055, 0.0007, 0.00085, 0.001]


def T7(*a): return dict(zip(LG, a))


DESC = {
    'wave': T7("Chaque coup lance un croissant tranchant qui file à travers les rangs ennemis. Même les Bouftous ont compris le message.",
               "Each blow hurls a cutting crescent straight through the enemy ranks. Even the Gobballs got the message.",
               "Jeder Schlag schleudert eine scharfe Sichel quer durch die feindlichen Reihen. Selbst die Fresssäcke haben es verstanden.",
               "Cada golpe lanza una media luna cortante que atraviesa las filas enemigas. Hasta los Jalatós lo han entendido.",
               "Ogni colpo scaglia una mezzaluna tagliente attraverso le file nemiche. Perfino i Bouftou hanno capito l'antifona.",
               "Elke slag werpt een scherpe sikkel dwars door de vijandelijke rijen. Zelfs de Bouftous snappen het.",
               "Cada golpe lança um crescente cortante pelas fileiras inimigas. Até os Papatudos entenderam o recado."),
    'cloud': T7("Chaque coup libère un nuage toxique d'origine… douteuse. Les monstres dedans perdent des PV et leur dignité.",
                "Each blow releases a toxic cloud of… dubious origin. Monsters inside lose HP and their dignity.",
                "Jeder Schlag setzt eine giftige Wolke zweifelhafter Herkunft frei. Monster darin verlieren LP und ihre Würde.",
                "Cada golpe suelta una nube tóxica de origen… dudoso. Los monstruos dentro pierden PdV y su dignidad.",
                "Ogni colpo rilascia una nube tossica di origine… dubbia. I mostri dentro perdono PV e dignità.",
                "Elke slag laat een giftige wolk van… twijfelachtige herkomst los. Monsters erin verliezen LP en hun waardigheid.",
                "Cada golpe solta uma nuvem tóxica de origem… duvidosa. Os monstros dentro perdem PV e a dignidade."),
    'execute': T7("Achève net les monstres sous 15 % de leurs PV (pas les boss, ils ont un avocat).",
                  "Finishes off monsters under 15% HP on the spot (not bosses, they have a lawyer).",
                  "Erledigt Monster unter 15 % LP sofort (keine Bosse, die haben einen Anwalt).",
                  "Remata en el acto a los monstruos por debajo del 15 % de PdV (los jefes no, tienen abogado).",
                  "Finisce all'istante i mostri sotto il 15% dei PV (non i boss, hanno un avvocato).",
                  "Maakt monsters onder 15% LP meteen af (geen bazen, die hebben een advocaat).",
                  "Acaba na hora com monstros abaixo de 15% de PV (os chefes não, eles têm advogado)."),
    'bleedW': T7("Chaque coup fait saigner : les monstres perdent des PV pendant quelques secondes. Prévoir des pansements.",
                 "Each blow makes them bleed: monsters lose HP for a few seconds. Bring bandages.",
                 "Jeder Schlag lässt sie bluten: Monster verlieren einige Sekunden lang LP. Pflaster mitbringen.",
                 "Cada golpe los hace sangrar: los monstruos pierden PdV unos segundos. Trae vendas.",
                 "Ogni colpo li fa sanguinare: i mostri perdono PV per qualche secondo. Portate i cerotti.",
                 "Elke slag laat ze bloeden: monsters verliezen een paar seconden LP. Neem verband mee.",
                 "Cada golpe faz sangrar: os monstros perdem PV por alguns segundos. Traga curativos."),
    'crit': T7("+25 % de chances de coup critique. Les Ecaflips jurent que c'est de la chance, pas du talent.",
               "+25% critical hit chance. Ecaflips swear it's luck, not talent.",
               "+25 % kritische Trefferchance. Die Ecaflips schwören, es sei Glück, kein Talent.",
               "+25 % de probabilidad de golpe crítico. Los Zurcarák juran que es suerte, no talento.",
               "+25% di probabilità di colpo critico. Gli Ecaflip giurano che è fortuna, non talento.",
               "+25% kans op een kritieke treffer. Ecaflips zweren dat het geluk is, geen talent.",
               "+25% de chance de golpe crítico. Os Ecaflips juram que é sorte, não talento."),
    'chakram': T7("Chaque coup lance un disque tranchant qui fait l'aller-retour. Attention aux doigts.",
                  "Each blow throws a cutting disc that flies out and back. Mind your fingers.",
                  "Jeder Schlag wirft eine scharfe Scheibe, die hin und zurück fliegt. Achtung, Finger!",
                  "Cada golpe lanza un disco cortante de ida y vuelta. Cuidado con los dedos.",
                  "Ogni colpo lancia un disco tagliente che va e torna. Attenti alle dita.",
                  "Elke slag gooit een scherpe schijf die heen en terug vliegt. Pas op je vingers.",
                  "Cada golpe lança um disco cortante de ida e volta. Cuidado com os dedos."),
    'burnW': T7("Chaque coup enflamme les monstres, qui brûlent quelques secondes. Odeur de Bouftou grillé garantie.",
                "Each blow sets monsters on fire for a few seconds. Smell of grilled Gobball guaranteed.",
                "Jeder Schlag setzt Monster für ein paar Sekunden in Brand. Duft von gegrilltem Fresssack garantiert.",
                "Cada golpe prende fuego a los monstruos unos segundos. Olor a Jalató asado garantizado.",
                "Ogni colpo dà fuoco ai mostri per qualche secondo. Profumo di Bouftou alla griglia garantito.",
                "Elke slag steekt monsters een paar seconden in brand. Geur van gegrilde Bouftou gegarandeerd.",
                "Cada golpe incendeia os monstros por alguns segundos. Cheiro de Papatudo assado garantido."),
    'slowW': T7("Chaque coup ralentit les monstres touchés. Même un Tofu devient lent, c'est dire.",
                "Each blow slows the monsters it hits. Even a Tofu turns slow, imagine that.",
                "Jeder Schlag verlangsamt die getroffenen Monster. Sogar ein Tofu wird langsam, stell dir vor.",
                "Cada golpe ralentiza a los monstruos alcanzados. Hasta un Tofu se vuelve lento, fíjate.",
                "Ogni colpo rallenta i mostri colpiti. Perfino un Tofu diventa lento, pensa un po'.",
                "Elke slag vertraagt de geraakte monsters. Zelfs een Tofu wordt traag, stel je voor.",
                "Cada golpe deixa lentos os monstros atingidos. Até um Tofu fica lento, imagine."),
    'quake': T7("Chaque coup fait trembler le sol autour de l'impact. Les voisins vont encore se plaindre.",
                "Each blow shakes the ground around the impact. The neighbours will complain again.",
                "Jeder Schlag lässt den Boden um den Einschlag beben. Die Nachbarn werden sich wieder beschweren.",
                "Cada golpe hace temblar el suelo alrededor del impacto. Los vecinos volverán a quejarse.",
                "Ogni colpo fa tremare il suolo attorno all'impatto. I vicini si lamenteranno di nuovo.",
                "Elke slag laat de grond rond de inslag beven. De buren gaan weer klagen.",
                "Cada golpe faz o chão tremer ao redor do impacto. Os vizinhos vão reclamar de novo."),
    'firePatch': T7("Chaque coup laisse une flaque de feu au sol qui brûle tout ce qui passe. Ne pas marcher pieds nus.",
                    "Each blow leaves a puddle of fire that burns whatever walks in. Don't go barefoot.",
                    "Jeder Schlag hinterlässt eine Feuerlache, die alles verbrennt, was hineintritt. Nicht barfuß gehen.",
                    "Cada golpe deja un charco de fuego que quema todo lo que pasa. No ir descalzo.",
                    "Ogni colpo lascia una pozza di fuoco che brucia chiunque ci passi. Niente piedi nudi.",
                    "Elke slag laat een vuurplas achter die alles verbrandt wat erin loopt. Niet op blote voeten.",
                    "Cada golpe deixa uma poça de fogo que queima tudo o que passa. Nada de pés descalços."),
    'confuse': T7("Les monstres touchés perdent le nord quelques instants et errent au hasard. Comme un Iop sans carte.",
                  "Monsters hit lose their bearings for a moment and wander about. Like an Iop without a map.",
                  "Getroffene Monster verlieren kurz die Orientierung und irren umher. Wie ein Iop ohne Karte.",
                  "Los monstruos alcanzados se desorientan un momento y vagan al azar. Como un Yopuka sin mapa.",
                  "I mostri colpiti perdono l'orientamento per un attimo e vagano a caso. Come un Iop senza mappa.",
                  "Geraakte monsters raken even de weg kwijt en dwalen rond. Zoals een Iop zonder kaart.",
                  "Os monstros atingidos ficam desorientados um instante e vagam ao acaso. Como um Iop sem mapa."),
    'bolt': T7("Chaque coup fait tomber un éclair sur un monstre proche, qui reste sonné. Les Xélors trouvent ça électrisant.",
               "Each blow drops a lightning bolt on a nearby monster, leaving it dazed. Xelors find it electrifying.",
               "Jeder Schlag lässt einen Blitz auf ein nahes Monster fahren, das benommen bleibt. Xélors finden das elektrisierend.",
               "Cada golpe hace caer un rayo sobre un monstruo cercano, que queda aturdido. A los Xelor les parece electrizante.",
               "Ogni colpo fa cadere un fulmine su un mostro vicino, che resta stordito. Gli Xelor lo trovano elettrizzante.",
               "Elke slag laat een bliksem op een nabij monster vallen, dat versuft blijft. Xelors vinden het elektriserend.",
               "Cada golpe faz cair um raio num monstro próximo, que fica atordoado. Os Xelors acham isso eletrizante."),
    'cake': T7("Un coup sur 25 fait tomber du pain d'un monstre. On ne pose pas de questions sur la recette.",
               "One blow in 25 knocks bread out of a monster. Don't ask about the recipe.",
               "Jeder 25. Schlag schlägt Brot aus einem Monster. Frag nicht nach dem Rezept.",
               "Uno de cada 25 golpes le saca pan a un monstruo. No preguntes por la receta.",
               "Un colpo su 25 fa cadere del pane da un mostro. Non chiedete la ricetta.",
               "Eén op de 25 slagen slaat brood uit een monster. Vraag niet naar het recept.",
               "Um golpe em cada 25 arranca pão de um monstro. Não pergunte pela receita."),
    'poisonW': T7("Chaque coup empoisonne : les monstres perdent des PV pendant 3 secondes. Les Srams approuvent.",
                  "Each blow poisons: monsters lose HP for 3 seconds. Srams approve.",
                  "Jeder Schlag vergiftet: Monster verlieren 3 Sekunden lang LP. Die Srams sind begeistert.",
                  "Cada golpe envenena: los monstruos pierden PdV durante 3 segundos. Los Sram lo aprueban.",
                  "Ogni colpo avvelena: i mostri perdono PV per 3 secondi. Gli Sram approvano.",
                  "Elke slag vergiftigt: monsters verliezen 3 seconden lang LP. Srams keuren het goed.",
                  "Cada golpe envenena: os monstros perdem PV por 3 segundos. Os Srams aprovam."),
    'pierce': T7("Les projectiles transpercent 4 monstres de plus. Pratique pour les files d'attente.",
                 "Projectiles go through 4 more monsters. Handy for queues.",
                 "Geschosse durchbohren 4 Monster mehr. Praktisch bei Warteschlangen.",
                 "Los proyectiles atraviesan 4 monstruos más. Práctico para las colas.",
                 "I proiettili trapassano 4 mostri in più. Comodo per le code.",
                 "Projectielen gaan door 4 extra monsters. Handig bij wachtrijen.",
                 "Os projéteis atravessam mais 4 monstros. Prático para filas."),
    'bounce': T7("Les projectiles rebondissent sur 2 monstres de plus. Personne ne sait comment, c'est de la magie.",
                 "Projectiles bounce to 2 more monsters. Nobody knows how; it's magic.",
                 "Geschosse prallen auf 2 weitere Monster ab. Niemand weiß wie, es ist Magie.",
                 "Los proyectiles rebotan en 2 monstruos más. Nadie sabe cómo, es magia.",
                 "I proiettili rimbalzano su altri 2 mostri. Nessuno sa come, è magia.",
                 "Projectielen stuiteren naar 2 extra monsters. Niemand weet hoe, het is magie.",
                 "Os projéteis ricocheteiam em mais 2 monstros. Ninguém sabe como, é magia."),
    'stun': T7("De gros coups qui étourdissent longtemps les monstres. Ils voient des Tofus tourner.",
               "Heavy blows that stun monsters for a long time. They see Tofus spinning.",
               "Schwere Schläge, die Monster lange betäuben. Sie sehen Tofus kreisen.",
               "Golpes pesados que aturden mucho rato a los monstruos. Ven Tofus dando vueltas.",
               "Colpi pesanti che stordiscono a lungo i mostri. Vedono Tofu girare.",
               "Zware slagen die monsters lang verdoven. Ze zien Tofu's rondcirkelen.",
               "Golpes pesados que atordoam os monstros por muito tempo. Eles veem Tofus girando."),
}
BLOOD = T7("Soif de Sang : vole un peu de vie à chaque coup, mais frappe un peu moins fort. Le sang, ça creuse.",
           "Bloodthirst: steals a little life with every blow, but hits a little softer. Blood makes you peckish.",
           "Blutdurst: stiehlt bei jedem Schlag etwas Leben, trifft aber etwas schwächer. Blut macht hungrig.",
           "Sed de Sangre: roba algo de vida en cada golpe, pero pega algo más flojo. La sangre da hambre.",
           "Sete di Sangue: ruba un po' di vita a ogni colpo, ma picchia un po' meno forte. Il sangue mette fame.",
           "Bloeddorst: steelt bij elke slag wat leven, maar slaat iets zachter. Bloed maakt hongerig.",
           "Sede de Sangue: rouba um pouco de vida a cada golpe, mas bate um pouco mais fraco. Sangue dá fome.")


def names_of(sym, keep=None):
    """the real item(s) wearing this look: keeps the current name if it is one of them, else the lowest-level one"""
    t, g = sym.split('_'); IT = {lg: json.load(open(f'{ROOT}/work/lang_new/items_{lg}.json', encoding='utf-8'))['I']['u'] for lg in LG}
    cand = sorted((v.get('l', 1), int(k)) for k, v in IT['fr'].items() if str(v.get('t')) == t and str(v.get('g')) == g)
    if not cand: return None, None
    iid = next((i for l, i in cand if keep and IT['fr'][str(i)]['n'] == keep), cand[0][1])
    return iid, {lg: (IT[lg].get(str(iid)) or {}).get('n') or IT['fr'][str(iid)]['n'] for lg in LG}


def scale_dmg(w, k):
    w['base']['dmg'] = round(w['base']['dmg'] * k, 2)
    for l in w['lv']:
        if 'dmg' in l: l['dmg'] = round(l['dmg'] * k, 2)


def apply(C, put_ui):
    types = {w['id']: w for w in C['weapons']}; old = {u['id']: u for u in C['uniqueWeapons']}
    out = []
    for wid, of, sym, eff, blood, keep in TABLE:
        t = types[of]; params, k = EFF[eff]
        if keep:   # a 0.59 weapon kept: its calibrated numbers, without its second effect
            w = copy.deepcopy(old[keep])
            for x in SECONDARY.get(keep, []):
                if x in w['base'] and x not in t['base']: w['base'].pop(x); scale_dmg(w, 1.1)
                elif x in w['base'] and x in t['base']: w['base'][x] = t['base'][x]
        else:      # built from its type: the type's numbers, the effect's cost on the direct damage
            w = {k2: copy.deepcopy(v) for k2, v in t.items() if k2 not in ('name', 'itemName', 'desc')}
            scale_dmg(w, k)
        w['base'].update(params)
        if eff == 'crit': w['base']['crit'] = round(t['base'].get('crit', 0) + 0.25, 3)   # (on top of the daggers' own crit)
        for x in ('leech', 'blood', 'src', 'unique'): w.pop(x, None)
        if blood: scale_dmg(w, 0.8); w['blood'] = 1; w['leech'] = LEECH
        iid, nm = names_of(sym, (old.get(keep) or old.get(wid) or {}).get('name', {}).get('fr'))
        if nm: w['name'] = nm; w['itemName'] = nm; w['item'] = iid
        w.update(id=wid, of=of, acc=sym + ('_sang' if blood else ''), icon=f'it_{sym}' + ('_sang' if blood else ''),   # (bloody look + picture: build_blood060)
                 unique=1, weapon=1, type=t['type'], masteryName=t['masteryName'], masteryIcon=t.get('masteryIcon'), typeName=t['name'])
        if eff in DESC: w['desc'] = dict(DESC[eff])
        else: w['desc'] = {lg: old[keep]['desc'][lg] for lg in LG}   # (slow / pierceAll / burn / stack: their own 0.59 texts, still true)
        if blood: w['desc'] = {lg: w['desc'][lg] + ' ' + BLOOD[lg] for lg in LG}
        w['eff'] = eff
        out.append(w)
    C['uniqueWeapons'] = out
    C['weaponEvo'] = {}
    for t in C['weapons']: t['typeOnly'] = 1
    return out
