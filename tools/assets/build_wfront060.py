"""0.60: a weapon passes behind or in front of the character as in the client. The character is one flat
picture per frame, and the weapon was drawn either behind all of it or over all of it (its depth >= 0.15): during the
attacks it went over the head and the body. Now every weapon attack (the '<sid>_x' sheets: anim10R..anim17R) is
rendered again with, for each frame, its FRONT LAYER = what the client paints over the weapon at that frame. It is cut
by an occluder: a huge rectangle put inside the weapon holder (client accessory 0) hides everything painted before it;
rendered once black and once white, the two pictures give the front layer and its exact alpha (a = 1 - (white - black),
colour = black / a). Its colour mask is the frame's own mask under that alpha (it is recoloured with the character).
CharSprite.draw: body, the weapon, then the front layer (an.ff). Other animations of the sheet (emotes) are copied.
0.61 (the Iop's hair during weapon blows): the head clips are frozen like build_chars20 does (frame 1 = hair,
frame 2 = short hair under a hat) — the 0.60 sheets let the Iop's two-frame head clip play, so his hair flickered
between the two every frame. A sprite whose head clips have two frames also gets '<sid>_h_x' (the hat variant, its
other animations (eating) rendered again too, on the frames the '<sid>_x' sheet shows: found by matching).
usage: python tools/assets/build_wfront060.py [sid…]   (HAT=1: the hat variants only; HAT=0: the plain sheets only)"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import sys, os, json, struct
import numpy as np
import swflib as S, timeline as TL, stage as ST
import build_chars20 as BC
from PIL import Image

G = f'{ROOT}/game'
WORK = f'{ROOT}/work/wfront061'
Z = 4.8
RECT_ID = 64999
SLOT = {0: 0, 1: 1, 2: 2, 3: 3}


def rect_shape(cid, rgb, R=300000, SEG=10):
    """DefineShape: a solid square of side 2R twips centred on 0 (each side in SEG edges: an edge is 17 bits at most)"""
    body = struct.pack('<H', cid) + S.write_rect((-R, R, -R, R)) + bytes([1, 0x00, *rgb, 0])   # 1 solid fill, 0 lines
    w = S.BitWriter(); w.ub(1, 4); w.ub(0, 4)   # NumFillBits 1, NumLineBits 0
    n = S.nbits_s(-R, -R); w.ub(0, 1); w.ub(0, 1); w.ub(0, 1); w.ub(1, 1); w.ub(0, 1); w.ub(1, 1); w.ub(n, 5); w.sb(-R, n); w.sb(-R, n); w.ub(1, 1)
    step = 2 * R // SEG
    for vert, sgn in ((0, 1), (1, 1), (0, -1), (1, -1)):
        for _ in range(SEG):
            d = sgn * step; nb = S.nbits_s(d); w.ub(1, 1); w.ub(1, 1); w.ub(nb - 2, 4); w.ub(0, 1); w.ub(vert, 1); w.sb(d, nb)
    w.ub(0, 6)
    return S.Tag(2, body + w.flush())


def occluder_patch(tl, rgb, base_patch):
    holders = {sid for sid, (idx, d) in tl.acc.items() if idx == 0}
    shape = rect_shape(RECT_ID, rgb)
    def patch(t):
        t = base_patch(t)
        if t.code == S.T_SPRITE and t.sprite_id in holders:
            sub = list(t.sub); i = next((k for k, x in enumerate(sub) if x.code == S.T_SHOWFRAME), len(sub))
            sub.insert(i, S.make_place2(999, char=RECT_ID, matrix=[1.0, 0.0, 0.0, 1.0, 0.0, 0.0]))
            nt = S.Tag(S.T_SPRITE, t.data[:4], sub); nt.sprite_id = t.sprite_id; nt.frames = t.frames
            return nt
        return t
    return patch, shape, holders


def render_pass(src, jobs, wd, tl, zone=None, occ=None, hat=False, heads=()):
    base = BC.make_patch(tl, zone, hat, heads)
    if occ is None: return ST.stage_render(src, jobs, wd, holds=True, tagpatch=base, prune=False)
    patch, shape, holders = occluder_patch(tl, occ, base)
    # the rectangle's DefineShape goes in before every sprite (an extra file made from the source with it)
    sw = S.read_swf(src); tags = list(sw['tags']); first = next(k for k, x in enumerate(tags) if x.code == S.T_SPRITE)
    tags.insert(first, shape); p = f'{wd}_src.swf'; os.makedirs(os.path.dirname(p), exist_ok=True)
    S.write_swf(dict(sw, tags=tags), p)
    return ST.stage_render(p, jobs, wd, holds=True, tagpatch=patch, prune=False)


def two_heads(sid):   # (0.64: any change under a hat: two-frame heads or 'Cheveux' clips, BC.hat_differs)
    return BC.hat_differs(f'{BC.RAW}/{sid}.swf')


def build(sid, out_dir=f'{G}/assets/chars', hat=False, spr=None):
    SPR = spr or json.load(open(f'{G}/data/sprites.json')); key = f'{sid}_h_x' if hat else f'{sid}_x'; old = SPR['chars'][f'{sid}_x']
    src = f'{BC.RAW}/{sid}.swf'; sw = S.read_swf(src); tl = TL.Timeline(sw); ex = S.exports(sw['tags'])
    heads = BC.head_ids(sw); wd = f'{WORK}/{key}'
    wanims = [a for a, v in old['anims'].items() if any(x[0] == 0 for al in (v.get('anc') or []) for x in al) and a in ex]
    jobs = []
    for a in wanims:
        fr = list(range(tl.eff_frames(ex[a])))
        jobs.append(dict(key=a, sym=a, zoom=Z, frames=fr, bounds=tl.bounds(ex[a], frames=fr)))   # (the unpatched bounds: the occluder must not grow the picture)
    P = {z: render_pass(src, jobs, f'{wd}/z{z}', tl, zone=z, hat=hat, heads=heads) for z in (0, 1, 2, 3)}
    OB = render_pass(src, jobs, f'{wd}/ob', tl, zone=0, occ=(0, 0, 0), hat=hat, heads=heads)
    OW = render_pass(src, jobs, f'{wd}/ow', tl, zone=0, occ=(255, 255, 255), hat=hat, heads=heads)
    items, meta_f, meta_ff = [], {}, {}
    for job in jobs:
        a = job['key']; o = P[0][a]['meta']['origin']; meta_f[a] = []; meta_ff[a] = []
        for n, fi in enumerate(job['frames']):
            im = P[0][a]['imgs'][n] if n < len(P[0][a]['imgs']) else None
            if im is None or not im.getbbox(): meta_f[a].append(None); meta_ff[a].append(None); continue
            bb = im.getbbox(); b0 = np.asarray(im).astype(np.int16)
            ch = []
            for z in (1, 2, 3):
                iz = P[z][a]['imgs'][n] if n < len(P[z][a]['imgs']) else None
                ch.append(np.clip((np.asarray(iz).astype(np.int16)[:, :, :3] - b0[:, :, :3]).mean(axis=2), 0, 255) if iz is not None else np.zeros(b0.shape[:2]))
            mask = np.stack(ch, axis=2).astype(np.uint8)
            items.append(((a, n, 'b'), im.crop(bb), Image.fromarray(mask).crop(bb))); meta_f[a].append((o[0] - bb[0], o[1] - bb[1]))
            ib = OB[a]['imgs'][n] if n < len(OB[a]['imgs']) else None; iw = OW[a]['imgs'][n] if n < len(OW[a]['imgs']) else None
            if ib is None or iw is None: meta_ff[a].append(None); continue
            B = np.asarray(ib).astype(np.float32); Wt = np.asarray(iw).astype(np.float32)
            cover = (B[:, :, 3] > 250) & (Wt[:, :, 3] > 250)
            al = np.clip(1 - (Wt[:, :, :3] - B[:, :, :3]).mean(axis=2) / 255, 0, 1) * cover
            al = np.minimum(al, b0[:, :, 3].astype(np.float32) / 255)   # (inside the character only: a flash frame whitens the occluder too)
            al[al < 0.02] = 0
            if al.max() <= 0: meta_ff[a].append(None); continue
            rgb = np.clip(B[:, :, :3] / np.maximum(al[:, :, None], 1e-3), 0, 255)
            fimg = Image.fromarray(np.dstack([rgb, al * 255]).astype(np.uint8), 'RGBA'); fb = fimg.getbbox()
            if not fb: meta_ff[a].append(None); continue
            fmask = Image.fromarray((mask.astype(np.float32) * (al[:, :, None] > 0.5)).astype(np.uint8))
            items.append(((a, n, 'f'), fimg.crop(fb), fmask.crop(fb))); meta_ff[a].append((o[0] - fb[0], o[1] - fb[1]))
    # the sheet's other animations (emotes…) come from the old atlas as they are; in the hat variant they are rendered
    # again with the short hair, on the very frames the plain sheet shows (each plain frame matched to a client frame)
    oi = Image.open(f'{G}/assets/chars/{sid}_x.webp').convert('RGBA'); om = Image.open(f'{G}/assets/chars/{sid}_x_m.webp').convert('RGB') if not old.get('nomask') else None
    keep = {a: v for a, v in old['anims'].items() if a not in wanims}
    if hat and keep:
        low = {k_.lower(): k_ for k_ in ex}; ks = {a: low[a.lower()] for a in keep if a.lower() in low}
        mjobs = [dict(key=a, sym=s_, zoom=Z, n=min(80, tl.eff_frames(ex[s_]))) for a, s_ in ks.items()]
        res = render_pass(src, mjobs, f'{wd}/km', tl, zone=0, hat=False, heads=heads)
        mres = BC.match_frames(oi, {'anims': {a: keep[a] for a in ks}}, res)
        kidx = {a: [(i if i is not None and i >= 0 else 0) for i, _, _ in (mres.get(a) or [])] for a in ks}
        print(key, 'kept animations matched (frames, unmatched)', {a: (len(v), sum(1 for i, _, _ in (mres.get(a) or []) if i is None)) for a, v in kidx.items()}, flush=True)
        kjobs = [dict(key=a, sym=ks[a], zoom=Z, frames=sorted(set(kidx[a]))) for a in ks if kidx[a]]
        KP = {z: render_pass(src, kjobs, f'{wd}/k{z}', tl, zone=z, hat=True, heads=heads) for z in (0, 1, 2, 3)}
        for job in kjobs:
            a = job['key']; o = KP[0][a]['meta']['origin']; at = {fi: n for n, fi in enumerate(job['frames'])}; F = []
            for j, fi in enumerate(kidx[a]):
                im = KP[0][a]['imgs'][at[fi]]; bb = im.getbbox() if im is not None else None
                if not bb: F.append(None); continue
                b0 = np.asarray(im).astype(np.int16)
                ch = [np.clip((np.asarray(KP[z][a]['imgs'][at[fi]]).astype(np.int16)[:, :, :3] - b0[:, :, :3]).mean(axis=2), 0, 255) for z in (1, 2, 3)]
                items.append(((a, j, 'k'), im.crop(bb), Image.fromarray(np.stack(ch, axis=2).astype(np.uint8)).crop(bb))); F.append((o[0] - bb[0], o[1] - bb[1]))
            keep[a] = dict(keep[a], _off=F)
    for a, v in keep.items():
        if '_off' in v: continue
        for n, (x, y, w, h, ox, oy) in enumerate(v['f']):
            items.append(((a, n, 'k'), oi.crop((x, y, x + w, y + h)), om.crop((x, y, x + w, y + h)) if om else Image.new('RGB', (w, h))))
    atlas, pos = ST.pack([(k, b) for k, b, m in items], maxw=4096)
    ma = Image.new('RGB', atlas.size)
    for k, b, m in items: ma.paste(m, pos[k][:2])
    os.makedirs(out_dir, exist_ok=True); atlas.save(f'{out_dir}/{key}.webp', 'WEBP', quality=90, method=6); ma.save(f'{out_dir}/{key}_m.webp', 'WEBP', **BC.MASK_WEBP)   # (0.91: lossless masks)
    meta = dict(old); meta.update(w=atlas.width, h=atlas.height, anims={}); meta.pop('nomask', None)
    k = Z / 20.0
    for job in jobs:
        a = job['key']; F, FF, A = [], [], []
        anc = tl.anchors(ex[a], frames=job['frames'])
        for n in range(len(job['frames'])):
            if meta_f[a][n] is None: continue
            x, y, w, h = pos[(a, n, 'b')]; ox, oy = meta_f[a][n]; F.append([x, y, w, h, round(ox, 2), round(oy, 2)])
            if meta_ff[a][n] is not None: x, y, w, h = pos[(a, n, 'f')]; fx, fy = meta_ff[a][n]; FF.append([x, y, w, h, round(fx, 2), round(fy, 2)])
            else: FF.append(None)
            A.append([[SLOT[i], d, *[round(v * k, 4) for v in m[:4]], round(m[4] * k, 3), round(m[5] * k, 3), round(o_, 3)] for i, d, m, o_ in anc[n] if i in SLOT])
        meta['anims'][a] = dict(old['anims'][a], f=F, ff=FF, anc=A)
    for a, v in keep.items():
        if '_off' in v:   # (rendered again: its own offsets; a frame with nothing drawn keeps the one before)
            F = []
            for n, off in enumerate(v['_off']):
                F.append([*pos[(a, n, 'k')], round(off[0], 2), round(off[1], 2)] if off else (F[-1] if F else [0, 0, 1, 1, 0, 0]))
            meta['anims'][a] = dict({k_: x_ for k_, x_ in v.items() if k_ != '_off'}, f=F)
        else: meta['anims'][a] = dict(v, f=[[*pos[(a, n, 'k')], ox, oy] for n, (x, y, w, h, ox, oy) in enumerate(v['f'])])
    print(key, atlas.size, {a: (len(meta['anims'][a]['f']), sum(1 for x in meta['anims'][a].get('ff') or [] if x)) for a in wanims}, flush=True)
    return key, meta


if __name__ == '__main__':
    import sprio
    SPR = json.load(open(f'{G}/data/sprites.json'))
    sids = sys.argv[1:] or sorted(k[:-2] for k in SPR['chars'] if k.endswith('_x') and not k.endswith('_h_x'))
    out = {}; H = os.environ.get('HAT')
    for sid in sids:
        for hat in ([False] if H == '0' else []) + ([True] if H == '1' else []) + ([False, True] if H is None else []):
            if hat and not two_heads(sid): continue
            try: k, m = build(sid, hat=hat, spr=SPR); out[k] = m; SPR['chars'][k] = m   # (the hat variant reads the plain sheet just made)
            except Exception as e:
                import traceback; traceback.print_exc(); print('FAIL', sid, hat, e, flush=True)
    sprio.update(lambda S_: S_['chars'].update(out)); print('done', len(out))
