"""0.98 content, on top of patch_097 (the numbers the shop shows are at a spell's first level with 5/5 bought: ui.js
menuSpellParams — damage x the class's might x C.run.spellDmgMul x 1.5, cooldown / 1.25, duration x 1.5):
- Invisibilité (Sram): 15.2 s / 2.3 s shown at 5/5 -> 25 s / 1.5 s; every level and shop level keeps its ratios (cd x25/15.2,
  duration x1.5/2.25)
- Flèche Explosive (Cra): 23.6 damage / 1.5 s shown at 5/5 -> 20 / 2 s (damage x20/23.625 at every level, cd 1.9 -> 2.5)
- Flèche Magique (Cra) and its fusion Flèche Punitive (its arrows are Flèches Magiques): no push back (push 0: a projectile
  without `push` knocks back by default, game.js)
- Attaque Mortelle (Sram): its reach 360 -> 270 (a strike's `range`, spells.js; strikes used 360)
- damage -25 % at every level: Frappe du Craqueleur (Osamodas), Fiole Corrosive (Otomaï: its blow and its puddle's poison),
  Dagues Boomerang (Roublard), Lancer de Pièces (Enutrof), Marteau de Moon, Toile d'Arakne
- Épée du Jugement (Iop): damage -35 %
- Intelligence (characteristic): its total at 5/5 in the shop and 4/4 in a run 50 % -> 42.5 % area (-15 % relative): perShop
  [8.3375 %, 10.63 %] a level (util.js passivePer); with no shop level it is unchanged
- Manuel du Tailleur: every boss may drop it, by its place in the progression (zone tier + its minute / 8 in the zone):
  Bouftou Royal 1 % (and the bosses before it), Goultard 5 %, a straight line between (C.manuel.boss, game.js bossDeath)
part HIGH:
- Invisibilité: new description (the monsters' areas on the ground still hit him: game.js damagePlayer's `area`)
- Piège Sournois / Piège Empoisonné: radius x0.5, damage x1.5, cooldown x2, one trap a cast (count 1); one Piège Sournois
  on the ground (max 1), several Piège Empoisonné (its max 14); the Piège Empoisonné goes off on its cone only (trig 8.5),
  its blow no longer poisons (rPoison removed): a 1 s gas cloud does, once a monster, for a level-4 Piège Sournois's
  damage over 4 s (gas / gasDur / gasPoison, game.js poisonCloud)
- Bénédiction Animale: no area on every blow (aoe removed); each Boufcoul bursts once, dead or gone: boom 5 blows,
  boomR 3 x its melee reach (16); hitJit 0.25 = its blows' rhythm drawn once at x0.75-1.25 (game.js updateSummons)
- Rempart élémentaire: damage x3, radius 125 -> 93.75, cooldown x2
- Explobombe: cooldown x1.15 (2.823 -> 3.246), fuse x0.75 (1.0 -> 0.75, 0.85 -> 0.6375 at level 3)
after HIGH: Attaque Mortelle single (one blow, one monster: the strongest within 125), bossK 2; Piège Mortel the same
within 250, its web under the monster hit (rWeb)
part ULTRA (and, after the first 0.98 build: cooldowns x1.15, the Cra x1.2 but Flèche Enflammée; Hard hp x1.1; an
elite's relic 15 %; Dofus Ocre -5 % cooldown, Cawotte +15 % xp, Pourpre +15 % damage; the Arakne majeure's text):
- the poisons of single hits through little zones (code only: game.js poisonPuff)
- every boss's hp x0.85 (not the Maître Corbac de l'Apocalypse's own: it copies the strongest boss)
- the level damage bonus at its top (9.9 %) at level 50: lvDmg 0.099 / 49, lvDmgMax 0.099
- xpEarly x0.8 on levels 1-5, the xp saved given back on the level-ups 20-50 (run.xpBack, game.js addXP)
- run.cdLate: cooldowns +20 % (1 s) to +10 % (10 s) at level 50 (spells.js cdLateK)
usage: python tools/make_content.py   (runs the newest patch; this one imports patch_097 and writes game/data/content.json)"""
import sys as _sys, os as _os, json
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
import _root
import patch_097 as P

C, G, T, put_ui = P.C, P.G, P.T, P.put_ui
S = C['spells']


def scale(sid, keys, k, nd=3):
    """Multiplies keys of a spell at its base and every level (the levels' steps keep their ratios)."""
    for lv in [S[sid]['base']] + S[sid].get('lv', []):
        for key in keys:
            if key in lv: lv[key] = round(lv[key] * k, nd)


# ---------------------------------------------------------------- Invisibilité: 25 s / 1.5 s at its first level, 5/5 bought
IV = S['invisibilite']['base']; assert IV['cd'] == 19.0 and IV['duration'] == 1.5
scale('invisibilite', ['cd'], 25 / (19.0 / 1.25)); scale('invisibilite', ['duration'], 1.5 / (1.5 * 1.5))

# ---------------------------------------------------------------- Flèche Explosive: 20 damage / 2 s at 5/5
cra = next(c for c in C['classes'] if c['id'] == 'cra')
FE = S['fleche_explosive']['base']; assert FE['dmg'] == 30 and FE['cd'] == 1.9
shown = FE['dmg'] * (cra['base']['might'] + (cra.get('passiveStats') or {}).get('might', 0)) * C['run']['spellDmgMul'] * (1 + 5 * C['spellPer'])
scale('fleche_explosive', ['dmg'], 20 / shown, 2); FE['cd'] = 2.5

# ---------------------------------------------------------------- Flèche Magique: no push back (and its fusion's arrows)
for sid in ('fleche_magique', 'fu_cra_arc'):
    assert S[sid]['base'].get('push') == 97.5, sid
    S[sid]['base']['push'] = 0
    for lv in S[sid].get('lv', []): lv.pop('push', None)

# ---------------------------------------------------------------- Attaque Mortelle: a quarter less reach
S['attaque_mortelle']['base']['range'] = 270

# ---------------------------------------------------------------- damage cuts (every level: the same ratio)
for sid in ('fu_osa_marteau', 'dagues_boomerang', 'lancer_pieces', 'marteau_moon', 'toile_arakne'):
    scale(sid, ['dmg'], 0.75, 2)
scale('oto_fiole', ['dmg', 'puddlePoison'], 0.75, 2)
scale('fu_iop_jugement', ['dmg'], 0.65, 2)

# ---------------------------------------------------------------- Intelligence: -15 % of its total at 5/5
INT = next(p for p in C['passives'] if p['id'] == 'intelligence'); assert INT['per'] == 0.083375 and INT['max'] == 4
INT['perShop'] = [INT['per'], round(INT['per'] * (1 + 5 * C['spellPer']) * 0.85, 6)]

# ---------------------------------------------------------------- Manuel du Tailleur: a boss's chance by its place in the game
# place = its zone's tier + the minute it comes / 8 (3, 5.5, 8: the final one is +1); Bouftou Royal (Astrub's final, 1)
# 1 %, Goultard (the last zone's final, 15) 5 %, a straight line between; the bosses before the Bouftou Royal 1 %
place = {}
for m in C['maps']:
    for t, bid in m['bosses']: place[bid] = max(place.get(bid, 0), m['tier'] + t / 8)
