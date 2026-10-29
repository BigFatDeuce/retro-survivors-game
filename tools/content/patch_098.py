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
