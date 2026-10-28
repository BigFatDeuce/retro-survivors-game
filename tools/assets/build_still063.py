"""0.63 (hats / capes still off and hair showing in many skins: everything must come from the client): the poses
of the main character sheets (standing, casts, blows without a weapon, death…) were matched in 1.41.9 against the v1.9
sheets (build_chars20): their accessory anchors are approximate and they can carry no front layers. This renders them
again from the up-to-date client like the runs (build_move060.char): base + 3 colour-zone passes, the accessory anchors of
every frame from the client's timeline (hat, cape, pet), into '<sid>_s' (and '<sid>_h_s' for the Iop 80's two-frame
head under a hat). The standing poses keep the client's 60 fps; the other animations one frame in three (20 fps, the
1.41.9 rate: the sheets stay under 4096 px). CharSprite takes these animations from this sheet first (sheetFor), the
hats' and capes' front layers come from build_accfront061 SHEET=_s.
usage: python tools/assets/build_still063.py [key…]   (key = '<sid>' or '<sid>_h'; default: every class sprite; resumes)"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import sys, os, json
import numpy as np
from PIL import Image
import swflib as S, timeline as TL, stage as ST
import build_chars20 as BC, build_move060 as BM
import sprio

G = f'{ROOT}/game'
WORK = f'{ROOT}/work/still063'
Z = BM.Z
SLOT = BM.SLOT
STILL = ('staticR', 'staticL')   # (60 fps; the rest at 20)
NOANC = {'1150', '1155', '8000', '8001'}   # (the Brigandin and the Roublard: their client clips have no accessory holders: they keep the old sheets)


def anims_of(SPR, sid, ex):
    return [a for a in SPR['chars'][sid]['anims'] if not a.startswith('run') and a in ex]


def plan(sw, tl, ex, names):
    """the frames to keep per animation and the timeline their anchors come from. The client's clips often start with
    gotoAndStop('static') (the standing pose skips the way out of an emote) and stop() further on: the renders hold a
    stop() frame (stage.stops_of / hold), the anchors must too (a timeline of the held tags), and the frames before the
    label jumped to are never shown"""
    holds = ST.stops_of(sw); D = S.defs(sw['tags'])
    tags = [ST.hold(t, holds[t.sprite_id]) if t.code == S.T_SPRITE and t.sprite_id in holds else t for t in sw['tags']]
    tlh = TL.Timeline(dict(sw, tags=tags))
    out = {}
    for a in names:
        sym = ex[a]; n = tl.eff_frames(sym); start = 0
        clips = [sym] + [e['char'] for e in (tl.states(sym)[0].values() if tl.nframes(sym) <= 1 else []) if D.get(e['char']) is not None and D[e['char']].code == S.T_SPRITE and tl.nframes(e['char']) > 1]
        for c in clips:
            labs = S.labels(D[c].sub); acts = S.scripts_of(D[c].sub).get(0, [])
            hit = [labs[v] for b in acts for k, v in S.action_strings(b) if k == 's' and v in labs]
            if hit: start = hit[0]; break
        out[a] = list(range(start, n, 1 if a in STILL else 3)) or [start]
    return tlh, out


def char(key, SPR):
    sid = key.split('_')[0]; hat = key.endswith('_h'); src = f'{BM.NSPR}/{sid}.swf'
    sw = S.read_swf(src); tl = TL.Timeline(sw); ex = S.exports(sw['tags']); heads = BC.head_ids(sw); rate = 60.0   # (the client plays every loaded clip at its own window's rate, 60: some sprite files declare 40 — the female Ecaflip 61, the female Sacrieur 111, the Roublard — and ran slowed down)
    names = anims_of(SPR, sid, ex); tlh, FR = plan(sw, tl, ex, names)
    jobs = [dict(key=a, sym=a, zoom=Z, frames=FR[a]) for a in names]
    R = {z: BC.render(src, jobs, f'{WORK}/{key}', tl, z, hat, heads) for z in (0, 1, 2, 3)}
    items, frames = [], {}
    for job in jobs:
        a = job['key']; rb = R[0][a]; o = rb['meta']['origin']
        for n, fi in enumerate(job['frames'][:len(rb['imgs'])]):
            im = rb['imgs'][n]
            if im is None or not im.getbbox(): continue
            bb = im.getbbox(); b0 = np.asarray(im.crop(bb)).astype(np.int16); ch = []
            for z in (1, 2, 3):
                iz = R[z][a]['imgs'][n] if n < len(R[z][a]['imgs']) else None
                d = (np.asarray(iz.crop(bb)).astype(np.int16)[:, :, :3] - b0[:, :, :3]).mean(axis=2) if iz is not None else np.zeros(b0.shape[:2])
                ch.append(np.clip(d, 0, 255))
            items.append(((a, fi), im.crop(bb), Image.fromarray(np.stack(ch, axis=2).astype(np.uint8), 'RGB'))); frames[(a, fi)] = (o[0] - bb[0], o[1] - bb[1])
    atlas, pos = ST.pack([(k, b) for k, b, m in items], maxw=4096)
    out = f'{key}_s'
    atlas.save(f'{G}/assets/chars/{out}.webp', 'WEBP', quality=88, method=6)
    ma = Image.new('RGB', atlas.size)
    for k, b, m in items: ma.paste(m, pos[k][:2])
    ma.save(f'{G}/assets/chars/{out}_m.webp', 'WEBP', **BC.MASK_WEBP)   # (0.91: lossless masks)
    meta = dict(w=atlas.width, h=atlas.height, zoom=Z, anims={}); k = Z / 20.0
    old = SPR['chars'][sid]['anims']
    for job in jobs:
        a = job['key']; F, A = [], []
        anc = tlh.anchors(ex[a], frames=job['frames'])
        for n, fi in enumerate(job['frames']):
            if (a, fi) not in pos: continue
            x, y, w, h = pos[(a, fi)]; ox, oy = frames[(a, fi)]; F.append([x, y, w, h, round(ox, 2), round(oy, 2)])
            A.append([[SLOT[i], d, *[round(v * k, 4) for v in m[:4]], round(m[4] * k, 3), round(m[5] * k, 3), 1.0 if SLOT[i] == 1 else round(o_, 3)] for i, d, m, o_ in anc[n] if i in SLOT])
        if len(F) != len(job['frames']): print(out, a, 'empty frames', len(job['frames']) - len(F), flush=True)
        meta['anims'][a] = dict(fps=rate if a in STILL else rate / 3, loop=old.get(a, {}).get('loop', a in STILL), f=F, anc=A, src=job['frames'])
    print(out, atlas.size, {a: len(v['f']) for a, v in meta['anims'].items()}, os.path.getsize(f'{G}/assets/chars/{out}.webp') // 1024, 'KB', flush=True)
    return out, meta


def main(keys):
    SPR = json.load(open(f'{G}/data/sprites.json', encoding='utf8'))
    os.makedirs(WORK, exist_ok=True); dp = f'{WORK}/done.json'
    done = json.load(open(dp)) if os.path.exists(dp) else {}
    if not keys:
        sids = sorted({k for k in SPR['chars'] if k.isdigit() and k not in NOANC and os.path.exists(f'{BM.NSPR}/{k}.swf')}, key=int)
        keys = sids + [f'{s}_h' for s in sids if BC.hat_differs(f'{BM.NSPR}/{s}.swf')]   # (0.64: hair hidden under hats too, build_chars20.hide_hair)
    for key in keys:
        if key in done: continue
        try: out, meta = char(key, SPR)
        except Exception as e:
            import traceback; traceback.print_exc(); print('FAIL', key, e, flush=True); continue
        done[key] = [out, meta]; json.dump(done, open(dp + '.tmp', 'w')); os.replace(dp + '.tmp', dp)
    asked = set(keys)   # (0.91: only the keys of this call: the cache's older sheets lack the later front layers / fps)
    def up(S2):
        for key, (out, meta) in done.items():
            if key not in asked: continue
            if key.split('_')[0] not in NOANC: S2['chars'][out] = meta
    sprio.update(up)
    print('still sheets', len(done))


if __name__ == '__main__':
    main(sys.argv[1:])
