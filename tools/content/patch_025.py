"""Beta 0.25 content (lot 5C), applied on top of patch_023: unique weapons (2 per weapon type, real client items, skins
rendered then by build_weapons23, retired: weapon looks are tools/assets/build_acc060.py weapons now), weapon fusion (a maxed weapon fused with a characteristic), weapon sounds of
the client's own attack animations.  ->  game/data/content.json
usage: python tools/content/patch_025.py"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
import _root
import json, copy
import patch_023 as P3
import langdata as LD

C, T, G = P3.C, P3.T, P3.G

# ---------------------------------------------------------------- weapon sounds: the client's attack animations
# (sounds.json chars: anim11 wand / anim12 staff = rapid_swish, anim13 dagger / anim16 shovel = epee_1m)
for w in C['weapons']:
    w['snd'] = {'baguette': 'rapid_swish', 'baton': 'rapid_swish', 'dague': 'epee_1m', 'pelle': 'epee_1m'}.get(w['id'], w['snd'])
    if w['id'] == 'hache': w['fx'] = []; w['base']['cleave'] = 1   # 0.25: a drawn cleave (the old swoosh was unreadable)

# ---------------------------------------------------------------- unique weapons
# of: weapon type; skin: acc key; item: client item (name in 7 languages); set: parameters over the type's (level 1);
# mul: multipliers of the type's numbers (every level). Their own effects (weapons.js): bolt, wave, chakram, cloud,
# firePatch, quake, stack, cake, confuse.
U = [
    ('arc_ange', 'arc', '2_31', 6451, dict(pierce=99, homing=3.0, holy=1, col='#fff1a8'), dict(dmg=1.1),
     T('Ses flèches bénies traversent tous les monstres. Même les Bouftous prient avant de se faire toucher.', 'Its blessed arrows pierce every monster. Even Gobballs pray before being hit.', 'Seine gesegneten Pfeile durchbohren alle Monster. Sogar Fresssäcke beten vor dem Treffer.', 'Sus flechas benditas atraviesan a todos los monstruos. Hasta los Jalatós rezan antes del impacto.', 'Le sue frecce benedette trapassano tutti i mostri. Persino i Bufotti pregano prima del colpo.', 'Zijn gezegende pijlen doorboren alle monsters. Zelfs Boefjes bidden voor de inslag.', 'As suas flechas abençoadas trespassam todos os monstros. Até os Papatudos rezam antes do impacto.')),
    ('arc_feugeuf', 'arc', '2_27', 5096, dict(aoe=55, burn=6, fire=1, col='#ff7a2a'), dict(dmg=1.15),
     T('Des flèches qui explosent et brûlent. Le Feugeuf, lui, n\'a jamais demandé à être un arc.', 'Arrows that explode and burn. The Feugeuf never asked to become a bow.', 'Pfeile, die explodieren und brennen. Der Feugeuf wollte nie ein Bogen werden.', 'Flechas que explotan y queman. El Feugeuf nunca pidió ser un arco.', 'Frecce che esplodono e bruciano. Il Feugeuf non ha mai chiesto di diventare un arco.', 'Pijlen die ontploffen en branden. De Feugeuf vroeg nooit om een boog te worden.', 'Flechas que explodem e queimam. O Feugeuf nunca pediu para ser um arco.')),
    ('pieu_vampirique', 'baguette', '3_14', 1362, dict(leech=0.004, vamp=1, col='#c0204a', homing=6.0), dict(dmg=1.15),
     T('Des orbes de sang qui suivent leur proie et vous rendent une miette de vie. Un vampire au régime.', 'Blood orbs that chase their prey and give you a crumb of life. A vampire on a diet.', 'Blutkugeln, die ihre Beute verfolgen und dir einen Krümel Leben geben. Ein Vampir auf Diät.', 'Orbes de sangre que persiguen a su presa y te dan una migaja de vida. Un vampiro a dieta.', 'Sfere di sangue che inseguono la preda e ti ridanno una briciola di vita. Un vampiro a dieta.', 'Bloedbollen die hun prooi achtervolgen en je een kruimel leven geven. Een vampier op dieet.', 'Orbes de sangue que perseguem a presa e devolvem uma migalha de vida. Um vampiro de dieta.')),
    ('baguette_glace', 'baguette', '3_2', 165, dict(slow=0.5, slowDur=1.6, ice=1, aoe=40, col='#8fe4ff'), dict(dmg=1.0),
     T('Des éclats de glace qui ralentissent tout ce qu\'ils touchent. Idéal pour garder la Bière de Bouftou au frais.', 'Ice shards that slow whatever they hit. Perfect to keep your Gobball Beer cold.', 'Eissplitter, die alles verlangsamen. Ideal, um das Fresssackbier kühl zu halten.', 'Esquirlas de hielo que ralentizan todo lo que tocan. Ideal para mantener fría la Cerveza de Jalató.', 'Schegge di ghiaccio che rallentano tutto ciò che colpiscono. Perfette per tenere al fresco la Birra di Bufotto.', 'IJssplinters die alles vertragen wat ze raken. Perfect om je Boefjesbier koud te houden.', 'Lascas de gelo que abrandam tudo o que tocam. Ideal para manter fresca a Cerveja de Papatudo.')),
    ('god_rod', 'baton', '4_7', 200, dict(bolt=1), dict(dmg=1.1),
     T('Chaque coup appelle la foudre sur un monstre au hasard. Le nom est modeste, le bâton beaucoup moins.', 'Every swing calls lightning down on a random monster. The name is modest, the staff much less so.', 'Jeder Schlag ruft einen Blitz auf ein zufälliges Monster. Der Name ist bescheiden, der Stab weniger.', 'Cada golpe invoca un rayo sobre un monstruo al azar. El nombre es modesto, el bastón mucho menos.', 'Ogni colpo richiama un fulmine su un mostro a caso. Il nome è modesto, il bastone molto meno.', 'Elke slag roept bliksem op een willekeurig monster. De naam is bescheiden, de staf veel minder.', 'Cada golpe chama um raio sobre um monstro ao acaso. O nome é modesto, o bastão muito menos.')),
    ('canne_bonbon', 'baton', '4_48', 7037, dict(confuse=1.6, knock=110), dict(dmg=1.05),
     T('Mamie Bonbon frappe fort : les monstres touchés repartent tout étourdis, sans savoir où aller.', 'Granny Candy hits hard: the monsters she hits wander off dizzy, not knowing where to go.', 'Oma Bonbon schlägt hart zu: Getroffene Monster torkeln verwirrt davon.', 'La Abuela Caramelo pega fuerte: los monstruos golpeados se marchan mareados, sin saber adónde ir.', 'Nonna Caramella picchia duro: i mostri colpiti se ne vanno storditi, senza sapere dove andare.', 'Oma Snoepje slaat hard: geraakte monsters dwalen duizelig rond.', 'A Avó Rebuçado bate com força: os monstros atingidos ficam tontos, sem saber para onde ir.')),
    ('dagues_rat_noir', 'dague', '5_59', 8444, dict(crit=0.35, bleed=2), dict(dmg=1.1),
     T('Des coups critiques à la pelle et des plaies qui saignent. Le Rat Noir ne se lave jamais les dagues.', 'Critical hits galore and bleeding wounds. The Black Rat never washes his daggers.', 'Kritische Treffer zuhauf und blutende Wunden. Die Schwarze Ratte wäscht ihre Dolche nie.', 'Golpes críticos a montones y heridas que sangran. La Rata Negra nunca lava sus dagas.', 'Colpi critici a palate e ferite che sanguinano. Il Ratto Nero non lava mai i pugnali.', 'Kritieke treffers bij de vleet en bloedende wonden. De Zwarte Rat wast zijn dolken nooit.', 'Golpes críticos aos montes e feridas que sangram. O Rato Negro nunca lava as adagas.')),
    ('chakra_style', 'dague', '5_8', 220, dict(chakram=1), dict(dmg=1.0),
     T('Chaque coup lance aussi une lame tournoyante qui revient comme un boomerang. Style garanti.', 'Every stab also throws a spinning blade that comes back like a boomerang. Style guaranteed.', 'Jeder Stich wirft auch eine wirbelnde Klinge, die wie ein Bumerang zurückkehrt. Stil garantiert.', 'Cada golpe lanza también una hoja giratoria que vuelve como un bumerán. Estilo garantizado.', 'Ogni colpo lancia anche una lama rotante che torna come un boomerang. Stile garantito.', 'Elke steek werpt ook een draaiend lemmet dat terugkeert als een boemerang. Stijl gegarandeerd.', 'Cada golpe lança também uma lâmina giratória que volta como um bumerangue. Estilo garantido.')),
    ('epee_dark_vlad', 'epee', '6_61', 7193, dict(wave=1), dict(dmg=1.1),
     T('Chaque coup projette un croissant de flammes sombres qui traverse tout. Dark Vlad n\'est plus là pour se plaindre.', 'Every swing sends a crescent of dark flames that cuts through everything. Dark Vlad is no longer around to complain.', 'Jeder Hieb schleudert eine Sichel aus dunklen Flammen, die alles durchschneidet. Dark Vlad kann sich nicht mehr beschweren.', 'Cada tajo lanza una media luna de llamas oscuras que lo atraviesa todo. Dark Vlad ya no está para quejarse.', 'Ogni fendente lancia una mezzaluna di fiamme oscure che trapassa tutto. Dark Vlad non c\'è più per lamentarsi.', 'Elke slag werpt een sikkel van duistere vlammen die alles doorsnijdt. Dark Vlad is er niet meer om te klagen.', 'Cada golpe lança um crescente de chamas sombrias que atravessa tudo. O Dark Vlad já não está cá para se queixar.')),
    ('epee_qui_pete', 'epee', '6_75', 8676, dict(cloud=1), dict(dmg=1.05),
     T('Chaque coup laisse un petit nuage toxique. Elle porte bien son nom, et son odeur aussi.', 'Every swing leaves a little toxic cloud. It lives up to its name, and to its smell.', 'Jeder Hieb hinterlässt eine kleine Giftwolke. Sie trägt ihren Namen zu Recht, ihren Geruch auch.', 'Cada tajo deja una nubecita tóxica. Hace honor a su nombre, y a su olor.', 'Ogni colpo lascia una nuvoletta tossica. Fa onore al suo nome, e al suo odore.', 'Elke slag laat een giftig wolkje achter. Ze doet haar naam eer aan, en haar geur ook.', 'Cada golpe deixa uma nuvenzinha tóxica. Faz jus ao nome, e ao cheiro.')),
    ('kaiser', 'marteau', '7_10', 233, dict(quake=1, stun=0.8), dict(dmg=1.0, radius=1.15),
     T('Le sol tremble deux fois : un coup, puis une onde de choc plus large. L\'Empereur ne frappe jamais qu\'une fois… enfin, presque.', 'The ground shakes twice: a blow, then a wider shockwave. The Emperor only strikes once… well, almost.', 'Der Boden bebt zweimal: ein Schlag, dann eine größere Schockwelle. Der Kaiser schlägt nur einmal zu… fast.', 'El suelo tiembla dos veces: un golpe y luego una onda expansiva más amplia. El Emperador solo golpea una vez… casi.', 'Il suolo trema due volte: un colpo, poi un\'onda d\'urto più ampia. L\'Imperatore colpisce una volta sola… quasi.', 'De grond beeft twee keer: een slag, dan een bredere schokgolf. De Keizer slaat maar één keer… bijna.', 'O chão treme duas vezes: um golpe, depois uma onda de choque maior. O Imperador só bate uma vez… quase.')),
    ('marteau_dragoeuf', 'marteau', '7_59', 8294, dict(firePatch=1), dict(dmg=1.05),
     T('Chaque impact laisse le sol en feu. Un Dragoeuf ne fait jamais les choses à moitié cuites.', 'Every impact leaves the ground on fire. A Dragoeuf never does things half-baked.', 'Jeder Aufprall setzt den Boden in Brand. Ein Drachenei macht nichts halbgar.', 'Cada impacto deja el suelo en llamas. Un Dragohuevo nunca hace las cosas a medio cocer.', 'Ogni impatto lascia il suolo in fiamme. Un Dragovo non fa mai le cose a metà cottura.', 'Elke inslag zet de grond in brand. Een Drakenei doet niets half gaar.', 'Cada impacto deixa o chão em chamas. Um Dragovo nunca faz as coisas meio cozidas.')),
    ('ares', 'pelle', '8_9', 250, dict(stack=1), dict(dmg=1.0),
     T('Chaque coup qui touche rend le suivant plus fort (jusqu\'à +60 %). Arrêtez de frapper et la rage retombe.', 'Every hit makes the next one stronger (up to +60%). Stop hitting and the rage fades.', 'Jeder Treffer macht den nächsten stärker (bis +60 %). Hör auf zu schlagen, und die Wut verfliegt.', 'Cada golpe que acierta hace el siguiente más fuerte (hasta +60 %). Deja de golpear y la rabia se esfuma.', 'Ogni colpo a segno rende il successivo più forte (fino a +60%). Smetti di colpire e la rabbia svanisce.', 'Elke treffer maakt de volgende sterker (tot +60%). Stop met slaan en de woede zakt.', 'Cada golpe certeiro torna o seguinte mais forte (até +60%). Pare de bater e a raiva passa.')),
    ('pelle_gateau', 'pelle', '8_43', 8417, dict(cake=0.04, dig=0.25), dict(dmg=1.0),
     T('Elle déterre des kamas et, parfois, un gâteau. Personne ne sait pourquoi il y avait un gâteau sous terre.', 'It digs up kamas and, sometimes, a cake. Nobody knows why there was a cake underground.', 'Sie gräbt Kamas aus und manchmal einen Kuchen. Niemand weiß, warum da ein Kuchen in der Erde war.', 'Desentierra kamas y, a veces, un pastel. Nadie sabe por qué había un pastel bajo tierra.', 'Dissotterra kama e, a volte, una torta. Nessuno sa perché ci fosse una torta sottoterra.', 'Ze graaft kama\'s op en soms een taart. Niemand weet waarom er een taart onder de grond lag.', 'Desenterra kamas e, às vezes, um bolo. Ninguém sabe porque havia um bolo debaixo da terra.')),
    ('bardiche', 'hache', '19_3', 2604, dict(knock=90), dict(dmg=1.05, range=1.35, width=1.15),
     T('Une hache d\'arme à très longue portée qui repousse les monstres. La Milice garde ses distances, et vous aussi.', 'A very long reach poleaxe that pushes monsters back. The Militia keeps its distance, and so do you.', 'Eine Hellebarde mit sehr großer Reichweite, die Monster zurückstößt. Die Miliz hält Abstand, du auch.', 'Una alabarda de muy largo alcance que repele a los monstruos. La Milicia guarda las distancias, y tú también.', 'Un\'alabarda a lunghissima portata che respinge i mostri. La Milizia mantiene le distanze, e anche tu.', 'Een hellebaard met heel groot bereik die monsters terugduwt. De Militie houdt afstand, jij ook.', 'Uma alabarda de alcance muito longo que repele os monstros. A Milícia mantém a distância, e você também.')),
    ('hache_zoth', 'hache', '19_47', 8827, dict(sides=2, bleed=1), dict(dmg=1.05),
     T('Frappe devant et derrière en même temps. Les Guerriers Zoth n\'ont jamais aimé qu\'on les prenne à revers.', 'Strikes in front and behind at once. Zoth Warriors never liked being caught from behind.', 'Schlägt gleichzeitig nach vorn und nach hinten. Zoth-Krieger mögen keine Angriffe von hinten.', 'Golpea delante y detrás a la vez. A los Guerreros Zoth nunca les gustó que los pillaran por la espalda.', 'Colpisce davanti e dietro allo stesso tempo. Ai Guerrieri Zoth non è mai piaciuto essere presi alle spalle.', 'Slaat tegelijk voor en achter. Zoth-krijgers houden er niet van van achteren gepakt te worden.', 'Golpeia à frente e atrás ao mesmo tempo. Os Guerreiros Zoth nunca gostaram de ser apanhados pelas costas.')),
]
C['uniqueRate'] = 0.15   # chance that an offered weapon is one of its type's unique weapons (x luck)
UNIQ = []
for uid, of, skin, item, setp, mul, desc in U:
    b = next(w for w in C['weapons'] if w['id'] == of)
    w = copy.deepcopy(b)
    w.update(id=uid, of=of, unique=1, acc=skin, icon=f'it_{skin}', itemName=LD.item(item), name=LD.item(item), desc=desc)
    for d in [w['base']] + w['lv']:
        for k, f in mul.items():
            if k in d: d[k] = round(d[k] * f, 2)
    w['base'].update(setp)
    UNIQ.append(w)
    # the type's three finales, without their skin (a unique weapon keeps its own look)
    C['weaponEvo'][uid] = [dict(e, skin=None, skinName=None, icon=w['icon']) for e in copy.deepcopy(C['weaponEvo'][of])]
C['uniqueWeapons'] = UNIQ

# ---------------------------------------------------------------- weapon cooldown pass (as patch_023's CD_PASS): every
# weapon benched alone at level 6 (sim_node.js BENCH=weapons, two passes: 90 s then 2 x 240 s), target the median of the
# weapon types (+20 % for the unique weapons, their effects count),
# f = ratio ** 0.6 outside [0.8, 1.25] x target, half on the cooldown, half on the damage
WCD_PASS = dict(baguette=0.6, arc_ange=0.6, epee_dark_vlad=1.75, ares=1.2, dague=1.35, arc=0.65, canne_bonbon=0.75, epee_qui_pete=1.8, marteau=1.4, pieu_vampirique=0.6, dagues_rat_noir=1.35, kaiser=3.7, bardiche=2.05, baguette_glace=1.25, chakra_style=1.75, marteau_dragoeuf=2.95, god_rod=1.25, hache=1.3, hache_zoth=1.45)
for w in C['weapons'] + UNIQ:
    f = WCD_PASS.get(w['id'])
    if not f: continue
    k = f ** 0.5
    for d in [w['base']] + w['lv']:
        if 'cd' in d: d['cd'] = round(max(0.3, d['cd'] * k), 2)
        if 'dmg' in d: d['dmg'] = round(d['dmg'] / k, 1)

# ---------------------------------------------------------------- weapon fusion (once the weapon has its finale and
# every spell is maxed): the weapon takes a characteristic's element. mul: weapon numbers; stats: run stats;
# fx: what weapons.js draws / does.
C['fusions'] = [
    dict(id='force', stat='force', icon='Icon_33', color='#c08a3e', mul=dict(dmg=0.3, range=0.35, width=0.35, radius=0.35, size=0.25), fx='earth',
         name=T('Fusion de la Terre', 'Earth Fusion', 'Erdfusion', 'Fusión de Tierra', 'Fusione della Terra', 'Aardefusie', 'Fusão da Terra'),
         desc=T('Force : l\'arme grandit (+35 % de zone, +30 % de dégâts) et chaque coup fend le sol.', 'Strength: the weapon grows (+35% area, +30% damage) and every blow cracks the ground.', 'Stärke: Die Waffe wächst (+35 % Fläche, +30 % Schaden) und jeder Schlag spaltet den Boden.', 'Fuerza: el arma crece (+35 % de zona, +30 % de daño) y cada golpe agrieta el suelo.', 'Forza: l\'arma cresce (+35% di area, +30% di danni) e ogni colpo spacca il suolo.', 'Kracht: het wapen groeit (+35% bereik, +30% schade) en elke slag splijt de grond.', 'Força: a arma cresce (+35% de zona, +30% de dano) e cada golpe racha o chão.')),
    dict(id='intelligence', stat='intelligence', icon='Icon_34', color='#ff6a1e', mul=dict(dmg=0.15), fx='fire', aura=dict(radius=110, k=0.12, tick=0.4),
         name=T('Fusion du Feu', 'Fire Fusion', 'Feuerfusion', 'Fusión de Fuego', 'Fusione del Fuoco', 'Vuurfusie', 'Fusão do Fogo'),
         desc=T('Intelligence : une aura de flammes brûle les monstres proches et chaque coup les enflamme.', 'Intelligence: an aura of flames burns nearby monsters and every hit sets them ablaze.', 'Intelligenz: Eine Flammenaura verbrennt nahe Monster und jeder Treffer setzt sie in Brand.', 'Inteligencia: un aura de llamas quema a los monstruos cercanos y cada golpe los incendia.', 'Intelligenza: un\'aura di fiamme brucia i mostri vicini e ogni colpo li incendia.', 'Intelligentie: een vlammenaura verbrandt nabije monsters en elke treffer zet ze in brand.', 'Inteligência: uma aura de chamas queima os monstros próximos e cada golpe incendeia-os.')),
    dict(id='chance', stat='chance', icon='Icon_35', color='#3fa8ff', mul=dict(dmg=0.15), fx='water',
         name=T('Fusion de l\'Eau', 'Water Fusion', 'Wasserfusion', 'Fusión de Agua', 'Fusione dell\'Acqua', 'Waterfusie', 'Fusão da Água'),
         desc=T('Chance : chaque coup éclabousse les monstres autour, et un sur dix fait tomber des kamas.', 'Chance: every hit splashes the monsters around, and one in ten drops kamas.', 'Glück: Jeder Treffer bespritzt die Monster ringsum, jeder zehnte lässt Kamas fallen.', 'Suerte: cada golpe salpica a los monstruos de alrededor, y uno de cada diez suelta kamas.', 'Fortuna: ogni colpo schizza i mostri intorno, e uno su dieci fa cadere kama.', 'Geluk: elke treffer bespat de monsters rondom, en één op tien laat kama\'s vallen.', 'Sorte: cada golpe salpica os monstros à volta, e um em cada dez deixa cair kamas.')),
    dict(id='agilite', stat='agilite', icon='Icon_36', color='#58d68d', mul=dict(cd=-0.35), stats=dict(speed=0.15), fx='air',
         name=T('Fusion de l\'Air', 'Air Fusion', 'Luftfusion', 'Fusión de Aire', 'Fusione dell\'Aria', 'Luchtfusie', 'Fusão do Ar'),
         desc=T('Agilité : l\'arme frappe 35 % plus vite, vous courez plus vite et le vent tranche avec vous.', 'Agility: the weapon strikes 35% faster, you run faster and the wind slices along.', 'Flinkheit: Die Waffe schlägt 35 % schneller, du läufst schneller und der Wind schneidet mit.', 'Agilidad: el arma golpea un 35 % más rápido, corres más y el viento corta contigo.', 'Agilità: l\'arma colpisce il 35% più veloce, corri più veloce e il vento taglia con te.', 'Behendigheid: het wapen slaat 35% sneller, je rent sneller en de wind snijdt mee.', 'Agilidade: a arma golpeia 35% mais rápido, corre mais depressa e o vento corta consigo.')),
    dict(id='sagesse', stat='sagesse', icon='Icon_22', color='#b07cff', mul=dict(dmg=0.1), stats=dict(growth=0.2), fx='stars', stars=dict(n=4, k=0.45, radius=120),
         name=T('Fusion Cosmique', 'Cosmic Fusion', 'Kosmische Fusion', 'Fusión Cósmica', 'Fusione Cosmica', 'Kosmische fusie', 'Fusão Cósmica'),
         desc=T('Sagesse : quatre étoiles tournent autour de vous et frappent, la nuit s\'invite et l\'expérience coule (+20 %).', 'Wisdom: four stars orbit and strike, the night sky joins in and experience flows (+20%).', 'Weisheit: Vier Sterne kreisen und treffen, der Nachthimmel zieht ein und Erfahrung fließt (+20 %).', 'Sabiduría: cuatro estrellas giran y golpean, la noche se cuela y la experiencia fluye (+20 %).', 'Saggezza: quattro stelle ruotano e colpiscono, la notte si fa avanti e l\'esperienza scorre (+20%).', 'Wijsheid: vier sterren draaien en raken, de nacht schuift aan en ervaring stroomt (+20%).', 'Sabedoria: quatro estrelas giram e atacam, a noite instala-se e a experiência flui (+20%).')),
    dict(id='vitalite', stat='vitalite', icon='Icon_0', color='#e8d24a', mul=dict(dmg=0.1), stats=dict(maxhp=0.35, armor=3), fx='life',
         name=T('Fusion Vitale', 'Vital Fusion', 'Lebensfusion', 'Fusión Vital', 'Fusione Vitale', 'Levensfusie', 'Fusão Vital'),
         desc=T('Vitalité : +35 % de PV max et +3 résistance, et l\'arme sème des feuilles d\'or à chaque coup.', 'Vitality: +35% max HP and +3 armour, and the weapon scatters golden leaves with every blow.', 'Vitalität: +35 % max. LP und +3 Resistenz, und die Waffe streut bei jedem Schlag goldene Blätter.', 'Vitalidad: +35 % de PV máx. y +3 de resistencia, y el arma esparce hojas doradas en cada golpe.', 'Vitalità: +35% PV max e +3 resistenza, e l\'arma sparge foglie d\'oro a ogni colpo.', 'Vitaliteit: +35% max. LP en +3 weerstand, en het wapen strooit gouden bladeren bij elke slag.', 'Vitalidade: +35% PV máx. e +3 de resistência, e a arma espalha folhas douradas a cada golpe.')),
]

UI = {
    'unique_tag': T('Arme unique', 'Unique weapon', 'Einzigartige Waffe', 'Arma única', 'Arma unica', 'Uniek wapen', 'Arma única'),
    'unique_found': T('Arme unique : {n} !', 'Unique weapon: {n}!', 'Einzigartige Waffe: {n}!', '¡Arma única: {n}!', 'Arma unica: {n}!', 'Uniek wapen: {n}!', 'Arma única: {n}!'),
    'fusion_tag': T('Fusion', 'Fusion', 'Fusion', 'Fusión', 'Fusione', 'Fusie', 'Fusão'),
    'fusion_done': T('{w} fusionne : {n} !', '{w} fuses: {n}!', '{w} verschmilzt: {n}!', '¡{w} se fusiona: {n}!', '{w} si fonde: {n}!', '{w} versmelt: {n}!', '{w} funde-se: {n}!'),
    'fusion_note': T('Une seule fusion par partie : l\'arme prend l\'élément pour de bon.', 'One fusion per run: the weapon takes the element for good.', 'Eine Fusion pro Lauf: Die Waffe behält das Element.', 'Una sola fusión por partida: el arma adopta el elemento para siempre.', 'Una sola fusione per partita: l\'arma prende l\'elemento per sempre.', 'Eén fusie per run: het wapen houdt het element voorgoed.', 'Uma só fusão por partida: a arma fica com o elemento de vez.'),
}
for k, v in UI.items():
    for lg, txt in v.items(): C['ui'][lg][k] = txt

if __name__ == '__main__':
    json.dump(C, open(f'{G}/data/content.json', 'w'), ensure_ascii=False, separators=(',', ':'))
    print('0.25 ok', len(UNIQ), 'unique weapons,', len(C['fusions']), 'fusions')
