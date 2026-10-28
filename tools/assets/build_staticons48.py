"""0.48: the characteristic icons that were not in the client's framed style (Vol de vie, Renvoi, Esquive, Phénix, Borné,
Prospection) redrawn in it: the white box with its grey frame of the effect icons (Icon_23 of clips/effectsicons.swf,
emptied) and a flat drawing in the spirit of the others, drawn as vectors (SVG, rendered by Chromium) — no client
symbol exists for them. Prospection keeps the client's gem (IconPP) without its gold ring.
usage: python tools/assets/build_staticons48.py   -> icons3 'Icon_<id>' + the passives' icons in tools/patch_043 (content)"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import io, numpy as np
from PIL import Image, ImageFilter
import swflib as SW, stage as ST
import build_icons20 as B

W = f'{ROOT}/work/staticons48'
O = 'stroke-linejoin="round" stroke-linecap="round"'
SVG = {   # 100 x 100 drawings
    # a drop of blood, two reds like the shield's two greys, a white shine
    'leech': f'''<path d="M50 6 C 64 30 82 46 82 64 A 32 32 0 0 1 18 64 C 18 46 36 30 50 6 Z" fill="#b3121f" stroke="#4a0008" stroke-width="3.5" {O}/>
      <path d="M50 6 C 64 30 82 46 82 64 A 32 32 0 0 1 50 96 Z" fill="#e0283a"/>
      <path d="M50 6 C 64 30 82 46 82 64 A 32 32 0 0 1 18 64 C 18 46 36 30 50 6 Z" fill="none" stroke="#4a0008" stroke-width="3.5" {O}/>
      <path d="M33 62 C 33 52 38 44 43 38" fill="none" stroke="#fff" stroke-width="6" opacity=".85" {O}/><circle cx="33" cy="72" r="3.6" fill="#fff" opacity=".85"/>''',
    # a spiked shell (the Prespic's back): a dome with a ring of spikes, two browns
    'reflect': f'''<g stroke="#3a2410" stroke-width="3" {O}>
      {''.join(f'<path d="M{50 + 30 * np.cos(a):.1f} {70 - 30 * np.sin(a):.1f} L{50 + 47 * np.cos(a):.1f} {70 - 47 * np.sin(a):.1f} L{50 + 30 * np.cos(a + 0.22):.1f} {70 - 30 * np.sin(a + 0.22):.1f} Z" fill="#e8dcc0"/>' for a in np.linspace(0.12, np.pi - 0.34, 7))}
      <path d="M14 72 A 36 34 0 0 1 86 72 Z" fill="#8a5a2a"/>
      <path d="M50 38 A 36 34 0 0 1 86 72 L 50 72 Z" fill="#b07a3a" stroke="none"/>
      <path d="M14 72 A 36 34 0 0 1 86 72 Z" fill="none"/>
      <path d="M28 66 Q 34 52 44 48 M50 70 L 50 46 M72 66 Q 66 52 56 48" fill="none" stroke-width="2.5"/>
      <path d="M10 74 L 90 74" stroke-width="5"/></g>''',
    # a dodge: an arrow flies through where the character was (a faded outline), the character leans aside
    'evade': f'''<g {O}>
      <g opacity=".35" fill="#7a9ab8"><circle cx="40" cy="26" r="10"/><path d="M28 40 Q 40 34 52 40 L 50 74 L 30 74 Z"/></g>
      <g fill="#3f7fc0" stroke="#183a5a" stroke-width="3"><circle cx="66" cy="30" r="10"/><path d="M56 44 Q 68 38 80 46 L 74 78 L 56 76 Z"/></g>
      <path d="M8 52 L 74 52" stroke="#5a3a1a" stroke-width="4"/><path d="M78 52 L 66 44 L 68 52 L 66 60 Z" fill="#c8c8c8" stroke="#3a3a3a" stroke-width="2.5"/>
      <path d="M8 52 L 2 46 M8 52 L 2 58 M14 52 L 8 46 M14 52 L 8 58" stroke="#d04040" stroke-width="3"/>
      <path d="M84 34 L 94 30 M86 46 L 96 46 M84 58 L 94 62" stroke="#3f7fc0" stroke-width="3"/></g>''',
    # the phoenix potion, simpler: a round flask of glowing orange, a cork, a small flame
    'revive': f'''<g stroke="#4a1a08" stroke-width="3.5" {O}>
      <path d="M40 22 L 60 22 L 60 36 C 78 42 86 54 86 66 A 36 30 0 0 1 14 66 C 14 54 22 42 40 36 Z" fill="#f4f0e8"/>
      <path d="M17 62 C 30 56 70 56 83 62 A 34 28 0 0 1 17 62 Z" fill="#ff6a1e" stroke="none"/>
      <path d="M50 58 C 70 56 80 58 84 62 A 34 28 0 0 1 50 92 Z" fill="#ff9a2a" stroke="none"/>
      <path d="M40 22 L 60 22 L 60 36 C 78 42 86 54 86 66 A 36 30 0 0 1 14 66 C 14 54 22 42 40 36 Z" fill="none"/>
      <rect x="37" y="10" width="26" height="13" rx="3" fill="#a8743a"/>
      <path d="M50 80 C 40 76 42 66 48 62 C 48 68 52 68 52 64 C 58 68 60 76 50 80 Z" fill="#ffe14a" stroke="#c0400a" stroke-width="2.5"/></g>
      <path d="M26 56 C 26 50 30 46 34 44" fill="none" stroke="#fff" stroke-width="5" opacity=".8" {O}/>''',
    # one more spell slot: four slots and a fifth, golden, with a '+'
    'spellslot': f'''<g stroke="#2a2a2a" stroke-width="3" {O}>
      <rect x="8" y="14" width="34" height="34" rx="6" fill="#9a9a9a"/><rect x="58" y="14" width="34" height="34" rx="6" fill="#9a9a9a"/>
      <rect x="8" y="56" width="34" height="34" rx="6" fill="#9a9a9a"/><rect x="58" y="56" width="34" height="34" rx="6" fill="#ffc83a" stroke="#7a4a00"/>
      <path d="M75 63 L 75 83 M65 73 L 85 73" stroke="#fff" stroke-width="7"/>
      <path d="M14 22 L 26 22 M64 22 L 76 22 M14 64 L 26 64" stroke="#d8d8d8" stroke-width="3"/></g>''',
}


def svg_pngs(names, px=600):
    from playwright.sync_api import sync_playwright
    out = {}
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=_os.environ['CHROME']) if _os.environ.get('CHROME') else p.chromium.launch()   # (0.68: Playwright's own Chromium unless CHROME says otherwise)
        pg = b.new_page(viewport={'width': px, 'height': px})
        for k in names:
            pg.set_content(f'<html><body style="margin:0;background:transparent"><svg xmlns="http://www.w3.org/2000/svg" width="{px}" height="{px}" viewBox="0 0 100 100">{SVG[k]}</svg></body></html>')
            out[k] = Image.open(io.BytesIO(pg.screenshot(omit_background=True))).convert('RGBA')
        b.close()
    return out


def empty_box():
    """Icon_23's frame with its inside painted white (as Icon_duree in build_spellicons21)"""
    p = f'{ROOT}/raw/rc/clips/effectsicons.swf'; ex = SW.exports(SW.read_swf(p)['tags'])
    box = ST.stage_render(p, [dict(key='b', cid=ex['Icon_23'], zoom=8, frames=[0])], f'{W}/box')['b']['imgs'][0]
    box = box.crop(box.getbbox()); a = np.asarray(box).copy()
    white = (a[..., :3].min(-1) > 235) & (a[..., 3] > 200); ys, xs = np.where(white)
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max(); a[y0:y1 + 1, x0:x1 + 1, :3] = 255; a[y0:y1 + 1, x0:x1 + 1, 3] = 255
    return Image.fromarray(a, 'RGBA'), (x0, y0, x1, y1)


