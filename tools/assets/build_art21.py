"""0.21: every bestiary artwork re-rendered from its vector source (clips/artworks/big/<gfx>.swf) at A px on the
longest side (v1.9/v2.0: 360, upscaled on 2K screens = blocky edges), rendered at 2A and reduced (smooth edges).
Entries without a source (class emblems b*, the recoloured Pious p1212*/a1212_*) are kept as they are.
All sheets are repacked (assets/art/art_<n>.webp, SPR.art).  usage: python tools/assets/build_art21.py [A]"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import sys, os, json, re
import swflib as S, timeline as TL, stage as ST
from PIL import Image

G = f'{ROOT}/game'
RAW = f'{ROOT}/raw/rc/clips/artworks/big'
# 0.29: drawings whose outline is missing on part of the silhouette in the client SWF (the Larve Bleue: only ~58 % of
# its rim is outlined, the other Larvas 100 %): the rim (W px at A=520) is painted in the outline colour where it isn't
OUTLINE = {'a1563': ((1, 40, 70), 11.5, 18)}   # colour, rim width (px at A=520) like the Larve Verte's, bump-removal radius


def fix_outline(im, col, W, smooth=0):
    """0.34: the silhouette is first smoothed (an opening: the little knob on the Larve Bleue's back goes), then its rim
    is painted in the outline colour, as thick as the other Larvas' outline"""
    import numpy as np, cv2
    a = np.array(im.convert('RGBA')); al = (a[..., 3] > 128).astype(np.uint8)
    if smooth:
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * smooth + 1, 2 * smooth + 1))
        keep = cv2.morphologyEx(np.pad(al, smooth + 2), cv2.MORPH_OPEN, k)[smooth + 2:-smooth - 2, smooth + 2:-smooth - 2]
        a[..., 3] = (a[..., 3] * cv2.GaussianBlur(keep.astype(np.float32), (0, 0), 0.8)).astype(np.uint8); al = keep
    if smooth:   # bumps on the top contour (the knob on the back): the top edge follows its own median line
        H, Wd = al.shape; top = np.array([np.argmax(al[:, x]) if al[:, x].any() else H for x in range(Wd)], float)
        r = smooth * 3; med = top.copy(); xs = np.arange(Wd)
        for x in range(Wd):   # a local line fitted on the contour, the points above it rejected (twice): the bump's not in it
            lo, hi = max(0, x - r), min(Wd, x + r + 1); X, Y = xs[lo:hi], top[lo:hi]; ok = Y < H
            for _ in range(3):
                if ok.sum() < 4: break
                c = np.polyfit(X[ok], Y[ok], 2); f = np.polyval(c, X); ok = ok & (Y >= f - 2)
            if ok.sum() >= 4: med[x] = np.polyval(c, x)
        cut = np.zeros(Wd, bool)
        for x in range(Wd):
            if top[x] < H and top[x] < med[x] - 2: a[:int(round(med[x])), x, 3] = 0; al[:int(round(med[x])), x] = 0; cut[x] = True
        if cut.any():   # the cut edge anti-aliased, and the knob's dark base under it painted over with the body
            sm = cv2.GaussianBlur(al.astype(np.float32), (0, 0), 1.0); a[..., 3] = np.minimum(a[..., 3], (np.clip(sm * 1.6 - 0.3, 0, 1) * 255).astype(np.uint8))
            cols = np.convolve(cut.astype(float), np.ones(13), 'same') > 0
            d0 = cv2.distanceTransform(np.pad(al, 1), cv2.DIST_L2, 5)[1:-1, 1:-1]; lum0 = a[..., :3].astype(float).mean(2)
            m = ((d0 > 3) & (d0 < W * 2 + 8) & (lum0 < 70) & cols[None, :]).astype(np.uint8)
            if m.any(): a[..., :3] = cv2.inpaint(np.ascontiguousarray(a[..., :3]), cv2.dilate(m, np.ones((3, 3), np.uint8)) * 255, 9, cv2.INPAINT_TELEA)
    d = cv2.distanceTransform(np.pad(al, 1), cv2.DIST_L2, 5)[1:-1, 1:-1] * max(im.size) / 520
    if smooth:   # dark knobs drawn just inside the edge (deeper than the rim): painted over with the body around them
        lum0 = a[..., :3].astype(float).mean(2); knob = ((lum0 < 70) & (d > W + 1) & (d < W + smooth * 2)).astype(np.uint8)
        n, lab, st, _ = cv2.connectedComponentsWithStats(knob)
        m = np.zeros_like(knob)
        for i in range(1, n):
            if st[i, cv2.CC_STAT_AREA] < 900: m[lab == i] = 1
        if m.any():
            m = cv2.dilate(m, np.ones((5, 5), np.uint8)); a[..., :3] = cv2.inpaint(np.ascontiguousarray(a[..., :3]), m * 255, 7, cv2.INPAINT_TELEA)
    lum = a[..., :3].astype(float).mean(2)
    k = (np.clip(W - d, 0, 1) * (lum > 60))[..., None]
    a[..., :3] = (a[..., :3] * (1 - k) + np.array(col) * k).astype(np.uint8)
    return Image.fromarray(a)


