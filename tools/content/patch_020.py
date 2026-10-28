"""Beta 0.20 content, applied on top of patch_v20 (the game is in beta: "v2.0" becomes 0.20, then +0.01 per patch).
Bosses +50% HP rounded up to the next 1000, monster crowd growing every minute (x2 from minute 5), new UI strings."""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
import _root
import json, math
import patch_v20 as P

C, T, G = P.C, P.T, P.G

# ---------------------------------------------------------------- balance
for b in C['bosses'].values():
    b['hp'] = int(math.ceil(b['hp'] * 1.5 / 1000) * 1000)   # +50%, always a round number (the game rounds again in a run)
R = C['run']
R['spawnGrow'] = 0.06      # the crowd target grows by 6% of its base every minute
R['spawnLateT'] = 5.0      # from minute 5...
R['spawnLate'] = 2.0       # ...twice as many monsters (ramped over that minute, with a warning)
R['spawnCap'] = 600        # (was 380) room for the doubled crowd

R['spawnStopT'] = 9.5      # no new monster after 9:30 (the Maîtres Corbacs still come at 10:00)
C['spellPer'] = 0.05       # spell shop: +5% power per level (was 10%)
C['spellSlots'] = 4        # 4 attack spells per run (was 5); 'Borné' gives the 5th for a characteristic slot
C['hard'] = dict(hpMin=0.5, hpMax=0.75, dmg=1.5, speed=1.05, atk=1.15, bossHp=2)   # Difficile mode
for lg in C['ui']:
    C['ui'][lg]['spell_intro'] = C['ui'][lg]['spell_intro'].replace('+10 %', '+5 %').replace('+10%', '+5%')
if not any(p['id'] == 'borne' for p in C['passives']):
    C['passives'].append(dict(id='borne', icon='ch_20', max=1, stat='spellslot', per=1,
        name=T('Borné', 'Stubborn', 'Stur', 'Obstinado', 'Testardo', 'Koppig', 'Teimoso'),
        desc=T('+1 emplacement de sort offensif (5 au lieu de 4), au prix de cet emplacement de caractéristique.',
               '+1 attack spell slot (5 instead of 4), at the cost of this characteristic slot.',
               '+1 Angriffszauber-Platz (5 statt 4), auf Kosten dieses Eigenschaftsplatzes.',
               '+1 espacio de hechizo ofensivo (5 en vez de 4), a cambio de este espacio de característica.',
               '+1 slot di incantesimo offensivo (5 invece di 4), al prezzo di questo slot di caratteristica.',
               '+1 aanvalsspreukplek (5 in plaats van 4), ten koste van deze eigenschapsplek.',
               '+1 espaço de feitiço ofensivo (5 em vez de 4), ao custo deste espaço de característica.')))

# ---------------------------------------------------------------- original spell sounds and cast animations (0.21)
# work/spell_sprites.json: id -> [name, spell clip (clips/spells/<n>.swf, 0 = none), "launch,casterAnim,?"] from the
# SunDofus emulator database (github.com/nicopetit95/sundofus). A spell clip plays its own sound; without one (or a
# silent clip) the client plays the caster's cast animation and its sound.
SPS = json.load(open(f'{P.ROOT}/work/spell_sprites.json'))
C['drops']['liberation']['anim'] = 'anim' + SPS['368'][2].split(',')[1]   # Libération: no clip, the caster's anim1 (and its sound)
KEEP_ANIM = {'bond', 'assaut', 'tromblon', 'fronde', 'appel_mama', 'vol_pieces', 'dagues_boomerang', 'elagage_cou', 'karcham'}  # moves / Dofus 2 classes
for k, s in C['spells'].items():
    o = SPS.get(str(s.get('sid', s.get('icon'))))
    if not o or k in KEEP_ANIM or s.get('weapon'): continue
    a = 'anim' + o[2].split(',')[1]
    if a != s.get('anim') and a != 'anim-1': s['anim'] = a
for c in C['classes']: c.pop('nopets', None)   # every class can take a pet (sheets without pet anchors get the standard spot)
C['spells']['roulage_pelle']['snd'] = 'setag_305'
C['drops']['flamiche']['snd'] = 'explosion'          # the sound of its own clip (4600), not the Crâ's arrow
C['drops']['liberation']['snd'] = 'punch'           # fallback only (a class sprite without a cast sound)   # its original clip (305) sound; the game draws it without that clip

