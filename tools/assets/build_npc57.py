"""0.57: a scene character in HD — only the animations a scene plays, rendered natively from the client sprite at a
high zoom, identical frames stored once -> assets/mobs/<gfx>_z<zoom*10>.webp + SPR.mobs.
  GFX=1010 python tools/assets/build_npc57.py 8      ToT (the quiz lion, C.totSprite 1010_z80; 10 overflows the 4096 atlas)
  GFX=1153 ANIMS=staticR,bonusR,anim1R,anim2R python tools/assets/build_npc57.py 12     Musha l'Oni (1153_z120, his
      treasure-map scene; was build_musha47.py)
  env GFX (default 1010), ANIMS (default ToT's), argument ZOOM (default 10)."""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import sys, os, json, hashlib
import swflib as S, timeline as TL, stage as ST
import sprio

G = f'{ROOT}/game'
GFX = int(os.environ.get("GFX", "1010")); ANIMS = tuple(os.environ.get("ANIMS", "staticR,staticF,staticB,walkR,walkL,walkF,walkB,runR,runS").split(","))

if __name__ == '__main__':
    z = float(sys.argv[1]) if len(sys.argv) > 1 else 10.0
    key = f'{GFX}_z{round(z * 10)}'
    path = f'{ROOT}/raw/rc/clips/sprites/{GFX}.swf'
    sw = S.read_swf(path); ex = S.exports(sw['tags']); tl = TL.Timeline(sw); low = {k.lower(): k for k in ex}
    jobs = [dict(key=a, sym=low[a.lower()], zoom=z, n=min(60, tl.eff_frames(ex[low[a.lower()]]))) for a in ANIMS if a.lower() in low]
    res = ST.stage_render(path, jobs, f'{ROOT}/work/mobs57/{GFX}_{key}', prune=True)
    items, frames, seen = [], {}, {}
    for job in jobs:
        r = res[job['key']]; fl = []
        for i, im in enumerate(r['imgs']):
            if im is None or not im.getbbox(): fl.append(None); continue
            c, ox, oy = ST.crop(im, r['meta']['origin'])
            hs = hashlib.md5(c.tobytes() + bytes(str(c.size), 'ascii')).hexdigest()
            if hs not in seen: seen[hs] = (job['key'], i); items.append(((job['key'], i), c))
            fl.append((seen[hs], round(ox, 2), round(oy, 2)))
        frames[job['key']] = fl
    atlas, pos = ST.pack(items, maxw=4096)
    print(key, 'frames', sum(len(v) for v in frames.values()), 'unique', len(items), 'atlas', atlas.size)
    if atlas.height > 4096: raise SystemExit('atlas too tall: lower the zoom')
    atlas.save(f'{G}/assets/mobs/{key}.webp', 'WEBP', quality=90, method=6)
    anims = {}
    for a, fl in frames.items():
        F = []
        for o in fl:
            if o is None: F.append(F[-1] if F else [0, 0, 1, 1, 0, 0]); continue
            x, y, w, h = pos[o[0]]; F.append([x, y, w, h, o[1], o[2]])
        anims[a] = dict(fps=sw['rate'], f=F)
    sprio.update(lambda SPR: SPR['mobs'].__setitem__(key, dict(w=atlas.width, h=atlas.height, zoom=z, anims=anims)))
    print('ok', key, os.path.getsize(f'{G}/assets/mobs/{key}.webp'))