lo, hi = place['bouftou_royal'], place['goultard']
assert hi == max(place.values())
C['manuel']['boss'] = {bid: round(0.01 + 0.04 * min(1, max(0, (v - lo) / (hi - lo))), 5) for bid, v in sorted(place.items())}

# ================================================================ part HIGH
# ---------------------------------------------------------------- Invisibilité: the monsters' areas still hit him (game.js damagePlayer)
S['invisibilite']['desc'] = {
    'fr': "Vous devenez invisible : les monstres perdent votre trace, ni leurs coups ni leurs projectiles ne vous touchent, mais leurs zones au sol, si.",
    'en': "You turn invisible: monsters lose track of you and neither their blows nor their projectiles reach you, but their areas on the ground still do.",
    'de': "Du wirst unsichtbar: Monster verlieren deine Spur, weder ihre Schläge noch ihre Geschosse treffen dich, ihre Bodenzonen aber schon.",
    'es': "Te vuelves invisible: los monstruos te pierden la pista y ni sus golpes ni sus proyectiles te alcanzan, pero sus zonas en el suelo sí.",
    'it': "Diventi invisibile: i mostri perdono le tue tracce e né i loro colpi né i loro proiettili ti colpiscono, ma le loro zone a terra sì.",
    'nl': "Je wordt onzichtbaar: monsters raken je kwijt en hun slagen en projectielen raken je niet, hun zones op de grond wel.",
    'pt': "Ficas invisível: os monstros perdem-te o rasto e nem os golpes nem os projéteis deles te atingem, mas as zonas no chão sim."}

# ---------------------------------------------------------------- the Sram's traps: half as wide, one on the ground at a time,
# cooldown x2, damage x1.5; the Piège Empoisonné leaves a 0.5 s gas cloud that poisons each monster once for what a Piège
# Sournois of the same level hits (its level 4, a fusion's level), over 4 s (spells.js trap, game.js poisonCloud)
for sid in ('piege_sournois', 'fu_sram_piege'):
    B = S[sid]['base']; assert B['cd'] == 2.199, sid
    scale(sid, ['radius'], 0.5); scale(sid, ['dmg'], 1.5, 3); B['cd'] = round(B['cd'] * 2, 3)
    B['count'] = 1
    for lv in S[sid].get('lv', []): lv.pop('count', None)
S['piege_sournois']['base']['max'] = 1
for lv in S['piege_sournois']['lv']: lv.pop('max', None)   # (one Piège Sournois on the ground; the Piège Empoisonné keeps its 14, one a cast)
FU = S['fu_sram_piege']['base']; FU.pop('rPoison')   # (its explosion no longer poisons: the gas does, once)
lv4 = dict(S['piege_sournois']['base'])
for lv in S['piege_sournois']['lv']: lv4.update(lv)
FU['gas'] = lv4['dmg']; FU['gasDur'] = 1.0; FU['gasPoison'] = 4   # (its cloud 1 s: twice the first 0.5 s)
FU['trig'] = 8.5   # (it goes off when a monster steps on its cone: drawTrapCone's base radius, + half the monster's size)
S['piege_sournois']['desc'] = {
    'fr': "Pose un piège qui explose quand un ennemi marche dessus. Un seul piège à la fois : le nouveau remplace l'ancien.",
    'en': "Lays a trap that explodes when an enemy steps on it. One trap at a time: the new one replaces the old one.",
    'de': "Legt eine Falle, die explodiert, wenn ein Gegner darauf tritt. Nur eine Falle zugleich: die neue ersetzt die alte.",
    'es': "Coloca una trampa que explota cuando un enemigo la pisa. Una sola trampa a la vez: la nueva sustituye a la anterior.",
    'it': "Piazza una trappola che esplode quando un nemico la calpesta. Una trappola alla volta: la nuova sostituisce la vecchia.",
    'nl': "Legt een val die ontploft als een vijand erop stapt. Eén val tegelijk: de nieuwe vervangt de oude.",
    'pt': "Coloca uma armadilha que explode quando um inimigo a pisa. Uma armadilha de cada vez: a nova substitui a antiga."}
S['fu_sram_piege']['desc'] = {
    'fr': "Un piège plus fort qui, en explosant, laisse un bref nuage de gaz : chaque monstre qui le traverse est empoisonné. Le Sram ne fait jamais les choses à moitié.",
    'en': "A stronger trap that leaves a brief gas cloud when it explodes: every monster passing through is poisoned. A Sram never does things by halves.",
    'de': "Eine stärkere Falle, die beim Explodieren eine kurze Gaswolke hinterlässt: Jedes Monster darin wird vergiftet. Ein Sram macht keine halben Sachen.",
    'es': "Una trampa más fuerte que, al explotar, deja una breve nube de gas: cada monstruo que la cruza queda envenenado. Un Sram nunca hace las cosas a medias.",
    'it': "Una trappola più forte che, esplodendo, lascia una breve nube di gas: ogni mostro che la attraversa viene avvelenato. Uno Sram non fa mai le cose a metà.",
    'nl': "Een sterkere val die bij het ontploffen een korte gaswolk achterlaat: elk monster erin wordt vergiftigd. Een Sram doet niets half.",
    'pt': "Uma armadilha mais forte que, ao explodir, deixa uma breve nuvem de gás: cada monstro que a atravessa fica envenenado. Um Sram nunca faz as coisas pela metade."}

# ---------------------------------------------------------------- Bénédiction Animale: no area on every blow; each Boufcoul
# bursts once, dead or gone (5 of its blows, 3 x its melee reach), its blows' rhythm drawn once x0.75-1.25 (game.js)
BA = S['fu_osa_bouftou']['base']; assert BA.pop('aoe') == 45
BA['boom'] = 5; BA['boomR'] = 3; BA['hitJit'] = 0.25
S['fu_osa_bouftou']['desc'] = {
    'fr': "Vos Bouftous deviennent des Boufcouls : plus nombreux, plus solides, et chacun explose en partant, cognant tous les monstres autour. Bêêê… BAM.",
    'en': "Your Gobballs become Gobkools: more of them, sturdier, and each one bursts as it goes, bashing every monster around. Baaa… BAM.",
    'de': "Deine Fresssäcke werden Fresscools: mehr, zäher, und jeder explodiert beim Verschwinden und trifft alle Monster ringsum. Määäh… BAM.",
    'es': "Tus Jalatos se vuelven Jalatrankis: más numerosos, más fuertes, y cada uno explota al irse, golpeando a todos los monstruos alrededor. Beee… ¡BAM!",
    'it': "I tuoi Mangiabù diventano Pappacool: più numerosi, più robusti, e ognuno esplode andandosene, colpendo tutti i mostri intorno. Beee… BAM.",
    'nl': "Je Schapen worden Gobkools: meer, steviger, en elk ontploft bij het verdwijnen en raakt alle monsters rondom. Bèèè… BAM.",
    'pt': "Seus Papatudos viram Gobkools: mais numerosos, mais fortes, e cada um explode ao partir, acertando todos os monstros ao redor. Bééé… BAM."}

