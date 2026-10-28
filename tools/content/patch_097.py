"""0.97 content, on top of patch_096:
- the controls' texts: the touch double tap dashes the way the touch joystick points (ctl_dtap, controls); F1 / R3 switch
  the light / dark menus (ctl_theme, theme_hint)
- Potagew Pwoutant (fu_pwout_cawotte): its four Cawottes stay where they sprang up (gspells.js pwcawotte), its cooldown
  doubled (5.252 -> 10.504 s), its blow and heal per tick doubled with it (same damage and heal per minute: the fusions'
  rule and the Cawotte's heal, patch_095); its cloud heals the summons in it too; its text says so
- the Armurerie's fusions: their life steal and heal over time (ui.js sfStats: sf_leech, sf_leech_cap, sf_hot)
- the Bague Houx (C.houx): a ground pickup three times rarer than a spell scroll, one more reroll; the GODMODE test code's texts
- the Île de Frigost zone after L'île de Grobe, at Grobe's difficulty: its monsters, bosses and waves (frigost097.py)
usage: python tools/make_content.py   (runs the newest patch; this one imports patch_096 and writes game/data/content.json)"""
import sys as _sys, os as _os, json
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
import _root
import patch_096 as P

C, G, T, put_ui = P.C, P.G, P.T, P.put_ui

# ---------------------------------------------------------------- the touch dash goes the joystick's way; F1 / R3 switch the light / dark menus
put_ui({'ctl_dtap': T('Double appui (direction du joystick)', "Double tap (the joystick's way)", 'Doppeltippen (Richtung des Joysticks)', 'Doble toque (dirección del joystick)',
                      'Doppio tocco (direzione del joystick)', 'Dubbeltik (richting van de joystick)', 'Toque duplo (direção do joystick)'),
        'ctl_theme': T('mode sombre / clair', 'dark / light mode', 'dunkler / heller Modus', 'modo oscuro / claro', 'modalità scura / chiara', 'donkere / lichte modus', 'modo escuro / claro')})
for lg, a, b in (('fr', '(vers le doigt)', '(direction du joystick)'), ('en', '(towards your finger)', "(the joystick's way)"), ('de', '(zum Finger)', '(Richtung des Joysticks)'),
                 ('es', '(hacia el dedo)', '(dirección del joystick)'), ('it', '(verso il dito)', '(direzione del joystick)'), ('nl', '(naar je vinger)', '(richting van de joystick)'),
                 ('pt', '(na direção do dedo)', '(direção do joystick)')):
    assert a in C['ui'][lg]['controls'], lg; C['ui'][lg]['controls'] = C['ui'][lg]['controls'].replace(a, b)
for lg, add_ in (('fr', ' (F1 / R3)'), ('en', ' (F1 / R3)'), ('de', ' (F1 / R3)'), ('es', ' (F1 / R3)'), ('it', ' (F1 / R3)'), ('nl', ' (F1 / R3)'), ('pt', ' (F1 / R3)')):
    C['ui'][lg]['theme_hint'] += add_

# ---------------------------------------------------------------- Potagew Pwoutant: its Cawottes stay put, a cooldown twice as long
# Its cloud is up p.duration (4 s) of every cd: with the cd doubled it is up half as often, so its blow and its heal per
# tick double to keep what patch_095 set per minute (x1.25 the Pwout's damage on an even crowd; the Cawotte's heal per
# minute at the same shop level). The four Cawottes keep p.satK of the cloud's blow.
FU = C['spells']['fu_pwout_cawotte']['base']; K = 2
assert FU['cd'] == 5.252 and FU['dmg'] == 18.56
FU.update(cd=round(FU['cd'] * K, 3), dmg=round(FU['dmg'] * K, 2), heal=round(FU['heal'] * K, 3), healShop=round(FU['healShop'] * K, 3))
C['spells']['fu_pwout_cawotte']['desc'] = T(
    "Un Pwout de Cawotte rouge-brun vous suit : il blesse les monstres et vous soigne, vous et vos invocations. Quatre Cawottes surgissent autour de vous, restent plantées là et frappent aussi.",
    'A red-brown Cawwot Fawt follows you: it hurts the monsters and heals you and your summons. Four Cawwots spring up around you, stay planted there and strike too.',
    'Ein rotbrauner Kawotten-Pups folgt dir: Er verletzt die Monster und heilt dich und deine Beschwörungen. Vier Kawotten springen um dich herum hervor, bleiben dort stecken und schlagen ebenfalls zu.',
    'Un Pedo de Zanahowia rojizo te sigue: hiere a los monstruos y te cura a ti y a tus invocaciones. Cuatro Zanahowias brotan a tu alrededor, se quedan plantadas allí y también golpean.',
    'Un Peto di Cawota rosso-bruno ti segue: ferisce i mostri e cura te e le tue evocazioni. Quattro Cawote spuntano intorno a te, restano piantate lì e colpiscono anche loro.',
    'Een roodbruine Wortewscheet volgt je: hij verwondt de monsters en geneest jou en je oproepingen. Vier Wortews springen rondom je op, blijven daar geplant staan en slaan ook toe.',
    'Um Pum de Cenouwa castanho-avermelhado segue-te: fere os monstros e cura-te a ti e às tuas invocações. Quatro Cenouwas brotam à tua volta, ficam ali plantadas e também atacam.')

