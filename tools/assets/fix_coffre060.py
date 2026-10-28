"""0.60: the Coffre Animé's walks (sheet 1083_z60: walkR, walkL, runR) carry the client clip's own forward hop (the frame
origin slides ~100 px across the cycle): the game also moves the monster, so the drawing went forward twice then
snapped back at every loop (the 'teleporting' blue chest of the Minotoror trapdoor, 500 HP, the only one seen walking).
The frames' origins are moved so the chest's middle stays at the same place (the hop's height is kept).
usage: python tools/assets/fix_coffre060.py [sheet…]"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
import _root
import sys
import sprio


def fix(S, key):
    an = S['mobs'][key]['anims']
    for a in ('walkR', 'walkL', 'runR', 'runL'):
        if a not in an: continue
        fr = an[a]['f']; mids = [f[2] / 2 - f[4] for f in fr]; c = sum(mids) / len(mids)   # (the frame's middle, from its origin)
        for f in fr: f[4] = round(f[2] / 2 - c, 2)
        print(key, a, 'centred', len(fr), 'frames')


if __name__ == '__main__':
    keys = sys.argv[1:] or ['1083_z60']
    sprio.update(lambda S: [fix(S, k) for k in keys])
