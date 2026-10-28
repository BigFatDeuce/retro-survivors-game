"""0.92 (the Dofus shields as a new skin slot): the shield's anchors (slot 4) in the character sheets.
Every class clip of the up-to-date client has shield holders (GAC.applyAccessory(this, 4, 'R' | 'L')) in nearly every
animation, standing, runs and casts alike; the sheets' anchors (SPR.chars[key].anims[a].anc) only kept slots 0-3. Each
frame of a sheet is matched to the client frame of the same animation whose hat / cape / pet / weapon anchors are the
same (the sheets' anchors = the client's matrices x 0.24), and that frame's slot 4 anchors are added (view, matrix, paint
order). A frame with no anchor to match takes the client frame at the same point of the animation.
usage: python tools/assets/shield_anc092.py [key…]   (writes game/data/sprites.json)"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import sys, os, json
import swflib as S, timeline as TL

from _root import CLIENT
NEW = f'{CLIENT}/clips/sprites'
K = 0.24


def run(keys=None):
    import sprio
    SPR = json.load(open(f'{ROOT}/game/data/sprites.json'))
    tls, cache, stats = {}, {}, dict(frames=0, matched=0, timed=0, with4=0, keys=0)
    for key, ch in SPR['chars'].items():
        if keys and key not in keys: continue
        sid = key.split('_')[0]; p = f'{NEW}/{sid}.swf'
        if not os.path.exists(p): continue
        if sid not in tls: tls[sid] = TL.Timeline(S.read_swf(p))
        tl = tls[sid]; stats['keys'] += 1
        for an, A in ch['anims'].items():
            if an not in tl.ex or not A.get('anc'): continue
            ck = (sid, an)
            if ck not in cache:
                try: cache[ck] = tl.anchors(tl.ex[an])
                except Exception: cache[ck] = []
            cl = cache[ck]
            if not cl or not any(a[0] == 4 for fr in cl for a in fr): continue
            n = len(A['anc'])
            for i, fr in enumerate(A['anc']):
                fr[:] = [a for a in fr if a[0] != 4]
                stats['frames'] += 1
                best, be = None, 1e9
                if fr:
                    for j, cf in enumerate(cl):
                        e = 0; ok = True
                        for a in fr:
                            c = next((c for c in cf if c[0] == a[0] and c[1] == a[1]), None)
                            if c is None: ok = False; break
                            m = c[2]; e += sum(abs(a[2 + q] - m[q] * K) * (1 if q < 4 else 0.02) for q in range(6))
                        if ok and e < be: be, best = e, j
                if best is not None and be < 0.6: stats['matched'] += 1
                else: best = min(len(cl) - 1, round(i * len(cl) / max(1, n))); stats['timed'] += 1
                add = [[4, c[1], *[round(x * K, 4) for x in c[2][:4]], round(c[2][4] * K, 3), round(c[2][5] * K, 3), round(c[3], 3)] for c in cl[best] if c[0] == 4]
                if add: fr.extend(add); stats['with4'] += 1
    import shield_back094; stats['back094'] = shield_back094.fix(SPR['chars'])   # (0.94: no shield face over the back in the back runs, but the male Sadida's)
    sprio.update(lambda S_: S_.__setitem__('chars', SPR['chars']))
    print(stats)


if __name__ == '__main__':
    run(set(sys.argv[1:]) or None)
