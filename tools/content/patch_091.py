"""0.91 content: a new playable class, the Otomaï — the alchemist NPC of the client (sprite 9066, NPC 914, a Crâ
skeleton: runs / standing / casts / blows / death rendered from the up-to-date client like the other classes). Alchemy,
potions, mutations and the creatures of his island, with the game's own spell types (no system of its own):
- oto_fiole        Fiole Corrosive      projectile `lob` (the client item Impressionnante potion d'agression it_14_35, spinning), burst + a green
                                        puddle that poisons (`puddlePoison`, `puddleDur`: game.js explode / zone tick)
- oto_vapeurs      Brume Mutagène       aura: slow + `mark` (monsters in it take more damage) + `mist` puffs (render.js)
- oto_mutation     Élixir de Mutation   buff 'mutate': `power` (damage), `haste` (run speed), the character grows
- oto_kido         Appel des Kidos      summon: the Kidos of Otomaï island (monster sheet 1628_z32)
- oto_transmutation Transmutation       strike on a group: ordinary monsters left under `transmute` of their life
                                        turn into gold, its kills drop kamas `gold` of the time (Run.transmute)
- oto_potion       Potion de Soin       heal + `armorBuff`
Passive Alchimie: +20 % of the effects' durations (`passiveStats.duration`). Fusions (fusions060 pattern, riders):
Venin Déstabilisateur (fiole + brume, spell), Grand Œuvre (transmutation + baguette, weapon), Mutagen (kidos + Tofus
kamikazes, global). The class casts anim4 (rummaging in his potion bag) / anim3 (kneeling) — the NPC's anim2 is the
Crâ's bow — played 1.6x faster (`castRate`: they last 1.6-1.9 s in the client), eats with anim4 (`eatAnim`), keeps the
NPC's own colours and wears no hat / cape (`nocolors`, `nohats`, like the Roublard and the Brigandin: his sheets are
rendered in the sprite's colours, build_otomai091 orig), his island's music as his theme (`theme`). Assets: tools/assets/build_otomai091.py (icons, fusion icons, emblem b15, sounds).
usage: PYTHONUTF8=1 python tools/content/patch_091.py  (imports patch_089, writes game/data/content.json)"""
import sys as _sys, os as _os, json, copy
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
import _root
import patch_089 as P9
import fusions060 as F6

C, G, T, put_ui = P9.C, P9.G, P9.T, P9.put_ui
S = C['spells']
LG = ['fr', 'en', 'de', 'es', 'it', 'nl', 'pt']
npc = {lg: json.load(open(f'{_root.ROOT}/work/lang_json/npc_{lg}.json', encoding='utf-8'))['N']['d']['914']['n'] for lg in LG}

# the client print of each spell's icon (clips/spells/icons/up/<n>.swf) -> 'sp_oto_<n>' (build_otomai091)
ICONS = {'oto_fiole': 336, 'oto_vapeurs': 483, 'oto_mutation': 593, 'oto_kido': 417, 'oto_transmutation': 516, 'oto_potion': 127}
FICONS = {'fu_oto_venin': 386, 'fu_oto_oeuvre': 497, 'fu_oto_mutagen': 613}


def spell(sid, name, t, anim, fx, desc, base, lv, **extra):
    d = dict(id=sid, name=name, t=t, anim=anim, fx=fx, icon=f'oto_{ICONS[sid]}', desc=desc, base=base, lv=lv)
    d.update(extra); S[sid] = d


spell('oto_fiole', T('Fiole Corrosive', 'Corrosive Phial', 'Ätzende Phiole', 'Frasco Corrosivo', 'Fiala Corrosiva', 'Bijtende Flacon', 'Frasco Corrosivo'),
      'projectile', 'anim4', [1011],
      T("Une fiole d'acide lancée en cloche éclate sur les monstres et laisse une flaque qui les empoisonne.",
        "A phial of acid lobbed at the monsters shatters and leaves a puddle that poisons them.",
        "Eine im Bogen geworfene Säurephiole zerplatzt bei den Monstern und hinterlässt eine giftige Pfütze.",
        "Un frasco de ácido lanzado en parábola estalla sobre los monstruos y deja un charco que los envenena.",
        "Una fiala d'acido lanciata a parabola esplode sui mostri e lascia una pozza che li avvelena.",
        "Een met een boog gegooide flacon zuur spat uiteen op de monsters en laat een vergiftigende plas achter.",
        "Um frasco de ácido lançado em arco rebenta sobre os monstros e deixa uma poça que os envenena."),
      {'dmg': 16.0, 'count': 1, 'speed': 240, 'cd': 4.2, 'pierce': 1, 'size': 12, 'life': 1.2, 'target': 'nearest', 'aoe': 58, 'lob': 1,
       'puddle': 1, 'puddleColor': '#7ed957', 'slow': 0.2, 'puddlePoison': 2.0, 'puddleDur': 3.0, 'drawIcon': 'it_14_35', 'col': 'rgba(126,217,87,0.55)'},
      [{}, {'aoe': 66, 'dmg': 22.0, 'puddlePoison': 2.8}, {'count': 2, 'dmg': 29.0, 'aoe': 74, 'puddlePoison': 3.6}, {'count': 3, 'dmg': 38.0, 'puddlePoison': 4.8}],
      snd='panda_molotov')
spell('oto_vapeurs', T('Brume Mutagène', 'Mutagenic Mist', 'Mutagener Nebel', 'Bruma Mutágena', 'Bruma Mutagena', 'Mutagene Nevel', 'Bruma Mutagênica'),
      'aura', 'anim4', [],
      T("Une brume verdâtre entoure l'Otomaï : les monstres qui la respirent ralentissent et encaissent plus de dégâts.",
        "A greenish mist surrounds the Otomai: monsters breathing it slow down and take more damage.",
        "Ein grünlicher Nebel umgibt den Otomai: Monster, die ihn einatmen, werden langsamer und nehmen mehr Schaden.",
        "Una bruma verdosa rodea al Otomai: los monstruos que la respiran se ralentizan y reciben más daño.",
        "Una bruma verdastra avvolge l'Otomai: i mostri che la respirano rallentano e subiscono più danni.",
        "Een groenige nevel omringt de Otomai: monsters die hem inademen worden trager en lopen meer schade op.",
        "Uma bruma esverdeada envolve o Otomai: os monstros que a respiram abrandam e sofrem mais dano."),
      {'dmg': 2.5, 'radius': 85, 'tick': 0.5, 'slow': 0.15, 'mark': 0.08, 'cd': 0.0, 'color': '#8fd45a', 'mist': 1},
      [{}, {'radius': 95, 'mark': 0.1, 'dmg': 3.2}, {'radius': 105, 'mark': 0.12, 'slow': 0.2, 'dmg': 4.0}, {'radius': 115, 'mark': 0.15, 'slow': 0.25, 'dmg': 5.0}])
