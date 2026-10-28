"""v2.0 HD characters: the class sheets (assets/chars/<key>.webp + <key>_m.webp colour masks) re-rendered natively from the
client's vector sprites (clips/sprites/<sid>.swf) at a higher zoom (v1.x: 3.2).

The frames kept by the v1 sheets are found again by matching (every frame of each animation rendered at the old zoom,
the closest one wins), so the animations, their timing and the accessory anchors (SPR.chars[key].anims[a].anc, in Dofus
units) stay exactly the same; only the pictures and their offsets change.
Passes: base = colour zones black (GAC.applyColor zones 1-3), then zone k white -> mask channel k (out = base + mask * colour).
'<sid>_h' = the hat variant (head clips *_tete on their short-hair frame). Usage: build_chars20.py ZOOM key..."""
import sys as _sys, os as _os, re
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import sys, os, json, math
import swflib as S, timeline as TL, stage as ST
from PIL import Image, ImageChops
import numpy as np

G = f'{ROOT}/game'
RAW = f'{ROOT}/raw/rc/clips/sprites'
WORK = f'{ROOT}/work/chars20'
HEADS = {'R_tete', 'L_tete', 'L_Tete', 'F_tete', 'B_tete', 'S_tete'}
BLACK = ((0, 0, 0, 256), (0, 0, 0, 0))
WHITE = ((0, 0, 0, 256), (255, 255, 255, 0))


def place_with_cx(tag, cx):
    p = S.parse_place(tag)
    return S.make_place2(p['depth'], char=p.get('char'), matrix=p.get('matrix'), cx=cx, name=p.get('name'), move=p.get('move', False),
                         clipdepth=p.get('clipdepth'), ratio=p.get('ratio'))


def head_ids(sw):
    out = set()
    for t in sw['tags']:
        if t.code != S.T_SPRITE: continue
        for x in t.sub:
            if x.code in (S.T_PLACE2, S.T_PLACE3):
                p = S.parse_place(x)
                if p.get('name') in HEADS and p.get('char') is not None: out.add(p['char'])
    return out


HAIR = re.compile('cheveux', re.I)
GONE = ((256, 256, 256, 0), (0, 0, 0, 0))


# 0.91: unnamed hair shapes hidden under a hat too, per sprite file: the Otomaï's bun in his front / side views is a shape
# beside the 'cCra_F_Cheveux' / 'cCra_S_Cheveux' clip (in his other views it is inside the clip): it stuck out over hats
HAIR_SHAPES = {9066: {127, 47}}
# 0.91 (the characters' colours shimmered and were not as in the client): the colour masks are saved LOSSLESS. Lossy
# WebP stores colour at half resolution (YUV 4:2:0) — the three zones are the three channels, so their borders bled into
# one another (dark rims, blotches, a different smear on every frame: the colours flickered while animating); measured on
# a Crâ standing / an Iop running against a lossless render: 1.7-3.4 % of the pixels off by more than 40 levels
MASK_WEBP = dict(lossless=True, quality=80, method=4)


def hide_hair(t, shapes=()):
    """0.64: under a hat the client (Dofus Retro) hides every clip whose instance name holds 'Cheveux' (checked against
    in-game screenshots: a Cra under goggles shows no hair, an Eniripsa — no 'Cheveux' clip — keeps hers under a halo,
    the Enutrof's 'Barbe' and the Xelor's locks stay): those placements (and later moves at their depth) go fully
    transparent and scaled to nothing. The unnamed line / shade shape the client draws over that fill stays, as in the
    client (a woman under a witch hat shows those faint brown strands beside her face): mostly under the hat"""
    if t.code != S.T_SPRITE or not t.sub: return t
    hid, sub, ch = set(), [], False
    for x in t.sub:
        if x.code in (S.T_PLACE2, S.T_PLACE3):
            p = S.parse_place(x); d = p['depth']
            if (p.get('name') and HAIR.search(p['name'])) or (p.get('char') in shapes and not p.get('move')): hid.add(d)
            elif p.get('char') is not None and not p.get('move'): hid.discard(d)
            if d in hid:
                m = p.get('matrix') or [1.0, 0.0, 0.0, 1.0, 0.0, 0.0]   # (scaled to nothing as well: an alpha of 0 alone left a faint ghost in the renders)
                x = S.make_place2(d, char=p.get('char'), matrix=[0.0, 0.0, 0.0, 0.0, m[4], m[5]], cx=GONE, name=p.get('name'), move=p.get('move', False), clipdepth=p.get('clipdepth'), ratio=p.get('ratio')); ch = True
        elif x.code in (S.T_REMOVE, S.T_REMOVE2):
            hid.discard(S.BitReader(x.data).u16() if x.code == S.T_REMOVE2 else S.BitReader(x.data, 2).u16())
        sub.append(x)
    return ST.make_sprite(t.sprite_id, sub) if ch else t


