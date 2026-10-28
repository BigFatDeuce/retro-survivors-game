"""0.21: class spell icons rebuilt from the client (clips/spells/icons/up/<n>.swf, white print, vector -> HD) on the
class background of the icons already in icons2 (background learnt from them: a per-class colour LUT applied to
icons/back/3.swf). Writes 'sp_<cls>_<n>' entries into icons2.
The up/<n> numbers are icon numbers, not spell ids, for the later classes (Sacrieur 236-254, Pandawa 267-286).
usage: python tools/assets/build_spellicons21.py            (the PLAN below)"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import sys, json
import numpy as np
import stage as ST, build_icons20 as B
from PIL import Image

G = f'{ROOT}/game'
UP = f'{ROOT}/raw/rc/clips/spells/icons/up'
PLAN = {   # class -> {spell id in content: icon number}
    'sacrieur': dict(furie=251, attirance=238, absorption=246, epee_volante=252, assaut=240, dissolution=243),
    'pandawa': dict(karcham=274, flasque_explosive=283, gueule_de_bois=273, lait_de_bambou=280, vague_lame=281, poing_enflamme=268),
    'bandit': dict(persecution=409),   # its spiral was the Sacrieur's Attirance: a target instead
}
W, H = 201, 200


def render(paths, size):
    jobs = []
    for k, p in paths.items():
        _, s = B.size_of(p); jobs.append((p, [dict(key=k, root=True, zoom=size * 2 / s, frames=[0], n=1)]))
    res = ST.stage_batch(jobs, f'{ROOT}/work/spellicons21'); out = {}
    for k in paths:
        im = res[k]['imgs'][0]; out[k] = im.crop(im.getbbox())
    return out


def lut_for(icons, back):
    """per-class colours: back/3 grey level -> mean RGB of the class icons, outside their white print"""
    b = np.asarray(back.convert('RGBA')).astype(np.float32); lum = (b[..., :3].mean(-1)).astype(int)
    acc = np.zeros((256, 3)); n = np.zeros(256)
    yy, xx = np.mgrid[0:H, 0:W]; inner = ((xx - W / 2) ** 2 + (yy - H / 2) ** 2) < (0.36 * W) ** 2
    for ic in icons:
        a = np.asarray(ic.convert('RGBA')).astype(np.float32)
        white = (a[..., :3].min(-1) > 200) & inner
        ok = ~white & (a[..., 3] > 250) & (b[..., 3] > 250)
        np.add.at(acc, lum[ok], a[..., :3][ok]); np.add.at(n, lum[ok], 1)
    have = n > 0; xs = np.arange(256); L = np.zeros((256, 3))
    for c in range(3): L[:, c] = np.interp(xs, xs[have], acc[have, c] / n[have])
    out = L[lum]; o = np.dstack([out, b[..., 3]]).clip(0, 255).astype(np.uint8)
    return Image.fromarray(o, 'RGBA')


# ---------------------------------------------------------------- the Roublard (a Dofus 2.0 class: no Retro icons)
# white prints drawn as shapes (4x supersampled), after its Dofus 2.0 spell list: bomb, water-drop bomb, whirlwind bomb,
# detonator plunger
def _glyph(kind, S=480):
    from PIL import ImageDraw
    im = Image.new('L', (S, S), 0); d = ImageDraw.Draw(im); c = S // 2
    def bomb(cx, cy, r, drop=False):
        if drop:   # a water drop: round bottom, pointed top
            d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=255)
            d.polygon([(cx - r * 0.93, cy - r * 0.35), (cx, cy - r * 1.75), (cx + r * 0.93, cy - r * 0.35)], fill=255)
            top = cy - r * 1.75
        else:
            d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=255); top = cy - r
            d.rectangle((cx - r * 0.32, top - r * 0.28, cx + r * 0.32, top + r * 0.1), fill=255)
            top -= r * 0.28
        d.line([(cx, top), (cx + r * 0.12, top - r * 0.3), (cx + r * 0.38, top - r * 0.5)], fill=255, width=int(r * 0.13), joint='curve')
        sx, sy = cx + r * 0.42, top - r * 0.58   # spark
        for a in range(0, 360, 45):
            import math
            L = r * (0.32 if a % 90 == 0 else 0.2); d.line([(sx, sy), (sx + L * math.cos(math.radians(a)), sy + L * math.sin(math.radians(a)))], fill=255, width=int(r * 0.07))
        # highlight cut-out
        d.ellipse((cx - r * 0.62, cy - r * 0.62, cx - r * 0.22, cy - r * 0.22), fill=0)
        d.ellipse((cx - r * 0.5, cy - r * 0.5, cx - r * 0.34, cy - r * 0.34), fill=255)
    if kind == 'bomb': bomb(c, c + S * 0.08, S * 0.3)
    elif kind == 'bomb_w': bomb(c, c + S * 0.14, S * 0.27, drop=True)
    elif kind == 'bomb_a':
        bomb(c, c + S * 0.08, S * 0.3)
        for i, (w, y) in enumerate(((0.62, 0.0), (0.46, 0.13), (0.3, 0.26))):   # the whirlwind across the ball
            d.arc((c - S * w / 2, c + S * (y - 0.02), c + S * w / 2, c + S * (y + 0.12)), 200, 340, fill=0, width=int(S * 0.035))
    elif kind == 'kaboom':   # detonator box with its plunger
        bw, bh = S * 0.5, S * 0.3; d.rectangle((c - bw / 2, c + S * 0.06, c + bw / 2, c + S * 0.06 + bh), fill=255)
        d.rectangle((c - S * 0.04, c - S * 0.22, c + S * 0.04, c + S * 0.08), fill=255)
        d.rectangle((c - S * 0.2, c - S * 0.28, c + S * 0.2, c - S * 0.2), fill=255)
        d.rectangle((c - bw / 2 + S * 0.05, c + S * 0.13, c + bw / 2 - S * 0.05, c + S * 0.17), fill=0)
        for k in (-1, 1): d.line([(c + k * S * 0.32, c - S * 0.05), (c + k * S * 0.42, c - S * 0.14)], fill=255, width=int(S * 0.03))
        d.line([(c + S * 0.25, c + S * 0.36), (c + S * 0.42, c + S * 0.42)], fill=255, width=int(S * 0.03))
    out = Image.new('RGBA', (S, S), (255, 255, 255, 0)); out.putalpha(im)
    return out.crop(out.getbbox())


CUSTOM = {'roublard': dict(explobombe='bomb', bombe_aqueuse='bomb_w', grisou='bomb_a', kaboom='kaboom')}


def main():
    SPR = json.load(open(f'{G}/data/sprites.json')); C = json.load(open(f'{G}/data/content.json'))
    at2 = Image.open(f'{G}/assets/ui/icons2.webp').convert('RGBA'); F2 = SPR['icons2']
    crop = lambda k: at2.crop((F2[k][0], F2[k][1], F2[k][0] + F2[k][2], F2[k][1] + F2[k][3])).resize((W, H), Image.LANCZOS)
    back = render({'b3': f'{ROOT}/raw/rc/clips/spells/icons/back/3.swf'}, 200)['b3'].resize((W, H), Image.LANCZOS)
    # the print size of the existing icons (white pixels inside the ring)
    ref = np.asarray(crop('sp_160'))
    ys, xs = np.where((ref[..., :3].min(-1) > 225) & (((np.mgrid[0:H, 0:W][1] - W / 2) ** 2 + (np.mgrid[0:H, 0:W][0] - H / 2) ** 2) < (0.33 * W) ** 2))
    span = max(xs.max() - xs.min(), ys.max() - ys.min()); print('print span', span)
    new = {}
    for cls, plan in PLAN.items():
        cl = next(c for c in C['classes'] if c['id'] == cls)
        old = [f'sp_{C["spells"][s]["icon"]}' for s in cl['spells'] if f'sp_{C["spells"][s]["icon"]}' in F2]
        bg = lut_for([crop(k) for k in old], back)
        glyphs = render({str(n): f'{UP}/{n}.swf' for n in plan.values()}, span)
        for sid, n in plan.items():
            g = glyphs[str(n)]; s = span / max(g.size); g = g.resize((max(1, round(g.width * s)), max(1, round(g.height * s))), Image.LANCZOS)
            im = bg.copy(); im.alpha_composite(g, ((W - g.width) // 2, (H - g.height) // 2))
            new[f'sp_{cls}_{n}'] = im
    for cls, plan in CUSTOM.items():
        cl = next(c for c in C['classes'] if c['id'] == cls)
        old = [f'sp_{C["spells"][s]["icon"]}' for s in cl['spells'] if f'sp_{C["spells"][s]["icon"]}' in F2]
        bg = lut_for([crop(k) for k in old], back)
        for sid, kind in plan.items():
            g = _glyph(kind); s = span / max(g.size); g = g.resize((round(g.width * s), round(g.height * s)), Image.LANCZOS)
            im = bg.copy(); im.alpha_composite(g, ((W - g.width) // 2, (H - g.height) // 2)); new[f'sp_{cls}_{kind}'] = im
    items = [(k, at2.crop((f[0], f[1], f[0] + f[2], f[1] + f[3]))) for k, f in F2.items() if k not in new] + list(new.items())
    atlas, pos = ST.pack(items, maxw=4096)
    atlas.save(f'{G}/assets/ui/icons2.webp', 'WEBP', quality=92, method=6)
    F = {}
    for k, im in items:
        x, y, w, h = pos[k]; F[k] = F2[k] if k in F2 and k not in new else [x, y, w, h, w / 2, h / 2, 1.0, 1]
        if k in F2 and k not in new: F[k] = [x, y, w, h] + F2[k][4:]
    import sprio
    sprio.update(lambda S_: S_.__setitem__('icons2', F))
    print('icons2', atlas.size, len(F), sorted(new))


def duree_icon():
    """'Durée' had a boot like 'Points de mouvement': the same framed style (Icon_23's white box) with an hourglass"""
    import swflib as SW
    from PIL import ImageFilter
    p = f'{ROOT}/raw/rc/clips/effectsicons.swf'; ex = SW.exports(SW.read_swf(p)['tags'])
    box = ST.stage_render(p, [dict(key='b', cid=ex['Icon_23'], zoom=8, frames=[0])], f'{ROOT}/work/spellicons21_d')['b']['imgs'][0]
    box = box.crop(box.getbbox()); a = np.asarray(box).copy(); h, w = a.shape[:2]
    # the white inside of the box: everything brighter than the frame, between the frame's edges
    white = (a[..., :3].min(-1) > 235) & (a[..., 3] > 200); ys, xs = np.where(white)
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max(); a[y0:y1 + 1, x0:x1 + 1, :3] = 255; a[y0:y1 + 1, x0:x1 + 1, 3] = 255
    im = Image.fromarray(a, 'RGBA')
    g = render({'g': f'{UP}/96.swf'}, int((y1 - y0) * 0.8))['g']; s = (y1 - y0) * 0.78 / max(g.size)
    g = g.resize((round(g.width * s), round(g.height * s)), Image.LANCZOS); al = g.split()[3]
    out = Image.new('RGBA', g.size, (74, 46, 16, 0)); out.putalpha(al.filter(ImageFilter.MaxFilter(5)))
    fill = Image.new('RGBA', g.size, (196, 136, 52, 255)); fill.putalpha(al)
    out.alpha_composite(fill); cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    im.alpha_composite(out, (cx - g.width // 2, cy - g.height // 2))
    s = B.T / max(im.size)
    return im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)


if __name__ == '__main__':
    main()
    B.merge({'Icon_duree': duree_icon()})
