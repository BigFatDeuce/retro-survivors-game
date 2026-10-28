"""0.60: the 16 Soifs de Sang look bloody: their shop / level-up / Armurerie picture (it_<sym>_sang in icons3) and the
weapon held in the hand (SPR.acci['<sym>_sang'], the R / L views) get blood drawn over the item itself: stains and
drips clipped to the picture (they run down and end in a round drop), a darker rim, a small wet highlight, and a few
drops falling under it. Seeded per weapon: the same blood at every build.
usage: python tools/assets/build_blood060.py"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import json, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import build_icons20 as B

G = f'{ROOT}/game'
SYMS = '6_72 6_66 5_47 5_68 7_59 7_62 4_48 4_80 3_14 3_42 2_47 2_46 8_42 8_45 19_48 19_43'.split()


def bloody(im, seed, k=1.0):
    """im: RGBA item picture -> the same with blood on it; k = drawing scale (1 = a 180 px icon)"""
    im = im.convert('RGBA'); W, H = im.size; rnd = random.Random(seed)
    a = np.asarray(im)[..., 3] > 40
    ys, xs = np.nonzero(a)
    if not len(xs): return im
    top = ys.min() + (ys.max() - ys.min()) * 0.62          # (stains on the upper part: the blade / the head)
    cand = [(x, y) for x, y in zip(xs, ys) if y < top] or list(zip(xs, ys))
    S = 4   # supersampled drawing
    lay = Image.new('L', (W * S, H * S)); d = ImageDraw.Draw(lay)
    free = Image.new('L', (W * S, H * S)); fd = ImageDraw.Draw(free)   # (drops that may leave the item)
    def blob(dr, x, y, r): dr.ellipse(((x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S), fill=255)
    for _ in range(rnd.randint(4, 6)):   # stains
        x, y = rnd.choice(cand); r = rnd.uniform(5, 11) * k
        for _ in range(rnd.randint(3, 6)): blob(d, x + rnd.uniform(-r, r), y + rnd.uniform(-r * 0.6, r * 0.6), rnd.uniform(0.35, 0.8) * r)
    for _ in range(rnd.randint(3, 5)):   # drips running down from a stain
        x, y = rnd.choice(cand); w = rnd.uniform(1.6, 3.2) * k; L = rnd.uniform(14, 34) * k
        for t in np.linspace(0, 1, 24):
            yy = y + t * L; xx = x + np.sin(t * 3 + seed) * 1.2 * k
            if 0 <= int(xx) < W and 0 <= int(yy) < H and a[int(yy), int(xx)]: blob(d, xx, yy, w * (1 - 0.35 * t))
            else:
                blob(fd, xx, yy + 2 * k, w * 1.35); break   # (it falls off the edge: a drop)
        else: blob(d, xx, yy + w * 0.4, w * 1.45)          # (a round drop at its end)
    for _ in range(rnd.randint(2, 4)):   # splashes
        x, y = rnd.choice(cand)
        for _ in range(rnd.randint(3, 7)): blob(d, x + rnd.uniform(-14, 14) * k, y + rnd.uniform(-10, 10) * k, rnd.uniform(0.6, 1.6) * k)
    lay = lay.resize((W, H), Image.LANCZOS); free = free.resize((W, H), Image.LANCZOS)
    m = np.asarray(lay).astype(np.float32) / 255 * a + np.asarray(free).astype(np.float32) / 255 * (1 - a)
    m = np.clip(m, 0, 1)
    base = np.asarray(im).astype(np.float32)
    lum = (base[..., 0] * 0.3 + base[..., 1] * 0.59 + base[..., 2] * 0.11) / 255
    lum = np.where(a, lum, 0.45)
    # blood: deep red, a bit of the item's shading kept, darker on the stain's rim, a wet highlight up-left
    blur = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.6 * k))).astype(np.float32) / 255
    rim = np.clip((m - blur) * 3, 0, 1)
    hl = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2 * k)).transform((W, H), Image.AFFINE, (1, 0, 1.2 * k, 0, 1, 1.2 * k))).astype(np.float32) / 255
    hl = np.clip(m - hl, 0, 1) * (lum > 0.25)
    r = 128 + 62 * lum - 64 * rim; g = 6 + 8 * lum; b = 14 + 10 * lum
    col = np.stack([r, g, b], -1)
    col = col + hl[..., None] * np.array([110, 90, 90])
    alpha = m * 0.92
    out = base.copy()
    out[..., :3] = base[..., :3] * (1 - alpha[..., None]) + col * alpha[..., None]
    out[..., 3] = np.maximum(base[..., 3], alpha * 255)
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def icon(SPR, key):
    f = SPR['icons3'][key]; pg = f[8] if len(f) > 8 else 0
    page = Image.open(f'{G}/assets/ui/icons3{"_" + str(pg) if pg else ""}.webp').convert('RGBA')
    return page.crop((f[0], f[1], f[0] + f[2], f[1] + f[3]))


def main():
    SPR = json.load(open(f'{G}/data/sprites.json'))
    new = {}
    for i, s in enumerate(SYMS):
        im = icon(SPR, f'it_{s}'); new[f'it_{s}_sang'] = bloody(im, 600 + i, max(im.size) / 180)
    B.merge(new)
    import build_acc060 as A, sprio
    acci = {}
    for i, s in enumerate(SYMS):   # the weapon in the hand: its R / L views bloodied the same way
        meta = SPR['acci'][s]; pic = Image.open(f'{G}/assets/acc/i/{s}.webp').convert('RGBA'); views = {}
        for v, fr in meta['f'].items():
            fl = fr if isinstance(fr[0], list) else [fr]
            views[v] = [(bloody(pic.crop((x, y, x + w, y + h)), 600 + i, max(w, h) / 180 * 1.3), ox, oy) for x, y, w, h, ox, oy in fl]
        acci[f'{s}_sang'] = A.write_item(f'{s}_sang', views, zoom=meta.get('zoom') or A.Z)
    sprio.update(lambda S_: S_['acci'].update(acci))
    print('bloody', len(new), 'icons,', len(acci), 'weapon looks')


if __name__ == '__main__':
    A_ = _sys.argv
    if len(A_) > 2 and A_[1] == 'preview':   # (a sheet of every bloody icon, to look at)
        SPR = json.load(open(f'{G}/data/sprites.json')); out = Image.new('RGBA', (8 * 190, 4 * 190), (40, 40, 48, 255))
        for i, s in enumerate(SYMS):
            im = icon(SPR, f'it_{s}'); bl = bloody(im, 600 + i, max(im.size) / 180)
            out.alpha_composite(im, ((i % 4) * 2 * 190, (i // 4) * 190)); out.alpha_composite(bl, ((i % 4) * 2 * 190 + 190, (i // 4) * 190))
        out.save(A_[2]); print(A_[2])
    else: main()
