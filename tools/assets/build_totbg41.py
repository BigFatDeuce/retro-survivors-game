"""0.41: the background of ToT's quiz = the Astrub zaap (client map 7411, 4,-19) and the maps around it, rendered
natively from the client map SWFs like the worlds (build_worlds20.compose, RES 3) -> game/assets/ui/tot_bg.webp
(2560x1440, the zaap near the top, above the question card; darkened + the portal's particles in game, tot.js).
usage: python tools/assets/build_totbg41.py"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
_os.environ.setdefault('RES', '3.0')
from _root import ROOT
import sqlite3
from PIL import Image
import build_worlds20 as BW
MR = BW.MR

ZAAP, ZX, ZY = 7411, 4, -19
OUT = (2560, 1440)


def main():
    db = sqlite3.connect(f'{ROOT}/work/sl.db'); pos = {}
    for i, mp in db.execute('select id, mappos from maps'):
        try: x, y, sa = map(int, mp.split(','))
        except Exception: continue
        if sa == 95: pos.setdefault((x, y), i)
    pos[(ZX, ZY)] = ZAAP
    maps = [[pos.get((ZX + i, ZY + j)) for i in (-1, 0, 1)] for j in (-1, 0, 1)]
    print(maps, flush=True)
    W, H = int(round(3 * MR.MAPW * BW.RES)), int(round(3 * MR.MAPH * BW.RES))
    needs = set()
    for row in maps:
        for m in row:
            if m: needs |= MR.needs_of(m)
    MR.ensure_symbols(needs, BW.RES)
    img = BW.compose(maps, Image.new('RGBA', (W, H))).convert('RGB')
    img.save(f'{ROOT}/work/totbg41_full.webp', quality=85)
    cw = int(MR.MAPW * BW.RES * 1.45); ch = cw * 9 // 16              # the zaap's map and a bit of its neighbours
    cx = W // 2 + int(float(_os.environ.get('DX', 0)) * BW.RES); cy = H // 2 + int(float(_os.environ.get('DY', 165)) * BW.RES)
    crop = img.crop((cx - cw // 2, cy - ch // 2, cx + cw // 2, cy + ch // 2)).resize(OUT, Image.LANCZOS)
    crop.save(f'{ROOT}/game/assets/ui/tot_bg.webp', 'WEBP', quality=86, method=6)
    print('tot_bg', crop.size, _os.path.getsize(f'{ROOT}/game/assets/ui/tot_bg.webp'))


if __name__ == '__main__':
    main()
