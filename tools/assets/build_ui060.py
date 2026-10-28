"""0.60: small UI pictures straight from the client, in HD, into icons3:
  ui_none  = clips/forbidden.swf (the client's red 'forbidden' sign) for the shop's 'Aucune' (no hat / cape / pet)
usage: python tools/assets/build_ui060.py"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import stage as ST
import build_icons20 as BI
from PIL import Image

PX = 180
JOBS = {'ui_none': f'{ROOT}/raw/rc/clips/forbidden.swf'}


def main():
    work = f'{ROOT}/work/ui060'; out = {}
    for key, path in JOBS.items():
        probe = ST.stage_render(path, [dict(key=key, root=True, zoom=4, frames=[0], n=1)], f'{work}/p_{key}')
        im = probe[key]['imgs'][0]; b = im.getbbox()
        r = ST.stage_render(path, [dict(key=key, root=True, zoom=4 * PX * 2 / max(b[2] - b[0], b[3] - b[1]), frames=[0], n=1)], f'{work}/r_{key}')
        im = r[key]['imgs'][0]; im = im.crop(im.getbbox()); s = PX / max(im.size)
        out[key] = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
        print(key, out[key].size)
    BI.merge(out)


if __name__ == '__main__':
    main()