def size1(path):
    sw = S.read_swf(path); sw['tags'].append(ST.root_sprite(sw)); tl = TL.Timeline(sw)
    b = tl.bounds(ST.ROOT_ID, frames=range(1)); return max(b[1] - b[0], b[3] - b[2]) / 20.0


def main(A=520, extra=()):
    SPR = json.load(open(f'{G}/data/sprites.json')); F = dict(SPR['art']['f'])
    for g in extra: F.setdefault(f'a{g}', None)   # 0.27: new artworks (e.g. +1245,1258)
    sheets = {}
    old = lambda k: (sheets.setdefault(F[k][0], Image.open(f'{G}/assets/art/art_{F[k][0]}.webp').convert('RGBA'))
                     .crop((F[k][1], F[k][2], F[k][1] + F[k][3], F[k][2] + F[k][4])))
    redo = [k for k in F if re.fullmatch(r'a\d+', k) and os.path.exists(f'{RAW}/{k[1:]}.swf') and (not extra or os.environ.get('ALL') or int(k[1:]) in extra)]   # (0.50: with +gfx, only the new ones are rendered, ALL=1 for every one)
    jobs = []
    for k in redo:
        p = f'{RAW}/{k[1:]}.swf'; s = size1(p)
        if s > 0: jobs.append((p, [dict(key=k, root=True, zoom=A * 2 / s, frames=[0], n=1)]))
    res = {}
    for i in range(0, len(jobs), 40):   # FFDec in batches
        res.update(ST.stage_batch(jobs[i:i + 40], f'{ROOT}/work/art21/{i}', prune=True)); print('rendered', min(i + 40, len(jobs)), '/', len(jobs), flush=True)
    # 2nd pass: some artworks declare a frame much larger than their drawing (the Larvas: 170 px out of 1045), so the
    # drawing came out small and blocky. Measure the drawn box and render again, framed on it, at the right zoom.
    again = []
    for p, js in jobs:
        j = js[0]; r = res.get(j['key']); im = r['imgs'][0] if r and r['imgs'] else None
        if im is None or not im.getbbox(): continue
        x0, y0, x1, y1 = im.getbbox(); big = max(x1 - x0, y1 - y0)
        if big >= A * 2 * 0.9: continue
        ox, oy = r['meta']['origin']; k = j['zoom'] / 20.0; pad = 4
        bt = ((x0 - pad - ox) / k, (x1 + pad - ox) / k, (y0 - pad - oy) / k, (y1 + pad - oy) / k)
        again.append((p, [dict(j, zoom=j['zoom'] * A * 2 / big, bounds=bt)]))
    print('reframed', len(again), flush=True)
    for i in range(0, len(again), 40):
        res.update(ST.stage_batch(again[i:i + 40], f'{ROOT}/work/art21b/{i}', prune=True)); print('re-rendered', min(i + 40, len(again)), flush=True)
    items = []
    for k in F:
        r = res.get(k); im = r['imgs'][0] if r and r['imgs'] else None
        if im is not None and im.getbbox():
            im = im.crop(im.getbbox()); s = A / max(im.size)
            im = im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS)
            if k in OUTLINE: im = fix_outline(im, *OUTLINE[k])
        else:
            if k in redo: print('kept old', k)
            im = old(k)
        items.append((k, im))
    # pack into as few 4096 sheets as needed
    for f in os.listdir(f'{G}/assets/art'):
        if f.startswith('art_'): os.remove(f'{G}/assets/art/{f}')
    NF, n, rest = {}, 0, items
    while rest:
        atlas, pos = ST.pack(rest, maxw=4096)
        fit = [(k, im) for k, im in rest if k in pos and pos[k][1] + pos[k][3] <= 4096]
        if atlas.height > 4096:
            atlas = atlas.crop((0, 0, atlas.width, 4096))
        atlas.save(f'{G}/assets/art/art_{n}.webp', 'WEBP', quality=88, method=6)
        for k, _ in fit: x, y, w, h = pos[k]; NF[k] = [n, x, y, w, h]
        print('sheet', n, atlas.size, len(fit), os.path.getsize(f'{G}/assets/art/art_{n}.webp'), flush=True)
        rest = [(k, im) for k, im in rest if k not in NF]; n += 1
    import sprio
    sprio.update(lambda S: S.__setitem__('art', {'sheets': n, 'f': NF}))


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('+')]; ext = [int(g) for a in sys.argv[1:] if a.startswith('+') for g in a[1:].split(',')]
    main(int(args[0]) if args else 520, ext)   # usage: build_art21.py [A] [+gfx,gfx]
