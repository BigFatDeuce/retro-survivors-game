"""v2.0 the new zone: L'île des naufragés (Otomaï's pirates).
Monsters, bosses and waves; names / spells / levels / HP come from the official lang files and the emulator data."""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import sys, json
import langdata as LD, maprender as MR

LG = ['fr', 'en', 'de', 'es', 'it', 'nl', 'pt']


def T(*a): return dict(zip(LG, a))


def dbmon(did):
    r = MR.db().execute('select name, gfxID, grades, pdvs, spells from monsters where id=?', (did,)).fetchone()
    name, gfx, grades, pdvs, spells = r
    lv = [int(g.split('@')[0]) for g in grades.split('|') if '@' in g]
    hp = [int(x) for x in pdvs.split('|') if x.strip().isdigit()]
    sp = []
    for s in (spells.split('|')[0] if spells else '').split(';'):
        if '@' in s:
            n = LD.spell(int(s.split('@')[0]))
            if n['fr'] and n not in sp and not n['fr'].startswith('Invocation'): sp.append(n)
    return dict(gfx=gfx, lore=dict(lv=[min(lv), max(lv)], hp=[min(hp), max(hp)]), attacks=sp[:3])


# id, emulator id, hp, dmg, speed, xp, behaviour, size, attack, flavor
MONS = [
    ('tikokoko', 208, 28, 6, 140, 1, 'erratic', 10, None,
     T('Une pousse de cocotier qui court partout. Personne ne sait où elle va, elle non plus.', 'A coconut sprout running all over the place. Nobody knows where it is going, not even itself.',
       'Ein Kokospalmen-Spross, der überall herumrennt. Niemand weiß, wohin er will, er selbst auch nicht.', 'Un brote de cocotero que corre por todas partes. Nadie sabe adónde va, ni él mismo.',
       'Un germoglio di cocco che corre ovunque. Nessuno sa dove vada, nemmeno lui.', 'Een kokosscheut die overal heen rent. Niemand weet waarheen, hijzelf ook niet.', 'Um broto de coqueiro que corre para todo lado. Ninguém sabe para onde vai, nem ele.')),
    ('nodkoko', 218, 46, 8, 115, 2, 'ranged', 11, dict(kind='lob', fx=2004, dmg=10, speed=150, cd=3.6, range=260, aoe=50),
     T('Il lance des noix de coco. Avec une précision qui force le respect.', 'It throws coconuts. With an accuracy that commands respect.', 'Er wirft Kokosnüsse. Mit einer Treffsicherheit, die Respekt einflößt.', 'Lanza cocos. Con una puntería que impone respeto.',
       'Lancia noci di cocco. Con una mira che incute rispetto.', 'Hij gooit kokosnoten. Met een precisie die respect afdwingt.', 'Atira cocos. Com uma pontaria que impõe respeito.')),
    ('kokoko', 209, 100, 12, 90, 3, 'chase', 15, None,
     T('Le grand frère des Tikokokos. Il fait de l\'ombre, et pas seulement aux touristes.', 'The Tikokokos\' big brother. It casts a long shadow, and not only over tourists.', 'Der große Bruder der Tikokokos. Er wirft lange Schatten, nicht nur auf Touristen.',
       'El hermano mayor de los Tikokokos. Da sombra, y no solo a los turistas.', 'Il fratello maggiore dei Tikokoko. Fa ombra, e non solo ai turisti.', 'De grote broer van de Tikokoko\'s. Hij werpt schaduw, en niet alleen op toeristen.', 'O irmão mais velho dos Tikokokos. Faz sombra, e não só aos turistas.')),
    # the shipwreck island
    ('boomba_saoule', 1229, 40, 8, 100, 1, 'erratic', 12, None,
     T('Il a fêté le naufrage. Un peu trop. Il zigzague, mais il mord toujours.', 'It celebrated the shipwreck. A bit too much. It zigzags, but it still bites.', 'Er hat den Schiffbruch gefeiert. Etwas zu sehr. Er torkelt, aber er beißt noch.',
       'Celebró el naufragio. Un poco demasiado. Hace eses, pero sigue mordiendo.', 'Ha festeggiato il naufragio. Un po\' troppo. Barcolla, ma morde ancora.', 'Hij heeft de schipbreuk gevierd. Iets te veel. Hij zigzagt, maar bijt nog steeds.', 'Comemorou o naufrágio. Um pouco demais. Ziguezagueia, mas ainda morde.')),
    ('nakunbra_esseule', 1231, 50, 9, 105, 2, 'chase', 13, None,
     T('Oublié sur l\'île par son équipage. Il ne l\'a pas très bien pris.', 'Left behind on the island by its crew. It did not take it very well.', 'Von seiner Mannschaft auf der Insel vergessen. Er hat es nicht gut aufgenommen.',
       'Olvidado en la isla por su tripulación. No se lo tomó muy bien.', 'Dimenticato sull\'isola dal suo equipaggio. Non l\'ha presa benissimo.', 'Door zijn bemanning op het eiland vergeten. Hij nam het niet zo goed op.', 'Esquecido na ilha pela tripulação. Não aceitou muito bem.')),
    ('canon_dorf_debutant', 1230, 62, 10, 50, 2, 'ranged', 14, dict(kind='lob', fx=2004, dmg=11, speed=150, cd=4.0, range=290, aoe=55),
     T('Un canon qui apprend encore à viser. Restez loin de ses essais.', 'A cannon still learning to aim. Stay clear of its practice shots.', 'Eine Kanone, die noch zielen lernt. Halte dich von ihren Probeschüssen fern.',
       'Un cañón que aún aprende a apuntar. Aléjate de sus prácticas.', 'Un cannone che sta ancora imparando a mirare. Stai lontano dalle sue prove.', 'Een kanon dat nog leert mikken. Blijf uit de buurt van zijn oefenschoten.', 'Um canhão que ainda aprende a mirar. Fique longe dos seus treinos.')),
    ('boomba', 228, 120, 14, 100, 4, 'chase', 14, None,
     T('Un pirate à crocs. Il garde le butin et ne partage jamais.', 'A pirate with fangs. It guards the loot and never shares.', 'Ein Pirat mit Reißzähnen. Er bewacht die Beute und teilt nie.', 'Un pirata con colmillos. Guarda el botín y nunca comparte.',
       'Un pirata con le zanne. Custodisce il bottino e non lo divide mai.', 'Een piraat met slagtanden. Hij bewaakt de buit en deelt nooit.', 'Um pirata de presas. Guarda o saque e nunca o divide.')),
    ('nakunbra', 229, 140, 15, 100, 4, 'charge', 15, None,
     T('Il embroche d\'abord, il pose les questions ensuite. Il ne pose jamais de questions.', 'It skewers first and asks questions later. It never asks questions.', 'Er spießt zuerst auf und fragt später. Er fragt nie.',
       'Primero ensarta, luego pregunta. Nunca pregunta.', 'Prima infilza, poi fa domande. Non fa mai domande.', 'Eerst spietsen, dan vragen stellen. Hij stelt nooit vragen.', 'Primeiro espeta, depois pergunta. Nunca pergunta.')),
    ('canon_dorf', 231, 130, 15, 45, 4, 'ranged', 15, dict(kind='lob', fx=2004, dmg=16, speed=150, cd=3.6, range=310, aoe=62),
     T('Le vrai canon du bord. Ses boulets ont la fâcheuse habitude d\'arriver là où vous êtes.', 'The ship\'s real cannon. Its cannonballs have the nasty habit of landing where you stand.', 'Die echte Bordkanone. Ihre Kugeln landen dummerweise immer dort, wo du stehst.',
       'El verdadero cañón de a bordo. Sus balas tienen la mala costumbre de caer donde estás.', 'Il vero cannone di bordo. Le sue palle hanno il vizio di cadere dove sei tu.', 'Het echte scheepskanon. Zijn kogels landen vervelend genoeg precies waar jij staat.', 'O verdadeiro canhão de bordo. As suas balas têm o mau hábito de cair onde você está.')),
    ('boomba_shika', 1082, 190, 16, 95, 5, 'tank', 16, None,
     T('Le second du capitaine. Plus gros, plus fort, et toujours aussi peu partageur.', 'The captain\'s first mate. Bigger, stronger, and just as unwilling to share.', 'Der erste Maat des Kapitäns. Größer, stärker und genauso wenig teilfreudig.',
       'El segundo del capitán. Más grande, más fuerte y igual de poco generoso.', 'Il secondo del capitano. Più grosso, più forte e altrettanto poco generoso.', 'De eerste stuurman van de kapitein. Groter, sterker en net zo gierig.', 'O imediato do capitão. Maior, mais forte e igualmente avarento.')),
    ('coffre_maudit_flib', 1078, 260, 0, 120, 0, 'flee', 13, None,
     T('Le coffre maudit du Flib s\'est fait la malle. Rattrapez-le : il est plein de kamas.', 'Ze Flib\'s cursed chest has run off. Catch it: it is full of kamas.', 'Die verfluchte Truhe des Flib ist abgehauen. Fang sie: Sie ist voller Kamas.',
       'El cofre maldito del Flib se ha dado a la fuga. Atrápalo: está lleno de kamas.', 'Il forziere maledetto del Flib è scappato. Prendilo: è pieno di kama.', 'De vervloekte kist van de Flib is ervandoor. Vang hem: hij zit vol kama\'s.', 'O baú amaldiçoado do Flib fugiu. Apanhe-o: está cheio de kamas.')),
]

