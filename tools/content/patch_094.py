"""0.94 content, on top of patch_091 (the whole chain: run this one now):
- Difficile: the kamas dropped on the ground x1.5 (`C.hard.kamaDrop`, read once in Run.killMob — Normal unchanged; the
  other kama sources — chests, bosses, purse, merchant… — unchanged)
- Crâ: one projectile less at the top of every spell (the last +1 projectile step of each spell's levels removed or
  lowered; the three Crâ fusions -1 too, the Arc's text says seven)
- shop characteristics Vitalité and Points d'action: their value per level in a run goes with the shop's level, from
  `perShop[0]` (shop 0/5) to `perShop[1]` (5/5) in even steps (util.js passivePer) instead of `per` + 10 % a shop level
- Tofuzmo: the reach of its contact blows a third shorter (its `size`, the radius those blows use)
- chat strings: the Nowel zone gives no kamas (`nowel_info`), what Difficile changes (`hard_info`)
usage: python tools/make_content.py   (runs the newest patch; this one imports patch_091 and writes game/data/content.json)"""
import sys as _sys, os as _os, json
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
import _root
import patch_091 as P91

C, G, T, put_ui = P91.C, P91.G, P91.T, P91.put_ui
S = C['spells']

# Difficile: ground kamas x1.5 (multiplies C.run.kamaDrop, game.js killMob)
C['hard']['kamaDrop'] = 1.5

# Crâ: the top count of each spell -1 (the level that brought the last +1 now brings nothing more, or one less)
CRA = {'fleche_explosive': 2, 'fleche_magique': 5, 'fleche_enflammee': 1, 'fleche_glacee': 2, 'fleche_recul': 2, 'fleche_empoisonnee': 2}
for sid, top in CRA.items():
    lv = S[sid]['lv']; last = max(i for i, l in enumerate(lv) if 'count' in l)
    prev = max([l['count'] for l in lv[:last] if 'count' in l] + [S[sid]['base'].get('count', 1)])
    if top <= prev: del lv[last]['count']   # (the +1 of that level goes)
    else: lv[last]['count'] = top
for sid in ('fu_cra_harcel', 'fu_cra_arc', 'fu_cra_destr'): S[sid]['base']['count'] -= 1
for lg, (a, b) in dict(fr=('Huit', 'Sept'), en=('Eight', 'Seven'), de=('Acht', 'Sieben'), es=('Ocho', 'Siete'), it=('Otto', 'Sette'), nl=('Acht', 'Zeven'), pt=('Oito', 'Sete')).items():
    d = S['fu_cra_arc']['desc']; assert d[lg].startswith(a), (lg, d[lg]); d[lg] = b + d[lg][len(a):]

# Vitalité / Points d'action: per level in a run, with the shop 0/5 -> 5/5
P = {p['id']: p for p in C['passives']}
P['vitalite']['perShop'] = [0.10, 0.20]; P['vitalite']['per'] = 0.10
P['vitalite']['desc'] = T('+10 % de PV max par niveau (+20 % avec la boutique au maximum).', '+10% max HP per level (+20% with the shop maxed).',
                          '+10 % max. LP pro Stufe (+20 % mit dem Laden auf Maximum).', '+10 % de PdV máx. por nivel (+20 % con la tienda al máximo).',
                          '+10% PV max per livello (+20% con il negozio al massimo).', '+10% max. LP per niveau (+20% met de winkel op maximum).',
                          '+10% de PV máx. por nível (+20% com a loja no máximo).')
P['pa']['perShop'] = [-0.03, -0.05]; P['pa']['per'] = -0.03
P['pa']['desc'] = T('-3 % de temps de recharge des sorts par niveau (-5 % avec la boutique au maximum).', '-3% spell cooldown per level (-5% with the shop maxed).',
                    '-3 % Abklingzeit der Zauber pro Stufe (-5 % mit dem Laden auf Maximum).', '-3 % de tiempo de recarga de los hechizos por nivel (-5 % con la tienda al máximo).',
                    '-3% di tempo di ricarica degli incantesimi per livello (-5% con il negozio al massimo).', '-3% hersteltijd van spreuken per niveau (-5% met de winkel op maximum).',
                    '-3% de tempo de recarga dos feitiços por nível (-5% com a loja no máximo).')

# the Tofuzmo (the big Tofu that comes instead of ToT's door): the reach of its contact blows a third shorter. That
# reach is its radius + 12 (game.js contact damage), radius = size x ES 1.5: 30 -> 57 units; size 17.33 -> 38 (2/3).
# Its picture keeps its size (drawn by `scale`), its life / damage / moves and its bonus (+10 %, as ToT's) unchanged
TM = C['monsters']['tofu_mutant']; TM['size'] = round(((30 * 1.5 + 12) * 2 / 3 - 12) / 1.5, 2)

put_ui({
    'nowel_info': T('🎁 {n} : ici, pas de kamas à gagner, seulement des cadeaux !', '🎁 {n}: no kamas to win here, only presents!',
                    '🎁 {n}: hier gibt es keine Kamas, nur Geschenke!', '🎁 {n}: aquí no se ganan kamas, ¡solo regalos!',
                    '🎁 {n}: qui niente kama da vincere, solo regali!', '🎁 {n}: hier valt geen kama te winnen, alleen cadeaus!',
                    '🎁 {n}: aqui não se ganham kamas, só presentes!'),
    'hard_info': T('💀 Difficile : monstres +25 % de PV, coups ×2,5, un peu plus rapides et qui frappent 15 % plus souvent ; boss +25 % de PV ; deux fois plus d\'élites ; kamas au sol ×1,5.',
                   '💀 Hard: monsters +25% HP, hits ×2.5, a little faster and striking 15% more often; bosses +25% HP; twice as many elites; kamas on the ground ×1.5.',
                   '💀 Schwer: Monster +25 % LP, Treffer ×2,5, etwas schneller und schlagen 15 % öfter zu; Bosse +25 % LP; doppelt so viele Elite; Kamas am Boden ×1,5.',
                   '💀 Difícil: monstruos +25 % de PdV, golpes ×2,5, algo más rápidos y atacan un 15 % más a menudo; jefes +25 % de PdV; el doble de élites; kamas en el suelo ×1,5.',
                   '💀 Difficile: mostri +25% PV, colpi ×2,5, un po\' più veloci e colpiscono il 15% più spesso; boss +25% PV; il doppio delle élite; kama a terra ×1,5.',
                   '💀 Moeilijk: monsters +25% LP, klappen ×2,5, iets sneller en slaan 15% vaker; bazen +25% LP; twee keer zoveel elites; kama op de grond ×1,5.',
                   '💀 Difícil: monstros +25% de PV, golpes ×2,5, um pouco mais rápidos e atacam 15% mais vezes; chefes +25% de PV; o dobro de elites; kamas no chão ×1,5.'),
})

if __name__ == '__main__':
    json.dump(C, open(f'{G}/data/content.json', 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
    print('0.94 ok', {k: [l.get('count') for l in S[k]['lv']] for k in CRA})
