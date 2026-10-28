"""0.96 content, on top of patch_095:
- Épée du Destin (Iop fusion fu_iop_destin): no more client clip 814 (Épée du Destin's own line of fire) on each monster its
  orbiting swords touch, nor at the fusion's show: a horizontal blaze flashing on every touch read as another spell
- new global spell Boule de Chaos (`boule_chaos`, gspells.js chaosTrail / chaosBurst, render.js drawChaosBall): a big
  violet fireball thrown straight at the nearest monster (no homing), exploding on the first one it touches (projectile
  `aoe`), the Flamiche's client burst (fx 4600 'shoot') tinted violet; icon sp_g_chaos (build_globalicons060: the client's
  Orbe reconstituant, it_50_460)
- new fusion Marteau du Chaos (`fu_chaos_marteau`, any class: Boule de Chaos + Marteau de Moon): the Marteau de Moon at its
  top level, its blows x1.3, its trail violet; each blow opens two little void rifts (sfusions.js riderHit rChaos, 0.5 s)
- Élagage de cou (Brigandin): cooldown 1.5 s with no shop level, 1.0 s at 5/5 (cd / cdShop, SpellInst.cooldown)
- Cupidité (Enutrof fusion fu_enu_pioche): cooldown -10 % (1.357 -> 1.221 s)
- Roublard: base speed 107 % -> 110 %; Écaflip: base might 105 % -> 115 %, speed 105 % -> 110 %
- Immunité (Féca): at its first level 35 s / 1.5 s with no shop level, 30 s / 2.0 s at 5/5 (cd / cdShop, duration /
  durShop); its levels 2-4 keep their steps (same ratios as before)
- string sf_extra: the Armurerie's fusions show their damage and cooldown, and this line when their effects add damage
- the game's check: the Écaflip's passive text (+15 % luck, not critical hits), La bonne Pioche's text (no '5 seconds'),
  the Tofuzmo's announcement with its real life ({hp}), the Hard mode's tooltip (the old numbers), the crows' warning with
  their real time ({t}), the Pieu vampirique's pierce (3 more), the ToT tip (Jorbak further on); decisions: the
  Osamodas's text +40 % (keeps x1.4), the Iop's might 115 % + his passive +12 % (passiveStats: 127 % in a run), Cupidité
  a bit above Lancer de Pièces at its top (blows 34), Élagage de tête about 20 % above Élagage de cou (blows 24, its cadence)
- Démultiplication and the Craqueleur's legendary belt: their extra copies hit at 50 % (C.run.extraK, SpellInst.extraK)
usage: python tools/make_content.py   (runs the newest patch; this one imports patch_095 and writes game/data/content.json)"""
import sys as _sys, os as _os, json
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
import _root
import patch_095 as P

C, G, T, put_ui = P.C, P.G, P.T, P.put_ui
S = C['spells']
def lvl(d, n=4):
    """a spell's parameters at level n (game.js spellParams: the level steps merged in order)"""
    p = dict(d['base'])
    for l in d['lv'][:n]: p.update(l)
    return p

# ---------------------------------------------------------------- Épée du Destin: no line of fire
IO = S['fu_iop_destin']; IO['fx'] = []; IO.pop('fx2')

# ---------------------------------------------------------------- Boule de Chaos (global spell)
# Numbers: the Marteau de Moon's place among the global spells (both projectiles, one slot each). Spell bench (sim_node
# BENCH, 3 maps, 90 s) at BOULE_K 1: x0.67 the Marteau de Moon at level 1 (45 / 68 dps), x0.69 at level 4 (125 / 180)
BOULE_K = 1.45
S['boule_chaos'] = dict(
    id='boule_chaos', t='projectile', anim=None, fx=[4600], icon='g_chaos', sid=0, glob=1, snd='vlad_805',
    name=T('Boule de Chaos', 'Chaos Ball', 'Chaoskugel', 'Bola de Caos', 'Sfera del Caos', 'Chaosbol', 'Bola do Caos'),
    desc=T("Une énorme boule de feu violet fonce droit sur le monstre le plus proche et explose au premier contact. Le chaos ne vise pas deux fois.",
           'A huge violet fireball rushes straight at the nearest monster and explodes on first contact. Chaos never aims twice.',
           'Eine riesige violette Feuerkugel rast geradewegs auf das nächste Monster zu und explodiert bei der ersten Berührung. Das Chaos zielt nie zweimal.',
           'Una enorme bola de fuego violeta se lanza en línea recta hacia el monstruo más cercano y estalla al primer contacto. El caos nunca apunta dos veces.',
           'Un\'enorme palla di fuoco viola si lancia dritta sul mostro più vicino ed esplode al primo contatto. Il caos non mira mai due volte.',
           'Een enorme paarse vuurbal schiet recht op het dichtstbijzijnde monster af en ontploft bij de eerste aanraking. Chaos mikt nooit twee keer.',
           'Uma enorme bola de fogo violeta dispara a direito para o monstro mais próximo e explode ao primeiro contacto. O caos nunca aponta duas vezes.'),
    base={'dmg': round(40 * BOULE_K, 1), 'count': 1, 'speed': 230, 'cd': 3.2, 'pierce': 1, 'size': 46, 'life': 2.4, 'target': 'nearest', 'aoe': 100, 'chaos': 1, 'tint': '#a64dff'},
    lv=[{}, {'dmg': round(52 * BOULE_K, 1), 'aoe': 110}, {'dmg': round(66 * BOULE_K, 1), 'cd': 2.8, 'aoe': 120}, {'dmg': round(84 * BOULE_K, 1), 'aoe': 135, 'size': 50}])
