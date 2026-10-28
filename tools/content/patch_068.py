"""0.68 content: balance list, the Osamodas fusions (Crackler strikes, Boufcouls), shorter statistics labels.
usage: PYTHONUTF8=1 python tools/content/patch_068.py  (imports patch_065, writes game/data/content.json)"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
import _root
import json
CRAQ_DMG = 42.0   # (bench: tools/checks/sim_node.js BENCH=fu_osa_marteau)
import patch_065 as P5

C, G, T, put_ui = P5.C, P5.G, P5.T, P5.put_ui
S = C['spells']
PAS = {p['id']: p for p in C['passives']}
SCR = {s['id']: s for s in C['scrolls']}

# ------------------------------------------------------------------ balance
# Lait de Bambou: heals ÷10, cooldown ×2; clears the monsters' / ground's debuffs, +15 % speed, +10 resistance, immune
# to debuffs 1 s (Durée lengthens it up to 1.5 s): spells.js 'heal' (haste, cleanse), bosses.js cleanse / cleansed
lb = S['lait_de_bambou']
lb['base'] = {'heal': 1.0, 'cd': 14.0, 'armorBuff': 10, 'buffDur': 3.0, 'haste': 0.15, 'cleanse': 1.0}
lb['lv'] = [{}, {'heal': 1.4}, {'cd': 12.0}, {'buffDur': 3.5}, {'heal': 2.0, 'cd': 10.0}, {'heal': 2.8, 'buffDur': 4.0}]
lb['desc'] = T("Soigne un peu, retire tous les effets négatifs des monstres et du terrain, et donne +15 % de vitesse et +10 de résistance un moment. Immunisé aux effets négatifs pendant 1 s.",
               "Heals a little, removes every negative effect from monsters and the ground, and gives +15% speed and +10 resistance for a while. Immune to negative effects for 1 s.",
               "Heilt ein wenig, entfernt alle negativen Effekte von Monstern und Gelände und gibt eine Weile +15 % Tempo und +10 Resistenz. 1 s immun gegen negative Effekte.",
               "Cura un poco, quita todos los efectos negativos de monstruos y terreno, y da +15 % de velocidad y +10 de resistencia un rato. Inmune a efectos negativos durante 1 s.",
               "Cura un po', rimuove ogni effetto negativo di mostri e terreno, e dà +15% di velocità e +10 di resistenza per un po'. Immune agli effetti negativi per 1 s.",
               "Geneest een beetje, verwijdert alle negatieve effecten van monsters en terrein, en geeft even +15% snelheid en +10 weerstand. 1 s immuun voor negatieve effecten.",
               "Cura um pouco, remove todos os efeitos negativos de monstros e terreno, e dá +15% de velocidade e +10 de resistência por um tempo. Imune a efeitos negativos por 1 s.")

# Force and Point d'action: half their total; every cooldown 5 % shorter; +0.1 % damage per level gained in a run (10 % max)
PAS['force']['per'] = 0.05
PAS['force']['desc'] = T('+5 % de dégâts par niveau.', '+5% damage per level.', '+5 % Schaden pro Stufe.', '+5 % de daño por nivel.',
                         '+5% di danni per livello.', '+5% schade per niveau.', '+5% de dano por nível.')
PAS['pa']['per'] = -0.035
PAS['pa']['desc'] = T('-3,5 % de temps de recharge des sorts par niveau.', '-3.5% spell cooldown per level.', '-3,5 % Abklingzeit der Zauber pro Stufe.',
                      '-3,5 % de tiempo de recarga de los hechizos por nivel.', '-3,5% di tempo di ricarica degli incantesimi per livello.',
                      '-3,5% hersteltijd van spreuken per niveau.', '-3,5% de tempo de recarga dos feitiços por nível.')
C['run']['cdMul'] = round(C['run']['cdMul'] * 0.95, 6)
C['run']['lvDmg'] = 0.001; C['run']['lvDmgMax'] = 0.10
# Intelligence: 50 % at most with every level and the whole shop (5 levels × (1 + 5 × spellPer))
PAS['intelligence']['per'] = round(0.5 / (5 * (1 + 5 * C.get('spellPer', 0.1))), 4)
PAS['intelligence']['desc'] = T('+6,7 % de zone d\'effet par niveau.', '+6.7% area of effect per level.', '+6,7 % Wirkungsbereich pro Stufe.',
                                '+6,7 % de área de efecto por nivel.', '+6,7% di area d\'effetto per livello.', '+6,7% effectgebied per niveau.', '+6,7% de área de efeito por nível.')
# scrolls: Intelligence 10 % area and 10 % heals at most, Sagesse 20 % experience and 5 % spell block
SCR['intelligence']['per'] = {'area': 0.01, 'healBonus': 0.01}; SCR['intelligence']['totN'] = [1, 1]
SCR['intelligence']['desc'] = T('+1 % de zone d\'effet et +1 % de soins par niveau, pour tous vos personnages.', '+1% area of effect and +1% healing per level, for all your characters.',
                                '+1 % Wirkungsbereich und +1 % Heilung pro Stufe, für alle Charaktere.', '+1 % de área de efecto y +1 % de curación por nivel, para todos tus personajes.',
                                '+1% di area d\'effetto e +1% di cure per livello, per tutti i personaggi.', '+1% effectgebied en +1% genezing per niveau, voor al je personages.',
                                '+1% de área de efeito e +1% de cura por nível, para todos os personagens.')
SCR['sagesse']['per'] = {'growth': 0.02, 'pblock': 0.005}; SCR['sagesse']['totN'] = [2, 0.5]
SCR['sagesse']['desc'] = T("+2 % d'expérience et +0,5 % de blocage des sorts à distance par niveau, pour tous vos personnages.", '+2% experience and +0.5% ranged spell block per level, for all your characters.',
                           '+2 % Erfahrung und +0,5 % Fernzauberabwehr pro Stufe, für alle Charaktere.', '+2 % de experiencia y +0,5 % de bloqueo de hechizos a distancia por nivel, para todos tus personajes.',
                           '+2% di esperienza e +0,5% di blocco degli incantesimi a distanza per livello, per tutti i personaggi.', '+2% ervaring en +0,5% blokkade van afstandsspreuken per niveau, voor al je personages.',
                           '+2% de experiência e +0,5% de bloqueio de feitiços à distância por nível, para todos os personagens.')
# weapon masteries: +35 % at 5/5 (was 25 %)
C['masteryPer'] = 0.07
put_ui({'mastery_intro': T("Chaque niveau de Maîtrise ajoute +7 % aux dégâts de ce type d'arme, jusqu'à 5 niveaux. Le mannequin d'entraînement n'a toujours rien demandé.",
                           "Each Mastery level adds +7% to this weapon type's damage, up to 5 levels. The training dummy still didn't ask for any of this.",
                           'Jede Meisterschaftsstufe gibt +7 % Schaden für diesen Waffentyp, bis zu 5 Stufen. Die Trainingspuppe hat immer noch nicht darum gebeten.',
                           'Cada nivel de Maestría añade +7 % al daño de este tipo de arma, hasta 5 niveles. El muñeco de entrenamiento sigue sin pedir nada.',
                           "Ogni livello di Maestria aggiunge +7% ai danni di questo tipo d'arma, fino a 5 livelli. Il manichino non ha ancora chiesto niente.",
                           'Elk Meesterschapsniveau geeft +7% schade aan dit type wapen, tot 5 niveaus. De oefenpop heeft nog steeds nergens om gevraagd.',
                           'Cada nível de Maestria soma +7% ao dano deste tipo de arma, até 5 níveis. O boneco de treino continua sem pedir nada.')})
# Portée also helps the summons (game.js spawnSummon / updateSummons: faster, see and shoot farther)
PAS['portee']['desc'] = T('+10 % de vitesse et de portée des projectiles par niveau. Vos invocations vont plus vite et voient plus loin.',
                          '+10% projectile speed and range per level. Your summons move faster and see farther.',
                          '+10 % Tempo und Reichweite der Geschosse pro Stufe. Deine Beschwörungen sind schneller und sehen weiter.',
                          '+10 % de velocidad y alcance de los proyectiles por nivel. Tus invocaciones van más rápido y ven más lejos.',
                          '+10% di velocità e portata dei proiettili per livello. Le tue evocazioni vanno più veloci e vedono più lontano.',
                          '+10% snelheid en bereik van projectielen per niveau. Je oproepingen bewegen sneller en zien verder.',
                          '+10% de velocidade e alcance dos projéteis por nível. Suas invocações andam mais rápido e veem mais longe.')

# the characteristics' icons of the up-to-date client's stats window (tools/assets/build_staticons068.py): Vitalité, Sagesse (the
# violet ring), PA, PM, Résistances (neutral resistance), Portée = the original spyglass picture
for pid, ic in (('vitalite', 'vita'), ('sagesse', 'wisdom'), ('pa', 'ap'), ('pm', 'mp'), ('resistances', 'neutral'), ('portee', 'range'),
                ('force', 'earth'), ('intelligence', 'fire'), ('chance', 'water'), ('agilite', 'air')):   # (0.71: the four elements too)
    PAS[pid]['icon'] = 'Icon_c_' + ic

# the waves: fewer, irregular, bigger and packed (game.js spawner): every 2.5-4.5 times the old interval, as many monsters a
# minute on average
C['run']['packT'] = [2.5, 4.5]

# ------------------------------------------------------------------ Osamodas fusions
# the whip fusion casts Crackler strikes (the Osamodas spell Frappe du Craqueleur, client clip 212) on the crowd it hits
fm = S['fu_osa_marteau']['base']
for k in ('rStun', 'rStunP'): fm.pop(k, None)
fm.update(rCraq=0.7, rCraqN=3, rCraqR=70, rCraqStun=0.4, rCraqCd=0.45)
S['fu_osa_marteau']['desc'] = T("Le fouet claque des quatre côtés et fait jaillir des Frappes du Craqueleur sous les monstres touchés. Ça claque, ça craque, ça vole.",
                                "The whip cracks on all four sides and makes Crackler Strikes burst out under the monsters it hits. Crack, crack, fly.",
                                "Die Peitsche knallt in alle vier Richtungen und lässt Krachlerschläge unter den getroffenen Monstern hervorbrechen. Knall, Krach, Flug.",
                                "El látigo restalla por los cuatro lados y hace brotar Golpes del Crujidor bajo los monstruos que toca. Crac, crac, a volar.",
                                "La frusta schiocca sui quattro lati e fa esplodere Colpi del Croccaroc sotto i mostri colpiti. Schiocca, crocca, vola.",
                                "De zweep knalt aan alle vier de kanten en laat Kraklerslagen opspringen onder de geraakte monsters. Knal, krak, weg.",
                                "O chicote estala nos quatro lados e faz surgir Golpes do Crackler sob os monstros atingidos. Estala, racha, voa.")
# Bénédiction Animale: Boufcouls instead of Bouftous (client sprite 1355, tools/assets/build_mobs20.py 1355:z=3.0), their blows hit
# around their target; no more paw-print blasts (fx 213) covering the screen
fb = S['fu_osa_bouftou']; b = fb['base']
for k in ('rBlast', 'rBlastR', 'rBlastP'): b.pop(k, None)
b.update(sprite=1355, spriteKey='1355_z30', aoe=45)
fb['fx'] = [1100]; fb['fx2'] = None
fb['desc'] = T("Vos Bouftous deviennent des Boufcouls : plus nombreux, plus solides, et chaque coup de tête cogne tous les monstres autour. Bêêê… BAM.",
               "Your Gobballs become Gobkools: more of them, sturdier, and every headbutt bashes every monster around. Baaa… BAM.",
               "Deine Fresssäcke werden Fresscools: mehr, zäher, und jeder Kopfstoß trifft alle Monster ringsum. Määäh… BAM.",
               "Tus Jalatos se vuelven Jalatrankis: más numerosos, más fuertes, y cada cabezazo golpea a todos los monstruos alrededor. Beee… ¡BAM!",
               "I tuoi Mangiabù diventano Pappacool: più numerosi, più robusti, e ogni testata colpisce tutti i mostri intorno. Beee… BAM.",
               "Je Schapen worden Gobkools: meer, steviger, en elke kopstoot raakt alle monsters rondom. Bèèè… BAM.",
               "Seus Papatudos viram Gobkools: mais numerosos, mais fortes, e cada cabeçada acerta todos os monstros ao redor. Béé… BAM.")
C.setdefault('summonSnd', {})
if 'invoc_bouftou' in C['summonSnd']: C['summonSnd']['fu_osa_bouftou'] = C['summonSnd']['invoc_bouftou']

# ------------------------------------------------------------------ shorter statistics labels (room)
put_ui({
    'st_dmg_dealt': T('Dégâts', 'Damage', 'Schaden', 'Daño', 'Danni', 'Schade', 'Dano'),
    'ov_dealt': T('Dégâts', 'Damage', 'Schaden', 'Daño', 'Danni', 'Schade', 'Dano'),
    'st_kills': T('Monstres tués', 'Monsters killed', 'Getötete Monster', 'Monstruos muertos', 'Mostri uccisi', 'Gedode monsters', 'Monstros mortos'),
    'st_bosses': T('Boss tués', 'Bosses killed', 'Getötete Bosse', 'Jefes muertos', 'Boss uccisi', 'Gedode bazen', 'Chefes mortos'),
    'ov_bosses': T('Boss tués', 'Bosses killed', 'Getötete Bosse', 'Jefes muertos', 'Boss uccisi', 'Gedode bazen', 'Chefes mortos'),
    'st_elites': T('Élites tués', 'Elites killed', 'Getötete Eliten', 'Élites muertos', 'Élite uccisi', 'Gedode elites', 'Elites mortos'),
    'st_gems': T('Ambres', 'Ambers', 'Bernsteine', 'Ámbares', 'Ambre', 'Barnstenen', 'Âmbares'),
    'st_chests': T('Coffres', 'Chests', 'Truhen', 'Cofres', 'Forzieri', 'Kisten', 'Baús'),
    'st_breads': T('Pains', 'Bread', 'Brote', 'Panes', 'Pani', 'Broden', 'Pães'),
    'st_dofus': T('Dofus', 'Dofus', 'Dofus', 'Dofus', 'Dofus', 'Dofus', 'Dofus'),
    'st_runs': T('Parties', 'Runs', 'Läufe', 'Partidas', 'Partite', 'Runs', 'Partidas'),
    'st_levelups': T('Niveaux', 'Levels', 'Stufen', 'Niveles', 'Livelli', 'Levels', 'Níveis'),
    'st_rerolls': T('Relances', 'Rerolls', 'Würfe', 'Tiradas', 'Rilanci', 'Worpen', 'Rolagens'),
    'st_tot': T('ToT battu', 'ToT beaten', 'ToT besiegt', 'ToT vencido', 'ToT battuto', 'ToT verslagen', 'ToT vencido'),
    'st_kamas_earned': T('Kamas gagnés', 'Kamas earned', 'Kamas verdient', 'Kamas ganados', 'Kama vinti', 'Kama verdiend', 'Kamas ganhos'),
    'st_kamas_spent': T('Kamas dépensés', 'Kamas spent', 'Kamas ausgegeben', 'Kamas gastados', 'Kama spesi', 'Kama uitgegeven', 'Kamas gastos'),
})

# L'île de Nowel: no kamas at all, no merchant; a big gift every 4 minutes (twice) holding a hat or a cape; the
# final boss drops the Trool fair ticket = a wheel of skins (game/js/nowel.js)
KW = next(m for m in C['maps'] if m['id'] == 'kwismas')
KW.update(noKamas=1, noMerchant=1, nowel={'every': 240, 'n': 2}, troolTicket=1)
put_ui({
    'nowel_gift_here': T('Un Cadeau de Nowel potentiellement surpuissant est tombé du ciel !', 'A Potentially Overpowered Kwismas Present fell from the sky!',
                         'Ein potenziell übermächtiges Nowel-Geschenk ist vom Himmel gefallen!', '¡Un Regalo de Nowel potencialmente superpoderoso ha caído del cielo!',
                         'Un Regalo di Nowel potenzialmente strapotente è caduto dal cielo!', 'Een mogelijk overpowered Nowelcadeau is uit de lucht gevallen!',
                         'Um Presente de Nowel potencialmente superpoderoso caiu do céu!'),
    'nowel_gift': T('Cadeau de Nowel !', 'Kwismas Present!', 'Nowel-Geschenk!', '¡Regalo de Nowel!', 'Regalo di Nowel!', 'Nowelcadeau!', 'Presente de Nowel!'),
    'nowel_gift_got': T('Skin débloqué : {n} !', 'Skin unlocked: {n}!', 'Skin freigeschaltet: {n}!', '¡Skin desbloqueado: {n}!', 'Skin sbloccata: {n}!', 'Skin ontgrendeld: {n}!', 'Skin desbloqueada: {n}!'),
    'nowel_all': T('Tu as déjà tous les skins ! Le Papa Nowel est impressionné.', 'You already own every skin! Papa Nowel is impressed.', 'Du hast schon alle Skins! Papa Nowel ist beeindruckt.',
                   '¡Ya tienes todos los skins! Papá Nowel está impresionado.', 'Hai già tutte le skin! Babbo Nowel è colpito.', 'Je hebt alle skins al! Papa Nowel is onder de indruk.', 'Já tens todas as skins! O Pai Nowel está impressionado.'),
    'nowel_wheel': T('Ticket de la foire du Trool', 'Trool Fair Ticket', 'Ticket der Trool-Kirmes', 'Ticket de la feria del Trool', 'Biglietto della fiera del Trool', 'Ticket van de Troolkermis', 'Bilhete da feira do Trool'),
})

# 0.71: Frappe du Craqueleur is no whip any more: only its area — the Craqueleurs' rocks falling on the crowd
# (strikes with rock 1, the client's rockfall clip 1003 in HD), damage raised to keep its strength
FM = S['fu_osa_marteau']; FM.update(t='strike', fx=['212f', 1003], fx2=212, snd='impact_lourd'); FM.pop('whip', None)   # (0.74: the client's stone fist, tools/assets/build_fist073.py)
FM['base'] = dict(dmg=CRAQ_DMG, count=4, radius=72, delay=0.9, cd=1.5, stun=0.5, shake=3, target='random', color='#c8b89a', fist=1)

S['prouts']['name'] = T('Pwout de Cawotte', 'Cawwot Fawt', 'Kawotten-Pups', 'Pedo de Zanahowia', 'Peto di Cawota', 'Wortewscheet', 'Pum de Cenouwa')   # (0.73)
S['prouts']['desc'] = T("Un nuage orange qui sent la cawotte blesse les monstres autour de vous. Des cawottes tournent dedans, personne ne sait pourquoi.",
    "An orange cloud smelling of cawwots hurts the monsters around you. Cawwots spin in it, nobody knows why.",
    "Eine orange Wolke, die nach Kawotten riecht, verletzt die Monster um dich herum. Kawotten drehen sich darin, keiner weiß warum.",
    "Una nube naranja con olor a zanahowia hiere a los monstruos a tu alrededor. Dentro giran zanahowias, nadie sabe por qué.",
    "Una nuvola arancione che sa di cawota ferisce i mostri intorno a te. Dentro girano cawote, nessuno sa perché.",
    "Een oranje wolk die naar wortews ruikt verwondt de monsters om je heen. Er draaien wortews in rond, niemand weet waarom.",
    "Uma nuvem laranja que cheira a cenouwa fere os monstros à tua volta. Lá dentro giram cenouwas, ninguém sabe porquê.")
S['fu_pan_souffle']['desc'] = T("Des flasques qui explosent et laissent un Pwout de Cawotte bien orange. Ne pas allumer de bougie.",
    "Flasks that explode and leave a very orange Cawwot Fawt behind. Do not light a candle.",
    "Flaschen, die explodieren und einen knallorangen Kawotten-Pups hinterlassen. Keine Kerze anzünden.",
    "Frascos que explotan y dejan un Pedo de Zanahowia bien naranja. No encender velas.",
    "Fiaschette che esplodono e lasciano un Peto di Cawota bello arancione. Non accendere candele.",
    "Flessen die ontploffen en een knaloranje Wortewscheet achterlaten. Geen kaars aansteken.",
    "Frascos que explodem e deixam um Pum de Cenouwa bem laranja. Não acender velas.")
S['prouts']['base']['color'] = '#b0420c'   # (0.71: dark orange zone; render.js orangePuff + spinning cawottes)

# 0.71: new global spell 'Cawotte' (gspells.js cawotte): a Cawotte on a red cross of cells, cawottes spinning;
# 1 HP/s, 25 s, 5 s → 1.75 HP/s, 18 s, 8 s with the whole shop
S['cawotte'] = dict(id='cawotte', t='cawotte', glob=1, sid=0, anim=None, animAll='anim1', fx=[], icon='g_cawotte', snd='saut',
    name=T('Cawotte', 'Cawwot', 'Kawotte', 'Zanahowia', 'Cawota', 'Wortew', 'Cenouwa'),
    desc=T("Une Cawotte jaillit sous vos pieds sur une croix de cases : restez dessus pour vous soigner. Le Wa Wabbit en pleure encore.",
           "A Cawwot springs up under your feet on a cross of cells: stand on it to heal. The Wa Wabbit still cries about it.",
           "Eine Kawotte springt unter deinen Füßen auf einem Kreuz aus Feldern hervor: bleib darauf, um dich zu heilen. Der Wa Wabbit weint noch.",
           "Una Zanahowia brota bajo tus pies sobre una cruz de casillas: quédate encima para curarte. El Wa Wabbit aún llora.",
           "Una Cawota spunta sotto i tuoi piedi su una croce di caselle: restaci sopra per curarti. Il Wa Wabbit piange ancora.",
           "Een Wortew schiet onder je voeten op uit een kruis van vakjes: blijf erop staan om te genezen. De Wa Wabbit huilt er nog om.",
           "Uma Cenouwa brota debaixo dos teus pés numa cruz de casas: fica em cima para te curares. O Wa Wabbit ainda chora."),
    base=dict(heal=1.0, healShop=1.75, cd=round(25.0 / C['run']['cdMul'], 3), cdShop=round(18.0 / C['run']['cdMul'], 3), duration=5.0, durShop=8.0, radius=150),   # (0.74: twice as wide)   # (cdMul is applied on top: 25 s / 18 s on screen)
    lv=[{}, {'radius': 164}, {'heal': 1.1, 'healShop': 1.9}, {'radius': 180}, {'duration': 5.5, 'durShop': 8.5}, {'heal': 1.2, 'healShop': 2.0, 'radius': 196}])
if not any(g['id'] == 'cawotte' for g in C['globalSpells']): C['globalSpells'].append({'id': 'cawotte', 'w': 0.8})

# the Hidden Kwak Nest: a secret zone, 5th in the list, opened by beating ToT once (tools/content/kwaknest068.py)
import kwaknest068
kwaknest068.apply(C, T, put_ui)

# the weapon fusions' badges follow the characteristics' icons (0.71: the old yin-yang / XP pictures were left)
PI = {p['id']: p['icon'] for p in C['passives']}
for f in C.get('fusions') or []:
    k = f.get('stat') or ('sagesse' if f['id'] == 'brute' else f['id'])
    if f['id'] == 'brute': f['icon'] = PI.get('force', f['icon'])
    elif k in PI: f['icon'] = PI[k]

# 0.71: no Mulous in the Porcos' territory any more: the pigs of the Dragon Cochon's dungeon instead
PIGS = {'mulou': 'cochon_de_farle', 'milimulou': 'cochon_de_lait'}
for m in C['maps']:
    if m['id'] != 'porco': continue
    for w in m['waves']:
        tot = {}
        for mid, n in w[2]: k = PIGS.get(mid, mid); tot[k] = tot.get(k, 0) + n
        w[2] = [[k, n] for k, n in tot.items()]
    m['events'] = [[t, kind, PIGS.get(mob, mob), n] for t, kind, mob, n in m['events']]
    m['rare'] = [r for r in m.get('rare') or [] if r[0] not in PIGS]

# 0.71: bosses in crescendo along the zones' order — the final boss 8 000 + 1 000 per place (a group of final bosses
# shares that life; Goultard keeps his 32 000 at least), the mini-bosses 45 % and 70 % of it (never more than the final
# boss), the final bosses' XP gem 3 times the mini-bosses'; ambers -10 % everywhere but the first three zones
r500 = lambda v: int(round(v / 500.0) * 500)
for i, m in enumerate(C['maps']):
    fin = max(8000 + 1000 * i, 32000 if m['id'] == 'goultard' else 0)
    finals = [b for _, b in m['bosses'] if C['bosses'][b].get('final')]; minis = [b for _, b in m['bosses'] if not C['bosses'][b].get('final')]
    for b in finals: C['bosses'][b]['hp'] = r500(fin / len(finals)); C['bosses'][b]['xp'] = round(45.0 / len(finals), 2)
    for k, b in enumerate(minis): C['bosses'][b]['hp'] = r500(fin * (0.45, 0.70)[min(k, 1)]); C['bosses'][b]['xp'] = (14.0, 18.0)[min(k, 1)]
C['run']['xpPace'] = round(C['run']['xpPace'] * 0.9, 4)
for m in C['maps'][:3]:
    for n in m['norm']: n[4] = round(n[4] / 0.9, 4)

# Musha l'Oni changes the subject: a true anecdote about the treasure's zone after his 2nd line (ui_events.js)
import anec068
C['tmap']['anec'] = anec068.ANEC
C['tmap']['ghost'] = anec068.GHOST   # (the dug treasure's cinematic, events.js drawTreasure)

# 0.73: the grades are A to F (his medallions assets/ui/rank_<L>.webp): A = the old S, B = A, C = B, D = C, E = D, F new
for lg in C['ui']:
    U_ = C['ui'][lg]; old = {g: U_.get('ov_grade_' + g) for g in 'SABCD'}
    if old['S'] and not U_.get('ov_grade_F'):
        for new, o in zip('ABCDE', 'SABCD'): U_['ov_grade_' + new] = old[o]
put_ui({'ov_grade_F': T("Le Tofu s'est assis pour regarder. Il n'a pas eu le temps de finir son pain.", "The Tofu sat down to watch. It didn't even finish its bread.",
                        "Der Tofu hat sich zum Zuschauen hingesetzt. Er hat nicht mal sein Brot aufgegessen.", "El Tofu se sentó a mirar. Ni le dio tiempo a terminar su pan.",
                        "Il Tofu si è seduto a guardare. Non ha nemmeno finito il suo pane.", "De Tofu ging zitten om te kijken. Hij had zijn brood nog niet op.",
                        "O Tofu sentou-se a ver. Nem teve tempo de acabar o pão.")})

# 0.73: no global cooldown multiplier any more: every spell's / weapon's cooldown takes it in (what the game showed
# becomes the written value), then run.cdMul = 1
def _bake(o, k, inmul=False):
    if isinstance(o, dict):
        for key, v in o.items():
            if key in ('cd', 'cdShop') and isinstance(v, (int, float)) and not isinstance(v, bool) and not inmul: o[key] = round(v * k, 3)
            elif key != 'abilities': _bake(v, k, inmul or key == 'mul')
    elif isinstance(o, list):
        for v in o: _bake(v, k, inmul)
_K = C['run'].get('cdMul', 1)
if _K != 1:
    for sec in ('spells', 'weapons', 'uniqueWeapons', 'weaponEvo'): _bake(C.get(sec), _K)
    C['run']['cdMul'] = 1

if __name__ == '__main__':
    json.dump(C, open(f'{G}/data/content.json', 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
    print('0.68 ok')
