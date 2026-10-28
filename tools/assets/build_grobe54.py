"""0.54: L'île de Grobe made again (the client maps' marsh did not suit): one composed plain in Grobe's look, from
the client's own Grobe pieces, as Dark Vlad's clearing was (build_vlad51.py): lime grass (49) with soft patches of the
dark moss (254 / 193), winding earth paths (239, and 240 / 247 with the bamboos' shade), moss and stone decals, a forest
of bamboos all around (several rows), bamboo clumps, mossy stones and Grobe's totems inside, flowers, reeds, a little
mist. No water at all. 75 % of the area of a 5 x 5 zone (3710 x 2160 Dofus px): 3216 x 1872.
Writes assets/worlds/grobe_*.webp, grobe_mini.webp and SPR.worlds['grobe'] (no water mask; build_worlds20.py grobe comes here).
usage: RES=3.0 python tools/assets/build_grobe54.py [seed]"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import sys, os, json, math
import numpy as np, cv2
from PIL import Image
import maprender as MR

G = f'{ROOT}/game'
RES = float(os.environ.get('RES', '3.0'))
TILE = 4096
Q = int(os.environ.get('Q', '80'))
W, H = 3216, 1872
GRASS, MOSS, DARK = 49, 254, 193
EARTH, SHADE = 239, [240, 247, 250]
BAMBOOS = [2151, 2150, 2139, 2152, 2144, 2145, 2149, 2132, 2133, 2134, 2135, 2136, 2146, 2147, 2148]
CLUMPS = [2168, 2169, 2170, 2171]
STONES = [2117, 2118, 2125, 2124, 2127, 2115, 2116]
TOTEMS = [2419, 2422, 2421]
SMALL = [(2140, 3), (2156, 3), (2143, 3), (2142, 2), (2154, 2), (2153, 2), (2141, 2), (225, 3), (283, 4), (2128, 2), (2129, 2), (2130, 2), (2162, 2), (2161, 2)]
DECALS = [(2108, 3), (2105, 2), (2159, 2), (2160, 2), (2109, 3), (2226, 3), (991, 1), (2246, 2), (2107, 2)]
MIST = 2403
SHADOW = 2224


def seal(t):
    import build_worlds20 as B
    B.RES = RES
    return B.seal(t)


def build(seed=54, name='grobe'):
    rng = np.random.default_rng(seed)
    X, Y = int(round(W * RES)), int(round(H * RES))
    rows = range(-3, int(H / MR.CHH) + 4); cols = range(-2, int(W / MR.CW) + 3)
    cells = [(c * MR.CW + (r % 2) * MR.CHW, r * MR.CHH) for r in rows for c in cols]
    grounds = [GRASS, MOSS, DARK, EARTH] + SHADE
    objs_all = BAMBOOS + CLUMPS + STONES + TOTEMS + [o for o, _ in SMALL] + [o for o, _ in DECALS] + [MIST, SHADOW]
    needs = {('g', g, 0, 0, 0) for g in grounds} | {('o', o, 0, 0, f) for o in objs_all for f in (0, 1)}
    meta = MR.ensure_symbols(needs, RES)

    def layer(pick):   # one ground everywhere, as the client draws its cells
        im = Image.new('RGBA', (X, Y))
        for n, (x, y) in enumerate(cells):
            k = MR.sym_key('g', pick(n), 0, 0, 0, RES); o = meta.get(k); s = MR.sym_img(k)
            if not o or s is None: continue
            px, py = int(round(x * RES - o[0])), int(round(y * RES - o[1]))
            if px >= X or py >= Y or px + s.width <= 0 or py + s.height <= 0: continue
            im.alpha_composite(s, (max(0, px), max(0, py)), (max(0, -px), max(0, -py)))
        return np.array(seal(im).convert('RGB')).astype(np.float32)
    sh_pick = lambda n: SHADE[(n * 7 + n // 61) % len(SHADE)]
    L = {k: layer(lambda n, g=g: g) for k, g in (('grass', GRASS), ('moss', MOSS), ('dark', DARK), ('earth', EARTH))}
    L['shade'] = layer(sh_pick)

    def noise(s):
        n = cv2.GaussianBlur(rng.random((H, W)).astype(np.float32), (0, 0), s); return (n - n.mean()) / (n.std() + 1e-6)
    up = lambda m: cv2.resize(m.astype(np.float32), (X, Y), interpolation=cv2.INTER_CUBIC)[..., None]
    # dark moss: big soft patches (iso: wider than tall)
    mM = np.clip(noise(70) * 0.55 + noise(25) * 0.2 - 0.15, 0, 0.9)
    mD = np.clip(noise(45) * 0.5 - 0.55, 0, 0.7)
    # earth paths: a few winding walks across the plain, a wider glade in the middle
    mP = np.zeros((H, W), np.float32)
    def walk(x, y, a, n):
        pts = [(x, y)]
        for _ in range(n):
            a += rng.uniform(-0.35, 0.35); x += math.cos(a) * 60; y += math.sin(a) * 33; pts.append((x, y))
        cv2.polylines(mP, [np.array(pts, np.int32)], False, 1.0, int(rng.uniform(46, 70)), cv2.LINE_AA)
    for _ in range(4):
        side = rng.integers(4)
        if side == 0: walk(rng.uniform(0, W * 0.3), rng.uniform(H * 0.2, H * 0.8), rng.uniform(-0.5, 0.5), 70)
        elif side == 1: walk(rng.uniform(W * 0.7, W), rng.uniform(H * 0.2, H * 0.8), math.pi + rng.uniform(-0.5, 0.5), 70)
        elif side == 2: walk(rng.uniform(W * 0.2, W * 0.8), 0, math.pi / 2 + rng.uniform(-0.6, 0.6), 60)
        else: walk(rng.uniform(W * 0.2, W * 0.8), H, -math.pi / 2 + rng.uniform(-0.6, 0.6), 60)
    cv2.ellipse(mP, (W // 2, H // 2), (300, 150), 0, 0, 360, 1, -1)
    for _ in range(7):
        cv2.ellipse(mP, (int(rng.uniform(300, W - 300)), int(rng.uniform(220, H - 220))), (int(rng.uniform(90, 200)), int(rng.uniform(45, 95))), float(rng.uniform(-15, 15)), 0, 360, 1, -1)
    mP = np.clip(cv2.GaussianBlur(mP, (0, 0), 14) * 1.25 + noise(12) * 0.12, 0, 1)
    mS = np.clip(noise(30) * 0.6 + 0.35, 0, 1) * mP   # (the shaded earth inside the paths)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.minimum(np.minimum(xx, W - xx), np.minimum(yy * 1.6, (H - yy) * 1.3))
    mE = np.clip(1 - d / 260 + noise(20) * 0.15, 0, 1)   # (the forest floor: dark moss under the bamboos)
    A = L['grass']
    for k, m in (('moss', mM), ('dark', np.maximum(mD, mE)), ('earth', mP * 0.95 * (1 - mE)), ('shade', mS * 0.85 * (1 - mE))):
        u = up(m); A = A * (1 - u) + L[k] * u
    # the bamboo forest's shade around (cells go dark toward the trees), soft
    A *= up(0.35 + 0.65 * np.clip(d / 320, 0, 1) ** 0.8)
    A *= up(1 - 0.08 * np.clip(noise(90), -1, 1))   # (light and shade under the canopy)
    img = Image.fromarray(np.clip(A, 0, 255).astype(np.uint8)).convert('RGBA')

    mid = lambda x, y, r: math.hypot((x - W / 2) / 2, y - H / 2) < r
    wpick = lambda lst: [k for k, w in lst for _ in range(w)][rng.integers(sum(w for _, w in lst))]
    objs = []   # (layer, x, y, symbol, flip, alpha)
    for _ in range(140):   # flat moss / stone decals
        x, y = rng.uniform(60, W - 60), rng.uniform(60, H - 60)
        if not mid(x, y, 120): objs.append((1, x, y, wpick(DECALS), int(rng.integers(2)), 1.0))
    ring = []   # the forest: rows of bamboos along every edge, clumps between them
    for x in np.arange(-40, W + 60, 24):
        for yb in (rng.uniform(-30, 10), rng.uniform(25, 70), rng.uniform(80, 130)): ring.append((x + rng.uniform(-10, 10), yb))
        if rng.random() < 0.5: ring.append((x + rng.uniform(-10, 10), rng.uniform(130, 165)))
        for yb in (rng.uniform(H - 40, H), rng.uniform(H + 10, H + 70), rng.uniform(H + 80, H + 160)): ring.append((x + rng.uniform(-10, 10), yb))
    for y in np.arange(20, H + 40, 18):
        for side in (0, 1):
            for dx in (rng.uniform(-50, -10), rng.uniform(5, 50), rng.uniform(55, 110)):
                ring.append((dx if side == 0 else W - dx, y + rng.uniform(-8, 8)))
            if rng.random() < 0.45: ring.append(((rng.uniform(110, 150) if side == 0 else W - rng.uniform(110, 150)), y + rng.uniform(-8, 8)))
    for x, y in ring:
        objs.append((2, x, y, (BAMBOOS + CLUMPS)[rng.integers(len(BAMBOOS) + len(CLUMPS))], int(rng.integers(2)), 1.0))
    inner = []   # bamboo clumps, mossy stones and totems in the plain, away from the middle (where the runs start)
    for _ in range(2000):
        if len(inner) >= 26: break
        x, y = rng.uniform(300, W - 300), rng.uniform(240, H - 220)
        if mid(x, y, 300) or any(math.hypot((x - a) / 2, y - b) < 140 for a, b in inner): continue
        inner.append((x, y))
    for n, (x, y) in enumerate(inner):
        objs.append((1, x, y + 6, SHADOW, 0, 0.45))
        kind = n % 4
        if kind in (0, 1):
            for _ in range(int(rng.integers(3, 8))): objs.append((2, x + rng.uniform(-45, 45), y + rng.uniform(-20, 20), (BAMBOOS + CLUMPS)[rng.integers(len(BAMBOOS) + len(CLUMPS))], int(rng.integers(2)), 1.0))
        elif kind == 2:
            for _ in range(int(rng.integers(1, 4))): objs.append((2, x + rng.uniform(-35, 35), y + rng.uniform(-16, 16), STONES[rng.integers(len(STONES))], int(rng.integers(2)), 1.0))
        else:
            objs.append((2, x, y, TOTEMS[rng.integers(len(TOTEMS))], int(rng.integers(2)), 1.0))
            for _ in range(2): objs.append((2, x + rng.uniform(-40, 40), y + rng.uniform(-18, 18), STONES[rng.integers(len(STONES))], int(rng.integers(2)), 1.0))
        for _ in range(int(rng.integers(2, 6))): objs.append((2, x + rng.uniform(-70, 70), y + rng.uniform(-30, 30), wpick(SMALL), int(rng.integers(2)), 1.0))
    for _ in range(420):   # sprouts, reeds, grass, flowers
        x, y = rng.uniform(60, W - 60), rng.uniform(60, H - 40)
        if not mid(x, y, 90): objs.append((2, x, y, wpick(SMALL), int(rng.integers(2)), 1.0))
    for _ in range(9):   # a little mist
        objs.append((3, rng.uniform(200, W - 200), rng.uniform(150, H - 150), MIST, int(rng.integers(2)), 0.55))
    objs.sort(key=lambda o: (o[0], o[2] if o[0] == 2 else 0))
    import decormask087 as DM; dm = DM.Mask(X, Y, RES)   # (0.87: the tall scenery, for the areas drawn under it)
    for lay, x, y, o, f, al in objs:
        k = MR.sym_key('o', o, 0, 0, f, RES); m = meta.get(k); s = MR.sym_img(k)
        if not m or s is None: continue
        if al < 1:
            s = s.copy(); a = np.array(s); a[..., 3] = (a[..., 3] * al).astype(np.uint8); s = Image.fromarray(a)
        px, py = int(round(x * RES - m[0])), int(round(y * RES - m[1]))
        if px >= X or py >= Y or px + s.width <= 0 or py + s.height <= 0: continue
        if lay == 2: dm.add(s, px, py, m[1])
        if os.environ.get('MASK_ONLY'): continue
        img.alpha_composite(s, (max(0, px), max(0, py)), (max(0, -px), max(0, -py)))
    dm.save(name)
    if os.environ.get('MASK_ONLY'): return
    img = img.convert('RGB')

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
    meta_w = dict(w=W, h=H, tile=round(TILE / RES, 4), res=RES, inset=[190, 190, 190, 200], music=old.get('music', 123), tiles=tiles)
    if old.get('decor'): meta_w['decor'] = old['decor']
    import sprio
    sprio.update(lambda S: S['worlds'].__setitem__(name, meta_w))
    print(name, 'done', (X, Y), len(tiles), 'tiles', round(tot / 1e6, 1), 'MB', flush=True)


if __name__ == '__main__':
    a = sys.argv[1:]
    build(next((int(x) for x in a if x.isdigit()), 54))
