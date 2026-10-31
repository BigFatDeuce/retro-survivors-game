"""The game's instruction booklet (PDF) in French, English and Spanish, in the style of the 90s console manuals (N64 /
PS1): A5 pages, a bold cover, a warning page, contents, controls, how a run goes, first steps, then every class, spell,
characteristic, weapon, relic, Dofus, zone and mode. Everything that changes with the game (names, descriptions,
numbers, pictures) is read from game/data/content.json (in the booklet's language) and the game's own atlases, so
re-running this after a patch updates the booklets; only the hand-written chapters (story, controls, how to play,
events) live here, as t(fr, en, es).
usage: python tools/make_manual.py [fr|en|es ...]   (default: the three)
       -> manual/RetroSurvivors_Manual_<FR|EN|ES>.pdf (+ manual/manual_<lang>.html)"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from _root import ROOT
import os, io, re, json, base64, html
from PIL import Image

G = f'{ROOT}/game'
OUT = f'{ROOT}/manual'
C = json.load(open(f'{G}/data/content.json', encoding='utf8'))
S = json.load(open(f'{G}/data/sprites.json', encoding='utf8'))
BUILD = re.search(r"BUILD = '([^']+)'", open(f'{G}/js/assets.js', encoding='utf8').read()).group(1)
LANGS = ('fr', 'en', 'es')
LG = 'fr'   # (the booklet being made: L() and t() read it)
L = lambda o: (o.get(LG) or o.get('fr') or next(iter(o.values()))) if isinstance(o, dict) else (o or '')
t = lambda fr, en, es: {'fr': fr, 'en': en, 'es': es}[LG]
E = html.escape
_img, _uri = {}, {}


def atlas(path):
    if path not in _img: _img[path] = Image.open(path).convert('RGBA')
    return _img[path]


def uri(im, q=88):
    b = io.BytesIO(); im.save(b, 'WEBP', quality=q); return 'data:image/webp;base64,' + base64.b64encode(b.getvalue()).decode()


def icon(key, px=96):
    """an icon from the game's atlases (icons3 pages, icons2, icons), as a data URI (kept: the three booklets share them)"""
    if (key, px) in _uri: return _uri[key, px]
    out = ''
    for name, F in (('icons3', S.get('icons3', {})), ('icons2', S.get('icons2', {})), ('icons', S.get('icons', {}))):
        f = F.get(key)
        if not f: continue
        page = f[8] if name == 'icons3' and len(f) > 8 else 0
        p = f'{G}/assets/ui/{name}' + (f'_{page}' if page else '') + '.webp'
        im = atlas(p).crop((f[0], f[1], f[0] + f[2], f[1] + f[3])); im.thumbnail((px, px), Image.LANCZOS)
        out = uri(im); break
    _uri[key, px] = out; return out


def art(key, px=360):
    if ('art', key, px) in _uri: return _uri['art', key, px]
    f = S['art']['f'].get(key); out = ''
    if f:
        im = atlas(f'{G}/assets/art/art_{f[0]}.webp').crop((f[1], f[2], f[1] + f[3], f[2] + f[4])); im.thumbnail((px, px), Image.LANCZOS); out = uri(im)
    _uri['art', key, px] = out; return out


def mini(world, px=520):
    p = f'{G}/assets/worlds/{world}_mini.webp'
    if not os.path.exists(p): return ''
    if ('mini', world, px) not in _uri:
        im = Image.open(p).convert('RGB'); im.thumbnail((px, px), Image.LANCZOS); _uri['mini', world, px] = uri(im, 82)
    return _uri['mini', world, px]


def font(f):
    return 'data:font/woff2;base64,' + base64.b64encode(open(f'{G}/assets/fonts/{f}', 'rb').read()).decode()


def h2(title, ic=None, style=''):
    """a chapter title with an icon of the game before it (0.46); ic = an icon key, or 'zone' (the first zone's map)"""
    src = mini('astrub', 90) if ic == 'zone' else icon(ic, 90) if ic else ''
    im = f'<img class="h2i{" round" if ic == "zone" else ""}" src="{src}">' if src else ''
    return f'<h2{f" style={chr(34)}{style}{chr(34)}" if style else ""}>{im}{title}</h2>'


def zname(zid):
    return L(next((m['name'] for m in C['maps'] if m['id'] == zid), {}))


