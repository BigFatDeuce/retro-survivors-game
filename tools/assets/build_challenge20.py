"""Challenge pictures (clips/challenges/<n>.swf) added to the HD icon atlas icons3 as 'ch_<n>' (same recipe as
build_icons20: rendered at 2T from the vectors, reduced to T). Used by the 'Borné' characteristic (0.20).
usage: python tools/assets/build_challenge20.py 20 [n…]"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import sys
import stage as ST, build_icons20 as B
from PIL import Image

T = B.T


def render(ns, work=f'{ROOT}/work/chall20'):
    jobs = []
    for n in ns:
        p = f'{ROOT}/raw/rc/clips/challenges/{n}.swf'
        _, s = B.size_of(p)
        jobs.append((p, [dict(key=f'ch_{n}', root=True, zoom=T * 2 / s, frames=[0], n=1)]))
    res = ST.stage_batch(jobs, work); out = {}
    for n in ns:
        r = res.get(f'ch_{n}'); im = r['imgs'][0] if r and r['imgs'] else None
        if im is None or not im.getbbox(): print('empty', n); continue
        im = im.crop(im.getbbox()); s = T / max(im.size)
        out[f'ch_{n}'] = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    return out


if __name__ == '__main__':
    B.merge(render([int(a) for a in sys.argv[1:]] or [20]))
