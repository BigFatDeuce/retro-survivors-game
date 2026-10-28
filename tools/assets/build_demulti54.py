"""0.54: the icon of Démultiplication (the old Invocations, +1 summon / projectile / multi-hit spell per level): the
client's Invocations icon (Icon_26 of clips/effectsicons.swf: the Tofu) taken out of its frame, smaller, with an arrow
and a fireball drawn as vectors (the three things it multiplies), in the same grey-framed white box as the other
characteristics (build_staticons48.empty_box / framed).   usage: python tools/assets/build_demulti54.py   -> icons3 'Icon_s_amount'"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import numpy as np
from PIL import Image
import swflib as SW, stage as ST
import build_icons20 as B, build_staticons48 as S

W = f'{ROOT}/work/staticons54'
O = 'stroke-linejoin="round" stroke-linecap="round"'
S.SVG['arrow'] = f'''<g {O}><path d="M10 90 L 78 22" stroke="#6a4214" stroke-width="7"/><path d="M10 90 L 78 22" stroke="#b07a3a" stroke-width="3"/>
  <path d="M92 8 L 66 18 L 74 26 L 82 34 Z" fill="#d8d8d8" stroke="#2a2a2a" stroke-width="3.5"/>
  <path d="M18 82 L 6 80 M18 82 L 20 94 M26 74 L 14 72 M26 74 L 28 86" stroke="#c83030" stroke-width="5"/></g>'''
S.SVG['fire'] = f'''<g {O}><path d="M50 96 C 22 96 10 76 16 56 C 20 42 30 36 30 20 C 40 28 44 36 44 44 C 50 30 58 16 70 6 C 70 26 86 36 88 58 C 90 80 74 96 50 96 Z"
  fill="#ff6a1e" stroke="#7a1a04" stroke-width="4"/>
  <path d="M50 88 C 34 88 28 76 32 64 C 36 56 42 54 44 46 C 52 54 54 60 54 66 C 60 58 64 50 66 44 C 74 58 76 66 74 74 C 72 84 62 88 50 88 Z" fill="#ffc83a"/>
  <circle cx="50" cy="74" r="9" fill="#fff6c0"/></g>'''


def tofu():
    p = f'{ROOT}/raw/rc/clips/effectsicons.swf'; ex = SW.exports(SW.read_swf(p)['tags'])
    im = ST.stage_render(p, [dict(key='t', cid=ex['Icon_26'], zoom=8, frames=[0])], f'{W}/tofu')['t']['imgs'][0]
    im = im.crop(im.getbbox()); a = np.asarray(im).copy()
    white = (a[..., :3].min(-1) > 235) & (a[..., 3] > 200); ys, xs = np.where(white)
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    inner = a[y0 + 2:y1 - 1, x0 + 2:x1 - 1].copy()
    wh = inner[..., :3].min(-1) > 235; inner[wh, 3] = 0   # (its white box gone: only the drawing)
    o = Image.fromarray(inner, 'RGBA'); return o.crop(o.getbbox())


if __name__ == '__main__':
    _os.makedirs(W, exist_ok=True)
    box, (x0, y0, x1, y1) = S.empty_box()
    pics = S.svg_pngs(['arrow', 'fire'])
    side = min(x1 - x0, y1 - y0)
    def put(im, pic, k, cx, cy):
        pic = pic.crop(pic.getbbox()); s = side * k / max(pic.size); pic = pic.resize((max(1, round(pic.width * s)), max(1, round(pic.height * s))), Image.LANCZOS)
        im.alpha_composite(pic, (round(x0 + cx * (x1 - x0) - pic.width / 2), round(y0 + cy * (y1 - y0) - pic.height / 2)))
    im = box.copy()
    put(im, pics['arrow'], 0.46, 0.72, 0.27)
    put(im, pics['fire'], 0.40, 0.26, 0.28)
    put(im, tofu(), 0.58, 0.44, 0.68)
    s = B.T / max(im.size); im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    im.save(f'{W}/Icon_s_amount.png')
    B.merge({'Icon_s_amount': im})
    print('ok Icon_s_amount', im.size)
