"""Beta 0.52 content, applied on top of patch_051.   usage: python tools/content/patch_052.py"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
import _root
import json
import patch_051 as P5

C, G = P5.C, P5.G
P4 = P5.P4; T = P4.T

# the Abraknes have nothing to do in the Champs de Bonta: the Champa Rouge instead (a field mushroom, the Champa's
# sprite in its own colours from sl.db: tools/assets/build_coloured52.py 1335 1335r_z36 3.6 f14107,eef2fc,-1 art), same place
P4.mon('champa_rouge', 653, 90, 8.0, 115, 0.8, 'chase', 13, None,
       T('Un champignon rouge, plus vif que ses cousins verts.', 'A red mushroom, quicker than its green cousins.', 'Ein roter Pilz, flinker als seine grünen Vettern.',
         'Una seta roja, más rápida que sus primas verdes.', 'Un fungo rosso, più svelto dei cugini verdi.', 'Een rode paddenstoel, sneller dan zijn groene neven.',
         'Um cogumelo vermelho, mais rápido do que os primos verdes.'))
C['monsters']['champa_rouge'].update(sprite='1335r_z36', colors=['f14107', 'eef2fc'], art='p1335_f14107')
B = next(m for m in C['maps'] if m['id'] == 'bonta')
for w in B['waves']: w[2] = [['champa_rouge' if e[0] == 'abrakne' else e[0], e[1]] for e in w[2]]
for e in B['events']:
    if e[2] == 'abrakne': e[2] = 'champa_rouge'
C['monsters'].pop('abrakne', None)

# the vampiric weapons are weapons of their own, not versions of another one: their own description (the blows of
# their source, then the life steal), and 10 % less damage than the weapon they copy (they heal)
LK = 0.9
SRC = {w['id']: w for w in C['weapons'] + C['uniqueWeapons'] if not w.get('blood')}
LS = T('Vol de vie : {a} % des dégâts infligés, jusqu\'à {b} % au niveau 6.', 'Life steal: {a}% of the damage dealt, up to {b}% at level 6.',
       'Lebensraub: {a} % des verursachten Schadens, bis zu {b} % auf Stufe 6.', 'Robo de vida: {a} % del daño infligido, hasta {b} % al nivel 6.',
       'Furto di vita: {a}% dei danni inflitti, fino al {b}% al livello 6.', 'Levensroof: {a}% van de aangerichte schade, tot {b}% op niveau 6.',
       'Roubo de vida: {a}% do dano causado, até {b}% no nível 6.')
pc = lambda v, lg: f'{v * 100:.3f}' if lg == 'en' else f'{v * 100:.3f}'.replace('.', ',')
for w in C['uniqueWeapons']:
    if not w.get('blood'): continue
    s = SRC[w['src']]
    w['desc'] = {lg: f"{s['desc'][lg]} " + LS[lg].format(a=pc(w['leech'][0], lg), b=pc(w['leech'][-1], lg)) for lg in s['desc']}
    for d in [w['base']] + w['lv']:
        if 'dmg' in d: d['dmg'] = round(d['dmg'] * LK, 2)

# 0.52: scheduled elites: one every 30 s (two from 3:00, three from 6:00), their life over their head; their life
# grows each time (x2 at most) up to 30 % of the zone's final boss's life at the end of the run (extras.js updateElites);
# a chest every third wave, half their usual XP
C['elites'] = dict(t0=30, every=30, n=[[0, 1], [3, 2], [6, 3]], grow=2, cap=0.3, lvl=40, xpK=0.5, chest=3)
P4.P3.put_ui({'elite_comes': T('Un élite approche : {n} !', 'An elite is coming: {n}!', 'Ein Elitemonster naht: {n}!', '¡Se acerca un élite: {n}!',
                               'Arriva un élite: {n}!', 'Er komt een elite aan: {n}!', 'Aproxima-se um elite: {n}!')})

# ------------------------------------------------------------------ the Goultard secret: Dark Vlad beaten in
# Difficile opens the last zone, his clearing taken over by Goultard (red, blood, cracks: build_vlad51.py goultard), with
# the monsters of Qu'Tan's dungeon (sprite 1664 in their sl.db colours: build_coloured52.py; Qu'Tan 1665) and Goultard
# himself as its final boss (the client's NPC sprite 9272: build_mobs20.py 9272:boss:z=6, art build_art38-style a9272).
# The highest zone, over Grobe.
A = T   # (attack names: the client's are English test names, '[tag]…')
def demon(mid, did, name, sheet, cols, hp, dmg, sp, xp, beh, size, atk, attacks, flavor, scale=1.0):
    P4.mon(mid, did, hp, dmg, sp, xp, beh, size, atk, flavor, scale)
    C['monsters'][mid].update(name=name, attacks=attacks, sprite=sheet, colors=cols, art=(f'p1664_{cols[0]}' if cols else 'a1664'))
demon('sbire_qutan', 1197, T("Sbire de Qu'Tan", "Ku'Tan's Henchman", "Lakai von Ku'Tan", "Esbirro de Ku'Tan", "Scagnozzo di Ku'Tan", "Ku'Tan's Volgeling", "Seguidor de Ku'Tan"),
      '1664_z36', None, 420, 26.0, 100, 2.2, 'chase', 16, None,
      [A('Flèche magique', 'Magic Dart', 'Magischer Pfeil', 'Dardo mágico', 'Dardo magico', 'Magische pijl', 'Dardo mágico'),
       A('Étreinte vampirique', 'Vampire Hug', 'Vampirumarmung', 'Abrazo vampírico', 'Abbraccio vampirico', 'Vampierknuffel', 'Abraço vampírico'),
       A('Lenteur', 'Slowness', 'Langsamkeit', 'Lentitud', 'Lentezza', 'Traagheid', 'Lentidão')],
      T("Le petit démon de Qu'Tan. Il fonce droit sur vous.", "Ku'Tan's little demon. It rushes straight at you.", "Ku'Tans kleiner Dämon. Er stürmt direkt auf dich los.",
        "El pequeño demonio de Ku'Tan. Va directo hacia ti.", "Il piccolo demone di Ku'Tan. Ti si lancia contro.", "Ku'Tans kleine demoon. Hij stormt recht op je af.", "O pequeno demónio de Ku'Tan. Avança direito a ti."))
demon('diablotin_rouge', 1198, T('Diablotin Rouge', 'Red Imp', 'Rotes Teufelchen', 'Diablotín rojo', 'Diavoletto Rosso', 'Rode Imp', 'Diabinho Vermelho'),
      '1664r_z36', ['ff0000', 'ea0404', 'df1a1a'], 300, 24.0, 150, 1.6, 'erratic', 13, None,
      [A('Toucher mortel', 'Deadly Touch', 'Tödliche Berührung', 'Toque mortal', 'Tocco mortale', 'Dodelijke aanraking', 'Toque mortal'),
       A('Pensée positive', 'Positive Thinking', 'Positives Denken', 'Pensamiento positivo', 'Pensiero positivo', 'Positief denken', 'Pensamento positivo')],
      T('Un diablotin rapide qui court en tous sens.', 'A quick imp running every which way.', 'Ein flinkes Teufelchen, das kreuz und quer rennt.', 'Un diablotín rápido que corre en todas direcciones.',
        'Un diavoletto veloce che corre in ogni direzione.', 'Een snelle imp die alle kanten op rent.', 'Um diabinho rápido que corre em todas as direções.'), 0.85)
demon('diablotin_jaune', 1199, T('Diablotin Jaune', 'Yellow Imp', 'Gelbes Teufelchen', 'Diablotín amarillo', 'Diavoletto Giallo', 'Gele Imp', 'Diabinho Amarelo'),
      '1664j_z36', ['ffff66', 'ffff00', 'f5f522'], 340, 25.0, 120, 1.8, 'charge', 13, None,
      [A('Toucher étourdissant', 'Dizzying Touch', 'Schwindelerregende Berührung', 'Toque mareante', 'Tocco vertiginoso', 'Duizelingwekkende aanraking', 'Toque estonteante')],
      T('Un diablotin qui charge sans prévenir.', 'An imp that charges without warning.', 'Ein Teufelchen, das ohne Vorwarnung losstürmt.', 'Un diablotín que embiste sin avisar.',
        'Un diavoletto che carica senza preavviso.', 'Een imp die zonder waarschuwing aanvalt.', 'Um diabinho que investe sem aviso.'), 0.85)
demon('diablotin_bleu', 1200, T('Diablotin Bleu', 'Blue Imp', 'Blaues Teufelchen', 'Diablotín azul', 'Diavoletto Blu', 'Blauwe Imp', 'Diabinho Azul'),
      '1664b_z36', ['26d6f2', '56dff5', '52adeb'], 320, 22.0, 95, 2.0, 'ranged', 13, dict(kind='proj', fx=1012, dmg=18, speed=160, cd=3.0, range=300),
      [A('Illumination obscure', 'Dark Illumination', 'Dunkle Erleuchtung', 'Iluminación oscura', 'Illuminazione oscura', 'Duistere verlichting', 'Iluminação sombria'),
       A('Météore obscur', 'Dark Meteor', 'Dunkler Meteor', 'Meteoro oscuro', 'Meteora oscura', 'Duistere meteoor', 'Meteoro sombrio')],
      T('Un diablotin qui tire de loin.', 'An imp that shoots from afar.', 'Ein Teufelchen, das aus der Ferne schießt.', 'Un diablotín que dispara desde lejos.',
        'Un diavoletto che spara da lontano.', 'Een imp die van ver schiet.', 'Um diabinho que dispara de longe.'), 0.85)
demon('diablotin_vert', 1203, T('Diablotin Vert', 'Green Imp', 'Grünes Teufelchen', 'Diablotín verde', 'Diavoletto Verde', 'Groene Imp', 'Diabinho Verde'),
      '1664v_z36', ['52eb80', '13fb21', '39a459'], 330, 24.0, 105, 1.9, 'invisible', 13, None,
      [A('Parole obscure', 'Dark Word', 'Dunkles Wort', 'Palabra oscura', 'Parola oscura', 'Duister woord', 'Palavra sombria'),
       A('Parole abyssale', 'Abyssal Word', 'Abgründiges Wort', 'Palabra abisal', 'Parola abissale', 'Abyssaal woord', 'Palavra abissal')],
      T('Un diablotin qui disparaît puis surgit à côté de vous.', 'An imp that vanishes, then pops up next to you.', 'Ein Teufelchen, das verschwindet und neben dir auftaucht.',
        'Un diablotín que desaparece y surge a tu lado.', 'Un diavoletto che sparisce e ricompare accanto a te.', 'Een imp die verdwijnt en naast je opduikt.', 'Um diabinho que desaparece e surge ao teu lado.'), 0.85)
demon('petit_demon_rapide', 1218, T('Petit Démon Rapide', 'Quick Little Demon', 'Kleiner schneller Dämon', 'Demoncete veloz', 'Piccolo demone rapido', 'Snelle Kleine Demoon', 'Pequeno Demônio Veloz'),
      '1664p_z36', ['A1F2F2', 'D7A0D9', 'A1F2F2'], 260, 22.0, 175, 1.6, 'chase', 12, None,
      [A('Morsure démoniaque', 'Demonic Bite', 'Dämonischer Biss', 'Mordisco demoníaco', 'Morso demoniaco', 'Demonische beet', 'Mordida demoníaca')],
      T('Petit, fragile et très rapide.', 'Small, frail and very fast.', 'Klein, zerbrechlich und sehr schnell.', 'Pequeño, frágil y muy rápido.', 'Piccolo, fragile e velocissimo.', 'Klein, breekbaar en heel snel.', 'Pequeno, frágil e muito rápido.'), 0.75)
demon('envoye_abysses', 1219, T('Envoyé des Abysses', 'Abyssal Envoy', 'Gesandter des Abgrunds', 'Enviado de los abismos', 'Inviato degli abissi', 'Abyssalien', 'Abissalino'),
      '1664e_z36', ['BE7237', 'D44E01', 'BE7237'], 640, 30.0, 90, 3.0, 'tank', 18, None,
      [A('Ronces abyssales', 'Abyssal Brambles', 'Abgrunddornen', 'Zarzas abisales', 'Rovi abissali', 'Abyssale braamstruiken', 'Silvas abissais'),
       A('Poison abyssal', 'Abyssal Poison', 'Abgrundgift', 'Veneno abisal', 'Veleno abissale', 'Abyssaal gif', 'Veneno abissal'),
       A('Miroir démoniaque', 'Demonic Mirror', 'Dämonischer Spiegel', 'Espejo demoníaco', 'Specchio demoniaco', 'Demonische spiegel', 'Espelho demoníaco')],
      T('Un démon massif venu des abysses. Lent, mais il encaisse.', 'A massive demon from the abyss. Slow, but it takes a beating.', 'Ein massiger Dämon aus dem Abgrund. Langsam, aber zäh.',
        'Un demonio enorme venido de los abismos. Lento, pero aguanta.', 'Un demone massiccio venuto dagli abissi. Lento, ma resistente.', 'Een massieve demoon uit de afgrond. Traag, maar taai.', 'Um demónio maciço vindo dos abismos. Lento, mas resistente.'), 1.15)
demon('sorcier_demon', 1220, T('Sorcier Démon', 'Demon Sorcerer', 'Dämonischer Zauberer', 'Demonio hechicero', 'Stregone demone', 'Demoon Bezweerder', 'Demônio Feiticeiro'),
      '1664s_z36', ['82921C', '808F1B', '82921C'], 420, 26.0, 90, 2.4, 'ranged', 16, dict(kind='lob', fx=2004, dmg=20, speed=150, cd=3.4, range=300, aoe=65),
      [A("Malédiction d'imprudence", 'Curse of Carelessness', 'Fluch der Unachtsamkeit', 'Maldición de imprudencia', 'Maledizione dell\'imprudenza', 'Vloek van onvoorzichtigheid', 'Maldição da imprudência'),
       A('Malédiction de douleur', 'Curse of Pain', 'Fluch des Schmerzes', 'Maldición de dolor', 'Maledizione del dolore', 'Vloek van pijn', 'Maldição da dor')],
      T('Il lance des malédictions qui explosent au sol.', 'It throws curses that burst on the ground.', 'Er wirft Flüche, die am Boden explodieren.', 'Lanza maldiciones que estallan en el suelo.',
        'Lancia maledizioni che esplodono al suolo.', 'Hij werpt vloeken die op de grond ontploffen.', 'Lança maldições que explodem no chão.'))
P4.mon('essence_goultard', 2773, 360, 28.0, 110, 2.0, 'chase', 15, None,
       T('Le mal de Goultard, devenu chair. Elle suit sa proie sans relâche.', "Goultard's evil, made flesh. It follows its prey relentlessly.", 'Goultards Böses, zu Fleisch geworden. Sie verfolgt ihre Beute unerbittlich.',
         'El mal de Gúltar hecho carne. Persigue a su presa sin descanso.', 'Il male di Gultard fatto carne. Insegue la preda senza sosta.', 'Het kwaad van Goultard, vlees geworden. Ze volgt haar prooi zonder ophouden.',
         'O mal de Goultard feito carne. Persegue a presa sem descanso.'))
C['monsters']['essence_goultard'].update(sprite='1664x_z36', art='p1664_essence')

P4.boss('grand_envoye', 1219, 14000, 26.0, 95, 30, 1.6, False,
        [dict(k='charge', cd=4.5), dict(k='summon', pool=['petit_demon_rapide', 'diablotin_rouge'], count=3, cd=8), dict(k='puddle', dmg=4.0, count=3, cd=7, color='#9a3a10'),
         dict(k='nova', count=16, dmg=20.0, cd=5, color='#ff6a2a')],
        T('Le plus grand des envoyés des abysses. Il sème le poison sous ses pas.', 'The greatest of the abyssal envoys. It leaves poison where it walks.', 'Der größte der Gesandten des Abgrunds. Er hinterlässt Gift, wo er geht.',
          'El mayor de los enviados de los abismos. Deja veneno a su paso.', 'Il più grande degli inviati degli abissi. Lascia veleno dove passa.', 'De grootste van de abyssaliens. Hij laat gif achter waar hij loopt.', 'O maior dos abissalinos. Deixa veneno por onde passa.'),
        dict(sprite='1664e_z48', colors=['BE7237', 'D44E01', 'BE7237'], art='p1664_BE7237',
             name=T('Grand Envoyé des Abysses', 'Great Abyssal Envoy', 'Großer Gesandter des Abgrunds', 'Gran enviado de los abismos', 'Grande inviato degli abissi', 'Grote Abyssalien', 'Grande Abissalino'),
             attacks=C['monsters']['envoye_abysses']['attacks']))
P4.boss('qutan', 1195, 21000, 30.0, 100, 32, 1.6, False,
        [dict(k='blink', cd=5), dict(k='rain', dmg=18.0, count=8, cd=7, color='#ff4a3a'), dict(k='beam', cd=7, length=480, width=70, dmg=42.0, color='#ff3020'),
         dict(k='summon', pool=['diablotin_rouge', 'diablotin_jaune', 'diablotin_bleu', 'diablotin_vert'], count=4, cd=9), dict(k='ring', dmg=9.0, count=22, cd=6, color='#ff5030')],
        T('Le maître du donjon des démons. Il appelle ses diablotins de toutes les couleurs.', 'The master of the demons\' dungeon. It calls imps of every colour.', 'Der Herr des Dämonenkerkers. Er ruft Teufelchen in allen Farben.',
          'El amo de la mazmorra de los demonios. Llama a diablotines de todos los colores.', 'Il padrone del dungeon dei demoni. Chiama diavoletti di ogni colore.', 'De meester van de demonenkerker. Hij roept imps in alle kleuren.', 'O senhor da masmorra dos demónios. Chama diabinhos de todas as cores.'),
        dict(sprite='1665_z48', art='a1665', name=T("Qu'Tan", "Ku'Tan", "Ku'Tan", "Ku'Tan", "Ku'Tan", "Ku'Tan", "Ku'Tan"),
             attacks=[A("Tir de Qu'Tan", "Ku'Tan's Shot", "Ku'Tans Schuss", "Disparo de Ku'Tan", "Tiro di Ku'Tan", "Ku'Tans schot", "Tiro de Ku'Tan"),
                      A("Malédiction de Qu'Tan", "Ku'Tan's Malediction", "Ku'Tans Fluch", "Maldición de Ku'Tan", "Maledizione di Ku'Tan", "Ku'Tans vervloeking", "Maldição de Ku'Tan"),
                      A("Lacération de Qu'Tan", "Ku'Tan's Laceration", "Ku'Tans Zerfleischung", "Laceración de Ku'Tan", "Lacerazione di Ku'Tan", "Ku'Tans verscheuring", "Laceração de Ku'Tan")]))
P4.boss('goultard', 107, 32000, 36.0, 125, 34, 2.2, True,
        [dict(k='leap', cd=5.5, radius=120, dmg=38.0), dict(k='slash', cd=3, range=180, dmg=34.0), dict(k='summon', mob='essence_goultard', count=4, cd=10),
         dict(k='pull', dmg=0.0, cd=9, color='#ff2a2a'), dict(k='ring', dmg=10.0, count=24, cd=5, color='#c01818'), dict(k='fissure', dmg=16.0, steps=9, cd=6.5, color='#ff3010'),
         dict(k='roar', dmg=12.0, radius=260, cd=9, color='#ff4020')],
        T('Le héros iop, rendu au mal par la mort de Dark Vlad. Le maître de la clairière.', 'The Iop hero, given over to evil by Dark Vlad\'s death. The master of the clearing.',
          'Der Iop-Held, durch Dark Vlads Tod dem Bösen verfallen. Der Herr der Lichtung.', 'El héroe yopuka, entregado al mal por la muerte de Dark Vlad. El amo del claro.',
          'L\'eroe iop, consegnato al male dalla morte di Dark Vlad. Il padrone della radura.', 'De Iop-held, door de dood van Dark Vlad aan het kwaad overgeleverd. De meester van de open plek.',
          'O herói iop, entregue ao mal pela morte de Dark Vlad. O senhor da clareira.'),
        dict(sprite='9272_z60', rz=6.0, art='a9272', gfx=9272, lore=dict(lv=[200, 200], hp=[10000, 10000]),
             name=T('Goultard', 'Goultard', 'Goultard', 'Gúltar', 'Gultard', 'Goultard', 'Goultard')))
GN = T('Clairière maudite de Goultard', "Goultard's Cursed Clearing", 'Goultards verfluchte Lichtung', 'Claro maldito de Gúltar', 'Radura maledetta di Gultard',
       'Vervloekte open plek van Goultard', 'Clareira amaldiçoada de Goultard')
GZ = P4.zone('goultard', 'goultard', GN, '200 - 600', 'fig_kutan', 'fig_tower_final', [
    [('sbire_qutan', 4), ('petit_demon_rapide', 3), ('diablotin_rouge', 2)],
    [('sbire_qutan', 3), ('diablotin_rouge', 3), ('diablotin_jaune', 3), ('petit_demon_rapide', 2)],
    [('diablotin_jaune', 3), ('diablotin_bleu', 3), ('sbire_qutan', 3), ('petit_demon_rapide', 2), ('diablotin_vert', 1)],
    [('diablotin_bleu', 3), ('diablotin_vert', 3), ('sorcier_demon', 2), ('sbire_qutan', 3)],
    [('sorcier_demon', 3), ('envoye_abysses', 2), ('diablotin_vert', 3), ('diablotin_rouge', 3)],
    [('envoye_abysses', 3), ('sorcier_demon', 3), ('essence_goultard', 2), ('diablotin_bleu', 3), ('petit_demon_rapide', 2)],
    [('envoye_abysses', 3), ('essence_goultard', 3), ('sorcier_demon', 3), ('diablotin_jaune', 3), ('sbire_qutan', 2)],
], [[1.25, 'swarm', 'petit_demon_rapide', 30], [3.25, 'ring', 'diablotin_rouge', 18], [5.0, 'swarm', 'diablotin_jaune', 32], [7.5, 'ring', 'envoye_abysses', 12], [9.0, 'swarm', 'petit_demon_rapide', 55]],
    [[3.0, 'grand_envoye'], [5.5, 'qutan'], [8.0, 'goultard']], ('minotoror', 'grobe'), 1.5)
for n in GZ['norm']: n[2], n[3] = round(n[2] * 1.12, 4), round(n[3] * 1.08, 4)   # (clearly over Grobe's)
GZ.update(hidden=True, unlockBy='vlad_hard', tier=14)
C['maps'].append(GZ)
C['tmap']['maps'].append('goultard'); C['tmap']['prize']['goultard'] = 6000
C['cine']['vlad'] = 5.5   # (Dark Vlad's fall in Difficile, then UI.vladScene)
P4.P3.put_ui({
    'goultard_lock': T('Dark Vlad garde un secret… en Difficile.', 'Dark Vlad keeps a secret… in Hard mode.', 'Dark Vlad hütet ein Geheimnis… im schweren Modus.', 'Dark Vlad guarda un secreto… en Difícil.',
                       'Dark Vlad custodisce un segreto… in Difficile.', 'Dark Vlad bewaakt een geheim… in Moeilijk.', 'Dark Vlad guarda um segredo… no Difícil.'),
    'vlad_d1': T('Argh… Vaincu… par un aventurier…', 'Argh… Beaten… by an adventurer…', 'Argh… Besiegt… von einem Abenteurer…', 'Argh… Vencido… por un aventurero…',
                 'Argh… Sconfitto… da un avventuriero…', 'Argh… Verslagen… door een avonturier…', 'Argh… Vencido… por um aventureiro…'),
    'vlad_d2': T('Pauvre fou ! Cette clairière, je la gardais. Tant que je vivais, il restait enchaîné.', 'You fool! I was guarding this clearing. As long as I lived, he stayed in chains.',
                 'Du Narr! Ich habe diese Lichtung bewacht. Solange ich lebte, blieb er in Ketten.', '¡Insensato! Yo guardaba este claro. Mientras yo viviera, él seguía encadenado.',
                 'Folle! Ero io a custodire questa radura. Finché vivevo, lui restava in catene.', 'Dwaas! Ik bewaakte deze open plek. Zolang ik leefde, bleef hij geketend.',
                 'Insensato! Era eu quem guardava esta clareira. Enquanto eu vivesse, ele ficava acorrentado.'),
    'vlad_d3': T('Ma mort brise le sceau… Le vrai maître de ces terres se réveille.', 'My death breaks the seal… The true master of these lands awakens.',
                 'Mein Tod bricht das Siegel… Der wahre Herr dieser Lande erwacht.', 'Mi muerte rompe el sello… El verdadero amo de estas tierras despierta.',
                 'La mia morte spezza il sigillo… Il vero padrone di queste terre si risveglia.', 'Mijn dood breekt het zegel… De ware meester van dit land ontwaakt.',
                 'A minha morte quebra o selo… O verdadeiro senhor destas terras desperta.'),
    'vlad_d4': T('Goultard… Pardonne-moi…', 'Goultard… Forgive me…', 'Goultard… Vergib mir…', 'Gúltar… Perdóname…', 'Gultard… Perdonami…', 'Goultard… Vergeef me…', 'Goultard… Perdoa-me…'),
    'goultard_d1': T('Enfin libre. Vlad n\'était que mon geôlier. Rushu m\'a rendu ma lame.', 'Free at last. Vlad was only my jailer. Rushu gave me back my blade.',
                     'Endlich frei. Vlad war nur mein Kerkermeister. Rushu gab mir meine Klinge zurück.', 'Libre por fin. Vlad solo era mi carcelero. Rushu me devolvió mi espada.',
                     'Finalmente libero. Vlad era solo il mio carceriere. Rushu mi ha ridato la mia lama.', 'Eindelijk vrij. Vlad was maar mijn cipier. Rushu gaf me mijn zwaard terug.',
                     'Finalmente livre. O Vlad era apenas o meu carcereiro. O Rushu devolveu-me a minha lâmina.'),
    'goultard_d2': T('Cette clairière m\'appartient. Le sang y coule déjà : viens y verser le tien.', 'This clearing is mine. Blood already flows here: come and spill yours.',
                     'Diese Lichtung gehört mir. Hier fließt schon Blut: Komm und vergieß deins.', 'Este claro me pertenece. La sangre ya corre aquí: ven a derramar la tuya.',
                     'Questa radura è mia. Il sangue scorre già: vieni a versare il tuo.', 'Deze open plek is van mij. Hier vloeit al bloed: kom het jouwe vergieten.',
                     'Esta clareira pertence-me. O sangue já corre aqui: vem derramar o teu.'),
    'goultard_open': T('Zone secrète : {n}', 'Secret zone: {n}', 'Geheime Zone: {n}', 'Zona secreta: {n}', 'Zona segreta: {n}', 'Geheime zone: {n}', 'Zona secreta: {n}'),
    'next': T('Suite', 'Next', 'Weiter', 'Siguiente', 'Avanti', 'Verder', 'Seguinte'),
})

# XP -15 % everywhere: the ambers of the monsters, the bosses, the Archimonsters (last, so it covers the new zone)
for m in C['monsters'].values(): m['xp'] = round(m['xp'] * 0.85, 4)
for b in C['bosses'].values(): b['xp'] = round(b['xp'] * 0.85, 2)
C['archiCfg']['xp'] = round(C['archiCfg']['xp'] * 0.85, 2)

if __name__ == '__main__':
    json.dump(C, open(f'{G}/data/content.json', 'w'), ensure_ascii=False, separators=(',', ':'))
    GZ_ = next(m for m in C['maps'] if m['id'] == 'goultard'); print('goultard', [n[2:] for n in GZ_['norm']])
    print('0.52 ok', len(C['maps']), 'zones', next(w for w in C['uniqueWeapons'] if w['id'] == 'epee_sang')['desc']['fr'])
