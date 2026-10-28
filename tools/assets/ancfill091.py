"""0.91: accessory anchors the client's clips lack. The Otomaï (NPC sprite 9066) never wears a hat or a cape in the
client, so several of his own clips have no holder for them (standing R: no hat; standing L, run L / S: neither; run R /
F: no hat; no pet holder anywhere: CharSprite's standard pet spot): the hat / cape were simply not drawn there. For a
sheet frame without the holder of a slot, its anchor is rebuilt from the body part the accessory rides on — the hat on
the hair clip ('cCra_<V>_Cheveux'), the cape on the body ('cCra_<V>_Corps') —: M_holder = M_part(frame) x rel, with
rel = M_part^-1 x M_holder measured where a clip has both, the reference with the steadiest rel among (in this order)
the same animation's other frames, the sprite's own other animations with that part (hats), the male Crâ's (90) same
animation (the NPC is built on his skeleton and uses his part names; capes of the runs take it first: its flapping
'RR' / 'RL' views), any Crâ animation with that part. The view label and the paint order come from the reference.
usage: python tools/assets/ancfill091.py [sid] [--dry]      (sid 9066 by default: its _s, _h_s, _r, _h_r sheets; run it again
after any of them is rendered again)"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import sys, json, re
import numpy as np
import swflib as S, timeline as TL, build_move060 as BM

G = f'{ROOT}/game'
K = BM.Z / 20.0
SLOTS = {1: 'hat', 2: 'cape'}
CRA = 90


def inv(m):
    a, b, c, d, e, f = m; det = a * d - b * c
    return [d / det, -b / det, -c / det, a / det, (c * f - d * e) / det, (b * e - a * f) / det]


def named(tl, sid, f, m=TL.IDENT, out=None):
    """world matrix of every named clip instance shown at frame f (TL.walk's frame logic)"""
    out = {} if out is None else out
    st = tl.states(sid)
    if not st: return out
    lst = st[min(f, len(st) - 1)]
    for d in sorted(lst):
        e = lst[d]
        if e.get('clip'): continue
        ch = tl.defs.get(e['char'])
        if ch is None or ch.code != S.T_SPRITE: continue
        mm = TL.mul(m, e['m'])
        if e.get('name') and e['name'] not in out: out[e['name']] = mm
        n = tl.nframes(e['char'])
        named(tl, e['char'], 0 if e['char'] in tl.frozen else (f - e['born']) if n <= 1 else (f - e['born']) % n, mm, out)
    return out


def part_of(names, slot):
    if slot == 1: return next((n for n in names if re.match(r'^cCra_[RLFBS]_Cheveux$', n)), None)
    return next((n for n in names if re.match(r'^cCra_[RLFBS]_Corps$', n)), None)


class Clip:
    def __init__(self, sid):
        self.sw = S.read_swf(f'{BM.NSPR}/{sid}.swf'); self.tl = TL.Timeline(self.sw); self.ex = S.exports(self.sw['tags']); self.cache = {}

    def frame(self, anim, f):
        k = (anim, f)
        if k not in self.cache:
            sid = self.ex[anim]; hold = {a[0]: a for a in self.tl.anchors(sid, frames=[f])[0]}
            self.cache[k] = (named(self.tl, sid, f), hold)
        return self.cache[k]

    def rel(self, anim, slot, pname, frames=None):
        """[median rel, dispersion, view, order] of the holder `slot` on part `pname` over the frames that have both"""
        if anim not in self.ex: return None
        rs, views, orders, per = [], [], [], {}
        for f in (frames if frames is not None else range(self.tl.eff_frames(self.ex[anim]))):
            names, hold = self.frame(anim, f)
            if slot in hold and pname in names:
                r = TL.mul(inv(names[pname]), hold[slot][2]); rs.append(r); per[f] = r; views.append(hold[slot][1]); orders.append(hold[slot][3])
        if not rs: return None
        R = np.array(rs); med = np.median(R, axis=0)
        disp = float(np.abs(R[:, :4] - med[:4]).mean() * 200 + np.abs(R[:, 4:] - med[4:]).mean() / 20)   # (scale ~ x200, translation in Dofus px)
        return [list(med), disp, max(set(views), key=views.count), float(np.median(orders)), per, self.tl.eff_frames(self.ex[anim])]


def fill(sid=9066, dry=False):
    SPR = json.load(open(f'{G}/data/sprites.json')); own, cra = Clip(sid), Clip(CRA)
    own_anims = [a for a in own.ex if re.match(r'^(static|run|anim\d+|die|hit|bonus)[RLFBS]$', a)]
    out = {}
    for key in (f'{sid}_s', f'{sid}_h_s', f'{sid}_r', f'{sid}_h_r'):   # (each on its own: a sheet rendered again lost its filled anchors)
        meta = SPR['chars'].get(key)
        if not meta: continue
        for a, an in meta['anims'].items():
            if a not in own.ex or not an.get('anc'): continue
            src = an.get('src') or list(range(len(an['f'])))
            if len(src) != len(an['anc']): print(key, a, 'skipped: frames without their client frame number', len(src), len(an['anc'])); continue
            new = [list(x) for x in an['anc']]; added = {1: 0, 2: 0}; refs = {}
            for n, fi in enumerate(src):
                names, hold = own.frame(a, fi)
                for slot in SLOTS:
                    if any(x[0] == slot for x in new[n]): continue
                    pname = part_of(names, slot)
                    if not pname: continue
                    if (slot, pname) not in refs:
                        cands = [('self', own.rel(a, slot, pname))]
                        others = [('own:' + b, own.rel(b, slot, pname)) for b in own_anims if b != a]
                        crs = [('cra:' + a, cra.rel(a, slot, pname))]
                        cany = [('cra:' + b, cra.rel(b, slot, pname)) for b in cra.ex if b != a and re.match(r'^(static|run|anim\d+)[RLFBS]$', b)]
                        groups = [cands, crs, others, cany] if slot == 2 and a.startswith('run') else [cands, others, crs, cany]
                        best = None
                        for g in groups:
                            g = [c for c in g if c[1]]
                            if g: best = min(g, key=lambda c: c[1][1]); break
                        refs[(slot, pname)] = best
                        print(key, a, SLOTS[slot], pname, '->', best[0] if best else None, 'disp %.2f view %s' % (best[1][1], best[1][2]) if best else '')
                    best = refs[(slot, pname)]
                    if not best: continue
                    rel, _, view, order, per, nref = best[1]
                    # the same animation (its own other frames, or the Crâ's with as many frames): the nearest frame's own
                    # rel — a cape flaps while running —, else the steadiest median
                    if best[0] == 'self' or (best[0] == 'cra:' + a and nref == own.tl.eff_frames(own.ex[a])): rel = per[min(per, key=lambda g: abs(g - fi))]
                    m = TL.mul(names[pname], rel)
                    new[n].append([slot, view, *[round(v * K, 4) for v in m[:4]], round(m[4] * K, 3), round(m[5] * K, 3), 1.0 if slot == 1 else round(order, 3)])
                    added[slot] += 1
            if added[1] or added[2]:
                print(key, a, 'frames given a hat', added[1], 'a cape', added[2], '/', len(src))
                out.setdefault(key, {})[a] = new
    if dry: return out
    import sprio
    def up(S_):
        for k2, anims in out.items():
            for a, anc in anims.items(): S_['chars'][k2]['anims'][a]['anc'] = anc
    sprio.update(up); print('sheets updated', sorted(out))
    return out


if __name__ == '__main__':
    args = [x for x in sys.argv[1:] if not x.startswith('--')]
    fill(int(args[0]) if args else 9066, dry='--dry' in sys.argv)
