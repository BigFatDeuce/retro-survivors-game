"""v2.0 HD item pictures added to icons3 (the HD atlas, looked up first): the achievement pictures, the Le Oiram cap redrawn
with its 'M' as bold as on the original small picture (the hairlines of the vector drawing are given a real width),
and any extra item asked on the command line. Same recipe as v1.9: rendered at 2T from the vectors, reduced to T.
Also redraws the worn Le Oiram cap (acc atlas) with the same bolder M."""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import sys, os, json
import swflib as S, timeline as TL, stage as ST
from PIL import Image

G = f'{ROOT}/game'
RAW = f'{ROOT}/raw/rc/clips/items'
T = 180
BIT = {6, 20, 21, 35, 36, 90}
WHITE = lambda w, c: c is not None and len(c) >= 3 and c[0] > 200 and c[1] > 200 and c[2] > 200
LINEPATCH = {'it_16_7': 12}   # item -> minimum width (twips) of its white lines


def shape_patch(minw):
    def f(t):
        if t.code in (S.T_SHAPE, S.T_SHAPE2, S.T_SHAPE3, S.T_SHAPE4): return S.scale_lines(t, 1.0, pred=WHITE, minw=minw)
        return t
    return f


def size_of(path):
    sw = S.read_swf(path); bitmap = bool({t.code for t in sw['tags']} & BIT)
    rs = ST.root_sprite(sw); sw['tags'].append(rs); tl = TL.Timeline(sw)
    b = tl.bounds(ST.ROOT_ID, frames=range(1))
    return bitmap, max(b[1] - b[0], b[3] - b[2]) / 20.0


def render(keys, work=f'{ROOT}/work/icons20'):
    plain, patched = [], []
    for k in keys:
        t, g = k[3:].split('_'); path = f'{RAW}/{t}/{g}.swf'
        if not os.path.exists(path): print('missing', k); continue
        bitmap, size1 = size_of(path)
        if size1 <= 0: continue
        z = (T * 2 / size1) if not bitmap else (T * 0.75 / size1)
        job = (path, [dict(key=k, root=True, zoom=z, frames=[0], n=1)])
        (patched if k in LINEPATCH else plain).append((job, bitmap))
    out = {}
    res = ST.stage_batch([j for j, _ in plain], work) if plain else {}
    for (job, bitmap) in plain: out[job[1][0]['key']] = (res.get(job[1][0]['key']), bitmap)
    for (job, bitmap) in patched:
        k = job[1][0]['key']; r = ST.stage_render(job[0], job[1], work + '_p', tagpatch=shape_patch(LINEPATCH[k]))
        out[k] = (r[k], bitmap)
    ims = {}
    for k, (r, bitmap) in out.items():
        im = r['imgs'][0] if r and r['imgs'] else None
        if im is None or not im.getbbox(): print('empty', k); continue
        im = im.crop(im.getbbox())
        if bitmap:
            import upscale as U
            im = U.upscale(im)
        s = T / max(im.size)
        ims[k] = im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS)
    return ims


def merge(new):
    SPR = json.load(open(f'{G}/data/sprites.json'))
    # 0.31: icons3 is split into pages of at most 4096 x 4096 (icons3.webp, icons3_1.webp…; frame[8] = page)
    F3 = SPR['icons3']; npg = SPR.get('icons3pages', 1)
    pages = [Image.open(f'{G}/assets/ui/icons3{"_" + str(i) if i else ""}.webp').convert('RGBA') for i in range(npg)]
    old = {**SPR['icons'].get('f', SPR['icons']), **SPR['icons2']}
    items = [(k, pages[f[8] if len(f) > 8 else 0].crop((f[0], f[1], f[0] + f[2], f[1] + f[3]))) for k, f in F3.items() if k not in new] + list(new.items())
    F, n, rest = {}, 0, items
    while rest:
        atlas, pos = ST.pack(rest, maxw=4096)
        fit = [(k, im) for k, im in rest if pos[k][1] + pos[k][3] <= 4096]
        if atlas.height > 4096: atlas = atlas.crop((0, 0, atlas.width, 4096))
        atlas.save(f'{G}/assets/ui/icons3{"_" + str(n) if n else ""}.webp', 'WEBP', quality=92, method=6)
        for k, im in fit:
            x, y, w, h = pos[k]
            if k in F3 and k not in new: F[k] = [x, y, w, h, w / 2, h / 2, F3[k][6], F3[k][7] if len(F3[k]) > 7 else 0, n]; continue   # (0.34: keeps the full-icon flag)
            o = old.get(k)
            drawn = (max(o[2], o[3]) / (o[6] if len(o) > 6 and o[6] else 1.0)) if o else 40.0
            F[k] = [x, y, w, h, w / 2, h / 2, round(max(w, h) / drawn, 4), 0, n]
        print('icons3 page', n, atlas.size, len(fit))
        rest = [(k, im) for k, im in rest if k not in F]; n += 1
    for i in range(n, npg):
        p = f'{G}/assets/ui/icons3_{i}.webp'
        if os.path.exists(p): os.remove(p)
    import sprio   # (0.94: only these two entries are written, under sprio's lock: a builder running meanwhile keeps its own)
    sprio.update(lambda S_: S_.update(icons3=F, icons3pages=n))


def oiram_worn():
    """the worn cap (acc atlas, labels R / L) with the same bolder M, pasted over its old frames (same size and origin)"""
    f = f'{ROOT}/raw/rc/clips/sprites/accessories/a1.swf'
    sw = S.read_swf(f); cid = S.exports(sw['tags'])['16_7']; lb = S.labels(TL.Timeline(sw).defs[cid].sub)
    SPR = json.load(open(f'{G}/data/sprites.json')); A = SPR['acc']; z = A['zoom']
    jobs = [dict(key=d, cid=cid, snap=lb[d], zoom=z, frames=[0]) for d in ('R', 'L')]
    r = ST.stage_render(f, jobs, f'{ROOT}/work/oiram_acc', tagpatch=shape_patch(LINEPATCH['it_16_7']))
    acc = Image.open(f'{G}/assets/acc/acc.webp').convert('RGBA')
    for d in ('R', 'L'):
        fr = A['f']['16_7|' + d]; c, ox, oy = ST.crop(r[d]['imgs'][0], r[d]['meta']['origin'])
        x, y, w, h = int(fr[0]), int(fr[1]), int(round(fr[2])), int(round(fr[3]))
        if abs(c.width - w) > 2 or abs(c.height - h) > 2: print('size differs', d, c.size, (w, h)); continue
        acc.paste(Image.new('RGBA', (w, h)), (x, y))
        acc.alpha_composite(c.crop((0, 0, min(w, c.width), min(h, c.height))), (x, y))
    acc.save(f'{G}/assets/acc/acc.webp', 'WEBP', quality=90, method=6)
    print('acc oiram ok', os.path.getsize(f'{G}/assets/acc/acc.webp'))


if __name__ == '__main__':
    keys = sys.argv[1:]
    C = json.load(open(f'{G}/data/content.json'))
    want = set(keys) | {'it_16_7'} | {a['icon'] for a in C.get('achievements', []) if a['icon'].startswith('it_')}
    SPR = json.load(open(f'{G}/data/sprites.json'))
    todo = sorted(k for k in want if k not in SPR['icons3'] or k in LINEPATCH or k in keys)
    print('render', todo)
    merge(render(todo))
    if 'acc' in SPR: oiram_worn()   # (0.68: the big accessory sheets are gone since 0.60: one picture per accessory)