spell('oto_mutation', T('Élixir de Mutation', 'Mutation Elixir', 'Mutationselixier', 'Elixir de Mutación', 'Elisir di Mutazione', 'Mutatie-elixer', 'Elixir de Mutação'),
      'buff', 'anim4', [707],
      T("L'Otomaï avale son élixir et mute : il grandit, frappe plus fort et court plus vite un moment.",
        "The Otomai gulps down his elixir and mutates: he grows, hits harder and runs faster for a while.",
        "Der Otomai schluckt sein Elixier und mutiert: Er wächst, schlägt härter zu und läuft eine Weile schneller.",
        "El Otomai se bebe su elixir y muta: crece, golpea más fuerte y corre más rápido durante un rato.",
        "L'Otomai trangugia il suo elisir e muta: cresce, colpisce più forte e corre più veloce per un po'.",
        "De Otomai slokt zijn elixer op en muteert: hij groeit, slaat harder en rent een tijdje sneller.",
        "O Otomai bebe o seu elixir e sofre uma mutação: cresce, bate com mais força e corre mais depressa por um tempo."),
      {'buff': 'mutate', 'duration': 5.0, 'cd': 18.0, 'power': 0.2, 'haste': 0.12},
      [{}, {'power': 0.25, 'duration': 6.0}, {'power': 0.3, 'haste': 0.15, 'cd': 16.0}, {'power': 0.4, 'haste': 0.2, 'duration': 7.0}],
      snd='gonfle')
spell('oto_kido', T('Appel des Kidos', 'Call of the Kidos', 'Ruf der Kidos', 'Llamada de los Kidos', 'Richiamo dei Kido', "Roep van de Kido's", 'Chamado dos Kidos'),
      'summon', 'anim3', [1100],
      T("Des Kidos de l'île d'Otomaï accourent et mordillent les monstres. Ils ont toujours faim.",
        "Kidos from Otomai Island come running and nibble at the monsters. They're always hungry.",
        "Kidos von der Insel Otomai eilen herbei und knabbern an den Monstern. Sie haben immer Hunger.",
        "Kidos de la isla de Otomai acuden corriendo y mordisquean a los monstruos. Siempre tienen hambre.",
        "Dei Kido dell'isola di Otomai accorrono e mordicchiano i mostri. Hanno sempre fame.",
        "Kido's van het eiland Otomai komen aangerend en knabbelen aan de monsters. Ze hebben altijd honger.",
        "Kidos da ilha de Otomai acorrem e mordiscam os monstros. Estão sempre com fome."),
      {'dmg': 8.0, 'count': 2, 'hp': 55, 'speed': 175, 'duration': 11.0, 'cd': 12.2, 'sprite': 1628, 'hitcd': 0.35, 'spriteKey': '1628_z32'},
      [{}, {'dmg': 12.0, 'count': 3}, {'hp': 90, 'duration': 13.0, 'dmg': 16.5}, {'count': 4, 'dmg': 22.0}])
spell('oto_transmutation', T('Transmutation', 'Transmutation', 'Transmutation', 'Transmutación', 'Trasmutazione', 'Transmutatie', 'Transmutação'),
      'strike', 'anim3', [2004],
      T("Un cercle alchimique s'abat sur un groupe : les monstres trop affaiblis sont changés en or, et l'or, ça se ramasse.",
        "An alchemical circle strikes a group: monsters left too weak turn into gold, and gold can be picked up.",
        "Ein alchemistischer Kreis trifft eine Gruppe: Zu geschwächte Monster werden zu Gold, und Gold kann man aufheben.",
        "Un círculo alquímico golpea a un grupo: los monstruos demasiado débiles se convierten en oro, y el oro se recoge.",
        "Un cerchio alchemico colpisce un gruppo: i mostri troppo indeboliti diventano oro, e l'oro si raccoglie.",
        "Een alchemistische cirkel treft een groep: te verzwakte monsters veranderen in goud, en goud raap je op.",
        "Um círculo alquímico atinge um grupo: os monstros demasiado fracos transformam-se em ouro, e o ouro apanha-se."),
      {'dmg': 22.0, 'count': 1, 'radius': 72, 'delay': 0.6, 'cd': 6.3, 'target': 'cluster', 'transmute': 0.12, 'gold': 0.08, 'color': '#ffd54a'},
      [{}, {'radius': 80, 'dmg': 26.0, 'transmute': 0.15}, {'count': 2, 'dmg': 34.0, 'radius': 88}, {'count': 3, 'dmg': 43.0, 'transmute': 0.2, 'gold': 0.12}],
      snd='stars')
spell('oto_potion', T('Potion de Soin', 'Healing Potion', 'Heiltrank', 'Poción de Curación', 'Pozione Curativa', 'Genezingsdrank', 'Poção de Cura'),
      'heal', 'anim4', [301],
      T("Une bonne gorgée de potion : l'Otomaï récupère des points de vie et sa peau durcit un instant.",
        "A good swig of potion: the Otomai recovers health and his skin hardens for a moment.",
        "Ein kräftiger Schluck Trank: Der Otomai erhält Lebenspunkte zurück und seine Haut härtet kurz aus.",
        "Un buen trago de poción: el Otomai recupera vida y su piel se endurece un instante.",
        "Un bel sorso di pozione: l'Otomai recupera punti vita e la sua pelle si indurisce per un attimo.",
        "Een flinke slok drank: de Otomai krijgt levenspunten terug en zijn huid wordt even harder.",
        "Um bom gole de poção: o Otomai recupera vida e a pele endurece por um instante."),
      {'heal': 4.5, 'cd': 15.0, 'armorBuff': 3, 'buffDur': 3.0},
      [{}, {'heal': 6.0, 'cd': 13.0}, {'heal': 8.0, 'armorBuff': 4, 'cd': 11.5}, {'heal': 9.5, 'cd': 10.0, 'buffDur': 4.0}],
      snd='panda_gloups')

C['classes'] = [c for c in C['classes'] if c['id'] != 'otomai'] + [{
    'id': 'otomai', 'name': npc, 'breed': 15, 'sprites': [9066, 9066], 'casts': ['anim4', 'anim3'], 'castRate': 1.6, 'eatAnim': 'anim4',
    'color': '#2f8f8a', 'nocolors': 1, 'nohats': 1, 'theme': 'loc_otomai', 'emblemArt': 'b15',   # (his own colours, no skins, like the Roublard / Brigandin)
    'base': {'hp': 64, 'speed': 1.03, 'might': 1.092, 'armor': 0, 'regen': 0.1},
    'passive': T('Alchimie : +20 % de durée des effets.', 'Alchemy: +20% effect duration.', 'Alchemie: +20 % Effektdauer.',
                 'Alquimia: +20 % de duración de los efectos.', "Alchimia: +20% di durata degli effetti.", 'Alchemie: +20% duur van effecten.',
                 'Alquimia: +20% de duração dos efeitos.'),
    'passiveStats': {'duration': 0.2},
    'spells': list(ICONS)}]

# ---------------------------------------------------------------- the three fusions (fusions060's pattern: the main
# ingredient at its last level + changes + a rider, damage set so that it beats what it replaces — see the 0.91 notes)
def fusion(fid, a, b, kind, name, desc, ch, rider, fx2):
    M = S[a]; base = F6.params6(M); base.update(ch); base.update(rider)
    d = {k: copy.deepcopy(v) for k, v in M.items() if k not in ('name', 'desc', 'base', 'lv', 'id', 'icon')}
    d.update(id=fid, name=name, desc=desc, base=base, lv=[], icon=f'sf_{fid}', sfusion=1, cls='otomai', src=[a, b], fkind=kind,
             fx=list(M.get('fx') or []) + ([fx2] if fx2 and fx2 not in (M.get('fx') or []) else []), fx2=fx2)
    S[fid] = d
    C['spellFusions'] = [f for f in C['spellFusions'] if f['id'] != fid] + [{'id': fid, 'cls': 'otomai', 'src': [a, b], 'kind': kind}]


