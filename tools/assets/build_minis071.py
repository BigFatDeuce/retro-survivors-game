"""0.71: every zone's mini map (zone choice, minimap, Musha's / the Armurerie's treasure maps) made again from the
world's current tiles, 540 px on the long side (+50 %: the builders made 360).
usage: python tools/assets/build_minis071.py [world…]"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import sys, json
from PIL import Image

G = f'{ROOT}/game'
SIDE = 540


def mini(name, W):
    res = W.get('res') or 1.0; tile = W['tile'] * res; X, Y = int(round(W['w'] * res)), int(round(W['h'] * res))
    k = SIDE / max(X, Y); out = Image.new('RGB', (max(1, round(X * k)), max(1, round(Y * k))))
    for tx, ty, fn in W['tiles']:
        p = f'{G}/assets/worlds/{fn}'
        if not _os.path.exists(p): continue
        im = Image.open(p).convert('RGB'); x0, y0 = tx * tile, ty * tile
        # (0.92: a dark 1-px line on some minis: position and size rounded apart left a gap between tiles; the
        # size now runs from this tile's rounded edge to the next one's)
        px, py = round(x0 * k), round(y0 * k)
        w, h = max(1, round((x0 + im.width) * k) - px), max(1, round((y0 + im.height) * k) - py)
        out.paste(im.resize((w, h), Image.LANCZOS), (px, py))
    out.save(f'{G}/assets/worlds/{name}_mini.webp', 'WEBP', quality=86, method=6)
    return out.size


if __name__ == '__main__':
    S = json.load(open(f'{G}/data/sprites.json'))['worlds']
    for name in (sys.argv[1:] or sorted(S)):
        if S.get(name, {}).get('tiles'): print(name, mini(name, S[name]), flush=True)