# ---------------------------------------------------------------- Rempart élémentaire: damage x3, area -25 %, cooldown x2
RE = S['fu_feca_glyphe']['base']; assert RE['radius'] == 125 and RE['cd'] == 5.524
RE['dmg'] = round(RE['dmg'] * 3, 3); RE['radius'] = round(RE['radius'] * 0.75, 3); RE['cd'] = round(RE['cd'] * 2, 3)

# ---------------------------------------------------------------- Explobombe: cooldown +15 %, fuse -25 % (1.0, 0.85 at level 3)
EB = S['explobombe']; assert EB['base']['cd'] == 2.823 and EB['base']['fuse'] == 1.0
EB['base']['cd'] = round(EB['base']['cd'] * 1.15, 3); scale('explobombe', ['fuse'], 0.75, 4)

# ================================================================ part ULTRA
# ---------------------------------------------------------------- the poisons of single hits become little zones: code only
# (game.js poisonPuff: 38 x area, 0.25 s; C.run.poisonPuff may override)

# ---------------------------------------------------------------- the bosses' HP -15 %, once (the Maître Corbac de l'Apocalypse
# copies the strongest boss's hp at its spawn: it follows by itself, its own hp is not used)
for bid, b in C['bosses'].items():
    if b.get('doom'): continue
    b['hp'] = round(b['hp'] * 0.85, 2)

# ---------------------------------------------------------------- the damage bonus per level reaches its top at level 50:
# 9.9 % (its value at level 100 before: 0.001 x 99)
R = C['run']; assert R['lvDmg'] == 0.001 and R['lvDmgMax'] == 0.1
R['lvDmg'] = 0.099 / 49; R['lvDmgMax'] = 0.099

# ---------------------------------------------------------------- experience: -20 % on levels 1 to 5 (the xp each one needs),
# the xp saved given back exactly, growing, on the level-ups from 20 to 50 (game.js addXP: + xpBack.add[level - 20])
def need(xe, lv):   # game.js addXP (Math.round: JS rounds .5 up)
    import math
    base = 5 + (lv - 1) * 10 if lv < 20 else 195 + (lv - 20) * 22 if lv < 40 else 640 + (lv - 40) * 40
    return math.floor(base * (xe[lv - 1] if lv - 1 < len(xe) else 1) + 0.5)
XE0 = list(R['xpEarly']); assert XE0 == [2.8, 2.8, 2.4, 1.9, 1.5, 1.25, 1.1]
R['xpEarly'] = [round(x * 0.8, 4) for x in XE0[:5]] + XE0[5:]
saved = sum(need(XE0, l) for l in range(1, 6)) - sum(need(R['xpEarly'], l) for l in range(1, 6))
w = list(range(1, 31)); share = [saved * x / sum(w) for x in w]; add = [int(s) for s in share]   # the level-ups 20 -> 21 ... 49 -> 50
for i in sorted(range(30), key=lambda i: share[i] - add[i], reverse=True)[:saved - sum(add)]: add[i] += 1   # (largest remainders: the sum is exact)
assert sum(add) == saved and add == sorted(add)
R['xpBack'] = {'from': 20, 'add': add}

# ---------------------------------------------------------------- cooldowns +20 % (1 s or less) to +10 % (10 s and more) at level
# 50, from 0 at level 1 (spells.js cdLateK, once, in SpellInst.cooldown and ui.js menuSpellParams)
R['cdLate'] = {'lv': 50, 'fast': [1, 0.2], 'slow': [10, 0.1]}

# ================================================================ after ULTRA: Attaque Mortelle and Piège Mortel
# one blow on one monster (single: no area, no extra copy), the strongest one within 125 (about 2 m: the character is
# ~105 high), x2 on a boss (bossK); its fusion with Toile d'Arakne the same with twice the reach, its web under the
# monster hit (rWeb, sfusions.js); count 1 at every level
for sid, rng in (('attaque_mortelle', 125), ('fu_sram_toile', 250)):
    B = S[sid]['base']; B['single'] = 1; B['bossK'] = 2; B['range'] = rng; B['count'] = 1; B['target'] = 'strongest'
    for lv in S[sid].get('lv', []): lv.pop('count', None)
S['attaque_mortelle']['desc'] = {
    'fr': "Un pilier d'ombre frappe l'ennemi le plus résistant tout proche de vous, lui seul. Double dégâts sur les boss.",
    'en': "A pillar of shadow strikes the toughest enemy right next to you, and only it. Double damage to bosses.",
    'de': "Eine Schattensäule trifft den zähesten Gegner direkt neben dir, nur ihn. Doppelter Schaden an Bossen.",
    'es': "Un pilar de sombra golpea al enemigo más resistente justo a tu lado, solo a él. Daño doble a los jefes.",
    'it': "Un pilastro d'ombra colpisce il nemico più resistente proprio accanto a te, solo lui. Danni doppi ai boss.",
    'nl': "Een schaduwzuil treft de taaiste vijand vlak naast je, alleen hem. Dubbele schade aan bazen.",
    'pt': "Um pilar de sombra atinge o inimigo mais resistente mesmo ao teu lado, só ele. Dano a dobrar nos chefes."}
S['fu_sram_toile']['desc'] = {
    'fr': "Une Attaque Mortelle qui porte deux fois plus loin et laisse une toile d'Arakne sous le monstre touché. Double dégâts sur les boss.",
    'en': "A Lethal Attack that reaches twice as far and leaves an Arachnee web under the monster hit. Double damage to bosses.",
    'de': "Ein Tödlicher Angriff mit doppelter Reichweite, der ein Arakne-Netz unter dem getroffenen Monster hinterlässt. Doppelter Schaden an Bossen.",
    'es': "Un Ataque Mortal que llega el doble de lejos y deja una telaraña de Arakne bajo el monstruo golpeado. Daño doble a los jefes.",
    'it': "Un Attacco Mortale che arriva due volte più lontano e lascia una ragnatela di Arakne sotto il mostro colpito. Danni doppi ai boss.",
    'nl': "Een Dodelijke Aanval die twee keer zo ver reikt en een Arakne-web onder het geraakte monster achterlaat. Dubbele schade aan bazen.",
    'pt': "Um Ataque Mortal que chega duas vezes mais longe e deixa uma teia de Arakne debaixo do monstro atingido. Dano a dobrar nos chefes."}

# ================================================================ after the first 0.98 build (the owner's list)
# cooldowns: every class spell, every global spell and every spell fusion x1.15 — the Cra's spells and the Cra's fusions
# x1.2, Flèche Enflammée x1.15 (it has no fusion); at their source (base, level steps, cdShop), each spell once; weapons
# untouched. The shop's levels, characteristics, relics, Dofus and cdLate still work on top (SpellInst.cooldown)
CRA = next(c for c in C['classes'] if c['id'] == 'cra')['spells']
cdK = {}
for c in C['classes']:
    for sid in c['spells']: cdK[sid] = 1.15
