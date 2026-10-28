"""0.27: monsters with no sound in game/data/sounds.json (the Île des Naufragés crew, the new bosses…) get the sound
keys their own client clip calls (tools/lib/sndanim27.py): atk = anim0R (else anim1R), hit = hitR, die = dieR. Entries that
already exist are kept. Only keys already in sfx_pack.mp3 can be used (the key -> sound table of the client is missing).
usage: python tools/assets/fix_sounds27.py [gfx…]     (no gfx: every monster and boss of content.json)"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import sys, os, json
import sndanim27 as SA

P = f'{ROOT}/game/data/sounds.json'


def main(gfxs):
    snd = json.load(open(P)); done = []
    for g in gfxs:
        if snd['mobs'].get(str(g)) or not os.path.exists(f'{ROOT}/raw/rc/clips/sprites/{g}.swf'): continue
        a = SA.anim_sounds(g)
        e = {'atk': a.get('anim0R') or a.get('anim1R') or [], 'hit': a.get('hitR') or [], 'die': a.get('dieR') or []}
        if any(e.values()): snd['mobs'][str(g)] = e; done.append(g)
    json.dump(snd, open(P, 'w'), separators=(',', ':'))
    print('sounds for', len(done), 'monsters:', done)


if __name__ == '__main__':
    if len(sys.argv) > 1: main([int(g) for g in sys.argv[1:]])
    else:
        C = json.load(open(f'{ROOT}/game/data/content.json'))
        main(sorted({d['gfx'] for d in list(C['monsters'].values()) + list(C['bosses'].values()) if d.get('gfx')}))
