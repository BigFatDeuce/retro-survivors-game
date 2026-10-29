"""Item pictures re-rendered big from the client's own vector item (clips/items/<T>/<G>.swf through build_icons20.render),
for the places that show an icon bigger than its 180-px picture (never upscale or redraw them).
  python tools/assets/build_iconhd091.py [skins] [it_T_G…]   0.91: every hat / cape / pet at 400 px, one file each in
        game/assets/ui/hd/<it_T_G>.webp (only the missing ones), SPR.iconsHD = their names (Atlas.hd, assets.js: drawFit
        takes them over 90 px — Nowel's gift reveal, ground pickups)
  python tools/assets/build_iconhd091.py dofus    0.38 / 0.47: the Dofus eggs at 440 px -> icons3 'dofus_hd_<icon>' (Dofus
        window, 'item get' scene); the dofus_hd_* / it_23_* pictures content.json no longer names leave the atlas
  python tools/assets/build_iconhd091.py relics   0.61: every relic at 400 px -> icons3 'relic_hd_<icon>' (the 'relic got' show)
  python tools/assets/build_iconhd091.py gift     0.91: Nowel's gift (item 89/2) at 512 px -> icons3 'gift_hd'
  python tools/assets/build_iconhd091.py gosword  0.98: the Épée Royale du Bouftou (item 2440, picture 6/30) at 640 px -> icons3
        'go_sword' (the two swords that cross before GO!, events.js drawCountdown)
(dofus / relics / gift used to be build_dofus38.py, build_relics061.py, build_gift091.py.)"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import sys, os, json
import build_icons20 as B
import sprio

PX = 400


def content():
    return json.load(open(f'{ROOT}/game/data/content.json', encoding='utf-8'))


def skins(keys):
    C = content()
    keys = keys or ['it_' + it['id'] for k in ('hats', 'capes', 'pets') for it in C[k]]
    out = f'{ROOT}/game/assets/ui/hd'; os.makedirs(out, exist_ok=True)
    todo = [k for k in keys if not os.path.exists(f'{out}/{k}.webp')]
    B.T = PX
    for i in range(0, len(todo), 60):
        ims = B.render(todo[i:i + 60], f'{ROOT}/work/iconhd091')
        for k, im in ims.items(): im.save(f'{out}/{k}.webp', 'WEBP', quality=92, method=6)
        print(i + len(todo[i:i + 60]), '/', len(todo), flush=True)
    have = sorted(f[:-5] for f in os.listdir(out) if f.endswith('.webp'))
    sprio.update(lambda S: S.__setitem__('iconsHD', have))
    print('hd icons', len(have))


def dofus():
    C = content()
    B.T = 440
    ims = B.render([f"it_23_{d['icon']}" for d in C['dofus']], f'{ROOT}/work/dofus38')
    used = json.dumps(C)
    sprio.update(lambda SPR: [SPR['icons3'].pop(k) for k in list(SPR['icons3']) if (k.startswith('dofus_hd_') or k.startswith('it_23_')) and f'"{k}"' not in used])
    B.merge({k.replace('it_23_', 'dofus_hd_'): im for k, im in ims.items()})
    print('ok', sorted(ims))


def relics():
    C = content()
    B.T = 400
    icons = sorted({r['icon'] for r in C['relics'] if r.get('icon', '').startswith('it_')})
    ims = B.render(icons, f'{ROOT}/work/relics061')
    B.merge({'relic_hd_' + k: im for k, im in ims.items()})
    print('ok', len(ims), 'of', len(icons), sorted(ims))


def gift():
    B.T = 512
    ims = B.render(['it_89_2'], f'{ROOT}/work/gift091')
    B.merge({'gift_hd': ims['it_89_2']})
    print('ok', ims['it_89_2'].size)


def gosword():
    B.T = 640
    ims = B.render(['it_6_30'], f'{ROOT}/work/gosword098')
    B.merge({'go_sword': ims['it_6_30']})
    print('ok', ims['it_6_30'].size)


if __name__ == '__main__':
    a = sys.argv[1:]
    what = a.pop(0) if a and a[0] in ('skins', 'dofus', 'relics', 'gift', 'gosword') else 'skins'
    {'skins': lambda: skins(a), 'dofus': dofus, 'relics': relics, 'gift': gift, 'gosword': gosword}[what]()
