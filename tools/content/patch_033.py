"""Beta 0.34 content, applied on top of patch_032: the 0.34 changes (icons, balance, texts).
->  game/data/content.json      usage: python tools/content/patch_033.py"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
import json
import patch_032 as P2
from _root import ROOT as _ROOT0

C, T, G = P2.C, P2.T, P2.G

for p in C['passives']:
    if p['id'] == 'prospection': p['icon'] = 'IconPP'   # the client's Prospection icon (blue gem in a gold ring)

# ---------------------------------------------------------------- the unique weapons' own finales (0.34): three each,
# none shared with another weapon; their descriptions are built from what they change (7 languages)
TPL = {
    'dmg': T('+{n} % de dégâts.', '+{n}% damage.', '+{n} % Schaden.', '+{n} % de daño.', '+{n}% di danni.', '+{n}% schade.', '+{n}% de dano.'),
    'cd': T('Frappe {n} % plus vite.', 'Strikes {n}% faster.', 'Schlägt {n} % schneller zu.', 'Golpea un {n} % más rápido.', 'Colpisce il {n}% più in fretta.', 'Slaat {n}% sneller.', 'Ataca {n}% mais depressa.'),
    'count': T('+{n} projectiles.', '+{n} projectiles.', '+{n} Geschosse.', '+{n} proyectiles.', '+{n} proiettili.', '+{n} projectielen.', '+{n} projéteis.'),
    'pierce': T('Transperce {n} ennemis de plus.', 'Pierces {n} more enemies.', 'Durchbohrt {n} Gegner mehr.', 'Atraviesa {n} enemigos más.', 'Trapassa {n} nemici in più.', 'Doorboort {n} vijanden meer.', 'Trespassa mais {n} inimigos.'),
    'aoe': T('Explosions bien plus grandes.', 'Much bigger explosions.', 'Viel größere Explosionen.', 'Explosiones mucho mayores.', 'Esplosioni molto più grandi.', 'Veel grotere explosies.', 'Explosões muito maiores.'),
    'burn': T('Brûlure bien plus forte.', 'Much stronger burn.', 'Viel stärkeres Brennen.', 'Quemadura mucho más fuerte.', 'Bruciatura molto più forte.', 'Veel sterkere brandwond.', 'Queimadura muito mais forte.'),
    'leech': T('Vol de vie doublé.', 'Life steal doubled.', 'Lebensraub verdoppelt.', 'Robo de vida doble.', 'Furto di vita raddoppiato.', 'Levensroof verdubbeld.', 'Roubo de vida a dobrar.'),
    'slow': T('Ralentit plus fort et plus longtemps.', 'Slows harder and longer.', 'Verlangsamt stärker und länger.', 'Ralentiza más y durante más tiempo.', 'Rallenta di più e più a lungo.', 'Vertraagt sterker en langer.', 'Abranda mais e durante mais tempo.'),
    'crit': T('+{n} % de coups critiques.', '+{n}% critical hits.', '+{n} % kritische Treffer.', '+{n} % de golpes críticos.', '+{n}% colpi critici.', '+{n}% voltreffers.', '+{n}% de golpes críticos.'),
    'bolt': T('+{n} éclair à chaque coup.', '+{n} lightning bolt per swing.', '+{n} Blitz pro Schlag.', '+{n} rayo por golpe.', '+{n} fulmine per colpo.', '+{n} bliksem per slag.', '+{n} raio por golpe.'),
    'confuse': T('Confusion deux fois plus longue.', 'Confusion lasts twice as long.', 'Verwirrung hält doppelt so lange.', 'La confusión dura el doble.', 'La confusione dura il doppio.', 'Verwarring duurt twee keer zo lang.', 'A confusão dura o dobro.'),
    'knock': T('Repousse bien plus loin.', 'Knocks back much further.', 'Stößt viel weiter zurück.', 'Empuja mucho más lejos.', 'Respinge molto più lontano.', 'Duwt veel verder terug.', 'Empurra muito mais longe.'),
    'chakram': T('+{n} disque à chaque coup.', '+{n} disc per swing.', '+{n} Scheibe pro Schlag.', '+{n} disco por golpe.', '+{n} disco per colpo.', '+{n} schijf per slag.', '+{n} disco por golpe.'),
    'bleed': T('Saignement bien plus fort.', 'Much stronger bleeding.', 'Viel stärkere Blutung.', 'Sangrado mucho más fuerte.', 'Sanguinamento molto più forte.', 'Veel sterkere bloeding.', 'Sangramento muito mais forte.'),
    'wave': T('+{n} vague tranchante à chaque coup.', '+{n} slicing wave per swing.', '+{n} Schnittwelle pro Schlag.', '+{n} onda cortante por golpe.', '+{n} onda tagliente per colpo.', '+{n} snijgolf per slag.', '+{n} onda cortante por golpe.'),
    'range': T('Portée et largeur augmentées.', 'Longer and wider swings.', 'Größere Reichweite und Breite.', 'Más alcance y anchura.', 'Più portata e ampiezza.', 'Meer bereik en breedte.', 'Mais alcance e largura.'),
    'sides4': T('Frappe dans les quatre directions.', 'Strikes in all four directions.', 'Schlägt in alle vier Richtungen.', 'Golpea en las cuatro direcciones.', 'Colpisce nelle quattro direzioni.', 'Slaat in alle vier richtingen.', 'Ataca nas quatro direções.'),
    'cloud': T('Nuage deux fois plus grand.', 'A cloud twice as big.', 'Doppelt so große Wolke.', 'Nube el doble de grande.', 'Nuvola grande il doppio.', 'Een twee keer zo grote wolk.', 'Nuvem com o dobro do tamanho.'),
    'quake': T('Secousses deux fois plus fortes.', 'Tremors twice as strong.', 'Doppelt so starke Beben.', 'Temblores el doble de fuertes.', 'Scosse forti il doppio.', 'Twee keer zo sterke bevingen.', 'Tremores com o dobro da força.'),
    'radius': T("Zone d'impact plus grande.", 'Bigger impact area.', 'Größerer Wirkungsbereich.', 'Zona de impacto mayor.', "Zona d'impatto più grande.", 'Groter inslaggebied.', 'Zona de impacto maior.'),
    'stun': T('Étourdit plus longtemps.', 'Stuns for longer.', 'Betäubt länger.', 'Aturde durante más tiempo.', 'Stordisce più a lungo.', 'Verdooft langer.', 'Atordoa durante mais tempo.'),
    'firePatch': T('Flammes au sol bien plus grandes.', 'Much bigger flames on the ground.', 'Viel größere Bodenflammen.', 'Llamas en el suelo mucho mayores.', 'Fiamme a terra molto più grandi.', 'Veel grotere vlammen op de grond.', 'Chamas no chão muito maiores.'),
    'stack': T('La rage monte deux fois plus haut.', 'Rage builds twice as high.', 'Die Wut steigt doppelt so hoch.', 'La rabia sube el doble.', 'La rabbia sale il doppio.', 'De woede stijgt twee keer zo hoog.', 'A raiva sobe o dobro.'),
    'dig': T('Déterre bien plus de kamas.', 'Digs up many more kamas.', 'Gräbt viel mehr Kamas aus.', 'Desentierra muchos más kamas.', 'Dissotterra molti più kama.', 'Graaft veel meer kama op.', 'Desenterra muitos mais kamas.'),
    'cake': T('Deux fois plus de gâteaux.', 'Twice as many cakes.', 'Doppelt so viele Kuchen.', 'El doble de pasteles.', 'Il doppio delle torte.', 'Twee keer zoveel taartjes.', 'O dobro dos bolos.'),
    'homing': T('Projectiles plus vifs et plus précis.', 'Faster, more accurate shots.', 'Schnellere, genauere Geschosse.', 'Proyectiles más rápidos y precisos.', 'Proiettili più rapidi e precisi.', 'Snellere, preciezere schoten.', 'Projéteis mais rápidos e precisos.'),
}
def N(*a): return T(*a)
UF = {   # unique: [(id, name x7, effect)]
 'arc_ange': [('ange_aureole', N('Auréole', 'Halo', 'Heiligenschein', 'Aureola', 'Aureola', 'Stralenkrans', 'Auréola'), dict(add={'count': 2})),
              ('ange_jugement', N('Jugement dernier', 'Last Judgement', 'Jüngstes Gericht', 'Juicio final', 'Giudizio finale', 'Laatste oordeel', 'Juízo final'), dict(mul={'dmg': 0.45}, add={'crit': 0.1})),
              ('ange_seraphin', N('Séraphin', 'Seraph', 'Seraph', 'Serafín', 'Serafino', 'Serafijn', 'Serafim'), dict(mul={'cd': -0.3}, add={'homing': 3})),],
 'arc_feugeuf': [('feugeuf_brasier', N('Brasier', 'Blaze', 'Feuersbrunst', 'Hoguera', 'Rogo', 'Vuurzee', 'Fogueira'), dict(add={'aoe': 40})),
                 ('feugeuf_braise', N('Braises ardentes', 'Live Embers', 'Glühende Asche', 'Brasas ardientes', 'Braci ardenti', 'Gloeiende sintels', 'Brasas ardentes'), dict(add={'burn': 10})),
                 ('feugeuf_salve', N('Salve enflammée', 'Fiery Volley', 'Feuersalve', 'Salva ígnea', 'Salva infuocata', 'Vurig salvo', 'Salva ígnea'), dict(add={'count': 2})),],
 'pieu_vampirique': [('pieu_soif', N('Soif de sang', 'Bloodthirst', 'Blutdurst', 'Sed de sangre', 'Sete di sangue', 'Bloeddorst', 'Sede de sangue'), dict(mul={'leech': 1.0})),
                     ('pieu_crocs', N('Crocs', 'Fangs', 'Fangzähne', 'Colmillos', 'Zanne', 'Hoektanden', 'Presas'), dict(add={'pierce': 3})),
                     ('pieu_nuit', N('Nuit éternelle', 'Endless Night', 'Ewige Nacht', 'Noche eterna', 'Notte eterna', 'Eeuwige nacht', 'Noite eterna'), dict(mul={'dmg': 0.45})),],
 'baguette_glace': [('glace_blizzard', N('Blizzard', 'Blizzard', 'Schneesturm', 'Ventisca', 'Bufera', 'Sneeuwstorm', 'Nevasca'), dict(add={'aoe': 40})),
                    ('glace_givre', N('Givre profond', 'Deep Frost', 'Tiefer Frost', 'Escarcha profunda', 'Brina profonda', 'Diepe vorst', 'Geada profunda'), dict(add={'slow': 0.2, 'slowDur': 1.2})),
                    ('glace_eclats', N('Éclats de glace', 'Ice Shards', 'Eissplitter', 'Esquirlas de hielo', 'Schegge di ghiaccio', 'IJsscherven', 'Estilhaços de gelo'), dict(add={'count': 2})),],
 'god_rod': [('rod_tonnerre', N('Tonnerre', 'Thunder', 'Donner', 'Trueno', 'Tuono', 'Donder', 'Trovão'), dict(add={'bolt': 1})),
             ('rod_foudre', N('Foudre vive', 'Quick Lightning', 'Schneller Blitz', 'Rayo veloz', 'Fulmine rapido', 'Snelle bliksem', 'Relâmpago veloz'), dict(mul={'cd': -0.3})),
             ('rod_orage', N('Orage divin', 'Divine Storm', 'Göttliches Gewitter', 'Tormenta divina', 'Tempesta divina', 'Goddelijk onweer', 'Tempestade divina'), dict(mul={'dmg': 0.45}, add={'knock': 60})),],
 'canne_bonbon': [('bonbon_sucre', N("Overdose de sucre", 'Sugar Rush', 'Zuckerschock', 'Subidón de azúcar', 'Overdose di zucchero', 'Suikerroes', 'Overdose de açúcar'), dict(mul={'confuse': 1.0})),
                  ('bonbon_sucette', N('Sucette géante', 'Giant Lollipop', 'Riesenlutscher', 'Piruleta gigante', 'Lecca-lecca gigante', 'Reuzenlolly', 'Chupa gigante'), dict(add={'range': 60, 'width': 40})),
                  ('bonbon_caramel', N('Caramel dur', 'Hard Candy', 'Hartes Karamell', 'Caramelo duro', 'Caramella dura', 'Harde karamel', 'Caramelo duro'), dict(mul={'dmg': 0.45})),],
 'dagues_rat_noir': [('rat_egout', N('Lames d’égout', 'Sewer Blades', 'Kanalklingen', 'Hojas de cloaca', 'Lame di fogna', 'Rioolmessen', 'Lâminas de esgoto'), dict(add={'bleed': 3})),
                     ('rat_ombre', N("Dans l'ombre", 'In the Shadows', 'Im Schatten', 'En las sombras', "Nell'ombra", 'In de schaduw', 'Nas sombras'), dict(add={'crit': 0.2})),
                     ('rat_rafale', N('Rafale de lames', 'Blade Flurry', 'Klingenwirbel', 'Ráfaga de hojas', 'Raffica di lame', 'Messenregen', 'Rajada de lâminas'), dict(mul={'cd': -0.35})),],
 'chakra_style': [('chakra_double', N('Double chakra', 'Twin Chakra', 'Doppel-Chakra', 'Chakra doble', 'Chakra doppio', 'Dubbel chakra', 'Chakra duplo'), dict(add={'chakram': 1})),
                  ('chakra_cyclone', N('Cyclone', 'Cyclone', 'Zyklon', 'Ciclón', 'Ciclone', 'Cycloon', 'Ciclone'), dict(set={'sides': 4})),
                  ('chakra_acier', N("Fil d'acier", 'Steel Edge', 'Stahlschneide', 'Filo de acero', "Filo d'acciaio", 'Stalen snede', 'Fio de aço'), dict(mul={'dmg': 0.45})),],
 'epee_dark_vlad': [('vlad_croissant', N('Croissant de lune', 'Crescent Moon', 'Mondsichel', 'Media luna', 'Falce di luna', 'Maansikkel', 'Quarto crescente'), dict(add={'wave': 1})),
                    ('vlad_comte', N('Soif du Comte', "The Count's Thirst", 'Durst des Grafen', 'Sed del Conde', 'Sete del Conte', 'Dorst van de Graaf', 'Sede do Conde'), dict(add={'leech': 0.004})),
                    ('vlad_ombre', N('Lame des ténèbres', 'Blade of Darkness', 'Klinge der Finsternis', 'Hoja de las tinieblas', 'Lama delle tenebre', 'Zwaard der duisternis', 'Lâmina das trevas'), dict(add={'range': 60, 'width': 30})),],
 'epee_qui_pete': [('pete_tornade', N('Tornade fétide', 'Foul Tornado', 'Stinktornado', 'Tornado fétido', 'Tornado fetido', 'Stinkende tornado', 'Tornado fétido'), dict(add={'cloud': 1})),
                   ('pete_souffle', N('Souffle puissant', 'Mighty Gust', 'Kräftiger Wind', 'Soplo potente', 'Soffio potente', 'Krachtige wind', 'Sopro potente'), dict(add={'knock': 120})),
                   ('pete_gaz', N('Gaz de combat', 'Battle Gas', 'Kampfgas', 'Gas de combate', 'Gas da battaglia', 'Strijdgas', 'Gás de combate'), dict(mul={'dmg': 0.45})),],
 'kaiser': [('kaiser_seisme', N('Grand séisme', 'Great Earthquake', 'Großes Erdbeben', 'Gran terremoto', 'Grande terremoto', 'Grote aardbeving', 'Grande sismo'), dict(add={'quake': 1})),
            ('kaiser_empire', N('Empire', 'Empire', 'Kaiserreich', 'Imperio', 'Impero', 'Keizerrijk', 'Império'), dict(add={'radius': 45})),
            ('kaiser_ordre', N("Ordre de l'Empereur", "Emperor's Order", 'Befehl des Kaisers', 'Orden del Emperador', "Ordine dell'Imperatore", 'Bevel van de Keizer', 'Ordem do Imperador'), dict(add={'stun': 0.6})),],
 'marteau_dragoeuf': [('dragoeuf_fournaise', N('Fournaise', 'Furnace', 'Glutofen', 'Horno', 'Fornace', 'Smeltoven', 'Fornalha'), dict(add={'firePatch': 0.8})),
                      ('dragoeuf_ecaille', N('Écaille de dragon', 'Dragon Scale', 'Drachenschuppe', 'Escama de dragón', 'Scaglia di drago', 'Drakenschub', 'Escama de dragão'), dict(mul={'dmg': 0.55})),
                      ('dragoeuf_souffle', N('Souffle du dragon', "Dragon's Breath", 'Drachenatem', 'Aliento de dragón', 'Soffio del drago', 'Drakenadem', 'Sopro do dragão'), dict(add={'radius': 40, 'knock': 80})),],
 'ares': [('ares_furie', N('Furie divine', 'Divine Fury', 'Göttlicher Zorn', 'Furia divina', 'Furia divina', 'Goddelijke furie', 'Fúria divina'), dict(add={'stack': 1})),
          ('ares_guerre', N('Dieu de la guerre', 'God of War', 'Kriegsgott', 'Dios de la guerra', 'Dio della guerra', 'God van de oorlog', 'Deus da guerra'), dict(mul={'dmg': 0.45})),
          ('ares_fracas', N('Fracas', 'Crash', 'Getöse', 'Estruendo', 'Fragore', 'Geraas', 'Estrondo'), dict(add={'radius': 36})),],
 'pelle_gateau': [('gateau_patissier', N('Maître pâtissier', 'Pastry Chef', 'Konditormeister', 'Maestro pastelero', 'Maestro pasticciere', 'Meesterbakker', 'Mestre pasteleiro'), dict(add={'cake': 0.04})),
                  ('gateau_chantilly', N('Chantilly', 'Whipped Cream', 'Sahne', 'Nata montada', 'Panna montata', 'Slagroom', 'Chantilly'), dict(add={'radius': 36, 'stun': 0.3})),
                  ('gateau_gourmand', N('Gourmandise', 'Sweet Tooth', 'Naschkatze', 'Golosina', 'Golosità', 'Zoetekauw', 'Gulodice'), dict(add={'dig': 0.3})),],
 'bardiche': [('bardiche_milice', N('Ronde de la milice', 'Militia Patrol', 'Milizstreife', 'Ronda de la milicia', 'Ronda della milizia', 'Militiepatrouille', 'Ronda da milícia'), dict(add={'range': 60, 'width': 40})),
              ('bardiche_garde', N('Garde à vous', 'Attention!', 'Stillgestanden!', '¡Firmes!', 'Attenti!', 'Geef acht!', 'Sentido!'), dict(add={'knock': 120, 'stun': 0.4})),
              ('bardiche_hallebarde', N('Hallebarde', 'Halberd', 'Hellebarde', 'Alabarda', 'Alabarda', 'Hellebaard', 'Alabarda'), dict(add={'bleed': 3})),],
 'hache_zoth': [('zoth_guerrier', N('Guerrier Zoth', 'Zoth Warrior', 'Zoth-Krieger', 'Guerrero Zoth', 'Guerriero Zoth', 'Zoth-krijger', 'Guerreiro Zoth'), dict(mul={'dmg': 0.55})),
                ('zoth_tourbillon', N('Tourbillon Zoth', 'Zoth Whirl', 'Zoth-Wirbel', 'Torbellino Zoth', 'Turbine Zoth', 'Zoth-werveling', 'Turbilhão Zoth'), dict(set={'sides': 4})),
                ('zoth_sang', N('Sang du clan', 'Clan Blood', 'Blut des Clans', 'Sangre del clan', 'Sangue del clan', 'Clanbloed', 'Sangue do clã'), dict(add={'bleed': 3, 'range': 30})),],
}
def desc_of(e):
    parts = []
    for k, v in (e.get('mul') or {}).items():
        if k == 'dmg': parts.append(('dmg', round(v * 100)))
        elif k == 'cd': parts.append(('cd', round(-v * 100)))
        elif k in TPL: parts.append((k, None))
    for k, v in (e.get('add') or {}).items():
        if k in ('slowDur', 'width'): continue
        n = round(v * 100) if k == 'crit' else (int(v) if float(v).is_integer() else v)
        parts.append((k, n))
    for k, v in (e.get('set') or {}).items():
        if k == 'sides' and v == 4: parts.append(('sides4', None))
    return {lg: ' '.join(TPL[k][lg].replace('{n}', str(n)) for k, n in parts) for lg in TPL['dmg']}
for u in C['uniqueWeapons']:
    L = UF.get(u['id'])
    if not L: continue
    C['weaponEvo'][u['id']] = [dict(id=i, name=nm, desc=desc_of(e), max=1, icon=u['icon'], **e) for i, nm, e in L]

# the spell shop's power: what it really does since 0.34 (the old text said +5 %, the game gives +10 % per level)
INTRO = T('Améliorez les sorts de chaque classe : +10 % de puissance par niveau, 5 niveaux par sort. La puissance vaut pour tout le sort : dégâts, soins, durée, invocations, boucliers, et un temps de recharge plus court. Le maître de classe approuve.',
          'Upgrade every class spell: +10% power per level, 5 levels per spell. Power counts for the whole spell: damage, heals, duration, summons, shields, and a shorter cooldown. Your class master approves.',
          'Verbessere jeden Klassenzauber: +10 % Kraft pro Stufe, 5 Stufen pro Zauber. Die Kraft gilt für den ganzen Zauber: Schaden, Heilung, Dauer, Beschwörungen, Schilde und eine kürzere Abklingzeit. Dein Klassenmeister ist zufrieden.',
          'Mejora cada hechizo de clase: +10 % de poder por nivel, 5 niveles por hechizo. El poder vale para todo el hechizo: daño, curas, duración, invocaciones, escudos y un tiempo de recarga más corto. Tu maestro de clase lo aprueba.',
          'Migliora ogni incantesimo di classe: +10% di potenza per livello, 5 livelli per incantesimo. La potenza vale per tutto l\'incantesimo: danni, cure, durata, evocazioni, scudi e una ricarica più breve. Il tuo maestro di classe approva.',
          'Verbeter elke klassenspreuk: +10% kracht per niveau, 5 niveaus per spreuk. Kracht geldt voor de hele spreuk: schade, genezing, duur, oproepingen, schilden en een kortere afkoeltijd. Je klassenmeester keurt het goed.',
          'Melhora cada feitiço de classe: +10% de poder por nível, 5 níveis por feitiço. O poder vale para todo o feitiço: dano, curas, duração, invocações, escudos e um tempo de recarga mais curto. O teu mestre de classe aprova.')
for lg in C['ui']: C['ui'][lg]['spell_intro'] = INTRO[lg]

# "lâcher" -> "dropper" (the MMO word: a monster drops an item; Dofus players don't say it "lâche" it). Only where it
# means dropping an item (not "Lâcher les gaz", "ne lâche jamais", "Tiwoflan le Lâche")
import re as _re
DROPFR = [(r'\bpeut lâcher\b', 'peut dropper'), (r'\bPeut lâcher\b', 'Peut dropper'), (r'\bLâché par\b', 'Droppé par'), (r'\ba lâché le\b', 'a droppé le'),
          (r'\blâche des kamas\b', 'droppe des kamas'), (r'Coffre Animé lâche :', 'Coffre Animé droppe :'), (r'qu\'il lâchait', 'qu\'il droppait')]
def _fixfr(o):
    if isinstance(o, dict):
        for k, v in o.items():
            if k == 'fr' and isinstance(v, str):
                for a, b in DROPFR: v = _re.sub(a, b, v)
                o[k] = v
            else: _fixfr(v)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            if isinstance(v, str) and o is C['tips'].get('fr'):
                for a, b in DROPFR: v = _re.sub(a, b, v)
                o[i] = v
            else: _fixfr(v)
_fixfr(C)
for k in list(C['ui']['fr']):
    v = C['ui']['fr'][k]
    for a, b in DROPFR: v = _re.sub(a, b, v)
    C['ui']['fr'][k] = v

# ---------------------------------------------------------------- balance (0.34)
import statistics
M = C['monsters']
lambda_speed = statistics.median(m['speed'] for m in M.values() if 'speed' in m)
FAST = []
for k, m in M.items():
    if m.get('special') or k in ('corbac_doom', 'coffre_anime', 'tofu_mutant'): continue
    if m.get('speed', 0) >= 130 and m.get('hp', 999) <= 60:   # fast and weak: Tofus, mice, mosquitoes, crabs…
        FAST.append(k); m['speed'] = round(lambda_speed * 1.03); m['dmg'] = round(m['dmg'] * 0.65, 2)
for m in M.values(): m['dmg'] = round(m['dmg'] * 0.85, 2)   # every monster hits 15 % softer
C['run']['breadRate'] = round(C['run']['breadRate'] * 1.25, 6)   # bread 25 % more often
for c in C['classes']:
    if c['id'] == 'cra': c['base']['hp'] -= 2
    if c['id'] == 'sadida': c['base']['hp'] += 5
print('fast & weak:', len(FAST), FAST, 'speed', round(lambda_speed * 1.03))

# ---------------------------------------------------------------- unique weapons: about 5 % above their weapon type at
# every level (factors on their damage from the weapon bench, BENCH=weapons LV=1,6 DUR=120, 3 runs averaged; lv 1 and
# lv 6, in between interpolated). The damage of their own effects follows (they read the weapon's dmg)
UCAL = {'arc_ange': [0.4, 0.87], 'arc_feugeuf': [0.73, 1.18], 'pieu_vampirique': [0.89, 0.94], 'baguette_glace': [0.65, 0.73], 'god_rod': [0.76, 1.15], 'canne_bonbon': [0.96, 0.58], 'dagues_rat_noir': [0.68, 0.78], 'chakra_style': [0.59, 0.47], 'epee_dark_vlad': [0.67, 0.97], 'epee_qui_pete': [0.58, 1.11], 'kaiser': [0.91, 0.79], 'marteau_dragoeuf': [0.83, 0.94], 'ares': [1.12, 0.97], 'pelle_gateau': [1.26, 0.73], 'bardiche': [1.11, 0.81], 'hache_zoth': [0.91, 0.67]}
UCAL2 = {'arc_ange': [0.6, 1.02], 'arc_feugeuf': [1.08, 1.01], 'pieu_vampirique': [1.02, 0.97], 'baguette_glace': [0.78, 0.68], 'god_rod': [0.85, 1.0], 'canne_bonbon': [1.02, 0.6], 'dagues_rat_noir': [1.28, 1.19], 'chakra_style': [1.04, 1.06], 'epee_dark_vlad': [0.89, 1.01], 'epee_qui_pete': [1.03, 1.21], 'kaiser': [0.84, 0.87], 'marteau_dragoeuf': [1.08, 0.9], 'ares': [0.98, 0.93], 'pelle_gateau': [1.29, 1.01], 'bardiche': [0.92, 0.97], 'hache_zoth': [1.2, 1.27]}   # (second pass, after a re-bench)
for u in C['uniqueWeapons']:
    f1, f6 = UCAL.get(u['id'], (1, 1)); g1, g6 = UCAL2.get(u['id'], (1, 1)); f1 *= g1; f6 *= g6
    f = lambda i: f1 + (f6 - f1) * (i - 1) / 5
    u['base']['dmg'] = round(u['base']['dmg'] * f(1), 1)
    for i, l in enumerate(u['lv']):
        if 'dmg' in l: l['dmg'] = round(l['dmg'] * f(i + 1), 1)

# 6 Millions de Prouts: with its capital M
_PN = T('6 Millions de Prouts', '6 Million Farts', '6 Millionen Pupse', '6 Millones de Pedos', '6 Milioni di Peti', '6 Miljoen Scheten', '6 Milhões de Puns')
C['spells']['prouts']['name'] = _PN
for g in C.get('globalSpells', []):
    if g.get('id') == 'prouts' and 'name' in g: g['name'] = _PN

# Marteau de Moon as the client casts it (spell 366, clip 2051: the swirl, its arcs and the spark; tools/assets/build_moon34.py),
# with its own sound (the clip plays 'wab_swirl')
_mm = C['spells']['marteau_moon']; _mm['fx'] = [2051]; _mm['base'].pop('drawIcon', None); _mm['snd'] = 'wab_swirl'

# Archimonsters: one soul = one monster (they were matched by look, so the six Pious shared six souls, Serpentin and
# Cooleuvre two, the Boomba / Canon Dorf / Nakunbra variants theirs: 194 entries for 153 different souls, 100 % was out
# of reach). Each goes to the monster its name / client colours point at
ARCHI_OF = {2341: 'piou_bleu', 2342: 'piou_rouge', 2343: 'piou_rose', 2344: 'piou_jaune', 2345: 'piou_vert', 2347: 'piou_violet',
            2286: 'serpentin', 2434: 'cooleuvre', 2592: 'pandit', 2593: 'pandikaze', 2408: 'boomba', 2419: 'canon_dorf', 2538: 'nakunbra'}
for mob in list(C['archi']):
    C['archi'][mob] = [a for a in C['archi'][mob] if ARCHI_OF.get(a['id'], mob) == mob]
    if not C['archi'][mob]: del C['archi'][mob]
# (0.35) one soul per look: a single Archimonster per monster skin (gfx), each with the original game's level,
# the soul list is sorted by it
_lvl = {}
for _k, _v in json.load(open(f'{_ROOT0}/work/lang_json/monsters_fr.json'))['M'].items():
    if isinstance(_v, dict) and _v.get('g1'): _lvl[int(_k)] = _v['g1'].get('l', 0)
_seen = set()
for mob in sorted(C['archi'], key=lambda m: C['monsters'][m].get('did', 0)):
    g = C['monsters'][mob]['gfx']; keep = []
    for a in C['archi'][mob]:
        if g in _seen: continue
        _seen.add(g); a['lv'] = _lvl.get(a['id'], 0); keep.append(a)
    if keep: C['archi'][mob] = keep
    else: del C['archi'][mob]
_ids = [a['id'] for l in C['archi'].values() for a in l]; assert len(_ids) == len(set(_ids)), 'archi duplicates'

# the Tofu Mutant's client walk is a four-frame shuffle (it looked like sliding): the escaping tofu is now a Tofuzmo
# (client monster 807, gfx 1373, a real seven-frame run; sheet 1373_z40 by build_mobs20), named so in every text
_tm = C['monsters']['tofu_mutant']; _tm.update(did=807, gfx=1373, sprite='1373_z40', name=T(*['Tofuzmo'] * 7))
_TZ = [(r'Tofu Mutant\b', 'Tofuzmo'), (r'Mutant Tofu', 'Tofuzmo'), (r'Mutierte[nrs]? Tofus?', 'Tofuzmo'), (r'Tofus? Mutantes?', 'Tofuzmo'), (r'Gemuteerde Tofu', 'Tofuzmo'), (r'Mutanten-Tofus?', 'Tofuzmo'), (r'Mutant-Tofu', 'Tofuzmo'), (r'Mutantentofu', 'Tofuzmo')]
def _tz(o):
    if isinstance(o, dict):
        for k in o: o[k] = _tz(o[k])
    elif isinstance(o, list): return [_tz(v) for v in o]
    elif isinstance(o, str):
        for a, b in _TZ: o = _re.sub(a, b, o)
    return o
for _k in list(C): C[_k] = _tz(C[_k])

# the TTG cards at last (464, the official list: tools/assets/build_ttg34.py -> work/ttg34.json, pictures in assets/ttg):
# a booster gives a common card 55 % of the time, a rare 30 %, an epic 12 %, a unique 3 %
from _root import ROOT as _ROOT
if _os.path.exists(f'{_ROOT}/work/ttg34.json'):
    C['ttg']['cards'] = json.load(open(f'{_ROOT}/work/ttg34.json')); C['ttg']['rw'] = [55, 30, 12, 3]

# (0.35) bosses -20 %, still a round number (next 1000 up); the escaping Tofuzmo 5000 -> 3500 HP
import math as _math
for _b in C['bosses'].values():
    if _b.get('hp'): _b['hp'] = int(_math.ceil(_b['hp'] * 0.8 / 1000) * 1000)
C['mutant']['hp'] = 3500
for _lg in C['ui']:
    for _k in ('mutant_appears',): C['ui'][_lg][_k] = C['ui'][_lg][_k].replace('5000', '3500').replace('5 000', '3 500')

# ---------------------------------------------------------------- new UI strings (0.34)
UI34 = {
    'locked_hint': T('Terminez la zone précédente en battant tous ses boss', 'Finish the previous zone and beat all of its bosses', 'Beende die vorige Zone und besiege alle ihre Bosse', 'Termina la zona anterior venciendo a todos sus jefes', 'Completa la zona precedente battendo tutti i suoi boss', 'Voltooi de vorige zone en versla al haar bazen', 'Termina a zona anterior vencendo todos os seus chefes'),
    'auto_on': T('Choix automatique : {n}', 'Auto-pick: {n}', 'Automatische Wahl: {n}', 'Elección automática: {n}', 'Scelta automatica: {n}', 'Automatische keuze: {n}', 'Escolha automática: {n}'),
    'auto_off2': T('Choix automatique désactivé', 'Auto-pick off', 'Automatische Wahl aus', 'Elección automática desactivada', 'Scelta automatica disattivata', 'Automatische keuze uit', 'Escolha automática desligada'),
}

def put_ui(D):
    for k, v in D.items():
        for lg in C['ui']: C['ui'][lg][k] = v[lg]
UI34.update({
    'ren_title': T('Nom du profil {n}', 'Profile {n} name', 'Name von Profil {n}', 'Nombre del perfil {n}', 'Nome del profilo {n}', 'Naam van profiel {n}', 'Nome do perfil {n}'),
    'ren_hint': T('8 caractères au plus. Tapez au clavier ou choisissez les lettres ci-dessous.', '8 characters at most. Type on your keyboard or pick the letters below.', 'Höchstens 8 Zeichen. Tippe auf der Tastatur oder wähle die Buchstaben unten.', '8 caracteres como máximo. Escribe con el teclado o elige las letras de abajo.', 'Al massimo 8 caratteri. Scrivi con la tastiera o scegli le lettere qui sotto.', 'Hoogstens 8 tekens. Typ op je toetsenbord of kies de letters hieronder.', 'No máximo 8 caracteres. Escreve no teclado ou escolhe as letras abaixo.'),
    'ren_random': T('Aléatoire', 'Random', 'Zufällig', 'Aleatorio', 'Casuale', 'Willekeurig', 'Aleatório'),
    'ctl_auto': T('Choix auto pain / kamas', 'Auto bread / kamas', 'Auto-Wahl Brot / Kamas', 'Pan / kamas automático', 'Pane / kama automatico', 'Auto brood / kama', 'Pão / kamas automático'),
    'ctl_mouse': T('clic gauche maintenu (vers le curseur)', 'hold left click (towards the cursor)', 'linke Maustaste halten (zum Mauszeiger)', 'mantén el clic izquierdo (hacia el cursor)', 'tieni premuto il clic sinistro (verso il cursore)', 'linkermuisknop ingedrukt (naar de cursor)', 'mantém o clique esquerdo (em direção ao cursor)'),
    'ctl_clickicon': T('clic sur son icône', 'click its icon', 'Klick auf sein Symbol', 'clic en su icono', 'clic sulla sua icona', 'klik op het pictogram', 'clique no ícone'),
    'ctl_inrun': T('en partie', 'in a run', 'im Lauf', 'en partida', 'in partita', 'tijdens een run', 'em jogo'),
    'ctl_autotap': T("Touchez l'icône pain / kamas (à droite de la plume)", 'Tap the bread / kamas icon (right of the feather)', 'Tippe auf das Brot-/Kamas-Symbol (rechts der Feder)', 'Toca el icono pan / kamas (a la derecha de la pluma)', "Tocca l'icona pane / kama (a destra della piuma)", 'Tik op het brood- / kama-pictogram (rechts van de veer)', 'Toca no ícone pão / kamas (à direita da pena)'),
    'konami_tofu': T('Tofu !', 'Tofu!', 'Tofu!', '¡Tofu!', 'Tofu!', 'Tofu!', 'Tofu!'),
    'lvl_short': T('Niv.', 'Lv.', 'St.', 'Niv.', 'Liv.', 'Niv.', 'Nív.'),
    'booster_here': T("Un booster de cartes TTG est apparu dans un coin de la carte !", 'A TTG card booster appeared in a corner of the map!', 'Ein TTG-Booster ist in einer Ecke der Karte aufgetaucht!', '¡Un sobre de cartas TTG ha aparecido en una esquina del mapa!', "Una bustina di carte TTG è apparsa in un angolo della mappa!", 'Er is een TTG-booster verschenen in een hoek van de kaart!', 'Apareceu um booster de cartas TTG num canto do mapa!'),
    # 0.35: short statistic labels (the records were cut)
    'st_best_kills': T('Kills max', 'Most kills', 'Max. Kills', 'Máx. muertes', 'Max uccisioni', 'Max kills', 'Máx. abates'),
    'st_best_level': T('Niveau max', 'Top level', 'Max. Stufe', 'Nivel máx.', 'Livello max', 'Max niveau', 'Nível máx.'),
    'st_best_dps': T('Dégâts max / s', 'Best DPS', 'Max. Schaden/s', 'Daño máx./s', 'Danni max/s', 'Max schade/s', 'Dano máx./s'),
    'st_best_kamas': T('Kamas max', 'Most kamas', 'Max. Kamas', 'Kamas máx.', 'Kama max', 'Max kama', 'Kamas máx.'),
    'st_best_time': T('Survie max', 'Longest run', 'Längster Lauf', 'Mayor partida', 'Partita più lunga', 'Langste run', 'Maior partida'),
    'st_doom': T('Survie aux Corbacs', 'Corbac survival', 'Corbac-Überleben', 'Contra Corbacs', 'Contro i Corbac', 'Tegen Corbacs', 'Contra Corbacs'),
    'st_fav_class': T('Classe favorite', 'Top class', 'Lieblingsklasse', 'Clase favorita', 'Classe preferita', 'Favoriete klasse', 'Classe favorita'),
    'st_fav_weapon': T('Arme favorite', 'Top weapon', 'Lieblingswaffe', 'Arma favorita', 'Arma preferita', 'Favoriet wapen', 'Arma favorita'),
    'st_fav_spell': T('Sort n° 1', 'Top spell', 'Bester Zauber', 'Hechizo n.º 1', 'Incantesimo n. 1', 'Beste spreuk', 'Feitiço n.º 1'),
    'st_nemesis': T('Pire ennemi', 'Nemesis', 'Erzfeind', 'Peor enemigo', 'Nemico n. 1', 'Aartsvijand', 'Pior inimigo'),
    'st_wins': T('Boss finaux', 'Final bosses', 'Endbosse', 'Jefes finales', 'Boss finali', 'Eindbazen', 'Chefes finais'),
    'st_distance': T('Distance', 'Distance', 'Strecke', 'Distancia', 'Distanza', 'Afstand', 'Distância'),
    'st_kpm': T('Monstres / min', 'Kills / min', 'Kills / Min', 'Muertes / min', 'Uccisioni / min', 'Kills / min', 'Abates / min'),
    'shop_glob': T('Communs', 'Common', 'Allgemein', 'Comunes', 'Comuni', 'Algemeen', 'Comuns'),
    'ren_ok': T('Valider', 'OK', 'OK', 'Aceptar', 'OK', 'OK', 'OK'),
})
# the performance mode keeps 60 fps since 0.34 (no more ', 30 fps' in its hint)
for lg in C['ui']:
    C['ui'][lg]['perf_hint'] = _re.sub(r',? ?(30 images/s|30 fps)', '', C['ui'][lg]['perf_hint'])
put_ui(UI34)

# 0.34: the random profile names: the client's NPC names of 8 characters at most (no job titles)
import re as _re2
from _root import ROOT as _ROOT
_npc = json.load(open(f'{_ROOT}/work/lang_json/npc_fr.json'))['N']['d']
_JOBS = {'Banquier', 'Classman', 'Corbac', 'Docker', 'Gardien', 'Gobelin', 'Marin', 'Milicien', 'Prêtre', 'Servante', 'Tourist', 'Tourista', 'Vagabond', 'Test', 'Marquis', 'Mousse', 'Neige', 'Torche', 'Trape', 'Thanos', 'Dikaprio', 'Paindep'}
C['npcNames'] = sorted({v['n'].strip() for v in _npc.values() if isinstance(v, dict) and 'n' in v and len(v['n'].strip()) <= 8
                        and _re2.fullmatch(r"[A-ZÀ-Ý][A-Za-zÀ-ÿ'\-]*( [A-ZÀ-Ý][A-Za-zÀ-ÿ'\-]*)?", v['n'].strip()) and v['n'].strip() not in _JOBS})

if __name__ == '__main__':
    json.dump(C, open(f'{G}/data/content.json', 'w'), ensure_ascii=False, separators=(',', ':'))
    print('0.34 ok')