# 0.91 (checked in the official client 1.49.8 — a Crâ under 5 hats: Earmuffs, Adventurer Hat, Kritter, Flud… — and in
# 1.39.8 for every class): no hair is hidden under a hat. Hiding the 'Cheveux' clips (0.65) also left their shade layer,
# a see-through ghost of the hair. A hat variant now only shows the two-frame heads' second frame (the Iop's short flame).
HAIR_KEEP = {'31'}   # (kept for the older call sites; every class keeps its hair now)


def hat_differs(path):
    """0.64: does a hat change this character's own drawing (two-frame heads, or 'Cheveux' clips hidden)? Then its hat
    variants ('_h_r', '_h_s', '_h_x', '_h_e') are rendered apart; else they are the plain sheets"""
    sw = S.read_swf(path); tl = TL.Timeline(sw)
    return any(len(tl.states(h)) >= 2 for h in head_ids(sw))
    for t in sw['tags']:
        if t.code == S.T_SPRITE:
            for x in t.sub or []:
                if x.code in (S.T_PLACE2, S.T_PLACE3):
                    n = S.parse_place(x).get('name')
                    if n and HAIR.search(n): return True
    return False


def make_patch(tl, zone=None, hat=False, heads=(), shapes=()):
    if zone == 0 and os.environ.get('ORIG'): zone = None   # (0.91: ORIG=1 — the base in the sprite's own colours: a class that keeps them, the Otomaï)
    """tagpatch: zone None = untouched colours; 0 = all zones black; k = zone k white, the others black.
    hat: the head clips show their second frame (short hair under a hat) and the 'Cheveux' clips are hidden (hide_hair)"""
    def patch(t):
        t = patch0(t)
        return t   # (0.91: no hair hidden under hats — the client hides none; hide_hair is kept for reference)
    def patch0(t):
        if t.code != S.T_SPRITE: return t
        sid = t.sprite_id
        if sid in heads:   # the head clips are driven by the client: frame 1 = hair, frame 2 = under a hat
            st = tl.states(sid); fi = 1 if hat else 0
            if len(st) >= 2:
                sub = []
                for d in sorted(st[fi]):
                    e = st[fi][d]
                    sub.append(S.make_place2(d, char=e['char'], matrix=e['m'], cx=e.get('cx'), name=e.get('name'), clipdepth=e.get('clip')))
                sub.append(S.Tag(S.T_SHOWFRAME, b''))
                t = ST.make_sprite(sid, sub)
        if zone is None or sid not in tl.colors: return t
        names = tl.colors[sid]; dz = {}; sub = []
        for x in t.sub:
            if x.code in (S.T_PLACE2, S.T_PLACE3):
                p = S.parse_place(x); d = p['depth']
                if p.get('name') in names: dz[d] = names[p['name']]
                elif p.get('char') is not None and not p.get('move'): dz.pop(d, None)
                if d in dz:
                    x = place_with_cx(x, WHITE if dz[d] == zone else BLACK)
            sub.append(x)
        return ST.make_sprite(sid, sub)
    return patch


def render(src, jobs, wd, tl, zone, hat, heads):
    b = os.path.basename(src)[:-4]; shapes = HAIR_SHAPES.get(int(b), ()) if b.isdigit() else ()
    return ST.stage_render(src, jobs, wd, holds=True, tagpatch=make_patch(tl, zone, hat, heads, shapes), prune=True)


