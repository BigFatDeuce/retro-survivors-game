"""0.68: a new secret zone, 5th in the list: the Kwaks' hidden nest ('kwaknest'), unlocked by beating ToT once
(unlockBy 'tot', main.js). A flat map like Grobe's size from the Montagne des Craqueleurs' pieces with four Kwak nests
(tools/assets/build_flat068.py kwaknest), the mountain's bestiary (Bwaks, Kwaks, Craqueboules, Craqueleurs, Chevaucheurs de
Karne, Kwakus) and, as its final boss, the four Kwakeres (flame / ice / wind / earth) together: the life of one final
boss of that rank split between them (finalGroup: the zone is cleared when the four are down, game.js).
Sheets: tools/assets/build_mobs20.py <gfx>:z=3.6 (monsters) / <gfx>:boss:z=4.8; art: tools/assets/build_art21.py 520 +gfx,…
apply(C, T, put_ui) is called by patch_068."""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
import _root
import langdata as LD, newzones20 as NZ

MZ, BZ = 36, 48


def apply(C, T, put_ui):
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

    # ------------------------------------------------------------------ the bestiary
    for mid, did, col, fl in (
            ('bwak_feu', 265, '#ff7a2a', T('Un bébé Kwak de feu. Il crache des braises en piaillant.', 'A baby fire Kwak. It spits embers as it chirps.', 'Ein Feuer-Kwak-Küken. Es spuckt piepsend Glut.', 'Un bebé Kwak de fuego. Escupe brasas piando.', 'Un piccolo Kwak di fuoco. Sputa braci pigolando.', 'Een babyvuurkwak. Hij spuwt sintels terwijl hij piept.', 'Um bebé Kwak de fogo. Cospe brasas a piar.')),
            ('bwak_terre', 266, '#a07040', T('Un bébé Kwak de terre. Petit, mais têtu comme un rocher.', 'A baby earth Kwak. Small, but stubborn as a rock.', 'Ein Erd-Kwak-Küken. Klein, aber stur wie ein Fels.', 'Un bebé Kwak de tierra. Pequeño, pero terco como una roca.', 'Un piccolo Kwak di terra. Piccolo, ma testardo come una roccia.', 'Een babyaardkwak. Klein, maar koppig als een rots.', 'Um bebé Kwak de terra. Pequeno, mas teimoso como uma rocha.')),
            ('bwak_air', 267, '#9ad87a', T('Un bébé Kwak d\'air. Impossible à attraper.', 'A baby air Kwak. Impossible to catch.', 'Ein Luft-Kwak-Küken. Unmöglich zu fangen.', 'Un bebé Kwak de aire. Imposible de atrapar.', 'Un piccolo Kwak d\'aria. Impossibile da prendere.', 'Een babyluchtkwak. Onmogelijk te vangen.', 'Um bebé Kwak de ar. Impossível de apanhar.')),
            ('bwak_eau', 268, '#5ab0ff', T('Un bébé Kwak d\'eau. Il éclabousse tout ce qui bouge.', 'A baby water Kwak. It splashes everything that moves.', 'Ein Wasser-Kwak-Küken. Es bespritzt alles, was sich bewegt.', 'Un bebé Kwak de agua. Salpica todo lo que se mueve.', 'Un piccolo Kwak d\'acqua. Schizza tutto ciò che si muove.', 'Een babywaterkwak. Hij spat alles nat wat beweegt.', 'Um bebé Kwak de água. Salpica tudo o que mexe.'))):
        mon(mid, did, 70, 8.5, 120, 0.55, 'erratic' if mid == 'bwak_air' else 'chase', 12, None, fl)
    mon('kwak_flamme', 83, 150, 12.5, 105, 1.0, 'ranged', 15, dict(kind='proj', fx=None, dmg=10, speed=170, cd=3.0, range=280, color='#ff7a2a'),
        T('Un Kwak de flamme. Il lance des boules de feu du haut des rochers.', 'A Flame Kwak. It throws fireballs from the top of the rocks.', 'Ein Flammen-Kwak. Er wirft Feuerbälle von den Felsen.', 'Un Kwak de llama. Lanza bolas de fuego desde lo alto de las rocas.', 'Un Kwak di fiamma. Lancia palle di fuoco dall\'alto delle rocce.', 'Een vlammenkwak. Hij gooit vuurballen vanaf de rotsen.', 'Um Kwak de chama. Lança bolas de fogo do alto das rochas.'))
    mon('kwak_glace', 84, 160, 12.0, 95, 1.0, 'ranged', 15, dict(kind='proj', fx=None, dmg=9, speed=150, cd=3.2, range=280, color='#9ad8ff'),
        T('Un Kwak de glace. Ses projectiles gèlent l\'air autour.', 'An Ice Kwak. Its projectiles freeze the air around.', 'Ein Eis-Kwak. Seine Geschosse lassen die Luft gefrieren.', 'Un Kwak de hielo. Sus proyectiles congelan el aire.', 'Un Kwak di ghiaccio. I suoi proiettili gelano l\'aria.', 'Een ijskwak. Zijn projectielen bevriezen de lucht.', 'Um Kwak de gelo. Os projéteis congelam o ar.'))
    mon('kwak_vent', 81, 130, 11.5, 135, 1.0, 'chase', 15, None,
        T('Un Kwak du vent. Il fond sur sa proie plus vite qu\'une rafale.', 'A Wind Kwak. It swoops on its prey faster than a gust.', 'Ein Wind-Kwak. Er stürzt sich schneller als eine Böe auf die Beute.', 'Un Kwak del viento. Cae sobre su presa más rápido que una ráfaga.', 'Un Kwak del vento. Piomba sulla preda più veloce di una raffica.', 'Een windkwak. Hij duikt sneller dan een windvlaag op zijn prooi.', 'Um Kwak do vento. Cai sobre a presa mais rápido que uma rajada.'))
    mon('kwak_terre', 235, 210, 13.5, 85, 1.1, 'tank', 16, None,
        T('Un Kwak de terre. Lourd, solide, et pas du tout pressé.', 'An Earth Kwak. Heavy, sturdy and in no hurry at all.', 'Ein Erd-Kwak. Schwer, robust und überhaupt nicht in Eile.', 'Un Kwak de tierra. Pesado, sólido y nada apurado.', 'Un Kwak di terra. Pesante, solido e per niente di fretta.', 'Een aardkwak. Zwaar, stevig en totaal niet gehaast.', 'Um Kwak de terra. Pesado, sólido e nada apressado.'))
    mon('craqueboule', 483, 140, 12.0, 110, 0.9, 'charge', 14, None,
        T('Un petit rocher qui roule tout droit sur vous. Les Craqueleurs l\'adorent.', 'A little rock that rolls straight at you. The Cracklers love it.', 'Ein kleiner Felsen, der direkt auf dich zurollt. Die Krachler lieben ihn.', 'Una roca pequeña que rueda directo hacia ti. Los Crujidores la adoran.', 'Una piccola roccia che rotola dritta verso di te. I Croccaroc la adorano.', 'Een rotsje dat recht op je af rolt. De Kraklers zijn er dol op.', 'Uma pequena rocha que rola direito a ti. Os Cracklers adoram-na.'))
    mon('shin_larve', 457, 200, 13.0, 100, 1.1, 'chase', 15, None,
        T('Une Shin Larve, la plus coriace des larves. Elle rampe vite et mord fort.', 'A Shin Larva, the toughest of larvae. It crawls fast and bites hard.', 'Eine Shin-Larve, die zäheste aller Larven. Sie kriecht schnell und beißt fest.',
          'Una Shin Larva, la más dura de las larvas. Repta rápido y muerde fuerte.', 'Una Shin Larva, la più tosta delle larve. Striscia veloce e morde forte.', 'Een Shin Larve, de taaiste larve. Ze kruipt snel en bijt hard.', 'Uma Shin Larva, a mais rija das larvas. Rasteja depressa e morde com força.'))
    # ------------------------------------------------------------------ the bosses
    boss('mega_craqueleur', 295, 5000, 13.0, 75, 30, 1.5, False,
         [dict(k='slam', radius=130, dmg=22.0, cd=5.5), dict(k='summon', pool=['craqueboule', 'craqueleur_plaines'], count=3, cd=9), dict(k='fissure', dmg=12.0, steps=8, cd=6.5, color='#8a8a9a')],
         T('Un Craqueleur énorme, gardien du chemin des nids.', 'A huge Crackler, guardian of the path to the nests.', 'Ein riesiger Krachler, Wächter des Weges zu den Nestern.', 'Un Crujidor enorme, guardián del camino a los nidos.', 'Un Croccaroc enorme, guardiano del sentiero dei nidi.', 'Een enorme Krakler, bewaker van het pad naar de nesten.', 'Um Crackler enorme, guardião do caminho dos ninhos.'),
         dict(sprite='1152_z36', rz=3.6))   # (a huge sprite: zoom 3.6, as the Craqueleur Légendaire)
    boss('shin_larve_boss', 457, 8000, 15.0, 110, 28, 1.6, False,
         [dict(k='charge', cd=4), dict(k='summon', pool=['larve_bleue', 'larve_verte', 'larve_orange', 'moskito'], count=4, cd=8), dict(k='puddle', dmg=3.0, count=3, cd=8, color='#7ac040')],
         T('La reine des larves de la montagne. Elle appelle ses petites quand ça tourne mal.', "The queen of the mountain's larvae. She calls her little ones when things go wrong.",
           'Die Königin der Berglarven. Sie ruft ihre Kleinen, wenn es schiefgeht.', 'La reina de las larvas de la montaña. Llama a sus pequeñas cuando la cosa se tuerce.',
           'La regina delle larve della montagna. Chiama le sue piccole quando le cose si mettono male.', 'De koningin van de berglarven. Ze roept haar kleintjes als het misgaat.', 'A rainha das larvas da montanha. Chama as pequenas quando a coisa corre mal.'),
         dict(sprite=f'1231_z{BZ}'))
    K4 = 3250   # (13 000 in all: between the Dragon Cochon (11 000) and the Chouque (16 000), the zones around it)
    G = dict(finalGroup='kwakeres')
    boss('kwakere_flamme', 269, K4, 15.5, 100, 30, 1.45, True,
         [dict(k='breath', cd=6.5, dmg=12.0, range=210, color='#ff7a1a'), dict(k='rain', dmg=7.0, count=5, cd=8, color='#ff7a2a'), dict(k='summon', pool=['kwak_flamme', 'bwak_feu'], count=2, cd=10)],
         T('La Kwakere de Flamme. Elle couve ses œufs dans les braises.', 'The Flame Kwakere. She broods her eggs in the embers.', 'Die Flammen-Kwakere. Sie brütet ihre Eier in der Glut aus.', 'La Kwakere de Llama. Incuba sus huevos en las brasas.', 'La Kwakere di Fiamma. Cova le uova tra le braci.', 'De Vlammenkwakere. Ze broedt haar eieren uit in de sintels.', 'A Kwakere de Chama. Choca os ovos nas brasas.'), dict(G))
    boss('kwakere_glace', 271, K4, 14.5, 90, 30, 1.45, True,
         [dict(k='ring', dmg=6.5, count=16, cd=6, color='#9ad8ff'), dict(k='roar', dmg=5.0, radius=200, cd=8, color='#bfe8ff', slow=0.45), dict(k='summon', pool=['kwak_glace', 'bwak_eau'], count=2, cd=10)],
         T('La Kwakere de Glace. Son regard suffit à geler un Bouftou.', 'The Ice Kwakere. Her gaze is enough to freeze a Gobball.', 'Die Eis-Kwakere. Ihr Blick genügt, um einen Fresssack einzufrieren.', 'La Kwakere de Hielo. Su mirada basta para congelar a un Jalato.', 'La Kwakere di Ghiaccio. Il suo sguardo basta a congelare un Mangiabù.', 'De IJskwakere. Haar blik is genoeg om een Schaap te bevriezen.', 'A Kwakere de Gelo. O olhar dela chega para congelar um Papatudo.'), dict(G))
    boss('kwakere_vent', 272, K4, 14.0, 130, 30, 1.45, True,
         [dict(k='blink', cd=4.5), dict(k='charge', cd=4.5), dict(k='pull', range=420, dur=1.3, str=110, cd=10, color='#c8f0a0'), dict(k='summon', pool=['kwak_vent', 'bwak_air'], count=2, cd=10)],
         T('La Kwakere de Vent. Là, puis là, puis dans votre dos.', 'The Wind Kwakere. Here, then there, then behind you.', 'Die Wind-Kwakere. Hier, dann da, dann hinter dir.', 'La Kwakere de Viento. Aquí, luego allí, luego a tu espalda.', 'La Kwakere di Vento. Qui, poi lì, poi alle tue spalle.', 'De Windkwakere. Hier, dan daar, dan achter je.', 'A Kwakere de Vento. Aqui, depois ali, depois nas tuas costas.'), dict(G))
    boss('kwakere_terre', 270, K4, 16.5, 80, 30, 1.45, True,
         [dict(k='slam', radius=135, dmg=21.0, cd=5.5), dict(k='fissure', dmg=11.0, steps=8, cd=6.5, color='#a07040'), dict(k='summon', pool=['kwak_terre', 'bwak_terre'], count=2, cd=10)],
         T('La Kwakere de Terre. Elle fait trembler la montagne quand elle se pose.', 'The Earth Kwakere. The mountain shakes when she lands.', 'Die Erd-Kwakere. Der Berg bebt, wenn sie landet.', 'La Kwakere de Tierra. La montaña tiembla cuando se posa.', 'La Kwakere di Terra. La montagna trema quando atterra.', 'De Aardkwakere. De berg trilt als ze landt.', 'A Kwakere de Terra. A montanha treme quando ela pousa.'), dict(G))
    # ------------------------------------------------------------------ the zone (5th, secret)
    name = T('Nid caché des Kwaks', 'Hidden Kwak Nest', 'Verstecktes Kwak-Nest', 'Nido oculto de los Kwaks', 'Nido nascosto dei Kwak', 'Verborgen Kwaknest', 'Ninho escondido dos Kwaks')
    cania = next(m for m in C['maps'] if m['id'] == 'cania')
    Z = NZ.make_map(C, 'kwaknest', 'kwaknest', name, '15 - 80', cania['music'], cania['boss_music'], [
        [('bwak_feu', 3), ('bwak_eau', 3), ('bwak_air', 2), ('larve_bleue', 2), ('moskito', 2)],
        [('bwak_feu', 2), ('bwak_terre', 2), ('craqueboule', 3), ('kwak_vent', 2), ('larve_verte', 2)],
        [('craqueboule', 3), ('kwak_vent', 3), ('kwak_flamme', 2), ('chevaucheur_karne', 2)],
        [('kwak_flamme', 3), ('kwak_glace', 3), ('craqueleur_plaines', 2), ('chevaucheur_karne', 2)],
        [('kwak_glace', 3), ('kwak_terre', 3), ('craqueleur_plaines', 2), ('shin_larve', 2), ('larve_orange', 2)],
        [('kwak_terre', 3), ('shin_larve', 3), ('craqueleur_plaines', 3), ('kwak_flamme', 3), ('moskito', 2)],
        [('shin_larve', 3), ('kwak_terre', 3), ('craqueleur_plaines', 3), ('kwak_glace', 3), ('chevaucheur_karne', 2)],
    ], [[1.25, 'swarm', 'bwak_feu', 30], [3.25, 'ring', 'craqueboule', 16], [5.0, 'swarm', 'kwak_vent', 30], [7.5, 'ring', 'kwak_terre', 12], [9.0, 'swarm', 'bwak_air', 50]],
        [[3.0, 'mega_craqueleur'], [5.5, 'shin_larve_boss'], [8.0, 'kwakere_flamme'], [8.0, 'kwakere_glace'], [8.0, 'kwakere_vent'], [8.0, 'kwakere_terre']], [], ('porco', 'naufrages'), 0.5)
    Z.update(hidden=True, unlockBy='tot', lockKey='kwak_lock', tier=2.5)
    at = [m['id'] for m in C['maps']].index('porco') + 1; C['maps'][at:at] = [Z]
    C['tmap']['maps'] = [m['id'] for m in C['maps']]; C['tmap'].setdefault('prize', {})['kwaknest'] = 2600
    put_ui({
        'kwak_lock': T('Battez ToT une fois pour trouver ce nid.', 'Beat ToT once to find this nest.', 'Besiege ToT einmal, um dieses Nest zu finden.', 'Vence a ToT una vez para encontrar este nido.',
                       'Batti ToT una volta per trovare questo nido.', 'Versla ToT één keer om dit nest te vinden.', 'Vence o ToT uma vez para encontrar este ninho.'),
        'kwak_found': T('Un Kwak vous a suivi depuis le portail de ToT… Le Nid caché des Kwaks est débloqué !', 'A Kwak followed you from ToT\'s portal… The Hidden Kwak Nest is unlocked!',
                        'Ein Kwak ist dir von ToTs Portal gefolgt… Das versteckte Kwak-Nest ist freigeschaltet!', 'Un Kwak te siguió desde el portal de ToT… ¡El Nido oculto de los Kwaks está desbloqueado!',
                        'Un Kwak ti ha seguito dal portale di ToT… Il Nido nascosto dei Kwak è sbloccato!', 'Een Kwak volgde je vanaf ToTs portaal… Het Verborgen Kwaknest is ontgrendeld!',
                        'Um Kwak seguiu-te desde o portal do ToT… O Ninho escondido dos Kwaks está desbloqueado!'),
    })
    return Z
