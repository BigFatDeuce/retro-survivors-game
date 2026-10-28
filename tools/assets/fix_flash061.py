"""0.61 (global test: a white silhouette at every weapon blow): the client's weapon attack clips end on a frame where the
whole character is white (a flash). In the weapon sheets ('<sid>_x', '<sid>_h_x') such a frame now shows the frame
before it (same timing, its anchors and front layer too); nothing is rendered again, only sprites.json changes.
A frame is 'white' when its opaque pixels are mostly white in the sheet (whose colour zones are black).
usage: python tools/assets/fix_flash061.py"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import json
import numpy as np
from PIL import Image
import sprio

G = f'{ROOT}/game'


def white(im, f):
    x, y, w, h = [int(round(v)) for v in f[:4]]
    if w <= 1 or h <= 1: return False
    a = im[y:y + h, x:x + w]; m = a[..., 3] > 128
    return bool(m.sum() > 50 and a[..., :3][m].mean() > 120)


def main():
    S = json.load(open(f'{G}/data/sprites.json', encoding='utf8'))
    out, n = {}, 0
    for key, meta in S['chars'].items():
        if not (key.endswith('_x') or key.endswith('_h_x')): continue
        im = np.asarray(Image.open(f'{G}/assets/chars/{key}.webp').convert('RGBA')).astype(np.float32)
        anims = {}
        for a, an in meta['anims'].items():
            f = an['f']; idx = [i for i in range(1, len(f)) if white(im, f[i])]
            if not idx: continue
            an = dict(an, f=list(f))
            for k_ in ('ff', 'anc'):
                if an.get(k_): an[k_] = list(an[k_])
            for i in idx:
                an['f'][i] = an['f'][i - 1]
                for k_ in ('ff', 'anc'):
                    if an.get(k_) and i < len(an[k_]): an[k_][i] = an[k_][i - 1]
                n += 1
            anims[a] = an
        if anims: out[key] = anims
    def up(S2):
        for key, anims in out.items(): S2['chars'][key]['anims'].update(anims)
    sprio.update(up)
    print('white frames replaced:', n, 'in', len(out), 'sheets')


if __name__ == '__main__':
    main()
