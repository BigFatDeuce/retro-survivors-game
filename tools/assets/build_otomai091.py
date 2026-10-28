"""0.91: the Otomaï's assets (the class itself: tools/content/patch_091.py; his sheets: build_move060 chars 9066 9066_h,
build_still063 9066 9066_h, build_wfront060 9066, build_accfront061 SLOT=2/1 SHEET=_r/_s 9066, fix_flash061).
- icons   : his six spell icons 'sp_oto_<n>' (icons3, full spell icons) = the client's white print
            clips/spells/icons/up/<n>.swf on a teal class background: the Sadida's background (the colour LUT of
            build_spellicons21 learnt from its icons) turned to the Otomaï's hue, light and shade kept
- fusions : his three fusion icons 'sp_sf_<id>' = a client print on that background + the fusion ring
            (build_fusionicons060.ring)
- xscale  : his weapon blows (9066_x / 9066_h_x, anim10R..17R) are the Crâ's clips at the Crâ's size, his own clips (standing,
            runs, casts) are drawn bigger (the NPC is tall): measured on the red potion of his bag, the blows are x0.85 —
            those two sheets are drawn x1.18 (their `zoom` 4.8 / 1.18; build_wfront060 keeps a sheet's zoom when it
            renders it again)
- sounds  : sounds.json chars['9066'] = the male Crâ's (90): the NPC is built on the Crâ's skeleton and his clips call
            the same keys (tools/lib/sndanim27.py 9066: hit_defaut, death, cc_jet…); he has no voice of his own
The emblem b15 is composed by tools/assets/build_emblems30.py (COMPOSED: his artwork artworks/big/9066.swf).
usage: python tools/assets/build_otomai091.py [icons|fusions|sounds|xscale|orig]…   (all by default; run it alone: it writes sprites.json)"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import sys, os, json, colorsys
import numpy as np
from PIL import Image
import build_icons20 as B, build_spellicons21 as SI, build_fusionicons060 as FI
import patch_091 as P

G = f'{ROOT}/game'
W, H = SI.W, SI.H
HUE = 0.49   # the Otomaï's teal (#2f8f8a)


def background(SPR, C):
    back = SI.render({'b3': f'{ROOT}/raw/rc/clips/spells/icons/back/3.swf'}, 200)['b3'].resize((W, H), Image.LANCZOS)
    sad = next(c for c in C['classes'] if c['id'] == 'sadida')
    bg = SI.lut_for([FI.atlas_icon(SPR, 'sp_' + str(C['spells'][s]['icon'])) for s in sad['spells'] if 'sp_' + str(C['spells'][s]['icon']) in SPR['icons2']], back)
    a = np.asarray(bg).astype(np.float32) / 255; out = a.copy()
    for y in range(H):
        for x in range(W):
            h, l, s = colorsys.rgb_to_hls(*a[y, x, :3]); out[y, x, :3] = colorsys.hls_to_rgb(HUE, l, s * 0.9)
    return Image.fromarray((out * 255).clip(0, 255).astype(np.uint8), 'RGBA')


def print_span(SPR):
    ref = np.asarray(FI.atlas_icon(SPR, 'sp_160')); yy, xx = np.mgrid[0:H, 0:W]
    ys, xs = np.where((ref[..., :3].min(-1) > 225) & (((xx - W / 2) ** 2 + (yy - H / 2) ** 2) < (0.33 * W) ** 2))
    return max(xs.max() - xs.min(), ys.max() - ys.min())


def on_bg(bg, g, span):
    s = span / max(g.size); g = g.resize((max(1, round(g.width * s)), max(1, round(g.height * s))), Image.LANCZOS)
    im = bg.copy(); im.alpha_composite(g, ((W - g.width) // 2, (H - g.height) // 2)); return im


def icons(fusions_too=True, spells_too=True):
    SPR = json.load(open(f'{G}/data/sprites.json')); C = json.load(open(f'{G}/data/content.json', encoding='utf-8'))
    bg = background(SPR, C); span = print_span(SPR); new = {}
    nums = (set(P.ICONS.values()) if spells_too else set()) | (set(P.FICONS.values()) if fusions_too else set())
    glyphs = SI.render({str(n): f'{SI.UP}/{n}.swf' for n in nums}, span)
    if spells_too:
        for sid, n in P.ICONS.items(): new[f'sp_oto_{n}'] = on_bg(bg, glyphs[str(n)], span)
    if fusions_too:
        for fid, n in P.FICONS.items(): new[f'sp_sf_{fid}'] = FI.ring(on_bg(bg, glyphs[str(n)], span))
    B.merge(new)
    import sprio
    def full(S_):
        for k in new: S_['icons3'][k][7] = 1   # (full spell icons, like the global spells' and the fusions')
    sprio.update(full); print('icons', sorted(new))


def xscale(k=1.18):
    import sprio
    def up(S_):
        for key in ('9066_x', '9066_h_x'): S_['chars'][key]['zoom'] = round(4.8 / k, 3)
    sprio.update(up); print('weapon blows x', k)


def orig():
    """0.91 (like the Roublard and the Brigandin, the Otomaï keeps his own colours and wears no skin): his sheets are
    rendered again in the sprite's own colours (ORIG=1: build_move060 chars 9066, build_still063 9066, HAT=0
    build_wfront060 9066, then fix_flash061) — here they lose their (meaningless) colour masks, the hat variants and the
    cape / hat front layers go, and the data-only base entry is the standing sheet's"""
    import sprio, copy, glob
    def up(S_):
        C_ = S_['chars']
        for k in ('9066_r', '9066_s', '9066_x'):
            C_[k]['nomask'] = 1; C_[k].pop('fa', None); C_[k].pop('fh', None)
            for a in C_[k]['anims'].values():
                for x in ('fa', 'fd', 'fh', 'hd'): a.pop(x, None)
        for k in [k for k in C_ if k.startswith('9066_h')]: del C_[k]
        m = copy.deepcopy(C_['9066_s']); m.pop('nomask', None)
        for a in m['anims'].values():
            for x in ('src',): a.pop(x, None)
        C_['9066'] = m
    sprio.update(up)
    for f in glob.glob(f'{G}/assets/chars/9066_*'):
        b = os.path.basename(f)
        if b.startswith('9066_h_') or b.endswith('_m.webp') or '_fa' in b or '_fh' in b: os.remove(f)
    print('Otomaï: own colours, no skins:', sorted(os.path.basename(f) for f in glob.glob(f'{G}/assets/chars/9066*')))


def sounds():
    p = f'{G}/data/sounds.json'; S = json.load(open(p, encoding='utf-8'))
    S['chars']['9066'] = {k: v for k, v in S['chars']['90'].items() if not k.startswith('emote')}
    json.dump(S, open(p, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':')); print('sounds 9066', len(S['chars']['9066']))


if __name__ == '__main__':
    what = sys.argv[1:] or ['icons', 'sounds', 'xscale']
    if 'icons' in what: icons()
    elif 'fusions' in what: icons(spells_too=False)
    if 'sounds' in what: sounds()
    if 'xscale' in what: xscale()
    if 'orig' in what: orig()
