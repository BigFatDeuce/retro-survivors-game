"""0.27: which original sound keys a sprite's animations call (a stand-in for the missing sndscan): for each exported
animation symbol (anim0R, dieR, hitR…) of clips/sprites/<gfx>.swf, the strings of the DoAction tags of the symbol and of
every sprite it places (recursively) that are sound keys already in game/data/sounds.json (pack).
usage: python tools/lib/sndanim27.py gfx [gfx…]      -> prints {anim: [keys]}"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import sys, json
import swflib as S

PACK = set(json.load(open(f'{ROOT}/game/data/sounds.json'))['pack'])


def anim_sounds(gfx, keys=PACK):
    sw = S.read_swf(f'{ROOT}/raw/rc/clips/sprites/{gfx}.swf'); D = S.defs(sw['tags']); ex = S.exports(sw['tags'])
    memo = {}

    def walk(cid, seen):
        if cid in memo: return memo[cid]
        if cid in seen or cid not in D or D[cid].code != S.T_SPRITE: return []
        seen = seen | {cid}; out = []
        for t in D[cid].sub:
            if t.code == S.T_DOACTION:
                for s in S.action_strings(t.data):   # ('s', string) / ('n', number) constants
                    s = s[1] if isinstance(s, tuple) else s
                    if isinstance(s, str) and s.lower() in keys and s.lower() not in out: out.append(s.lower())
            elif t.code in (S.T_PLACE, S.T_PLACE2, S.T_PLACE3):
                p = S.parse_place(t)
                if p.get('char') is not None:
                    for k in walk(p['char'], seen):
                        if k not in out: out.append(k)
        memo[cid] = out; return out
    return {a: walk(cid, frozenset()) for a, cid in ex.items() if a.endswith('R')}


if __name__ == '__main__':
    for g in sys.argv[1:]: print(g, json.dumps(anim_sounds(int(g))))
