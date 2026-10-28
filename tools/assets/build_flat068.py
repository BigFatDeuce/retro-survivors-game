"""0.68: zones made again as flat plains like Dark Vlad's clearing / Grobe (build_vlad51 / build_grobe54), with
more decor, 2/3 of their old area (4452 x 2592 -> 3635 x 2116 Dofus px), from the zone's own client pieces only:
tools/zonestats068 counts what its client maps are made of; here the most used ground is the plain, the next ones its
paths and patches, its flat decals are strewn, its big objects (trees, rocks: measured on their rendered symbol) make a
forest / rock border on every edge and clusters inside, the small ones are sown everywhere; no water. The middle stays
clear (the runs start there). Writes assets/worlds/<world>_*.webp, <world>_mini.webp, SPR.worlds[world] (no water mask).
usage: RES=3.0 python tools/assets/build_flat068.py zone… [--seed=N]   (RES=1 for a quick look; PREVIEW=1 writes only work/flat068/<zone>.png)"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import sys, os, json, math
import numpy as np, cv2
from PIL import Image
import maprender as MR
import zonestats068 as ZS

G = f'{ROOT}/game'
RES = float(os.environ.get('RES', '3.0'))
TILE = 4096
Q = int(os.environ.get('Q', '80'))
# per zone: its world key, size, what to leave out (pieces that only make sense in their map: walls, cliff edges,
# water, buildings, doors…), its extra wishes; 'src' = where its client pieces come from (a zonestats068 name)
Z = {   # grounds = [plain, paths, patches, darker patches] (None: none); skip = pieces left out (light beams, black stalks,
        # mist, buildings and bridge pieces that only make sense in their own map…)
    'koalak': dict(world='koalak', src='koalak', grounds=[502, 507, 511, 501], smooth=1,
                   skip=[1030, 2224, 986, 2114, 2113, 2218, 2208, 2206, 2207, 2209, 2403, 3095, 218, 35, 37,
                         2809, 2810, 2811, 2813, 2814, 2815, 2817, 3025, 3085]),
    'otomai_jungle': dict(world='otomai_jungle', src='otomai_jungle', grounds=[255, 427, None, None],
                          skip=[1030, 3990, 3991, 3992, 4174, 3997, 3993, 3999, 3994, 3996, 4000, 3995, 3998, 30, 31, 32, 34,
                                4045, 4048, 4049, 2088, 2089, 2090, 2091, 2093, 2094, 2095, 3579]),
    'pandala': dict(world='pandala', src='pandala', grounds=[254, 265, 264, 238],
                    skip=[1030, 2224, 2225, 374, 2246, 2113, 2114, 2055, 2057, 2249, 6755, 2172,
                          2079, 2080, 2081, 2082, 2085, 2086, 2098, 2227, 2161, 2162, 2174, 2060, 2061, 2062, 2063, 2064]),   # (none of the ponds' pieces: banks, lily pads, raft, landing rails)
    'kwismas': dict(world='kwismas', src='kwismas', grounds=[349, None, None, None], skip=[1030, 7536, 3337, 3427]),
    # the Kwaks' hidden nest (Montagne des Craqueleurs pieces, the size of Grobe), extra: 4 nests
    'kwaknest': dict(world='kwaknest', src='sa:2,480', grounds=[69, 10, 17, 13], size=(3216, 1872), nest=1330,
                     skip=[1030, 2224, 88, 87, 89, 120, 34, 30, 35, 39, 32, 31, 121, 102, 801, 1290, 7534, 7536, 1103, 1102, 1512, 1289, 1288, 218, 1330,
                           90, 91, 93, 95, 96, 99, 100, 552, 328, 329,
                           891, 892, 92, 94, 97, 98, 920]),   # (no stone spires / layered pillars / lime tiles)
}
W0, H0 = 3635, 2116


def seal(t):
    import build_worlds20 as B
    B.RES = RES
    return B.seal(t)


def pieces(cfg):
    """(grounds by use, decals by use, objects by use) of the zone's client maps, minus the skipped ones"""
    if cfg.get('stats'): return cfg['stats']
    n, g, o1, o2 = ZS.stats(cfg['src'])
    sk = set(cfg.get('skip') or [])
    gr = cfg.get('grounds') or [k for k, _ in g.most_common(4)]
    return gr, [(k, v) for k, v in o1.most_common(30) if k not in sk], [(k, v) for k, v in o2.most_common(70) if k not in sk]