def match_frames(old_img, meta, res_old):
    """for every frame of the v1 sheet: (index of the closest re-rendered frame, origin shift old - new) by content,
    whatever the registration point (v1.9 moved some animations' origins, e.g. the weapon attacks)"""
    out = {}
    for a, v in meta['anims'].items():
        r = res_old.get(a)
        if not r or not r['imgs']: out[a] = None; continue
        cands = []
        for i, im in enumerate(r['imgs']):
            if im is None or not im.getbbox(): cands.append(None); continue
            c, ox, oy = ST.crop(im, r['meta']['origin']); cands.append((np.asarray(c).astype(np.int16), ox, oy))
        res = []
        for f in v['f']:
            x, y, w, h, ox, oy = f[:6]
            if w <= 1 and h <= 1: res.append((-1, 0, 0)); continue
            ref = np.asarray(old_img.crop((x, y, x + w, y + h))).astype(np.int16)
            best = None
            for i, cd in enumerate(cands):
                if cd is None: continue
                c, cx_, cy_ = cd
                if abs(c.shape[1] - w) > 3 or abs(c.shape[0] - h) > 3: continue
                hh, ww = min(h, c.shape[0]), min(w, c.shape[1])
                err = np.abs(c[:hh, :ww] - ref[:hh, :ww]).mean()
                if best is None or err < best[0]: best = (err, i, ox - cx_, oy - cy_)
            res.append((best[1], best[2], best[3]) if best and best[0] < 40 else (None, 0, 0))
        out[a] = res
    return out


def shifts(res):
    """the origin shift of an animation: one value if v1.9 moved it as a whole (the usual case), else per frame"""
    d = [(dx, dy) for i, dx, dy in res if i is not None and i >= 0]
    if not d: return [(0, 0)] * len(res)
    mx, my = float(np.median([x for x, _ in d])), float(np.median([y for _, y in d]))
    if all(abs(x - mx) <= 2 and abs(y - my) <= 2 for x, y in d): return [(mx, my)] * len(res)
    return [(dx, dy) if i is not None else (mx, my) for i, dx, dy in res]


