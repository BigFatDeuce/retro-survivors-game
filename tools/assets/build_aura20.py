"""v2.0 idle auras (clips/auras/1.swf = level 100, 2.swf = level 200), re-rendered from the client's root timeline
(its own ground squash) with the clips' stop() actions honoured, so the sparks rise once around the feet instead of
looping all over the place. Writes assets/fx/aura1.webp / aura2.webp and SPR.fx.aura1 / aura2."""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import sys, os, json
import swflib as S, timeline as TL, stage as ST

G = f'{ROOT}/game'
Z = 2.4


def build(name, key):
    src = f'{ROOT}/raw/rc/clips/auras/{name}.swf'
    sw = S.read_swf(src); sw['tags'].append(ST.root_sprite(sw)); n = TL.Timeline(sw).eff_frames(ST.ROOT_ID)
    r = ST.stage_render(src, [dict(key='a', root=True, zoom=Z, n=n)], f'{ROOT}/work/aura20_{name}', holds=True)['a']
    items = []; fr = []
    for i, im in enumerate(r['imgs']):
        if im is None or not im.getbbox(): fr.append(None); continue
        c, ox, oy = ST.crop(im, r['meta']['origin']); items.append((i, c)); fr.append((ox, oy))
    atlas, pos = ST.pack(items, maxw=2048)
    atlas.save(f'{G}/assets/fx/{key}.webp', 'WEBP', quality=90, method=6)
    F = []
    for i, o in enumerate(fr):
        if o is None: F.append([0, 0, 1, 1, 0, 0]); continue
        x, y, w, h = pos[i]; F.append([x, y, w, h, round(o[0], 2), round(o[1], 2)])
    print(key, n, atlas.size, os.path.getsize(f'{G}/assets/fx/{key}.webp'))
    return dict(w=atlas.width, h=atlas.height, zoom=Z, anims=dict(root=dict(fps=sw['rate'], f=F)))


if __name__ == '__main__':
    import sprio
    a1, a2 = build('1', 'aura1'), build('2', 'aura2')
    sprio.update(lambda S_: S_['fx'].update(aura1=a1, aura2=a2))