fusion('fu_oto_venin', 'oto_fiole', 'oto_vapeurs', 'spell', F6.names(819),
       T("Des fioles de venin : leurs flaques empoisonnent, ralentissent et rendent les monstres vulnérables. Le chef-d'œuvre toxique de l'Otomaï.",
         "Phials of venom: their puddles poison, slow and leave the monsters vulnerable. The Otomai's toxic masterpiece.",
         "Giftphiolen: Ihre Pfützen vergiften, verlangsamen und machen die Monster verwundbar. Das giftige Meisterwerk des Otomai.",
         "Frascos de veneno: sus charcos envenenan, ralentizan y dejan a los monstruos vulnerables. La obra maestra tóxica del Otomai.",
         "Fiale di veleno: le loro pozze avvelenano, rallentano e rendono vulnerabili i mostri. Il capolavoro tossico dell'Otomai.",
         "Flacons gif: hun plassen vergiftigen, vertragen en maken de monsters kwetsbaar. Het giftige meesterwerk van de Otomai.",
         "Frascos de veneno: as poças envenenam, abrandam e deixam os monstros vulneráveis. A obra-prima tóxica do Otomai."),
       {'count': 4, 'dmg': 30.0, 'aoe': 85, 'puddlePoison': 4.0, 'puddleDur': 3.5, 'slow': 0.35, 'puddleColor': '#9ad14a'}, {'rMark': 0.15}, 405)
fusion('fu_oto_oeuvre', 'oto_transmutation', 'baguette', 'weapon',
       T('Grand Œuvre', 'Magnum Opus', 'Großes Werk', 'Gran Obra', 'Grande Opera', 'Groot Werk', 'Grande Obra'),
       T("Des cercles alchimiques en série : bien plus de monstres changés en or, et bien plus de kamas. La baguette, c'était pour le style.",
         "Alchemical circles in a row: far more monsters turned into gold, and far more kamas. The wand was for style.",
         "Alchemistische Kreise am laufenden Band: viel mehr Monster werden zu Gold, und viel mehr Kamas. Der Zauberstab war nur für den Stil.",
         "Círculos alquímicos en serie: muchos más monstruos convertidos en oro, y muchos más kamas. La varita era por estilo.",
         "Cerchi alchemici a raffica: molti più mostri trasformati in oro, e molti più kama. La bacchetta era per stile.",
         "Alchemistische cirkels aan de lopende band: veel meer monsters worden goud, en veel meer kama's. De toverstaf was voor de stijl.",
         "Círculos alquímicos em série: muitos mais monstros transformados em ouro, e muitos mais kamas. A varinha era só estilo."),
       {'count': 5, 'dmg': 48.0, 'radius': 84, 'delay': 0.5, 'cd': 5.0, 'transmute': 0.3, 'gold': 0.2}, {}, 806)
fusion('fu_oto_mutagen', 'oto_kido', 'tofus_kamikazes', 'global', F6.names(1018),
       T("Des Kidos mutants, plus nombreux et plus coriaces : leurs morsures éclaboussent tout autour et empoisonnent. Les Tofus n'ont pas survécu à l'expérience.",
         "Mutant Kidos, more numerous and tougher: their bites splash all around and poison. The Tofus didn't survive the experiment.",
         "Mutierte Kidos, zahlreicher und zäher: Ihre Bisse spritzen ringsum und vergiften. Die Tofus haben das Experiment nicht überlebt.",
         "Kidos mutantes, más numerosos y resistentes: sus mordiscos salpican alrededor y envenenan. Los Tofus no sobrevivieron al experimento.",
         "Kido mutanti, più numerosi e coriacei: i loro morsi schizzano tutt'intorno e avvelenano. I Tofu non sono sopravvissuti all'esperimento.",
         "Gemuteerde Kido's, talrijker en taaier: hun beten spatten alle kanten op en vergiftigen. De Tofu's hebben het experiment niet overleefd.",
         "Kidos mutantes, mais numerosos e resistentes: as mordidas salpicam tudo à volta e envenenam. Os Tofus não sobreviveram à experiência."),
       {'count': 4, 'dmg': 9.0, 'hp': 120, 'speed': 190, 'duration': 13.0, 'cd': 10.0, 'aoe': 40}, {'rPoison': 0.6}, 1011)

# the Féca's Trêve (0.89) played the client clip 101 at its cast: a blue orb with a white streak that stayed 2.5 s on the
# ground (nothing to do there) — the dome alone now (spells.js plays no clip when a dome / armour has none)
S['glyphe_immobilisation']['fx'] = []

# the Roublard's 'Invocation de Bomberfu' fusion: real Bomberfus (client monster 802, sprite 1379, native colours:
# `build_mobs20.py 1379:z=3.0` -> 1379_z30) instead of Tofus
bf = S['fu_rou_bomberfu']; bf['base']['spriteKey'] = '1379_z30'; bf['base']['sprite'] = 1379
bf['desc'] = T("Des Bomberfus bourrés de poudre foncent sur les monstres et explosent en les assommant. Le meilleur ami du Roublard.",
               "Gunpowder-stuffed Bomberfus rush the monsters and explode, knocking them out. A Rogue's best friend.",
               "Mit Pulver gefüllte Bomberfus stürmen auf die Monster zu und explodieren betäubend. Des Schurken bester Freund.",
               "Bomberlokos rellenos de pólvora se lanzan contra los monstruos y explotan aturdiéndolos. El mejor amigo del Tymador.",
               "Bomber Paz imbottiti di polvere da sparo si lanciano sui mostri ed esplodono stordendoli. Il migliore amico del Furfante.",
               "Met buskruit gevulde Bomberfu's stormen op de monsters af en ontploffen verdovend. De beste vriend van de Schurk.",
               "Bomberfus recheados de pólvora avançam contra os monstros e explodem atordoando-os. O melhor amigo do Ladino.")
C['summonSnd']['fu_rou_bomberfu'] = {'spawn': 'tofu1', 'atk': ['tofu2'], 'die': 'explosion'}

# Goultard's zone: Difficile only (play screen: Normale greyed; Run forces it)
next(m for m in C['maps'] if m['id'] == 'goultard')['hardOnly'] = 1
put_ui({'hard_only': T('Difficile uniquement', 'Hard mode only', 'Nur auf Schwer', 'Solo en Difícil', 'Solo in Difficile', 'Alleen op Moeilijk', 'Só em Difícil')})

# every class's own colours (a button that puts them back; tools/research/classcolors091.py measured them on the client's clips)
_bc = json.load(open(f'{_root.ROOT}/work/classcolors091.json'))
for c in C['classes']:
    if not c.get('nocolors'): c['baseColors'] = {str(s): _bc[str(s)] for s in dict.fromkeys(c['sprites']) if str(s) in _bc}
