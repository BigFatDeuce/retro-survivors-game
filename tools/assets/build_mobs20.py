"""v2.0 monster sheets for the two new zones (Moon and the shipwreck island): rendered from the client sprites
(clips/sprites/<gfx>.swf: walkR, walkL, dieR, anim0R -> atkR), native colours, at the in-game resolution
(monsters 2.4, bosses 3.0). Writes assets/mobs/<key>.webp + SPR.mobs[<key>]."""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import sys, os, json
import swflib as S, timeline as TL, stage as ST
from PIL import Image

G = f'{ROOT}/game'
SPRITES = f'{ROOT}/raw/rc/clips/sprites'
AMAP = {'walkR': 'walkR', 'walkL': 'walkL', 'dieR': 'dieR', 'atkR': 'anim0R', 'staticR': 'staticR'}


def build(gfx, key, zoom, boss=False, extra=()):
    path = f'{SPRITES}/{gfx}.swf'
    sw = S.read_swf(path); ex = S.exports(sw['tags']); tl = TL.Timeline(sw)
    low = {k.lower(): k for k in ex}
    jobs = []; names = {}
    for dst, src in list(AMAP.items()) + [(a, a) for a in extra]:
        if dst == 'staticR' and not boss: continue
        s = low.get(src.lower())
        if not s: continue
        n = min(60, tl.eff_frames(ex[s]))
        jobs.append(dict(key=dst, sym=s, zoom=zoom, n=n)); names[dst] = s
    res = ST.stage_render(path, jobs, f'{ROOT}/work/mobs20/{key}', prune=True)   # (0.51: per key: parallel builds)
    items = []; frames = {}
    for job in jobs:
        r = res[job['key']]; fl = []
        for i, im in enumerate(r['imgs']):
            if im is None or not im.getbbox(): fl.append(None); continue
            c, ox, oy = ST.crop(im, r['meta']['origin']); items.append(((job['key'], i), c)); fl.append((round(ox, 2), round(oy, 2)))
        frames[job['key']] = fl
    atlas, pos = ST.pack(items, maxw=4096)
    if atlas.height > 4096: raise SystemExit(f'{key} atlas too tall {atlas.size}')
    atlas.save(f'{G}/assets/mobs/{key}.webp', 'WEBP', quality=88, method=6)
    anims = {}
    for a, fl in frames.items():
        F = []
        for i, o in enumerate(fl):
            if o is None:
                if F: F.append(F[-1]); continue
                F.append([0, 0, 1, 1, 0, 0]); continue
            x, y, w, h = pos[(a, i)]; F.append([x, y, w, h, o[0], o[1]])
        anims[a] = dict(fps=sw['rate'], f=F)
    print(key, atlas.size, os.path.getsize(f'{G}/assets/mobs/{key}.webp'), {a: len(v['f']) for a, v in anims.items()}, flush=True)
    return dict(w=atlas.width, h=atlas.height, zoom=zoom, anims=anims)


if __name__ == '__main__':
    os.makedirs(f'{ROOT}/work/mobs20', exist_ok=True)
    import sprio
    for spec in sys.argv[1:]:   # gfx[:boss][:z=ZOOM][:+anim,anim]  (0.25: zoom and extra animations, e.g. 1153:boss:z=4.8:+anim1R,bonusR)
        gfx, *flag = spec.split(':'); boss = 'boss' in flag
        z = next((float(f[2:]) for f in flag if f.startswith('z=')), None); extra = next((f[1:].split(',') for f in flag if f.startswith('+')), ())
        key = f'{gfx}_z{round(z * 10)}' if z else f'{gfx}_z40' if boss else f'{gfx}_z32'
        meta = build(int(gfx), key, z or (3.0 if boss else 2.4), boss, extra)
        sprio.update(lambda S: S['mobs'].__setitem__(key, meta))   # (0.50: safe next to other builders)
        print('key', key)