# id, emulator id, hp, dmg, speed, size, scale, final, abilities, flavor
BOSSES = [
    ('boombata', 2408, 4900, 16.0, 95, 28, 1.6, False,
     [dict(k='charge', cd=5), dict(k='summon', pool=['boomba_saoule', 'nakunbra_esseule'], count=4, cd=8), dict(k='spin', radius=115, dmg=14.0, cd=7)],
     T('Le garde de la cale. Personne ne touche au rhum sans son accord.', 'The guard of the hold. Nobody touches the rum without its say-so.', 'Der Wächter des Laderaums. Niemand rührt den Rum ohne sein Einverständnis an.',
       'El guardia de la bodega. Nadie toca el ron sin su permiso.', 'La guardia della stiva. Nessuno tocca il rum senza il suo permesso.', 'De bewaker van het ruim. Niemand komt zonder zijn toestemming aan de rum.', 'O guarda do porão. Ninguém toca no rum sem a sua autorização.')),
    ('flib_capitaine', 1050, 7600, 17.0, 95, 26, 1.7, False,
     [dict(k='nova', count=12, dmg=15.5, cd=4.5, color='#c8a060'), dict(k='blink', cd=6), dict(k='lob', cd=3.5, dmg=17.0, aoe=65, count=2), dict(k='summon', mob='canon_dorf_debutant', count=2, cd=9)],
     T('Le Flib en personne, son coffre maudit jamais très loin. Trinquons ensemble, moussaillon !', 'Ze Flib in person, its cursed chest never far away. Let us drink together, ship\'s boy!', 'Der Flib persönlich, seine verfluchte Truhe nie weit. Lass uns anstoßen, Schiffsjunge!',
       'El Flib en persona, con su cofre maldito siempre cerca. ¡Brindemos juntos, grumete!', 'Il Flib in persona, il suo forziere maledetto mai lontano. Brindiamo insieme, mozzo!', 'De Flib in eigen persoon, zijn vervloekte kist nooit ver weg. Laten we proosten, scheepsmaatje!', 'O Flib em pessoa, com o baú amaldiçoado sempre por perto. Brindemos juntos, grumete!')),
    ('le_chouque', 230, 12300, 25.0, 100, 34, 1.6, True,
     [dict(k='slash', range=170, dmg=31.0, cd=5), dict(k='lob', cd=3.0, dmg=20.0, aoe=70, count=3), dict(k='heal', amount=0.06, cd=12), dict(k='summon', pool=['boomba', 'nakunbra', 'canon_dorf'], count=3, cd=9)],
     T('Le capitaine des pirates. Il éventre, il bombarde, et il se recoud tout seul.', 'The pirates\' captain. It slashes, it bombards, and it stitches itself back up.', 'Der Kapitän der Piraten. Er schlitzt, er bombardiert und flickt sich selbst wieder zusammen.',
       'El capitán de los piratas. Destripa, bombardea y se cose él solito.', 'Il capitano dei pirati. Sventra, bombarda e si ricuce da solo.', 'De kapitein van de piraten. Hij snijdt, bombardeert en naait zichzelf weer dicht.', 'O capitão dos piratas. Estripa, bombardeia e cose-se sozinho.')),
]


