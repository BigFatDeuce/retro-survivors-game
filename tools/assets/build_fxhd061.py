"""0.61 (some spells looked pixelated): effect sheets rendered again from the client's spell clips
(clips/spells/<n>.swf) at the zoom the game really shows them at. v1.6 had shrunk every effect to zoom 1.6 (the
lightning 808 to 1.1, downscale16) and the area spells are drawn scaled with their radius: measured in game at
2560x1440 (sprite px -> screen px, 90th percentile, every class with its spells at level 6), 702 / 809 were drawn
x3 bigger than their sheet, 704 x2.5, 808 x2.3...  Each sheet keeps its animations, frame count and timing: every
frame of the old sheet is matched to the client frame it was cut from (small thumbnails, size and origin checked),
then that client frame is rendered at the new zoom.
usage: [HOLDS=0] python tools/assets/build_fxhd061.py id:zoom[:key] …     e.g. 702:4.2 808:1.8 603:8:ui603 (key: a new sheet, the old
one kept — the dice of the level-up reroll use their own big copies)"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import sys, os, json
import numpy as np
from PIL import Image
import swflib as S, timeline as TL, stage as ST, sprio

G = f'{ROOT}/game'
WORK = f'{ROOT}/work/fxhd061'


def thumb(im, n=24):
    return np.asarray(im.convert('RGBA').resize((n, n), Image.BILINEAR)).astype(np.float32)


def render(n, anims, Z, counts=None, holds=True):
    """the client frames of every animation of the sheet, at zoom Z: {anim: [(crop, ox, oy) | None]}"""
    src = f'{ROOT}/raw/rc/clips/spells/{n}.swf'
    sw = S.read_swf(src); ex = S.exports(sw['tags']); tl = TL.Timeline(sw)
    jobs = []
    for a in anims:
        if a == 'root':
            sw2 = S.read_swf(src); sw2['tags'].append(ST.root_sprite(sw2))
            jobs.append(dict(key='root', root=True, zoom=Z, n=max(TL.Timeline(sw2).eff_frames(ST.ROOT_ID), (counts or {}).get(a, 0))))
        elif a in ex: jobs.append(dict(key=a, sym=a, zoom=Z, n=max(tl.eff_frames(ex[a]), (counts or {}).get(a, 0))))
        else: print(n, 'no symbol', a, flush=True)
    R = ST.stage_render(src, jobs, f'{WORK}/{n}_z{Z}' + ('' if holds else '_run'), holds=holds)
    out = {}
    for a, r in R.items():
        out[a] = [None if im is None or not im.getbbox() else ST.crop(im, r['meta']['origin']) for im in r['imgs']]
    return out, sw['rate']


def build(n, Z, key=None):
    SPR = json.load(open(f'{G}/data/sprites.json', encoding='utf8')); meta = SPR['fx'][str(n)]; Z0 = meta['zoom']; key = key or str(n)
    old = Image.open(f'{G}/assets/fx/{n}.webp').convert('RGBA')
    run = os.environ.get('HOLDS') == '0'   # (HOLDS=0: the clip runs on past its stop() — as the old sheets were cut, as many frames as they have)
    new, rate = render(n, list(meta['anims']), Z, {a: len(v['f']) for a, v in meta['anims'].items()} if run else None, holds=not run)
    kz = Z0 / Z
    items, fmap, report = [], {}, {}
    for a, an in meta['anims'].items():
        cand = new.get(a)
        if not cand: raise SystemExit(f'{n}: animation {a} has no client frames, sheet left as it is')
        th = [None if c is None else (thumb(c[0]), c[0].width * kz, c[0].height * kz, c[1] * kz, c[2] * kz) for c in cand]
        picks, bad = [], 0
        for f in an['f']:
            x, y, w, h, ox, oy = f[:6]
            if w <= 1 and h <= 1: picks.append(None); continue
            t0 = thumb(old.crop((round(x), round(y), round(x + w), round(y + h)))); best = None
            for i, c in enumerate(th):
                if c is None: continue
                tt, cw, ch, cox, coy = c
                fit = abs(cw - w) <= max(3, w * 0.08) and abs(ch - h) <= max(3, h * 0.08) and abs(cox - ox) <= max(4, w * 0.1) and abs(coy - oy) <= max(4, h * 0.1)
                err = float(np.abs(tt - t0).mean()) + (0 if fit else 40)
                if best is None or err < best[0]: best = (err, i)
            if best is None or best[0] >= 40: bad += 1
            picks.append(best[1] if best else None)
        for i in set(p for p in picks if p is not None): items.append(((a, i), cand[i][0]))
        fmap[a] = picks; report[a] = f'{len(picks)} frames, {bad} poor matches'
        if os.environ.get('PICKS'): print(n, a, 'picks', picks, flush=True)
    atlas, pos = ST.pack(items, maxw=4096)
    if atlas.width > 4096 or atlas.height > 4096: raise SystemExit(f'{n}: atlas too big {atlas.size}, lower the zoom')
    atlas.save(f'{G}/assets/fx/{key}.webp', 'WEBP', quality=88, method=6)
    M = dict(meta, w=atlas.width, h=atlas.height, zoom=Z, anims={})
    for a, an in meta['anims'].items():
        F = []
        for f, p in zip(an['f'], fmap[a]):
            if p is None: F.append([0, 0, 1, 1, 0, 0]); continue
            c = new[a][p]; F.append([*pos[(a, p)], round(c[1], 2), round(c[2], 2)] + list(f[6:]))
        M['anims'][a] = dict(an, f=F)
    sprio.update(lambda S_: S_['fx'].__setitem__(key, M))
    print(key, f'zoom {Z0} -> {Z}', atlas.size, report, flush=True)


if __name__ == '__main__':
    for arg in sys.argv[1:]:
        p = arg.split(':'); n, Z = p[0], float(p[1]); key = p[2] if len(p) > 2 else None
        try: build(n, Z, key)
        except SystemExit as e: print('FAIL', e, flush=True)
        except Exception as e:
            import traceback; traceback.print_exc(); print('FAIL', n, e, flush=True)
