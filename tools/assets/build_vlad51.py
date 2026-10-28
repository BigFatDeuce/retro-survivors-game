"""0.51: Dark Vlad's zone, made again (the labyrinth was ugly): Dark Vlad's clearing as one grass plain, half the
area of the other zones, with a few trees. Everything is drawn from the client's own pieces, as in the clearing where
Dark Vlad waits in the game (map 325, 'clairière de Dark Vlad', -7,16): its dark grass cells (502), the lighter grass (69) and the glow (4) as soft patches (their
diamonds would show), the light beams (2113 / 2114), its dark
trees (212 / 213 / 222 / 223, 42) and big tree (7509), grass tufts and flowers; a ring of forest around the plain.
Writes assets/worlds/vlad_*.webp, vlad_mini.webp and SPR.worlds['vlad'] (build_worlds20.py vlad comes here).
0.52: 'goultard' = the same clearing taken over by Goultard (the last zone): every piece through a hellish grade (dark
crimson ground, dead red trees, red light beams), dark burnt patches, blood (splashes, sprays and trails of drops) and
glowing cracks; all drawn soft-edged at the final resolution (no seams, no hard cut-outs).
usage: RES=3.0 python tools/assets/build_vlad51.py [seed] [vlad|goultard]   (build_worlds20.py goultard comes here too)"""
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
W, H = 2624, 1528   # Dofus px: half the area of a 5 x 5 zone (3710 x 2160)
DARK = 502   # the clearing's dark grass (as drawn: one ground, unturned, tiles without seams)
TREES = [212, 213, 222, 223]
TUFTS = [(117, 6), (118, 3), (819, 4), (820, 3), (821, 2), (822, 2), (836, 1), (283, 1), (204, 2), (216, 1), (1063, 1)]
BEAMS = [2113, 2114]


# the hellish grade: tones (luminance) mapped from near-black red to a hot ember red, some of the piece's colour kept
HELL_G = np.array([[0, 10, 3, 4], [0.22, 52, 9, 9], [0.45, 108, 20, 15], [0.7, 165, 48, 28], [1.0, 236, 132, 84]], np.float32)
HELL_O = np.array([[0, 14, 3, 4], [0.18, 70, 10, 10], [0.42, 140, 22, 16], [0.7, 205, 56, 28], [1.0, 255, 128, 70]], np.float32)


def hell(rgb, stops, keep, lift=1.08):
    L = np.clip((rgb @ np.array([0.299, 0.587, 0.114], np.float32)) / 255 * lift, 0, 1)
    return np.stack([np.interp(L, stops[:, 0], stops[:, k]) for k in (1, 2, 3)], -1) * (1 - keep) + rgb * keep


