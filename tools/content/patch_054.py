"""Beta 0.54 content, applied on top of patch_053.   usage: python tools/content/patch_054.py"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
import _root
import json
import patch_053 as P3

C, G, T, put_ui = P3.C, P3.G, P3.T, P3.put_ui
pas = {p['id']: p for p in C['passives']}

# Invocations becomes Démultiplication (same effect: +1 to the spells' counts, st.amount), its own framed icon
# (tools/assets/build_demulti54.py: the client's Tofu, an arrow, a fireball)
pas['invocations'].update(icon='Icon_s_amount',
    name=T('Démultiplication', 'Multiplication', 'Vervielfältigung', 'Multiplicación', 'Moltiplicazione', 'Vermenigvuldiging', 'Multiplicação'),
    desc=T('+1 par niveau aux invocations, aux projectiles et aux sorts à plusieurs coups (orbes, frappes, bombes, rayons).',
           '+1 per level to summons, projectiles and multi-hit spells (orbs, strikes, bombs, beams).',
           '+1 pro Stufe auf Beschwörungen, Geschosse und Mehrfachzauber (Kugeln, Einschläge, Bomben, Strahlen).',
           '+1 por nivel a las invocaciones, los proyectiles y los hechizos de varios golpes (orbes, impactos, bombas, rayos).',
           '+1 per livello a evocazioni, proiettili e incantesimi a più colpi (sfere, colpi, bombe, raggi).',
           '+1 per niveau op oproepingen, projectielen en spreuken met meerdere treffers (bollen, inslagen, bommen, stralen).',
           '+1 por nível às invocações, aos projéteis e aos feitiços de vários golpes (orbes, impactos, bombas, raios).'))

# Sagesse, Renvoi, Borné: written like the other characteristics ('+x … par niveau.')
pas['sagesse']['desc'] = T("+8 % d'expérience par niveau, et 5 % à 10 % de chances de bloquer un sort à distance (pas les flèches).",
                           '+8% experience per level, and a 5% to 10% chance to block a ranged spell (not arrows).',
                           '+8 % Erfahrung pro Stufe und 5 % bis 10 % Chance, einen Fernzauber abzuwehren (keine Pfeile).',
                           '+8 % de experiencia por nivel y del 5 % al 10 % de probabilidad de bloquear un hechizo a distancia (no las flechas).',
                           "+8% di esperienza per livello e dal 5% al 10% di probabilità di bloccare un incantesimo a distanza (non le frecce).",
                           '+8% ervaring per niveau en 5% tot 10% kans om een afstandsspreuk te blokkeren (geen pijlen).',
                           '+8% de experiência por nível e 5% a 10% de hipótese de bloquear um feitiço à distância (não as flechas).')
pas['renvoi']['desc'] = T('+30 dégâts renvoyés par niveau aux monstres qui vous frappent au corps à corps, repoussés.',
                          '+30 damage per level returned to monsters that hit you in melee, pushed back.',
                          '+30 zurückgeworfener Schaden pro Stufe an Monster, die dich im Nahkampf treffen; sie werden zurückgestoßen.',
                          '+30 de daño reenviado por nivel a los monstruos que te golpean cuerpo a cuerpo, que son repelidos.',
                          '+30 danni rinviati per livello ai mostri che ti colpiscono in mischia, respinti.',
                          '+30 teruggekaatste schade per niveau aan monsters die je van dichtbij raken; ze worden teruggeduwd.',
                          '+30 de dano reenviado por nível aos monstros que te atingem corpo a corpo, repelidos.')
pas['borne']['desc'] = T('+1 emplacement de sort (5 au lieu de 4), contre un emplacement de caractéristique.',
                         '+1 spell slot (5 instead of 4), in exchange for a characteristic slot.',
                         '+1 Zauberplatz (5 statt 4), im Tausch gegen einen Eigenschaftsplatz.',
                         '+1 casilla de hechizo (5 en vez de 4), a cambio de una casilla de característica.',
                         '+1 slot incantesimo (5 invece di 4), in cambio di uno slot caratteristica.',
                         '+1 spreukplaats (5 in plaats van 4), in ruil voor een eigenschapsplaats.',
                         '+1 espaço de feitiço (5 em vez de 4), em troca de um espaço de característica.')

# the Fouet: its client lash drawn from the handle (fx 211 cleaned by tools/assets/fix_whip54.py): handle x, y, reach (sheet units)
C['spells']['fouet']['whip'] = [153, 130, 320]

# Musha l'Oni's treasure maps drop twice as often
C['tmap']['chance'] = round(C['tmap']['chance'] * 2, 4)

put_ui({
    'ps_amount': T('Invocations, projectiles, coups', 'Summons, projectiles, hits', 'Beschwörungen, Geschosse, Treffer', 'Invocaciones, proyectiles, golpes',
                   'Evocazioni, proiettili, colpi', 'Oproepingen, projectielen, treffers', 'Invocações, projéteis, golpes'),
})

# 0.54b: the shop's characteristics intro without its last sentence (not useful)
for lg, u in C['ui'].items():
    if 'traits_intro' in u: u['traits_intro'] = u['traits_intro'].rsplit('. ', 1)[0].rstrip('.') + '.'
# the Sagesse scroll also gives +0.5 % per level to block a ranged spell (as Sagesse in a run)
sc = next(s_ for s_ in C['scrolls'] if s_['id'] == 'sagesse'); sc['per']['pblock'] = 0.005
sc['desc'] = T("+3 % d'expérience et +0,5 % de blocage des sorts à distance par niveau, pour tous vos personnages.",
               '+3% experience and +0.5% ranged spell block per level, for all your characters.',
               '+3 % Erfahrung und +0,5 % Fernzauberabwehr pro Stufe, für alle Charaktere.',
               '+3 % de experiencia y +0,5 % de bloqueo de hechizos a distancia por nivel, para todos tus personajes.',
               "+3% di esperienza e +0,5% di blocco degli incantesimi a distanza per livello, per tutti i personaggi.",
               '+3% ervaring en +0,5% blokkade van afstandsspreuken per niveau, voor al je personages.',
               '+3% de experiência e +0,5% de bloqueio de feitiços à distância por nível, para todos os personagens.')
sc['totN'] = [3, 0.5]
sc['tot'] = T("+{0} % d'expérience et +{1} % de blocage des sorts", '+{0}% experience and +{1}% spell block', '+{0} % Erfahrung und +{1} % Zauberabwehr',
              '+{0} % de experiencia y +{1} % de bloqueo de hechizos', '+{0}% di esperienza e +{1}% di blocco incantesimi', '+{0}% ervaring en +{1}% spreukblokkade',
              '+{0}% de experiência e +{1}% de bloqueio de feitiços')

if __name__ == '__main__':
    json.dump(C, open(f'{G}/data/content.json', 'w'), ensure_ascii=False, separators=(',', ':'))
    print('0.54 ok', C['tmap']['chance'], pas['invocations']['name']['fr'])