# ---------------------------------------------------------------- the Armurerie's fusions: life steal and heal over time (ui.js sfStats)
put_ui({'sf_leech': T('Vol de vie : {n} des dégâts infligés', 'Life steal: {n} of the damage dealt', 'Lebensraub: {n} des verursachten Schadens', 'Robo de vida: {n} del daño infligido',
                      'Furto di vita: {n} dei danni inflitti', 'Levensroof: {n} van de toegebrachte schade', 'Roubo de vida: {n} do dano causado'),
        'sf_leech_cap': T('au plus {n} de vos PV max par vague', 'at most {n} of your max HP per wave', 'höchstens {n} deiner max. LP pro Welle', 'como mucho {n} de tus PdV máx. por oleada',
                          'al massimo {n} dei tuoi PV max per ondata', 'hoogstens {n} van je max. LP per golf', 'no máximo {n} dos teus PV máx. por onda'),
        'sf_hot': T('Soin périodique : {n} PV par seconde dans le nuage, pendant {d} s', 'Heal over time: {n} HP a second in the cloud, for {d} s', 'Heilung über Zeit: {n} LP pro Sekunde in der Wolke, {d} s lang',
                    'Curación periódica: {n} PdV por segundo en la nube, durante {d} s', 'Cura periodica: {n} PV al secondo nella nube, per {d} s', 'Genezing over tijd: {n} LP per seconde in de wolk, {d} s lang',
                    'Cura periódica: {n} PV por segundo na nuvem, durante {d} s')})

# ---------------------------------------------------------------- the Bague Houx: a ground pickup, one more reroll (game.js collect 'houx')
import langdata as LD
_rate = min(C['drops'][k]['rate'] for k in ('flamiche', 'foudre'))   # (the spell scrolls' chance a monster killed)
C['houx'] = dict(item='it_9_127', rate=round(_rate / 3, 7), name=LD.item(8715))   # three times rarer
put_ui({'houx_got': T('Bague Houx : un relancement de plus ({n} en tout).', 'Blaber Ring: one more reroll ({n} in all).', 'Würfelring: ein Neuwurf mehr ({n} insgesamt).', 'Anillo del Craps: una tirada más ({n} en total).',
                      'Anello Bla: un rilancio in più ({n} in tutto).', 'Blaber Ring: één herworp meer ({n} in totaal).', 'Anel Blaber: mais um relançamento ({n} no total).'),
        # the test code GODMODE (Options > save code, Store.godMode)
        'god_mode_confirm': T('Tout débloquer sur {p} ?', 'Unlock everything on {p}?', 'Alles auf {p} freischalten?', '¿Desbloquear todo en {p}?', 'Sbloccare tutto su {p}?', 'Alles ontgrendelen op {p}?', 'Desbloquear tudo em {p}?'),
        'god_mode_on': T('GODMODE : tout est débloqué et au maximum.', 'GODMODE: everything is unlocked and maxed.', 'GODMODE: alles ist freigeschaltet und maximal.', 'GODMODE: todo está desbloqueado y al máximo.',
                         'GODMODE: tutto è sbloccato e al massimo.', 'GODMODE: alles is ontgrendeld en op het maximum.', 'GODMODE: tudo está desbloqueado e no máximo.')})

