"""0.61 (capes hidden in part by the body in the client — the Enutrof's sack in front of his cape seen from behind
— were drawn whole by the game): the capes' front layers of the 60-fps runs ('<sid>_r' / '<sid>_h_r', build_move060),
like the weapons' an.ff (build_wfront060): an occluder rectangle put in the cape holders (client accessory 2) hides
everything the client paints before the cape; rendered once black and once white, the two pictures give what the client
paints over the cape at each frame and its alpha (a = 1 - (white - black)). Its pixels are the sheet frame's own (colour
zones black) under that alpha, its colour mask the frame's mask. Written as '<key>_fa.webp' (+ _m) and, per animation,
anims[a].fa = [[x, y, w, h, ox, oy] | null per frame] + anims[a].fd = the cape holder's real depth per frame.
CharSprite.draw then paints: body, cape, front layer (cape sheets with fa).
usage: python tools/assets/build_accfront061.py [sid…]   (default: every '<sid>_r' sheet; '<sid>_h_r' shares it when the head
does not change under a hat, else gets its own)"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import os, sys, json, struct
import numpy as np
from PIL import Image
import swflib as S, timeline as TL, stage as ST
import build_chars20 as BC
import build_move060 as BM
import build_wfront060 as WF
import sprio

G = f'{ROOT}/game'
# 0.62 (from the back the client paints the bun / the ponytail over the hat): SLOT=1 builds the hats' front
# layers the same way: '<key>_fh.webp', anims[a].fh / hd, SPR.chars[key].fh (CharSprite: body, hat, then its front layer)
SLOT = int(os.environ.get('SLOT', '2'))
SUF, KL, KD = ('_fa', 'fa', 'fd') if SLOT == 2 else ('_fh', 'fh', 'hd')
# 0.63: SHEET=_s = the same for the client's standing / cast / death sheets (build_still063: one frame in three outside
# the standing poses)
SHEET = os.environ.get('SHEET', '_r')
WORK = (f'{ROOT}/work/accfront061' if SLOT == 2 else f'{ROOT}/work/accfront062') + ('' if SHEET == '_r' else '/s')


def occluder(tl, rgb, base):
    holders = {sid for sid, (idx, d) in tl.acc.items() if idx == SLOT}
    shape = WF.rect_shape(WF.RECT_ID, rgb)
    def patch(t):
        t = base(t)
        if t.code == S.T_SPRITE and t.sprite_id in holders:
            sub = list(t.sub); i = next((k for k, x in enumerate(sub) if x.code == S.T_SHOWFRAME), len(sub))
            sub.insert(i, S.make_place2(999, char=WF.RECT_ID, matrix=[1.0, 0.0, 0.0, 1.0, 0.0, 0.0]))
            nt = S.Tag(S.T_SPRITE, t.data[:4], sub); nt.sprite_id = t.sprite_id; nt.frames = t.frames
            return nt
        return t
    return patch, shape


def render(src, jobs, wd, tl, rgb, hat, heads):
    base = BC.make_patch(tl, 0, hat, heads)
    patch, shape = occluder(tl, rgb, base)
    sw = S.read_swf(src); tags = list(sw['tags']); first = next(k for k, x in enumerate(tags) if x.code == S.T_SPRITE)
    tags.insert(first, shape); p = f'{wd}_src.swf'; os.makedirs(os.path.dirname(p), exist_ok=True)
    S.write_swf(dict(sw, tags=tags), p)
    return ST.stage_render(p, jobs, wd, holds=True, tagpatch=patch, prune=True)


def build(key, SPR):
    """key = '<sid>_r' or '<sid>_h_r' -> (anims fa / fd, the front atlas name)"""
    meta = SPR['chars'][key]; sid = key.split('_')[0]; hat = '_h_' in key; src = f'{BM.NSPR}/{sid}.swf'
    sw = S.read_swf(src); tl = TL.Timeline(sw); ex = S.exports(sw['tags']); heads = BC.head_ids(sw)
    anims = {a: ex[a] for a in (BM.RUNS if SHEET == '_r' else meta['anims']) if a in ex and a in meta['anims']}
    if SHEET != '_r':   # (0.63: the still sheets' own frames and the held timeline of their anchors, build_still063.plan)
        import build_still063 as B3
        tl, FR = B3.plan(sw, tl, ex, list(anims))
    jobs = []
    for a, s in anims.items():
        fr = list(range(min(BM.MAXF, tl.eff_frames(s)))) if SHEET == '_r' else FR[a]
        jobs.append(dict(key=a, sym=a, zoom=BM.Z, frames=fr, bounds=tl.bounds(s, frames=fr)))   # (the bounds of the plain render: the occluder must not grow the picture)
    wd = f'{WORK}/{key}'
    OB = render(src, jobs, f'{wd}/ob', tl, (0, 0, 0), hat, heads); OW = render(src, jobs, f'{wd}/ow', tl, (255, 255, 255), hat, heads)
    sh = np.asarray(Image.open(f'{G}/assets/chars/{key}.webp').convert('RGBA')); shm = np.asarray(Image.open(f'{G}/assets/chars/{key}_m.webp').convert('RGB'))
    items, out = [], {}
    for job in jobs:
        a = job['key']; o = OB[a]['meta']['origin']; F = meta['anims'][a]['f']; fa, fd = [], []
        anc = tl.anchors(anims[a], frames=job['frames'])
        # (the run sheets keep every frame of the render: frame j of the sheet = render j; a sheet that dropped empty
        # frames would not line up: left without front layers)
        if len(F) != len(job['frames']): print(key, a, 'frames', len(F), '!=', len(job['frames']), ': no front layer', flush=True); continue
        for j, f in enumerate(F):
            n = j
            dep = next((round(o_, 3) for i, d, m, o_ in (anc[n] if n is not None and n < len(anc) else []) if i == SLOT), None); fd.append(dep)
            ib = OB[a]['imgs'][n] if n is not None else None; iw = OW[a]['imgs'][n] if n is not None and n < len(OW[a]['imgs']) else None
            if ib is None or iw is None or dep is None: fa.append(None); continue
            x, y, w, h, ox, oy = f[:6]; x, y, w, h = int(round(x)), int(round(y)), int(round(w)), int(round(h))
            bx, by = int(round(o[0] - ox)), int(round(o[1] - oy))   # the frame's crop corner in the render
            B = np.asarray(ib).astype(np.float32); Wt = np.asarray(iw).astype(np.float32)
            Hh, Ww = B.shape[:2]
            if bx < 0 or by < 0 or bx + w > Ww or by + h > Hh: fa.append(None); continue
            Bc, Wc = B[by:by + h, bx:bx + w], Wt[by:by + h, bx:bx + w]
            base = sh[y:y + h, x:x + w].astype(np.float32); mask = shm[y:y + h, x:x + w]
            cover = (Bc[:, :, 3] > 250) & (Wc[:, :, 3] > 250)
            al = np.clip(1 - (Wc[:, :, :3] - Bc[:, :, :3]).mean(axis=2) / 255, 0, 1) * cover
            al = np.minimum(al, base[:, :, 3] / 255); al[al < 0.02] = 0
            if al.max() <= 0: fa.append(None); continue
            img = Image.fromarray(np.dstack([base[:, :, :3], al * 255]).astype(np.uint8), 'RGBA'); bb = img.getbbox()
            if not bb: fa.append(None); continue
            m = Image.fromarray((mask.astype(np.float32) * (al[:, :, None] > 0.5)).astype(np.uint8))
            items.append(((a, j), img.crop(bb), m.crop(bb))); fa.append((ox - bb[0], oy - bb[1]))
        out[a] = (fa, fd)
    if not items: return None
    atlas, pos = ST.pack([(k, b) for k, b, m in items], maxw=4096)
    ma = Image.new('RGB', atlas.size)
    for k, b, m in items: ma.paste(m, pos[k][:2])
    name = key + SUF
    atlas.save(f'{G}/assets/chars/{name}.webp', 'WEBP', quality=88, method=6); ma.save(f'{G}/assets/chars/{name}_m.webp', 'WEBP', **BC.MASK_WEBP)   # (0.91: lossless masks)
    res = {}
    for a, (fa, fd) in out.items():
        res[a] = dict(fa=[None if v is None else [*pos[(a, j)], round(v[0], 2), round(v[1], 2)] for j, v in enumerate(fa)], fd=fd)
    print(key, atlas.size, {a: sum(1 for v in r['fa'] if v) for a, r in res.items()}, flush=True)
    return name, atlas.size, res


def two_heads(sid):   # (0.64: any change under a hat: two-frame heads or 'Cheveux' clips, BC.hat_differs)
    return BC.hat_differs(f'{BM.NSPR}/{sid}.swf')


def main(sids):
    SPR = json.load(open(f'{G}/data/sprites.json', encoding='utf8'))
    X = SHEET
    sids = sids or sorted({k[:-len(X)] for k in SPR['chars'] if k.endswith(X) and not k.endswith('_h' + X)})
    done = {}
    for sid in sids:
        for key in [f'{sid}{X}'] + ([f'{sid}_h{X}'] if two_heads(sid) and f'{sid}_h{X}' in SPR['chars'] else []):
            if key not in SPR['chars'] or not os.path.exists(f'{BM.NSPR}/{sid}.swf'): continue
            try: r = build(key, SPR)
            except Exception as e:
                import traceback; traceback.print_exc(); print('FAIL', key, e, flush=True); continue
            if r: done[key] = r
        if f'{sid}{X}' in done and not two_heads(sid) and f'{sid}_h{X}' in SPR['chars']: done[f'{sid}_h{X}'] = done[f'{sid}{X}']   # (same frames: shared)
    def up(S2):
        for key, (name, size, res) in done.items():
            m = S2['chars'][key]; m[KL] = dict(src=name, w=size[0], h=size[1])
            for a, r in res.items():
                if a in m['anims'] and len(r['fa']) == len(m['anims'][a]['f']): m['anims'][a][KL] = r['fa']; m['anims'][a][KD] = r['fd']
    sprio.update(up)
    print('front layers (slot', SLOT, ') for', len(done), 'sheets')


if __name__ == '__main__':
    main(sys.argv[1:])