C['globalSpells'].append({'id': 'boule_chaos', 'w': 1.0})

# ---------------------------------------------------------------- Marteau du Chaos (fusion, any class)
# The Marteau de Moon at its top level (3 hammers, every 2.85 s, a random arc and back), its blows x1.3. Each blow
# opens two void rifts (radius 36, 0.5 s, a blow at 0.25 and at 0.5 s, RIFT_K of the hammer's blow; one clock for all the
# rifts: a monster under several of them is hit once per 0.25 s). A monster on a hammer's way takes 1.3 + 2 x RIFT_K x 1.3
# = 1.8 Marteau de Moon blows a pass (moderate rifts). The rifts also hit the crowd round the blow: on the spell
# bench (3 maps) the fusion did 384 dps against 180 for the Marteau de Moon at level 4, about x1.07 the two spells side by
# side once the Boule de Chaos is at the Moon's level (other fusions: x1.25), with one slot instead of two
MO = lvl(S['marteau_moon']); RIFT_K = 0.19
assert abs((1.3 + 2 * RIFT_K * 1.3) - 1.8) < 0.01
S['fu_chaos_marteau'] = dict(
    id='fu_chaos_marteau', t='projectile', anim=None, fx=list(S['marteau_moon']['fx']), snd=S['marteau_moon']['snd'], sid=0,
    icon='sf_fu_chaos_marteau', sfusion=1, cls=None, src=['boule_chaos', 'marteau_moon'], fkind='global', lv=[],
    name=T('Marteau du Chaos', 'Chaos Hammer', 'Chaoshammer', 'Martillo del Caos', 'Martello del Caos', 'Chaoshamer', 'Martelo do Caos'),
    desc=T("Les marteaux de Moon, gorgés de chaos, frappent plus fort et ouvrent de petites failles du Néant là où ils cognent.",
           "Moon's hammers, swollen with chaos, hit harder and open little rifts of the Void wherever they strike.",
           'Moons Hämmer, voller Chaos, schlagen härter zu und reißen kleine Risse ins Nichts, wo sie treffen.',
           'Los martillos de Moon, rebosantes de caos, golpean más fuerte y abren pequeñas grietas del Vacío allí donde pegan.',
           'I martelli di Moon, gonfi di caos, colpiscono più forte e aprono piccole crepe del Vuoto dove colpiscono.',
           'Moons hamers, vol chaos, slaan harder en openen kleine scheuren in de Leegte waar ze inslaan.',
           'Os martelos de Moon, cheios de caos, batem mais forte e abrem pequenas fendas do Vazio onde acertam.'),
    base=dict(MO, dmg=round(MO['dmg'] * 1.3, 2), rChaos=RIFT_K, rChaosR=36, tint='#a64dff'))
assert S['fu_chaos_marteau']['base']['dmg'] == 62.4
C['spellFusions'].append({'id': 'fu_chaos_marteau', 'cls': None, 'src': ['boule_chaos', 'marteau_moon'], 'kind': 'global'})