for g in C['globalSpells']: cdK[g['id']] = 1.15
for f in C['spellFusions']: cdK[f['id']] = 1.15
for sid in CRA: cdK[sid] = 1.2
for f in C['spellFusions']:
    if f.get('cls') == 'cra': cdK[f['id']] = 1.2
cdK['fleche_enflammee'] = 1.15
assert not any('fleche_enflammee' in f['src'] for f in C['spellFusions'])
for sid, k in sorted(cdK.items()):
    sp = S[sid]
    for lv in [sp['base']] + sp.get('lv', []):
        for key in ('cd', 'cdShop'):
            if key in lv and 0 < lv[key] < 900: lv[key] = round(lv[key] * k, 3)
CD_DONE = {k: v for k, v in cdK.items()}

# Hard mode: every monster's and boss's hp x1.1 on top of its Hard bonus (hardHp = 1 + hpMin..hpMax: 1.25 -> 1.375;
# bossHp 1.25 -> 1.375, the elites' cap and the Maître Corbac follow it)
H = C['hard']; assert H['hpMin'] == H['hpMax'] == 0.25 and H['bossHp'] == 1.25
H['hpMin'] = H['hpMax'] = round((1 + H['hpMin']) * 1.1 - 1, 4); H['bossHp'] = round(H['bossHp'] * 1.1, 4)

# an elite's relic 25 % -> 15 % (extras.js maybeEliteRelic: x the luck, as before); bosses, mini-bosses, the merchant unchanged
assert C['relicElite'] == 0.25; C['relicElite'] = 0.15

# the Dofus: Ocre -10 % -> -5 % cooldown, Cawotte +25 % -> +15 % xp, Pourpre +25 % -> +15 % damage (their texts too)
DF = {d['id']: d for d in C['dofus']}
assert DF['ocre']['bonus']['cooldown'] == -0.1 and DF['cawotte']['bonus']['growth'] == 0.25 and DF['pourpre']['bonus']['might'] == 0.25
DF['ocre']['bonus']['cooldown'] = -0.05; DF['cawotte']['bonus']['growth'] = 0.15; DF['pourpre']['bonus']['might'] = 0.15
for did, old, new in (('ocre', '-10', '-5'), ('cawotte', '+25', '+15'), ('pourpre', '+25', '+15')):
    for lg, v in DF[did]['desc'].items(): assert v.count(old) == 1, (did, lg); DF[did]['desc'][lg] = v.replace(old, new)

# the Arakne majeure (an Arakne's critical summon) doubles the character's damage while it is there (game.js dmgMul)
T_MAJ = {'fr': "Coup critique ! Arakne Majeure se joint à vous : vos dégâts ×2 tant qu'elle est là !",
         'en': "Critical hit! Major Arachnee joins you: your damage ×2 while it stays!",
         'de': "Kritischer Treffer! Große Arakne schließt sich dir an: dein Schaden ×2, solange sie bleibt!",
         'es': "¡Golpe crítico! Arakna Mayor se une a ti: ¡tu daño ×2 mientras esté!",
         'it': "Colpo critico! Arakne Maggiore si unisce a te: i tuoi danni ×2 finché resta!",
         'nl': "Kritieke treffer! Grote Arachnee sluit zich bij je aan: je schade ×2 zolang ze blijft!",
         'pt': "Golpe crítico! Aracne Adulta junta-se a ti: o teu dano ×2 enquanto estiver!"}
for lg, v in T_MAJ.items(): C['ui'][lg]['pw_majeure'] = v
# the Hard mode's texts: monsters' and bosses' life +25 % -> +37.5 % (both, every language)
for lg in C['ui']:
    for key in ('mode_hint', 'hard_info'):
        v = C['ui'][lg][key]; n = v.count('+25'); assert n == 2, (lg, key, n); C['ui'][lg][key] = v.replace('+25', '+37,5' if lg in ('fr', 'de', 'es', 'it', 'nl', 'pt') else '+37.5')

# the summons drawn from sheets rendered at their size on screen (tools/assets/build_mobs20.py, from the client's vector
# sprites; they were blown up): Arakne Agressive 4.0 -> 6.6 (with its attack), Arakne majeure 4.0 -> 10.4, Chaferfu
# Lancier 3.0 -> 3.3 (the Chaferfu's 3.0 is already its size)
for kind, old_k, new_k in (('arakne', '1564_z60', '1564_z66'), ('majeure', '1161_z60', '1161_z104'), ('lancier', '1189_z32', '1189_z33')):
    assert C['allies'][kind]['sprite'] == old_k, kind; C['allies'][kind]['sprite'] = new_k

