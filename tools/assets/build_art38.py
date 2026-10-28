"""0.38: bestiary artworks for the monsters that have none in the client (clips/artworks/big/<gfx>.swf missing: the
Kanigrou hivernal 1497, Père Fwetar 1660): their in-game sprite (clips/sprites/<gfx>.swf, staticR or walkR, frame 0)
rendered natively at A px, added to the art atlases as a<gfx> (the other artworks are kept as they are).
usage: python tools/assets/build_art38.py [gfx…]"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import sys, os, json
import swflib as S, stage as ST
from PIL import Image

G = f'{ROOT}/game'
SPRITES = f'{ROOT}/raw/rc/clips/sprites'


def render(gfx, A):
    path = f'{SPRITES}/{gfx}.swf'; ex = S.exports(S.read_swf(path)['tags']); low = {k.lower(): k for k in ex}
    sym = low.get('staticr') or low.get('walkr')
    r = ST.stage_render(path, [dict(key='a', sym=sym, zoom=8, n=1)], f'{ROOT}/work/art38/{gfx}', prune=True)['a']['imgs'][0]
    big = max(r.getbbox()[2] - r.getbbox()[0], r.getbbox()[3] - r.getbbox()[1])
    r = ST.stage_render(path, [dict(key='a', sym=sym, zoom=8 * A * 2 / big, n=1)], f'{ROOT}/work/art38/{gfx}b', prune=True)['a']['imgs'][0]
    im = r.crop(r.getbbox()); s = A / max(im.size)
    return im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)


def main(gfxs, A=520):
    SPR = json.load(open(f'{G}/data/sprites.json')); F = SPR['art']['f']; sheets = {}
    items = [(k, sheets.setdefault(v[0], Image.open(f'{G}/assets/art/art_{v[0]}.webp').convert('RGBA')).crop((v[1], v[2], v[1] + v[3], v[2] + v[4]))) for k, v in F.items()]
    items = [(k, im) for k, im in items if k not in {f'a{g}' for g in gfxs}] + [(f'a{g}', render(g, A)) for g in gfxs]
    for f in os.listdir(f'{G}/assets/art'):
        if f.startswith('art_'): os.remove(f'{G}/assets/art/{f}')
    NF, n, rest = {}, 0, items
    while rest:
        atlas, pos = ST.pack(rest, maxw=4096)
        fit = [(k, im) for k, im in rest if k in pos and pos[k][1] + pos[k][3] <= 4096]
        if atlas.height > 4096: atlas = atlas.crop((0, 0, atlas.width, 4096))
        atlas.save(f'{G}/assets/art/art_{n}.webp', 'WEBP', quality=88, method=6)
        for k, _ in fit: x, y, w, h = pos[k]; NF[k] = [n, x, y, w, h]
        rest = [(k, im) for k, im in rest if k not in NF]; n += 1
    import sprio
    sprio.update(lambda S_: S_.__setitem__('art', {'sheets': n, 'f': NF}))
    print('ok', n, 'sheets', [f'a{g}' in NF for g in gfxs])


if __name__ == '__main__':
    main([int(x) for x in sys.argv[1:]] or [1497, 1660])