# ---------------------------------------------------------------- 0.21 lot 4: pictures
# the masteries use the pictures of the client's 'Sort Maîtrise …' scrolls (items type 73, built by build_icons20)
MASTERY_IT = dict(epee=1, baton=2, arc=3, marteau=4, baguette=5, dague=6, pelle=7, hache=8)
for w in C['weapons']: w['masteryIcon'] = f"it_73_{MASTERY_IT[w['id']]}"
# Sacrieur / Pandawa: their real client icons (icon numbers ≠ spell ids), on the class colour (build_spellicons21)
import build_spellicons21 as SI
for cls, plan in SI.PLAN.items():
    for sid, n in plan.items(): C['spells'][sid]['icon'] = f'{cls}_{n}'
for cls, plan in SI.CUSTOM.items():
    for sid, kind in plan.items(): C['spells'][sid]['icon'] = f'{cls}_{kind}'
for p_ in C['passives']:
    if p_['id'] == 'duree': p_['icon'] = 'Icon_duree'   # an hourglass (PM keeps the boot)

# ---------------------------------------------------------------- UI strings
UI = {
    'crowd_grows': T('Les monstres ont décidé d\'appeler leurs potes !', 'The monsters decided to call their mates!', 'Die Monster haben beschlossen, ihre Kumpels zu rufen!', '¡Los monstruos han decidido llamar a sus colegas!', 'I mostri hanno deciso di chiamare i loro amici!', 'De monsters hebben besloten hun maten te roepen!', 'Os monstros decidiram chamar os amigos!'),
    'doom': T('Les Maîtres Corbac arrivent !', 'The Lord Crows are coming!', 'Die Meister Raben kommen!', '¡Llegan los Maestros Cuerbok!', 'Arrivano i Messer Cuervoc!', 'De Heren Kraai komen eraan!', 'Os Lordes Corvos estão chegando!'),
    'exploit_tot': T('ToT vous remet le {d} ! Son effet vous accompagnera dans toutes vos parties.', 'ToT hands you the {d}! Its effect will stay with you in every run.', 'ToT überreicht dir das {d}! Sein Effekt begleitet dich in allen Runden.', '¡ToT te entrega el {d}! Su efecto te acompañará en todas tus partidas.', 'ToT ti consegna il {d}! Il suo effetto ti accompagnerà in tutte le partite.', 'ToT geeft je de {d}! Het effect blijft je in elk spel bij.', 'ToT entrega-lhe o {d}! O efeito dele acompanhará você em todas as partidas.'),
    'door_text2': T('« Encore toi ?! Mon Dofus, tu l\'as déjà… Alors : on rejoue au quiz comme un vrai héros, ou tu prends le raccourci des tricheurs ? »', '"You again?! You already have my Dofus… So: do we play the quiz again like a true hero, or do you take the cheater\'s shortcut?"', '„Du schon wieder?! Mein Dofus hast du doch schon… Also: noch ein Quiz wie ein echter Held, oder nimmst du die Abkürzung der Schummler?"', '«¡¿Tú otra vez?! Mi Dofus ya lo tienes… Entonces: ¿repetimos el quiz como un verdadero héroe, o tomas el atajo de los tramposos?»', '«Ancora tu?! Il mio Dofus ce l\'hai già… Allora: rifacciamo il quiz da vero eroe, o prendi la scorciatoia dei furbetti?»', '"Jij weer?! Mijn Dofus heb je al… Dus: spelen we de quiz opnieuw als een echte held, of neem je de valsspelersroute?"', '«Você de novo?! O meu Dofus você já tem… Então: jogamos o quiz outra vez como um verdadeiro herói, ou vai pelo atalho dos trapaceiros?»'),
    'door_fight': T('Je relève le défi !', 'Bring it on!', 'Her mit der Herausforderung!', '¡Acepto el reto!', 'Accetto la sfida!', 'Kom maar op!', 'Aceito o desafio!'),
    'door_bonus': T('Le bonus… et la claque', 'The bonus… and the slap', 'Der Bonus… und die Ohrfeige', 'El bonus… y la colleja', 'Il bonus… e lo schiaffo', 'De bonus… en de mep', 'O bónus… e a chapada'),
    'door_bonus_desc': T('Raccourci : ToT vous donne son bonus tout de suite, mais vous colle une claque qui divise vos dégâts par deux pendant 30 secondes.', 'Shortcut: ToT gives you his bonus at once, but slaps you so hard your damage is halved for 30 seconds.', 'Abkürzung: ToT gibt dir sofort seinen Bonus, verpasst dir aber eine Ohrfeige, die deinen Schaden 30 Sekunden lang halbiert.', 'Atajo: ToT te da su bonus al instante, pero te suelta una colleja que reduce tu daño a la mitad durante 30 segundos.', 'Scorciatoia: ToT ti dà subito il suo bonus, ma ti molla uno schiaffo che dimezza i tuoi danni per 30 secondi.', 'Kortere weg: ToT geeft je meteen zijn bonus, maar deelt een mep uit die je schade 30 seconden halveert.', 'Atalho: ToT dá-lhe o bónus de imediato, mas prega-lhe uma chapada que reduz o seu dano para metade durante 30 segundos.'),
    'tot_slap': T('PAF ! La claque de ToT : -50 % de dégâts pendant 30 s !', 'SMACK! ToT\'s slap: -50% damage for 30 s!', 'KLATSCH! ToTs Ohrfeige: -50 % Schaden für 30 s!', '¡ZAS! La colleja de ToT: -50 % de daño durante 30 s!', 'SBAM! Lo schiaffo di ToT: -50% di danni per 30 s!', 'PATS! De mep van ToT: -50% schade gedurende 30 s!', 'PÁ! A chapada do ToT: -50% de dano durante 30 s!'),
    'ctl_title': T('Commandes', 'Controls', 'Steuerung', 'Controles', 'Comandi', 'Besturing', 'Controlos'),
    'ctl_kb': T('Clavier', 'Keyboard', 'Tastatur', 'Teclado', 'Tastiera', 'Toetsenbord', 'Teclado'),
    'ctl_pad': T('Manette', 'Controller', 'Controller', 'Mando', 'Controller', 'Controller', 'Comando'),
    'ctl_touch': T('Téléphone / tablette', 'Phone / tablet', 'Handy / Tablet', 'Móvil / tableta', 'Telefono / tablet', 'Telefoon / tablet', 'Telemóvel / tablet'),
    'ctl_move': T('Se déplacer', 'Move', 'Bewegen', 'Moverse', 'Muoversi', 'Bewegen', 'Mover-se'),
    'ctl_dash': T('Esquive (ruée)', 'Dodge (dash)', 'Ausweichen (Sprint)', 'Esquiva (carrera)', 'Schivata (scatto)', 'Ontwijken (sprint)', 'Esquiva (investida)'),
    'ctl_movespells': T('Sorts de déplacement on/off', 'Movement spells on/off', 'Bewegungszauber an/aus', 'Hechizos de movimiento sí/no', 'Incantesimi di movimento on/off', 'Bewegingsspreuken aan/uit', 'Feitiços de movimento on/off'),
    'ctl_pause': T('Pause', 'Pause', 'Pause', 'Pausa', 'Pausa', 'Pauze', 'Pausa'),
    'ctl_levelup': T('Choisir un bonus', 'Pick a bonus', 'Bonus wählen', 'Elegir un bonus', 'Scegliere un bonus', 'Bonus kiezen', 'Escolher um bónus'),
    'ctl_reroll': T('relancer', 'reroll', 'neu würfeln', 'cambiar', 'rilanciare', 'opnieuw', 'trocar'),
    'ctl_menus': T('Menus', 'Menus', 'Menüs', 'Menús', 'Menu', "Menu's", 'Menus'),
    'ctl_back': T('retour', 'back', 'zurück', 'atrás', 'indietro', 'terug', 'voltar'),
    'ctl_tabs': T('onglets', 'tabs', 'Reiter', 'pestañas', 'schede', 'tabbladen', 'separadores'),
    'ctl_fullscreen': T('Plein écran', 'Fullscreen', 'Vollbild', 'Pantalla completa', 'Schermo intero', 'Volledig scherm', 'Ecrã inteiro'),
    'ctl_lstick': T('Stick gauche', 'Left stick', 'Linker Stick', 'Stick izquierdo', 'Stick sinistro', 'Linker stick', 'Analógico esquerdo'),
    'ctl_dpad': T('croix', 'D-pad', 'Steuerkreuz', 'cruceta', 'croce', 'D-pad', 'direcional'),
    'ctl_drag': T('Posez le doigt et glissez (joystick virtuel)', 'Put a finger down and slide (virtual stick)', 'Finger auflegen und ziehen (virtueller Stick)', 'Apoya el dedo y deslízalo (joystick virtual)', 'Appoggia il dito e trascina (joystick virtuale)', 'Zet een vinger neer en schuif (virtuele stick)', 'Pouse o dedo e deslize (joystick virtual)'),
    'ctl_dtap': T('Double appui, vers le doigt', 'Double tap, towards the finger', 'Doppeltippen, zum Finger hin', 'Doble toque, hacia el dedo', 'Doppio tocco, verso il dito', 'Dubbeltik, naar de vinger toe', 'Toque duplo, na direção do dedo'),
    'ctl_icon': T('Touchez leur icône (à gauche du cœur)', 'Tap their icon (left of the heart)', 'Ihr Symbol antippen (links vom Herz)', 'Toca su icono (a la izquierda del corazón)', 'Tocca la loro icona (a sinistra del cuore)', 'Tik op hun icoon (links van het hart)', 'Toque no ícone (à esquerda do coração)'),
    'ctl_pausebtn': T('Bouton pause, en haut à droite', 'Pause button, top right', 'Pausetaste oben rechts', 'Botón de pausa, arriba a la derecha', 'Pulsante pausa, in alto a destra', 'Pauzeknop, rechtsboven', 'Botão de pausa, no canto superior direito'),
    'ctl_card': T('Touchez la carte', 'Tap the card', 'Karte antippen', 'Toca la carta', 'Tocca la carta', 'Tik op de kaart', 'Toque na carta'),
    'ctl_space': T('Espace', 'Space', 'Leertaste', 'Espacio', 'Spazio', 'Spatie', 'Espaço'),
    'ctl_esc': T('Échap', 'Esc', 'Esc', 'Esc', 'Esc', 'Esc', 'Esc'),
    'ctl_enter': T('Entrée', 'Enter', 'Eingabe', 'Intro', 'Invio', 'Enter', 'Enter'),
    'ctl_or': T('ou', 'or', 'oder', 'o', 'o', 'of', 'ou'),
    'perf_mode': T('Mode performance', 'Performance mode', 'Leistungsmodus', 'Modo rendimiento', 'Modalità prestazioni', 'Prestatiemodus', 'Modo desempenho'),
    'perf_hint': T('Pour les petits PC et téléphones : effets réduits, image moins fine, 30 images/s.', 'For small PCs and phones: fewer effects, a softer picture, 30 fps.', 'Für schwache PCs und Handys: weniger Effekte, weicheres Bild, 30 fps.', 'Para PC y móviles modestos: menos efectos, imagen más suave, 30 fps.', 'Per PC e telefoni poco potenti: meno effetti, immagine più morbida, 30 fps.', 'Voor zwakke pc\'s en telefoons: minder effecten, zachter beeld, 30 fps.', 'Para PCs e telemóveis fracos: menos efeitos, imagem mais suave, 30 fps.'),
    'mode_normal': T('Normale', 'Normal', 'Normal', 'Normal', 'Normale', 'Normaal', 'Normal'),
    'mode_hard': T('Difficile', 'Hard', 'Schwer', 'Difícil', 'Difficile', 'Moeilijk', 'Difícil'),
    'mode_hint': T('Difficile : monstres +50 à 75 % de PV, +50 % de dégâts, plus rapides ; boss ×2 PV.', 'Hard: monsters +50 to 75% HP, +50% damage, faster; bosses x2 HP.', 'Schwer: Monster +50 bis 75 % LP, +50 % Schaden, schneller; Bosse x2 LP.', 'Difícil: monstruos +50 a 75 % de PdV, +50 % de daño, más rápidos; jefes x2 PdV.', 'Difficile: mostri +50-75% PV, +50% danni, più veloci; boss x2 PV.', 'Moeilijk: monsters +50 tot 75% LP, +50% schade, sneller; bazen x2 LP.', 'Difícil: monstros +50 a 75% de PV, +50% de dano, mais rápidos; chefes x2 PV.'),
    'main_menu': T('Menu principal', 'Main menu', 'Hauptmenü', 'Menú principal', 'Menu principale', 'Hoofdmenu', 'Menu principal'),
    'quit_game': T('Quitter', 'Quit', 'Beenden', 'Salir', 'Esci', 'Afsluiten', 'Sair'),
    'quit_tab': T('Vous pouvez fermer cet onglet.', 'You can close this tab.', 'Du kannst diesen Tab schließen.', 'Puedes cerrar esta pestaña.', 'Puoi chiudere questa scheda.', 'Je kunt dit tabblad sluiten.', 'Pode fechar este separador.'),
    'beta': T('Bêta', 'Beta', 'Beta', 'Beta', 'Beta', 'Bèta', 'Beta'),
}
for k, v in UI.items():
    for lg, s in v.items(): C['ui'][lg][k] = s

