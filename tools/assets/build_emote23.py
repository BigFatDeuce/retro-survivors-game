"""0.23: extra character animations (emotes) rendered natively from the class sprites (clips/sprites/<sid>.swf) into a
sheet of their own, assets/chars/<sid>_e.webp (+ _m colour mask, same recipe as build_chars20: base with the colour
zones black, then zone k white -> mask channel k). CharSprite looks the animation up in '<sid>_e' too.
usage: python tools/assets/build_emote23.py ZOOM anim[,anim…] [sid…]     e.g. build_emote23.py 4.8 emote8R,emote8L
(no sid: every class sprite of content.json)
0.61: HAT=1 = the hat variant '<sid>_h_e' (head clips on their short-hair frame, as '<sid>_h' / '<sid>_h_r'), for the
sprites whose head clips have two frames (the Iop 80: his spikes showed over the hat); it takes the plain sheet's anchors"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import sys, os, json
import numpy as np
from PIL import Image
import swflib as S, timeline as TL, stage as ST
import build_chars20 as BC

G = f'{ROOT}/game'


def build(sid, anims, Z, hat=False):
    src = f'{BC.RAW}/{sid}.swf'
    sw = S.read_swf(src); tl = TL.Timeline(sw); ex = S.exports(sw['tags']); low = {k.lower(): k for k in ex}
    heads = BC.head_ids(sw)
    have = {a: low[a.lower()] for a in anims if a.lower() in low}
    if not have: print(sid, 'no', anims); return
    wd = f'{ROOT}/work/emote23/{sid}' + ('_h' if hat else '')
    jobs = [dict(key=a, sym=s, zoom=Z, n=min(80, tl.eff_frames(ex[s]))) for a, s in have.items()]
    R = {z: BC.render(src, jobs, wd, tl, z, hat, heads) for z in (0, 1, 2, 3)}
    items, frames, order = [], {}, {}
    for a in have:
        rb = R[0][a]; o = rb['meta']['origin']; order[a] = []
        for n, im in enumerate(rb['imgs']):
            if im is None or not im.getbbox(): order[a].append(None); continue
            bb = im.getbbox(); b = im.crop(bb); b0 = np.asarray(b).astype(np.int16); ch = []
            for z in (1, 2, 3):
                iz = R[z][a]['imgs'][n]
                d = (np.asarray(iz.crop(bb)).astype(np.int16)[:, :, :3] - b0[:, :, :3]).mean(axis=2) if iz is not None else np.zeros(b0.shape[:2])
                ch.append(np.clip(d, 0, 255))
            m = Image.fromarray(np.stack(ch, axis=2).astype(np.uint8), 'RGB')
            items.append(((a, n), b, m)); frames[(a, n)] = (o[0] - bb[0], o[1] - bb[1]); order[a].append(n)
    atlas, pos = ST.pack([(k, b) for k, b, m in items], maxw=4096)
    key = f'{sid}_h_e' if hat else f'{sid}_e'
    atlas.save(f'{G}/assets/chars/{key}.webp', 'WEBP', quality=90, method=6)
    ma = Image.new('RGB', atlas.size)
    for k, b, m in items: ma.paste(m, pos[k][:2])
    ma.save(f'{G}/assets/chars/{key}_m.webp', 'WEBP', **BC.MASK_WEBP)   # (0.91: lossless masks)
    meta = dict(w=atlas.width, h=atlas.height, zoom=Z, anims={})
    for a, lst in order.items():
        F = []
        for n in lst:
            if n is None: F.append(F[-1] if F else [0, 0, 1, 1, 0, 0]); continue
            x, y, w, h = pos[(a, n)]; ox, oy = frames[(a, n)]; F.append([x, y, w, h, round(ox, 2), round(oy, 2)])
        meta['anims'][a] = dict(fps=sw['rate'], loop=False, f=F)
    import sprio
    if hat:   # the same frames as the plain sheet: its accessory anchors (build_emoteanc45) hold
        plain = json.load(open(f'{G}/data/sprites.json'))['chars'].get(f'{sid}_e', {}).get('anims', {})
        for a, v in meta['anims'].items():
            if a in plain and plain[a].get('anc') and len(plain[a]['anc']) == len(v['f']): v['anc'] = plain[a]['anc']
    sprio.update(lambda SPR: SPR['chars'].__setitem__(key, meta))
    print(key, 'done', atlas.size, list(have), flush=True)


if __name__ == '__main__':
    Z = float(sys.argv[1]); anims = sys.argv[2].split(',')
    sids = sys.argv[3:] or sorted({s for c in json.load(open(f'{G}/data/content.json'))['classes'] for s in c['sprites']})
    hat = os.environ.get('HAT') == '1'
    for sid in sids:
        if hat and not BC.hat_differs(f'{BC.RAW}/{sid}.swf'): continue   # (0.64: two-frame heads or 'Cheveux' clips)
        build(sid, anims, Z, hat)