def hell_img(im, keep=0.1):   # (the dark trees lifted a little: dark crimson, not black)
    a = np.array(im.convert('RGBA')).astype(np.float32); a[..., :3] = hell(a[..., :3], HELL_O, keep, 1.3)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def gore(A, rng, X, Y, avoid):
    """Goultard's clearing on the graded ground A (float RGB, final px): burnt patches, glowing cracks, blood"""
    R = RES
    # dark burnt patches (soft, multiplied)
    m = np.zeros((H, W), np.float32)
    for _ in range(26):
        x, y = rng.uniform(80, W - 80), rng.uniform(60, H - 60)
        cv2.ellipse(m, (int(x), int(y)), (int(rng.uniform(40, 120)), int(rng.uniform(18, 50))), float(rng.uniform(-20, 20)), 0, 360, 1, -1)
    nz = cv2.GaussianBlur(rng.random((H, W)).astype(np.float32), (0, 0), 6); nz = (nz - nz.mean()) / (nz.std() + 1e-6)
    m = np.clip(cv2.GaussianBlur(m, (0, 0), 16) * 1.2 + nz * 0.12, 0, 1)
    A *= (1 - 0.5 * cv2.resize(m, (X, Y), interpolation=cv2.INTER_CUBIC))[..., None]
    # glowing cracks: jagged lines with forks; a charred rim, a red glow, a hot core
    core = np.zeros((Y, X), np.float32)
    def crack(x, y, a, n, w):
        pts = [(x, y)]
        for _ in range(n):
            a += rng.uniform(-0.55, 0.55); l = rng.uniform(14, 34); x += math.cos(a) * l; y += math.sin(a) * l * 0.55; pts.append((x, y))
            if rng.random() < 0.18 and w > 1: crack(x, y, a + rng.choice([-1, 1]) * rng.uniform(0.6, 1.1), int(n * 0.5), w * 0.6)
        for (x0, y0), (x1, y1), k in zip(pts, pts[1:], range(len(pts))):
            t = 1 - 0.65 * k / len(pts)
            cv2.line(core, (int(x0 * R * 4), int(y0 * R * 4)), (int(x1 * R * 4), int(y1 * R * 4)), 1.0, max(1, int(w * R * t + 0.5)), cv2.LINE_AA, 2)
    for _ in range(14):
        for _t in range(50):
            x, y = rng.uniform(150, W - 150), rng.uniform(120, H - 120)
            if math.hypot((x - W / 2) / 2, y - H / 2) > 140: break
        crack(x, y, rng.uniform(0, math.tau), int(rng.integers(8, 15)), rng.uniform(2.6, 3.8))
    core = cv2.GaussianBlur(core, (0, 0), 0.6 * R)
    rim = cv2.GaussianBlur(core, (0, 0), 3.2 * R); glow = cv2.GaussianBlur(core, (0, 0), 9 * R); halo = cv2.GaussianBlur(core, (0, 0), 3 * R)
    A *= (1 - 0.6 * np.clip(rim * 2.0, 0, 1))[..., None]
    A += glow[..., None] * np.array([255, 52, 10], np.float32) * 2.2 + np.clip(halo * 1.6, 0, 1)[..., None] * np.array([230, 70, 12], np.float32)
    c = np.clip(core * 1.2, 0, 1)[..., None]; A[:] = A * (1 - c) + np.array([255, 150, 40], np.float32) * c
    # blood: splashes (a blob, its drops), sprays and trails of drops, multiplied into the ground (stains, not stickers)
    bl = np.zeros((Y, X), np.float32)
    def blob(x, y, r, k=1.0):
        rr = max(2, int(r * R)); p = rr * 3; sz = 2 * p + 1
        loc = np.zeros((sz, sz), np.float32)
        for _ in range(int(rng.integers(3, 7))):
            ox, oy = rng.normal(0, 0.45) * rr, rng.normal(0, 0.25) * rr
            cv2.ellipse(loc, (int(p + ox), int(p + oy)), (max(1, int(rr * rng.uniform(0.5, 1.0))), max(1, int(rr * rng.uniform(0.25, 0.5)))), float(rng.uniform(-25, 25)), 0, 360, 1, -1)
        nz = cv2.GaussianBlur(rng.random((sz, sz)).astype(np.float32), (0, 0), max(1, rr * 0.18)); nz = (nz - nz.mean()) / (nz.std() + 1e-6)
        loc = np.clip(cv2.GaussianBlur(loc, (0, 0), max(1, rr * 0.15)) + nz * 0.18, 0, 1)
        loc = np.clip((loc - 0.45) * 6, 0, 1); loc = cv2.GaussianBlur(loc, (0, 0), 0.9 * R / 3 + 0.4) * k
        cx, cy = int(x * R) - p, int(y * R) - p
        x0, y0, x1, y1 = max(0, cx), max(0, cy), min(X, cx + sz), min(Y, cy + sz)
        if x1 > x0 and y1 > y0: np.maximum(bl[y0:y1, x0:x1], loc[y0 - cy:y1 - cy, x0 - cx:x1 - cx], out=bl[y0:y1, x0:x1])
    def drop(x, y, r):
        cv2.ellipse(bl, (int(x * R * 4), int(y * R * 4)), (max(2, int(r * R * 4)), max(2, int(r * R * 4 * 0.6))), 0, 0, 360, 0.95, -1, cv2.LINE_AA, 2)
    n = 0
    while n < 60:
        x, y = rng.uniform(70, W - 70), rng.uniform(60, H - 60)
        if avoid(x, y): continue
        n += 1; r = rng.uniform(10, 34); blob(x, y, r)
        for _ in range(int(rng.integers(4, 14))):   # its spray
            a = rng.uniform(0, math.tau); d = r * rng.uniform(1.1, 2.8); drop(x + math.cos(a) * d, y + math.sin(a) * d * 0.55, rng.uniform(0.5, 1.6))
    for _ in range(14):   # trails of drops (something wounded went that way)
        x, y = rng.uniform(150, W - 150), rng.uniform(120, H - 120); a = rng.uniform(0, math.tau)
        for k in range(int(rng.integers(14, 30))):
            a += rng.uniform(-0.25, 0.25); x += math.cos(a) * rng.uniform(7, 14); y += math.sin(a) * rng.uniform(7, 14) * 0.55
            drop(x + rng.normal(0, 2), y + rng.normal(0, 1.2), rng.uniform(0.6, 1.5))
            if rng.random() < 0.08: blob(x, y, rng.uniform(3, 6))
    bl = np.clip(bl, 0, 1)[..., None] * 0.92
    wet = A * np.array([0.3, 0.04, 0.05], np.float32) + np.array([24, 0, 2], np.float32)   # (darker than the red ground: old, soaked in)
    A[:] = A * (1 - bl) + wet * bl
    return A


