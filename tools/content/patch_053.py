"""Beta 0.53 content, applied on top of patch_052.   usage: python tools/content/patch_053.py"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
import _root
import json, math
import patch_052 as P2

C, G = P2.C, P2.G
P4 = P2.P4; T = P4.T; put_ui = P4.P3.put_ui

# Sagesse: its real icon (the client's yin-yang, Icon_37, not 'XP') and, besides the XP, a chance to block the monsters'
# ranged spells (projectiles and thrown spells; not the arrows, not the blows): 5 % at level 1 to 10 % at level 5
S = next(p for p in C['passives'] if p['id'] == 'sagesse')
S.update(icon='Icon_37', block=[0.05, 0.10],
         desc=T("+8 % d'expérience par niveau. 5 % (niv. 1) à 10 % (niv. 5) de chances de bloquer un sort à distance d'un monstre (pas les flèches).",
                "+8% experience per level. 5% (lv 1) to 10% (lv 5) chance to block a monster's ranged spell (not arrows).",
                '+8 % Erfahrung pro Stufe. 5 % (St. 1) bis 10 % (St. 5) Chance, einen Fernzauber eines Monsters abzuwehren (keine Pfeile).',
                '+8 % de experiencia por nivel. 5 % (niv. 1) a 10 % (niv. 5) de probabilidad de bloquear un hechizo a distancia de un monstruo (no las flechas).',
                "+8% di esperienza per livello. Dal 5% (liv. 1) al 10% (liv. 5) di probabilità di bloccare un incantesimo a distanza di un mostro (non le frecce).",
                '+8% ervaring per niveau. 5% (niv. 1) tot 10% (niv. 5) kans om een afstandsspreuk van een monster te blokkeren (geen pijlen).',
                '+8% de experiência por nível. 5% (nív. 1) a 10% (nív. 5) de hipótese de bloquear um feitiço à distância de um monstro (não as flechas).'))

# the melee weapons that hit an area (swords, staffs, axes, hammers, shovels; not the daggers' narrow stab): the area
# halved (each size x 1/sqrt 2), levels and finales too
K = 1 / math.sqrt(2)
def shrink(d, keys=('range', 'width', 'radius')):
    for k in keys:
        if isinstance(d.get(k), (int, float)): d[k] = round(d[k] * K, 1)
AOE = [w for w in C['weapons'] + C['uniqueWeapons'] if w['t'] in ('melee', 'slam') and w['base'].get('width', 999) >= 70]
for w in AOE:
    for d in [w['base']] + w['lv']: shrink(d)
    for e in C['weaponEvo'].get(w['id'], []):
        for op in ('set', 'add'): shrink(e.get(op) or {})

put_ui({
    'cd_go': T('GO !', 'GO!', 'LOS!', '¡YA!', 'VIA!', 'GO!', 'JÁ!'),
    'spell_block': T('Bloqué !', 'Blocked!', 'Abgewehrt!', '¡Bloqueado!', 'Bloccato!', 'Geblokkeerd!', 'Bloqueado!'),
    # (the real values on the level-up cards, ui.js passiveReal)
    'ps_maxhp': T('PV max', 'Max HP', 'Max. LP', 'PdV máx.', 'PV max', 'Max. LP', 'PV máx.'),
    'ps_growth': T('Expérience', 'Experience', 'Erfahrung', 'Experiencia', 'Esperienza', 'Ervaring', 'Experiência'),
    'ps_block': T('Blocage des sorts', 'Spell block', 'Zauberabwehr', 'Bloqueo de hechizos', 'Blocco incantesimi', 'Spreukblokkade', 'Bloqueio de feitiços'),
    'ps_projspeed': T('Vitesse et portée des projectiles', 'Projectile speed and range', 'Tempo und Reichweite der Geschosse', 'Velocidad y alcance de los proyectiles',
                      'Velocità e portata dei proiettili', 'Snelheid en bereik van projectielen', 'Velocidade e alcance dos projéteis'),
    'ps_regen': T('PV par seconde', 'HP per second', 'LP pro Sekunde', 'PdV por segundo', 'PV al secondo', 'LP per seconde', 'PV por segundo'),
    'ps_magnet': T('Ramassage', 'Pickup range', 'Aufsammelradius', 'Radio de recogida', 'Raggio di raccolta', 'Oppakbereik', 'Alcance de recolha'),
    'ps_kamas': T('Kamas', 'Kamas', 'Kamas', 'Kamas', 'Kama', "Kama's", 'Kamas'),
    'ps_reflect': T('Dégâts renvoyés', 'Damage reflected', 'Zurückgeworfener Schaden', 'Daño reenviado', 'Danni rinviati', 'Teruggekaatste schade', 'Dano reenviado'),
})

# once everything is maxed, a level offers the client's Incroyable potion de soin de masse (item 9900) instead of the
# bread: heals 25 % of the life and the summons (extras.js massPotion; the upgrade kind stays 'bread', saved settings)
C['massPotion'] = dict(heal=0.25, icon='it_14_70', snd='panda_gloups')
put_ui({
    'take_bread': T('Incroyable potion de soin de masse', 'Incredible Mass Healing Potion', 'Unglaublicher Trank der Massenheilung',
                    'Increíble pócima de curación de masas', 'Incredibile pozione di cura di massa', 'Ongelooflijk Drankje van Massale Genezing',
                    'Incrível Poção de Cura em Massa'),
    'take_bread_d': T('Rend 25 % de vos PV et soigne vos invocations.', 'Restores 25% of your HP and heals your summons.',
                      'Stellt 25 % deiner LP wieder her und heilt deine Beschwörungen.', 'Restaura el 25 % de tus PdV y cura a tus invocaciones.',
                      'Ripristina il 25% dei tuoi PV e cura le tue evocazioni.', 'Herstelt 25% van je LP en geneest je oproepingen.',
                      'Restaura 25% dos teus PV e cura as tuas invocações.'),
    'ctl_auto': T('Choix auto potion / kamas', 'Auto potion / kamas', 'Auto-Wahl Trank / Kamas', 'Pócima / kamas automático', 'Pozione / kama automatico',
                  'Auto drankje / kama', 'Poção / kamas automático'),
    'ctl_autotap': T("Touchez l'icône potion / kamas (à droite de la plume)", 'Tap the potion / kamas icon (right of the feather)',
                     'Tippe auf das Trank-/Kamas-Symbol (rechts der Feder)', 'Toca el icono pócima / kamas (a la derecha de la pluma)',
                     "Tocca l'icona pozione / kama (a destra della piuma)", 'Tik op het drankje- / kama-pictogram (rechts van de veer)',
                     'Toca no ícone poção / kamas (à direita da pena)'),
})

# loading tips: the max-level one names the potion now; three tips for the newer systems (elites, vampiric weapons, Sagesse)
LG = ('fr', 'en', 'de', 'es', 'it', 'nl', 'pt')
def tip_set(old_fr, t):
    i = C['tips']['fr'].index(next(x for x in C['tips']['fr'] if old_fr in x))
    for lg in LG: C['tips'][lg][i] = t[lg]
def tip_add(t):
    for lg in LG:
        if t[lg] not in C['tips'][lg]: C['tips'][lg].append(t[lg])
tip_set('chaque niveau donne du pain ou des kamas', T(
    "Une fois tout au maximum, chaque niveau donne une Incroyable potion de soin de masse ou des kamas (R ou B pour garder le choix). Les Enutrofs prennent les kamas, les Pandawas la potion… en espérant qu'elle soit alcoolisée.",
    'Once everything is maxed, each level gives an Incredible Mass Healing Potion or kamas (R or B keeps the choice). Enutrofs take the kamas, Pandawas the potion… hoping there is alcohol in it.',
    'Ist alles ausgebaut, gibt jede Stufe einen Unglaublichen Trank der Massenheilung oder Kamas (R oder B behält die Wahl). Enutrofs nehmen die Kamas, Pandawas den Trank… in der Hoffnung, dass Alkohol drin ist.',
    'Con todo al máximo, cada nivel da una Increíble pócima de curación de masas o kamas (R o B mantiene la elección). Los Anutrofs se quedan los kamas, los Pandawas la pócima… esperando que lleve alcohol.',
    "Con tutto al massimo, ogni livello dà un'Incredibile pozione di cura di massa o kama (R o B mantiene la scelta). Gli Anutrof prendono i kama, i Pandawa la pozione… sperando che sia alcolica.",
    "Staat alles op het maximum, dan geeft elk niveau een Ongelooflijk Drankje van Massale Genezing of kama's (R of B houdt de keuze). Enutrofs nemen de kama's, Pandawa's het drankje… in de hoop dat er alcohol in zit.",
    'Com tudo no máximo, cada nível dá uma Incrível Poção de Cura em Massa ou kamas (R ou B mantém a escolha). Os Enutrofs ficam com os kamas, os Pandawas com a poção… na esperança de que tenha álcool.'))
tip_add(T('Toutes les 30 secondes, des élites débarquent avec leur nom et leur barre de vie, et un coffre arrive toutes les trois vagues. Un Enutrof, lui, ne compte que les coffres.',
          'Every 30 seconds, elites show up with their name and life bar, and every third wave brings a chest. An Enutrof only counts the chests.',
          'Alle 30 Sekunden kommen Elitemonster mit Namen und Lebensbalken, und jede dritte Welle bringt eine Truhe. Ein Enutrof zählt nur die Truhen.',
          'Cada 30 segundos llegan élites con su nombre y su barra de vida, y cada tres oleadas trae un cofre. Un Anutrof solo cuenta los cofres.',
          'Ogni 30 secondi arrivano élite con nome e barra della vita, e ogni tre ondate porta un forziere. Un Anutrof conta solo i forzieri.',
          'Elke 30 seconden komen er elites met hun naam en levensbalk, en elke derde golf brengt een kist. Een Enutrof telt alleen de kisten.',
          'A cada 30 segundos chegam elites com o nome e a barra de vida, e cada três vagas trazem um baú. Um Enutrof só conta os baús.'))
tip_add(T('Les armes au cadre rouge volent de la vie à chaque coup. Un Sacrieur trouve ça normal, un Eniripsa trouve ça déloyal.',
          'Weapons with a red frame steal life with every hit. A Sacrier finds it normal, an Eniripsa finds it unfair.',
          'Waffen mit rotem Rahmen stehlen bei jedem Treffer Leben. Ein Sacrieur findet das normal, ein Eniripsa unfair.',
          'Las armas con marco rojo roban vida en cada golpe. A un Sacrógrito le parece normal; a un Aniripsa, desleal.',
          'Le armi dalla cornice rossa rubano vita a ogni colpo. Per un Sàcride è normale, per un Aniripsa è sleale.',
          'Wapens met een rode rand stelen leven bij elke klap. Een Sacrier vindt dat normaal, een Eniripsa oneerlijk.',
          'As armas de moldura vermelha roubam vida a cada golpe. Um Sacrier acha normal, um Eniripsa acha desleal.'))
tip_add(T("La Sagesse ne fait pas que monter l'expérience : elle bloque parfois un sort lancé par un monstre. Pas les flèches : un Crâ vise trop bien.",
          "Wisdom doesn't only raise experience: it sometimes blocks a spell cast by a monster. Not arrows: a Cra aims too well.",
          'Weisheit erhöht nicht nur die Erfahrung: Sie wehrt manchmal einen Zauber eines Monsters ab. Keine Pfeile: Ein Cra zielt zu gut.',
          'La Sabiduría no solo sube la experiencia: a veces bloquea un hechizo lanzado por un monstruo. Las flechas no: un Ocra apunta demasiado bien.',
          "La Saggezza non aumenta solo l'esperienza: a volte blocca un incantesimo lanciato da un mostro. Non le frecce: un Ocra mira troppo bene.",
          'Wijsheid verhoogt niet alleen de ervaring: ze blokkeert soms een spreuk van een monster. Geen pijlen: een Cra mikt te goed.',
          'A Sabedoria não aumenta só a experiência: às vezes bloqueia um feitiço lançado por um monstro. As flechas não: um Cra aponta bem demais.'))

if __name__ == '__main__':
    json.dump(C, open(f'{G}/data/content.json', 'w'), ensure_ascii=False, separators=(',', ':'))
    print('0.53 ok', len(AOE), 'area weapons', next(w for w in C['weapons'] if w['id'] == 'epee')['base'])
