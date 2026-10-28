"""0.87 (ground areas under the scenery): a world's 'decor mask' = where its tall standing objects (trees, bamboos,
rocks, walls: map objects of layer 2 at least TALL Dofus px high) cover the ground, at MK pixels per world unit, saved as
game/assets/worlds/<name>_decor.webp (white, the mask in alpha) and SPR.worlds[name].decor = [file, MK]. The game draws
the areas on the ground in a layer of their own and erases them under the mask (render.js decorMask): the scenery, which
is already in the ground picture, then stands in front of them.
The world builders feed it while they place their objects (build_worlds20 compose, build_vlad51, build_grobe54,
build_flat068); MASK_ONLY=1 makes them stop there (no world tile rewritten): python tools/assets/decormask087.py <name>…|all
0.91: also the depth map <name>_depth.webp (SPR.worlds[name].depth, Mask.add's `oy` = the object's anchor): characters
and effects pass behind the scenery that stands in front of them (render.js decorFront)."""
import sys, os, json, math
import numpy as np
from PIL import Image, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT

MK = 0.75    # mask pixels per world unit (Dofus px)
DK = 0.5     # 0.91: depth map pixels per world unit
TALL = 45    # Dofus px: shorter objects (tufts, flowers, small stones) never hide an area; nor wide low ones (Mask.add)


class Mask:
    def __init__(self, W, H, res):   # W, H: the world picture in pixels, res pixels per world unit
        self.res, self.f, self.fd = res, MK / res, DK / res
        self.a = np.zeros((int(math.ceil(H * self.f)), int(math.ceil(W * self.f))), np.uint8)
        # 0.91: the depth map — per pixel, the foot line (world y of its anchor, the cell it stands on) of the frontmost
        # standing object drawn there (they are drawn in cell order, so the one with the largest foot line shows), and
        # that object's cover: the game hides a character standing above that line (behind the object) there
        self.d = np.zeros((int(math.ceil(H * self.fd)), int(math.ceil(W * self.fd))), np.uint16)
        self.da = np.zeros(self.d.shape, np.uint8)

    def add(self, s, px, py, oy=None):   # s: the object's picture (RGBA) placed at (px, py) in the world picture, its anchor oy px below its top
        if s is None: return
        h, w = s.height / self.res, s.width / self.res
        if h < TALL or (h < 0.75 * w and h < 110): return   # (wide low patches — tall grass, fences — never hide an area; trees, rocks, walls do)
        for arr, f, depth in ((self.a, self.f, False), (self.da, self.fd, True)):
            w, h = max(1, round(s.width * f)), max(1, round(s.height * f))
            a = np.asarray(s.getchannel('A').resize((w, h), Image.BOX))
            x0, y0 = int(round(px * f)), int(round(py * f)); H, W = arr.shape
            sx, sy = max(0, -x0), max(0, -y0); x1, y1 = min(W, x0 + w), min(H, y0 + h)
            if x1 <= max(0, x0) or y1 <= max(0, y0): continue
            src = a[sy:sy + (y1 - max(0, y0)), sx:sx + (x1 - max(0, x0))]
            reg = arr[max(0, y0):y1, max(0, x0):x1]
            if not depth: np.maximum(reg, src, out=reg); continue
            foot = max(0, int(round((py + (oy if oy is not None else s.height)) / self.res)))   # (world units)
            on = src > 40; dreg = self.d[max(0, y0):y1, max(0, x0):x1]
            dreg[on] = np.maximum(dreg[on], foot); reg[on] = np.maximum(reg[on], src[on])

    def save(self, name):
        G = f'{ROOT}/game'; fn = f'{name}_decor.webp'
        al = Image.fromarray(self.a).filter(ImageFilter.GaussianBlur(0.6))
        im = Image.new('RGBA', al.size, (255, 255, 255, 0)); im.putalpha(al)
        im.save(f'{G}/assets/worlds/{fn}', 'WEBP', quality=88, alpha_quality=90, method=6)   # (no metadata)
        import sprio
        sprio.update(lambda S: S['worlds'].setdefault(name, {}).__setitem__('decor', [fn, MK]))
        print(name, 'decor mask', im.size, round((self.a > 128).mean() * 100, 1), '% covered', os.path.getsize(f'{G}/assets/worlds/{fn}') // 1024, 'KB', flush=True)
        # 0.91: the depth map, lossless and opaque (exact numbers: no alpha to premultiply): R, G = the foot line (world
        # units, high / low byte), B = the cover
        fd = f'{name}_depth.webp'; d = self.d
        dm = np.dstack([(d >> 8).astype(np.uint8), (d & 255).astype(np.uint8), self.da])
        Image.fromarray(dm, 'RGB').save(f'{G}/assets/worlds/{fd}', 'WEBP', lossless=True, quality=100, method=6)
        sprio.update(lambda S: S['worlds'][name].__setitem__('depth', [fd, DK]))
        print(name, 'depth map', dm.shape[1], 'x', dm.shape[0], os.path.getsize(f'{G}/assets/worlds/{fd}') // 1024, 'KB', flush=True)


if __name__ == '__main__':
    os.environ['MASK_ONLY'] = '1'
    names = sys.argv[1:]
    if names == ['all']:
        names = ['astrub', 'bonta', 'chafer', 'porco', 'naufrages', 'gelee', 'sidimote', 'cania', 'wabbit', 'otomai_coast', 'mino',
                 'koalak', 'otomai_jungle', 'pandala', 'kwismas', 'kwaknest', 'vlad', 'goultard', 'grobe']
    FLAT = {'koalak', 'otomai_jungle', 'pandala', 'kwismas', 'kwaknest'}
    import build_worlds20 as BW
    for n in names:
        if n in FLAT:
            import build_flat068 as F; F.build(n)
        else: BW.build(n)