def monsters(C):
    out = {}
    for mid, did, hp, dmg, sp, xp, beh, size, atk, flavor in MONS:
        if mid in C['monsters']: continue
        d = dbmon(did)
        out[mid] = dict(id=mid, did=did, gfx=d['gfx'], name=LD.monster(did), hp=hp, dmg=dmg, speed=sp, xp=xp, beh=beh, size=size, atk=atk,
                        attacks=d['attacks'], colors=None, scale=1.0, flavor=flavor, lore=d['lore'], sprite=f"{d['gfx']}_z32", kb=1.0, rz=2.4)
        if mid == 'coffre_maudit_flib': out[mid]['jackpot'] = [40, 80]
        # the variants sharing one sprite are told apart by their size
        out[mid]['scale'] = {'boomba_saoule': 0.88, 'boomba_shika': 1.18, 'nakunbra_esseule': 0.9, 'canon_dorf_debutant': 0.88}.get(mid, 1.0)
    return out


def bosses(C):
    out = {}
    for bid, did, hp, dmg, sp, size, scale, final, ab, flavor in BOSSES:
        d = dbmon(did)
        out[bid] = dict(id=bid, did=did, gfx=d['gfx'], name=LD.monster(did), hp=hp, dmg=dmg, speed=sp, abilities=ab, drops=[], scale=scale, size=size,
                        final=final, xp=200, boss=1, rz=4.0, sprite=f"{d['gfx']}_z40", _norm=1, lore=d['lore'], attacks=d['attacks'], flavor=flavor)
    return out


