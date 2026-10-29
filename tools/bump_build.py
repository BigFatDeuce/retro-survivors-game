"""0.48: the version in one go (0.98.1: a third number for a patch release) — BUILD in game/js/assets.js (shown on the main menu, ?v= of every data / image URL) and
the ?v= of the scripts in game/index.html (browsers kept old JS files next to new ones).   usage: python tools/bump_build.py 0.49"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from _root import ROOT
import re, sys

if len(sys.argv) != 2 or not re.fullmatch(r'\d+\.\d+(\.\d+)?', sys.argv[1]): sys.exit('usage: python tools/bump_build.py 0.95   (or a patch release: 0.98.1)')
v = sys.argv[1]
p = f'{ROOT}/game/js/assets.js'; s = open(p, encoding='utf8').read()
s, n = re.subn(r"const BUILD = '[^']*'", f"const BUILD = '{v}'", s, count=1)
if not n: sys.exit('const BUILD not found in game/js/assets.js')
open(p, 'w', encoding='utf8').write(s)
p = f'{ROOT}/game/index.html'; s = open(p, encoding='utf8').read()
s, n = re.subn(r'<script src="(js/[^"?]+)(?:\?v=[^"]*)?"></script>', rf'<script src="\1?v={v}"></script>', s)
open(p, 'w', encoding='utf8').write(s)
print('BUILD', v, n, 'scripts')