# ---------------------------------------------------------------- balance values
S['elagage_cou']['base'].update(cd=1.5, cdShop=1.0)
S['fu_enu_pioche']['base']['cd'] = round(S['fu_enu_pioche']['base']['cd'] * 0.9, 3)
assert S['fu_enu_pioche']['base']['cd'] == 1.221
# (after the check: Cupidité a bit stronger than Lancer de Pièces at its top, Élagage de tête about 20 % above
# Élagage de cou at its top) — their blow, calibrated on the spell bench below; Élagage de tête takes Élagage de cou's
# cadence (1.5 s -> 1.0 s over the shop) so the gap holds at every shop level
# Bench (sim_node BENCH, level 4, 3 maps): Cupidité x1.00 Lancer de Pièces with blows of 30, x1.12 with 34 (it was x0.58:
# 158 / 271 dps). Élagage de tête (4 sides, bleeding, executes under 50 %) was x8 Élagage de cou (402 / 48); at its
# cadence, 6 runs each: blows of 20 -> x0.84, 26 -> x1.36, so 24 (on paper: 2.27 x the strip, x1.4 the bleeding, crits:
# 22). Its blow is lower than Élagage de cou's 59.4 because it strikes all round, bleeds and executes.
CUP_DMG, TETE_DMG = 34, 24
S['fu_enu_pioche']['base']['dmg'] = CUP_DMG
S['fu_ban_tete']['base'].update(dmg=TETE_DMG, cd=1.5, cdShop=1.0)
CL = {c['id']: c for c in C['classes']}
CL['roublard']['base']['speed'] = 1.10
CL['ecaflip']['base'].update(might=1.15, speed=1.10)
# Immunité: 35 s / 1.5 s -> 30 s / 2.0 s over the shop at its first level; its levels keep their old steps
IM = S['immunite']; c0, d0 = IM['base']['cd'], IM['base']['duration']
IM['base'].update(cd=35.0, cdShop=30.0, duration=1.5, durShop=2.0)
for l in IM['lv'][1:]:
    rc, rd = l['cd'] / c0, l['duration'] / d0
    l.update(cd=round(35 * rc, 3), cdShop=round(30 * rc, 3), duration=round(1.5 * rd, 3), durShop=round(2.0 * rd, 3))

# ---------------------------------------------------------------- the Armurerie's fusions: their damage and cooldown (ui.js sfStats)
put_ui({'sf_extra': T('+ les dégâts des effets décrits', '+ the damage of the effects described', '+ der Schaden der beschriebenen Effekte',
                      '+ el daño de los efectos descritos', '+ i danni degli effetti descritti', '+ de schade van de beschreven effecten', '+ o dano dos efeitos descritos')})

# ---------------------------------------------------------------- 0.96 check of the game: texts that said something else than the game does
# the Écaflip's passive gives +15 % luck (Run.recompute, as in the v1.9 text '+15% chance'), the texts said critical hits
EC = CL['ecaflip']['passive']
for lg, a, b in (('fr', '+15 % de critiques', '+15 % de chance'), ('en', '+15% critical chance', '+15% luck'), ('de', '+15 % kritische Trefferchance', '+15 % Glück'),
                 ('es', '+15 % de críticos', '+15 % de suerte'), ('it', '+15% di critici', '+15% di fortuna'), ('nl', '+15% kritieke treffers', '+15% geluk'), ('pt', '+15% de críticos', '+15% de sorte')):
    assert a in EC[lg], lg; EC[lg] = EC[lg].replace(a, b)
# La bonne Pioche said 'every 5 seconds': its cooldown is 6.8 s (5.4 s with the whole shop); its card shows the real one
PI = S['pioche']['desc']
for lg, a, b in (('fr', 'toutes les 5 secondes', 'régulièrement'), ('en', 'every 5 seconds', 'every few seconds'), ('de', 'Alle 5 Sekunden gräbt', 'Regelmäßig gräbt'),
                 ('es', 'cada 5 segundos', 'cada pocos segundos'), ('it', 'ogni 5 secondi', 'a intervalli regolari'), ('nl', 'elke 5 seconden', 'om de paar seconden'), ('pt', 'a cada 5 segundos', 'a cada poucos segundos')):
    assert a in PI[lg], lg; PI[lg] = PI[lg].replace(a, b)
# the Tofuzmo's announcement said 1000 HP when the beginners' help left it 700: its real life now ({hp}, events.js spawnMutant)
for lg in P.LG: assert '1000' in C['ui'][lg]['mutant_appears'], lg; C['ui'][lg]['mutant_appears'] = C['ui'][lg]['mutant_appears'].replace('1000', '{hp}')
# the play screen's Normal / Hard tooltip (mode_hint) still told the old Hard (+50 to 75 % HP, +50 % damage, bosses x2): the
# run's own text (hard_info, C.hard) instead
for lg in P.LG: h = C['ui'][lg]['hard_info']; assert h.startswith('💀 '), lg; C['ui'][lg]['mode_hint'] = h[2:]
# the crows' warning said 10:00 even when they come at 11:00 (C.doom.t; 10:00 only once the final boss is down): their time
for lg in P.LG: assert '10:00' in C['ui'][lg]['doom_soon'], lg; C['ui'][lg]['doom_soon'] = C['ui'][lg]['doom_soon'].replace('10:00', '{t}')
# Pieu vampirique: pierce 4 against the wand's 1, '4 more monsters' said one too many
PV = next(w for w in C['uniqueWeapons'] if w['id'] == 'pieu_vampirique')['desc']
for lg, a, b in (('fr', 'transpercent 4 monstres de plus', 'transpercent 3 monstres de plus'), ('en', 'go through 4 more monsters', 'go through 3 more monsters'),
                 ('de', 'durchbohren 4 Monster mehr', 'durchbohren 3 Monster mehr'), ('es', 'atraviesan 4 monstruos más', 'atraviesan 3 monstruos más'),
                 ('it', 'trapassano 4 mostri in più', 'trapassano 3 mostri in più'), ('nl', 'gaan door 4 extra monsters', 'gaan door 3 extra monsters'),
                 ('pt', 'atravessam mais 4 monstros', 'atravessam mais 3 monstros')):
    assert a in PV[lg], lg; PV[lg] = PV[lg].replace(a, b)