put_ui({'col_reset': T("Couleurs d'origine", 'Original colours', 'Originalfarben', 'Colores originales', 'Colori originali', 'Oorspronkelijke kleuren', 'Cores originais')})

# everything maxed: the purse gives 5 kamas (10 before), the mass healing potion 10 % of the life (25 %); shorter texts
C['maxKamas'] = 5; C['massPotion']['heal'] = 0.10
put_ui({
    'take_kamas_d': T('Gagnez {n} kamas.', 'Gain {n} kamas.', 'Erhalte {n} Kamas.', 'Gana {n} kamas.', 'Ottieni {n} kama.', "Krijg {n} kama's.", 'Ganha {n} kamas.'),
    'take_bread_d': T('Soigne 10 % de vos PV et vos invocations.', 'Heals 10% of your HP and your summons.', 'Heilt 10 % deiner LP und deine Beschwörungen.',
                      'Cura el 10 % de tus PdV y a tus invocaciones.', 'Cura il 10% dei tuoi PV e le tue evocazioni.', 'Geneest 10% van je LP en je oproepingen.',
                      'Cura 10% dos teus PV e as tuas invocações.'),
})

C['summonSnd']['oto_kido'] = C['summonSnd']['fu_oto_mutagen'] = {'spawn': 'blop_up', 'atk': ['machouille'], 'die': 'Kido_Die'}
for a in C['achievements']:
    if a['id'] == 'classes_all': a['n'] = len(C['classes'])   # (a final boss beaten with every class: 15 now)

put_ui({
    'mutate': T('Mutation !', 'Mutation!', 'Mutation!', '¡Mutación!', 'Mutazione!', 'Mutatie!', 'Mutação!'),
    'p_mark': T('Vulnérabilité', 'Vulnerability', 'Verwundbarkeit', 'Vulnerabilidad', 'Vulnerabilità', 'Kwetsbaarheid', 'Vulnerabilidade'),
    'p_power': T('Puissance', 'Power', 'Kraft', 'Potencia', 'Potenza', 'Kracht', 'Potência'),
    'p_haste': T('Vitesse de course', 'Run speed', 'Laufgeschwindigkeit', 'Velocidad de carrera', 'Velocità di corsa', 'Loopsnelheid', 'Velocidade de corrida'),
    'p_transmute': T("Seuil d'or", 'Gold threshold', 'Goldschwelle', 'Umbral de oro', "Soglia d'oro", 'Goudgrens', 'Limiar de ouro'),
    'p_gold': T('Chance de kamas', 'Kama chance', 'Kama-Chance', 'Prob. de kamas', 'Probabilità di kama', "Kans op kama's", 'Chance de kamas'),
    'p_puddlePoison': T('Poison', 'Poison', 'Gift', 'Veneno', 'Veleno', 'Gif', 'Veneno'),
    'gl_lost': T("La carte graphique a coupé le rendu WebGL : le jeu continue en rendu Canvas 2D.",
                 "The graphics card dropped WebGL rendering: the game goes on with Canvas 2D rendering.",
                 "Die Grafikkarte hat das WebGL-Rendering beendet: Das Spiel läuft mit Canvas-2D-Rendering weiter.",
                 "La tarjeta gráfica cortó el renderizado WebGL: el juego sigue con renderizado Canvas 2D.",
                 "La scheda grafica ha interrotto il rendering WebGL: il gioco continua in Canvas 2D.",
                 "De videokaart stopte de WebGL-weergave: het spel gaat verder met Canvas 2D.",
                 "A placa gráfica cortou o rendering WebGL: o jogo continua em Canvas 2D."),
})

# 0.91: Goultard beaten the first time, back on the main menu: thanks, the Discord link and a joke of Dofus
DISCORD = 'https://discord.gg/N8f62M2eaK'
C['discord'] = DISCORD
put_ui({
    'gt_title': T('Goultard est tombé !', 'Goultard has fallen!', 'Goultard ist gefallen!', '¡Goultard ha caído!', 'Goultard è caduto!', 'Goultard is gevallen!', 'Goultard caiu!'),
    'gt_text': T("Tu as mis Goultard le Barbare au tapis. Même Rubilax en reste sans voix, c'est dire.\nMerci d'avoir joué à Retro Survivors jusqu'au bout : les Douze sont fiers de toi et Amakna te doit une fière chandelle… mais pas de kamas, la caisse est vide. Un Bouftou a tout mangé.",
                 "You knocked Goultard the Barbarian flat. Even Rubilax is speechless, and that's saying something.\nThanks for playing Retro Survivors all the way: the Twelve are proud of you and Amakna owes you big… but there are no kamas left in the till. A Gobball ate them all.",
                 "Du hast Goultard den Barbaren auf die Bretter geschickt. Selbst Rubilax ist sprachlos – und das will was heißen.\nDanke, dass du Retro Survivors bis zum Ende gespielt hast: Die Zwölf sind stolz auf dich und Amakna steht tief in deiner Schuld… nur Kamas gibt es keine mehr, die Kasse ist leer. Ein Fresssack hat alles aufgefressen.",
                 "Has tumbado a Goultard el Bárbaro. Hasta Rubilax se ha quedado sin palabras, y eso ya es decir.\nGracias por jugar a Retro Survivors hasta el final: los Doce están orgullosos de ti y Amakna te debe una… pero no quedan kamas en la caja. Un Jalató se los ha comido todos.",
                 "Hai messo al tappeto Goultard il Barbaro. Persino Rubilax è rimasto senza parole, ed è tutto dire.\nGrazie per aver giocato a Retro Survivors fino in fondo: i Dodici sono fieri di te e Amakna ti deve un favore… ma in cassa non ci sono più kama. Se li è mangiati tutti un Bouftou.",
                 "Je hebt Goultard de Barbaar tegen de vlakte geslagen. Zelfs Rubilax is sprakeloos, en dat zegt wat.\nBedankt dat je Retro Survivors tot het einde hebt gespeeld: de Twaalf zijn trots op je en Amakna staat bij je in het krijt… maar er zijn geen kama's meer in de kas. Een Bouftou heeft alles opgegeten.",
                 "Deitaste ao tapete o Goultard, o Bárbaro. Até o Rubilax ficou sem palavras, o que já diz muito.\nObrigado por jogares Retro Survivors até ao fim: os Doze estão orgulhosos de ti e Amakna fica a dever-te uma… mas já não há kamas no cofre. Um Papatudo comeu-os todos."),
    'gt_join': T('Viens fêter ça sur le Discord : bugs, idées, captures de tes plus belles runs (et de tes morts les plus bêtes face aux Tofus) !',
                 'Come and celebrate on the Discord: bugs, ideas, screenshots of your best runs (and of your silliest deaths to Tofus)!',
                 'Feier mit uns auf dem Discord: Bugs, Ideen, Screenshots deiner besten Runs (und deiner dümmsten Tode gegen Tofus)!',
                 '¡Ven a celebrarlo en el Discord: bugs, ideas, capturas de tus mejores partidas (y de tus muertes más tontas contra Tofus)!',
                 'Vieni a festeggiare sul Discord: bug, idee, screenshot delle tue run migliori (e delle tue morti più assurde contro i Tofu)!',
                 "Kom het vieren op de Discord: bugs, ideeën, screenshots van je beste runs (en van je domste doden tegen Tofu's)!",
                 'Vem festejar no Discord: bugs, ideias, capturas das tuas melhores partidas (e das tuas mortes mais parvas contra Tofus)!'),
    'gt_ok': T('Que les Douze veillent sur toi !', 'May the Twelve watch over you!', 'Mögen die Zwölf über dich wachen!', '¡Que los Doce velen por ti!', 'Che i Dodici veglino su di te!', 'Mogen de Twaalf over je waken!', 'Que os Doze olhem por ti!'),
})
if not any(DISCORD in json.dumps(x, ensure_ascii=False) for x in C['credits']):   # (before the Konami hint, the last line)
    C['credits'].insert(len(C['credits']) - 1, ['p', T(f'Rejoins la communauté sur **Discord** : {DISCORD}', f'Join the community on **Discord**: {DISCORD}',
        f'Komm in die Community auf **Discord**: {DISCORD}', f'Únete a la comunidad en **Discord**: {DISCORD}', f'Unisciti alla community su **Discord**: {DISCORD}',
        f'Kom bij de community op **Discord**: {DISCORD}', f'Junta-te à comunidade no **Discord**: {DISCORD}')])

