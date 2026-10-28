"""0.60: the spell fusions' icons (sp_sf_<id> in icons3, full spell icons: frame[7] = 1). For the Dofus classes, the
client's own icon of the real spell the fusion is named after (clips/spells/icons/up/<n>.swf, white print) on the class's
background (the colour LUT of build_spellicons21); the Roublard and the Brigandin (no Retro icons) get their two
spells' icons split along a glowing diagonal. Every fusion icon wears a gold / violet ring and a little 4-point star.
The fusions added after 0.60 (in content.json, not in fusions060: 0.95 the Pwout de Cawotte + Cawotte) get their two
spells' icons split the same way; name fusion ids to build only those.
usage: python tools/assets/build_fusionicons060.py [fusion id…]"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import build_icons20 as B, build_spellicons21 as SI, fusions060 as F6

G = f'{ROOT}/game'
W, H = SI.W, SI.H


def atlas_icon(SPR, key):
    if key in SPR.get('icons2', {}):
        f = SPR['icons2'][key]; im = Image.open(f'{G}/assets/ui/icons2.webp').convert('RGBA')
    else:
        f = SPR['icons3'][key]; pg = f[8] if len(f) > 8 else 0
        im = Image.open(f'{G}/assets/ui/icons3{"_" + str(pg) if pg else ""}.webp').convert('RGBA')
    return im.crop((f[0], f[1], f[0] + f[2], f[1] + f[3])).resize((W, H), Image.LANCZOS)


def ring(im):
    """the fusion's mark: a gold -> violet ring with a soft glow, and a 4-point star at the top right"""
    S = 4; big = Image.new('RGBA', (W * S, H * S)); d = ImageDraw.Draw(big)
    cx, cy, r = W * S / 2, H * S / 2, W * S * 0.455
    for i in range(72):   # (a ring of short arcs, its colour turning from gold to violet and back)
        t = abs(((i / 72) * 2) % 2 - 1); col = tuple(int(a + (b - a) * t) for a, b in zip((255, 205, 70), (176, 110, 255))) + (255,)
        d.arc((cx - r, cy - r, cx + r, cy + r), i * 5 - 90, i * 5 - 84, fill=col, width=int(W * S * 0.045))
    glow = big.filter(ImageFilter.GaussianBlur(W * S * 0.02))
    out = im.resize((W * S, H * S), Image.LANCZOS); out.alpha_composite(glow); out.alpha_composite(big)
    sx, sy, R = W * S * 0.80, H * S * 0.20, W * S * 0.16   # the star (0.85: a bit bigger, was 0.13 at 0.82 / 0.18)
    star = lambda x, y, r, w: [(x + (r if k % 2 == 0 else r * 0.28) * np.cos(np.pi / 4 * k - np.pi / 2), y + (r if k % 2 == 0 else r * 0.28) * np.sin(np.pi / 4 * k - np.pi / 2)) for k in range(8)]
    st = Image.new('RGBA', out.size); sd = ImageDraw.Draw(st); sd.polygon(star(sx, sy, R, 1), fill=(255, 246, 200, 255), outline=(120, 60, 20, 255), width=int(S * 3))
    # 0.85: small sparkles round the star: tiny 4-point glints and dots, gold and violet, soft glow
    sp = Image.new('RGBA', out.size); pd = ImageDraw.Draw(sp)
    for a, d, r, col in ((200, 1.55, 0.30, (255, 236, 160, 255)), (250, 1.45, 0.20, (214, 180, 255, 255)), (300, 1.6, 0.24, (255, 246, 200, 255)), (140, 1.5, 0.16, (214, 180, 255, 255)), (20, 1.35, 0.14, (255, 236, 160, 255))):
        x, y = sx + np.cos(np.radians(a)) * R * d, sy + np.sin(np.radians(a)) * R * d
        if r >= 0.2: pd.polygon(star(x, y, R * r, 1), fill=col)
        else: pd.ellipse((x - R * r * 0.5, y - R * r * 0.5, x + R * r * 0.5, y + R * r * 0.5), fill=col)
    out.alpha_composite(sp.filter(ImageFilter.GaussianBlur(S * 2.5))); out.alpha_composite(sp)
    out.alpha_composite(st.filter(ImageFilter.GaussianBlur(S * 3))); out.alpha_composite(st)
    return out.resize((W, H), Image.LANCZOS)


def split(a, b):
    """two icons along a diagonal, the seam glowing"""
    yy, xx = np.mgrid[0:H, 0:W]; m = (xx + yy) < (W + H) / 2
    A, Bm = np.asarray(a).copy(), np.asarray(b)
    A[~m] = Bm[~m]; out = Image.fromarray(A)
    seam = Image.new('RGBA', (W, H)); sd = ImageDraw.Draw(seam); sd.line((W, 0, 0, H), fill=(255, 240, 190, 255), width=5)
    out.alpha_composite(seam.filter(ImageFilter.GaussianBlur(5))); out.alpha_composite(seam)
    return out


def main(only=()):
    SPR = json.load(open(f'{G}/data/sprites.json')); C = json.load(open(f'{G}/data/content.json', encoding='utf-8'))
    todo = dict(F6.F, **{f['id']: (f['cls'], f['src'][0], f['src'][1], f['kind'], None, None) for f in C['spellFusions'] if f['id'] not in F6.F})
    if only: todo = {k: v for k, v in todo.items() if k in only}
    back = SI.render({'b3': f'{ROOT}/raw/rc/clips/spells/icons/back/3.swf'}, 200)['b3'].resize((W, H), Image.LANCZOS)
    ref = np.asarray(atlas_icon(SPR, 'sp_160'))
    yy, xx = np.mgrid[0:H, 0:W]; inner = ((xx - W / 2) ** 2 + (yy - H / 2) ** 2) < (0.33 * W) ** 2
    ys, xs = np.where((ref[..., :3].min(-1) > 225) & inner); span = max(xs.max() - xs.min(), ys.max() - ys.min())
    nums = {v[5] for v in todo.values() if v[5]}
    glyphs = SI.render({str(n): f'{SI.UP}/{n}.swf' for n in nums}, span)
    bgs, new = {}, {}
    for fid, v in todo.items():
        cls, a, b, kind, n = v[0], v[1], v[2], v[3], v[5]
        if n:
            if cls not in bgs:
                cl = next(c for c in C['classes'] if c['id'] == cls)
                bgs[cls] = SI.lut_for([atlas_icon(SPR, 'sp_' + str(C['spells'][s]['icon'])) for s in cl['spells'] if 'sp_' + str(C['spells'][s]['icon']) in SPR['icons2']], back)
            g = glyphs[str(n)]; s = span / max(g.size); g = g.resize((max(1, round(g.width * s)), max(1, round(g.height * s))), Image.LANCZOS)
            im = bgs[cls].copy(); im.alpha_composite(g, ((W - g.width) // 2, (H - g.height) // 2))
        else:
            im = split(atlas_icon(SPR, 'sp_' + str(C['spells'][a]['icon'])), atlas_icon(SPR, 'sp_' + str(C['spells'][b]['icon'])))
        new[f'sp_sf_{fid}'] = ring(im)
    if not only: new['it_82_27'] = B.render(['it_82_27'])['it_82_27']   # (Horloge's turning dials)
    B.merge(new)
    import sprio
    def full(S_):
        for k in new:
            if k.startswith('sp_sf_'): S_['icons3'][k][7] = 1
    sprio.update(full)
    print('fusion icons', len(new))


if __name__ == '__main__':
    main(tuple(_sys.argv[1:]))
