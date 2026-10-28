"""v2.0 worlds re-rendered natively from the client's vector map graphics at RES pixels per Dofus pixel (v1.9: 1.5).
The map blocks of the existing worlds were recovered by matching (findworld.py -> work/world_<name>.json); the new
zone is given here. Slots without a map keep the old picture (existing worlds) or the sea (new islands).
Writes assets/worlds/<name>_<tx>_<ty>.webp tiles (4096 px), <name>_mini.webp and SPR.worlds[name]."""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import sys, os, json, math
import maprender as MR
from PIL import Image, ImageFilter
import numpy as np

G = f'{ROOT}/game'
RES = float(os.environ.get('RES', '2.5'))
TILE = 4096
Q = int(os.environ.get('Q', '80'))
Image.MAX_IMAGE_PIXELS = None

NEW = {
    # L'île des naufragés (Otomaï): the pirates' island in the middle of the sea
    # (the island itself: 4 x 5 maps, the two missing bottom corners are filled with its own sea)
    'naufrages': dict(x0=-45, y0=-2, cols=4, rows=5, sas=[451], music=136),
    # 0.50: the Champs de Bonta (the fields of Les Champs de Cania next to Bonta), the Montagne des Koalaks (Canyon sauvage,
    # Forêt de Kaliptus, Cimetière primitif, Vallée de la Morh'Kitu: where the Koalaks live), L'île de Grobe (Pandala's
    # ghost island, its two missing corners filled with its own sea)
    'bonta': dict(x0=-25, y0=-46, cols=6, rows=6, sas=[68, 279], music=116),
    'koalak': dict(x0=-14, y0=9, cols=6, rows=6, sas=[253, 234, 230, 275, 231, 235], music=127),
    'grobe': dict(x0=31, y0=-54, cols=5, rows=5, sas=[152, 476], music=123),
}


def new_block(cfg):
    I = MR.infos(); pos = {}
    for m, v in I.items():
        if v.get('sa') in cfg['sas'] and v.get('outdoor') and v['x'] is not None: pos.setdefault((v['x'], v['y']), m)
    return [[pos.get((cfg['x0'] + i, cfg['y0'] + j)) for i in range(cfg['cols'])] for j in range(cfg['rows'])]


def old_world(name, W, H):
    SPR = json.load(open(f'{ROOT}/work/v19_worlds/sprites.json')); w = SPR['worlds'].get(name)   # the v1.9 picture
    if not w: return None, None
    res = w.get('res', 1.5); T = w['tile']
    full = Image.new('RGB', (int(round(w['w'] * res)), int(round(w['h'] * res))))
    for tx, ty, fn in w['tiles']:
        p = f'{ROOT}/work/v19_worlds/{fn}'
        full.paste(Image.open(p).convert('RGB'), (int(round(tx * T * res)), int(round(ty * T * res))))
    return full.resize((W, H), Image.BICUBIC), w


def sea_fill(maps, W, H, res):
    """the sea around an island: the background picture of its maps (their own sea), tiled"""
    I = MR.infos(); bgs = {}
    for row in maps:
        for m in row:
            if m and I[m].get('bg'): bgs[I[m]['bg']] = bgs.get(I[m]['bg'], 0) + 1
    out = Image.new('RGBA', (W, H), (40, 120, 160, 255))
    if not bgs: return out
    bg = max(bgs, key=bgs.get)
    MR.ensure_symbols({('g', bg, 0, 0, 0)}, res)
    s = MR.sym_img(MR.sym_key('g', bg, 0, 0, 0, res)); o = json.load(open(f'{MR.CACHE}/meta.json')).get(MR.sym_key('g', bg, 0, 0, 0, res))
    if s is None: return out
    sw, sh = int(MR.MAPW * res), int(MR.MAPH * res)
    for y in range(0, H, sh):
        for x in range(0, W, sw): out.alpha_composite(s, (x - int(o[0]) if o else x, y - int(o[1]) if o else y))
    return out


