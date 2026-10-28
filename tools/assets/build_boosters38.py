"""0.38: the booster packs = 14 original pictures (work/boosters38_src/*.png, packs on a plain white / grey
background): the background is cut away (flood fill from the borders, biggest shape, holes filled, soft 1-px edge),
each pack is cropped and brought to the same size W x H. -> game/assets/ui/boosters.webp (atlas, COLS columns) +
SPR.boosters.   usage: python tools/assets/build_boosters38.py"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import os, glob
import numpy as np, cv2
from PIL import Image
import sprio

G = f'{ROOT}/game'
SRC = f'{ROOT}/work/boosters38_src'
W, H, COLS = 440, 704, 5


def cut(f):
    im = cv2.imread(f)
    if im.shape[1] < 1792: im = cv2.resize(im, (1792, 2400), interpolation=cv2.INTER_CUBIC)
    h, w = im.shape[:2]
    mask = np.zeros((h + 2, w + 2), np.uint8)
    flags = 4 | cv2.FLOODFILL_MASK_ONLY | (255 << 8) | cv2.FLOODFILL_FIXED_RANGE
    for x, y in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1), (w // 2, 0), (w // 2, h - 1), (0, h // 2), (w - 1, h // 2)]:
        if mask[y + 1, x + 1] == 0: cv2.floodFill(im, mask, (x, y), 0, (14,) * 3, (14,) * 3, flags)
    fg = mask[1:-1, 1:-1] == 0
    n, lab, st, _ = cv2.connectedComponentsWithStats(fg.astype(np.uint8), 8)
    fg = lab == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])
    cnt, _ = cv2.findContours(fg.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    a = np.zeros(fg.shape, np.uint8); cv2.drawContours(a, cnt, -1, 255, -1)
    a = cv2.GaussianBlur(cv2.erode(a, np.ones((3, 3), np.uint8)), (0, 0), 1.2)
    p = Image.fromarray(np.dstack([cv2.cvtColor(im, cv2.COLOR_BGR2RGB), a]), 'RGBA')
    return p.crop(p.getbbox()).resize((W, H), Image.LANCZOS)   # (the packs' shapes differ by a few %: all the same size)


if __name__ == '__main__':
    fs = sorted(glob.glob(f'{SRC}/*.png')); rows = (len(fs) + COLS - 1) // COLS
    atlas = Image.new('RGBA', (W * COLS, H * rows))
    for i, f in enumerate(fs): atlas.paste(cut(f), ((i % COLS) * W, (i // COLS) * H))
    atlas.save(f'{G}/assets/ui/boosters.webp', 'WEBP', quality=88, method=6)
    sprio.update(lambda S: S.__setitem__('boosters', {'n': len(fs), 'cols': COLS, 'w': W, 'h': H, 'names': [os.path.basename(f)[:-4] for f in fs]}))
    print('ok', len(fs), os.path.getsize(f'{G}/assets/ui/boosters.webp'))
