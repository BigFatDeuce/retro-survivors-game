"""Real-ESRGAN x4 (anime model, ncnn) on the CPU through Chromium's SwiftShader Vulkan driver: only for the few pictures
that are bitmaps in the client (the vector ones are re-rendered instead). RGB is upscaled by the network, the alpha
channel with Lanczos."""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import os, subprocess, tempfile
from PIL import Image

BIN = f'{ROOT}/esr/realesrgan-ncnn-vulkan'
ICD = '/opt/pw-browsers/chromium-1194/chrome-linux/vk_swiftshader_icd.json'


def upscale(im, model='realesrgan-x4plus-anime', scale=4):
    im = im.convert('RGBA')
    if not (os.path.exists(BIN) or os.path.exists(BIN + '.exe')):   # (0.60: no ncnn build here, e.g. on Windows: Lanczos)
        return im.resize((im.width * scale, im.height * scale), Image.LANCZOS)
    with tempfile.TemporaryDirectory() as d:
        bg = Image.new('RGBA', im.size, (128, 128, 128, 255)); bg.alpha_composite(im)
        # bleed the colours outwards under transparent pixels so the edges do not pick up the grey
        rgb = bg.convert('RGB'); rgb.save(f'{d}/i.png')
        env = dict(os.environ, VK_ICD_FILENAMES=ICD)
        r = subprocess.run([BIN, '-i', f'{d}/i.png', '-o', f'{d}/o.png', '-n', model, '-s', str(scale), '-m', f'{ROOT}/esr/models'], capture_output=True, env=env, timeout=1800)
        if not os.path.exists(f'{d}/o.png'):
            return im.resize((im.width * scale, im.height * scale), Image.LANCZOS)
        out = Image.open(f'{d}/o.png').convert('RGB')
        a = im.getchannel('A').resize(out.size, Image.LANCZOS)
        out = out.convert('RGBA'); out.putalpha(a)
        return out