def target_waves(C, a, b, t):
    """the effective [hp, dmg, xp] per wave of a zone placed between zones a and b (t = 0..1)"""
    def eff(m):
        out = []
        for w, n in zip(m['waves'], m['norm']):
            tot = sum(x[1] for x in w[2])
            hp = sum(C['monsters'][k]['hp'] * c for k, c in w[2]) / tot; dm = sum(C['monsters'][k]['dmg'] * c for k, c in w[2]) / tot
            xp = sum(C['monsters'][k]['xp'] * c for k, c in w[2]) / tot
            out.append((hp * n[2], dm * n[3], xp * n[4]))
        return out
    A = eff(next(m for m in C['maps'] if m['id'] == a)); B = eff(next(m for m in C['maps'] if m['id'] == b))
    return [tuple(x + (y - x) * t for x, y in zip(p, q)) for p, q in zip(A, B)]


def make_map(C, mid, world, name, lvl, music, boss_music, waves, events, bosses_, rare, between, t):
    M = {**C['monsters']}
    tgt = target_waves(C, between[0], between[1], t)
    tmpl = next(m for m in C['maps'] if m['id'] == between[0])
    W = []; N = []
    for (w, tw), base in zip(zip(waves, tgt), tmpl['waves']):
        tot = sum(c for _, c in w)
        hp = sum(M[k]['hp'] * c for k, c in w) / tot; dm = sum(M[k]['dmg'] * c for k, c in w) / tot; xp = sum(max(0.5, M[k]['xp']) * c for k, c in w) / tot
        W.append([base[0], base[1], [list(x) for x in w], base[3], base[4]])
        N.append([base[0], base[1], round(tw[0] / hp, 4), round(tw[1] / dm, 4), round(tw[2] / xp, 4)])
    return dict(id=mid, world=world, music=music, boss_music=boss_music, fill=None, lvl=lvl, waves=W, events=events,
                bosses=bosses_, rare=rare, norm=N, name=name)


def apply(C):
    C['monsters'].update(monsters(C))
    C['bosses'].update(bosses(C))
    nauf = make_map(C, 'naufrages', 'naufrages', LD.subarea(451), '5 - 70', 'loc_otomai', 'fig_otomai', [
        [('boomba_saoule', 5), ('tikokoko', 3), ('crabe', 2)],
        [('boomba_saoule', 4), ('nakunbra_esseule', 3), ('tikokoko', 2), ('crabe', 2)],
        [('nakunbra_esseule', 3), ('canon_dorf_debutant', 2), ('boomba_saoule', 3), ('nodkoko', 2), ('kokoko', 1)],
        [('boomba', 3), ('nakunbra_esseule', 2), ('canon_dorf_debutant', 2), ('kokoko', 2), ('nodkoko', 2)],
        [('boomba', 3), ('nakunbra', 3), ('canon_dorf', 2), ('kokoko', 2), ('boomba_saoule', 2)],
        [('nakunbra', 3), ('canon_dorf', 2), ('boomba_shika', 2), ('boomba', 3), ('le_flib', 2)],
        [('boomba_shika', 3), ('nakunbra', 3), ('canon_dorf', 3), ('boomba', 3), ('le_flib', 2)],
    ], [[1.25, 'swarm', 'boomba_saoule', 30], [3.25, 'ring', 'nakunbra_esseule', 16], [5.0, 'swarm', 'tikokoko', 30], [7.5, 'ring', 'boomba', 14], [9.0, 'swarm', 'boomba_saoule', 50]],
        [[3.0, 'boombata'], [5.5, 'flib_capitaine'], [8.0, 'le_chouque']], [['coffre_maudit_flib', 0.0015]], ('wabbit', 'pandala'), 0.5)
    ids = [m['id'] for m in C['maps']]
    for z in ('moon', 'naufrages'):   # (Moon was dropped in v2.0)
        if z in ids: C['maps'] = [m for m in C['maps'] if m['id'] != z]
    at = [m['id'] for m in C['maps']].index('pandala')
    C['maps'][at:at] = [nauf]
    return C
