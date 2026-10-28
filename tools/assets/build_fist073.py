"""0.73: Frappe du Craqueleur's real effect — the grey stone fist falling and smashing (client clip
clips/spells/212.swf, inner sprite 8: its exported 'shoot' only holds the ring and places the fist by script, so the fist
is rendered from its own sprite) → assets/fx/212f.webp + SPR.fx['212f'] (origin = the impact point on the ground).
usage: python tools/assets/build_fist073.py [zoom=3.6]"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import sys, os
import swflib as S, stage as ST, sprio

G = f'{ROOT}/game'


def main(z):
    src = f'{ROOT}/raw/rc/clips/spells/212.swf'; rate = S.read_swf(src)['rate']
    r = ST.stage_render(src, [dict(key='f', cid=8, zoom=z, frames=list(range(48)), n=48)], f'{ROOT}/work/fx073/212f', holds=True)['f']
    items, fr = [], []
    for i, im in enumerate(r['imgs']):
        if im is None or not im.getbbox(): fr.append(None); continue
        c, ox, oy = ST.crop(im, r['meta']['origin']); items.append((i, c)); fr.append((i, ox, oy))
    while fr and fr[-1] is None: fr.pop()
    atlas, pos = ST.pack(items, maxw=4096)
    atlas.save(f'{G}/assets/fx/212f.webp', 'WEBP', quality=88, method=6)
    F = [[0, 0, 1, 1, 0, 0] if o is None else [*pos[o[0]], round(o[1], 2), round(o[2], 2)] for o in fr]
    meta = dict(w=atlas.width, h=atlas.height, zoom=z, anims=dict(root=dict(fps=rate, f=F)))
    sprio.update(lambda S_: S_['fx'].__setitem__('212f', meta))
    print('212f', len(F), 'frames', atlas.size, os.path.getsize(f'{G}/assets/fx/212f.webp') // 1024, 'KB')


if __name__ == '__main__':
    main(float(sys.argv[1]) if len(sys.argv) > 1 else 3.6)