# ================================================================ 0.98.1: the announcements are names
# the middle of the screen shows a name (Run.announce, game.js), what it does stays in the chat (twice as long); the names
# that are not already in the data (monsters, bosses, items, drops, allies) — the critical summons' red word before theirs
LANGS7 = ('fr', 'en', 'de', 'es', 'it', 'nl', 'pt')
TITLES = {
    'crowd_grows_t': ('Renforts', 'Reinforcements', 'Verstärkung', 'Refuerzos', 'Rinforzi', 'Versterking', 'Reforços'),
    'door_appears_t': ('Porte mystérieuse', 'Mysterious door', 'Geheimnisvolle Tür', 'Puerta misteriosa', 'Porta misteriosa', 'Mysterieuze deur', 'Porta misteriosa'),
    'doom_t': ('Maîtres Corbacs', 'Lord Crows', 'Meister Raben', 'Maestros Cuerbok', 'Messer Cuervoc', 'Heren Kraai', 'Lordes Corvos'),
    'jackpot_t': ('Jackpot', 'Jackpot', 'Jackpot', 'Premio gordo', 'Jackpot', 'Jackpot', 'Jackpot'),
    'revived_t': ('Phénix', 'Phoenix', 'Phönix', 'Fénix', 'Fenice', 'Feniks', 'Fênix'),
    'kamaboost_t': ('Bourse magique', 'Magic purse', 'Magischer Beutel', 'Bolsa mágica', 'Borsa magica', 'Magische buidel', 'Bolsa mágica'),
    'batofu_t': ('Plume du Batofu', 'Batofu Feather', 'Batofu-Feder', 'Pluma del Batofu', 'Piuma del Batofu', 'Batofuveer', 'Pena do Batofu'),
    'sandglass_t': ('Sablier de Xélor', "Xelor's Sandglass", 'Xelors Sanduhr', 'Reloj de arena de Xelor', 'Clessidra di Xelor', 'Zandloper van Xelor', 'Ampulheta de Xelor'),
    'crit_t': ('Coup critique !', 'Critical hit!', 'Kritischer Treffer!', '¡Golpe crítico!', 'Colpo critico!', 'Kritieke treffer!', 'Golpe crítico!'),
    'exploit_t': ('Exploit', 'Feat', 'Heldentat', 'Hazaña', 'Impresa', 'Heldendaad', 'Façanha'),
    'fireworks_t': ("Fée d'Artifice", 'Firework Fairy', 'Feuerwerksfee', 'Hada de Artificio', 'Fata d’Artificio', 'Vuurwerkfee', 'Fada de Artifício'),
    'booster_here_t': ('Booster TTG', 'TTG booster', 'TTG-Booster', 'Sobre TTG', 'Bustina TTG', 'TTG-booster', 'Booster TTG'),
    'down_t': ('{n} vaincu', '{n} defeated', '{n} besiegt', '{n} vencido', '{n} sconfitto', '{n} verslagen', '{n} derrotado'),
    'trap_found_t': ('Une trappe', 'A trapdoor', 'Eine Falltür', 'Una trampilla', 'Una botola', 'Een valluik', 'Um alçapão'),
    'tmap_found_t': ('Trésor déterré', 'Treasure dug up', 'Schatz ausgegraben', 'Tesoro desenterrado', 'Tesoro dissotterrato', 'Schat opgegraven', 'Tesouro desenterrado'),
    'lb_cycle_t': ('Cycle {n}', 'Cycle {n}', 'Zyklus {n}', 'Ciclo {n}', 'Ciclo {n}', 'Cyclus {n}', 'Ciclo {n}'),
    'ev_bworks_t': ('Invasion de Bworks', 'Bwork invasion', 'Bwork-Invasion', 'Invasión de Bworks', 'Invasione di Bwork', 'Bwork-invasie', 'Invasão de Bworks'),
    'ev_tofus_t': ('Pluie de Tofus', 'Tofu rain', 'Tofu-Regen', 'Lluvia de Tofus', 'Pioggia di Tofu', 'Tofuregen', 'Chuva de Tofus'),
    'ev_kamarain_t': ('Pluie de kamas', 'Kama rain', 'Kama-Regen', 'Lluvia de kamas', 'Pioggia di kama', 'Kama-regen', 'Chuva de kamas'),
    'ev_eclipse_t': ('Éclipse', 'Eclipse', 'Finsternis', 'Eclipse', 'Eclissi', 'Eclips', 'Eclipse'),
    'ev_merchant_t': ('Marchand ambulant', 'Travelling merchant', 'Fahrender Händler', 'Mercader ambulante', 'Mercante ambulante', 'Rondreizende handelaar', 'Mercador ambulante'),
    'pioche_jackpot_t': ('Filon', 'Motherlode', 'Goldader', 'Filón', 'Filone', 'Goudader', 'Filão'),
    'tot_slap_t': ('La claque de ToT', "ToT's slap", 'ToTs Ohrfeige', 'La colleja de ToT', 'Lo schiaffo di ToT', 'De mep van ToT', 'A chapada do ToT'),
    'nowel_gift_here_t': ('Cadeau de Nowel', 'Kwismas Present', 'Nowel-Geschenk', 'Regalo de Nowel', 'Regalo di Nowel', 'Nowelcadeau', 'Presente de Nowel'),
    'aura_secret_t': ('Secret débloqué', 'Secret unlocked', 'Geheimnis freigeschaltet', 'Secreto desbloqueado', 'Segreto sbloccato', 'Geheim ontgrendeld', 'Segredo desbloqueado'),
}
for key, vals in TITLES.items():
    for lg, v in zip(LANGS7, vals): assert key not in C['ui'][lg], (lg, key); C['ui'][lg][key] = v
assert C['ui']['fr']['doom'] == 'Les Maîtres Corbac arrivent !'; C['ui']['fr']['doom'] = 'Les Maîtres Corbacs arrivent !'   # (the plural, as in doom_rw_*)

# ================================================================ 0.98.2
# every spell, global spell and spell fusion +10 %: in the data, each damage number of each spell once (a fusion is a spell of
# its own, its riders are shares of its damage), so the menus and the blows read the same value; weapons, allies, drops apart
for sid in S: scale(sid, ['dmg', 'poison', 'puddlePoison', 'burn', 'gas', 'wallDmg'], 1.1)
# the first four thresholds (levels 2 to 5) -10 %; from level 5 on the same experience (xpBack untouched)
XE = C['run']['xpEarly']; assert XE[:4] == [2.24, 2.24, 1.92, 1.52]; XE[:4] = [round(x * 0.9, 3) for x in XE[:4]]
assert C['banishes'] == 1; C['banishes'] = 2
# the ground drop's Araknes: no more push, a slow on what they hit (renewed, never added up: Run.updateAllies)
for A in (C['drops']['arakne'], C['drops']['arakne']['majeure']):
    del A['knock']; A['slow'] = 0.9; A['slowDur'] = 2
del C['drops']['arakne']['majeure']['pushOnce']
# Ganymède's blessing: zone cards 1 to 10 in Normal, on top of the first three zones' help (beginnerAid); Dark Vlad takes it
# away on card 11 (Run.bless, Game.startRun, UI.ganyScene key 'taunt')
GY = C['gany']; GY['bless'] = {'maps': 10, 'dmg': 0.05, 'bread': 3}
assert C['maps'][10]['id'] == 'pandala'
def line7(*v): return dict(zip(LANGS7, v))
GY['scenes']['astrub'] += [
    line7("Et ce n'est pas tout ! Ce coup de pouce, tu le gardes, et j'y ajoute ma bénédiction : +{bd} % de dégâts sur tes {bn} premières cartes. Ne me remercie pas, frappe !",
          "And that's not all! You keep that helping hand, and I'm adding my blessing: +{bd}% damage on your first {bn} maps. Don't thank me, hit something!",
          "Und das ist noch nicht alles! Diese Hilfe behältst du, und dazu kommt mein Segen: +{bd} % Schaden auf deinen ersten {bn} Karten. Dank mir nicht, schlag lieber zu!",
          "¡Y eso no es todo! Esa ayudita te la quedas, y le sumo mi bendición: +{bd} % de daño en tus {bn} primeros mapas. No me des las gracias, ¡pega!",
          "E non è tutto! Quell'aiuto te lo tieni, e ci aggiungo la mia benedizione: +{bd}% di danni sulle tue prime {bn} mappe. Non ringraziarmi, picchia!",
          "En dat is nog niet alles! Dat steuntje houd je, en ik voeg er mijn zegen aan toe: +{bd}% schade op je eerste {bn} kaarten. Niet bedanken, gewoon meppen!",
          "E não é tudo! Essa ajudinha fica contigo, e junto-lhe a minha bênção: +{bd}% de dano nos teus {bn} primeiros mapas. Não me agradeças, bate!"),
    line7("Quant au boulanger d'Incarnam, il t'a à la bonne : {bp} fois plus de pain par terre pendant tes premières aventures. Il paraît que tu as une mine de Tofu mal nourri.",
          "As for the Incarnam baker, he's taken a liking to you: {bp} times more bread on the ground during your first adventures. He says you look like an underfed Tofu.",
          "Und der Bäcker von Incarnam mag dich: {bp}-mal mehr Brot auf dem Boden während deiner ersten Abenteuer. Er meint, du siehst aus wie ein unterernährtes Tofu.",
          "En cuanto al panadero de Incarnam, le has caído bien: {bp} veces más pan por el suelo durante tus primeras aventuras. Dice que tienes cara de Tofu mal alimentado.",
          "Quanto al fornaio di Incarnam, gli stai simpatico: {bp} volte più pane per terra durante le tue prime avventure. Dice che hai la faccia di un Tofu denutrito.",
          "En de bakker van Incarnam mag je wel: {bp} keer meer brood op de grond tijdens je eerste avonturen. Hij zegt dat je eruitziet als een ondervoede Tofu.",
          "Quanto ao padeiro de Incarnam, foi com a tua cara: {bp} vezes mais pão no chão durante as tuas primeiras aventuras. Diz que tens ar de Tofu mal alimentado."),
]
GY['scenes']['bonta'].append(
    line7("Et bien sûr, ma bénédiction et le pain du boulanger d'Incarnam te suivent toujours. Je ne suis pas un monstre… enfin, pas comme ceux d'ici.",
          "And of course, my blessing and the Incarnam baker's bread are still with you. I'm no monster… well, not like the ones around here.",
          "Und natürlich begleiten dich mein Segen und das Brot des Bäckers von Incarnam weiterhin. Ich bin ja kein Monster … jedenfalls nicht wie die hier.",
          "Y, por supuesto, mi bendición y el pan del panadero de Incarnam te siguen acompañando. No soy un monstruo… bueno, no como los de aquí.",
          "E naturalmente la mia benedizione e il pane del fornaio di Incarnam ti seguono ancora. Non sono un mostro… be', non come quelli di qui.",
          "En natuurlijk blijven mijn zegen en het brood van de bakker van Incarnam je volgen. Ik ben geen monster… nou ja, niet zoals die hier.",
          "E claro, a minha bênção e o pão do padeiro de Incarnam continuam contigo. Não sou nenhum monstro… bem, não como os daqui."))