def compose(maps, img):
    """the whole world at once, like one big map: every map's ground in its own window, then the flat objects (o1) of
    all the maps, then the standing ones (o2) in world depth order, so trees and walls spill over the map edges
    instead of being cut at them"""
    meta = json.load(open(f'{MR.CACHE}/meta.json')) if os.path.exists(f'{MR.CACHE}/meta.json') else {}
    under = np.array(img)   # (0.32: what lies under the maps: the old picture, or nothing)
    for j, row in enumerate(maps):   # backgrounds, inside their window
        for i, m in enumerate(row):
            if not m: continue
            t = MR.render_map(m, RES, layers=('bg',))
            img.alpha_composite(t, (int(round(i * MR.MAPW * RES)), int(round(j * MR.MAPH * RES))))
    M = 40   # ground cells: their half cells past the window edges are kept (no seams between maps)
    cover = Image.new('L', img.size)   # 0.32: where some map really has ground (bg picture or cells)
    for j, row in enumerate(maps):
        for i, m in enumerate(row):
            if not m: continue
            t = seal(MR.render_map(m, RES, margin=M, layers=('cells',)))
            x, y = int(round((i * MR.MAPW - M) * RES)), int(round((j * MR.MAPH - M) * RES))
            img.alpha_composite(t, (max(0, x), max(0, y)), (max(0, -x), max(0, -y)))
            a = t.getchannel('A').crop((max(0, -x), max(0, -y), t.width, t.height)); cover.paste(Image.fromarray(np.maximum(np.array(cover.crop((max(0, x), max(0, y), max(0, x) + a.width, max(0, y) + a.height))), np.array(a))), (max(0, x), max(0, y)))
    # 0.38: then each map's own cells (0.51: and background) again, inside its window only, with a short soft edge (FE Dofus px across the
    # window line): the half cells a neighbour pushed into this window (the saw teeth) are covered, and two different
    # grounds meet on a straight, softened line instead of interlocking diamonds
    FE = 56; VW = None   # (VW: where the open-water slots lie, for the flat objects below; 0.53: FE 24 -> 56 Dofus px, wavy)
    for j, row in enumerate(maps):
        for i, m in enumerate(row):
            if not m: continue
            t = seal(MR.render_map(m, RES, margin=M, layers=('bg', 'cells') if m in BG2 else ('cells',)))   # (0.51, BG2: a map of water redraws its water too: it covers the teeth; 0.52: only those, an ordinary background drawn again over the cells showed through their slits as thin lines)
            if m < 0:   # (0.52: a slot of open water next to the land: a wider fade along a wavy line, not a straight cut)
                va = vramp(t.width, t.height, i, j, maps, M, ); ta = np.array(t); ta[..., 3] = (ta[..., 3] * va).astype(np.uint8); t = Image.fromarray(ta)
                if VW is None: VW = np.zeros((img.height, img.width), np.uint8)
                x_, y_ = int(round((i * MR.MAPW - M) * RES)), int(round((j * MR.MAPH - M) * RES)); sx, sy = max(0, -x_), max(0, -y_)
                reg = VW[max(0, y_):y_ + t.height, max(0, x_):x_ + t.width]
                np.maximum(reg, (va[sy:sy + reg.shape[0], sx:sx + reg.shape[1]] * 255).astype(np.uint8), out=reg)
            else:
                ta = np.array(t); ta[..., 3] = (ta[..., 3] * seam_alpha(t.width, t.height, i, j, len(row), len(maps), M, FE)).astype(np.uint8); t = Image.fromarray(ta)
            x, y = int(round((i * MR.MAPW - M) * RES)), int(round((j * MR.MAPH - M) * RES))
            img.alpha_composite(t, (max(0, x), max(0, y)), (max(0, -x), max(0, -y)))
    for j, row in enumerate(maps):   # (a map's background picture counts as ground too)
        for i, m in enumerate(row):
            if not m: continue
            t = MR.render_map(m, RES, layers=('bg',)); a = t.getchannel('A'); x, y = int(round(i * MR.MAPW * RES)), int(round(j * MR.MAPH * RES))
            cover.paste(Image.fromarray(np.maximum(np.array(cover.crop((x, y, x + a.width, y + a.height))), np.array(a))), (x, y))
    img = fix_ground(img, cover, maps, under)
    img = blend_open_sea(img, VW)
    objs = []
    import decormask087 as DM; dm = DM.Mask(img.width, img.height, RES)   # (0.87: the tall scenery, for the areas drawn under it)
    for j, row in enumerate(maps):
        for i, m in enumerate(row):
            if not m: continue
            for n, (layer, x, y, k) in enumerate(MR.objects_of(m, RES)):
                objs.append((layer, j * MR.MAPH + y, i * MR.MAPW + x, n, k))
    objs.sort(key=lambda o: (o[0], o[1] if o[0] == 2 else 0, o[2] if o[0] == 2 else 0, o[3]) if o[0] == 2 else (1, 0, 0, 0))
    W, H = img.size
    G0 = np.asarray(img.convert('RGB').resize((max(1, W // 8), max(1, H // 8)), Image.BOX)).astype(np.int16)   # (the ground before the objects)
    grass = (G0[..., 1] > G0[..., 0] + 20) & (G0[..., 1] > G0[..., 2] + 80) & (G0[..., 2] < 110)   # (lime grass; not the pale shallows)
    for layer, gy, gx, n, k in objs:
        o = meta.get(k)
        if not o: continue
        if int(k[1:].split('_')[0]) in EDGE_DECALS:   # (0.52: a grass-edge decal with no grass next to it: left out)
            cx, cy, rx, ry = int(gx * RES / 8), int(gy * RES / 8), int(40 * RES / 8), int(22 * RES / 8)
            if grass[max(0, cy - ry):cy + ry, max(0, cx - rx):cx + rx].mean() < 0.12 if grass[max(0, cy - ry):cy + ry, max(0, cx - rx):cx + rx].size else True: continue
        s = MR.sym_img(k)
        if s is None: continue
        if k[0] == 'o' and int(k[1:].split('_')[0]) in FADE_TOP: s = fade_top(s, FADE_TOP[int(k[1:].split('_')[0])])
        if k[0] == 'o' and int(k[1:].split('_')[0]) in FEATHER: s = feather(s, FEATHER[int(k[1:].split('_')[0])])
        px = int(round(gx * RES - o[0])); py = int(round(gy * RES - o[1]))
        if px >= W or py >= H or px + s.width <= 0 or py + s.height <= 0: continue
        if layer == 1 and VW is not None:   # (0.52: a flat object reaching into an open-water slot fades under its water)
            reg = VW[max(0, py):py + s.height, max(0, px):px + s.width]
            if reg.any():
                a = np.array(s); sub = a[max(0, -py):max(0, -py) + reg.shape[0], max(0, -px):max(0, -px) + reg.shape[1]]
                sub[..., 3] = (sub[..., 3] * (1 - reg / 255.0)).astype(np.uint8); s = Image.fromarray(a)
        if layer == 2: dm.add(s, px, py, o[1])
        img.alpha_composite(s, (max(0, px), max(0, py)), (max(0, -px), max(0, -py)))
    dm.save(CUR_NAME)
    return img


def seal(t):
    """0.51: the hairline gaps of a map's ground (between two cells' diamonds, and the slits some ground pictures have
    down their middle) showed what lay under the ground (black, the old picture, water: thin lines all over the maps):
    closed with the colour around them"""
    import cv2
    a = np.array(t); al = a[..., 3]; k = int(2 * RES) | 1
    closed = cv2.morphologyEx(al, cv2.MORPH_CLOSE, np.ones((k, k), np.uint8))
    g = closed > al
    if not g.any(): return t
    w = (al > 250).astype(np.float32)
    num = cv2.GaussianBlur(a[..., :3].astype(np.float32) * w[..., None], (0, 0), RES); den = cv2.GaussianBlur(w, (0, 0), RES)
    ok = g & (den > 0.02)
    c = num[ok] / den[ok][:, None]; o = al[ok].astype(np.float32)[:, None] / 255; n = closed[ok].astype(np.float32)[:, None] / 255
    a[ok, :3] = ((a[ok, :3] * o + c * (n - o)) / n).clip(0, 255).astype(np.uint8); a[ok, 3] = closed[ok]
    return Image.fromarray(a)


def edge_inherit():
    """0.52: the cells on a map's window border are half outside it: the client never shows them next to the next map, so
    the map makers left odd grounds there (a grass cell on a beach, a lone dark cell…) that drew green chevrons and wedges
    along the seams. Each one takes the ground of its inward neighbours (the map's own ground, continued)"""
    real = MR.cells_of; memo = {}
    def cells_of(mid):
        if mid is None or mid <= 0: return real(mid)
        if mid in memo: return memo[mid]
        d = real(mid)
        if not d: return d
        cells, w, h = d; xy = MR.cell_xy([dict(c, level=7) for c in cells], w)
        at = {(round(x * 2), round(y * 2)): n for n, (x, y) in enumerate(xy)}
        out = list(cells); MW, MH = MR.MAPW, MR.MAPH
        for n, (x, y) in enumerate(xy):
            if not cells[n]['ground']: continue
            dirs = []
            if y <= 0.5: dirs += [(-MR.CHW, MR.CHH), (MR.CHW, MR.CHH)]
            if y >= MH - 0.5: dirs += [(-MR.CHW, -MR.CHH), (MR.CHW, -MR.CHH)]
            if x <= 0.5: dirs += [(MR.CHW, -MR.CHH), (MR.CHW, MR.CHH)]
            if x >= MW - 0.5: dirs += [(-MR.CHW, -MR.CHH), (-MR.CHW, MR.CHH)]
            if not dirs: continue
            nb = [cells[at[k]] for k in ((round((x + dx) * 2), round((y + dy) * 2)) for dx, dy in dirs) if k in at and cells[at[k]]['ground']]
            if not nb or any(c['ground'] == cells[n]['ground'] for c in nb): continue
            src = max(nb, key=lambda c: sum(1 for o in nb if o['ground'] == c['ground']))
            out[n] = dict(cells[n], ground=src['ground'], groundRot=src['groundRot'], groundFlip=src['groundFlip'], slope=src['slope'])
        memo[mid] = (out, w, h); return memo[mid]
    MR.cells_of = cells_of


CUR = None   # (the WATER config of the world being built)


def seam_wave(n, key, amp):
    """0.53: a smooth wavy offset along a seam (px at RES), the same for the two maps sharing it (seeded by the seam)"""
    import zlib
    rng = np.random.default_rng(zlib.crc32(repr(key).encode())); t = np.arange(n, dtype=np.float32) / RES; v = np.zeros(n, np.float32)
    for lam, a in ((260, 0.5), (120, 0.32), (55, 0.18)): v += a * np.sin(t / lam * 2 * np.pi + rng.uniform(0, 2 * np.pi))
    return v * amp * RES


def seam_alpha(W, H, i, j, cols, rows, M, FE, amp=12):
    """0.53: the alpha of a map's own cells drawn again in its window (second pass of compose): a cross-fade FE Dofus px wide
    across each window edge that has a neighbour, along a wavy line (+-amp px), instead of a straight 24 px one"""
    x = np.arange(W, dtype=np.float32); y = np.arange(H, dtype=np.float32); k = FE * RES
    x0, x1, y0, y1 = M * RES, (M + MR.MAPW) * RES, M * RES, (M + MR.MAPH) * RES
    wv = lambda key, n, o: seam_wave(n, key, amp)   # (two maps of a seam share its row / column: same rows, same waves)
    a = np.ones((H, W), np.float32)
    if i > 0: a = np.minimum(a, np.clip((x[None, :] - x0 + wv(('v', i, j), H, 0)[:, None]) / k + 0.5, 0, 1))
    if i < cols - 1: a = np.minimum(a, np.clip((x1 - x[None, :] - wv(('v', i + 1, j), H, 0)[:, None]) / k + 0.5, 0, 1))
    if j > 0: a = np.minimum(a, np.clip((y[:, None] - y0 + wv(('h', i, j), W, 0)[None, :]) / k + 0.5, 0, 1))
    if j < rows - 1: a = np.minimum(a, np.clip((y1 - y[:, None] - wv(('h', i, j + 1), W, 0)[None, :]) / k + 0.5, 0, 1))
    return a


def is_water(rgb):
    """water of any colour (blue, cyan, turquoise, the swamps' green), not grass, sand, earth nor snow (0..1)"""
    r, g, b = rgb[..., 0].astype(np.float32), rgb[..., 1].astype(np.float32), rgb[..., 2].astype(np.float32)
    return np.clip(np.minimum((b - r - 12) / 18, (g - r - 6) / 18), 0, 1)


def blend_open_sea(img, VW, sig=160):
    """0.53, a retouch: the open-water slots (the sea of an empty slot, VW = where they lie, soft) take the colour of the
    real maps' water: the local one next to it (normalized convolution, 40 then sig Dofus px), the mean of all of it
    farther away; only the low frequencies move (the waves stay) and the change follows VW's soft alpha, so no edge
    (0.53 first evened the shades along each seam in strips: their ends and the seam itself made straight steps)"""
    import cv2
    if VW is None: return img
    A = np.array(img.convert('RGB')).astype(np.float32); H, W = A.shape[:2]; q = int(round(4 * RES)); w, h = W // q, H // q
    lo = cv2.GaussianBlur(cv2.resize(A, (w, h), interpolation=cv2.INTER_AREA), (0, 0), 2)
    vw = cv2.resize(VW.astype(np.float32) / 255, (w, h), interpolation=cv2.INTER_AREA)
    wat = is_water(lo); K = wat * (vw < 0.02)   # (the real maps' water)
    if K.sum() < 50: return img
    nc = lambda s_: (cv2.GaussianBlur(lo * K[..., None], (0, 0), s_), cv2.GaussianBlur(K, (0, 0), s_))
    (n1, d1), (n2, d2) = nc(10), nc(sig / 4)
    ext = (n1 + 0.2 * n2) / np.maximum(d1 + 0.2 * d2, 1e-4)[..., None]
    gm = np.median(lo[K > 0.5], 0) if (K > 0.5).sum() > 50 else (lo * K[..., None]).sum((0, 1)) / K.sum()
    wg = np.clip(d2 / 0.3, 0, 1)[..., None]
    corr = cv2.GaussianBlur((ext * wg + gm * (1 - wg) - lo) * (vw * wat)[..., None], (0, 0), 1.5)
    A += cv2.resize(corr, (W, H), interpolation=cv2.INTER_CUBIC)
    print('open sea blended', round(float((vw > 0.5).mean()) * 100, 1), '%', flush=True)
    return Image.fromarray(np.clip(A, 0, 255).astype(np.uint8)).convert('RGBA')


def vramp(W, H, i, j, maps, M, fe=70, wob=45):
    """0.52: the alpha of an open-water slot's render (margin M): 1 inside; along each window edge that faces land, the
    coast is one wavy line (a few sines along the edge, seeded by the slot) reaching 2 to 38 Dofus px over the land,
    feathered over fe px (wob: the waves' amplitude, at most what the margin allows)"""
    import cv2
    k = 1 / RES; w, h = int(W * k), int(H * k)
    rng = np.random.default_rng(97 * j + i + 7)
    def wave(n):   # (a smooth line along an edge, in -1..1)
        t = np.arange(n, dtype=np.float32); v = np.zeros(n, np.float32)
        for lam, amp in ((330, 0.55), (150, 0.3), (70, 0.15)): v += amp * np.sin(t / lam * 2 * np.pi + rng.uniform(0, 2 * np.pi))
        return v
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32); x0, x1, y0, y1 = M, M + MR.MAPW, M, M + MR.MAPH
    reach = lambda v: 20 + min(wob, M - 2 - 20) * v   # (how far the water goes over the land there)
    big = 1e4
    land = lambda di, dj: 0 <= j + dj < len(maps) and 0 <= i + di < len(maps[0]) and (maps[j + dj][i + di] or 0) > 0
    wy, wx = wave(h)[:, None], wave(w)[None, :]
    d = np.minimum.reduce([xx - x0 + reach(wy) if land(-1, 0) else np.full_like(xx, big), x1 - xx + reach(-wy) if land(1, 0) else np.full_like(xx, big),
                           yy - y0 + reach(wx) if land(0, -1) else np.full_like(xx, big), y1 - yy + reach(-wx) if land(0, 1) else np.full_like(xx, big)])
    return cv2.resize(np.clip(d / fe, 0, 1), (W, H), interpolation=cv2.INTER_LINEAR)   # (0 at the reach, within the margin: no edge where the render stops)


def fix_ground(img, cover, maps, under=None):
    """0.32, before the objects are drawn: (1) the holes where no map has ground (they showed the dark background or an
    old picture) are filled from the ground around them (inpainting on a reduced picture, then feathered in);
    (2) where two neighbouring maps don't have the same ground (sand / sea…), the interlocking half cells of their
    edges made saw teeth: the seam is cross-faded (blurred across, only where the two sides really differ)"""
    import cv2
    W, H = img.size; A = np.array(img); cov = np.array(cover)
    slot = np.zeros((H, W), bool)   # only inside the slots that have a map (the others keep their old picture)
    mw, mh = MR.MAPW * RES, MR.MAPH * RES
    for j, row in enumerate(maps):
        for i, m in enumerate(row):
            if m or FILL_EMPTY: slot[int(j * mh):int((j + 1) * mh), int(i * mw):int((i + 1) * mw)] = True
    if under is not None:   # the edges of the ground fade into what lies under it (no saw teeth against a dark floor)
        has = (under[..., 3] > 0) & slot
        cs = np.clip(cv2.GaussianBlur(cov.astype(np.float32) / 255, (0, 0), 5 * RES) * 1.25, 0, 1)
        m = has & (cov > 0) & (cs < 0.999)
        if m.any():
            w = cs[m][:, None]; A[m, :3] = (A[m, :3] * w + under[m, :3] * (1 - w)).astype(np.uint8)
            print('ground edges faded', round(m.mean() * 100, 2), '%', flush=True)
    else: has = np.zeros((H, W), bool)
    hole = (cov < 128) & slot & ~has   # nothing at all there: filled from the ground around
    if hole.mean() > 0.0005:
        f = 8; sw, sh = W // f, H // f
        small = cv2.resize(A[..., :3], (sw, sh), interpolation=cv2.INTER_AREA)
        hm = cv2.resize(hole.astype(np.uint8) * 255, (sw, sh), interpolation=cv2.INTER_AREA) > 60
        filled = cv2.inpaint(small, hm.astype(np.uint8) * 255, 6, cv2.INPAINT_TELEA)
        # texture: a patch of this world's real ground that looks like the ground around the holes, mirrored into a
        # seamless tile; its fine detail (patch / its blur) modulates the inpainted colour, so the holes get ground,
        # not a smear
        covs = cv2.resize(cov, (sw, sh), interpolation=cv2.INTER_AREA) > 250
        ring = (cv2.dilate(hm.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0) & ~hm & covs
        mc = small[ring].mean(0) if ring.any() else small[covs].mean(0)
        n = int(8 * 24 * RES) // f * f; nk = n // f; best = None
        cint = np.pad(covs.astype(np.int32), ((1, 0), (1, 0))).cumsum(0).cumsum(1)
        for y in range(0, sh - nk, max(1, nk // 3)):
            for x in range(0, sw - nk, max(1, nk // 3)):
                if cint[y + nk, x + nk] - cint[y, x + nk] - cint[y + nk, x] + cint[y, x] < nk * nk: continue
                blk = small[y:y + nk, x:x + nk].reshape(-1, 3).astype(np.float32)
                v = np.abs(blk.mean(0) - mc).sum() + 0.5 * blk.std(0).sum()
                if best is None or v < best[0]: best = (v, x * f, y * f)
        big = cv2.resize(filled, (W, H), interpolation=cv2.INTER_CUBIC).astype(np.float32)
        if best:
            _, px, py = best; P = A[py:py + n, px:px + n, :3].astype(np.float32)
            tile = np.concatenate([np.concatenate([P, P[:, ::-1]], 1), np.concatenate([P[::-1], P[::-1, ::-1]], 1)], 0)
            det = np.clip(tile / (cv2.GaussianBlur(tile, (0, 0), n / 6) + 1), 0.55, 1.6)
            T2 = 2 * n
            for y0 in range(0, H, T2):   # (row blocks: memory)
                rows = slice(y0, min(H, y0 + T2)); hb = rows.stop - y0
                reps = int(np.ceil(W / T2)); D = np.tile(det[:hb], (1, reps, 1))[:, :W]
                big[rows] *= D
            print('hole texture from', (px, py), flush=True)
        k = cv2.GaussianBlur(hole.astype(np.float32), (0, 0), 6 * RES)[..., None]
        k = np.maximum(k, cv2.erode(hole.astype(np.uint8), np.ones((int(4 * RES), int(4 * RES)), np.uint8))[..., None].astype(np.float32))
        A[..., :3] = np.clip(A[..., :3] * (1 - k) + big * k, 0, 255).astype(np.uint8); A[..., 3] = np.maximum(A[..., 3], (k[..., 0] * 255).astype(np.uint8))
        print('holes filled', round(hole.mean() * 100, 2), '%', flush=True)
    n = 0
    def soften(x0, x1, y0, y1, axis, half):
        """the band [x0, x1) x [y0, y1) straddles a seam (axis 1: vertical seam, the band is crossed along x). Inside it
        the ground is rebuilt as a cross-fade between the two sides mirrored from outside the saw teeth; where the
        two sides look alike nothing changes (decided every ~120 Dofus px along the seam, weights interpolated)"""
        nonlocal n
        x0, x1, y0, y1 = max(0, x0), min(W, x1), max(0, y0), min(H, y1)
        if x1 - x0 < 8 or y1 - y0 < 8: return
        B = A[y0:y1, x0:x1, :3]
        if axis == 0: B = B.transpose(1, 0, 2)   # work as if the seam were vertical: rows along it, columns across
        Lr, Ln = B.shape[0], B.shape[1]
        if axis == 1:
            src = A[y0:y1, :, :3]; lo, hi = x0, x1
        else:
            src = A[:, x0:x1, :3].transpose(1, 0, 2); lo, hi = y0, y1
        ext = src.shape[1]
        idx = np.arange(Ln)
        li = np.clip(2 * lo - (lo + idx) - 1, 0, ext - 1); ri = np.clip(2 * hi - (lo + idx) - 1, 0, ext - 1)   # mirrors
        Lm, Rm = src[:, li].astype(np.float32), src[:, ri].astype(np.float32)
        p = int(30 * RES)
        a_ = src[:, max(0, lo - p):lo].astype(np.float32); b_ = src[:, hi:min(ext, hi + p)].astype(np.float32)
        if not a_.shape[1] or not b_.shape[1]: return
        step = int(120 * RES); cs = np.arange(0, Lr, step)
        # 0.37: the texture counts too (yellow grass against swamp have close means), and the fade starts sooner
        d = np.array([np.abs(a_[c:c + step].reshape(-1, 3).mean(0) - b_[c:c + step].reshape(-1, 3).mean(0)).sum()
                      + 0.5 * np.abs(a_[c:c + step].reshape(-1, 3).std(0) - b_[c:c + step].reshape(-1, 3).std(0)).sum() for c in cs])
        wv = np.clip((d - 3) / 9, 0, 1)
        t = (idx + 0.5) / Ln; t = t * t * (3 - 2 * t)
        X = Lm * (1 - t)[None, :, None] + Rm * t[None, :, None]
        # 0.38: teeth also where both sides look alike from outside (water / water with the other map's land cells
        # hanging into the band): the band itself is compared with the clean cross-fade
        # (the band holds far more pixels unlike both sides than the sides themselves do = cells of another ground)
        Bf = B.astype(np.float32); d2 = []
        for c in cs:
            o = np.concatenate([a_[c:c + step].reshape(-1, 3), b_[c:c + step].reshape(-1, 3)]); m = o.mean(0)
            fo = (np.abs(o - m).sum(1) > 70).mean(); fb = (np.abs(Bf[c:c + step].reshape(-1, 3) - m).sum(1) > 70).mean()
            d2.append(fb - fo)
        wv = np.maximum(wv, np.clip((np.array(d2) - 0.06) / 0.1, 0, 1))
        wv = np.maximum(wv, np.maximum(np.r_[wv[1:], 0], np.r_[0, wv[:-1]]))   # (the fade starts one piece before a different one)
        if wv.max() <= 0: return
        prof = np.interp(np.arange(Lr), cs + step / 2, wv)[:, None, None]
        out = (B.astype(np.float32) * (1 - prof) + X * prof).astype(np.uint8)
        if axis == 0: out = out.transpose(1, 0, 2)
        A[y0:y1, x0:x1, :3] = out; n += 1
    rows, cols = len(maps), len(maps[0])
    hx, hy = int(44 * RES), int(28 * RES)   # (0.37: a little wider: the last teeth went past the band)   # half widths of the bands: past the half cells (26.5 / 13.5 Dofus px)
    for j in range(rows):
        for i in range(1, cols):
            if (SEAMS and (maps[j][i] or maps[j][i - 1])) or bool(maps[j][i]) != bool(maps[j][i - 1]):   # (0.38: only a map next to an empty slot: its half cells stick out over the old picture; 0.52: SEAMS, every seam where the two grounds differ: no more straight cuts)
                x = int(i * mw); soften(x - hx, x + hx, int(j * mh), int((j + 1) * mh), 1, hx)
    for j in range(1, rows):
        for i in range(cols):
            if (SEAMS and (maps[j][i] or maps[j - 1][i])) or bool(maps[j][i]) != bool(maps[j - 1][i]):
                y = int(j * mh); soften(int(i * mw), int((i + 1) * mw), y - hy, y + hy, 0, hy)
    print('seams softened', n, flush=True)
    return Image.fromarray(A)


def sea_patch_fill(img, maps):
    """the slots of a new island without a map: tiled with a patch of its own open sea (mirrored, so it is seamless)"""
    holes = [(i, j) for j, row in enumerate(maps) for i, m in enumerate(row) if not m]
    if not holes: return img
    cs = 24 * RES; k = 8; best = None   # k x k cells (24 Dofus px each) of open sea (blue, opaque), the darkest
    cols, rows = int(img.width // cs), int(img.height // cs)
    sm = np.array(img.resize((cols, rows), Image.BOX)).astype(np.int32)
    blue = (sm[:, :, 2] > sm[:, :, 0] + 40) & (sm[:, :, 3] == 255)
    for k in range(18, 5, -2):   # the largest patch there is (less repetition)
        for y in range(0, rows - k):
            for x in range(0, cols - k):
                if not blue[y:y + k, x:x + k].all(): continue
                v = sm[y:y + k, x:x + k, :3].mean() + sm[y:y + k, x:x + k, :3].std()
                if best is None or v < best[0]: best = (v, int(x * cs), int(y * cs))
        if best: break
    if best is None: return img
    _, px, py = best; n = int(k * cs)
    p = img.crop((px, py, px + n, py + n)).convert('RGBA')
    t = Image.new('RGBA', (2 * n, 2 * n))
    t.paste(p, (0, 0)); t.paste(p.transpose(Image.FLIP_LEFT_RIGHT), (n, 0))
    t.paste(p.transpose(Image.FLIP_TOP_BOTTOM), (0, n)); t.paste(p.transpose(Image.ROTATE_180), (n, n))
    mw, mh = int(round(MR.MAPW * RES)), int(round(MR.MAPH * RES))
    for i, j in holes:
        x0, y0 = int(round(i * MR.MAPW * RES)), int(round(j * MR.MAPH * RES))
        sea = Image.new('RGBA', (mw, mh))
        for yy in range(0, mh, 2 * n):
            for xx in range(0, mw, 2 * n): sea.paste(t, (xx, yy))
        under = Image.new('RGBA', img.size); under.paste(sea, (x0, y0))
        under.alpha_composite(img); img = under
    print('sea patch', best, len(holes), 'holes', flush=True)
    return img


SEA = [g for g in range(450, 470) if g not in (456, 460, 461)]   # the beach and sea cells of the Otomai / Minotoror islands
# (sand, shallow, deep: gradients; not 456 = grass, 460 / 461 = earth)
# 0.51: worlds whose water is drawn again from the client's own pieces (client_water):
#   bg = the water picture (a map background) shown through the water cells' diamonds, tint = one even tint for it,
#   ground = the water cells, plain = the cell whose colour the picture takes, void = the empty ground of maps without
#   a background is water too (a list: + the cells that fade the ground into that void, grass to black, one or two
#   cells deep; vgrass = the ground those cells become at the window's edges, toward the next map), soft = (sx, sy) Dofus px: the water cells' shades (deep / shallow…) are blurred into
#   one smooth shade (no more stair steps of diamonds), drop = objects left out, empty = what fills the slots without a
#   map ('bg': maps of the water picture only; or dict(ground, o1, n): maps of that sea cell with n waves o1),
#   swap = {ground: ground} cells drawn as others
WATER = {
    # (0.52: + the pond-edge moss tiles cut as boxes, straight edges over the water: 2079-2095, 2227, 2228)
    'grobe': dict(bg=260, ground=[254, 255, 256, 257, 258], plain=254, tint=(70, 172, 146), soft=(18, 9), toneK=0.45, empty='bg',
                  drop=[1352, 2079, 2080, 2082, 2085, 2086, 2087, 2088, 2089, 2091, 2093, 2094, 2095, 2227, 2228]),   # (0.52: the dark ponds 255-258 are water too, a deeper shade)
    # Chafer / Porco: rippled water picture 38, flat water cells 27 and deep water cells 28-31 (hard diamonds) in the
    # client: here all rippled, one even shade (0.53, toneK 0: the deep water's soft dark blots made round shapes);
    # the black void around Chafer's cemetery is water
    'chafer': dict(bg=38, ground=[27, 28, 29, 30, 31], plain=27, void=[40, 41, 42], vgrass=511, soft=(18, 9), toneK=0),
    'porco': dict(bg=38, ground=[27, 28, 29, 30, 31], plain=27, soft=(18, 9), toneK=0, swap={83: 28, 84: 28, 85: 28, 44: 31}),   # (its blue sea cells: deep water)
    'wabbit': dict(bg=56, ground=[44, 45, 46, 47], plain=44, soft=(18, 9)),   # (its sea picture 56, flat / deep sea cells)
    'mino': dict(ground=SEA, soft=(18, 9)),
    'gelee': dict(ground=SEA, soft=(18, 9)),
    'otomai_coast': dict(ground=SEA, soft=(18, 9), bgs=[411]),
    'naufrages': dict(ground=SEA, soft=(18, 9), empty=dict(ground=455, o1=[80, 81], n=5)),
}
FADE_TOP = {1046: 0.5}
FEATHER = {1352: 0.3}   # (0.53: big glows cut square by their picture's box, e.g. the Koalaks' turquoise water glow: every edge fades)
EDGE_DECALS = {50, 51, 52, 53, 54, 55}   # (0.52: the lime borders the client lays where sand meets grass)   # light beams cut square at their top (the client hides it past the map's top edge): faded


def feather(s, part):
    """0.53: an object's picture fading out toward all four sides of its opaque box (part of its size on each side)"""
    a = np.array(s); ys, xs = np.nonzero(a[..., 3])
    if not len(xs): return s
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    rx = np.clip(np.minimum(np.arange(a.shape[1]) - x0, x1 - np.arange(a.shape[1])) / max(1, (x1 - x0) * part), 0, 1)
    ry = np.clip(np.minimum(np.arange(a.shape[0]) - y0, y1 - np.arange(a.shape[0])) / max(1, (y1 - y0) * part), 0, 1)
    f = np.minimum(ry[:, None], rx[None, :]); f = f * f * (3 - 2 * f)
    a[..., 3] = (a[..., 3] * f).astype(np.uint8)
    return Image.fromarray(a)


def fade_top(s, part):
    a = np.array(s); r = np.nonzero(a[..., 3].any(1))[0]
    if not len(r): return s
    y0 = r[0]; n = max(1, int((r[-1] - y0) * part))
    a[y0:y0 + n, :, 3] = (a[y0:y0 + n, :, 3] * ((np.arange(n) / n) ** 1.5)[:, None]).astype(np.uint8)
    return Image.fromarray(a)


def vcell(**k):
    c = dict(active=1, los=1, groundRot=0, level=7, mov=4, ground=0, slope=1, groundFlip=0, o1=0, o1Rot=0, o1Flip=0,
             o2Flip=0, o2Inter=0, o2=0); c.update(k); return c


def client_water(maps, cfg):
    """0.51, the water as the client draws it, cleaned (WATER): Grobe (0.51 first: its marsh ground shows the bridge
    map's water picture instead, the empty slots are maps of that water), Chafer / Porco, the sand-and-sea islands.
    Patches maprender (cells_of / render_map / sym_img / objects_of) for the build; returns the maps (+ virtual ones)"""
    I = MR.infos(); vid = -1; out = []; G = set(cfg['ground']); P = cfg.get('bg'); virt = {}; BGS = set(cfg.get('bgs', []))
    VG = set(cfg['void']) if isinstance(cfg.get('void'), list) else set()   # (cells that become the void's water)
    emp = cfg.get('empty')
    for j, row in enumerate(maps):
        r = []
        for i, m in enumerate(row):
            if m or not emp: r.append(m); continue
            I[vid] = dict(w=15, h=17, bg=P if emp == 'bg' else 0, music=None, outdoor=True, x=None, y=None, sa=None)
            if isinstance(emp, dict):   # a map of open sea: that cell everywhere, a few waves (seeded: the same each build)
                rng = np.random.default_rng(1000 * j + i); cells = [vcell(ground=emp['ground']) for _ in range(479)]
                for n in rng.choice(479, emp['n'], replace=False): cells[n].update(o1=int(rng.choice(emp['o1'])), o1Flip=int(rng.integers(2)))
                virt[vid] = cells
            r.append(vid); vid -= 1
        out.append(r)
    pos = {m: (i, j) for j, row in enumerate(out) for i, m in enumerate(row) if m}
    real_cells0, real_render, real_sym, real_objs = MR.cells_of, MR.render_map, MR.sym_img, MR.objects_of
    SW = cfg.get('swap', {})   # (grounds drawn as others)
    def real_cells(mid):
        d = real_cells0(mid)
        if not d or not SW: return d
        return ([dict(c, ground=SW.get(c['ground'], c['ground'])) for c in d[0]], d[1], d[2])
    MR.cells_of = real_cells
    over = {}; inner = {}
    isw = lambda m: P and (I[m].get('bg') == P or (cfg.get('void') and m > 0 and not I[m].get('bg')))   # (its window is water)
    BG2.update(m for row in out for m in row if m and isw(m))
    if cfg.get('void'):   # the void inside the window (its edge cells are off screen in the client) and the fading cells
        for m in pos:      # reached from it through such cells (the same cells inside the ground stay ground)
            if m <= 0 or I[m].get('bg'): continue
            cells, w, h = real_cells(m); xy = MR.cell_xy(cells, w); i, j = pos[m]
            def wet(di, dj):   # (the next map on that side is water: no map, or a map of the water picture)
                ii, jj = i + di, j + dj
                if not (0 <= jj < len(out) and 0 <= ii < len(out[0])): return True
                m2 = out[jj][ii]; return not m2 or I[m2].get('bg') == P
            sides = [(-1, 0, lambda x, y: x < MR.CW), (1, 0, lambda x, y: x > MR.MAPW - MR.CW), (0, -1, lambda x, y: y < 2 * MR.CHH),
                     (0, 1, lambda x, y: y > MR.MAPH - 2 * MR.CHH)]
            edge = lambda n: [s_ for s_ in sides if s_[2](*xy[n])]
            inside = lambda n: not edge(n) or all(wet(di, dj) for di, dj, _ in edge(n))   # (edge cells toward water count as inside)
            V = {n for n, c in enumerate(cells) if not c['ground'] and inside(n)}; front = set(V)
            for step in range(2):   # (the fade is one or two cells deep)
                nxt = set()
                for n in front:
                    for d in (-w, -(w - 1), w - 1, w):
                        q = n + d
                        if 0 <= q < len(cells) and q not in V and cells[q]['ground'] in VG and inside(q): nxt.add(q)
                V |= nxt; front = nxt
            g2 = cfg.get('vgrass')   # (the fading cells at the window's edges, toward the next map: plain ground there)
            over[m] = ([dict(c, ground=-1) if n in V and c['ground'] else dict(c, ground=g2) if g2 and c['ground'] in VG and not inside(n) else c
                        for n, c in enumerate(cells)], w, h); inner[m] = V
    def cells_of(mid):
        if mid in over: return over[mid]
        if mid < 0: return (virt.get(mid, []), 15, 17)
        return real_cells(mid)
    MR.cells_of = cells_of

    def only(mid, res, margin, keep, layers=('cells',), bgcol=(0, 0, 0, 0)):   # the map with some of its cells only
        cells, w, h = cells_of(mid); old = over.get(mid); over[mid] = ([c if keep(c) else dict(c, ground=0) for c in cells], w, h)
        try: return real_render(mid, res, bgcol, margin, layers)
        finally:
            if old: over[mid] = old
            else: over.pop(mid)
    if P:
        bgk = lambda res: MR.sym_key('g', P, 0, 0, 0, res); tinted = {}
        def sym_img(k):   # the water picture, tinted once (a uniform shift: its ripples stay as drawn)
            im = real_sym(k)
            if im is None or not cfg.get('tint') or k != bgk(RES): return im
            if k not in tinted:
                a = np.array(im).astype(np.float32); op = a[..., 3] > 0
                a[..., :3] = np.clip(a[..., :3] + (np.array(cfg['tint'], np.float32) - a[..., :3][op].mean(0)), 0, 255)
                tinted[k] = Image.fromarray(a.astype(np.uint8), 'RGBA')
            return tinted[k]
        MR.sym_img = sym_img
        MR.ensure_symbols({('g', P, 0, 0, 0)}, RES)
        I[0] = dict(w=15, h=17, bg=P, outdoor=True, x=None, y=None, sa=None)
        MR.cells_of = lambda mid: ([], 15, 17) if mid == 0 else cells_of(mid)
        win = np.array(real_render(0, RES, (0, 0, 0, 0), 0, ('bg',))).astype(np.float32)   # one window of the water picture
        MR.cells_of = cells_of; del I[0]
        import cv2   # (its edges carry a row of dark dots: they made a dotted line along every map edge once tiled)
        lum = win[..., :3].mean(-1); b = int(4 * RES); band = np.zeros(lum.shape, bool); band[:b] = band[-b:] = True; band[:, :b] = band[:, -b:] = True
        dots = band & (lum < np.median(lum) - 25)
        if dots.any():
            dots = cv2.dilate(dots.astype(np.uint8), np.ones((3, 3), np.uint8))
            win[..., :3] = cv2.inpaint(np.clip(win[..., :3], 0, 255).astype(np.uint8), dots, 5, cv2.INPAINT_TELEA).astype(np.float32)
        # 0.53: the picture's own light (lighter toward a corner, a dark band along its edges) drew a grid of map seams once
        # tiled: its low frequencies are flattened (the ripples stay), measured on the picture tiled 3 x 3 so it still tiles
        q = 8; sm = cv2.resize(np.ascontiguousarray(win[..., :3]), (win.shape[1] // q, win.shape[0] // q), interpolation=cv2.INTER_AREA)
        lowf = cv2.GaussianBlur(np.tile(sm, (3, 3, 1)), (0, 0), 50 / q)[sm.shape[0]:2 * sm.shape[0], sm.shape[1]:2 * sm.shape[1]]
        lowf = cv2.resize(lowf, (win.shape[1], win.shape[0]), interpolation=cv2.INTER_CUBIC)
        win[..., :3] = np.clip(win[..., :3] - lowf + sm.reshape(-1, 3).mean(0), 0, 255)
        op = win[..., 3] > 0; meanP = win[..., :3][op].mean(0)
    W0, H0 = int(round(MR.MAPW * RES)), int(round(MR.MAPH * RES))
    tone = None
    if cfg.get('soft'):   # the water cells' shade over the whole world, at 1 px per Dofus px, blurred inside the water only
        import cv2
        k = 1 / RES; rows, cols = len(out), len(out[0]); Wt, Ht = int(cols * MR.MAPW), int(rows * MR.MAPH)
        T = np.zeros((Ht, Wt, 3), np.float32); R = np.zeros((Ht, Wt), np.float32); M = 40
        shift = 0; K = cfg.get('toneK', 1)
        if P and cfg.get('plain'):
            MR.ensure_symbols({('g', cfg['plain'], 0, 0, 0)}, RES); s = np.array(real_sym(MR.sym_key('g', cfg['plain'], 0, 0, 0, RES))).astype(np.float32)
            shift = meanP - s[..., :3][s[..., 3] > 128].mean(0)
        def paste(t, x, y, f):   # f(region of T, region of R, rgba of t) in world px at 1 px per Dofus px
            t = np.array(t.resize((int(round(t.width * k)), int(round(t.height * k))), Image.BOX)).astype(np.float32)
            x0, y0 = max(0, x), max(0, y); x1, y1 = min(Wt, x + t.shape[1]), min(Ht, y + t.shape[0])
            if x1 > x0 and y1 > y0: f(T[y0:y1, x0:x1], R[y0:y1, x0:x1], t[y0 - y:y1 - y, x0 - x:x1 - x])
        for m, (i, j) in pos.items():
            sl = (slice(int(j * MR.MAPH), int((j + 1) * MR.MAPH)), slice(int(i * MR.MAPW), int((i + 1) * MR.MAPW)))
            if isw(m): T[sl] = meanP; R[sl] = 1
            elif I[m].get('bg') in BGS:   # (0.52: a background the sea cells meet, e.g. the Otomai coast's sand picture: its
                k_ = MR.sym_key('g', I[m]['bg'], 0, 0, 0, RES); MR.ensure_symbols({('g', I[m]['bg'], 0, 0, 0)}, RES)   # colour joins the shade)
                b_ = np.array(real_sym(k_)).astype(np.float32); T[sl] = b_[..., :3][b_[..., 3] > 128].mean(0); R[sl] = 1
        def put(Tr, Rr, t):
            a = t[..., 3:] / 255; c = t[..., :3] + shift
            if K != 1: c = meanP + (c - meanP) * K   # (0.52: toneK, the deep cells' shades a little closer to the water's own)
            Tr[:] = Tr * (1 - a) + c * a; Rr[:] = np.maximum(Rr, a[..., 0])
        for m, (i, j) in pos.items():
            if any(c['ground'] in G for c in cells_of(m)[0]): paste(only(m, RES, M, lambda c: c['ground'] in G), int(i * MR.MAPW - M), int(j * MR.MAPH - M), put)
        def cut(Tr, Rr, t): Rr[:] = Rr * (1 - t[..., 3] / 255)
        for m, (i, j) in pos.items():
            if any(c['ground'] and c['ground'] not in G for c in cells_of(m)[0]): paste(only(m, RES, M, lambda c: c['ground'] not in G), int(i * MR.MAPW - M), int(j * MR.MAPH - M), cut)
        sx, sy = cfg['soft']
        bl = lambda x: cv2.GaussianBlur(x, (0, 0), sigmaX=sx, sigmaY=sy)
        mw_ = meanP if P else (T * R[..., None]).sum((0, 1)) / max(1.0, float(R.sum()))
        den = bl(R)[..., None]; tone = (bl(T * R[..., None]) + mw_ * 0.02) / (den + 0.02)   # (0.52: far from any water cell, the water's own mean, not black)
        tone = Image.fromarray(np.pad(np.clip(tone, 0, 255).astype(np.uint8), ((64, 64), (64, 64), (0, 0)), mode='edge'))   # (margins past the world's edges)
        print('water shade', cfg['soft'], round(float((R > 0.5).mean()) * 100, 1), '% water', flush=True)
        if P: cfg['_R'] = R   # (where the water is: the slow water mask)

    def fill(x0, y0, w, h):   # the water at RES over world px [x0, x0 + w) x [y0, y0 + h)
        if tone is not None:
            sh = np.array(tone.resize((w, h), Image.BICUBIC, box=(x0 / RES + 64, y0 / RES + 64, (x0 + w) / RES + 64, (y0 + h) / RES + 64))).astype(np.float32)
        if P:
            ys = (np.arange(y0, y0 + h) % H0); xs = (np.arange(x0, x0 + w) % W0)
            f = win[ys][:, xs].copy()
            if tone is not None: f[..., :3] = np.clip(f[..., :3] + sh - meanP, 0, 255)
            f[..., 3] = 255
        else:
            f = np.dstack([sh, np.full((h, w), 255, np.float32)])
        return f.astype(np.uint8)

    cfg['_fill'] = fill

    def render_map(mid, res, bgcol=(0, 0, 0, 0), margin=0, layers=('ground', 'o1', 'o2')):
        if mid not in pos: return real_render(mid, res, bgcol, margin, layers)
        i, j = pos[mid]; ox, oy = int(round((i * MR.MAPW - margin) * res)), int(round((j * MR.MAPH - margin) * res))
        cells = cells_of(mid)[0]; void = bool(inner.get(mid))
        wbg = ('bg' in layers or 'ground' in layers) and isw(mid) and (tone is not None or I[mid].get('bg') != P)   # (water background)
        cl = ('cells' in layers or 'ground' in layers) and (void or any(c['ground'] in G for c in cells))
        if not wbg and not cl: return real_render(mid, res, bgcol, margin, layers)
        lay = tuple(l for l in layers if not (wbg and l == 'bg')) if 'ground' not in layers or not wbg else tuple(l for l in layers if l != 'ground') + ('cells',)
        under = None
        if cl and 'bg' in lay:   # (a background that is not water: under the water, the cells over both)
            under = real_render(mid, res, bgcol, margin, ('bg',)); lay = tuple(l for l in lay if l != 'bg'); bgcol = (0, 0, 0, 0)
        if cl:   # (the water cells' diamonds, their hairline gaps closed: no line of the background between two of them)
            import cv2
            mask = cv2.morphologyEx(np.array(only(mid, res, margin, lambda c: c['ground'] in G).getchannel('A')), cv2.MORPH_CLOSE, np.ones((int(2 * res) | 1,) * 2, np.uint8))
            rest = only(mid, res, margin, lambda c: c['ground'] not in G, lay, bgcol)
        else:
            rest = real_render(mid, res, bgcol, margin, lay) if lay else Image.new('RGBA', (int(round((MR.MAPW + 2 * margin) * res)), int(round((MR.MAPH + 2 * margin) * res))))
            mask = np.zeros((rest.height, rest.width), np.uint8)
        if void and cl:   # the ground's edge against the void's water: soft (a short fade inside the ground), not stair steps
            import cv2
            V = inner[mid]; full = sorted(G)[0]
            cs, w, h = cells_of(mid); old = over.get(mid)
            over[mid] = ([dict(c, ground=full if n in V else 0) for n, c in enumerate(cs)], w, h)
            try: v = np.array(real_render(mid, res, (0, 0, 0, 0), margin, ('cells',)).getchannel('A'))
            finally: over[mid] = old
            vs = cv2.GaussianBlur((v > 128).astype(np.float32), (0, 0), 3 * res)
            ra = np.array(seal(rest)); ra[..., 3] = (ra[..., 3] * np.clip(1 - 2 * vs, 0, 1)).astype(np.uint8); rest = Image.fromarray(ra)
        if wbg: mx = int(round(margin * res)); mask[mx:mx + H0, mx:mx + W0] = 255
        if cl:   # 0.52: the shore: the notches between the water's diamonds are water too (a line along their tips, not a
            import cv2   # saw blade), the land cells give way there, and the edge is feathered a little
            ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(46 * res) | 1, int(24 * res) | 1))
            closed = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, ker)
            closed = np.maximum(mask, cv2.GaussianBlur(closed, (0, 0), 2.5 * res)).astype(np.uint8)
            add = (closed.astype(np.int16) - mask) > 0
            if add.any():
                ra = np.array(rest); ra[..., 3] = np.where(add, (ra[..., 3] * (1 - closed / 255.0)).astype(np.uint8), ra[..., 3]); rest = Image.fromarray(ra)
            mask = closed
        f = fill(ox, oy, rest.width, rest.height); f[..., 3] = mask
        water = Image.fromarray(f, 'RGBA')
        if under is not None: under.alpha_composite(water); water = under
        water.alpha_composite(rest)
        return water
    MR.render_map = render_map
    dropk = set(cfg.get('drop', []))   # (0.52: every rotation / flip of them)
    MR.objects_of = lambda mid, res: [o for o in real_objs(mid, res) if int(o[3][1:].split('_')[0]) not in dropk]
    return out


def water_mask(img, cell=24):
    """slow water: blue / turquoise cells (24 x 24 Dofus px) -> run-length rows"""
    k = cell * RES
    cols, rows = int(math.ceil(img.width / k)), int(math.ceil(img.height / k))
    small = np.array(img.convert('RGB').resize((cols * 4, rows * 4), Image.BOX)).astype(np.int32)
    r, g, b = small[:, :, 0], small[:, :, 1], small[:, :, 2]
    wat = (b > r + 40) & (b > 110) & (g > r) & (abs(g - b) < 90)
    return rle_mask(wat.reshape(rows, 4, cols, 4).mean(axis=(1, 3)) > 0.6, cell)


def rle_mask(w, cell=24):
    rows, cols = w.shape
    bits = w.flatten().astype(np.uint8); rle = []; v = 0; n = 0
    for x in bits:
        if x == v: n += 1
        else: rle.append(n); v ^= 1; n = 1
    rle.append(n)
    return dict(cell=cell, cols=cols, rows=rows, rle=rle), w


BG2 = set()   # (0.51: the maps whose window is water, set by client_water)
SEAMS = False   # (0.52 tried a mirrored cross-fade of every seam whose sides differ: it smeared sand over the water and made
#  diamonds of mirrored teeth; 0.53: off, the seams are softened by the wavy cross-fade of compose and blend_open_sea for the open-water slots)
NO_OLD = {'otomai_jungle'}   # worlds whose empty map slots get the world's own ground (inpainted + textured), not the old picture
FILL_EMPTY = False


# 0.51: worlds whose grass ground is smoothed (soft_ground): ground = the plain grass cells, drop = the cells that only
# fade one grass into another (gradients inside a diamond: replaced by the background), bgs = the grass backgrounds,
# tone = cells that only lend their colour (drawn with the background's texture: a soft lighter patch, no flat diamond
# with a slit down it), bgswap = backgrounds drawn as others (Koalak's 287 is a painted view down a valley, white around, cut at its window),
# soft = (sx, sy) Dofus px. The shade of each cell / background (its mean colour) is blurred into one smooth field and
# every grass pixel is moved by (smooth shade - its own flat shade): the texture stays, the diamond stair steps between
# two shades (the 'teeth') melt
GSOFT = {
    'koalak': dict(ground=[502, 511, 509, 507, 501, 504, 49, 4, 69], drop=[57, 58, 59], tone=[501, 504, 507, 509, 511], bgs=[71, 114], bgswap={287: 71}, soft=(20, 10)),
}
GRADE = {'kwismas': dict(gamma=1.32, white=0.92, sat=1.08)}   # (0.51: the snow was too bright: whites down, mids a little deeper)


def soft_ground(maps, cfg):
    import cv2
    I = MR.infos(); G = set(cfg['ground']); D = set(cfg.get('drop', [])); B = set(cfg.get('bgs', [])); TN = set(cfg.get('tone', []))
    for row in maps:
        for m in row:
            if m and I[m].get('bg') in cfg.get('bgswap', {}): I[m]['bg'] = cfg['bgswap'][I[m]['bg']]
    real_cells, real_render, real_sym = MR.cells_of, MR.render_map, MR.sym_img
    over = {}
    def cells_of(mid):
        if mid in over: return over[mid]
        d = real_cells(mid)
        if not d: return d
        return ([dict(c, ground=0) if c['ground'] in D else c for c in d[0]], d[1], d[2])
    MR.cells_of = cells_of
    flat = {}
    def flat_sym(k):   # the same picture in its mean colour
        if k not in flat:
            im = real_sym(k)
            if im is None: flat[k] = None
            else:
                a = np.array(im); op = a[..., 3] > 128
                if op.any(): a[..., :3] = a[..., :3][op].mean(0).astype(np.uint8)
                flat[k] = Image.fromarray(a)
        return flat[k]
    def only(mid, res, margin, keep, layers=('cells',), sym=None):
        cells, w, h = cells_of(mid); over[mid] = ([c if keep(c) else dict(c, ground=0) for c in cells], w, h)
        if sym: MR.sym_img = sym
        try: return real_render(mid, res, (0, 0, 0, 0), margin, layers)
        finally: over.pop(mid); MR.sym_img = real_sym
    pos = {m: (i, j) for j, row in enumerate(maps) for i, m in enumerate(row) if m}
    W0, H0 = int(round(MR.MAPW * RES)), int(round(MR.MAPH * RES))
    rows, cols = len(maps), len(maps[0]); Wt, Ht = int(cols * MR.MAPW), int(rows * MR.MAPH)
    T = np.zeros((Ht, Wt, 3), np.float32); R = np.zeros((Ht, Wt), np.float32); k = 1 / RES
    small = lambda im: np.array(im.resize((int(MR.MAPW), int(MR.MAPH)), Image.BOX)).astype(np.float32)
    for m, (i, j) in pos.items():   # each window: the flat shades (grass background + grass cells), and where they show
        sl = (slice(int(j * MR.MAPH), int(j * MR.MAPH) + int(MR.MAPH)), slice(int(i * MR.MAPW), int(i * MR.MAPW) + int(MR.MAPW)))
        if I[m].get('bg') in B:
            b = small(only(m, RES, 0, lambda c: False, ('bg',), flat_sym))
            a = b[..., 3:] / 255; T[sl] = T[sl] * (1 - a) + b[..., :3] * a; R[sl] = np.maximum(R[sl], a[..., 0])
        g = small(only(m, RES, 0, lambda c: c['ground'] in G, sym=flat_sym)); a = g[..., 3:] / 255
        T[sl] = T[sl] * (1 - a) + g[..., :3] * a; R[sl] = np.maximum(R[sl], a[..., 0])
        n = small(only(m, RES, 0, lambda c: c['ground'] > 0 and c['ground'] not in G)); R[sl] *= 1 - n[..., 3] / 255
    sx, sy = cfg['soft']; bl = lambda x: cv2.GaussianBlur(x, (0, 0), sigmaX=sx, sigmaY=sy)
    den = bl(R)[..., None]; Ts = np.where(den > 1e-3, bl(T * R[..., None]) / np.maximum(den, 1e-3), T)
    P = 64; Ts = Image.fromarray(np.pad(np.clip(Ts, 0, 255).astype(np.uint8), ((P, P), (P, P), (0, 0)), mode='edge'))
    print('ground shade', cfg['soft'], round(float((R > 0.5).mean()) * 100, 1), '% grass', flush=True)
    def shade(ox, oy, w, h):
        return np.array(Ts.resize((w, h), Image.BICUBIC, box=(ox / RES + P, oy / RES + P, (ox + w) / RES + P, (oy + h) / RES + P))).astype(np.float32)
    def moved(act, fl, ox, oy):   # act + (smooth shade - flat shade) where the flat layer is
        a = np.array(act).astype(np.float32); f = np.array(fl).astype(np.float32)
        d = (shade(ox, oy, a.shape[1], a.shape[0]) - f[..., :3]) * (f[..., 3:] / 255)
        a[..., :3] = np.clip(a[..., :3] + d, 0, 255); return Image.fromarray(a.astype(np.uint8))

    def render_map(mid, res, bgcol=(0, 0, 0, 0), margin=0, layers=('ground', 'o1', 'o2')):
        if mid not in pos or not ({'bg', 'cells', 'ground'} & set(layers)): return real_render(mid, res, bgcol, margin, layers)
        i, j = pos[mid]; ox, oy = int(round((i * MR.MAPW - margin) * res)), int(round((j * MR.MAPH - margin) * res))
        out = Image.new('RGBA', (int(round((MR.MAPW + 2 * margin) * res)), int(round((MR.MAPH + 2 * margin) * res))), bgcol)
        if 'bg' in layers or 'ground' in layers:
            b = only(mid, res, margin, lambda c: False, ('bg',))
            if I[mid].get('bg') in B: b = moved(b, only(mid, res, margin, lambda c: False, ('bg',), flat_sym), ox, oy)
            out.alpha_composite(b)
        if 'cells' in layers or 'ground' in layers:
            gl = lambda c: c['ground'] in G and (c['ground'] not in TN or I[mid].get('bg') not in B)
            out.alpha_composite(moved(only(mid, res, margin, gl), only(mid, res, margin, gl, sym=flat_sym), ox, oy))
            out.alpha_composite(only(mid, res, margin, lambda c: c['ground'] not in G))
        rest = tuple(l for l in layers if l in ('o1', 'o2'))
        if rest: out.alpha_composite(real_render(mid, res, (0, 0, 0, 0), margin, rest))
        return out
    MR.render_map = render_map
    return maps


def grade(img, g):
    a = np.asarray(img.convert('RGB')).astype(np.float32) / 255
    a = np.power(a, g.get('gamma', 1)) * g.get('white', 1)
    if g.get('sat', 1) != 1:
        l = a.mean(-1, keepdims=True); a = l + (a - l) * g['sat']
    return Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8))


def build(name):
    if name in ('vlad', 'goultard'):   # (0.51: Dark Vlad's clearing, composed: build_vlad51.py; 0.52: Goultard's, the same taken over)
        import build_vlad51 as V; V.RES = RES; return V.build(name=name)
    if name == 'grobe':   # (0.54: Grobe composed from its client pieces, no water: build_grobe54.py)
        import build_grobe54 as V; V.RES = RES; return V.build()
    if name in NEW:
        cfg = NEW[name]; maps = new_block(cfg)
    else:
        cfg = json.load(open(f'{ROOT}/work/world_{name}.json')); maps = cfg['maps']
    cols, rows = len(maps[0]), len(maps)
    W, H = int(round(cols * MR.MAPW * RES)), int(round(rows * MR.MAPH * RES))
    under, oldmeta = old_world(name, W, H) if name not in NEW else (None, None)
    global BG2, CUR; BG2 = set(); CUR = WATER.get(name)
    edge_inherit()
    if name in WATER: maps = client_water(maps, WATER[name])
    if name in GSOFT: maps = soft_ground(maps, GSOFT[name])
    global FILL_EMPTY; FILL_EMPTY = name in NO_OLD
    if FILL_EMPTY: under = None   # 0.38: the old picture under the empty slots is not wanted there (Otomai's jungle: a sky): own ground instead
    base = under.convert('RGBA') if under is not None else Image.new('RGBA', (W, H))
    needs = set()
    for row in maps:
        for m in row:
            if m: needs |= MR.needs_of(m)
    print(name, cols, rows, 'maps', sum(1 for r in maps for m in r if m), 'symbols', len(needs), flush=True)
    MR.ensure_symbols(needs, RES)
    global CUR_NAME; CUR_NAME = name
    if os.environ.get('MASK_ONLY'): return mask_only(name, maps, W, H)   # (0.87: the decor mask alone, no tile rewritten)
    img = compose(maps, base)
    if name in NEW and not WATER.get(name, {}).get('empty'): img = sea_patch_fill(img, maps)
    img = img.convert('RGB')
    if name in GRADE: img = grade(img, GRADE[name])
    os.makedirs(f'{G}/assets/worlds', exist_ok=True)
    for f in os.listdir(f'{G}/assets/worlds'):
        if f.startswith(name + '_') and f.endswith('.webp') and f[len(name) + 1].isdigit(): os.remove(f'{G}/assets/worlds/{f}')
    tiles = []; tot = 0
    for ty in range(0, H, TILE):
        for tx in range(0, W, TILE):
            t = img.crop((tx, ty, min(W, tx + TILE), min(H, ty + TILE)))
            fn = f'{name}_{tx // TILE}_{ty // TILE}.webp'
            t.save(f'{G}/assets/worlds/{fn}', 'WEBP', quality=Q, method=6); tot += os.path.getsize(f'{G}/assets/worlds/{fn}')
            tiles.append([tx // TILE, ty // TILE, fn])
    mini = img.copy(); mini.thumbnail((360, 360), Image.LANCZOS); mini.save(f'{G}/assets/worlds/{name}_mini.webp', 'WEBP', quality=82)
    SPR = json.load(open(f'{G}/data/sprites.json'))
    old = SPR['worlds'].get(name) or {}
    meta = dict(w=cols * MR.MAPW, h=rows * MR.MAPH, tile=round(TILE / RES, 4), res=RES, inset=old.get('inset', [0, 0, 0, 0]),
                music=old.get('music', cfg.get('music')), tiles=tiles)
    if old.get('decor'): meta['decor'] = old['decor']
    if WATER.get(name, {}).get('_R') is not None:   # (0.51: exactly where the water was drawn)
        R = WATER[name]['_R']; c = 24; rows_, cols_ = int(math.ceil(R.shape[0] / c)), int(math.ceil(R.shape[1] / c))
        R = np.pad(R, ((0, rows_ * c - R.shape[0]), (0, cols_ * c - R.shape[1])))
        meta['water'] = rle_mask(R.reshape(rows_, c, cols_, c).mean(axis=(1, 3)) > 0.5, c)[0]
    elif old.get('water'): meta['water'] = old['water']
    elif name in NEW:
        wm, w = water_mask(img); meta['water'] = wm
        meta['inset'] = island_inset(w, cols, rows)
    import sprio
    sprio.update(lambda S: S['worlds'].__setitem__(name, meta))
    print(name, 'done', (W, H), len(tiles), 'tiles', round(tot / 1e6, 1), 'MB', flush=True)


def mask_only(name, maps, W, H):
    """0.87: the standing objects of compose, placed the same way, into the decor mask only (decormask087)"""
    import decormask087 as DM; dm = DM.Mask(W, H, RES); meta = json.load(open(f'{MR.CACHE}/meta.json'))
    for j, row in enumerate(maps):
        for i, m in enumerate(row):
            if not m: continue
            for layer, x, y, k in MR.objects_of(m, RES):
                if layer != 2: continue
                o = meta.get(k); s = MR.sym_img(k)
                if not o or s is None: continue
                if k[0] == 'o' and int(k[1:].split('_')[0]) in FADE_TOP: s = fade_top(s, FADE_TOP[int(k[1:].split('_')[0])])
                if k[0] == 'o' and int(k[1:].split('_')[0]) in FEATHER: s = feather(s, FEATHER[int(k[1:].split('_')[0])])
                dm.add(s, int(round((i * MR.MAPW + x) * RES - o[0])), int(round((j * MR.MAPH + y) * RES - o[1])), o[1])
    dm.save(name)


def island_inset(w, cols, rows, cell=24, margin=140):
    """the playable bounds hug the land (+ a strip of shallow sea): insets left, right, top, bottom in world px"""
    land = ~w; ys, xs = np.nonzero(land)
    if not len(xs): return [0, 0, 0, 0]
    Wd, Hd = cols * MR.MAPW, rows * MR.MAPH
    x0, x1, y0, y1 = xs.min() * cell, (xs.max() + 1) * cell, ys.min() * cell, (ys.max() + 1) * cell
    return [max(0, int(x0 - margin)), max(0, int(Wd - x1 - margin)), max(0, int(y0 - margin)), max(0, int(Hd - y1 - margin))]


if __name__ == '__main__':
    for n in sys.argv[1:]: build(n)