def build(key, Z, check=False):
    # always from the v1.9 sheet and its metadata (work/chars_v19, work/sprites_before_chars.json)
    meta = json.load(open(f'{ROOT}/work/sprites_before_chars.json'))['chars'][key]
    sid = key.split('_')[0]; hat = key.endswith('_h'); src = f'{RAW}/{sid}.swf'
    sw = S.read_swf(src); tl = TL.Timeline(sw); ex = S.exports(sw['tags']); low = {k.lower(): k for k in ex}
    heads = head_ids(sw)
    nomask = bool(meta.get('nomask'))
    old = Image.open(f'{ROOT}/work/chars_v19/{key}.webp').convert('RGBA')
    wd = f'{WORK}/{key}'
    anims = {a: low.get(a.lower()) for a in meta['anims']}
    miss = [a for a, s in anims.items() if not s]
    if miss: print(key, 'missing symbols', miss, flush=True)
    # 1) which frames: everything at the old zoom (base pass), matched against the v1 sheet
    jobs = [dict(key=a, sym=s, zoom=meta['zoom'], n=min(80, tl.eff_frames(ex[s]))) for a, s in anims.items() if s]
    r0 = render(src, jobs, wd, tl, None if nomask else 0, hat, heads)
    mres = match_frames(old, meta, r0)
    idx = {a: (None if v is None else [i for i, _, _ in v]) for a, v in mres.items()}
    shf = {a: (None if v is None else shifts(v)) for a, v in mres.items()}
    for a, v in idx.items():   # an unmatched frame: the one after its predecessor's
        if v and None in v:
            n = len(r0[a]['imgs']) if r0.get(a) else 0
            for j, i in enumerate(v):
                if i is None: v[j] = min(n - 1, (v[j - 1] + max(1, round(n / len(v)))) if j and v[j - 1] is not None and v[j - 1] >= 0 else round(j * n / len(v)))
    bad = {a: v for a, v in mres.items() if v is None or any(i is None for i, _, _ in v)}
    if bad: print(key, 'unmatched (guessed)', {a: (v if v is None else sum(1 for i, _, _ in v if i is None)) for a, v in bad.items()}, flush=True)
    moved = {a: (round(v[0][0], 1), round(v[0][1], 1)) for a, v in shf.items() if v and (abs(v[0][0]) > 1.5 or abs(v[0][1]) > 1.5)}
    if moved: print(key, 'v1.9 origin shifts', moved, flush=True)
    if check: return idx
    # 2) the kept frames at the new zoom: base + one pass per colour zone
    jobs = []
    for a, s in anims.items():
        if not s or not idx.get(a): continue
        fr = sorted({i for i in idx[a] if i is not None and i >= 0})
        if fr: jobs.append(dict(key=a, sym=s, zoom=Z, frames=fr))
    passes = [None] if nomask else [0, 1, 2, 3]
    R = {z: render(src, jobs, wd, tl, z, hat, heads) for z in passes}
    base = R[passes[0]]
    items = []; frames = {}
    for job in jobs:
        a = job['key']; rb = base[a]; o = rb['meta']['origin']
        for n, fi in enumerate(job['frames']):
            im = rb['imgs'][n]
            if im is None or not im.getbbox(): continue
            bb = im.getbbox()
            b = im.crop(bb)
            if nomask: m = None
            else:
                b0 = np.asarray(im.crop(bb)).astype(np.int16)
                ch = []
                for z in (1, 2, 3):
                    iz = R[z][a]['imgs'][n]
                    d = (np.asarray(iz.crop(bb)).astype(np.int16)[:, :, :3] - b0[:, :, :3]).mean(axis=2) if iz is not None else np.zeros(b0.shape[:2])
                    ch.append(np.clip(d, 0, 255))
                m = Image.fromarray(np.stack(ch, axis=2).astype(np.uint8), 'RGB')
            items.append(((a, fi), b, m)); frames[(a, fi)] = (o[0] - bb[0], o[1] - bb[1])
    atlas, pos = ST.pack([(k, b) for k, b, m in items], maxw=4096)
    if atlas.height > 4096: print(key, 'atlas tall', atlas.size, flush=True)
    os.makedirs(f'{G}/assets/chars', exist_ok=True)
    atlas.save(f'{G}/assets/chars/{key}.webp', 'WEBP', quality=90, method=6)
    if not nomask:
        ma = Image.new('RGB', atlas.size)
        for k, b, m in items: ma.paste(m, pos[k][:2])
        ma.save(f'{G}/assets/chars/{key}_m.webp', 'WEBP', quality=88, method=6)
    for a, v in meta['anims'].items():
        if not idx.get(a): continue
        F = []
        for j, fi in enumerate(idx[a]):
            f0 = v['f'][j]
            if fi is None or fi < 0 or (a, fi) not in pos: F.append(F[-1] if F else [0, 0, 1, 1, 0, 0]); continue
            x, y, w, h = pos[(a, fi)]; ox, oy = frames[(a, fi)]
            sx, sy = shf[a][j] if shf.get(a) else (0, 0); kz0 = Z / meta['zoom']   # (v1.9's origin shift, at the new zoom)
            F.append([x, y, w, h, round(ox + sx * kz0, 2), round(oy + sy * kz0, 2)] + list(f0[6:]))
        v['f'] = F
    # the accessory anchors are in sheet pixels (their matrices too): scaled with the sheet
    kz = Z / meta['zoom']
    for v in meta['anims'].values():
        for fl in v.get('anc') or []:
            for a in fl:
                for i in range(2, 8): a[i] = round(a[i] * kz, 4 if i < 6 else 3)
    meta['zoom'] = Z; meta['w'], meta['h'] = atlas.width, atlas.height
    import sprio
    sprio.update(lambda SPR: SPR['chars'].__setitem__(key, meta))
    print(key, 'done', atlas.size, os.path.getsize(f'{G}/assets/chars/{key}.webp'), flush=True)


if __name__ == '__main__':
    Z = float(sys.argv[1])
    for k in sys.argv[2:]:
        if k.startswith('check:'): print(build(k[6:], Z, check=True))
        else: build(k, Z)