def build(zone, seed=68):
    cfg = Z[zone]; name = cfg['world']; W, H = cfg.get('size', (W0, H0))
    rng = np.random.default_rng(seed)
    X, Y = int(round(W * RES)), int(round(H * RES))
    grounds, decals, objects = pieces(cfg)
    objs_ids = [k for k, _ in decals] + [k for k, _ in objects]
    needs = {('o', cfg['nest'], 0, 0, f) for f in (0, 1)} if cfg.get('nest') else set()
    needs |= {('g', g, 0, 0, 0) for g in grounds if g} | {('o', o, 0, 0, f) for o in objs_ids for f in (0, 1)}
    meta = MR.ensure_symbols(needs, RES)
    # the objects by size (their rendered symbol, in Dofus px): big = trees / rocks, small = plants / stones / flowers
    size = {}
    for o in objs_ids:
        s = MR.sym_img(MR.sym_key('o', o, 0, 0, 0, RES))
        if s is not None: size[o] = (s.width / RES, s.height / RES)
    big = [(k, v) for k, v in objects if k in size and size[k][1] > 95 and size[k][0] > 50]
    mid_ = [(k, v) for k, v in objects if k in size and (k, v) not in big and size[k][1] > 45]
    small = [(k, v) for k, v in objects if k in size and size[k][1] <= 45 and size[k][0] < 140]
    flat = [(k, v) for k, v in decals if k in size and size[k][0] < 260]
    print(zone, 'grounds', grounds[:5], '| big', [k for k, _ in big][:12], '| mid', [k for k, _ in mid_][:12], '| small', len(small), '| decals', len(flat), flush=True)
    wpick = lambda lst: lst[rng.choice(len(lst), p=np.array([math.sqrt(v) for _, v in lst]) / sum(math.sqrt(v) for _, v in lst))][0]

    rows = range(-3, int(H / MR.CHH) + 4); cols = range(-2, int(W / MR.CW) + 3)
    cells = [(c * MR.CW + (r % 2) * MR.CHW, r * MR.CHH) for r in rows for c in cols]

    def layer(g, under=None):   # one ground everywhere, as the client draws its cells (over the plain: no gaps)
        if not g: return None
        im = Image.fromarray(under.astype(np.uint8)).convert('RGBA') if under is not None else Image.new('RGBA', (X, Y)); k = MR.sym_key('g', g, 0, 0, 0, RES); o = meta.get(k); s = MR.sym_img(k)
        if not o or s is None: return None
        for x, y in cells:
            px, py = int(round(x * RES - o[0])), int(round(y * RES - o[1]))
            if px >= X or py >= Y or px + s.width <= 0 or py + s.height <= 0: continue
            im.alpha_composite(s, (max(0, px), max(0, py)), (max(0, -px), max(0, -py)))
        return np.array(seal(im).convert('RGB')).astype(np.float32)
    base = layer(grounds[0]); L = [base] + [layer(g, base) for g in (list(grounds[1:4]) + [None] * 3)[:3]]

    def noise(s):
        n = cv2.GaussianBlur(rng.random((H, W)).astype(np.float32), (0, 0), s); return (n - n.mean()) / (n.std() + 1e-6)
    up = lambda m: cv2.resize(m.astype(np.float32), (X, Y), interpolation=cv2.INTER_CUBIC)[..., None]
    A = L[0].copy()
    if L[2] is not None:   # big soft patches of the third ground
        m = up(np.clip(noise(70) * 0.45 + noise(22) * 0.2 - 0.3, 0, 0.7)); A = A * (1 - m) + L[2] * m
    if L[3] is not None:
        m = up(np.clip(noise(45) * 0.5 - 0.6, 0, 0.6)); A = A * (1 - m) + L[3] * m
    if L[1] is not None:   # winding paths of the second ground and a glade in the middle
        mP = np.zeros((H, W), np.float32)
        def walk(x, y, a, n):
            pts = [(x, y)]
            for _ in range(n):
                a += rng.uniform(-0.35, 0.35); x += math.cos(a) * 60; y += math.sin(a) * 33; pts.append((x, y))
            cv2.polylines(mP, [np.array(pts, np.int32)], False, 1.0, int(rng.uniform(46, 70)), cv2.LINE_AA)
        for i in range(4):
            side = i % 4
            if side == 0: walk(0, rng.uniform(H * 0.25, H * 0.75), rng.uniform(-0.4, 0.4), 70)
            elif side == 1: walk(W, rng.uniform(H * 0.25, H * 0.75), math.pi + rng.uniform(-0.4, 0.4), 70)
            elif side == 2: walk(rng.uniform(W * 0.25, W * 0.75), 0, math.pi / 2 + rng.uniform(-0.5, 0.5), 60)
            else: walk(rng.uniform(W * 0.25, W * 0.75), H, -math.pi / 2 + rng.uniform(-0.5, 0.5), 60)
        cv2.ellipse(mP, (W // 2, H // 2), (320, 160), 0, 0, 360, 1, -1)
        mP = np.clip(cv2.GaussianBlur(mP, (0, 0), 14) * 1.25 + noise(12) * 0.12, 0, 1)
        A = A * (1 - up(mP * 0.95)) + L[1] * up(mP * 0.95)
    if cfg.get('smooth'):   # (Koalak: the cells' repeated pattern — light squares, diagonal strokes — goes: the broad shades
        # and the finest grain stay, the scale of the cells is taken out)
        lo = cv2.GaussianBlur(A, (0, 0), 22 * RES); fine = A - cv2.GaussianBlur(A, (0, 0), 1.2 * RES); A = lo + fine * 0.55
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.minimum(np.minimum(xx, W - xx), np.minimum(yy * 1.6, (H - yy) * 1.3))
    A *= up(0.45 + 0.55 * np.clip(d / 320, 0, 1) ** 0.8)   # (the border's shade)
    A *= up(1 - 0.07 * np.clip(noise(90), -1, 1))
    img = Image.fromarray(np.clip(A, 0, 255).astype(np.uint8)).convert('RGBA')

    mid = lambda x, y, r: math.hypot((x - W / 2) / 2, y - H / 2) < r
    objs = []   # (layer, x, y, symbol, flip)
    for _ in range(int(W * H / 26000)):   # flat decals
        x, y = rng.uniform(60, W - 60), rng.uniform(60, H - 60)
        if flat and not mid(x, y, 130): objs.append((1, x, y, wpick(flat), int(rng.integers(2))))
    B = big or mid_
    if B:   # the border: rows of the big pieces along every edge
        for x in np.arange(-40, W + 60, 70):
            for yb in (rng.uniform(-40, 10), rng.uniform(40, 110)): objs.append((2, x + rng.uniform(-25, 25), yb, wpick(B), int(rng.integers(2))))
            for yb in (rng.uniform(H - 30, H + 10), rng.uniform(H + 30, H + 120)): objs.append((2, x + rng.uniform(-25, 25), yb, wpick(B), int(rng.integers(2))))
        for y in np.arange(40, H + 40, 46):
            for side in (0, 1):
                for dx in (rng.uniform(-60, 0), rng.uniform(40, 120)): objs.append((2, dx if side == 0 else W - dx, y + rng.uniform(-14, 14), wpick(B), int(rng.integers(2))))
    inner = []   # clusters inside, away from the middle
    for _ in range(3000):
        if len(inner) >= int(W * H / 230000): break
        x, y = rng.uniform(320, W - 320), rng.uniform(260, H - 220)
        if mid(x, y, 320) or any(math.hypot((x - a) / 2, y - b) < 150 for a, b in inner): continue
        inner.append((x, y))
    for n, (x, y) in enumerate(inner):
        pool = B if n % 3 != 2 and B else (mid_ or B)
        for _ in range(int(rng.integers(1, 4))): objs.append((2, x + rng.uniform(-50, 50), y + rng.uniform(-22, 22), wpick(pool), int(rng.integers(2))))
        if mid_:
            for _ in range(int(rng.integers(1, 3))): objs.append((2, x + rng.uniform(-80, 80), y + rng.uniform(-36, 36), wpick(mid_), int(rng.integers(2))))
        if small:
            for _ in range(int(rng.integers(2, 6))): objs.append((2, x + rng.uniform(-90, 90), y + rng.uniform(-40, 40), wpick(small), int(rng.integers(2))))
    for _ in range(int(W * H / 14000)):   # small plants, stones, flowers everywhere
        x, y = rng.uniform(60, W - 60), rng.uniform(60, H - 40)
        if small and not mid(x, y, 90): objs.append((2, x, y, wpick(small), int(rng.integers(2))))
    if cfg.get('nest'): objs += nests(rng, W, H, cfg['nest'], [k for k in (544, 550, 556) if k in size] or [k for k, _ in small])
    objs.sort(key=lambda o: (o[0], o[2] if o[0] == 2 else 0))
    import decormask087 as DM; dm = DM.Mask(X, Y, RES)   # (0.87: the tall scenery, for the areas drawn under it)
    for lay, x, y, o, f in objs:
        k = MR.sym_key('o', o, 0, 0, f, RES); m = meta.get(k); s = MR.sym_img(k)
        if not m or s is None: continue
        px, py = int(round(x * RES - m[0])), int(round(y * RES - m[1]))
        if px >= X or py >= Y or px + s.width <= 0 or py + s.height <= 0: continue
        if lay == 2: dm.add(s, px, py, m[1])
        if os.environ.get('MASK_ONLY'): continue
        img.alpha_composite(s, (max(0, px), max(0, py)), (max(0, -px), max(0, -py)))
    dm.save(name)
    if os.environ.get('MASK_ONLY'): return
    img = img.convert('RGB')
    if os.environ.get('PREVIEW'):
        os.makedirs(f'{ROOT}/work/flat068', exist_ok=True); p = img.copy(); p.thumbnail((1600, 1600)); p.save(f'{ROOT}/work/flat068/{zone}.png'); print('preview', zone); return
    for f in os.listdir(f'{G}/assets/worlds'):
        if f.startswith(name + '_') and f.endswith('.webp') and f[len(name) + 1].isdigit(): os.remove(f'{G}/assets/worlds/{f}')
    tiles = []; tot = 0
    for ty in range(0, Y, TILE):
        for tx in range(0, X, TILE):
            fn = f'{name}_{tx // TILE}_{ty // TILE}.webp'
            img.crop((tx, ty, min(X, tx + TILE), min(Y, ty + TILE))).save(f'{G}/assets/worlds/{fn}', 'WEBP', quality=Q, method=6)
            tot += os.path.getsize(f'{G}/assets/worlds/{fn}'); tiles.append([tx // TILE, ty // TILE, fn])
    mini = img.copy(); mini.thumbnail((360, 360), Image.LANCZOS); mini.save(f'{G}/assets/worlds/{name}_mini.webp', 'WEBP', quality=82)
    old = json.load(open(f'{G}/data/sprites.json'))['worlds'].get(name) or {}
    meta_w = dict(w=W, h=H, tile=round(TILE / RES, 4), res=RES, inset=[200, 200, 200, 210], music=old.get('music', 123), tiles=tiles)
    if old.get('decor'): meta_w['decor'] = old['decor']
    import sprio
    sprio.update(lambda S: S['worlds'].__setitem__(name, meta_w))
    print(name, 'done', (X, Y), len(tiles), 'tiles', round(tot / 1e6, 1), 'MB', flush=True)


def nests(rng, W, H, nest, stones):
    """the Kwaks' four nests (client object 1330: a nest with its egg on a rock), one in each quarter of the plain,
    a ring of rocks around each"""
    out = []
    for qx, qy in ((0.27, 0.3), (0.73, 0.3), (0.27, 0.72), (0.73, 0.72)):
        x, y = W * qx + rng.uniform(-60, 60), H * qy + rng.uniform(-40, 40)
        for k in range(9):
            a = k / 9 * math.tau + rng.uniform(-0.2, 0.2); out.append((2, x + math.cos(a) * 95, y + math.sin(a) * 48, stones[int(rng.integers(len(stones)))], int(rng.integers(2))))
        out.append((2, x, y, nest, int(rng.integers(2))))
    return out


if __name__ == '__main__':
    a = [x for x in sys.argv[1:] if not x.startswith('--')]; seed = next((int(x.split('=')[1]) for x in sys.argv[1:] if x.startswith('--seed=')), 68)
    for z in a: build(z, seed)
