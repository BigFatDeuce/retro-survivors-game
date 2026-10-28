"""0.36: the Phoenix statue of the death screen. The original picture (work/phoenix_owner.png, 152 x 208: the client
has the statue only as a 92 x 137 bitmap, map object o5.swf '542', and no vector version) upscaled x4 by the
Real-ESRGAN anime network (tools/lib/esrgan.py) into icons3 as 'phoenix_statue'.   usage: python tools/assets/build_phoenix36.py"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
from PIL import Image
import build_icons20 as B, esrgan

if __name__ == '__main__':
    im = esrgan.upscale(Image.open(f'{ROOT}/work/phoenix_owner.png'))
    im = im.crop(im.getbbox()); im.save(f'{ROOT}/work/esrgan/phoenix_x4.png')
    B.merge({'phoenix_statue': im})
    print('ok', im.size)
