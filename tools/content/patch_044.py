"""Beta 0.50 content, applied on top of patch_043: three new zones — the Champs de Bonta (2nd zone),
the Montagne des Koalaks (after Cania, the Koulosse is its final boss now; Cania gets the Craqueleur Légendaire) and
L'île de Grobe (the highest zone, before the secret ones). Worlds: build_worlds20.py NEW; sheets: build_mobs20.py
(monsters at zoom 3.6, bosses 4.8).   usage: python tools/content/patch_044.py"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
import _root
import json, math
import patch_043 as P3
import langdata as LD, newzones20 as NZ
from _root import ROOT

C, T, G, put_ui = P3.C, P3.T, P3.G, P3.put_ui
MZ, BZ = 36, 48   # sheet keys: <gfx>_z36 (monsters, zoom 3.6), <gfx>_z48 (bosses, zoom 4.8)

# the zones' own difficulty tier (kamas, boss XP gems, merchant prices, zone multiplier): what their position gave before
# 0.50, so the new zones in the list change nothing for the old ones
for i, m in enumerate(C['maps']):
    m.setdefault('tier', i)


def mon(mid, did, hp, dmg, sp, xp, beh, size, atk, flavor, scale=1.0, extra=None):
    d = NZ.dbmon(did)
    o = dict(id=mid, did=did, gfx=d['gfx'], name=LD.monster(did), hp=hp, dmg=dmg, speed=sp, xp=xp, beh=beh, size=size, atk=atk,
             attacks=d['attacks'], colors=None, scale=scale, flavor=flavor, lore=d['lore'], sprite=f"{d['gfx']}_z{MZ}", kb=1.0, rz=MZ / 10)
    if extra: o.update(extra)
    C['monsters'][mid] = o


def boss(bid, did, hp, dmg, sp, size, scale, final, ab, flavor, extra=None):
    d = NZ.dbmon(did)
    o = dict(id=bid, did=did, gfx=d['gfx'], name=LD.monster(did), hp=hp, dmg=dmg, speed=sp, abilities=ab, drops=[], scale=scale, size=size,
             final=final, xp=25.0, boss=1, rz=BZ / 10, sprite=f"{d['gfx']}_z{BZ}", _norm=1, lore=d['lore'], attacks=d['attacks'], flavor=flavor)
    if extra: o.update(extra)
    C['bosses'][bid] = o


# ------------------------------------------------------------------ Champs de Bonta (plants, Bonta's militia)
mon('champa_vert', 652, 60, 6.0, 85, 0.6, 'chase', 13, None,
    T('Un champignon vert qui fonce tête baissée.', 'A green mushroom that charges head down.', 'Ein grüner Pilz, der mit gesenktem Kopf losstürmt.', 'Una seta verde que embiste con la cabeza gacha.',
      'Un fungo verde che carica a testa bassa.', 'Een groene paddenstoel die met gebogen hoofd aanvalt.', 'Um cogumelo verde que investe de cabeça baixa.'))
mon('abrakne', 650, 90, 8.0, 115, 0.8, 'chase', 13, None,
    T('Une araignée des bois, rapide et collante.', 'A wood spider, fast and sticky.', 'Eine Waldspinne, schnell und klebrig.', 'Una araña del bosque, rápida y pegajosa.',
      'Un ragno dei boschi, veloce e appiccicoso.', 'Een bosspin, snel en kleverig.', 'Uma aranha do bosque, rápida e pegajosa.'))
mon('tournesol_affame', 799, 150, 10.0, 50, 1.2, 'ranged', 15, dict(kind='proj', fx=1012, dmg=9, speed=130, cd=3.2, range=280),
    T('Un tournesol qui a faim. Il tire ses graines de loin.', 'A hungry sunflower. It shoots its seeds from afar.', 'Eine hungrige Sonnenblume. Sie schießt ihre Kerne aus der Ferne.', 'Un girasol hambriento. Dispara sus pipas desde lejos.',
      'Un girasole affamato. Spara i suoi semi da lontano.', 'Een hongerige zonnebloem. Hij schiet zijn zaden van ver.', 'Um girassol esfomeado. Atira as sementes de longe.'))
mon('milicien', 296, 160, 12.0, 100, 1.3, 'charge', 15, None,
    T('La milice de Bonta garde les champs. Elle charge sans prévenir.', 'Bonta\'s militia guards the fields. It charges without warning.', 'Bontas Miliz bewacht die Felder. Sie stürmt ohne Vorwarnung los.',
      'La milicia de Bonta vigila los campos. Embiste sin avisar.', 'La milizia di Bonta sorveglia i campi. Carica senza preavviso.', 'De militie van Bonta bewaakt de velden. Ze stormt zonder waarschuwing.', 'A milícia de Bonta guarda os campos. Investe sem aviso.'))
boss('milicien_puissant', 1128, 4000, 11.5, 100, 26, 1.5, False,
     [dict(k='charge', cd=4.5), dict(k='summon', pool=['milicien', 'champa_vert'], count=3, cd=8), dict(k='roar', dmg=4.0, radius=200, cd=8, color='#7ab0ff')],
     T('Le chef de la milice de Bonta. Il appelle ses hommes en renfort.', 'The head of Bonta\'s militia. He calls his men for backup.', 'Der Anführer von Bontas Miliz. Er ruft seine Männer zu Hilfe.',
       'El jefe de la milicia de Bonta. Llama a sus hombres como refuerzo.', 'Il capo della milizia di Bonta. Chiama i suoi uomini in aiuto.', 'De leider van Bonta\'s militie. Hij roept zijn mannen te hulp.', 'O chefe da milícia de Bonta. Chama os seus homens como reforço.'),
     dict(sprite=f'1192_z{BZ}'))
boss('champmane', 1156, 7000, 12.5, 70, 32, 1.5, False,
     [dict(k='summon', pool=['champ_champ', 'champa_vert'], count=4, cd=8), dict(k='nova', count=12, dmg=10.0, cd=4.5, color='#c8a0e0'), dict(k='puddle', dmg=2.5, count=3, cd=8, color='#a080c0'), dict(k='heal', amount=0.05, cd=12)],
     T('Un champignon géant qui sème ses spores partout.', 'A giant mushroom that spreads its spores everywhere.', 'Ein Riesenpilz, der seine Sporen überall verstreut.', 'Una seta gigante que siembra esporas por todas partes.',
       'Un fungo gigante che sparge spore ovunque.', 'Een reuzenpaddenstoel die overal sporen verspreidt.', 'Um cogumelo gigante que espalha esporos por todo o lado.'))
boss('champ_a_gnons', 1158, 9000, 17.0, 85, 34, 1.6, True,
     [dict(k='slam', radius=140, dmg=25.0, cd=5.5), dict(k='summon', pool=['champ_champ', 'champa_vert', 'maitre_bolet'], count=3, cd=9), dict(k='fissure', dmg=13.0, steps=8, cd=6.5, color='#8a6a4a'),
      dict(k='rain', dmg=10.0, count=6, cd=8, color='#c0a080'), dict(k='heal', amount=0.05, cd=14)],
     T('Le roi des champignons des champs. Il cogne fort et ne se laisse pas cueillir.', 'The king of the field mushrooms. It hits hard and will not be picked.', 'Der König der Feldpilze. Er schlägt hart zu und lässt sich nicht pflücken.',
       'El rey de las setas del campo. Golpea fuerte y no se deja recoger.', 'Il re dei funghi dei campi. Colpisce forte e non si lascia raccogliere.', 'De koning van de veldpaddenstoelen. Hij slaat hard en laat zich niet plukken.', 'O rei dos cogumelos do campo. Bate com força e não se deixa colher.'))

# ------------------------------------------------------------------ Montagne des Koalaks
mon('koalak_immature', 748, 120, 11.0, 100, 0.8, 'chase', 14, None,
    T('Un jeune Koalak, encore maladroit mais déjà teigneux.', 'A young Koalak, still clumsy but already nasty.', 'Ein junger Koalak, noch ungeschickt, aber schon bissig.', 'Un Koalak joven, aún torpe pero ya rabioso.',
      'Un giovane Koalak, ancora goffo ma già cattivo.', 'Een jonge Koalak, nog onhandig maar al vals.', 'Um Koalak jovem, ainda desajeitado mas já rabugento.'))
mon('dok_alako', 747, 110, 10.0, 120, 0.8, 'erratic', 13, None,
    T('Un petit dinosaure qui court dans tous les sens.', 'A small dinosaur running in every direction.', 'Ein kleiner Dinosaurier, der in alle Richtungen rennt.', 'Un pequeño dinosaurio que corre en todas direcciones.',
      'Un piccolo dinosauro che corre in ogni direzione.', 'Een kleine dinosaurus die alle kanten op rent.', 'Um pequeno dinossauro que corre para todo o lado.'))
mon('koalak_coco', 752, 170, 13.0, 100, 1.1, 'chase', 15, None,
    T('Un Koalak adulte. Il protège son canyon.', 'An adult Koalak. It guards its canyon.', 'Ein erwachsener Koalak. Er bewacht seinen Canyon.', 'Un Koalak adulto. Protege su cañón.',
      'Un Koalak adulto. Protegge il suo canyon.', 'Een volwassen Koalak. Hij bewaakt zijn kloof.', 'Um Koalak adulto. Protege o seu desfiladeiro.'))
mon('warko_marron', 746, 220, 15.0, 110, 1.4, 'charge', 16, None,
    T('La monture des Koalaks. Elle fonce sur tout ce qui bouge.', 'The Koalaks\' mount. It charges at anything that moves.', 'Das Reittier der Koalaks. Es stürmt auf alles los, was sich bewegt.', 'La montura de los Koalaks. Embiste todo lo que se mueve.',
      'La cavalcatura dei Koalak. Carica tutto ciò che si muove.', 'Het rijdier van de Koalaks. Het stormt op alles af wat beweegt.', 'A montada dos Koalaks. Investe contra tudo o que mexe.'))
mon('koalak_forestier', 785, 200, 14.0, 85, 1.4, 'ranged', 15, dict(kind='lob', fx=2004, dmg=13, speed=150, cd=3.8, range=280, aoe=55),
    T('Il lance des noix de Kaliptus depuis la forêt.', 'It throws Kaliptus nuts from the forest.', 'Er wirft Kaliptus-Nüsse aus dem Wald.', 'Lanza nueces de Kaliptus desde el bosque.',
      'Lancia noci di Kaliptus dalla foresta.', 'Hij gooit Kaliptusnoten vanuit het bos.', 'Atira nozes de Kaliptus a partir da floresta.'))
mon('piralak', 784, 200, 15.0, 115, 1.4, 'chase', 15, None,
    T('Un Koalak pirate des lacs. Il mord vite.', 'A Koalak pirate of the lakes. It bites fast.', 'Ein Koalak-Pirat der Seen. Er beißt schnell.', 'Un Koalak pirata de los lagos. Muerde rápido.',
      'Un Koalak pirata dei laghi. Morde in fretta.', 'Een Koalak-piraat van de meren. Hij bijt snel.', 'Um Koalak pirata dos lagos. Morde depressa.'))
mon('pekeualak', 786, 190, 14.0, 80, 1.4, 'ranged', 15, dict(kind='proj', fx=1012, dmg=11, speed=140, cd=3.4, range=270),
    T('Un Koalak pêcheur. Son hameçon vise juste.', 'A fisherman Koalak. Its hook is accurate.', 'Ein Fischer-Koalak. Sein Haken trifft genau.', 'Un Koalak pescador. Su anzuelo apunta bien.',
      'Un Koalak pescatore. Il suo amo è preciso.', 'Een vissende Koalak. Zijn haak mikt goed.', 'Um Koalak pescador. O seu anzol tem boa pontaria.'))
mon('guerrier_koalak', 749, 320, 16.0, 85, 1.8, 'tank', 17, None,
    T('Un guerrier en armure. Il encaisse beaucoup.', 'An armoured warrior. It takes a lot of hits.', 'Ein gepanzerter Krieger. Er steckt viel ein.', 'Un guerrero con armadura. Aguanta mucho.',
      'Un guerriero corazzato. Incassa molto.', 'Een gepantserde krijger. Hij kan veel hebben.', 'Um guerreiro de armadura. Aguenta muito.'), extra=dict(kb=0.4))
mon('koalak_sanguin', 744, 280, 18.0, 120, 1.8, 'charge', 16, None,
    T('Un Koalak rouge de colère. Il charge sans relâche.', 'A Koalak red with rage. It charges again and again.', 'Ein vor Wut roter Koalak. Er stürmt immer wieder los.', 'Un Koalak rojo de ira. Embiste sin descanso.',
      'Un Koalak rosso di rabbia. Carica senza sosta.', 'Een Koalak rood van woede. Hij stormt keer op keer.', 'Um Koalak vermelho de raiva. Investe sem parar.'))
mon('koalak_farouche', 756, 300, 18.0, 110, 1.9, 'chase', 16, None,
    T('Un Koalak sauvage qui ne recule jamais.', 'A wild Koalak that never backs down.', 'Ein wilder Koalak, der nie zurückweicht.', 'Un Koalak salvaje que nunca retrocede.',
      'Un Koalak selvaggio che non indietreggia mai.', 'Een wilde Koalak die nooit terugdeinst.', 'Um Koalak selvagem que nunca recua.'))
mon('momie_koalak', 760, 380, 17.0, 70, 2.0, 'tank', 17, None,
    T('Un ancien Koalak sorti du Cimetière primitif. Lent mais coriace.', 'An ancient Koalak risen from the Primitive Cemetery. Slow but tough.', 'Ein uralter Koalak aus dem Urzeitfriedhof. Langsam, aber zäh.', 'Un antiguo Koalak salido del Cementerio primitivo. Lento pero duro.',
      'Un antico Koalak uscito dal Cimitero primitivo. Lento ma coriaceo.', 'Een oude Koalak uit de Oerbegraafplaats. Traag maar taai.', 'Um Koalak antigo saído do Cemitério primitivo. Lento mas resistente.'), extra=dict(kb=0.4))
mon('fossoyeur_koalak', 761, 260, 14.0, 90, 1.8, 'healer', 16, None,
    T('Il soigne les autres Koalaks. À abattre en premier.', 'It heals the other Koalaks. Take it down first.', 'Er heilt die anderen Koalaks. Zuerst ausschalten.', 'Cura a los demás Koalaks. Derríbalo primero.',
      'Cura gli altri Koalak. Da abbattere per primo.', 'Hij geneest de andere Koalaks. Schakel hem eerst uit.', 'Cura os outros Koalaks. Derruba-o primeiro.'))
mon('chevaucheur_koalak', 759, 320, 19.0, 140, 2.0, 'charge', 18, None,
    T('Un Koalak sur son Warko. Très rapide en ligne droite.', 'A Koalak on its Warko. Very fast in a straight line.', 'Ein Koalak auf seinem Warko. Sehr schnell geradeaus.', 'Un Koalak sobre su Warko. Muy rápido en línea recta.',
      'Un Koalak sul suo Warko. Velocissimo in linea retta.', 'Een Koalak op zijn Warko. Heel snel in een rechte lijn.', 'Um Koalak no seu Warko. Muito rápido em linha reta.'))
mon('warko_violet', 745, 340, 19.0, 115, 2.1, 'charge', 17, None,
    T('Un Warko adulte, plus lourd et plus brutal.', 'An adult Warko, heavier and more brutal.', 'Ein ausgewachsener Warko, schwerer und brutaler.', 'Un Warko adulto, más pesado y brutal.',
      'Un Warko adulto, più pesante e brutale.', 'Een volwassen Warko, zwaarder en ruwer.', 'Um Warko adulto, mais pesado e brutal.'))
mon('fauchalak', 783, 360, 21.0, 105, 2.2, 'chase', 17, None,
    T('Il fauche tout ce qui passe à portée de sa lame.', 'It mows down anything within reach of its blade.', 'Er mäht alles nieder, was in Reichweite seiner Klinge kommt.', 'Siega todo lo que pasa al alcance de su hoja.',
      'Falcia tutto ciò che è alla portata della sua lama.', 'Hij maait alles neer wat binnen bereik van zijn kling komt.', 'Ceifa tudo o que passa ao alcance da sua lâmina.'))
boss('mama_koalak', 755, 7000, 14.5, 95, 30, 1.5, False,
     [dict(k='charge', cd=5), dict(k='summon', pool=['koalak_immature', 'dok_alako'], count=4, cd=8), dict(k='heal', amount=0.05, cd=12), dict(k='roar', dmg=5.5, radius=210, cd=8.5, color='#d0a060')],
     T('La mère de tous les Koalaks. Elle appelle ses petits et se soigne.', 'The mother of all Koalaks. She calls her young and heals herself.', 'Die Mutter aller Koalaks. Sie ruft ihre Jungen und heilt sich.', 'La madre de todos los Koalaks. Llama a sus crías y se cura.',
       'La madre di tutti i Koalak. Chiama i suoi piccoli e si cura.', 'De moeder van alle Koalaks. Ze roept haar jongen en geneest zichzelf.', 'A mãe de todos os Koalaks. Chama as crias e cura-se.'))
boss('maitre_koalak', 758, 10000, 16.5, 100, 28, 1.6, False,
     [dict(k='slash', range=165, dmg=26.0, cd=5), dict(k='summon', pool=['guerrier_koalak', 'koalak_sanguin'], count=3, cd=9), dict(k='blink', cd=6), dict(k='ring', dmg=6.0, count=18, cd=6, color='#c0a070')],
     T('Le maître d\'armes des Koalaks. Il tranche, disparaît et revient.', 'The Koalaks\' weapon master. It slashes, vanishes and comes back.', 'Der Waffenmeister der Koalaks. Er schlägt zu, verschwindet und kehrt zurück.', 'El maestro de armas de los Koalaks. Corta, desaparece y vuelve.',
       'Il maestro d\'armi dei Koalak. Colpisce, sparisce e ritorna.', 'De wapenmeester van de Koalaks. Hij hakt, verdwijnt en komt terug.', 'O mestre de armas dos Koalaks. Corta, desaparece e volta.'))
K = C['bosses']['koulosse']
craq = dict(K); craq.update(dict(id='craqueleur_legendaire', did=669, gfx=1358, name=LD.monster(669), sprite='1358_z36', rz=3.6,   # (a huge sprite: zoom 3.6 is plenty)
    scale=1.5, speed=65,
    abilities=[dict(k='slam', radius=150, dmg=35.1, cd=5.5), dict(k='summon', pool=['craqueleur_plaines', 'sanglier_plaines'], count=3, cd=9), dict(k='fissure', dmg=19.4, steps=9, cd=6, color='#8a8a9a'),
               dict(k='rain', dmg=12.0, count=7, cd=8, color='#9a9aaa'), dict(k='roar', dmg=9.1, radius=240, cd=9, color='#b0b0c0')],
    flavor=T('Le plus vieux des Craqueleurs. Ses rochers pleuvent sur Cania.', 'The oldest of the Crackrocks. Its rocks rain down on Cania.', 'Der älteste der Krachler. Seine Felsen regnen auf Cania herab.', 'El más viejo de los Crujidores. Sus rocas llueven sobre Cania.',
             'Il più vecchio dei Crepapietre. Le sue rocce piovono su Cania.', 'De oudste van de Kraakrotsen. Zijn rotsen regenen op Cania neer.', 'O mais velho dos Craqueleurs. As suas rochas chovem sobre Cania.'),
    lore=NZ.dbmon(669)['lore'], attacks=NZ.dbmon(669)['attacks']))
C['bosses']['craqueleur_legendaire'] = craq
K.update(dict(hp=15000, dmg=24.0, sprite=f'1356_z{BZ}', rz=BZ / 10,
              abilities=[dict(k='slam', radius=150, dmg=36.0, cd=5.5), dict(k='summon', pool=['warko_violet', 'chevaucheur_koalak'], count=3, cd=9), dict(k='charge', cd=5),
                         dict(k='fissure', dmg=20.0, steps=9, cd=6, color='#8a8a9a'), dict(k='roar', dmg=9.5, radius=240, cd=9, color='#b0b0c0')]))
for m in C['maps']:
    if m['id'] == 'cania': m['bosses'] = [[t, 'craqueleur_legendaire' if b == 'koulosse' else b] for t, b in m['bosses']]

# ------------------------------------------------------------------ L'île de Grobe (Pandala's ghosts)
mon('fantome_tanuki', 590, 200, 16.0, 140, 1.2, 'erratic', 13, None,
    T('Un petit fantôme qui file dans tous les sens.', 'A little ghost darting in every direction.', 'Ein kleiner Geist, der in alle Richtungen flitzt.', 'Un pequeño fantasma que va en todas direcciones.',
      'Un piccolo fantasma che sfreccia in ogni direzione.', 'Een klein spookje dat alle kanten op schiet.', 'Um pequeno fantasma que dispara para todo o lado.'))
mon('fantome_pandikaze', 583, 300, 20.0, 100, 1.6, 'charge', 15, None,
    T('Le fantôme d\'un Pandikaze. Il charge à travers tout.', 'The ghost of a Pandikaze. It charges through everything.', 'Der Geist eines Pandikaze. Er stürmt durch alles hindurch.', 'El fantasma de un Pandikaze. Embiste a través de todo.',
      'Il fantasma di un Pandikaze. Carica attraverso tutto.', 'De geest van een Pandikaze. Hij stormt overal doorheen.', 'O fantasma de um Pandikaze. Investe através de tudo.'))
mon('fantome_leopardo', 586, 320, 21.0, 125, 1.7, 'chase', 16, None,
    T('Un félin spectral, rapide et silencieux.', 'A spectral feline, fast and silent.', 'Eine geisterhafte Raubkatze, schnell und lautlos.', 'Un felino espectral, rápido y silencioso.',
      'Un felino spettrale, veloce e silenzioso.', 'Een spookachtige katachtige, snel en stil.', 'Um felino espectral, rápido e silencioso.'))
mon('fantome_pandule', 589, 300, 20.0, 95, 1.7, 'invisible', 15, None,
    T('Il disparaît par moments. On ne le voit qu\'à l\'impact.', 'It vanishes now and then. You only see it on impact.', 'Er verschwindet zeitweise. Man sieht ihn erst beim Aufprall.', 'Desaparece a ratos. Solo se le ve al impactar.',
      'Ogni tanto scompare. Lo vedi solo all\'impatto.', 'Hij verdwijnt af en toe. Je ziet hem pas bij de klap.', 'Desaparece de vez em quando. Só se vê no impacto.'))
mon('fantome_soryo', 585, 340, 22.0, 90, 1.9, 'ranged', 16, dict(kind='proj', fx=1012, dmg=16, speed=150, cd=3.0, range=300),
    T('Un renard fantôme qui lance des feux follets.', 'A ghost fox that throws will-o\'-the-wisps.', 'Ein Geisterfuchs, der Irrlichter wirft.', 'Un zorro fantasma que lanza fuegos fatuos.',
      'Una volpe fantasma che lancia fuochi fatui.', 'Een spookvos die dwaallichtjes werpt.', 'Uma raposa fantasma que lança fogos-fátuos.'))
mon('fantome_maho', 584, 380, 24.0, 90, 2.1, 'ranged', 16, dict(kind='lob', fx=2004, dmg=18, speed=150, cd=3.4, range=300, aoe=60),
    T('Un renard fantôme plus puissant. Ses sorts explosent au sol.', 'A stronger ghost fox. Its spells explode on the ground.', 'Ein stärkerer Geisterfuchs. Seine Zauber explodieren am Boden.', 'Un zorro fantasma más poderoso. Sus hechizos explotan en el suelo.',
      'Una volpe fantasma più potente. I suoi incantesimi esplodono al suolo.', 'Een sterkere spookvos. Zijn spreuken ontploffen op de grond.', 'Uma raposa fantasma mais poderosa. Os seus feitiços explodem no chão.'), scale=1.12)
mon('fantome_yokai', 587, 520, 26.0, 95, 2.6, 'tank', 18, None,
    T('Le plus fort des renards fantômes. Il encaisse et frappe fort.', 'The strongest of the ghost foxes. It takes hits and hits back hard.', 'Der stärkste der Geisterfüchse. Er steckt ein und schlägt hart zurück.', 'El más fuerte de los zorros fantasma. Aguanta y golpea fuerte.',
      'La più forte delle volpi fantasma. Incassa e colpisce forte.', 'De sterkste van de spookvossen. Hij kan veel hebben en slaat hard terug.', 'A mais forte das raposas fantasma. Aguenta e bate com força.'), extra=dict(kb=0.4))
boss('fantome_yokai_firefoux', 587, 10000, 22.0, 100, 30, 1.6, False,
     [dict(k='blink', cd=5), dict(k='nova', count=16, dmg=18.0, cd=4.5, color='#9ad0ff'), dict(k='rain', dmg=14.0, count=7, cd=8, color='#7ab0ff'), dict(k='summon', pool=['fantome_tanuki', 'fantome_pandikaze'], count=3, cd=9)],
     T('Le spectre du chef des Firefoux. Il apparaît, tire et disparaît.', 'The spectre of the Firefoux chief. It appears, shoots and vanishes.', 'Das Gespenst des Firefoux-Anführers. Es erscheint, schießt und verschwindet.', 'El espectro del jefe de los Firefoux. Aparece, dispara y desaparece.',
       'Lo spettro del capo dei Firefoux. Appare, spara e scompare.', 'De geest van het hoofd van de Firefoux. Hij verschijnt, schiet en verdwijnt.', 'O espectro do chefe dos Firefoux. Aparece, dispara e desaparece.'),
     dict(sprite=f'1289_z{BZ}'))
boss('fantome_pandore', 597, 15000, 26.0, 100, 32, 1.6, False,
     [dict(k='charge', cd=4.5), dict(k='slam', radius=145, dmg=34.0, cd=6), dict(k='summon', pool=['fantome_pandikaze', 'fantome_pandule'], count=3, cd=9), dict(k='spin', radius=120, dmg=24.0, cd=11), dict(k='roar', dmg=10.0, radius=240, cd=9, color='#a0c8ff')],
     T('Le fantôme de Maître Pandore. Toujours aussi brutal.', 'The ghost of Master Pandore. As brutal as ever.', 'Der Geist von Meister Pandore. Brutal wie eh und je.', 'El fantasma del Maestro Pandore. Tan brutal como siempre.',
       'Il fantasma di Mastro Pandore. Brutale come sempre.', 'De geest van Meester Pandore. Even ruw als altijd.', 'O fantasma do Mestre Pandore. Brutal como sempre.'))
boss('fantome_tanukoui_san', 588, 23000, 31.0, 105, 34, 1.7, True,
     [dict(k='blink', cd=4.5), dict(k='summon', pool=['fantome_soryo', 'fantome_maho', 'fantome_leopardo'], count=3, cd=9), dict(k='nova', count=18, dmg=24.0, cd=4.5, color='#b0d8ff'),
      dict(k='beam', cd=7, length=480, width=70, dmg=40.0, color='#9ad0ff'), dict(k='ring', dmg=8.0, count=22, cd=6, color='#c0e0ff'), dict(k='rain', dmg=16.0, count=8, cd=8.5, color='#7ab0ff')],
     T('Le maître de l\'île de Grobe. Le fantôme le plus puissant du Krosmoz.', 'The master of Grobe Island. The mightiest ghost in the Krosmoz.', 'Der Herr der Insel Grobe. Der mächtigste Geist im Krosmoz.', 'El amo de la isla de Grobe. El fantasma más poderoso del Krosmoz.',
       'Il padrone dell\'isola di Grobe. Il fantasma più potente del Krosmoz.', 'De meester van het eiland Grobe. De machtigste geest van de Krosmoz.', 'O senhor da ilha de Grobe. O fantasma mais poderoso do Krosmoz.'))


# ------------------------------------------------------------------ the three zones
def zone(mid, world, name, lvl, music, boss_music, waves, events, bosses, between, t, fill=None):
    return dict(NZ.make_map(C, mid, world, name, lvl, music, boss_music, waves, events, bosses, [], between, t), fill=fill)


BONTA = zone('bonta', 'bonta', T('Champs de Bonta', 'Bonta Fields', 'Felder von Bonta', 'Campos de Bonta', 'Campi di Bonta', 'Velden van Bonta', 'Campos de Bonta'), '5 - 60', 'loc_bonta', 'fig_cania', [
    [('champ_champ', 4), ('pissenlit', 3), ('rose_demoniaque', 3)],
    [('champ_champ', 3), ('rose_demoniaque', 3), ('champa_vert', 3), ('tournesol', 2)],
    [('champa_vert', 3), ('tournesol', 2), ('abrakne', 3), ('pissenlit', 2), ('sanglier_plaines', 1)],
    [('abrakne', 3), ('milicien', 2), ('tournesol_affame', 2), ('champa_vert', 3), ('maitre_bolet', 1)],
    [('milicien', 3), ('sanglier_plaines', 3), ('abrakne', 3), ('tournesol_affame', 2), ('maitre_bolet', 2)],
    [('milicien', 3), ('maitre_bolet', 2), ('tournesol_affame', 3), ('sanglier_plaines', 3), ('abrakne', 2)],
    [('milicien', 4), ('maitre_bolet', 3), ('tournesol_affame', 3), ('sanglier_plaines', 3), ('champa_vert', 2)],
], [[1.25, 'swarm', 'champ_champ', 30], [3.25, 'ring', 'champa_vert', 18], [5.0, 'swarm', 'abrakne', 30], [7.5, 'ring', 'milicien', 12], [9.0, 'swarm', 'pissenlit', 50]],
    [[3.0, 'milicien_puissant'], [5.5, 'champmane'], [8.0, 'champ_a_gnons']], ('astrub', 'chafer'), 0.5)
KOALAK = zone('koalak', 'koalak', LD.area(28), '40 - 160', 'loc_dragoturkey2', 'fig_sidimote', [
    [('koalak_immature', 5), ('dok_alako', 3)],
    [('koalak_immature', 4), ('dok_alako', 3), ('koalak_coco', 3)],
    [('koalak_coco', 3), ('warko_marron', 3), ('piralak', 2), ('pekeualak', 2), ('koalak_immature', 2)],
    [('warko_marron', 3), ('koalak_forestier', 2), ('piralak', 3), ('pekeualak', 2), ('guerrier_koalak', 2)],
    [('guerrier_koalak', 3), ('koalak_sanguin', 3), ('fossoyeur_koalak', 2), ('momie_koalak', 2), ('koalak_forestier', 2)],
    [('koalak_farouche', 3), ('momie_koalak', 3), ('chevaucheur_koalak', 2), ('warko_violet', 2), ('fossoyeur_koalak', 2), ('koalak_sanguin', 2)],
    [('fauchalak', 3), ('warko_violet', 3), ('chevaucheur_koalak', 3), ('koalak_farouche', 3), ('momie_koalak', 2)],
], [[1.25, 'swarm', 'koalak_immature', 30], [3.25, 'ring', 'dok_alako', 18], [5.0, 'swarm', 'piralak', 30], [7.5, 'ring', 'guerrier_koalak', 12], [9.0, 'swarm', 'koalak_coco', 50]],
    [[3.0, 'mama_koalak'], [5.5, 'maitre_koalak'], [8.0, 'koulosse']], ('cania', 'pandala'), 0.5)
GROBE = zone('grobe', 'grobe', LD.subarea(152), '160 - 450', 'loc_pandawaforest', 'loc_pandawafight', [
    [('fantome_tanuki', 5), ('fantome_pandikaze', 3)],
    [('fantome_tanuki', 3), ('fantome_pandikaze', 4), ('fantome_pandule', 3)],
    [('fantome_pandikaze', 3), ('fantome_leopardo', 3), ('fantome_pandule', 3), ('fantome_soryo', 2)],
    [('fantome_leopardo', 4), ('fantome_soryo', 3), ('fantome_pandule', 2), ('fantome_maho', 2)],
    [('fantome_leopardo', 3), ('fantome_maho', 3), ('fantome_soryo', 3), ('fantome_yokai', 1), ('fantome_pandule', 2)],
    [('fantome_maho', 3), ('fantome_yokai', 2), ('fantome_leopardo', 3), ('fantome_soryo', 3)],
    [('fantome_yokai', 3), ('fantome_maho', 3), ('fantome_leopardo', 4), ('fantome_pandule', 3)],
], [[1.25, 'swarm', 'fantome_tanuki', 30], [3.25, 'ring', 'fantome_pandikaze', 16], [5.0, 'swarm', 'fantome_pandule', 30], [7.5, 'ring', 'fantome_leopardo', 12], [9.0, 'swarm', 'fantome_tanuki', 55]],
    [[3.0, 'fantome_yokai_firefoux'], [5.5, 'fantome_pandore'], [8.0, 'fantome_tanukoui_san']], ('otomai_jungle', 'minotoror'), 1.4, fill='water')
for n in GROBE['norm']: n[2], n[3], n[4] = round(n[2] * 1.15, 4), round(n[3] * 1.1, 4), round(n[4] * 1.08, 4)   # (the highest zone: clearly over the Minotoror's)
TIER = {'bonta': 0.5, 'koalak': 6.5, 'grobe': 12}
for z in (BONTA, KOALAK, GROBE): z['tier'] = TIER[z['id']]
ids = [m['id'] for m in C['maps']]
C['maps'] = [m for m in C['maps'] if m['id'] not in TIER]
def put_after(after, z):
    at = [m['id'] for m in C['maps']].index(after) + 1; C['maps'][at:at] = [z]
put_after('astrub', BONTA); put_after('cania', KOALAK); put_after('minotoror', GROBE)

# Musha l'Oni's treasure maps: the new zones have their treasure too
TM = C['tmap']; TM['maps'] = [m['id'] for m in C['maps']]
TM['prize'].update({'bonta': 1600, 'koalak': 3100, 'grobe': 5000})

if __name__ == '__main__':
    json.dump(C, open(f'{G}/data/content.json', 'w'), ensure_ascii=False, separators=(',', ':'))
    for m in C['maps']: print(f"{m['id']:14s} tier {m['tier']:5} {m['lvl']:10s}", [C['bosses'][b]['hp'] for _, b in m['bosses']], [round(n[2], 3) for n in m['norm']])
    print('0.50 ok', len(C['maps']), 'zones')
