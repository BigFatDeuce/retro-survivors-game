"""0.60 relics (the): each relic's bonus follows what the real Dofus Retro item gives (its effects in work/sl.db:
6f = 1 PA -> faster spells, 80 = PM -> speed, 7d = Vitality -> max HP, 76 = Strength / 8a = % damage -> damage,
7c = Wisdom -> experience, 7b = Chance -> luck, 77 = Agility -> crits / dodge, 73 = critical hits, b6 = summons -> amount,
b2 = heals, b0 = prospecting, 79 / dc = damage returned, resistances -> armour…); descriptions written from the numbers.
apply(C) is called by patch_060."""

LG = ('fr', 'en', 'de', 'es', 'it', 'nl', 'pt')
BONUS = {   # id: (bonus, special)
    'gelano': ({'cooldown': -0.10}, {}),                                       # 1 PA
    'amu_craqueleur': ({'maxhp': 0.08, 'might': 0.06, 'crit': 0.03}, {}),     # Vitality, Strength, Agility, Intelligence
    'anneau_sanglier': ({'growth': 0.15}, {}),                                 # Wisdom
    'anneau_prespic': ({}, {'thorns': 0.6}),                                   # damage returned
    'dents_wabbit': ({'crit': 0.06, 'projspeed': 0.15}, {}),                   # Agility, crits, 1 range
    'sandales_tofu': ({'luck': 0.2}, {}),                                      # Chance
    'collier_minotoror': ({'maxhp': 0.25, 'cooldown': -0.05}, {}),             # 1 PA, lots of Vitality
    'kwakanneau_flammes': ({'area': 0.1}, {'burn': 0.15}),                     # Intelligence, fire resistance
    'talisman_chene_mou': ({'maxhp': 0.12, 'regen': 0.4, 'cooldown': -0.04}, {}),   # Vitality, heals, 1 PA
    'anneau_kitsou': ({'armor': 3, 'maxhp': 0.08}, {}),                        # resistances, Vitality
    'bottes_koulosse': ({'speed': 0.15, 'maxhp': 0.06}, {}),                   # 1 PM, Vitality
    'amu_craqueleur_leg': ({'cooldown': -0.08, 'maxhp': 0.08, 'armor': 2}, {}),    # 1 PA, Vitality, resistances
    'ceinture_craqueleur_leg': ({'amount': 1}, {}),                            # 1 summon
    'anneau_dragon_cochon': ({'might': 0.12, 'crit': 0.04, 'luck': 0.1}, {}),  # % damage, crits, Chance
    'coiffe_dragon_cochon': ({'critMult': 0.5, 'reflect': 1}, {}),             # crits, damage returned
    'masque_rat_noir': ({'evade': 0.06, 'crit': 0.03}, {}),                    # Agility
    'anneau_rat_noir': ({'might': 0.06, 'reflect': 1}, {}),                    # % damage, damage returned
    'cape_wa_wabbit': ({'maxhp': 0.2}, {}),                                    # Vitality
    'coiffe_chene_mou': ({'might': 0.1, 'maxhp': 0.1, 'healBonus': 0.2}, {}),  # % damage, Vitality, heals
    'bouclier_moon': ({'duration': 0.2, 'projspeed': 0.2}, {}),                # (a trophy: no stats in Retro)
}
PH = {   # one phrase per stat: {p} = percent, {n} = number
    'maxhp': ('+{p} % de PV max', '+{p}% max HP', '+{p} % max. LP', '+{p} % de PdV máx.', '+{p}% PV max', '+{p}% max. LP', '+{p}% de PV máx.'),
    'might': ('+{p} % de dégâts', '+{p}% damage', '+{p} % Schaden', '+{p} % de daño', '+{p}% danni', '+{p}% schade', '+{p}% de dano'),
    'crit': ('+{p} % de coups critiques', '+{p}% critical hits', '+{p} % kritische Treffer', '+{p} % de golpes críticos', '+{p}% colpi critici', '+{p}% kritieke treffers', '+{p}% de golpes críticos'),
    'cooldown': ('sorts rechargés {p} % plus vite', 'spells recharge {p}% faster', 'Zauber laden {p} % schneller', 'hechizos recargados un {p} % más rápido', 'incantesimi ricaricati del {p}% più in fretta', 'spreuken laden {p}% sneller op', 'feitiços recarregam {p}% mais rápido'),
    'growth': ('+{p} % d\'expérience', '+{p}% experience', '+{p} % Erfahrung', '+{p} % de experiencia', '+{p}% esperienza', '+{p}% ervaring', '+{p}% de experiência'),
    'projspeed': ('+{p} % de vitesse des projectiles', '+{p}% projectile speed', '+{p} % Geschossgeschwindigkeit', '+{p} % de velocidad de proyectiles', '+{p}% velocità dei proiettili', '+{p}% projectielsnelheid', '+{p}% de velocidade dos projéteis'),
    'luck': ('+{p} % de chance', '+{p}% luck', '+{p} % Glück', '+{p} % de suerte', '+{p}% fortuna', '+{p}% geluk', '+{p}% de sorte'),
    'area': ('+{p} % de zone d\'effet', '+{p}% area of effect', '+{p} % Wirkungsbereich', '+{p} % de área de efecto', '+{p}% area d\'effetto', '+{p}% bereik', '+{p}% de área de efeito'),
    'regen': ('+{n} PV régénérés par seconde', '+{n} HP regenerated per second', '+{n} LP Regeneration pro Sekunde', '+{n} PdV regenerados por segundo', '+{n} PV rigenerati al secondo', '+{n} LP regeneratie per seconde', '+{n} PV regenerados por segundo'),
    'armor': ('+{n} résistance', '+{n} resistance', '+{n} Widerstand', '+{n} de resistencia', '+{n} resistenza', '+{n} weerstand', '+{n} de resistência'),
    'speed': ('+{p} % de vitesse', '+{p}% speed', '+{p} % Tempo', '+{p} % de velocidad', '+{p}% velocità', '+{p}% snelheid', '+{p}% de velocidade'),
    'amount': ('+{n} projectile / invocation par sort', '+{n} projectile / summon per spell', '+{n} Geschoss / Beschwörung pro Zauber', '+{n} proyectil / invocación por hechizo', '+{n} proiettile / evocazione per incantesimo', '+{n} projectiel / oproeping per spreuk', '+{n} projétil / invocação por feitiço'),
    'critMult': ('coups critiques : +{p} % de dégâts en plus', 'critical hits: +{p}% more damage', 'kritische Treffer: +{p} % mehr Schaden', 'golpes críticos: +{p} % más de daño', 'colpi critici: +{p}% danni in più', 'kritieke treffers: +{p}% meer schade', 'golpes críticos: +{p}% a mais de dano'),
    'reflect': ('renvoie {n} niveau de dommages', 'returns {n} level of damage', 'wirft {n} Stufe Schaden zurück', 'devuelve {n} nivel de daño', 'rinvia {n} livello di danni', 'kaatst {n} niveau schade terug', 'devolve {n} nível de dano'),
    'evade': ('+{p} % d\'esquive', '+{p}% dodge', '+{p} % Ausweichen', '+{p} % de esquiva', '+{p}% schivata', '+{p}% ontwijken', '+{p}% de esquiva'),
    'healBonus': ('+{p} % de soins reçus', '+{p}% healing received', '+{p} % erhaltene Heilung', '+{p} % de curación recibida', '+{p}% cure ricevute', '+{p}% ontvangen genezing', '+{p}% de cura recebida'),
    'duration': ('+{p} % de durée des effets', '+{p}% effect duration', '+{p} % Wirkungsdauer', '+{p} % de duración de los efectos', '+{p}% durata degli effetti', '+{p}% effectduur', '+{p}% de duração dos efeitos'),
    'thorns': ('renvoie {p} % des coups reçus au corps à corps', 'returns {p}% of melee blows taken', 'wirft {p} % der erlittenen Nahkampftreffer zurück', 'devuelve el {p} % de los golpes cuerpo a cuerpo recibidos', 'rinvia il {p}% dei colpi in mischia subiti', 'kaatst {p}% van ontvangen melee-slagen terug', 'devolve {p}% dos golpes corpo a corpo recebidos'),
    'burn': ('chaque coup a {p} % de chances d\'enflammer l\'ennemi', 'each blow has a {p}% chance to set the enemy on fire', 'jeder Schlag setzt den Gegner mit {p} % Chance in Brand', 'cada golpe tiene un {p} % de probabilidad de prender fuego al enemigo', 'ogni colpo ha il {p}% di probabilità di incendiare il nemico', 'elke slag heeft {p}% kans de vijand in brand te steken', 'cada golpe tem {p}% de chance de incendiar o inimigo'),
}


def desc_of(bonus, special):
    out = {}
    for i, lg in enumerate(LG):
        parts = []
        for k, v in list(bonus.items()) + list(special.items()):
            sep = '.' if lg == 'en' else ','; t = PH[k][i]
            parts.append(t.replace('{p}', ('%g' % round(abs(v) * 100, 1)).replace('.', sep)).replace('{n}', ('%g' % v).replace('.', sep)))
        s = ', '.join(parts); out[lg] = s[0].upper() + s[1:] + '.'
    return out


def apply(C):
    for r in C['relics']:
        if r['id'] not in BONUS: continue
        b, sp = BONUS[r['id']]; r['bonus'] = dict(b); r['special'] = dict(sp); r['desc'] = desc_of(b, sp)