# ================================================================ 0.22 (balance pass + small features)
import re as _re
R['spellDmgMul'] = 0.5         # every spell and weapon of the player hits half as hard
R['fecaDmg'] = 0.95            # the Féca's spells -5%
R['xpPace'] = 10.0             # everything maxed around minute 7 (asked: -30% XP, but with half the damage the kills come much slower: tuned on the sim)
R['meleeMul'] = round(R['meleeMul'] * 1.5, 3); R['rangedMul'] = round(R['rangedMul'] * 1.5, 3)   # monsters +50% damage
R['firstAtk'] = 0.5            # their first attack comes twice as fast
R['mobSpeed'] = round(R.get('mobSpeed', 1) * 1.05, 4)   # +5% speed
R['breadRate'] = 0.006 / 4     # bread drops divided by 4
R['goldRate'] = 0.001          # Minerai d'Or: about 3 per run (a rare object: Chance raises it)
R['projKnock'] = 90            # a projectile pushes a monster back about half a cell
C['spellPer'] = 0.10           # spell shop back to +10% per level (masteries are +10% per level too)
C['goldKamas'] = 25
C['batofu'] = dict(dur=30, dist=1.25, cd=0.5)   # Plume du Batofu: dashes 25% longer, cooldown halved, for 30 seconds
C['breads'] = {'amakna': dict(hp=10, icon='it_33_13'), 'ble': dict(hp=20, icon='it_33_7'), 'champs': dict(hp=30, icon='it_33_68'), 'chapain': dict(hp=-1, icon='it_33_4')}
C['hard'] = dict(hpMin=0.5, hpMax=0.5, dmg=2.5, speed=1.05, atk=1.15, bossHp=1.5)   # Difficile: +50% HP, x2.5 damage, bosses +50% HP
C['doom'].update(t=660, tWon=600, every=10)   # the Maîtres Corbacs: 11:00 (10:00 once the zone is won), a wave every 10 seconds
C['bosses']['maitre_corbac_doom']['speed'] = round(C['bosses']['maitre_corbac_doom']['speed'] * 0.95 / 1.05, 1)   # -5% (net of the +5% for all)
for c in C['classes']: c['base']['hp'] = round(c['base']['hp'] / 2)   # every character starts with half the HP
for p_ in C['passives']:
    if p_['id'] == 'vol_de_vie': p_['per'] = round(p_['per'] / 3, 6); p_['desc'] = {k: v.replace('0,08%', '0,027%').replace('0.08%', '0.027%') for k, v in p_['desc'].items()}