GY['scenes']['chafer'][1] = line7(
    "Mais c'est ma dernière visite. Après, il faudra avancer sans moi, comme une grande âme.",
    "But this is my last visit. After that, you'll have to carry on without me, like a big soul.",
    "Aber das ist mein letzter Besuch. Danach musst du ohne mich weiterziehen, wie eine große Seele.",
    "Pero es mi última visita. Después tendrás que seguir sin mí, como un alma mayor.",
    "Ma è la mia ultima visita. Dopo dovrai andare avanti senza di me, come un'anima grande.",
    "Maar dit is mijn laatste bezoek. Daarna moet je zonder mij verder, als een grote ziel.",
    "Mas é a minha última visita. Depois vais ter de continuar sem mim, como uma alma crescida.")
GY['scenes']['chafer'][3] = line7(
    "Allez, pour la route : sur cette carte, les monstres ont {h} % de points de vie en moins et infligent {d} % de dégâts en moins. Ce coup de pouce-là s'arrête ici.",
    "One for the road: on this map, monsters have {h}% less HP and deal {d}% less damage. That particular helping hand stops here.",
    "Und eins für unterwegs: Auf dieser Karte haben die Monster {h} % weniger LP und verursachen {d} % weniger Schaden. Diese Hilfe endet hier.",
    "Y una para el camino: en este mapa, los monstruos tienen un {h} % menos de PV e infligen un {d} % menos de daño. Esa ayudita se acaba aquí.",
    "E una per la strada: su questa mappa i mostri hanno il {h}% di PV in meno e infliggono il {d}% di danni in meno. Quest'aiuto finisce qui.",
    "Nog eentje voor onderweg: op deze kaart hebben de monsters {h}% minder LP en doen ze {d}% minder schade. Dat steuntje stopt hier.",
    "Mais uma para o caminho: neste mapa, os monstros têm menos {h}% de PV e causam menos {d}% de dano. Essa ajudinha acaba aqui.")
GY['scenes']['chafer'].append(line7(
    "Mais le boulanger d'Incarnam t'aime bien : il continue de te gâter, {bp} fois plus de pain jusqu'à la fin de la carte {bn}. Et je te laisse ma bénédiction : +{bd} % de dégâts jusque-là. Ne gâche pas tout !",
    "But the Incarnam baker likes you: he'll keep spoiling you, {bp} times more bread until the end of map {bn}. And I'm leaving you my blessing: +{bd}% damage until then. Don't waste it!",
    "Aber der Bäcker von Incarnam mag dich: Er verwöhnt dich weiter, {bp}-mal mehr Brot bis zum Ende von Karte {bn}. Und mein Segen bleibt dir: +{bd} % Schaden bis dahin. Vermassel es nicht!",
    "Pero el panadero de Incarnam te aprecia: seguirá mimándote, {bp} veces más pan hasta el final del mapa {bn}. Y te dejo mi bendición: +{bd} % de daño hasta entonces. ¡No lo eches a perder!",
    "Ma il fornaio di Incarnam ti vuole bene: continuerà a viziarti, {bp} volte più pane fino alla fine della mappa {bn}. E ti lascio la mia benedizione: +{bd}% di danni fin lì. Non sprecarla!",
    "Maar de bakker van Incarnam mag je: hij blijft je verwennen, {bp} keer meer brood tot het einde van kaart {bn}. En mijn zegen laat ik bij je: +{bd}% schade tot dan. Verpruts het niet!",
    "Mas o padeiro de Incarnam gosta de ti: vai continuar a mimar-te, {bp} vezes mais pão até ao fim do mapa {bn}. E deixo-te a minha bênção: +{bd}% de dano até lá. Não estragues tudo!"))