# ---------------------------------------------------------------- hand-written chapters (edit here when the rules change)
def texts():
    J, A, M_ = C.get('jorbak', {}), C.get('beginnerAid', {}), C.get('manuel', {})
    aid = ', '.join(f"{zname(z)} −{round((1 - a['hp']) * 100)} %" for z, a in A.items())
    grobe = zname((C.get('gany') or {}).get('unlockHard', 'grobe'))
    jfrom = J.get('from', 10) + 1
    T = {}
    T['story'] = t(
        """Le Monde des Douze ne tourne plus rond : les monstres des quatre coins d'Amakna se sont réveillés en même temps
et déferlent par vagues sur les aventuriers. Les sages de l'Ordre des Survivants n'ont qu'un conseil : tenir. Dix
minutes. Assez longtemps pour que le gardien de la zone se montre, que vous l'abattiez, et que les Dofus, ces œufs
de dragon que tout le monde convoite, roulent enfin à vos pieds.<br><br>Choisissez votre classe, votre zone, et
survivez. Le reste, c'est une histoire de sorts, de reliques… et d'un peu de chance d'Ecaflip.""",
        """The World of Twelve has gone mad: monsters from every corner of Amakna woke up at the same time and are
sweeping over adventurers in waves. The sages of the Order of Survivors have only one piece of advice: hold on. Ten
minutes. Long enough for the zone's guardian to show up, for you to bring it down, and for the Dofus, those dragon
eggs everyone covets, to finally roll at your feet.<br><br>Pick your class, pick your zone, and survive. The rest
is a matter of spells, relics… and a little of Ecaflip's luck.""",
        """El Mundo de los Doce ha perdido el juicio: los monstruos de todos los rincones de Amakna despertaron a la vez
y caen en oleadas sobre los aventureros. Los sabios de la Orden de los Supervivientes solo tienen un consejo: aguantar.
Diez minutos. Lo justo para que aparezca el guardián de la zona, lo derrotes y los Dofus, esos huevos de dragón que
todos codician, rueden por fin a tus pies.<br><br>Elige tu clase, elige tu zona y sobrevive. El resto es cuestión de
hechizos, reliquias… y un poco de la suerte de Ecaflip.""")
    T['goal'] = t(
        """Une partie dure <b>10 minutes</b>. Les monstres arrivent par vagues de plus en plus fortes ; vous attaquez
<b>automatiquement</b> : il suffit de vous déplacer. Les monstres vaincus lâchent des <b>ambres d'expérience</b>.
À chaque niveau gagné, choisissez une amélioration parmi trois (ou relancez les dés ; une fois par partie, vous pouvez
aussi <b>Bannir</b> une carte pour de bon (une arme : tout son type) ou <b>Passer</b> le choix). Deux sorts au maximum (ou un sort et l'arme qui va
avec) peuvent <b>fusionner</b> en un sort plus fort qui libère une place. Des <b>boss</b> apparaissent
au fil de la partie ; le <b>boss final</b> arrive vers la fin. Abattez-le pour gagner la zone et débloquer la suivante
(tous les boss de la zone doivent tomber dans la même partie).<br><br>Après 10:00, les <b>Maîtres Corbacs</b>
envahissent la carte : la partie devient une course à la survie.""",
        """A run lasts <b>10 minutes</b>. Monsters come in stronger and stronger waves; you attack <b>automatically</b>:
all you do is move. Defeated monsters drop <b>experience ambers</b>. At each level, pick one upgrade out of three (or
reroll the dice; once per run you can also <b>Banish</b> a card for good (a weapon: its whole type) or <b>Skip</b> the choice). Two spells at their
top level (or a spell and its matching weapon) can <b>fuse</b> into a stronger spell that frees a slot. <b>Bosses</b>
show up during the run; the <b>final boss</b> comes near the end. Bring it down to win the zone and unlock the next one
(every boss of the zone must fall in the same run).<br><br>After 10:00, the <b>Lord Crows</b> invade the map: the
run becomes a race to survive.""",
        """Una partida dura <b>10 minutos</b>. Los monstruos llegan en oleadas cada vez más fuertes; atacas
<b>automáticamente</b>: solo tienes que moverte. Los monstruos derrotados sueltan <b>ámbares de experiencia</b>. En cada
nivel, elige una mejora entre tres (o vuelve a tirar los dados; una vez por partida también puedes <b>Desterrar</b> una
carta para siempre (un arma: todo su tipo) o <b>Saltar</b> la elección). Dos hechizos al máximo (o un hechizo y su arma) pueden <b>fusionarse</b>
en un hechizo más fuerte que libera un hueco. Los <b>jefes</b> aparecen durante la partida; el <b>jefe final</b> llega
hacia el final. Derrótalo para ganar la zona y desbloquear la siguiente (todos los jefes de la zona deben caer en la
misma partida).<br><br>Después de las 10:00, los <b>Maestros Cuerbok</b> invaden el mapa: la partida se convierte en una
carrera por sobrevivir.""")
    T['after'] = t(
        """Les kamas gagnés en partie s'ajoutent à votre bourse. Dépensez-les dans la <b>Boutique</b> (niveaux de
sorts, de caractéristiques, maîtrises d'armes, chapeaux, capes, familiers, boucliers). Le <b>Bestiaire</b> garde la trace
de chaque monstre rencontré, l'<b>Armurerie</b> vos armes, vos caractéristiques, votre classeur de cartes TTG, vos cartes
au trésor, vos reliques et vos âmes d'Archimonstres. Les <b>Succès</b> récompensent les exploits… et les échecs les plus
ridicules.""",
        """The kamas earned in a run go into your purse. Spend them in the <b>Shop</b> (spell levels, characteristics,
weapon masteries, hats, capes, pets, shields). The <b>Bestiary</b> keeps track of every monster met, the <b>Armory</b>
your weapons, characteristics, TTG card binder, treasure maps, relics and Archmonster souls. <b>Achievements</b> reward
great feats… and the most ridiculous failures.""",
        """Los kamas ganados en partida se suman a tu bolsa. Gástalos en la <b>Tienda</b> (niveles de hechizos,
características, maestrías de armas, sombreros, capas, mascotas, escudos). El <b>Bestiario</b> recuerda cada monstruo
encontrado, la <b>Armería</b> tus armas, características, carpeta de cartas TTG, mapas del tesoro, reliquias y almas de
Archimonstruos. Los <b>Logros</b> premian las hazañas… y los fracasos más ridículos.""")
    T['first'] = [
        (t('Ganymède, le guide', 'Ganymede, the guide', 'Ganymed, el guía'), t(
            "Lors de vos premières parties dans les trois premières zones (en Normal), Ganymède vient vous donner quelques "
            "conseils, une seule fois par zone. Le jeu est en pause pendant qu'il parle ; Échap ou « Passer » abrège la scène.",
            "In your first runs on the first three zones (in Normal), Ganymede comes to give you a few tips, once per zone. "
            "The game is paused while he talks; Esc or 'Skip' cuts the scene short.",
            "En tus primeras partidas en las tres primeras zonas (en Normal), Ganymed viene a darte algunos consejos, una sola "
            "vez por zona. El juego se pausa mientras habla; Esc o «Saltar» acorta la escena.")),
        (t("L'aide aux débutants", "Beginners' help", 'Ayuda para principiantes'), t(
            f"Tant que vous n'avez pas gagné l'une des trois premières zones en Normal, elle est plus clémente : les monstres "
            f"y ont moins de vie ({aid}) et frappent deux fois moins fort. Un message dans le chat vous le rappelle.",
            f"Until you win one of the first three zones in Normal, it goes easier on you: its monsters have less life "
            f"({aid}) and hit half as hard. A chat message reminds you.",
            f"Mientras no hayas ganado una de las tres primeras zonas en Normal, será más indulgente: sus monstruos tienen "
            f"menos vida ({aid}) y golpean la mitad de fuerte. Un mensaje en el chat te lo recuerda.")),
        (t('Le mode Difficile', 'Hard mode', 'El modo Difícil'), t(
            f"Il se débloque en gagnant {grobe}. Ce jour-là, Ganymède a quelque chose à vous dire…",
            f"It unlocks when you win {grobe}. That day, Ganymede has something to tell you…",
            f"Se desbloquea al ganar {grobe}. Ese día, Ganymed tiene algo que decirte…")),
    ]
    T['controls'] = [
        (t('Se déplacer', 'Move', 'Moverse'), t('ZQSD / WASD / flèches', 'WASD / ZQSD / arrows', 'WASD / ZQSD / flechas'), t('Stick gauche / croix', 'Left stick / D-pad', 'Stick izquierdo / cruceta'), t('Glisser le doigt', 'Drag your finger', 'Deslizar el dedo')),
        (t('Esquive (ruée)', 'Dodge (dash)', 'Esquiva (embestida)'), t('Espace / E', 'Space / E', 'Espacio / E'), 'RB / RT', t('Double-tap (direction du joystick)', "Double tap (the joystick's way)", 'Doble toque (dirección del joystick)')),
        (t('Sorts de mouvement', 'Movement spells', 'Hechizos de movimiento'), t('A (AZERTY) / Q (QWERTY)', 'Q (QWERTY) / A (AZERTY)', 'Q (QWERTY) / A (AZERTY)'), 'LB / LT', t('Leur icône', 'Their icon', 'Su icono')),
        (t('Pause', 'Pause', 'Pausa'), t('Échap / P', 'Esc / P', 'Esc / P'), 'Start', t('Bouton pause', 'Pause button', 'Botón de pausa')),
        (t('Choisir une amélioration', 'Pick an upgrade', 'Elegir una mejora'), t('Flèches + Entrée / clic', 'Arrows + Enter / click', 'Flechas + Intro / clic'), t('Croix + A', 'D-pad + A', 'Cruceta + A'), t('Toucher la carte', 'Tap the card', 'Tocar la carta')),
        (t('Relancer, Bannir, Passer', 'Reroll, Banish, Skip', 'Volver a tirar, Desterrar, Saltar'), t('Boutons sous les cartes', 'Buttons under the cards', 'Botones bajo las cartas'), t('Croix + A', 'D-pad + A', 'Cruceta + A'), t('Toucher le bouton', 'Tap the button', 'Tocar el botón')),
        (t('Choix auto potion / kamas', 'Auto-pick bread / kamas', 'Elección auto pan / kamas'), 'R', 'Y', t('Case à cocher', 'Checkbox', 'Casilla')),
        (t('Menus : retour', 'Menus: back', 'Menús: volver'), t('Échap', 'Esc', 'Esc'), 'B', '×'),
        (t('Menus : onglets', 'Menus: tabs', 'Menús: pestañas'), 'Tab', 'LB / RB', t('Toucher', 'Tap', 'Tocar')),
        (t('Mode sombre / clair', 'Dark / light mode', 'Modo oscuro / claro'), 'F1', t('R3 (clic du stick droit)', 'R3 (right stick click)', 'R3 (clic del stick derecho)'), t('Bouton du menu principal', 'Main menu button', 'Botón del menú principal')),
        (t('Faire défiler', 'Scroll', 'Desplazar'), t('Molette', 'Mouse wheel', 'Rueda del ratón'), t('Stick droit', 'Right stick', 'Stick derecho'), t('Glisser', 'Drag', 'Deslizar')),
    ]
    T['modes'] = [
        (t('Normale', 'Normal', 'Normal'), t('La partie classique de 10 minutes.', 'The classic 10-minute run.', 'La partida clásica de 10 minutos.')),
        (t('Difficile', 'Hard', 'Difícil'), t(f'Monstres plus résistants, plus rapides et plus méchants, boss bien plus coriaces. Se débloque en gagnant {grobe}. Le crâne sur le bouton ne ment pas.',
                                              f'Tougher, faster and nastier monsters, much sturdier bosses. Unlocked by winning {grobe}. The skull on the button does not lie.',
                                              f'Monstruos más resistentes, rápidos y malvados, jefes mucho más duros. Se desbloquea al ganar {grobe}. La calavera del botón no miente.')),
        (t('Infini', 'Endless', 'Infinito'), t("Pas de fin : les boss reviennent par cycles, de plus en plus forts. Après 10:00, le boss final de la zone revient chaque minute, deux fois plus nombreux à chaque fois. Votre temps entre au classement.",
                                              "No end: bosses come back in cycles, stronger and stronger. After 10:00, the zone's final boss comes back every minute, twice as many each time. Your time goes on the leaderboard.",
                                              "Sin final: los jefes vuelven por ciclos, cada vez más fuertes. Después de las 10:00, el jefe final de la zona vuelve cada minuto, el doble cada vez. Tu tiempo entra en la clasificación.")),
    ]
    T['events'] = [
        (t('ToT et le portail temporel', 'ToT and the time portal', 'ToT y el portal temporal'), t(
            "Vers 2:30, une porte apparaît au centre de la carte : ToT, le Maître du Jeu, vous défie à un mini-jeu. Parfois, la porte est un portail temporel.",
            "Around 2:30, a door appears in the middle of the map: ToT, the Game Master, challenges you to a mini-game. Sometimes the door is a time portal.",
            "Hacia las 2:30, aparece una puerta en el centro del mapa: ToT, el Maestro del Juego, te reta a un minijuego. A veces, la puerta es un portal temporal.")),
        (t('Le Tofuzmo et Jorbak', 'The Tofuzmo and Jorbak', 'El Tofuzmo y Jorbak'), t(
            f"Les autres parties, un Tofu muté s'échappe : rattrapez-le avant qu'il ne file. À partir de la {jfrom}e zone, c'est Jorbak qui vient à sa place : "
            f"il garde ses distances et, si vous l'approchez à moins d'un mètre, sa {L(J.get('spell', {}))} vous repousse. Abattu, il donne un bonus de "
            f"+{round(J.get('buff', 0.15) * 100)} % pour la partie et {round(J.get('tmap', 0.5) * 100)} % de chances de lâcher une carte au trésor.",
            f"In the other runs, a mutant Tofu breaks loose: catch it before it gets away. From zone {jfrom} on, Jorbak comes instead: he keeps his distance "
            f"and, if you get within a metre of him, his {L(J.get('spell', {}))} pushes you back. Beaten, he gives a +{round(J.get('buff', 0.15) * 100)} % bonus "
            f"for the run and a {round(J.get('tmap', 0.5) * 100)} % chance of a treasure map.",
            f"En las demás partidas, un Tofu mutante se escapa: atrápalo antes de que huya. A partir de la zona {jfrom}, viene Jorbak en su lugar: mantiene "
            f"las distancias y, si te acercas a menos de un metro, su {L(J.get('spell', {}))} te empuja. Derrotado, da una bonificación de "
            f"+{round(J.get('buff', 0.15) * 100)} % para la partida y un {round(J.get('tmap', 0.5) * 100)} % de probabilidad de soltar un mapa del tesoro.")),
        (t('Le marchand', 'The merchant', 'El mercader'), t(
            "Vers 5:00, un marchand de skins s'installe quelque part (sur la minicarte). Ses prix sont soldés ; les kamas de la partie servent en premier, puis ceux de votre bourse.",
            "Around 5:00, a skin merchant sets up somewhere (on the minimap). His prices are slashed; the run's kamas are used first, then your purse.",
            "Hacia las 5:00, un mercader de aspectos se instala en algún lugar (en el minimapa). Sus precios están rebajados; primero se usan los kamas de la partida y luego los de tu bolsa.")),
        (t('Les boosters TTG', 'TTG boosters', 'Los sobres TTG'), t(
            "Entre 3:00 et 6:00, un booster de cartes apparaît dans un coin de la carte : chaque paquet officiel contient une carte de son thème, parmi les 464 du jeu de cartes. Rangez-les dans le classeur de l'Armurerie.",
            "Between 3:00 and 6:00, a card booster appears in a corner of the map: each official pack holds a card of its theme, among the 464 of the card game. Keep them in the Armory's binder.",
            "Entre las 3:00 y las 6:00, aparece un sobre de cartas en una esquina del mapa: cada sobre oficial contiene una carta de su tema, entre las 464 del juego de cartas. Guárdalas en la carpeta de la Armería.")),
        (t('Les reliques', 'Relics', 'Las reliquias'), t(
            f"Les boss, les mini-boss (grosse barre de vie) et parfois les élites en lâchent, {C['relicDropMax']} au plus par partie. Une relique dure toute la partie.",
            f"Bosses, mini-bosses (big life bar) and sometimes elites drop them, {C['relicDropMax']} at most per run. A relic lasts the whole run.",
            f"Los jefes, los minijefes (gran barra de vida) y a veces las élites las sueltan, {C['relicDropMax']} como máximo por partida. Una reliquia dura toda la partida.")),
        (t('Les Dofus', 'Dofus', 'Los Dofus'), t(
            "Certains boss lâchent un Dofus : son effet s'applique dans toutes vos parties suivantes.",
            "Some bosses drop a Dofus: its effect applies to all your following runs.",
            "Algunos jefes sueltan un Dofus: su efecto se aplica en todas tus partidas siguientes.")),
        (t('Le Coffre Animé', 'The Living Chest', 'El Cofre Animado'), t(
            "Tuez tous les boss avant 10:00 et un coffre vivant tentera de s'enfuir avec son trésor.",
            "Kill every boss before 10:00 and a living chest will try to run away with its treasure.",
            "Mata a todos los jefes antes de las 10:00 y un cofre vivo intentará huir con su tesoro.")),
        (t('Les cartes au trésor', 'Treasure maps', 'Los mapas del tesoro'), t(
            "Un trésor est caché dans chaque zone. Les cartes viennent de Jorbak : une carte peut mener à n'importe quelle zone, même secrète. Restez sur la croix pour creuser ; l'Armurerie garde vos cartes (Musha y répète ses indications).",
            "A treasure is hidden in every zone. The maps come from Jorbak: a map can lead to any zone, even a secret one. Stand on the cross to dig; the Armory keeps your maps (Musha repeats his directions there).",
            "Hay un tesoro escondido en cada zona. Los mapas vienen de Jorbak: un mapa puede llevar a cualquier zona, incluso secreta. Quédate sobre la cruz para cavar; la Armería guarda tus mapas (Musha repite allí sus indicaciones).")),
        (t('Les Archimonstres', 'Archmonsters', 'Los Archimonstruos'), t(
            "Des versions brillantes et coriaces des monstres. Leur âme rejoint votre collection.",
            "Shiny, tough versions of the monsters. Their soul joins your collection.",
            "Versiones brillantes y duras de los monstruos. Su alma se une a tu colección.")),
        (t('Les élites', 'Elites', 'Las élites'), t(
            "Toutes les 30 secondes, un élite arrive (deux dès 3:00, trois dès 6:00), son nom et sa vie au-dessus de la tête. Leur vie grandit à chaque vague sans jamais dépasser 30 % de celle du boss final ; une vague sur trois laisse un coffre.",
            "Every 30 seconds an elite arrives (two from 3:00, three from 6:00), its name and life over its head. Their life grows with each wave but never passes 30 % of the final boss's; one wave in three leaves a chest.",
            "Cada 30 segundos llega una élite (dos desde las 3:00, tres desde las 6:00), con su nombre y vida sobre la cabeza. Su vida crece en cada oleada sin pasar nunca del 30 % de la del jefe final; una oleada de cada tres deja un cofre.")),
        (t('Les Maîtres Corbacs', 'The Lord Crows', 'Los Maestros Cuerbok'), t(
            f"Après 10:00, ils envahissent la carte. Dès 11:00, chaque minute de survie fait apparaître un {L(M_.get('name', {}))} quelque part sur la carte.",
            f"After 10:00, they invade the map. From 11:00, each minute you survive drops a {L(M_.get('name', {}))} somewhere on the map.",
            f"Después de las 10:00, invaden el mapa. Desde las 11:00, cada minuto que sobrevives aparece un {L(M_.get('name', {}))} en algún lugar del mapa.")),
        (t('Le secret de Dark Vlad', "Dark Vlad's secret", 'El secreto de Dark Vlad'), t(
            "Dark Vlad garde sa clairière… Battez-le en Difficile et le vrai maître des lieux se réveillera.",
            "Dark Vlad guards his glade… Beat him in Hard mode and the true master of the place will wake up.",
            "Dark Vlad guarda su claro… Derrótalo en Difícil y el verdadero amo del lugar despertará.")),
        (t('Événements aléatoires', 'Random events', 'Eventos aleatorios'), t(
            "Pluie de kamas, éclipse, invasion de Bworks, déluge de Tofus… restez sur vos gardes.",
            "Kama rain, eclipse, Bwork invasion, Tofu flood… stay on your guard.",
            "Lluvia de kamas, eclipse, invasión de Bworks, diluvio de Tofus… mantente alerta.")),
    ]
    return T


