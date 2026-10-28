"""0.60: icons of the three new global spells, in the look of build_globalicons23 (the client's spell background turned
silver-violet, a white print of a client item on it): sp_g_tofus (Plume de Tofu Royal), sp_g_toile (Toile peu
ragoutante), sp_g_eboul (Pierre du Craqueleur); 0.96: sp_g_chaos (Boule de Chaos: the Orbe reconstituant, a round orb).
Name keys (tofus, toile, eboul, chaos) to build only those. sprites.json through sprio.
usage: python tools/assets/build_globalicons060.py [key…]"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
from PIL import Image
import build_icons20 as B, build_spellicons21 as SI, build_globalicons23 as G

ITEMS = dict(tofus='it_53_413', toile='it_55_164', eboul='it_51_127', chaos='it_50_460')


def main(only=()):
    W, H = SI.W, SI.H
    items = {k: v for k, v in ITEMS.items() if not only or k in only}
    back = G.silver(SI.render({'b3': f'{ROOT}/raw/rc/clips/spells/icons/back/3.swf'}, 200)['b3'].resize((W, H), Image.LANCZOS))
    pics = B.render(list(items.values())); new = {}
    for k, it in items.items():
        g = G.white_detail(pics[it]); s = W * 0.62 / max(g.size); g = g.resize((max(1, round(g.width * s)), max(1, round(g.height * s))), Image.LANCZOS)
        im = back.copy(); im.alpha_composite(g, ((W - g.width) // 2, (H - g.height) // 2)); new[f'sp_g_{k}'] = im
    for it in items.values(): new[it] = pics[it]
    B.merge(new)
    import sprio   # (full spell icons, like build_moon34 flags the others: frame[7] = 1, no second background)
    def full(S):
        for k in new:
            if k.startswith('sp_g_'): S['icons3'][k][7] = 1
    sprio.update(full); print(sorted(new))


if __name__ == '__main__':
    main(tuple(_sys.argv[1:]))
