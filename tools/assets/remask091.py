"""0.91 (the characters' colours shimmer and are not as in the client): the class sheets' colour masks rendered
again, LOSSLESS. The game colours a character as base (colour zones black) + mask x colour (zone k in channel k) — which
is exactly the client's GAC.applyColor (the zone clip filled with the colour, the shading drawn over it) — but the masks
were lossy WebP: colour at half resolution (YUV 4:2:0), so the three zones bled into one another (dark rims, blotches)
differently on every frame, and the colours flickered while a character moved (measured: 1.7-3.4 % of the pixels off by
more than 40 levels on a Crâ standing / an Iop running). Only the masks change: every frame keeps its place in its
atlas, the base pictures, anchors, front layers, fps and flash fixes stay as they are. Each sheet's frames are rendered
again from the client file its builder used (zone passes 0-3 as build_chars20 / the builders), lined up on their origin,
and pasted where the old mask was; the front layers' masks (`fa` / `fh` sheets, the weapon blows' `ff`) follow (the
frame's mask where the layer is opaque). Kept as they were: the weapon sheets' copied animations (no client frame),
the Otomaï (his own colours, no mask), the Roublard and the Brigandin (no colour zones).
usage: python tools/assets/remask091.py [key…]   (every class sheet by default; env JOBS=n sheets at once, default 4)"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import sys, os, json, re
import numpy as np
from PIL import Image
import swflib as S, timeline as TL, stage as ST
import build_chars20 as BC, build_move060 as BM

G = f'{ROOT}/game'
WORK = f'{ROOT}/work/remask091'
Z = 4.8
SKIP = {'9066', '8000', '8001', '1150', '1155'}


def kind_of(key):
    m = re.match(r'^(\d+)(_h)?_(r|s|x|e)$', key)
    return (m.group(3), m.group(1), bool(m.group(2))) if m else (None, None, None)


def masks_of(R, a, n):
    """the full-frame mask of render frame n (zone k white - all black, channel k), and the base render"""
    b = R[0][a]['imgs'][n]; b0 = np.asarray(b).astype(np.int16); ch = []
    for z in (1, 2, 3):
        iz = R[z][a]['imgs'][n] if n < len(R[z][a]['imgs']) else None
        ch.append(np.clip((np.asarray(iz).astype(np.int16)[:, :, :3] - b0[:, :, :3]).mean(axis=2), 0, 255) if iz is not None else np.zeros(b0.shape[:2]))
    return np.stack(ch, axis=2).astype(np.uint8), b0


def cut(full, origin, rect):
    """the part of a full-frame picture under an atlas rect [x, y, w, h, ox, oy] (ox, oy: its origin in the rect)"""
    x, y, w, h, ox, oy = rect; x0, y0 = int(round(origin[0] - ox)), int(round(origin[1] - oy)); w, h = int(round(w)), int(round(h))
    out = np.zeros((h, w) + full.shape[2:], full.dtype)
    sx0, sy0, sx1, sy1 = max(0, x0), max(0, y0), min(full.shape[1], x0 + w), min(full.shape[0], y0 + h)
    if sx1 > sx0 and sy1 > sy0: out[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = full[sy0:sy1, sx0:sx1]
    return out


def remask(key, SPR):
    kind, sid, hat = kind_of(key); meta = SPR['chars'][key]
    src = f'{BM.NSPR if kind in ("r", "s") else BC.RAW}/{sid}.swf'
    sw = S.read_swf(src); tl = TL.Timeline(sw); ex = S.exports(sw['tags']); low = {k.lower(): k for k in ex}; heads = BC.head_ids(sw)
    plan = {}
    for a, an in meta['anims'].items():
        sym = a if a in ex else low.get(a.lower())   # (the exported name)
        if not sym or not an.get('f'): continue
        if kind == 'x' and not any(x[0] == 0 for al in (an.get('anc') or []) for x in al): continue   # (copied from an old atlas)
        n = tl.eff_frames(ex[sym])
        fr = an['src'] if kind == 's' and an.get('src') else list(range(min(90, n))) if kind == 'r' else list(range(min(80, n))) if kind == 'e' else list(range(n))
        plan[a] = (sym, fr)
    if not plan: print(key, 'nothing to do', flush=True); return
    jobs = [dict(key=a, sym=s, zoom=Z, frames=fr, **({'bounds': tl.bounds(ex[s], frames=fr)} if kind == 'x' else {})) for a, (s, fr) in plan.items()]
    wd = f'{WORK}/{key}'
    if kind == 'x': R = {z: ST.stage_render(src, jobs, f'{wd}/z{z}', holds=True, tagpatch=BC.make_patch(tl, z, hat, heads), prune=False) for z in (0, 1, 2, 3)}
    else: R = {z: BC.render(src, jobs, f'{wd}/z{z}', tl, z, hat, heads) for z in (0, 1, 2, 3)}
    base = np.asarray(Image.open(f'{G}/assets/chars/{key}.webp').convert('RGBA'))
    M = np.asarray(Image.open(f'{G}/assets/chars/{key}_m.webp').convert('RGB')).copy()
    fronts = {}
    for fk in ('fa', 'fh'):
        fm = meta.get(fk)
        if fm and os.path.exists(f'{G}/assets/chars/{fm["src"]}.webp'):
            fronts[fk] = (fm['src'], np.asarray(Image.open(f'{G}/assets/chars/{fm["src"]}.webp').convert('RGBA')), np.asarray(Image.open(f'{G}/assets/chars/{fm["src"]}_m.webp').convert('RGB')).copy())
    done, bad, nfr = set(), [], 0
    for a, (sym, fr) in plan.items():
        an = meta['anims'][a]; imgs = R[0][a]['imgs']; o = R[0][a]['meta']['origin']
        full = [n for n, im in enumerate(imgs) if im is not None and im.getbbox()]
        if len(full) != len(an['f']): bad.append((a, len(full), len(an['f']))); continue
        for j, n in enumerate(full):
            mk, b0 = masks_of(R, a, n)
            r = an['f'][j]; k = tuple(int(round(v)) for v in r[:4])
            if k not in done:   # (a flash frame shows the frame before: that rect holds the earlier frame's picture)
                done.add(k); x, y, w, h = k; sub = cut(mk, o, r)
                ref = base[y:y + h, x:x + w, 3]; new = cut(b0, o, r)[..., 3]
                if ref.shape == new.shape and np.abs(ref.astype(np.int16) - new).mean() > 12: bad.append((a, j, 'shifted')); continue
                M[y:y + h, x:x + w] = sub[:M.shape[0] - y, :M.shape[1] - x]; nfr += 1
            ff = an.get('ff')
            if kind == 'x' and ff and j < len(ff) and ff[j] and ('ff',) + tuple(int(round(v)) for v in ff[j][:4]) not in done:   # (a flash frame shares the rects of the frame before: the first one paints them)
                fr_ = ff[j]; x, y, w, h = (int(round(v)) for v in fr_[:4]); al = base[y:y + h, x:x + w, 3] > 127; done.add(('ff', x, y, w, h))
                M[y:y + h, x:x + w] = cut(mk, o, fr_)[:h, :w] * al[..., None]
            for fk, (fs, FA, FM) in fronts.items():
                lst = an.get(fk)
                if not lst or j >= len(lst) or not lst[j]: continue
                fr_ = lst[j]; x, y, w, h = (int(round(v)) for v in fr_[:4]); al = FA[y:y + h, x:x + w, 3] > 127
                FM[y:y + h, x:x + w] = cut(mk, o, fr_)[:h, :w] * al[..., None]
    Image.fromarray(M).save(f'{G}/assets/chars/{key}_m.webp', 'WEBP', **BC.MASK_WEBP)
    for fk, (fs, FA, FM) in fronts.items(): Image.fromarray(FM).save(f'{G}/assets/chars/{fs}_m.webp', 'WEBP', **BC.MASK_WEBP)
    print(key, 'frames', nfr, 'fronts', sorted(fronts), 'left as they were:', bad[:6], flush=True)


def keys_all(SPR):
    return sorted(k for k in SPR['chars'] if kind_of(k)[0] and kind_of(k)[1] not in SKIP and os.path.exists(f'{G}/assets/chars/{k}_m.webp'))


if __name__ == '__main__':
    SPR = json.load(open(f'{G}/data/sprites.json'))
    keys = sys.argv[1:] or keys_all(SPR)
    J = int(os.environ.get('JOBS', '4'))
    if J <= 1 or len(keys) == 1:
        for k in keys:
            try: remask(k, SPR)
            except Exception as e:
                import traceback; traceback.print_exc(); print('FAIL', k, e, flush=True)
    else:
        import subprocess
        procs = []
        for k in keys:
            while len([p for p in procs if p.poll() is None]) >= J:
                import time; time.sleep(2)
            procs.append(subprocess.Popen([sys.executable, __file__, k], env=dict(os.environ, JOBS='1')))
        for p in procs: p.wait()
    print('remask done', len(keys))