def cls_page(c):
    sp = [C['spells'][s] for s in c['spells']]
    b = c['base']
    rows = ''.join(f'<div class="spell"><img src="{icon("sp_" + str(s["icon"]), 72)}"><div><b>{E(L(s["name"]))}{" ★" if i == 0 else ""}</b>'
                   f'<p>{E(L(s["desc"]))}</p></div></div>' for i, s in enumerate(sp))
    return f'''<section class="page cls" style="--cc:{c["color"]}">
  <div class="band"><span>{E(L(c["name"]))}</span></div>
  <div class="cls-top"><img class="emb" src="{art(c.get("emblemArt") or ("b" + str(c["breed"])), 300)}">
    <div><div class="stats"><span>❤ {b["hp"]} {t("PV", "HP", "PV")}</span><span>⚔ {round(b["might"] * 100)} %</span><span>➶ {round(b["speed"] * 100)} %</span><span>⛨ {b["armor"]}</span></div>
    <p class="passive"><b>{t("Bonus de classe :", "Class bonus:", "Bonificación de clase:")}</b> {E(L(c["passive"]))}</p></div></div>
  <h3>{t("Sorts", "Spells", "Hechizos")}</h3>{rows}</section>'''


CSS = """
@page { size: 148mm 210mm; margin: 0; }
* { box-sizing: border-box; }
body { margin: 0; font: 9.2pt/1.38 Dofus, Verdana, sans-serif; color: #2b1d0e; }
.page { width: 148mm; height: 210mm; padding: 12mm 11mm 14mm; position: relative; overflow: hidden; page-break-after: always;
  background: #fff; }   /* (white pages: cheap to print) */
.page::after { content: counter(pg); counter-increment: pg; position: absolute; bottom: 6mm; left: 0; right: 0; text-align: center;
  font: 9pt Lilita; color: #8a6a3a; }
body { counter-reset: pg; }
h1, h2, h3, .band span { font-size: 24pt; color: var(--cc); -webkit-text-stroke: .4px #3b1d07; }
h2 { font-size: 20pt; margin: 0 0 4mm; color: #7a2e0a; -webkit-text-stroke: .3px #3b1d07; border-bottom: 1.5mm solid #e8a53a; padding-bottom: 1mm; }
h3 { font-size: 12.5pt; margin: 3.5mm 0 1.5mm; color: #8a3d0c; }
p { margin: 0 0 2mm; }
.cover { background: #fff; color: #3b1d07; text-align: center; padding-top: 8mm; }
.cover::after { content: none; }
.cover .logo { width: 104mm; display: block; margin: 0 auto; }
.cover .sub { font: 13pt Lilita; letter-spacing: 3px; margin-top: 3mm; }
.cover .art { height: 64mm; margin: 5mm auto 2mm; display: flex; justify-content: center; align-items: flex-end; gap: 2mm; }
.cover .art img { height: 40mm; }
.cover .art img.mid { height: 54mm; }
.cover .box { display: inline-block; margin-top: 4mm; padding: 2mm 8mm; border: .8mm solid #7a2e0a; border-radius: 3mm; font: 15pt Lilita; letter-spacing: 2px; color: #7a2e0a; }
.cover .ver { margin-top: 6mm; font-size: 8pt; opacity: .85; }   /* (0.92: under the box, never over it) */
.warn { border: .8mm solid #7a2e0a; border-radius: 3mm; padding: 4mm; }
.warn h3 { margin-top: 0; text-align: center; font-size: 15pt; }
.toc li { font: 11pt Lilita; margin: 1.6mm 0; border-bottom: .3mm dotted #b08a50; list-style: none; }
table { width: 100%; border-collapse: collapse; font-size: 8.3pt; }
th { color: #7a2e0a; font: 9.5pt Lilita; padding: 1.2mm; text-align: left; border-bottom: .6mm solid #7a2e0a; }
td { padding: 1.2mm; border-bottom: .3mm solid #d8c08a; vertical-align: top; }

.band { margin: 0 0 4mm; padding: 0 0 1.5mm 3mm; border-left: 2.2mm solid var(--cc); border-bottom: .6mm solid var(--cc); }
.band span { font-size: 24pt; color: var(--cc); -webkit-text-stroke: .4px #3b1d07; }
.cls-top { display: flex; gap: 4mm; align-items: center; }
.emb { width: 34mm; height: 34mm; object-fit: contain; }
.stats { display: flex; flex-wrap: wrap; gap: 1.5mm; margin-bottom: 2mm; }
.stats span { border: .4mm solid #3b1d07; color: #3b1d07; border-radius: 2mm; padding: .5mm 2mm; font: 9pt Lilita; }
.passive { font-size: 8.8pt; }
.spell { display: flex; gap: 3mm; align-items: flex-start; margin: 0 0 3mm; }
.spell img { width: 11mm; height: 11mm; flex: none; border-radius: 2mm; }
.spell b { font: 10pt Lilita; color: #5a2a08; }
.spell p { margin: .4mm 0 0; font-size: 8.4pt; }
.tightsp .spell { margin-bottom: 2mm; } .tightsp .spell img { width: 10mm; height: 10mm; } .tightsp .spell p { font-size: 8.1pt; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 3mm 4mm; align-items: start; }
.it { display: flex; gap: 2.5mm; align-items: flex-start; font-size: 8pt; }
.it img { width: 10mm; height: 10mm; object-fit: contain; flex: none; }
.it b { font: 9.2pt Lilita; color: #5a2a08; display: block; }
.zone { display: flex; gap: 3mm; margin: 0 0 3mm; align-items: flex-start; }
.zone img { width: 38mm; border-radius: 2mm; border: .6mm solid #8a6a3a; }
.zone b { font: 11pt Lilita; color: #5a2a08; }
.tip { border: .6mm dashed #7a2e0a; border-radius: 3mm; padding: 3mm 4mm; margin-top: 3mm; font-size: 8.5pt; }
.tip b { font-family: Lilita; color: #7a2e0a; }
.hint { font-size: 8pt; color: #6a5030; }
/* 0.46: light decorations from the game's own pictures (the pages stay white, cheap to print) */
.wm { position: absolute; right: 5mm; bottom: 9mm; width: 42mm; height: 42mm; object-fit: contain; opacity: .12; z-index: 0; }
.page > *:not(.wm) { position: relative; z-index: 1; }
.h2i { height: 9mm; width: 9mm; object-fit: contain; vertical-align: -1.8mm; margin-right: 2.2mm; }
.h2i.round { border-radius: 50%; border: .5mm solid #8a6a3a; }
"""