# ---------------------------------------------------------------- the loading / chat tips that no longer told the truth
# (a Dofus drops from several bosses, C.dofus[].from; elites drop relics too, C.relicElite; the treasure maps come from
# Jorbak only since 0.95, C.tmap.chance 0 / C.jorbak.tmap; a fusion needs the weapon maxed only since 0.60, and Brute none)
TIPFIX = {
    "Chaque Dofus tombe d'un boss bien précis": T(
        "Chaque Dofus tombe de quelques boss bien précis : sa fiche dit lesquels. Farmer en boucle, c'est aussi ça, Dofus.",
        'Each Dofus drops from a few specific bosses: its sheet tells you which. Farming in a loop is part of Dofus too.',
        'Jedes Dofus fällt von einigen bestimmten Bossen: Sein Steckbrief verrät, von welchen. Endlos farmen gehört auch zu Dofus.',
        'Cada Dofus cae de unos jefes concretos: su ficha dice cuáles. Farmear en bucle también es Dofus.',
        'Ogni Dofus cade da alcuni boss precisi: la sua scheda dice quali. Farmare all\'infinito è anche questo, Dofus.',
        'Elke Dofus valt bij een paar bepaalde bazen: zijn fiche zegt welke. Eindeloos farmen hoort ook bij Dofus.',
        'Cada Dofus cai de alguns chefes precisos: a ficha diz quais. Farmar em ciclo também faz parte de Dofus.'),
    'Les reliques ne tombent que des boss': T(
        'Les reliques tombent des boss, des monstres spéciaux et parfois des élites, six par partie au maximum. Non, ça ne drop pas sur les Larves.',
        'Relics drop from bosses, special monsters and sometimes elites, six per run at most. No, Larvae don\'t drop them.',
        'Relikte fallen von Bossen, Spezialmonstern und manchmal Eliten, höchstens sechs pro Runde. Nein, Larven droppen keine.',
        'Las reliquias caen de jefes, monstruos especiales y a veces élites, seis por partida como máximo. No, las Larvas no las sueltan.',
        'Le reliquie cadono da boss, mostri speciali e a volte élite, sei per partita al massimo. No, le Larve non le droppano.',
        'Relikwieën vallen bij bazen, speciale monsters en soms elites, hoogstens zes per run. Nee, Larven droppen ze niet.',
        'As relíquias caem de chefes, monstros especiais e às vezes elites, seis por partida no máximo. Não, as Larvas não as largam.'),
    "Musha l'Oni perd des cartes au trésor": T(
        "Jorbak a volé les cartes au trésor de Musha l'Oni : battez-le pour en récupérer une, puis creusez sur la croix rouge lors d'une partie suivante. Un Enutrof, lui, aurait déjà la pelle à la main.",
        "Jorbak stole Musha the Oni's treasure maps: beat him to get one back, then dig on the red cross in a later run. An Enutrof would already have the shovel in hand.",
        'Jorbak hat Musha dem Oni die Schatzkarten gestohlen: Besiege ihn, um eine zurückzuholen, und grab in einer späteren Runde am roten Kreuz. Ein Enutrof hätte die Schaufel schon in der Hand.',
        'Jorbak robó los mapas del tesoro de Musha el Oni: derrótalo para recuperar uno y cava en la cruz roja en una partida siguiente. Un Anutrof ya tendría la pala en la mano.',
        "Giorbak ha rubato le mappe del tesoro di Musha l'Oni: sconfiggilo per riprenderne una, poi scava sulla croce rossa in una partita successiva. Un Anutrof avrebbe già la pala in mano.",
        'Nanok heeft de schatkaarten van Musha de Oni gestolen: versla hem om er een terug te krijgen en graaf in een latere run op het rode kruis. Een Enutrof had de schep al in de hand.',
        'O Jorbak roubou os mapas do tesouro do Musha, o Oni: derrota-o para recuperar um e escava na cruz vermelha numa partida seguinte. Um Enutrof já teria a pá na mão.'),
    'Arme au maximum et tous vos sorts au maximum': T(
        "Arme au maximum ? Une fusion vous attend, avec une caractéristique que vous avez (la Fusion Brute n'en demande aucune). Même un Xélor n'y verrait pas passer le temps.",
        'Weapon maxed? A fusion awaits, with a characteristic you have (Raw Fusion needs none). Even a Xelor would lose track of time.',
        'Waffe auf Maximum? Eine Fusion wartet, mit einer Eigenschaft, die du hast (die Rohe Fusion braucht keine). Selbst ein Xelor würde die Zeit vergessen.',
        '¿Arma al máximo? Te espera una fusión, con una característica que tengas (la Fusión Bruta no necesita ninguna). Hasta un Xelor perdería la noción del tiempo.',
        'Arma al massimo? Ti aspetta una fusione, con una caratteristica che hai (la Fusione Bruta non ne chiede nessuna). Persino uno Xelor perderebbe la nozione del tempo.',
        'Wapen op het maximum? Er wacht een fusie, met een eigenschap die je hebt (de Ruwe fusie vraagt er geen). Zelfs een Xelor zou de tijd vergeten.',
        'Arma no máximo? Espera-te uma fusão, com uma característica que tenhas (a Fusão Bruta não pede nenhuma). Até um Xelor perdia a noção do tempo.'),
}
for _start, _t in TIPFIX.items():
    _i = next(i for i, x in enumerate(C['tips']['fr']) if x.startswith(_start))
    for lg in _t: C['tips'][lg][_i] = _t[lg]