SP_ = C['spells']
SP_['immunite']['base']['cd'] *= 3
for l in SP_['immunite']['lv']:
    if 'cd' in l: l['cd'] *= 3
for sid in ('mot_curatif', 'mot_amitie'):   # the Eniripsa heals twice as rarely, half as much
    sp = SP_[sid]
    for d in [sp['base']] + sp['lv']:
        if 'cd' in d: d['cd'] = round(d['cd'] * 2, 2)
        if 'heal' in d: d['heal'] = round(d['heal'] / 2, 2)
        if 'healTick' in d: d['healTick'] = round(d['healTick'] * 2, 2)
osa = next(c for c in C['classes'] if c['id'] == 'osamodas')
for sid in osa['spells']:   # the Osamodas' summons last half as long
    for d in [SP_[sid]['base']] + SP_[sid]['lv']:
        if 'duration' in d and SP_[sid]['t'] == 'summon': d['duration'] = round(d['duration'] / 2, 2)
feca = next(c for c in C['classes'] if c['id'] == 'feca')
feca['passive'] = T('Armure Féca : +2 résistance.', 'Feca Armour: +2 armour.', 'Feca-Rüstung: +2 Resistenz.', 'Armadura Feca: +2 de resistencia.', 'Armatura Feca: +2 resistenza.', 'Feca-pantser: +2 weerstand.', 'Armadura Feca: +2 de resistência.')
SP_['bouclier_feca']['desc'] = T('Des glyphes protectrices tournent autour de vous, frappent et repoussent les ennemis, et vous donnent +1 résistance par niveau tant qu\'elles tournent.', 'Protective glyphs orbit you, hitting and pushing enemies away, and give you +1 armour per level while they spin.', 'Schützende Glyphen kreisen um dich, treffen Gegner, stoßen sie zurück und geben dir +1 Resistenz pro Stufe, solange sie kreisen.', 'Glifos protectores giran a tu alrededor, golpean y repelen a los enemigos y te dan +1 de resistencia por nivel mientras giran.', 'Glifi protettivi ruotano attorno a te, colpiscono e respingono i nemici, e ti danno +1 resistenza per livello finché girano.', 'Beschermende glyphen draaien om je heen, raken en duwen vijanden weg en geven je +1 weerstand per niveau zolang ze draaien.', 'Glifos protetores giram ao seu redor, golpeiam e repelem os inimigos, e dão +1 de resistência por nível enquanto giram.')
# monsters that push their enemies back in Dofus Retro (a spell with the push effect, from the emulator data)
import sqlite3 as _sq
_db = _sq.connect(f'{P.ROOT}/work/sl.db'); _L = json.load(open(f'{P.ROOT}/work/lang_json/spells_fr.json'))['S']
def _pushes(i):
    s_ = _L.get(str(i)) or {}
    return any(e and e[0] == 5 for lv in ('l1', 'l2', 'l3', 'l4', 'l5', 'l6') for e in ((s_.get(lv) or [[]])[0] or []))