GY['taunt'] = {'map': 'pandala', 'lines': [
    line7("Tiens… une âme qui se cache derrière les plumes de {g} et les miches d'un boulanger. C'est quoi, ces bénédictions pour faiblards ?",
          "Well now… a soul hiding behind {g}'s feathers and a baker's loaves. What are these blessings for weaklings?",
          "Sieh an … eine Seele, die sich hinter {g}s Federn und den Broten eines Bäckers versteckt. Was sollen diese Segen für Schwächlinge?",
          "Vaya… un alma que se esconde tras las plumas de {g} y las hogazas de un panadero. ¿Qué son estas bendiciones para debiluchos?",
          "Guarda un po'… un'anima che si nasconde dietro le piume di {g} e le pagnotte di un fornaio. Cosa sono queste benedizioni da smidollati?",
          "Kijk eens aan… een ziel die zich verschuilt achter de veren van {g} en de broden van een bakker. Wat moeten die zegens voor slappelingen?",
          "Ora vejam… uma alma escondida atrás das penas de {g} e dos pães de um padeiro. Que bênçãos de fracotes são estas?"),
    line7("Tu crois vraiment pouvoir me vaincre ? Alors tu n'as plus besoin de tout ça, n'est-ce pas ? Montre-moi ce que tu vaux, seul.",
          "You truly think you can defeat me? Then you won't be needing all that, will you? Show me what you're worth, alone.",
          "Glaubst du wirklich, du könntest mich besiegen? Dann brauchst du das alles ja nicht mehr, oder? Zeig mir, was du allein wert bist.",
          "¿De verdad crees que puedes vencerme? Entonces ya no necesitas todo eso, ¿verdad? Muéstrame lo que vales, solo.",
          "Credi davvero di potermi sconfiggere? Allora tutto questo non ti serve più, vero? Mostrami quanto vali, da solo.",
          "Denk je echt dat je mij kunt verslaan? Dan heb je dat allemaal niet meer nodig, toch? Laat maar zien wat je alleen waard bent.",
          "Achas mesmo que me consegues vencer? Então já não precisas de nada disso, pois não? Mostra-me o que vales, sozinho."),
]}
NEW_UI = {
    # the blessing alone (cards 4 to 10, or a beginners' zone already won); with the beginners' help it joins aid_info: one line
    'bless_info': ("✨ Bénédiction de {g} : +{p} % de dégâts, et 🥖 {k} fois plus de pain au sol grâce au boulanger d'Incarnam, sur les {n} premières cartes en Normale.",
                   "✨ {g}'s blessing: +{p}% damage, and 🥖 {k} times more bread on the ground thanks to the Incarnam baker, on the first {n} maps in Normal.",
                   "✨ Segen von {g}: +{p} % Schaden und 🥖 {k}-mal mehr Brot auf dem Boden dank des Bäckers von Incarnam, auf den ersten {n} Karten auf Normal.",
                   "✨ Bendición de {g}: +{p} % de daño y 🥖 {k} veces más pan en el suelo gracias al panadero de Incarnam, en los {n} primeros mapas en Normal.",
                   "✨ Benedizione di {g}: +{p}% di danni e 🥖 {k} volte più pane per terra grazie al fornaio di Incarnam, sulle prime {n} mappe in Normale.",
                   "✨ Zegen van {g}: +{p}% schade en 🥖 {k} keer meer brood op de grond dankzij de bakker van Incarnam, op de eerste {n} kaarten op Normaal.",
                   "✨ Bênção de {g}: +{p}% de dano e 🥖 {k} vezes mais pão no chão graças ao padeiro de Incarnam, nos {n} primeiros mapas no Normal."),
    'bless_end': ("💀 {v} a balayé vos bénédictions : plus d'aide de {g} ni du boulanger d'Incarnam ici.",
                  "💀 {v} swept your blessings away: no more help from {g} or the Incarnam baker here.",
                  "💀 {v} hat deine Segen hinweggefegt: Hier gibt es keine Hilfe mehr von {g} oder dem Bäcker von Incarnam.",
                  "💀 {v} ha barrido tus bendiciones: aquí ya no hay ayuda de {g} ni del panadero de Incarnam.",
                  "💀 {v} ha spazzato via le tue benedizioni: qui niente più aiuto da {g} né dal fornaio di Incarnam.",
                  "💀 {v} heeft je zegens weggevaagd: hier geen hulp meer van {g} of de bakker van Incarnam.",
                  "💀 {v} varreu as tuas bênçãos: aqui já não há ajuda de {g} nem do padeiro de Incarnam."),
}
for key, vals in NEW_UI.items():
    for lg, v in zip(LANGS7, vals): assert key not in C['ui'][lg], (lg, key); C['ui'][lg][key] = v
for lg in LANGS7: C['ui'][lg]['relic_got'] = C['ui'][lg]['relic_got'].strip('¡! \u00a0')   # (a plain word in the relic's frame)
for lg in LANGS7: C['ui'][lg]['bless_all'] = C['ui'][lg]['aid_info'] + ' ' + C['ui'][lg]['bless_info'].replace('{g}', '{g2}')   # (T fills a name once)

# ================================================================ 0.98.3
# Hard: monsters' and bosses' life +37.5 % -> +35 % (hardHp, bossHp: the elites' cap and the Maître Corbac follow it)
assert H['hpMin'] == H['hpMax'] == 0.375 and H['bossHp'] == 1.375
H['hpMin'] = H['hpMax'] = 0.35; H['bossHp'] = 1.35
for lg in C['ui']:
    for key in ('mode_hint', 'hard_info'):
        v = C['ui'][lg][key]; old = '+37,5' if lg in ('fr', 'de', 'es', 'it', 'nl', 'pt') else '+37.5'; assert v.count(old) == 2, (lg, key); C['ui'][lg][key] = v.replace(old, '+35')
# the ground's objects: the rates are the real ones: no more hidden x1.15 on all of them (C.run.itemDropK, 0.60, every mode)
assert C['run'].pop('itemDropK') == 1.15
# the bread: 0.1875 % -> 0.3 % a monster, x Chance (x a blessing, game.js)
assert C['run']['breadRate'] == 0.001875; C['run']['breadRate'] = 0.003
# the Manuel du Tailleur: a real rate on every monster instead of one roll a run: -ln(0.9) / the kills of a whole run, so
# about 10 % of whole runs (280 to 370 kills: mean of the bot's 10-minute runs on 9 zones, no shop / shop 4; 350 taken)
for key in ('chance', 't0', 't1'): C['manuel'].pop(key)
C['manuel']['rate'] = 0.0003
# its rate on a boss: by the boss's real power (life x (1 + damage / 10): hardHp's measure, with its zone's multiplier as spawnBoss
# applies it; the four Kwakeres, one roll, count together): 1 % on the weakest, 5 % on the Goultard, proportional between
_pw = {}
for _m in C['maps']:
    _z = 1 if _m.get('hidden') else 0.8 + 0.025 * min(6, max(0, _m['tier']))
    for _t, _b in _m['bosses']:
        _d = C['bosses'][_b]; _pw[_b] = max(_pw.get(_b, 0), _d['hp'] * _z * (4 if _b.startswith('kwakere') else 1) * (1 + _d['dmg'] * _z / 10))
_lo, _hi = min(_pw.values()), _pw['goultard']; assert _hi == max(_pw.values())
C['manuel']['boss'] = {_b: round(0.01 + 0.04 * (_v - _lo) / (_hi - _lo), 5) for _b, _v in sorted(_pw.items())}
# TTG rarities: drawn first in a pack (among those it holds), then a card of that rarity (events.js openBooster): C.ttg.rw solved so
# that one pack in 48 each gives 55 / 30 / 11.8 / 3.2 % overall (the four rarity packs alone give 2.08 % of each)
_cards = C['ttg']['cards']; _fams = sorted({c['fam'] for c in _cards}); _np = len(_fams) + 4; _T = [0.55, 0.30, 0.118, 0.032]
def _ttg(rw):
    P = [0] * 4
    for f in _fams:
        has = {c['r'] for c in _cards if c['fam'] == f}; s = sum(rw[r] for r in has)
        for r in has: P[r] += rw[r] / s / _np
    return P