def booklet():
    """the pages of the booklet in LG"""
    TX = texts(); cont = t(' (suite)', ' (cont.)', ' (cont.)')
    pages = []
    logo = uri(Image.open(f'{OUT}/logo.png').convert('RGBA'), 92) if os.path.exists(f'{OUT}/logo.png') else ''   # (the game's own title logo, UI.logo rendered once)
    hero = [art('b8', 420), art('b9', 500), art('b1', 420)]
    pages.append(f'''<section class="page cover"><img class="logo" src="{logo}"><div class="sub" style="margin-top:3mm">{t("MANUEL D'INSTRUCTIONS", "INSTRUCTION MANUAL", "MANUAL DE INSTRUCCIONES")}</div>
      <div class="art"><img src="{hero[0]}"><img class="mid" src="{hero[1]}"><img src="{hero[2]}"></div>
      <div class="box">{t("SURVIVEZ 10 MINUTES", "SURVIVE 10 MINUTES", "SOBREVIVE 10 MINUTOS")}</div>
      <div class="ver">{t("Version bêta", "Beta version", "Versión beta")} {BUILD} · {t("jeu de fans non officiel, univers Dofus © Ankama Games", "unofficial fan game, Dofus universe © Ankama Games", "juego de fans no oficial, universo Dofus © Ankama Games")}</div></section>''')
    toc = t(["L'histoire", 'Les commandes', "Déroulement d'une partie", 'Premiers pas', 'Les classes', 'Les sorts globaux', 'Les armes', 'Les caractéristiques', 'Reliques et Dofus', 'Événements et secrets', 'Les zones', 'Modes de jeu et menus', 'Astuces'],
            ['The story', 'Controls', 'How a run goes', 'First steps', 'The classes', 'Global spells', 'Weapons', 'Characteristics', 'Relics and Dofus', 'Events and secrets', 'The zones', 'Game modes and menus', 'Tips'],
            ['La historia', 'Los controles', 'Cómo es una partida', 'Primeros pasos', 'Las clases', 'Hechizos globales', 'Las armas', 'Las características', 'Reliquias y Dofus', 'Eventos y secretos', 'Las zonas', 'Modos de juego y menús', 'Consejos'])
    pages.append(f'''<section class="page"><div class="warn"><h3>⚠ {t("AVERTISSEMENT", "WARNING", "ADVERTENCIA")} ⚠</h3>
      <p>{t("Retro Survivors est un jeu <b>non officiel</b>, réalisé par des fans, sans lien avec Ankama Games. L'univers, les personnages, les images et les sons de Dofus Retro appartiennent à Ankama Games.",
            "Retro Survivors is an <b>unofficial</b> game made by fans, not affiliated with Ankama Games. The universe, characters, pictures and sounds of Dofus Retro belong to Ankama Games.",
            "Retro Survivors es un juego <b>no oficial</b>, hecho por fans, sin relación con Ankama Games. El universo, los personajes, las imágenes y los sonidos de Dofus Retro pertenecen a Ankama Games.")}</p>
      <p>{t(f"Ce manuel est généré à partir des données du jeu (version {BUILD}) : les valeurs peuvent évoluer d'une version à l'autre.",
            f"This manual is generated from the game's data (version {BUILD}): values may change from one version to the next.",
            f"Este manual se genera a partir de los datos del juego (versión {BUILD}): los valores pueden cambiar de una versión a otra.")}</p>
      <p>{t("<b>Santé :</b> jouez dans une pièce bien éclairée, faites une pause de 10 à 15 minutes toutes les heures, et arrêtez si vous ressentez une fatigue des yeux ou des mains. Les Tofus, eux, ne font jamais de pause.",
            "<b>Health:</b> play in a well-lit room, take a 10 to 15 minute break every hour, and stop if your eyes or hands feel tired. The Tofus, for their part, never take a break.",
            "<b>Salud:</b> juega en una habitación bien iluminada, haz una pausa de 10 a 15 minutos cada hora y para si notas cansancio en los ojos o las manos. Los Tofus, en cambio, nunca descansan.")}</p></div>
      {h2(t("Sommaire", "Contents", "Índice"), None, "margin-top:8mm")}<ul class="toc">{"".join(f"<li>{E(x)}</li>" for x in toc)}</ul></section>''')
    th = t(['Action', 'Clavier / souris', 'Manette', 'Mobile'], ['Action', 'Keyboard / mouse', 'Controller', 'Mobile'], ['Acción', 'Teclado / ratón', 'Mando', 'Móvil'])
    pages.append(f'''<section class="page">{h2(toc[0], 'dofus_hd_' + str(next(d['icon'] for d in C['dofus'] if d['id'] == 'emeraude')))}<p>{TX["story"]}</p>
      {h2(toc[1], None, "margin-top:1.5mm")}<table style="font-size:7pt"><tr>{"".join(f"<th>{x}</th>" for x in th)}</tr>
      {''.join(f"<tr><td><b>{E(a)}</b></td><td>{E(b)}</td><td>{E(c)}</td><td>{E(d)}</td></tr>" for a, b, c, d in TX['controls'])}</table>
      <p class="hint" style="margin-top:2mm">{t("Le clavier AZERTY et QWERTY sont reconnus. Les touches se consultent dans le menu « Commandes ».", "AZERTY and QWERTY keyboards are both recognised. The keys are listed in the 'Controls' menu.", "Se reconocen los teclados AZERTY y QWERTY. Las teclas se consultan en el menú «Controles».")}</p></section>''')
    scr = t([('Haut', "Barre d'expérience et niveau, chronomètre, barres de vie des boss."), ('Haut gauche', 'Vos sorts et votre arme, avec leur niveau ; dessous, vos caractéristiques.'),
             ('Haut droite', 'Monstres vaincus et kamas de la partie.'), ('Côtés', 'À gauche vos reliques, à droite vos Dofus.'), ('Bas', "Votre cœur de vie, l'esquive (rechargement), la minicarte et le fil des messages.")],
            [('Top', 'Experience bar and level, timer, bosses\' life bars.'), ('Top left', 'Your spells and weapon with their level; below, your characteristics.'),
             ('Top right', "Monsters defeated and the run's kamas."), ('Sides', 'Your relics on the left, your Dofus on the right.'), ('Bottom', 'Your life heart, the dodge (cooldown), the minimap and the message feed.')],
            [('Arriba', 'Barra de experiencia y nivel, cronómetro, barras de vida de los jefes.'), ('Arriba izquierda', 'Tus hechizos y tu arma con su nivel; debajo, tus características.'),
             ('Arriba derecha', 'Monstruos derrotados y kamas de la partida.'), ('Lados', 'A la izquierda tus reliquias, a la derecha tus Dofus.'), ('Abajo', 'Tu corazón de vida, la esquiva (recarga), el minimapa y el hilo de mensajes.')])
    pages.append(f'''<section class="page">{h2(toc[2], C['ambers'][-1])}<p>{TX["goal"]}</p>
      <h3>{t("L'écran de jeu", "The game screen", "La pantalla de juego")}</h3><table>{"".join(f"<tr><td><b>{a}</b></td><td>{b}</td></tr>" for a, b in scr)}</table>
      <h3>{t("Après la partie", "After the run", "Después de la partida")}</h3><p>{TX["after"]}</p></section>''')   # (0.95: no tip box: the three languages fit)
    gy = (C.get('gany') or {}).get('sprite', '')
    pages.append(f'''<section class="page">{h2(toc[3], 'IconWisdom')}{"".join(f"<h3>{E(a)}</h3><p>{E(b)}</p>" for a, b in TX['first'])}
      <div class="tip"><b>{t("Astuce :", "Tip:", "Consejo:")}</b> {t("Les options proposent trois niveaux d'effets visuels (complets, réduits, minimaux) et trois distances de caméra. Sur un PC modeste ou un téléphone, essayez 720p et des effets réduits.",
          "The options offer three levels of visual effects (full, reduced, minimal) and three camera distances. On a modest PC or a phone, try 720p and reduced effects.",
          "Las opciones ofrecen tres niveles de efectos visuales (completos, reducidos, mínimos) y tres distancias de cámara. En un PC modesto o un teléfono, prueba 720p y efectos reducidos.")}</div></section>''')
    for c in C['classes']: pages.append(cls_page(c))
    gl = ''.join(f'<div class="spell"><img src="{icon("sp_" + str(C["spells"][g["id"]]["icon"]), 72)}"><div><b>{E(L(C["spells"][g["id"]]["name"]))}</b><p>{E(L(C["spells"][g["id"]]["desc"]))}</p></div></div>' for g in C.get('globalSpells', []))
    pages.append(f'<section class="page tightsp">{h2(toc[5], "sp_g_kokoko")}<p>{t("Toutes les classes peuvent les recevoir au fil des niveaux (bordure argentée).", "Every class can get them while levelling up (silver border).", "Todas las clases pueden recibirlos al subir de nivel (borde plateado).")}</p>{gl}</section>')
    wp = ''.join(f'<div class="it"><img src="{icon(w["icon"], 72)}"><div><b>{E(L(w["name"]))}</b>{E(L(w["desc"]))}</div></div>' for w in C['weapons'])
    pages.append(f'''<section class="page">{h2(toc[6], 'it_6_17')}<p>{t("Une seule arme par partie, parmi 40 (5 par type : 3 armes et 2 <b>Soifs de Sang</b> qui volent de la vie). Chacune a son effet. Montée au maximum, elle peut <b>fusionner</b> avec une caractéristique. Les <b>maîtrises</b> achetées en boutique (+5 % par niveau) s'appliquent à toutes les armes de leur type.",
        "One weapon per run, out of 40 (5 per type: 3 weapons and 2 <b>Bloodthirsts</b> that steal life). Each has its own effect. At its top level it can <b>fuse</b> with a characteristic. <b>Masteries</b> bought in the shop (+5 % per level) apply to every weapon of their type.",
        "Una sola arma por partida, entre 40 (5 por tipo: 3 armas y 2 <b>Sed de Sangre</b> que roban vida). Cada una tiene su efecto. Al máximo, puede <b>fusionarse</b> con una característica. Las <b>maestrías</b> compradas en la tienda (+5 % por nivel) se aplican a todas las armas de su tipo.")}</p><div class="grid">{wp}</div></section>''')
    SF = C.get('spellFusions', [])
    def sf_name(k, kind, i):
        if kind == 'weapon' and i: return L(next(w for w in C['weapons'] if w['id'] == k)['name'])
        return L(C['spells'][k]['name'])
    for i in range(0, len(SF), 7):
        rows = ''.join(f'<div class="spell"><img src="{icon("sp_" + str(C["spells"][f["id"]]["icon"]), 72)}"><div><b>{E(L(C["spells"][f["id"]]["name"]))}</b> '
                       f'<small>({E(L(next(c for c in C["classes"] if c["id"] == f["cls"])["name"]) if f["cls"] else t("toutes les classes", "every class", "todas las clases"))} : {E(sf_name(f["src"][0], f["kind"], 0))} + {E(sf_name(f["src"][1], f["kind"], 1))})</small>'
                       f'<p>{E(L(C["spells"][f["id"]]["desc"]))}</p></div></div>' for f in SF[i:i + 7])
        hf = t('Les fusions de sorts', 'Spell fusions', 'Fusiones de hechizos')
        head = (h2(hf, 'it_6_72') + '<p>' + t("Trois par classe : deux de ses sorts, un sort et son arme de prédilection, un sort et un sort global ; et deux pour toutes les classes, de deux sorts globaux. Montez les deux au maximum : la fusion apparaît dans les choix, remplace ses sorts (l'arme reste) et libère leur place.",
                                             "Three per class: two of its spells, a spell and its favourite weapon, a spell and a global spell; and two for every class, of two global spells. Bring both to their top level: the fusion shows up in the choices, replaces its spells (the weapon stays) and frees their slot.",
                                             "Tres por clase: dos de sus hechizos, un hechizo y su arma predilecta, un hechizo y un hechizo global; y dos para todas las clases, de dos hechizos globales. Sube ambos al máximo: la fusión aparece entre las opciones, sustituye a sus hechizos (el arma se queda) y libera su hueco.") + '</p>') if i == 0 else h2(hf + cont, 'it_6_72')
        pages.append(f'<section class="page">{head}{rows}</section>')
    # 0.60: the 40 weapons, type by type (3 weapons + 2 Soifs de Sang each)
    W40 = [w for tp in C['weapons'] for w in C.get('uniqueWeapons', []) if w.get('of') == tp['id']]
    blood = t('Soif de Sang', 'Bloodthirst', 'Sed de Sangre')
    for i in range(0, len(W40), 10):
        rows = ''.join(f'<div class="it"><img src="{icon(w["icon"], 72)}"><div><b>{E(L(w["name"]))}{f" <span class=hint>({blood})</span>" if w.get("blood") else ""}</b>{E(L(w.get("desc", {})))[:170]}</div></div>' for w in W40[i:i + 10])
        intro = '' if i else '<p>' + t('Cinq par type : trois armes et deux Soifs de Sang (elles volent un peu de vie à chaque coup, mais frappent un peu moins fort).', 'Five per type: three weapons and two Bloodthirsts (they steal a little life with each blow, but hit a little softer).', 'Cinco por tipo: tres armas y dos Sed de Sangre (roban un poco de vida en cada golpe, pero pegan algo menos fuerte).') + '</p>'
        pages.append(f'<section class="page">{h2(t("Les 40 armes", "The 40 weapons", "Las 40 armas") + (cont if i else ""), "it_7_10")}{intro}<div class="grid">{rows}</div></section>')
    PS = C['passives']
    for i in range(0, len(PS), 12):
        ps = ''.join(f'<div class="it"><img src="{icon(p["icon"], 72)}"><div><b>{E(L(p["name"]))} <span class="hint">({t("niv. max", "max lv", "niv. máx")} {p["max"]})</span></b>{E(L(p["desc"]))}</div></div>' for p in PS[i:i + 12])
        intro = '' if i else '<p>' + t("Proposées à chaque niveau comme les sorts ; elles améliorent tous vos sorts concernés (voir l'Armurerie).", 'Offered at each level like the spells; they improve all your spells concerned (see the Armory).', 'Se ofrecen en cada nivel como los hechizos; mejoran todos tus hechizos afectados (ver la Armería).') + '</p>'
        pages.append(f'<section class="page">{h2(toc[7] + (cont if i else ""), "Icon_c_vita")}{intro}<div class="grid">{ps}</div></section>')
    df = ''.join(f'<div class="it"><img src="{icon("dofus_hd_" + str(d["icon"]), 96) or icon("it_23_" + str(d["icon"]), 72)}"><div><b style="color:{d["color"]}">{E(L(d["name"]))}</b>{E(L(d["desc"]))}</div></div>' for d in C['dofus'])
    RL = C['relics']; hr = t('Reliques', 'Relics', 'Reliquias')
    for i in range(0, len(RL), 10):   # (0.60: 20 relics with their real numbers: two pages)
        rl = ''.join(f'<div class="it"><img src="{icon(r["icon"], 72)}"><div><b>{E(L(r["name"]))}</b>{E(L(r["desc"]))}</div></div>' for r in RL[i:i + 10])
        intro = '' if i else '<p>' + t("Lâchées par les boss, les mini-boss et parfois les élites ; leur effet, inspiré de l'objet de Dofus Retro, dure jusqu'à la fin de la partie.", "Dropped by bosses, mini-bosses and sometimes elites; their effect, inspired by the Dofus Retro item, lasts until the end of the run.", "Las sueltan los jefes, los minijefes y a veces las élites; su efecto, inspirado en el objeto de Dofus Retro, dura hasta el final de la partida.") + '</p>'
        pages.append(f'<section class="page">{h2(hr + (cont if i else ""), "it_9_47")}{intro}<div class="grid">{rl}</div></section>')
    pages.append(f'<section class="page">{h2(t("Les Dofus", "Dofus", "Los Dofus"), "dofus_hd_3")}<p>{t("Les œufs de dragon : rares, convoités, et leur effet reste acquis pour toutes vos parties.", "Dragon eggs: rare, coveted, and their effect stays with you for all your runs.", "Huevos de dragón: raros, codiciados, y su efecto se queda para todas tus partidas.")}</p><div class="grid">{df}</div></section>')
    EV = TX['events']
    for i in range(0, len(EV), 5):
        ev = ''.join(f'<h3>{E(a)}</h3><p>{E(b)}</p>' for a, b in EV[i:i + 5])
        pages.append(f'<section class="page">{h2(toc[9] + (cont if i else ""), "it_24_6")}{ev}</section>')
    zs = []
    for m in [m for m in C['maps'] if not m.get('hidden')]:
        bosses = ', '.join(L(C['bosses'][b[1]]['name']) for b in m.get('bosses', []) if b[1] in C['bosses'])
        zs.append(f'<div class="zone"><img src="{mini(m["world"])}"><div><b>{E(L(m["name"]))}</b><br><span class="hint">{t("Niveaux", "Levels", "Niveles")} {E(str(m.get("lvl", "")))}</span><p>{t("Boss", "Bosses", "Jefes")} : {E(bosses)}</p></div></div>')
    for i in range(0, len(zs), 5):
        tail = '<p class=hint>' + t('Et quelques zones secrètes… à vous de les trouver.', 'And a few secret zones… yours to find.', 'Y algunas zonas secretas… te toca encontrarlas.') + '</p>' if i + 5 >= len(zs) else ''
        pages.append(f'<section class="page">{h2(toc[10] + (cont if i else ""), "zone")}{"".join(zs[i:i + 5])}{tail}</section>')
    md = ''.join(f'<h3>{E(a)}</h3><p>{E(b)}</p>' for a, b in TX['modes'])
    menus = t([('Boutique', 'Sorts, caractéristiques, maîtrises, sorts globaux, chapeaux, capes, familiers et boucliers.'), ('Bestiaire', "Chaque monstre et boss rencontré, ses attaques et ce qu'il lâche."),
               ('Armurerie', 'Armes (dont les armes uniques et vampiriques), caractéristiques, classeur TTG, cartes au trésor, reliques, âmes.'), ('Succès', f'{len(C["achievements"])} succès, chacun avec son objet. Tous les obtenir réserve une surprise…'),
               ('Statistiques', 'Vos records, par classe et par zone.'), ('Options', 'Langue (7), volumes, style de musique, qualité graphique (720p à 4K), effets visuels (complets, réduits, minimaux), caméra (éloignée, normale, proche), chiffres de dégâts, tremblements, chat.')],
              [('Shop', 'Spells, characteristics, masteries, global spells, hats, capes, pets and shields.'), ('Bestiary', 'Every monster and boss met, its attacks and what it drops.'),
               ('Armory', 'Weapons (unique and vampiric ones included), characteristics, TTG binder, treasure maps, relics, souls.'), ('Achievements', f'{len(C["achievements"])} achievements, each with its item. Getting them all holds a surprise…'),
               ('Statistics', 'Your records, per class and per zone.'), ('Options', 'Language (7), volumes, music style, graphics quality (720p to 4K), visual effects (full, reduced, minimal), camera (far, normal, close), damage numbers, screen shake, chat.')],
              [('Tienda', 'Hechizos, características, maestrías, hechizos globales, sombreros, capas, mascotas y escudos.'), ('Bestiario', 'Cada monstruo y jefe encontrado, sus ataques y lo que suelta.'),
               ('Armería', 'Armas (incluidas las únicas y vampíricas), características, carpeta TTG, mapas del tesoro, reliquias, almas.'), ('Logros', f'{len(C["achievements"])} logros, cada uno con su objeto. Conseguirlos todos guarda una sorpresa…'),
               ('Estadísticas', 'Tus récords, por clase y por zona.'), ('Opciones', 'Idioma (7), volúmenes, estilo de música, calidad gráfica (720p a 4K), efectos visuales (completos, reducidos, mínimos), cámara (lejana, normal, cercana), cifras de daño, temblores, chat.')])
    pages.append(f'''<section class="page">{h2(t("Modes de jeu", "Game modes", "Modos de juego"), "it_47_26")}{md}{h2(t("Les menus", "The menus", "Los menús"), None, "margin-top:5mm")}
      <table>{"".join(f"<tr><td><b>{a}</b></td><td>{E(b)}</td></tr>" for a, b in menus)}</table></section>''')
    tips = C['tips'][LG]
    for i in range(0, len(tips), 9):   # (0.45: every tip, nine per page — they are longer now)
        pages.append(f'<section class="page">{h2(toc[12] + (cont if i else ""), "IconWisdom")}{"".join(f"<p>• {E(x)}</p>" for x in tips[i:i + 9])}</section>')
    pages.extend(numbers(cont))
    pages.append(f'''<section class="page">{h2(t("Crédits", "Credits", "Créditos"), 'dofus_hd_' + str(next(d['icon'] for d in C['dofus'] if d['id'] == 'vulbis')))}<p>{t("Retro Survivors — jeu de fans non officiel.", "Retro Survivors — an unofficial fan game.", "Retro Survivors — juego de fans no oficial.")}</p>
      <p>{t("Univers, personnages, images, musiques et sons :", "Universe, characters, pictures, music and sounds:", "Universo, personajes, imágenes, músicas y sonidos:")} <b>Dofus Retro © Ankama Games</b>.</p>
      <p>{t(f"Version du jeu : bêta {BUILD}. Ce manuel est régénéré à chaque version à partir des données du jeu.", f"Game version: beta {BUILD}. This manual is generated again for each version from the game's data.", f"Versión del juego: beta {BUILD}. Este manual se regenera en cada versión a partir de los datos del juego.")}</p>
      <div class="tip"><b>{t("Merci d'avoir joué !", "Thanks for playing!", "¡Gracias por jugar!")}</b> {t("Et si un Tofu vous a vaincu, on ne le dira à personne.", "And if a Tofu beat you, we won't tell anyone.", "Y si un Tofu te ha vencido, no se lo diremos a nadie.")}</div></section>''')
    return pages


