"""0.36: AI upscale ×4 for the few pictures that exist only as small bitmaps (no vector source in the client), with the
official Real-ESRGAN 'x4plus_anime_6B' weights (BSD-3, xinntao/Real-ESRGAN v0.2.2.4, downloaded into work/esrgan/).
Needs torch (CPU is enough: pip install torch --index-url https://download.pytorch.org/whl/cpu).
Transparency: the colours are first bled into the transparent area (no dark halo), the alpha channel is upscaled by the
same network as a grey picture.   usage: python tools/lib/esrgan.py in.png out.png"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import numpy as np
from PIL import Image, ImageFilter
import torch
from torch import nn
import torch.nn.functional as F

W = f'{ROOT}/work/esrgan/RealESRGAN_x4plus_anime_6B.pth'


class RDB5(nn.Module):
    def __init__(s, nf=64, gc=32):
        super().__init__()
        s.conv1 = nn.Conv2d(nf, gc, 3, 1, 1); s.conv2 = nn.Conv2d(nf + gc, gc, 3, 1, 1); s.conv3 = nn.Conv2d(nf + 2 * gc, gc, 3, 1, 1)
        s.conv4 = nn.Conv2d(nf + 3 * gc, gc, 3, 1, 1); s.conv5 = nn.Conv2d(nf + 4 * gc, nf, 3, 1, 1); s.l = nn.LeakyReLU(0.2, True)

    def forward(s, x):
        x1 = s.l(s.conv1(x)); x2 = s.l(s.conv2(torch.cat((x, x1), 1))); x3 = s.l(s.conv3(torch.cat((x, x1, x2), 1)))
        x4 = s.l(s.conv4(torch.cat((x, x1, x2, x3), 1))); x5 = s.conv5(torch.cat((x, x1, x2, x3, x4), 1))
        return x5 * 0.2 + x


class RRDB(nn.Module):
    def __init__(s, nf=64):
        super().__init__(); s.rdb1 = RDB5(nf); s.rdb2 = RDB5(nf); s.rdb3 = RDB5(nf)

    def forward(s, x): return s.rdb3(s.rdb2(s.rdb1(x))) * 0.2 + x


class RRDBNet(nn.Module):
    def __init__(s, nb=6, nf=64):
        super().__init__()
        s.conv_first = nn.Conv2d(3, nf, 3, 1, 1); s.body = nn.Sequential(*[RRDB(nf) for _ in range(nb)]); s.conv_body = nn.Conv2d(nf, nf, 3, 1, 1)
        s.conv_up1 = nn.Conv2d(nf, nf, 3, 1, 1); s.conv_up2 = nn.Conv2d(nf, nf, 3, 1, 1); s.conv_hr = nn.Conv2d(nf, nf, 3, 1, 1)
        s.conv_last = nn.Conv2d(nf, 3, 3, 1, 1); s.l = nn.LeakyReLU(0.2, True)

    def forward(s, x):
        f = s.conv_first(x); f = f + s.conv_body(s.body(f))
        f = s.l(s.conv_up1(F.interpolate(f, scale_factor=2, mode='nearest')))
        f = s.l(s.conv_up2(F.interpolate(f, scale_factor=2, mode='nearest')))
        return s.conv_last(s.l(s.conv_hr(f)))


_net = None
def net():
    global _net
    if _net is None:
        m = RRDBNet(); sd = torch.load(W, map_location='cpu', weights_only=True); m.load_state_dict(sd.get('params_ema', sd.get('params', sd))); m.eval(); _net = m
    return _net


def run(rgb):
    """float RGB [0,1] HxWx3 -> 4x"""
    with torch.no_grad():
        t = torch.from_numpy(np.ascontiguousarray(rgb.transpose(2, 0, 1))).float()[None]
        return net()(t)[0].clamp(0, 1).numpy().transpose(1, 2, 0)


def bleed(im):
    """the visible colours spread into the transparent pixels (so the network sees no black around the drawing)"""
    a = np.asarray(im).astype(np.float32); al = a[..., 3] > 8; rgb = a[..., :3].copy(); known = al.copy()
    for _ in range(40):
        if known.all(): break
        s = np.zeros_like(rgb); n = np.zeros(known.shape, np.float32)
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)):
            k = np.roll(np.roll(known, dy, 0), dx, 1); c = np.roll(np.roll(rgb, dy, 0), dx, 1)
            s += c * k[..., None]; n += k
        new = (~known) & (n > 0); rgb[new] = s[new] / n[new][:, None]; known = known | new
    return rgb / 255


def upscale(im):
    im = im.convert('RGBA')
    rgb = run(bleed(im))
    a = np.asarray(im)[..., 3].astype(np.float32) / 255
    al = run(np.repeat(a[..., None], 3, 2)).mean(2)
    out = np.dstack([rgb, al]); return Image.fromarray((out * 255 + 0.5).astype(np.uint8), 'RGBA')


if __name__ == '__main__':
    upscale(Image.open(_sys.argv[1])).save(_sys.argv[2]); print('ok')
