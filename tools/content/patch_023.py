"""Beta 0.23 content (lot 5), applied on top of patch_020 (which applies patch_v20 on work/content_v19.json).
Relics (unique run items dropped by bosses), random events, Archimonsters (the client's own, with their names in the 7
languages), Infinite mode with a local leaderboard.  ->  game/data/content.json
usage: python tools/content/patch_023.py"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
import _root
import json, sqlite3
import patch_020 as P2
import langdata as LD

C, T, G, ROOT = P2.C, P2.T, P2.G, P2.P.ROOT
LG = ['fr', 'en', 'de', 'es', 'it', 'nl', 'pt']
_IT = {lg: json.load(open(f'{ROOT}/work/lang_json/items_{lg}.json'))['I']['u'] for lg in LG}


def flavor(iid):   # the official item description, in every language
    return {lg: (_IT[lg].get(str(iid)) or {}).get('d', '') for lg in LG}


# ---------------------------------------------------------------- relics: one-run unique items (bosses drop them)
# bonus: stat additions (maxhp: multiplier); special: handled in the run (thorns, burn, dashCd)
RELICS = [
    ('gelano', 2469, dict(speed=0.12), dict(dashCd=0.75),
     T('+12 % de vitesse, esquive rechargée 25 % plus vite.', '+12% speed, dash recharges 25% faster.', '+12 % Tempo, Ausweichen lädt 25 % schneller.', '+12 % de velocidad, la esquiva se recarga un 25 % más rápido.', '+12% velocità, schivata ricaricata il 25% più in fretta.', '+12% snelheid, ontwijken laadt 25% sneller op.', '+12% de velocidade, esquiva recarrega 25% mais rápido.')),
    ('amu_craqueleur', 1476, dict(armor=4), {},
     T('+4 résistance fixe. Dur comme un caillou, et aussi bavard.', '+4 armour. Hard as a rock, and just as chatty.', '+4 Resistenz. Hart wie ein Stein, und genauso gesprächig.', '+4 de resistencia. Duro como una piedra, e igual de hablador.', '+4 resistenza. Duro come un sasso, e altrettanto loquace.', '+4 weerstand. Hard als een steen, en net zo spraakzaam.', '+4 de resistência. Duro como uma pedra, e igualmente falador.')),
    ('anneau_sanglier', 6910, dict(might=0.20), {},
     T('+20 % de dégâts.', '+20% damage.', '+20 % Schaden.', '+20 % de daño.', '+20% danni.', '+20% schade.', '+20% de dano.')),
    ('ceinture_prespic', 6929, {}, dict(thorns=0.6),
     T('Renvoie 60 % des coups reçus au corps à corps. Ça pique.', 'Returns 60% of melee hits taken. Prickly.', 'Wirft 60 % der Nahkampftreffer zurück. Pikst.', 'Devuelve el 60 % de los golpes cuerpo a cuerpo. Pica.', 'Rimanda il 60% dei colpi in mischia. Punge.', 'Kaatst 60% van de melee-treffers terug. Prikt.', 'Devolve 60% dos golpes corpo a corpo. Pica.')),
    ('dents_wabbit', 6499, dict(crit=0.12), {},
     T('+12 % de coups critiques.', '+12% critical hits.', '+12 % kritische Treffer.', '+12 % de golpes críticos.', '+12% colpi critici.', '+12% kritieke treffers.', '+12% de golpes críticos.')),
    ('sandales_tofu', 298, dict(speed=0.10, magnet=0.4), {},
     T('+10 % de vitesse et +40 % de rayon de ramassage.', '+10% speed and +40% pickup radius.', '+10 % Tempo und +40 % Aufsammelradius.', '+10 % de velocidad y +40 % de radio de recogida.', '+10% velocità e +40% raggio di raccolta.', '+10% snelheid en +40% oprapbereik.', '+10% de velocidade e +40% de raio de recolha.')),
    ('collier_minotoror', 8268, dict(maxhp=0.30), {},
     T('+30 % de PV max.', '+30% max HP.', '+30 % max. LP.', '+30 % de PdV máx.', '+30% PV max.', '+30% max. LP.', '+30% de PV máx.')),
    ('kwakanneau_flammes', 2418, {}, dict(burn=0.15),
     T('Chaque coup a 15 % de chances d\'enflammer l\'ennemi.', 'Every hit has a 15% chance to set the enemy on fire.', 'Jeder Treffer hat 15 % Chance, den Gegner anzuzünden.', 'Cada golpe tiene un 15 % de probabilidad de quemar al enemigo.', 'Ogni colpo ha il 15% di probabilità di incendiare il nemico.', 'Elke treffer heeft 15% kans de vijand in brand te zetten.', 'Cada golpe tem 15% de hipótese de incendiar o inimigo.')),
    ('talisman_chene_mou', 8469, dict(regen=0.6), {},
     T('+0,6 PV régénérés par seconde.', '+0.6 HP regenerated per second.', '+0,6 LP Regeneration pro Sekunde.', '+0,6 PdV regenerados por segundo.', '+0,6 PV rigenerati al secondo.', '+0,6 LP herstel per seconde.', '+0,6 PV regenerados por segundo.')),
    ('anneau_kitsou', 7341, dict(amount=1), {},
     T('+1 projectile / invocation par sort.', '+1 projectile / summon per spell.', '+1 Projektil / Beschwörung pro Zauber.', '+1 proyectil / invocación por hechizo.', '+1 proiettile / evocazione per incantesimo.', '+1 projectiel / oproeping per spreuk.', '+1 projétil / invocação por feitiço.')),
]
C['relics'] = []
for rid, iid, bonus, special, eff in RELICS:
    info = LD.item_info(iid)
    C['relics'].append(dict(id=rid, item=iid, icon=f"it_{info['t']}_{info['g']}", name=LD.item(iid), bonus=bonus, special=special,
                            desc=eff, flavor=flavor(iid)))
C['relicRate'] = 0.4   # chance per boss (the final boss always drops one), never twice the same in a run

# ---------------------------------------------------------------- random events (2 per run, between 1:30 and 9:00)
C['randEvents'] = dict(n=2, t0=90, t1=540, list=['bworks', 'tofus', 'merchant', 'kamarain', 'eclipse'],
                       merchant=dict(heal=30, upgrade=60, relic=150, perZone=10, stay=40),
                       eclipse=dict(dur=20, speed=1.15), kamarain=dict(dur=12, every=0.2))

# ---------------------------------------------------------------- Archimonsters: the client's own (same look, own name)
_db = sqlite3.connect(f'{ROOT}/work/sl.db')
_gfx = {}
for k, m in C['monsters'].items(): _gfx.setdefault(m['gfx'], []).append(k)
C['archi'] = {}
for did, gfx in _db.execute('select id, gfxID from monsters where isArchmonster=1'):
    for k in _gfx.get(gfx, []):
        try: nm = LD.monster(did)
        except Exception: continue
        C['archi'].setdefault(k, []).append(dict(id=did, name=nm))
C['archiCfg'] = dict(rate=0.0012, hp=8, dmg=1.6, speed=1.1, scale=1.3, kamas=40, xp=25)

# ---------------------------------------------------------------- Infinite mode
C['infinite'] = dict(cycle=480, grow=0.35, top=10)   # every 8 minutes the bosses come back, 35% stronger each cycle

# ---------------------------------------------------------------- global spells: offered to every class (silver icons,
# tools/assets/build_globalicons23.py). They take a spell slot like class spells. 'w' = offer weight (the Jeton half the others).
def gspell(id, t, name, desc, base, lv, icon, w=1.0, **kw):
    C['spells'][id] = dict(id=id, name=name, desc=desc, t=t, anim=None, fx=[], icon=icon, base=base, lv=lv, sid=0, glob=1, **kw)
    return dict(id=id, w=w)


C['globalSpells'] = [
    gspell('kokoko', 'projectile',
           T('Lancé de Kokoko Trauma', 'Kokoko Trauma Toss', 'Kokoko-Trauma-Wurf', 'Lanzamiento de Kokoko Trauma', 'Lancio di Kokoko Trauma', 'Kokoko-Traumaworp', 'Lançamento de Kokoko Trauma'),
           T('Lance une Noix de Kokoko Traumatisée sur le plus gros monstre. Elle explose au contact : elle aussi a eu une enfance difficile.',
             'Throws a Traumatised Kokoko Nut at the biggest monster. It explodes on contact: it had a rough childhood too.',
             'Wirft eine traumatisierte Kokoko-Nuss auf das dickste Monster. Sie explodiert bei Kontakt: Sie hatte auch eine schwere Kindheit.',
             'Lanza una Nuez de Kokoko Traumatizada al monstruo más gordo. Explota al contacto: ella también tuvo una infancia difícil.',
             'Lancia una Noce di Kokoko Traumatizzata sul mostro più grosso. Esplode al contatto: anche lei ha avuto un\'infanzia difficile.',
             'Gooit een Getraumatiseerde Kokoko-noot naar het dikste monster. Hij ontploft bij contact: hij had ook een zware jeugd.',
             'Lança uma Noz de Kokoko Traumatizada no maior monstro. Explode ao contacto: também teve uma infância difícil.'),
           dict(dmg=40, count=1, speed=250, cd=3.2, pierce=1, size=15, life=3.0, target='strongest', homing=3.0, aoe=78, spin=1, drawIcon='it_46_552'),
           [{}, dict(dmg=50), dict(aoe=92), dict(dmg=62, cd=2.9), dict(count=2), dict(dmg=80, aoe=105)], 'g_kokoko', snd='explosion'),
    gspell('faux_spin', 'orbit',
           T('Faux qui Spin', 'Spinning Scythes', 'Wirbelsensen', 'Guadañas Giratorias', 'Falci Rotanti', 'Draaiende Zeisen', 'Foices Giratórias'),
           T('Les faux maudites du Saigneur Guerrier tournent autour de vous en permanence. Il les cherche encore, ne dites rien.',
             'The Warrior Bleeder\'s cursed scythes spin around you non-stop. He is still looking for them, keep it quiet.',
             'Die verfluchten Sensen des Kriegerblutsaugers kreisen ständig um dich. Er sucht sie noch, sag nichts.',
             'Las guadañas malditas del Sangrador Guerrero giran sin parar a tu alrededor. Aún las está buscando, no digas nada.',
             'Le falci maledette del Salassatore Guerriero ti girano attorno senza sosta. Le sta ancora cercando, acqua in bocca.',
             'De vervloekte zeisen van de Krijger-Aderlater draaien constant om je heen. Hij zoekt ze nog, zeg niks.',
             'As foices amaldiçoadas do Sangrador Guerreiro giram à sua volta sem parar. Ele ainda as procura, bico calado.'),
           dict(dmg=14, count=1, radius=95, rotSpeed=2.6, duration=1e9, cd=1.0, knock=20, size=18, perm=1, drawIcon='it_22_3'),
           [{}, dict(count=2), dict(dmg=18), dict(count=3, radius=105), dict(dmg=22, rotSpeed=3.0), dict(count=4, dmg=27)], 'g_faux', snd='son_attaque_faucille'),
    gspell('pioche', 'pioche',
           T('La bonne Pioche', 'The Lucky Pickaxe', 'Die gute Spitzhacke', 'El Buen Pico', 'Il Piccone Fortunato', 'Het Goede Houweel', 'A Boa Picareta'),
           T('Aucun dégât. Toutes les 5 secondes, un coup de pioche déterre des kamas. Rarement, un filon de 1000 kamas : les Enutrofs appellent ça « la retraite ».',
             'No damage. Every 5 seconds, a pickaxe blow digs up kamas. Rarely, a 1000-kama vein: Enutrofs call it "retirement".',
             'Kein Schaden. Alle 5 Sekunden gräbt ein Hackenschlag Kamas aus. Selten eine 1000-Kama-Ader: Enutrofs nennen das „Rente".',
             'Sin daño. Cada 5 segundos, un golpe de pico desentierra kamas. Raramente, una veta de 1000 kamas: los Anutrofs lo llaman «la jubilación».',
             'Nessun danno. Ogni 5 secondi un colpo di piccone dissotterra kama. Raramente un filone da 1000 kama: gli Enutrof la chiamano «la pensione».',
             'Geen schade. Elke 5 seconden graaft een houweelslag kama\'s op. Soms een ader van 1000 kama\'s: Enutrofs noemen dat "pensioen".',
             'Sem dano. A cada 5 segundos, um golpe de picareta desenterra kamas. Raramente, um veio de 1000 kamas: os Enutrofs chamam-lhe «a reforma».'),
           dict(cd=5.0, kamas=1, jackpot=1000, odds=2000, odds5=1000),
           [{}, dict(kamas=2), dict(cd=4.6), dict(kamas=3), dict(cd=4.2), dict(kamas=4, cd=4.0)], 'g_pioche', snd='pic'),
    gspell('marteau_moon', 'projectile',
           T('Marteau de Moon', 'Moon\'s Hammer', 'Moons Hammer', 'Martillo de Moon', 'Martello di Moon', 'Moons Hamer', 'Martelo de Moon'),
           T('Comme Moon, vous lancez son marteau : il part en arc au hasard et revient toujours. Moon, lui, ne l\'a jamais revu.',
             'Like Moon, you throw his hammer: it flies off in a random arc and always comes back. Moon never saw it again.',
             'Wie Moon wirfst du seinen Hammer: Er fliegt in einem zufälligen Bogen und kommt immer zurück. Moon hat ihn nie wiedergesehen.',
             'Como Moon, lanzas su martillo: sale en un arco al azar y siempre vuelve. Moon nunca lo volvió a ver.',
             'Come Moon, lanci il suo martello: parte in un arco a caso e torna sempre. Moon non l\'ha mai più rivisto.',
             'Net als Moon gooi je zijn hamer: hij vliegt in een willekeurige boog en komt altijd terug. Moon heeft hem nooit meer gezien.',
             'Como Moon, lança o martelo dele: parte num arco ao acaso e volta sempre. O Moon nunca mais o viu.'),
           dict(dmg=26, count=1, speed=330, cd=2.4, pierce=99, size=17, life=2.6, target='random', boomerang=1, curve=2.2, backAt=0.75, spin=1, drawIcon='it_g_hammer'),
           [{}, dict(dmg=32), dict(size=20, curve=2.6), dict(count=2), dict(dmg=40, cd=2.1), dict(count=3, dmg=48)], 'g_moon', snd='marteau_2m'),
    gspell('prouts', 'zone',
           T('6 millions de Prouts', '6 Million Farts', '6 Millionen Pupse', '6 millones de Pedos', '6 milioni di Peti', '6 miljoen Scheten', '6 milhões de Puns'),
           T('« Lâcher les gaz » : un nuage vert et odorant blesse les monstres autour de vous. Personne ne veut se battre à côté de vous.',
             '"Break wind": a smelly green cloud hurts the monsters around you. Nobody wants to fight next to you.',
             '„Winde lassen": Eine stinkende grüne Wolke verletzt die Monster um dich herum. Niemand will neben dir kämpfen.',
             '«Soltar gases»: una nube verde y apestosa hiere a los monstruos a tu alrededor. Nadie quiere luchar a tu lado.',
             '«Liberare i gas»: una nube verde e puzzolente ferisce i mostri attorno a te. Nessuno vuole combattere accanto a te.',
             '"Een wind laten": een stinkende groene wolk verwondt de monsters om je heen. Niemand wil naast je vechten.',
             '«Soltar gases»: uma nuvem verde e fedorenta fere os monstros à sua volta. Ninguém quer lutar ao seu lado.'),
           dict(dmg=8, radius=85, duration=3.0, tick=0.35, cd=6.0, count=1, color='#8fcf3a', follow=1, cloud=1, fart=1),
           [{}, dict(dmg=11), dict(radius=100), dict(duration=4.0, dmg=14), dict(cd=5.0), dict(radius=120, dmg=18)], 'g_prouts', snd='pet',
           animAll='emote8', animBy={'1150': 'anim1', '1155': 'anim1'}),
    gspell('jeton_trool', 'wheel',
           T('Jeton de la Foire du Trool', 'Trool Fair Token', 'Trool-Jahrmarkt-Jeton', 'Ficha de la Feria del Trool', 'Gettone della Fiera del Trool', 'Trool-kermisfiche', 'Ficha da Feira do Trool'),
           T('Faites tourner la roue de la Foire du Trool : elle vous donne un sort d\'une autre classe, au hasard. Le Trool garantit qu\'elle n\'est pas truquée. Le Trool ment.',
             'Spin the Trool Fair wheel: it gives you a random spell from another class. The Trool swears it is not rigged. The Trool lies.',
             'Dreh das Rad des Trool-Jahrmarkts: Es gibt dir einen zufälligen Zauber einer anderen Klasse. Der Trool schwört, es ist nicht manipuliert. Der Trool lügt.',
             'Gira la rueda de la Feria del Trool: te da un hechizo al azar de otra clase. El Trool jura que no está trucada. El Trool miente.',
             'Gira la ruota della Fiera del Trool: ti dà un incantesimo a caso di un\'altra classe. Il Trool giura che non è truccata. Il Trool mente.',
             'Draai aan het rad van de Trool-kermis: het geeft je een willekeurige spreuk van een andere klasse. De Trool zweert dat het niet vals is. De Trool liegt.',
             'Gire a roda da Feira do Trool: dá-lhe um feitiço ao acaso de outra classe. O Trool jura que não está viciada. O Trool mente.'),
           dict(cd=999), [{}], 'g_jeton', w=0.5),
]

# ---------------------------------------------------------------- 0.23 cooldown pass. Every spell benched alone at level 6
# (sim_node.js BENCH=all: minute 4, 90 s, no level-ups): damage per second / median of the attack spells (107), then
# f = ratio ** 0.6 for the ones outside [0.65, 1.6] x median. Half of f goes to the cooldown, half to the damage (and
# poison), so fast spells don't turn into machine guns and slow ones keep their punch. Utility spells (heals, buffs,
# auras, Kaboom, life steal) are not touched. f > 1: too strong.
CD_PASS = dict(explobombe=2.2, poussiere_temporelle=2.0, grisou=1.95, mot_interdit=1.85, dagues_boomerang=1.8, ronce=1.8, lancer_hachette=1.75, karcham=1.65, bombe_aqueuse=1.55, pelle_massacrante=1.55, piege_sournois=1.55, colere_iop=1.5, tempete_puissance=1.45, larme=1.45, mot_blessant=1.45, roulage_pelle=1.4, rekop=1.4, fleche_enflammee=1.4, bond=1.35, glyphe_enflammee=1.35, lancer_pelle=1.35, flasque_explosive=1.35, tremblement=0.75, fleche_empoisonnee=0.75, lancer_pieces=0.75, tout_ou_rien=0.7, coup_sournois=0.65, pression=0.65, epee_celeste=0.65, griffe_joueuse=0.65, dragonnet_rouge=0.6, fleche_magique=0.6, frappe_xelor=0.6, elagage_cou=0.6, prouts=0.6, vol_pieces=0.6, attirance=0.6, dissolution=0.6, fouet=0.6, poing_enflamme=0.6)
for sid, f in CD_PASS.items():
    k = f ** 0.5
    for d in [C['spells'][sid]['base']] + C['spells'][sid]['lv']:
        if 'cd' in d: d['cd'] = round(max(0.6, d['cd'] * k), 2)
        for key in ('dmg', 'poison'):
            if key in d: d[key] = round(d[key] / k, 1)

UI = {
    'relic_found': T('Relique : {n} !', 'Relic: {n}!', 'Relikt: {n}!', '¡Reliquia: {n}!', 'Reliquia: {n}!', 'Relikwie: {n}!', 'Relíquia: {n}!'),
    'relics': T('Reliques', 'Relics', 'Relikte', 'Reliquias', 'Reliquie', 'Relikwieën', 'Relíquias'),
    'ev_bworks': T('Invasion de Bworks ! Ils ont faim, et vous avez l\'air comestible.', 'Bwork invasion! They are hungry, and you look edible.', 'Bwork-Invasion! Sie haben Hunger, und du siehst essbar aus.', '¡Invasión de Bworks! Tienen hambre y tú pareces comestible.', 'Invasione di Bwork! Hanno fame, e tu sembri commestibile.', 'Bwork-invasie! Ze hebben honger, en jij ziet er eetbaar uit.', 'Invasão de Bworks! Têm fome, e você parece comestível.'),
    'ev_tofus': T('Pluie de Tofus ! Ouvrez le parapluie… ou la bouche.', 'It\'s raining Tofus! Open your umbrella… or your mouth.', 'Es regnet Tofus! Schirm auf… oder Mund.', '¡Lluvia de Tofus! Abre el paraguas… o la boca.', 'Pioggia di Tofu! Aprite l\'ombrello… o la bocca.', 'Het regent Tofu\'s! Paraplu open… of mond open.', 'Chuva de Tofus! Abra o guarda-chuva… ou a boca.'),
    'ev_merchant': T('Un marchand Enutrof s\'est installé sur la carte. Ses prix ? Honnêtes. Pour un Enutrof.', 'An Enutrof merchant set up shop on the map. His prices? Honest. For an Enutrof.', 'Ein Enutrof-Händler hat seinen Stand aufgebaut. Seine Preise? Ehrlich. Für einen Enutrof.', 'Un mercader Anutrof se ha instalado en el mapa. ¿Sus precios? Honrados. Para un Anutrof.', 'Un mercante Enutrof si è piazzato sulla mappa. I suoi prezzi? Onesti. Per un Enutrof.', 'Een Enutrof-handelaar heeft zijn kraam opgezet. Zijn prijzen? Eerlijk. Voor een Enutrof.', 'Um mercador Enutrof montou banca no mapa. Os preços? Honestos. Para um Enutrof.'),
    'ev_kamarain': T('Pluie de kamas ! Un Enutrof a percé ses poches.', 'Kama rain! An Enutrof has a hole in his pockets.', 'Kama-Regen! Ein Enutrof hat Löcher in den Taschen.', '¡Lluvia de kamas! Un Anutrof tiene los bolsillos agujereados.', 'Pioggia di kama! Un Enutrof ha le tasche bucate.', 'Kama-regen! Een Enutrof heeft gaten in zijn zakken.', 'Chuva de kamas! Um Enutrof tem os bolsos furados.'),
    'ev_eclipse': T('Éclipse ! Les monstres y voient mieux que vous dans le noir (20 secondes).', 'Eclipse! Monsters see better than you in the dark (20 seconds).', 'Finsternis! Monster sehen im Dunkeln besser als du (20 Sekunden).', '¡Eclipse! Los monstruos ven mejor que tú en la oscuridad (20 segundos).', 'Eclissi! I mostri vedono meglio di te al buio (20 secondi).', 'Eclips! Monsters zien beter in het donker dan jij (20 seconden).', 'Eclipse! Os monstros veem melhor do que você no escuro (20 segundos).'),
    'merchant': T('Marchand Enutrof', 'Enutrof merchant', 'Enutrof-Händler', 'Mercader Anutrof', 'Mercante Enutrof', 'Enutrof-handelaar', 'Mercador Enutrof'),
    'merchant_hello': T('« Approchez, approchez ! Tout doit disparaître… surtout vos kamas. »', '"Step right up! Everything must go… especially your kamas."', '„Hereinspaziert! Alles muss raus… vor allem deine Kamas."', '«¡Acérquense! Todo debe desaparecer… sobre todo sus kamas.»', '«Avvicinatevi! Tutto deve sparire… soprattutto i vostri kama.»', '"Kom dichterbij! Alles moet weg… vooral je kama\'s."', '«Cheguem-se! Tudo tem de desaparecer… sobretudo os vossos kamas.»'),
    'm_heal': T('Potion de soin complète', 'Full healing potion', 'Volle Heiltrank', 'Poción de curación completa', 'Pozione di cura completa', 'Volledig genezingsdrankje', 'Poção de cura completa'),
    'm_upgrade': T('Amélioration au hasard', 'Random upgrade', 'Zufällige Verbesserung', 'Mejora al azar', 'Miglioramento casuale', 'Willekeurige verbetering', 'Melhoria aleatória'),
    'm_relic': T('Relique mystère', 'Mystery relic', 'Geheimnisvolles Relikt', 'Reliquia misteriosa', 'Reliquia misteriosa', 'Mysterieuze relikwie', 'Relíquia mistério'),
    'm_leave': T('Au revoir', 'Goodbye', 'Auf Wiedersehen', 'Adiós', 'Arrivederci', 'Tot ziens', 'Adeus'),
    'm_broke': T('« Pas de kamas, pas d\'affaire. C\'est la loi d\'Enutrof. »', '"No kamas, no deal. That\'s Enutrof\'s law."', '„Keine Kamas, kein Geschäft. Enutrofs Gesetz."', '«Sin kamas, no hay trato. Es la ley de Anutrof.»', '«Niente kama, niente affare. È la legge di Enutrof.»', '"Geen kama\'s, geen deal. De wet van Enutrof."', '«Sem kamas, sem negócio. É a lei de Enutrof.»'),
    'archi_appears': T('Un Archimonstre rôde : {n} !', 'An Archmonster is lurking: {n}!', 'Ein Archimonster lauert: {n}!', '¡Un Archimonstruo merodea: {n}!', 'Un Arcimostro si aggira: {n}!', 'Een Aartsmonster sluipt rond: {n}!', 'Um Arquimonstro anda por aí: {n}!'),
    'archi_soul': T('Âme capturée : {n} ({c}/{t})', 'Soul captured: {n} ({c}/{t})', 'Seele gefangen: {n} ({c}/{t})', 'Alma capturada: {n} ({c}/{t})', 'Anima catturata: {n} ({c}/{t})', 'Ziel gevangen: {n} ({c}/{t})', 'Alma capturada: {n} ({c}/{t})'),
    'mode_infinite': T('Infini', 'Endless', 'Endlos', 'Infinito', 'Infinito', 'Eindeloos', 'Infinito'),
    'mode_inf_hint': T('Mode infini : pas de fin, les boss reviennent toujours plus forts. Survivez le plus longtemps possible !', 'Endless mode: no end, the bosses keep coming back stronger. Survive as long as you can!', 'Endlosmodus: kein Ende, die Bosse kommen immer stärker zurück. Überlebe so lange wie möglich!', 'Modo infinito: sin final, los jefes vuelven cada vez más fuertes. ¡Sobrevive lo máximo posible!', 'Modalità infinita: nessuna fine, i boss tornano sempre più forti. Sopravvivi il più a lungo possibile!', 'Eindeloze modus: geen einde, de bazen komen steeds sterker terug. Overleef zo lang mogelijk!', 'Modo infinito: sem fim, os chefes voltam sempre mais fortes. Sobreviva o máximo possível!'),
    'leaderboard': T('Classement', 'Leaderboard', 'Rangliste', 'Clasificación', 'Classifica', 'Ranglijst', 'Classificação'),
    'lb_empty': T('Aucune partie infinie… pour l\'instant. Le Tofu attend son heure.', 'No endless run… yet. The Tofu bides its time.', 'Noch kein Endlos-Lauf… Der Tofu wartet ab.', 'Ninguna partida infinita… por ahora. El Tofu espera su momento.', 'Nessuna partita infinita… per ora. Il Tofu aspetta il suo momento.', 'Nog geen eindeloze run… De Tofu wacht zijn tijd af.', 'Nenhuma partida infinita… por agora. O Tofu espera a sua vez.'),
    'lb_rank': T('Classement : {n}e', 'Rank: #{n}', 'Platz {n}', 'Puesto: {n}.º', 'Posizione: {n}ª', 'Plaats: {n}e', 'Posição: {n}.º'),
    'lb_cycle': T('Cycle {n} : les boss reviennent, plus forts !', 'Cycle {n}: the bosses are back, stronger!', 'Zyklus {n}: die Bosse kehren stärker zurück!', 'Ciclo {n}: ¡los jefes vuelven, más fuertes!', 'Ciclo {n}: i boss tornano, più forti!', 'Cyclus {n}: de bazen zijn terug, sterker!', 'Ciclo {n}: os chefes voltam, mais fortes!'),
    'g_spell': T('Sort global', 'Global spell', 'Globaler Zauber', 'Hechizo global', 'Incantesimo globale', 'Algemene spreuk', 'Feitiço global'),
    'pioche_jackpot': T('FILON ! +{n} kamas ! L\'Enutrof en vous pleure de joie.', 'MOTHERLODE! +{n} kamas! The Enutrof in you weeps with joy.', 'GOLDADER! +{n} Kamas! Der Enutrof in dir weint vor Freude.', '¡FILÓN! ¡+{n} kamas! El Anutrof que llevas dentro llora de alegría.', 'FILONE! +{n} kama! L\'Enutrof che è in te piange di gioia.', 'GOUDADER! +{n} kama\'s! De Enutrof in jou huilt van vreugde.', 'FILÃO! +{n} kamas! O Enutrof que há em si chora de alegria.'),
    'wheel_title': T('Roue de la Foire du Trool', 'Trool Fair Wheel', 'Rad des Trool-Jahrmarkts', 'Rueda de la Feria del Trool', 'Ruota della Fiera del Trool', 'Rad van de Trool-kermis', 'Roda da Feira do Trool'),
    'wheel_spin': T('Ça tourne, ça tourne… le Trool sourit, c\'est mauvais signe.', 'Round and round… the Trool is smiling, that\'s a bad sign.', 'Es dreht sich… der Trool lächelt, kein gutes Zeichen.', 'Gira que gira… el Trool sonríe, mala señal.', 'Gira e rigira… il Trool sorride, brutto segno.', 'Het draait en draait… de Trool glimlacht, slecht teken.', 'Gira, gira… o Trool sorri, mau sinal.'),
    'wheel_won': T('Gagné : {n} ({c}) !', 'You won: {n} ({c})!', 'Gewonnen: {n} ({c})!', '¡Ganaste: {n} ({c})!', 'Hai vinto: {n} ({c})!', 'Gewonnen: {n} ({c})!', 'Ganhou: {n} ({c})!'),
    'wheel_ok': T('Encaisser', 'Collect', 'Einsacken', 'Cobrar', 'Incassa', 'Innen', 'Receber'),
    'p_kamas': T('Kamas', 'Kamas', 'Kamas', 'Kamas', 'Kama', 'Kama\'s', 'Kamas'),
    'p_size': T('Taille', 'Size', 'Größe', 'Tamaño', 'Dimensione', 'Grootte', 'Tamanho'),
    'p_rotSpeed': T('Rotation', 'Spin', 'Drehung', 'Rotación', 'Rotazione', 'Draaiing', 'Rotação'),
    'p_curve': T('Courbe', 'Curve', 'Kurve', 'Curva', 'Curva', 'Boog', 'Curva'),
    'souls': T('Âmes', 'Souls', 'Seelen', 'Almas', 'Anime', 'Zielen', 'Almas'),
}
for k, v in UI.items():
    for lg, txt in v.items(): C['ui'][lg][k] = txt

if __name__ == '__main__':
    json.dump(C, open(f'{G}/data/content.json', 'w'), ensure_ascii=False, separators=(',', ':'))
    print('0.23 ok', len(C['relics']), 'relics,', sum(len(v) for v in C['archi'].values()), 'archimonsters on', len(C['archi']), 'monsters')