# the ToT tip: from the zone after the 10th it is Jorbak, not the Tofuzmo (C.jorbak.from)
for lg, a, b in (('fr', "c'est le Tofuzmo qui fait le malin.", "c'est le Tofuzmo (Jorbak, plus loin) qui fait le malin."),
                 ('en', 'the Tofuzmo shows off instead.', 'the Tofuzmo (Jorbak, further on) shows off instead.'),
                 ('de', 'Sonst gibt der Tofuzmo an.', 'Sonst gibt der Tofuzmo an (weiter hinten Jorbak).'),
                 ('es', 'el Tofuzmo se hace el listo.', 'el Tofuzmo (Jorbak, más adelante) se hace el listo.'),
                 ('it', 'fa lo spiritoso il Tofuzmo.', 'fa lo spiritoso il Tofuzmo (più avanti Jorbak).'),
                 ('nl', 'speelt de Tofuzmo de slimmerik.', 'speelt de Tofuzmo (verderop Jorbak) de slimmerik.'),
                 ('pt', 'é o Tofuzmo que se arma em esperto.', 'é o Tofuzmo (mais à frente, o Jorbak) que se arma em esperto.')):
    t = C['tips'][lg]; i = next(k for k, x in enumerate(t) if a in x); t[i] = t[i].replace(a, b)
# after the check: the Osamodas's summons keep x1.4 (game.js spawnSummon): the text said +20 %
OS = CL['osamodas']['passive']
for lg in P.LG: assert '+20' in OS[lg], lg; OS[lg] = OS[lg].replace('+20', '+40', 1)
# the Iop's base might 115 % (the class card shows the base) and his passive +12 % on top (passiveStats, added by
# Run.recompute): 127 % in a run; it was 121.8 % in the base alone, the +12 % of his text nowhere
CL['iop']['base']['might'] = 1.15; CL['iop']['passiveStats'] = {'might': 0.12}
# option C of the measured proposals: the copies Démultiplication and the Craqueleur's legendary belt add (st.amount) hit at
# half damage (SpellInst.extraK): as many things on screen, the damage in line (2/2: x1.33 median instead of x1.67, x2 at
# most instead of x3); their texts say it
C['run']['extraK'] = 0.5
DM = next(x for x in C['passives'] if x['id'] == 'invocations')['desc']
for lg, add_ in (('fr', ' Ces exemplaires en plus font 50 % des dégâts.'), ('en', ' These extra copies deal 50% damage.'), ('de', ' Diese zusätzlichen Exemplare verursachen 50 % Schaden.'),
                 ('es', ' Estas copias extra hacen el 50 % del daño.'), ('it', ' Queste copie in più infliggono il 50% dei danni.'), ('nl', ' Deze extra exemplaren doen 50% schade.'), ('pt', ' Estas cópias extra causam 50% do dano.')):
    assert DM[lg].endswith('.'), lg; DM[lg] += add_
CB = next(x for x in C['relics'] if x['id'] == 'ceinture_craqueleur_leg')['desc']
for lg, add_ in (('fr', ' (à 50 % des dégâts)'), ('en', ' (at 50% damage)'), ('de', ' (mit 50 % Schaden)'), ('es', ' (al 50 % del daño)'), ('it', ' (al 50% dei danni)'), ('nl', ' (op 50% schade)'), ('pt', ' (a 50% do dano)')):
    assert CB[lg].endswith('.'), lg; CB[lg] = CB[lg][:-1] + add_ + '.'

if __name__ == '__main__':
    json.dump(C, open(f'{G}/data/content.json', 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
    print('0.96 ok: Immunité', [(l.get('cd'), l.get('cdShop'), l.get('duration'), l.get('durShop')) for l in [IM['base']] + IM['lv'][1:]],
          '| Boule', S['boule_chaos']['lv'][3]['dmg'], '| Marteau du Chaos', S['fu_chaos_marteau']['base']['dmg'])
