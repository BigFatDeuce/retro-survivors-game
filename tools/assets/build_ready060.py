"""0.60: the up-to-date client's fight 'ready' sign (clips/ready.swf, symbol 'ready': two crossed swords) in HD ->
icons3 'ui_ready', drawn behind GO! in the countdown (events.js drawCountdown).
usage: python tools/assets/build_ready060.py"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import os
import stage as ST, build_icons20 as B

from _root import CLIENT as NEW   # the up-to-date installed client (_root.py)


def main():
    src = f'{NEW}/clips/ready.swf'
    r = ST.stage_render(src, [dict(key='ready', sym='ready', zoom=9, frames=[0], n=1)], f'{ROOT}/work/ready060')['ready']
    im = r['imgs'][0]; im = im.crop(im.getbbox())
    B.merge({'ui_ready': im}); print('ui_ready', im.size)


if __name__ == '__main__':
    main()
