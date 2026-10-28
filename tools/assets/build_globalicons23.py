"""0.23: icons of the global spells (offered to every class), 'sp_g_<id>' in icons3. No class icon is reused: the client's
spell background (icons/back/3.swf) recoloured silver-violet (a colour no class has), with the client picture that
matches the spell on it (item pictures, the 'Lâcher les gaz' emote print, the hammer print 215 painted as Moon's mallet).
Also writes 'it_g_hammer' (the painted mallet, thrown by Marteau de Moon) and the item pictures the spells draw.
usage: python tools/assets/build_globalicons23.py"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import numpy as np
from PIL import Image, ImageFilter
import build_icons20 as B, build_spellicons21 as SI

W, H = SI.W, SI.H
ITEMS = dict(kokoko='it_46_552', faux='it_22_3', pioche='it_21_1', jeton='it_15_737', cawotte='it_68_31')   # (0.71: + Cawotte)


def silver(back):
    """the class icons' look (light ring on a coloured disc: the Féca LUT over back/3), turned to a cold silver with a
    violet hint, a colour no class has"""
    import json
    SPR = json.load(open(f'{ROOT}/game/data/sprites.json')); F2 = SPR['icons2']; C = json.load(open(f'{ROOT}/game/data/content.json'))
    at2 = Image.open(f'{ROOT}/game/assets/ui/icons2.webp').convert('RGBA')
    crop = lambda k: at2.crop((F2[k][0], F2[k][1], F2[k][0] + F2[k][2], F2[k][1] + F2[k][3])).resize((W, H), Image.LANCZOS)
    cl = next(c for c in C['classes'] if c['id'] == 'feca')
    ref = SI.lut_for([crop(f'sp_{C["spells"][s]["icon"]}') for s in cl['spells'] if f'sp_{C["spells"][s]["icon"]}' in F2], back)
    a = np.asarray(ref).astype(np.float32); l = (a[..., :3] @ np.array([0.3, 0.55, 0.15])) / 255.0
    lo, hi = np.array([34, 28, 52]), np.array([246, 244, 252])
    rgb = lo + (hi - lo) * np.clip(l, 0, 1)[..., None] ** 1.1
    return Image.fromarray(np.dstack([rgb, a[..., 3]]).clip(0, 255).astype(np.uint8), 'RGBA')


def white_print(im):
    """a coloured print -> white with a soft dark rim (the class icons' look)"""
    a = np.asarray(im.convert('RGBA')); al = Image.fromarray(a[..., 3])
    out = Image.new('RGBA', im.size, (40, 26, 60, 0)); out.putalpha(al.filter(ImageFilter.MaxFilter(5)).point(lambda v: v * 0.7))
    w = Image.new('RGBA', im.size, (255, 255, 255, 255)); w.putalpha(al); out.alpha_composite(w); return out


def hammer(size):
    """print 215 (a hammer) painted: stone-grey head, wooden handle, dark outline"""
    g = SI.render({'h': f'{SI.UP}/215.swf'}, size)['h']; a = np.asarray(g).astype(np.float32); al = a[..., 3]
    h, w = al.shape; yy, xx = np.mgrid[0:h, 0:w]
    head = yy < h * 0.47 + (xx / w - 0.45) * h * 0.66   # the head is the upper right block, the handle leaves it bottom-left
    rgb = np.zeros((h, w, 3), np.float32)
    shade = 0.75 + 0.25 * (1 - yy / h)
    rgb[...] = np.array([150, 98, 52]) * shade[..., None]   # wood
    stone = np.array([132, 138, 150]) * (0.7 + 0.45 * (1 - (yy / (h * 0.6)).clip(0, 1)))[..., None]
    rgb[head] = stone[head]
    im = Image.fromarray(np.dstack([rgb, al]).clip(0, 255).astype(np.uint8), 'RGBA')
    pad = 8; out = Image.new('RGBA', (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    rim = Image.new('RGBA', out.size, (34, 22, 14, 0)); m = Image.new('L', out.size, 0); m.paste(Image.fromarray(al.astype(np.uint8)), (pad, pad))
    rim.putalpha(m.filter(ImageFilter.MaxFilter(7))); out.alpha_composite(rim); out.alpha_composite(im, (pad, pad))
    return out.crop(out.getbbox())


def white_detail(im):
    """0.38: an item picture -> a white print that keeps its inner lines (light greys), with the soft dark rim: it reads
    like the class spells' prints instead of a coloured object"""
    a = np.asarray(im.convert('RGBA')).astype(np.float32); l = (a[..., :3] @ np.array([0.3, 0.55, 0.15])) / 255.0
    lo, hi = np.percentile(l[a[..., 3] > 128], [5, 95]) if (a[..., 3] > 128).any() else (0, 1)
    l = np.clip((l - lo) / max(1e-3, hi - lo), 0, 1)
    v = 255 * (0.58 + 0.42 * l ** 0.55)
    w = Image.fromarray(np.dstack([v, v, v * 0.98 + 5, a[..., 3]]).clip(0, 255).astype(np.uint8), 'RGBA')
    al = Image.fromarray(a[..., 3].astype(np.uint8))
    out = Image.new('RGBA', im.size, (40, 26, 60, 0)); out.putalpha(al.filter(ImageFilter.MaxFilter(5)).point(lambda x: x * 0.75))
    out.alpha_composite(w); return out


def main():
    back = silver(SI.render({'b3': f'{ROOT}/raw/rc/clips/spells/icons/back/3.swf'}, 200)['b3'].resize((W, H), Image.LANCZOS))
    pics = B.render(list(ITEMS.values()))
    emo = SI.render({'e': f'{ROOT}/raw/rc/clips/emotes/8.swf'}, 400)['e']
    # the emote picture is a framed square: keep only its light print (the character and the puff)
    a = np.asarray(emo).astype(np.int16); m = (a[..., :3].min(-1) > 175) & (a[..., 0] > a[..., 2] + 10)
    emo_p = Image.fromarray(np.dstack([np.full(m.shape + (3,), 255, np.uint8), (m * 255).astype(np.uint8)]), 'RGBA')
    emo_p = emo_p.crop(emo_p.getbbox())
    ham = hammer(420)
    new = {}
    def put(key, g, frac, glow=False):
        s = W * frac / max(g.size); g = g.resize((max(1, round(g.width * s)), max(1, round(g.height * s))), Image.LANCZOS)
        im = back.copy()
        if glow:   # a dark halo so a coloured item reads on the silver
            sh = Image.new('RGBA', g.size, (30, 18, 50, 0)); sh.putalpha(g.split()[3].filter(ImageFilter.GaussianBlur(5)).point(lambda v: min(255, v * 1.4)))
            im.alpha_composite(sh, ((W - g.width) // 2 + 2, (H - g.height) // 2 + 3))
        im.alpha_composite(g, ((W - g.width) // 2, (H - g.height) // 2)); new[f'sp_g_{key}'] = im
    for k, it in ITEMS.items(): put(k, white_detail(pics[it]), 0.62)   # (0.38: white prints like the class spells)
    # (0.78: no more hammer icon for Moon — sp_g_moon is the client print 366, made by build_moon34 only)
    put('prouts', white_print(emo_p), 0.58)
    for it in ITEMS.values(): new[it] = pics[it]   # the items themselves (thrown nut, orbiting scythes, pickaxe swing)
    s = B.T / max(ham.size); new['it_g_hammer'] = ham.resize((round(ham.width * s), round(ham.height * s)), Image.LANCZOS)
    B.merge(new)
    print(sorted(new))


if __name__ == '__main__':
    main()
