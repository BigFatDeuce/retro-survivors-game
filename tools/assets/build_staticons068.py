"""0.68: the characteristics' icons of the up-to-date client's stats window (modules/core.swf: IconVita, IconWisdom
the violet ring, IconEarth, IconFire, IconWater, IconAir, IconMP, Star; IconNeutral = the neutral resistance) rendered
from their vectors in the white box with the grey frame of the effect icons (build_staticons48.empty_box), and Portée's
spyglass drawn flat (SVG, the colours of the original picture work/art068/spyglass.webp; the picture itself was too
detailed next to the others).
usage: python tools/assets/build_staticons068.py   -> icons3 'Icon_c_<name>' (the passives point at them in tools/patch_068)"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import stage as ST
import build_icons20 as B
import build_staticons48 as S48

W = f'{ROOT}/work/staticons068'
from _root import CLIENT as NEW   # the up-to-date installed client (_root.py)
SYMS = {'vita': 'IconVita', 'wisdom': 'IconWisdom', 'earth': 'IconEarth', 'fire': 'IconFire', 'water': 'IconWater', 'air': 'IconAir',
        'mp': 'IconMP', 'ap': 'Star', 'neutral': 'IconNeutral'}


def client_pics():
    p = f'{NEW}/modules/core.swf'
    r = ST.stage_render(p, [dict(key=k, sym=s, zoom=14, frames=[0], n=1) for k, s in SYMS.items()], f'{W}/core', prune=True)
    return {k: v['imgs'][0].crop(v['imgs'][0].getbbox()) for k, v in r.items() if v['imgs'] and v['imgs'][0] is not None}


if __name__ == '__main__':
    _os.makedirs(W, exist_ok=True)
    box, inner = S48.empty_box()
    # Portée (the picture was too detailed and kept black inside its strap): a flat spyglass drawn like the
    # other framed icons, the original picture's colours (brown tube, gold rings, blue lens)
    O = S48.O
    S48.SVG['range'] = f'''<g transform="rotate(-32 50 50)" stroke="#3a2210" stroke-width="3.5" {O}>
      <rect x="10" y="40" width="16" height="20" rx="3" fill="#e0b030"/>
      <rect x="24" y="36" width="30" height="28" rx="3" fill="#8a4a20"/><rect x="24" y="36" width="30" height="11" rx="3" fill="#a8622c" stroke="none"/>
      <rect x="24" y="36" width="30" height="28" rx="3" fill="none"/>
      <rect x="52" y="31" width="10" height="38" rx="3" fill="#e0b030"/>
      <rect x="60" y="33" width="22" height="34" rx="3" fill="#8a4a20"/><rect x="60" y="33" width="22" height="12" rx="3" fill="#a8622c" stroke="none"/>
      <rect x="60" y="33" width="22" height="34" rx="3" fill="none"/>
      <rect x="80" y="28" width="10" height="44" rx="4" fill="#e0b030"/>
      <ellipse cx="90" cy="50" rx="4" ry="15" fill="#7ab8e8"/></g>'''
    pics = client_pics(); pics['range'] = S48.svg_pngs(['range'])['range']
    new = {f'Icon_c_{k}': S48.framed(box, inner, im, 0.84 if k in ('ap', 'mp', 'range') else 0.9) for k, im in pics.items()}
    for k, im in new.items(): im.save(f'{W}/{k}.png')
    B.merge(new)
    print('ok', sorted(new))