def gem():
    """the client's Prospection gem (IconPP) without its gold ring: the convex hull of its blue / violet pixels"""
    import cv2
    p = f'{ROOT}/raw/rc/modules/core.swf'
    im = ST.stage_render(p, [dict(key='g', sym='IconPP', zoom=12, frames=[0], n=1)], f'{W}/gem', prune=True)['g']['imgs'][0]
    im = im.crop(im.getbbox()); a = np.asarray(im).astype(int)
    r, g, b, al = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
    h, w = al.shape; yy, xx = np.mgrid[0:h, 0:w]; inner = np.hypot(xx - w / 2, yy - h / 2) < 0.8 * min(w, h) / 2   # (inside the gold ring)
    blue = inner & (al > 200) & (((r < 200) & (b > 200)) | (a[..., :3].min(-1) > 248))   # (the gem: blue / cyan / violet or white facets; the disc is grey 227, the ring gold)
    pts = np.argwhere(blue)[:, ::-1].astype(np.int32); hull = cv2.convexHull(pts)
    m = np.zeros(blue.shape, np.uint8); cv2.fillConvexPoly(m, hull, 255); m = cv2.GaussianBlur(cv2.dilate(m, np.ones((3, 3), np.uint8)), (3, 3), 0)
    out = np.asarray(im).copy(); out[..., 3] = np.minimum(out[..., 3], m)
    o = Image.fromarray(out, 'RGBA')
    rim = Image.new('RGBA', o.size, (24, 26, 80, 0)); rim.putalpha(o.split()[3].filter(ImageFilter.MaxFilter(7)))   # a dark rim, as the other icons' drawings
    rim.alpha_composite(o); return rim.crop(rim.getbbox())


def framed(box, inner, pic, k=0.80):
    im = box.copy(); x0, y0, x1, y1 = inner; side = min(x1 - x0, y1 - y0) * k
    pic = pic.crop(pic.getbbox()); s = side / max(pic.size); pic = pic.resize((max(1, round(pic.width * s)), max(1, round(pic.height * s))), Image.LANCZOS)
    im.alpha_composite(pic, ((x0 + x1 - pic.width) // 2, (y0 + y1 - pic.height) // 2))
    s = B.T / max(im.size)
    return im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)


if __name__ == '__main__':
    _os.makedirs(W, exist_ok=True)
    box, inner = empty_box()
    pics = svg_pngs(list(SVG)); pics['magnet'] = gem()
    new = {f'Icon_s_{k}': framed(box, inner, im, 0.74 if k == 'magnet' else 0.82) for k, im in pics.items()}
    for k, im in new.items(): im.save(f'{W}/{k}.png')
    B.merge(new)
    print('ok', sorted(new))
