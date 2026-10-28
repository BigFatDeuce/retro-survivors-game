"""Beta 0.37 content, applied on top of patch_034.   usage: python tools/content/patch_035.py"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
import _root
import json
import patch_034 as P4
import langdata as LD
import patch_023 as P23   # (already loaded by the chain: its flavor() reads the official item texts)

C, T, G = P4.C, P4.T, P4.G
P3 = P4.P3


def put_ui(D):
    for k, v in D.items():
        for lg in C['ui']: C['ui'][lg][k] = v[lg]


# XP: the ambers (monsters' XP) -25 %, the bosses' -50 %
for m in C['monsters'].values(): m['xp'] = round(m['xp'] * 0.75, 2)
for b in C['bosses'].values(): b['xp'] = round(b['xp'] * 0.5, 2)

# the Maîtres Corbacs: half the life, they call their corbacs only from half as far (they used to from anywhere)
C['doomHpK'] = 0.5
for a in C['bosses']['maitre_corbac_doom']['abilities']:
    if a['k'] == 'crow': a['range'] = 600

# Endless: from 10:00 on, the zone's final boss every minute, 2, 4, 8… of them (no Maîtres Corbacs); they drop the
# Manuel du Tailleur 5x as often as the run's own roll
C['infinite'].update(bossT=600, bossCap=64, manuelK=5)

# ToT's portal: one run in five
C['portal']['chance'] = 0.2

# relics: 10 more (still only from bosses, and now from the mini-bosses: elites and Archimonsters)
C['relicMini'] = 0.12
RELICS = [
    ('bottes_koulosse', 7889, dict(speed=0.15), {},
     T('+15 % de vitesse. Le Koulosse ne court pas, il arrive.', '+15% speed. The Koulosse doesn\'t run, it arrives.', '+15 % Tempo. Der Koloss rennt nicht, er kommt an.', '+15 % de velocidad. El Kolosso no corre, llega.', '+15% velocità. Il Kolosso non corre, arriva.', '+15% snelheid. De Kolos rent niet, hij arriveert.', '+15% de velocidade. O Kolosso não corre, chega.')),
    ('amu_craqueleur_leg', 8150, dict(armor=6, maxhp=0.1), {},
     T('+6 résistance et +10 % de PV max. Un caillou de luxe.', '+6 armour and +10% max HP. A luxury pebble.', '+6 Resistenz und +10 % max. LP. Ein Luxuskiesel.', '+6 de resistencia y +10 % de PdV máx. Un guijarro de lujo.', '+6 resistenza e +10% PV max. Un sassolino di lusso.', '+6 weerstand en +10% max. LP. Een luxe kiezel.', '+6 de resistência e +10% de PV máx. Um seixo de luxo.')),
    ('ceinture_craqueleur_leg', 8152, dict(area=0.2), {},
     T('+20 % de zone d\'effet. Elle fait aussi le tour de taille.', '+20% area. It goes all the way round, too.', '+20 % Wirkungsbereich. Sie passt auch um den Bauch.', '+20 % de área. También da la vuelta a la cintura.', '+20% area. Fa anche il giro vita.', '+20% bereik. Hij past ook om je middel.', '+20% de área. Também dá a volta à cintura.')),
    ('anneau_dragon_cochon', 8271, dict(might=0.15, crit=0.05), {},
     T('+15 % de dégâts et +5 % de critiques. Ça sent le lard grillé.', '+15% damage and +5% crits. Smells of grilled bacon.', '+15 % Schaden und +5 % kritische Treffer. Riecht nach gegrilltem Speck.', '+15 % de daño y +5 % de críticos. Huele a panceta asada.', '+15% danni e +5% critici. Sa di lardo alla griglia.', '+15% schade en +5% kritiek. Ruikt naar gegrild spek.', '+15% de dano e +5% de críticos. Cheira a toucinho grelhado.')),
    ('coiffe_dragon_cochon', 8285, dict(critMult=0.5), {},
     T('Les coups critiques font +50 % de dégâts en plus. Groin !', 'Critical hits deal +50% more damage. Oink!', 'Kritische Treffer machen +50 % mehr Schaden. Grunz!', 'Los críticos hacen +50 % más de daño. ¡Oink!', 'I colpi critici fanno +50% danni in più. Oink!', 'Kritieke treffers doen +50% meer schade. Knor!', 'Os críticos fazem +50% mais dano. Oinc!')),
    ('masque_rat_noir', 8442, dict(cooldown=-0.12), {},
     T('Sorts rechargés 12 % plus vite. On ne voit plus vos cernes.', 'Spells recharge 12% faster. No one sees your dark circles any more.', 'Zauber laden 12 % schneller. Niemand sieht mehr deine Augenringe.', 'Hechizos un 12 % más rápidos. Ya nadie ve tus ojeras.', 'Incantesimi ricaricati il 12% più in fretta. Nessuno vede più le tue occhiaie.', 'Spreuken laden 12% sneller op. Niemand ziet je wallen nog.', 'Feitiços recarregam 12% mais rápido. Ninguém vê as tuas olheiras.')),
    ('anneau_rat_noir', 8448, dict(luck=0.3), {},
     T('+30 % de chance. Un rat noir qui porte bonheur, cherchez l\'erreur.', '+30% luck. A lucky black rat, go figure.', '+30 % Glück. Eine schwarze Ratte, die Glück bringt, wer versteht das.', '+30 % de suerte. Una rata negra que trae suerte, a ver quién lo entiende.', '+30% fortuna. Un ratto nero portafortuna, chi l\'avrebbe detto.', '+30% geluk. Een zwarte rat die geluk brengt, snap het maar.', '+30% de sorte. Um rato preto que dá sorte, vai-se lá perceber.')),
    ('cape_wa_wabbit', 971, dict(greed=0.4, growth=0.1), {},
     T('+40 % de kamas et +10 % d\'expérience. Royale, mais à poils.', '+40% kamas and +10% experience. Royal, but furry.', '+40 % Kamas und +10 % Erfahrung. Königlich, aber haarig.', '+40 % de kamas y +10 % de experiencia. Real, pero peluda.', '+40% kama e +10% esperienza. Regale, ma pelosa.', '+40% kama en +10% ervaring. Koninklijk, maar harig.', '+40% de kamas e +10% de experiência. Real, mas peluda.')),
    ('coiffe_chene_mou', 8474, dict(healBonus=0.3, regen=0.3), {},
     T('+30 % de soins reçus et +0,3 PV par seconde. Ça repousse.', '+30% healing and +0.3 HP per second. It grows back.', '+30 % Heilung und +0,3 LP pro Sekunde. Wächst nach.', '+30 % de curación y +0,3 PdV por segundo. Vuelve a crecer.', '+30% cure e +0,3 PV al secondo. Ricresce.', '+30% genezing en +0,3 LP per seconde. Het groeit terug.', '+30% de cura e +0,3 PV por segundo. Volta a crescer.')),
    ('bouclier_moon', 10159, dict(duration=0.2, projspeed=0.2), {},
     T('+20 % de durée et de vitesse des projectiles. Trophée de la plage.', '+20% duration and projectile speed. A beach trophy.', '+20 % Dauer und Projektiltempo. Eine Strandtrophäe.', '+20 % de duración y velocidad de proyectiles. Trofeo de playa.', '+20% durata e velocità dei proiettili. Trofeo da spiaggia.', '+20% duur en projectielsnelheid. Een strandtrofee.', '+20% de duração e velocidade dos projéteis. Troféu de praia.')),
]
have = {r['id'] for r in C['relics']}
for rid, iid, bonus, special, eff in RELICS:
    if rid in have: continue
    info = LD.item_info(iid)
    C['relics'].append(dict(id=rid, item=iid, icon=f"it_{info['t']}_{info['g']}", name=LD.item(iid), bonus=bonus, special=special, desc=eff, flavor=P23.flavor(iid)))

# 4 achievements
A = [
    ('ttg_50', 'ttgCards', 50, 'it_24_43',
     T('Collectionneur compulsif', 'Compulsive Collector', 'Zwanghafter Sammler', 'Coleccionista compulsivo', 'Collezionista compulsivo', 'Dwangmatige verzamelaar', 'Colecionador compulsivo'),
     T('Posséder 50 cartes TTG différentes. Le classeur commence à peser.', 'Own 50 different TTG cards. The binder is getting heavy.', '50 verschiedene TTG-Karten besitzen. Der Ordner wird schwer.', 'Tener 50 cartas TTG distintas. El archivador empieza a pesar.', 'Possedere 50 carte TTG diverse. Il raccoglitore comincia a pesare.', '50 verschillende TTG-kaarten bezitten. De map wordt zwaar.', 'Ter 50 cartas TTG diferentes. O dossiê começa a pesar.')),
    ('boosters_10', 'boosters', 10, 'it_15_224',
     T('Ça sent le neuf', 'That New Card Smell', 'Riecht nach neu', 'Huele a nuevo', 'Profumo di nuovo', 'Dat ruikt nieuw', 'Cheira a novo'),
     T('Ouvrir 10 boosters. Ne mangez pas le papier.', 'Open 10 boosters. Don\'t eat the wrapper.', '10 Booster öffnen. Nicht die Verpackung essen.', 'Abrir 10 sobres. No te comas el envoltorio.', 'Aprire 10 bustine. Non mangiare la carta.', '10 boosters openen. Eet de verpakking niet op.', 'Abrir 10 boosters. Não comas o papel.')),
    ('endless_finals', 'endlessBosses', 50, 'it_24_156',
     T('Encore ? Encore !', 'Again? Again!', 'Schon wieder? Schon wieder!', '¿Otra vez? ¡Otra vez!', 'Ancora? Ancora!', 'Alweer? Alweer!', 'Outra vez? Outra vez!'),
     T('Vaincre 50 boss de fin de zone après 10:00 en mode Infini. Ils ont des cousins.', 'Defeat 50 final bosses after 10:00 in Endless mode. They have cousins.', 'Im Endlos-Modus nach 10:00 50 Endbosse besiegen. Sie haben Cousins.', 'Vencer a 50 jefes finales tras el 10:00 en modo Infinito. Tienen primos.', 'Sconfiggere 50 boss finali dopo le 10:00 in modalità Infinita. Hanno cugini.', '50 eindbazen verslaan na 10:00 in de Eindeloze modus. Ze hebben neven.', 'Vencer 50 chefes finais depois das 10:00 no modo Infinito. Eles têm primos.')),
    ('reflect_100', 'reflectKills', 100, 'it_82_23',
     T('Qui s\'y frotte s\'y pique', 'Look But Don\'t Touch', 'Wer sich reibt, der sticht sich', 'Quien se roza, se pincha', 'Chi tocca si punge', 'Wie aanraakt, wordt geprikt', 'Quem se roça, pica-se'),
     T('Achever 100 monstres avec le Renvoi de dommages. Ils l\'ont cherché.', 'Finish off 100 monsters with Damage reflection. They asked for it.', '100 Monster mit dem Schadensrückwurf erledigen. Selbst schuld.', 'Rematar a 100 monstruos con el Reenvío de daños. Se lo buscaron.', 'Finire 100 mostri con il Rinvio dei danni. Se la sono cercata.', '100 monsters afmaken met Schadeterugkaatsing. Ze vroegen erom.', 'Acabar com 100 monstros com o Reenvio de danos. Estavam a pedi-las.')),
]
have = {a['id'] for a in C['achievements']}
for i, k, n, icon, name, desc in A:
    if i not in have: C['achievements'].append(dict(id=i, k=k, n=n, icon=icon, name=name, desc=desc))

# the spells that jump or dash onto the monsters: untouchable in the air / while dashing, and 0.2 s after
_INV = T(' Invulnérable pendant le mouvement et 0,2 s après.', ' Invulnerable during the move and for 0.2 s after.', ' Unverwundbar während der Bewegung und 0,2 s danach.', ' Invulnerable durante el movimiento y 0,2 s después.', ' Invulnerabile durante il movimento e per 0,2 s dopo.', ' Onkwetsbaar tijdens de beweging en 0,2 s erna.', ' Invulnerável durante o movimento e 0,2 s depois.')
for sp in (C['spells'].values() if isinstance(C['spells'], dict) else C['spells']):
    if sp.get('t') in ('leap', 'dash'):
        for lg in sp['desc']:
            if not sp['desc'][lg].endswith(_INV[lg]): sp['desc'][lg] += _INV[lg]

put_ui({
    'lb_finals': T('10:00 — {n} revient, et il amène sa famille ! Deux fois plus à chaque minute.', '10:00 — {n} is back, and brought the family! Twice as many every minute.', '10:00 — {n} ist zurück und bringt die Familie mit! Jede Minute doppelt so viele.', '10:00 — ¡{n} vuelve, y trae a la familia! El doble cada minuto.', '10:00 — {n} è tornato, e ha portato la famiglia! Il doppio ogni minuto.', '10:00 — {n} is terug, met de hele familie! Elke minuut twee keer zoveel.', '10:00 — {n} está de volta, e trouxe a família! O dobro a cada minuto.'),
})

if __name__ == '__main__':
    json.dump(C, open(f'{G}/data/content.json', 'w'), ensure_ascii=False, separators=(',', ':'))
    print('0.37 ok', len(C['relics']), 'relics,', len(C['achievements']), 'achievements')
