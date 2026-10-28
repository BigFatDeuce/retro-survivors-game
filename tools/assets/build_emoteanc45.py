"""0.45: the emote sheets (<sid>_e, build_emote23) had no accessory anchors, so the character lost its hat, cape
and pet during '6 Millions de Prouts' (emote8R). This reads them from the client timeline (as the run sheets did: hats
'F'/'R'…, capes, pets; the hat always over the head) for every frame of every emote already in the sheets — no
re-render.   usage: python tools/assets/build_emoteanc45.py [sid…]   (default: every '<sid>_e' sheet)"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import sys, json
import swflib as S, timeline as TL
import build_chars20 as BC
import sprio

SLOT = {1: 1, 2: 2, 3: 3}   # client accessory index -> the game's slot (1 hat, 2 cape, 3 pet; no weapon in emotes)


def anchors(sid, meta):
    sw = S.read_swf(f'{BC.RAW}/{sid}.swf'); tl = TL.Timeline(sw); ex = S.exports(sw['tags']); low = {k.lower(): k for k in ex}
    k = meta['zoom'] / 20.0; out = {}
    for a, an in meta['anims'].items():
        sym = low.get(a.lower())
        if not sym: continue
        fr = list(range(len(an['f'])))
        anc = tl.anchors(ex[sym], frames=fr)
        out[a] = [[[SLOT[i], d, *[round(v * k, 4) for v in m[:4]], round(m[4] * k, 3), round(m[5] * k, 3), 1.0 if SLOT[i] == 1 else round(o_, 3)]
                   for i, d, m, o_ in (anc[n] if n < len(anc) else []) if i in SLOT] for n in fr]
    return out


def main(sids):
    SPR = json.load(open(f'{ROOT}/game/data/sprites.json'))
    keys = [f'{s}_e' for s in sids] if sids else [k for k in SPR['chars'] if k.endswith('_e')]
    res = {}
    for key in keys:
        if key not in SPR['chars']: continue
        res[key] = anchors(key[:-2], SPR['chars'][key])
        print(key, {a: sum(1 for f in v if f) for a, v in res[key].items()}, flush=True)
    def up(S2):
        for key, an in res.items():
            for a, A in an.items(): S2['chars'][key]['anims'][a]['anc'] = A
    sprio.update(up)


if __name__ == '__main__':
    main(sys.argv[1:])
