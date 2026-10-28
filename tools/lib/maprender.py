"""Dofus Retro maps rendered from the client's own vector graphics, at any resolution.
Map data: the client map SWFs (data/maps/<id>_<date>X.swf: size, background, music, encrypted cell data) + the keys
of the StarLoco emulator database (work/sl.db). Ground and object graphics: clips/gfx/g*.swf and o*.swf, rendered with
FFDec once per (symbol, frame, rotation, flip, resolution) and cached as PNG in work/symcache.
A map is drawn like the client's MapHandler: cells in rows of 15 / 14 (53 x 27 px diamonds, levels 20 px high),
grounds (rotated / flipped / sloped), then the object layer 1, then the object layer 2 in cell order; the visible
window is 742 x 432 px (the neighbour maps continue the edge cells)."""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import sys, os, re, json, glob, sqlite3, math
from urllib.parse import unquote
import swflib as S, stage as ST
from PIL import Image
import numpy as np

RAW = f'{ROOT}/raw/rc'
GFX = f'{RAW}/clips/gfx'
WORK = f'{ROOT}/work'
CACHE = f'{WORK}/symcache'
CW, CHW, CHH, LH = 53.0, 26.5, 13.5, 20.0
MAPW, MAPH = 742.0, 432.0
HASH = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_'
HX = {c: i for i, c in enumerate(HASH)}

# ---------------------------------------------------------------- map data
_info = None


def map_files():
    out = {}
    for f in os.listdir(f'{RAW}/data/maps'):
        m = re.match(r'(\d+)_(\d+)(X?)\.swf$', f)
        if m: out[int(m.group(1))] = f
    return out


def infos():
    """{map id: {w, h, bg, music, outdoor, x, y, sa, file}} (cached in work/mapinfo.json)"""
    global _info
    if _info is not None: return _info
    p = f'{WORK}/mapinfo.json'
    if os.path.exists(p):
        _info = {int(k): v for k, v in json.load(open(p)).items()}; return _info
    import lang2json as LJ
    MA = json.load(open(f'{WORK}/lang_json/maps_fr.json'))['MA']['m']
    out = {}
    for mid, f in sorted(map_files().items()):
        try: G = LJ.convert(f'{RAW}/data/maps/{f}')
        except Exception as e: print('bad', f, e); continue
        L = MA.get(str(mid), {})
        out[mid] = dict(w=G.get('width'), h=G.get('height'), bg=G.get('backgroundNum') or 0, music=G.get('musicId'), amb=G.get('ambianceId'),
                        outdoor=bool(G.get('bOutdoor')), x=L.get('x'), y=L.get('y'), sa=L.get('sa'), file=f, n=len(G.get('mapData') or ''))
    json.dump(out, open(p, 'w')); _info = out
    return out


_db = None


def db():
    global _db
    if _db is None: _db = sqlite3.connect(f'{WORK}/sl.db')
    return _db