def numbers(cont):
    """the exact numbers (0.40): every rate read from the game's data"""
    sep = ',' if LG != 'en' else '.'
    pc = lambda v, d=1: (f'{v * 100:.{d}f}'.rstrip('0').rstrip('.') + ' %').replace('.', sep)
    nm = lambda v: (f'{v:.2f}'.rstrip('0').rstrip('.')).replace('.', sep)   # (5.0 s -> 5 s, 0.4 -> 0,4)
    R_ = C['run']; rw = C['ttg']['rw']; rws = sum(rw); A = C.get('archiCfg', {}); H_ = C.get('hard', {}); I_ = C.get('infinite', {}); M_ = C.get('manuel', {}); J = C.get('jorbak', {}); MB = list((M_.get('boss') or {0: 0}).values())   # (0.98: every boss's chance)
    tm = list(C['tmap'].get('prize', {}).values()) or [C['tmap']['kamas']]
    GB = C['gany']['bless']; gt = f"{C['gladia']['t'] // 60}:{C['gladia']['t'] % 60:02d}"
    def ttg_odds():   # (0.98.3: one of the packs, each as often: a rarity among those it holds, by C.ttg.rw; a rarity's pack gives its own)
        fams = {c['fam'] for c in C['ttg']['cards']}; n = len(fams) + 4; P = [1 / n] * 4
        for f in fams:
            has = {c['r'] for c in C['ttg']['cards'] if c['fam'] == f}; s_ = sum(rw[r] for r in has)
            for r in has: P[r] += rw[r] / s_ / n
        return P
    per = t('par monstre', 'per monster', 'por monstruo'); luck = t('(× Chance)', '(× Luck)', '(× Suerte)')
    cb, ob, ev, md = t('Combat', 'Combat', 'Combate'), t('Objets', 'Items', 'Objetos'), t('Événements', 'Events', 'Eventos'), t('Modes', 'Modes', 'Modos')
    dofus_from = lambda b: 'ToT' if b == 'tot' else t('tout boss final', 'any final boss', 'cualquier jefe final') if b == 'any_final' else L(C['bosses'][b]['name']) if b in C['bosses'] else b
    rows = [
        (cb, t('Coup critique de base', 'Base critical hit', 'Golpe crítico base'), f"{pc(0.05)} ({t('dégâts × 2', 'damage × 2', 'daño × 2')})"),
        (cb, t('Esquive (ruée)', 'Dodge (dash)', 'Esquiva (embestida)'), t(f"recharge {nm(C['dodge']['cd'])} s, invulnérable {nm(C['dodge']['inv'])} s", f"cooldown {nm(C['dodge']['cd'])} s, invulnerable {nm(C['dodge']['inv'])} s", f"recarga {nm(C['dodge']['cd'])} s, invulnerable {nm(C['dodge']['inv'])} s")),
        (cb, t('Caractéristique Esquive', 'Evasion characteristic', 'Característica Esquiva'), t(f"+{pc([p for p in C['passives'] if p['id'] == 'esquive'][0]['per'])} d'esquive totale par niveau", f"+{pc([p for p in C['passives'] if p['id'] == 'esquive'][0]['per'])} total evasion per level", f"+{pc([p for p in C['passives'] if p['id'] == 'esquive'][0]['per'])} de esquiva total por nivel")),
        (cb, t('Bonds et ruées des sorts', 'Spell leaps and dashes', 'Saltos y embestidas de hechizos'), t('invulnérable pendant le mouvement et 0,2 s après', 'invulnerable during the move and 0.2 s after', 'invulnerable durante el movimiento y 0,2 s después')),
        (cb, t('Renvoi de dommages', 'Damage reflection', 'Reenvío de daño'), t('au plus 30 par niveau (150 au niveau 5) et la moitié de la vie du monstre', 'at most 30 per level (150 at level 5) and half the monster\'s life', 'como máximo 30 por nivel (150 en el nivel 5) y la mitad de la vida del monstruo')),
        (cb, t('Aide aux débutants', "Beginners' help", 'Ayuda para principiantes'), ', '.join(f"{zname(z)} {t('PV', 'HP', 'PV')} × {nm(a['hp'])}" for z, a in C.get('beginnerAid', {}).items()) + t(', coups × 0,5', ', blows × 0.5', ', golpes × 0,5')),
        (ob, t('Kamas sur un monstre', 'Kamas on a monster', 'Kamas de un monstruo'), pc(R_['kamaDrop'], 2) + ' ' + luck),
        (ob, t('Pain', 'Bread', 'Pan'), f"{R_['breadRate'] * 100:.3f} %".replace('.', sep) + f" {per} {luck}" + t(f" ; × {GB['bread']} avec la bénédiction de Ganymède ({GB['maps']} premières cartes en Normale)", f"; × {GB['bread']} with Ganymede's blessing (first {GB['maps']} maps in Normal)", f"; × {GB['bread']} con la bendición de Ganimedes ({GB['maps']} primeros mapas en Normal)")),
        (ob, t('Potion de Rappel / Fée / Sablier', 'Recall Potion / Fairy / Hourglass', 'Poción de Recuerdo / Hada / Reloj de arena'), f"0{sep}12 % / 0{sep}08 % / 0{sep}09 % {per} {luck}"),
        *[(ob, L(d['name']), pc(d['rate'], 3) + f' {per} {luck}') for d in C['drops'].values()],
        (ob, L(M_.get('name', {})), t(f"{pc(M_['rate'], 3)} {per}, soit environ 1 partie complète sur 10 ; chaque boss : {pc(min(MB), 1)} à {pc(max(MB), 1)} selon sa puissance ; Maîtres Corbacs : un par minute dès 11:00 ; boss du mode Infini : {pc(I_.get('manuelP', 0.05), 1)} à 10:00, +{pc(I_.get('manuelStep', 0.025), 1)} par minute ensuite",
                                      f"{pc(M_['rate'], 3)} {per}, about 1 whole run in 10; every boss: {pc(min(MB), 1)} to {pc(max(MB), 1)} by its power; Lord Crows: one a minute from 11:00; Endless bosses: {pc(I_.get('manuelP', 0.05), 1)} at 10:00, +{pc(I_.get('manuelStep', 0.025), 1)} every minute after",
                                      f"{pc(M_['rate'], 3)} {per}, cerca de 1 partida completa de cada 10; cada jefe: {pc(min(MB), 1)} a {pc(max(MB), 1)} según su poder; Maestros Cuerbok: uno por minuto desde las 11:00; jefes del modo Infinito: {pc(I_.get('manuelP', 0.05), 1)} a las 10:00, +{pc(I_.get('manuelStep', 0.025), 1)} por minuto después")),
        (ob, t('Carte au trésor', 'Treasure map', 'Mapa del tesoro'), t(f"Jorbak : {pc(J.get('tmap', 0.25))} ; trésor : {min(tm)} à {max(tm)} kamas", f"Jorbak: {pc(J.get('tmap', 0.25))}; treasure: {min(tm)} to {max(tm)} kamas", f"Jorbak: {pc(J.get('tmap', 0.25))}; tesoro: {min(tm)} a {max(tm)} kamas")),
        (ob, t('Coffre du trésor', "The treasure's chest", 'Cofre del tesoro'), t(f"en plus des kamas, {pc(C['tmap'].get('bonus', 0))} : un Dofus pas encore trouvé ({pc(C['tmap'].get('bonusDofus', 0.5))}) ou un bouclier pas encore possédé",
                                                                               f"besides the kamas, {pc(C['tmap'].get('bonus', 0))}: a Dofus not found yet ({pc(C['tmap'].get('bonusDofus', 0.5))}) or a shield not owned yet",
                                                                               f"además de los kamas, {pc(C['tmap'].get('bonus', 0))}: un Dofus aún no encontrado ({pc(C['tmap'].get('bonusDofus', 0.5))}) o un escudo aún no conseguido")) if C['tmap'].get('bonus') else None,
        (ob, L(C['houx']['name']), pc(C['houx']['rate'], 3) + f' {per} {luck} — ' + t('un relancement de plus', 'one more reroll', 'una tirada más')) if C.get('houx') else None,
        (ob, L(C['gladia']['name']), t(f"à {gt}, un par partie, n'importe où sur la carte : une caractéristique en plus des 5", f"at {gt}, one per run, anywhere on the map: a characteristic on top of the 5", f"a las {gt}, una por partida, en cualquier lugar del mapa: una característica además de las 5")),
        (t('Reliques', 'Relics', 'Reliquias'), t('Boss', 'Boss', 'Jefe'), t(f"{pc(C.get('relicRate', 0.4))} {luck} (boss final : 100 %), {C['relicDropMax']} au plus par partie", f"{pc(C.get('relicRate', 0.4))} {luck} (final boss: 100 %), {C['relicDropMax']} at most per run", f"{pc(C.get('relicRate', 0.4))} {luck} (jefe final: 100 %), {C['relicDropMax']} como máximo por partida")),
        (t('Reliques', 'Relics', 'Reliquias'), t('Mini-boss (Tofuzmo, Jorbak, Coffre Animé)', 'Mini-bosses (Tofuzmo, Jorbak, Living Chest)', 'Minijefes (Tofuzmo, Jorbak, Cofre Animado)'), pc(C.get('relicMini', 0.5)) + ' ' + luck),
        (t('Reliques', 'Relics', 'Reliquias'), t('Élite', 'Elite', 'Élite'), pc(C['relicElite']) + ' ' + luck) if C.get('relicElite') else None,
        *[('Dofus', L(d['name']), f"{pc(d['rate'])} {luck} — " + ', '.join(dofus_from(b) for b in d['from'])) for d in C['dofus']],
        (ev, t('Porte de ToT', "ToT's door", 'Puerta de ToT'), t(f"à {R_['doorT'] // 60}:{R_['doorT'] % 60:02d} ; portail temporel : {pc(C['portal']['chance'])} des parties, sinon le Tofuzmo ({C['mutant']['hp']} PV) ou Jorbak ({J.get('hp', 3000)} PV, zone {J.get('from', 10) + 1} et après)",
                                                               f"at {R_['doorT'] // 60}:{R_['doorT'] % 60:02d}; time portal: {pc(C['portal']['chance'])} of runs, otherwise the Tofuzmo ({C['mutant']['hp']} HP) or Jorbak ({J.get('hp', 3000)} HP, zone {J.get('from', 10) + 1} and after)",
                                                               f"a las {R_['doorT'] // 60}:{R_['doorT'] % 60:02d}; portal temporal: {pc(C['portal']['chance'])} de las partidas, si no el Tofuzmo ({C['mutant']['hp']} PV) o Jorbak ({J.get('hp', 3000)} PV, zona {J.get('from', 10) + 1} y siguientes)")),
        (ev, t('Marchand de skins', 'Skin merchant', 'Mercader de aspectos'), t(f"à {C['merchant']['t'] // 60}:00, {C['merchant']['n']} skins à -25 / -75 %", f"at {C['merchant']['t'] // 60}:00, {C['merchant']['n']} skins at -25 / -75 %", f"a las {C['merchant']['t'] // 60}:00, {C['merchant']['n']} aspectos a -25 / -75 %")),
        (ev, t('Booster TTG', 'TTG booster', 'Sobre TTG'), t('entre 3:00 et 6:00, dans un coin de la carte', 'between 3:00 and 6:00, in a corner of the map', 'entre las 3:00 y las 6:00, en una esquina del mapa')),
        (ev, t('Cartes TTG (rareté)', 'TTG cards (rarity)', 'Cartas TTG (rareza)'), ' / '.join(pc(x) for x in ttg_odds()) + t(' (commune → légendaire)', ' (common → legendary)', ' (común → legendaria)')),
        (ev, t('Archimonstre', 'Archmonster', 'Archimonstruo'), t(f"{pc(A.get('rate', 0), 2)} par monstre ; PV × {nm(A.get('hp'))}, dégâts × {nm(A.get('dmg'))}", f"{pc(A.get('rate', 0), 2)} per monster; HP × {nm(A.get('hp'))}, damage × {nm(A.get('dmg'))}", f"{pc(A.get('rate', 0), 2)} por monstruo; PV × {nm(A.get('hp'))}, daño × {nm(A.get('dmg'))}")),
        (ev, t('Arme unique', 'Unique weapon', 'Arma única'), pc(C.get('uniqueRate', 0.15)) + t(" à la place d'une arme de son type", ' instead of a weapon of its type', ' en lugar de un arma de su tipo')),
        (ev, t('Arme vampirique', 'Vampiric weapon', 'Arma vampírica'), pc(C.get('bloodRate', 0.1)) + t(" à la place d'une arme de son type", ' instead of a weapon of its type', ' en lugar de un arma de su tipo')),
        (ev, t('Coffre Animé', 'Living Chest', 'Cofre Animado'), t('tous les boss tués avant 10:00', 'every boss killed before 10:00', 'todos los jefes muertos antes de las 10:00')),
        (md, t('Difficile', 'Hard', 'Difícil'), t(f"vie des monstres +{pc(H_.get('hpMin', 0))}, dégâts des monstres × {nm(H_.get('dmg'))}, vitesse × {nm(H_.get('speed'))}, attaques {pc(H_.get('atk', 1) - 1)} plus rapides, vie des boss +{pc(H_.get('bossHp') - 1)}, kamas au sol × {nm(H_.get('kamaDrop', 1))}",
                                                  f"monster life +{pc(H_.get('hpMin', 0))}, monster damage × {nm(H_.get('dmg'))}, speed × {nm(H_.get('speed'))}, attacks {pc(H_.get('atk', 1) - 1)} faster, boss life +{pc(H_.get('bossHp') - 1)}, kamas on the ground × {nm(H_.get('kamaDrop', 1))}",
                                                  f"vida de los monstruos +{pc(H_.get('hpMin', 0))}, daño de los monstruos × {nm(H_.get('dmg'))}, velocidad × {nm(H_.get('speed'))}, ataques {pc(H_.get('atk', 1) - 1)} más rápidos, vida de los jefes +{pc(H_.get('bossHp') - 1)}, kamas en el suelo × {nm(H_.get('kamaDrop', 1))}")),
        (md, t('Infini', 'Endless', 'Infinito'), t(f"cycles de {I_.get('cycle', 480) // 60} min ; à {I_.get('bossT', 600) // 60}:00 le boss final ×2 chaque minute", f"{I_.get('cycle', 480) // 60}-minute cycles; at {I_.get('bossT', 600) // 60}:00 the final boss ×2 every minute", f"ciclos de {I_.get('cycle', 480) // 60} min; a las {I_.get('bossT', 600) // 60}:00 el jefe final ×2 cada minuto")),
        (t('Secrets', 'Secrets', 'Secretos'), '???', t("Certaines trappes cachent plus qu'un courant d'air…", 'Some trapdoors hide more than a draught…', 'Algunas trampillas esconden algo más que una corriente de aire…')),
    ]
    rows = [r for r in rows if r]   # (0.97: the rows of a system the game has not)
    out, th = [], t(['Domaine', 'Quoi', 'Valeur'], ['Area', 'What', 'Value'], ['Ámbito', 'Qué', 'Valor'])
    for i in range(0, len(rows), 13):
        tb = ''.join(f'<tr><td>{E(a)}</td><td><b>{E(b)}</b></td><td>{E(c)}</td></tr>' for a, b, c in rows[i:i + 13])
        out.append(f'<section class="page">{h2(t("Les chiffres exacts", "The exact numbers", "Las cifras exactas") + (cont if i else ""), "Icon_duree")}<table><tr>{"".join(f"<th>{x}</th>" for x in th)}</tr>{tb}</table></section>')
    return out