# 0.92: the Discord button of the main menu's top bar (UI.discordInfo): what the Discord is for, a joke of Dofus.
# No download link of its own: the local version's link is given on the Discord (none is defined in the project)
put_ui({
    'dc_tip': T('Discord : news, bugs, idées, version locale', 'Discord: news, bugs, ideas, local version', 'Discord: News, Bugs, Ideen, lokale Version',
                'Discord: noticias, bugs, ideas, versión local', 'Discord: news, bug, idee, versione locale', 'Discord: nieuws, bugs, ideeën, lokale versie',
                'Discord: novidades, bugs, ideias, versão local'),
    'dc_title': T('Le Discord de Retro Survivors', 'The Retro Survivors Discord', 'Der Discord von Retro Survivors', 'El Discord de Retro Survivors',
                  'Il Discord di Retro Survivors', 'De Discord van Retro Survivors', 'O Discord de Retro Survivors'),
    'dc_joke': T("Les Douze ont un Discord. Même les Bouftous ont le droit d'y signaler leurs bugs.",
                 'The Twelve have a Discord. Even the Gobballs are allowed to report their bugs there.',
                 'Die Zwölf haben einen Discord. Sogar die Fresssäcke dürfen dort ihre Bugs melden.',
                 'Los Doce tienen un Discord. Hasta los Jalatós tienen derecho a reportar sus bugs.',
                 'I Dodici hanno un Discord. Persino i Pappatutto possono segnalarci i loro bug.',
                 'De Twaalf hebben een Discord. Zelfs de Veelvraten mogen er hun bugs melden.',
                 'Os Doze têm um Discord. Até os Gobballs têm o direito de reportar os seus bugs.'),
    'dc_news': T('Les actualités et les prochaines mises à jour', 'News and the coming updates', 'News und die nächsten Updates', 'Noticias y próximas actualizaciones',
                 'Notizie e prossimi aggiornamenti', 'Nieuws en de komende updates', 'Novidades e próximas atualizações'),
    'dc_new': T('Les nouveautés du jeu', "What's new in the game", 'Neues im Spiel', 'Las novedades del juego', 'Le novità del gioco', 'Wat er nieuw is in het spel', 'As novidades do jogo'),
    'dc_bugs': T('Signaler un bug et aider à le corriger', 'Report a bug and help fix it', 'Bugs melden und beim Beheben helfen', 'Reportar un bug y ayudar a corregirlo',
                 'Segnalare un bug e aiutare a correggerlo', 'Een bug melden en helpen hem op te lossen', 'Reportar um bug e ajudar a corrigi-lo'),
    'dc_ideas': T('Proposer tes idées pour faire évoluer le jeu', 'Suggest your ideas to shape the game', 'Deine Ideen für das Spiel vorschlagen', 'Proponer tus ideas para hacer evolucionar el juego',
                  'Proporre le tue idee per far evolvere il gioco', 'Je ideeën voorstellen om het spel te laten groeien', 'Propor as tuas ideias para fazer evoluir o jogo'),
    'dc_dl': T('Le lien de la version locale à télécharger : la plus fluide !', 'The link to download the local version: the smoothest one!',
               'Den Link zur lokalen Version zum Herunterladen: die flüssigste!', 'El enlace para descargar la versión local: ¡la más fluida!',
               'Il link per scaricare la versione locale: la più fluida!', 'De link om de lokale versie te downloaden: de soepelste!',
               'O link para descarregar a versão local: a mais fluida!'),
    'dc_lag': T("Parce que combattre le lag, c'est aussi un métier.", 'Because fighting lag is a profession too.', 'Denn gegen Lag zu kämpfen ist auch ein Beruf.',
                'Porque combatir el lag también es un oficio.', 'Perché combattere il lag è anche un mestiere.', 'Want tegen lag vechten is ook een beroep.',
                'Porque combater o lag também é uma profissão.'),
    'dc_join': T('Rejoindre le Discord', 'Join the Discord', 'Dem Discord beitreten', 'Unirse al Discord', 'Unisciti al Discord', 'Word lid van de Discord', 'Entrar no Discord'),
})

# 0.92: the Dofus Pourpre had the Cawotte's joke (dofus_joke 1-4 picked by the id's length, both 7 letters):
# a joke of its own (UI.dofusInfo takes dofus_joke_<id> first)
put_ui({'dofus_joke_pourpre': T("Droppé par : ??? — le Minotoror voit rouge dès qu'on lui en parle. Pourpre, pardon.",
    'Dropped by: ??? — the Minotoror sees red the moment you mention it. Crimson, sorry.',
    'Gedroppt von: ??? — der Minotoror sieht rot, sobald man ihn danach fragt. Purpur, Verzeihung.',
    'Lo dropea: ??? — el Minotauroro se pone rojo de ira en cuanto se lo mencionas. Púrpura, perdón.',
    'Droppato da: ??? — il Minotoror vede rosso appena glielo nomini. Porpora, scusate.',
    'Gedropt door: ??? — de Minotoror ziet rood zodra je erover begint. Purper, sorry.',
    'Dropado por: ??? — o Minotororo fica vermelho de raiva mal lhe falas nisso. Púrpura, perdão.')})

