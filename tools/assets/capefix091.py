"""0.91: one view of an accessory rendered again from the up-to-date client's symbol, the other views kept. 17_170's run
view (RR) was a copy of its standing picture (fur hanging straight, too high and too big while running: real client
measured in work/retrolab, acccompare061 runR / runF); the client's RR label is a flowing fur.
An animated view (the label's clip plays) keeps its distinct frames at VF fps.
Then (capes looked wrong while running): 147 capes had ONE run picture (RR) where the client's RR label plays a
12-frame flap (build_acc060 rendered n=1): ONLY_ANIM=1 replaces the view only when the client animates it.
usage: [ONLY_ANIM=1] python tools/assets/capefix091.py sym:view[,view…] […]      e.g. capefix091.py 17_170:RR"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import sys, os, json
import numpy as np
import swflib as S, timeline as TL, stage as ST
import build_chars20 as BC, build_acc060 as A6
from PIL import Image

G = f'{ROOT}/game'
NFRAMES = int(os.environ.get('NFRAMES', 24))
ONLY_ANIM = os.environ.get('ONLY_ANIM') == '1'   # (replace a view only when the client animates it)
VF = int(os.environ.get('VF', 60))   # (0.66: the client plays every clip at its window's 60 fps)


def main(specs):
    lib = f'{A6.NEW}/clips/sprites/accessories'; where = {}
    for f in sorted(os.listdir(lib)):
        for k in S.exports(S.read_swf(f'{lib}/{f}')['tags']): where.setdefault(k, f'{lib}/{f}')
    SPR = json.load(open(f'{G}/data/sprites.json')); out = {}; groups = {}
    for spec in specs:   # (one render per client file)
        sym, _, vs = spec.partition(':'); groups.setdefault(where[sym], []).append((sym, vs.split(',')))
    for src, items in groups.items():
        sw = S.read_swf(src); tl = TL.Timeline(sw); ex = S.exports(sw['tags']); D = S.defs(sw['tags']); jobs = []
        for sym, vs in items:
            labs = A6.frame_labels(D, ex[sym])
            jobs += [dict(key=f'{sym}__{v}', sym=sym, snap=labs[v], zoom=A6.Z, n=NFRAMES) for v in vs if v in labs]
        print(os.path.basename(src), len(items), 'accessories', flush=True)
        r = ST.stage_render(src, jobs, f'{ROOT}/work/capefix091/{os.path.basename(src)[:-4]}', tagpatch=BC.make_patch(tl, None), prune=True)
        for sym, vs in items:
            meta = SPR['acci'][sym]; pic = Image.open(f'{G}/assets/acc/i/{sym}.webp').convert('RGBA'); views, vf = {}, dict(meta.get('vf') or {})
            for v, fr in meta['f'].items():   # every view as it is
                fl = fr if isinstance(fr[0], list) else [fr]
                views[v] = [(pic.crop((x, y, x + w, y + h)), ox, oy) for x, y, w, h, ox, oy in fl]
            changed = False
            for v in vs:
                rr = r.get(f'{sym}__{v}')
                fl = [ST.crop(im, rr['meta']['origin']) for im in (rr['imgs'] if rr else []) if im is not None and im.getbbox()]
                if not fl: print(sym, v, 'nothing rendered: kept'); continue
                # (the clip loops: its period = the shortest p with frame i == frame i + p for every i; 1 = a still view)
                def same(a, b): return a[0].size == b[0].size and np.abs(np.asarray(a[0]).astype(int) - np.asarray(b[0]).astype(int)).max() < 8
                n = next((q for q in range(1, len(fl) // 2 + 1) if all(same(fl[i], fl[i + q]) for i in range(len(fl) - q))), len(fl))
                if n == 1 and ONLY_ANIM: print(sym, v, 'still in the client: kept'); continue
                views[v] = fl[:n]; changed = True
                if n > 1: vf[v] = VF
                else: vf.pop(v, None)
                print(sym, v, n, 'frame(s)', fl[0][0].size, 'origin', [round(fl[0][1], 1), round(fl[0][2], 1)], flush=True)
            if not changed: continue
            m2 = A6.write_item(sym, views, zoom=meta.get('zoom') or A6.Z, vf=vf or None)
            for k in ('m', 'none'):
                if k in meta: m2[k] = meta[k]
            out[sym] = m2
    import sprio
    sprio.update(lambda S_: S_['acci'].update(out))


if __name__ == '__main__':
    main(sys.argv[1:])
