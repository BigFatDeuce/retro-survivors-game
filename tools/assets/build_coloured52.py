"""0.52: a monster of the client in its own colours (the Champa Rouge, Bleu, Marron share the Champa's sprite 1335): its
colour zones (instances named in the sprite's frame scripts, timeline.colors) get the monster's colours from sl.db the way
the client applies them (flat colour, the shading drawn over it; -1 = the sprite's own colour). Writes the sheet
assets/mobs/<key>.webp + SPR.mobs[key] (like build_mobs20) and its bestiary art 'p<gfx>_<hex>' (the in-game sprite
rendered big, like build_art38), then repacks the art atlases.
usage: python tools/assets/build_coloured52.py <gfx> <key> <zoom> <hex1,hex2,hex3> [art] [boss] [cx=<json>] [akey=<art key>] [devil]
(cx = a colour transform over the whole sprite; devil = the 'devil' gradient map of Goultard: tones mapped from near-black
red to hot red, a little of the drawing's own colour kept)"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import sys, os, json
import numpy as np
import swflib as S, timeline as TL, stage as ST
from PIL import Image
import build_mobs20 as BM, build_art38 as BA, build_chars20 as BC

G = f'{ROOT}/game'
SPRITES = f'{ROOT}/raw/rc/clips/sprites'


def colour_patch(tl, cols):
    """zone k (1..3) -> its flat colour (setRGB: multiply 0, add the colour); None / -1 = untouched"""
    cx = {}
    for k, h in enumerate(cols, 1):
        if h and h != '-1': r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4)); cx[k] = ((0, 0, 0, 256), (r, g, b, 0))
    def patch(t):
        if t.code != S.T_SPRITE or t.sprite_id not in tl.colors: return t
        names = tl.colors[t.sprite_id]; dz = {}; sub = []
        for x in t.sub:
            if x.code in (S.T_PLACE2, S.T_PLACE3):
                p = S.parse_place(x); d = p['depth']
                if p.get('name') in names: dz[d] = names[p['name']]
                elif p.get('char') is not None and not p.get('move'): dz.pop(d, None)
                if d in dz and dz[d] in cx: x = BC.place_with_cx(x, cx[dz[d]])
            sub.append(x)
        return ST.make_sprite(t.sprite_id, sub)
    return patch


DEVIL = np.array([[0, 8, 2, 4], [0.28, 70, 6, 10], [0.55, 150, 18, 16], [0.8, 205, 48, 26], [1.0, 248, 120, 76]], np.float32)


def devil(im, keep=0.15):
    a = np.array(im.convert('RGBA')).astype(np.float32); rgb = a[..., :3]
    L = (rgb @ np.array([0.299, 0.587, 0.114], np.float32)) / 255
    a[..., :3] = np.stack([np.interp(L, DEVIL[:, 0], DEVIL[:, k]) for k in (1, 2, 3)], -1) * (1 - keep) + rgb * keep
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def with_colours(gfx, cols, fn, cx=None):
    """cx: a colour transform over the whole sprite ((mulR, mulG, mulB, mulA), (addR, addG, addB, addA)), e.g. Goultard red"""
    tl = TL.Timeline(S.read_swf(f'{SPRITES}/{gfx}.swf')); patch = colour_patch(tl, cols); real = ST.stage_render
    def staged(src, jobs, *a, **k):
        if cx: jobs = [dict(j, cx=cx) for j in jobs]
        return real(src, jobs, *a, **dict(k, tagpatch=patch))
    ST.stage_render = staged
    try: return fn()
    finally: ST.stage_render = real


def sheet(gfx, key, zoom, cols, boss=False, cx=None, dv=False):
    meta = with_colours(gfx, cols, lambda: BM.build(gfx, key, zoom, boss), cx)
    if dv: fn = f'{G}/assets/mobs/{key}.webp'; devil(Image.open(fn)).save(fn, 'WEBP', quality=88, method=6)
    import sprio
    sprio.update(lambda S_: S_['mobs'].__setitem__(key, meta))
    print('sheet', key, meta['w'], meta['h'], flush=True)


def art(gfx, cols, A=520, cx=None, key=None, dv=False):
    arts([(gfx, cols, cx, key, dv)], A)


def arts(jobs, A=520):
    """[(gfx, cols, cx, key, devil)…]: renders each artwork, then repacks the art atlases once"""
    new = {}
    for gfx, cols, cx, key, dv in jobs:
        key = key or f'p{gfx}_{cols[0]}'
        im = with_colours(gfx, cols, lambda: BA.render(gfx, A), cx)
        new[key] = devil(im) if dv else im
        print('art', key, im.size, flush=True)
    SPR = json.load(open(f'{G}/data/sprites.json')); F = SPR['art']['f']; sheets = {}
    items = [(k, sheets.setdefault(v[0], Image.open(f'{G}/assets/art/art_{v[0]}.webp').convert('RGBA')).crop((v[1], v[2], v[1] + v[3], v[2] + v[4])))
             for k, v in F.items() if k not in new] + list(new.items())
    for f in os.listdir(f'{G}/assets/art'):
        if f.startswith('art_'): os.remove(f'{G}/assets/art/{f}')
    NF, n, rest = {}, 0, items
    while rest:
        atlas, pos = ST.pack(rest, maxw=4096)
        fit = [(k, i) for k, i in rest if k in pos and pos[k][1] + pos[k][3] <= 4096]
        if atlas.height > 4096: atlas = atlas.crop((0, 0, atlas.width, 4096))
        atlas.save(f'{G}/assets/art/art_{n}.webp', 'WEBP', quality=88, method=6)
        for k, _ in fit: x, y, w, h = pos[k]; NF[k] = [n, x, y, w, h]
        rest = [(k, i) for k, i in rest if k not in NF]; n += 1
    import sprio
    sprio.update(lambda S_: S_.__setitem__('art', {'sheets': n, 'f': NF}))
    print('arts', len(new), n, 'sheets', flush=True)


if __name__ == '__main__':
    gfx, key, zoom, cols = int(sys.argv[1]), sys.argv[2], float(sys.argv[3]), sys.argv[4].split(',')
    cx = next((json.loads(a[3:]) for a in sys.argv[5:] if a.startswith('cx=')), None)
    akey = next((a[5:] for a in sys.argv[5:] if a.startswith('akey=')), None)
    dv = 'devil' in sys.argv[5:]
    sheet(gfx, key, zoom, cols, 'boss' in sys.argv[5:], cx, dv)
    if 'art' in sys.argv[5:]: art(gfx, cols, cx=cx, key=akey, dv=dv)