# 0.92: the Chouque's ghost hints at the profile names' music easter eggs (UI.NAME_EGGS): one of these as the
# last line of the treasure's show, never the same twice in a row (events.js, Store.data.tmEgg)
C['tmap']['ghost']['egglines'] = [
    T("Psst… un conseil de fantôme : appelle ton profil Bardella. Tu verras, ça fait du bruit.",
      "Psst… a ghost's advice: name your profile Bardella. You'll see, it makes some noise.",
      "Psst… ein Rat vom Geist: Nenn dein Profil Bardella. Du wirst sehen, das macht Lärm.",
      "Psst… un consejo de fantasma: llama a tu perfil Bardella. Ya verás, hace ruido.",
      "Psst… un consiglio da fantasma: chiama il tuo profilo Bardella. Vedrai, fa rumore.",
      "Psst… advies van een spook: noem je profiel Bardella. Je zult zien, dat maakt lawaai.",
      "Psst… um conselho de fantasma: chama ao teu perfil Bardella. Vais ver, faz barulho."),
    T("Les vivants qui s'ennuient renomment leur profil Jordan. Moi, je hante. Chacun son passe-temps.",
      "Bored living folks rename their profile Jordan. Me, I haunt. Everyone has a hobby.",
      "Gelangweilte Lebende nennen ihr Profil Jordan. Ich spuke. Jedem sein Hobby.",
      "Los vivos aburridos renombran su perfil Jordan. Yo embrujo. Cada uno con su pasatiempo.",
      "I vivi annoiati rinominano il profilo Jordan. Io infesto. Ognuno ha il suo passatempo.",
      "Verveelde levenden noemen hun profiel Jordan. Ik spook. Ieder z'n hobby.",
      "Os vivos aborrecidos mudam o perfil para Jordan. Eu assombro. Cada um com o seu passatempo."),
    T("Mets Lassalle comme nom de profil. Si tu entends chanter les montagnes, c'est normal. Enfin, presque.",
      "Put Lassalle as your profile name. If you hear the mountains sing, that's normal. Well, almost.",
      "Nimm Lassalle als Profilnamen. Wenn die Berge singen, ist das normal. Na ja, fast.",
      "Pon Lassalle como nombre de perfil. Si oyes cantar a las montañas, es normal. Bueno, casi.",
      "Metti Lassalle come nome del profilo. Se senti cantare le montagne, è normale. Più o meno.",
      "Zet Lassalle als profielnaam. Hoor je de bergen zingen, dan is dat normaal. Nou ja, bijna.",
      "Põe Lassalle como nome de perfil. Se ouvires as montanhas a cantar, é normal. Bem, quase."),
    T("On raconte qu'un profil nommé Zemmour fait trembler les Bouftous. Je n'ai pas vérifié : je suis mort.",
      "They say a profile named Zemmour makes the Gobballs tremble. I didn't check: I'm dead.",
      "Man sagt, ein Profil namens Zemmour lässt die Fresssäcke zittern. Ich hab's nicht geprüft: Ich bin tot.",
      "Dicen que un perfil llamado Zemmour hace temblar a los Jalatós. No lo he comprobado: estoy muerto.",
      "Si dice che un profilo chiamato Zemmour faccia tremare i Pappatutto. Non ho controllato: sono morto.",
      "Ze zeggen dat een profiel met de naam Zemmour de Veelvraten doet beven. Niet gecontroleerd: ik ben dood.",
      "Dizem que um perfil chamado Zemmour faz tremer os Gobballs. Não confirmei: estou morto."),
    T("Essaie Jean-Luc comme nom de profil. Et après, ne viens pas te plaindre au fantôme.",
      "Try Jean-Luc as your profile name. And then don't come complaining to the ghost.",
      "Versuch Jean-Luc als Profilnamen. Und danach beschwer dich nicht beim Geist.",
      "Prueba Jean-Luc como nombre de perfil. Y luego no vengas a quejarte al fantasma.",
      "Prova Jean-Luc come nome del profilo. E poi non venire a lamentarti dal fantasma.",
      "Probeer Jean-Luc als profielnaam. En kom daarna niet klagen bij het spook.",
      "Experimenta Jean-Luc como nome de perfil. E depois não venhas queixar-te ao fantasma."),
    T("Un profil Sardoche ? Bouche-toi les oreilles, moussaillon : ça risque de rager.",
      "A profile called Sardoche? Cover your ears, cabin boy: there may be some raging.",
      "Ein Profil namens Sardoche? Halt dir die Ohren zu, Schiffsjunge: Da wird gleich getobt.",
      "¿Un perfil llamado Sardoche? Tápate los oídos, grumete: puede haber rabia.",
      "Un profilo chiamato Sardoche? Tappati le orecchie, mozzo: potrebbe arrabbiarsi.",
      "Een profiel genaamd Sardoche? Oren dicht, scheepsmaatje: er kan getierd worden.",
      "Um perfil chamado Sardoche? Tapa os ouvidos, grumete: pode haver fúria."),
    T("Lisnard. Tape ça dans ton profil. Pourquoi ? Parce qu'un fantôme te l'a dit, voilà pourquoi.",
      "Lisnard. Type that into your profile. Why? Because a ghost told you so, that's why.",
      "Lisnard. Tipp das in dein Profil. Warum? Weil ein Geist es dir sagt, darum.",
      "Lisnard. Escribe eso en tu perfil. ¿Por qué? Porque te lo dice un fantasma, por eso.",
      "Lisnard. Scrivilo nel tuo profilo. Perché? Perché te lo dice un fantasma, ecco perché.",
      "Lisnard. Typ dat in je profiel. Waarom? Omdat een spook het zegt, daarom.",
      "Lisnard. Escreve isso no teu perfil. Porquê? Porque um fantasma to disse, é por isso."),
    T("Renomme ton profil Sarkozy et tends l'oreille. Même mon perroquet en a perdu ses plumes.",
      "Rename your profile Sarkozy and listen closely. Even my parrot lost its feathers over it.",
      "Nenn dein Profil Sarkozy und hör gut hin. Sogar mein Papagei hat dabei Federn gelassen.",
      "Renombra tu perfil Sarkozy y escucha bien. Hasta mi loro perdió las plumas.",
      "Rinomina il profilo Sarkozy e ascolta bene. Persino il mio pappagallo ci ha perso le piume.",
      "Noem je profiel Sarkozy en luister goed. Zelfs mijn papegaai verloor er zijn veren bij.",
      "Muda o perfil para Sarkozy e escuta bem. Até o meu papagaio perdeu as penas."),
    T("Hollande, en nom de profil. Il ne pleuvra pas forcément, mais prends quand même un parapluie.",
      "Hollande, as a profile name. It won't necessarily rain, but take an umbrella anyway.",
      "Hollande als Profilname. Es regnet nicht unbedingt, aber nimm trotzdem einen Schirm mit.",
      "Hollande como nombre de perfil. No tiene por qué llover, pero lleva paraguas por si acaso.",
      "Hollande come nome del profilo. Non pioverà per forza, ma porta comunque l'ombrello.",
      "Hollande als profielnaam. Het regent niet per se, maar neem toch een paraplu mee.",
      "Hollande como nome de perfil. Não vai chover de certeza, mas leva um guarda-chuva na mesma."),
    T("Écris Lepen dans ton profil. Le Chouque décline toute responsabilité : il est déjà mort.",
      "Write Lepen in your profile. The Chouque declines all responsibility: he's already dead.",
      "Schreib Lepen in dein Profil. Der Chouque übernimmt keine Verantwortung: Er ist schon tot.",
      "Escribe Lepen en tu perfil. El Chouque declina toda responsabilidad: ya está muerto.",
      "Scrivi Lepen nel tuo profilo. Il Chouque declina ogni responsabilità: è già morto.",
      "Schrijf Lepen in je profiel. De Chouque wijst alle verantwoordelijkheid af: hij is al dood.",
      "Escreve Lepen no teu perfil. O Chouque declina toda a responsabilidade: já está morto."),
    T("Trois lettres : N, T, M. Dans ton profil. Le reste, c'est entre toi et tes oreilles.",
      "Three letters: N, T, M. In your profile. The rest is between you and your ears.",
      "Drei Buchstaben: N, T, M. In dein Profil. Der Rest bleibt zwischen dir und deinen Ohren.",
      "Tres letras: N, T, M. En tu perfil. Lo demás queda entre tú y tus oídos.",
      "Tre lettere: N, T, M. Nel tuo profilo. Il resto è tra te e le tue orecchie.",
      "Drie letters: N, T, M. In je profiel. De rest is tussen jou en je oren.",
      "Três letras: N, T, M. No teu perfil. O resto fica entre ti e os teus ouvidos."),
    T("Un fantôme ne dit jamais Marine à voix haute. Toi, tu peux l'écrire dans ton profil…",
      "A ghost never says Marine out loud. You, though, can write it in your profile…",
      "Ein Geist sagt nie laut Marine. Du aber kannst es in dein Profil schreiben…",
      "Un fantasma nunca dice Marine en voz alta. Tú, en cambio, puedes escribirlo en tu perfil…",
      "Un fantasma non dice mai Marine ad alta voce. Tu però puoi scriverlo nel tuo profilo…",
      "Een spook zegt nooit hardop Marine. Jij kunt het wel in je profiel schrijven…",
      "Um fantasma nunca diz Marine em voz alta. Tu, porém, podes escrevê-lo no teu perfil…"),
    T("Appelle ton profil Macron. Si on te demande pourquoi, réponds que c'est un fantôme qui traverse la rue pour te le dire.",
      "Name your profile Macron. If anyone asks why, say a ghost crossed the street to tell you.",
      "Nenn dein Profil Macron. Fragt jemand warum, sag, ein Geist ist extra über die Straße gekommen, um es dir zu sagen.",
      "Llama a tu perfil Macron. Si te preguntan por qué, di que un fantasma cruzó la calle para decírtelo.",
      "Chiama il tuo profilo Macron. Se ti chiedono perché, di' che un fantasma ha attraversato la strada per dirtelo.",
      "Noem je profiel Macron. Vraagt iemand waarom, zeg dan dat een spook de straat overstak om het je te vertellen.",
      "Chama ao teu perfil Macron. Se te perguntarem porquê, diz que um fantasma atravessou a rua para te dizer."),
]