_rw = [55.0, 30.0, 12.0, 3.0]
for _ in range(400):
    _p = _ttg(_rw); _rw = [_rw[r] * (_T[r] - 1 / _np) / _p[r] for r in range(4)]
_k = 100 / sum(_rw); C['ttg']['rw'] = [round(x * _k, 3) for x in _rw]
assert all(abs(_ttg(C['ttg']['rw'])[r] + 1 / _np - _T[r]) < 0.0002 for r in range(4))
# the relic tip: at most C.relicDropMax (5) fall in a run (extras.js dropRelic), not C.relicMax (6)
assert C['relicDropMax'] == 5
TIP_R = {'fr': ('six par partie', 'cinq par partie'), 'en': ('six per run', 'five per run'), 'de': ('höchstens sechs', 'höchstens fünf'), 'es': ('seis por partida', 'cinco por partida'),
         'it': ('sei per partita', 'cinque per partita'), 'nl': ('hoogstens zes', 'hoogstens vijf'), 'pt': ('seis por partida', 'cinco por partida')}
_i = next(i for i, x in enumerate(C['tips']['fr']) if x.startswith('Les reliques tombent des boss'))
for lg, (old, new) in TIP_R.items(): assert old in C['tips'][lg][_i], lg; C['tips'][lg][_i] = C['tips'][lg][_i].replace(old, new)
# the thrown shovels: kamas round them, drawn bigger (spell `coins`: render.js shovelCoins, game.js their trail; the hitbox is unchanged)
for sid in ('lancer_pelle', 'fu_enu_pelles', 'roulage_pelle'): S[sid]['base']['coins'] = 1
# the Jeton d'entrée au Gladiatrool: at C.gladia.t, one a run, anywhere on the map (gspells.js dropGladia): its wheel gives
# a characteristic in a place of its own, outside the 5 (gladiaToken)
C['gladia'] = {'t': 450, 'icon': 'it_15_737',
               'name': {'fr': "Jeton d'entrée au Gladiatrool", 'en': 'Gladiatrool Entry Token', 'de': 'Gladiatrool-Eintrittsjeton', 'es': 'Ficha de entrada al Gladiatrool',
                        'it': "Gettone d'ingresso al Gladiatrool", 'nl': 'Gladiatrool-toegangsfiche', 'pt': 'Ficha de entrada no Gladiatrool'}}
# the Roublard's Bomberfus 1.5 times as big (sumK: pixi_render.js summon, render.js drawSummon), from a sheet rendered at that size
assert S['fu_rou_bomberfu']['base']['spriteKey'] == '1379_z30'; S['fu_rou_bomberfu']['base'].update(spriteKey='1379_z45', sumK=1.5)
UI_983 = {
    'owned_f': ("Obtenus", "Owned", "Erhalten", "Obtenidos", "Ottenuti", "Verkregen", "Obtidos"),
    'gl_here': ("Un jeton est apparu quelque part sur la carte ! (voir la minicarte)", "A token has appeared somewhere on the map! (see the minimap)", "Ein Jeton ist irgendwo auf der Karte erschienen! (siehe Minikarte)",
                "¡Ha aparecido una ficha en algún lugar del mapa! (mira el minimapa)", "Un gettone è apparso da qualche parte sulla mappa! (vedi la minimappa)", "Er is ergens op de kaart een fiche verschenen! (zie de minikaart)", "Apareceu uma ficha algures no mapa! (vê o minimapa)"),
    'gl_title': ("Roue du Gladiatrool", "Gladiatrool Wheel", "Gladiatrool-Rad", "Rueda del Gladiatrool", "Ruota del Gladiatrool", "Gladiatrool-rad", "Roda do Gladiatrool"),
    'gl_spin': ("Le Trool lance sa roue… tiens-toi prêt, l'arène n'attend pas.", "The Trool spins his wheel… get ready, the arena won't wait.", "Der Trool dreht sein Rad … mach dich bereit, die Arena wartet nicht.",
                "El Trool hace girar su rueda… prepárate, la arena no espera.", "Il Trool gira la sua ruota… preparati, l'arena non aspetta.", "De Trool draait zijn rad… maak je klaar, de arena wacht niet.", "O Trool gira a sua roda… prepara-te, a arena não espera."),
    'gl_won': ("{n} : caractéristique bonus !", "{n}: bonus characteristic!", "{n}: Bonus-Eigenschaft!", "{n}: ¡característica adicional!", "{n}: caratteristica bonus!", "{n}: bonuskenmerk!", "{n}: característica bónus!"),
    'gl_note': ("Elle prend une place à part : vos 5 caractéristiques habituelles restent toutes disponibles.", "It takes a place of its own: your usual 5 characteristics all stay available.",
                "Sie bekommt einen eigenen Platz: Deine üblichen 5 Eigenschaften bleiben alle verfügbar.", "Ocupa un lugar propio: tus 5 características habituales siguen disponibles.",
                "Occupa un posto a parte: le tue 5 caratteristiche abituali restano tutte disponibili.", "Het krijgt een eigen plaats: je gebruikelijke 5 kenmerken blijven allemaal beschikbaar.",
                "Ocupa um lugar à parte: as tuas 5 características habituais continuam disponíveis."),
}
for key, vals in UI_983.items():
    for lg, v in zip(LANGS7, vals): assert key not in C['ui'][lg], (lg, key); C['ui'][lg][key] = v

if __name__ == '__main__':
    json.dump(C, open(f'{G}/data/content.json', 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
    print('0.98 ok: Invisibilité', [(l.get('cd'), l.get('duration')) for l in [S['invisibilite']['base']] + S['invisibilite']['lv']],
          '| Flèche Explosive', [l.get('dmg') for l in [FE] + S['fleche_explosive']['lv']], FE['cd'],
          '| Intelligence', INT['perShop'], '| Manuel', {k: C['manuel']['boss'][k] for k in ('chef_bouftou', 'bouftou_royal', 'kruorre', 'minotoror', 'royalmouth', 'grand_envoye', 'goultard')})
    print('HIGH: traps', [(k, S[k]['base']) for k in ('piege_sournois', 'fu_sram_piege')], [l.get('dmg') for l in S['piege_sournois']['lv']],
          '| Boufcouls', BA, '| Rempart', RE, '| Explobombe', EB['base']['cd'], [l.get('fuse') for l in [EB['base']] + EB['lv']])
    print('after the build: cooldowns', len(CD_DONE), 'spells (Cra x1.2:', sorted(k for k, v in CD_DONE.items() if v == 1.2), ') | hard', H, '| relicElite', C['relicElite'], '| dofus', {k: DF[k]['bonus'] for k in ('ocre', 'cawotte', 'pourpre')})
    print('ULTRA: bosses', {k: C['bosses'][k]['hp'] for k in ('chef_bouftou', 'bouftou_royal', 'dark_vlad', 'goultard')}, '| lvDmg', R['lvDmg'], R['lvDmgMax'],
          '| xpEarly', R['xpEarly'], 'saved', saved, 'back', add, '| cdLate', R['cdLate'])