def main():
    global LG
    langs = [a for a in _sys.argv[1:] if a in LANGS] or list(LANGS)
    css = ''.join(f'@font-face {{ font-family: {n}; src: url({font(f)}); }}' + chr(10) for n, f in (('Lilita', 'lilita.woff2'), ('DofusBold', 'dofus-bold.woff2'), ('Dofus', 'dofus-regular.woff2'))) + CSS
    # 0.46: decorations from the game's assets on every page but the cover: a bestiary monster as a pale watermark
    # (a different one per page). Re-run on every release.
    WM, seen = [], set()
    for m in C['monsters'].values():
        k = 'a' + str(m.get('sprite', '')).split('_')[0]
        if k in S['art']['f'] and k not in seen: seen.add(k); WM.append(k)
    WM = WM[::max(1, len(WM) // 40)]
    os.makedirs(OUT, exist_ok=True)
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        for LG in langs:
            pages = [pg_ if 'class="page cover"' in pg_ else pg_.replace('<section class="page">', f'<section class="page"><img class="wm" src="{art(WM[n % len(WM)], 260)}">', 1)
                     for n, pg_ in enumerate(booklet())]
            doc = f'<!doctype html><html lang="{LG}"><head><meta charset="utf-8"><title>Retro Survivors — {t("Manuel", "Manual", "Manual")}</title><style>{css}</style></head><body>{"".join(pages)}</body></html>'
            html_p, pdf_p = f'{OUT}/manual_{LG}.html', f'{OUT}/RetroSurvivors_Manual_{LG.upper()}.pdf'
            open(html_p, 'w', encoding='utf8').write(doc)
            pg = b.new_page(); pg.goto('file:///' + os.path.abspath(html_p).replace('\\', '/')); pg.wait_for_timeout(800)
            over = pg.evaluate("[...document.querySelectorAll('.page')].map((p, i) => [i + 1, p.scrollHeight - p.clientHeight, (p.querySelector('h2,.band') || {}).textContent]).filter(x => x[1] > 2)")
            if over: print(f'{LG}: PAGES THAT OVERFLOW (fix them):', over)
            pg.pdf(path=pdf_p, width='148mm', height='210mm', print_background=True, prefer_css_page_size=True); pg.close()
            print('ok', LG, len(pages), 'pages', os.path.getsize(pdf_p) // 1024, 'KB')
        b.close()


if __name__ == '__main__':
    main()
