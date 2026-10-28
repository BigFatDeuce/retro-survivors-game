"""0.56: ToT's time portal in the runs is the client's zaap (map object 7000, rendered natively at RES 6) with the
portal swirling inside its ring (events.js drawTimePortal).   usage: python tools/assets/build_zaap56.py -> icons3 'zaap_hd'"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
import _root
import numpy as np
import maprender as MR, build_icons20 as B

R = 6.0
MR.ensure_symbols({('o', 7000, 0, 0, 0)}, R)
s = MR.sym_img(MR.sym_key('o', 7000, 0, 0, 0, R)); s = s.crop(s.getbbox())
a = np.asarray(s)
print('size', s.size)
B.merge({'zaap_hd': s})
s.save(f'{_root.ROOT}/work/zaap_hd.png')
