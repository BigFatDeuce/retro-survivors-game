"""0.30: the class emblems in HD (they were 194-209 px pictures from v1.x). b1..b12 = the client's class symbols
(clips/artworks/symbols/<breed>.swf) rendered at A px. b13 (Brigandin) and b14 (Roublard), classes the client has no
symbol for, are composed from vectors too: the ring of those symbols (darkened: the "black class circle"), a pale disc,
the character's artwork inside it (Brigandin = artworks/big/1155, Roublard = artworks/faces/8000) with the ring in front
of the body, and the head in front of the ring (the Brigandin's bones, the Roublard's hood and bandana stick out).
The art atlases are repacked (assets/art/art_<n>.webp, SPR.art).   usage: python tools/assets/build_emblems30.py [A=520]"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import sys, os, json
import numpy as np
import swflib as S, stage as ST
from PIL import Image, ImageDraw

G = f'{ROOT}/game'
ART = f'{ROOT}/raw/rc/clips/artworks'
WORK = f'{ROOT}/work/emblems30'
# per composed emblem: artwork, disc centre and radius (Dofus units from the artwork's registration point), the head
# ellipse that goes in front of the ring (cx, cy, rx, ry, units) and an optional x / y limit on it
COMPOSED = {
    'b13': dict(src=f'{ART}/big/1155.swf', c=(8, -178), r=70, head=(-27, -198, 70, 80), xmax=27, ymax=-142),
    'b14': dict(src=f'{ART}/faces/8000.swf', c=(4, 2), r=28, head=(4, -12, 60, 45), ymax=8.4),
    'b15': dict(src=f'{ART}/big/9066.swf', c=(14, -138), r=100, head=(24, -246, 82, 52), ymax=-212),   # 0.91: the Otomaï (NPC 914), his bun over the ring
}


def ring_only(work):
    """the symbol frame without the class picture: the four quarters (sprite 2) of symbols/1.swf"""
    sw = S.read_swf(f'{ART}/symbols/1.swf')
    sw['tags'] = [t for t in sw['tags'] if not (t.code in (4, 26, 70) and S.parse_place(t)['depth'] not in (1, 4, 7, 10))]
    os.makedirs(work, exist_ok=True); p = f'{work}/ring.swf'; S.write_swf(sw, p); return p


def without_ring(b, work):
    """0.34: a class symbol without its own ring (six classes have a purple one in the client): put on the common ring"""
    sw = S.read_swf(f'{ART}/symbols/{b}.swf')
    sw['tags'] = [t for t in sw['tags'] if not (t.code in (4, 26, 70) and S.parse_place(t)['depth'] in (1, 4, 7, 10))]
    os.makedirs(work, exist_ok=True); p = f'{work}/content_{b}.swf'; S.write_swf(sw, p); return p


def root_bounds(path):
    import timeline as TL
    sw = S.read_swf(path); sw['tags'].append(ST.root_sprite(sw)); tl = TL.Timeline(sw)
    return tuple(tl.bounds(ST.ROOT_ID, frames=range(1)))


def inner_radius(im):
    """radius of the disc inside the ring: first dark pixel from the centre, median over 16 directions"""
    a = np.array(im); h, w = a.shape[:2]; cx, cy = w / 2, h / 2; rs = []
    for k in range(16):
        an = k * np.pi / 8 + 0.2
        for r in range(10, int(min(w, h) / 2)):
            x, y = int(cx + np.cos(an) * r), int(cy + np.sin(an) * r)
            if a[y, x, 3] > 200 and a[y, x, :3].mean() < 70: rs.append(r); break
    return float(np.median(rs))


def darken(im):
    """the ring in dark blue-black: luminance mapped on a ramp (the white teeth stay light)"""
    a = np.array(im).astype(float); L = a[..., :3].mean(2) / 255
    ramp = np.array([[0, 10, 10, 20], [0.45, 30, 30, 50], [0.75, 80, 80, 110], [1.0, 236, 236, 248]])
    for ch in range(3): a[..., ch] = np.interp(L, ramp[:, 0], ramp[:, ch + 1])
    return Image.fromarray(a.astype(np.uint8))


def disc(size, r):
    """pale lavender disc, lighter in the middle"""
    yy, xx = np.mgrid[0:size, 0:size]; d = np.hypot(xx - size / 2, yy - size / 2) / r
    k = np.clip(d, 0, 1)[..., None]
    col = (np.array([244, 244, 255]) * (1 - k) + np.array([176, 182, 214]) * k)
    a = np.dstack([col, np.where(d <= 1, 255, 0)]).astype(np.uint8)
    return Image.fromarray(a, 'RGBA')


def compose(key, spec, ringim, rin, N, disc_img=None):
    z = rin / spec['r']
    r = ST.stage_batch([(spec['src'], [dict(key=key, root=True, zoom=z, frames=[0], n=1)])], f'{WORK}/{key}', prune=True)[key]
    ch, (ox, oy) = r['imgs'][0], r['meta']['origin']
    px, py = ox + spec['c'][0] * z, oy + spec['c'][1] * z           # disc centre in the artwork picture
    char = Image.new('RGBA', (N, N)); char.alpha_composite(ch, (int(round(N / 2 - px)), int(round(N / 2 - py))))
    out = disc_img.copy() if disc_img is not None else disc(N, rin + 3)   # (0.34: the common cream disc)
    m = Image.new('L', (N, N)); ImageDraw.Draw(m).ellipse([N / 2 - rin - 2, N / 2 - rin - 2, N / 2 + rin + 2, N / 2 + rin + 2], fill=255)
    back = char.copy(); back.putalpha(Image.fromarray((np.array(char)[..., 3] * (np.array(m) / 255)).astype(np.uint8)))
    out.alpha_composite(back); out.alpha_composite(ringim)
    hx, hy, rx, ry = spec['head']; to = lambda ux, uy: (N / 2 + (ux - spec['c'][0]) * z, N / 2 + (uy - spec['c'][1]) * z)
    hm = Image.new('L', (N, N)); x0, y0 = to(hx - rx, hy - ry); x1, y1 = to(hx + rx, hy + ry); ImageDraw.Draw(hm).ellipse([x0, y0, x1, y1], fill=255)
    hm = np.array(hm).astype(float) / 255
    if 'xmax' in spec: hm[:, int(to(spec['xmax'], 0)[0]):] = 0
    if 'ymax' in spec: hm[int(to(0, spec['ymax'])[1]):, :] = 0
    front = char.copy(); front.putalpha(Image.fromarray((np.array(char)[..., 3] * hm).astype(np.uint8)))
    out.alpha_composite(front)
    return out


def global_emblem(ring_out, disc_in, rin, N):
    """0.34: the emblem of the spells every class gets (shop sub-tab): the common ring on the silver of the global spell
    icons, with the client's Dofus egg (core.swf 'Oeuf') in the middle"""
    import build_staticons34 as BS
    BS.PX = int(rin * 1.25)
    egg = BS.render(f'{ROOT}/raw/rc/modules/core.swf', ['Oeuf'], f'{WORK}/egg')['Oeuf']
    a = np.array(disc_in).astype(float); L = a[..., :3].mean(2, keepdims=True) / 255
    a[..., :3] = np.clip(np.array([112, 120, 136]) + L * np.array([96, 94, 86]), 0, 255)   # silver, lighter where the cream was
    out = Image.fromarray(a.astype(np.uint8)); out.alpha_composite(ring_out)
    out.alpha_composite(egg, ((N - egg.width) // 2, (N - egg.height) // 2))
    return out


def main(A=520):
    N = A * 2
    # the ring (arrows included) fills the picture
    rp = ring_only(WORK); probe = ST.stage_batch([(rp, [dict(key='r', root=True, zoom=4, frames=[0], n=1)])], f'{WORK}/probe', prune=True)['r']['imgs'][0]
    zr = 4 * (N - 8) / max(probe.getbbox()[2] - probe.getbbox()[0], probe.getbbox()[3] - probe.getbbox()[1])
    B = root_bounds(rp)   # every layer is rendered in the frame of the common ring, so they line up exactly
    jobs = [(rp, [dict(key='ring', root=True, zoom=zr, frames=[0], n=1, bounds=B)])]
    jobs += [(without_ring(b, WORK), [dict(key=f'b{b}', root=True, zoom=zr, frames=[0], n=1, bounds=B)]) for b in range(1, 13)]
    res = ST.stage_batch(jobs, f'{WORK}/sym', prune=True)
    full = res['ring']['imgs'][0]; ox, oy = full.getbbox()[:2]
    def frame(im):   # (same offset for all: the ring's box, centred in N x N)
        bb = full.getbbox(); o = Image.new('RGBA', (N, N)); o.alpha_composite(im, ((N - (bb[2] - bb[0])) // 2 - bb[0], (N - (bb[3] - bb[1])) // 2 - bb[1])); return o
    ring = frame(full); rin = inner_radius(ring)
    yy, xx = np.mgrid[0:N, 0:N]; outside = (np.hypot(xx - N / 2, yy - N / 2) > rin - 1)
    ra = np.array(ring); ra[..., 3] = (ra[..., 3] * outside).astype(np.uint8); ring_out = Image.fromarray(ra)
    dsc = np.array(ring); dsc[..., 3] = (dsc[..., 3] * ~outside).astype(np.uint8); disc_in = Image.fromarray(dsc)
    new = {}
    for b in range(1, 13):
        o = ring.copy(); o.alpha_composite(frame(res[f'b{b}']['imgs'][0])); new[f'b{b}'] = o
    for k, spec in COMPOSED.items(): new[k] = compose(k, spec, ring_out, rin, N, disc_in)
    new['b0'] = global_emblem(ring_out, disc_in, rin, N)
    new = {k: v.resize((A, A), Image.LANCZOS) for k, v in new.items()}
    os.makedirs(WORK, exist_ok=True)
    for k in ('b0', 'b13', 'b14', 'b15'): new[k].save(f'{WORK}/{k}.png')
    repack(new)


def repack(new):
    """replace some art frames and repack every art atlas (same packing as build_art21)"""
    SPR = json.load(open(f'{G}/data/sprites.json')); F = SPR['art']['f']; sheets = {}
    items = []
    for k, (n, x, y, w, h) in F.items():
        if k in new: items.append((k, new[k])); continue
        if n not in sheets: sheets[n] = Image.open(f'{G}/assets/art/art_{n}.webp').convert('RGBA')
        items.append((k, sheets[n].crop((x, y, x + w, y + h))))
    items += [(k, im) for k, im in new.items() if k not in F]   # (0.34: b0, a new picture)
    for f in os.listdir(f'{G}/assets/art'):
        if f.startswith('art_'): os.remove(f'{G}/assets/art/{f}')
    NF, n, rest = {}, 0, items
    while rest:
        atlas, pos = ST.pack(rest, maxw=4096)
        fit = [(k, im) for k, im in rest if k in pos and pos[k][1] + pos[k][3] <= 4096]
        if atlas.height > 4096: atlas = atlas.crop((0, 0, atlas.width, 4096))
        atlas.save(f'{G}/assets/art/art_{n}.webp', 'WEBP', quality=88, method=6)
        for k, _ in fit: x, y, w, h = pos[k]; NF[k] = [n, x, y, w, h]
        print('sheet', n, atlas.size, len(fit), flush=True)
        rest = [(k, im) for k, im in rest if k not in NF]; n += 1
    import sprio
    def upd(S_): S_['art'] = {'sheets': n, 'f': NF}
    sprio.update(upd)


if __name__ == '__main__':
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 520)