# ---------------------------------------------------------------- names the client never translated (its lang files copy the English)
NAMEFIX = {   # French name -> the languages that had the English text
    'Casque Blanc aux cornes Noires': dict(nl='Witte Helm met Zwarte Hoorns'),
    'Hennin du Savoir': dict(en='Hennin of Knowledge', nl='Hennin van Kennis'),
    'Cape avec posigrobeur désintégrant': dict(de='Umhang mit Protonolifis-Pack', it='Mantello con Zaino Protonolifis', nl='Cape met Protonolifis-pak'),
    'Hek la cooleuvre': dict(de='Hek die Ringelnatter', it='Hek la Biscia', nl='Hek de Ringslang'),
    'Leomallow le gentil fantôme': dict(de='Leokasper das freundliche Gespenst', it='Leokasper il Fantasma Buono', nl='Leokasper het Vriendelijke Spook'),
    "Trooyé l'Oxydé": dict(pt='Trooligan, o Buldogue'),
    "Chiendanlémin l'Illusionniste": dict(pt='Warazpacho, a Cherrilla'),
    'Craquetou le Fissuré': dict(pt='Crackrodilrock, o Desafinado'),
    'Eratz le Revendicateur': dict(nl='Eratz de Protesteerder'),
    'Gardien du Savoir': dict(nl='Hoeder van Kennis'),
    'Bouclier trophée du Gourlo le Terrible': dict(de='Trophäenschild von Gourlo dem Schrecklichen', it='Scudo Trofeo di Gourlo il Terribile', nl='Trofeeschild van Gourlo de Verschrikkelijke'),
    'Bague Houx': dict(nl='Blaberring'),
}
def _names(o):
    if isinstance(o, dict):
        fx = NAMEFIX.get(o.get('fr')) if isinstance(o.get('fr'), str) else None
        if fx and 'en' in o: o.update(fx); return
        for v in o.values(): _names(v)
    elif isinstance(o, list):
        for v in o: _names(v)
_names(C)

# ---------------------------------------------------------------- the treasure's Chouque: a pirate killed by Kack Sparo (chouque097.py)
# his lines; his hints at the profile names (the name between ** in bold and quotes, events.js richWrap); his music while
# he talks (assets/audio/music/ghostchouque.mp3); the chest's bonus: half the time a shield or a Dofus (one in two)
import chouque097
C['tmap']['ghost'].update(lines=chouque097.LINES, egglines=chouque097.EGGLINES, music='ghostchouque')
C['tmap'].update(bonus=0.5, bonusDofus=0.5)
put_ui({'tmap_shield': T('Dans le coffre du Chouque : {n} !', "In the Chouque's chest: {n}!", 'In der Truhe des Chouque: {n}!', 'En el cofre del Chouque: ¡{n}!',
                         'Nel forziere del Chouque: {n}!', 'In de kist van de Chouque: {n}!', 'No baú do Chouque: {n}!'),
        'tmap_dofus': T('Un Dofus dort dans le coffre du Chouque !', "A Dofus lies in the Chouque's chest!", 'Ein Dofus liegt in der Truhe des Chouque!', '¡Un Dofus descansa en el cofre del Chouque!',
                        'Un Dofus riposa nel forziere del Chouque!', 'Er ligt een Dofus in de kist van de Chouque!', 'Há um Dofus no baú do Chouque!')})

# ---------------------------------------------------------------- the Île de Frigost, right after Grobe (frigost097.py)
import frigost097
FRIGOST = frigost097.apply(C)

if __name__ == '__main__':
    json.dump(C, open(f'{G}/data/content.json', 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
    print('0.97 ok: Potagew Pwoutant', {k: C['spells']['fu_pwout_cawotte']['base'][k] for k in ('cd', 'dmg', 'heal', 'healShop')})