for k, m in list(C['monsters'].items()) + list(C['bosses'].items()):
    r_ = _db.execute('select spells from monsters where id=?', (m.get('did'),)).fetchone()
    ids = {int(x.split('@')[0]) for g in (r_[0] if r_ and r_[0] else '').split('|') for x in g.split(';') if x}
    if any(_pushes(i) for i in ids): m['push'] = 150 if k in C['bosses'] else 110
C['monsters']['wo_wabbit']['push'] = 180; C['monsters']['wo_wabbit']['melee'] = 1   # the Wo Wabbit comes to hit you, about 5 metres
# zones from the easiest to the hardest; the Île de Nowel opens with 50 achievements
order = ['astrub', 'chafer', 'porco', 'naufrages', 'gelee', 'foret', 'cania', 'pandala', 'wabbit', 'otomai_coast', 'otomai_jungle', 'minotoror', 'vlad', 'kwismas']
C['maps'].sort(key=lambda m: order.index(m['id']) if m['id'] in order else 99)
for m in C['maps']:
    if m['id'] == 'kwismas': m['unlockAch'] = 50
# "30 s" -> "30 secondes" in the messages
SEC = dict(fr='secondes', en='seconds', de='Sekunden', es='segundos', it='secondi', nl='seconden', pt='segundos')
for lg in C['ui']:
    for k, v in list(C['ui'][lg].items()):
        if isinstance(v, str): C['ui'][lg][k] = _re.sub(r'(\d+) s\b(?!\w)', lambda mm: mm.group(1) + ' ' + SEC[lg], v)
