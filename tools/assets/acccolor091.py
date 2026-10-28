"""0.91 (capes / hats not like the client): the accessories whose client symbol paints parts of itself with the
character's colours (GAC.applyColor(part, n) / applyHeadColor = 1 / applyBodyColor = 2 / applyBottomColor = 3 — 90
in the up-to-date client: capes, hats, pets) get a colour mask like the class sheets: a base with those parts black
and <sym>_m.webp (zone k -> channel k, lossless), acci[sym].m = 1; CharSprite.tintAcc recolours them with the
character's colours. Checked in the real client (work/retrolab, a Crâ in pure red / green / blue: cape 17_138 turns
red, 16_185 red / yellow…); the game showed their default colours, or black.
Every view keeps its frame count; a frame whose size is unchanged keeps its origin (accfix061's corrections).
usage: python tools/assets/acccolor091.py [sym…]   (default: every accessory of the game with colour parts in the client)"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import sys, os, json
import numpy as np
from PIL import Image
import swflib as S, timeline as TL, stage as ST
import build_chars20 as BC, build_acc060 as A6

G = f'{ROOT}/game'


def coloured(tl, D, cid, seen=None):
    """does the symbol (or a clip inside it) have colour parts?"""
    seen = seen if seen is not None else set()
    if cid in seen or cid not in D: return False
    seen.add(cid)
    if cid in tl.colors: return True
    t = D[cid]
    if t.code != S.T_SPRITE: return False
    for st in t.sub or []:
        if st.code in (S.T_PLACE, S.T_PLACE2, 70):
            p = S.parse_place(st)
            if 'char' in p and coloured(tl, D, p['char'], seen): return True
    return False


def main(only):
    lib = f'{A6.NEW}/clips/sprites/accessories'
    SPR = json.load(open(f'{G}/data/sprites.json')); A = SPR['acci']; out = {}
    for f in sorted(os.listdir(lib)):
        src = f'{lib}/{f}'; sw = S.read_swf(src); tl = TL.Timeline(sw); ex = S.exports(sw['tags']); D = S.defs(sw['tags'])
        syms = [s for s in ex if s in A and s[:3] in ('16_', '17_', '18_') and (not only or s in only) and coloured(tl, D, ex[s])]
        if not syms: continue
        jobs = []
        for s in syms:
            labs = A6.frame_labels(D, ex[s])
            for v, fr in A[s]['f'].items():
                if v not in labs: continue
                n = len(fr) if isinstance(fr[0], list) else 1
                jobs.append(dict(key=f'{s}__{v}', sym=s, snap=labs[v], zoom=A[s].get('zoom') or A6.Z, n=n))
        print(f, len(syms), 'accessories', len(jobs), 'views', flush=True)
        R = {z: ST.stage_render(src, jobs, f'{ROOT}/work/acccolor091/{f[:-4]}_{z}', tagpatch=BC.make_patch(tl, z), prune=True) for z in (0, 1, 2, 3)}
        for s in syms:
            M = A[s]; pic = Image.open(f'{G}/assets/acc/i/{s}.webp').convert('RGBA'); items = []; kept = moved = 0
            for v, fr in M['f'].items():
                fl = fr if isinstance(fr[0], list) else [fr]; key = f'{s}__{v}'; rb = R[0].get(key)
                imgs = [im for im in (rb['imgs'] if rb else [])]
                for i, (x, y, w, h, ox, oy) in enumerate(fl):
                    im = imgs[i] if i < len(imgs) else None
                    if im is None or not im.getbbox():   # (nothing rendered: the old picture, no colour)
                        items.append(((v, i), pic.crop((x, y, x + w, y + h)), None, ox, oy)); continue
                    bb = im.getbbox(); b = im.crop(bb); b0 = np.asarray(b).astype(np.int16)
                    ch = []
                    for z in (1, 2, 3):
                        iz = R[z][key]['imgs'][i] if R[z].get(key) and i < len(R[z][key]['imgs']) else None
                        d = (np.asarray(iz.crop(bb)).astype(np.int16)[:, :, :3] - b0[:, :, :3]).mean(axis=2) if iz is not None else np.zeros(b0.shape[:2])
                        ch.append(np.clip(d, 0, 255))
                    m = Image.fromarray(np.stack(ch, axis=2).astype(np.uint8), 'RGB')
                    o = rb['meta']['origin']; nox, noy = o[0] - bb[0], o[1] - bb[1]
                    if b.size == (w, h): nox, noy = ox, oy; kept += 1   # (same picture size: the corrected origin)
                    else: moved += 1
                    items.append(((v, i), b, m, nox, noy))
            atlas, pos = ST.pack([(k, b) for k, b, m, _, _ in items], maxw=2048)
            ma = Image.new('RGB', atlas.size)
            for k, b, m, _, _ in items:
                if m is not None: ma.paste(m, pos[k][:2])
            if not np.asarray(ma).any(): print('  no colour part drawn', s); continue
            atlas.save(f'{G}/assets/acc/i/{s}.webp', 'WEBP', quality=A6.Q, method=A6.METHOD)
            ma.save(f'{G}/assets/acc/i/{s}_m.webp', 'WEBP', **BC.MASK_WEBP)
            F = {}
            for (v, i), b, m, ox, oy in items: F.setdefault(v, []).append([*pos[(v, i)], round(ox, 2), round(oy, 2)])
            nm = dict(M); nm.update(w=atlas.width, h=atlas.height, m=1, f={v: (fl if len(fl) > 1 else fl[0]) for v, fl in F.items()})
            out[s] = nm; print(' ', s, 'origins kept', kept, 'new', moved, flush=True)
    import sprio
    sprio.update(lambda S_: S_['acci'].update(out))
    print('masks', len(out))


if __name__ == '__main__':
    main(set(sys.argv[1:]) or None)
