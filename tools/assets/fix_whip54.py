"""0.54: the Fouet's client effect (fx 211) as one clean whip lash: the exported clip alternated empty frames with the
whip (it blinked) and mixed in the impact stars and a second lash (the whip seemed to fly anywhere); only the lash's
frames are kept. The game draws it from the whip's handle (C.spells.fouet.whip = handle x, y, reach, sheet units).
usage: python tools/assets/fix_whip54.py"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
import _root
import sprio


def fix(S):
    a = S['fx']['211']['anims']['root']
    if a.get('clean'): return
    a['f'] = [f for i, f in enumerate(a['f'][:22]) if f[2] > 2]
    a['fps'] = 20; a['clean'] = 1


sprio.update(fix)
print('fx 211 whip cleaned')