def decrypt(data, key):
    if not key: return unquote(data, encoding='latin-1')
    k = unquote(''.join(chr(int(key[i:i + 2], 16)) for i in range(0, len(key), 2)), encoding='latin-1')
    c = int('0123456789ABCDEF'[sum(ord(ch) % 16 for ch in k) % 16], 16) * 2
    out = ''.join(chr(int(data[i:i + 2], 16) ^ ord(k[(i // 2 + c) % len(k)])) for i in range(0, len(data), 2))
    return unquote(out, encoding='latin-1')


_plain = None


def cells_of(mid):
    """decoded cells (list of dicts) of a map, or None when its data / key is missing"""
    global _plain
    r = db().execute('select key, mapData, width, heigth from maps where id=?', (mid,)).fetchone()
    if not r: return None
    key, data, w, h = r
    if _plain is None:   # (0.51: the maps whose key does not open their data, recovered by crack_maps51.py)
        _plain = json.load(open(f'{WORK}/map_plain.json')) if os.path.exists(f'{WORK}/map_plain.json') else {}
    plain = data and all(ch in HX for ch in data[:40]) and not all(ch in '0123456789abcdefABCDEF' for ch in data[:40])
    try: s = _plain.get(str(mid)) or (data if plain or not key else decrypt(data, key))
    except Exception: return None
    if not s or len(s) % 10 or any(ch not in HX for ch in s[:50]): return None
    out = []
    for i in range(0, len(s), 10):
        v = [HX.get(ch, 0) for ch in s[i:i + 10]]
        out.append(dict(
            active=(v[0] & 32) >> 5, los=v[0] & 1, groundRot=(v[1] & 48) >> 4, level=v[1] & 15, mov=(v[2] & 56) >> 3,
            ground=((v[0] & 24) << 6) + ((v[2] & 7) << 6) + v[3], slope=(v[4] & 60) >> 2, groundFlip=(v[4] & 2) >> 1,
            o1=((v[0] & 4) << 11) + ((v[4] & 1) << 12) + (v[5] << 6) + v[6], o1Rot=(v[7] & 48) >> 4, o1Flip=(v[7] & 8) >> 3,
            o2Flip=(v[7] & 4) >> 2, o2Inter=(v[7] & 2) >> 1, o2=((v[0] & 2) << 12) + ((v[7] & 1) << 12) + (v[8] << 6) + v[9]))
    return out, w, h


def cell_xy(cells, w):
    """screen position of every cell (client MapHandler.build)"""
    out = []; lim = w - 1; ix = -1; row = 0; half = 0.0
    for c in cells:
        if ix == lim:
            ix = 0; row += 1
            if half == 0: half = CHW; lim -= 1
            else: half = 0.0; lim += 1
        else: ix += 1
        out.append((ix * CW + half, row * CHH - LH * (c['level'] - 7)))
    return out


# ---------------------------------------------------------------- symbols
_idx = None


def sym_index():
    global _idx
    if _idx is not None: return _idx
    p = f'{WORK}/symindex.json'
    if os.path.exists(p): _idx = json.load(open(p)); return _idx
    out = {}
    for f in sorted(glob.glob(f'{GFX}/*.swf')):
        b = os.path.basename(f)
        if b == 'cell.swf': continue
        kind = b[0]
        for name in S.exports(S.read_swf(f)['tags']):
            if name.isdigit(): out[f'{kind}{name}'] = b
    json.dump(out, open(p, 'w')); _idx = out
    return out


def rot_mat(rot, flip):
    """local matrix [a, b, c, d] of a ground / object-1 layer: rotation by 90° steps (with the client's 51.85 / 192.86
    scales that keep the isometric diamond), horizontal flip"""
    sx, sy = 1.0, 1.0
    if rot % 2: sx, sy = 0.5185, 1.9286
    if flip: sx = -sx
    a = math.radians(rot * 90); ca, sa = round(math.cos(a), 6), round(math.sin(a), 6)
    return [sx * ca, sx * sa, -sy * sa, sy * ca]


def sym_key(kind, gid, frame, rot, flip, res):
    return f'{kind}{gid}_{frame}_{rot}_{flip}_{res:g}'


def ensure_symbols(needs, res):
    """needs: set of (kind, gid, frame, rot, flip) -> renders the missing ones (one FFDec run per source file)"""
    os.makedirs(CACHE, exist_ok=True)
    meta_p = f'{CACHE}/meta.json'
    meta = json.load(open(meta_p)) if os.path.exists(meta_p) else {}
    idx = sym_index(); byfile = {}
    for kind, gid, frame, rot, flip in needs:
        k = sym_key(kind, gid, frame, rot, flip, res)
        if k in meta: continue
        f = idx.get(f'{kind}{gid}')
        if not f: meta[k] = None; continue
        job = dict(key=k, sym=str(gid), zoom=res, frames=[frame], n=frame + 1)
        if rot or flip: job['mat'] = rot_mat(rot, flip)
        byfile.setdefault(f, []).append(job)
    todo = sum(len(v) for v in byfile.values())
    if todo: print('render symbols', todo, flush=True)
    for f, jobs in byfile.items():
        for i in range(0, len(jobs), 400):
            part = jobs[i:i + 400]
            src = f'{GFX}/{f}'   # (0.52: the ESRGAN bitmaps of hd_gfx52.py were tried and dropped: they looked worse in game)
            res_ = ST.stage_batch([(src, part)], f'{WORK}/symwork_{os.getpid()}', prune=True)
            new = {}
            for job in part:
                r = res_.get(job['key'])
                if not r or r['meta'].get('error'): continue   # a failed run: try again next time
                im = r['imgs'][0] if r['imgs'] else None
                if im is None or not im.getbbox(): new[job['key']] = None; continue
                c, ox, oy = ST.crop(im, r['meta']['origin'])
                if job['key'][0] == 'o': c = strip_red(c, int(job['sym']))
                c.save(f'{CACHE}/{job["key"]}.png'); new[job['key']] = [ox, oy]
            # merge with what other processes may have added meanwhile
            try: import fcntl
            except ImportError: fcntl = None
            with open(meta_p + '.lock', 'w') as lk:
                fcntl and fcntl.flock(lk, fcntl.LOCK_EX)
                cur = json.load(open(meta_p)) if os.path.exists(meta_p) else {}
                tmp = f'{meta_p}.{os.getpid()}.tmp'
                cur.update(new); json.dump(cur, open(tmp, 'w')); os.replace(tmp, meta_p)
            meta.update(cur)
    return meta


MARKS = {2168, 2169, 2170, 2171}   # (0.51: Otomai bamboos with red marks drawn across them, not pure red: red lines on the maps)


def strip_red(im, gid=0):
    """pure red helper shapes of some objects (editor markers) are removed (0.51: with their dark red anti-aliased rim;
    where they crossed the drawing, the hole is filled with the colour around it)"""
    a = np.array(im); ai = a.astype(np.int32)
    red = (a[:, :, 0] > 225) & (a[:, :, 1] < 25) & (a[:, :, 2] < 25) & (a[:, :, 3] > 200)
    if gid in MARKS: red |= (ai[..., 0] - np.maximum(ai[..., 1], ai[..., 2]) > 90) & (ai[..., 0] > 120) & (a[..., 3] > 40)
    if red.sum() <= 20: return im
    import cv2
    near = cv2.dilate(red.astype(np.uint8), np.ones((7, 7), np.uint8)) > 0
    rem = red | (near & (ai[..., 0] - np.maximum(ai[..., 1], ai[..., 2]) > 50))
    al = (a[..., 3] * ~rem).astype(np.uint8)
    closed = cv2.morphologyEx(al, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    w = (al > 128).astype(np.float32)
    num = cv2.GaussianBlur(a[..., :3].astype(np.float32) * w[..., None], (0, 0), 3); den = cv2.GaussianBlur(w, (0, 0), 3)
    a[rem] = 0
    f = rem & (closed > 128) & (den > 0.05)
    a[f, :3] = (num[f] / den[f][:, None]).clip(0, 255).astype(np.uint8); a[f, 3] = closed[f]
    return Image.fromarray(a)


_imc = {}


def seal_sym(im, res):
    """0.52: a ground picture's own hairline gaps (some are drawn in two halves, e.g. 69, 501: a slit down the middle)
    closed with the colour around them: the ground under it showed through as thin light lines"""
    import cv2
    a = np.array(im); al = a[..., 3]; k = int(2 * res) | 1
    closed = cv2.morphologyEx(al, cv2.MORPH_CLOSE, np.ones((k, k), np.uint8))
    g = closed > al
    if not g.any(): return im
    w = (al > 250).astype(np.float32)
    num = cv2.GaussianBlur(a[..., :3].astype(np.float32) * w[..., None], (0, 0), max(1, res)); den = cv2.GaussianBlur(w, (0, 0), max(1, res))
    ok = g & (den > 0.02)
    c = num[ok] / den[ok][:, None]; o = al[ok].astype(np.float32)[:, None] / 255; n = closed[ok].astype(np.float32)[:, None] / 255
    a[ok, :3] = ((a[ok, :3] * o + c * (n - o)) / n).clip(0, 255).astype(np.uint8); a[ok, 3] = closed[ok]
    return Image.fromarray(a)


def sym_img(k):
    if k not in _imc:
        if len(_imc) > 4000: _imc.clear()
        p = f'{CACHE}/{k}.png'
        _imc[k] = Image.open(p).convert('RGBA') if os.path.exists(p) else None
        if _imc[k] is not None and k[0] == 'g': _imc[k] = seal_sym(_imc[k], float(k.rsplit('_', 1)[1]))
    return _imc[k]


def needs_of(mid):
    d = cells_of(mid)
    if not d: return set()
    cells, w, h = d; out = set()
    bg = infos().get(mid, {}).get('bg') or 0
    if bg > 0: out.add(('g', bg, 0, 0, 0))
    for c in cells:
        if c['ground'] > 0: out.add(('g', c['ground'], max(0, c['slope'] - 1), c['groundRot'], c['groundFlip']))
        if c['o1'] > 0: out.add(('o', c['o1'], 0, c['o1Rot'], c['o1Flip']))
        if c['o2'] > 0: out.add(('o', c['o2'], 0, 0, c['o2Flip']))
    return out


def render_map(mid, res, bgcol=(0, 0, 0, 0), margin=0, layers=('ground', 'o1', 'o2')):
    """the map's visible window (742 x 432 px, plus `margin` px around) at `res` pixels per Dofus pixel"""
    d = cells_of(mid)
    W, H = int(round((MAPW + 2 * margin) * res)), int(round((MAPH + 2 * margin) * res))
    im = Image.new('RGBA', (W, H), bgcol)
    if not d: return im
    cells, w, h = d; xy = cell_xy(cells, w)
    meta = ensure_symbols(needs_of(mid), res)

    def put(k, x, y):
        o = meta.get(k)
        if not o: return
        s = sym_img(k)
        if s is None: return
        px = int(round((x + margin) * res - o[0])); py = int(round((y + margin) * res - o[1]))
        if px >= W or py >= H or px + s.width <= 0 or py + s.height <= 0: return
        im.alpha_composite(s, (max(0, px), max(0, py)), (max(0, -px), max(0, -py)))
    bg = infos().get(mid, {}).get('bg') or 0
    if 'ground' in layers or 'bg' in layers:
        if bg > 0: put(sym_key('g', bg, 0, 0, 0, res), 0, 0)   # the map's background picture (a big ground symbol)
    if 'ground' in layers or 'cells' in layers:
        for c, (x, y) in zip(cells, xy):
            if c['ground'] > 0: put(sym_key('g', c['ground'], max(0, c['slope'] - 1), c['groundRot'], c['groundFlip'], res), x, y)
    if 'o1' in layers:
        for c, (x, y) in zip(cells, xy):
            if c['o1'] > 0: put(sym_key('o', c['o1'], 0, c['o1Rot'], c['o1Flip'], res), x, y)
    if 'o2' in layers:
        for c, (x, y) in zip(cells, xy):
            if c['o2'] > 0: put(sym_key('o', c['o2'], 0, 0, c['o2Flip'], res), x, y)
    return im


def objects_of(mid, res):
    """[(layer, x, y, symbol key)] of a map's objects (Dofus px in its window), in the map's drawing order"""
    d = cells_of(mid)
    if not d: return []
    cells, w, h = d; xy = cell_xy(cells, w); out = []
    for c, (x, y) in zip(cells, xy):
        if c['o1'] > 0: out.append((1, x, y, sym_key('o', c['o1'], 0, c['o1Rot'], c['o1Flip'], res)))
    for c, (x, y) in zip(cells, xy):
        if c['o2'] > 0: out.append((2, x, y, sym_key('o', c['o2'], 0, 0, c['o2Flip'], res)))
    return out


if __name__ == '__main__':
    mid = int(sys.argv[1]); res = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
    render_map(mid, res).save(f'{ROOT}/tests/map_{mid}.png')
