"""0.34: Marteau de Moon as the client casts it (spell 366, clip clips/spells/2051.swf): the spinning swirl that flies
(sprite 11, 'move'), the arcs it leaves behind (sprite 7 = the 'cercle' it attaches on its way, 'trail') and the spark
on impact (sprite 21, frames 18-26, 'shoot') -> assets/fx/2051.webp + SPR.fx['2051']. The icon sp_g_moon is the
client print spells/icons/up/366.swf on the global spells' silver background; every sp_g_* icon is flagged as a full
spell icon (drawn at the class icons' size, without the generic yellow disc).
usage: python tools/assets/build_moon34.py"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import os
from PIL import Image
import stage as ST, sprio
import build_icons20 as B, build_spellicons21 as SI, build_globalicons23 as GI

G = f'{ROOT}/game'
SRC = f'{ROOT}/raw/rc/clips/spells/2051.swf'
Z = 4.8          # render zoom (HD)
SIZE = 2.2       # drawn this much bigger than the client's own size (a survivors projectile, seen from further away)


def fx_sheet():
    parts = [('move', 11, range(3)), ('trail', 7, range(10)), ('shoot', 21, range(18, 27))]
    jobs = [dict(key=k, cid=c, zoom=Z, frames=list(fr), n=max(fr) + 1) for k, c, fr in parts]
    R = ST.stage_render(SRC, jobs, f'{ROOT}/work/moon34/fx', prune=True)
    items, F = [], {}
    for k, c, fr in parts:
        r = R[k]; F[k] = []
        for i, im in enumerate(r['imgs']):
            if im is None or not im.getbbox(): F[k].append(None); continue
            cimg, ox, oy = ST.crop(im, r['meta']['origin']); items.append(((k, i), cimg)); F[k].append((ox, oy))
    atlas, pos = ST.pack(items, maxw=2048)
    atlas.save(f'{G}/assets/fx/2051.webp', 'WEBP', quality=90, method=6)
    anims = {}
    for k, _, _ in parts:
        fl = []
        for i, o in enumerate(F[k]):
            if o is None: fl.append([0, 0, 1, 1, 0, 0]); continue
            x, y, w, h = pos[(k, i)]; fl.append([x, y, w, h, round(o[0], 2), round(o[1], 2)])
        anims[k] = dict(fps=20, f=fl)
    print('fx 2051', atlas.size, {k: len(v['f']) for k, v in anims.items()})
    return dict(w=atlas.width, h=atlas.height, zoom=round(Z / SIZE, 4), anims=anims)


def icon():
    back = GI.silver(SI.render({'b3': f'{ROOT}/raw/rc/clips/spells/icons/back/3.swf'}, 200)['b3'].resize((GI.W, GI.H), Image.LANCZOS))
    pr = SI.render({'p': f'{SI.UP}/366.swf'}, 400)['p']; pr = GI.white_print(pr.crop(pr.getbbox()))
    s = GI.W * 0.62 / max(pr.size); pr = pr.resize((round(pr.width * s), round(pr.height * s)), Image.LANCZOS)
    im = back.copy(); im.alpha_composite(pr, ((GI.W - pr.width) // 2, (GI.H - pr.height) // 2))
    return im


if __name__ == '__main__':
    meta = fx_sheet()
    sprio.update(lambda S: S['fx'].__setitem__('2051', meta))
    B.merge({'sp_g_moon': icon()})
    def full(S):   # the global spell icons are complete icons (background + print), like the class ones
        for k, f in S['icons3'].items():
            if k.startswith('sp_g_'): f[7] = 1
    sprio.update(full)
    print('ok')