UI2 = {
    'gold_found': T('Minerai d\'Or ! +{n} kamas. Ça brille, donc c\'est à vous.', 'Gold ore! +{n} kamas. It shines, so it\'s yours.', 'Golderz! +{n} Kamas. Es glänzt, also gehört es dir.', '¡Mineral de oro! +{n} kamas. Brilla, así que es tuyo.', 'Minerale d\'oro! +{n} kama. Luccica, quindi è tuo.', 'Gouderts! +{n} kama\'s. Het glimt, dus het is van jou.', 'Minério de ouro! +{n} kamas. Brilha, logo é seu.'),
    'batofu': T('Plume du Batofu : esquives 25 % plus longues et deux fois plus fréquentes pendant 30 secondes !', 'Batofu Feather: dashes 25% longer and twice as often for 30 seconds!', 'Batofu-Feder: Ausweichen 25 % weiter und doppelt so oft für 30 Sekunden!', 'Pluma del Batofu: esquivas un 25 % más largas y el doble de seguido durante 30 segundos.', 'Piuma del Batofu: schivate più lunghe del 25% e due volte più spesso per 30 secondi!', 'Batofuveer: 25% langere ontwijkingen, twee keer zo vaak, 30 seconden lang!', 'Pena do Batofu: esquivas 25% mais longas e duas vezes mais frequentes durante 30 segundos!'),
    'plumec': T('Plume du Maître Corbac ramassée ({n} au total). Elle ne sert à rien, mais quelle classe !', 'Lord Crow feather picked up ({n} in all). Useless, but so stylish!', 'Meister-Raben-Feder aufgehoben ({n} insgesamt). Nutzlos, aber so stilvoll!', 'Pluma del Maestro Cuerbok recogida ({n} en total). No sirve para nada, ¡pero qué estilo!', 'Piuma di Messer Cuervoc raccolta ({n} in tutto). Inutile, ma che stile!', 'Veer van Heer Kraai opgeraapt ({n} in totaal). Nutteloos, maar zo stijlvol!', 'Pena do Lorde Corvo apanhada ({n} no total). Não serve para nada, mas que estilo!'),
    'konami': T('Tofu-mania ! Le monde s\'arrête… et tout le monde devient Tofu.', 'Tofu-mania! The world stops… and everyone turns into a Tofu.', 'Tofu-Manie! Die Welt hält an… und alle werden zu Tofus.', '¡Tofumanía! El mundo se detiene… y todos se vuelven Tofus.', 'Tofu-mania! Il mondo si ferma… e tutti diventano Tofu.', 'Tofu-manie! De wereld staat stil… en iedereen wordt een Tofu.', 'Tofu-mania! O mundo para… e todos viram Tofus.'),
    'nowel_lock': T('Remportez 50 succès pour ouvrir cette zone.', 'Earn 50 achievements to open this zone.', 'Erringe 50 Erfolge, um diese Zone zu öffnen.', 'Consigue 50 logros para abrir esta zona.', 'Ottieni 50 obiettivi per aprire questa zona.', 'Behaal 50 prestaties om deze zone te openen.', 'Conquiste 50 conquistas para abrir esta zona.'),
    'cr7': T('Ce jeu a été vibecodé, mais vibecodé avec la passion d\'un nostalgique de Dofus qui a encore son Gelano de 2006 rangé quelque part.',
             'This game was vibecoded, but vibecoded with the passion of a Dofus nostalgic who still keeps his 2006 Gelano somewhere.',
             'Dieses Spiel wurde vibegecodet, aber mit der Leidenschaft eines Dofus-Nostalgikers, der seinen Gelano von 2006 noch irgendwo aufbewahrt.',
             'Este juego fue vibecodeado, pero vibecodeado con la pasión de un nostálgico de Dofus que aún guarda su Gelano de 2006 en algún cajón.',
             'Questo gioco è stato vibecodato, ma vibecodato con la passione di un nostalgico di Dofus che conserva ancora il suo Gelano del 2006.',
             'Deze game is gevibecodet, maar met de passie van een Dofus-nostalgicus die zijn Gelano uit 2006 nog ergens bewaart.',
             'Este jogo foi vibecodado, mas vibecodado com a paixão de um nostálgico de Dofus que ainda guarda o seu Gelano de 2006 algures.'),
    'cr8': T('Il ne sera jamais payant : l\'argent n\'a jamais été et ne sera jamais le moteur des jeux que je vibecode. Gardez vos kamas, vous en aurez besoin pour le Zaap.',
             'It will never cost a thing: money never was and never will be what drives the games I vibecode. Keep your kamas, you\'ll need them for the Zaap.',
             'Es wird nie etwas kosten: Geld war und wird nie der Antrieb der Spiele sein, die ich vibecode. Behaltet eure Kamas, ihr braucht sie für den Zaap.',
             'Nunca será de pago: el dinero nunca ha sido ni será el motor de los juegos que vibecodeo. Guardad vuestros kamas, los necesitaréis para el Zaap.',
             'Non sarà mai a pagamento: il denaro non è mai stato e mai sarà il motore dei giochi che vibecodo. Tenetevi i kama, vi serviranno per lo Zaap.',
             'Het wordt nooit betalend: geld is nooit de drijfveer geweest van de games die ik vibecode, en dat blijft zo. Houd je kama\'s, je hebt ze nodig voor de Zaap.',
             'Nunca será pago: o dinheiro nunca foi nem será o motor dos jogos que vibecodo. Guardem os vossos kamas, vão precisar deles para o Zaap.'),
    'cr9': T('Ankama mérite de perdurer, pas d\'être exploité. Mais il serait temps de se sortir les doigts du Slip de Trool et de bloquer enfin les bots : il n\'y a jamais eu d\'excuse, et avec l\'IA d\'aujourd\'hui il y en a encore moins pour détecter et bannir ces fermes à pognon que des petits malins nourrissent en leur achetant des kamas.',
             'Ankama deserves to last, not to be exploited. But it\'s time to take their fingers out of the Trool\'s Pants and finally block the bots: there never was an excuse, and with today\'s AI there\'s even less of one for not detecting and banning those money farms that clever clogs keep feeding by buying kamas.',
             'Ankama verdient es, zu bestehen, nicht ausgebeutet zu werden. Aber es wird Zeit, die Finger aus der Trool-Unterhose zu nehmen und endlich die Bots zu sperren: Es gab nie eine Ausrede, und mit der heutigen KI erst recht keine, diese Geldfarmen nicht zu erkennen und zu bannen, die schlaue Köpfe mit Kamakäufen füttern.',
             'Ankama merece perdurar, no ser explotado. Pero ya es hora de que se saquen los dedos del Calzón de Trool y bloqueen por fin los bots: nunca hubo excusa, y con la IA de hoy aún menos para no detectar ni banear esas granjas de dinero que algunos listillos alimentan comprando kamas.',
             'Ankama merita di durare, non di essere sfruttata. Ma è ora di togliere le dita dalle Mutande di Trool e bloccare finalmente i bot: non c\'è mai stata una scusa, e con l\'IA di oggi ancora meno per non scovare e bannare quelle fattorie di soldi che certi furbetti nutrono comprando kama.',
             'Ankama verdient het om te blijven bestaan, niet om uitgebuit te worden. Maar het wordt tijd om de vingers uit de Troolonderbroek te halen en eindelijk de bots te blokkeren: er was nooit een excuus, en met de AI van vandaag nog minder om die geldfarms niet op te sporen en te bannen die slimmeriken voeden door kama\'s te kopen.',
             'A Ankama merece perdurar, não ser explorada. Mas está na hora de tirar os dedos das Cuecas de Trool e bloquear finalmente os bots: nunca houve desculpa, e com a IA de hoje ainda menos para não detetar e banir essas quintas de dinheiro que alguns espertalhões alimentam comprando kamas.'),
    'cr10': T('Et nerfez les Crâs sur Rétro. Bisou.', 'And nerf the Cras on Retro. Kisses.', 'Und nerft die Cras auf Retro. Küsschen.', 'Y nerfead a los Zurcarák en Retro. Besos.', 'E nerfate i Cra su Retro. Bacio.', 'En nerf de Cra\'s op Retro. Kusje.', 'E nerfem os Cras no Retro. Beijinhos.'),
}
UI2['st_best_dps'] = T('Meilleurs dégâts en 1 seconde', 'Best damage in 1 second', 'Bester Schaden in 1 Sekunde', 'Mejor daño en 1 segundo', 'Danni migliori in 1 secondo', 'Beste schade in 1 seconde', 'Melhor dano em 1 segundo')
UI2['traits_intro'] = T('Entraînez vos caractéristiques : +10 % de leur effet par niveau, pour tous vos personnages. Même la Sagesse finit par rentrer.', 'Train your characteristics: +10% of their effect per level, for all your characters. Even Wisdom gets in eventually.', 'Trainiere deine Eigenschaften: +10 % ihrer Wirkung pro Stufe, für alle Charaktere. Selbst Weisheit kommt irgendwann an.', 'Entrena tus características: +10 % de su efecto por nivel, para todos tus personajes. Hasta la Sabiduría acaba entrando.', 'Allena le tue caratteristiche: +10% del loro effetto per livello, per tutti i personaggi. Perfino la Saggezza alla fine entra.', 'Train je eigenschappen: +10% van hun effect per niveau, voor al je personages. Zelfs Wijsheid dringt uiteindelijk door.', 'Treine as suas características: +10% do efeito por nível, para todos os personagens. Até a Sabedoria acaba por entrar.')
UI2['st_dps_col'] = T('Record DPS', 'Best DPS', 'Bester DPS', 'Récord DPS', 'Record DPS', 'Beste DPS', 'Recorde DPS')
if not any(a['id'] == 'plumes_3' for a in C['achievements']):
    C['achievements'].append(dict(id='plumes_3', k='plumes', n=3, icon='it_53_362', name=T('Plumé', 'Plucked', 'Gerupft', 'Desplumado', 'Spennato', 'Geplukt', 'Depenado'),
        desc=T('Ramasser 3 Plumes du Maître Corbac. Le Corbac, lui, a froid.', 'Pick up 3 Lord Crow feathers. The Crow, for his part, is cold.', 'Sammle 3 Federn des Meister Raben. Dem Raben ist jetzt kalt.', 'Recoge 3 plumas del Maestro Cuerbok. El Cuerbok, por su parte, tiene frío.', 'Raccogli 3 piume di Messer Cuervoc. Lui, intanto, ha freddo.', 'Raap 3 veren van Heer Kraai op. De kraai heeft het nu koud.', 'Apanhe 3 penas do Lorde Corvo. O Corvo, esse, tem frio.')))
for k, v in UI2.items():
    for lg, txt in v.items(): C['ui'][lg][k] = txt

if __name__ == '__main__':
    json.dump(C, open(f'{G}/data/content.json', 'w'), ensure_ascii=False, separators=(',', ':'))
    print('0.20 ok', {k: C['bosses'][k]['hp'] for k in ('chef_bouftou', 'dark_vlad', 'minotot')}, {k: R[k] for k in ('spawnGrow', 'spawnLate', 'spawnCap')})