def build(seed=51, name='vlad'):
    gt = name == 'goultard'
    rng = np.random.default_rng(seed)
    X, Y = int(round(W * RES)), int(round(H * RES))
    rows = range(-3, int(H / MR.CHH) + 4); cols = range(-2, int(W / MR.CW) + 3)
    cells = [(c * MR.CW + (r % 2) * MR.CHW, r * MR.CHH) for r in rows for c in cols]
    needs = {('g', g, 0, 0, 0) for g in (DARK, 69, 4)}
    needs |= {('o', o, 0, 0, f) for o in TREES + [42, 7509] + BEAMS + [t for t, _ in TUFTS] for f in (0, 1)}
    meta = MR.ensure_symbols(needs, RES)

    def layer(pick):   # one ground layer: a cell everywhere, as the client draws the cells
        im = Image.new('RGBA', (X, Y))
        for n, (x, y) in enumerate(cells):
            g, rt = pick(n)
            k = MR.sym_key('g', g, 0, rt, 0, RES); o = meta.get(k); s = MR.sym_img(k)
            if not o or s is None: continue
            px, py = int(round(x * RES - o[0])), int(round(y * RES - o[1]))
            if px >= X or py >= Y or px + s.width <= 0 or py + s.height <= 0: continue
            im.alpha_composite(s, (max(0, px), max(0, py)), (max(0, -px), max(0, -py)))
        return seal(im)
    base = layer(lambda n: (DARK, 0)); light = layer(lambda n: (69, 0)); bright = layer(lambda n: (4, 0))

    # soft masks at 1 px per Dofus px (iso: the patches are twice as wide as tall), then scaled up
    def blobs(n, rx, ry, keep):
        m = np.zeros((H, W), np.float32); out = []
        for _ in range(400):
            if len(out) >= n: break
            x, y = rng.uniform(220, W - 220), rng.uniform(160, H - 200)
            if not keep(x, y) or any(math.hypot((x - a) / 2, y - b) < ry * 1.2 for a, b in out): continue
            out.append((x, y)); r = rng.uniform(0.7, 1.15)
            cv2.ellipse(m, (int(x), int(y)), (int(rx * r), int(ry * r)), float(rng.uniform(-12, 12)), 0, 360, 1, -1)
        return m, out
    mL, spots = blobs(9, 230, 105, lambda x, y: True)
    noise = cv2.GaussianBlur(rng.random((H, W)).astype(np.float32), (0, 0), 60); noise = (noise - noise.mean()) / (noise.std() + 1e-6)
    mL = np.clip(cv2.GaussianBlur(mL, (0, 0), 38) * 1.3 + noise * 0.12, 0, 0.85)
    beams = [(x + rng.uniform(-60, 60), y + rng.uniform(-25, 25)) for x, y in spots[:7]]
    mG = np.zeros((H, W), np.float32); mB = np.zeros((H, W), np.float32)
    for x, y in beams:
        cv2.ellipse(mG, (int(x), int(y)), (95, 45), 0, 0, 360, 1, -1); cv2.ellipse(mB, (int(x), int(y)), (48, 22), 0, 0, 360, 1, -1)
    mG = np.clip(cv2.GaussianBlur(mG, (0, 0), 22), 0, 1) * 0.9; mB = np.clip(cv2.GaussianBlur(mB, (0, 0), 16), 0, 1) * 0.75
    up = lambda m: cv2.resize(m, (X, Y), interpolation=cv2.INTER_CUBIC)[..., None]
    A = np.array(base.convert('RGB')).astype(np.float32)
    for lay, m in ((light, mL), (bright, np.maximum(mG * 0.45, mB))):
        A = A * (1 - up(m)) + np.array(lay.convert('RGB')).astype(np.float32) * up(m)
    # the forest's shade around the clearing (the client's cells there go dark toward the trees)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.minimum(np.minimum(xx, W - xx), np.minimum(yy * 1.6, (H - yy) * 1.3))
    sh = 0.42 + 0.58 * np.clip(d / 260, 0, 1) ** 0.8
    A *= up(sh.astype(np.float32))
    if gt:   # Goultard's: the ground graded (in strips: the picture is big), then the blood and the cracks
        for y0 in range(0, Y, 512): A[y0:y0 + 512] = hell(A[y0:y0 + 512], HELL_G, 0.16)
        A = gore(A, np.random.default_rng(seed + 1), X, Y, lambda x, y: math.hypot((x - W / 2) / 2, y - H / 2) < 70)
    img = Image.fromarray(np.clip(A, 0, 255).astype(np.uint8)).convert('RGBA')

    # objects: flat tufts first, then everything standing in depth order
    objs = []
    for _ in range(520):
        t = [k for k, w in TUFTS for _ in range(w)][rng.integers(sum(w for _, w in TUFTS))]
        objs.append((1, rng.uniform(40, W - 40), rng.uniform(40, H - 30), t, int(rng.integers(2))))
    for x, y in beams: objs.append((2, x, y, BEAMS[rng.integers(2)], int(rng.integers(2))))
    ring = []   # the forest around: trees every ~50 px along the edges, a little in and out
    for x in np.arange(-30, W + 60, 52):
        ring.append((x + rng.uniform(-18, 18), rng.uniform(-10, 70))); ring.append((x + rng.uniform(-18, 18), H + rng.uniform(-20, 110)))
        if rng.random() < 0.6: ring.append((x + rng.uniform(-18, 18), rng.uniform(70, 125)))
    for y in np.arange(40, H + 40, 46):
        for side in (0, 1):
            x0 = rng.uniform(-40, 60) if side == 0 else W - rng.uniform(-40, 60)
            ring.append((x0, y + rng.uniform(-12, 12)))
            if rng.random() < 0.5: ring.append(((rng.uniform(60, 110) if side == 0 else W - rng.uniform(60, 110)), y + rng.uniform(-15, 15)))
    for x, y in ring: objs.append((2, x, y, (TREES + [42])[rng.integers(5)], int(rng.integers(2))))
    inner = []   # a few trees in the plain: small groups, away from the middle (where the runs start)
    for _ in range(300):
        if len(inner) >= 6: break
        x, y = rng.uniform(320, W - 320), rng.uniform(260, H - 260)
        if math.hypot((x - W / 2) / 2, y - H / 2) < 260 or any(math.hypot((x - a) / 2, y - b) < 160 for a, b in inner + beams): continue
        inner.append((x, y))
    for n, (x, y) in enumerate(inner):
        if n < 2: objs.append((2, x, y, 7509, int(rng.integers(2)))); continue
        for k in range(int(rng.integers(1, 4))):
            objs.append((2, x + rng.uniform(-50, 50), y + rng.uniform(-22, 22), TREES[rng.integers(4)], int(rng.integers(2))))
    objs.sort(key=lambda o: (o[0], o[2] if o[0] == 2 else 0))
    graded = {}
    import decormask087 as DM; dm = DM.Mask(X, Y, RES)   # (0.87: the tall scenery, for the areas drawn under it)
    for layer, x, y, o, f in objs:
        k = MR.sym_key('o', o, 0, 0, f, RES); m = meta.get(k); s = MR.sym_img(k)
        if not m or s is None: continue
        if gt: s = graded[k] if k in graded else graded.setdefault(k, hell_img(s, 0.3 if o in BEAMS else 0.2))
        if layer == 1 and math.hypot((x - W / 2) / 2, y - H / 2) < 60: continue
        px, py = int(round(x * RES - m[0])), int(round(y * RES - m[1]))
        if px >= X or py >= Y or px + s.width <= 0 or py + s.height <= 0: continue
        if layer == 2: dm.add(s, px, py, m[1])
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
    meta_w = dict(w=W, h=H, tile=round(TILE / RES, 4), res=RES, inset=[130, 130, 100, 150], music=old.get('music', 119), tiles=tiles)
    if old.get('decor'): meta_w['decor'] = old['decor']
    import sprio
    sprio.update(lambda S: S['worlds'].__setitem__(name, meta_w))
    print(name, 'done', (X, Y), len(tiles), 'tiles', round(tot / 1e6, 1), 'MB', flush=True)


def seal(t):
    import build_worlds20 as B
    B.RES = RES
    return B.seal(t)


if __name__ == '__main__':
    a = sys.argv[1:]
    build(next((int(x) for x in a if x.isdigit()), 51), next((x for x in a if not x.isdigit()), 'vlad'))
