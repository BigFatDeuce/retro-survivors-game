# 0.62: the same frozen run drawn by the 2D canvas, then by PixiJS (one page: PX.on switched), compared pixel by pixel.
# Every class with all of its spells (zones, glyphs, traps, bombs, summons, allies, orbiters, projectiles, effects),
# pickups of every kind, marked / stunned / slowed / poisoned monsters. Prints the mean difference per scene (0-255) and
# the share of pixels off by more than 40; writes <scene>_canvas.png, <scene>_pixi.png, <scene>_diff.png.
# env SCENES=cra,feca… (default: all classes)
import os
import numpy as np
from PIL import Image
SC = os.environ.get('SCENES', 'feca,osamodas,enutrof,sram,xelor,ecaflip,eniripsa,iop,cra,sadida,sacrieur,pandawa,roublard,bandit').split(',')
SP = {
    'feca': 'bouclier_feca:4,bulle:4,glyphe_enflammee:4,attaque_nuageuse:4,glyphe_immobilisation:4',
    'osamodas': 'invoc_bouftou:4,fouet:4,corbeau:4,invoc_tofu:4,dragonnet_rouge:4',
    'enutrof': 'lancer_pieces:4,lancer_pelle:4,pelle_massacrante:4,coffre_anime:4,boite_pandore:4',
    'sram': 'piege_sournois:4,coup_sournois:4,attaque_mortelle:4,double:4,poison_insidieux:4',
    'xelor': 'aiguille:4,rayon_obscur:4,ralentissement:4,poussiere_temporelle:4,frappe_xelor:4',
    'ecaflip': 'pile_ou_face:4,griffe_joueuse:4,rekop:4,griffe_invocatrice:4,tout_ou_rien:4',
    'eniripsa': 'mot_blessant:4,mot_interdit:4,mot_frayeur:4,mot_amitie:4,mot_vampirique:4',
    'iop': 'epee_iop:4,pression:4,colere_iop:4,epee_celeste:4,tempete_puissance:4',
    'cra': 'fleche_explosive:4,fleche_magique:4,fleche_enflammee:4,fleche_glacee:4,fleche_empoisonnee:4',
    'sadida': 'ronce:4,tremblement:4,la_folle:4,vent_empoisonne:4,la_sacrifiee:4',
    'sacrieur': 'furie:4,attirance:4,absorption:4,epee_volante:4,assaut:4',
    'pandawa': 'karcham:4,flasque_explosive:4,gueule_de_bois:4,vague_lame:4,poing_enflamme:4',
    'roublard': 'explobombe:4,dagues_boomerang:4,tromblon:4,kaboom:4,grisou:4',
    'bandit': 'elagage_cou:4,fronde:4,vol_pieces:4,appel_mama:4,lancer_hachette:4',
}
SETUP = """(() => { const R = Game.run, P = R.player; P.god = 1;
  const kinds = ['gem', 'kama', 'bread', 'rappel', 'gold', 'relic', 'manuel', 'kamaboost', 'dofus', 'tmap', 'booster', 'chest'];
  kinds.forEach((k, i) => R.pickups.push({ kind: k, x: P.x - 260 + i * 46, y: P.y + 150, v: k === 'gem' ? 20 : k === 'relic' ? R.C.relics[0].id : k === 'dofus' ? R.C.dofus[0].id : 1, pk: 1 }));
  R.mobs.slice(0, 40).forEach((m, i) => { if (i % 4 === 0) m.markUntil = 1e9; if (i % 4 === 1) m.stunUntil = 1e9; if (i % 4 === 2) m.slowUntil = 1e9; if (i % 4 === 3) { m.poisonUntil = 1e9; m.bleedUntil = 1e9; } });
})()"""
FREEZE = "(() => { const R = Game.run; R.update = () => {}; R.update._f = 1; R.shakeAmt = 0; R.shake = () => {}; R.chromaK = () => 0; })()"   # (0.98: no chromatic aberration: a PixiJS-only pass over the frame, Run.chromaK)
res = []
for c in SC:
    url(f'autostart=1&fresh=1&cls={c}&map=astrub&t=150&pixi=1&spells={SP[c]}')
    pg.wait_for_function('Game.run && Game.state==="run" && PX.on', timeout=90000)
    pg.evaluate("setInterval(() => { const R = Game.run; if (R && !R.update._f) R.player.hp = R.stats.maxHp; }, 30)")
    time.sleep(9)
    pg.evaluate(SETUP); time.sleep(1.2)
    pg.evaluate(FREEZE); time.sleep(0.6)
    shot(f'{c}_pixi')
    pg.evaluate("PX.on = false; PX.hide()"); time.sleep(0.5)
    shot(f'{c}_canvas')
    pg.evaluate("PX.on = true"); time.sleep(0.3)
    a = np.asarray(Image.open(f'{out}/{c}_canvas.png').convert('RGB')).astype(int)
    b = np.asarray(Image.open(f'{out}/{c}_pixi.png').convert('RGB')).astype(int)
    d = np.abs(a - b).max(axis=2)
    Image.fromarray(np.clip(d * 4, 0, 255).astype('uint8')).save(f'{out}/{c}_diff.png')
    res.append((c, d.mean(), (d > 40).mean() * 100))
    print(f'{c:10s} mean {d.mean():5.2f}   off>40: {(d > 40).mean() * 100:5.2f} %', flush=True)
print('ERRS', [l for l in logs if 'pageerror' in l or 'error' in l.lower()][:10])
