"""0.97: the Frigost zone ('frigost'), a composed plain like the flat zones (build_flat068) but laid out by hand in
quarters, from the client's own snow pieces only:
- the snow kit of Kwismas Island (subareas 320 / 321): the ice ground 349 under white snow patches 3335 / 3336, snowy
  firs 3399–3414, ice blocks 3340–3346 / 3359 / 3360 / 3365, ice crystals 3366 / 3368 / 3369–3371 / 3424 / 3425,
  the frozen-lake slabs and cracks 3338 / 3348–3356, snow tufts 3380–3382 / 3393 / 3398 (no gifts, no decorated tree);
- the 2021 snow village pieces of o12.swf, placed by one client map only (14000): the snowy stone keep 6596, the
  ice-block water towers 6598, the ice-crystal lamps 6599, the knight statue 6615, snowmen 6604, snow bunnies 6603,
  snowy rocks 6601, frozen grass 6602, ice crystals 6597 (not its pale ice spikes 6583–6591: they read as planks).
Quarters: the village (north-west: keep, towers, statue square, lamps along its road), the frozen lake (north-east,
snow-free ice with slabs and cracks, ice blocks on its shore), the lost pines (south-west, a dense fir wood), the
crevasse (south-east, ridges of tall ice blocks); a fir border on every edge, the middle left clear (the runs start there),
trodden roads between the quarters (the ice shows through the snow); the whole picture toned down like Kwismas' (GRADE).
Writes assets/worlds/frigost_*.webp, frigost_mini.webp, the decor mask / depth map and SPR.worlds.frigost.
usage: RES=3.0 python tools/assets/build_frigost097.py [--seed=N]   (RES=1 PREVIEW=1: only work/frigost097/frigost.png)"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import sys, os, json, math
import numpy as np, cv2
from PIL import Image
import maprender as MR

G = f'{ROOT}/game'
RES = float(os.environ.get('RES', '3.0'))
TILE, Q = 4096, int(os.environ.get('Q', '80'))
NAME = 'frigost'
W, H = 3635, 2116   # (the flat zones' size, build_flat068)
GROUND = 349
GRADE = dict(gamma=1.6, white=0.86, sat=1.1)   # (Kwismas' snow tone-down, build_worlds20.GRADE, taken further: this snow is whiter — same mean brightness as Kwismas, ~190)
SNOW_BIG, SNOW_SMALL, POWDER = 3335, 3336, [3363, 3362]
FIRS = [3413, 3414, 3401, 3402, 3399, 3407, 3403, 3411, 3412, 3409, 3410, 3404, 3405, 3408, 3406, 3400]
FIRS_BIG = [3413, 3414, 3411, 3412, 3401, 3402, 3407, 3403]
ICE_BLOCKS = [3341, 3344, 3345, 3340, 3342, 3343, 3346, 3360, 3359]
ICE_CRYST = [3366, 3368, 3424, 3425]
CAVE_CRYST = [3369, 3370, 3371]   # (tall teal clusters: the crevasse only)
LAKE_DECALS = [3350, 3352, 3353, 3354, 3355, 3356, 3351, 3349, 3348, 3338]
TUFTS = [3382, 3393, 3380, 3381, 3398, 6602]
SPIKES = [6584, 6589, 6591, 6586, 6585, 6583, 6588, 6590, 6587, 6614]
KEEP, TOWER, LAMP, STATUE, SNOWMAN, BUNNY, ROCK, CRYST2 = 6596, 6598, 6599, 6615, 6604, 6603, 6601, 6597


def seal(t):
    import build_worlds20 as B
    B.RES = RES
    return B.seal(t)


def build(seed=97):
    rng = np.random.default_rng(seed)
    X, Y = int(round(W * RES)), int(round(H * RES))
    every = set(FIRS + ICE_BLOCKS + ICE_CRYST + LAKE_DECALS + TUFTS + CAVE_CRYST + [3365] + POWDER + [SNOW_BIG, SNOW_SMALL, KEEP, TOWER, LAMP, STATUE, SNOWMAN, BUNNY, ROCK, CRYST2])
    meta = MR.ensure_symbols({('g', GROUND, 0, 0, 0)} | {('o', o, 0, 0, f) for o in every for f in (0, 1)}, RES)
    noise = lambda s: (lambda n: (n - n.mean()) / (n.std() + 1e-6))(cv2.GaussianBlur(rng.random((H, W)).astype(np.float32), (0, 0), s))
    up = lambda m: cv2.resize(m.astype(np.float32), (X, Y), interpolation=cv2.INTER_CUBIC)[..., None]

    # ---- the ice ground, as the client draws its cells
    rows = range(-3, int(H / MR.CHH) + 4); cols = range(-2, int(W / MR.CW) + 3)
    im = Image.new('RGBA', (X, Y)); k = MR.sym_key('g', GROUND, 0, 0, 0, RES); o = meta[k]; s = MR.sym_img(k)
    for r in rows:
        for c in cols:
            x, y = c * MR.CW + (r % 2) * MR.CHW, r * MR.CHH
            px, py = int(round(x * RES - o[0])), int(round(y * RES - o[1]))
            if px < X and py < Y and px + s.width > 0 and py + s.height > 0: im.alpha_composite(s, (max(0, px), max(0, py)), (max(0, -px), max(0, -py)))
    A = np.array(seal(im).convert('RGB')).astype(np.float32)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.minimum(np.minimum(xx, W - xx), np.minimum(yy * 1.6, (H - yy) * 1.3))
    A *= up(0.55 + 0.45 * np.clip(d / 320, 0, 1) ** 0.8) * up(1 - 0.05 * np.clip(noise(90), -1, 1))   # (the border's shade)
    img = Image.fromarray(np.clip(A, 0, 255).astype(np.uint8)).convert('RGBA')

    # ---- the plan: where the lake, the roads and the quarters are (Dofus px)
    VIL, LAKE, PINES, CREV, MID = (760, 560), (2820, 640), (760, 1600), (2860, 1590), (W / 2, H / 2)
    ell = lambda p, c, rx, ry: ((p[0] - c[0]) / rx) ** 2 + ((p[1] - c[1]) / ry) ** 2
    lakeN = noise(40)
    in_lake = lambda x, y: ell((x, y), LAKE, 560, 270) + 0.18 * lakeN[int(min(H - 1, max(0, y))), int(min(W - 1, max(0, x)))] < 1
    road = np.zeros((H, W), np.float32)
    def line(pts, w):
        P = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            for t in np.linspace(0, 1, 12)[1:]:
                P.append((a[0] + (b[0] - a[0]) * t + rng.uniform(-10, 10), a[1] + (b[1] - a[1]) * t + rng.uniform(-6, 6)))
        cv2.polylines(road, [np.array(P, np.int32)], False, 1.0, w, cv2.LINE_AA)
        return P
    roads = [line([(VIL[0] + 140, VIL[1] + 110), (1180, 820), (1500, 960), MID], 74),
             line([MID, (2140, 900), (2420, 760), (LAKE[0] - 520, LAKE[1] + 40)], 70),
             line([MID, (1560, 1260), (1180, 1440), (PINES[0] + 260, PINES[1] - 120)], 62),
             line([MID, (2140, 1230), (2480, 1420), (CREV[0] - 300, CREV[1] - 80)], 62),
             line([(VIL[0] + 140, VIL[1] + 110), (VIL[0] - 40, VIL[1] + 360), (PINES[0] - 60, PINES[1] - 360)], 56)]
    cv2.ellipse(road, (int(VIL[0] + 120), int(VIL[1] + 120)), (190, 95), 0, 0, 360, 1.0, -1)   # (the statue's square)
    road = cv2.GaussianBlur(road, (0, 0), 9)
    on_road = lambda x, y: road[int(min(H - 1, max(0, y))), int(min(W - 1, max(0, x)))] > 0.25

    objs = []   # (layer, x, y, symbol, flip)
    put = lambda lay, x, y, sym, f=None: objs.append((lay, x, y, sym, int(rng.integers(2)) if f is None else f))
    pick = lambda lst: lst[int(rng.integers(len(lst)))]
    # ---- snow: white patches everywhere but on the lake, thinner on the roads (trodden), denser away from them
    for gy in np.arange(-60, H + 80, 70):
        for gx in np.arange(-80, W + 100, 120):
            x, y = gx + rng.uniform(-50, 50) + (35 if int(gy / 70) % 2 else 0), gy + rng.uniform(-28, 28)
            if in_lake(x, y): continue
            if on_road(x, y):
                if rng.random() < 0.2: put(1, x, y, pick(POWDER))
                continue
            put(1, x, y, SNOW_BIG if rng.random() < 0.72 else SNOW_SMALL)
    for _ in range(90):   # the lake: slabs and cracks on the bare ice
        x, y = LAKE[0] + rng.uniform(-520, 520), LAKE[1] + rng.uniform(-250, 250)
        if in_lake(x, y): put(1, x, y, pick(LAKE_DECALS))

    # ---- the fir border on every edge (inside the inset the player never reaches) and the lost pines' wood
    def fir_row(xs, ys):
        for x in xs:
            for y in ys(): put(2, x + rng.uniform(-22, 22), y, pick(FIRS_BIG if rng.random() < 0.75 else FIRS))
    fir_row(np.arange(-40, W + 60, 62), lambda: (rng.uniform(-30, 20), rng.uniform(50, 120), rng.uniform(140, 190)))
    fir_row(np.arange(-40, W + 60, 62), lambda: (rng.uniform(H - 40, H + 10), rng.uniform(H + 30, H + 120)))
    for y in np.arange(60, H + 40, 44):
        for x in (rng.uniform(-60, 0), rng.uniform(40, 130), rng.uniform(150, 200), W - rng.uniform(-60, 0), W - rng.uniform(40, 130), W - rng.uniform(150, 200)):
            put(2, x, y + rng.uniform(-14, 14), pick(FIRS_BIG))
    pines = 0
    for _ in range(4000):   # the wood: firs in small stands, a few clearings
        if pines >= 150: break
        x, y = PINES[0] + rng.normal(0, 330), PINES[1] + rng.normal(0, 190)
        if not (230 < x < W - 230 and 300 < y < H - 200) or on_road(x, y) or ell((x, y), MID, 700, 380) < 1: continue
        put(2, x, y, pick(FIRS)); pines += 1
        if rng.random() < 0.3: put(2, x + rng.uniform(-70, 70), y + rng.uniform(-30, 30), pick(TUFTS))
    for _ in range(26):   # stray firs over the plain
        x, y = rng.uniform(300, W - 300), rng.uniform(320, H - 260)
        if ell((x, y), MID, 620, 320) < 1 or on_road(x, y) or in_lake(x, y) or ell((x, y), VIL, 520, 330) < 1: continue
        for _ in range(int(rng.integers(1, 4))): put(2, x + rng.uniform(-60, 60), y + rng.uniform(-26, 26), pick(FIRS))

    # ---- the village: the keep, two ice towers, the statue's square with its lamps, the lamps along the road
    put(2, VIL[0] - 150, VIL[1] - 70, KEEP, 0)
    put(2, VIL[0] + 230, VIL[1] - 120, TOWER, 0); put(2, VIL[0] - 300, VIL[1] + 150, TOWER, 1)
    put(2, VIL[0] + 120, VIL[1] + 120, STATUE, 0)
    for a in (0.6, 2.2, 3.7, 5.3): put(2, VIL[0] + 120 + math.cos(a) * 200, VIL[1] + 120 + math.sin(a) * 100, LAMP, 0)
    for P in roads[:2]:
        for i in range(4, len(P) - 2, 5):
            x, y = P[i]; side = 1 if (i // 5) % 2 else -1
            if not in_lake(x, y + side * 62): put(2, x + side * 18, y + side * 62, LAMP, 0)
    for x, y, sym in ((VIL[0] + 360, VIL[1] + 60, SNOWMAN), (VIL[0] - 80, VIL[1] + 260, SNOWMAN), (VIL[0] + 300, VIL[1] + 250, BUNNY),
                      (VIL[0] - 260, VIL[1] - 10, BUNNY), (VIL[0] + 470, VIL[1] - 30, CRYST2), (VIL[0] - 420, VIL[1] + 40, ROCK),
                      (VIL[0] + 40, VIL[1] - 150, ROCK), (1260, 1030, SNOWMAN), (2300, 1050, BUNNY)):
        put(2, x, y, sym)
    for _ in range(14): put(2, VIL[0] + rng.uniform(-420, 520), VIL[1] + rng.uniform(-180, 320), pick(TUFTS))

    # ---- the frozen lake's shore: ice blocks and crystals around it
    for i in range(26):
        a = i / 26 * math.tau + rng.uniform(-0.12, 0.12); r = rng.uniform(1.0, 1.18)
        x, y = LAKE[0] + math.cos(a) * 580 * r, LAKE[1] + math.sin(a) * 285 * r
        if not (210 < x < W - 200 and 220 < y < H - 200) or on_road(x, y): continue
        q = rng.random()
        put(2, x, y, pick([3340, 3342, 3343, 3346, 3360, 3359]) if q < 0.4 else pick([3341, 3344, 3345]) if q < 0.52 else pick(ICE_CRYST))
        for _ in range(int(rng.integers(0, 3))): put(2, x + rng.uniform(-60, 60), y + rng.uniform(-10, 40), pick(TUFTS))
    for _ in range(6):   # a few blocks frozen in the lake
        x, y = LAKE[0] + rng.uniform(-380, 380), LAKE[1] + rng.uniform(-170, 170)
        if in_lake(x, y): put(2, x, y, pick([3359, 3360, 3343, 3346]))

    # ---- the crevasse: ridges of tall ice blocks and ice rocks, crystals and teal clusters between them
    for ridge in range(4):
        cx, cy = CREV[0] + rng.uniform(-300, 300), CREV[1] + rng.uniform(-140, 140); a = rng.uniform(-0.5, 0.5)
        for t in range(int(rng.integers(3, 6))):
            x, y = cx + math.cos(a) * (t - 2) * 70 + rng.uniform(-14, 14), cy + math.sin(a) * (t - 2) * 36 + rng.uniform(-10, 10)
            if on_road(x, y) or not (230 < x < W - 230 and 300 < y < H - 200): continue
            put(2, x, y, pick([3341, 3344, 3345, 3365, 3340, 3342]))
        for _ in range(3): put(2, cx + rng.uniform(-170, 170), cy + rng.uniform(-60, 80), pick(CAVE_CRYST + [CRYST2, 3366, 3368]))
        for _ in range(5): put(2, cx + rng.uniform(-200, 200), cy + rng.uniform(-80, 90), pick(TUFTS))

    # ---- small things everywhere (not in the middle, where the runs start)
    for _ in range(int(W * H / 22000)):
        x, y = rng.uniform(220, W - 220), rng.uniform(260, H - 200)
        if ell((x, y), MID, 260, 130) < 1 or in_lake(x, y): continue
        put(2, x, y, pick(TUFTS) if rng.random() < 0.85 else pick(ICE_CRYST + [ROCK]))

    objs.sort(key=lambda o: (o[0], o[2] if o[0] == 2 else 0))
    import decormask087 as DM; dm = DM.Mask(X, Y, RES)
    for lay, x, y, o, f in objs:
        k = MR.sym_key('o', o, 0, 0, f, RES); m = meta.get(k); s = MR.sym_img(k)
        if not m or s is None: continue
        px, py = int(round(x * RES - m[0])), int(round(y * RES - m[1]))
        if px >= X or py >= Y or px + s.width <= 0 or py + s.height <= 0: continue
        if lay == 2: dm.add(s, px, py, m[1])
        img.alpha_composite(s, (max(0, px), max(0, py)), (max(0, -px), max(0, -py)))
    import build_worlds20 as BW
    img = BW.grade(img, GRADE)
    if os.environ.get('PREVIEW'):
        os.makedirs(f'{ROOT}/work/frigost097', exist_ok=True); img.save(f'{ROOT}/work/frigost097/{NAME}.png'); print('preview', img.size, len(objs), 'objects'); return
    dm.save(NAME)
    for f in os.listdir(f'{G}/assets/worlds'):
        if f.startswith(NAME + '_') and f.endswith('.webp') and f[len(NAME) + 1].isdigit(): os.remove(f'{G}/assets/worlds/{f}')
    tiles = []; tot = 0
    for ty in range(0, Y, TILE):
        for tx in range(0, X, TILE):
            fn = f'{NAME}_{tx // TILE}_{ty // TILE}.webp'
            img.crop((tx, ty, min(X, tx + TILE), min(Y, ty + TILE))).save(f'{G}/assets/worlds/{fn}', 'WEBP', quality=Q, method=6)
            tot += os.path.getsize(f'{G}/assets/worlds/{fn}'); tiles.append([tx // TILE, ty // TILE, fn])
    mini = img.copy(); mini.thumbnail((360, 360), Image.LANCZOS); mini.save(f'{G}/assets/worlds/{NAME}_mini.webp', 'WEBP', quality=82)
    old = json.load(open(f'{G}/data/sprites.json'))['worlds'].get(NAME) or {}
    meta_w = dict(w=W, h=H, tile=round(TILE / RES, 4), res=RES, inset=[200, 200, 200, 210], music=old.get('music', 128), tiles=tiles)
    for k in ('decor', 'depth'):
        if old.get(k): meta_w[k] = old[k]
    import sprio
    sprio.update(lambda S: S['worlds'].__setitem__(NAME, {**meta_w, **{k: v for k, v in S['worlds'].get(NAME, {}).items() if k in ('decor', 'depth')}}))
    print(NAME, 'done', (X, Y), len(tiles), 'tiles', round(tot / 1e6, 1), 'MB', len(objs), 'objects', flush=True)


if __name__ == '__main__':
    build(next((int(a[7:]) for a in sys.argv if a.startswith('--seed=')), 97))