# 0.92: the play screen's mark of a zone won in Difficile (Store.data.clearedHard)
put_ui({'hard_won': T('Gagnée en Difficile', 'Won in Hard mode', 'Auf Schwer gewonnen', 'Ganada en Difícil', 'Vinta in Difficile', 'Gewonnen op Moeilijk', 'Ganha em Difícil')})

# 0.92 (the Brigandin seemed to teleport on his melee blows): his anim0 (Élagage du Cou, Persécution) ends in a
# leap off the spot, then snapped back: only the blow is played (main.js applies C.animCut to the character sheets)
C['animCut'] = {'1155': {'anim0R': 10, 'anim0L': 8}}

# 0.92: the Maîtres Corbacs' reward every minute (Run.doomReward)
put_ui({
    'doom_rw_tmap': T('Les Maîtres Corbacs ont lâché une carte au trésor quelque part !', 'The Master Crows dropped a treasure map somewhere!',
                      'Die Meisterraben haben irgendwo eine Schatzkarte fallen lassen!', '¡Los Maestros Cuervos han soltado un mapa del tesoro en algún sitio!',
                      'I Maestri Corvi hanno lasciato cadere una mappa del tesoro da qualche parte!', 'De Meesterraven hebben ergens een schatkaart laten vallen!',
                      'Os Mestres Corvos largaram um mapa do tesouro algures!'),
    'doom_rw_manuel': T('Les Maîtres Corbacs ont lâché un Manuel du Tailleur quelque part !', 'The Master Crows dropped a Tailor Manual somewhere!',
                        'Die Meisterraben haben irgendwo ein Handbuch der Schneiderei fallen lassen!', '¡Los Maestros Cuervos han soltado un Manual del Sastre en algún sitio!',
                        'I Maestri Corvi hanno lasciato cadere un Manuale del Sarto da qualche parte!', 'De Meesterraven hebben ergens een Kleermakershandboek laten vallen!',
                        'Os Mestres Corvos largaram um Manual do Alfaiate algures!'),
})
# 0.92: treasure maps twice as common as the Manuel du Tailleur: a run rolls the Manuel (manuel.chance) and, when its
# final boss falls in time, the Coffre Animé may give one (coffre.drops 'manuel'): the map's roll is twice that
_pm = 1 - (1 - C['manuel']['chance']) * (1 - dict(C['coffre']['drops']).get('manuel', 0))
C['tmap']['chance'] = round(2 * _pm, 3)

# 0.92: Portée's level-up card names its weapon reach too (passiveReal)
put_ui({'ps_wreach': T('Portée des armes', 'Weapon reach', 'Waffenreichweite', 'Alcance de las armas', 'Portata delle armi', 'Bereik van wapens', 'Alcance das armas')})

