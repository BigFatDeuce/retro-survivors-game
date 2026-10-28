"""0.34: the characteristic / effect icons in HD from their vectors: every Icon_<n> of clips/effectsicons.swf and the
client's stat icons and small UI pictures of modules/core.swf (Ghost, Heart, KamaSymbol…; IconPP = Prospection, the blue gem in a gold ring; IconWisdom, IconVita,
IconInit…), rendered at ~180 px into icons3 (they were 56 px pictures, blurry once zoomed).
usage: python tools/assets/build_staticons34.py"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import swflib as S, stage as ST
import build_icons20 as BI

PX = 180


def render(src, syms, work):
    out = {}
    probe = ST.stage_render(src, [dict(key=k, sym=k, zoom=4, frames=[0], n=1) for k in syms], f'{work}/p', prune=True)
    jobs = []
    for k in syms:
        im = probe[k]['imgs'][0]
        if im is None or not im.getbbox(): continue
        b = im.getbbox(); jobs.append(dict(key=k, sym=k, zoom=4 * PX / max(b[2] - b[0], b[3] - b[1]), frames=[0], n=1))
    res = ST.stage_render(src, jobs, f'{work}/r', prune=True)
    for j in jobs:
        im = res[j['key']]['imgs'][0]
        if im is not None and im.getbbox(): out[j['key']] = im.crop(im.getbbox())
    return out


def main():
    W = f'{ROOT}/work/staticons34'
    src = f'{ROOT}/raw/rc/clips/effectsicons.swf'
    eff = [k for k in S.exports(S.read_swf(src)['tags']) if k.startswith('Icon_')]
    new = render(src, eff, W + '/eff')
    core = f'{ROOT}/raw/rc/modules/core.swf'
    new.update(render(core, ['IconPP', 'IconWisdom', 'IconVita', 'IconInit', 'Ghost', 'Heart', 'KamaSymbol', 'Star', 'StarSymbol', 'Oeuf', 'OeufCasse', 'Coeur', 'IconMP'], W + '/core'))
    print(len(new), 'icons')
    BI.merge(new)


if __name__ == '__main__':
    main()
