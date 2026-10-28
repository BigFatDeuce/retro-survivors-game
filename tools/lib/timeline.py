"""Display-list simulation of SWF sprites, following FFDec's renderer: nested clips play from the frame they
were placed (looping), scripts are ignored, except clips frozen by stage.freeze rules.

Used for: conservative bounds of an animation (to stage it in a fixed box) and accessory anchors
(GAC.applyAccessory placeholders: weapon 0, hat 1, cape 2, pet 3, shield 4).
"""
import swflib as S


def mul(p, c):
    pa, pb, pc, pd, pe, pf = p
    ca, cb, cc, cd, ce, cf = c
    return [pa * ca + pc * cb, pb * ca + pd * cb, pa * cc + pc * cd, pb * cc + pd * cd,
            pa * ce + pc * cf + pe, pb * ce + pd * cf + pf]


IDENT = [1.0, 0.0, 0.0, 1.0, 0.0, 0.0]


class Timeline:
    def __init__(self, swf, frozen=()):
        self.swf = swf
        self.defs = S.defs(swf['tags'])
        self.ex = S.exports(swf['tags'])
        self.frozen = set(frozen)
        self._states = {}
        self.acc = {}       # sprite id -> (idx, dir)
        self.colors = {}    # sprite id -> {name: zone}
        self.stop1 = set()  # sprites with stop() on frame 1
        for t in swf['tags']:
            if t.code != S.T_SPRITE: continue
            for fi, bodies in S.scripts_of(t.sub).items():
                for b in bodies:
                    toks = S.action_strings(b)
                    if fi == 0 and any(k == 'op' and v == 'stop' for k, v in toks): self.stop1.add(t.sprite_id)
                    for i, (k, v) in enumerate(toks):
                        if k != 's' or i < 4: continue
                        if v == 'applyAccessory' and i >= 5 and toks[i - 1] == ('s', 'GAC'):
                            idx, d = toks[i - 4][1], toks[i - 5][1]
                            if isinstance(idx, (int, float)) and isinstance(d, str): self.acc[t.sprite_id] = (int(idx), d)
                        elif v in ('applyHeadColor', 'applyBodyColor', 'applyBottomColor') and toks[i - 1] == ('s', 'GAC') and i >= 3:
                            # accessories tinted with the character's colours (head = 1, body = 2, bottom = 3)
                            name = toks[i - 3][1]
                            if isinstance(name, str):
                                self.colors.setdefault(t.sprite_id, {})[name] = {'applyHeadColor': 1, 'applyBodyColor': 2, 'applyBottomColor': 3}[v]
                        elif v == 'applyColor' and toks[i - 1] == ('s', 'GAC'):
                            name, zone = toks[i - 3][1], toks[i - 4][1]
                            if isinstance(name, str) and isinstance(zone, (int, float)):
                                self.colors.setdefault(t.sprite_id, {})[name] = int(zone)

    def states(self, sid):
        """per-frame display lists: [{depth: dict(char, m, cx, name, born, clip)}]"""
        if sid in self._states: return self._states[sid]
        t = self.defs[sid]
        out = []; cur = {}; fi = 0
        for tag in t.sub:
            if tag.code in (S.T_PLACE, S.T_PLACE2, S.T_PLACE3):
                p = S.parse_place(tag); d = p['depth']
                if p.get('move') and d in cur:
                    e = dict(cur[d])
                    if 'char' in p and p['char'] != e['char']: e['char'] = p['char']; e['born'] = fi
                    if 'matrix' in p: e['m'] = p['matrix']
                    if 'cx' in p: e['cx'] = p['cx']
                    if 'name' in p: e['name'] = p['name']
                    if 'clipdepth' in p: e['clip'] = p['clipdepth']
                    cur[d] = e
                elif 'char' in p:
                    cur[d] = dict(char=p['char'], m=p.get('matrix', IDENT), cx=p.get('cx'), name=p.get('name'), born=fi, clip=p.get('clipdepth'))
            elif tag.code in (S.T_REMOVE, S.T_REMOVE2):
                d = S.BitReader(tag.data).u16() if tag.code == S.T_REMOVE2 else S.BitReader(tag.data, 2).u16()
                cur.pop(d, None)
            elif tag.code == S.T_SHOWFRAME:
                out.append(dict(cur)); fi += 1
        if not out: out.append(dict(cur))
        self._states[sid] = out
        return out

    def nframes(self, sid):
        t = self.defs.get(sid)
        return len(self.states(sid)) if t is not None and t.code == S.T_SPRITE else 1

    def walk(self, sid, frame, m, cb, top=None, order=None):
        """visit every leaf of sprite sid at its frame; cb(kind, cid, matrix, top_depth_rank, extra)"""
        st = self.states(sid)
        if not st: return
        lst = st[min(frame, len(st) - 1)]
        depths = sorted(lst)
        for rank, d in enumerate(depths):
            e = lst[d]
            if e.get('clip'): continue   # masks: ignored for bounds
            mm = mul(m, e['m'])
            tr = (rank, len(depths)) if top is None else top
            ch = self.defs.get(e['char'])
            if ch is None: continue
            if ch.code == S.T_SPRITE:
                if e['char'] in self.acc:
                    cb('acc', e['char'], mm, tr, self.acc[e['char']])
                n = self.nframes(e['char'])
                # a single-frame clip keeps the time running for its own children (like the player)
                sub = 0 if e['char'] in self.frozen else (frame - e['born']) if n <= 1 else (frame - e['born']) % n
                self.walk(e['char'], sub, mm, cb, tr)
            elif ch.code in S.SHAPE_CODES:
                cb('shape', e['char'], mm, tr, S.shape_bounds(ch))
            else:
                cb('other', e['char'], mm, tr, None)

    def bounds(self, sid, frames=None, m=IDENT):
        """conservative bounds (twips) over frames: x0, x1, y0, y1"""
        b = [1e9, -1e9, 1e9, -1e9]
        def cb(kind, cid, mm, tr, extra):
            if kind != 'shape': return
            x0, x1, y0, y1 = extra
            for x, y in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
                X = mm[0] * x + mm[2] * y + mm[4]; Y = mm[1] * x + mm[3] * y + mm[5]
                b[0] = min(b[0], X); b[1] = max(b[1], X); b[2] = min(b[2], Y); b[3] = max(b[3], Y)
        n = self.nframes(sid)
        for f in (frames if frames is not None else range(n)):
            self.walk(sid, f, m, cb)
        return b

    def anchors(self, sid, frames=None):
        """per frame: list of (idx, dir, matrix(twips), order); order = share of the paint order drawn before it"""
        out = []
        n = self.eff_frames(sid)
        for f in (frames if frames is not None else range(n)):
            lst = []; cnt = [0]
            def cb(kind, cid, mm, tr, extra):
                if kind == 'acc': lst.append([extra[0], extra[1], mm, cnt[0]])
                elif kind == 'shape': cnt[0] += 1
            self.walk(sid, f, IDENT, cb)
            for a in lst: a[3] = a[3] / max(1, cnt[0])
            out.append([tuple(a) for a in lst])
        return out

    def eff_frames(self, sid, depth=0):
        """frames of an animation; single-frame wrappers take the length of their longest child (deep)"""
        n = self.nframes(sid)
        if n > 1 or depth > 4: return n
        st = self.states(sid)
        best = 1
        for e in (st[0].values() if st else []):
            ch = self.defs.get(e['char'])
            if ch is not None and ch.code == S.T_SPRITE and e['char'] not in self.frozen:
                best = max(best, self.eff_frames(e['char'], depth + 1))
        return best