# 0.92: 5 achievements — a profile name with a clip (UI.NAME_EGGS, Goultard too: st.nameEgg), 3 Nowel gifts
# (st.nowelGifts), 5 zones won in Difficile (clearedHard), 5 Maîtres Corbacs' rewards picked up, the victory's 'fah'
_have = {a['id'] for a in C['achievements']}
for _a in [
    dict(id='name_egg', k='nameEgg', n=1, icon='it_1_25',
         name=T('Un nom qui chante', 'A Name That Sings', 'Ein Name, der singt', 'Un nombre que canta', 'Un nome che canta', 'Een naam die zingt', 'Um nome que canta'),
         desc=T("Donner à un profil un nom qui cache une surprise. Le Chouque fantôme a peut-être des idées.", "Give a profile a name that hides a surprise. The Chouque's ghost may have ideas.",
                "Einem Profil einen Namen geben, der eine Überraschung verbirgt. Der Geist des Chouque hat vielleicht Ideen.", "Dar a un perfil un nombre que esconde una sorpresa. El fantasma del Chouque quizá tenga ideas.",
                "Dare a un profilo un nome che nasconde una sorpresa. Il fantasma del Chouque forse ha qualche idea.", "Een profiel een naam geven die een verrassing verbergt. Het spook van de Chouque heeft misschien ideeën.",
                "Dar a um perfil um nome que esconde uma surpresa. O fantasma do Chouque talvez tenha ideias.")),
    dict(id='nowel_gifts_3', k='nowelGifts', n=3, icon='it_89_2',
         name=T('Hotte bien remplie', 'A Well-Filled Sack', 'Gut gefüllter Sack', 'Saco bien lleno', 'Gerla ben piena', 'Goed gevulde zak', 'Saco bem cheio'),
         desc=T("Ramasser 3 cadeaux sur l'Île de Nowel. Papa Nowel compte ses chaussettes.", "Pick up 3 gifts on Nowel Island. Santa Jaws is counting his socks.",
                "3 Geschenke auf der Nowel-Insel aufheben. Der Weihnachtsmann zählt seine Socken.", "Recoger 3 regalos en la Isla de Nowel. Chanta Klaus cuenta sus calcetines.",
                "Raccogliere 3 regali sull'Isola di Nowel. Babbo Nawal conta i suoi calzini.", "3 cadeaus oprapen op het Nowel-eiland. De Kwestman telt zijn sokken.",
                "Apanhar 3 presentes na Ilha de Nowel. O Papai Nowel conta as meias.")),
    dict(id='hard_zones_5', k='hardZones', n=5, icon='it_47_27',
         name=T('Crâne dur', 'Hard-Headed', 'Dickschädel', 'Cabeza dura', 'Testa dura', 'Stijfkop', 'Cabeça-dura'),
         desc=T("Gagner 5 zones différentes en Difficile. Même les Iops trouvent ça costaud.", "Win 5 different zones in Hard mode. Even the Iops find it tough.",
                "5 verschiedene Zonen auf Schwer gewinnen. Sogar die Iops finden das heftig.", "Ganar 5 zonas distintas en Difícil. Hasta los Yopukas lo ven duro.",
                "Vincere 5 zone diverse in Difficile. Persino gli Iop lo trovano tosto.", "5 verschillende zones winnen op Moeilijk. Zelfs de Iops vinden het pittig.",
                "Ganhar 5 zonas diferentes em Difícil. Até os Iops acham duro.")),
    dict(id='doom_rewards_5', k='doomRewards', n=5, icon='it_24_6',
         name=T('Pilleur de Corbacs', 'Crow Plunderer', 'Rabenplünderer', 'Saqueador de Cuervos', 'Predone di Corvi', 'Ravenplunderaar', 'Saqueador de Corvos'),
         desc=T("Ramasser 5 récompenses lâchées par les Maîtres Corbacs. Ils n'avaient qu'à mieux les tenir.", "Pick up 5 rewards dropped by the Master Crows. They should have held on tighter.",
                "5 von den Meisterraben fallen gelassene Belohnungen aufheben. Hätten sie mal besser festgehalten.", "Recoger 5 recompensas soltadas por los Maestros Cuervos. Haberlas agarrado mejor.",
                "Raccogliere 5 ricompense lasciate cadere dai Maestri Corvi. Dovevano tenerle meglio.", "5 beloningen oprapen die de Meesterraven lieten vallen. Hadden ze maar beter moeten vasthouden.",
                "Apanhar 5 recompensas largadas pelos Mestres Corvos. Deviam tê-las agarrado melhor.")),
    dict(id='fah', k='fahHeard', n=1, icon='it_1_89',
         name=T('Fah !', 'Fah!', 'Fah!', '¡Fah!', 'Fah!', 'Fah!', 'Fah!'),
         desc=T("Entendre un drôle de bruit en remportant une zone. Ça n'arrive pas à chaque fois.", "Hear a funny noise when winning a zone. It doesn't happen every time.",
                "Beim Gewinnen einer Zone ein komisches Geräusch hören. Das passiert nicht jedes Mal.", "Oír un ruido raro al ganar una zona. No pasa siempre.",
                "Sentire uno strano rumore vincendo una zona. Non succede ogni volta.", "Een raar geluid horen bij het winnen van een zone. Dat gebeurt niet elke keer.",
                "Ouvir um barulho estranho ao ganhar uma zona. Não acontece sempre.")),
]:
    if _a['id'] not in _have: C['achievements'].append(_a)

# 0.92: the Crâ's arrows push the monsters 25 % less. A projectile's push on a hit was the game's rule (run.projKnock
# + its knock x3, else 40): his projectile spells and fusions now carry their own `push` (game.js), 75 % of what they had;
# their knock becomes it (levels too). The weapons and the global spells keep the rule
def _cra_push(d):
    B = C['run'].get('projKnock', 0)
    full = lambda kn: round(0.75 * (B + (kn * 3 if kn else 40)), 1)
    kn = d['base'].pop('knock', None); d['base']['push'] = full(kn)
    for lv in d.get('lv') or []:
        if 'knock' in lv: kn = lv.pop('knock'); lv['push'] = full(kn)
_cra = next(c for c in C['classes'] if c['id'] == 'cra')
for _sid in _cra['spells'] + [f['id'] for f in C['spellFusions'] if f['cls'] == 'cra']:
    _d = C['spells'][_sid]
    if _d['t'] == 'projectile' and 'push' not in _d['base']: _cra_push(_d)
put_ui({'p_push': T('Recul', 'Knockback', 'Rückstoß', 'Retroceso', 'Respinta', 'Terugslag', 'Recuo')})

# 0.92: the Dofus shields, a skin slot like the hats / capes (not for the classes without them: Roublard, Brigandin,
# Otomaï — `nohats`). Built by tools/assets/build_shields092.py (pictures, shop icons, work/shields092.json) and
# tools/assets/shield_anc092.py (their anchors in the character sheets). Price 5 000 -> 10 000 kamas by the item's level (1-11),
# rounded to 50; a worn shield gives +1 resistance (Run.shieldOn, C.shieldArmor)
_SHP = f'{_root.ROOT}/work/shields092.json'
if _os.path.exists(_SHP):
    _sh = json.load(open(_SHP, encoding='utf-8'))
    _l0, _l1 = min(e['lvl'] for e in _sh), max(e['lvl'] for e in _sh)
    C['shields'] = [dict(id=e['sym'], item=e['item'], name=e['name'], lvl=e['lvl'],
                         price=int(round((5000 + 5000 * (e['lvl'] - _l0) / max(1, _l1 - _l0)) / 50) * 50)) for e in _sh]
C['shieldArmor'] = 1
put_ui({
    'shields': T('Boucliers', 'Shields', 'Schilde', 'Escudos', 'Scudi', 'Schilden', 'Escudos'),
    'shield_res': T('+1 résistance', '+1 resistance', '+1 Resistenz', '+1 resistencia', '+1 resistenza', '+1 weerstand', '+1 resistência'),
    'shield_bonus': (lambda N: {lg: t.format(*N[lg]) for lg, t in T("Un bouclier porté au bras : +1 résistance, chaque coup reçu est réduit d'autant. {0}, {1} et {2} n'en portent pas.",
                      'A shield worn on the arm: +1 resistance, every blow taken is reduced by that much. {0}, {1} and {2} wear none.',
                      'Ein am Arm getragener Schild: +1 Resistenz, jeder erlittene Treffer wird um so viel verringert. {0}, {1} und {2} tragen keinen.',
                      'Un escudo llevado en el brazo: +1 resistencia, cada golpe recibido se reduce en esa cantidad. {0}, {1} y {2} no llevan.',
                      'Uno scudo portato al braccio: +1 resistenza, ogni colpo subito è ridotto di tanto. {0}, {1} e {2} non ne portano.',
                      'Een schild aan de arm: +1 weerstand, elke ontvangen klap wordt met zoveel verminderd. {0}, {1} en {2} dragen er geen.',
                      'Um escudo usado no braço: +1 resistência, cada golpe recebido é reduzido nesse valor. {0}, {1} e {2} não usam.').items()})(
        {lg: [next(c for c in C['classes'] if c['id'] == k)['name'][lg] for k in ('roublard', 'bandit', 'otomai')] for lg in LG}),
})

if __name__ == '__main__':
    json.dump(C, open(f'{G}/data/content.json', 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
    print('0.91 ok', len(C['classes']), 'classes')
